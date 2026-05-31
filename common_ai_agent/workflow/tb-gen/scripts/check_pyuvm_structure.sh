#!/usr/bin/env bash
# check_pyuvm_structure.sh — verify cocotb backend is layered UVM-style TB.
#
# This validator intentionally rejects partial support-file drops and flat
# cocotb tests for SSOT TB work. The default /ssot-tb backend is pyuvm/cocotb,
# so the agent must produce executable orchestration plus the UVM-style layers.

set -u

IP="${IP_NAME:-${1:-}}"
if [ -z "$IP" ]; then
    IP=$(find . -maxdepth 3 -type f -name "*.ssot.yaml" 2>/dev/null \
         | sort -t/ -k2 | head -1 | awk -F/ '{print $(NF-2)}')
fi

if [ -z "$IP" ] || [ ! -d "$IP" ]; then
    echo "[check_pyuvm_structure] FAIL: cannot locate IP directory"
    exit 1
fi

TB_DIR="$IP/tb/cocotb"
TEST="$TB_DIR/test_$IP.py"
RUNNER="$TB_DIR/test_runner.py"
SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"

fail=0
for path in "$TEST" "$RUNNER"; do
    if [ ! -s "$path" ]; then
        echo "[check_pyuvm_structure] FAIL: missing or empty $path"
        fail=1
    fi
done

if [ ! -d "$TB_DIR" ]; then
    echo "[check_pyuvm_structure] FAIL: missing $TB_DIR"
    exit 1
fi

ALL_TEXT="$(find "$TB_DIR" -maxdepth 1 -type f -name '*.py' -print0 2>/dev/null | xargs -0 cat 2>/dev/null || true)"

require_pattern() {
    local label="$1"
    local pattern="$2"
    if ! printf '%s\n' "$ALL_TEXT" | grep -Eiq "$pattern"; then
        echo "[check_pyuvm_structure] FAIL: missing $label ($pattern)"
        fail=1
    fi
}

require_pattern "transaction / sequence item" 'transaction|sequence[[:space:]_]*item|uvm_sequence_item'
require_pattern "sequence" 'class[[:space:]].*sequence|uvm_sequence|start_item|finish_item'
require_pattern "driver" 'class[[:space:]].*driver|uvm_driver|drive_'
require_pattern "monitor" 'class[[:space:]].*monitor|uvm_monitor|monitor_'
require_pattern "scoreboard" 'scoreboard|uvm_scoreboard|expected.*got|got.*expected'
require_pattern "coverage collector" 'coverage|coverpoint|functional_bins|coverage_bins'
require_pattern "environment" 'uvm_env|class[[:space:]].*env'
require_pattern "assertion failure path" 'raise[[:space:]]+AssertionError|assert[[:space:]][^=]'

if python3 - <<'PY' >/dev/null 2>&1
import pyuvm  # noqa: F401
PY
then
    if ! printf '%s\n' "$ALL_TEXT" | grep -Eq '(^|[[:space:]])(import pyuvm|from pyuvm import|uvm_test|uvm_env|uvm_component)'; then
        echo "[check_pyuvm_structure] FAIL: pyuvm imports in this environment, but TB has no pyuvm component usage"
        fail=1
    fi
else
    if ! printf '%s\n' "$ALL_TEXT" | grep -Eiq 'pyuvm.*unavailable|cocotb-native.*fallback|fallback.*pyuvm'; then
        echo "[check_pyuvm_structure] FAIL: pyuvm unavailable fallback reason is not documented in TB files"
        fail=1
    fi
fi

if ! python3 "$SCRIPT_DIR/check_tb_python_compile.py" "$IP" --root . >/tmp/check_pyuvm_structure.$$ 2>&1; then
    cat /tmp/check_pyuvm_structure.$$
    rm -f /tmp/check_pyuvm_structure.$$
    echo "[check_pyuvm_structure] FAIL: Python syntax check failed"
    exit 1
fi
rm -f /tmp/check_pyuvm_structure.$$

if [ -f "$IP/verify/equivalence_goals.json" ]; then
    if ! python3 "$SCRIPT_DIR/check_scoreboard_events.py" "$IP" --root . --source-check >/tmp/check_scoreboard_events.$$ 2>&1; then
        cat /tmp/check_scoreboard_events.$$
        rm -f /tmp/check_scoreboard_events.$$
        fail=1
    else
        cat /tmp/check_scoreboard_events.$$
        rm -f /tmp/check_scoreboard_events.$$
    fi
fi

if [ "$fail" -ne 0 ]; then
    echo "[check_pyuvm_structure] Disk reality is not a complete UVM-style cocotb environment."
    exit 1
fi

echo "[check_pyuvm_structure] PASS: layered pyuvm/cocotb structure exists for $IP"
exit 0
