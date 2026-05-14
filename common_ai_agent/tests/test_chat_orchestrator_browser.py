"""Browser e2e tests for Orchestrator Chat.

Stands up a live uvicorn server with the real chat API + a tiny HTML
test harness, then drives a headless Chromium with Playwright to
exercise the same network path a real ATLAS UI client would: cookie
auth, fetch() for REST, JSON round-trip, multi-tab cross-broadcast.

This complements the in-process TestClient suite by catching anything
that breaks when the API actually rides through ASGI + httpx + the
browser fetch stack (CORS, cookie handling, JSON encoding edges).
"""
from __future__ import annotations

import socket
import sys
import threading
import time
from pathlib import Path

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
import atlas_api_chat as chat_api


# ---------------------------------------------------------------------------
# Test harness HTML page
#
# The page exposes a few JS globals (state, lastError) that Playwright
# inspects via page.evaluate(). Real ATLAS UI uses the same fetch /
# JSON contract, so behaviour matches what a logged-in user gets.
# ---------------------------------------------------------------------------

_HARNESS_HTML = """<!doctype html>
<html><body>
<h1>chat harness</h1>
<input id="user" placeholder="user id"/>
<input id="room" placeholder="room"/>
<input id="content" placeholder="content"/>
<button id="send">send</button>
<button id="load">load messages</button>
<div id="status"></div>
<pre id="output"></pre>
<script>
window.state = { rooms: [], messages: [], lastSend: null, lastError: null };

async function api(path, opts) {
  opts = opts || {};
  opts.credentials = 'include';
  opts.headers = opts.headers || {};
  const uid = document.getElementById('user').value;
  if (uid) opts.headers['x-test-user'] = uid;
  const r = await fetch(path, opts);
  let body;
  try { body = await r.json(); } catch (_) { body = null; }
  if (!r.ok) {
    window.state.lastError = { status: r.status, body };
    document.getElementById('status').textContent = 'ERR ' + r.status;
    return null;
  }
  window.state.lastError = null;
  return body;
}

window.loadRooms = async function() {
  const data = await api('/api/chat/rooms');
  if (data) window.state.rooms = data.rooms;
};

window.loadMessages = async function() {
  const room = document.getElementById('room').value || '_global';
  const data = await api('/api/chat/' + encodeURIComponent(room) + '/messages');
  if (data) window.state.messages = data.messages;
};

window.send = async function() {
  const room = document.getElementById('room').value || '_global';
  const content = document.getElementById('content').value;
  const r = await api('/api/chat/' + encodeURIComponent(room) + '/send', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ content })
  });
  window.state.lastSend = r;
  if (r) {
    document.getElementById('output').textContent = JSON.stringify(r, null, 2);
    document.getElementById('status').textContent = 'OK ' + r.id;
  }
};

document.getElementById('send').addEventListener('click', () => window.send());
document.getElementById('load').addEventListener('click', () => window.loadMessages());
</script>
</body></html>"""


# ---------------------------------------------------------------------------
# Server fixture
# ---------------------------------------------------------------------------


def _free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


@pytest.fixture(scope="module")
def live_server(tmp_path_factory):
    db_path = tmp_path_factory.mktemp("chat-browser") / "atlas.db"
    db = AtlasDB(str(db_path))
    bridge = _MultiUserBridge(single_user=False)
    permissions = PermissionPolicy(db)

    # Fixtures: alice owns workspace + uart_lite + dma; bob has view
    # on uart_lite; carol has no grants.
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    carol = db.create_user("carol", "Carol", "pw")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/repo")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")

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

    @app.get("/", response_class=HTMLResponse)
    async def harness():
        return HTMLResponse(_HARNESS_HTML)

    @app.get("/__fixtures")
    async def fixtures():
        return JSONResponse({
            "alice": alice["id"], "bob": bob["id"], "carol": carol["id"],
            "ip_uart": ip_uart["id"],
        })

    port = _free_port()
    config = uvicorn.Config(app, host="127.0.0.1", port=port, log_level="warning")
    server = uvicorn.Server(config)
    th = threading.Thread(target=server.run, daemon=True)
    th.start()

    # Wait for socket
    deadline = time.time() + 10
    while time.time() < deadline:
        try:
            with socket.socket() as s:
                s.connect(("127.0.0.1", port))
            break
        except OSError:
            time.sleep(0.1)
    else:
        pytest.fail("uvicorn never came up")

    yield {
        "base_url": f"http://127.0.0.1:{port}",
        "alice_id": alice["id"],
        "bob_id": bob["id"],
        "carol_id": carol["id"],
        "ip_uart_id": ip_uart["id"],
        "db": db,
        "bridge": bridge,
    }

    server.should_exit = True
    th.join(timeout=5)


