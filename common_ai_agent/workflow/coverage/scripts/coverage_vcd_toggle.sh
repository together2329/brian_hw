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

# Always persist a JSON copy to <DUT>/cov/toggle.json so the Atlas UI
# panel can fetch it. The text or --json output is what gets shown to
# the agent; the persisted JSON is what the UI consumes.
mkdir -p "${DUT}/cov"
TOGGLE_JSON_PATH="${DUT}/cov/toggle.json"
python3 "${ADAPTER}" --json --top "${TOP}" "${TARGET}" > "${TOGGLE_JSON_PATH}"
echo "JSON snapshot: ${TOGGLE_JSON_PATH}"

if [ ${WANT_JSON} -eq 1 ]; then
    cat "${TOGGLE_JSON_PATH}"
else
    # Pretty-print summary from the JSON we just wrote (avoid running
    # the parser twice — that's wasted work on big VCDs).
    python3 - "${TOGGLE_JSON_PATH}" <<'PYEOF'
import json, sys
d = json.load(open(sys.argv[1]))
print()
print(f"=== VCD Toggle Coverage: {d['vcd']} ===")
print(f"Nets         : {d['nets']}")
print(f"Total bits   : {d['total_bits']}")
print(f"Toggled bits : {d['toggled_bits']}")
print(f"Toggle %     : {d['pct']:.2f} %")
print()
print(f"=== Worst-{len(d['scopes'])} scopes (by toggle %) ===")
for s in sorted(d['scopes'], key=lambda x: x['pct'])[:10]:
    print(f"  {s['pct']:5.1f} %  {s['toggled']:>4}/{s['total']:<4} bits  ({s['nets']} nets)  {s['scope']}")
PYEOF
fi
