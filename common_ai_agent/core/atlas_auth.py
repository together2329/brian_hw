"""
Atlas Authentication Layer

Username+password authentication for Atlas UI. Uses HMAC-signed cookies
(no JWT) so the local tool stays dependency-light. There is no guest
fallback — every request must come from a logged-in user; unauthenticated
requests pass through with scope['user']=None and are rejected by
upstream route gates.
"""

from __future__ import annotations

import hmac
import hashlib
import os
import secrets
import smtplib
import time
from email.message import EmailMessage
from pathlib import Path
from typing import Any, Dict, Optional, TYPE_CHECKING

from core.atlas_db import AtlasDB

try:
    import bcrypt
    _HAS_BCRYPT = True
except Exception:  # pragma: no cover
    _HAS_BCRYPT = False

if TYPE_CHECKING:
    from fastapi import FastAPI, Request, Response, HTTPException
    from starlette.requests import Request as StarletteRequest
else:
    try:
        from fastapi import FastAPI, Response, HTTPException
        from starlette.requests import Request
        from starlette.requests import Request as StarletteRequest
    except Exception:  # pragma: no cover
        FastAPI = None  # type: ignore
        Request = None  # type: ignore
        Response = None  # type: ignore
        HTTPException = None  # type: ignore
        StarletteRequest = None  # type: ignore

_COOKIE_NAME = "atlas_session"
_MAX_AGE = 90 * 24 * 60 * 60
_DEFAULT_ADMIN_USERS = "admin"
_DEFAULT_ADMIN_USERNAME = "admin"
_DEFAULT_ADMIN_PASSWORD = "1151"
_LOCAL_ADMIN_MODES = {"local", "open", "legacy", "bypass", "none", "off"}
_TRUTHY = {"1", "true", "yes", "on"}
_FALSY = {"0", "false", "no", "off"}
_DEFAULT_RECOVERY_TTL_SECONDS = 30 * 60
_DEFAULT_EMAIL_CODE_TTL_SECONDS = 10 * 60
_DEFAULT_EMAIL_CODE_MAX_ATTEMPTS = 6
_EMAIL_CODE_PURPOSES = {"register", "recover_id", "reset_password"}


def _default_cookie_secret() -> str:
    """Return a stable per-user cookie secret for backend restarts."""
    env_secret = os.environ.get("ATLAS_COOKIE_SECRET") or os.environ.get("ATLAS_AUTH_SECRET")
    if env_secret:
        return env_secret
    try:
        secret_path = Path(os.environ.get("ATLAS_COOKIE_SECRET_FILE") or Path.home() / ".common_ai_agent" / "atlas_cookie_secret")
        secret_path.parent.mkdir(parents=True, exist_ok=True)
        if secret_path.is_file():
            secret = secret_path.read_text(encoding="utf-8").strip()
            if secret:
                return secret
        secret = os.urandom(32).hex()
        secret_path.write_text(secret, encoding="utf-8")
        try:
            secret_path.chmod(0o600)
        except Exception:
            pass
        return secret
    except Exception:
        return os.urandom(32).hex()


def _now() -> float:
    return time.time()


def _admin_usernames() -> set[str]:
    """Usernames that should be treated as Atlas admins.

    ATLAS_ADMIN_USERS is a comma-separated bootstrap list. The default keeps
    the local "admin" account useful without requiring manual SQLite edits.
    Set ATLAS_ADMIN_USERS="" to disable this bootstrap behavior.
    """
    raw = os.environ.get("ATLAS_ADMIN_USERS", _DEFAULT_ADMIN_USERS)
    return {item.strip().lower() for item in raw.split(",") if item.strip()}


def _env_flag(name: str, default: bool = False) -> bool:
    raw = os.environ.get(name)
    if raw is None:
        return default
    value = raw.strip().lower()
    if value in _TRUTHY:
        return True
    if value in _FALSY:
        return False
    return default


def _env_int(name: str, default: int) -> int:
    raw = os.environ.get(name)
    if raw is None:
        return default
    try:
        value = int(raw)
    except ValueError:
        return default
    return value if value > 0 else default


def account_recovery_enabled() -> bool:
    return _env_flag("ATLAS_ACCOUNT_RECOVERY_ENABLED", False)


def account_recovery_debug_enabled() -> bool:
    return _env_flag("ATLAS_ACCOUNT_RECOVERY_DEBUG", False)


