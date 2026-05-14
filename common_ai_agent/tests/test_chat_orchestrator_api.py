"""Route-level tests for the Orchestrator Chat API."""
from __future__ import annotations

import sys
from pathlib import Path

import pytest

# Make the src/ tree importable as `atlas_api_chat` (matches how
# atlas_ui mounts these modules in production).
_REPO = Path(__file__).resolve().parents[1]
for _candidate in (_REPO, _REPO / "src"):
    p = str(_candidate)
    if p not in sys.path:
        sys.path.insert(0, p)

from fastapi import FastAPI
from fastapi.testclient import TestClient
from starlette.middleware.base import BaseHTTPMiddleware

from core.atlas_db import AtlasDB
from core.atlas_multiuser import _MultiUserBridge
from core.atlas_permissions import PermissionPolicy
import atlas_api_chat as chat_api


def _build_client(tmp_path: Path):
    db = AtlasDB(str(tmp_path / "atlas.db"))
    bridge = _MultiUserBridge(single_user=True)
    permissions = PermissionPolicy(db)

    app = FastAPI()

    class _TestAuth(BaseHTTPMiddleware):
        async def dispatch(self, request, call_next):
            uid = request.headers.get("x-test-user")
            if uid:
                user = db.get_user(uid)
                if user:
                    request.scope["user"] = user
            return await call_next(request)

    app.add_middleware(_TestAuth)
    chat_api.register_chat_routes(app, db=db, bridge=bridge, permissions=permissions)
    return TestClient(app), db, bridge


@pytest.fixture
def fixtures(tmp_path):
    cli, db, bridge = _build_client(tmp_path)
    alice = db.create_user("alice", "Alice", "pw")
    bob = db.create_user("bob", "Bob", "pw")
    carol = db.create_user("carol", "Carol", "pw")
    ws = db.upsert_workspace("ws1", owner_user_id=alice["id"], local_path="/repo/ws1")
    ip_uart = db.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = db.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    db.grant_ip_permission(ip_uart["id"], bob["id"], "view")
    return {
        "cli": cli, "db": db, "bridge": bridge,
        "alice": alice, "bob": bob, "carol": carol,
        "ip_uart": ip_uart, "ip_dma": ip_dma,
    }


def _auth(uid):
    return {"x-test-user": uid}


def test_rooms_endpoint_requires_authentication(fixtures):
    r = fixtures["cli"].get("/api/chat/rooms")
    assert r.status_code == 401


def test_rooms_returns_only_permitted_rooms(fixtures):
    f = fixtures
    bob_rooms = {r["name"]
                 for r in f["cli"].get("/api/chat/rooms",
                                       headers=_auth(f["bob"]["id"])).json()["rooms"]}
    assert bob_rooms == {"_global", "uart_lite"}

    carol_rooms = f["cli"].get("/api/chat/rooms",
                                headers=_auth(f["carol"]["id"])).json()["rooms"]
    assert carol_rooms == []


def test_post_denied_for_user_without_view_grant(fixtures):
    f = fixtures
    r = f["cli"].post("/api/chat/uart_lite/send",
                       headers=_auth(f["carol"]["id"]),
                       json={"content": "no entry"})
    assert r.status_code == 403


def test_post_denied_on_unrelated_ip(fixtures):
    f = fixtures
    r = f["cli"].post("/api/chat/dma/send",
                       headers=_auth(f["bob"]["id"]),
                       json={"content": "wrong ip"})
    assert r.status_code == 403


def test_post_then_get_round_trip(fixtures):
    f = fixtures
    r = f["cli"].post("/api/chat/uart_lite/send",
                       headers=_auth(f["bob"]["id"]),
                       json={"content": "lock parity"})
    assert r.status_code == 200
    mid = r.json()["id"]

    r2 = f["cli"].get("/api/chat/uart_lite/messages",
                       headers=_auth(f["bob"]["id"]))
    assert r2.status_code == 200
    msgs = r2.json()["messages"]
    assert len(msgs) == 1
    assert msgs[0]["id"] == mid
    assert msgs[0]["content"] == "lock parity"
    assert msgs[0]["display_name"] == "Bob"


def test_post_broadcasts_through_bridge(fixtures):
    f = fixtures
    # Drain anything queued during setup.
    sess = f["bridge"]._ensure_session("default")
    while not sess._outbox.empty():
        sess._outbox.get_nowait()

    f["cli"].post("/api/chat/uart_lite/send",
                   headers=_auth(f["bob"]["id"]),
                   json={"content": "ping"})

    events = []
    while not sess._outbox.empty():
        events.append(sess._outbox.get_nowait())
    chats = [e for e in events if e.get("type") == "chat_message"]
    assert len(chats) == 1
    assert chats[0]["room"] == "uart_lite"
    assert chats[0]["content"] == "ping"


def test_empty_content_is_rejected(fixtures):
    f = fixtures
    r = f["cli"].post("/api/chat/uart_lite/send",
                       headers=_auth(f["bob"]["id"]),
                       json={"content": "   "})
    assert r.status_code == 400


def test_oversize_content_is_rejected(fixtures):
    f = fixtures
    r = f["cli"].post("/api/chat/uart_lite/send",
                       headers=_auth(f["bob"]["id"]),
                       json={"content": "x" * 9000})
    assert r.status_code == 413


def test_global_context_lists_workspace_ips(fixtures):
    f = fixtures
    r = f["cli"].get("/api/chat/_global/context",
                      headers=_auth(f["alice"]["id"]))
    assert r.status_code == 200
    names = {ip["name"] for ip in r.json()["ips"]}
    assert names == {"uart_lite", "dma"}


def test_ip_context_returns_workflow_block(fixtures):
    f = fixtures
    db = f["db"]
    db.start_workflow_run(
        workspace_id=f["ip_uart"]["workspace_id"],
        ip_id=f["ip_uart"]["id"],
        workflow="rtl-gen",
        mode="pipeline",
        status="running",
    )
    r = f["cli"].get("/api/chat/uart_lite/context",
                      headers=_auth(f["bob"]["id"]))
    assert r.status_code == 200
    body = r.json()
    assert body["ip"]["name"] == "uart_lite"
    assert body["workflow"]["latest_run"]["workflow"] == "rtl-gen"


def test_unknown_room_returns_403(fixtures):
    f = fixtures
    r = f["cli"].get("/api/chat/nonexistent_ip/messages",
                      headers=_auth(f["alice"]["id"]))
    assert r.status_code == 403