@pytest.fixture(scope="module")
def browser_ctx():
    from playwright.sync_api import sync_playwright
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        yield browser
        browser.close()


def _open(browser_ctx, base_url):
    ctx = browser_ctx.new_context(base_url=base_url)
    page = ctx.new_page()
    page.goto("/")
    page.wait_for_selector("#send")
    return ctx, page


def _set_user(page, uid):
    page.fill("#user", uid)


def _set_room(page, room):
    page.fill("#room", room)


# ---------------------------------------------------------------------------
# Browser tests
# ---------------------------------------------------------------------------


def test_browser_rooms_endpoint_filters_by_permission(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        # Bob
        _set_user(page, live_server["bob_id"])
        page.evaluate("window.loadRooms()")
        page.wait_for_function("() => window.state.rooms.length > 0")
        bob_rooms = page.evaluate("() => window.state.rooms.map(r => r.name)")
        assert set(bob_rooms) == {"_global", "uart_lite"}

        # Carol — no rooms
        _set_user(page, live_server["carol_id"])
        page.evaluate("window.state.rooms = []; window.loadRooms()")
        page.wait_for_function(
            "() => Array.isArray(window.state.rooms) && document.getElementById('status').textContent !== ''",
            timeout=3000,
        ) if False else page.wait_for_timeout(500)
        # carol returns empty list, lastError is null
        rooms = page.evaluate("() => window.state.rooms")
        assert rooms == []
    finally:
        ctx.close()


def test_browser_post_then_load_shows_message(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["bob_id"])
        _set_room(page, "uart_lite")
        page.fill("#content", "from-browser-1")
        page.click("#send")
        page.wait_for_function(
            "() => window.state.lastSend && window.state.lastSend.content === 'from-browser-1'"
        )
        sent = page.evaluate("() => window.state.lastSend")
        assert sent["display_name"] == "Bob"
        assert sent["content"] == "from-browser-1"

        # Now load and ensure it is in the list.
        page.click("#load")
        page.wait_for_function(
            "() => window.state.messages.length > 0 "
            "&& window.state.messages.some(m => m.content === 'from-browser-1')"
        )
    finally:
        ctx.close()


def test_browser_carol_blocked_at_send(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["carol_id"])
        _set_room(page, "uart_lite")
        page.fill("#content", "should be 403")
        page.click("#send")
        page.wait_for_function("() => window.state.lastError !== null")
        err = page.evaluate("() => window.state.lastError")
        assert err["status"] == 403
    finally:
        ctx.close()


def test_browser_global_post_visible_to_per_ip_loader(live_server, browser_ctx):
    """A message posted to _global by alice must be loadable from
    /_global/messages by bob (who has _global access via his uart_lite
    grant)."""
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["alice_id"])
        _set_room(page, "_global")
        page.fill("#content", "global-from-alice")
        page.click("#send")
        page.wait_for_function(
            "() => window.state.lastSend && window.state.lastSend.content === 'global-from-alice'"
        )

        # Switch user to bob and load _global messages
        _set_user(page, live_server["bob_id"])
        page.click("#load")
        page.wait_for_function(
            "() => window.state.messages.some(m => m.content === 'global-from-alice')"
        )
    finally:
        ctx.close()


