"""
Single-user-mode auth + identity verification.

ATLAS_MULTI_USER=0 still requires login (guest auto-creation removed).
Tests confirm:
  - /healthz is public and reports user_session=null when unauthenticated,
    username when authenticated
  - Protected endpoints return 401 without a cookie
  - /ws/agent rejects unauthenticated connections (1008)
  - /ws/agent without a session_id defaults to the authenticated user's
    own namespace (= username)
  - The bridge is still _MultiUserBridge (architectural invariant)
"""
import os
import sys

os.environ["ATLAS_MULTI_USER"] = "0"
os.environ["ATLAS_MULTI_USER_PROC"] = "0"

sys.path.insert(0, '/Users/brian/Desktop/Project/brian_hw/common_ai_agent')

from fastapi.testclient import TestClient
from src.atlas_ui import create_app


def _register(client: TestClient, username: str, password: str = "pw"):
    r = client.post("/api/auth/register",
                    json={"username": username, "password": password})
    assert r.status_code == 200, f"register failed: {r.status_code} {r.text}"
    return r.json()["user"]


def test_healthz_anonymous():
    app = create_app()
    client = TestClient(app)
    r = client.get("/healthz")
    assert r.status_code == 200, f"/healthz should be public, got {r.status_code}"
    data = r.json()
    assert data["multi_user"] is False
    assert data["user_session"] is None, f"unauth user_session should be null: {data['user_session']}"
    print("PASS: /healthz anonymous → user_session=null")


def test_healthz_authenticated():
    app = create_app()
    client = TestClient(app)
    _register(client, "compat_a")
    r = client.get("/healthz")
    assert r.status_code == 200
    data = r.json()
    assert data["user_session"] == "compat_a", f"expected username, got {data['user_session']}"
    print("PASS: /healthz authenticated → user_session=<username>")


def test_protected_endpoint_requires_auth():
    app = create_app()
    client = TestClient(app)
    r = client.get("/api/users/me")
    assert r.status_code == 401, f"protected endpoint should 401, got {r.status_code}"
    print("PASS: /api/users/me unauth → 401")


def test_protected_endpoint_with_auth():
    app = create_app()
    client = TestClient(app)
    _register(client, "compat_b")
    r = client.get("/api/users/me")
    assert r.status_code == 200
    assert r.json()["user"]["username"] == "compat_b"
    print("PASS: /api/users/me with cookie → 200")


def test_ws_requires_auth():
    from starlette.websockets import WebSocketDisconnect
    app = create_app()
    client = TestClient(app)
    try:
        with client.websocket_connect("/ws/agent") as ws:
            ws.receive_json()
        raise AssertionError("WS without cookie should be rejected")
    except WebSocketDisconnect as e:
        assert e.code == 1008, f"expected 1008, got {e.code}"
        print("PASS: /ws/agent unauth → 1008")


def test_ws_with_auth_binds_to_user_namespace():
    app = create_app()
    client = TestClient(app)
    user = _register(client, "compat_c")
    with client.websocket_connect("/ws/agent") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        bridge = app.state.bridge
        assert bridge.get_session(user["username"]) is not None, \
            f"expected a session bound to '{user['username']}'"
        print(f"PASS: /ws/agent authenticated → session_id=user.username ({user['username']})")


def test_bridge_is_multiuser():
    app = create_app()
    bridge = app.state.bridge
    from core.atlas_multiuser import _MultiUserBridge
    assert isinstance(bridge, _MultiUserBridge)
    print("PASS: bridge is _MultiUserBridge")


if __name__ == "__main__":
    # Each test gets a fresh DB file so registrations don't collide.
    import pathlib, tempfile
    for fn in [
        test_healthz_anonymous,
        test_healthz_authenticated,
        test_protected_endpoint_requires_auth,
        test_protected_endpoint_with_auth,
        test_ws_requires_auth,
        test_ws_with_auth_binds_to_user_namespace,
        test_bridge_is_multiuser,
    ]:
        db = pathlib.Path.home() / ".common_ai_agent" / "atlas.db"
        if db.exists():
            db.unlink()
        fn()
    print("\nALL SINGLE-USER VERIFICATION TESTS PASSED")
