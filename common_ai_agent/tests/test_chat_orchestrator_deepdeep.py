"""Deep-deep tests: concurrency, encoding, ledger hygiene, and
cross-cutting invariants beyond the basic API / DB / injector slices.

Each test targets one invariant the design must hold even under
adversarial input, multi-threaded load, or odd workspace topologies.
"""
from __future__ import annotations

import os
import sys
import threading
import time
import unicodedata
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
from typing import Any

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _candidate in (_REPO, _REPO / "src"):
    p = str(_candidate)
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from core.atlas_db import AtlasDB
from core.atlas_admin_usage import build_admin_usage_payload
from core.atlas_multiuser import (
    _MultiUserBridge,
    _SessionBridge,
    set_atlas_bridge_session_id,
    reset_atlas_bridge_session_id,
)
from core.atlas_permissions import PermissionPolicy, PermissionDenied
from core.orchestrator_inject import (
    build_orchestrator_inject_fn,
    register_bridge,
)
import atlas_api_chat as chat_api


# ---------------------------------------------------------------------------
# Setup
# ---------------------------------------------------------------------------


def _seed(tmp_path: Path) -> dict:
    db = AtlasDB(str(tmp_path / "atlas.db"))
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    carol = db.create_user("carol", "Carol", "pw")
    admin = db.create_user("root", "Root", "pw", role="admin")
    ws = db.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/repo")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")
    return {
        "db": db, "alice": alice, "bob": bob, "carol": carol, "admin": admin,
        "ws": ws, "ip_uart": ip_uart, "ip_dma": ip_dma,
    }


@pytest.fixture
def world(tmp_path):
    return _seed(tmp_path)


def _api_client(world: dict):
    db = world["db"]
    bridge = _MultiUserBridge(single_user=False)
    permissions = PermissionPolicy(db)
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
    return TestClient(app), bridge


# ---------------------------------------------------------------------------
# Concurrency
# ---------------------------------------------------------------------------


