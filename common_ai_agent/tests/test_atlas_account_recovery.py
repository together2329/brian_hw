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
        "ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED",
        "ATLAS_AUTH_EMAIL_DEBUG",
        "ATLAS_AUTH_EMAIL_CODE_TTL_SECONDS",
        "ATLAS_AUTH_EMAIL_CODE_MAX_ATTEMPTS",
        "ATLAS_SMTP_HOST",
        "ATLAS_SMTP_FROM",
        "ATLAS_SMTP_USERNAME",
        "ATLAS_SMTP_PASSWORD",
        "ATLAS_FEEDBACK_EMAIL_ENABLED",
        "ATLAS_FEEDBACK_EMAIL_TO",
        "ATLAS_ADMIN_EMAIL",
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


def test_registration_can_require_email_verification_code(tmp_path, monkeypatch):
    client = _client(
        tmp_path,
        monkeypatch,
        ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED="1",
        ATLAS_AUTH_EMAIL_DEBUG="1",
    )

    status = client.get("/api/auth/status")
    assert status.status_code == 200, status.text
    assert status.json()["email_required"] is True
    assert status.json()["email_verification_enabled"] is True

    requested = client.post(
        "/api/auth/email-code",
        json={
            "purpose": "register",
            "username": "alice",
            "email": "Alice@Example.com",
        },
    )
    assert requested.status_code == 200, requested.text
    code = requested.json()["verification_code"]
    assert len(code) == 6

    missing_code = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw", "email": "alice@example.com"},
    )
    assert missing_code.status_code == 400, missing_code.text
    assert missing_code.json()["detail"] == "verification code required"

    wrong_code = client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "password": "pw",
            "email": "alice@example.com",
            "verification_code": "000000",
        },
    )
    assert wrong_code.status_code == 400, wrong_code.text

    registered = client.post(
        "/api/auth/register",
        json={
            "username": "alice",
            "password": "pw",
            "email": "alice@example.com",
            "verification_code": code,
        },
    )
    assert registered.status_code == 200, registered.text
    assert registered.json()["user"]["email"] == "alice@example.com"


def test_auth_code_email_uses_admin_email_as_sender(monkeypatch):
    import core.atlas_auth as atlas_auth

    sent_messages = []

    class FakeSMTP:
        def __init__(self, host, port, timeout):
            self.host = host
            self.port = port
            self.timeout = timeout

        def __enter__(self):
            return self

        def __exit__(self, exc_type, exc, tb):
            return False

        def starttls(self):
            pass

        def login(self, username, password):
            pass

        def send_message(self, msg):
            sent_messages.append(msg)

    monkeypatch.setenv("ATLAS_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("ATLAS_ADMIN_EMAIL", "admin@example.com")
    monkeypatch.delenv("ATLAS_SMTP_FROM", raising=False)
    monkeypatch.delenv("ATLAS_SMTP_USERNAME", raising=False)
    monkeypatch.setattr(atlas_auth.smtplib, "SMTP", FakeSMTP)

    assert atlas_auth._send_auth_code_email("user@example.com", "register", "123456") is True
    assert sent_messages[0]["From"] == "admin@example.com"
    assert sent_messages[0]["To"] == "user@example.com"


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


def test_recovery_codes_find_id_and_reset_password(tmp_path, monkeypatch):
    client = _client(
        tmp_path,
        monkeypatch,
        ATLAS_ACCOUNT_RECOVERY_ENABLED="1",
        ATLAS_AUTH_EMAIL_DEBUG="1",
    )

    registered = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "oldpw", "email": "alice@example.com"},
    )
    assert registered.status_code == 200, registered.text

    id_code_response = client.post(
        "/api/auth/email-code",
        json={"purpose": "recover_id", "email": "ALICE@example.com"},
    )
    assert id_code_response.status_code == 200, id_code_response.text
    id_code = id_code_response.json()["verification_code"]

    found = client.post(
        "/api/auth/recover/id",
        json={"email": "alice@example.com", "verification_code": id_code},
    )
    assert found.status_code == 200, found.text
    assert found.json()["usernames"] == ["alice"]

    reset_code_response = client.post(
        "/api/auth/email-code",
        json={"purpose": "reset_password", "identifier": "alice"},
    )
    assert reset_code_response.status_code == 200, reset_code_response.text
    reset_code = reset_code_response.json()["verification_code"]

    reset = client.post(
        "/api/auth/reset/password",
        json={
            "identifier": "alice",
            "verification_code": reset_code,
            "password": "newpw",
        },
    )
    assert reset.status_code == 200, reset.text

    old_login = client.post("/api/auth/login", json={"username": "alice", "password": "oldpw"})
    assert old_login.status_code == 401, old_login.text

    new_login = client.post("/api/auth/login", json={"username": "alice", "password": "newpw"})
    assert new_login.status_code == 200, new_login.text


def test_feedback_can_email_admin_recipients(tmp_path, monkeypatch):
    import core.atlas_auth as atlas_auth

    sent = []

    def fake_send(to_email, subject, body):
        sent.append({"to": to_email, "subject": subject, "body": body})
        return True

    monkeypatch.setattr(atlas_auth, "_send_smtp_email", fake_send)
    client = _client(
        tmp_path,
        monkeypatch,
        ATLAS_SMTP_HOST="smtp.example.com",
        ATLAS_SMTP_FROM="atlas@example.com",
        ATLAS_FEEDBACK_EMAIL_TO="admin@example.com",
    )

    registered = client.post(
        "/api/auth/register",
        json={"username": "alice", "password": "pw", "email": "alice@example.com"},
    )
    assert registered.status_code == 200, registered.text

    feedback = client.post("/api/feedback", json={"content": "please check this"})
    assert feedback.status_code == 200, feedback.text
    assert feedback.json()["email_sent"] is True
    assert len(sent) == 1
    assert sent[0]["to"] == "admin@example.com"
    assert sent[0]["subject"] == "ATLAS feedback from alice"
    assert "please check this" in sent[0]["body"]
    assert "alice@example.com" in sent[0]["body"]
