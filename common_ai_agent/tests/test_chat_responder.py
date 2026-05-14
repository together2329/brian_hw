"""Tests for the chat-responder bot (core/chat_responder.py).

LLM calls are mocked — the loop logic, watermark, throttle, self-loop
guard, and ledger writes are exercised end-to-end with an in-memory
AtlasDB.
"""
from __future__ import annotations

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
from core import chat_responder as cr


@pytest.fixture
def world(tmp_path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/r")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    return {
        "db": db, "alice": alice, "bob": bob, "ip_uart": ip_uart,
    }


def _mock_llm(reply: str):
    """Patch chat_completion_stream to yield a fixed reply chunked."""
    def fake_stream(messages, stop=None, suppress_spinner=False, tools=None):
        for ch in [reply[i:i+8] for i in range(0, len(reply), 8)]:
            yield ch
    # llm_client lives under src/ — patch where chat_responder imports it.
    return patch("llm_client.chat_completion_stream", new=fake_stream)


# ---------------------------------------------------------------------------
# Service account
# ---------------------------------------------------------------------------


def test_agent_service_account_seeded(world):
    r = cr.Responder("uart_lite", db=world["db"], model="mock", poll_seconds=0.01)
    user = world["db"].get_user_by_username("atlas-helper")
    assert user is not None
    assert user["role"] == "agent"
    assert user["id"] == r.agent_uid
    assert "ATLAS Helper" in user["display_name"]


def test_agent_account_idempotent(world):
    cr.Responder("uart_lite", db=world["db"], model="mock", poll_seconds=0.01)
    cr.Responder("uart_lite", db=world["db"], model="mock", poll_seconds=0.01)
    rows = world["db"]._fetchall(
        "SELECT id FROM users WHERE username='atlas-helper'"
    )
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Room resolution
# ---------------------------------------------------------------------------


def test_unknown_room_raises(world):
    with pytest.raises(SystemExit):
        cr.Responder("not_an_ip", db=world["db"], model="mock", poll_seconds=0.01)


def test_global_room_resolves_to_null_ip(world):
    r = cr.Responder("_global", db=world["db"], model="mock", poll_seconds=0.01)
    assert r.ip_id is None
    assert r.ip_name is None
    assert "_global" in r.system_prompt


def test_per_ip_room_loads_ip_prompt_with_substitution(world):
    r = cr.Responder("uart_lite", db=world["db"], model="mock", poll_seconds=0.01)
    assert r.ip_id == world["ip_uart"]["id"]
    assert r.ip_name == "uart_lite"
    # The prompt template uses {ip_name} placeholder; substitution must happen.
    assert "uart_lite" in r.system_prompt
    assert "{ip_name}" not in r.system_prompt


# ---------------------------------------------------------------------------
# Tick: end-to-end reply
# ---------------------------------------------------------------------------


def test_tick_replies_to_human_message(world):
    db = world["db"]
    db.record_chat_message(
        world["ip_uart"]["id"], world["alice"]["id"],
        "lock parity_en, drop optional",
        display_name="Alice",
    )

    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _mock_llm("Acknowledged. Will lock parity_en CSR bit."):
        n = r.tick()

    assert n == 1
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    # Newest-first: agent reply on top, then Alice's chat.
    assert rows[0]["actor_user_id"] == r.agent_uid
    assert rows[0]["payload"]["content"].startswith("Acknowledged.")
    assert rows[0]["payload"]["display_name"] == "🤖 ATLAS Helper"


