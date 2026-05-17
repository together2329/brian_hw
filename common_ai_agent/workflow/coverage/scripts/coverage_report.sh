#!/usr/bin/env bash
# coverage_report.sh — Generate annotated/ + .info from merged.dat.
# Side-effects on each run:
#   <DUT>/cov/annotated/        verilator_coverage annotated source
#   <DUT>/cov/coverage.info     LCOV info file (DA/BRDA records)
#   <DUT>/cov/coverage.json     parsed summary snapshot for the UI
#   <DUT>/cov/history.jsonl     append-only run log (one JSON per iter)
#   <DUT>/cov/html/             optional HTML report (when genhtml available)
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
WANT_HTML=0
NO_HTML=0
for arg in "$@"; do
    case "$arg" in
        --html)    WANT_HTML=1 ;;
        --no-html) NO_HTML=1 ;;
    esac
done
DUT="${DUT// /}"

OUT="${DUT}/cov"
MERGED="${OUT}/merged.dat"

if [ ! -f "${MERGED}" ]; then
    echo "ERROR: ${MERGED} not found — run /coverage-merge first."
    exit 1
fi

# Auto-enable HTML when genhtml is available (unless --no-html was passed).
# This makes /coverage-report do the right thing without remembering --html.
if [ ${WANT_HTML} -eq 0 ] && [ ${NO_HTML} -eq 0 ]; then
    if command -v genhtml >/dev/null 2>&1; then
        WANT_HTML=1
    fi
fi

echo "=== Annotated source ==="
verilator_coverage "${MERGED}" --annotate "${OUT}/annotated/" 2>&1 | tail -5

echo ""
echo "=== LCOV .info ==="
verilator_coverage "${MERGED}" --write-info "${OUT}/coverage.info" 2>&1 | tail -3

if [ ${WANT_HTML} -eq 1 ]; then
    if command -v genhtml >/dev/null 2>&1; then
        echo ""
        echo "=== HTML report (genhtml) ==="
        genhtml "${OUT}/coverage.info" -o "${OUT}/html" --quiet 2>&1 | tail -5 \
            || echo "WARN: genhtml exited non-zero — partial HTML may be present"
        echo "HTML index: ${OUT}/html/index.html"
    else
        echo ""
        echo "WARN: genhtml not available — skipping HTML."
        echo "      Install with: brew install lcov   (provides genhtml)"
    fi
fi

echo ""
echo "=== Raw LCOV summary (line / all BRDA %) ==="
LINES_TOTAL=$(grep -c "^DA:" "${OUT}/coverage.info" 2>/dev/null || echo 0)
LINES_HIT=$(awk -F'[:,]' '/^DA:/ && $3 != "0" {n++} END{print n+0}' "${OUT}/coverage.info")
BRS_TOTAL=$(grep -c "^BRDA:" "${OUT}/coverage.info" 2>/dev/null || echo 0)
BRS_HIT=$(awk -F, '/^BRDA:/ {n=split($0,a,","); if (a[n] != "0" && a[n] != "-") h++} END{print h+0}' "${OUT}/coverage.info")

if [ "${LINES_TOTAL}" -gt 0 ]; then
    LPCT=$(awk -v h="${LINES_HIT}" -v f="${LINES_TOTAL}" 'BEGIN{printf "%.2f", (h/f)*100}')
    echo "Lines    : ${LINES_HIT}/${LINES_TOTAL}  (${LPCT}%)"
else
    LPCT="0.00"
    echo "Lines    : 0/0  (no DA records — coverage.info empty?)"
fi
if [ "${BRS_TOTAL}" -gt 0 ]; then
    BPCT=$(awk -v h="${BRS_HIT}" -v f="${BRS_TOTAL}" 'BEGIN{printf "%.2f", (h/f)*100}')
    echo "All BRDA : ${BRS_HIT}/${BRS_TOTAL}  (${BPCT}%)"
    echo "           raw Verilator BRDA may include toggle/expression bins; SSOT summary filters control-flow branches."
