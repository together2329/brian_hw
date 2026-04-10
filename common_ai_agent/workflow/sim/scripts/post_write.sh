#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ARGS="${HOOK_TOOL_ARGS:-}"
FILE=$(echo "${ARGS}" | grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\.(?:sv|v)' | head -1)
[ -n "${FILE}" ] && echo "${TS} write file=${FILE}" >> "${LOG}"
