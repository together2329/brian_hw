"""Parity tests — legacy ``OrchestratorLoop`` semantics on ``OrchestratorReactLoop``.

Step 6 of `[[orchestrator-loop-on-react-loop-plan]]` is "delete the legacy
``OrchestratorLoop`` scaffold". Before deletion we need ``OrchestratorReactLoop``
to honour the same terminal-state contracts the legacy 11 ``test_orchestrator_loop.py``
cases asserted:

- ``__final__`` with ``payload.state="blocked"`` → run status ``"blocked"``,
  ``final_state="blocked"``, ``ended_at`` set.
- ``__final__`` with ``payload.state="completed"`` → run status ``"completed"``,
  ``ended_at`` set.
- ``ask_user`` → run status ``"paused"``, ``final_state="paused"``,
  ``ended_at`` left NULL (paused ≠ ended).
- Hard cap (max_steps=3 + endless tool calls) → ``"blocked"`` / ``"cap_exceeded"``.
- LLM exception → ``"error"`` / ``"llm_error"``.
- Tool exception inside the wrapper → step ``verdict="tool_error"``, loop continues.
- Parallel tool calls in one LLM response → all execute, each persists a step row.

Hard-cap and LLM-exception cases are already covered by
``tests/test_orchestrator_react_loop.py``; we don't re-test them here, only the
gaps the existing suite didn't cover.
"""

from __future__ import annotations

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator import tools as orch_tools
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import OrchestratorReactLoop
from src.orchestrator.runner import OrchestratorRunner


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


@pytest.fixture
def runner(db):
    r = OrchestratorRunner(db, max_workers=1)
    yield r
    r.shutdown(wait=True)


@pytest.fixture
def ctx(db, runner, tmp_path):
    run = db.create_orchestrator_run(user_id="u1", ip_id="ip1", session_id="s1")
    return OrchestratorContext(
        run_id=run["id"],
        user_id="u1",
        ip_id="ip1",
        ip_name="ipA",
        session_id="s1",
        project_root=tmp_path,
        runner=runner,
    )


def _scripted(*responses):
    iterator = iter(responses)

    def caller(messages, tools):
        try:
            return next(iterator)
        except StopIteration:
            return {"content": "no more"}

    return caller


def _tool_call(name, **args):
    return {"tool_calls": [{"id": "call_x", "name": name, "arguments": args}]}


class TestFinalWorkflowTermination:
    def test_final_completed_marks_run_completed(self, db, ctx):
        caller = _scripted(
            _tool_call(
                "dispatch_workflow",
                workflow="__final__",
                payload={"state": "completed", "reason": "all green"},
            ),
            {"content": "done"},
        )
        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)
        assert outcome.status == "completed"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "completed"
        assert run["ended_at"] is not None

    def test_final_blocked_preserves_blocked_state(self, db, ctx):
        """The legacy loop honoured ``payload.state="blocked"`` as the
        terminal state. The react_loop migration must too — otherwise budget
        exhaustion / human escalation final calls all collapse to
        ``"completed"``, hiding the failure."""
        caller = _scripted(
            _tool_call(
                "dispatch_workflow",
                workflow="__final__",
                payload={"state": "blocked", "reason": "budget exhausted"},
            ),
            {"content": "stopping"},
        )
        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)
        assert outcome.status == "blocked"
        assert outcome.final_state == "blocked"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "blocked"
        assert run["final_state"] == "blocked"
        assert run["ended_at"] is not None


class TestAskUserPause:
    def test_ask_user_pauses_run_without_ending(self, db, ctx):
        """``ask_user`` puts the run in ``status="paused"``. ``ended_at`` must
        stay NULL — a paused run is not ended; the runner appends the user's
        reply as a step and resumes."""
        caller = _scripted(
            _tool_call("ask_user", question="pick FIFO depth"),
            {"content": "waiting"},
        )
        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)
        assert outcome.status == "paused"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "paused"
        # Paused runs leave ended_at unset so the runner knows to resume them.
        assert run["ended_at"] is None


class TestToolErrorContinuesLoop:
    def test_tool_error_recorded_loop_continues_to_final(self, db, ctx, monkeypatch):
        """A tool raising mid-iteration must not abort the run — the wrapper
        records ``verdict="tool_error"`` and the LLM gets a chance to recover
        or finalize on the next turn."""

        def faulty_bridge():
            def _impl(**kw):
                raise ValueError("boom")
            return _impl

        monkeypatch.setattr(orch_tools, "_read_pipeline_state_bridge", faulty_bridge)
        caller = _scripted(
            _tool_call("read_pipeline_state", ip="ipA"),
            _tool_call(
                "dispatch_workflow",
                workflow="__final__",
                payload={"state": "completed"},
            ),
            {"content": "done"},
        )
        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)
        assert outcome.status == "completed"
        steps = db.list_orchestrator_steps(ctx.run_id)
        verdicts = [s["verdict"] for s in steps]
        assert "tool_error" in verdicts


class TestParallelToolCalls:
    def test_multiple_tool_calls_all_persist_steps(self, db, ctx, monkeypatch):
        """Native parallel tool_calls in one LLM response: every tool gets a
        step row. Step ordering is enforced by ``_OrderedStepCollector`` so the
        recorded ``step_index`` reflects LLM-call order, not completion order."""
        monkeypatch.setattr(
            orch_tools, "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": [], "failed": []},
        )
        dispatched = []

        def fake_dispatch(**kw):
            dispatched.append(kw)
            return {"ok": True, "pipeline_run_id": "pr", "jobs": [{"job_id": "j"}]}

        monkeypatch.setattr(
            orch_tools, "_dispatch_workflow_bridge", lambda: fake_dispatch
        )
        parallel = {
            "tool_calls": [
                {"id": "c1", "name": "read_pipeline_state", "arguments": {"ip": "ipA"}},
                {"id": "c2", "name": "dispatch_workflow", "arguments": {"ip": "ipA", "workflow": "lint"}},
                {"id": "c3", "name": "dispatch_workflow", "arguments": {"ip": "ipA", "workflow": "tb-gen"}},
            ]
        }
        caller = _scripted(parallel, {"content": "done"})
        # max_steps=5 (not 3) so react_loop's iteration counter doesn't trip
        # cap_exceeded — parallel batches count multiple iterations through
        # ``tracker``, and the post-loop natural-completion read must run.
        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)
        assert outcome.status == "completed"
        steps = db.list_orchestrator_steps(ctx.run_id)
        names = [s["tool_name"] for s in steps]
        assert names.count("read_pipeline_state") == 1
        assert names.count("dispatch_workflow") == 2
        # Both dispatches actually invoked the bridge.
        assert len(dispatched) == 2
        assert {d["workflow"] for d in dispatched} == {"lint", "tb-gen"}