def account_recovery_email_enabled() -> bool:
    return account_recovery_enabled() and _env_flag("ATLAS_ACCOUNT_RECOVERY_EMAIL_ENABLED", False)


def auth_email_verification_enabled() -> bool:
    return _env_flag("ATLAS_AUTH_EMAIL_VERIFICATION_ENABLED", False)


def auth_email_debug_enabled() -> bool:
    return _env_flag("ATLAS_AUTH_EMAIL_DEBUG", False) or account_recovery_debug_enabled()


def auth_email_code_ttl_seconds() -> int:
    return _env_int("ATLAS_AUTH_EMAIL_CODE_TTL_SECONDS", _DEFAULT_EMAIL_CODE_TTL_SECONDS)


def auth_email_code_max_attempts() -> int:
    return _env_int("ATLAS_AUTH_EMAIL_CODE_MAX_ATTEMPTS", _DEFAULT_EMAIL_CODE_MAX_ATTEMPTS)


def registration_email_required() -> bool:
    return (
        _env_flag("ATLAS_AUTH_EMAIL_REQUIRED", False)
        or account_recovery_enabled()
        or auth_email_verification_enabled()
    )


def _smtp_configured() -> bool:
    return bool(
        os.environ.get("ATLAS_SMTP_HOST")
        and (
            os.environ.get("ATLAS_SMTP_FROM")
            or os.environ.get("ATLAS_ADMIN_EMAIL")
            or os.environ.get("ATLAS_SMTP_USERNAME")
        )
    )


def auth_feature_status() -> Dict[str, Any]:
    return {
        "recovery_enabled": account_recovery_enabled(),
        "recovery_email_enabled": account_recovery_email_enabled(),
        "recovery_email_configured": account_recovery_email_enabled() and _smtp_configured(),
        "email_required": registration_email_required(),
        "email_verification_enabled": auth_email_verification_enabled(),
        "email_delivery_configured": _smtp_configured(),
        "email_code_ttl_seconds": auth_email_code_ttl_seconds(),
        "default_admin_enabled": _default_admin_enabled(),
        "default_admin_username": _default_admin_username(),
    }


def _normalize_email(email: Any) -> str:
    value = str(email or "").strip().lower()
    if not value:
        return ""
    if "@" not in value or value.startswith("@") or value.endswith("@"):
        return ""
    return value


def _hash_recovery_token(token: str) -> str:
    return hashlib.sha256(token.encode("utf-8")).hexdigest()


def _normalize_email_code(code: Any) -> str:
    return "".join(ch for ch in str(code or "").strip() if ch.isdigit())


def _new_email_code() -> str:
    return f"{secrets.randbelow(1_000_000):06d}"


def _hash_email_code(secret: str, purpose: str, email: str, code: str) -> str:
    normalized = _normalize_email(email)
    normalized_code = _normalize_email_code(code)
    payload = f"{str(purpose or '').strip().lower()}:{normalized}:{normalized_code}"
    return hmac.new(str(secret or "").encode("utf-8"), payload.encode("utf-8"), hashlib.sha256).hexdigest()


def _consume_email_code(auth: "GuestAuth", purpose: str, email: str, code: str) -> bool:
    normalized_email = _normalize_email(email)
    normalized_code = _normalize_email_code(code)
    if not normalized_email or not normalized_code:
        return False
    return auth.db.consume_auth_email_code(
        purpose,
        normalized_email,
        _hash_email_code(auth.cookie_secret, purpose, normalized_email, normalized_code),
        max_attempts=auth_email_code_max_attempts(),
    )


def _mask_email(email: str) -> str:
    normalized = _normalize_email(email)
    if not normalized or "@" not in normalized:
        return ""
    local, domain = normalized.split("@", 1)
    if len(local) <= 2:
        return f"{local[:1]}***@{domain}"
    return f"{local[:2]}***@{domain}"


def _password_reset_url(token: str) -> str:
    explicit = os.environ.get("ATLAS_PASSWORD_RESET_URL", "").strip()
    if explicit:
        return explicit.replace("{token}", token)
    base = os.environ.get("ATLAS_PUBLIC_BASE_URL", "").strip().rstrip("/")
    if base:
        return f"{base}/?reset_token={token}"
    return f"/?reset_token={token}"


