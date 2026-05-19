#!/usr/bin/env bash
# auto_dft.sh — End-to-end DFT driver. Single entry point for /dft.
# Args: <ip_name>
# Pipeline: handoff gate → SSOT read → passthrough OR (tcl → openroad → parse → optional ATPG) → report
set -uo pipefail

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[DFT] usage: auto_dft.sh <ip_name>" >&2; exit 2; fi
if [ ! -d "${IP}" ]; then echo "[DFT] no such IP dir: ${IP}" >&2; exit 2; fi

DIR="$(dirname "$0")"
NETLIST="${IP}/syn/out/synth.v"
OUT="${IP}/dft/out"
SSOT="${IP}/yaml/${IP}.ssot.yaml"
mkdir -p "${OUT}"

# Handoff gate
if [ ! -s "${NETLIST}" ]; then
  echo "[DFT HANDOFF MISSING] ${NETLIST} — run /syn first" >&2; exit 5
fi
if compgen -G "${IP}/rtl/*.sv" >/dev/null || compgen -G "${IP}/rtl/*.v" >/dev/null; then
  NEWEST_RTL=$(ls -t ${IP}/rtl/*.sv ${IP}/rtl/*.v 2>/dev/null | head -1)
  if [ -n "${NEWEST_RTL}" ] && [ "${NEWEST_RTL}" -nt "${NETLIST}" ]; then
    echo "[DFT STALE NETLIST] ${NEWEST_RTL} newer than ${NETLIST} — re-run /syn" >&2; exit 6
  fi
fi

# Read dft.enabled from SSOT
ENABLED=$(python3 - "${SSOT}" <<'PY'
import sys, pathlib
p = pathlib.Path(sys.argv[1])
if not p.is_file(): print("false"); sys.exit(0)
try:
    import yaml; d = yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
except Exception:
    d = {}
dft = d.get("dft", {}) or {}
print("true" if dft.get("enabled", False) else "false")
PY
)

if [ "${ENABLED}" != "true" ]; then
  cp "${NETLIST}" "${OUT}/scan.v"
  python3 - "${IP}" "${OUT}" <<'PY'
import json, sys, pathlib
ip, out = sys.argv[1:3]
obj = {
  "top": ip, "tool": "passthrough", "scan_chains": [],
  "summary": {"total_ffs": None, "ffs_in_chains": 0, "ffs_skipped": 0,
              "chains": 0, "max_length": 0, "min_length": 0,
              "scan_enable_port": None, "mode": "passthrough"},
}
pathlib.Path(out, "scan_chains.json").write_text(json.dumps(obj, indent=2), encoding="utf-8")
PY
  bash "${DIR}/write_report.sh" "${IP}" || true
  echo "[DFT DISABLED] passthrough — ${NETLIST} copied to ${OUT}/scan.v"
  exit 0
fi

# Real scan-insert path: need OpenROAD + Liberty + scan_enable_port to exist
if ! command -v openroad >/dev/null 2>&1; then
  echo "[DFT TOOL MISSING] openroad not on PATH" >&2; exit 3
fi
LIB="${SKY130_LIB:-}"
if [ ! -r "${LIB}" ]; then
  echo "[DFT MISSING PDK] \$SKY130_LIB unreadable: ${LIB}" >&2; exit 4
fi
export SKY130_LIB="${LIB}"

bash "${DIR}/write_dft_tcl.sh"     "${IP}" || exit $?
bash "${DIR}/run_openroad_dft.sh"  "${IP}" || exit $?
bash "${DIR}/parse_chains.sh"      "${IP}" || exit $?

# Optional ATPG via Fault
ATPG_ENABLED=$(python3 - "${SSOT}" <<'PY'
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
atpg = ((d.get("dft") or {}).get("atpg") or {})
print("true" if atpg.get("enabled", False) else "false")
PY
)
if [ "${ATPG_ENABLED}" = "true" ]; then
  if command -v fault >/dev/null 2>&1; then
    bash "${DIR}/run_fault_atpg.sh" "${IP}" || echo "[DFT] Fault ATPG step failed — continuing without coverage" >&2
  else
    echo "[DFT] Fault not on PATH — skipping ATPG (set dft.atpg.enabled: false in SSOT to suppress this warning)" >&2
  fi
fi

bash "${DIR}/write_report.sh" "${IP}" || true

CHAINS=$(python3 -c "import json; d=json.load(open('${OUT}/scan_chains.json')); print(d['summary']['chains'])" 2>/dev/null || echo 0)
FFS=$(python3   -c "import json; d=json.load(open('${OUT}/scan_chains.json')); print(d['summary']['ffs_in_chains'])" 2>/dev/null || echo 0)
echo "[DFT HANDOFF] ${OUT}/scan.v ready (chains=${CHAINS}, scan_ffs=${FFS}) — run /pnr-fp"
