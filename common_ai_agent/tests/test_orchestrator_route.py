"""Unit tests for the rewritten POST /api/pipeline/orchestrator/chat route
and the new GET /api/orchestrator/runs/{run_id} route.

Stubs the runner so the test is hermetic and does not need an LLM key.
"""

import importlib
from pathlib import Path
from typing import Any, cast

import pytest
from fastapi.testclient import TestClient

from src.orchestrator import runner as runner_mod
from src.orchestrator.runner import SubmitOutcome


def _atlas_db_cls():
    return importlib.import_module("core.atlas_db").AtlasDB


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


def _make_client(tmp_path: Path, monkeypatch, username: str = "u") -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def _make_unauthenticated_client(tmp_path: Path, monkeypatch) -> TestClient:
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    return TestClient(atlas_ui.create_app())


def _make_client_with_project_root(tmp_path: Path, monkeypatch, project_root: Path, username: str = "u") -> TestClient:
    import src.atlas_ui as atlas_ui

    project_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(project_root)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", project_root)

    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


@pytest.fixture
def stub_runner(monkeypatch):
    stub = _StubRunner()
    runner_mod.set_runner_for_test(cast(Any, stub))
    monkeypatch.setattr(runner_mod, "get_runner", lambda db_path: stub)
    yield stub
    runner_mod.set_runner_for_test(None)


def test_chat_returns_run_id_and_started_status(tmp_path, monkeypatch, stub_runner):
    from src.atlas_api_jobs import ORCHESTRATOR_MODEL, ORCHESTRATOR_REASONING_EFFORT

    AtlasDB = _atlas_db_cls()
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
    assert stub_runner.calls[0]["session_id"] == "u/default/ipA/orchestrator"
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


def test_chat_start_records_replayable_ack_before_worker_reply(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA and run to green", "ip": "ipA"},
    )

    assert resp.status_code == 200, resp.text
    body = resp.json()
    messages = client.get("/api/orchestrator/chat/messages?ip=ipA").json()["messages"]
    roles = [m["payload"]["role"] for m in messages]
    assert roles == ["user", "assistant"]
    assert messages[0]["payload"]["content"] == "create ipA and run to green"
    assert body["run_id"] in messages[1]["payload"]["content"]
    assert "started" in messages[1]["payload"]["content"]


def test_chat_body_workspace_session_sets_orchestrator_workspace(
    tmp_path, monkeypatch, stub_runner
):
    AtlasDB = _atlas_db_cls()

    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={
            "message": "create ipA and run to green",
            "ip": "ipA",
            "workspace_session": "alt",
        },
    )

    assert resp.status_code == 200, resp.text
    assert stub_runner.calls[0]["session_id"] == "u/alt/ipA/orchestrator"

    db = AtlasDB(str(tmp_path / "atlas.db"))
    try:
        workspace = db.get_workspace(stub_runner.calls[0]["workspace_id"])
        assert workspace is not None
        assert workspace["name"] == "alt"
        assert workspace["local_path"] == str(tmp_path / "u" / "alt")
    finally:
        db.close()


def test_chat_rejects_unauthenticated_multiuser_request(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_unauthenticated_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA", "ip": "ipA"},
    )

    assert resp.status_code == 401
    assert stub_runner.calls == []


@pytest.mark.parametrize("session_key", ["session_id", "orchestrator_session_id"])
def test_chat_rejects_spoofed_foreign_orchestrator_session(
    session_key,
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch, username="alice")

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={
            "message": "create ipA and run to green",
            "ip": "ipA",
            session_key: "bob/alt/ipA/orchestrator",
        },
    )

    assert resp.status_code == 403, resp.text
    assert "session owner/workspace mismatch" in resp.text
    assert stub_runner.calls == []


