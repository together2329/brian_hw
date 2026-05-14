"""Round-5 responder tests — ledger row-count invariants, model
resolution, WS subscriber visibility, multi-instance race bounds,
permission revoke-mid-flight, rich-text reply preservation, and
config edge cases.
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path
from unittest.mock import patch

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from core.atlas_db import AtlasDB
from core.atlas_multiuser import _MultiUserBridge
from core.atlas_permissions import PermissionPolicy
from core import chat_responder as cr


@pytest.fixture
def world(tmp_path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/r")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")
    return {"db": db, "alice": alice, "bob": bob, "ws": ws, "ip_uart": ip_uart}


def _stream(*chunks):
    def fake(messages, stop=None, suppress_spinner=False, tools=None):
        for c in chunks:
            yield c
    return patch("llm_client.chat_completion_stream", new=fake)


# ---------------------------------------------------------------------------
# Trace ledger row-count invariants
# ---------------------------------------------------------------------------


def test_one_human_chat_produces_exactly_one_reply_and_one_consume(world):
    db = world["db"]
    ip_id = world["ip_uart"]["id"]
    human = db.record_chat_message(ip_id, world["alice"]["id"], "ping")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("pong"):
        r.tick()

    # 1 chat_message from Alice + 1 chat_message from bot = 2 chat_message rows
    chat_msgs = db._fetchall(
        "SELECT * FROM trace_events WHERE event_type='chat_message'"
    )
    assert len(chat_msgs) == 2

    # Exactly 1 chat_consumed row, correlation_id = Alice's chat
    consumed = db._fetchall(
        "SELECT * FROM trace_events WHERE event_type='chat_consumed'"
    )
    assert len(consumed) == 1
    assert consumed[0]["correlation_id"] == human["id"]
    assert consumed[0]["session_id"] == r.session_id


def test_three_human_chats_yield_one_reply_and_three_consumes(world):
    db = world["db"]
    ip_id = world["ip_uart"]["id"]
    ids = []
    for i in range(3):
        ids.append(db.record_chat_message(ip_id, world["alice"]["id"], f"m{i}")["id"])

    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("batch ack"):
        r.tick()

    chat_msgs = db._fetchall(
        "SELECT * FROM trace_events WHERE event_type='chat_message'"
    )
    assert len(chat_msgs) == 4  # 3 human + 1 bot

    consumed = db._fetchall(
        "SELECT correlation_id FROM trace_events WHERE event_type='chat_consumed'"
    )
    assert sorted(r["correlation_id"] for r in consumed) == sorted(ids)


# ---------------------------------------------------------------------------
# Model resolution: --model arg overrides env; env overrides default
# ---------------------------------------------------------------------------


def test_explicit_model_argument_overrides_env(world, monkeypatch):
    monkeypatch.setenv("CHAT_RESPONDER_MODEL", "from-env")
    r = cr.Responder("uart_lite", db=world["db"], model="from-arg",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    assert r.model == "from-arg"


def test_env_model_used_when_no_argument(world, monkeypatch):
    monkeypatch.setenv("CHAT_RESPONDER_MODEL", "haiku-from-env")
    r = cr.Responder("uart_lite", db=world["db"],
                      poll_seconds=0.01, min_interval_seconds=0.0)
    assert r.model == "haiku-from-env"


def test_default_model_when_neither_set(world, monkeypatch):
    monkeypatch.delenv("CHAT_RESPONDER_MODEL", raising=False)
    r = cr.Responder("uart_lite", db=world["db"],
                      poll_seconds=0.01, min_interval_seconds=0.0)
    assert r.model == "gpt-5.3-codex"


# ---------------------------------------------------------------------------
# WS subscriber visibility — broadcast_all reaches the outbox in real time
# ---------------------------------------------------------------------------


def test_bot_reply_event_lands_in_every_session_outbox_in_real_time(world):
    db = world["db"]
    bridge = _MultiUserBridge(single_user=False)
    s1 = bridge._ensure_session("alice/uart_lite/rtl-gen")
    s2 = bridge._ensure_session("bob/uart_lite/rtl-gen")
    s3 = bridge._ensure_session("admin/observer")

    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "live?")
    r = cr.Responder("uart_lite", db=db, bridge=bridge, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("live ack."):
        r.tick()

    for s in (s1, s2, s3):
        events = []
        while not s._outbox.empty():
            events.append(s._outbox.get_nowait())
        chats = [e for e in events if e.get("type") == "chat_message"]
        assert len(chats) == 1, f"session {s.session_id} got {len(chats)} chats"
        assert chats[0]["content"] == "live ack."
        assert chats[0]["display_name"] == "🤖 ATLAS Helper"
        assert chats[0]["room"] == "uart_lite"


# ---------------------------------------------------------------------------
# Multi-instance race bounds — two Responder() instances on same room
# ---------------------------------------------------------------------------


def test_two_responder_instances_same_room_bounded_replies(world):
    """If two Responder() are constructed for the same room (e.g. two
    atlas_ui processes pointing at the same DB), both share the same
    session_id (atlas-helper/<room>/chat-responder). The unread query
    NOT-IN-consumed protects against unbounded duplicate replies — but
    a tight race window can leak a duplicate. We assert ≤2."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "race")
    r1 = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    r2 = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)

    # Sequential ticks; second sees the chat already consumed.
    with _stream("first reply"):
        r1.tick()
    with _stream("second reply (should not appear)"):
        r2.tick()

    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot_replies = [m for m in rows
                   if m["actor_user_id"] in (r1.agent_uid, r2.agent_uid)
                   and m["payload"]["content"].startswith(("first", "second"))]
    assert len(bot_replies) == 1
    assert bot_replies[0]["payload"]["content"] == "first reply"


