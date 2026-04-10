#!/usr/bin/env bash
# benchmark_report.sh — Print session benchmark summary
# Used by /report command

LOG="${BENCHMARK_LOG:-.benchmark}"

if [ ! -f "${LOG}" ]; then
    echo "No benchmark data found. Run simulation first."
    exit 0
fi

TOTAL_ITERS=$(grep -c "iter=" "${LOG}" 2>/dev/null || echo 0)
SIM_PASS=$(grep -c "sim=PASS" "${LOG}" 2>/dev/null || echo 0)
SIM_FAIL=$(grep -c "sim=FAIL" "${LOG}" 2>/dev/null || echo 0)
WRITES=$(grep -c "^.*write tool=" "${LOG}" 2>/dev/null || echo 0)
ERROR_SNAPS=$(grep -c "ERRORS:" "${LOG}" 2>/dev/null || echo 0)

FIRST_TS=$(head -1 "${LOG}" | cut -d' ' -f1)
LAST_TS=$(tail -1 "${LOG}" | cut -d' ' -f1)

echo "=== RTL Session Benchmark Report ==="
echo "Period     : ${FIRST_TS} → ${LAST_TS}"
echo "Iterations : ${TOTAL_ITERS}"
echo "File writes: ${WRITES}"
echo "Sim PASS   : ${SIM_PASS}"
echo "Sim FAIL   : ${SIM_FAIL}"
echo "Error snaps: ${ERROR_SNAPS}"
echo "Log file   : ${LOG}"