def test_chat_allows_same_ip_name_in_each_user_default_workspace(tmp_path, monkeypatch, stub_runner):
    AtlasDB = _atlas_db_cls()

    _make_client(tmp_path, monkeypatch, username="alice")
    bob = _make_client(tmp_path, monkeypatch, username="bob")
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        alice = db.get_user_by_username("alice")
        assert alice is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=alice["id"],
            local_path=str(tmp_path / "alice" / "default"),
        )
        ip_row = db.upsert_ip_block(
            workspace["id"],
            "ownedIp",
            ssot_path="ownedIp/yaml/ownedIp.ssot.yaml",
        )
        db.start_workflow_run(
            session_id="alice/default/ownedIp/ssot-gen",
            workspace_id=str(workspace["id"] or ""),
            ip_id=str(ip_row["id"] or ""),
            workflow="ssot-gen",
            status="completed",
        )

    resp = bob.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "continue implementation", "ip": "ownedIp"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["status"] == "started"
    assert stub_runner.calls[0]["session_id"] == "bob/default/ownedIp/orchestrator"


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


def test_status_chat_fast_path_records_body_workspace_session_scope(
    tmp_path, monkeypatch, stub_runner
):
    client = _make_client(tmp_path, monkeypatch)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "status ?", "ip": "ipA", "workspace_session": "alt"},
    )

    assert resp.status_code == 200, resp.text
    alt_messages = client.get(
        "/api/orchestrator/chat/messages?ip=ipA&workspace_session=alt"
    ).json()["messages"]
    default_messages = client.get(
        "/api/orchestrator/chat/messages?ip=ipA&workspace_session=default"
    ).json()["messages"]
    assert [m["payload"]["role"] for m in alt_messages] == ["user", "assistant"]
    assert default_messages == []
    assert stub_runner.calls == []


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
    AtlasDB = _atlas_db_cls()

    client = _make_client(tmp_path, monkeypatch)
    db_path = str(tmp_path / "atlas.db")
    db = AtlasDB(db_path)
    db.init_db()
    user = db.get_user_by_username("u")
    assert user is not None
    workspace = db.upsert_workspace(
        "default",
        owner_user_id=user["id"],
        local_path=str(tmp_path / "u" / "default"),
    )
    ip_row = db.upsert_ip_block(
        workspace["id"],
        "ipA",
        ssot_path="ipA/yaml/ipA.ssot.yaml",
    )
    run = db.create_orchestrator_run(
        user_id=user["id"],
        ip_id=ip_row["id"],
        workspace_id=workspace["id"],
        session_id="u/default/ipA/orchestrator",
    )
    db.append_orchestrator_step(
        run["id"],
        tool_name="read_pipeline_state",
        decision={"args": {"ip": "ipA"}},
        verdict="ok",
    )
    db.close()

    resp = client.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=default"
    )
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["run"]["id"] == run["id"]
    assert len(body["steps"]) == 1
    assert body["steps"][0]["tool_name"] == "read_pipeline_state"


def test_run_detail_hides_run_from_wrong_workspace_or_ip(
    tmp_path, monkeypatch, stub_runner
):
    AtlasDB = _atlas_db_cls()

    client = _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "ipA")
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id=ip_row["id"],
            workspace_id=workspace["id"],
            session_id="u/default/ipA/orchestrator",
        )

    wrong_workspace = client.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=alt"
    )
    wrong_ip = client.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipB&workspace_session=default"
    )

    assert wrong_workspace.status_code == 404
    assert wrong_ip.status_code == 404


def test_run_detail_hides_run_without_workspace_or_ip_scope(
    tmp_path, monkeypatch, stub_runner
):
    AtlasDB = _atlas_db_cls()

    client = _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id="",
            workspace_id="",
            session_id="u/default/ipA/orchestrator",
        )

    resp = client.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=default"
    )

    assert resp.status_code == 404


def test_run_detail_hides_run_from_other_authenticated_user(
    tmp_path, monkeypatch, stub_runner
):
    AtlasDB = _atlas_db_cls()

    alice = _make_client(tmp_path, monkeypatch, username="u")
    bob = _make_client(tmp_path, monkeypatch, username="bob")
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "ipA")
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id=ip_row["id"],
            workspace_id=workspace["id"],
            session_id="u/default/ipA/orchestrator",
        )

    owner_resp = alice.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=default"
    )
    other_resp = bob.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=default"
    )

    assert owner_resp.status_code == 200, owner_resp.text
    assert other_resp.status_code == 404


