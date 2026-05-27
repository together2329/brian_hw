import json

from fastapi.testclient import TestClient

from src.atlas_ui import _clear_history_file, _compact_history_file


def _register(client: TestClient, username: str) -> None:
    response = client.post(
        "/api/auth/register",
        json={"username": username, "password": "pw"},
    )
    assert response.status_code == 200, response.text


def test_web_compact_updates_local_conversation_file(tmp_path):
    history = tmp_path / ".session" / "brian" / "new_axi" / "default" / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "first requirement"},
        {"role": "assistant", "content": "first answer"},
        {"role": "user", "content": "second requirement"},
        {"role": "assistant", "content": "second answer"},
        {"role": "user", "content": "current question"},
        {"role": "assistant", "content": "current answer"},
    ]
    history.parent.mkdir(parents=True)
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, compacted = _compact_history_file(history, "COMPACT_HISTORY:keep=2")

    saved = json.loads(history.read_text(encoding="utf-8"))
    assert "Compacted local session history" in message
    assert compacted == saved
    assert [m["role"] for m in saved] == ["system", "system", "user", "assistant"]
    assert "first requirement" in saved[1]["content"]
    assert saved[-2]["content"] == "current question"
    assert saved[-1]["content"] == "current answer"


def test_web_compact_dry_run_does_not_write(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old response"},
        {"role": "user", "content": "middle"},
        {"role": "assistant", "content": "middle response"},
        {"role": "user", "content": "new"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, returned = _compact_history_file(history, "COMPACT_HISTORY:dry_run=true")

    assert message.startswith("Dry run:")
    assert returned == messages
    assert json.loads(history.read_text(encoding="utf-8")) == messages


def test_web_clear_keeps_requested_pairs(tmp_path):
    history = tmp_path / "conversation.json"
    messages = [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "old"},
        {"role": "assistant", "content": "old response"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new response"},
    ]
    history.write_text(json.dumps(messages), encoding="utf-8")

    message, cleared = _clear_history_file(history, "CLEAR_HISTORY:1")

    assert "kept last 1 message pair" in message
    assert cleared == json.loads(history.read_text(encoding="utf-8"))
    assert cleared == [
        {"role": "system", "content": "system prompt"},
        {"role": "user", "content": "new"},
        {"role": "assistant", "content": "new response"},
    ]


def test_websocket_compact_slash_compacts_active_session_file(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    session_id = "alice/ip_alpha/default"
    history = tmp_path / ".session" / "alice" / "ip_alpha" / "default" / "conversation.json"
    history.parent.mkdir(parents=True)
    history.write_text(
        json.dumps([
            {"role": "system", "content": "system prompt"},
            {"role": "user", "content": "old"},
            {"role": "assistant", "content": "old response"},
            {"role": "user", "content": "new"},
        ]),
        encoding="utf-8",
    )

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/compact --keep 1", "msg_id": "compact-1"})
        seen = []
        for _ in range(6):
            event = ws.receive_json()
            seen.append(event)
            if event.get("type") == "slash_output":
                break

    outputs = [event.get("text", "") for event in seen if event.get("type") == "slash_output"]
    assert outputs and "Compacted local session history" in outputs[-1]
    saved = json.loads(history.read_text(encoding="utf-8"))
    assert [m["role"] for m in saved] == ["system", "system", "user"]
    assert "old response" in saved[1]["content"]
    assert saved[-1]["content"] == "new"
