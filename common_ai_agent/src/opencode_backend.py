"""
opencode_backend.py — own ChatGPT OAuth credential management so
common_ai_agent can use a user's ChatGPT Plus/Pro subscription against the
Codex backend (https://chatgpt.com/backend-api/codex/responses) without
needing opencode installed at runtime.

Provides:
  • login_browser()     PKCE flow: opens browser, runs local callback
  • login_headless()    Device-code flow: shows user_code, polls
  • logout()            Delete stored credential
  • get_credentials()   Read + auto-refresh
  • codex_extra_headers() Codex-specific HTTP headers (originator, account-id)

File format and refresh flow are byte-compatible with opencode's
auth.json so the same login is shared between both tools (login once,
both work). Mirrors opencode/packages/opencode/src/plugin/codex.ts.

auth.json shape:
  {
    "openai": {
      "type":     "oauth",
      "access":   "<JWT>",
      "refresh":  "<token>",
      "expires":  <ms_since_epoch>,
      "accountId": "<chatgpt_account_id>"   # optional; we re-derive if absent
    }
  }

CLI entrypoint:
  $ python -m src.opencode_backend login           # browser flow
  $ python -m src.opencode_backend login --headless
  $ python -m src.opencode_backend status
  $ python -m src.opencode_backend logout
"""

import base64
import hashlib
import http.server
import json
import os
import secrets
import socketserver
import sys
import threading
import time
import urllib.error
import urllib.parse
import urllib.request
import webbrowser
from pathlib import Path
from typing import Optional

# Mirrors opencode/packages/opencode/src/plugin/codex.ts
CODEX_API_ENDPOINT = "https://chatgpt.com/backend-api/codex/responses"
CODEX_BASE_URL = "https://chatgpt.com/backend-api/codex"
CODEX_OAUTH_ISSUER = "https://auth.openai.com"
CODEX_CLIENT_ID = "app_EMoamEEZ73f0CkXaXp7hrann"

DEFAULT_AUTH_PATH = os.path.expanduser("~/.local/share/opencode/auth.json")


# ──────────────────────────────────────────────────────────────────────────
# auth.json IO
# ──────────────────────────────────────────────────────────────────────────

def _auth_path() -> str:
    return os.environ.get("OPENCODE_AUTH_PATH") or DEFAULT_AUTH_PATH


def _read_auth_file(path: str = "") -> dict:
    p = path or _auth_path()
    try:
        with open(p, "r", encoding="utf-8") as f:
            return json.load(f)
    except (FileNotFoundError, json.JSONDecodeError):
        return {}


def _write_auth_file(data: dict, path: str = "") -> None:
    p = path or _auth_path()
    Path(p).parent.mkdir(parents=True, exist_ok=True)
    with open(p, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2)
    try:
        os.chmod(p, 0o600)
    except OSError:
        pass


# ──────────────────────────────────────────────────────────────────────────
# JWT helpers — derive accountId from id_token / access_token claims
# ──────────────────────────────────────────────────────────────────────────

def _b64url_decode(s: str) -> bytes:
    pad = "=" * ((4 - len(s) % 4) % 4)
    return base64.urlsafe_b64decode(s + pad)


def _parse_jwt_claims(token: str) -> dict:
    parts = token.split(".")
    if len(parts) != 3:
        return {}
    try:
        return json.loads(_b64url_decode(parts[1]).decode("utf-8"))
    except Exception:
        return {}


def _extract_account_id(claims: dict) -> Optional[str]:
    if not claims:
        return None
    if claims.get("chatgpt_account_id"):
        return claims["chatgpt_account_id"]
    nested = claims.get("https://api.openai.com/auth") or {}
    if isinstance(nested, dict) and nested.get("chatgpt_account_id"):
        return nested["chatgpt_account_id"]
    orgs = claims.get("organizations") or []
    if orgs and isinstance(orgs[0], dict):
        return orgs[0].get("id")
    return None


# ──────────────────────────────────────────────────────────────────────────
# OAuth refresh — POST /oauth/token grant_type=refresh_token
# ──────────────────────────────────────────────────────────────────────────

