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


def _activate(client: TestClient, username: str, ip: str, workflow: str) -> None:
    response = client.post(
        "/api/session/activate",
        json={"session_id": username, "ip": ip, "workflow": workflow},
    )
    assert response.status_code == 200, response.text


def _seed_call(db, username: str, ip_name: str, workflow: str, cost: float, tokens: int = 100):
    user = db.get_user_by_username(username)
    session = db.get_session(f"{username}/{ip_name}/{workflow}")
    assert user is not None
    assert session is not None
    workspace = db.upsert_workspace(
        owner_user_id=user["id"],
        name=f"{username}-ws",
        local_path=f"/repo/{username}",
    )
    ip = db.upsert_ip_block(workspace["id"], ip_name, ip_type="rtl")
    run = db.start_workflow_run(
        session_id=session["id"],
        workspace_id=workspace["id"],
        ip_id=ip["id"],
        workflow=workflow,
        status="running",
    )
    db.record_llm_call(
        session_id=session["id"],
        run_id=run["id"],
        workspace_id=workspace["id"],
        ip_id=ip["id"],
        workflow=workflow,
        model="gpt-test",
        tokens_input=tokens,
        tokens_output=tokens // 4,
        tokens_reasoning=5,
        cost_usd=cost,
    )
    return run


def test_user_dashboard_requires_login(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    response = client.get("/api/user/dashboard")

    assert response.status_code == 401, response.text


def test_user_dashboard_is_scoped_per_user(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_RUN_MODE", "engineering")
    monkeypatch.setenv("ATLAS_EXEC_MODE", "orchestrator")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    alice = TestClient(app)
    bob = TestClient(app)

    _register(alice, "alice")
    _register(bob, "bob")
    _activate(alice, "alice", "spi_core", "rtl-gen")
    _activate(bob, "bob", "uart_core", "ssot-gen")

    with AtlasDB() as db:
        _seed_call(db, "alice", "spi_core", "rtl-gen", 0.12, tokens=240)
        _seed_call(db, "bob", "uart_core", "ssot-gen", 0.03, tokens=60)
        alice_user = db.get_user_by_username("alice")
        alice_workspace = db.upsert_workspace(
            owner_user_id=alice_user["id"],
            name="alice-extra-ws",
            local_path="/repo/alice-extra",
        )
        db.upsert_ip_block(alice_workspace["id"], "idle_core", ip_type="rtl", status="active")

    alice_response = alice.get("/api/user/dashboard")
    assert alice_response.status_code == 200, alice_response.text
    alice_body = alice_response.json()
    assert alice_body["user"]["username"] == "alice"
    assert alice_body["current"]["ip"] == "spi_core"
    assert alice_body["current"]["workflow"] == "rtl-gen"
    assert alice_body["current"]["exec_mode"] == "orchestrator"
    assert round(alice_body["metrics"]["total_cost_usd"], 4) == 0.12
    assert alice_body["metrics"]["llm_calls"] == 1
    assert [row["ip"] for row in alice_body["ip_workload"]] == ["spi_core"]
    assert {row["ip"] for row in alice_body["ip_inventory"]} == {"idle_core", "spi_core"}
    idle_row = next(row for row in alice_body["ip_inventory"] if row["ip"] == "idle_core")
    assert idle_row["status"] == "active"
    assert idle_row["last_workflow"] == ""
    assert idle_row["workflows"] == []
    assert idle_row["runs"] == 0
    assert idle_row["calls"] == 0
    assert [row["workflow"] for row in alice_body["workflow_progress"]] == ["rtl-gen"]
    assert all(row["ip"] != "uart_core" for row in alice_body["cost_by_context"])

    bob_response = bob.get("/api/user/dashboard")
    assert bob_response.status_code == 200, bob_response.text
    bob_body = bob_response.json()
    assert bob_body["user"]["username"] == "bob"
    assert bob_body["current"]["ip"] == "uart_core"
    assert bob_body["current"]["workflow"] == "ssot-gen"
    assert round(bob_body["metrics"]["total_cost_usd"], 4) == 0.03
    assert bob_body["metrics"]["llm_calls"] == 1
    assert [row["ip"] for row in bob_body["ip_workload"]] == ["uart_core"]
    assert {row["ip"] for row in bob_body["ip_inventory"]} == {"uart_core"}
    assert [row["workflow"] for row in bob_body["workflow_progress"]] == ["ssot-gen"]
    assert all(row["ip"] != "spi_core" for row in bob_body["cost_by_context"])


def test_user_dashboard_shell_loads_before_app(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    page = client.get("/")

    assert page.status_code == 200, page.text
    assert "user-dashboard.jsx" in page.text

    asset = client.get("/user-dashboard.jsx")
    assert asset.status_code == 200, asset.text[:200]
    assert "window.AtlasUserDashboard = AtlasUserDashboard" in asset.text