# ---------------------------------------------------------------------------
# Permission revoke mid-flight
# ---------------------------------------------------------------------------


def test_bot_replies_even_if_user_grant_revoked_mid_flight(world):
    """Bob is the grantee; while he's typing, alice revokes his view.
    The bot's response logic doesn't check the chat author's permission
    (the API gateway did that before insertion), so it should still
    reply to Bob's already-posted chat."""
    db = world["db"]
    ip_id = world["ip_uart"]["id"]
    db.record_chat_message(ip_id, world["bob"]["id"], "blocked?", display_name="Bob")

    # Now revoke Bob's view permission (alice does this in admin)
    db.revoke_ip_permission(ip_id, world["bob"]["id"], "view")

    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("yes, Real test todo B is blocked."):
        n = r.tick()
    assert n == 1

    # The bot reply exists in the ledger — Bob's revocation does not
    # retroactively delete his prior post or block the bot's response.
    rows = db.list_chat_messages(ip_id)
    assert any("Real test todo B is blocked." in m["payload"]["content"]
               for m in rows if m["actor_user_id"] != world["bob"]["id"])

    # But Bob's GET via the API would now 403 (handled at the gateway).
    p = PermissionPolicy(db)
    assert not p.can_enter_room(world["bob"]["id"], "uart_lite")


# ---------------------------------------------------------------------------
# Rich-text reply preservation
# ---------------------------------------------------------------------------


def test_reply_with_newlines_tabs_and_code_blocks_preserved(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "fmt?")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    rich = (
        "Line 1\n"
        "\tindented line\n"
        "```python\n"
        "def foo():\n"
        "    return 42\n"
        "```\n"
        "Final."
    )
    with _stream(rich):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = next(m for m in rows if m["actor_user_id"] == r.agent_uid)
    # Whitespace and structure preserved exactly (strip() only trims edges)
    assert bot["payload"]["content"] == rich.strip()


def test_reply_with_unicode_emoji_korean_preserved(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "다국어")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    reply = "준비 ✅ — workflow status: rtl-gen / running. blocker는 *Real test todo B* 🚧."
    with _stream(reply):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = next(m for m in rows if m["actor_user_id"] == r.agent_uid)
    assert bot["payload"]["content"] == reply


# ---------------------------------------------------------------------------
# Context bundle: IP with no workflow run yet
# ---------------------------------------------------------------------------


