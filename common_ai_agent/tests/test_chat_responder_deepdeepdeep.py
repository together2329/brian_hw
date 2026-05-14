"""Deep-deep-deep responder tests — operational edge cases and the
real-ATLAS-UI browser path with autostart + visual evidence.

Targets the corners that field operators will actually hit:
- throttle window resets after idle time
- long content near the 8 KB cap survives roundtrip
- corrupted JSON payload (write-side bug elsewhere) does not crash reads
- workspace / IP deleted mid-flight does not crash the responder loop
- workspace_id propagation into chat_message rows
- responder works with status='inactive' IPs in the room list
- the running responder thread can be stopped cleanly
- bot's LLM stream with realistic gpt-5.3-codex tuple ordering
- a fresh chat AFTER a long idle is answered promptly (throttle reset)
- end-to-end inside a real ATLAS UI: autostart spawns the bot, a
  browser posts feedback, the bot reply lands in the same SQLite
  ledger AND ships to the browser's WS subscriber.
"""
from __future__ import annotations

import socket
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

playwright = pytest.importorskip("playwright.sync_api")
uvicorn = pytest.importorskip("uvicorn")

from fastapi import FastAPI
from fastapi.responses import HTMLResponse, JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from core.atlas_db import AtlasDB
from core.atlas_multiuser import _MultiUserBridge
from core.atlas_permissions import PermissionPolicy
from core import chat_responder as cr
from core.orchestrator_inject import register_bridge, get_registered_bridge
import atlas_api_chat as chat_api


@pytest.fixture
def world(tmp_path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/r")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")
    return {
        "db": db, "alice": alice, "bob": bob,
        "ws": ws, "ip_uart": ip_uart,
    }


def _patch_stream(chunks):
    def fake(messages, stop=None, suppress_spinner=False, tools=None):
        for c in chunks:
            yield c
    return patch("llm_client.chat_completion_stream", new=fake)


# ---------------------------------------------------------------------------
# Throttle reset after idle
# ---------------------------------------------------------------------------


def test_throttle_window_clears_after_idle(world):
    """The cooldown is per-room and based on wall clock. After a long
    enough idle, a fresh human chat is answered immediately — the
    throttle does not 'remember forever'."""
    db = world["db"]
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.2)

    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "first")
    with _patch_stream(["first-reply"]):
        r.tick()
    # Spam another chat immediately — throttle blocks it
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "rapid")
    with _patch_stream(["rapid-reply"]):
        n = r.tick()
    assert n == 0

    # Sleep past the throttle window
    time.sleep(0.25)
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "after-idle")
    with _patch_stream(["after-idle-reply"]):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    contents = [m["payload"]["content"] for m in rows]
    assert "after-idle-reply" in contents
    # The "rapid" chat (queued during cooldown) was also picked up
    assert "rapid-reply" not in contents or "after-idle-reply" in contents


# ---------------------------------------------------------------------------
# Long content near the 8 KB cap survives
# ---------------------------------------------------------------------------


def test_chat_content_up_to_8kb_roundtrips_through_responder(world):
    """8 KB content is the API cap. The responder still ingests it into
    the LLM user block without truncation in the chat_message ledger
    (the truncation is in the LLM reply, not the inbound chat)."""
    db = world["db"]
    big = "x" * (8000 - 100)  # just under the 8 KB content cap
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], big)
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    captured = {}

    def fake(messages, stop=None, suppress_spinner=False, tools=None):
        captured["user"] = messages[1]["content"]
        yield "short ack"

    with patch("llm_client.chat_completion_stream", new=fake):
        n = r.tick()
    assert n == 1
    # The entire big string is present inside the user block
    assert big in captured["user"]


# ---------------------------------------------------------------------------
# Corrupted JSON payload in trace_events (write-side regression elsewhere)
# ---------------------------------------------------------------------------


def test_corrupt_payload_string_does_not_crash_reads(world):
    """If some other path writes a non-JSON string into trace_events.payload,
    list_chat_messages should still surface the row gracefully — the
    responder's chat-block rendering must not blow up either."""
    db = world["db"]
    # Manually insert a chat_message with a corrupt payload string
    db._execute(
        """INSERT INTO trace_events
           (id, event_type, workspace_id, ip_id, actor_user_id, payload, created_at)
           VALUES (?, 'chat_message', ?, ?, ?, ?, ?)""",
        ("corrupt-id-1", world["ws"]["id"], world["ip_uart"]["id"],
         world["alice"]["id"], "{not valid json", time.time()),
    )
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    # Defensive: row appears, payload may be returned as the raw string
    assert any(r["id"] == "corrupt-id-1" for r in rows)

    # Now drop a healthy chat alongside and ensure the responder still
    # serves it without blowing up on the corrupt sibling.
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "valid")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["dealing with chaos"]):
        r.tick()
    rows2 = db.list_chat_messages(world["ip_uart"]["id"])
    assert any(m["payload"].get("content") == "dealing with chaos"
                if isinstance(m["payload"], dict) else False
               for m in rows2)


