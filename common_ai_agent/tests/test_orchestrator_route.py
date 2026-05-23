"""Unit tests for the rewritten POST /api/pipeline/orchestrator/chat route
and the new GET /api/orchestrator/runs/{run_id} route.

Stubs the runner so the test is hermetic and does not need an LLM key.
"""

from pathlib import Path

import pytest
from fastapi.testclient import TestClient

from src.orchestrator import runner as runner_mod
from src.orchestrator.runner import OrchestratorRunner, SubmitOutcome


class _StubRunner:
    """Drop-in replacement for OrchestratorRunner used in route tests."""

    def __init__(self):
        self.calls = []
        self._active = {}  # (user_id, ip_id) -> run_id
        self._counter = 0

    def submit_or_attach(self, **kwargs):
        self.calls.append(kwargs)
        key = (kwargs["user_id"], kwargs["ip_id"])
        if key in self._active:
            return SubmitOutcome(run_id=self._active[key], status="appended")
        self._counter += 1
        run_id = f"stub-run-{self._counter}"
        self._active[key] = run_id
        return SubmitOutcome(run_id=run_id, status="started")

    def shutdown(self, wait=False):
        pass


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


@pytest.fixture
def stub_runner(monkeypatch):
    stub = _StubRunner()
    runner_mod.set_runner_for_test(stub)
    monkeypatch.setattr(runner_mod, "get_runner", lambda db_path: stub)
    yield stub
    runner_mod.set_runner_for_test(None)


def test_chat_returns_run_id_and_started_status(tmp_path, monkeypatch, stub_runner):
    from core.atlas_db import AtlasDB
    from src.atlas_api_jobs import ORCHESTRATOR_MODEL, ORCHESTRATOR_REASONING_EFFORT

    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA and run to green", "ip": "ipA"},
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["ip"] == "ipA"
    assert body["run_id"] == "stub-run-1"
    assert body["status"] == "started"
    assert len(stub_runner.calls) == 1
    assert stub_runner.calls[0]["ip_name"] == "ipA"
    assert stub_runner.calls[0]["message_text"] == "create ipA and run to green"
    assert stub_runner.calls[0]["model"] == ORCHESTRATOR_MODEL
    assert stub_runner.calls[0]["reasoning_effort"] == ORCHESTRATOR_REASONING_EFFORT
    assert stub_runner.calls[0]["session_id"] == "u/ipA/orchestrator"
    assert stub_runner.calls[0]["workspace_id"]
    assert body["model"] == ORCHESTRATOR_MODEL
    assert body["reasoning_effort"] == ORCHESTRATOR_REASONING_EFFORT

    db = AtlasDB(str(tmp_path / "atlas.db"))
    try:
        session = db.get_session(stub_runner.calls[0]["session_id"])
        assert session is not None
        assert session["user_id"] == stub_runner.calls[0]["user_id"]
        assert session["ip"] == "ipA"
        assert session["workflow"] == "orchestrator"
    finally:
        db.close()


def test_second_chat_to_same_ip_is_appended(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    first = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA", "ip": "ipA"},
    )
    second = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "also add lint", "ip": "ipA"},
    )
    assert first.json()["status"] == "started"
    assert second.json()["status"] == "appended"
    assert first.json()["run_id"] == second.json()["run_id"]


def test_chat_body_ip_wins_over_generic_for_phrase(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={
            "ip": "mctp_axi",
            "message": "Continue automatically without asking for permission.",
        },
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["ip"] == "mctp_axi"
    assert stub_runner.calls[0]["ip_name"] == "mctp_axi"


def test_chat_explicit_ip_marker_can_override_body_ip(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"ip": "ipA", "message": "continue for ip ipB"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["ip"] == "ipB"
    assert stub_runner.calls[0]["ip_name"] == "ipB"


def test_status_chat_fast_path_records_assistant_reply_without_runner(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "status ?", "ip": "ipA"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["ok"] is True
    assert body["action"] == "status"
    assert body["status"] == "answered"
    assert body["fast_path"] is True
    assert "ipA" in body["reply"]
    assert stub_runner.calls == []

    messages = client.get("/api/orchestrator/chat/messages?ip=ipA").json()["messages"]
    roles = [m["payload"]["role"] for m in messages]
    assert roles == ["user", "assistant"]
    assert messages[-1]["payload"]["content"] == body["reply"]


def test_chat_rejects_missing_message(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post("/api/pipeline/orchestrator/chat", json={"ip": "ipA"})
    assert resp.status_code == 400
    assert "message required" in resp.text


def test_chat_rejects_missing_ip(tmp_path, monkeypatch, stub_runner):
    # No ip in body and no IP marker in message → extraction returns empty
    # → endpoint must reject with 400.
    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "just chatting, no target"},
    )
    assert resp.status_code == 400


def test_run_detail_endpoint_returns_steps(tmp_path, monkeypatch, stub_runner):
    # Seed a run + step directly via the DB the route uses.
    from core.atlas_db import AtlasDB

    db_path = str(tmp_path / "atlas.db")
    db = AtlasDB(db_path)
    db.init_db()
    run = db.create_orchestrator_run(user_id="u1", ip_id="ip1", session_id="s1")
    db.append_orchestrator_step(
        run["id"],
        tool_name="read_pipeline_state",
        decision={"args": {"ip": "ipA"}},
        verdict="ok",
    )
    db.close()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.get(f"/api/orchestrator/runs/{run['id']}")
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["run"]["id"] == run["id"]
    assert len(body["steps"]) == 1
    assert body["steps"][0]["tool_name"] == "read_pipeline_state"


def test_run_detail_404_for_unknown_run(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/runs/does-not-exist")
    assert resp.status_code == 404
