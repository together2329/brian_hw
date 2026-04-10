#!/usr/bin/env bash
TB="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

[ -z "${TB}" ] && TB=$(find . -maxdepth 3 -name "tb_*.sv" -o -name "tb_*.v" | head -1)
[ -z "${TB}" ] && { echo "No testbench found. Use /sim tb_<module>.sv"; exit 1; }

echo "Compiling: ${TB}"
if command -v iverilog &>/dev/null; then
    iverilog -g2012 -Wall -o /tmp/_sim.vvp "${TB}" 2>&1
    [ $? -ne 0 ] && { echo "Compile FAILED"; echo "${TS} sim=FAIL stage=compile" >> "${LOG}"; exit 1; }
    echo "Running..."
    OUT=$(vvp /tmp/_sim.vvp 2>&1)
    echo "${OUT}"
elif command -v verilator &>/dev/null; then
    OUT=$(verilator --binary --build -j 0 "${TB}" -o /tmp/_vsim 2>&1 && /tmp/_vsim 2>&1)
    echo "${OUT}"
else
    echo "No simulator found."; exit 1
fi

ERRORS=$(echo "${OUT}" | grep -c -i "^.*error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "^.*warning" || true)
PASS=$(echo "${OUT}" | grep -c "\[PASS\]" || true)
FAIL=$(echo "${OUT}" | grep -c "\[FAIL\]" || true)
STATUS="FAIL"; [ "${ERRORS}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ] && STATUS="PASS"

echo ""; echo "Result: ${ERRORS} errors, ${WARNINGS} warnings | ${PASS} PASS, ${FAIL} FAIL"
echo "${TS} sim=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS} fail=${FAIL} tb=${TB}" >> "${LOG}"
[ "${STATUS}" = "PASS" ] && echo "0 errors, 0 warnings"
[ "${STATUS}" = "PASS" ]
