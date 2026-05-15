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
