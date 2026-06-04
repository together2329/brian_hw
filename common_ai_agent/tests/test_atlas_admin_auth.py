import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_default_admin_login_creates_fixed_admin(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    wrong = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "pw"},
    )
    assert wrong.status_code == 401, wrong.text

    registered = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "1151"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"

    me = client.get("/api/users/me")
    assert me.status_code == 200
    assert me.json()["user"]["role"] == "admin"

    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text
    ips = client.get("/api/admin/ips")
    assert ips.status_code == 200, ips.text

    page = client.get("/admin")
    assert page.status_code == 200, page.text
    assert "ATLAS Admin" in page.text


def test_default_admin_username_cannot_be_registered_with_custom_password(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    response = client.post(
        "/api/auth/register",
        json={"username": "admin", "password": "pw"},
    )
    assert response.status_code == 409, response.text
    assert response.json()["detail"] == "default admin account is fixed"


def test_standalone_admin_login_uses_admin_cookie(tmp_path, monkeypatch):
    import src.atlas_admin as atlas_admin

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.chdir(tmp_path)

    client = TestClient(atlas_admin.create_admin_app(PROJECT_ROOT))

    registered = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "1151"},
    )
    assert registered.status_code == 200, registered.text
    assert client.cookies.get("atlas_admin_session")
    assert client.cookies.get("atlas_session") is None

    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text


def test_standalone_admin_accepts_main_cookie_fallback(tmp_path, monkeypatch):
    import src.atlas_admin as atlas_admin
    from core.atlas_auth import GuestAuth, hash_password
    from core.atlas_db import AtlasDB

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.chdir(tmp_path)

    with AtlasDB() as db:
        user = db.create_user(
            "admin",
            "admin",
            hash_password("pw"),
            role="admin",
        )
    main_auth = GuestAuth(AtlasDB())
    client = TestClient(atlas_admin.create_admin_app(PROJECT_ROOT))
    client.cookies.set("atlas_session", main_auth._sign(user["id"]))

    users = client.get("/api/admin/users")
    assert users.status_code == 200, users.text
    assert client.cookies.get("atlas_admin_session") is None


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
    assert "Runtime Settings" in bundle.text
    assert "IPC Jobs" in bundle.text


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


def test_admin_runtime_reports_ipc_limits_jobs_and_scm_override(tmp_path, monkeypatch):
    import atlas_api_jobs as jobs
    import src.atlas_ui as atlas_ui

    override = tmp_path / "perforce-scm-tab.jsx"
    override.write_text("window.SCMTab = function P4Tab(){ return null; };\n", encoding="utf-8")
    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "local")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_WORKER_TRANSPORT", "ipc")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_CONCURRENT", "1")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_USER", "1")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_PER_WORKFLOW", "1")
    monkeypatch.setenv("ATLAS_IPC_WORKER_QUEUE_LIMIT", "3")
    monkeypatch.setenv("ATLAS_IPC_WORKER_TIMEOUT_SEC", "7")
    monkeypatch.setenv("ATLAS_IPC_WORKER_MAX_ATTEMPTS", "2")
    monkeypatch.setenv("ATLAS_SCM_PROVIDER", "perforce")
    monkeypatch.setenv("ATLAS_SCM_UI_OVERRIDE_PERFORCE", str(override))
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "SOURCE_ROOT", tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    running = {
        "job_id": "running-job",
        "run_id": "ipc-running-job",
        "worker": "ipc://user-a/orchestrator/rtl-gen",
        "worker_transport": "ipc",
        "workflow": "rtl-gen",
        "ip": "ip_a",
        "status": "running",
        "attempt": 1,
        "max_attempts": 2,
        "db_user_id": "user-a",
        "started_at": 10,
    }
    queued = {
        "job_id": "queued-job",
        "worker": "ipc://user-a/orchestrator/sim",
        "worker_transport": "ipc",
        "workflow": "sim",
        "ip": "ip_a",
        "status": "queued",
        "queue_reason": "ipc_global_limit",
        "attempt": 2,
        "retry_count": 1,
        "max_attempts": 2,
        "last_retry_reason": "IPC worker timeout after 7.0s",
        "db_user_id": "user-a",
        "queued_at": 20,
    }
    with jobs._jobs_lock:
        jobs._jobs.clear()
        jobs._jobs[running["job_id"]] = running
        jobs._jobs[queued["job_id"]] = queued

    try:
        client = TestClient(atlas_ui.create_app())
        response = client.get("/api/admin/runtime")
        assert response.status_code == 200, response.text
        data = response.json()

        worker_runtime = data["worker_runtime"]
        assert worker_runtime["transport"] == "ipc"
        assert worker_runtime["ipc"]["limits"] == {
            "max_concurrent": 1,
            "max_per_user": 1,
            "max_per_workflow": 1,
            "queue_limit": 3,
            "timeout_sec": 7.0,
            "max_attempts": 2,
        }
        assert worker_runtime["ipc"]["running_count"] == 1
        assert worker_runtime["ipc"]["queued_count"] == 1
        assert worker_runtime["ipc"]["available_slots"] == 0
        assert {job["job_id"] for job in worker_runtime["ipc"]["jobs"]} == {
            "running-job",
            "queued-job",
        }
        assert data["scm"]["provider"] == "perforce"
        assert data["scm"]["ui_override"]["enabled"] is True
        assert data["scm"]["ui_override"]["kind"] == "local"
        assert data["scm"]["ui_override"]["exists"] is True
    finally:
        with jobs._jobs_lock:
            jobs._jobs.clear()


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


