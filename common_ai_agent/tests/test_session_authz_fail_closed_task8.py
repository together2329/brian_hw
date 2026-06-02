"""Task 8 / R20 — ``_authorize_session_request`` must FAIL CLOSED.

The ownership lookup IS the authorization decision: if the lookup raises (e.g. a
transient control-DB error), the request must be DENIED (403), never allowed.
Before Task 8 the ``except Exception: pass`` swallowed the error and fell through
to ``return None`` (ALLOW) — a fail-OPEN authz bug that becomes a cross-user read
risk once reads span runtime DBs.

We drive the REAL ``/api/session/history`` route (which calls
``_authorize_session_request``) with multi-user enabled and an injected DB factory
whose ownership lookup raises, and assert a 403.
"""

from __future__ import annotations

from pathlib import Path

import pytest
from fastapi import FastAPI
from starlette.middleware.base import BaseHTTPMiddleware
from starlette.testclient import TestClient

from src.atlas_api_sessions import register_sessions_routes


class _RaisingDB:
    """Context-managed AtlasDB stub whose ownership lookups raise."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def db_path(self):
        return ":memory:"

    def get_session_for_user(self, *a, **k):
        raise RuntimeError("simulated control-DB failure")

    def find_session(self, *a, **k):
        raise RuntimeError("simulated control-DB failure")


class _AllowingDB:
    """Stub where the requesting user OWNS the session (control lookup succeeds)."""

    def __enter__(self):
        return self

    def __exit__(self, *exc):
        return False

    @property
    def db_path(self):
        return ":memory:"

    def get_session_for_user(self, user_id, session):
        return {"id": session, "user_id": user_id}

    def find_session(self, session):
        return {"id": session, "user_id": "owner-uid"}


def _make_client(db_factory, *, username="alice", user_id="alice-uid"):
    app = FastAPI()

    class _InjectUser(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            request.scope["user"] = {"id": user_id, "username": username}
            return await call_next(request)

    app.add_middleware(_InjectUser)

    register_sessions_routes(
        app,
        project_root=lambda: Path.cwd(),
        normalize_session_name=lambda s: str(s or "").strip().strip("/"),
        active_session_value=lambda: "",
        atlas_active_session_cv=None,
        atlas_active_ip_cv=None,
        bridge=object(),
        get_jobs_state=lambda: ({}, None),
        atlas_db_factory=db_factory,
    )
    return TestClient(app)


def test_authorize_fails_closed_on_lookup_error(monkeypatch):
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    client = _make_client(_RaisingDB)
    # A session NOT owned-by-namespace (no namespace prefix mismatch) so we reach
    # the DB ownership lookup, which raises -> must DENY (403), not allow.
    resp = client.get("/api/session/history", params={"session": "alice/ip/wf"})
    assert resp.status_code == 403, resp.text
    body = resp.json()
    assert "error" in body
    # No filesystem path disclosed in the denial body.
    assert "path" not in body
    assert "db_path" not in body


def test_authorize_allows_owner(monkeypatch):
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    client = _make_client(_AllowingDB)
    # Owner of the session reaches the route body (200, even with no history file).
    resp = client.get("/api/session/history", params={"session": "alice/ip/wf"})
    assert resp.status_code == 200, resp.text


def test_authorize_denies_namespace_mismatch(monkeypatch):
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    client = _make_client(_AllowingDB)
    # Namespace owner (bob) != requesting user (alice) -> 403 before any DB call.
    resp = client.get("/api/session/history", params={"session": "bob/ip/wf"})
    assert resp.status_code == 403, resp.text
