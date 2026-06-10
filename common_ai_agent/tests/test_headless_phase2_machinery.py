"""Pinned tests for the phase-2 headless machinery fixes (2026-06-10).

Four general fixes landed while walking pulse_counter_hx through the headless
pipeline (doc/wiki/headless-stage-validation-phase2-20260610.md). Each was
verified by IP-level regression (pc1 31/31 + hx 57/57); these pins protect the
behaviors at unit level so a future edit cannot silently revert them:

1. headless_workflow._copy_requirement must not clobber a requirements_locked
   approval manifest (the lock gate's authority file).
2. derive_rtl_todos: locked_truth_contract_implementation must not be
   draft-blocking (fresh-IP deadlock) but must stay PASS-blocking.
3. derive_rtl_todos._assign_chain_links: connection contracts accept
   continuous-assign chains, reject unrelated nets, bounded depth.
4. emit_goal_scoreboard_cocotb machine-spec runner: FL stimulus mirrors only
   written DATA + EVENT assign values (never op/addr — kind resolution must
   stay pinned to the donor), and the idle park honors timeline-final assigns.
"""
from __future__ import annotations

import importlib.util
import json
from pathlib import Path

from src.headless_workflow import FakeLLMProvider, HeadlessWorkflowRunner

REPO = Path(__file__).resolve().parents[1]


def _load_module(rel: str, name: str):
    path = REPO / rel
    spec = importlib.util.spec_from_file_location(name, path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _req_md(tmp_path: Path) -> Path:
    req = tmp_path / "req.md"
    req.write_text("# Requirement\n\n" + ("A counter counts pulses. " * 40), encoding="utf-8")
    return req


# ---------------------------------------------------------------------------
# 1. locked manifest preservation
# ---------------------------------------------------------------------------

def test_copy_requirement_preserves_locked_manifest(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work", model="fake", llm_provider=FakeLLMProvider()
    )
    ip = "pc_test"
    req_dir = runner._ip_dir(ip) / "req"
    req_dir.mkdir(parents=True)
    locked = {
        "type": "locked_truth_approval_manifest",
        "status": "requirements_locked",
        "approved_by": "brian",
        "files": ["req/obligations.json"],
        "requirements": [{"requirement_id": "REQ_X", "status": "locked"}],
    }
    manifest = req_dir / "approval_manifest.json"
    manifest.write_text(json.dumps(locked), encoding="utf-8")

    runner._copy_requirement(ip, _req_md(tmp_path))

    survived = json.loads(manifest.read_text(encoding="utf-8"))
    assert survived["status"] == "requirements_locked", (
        "the lock_requirement_set manifest is the contract authority gate's "
        "input; the headless copy stage must never overwrite it"
    )
    assert survived == locked
    side = json.loads((req_dir / "headless_req_copy_manifest.json").read_text(encoding="utf-8"))
    assert side["type"] == "requirement_approval_manifest"


def test_copy_requirement_writes_manifest_when_not_locked(tmp_path: Path):
    runner = HeadlessWorkflowRunner(
        root=tmp_path / "work", model="fake", llm_provider=FakeLLMProvider()
    )
    ip = "pc_test"
    runner._copy_requirement(ip, _req_md(tmp_path))
    manifest = json.loads(
        (runner._ip_dir(ip) / "req" / "approval_manifest.json").read_text(encoding="utf-8")
    )
    assert manifest["type"] == "requirement_approval_manifest"


# ---------------------------------------------------------------------------
# 2. draft policy: contract implementation must not deadlock fresh IPs
# ---------------------------------------------------------------------------

def test_contract_implementation_gate_is_not_draft_blocking():
    derive = _load_module("workflow/rtl-gen/scripts/derive_rtl_todos.py", "derive_p2")
    assert "locked_truth_contract_implementation" not in derive._DRAFT_BLOCKING_GATE_KINDS, (
        "this gate is closable only BY authoring RTL; making it draft-blocking "
        "deadlocks every fresh IP that carries a locked req bundle"
    )
    # It must still forbid rtl-gen PASS/signoff.
    assert "locked_truth_contract_implementation" in derive._LOCKED_TRUTH_GATE_KINDS
    # SSOT-side defects that RTL authoring cannot fix stay draft-blocking.
    assert {
        "ssot_required_sections",
        "ssot_workflow_todo_format",
        "owner_traceability",
    } <= derive._DRAFT_BLOCKING_GATE_KINDS


# ---------------------------------------------------------------------------
# 3. connection contracts: continuous-assign chains
# ---------------------------------------------------------------------------

def test_assign_chain_links_follows_continuous_assigns():
    derive = _load_module("workflow/rtl-gen/scripts/derive_rtl_todos.py", "derive_p2b")
    body = """
    assign irq_one_cycle = irq_q;
    assign irq = irq_one_cycle;
    """
    assert derive._assign_chain_links(body, {"irq"}, {"irq_q"}) is True
    # Reverse direction (input-side aliasing) also counts.
    assert derive._assign_chain_links(body, {"irq_q"}, {"irq"}) is True
    # An unrelated net never reaches the expected term.
    assert derive._assign_chain_links(body, {"irq"}, {"some_other_net"}) is False
    # Depth is bounded: a 3-hop chain is rejected at max_depth=2.
    deep = """
    assign a = b;
    assign b = c;
    assign c = d;
    """
    assert derive._assign_chain_links(deep, {"a"}, {"d"}, max_depth=2) is False
    assert derive._assign_chain_links(deep, {"a"}, {"d"}, max_depth=3) is True


# ---------------------------------------------------------------------------
# 4. machine-spec runner template invariants
# ---------------------------------------------------------------------------

def _template_text() -> str:
    return (REPO / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py").read_text(
        encoding="utf-8"
    )


def test_machine_spec_mirrors_written_data_but_never_op_addr():
    text = _template_text()
    # DATA from the timeline's LAST csr_write reaches the FL stimulus, even
    # when a csr_read follows it (read-back sampling is mandated by the
    # authoring rules; hx2 regression: write data=3 was hidden from FL by a
    # trailing read and FL applied index-derived 14)...
    assert "_last_write = _step[\"csr_write\"]" in text
    assert 'stimulus[_k] = _adata' in text
    # ...but op/addr must NOT be mirrored: the FL resolves its transaction
    # kind from the stimulus, and a trailing csr_read re-resolved goals into
    # READ transactions (pc1 EQ_TIMING_ORDERING 31/31 -> 29/31 regression).
    assert 'stimulus["op"] = _op' not in text
    assert 'stimulus[_k] = _aoff' not in text


def test_machine_spec_mirrors_event_value_not_resting_value():
    text = _template_text()
    # A pulse timeline assigns 1 then parks 0; FL's edge condition needs the
    # 1 (event), while the park needs the 0 (resting). Both maps must exist
    # and the FL mirror must prefer the event value.
    assert "_event_assigns" in text
    assert "_ev = _event_assigns.get(_f, _v)" in text


def test_machine_spec_park_honors_timeline_final_assigns():
    text = _template_text()
    # The post-spec idle park must keep explicitly assigned level-holds
    # (e.g. pulse_in=1) instead of forcing idle, or synchronizer-state goals
    # fail by construction.
    assert "_field in _final_assigns or str(_port) in _final_assigns" in text
