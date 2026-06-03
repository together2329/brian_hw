#!/usr/bin/env bash
# coverage_vcd_merge.sh — Wrap vcd_merge.py for the slash command.
# Discovers all *.vcd files under <DUT>/ (or under <DUT>/sim/, <DUT>/cocotb/sim_build/)
# and concat-merges them into <DUT>/cov/merged.vcd.
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
DUT="${DUT// /}"
MODE="concat"

# Allow `--mode <m>` override
for ((i=1; i<=$#; i++)); do
    if [ "${!i}" = "--mode" ]; then
        j=$((i+1))
        MODE="${!j}"
    fi
done

# Locate the python adapter — script lives in workflow/coverage/scripts/,
# adapters lives in workflow/coverage/adapters/.
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER="${SCRIPT_DIR}/../adapters/vcd_merge.py"
if [ ! -f "${ADAPTER}" ]; then
    echo "ERROR: adapter not found: ${ADAPTER}"
    exit 1
fi

OUT_DIR="${DUT}/cov"
OUT="${OUT_DIR}/merged.vcd"
mkdir -p "${OUT_DIR}"

# Discover .vcd files in priority order. Common locations:
#   <DUT>/sim/*.vcd                    (iverilog standalone)
#   <DUT>/cocotb/sim_build/*.vcd       (cocotb default)
#   <DUT>/sim/cov/*.vcd                (test-name partitioned)
VCDS=()
while IFS= read -r line; do
    [ -n "${line}" ] && VCDS+=("${line}")
done < <(find "${DUT}" -name "*.vcd" -not -path "*/cov/merged.vcd" 2>/dev/null | sort)

if [ ${#VCDS[@]} -eq 0 ]; then
    echo "ERROR: no .vcd files found under ${DUT}/"
    echo "  Common locations checked:"
    echo "    ${DUT}/sim/*.vcd"
    echo "    ${DUT}/cocotb/sim_build/*.vcd"
    echo "  Run a simulation first (iverilog or cocotb with WAVES=1)."
    exit 1
fi

if [ ${#VCDS[@]} -eq 1 ]; then
    echo "Only 1 .vcd found (${VCDS[0]}) — nothing to merge."
    cp "${VCDS[0]}" "${OUT}"
    echo "Copied to ${OUT}"
    exit 0
fi

echo "=== VCD merge (${MODE}) ==="
echo "DUT     : ${DUT}"
echo "Inputs  : ${#VCDS[@]}"
printf "  - %s\n" "${VCDS[@]}"
echo "Output  : ${OUT}"
echo ""

python3 "${ADAPTER}" --mode "${MODE}" --out "${OUT}" "${VCDS[@]}"
RC=$?

if [ ${RC} -eq 0 ]; then
    echo ""
    echo "Next: open in gtkwave  →  gtkwave ${OUT}"
    echo "      or use /coverage-vcd-toggle to extract toggle coverage from this VCD"
fi
exit ${RC}