def test_run_detail_404_for_unknown_run(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/runs/does-not-exist?ip=ipA")
    assert resp.status_code == 404


def test_chat_route_uses_runtime_selector_not_direct_runner(
    tmp_path, monkeypatch
):
    import src.atlas_ui as atlas_ui
    import importlib

    from src.orchestrator import runner as runner_mod

    runtime_mod = importlib.import_module("src.orchestrator.runtime")

    stub = _StubRunner()
    runtime_calls = []

    def fake_runtime_selector(db_path: str, *, project_root: Path, **kwargs):
        runtime_calls.append((db_path, project_root, kwargs))
        return stub

    def fail_direct_runner_lookup(_db_path: str):
        raise AssertionError("route should resolve orchestrator runtime, not direct runner")

    monkeypatch.setattr(runtime_mod, "get_orchestrator_runtime", fake_runtime_selector)
    monkeypatch.setattr(runner_mod, "get_runner", fail_direct_runner_lookup)
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "thread")
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = _make_client(tmp_path, monkeypatch)
    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA and run to green", "ip": "ipA"},
    )

    assert resp.status_code == 200, resp.text
    assert resp.json()["run_id"] == "stub-run-1"
    assert runtime_calls
    assert runtime_calls[0][0] == str(tmp_path / "atlas.db")
    assert runtime_calls[0][1] == tmp_path / "u" / "default"
    assert len(stub.calls) == 1


def test_chat_route_uses_auth_db_for_ipc_runtime_when_trace_db_is_separate(
    tmp_path,
    monkeypatch,
):
    import importlib

    import src.atlas_ui as atlas_ui

    runtime_mod = importlib.import_module("src.orchestrator.runtime")

    stub = _StubRunner()
    runtime_calls = []

    def fake_runtime_selector(db_path: str, *, project_root: Path, **kwargs):
        runtime_calls.append((db_path, project_root, kwargs))
        return stub

    monkeypatch.setattr(runtime_mod, "get_orchestrator_runtime", fake_runtime_selector)
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_TRANSPORT", "ipc")
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = _make_client(tmp_path, monkeypatch)
    auth_db_path = tmp_path / "atlas.db"
    trace_db_path = tmp_path / "trace.db"
    monkeypatch.setenv("ATLAS_TRACE_DB_PATH", str(trace_db_path))

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={"message": "create ipA and run to green", "ip": "ipA"},
    )

    assert resp.status_code == 200, resp.text
    assert runtime_calls
    assert runtime_calls[0][0] == str(auth_db_path)
    assert runtime_calls[0][0] != str(trace_db_path)
    assert stub.calls[0]["session_id"] == "u/default/ipA/orchestrator"


def test_chat_route_does_not_double_append_already_scoped_project_root(
    tmp_path,
    monkeypatch,
):
    import importlib

    import src.atlas_ui as atlas_ui

    runtime_mod = importlib.import_module("src.orchestrator.runtime")

    stub = _StubRunner()
    runtime_calls = []

    def fake_runtime_selector(db_path: str, *, project_root: Path, **kwargs):
        runtime_calls.append((db_path, project_root, kwargs))
        return stub

    scoped_root = tmp_path / "u" / "default"
    monkeypatch.setattr(runtime_mod, "get_orchestrator_runtime", fake_runtime_selector)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", scoped_root)
    client = _make_client_with_project_root(tmp_path, monkeypatch, scoped_root)

    resp = client.post(
        "/api/pipeline/orchestrator/chat",
        json={
            "message": "continue ipA",
            "ip": "ipA",
            "session_id": "u",
            "workspace_session": "default",
            "workflow": "orchestrator",
        },
    )

    assert resp.status_code == 200, resp.text
    assert runtime_calls
    assert runtime_calls[0][1] == scoped_root

    AtlasDB = _atlas_db_cls()
    db = AtlasDB(str(tmp_path / "atlas.db"))
    try:
        workspace = db._execute("SELECT * FROM workspaces WHERE name = ?", ("default",)).fetchone()
        assert workspace is not None
        assert workspace["local_path"] == str(scoped_root)
    finally:
        db.close()


def test_run_detail_requires_ip_scope(tmp_path, monkeypatch, stub_runner):
    client = _make_client(tmp_path, monkeypatch)
    resp = client.get("/api/orchestrator/runs/does-not-exist")
    assert resp.status_code == 400


