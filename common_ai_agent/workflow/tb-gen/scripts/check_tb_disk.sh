#!/usr/bin/env bash
# check_tb_disk.sh — Disk-truth validator for tb-gen tasks.
#
# Verifies the deliverables that a TB-gen task CLAIMS to have produced
# actually exist on disk with non-trivial size. Replaces the previous
# stdout-grep-only validator that lets agents fake completions by
# echoing "0 errors, 0 warnings" without running anything.
#
# Supports four verification surfaces:
#   - cocotb/Python: <ip>/tb/cocotb/test_<ip>.py + test_runner.py
#   - cocotb flat:   <ip>/tb/test_<ip>.py + test_runner.py
#   - cocotb sim:    <ip>/sim/test_<ip>.py + <ip>/sim/Makefile (Makefile IS the runner)
#   - legacy SV:     <ip>/tb/tb_<ip>.sv + <ip>/tc/tc_<ip>.sv + list/<ip>.f
#
# Inputs (env vars):
#   IP_NAME — IP root name (default: derived from current working directory).
#   MIN_PY  — minimum bytes for cocotb Python files (default 500)
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

MIN_PY="${MIN_PY:-500}"
MIN_TC="${MIN_TC:-1000}"
MIN_TB="${MIN_TB:-500}"
MIN_F="${MIN_F:-50}"

TC="$IP/tc/tc_$IP.sv"
TB="$IP/tb/tb_$IP.sv"
LIST="$IP/list/$IP.f"
COCOTB_TEST="$IP/tb/cocotb/test_$IP.py"
COCOTB_RUNNER="$IP/tb/cocotb/test_runner.py"
COCOTB_RUN_TESTS="$IP/tb/cocotb/run_tests.py"
FLAT_COCOTB_TEST="$IP/tb/test_$IP.py"
FLAT_COCOTB_RUNNER="$IP/tb/test_runner.py"
FLAT_COCOTB_RUN_TESTS="$IP/tb/run_tests.py"
MAKEFILE="$IP/Makefile"
UVM_DIR="$IP/tb/uvm"

_size() { [ -f "$1" ] && wc -c < "$1" | tr -d ' ' || echo 0; }

_check_cocotb_layout() {
    test_path="$1"
    runner_path="$2"
    layout="$3"

    TEST_SZ=$(_size "$test_path")
    RUNNER_SZ=$(_size "$runner_path")
    FAIL=0
    [ "$TEST_SZ" -lt "$MIN_PY" ] && { echo "[check_tb_disk] FAIL: $test_path = ${TEST_SZ}B (need ≥${MIN_PY})"; FAIL=1; }
    [ "$RUNNER_SZ" -lt "$MIN_PY" ] && { echo "[check_tb_disk] FAIL: $runner_path = ${RUNNER_SZ}B (need ≥${MIN_PY})"; FAIL=1; }
    if [ $FAIL -ne 0 ]; then
        return 1
    fi

    if ! grep -Eq '^[[:space:]]*(import cocotb|from cocotb)' "$test_path"; then
        echo "[check_tb_disk] FAIL: $test_path does not import cocotb"
        return 1
    fi
    if ! grep -Eq "get_runner|cocotb_test|pytest|cocotb" "$runner_path"; then
        echo "[check_tb_disk] FAIL: $runner_path is not a recognizable cocotb runner"
        return 1
    fi
    if grep -q '\[FAIL\]' "$test_path" && ! grep -Eq 'raise[[:space:]]+AssertionError|assert[[:space:]]+[^=]' "$test_path"; then
        echo "[check_tb_disk] FAIL: $test_path logs [FAIL] but has no assertion/raise path"
        echo "  Hint: SSOT scenario failures must fail cocotb, not only increment counters or log text."
        return 1
    fi
    if [ -f "$MAKEFILE" ] && grep -Eq "tb_${IP}\.sv|tc_${IP}\.sv|tb/.*\.sv|tc/.*\.sv" "$MAKEFILE"; then
        echo "[check_tb_disk] FAIL: $MAKEFILE references legacy SV TB while cocotb layout is present"
        return 1
    fi

    echo "[check_tb_disk] PASS: ${layout} cocotb test=${TEST_SZ}B runner=${RUNNER_SZ}B"
    return 0
}

if [ -f "$COCOTB_TEST" ] || [ -f "$COCOTB_RUNNER" ] || [ -f "$COCOTB_RUN_TESTS" ]; then
    if [ ! -f "$COCOTB_RUNNER" ] && [ -f "$COCOTB_RUN_TESTS" ]; then
        COCOTB_RUNNER="$COCOTB_RUN_TESTS"
    fi
    _check_cocotb_layout "$COCOTB_TEST" "$COCOTB_RUNNER" "tb/cocotb" && exit 0
    echo "[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real."
    exit 1
fi

if [ -f "$FLAT_COCOTB_TEST" ] || [ -f "$FLAT_COCOTB_RUNNER" ] || [ -f "$FLAT_COCOTB_RUN_TESTS" ]; then
    if [ ! -f "$FLAT_COCOTB_RUNNER" ] && [ -f "$FLAT_COCOTB_RUN_TESTS" ]; then
        FLAT_COCOTB_RUNNER="$FLAT_COCOTB_RUN_TESTS"
    fi
    _check_cocotb_layout "$FLAT_COCOTB_TEST" "$FLAT_COCOTB_RUNNER" "tb" && exit 0
    echo "[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real."
    exit 1
fi

