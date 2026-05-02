#!/usr/bin/env bash
# check_tb_disk.sh — Disk-truth validator for tb-gen tasks.
#
# Verifies the deliverables that a TB-gen task CLAIMS to have produced
# actually exist on disk with non-trivial size. Replaces the previous
# stdout-grep-only validator that lets agents fake completions by
# echoing "0 errors, 0 warnings" without running anything.
#
# Inputs (env vars):
#   IP_DIR  — IP root (default: derived from current working directory).
#   MIN_TC  — minimum bytes for tc_<ip>.sv (default 1000)
#   MIN_TB  — minimum bytes for tb_<ip>.sv (default 500)
#   MIN_F   — minimum bytes for list/<ip>.f (default 50)
#
# Exit 0 = real artifacts on disk meet thresholds; tracker may approve.
# Exit 1 = disk reality contradicts claimed completion; tracker rejects.

set -u

# Auto-detect IP from current working directory if not provided.
IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    # Try the most-recently-modified <ip>/yaml/<ip>.ssot.yaml under cwd.
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi

if [ -z "$IP" ] || [ ! -d "$IP" ]; then
    echo "[check_tb_disk] FAIL: cannot locate IP directory (IP=${IP:-unset})"
    exit 1
fi

MIN_TC="${MIN_TC:-1000}"
MIN_TB="${MIN_TB:-500}"
MIN_F="${MIN_F:-50}"

TC="$IP/tc/tc_$IP.sv"
TB="$IP/tb/tb_$IP.sv"
LIST="$IP/list/$IP.f"

_size() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }

TC_SZ=$(_size "$TC")
TB_SZ=$(_size "$TB")
F_SZ=$(_size "$LIST")

FAIL=0
[ "$TC_SZ" -lt "$MIN_TC" ] && { echo "[check_tb_disk] FAIL: $TC = ${TC_SZ}B (need ≥${MIN_TC})"; FAIL=1; }
[ "$TB_SZ" -lt "$MIN_TB" ] && { echo "[check_tb_disk] FAIL: $TB = ${TB_SZ}B (need ≥${MIN_TB})"; FAIL=1; }
[ "$F_SZ" -lt "$MIN_F"  ] && { echo "[check_tb_disk] FAIL: $LIST = ${F_SZ}B (need ≥${MIN_F})"; FAIL=1; }

# Filelist must reference both tb and tc.
if [ "$F_SZ" -ge "$MIN_F" ]; then
    grep -q "tb_$IP" "$LIST" || { echo "[check_tb_disk] FAIL: $LIST does not reference tb_$IP"; FAIL=1; }
fi

if [ $FAIL -ne 0 ]; then
    echo "[check_tb_disk] Disk reality contradicts claimed completion. Run write_file/run_command for real."
    exit 1
fi

echo "[check_tb_disk] PASS: tc=${TC_SZ}B tb=${TB_SZ}B list=${F_SZ}B"
exit 0
