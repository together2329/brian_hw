#!/usr/bin/env bash
# mas_status.sh — Show project status: files, sim result, phase
LOG="${BENCHMARK_LOG:-.benchmark}"

echo "=== MAS Project Status ==="
echo ""

# Detect files
RTL_FILES=$(find . -maxdepth 2 -name "*.sv" -o -name "*.v" | grep -v "^./tb_" | grep -v "^./tc_" | sort)
TB_FILES=$(find . -maxdepth 2 -name "tb_*.sv" -o -name "tb_*.v" | sort)
TC_FILES=$(find . -maxdepth 2 -name "tc_*.sv" -o -name "tc_*.v" | sort)
DOC_FILES=$(find . -maxdepth 2 -name "*_spec.md" | sort)

echo "RTL files  :"
[ -n "${RTL_FILES}" ] && echo "${RTL_FILES}" | sed 's/^/  /' || echo "  (none)"
echo "TB files   :"
[ -n "${TB_FILES}" ] && echo "${TB_FILES}" | sed 's/^/  /' || echo "  (none)"
echo "TC files   :"
[ -n "${TC_FILES}" ] && echo "${TC_FILES}" | sed 's/^/  /' || echo "  (none)"
echo "Doc files  :"
[ -n "${DOC_FILES}" ] && echo "${DOC_FILES}" | sed 's/^/  /' || echo "  (none)"

echo ""
if [ -f "${LOG}" ]; then
    LAST_SIM=$(grep "sim=" "${LOG}" | tail -1)
    LAST_HANDOFF=$(grep "handoff=" "${LOG}" | tail -1)
    echo "Last sim   : ${LAST_SIM:-(none)}"
    echo "Last agent : ${LAST_HANDOFF:-(none)}"
    PHASE="SPEC"
    [ -n "${RTL_FILES}" ] && PHASE="RTL"
    [ -n "${TB_FILES}" ] && PHASE="TB"
    grep -q "sim=PASS" "${LOG}" 2>/dev/null && PHASE="DOC"
    [ -n "${DOC_FILES}" ] && PHASE="COMPLETE"
    echo "Phase      : ${PHASE}"
else
    echo "Phase      : SPEC (no benchmark log)"
fi
