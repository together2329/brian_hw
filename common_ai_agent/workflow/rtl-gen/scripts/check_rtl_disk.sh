#!/usr/bin/env bash
# check_rtl_disk.sh — Disk-truth validator for rtl-gen tasks.
#
# Verifies real RTL artifacts exist on disk + compile clean. Replaces
# stdout-grep validators that let agents fake "0 lint errors" without
# actually writing or compiling files.
#
# Inputs (env):
#   IP_NAME — IP slug (auto-detected from cwd if missing)
#   MIN_RTL — minimum bytes per .v/.sv file (default 200)
#
# Exit 0 = filelist exists + every listed RTL file ≥ MIN_RTL bytes
#          + iverilog -c compile passes (parse-only, no -o).
# Exit 1 = otherwise.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi
[ -z "$IP" ] || [ ! -d "$IP" ] && { echo "[check_rtl_disk] FAIL: IP dir not found"; exit 1; }

LIST="$IP/list/$IP.f"
MIN_RTL="${MIN_RTL:-200}"

[ -f "$LIST" ] || { echo "[check_rtl_disk] FAIL: filelist $LIST missing"; exit 1; }

# Each entry in filelist must exist + meet size threshold.
FAIL=0
while read -r line; do
    # Strip comments and whitespace.
    f=$(echo "$line" | sed 's|//.*||' | xargs)
    [ -z "$f" ] && continue
    # Skip non-RTL files (e.g. tb_*.sv lines for sim mode).
    case "$f" in
        *.v|*.sv|*.vh|*.svh) ;;
        *) continue ;;
    esac
    # Resolve relative to IP/.. (filelist paths usually relative to IP root).
    fpath="$IP/$f"
    [ -f "$fpath" ] || fpath="$f"  # fallback: as-given
    if [ ! -f "$fpath" ]; then
        echo "[check_rtl_disk] FAIL: filelist references missing file: $f"
        FAIL=1; continue
    fi
    sz=$(wc -c < "$fpath" | tr -d ' ')
    if [ "$sz" -lt "$MIN_RTL" ]; then
        echo "[check_rtl_disk] FAIL: $f = ${sz}B (need ≥${MIN_RTL})"
        FAIL=1
    fi
done < "$LIST"

[ $FAIL -ne 0 ] && exit 1

# Compile check (parse-only). iverilog -c reads filelist, -o /dev/null → parse only.
# Filelist paths are usually relative to IP root, so cd there first.
if command -v iverilog >/dev/null 2>&1; then
    LIST_REL="$(basename "$LIST")"
    if ! ( cd "$IP" && iverilog -g2012 -Irtl -f "list/$LIST_REL" -o /dev/null ) 2>/tmp/_rtl_compile.err; then
        echo "[check_rtl_disk] FAIL: iverilog compile errors:"
        head -10 /tmp/_rtl_compile.err | sed 's/^/  /'
        exit 1
    fi
fi

echo "[check_rtl_disk] PASS: filelist OK, all RTL files ≥${MIN_RTL}B, compile clean"
exit 0
