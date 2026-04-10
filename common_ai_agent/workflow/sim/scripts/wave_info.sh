#!/usr/bin/env bash
VCD="${HOOK_CMD_ARGS:-$1}"
[ -z "${VCD}" ] && VCD=$(find . -maxdepth 2 -name "*.vcd" | head -1)
[ -z "${VCD}" ] && { echo "No VCD found. Add \$dumpfile/\$dumpvars to TB and re-run /sim."; exit 1; }

echo "=== VCD: ${VCD} ==="
echo "Size: $(du -h "${VCD}" | cut -f1)"
echo ""
echo "Signals (top-level):"
grep -oP '(?<=\$var wire \d+ )\S+ \S+(?= \$end)' "${VCD}" 2>/dev/null | head -30 || \
    grep "^\$var" "${VCD}" | head -20
echo ""
echo "Time range:"
grep "^#" "${VCD}" | tail -5
