"""Seed propagation: the orchestrator chat message must reach worker prompts.

Bug report (2026-05-19): when a user typed
  "run ssot for cmux_flow_beta. A small async FIFO, 8 entries, 16-bit data,
   push/pop with full/empty flags. Top module name: beta_fifo."
the dispatched ssot-gen worker generated a CMUX (clock mux) instead of a
FIFO because the seed text never landed in the worker prompt — workers only
saw ``[ATLAS ARCHITECT WORKFLOW CONTEXT]`` boilerplate.

These tests pin the propagation contract end-to-end:
  payload.user_seed (set by react_bridge from ctx.user_seed) →
  ``[USER REQUIREMENT]`` section in the worker stage_prompt →
  job["prompt"] (boundary + stage_prompt) visible to the worker.
"""

from __future__ import annotations

import sys
from pathlib import Path
from typing import Any, Dict, Optional


# ----------------------------------------------------------------------
# react_bridge level: ctx.user_seed lands on payload.user_seed.
# ----------------------------------------------------------------------


class _StubBudgetTracker:
    def attempt(self, _workflow: str) -> Dict[str, Any]:
        return {"allowed": True, "workflow": _workflow, "attempts": 1, "budget": 99}

    def reset(self, _workflow: str) -> None:
        return None

    def snapshot(self) -> Dict[str, Any]:
        return {}


class _StubCollector:
    def __init__(self) -> None:
        self.rows: list[Dict[str, Any]] = []

    def append(self, **kw: Any) -> Dict[str, Any]:
        self.rows.append(kw)
        return {}


class _StubCtx:
    def __init__(
        self,
        *,
        ip_name: str = "cmux_flow_beta",
        session_id: str = "",
        user_seed: str = "",
    ) -> None:
        self.run_id = "run-test"
        self.user_id = "u-test"
        self.ip_id = "ip-test"
        self.ip_name = ip_name
        self.session_id = session_id
        self.project_root = Path(".")
        self.runner = None
        self.user_seed = user_seed


def _capture_dispatch_call(monkeypatch, captured: Dict[str, Any]):
    """Replace ``orch_tools.dispatch_workflow`` with a recorder."""
    from src.orchestrator import react_bridge

    def _fake_dispatch_workflow(**kw: Any):
        captured.update(kw)
        return {"ok": True, "pipeline_run_id": "pr-1", "jobs": []}, "ok"

    monkeypatch.setattr(
        react_bridge.orch_tools, "dispatch_workflow", _fake_dispatch_workflow
    )


def test_react_bridge_propagates_user_seed_to_payload(monkeypatch):
    """The bridge MUST copy ``ctx.user_seed`` onto payload.user_seed when the
    LLM dispatches a workflow, regardless of whether the LLM also passes
    ``prompt``. This is the contained fix described in the bug report."""
    from src.orchestrator import react_bridge

    seed = "make a 4-bit gray counter, top=gray_ctr"
    ctx = _StubCtx(ip_name="gray", user_seed=seed)

    captured: Dict[str, Any] = {}
    _capture_dispatch_call(monkeypatch, captured)

    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_StubCollector(),
        budgets=_StubBudgetTracker(),
    )
    dispatch = bound["dispatch_workflow"]

    # Simulate the react_loop tool dispatcher: it passes args via **kw on the
    # wrapped callable (see _wrap in react_bridge).
    dispatch(
        "",
        pre_parsed_kwargs={
            "workflow": "ssot-gen",
            "ip": "gray",
            # LLM does NOT pass `prompt` here — that's the failure mode that
            # caused the cmux_flow_beta bug. The seed must still arrive at the
            # worker via payload.user_seed.
        },
    )

    payload = captured.get("payload") or {}
    assert payload.get("user_seed") == seed, (
        f"react_bridge must inject ctx.user_seed into payload.user_seed; "
        f"got payload={payload!r}"
    )


def test_react_bridge_read_pipeline_state_passes_session_scope(monkeypatch):
    from src.orchestrator import react_bridge

    session_id = "u-test/alt/ipA/orchestrator"
    ctx = _StubCtx(ip_name="ipA", session_id=session_id)
    captured: Dict[str, Any] = {}

    def _fake_read_pipeline_state(**kw: Any):
        captured.update(kw)
        return {"ok": True, "active_jobs": []}, "ok"

    monkeypatch.setattr(
        react_bridge.orch_tools, "read_pipeline_state", _fake_read_pipeline_state
    )
    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_StubCollector(),
        budgets=_StubBudgetTracker(),
    )

    bound["read_pipeline_state"]("", pre_parsed_kwargs={"ip": "ipA"})

    assert captured["ip"] == "ipA"
    assert captured["scope"] == session_id
    assert captured["db_user_id"] == "u-test"
    assert captured["include_jobs"] is True


