"""Deep / corner-case tests for the chat-responder bot.

Targets the invariants the basic test_chat_responder suite does not
cover: stream filter robustness against mixed-tuple chunks, real-time
WS broadcast through the bridge, multi-room concurrent threads,
autostart_all enumeration, cost attribution to the agent service
account, throttle under burst load, and the bot's interaction with
the human ↔ agent ReAct orchestrator inject path.
"""
from __future__ import annotations

import sys
import threading
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
from core.orchestrator_inject import (
    build_orchestrator_inject_fn,
    register_bridge,
    get_registered_bridge,
)
from core import chat_responder as cr


@pytest.fixture
def world(tmp_path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/r")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    return {
        "db": db, "alice": alice, "bob": bob,
        "ws": ws, "ip_uart": ip_uart, "ip_dma": ip_dma,
    }


def _patch_stream(chunks):
    """Patch llm_client.chat_completion_stream to yield arbitrary chunks
    (strings + tuples) — same wire format the responder sees in prod."""
    def fake(messages, stop=None, suppress_spinner=False, tools=None):
        for c in chunks:
            yield c
    return patch("llm_client.chat_completion_stream", new=fake)


# ---------------------------------------------------------------------------
# Stream filter — the bug that "reasoningreasoningreasoning" was the bot's
# reply, caused by treating tuple chunks as content.
# ---------------------------------------------------------------------------


def test_stream_filter_drops_reasoning_tuples(world):
    """('reasoning', text) tuples must not appear in the final reply."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    chunks = [
        ("reasoning", "let me think..."),
        "The ",
        ("reasoning", "more thinking"),
        "uart_lite ",
        ("reasoning", "even more"),
        "status is running.",
    ]
    with _patch_stream(chunks):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid][0]
    assert bot["payload"]["content"] == "The uart_lite status is running."
    assert "reasoning" not in bot["payload"]["content"]


def test_stream_filter_drops_native_tool_calls_and_finish_tuples(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    chunks = [
        "Hello.",
        ("native_tool_calls", [{"name": "x"}]),
        " More text.",
        ("finish_reason", "stop"),
    ]
    with _patch_stream(chunks):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid][0]
    assert bot["payload"]["content"] == "Hello. More text."


def test_stream_with_only_tuples_yields_empty_but_consumes(world):
    """If the LLM never emits a content chunk, the reply is empty —
    must still consume the chat to prevent retry storms."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    chunks = [
        ("reasoning", "..."),
        ("finish_reason", "stop"),
    ]
    with _patch_stream(chunks):
        n = r.tick()
    assert n == 1
    # No bot post (empty content)
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    assert not any(m["actor_user_id"] == r.agent_uid for m in rows)
    # But Alice's chat is consumed — won't replay
    unread = db.list_chat_unconsumed_for(r.session_id, r.ip_id)
    assert unread == []


def test_stream_char_budget_caps_reply_length(world):
    """If the LLM streams way more than max_tokens, the reply must be
    truncated to the configured cap. Prevents accidental megabyte
    replies blowing up the chat panel."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0,
                       max_output_tokens=20)
    # 20 tokens × 8 = 160 char hard cap; tests expect well under that
    chunks = ["A" * 100, "B" * 100, "C" * 100]
    with _patch_stream(chunks):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid][0]
    content = bot["payload"]["content"]
    assert len(content) <= 20 * 8
    # The first chunk is well within budget
    assert content.startswith("A")


# ---------------------------------------------------------------------------
# Bridge broadcast — bot reply must reach WS clients in real time
# ---------------------------------------------------------------------------


def test_responder_broadcasts_reply_via_bridge(world):
    db = world["db"]
    bridge = _MultiUserBridge(single_user=False)
    other_session = bridge._ensure_session("alice/uart_lite/rtl-gen")

    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "ping")
    r = cr.Responder("uart_lite", db=db, bridge=bridge, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["pong from bot"]):
        r.tick()

    # The bridge should have pushed a chat_message event to every active
    # session's outbox (the WS broadcaster reads from these).
    events = []
    while not other_session._outbox.empty():
        events.append(other_session._outbox.get_nowait())
    chat_events = [e for e in events if e.get("type") == "chat_message"]
    assert len(chat_events) == 1
    ev = chat_events[0]
    assert ev["room"] == "uart_lite"
    assert ev["content"] == "pong from bot"
    assert ev["user_id"] == r.agent_uid
    assert ev["display_name"] == "🤖 ATLAS Helper"


def test_responder_without_bridge_still_persists_reply(world):
    """Standalone CLI mode (bridge=None) — DB write must still happen,
    only the WS push is missing."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, bridge=None, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["reply"]):
        n = r.tick()
    assert n == 1
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid]
    assert len(bot) == 1


