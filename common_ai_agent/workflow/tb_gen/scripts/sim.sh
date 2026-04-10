#!/usr/bin/env bash
# sim.sh — Compile and run simulation for tb_gen workspace
TB="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

[ -z "${TB}" ] && TB=$(find . -maxdepth 2 -name "tb_*.sv" -o -name "tb_*.v" | head -1)
[ -z "${TB}" ] && { echo "No testbench found. Use /sim tb_<module>.sv"; exit 1; }

echo "Compiling: ${TB}"
if command -v iverilog &>/dev/null; then
    iverilog -g2012 -Wall -o /tmp/_tb_sim.vvp "${TB}" 2>&1
    [ $? -ne 0 ] && { echo "Compile FAILED"; echo "${TS} sim=FAIL stage=compile" >> "${LOG}"; exit 1; }
    OUT=$(vvp /tmp/_tb_sim.vvp 2>&1)
    echo "${OUT}"
elif command -v verilator &>/dev/null; then
    OUT=$(verilator --binary --build -j 0 "${TB}" -o /tmp/_tb_verilator 2>&1 && /tmp/_tb_verilator 2>&1)
    echo "${OUT}"
else
    echo "No sim tool found."; exit 1
fi

ERRORS=$(echo "${OUT}" | grep -c -i "error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "warning" || true)
PASS_CNT=$(echo "${OUT}" | grep -c "\[PASS\]" || true)
FAIL_CNT=$(echo "${OUT}" | grep -c "\[FAIL\]" || true)

echo ""
echo "Simulation: ${ERRORS} errors, ${WARNINGS} warnings"
echo "Tests: ${PASS_CNT} passed, ${FAIL_CNT} failed"

STATUS="FAIL"
[ "${ERRORS}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ] && STATUS="PASS"

echo "${TS} sim=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS_CNT} fail=${FAIL_CNT} tb=${TB}" >> "${LOG}"

[ "${STATUS}" = "PASS" ] && echo "0 errors, 0 warnings"
[ "${STATUS}" = "PASS" ]
