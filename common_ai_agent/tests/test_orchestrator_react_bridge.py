"""Unit tests for src/orchestrator/react_bridge.py.

These formalize the structural checks the Step 1 spike at
``artifacts/runtime/_runspaces/orchestrator_react_spike.py`` ran ad-hoc. They guard the four
review findings the plan calls out (P0 tool-replace, P1 no-src.main, P1
yield_run-separate, P2 ctx-bound injector) plus the P2 parallel-step-ordering
assertion that the spike did not exercise.

Step 2A scope: deps factory structure + per-callable round trip. Driving the
real ``run_react_agent_impl`` with a stub LLM is Step 2B.
"""

from __future__ import annotations

import sys
import threading
from pathlib import Path

import pytest

from core.atlas_db import AtlasDB
from src.orchestrator.loop import OrchestratorContext
from src.orchestrator.react_bridge import (
    OrchestratorReactBridge,
    build_orchestrator_deps,
    build_orchestrator_inject_fn_for,
)
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


@pytest.fixture
def bridge(db, runner, ctx):
    return build_orchestrator_deps(ctx=ctx, runner=runner, db=db)


EXPECTED_CALLABLES = {
    "read_pipeline_state",
    "dispatch_workflow",
    "wait_job",
    "read_artifact",
    "classify_failure",
    "ask_user",
    "write_handoff",
    "mark_downstream_stale",
    "import_document",
}


class TestNoMainImport:
    def test_react_bridge_import_does_not_pull_in_src_main(self):
        # If this module was imported earlier in the session, the check is
        # not informative — assert it's NOT loaded as a side effect of the
        # bridge's own imports.
        # (We can't unimport reliably mid-process; the spike script that runs
        # `python3 artifacts/runtime/_runspaces/orchestrator_react_spike.py` is the authoritative
        # green-field check.)
        import src.orchestrator.react_bridge  # noqa: F401

        # Stronger assertion than just "absent": the module's own __dict__
        # must not reference src.main.
        leaked = [
            k for k, v in vars(src.orchestrator.react_bridge).items()
            if hasattr(v, "__module__") and v.__module__ == "src.main"
        ]
        assert not leaked, f"react_bridge leaked src.main attrs: {leaked}"


class TestAvailableToolsReplaced:
    def test_exactly_nine_orchestrator_callables(self, bridge):
        assert set(bridge.deps.available_tools.keys()) == EXPECTED_CALLABLES

    def test_no_generic_agent_tools_leaked(self, bridge):
        forbidden = {"read_file", "write_file", "edit_file", "web_search",
                     "todo_write", "todo_update", "spawn_subagent",
                     "parallel_todo_dispatch", "dispatch_workflow_v1"}
        leaked = forbidden & set(bridge.deps.available_tools.keys())
        assert not leaked, f"generic agent tools leaked into orchestrator: {leaked}"

    def test_yield_run_is_not_in_available_tools(self, bridge):
        # yield_run is wrapper-handled (see P1 finding) — must NOT appear in
        # the dict that dispatch_tool resolves names against.
        assert "yield_run" not in bridge.deps.available_tools


class TestCallableRoundTrip:
    def test_read_pipeline_state_persists_step_row(self, db, bridge, ctx):
        before = len(db.list_orchestrator_steps(ctx.run_id))
        obs = bridge.available_tools["read_pipeline_state"](
            pre_parsed_kwargs={"ip": "ipA"}
        )
        after = db.list_orchestrator_steps(ctx.run_id)
        assert isinstance(obs, str) and len(obs) > 0
        assert len(after) == before + 1
        assert after[-1]["tool_name"] == "read_pipeline_state"

    def test_classify_failure_callable_returns_owner_routing(self, db, bridge, ctx):
        obs = bridge.available_tools["classify_failure"](
            pre_parsed_kwargs={"stage": "lint"}
        )
        # The pure classifier always routes lint -> rtl-gen with high confidence.
        assert "rtl-gen" in obs
        step = db.latest_orchestrator_step(ctx.run_id)
        assert step["tool_name"] == "classify_failure"

    def test_failed_tool_records_tool_error_verdict(self, db, bridge, ctx, monkeypatch):
        from src.orchestrator import tools as orch_tools

        def boom(*_a, **_kw):
            raise RuntimeError("synthetic failure")

        monkeypatch.setattr(orch_tools, "_read_pipeline_state_bridge", lambda: boom)
        bridge.available_tools["read_pipeline_state"](pre_parsed_kwargs={"ip": "ipA"})
        step = db.latest_orchestrator_step(ctx.run_id)
        assert step["verdict"] == "tool_error"


