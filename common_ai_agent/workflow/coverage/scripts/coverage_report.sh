#!/usr/bin/env bash
# coverage_report.sh — Generate annotated/ + .info from merged.dat.
# Prints summary line/toggle %.
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
WANT_HTML=0
for arg in "$@"; do
    [ "$arg" = "--html" ] && WANT_HTML=1
done
DUT="${DUT// /}"

OUT="${DUT}/cov"
MERGED="${OUT}/merged.dat"

if [ ! -f "${MERGED}" ]; then
    echo "ERROR: ${MERGED} not found — run /coverage-merge first."
    exit 1
fi

echo "=== Annotated source ==="
verilator_coverage "${MERGED}" --annotate "${OUT}/annotated/" 2>&1 | tail -5

echo ""
echo "=== LCOV .info ==="
verilator_coverage "${MERGED}" --write-info "${OUT}/coverage.info" 2>&1 | tail -3

if [ ${WANT_HTML} -eq 1 ]; then
    if command -v genhtml >/dev/null 2>&1; then
        genhtml "${OUT}/coverage.info" -o "${OUT}/html" 2>&1 | tail -3
        echo "HTML report: ${OUT}/html/index.html"
    else
        echo "WARN: genhtml not available — skipping HTML"
    fi
fi

echo ""
echo "=== Summary (line / branch %) ==="
# Verilator --write-info emits per-line `DA:<line>,<count>` and per-branch
# `BRDA:<line>,<block>,<branch>,<count>` records but does NOT emit LCOV's
# LF:/LH: rollup lines (lcov/genhtml compute those at render time). So
# count DA / BRDA records directly.
LINES_TOTAL=$(grep -c "^DA:" "${OUT}/coverage.info" 2>/dev/null || echo 0)
LINES_HIT=$(awk -F'[:,]' '/^DA:/ && $3 != "0" {n++} END{print n+0}' "${OUT}/coverage.info")
BRS_TOTAL=$(grep -c "^BRDA:" "${OUT}/coverage.info" 2>/dev/null || echo 0)
BRS_HIT=$(awk -F, '/^BRDA:/ {n=split($0,a,","); if (a[n] != "0" && a[n] != "-") h++} END{print h+0}' "${OUT}/coverage.info")

if [ "${LINES_TOTAL}" -gt 0 ]; then
    LPCT=$(awk -v h="${LINES_HIT}" -v f="${LINES_TOTAL}" 'BEGIN{printf "%.2f", (h/f)*100}')
    echo "Lines    : ${LINES_HIT}/${LINES_TOTAL}  (${LPCT}%)"
else
    echo "Lines    : 0/0  (no DA records — coverage.info empty?)"
fi
if [ "${BRS_TOTAL}" -gt 0 ]; then
    BPCT=$(awk -v h="${BRS_HIT}" -v f="${BRS_TOTAL}" 'BEGIN{printf "%.2f", (h/f)*100}')
    echo "Branches : ${BRS_HIT}/${BRS_TOTAL}  (${BPCT}%)"
fi
# Toggle coverage doesn't show up in --write-info output. Pull from the
# annotate output's "Total coverage (X/Y) Z%" line instead.
TOG_LINE=$(verilator_coverage "${MERGED}" 2>&1 | grep -i "total coverage" | head -1)
if [ -n "${TOG_LINE}" ]; then
    echo "Overall  : ${TOG_LINE# }"
fi
echo ""
echo "Annotated dir : ${OUT}/annotated/"
echo "LCOV info     : ${OUT}/coverage.info"
[ ${WANT_HTML} -eq 1 ] && echo "HTML report   : ${OUT}/html/index.html"
echo ""
echo "Next: /coverage-gaps     (find uncovered hot-spots)"
