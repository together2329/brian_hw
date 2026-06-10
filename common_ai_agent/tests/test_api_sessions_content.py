"""Content-level tests for the /api/sessions* and /api/session/* surface.

Covers:
  - POST /api/sessions  : create session, missing title -> 400, non-JSON -> 400
  - GET  /api/sessions  : list scoped to calling user
  - GET  /api/sessions/{id} : owner gets session, wrong owner gets 404
  - PATCH /api/sessions/{id}: update allowed fields, non-owner 404
  - DELETE /api/sessions/{id}: owner deletes, non-owner 404
  - GET /api/session/list : filesystem+DB list respects multi-user owner scoping,
                            unauthed in multi-user mode -> 401
  - GET /api/session/history : missing param -> 400, path traversal -> 400,
                               owner access -> 200, cross-user -> 403
  - GET /api/session/state  : owner gets state with todos/messages, cross-user -> 403
  - GET /api/session/worker/status : cross-session owner mismatch -> 403,
                                     unauthenticated -> 401
  - session list isolation: alice sees only her sessions, bob sees only his

Design notes
  - Uses a real in-memory AtlasDB and a fresh FastAPI app per test.
  - Bridge is a minimal mock (no LLM/worker spawning).
  - LLM providers are billing-blocked; no real workers are started.
  - ATLAS_MULTI_USER is controlled per test via monkeypatch.setenv.
"""
from __future__ import annotations

import contextvars
import threading
from pathlib import Path
from types import SimpleNamespace
from typing import Any, Optional

import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient

from core.atlas_db import AtlasDB
from src.atlas_api_sessions import register_sessions_routes


# ---------------------------------------------------------------------------
# Helpers / fixtures
# ---------------------------------------------------------------------------

def _norm(s: str) -> str:
    return str(s or "").strip().strip("/")


class _MockPolicy:
    is_strict = False
    cap_enabled = False

    def to_status_dict(self) -> dict:
        return {"policy": "session-scoped", "single_active_owner": False}


class _MockBridge:
    """Minimal bridge stub — no LLM, no workers, no subprocesses."""

    _owner_active_sessions: dict = {}

    def emit(self, *a: Any, **kw: Any) -> None:
        pass

    def activate_session(self, *a: Any, **kw: Any) -> None:
        pass

    def exit_session(self, *a: Any, **kw: Any) -> None:
        pass

    def request_stop_for_session(self, *a: Any, **kw: Any) -> None:
        pass

    def get_session(self, *a: Any, **kw: Any) -> Optional[object]:
        return None

    def session_worker_policy(self) -> _MockPolicy:
        return _MockPolicy()

    def active_session_for_owner(self, *a: Any, **kw: Any) -> str:
        return ""

    def is_session_running(self, *a: Any, **kw: Any) -> bool:
        return False

    def _using_processes(self) -> bool:
        return False


def _make_db_factory(db_path: str) -> Any:
    """Return a callable that yields fresh context-managed AtlasDB instances."""
    def factory() -> AtlasDB:
        db = AtlasDB(db_path)
        return db

    return factory


