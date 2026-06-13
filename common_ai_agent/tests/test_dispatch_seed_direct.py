"""Seed propagation on the DIRECT dispatch path (UI button / WS).

Companion to ``tests/test_orchestrator_dispatch_seed.py`` which pins the
orchestrator-chat -> react_bridge -> dispatch_workflow_tool_bridge path.

This file pins the SECOND path that bypasses the orchestrator entirely:
``POST /api/pipeline/dispatch`` invoked by the pipeline UI button (or
WebSocket pipeline dispatch). Before the fix, the handler accepted ``prompt``
as a pipeline-level goal but never tagged it as ``[USER REQUIREMENT]``, so
ssot-gen workers ignored it and produced default CMUX skeletons instead of
the FIFO the user asked for.
"""

from __future__ import annotations

import asyncio
import json
import sys
import types
from pathlib import Path
from typing import Any, Dict


class _StubRequest:
    def __init__(self, payload: Dict[str, Any]) -> None:
        self._payload = payload
        self.headers: Dict[str, str] = {}
        self.client = types.SimpleNamespace(host="127.0.0.1")
        self.cookies: Dict[str, str] = {}
        self.query_params: Dict[str, str] = {}
        self.state = types.SimpleNamespace()
        # `_request_username` and friends read these via Starlette's `scope`
        # dict; we just expose the bits the handler actually touches.
        self.scope: Dict[str, Any] = {"user": {}}

    async def json(self) -> Dict[str, Any]:
        return self._payload


class _StubApp:
    def __init__(self) -> None:
        self.routes: Dict[str, Any] = {}

    def _make_decorator(self, method: str):
        def _decorator(path: str, *_a, **_kw):
            def _wrap(fn):
                self.routes[(method, path)] = fn
                return fn
            return _wrap
        return _decorator

    def __getattr__(self, name: str):
        if name in {"post", "get", "delete", "put", "patch", "websocket", "on_event"}:
            return self._make_decorator(name)
        raise AttributeError(name)


def _write_approval_manifest(project_root: Path, ip: str, *, status: str = "requirements_locked") -> None:
    manifest = project_root / ip / "req" / "approval_manifest.json"
    manifest.parent.mkdir(parents=True, exist_ok=True)
    manifest.write_text(
        json.dumps({
            "status": status,
            "requirements": [{"requirement_id": "REQ_GRAY", "status": "locked", "required": True}],
        }),
        encoding="utf-8",
    )


def _install_dispatch_route(
    tmp_path: Path,
    monkeypatch,
    *,
    approve_truth: bool = True,
) -> tuple[Any, Any]:
    """Register the jobs routes against a stub app, return (app, api_jobs)."""
    monkeypatch.chdir(tmp_path)
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "gray")
    monkeypatch.setenv("ATLAS_ACTIVE_USER", "local-admin")
    if approve_truth:
        _write_approval_manifest(tmp_path, "gray")

    callbacks: Dict[str, Any] = {}
    fake_core_tools = types.SimpleNamespace(
        set_dispatch_workflow_callback=lambda callback, *_a, **_kw: callbacks.__setitem__("dispatch", callback),
        set_read_pipeline_state_callback=lambda *_a, **_kw: None,
    )
    fake_core_pkg = types.ModuleType("core")
    fake_core_pkg.__path__ = [str(Path(__file__).resolve().parents[1] / "core")]
    fake_core_pkg.tools = fake_core_tools  # type: ignore[attr-defined]
    monkeypatch.setitem(sys.modules, "core", fake_core_pkg)
    monkeypatch.setitem(sys.modules, "core.tools", fake_core_tools)

    import src.atlas_api_jobs as api_jobs

    api_jobs._jobs.clear()
    monkeypatch.setattr(api_jobs, "_dispatch_job_to_worker", lambda job: None)
    monkeypatch.setattr(api_jobs, "_record_job_db_start", lambda job: None)
    # The pipeline DB session helper is a closure inside register_jobs_routes,
    # but it returns "" early when the stub request has no db_user_id, so we
    # don't need to patch it.

    app = _StubApp()
    api_jobs.register_jobs_routes(
        app,
        project_root=lambda: tmp_path,
        normalize_session_name=lambda s: (s or "").strip().replace("\\", "/"),
    )
    setattr(app, "dispatch_workflow_callback", callbacks.get("dispatch"))
    return app, api_jobs


def _jobs_from_response(response) -> list[dict[str, Any]]:
    body = getattr(response, "body", None)
    if body is None:
        raise AssertionError(f"no body on response: {response!r}")
    data = json.loads(body.decode("utf-8") if isinstance(body, (bytes, bytearray)) else body)
    assert data.get("ok") is True, f"dispatch failed: {data!r}"
    return data.get("jobs") or []


