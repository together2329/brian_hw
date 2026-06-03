#!/usr/bin/env bash
# coverage.sh — Simple branch coverage hint (grep-based, no tool required)
MODULE="${HOOK_CMD_ARGS:-$1}"
[ -z "${MODULE}" ] && MODULE=$(find . -maxdepth 1 -name "*.sv" | grep -v "tb_\|tc_" | head -1 | sed 's|./||')
SRC="${MODULE%.sv}.sv"
TC="tc_${MODULE%.sv}.sv"

[ ! -f "${SRC}" ] && { echo "DUT not found: ${SRC}"; exit 1; }

echo "=== Coverage Hint: ${SRC} ==="
echo ""

# Count if/case branches in DUT
IF_BRANCHES=$(grep -c "if\s*(" "${SRC}" || true)
CASE_ITEMS=$(grep -c "^\s*[0-9a-fA-Fx']*\s*:" "${SRC}" || true)
echo "DUT branches (approx):"
echo "  if statements : ${IF_BRANCHES}"
echo "  case items    : ${CASE_ITEMS}"
echo ""

# Check which are exercised in TC
if [ -f "${TC}" ]; then
    TC_TASKS=$(grep -c "^task" "${TC}" || true)
    echo "Test cases in ${TC}: ${TC_TASKS} tasks"
    grep "^task" "${TC}" | sed 's/^/  /'
else
    echo "TC file not found: ${TC} — run /gen-tc first"
fi

echo ""
echo "Note: For full coverage use verilator --coverage or VCS/Questa"