def _build_app(
    db_path: str,
    project_root: Path,
    *,
    username: str = "alice",
    user_id: str = "uid-alice",
) -> TestClient:
    """Build a FastAPI test client injecting a fixed user into every request."""
    app = FastAPI()

    _username = username
    _user_id = user_id

    class _InjectUser(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.scope["user"] = {
                "id": _user_id,
                "username": _username,
            }
            return await call_next(request)

    app.add_middleware(_InjectUser)

    cv: contextvars.ContextVar[str] = contextvars.ContextVar("test_cv", default="")

    register_sessions_routes(
        app,
        project_root=lambda: project_root,
        normalize_session_name=_norm,
        active_session_value=lambda: "",
        atlas_active_session_cv=cv,
        atlas_active_ip_cv=cv,
        bridge=_MockBridge(),
        get_jobs_state=lambda: ({}, threading.Lock()),
        atlas_db_factory=_make_db_factory(db_path),
    )
    return TestClient(app)


# ---------------------------------------------------------------------------
# Tests: POST /api/sessions
# ---------------------------------------------------------------------------

def test_create_session_returns_session_id(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.post("/api/sessions", json={"title": "My Session", "project_id": "proj1"})

    assert resp.status_code == 200
    body = resp.json()
    assert "session_id" in body
    assert body["status"] == "created"
    assert isinstance(body["session_id"], str) and len(body["session_id"]) > 0


def test_create_session_missing_title_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.post("/api/sessions", json={"project_id": "proj1"})

    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
    assert "title" in body["error"].lower()


def test_create_session_non_json_body_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.post(
        "/api/sessions",
        content=b"not-json",
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body


def test_create_session_json_array_body_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.post("/api/sessions", json=["array", "not", "object"])

    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body


# ---------------------------------------------------------------------------
# Tests: GET /api/sessions
# ---------------------------------------------------------------------------

def test_list_sessions_empty_for_new_user(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/sessions")

    assert resp.status_code == 200
    body = resp.json()
    assert "sessions" in body
    assert body["sessions"] == []


def test_list_sessions_scoped_per_user(tmp_path: Path, monkeypatch) -> None:
    """Alice and Bob share the same DB but each only sees their own sessions."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")

    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    bob_client = _build_app(db_path, tmp_path, username="bob", user_id="uid-bob")

    alice_client.post("/api/sessions", json={"title": "Alice Session"})
    alice_client.post("/api/sessions", json={"title": "Alice Session 2"})
    bob_client.post("/api/sessions", json={"title": "Bob Session"})

    alice_resp = alice_client.get("/api/sessions").json()
    bob_resp = bob_client.get("/api/sessions").json()

    alice_titles = {s["title"] for s in alice_resp["sessions"]}
    bob_titles = {s["title"] for s in bob_resp["sessions"]}

    assert "Alice Session" in alice_titles
    assert "Alice Session 2" in alice_titles
    assert "Bob Session" not in alice_titles

    assert "Bob Session" in bob_titles
    assert "Alice Session" not in bob_titles


# ---------------------------------------------------------------------------
# Tests: GET /api/sessions/{id}
# ---------------------------------------------------------------------------

def test_get_session_by_owner_returns_full_payload(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    create_resp = client.post(
        "/api/sessions", json={"title": "Detail Test", "project_id": "proj-abc"}
    )
    session_id = create_resp.json()["session_id"]

    resp = client.get(f"/api/sessions/{session_id}")

    assert resp.status_code == 200
    body = resp.json()
    assert body["id"] == session_id
    assert body["title"] == "Detail Test"
    assert body["project_id"] == "proj-abc"
    assert body["status"] == "active"
    assert "user_id" in body


def test_get_session_cross_user_returns_404(tmp_path: Path, monkeypatch) -> None:
    """Bob must not read Alice's session — returns 404 (ownership mismatch)."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")

    alice = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    bob = _build_app(db_path, tmp_path, username="bob", user_id="uid-bob")

    create_resp = alice.post("/api/sessions", json={"title": "Alice Private"})
    session_id = create_resp.json()["session_id"]

    resp = bob.get(f"/api/sessions/{session_id}")

    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body


def test_get_session_nonexistent_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/sessions/nonexistent-id-xyz")

    assert resp.status_code == 404
    body = resp.json()
    assert "error" in body


# ---------------------------------------------------------------------------
# Tests: PATCH /api/sessions/{id}
# ---------------------------------------------------------------------------

def test_update_session_title_persists(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    create_resp = client.post("/api/sessions", json={"title": "Original Title"})
    session_id = create_resp.json()["session_id"]

    patch_resp = client.patch(f"/api/sessions/{session_id}", json={"title": "New Title"})

    assert patch_resp.status_code == 200
    body = patch_resp.json()
    assert body["title"] == "New Title"

    # Verify the change is durable (re-fetch from DB).
    get_resp = client.get(f"/api/sessions/{session_id}")
    assert get_resp.json()["title"] == "New Title"


def test_update_session_cross_user_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")

    alice = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    bob = _build_app(db_path, tmp_path, username="bob", user_id="uid-bob")

    create_resp = alice.post("/api/sessions", json={"title": "Alice's Session"})
    session_id = create_resp.json()["session_id"]

    resp = bob.patch(f"/api/sessions/{session_id}", json={"title": "Bob hijack"})

    assert resp.status_code == 404
    # Verify Alice's session is unchanged.
    original = alice.get(f"/api/sessions/{session_id}").json()
    assert original["title"] == "Alice's Session"


def test_update_session_non_json_body_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    create_resp = client.post("/api/sessions", json={"title": "Temp"})
    session_id = create_resp.json()["session_id"]

    resp = client.patch(
        f"/api/sessions/{session_id}",
        content=b"not json",
        headers={"Content-Type": "application/json"},
    )

    assert resp.status_code == 400
    assert "error" in resp.json()


# ---------------------------------------------------------------------------
# Tests: DELETE /api/sessions/{id}
# ---------------------------------------------------------------------------

def test_delete_session_by_owner_succeeds(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    create_resp = client.post("/api/sessions", json={"title": "To Be Deleted"})
    session_id = create_resp.json()["session_id"]

    del_resp = client.delete(f"/api/sessions/{session_id}")

    assert del_resp.status_code == 200
    body = del_resp.json()
    assert body.get("deleted") is True or body.get("session_id") == session_id

    # Session should no longer appear in the list.
    listing = client.get("/api/sessions").json()
    ids = {s["id"] for s in listing["sessions"]}
    assert session_id not in ids


def test_delete_session_cross_user_returns_404(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")

    alice = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    bob = _build_app(db_path, tmp_path, username="bob", user_id="uid-bob")

    create_resp = alice.post("/api/sessions", json={"title": "Keep This"})
    session_id = create_resp.json()["session_id"]

    resp = bob.delete(f"/api/sessions/{session_id}")

    assert resp.status_code == 404
    # Alice's session must still be retrievable.
    still_there = alice.get(f"/api/sessions/{session_id}")
    assert still_there.status_code == 200


# ---------------------------------------------------------------------------
# Tests: GET /api/session/list
# ---------------------------------------------------------------------------

def test_session_list_single_user_mode_no_auth_needed(tmp_path: Path, monkeypatch) -> None:
    """In single-user mode (ATLAS_MULTI_USER=0) the list is always accessible."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/session/list")

    assert resp.status_code == 200
    body = resp.json()
    assert "sessions" in body
    assert "count" in body
    assert isinstance(body["sessions"], list)


def test_session_list_multi_user_no_login_returns_401(tmp_path: Path, monkeypatch) -> None:
    """When ATLAS_MULTI_USER=1 and the user has no username the list must deny."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")

    # Build a client that injects NO username (empty string simulates anon).
    app = FastAPI()

    class _NoUser(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.scope["user"] = {"id": "", "username": ""}
            return await call_next(request)

    app.add_middleware(_NoUser)
    cv: contextvars.ContextVar[str] = contextvars.ContextVar("cv2", default="")

    register_sessions_routes(
        app,
        project_root=lambda: tmp_path,
        normalize_session_name=_norm,
        active_session_value=lambda: "",
        atlas_active_session_cv=cv,
        atlas_active_ip_cv=cv,
        bridge=_MockBridge(),
        get_jobs_state=lambda: ({}, threading.Lock()),
        atlas_db_factory=_make_db_factory(str(db_path)),
    )
    client = TestClient(app)

    resp = client.get("/api/session/list")

    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body


def test_session_list_multi_user_filters_by_owner(tmp_path: Path, monkeypatch) -> None:
    """Each user only sees their own file-backed sessions."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")

    # Create alice and bob .session directories under tmp_path.
    alice_session = tmp_path / ".session" / "alice" / "myip" / "rtl-gen"
    alice_session.mkdir(parents=True)
    (alice_session / "conversation.json").write_text("[]", encoding="utf-8")

    bob_session = tmp_path / ".session" / "bob" / "bobip" / "fl-gen"
    bob_session.mkdir(parents=True)
    (bob_session / "conversation.json").write_text("[]", encoding="utf-8")

    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    bob_client = _build_app(db_path, tmp_path, username="bob", user_id="uid-bob")

    alice_resp = alice_client.get("/api/session/list").json()
    bob_resp = bob_client.get("/api/session/list").json()

    alice_sessions = {s["session"] for s in alice_resp["sessions"]}
    bob_sessions = {s["session"] for s in bob_resp["sessions"]}

    # Alice sees her session but not Bob's.
    assert any("alice" in s for s in alice_sessions)
    assert not any("bob" in s for s in alice_sessions)

    # Bob sees his session but not Alice's.
    assert any("bob" in s for s in bob_sessions)
    assert not any("alice" in s for s in bob_sessions)


# ---------------------------------------------------------------------------
# Tests: GET /api/session/history
# ---------------------------------------------------------------------------

def test_session_history_missing_param_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/session/history")

    # FastAPI returns 422 for missing required query params.
    assert resp.status_code in (400, 422)


def test_session_history_empty_session_param_returns_400(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/session/history", params={"session": "  "})

    assert resp.status_code == 400
    body = resp.json()
    assert "error" in body
    assert "missing" in body["error"].lower() or "invalid" in body["error"].lower()


def test_session_history_path_traversal_rejected(tmp_path: Path, monkeypatch) -> None:
    """A session value that escapes .session/ must be rejected."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    resp = client.get("/api/session/history", params={"session": "../../../etc/passwd"})

    # Either 400 (traversal detected) or 422 (validation).
    assert resp.status_code in (400, 422)


def test_session_history_owner_gets_messages(tmp_path: Path, monkeypatch) -> None:
    """Owner retrieves history from a real conversation.json file."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    # Seed a session directory with some history.
    session_dir = tmp_path / ".session" / "alice" / "myip" / "rtl-gen"
    session_dir.mkdir(parents=True)
    messages = [
        {"role": "user", "content": "hello"},
        {"role": "assistant", "content": "hi there"},
    ]
    import json
    (session_dir / "conversation.json").write_text(json.dumps(messages), encoding="utf-8")

    resp = client.get("/api/session/history", params={"session": "alice/myip/rtl-gen"})

    assert resp.status_code == 200
    body = resp.json()
    assert "messages" in body
    assert isinstance(body["messages"], list)
    # The two messages should be present (system rows stripped, but user/assistant kept).
    roles = {m.get("role") for m in body["messages"]}
    assert "user" in roles
    assert "assistant" in roles


def test_session_history_cross_user_denied(tmp_path: Path, monkeypatch) -> None:
    """In multi-user mode Alice cannot read Bob's session history."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")

    bob_session = tmp_path / ".session" / "bob" / "bobip" / "wf"
    bob_session.mkdir(parents=True)
    import json
    (bob_session / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "secret"}]), encoding="utf-8"
    )

    # Alice tries to read Bob's session namespace.
    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    resp = alice_client.get("/api/session/history", params={"session": "bob/bobip/wf"})

    assert resp.status_code == 403
    body = resp.json()
    assert "error" in body


def test_session_history_limit_zero_returns_empty(tmp_path: Path, monkeypatch) -> None:
    """limit=0 must return an empty list, not the full history."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    session_dir = tmp_path / ".session" / "alice" / "myip" / "rtl-gen"
    session_dir.mkdir(parents=True)
    import json
    (session_dir / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "msg1"}, {"role": "assistant", "content": "msg2"}]),
        encoding="utf-8",
    )

    resp = client.get(
        "/api/session/history",
        params={"session": "alice/myip/rtl-gen", "limit": "0"},
    )

    assert resp.status_code == 200
    body = resp.json()
    assert body["messages"] == []


# ---------------------------------------------------------------------------
# Tests: GET /api/session/state
# ---------------------------------------------------------------------------

def test_session_state_includes_todos_and_conversation(tmp_path: Path, monkeypatch) -> None:
    """Owner gets full state: conversation + todos + jobs."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path)

    import json
    session_dir = tmp_path / ".session" / "alice" / "myip" / "rtl-gen"
    session_dir.mkdir(parents=True)
    (session_dir / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "test msg"}]),
        encoding="utf-8",
    )
    (session_dir / "todo.json").write_text(
        json.dumps({"todos": [{"id": 1, "text": "do something", "done": False}]}),
        encoding="utf-8",
    )

    resp = client.get("/api/session/state", params={"session": "alice/myip/rtl-gen"})

    assert resp.status_code == 200
    body = resp.json()
    assert "conversation" in body
    assert "todos" in body
    assert "jobs" in body
    assert isinstance(body["conversation"]["messages"], list)
    assert len(body["conversation"]["messages"]) >= 1
    todos = body["todos"].get("todos", [])
    assert len(todos) == 1
    assert todos[0]["text"] == "do something"


def test_session_state_cross_user_denied(tmp_path: Path, monkeypatch) -> None:
    """In multi-user mode Alice cannot read Bob's session state."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")

    bob_session = tmp_path / ".session" / "bob" / "ip" / "wf"
    bob_session.mkdir(parents=True)
    import json
    (bob_session / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "private"}]),
        encoding="utf-8",
    )

    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")
    resp = alice_client.get("/api/session/state", params={"session": "bob/ip/wf"})

    assert resp.status_code == 403
    body = resp.json()
    assert "error" in body


# ---------------------------------------------------------------------------
# Tests: GET /api/session/worker/status
# ---------------------------------------------------------------------------

def test_worker_status_cross_session_denied_in_multi_user(tmp_path: Path, monkeypatch) -> None:
    """Alice cannot query the worker status for Bob's session namespace."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")
    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")

    resp = alice_client.get(
        "/api/session/worker/status",
        params={"session_id": "bob/ip/wf"},
    )

    assert resp.status_code == 403
    body = resp.json()
    assert "error" in body


def test_worker_status_unauthenticated_with_session_returns_401(
    tmp_path: Path, monkeypatch
) -> None:
    """Querying worker status for an explicit session without auth -> 401."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")

    app = FastAPI()

    class _NoUser(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.scope["user"] = {"id": "", "username": ""}
            return await call_next(request)

    app.add_middleware(_NoUser)
    cv: contextvars.ContextVar[str] = contextvars.ContextVar("cv3", default="")

    register_sessions_routes(
        app,
        project_root=lambda: tmp_path,
        normalize_session_name=_norm,
        active_session_value=lambda: "",
        atlas_active_session_cv=cv,
        atlas_active_ip_cv=cv,
        bridge=_MockBridge(),
        get_jobs_state=lambda: ({}, threading.Lock()),
        atlas_db_factory=_make_db_factory(str(db_path)),
    )
    client = TestClient(app)

    resp = client.get("/api/session/worker/status", params={"session_id": "alice/ip/wf"})

    assert resp.status_code == 401
    body = resp.json()
    assert "error" in body


def test_worker_status_returns_policy_fields(tmp_path: Path, monkeypatch) -> None:
    """Worker status (no session param) returns policy shape."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")

    resp = client.get("/api/session/worker/status")

    assert resp.status_code == 200
    body = resp.json()
    # Must include the standard policy fields.
    assert "active_count" in body
    assert isinstance(body["active_count"], int)


