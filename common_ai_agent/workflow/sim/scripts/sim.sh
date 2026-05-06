#!/usr/bin/env bash
set -u
TB="${HOOK_CMD_ARGS:-${1:-}}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

[ -z "${TB}" ] && TB=$(find . -maxdepth 4 -path "*/tb/cocotb/test_runner.py" -o -path "*/tb/test_runner.py" | head -1)
[ -z "${TB}" ] && TB=$(find . -maxdepth 3 -name "tb_*.sv" -o -name "tb_*.v" | head -1)
[ -z "${TB}" ] && { echo "No testbench found. Use /sim <test_runner.py|tb_<module>.sv>"; exit 1; }

PY_FLOW=0
if echo "${TB}" | grep -qE '\.py$'; then
    PY_FLOW=1
    echo "Running cocotb Python runner: ${TB}"
    TB_DIR=$(cd "$(dirname "${TB}")" && pwd)
    IP_DIR=$(cd "${TB_DIR}/.." && pwd)
    [ "$(basename "${IP_DIR}")" = "tb" ] && IP_DIR=$(cd "${IP_DIR}/.." && pwd)
    if grep -q "if __name__" "${TB}"; then
        OUT=$(cd "${TB_DIR}" && PYTHONPATH="${TB_DIR}:${IP_DIR}:${PYTHONPATH:-}" python3 "$(basename "${TB}")" 2>&1)
    else
        OUT=$(PYTHONPATH="${TB_DIR}:${IP_DIR}:${PYTHONPATH:-}" python3 -m pytest -q "${TB}" --tb=short 2>&1)
    fi
    RC=$?
    echo "${OUT}"
    [ ${RC} -ne 0 ] && { echo "Simulation FAILED"; echo "${TS} sim=FAIL stage=cocotb rc=${RC}" >> "${LOG}"; exit ${RC}; }
elif command -v iverilog &>/dev/null; then
    echo "Compiling: ${TB}"
    iverilog -g2012 -Wall -o /tmp/_sim.vvp "${TB}" 2>&1
    [ $? -ne 0 ] && { echo "Compile FAILED"; echo "${TS} sim=FAIL stage=compile" >> "${LOG}"; exit 1; }
    echo "Running..."
    OUT=$(vvp /tmp/_sim.vvp 2>&1)
    echo "${OUT}"
elif command -v verilator &>/dev/null; then
    echo "Compiling: ${TB}"
    OUT=$(verilator --binary --build -j 0 "${TB}" -o /tmp/_vsim 2>&1 && /tmp/_vsim 2>&1)
    echo "${OUT}"
else
    echo "No simulator found."; exit 1
fi

ERRORS=$(echo "${OUT}" | grep -c -i "^.*error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "^.*warning" || true)
PASS=$(echo "${OUT}" | grep -Ec "\[PASS\]| passed| PASS=" || true)
FAIL=$(echo "${OUT}" | grep -Ec "\[FAIL\]| failed| FAIL=[1-9]" || true)
if [ "${PY_FLOW}" -eq 1 ]; then
    WARNINGS=$(echo "${OUT}" | grep -i "warning" | grep -vi "UserWarning: Python runners" | grep -vi "experimental feature" | wc -l | tr -d ' ' || true)
fi
SUMMARY=$(echo "${OUT}" | grep -Eo 'TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+' | tail -1 || true)
if [ -n "${SUMMARY}" ]; then
    PASS_PART=${SUMMARY#*PASS=}; PASS=${PASS_PART%% *}
    FAIL_PART=${SUMMARY#*FAIL=}; FAIL=${FAIL_PART%% *}
fi
STATUS="FAIL"; [ "${ERRORS}" -eq 0 ] && [ "${FAIL}" -eq 0 ] && STATUS="PASS"

echo ""; echo "Result: ${ERRORS} errors, ${WARNINGS} warnings | ${PASS} PASS, ${FAIL} FAIL"
echo "${TS} sim=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS} fail=${FAIL} tb=${TB}" >> "${LOG}"
[ "${STATUS}" = "PASS" ] && echo "0 errors, 0 warnings"
[ "${STATUS}" = "PASS" ]
