#!/usr/bin/env bash
# lint.sh — RTL lint using iverilog (or verilator if available)
# Usage: bash scripts/lint.sh [file.v|file.sv]
# /lint command handler

FILE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

if [ -z "${FILE}" ]; then
    # Lint all .v and .sv files in current directory
    FILES=$(find . -maxdepth 2 -name "*.v" -o -name "*.sv" | grep -v tb_ | head -20)
else
    FILES="${FILE}"
fi

if [ -z "${FILES}" ]; then
    echo "No Verilog/SystemVerilog files found."
    exit 1
fi

ERRORS=0
WARNINGS=0

for F in ${FILES}; do
    if command -v verilator &>/dev/null; then
        OUT=$(verilator --lint-only -Wall "${F}" 2>&1)
    elif command -v iverilog &>/dev/null; then
        OUT=$(iverilog -Wall -o /dev/null "${F}" 2>&1)
    else
        echo "Warning: No lint tool found (install verilator or iverilog)"
        exit 1
    fi

    ERR=$(echo "${OUT}" | grep -c -i "error" || true)
    WARN=$(echo "${OUT}" | grep -c -i "warning" || true)
    ERRORS=$((ERRORS + ERR))
    WARNINGS=$((WARNINGS + WARN))

    if [ -n "${OUT}" ]; then
        echo "--- ${F} ---"
        echo "${OUT}"
    else
        echo "--- ${F}: OK ---"
    fi
done

echo ""
echo "Lint result: ${ERRORS} errors, ${WARNINGS} warnings"
echo "${TS} lint errors=${ERRORS} warnings=${WARNINGS}" >> "${LOG}"

[ "${ERRORS}" -eq 0 ]
