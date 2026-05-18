import pytest

from core.atlas_db import AtlasDB
from src.orchestrator import tools as orch_tools
from src.orchestrator.loop import OrchestratorContext, OrchestratorLoop


@pytest.fixture
def db(tmp_path):
    atlas = AtlasDB(str(tmp_path / "atlas.db"))
    atlas.init_db()
    yield atlas
    atlas.close()


@pytest.fixture
def ctx(db):
    run = db.create_orchestrator_run(
        user_id="u1", ip_id="ip1", session_id="s1"
    )
    return OrchestratorContext(
        run_id=run["id"],
        user_id="u1",
        ip_id="ip1",
        ip_name="ipA",
        session_id="s1",
    )


def _scripted_caller(script):
    """Return an LLM caller that yields one scripted response per call."""
    iterator = iter(script)

    def caller(messages, tools):
        try:
            return next(iterator)
        except StopIteration:
            return {"content": "no more scripted responses"}

    return caller


def _tool_call(name, **args):
    return {"tool_calls": [{"name": name, "arguments": args}]}


class TestIteratePersistsSteps:
    def test_read_pipeline_state_step_persisted(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools,
            "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": ["ssot"], "failed": []},
        )
        caller = _scripted_caller([_tool_call("read_pipeline_state", ip="ipA")])
        loop = OrchestratorLoop(db, ctx, llm_caller=caller)
        step = loop.iterate()
        assert step.tool_name == "read_pipeline_state"
        assert step.verdict == "ok"
        steps = db.list_orchestrator_steps(ctx.run_id)
        assert len(steps) == 1
        assert steps[0]["tool_name"] == "read_pipeline_state"
        assert steps[0]["evidence_read_json"]["result"]["passed"] == ["ssot"]

    def test_dispatch_workflow_records_job_id(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools,
            "_dispatch_workflow_bridge",
            lambda: lambda **kw: {
                "ok": True,
                "pipeline_run_id": "pr1",
                "jobs": [{"job_id": "job-42"}],
            },
        )
        caller = _scripted_caller(
            [_tool_call("dispatch_workflow", workflow="rtl-gen", ip="ipA")]
        )
        loop = OrchestratorLoop(db, ctx, llm_caller=caller)
        loop.iterate()
        step = db.list_orchestrator_steps(ctx.run_id)[0]
        assert step["dispatched_workflow"] == "rtl-gen"
        assert step["dispatched_job_id"] == "job-42"


class TestRunTermination:
    def test_final_workflow_marks_run_completed(self, db, ctx):
        caller = _scripted_caller(
            [
                _tool_call(
                    "dispatch_workflow",
                    workflow="__final__",
                    payload={"state": "completed", "reason": "all green"},
                )
            ]
        )
        loop = OrchestratorLoop(db, ctx, llm_caller=caller)
        outcome = loop.run()
        assert outcome.status == "completed"
        assert outcome.final_state == "completed"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "completed"
        assert run["ended_at"] is not None

    def test_blocked_final_state(self, db, ctx):
        caller = _scripted_caller(
            [
                _tool_call(
                    "dispatch_workflow",
                    workflow="__final__",
                    payload={"state": "blocked", "reason": "budget exhausted"},
                )
            ]
        )
        outcome = OrchestratorLoop(db, ctx, llm_caller=caller).run()
        assert outcome.status == "blocked"
        assert outcome.final_state == "blocked"

    def test_ask_user_pauses_run(self, db, ctx):
        caller = _scripted_caller(
            [_tool_call("ask_user", question="pick FIFO depth")]
        )
        outcome = OrchestratorLoop(db, ctx, llm_caller=caller).run()
        assert outcome.status == "paused"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "paused"
        # paused runs do not get ended_at set
        assert run["ended_at"] is None

    def test_hard_cap_on_steps(self, db, ctx, monkeypatch):
        monkeypatch.setattr(
            orch_tools,
            "_read_pipeline_state_bridge",
            lambda: lambda **kw: {"ok": True, "passed": [], "failed": []},
        )
        # Endless read_pipeline_state responses
        caller = _scripted_caller(
            [_tool_call("read_pipeline_state", ip="ipA")] * 200
        )
        outcome = OrchestratorLoop(db, ctx, llm_caller=caller).run(max_steps=3)
        assert outcome.status == "blocked"
        assert outcome.final_state == "cap_exceeded"
        assert outcome.steps_taken == 3
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["final_state"] == "cap_exceeded"

    def test_llm_exception_marks_run_error(self, db, ctx):
        def boom(messages, tools):
            raise RuntimeError("rate limit")

        outcome = OrchestratorLoop(db, ctx, llm_caller=boom).run(max_steps=5)
        assert outcome.status == "error"
        assert outcome.final_state == "llm_error"
        run = db.get_orchestrator_run(ctx.run_id)
        assert run["status"] == "error"
        assert run["final_state"] == "llm_error"


class TestToolErrorContinuesLoop:
    def test_tool_error_is_recorded_and_loop_continues(self, db, ctx, monkeypatch):
        # First call raises inside the tool; second call finalizes.
        def faulty_bridge():
            def _impl(**kw):
                raise ValueError("boom")
            return _impl

        monkeypatch.setattr(orch_tools, "_read_pipeline_state_bridge", faulty_bridge)
        caller = _scripted_caller(
            [
                _tool_call("read_pipeline_state", ip="ipA"),
                _tool_call(
                    "dispatch_workflow",
                    workflow="__final__",
                    payload={"state": "completed"},
                ),
            ]
        )
        outcome = OrchestratorLoop(db, ctx, llm_caller=caller).run()
        assert outcome.steps_taken == 2
        steps = db.list_orchestrator_steps(ctx.run_id)
        assert steps[0]["verdict"] == "tool_error"
        assert steps[1]["verdict"] == "completed"
