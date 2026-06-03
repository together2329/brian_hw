#!/usr/bin/env bash
TB="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
[ -z "${TB}" ] && TB=$(find . -maxdepth 3 -name "tb_*.sv" | head -1)
[ -z "${TB}" ] && { echo "No TB found."; exit 1; }

if command -v iverilog &>/dev/null; then
    OUT=$(iverilog -g2012 -Wall -o /tmp/_sim_compile_only.vvp "${TB}" 2>&1)
    RC=$?
else
    OUT=$(verilator --lint-only -Wall "${TB}" 2>&1); RC=$?
fi

echo "${OUT}"
ERRORS=$(echo "${OUT}" | grep -c -i "error" || true)
echo ""; echo "Compile: ${ERRORS} errors"
echo "${TS} compile errors=${ERRORS} tb=${TB}" >> "${LOG}"
[ "${RC}" -eq 0 ]
