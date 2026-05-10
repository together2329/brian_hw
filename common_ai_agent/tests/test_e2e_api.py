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

    r = client.post("/api/auth/register",
                    json={"username": "e2e_user", "password": "pw"})
    assert r.status_code == 200, f"register: {r.status_code} {r.text}"
    user = r.json()["user"]
    assert user["username"] == "e2e_user"
    print("PASS: /api/auth/register")

    r = client.get("/api/users/me")
    assert r.status_code == 200
    assert r.json()["user"]["id"] == user["id"]
    print("PASS: /api/users/me")

    r = client.get("/api/sessions")
    assert r.status_code == 200
    sessions_before = r.json()["sessions"]
    assert isinstance(sessions_before, list)
    print("PASS: /api/sessions (list)")

    r = client.post("/api/sessions", json={"title": "GPIO Controller", "project_id": "gpio"})
    assert r.status_code == 200
    session_id = r.json()["session_id"]
    assert session_id
    print("PASS: POST /api/sessions")

    r = client.get("/api/sessions")
    assert r.status_code == 200
    sessions = r.json()["sessions"]
    assert len(sessions) == len(sessions_before) + 1
    assert any(s["title"] == "GPIO Controller" for s in sessions)
    print("PASS: /api/sessions (contains created item)")

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
