#!/usr/bin/env bash
# Mirror of workflow/sim/scripts/wave_info.sh with extended search depth
# (sim_debug is invoked from any cwd, not just an IP root).
VCD="${HOOK_CMD_ARGS:-$1}"
[ -z "${VCD}" ] && VCD=$(find . -maxdepth 4 -name "*.vcd" 2>/dev/null | head -1)
[ -z "${VCD}" ] && { echo "No VCD found. Add \$dumpfile/\$dumpvars to TB and re-run /sim, or pass /wave <file>."; exit 1; }

echo "=== VCD: ${VCD} ==="
echo "Size: $(du -h "${VCD}" | cut -f1)"
if ! head -c 256 "${VCD}" | LC_ALL=C grep -qa '\$date\|\$timescale\|\$var'; then
    echo ""
    echo "ERROR: ${VCD} is not parseable ASCII VCD."
    echo "It may be FST/LXT/binary simulator data with a .vcd suffix."
    echo "Re-run TB with an ASCII VCD dump, or provide a matching converter"
    echo "(for example fst2vcd/lxt2vcd) and the real waveform format."
    exit 2
fi
echo ""
echo "Signals (top-level):"
grep -oP '(?<=\$var wire \d+ )\S+ \S+(?= \$end)' "${VCD}" 2>/dev/null | head -30 || \
    grep "^\$var" "${VCD}" | head -20
echo ""
echo "Time range:"
grep "^#" "${VCD}" | tail -5
