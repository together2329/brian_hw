#!/usr/bin/env bash
# coverage_build.sh — Verilator build with line + toggle coverage flags.
# Reads filelist from <DUT>/list/<DUT>.f, builds into build_<DUT>_cov/
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
DUT="${DUT// /}"   # strip whitespace

if ! command -v verilator >/dev/null 2>&1; then
    echo "ERROR: verilator not found in PATH"
    echo "  Install: brew install verilator   (or use system package manager)"
    exit 1
fi

FLIST="${DUT}/list/${DUT}.f"
if [ ! -f "${FLIST}" ]; then
    echo "ERROR: filelist not found: ${FLIST}"
    echo "  Looking from: $(pwd)"
    exit 1
fi

BUILD="build_${DUT}_cov"
echo "=== Verilator coverage build ==="
echo "DUT       : ${DUT}"
echo "Filelist  : ${FLIST}"
echo "Build dir : ${BUILD}"
echo ""

verilator \
    --cc --exe \
    --coverage \
    --coverage-line \
    --coverage-toggle \
    --trace \
    --top-module "${DUT}" \
    -f "${FLIST}" \
    --Mdir "${BUILD}" \
    -Wno-fatal \
    2>&1 | tee "${BUILD}.verilator.log"

if [ ${PIPESTATUS[0]} -ne 0 ]; then
    echo ""
    echo "BUILD FAILED — see ${BUILD}.verilator.log"
    exit 1
fi

echo ""
echo "BUILD OK — instrumented sources in ${BUILD}/"
ls "${BUILD}"/*.cpp 2>/dev/null | wc -l | xargs -I{} echo "  C++ source files: {}"
echo ""
echo "Next: run testbench under SIM=verilator, then /coverage-merge"