def _send_smtp_email(to_email: str, subject: str, body: str) -> bool:
    if not _smtp_configured():
        return False

    host = os.environ.get("ATLAS_SMTP_HOST", "").strip()
    port = _env_int("ATLAS_SMTP_PORT", 587)
    username = os.environ.get("ATLAS_SMTP_USERNAME", "").strip()
    password = os.environ.get("ATLAS_SMTP_PASSWORD", "")
    sender = (
        os.environ.get("ATLAS_SMTP_FROM", "").strip()
        or os.environ.get("ATLAS_ADMIN_EMAIL", "").strip()
        or username
    )
    use_tls = _env_flag("ATLAS_SMTP_TLS", True)

    msg = EmailMessage()
    msg["From"] = sender
    msg["To"] = to_email
    msg["Subject"] = subject
    msg.set_content(body)

    with smtplib.SMTP(host, port, timeout=10) as smtp:
        if use_tls:
            smtp.starttls()
        if username:
            smtp.login(username, password)
        smtp.send_message(msg)
    return True


def _send_recovery_email(to_email: str, subject: str, body: str) -> bool:
    if not account_recovery_email_enabled():
        return False
    return _send_smtp_email(to_email, subject, body)


def _send_auth_code_email(to_email: str, purpose: str, code: str) -> bool:
    purpose_labels = {
        "register": "ATLAS signup verification",
        "recover_id": "ATLAS ID recovery verification",
        "reset_password": "ATLAS password reset verification",
    }
    subject = purpose_labels.get(purpose, "ATLAS verification code")
    body = (
        f"Your ATLAS verification code is: {code}\n\n"
        f"This code expires in {auth_email_code_ttl_seconds() // 60} minutes.\n"
        "If you did not request this, ignore this email.\n"
    )
    return _send_smtp_email(to_email, subject, body)


def feedback_email_recipients(db: AtlasDB = None) -> list[str]:
    """Configured admin feedback recipients plus DB admin emails."""
    raw = os.environ.get("ATLAS_FEEDBACK_EMAIL_TO") or os.environ.get("ATLAS_ADMIN_EMAIL") or ""
    recipients: list[str] = []
    for item in raw.split(","):
        email = _normalize_email(item)
        if email and email not in recipients:
            recipients.append(email)
    if db is not None:
        try:
            rows = db._fetchall(
                "SELECT email FROM users WHERE role = 'admin' AND email IS NOT NULL AND email != ''"
            )
            for row in rows:
                email = _normalize_email(row["email"])
                if email and email not in recipients:
                    recipients.append(email)
        except Exception:
            pass
    return recipients


def send_feedback_email(db: AtlasDB, user: Dict[str, Any], feedback_id: str, content: str) -> bool:
    """Notify admins about new user feedback without blocking feedback storage."""
    if not _env_flag("ATLAS_FEEDBACK_EMAIL_ENABLED", True) or not _smtp_configured():
        return False
    recipients = feedback_email_recipients(db)
    if not recipients:
        return False
    username = str((user or {}).get("username") or (user or {}).get("id") or "unknown")
    user_email = str((user or {}).get("email") or "")
    subject = f"ATLAS feedback from {username}"
    body = (
        "A user submitted ATLAS feedback.\n\n"
        f"Feedback ID: {feedback_id}\n"
        f"User: {username}\n"
        f"Email: {user_email or '-'}\n\n"
        f"{content}\n"
    )
    sent = False
    for recipient in recipients:
        try:
            sent = _send_smtp_email(recipient, subject, body) or sent
        except Exception:
            continue
    return sent


def is_local_admin_mode() -> bool:
    """Return True when legacy passwordless local admin is explicitly enabled.

    The default admin policy is DB-backed username/password auth. The old
    desktop-local open-admin behavior remains available for compatibility via
    ATLAS_ADMIN_AUTH_MODE=local or ATLAS_ADMIN_LOGIN_REQUIRED=0.
    """
    mode = os.environ.get("ATLAS_ADMIN_AUTH_MODE", "").strip().lower()
    if mode in _LOCAL_ADMIN_MODES:
        return True
    if _env_flag("ATLAS_LOCAL_ADMIN", False) or _env_flag("ATLAS_ADMIN_BYPASS", False):
        return True
    if os.environ.get("ATLAS_ADMIN_LOGIN_REQUIRED") is not None:
        return not _env_flag("ATLAS_ADMIN_LOGIN_REQUIRED", True)
    return False


