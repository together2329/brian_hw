#!/usr/bin/env bash
# check_lint_disk.sh — Disk-truth validator for lint tasks.
#
# Verifies lint_report.txt actually exists on disk + claims 0 errors / 0 warnings
# AS PRESENT IN THE FILE (not just the assistant's prose).
#
# Inputs (env):
#   IP_NAME — IP slug (auto-detected from cwd)
#   ALLOW_WARNINGS — set to "1" to allow ≥0 warnings (default: 0 = strict)
#
# Exit 0 = report file exists, contains 0 errors AND (0 warnings OR allowed).
# Exit 1 = file missing OR contains non-zero errors / disallowed warnings.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
[ -z "$IP" ] || [ ! -d "$IP" ] && { echo "[check_lint_disk] FAIL: IP dir not found"; exit 1; }

REPORT="$IP/lint/lint_report.txt"
[ -f "$REPORT" ] || { echo "[check_lint_disk] FAIL: $REPORT missing"; exit 1; }

SZ=$(wc -c < "$REPORT" | tr -d ' ')
[ "$SZ" -lt 30 ] && { echo "[check_lint_disk] FAIL: $REPORT too small (${SZ}B)"; exit 1; }

# Look for failure markers verbatim in the file.
if grep -qiE '[1-9][0-9]* error|FAIL|FATAL' "$REPORT"; then
    LINE=$(grep -m1 -niE '[1-9][0-9]* error|FAIL|FATAL' "$REPORT")
    echo "[check_lint_disk] FAIL: $REPORT contains error markers"
    echo "  → $LINE"
    exit 1
fi

if [ "${ALLOW_WARNINGS:-0}" != "1" ]; then
    if grep -qiE '[1-9][0-9]* warning' "$REPORT"; then
        LINE=$(grep -m1 -niE '[1-9][0-9]* warning' "$REPORT")
        echo "[check_lint_disk] FAIL: $REPORT contains warning markers (set ALLOW_WARNINGS=1 to permit)"
        echo "  → $LINE"
        exit 1
    fi
fi

# Must contain a positive pass signature.
if grep -qiE '0 error|0 warning|lint clean|all clean|no issues' "$REPORT"; then
    echo "[check_lint_disk] PASS: $REPORT = ${SZ}B, clean"
    exit 0
fi

echo "[check_lint_disk] FAIL: $REPORT lacks positive pass signature"
exit 1