else
    BPCT="0.00"
fi
TOG_LINE=$(verilator_coverage "${MERGED}" 2>&1 | grep -i "total coverage" | head -1)
if [ -n "${TOG_LINE}" ]; then
    echo "Overall  : ${TOG_LINE# }"
fi

# ── Write summary snapshot for the UI ─────────────────────────────────
# coverage.json: latest stats, used by coverage.jsx as the canonical source
# of truth (no need to re-parse coverage.info on every fetch — though the
# UI also supports falling back to .info parsing).
TIMESTAMP_ISO=$(date -u +"%Y-%m-%dT%H:%M:%SZ")
TIMESTAMP_EPOCH=$(date +%s)
cat > "${OUT}/coverage.json" <<EOF
{
  "timestamp_iso": "${TIMESTAMP_ISO}",
  "timestamp_epoch": ${TIMESTAMP_EPOCH},
  "dut": "${DUT}",
  "lines":    { "hit": ${LINES_HIT:-0}, "total": ${LINES_TOTAL:-0}, "pct": ${LPCT:-0} },
  "branches": { "hit": ${BRS_HIT:-0},   "total": ${BRS_TOTAL:-0},   "pct": ${BPCT:-0} },
  "html_available": ${WANT_HTML}
}
EOF

# ── Append to per-run history ────────────────────────────────────────
# history.jsonl: one JSON object per /coverage-report invocation. The UI
# reads the last 20 to render the delta tracker.
mkdir -p "${OUT}"
echo "{\"timestamp_iso\":\"${TIMESTAMP_ISO}\",\"timestamp_epoch\":${TIMESTAMP_EPOCH},\"lines\":{\"hit\":${LINES_HIT:-0},\"total\":${LINES_TOTAL:-0},\"pct\":${LPCT:-0}},\"branches\":{\"hit\":${BRS_HIT:-0},\"total\":${BRS_TOTAL:-0},\"pct\":${BPCT:-0}}}" >> "${OUT}/history.jsonl"
HIST_COUNT=$(wc -l < "${OUT}/history.jsonl" | tr -d ' ')

echo ""
echo "=== SSOT coverage summary ==="
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
python3 "${SCRIPT_DIR}/ssot_coverage_summary.py" "${DUT}" || {
    RC=$?
    if [ "${RC}" -eq 3 ]; then
        echo "SSOT coverage goals are not fully closed; see ${OUT}/coverage.json and ${DUT}/sim/coverage_report.md"
    else
        exit "${RC}"
    fi
}

python3 - "${OUT}/coverage.json" <<'PY'
import json
import sys
from pathlib import Path

path = Path(sys.argv[1])
if path.is_file():
    doc = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    lines = doc.get("lines") or {}
    branches = doc.get("branches") or {}
    print("")
    print("=== SSOT-filtered coverage summary ===")
    print(
        "Lines    : {}/{}  ({}%) target={} status={}".format(
            lines.get("hit", 0),
            lines.get("total", 0),
            lines.get("pct"),
            lines.get("target_pct"),
            "PASS" if lines.get("meets_target") else "BLOCKED",
        )
    )
    print(
        "Branches : {}/{}  ({}%) target={} status={}".format(
            branches.get("hit", 0),
            branches.get("total", 0),
            branches.get("pct"),
            branches.get("target_pct"),
            "PASS" if branches.get("meets_target") else "BLOCKED",
        )
    )
PY

echo ""
echo "Annotated dir : ${OUT}/annotated/"
echo "LCOV info     : ${OUT}/coverage.info"
echo "JSON summary  : ${OUT}/coverage.json"
echo "History       : ${OUT}/history.jsonl  (${HIST_COUNT} runs)"
[ ${WANT_HTML} -eq 1 ] && echo "HTML report   : ${OUT}/html/index.html"
echo ""
echo "Next: /coverage-gaps     (find uncovered hot-spots)"