# ── Layout: tb/uvm/ SystemVerilog UVM ──────────────────────────────────────
_check_uvm_layout() {
    local dir="$1"
    local all_text
    local fail=0
    local files
    files=$(find "$dir" -maxdepth 1 -type f \( -name '*.sv' -o -name '*.svh' -o -name '*.f' \) 2>/dev/null | sort)
    if [ -z "$files" ]; then
        echo "[check_tb_disk] FAIL: $dir has no UVM source files"
        return 1
    fi
    all_text="$(printf '%s\n' "$files" | xargs cat 2>/dev/null || true)"

    if [ "$(printf '%s\n' "$all_text" | wc -c | tr -d ' ')" -lt 1000 ]; then
        echo "[check_tb_disk] FAIL: $dir UVM sources are too small to be a real environment"
        return 1
    fi

    require_uvm_pattern() {
        label="$1"
        pattern="$2"
        if ! printf '%s\n' "$all_text" | grep -Eiq "$pattern"; then
            echo "[check_tb_disk] FAIL: UVM layout missing $label ($pattern)"
            fail=1
        fi
    }

    require_uvm_pattern "uvm package/import" '`include[[:space:]]+"uvm_macros\.svh"|import[[:space:]]+uvm_pkg::\*'
    require_uvm_pattern "interface or virtual interface" 'interface[[:space:]]|virtual[[:space:]]+.*interface'
    require_uvm_pattern "sequence item / transaction" 'uvm_sequence_item|class[[:space:]].*(transaction|item)'
    require_uvm_pattern "sequence" 'uvm_sequence|class[[:space:]].*sequence'
    require_uvm_pattern "driver" 'uvm_driver|class[[:space:]].*driver'
    require_uvm_pattern "monitor" 'uvm_monitor|class[[:space:]].*monitor'
    require_uvm_pattern "scoreboard" 'uvm_scoreboard|class[[:space:]].*scoreboard|expected.*got|got.*expected'
    require_uvm_pattern "coverage collector" 'covergroup|coverage|coverpoint'
    require_uvm_pattern "environment" 'uvm_env|class[[:space:]].*env'
    require_uvm_pattern "test" 'uvm_test|class[[:space:]].*test'
    require_uvm_pattern "assertion/fatal failure path" '`uvm_error|`uvm_fatal|\$fatal|assert[[:space:]]*\('

    if [ "$fail" -ne 0 ]; then
        return 1
    fi
    echo "[check_tb_disk] PASS: tb/uvm UVM structure exists under $dir"
    return 0
}

if [ -d "$UVM_DIR" ]; then
    _check_uvm_layout "$UVM_DIR" && exit 0
    echo "[check_tb_disk] Disk reality contradicts claimed UVM completion. Run write_file/run_command for real."
    exit 1
fi

# ── Layout: sim/ Makefile-based cocotb ──────────────────────────────────────
# Some cocotb flows put the test file and Makefile directly in <ip>/sim/
# without a separate runner script. The Makefile IS the runner.
SIM_COCOTB_TEST="$IP/sim/test_$IP.py"
SIM_MAKEFILE="$IP/sim/Makefile"

_check_sim_cocotb_layout() {
    local test_path="$1"
    local makefile_path="$2"

    TEST_SZ=$(_size "$test_path")
    MAKEFILE_SZ=$(_size "$makefile_path")
    FAIL=0
    [ "$TEST_SZ" -lt "$MIN_PY" ] && { echo "[check_tb_disk] FAIL: $test_path = ${TEST_SZ}B (need ≥${MIN_PY})"; FAIL=1; }
    [ "$MAKEFILE_SZ" -lt "$MIN_F" ] && { echo "[check_tb_disk] FAIL: $makefile_path = ${MAKEFILE_SZ}B (need ≥${MIN_F})"; FAIL=1; }
    if [ $FAIL -ne 0 ]; then
        return 1
    fi

    if ! grep -Eq '^[[:space:]]*(import cocotb|from cocotb)' "$test_path"; then
        echo "[check_tb_disk] FAIL: $test_path does not import cocotb"
        return 1
    fi

    # Makefile must reference cocotb-compatible settings.
    if ! grep -Eq '(MODULE|TOPLEVEL_LANG|cocotb|COCOTB)' "$makefile_path"; then
        echo "[check_tb_disk] FAIL: $makefile_path does not reference cocotb settings (MODULE, TOPLEVEL_LANG, COCOTB)"
        return 1
    fi

    if grep -q '\[FAIL\]' "$test_path" && ! grep -Eq 'raise[[:space:]]+AssertionError|assert[[:space:]]+[^=]' "$test_path"; then
        echo "[check_tb_disk] FAIL: $test_path logs [FAIL] but has no assertion/raise path"
        echo "  Hint: SSOT scenario failures must fail cocotb, not only increment counters or log text."
        return 1
    fi

    if grep -Eq "tb_${IP}\.sv|tc_${IP}\.sv|tb/.*\.sv|tc/.*\.sv" "$makefile_path"; then
        echo "[check_tb_disk] FAIL: $makefile_path references legacy SV TB while cocotb layout is present"
        return 1
    fi

    echo "[check_tb_disk] PASS: sim/ cocotb test=${TEST_SZ}B makefile=${MAKEFILE_SZ}B"
    return 0
}

if [ -f "$SIM_COCOTB_TEST" ] && [ -f "$SIM_MAKEFILE" ]; then
    _check_sim_cocotb_layout "$SIM_COCOTB_TEST" "$SIM_MAKEFILE" && exit 0
    echo "[check_tb_disk] Disk reality contradicts claimed cocotb completion. Run write_file/run_command for real."
    exit 1
fi

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
