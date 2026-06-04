import json
import importlib
import os
import sys
import time
from pathlib import Path
from typing import Optional

import pytest
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


@pytest.fixture(autouse=True)
def _isolate_atlas_db_path(tmp_path, monkeypatch):
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    for key in (
        "ATLAS_EXEC_MODE",
        "ATLAS_DEFAULT_EXEC_MODE",
        "ATLAS_ORCHESTRATOR_MODE",
        "ATLAS_SINGLE_MAIN_LOOP",
        "ATLAS_WORKSPACE_SESSION",
    ):
        monkeypatch.delenv(key, raising=False)


def _activate(
    client: TestClient,
    session_id: str,
    ip: str,
    workflow: str,
    preserve_running: Optional[bool] = None,
):
    body: dict[str, object] = {"session_id": session_id, "ip": ip, "workflow": workflow}
    if preserve_running is not None:
        body["preserve_running"] = preserve_running
    return client.post(
        "/api/session/activate",
        json=body,
    )


def _receive_until_types(ws, *types: str, limit: int = 12):
    seen = []
    needed = set(types)
    for _ in range(limit):
        msg = ws.receive_json()
        seen.append(msg)
        needed.discard(msg.get("type"))
        if not needed:
            return seen
    raise AssertionError(f"expected websocket events {sorted(types)!r}, saw {seen!r}")


def test_context_exports_ip_local_workflow_root(tmp_path):
    AtlasContext = importlib.import_module("core.atlas_context").AtlasContext

    context = AtlasContext(
        user_name="alice",
        workspace_session="s1",
        ip_name="spi_core",
        workflow="rtl-gen",
        atlas_root=tmp_path,
    )

    expected = tmp_path / "alice" / "s1" / "spi_core" / "workflow"
    assert context.workflow_root == expected
    assert context.export_env()["ATLAS_WORKFLOW_ROOT"] == str(expected)


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


def test_ip_list_hides_orphan_session_dirs_without_db_session(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "owned_ip", "rtl-gen")
    assert response.status_code == 200, response.text

    orphan = tmp_path / ".session" / "alice" / "stale_orphan_ip" / "ssot-gen"
    orphan.mkdir(parents=True)
    (orphan / "conversation.json").write_text("[]", encoding="utf-8")

    listed = client.get("/api/ip/list?session_id=alice")

    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["source"] == "db_sessions"
    assert {item["name"] for item in body["items"]} == {"owned_ip"}


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


