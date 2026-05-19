#!/usr/bin/env bash
# run_route.sh — Global + detailed route + SPEF extraction.
# Args: <ip>. Reads cts.def + cts.v. Writes routed.def + routed.v + routed.spef.
set -uo pipefail

if [ $# -eq 0 ] && [ -n "${HOOK_CMD_ARGS:-}" ]; then
  # shellcheck disable=SC2086
  set -- ${HOOK_CMD_ARGS}
fi

DIR="$(dirname "$0")"
. "${DIR}/_pnr_common.sh"

IP="${1:-}"; [ -z "${IP}" ] && { echo "[PNR] usage: run_route.sh <ip>" >&2; exit 2; }

pnr_check_tools || exit $?
TOP=$(pnr_top_from_ssot "${IP}")
SDC="${IP}/sta/out/${IP}.sdc"
CTS_DEF="${IP}/pnr/out/cts.def"
CTS_NET="${IP}/pnr/out/cts.v"
ROUTE_DEF="${IP}/pnr/out/cts_route.def"
TCL="${IP}/pnr/tcl/route.tcl"
DEF="${IP}/pnr/out/routed.def"
NET="${IP}/pnr/out/routed.v"
SPEF="${IP}/pnr/out/routed.spef"
DRC="${IP}/pnr/out/drc.rpt"
LOG="${IP}/pnr/out/pnr.log"
mkdir -p "${IP}/pnr/tcl" "${IP}/pnr/out"

pnr_check_stale "CTS"     "${CTS_DEF}" "${DEF}"  || exit $?
pnr_check_stale "CTS-NET" "${CTS_NET}" "${NET}"  || exit $?

python3 - "${CTS_DEF}" "${ROUTE_DEF}" <<'PY'
import pathlib
import re
import sys

src, dst = map(pathlib.Path, sys.argv[1:3])
const_nets = {"zero_", "one_", "const0", "const1", "_zero_", "_one_"}
changed = 0
out = []
for line in src.read_text(encoding="utf-8", errors="replace").splitlines():
    match = re.match(r"^(\s*-\s+)(\S+)(\b.*\+\s+USE\s+)(GROUND|POWER)(\s*;.*)$", line)
    if match and match.group(2).lower() in const_nets:
        line = "".join([match.group(1), match.group(2), match.group(3), "SIGNAL", match.group(5)])
        changed += 1
    out.append(line)
dst.write_text("\n".join(out) + "\n", encoding="utf-8")
if changed:
    print(f"[PNR-ROUTE] normalized {changed} constant tie net(s) to USE SIGNAL for detailed_route")
PY

cat > "${TCL}" <<EOF
read_lef ${SKY130_TLEF}
read_lef ${SKY130_LEF}
read_liberty ${SKY130_LIB}
read_def ${ROUTE_DEF}
read_sdc ${SDC}

global_route -guide_file ${IP}/pnr/out/route.guide
detailed_route -output_drc ${DRC}
write_def ${DEF}
write_verilog ${NET}

# Parasitic extraction → SPEF for /sta-post sign-off.
define_process_corner -ext_model_index 0 X
extract_parasitics -ext_model_file \$::env(SKY130_RCX_RULES) -corner_cnt 1
write_spef ${SPEF}
exit
EOF

echo "[PNR-ROUTE] openroad → ${DEF} + ${NET} + ${SPEF}"
openroad -no_init -exit "${TCL}" 2>&1 | tee -a "${LOG}"
RC=${PIPESTATUS[0]}

# DRC summary
DRC_COUNT=0
if [ -f "${DRC}" ]; then
  DRC_COUNT=$(grep -cE '^violation' "${DRC}" || true)
  DRC_COUNT="${DRC_COUNT:-0}"
fi
python3 - "${IP}/pnr/out/drc.json" "${DRC_COUNT}" "${DRC}" <<'PY' || true
import json, sys, pathlib, re
out, count, rpt = sys.argv[1:4]
violations = []
if pathlib.Path(rpt).exists():
    text = pathlib.Path(rpt).read_text(encoding="utf-8", errors="replace")
    for m in re.finditer(r"^violation .*$", text, re.M):
        if len(violations) < 10: violations.append(m.group(0))
pathlib.Path(out).write_text(
  json.dumps({"drc_count": int(count), "first_10": violations}, indent=2),
  encoding="utf-8",
)
PY

if [ "${RC}" -ne 0 ] || [ ! -s "${DEF}" ] || [ ! -s "${NET}" ]; then
  echo "[PNR-ROUTE] FAILED rc=${RC}" >&2; exit "${RC}"
fi
if [ ! -s "${SPEF}" ]; then
  echo "[PNR SPEF FAILED] ${SPEF} empty — sign-off STA cannot proceed" >&2; exit 12
fi
echo "[PNR HANDOFF] ${SPEF} ready  drc=${DRC_COUNT}  — run /sta-post"
