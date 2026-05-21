import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_admin_username_registers_with_admin_role(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    registered = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"

    me = client.get("/api/users/me")
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "admin"

    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text

    page = client.get("/admin")
    assert page.status_code == 200, page.text
    assert "ATLAS Admin" in page.text


def test_admin_dashboard_serves_login_shell_without_login(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    page = client.get("/admin")
    assert page.status_code == 200, page.text
    assert "ATLAS Admin" in page.text
    assert "@babel/standalone" not in page.text
    assert 'type="text/babel"' not in page.text
    assert "admin.bundle.js" in page.text

    status = client.get("/api/admin/auth/status")
    assert status.status_code == 200, status.text
    assert status.json()["mode"] == "db"
    assert status.json()["login_required"] is True
    assert status.json()["authenticated"] is False

    users = client.get("/api/admin/users")
    assert users.status_code == 401, users.text

    bundle = client.get("/admin.bundle.js")
    assert bundle.status_code == 200, bundle.text[:200]
    assert "window.AdminPage = AdminPage" in bundle.text
    assert "React.createElement" in bundle.text
    assert "Admin Login" in bundle.text
    assert "Active User Focus" in bundle.text
    assert "IP Workload" in bundle.text
    assert "Workflow Load" in bundle.text


def test_legacy_local_admin_mode_keeps_passwordless_access(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "local")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    status = client.get("/api/admin/auth/status")
    assert status.status_code == 200, status.text
    assert status.json()["mode"] == "local"
    assert status.json()["login_required"] is False
    assert status.json()["authenticated"] is True

    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text
    assert users.json()["users"] == []

    bundle = client.get("/admin.bundle.js")
    assert bundle.status_code == 200, bundle.text[:200]
    assert "window.AdminPage = AdminPage" in bundle.text
    assert "React.createElement" in bundle.text


def test_non_admin_user_cannot_call_admin_api(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    registered = client.post(
        "/api/auth/register",
        json={"username": "member", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "user"

    users = client.get("/api/admin/users")
    assert users.status_code == 403, users.text


def test_existing_admin_username_cookie_is_promoted(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    registered = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "user"

    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text

    with AtlasDB() as db:
        assert db.get_user_by_username("admin")["role"] == "admin"


def test_db_admin_sees_team_control_plane_sessions(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "lead")
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    lead = TestClient(app)
    alice = TestClient(app)
    bob = TestClient(app)
    carol = TestClient(app)

    registered = lead.post(
        "/api/auth/register",
        json={"username": "lead", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"

    for client, username, ip_name, workflow in (
        (alice, "alice", "spi_core", "orchestrator"),
        (bob, "bob", "uart_core", "rtl-gen"),
        (carol, "carol", "dma_core", "sim_debug"),
    ):
        response = client.post(
            "/api/auth/register",
            json={"username": username, "password": "pw"},
        )
        assert response.status_code == 200, response.text
        activated = client.post(
            "/api/session/activate",
            json={"session_id": username, "ip": ip_name, "workflow": workflow},
        )
        assert activated.status_code == 200, activated.text

    sessions = lead.get("/api/admin/sessions")

    assert sessions.status_code == 200, sessions.text
    by_id = {row["id"]: row for row in sessions.json()["sessions"]}
    assert by_id["alice/spi_core/orchestrator"]["owner_username"] == "alice"
    assert by_id["alice/spi_core/orchestrator"]["ip"] == "spi_core"
    assert by_id["alice/spi_core/orchestrator"]["workflow"] == "orchestrator"
    assert by_id["bob/uart_core/rtl-gen"]["owner_username"] == "bob"
    assert by_id["bob/uart_core/rtl-gen"]["ip"] == "uart_core"
    assert by_id["bob/uart_core/rtl-gen"]["workflow"] == "rtl-gen"
    assert by_id["carol/dma_core/sim_debug"]["owner_username"] == "carol"
    assert by_id["carol/dma_core/sim_debug"]["ip"] == "dma_core"
    assert by_id["carol/dma_core/sim_debug"]["workflow"] == "sim_debug"


def test_db_admin_sees_user_active_focus_and_work_amount(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "lead")
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    app = atlas_ui.create_app()
    lead = TestClient(app)
    alice = TestClient(app)
    bob = TestClient(app)

    registered = lead.post(
        "/api/auth/register",
        json={"username": "lead", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"

    for client, username, ip_name, workflow in (
        (alice, "alice", "spi_core", "rtl-gen"),
        (bob, "bob", "uart_core", "ssot-gen"),
    ):
        response = client.post(
            "/api/auth/register",
            json={"username": username, "password": "pw"},
        )
        assert response.status_code == 200, response.text
        activated = client.post(
            "/api/session/activate",
            json={"session_id": username, "ip": ip_name, "workflow": workflow},
        )
        assert activated.status_code == 200, activated.text

    with AtlasDB() as db:
        alice_user = db.get_user_by_username("alice")
        bob_user = db.get_user_by_username("bob")
        alice_session = db.get_session("alice/spi_core/rtl-gen")
        bob_session = db.get_session("bob/uart_core/ssot-gen")
        assert alice_session is not None
        assert bob_session is not None

        alice_ws = db.upsert_workspace(
            owner_user_id=alice_user["id"],
            name="alice-ws",
            local_path="/repo/alice",
        )
        alice_ip = db.upsert_ip_block(alice_ws["id"], "spi_core", ip_type="rtl")
        alice_run = db.start_workflow_run(
            session_id=alice_session["id"],
            workspace_id=alice_ws["id"],
            ip_id=alice_ip["id"],
            workflow="rtl-gen",
            status="running",
        )
        db.record_llm_call(
            session_id=alice_session["id"],
            run_id=alice_run["id"],
            workspace_id=alice_ws["id"],
            ip_id=alice_ip["id"],
            workflow="rtl-gen",
            model="gpt-test",
            tokens_input=100,
            tokens_output=20,
            tokens_reasoning=5,
            cost_usd=0.05,
        )
        db.record_llm_call(
            session_id=alice_session["id"],
            run_id=alice_run["id"],
            workspace_id=alice_ws["id"],
            ip_id=alice_ip["id"],
            workflow="rtl-gen",
            model="gpt-test",
            tokens_input=140,
            tokens_output=30,
            tokens_reasoning=10,
            cost_usd=0.07,
        )

        bob_ws = db.upsert_workspace(
            owner_user_id=bob_user["id"],
            name="bob-ws",
            local_path="/repo/bob",
        )
        bob_ip = db.upsert_ip_block(bob_ws["id"], "uart_core", ip_type="spec")
        bob_run = db.start_workflow_run(
            session_id=bob_session["id"],
            workspace_id=bob_ws["id"],
            ip_id=bob_ip["id"],
            workflow="ssot-gen",
            status="running",
        )
        db.record_llm_call(
            session_id=bob_session["id"],
            run_id=bob_run["id"],
            workspace_id=bob_ws["id"],
            ip_id=bob_ip["id"],
            workflow="ssot-gen",
            model="gpt-test",
            tokens_input=60,
            tokens_output=15,
            tokens_reasoning=0,
            cost_usd=0.03,
        )

    users = lead.get("/api/admin/users")
    assert users.status_code == 200, users.text
    by_name = {row["username"]: row for row in users.json()["users"]}
    assert by_name["alice"]["active_ip"] == "spi_core"
    assert by_name["alice"]["active_workflow"] == "rtl-gen"
    assert by_name["alice"]["active_workflow_status"] == "running"
    assert by_name["alice"]["session_count"] == 1
    assert by_name["bob"]["active_ip"] == "uart_core"
    assert by_name["bob"]["active_workflow"] == "ssot-gen"
    assert by_name["bob"]["active_workflow_status"] == "running"

    sessions = lead.get("/api/admin/sessions")
    assert sessions.status_code == 200, sessions.text
    sessions_by_id = {row["id"]: row for row in sessions.json()["sessions"]}
    assert sessions_by_id["alice/spi_core/rtl-gen"]["owner_username"] == "alice"
    assert sessions_by_id["alice/spi_core/rtl-gen"]["ip"] == "spi_core"
    assert sessions_by_id["alice/spi_core/rtl-gen"]["workflow"] == "rtl-gen"
    assert sessions_by_id["bob/uart_core/ssot-gen"]["owner_username"] == "bob"
    assert sessions_by_id["bob/uart_core/ssot-gen"]["ip"] == "uart_core"
    assert sessions_by_id["bob/uart_core/ssot-gen"]["workflow"] == "ssot-gen"

    usage = lead.get("/api/admin/usage")
    assert usage.status_code == 200, usage.text
    usage_body = usage.json()
    usage_by_name = {row["username"]: row for row in usage_body["users"]}
    assert round(usage_by_name["alice"]["total_cost_usd"], 4) == 0.12
    assert round(usage_by_name["bob"]["total_cost_usd"], 4) == 0.03

    contexts = {
        (row["username"], row["ip"], row["workflow"]): row
        for row in usage_body["cost_by_context"]
    }
    assert contexts[("alice", "spi_core", "rtl-gen")]["calls"] == 2
    assert round(contexts[("alice", "spi_core", "rtl-gen")]["cost"], 4) == 0.12
    assert contexts[("bob", "uart_core", "ssot-gen")]["calls"] == 1
    assert round(contexts[("bob", "uart_core", "ssot-gen")]["cost"], 4) == 0.03