def test_consumed_ledger_advances_after_reply(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _mock_llm("Got it."):
        r.tick()
    unread = db.list_chat_unconsumed_for(
        session_id=r.session_id, ip_id=r.ip_id,
    )
    # Alice's "hi" must have been consumed.
    assert all(m.get("payload", {}).get("content") != "hi" for m in unread)
    # The agent's own reply may sit in the unread queue (we don't
    # self-consume to keep the ledger interpretable), but the next-tick
    # self-filter in tick() removes it before any LLM call. Verify the
    # filter would do its job.
    after_filter = [m for m in unread
                    if (m.get("actor_user_id") or "") != r.agent_uid]
    assert after_filter == []


def test_second_tick_does_not_replay(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "msg-1")
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _mock_llm("reply-1"):
        r.tick()
    initial_count = len(db.list_chat_messages(world["ip_uart"]["id"]))
    with _mock_llm("reply-2"):
        r.tick()
    # No new chat → no new reply
    assert len(db.list_chat_messages(world["ip_uart"]["id"])) == initial_count


# ---------------------------------------------------------------------------
# Self-loop guard
# ---------------------------------------------------------------------------


def test_responder_does_not_reply_to_its_own_messages(world):
    db = world["db"]
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    # Simulate a prior agent reply (no human chat yet).
    db.record_chat_message(
        world["ip_uart"]["id"], r.agent_uid,
        "I was here", display_name="🤖 ATLAS Helper"
    )
    with _mock_llm("should not be called"):
        n = r.tick()
    # No unread human chat → zero consumed.
    assert n == 0
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    # Only the seeded agent message exists; no infinite loop reply.
    assert len(rows) == 1


# ---------------------------------------------------------------------------
# Throttle (cooldown)
# ---------------------------------------------------------------------------


def test_min_interval_throttles_back_to_back_replies(world):
    db = world["db"]
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=2.0)

    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "a")
    with _mock_llm("reply-a"):
        r.tick()
    assert any(
        m["payload"]["content"] == "reply-a"
        for m in db.list_chat_messages(world["ip_uart"]["id"])
    )

    # Immediately post another human chat — throttle should bounce it.
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "b")
    with _mock_llm("reply-b-blocked"):
        r.tick()
    contents = [m["payload"]["content"]
                for m in db.list_chat_messages(world["ip_uart"]["id"])]
    assert "reply-b-blocked" not in contents

    # b is still unconsumed (loop deliberately defers, not drops)
    pending = r.db.list_chat_unconsumed_for(
        session_id=r.session_id, ip_id=r.ip_id
    )
    assert any(m["payload"]["content"] == "b" for m in pending)


# ---------------------------------------------------------------------------
# Global room: cross-IP context
# ---------------------------------------------------------------------------


def test_global_room_replies_use_global_context(world):
    db = world["db"]
    db.record_chat_message(None, world["alice"]["id"], "which IPs are blocking?")
    r = cr.Responder("_global", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)

    captured: dict = {}
    def fake_stream(messages, stop=None, suppress_spinner=False, tools=None):
        captured["sys"] = messages[0]["content"]
        captured["user"] = messages[1]["content"]
        for ch in ["dma ", "and uart_lite ", "are running."]:
            yield ch

    with patch("llm_client.chat_completion_stream", new=fake_stream):
        n = r.tick()

    assert n == 1
    # System prompt should be the _global one
    assert "_global" in captured["sys"]
    # User block should include the orchestrator-context with both IPs
    assert "<orchestrator-context room='_global'>" in captured["user"]
    assert "uart_lite" in captured["user"]
    assert "dma" in captured["user"]
    assert "<team-chat-feedback room='_global'>" in captured["user"]

    # Reply landed in the _global room (ip_id is null)
    rows = db.list_chat_messages(None)
    assert any(m["actor_user_id"] == r.agent_uid for m in rows)


# ---------------------------------------------------------------------------
# Empty LLM reply still consumes (no infinite retry loop)
# ---------------------------------------------------------------------------


def test_empty_llm_reply_still_consumes_chat(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hello")
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _mock_llm(""):  # empty
        n = r.tick()
    assert n == 1
    unread = db.list_chat_unconsumed_for(session_id=r.session_id, ip_id=r.ip_id)
    assert unread == []


# ---------------------------------------------------------------------------
# Cost / actor accounting
# ---------------------------------------------------------------------------


def test_replies_carry_agent_actor_user_id_for_admin_tracking(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "cost?")
    r = cr.Responder("uart_lite", db=db, model="mock",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _mock_llm("Total cost so far is in the context bundle."):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot_replies = [m for m in rows if m["actor_user_id"] == r.agent_uid]
    assert len(bot_replies) == 1
    # Same role recorded on the user row
    assert db.get_user(r.agent_uid)["role"] == "agent"
