from __future__ import annotations

import importlib
import socket
import sys
import threading
import time
from contextlib import contextmanager
from pathlib import Path
from typing import Iterator, Protocol

import pytest
from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


RunCall = dict[str, object]


class _RunEntryLike(Protocol):
    run_id: str
    status: str
    started_at: float
    finished_at: float
    result: dict[str, object]

    def add_log(self, kind: str, content: str, *, role: str = "") -> None:
        ...


def _wait_for_port(port: int, timeout_s: float = 5.0) -> None:
    deadline = time.time() + timeout_s
    while time.time() < deadline:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.settimeout(0.1)
            try:
                sock.connect(("127.0.0.1", port))
                return
            except OSError:
                time.sleep(0.05)
    raise RuntimeError(f"server did not bind port {port}")


def _port_from_url(url: str) -> int:
    return int(url.rstrip("/").rsplit(":", 1)[1])


@contextmanager
def _real_agent_worker(
    monkeypatch: pytest.MonkeyPatch,
    calls: list[RunCall],
    port: int,
) -> Iterator[str]:
    import uvicorn

    agent_server = importlib.import_module("core.agent_server")

    def fake_react_task(
        entry: _RunEntryLike,
        task: str,
        model: str = "",
        todos: object | None = None,
        context: str = "",
        workflow: str = "",
        session_name: str = "",
        ip: str = "",
        rtl_version_id: str = "",
        project_root: str = "",
        artifact_versions: object | None = None,
        reasoning_effort: str = "",
        custom_system_prompt: str = "",
        custom_allowed_tools: object | None = None,
        custom_agent: str = "",
        custom_agent_owner_id: str = "",
    ) -> None:
        entry.status = "running"
        entry.started_at = time.time()
        entry.add_log("system", f"fake worker executing {workflow}", role="system")
        calls.append({
            "artifact_versions": artifact_versions or [],
            "context": context,
            "ip": ip,
            "model": model,
            "project_root": project_root,
            "reasoning_effort": reasoning_effort,
            "rtl_version_id": rtl_version_id,
            "run_id": entry.run_id,
            "session": session_name,
            "task": task,
            "workflow": workflow,
        })
        entry.status = "completed"
        entry.finished_at = time.time()
        entry.result = {
            "error": "",
            "execution_time_ms": 1,
            "files_modified": [],
            "result": f"completed {workflow}",
            "run_id": entry.run_id,
            "status": "completed",
        }

    monkeypatch.setattr(agent_server, "_run_react_task", fake_react_task)
    monkeypatch.setattr(agent_server, "_PERSISTENCE_ENABLED", False)
    with agent_server._runs_lock:
        agent_server._runs.clear()

    app = agent_server.create_app()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()
    _wait_for_port(port)
    try:
        yield f"http://127.0.0.1:{port}"
    finally:
        server.should_exit = True
        thread.join(timeout=5)
        with agent_server._runs_lock:
            agent_server._runs.clear()