def local_admin_user() -> Dict[str, Any]:
    """Synthetic local admin identity for explicit passwordless local mode."""
    return {
        "id": "local-admin",
        "username": "local-admin",
        "display_name": "Local Admin",
        "email": "",
        "role": "admin",
        "created_at": None,
        "last_login_at": None,
    }


def admin_auth_mode() -> str:
    return "local" if is_local_admin_mode() else "db"


def is_admin_user(user: Optional[Dict[str, Any]]) -> bool:
    return bool(user and str(user.get("role") or "").strip().lower() == "admin")


def admin_user_exists(db: AtlasDB) -> bool:
    """Return whether the DB already has a usable admin login."""
    row = db._fetchone("SELECT 1 FROM users WHERE role = 'admin' LIMIT 1")
    if row is not None:
        return True
    names = sorted(_admin_usernames())
    if not names:
        return False
    placeholders = ",".join("?" for _ in names)
    row = db._fetchone(
        f"SELECT 1 FROM users WHERE lower(username) IN ({placeholders}) LIMIT 1",
        tuple(names),
    )
    return row is not None


def admin_auth_status(db: AtlasDB, user: Optional[Dict[str, Any]]) -> Dict[str, Any]:
    """Small JSON-serializable status block for the admin login screen."""
    if is_local_admin_mode():
        return {
            "mode": "local",
            "login_required": False,
            "authenticated": True,
            "admin_user_exists": admin_user_exists(db),
            **auth_feature_status(),
            "user": {
                "id": (user or {}).get("id") or "local-admin",
                "username": (user or {}).get("username") or "local-admin",
                "display_name": (user or {}).get("display_name") or "Local Admin",
                "role": "admin",
            },
        }
    return {
        "mode": "db",
        "login_required": True,
        "authenticated": is_admin_user(user),
        "admin_user_exists": admin_user_exists(db),
        "bootstrap_admin_users": sorted(_admin_usernames()),
        **auth_feature_status(),
        "user": _sanitize_user(user) if is_admin_user(user) else None,
    }


def _bootstrap_role_for_username(username: str) -> str:
    if username.strip().lower() in _admin_usernames():
        return "admin"
    return "user"


def _default_admin_enabled() -> bool:
    if not _env_flag("ATLAS_DEFAULT_ADMIN_ENABLED", True):
        return False
    return _default_admin_username().lower() in _admin_usernames()


def _default_admin_username() -> str:
    return (os.environ.get("ATLAS_DEFAULT_ADMIN_USERNAME") or _DEFAULT_ADMIN_USERNAME).strip() or _DEFAULT_ADMIN_USERNAME


def _default_admin_password() -> str:
    return os.environ.get("ATLAS_DEFAULT_ADMIN_PASSWORD", _DEFAULT_ADMIN_PASSWORD)


def _is_default_admin_username(username: str) -> bool:
    return str(username or "").strip().lower() == _default_admin_username().lower()


def hash_password(password: str) -> str:
    """Hash password with bcrypt (if available) or PBKDF2 fallback."""
    pw_bytes = password.encode("utf-8")
    if _HAS_BCRYPT:
        salt = bcrypt.gensalt()
        hashed = bcrypt.hashpw(pw_bytes, salt)
        return hashed.decode("utf-8")
    salt = os.urandom(16)
    hashed = hashlib.pbkdf2_hmac("sha256", pw_bytes, salt, 100_000)
    return f"pbkdf2_sha256${salt.hex()}${hashed.hex()}"


def _verify_pbkdf2(password: str, password_hash: str) -> bool:
    try:
        _, salt_hex, hash_hex = password_hash.split("$")
        salt = bytes.fromhex(salt_hex)
        expected = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt, 100_000)
        return hmac.compare_digest(expected.hex(), hash_hex)
    except Exception:
        return False


def verify_password(password: str, password_hash: str) -> bool:
    """Verify password against hash (bcrypt or PBKDF2)."""
    if _HAS_BCRYPT:
        if not password_hash.startswith("$2"):
            return _verify_pbkdf2(password, password_hash)
        return bcrypt.checkpw(password.encode("utf-8"), password_hash.encode("utf-8"))
    return _verify_pbkdf2(password, password_hash)


