#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
OUT="${HOOK_TOOL_OUTPUT:-}"
ERRORS=$(echo "${OUT}" | grep -c -i "^.*error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "^.*warning" || true)
PASS=$(echo "${OUT}" | grep -c "\[PASS\]" || true)
FAIL=$(echo "${OUT}" | grep -c "\[FAIL\]" || true)
STATUS="FAIL"; [ "${ERRORS}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ] && STATUS="PASS"
echo "${TS} sim_capture=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS} fail=${FAIL}" >> "${LOG}"
