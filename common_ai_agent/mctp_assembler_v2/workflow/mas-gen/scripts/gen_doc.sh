#!/usr/bin/env bash
# gen_doc.sh — Generate module spec doc skeleton from RTL source
MODULE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

SRC="${MODULE:-module}.sv"
OUT="${MODULE:-module}_spec.md"

if [ ! -f "${SRC}" ]; then
    echo "Error: ${SRC} not found. Run /gen-rtl first."
    exit 1
fi

# Extract module name, ports, parameters from RTL
MOD_NAME=$(grep -oP 'module\s+\K\w+' "${SRC}" | head -1)
PARAMS=$(grep -oP 'parameter\s+\w+.*' "${SRC}" | sed 's/^/  - /')
INPUTS=$(grep -oP 'input\s+.*' "${SRC}" | sed 's/^/  - /')
OUTPUTS=$(grep -oP 'output\s+.*' "${SRC}" | sed 's/^/  - /')

cat > "${OUT}" << EOF
# Module: ${MOD_NAME:-${MODULE}}

## Overview
<!-- TODO: describe module function -->

## Parameters
${PARAMS:-  (none)}

## Port List

### Inputs
${INPUTS:-  (none)}

### Outputs
${OUTPUTS:-  (none)}

## Functional Description
<!-- TODO: describe operation, state machine, data path -->

## Timing Diagram
<!-- TODO: add waveform description or ASCII timing -->

## Design Notes
<!-- TODO: implementation decisions, known limitations -->

## Simulation Results
<!-- Auto-fill after sim passes -->
- Status: PENDING
- Test cases: TBD
EOF

echo "Generated: ${OUT}"
echo "${TS} doc_gen module=${MODULE} output=${OUT}" >> "${LOG}"
