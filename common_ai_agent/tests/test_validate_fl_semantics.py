"""Evidence for the FL (functional) model semantic-validation gate.

Twin of ``test_validate_cl_semantics``. A behavioral contract carrying
``cycle_model_waiver=true`` is combinational, so the FL model must not introduce
state-control machinery (an FSM, ``state_updates``, undeclared
``state_variables``). These tests pin:

  * the deterministic backstop FAILS fictional state without any LLM;
  * a genuinely stateful IP (contracts not waived) is NOT false-flagged;
  * the gate is inactive (pass) without locked contract authority;
  * the LLM judge degrades to an explicit ``not_run`` — never a silent pass.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

import pytest

REPO = Path(__file__).resolve().parents[1]
SCRIPTS = REPO / "workflow" / "fl-model-gen" / "scripts"
if str(SCRIPTS) not in sys.path:
    sys.path.insert(0, str(SCRIPTS))

from validate_fl_semantics import validate_fl_semantics  # noqa: E402


def _write_ip(
    root: Path,
    ip: str,
    *,
    cycle_model_waiver: bool,
    fsm: dict | None = None,
    state_variables: list | None = None,
    state_updates: list | None = None,
    sequential: bool = False,
) -> Path:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "req").mkdir(parents=True)

    txn: dict = {
        "id": "primary_operation",
        "name": "primary_operation",
        "contract_refs": [f"BC-{ip.upper()}-OP"],
        "output_rules": ["out = f(in)"],
    }
    if state_updates:
        txn["state_updates"] = state_updates

    fm: dict = {"transactions": [txn]}
    if state_variables:
        fm["state_variables"] = state_variables

    ssot: dict = {"ip": ip, "top_module": {"name": ip}, "function_model": fm}
    if fsm is not None:
        ssot["fsm"] = fsm

    import yaml

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


def test_fl_gate_flags_fictional_fsm_deterministic(tmp_path: Path) -> None:
    """A cycle-waived (combinational) IP carrying an FSM + state_variables FAILS."""
    _write_ip(
        tmp_path, "comb_fl", cycle_model_waiver=True,
        fsm={"states": ["IDLE", "EXEC", "DONE"],
             "transitions": [{"from": "IDLE", "to": "EXEC"}]},
        state_variables=[{"name": "phase", "width": 2}],
    )
    report = validate_fl_semantics("comb_fl", tmp_path, use_llm=False)
    assert report["passed"] is False
    assert report["status"] == "fail"
    assert report["deterministic_backstop"]["status"] == "fail"
    assert any(v["kind"] == "fictional_state"
               for v in report["deterministic_backstop"]["violations"])


def test_fl_gate_flags_fictional_state_updates(tmp_path: Path) -> None:
    """A waived contract's transaction carrying state_updates FAILS."""
    _write_ip(
        tmp_path, "comb_fl2", cycle_model_waiver=True,
        state_updates=[{"name": "phase", "next": "phase + 1"}],
    )
    report = validate_fl_semantics("comb_fl2", tmp_path, use_llm=False)
    assert report["passed"] is False
    assert any(v["kind"] == "fictional_state"
               for v in report["deterministic_backstop"]["violations"])


def test_fl_gate_no_false_positive_on_stateful_ip(tmp_path: Path) -> None:
    """A genuinely sequential IP (clocked decision table) keeps its FSM/state —
    the criterion is the decision-table vocabulary, not the SSOT state_variables."""
    _write_ip(
        tmp_path, "seq_fl", cycle_model_waiver=False, sequential=True,
        fsm={"states": ["IDLE", "COUNT"]},
        state_variables=[{"name": "count", "width": 8}],
        state_updates=[{"name": "count", "next": "count + 1"}],
    )
    report = validate_fl_semantics("seq_fl", tmp_path, use_llm=False)
    assert report["passed"] is True
    assert report["deterministic_backstop"]["violations"] == []


def test_fl_gate_catches_fictional_fsm_without_explicit_waiver(tmp_path: Path) -> None:
    """ROOT FIX: a combinational contract (no clocked vocabulary) carrying a
    fictional FSM is caught deterministically even with NO cycle_model_waiver
    flag — the waiver is derived from the locked decision table, not an optional
    field (the mux4_v1 class). Closes OBL_TRUTH_COMBINATIONAL_WAIVER_AUTOSET."""
    _write_ip(
        tmp_path, "comb_noflag_fl", cycle_model_waiver=False,  # flag absent
        fsm={"states": ["IDLE", "EXEC"]},
        state_variables=[{"name": "phase", "width": 2}],
    )
    report = validate_fl_semantics("comb_noflag_fl", tmp_path, use_llm=False)
    assert report["passed"] is False
    assert any(v["kind"] == "fictional_state"
               for v in report["deterministic_backstop"]["violations"])


def test_fl_gate_inactive_without_contract_authority(tmp_path: Path) -> None:
    ip_dir = tmp_path / "bare_fl"
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / "bare_fl.ssot.yaml").write_text(
        "ip: bare_fl\ntop_module: {name: bare_fl}\nfsm: {states: [A, B]}\n",
        encoding="utf-8",
    )
    report = validate_fl_semantics("bare_fl", tmp_path, use_llm=False)
    assert report["status"] == "inactive"
    assert report["passed"] is True


def test_fl_gate_llm_unavailable_records_not_run(tmp_path: Path, monkeypatch) -> None:
    """LLM unavailable → explicit not_run; deterministic layer still gates."""
    import validate_fl_semantics as mod

    monkeypatch.setattr(mod, "_default_provider", lambda: (None, "gpt-5.4"))
    _write_ip(
        tmp_path, "comb_fl3", cycle_model_waiver=True,
        fsm={"states": ["IDLE", "EXEC"]},
        state_variables=[{"name": "phase", "width": 2}],
    )
    report = validate_fl_semantics("comb_fl3", tmp_path, use_llm=True)
    assert report["llm_judge"]["status"] == "not_run"
    assert report["llm_judge"]["ran"] is False
    assert report["passed"] is False


if __name__ == "__main__":
    raise SystemExit(pytest.main([__file__, "-q"]))