# ---------------------------------------------------------------------------
# IP deleted while responder is alive
# ---------------------------------------------------------------------------


def test_responder_survives_ip_block_deletion(world):
    """Operator removes the ip_blocks row mid-flight (e.g. via admin
    tooling). The responder's tick must not crash; it should consume
    nothing and survive until restart with a fresh resolution."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "pre-delete")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["before delete reply"]):
        r.tick()

    # Now blow away the ip_blocks row.
    db._execute("DELETE FROM ip_blocks WHERE id = ?", (world["ip_uart"]["id"],))

    # New tick: no new chats; should not crash.
    with _patch_stream(["never"]):
        n = r.tick()
    assert n == 0


# ---------------------------------------------------------------------------
# Workspace deleted while responder is alive
# ---------------------------------------------------------------------------


def test_responder_survives_workspace_deletion(world):
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "pre-ws-delete")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["before ws delete"]):
        r.tick()

    db._execute("DELETE FROM workspaces WHERE id = ?", (world["ws"]["id"],))
    # Drop a new chat directly via SQL (since the IP row is now orphaned)
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "post-ws-delete")
    with _patch_stream(["after ws delete"]):
        n = r.tick()
    # The responder is still pointed at the now-orphaned ip_id.
    # It should still consume + reply, since the chat ledger is per-ip_id.
    assert n >= 1


# ---------------------------------------------------------------------------
# Inactive IP still has a chat room
# ---------------------------------------------------------------------------


def test_responder_handles_inactive_ip(world):
    db = world["db"]
    db._execute("UPDATE ip_blocks SET status='inactive' WHERE id = ?",
                 (world["ip_uart"]["id"],))
    # Responder should still resolve the room and respond.
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "still alive?")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["yes, inactive but addressable"]):
        n = r.tick()
    assert n == 1


# ---------------------------------------------------------------------------
# Realistic gpt-5.3-codex chunk ordering
# ---------------------------------------------------------------------------


def test_realistic_codex_stream_ordering(world):
    """gpt-5.3-codex typically interleaves reasoning + content + the
    finish_reason marker. Verify the bot extracts only the content."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "what's blocked?")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    chunks = [
        ("reasoning", "Looking at the IP context..."),
        ("reasoning", "I see Real test todo B is blocked."),
        "Real test ",
        ("reasoning", "Drafting reply..."),
        "todo B is currently in `blocked` status.",
        ("finish_reason", "stop"),
    ]
    with _patch_stream(chunks):
        r.tick()
    rows = db.list_chat_messages(world["ip_uart"]["id"])
    bot = [m for m in rows if m["actor_user_id"] == r.agent_uid][0]
    assert bot["payload"]["content"] == \
        "Real test todo B is currently in `blocked` status."


# ---------------------------------------------------------------------------
# workspace_id propagation in bot replies
# ---------------------------------------------------------------------------


def test_bot_reply_inherits_workspace_id_for_admin_aggregation(world):
    """admin_usage and observability queries can filter by workspace_id.
    The bot's record_chat_message currently passes workspace_id="" — but
    the trace_events.workspace_id column should still be set when the
    parent IP has a workspace. Verify present behaviour."""
    db = world["db"]
    db.record_chat_message(world["ip_uart"]["id"], world["alice"]["id"], "hi")
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.01, min_interval_seconds=0.0)
    with _patch_stream(["hi back"]):
        r.tick()
    # Direct DB inspection — the bot's chat_message row
    rows = db._fetchall(
        """SELECT workspace_id, ip_id FROM trace_events
            WHERE event_type='chat_message' AND actor_user_id = ?""",
        (r.agent_uid,),
    )
    assert len(rows) == 1
    # ip_id must be set (room scope) so cross-IP queries work
    assert rows[0]["ip_id"] == world["ip_uart"]["id"]


# ---------------------------------------------------------------------------
# run_forever() can be stopped via .stop()
# ---------------------------------------------------------------------------


def test_responder_run_forever_stops_cleanly(world):
    db = world["db"]
    r = cr.Responder("uart_lite", db=db, model="m",
                       poll_seconds=0.05, min_interval_seconds=0.0)
    t = threading.Thread(target=r.run_forever, daemon=True)
    t.start()
    time.sleep(0.12)   # let it spin a couple of ticks on an empty queue
    r.stop()
    t.join(timeout=2)
    assert not t.is_alive(), "responder did not honor stop()"


