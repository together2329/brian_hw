#!/usr/bin/env bash
# handoff_tb.sh — Print tb_gen context handoff instructions
MODULE="${HOOK_CMD_ARGS:-$1}"
LOG="${BENCHMARK_LOG:-.benchmark}"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

echo "================================================================"
echo "[MAS HANDOFF] → tb_gen"
echo "Module  : ${MODULE:-<module_name>}"
echo "Task    : Generate testbench + test cases + run simulation"
echo "Rules   : workflow/tb_gen/system_prompt.md"
echo "Input   : ${MODULE:-module}.sv (RTL source — read-only)"
echo "Output  : tb_${MODULE:-module}.sv, tc_${MODULE:-module}.sv"
echo "Criteria: simulation 0 errors, 0 warnings"
echo "================================================================"
echo ""
echo "Loading tb_gen rules..."
TB_RULES="$(dirname "$(dirname "$0")")/../../tb_gen/system_prompt.md"
[ -f "${TB_RULES}" ] && cat "${TB_RULES}" || echo "(tb_gen/system_prompt.md not found)"

echo "${TS} handoff=tb_gen module=${MODULE}" >> "${LOG}"
