#!/usr/bin/env bash
# error_capture.sh — Snapshot errors from tool output to benchmark log
# Triggered: after run_command when output contains Error/FAILED

LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ITER="${HOOK_ITERATION:-?}"

# Extract first 5 error lines from tool output
ERRORS=$(echo "${HOOK_TOOL_OUTPUT}" | grep -i -E "^.*(error|failed).*$" | head -5)

if [ -n "${ERRORS}" ]; then
    echo "${TS} iter=${ITER} ERRORS:" >> "${LOG}"
    echo "${ERRORS}" | sed 's/^/  /' >> "${LOG}"
fi
