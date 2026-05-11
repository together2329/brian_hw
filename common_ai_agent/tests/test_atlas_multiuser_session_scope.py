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


def test_main_serve_cli_has_host_option_and_passes_it():
    main_py = (PROJECT_ROOT / "src" / "main.py").read_text(encoding="utf-8")

    assert "_parser.add_argument('--host'" in main_py
    assert "host=_args.host" in main_py
    assert "_agent_serve(" in main_py
