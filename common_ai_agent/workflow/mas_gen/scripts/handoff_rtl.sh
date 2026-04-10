#!/usr/bin/env bash
# handoff_rtl.sh — Print rtl_gen context handoff instructions
MODULE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

echo "================================================================"
echo "[MAS HANDOFF] → rtl_gen"
echo "Module  : ${MODULE:-<module_name>}"
echo "Task    : Implement RTL module"
echo "Rules   : workflow/rtl_gen/system_prompt.md"
echo "Output  : ${MODULE:-module}.sv"
echo "Criteria: iverilog -Wall compile with 0 errors"
echo "================================================================"
echo ""
echo "Loading rtl_gen rules..."
RTL_RULES="$(dirname "$(dirname "$0")")/../../rtl_gen/system_prompt.md"
[ -f "${RTL_RULES}" ] && cat "${RTL_RULES}" || echo "(rtl_gen/system_prompt.md not found)"

echo "${TS} handoff=rtl_gen module=${MODULE}" >> "${LOG}"
