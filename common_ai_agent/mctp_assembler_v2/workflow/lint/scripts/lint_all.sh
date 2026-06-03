#!/usr/bin/env bash
# lint_all.sh — Run lint on all .sv/.v files (exclude tb_/tc_)
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

FILES=$(find . -maxdepth 3 \( -name "*.sv" -o -name "*.v" \) \
        | grep -v "tb_\|tc_\|_wave\|/sim/" | sort)
[ -z "${FILES}" ] && { echo "No RTL files found."; exit 1; }

TOTAL_ERR=0; TOTAL_WARN=0
for F in ${FILES}; do
    if command -v verilator &>/dev/null; then
        OUT=$(verilator --lint-only -Wall "${F}" 2>&1)
    elif command -v iverilog &>/dev/null; then
        OUT=$(iverilog -Wall -g2012 -o /dev/null "${F}" 2>&1)
    else
        echo "No lint tool found (install verilator or iverilog)"; exit 1
    fi
    ERR=$(echo "${OUT}" | grep -c -i "^.*error" || true)
    WARN=$(echo "${OUT}" | grep -c -i "^.*warning" || true)
    TOTAL_ERR=$((TOTAL_ERR+ERR)); TOTAL_WARN=$((TOTAL_WARN+WARN))
    if [ -n "${OUT}" ]; then
        echo "=== ${F} === (${ERR} errors, ${WARN} warnings)"
        echo "${OUT}"
    else
        echo "=== ${F} === OK"
    fi
done

echo ""
echo "TOTAL: ${TOTAL_ERR} errors, ${TOTAL_WARN} warnings"
echo "${TS} lint_all errors=${TOTAL_ERR} warnings=${TOTAL_WARN}" >> "${LOG}"
[ "${TOTAL_ERR}" -eq 0 ]