def test_active_run_rejects_unauthenticated_multiuser_request(
    tmp_path,
    monkeypatch,
    stub_runner,
):
    client = _make_unauthenticated_client(tmp_path, monkeypatch)

    resp = client.get("/api/orchestrator/active_run?ip=ipA&workspace_session=alt")

    assert resp.status_code == 401


def test_active_run_is_scoped_to_request_workspace(
    tmp_path,
    monkeypatch,
    stub_runner,
):
    AtlasDB = _atlas_db_cls()

    client = _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(tmp_path / "atlas.db")) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "ipA")
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id=ip_row["id"],
            workspace_id=workspace["id"],
            session_id="u/default/ipA/orchestrator",
        )

    owner_resp = client.get(
        "/api/orchestrator/active_run?ip=ipA&workspace_session=default"
    )
    alt_resp = client.get(
        "/api/orchestrator/active_run?ip=ipA&workspace_session=alt"
    )

    assert owner_resp.status_code == 200, owner_resp.text
    assert owner_resp.json()["run"]["id"] == run["id"]
    assert alt_resp.status_code == 200, alt_resp.text
    assert alt_resp.json()["run"] is None


def test_orchestrator_run_surfaces_use_control_db_when_trace_db_is_separate(
    tmp_path,
    monkeypatch,
    stub_runner,
):
    AtlasDB = _atlas_db_cls()
    control_db_path = tmp_path / "atlas.db"
    trace_db_path = tmp_path / "trace.db"
    monkeypatch.setenv("ATLAS_TRACE_DB_PATH", str(trace_db_path))

    client = _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(control_db_path)) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "ipA")
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id=ip_row["id"],
            workspace_id=workspace["id"],
            session_id="u/default/ipA/orchestrator",
        )
        db.append_orchestrator_step(
            run["id"],
            tool_name="dispatch_workflow",
            decision={"args": {"workflow": "contract-check"}},
            verdict="ok",
        )

    run_detail = client.get(
        f"/api/orchestrator/runs/{run['id']}?ip=ipA&workspace_session=default"
    )
    active_run = client.get(
        "/api/orchestrator/active_run?ip=ipA&workspace_session=default"
    )

    assert run_detail.status_code == 200, run_detail.text
    assert run_detail.json()["run"]["id"] == run["id"]
    assert run_detail.json()["steps"][0]["tool_name"] == "dispatch_workflow"
    assert active_run.status_code == 200, active_run.text
    assert active_run.json()["run"]["id"] == run["id"]


def test_orchestrator_run_trace_api_returns_shared_latest_decision_trace(
    tmp_path,
    monkeypatch,
    stub_runner,
):
    AtlasDB = _atlas_db_cls()
    control_db_path = tmp_path / "atlas.db"

    client = _make_client(tmp_path, monkeypatch)
    with AtlasDB(str(control_db_path)) as db:
        user = db.get_user_by_username("u")
        assert user is not None
        workspace = db.upsert_workspace(
            "default",
            owner_user_id=user["id"],
            local_path=str(tmp_path / "u" / "default"),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "ipA")
        run = db.create_orchestrator_run(
            user_id=user["id"],
            ip_id=ip_row["id"],
            workspace_id=workspace["id"],
            session_id="u/default/ipA/orchestrator",
        )
        db.update_orchestrator_run(run["id"], status="completed", final_state="completed", ended=True)
        db.append_orchestrator_step(
            run["id"],
            tool_name="dispatch_workflow",
            decision={"args": {"workflow": "tb-gen", "reason": "repair coverage"}},
            evidence_read={"result": {"ok": False, "error": "dispatch bridge timed out"}},
            verdict="tool_failed",
        )

    trace = client.get(
        "/api/orchestrator/runs/latest/trace?ip=ipA&workspace_session=default"
    )
    by_id = client.get(
        f"/api/orchestrator/runs/{run['id']}/trace?ip=ipA&workspace_session=default"
    )

    assert trace.status_code == 200, trace.text
    body = trace.json()
    assert body["run_id"] == run["id"]
    assert body["run"]["effective_status"] == "blocked"
    assert body["run"]["effective_final_state"] == "tool_failed"
    assert body["steps"][0]["status"] == "failed"
    assert body["steps"][0]["detail"] == "dispatch tb-gen [NO JOB] [FAILED]"
    assert by_id.status_code == 200, by_id.text
    assert by_id.json()["run_id"] == run["id"]
