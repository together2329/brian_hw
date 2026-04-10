#!/usr/bin/env bash
# check_sim_pass.sh — Validator script for simulation todo tasks
# Returns 0 (pass) if TOOL_OUTPUT contains "0 errors, 0 warnings"
# Returns 1 (fail) with message if not

OUTPUT="${TOOL_OUTPUT:-}"

if echo "${OUTPUT}" | grep -q "0 errors, 0 warnings"; then
    exit 0
fi

ERRORS=$(echo "${OUTPUT}" | grep -oP '\d+ error' | head -1)
WARNINGS=$(echo "${OUTPUT}" | grep -oP '\d+ warning' | head -1)

echo "Simulation not passing: ${ERRORS:-unknown errors}, ${WARNINGS:-unknown warnings}"
echo "Expected: 0 errors, 0 warnings"
exit 1
