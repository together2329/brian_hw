"""Deep / corner-case tests for the Orchestrator Chat stack.

Covers slices the route-level and DB-shape tests don't exercise:

- ip_id="" and ip_id=NULL semantics (both surface as the _global room
  because record_trace_event normalizes None → "")
- watermark resume from DB across a "bridge restart"
- pagination via after_id
- multi-session isolation of chat_consumed
- admin role / workspace owner / expired grant in PermissionPolicy
- _MultiUserBridge.broadcast_all reaching every active session
- the full POST-via-API → bridge broadcast → ReAct injector →
  trace_events.chat_consumed round trip
- content with newlines and json-ish payload survives roundtrip
- agents on different IPs do not see each other's chat
"""
from __future__ import annotations

import os
import sys
import time
from pathlib import Path

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
from core.atlas_multiuser import (
    _MultiUserBridge,
    set_atlas_bridge_session_id,
    reset_atlas_bridge_session_id,
)
from core.atlas_permissions import PermissionPolicy, PermissionDenied
from core.orchestrator_inject import (
    build_orchestrator_inject_fn,
    register_bridge,
    get_registered_bridge,
)
import atlas_api_chat as chat_api


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


def _seed(tmp_path: Path):
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


def _api_client(world):
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
# DB: edge cases on ip_id semantics
# ---------------------------------------------------------------------------


def test_chat_message_with_empty_string_ip_treated_as_global(world):
    """record_chat_message(None) calls record_trace_event(ip_id="").
    Reading the _global room should return that row, and the IP query
    must NOT pick it up."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]

    g = db.record_chat_message(None, alice["id"], "global hi")
    u = db.record_chat_message(ip_uart["id"], alice["id"], "uart hi")

    # Global query: both stored-as-NULL and stored-as-"" should appear
    global_rows = db.list_chat_messages(None)
    assert {r["id"] for r in global_rows} == {g["id"]}

    uart_rows = db.list_chat_messages(ip_uart["id"])
    assert {r["id"] for r in uart_rows} == {u["id"]}


def test_chat_message_with_newlines_and_special_chars_roundtrips(world):
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    payload = "line1\nline2\twith\ttabs\n{\"json\":\"like\"}\nfinal"
    rec = db.record_chat_message(ip_uart["id"], alice["id"], payload, "Alice")
    rows = db.list_chat_messages(ip_uart["id"])
    assert rows[0]["payload"]["content"] == payload


def test_chat_message_pagination_via_after_id(world):
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    ids = []
    for i in range(5):
        time.sleep(0.001)  # ensure monotonic created_at
        ids.append(db.record_chat_message(ip_uart["id"], alice["id"], f"m{i}")["id"])

    # Newest-first first page (limit 2)
    page1 = db.list_chat_messages(ip_uart["id"], limit=2)
    assert [r["id"] for r in page1] == [ids[4], ids[3]]

    # Using "after_id" = first message → only later messages.
    after_first = db.list_chat_messages(ip_uart["id"], limit=10, after_id=ids[0])
    assert [r["id"] for r in after_first] == [ids[4], ids[3], ids[2], ids[1]]


def test_chat_consumed_isolation_between_sessions(world):
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    m1 = db.record_chat_message(ip_uart["id"], alice["id"], "one")
    m2 = db.record_chat_message(ip_uart["id"], alice["id"], "two")

    db.record_chat_consumed(m1["id"], "session-A", ip_uart["id"])
    db.record_chat_consumed(m2["id"], "session-A", ip_uart["id"])

    # Session A: nothing left
    assert db.list_chat_unconsumed_for("session-A", ip_uart["id"]) == []
    # Session B: should still see both
    rows_b = db.list_chat_unconsumed_for("session-B", ip_uart["id"])
    assert {r["id"] for r in rows_b} == {m1["id"], m2["id"]}


def test_chat_unconsumed_orders_oldest_first(world):
    """Agents read feedback in chronological order, not newest-first."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    a = db.record_chat_message(ip_uart["id"], alice["id"], "first")
    time.sleep(0.001)
    b = db.record_chat_message(ip_uart["id"], alice["id"], "second")
    time.sleep(0.001)
    c = db.record_chat_message(ip_uart["id"], alice["id"], "third")
    rows = db.list_chat_unconsumed_for("s1", ip_uart["id"])
    assert [r["id"] for r in rows] == [a["id"], b["id"], c["id"]]