def test_session_flow_denied_for_non_admin(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())

    # Unauthenticated request -> 401 (login required), no flow rows.
    anon = client.get("/api/admin/session-flow")
    assert anon.status_code == 401, anon.text
    assert "sessions" not in anon.json()

    # Authenticated non-admin -> 403, no flow rows.
    registered = client.post(
        "/api/auth/register",
        json={"username": "member", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "user"

    denied = client.get("/api/admin/session-flow")
    assert denied.status_code == 403, denied.text
    assert "sessions" not in denied.json()


def test_session_flow_allowed_for_admin(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_ADMIN_USERS", "admin")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    client = TestClient(atlas_ui.create_app())
    login = client.post(
        "/api/auth/login",
        json={"username": "admin", "password": "1151"},
    )
    assert login.status_code == 200, login.text
    assert login.json()["user"]["role"] == "admin"

    ok = client.get("/api/admin/session-flow")
    assert ok.status_code == 200, ok.text
    body = ok.json()
    for k in ("summary", "needs_attention", "funnel", "sessions", "ip_flow",
              "attribution_gaps", "pagination"):
        assert k in body, f"missing top-level key {k}"


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


def test_admin_can_remove_ip_pointer_without_deleting_files(tmp_path, monkeypatch):
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

    registered = lead.post(
        "/api/auth/register",
        json={"username": "lead", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"
    response = alice.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw"},
    )
    assert response.status_code == 200, response.text

    real_ip_dir = tmp_path / "alice_repo" / "spi_core"
    real_ip_dir.mkdir(parents=True)
    with AtlasDB() as db:
        alice_user = db.get_user_by_username("alice")
        workspace = db.upsert_workspace(
            owner_user_id=alice_user["id"],
            name="alice-ws",
            local_path=str(real_ip_dir.parent),
        )
        ip = db.upsert_ip_block(workspace["id"], "spi_core", ip_type="rtl")
        session = db.create_session(alice_user["id"], "spi_core", project_id="spi_core")
        db._execute(
            """
            UPDATE sessions
               SET namespace = ?, owner = ?, workspace_id = ?, ip_id = ?, ip = ?, workflow = ?
             WHERE id = ?
            """,
            (
                "alice/spi_core/ssot-gen",
                "alice",
                workspace["id"],
                ip["id"],
                "spi_core",
                "ssot-gen",
                session["id"],
            ),
        )
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="ssot-gen",
            status="running",
        )
        todo = db.upsert_workflow_todo(run["id"], title="draft SSOT", status="pending")
        db.record_todo_event(todo["id"], "in_progress")
        db.record_llm_call(
            session_id=session["id"],
            run_id=run["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="ssot-gen",
            model="gpt-test",
            tokens_input=5,
            tokens_output=2,
            cost_usd=0.01,
        )
        db.record_trace_event(
            "workflow_started",
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="ssot-gen",
            run_id=run["id"],
            actor_user_id=alice_user["id"],
        )
        ip_id = ip["id"]
        session_id = session["id"]
        run_id = run["id"]

    listed = lead.get("/api/admin/ips")
    assert listed.status_code == 200, listed.text
    listed_ips = {row["id"]: row for row in listed.json()["ips"]}
    assert listed_ips[ip_id]["ip_name"] == "spi_core"
    assert listed_ips[ip_id]["session_count"] == 1
    assert listed_ips[ip_id]["workflow_run_count"] == 1

    deleted = lead.delete(f"/api/admin/ips/{ip_id}")
    assert deleted.status_code == 200, deleted.text
    body = deleted.json()
    assert body["deleted"] is True
    assert body["filesystem_deleted"] is False
    assert body["counts"]["ip_blocks"] == 1
    assert body["counts"]["sessions"] == 1
    assert real_ip_dir.is_dir()

    with AtlasDB() as db:
        assert db.get_ip_block(ip_id) is None
        assert db.get_session(session_id) is None
        assert db._fetchone("SELECT id FROM workflow_runs WHERE id = ?", (run_id,)) is None
        assert db._fetchone("SELECT id FROM workflow_todos WHERE run_id = ?", (run_id,)) is None
        assert db._fetchone("SELECT id FROM llm_calls WHERE run_id = ?", (run_id,)) is None


def test_admin_can_remove_user_pointer_without_deleting_files(tmp_path, monkeypatch):
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
    bob = TestClient(app)

    registered = lead.post(
        "/api/auth/register",
        json={"username": "lead", "password": "pw"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["role"] == "admin"
    response = bob.post(
        "/api/auth/register",
        json={"username": "bob", "password": "pw"},
    )
    assert response.status_code == 200, response.text

    real_ip_dir = tmp_path / "bob_repo" / "uart_core"
    real_ip_dir.mkdir(parents=True)
    with AtlasDB() as db:
        bob_user = db.get_user_by_username("bob")
        workspace = db.upsert_workspace(
            owner_user_id=bob_user["id"],
            name="bob-ws",
            local_path=str(real_ip_dir.parent),
        )
        ip = db.upsert_ip_block(workspace["id"], "uart_core", ip_type="spec")
        session = db.create_session(bob_user["id"], "uart_core", project_id="uart_core")
        db._execute(
            """
            UPDATE sessions
               SET namespace = ?, owner = ?, workspace_id = ?, ip_id = ?, ip = ?, workflow = ?
             WHERE id = ?
            """,
            (
                "bob/uart_core/default",
                "bob",
                workspace["id"],
                ip["id"],
                "uart_core",
                "default",
                session["id"],
            ),
        )
        run = db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="default",
            status="running",
        )
        db.record_trace_event(
            "chat",
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip["id"],
            workflow="default",
            run_id=run["id"],
            actor_user_id=bob_user["id"],
        )
        user_id = bob_user["id"]
        workspace_id = workspace["id"]
        ip_id = ip["id"]
        session_id = session["id"]

    self_delete = lead.delete(f"/api/admin/users/{registered.json()['user']['id']}")
    assert self_delete.status_code == 400, self_delete.text

    deleted = lead.delete(f"/api/admin/users/{user_id}")
    assert deleted.status_code == 200, deleted.text
    body = deleted.json()
    assert body["deleted"] is True
    assert body["filesystem_deleted"] is False
    assert body["username"] == "bob"
    assert body["counts"]["users"] == 1
    assert body["counts"]["ip_blocks"] == 1
    assert body["counts"]["sessions"] == 1
    assert real_ip_dir.is_dir()

    with AtlasDB() as db:
        assert db.get_user(user_id) is None
        assert db.get_workspace(workspace_id) is None
        assert db.get_ip_block(ip_id) is None
        assert db.get_session(session_id) is None


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
