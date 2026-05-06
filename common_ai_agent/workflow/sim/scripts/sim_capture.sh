#!/usr/bin/env bash
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"
OUT="${HOOK_TOOL_OUTPUT:-}"
ERRORS=$(echo "${OUT}" | grep -c -i "^.*error" || true)
WARNINGS=$(echo "${OUT}" | grep -c -i "^.*warning" || true)
PASS=$(echo "${OUT}" | grep -Ec "\[PASS\]| passed| PASS=" || true)
FAIL=$(echo "${OUT}" | grep -Ec "\[FAIL\]| failed| FAIL=[1-9]" || true)
SUMMARY=$(echo "${OUT}" | grep -Eo 'TESTS=[0-9]+ PASS=[0-9]+ FAIL=[0-9]+' | tail -1 || true)
if [ -n "${SUMMARY}" ]; then
    PASS_PART=${SUMMARY#*PASS=}; PASS=${PASS_PART%% *}
    FAIL_PART=${SUMMARY#*FAIL=}; FAIL=${FAIL_PART%% *}
fi
STATUS="FAIL"; [ "${ERRORS}" -eq 0 ] && [ "${WARNINGS}" -eq 0 ] && STATUS="PASS"
echo "${TS} sim_capture=${STATUS} errors=${ERRORS} warnings=${WARNINGS} pass=${PASS} fail=${FAIL}" >> "${LOG}"
