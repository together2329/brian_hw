"""Evidence for the CL (cycle) model semantic-validation gate.

The cycle-domain twin of the FL semantic gate: a behavioral contract carrying
``cycle_model_waiver=true`` is combinational, so the CL model must not declare
cycle-level timing (handshake / ordering / pipeline / multi-cycle latency). These
tests pin:

  * the deterministic backstop FAILS such fictional timing without any LLM;
  * a genuinely stateful IP (contracts not waived) is NOT false-flagged;
  * the gate is inactive (pass) when there is no locked contract authority;
  * the LLM judge degrades to an explicit ``not_run`` — never a silent pass;
  * emit_cycle_model wires the gate so fictional timing blocks CL emission.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workflow" / "fl-model-gen" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_cl_semantics import validate_cl_semantics  # noqa: E402

EMIT_CYCLE_MODEL = SCRIPTS / "emit_cycle_model.py"


# --------------------------------------------------------------------------- #
# Fixtures: minimal but schema-valid IP trees
# --------------------------------------------------------------------------- #
_FICTIONAL_CYCLE_MODEL = {
    "executable": "python",
    "latency": {
        "primary_operation": {"min_cycles": 1, "max_cycles": None,
                              "description": "waits on a fictional handshake"},
    },
    "handshake_rules": [
        {"signal": "valid/ready", "rule": "valid payload stable until ready"},
    ],
    "ordering": ["Updates occur after the operation reaches its terminal FSM state."],
}


def _write_ip(
    root: Path,
    ip: str,
    *,
    cycle_model_waiver: bool,
    cycle_model: dict | None = None,
    state_variables: list | None = None,
    sequential: bool = False,
) -> Path:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)
    (ip_dir / "model").mkdir(parents=True)

    fm: dict = {
        "transactions": [
            {
                "id": "primary_operation",
                "name": "primary_operation",
                "contract_refs": [f"BC-{ip.upper()}-OP"],
                "output_rules": ["out = f(in)"],
            }
        ],
    }
    if state_variables:
        fm["state_variables"] = state_variables

    ssot: dict = {
        "ip": ip,
        "top_module": {"name": ip},
        "function_model": fm,
    }
    if cycle_model is not None:
        ssot["cycle_model"] = cycle_model

    import yaml  # local import: only the tests need a yaml dumper

    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8"
    )

    decision_table = (
        [{"when": "en==1 at rising clk", "then": "count += 1 next cycle"}]
        if sequential
        else [{"when": "any in", "then": "out = f(in)"}]
    )
    contract = {
        "id": f"BC-{ip.upper()}-OP",
        "decision_table": decision_table,
        "obligations": [f"OBL_{ip.upper()}_OP_001"],
        "stage_contracts": [
            {"stage": "rtl", "check": "RTL realizes out = f(in)",
             "pass_condition": "rtl_compile PASS", "validator": "rtl_compile_report.py"},
            {"stage": "tb", "check": "scoreboard matches decision table",
             "pass_condition": "scoreboard PASS", "validator": "check_scoreboard_events.py"},
        ],
    }
    if cycle_model_waiver:
        contract["cycle_model_waiver"] = True
    (ip_dir / "req" / "behavioral_contracts.json").write_text(
        json.dumps({"ip": ip, "schema_version": 1, "type": "behavioral_contracts",
                    "contracts": [contract]}, indent=2),
        encoding="utf-8",
    )
    (ip_dir / "req" / "obligations.json").write_text(
        json.dumps({"ip": ip, "obligations": [{"obligation_id": f"OBL_{ip.upper()}_OP_001"}]}),
        encoding="utf-8",
    )
    return ip_dir


# --------------------------------------------------------------------------- #
# Deterministic backstop
# --------------------------------------------------------------------------- #
def test_cl_gate_flags_fictional_timing_deterministic(tmp_path: Path) -> None:
    """A cycle-waived (combinational) IP with handshake/latency timing FAILS."""
    _write_ip(tmp_path, "comb_ip", cycle_model_waiver=True,
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL))
    report = validate_cl_semantics("comb_ip", tmp_path, use_llm=False)

    assert report["passed"] is False
    assert report["status"] == "fail"
    assert report["deterministic_backstop"]["status"] == "fail"
    kinds = {v.get("subkind") for v in report["deterministic_backstop"]["violations"]}
    assert "handshake" in kinds
    assert "latency" in kinds
    assert all(v["kind"] == "fictional_timing"
               for v in report["deterministic_backstop"]["violations"])


def test_cl_gate_no_false_positive_on_stateful_ip(tmp_path: Path) -> None:
    """A genuinely sequential IP (clocked decision table) is not flagged — the
    criterion is the decision-table vocabulary, not the fictional state_variables."""
    _write_ip(tmp_path, "seq_ip", cycle_model_waiver=False, sequential=True,
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL),
              state_variables=[{"name": "count", "width": 8}])
    report = validate_cl_semantics("seq_ip", tmp_path, use_llm=False)

    assert report["passed"] is True
    assert report["deterministic_backstop"]["violations"] == []


def test_cl_gate_catches_fictional_timing_without_explicit_waiver(tmp_path: Path) -> None:
    """ROOT FIX: a combinational contract (no clocked vocabulary) carrying a
    fictional cycle_model is caught deterministically even with NO
    cycle_model_waiver flag — the waiver is derived from the locked decision
    table, not an optional field (the mux4_v1 class that the explicit-flag-only
    backstop missed). Closes OBL_TRUTH_COMBINATIONAL_WAIVER_AUTOSET."""
    _write_ip(tmp_path, "comb_noflag", cycle_model_waiver=False,  # flag absent
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL))
    report = validate_cl_semantics("comb_noflag", tmp_path, use_llm=False)
    assert report["passed"] is False
    assert report["status"] == "fail"
    assert any(v["kind"] == "fictional_timing"
               for v in report["deterministic_backstop"]["violations"])


def test_cl_gate_inactive_without_contract_authority(tmp_path: Path) -> None:
    """No behavioral_contracts.json → gate is inactive, not a hard fail."""
    ip_dir = tmp_path / "bare_ip"
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / "bare_ip.ssot.yaml").write_text(
        "ip: bare_ip\ntop_module: {name: bare_ip}\ncycle_model: {handshake_rules: [x]}\n",
        encoding="utf-8",
    )
    report = validate_cl_semantics("bare_ip", tmp_path, use_llm=False)
    assert report["status"] == "inactive"
    assert report["passed"] is True


def test_cl_gate_inactive_without_cycle_model(tmp_path: Path) -> None:
    """No cycle_model section → no CL artifact → no fictional timing possible."""
    _write_ip(tmp_path, "nocm_ip", cycle_model_waiver=True, cycle_model=None)
    report = validate_cl_semantics("nocm_ip", tmp_path, use_llm=False)
    assert report["status"] == "inactive"
    assert report["passed"] is True


# --------------------------------------------------------------------------- #
# Safe degradation — never a silent pass
# --------------------------------------------------------------------------- #
def test_cl_gate_llm_unavailable_records_not_run(tmp_path: Path, monkeypatch) -> None:
    """When the real LLM cannot be constructed the judge is an explicit
    ``not_run`` (never a silent pass), while the deterministic layer still gates."""
    import validate_cl_semantics as mod

    monkeypatch.setattr(mod, "_default_provider", lambda: (None, "gpt-5.4"))
    _write_ip(tmp_path, "comb_ip2", cycle_model_waiver=True,
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL))
    report = validate_cl_semantics("comb_ip2", tmp_path, use_llm=True)

    assert report["llm_judge"]["status"] == "not_run"
    assert report["llm_judge"]["ran"] is False
    # The deterministic backstop still fails the fictional timing — not masked.
    assert report["passed"] is False


# --------------------------------------------------------------------------- #
# emit_cycle_model wiring
# --------------------------------------------------------------------------- #
def test_emit_cycle_model_blocks_on_fictional_timing(tmp_path: Path) -> None:
    """emit_cycle_model exits non-zero and records the semantic FAIL in the
    cl_model_check.json report when fictional timing is present."""
    _write_ip(tmp_path, "emit_comb", cycle_model_waiver=True,
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL))
    # A trivial FunctionalModel so the generated CL self-check can import it.
    (tmp_path / "emit_comb" / "model" / "functional_model.py").write_text(
        "class FunctionalModel:\n"
        "    def __init__(self, params=None): self.params = params\n"
        "    def reset(self): pass\n"
        "    def apply(self, txn): return {'kind': txn.get('kind', 'primary_operation')}\n",
        encoding="utf-8",
    )
    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), "emit_comb",
         "--root", str(tmp_path), "--no-semantic-llm"],
        text=True, capture_output=True, check=False,
    )
    assert run.returncode != 0, run.stdout + run.stderr
    assert "SEMANTIC GATE FAIL" in run.stdout

    report = json.loads(
        (tmp_path / "emit_comb" / "model" / "cl_model_check.json").read_text(encoding="utf-8")
    )
    assert report["passed"] is False
    sv = report["semantic_validation"]
    assert sv["status"] == "fail"
    assert sv["passed"] is False
    assert sv["llm_judge"]["status"] == "not_run"


def test_emit_cycle_model_no_semantic_flag_skips_gate(tmp_path: Path) -> None:
    """--no-semantic records skipped (audit trail) and does not block on the
    semantic layer (the self-check / symbol-contract still govern)."""
    _write_ip(tmp_path, "emit_skip", cycle_model_waiver=True,
              cycle_model=dict(_FICTIONAL_CYCLE_MODEL))
    (tmp_path / "emit_skip" / "model" / "functional_model.py").write_text(
        "class FunctionalModel:\n"
        "    def __init__(self, params=None): self.params = params\n"
        "    def reset(self): pass\n"
        "    def apply(self, txn): return {'kind': txn.get('kind', 'primary_operation')}\n",
        encoding="utf-8",
    )
    run = subprocess.run(
        [sys.executable, str(EMIT_CYCLE_MODEL), "emit_skip",
         "--root", str(tmp_path), "--no-semantic"],
        text=True, capture_output=True, check=False,
    )
    report = json.loads(
        (tmp_path / "emit_skip" / "model" / "cl_model_check.json").read_text(encoding="utf-8")
    )
    assert report["semantic_validation"]["status"] == "skipped"


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
