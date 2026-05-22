import json
import sys
from pathlib import Path
from typing import Optional

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


def _activate(
    client: TestClient,
    session_id: str,
    ip: str,
    workflow: str,
    preserve_running: Optional[bool] = None,
):
    body = {"session_id": session_id, "ip": ip, "workflow": workflow}
    if preserve_running is not None:
        body["preserve_running"] = preserve_running
    return client.post(
        "/api/session/activate",
        json=body,
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
    alice_rows = alice_sessions.json()["sessions"]
    alice_listed = {row["session"] for row in alice_rows}
    assert alice_listed == {"alice/ip_alpha/sta", "alice/ip_beta/sta"}
    assert all(row["owner"] == "alice" for row in alice_rows)
    assert all(row["session_uid"] for row in alice_rows)
    assert {row["ip"] for row in alice_rows} == {"ip_alpha", "ip_beta"}

    forbidden = alice.post(
        "/api/session/activate",
        json={"session_id": "bob", "ip": "ip_stolen", "workflow": "sta"},
    )
    assert forbidden.status_code == 403
    assert not (tmp_path / ".session" / "bob" / "ip_stolen").exists()


def test_session_activate_records_db_control_plane_namespace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "spi_core", "orchestrator")

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["active_session"] == "alice/spi_core/orchestrator"
    assert payload["owner"] == "alice"
    assert payload["user_id"]
    assert payload["session_uid"]
    assert payload["runtime_session_id"] == payload["session_uid"]
    assert payload["session_label"].startswith("S-")
    health = client.get("/healthz")
    assert health.status_code == 200, health.text
    assert health.json()["db_session_id"] == "alice/spi_core/orchestrator"
    assert health.json()["session_uid"] == payload["session_uid"]
    user_id = client.get("/api/users/me").json()["user"]["id"]
    with AtlasDB() as db:
        session = db.get_session("alice/spi_core/orchestrator")
        assert session is not None
        assert session["session_uid"] == payload["session_uid"]
        assert session["user_id"] == user_id
        assert session["namespace"] == "alice/spi_core/orchestrator"
        assert session["owner"] == "alice"
        assert session["project_id"] == "spi_core"
        assert session["ip_id"] == "spi_core"
        assert session["ip"] == "spi_core"
        assert session["workflow"] == "orchestrator"
        assert session["session_kind"] == "runtime"
        assert session["summary"]["kind"] == "atlas_control_plane"
        assert session["summary"]["ip"] == "spi_core"
        assert session["summary"]["workflow"] == "orchestrator"
        listed = {row["id"]: row for row in db.list_all_sessions()}
        assert listed["alice/spi_core/orchestrator"]["ip"] == "spi_core"
        assert listed["alice/spi_core/orchestrator"]["workflow"] == "orchestrator"