def test_react_bridge_preserves_caller_supplied_user_seed(monkeypatch):
    """If the caller (or a future LLM revision) already supplied
    ``payload.user_seed`` explicitly, the bridge must not clobber it."""
    from src.orchestrator import react_bridge

    ctx = _StubCtx(user_seed="ctx-level-seed")
    captured: Dict[str, Any] = {}
    _capture_dispatch_call(monkeypatch, captured)

    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx, runner=None, db=None,
        collector=_StubCollector(), budgets=_StubBudgetTracker(),
    )
    dispatch = bound["dispatch_workflow"]

    dispatch(
        "",
        pre_parsed_kwargs={
            "workflow": "ssot-gen",
            "ip": "cmux_flow_beta",
            "payload": {"user_seed": "explicit-caller-seed"},
        },
    )
    assert captured["payload"]["user_seed"] == "explicit-caller-seed"


def test_react_bridge_maps_force_flag_to_dispatch_payload(monkeypatch):
    """When the orchestrator explicitly chooses relaxed progress-over-blocking
    dispatch, the bridge must carry that intent as payload.force=true so the
    existing upstream-red gate's documented escape hatch is actually used."""
    from src.orchestrator import react_bridge

    ctx = _StubCtx(ip_name="apb_timer")
    captured: Dict[str, Any] = {}
    _capture_dispatch_call(monkeypatch, captured)

    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_StubCollector(),
        budgets=_StubBudgetTracker(),
    )

    bound["dispatch_workflow"](
        "",
        pre_parsed_kwargs={
            "workflow": "rtl-gen",
            "ip": "apb_timer",
            "force": True,
            "reason": "Proceed despite red cl-model under relaxed policy.",
        },
    )

    payload = captured.get("payload") or {}
    assert payload["force"] is True
    assert captured["force"] is True


def test_react_bridge_uses_context_user_and_workspace_session_as_authority(monkeypatch):
    from src.orchestrator import react_bridge

    ctx = _StubCtx(ip_name="pl330", user_seed="ctx seed")
    ctx.user_id = "alice-db"
    ctx.session_id = "alice/alt/pl330/orchestrator"
    captured: Dict[str, Any] = {}
    _capture_dispatch_call(monkeypatch, captured)

    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_StubCollector(),
        budgets=_StubBudgetTracker(),
    )
    dispatch = bound["dispatch_workflow"]

    dispatch(
        "",
        pre_parsed_kwargs={
            "workflow": "rtl-gen",
            "ip": "pl330",
            "payload": {
                "db_user_id": "bob-db",
                "orchestrator_session_id": "bob/default/pl330/orchestrator",
                "workspace_session": "default",
            },
        },
    )

    payload = captured.get("payload") or {}
    assert payload["db_user_id"] == "alice-db"
    assert payload["orchestrator_session_id"] == "alice/alt/pl330/orchestrator"
    assert payload["workspace_session"] == "alt"


def test_react_bridge_passes_context_session_to_pipeline_state_reads(monkeypatch):
    from src.orchestrator import react_bridge

    ctx = _StubCtx(ip_name="pl330")
    ctx.session_id = "alice/alt/pl330/orchestrator"
    captured: Dict[str, Any] = {}

    def fake_read_pipeline_state(**kw: Any):
        captured.update(kw)
        return {"ok": True, "active_jobs": []}, "ok"

    monkeypatch.setattr(
        react_bridge.orch_tools,
        "read_pipeline_state",
        fake_read_pipeline_state,
    )

    bound = react_bridge._bind_orchestrator_tools(
        ctx=ctx,
        runner=None,
        db=None,
        collector=_StubCollector(),
        budgets=_StubBudgetTracker(),
    )

    bound["read_pipeline_state"](
        "",
        pre_parsed_kwargs={"ip": "pl330", "include_jobs": True},
    )

    assert captured["scope"] == "alice/alt/pl330/orchestrator"


# ----------------------------------------------------------------------
# atlas_api_jobs level: payload.user_seed → ``[USER REQUIREMENT]`` block
# inside the worker prompt rendered by ``_make_job_record``.
# ----------------------------------------------------------------------


