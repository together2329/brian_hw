#!/usr/bin/env bash
# preflight.sh — Validate OpenROAD/PDK/handoff inputs before PnR.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

DIR="$(dirname "$0")"
. "${DIR}/_pnr_common.sh"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[PNR PREFLIGHT] usage: preflight.sh <ip>" >&2; exit 2; fi

echo "[PNR PREFLIGHT] cwd=$(pwd -P)"
echo "[PNR PREFLIGHT] PDK_ROOT=${PDK_ROOT:-}"
echo "[PNR PREFLIGHT] SKY130_PDK_ROOT=${SKY130_PDK_ROOT:-}"

pnr_check_tools || exit $?

if [ ! -d "${IP}" ]; then echo "[PNR PREFLIGHT] IP dir missing: ${IP}" >&2; exit 2; fi
SSOT="${IP}/yaml/${IP}.ssot.yaml"
if [ ! -f "${SSOT}" ]; then echo "[PNR PREFLIGHT] SSOT missing: ${SSOT}" >&2; exit 2; fi
NETLIST="$(pnr_check_handoff "${IP}")" || exit $?
echo "[PNR PREFLIGHT] netlist=${NETLIST}"
echo "[PNR PREFLIGHT] sdc=${IP}/sta/out/${IP}.sdc"

PARAMS="$(python3 - "${SSOT}" <<'PY'
import pathlib, sys

try:
    import yaml
except Exception as exc:
    print(f"[PNR PREFLIGHT] PyYAML required to read SSOT: {exc}", file=sys.stderr)
    raise SystemExit(2)

doc = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text()) or {}
pnr = doc.get("pnr") or {}
required = [
    "utilization_pct",
    "aspect_ratio",
    "core_space_um",
    "global_density",
    "io_layers.horizontal",
    "io_layers.vertical",
]
missing = []
for key in required:
    cur = pnr
    for part in key.split("."):
        cur = cur.get(part) if isinstance(cur, dict) else None
    if cur in (None, ""):
        missing.append(f"pnr.{key}")
if missing:
    print("[PNR SSOT TBD REPORT] missing physical constraints:", file=sys.stderr)
    for item in missing:
        print(f"  - {item}", file=sys.stderr)
    raise SystemExit(7)
io = pnr.get("io_layers") or {}
cts = pnr.get("cts_buf_list") or "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
if isinstance(cts, list):
    cts = ",".join(str(item).strip() for item in cts if str(item).strip())
else:
    cts = ",".join(str(cts).replace(",", " ").split())
print(
    pnr.get("utilization_pct"),
    pnr.get("aspect_ratio"),
    pnr.get("core_space_um"),
    pnr.get("global_density"),
    io.get("horizontal"),
    io.get("vertical"),
    cts,
)
PY
)" || exit $?
read UTIL AR CSPACE DENSITY HOR VER CTS_BUF <<<"${PARAMS}"

pnr_check_io_layers "${HOR}" "${VER}" || exit $?

echo "[PNR PREFLIGHT] utilization=${UTIL}% aspect_ratio=${AR} core_space=${CSPACE}um density=${DENSITY}"
echo "[PNR PREFLIGHT] io_layers horizontal=${HOR} vertical=${VER}"
echo "[PNR PREFLIGHT] cts_buf_list=${CTS_BUF//,/ }"
echo "[PNR PREFLIGHT] OK"
