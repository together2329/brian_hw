#!/usr/bin/env bash
# write_report.sh — Generate lint_report.txt from .benchmark log
LOG="${BENCHMARK_LOG:-.benchmark}"
OUT="lint_report.txt"
TS="$(date '+%Y-%m-%dT%H:%M:%S')"

LAST=$(grep "lint" "${LOG}" 2>/dev/null | tail -1)
ERRORS=$(echo "${LAST}" | grep -oP 'errors=\K\d+' || echo "?")
WARNINGS=$(echo "${LAST}" | grep -oP 'warnings=\K\d+' || echo "?")
FILES=$(find . -maxdepth 3 \( -name "*.sv" -o -name "*.v" \) | grep -v "tb_\|tc_" | sort | tr '\n' ' ')
TOOL=$(command -v verilator &>/dev/null && echo "verilator" || echo "iverilog")

cat > "${OUT}" << EOF
=== Lint Report ===
Date  : ${TS}
Files : ${FILES}
Tool  : ${TOOL}
Result: ${ERRORS} errors, ${WARNINGS} warnings

[Errors]
$(grep "lint.*errors=[^0]" "${LOG}" 2>/dev/null | tail -5 || echo "NONE")

[Issues Log]
$(grep "lint_issues" "${LOG}" 2>/dev/null | tail -20 || echo "NONE")
EOF

echo "Written: ${OUT}"
cat "${OUT}"