def test_dispatch_workflow_bridge_seed_lands_in_worker_prompt(tmp_path, monkeypatch):
    """End-to-end: payload.user_seed is rendered into the worker stage_prompt
    so the worker (e.g. ssot-gen) sees the user's concrete requirement.

    We invoke ``_dispatch_workflow_tool_bridge`` directly: it is the function
    the orchestrator's dispatch_workflow tool ultimately calls (registered via
    ``set_dispatch_workflow_callback``)."""
    # Sandbox the project root so _make_job_record doesn't touch the real repo.
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "gray")
    monkeypatch.setenv("ATLAS_ACTIVE_USER", "local-admin")

    # Build a minimal FastAPI-like app: register_jobs_routes only needs the
    # decorator surface to install handlers; we extract the dispatch bridge
    # via the side-effect of register_jobs_routes calling
    # set_dispatch_workflow_callback.
    captured_bridge: Dict[str, Any] = {}

    def _capture_setter(callback):
        captured_bridge["fn"] = callback

    from core import tools as core_tools

    monkeypatch.setattr(core_tools, "set_dispatch_workflow_callback", _capture_setter)
    monkeypatch.setattr(core_tools, "set_read_pipeline_state_callback", lambda *_a, **_kw: None)

    # Stub the worker-dispatch HTTP side so _make_job_record(auto_start=True)
    # doesn't actually try to POST to a worker URL.
    import src.atlas_api_jobs as api_jobs

    # Clear the module-level job registry — see no-seed test for rationale.
    api_jobs._jobs.clear()
    monkeypatch.setattr(api_jobs, "_dispatch_job_to_worker", lambda job: None)
    monkeypatch.setattr(api_jobs, "_record_job_db_start", lambda job: None)

    # Install the bridge into the in-memory job registry by registering
    # routes against a stand-in FastAPI app.
    class _StubApp:
        def __init__(self) -> None:
            self.handlers: list[Any] = []

        def _decorator(self, *_a, **_kw):
            def _wrap(fn):
                self.handlers.append(fn)
                return fn
            return _wrap

        post = _decorator
        get = _decorator
        delete = _decorator
        put = _decorator
        patch = _decorator
        websocket = _decorator

        def on_event(self, *_a, **_kw):
            return self._decorator()

    app = _StubApp()
    api_jobs.register_jobs_routes(
        app,
        project_root=lambda: Path(tmp_path),
        normalize_session_name=lambda s: (s or "").strip().replace("\\", "/"),
    )

    bridge_fn = captured_bridge.get("fn")
    assert bridge_fn is not None, "register_jobs_routes did not install the bridge"

    seed = "make a 4-bit gray counter, top=gray_ctr"
    result = bridge_fn(
        workflow="ssot-gen",
        ip="gray",
        payload={"user_seed": seed},
    )

    assert isinstance(result, dict) and result.get("ok"), f"dispatch failed: {result!r}"
    jobs = result.get("jobs") or []
    assert jobs, "no jobs created"

    job_id = jobs[0]["job_id"]
    job = api_jobs._jobs[job_id]
    worker_prompt = job["prompt"]

    # The seed text MUST appear verbatim in the prompt the worker will see.
    assert "gray_ctr" in worker_prompt, (
        f"top-module name from user seed missing from worker prompt:\n{worker_prompt!r}"
    )
    assert "4-bit gray counter" in worker_prompt, (
        f"user seed body missing from worker prompt:\n{worker_prompt!r}"
    )
    # And it should be labelled so the worker recognises it as the user goal,
    # not just incidental boilerplate.
    assert "[USER REQUIREMENT]" in worker_prompt, (
        "expected [USER REQUIREMENT] section marker in worker prompt"
    )


def test_dispatch_workflow_bridge_no_seed_does_not_emit_section(tmp_path, monkeypatch):
    """If the caller did not supply a seed (e.g. legacy callers, pipeline
    button dispatch), the ``[USER REQUIREMENT]`` section is omitted so we
    don't pollute the worker prompt with an empty header."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "gray")
    monkeypatch.setenv("ATLAS_ACTIVE_USER", "local-admin")

    captured_bridge: Dict[str, Any] = {}
    from core import tools as core_tools

    monkeypatch.setattr(core_tools, "set_dispatch_workflow_callback", lambda cb: captured_bridge.setdefault("fn", cb))
    monkeypatch.setattr(core_tools, "set_read_pipeline_state_callback", lambda *_a, **_kw: None)

    import src.atlas_api_jobs as api_jobs

    # api_jobs._jobs is a module-level registry; jobs from a previous test in
    # this file would otherwise trigger _active_job_conflicts and short-circuit
    # the dispatch path (returning the stale job instead of building a new one).
    api_jobs._jobs.clear()
    monkeypatch.setattr(api_jobs, "_dispatch_job_to_worker", lambda job: None)
    monkeypatch.setattr(api_jobs, "_record_job_db_start", lambda job: None)

    class _StubApp:
        def __init__(self) -> None:
            self.handlers: list[Any] = []

        def _decorator(self, *_a, **_kw):
            def _wrap(fn):
                self.handlers.append(fn)
                return fn
            return _wrap

        post = _decorator
        get = _decorator
        delete = _decorator
        put = _decorator
        patch = _decorator
        websocket = _decorator

        def on_event(self, *_a, **_kw):
            return self._decorator()

    app = _StubApp()
    api_jobs.register_jobs_routes(
        app,
        project_root=lambda: Path(tmp_path),
        normalize_session_name=lambda s: (s or "").strip().replace("\\", "/"),
    )
    bridge_fn = captured_bridge["fn"]

    result = bridge_fn(workflow="ssot-gen", ip="gray", payload={})
    assert result.get("ok"), f"dispatch failed: {result!r}"
    job_id = result["jobs"][0]["job_id"]
    job = api_jobs._jobs[job_id]
    assert "[USER REQUIREMENT]" not in job["prompt"], (
        "no seed was supplied — [USER REQUIREMENT] section must not appear"
    )