# ---------------------------------------------------------------------------
# Tests: Defect A — no-DB-row fail-open hardening
# ---------------------------------------------------------------------------

def test_authorize_no_db_row_denied_on_read(tmp_path: Path, monkeypatch) -> None:
    """Defect A: in multi-user mode, a GET on a session with no DB row must be
    denied (403) even when the namespace owner matches the requesting user.
    Previously the check fell through to return None (allow) when both
    get_session_for_user and find_session returned None."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")
    # Use a real empty DB — no session rows exist for alice/no-db-row/wf.
    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")

    resp = alice_client.get(
        "/api/session/history",
        params={"session": "alice/no-db-row/wf"},
    )

    assert resp.status_code == 403, (
        f"Expected 403 for no-DB-row session read, got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert "error" in body


def test_authorize_no_db_row_denied_state_endpoint(tmp_path: Path, monkeypatch) -> None:
    """Defect A: same hardening applies to /api/session/state."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")
    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")

    resp = alice_client.get(
        "/api/session/state",
        params={"session": "alice/no-db-row/wf"},
    )

    assert resp.status_code == 403, (
        f"Expected 403 for no-DB-row session read, got {resp.status_code}: {resp.text}"
    )
    body = resp.json()
    assert "error" in body


def test_authorize_db_row_owner_allowed(tmp_path: Path, monkeypatch) -> None:
    """Defect A: legitimate flow — a session that has a DB row IS accessible.
    Activate creates the DB row; subsequent history read must succeed (200)."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")
    alice_client = _build_app(db_path, tmp_path, username="alice", user_id="uid-alice")

    # Seed a conversation.json so history has something to return.
    import json
    session_dir = tmp_path / ".session" / "alice" / "myip" / "rtl-gen"
    session_dir.mkdir(parents=True, exist_ok=True)
    (session_dir / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "hello"}]),
        encoding="utf-8",
    )

    # Insert a DB row so ownership is established.
    from core.atlas_db import AtlasDB
    with AtlasDB(db_path) as db:
        db.upsert_runtime_session(
            "alice/myip/rtl-gen",
            "uid-alice",
            owner="alice",
            ip="myip",
            workflow="rtl-gen",
        )

    resp = alice_client.get(
        "/api/session/history",
        params={"session": "alice/myip/rtl-gen"},
    )

    assert resp.status_code == 200, (
        f"Expected 200 for owned session with DB row, got {resp.status_code}: {resp.text}"
    )


# ---------------------------------------------------------------------------
# Tests: Defect B — global os.environ.update not executed in multi-user mode
# ---------------------------------------------------------------------------

def _build_activate_app(
    db_path: str,
    project_root: Path,
    *,
    username: str = "alice",
    user_id: str = "uid-alice",
) -> TestClient:
    """Build a minimal app that supports /api/session/activate for Defect B tests."""
    app = FastAPI()

    _username = username
    _user_id = user_id

    class _InjectUser(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):  # type: ignore[override]
            request.scope["user"] = {
                "id": _user_id,
                "username": _username,
            }
            return await call_next(request)

    app.add_middleware(_InjectUser)
    cv: contextvars.ContextVar[str] = contextvars.ContextVar("test_cv_act", default="")

    register_sessions_routes(
        app,
        project_root=lambda: project_root,
        normalize_session_name=_norm,
        active_session_value=lambda: "",
        atlas_active_session_cv=cv,
        atlas_active_ip_cv=cv,
        bridge=_MockBridge(),
        get_jobs_state=lambda: ({}, threading.Lock()),
        atlas_db_factory=_make_db_factory(db_path),
    )
    return TestClient(app)


def test_activate_multi_user_does_not_mutate_os_environ(
    tmp_path: Path, monkeypatch
) -> None:
    """Defect B: in ATLAS_MULTI_USER=1 mode, /api/session/activate must NOT
    call os.environ.update(context.export_env()).  A user-A activation must not
    bleed ATLAS_ACTIVE_SESSION / ATLAS_USER_NAME / etc. into the shared process
    env that user-B's concurrent request would then observe."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    db_path = str(tmp_path / "atlas.db")
    alice_client = _build_activate_app(
        db_path, tmp_path, username="alice", user_id="uid-alice"
    )

    import os
    sentinel_key = "ATLAS_ACTIVE_SESSION"
    before = os.environ.get(sentinel_key)

    resp = alice_client.post(
        "/api/session/activate",
        json={"owner": "alice", "ip": "myip", "workflow": "rtl-gen"},
    )
    assert resp.status_code == 200, resp.text

    after = os.environ.get(sentinel_key)
    assert after == before, (
        f"Defect B: os.environ[{sentinel_key!r}] was mutated in multi-user mode: "
        f"{before!r} -> {after!r}"
    )


def test_activate_single_user_preserves_os_environ_update(
    tmp_path: Path, monkeypatch
) -> None:
    """Defect B single-user leg: in ATLAS_MULTI_USER=0, the legacy chat_loop path
    still receives env via os.environ.update so the thread-based worker can see
    ATLAS_ACTIVE_SESSION without contextvars."""
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    db_path = str(tmp_path / "atlas.db")
    alice_client = _build_activate_app(
        db_path, tmp_path, username="alice", user_id="uid-alice"
    )

    import os
    resp = alice_client.post(
        "/api/session/activate",
        json={"owner": "alice", "ip": "myip", "workflow": "rtl-gen"},
    )
    assert resp.status_code == 200, resp.text

    # In single-user non-process mode, ATLAS_ACTIVE_SESSION must have been set.
    active = os.environ.get("ATLAS_ACTIVE_SESSION", "")
    assert "alice" in active, (
        f"Expected ATLAS_ACTIVE_SESSION to contain 'alice' in single-user mode, got {active!r}"
    )