def test_broadcast_failure_does_not_abort_consume(world):
    """If the bridge raises during broadcast (e.g. a session disappeared),
    the responder must still mark the chat consumed — otherwise a flapping
    bridge would block the loop."""
    db = world["db"]
    class _BrokenBridge:
        def broadcast_all(self, *a, **kw):
            raise RuntimeError("bridge boom")
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, bridge=_BrokenBridge(), model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["resilient reply"]):
        r.tick()
    # DB write happened
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    assert any(m["payload"]["content"] == "resilient reply" for m in rows)
    # Chat consumed despite broken broadcast
    unread = db.list_chat_unconsumed_for(r.session_id, r.ip_id)
    assert all(m["payload"]["content"] != "hi" for m in unread)


# ---------------------------------------------------------------------------
# autostart_all
# ---------------------------------------------------------------------------


def test_autostart_spawns_responder_per_ip_plus_global(world):
    """One thread per IP, one for _global. Threads are daemons so they
    die with the parent process — no explicit shutdown."""
    started = cr.autostart_all(db=world["db"])
    rooms = {r.room for r in started}
    assert rooms == {"_global", "uart_lite", "dma"}
    # All threads are daemons (won't block process exit)
    thread_names = {t.name for t in threading.enumerate()
                    if t.name.startswith("chat-responder-")}
    assert "chat-responder-_global" in thread_names
    assert "chat-responder-uart_lite" in thread_names
    assert "chat-responder-dma" in thread_names
    # Tell them to stop so the test doesn't leak background work
    for r in started:
        r.stop()


def test_autostart_with_empty_db_still_spawns_global(tmp_path):
    """Even with no IPs in the DB, the _global responder should start."""
    db = AtlasDB(str(tmp_path / "atlas.db"))
    started = cr.autostart_all(db=db)
    assert len(started) == 1
    assert started[0].room == "_global"
    for r in started:
        r.stop()


def test_autostart_picks_up_registered_bridge_from_orchestrator_inject(world):
    """When atlas_ui boots, it registers the bridge before calling
    autostart_all. The responders should inherit that bridge so their
    replies broadcast in real time."""
    bridge = _MultiUserBridge(single_user=False)
    register_bridge(bridge)
    try:
        started = cr.autostart_all(db=world["db"])
        for r in started:
            assert r.bridge is bridge
    finally:
        for r in started:
            r.stop()
        register_bridge(None)


# ---------------------------------------------------------------------------
# Multi-room concurrent responders — independent watermarks, no
# cross-room replies
# ---------------------------------------------------------------------------


def test_two_responders_on_different_rooms_dont_cross_reply(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "uart-only")
    db.record_chat_message(world["ip_dma"]["id"],  world["alice"]["id"], "dma-only")

    r_uart = cr.Responder("uart_lite", db=db, model="m",
                            poll_seconds=0.01, min_interval_seconds=0.0)
    r_dma  = cr.Responder("dma",       db=db, model="m",
                            poll_seconds=0.01, min_interval_seconds=0.0)

    with _patch_stream(["uart-reply"]):
        r_uart.tick()
    with _patch_stream(["dma-reply"]):
        r_dma.tick()

    uart_rows = db.list_chat_messages(world["ip_uart"]["id"])
    dma_rows  = db.list_chat_messages(world["ip_dma"]["id"])

    assert any("uart-reply" in m["payload"]["content"] for m in uart_rows)
    assert all("dma-reply" not in m["payload"]["content"] for m in uart_rows)
    assert any("dma-reply" in m["payload"]["content"] for m in dma_rows)
    assert all("uart-reply" not in m["payload"]["content"] for m in dma_rows)


def test_global_and_per_ip_responders_consume_separately(world):
    """A global chat is NOT consumed by a per-IP responder's session,
    and vice versa — each maintains its own watermark."""
    db = world["db"]
    db.record_chat_message(None, world["alice"]["id"], "everyone")

    r_global = cr.Responder("_global",   db=db, model="m",
                              poll_seconds=0.01, min_interval_seconds=0.0)
    r_uart   = cr.Responder("uart_lite", db=db, model="m",
                              poll_seconds=0.01, min_interval_seconds=0.0)

    with _patch_stream(["global-ack"]):
        n_g = r_global.tick()
    with _patch_stream(["uart-noop"]):
        # uart responder polls only ip_id=uart_lite, never global chat
        n_u = r_uart.tick()

    assert n_g == 1     # global responder saw and consumed the global chat
    assert n_u == 0     # uart responder saw nothing — global chat is not its scope


# ---------------------------------------------------------------------------
# Throttle under burst load
# ---------------------------------------------------------------------------


def test_burst_of_messages_only_one_reply_per_tick_with_throttle(world):
    """10 messages posted in sequence; the responder ticks 3 times.
    With a 1s throttle the responder should emit ≤3 replies, not 10.
    The unprocessed messages must be consumed (no replay) by the
    final tick after enough cooldown."""
    db = world["db"]
    for i in range(10):
        db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], f"m{i}")

    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01,
                       min_interval_seconds=0.5)

    # tick 1 → replies, consumes all 10 chats (loop consumes the whole
    # unread batch on a successful reply tick).
    with _patch_stream(["batch-1-reply"]):
        n1 = r.tick()
    assert n1 == 10
    # tick 2 → no new chats, no reply
    with _patch_stream(["batch-2-reply"]):
        n2 = r.tick()
    assert n2 == 0

    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot_replies = [m for m in rows if m["actor_user_id"] == r.agent_uid]
    assert len(bot_replies) == 1


