#!/usr/bin/env bash
# disk_diff.sh — Inject ground-truth disk diff into the agent's context
# after every write/run tool call.
#
# Without this, the agent can claim "I just wrote tc_uart.sv" without any
# real disk change. This hook reports what FILES actually changed since the
# previous tool call, giving the agent (and the operator reading logs) an
# unforgeable reality check.
#
# Snapshot is stored in $TMPDIR (volatile across restarts — that's fine,
# we just want per-turn delta). For each tracked IP-typical extension we
# capture path → mtime → size, then diff.
#
# This hook is non-blocking (always exit 0). Its output is appended to the
# tool result the agent sees on its next observation.

SNAPSHOT="${TMPDIR:-/tmp}/atlas_disk_snap_${ACTIVE_WORKSPACE:-default}.txt"
WATCH_ROOTS="${ATLAS_DISK_WATCH:-./}"
EXTS='\.(sv|v|vh|svh|yaml|yml|md|f|txt|log|json|sdc|upf|tcl|out|netlist|vcd)$'

# Build current snapshot: path  size  mtime
CURRENT=$(find $WATCH_ROOTS \
    -type f \
    \( -path '*/.*' -o -path '*/node_modules/*' -o -path '*/__pycache__/*' \) -prune -o \
    -type f -print 2>/dev/null \
    | grep -E "$EXTS" \
    | head -2000 \
    | xargs -I{} stat -f "%N %z %m" {} 2>/dev/null \
    | sort)

if [ ! -f "$SNAPSHOT" ]; then
    # First run: just save snapshot, no diff to report.
    printf '%s\n' "$CURRENT" > "$SNAPSHOT"
    exit 0
fi

PREV=$(cat "$SNAPSHOT")
DIFF=$(diff <(echo "$PREV") <(echo "$CURRENT") | grep -E '^[<>]')

if [ -z "$DIFF" ]; then
    # No file changes since previous tool call — important signal: if the
    # agent just claimed to write a file and this comes up empty, it lied.
    echo "[disk_diff] No tracked files changed since last tool call."
else
    ADDED=$(echo "$DIFF" | grep '^>' | wc -l | tr -d ' ')
    REMOVED=$(echo "$DIFF" | grep '^<' | wc -l | tr -d ' ')
    echo "[disk_diff] $ADDED file-states added/changed, $REMOVED removed since last tool call:"
    echo "$DIFF" | head -8 | sed 's/^/  /'
    if [ "$ADDED" -gt 8 ] || [ "$REMOVED" -gt 8 ]; then
        echo "  … (output truncated)"
    fi
fi

# Update snapshot for next iteration.
printf '%s\n' "$CURRENT" > "$SNAPSHOT"
exit 0