def _ensure_default_admin_login_user(db: AtlasDB, username: str, password: str) -> Optional[Dict[str, Any]]:
    """Create the fixed first-run admin only after the correct default login."""
    if not _default_admin_enabled() or not _is_default_admin_username(username):
        return None
    if password != _default_admin_password():
        return None
    existing = db.get_user_by_username(_default_admin_username())
    if existing is not None:
        refreshed = existing
        if existing.get("role") != "admin":
            refreshed = db.set_user_role(existing["id"], "admin") or refreshed
        if not verify_password(password, str(refreshed.get("password_hash") or "")):
            refreshed = db.update_user_password(refreshed["id"], hash_password(password)) or refreshed
        return refreshed
    email = _normalize_email(os.environ.get("ATLAS_ADMIN_EMAIL", ""))
    try:
        return db.create_user(
            _default_admin_username(),
            _default_admin_username(),
            hash_password(password),
            role="admin",
            email=email,
        )
    except Exception:
        return db.get_user_by_username(_default_admin_username())


class GuestAuth:
    """HMAC-signed cookie authentication. Class name kept for compatibility;
    no longer creates guest users (legacy auto-guest path removed)."""

    def __init__(
        self,
        db: AtlasDB,
        cookie_secret: Optional[str] = None,
        cookie_name: Optional[str] = None,
        fallback_cookie_names: tuple[str, ...] = (),
    ):
        self.db = db
        self.cookie_secret = cookie_secret or _default_cookie_secret()
        self.cookie_name = cookie_name or _COOKIE_NAME
        self.fallback_cookie_names = tuple(
            name for name in fallback_cookie_names
            if name and name != self.cookie_name
        )

    def _sign(self, user_id: str) -> str:
        sig = hmac.new(self.cookie_secret.encode(), user_id.encode(), hashlib.sha256).hexdigest()[:16]
        return f"{user_id}:{sig}"

    def _verify(self, cookie_value: str) -> Optional[str]:
        try:
            user_id, _sig = cookie_value.split(":", 1)
            expected = self._sign(user_id)
            if hmac.compare_digest(expected, cookie_value):
                return user_id
        except Exception:
            pass
        return None

    def _set_cookie(self, response, user_id: str) -> None:
        if response is None:
            return
        response.set_cookie(
            key=self.cookie_name,
            value=self._sign(user_id),
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=_MAX_AGE,
        )

    def _clear_cookie(self, response) -> None:
        if response is None:
            return
        response.delete_cookie(key=self.cookie_name)

    def get_user_from_cookie(self, request) -> Optional[Dict[str, Any]]:
        """Extract and verify user from request cookies."""
        if request is None:
            return None
        for cookie_name in (self.cookie_name, *self.fallback_cookie_names):
            cookie_value = request.cookies.get(cookie_name)
            if not cookie_value:
                continue
            user_id = self._verify(cookie_value)
            if user_id:
                return self.db.get_user(user_id)
        return None

    def ensure_bootstrap_role(self, user: Optional[Dict[str, Any]]) -> Optional[Dict[str, Any]]:
        """Apply configured bootstrap admin role to an existing user."""
        if not user and is_local_admin_mode():
            return local_admin_user()
        if not user:
            return user
        expected_role = _bootstrap_role_for_username(str(user.get("username") or ""))
        if expected_role == "admin" and user.get("role") != "admin":
            refreshed = self.db.set_user_role(str(user["id"]), "admin")
            return refreshed or {**user, "role": "admin"}
        return user

async def get_current_user(request: Request) -> dict:
    """FastAPI dependency that extracts user from cookie."""
    scoped_user = request.scope.get("user")
    if scoped_user is not None:
        return scoped_user
    auth: Optional[GuestAuth] = getattr(request.app.state, "auth", None)
    if auth is None:
        raise HTTPException(status_code=401, detail="Authentication not configured")
    user = auth.get_user_from_cookie(request)
    if user is None and is_local_admin_mode():
        return local_admin_user()
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


_PUBLIC_PATHS = {
    "/",
    "/index.html",
    "/admin",
    "/healthz",
    "/favicon.ico",
    "/api/admin/auth/status",
}
# NOTE: "/git/" is NOT a static public prefix. AuthMiddleware treats it as public
# only when git_anon_read_enabled() is true — which is the DEFAULT (anonymous
# fetch/clone allowed). Set ATLAS_GIT_ANON_READ=0 to require an authenticated,
# per-IP-authorized session for /git/ fetch too. PUSH always requires auth.
_PUBLIC_PREFIXES = ("/static/", "/assets/", "/api/auth/")
_PUBLIC_EXT = {"js", "jsx", "css", "html", "png", "jpg", "jpeg", "svg", "ico", "woff", "woff2", "ttf", "map"}


