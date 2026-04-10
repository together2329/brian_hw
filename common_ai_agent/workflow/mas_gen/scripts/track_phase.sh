#!/usr/bin/env bash
# track_phase.sh — Log file creation events (RTL/TB/TC/DOC)
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
ARGS="${HOOK_TOOL_ARGS:-}"

FILE=$(echo "${ARGS}" | grep -oP '(?<=path=")[^"]+|(?<=")[^"]+\.(?:sv|v|md)' | head -1)
[ -z "${FILE}" ] && FILE="${ARGS%%,*}"

if echo "${FILE}" | grep -q "tb_"; then
    TYPE="tb"
elif echo "${FILE}" | grep -q "tc_"; then
    TYPE="tc"
elif echo "${FILE}" | grep -q "_spec"; then
    TYPE="doc"
else
    TYPE="rtl"
fi

echo "${TS} write type=${TYPE} file=${FILE}" >> "${LOG}"
