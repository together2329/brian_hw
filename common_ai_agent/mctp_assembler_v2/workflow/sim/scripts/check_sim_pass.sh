#!/usr/bin/env bash
if [ -n "${IP_NAME:-}" ] && [ -d "${IP_NAME}" ]; then
    bash workflow/sim/scripts/check_sim_disk.sh "${IP_NAME}" && exit 0
fi
echo "${TOOL_OUTPUT:-}" | grep -Eq "0 errors, 0 warnings|TESTS=[0-9]+ PASS=[0-9]+ FAIL=0|[0-9]+ passed" && exit 0
ERRORS=$(echo "${TOOL_OUTPUT}" | grep -oP '\d+ error' | head -1)
WARNINGS=$(echo "${TOOL_OUTPUT}" | grep -oP '\d+ warning' | head -1)
echo "Sim not passing: ${ERRORS:-?}, ${WARNINGS:-?}. Expected: 0 errors, 0 warnings or cocotb PASS summary"
exit 1