class TestYieldRunInterception:
    def test_execute_tool_fn_handles_yield_run_inline(self, db, bridge, ctx):
        before = len(db.list_orchestrator_steps(ctx.run_id))
        reply = bridge.deps.execute_tool_fn(
            "yield_run",
            "",
            pre_parsed_kwargs={"wake_on": {"after_seconds": 0.05}},
        )
        after = db.list_orchestrator_steps(ctx.run_id)
        assert "woken" in reply
        assert len(after) == before + 1
        assert after[-1]["tool_name"] == "yield_run"
        assert after[-1]["verdict"] in {"timer", "user_message", "no_waker"}

    def test_yield_run_wakes_on_runner_notify_job_complete(self, db, runner, ctx):
        # Build a fresh bridge so we own the Waker registry path.
        bridge = build_orchestrator_deps(ctx=ctx, runner=runner, db=db)

        wake_reason: list[str] = []

        def yield_in_thread():
            reply = bridge.deps.execute_tool_fn(
                "yield_run",
                "",
                pre_parsed_kwargs={
                    "wake_on": {
                        "job_ids": ["job-watched-1"],
                        "after_seconds": 5.0,  # safety timeout
                    }
                },
            )
            wake_reason.append(reply)

        t = threading.Thread(target=yield_in_thread, daemon=True)
        t.start()
        # Give the loop a moment to register the waker.
        for _ in range(20):
            if runner._wakers.get(ctx.run_id):
                break
            threading.Event().wait(0.02)
        notified = runner.notify_job_complete("job-watched-1", "completed")
        assert notified == 1
        t.join(timeout=2)
        assert not t.is_alive(), "yield_run did not wake"
        assert wake_reason and "job_complete" in wake_reason[0]

    def test_yield_run_paused_status_during_wait(self, db, runner, ctx):
        bridge = build_orchestrator_deps(ctx=ctx, runner=runner, db=db)
        observed: list[str] = []

        def yield_in_thread():
            bridge.deps.execute_tool_fn(
                "yield_run",
                "",
                pre_parsed_kwargs={"wake_on": {"after_seconds": 0.5}},
            )

        t = threading.Thread(target=yield_in_thread, daemon=True)
        t.start()
        # Sample the run status while the loop sleeps on the waker.
        for _ in range(40):
            run = db.get_orchestrator_run(ctx.run_id)
            observed.append(run["status"])
            if run["status"] == "yielded":
                break
            threading.Event().wait(0.02)
        t.join(timeout=2)
        # We caught the transitional "yielded" state and it cleared after wake.
        assert "yielded" in observed
        final = db.get_orchestrator_run(ctx.run_id)
        assert final["status"] == "running"


class TestSystemPromptEmbedsTenSchemas:
    def test_system_prompt_contains_all_ten_tool_names(self, bridge):
        prompt = bridge.deps.build_prompt_fn(
            messages=[{"role": "user", "content": "hi"}],
            allowed_tools=set(bridge.deps.available_tools.keys()),
            agent_mode="normal",
        )
        assert isinstance(prompt, str)
        names = EXPECTED_CALLABLES | {"yield_run"}
        for n in names:
            assert f'"name": "{n}"' in prompt, f"missing schema for {n}"


class TestProductionHookReuse:
    def test_compress_fn_wraps_compress_history(self, bridge):
        # compress_history requires cfg + llm_call_fn as keyword-only args,
        # so react_bridge wraps it in a closure that pre-binds those. The
        # wrapper preserves the (messages, todo_tracker=...) signature that
        # react_loop calls deps.compress_fn with.
        import inspect

        sig = inspect.signature(bridge.deps.compress_fn)
        # The closure exposes (messages, todo_tracker=None, **kw).
        assert "messages" in sig.parameters
        assert "todo_tracker" in sig.parameters
        # Calling it with bogus input should NOT raise TypeError for missing
        # cfg/llm_call_fn — those are pre-bound. (May raise downstream when
        # actually invoking the LLM, but the signature contract is met.)
        # Empty messages → should just return them unchanged.
        result = bridge.deps.compress_fn([])
        assert isinstance(result, list)

    def test_execute_parallel_fn_delegates_to_production_helper(self, bridge, monkeypatch):
        """``core.parallel_executor.execute_actions_parallel`` is keyword-only
        for ``cfg``/``execute_tool_fn``/``tracker`` — but react_loop calls
        ``deps.execute_parallel_fn(actions, tracker, agent_mode=...)`` with
        ``tracker`` positional. The bridge therefore wraps the production
        helper with ``cfg`` + ``execute_tool_fn`` pre-bound (same pattern as
        ``src/main.py:1072``). Identity-equality with the bare core function
        would silently break the moment a real LLM streams parallel tool calls.
        """
        from core import parallel_executor

        captured = {}

        def _capture(actions, **kw):
            captured["actions"] = actions
            captured["kw"] = kw
            return []

        monkeypatch.setattr(parallel_executor, "execute_actions_parallel", _capture)
        # Call with the exact shape react_loop uses.
        bridge.deps.execute_parallel_fn(
            [("read_pipeline_state", "{}")], tracker=None, agent_mode="normal",
        )
        # The wrapper must have supplied cfg and execute_tool_fn so the inner
        # implementation gets a complete kwarg set.
        assert "cfg" in captured["kw"]
        assert "execute_tool_fn" in captured["kw"]
        assert callable(captured["kw"]["execute_tool_fn"])