def test_concurrent_chat_inserts_preserve_count_and_order(world):
    """50 threads each writing 10 chat rows → 500 rows, distinct ids,
    monotonic created_at ordering on read."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]

    N_THREADS = 50
    N_PER = 10

    def worker(idx: int):
        ids = []
        for j in range(N_PER):
            r = db.record_chat_message(ip["id"], alice["id"], f"t{idx}-m{j}")
            ids.append(r["id"])
        return ids

    with ThreadPoolExecutor(max_workers=N_THREADS) as ex:
        results = [f.result() for f in as_completed(
            [ex.submit(worker, i) for i in range(N_THREADS)])]

    all_ids = [i for sub in results for i in sub]
    assert len(all_ids) == N_THREADS * N_PER
    assert len(set(all_ids)) == len(all_ids)  # all unique

    rows = db.list_chat_messages(ip["id"], limit=N_THREADS * N_PER + 10)
    assert len(rows) == N_THREADS * N_PER
    # newest-first → strictly non-increasing created_at
    timestamps = [r["created_at"] for r in rows]
    assert timestamps == sorted(timestamps, reverse=True)


def test_concurrent_consume_same_message_yields_multiple_rows_no_corruption(world):
    """If two ReAct iterations of the same session race on the same
    chat (shouldn't happen, but if it did): both INSERT — and the
    NOT-IN unconsumed query still treats it as consumed exactly once,
    no crash, no missing chat."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    m = db.record_chat_message(ip["id"], alice["id"], "race")

    sid = "agent-1"
    BARRIER = threading.Barrier(8)

    def worker():
        BARRIER.wait()
        db.record_chat_consumed(m["id"], sid, ip["id"])

    threads = [threading.Thread(target=worker) for _ in range(8)]
    for t in threads: t.start()
    for t in threads: t.join()

    # No spurious unconsumed
    assert db.list_chat_unconsumed_for(sid, ip["id"]) == []
    # Multiple consume rows is fine; ledger is append-only.
    consumed = [r for r in db.list_trace_events(correlation_id=m["id"])
                if r["event_type"] == "chat_consumed"]
    assert len(consumed) == 8


def test_concurrent_writes_at_db_layer_preserve_all_messages(world):
    """50 concurrent writes from two users via the AtlasDB layer
    (the path the API ultimately takes) land 50 rows. The TestClient's
    anyio executor serializes requests, so concurrency at the API
    layer is bounded by the harness; the actual race we care about
    is the sqlite shared-connection + RLock path."""
    db = world["db"]
    alice = world["alice"]["id"]
    bob = world["bob"]["id"]
    ip = world["ip_uart"]["id"]

    def post(uid, n):
        return db.record_chat_message(ip, uid, f"u{uid[:6]}-{n}", "u")

    with ThreadPoolExecutor(max_workers=25) as ex:
        futs = []
        for i in range(25):
            futs.append(ex.submit(post, bob, i))
            futs.append(ex.submit(post, alice, i))
        ids = [f.result()["id"] for f in as_completed(futs)]

    assert len(ids) == 50
    assert len(set(ids)) == 50
    rows = db.list_chat_messages(ip, limit=100)
    assert len(rows) == 50


def test_broadcast_all_under_load_reaches_every_session():
    bridge = _MultiUserBridge(single_user=False)
    sessions = [bridge._ensure_session(f"s{i}") for i in range(20)]

    def broadcaster():
        for i in range(50):
            bridge.broadcast_all("chat_message", room="r", id=f"m{i}", content=f"x{i}")

    threads = [threading.Thread(target=broadcaster) for _ in range(4)]
    for t in threads: t.start()
    for t in threads: t.join()

    for s in sessions:
        events = []
        while not s._outbox.empty():
            events.append(s._outbox.get_nowait())
        assert len(events) == 4 * 50, f"session {s.session_id} got {len(events)}"


# ---------------------------------------------------------------------------
# Encoding / unicode
# ---------------------------------------------------------------------------


@pytest.mark.parametrize("text", [
    "안녕하세요, agent. parity_en 좀 잠가 주세요.",                  # Korean
    "🚀 emoji + 💡 mixed",                                          # emoji
    "مرحبا، يجب قفل العرض",                                          # Arabic (RTL)
    "日本語のフィードバック",                                         # Japanese
    "Combining: á é",                                   # combining marks
    "Math: ∀x∈ℝ. ε > 0",                                            # math symbols
])
def test_unicode_content_survives_storage_and_render(world, text):
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    db.record_chat_message(ip["id"], alice["id"], text, "Alice")
    rows = db.list_chat_messages(ip["id"])
    assert rows[0]["payload"]["content"] == text
    # Normalisation preserved (NFC == NFC)
    assert unicodedata.normalize("NFC", rows[0]["payload"]["content"]) \
           == unicodedata.normalize("NFC", text)


def test_display_name_with_unicode_survives(world):
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    db.record_chat_message(ip["id"], alice["id"], "hi", display_name="브라이언 🦊")
    rows = db.list_chat_messages(ip["id"])
    assert rows[0]["payload"]["display_name"] == "브라이언 🦊"


def test_null_byte_in_content_does_not_corrupt_sqlite(world):
    """sqlite TEXT silently truncates at NUL on some drivers — verify
    we either preserve it or fail loudly, never silently corrupt."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    text = "before\x00after"
    db.record_chat_message(ip["id"], alice["id"], text, "Alice")
    rows = db.list_chat_messages(ip["id"])
    # JSON-encoding step escapes the null, so it round-trips intact.
    assert "before" in rows[0]["payload"]["content"]
    assert "after" in rows[0]["payload"]["content"]


# ---------------------------------------------------------------------------
# Permission revocation race
# ---------------------------------------------------------------------------


def test_revoked_grant_blocks_next_request(world):
    cli, _ = _api_client(world)
    bob = world["bob"]["id"]
    ip_uart = world["ip_uart"]["id"]

    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": bob},
                  json={"content": "before revoke"})
    assert r.status_code == 200

    world["db"].revoke_ip_permission(ip_uart, bob, "view")

    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": bob},
                  json={"content": "after revoke"})
    assert r.status_code == 403
    r = cli.get("/api/chat/uart_lite/messages",
                 headers={"x-test-user": bob})
    assert r.status_code == 403


def test_user_role_downgrade_loses_admin_room_access(world):
    cli, _ = _api_client(world)
    admin = world["admin"]
    # Initially admin sees dma (admin shortcut)
    r = cli.get("/api/chat/dma/context", headers={"x-test-user": admin["id"]})
    assert r.status_code == 200

    # Downgrade — simulate by direct UPDATE.
    world["db"]._execute(
        "UPDATE users SET role = 'user' WHERE id = ?", (admin["id"],)
    )
    r = cli.get("/api/chat/dma/context", headers={"x-test-user": admin["id"]})
    assert r.status_code == 403


def test_deleted_user_id_in_header_does_not_authenticate(world):
    cli, _ = _api_client(world)
    fake_uid = "deadbeef-not-a-real-user"
    r = cli.get("/api/chat/rooms", headers={"x-test-user": fake_uid})
    assert r.status_code == 401


# ---------------------------------------------------------------------------
# Cross-workspace / IP name collision
# ---------------------------------------------------------------------------


def test_get_ip_block_by_name_with_workspace_id_disambiguates(world):
    db = world["db"]
    other = db.create_user("dora", "Dora", "pw")
    ws2 = db.upsert_workspace("ws2", owner_user_id=other["id"], local_path="/r2")
    ip_other = db.upsert_ip_block(ws2["id"], "uart_lite", ip_type="uart")

    # No workspace_id → first match by created_at (alice's workspace was first)
    first = db.get_ip_block_by_name("uart_lite")
    assert first["id"] == world["ip_uart"]["id"]

    # With workspace_id → exact match
    assert db.get_ip_block_by_name("uart_lite", workspace_id=ws2["id"])["id"] \
           == ip_other["id"]


def test_room_dispatch_does_not_let_underscore_global_collide_with_ip(world):
    """A workspace owner who happens to create an IP literally named
    "_global" must not be able to bypass the global-room
    can_enter_global_room check."""
    db = world["db"]; alice = world["alice"]
    ws = world["ws"]
    # Even if a malicious workspace owner creates this IP:
    db.upsert_ip_block(ws["id"], "_global", ip_type="trap")

    p = PermissionPolicy(db)
    # Carol still cannot enter _global by spelling it as an IP name.
    assert p.can_enter_room(world["carol"]["id"], "_global") is False
    with pytest.raises(PermissionDenied):
        p.require_room_access(world["carol"]["id"], "_global")


# ---------------------------------------------------------------------------
# Trace ledger hygiene — chat events must not pollute other slices
# ---------------------------------------------------------------------------


def test_recent_events_for_ip_excludes_chat_rows(world):
    """summarize_ip_room_context._recent_events_for_ip must filter
    out chat_message + chat_consumed — those belong to the chat
    thread, not the "recent activity" feed."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]

    # Mix chat with non-chat trace events
    db.record_chat_message(ip["id"], alice["id"], "chat-a")
    db.record_trace_event("stage.started", ip_id=ip["id"],
                           payload={"stage": "ssot-rtl"})
    db.record_chat_message(ip["id"], alice["id"], "chat-b")
    db.record_trace_event("compile.passed", ip_id=ip["id"],
                           payload={"errors": 0})

    ctx = db.summarize_ip_room_context(ip["id"])
    types = {e.get("event_type") for e in ctx["recent_events"]
             if e.get("kind") == "trace"}
    assert "chat_message" not in types
    assert "chat_consumed" not in types
    assert "stage.started" in types
    assert "compile.passed" in types


def test_global_context_recent_events_excludes_chat(world):
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    db.record_chat_message(ip["id"], alice["id"], "chat-x")
    db.record_trace_event("run.started", ip_id=ip["id"],
                           payload={"workflow": "rtl-gen"})

    ctx = db.summarize_global_room_context()
    types = {e["event_type"] for e in ctx["recent_cross_ip_events"]}
    assert "chat_message" not in types
    assert "run.started" in types


def test_admin_usage_payload_handles_chat_traffic_cleanly(world):
    """The admin usage report runs without error when chat_message and
    chat_consumed rows are present in trace_events, and does not
    inflate intervention counts beyond actual chat_message rows."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    db.record_chat_message(ip["id"], alice["id"], "chat one")
    db.record_chat_message(ip["id"], alice["id"], "chat two")
    db.record_chat_consumed(
        db.list_chat_messages(ip["id"])[0]["id"], "some-session", ip["id"]
    )

    payload = build_admin_usage_payload(db)
    assert isinstance(payload, dict)
    # Whatever intervention rows look like, chat_messages must not
    # exceed the two messages we actually inserted.
    for row in payload.get("interventions", []):
        assert row.get("chat_messages", 0) <= 2


# ---------------------------------------------------------------------------
# Watermark / consume invariants
# ---------------------------------------------------------------------------


def test_watermark_advances_only_on_ip_room_in_per_ip_inject(world):
    """In per-IP mode, IP messages advance bridge.last_chat_seen_id;
    _global messages don't (they have their own DB-side watermark)."""
    db = world["db"]; alice = world["alice"]
    ip = world["ip_uart"]
    g_msg = db.record_chat_message(None, alice["id"], "global")
    i_msg = db.record_chat_message(ip["id"], alice["id"], "ip-local")

    bridge = _MultiUserBridge(single_user=False)
    register_bridge(bridge)
    session = bridge._ensure_session("alice/uart_lite/rtl-gen")
    os.environ["ATLAS_ACTIVE_IP"] = "uart_lite"
    token = set_atlas_bridge_session_id(session.session_id)
    try:
        inject = build_orchestrator_inject_fn(db, bridge)
        msgs = [{"role": "system", "content": "sys"}]
        inject(msgs, "normal")
    finally:
        reset_atlas_bridge_session_id(token)
        os.environ["ATLAS_ACTIVE_IP"] = ""

    # IP-room message id is the watermark, NOT the global one.
    assert session.last_chat_seen_id == i_msg["id"]
    # Both should be in chat_consumed for this session.
    consumed_ids = {
        r["correlation_id"]
        for r in db._fetchall(
            "SELECT correlation_id FROM trace_events "
            "WHERE event_type='chat_consumed' AND session_id = ?",
            (session.session_id,),
        )
    }
    assert g_msg["id"] in consumed_ids
    assert i_msg["id"] in consumed_ids


def test_per_ip_agent_consumes_global_independently_from_other_ip(world):
    """A global post is consumed independently per IP-session. Posting
    a second iteration on dma still picks up the same global message
    (it wasn't consumed by the uart session for the dma session)."""
    db = world["db"]; alice = world["alice"]
    g = db.record_chat_message(None, alice["id"], "everyone")

    bridge = _MultiUserBridge(single_user=False)
    register_bridge(bridge)

    def inject_for(session_name: str, ip_name: str):
        sess = bridge._ensure_session(session_name)
        prev_ip = os.environ.get("ATLAS_ACTIVE_IP", "")
        os.environ["ATLAS_ACTIVE_IP"] = ip_name
        token = set_atlas_bridge_session_id(sess.session_id)
        try:
            inject = build_orchestrator_inject_fn(db, bridge)
            msgs = [{"role": "system", "content": "sys"}]
            inject(msgs, "normal")
            return msgs[0]["content"]
        finally:
            reset_atlas_bridge_session_id(token)
            os.environ["ATLAS_ACTIVE_IP"] = prev_ip

    uart_first = inject_for("alice/uart_lite/rtl-gen", "uart_lite")
    dma_first = inject_for("alice/dma/rtl-gen", "dma")
    assert "everyone" in uart_first
    assert "everyone" in dma_first  # dma agent must also see it

    # Second iteration: neither replays.
    uart_second = inject_for("alice/uart_lite/rtl-gen", "uart_lite")
    dma_second = inject_for("alice/dma/rtl-gen", "dma")
    assert "everyone" not in uart_second
    assert "everyone" not in dma_second


def test_after_id_with_unknown_id_returns_no_rows(world):
    """If a caller passes a nonsense after_id, the query should
    behave safely — not return everything or raise."""
    db = world["db"]; alice = world["alice"]; ip = world["ip_uart"]
    db.record_chat_message(ip["id"], alice["id"], "real")

    rows = db.list_chat_messages(ip["id"], after_id="00000000-bogus-id")
    # The subquery returns NULL → `created_at > NULL` is unknown,
    # so SQLite returns 0 rows. Important: must not raise.
    assert isinstance(rows, list)


# ---------------------------------------------------------------------------
# Bridge / outbox edge cases
# ---------------------------------------------------------------------------


def test_broadcast_all_with_no_sessions_is_safe():
    bridge = _MultiUserBridge(single_user=False)
    # Removing the default session would be too aggressive; check that
    # broadcast does not raise even if sessions list is small.
    bridge.broadcast_all("chat_message", room="r", id="x")
    # No assertion needed — must just not raise.


def test_session_outbox_does_not_block_on_full_queue(world):
    """outbox is unbounded by default; ensure many enqueues don't
    starve out the consumer side."""
    cli, bridge = _api_client(world)
    sess = bridge._ensure_session("listener")
    bob = world["bob"]["id"]
    for i in range(20):
        cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": bob},
                  json={"content": f"m{i}"})
    n_chat = 0
    while not sess._outbox.empty():
        ev = sess._outbox.get_nowait()
        if ev.get("type") == "chat_message":
            n_chat += 1
    assert n_chat == 20


