#!/usr/bin/env bash
# lint_file.sh — Run lint on a single file
FILE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
[ -z "${FILE}" ] && { echo "Usage: /lint-file <file.sv>"; exit 1; }
[ ! -f "${FILE}" ] && { echo "File not found: ${FILE}"; exit 1; }

if command -v verilator &>/dev/null; then
    OUT=$(verilator --lint-only -Wall "${FILE}" 2>&1)
elif command -v iverilog &>/dev/null; then
    OUT=$(iverilog -Wall -g2012 -o /dev/null "${FILE}" 2>&1)
else
    echo "No lint tool found"; exit 1
fi

ERR=$(echo "${OUT}" | grep -c -i "error" || true)
WARN=$(echo "${OUT}" | grep -c -i "warning" || true)
[ -n "${OUT}" ] && echo "${OUT}" || echo "OK — no issues"
echo ""; echo "${FILE}: ${ERR} errors, ${WARN} warnings"
echo "${TS} lint_file=${FILE} errors=${ERR} warnings=${WARN}" >> "${LOG}"
[ "${ERR}" -eq 0 ]
