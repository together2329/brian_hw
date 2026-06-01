import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _register(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def test_prompt_forbidden_session_returns_delivery_ack(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect("/ws/agent?session_id=alice/default/default") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "session": "bob/ip_alpha/rtl-gen",
            "text": "Hi",
            "msg_id": "forbidden-target",
            "ip": "ip_alpha",
            "workflow": "rtl-gen",
        })
        accepted = ws.receive_json()

    assert accepted["type"] == "agent_accepted"
    assert accepted["msg_id"] == "forbidden-target"
    assert accepted["ok"] is False
    assert "invalid or forbidden session" in accepted["error"]
