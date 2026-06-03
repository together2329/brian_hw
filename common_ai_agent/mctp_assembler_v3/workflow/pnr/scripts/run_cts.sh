#!/usr/bin/env bash
# run_cts.sh — Clock tree synthesis. Reads placed.def. Writes cts.def + cts.v.
# Args: <ip>
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

DIR="$(dirname "$0")"
. "${DIR}/_pnr_common.sh"

IP="${1:-}"; [ -z "${IP}" ] && { echo "[PNR] usage: run_cts.sh <ip>" >&2; exit 2; }

pnr_check_tools || exit $?
NETLIST=$(pnr_check_handoff "${IP}") || exit $?
TOP=$(pnr_top_from_ssot "${IP}")
SDC="${IP}/sta/out/${IP}.sdc"
PLACED="${IP}/pnr/out/placed.def"
TCL="${IP}/pnr/tcl/cts.tcl"
DEF="${IP}/pnr/out/cts.def"
NET="${IP}/pnr/out/cts.v"
LOG="${IP}/pnr/out/pnr.log"
mkdir -p "${IP}/pnr/tcl" "${IP}/pnr/out"

pnr_check_stale "PLACE" "${PLACED}" "${DEF}" || exit $?

BUFLIST=$(python3 - "${IP}/yaml/${IP}.ssot.yaml" <<'PY'
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text(encoding="utf-8", errors="replace")) or {}
except Exception: d = {}
bufs = (d.get("pnr") or {}).get("cts_buf_list") or "sky130_fd_sc_hd__clkbuf_4 sky130_fd_sc_hd__clkbuf_8"
if isinstance(bufs, list):
    print(" ".join(str(item).strip() for item in bufs if str(item).strip()))
else:
    print(" ".join(str(bufs).replace(",", " ").split()))
PY
)

cat > "${TCL}" <<EOF
read_lef ${SKY130_TLEF}
read_lef ${SKY130_LEF}
read_liberty ${SKY130_LIB}
read_def ${PLACED}
read_sdc ${SDC}

clock_tree_synthesis -buf_list "${BUFLIST}"
detailed_placement
write_def ${DEF}
write_verilog ${NET}
report_clock_skew
exit
EOF

echo "[PNR-CTS] openroad → ${DEF} + ${NET}"
openroad -no_init -exit "${TCL}" 2>&1 | tee -a "${LOG}"
RC=${PIPESTATUS[0]}
if [ "${RC}" -ne 0 ] || [ ! -s "${DEF}" ] || [ ! -s "${NET}" ]; then
  echo "[PNR-CTS] FAILED rc=${RC}" >&2; exit "${RC}"
fi
echo "[PNR-CTS HANDOFF] ${DEF}, ${NET} ready — run /pnr-route"