def git_anon_read_enabled() -> bool:
    """DEFAULT ON: anonymous git fetch/clone over /git/ is allowed unless the
    operator explicitly disables it with ATLAS_GIT_ANON_READ=0 (or false/no/off).

    With it on (the default), `git clone http://host/git/<ip>.git` works with no
    credentials for ANY IP bare repo reachable on the port. PUSH
    (git-receive-pack) ALWAYS still requires authentication. Set
    ATLAS_GIT_ANON_READ=0 to require an authenticated, per-IP-authorized session
    for fetch/clone too.
    """
    raw = (os.environ.get("ATLAS_GIT_ANON_READ", "") or "").strip().lower()
    if raw in ("0", "false", "no", "off"):
        return False
    if raw in ("1", "true", "yes", "on"):
        return True
    # Unset: anonymous cross-tenant fetch/clone of ANY IP's bare repo is a
    # disclosure in multi-user deployments, so default OFF there. Single-user/
    # local mode keeps the convenient default-ON. Operators can still force
    # either way with ATLAS_GIT_ANON_READ=1/0.
    mu = (os.environ.get("ATLAS_MULTI_USER", "1") or "1").strip().lower()
    multi_user = mu not in ("0", "false", "no", "off")
    return not multi_user


class AuthMiddleware:
    """Starlette middleware: attach scope['user'] from cookie, 401 anything
    non-public when unauthenticated."""

    def __init__(self, app, auth: GuestAuth):
        self.app = app
        self.auth = auth

    async def __call__(self, scope, receive, send):
        if scope["type"] != "http":
            await self.app(scope, receive, send)
            return

        path = scope.get("path", "")
        request = StarletteRequest(scope, receive)
        scope["user"] = self.auth.ensure_bootstrap_role(self.auth.get_user_from_cookie(request))

        if (
            self._is_public(path)
            or scope["user"] is not None
            or (path.startswith("/api/admin/") and is_local_admin_mode())
        ):
            await self.app(scope, receive, send)
            return

        await self._send_401(send)

    @staticmethod
    def _is_public(path: str) -> bool:
        if path in _PUBLIC_PATHS or path.startswith(_PUBLIC_PREFIXES):
            return True
        # Opt-in anonymous git read: let /git/ through so the proxy can serve
        # fetch/clone without a cookie (the proxy still blocks anonymous push).
        if path.startswith("/git/") and git_anon_read_enabled():
            return True
        if "." in path and path.rsplit(".", 1)[-1].lower() in _PUBLIC_EXT:
            return True
        return False

    @staticmethod
    async def _send_401(send) -> None:
        body = b'{"detail":"login required"}'
        await send({
            "type": "http.response.start",
            "status": 401,
            "headers": [
                (b"content-type", b"application/json"),
                (b"content-length", str(len(body)).encode()),
            ],
        })
        await send({"type": "http.response.body", "body": body})


def _sanitize_user(user: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "id": user.get("id"),
        "username": user.get("username"),
        "display_name": user.get("display_name"),
        "email": user.get("email"),
        "role": user.get("role"),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }


