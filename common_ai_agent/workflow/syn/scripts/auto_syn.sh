#!/usr/bin/env bash
# auto_syn.sh — End-to-end synthesis driver. Single entry point for /syn.
# Args: <ip_name>
# Pipeline: write run.ys → yosys → sanity gate → area.json → syn.report.md
set -uo pipefail

PDK_ENV="$(cd "$(dirname "$0")/../.." && pwd -P)/scripts/pdk_env.sh"
[ -f "${PDK_ENV}" ] && source "${PDK_ENV}"

IP="${1:-}"
if [ -z "${IP}" ]; then echo "[SYN] usage: auto_syn.sh <ip_name>" >&2; exit 2; fi
if [ ! -d "${IP}" ]; then echo "[SYN] no such IP dir: ${IP}" >&2; exit 2; fi

DIR="$(dirname "$0")"
OUT="${IP}/syn/out"
mkdir -p "${OUT}"

# Tool / PDK preflight
if ! command -v yosys >/dev/null 2>&1; then
  echo "[SYN TOOL MISSING] yosys not on PATH" >&2; exit 3
fi
LIB="${SKY130_LIB:-}"
if [ ! -r "${LIB}" ]; then
  echo "[SYN MISSING PDK] \$SKY130_LIB unreadable: ${LIB}" >&2; exit 4
fi
export SKY130_LIB="${LIB}"

bash "${DIR}/write_yosys_script.sh" "${IP}" || exit $?
bash "${DIR}/run_yosys.sh"          "${IP}" || exit $?
bash "${DIR}/check_unmapped.sh"     "${IP}" || exit $?
bash "${DIR}/parse_area.sh"         "${IP}" || exit $?
bash "${DIR}/write_report.sh"       "${IP}" || exit $?

NETLIST="${OUT}/synth.v"
CELLS=$(python3 -c "import json; d=json.load(open('${OUT}/area.json')); print(d.get('total_cells',0))" 2>/dev/null || echo 0)
SEQ=$(python3   -c "import json; d=json.load(open('${OUT}/area.json')); print(d['by_kind']['sequential']['cells'])" 2>/dev/null || echo 0)
AREA=$(python3  -c "import json; d=json.load(open('${OUT}/area.json')); print(d.get('total_area_um2',0))" 2>/dev/null || echo 0)
echo "[SYN HANDOFF] ${NETLIST} ready (cells=${CELLS}, FFs=${SEQ}, area=${AREA} μm²) — run /sta"
