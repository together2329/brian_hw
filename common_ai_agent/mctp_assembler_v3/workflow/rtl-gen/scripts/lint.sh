#!/usr/bin/env bash
# lint.sh — RTL lint for rtl_gen workspace
FILE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

[ -z "${FILE}" ] && FILE=$(find . -maxdepth 2 \( -name "*.sv" -o -name "*.v" \) | grep -v "^./tb_" | grep -v "^./tc_" | head -5)
[ -z "${FILE}" ] && { echo "No RTL files found."; exit 1; }

ERRORS=0; WARNINGS=0
for F in ${FILE}; do
    if command -v verilator &>/dev/null; then
        OUT=$(verilator --lint-only -Wall "${F}" 2>&1)
    elif command -v iverilog &>/dev/null; then
        OUT=$(iverilog -Wall -g2012 -o /dev/null "${F}" 2>&1)
    else
        echo "No lint tool (install verilator or iverilog)"; exit 1
    fi
    ERR=$(echo "${OUT}" | grep -c -i "error" || true)
    WARN=$(echo "${OUT}" | grep -c -i "warning" || true)
    ERRORS=$((ERRORS+ERR)); WARNINGS=$((WARNINGS+WARN))
    [ -n "${OUT}" ] && echo "--- ${F} ---" && echo "${OUT}" || echo "--- ${F}: OK ---"
done
echo ""; echo "Lint: ${ERRORS} errors, ${WARNINGS} warnings"
echo "${TS} lint errors=${ERRORS} warnings=${WARNINGS}" >> "${LOG}"
[ "${ERRORS}" -eq 0 ]
