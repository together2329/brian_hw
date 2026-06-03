#!/usr/bin/env bash
# check_lint_pass.sh — Validator for lint stage
# Returns 0 if lint passed (0 errors), 1 otherwise
# Used as validator in converge loop criteria checks

OUTPUT="${TOOL_OUTPUT:-}"

if echo "$OUTPUT" | grep -qi "0 error"; then
    echo "Lint PASS: 0 errors"
    exit 0
fi

ERRORS=$(echo "$OUTPUT" | grep -oiP '\d+(?= error)' | head -1)
WARNINGS=$(echo "$OUTPUT" | grep -oiP '\d+(?= warning)' | head -1)
echo "Lint FAIL: ${ERRORS:-?} errors, ${WARNINGS:-?} warnings"
exit 1
