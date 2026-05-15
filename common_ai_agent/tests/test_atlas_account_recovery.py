import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def _client(tmp_path, monkeypatch, **env):
    import src.atlas_ui as atlas_ui

    for key in (
        "ATLAS_ACCOUNT_RECOVERY_ENABLED",
        "ATLAS_ACCOUNT_RECOVERY_DEBUG",
        "ATLAS_ACCOUNT_RECOVERY_EMAIL_ENABLED",
        "ATLAS_AUTH_EMAIL_REQUIRED",
        "ATLAS_SMTP_HOST",
        "ATLAS_SMTP_FROM",
        "ATLAS_SMTP_USERNAME",
        "ATLAS_SMTP_PASSWORD",
    ):
        monkeypatch.delenv(key, raising=False)
    for key, value in env.items():
        monkeypatch.setenv(key, str(value))

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)
    return TestClient(atlas_ui.create_app())


def test_account_recovery_is_disabled_by_default(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch)

    status = client.get("/api/auth/status")
    assert status.status_code == 200, status.text
    assert status.json()["recovery_enabled"] is False
    assert status.json()["email_required"] is False

    registered = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw", "email": "Alice@Example.com"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["email"] == "alice@example.com"

    recover = client.post("/api/auth/recover/id", json={"email": "alice@example.com"})
    assert recover.status_code == 404, recover.text


def test_recovery_enabled_requires_email_and_keeps_it_unique(tmp_path, monkeypatch):
    client = _client(tmp_path, monkeypatch, ATLAS_ACCOUNT_RECOVERY_ENABLED="1")

    missing = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw"},
    )
    assert missing.status_code == 400, missing.text
    assert missing.json()["detail"] == "email required"

    registered = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw", "email": "Alice@Example.com"},
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["email"] == "alice@example.com"

    duplicate = client.post(
        "/api/auth/register",
        json={"username": "alice2", "password": "pw", "email": "alice@example.com"},
    )
    assert duplicate.status_code == 409, duplicate.text
    assert duplicate.json()["detail"] == "email already exists"


def test_debug_recovery_finds_id_and_resets_password(tmp_path, monkeypatch):
    client = _client(
        tmp_path,
        monkeypatch,
        ATLAS_ACCOUNT_RECOVERY_ENABLED="1",
        ATLAS_ACCOUNT_RECOVERY_DEBUG="1",
    )

    registered = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "oldpw", "email": "alice@example.com"},
    )
    assert registered.status_code == 200, registered.text

    find_id = client.post("/api/auth/recover/id", json={"email": "ALICE@example.com"})
    assert find_id.status_code == 200, find_id.text
    assert find_id.json()["usernames"] == ["alice"]
    assert find_id.json()["email_sent"] is False

    requested = client.post("/api/auth/recover/password", json={"identifier": "alice"})
    assert requested.status_code == 200, requested.text
    token = requested.json()["reset_token"]
    assert token

    reset = client.post("/api/auth/reset/password", json={"token": token, "password": "newpw"})
    assert reset.status_code == 200, reset.text

    old_login = client.post("/api/auth/login", json={"username": "alice", "password": "oldpw"})
    assert old_login.status_code == 401, old_login.text

    new_login = client.post("/api/auth/login", json={"username": "alice", "password": "newpw"})
    assert new_login.status_code == 200, new_login.text

    reuse = client.post("/api/auth/reset/password", json={"token": token, "password": "again"})
    assert reuse.status_code == 400, reuse.text
