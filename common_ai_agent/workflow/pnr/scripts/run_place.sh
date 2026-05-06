#!/usr/bin/env bash
# run_place.sh — Global + detailed placement.
# Args: <ip>. Reads floorplan.def. Writes placed.def.
set -uo pipefail

DIR="$(dirname "$0")"
. "${DIR}/_pnr_common.sh"

IP="${1:-}"; [ -z "${IP}" ] && { echo "[PNR] usage: run_place.sh <ip>" >&2; exit 2; }

pnr_check_tools || exit $?
NETLIST=$(pnr_check_handoff "${IP}") || exit $?
TOP=$(pnr_top_from_ssot "${IP}")
SDC="${IP}/sta/out/${IP}.sdc"
FP="${IP}/pnr/out/floorplan.def"
TCL="${IP}/pnr/tcl/place.tcl"
DEF="${IP}/pnr/out/placed.def"
LOG="${IP}/pnr/out/pnr.log"
mkdir -p "${IP}/pnr/tcl" "${IP}/pnr/out"

pnr_check_stale "FLOORPLAN" "${FP}" "${DEF}" || exit $?

DENSITY=$(python3 - "${IP}/yaml/${IP}.ssot.yaml" <<'PY'
import sys, pathlib
try:
    import yaml; d = yaml.safe_load(pathlib.Path(sys.argv[1]).read_text()) or {}
except Exception: d = {}
print((d.get("pnr") or {}).get("global_density", 0.65))
PY
)

cat > "${TCL}" <<EOF
read_lef ${SKY130_TLEF}
read_lef ${SKY130_LEF}
read_liberty ${SKY130_LIB}
read_def ${FP}
read_sdc ${SDC}

global_placement -density ${DENSITY}
detailed_placement
check_placement
write_def ${DEF}
report_design_area
exit
EOF

echo "[PNR-PLACE] openroad → ${DEF}  (density=${DENSITY})"
openroad -no_init -exit "${TCL}" 2>&1 | tee -a "${LOG}"
RC=${PIPESTATUS[0]}

if grep -qE "WARN: .*overlap|ERROR.*placement" "${LOG}"; then
  echo "[PNR PLACE OVERLAPS] check_placement found overlaps — usually utilization too high" >&2
  exit 11
fi
if [ "${RC}" -ne 0 ] || [ ! -s "${DEF}" ]; then
  echo "[PNR-PLACE] FAILED rc=${RC}" >&2; exit "${RC}"
fi

# Record density for the report.
python3 - "${LOG}" "${IP}/pnr/out/density.json" <<'PY' || true
import re, json, sys, pathlib
log = pathlib.Path(sys.argv[1]).read_text(errors="replace")
m = re.search(r"design area\s+(\d+(?:\.\d+)?)\s+u\^2.*?(\d+)\s*%\s*utilization", log, re.S)
obj = {"design_area_um2": float(m.group(1)) if m else None,
       "utilization_pct": int(m.group(2)) if m else None}
pathlib.Path(sys.argv[2]).write_text(json.dumps(obj, indent=2))
PY
echo "[PNR-PLACE HANDOFF] ${DEF} ready — run /pnr-cts"
