#!/usr/bin/env bash
# coverage_merge.sh — Merge all per-test coverage.dat files in <DUT>/cocotb/sim_build/
# (or any *.dat under <DUT>) into <DUT>/cov/merged.dat
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
DUT="${DUT// /}"

if ! command -v verilator_coverage >/dev/null 2>&1; then
    echo "ERROR: verilator_coverage not found (ships with verilator)"
    exit 1
fi

OUT="${DUT}/cov"
mkdir -p "${OUT}"

# Collect all .dat files under the DUT — typical locations:
#   <DUT>/cocotb/sim_build/coverage.dat            (single-test cocotb run)
#   <DUT>/sim/cov/*.dat                            (test-name partitioned)
#   <DUT>/cov/raw/*.dat                            (manual placement)
# Use a portable while-read loop instead of mapfile (bash 4+ only;
# macOS default bash is 3.2). Filenames with spaces/newlines are rare
# in this context, so word-by-line splitting is acceptable.
DAT_FILES=()
while IFS= read -r line; do
    [ -n "${line}" ] && DAT_FILES+=("${line}")
done < <(find "${DUT}" \( -name "coverage.dat" -o -name "*.cov.dat" \) 2>/dev/null)

if [ ${#DAT_FILES[@]} -eq 0 ]; then
    echo "ERROR: no coverage.dat found under ${DUT}/"
    echo "  Did you run the regression with verilator backend yet?"
    echo "  e.g. cd ${DUT}/cocotb && make SIM=verilator MODULE=tests.tb"
    exit 1
fi

echo "=== Coverage merge ==="
echo "Found ${#DAT_FILES[@]} coverage.dat file(s):"
printf "  %s\n" "${DAT_FILES[@]}"
echo ""

verilator_coverage --write "${OUT}/merged.dat" "${DAT_FILES[@]}"
echo ""
echo "Merged → ${OUT}/merged.dat"
ls -lh "${OUT}/merged.dat"
echo ""
echo "Next: /coverage-report"