def _make_client(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    return TestClient(atlas_ui.create_app())


def _register(client: TestClient, username: str) -> str:
    response = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert response.status_code == 200, response.text
    return str(response.json()["user"]["id"])


def _login(client: TestClient, username: str) -> None:
    response = client.post("/api/auth/login", json={"username": username, "password": "pw"})
    assert response.status_code == 200, response.text


def test_job_dispatch_denies_when_ip_access_lookup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    AtlasDB = importlib.import_module("core.atlas_db").AtlasDB

    client = _make_client(tmp_path, monkeypatch)
    _register(client, "alice")
    _login(client, "alice")
    original_fetchone = AtlasDB._fetchone

    def fail_access_lookup(self, sql, params=()):
        if "ip_permissions" in str(sql) or "workflow_runs" in str(sql):
            raise RuntimeError("db unavailable")
        return original_fetchone(self, sql, params)

    monkeypatch.setattr(AtlasDB, "_fetchone", fail_access_lookup)
    response = client.post("/api/job/dispatch", json={
        "exec_mode": "orchestrator",
        "ip": "db_fail_ip",
        "model": "gpt-5.5",
        "workflow": "rtl-gen",
        "workspace_session": "default",
    })

    assert response.status_code == 403, response.text
    assert "forbidden" in response.text


def test_dispatch_many_denies_when_ip_access_lookup_fails(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    AtlasDB = importlib.import_module("core.atlas_db").AtlasDB

    client = _make_client(tmp_path, monkeypatch)
    _register(client, "alice")
    _login(client, "alice")
    original_fetchone = AtlasDB._fetchone

    def fail_access_lookup(self, sql, params=()):
        if "ip_permissions" in str(sql) or "workflow_runs" in str(sql):
            raise RuntimeError("db unavailable")
        return original_fetchone(self, sql, params)

    monkeypatch.setattr(AtlasDB, "_fetchone", fail_access_lookup)
    response = client.post("/api/jobs/dispatch_many", json={
        "exec_mode": "orchestrator",
        "jobs": [
            {
                "ip": "db_fail_ip",
                "model": "gpt-5.5",
                "workflow": "rtl-gen",
                "workspace_session": "default",
            }
        ],
    })

    assert response.status_code == 207, response.text
    body = response.json()
    assert body["jobs"] == []
    assert body["errors"] == [{"error": "forbidden", "index": 0}]


def test_job_dispatch_reaches_distinct_real_agent_server_workers_per_user(
    tmp_path: Path,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    jobs = importlib.import_module("atlas_api_jobs")

    monkeypatch.setenv("ATLAS_WORKER_TRANSPORT", "http")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PER_USER", "1")
    monkeypatch.setenv("ATLAS_LAZY_WORKERS", "0")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_BASE", "6300")
    monkeypatch.setenv("ATLAS_WORKFLOW_WORKER_PORT_SPAN", "400")
    with jobs._jobs_lock:
        jobs._jobs.clear()
    with jobs._SESSION_WORKER_PORT_LOCK:
        jobs._SESSION_WORKER_PORTS.clear()
        jobs._SESSION_WORKER_KEYS_BY_PORT.clear()

    client = _make_client(tmp_path, monkeypatch)
    alice_id = _register(client, "alice")
    bob_id = _register(client, "bob")
    alice_session = "alice/alt/pl330/rtl-gen"
    bob_session = "bob/alt/pl330/rtl-gen"
    alice_url = jobs._resolve_worker_url_for_job(
        "rtl-gen",
        session_name=alice_session,
        user_id="alice",
        db_user_id=alice_id,
        exec_mode="orchestrator",
    )
    bob_url = jobs._resolve_worker_url_for_job(
        "rtl-gen",
        session_name=bob_session,
        user_id="bob",
        db_user_id=bob_id,
        exec_mode="orchestrator",
    )
    assert alice_url != bob_url

    calls: list[RunCall] = []
    try:
        with (
            _real_agent_worker(monkeypatch, calls, _port_from_url(alice_url)) as live_alice_url,
            _real_agent_worker(monkeypatch, calls, _port_from_url(bob_url)) as live_bob_url,
        ):
            assert live_alice_url == alice_url
            assert live_bob_url == bob_url

            _login(client, "alice")
            alice_resp = client.post("/api/job/dispatch", json={
                "exec_mode": "orchestrator",
                "ip": "pl330",
                "model": "gpt-5.5",
                "workflow": "rtl-gen",
                "workspace_session": "alt",
            })
            assert alice_resp.status_code == 200, alice_resp.text

            _login(client, "bob")
            bob_resp = client.post("/api/job/dispatch", json={
                "exec_mode": "orchestrator",
                "ip": "pl330",
                "model": "gpt-5.5",
                "workflow": "rtl-gen",
                "workspace_session": "alt",
            })
            assert bob_resp.status_code == 200, bob_resp.text

            for _ in range(50):
                if len(calls) == 2:
                    break
                time.sleep(0.1)

            by_session = {str(call["session"]): call for call in calls}
            assert sorted(by_session) == [alice_session, bob_session]
            assert by_session[alice_session]["project_root"] == str(tmp_path / "alice" / "alt")
            assert by_session[bob_session]["project_root"] == str(tmp_path / "bob" / "alt")
            assert by_session[alice_session]["model"] == "gpt-5.5"
            assert by_session[bob_session]["model"] == "gpt-5.5"
            assert alice_resp.json()["worker"] == alice_url
            assert bob_resp.json()["worker"] == bob_url
            assert alice_resp.json()["worker"] != bob_resp.json()["worker"]
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()
        with jobs._SESSION_WORKER_PORT_LOCK:
            jobs._SESSION_WORKER_PORTS.clear()
            jobs._SESSION_WORKER_KEYS_BY_PORT.clear()
