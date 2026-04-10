#!/usr/bin/env bash
# gate_check.sh — Log quality gate results to benchmark
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
OUT="${HOOK_TOOL_OUTPUT:-}"

if echo "${OUT}" | grep -qiE "0 errors.*0 warnings|0 errors, 0 warnings"; then
    echo "${TS} gate=PASS sim=PASS" >> "${LOG}"
elif echo "${OUT}" | grep -qi "error\|failed"; then
    ERRS=$(echo "${OUT}" | grep -iE "error|failed" | head -3 | tr '\n' '|')
    echo "${TS} gate=FAIL errors=${ERRS}" >> "${LOG}"
fi
