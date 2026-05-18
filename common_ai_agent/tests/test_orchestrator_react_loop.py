"""Phase 3.5 Step 3 — OrchestratorReactLoop integration tests.

Drives ``run_react_agent_impl`` end-to-end via the bridge's translation
layer that converts ``OrchestratorLoop``-style ``llm_caller(messages, tools)
-> dict`` test scripts into the streaming chunk protocol react_loop expects.
"""

from __future__ import annotations

import sys
import types

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
    run = db.create_orchestrator_run(
        user_id="u1", ip_id="ip1", session_id="s1"
    )
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
    return {
        "tool_calls": [
            {"id": "call_x", "name": name, "arguments": args}
        ]
    }


class TestRunCompletes:
    def test_single_tool_call_then_natural_completion(self, db, ctx, monkeypatch):
        # First LLM turn emits one tool call; second turn yields content (no
        # more tool calls) which run_react_agent_impl treats as completion.
        monkeypatch.setattr(
            orch_tools, "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": ["ssot"], "failed": []},
        )
        caller = _scripted(
            _tool_call("read_pipeline_state", ip="ipA"),
            {"content": "all good"},
        )
        loop = OrchestratorReactLoop(db, ctx, llm_caller=caller)
        outcome = loop.run(max_steps=5)
        assert outcome.status == "completed"

        steps = db.list_orchestrator_steps(ctx.run_id)
        # At least one step row from the read_pipeline_state tool call.
        tool_names = [s["tool_name"] for s in steps]
        assert "read_pipeline_state" in tool_names

    def test_text_reply_completes_even_when_outer_todos_exist(
        self, db, ctx, monkeypatch
    ):
        """The UI orchestrator runs inside a larger Codex process that may
        already have unfinished session todos. Those todos must not leak into
        the orchestrator react_loop and force generic tool calls after the
        orchestrator has already produced its final chat reply."""

        import config as cfg  # type: ignore

        class _Todo:
            content = "outer task"
            detail = "not part of the ATLAS orchestrator run"
            criteria = "must not nudge orchestrator"
            status = "pending"

        class _OuterTodoTracker:
            todos = [_Todo()]
            current_index = 0

            def is_all_processed(self):
                return False

            def get_current_todo(self):
                return self.todos[0]

        monkeypatch.setattr(cfg, "ENABLE_TODO_TRACKING", True, raising=False)
        monkeypatch.setattr(cfg, "EXECUTION_NO_ACTION_GUARD", True, raising=False)
        monkeypatch.setitem(
            sys.modules,
            "main",
            types.SimpleNamespace(todo_tracker=_OuterTodoTracker()),
        )
        monkeypatch.setattr(
            orch_tools, "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": ["ssot"], "failed": []},
        )

        calls = {"count": 0}

        def caller(messages, tools):
            calls["count"] += 1
            if calls["count"] == 1:
                return _tool_call("read_pipeline_state", ip="ipA")
            if calls["count"] == 2:
                return {"content": "pipeline state read; no dispatch requested"}
            raise AssertionError("outer todo guard leaked into orchestrator loop")

        outcome = OrchestratorReactLoop(db, ctx, llm_caller=caller).run(max_steps=5)

        assert outcome.status == "completed"
        assert calls["count"] == 2

    def test_llm_caller_exception_marks_run_error(self, db, ctx):
        def boom(messages, tools):
            raise RuntimeError("auth failed")

        loop = OrchestratorReactLoop(db, ctx, llm_caller=boom)
        outcome = loop.run(max_steps=3)
        assert outcome.status == "error"
        assert outcome.final_state == "llm_error"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "error"
        assert run["final_state"] == "llm_error"
