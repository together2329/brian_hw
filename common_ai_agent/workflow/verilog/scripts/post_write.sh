#!/usr/bin/env bash
# post_write.sh — Log RTL file writes to benchmark
# Triggered: after write_file/replace_in_file on .v/.sv files

LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
TOOL="${HOOK_TOOL_NAME:-write}"
ARGS="${HOOK_TOOL_ARGS:-}"

# Extract file path from args (first quoted string or bare word)
FILE=$(echo "${ARGS}" | grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\.(?:v|sv)' | head -1)
[ -z "${FILE}" ] && FILE="${ARGS%%,*}"

echo "${TS} write tool=${TOOL} file=${FILE}" >> "${LOG}"