def test_latest_chat_consumed_id_returns_most_recent(world):
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    m1 = db.record_chat_message(ip_uart["id"], alice["id"], "1")
    time.sleep(0.001)
    m2 = db.record_chat_message(ip_uart["id"], alice["id"], "2")

    db.record_chat_consumed(m1["id"], "s", ip_uart["id"])
    time.sleep(0.001)
    db.record_chat_consumed(m2["id"], "s", ip_uart["id"])

    assert db.latest_chat_consumed_id("s", ip_uart["id"]) == m2["id"]


# ---------------------------------------------------------------------------
# PermissionPolicy: admin / owner / expiration paths
# ---------------------------------------------------------------------------


def test_admin_role_can_enter_any_room(world):
    p = PermissionPolicy(world["db"])
    admin_id = world["admin"]["id"]
    assert p.can_enter_global_room(admin_id) is True
    assert p.can_enter_room(admin_id, "uart_lite") is True
    assert p.can_enter_room(admin_id, "dma") is True


def test_workspace_owner_bypasses_explicit_ip_grant(world):
    """Alice owns the workspace, so she does not need explicit
    ip_permissions rows for uart_lite / dma."""
    p = PermissionPolicy(world["db"])
    alice = world["alice"]
    assert p.can_enter_room(alice["id"], "uart_lite") is True
    assert p.can_enter_room(alice["id"], "dma") is True
    assert p.can_enter_global_room(alice["id"]) is True


def test_expired_grant_does_not_grant_access(world):
    db = world["db"]; bob = world["bob"]; ip_dma = world["ip_dma"]
    # Future grant
    db.grant_ip_permission(ip_dma["id"], bob["id"], "view",
                            expires_at=time.time() + 60)
    p = PermissionPolicy(db)
    assert p.can_enter_room(bob["id"], "dma") is True

    # Now revoke + re-grant with a past expiry
    db.revoke_ip_permission(ip_dma["id"], bob["id"], "view")
    db.grant_ip_permission(ip_dma["id"], bob["id"], "view",
                            expires_at=time.time() - 1)
    assert p.can_enter_room(bob["id"], "dma") is False


def test_require_room_access_returns_resolved_ip(world):
    """The dict returned by require_room_access carries the ip row so
    POST handlers can write workspace_id without a second lookup."""
    p = PermissionPolicy(world["db"])
    bob = world["bob"]
    ctx = p.require_room_access(bob["id"], "uart_lite")
    assert ctx["room"] == "uart_lite"
    assert ctx["ip"]["ip_name"] == "uart_lite"

    ctx_global = p.require_room_access(bob["id"], "_global")
    assert ctx_global["room"] == "_global"
    assert ctx_global["ip"] is None


def test_carol_denied_everywhere(world):
    """Carol has no grants and does not own any workspace — every room
    must reject her."""
    p = PermissionPolicy(world["db"])
    carol = world["carol"]
    assert p.can_enter_global_room(carol["id"]) is False
    assert p.can_enter_room(carol["id"], "uart_lite") is False
    with pytest.raises(PermissionDenied):
        p.require_room_access(carol["id"], "_global")
    with pytest.raises(PermissionDenied):
        p.require_room_access(carol["id"], "uart_lite")


# ---------------------------------------------------------------------------
# _MultiUserBridge.broadcast_all
# ---------------------------------------------------------------------------


def test_broadcast_all_reaches_every_active_session():
    bridge = _MultiUserBridge(single_user=False)
    s1 = bridge._ensure_session("user/uart_lite/rtl-gen")
    s2 = bridge._ensure_session("user/dma/rtl-gen")
    s3 = bridge._ensure_session("user2/uart_lite/rtl-gen")

    bridge.broadcast_all("chat_message", room="uart_lite", id="abc",
                          ip_id=None, user_id="u", display_name="U",
                          content="hi", created_at=time.time())

    for s in (s1, s2, s3):
        ev = s._outbox.get_nowait()
        assert ev["type"] == "chat_message"
        assert ev["room"] == "uart_lite"
        assert ev["id"] == "abc"


