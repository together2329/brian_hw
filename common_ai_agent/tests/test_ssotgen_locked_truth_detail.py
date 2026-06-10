"""ssot-gen must inject the locked truth's behavioral DETAIL, not just IDs.

2026-06-11 campaign finding 10: for a fresh IP with a human-locked req bundle,
ssot-gen authored a semantically vacuous SSOT (function_model.transactions named
feature_1/feature_2, fsm empty) because `_locked_truth_projection_brief` injected
only the contract IDs + generic projection rules — never the actual decision
tables. In headless mode the worker cannot self-read req/ (tool use blocked), so
the LLM had no idea what each behavioral contract specified and could not author
real function_model semantics.

Design decision (user): the Function Model is LLM-authored; the locked truth
provides the GUIDELINES. So the brief must carry the behavioral contract bodies
(decision tables) + requirement/obligation statements to author from.
"""
from __future__ import annotations

import json
from pathlib import Path

import pytest

from src.headless_workflow import HeadlessWorkflowRunner


def _lock(req_dir: Path) -> None:
    req_dir.mkdir(parents=True, exist_ok=True)
    (req_dir / "approval_manifest.json").write_text(
        json.dumps({"status": "requirements_locked"}), encoding="utf-8")
    (req_dir / "requirements_index.json").write_text(json.dumps({
        "requirements": [{
            "requirement_id": "REQ_CNT8_COUNT_001",
            "title": "8-bit enabled up-counter",
            "statement": "count increments by 1 each enabled cycle; clr clears; wraps 255->0.",
            "obligation_refs": ["OBL_CNT8_COUNT_001"],
        }]
    }), encoding="utf-8")
    (req_dir / "obligations.json").write_text(json.dumps({
        "obligations": [{
            "obligation_id": "OBL_CNT8_COUNT_001",
            "statement": "Counter increments exactly +1 per enabled cycle and wraps 255->0.",
        }]
    }), encoding="utf-8")
    (req_dir / "behavioral_contracts.json").write_text(json.dumps({
        "contracts": [{
            "id": "BC-CNT8-COUNT",
            "obligations": ["OBL_CNT8_COUNT_001"],
            "decision_table": [
                {"when": "en==1 && clr==0 at rising clk", "then": "count+=1; 255 wraps to 0"},
                {"when": "en==0 && clr==0", "then": "count holds"},
            ],
        }]
    }), encoding="utf-8")
    (req_dir / "structural_contracts.json").write_text(json.dumps({
        "contracts": [{"id": "SC_CNT8_PORTS", "signals": [{"name": "clk", "dir": "input"}]}]
    }), encoding="utf-8")


@pytest.fixture
def runner(tmp_path):
    return HeadlessWorkflowRunner(root=tmp_path, llm_provider=object())


def test_brief_includes_behavioral_decision_table(runner, tmp_path):
    _lock(tmp_path / "cnt8_en_v1" / "req")
    brief = runner._locked_truth_projection_brief("cnt8_en_v1")
    # IDs still present (the projection contract).
    assert "BC-CNT8-COUNT" in brief
    # NEW: the actual decision-table content reaches the LLM.
    assert "LOCKED TRUTH DETAIL" in brief
    assert "en==1 && clr==0" in brief
    assert "255 wraps to 0" in brief
    assert "count holds" in brief
    # Requirement + obligation statements too.
    assert "increments by 1 each enabled cycle" in brief
    assert "wraps 255->0" in brief
    # An explicit instruction to author (not placeholder).
    assert "feature_N" in brief  # the "never leave feature_N placeholders" instruction


def test_brief_empty_when_not_locked(runner, tmp_path):
    req = tmp_path / "x" / "req"
    req.mkdir(parents=True)
    (req / "approval_manifest.json").write_text(json.dumps({"status": "draft"}), encoding="utf-8")
    assert runner._locked_truth_projection_brief("x") == ""


def test_brief_empty_when_no_manifest(runner, tmp_path):
    (tmp_path / "y" / "req").mkdir(parents=True)
    assert runner._locked_truth_projection_brief("y") == ""