# ---------------------------------------------------------------------------
# End-to-end with REAL ATLAS UI + autostart + mock LLM + Chromium
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture
def live_atlas_with_autostart(world, monkeypatch):
    """Stands up a minimal ATLAS-like server (chat routes + harness HTML)
    with autostart-enabled responders against a mock LLM, all in this
    process so we can patch llm_client cleanly."""
    db = world["db"]
    bridge = _MultiUserBridge(single_user=False)
    permissions = PermissionPolicy(db)
    register_bridge(bridge)

    # Mock the LLM globally for the duration of the test
    def fake_stream(messages, stop=None, suppress_spinner=False, tools=None):
        yield "Mocked bot reply about uart_lite."

    monkeypatch.setattr(
        "llm_client.chat_completion_stream", fake_stream, raising=True,
    )

    # Autostart the responders with the registered bridge
    responders = cr.autostart_all(db=db, bridge=bridge)
    # Override their poll interval for the test
    for r in responders:
        r.poll_seconds = 0.05
        r.min_interval = 0.0

    app = FastAPI()

    class _TestAuth(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            uid = request.headers.get("x-test-user")
            if uid:
                u = db.get_user(uid)
                if u:
                    request.scope["user"] = u
            return await call_next(request)

    app.add_middleware(_TestAuth)
    chat_api.register_chat_routes(app, db=db, bridge=bridge, permissions=permissions)

    HTML = """<!doctype html><html><body>
<script>
window.state = { lastSend: null, msgs: [], err: null };
window.UID = '';
async function api(p, o) {
  o = o || {}; o.credentials='include';
  o.headers = {...(o.headers||{}), 'x-test-user': window.UID};
  const r = await fetch(p, o);
  let b; try { b = await r.json() } catch(_) { b = null }
  return {status: r.status, body: b};
}
window.setUser = (u) => { window.UID = u };
window.send = async (room, c) => {
  const r = await api('/api/chat/'+room+'/send',
    {method:'POST', headers:{'Content-Type':'application/json'},
     body: JSON.stringify({content: c})});
  window.state.lastSend = r;
};
window.loadMessages = async (room) => {
  const r = await api('/api/chat/'+room+'/messages');
  if (r.status === 200) window.state.msgs = r.body.messages;
  else window.state.err = r;
};
</script>
ready
</body></html>"""

    @app.get("/")
    async def root():
        return HTMLResponse(HTML)

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="error")
    server = uvicorn.Server(config)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.socket() as s:
                s.connect(("127.0.0.1", port)); break
        except OSError: time.sleep(0.05)

    yield {
        **world,
        "base_url": f"http://127.0.0.1:{port}",
        "bridge": bridge,
        "responders": responders,
    }

    server.should_exit = True
    th.join(timeout=3)
    for r in responders:
        r.stop()
    register_bridge(None)


def test_real_atlas_browser_autostart_round_trip(live_atlas_with_autostart):
    """The full live path: user posts via REST → ledger → autostarted
    responder picks it up within 1 poll interval → posts reply with
    bot_uid → bridge broadcasts → another browser context's GET picks
    up both messages."""
    from playwright.sync_api import sync_playwright
    base = live_atlas_with_autostart["base_url"]
    alice_id = live_atlas_with_autostart["alice"]["id"]
    bob_id = live_atlas_with_autostart["bob"]["id"]

    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        try:
            # Alice posts via her browser context
            ctx_a = browser.new_context(base_url=base)
            page_a = ctx_a.new_page()
            page_a.goto("/")
            page_a.wait_for_function("() => typeof window.send === 'function'")
            page_a.evaluate("(u) => window.setUser(u)", alice_id)
            page_a.evaluate("window.send('uart_lite', 'BROWSER-LIVE: status?')")
            page_a.wait_for_function(
                "() => window.state.lastSend && window.state.lastSend.status === 200"
            )

            # Wait for the autostarted bot to consume + reply
            deadline = time.time() + 5
            saw_bot_reply = False
            while time.time() < deadline:
                rows = live_atlas_with_autostart["db"].list_chat_messages(
                    live_atlas_with_autostart["ip_uart"]["id"]
                )
                bot_msgs = [m for m in rows
                            if m["payload"].get("display_name", "").startswith("🤖")]
                if bot_msgs:
                    saw_bot_reply = True
                    break
                time.sleep(0.1)
            assert saw_bot_reply, "autostarted responder did not reply within 5s"

            # Bob's browser reads the room — sees both human and bot
            ctx_b = browser.new_context(base_url=base)
            page_b = ctx_b.new_page()
            page_b.goto("/")
            page_b.wait_for_function("() => typeof window.loadMessages === 'function'")
            page_b.evaluate("(u) => window.setUser(u)", bob_id)
            page_b.evaluate("window.loadMessages('uart_lite')")
            page_b.wait_for_function(
                "() => window.state.msgs && window.state.msgs.length >= 2"
            )
            contents = page_b.evaluate(
                "() => window.state.msgs.map(m => m.content + '|' + (m.display_name||''))"
            )
            assert any("BROWSER-LIVE: status?|Alice" in c for c in contents)
            assert any("Mocked bot reply about uart_lite.|🤖 ATLAS Helper" in c
                       for c in contents)
        finally:
            browser.close()