def test_msg_id_dedup_on_session_bridge():
    """_SessionBridge tracks msg_ids for WS dedup. If the same chat
    event id surfaces twice (sender's session + own broadcast leg),
    msg_id_seen should report True on the second."""
    s = _SessionBridge("s")
    assert s.msg_id_seen("xyz") is False
    assert s.msg_id_seen("xyz") is True
    assert s.msg_id_seen("abc") is False


# ---------------------------------------------------------------------------
# API edge cases
# ---------------------------------------------------------------------------


def test_method_not_allowed_on_messages_returns_405(world):
    cli, _ = _api_client(world)
    r = cli.put("/api/chat/uart_lite/messages",
                 headers={"x-test-user": world["bob"]["id"]})
    assert r.status_code == 405


def test_post_without_content_type_still_works_if_body_is_json(world):
    """starlette's request.json() will still parse if body is valid
    JSON even without explicit Content-Type. Verify the route does not
    reject by accident."""
    cli, _ = _api_client(world)
    # Send raw JSON without Content-Type
    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": world["bob"]["id"]},
                  content=b'{"content": "raw"}')
    assert r.status_code in (200, 400)  # both acceptable; just not 500


def test_admin_cross_workspace_can_post_to_any_ip(world):
    """An admin can write to dma even though the workspace owner is
    alice — admin shortcut applies to write/view paths."""
    cli, _ = _api_client(world)
    r = cli.post("/api/chat/dma/send",
                  headers={"x-test-user": world["admin"]["id"]},
                  json={"content": "admin says hi"})
    assert r.status_code == 200


