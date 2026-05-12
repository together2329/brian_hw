import sys
from pathlib import Path

from fastapi.testclient import TestClient
from starlette.websockets import WebSocketDisconnect


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


def _activate(client: TestClient, session_id: str, ip: str, workflow: str):
    return client.post(
        "/api/session/activate",
        json={"session_id": session_id, "ip": ip, "workflow": workflow},
    )


def test_multiuser_session_ip_workflow_dirs_and_ip_visibility(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ACTIVE_WORKSPACE", "sta")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    assert _activate(alice, "alice", "ip_alpha", "sta").status_code == 200
    assert _activate(alice, "alice", "ip_beta", "sta").status_code == 200
    assert _activate(bob, "bob", "ip_gamma", "sta").status_code == 200

    assert (tmp_path / ".session" / "alice" / "ip_alpha" / "sta" / "conversation.json").is_file()
    assert (tmp_path / ".session" / "alice" / "ip_beta" / "sta" / "conversation.json").is_file()
    assert (tmp_path / ".session" / "bob" / "ip_gamma" / "sta" / "conversation.json").is_file()

    alice_ips = alice.get("/api/ip/list?session_id=alice")
    assert alice_ips.status_code == 200
    assert {item["name"] for item in alice_ips.json()["items"]} == {"ip_alpha", "ip_beta"}

    bob_ips = bob.get("/api/ip/list")
    assert bob_ips.status_code == 200
    assert {item["name"] for item in bob_ips.json()["items"]} == {"ip_gamma"}

    alice_reading_bob_ips = alice.get("/api/ip/list?session_id=bob")
    assert alice_reading_bob_ips.status_code == 403

    alice_sessions = alice.get("/api/session/list")
    assert alice_sessions.status_code == 200
    alice_listed = {row["session"] for row in alice_sessions.json()["sessions"]}
    assert alice_listed == {"alice/ip_alpha/sta", "alice/ip_beta/sta"}

    forbidden = alice.post(
        "/api/session/activate",
        json={"session_id": "bob", "ip": "ip_stolen", "workflow": "sta"},
    )
    assert forbidden.status_code == 403
    assert not (tmp_path / ".session" / "bob" / "ip_stolen").exists()


def test_ip_create_endpoint_does_not_pre_scaffold_ip_root(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = client.post("/api/ip/create", json={"name": "gpio"})

    assert response.status_code == 200
    assert response.json()["created"] is False
    assert not (tmp_path / "gpio").exists()


def test_multiuser_and_process_isolation_default_on(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.delenv("ATLAS_MULTI_USER", raising=False)
    monkeypatch.delenv("ATLAS_MULTI_USER_PROC", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()

    assert app.state.bridge._single_user is False
    assert app.state.bridge._process_manager is not None


def test_websocket_binds_full_session_namespace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect("/ws/agent?session_id=alice/ip_alpha/ssot-gen") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        session = app.state.bridge.get_session("alice/ip_alpha/ssot-gen")
        assert len(session.clients) == 1

    try:
        with client.websocket_connect("/ws/agent?session_id=bob/ip_beta/ssot-gen") as ws:
            ws.receive_json()
            raise AssertionError("cross-user websocket should be rejected")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_close_unbinds_and_reconnects_same_session(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_alpha/ssot-gen"
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        session = app.state.bridge.get_session(session_id)
        assert len(session.clients) == 1
        ws.close()

    assert len(app.state.bridge.get_session(session_id).clients) == 0

    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        assert len(app.state.bridge.get_session(session_id).clients) == 1

    assert len(app.state.bridge.get_session(session_id).clients) == 0


def test_websocket_slash_command_executes_without_agent_prompt(tmp_path, monkeypatch):
    import os
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_alpha/ssot-gen"
    session = app.state.bridge._ensure_session(session_id)
    session.agent_running = True
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/effort high", "msg_id": "effort-1"})

        seen = []
        for _ in range(3):
            seen.append(ws.receive_json())

    assert os.environ["REASONING_MODE"] == "high"
    assert any(msg.get("type") == "agent_received" for msg in seen)
    assert any(msg.get("type") == "slash_output" and "high" in msg.get("text", "") for msg in seen)
    assert not any(msg.get("type") == "agent_state" and msg.get("running") is False for msg in seen)
    assert session.agent_running is True
    assert session.agent_alive is False
    assert session._inbox.empty()


def test_multiuser_can_be_disabled(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.delenv("ATLAS_MULTI_USER_PROC", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()

    assert app.state.bridge._single_user is True
    assert app.state.bridge._process_manager is None


def test_multiuser_process_isolation_can_be_disabled(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()

    assert app.state.bridge._process_manager is None


def test_main_serve_cli_has_host_option_and_passes_it():
    main_py = (PROJECT_ROOT / "src" / "main.py").read_text(encoding="utf-8")

    assert "_parser.add_argument('--host'" in main_py
    assert "host=_args.host" in main_py
    assert "_agent_serve(" in main_py
