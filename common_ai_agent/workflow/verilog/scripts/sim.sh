#!/usr/bin/env bash
# sim.sh — Run Verilog/SystemVerilog simulation
# Usage: bash scripts/sim.sh [testbench.sv]
# /sim command handler

TB="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

if [ -z "${TB}" ]; then
    TB=$(find . -maxdepth 2 -name "tb_*.sv" -o -name "tb_*.v" | head -1)
fi

if [ -z "${TB}" ]; then
    echo "No testbench found. Provide: /sim tb_<module>.sv"
    exit 1
fi

echo "Running simulation: ${TB}"

if command -v vvp &>/dev/null && command -v iverilog &>/dev/null; then
    # Compile
    iverilog -g2012 -o /tmp/_sim_out.vvp "${TB}" 2>&1
    COMPILE_RC=$?
    if [ "${COMPILE_RC}" -ne 0 ]; then
        echo "Compilation FAILED"
        echo "${TS} sim=FAIL stage=compile tb=${TB}" >> "${LOG}"
        exit 1
    fi
    # Run
    OUT=$(vvp /tmp/_sim_out.vvp 2>&1)
    echo "${OUT}"
elif command -v verilator &>/dev/null; then
    OUT=$(verilator --binary --build -j 0 "${TB}" -o /tmp/_sim_verilator && /tmp/_sim_verilator 2>&1)
    echo "${OUT}"
else
    echo "Error: No simulation tool found (install iverilog+vvp or verilator)"
    exit 1
fi

ERRORS=$(echo "${OUT}" | grep -c -i "error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "warning" || true)

echo ""
echo "Simulation result: ${ERRORS} errors, ${WARNINGS} warnings"

if [ "${ERRORS}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ]; then
    STATUS="PASS"
else
    STATUS="FAIL"
fi

echo "${TS} sim=${STATUS} errors=${ERRORS} warnings=${WARNINGS} tb=${TB}" >> "${LOG}"

echo ""
echo "0 errors, 0 warnings" | grep -q "0 errors, 0 warnings" && [ "${STATUS}" = "PASS" ] && echo "PASS: 0 errors, 0 warnings"

[ "${STATUS}" = "PASS" ]
