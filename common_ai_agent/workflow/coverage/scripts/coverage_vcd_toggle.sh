#!/usr/bin/env bash
# coverage_vcd_toggle.sh — Wrap vcd_toggle.py for the slash command.
# Picks the merged.vcd if it exists (from /coverage-vcd-merge), otherwise
# the first *.vcd found under <DUT>/.
set -e

DUT="${HOOK_CMD_ARGS:-${1:-gpio_pad}}"
DUT="${DUT// /}"
WANT_JSON=0
TOP=10
for ((i=1; i<=$#; i++)); do
    case "${!i}" in
        --json) WANT_JSON=1 ;;
        --top)
            j=$((i+1))
            TOP="${!j}"
            ;;
    esac
done

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ADAPTER="${SCRIPT_DIR}/../adapters/vcd_toggle.py"
if [ ! -f "${ADAPTER}" ]; then
    echo "ERROR: adapter not found: ${ADAPTER}"
    exit 1
fi

# Pick a VCD: prefer merged.vcd from /coverage-vcd-merge, else first under <DUT>/
TARGET=""
if [ -f "${DUT}/cov/merged.vcd" ]; then
    TARGET="${DUT}/cov/merged.vcd"
else
    while IFS= read -r line; do
        [ -n "${line}" ] && TARGET="${line}" && break
    done < <(find "${DUT}" -name "*.vcd" 2>/dev/null | sort)
fi

if [ -z "${TARGET}" ]; then
    echo "ERROR: no VCD found under ${DUT}/"
    echo "  Run a simulation first (with WAVES=1 or analogous), or run"
    echo "  /coverage-vcd-merge to combine multiple VCDs."
    exit 1
fi

echo "VCD: ${TARGET}"
echo ""

if [ ${WANT_JSON} -eq 1 ]; then
    python3 "${ADAPTER}" --json --top "${TOP}" "${TARGET}"
else
    python3 "${ADAPTER}" --top "${TOP}" "${TARGET}"
fi