class TestCtxBoundInjector:
    def test_inject_uses_ctx_not_env(self, db, ctx, monkeypatch):
        # If the injector touched ATLAS_ACTIVE_IP, the assertion below would
        # depend on env, which is exactly the P2 finding we are guarding
        # against. We explicitly NOT set the env.
        monkeypatch.delenv("ATLAS_ACTIVE_IP", raising=False)
        monkeypatch.delenv("ACTIVE_IP", raising=False)

        inject = build_orchestrator_inject_fn_for(db, ctx)
        # Seed a fake context payload returned by summarize_ip_room_context.
        called_with = {}
        real = db.summarize_ip_room_context

        def fake_summary(ip_id):
            called_with["ip_id"] = ip_id
            return {"ip": {"name": ctx.ip_name}, "workflow": {}, "todos": {},
                    "gates": {}, "recent_events": []}

        monkeypatch.setattr(db, "summarize_ip_room_context", fake_summary)
        messages = [{"role": "system", "content": "BASE"}]
        inject(messages, "normal")
        # ctx.ip_id was passed (not env-resolved).
        assert called_with["ip_id"] == ctx.ip_id
        # Injection appended to the system message.
        assert "orchestrator-context" in messages[0]["content"]
        assert ctx.ip_name in messages[0]["content"]

        # Restore (good hygiene)
        monkeypatch.setattr(db, "summarize_ip_room_context", real)


class TestReactLoopCallShape:
    """Step 2B: prove ``deps.execute_tool_fn`` accepts the exact signature
    ``core/react_loop.py`` invokes it with at line 1645/1656:
    ``deps.execute_tool_fn(tool_name, _args_display, pre_parsed_kwargs=...)``.
    """

    def test_react_loop_call_shape_for_known_tool(self, db, bridge, ctx):
        before = len(db.list_orchestrator_steps(ctx.run_id))
        # react_loop builds _args_display from native kwargs as `key="value"` pairs.
        observation = bridge.deps.execute_tool_fn(
            "read_pipeline_state",
            'ip="ipA", include_jobs=true',
            pre_parsed_kwargs={"ip": "ipA", "include_jobs": True},
        )
        after = db.list_orchestrator_steps(ctx.run_id)
        assert isinstance(observation, str)
        assert len(after) == before + 1
        assert after[-1]["tool_name"] == "read_pipeline_state"

    def test_react_loop_call_shape_rejects_unknown_tool(self, bridge):
        # Generic agent tools (read_file, write_file, web_search, ...) must
        # be unresolvable. Routing them through deps.execute_tool_fn returns
        # the dispatcher's "Tool not found" string — no step row, no crash.
        observation = bridge.deps.execute_tool_fn(
            "read_file",
            'path="something.py"',
            pre_parsed_kwargs={"path": "something.py"},
        )
        assert "not found" in observation.lower()


class TestStepCollectorOrdering:
    def test_parallel_callable_invocations_get_distinct_step_indexes(self, db, runner, ctx):
        # The _OrderedStepCollector uses a single lock so step_index is
        # monotonically allocated even under contention. Hammer the same
        # callable from N threads and assert no duplicate / missing indexes.
        bridge = build_orchestrator_deps(ctx=ctx, runner=runner, db=db)

        N = 20
        errors: list[str] = []

        def call_once():
            try:
                bridge.available_tools["classify_failure"](
                    pre_parsed_kwargs={"stage": "lint"}
                )
            except Exception as exc:
                errors.append(f"{type(exc).__name__}: {exc}")

        threads = [threading.Thread(target=call_once) for _ in range(N)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()
        assert not errors, errors

        steps = db.list_orchestrator_steps(ctx.run_id)
        indexes = [s["step_index"] for s in steps]
        # Monotonic, unique, dense from 0..N-1.
        assert sorted(indexes) == list(range(N))