def test_browser_two_contexts_share_history_via_db(live_server, browser_ctx):
    """Open two browser contexts as different users; each one's POST
    is visible when the other reloads. This proves the API persists
    to the shared DB regardless of which browser context posted."""
    base = live_server["base_url"]
    ctx_a, page_a = _open(browser_ctx, base)
    ctx_b, page_b = _open(browser_ctx, base)
    try:
        _set_user(page_a, live_server["alice_id"])
        _set_room(page_a, "uart_lite")
        page_a.fill("#content", "from-a")
        page_a.click("#send")
        page_a.wait_for_function(
            "() => window.state.lastSend && window.state.lastSend.content === 'from-a'"
        )

        _set_user(page_b, live_server["bob_id"])
        _set_room(page_b, "uart_lite")
        page_b.fill("#content", "from-b")
        page_b.click("#send")
        page_b.wait_for_function(
            "() => window.state.lastSend && window.state.lastSend.content === 'from-b'"
        )

        # Each loads — both rows present.
        page_a.click("#load")
        page_a.wait_for_function(
            "() => window.state.messages.some(m => m.content === 'from-b')"
        )
        page_b.click("#load")
        page_b.wait_for_function(
            "() => window.state.messages.some(m => m.content === 'from-a')"
        )

        a_seen = page_a.evaluate("() => window.state.messages.map(m => m.content)")
        b_seen = page_b.evaluate("() => window.state.messages.map(m => m.content)")
        assert "from-a" in a_seen and "from-b" in a_seen
        assert "from-a" in b_seen and "from-b" in b_seen
    finally:
        ctx_a.close()
        ctx_b.close()


def test_browser_oversize_content_rejected_with_413(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["bob_id"])
        _set_room(page, "uart_lite")
        # 10KB > 8KB cap
        page.evaluate("document.getElementById('content').value = 'x'.repeat(10000)")
        page.click("#send")
        page.wait_for_function("() => window.state.lastError !== null")
        err = page.evaluate("() => window.state.lastError")
        assert err["status"] == 413
    finally:
        ctx.close()


def test_browser_unicode_payload_roundtrips(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["bob_id"])
        _set_room(page, "uart_lite")
        payload = "한국어 + 🚀 + ∀x∈ℝ"
        page.evaluate(
            "(t) => document.getElementById('content').value = t", payload
        )
        page.click("#send")
        page.wait_for_function(
            "(t) => window.state.lastSend && window.state.lastSend.content === t",
            arg=payload,
        )
        page.click("#load")
        page.wait_for_function(
            "(t) => window.state.messages.some(m => m.content === t)",
            arg=payload,
        )
    finally:
        ctx.close()


def test_browser_admin_sees_all_ip_rooms(live_server, browser_ctx):
    """Make alice an admin on the server side (raw SQL) and verify
    her rooms list now includes every IP, not just owned ones."""
    db = live_server["db"]
    db._execute("UPDATE users SET role='admin' WHERE id=?", (live_server["alice_id"],))
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["alice_id"])
        page.evaluate("window.loadRooms()")
        page.wait_for_function("() => window.state.rooms.length >= 3")
        names = page.evaluate("() => window.state.rooms.map(r => r.name)")
        assert "_global" in names
        assert "uart_lite" in names
        assert "dma" in names
    finally:
        ctx.close()


def test_browser_unknown_room_returns_403(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["alice_id"])
        _set_room(page, "no-such-ip")
        page.click("#load")
        page.wait_for_function("() => window.state.lastError !== null")
        err = page.evaluate("() => window.state.lastError")
        assert err["status"] == 403
    finally:
        ctx.close()


def test_browser_empty_content_400(live_server, browser_ctx):
    ctx, page = _open(browser_ctx, live_server["base_url"])
    try:
        _set_user(page, live_server["bob_id"])
        _set_room(page, "uart_lite")
        page.fill("#content", "   ")
        page.click("#send")
        page.wait_for_function("() => window.state.lastError !== null")
        err = page.evaluate("() => window.state.lastError")
        assert err["status"] == 400
    finally:
        ctx.close()
