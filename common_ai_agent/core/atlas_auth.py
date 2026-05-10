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
import time
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
        from fastapi import FastAPI, Request, Response, HTTPException
        from starlette.requests import Request as StarletteRequest
    except Exception:  # pragma: no cover
        FastAPI = None  # type: ignore
        Request = None  # type: ignore
        Response = None  # type: ignore
        HTTPException = None  # type: ignore
        StarletteRequest = None  # type: ignore

_COOKIE_NAME = "atlas_session"
_MAX_AGE = 90 * 24 * 60 * 60


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


class GuestAuth:
    """HMAC-signed cookie authentication. Class name kept for compatibility;
    no longer creates guest users (legacy auto-guest path removed)."""

    def __init__(self, db: AtlasDB, cookie_secret: Optional[str] = None):
        self.db = db
        self.cookie_secret = cookie_secret or _default_cookie_secret()

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
            key=_COOKIE_NAME,
            value=self._sign(user_id),
            httponly=True,
            secure=False,
            samesite="lax",
            max_age=_MAX_AGE,
        )

    def _clear_cookie(self, response) -> None:
        if response is None:
            return
        response.delete_cookie(key=_COOKIE_NAME)

    def get_user_from_cookie(self, request) -> Optional[Dict[str, Any]]:
        """Extract and verify user from request cookies."""
        if request is None:
            return None
        cookie_value = request.cookies.get(_COOKIE_NAME)
        if not cookie_value:
            return None
        user_id = self._verify(cookie_value)
        if not user_id:
            return None
        return self.db.get_user(user_id)

async def get_current_user(request: Request) -> dict:
    """FastAPI dependency that extracts user from cookie."""
    auth: Optional[GuestAuth] = getattr(request.app.state, "auth", None)
    if auth is None:
        raise HTTPException(status_code=401, detail="Authentication not configured")
    user = auth.get_user_from_cookie(request)
    if user is None:
        raise HTTPException(status_code=401, detail="Not authenticated")
    return user


_PUBLIC_PATHS = {"/", "/index.html", "/healthz", "/favicon.ico"}
_PUBLIC_PREFIXES = ("/static/", "/assets/", "/api/auth/")
_PUBLIC_EXT = {"js", "jsx", "css", "html", "png", "jpg", "jpeg", "svg", "ico", "woff", "woff2", "ttf", "map"}


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
        scope["user"] = self.auth.get_user_from_cookie(request)

        if self._is_public(path) or scope["user"] is not None:
            await self.app(scope, receive, send)
            return

        await self._send_401(send)

    @staticmethod
    def _is_public(path: str) -> bool:
        if path in _PUBLIC_PATHS or path.startswith(_PUBLIC_PREFIXES):
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
        "role": user.get("role"),
        "created_at": user.get("created_at"),
        "last_login_at": user.get("last_login_at"),
    }


def create_auth_endpoints(app: FastAPI, auth: GuestAuth) -> None:
    """Register auth endpoints on the FastAPI app."""

    @app.post("/api/auth/register")
    async def auth_register(request: Request, response: Response):
        body = await request.json()
        username = str(body.get("username", "")).strip()
        password = str(body.get("password", ""))
        display_name = str(body.get("display_name", "")).strip() or username

        if not username or not password:
            raise HTTPException(status_code=400, detail="username and password required")

        if auth.db.get_user_by_username(username) is not None:
            raise HTTPException(status_code=409, detail="username already exists")

        user = auth.db.create_user(username, display_name, hash_password(password))
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
        if user is None or not verify_password(password, user.get("password_hash") or ""):
            raise HTTPException(status_code=401, detail="invalid credentials")

        auth.db._execute(
            "UPDATE users SET last_login_at = ? WHERE id = ?",
            (_now(), user["id"]),
        )
        auth._set_cookie(response, user["id"])
        return {"user": _sanitize_user(user)}

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
