#!/usr/bin/env bash
# check_sim_pass.sh — Validator: TOOL_OUTPUT must contain "0 errors, 0 warnings"
OUTPUT="${TOOL_OUTPUT:-}"
echo "${OUTPUT}" | grep -q "0 errors, 0 warnings" && exit 0
ERRORS=$(echo "${OUTPUT}" | grep -oP '\d+ error' | head -1)
WARNINGS=$(echo "${OUTPUT}" | grep -oP '\d+ warning' | head -1)
echo "Simulation not passing: ${ERRORS:-?}, ${WARNINGS:-?}"
echo "Expected: 0 errors, 0 warnings"
exit 1
