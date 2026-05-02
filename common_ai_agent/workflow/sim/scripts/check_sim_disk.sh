#!/usr/bin/env bash
# check_sim_disk.sh — Disk-truth validator for sim tasks.
#
# Verifies real simulator artifacts exist + the report contains real
# pass markers. Stdout-grep-only validators let agents fabricate
# "0 errors, 0 warnings" without running anything; this script
# additionally requires:
#   - a compiled binary on disk with non-trivial size
#   - a sim_report.txt with non-trivial size
#   - the report contains either "0 errors, 0 warnings" OR an
#     equivalent test-summary line
#   - the report does NOT contain "[FAIL]" or fatal markers
#
# Exit 0 = sim ran for real and met success criteria.
# Exit 1 = artifacts missing OR report shows failures OR claim-only.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
if [ -z "$IP" ] || [ ! -d "$IP" ]; then
    echo "[check_sim_disk] FAIL: cannot locate IP directory"
    exit 1
fi

REPORT="$IP/sim/sim_report.txt"
# Compiled binary may be uart.out (iverilog) or <ip>_simv (VCS).
BIN_IV="$IP/sim/$IP.out"
BIN_VCS="$IP/sim/${IP}_simv"
BIN=""
if [ -f "$BIN_IV" ]; then BIN="$BIN_IV"; fi
if [ -z "$BIN" ] && [ -f "$BIN_VCS" ]; then BIN="$BIN_VCS"; fi

MIN_BIN="${MIN_BIN:-1000}"
MIN_RPT="${MIN_RPT:-100}"

_size() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }

if [ -z "$BIN" ]; then
    echo "[check_sim_disk] FAIL: no compiled binary at $BIN_IV or $BIN_VCS"
    exit 1
fi
BIN_SZ=$(_size "$BIN")
[ "$BIN_SZ" -lt "$MIN_BIN" ] && { echo "[check_sim_disk] FAIL: $BIN = ${BIN_SZ}B (need ≥${MIN_BIN})"; exit 1; }

RPT_SZ=$(_size "$REPORT")
[ "$RPT_SZ" -lt "$MIN_RPT" ] && { echo "[check_sim_disk] FAIL: $REPORT missing or ${RPT_SZ}B (need ≥${MIN_RPT})"; exit 1; }

# Report sanity: must not contain failure markers in any common shape:
#   [FAIL] SCx_...      ← per-test [FAIL] tag (textbook ssot-tb format)
#   N FAILED            ← end-of-report tally  ("6 FAILED")
#   FAIL: ...           ← bare FAIL: prefix lines
#   got=0xxx, x_state   ← X-propagation symptoms
#   Errors: N (N > 0)   ← non-zero error tally
#   Warnings: N (N > 0) ← non-zero warning tally
#   FATAL / Aborted     ← simulator panic
if grep -qE '\[FAIL\]|FATAL|Aborted' "$REPORT" \
   || grep -qE '^[[:space:]]*FAIL:' "$REPORT" \
   || grep -qE 'got=0[xX][xX]+' "$REPORT" \
   || grep -qiE '[1-9][0-9]* (FAILED|failures|errors)\b' "$REPORT"; then
    FAIL_LINE=$(grep -m1 -nE '\[FAIL\]|^[[:space:]]*FAIL:|FATAL|Aborted|[1-9][0-9]* FAILED|got=0[xX][xX]+' "$REPORT")
    echo "[check_sim_disk] FAIL: $REPORT contains failure markers"
    echo "  → $FAIL_LINE"
    echo "  Hint: even when failures are 'DUT bugs', sim is NOT done — escalate via [SIM ESCALATE] or fix RTL and re-run."
    exit 1
fi

# Must contain a positive pass signature.
if grep -qE 'all PASS|0 errors, 0 warnings|All tests passed|All [0-9]+ tests passed' "$REPORT"; then
    echo "[check_sim_disk] PASS: bin=${BIN_SZ}B report=${RPT_SZ}B"
    exit 0
fi

echo "[check_sim_disk] FAIL: $REPORT lacks positive pass signature (need 'all PASS' or '0 errors, 0 warnings' or 'All tests passed')"
exit 1