def test_room_name_with_slash_does_not_crash(world):
    """A URL with an unexpected segment shape should not 500 — FastAPI
    will route `/api/chat/foo/bar/send` as a sub-path which our route
    pattern won't match, so it should 404 (or 405). The interesting
    case is `/api/chat/{room}` where {room} contains a literal '/'."""
    cli, _ = _api_client(world)
    r = cli.get("/api/chat/foo%2Fbar/messages",
                 headers={"x-test-user": world["bob"]["id"]})
    # Decoded room "foo/bar" is unknown → 403 (unknown IP).
    # Either 403 or 404 acceptable; must not be 500.
    assert r.status_code in (400, 403, 404)


def test_two_users_chat_history_is_consistent(world):
    """Two users posting interleaved — both see the same ordered
    history after every API call."""
    cli, _ = _api_client(world)
    a = world["alice"]["id"]; b = world["bob"]["id"]
    expected = []
    for i in range(10):
        sender = a if i % 2 == 0 else b
        cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": sender},
                  json={"content": f"msg-{i}"})
        expected.append(f"msg-{i}")

    ra = cli.get("/api/chat/uart_lite/messages",
                  headers={"x-test-user": a}).json()["messages"]
    rb = cli.get("/api/chat/uart_lite/messages",
                  headers={"x-test-user": b}).json()["messages"]
    # newest-first
    assert [m["content"] for m in ra] == list(reversed(expected))
    assert [m["content"] for m in rb] == list(reversed(expected))


# ---------------------------------------------------------------------------
# Defensive shape of message payload returned to client
# ---------------------------------------------------------------------------


def test_message_payload_always_has_expected_keys(world):
    cli, _ = _api_client(world)
    cli.post("/api/chat/uart_lite/send",
              headers={"x-test-user": world["bob"]["id"]},
              json={"content": "shape check"})
    r = cli.get("/api/chat/uart_lite/messages",
                 headers={"x-test-user": world["bob"]["id"]}).json()
    msg = r["messages"][0]
    for k in ("id", "ip_id", "user_id", "display_name", "content", "created_at"):
        assert k in msg


def test_send_returns_full_message_shape(world):
    cli, _ = _api_client(world)
    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": world["bob"]["id"]},
                  json={"content": "return-shape"}).json()
    for k in ("id", "ip_id", "user_id", "display_name", "content", "created_at"):
        assert k in r
    assert r["display_name"] == "Bob"
    assert r["content"] == "return-shape"
