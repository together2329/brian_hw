import sys
sys.path.insert(0, '/Users/brian/Desktop/Project/brian_hw/common_ai_agent')

from fastapi.testclient import TestClient
from src.atlas_ui import create_app


def test_full_flow():
    app = create_app()
    client = TestClient(app)

    r = client.get("/healthz")
    assert r.status_code == 200
    print("PASS: /healthz")

    r = client.post("/api/auth/guest")
    assert r.status_code == 200
    user = r.json()["user"]
    assert user["username"].startswith("guest_")
    print("PASS: /api/auth/guest")

    r = client.get("/api/users/me")
    assert r.status_code == 200
    assert r.json()["user"]["id"] == user["id"]
    print("PASS: /api/users/me")

    r = client.get("/api/sessions")
    assert r.status_code == 200
    assert r.json()["sessions"] == []
    print("PASS: /api/sessions (empty)")

    r = client.post("/api/sessions", json={"title": "GPIO Controller", "project_id": "gpio"})
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    assert session_id
    print("PASS: POST /api/sessions")

    r = client.get("/api/sessions")
    assert r.status_code == 200
    sessions = r.json()["sessions"]
    assert len(sessions) == 1
    assert sessions[0]["title"] == "GPIO Controller"
    print("PASS: /api/sessions (1 item)")

    r = client.get(f"/api/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["title"] == "GPIO Controller"
    print("PASS: GET /api/sessions/{id}")

    r = client.patch(f"/api/sessions/{session_id}", json={"title": "UART Debug"})
    assert r.status_code == 200
    assert r.json()["title"] == "UART Debug"
    print("PASS: PATCH /api/sessions/{id}")

    r = client.post(f"/api/sessions/{session_id}/activate")
    assert r.status_code == 200
    assert r.json()["activated"] is True
    print("PASS: POST /api/sessions/{id}/activate")

    r = client.delete(f"/api/sessions/{session_id}")
    assert r.status_code == 200
    assert r.json()["deleted"] is True
    print("PASS: DELETE /api/sessions/{id}")

    r = client.get(f"/api/sessions/{session_id}")
    assert r.status_code == 404
    print("PASS: GET /api/sessions/{id} (404 after delete)")

    r = client.get("/lobby")
    assert r.status_code == 200
    assert "ATLAS Lobby" in r.text
    print("PASS: /lobby")

    with client.websocket_connect("/ws/agent?session_id=test-session") as ws:
        data = ws.receive_json()
        assert data["type"] == "hello"
        print("PASS: WebSocket /ws/agent?session_id=...")

    print("ALL END-TO-END TESTS PASSED")


if __name__ == "__main__":
    test_full_flow()