def test_direct_dispatch_warns_but_runs_before_locked_truth(tmp_path, monkeypatch):
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch, approve_truth=False)
    handler = app.routes[("post", "/api/pipeline/dispatch")]

    request = _StubRequest({
        "ip": "gray",
        "stages": ["ssot-gen"],
        "prompt": "build an async FIFO",
    })
    response = asyncio.get_event_loop().run_until_complete(handler(request))
    body = json.loads(response.body.decode("utf-8"))

    assert response.status_code == 200
    assert body["ok"] is True
    assert body["ip"] == "gray"
    assert body["locked_truth"]["warning"] == "truth_not_locked"
    assert body["locked_truth"]["blocking"] is False
    jobs = body.get("jobs") or []
    assert jobs, "truth lock warning must not prevent job creation"
    job = api_jobs._jobs[jobs[0]["job_id"]]
    assert "[ATLAS TRUTH LOCK STATUS]" in job["prompt"]
    assert "truth_not_locked" in job["prompt"]


def test_dispatch_workflow_tool_warns_but_runs_before_locked_truth(tmp_path, monkeypatch):
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch, approve_truth=False)
    callback = getattr(app, "dispatch_workflow_callback")

    result = callback(workflow="ssot-gen", ip="gray", payload={"session_id": "local-admin/default/gray/orchestrator"})

    assert result["ok"] is True
    assert result["source"] == "dispatch_workflow_tool"
    assert result["locked_truth"]["warning"] == "truth_not_locked"
    assert result["locked_truth"]["blocking"] is False
    jobs = result.get("jobs") or []
    assert jobs, "truth lock warning must not prevent tool dispatch"
    job = api_jobs._jobs[jobs[0]["job_id"]]
    assert "[ATLAS TRUTH LOCK STATUS]" in job["prompt"]
    assert "truth_not_locked" in job["prompt"]


def test_direct_dispatch_user_seed_lands_in_worker_prompt(tmp_path, monkeypatch):
    """POST /api/pipeline/dispatch with body.user_seed must inject
    [USER REQUIREMENT] into every stage's worker prompt."""
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch)
    handler = app.routes[("post", "/api/pipeline/dispatch")]

    seed = "make a FIFO, 8 entries, 16-bit, top=beta_fifo"
    request = _StubRequest({
        "ip": "gray",
        "stages": ["ssot-gen"],
        "user_seed": seed,
    })
    response = asyncio.get_event_loop().run_until_complete(handler(request))
    jobs = _jobs_from_response(response)
    assert jobs, "no jobs created on direct dispatch"

    job = api_jobs._jobs[jobs[0]["job_id"]]
    prompt = job["prompt"]
    assert "[USER REQUIREMENT]" in prompt, (
        f"direct-dispatch path missing [USER REQUIREMENT] section:\n{prompt!r}"
    )
    assert "FIFO" in prompt, f"user seed body missing from worker prompt:\n{prompt!r}"
    assert "beta_fifo" in prompt, f"top-module name missing from prompt:\n{prompt!r}"


def test_direct_dispatch_prompt_field_falls_back_as_seed(tmp_path, monkeypatch):
    """Legacy callers only send ``prompt`` — that should also surface as
    [USER REQUIREMENT] so the worker treats it as the user's concrete goal."""
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch)
    handler = app.routes[("post", "/api/pipeline/dispatch")]

    request = _StubRequest({
        "ip": "gray",
        "stages": ["ssot-gen"],
        "prompt": "build an async FIFO with full/empty flags",
    })
    response = asyncio.get_event_loop().run_until_complete(handler(request))
    jobs = _jobs_from_response(response)
    job = api_jobs._jobs[jobs[0]["job_id"]]
    prompt = job["prompt"]
    assert "[USER REQUIREMENT]" in prompt
    assert "async FIFO" in prompt


def test_direct_dispatch_no_seed_omits_section(tmp_path, monkeypatch):
    """If neither user_seed nor prompt is supplied, no empty header is added."""
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch)
    handler = app.routes[("post", "/api/pipeline/dispatch")]

    request = _StubRequest({"ip": "gray", "stages": ["ssot-gen"]})
    response = asyncio.get_event_loop().run_until_complete(handler(request))
    jobs = _jobs_from_response(response)
    job = api_jobs._jobs[jobs[0]["job_id"]]
    assert "[USER REQUIREMENT]" not in job["prompt"]


def test_job_dispatch_custom_prompt_preserves_ssot_stage_driver(tmp_path, monkeypatch):
    """POST /api/job/dispatch with a custom ssot-gen prompt must still carry
    the compact ATLAS pipeline marker.

    Without this, direct real-LLM ssot-gen runs bypass the compact prompt and
    fall back to the full SSOT template/system prompt path, making tiny smoke
    tests read tens of thousands of tokens before the first write.
    """
    app, api_jobs = _install_dispatch_route(tmp_path, monkeypatch)
    handler = app.routes[("post", "/api/job/dispatch")]

    request = _StubRequest({
        "ip": "gray",
        "workflow": "ssot-gen",
        "exec_mode": "orchestrator",
        "prompt": "build a compact AXI4-Lite status block",
    })
    response = asyncio.get_event_loop().run_until_complete(handler(request))
    body = json.loads(response.body.decode("utf-8"))
    assert body.get("ok") is True, body

    job = api_jobs._jobs[body["job_id"]]
    prompt = job["prompt"]
    assert "[ATLAS_PIPELINE_SSOT_DIRECT_WRITE]" in prompt
    assert "[Orchestrator worker instruction]" in prompt
    assert "compact AXI4-Lite status block" in prompt