def test_session_activate_owner_alias_keeps_db_user_id_distinct(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = client.post(
        "/api/session/activate",
        json={"owner": "alice", "ip": "spi_core", "workflow": "rtl-gen"},
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["active_session"] == "alice/spi_core/rtl-gen"
    assert payload["namespace"] == "alice/spi_core/rtl-gen"
    assert payload["owner"] == "alice"
    assert payload["session_id"] == "alice"
    assert payload["db_session_id"] == "alice/spi_core/rtl-gen"
    assert payload["session_uid"]
    assert payload["session"]["db_session_id"] == "alice/spi_core/rtl-gen"
    assert payload["session"]["owner"] == "alice"
    assert payload["session"]["ip"] == "spi_core"
    assert payload["session"]["workflow"] == "rtl-gen"
    user_id = client.get("/api/users/me").json()["user"]["id"]
    with AtlasDB() as db:
        session = db.get_session("alice/spi_core/rtl-gen")
        assert session is not None
        assert session["user_id"] == user_id
        assert session["user_id"] != session["id"]
        assert session["session_uid"] == payload["session_uid"]
        assert session["namespace"] == "alice/spi_core/rtl-gen"
        assert session["owner"] == "alice"


def test_session_history_and_state_forbid_cross_user_namespace_reads(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    activated = _activate(alice, "alice", "secret_ip", "rtl-gen")
    assert activated.status_code == 200, activated.text
    namespace = "alice/secret_ip/rtl-gen"
    session_dir = tmp_path / ".session" / "alice" / "secret_ip" / "rtl-gen"
    (session_dir / "conversation.json").write_text(
        json.dumps([{"role": "user", "content": "alice-only file"}]),
        encoding="utf-8",
    )
    (session_dir / "todo.json").write_text(
        json.dumps({"todos": [{"id": "alice-only-todo"}]}),
        encoding="utf-8",
    )
    with AtlasDB() as db:
        msg = db.save_message(namespace, "assistant")
        db.save_part(msg["id"], namespace, "text", text="alice-only db")

    assert alice.get("/api/session/history", params={"session": namespace}).status_code == 200
    assert alice.get("/api/session/state", params={"session": namespace}).status_code == 200

    forbidden_history = bob.get("/api/session/history", params={"session": namespace})
    forbidden_state = bob.get("/api/session/state", params={"session": namespace})

    assert forbidden_history.status_code == 403
    assert forbidden_state.status_code == 403


def test_healthz_context_cost_is_scoped_to_active_namespace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    alpha = _activate(client, "alice", "ip_alpha", "rtl-gen")
    assert alpha.status_code == 200, alpha.text
    alpha_cost = tmp_path / ".session" / "alice" / "ip_alpha" / "rtl-gen" / "cost.json"
    alpha_cost.write_text(
        json.dumps({
            "in_tok": 100,
            "cache_tok": 10,
            "out_tok": 20,
            "sum_tok": 120,
            "cost_usd": 0.01,
            "last_in_tok": 100,
            "last_cache_tok": 10,
            "last_out_tok": 20,
        }),
        encoding="utf-8",
    )

    beta = _activate(client, "alice", "ip_beta", "rtl-gen")
    assert beta.status_code == 200, beta.text
    beta_cost = tmp_path / ".session" / "alice" / "ip_beta" / "rtl-gen" / "cost.json"
    beta_cost.write_text(
        json.dumps({
            "in_tok": 200,
            "cache_tok": 30,
            "out_tok": 40,
            "sum_tok": 240,
            "cost_usd": 0.02,
            "last_in_tok": 200,
            "last_cache_tok": 30,
            "last_out_tok": 40,
        }),
        encoding="utf-8",
    )

    beta_health = client.get("/healthz")
    assert beta_health.status_code == 200, beta_health.text
    assert beta_health.json()["active_session"] == "alice/ip_beta/rtl-gen"
    assert beta_health.json()["tokens"] == 200
    assert beta_health.json()["tokens_in"] == 200
    assert beta_health.json()["cost_usd"] == 0.02

    alpha_again = _activate(client, "alice", "ip_alpha", "rtl-gen")
    assert alpha_again.status_code == 200, alpha_again.text
    alpha_health = client.get("/healthz")
    assert alpha_health.status_code == 200, alpha_health.text
    assert alpha_health.json()["active_session"] == "alice/ip_alpha/rtl-gen"
    assert alpha_health.json()["tokens"] == 100
    assert alpha_health.json()["tokens_in"] == 100
    assert alpha_health.json()["cost_usd"] == 0.01

    empty = _activate(client, "alice", "ip_empty", "rtl-gen")
    assert empty.status_code == 200, empty.text
    empty_health = client.get("/healthz")
    assert empty_health.status_code == 200, empty_health.text
    assert empty_health.json()["active_session"] == "alice/ip_empty/rtl-gen"
    assert empty_health.json()["tokens"] == 0
    assert empty_health.json()["tokens_in"] == 0
    assert empty_health.json()["cost_usd"] == 0.0


def test_healthz_does_not_share_cost_with_numeric_user_owner(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_SESSION_PER_MODEL", "0")
    monkeypatch.setenv("ATLAS_DEFAULT_WORKFLOW", "default")
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    brian = TestClient(app)
    numeric = TestClient(app)
    _register(brian, "brian")
    _register(numeric, "20766")

    brian_active = _activate(brian, "brian", "ip_brian", "rtl-gen")
    assert brian_active.status_code == 200, brian_active.text
    brian_cost = tmp_path / ".session" / "brian" / "ip_brian" / "rtl-gen" / "cost.json"
    brian_cost.write_text(
        json.dumps({
            "in_tok": 777,
            "cache_tok": 0,
            "out_tok": 333,
            "sum_tok": 1110,
            "cost_usd": 9.99,
        }),
        encoding="utf-8",
    )

    numeric_before_activate = numeric.get("/healthz")
    assert numeric_before_activate.status_code == 200, numeric_before_activate.text
    before_payload = numeric_before_activate.json()
    assert before_payload["active_session"] == "20766/default/default"
    assert before_payload["tokens"] == 0
    assert before_payload["tokens_in"] == 0
    assert before_payload["tokens_out"] == 0
    assert before_payload["cost_usd"] == 0.0

    numeric_active = _activate(numeric, "20766", "ip_207", "rtl-gen")
    assert numeric_active.status_code == 200, numeric_active.text
    numeric_cost = tmp_path / ".session" / "20766" / "ip_207" / "rtl-gen" / "cost.json"
    numeric_cost.write_text(
        json.dumps({
            "in_tok": 12,
            "cache_tok": 3,
            "out_tok": 4,
            "sum_tok": 16,
            "cost_usd": 0.07,
            "last_in_tok": 12,
            "last_cache_tok": 3,
            "last_out_tok": 4,
        }),
        encoding="utf-8",
    )

    numeric_after_activate = numeric.get("/healthz")
    assert numeric_after_activate.status_code == 200, numeric_after_activate.text
    after_payload = numeric_after_activate.json()
    assert after_payload["active_session"] == "20766/ip_207/rtl-gen"
    assert after_payload["tokens"] == 12
    assert after_payload["tokens_in"] == 12
    assert after_payload["tokens_out"] == 4
    assert after_payload["cost_usd"] == 0.07


def test_http_control_stop_targets_request_user_session_only(tmp_path, monkeypatch):
    import asyncio
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    assert _activate(alice, "alice", "ip_alpha", "rtl-gen").status_code == 200
    assert _activate(bob, "bob", "ip_beta", "rtl-gen").status_code == 200

    alice_session = app.state.bridge._ensure_session("alice/ip_alpha/rtl-gen")
    bob_session = app.state.bridge._ensure_session("bob/ip_beta/rtl-gen")
    alice_session.agent_running = True
    bob_session.agent_running = True

    while True:
        event, _sid = asyncio.get_event_loop().run_until_complete(
            app.state.bridge.next_event(timeout=0.01)
        )
        if event is None:
            break

    response = alice.post("/api/control/stop")

    assert response.status_code == 200, response.text
    assert response.json()["session_id"] == "alice/ip_alpha/rtl-gen"
    assert alice_session.agent_running is False
    assert bob_session.agent_running is True

    events = []
    while True:
        event, sid = asyncio.get_event_loop().run_until_complete(
            app.state.bridge.next_event(timeout=0.01)
        )
        if event is None:
            break
        events.append((event, sid))
    assert any(
        event.get("type") == "agent_state"
        and event.get("running") is False
        and sid == "alice/ip_alpha/rtl-gen"
        for event, sid in events
    )
    assert not any(
        event.get("type") == "agent_state"
        and event.get("running") is False
        and sid == "bob/ip_beta/rtl-gen"
        for event, sid in events
    )


def test_ip_list_requires_login_in_multiuser_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)

    response = client.get("/api/ip/list")

    assert response.status_code == 401, response.text
    assert response.json().get("items", []) == []


def test_websocket_session_switch_rebinds_without_disconnect(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect("/ws/agent?session_id=alice/ip_alpha/rtl-gen") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "session_switch",
            "session_id": "alice/ip_beta/tb-gen",
        })
        switched = ws.receive_json()
        assert switched["type"] == "session_switched"
        assert switched["session_id"] == "alice/ip_beta/tb-gen"
        ws.send_json({
            "type": "session_switch",
            "session_id": "bob/ip_beta/tb-gen",
        })
        rejected = ws.receive_json()
        assert rejected["type"] == "error"
        assert "forbidden" in rejected["message"]


def test_session_activate_preserves_running_worker_when_requested(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "spi_core", "orchestrator")
    assert response.status_code == 200, response.text
    orchestrator = app.state.bridge._ensure_session("alice/spi_core/orchestrator")
    orchestrator.agent_running = True

    preserved = _activate(
        client,
        "alice",
        "spi_core",
        "rtl-gen",
        preserve_running=True,
    )
    assert preserved.status_code == 200, preserved.text
    assert preserved.json()["active_session"] == "alice/spi_core/rtl-gen"
    assert preserved.json()["halted"] is False
    assert preserved.json()["preserve_running"] is True
    assert orchestrator.agent_running is True

    rtl = app.state.bridge._ensure_session("alice/spi_core/rtl-gen")
    rtl.agent_running = True
    halted = _activate(client, "alice", "spi_core", "tb-gen")
    assert halted.status_code == 200, halted.text
    assert halted.json()["active_session"] == "alice/spi_core/tb-gen"
    assert halted.json()["halted"] is True
    assert halted.json()["preserve_running"] is False
    assert rtl.agent_running is False


def test_session_activate_halts_only_previous_namespace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    # Another session is running, but the namespace the user is leaving is not.
    other = app.state.bridge._ensure_session("alice/spi_core/orchestrator")
    other.agent_running = True

    first = _activate(client, "alice", "spi_core", "rtl-gen")
    assert first.status_code == 200, first.text
    second = _activate(client, "alice", "spi_core", "tb-gen")

    assert second.status_code == 200, second.text
    assert second.json()["halted"] is False
    assert other.agent_running is True


def test_process_session_activate_terminates_previous_worker(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    calls = []

    class FakeProcessManager:
        def __init__(self):
            self.live = {"alice/spi_core/rtl-gen"}

        def is_alive(self, session_id):
            return session_id in self.live

        def kill(self, session_id):
            calls.append(("kill", session_id))
            self.live.discard(session_id)
            return True

        def list_active(self):
            return list(self.live)

        def send_input(self, session_id, msg_type, payload=None):
            calls.append(("send_input", session_id, msg_type, payload))
            return "msg-id" if session_id in self.live else None

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            self.live.add(session_id)
            calls.append(("spawn", session_id))
            return True

        def poll_output(self, session_id, since_id=None):
            return []

        def stop_all(self):
            calls.append(("stop_all",))
            self.live.clear()

    app.state.bridge._process_manager = FakeProcessManager()
    first = _activate(client, "alice", "spi_core", "rtl-gen")
    assert first.status_code == 200, first.text
    assert first.json()["halted"] is False
    assert calls == []
    app.state.bridge.get_session("alice/spi_core/rtl-gen").agent_running = True

    switched = _activate(client, "alice", "spi_core", "tb-gen")

    assert switched.status_code == 200, switched.text
    assert switched.json()["halted"] is True
    assert ("kill", "alice/spi_core/rtl-gen") in calls
    assert not any(call[:3] == ("send_input", "alice/spi_core/rtl-gen", "stop") for call in calls)
    assert app.state.bridge.get_session("alice/spi_core/rtl-gen").agent_alive is False


def test_process_session_activate_does_not_mutate_main_env(tmp_path, monkeypatch):
    import os

    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "sentinel/ip_old/wf_old")
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "ip_old")
    monkeypatch.setenv("ATLAS_DEFAULT_SESSION_ID", "sentinel")
    monkeypatch.setenv("ATLAS_DEFAULT_WORKFLOW", "wf_old")
    monkeypatch.setenv("ACTIVE_WORKSPACE", "wf_old")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "spi_core", "rtl-gen")

    assert response.status_code == 200, response.text
    assert response.json()["active_session"] == "alice/spi_core/rtl-gen"
    assert os.environ["ATLAS_ACTIVE_SESSION"] == "sentinel/ip_old/wf_old"
    assert os.environ["ATLAS_ACTIVE_IP"] == "ip_old"
    assert os.environ["ATLAS_DEFAULT_SESSION_ID"] == "sentinel"
    assert os.environ["ATLAS_DEFAULT_WORKFLOW"] == "wf_old"
    assert os.environ["ACTIVE_WORKSPACE"] == "wf_old"

    health = client.get("/healthz")
    assert health.status_code == 200, health.text
    assert health.json()["active_session"] == "alice/spi_core/rtl-gen"
    assert health.json()["active_ip"] == "spi_core"
    assert health.json()["active_workflow"] == "rtl-gen"


