#!/usr/bin/env bash
# =============================================================================
# build_gate.sh — RTL build-time gate orchestrator
# =============================================================================
# Runs all SSOT-driven contract checks BEFORE the simulator gets to
# touch the design. Any failure here aborts the loop with a clear
# repair_prompt and avoids burning sim cycles on an already-broken
# build.
#
# Usage:
#   build_gate.sh <ip> [--root .]
#
# Gates (in order):
#   G1  YAML validity                    (yaml.safe_load)
#   G2  SSOT completeness                (timing_constraints / invariants /
#                                         forbidden_states / forbidden_environment
#                                         non-empty)
#   G3  Register layout contract         (check_register_contract.py)
#   G4  TB magic-number lint             (check_tb_magic_numbers.py)
#   G5  RTL lint (verilator --lint-only) (single-driver, latch, etc.)
#   G6  Formal property emit (no run)    (emit_formal_properties.py — succeeds
#                                         iff invariants/forbidden parse OK)
#   G7  Timing header emit               (emit_timing_header.py — succeeds iff
#                                         timing_constraints parse OK)
#
# Each gate writes into <ip>/lint/build_gate.json with its result. A
# single non-pass gate fails the whole script.
#
# Exit codes:
#   0  all gates pass (or skip-allowed)
#   1  any gate failed
#   2  bad usage / missing dirs
# =============================================================================
set -uo pipefail

IP=""
ROOT="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --root=*) ROOT="${1#*=}"; shift ;;
        -*)
            echo "[build_gate] unknown flag: $1" >&2
            exit 2
            ;;
        *)
            if [[ -z "$IP" ]]; then IP="$1"; else
                echo "[build_gate] extra positional: $1" >&2
                exit 2
            fi
            shift
            ;;
    esac
done

if [[ -z "$IP" ]]; then
    echo "usage: build_gate.sh <ip> [--root .]" >&2
    exit 2
fi

ROOT="$(cd "$ROOT" && pwd)"
IP_DIR="$ROOT/$IP"

if [[ ! -d "$IP_DIR" ]]; then
    echo "[build_gate] missing IP dir: $IP_DIR" >&2
    exit 2
fi

# Resolve script directory (workflow/rtl-gen/scripts) and infer
# common_ai_agent root for sibling scripts.
SCRIPTS_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"
WORKFLOW_DIR="$( cd "$SCRIPTS_DIR/../.." && pwd )"

mkdir -p "$IP_DIR/lint"
GATE_JSON="$IP_DIR/lint/build_gate.json"

cyan() { printf "\033[1;36m%s\033[0m\n" "$*"; }
red()  { printf "\033[1;31m%s\033[0m\n" "$*"; }
green(){ printf "\033[1;32m%s\033[0m\n" "$*"; }
gate_status="pass"
declare -a gate_log=()

run_gate() {
    local name="$1"
    shift
    cyan "▸ $name"
    if "$@"; then
        gate_log+=("\"$name\":\"pass\"")
    else
        local rc=$?
        red "  ✗ $name failed (rc=$rc)"
        gate_log+=("\"$name\":\"fail\"")
        gate_status="fail"
    fi
}

# G1 — YAML validity
run_gate "G1_yaml_valid" python3 -c "
import yaml, sys
yaml.safe_load(open('$IP_DIR/yaml/$IP.ssot.yaml'))
print('[G1] YAML parses')
"

# G2 — SSOT negative spec presence
run_gate "G2_ssot_negative_spec" python3 -c "
import yaml, sys
d = yaml.safe_load(open('$IP_DIR/yaml/$IP.ssot.yaml'))
required = ['timing_constraints', 'invariants', 'forbidden_states',
            'forbidden_environment']
missing = [k for k in required if not d.get(k)]
if missing:
    print('[G2] missing/empty negative spec:', missing); sys.exit(1)
print(f'[G2] negative spec OK ({len(d[\"invariants\"])} invariants, '
      f'{len(d[\"forbidden_states\"])} forbidden_states, '
      f'{len(d[\"forbidden_environment\"])} forbidden_env)')
"

# G3 — Register layout contract
run_gate "G3_register_contract" \
    python3 "$WORKFLOW_DIR/rtl-gen/scripts/check_register_contract.py" \
    "$IP" --root "$ROOT"

# G4 — TB magic numbers (warning-only is OK; only error fails)
run_gate "G4_tb_magic_numbers" \
    python3 "$WORKFLOW_DIR/tb-gen/scripts/check_tb_magic_numbers.py" \
    "$IP" --root "$ROOT"

# G5 — RTL lint (verilator if available)
if command -v verilator >/dev/null 2>&1; then
    run_gate "G5_rtl_lint" bash -c "
set -e
cd '$IP_DIR'
RTL_FILES=\$(ls rtl/*.sv 2>/dev/null)
if [ -z \"\$RTL_FILES\" ]; then
    echo '[G5] no RTL files'
    exit 1
fi
verilator --lint-only --Wall -Wno-fatal -Irtl \$RTL_FILES 2>&1 | tee lint/verilator_lint.log
LINT_RC=\${PIPESTATUS[0]}
if [ \"\$LINT_RC\" -ne 0 ]; then
    echo '[G5] verilator lint reported issues (see lint/verilator_lint.log)'
    # don't fail immediately on warnings; only error-level matters.
    if grep -qE '%Error' lint/verilator_lint.log; then
        exit 1
    fi
fi
echo '[G5] RTL lint OK'
"
else
    echo "[G5] verilator not in PATH — skipping RTL lint"
    gate_log+=("\"G5_rtl_lint\":\"skip\"")
fi

# G6 — Formal property emit (parse only)
run_gate "G6_formal_emit" \
    python3 "$WORKFLOW_DIR/fl-model-gen/scripts/emit_formal_properties.py" \
    "$IP" --root "$ROOT"

# G7 — Timing header emit
run_gate "G7_timing_header" \
    python3 "$WORKFLOW_DIR/tb-gen/scripts/emit_timing_header.py" \
    "$IP" --root "$ROOT"

# G8 — Single-driver check (catches multi-NBA-driven regs that
# verilator passes silently — this is the SC3-class bug detector).
run_gate "G8_single_driver" \
    python3 "$WORKFLOW_DIR/rtl-gen/scripts/check_single_driver.py" \
    "$IP" --root "$ROOT"

# Write gate JSON
{
    printf '{\n'
    printf '  "schema_version": 1,\n'
    printf '  "type": "build_gate",\n'
    printf '  "ip": "%s",\n' "$IP"
    printf '  "overall_status": "%s",\n' "$gate_status"
    printf '  "gates": {\n    %s\n  }\n' "$(IFS=','; echo "${gate_log[*]}")"
    printf '}\n'
} > "$GATE_JSON"

if [[ "$gate_status" == "pass" ]]; then
    green "▣ build_gate ALL PASS  ($GATE_JSON)"
    exit 0
else
    red "▣ build_gate FAILED  ($GATE_JSON)"
    exit 1
fi