def _refresh(refresh_token: str) -> dict:
    body = urllib.parse.urlencode(
        {
            "grant_type": "refresh_token",
            "refresh_token": refresh_token,
            "client_id": CODEX_CLIENT_ID,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{CODEX_OAUTH_ISSUER}/oauth/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


# ──────────────────────────────────────────────────────────────────────────
# Public API
# ──────────────────────────────────────────────────────────────────────────

def get_credentials(provider: str = "openai", auto_refresh: bool = True) -> Optional[dict]:
    """
    Read the credential for `provider` from opencode's auth.json. When the
    access token is missing or within 60s of expiry, refresh via
    auth.openai.com and persist the new tokens back to disk so opencode and
    common_ai_agent stay in sync.

    Returns the full credential dict (with refreshed `access` if needed),
    or None when no usable credential can be obtained.
    """
    data = _read_auth_file()
    cred = data.get(provider) or {}
    if not cred:
        return None
    if cred.get("type") != "oauth":
        return cred  # API-key shape — caller can still use cred["key"]

    access = cred.get("access", "")
    expires = int(cred.get("expires", 0) or 0)
    now_ms = int(time.time() * 1000)
    needs_refresh = (not access) or (expires and expires < now_ms + 60_000)

    if needs_refresh and auto_refresh and cred.get("refresh"):
        try:
            tokens = _refresh(cred["refresh"])
        except Exception:
            return cred if cred.get("access") else None
        new_cred = {
            "type": "oauth",
            "refresh": tokens.get("refresh_token", cred["refresh"]),
            "access": tokens.get("access_token", ""),
            "expires": now_ms + int(tokens.get("expires_in", 3600)) * 1000,
        }
        # Re-derive accountId from fresh id_token if present
        if tokens.get("id_token"):
            aid = _extract_account_id(_parse_jwt_claims(tokens["id_token"]))
            if aid:
                new_cred["accountId"] = aid
        elif cred.get("accountId"):
            new_cred["accountId"] = cred["accountId"]
        cred = new_cred
        data[provider] = cred
        _write_auth_file(data)

    # If accountId missing, try to derive from access token JWT
    if not cred.get("accountId") and cred.get("access"):
        aid = _extract_account_id(_parse_jwt_claims(cred["access"]))
        if aid:
            cred["accountId"] = aid

    return cred


def codex_extra_headers(account_id: Optional[str], session_id: Optional[str] = None) -> dict:
    """Headers opencode's Codex plugin always adds for Codex requests."""
    h = {
        "originator": "opencode",
    }
    if account_id:
        h["ChatGPT-Account-Id"] = account_id
    if session_id:
        h["session_id"] = session_id
    return h


def get_session_cache_key() -> str:
    """Return a stable per-session key used for both:
      • prompt_cache_key in the request body  → enables prefix caching
      • session_id HTTP header                → mirrors opencode's codex.ts

    Lookup order (most-specific → fallback):
      1. OPENCODE_CACHE_KEY env (explicit override)
      2. src.main.current_session_id (active common_ai_agent session)
      3. ATLAS_SESSION_ID / LLM_SESSION_ID env
      4. process default ("common_ai_agent")
    """
    explicit = os.environ.get("OPENCODE_CACHE_KEY", "").strip()
    if explicit:
        return explicit
    try:
        import sys as _sys
        _main = _sys.modules.get("src.main") or _sys.modules.get("__main__")
        sid = getattr(_main, "current_session_id", None)
        if sid:
            return str(sid)
    except Exception:
        pass
    return (
        os.environ.get("ATLAS_SESSION_ID", "").strip()
        or os.environ.get("LLM_SESSION_ID", "").strip()
        or "common_ai_agent"
    )


def is_active() -> bool:
    """True when USE_OPENCODE_OAUTH is enabled in env."""
    return os.environ.get("USE_OPENCODE_OAUTH", "false").lower() in ("true", "1", "yes")


# ──────────────────────────────────────────────────────────────────────────
# PKCE helpers
# ──────────────────────────────────────────────────────────────────────────

_PKCE_ALPHABET = (
    "ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-._~"
)


def _gen_pkce() -> tuple:
    """Generate (verifier, challenge) for PKCE S256.

    Verifier: 43 chars from RFC 7636 unreserved alphabet.
    Challenge: base64url(sha256(verifier)) with padding stripped.
    """
    verifier = "".join(
        _PKCE_ALPHABET[secrets.randbelow(len(_PKCE_ALPHABET))] for _ in range(43)
    )
    digest = hashlib.sha256(verifier.encode("ascii")).digest()
    challenge = base64.urlsafe_b64encode(digest).rstrip(b"=").decode("ascii")
    return verifier, challenge


def _gen_state() -> str:
    return base64.urlsafe_b64encode(secrets.token_bytes(32)).rstrip(b"=").decode("ascii")


def _exchange_code(code: str, redirect_uri: str, verifier: str) -> dict:
    body = urllib.parse.urlencode(
        {
            "grant_type": "authorization_code",
            "code": code,
            "redirect_uri": redirect_uri,
            "client_id": CODEX_CLIENT_ID,
            "code_verifier": verifier,
        }
    ).encode("utf-8")
    req = urllib.request.Request(
        f"{CODEX_OAUTH_ISSUER}/oauth/token",
        data=body,
        headers={"Content-Type": "application/x-www-form-urlencoded"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=30) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _tokens_to_cred(tokens: dict, prev: Optional[dict] = None) -> dict:
    cred = {
        "type": "oauth",
        "access": tokens.get("access_token", ""),
        "refresh": tokens.get("refresh_token", (prev or {}).get("refresh", "")),
        "expires": int(time.time() * 1000)
        + int(tokens.get("expires_in", 3600)) * 1000,
    }
    aid = None
    if tokens.get("id_token"):
        aid = _extract_account_id(_parse_jwt_claims(tokens["id_token"]))
    if not aid and cred["access"]:
        aid = _extract_account_id(_parse_jwt_claims(cred["access"]))
    if aid:
        cred["accountId"] = aid
    elif prev and prev.get("accountId"):
        cred["accountId"] = prev["accountId"]
    return cred


# ──────────────────────────────────────────────────────────────────────────
# Login: browser flow (PKCE) — primary
# ──────────────────────────────────────────────────────────────────────────

_OAUTH_PORT_DEFAULT = 1455
_LOGIN_HTML_OK = (
    b"<!doctype html><html><head><title>Login successful</title>"
    b"<style>body{font-family:system-ui;background:#131010;color:#f1ecec;"
    b"display:flex;align-items:center;justify-content:center;height:100vh;margin:0}"
    b"</style></head><body><div style='text-align:center'>"
    b"<h1>Login successful</h1>"
    b"<p>You can close this window and return to common_ai_agent.</p>"
    b"<script>setTimeout(()=>window.close(),1500)</script>"
    b"</div></body></html>"
)
_LOGIN_HTML_ERR = (
    b"<!doctype html><html><head><title>Login failed</title></head>"
    b"<body><h1>Login failed</h1></body></html>"
)


def login_browser(
    auth_path: str = "",
    port: int = _OAUTH_PORT_DEFAULT,
    open_browser: bool = True,
    timeout: int = 300,
) -> dict:
    """PKCE OAuth flow with browser. Saves credential to auth.json on success.

    Args:
        auth_path: override location (default ~/.local/share/opencode/auth.json)
        port: localhost port for the redirect callback
        open_browser: when False, just print the authorize URL
        timeout: seconds to wait for the user to complete the redirect

    Returns: the saved credential dict.
    """
    redirect_uri = f"http://localhost:{port}/auth/callback"
    verifier, challenge = _gen_pkce()
    state = _gen_state()
    authorize_url = f"{CODEX_OAUTH_ISSUER}/oauth/authorize?" + urllib.parse.urlencode(
        {
            "response_type": "code",
            "client_id": CODEX_CLIENT_ID,
            "redirect_uri": redirect_uri,
            "scope": "openid profile email offline_access",
            "code_challenge": challenge,
            "code_challenge_method": "S256",
            "id_token_add_organizations": "true",
            "codex_cli_simplified_flow": "true",
            "state": state,
            "originator": "opencode",
        }
    )

    received: dict = {}
    done = threading.Event()

    class Handler(http.server.BaseHTTPRequestHandler):
        def log_message(self, *_args, **_kwargs):
            return  # silence default access log

        def do_GET(self):  # noqa: N802
            parsed = urllib.parse.urlparse(self.path)
            if parsed.path != "/auth/callback":
                self.send_response(404)
                self.end_headers()
                return
            qs = urllib.parse.parse_qs(parsed.query)
            err = qs.get("error_description", qs.get("error", [""]))[0]
            code = qs.get("code", [""])[0]
            recv_state = qs.get("state", [""])[0]
            if err:
                received["error"] = err
                self.send_response(200)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(_LOGIN_HTML_ERR)
                done.set()
                return
            if not code or recv_state != state:
                received["error"] = "missing code or state mismatch"
                self.send_response(400)
                self.send_header("Content-Type", "text/html")
                self.end_headers()
                self.wfile.write(_LOGIN_HTML_ERR)
                done.set()
                return
            received["code"] = code
            self.send_response(200)
            self.send_header("Content-Type", "text/html")
            self.end_headers()
            self.wfile.write(_LOGIN_HTML_OK)
            done.set()

    class _ReuseTCPServer(socketserver.TCPServer):
        allow_reuse_address = True

    httpd = _ReuseTCPServer(("127.0.0.1", port), Handler)
    th = threading.Thread(target=httpd.serve_forever, daemon=True)
    th.start()

    try:
        print(f"\n[opencode-oauth] Opening browser for ChatGPT login…")
        print(f"  if it doesn't open, paste this URL:\n  {authorize_url}\n")
        if open_browser:
            try:
                webbrowser.open(authorize_url)
            except Exception:
                pass
        if not done.wait(timeout=timeout):
            raise TimeoutError(f"login timed out after {timeout}s")
        if received.get("error"):
            raise RuntimeError(f"OAuth callback failed: {received['error']}")
        tokens = _exchange_code(received["code"], redirect_uri, verifier)
    finally:
        httpd.shutdown()
        httpd.server_close()

    cred = _tokens_to_cred(tokens)
    data = _read_auth_file(auth_path)
    data["openai"] = cred
    _write_auth_file(data, auth_path)
    return cred


# ──────────────────────────────────────────────────────────────────────────
# Login: headless device-code flow — for SSH / remote shells
# ──────────────────────────────────────────────────────────────────────────

def login_headless(auth_path: str = "", poll_safety_ms: int = 3000) -> dict:
    """Device-code OAuth flow — no browser on the host required."""
    init = urllib.request.Request(
        f"{CODEX_OAUTH_ISSUER}/api/accounts/deviceauth/usercode",
        data=json.dumps({"client_id": CODEX_CLIENT_ID}).encode("utf-8"),
        headers={
            "Content-Type": "application/json",
            "User-Agent": "opencode/cai-bridge",
        },
        method="POST",
    )
    with urllib.request.urlopen(init, timeout=30) as resp:
        device = json.loads(resp.read().decode("utf-8"))
    user_code = device["user_code"]
    device_id = device["device_auth_id"]
    interval_ms = max(int(device.get("interval", "5") or 5), 1) * 1000

    print("\n[opencode-oauth] Headless login")
    print(f"  Visit:  {CODEX_OAUTH_ISSUER}/codex/device")
    print(f"  Code:   {user_code}\n")

    deadline = time.time() + 15 * 60
    while time.time() < deadline:
        try:
            poll = urllib.request.Request(
                f"{CODEX_OAUTH_ISSUER}/api/accounts/deviceauth/token",
                data=json.dumps(
                    {"device_auth_id": device_id, "user_code": user_code}
                ).encode("utf-8"),
                headers={
                    "Content-Type": "application/json",
                    "User-Agent": "opencode/cai-bridge",
                },
                method="POST",
            )
            with urllib.request.urlopen(poll, timeout=30) as resp:
                payload = json.loads(resp.read().decode("utf-8"))
            tokens = _exchange_code(
                payload["authorization_code"],
                f"{CODEX_OAUTH_ISSUER}/deviceauth/callback",
                payload["code_verifier"],
            )
            cred = _tokens_to_cred(tokens)
            data = _read_auth_file(auth_path)
            data["openai"] = cred
            _write_auth_file(data, auth_path)
            return cred
        except urllib.error.HTTPError as e:
            if e.code not in (403, 404):
                raise
            time.sleep((interval_ms + poll_safety_ms) / 1000.0)
    raise TimeoutError("device login timed out")


# ──────────────────────────────────────────────────────────────────────────
# Logout / status
# ──────────────────────────────────────────────────────────────────────────

def logout(provider: str = "openai", auth_path: str = "") -> bool:
    data = _read_auth_file(auth_path)
    if provider not in data:
        return False
    del data[provider]
    _write_auth_file(data, auth_path)
    return True


def status(provider: str = "openai", auth_path: str = "") -> dict:
    """Return a redacted status dict suitable for printing."""
    cred = (_read_auth_file(auth_path) or {}).get(provider) or {}
    if not cred:
        return {"provider": provider, "logged_in": False}
    out = {
        "provider": provider,
        "logged_in": True,
        "type": cred.get("type"),
        "accountId": cred.get("accountId", ""),
    }
    if cred.get("expires"):
        remain_ms = int(cred["expires"]) - int(time.time() * 1000)
        out["expires_in_sec"] = max(remain_ms // 1000, 0)
    return out


# ──────────────────────────────────────────────────────────────────────────
# CLI entrypoint:  python -m src.opencode_backend <login|logout|status>
# ──────────────────────────────────────────────────────────────────────────

def _main(argv: list) -> int:
    if not argv:
        print("usage: python -m src.opencode_backend <login|logout|status> [--headless]")
        return 2
    cmd = argv[0]
    if cmd == "login":
        try:
            cred = (
                login_headless()
                if "--headless" in argv
                else login_browser()
            )
        except Exception as e:
            print(f"[opencode-oauth] login failed: {e}")
            return 1
        print(f"[opencode-oauth] login OK (account={cred.get('accountId', '?')})")
        return 0
    if cmd == "logout":
        ok = logout()
        print("[opencode-oauth] " + ("logged out" if ok else "no credential to remove"))
        return 0 if ok else 1
    if cmd == "status":
        s = status()
        print(json.dumps(s, indent=2))
        return 0 if s.get("logged_in") else 1
    print(f"unknown command: {cmd}")
    return 2


if __name__ == "__main__":
    sys.exit(_main(sys.argv[1:]))