def test_responder_handles_ip_with_no_workflow_run(world):
    """A freshly-scaffolded IP has no workflow_runs row. The bundle's
    workflow.latest_run is None and the responder should still build
    a coherent user block (just without workflow info)."""
    db = world["db"]
    # Wipe any runs for uart_lite (safe — none exist in this fixture)
    db._execute("DELETE FROM workflow_runs WHERE ip_id = ?", (world["ip_uart"]["id"],))
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "fresh?")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    captured = {}

    def fake(messages, stop=None, suppress_spinner=False, tools=None):
        captured["user"] = messages[1]["content"]
        yield "no workflow yet."

    with patch("llm_client.chat_completion_stream", new=fake):
        r.tick()
    # The orchestrator-context block exists but workflow line is absent
    assert "<orchestrator-context" in captured["user"]
    assert "ip: uart_lite" in captured["user"]
    # No "workflow:" line because latest_run is None
    assert "workflow:" not in captured["user"]


# ---------------------------------------------------------------------------
# autostart with a workspace that exists but has no IPs
# ---------------------------------------------------------------------------


def test_autostart_workspace_without_ips_still_starts_global(tmp_path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    db.create_user("alice", "Alice", "pw")
    db.upsert_workspace("empty-ws", owner_user_id=db.get_user_by_username("alice")["id"],
                          local_path="/r")
    # No IPs!
    started = cr.autostart_all(db=db)
    rooms = [r.room for r in started]
    assert rooms == ["_global"]
    for r in started:
        r.stop()


# ---------------------------------------------------------------------------
# Empty content after strip is treated as empty reply
# ---------------------------------------------------------------------------


def test_whitespace_only_reply_treated_as_empty(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "?")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("   \n\t  \n"):  # only whitespace
        n = r.tick()
    assert n == 1   # chat consumed
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    # No bot reply posted (record_chat_message would have stripped + skipped)
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid]
    assert bot == []


# ---------------------------------------------------------------------------
# Consume row carries the bot's session_id, not any random id
# ---------------------------------------------------------------------------


def test_consume_row_session_id_matches_responder_session(world):
    db = world["db"]
    chat = db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "id?")
    r = cr.Responder("uart_lite", db=db, model="m",
                      poll_seconds=0.01, min_interval_seconds=0.0)
    with _stream("yep"):
        r.tick()

    rows = db._fetchall(
        "SELECT * FROM trace_events WHERE event_type='chat_consumed' AND correlation_id = ?",
        (chat["id"],),
    )
    assert len(rows) == 1
    assert rows[0]["session_id"] == "atlas-helper/uart_lite/chat-responder"


# ---------------------------------------------------------------------------
# Two different bots (per-IP + global) consume independently of each other
# ---------------------------------------------------------------------------


def test_per_ip_and_global_bots_have_independent_consume_streams(world):
    """A user posts in BOTH the global room and uart_lite. Each bot
    consumes its own scope; their ledger rows do not interfere."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "ip-side")
    db.record_chat_message(None, world["alice"]["id"], "global-side")

    r_ip = cr.Responder("uart_lite", db=db, model="m",
                         poll_seconds=0.01, min_interval_seconds=0.0)
    r_global = cr.Responder("_global", db=db, model="m",
                              poll_seconds=0.01, min_interval_seconds=0.0)

    with _stream("ip-reply"):
        n_ip = r_ip.tick()
    with _stream("global-reply"):
        n_g = r_global.tick()
    assert n_ip == 1 and n_g == 1

    # IP bot's consume ledger
    ip_consumes = db._fetchall(
        "SELECT correlation_id FROM trace_events "
        "WHERE event_type='chat_consumed' AND session_id = ?",
        (r_ip.session_id,),
    )
    # Global bot's consume ledger
    g_consumes = db._fetchall(
        "SELECT correlation_id FROM trace_events "
        "WHERE event_type='chat_consumed' AND session_id = ?",
        (r_global.session_id,),
    )
    assert len(ip_consumes) == 1
    assert len(g_consumes) == 1
    # They reference different originating chats
    assert ip_consumes[0]["correlation_id"] != g_consumes[0]["correlation_id"]
