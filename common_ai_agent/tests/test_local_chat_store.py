"""Local .session chat store: unit round-trip + endpoint local-first read.

Covers the "local .session, minimize SQLite" move for chat: writers mirror to
.session/<owner>/<ip>/chat.jsonl and /api/orchestrator/chat/messages reads it
first (DB only as a legacy fallback).
"""
from __future__ import annotations

import sys
import time
from pathlib import Path

from fastapi.testclient import TestClient

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.local_chat_store import append_chat, read_chat, has_local_chat, chat_path


def test_local_chat_round_trip_shape_and_since(tmp_path: Path) -> None:
    owner, ip = "owner_x", "ip_y"
    assert not has_local_chat(tmp_path, owner, ip)
    r1 = append_chat(tmp_path, owner, ip, "hello", role="user", display_name="alice")
    time.sleep(0.01)
    r2 = append_chat(tmp_path, owner, ip, "hi back", role="assistant", display_name="ATLAS")
    assert has_local_chat(tmp_path, owner, ip)

    rows = read_chat(tmp_path, owner, ip)
    assert [r["payload"]["role"] for r in rows] == ["assistant", "user"]  # newest-first
    m = rows[0]
    assert m["event_type"] == "chat_message"
    assert {"id", "ip_id", "actor_user_id", "created_at", "payload"} <= set(m)
    assert {"content", "display_name", "role"} <= set(m["payload"])

    # since filter returns only rows strictly newer than the cutoff
    newer = read_chat(tmp_path, owner, ip, since=r1["created_at"])
    assert [r["payload"]["content"] for r in newer] == ["hi back"]

    # owner isolation
    assert read_chat(tmp_path, "other_owner", ip) == []


def test_appends_accumulate_in_conversation_log(tmp_path: Path) -> None:
    owner, ip = "o", "i"
    for i in range(5):
        append_chat(tmp_path, owner, ip, f"msg{i}", role="user")
    # reuses the existing per-scope full_conversation.json
    assert chat_path(tmp_path, owner, ip).name == "full_conversation.json"
    rows = read_chat(tmp_path, owner, ip, limit=100)
    assert len(rows) == 5
    assert [r["payload"]["content"] for r in rows][-1] == "msg0"  # newest-first


def _make_client(tmp_path: Path, monkeypatch) -> TestClient:
    monkeypatch.chdir(tmp_path)
    import src.atlas_ui as atlas_ui
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    client = TestClient(atlas_ui.create_app())
    reg = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert reg.status_code == 200, reg.text
    return client


def test_chat_messages_endpoint_reads_local_first(tmp_path: Path, monkeypatch) -> None:
    client = _make_client(tmp_path, monkeypatch)
    ip = "localchatip"

    # canonical owner id the reader will key on
    me = client.get("/api/users/me")
    assert me.status_code == 200, me.text
    owner = me.json()["user"]["id"]

    # empty before any chat
    empty = client.get(f"/api/orchestrator/chat/messages?ip={ip}")
    assert empty.status_code == 200, empty.text
    assert empty.json()["messages"] == []

    # seed a local-only message (no DB row) and confirm the endpoint serves it
    append_chat(tmp_path, owner, ip, "from local file", role="user", display_name="u")
    resp = client.get(f"/api/orchestrator/chat/messages?ip={ip}")
    assert resp.status_code == 200, resp.text
    msgs = resp.json()["messages"]
    assert len(msgs) == 1, msgs
    assert msgs[0]["payload"]["content"] == "from local file"