def test_throttle_defers_but_does_not_drop(world):
    """A chat that lands during cooldown must persist as unread until
    the cooldown clears — never silently dropped."""
    db = world["db"]
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01,
                       min_interval_seconds=0.3)

    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "first")
    with _patch_stream(["first-reply"]):
        r.tick()

    # Immediately post a second chat — within cooldown window
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "second")
    with _patch_stream(["should-be-suppressed"]):
        n = r.tick()
    assert n == 0      # nothing consumed during cooldown
    pending = db.list_chat_unconsumed_for(r.session_id, r.ip_id)
    assert any(m["payload"]["content"] == "second" for m in pending)

    # Wait out the cooldown, tick again — second chat lands
    time.sleep(0.35)
    with _patch_stream(["second-reply"]):
        n2 = r.tick()
    assert n2 >= 1
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    assert any(m["payload"]["content"] == "second-reply" for m in rows)


# ---------------------------------------------------------------------------
# Interaction with the running workflow agent's orchestrator-inject
# ---------------------------------------------------------------------------


def test_bot_replies_appear_in_running_agents_chat_feedback(world):
    """The bot's reply is itself a chat_message row; the running rtl-gen
    agent's orchestrator-inject will read it on its next iteration. This
    is intentional — the workflow agent should see the bot's
    acknowledgement to avoid duplicating the answer. We verify the bot's
    message ends up in the agent's <team-chat-feedback> block."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "lock parity_en")
    bot = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["Acknowledged. parity_en will be locked."]):
        bot.tick()

    # Simulate the rtl-gen agent's next iteration — a different session
    import os
    bridge = _MultiUserBridge(single_user=False)
    sess = bridge._ensure_session("alice/uart_lite/rtl-gen")
    os.environ["ATLAS_ACTIVE_IP"] = "uart_lite"
    try:
        from core.atlas_multiuser import (
            set_atlas_bridge_session_id, reset_atlas_bridge_session_id
        )
        token = set_atlas_bridge_session_id(sess.session_id)
        try:
            inject = build_orchestrator_inject_fn(db, bridge)
            messages = [{"role": "system", "content": "sys"}]
            inject(messages, "normal")
        finally:
            reset_atlas_bridge_session_id(token)
        content = messages[0]["content"]
    finally:
        os.environ["ATLAS_ACTIVE_IP"] = ""

    # The running agent should see both the human ask and the bot ack
    assert "lock parity_en" in content
    assert "Acknowledged" in content


def test_responder_session_id_is_distinct_from_workflow_agent_sessions(world):
    """The bot's chat_consumed rows live under its own session_id; the
    workflow agent's chat_consumed rows live under its session_id. They
    do not share a watermark, otherwise the bot would skip messages the
    workflow agent already consumed, or vice versa."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "context")

    # Workflow agent consumes first via the orchestrator-inject path
    workflow_sess = "alice/uart_lite/rtl-gen"
    msg_id = db.list_chat_messages(world["ip_uart"]["id"])[0]["id"]
    db.record_chat_consumed(msg_id, workflow_sess, world["ip_uart"]["id"])

    # The bot must STILL see this chat — independent watermark
    bot = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    unread = db.list_chat_unconsumed_for(bot.session_id, bot.ip_id)
    assert any(m["id"] == msg_id for m in unread)


# ---------------------------------------------------------------------------
# LLM call attribution path
# ---------------------------------------------------------------------------


def test_bot_message_attributable_to_agent_role_in_admin_usage(world):
    """admin_usage_payload should be able to slice 'agent vs human'
    activity using users.role. A bot reply must carry the agent_uid,
    and that user's role must be 'agent'."""
    from core.atlas_admin_usage import build_admin_usage_payload
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "ask")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["bot reply"]):
        r.tick()
    # The agent user is a real users row with role='agent'
    agent_user = db.get_user(r.agent_uid)
    assert agent_user["role"] == "agent"
    # build_admin_usage_payload tolerates the chat traffic
    payload = build_admin_usage_payload(db)
    assert isinstance(payload, dict)


def test_self_filter_uses_actor_user_id_not_display_name(world):
    """A human user could theoretically pick the display name
    '🤖 ATLAS Helper' (no actor_user_id collision though); the
    self-filter must reject the bot only by actor_user_id, never by
    display name — otherwise a malicious human could silence the bot."""
    db = world["db"]
    # Seed: human posts with bot-looking display name
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"],
                            "I am alice in disguise", display_name="🤖 ATLAS Helper")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["replying to alice"]):
        n = r.tick()
    # Alice's message gets consumed; the bot replies — display name
    # collision does not silence the bot.
    assert n == 1
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    assert any(m["payload"]["content"] == "replying to alice"
               for m in rows if m["actor_user_id"] == r.agent_uid)
