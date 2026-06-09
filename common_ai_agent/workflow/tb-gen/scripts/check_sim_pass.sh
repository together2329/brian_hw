#!/usr/bin/env bash
# check_sim_pass.sh — Validator for SV and cocotb simulation output.
OUTPUT="${TOOL_OUTPUT:-}"
if [ -n "${IP_NAME:-}" ] && [ -d "${IP_NAME}" ]; then
    bash workflow/sim/scripts/check_sim_disk.sh "${IP_NAME}" && exit 0
fi
# Reject any explicit failure evidence first, even when pass-like text also
# appears (e.g. "5 passed -- old run; FAIL=3 actual"): a non-zero FAIL count
# or "N failed" with N>=1 means the run did not pass.
if echo "${OUTPUT}" | grep -Eq "FAIL=[1-9][0-9]*|[1-9][0-9]* failed"; then
    echo "Simulation reports failures; not passing"
    echo "Expected: 0 errors, 0 warnings or cocotb PASS summary"
    exit 1
fi
# Require positive pass evidence: a clean iverilog summary, a cocotb TESTS line
# with at least one passing test and zero failures, or "N passed" with N>=1.
# "TESTS=0 PASS=0 FAIL=0" (zero tests) must NOT pass.
if echo "${OUTPUT}" | grep -Eq "0 errors, 0 warnings|TESTS=[0-9]+ PASS=[1-9][0-9]* FAIL=0|[1-9][0-9]* passed"; then
    exit 0
fi
ERRORS=$(echo "${OUTPUT}" | grep -oE '[0-9]+ error' | head -1)
WARNINGS=$(echo "${OUTPUT}" | grep -oE '[0-9]+ warning' | head -1)
echo "Simulation not passing: ${ERRORS:-?}, ${WARNINGS:-?}"
echo "Expected: 0 errors, 0 warnings or cocotb PASS summary"
exit 1