def test_session_activate_accepts_v2_user_session_context(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = client.post(
        "/api/session/activate",
        json={
            "user_name": "alice",
            "workspace_session": "s1",
            "ip": "NEWIP_MCTP",
            "workflow": "ssot-gen",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    workspace_root = tmp_path / "alice" / "s1"
    session_dir = workspace_root / ".session" / "NEWIP_MCTP" / "ssot-gen"
    assert body["active_session"] == "alice/s1/NEWIP_MCTP/ssot-gen"
    assert body["context_key"] == "alice/s1/NEWIP_MCTP/ssot-gen"
    assert body["workspace_session"] == "s1"
    assert Path(body["workspace_root"]).resolve() == workspace_root.resolve()
    assert Path(body["ip_root"]).resolve() == (workspace_root / "NEWIP_MCTP").resolve()
    assert Path(body["session_dir"]).resolve() == session_dir.resolve()
    assert (session_dir / "conversation.json").is_file()

    health = client.get("/healthz")
    assert health.status_code == 200, health.text
    health_data = health.json()
    assert health_data["active_session"] == "alice/s1/NEWIP_MCTP/ssot-gen"
    assert health_data["active_ip"] == "NEWIP_MCTP"
    assert health_data["active_workflow"] == "ssot-gen"
    assert health_data["context_key"] == "alice/s1/NEWIP_MCTP/ssot-gen"
    assert Path(health_data["workspace_root"]).resolve() == workspace_root.resolve()
    assert Path(health_data["session_dir"]).resolve() == session_dir.resolve()

    (workspace_root / "NEWIP_MCTP" / "yaml").mkdir(parents=True, exist_ok=True)
    (workspace_root / "NEWIP_MCTP" / "yaml" / "NEWIP_MCTP.ssot.yaml").write_text(
        "ip: NEWIP_MCTP\n",
        encoding="utf-8",
    )
    ip_list = client.get("/api/ip/list?session_id=alice/s1/NEWIP_MCTP/ssot-gen")
    assert ip_list.status_code == 200, ip_list.text
    assert {item["name"] for item in ip_list.json()["items"]} == {"NEWIP_MCTP"}
    files = client.get(
        "/api/files",
        params={
            "path": "NEWIP_MCTP",
            "session_id": "alice/s1/NEWIP_MCTP/ssot-gen",
        },
    )
    assert files.status_code == 200, files.text
    assert files.json()["path"] == "NEWIP_MCTP"
    assert {entry["name"] for entry in files.json()["entries"]} == {"yaml"}


def test_ip_list_scopes_v2_workspace_session_per_user(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    for workspace_session, ip_name in (("s1", "ip_alpha"), ("s2", "ip_beta")):
        response = client.post(
            "/api/session/activate",
            json={
                "user_name": "alice",
                "workspace_session": workspace_session,
                "ip": ip_name,
                "workflow": "default",
            },
        )
        assert response.status_code == 200, response.text
        yaml_dir = tmp_path / "alice" / workspace_session / ip_name / "yaml"
        yaml_dir.mkdir(parents=True, exist_ok=True)
        (yaml_dir / f"{ip_name}.ssot.yaml").write_text(f"ip: {ip_name}\n", encoding="utf-8")

    s1_list = client.get("/api/ip/list?session_id=alice/s1/default/default")
    assert s1_list.status_code == 200, s1_list.text
    assert s1_list.json()["workspace_session"] == "s1"
    assert {item["name"] for item in s1_list.json()["items"]} == {"ip_alpha"}

    s2_list = client.get("/api/ip/list?session_id=alice/s2")
    assert s2_list.status_code == 200, s2_list.text
    assert s2_list.json()["workspace_session"] == "s2"
    assert {item["name"] for item in s2_list.json()["items"]} == {"ip_beta"}


def test_ip_list_uses_ip_blocks_when_workspace_catalog_exists(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    workspace_root = tmp_path / "alice" / "hi"
    (workspace_root / "jjj" / "yaml").mkdir(parents=True)
    (workspace_root / "jjj" / "yaml" / "jjj.ssot.yaml").write_text(
        "ip: jjj\n",
        encoding="utf-8",
    )
    (workspace_root / "real_ip").mkdir(parents=True)
    (workspace_root / "uart").mkdir(parents=True)

    with AtlasDB() as db:
        user = db.get_user_by_username("alice")
        assert user is not None
        workspace = db.upsert_workspace(
            f"{tmp_path.name}/hi",
            owner_user_id=user["id"],
            local_path=str(workspace_root.resolve()),
        )
        ip_row = db.upsert_ip_block(
            workspace["id"],
            "jjj",
            ssot_path="jjj/yaml/jjj.ssot.yaml",
        )
        for ip_name in ("jjj", "real_ip", "uart"):
            db.upsert_runtime_session(
                f"alice/hi/{ip_name}/default",
                user["id"],
                owner="alice",
                ip=ip_name,
                workflow="default",
                workspace_id=workspace["id"],
                ip_id=ip_row["id"] if ip_name == "jjj" else ip_name,
                project_id=ip_name,
                directory=str(workspace_root / ".session" / ip_name / "default"),
                title=f"{ip_name} / default",
                status="active",
                summary={"workspace_session": "hi", "ip": ip_name},
            )

    listed = client.get("/api/ip/list?session_id=alice/hi")

    assert listed.status_code == 200, listed.text
    body = listed.json()
    assert body["workspace_session"] == "hi"
    assert body["source"] == "db_ip_blocks"
    assert {item["name"] for item in body["items"]} == {"jjj"}


def test_session_activate_ignores_unregistered_ip_when_workspace_catalog_exists(
    tmp_path,
    monkeypatch,
):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    workspace_root = tmp_path / "alice" / "hi"
    (workspace_root / "jjj" / "yaml").mkdir(parents=True)
    (workspace_root / "jjj" / "yaml" / "jjj.ssot.yaml").write_text(
        "ip: jjj\n",
        encoding="utf-8",
    )
    with AtlasDB() as db:
        user = db.get_user_by_username("alice")
        assert user is not None
        workspace = db.upsert_workspace(
            f"{tmp_path.name}/hi",
            owner_user_id=user["id"],
            local_path=str(workspace_root.resolve()),
        )
        db.upsert_ip_block(
            workspace["id"],
            "jjj",
            ssot_path="jjj/yaml/jjj.ssot.yaml",
        )

    activated = client.post(
        "/api/session/activate",
        json={
            "owner": "alice",
            "workspace_session": "hi",
            "ip": "real_ip",
            "workflow": "default",
        },
    )

    assert activated.status_code == 200, activated.text
    payload = activated.json()
    assert payload["active_session"] == "alice/hi/default/default"
    assert payload["ip"] == "default"
    assert not (workspace_root / "real_ip").exists()
    with AtlasDB() as db:
        assert db.get_session("alice/hi/real_ip/default") is None


def test_ip_list_scopes_v2_workspace_session_in_desktop_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    legacy_yaml = tmp_path / "legacy_ip" / "yaml"
    legacy_yaml.mkdir(parents=True)
    (legacy_yaml / "legacy_ip.ssot.yaml").write_text("ip: legacy_ip\n", encoding="utf-8")
    for workspace_session, ip_name in (("s1", "ip_alpha"), ("s2", "ip_beta")):
        yaml_dir = tmp_path / "alice" / workspace_session / ip_name / "yaml"
        yaml_dir.mkdir(parents=True)
        (yaml_dir / f"{ip_name}.ssot.yaml").write_text(f"ip: {ip_name}\n", encoding="utf-8")

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    s1_list = client.get("/api/ip/list?session_id=alice/s1")
    assert s1_list.status_code == 200, s1_list.text
    assert s1_list.json()["workspace_session"] == "s1"
    assert {item["name"] for item in s1_list.json()["items"]} == {"ip_alpha"}

    s2_list = client.get("/api/ip/list?session_id=alice/s2/default/default")
    assert s2_list.status_code == 200, s2_list.text
    assert s2_list.json()["workspace_session"] == "s2"
    assert {item["name"] for item in s2_list.json()["items"]} == {"ip_beta"}


def test_ip_list_rejects_workspace_session_symlinks_in_desktop_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    for owner, workspace_session, ip_name in (
        ("alice", "s1", "ip_alpha"),
        ("bob", "s1", "ip_bob"),
    ):
        yaml_dir = tmp_path / owner / workspace_session / ip_name / "yaml"
        yaml_dir.mkdir(parents=True)
        (yaml_dir / f"{ip_name}.ssot.yaml").write_text(f"ip: {ip_name}\n", encoding="utf-8")
    outside_root = tmp_path.parent / f"{tmp_path.name}_outside"
    outside_yaml = outside_root / "ip_outside" / "yaml"
    outside_yaml.mkdir(parents=True)
    (outside_yaml / "ip_outside.ssot.yaml").write_text("ip: ip_outside\n", encoding="utf-8")

    symlink_cases = (
        ("s2_same_user", tmp_path / "alice" / "s1"),
        ("s2_other_user", tmp_path / "bob" / "s1"),
        ("s2_outside_root", outside_root),
    )
    for workspace_session, target in symlink_cases:
        (tmp_path / "alice" / workspace_session).symlink_to(target, target_is_directory=True)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    for workspace_session, _target in symlink_cases:
        response = client.get(f"/api/ip/list?session_id=alice/{workspace_session}")
        assert response.status_code == 400, response.text
        assert response.json()["items"] == []


def test_healthz_session_hint_selects_v2_workspace_session(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    for workspace_session in ("s1", "s2"):
        response = client.post(
            "/api/session/activate",
            json={
                "user_name": "alice",
                "workspace_session": workspace_session,
                "ip": "NEWIP_MCTP",
                "workflow": "default",
            },
        )
        assert response.status_code == 200, response.text

    hinted = client.get(
        "/healthz",
        params={"session_id": "alice/s1/NEWIP_MCTP/default"},
    )

    assert hinted.status_code == 200, hinted.text
    data = hinted.json()
    assert data["active_session"] == "alice/s1/NEWIP_MCTP/default"
    assert data["active_ip"] == "NEWIP_MCTP"
    assert data["active_workflow"] == "default"
    assert data["workspace_session"] == "s1"
    assert data["tokens_in"] == 0
    assert data["cost_usd"] == 0.0
    assert Path(data["project_root"]).resolve() == (tmp_path / "alice" / "s1").resolve()
    assert Path(data["session_dir"]).resolve() == (
        tmp_path / "alice" / "s1" / ".session" / "NEWIP_MCTP" / "default"
    ).resolve()

    with AtlasDB() as db:
        user = db.get_user_by_username("alice")
        assert user is not None
        db.upsert_runtime_session(
            "alice/NEWIP_MCTP/default",
            user["id"],
            owner="alice",
            ip="NEWIP_MCTP",
            workflow="default",
        )
        db.record_llm_call(
            session_id="alice/NEWIP_MCTP/default",
            ip_id="NEWIP_MCTP",
            workflow="default",
            tokens_input=999,
            tokens_output=99,
            cost_usd=9.99,
        )
        db.record_llm_call(
            session_id="alice/s2/NEWIP_MCTP/default",
            ip_id="NEWIP_MCTP",
            workflow="default",
            tokens_input=77,
            tokens_output=7,
            cost_usd=0.77,
        )

    hinted_again = client.get(
        "/healthz",
        params={"session_id": "alice/s1/NEWIP_MCTP/default"},
    )
    assert hinted_again.status_code == 200, hinted_again.text
    assert hinted_again.json()["active_session"] == "alice/s1/NEWIP_MCTP/default"
    assert hinted_again.json()["cost_ip"] == "NEWIP_MCTP"
    assert hinted_again.json()["tokens_in"] == 0
    assert hinted_again.json()["tokens_out"] == 0
    assert hinted_again.json()["cost_usd"] == 0.0

    s2_cost = client.get(
        "/healthz",
        params={"session_id": "alice/s2/NEWIP_MCTP/default"},
    )
    assert s2_cost.status_code == 200, s2_cost.text
    assert s2_cost.json()["active_session"] == "alice/s2/NEWIP_MCTP/default"
    assert s2_cost.json()["tokens_in"] == 77
    assert s2_cost.json()["tokens_out"] == 7
    assert s2_cost.json()["cost_usd"] == 0.77


def test_v2_session_history_state_and_todos_use_workspace_session_root(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    for workspace_session, content in (("s1", "todo in s1"), ("s2", "todo in s2")):
        response = client.post(
            "/api/session/activate",
            json={
                "user_name": "alice",
                "workspace_session": workspace_session,
                "ip": "NEWIP_MCTP",
                "workflow": "default",
            },
        )
        assert response.status_code == 200, response.text
        session_dir = tmp_path / "alice" / workspace_session / ".session" / "NEWIP_MCTP" / "default"
        session_dir.mkdir(parents=True, exist_ok=True)
        (session_dir / "conversation.json").write_text(
            json.dumps([{"role": "assistant", "content": f"history {workspace_session}"}]),
            encoding="utf-8",
        )
        (session_dir / "todo.json").write_text(
            json.dumps({"todos": [{"content": content, "status": "pending"}]}),
            encoding="utf-8",
        )

    s1 = "alice/s1/NEWIP_MCTP/default"
    s2 = "alice/s2/NEWIP_MCTP/default"
    history_s1 = client.get("/api/session/history", params={"session": s1})
    history_s2 = client.get("/api/session/history", params={"session": s2})
    state_s1 = client.get("/api/session/state", params={"session": s1})
    todos_s1 = client.get("/api/todos", params={"session": s1})
    todos_s2 = client.get("/api/todos", params={"session": s2})

    assert history_s1.status_code == 200, history_s1.text
    assert history_s2.status_code == 200, history_s2.text
    assert state_s1.status_code == 200, state_s1.text
    assert todos_s1.status_code == 200, todos_s1.text
    assert todos_s2.status_code == 200, todos_s2.text
    assert history_s1.json()["messages"][0]["content"] == "history s1"
    assert history_s2.json()["messages"][0]["content"] == "history s2"
    assert state_s1.json()["todos"]["todos"][0]["content"] == "todo in s1"
    assert todos_s1.json()["todos"][0]["content"] == "todo in s1"
    assert todos_s2.json()["todos"][0]["content"] == "todo in s2"

    cleared = client.post("/api/todos/clear", json={"session": s1})

    assert cleared.status_code == 200, cleared.text
    assert client.get("/api/todos", params={"session": s1}).json()["todos"] == []
    assert client.get("/api/todos", params={"session": s2}).json()["todos"][0]["content"] == "todo in s2"


def test_orchestrator_session_state_includes_ip_chat_ledger(tmp_path, monkeypatch):
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
    user_id = client.get("/api/users/me").json()["user"]["id"]
    with AtlasDB() as db:
        workspace = db.upsert_workspace(
            tmp_path.name,
            owner_user_id=user_id,
            local_path=str(tmp_path),
        )
        ip_row = db.upsert_ip_block(workspace["id"], "spi_core")
        db.record_chat_message(
            ip_row["id"],
            user_id,
            "pipeline question",
            display_name="alice",
        )
        db.record_chat_message(
            ip_row["id"],
            user_id,
            "pipeline answer",
            display_name="orchestrator",
            role="assistant",
        )

    state = client.get(
        "/api/session/state",
        params={"session": "alice/spi_core/orchestrator"},
    )
    assert state.status_code == 200, state.text
    conversation = state.json()["conversation"]
    assert conversation["source"].endswith("+orchestrator_chat")
    contents = [m.get("content") for m in conversation["messages"]]
    assert "pipeline question" in contents
    assert "pipeline answer" in contents

    history = client.get(
        "/api/session/history",
        params={"session": "alice/spi_core/orchestrator"},
    )
    assert history.status_code == 200, history.text
    assert history.json()["source"].endswith("+orchestrator_chat")
    assert "pipeline answer" in [m.get("content") for m in history.json()["messages"]]


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
    from core.atlas_db import AtlasDB

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
    with AtlasDB() as db:
        db.record_llm_call(
            session_id="alice/ip_alpha/rtl-gen",
            ip_id="ip_alpha",
            workflow="rtl-gen",
            tokens_input=100,
            tokens_output=20,
            cache_read_tokens=10,
            cost_usd=0.01,
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
    with AtlasDB() as db:
        db.record_llm_call(
            session_id="alice/ip_beta/rtl-gen",
            ip_id="ip_beta",
            workflow="rtl-gen",
            tokens_input=200,
            tokens_output=40,
            cache_read_tokens=30,
            cost_usd=0.02,
        )
        db.record_llm_call(
            session_id="alice/ip_beta/ssot-gen",
            ip_id="ip_beta",
            workflow="ssot-gen",
            tokens_input=50,
            tokens_output=5,
            cache_read_tokens=0,
            cost_usd=0.03,
        )

    beta_health = client.get("/healthz")
    assert beta_health.status_code == 200, beta_health.text
    assert beta_health.json()["active_session"] == "alice/ip_beta/rtl-gen"
    assert beta_health.json()["tokens"] == 200
    assert beta_health.json()["tokens_in"] == 250
    assert beta_health.json()["cost_usd"] == 0.05
    assert beta_health.json()["cost_scope"] == "user_ip"
    assert beta_health.json()["cost_ip"] == "ip_beta"

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
    from core.atlas_db import AtlasDB

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
    with AtlasDB() as db:
        db.record_llm_call(
            session_id="brian/ip_brian/rtl-gen",
            ip_id="ip_brian",
            workflow="rtl-gen",
            tokens_input=777,
            tokens_output=333,
            cost_usd=9.99,
        )

    numeric_before_activate = numeric.get("/healthz")
    assert numeric_before_activate.status_code == 200, numeric_before_activate.text
    before_payload = numeric_before_activate.json()
    assert before_payload["active_session"] == "20766/default/default/default"
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
    with AtlasDB() as db:
        db.record_llm_call(
            session_id="20766/ip_207/rtl-gen",
            ip_id="ip_207",
            workflow="rtl-gen",
            tokens_input=12,
            tokens_output=4,
            cache_read_tokens=3,
            cost_usd=0.07,
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

    with client.websocket_connect("/ws/agent?session_id=alice/default/ip_alpha/rtl-gen") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "session_switch",
            "session_id": "alice/default/ip_beta/tb-gen",
        })
        switched = ws.receive_json()
        assert switched["type"] == "session_switched"
        assert switched["session_id"] == "alice/default/ip_beta/tb-gen"
        ws.send_json({
            "type": "session_switch",
            "session_id": "bob/default/ip_beta/tb-gen",
        })
        rejected = ws.receive_json()
        assert rejected["type"] == "error"
        assert "forbidden" in rejected["message"]


def test_session_activate_preserves_running_worker_when_requested(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    # preserve_running keeps >1 worker per owner alive — a session-scoped
    # behavior. Strict single-active-owner (the code default) halts the previous
    # worker on switch, so opt into session-scoped to exercise this path.
    monkeypatch.setenv("ATLAS_SESSION_WORKER_POLICY", "session-scoped")
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


def test_process_session_activate_keeps_single_worker_process_warm(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    # Exercises the legacy spawn/kill/send_input switch path (session-scoped).
    # Strict single-active-owner uses spawn_result/terminate_session instead, so
    # opt into session-scoped for this FakeProcessManager contract.
    monkeypatch.setenv("ATLAS_SESSION_WORKER_POLICY", "session-scoped")
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
    assert first.json()["session_worker_warmup"]["status"] == "ready"
    assert calls == []
    calls.clear()
    app.state.bridge.get_session("alice/spi_core/rtl-gen").agent_running = True

    switched = _activate(client, "alice", "spi_core", "tb-gen")

    assert switched.status_code == 200, switched.text
    assert switched.json()["halted"] is True
    assert any(call[:3] == ("send_input", "alice/spi_core/rtl-gen", "stop") for call in calls)
    assert switched.json()["session_worker_warmup"]["status"] in {"scheduled", "ready"}


def test_single_worker_session_activate_warms_chat_process(tmp_path, monkeypatch):
    import atlas_api_jobs as jobs
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_DEFAULT_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.setenv("ATLAS_SINGLE_MAIN_LOOP", "1")
    # Asserts the background (status="scheduled") warmup contract. Strict
    # single-active-owner (the code default) warms synchronously (status=
    # "started"), so opt into session-scoped here.
    monkeypatch.setenv("ATLAS_SESSION_WORKER_POLICY", "session-scoped")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    monkeypatch.setattr(
        jobs,
        "schedule_worker_warmup",
        lambda **_kwargs: {"enabled": False, "reason": "test"},
    )

    calls = []

    class FakeProcessManager:
        def __init__(self):
            self.live = set()

        def is_alive(self, session_id):
            return session_id in self.live

        def latest_output_id(self, session_id):
            return None

        def spawn(self, session_id):
            time.sleep(0.2)
            calls.append(("spawn", session_id))
            self.live.add(session_id)
            return True

        def get_pid(self, session_id):
            return 4321 if session_id in self.live else 0

        def list_active(self):
            return list(self.live)

        def kill(self, session_id):
            calls.append(("kill", session_id))
            self.live.discard(session_id)
            return True

        def poll_output(self, session_id, since_id=None):
            return []

        def stop_all(self):
            self.live.clear()

    app = atlas_ui.create_app()
    app.state.bridge._process_manager = FakeProcessManager()
    client = TestClient(app)
    _register(client, "alice")

    response = _activate(client, "alice", "spi_core", "ssot-gen")

    assert response.status_code == 200, response.text
    body = response.json()
    assert body["session_worker_warmup"] == {
        "enabled": True,
        "mode": "process",
        "session_id": "alice/spi_core/ssot-gen",
        "status": "scheduled",
        "alive": False,
        "background": True,
    }
    assert calls == []
    deadline = time.time() + 2.0
    while time.time() < deadline and ("spawn", "alice/spi_core/ssot-gen") not in calls:
        time.sleep(0.02)
    assert ("spawn", "alice/spi_core/ssot-gen") in calls
    session = app.state.bridge.get_session("alice/spi_core/ssot-gen")
    assert session.agent_alive is True
    assert session.agent_running is False

    health = client.get("/healthz?cost=0")
    assert health.status_code == 200, health.text
    assert health.json()["agent_alive"] is True
    assert health.json()["agent_running"] is False


def test_todos_api_uses_requested_session_file(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    default_session = tmp_path / ".session" / "alice" / "ip22" / "default"
    ssot_session = tmp_path / ".session" / "alice" / "ip22" / "ssot-gen"
    default_session.mkdir(parents=True)
    ssot_session.mkdir(parents=True)
    (default_session / "todo.json").write_text(
        json.dumps({"todos": [{"content": "default todo", "status": "pending"}]}),
        encoding="utf-8",
    )
    (ssot_session / "todo.json").write_text(
        json.dumps({"todos": [{"content": "ssot todo", "status": "pending"}]}),
        encoding="utf-8",
    )

    default_resp = client.get("/api/todos", params={"session": "alice/ip22/default"})
    ssot_resp = client.get("/api/todos", params={"session": "alice/ip22/ssot-gen"})

    assert default_resp.status_code == 200, default_resp.text
    assert ssot_resp.status_code == 200, ssot_resp.text
    assert default_resp.json()["todos"][0]["content"] == "default todo"
    assert ssot_resp.json()["todos"][0]["content"] == "ssot todo"

    cleared = client.post("/api/todos/clear", json={"session": "alice/ip22/default"})

    assert cleared.status_code == 200, cleared.text
    assert client.get("/api/todos", params={"session": "alice/ip22/default"}).json()["todos"] == []
    assert client.get("/api/todos", params={"session": "alice/ip22/ssot-gen"}).json()["todos"][0]["content"] == "ssot todo"


def test_todos_crud_add_update_remove_clear_round_trip(tmp_path, monkeypatch):
    """add → update → remove → clear round-trip on a session todo file,
    asserting both the on-disk file and GET /api/todos reflect each change."""
    import json as _json
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session = "alice/ip22/default"
    session_dir = tmp_path / ".session" / "alice" / "ip22" / "default"
    session_dir.mkdir(parents=True)
    todo_file = session_dir / "todo.json"
    todo_file.write_text(json.dumps({"todos": []}), encoding="utf-8")

    def _get_todos():
        resp = client.get("/api/todos", params={"session": session})
        assert resp.status_code == 200, resp.text
        return resp.json()["todos"]

    def _disk_todos():
        return _json.loads(todo_file.read_text(encoding="utf-8"))["todos"]

    # ── ADD ──────────────────────────────────────────────────────────────
    add_resp = client.post("/api/todos/add", json={
        "session": session,
        "content": "first todo",
        "detail": "implement the thing",
        "criteria": "compiles\npasses tests",
        "priority": "high",
    })
    assert add_resp.status_code == 200, add_resp.text
    todos = _get_todos()
    assert len(todos) == 1
    assert todos[0]["content"] == "first todo"
    assert todos[0]["detail"] == "implement the thing"
    assert "compiles" in todos[0]["criteria"]
    assert todos[0]["priority"] == "high"
    assert _disk_todos()[0]["content"] == "first todo"

    # Reject empty content (400)
    bad_add = client.post("/api/todos/add", json={"session": session, "content": "   "})
    assert bad_add.status_code == 400, bad_add.text
    assert len(_get_todos()) == 1

    # Add a second so update/remove indices are meaningful
    add2 = client.post("/api/todos/add", json={
        "session": session,
        "content": "second todo",
        "detail": "second implementation detail",
        "criteria": "second acceptance criterion",
    })
    assert add2.status_code == 200, add2.text
    assert len(_get_todos()) == 2

    # ── UPDATE ───────────────────────────────────────────────────────────
    upd_resp = client.post("/api/todos/update", json={
        "session": session,
        "index": 0,
        "content": "first todo edited",
        "detail": "new approach",
        "criteria": "criterion A\ncriterion B",
        "state": "in_progress",
    })
    assert upd_resp.status_code == 200, upd_resp.text
    todos = _get_todos()
    assert todos[0]["content"] == "first todo edited"
    assert todos[0]["detail"] == "new approach"
    assert "criterion A" in todos[0]["criteria"]
    assert todos[0]["status"] == "in_progress"
    # untouched field on second todo stays the same
    assert todos[1]["content"] == "second todo"
    assert _disk_todos()[0]["content"] == "first todo edited"
    assert _disk_todos()[0]["status"] == "in_progress"

    # bad index → 400
    bad_upd = client.post("/api/todos/update", json={"session": session, "index": 99, "content": "x"})
    assert bad_upd.status_code == 400, bad_upd.text

    # ── REMOVE ───────────────────────────────────────────────────────────
    rm_resp = client.post("/api/todos/remove", json={"session": session, "index": 0})
    assert rm_resp.status_code == 200, rm_resp.text
    todos = _get_todos()
    assert len(todos) == 1
    assert todos[0]["content"] == "second todo"
    assert len(_disk_todos()) == 1

    bad_rm = client.post("/api/todos/remove", json={"session": session, "index": 5})
    assert bad_rm.status_code == 400, bad_rm.text

    # ── CLEAR ────────────────────────────────────────────────────────────
    clr_resp = client.post("/api/todos/clear", json={"session": session})
    assert clr_resp.status_code == 200, clr_resp.text
    assert _get_todos() == []
    assert _disk_todos() == []


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
            seen = _receive_until_types(ws, "agent_received", "agent_accepted", "mode_change")

        assert os.environ["PLAN_MODE"] == expected_plan_mode
        assert any(msg.get("type") == "agent_received" for msg in seen)
        assert any(msg.get("type") == "agent_accepted" and msg.get("ok") is True for msg in seen)
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


def test_ip_create_endpoint_scaffolds_once_and_rejects_duplicate(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = client.post("/api/ip/create", json={"name": "gpio"})

    assert response.status_code == 200
    assert response.json()["created"] is True
    assert response.json()["session"] == "alice/default/gpio/default"
    assert response.json()["workspace_session"] == "default"
    assert (tmp_path / "alice" / "default" / "gpio" / "yaml" / "gpio.ssot.yaml").is_file()
    assert (
        tmp_path
        / "alice"
        / "default"
        / ".session"
        / "gpio"
        / "default"
        / "conversation.json"
    ).is_file()

    listed = client.get("/api/ip/list")
    assert listed.status_code == 200, listed.text
    assert {item["name"] for item in listed.json()["items"]} == {"gpio"}
    assert listed.json()["items"][0]["workflows"] == ["default"]

    with AtlasDB() as db:
        user = db.get_user_by_username("alice")
        assert user is not None
        session = db.get_session("alice/default/gpio/default")
        assert session is not None
        assert session["user_id"] == user["id"]
        assert session["owner"] == "alice"
        assert session["ip"] == "gpio"
        assert session["workflow"] == "default"
        assert session["summary"]["kind"] == "atlas_ip_scaffold"
        assert session["summary"]["workspace_session"] == "default"
        assert session["summary"]["context_key"] == "alice/default/gpio/default"
        ip_rows = db._fetchall("SELECT id, ip_name FROM ip_blocks WHERE ip_name = ?", ("gpio",))
        assert len(ip_rows) == 1

    duplicate = client.post("/api/ip/create", json={"name": "gpio"})

    assert duplicate.status_code == 409
    assert "already exists" in duplicate.json()["error"]


def test_ip_create_endpoint_uses_session_root_in_single_user_desktop_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    atlas_root = tmp_path / "atlas-root"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(atlas_root))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    response = client.post(
        "/api/ip/create",
        json={
            "name": "desktop_ip",
            "workspace_session": "s2",
            "session_id": "brian/s2/default/default",
            "user_name": "brian",
        },
    )

    assert response.status_code == 200, response.text
    body = response.json()
    workspace_root = atlas_root / "brian" / "s2"
    assert body["session"] == "brian/s2/desktop_ip/default"
    assert Path(body["workspace_root"]).resolve() == workspace_root.resolve()
    assert Path(body["ip_root"]).resolve() == (workspace_root / "desktop_ip").resolve()
    assert (workspace_root / "desktop_ip" / "yaml" / "desktop_ip.ssot.yaml").is_file()
    assert (workspace_root / ".session" / "desktop_ip" / "default" / "conversation.json").is_file()
    assert not (tmp_path / "desktop_ip").exists()
    assert not (tmp_path / ".session" / "brian" / "desktop_ip").exists()

    listed = client.get(
        "/api/ip/list",
        params={"session_id": "brian/s2/default/default"},
    )
    assert listed.status_code == 200, listed.text
    listed_body = listed.json()
    assert {item["name"] for item in listed_body["items"]} == {"desktop_ip"}
    assert Path(listed_body["project_root"]).resolve() == tmp_path.resolve()
    assert Path(listed_body["workspace_root"]).resolve() == workspace_root.resolve()


def test_healthz_honors_query_session_root_in_single_user_desktop_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    atlas_root = tmp_path / "atlas-root"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "single-worker")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "0")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(atlas_root))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    created = client.post(
        "/api/ip/create",
        json={
            "name": "desktop_ip",
            "workspace_session": "s2",
            "session_id": "brian/s2/default/default",
            "user_name": "brian",
        },
    )
    assert created.status_code == 200, created.text

    health = client.get(
        "/healthz",
        params={"cost": "0", "session_id": "brian/s2/desktop_ip/default"},
    )

    assert health.status_code == 200, health.text
    body = health.json()
    workspace_root = atlas_root / "brian" / "s2"
    assert body["active_session"] == "brian/s2/desktop_ip/default"
    assert body["context_key"] == "brian/s2/desktop_ip/default"
    assert body["workspace_session"] == "s2"
    assert body["active_ip"] == "desktop_ip"
    assert body["active_workflow"] == "default"
    assert Path(body["project_root"]).resolve() == workspace_root.resolve()
    assert Path(body["workspace_root"]).resolve() == workspace_root.resolve()
    assert Path(body["ip_root"]).resolve() == (workspace_root / "desktop_ip").resolve()
    assert Path(body["session_dir"]).resolve() == (
        workspace_root / ".session" / "desktop_ip" / "default"
    ).resolve()


def test_healthz_ignores_unauthenticated_multiuser_query_session(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    bob_session = "bob/default/ip_beta/default"
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    response = client.get(
        "/healthz",
        params={"cost": "0", "session_id": bob_session},
    )

    assert response.status_code == 200, response.text
    body = response.json()
    assert body.get("active_session") != bob_session
    assert body.get("active_ip") != "ip_beta"
    assert "bob/default" not in str(body.get("workspace_root") or "")


def test_ip_create_rejects_workspace_session_symlink_in_multiuser_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    outside = tmp_path.parent / f"{tmp_path.name}_outside_create"
    outside.mkdir()
    owner_root = tmp_path / "alice"
    owner_root.mkdir()
    (owner_root / "s2").symlink_to(outside, target_is_directory=True)
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    _register(client, "alice")
    response = client.post(
        "/api/ip/create",
        json={
            "name": "leak_ip",
            "workspace_session": "s2",
            "session_id": "alice/s2/default/default",
        },
    )

    assert response.status_code == 400, response.text
    assert "symlink" in response.json()["error"]
    assert not (outside / "leak_ip").exists()


def test_healthz_rejects_workspace_session_symlink_in_desktop_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    atlas_root = tmp_path / "atlas-root"
    outside = tmp_path / "outside-root"
    outside.mkdir(parents=True)
    owner_root = atlas_root / "brian"
    owner_root.mkdir(parents=True)
    (owner_root / "s2").symlink_to(outside, target_is_directory=True)
    (outside / ".session" / "desktop_ip" / "default").mkdir(parents=True)
    (outside / ".session" / "desktop_ip" / "default" / "cost.json").write_text(
        '{"input_tokens":999999}',
        encoding="utf-8",
    )
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "0")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "0")
    monkeypatch.setenv("ATLAS_ROOT", str(atlas_root))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    response = client.get(
        "/healthz",
        params={"cost": "1", "session_id": "brian/s2/desktop_ip/default"},
    )

    assert response.status_code == 400, response.text
    assert "symlink" in response.json()["error"]
    assert "999999" not in response.text


def test_ip_create_endpoint_uses_orchestrator_workflow_in_orchestrator_mode(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", "1")
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    response = client.post("/api/ip/create", json={"name": "mctp"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["session"] == "alice/default/mctp/orchestrator"
    assert payload["workspace_session"] == "default"
    assert payload["workflow"] == "orchestrator"
    assert (
        tmp_path
        / "alice"
        / "default"
        / ".session"
        / "mctp"
        / "orchestrator"
        / "conversation.json"
    ).is_file()

    listed = client.get("/api/ip/list")
    assert listed.status_code == 200, listed.text
    assert listed.json()["items"][0]["workflows"] == ["orchestrator"]

    with AtlasDB() as db:
        session = db.get_session("alice/default/mctp/orchestrator")
        assert session is not None
        assert session["ip"] == "mctp"
        assert session["workflow"] == "orchestrator"
        assert session["summary"]["workflow"] == "orchestrator"
        assert session["summary"]["workspace_session"] == "default"


@pytest.mark.parametrize(
    ("exec_mode", "orchestrator_mode", "expected_workflow", "alice_ip", "bob_ip"),
    [
        ("single-worker", "0", "default", "alice_gpio", "bob_timer"),
        ("orchestrator", "1", "orchestrator", "alice_mctp", "bob_bridge"),
    ],
)
def test_ip_create_endpoint_allows_each_user_to_create_one_ip_per_exec_mode(
    tmp_path,
    monkeypatch,
    exec_mode,
    orchestrator_mode,
    expected_workflow,
    alice_ip,
    bob_ip,
):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_EXEC_MODE", exec_mode)
    monkeypatch.setenv("ATLAS_DEFAULT_EXEC_MODE", exec_mode)
    monkeypatch.setenv("ATLAS_ORCHESTRATOR_MODE", orchestrator_mode)
    monkeypatch.setenv("ATLAS_ROOT", str(tmp_path))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)
    _register(alice, "alice")
    _register(bob, "bob")

    alice_response = alice.post("/api/ip/create", json={"name": alice_ip})
    bob_response = bob.post("/api/ip/create", json={"name": bob_ip})

    assert alice_response.status_code == 200, alice_response.text
    assert bob_response.status_code == 200, bob_response.text
    alice_payload = alice_response.json()
    bob_payload = bob_response.json()
    assert alice_payload["session"] == f"alice/default/{alice_ip}/{expected_workflow}"
    assert bob_payload["session"] == f"bob/default/{bob_ip}/{expected_workflow}"
    assert alice_payload["workflow"] == expected_workflow
    assert bob_payload["workflow"] == expected_workflow
    assert alice_payload["workspace_session"] == "default"
    assert bob_payload["workspace_session"] == "default"
    assert alice_payload["exec_mode"] == exec_mode
    assert bob_payload["exec_mode"] == exec_mode

    for owner, ip in (("alice", alice_ip), ("bob", bob_ip)):
        assert (tmp_path / owner / "default" / ip / "yaml" / f"{ip}.ssot.yaml").is_file()
        assert (
            tmp_path
            / owner
            / "default"
            / ".session"
            / ip
            / expected_workflow
            / "conversation.json"
        ).is_file()

    alice_list = alice.get("/api/ip/list")
    bob_list = bob.get("/api/ip/list")
    assert alice_list.status_code == 200, alice_list.text
    assert bob_list.status_code == 200, bob_list.text
    assert {item["name"] for item in alice_list.json()["items"]} == {alice_ip}
    assert {item["name"] for item in bob_list.json()["items"]} == {bob_ip}
    assert alice_list.json()["items"][0]["workflows"] == [expected_workflow]
    assert bob_list.json()["items"][0]["workflows"] == [expected_workflow]

    owner_mismatch = alice.get(
        "/api/ip/list",
        params={"session_id": f"bob/default/{bob_ip}/{expected_workflow}"},
    )
    assert owner_mismatch.status_code == 403, owner_mismatch.text

    with AtlasDB() as db:
        alice_user = db.get_user_by_username("alice")
        bob_user = db.get_user_by_username("bob")
        assert alice_user is not None
        assert bob_user is not None

        alice_session = db.get_session(f"alice/default/{alice_ip}/{expected_workflow}")
        bob_session = db.get_session(f"bob/default/{bob_ip}/{expected_workflow}")
        assert alice_session is not None
        assert bob_session is not None
        assert alice_session["user_id"] == alice_user["id"]
        assert bob_session["user_id"] == bob_user["id"]
        assert alice_session["owner"] == "alice"
        assert bob_session["owner"] == "bob"
        assert alice_session["ip"] == alice_ip
        assert bob_session["ip"] == bob_ip
        assert alice_session["workflow"] == expected_workflow
        assert bob_session["workflow"] == expected_workflow

        rows = db._fetchall(
            """
            SELECT i.ip_name, w.owner_user_id
            FROM ip_blocks i
            JOIN workspaces w ON w.id = i.workspace_id
            WHERE i.ip_name IN (?, ?)
            """,
            (alice_ip, bob_ip),
        )
        assert {row["ip_name"]: row["owner_user_id"] for row in rows} == {
            alice_ip: alice_user["id"],
            bob_ip: bob_user["id"],
        }


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

    with client.websocket_connect("/ws/agent?session_id=alice/default/ip_alpha/ssot-gen") as ws:
        hello = ws.receive_json()
        assert hello["type"] == "hello"
        session = app.state.bridge.get_session("alice/default/ip_alpha/ssot-gen")
        assert len(session.clients) == 1

    try:
        with client.websocket_connect("/ws/agent?session_id=bob/ip_beta/ssot-gen") as ws:
            ws.receive_json()
            raise AssertionError("cross-user websocket should be rejected")
    except WebSocketDisconnect as exc:
        assert exc.code == 1008


def test_websocket_default_bind_uses_default_workspace_session(tmp_path, monkeypatch):
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
        assert health.json()["active_session"] == "20766/default/default/default"


def test_websocket_close_unbinds_and_reconnects_same_session(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/default/ip_alpha/ssot-gen"
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

    session_id = "alice/default/ip_alpha/ssot-gen"
    session = app.state.bridge._ensure_session(session_id)
    session.agent_running = True
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/effort high", "msg_id": "effort-1"})

        seen = _receive_until_types(ws, "agent_received", "agent_accepted", "slash_output")

    assert os.environ["REASONING_MODE"] == "high"
    assert any(msg.get("type") == "agent_received" for msg in seen)
    assert any(msg.get("type") == "agent_accepted" and msg.get("ok") is True for msg in seen)
    assert any(msg.get("type") == "slash_output" and "high" in msg.get("text", "") for msg in seen)
    assert not any(msg.get("type") == "agent_state" and msg.get("running") is False for msg in seen)
    assert session.agent_running is True
    assert session.agent_alive is False
    assert session._inbox.empty()


def test_websocket_plain_command_words_are_llm_prompts(tmp_path, monkeypatch):
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

    session_id = "alice/default/ip_alpha/rtl-gen"
    session = app.state.bridge._ensure_session(session_id)
    prompts = ["list", "ls", "list up rtl", "ssot-rtl"]

    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        for idx, prompt in enumerate(prompts):
            ws.send_json({"type": "prompt", "text": prompt, "msg_id": f"plain-{idx}"})
            seen = _receive_until_types(ws, "agent_received", "agent_accepted")
            assert any(msg.get("type") == "agent_received" for msg in seen)
            assert any(
                msg.get("type") == "agent_accepted"
                and msg.get("ok") is True
                and msg.get("queued") is True
                for msg in seen
            )
            assert session._inbox.get(timeout=1) == prompt


def test_websocket_bang_command_runs_shell_without_llm_prompt(tmp_path, monkeypatch):
    import core.tools as tools
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    calls = []

    def fake_run_command(command, timeout=60):
        calls.append((command, timeout))
        return "BANG_OK"

    monkeypatch.setattr(tools, "run_command", fake_run_command)

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    session_id = "alice/default/ip_alpha/rtl-gen"
    session = app.state.bridge._ensure_session(session_id)
    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "!echo hi", "msg_id": "bang-1"})
        seen = _receive_until_types(ws, "agent_received", "agent_accepted", "tool_result", "agent_state")

    assert calls == [("echo hi", 60)]
    assert any(msg.get("type") == "agent_received" for msg in seen)
    assert any(msg.get("type") == "agent_accepted" and msg.get("ok") is True for msg in seen)
    assert any(
        msg.get("type") == "tool_result"
        and msg.get("tool") == "run_command"
        and "$ echo hi" in msg.get("text", "")
        and "BANG_OK" in msg.get("text", "")
        for msg in seen
    )
    assert any(msg.get("type") == "agent_state" and msg.get("running") is False for msg in seen)
    assert session._inbox.empty()


def test_websocket_context_verbose_reads_active_root_session_conversation(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.context_tracker import reset_tracker

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    reset_tracker(max_tokens=200000)

    session_id = "alice/default/ip_alpha/default"
    session_dir = tmp_path / "alice" / "default" / ".session" / "ip_alpha" / "default"
    session_dir.mkdir(parents=True)
    (session_dir / "conversation.json").write_text(
        json.dumps(
            [
                {"role": "system", "content": f"[ACTIVE_SESSION: {session_id}]\n[PROJECT_ROOT: {tmp_path}]"},
                {"role": "user", "content": "root session context question"},
                {"role": "assistant", "content": "root session context answer"},
            ]
        ),
        encoding="utf-8",
    )

    app = atlas_ui.create_app()
    client = TestClient(app)
    _register(client, "alice")

    with client.websocket_connect(f"/ws/agent?session_id={session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({"type": "prompt", "text": "/context -v", "msg_id": "ctx-1"})

        output = ""
        for _ in range(5):
            msg = ws.receive_json()
            if msg.get("type") == "slash_output":
                output = str(msg.get("text") or "")
                break

    assert "root session context question" in output
    assert "root session context answer" in output
    assert "No message history available" not in output
    assert "Current context window is empty" not in output


def test_websocket_prompt_explicit_session_rebinds_before_queueing(tmp_path, monkeypatch):
    import queue
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

    default_session_id = "alice/default/default/default"
    target_session_id = "alice/default/ip_alpha/rtl-gen"
    default_session = app.state.bridge._ensure_session(default_session_id)
    target_session = app.state.bridge._ensure_session(target_session_id)

    with client.websocket_connect(f"/ws/agent?session_id={default_session_id}") as ws:
        assert ws.receive_json()["type"] == "hello"
        ws.send_json({
            "type": "prompt",
            "session": target_session_id,
            "text": "Hi",
            "msg_id": "cloudflare-first-prompt",
        })
        seen = _receive_until_types(ws, "agent_received", "agent_accepted")
        ack = next(msg for msg in seen if msg.get("type") == "agent_received")
        accepted = next(msg for msg in seen if msg.get("type") == "agent_accepted")

        assert ack["session_id"] == target_session_id
        assert ack["msg_id"] == "cloudflare-first-prompt"
        assert accepted["session_id"] == target_session_id
        assert accepted["msg_id"] == "cloudflare-first-prompt"
        assert accepted["ok"] is True
        assert accepted["queued"] is True
        assert target_session._inbox.get_nowait() == "Hi"
        assert default_session._inbox.empty()
        assert len(default_session.clients) == 0
        assert len(target_session.clients) == 1
        assert os.environ["ATLAS_ACTIVE_SESSION"] == target_session_id
        assert os.environ["ATLAS_ACTIVE_IP"] == "ip_alpha"
        assert os.environ["ATLAS_DEFAULT_WORKFLOW"] == "rtl-gen"

        ws.send_json({
            "type": "prompt",
            "session": target_session_id,
            "text": "Hi again",
            "msg_id": "cloudflare-first-prompt",
        })
        seen = _receive_until_types(ws, "agent_received", "agent_accepted")
        duplicate_ack = next(msg for msg in seen if msg.get("type") == "agent_received")
        duplicate_accepted = next(msg for msg in seen if msg.get("type") == "agent_accepted")

        assert duplicate_ack["session_id"] == target_session_id
        assert duplicate_accepted["session_id"] == target_session_id
        assert duplicate_accepted["ok"] is True
        assert duplicate_accepted["duplicate"] is True
        assert target_session._inbox.empty()
        try:
            default_session._inbox.get_nowait()
        except queue.Empty:
            pass
        else:
            raise AssertionError("stale default session received explicit-session prompt")


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


def test_textual_chat_loop_bang_prefix_runs_shell_before_llm_turn():
    main_py = (PROJECT_ROOT / "src" / "main.py").read_text(encoding="utf-8")

    bang_idx = main_py.index('if user_input.startswith("!"):')
    slash_idx = main_py.index("# Handle slash commands")
    llm_idx = main_py.index("_process_chat_turn(user_input, _loop_state, _loop_deps)")

    assert bang_idx < slash_idx < llm_idx
    assert "_bang_run_command(_shell_command, timeout=60)" in main_py
    assert '_textual_emit_tool_result_fn(_shell_output, "run_command")' in main_py


def test_native_textual_slash_output_uses_stdout_capture_only():
    main_py = (PROJECT_ROOT / "src" / "main.py").read_text(encoding="utf-8")
    textual_main_py = (PROJECT_ROOT / "src" / "textual_main.py").read_text(encoding="utf-8")

    assert "_textual_native_tui = False" in main_py
    assert "_agent._textual_native_tui" in textual_main_py
    assert "_textual_emit_content_fn is not None and not _textual_native_tui" in main_py