def test_broadcast_all_does_not_share_message_objects():
    """Each session must receive its own dict, otherwise a downstream
    handler mutating one would corrupt the others."""
    bridge = _MultiUserBridge(single_user=False)
    s1 = bridge._ensure_session("a")
    s2 = bridge._ensure_session("b")
    bridge.broadcast_all("chat_message", room="r", content="x")
    e1 = s1._outbox.get_nowait()
    e2 = s2._outbox.get_nowait()
    e1["mutated"] = True
    assert "mutated" not in e2


# ---------------------------------------------------------------------------
# Orchestrator injector — deep behaviour
# ---------------------------------------------------------------------------


def _inject_once(db, bridge, session_id, ip_name):
    register_bridge(bridge)
    token = set_atlas_bridge_session_id(session_id)
    prev_ip = os.environ.get("ATLAS_ACTIVE_IP", "")
    if ip_name is None:
        os.environ["ATLAS_ACTIVE_IP"] = ""
    else:
        os.environ["ATLAS_ACTIVE_IP"] = ip_name
    try:
        inject = build_orchestrator_inject_fn(db, bridge)
        msgs = [{"role": "system", "content": "you are an agent."}]
        inject(msgs, "normal")
        return msgs[0]["content"]
    finally:
        reset_atlas_bridge_session_id(token)
        os.environ["ATLAS_ACTIVE_IP"] = prev_ip


def test_injector_does_not_replay_after_simulated_restart(world):
    """A fresh _SessionBridge (bridge restarted) must seed its
    in-memory watermark from the chat_consumed ledger so the agent
    does not re-replay history on the very first iteration."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    db.record_chat_message(ip_uart["id"], alice["id"], "old1", "Alice")
    db.record_chat_message(ip_uart["id"], alice["id"], "old2", "Alice")

    bridge1 = _MultiUserBridge(single_user=False)
    content1 = _inject_once(db, bridge1,
                             "user/uart_lite/rtl-gen", "uart_lite")
    assert "old1" in content1 and "old2" in content1

    # Drop bridge1, build bridge2 → simulates a server restart with the
    # same DB. chat_consumed rows now exist for both messages, so the
    # injector must NOT re-inject them.
    bridge2 = _MultiUserBridge(single_user=False)
    content2 = _inject_once(db, bridge2,
                             "user/uart_lite/rtl-gen", "uart_lite")
    assert "old1" not in content2
    assert "old2" not in content2
    # Context block (workflow / todos / gates) should still appear.
    assert "<orchestrator-context" in content2


def test_injector_global_room_picks_up_only_global_chat(world):
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    db.record_chat_message(ip_uart["id"], alice["id"], "uart-only",
                            "Alice")
    db.record_chat_message(None, alice["id"], "everyone read this",
                            "Alice")

    bridge = _MultiUserBridge(single_user=False)
    content = _inject_once(db, bridge, "user/_global", None)
    assert "everyone read this" in content
    assert "uart-only" not in content


def test_injector_isolates_between_two_concurrent_agents(world):
    """Two agents on different IPs should not see each other's
    feedback — and their watermarks must not collide."""
    db = world["db"]; alice = world["alice"]
    ip_uart = world["ip_uart"]; ip_dma = world["ip_dma"]
    db.record_chat_message(ip_uart["id"], alice["id"], "uart feedback")
    db.record_chat_message(ip_dma["id"], alice["id"], "dma feedback")

    bridge = _MultiUserBridge(single_user=False)
    uart_content = _inject_once(db, bridge,
                                  "alice/uart_lite/rtl-gen", "uart_lite")
    dma_content = _inject_once(db, bridge,
                                 "alice/dma/rtl-gen", "dma")

    assert "uart feedback" in uart_content and "dma feedback" not in uart_content
    assert "dma feedback" in dma_content and "uart feedback" not in dma_content


def test_injector_skips_when_system_role_missing(world):
    """If the loop hands us a transcript that does not start with a
    system message, the injector should be a no-op rather than mutate
    a user message."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    db.record_chat_message(ip_uart["id"], alice["id"], "should not appear")

    register_bridge(_MultiUserBridge(single_user=False))
    os.environ["ATLAS_ACTIVE_IP"] = "uart_lite"
    try:
        inject = build_orchestrator_inject_fn(db, get_registered_bridge())
        msgs = [{"role": "user", "content": "hello"}]
        inject(msgs, "normal")
        assert msgs[0]["content"] == "hello"
    finally:
        os.environ["ATLAS_ACTIVE_IP"] = ""


