#!/usr/bin/env bash
echo "${TOOL_OUTPUT:-}" | grep -q "0 errors, 0 warnings" && exit 0
ERRORS=$(echo "${TOOL_OUTPUT}" | grep -oP '\d+ error' | head -1)
WARNINGS=$(echo "${TOOL_OUTPUT}" | grep -oP '\d+ warning' | head -1)
echo "Sim not passing: ${ERRORS:-?}, ${WARNINGS:-?}. Expected: 0 errors, 0 warnings"
exit 1
