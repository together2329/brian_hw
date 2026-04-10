#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
OUT="sim_report.txt"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

LAST=$(grep "sim=" "${LOG}" 2>/dev/null | grep -v "stage=compile" | tail -1)
STATUS=$(echo "${LAST}" | grep -oP 'sim=\K\w+' || echo "UNKNOWN")
ERRORS=$(echo "${LAST}" | grep -oP 'errors=\K\d+' || echo "?")
WARNINGS=$(echo "${LAST}" | grep -oP 'warnings=\K\d+' || echo "?")
PASS=$(echo "${LAST}" | grep -oP 'pass=\K\d+' || echo "?")
FAIL=$(echo "${LAST}" | grep -oP 'fail=\K\d+' || echo "?")
TB=$(echo "${LAST}" | grep -oP 'tb=\K\S+' || echo "?")
ITERS=$(grep -c "sim_capture=" "${LOG}" 2>/dev/null || echo "?")
TOOL=$(command -v iverilog &>/dev/null && echo "iverilog+vvp" || echo "verilator")

cat > "${OUT}" << EOF
=== Simulation Report ===
Date      : ${TS}
TB        : ${TB}
Tool      : ${TOOL}
Result    : ${STATUS}
Errors    : ${ERRORS}
Warnings  : ${WARNINGS}
Tests     : ${PASS} passed, ${FAIL} failed
Iterations: ${ITERS}

[FAIL details]
$(grep "\[FAIL\]" "${LOG}" 2>/dev/null | tail -20 || echo "NONE")
EOF

echo "Written: ${OUT}"
cat "${OUT}"