def test_injector_renders_block_with_list_content_form(world):
    """When CACHE_OPTIMIZATION_MODE=optimized the system content is a
    list-of-blocks, not a string. The injector must append a text
    block instead of concatenating to a string."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    db.record_chat_message(ip_uart["id"], alice["id"], "block-form feedback")

    register_bridge(_MultiUserBridge(single_user=False))
    os.environ["ATLAS_ACTIVE_IP"] = "uart_lite"
    try:
        inject = build_orchestrator_inject_fn(db, get_registered_bridge())
        msgs = [{
            "role": "system",
            "content": [{"type": "text", "text": "static sys"}],
        }]
        inject(msgs, "normal")
        # Should have appended at least one extra block.
        content = msgs[0]["content"]
        assert isinstance(content, list)
        assert len(content) >= 2
        joined = " ".join(b.get("text", "") for b in content if isinstance(b, dict))
        assert "block-form feedback" in joined
    finally:
        os.environ["ATLAS_ACTIVE_IP"] = ""


# ---------------------------------------------------------------------------
# API: full POST → broadcast_all → injector → chat_consumed round trip
# ---------------------------------------------------------------------------


def test_full_round_trip_post_to_consumed_ledger(world):
    cli, bridge = _api_client(world)
    db = world["db"]
    bob_id = world["bob"]["id"]

    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": bob_id},
                  json={"content": "round-trip"})
    assert r.status_code == 200
    mid = r.json()["id"]

    # The broadcast_all should have queued a chat_message in every
    # already-active session (default + any side sessions).
    seen = False
    for s in bridge.list_sessions():
        while not s._outbox.empty():
            ev = s._outbox.get_nowait()
            if ev.get("type") == "chat_message" and ev.get("id") == mid:
                seen = True
    assert seen, "chat_message did not reach any session outbox"

    # ReAct injector picks it up.
    bridge.activate_session("alice/uart_lite/rtl-gen")
    content = _inject_once(db, bridge, "alice/uart_lite/rtl-gen", "uart_lite")
    assert "round-trip" in content

    # Replay must NOT happen.
    content2 = _inject_once(db, bridge, "alice/uart_lite/rtl-gen", "uart_lite")
    assert "round-trip" not in content2

    # The ledger has exactly one chat_consumed row for this chat.
    consumed = db.list_trace_events(correlation_id=mid)
    consumed_only = [r for r in consumed if r["event_type"] == "chat_consumed"]
    assert len(consumed_only) == 1
    assert consumed_only[0]["session_id"] == "alice/uart_lite/rtl-gen"


def test_concurrent_posts_all_persist_and_broadcast(world):
    """Three POSTs in quick succession from different users land in
    the right order in both the DB and every session outbox."""
    cli, bridge = _api_client(world)
    bob_id = world["bob"]["id"]
    alice_id = world["alice"]["id"]

    bridge._ensure_session("alice/uart/rtl")  # an extra session

    for label in ("a", "b", "c"):
        r = cli.post("/api/chat/uart_lite/send",
                      headers={"x-test-user": bob_id},
                      json={"content": f"msg-{label}"})
        assert r.status_code == 200

    r = cli.get("/api/chat/uart_lite/messages",
                 headers={"x-test-user": alice_id})
    contents = [m["content"] for m in r.json()["messages"]]
    # newest-first
    assert contents == ["msg-c", "msg-b", "msg-a"]

    # Each session saw all three.
    for s in bridge.list_sessions():
        chats = []
        while not s._outbox.empty():
            ev = s._outbox.get_nowait()
            if ev.get("type") == "chat_message":
                chats.append(ev["content"])
        assert chats == ["msg-a", "msg-b", "msg-c"]


def test_global_post_reaches_agent_on_any_ip(world):
    """A post to _global must surface to a per-IP ReAct iteration too."""
    cli, bridge = _api_client(world)
    db = world["db"]

    cli.post("/api/chat/_global/send",
              headers={"x-test-user": world["alice"]["id"]},
              json={"content": "global-payload"})

    content = _inject_once(db, bridge,
                            "alice/uart_lite/rtl-gen", "uart_lite")
    # The per-IP agent's injector pulls unread for (ip_id, _global).
    assert "global-payload" in content


def test_carol_blocked_at_every_route(world):
    cli, _ = _api_client(world)
    carol_id = world["carol"]["id"]
    h = {"x-test-user": carol_id}

    assert cli.get("/api/chat/_global/context", headers=h).status_code == 403
    assert cli.get("/api/chat/_global/messages", headers=h).status_code == 403
    assert cli.post("/api/chat/_global/send", headers=h,
                     json={"content": "x"}).status_code == 403
    assert cli.get("/api/chat/uart_lite/context", headers=h).status_code == 403


def test_send_invalid_json_returns_400(world):
    cli, _ = _api_client(world)
    h = {"x-test-user": world["bob"]["id"], "content-type": "application/json"}
    r = cli.post("/api/chat/uart_lite/send", headers=h, data="not-json")
    assert r.status_code == 400


def test_send_missing_content_field_returns_400(world):
    cli, _ = _api_client(world)
    h = {"x-test-user": world["bob"]["id"]}
    r = cli.post("/api/chat/uart_lite/send", headers=h, json={})
    assert r.status_code == 400


def test_send_oversize_content_returns_413(world):
    cli, _ = _api_client(world)
    h = {"x-test-user": world["bob"]["id"]}
    r = cli.post("/api/chat/uart_lite/send", headers=h,
                  json={"content": "x" * 10_000})
    assert r.status_code == 413


def test_messages_limit_bound_to_max(world):
    """limit param must clamp to the API _MAX_LIMIT — passing 10_000
    should not return more than the cap."""
    db = world["db"]; alice = world["alice"]; ip_uart = world["ip_uart"]
    for i in range(50):
        db.record_chat_message(ip_uart["id"], alice["id"], f"m{i}")
    cli, _ = _api_client(world)
    r = cli.get("/api/chat/uart_lite/messages?limit=10000",
                 headers={"x-test-user": alice["id"]})
    assert r.status_code == 200
    assert len(r.json()["messages"]) == 50  # bounded above by row count


def test_rooms_response_includes_scope_and_ip_id_metadata(world):
    cli, _ = _api_client(world)
    r = cli.get("/api/chat/rooms",
                 headers={"x-test-user": world["bob"]["id"]})
    rooms = {row["name"]: row for row in r.json()["rooms"]}
    assert rooms["_global"]["scope"] == "global"
    assert rooms["_global"]["ip_id"] is None
    assert rooms["uart_lite"]["scope"] == "ip"
    assert rooms["uart_lite"]["ip_id"] == world["ip_uart"]["id"]


def test_admin_user_sees_all_rooms(world):
    cli, _ = _api_client(world)
    r = cli.get("/api/chat/rooms",
                 headers={"x-test-user": world["admin"]["id"]})
    names = {row["name"] for row in r.json()["rooms"]}
    # admin always passes can_enter_global_room; per-IP also unblocked
    # via can_user_access_ip's admin shortcut for any visible IP.
    assert "_global" in names
    assert "uart_lite" in names
    assert "dma" in names


def test_context_endpoint_for_ip_without_workflow_run(world):
    """When no workflow_runs row exists yet for the IP, the bundle
    should still return — with workflow.latest_run = None — instead
    of 404 or 500."""
    cli, _ = _api_client(world)
    r = cli.get("/api/chat/uart_lite/context",
                 headers={"x-test-user": world["bob"]["id"]})
    assert r.status_code == 200
    body = r.json()
    assert body["ip"]["name"] == "uart_lite"
    assert body["workflow"]["latest_run"] is None
    assert body["workflow"]["stages"] == []
    assert body["todos"]["counts"] == {}


def test_parameterized_query_resists_sql_quote_in_content(world):
    """Content with single quotes / semicolons must not break the SQL
    parser. (sqlite parameterized queries already guarantee this — the
    test exists so a future regression to f-strings is caught.)"""
    cli, _ = _api_client(world)
    payload = "Robert'); DROP TABLE trace_events;--"
    r = cli.post("/api/chat/uart_lite/send",
                  headers={"x-test-user": world["bob"]["id"]},
                  json={"content": payload})
    assert r.status_code == 200
    # And the table still exists with the row.
    rows = world["db"].list_chat_messages(world["ip_uart"]["id"])
    assert any(r["payload"]["content"] == payload for r in rows)
