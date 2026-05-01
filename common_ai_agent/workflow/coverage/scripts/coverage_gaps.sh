#!/usr/bin/env bash
# coverage_gaps.sh — Identify top-N uncovered regions from annotated/ output.
# Lines starting with "%" or "0000" in *.cov files = unhit.
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
TOP_N="${2:-10}"
# Honor "--top N" too
for ((i=1; i<=$#; i++)); do
    if [ "${!i}" = "--top" ]; then
        j=$((i+1))
        TOP_N="${!j}"
    fi
done
DUT="${DUT// /}"

ANN="${DUT}/cov/annotated"
if [ ! -d "${ANN}" ]; then
    echo "ERROR: ${ANN} not found — run /coverage-report first."
    exit 1
fi

echo "=== Coverage Gaps (top ${TOP_N}) — ${ANN}/ ==="
echo ""

# Verilator annotates with format:
#   <hits> <code line>
#   %000000  always_comb begin     ← UNHIT (0 hits, but executable)
#   000000   if (foo)              ← UNHIT (no leading %)
#   00001234 dout <= ...           ← HIT
#
# Detect "%000000" or "^%" prefix → that's a missed line.
# Use portable while-read loop (mapfile is bash 4+; macOS default bash is 3.2).
MISSED=()
while IFS= read -r line; do
    [ -n "${line}" ] && MISSED+=("${line}")
done < <(grep -rn -E '^%[0 ]+|^%000000' "${ANN}" 2>/dev/null | head -n "${TOP_N}")

if [ ${#MISSED[@]} -eq 0 ]; then
    echo "No unhit lines detected. Either coverage is 100% or annotation parse failed."
    echo "Try: head -50 ${ANN}/<somefile>.cov"
    exit 0
fi

echo "Top ${#MISSED[@]} unhit line(s):"
printf "  %s\n" "${MISSED[@]}"
echo ""

# Group by file → tell agent which file has most gaps
echo "=== By-file gap count (top 10 files) ==="
printf "%s\n" "${MISSED[@]}" | cut -d: -f1 \
    | sort | uniq -c | sort -rn | head -10
echo ""

echo "Hint: read each ${ANN}/<file>.cov to see context around the unhit lines,"
echo "then write directed tests that exercise those branches."
