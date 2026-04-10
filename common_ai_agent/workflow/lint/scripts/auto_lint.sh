#!/usr/bin/env bash
# auto_lint.sh — Auto-triggered after every .sv/.v write; quick lint of changed file
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ARGS="${HOOK_TOOL_ARGS:-}"
FILE=$(echo "${ARGS}" | grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\.(?:sv|v)' | head -1)
[ -z "${FILE}" ] || [ ! -f "${FILE}" ] && exit 0

if command -v verilator &>/dev/null; then
    OUT=$(verilator --lint-only -Wall "${FILE}" 2>&1)
else
    OUT=$(iverilog -Wall -g2012 -o /dev/null "${FILE}" 2>&1)
fi
ERR=$(echo "${OUT}" | grep -c -i "error" || true)
WARN=$(echo "${OUT}" | grep -c -i "warning" || true)
echo "${TS} auto_lint file=${FILE} errors=${ERR} warnings=${WARN}" >> "${LOG}"
