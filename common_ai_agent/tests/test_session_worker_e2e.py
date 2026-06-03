"""E2E verification of single-active session-worker through the real HTTP path.

Drives create_app() -> auth (/api/auth/register) -> /api/session/activate ->
/api/session/worker/status exactly as Atlas runs in production. Only the LEAF
process manager is a FakeProcessManager (deterministic, no subprocess/LLM); the
entire bridge + API + policy control plane is real.
"""

from __future__ import annotations

import sys
import time
from pathlib import Path

import pytest
from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
for p in (PROJECT_ROOT, PROJECT_ROOT / "src"):
    if str(p) not in sys.path:
        sys.path.insert(0, str(p))

from tests.support.fake_process_manager import FakeProcessManager  # noqa: E402


def _register(client: TestClient, username: str) -> None:
    r = client.post("/api/auth/register", json={"username": username, "password": "pw"})
    assert r.status_code == 200, r.text


def _activate(client, session_id, ip, workflow, preserve_running=None, workspace_session=None):
    body = {"session_id": session_id, "ip": ip, "workflow": workflow}
    if workspace_session is not None:
        body["workspace_session"] = workspace_session
    if preserve_running is not None:
        body["preserve_running"] = preserve_running
    return client.post("/api/session/activate", json=body)


def _make_app(tmp_path, monkeypatch, *, max_active):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.setenv("ATLAS_SESSION_WORKER_KEEPALIVE", "1")
    monkeypatch.setenv("ATLAS_SESSION_WORKER_POLICY", "single-active-owner")
    monkeypatch.setenv("ATLAS_SESSION_WORKER_MAX_ACTIVE", str(max_active))
    for k in ("ATLAS_ORCHESTRATOR_MODE", "ATLAS_EXEC_MODE", "ATLAS_DEFAULT_EXEC_MODE"):
        monkeypatch.delenv(k, raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    app = atlas_ui.create_app()
    # Swap the leaf manager for a deterministic in-memory double; the bridge,
    # policy, activation API and status endpoint are all the real thing.
    app.state.bridge._process_manager = FakeProcessManager()
    assert app.state.bridge.session_worker_policy().is_strict is True
    return app


def _alive_for(fake, owner):
    return sorted(s for s in fake.list_active() if s.split("/", 1)[0] == owner)


def _wait_until_alive(fake, session_id: str) -> None:
    deadline = time.time() + 2.0
    while time.time() < deadline:
        if session_id in fake.list_active():
            return
        time.sleep(0.02)
    assert session_id in fake.list_active()


def test_e2e_strict_switch_isolation_and_status(tmp_path, monkeypatch):
    app = _make_app(tmp_path, monkeypatch, max_active=10)
    fake = app.state.bridge._process_manager
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    assert _activate(alice, "alice", "ip_a", "ssot-gen").status_code == 200
    assert _activate(bob, "bob", "ip_a", "rtl-gen").status_code == 200
    assert _alive_for(fake, "alice") == ["alice/ip_a/ssot-gen"]
    assert "bob/ip_a/rtl-gen" in fake.list_active()

    # Alice switches workflow (preserve_running=true must NOT keep the old worker
    # in strict mode): old terminates, bob untouched, response reports the switch.
    resp = _activate(alice, "alice", "ip_a", "rtl-gen", preserve_running=True)
    assert resp.status_code == 200, resp.text
    body = resp.json()
    assert body["single_active_owner"] is True
    assert body["session_worker_policy"]["policy"] == "single-active-owner"
    assert body["switch_status"] in {"switched", "active_no_worker"}
    assert body["preserve_running_effective"] is False  # strict overrides preserve
    assert _alive_for(fake, "alice") == ["alice/ip_a/rtl-gen"]
    assert "bob/ip_a/rtl-gen" in fake.list_active()  # other owner never touched

    # Status endpoint is user-scoped: alice sees only her slot, never bob's id.
    st = alice.get("/api/session/worker/status")
    assert st.status_code == 200, st.text
    sbody = st.json()
    assert sbody["policy"] == "single-active-owner"
    assert sbody["owner"] == "alice"
    assert sbody["owner_active_session"] == "alice/ip_a/rtl-gen"
    assert "bob" not in str(sbody)


def test_worker_status_uses_requested_v2_workspace_session(tmp_path, monkeypatch):
    app = _make_app(tmp_path, monkeypatch, max_active=10)
    fake = app.state.bridge._process_manager
    alice = TestClient(app)
    _register(alice, "alice")

    assert _activate(
        alice, "alice", "ip_a", "ssot-gen", workspace_session="s1"
    ).status_code == 200
    assert _activate(
        alice, "alice", "ip_a", "ssot-gen", workspace_session="s2"
    ).status_code == 200
    assert app.state.bridge.warm_session("alice/s1/ip_a/ssot-gen")["alive"] is True
    assert app.state.bridge.warm_session("alice/s2/ip_a/ssot-gen")["alive"] is True
    _wait_until_alive(fake, "alice/s1/ip_a/ssot-gen")
    _wait_until_alive(fake, "alice/s2/ip_a/ssot-gen")

    s1 = alice.get(
        "/api/session/worker/status",
        params={"session_id": "alice/s1/ip_a/ssot-gen"},
    )
    assert s1.status_code == 200, s1.text
    assert s1.json()["owner_active_session"] == "alice/s1/ip_a/ssot-gen"
    assert s1.json()["worker"]["session_id"] == "alice/s1/ip_a/ssot-gen"

    s2 = alice.get(
        "/api/session/worker/status",
        params={"session_id": "alice/s2/ip_a/ssot-gen"},
    )
    assert s2.status_code == 200, s2.text
    assert s2.json()["owner_active_session"] == "alice/s2/ip_a/ssot-gen"
    assert s2.json()["worker"]["session_id"] == "alice/s2/ip_a/ssot-gen"

    denied = alice.get(
        "/api/session/worker/status",
        params={"session_id": "bob/s1/ip_a/ssot-gen"},
    )
    assert denied.status_code == 403, denied.text


def test_e2e_capacity_blocked_activation_is_active_no_worker(tmp_path, monkeypatch):
    # Global cap of 1: the first owner consumes it; a NET-NEW second owner's
    # activation must succeed as a focus change but report capacity_wait and NOT
    # leave a live worker (plan Task 6 / Wave-3 H6).
    app = _make_app(tmp_path, monkeypatch, max_active=1)
    fake = app.state.bridge._process_manager
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    assert _activate(alice, "alice", "ip_a", "ssot-gen").status_code == 200
    assert _alive_for(fake, "alice") == ["alice/ip_a/ssot-gen"]

    resp = _activate(bob, "bob", "ip_a", "rtl-gen")
    assert resp.status_code == 200, resp.text  # focus change still succeeds
    body = resp.json()
    assert body["switch_status"] == "active_no_worker", body
    assert str(body.get("session_worker_warmup", {}).get("status")) == "capacity_wait", body
    # The cap held: bob never got a live worker; alice's is intact.
    assert "bob/ip_a/rtl-gen" not in fake.list_active()
    assert _alive_for(fake, "alice") == ["alice/ip_a/ssot-gen"]