def create_auth_endpoints(app: FastAPI, auth: GuestAuth) -> None:
    """Register auth endpoints on the FastAPI app."""

    @app.get("/api/auth/status")
    async def auth_status():
        return auth_feature_status()

    @app.post("/api/auth/email-code")
    async def auth_email_code(request: Request):
        body = await request.json()
        purpose = str(body.get("purpose", "")).strip().lower()
        if purpose not in _EMAIL_CODE_PURPOSES:
            raise HTTPException(status_code=400, detail="valid purpose required")
        if purpose == "register" and not auth_email_verification_enabled():
            raise HTTPException(status_code=404, detail="email verification disabled")
        if purpose in {"recover_id", "reset_password"} and not account_recovery_enabled():
            raise HTTPException(status_code=404, detail="account recovery disabled")

        username = str(body.get("username", "")).strip()
        identifier = str(
            body.get("identifier")
            or body.get("username")
            or body.get("email")
            or ""
        ).strip()
        email = _normalize_email(body.get("email", ""))
        target_email = email
        target_user: Optional[Dict[str, Any]] = None

        if purpose == "register":
            if not username:
                raise HTTPException(status_code=400, detail="username required")
            if not target_email:
                raise HTTPException(status_code=400, detail="valid email required")
            if auth.db.get_user_by_username(username) is not None:
                raise HTTPException(status_code=409, detail="username already exists")
            if auth.db.get_user_by_email(target_email) is not None:
                raise HTTPException(status_code=409, detail="email already exists")
        elif purpose == "recover_id":
            if not target_email:
                raise HTTPException(status_code=400, detail="valid email required")
            target_user = auth.db.get_user_by_email(target_email)
        else:
            if not identifier:
                raise HTTPException(status_code=400, detail="username or email required")
            target_user = auth.db.get_user_by_email(identifier) if "@" in identifier else auth.db.get_user_by_username(identifier)
            target_email = _normalize_email((target_user or {}).get("email", ""))

        email_sent = False
        debug_code = None
        expires_at = None
        if target_email and (purpose == "register" or target_user is not None):
            code = _new_email_code()
            now = _now()
            expires_at = now + auth_email_code_ttl_seconds()
            auth.db.create_auth_email_code(
                purpose,
                target_email,
                _hash_email_code(auth.cookie_secret, purpose, target_email, code),
                expires_at,
                username=username,
                identifier=identifier,
            )
            try:
                email_sent = _send_auth_code_email(target_email, purpose, code)
            except Exception:
                email_sent = False
            if auth_email_debug_enabled():
                debug_code = code

        result: Dict[str, Any] = {
            "ok": True,
            "email_sent": email_sent,
            "email_hint": _mask_email(target_email),
        }
        if expires_at is not None:
            result["expires_at"] = expires_at
        if debug_code:
            result["verification_code"] = debug_code
        return result

    @app.post("/api/auth/register")
    async def auth_register(request: Request, response: Response):
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        display_name = str(body.get("display_name", "")).strip() or username
        raw_email = body.get("email", "")
        email = _normalize_email(raw_email)

        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password required")
        if raw_email and not email:
            raise HTTPException(status_code=400, detail="valid email required")
        if registration_email_required() and not email:
            raise HTTPException(status_code=400, detail="email required")
        if (
            _default_admin_enabled()
            and _is_default_admin_username(username)
            and auth.db.get_user_by_username(username) is None
            and password != _default_admin_password()
        ):
            raise HTTPException(status_code=409, detail="default admin account is fixed")

        if auth.db.get_user_by_username(username) is not None:
            raise HTTPException(status_code=409, detail="username already exists")
        if email and auth.db.get_user_by_email(email) is not None:
            raise HTTPException(status_code=409, detail="email already exists")
        if auth_email_verification_enabled():
            code = _normalize_email_code(body.get("verification_code", ""))
            if not code:
                raise HTTPException(status_code=400, detail="verification code required")
            if not _consume_email_code(auth, "register", email, code):
                raise HTTPException(status_code=400, detail="invalid or expired verification code")

        user = auth.db.create_user(
            username,
            display_name,
            hash_password(password),
            role=_bootstrap_role_for_username(username),
            email=email,
        )
        auth._set_cookie(response, user["id"])
        return {"user": _sanitize_user(user)}

    @app.post("/api/auth/login")
    async def auth_login(request: Request, response: Response):
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))

        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password required")

        user = auth.db.get_user_by_username(username)
        if (
            _default_admin_enabled()
            and _is_default_admin_username(username)
            and password == _default_admin_password()
        ):
            user = _ensure_default_admin_login_user(auth.db, username, password)
        if user is None or not verify_password(password, user.get("password_hash") or ""):
            raise HTTPException(status_code=401, detail="invalid credentials")

        user = auth.ensure_bootstrap_role(user) or user
        auth.db._execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (_now(), user["id"]),
        )
        auth._set_cookie(response, user["id"])
        return {"user": _sanitize_user(user)}

    @app.post("/api/auth/recover/id")
    async def auth_recover_id(request: Request):
        if not account_recovery_enabled():
            raise HTTPException(status_code=404, detail="account recovery disabled")

        body = await request.json()
        email = _normalize_email(body.get("email", ""))
        if not email:
            raise HTTPException(status_code=400, detail="valid email required")

        user = auth.db.get_user_by_email(email)
        email_sent = False
        verified = False
        code = _normalize_email_code(body.get("verification_code", ""))
        if code:
            verified = _consume_email_code(auth, "recover_id", email, code)
            if not verified:
                raise HTTPException(status_code=400, detail="invalid or expired verification code")
        if user is not None and not verified:
            try:
                email_sent = _send_recovery_email(
                    email,
                    "ATLAS user ID recovery",
                    f"Your ATLAS user ID is: {user.get('username')}\n",
                )
            except Exception:
                email_sent = False

        result: Dict[str, Any] = {"ok": True, "email_sent": email_sent}
        if verified or account_recovery_debug_enabled():
            result["usernames"] = [user["username"]] if user is not None else []
        return result

    @app.post("/api/auth/recover/password")
    async def auth_recover_password(request: Request):
        if not account_recovery_enabled():
            raise HTTPException(status_code=404, detail="account recovery disabled")

        body = await request.json()
        identifier = str(
            body.get("identifier")
            or body.get("username")
            or body.get("email")
            or ""
        ).strip()
        if not identifier:
            raise HTTPException(status_code=400, detail="username or email required")

        user = auth.db.get_user_by_email(identifier) if "@" in identifier else auth.db.get_user_by_username(identifier)
        token = None
        reset_url = None
        expires_at = None
        email_sent = False
        if user is not None and user.get("email"):
            token = secrets.token_urlsafe(32)
            reset_url = _password_reset_url(token)
            now = _now()
            expires_at = now + _env_int("ATLAS_ACCOUNT_RECOVERY_TOKEN_TTL_SECONDS", _DEFAULT_RECOVERY_TTL_SECONDS)
            auth.db.set_user_password_reset(
                user["id"],
                _hash_recovery_token(token),
                expires_at,
                requested_at=now,
            )
            try:
                email_sent = _send_recovery_email(
                    str(user["email"]),
                    "ATLAS password reset",
                    (
                        "A password reset was requested for your ATLAS account.\n\n"
                        f"User ID: {user.get('username')}\n"
                        f"Reset link: {reset_url}\n\n"
                        "If you did not request this, ignore this email.\n"
                    ),
                )
            except Exception:
                email_sent = False

        result: Dict[str, Any] = {"ok": True, "email_sent": email_sent}
        if account_recovery_debug_enabled() and token:
            result.update({
                "reset_token": token,
                "reset_url": reset_url,
                "expires_at": expires_at,
            })
        return result

    @app.post("/api/auth/reset/password")
    async def auth_reset_password(request: Request):
        if not account_recovery_enabled():
            raise HTTPException(status_code=404, detail="account recovery disabled")

        body = await request.json()
        token = str(body.get("token", "")).strip()
        identifier = str(
            body.get("identifier")
            or body.get("username")
            or body.get("email")
            or ""
        ).strip()
        code = _normalize_email_code(body.get("verification_code", ""))
        password = str(body.get("password", ""))
        if not password:
            raise HTTPException(status_code=400, detail="password required")

        if identifier and code:
            user = auth.db.get_user_by_email(identifier) if "@" in identifier else auth.db.get_user_by_username(identifier)
            email = _normalize_email((user or {}).get("email", ""))
            if user is None or not email or not _consume_email_code(auth, "reset_password", email, code):
                raise HTTPException(status_code=400, detail="invalid or expired verification code")
            auth.db.update_user_password(user["id"], hash_password(password))
            return {"ok": True}

        if not token:
            raise HTTPException(status_code=400, detail="token or verification code required")

        user = auth.db.get_user_by_password_reset_token_hash(_hash_recovery_token(token))
        if user is None:
            raise HTTPException(status_code=400, detail="invalid or expired reset token")
        expires_at = float(user.get("password_reset_expires_at") or 0)
        if expires_at < _now():
            raise HTTPException(status_code=400, detail="invalid or expired reset token")

        auth.db.update_user_password(user["id"], hash_password(password))
        return {"ok": True}

    @app.post("/api/auth/logout")
    async def auth_logout(request: Request, response: Response):
        auth._clear_cookie(response)
        return {"ok": True}

    @app.get("/api/users/me")
    async def users_me(request: Request):
        user = request.scope.get("user") or auth.get_user_from_cookie(request)
        if user is None:
            raise HTTPException(status_code=401, detail="Not authenticated")
        return {"user": _sanitize_user(user)}