def test_process_workers_stop_on_app_shutdown(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    calls = []

    class FakeProcessManager:
        def stop_all(self):
            calls.append("stop_all")

    app.state.bridge._process_manager = FakeProcessManager()
    with TestClient(app):
        assert calls == []

    assert calls == ["stop_all"]


def test_session_activate_policy_and_mode_sweep_keeps_namespace_todos_isolated(tmp_path, monkeypatch):
    import os

    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_RUN_MODE", raising=False)
    monkeypatch.delenv("ATLAS_ORCHESTRATOR_MODE", raising=False)
    monkeypatch.delenv("AGENT_MODE_OVERRIDE", raising=False)
    monkeypatch.delenv("PLAN_MODE", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    cases = [
        ("spi_core", "ssot-gen", "starter", "orchestrator", "/mode plan", "true"),
        ("spi_core", "rtl-gen", "engineering", "single-worker", "/normal", "false"),
        ("uart_core", "tb-gen", "signoff", "orchestrator", "/mode plan", "true"),
        ("uart_core", "sim_debug", "starter", "single-worker", "/normal", "false"),
        ("spi_core", "coverage", "engineering", "orchestrator", "/mode plan", "true"),
        ("uart_core", "orchestrator", "signoff", "orchestrator", "/normal", "false"),
    ]
    sentinels: dict[str, str] = {}

    for idx, (ip, workflow, run_mode, exec_mode, slash, expected_plan_mode) in enumerate(cases):
        canonical = f"alice/{ip}/{workflow}"
        response = _activate(client, "alice", ip, workflow)
        assert response.status_code == 200, response.text
        assert response.json()["active_session"] == canonical
        assert os.environ["ATLAS_ACTIVE_SESSION"] == canonical
        assert os.environ["ATLAS_ACTIVE_IP"] == ip
        assert os.environ["ATLAS_DEFAULT_WORKFLOW"] == workflow

        session_dir = tmp_path / ".session" / "alice" / ip / workflow
        todo_path = session_dir / "todo.json"
        sentinel = f"{canonical}:todo:{idx}"
        todo_path.write_text(
            json.dumps({"todos": [{"id": sentinel, "title": sentinel, "status": "pending"}]}),
            encoding="utf-8",
        )
        sentinels[canonical] = sentinel

        policy = client.post(
            "/api/pipeline/run_policy",
            json={"run_mode": run_mode, "exec_mode": exec_mode},
        )
        assert policy.status_code == 200, policy.text
        assert policy.json()["run_mode"] == run_mode
        assert policy.json()["exec_mode"] == exec_mode

        bridge_session = app.state.bridge._ensure_session(canonical)
        while not bridge_session._outbox.empty():
            bridge_session._outbox.get_nowait()
        bridge_session.agent_running = True
        with client.websocket_connect(f"/ws/agent?session_id={canonical}") as ws:
            assert ws.receive_json()["type"] == "hello"
            ws.send_json({"type": "prompt", "text": slash, "msg_id": f"mode-{idx}"})
            seen = [ws.receive_json() for _ in range(3)]

        assert os.environ["PLAN_MODE"] == expected_plan_mode
        assert any(msg.get("type") == "agent_received" for msg in seen)
        assert any(msg.get("type") == "mode_change" for msg in seen)
        assert bridge_session._inbox.empty()

        health = client.get("/healthz")
        assert health.status_code == 200, health.text
        health_data = health.json()
        assert health_data["active_session"] == canonical
        assert health_data["active_ip"] == ip
        assert health_data["active_workflow"] == workflow
        assert Path(health_data["todo_file"]).resolve() == todo_path.resolve()
        assert Path(health_data["session_dir"]).resolve() == session_dir.resolve()

        state = client.get("/api/session/state", params={"session": canonical})
        assert state.status_code == 200, state.text
        todos = state.json()["todos"]["todos"]
        assert [todo["id"] for todo in todos] == [sentinel]

        for previous, previous_sentinel in sentinels.items():
            previous_state = client.get("/api/session/state", params={"session": previous})
            assert previous_state.status_code == 200, previous_state.text
            previous_ids = [todo["id"] for todo in previous_state.json()["todos"]["todos"]]
            assert previous_ids == [previous_sentinel]

    listed = client.get("/api/session/list")
    assert listed.status_code == 200, listed.text
    listed_sessions = {row["session"] for row in listed.json()["sessions"]}
    assert set(sentinels) <= listed_sessions

    with AtlasDB(os.environ["ATLAS_DB_PATH"]) as db:
        db_sessions = {row["id"]: row for row in db.list_all_sessions()}
        for canonical in sentinels:
            _, ip, workflow = canonical.split("/")
            assert db_sessions[canonical]["ip"] == ip
            assert db_sessions[canonical]["workflow"] == workflow
            session_row = db.get_session(canonical)
            assert session_row is not None
            assert session_row["summary"]["owner"] == "alice"
            assert session_row["summary"]["namespace"] == canonical


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


def test_model_scoped_session_dirs_are_opt_in(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_SESSION_PER_MODEL", "1")
    monkeypatch.setenv("LLM_ACTIVE_MODEL_NAME", "kimi-2.6")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "ip_alpha", "sta")

    assert response.status_code == 200
    assert response.json()["session_id"] == "alice__kimi-2_6"
    assert (tmp_path / ".session" / "alice__kimi-2_6" / "ip_alpha" / "sta" / "conversation.json").is_file()


def test_multiuser_and_process_isolation_default_on(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_MULTI_USER", raising=False)
    monkeypatch.delenv("ATLAS_MULTI_USER_PROC", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    root_only_ip = tmp_path / "root_only_ip"
    (root_only_ip / "rtl").mkdir(parents=True)
    (root_only_ip / "yaml").mkdir()
    (root_only_ip / "yaml" / "root_only_ip.ssot.yaml").write_text(
        "ip: root_only_ip\n",
        encoding="utf-8",
    )

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    assert app.state.bridge._single_user is False
    assert app.state.bridge._process_manager is not None

    assert _activate(alice, "alice", "ip_alpha", "sta").status_code == 200
    assert _activate(bob, "bob", "ip_beta", "sta").status_code == 200

    alice_ips = alice.get("/api/ip/list")
    assert alice_ips.status_code == 200, alice_ips.text
    assert {item["name"] for item in alice_ips.json()["items"]} == {"ip_alpha"}

    bob_ips = bob.get("/api/ip/list")
    assert bob_ips.status_code == 200, bob_ips.text
    assert {item["name"] for item in bob_ips.json()["items"]} == {"ip_beta"}

    alice_reading_bob_ips = alice.get("/api/ip/list?session_id=bob")
    assert alice_reading_bob_ips.status_code == 403

    alice_sessions = alice.get("/api/session/list")
    assert alice_sessions.status_code == 200, alice_sessions.text
    assert {row["session"] for row in alice_sessions.json()["sessions"]} == {"alice/ip_alpha/sta"}

    bob_sessions = bob.get("/api/session/list")
    assert bob_sessions.status_code == 200, bob_sessions.text
    assert {row["session"] for row in bob_sessions.json()["sessions"]} == {"bob/ip_beta/sta"}


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


def test_websocket_default_bind_keeps_three_part_user_namespace(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "20766")

    with client.websocket_connect("/ws/agent") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        health = client.get("/healthz")
        assert health.status_code == 200, health.text
        assert health.json()["active_session"] == "20766/default/default"


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


def test_no_arg_stage_slash_uses_websocket_session_ip(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ACTIVE_SESSION", "default/default/default")
    monkeypatch.setenv("ATLAS_ACTIVE_IP", "default")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/ip_alpha/rtl-gen"
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/ssot-rtl", "msg_id": "ssot-rtl-1"})
        seen = [ws.receive_json() for _ in range(6)]

    outputs = [msg.get("text", "") for msg in seen if msg.get("type") == "slash_output"]
    assert outputs
    assert "ip_alpha/yaml/ip_alpha.ssot.yaml" in outputs[0]
    assert "default/yaml/default.ssot.yaml" not in outputs[0]


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
