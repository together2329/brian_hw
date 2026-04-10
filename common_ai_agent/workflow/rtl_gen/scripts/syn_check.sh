#!/usr/bin/env bash
# syn_check.sh — Synthesis feasibility check
FILE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

[ -z "${FILE}" ] && FILE=$(find . -maxdepth 1 -name "*.sv" | grep -v "tb_" | head -1)
[ -z "${FILE}" ] && { echo "No RTL file found."; exit 1; }

if command -v yosys &>/dev/null; then
    OUT=$(yosys -p "read_verilog -sv ${FILE}; synth" 2>&1)
    echo "${OUT}"
    ERRORS=$(echo "${OUT}" | grep -c "ERROR" || true)
    echo ""; echo "Yosys: ${ERRORS} errors"
    echo "${TS} syn_check=yosys errors=${ERRORS} file=${FILE}" >> "${LOG}"
    [ "${ERRORS}" -eq 0 ]
else
    # Fallback: strict iverilog compile
    echo "Yosys not found. Running strict iverilog compile..."
    OUT=$(iverilog -Wall -Winfloop -g2012 -o /dev/null "${FILE}" 2>&1)
    echo "${OUT}"
    ERRORS=$(echo "${OUT}" | grep -c "error" || true)
    echo ""; echo "iverilog strict: ${ERRORS} errors"
    echo "${TS} syn_check=iverilog errors=${ERRORS} file=${FILE}" >> "${LOG}"
    [ "${ERRORS}" -eq 0 ]
fi
