#!/usr/bin/env bash
# run_fault_atpg.sh — Optional Fault ATPG step. Reads scan.v + SSOT,
# produces <ip>/dft/out/<ip>.test and <ip>/dft/out/coverage.json.
# Args: <ip_name>
# Best-effort: a Fault failure is non-fatal — auto_dft.sh continues without
# coverage and emits a [DFT COVERAGE LOW] / [DFT ATPG SKIPPED] hint.
set -uo pipefail

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[DFT] usage: run_fault_atpg.sh <ip_name>" >&2; exit 2; fi

OUT="${IP}/dft/out"
SCAN="${OUT}/scan.v"
SSOT="${IP}/yaml/${IP}.ssot.yaml"
TEST="${OUT}/${IP}.test"
COV="${OUT}/coverage.json"
LOG="${OUT}/fault.log"

if ! command -v fault >/dev/null 2>&1; then
  echo "[DFT] Fault not on PATH — skipping ATPG" >&2; exit 0
fi
if [ ! -s "${SCAN}" ]; then echo "[DFT] missing ${SCAN}" >&2; exit 2; fi

# Pull the fault config from SSOT.
read MODEL TOP TARGET < <(python3 - "${SSOT}" "${IP}" <<'PY'
import sys, pathlib
ssot, ip = sys.argv[1:3]
try:
    import yaml; d = yaml.safe_load(pathlib.Path(ssot).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
_t = d.get("top_module")
if isinstance(_t, dict): _t = _t.get("name")
top = _t or d.get("top") or ip
atpg = ((d.get("dft") or {}).get("atpg") or {})
print(atpg.get("fault_model", "stuck_at"), top, atpg.get("target_coverage", 0.90))
PY
)

# Fault CLI — invocation pattern (subject to AUCOHL/Fault docs):
#   fault [-m <model>] [-t <top>] -l <liberty> -o <test_out> <netlist>
fault \
  -m "${MODEL}" -t "${TOP}" \
  -l "${SKY130_LIB:-}" \
  -o "${TEST}" \
  "${SCAN}" 2>&1 | tee "${LOG}" || true
RC=${PIPESTATUS[0]:-1}

# Extract a coverage number — Fault prints something like "Coverage: 92.4%".
python3 - "${LOG}" "${TARGET}" "${COV}" <<'PY' || true
import json, re, sys, pathlib
log_p, tgt, out = sys.argv[1:4]
text = pathlib.Path(log_p).read_text(encoding="utf-8", errors="replace") if pathlib.Path(log_p).exists() else ""
m = re.search(r"(?:fault\s+)?coverage[: ]\s*([\d.]+)\s*%", text, re.I)
cov = float(m.group(1))/100.0 if m else None
target = float(tgt)
obj = {
  "fault_model": None, "coverage": cov, "target": target,
  "below_target": (cov is not None and cov < target),
  "patterns_path": None,
}
pathlib.Path(out).write_text(json.dumps(obj, indent=2), encoding="utf-8")
if cov is not None and cov < target:
    print(f"[DFT COVERAGE LOW] {cov*100:.2f}% < target {target*100:.0f}% — investigate untested logic")
PY
echo "[DFT] Fault rc=${RC} log=${LOG}"
exit 0   # ATPG is best-effort
