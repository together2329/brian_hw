import sys
from pathlib import Path

SOURCE_ROOT = Path(__file__).resolve().parents[1]
if str(SOURCE_ROOT) not in sys.path:
    sys.path.insert(0, str(SOURCE_ROOT))

from fastapi.testclient import TestClient


def test_full_flow(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
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

    with client.websocket_connect("/ws/agent?session_id=e2e_user/test_ip/ssot-gen") as ws:
        data = ws.receive_json()
        assert data["type"] == "hello"
        print("PASS: WebSocket /ws/agent?session_id=...")

    print("ALL END-TO-END TESTS PASSED")


def test_session_state_reads_db_messages_before_file_fallback(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    login = client.post("/api/auth/register", json={"username": "db_reader", "password": "pw"})
    assert login.status_code == 200, login.text

    created = client.post("/api/sessions", json={"title": "DB Session", "project_id": "timer"})
    assert created.status_code == 200, created.text
    session_id = created.json()["session_id"]

    with AtlasDB() as db:
        msg = db.save_message(session_id, "assistant", agent="ssot-gen")
        db.save_part(msg["id"], session_id, "text", text="hello from db")

    state = client.get(f"/api/session/state?session={session_id}")

    assert state.status_code == 200, state.text
    conversation = state.json()["conversation"]
    assert conversation["source"] == "db"
    assert conversation["exists"] is True
    assert conversation["messages"][0]["text"] == "hello from db"


def test_session_state_keeps_file_fallback_for_namespace_sessions(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    sdir = tmp_path / ".session" / "file_reader" / "ip_alpha" / "ssot-gen"
    sdir.mkdir(parents=True)
    (sdir / "conversation.json").write_text(
        '[{"role":"user","content":"hello from file"}]',
        encoding="utf-8",
    )

    client = TestClient(atlas_ui.create_app())
    login = client.post("/api/auth/register", json={"username": "file_reader", "password": "pw"})
    assert login.status_code == 200, login.text
    state = client.get("/api/session/state?session=file_reader/ip_alpha/ssot-gen")

    assert state.status_code == 200, state.text
    conversation = state.json()["conversation"]
    assert conversation["source"] == "file"
    assert conversation["messages"][0]["content"] == "hello from file"


if __name__ == "__main__":
    test_full_flow()
