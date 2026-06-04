"""Tests for GET /api/orchestrator/chat/messages endpoint.

Run with:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_chat_panel_api.py -v
"""
from __future__ import annotations

import importlib
import time
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient


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


def _seed_chat_message(
    db_path: Path,
    ip_name: str,
    content: str,
    ts: float | None = None,
    *,
    username: str = "u",
    workspace_name: str = "default",
) -> dict[str, Any]:
    """Seed a chat_message via record_chat_message using the resolved ip_blocks.id (UUID).

    Mirrors how the orchestrator writes messages so the endpoint's name→UUID
    resolution can find them. Uses the DB user UUID for owner_user_id so the
    workspace key matches what the endpoint resolves via _request_db_user_id.
    """
    AtlasDB = importlib.import_module("core.atlas_db").AtlasDB

    with AtlasDB(str(db_path)) as db:
        user_row = db.get_user_by_username(username)
        user_db_id = user_row["id"] if user_row else username
        workspace = db.upsert_workspace(
            workspace_name,
            owner_user_id=user_db_id,
            local_path=str(db_path.parent / username / workspace_name),
        )
        ip_row = db.upsert_ip_block(workspace["id"], ip_name)
        row = db.record_chat_message(
            ip_id=ip_row["id"],
            user_id=user_db_id,
            content=content,
            role="assistant",
        )
        if ts is not None:
            db._execute(
                "UPDATE trace_events SET created_at = ? WHERE id = ?",
                (ts, row["id"]),
            )
        return row


def _payloads(messages: list[dict[str, Any]]) -> list[str]:
    return [
        (m.get("payload") or {}).get("content") or m.get("content") or ""
        for m in messages
    ]


def test_get_without_auth_returns_401(tmp_path, monkeypatch):
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
    r = client.get("/api/orchestrator/chat/messages?ip=pl330")
    assert r.status_code == 401


def test_bad_ip_returns_400(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    r = client.get("/api/orchestrator/chat/messages?ip=bad%20ip!")
    assert r.status_code == 400


def test_overlong_ip_returns_400(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    overlong_ip = "a" * 65
    r = client.get(f"/api/orchestrator/chat/messages?ip={overlong_ip}")
    assert r.status_code == 400


def test_get_with_auth_returns_valid_schema(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"
    _seed_chat_message(db_path, "pl330", "hello from orchestrator")

    r = client.get("/api/orchestrator/chat/messages?ip=pl330")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    assert isinstance(j["messages"], list)
    assert "next_since" in j
    assert len(j["messages"]) >= 1
    msg = j["messages"][0]
    for field in ("id", "created_at"):
        assert field in msg, f"missing field: {field}"


def test_db_fallback_scopes_absent_workspace_to_default(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    _seed_chat_message(db_path, "pl330", "default workspace", workspace_name="default")
    _seed_chat_message(db_path, "pl330", "alt workspace", workspace_name="alt")

    implicit = client.get("/api/orchestrator/chat/messages?ip=pl330")
    explicit_alt = client.get("/api/orchestrator/chat/messages?ip=pl330&workspace_session=alt")

    assert implicit.status_code == 200, implicit.text
    assert explicit_alt.status_code == 200, explicit_alt.text
    assert _payloads(implicit.json()["messages"]) == ["default workspace"]
    assert _payloads(explicit_alt.json()["messages"]) == ["alt workspace"]


def test_overlong_workspace_session_is_bounded_to_default(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"
    overlong_workspace = "a" * 65

    _seed_chat_message(db_path, "pl330", "default workspace", workspace_name="default")
    _seed_chat_message(db_path, "pl330", "overlong workspace", workspace_name=overlong_workspace)

    r = client.get(f"/api/orchestrator/chat/messages?ip=pl330&workspace_session={overlong_workspace}")

    assert r.status_code == 200, r.text
    assert _payloads(r.json()["messages"]) == ["default workspace"]


def test_explicit_workspace_db_fallback_is_not_masked_by_legacy_local_chat(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    me = client.get("/api/users/me")
    assert me.status_code == 200, me.text
    owner = me.json()["user"]["id"]

    append_chat = importlib.import_module("core.local_chat_store").append_chat

    append_chat(tmp_path, owner, "pl330", "legacy local", role="assistant", display_name="ATLAS")
    _seed_chat_message(db_path, "pl330", "alt workspace", workspace_name="alt")

    r = client.get("/api/orchestrator/chat/messages?ip=pl330&workspace_session=alt")
    assert r.status_code == 200, r.text
    assert _payloads(r.json()["messages"]) == ["alt workspace"]


def test_db_fallback_keeps_user_workspace_isolation(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    AtlasDB = importlib.import_module("core.atlas_db").AtlasDB

    with AtlasDB(str(db_path)) as db:
        if db.get_user_by_username("other") is None:
            db.create_user("other", "other")

    _seed_chat_message(db_path, "pl330", "current user", username="u")
    _seed_chat_message(db_path, "pl330", "other user", username="other")

    r = client.get("/api/orchestrator/chat/messages?ip=pl330")
    assert r.status_code == 200, r.text
    assert _payloads(r.json()["messages"]) == ["current user"]


def test_since_filter_excludes_older_rows(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    old_ts = time.time() - 100
    new_ts = time.time()

    _seed_chat_message(db_path, "pl330", "old message", ts=old_ts)
    _seed_chat_message(db_path, "pl330", "new message", ts=new_ts)

    # since = old_ts + 50 should exclude the old message but include the new one
    cutoff = old_ts + 50
    r = client.get(f"/api/orchestrator/chat/messages?ip=pl330&since={cutoff}")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    payloads = _payloads(j["messages"])
    assert "new message" in payloads
    assert "old message" not in payloads


def test_messages_in_chronological_order(tmp_path, monkeypatch):
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    base = time.time() - 10
    _seed_chat_message(db_path, "pl330", "first", ts=base)
    _seed_chat_message(db_path, "pl330", "second", ts=base + 1)
    _seed_chat_message(db_path, "pl330", "third", ts=base + 2)

    r = client.get("/api/orchestrator/chat/messages?ip=pl330")
    assert r.status_code == 200
    msgs = r.json()["messages"]
    # Endpoint returns chronological order (oldest first)
    timestamps = [m["created_at"] for m in msgs]
    assert timestamps == sorted(timestamps)


def test_ip_name_resolves_to_uuid_round_trip(tmp_path, monkeypatch):
    """Regression: endpoint must resolve ip NAME to ip_blocks.id (UUID) before querying.

    Seeds a message using the UUID path (as the orchestrator does), then GETs
    by ip NAME — asserts the message is visible.
    """
    client = _make_client(tmp_path, monkeypatch)
    db_path = tmp_path / "atlas.db"

    _seed_chat_message(db_path, "foo_round_trip", "round trip content")

    r = client.get("/api/orchestrator/chat/messages?ip=foo_round_trip")
    assert r.status_code == 200
    j = r.json()
    assert j["ok"] is True
    payloads = _payloads(j["messages"])
    assert "round trip content" in payloads, f"message not found; got: {j['messages']}"
