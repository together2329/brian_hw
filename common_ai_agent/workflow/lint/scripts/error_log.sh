#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
LINES=$(echo "${HOOK_TOOL_OUTPUT}" | grep -i -E "error|warning" | head -10)
[ -n "${LINES}" ] && echo "${TS} lint_issues:" >> "${LOG}" && echo "${LINES}" | sed 's/^/  /' >> "${LOG}"
