#!/usr/bin/env bash
# =============================================================================
# stage_gate.sh <stage> <ip> --root <root>
# -----------------------------------------------------------------------------
# Deterministic VCM gate for the tb / sim / lint stages, with a detect-and-skip
# policy: pure python/bash checks are HARD; checks that need an external tool
# (iverilog / verilator / cocotb / pyslang) run only when that tool is present,
# otherwise they SKIP with a warning. EXCEPTION: the `sim` stage BLOCKS (exit 2)
# when no simulator is installed — running the simulator is the whole point of
# the stage, so a missing simulator must not silently pass.
#
# Stage scopes (closure_stage aware): tb/lint check stage-local deliverables;
# full obligation closure (check_evidence_contract.py) runs at the sim stage,
# where runtime evidence exists.
#
# Exit: 0 = all hard checks passed (skips allowed) ; 1 = a hard check failed
#       2 = blocked (sim stage, no simulator)
# =============================================================================
set -uo pipefail

STAGE="${1:-}"; shift || true
IP=""
ROOT="."
while [[ $# -gt 0 ]]; do
    case "$1" in
        --root) ROOT="$2"; shift 2 ;;
        --root=*) ROOT="${1#*=}"; shift ;;
        -*) echo "[stage_gate] unknown flag: $1" >&2; exit 2 ;;
        *) if [[ -z "$IP" ]]; then IP="$1"; fi; shift ;;
    esac
done
if [[ -z "$STAGE" || -z "$IP" ]]; then
    echo "usage: stage_gate.sh <tb|sim|lint> <ip> --root <root>" >&2
    exit 2
fi

SCRIPTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
WF="$(cd "$SCRIPTS_DIR/../.." && pwd)"   # workflow/ (script lives in workflow/req-gen/scripts)
ROOT="$(cd "$ROOT" 2>/dev/null && pwd || echo "$ROOT")"
cd "$ROOT" || { echo "[stage_gate] cannot cd to root: $ROOT" >&2; exit 2; }

status=0
have_tool(){ command -v "$1" >/dev/null 2>&1; }
have_py(){ python3 -c "import $1" >/dev/null 2>&1; }

run_hard(){ local name="$1"; shift; echo "▸ $name"; if "$@"; then echo "  ✓ $name"; else echo "  ✗ $name failed (rc=$?)"; status=1; fi; }
run_skip(){ local cond="$1"; local name="$2"; shift 2; if eval "$cond"; then run_hard "$name" "$@"; else echo "  [skip] $name: required tooling absent"; fi; }

case "$STAGE" in
    tb)
        run_hard "tb_python_compile" python3 "$WF/tb-gen/scripts/check_tb_python_compile.py" "$IP" --root .
        run_hard "scoreboard_source" python3 "$WF/tb-gen/scripts/check_scoreboard_events.py" "$IP" --root . --source-check
        run_hard "scoreboard_self_check" python3 "$WF/tb-gen/runtime/equivalence_scoreboard.py" "$IP" --root . --self-check
        run_skip "have_py cocotb" "pyuvm_structure" bash "$WF/tb-gen/scripts/check_pyuvm_structure.sh" "$IP"
        ;;
    lint)
        run_skip "have_tool verilator || have_py pyslang" "dut_lint" \
            python3 "$WF/lint/scripts/dut_lint_report.py" "$IP" --root .
        ;;
    sim)
        if ! have_tool iverilog && ! have_tool verilator; then
            echo "  🛑 sim BLOCKED: no simulator (iverilog/verilator) installed"
            exit 2
        fi
        run_hard "sim_run" bash "$WF/tb-gen/scripts/sim.sh" "$IP"
        run_hard "sim_evidence" bash "$WF/tb-gen/scripts/check_tb_sim_evidence.sh" "$IP"
        run_hard "evidence_contract_closure" python3 "$WF/contract-reflection/scripts/check_evidence_contract.py" "$IP" --root .
        ;;
    *)
        echo "[stage_gate] unknown stage: $STAGE" >&2; exit 2 ;;
esac

if [[ "$status" -eq 0 ]]; then
    echo "▣ stage_gate($STAGE) PASS"
else
    echo "▣ stage_gate($STAGE) FAILED"
fi
exit "$status"
