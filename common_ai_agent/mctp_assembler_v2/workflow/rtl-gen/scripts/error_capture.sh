#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ERRORS=$(echo "${HOOK_TOOL_OUTPUT}" | grep -i -E "error|failed" | head -5)
[ -n "${ERRORS}" ] && echo "${TS} rtl_errors:" >> "${LOG}" && echo "${ERRORS}" | sed 's/^/  /' >> "${LOG}"
