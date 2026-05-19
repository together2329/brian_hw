"""Tests for GET /api/orchestrator/chat/messages endpoint.

Run with:
    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_chat_panel_api.py -v
"""
from __future__ import annotations

import time
from pathlib import Path

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


def _seed_chat_message(db_path: Path, ip_name: str, content: str, ts: float = None):
    """Seed a chat_message trace event using ip_name as the ip_id field (same as the API)."""
    from core.atlas_db import AtlasDB

    with AtlasDB(str(db_path)) as db:
        payload = {"content": content, "display_name": ""}
        row = db.record_trace_event(
            event_type="chat_message",
            payload=payload,
            ip_id=ip_name,
            actor_user_id="",
        )
        if ts is not None:
            db._execute(
                "UPDATE trace_events SET created_at = ? WHERE id = ?",
                (ts, row["id"]),
            )
        return row


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
    payloads = [
        (m.get("payload") or {}).get("content") or m.get("content") or ""
        for m in j["messages"]
    ]
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
