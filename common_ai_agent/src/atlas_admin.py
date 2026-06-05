"""
ATLAS admin server — standalone process serving /admin + /api/admin/*.

Reads from the same DB (~/.common_ai_agent/atlas.db) and shares the
HMAC cookie secret (~/.common_ai_agent/atlas_cookie_secret) with the
main atlas_ui backend. The standalone admin server accepts the main UI
cookie as an SSO fallback, but direct admin login writes a separate
atlas_admin_session cookie so it does not overwrite the main UI session.

Why a separate process:
  • main backend can be exposed on 0.0.0.0 for LAN access while admin
    stays on 127.0.0.1 (or any tighter network policy)
  • admin restart / crash doesn't affect users
  • admin auth/access policy can diverge later (mTLS, IP allowlist…)
    without touching the main server

Usage:
    python -m src.atlas_admin --port 3002 --host 127.0.0.1
    # or via textual_main with --admin (launches both)
"""
from __future__ import annotations

import argparse
import errno
import os
import re
import site
import socket
import subprocess
import sys
import time
import uuid
from pathlib import Path
from typing import TYPE_CHECKING


# Self-bootstrap PYTHONPATH so `python src/atlas_admin.py` works without
# the user having to set PYTHONPATH manually.
_SRC = Path(__file__).resolve().parent
_ROOT = _SRC.parent
for _p in (str(_ROOT), str(_SRC)):
    if _p not in sys.path:
        sys.path.insert(0, _p)


def _account_home() -> Path | None:
    raw_home = os.environ.get("USERPROFILE", "").strip()
    if raw_home:
        return Path(raw_home).expanduser()
    try:
        import pwd
    except ImportError:
        raw_home = os.environ.get("HOME", "").strip()
        return Path(raw_home).expanduser() if raw_home else None
    try:
        raw = pwd.getpwuid(os.getuid()).pw_dir
    except KeyError:
        return None
    return Path(raw).expanduser()


def _account_user_site_paths(home: Path) -> list[Path]:
    version = f"{sys.version_info.major}.{sys.version_info.minor}"
    windows_version = f"Python{sys.version_info.major}{sys.version_info.minor}"
    paths = [
        home / "AppData" / "Roaming" / "Python" / windows_version / "site-packages",
        home / "AppData" / "Local" / "Python" / windows_version / "site-packages",
        home / "Library" / "Python" / version / "lib" / "python" / "site-packages",
        home / ".local" / "lib" / f"python{version}" / "site-packages",
    ]
    for env_name in ("APPDATA", "LOCALAPPDATA"):
        raw = os.environ.get(env_name, "").strip()
        if raw:
            paths.append(Path(raw) / "Python" / windows_version / "site-packages")
    return [
        path for path in paths
        if path.is_dir()
    ]


def _bootstrap_dependency_paths() -> None:
    home = _account_home()
    if home is None:
        return
    for path in _account_user_site_paths(home):
        if str(path) not in sys.path:
            site.addsitedir(str(path))


_bootstrap_dependency_paths()


def _local_ipv4_addresses() -> list[str]:
    addrs: set[str] = {"127.0.0.1"}
    try:
        for info in socket.getaddrinfo(socket.gethostname(), None, socket.AF_INET):
            ip = str(info[4][0] or "").strip()
            if ip:
                addrs.add(ip)
    except Exception:
        pass
    try:
        proc = subprocess.run(
            ["ifconfig"],
            check=False,
            capture_output=True,
            text=True,
            timeout=1,
        )
        for ip in re.findall(r"\binet\s+(\d+\.\d+\.\d+\.\d+)\b", proc.stdout or ""):
            addrs.add(ip)
    except Exception:
        pass
    return sorted(addrs, key=lambda ip: (ip.startswith("127."), ip))


def _lan_ipv4_addresses() -> list[str]:
    return [ip for ip in _local_ipv4_addresses() if not ip.startswith("127.")]


def _assert_bind_target_available(host: str, port: int, label: str) -> None:
    bind_host = str(host or "127.0.0.1").strip() or "127.0.0.1"
    family = socket.AF_INET6 if ":" in bind_host and bind_host != "0.0.0.0" else socket.AF_INET
    sock = socket.socket(family, socket.SOCK_STREAM)
    try:
        sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
        sock.bind((bind_host, int(port)))
    except OSError as exc:
        err = getattr(exc, "errno", None)
        if err in {errno.EADDRNOTAVAIL, 49, 99}:
            ips = _local_ipv4_addresses()
            options = ["127.0.0.1", "0.0.0.0", *_lan_ipv4_addresses()]
            sys.exit(
                f"{label}: cannot bind {bind_host}:{port}; address is not assigned to this Mac.\n"
                f"Current local IPv4 addresses: {', '.join(ips) or '(none)'}.\n"
                f"Use one of: --host {', '.join(dict.fromkeys(options))}."
            )
        if err in {errno.EADDRINUSE, 48, 98}:
            sys.exit(f"{label}: port {port} is already in use on {bind_host}.")
        sys.exit(f"{label}: cannot bind {bind_host}:{port}: {exc}")
    finally:
        sock.close()


def _access_url(host: str, port: int) -> str:
    display_host = str(host or "127.0.0.1").strip() or "127.0.0.1"
    if display_host in {"0.0.0.0", "::"}:
        lan = _lan_ipv4_addresses()
        if lan:
            display_host = lan[0]
    return f"http://{display_host}:{port}/admin"

if TYPE_CHECKING:
    from starlette.requests import Request
else:
    class Request:
        pass


def create_admin_app(project_root: Path):
    from fastapi import FastAPI
    from fastapi.responses import JSONResponse, HTMLResponse
    from starlette.requests import Request as StarletteRequest
    from starlette.staticfiles import StaticFiles

    from core.atlas_db import AtlasDB
    from core.atlas_auth import (
        GuestAuth,
        AuthMiddleware,
        admin_auth_status,
        create_auth_endpoints,
        is_admin_user,
        is_local_admin_mode,
    )

    globals()["Request"] = StarletteRequest
    app = FastAPI(title="ATLAS Admin")

    auth = GuestAuth(
        AtlasDB(),
        cookie_name="atlas_admin_session",
        fallback_cookie_names=("atlas_session",),
    )
    app.state.auth = auth
    app.add_middleware(AuthMiddleware, auth=auth)
    # Lets admins log in directly on the admin port without clobbering
    # the main UI's atlas_session cookie.
    create_auth_endpoints(app, auth)

    def _admin_required(request: Request):
        user = request.scope.get("user") or {}
        if is_local_admin_mode():
            return {
                "id": user.get("id") or "local-admin",
                "username": user.get("username") or "local-admin",
                "role": "admin",
            }
        return user if is_admin_user(user) else None

    def _admin_denied(request: Request):
        if request.scope.get("user"):
            return JSONResponse({"error": "Admin role required"}, status_code=403)
        return JSONResponse({"error": "Admin login required"}, status_code=401)

    def _scm_ui_override_ref() -> str:
        try:
            from core.scm import configured_scm_provider
            provider = configured_scm_provider()
        except Exception:
            provider = os.environ.get("ATLAS_SCM_PROVIDER", "auto").strip().lower() or "auto"
        suffix = provider.upper()
        return (
            os.environ.get(f"ATLAS_SCM_UI_OVERRIDE_{suffix}", "").strip()
            or os.environ.get(f"ATLAS_{suffix}_SCM_UI_OVERRIDE", "").strip()
            or os.environ.get("ATLAS_SCM_UI_OVERRIDE", "").strip()
        )

    def _scm_ui_override_is_url(ref: str) -> bool:
        return bool(re.match(r"^https?://", str(ref or ""), re.I))

    def _admin_runtime_payload() -> dict:
        try:
            from atlas_api_jobs import worker_runtime_snapshot  # noqa: WPS433
        except ImportError:
            from src.atlas_api_jobs import worker_runtime_snapshot  # type: ignore  # noqa: WPS433
        try:
            from core.scm import configured_scm_provider
            provider = configured_scm_provider()
        except Exception:
            provider = os.environ.get("ATLAS_SCM_PROVIDER", "auto").strip().lower() or "auto"
        override_ref = _scm_ui_override_ref()
        override_path = None
        override_exists = None
        if override_ref and not _scm_ui_override_is_url(override_ref):
            path = Path(override_ref).expanduser()
            if not path.is_absolute():
                path = project_root / path
            override_path = str(path.resolve())
            override_exists = path.is_file()
        return {
            "worker_runtime": worker_runtime_snapshot(project_root),
            "scm": {
                "provider": provider,
                "ui_override": {
                    "enabled": bool(override_ref),
                    "kind": "remote" if _scm_ui_override_is_url(override_ref) else ("local" if override_ref else ""),
                    "ref": override_ref,
                    "path": override_path,
                    "exists": override_exists,
                },
            },
            "atlas": {
                "run_mode": os.environ.get("ATLAS_RUN_MODE", "engineering"),
                "exec_mode": os.environ.get("ATLAS_EXEC_MODE") or os.environ.get("ATLAS_DEFAULT_EXEC_MODE", ""),
                "multi_user": os.environ.get("ATLAS_MULTI_USER", "1"),
                "multi_user_proc": os.environ.get("ATLAS_MULTI_USER_PROC", "1"),
            },
            "note": "Standalone admin sees its own process memory; use the main Atlas /admin for live in-process job queues.",
        }

    @app.get("/admin")
    async def admin_page(request: Request):
        frontend = project_root / "frontend" / "atlas"
        html_path = frontend / "admin.html"
        if not html_path.is_file():
            return JSONResponse({"error": "admin.html not bundled"}, status_code=500)
        # Inline admin.jsx the same way atlas_ui.py does so the page
        # works without a separate /static mount.
        import re as _re
        html = html_path.read_text(encoding="utf-8")

        def _inline_script(match):
            attrs = match.group("attrs")
            src = match.group("src").split("?", 1)[0]
            if not src.endswith((".jsx", ".js")):
                return match.group(0)
            path = (frontend / src).resolve()
            try:
                path.relative_to(frontend.resolve())
            except ValueError:
                return match.group(0)
            if not path.is_file():
                return match.group(0)
            body = path.read_text(encoding="utf-8")
            new_attrs = _re.sub(r'\s+src=["\'][^"\']+["\']', '', attrs)
            return f"<script{new_attrs}>{body}</script>"

        pattern = _re.compile(r"<script(?P<attrs>[^>]*\bsrc=[\"'](?P<src>[^\"']+)[\"'][^>]*)></script>")
        html = pattern.sub(_inline_script, html)
        return HTMLResponse(content=html)

    @app.get("/healthz")
    async def healthz():
        return JSONResponse({"ok": True, "role": "admin", "started": time.time()})

    @app.get("/api/admin/auth/status")
    async def api_admin_auth_status(request: Request):
        with AtlasDB() as db:
            return JSONResponse(admin_auth_status(db, request.scope.get("user")))

    @app.get("/api/admin/users")
    async def api_admin_users(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            users = db.list_all_users()
            counts = db.count_sessions_by_user()
            for u in users:
                u["session_count"] = counts.get(u["id"], 0)
            return JSONResponse({"users": users})

    @app.get("/api/admin/sessions")
    async def api_admin_sessions(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            return JSONResponse({"sessions": db.list_all_sessions()})

    @app.get("/api/admin/ips")
    async def api_admin_ips(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            return JSONResponse({"ips": db.list_all_ip_pointers()})

    @app.delete("/api/admin/ips/{ip_id}")
    async def api_admin_delete_ip_pointer(ip_id: str, request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            if db.get_ip_block(ip_id) is None:
                return JSONResponse({"error": "ip pointer not found"}, status_code=404)
            result = db.delete_ip_pointer(ip_id)
        return JSONResponse({**result, "filesystem_deleted": False})

    @app.delete("/api/admin/users/{user_id}")
    async def api_admin_delete_user_pointer(user_id: str, request: Request):
        admin = _admin_required(request)
        if admin is None:
            return _admin_denied(request)
        if str(admin.get("id") or "") == str(user_id or ""):
            return JSONResponse({"error": "cannot delete the signed-in admin user"}, status_code=400)
        with AtlasDB() as db:
            user = db.get_user(user_id)
            if user is None:
                return JSONResponse({"error": "user pointer not found"}, status_code=404)
            if str(user.get("role") or "").lower() == "admin":
                remaining = db._fetchone(
                    "SELECT COUNT(*) AS cnt FROM users WHERE role = 'admin' AND id != ?",
                    (user_id,),
                )
                if int(remaining["cnt"] if remaining is not None else 0) <= 0:
                    return JSONResponse({"error": "cannot delete the last admin user"}, status_code=400)
            result = db.delete_user_pointer(user_id)
        return JSONResponse({**result, "filesystem_deleted": False})

    @app.delete("/api/admin/sessions/{session_id}")
    async def api_admin_delete_session(session_id: str, request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        # Propagate the runtime delete outcome (review #2 gap1): a pending runtime
        # queue without ?force=1 must return 409 / deleted=False, not a misleading
        # 200 {"deleted": true} that orphans the runtime file/manifest.
        from atlas_session_delete import force_delete_requested, session_delete_response
        with AtlasDB() as db:
            if db.get_session(session_id) is None:
                return JSONResponse({"error": "session not found"}, status_code=404)
            result = db.delete_session(session_id, force=force_delete_requested(request))
        return session_delete_response(result)

    @app.get("/api/admin/usage")
    async def api_admin_usage(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            from core.atlas_admin_usage import build_admin_usage_payload
            return JSONResponse(build_admin_usage_payload(db))

    @app.get("/api/admin/session-flow")
    async def api_admin_session_flow(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            from core.session_flow_usage import build_session_flow_payload
            qp = request.query_params
            payload = build_session_flow_payload(db, {
                "range": (qp.get("range") or "7d").strip(),
                "lens": (qp.get("lens") or "team_lead").strip(),
                "risk": (qp.get("risk") or "all").strip(),
                "ip_id": (qp.get("ip_id") or "").strip() or None,
                "workflow": (qp.get("workflow") or "").strip() or None,
                "user_id": (qp.get("user_id") or "").strip() or None,
                "session_id": (qp.get("session_id") or "").strip() or None,
                "limit": qp.get("limit"),
                "offset": qp.get("offset"),
            })
            # Plan response shape exposes the page window as `pagination`.
            payload["pagination"] = payload.pop("limits", {})
            return JSONResponse(payload)

    @app.get("/api/admin/runtime")
    async def api_admin_runtime(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        return JSONResponse(_admin_runtime_payload())

    @app.get("/api/admin/feedback")
    async def api_admin_feedback(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            rows = db._fetchall(
                "SELECT f.id, f.user_id, u.username, f.content, f.status, "
                "       f.created_at, f.resolved_at, f.resolved_by, f.notes "
                "  FROM feedback f LEFT JOIN users u ON u.id = f.user_id "
                " ORDER BY f.created_at DESC"
            )
            items = [dict(r) for r in rows]
        return JSONResponse({"feedback": items})

    @app.get("/api/admin/permissions")
    async def api_admin_permissions(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            rows = db._fetchall(
                "SELECT p.id, p.ip_id, i.ip_name, p.grantee_user_id, u.username, "
                "       p.granted_by_user_id, gu.username AS granted_by_username, "
                "       p.permission, p.created_at, p.expires_at "
                "  FROM ip_permissions p "
                "  LEFT JOIN ip_blocks i ON i.id = p.ip_id "
                "  LEFT JOIN users u ON u.id = p.grantee_user_id "
                "  LEFT JOIN users gu ON gu.id = p.granted_by_user_id "
                " ORDER BY p.created_at DESC"
            )
            return JSONResponse({"permissions": [dict(r) for r in rows]})

    @app.get("/api/admin/permissions/options")
    async def api_admin_permissions_options(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        with AtlasDB() as db:
            ip_rows = db._fetchall(
                "SELECT i.id, i.ip_name, w.name AS workspace_name, w.owner_user_id, "
                "       ou.username AS owner_username "
                "  FROM ip_blocks i "
                "  LEFT JOIN workspaces w ON w.id = i.workspace_id "
                "  LEFT JOIN users ou ON ou.id = w.owner_user_id "
                " ORDER BY i.ip_name"
            )
            user_rows = db._fetchall(
                "SELECT id, username, display_name, role FROM users ORDER BY username"
            )
            return JSONResponse({
                "ips": [dict(r) for r in ip_rows],
                "users": [dict(r) for r in user_rows],
                "levels": ["view", "import", "write", "admin"],
            })

    @app.post("/api/admin/permissions")
    async def api_admin_permissions_grant(request: Request):
        admin = _admin_required(request)
        if admin is None:
            return _admin_denied(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        ip_id = str((body or {}).get("ip_id") or "").strip()
        grantee = str((body or {}).get("grantee_user_id") or "").strip()
        permission = str((body or {}).get("permission") or "").strip().lower()
        expires_at = (body or {}).get("expires_at")
        if not ip_id or not grantee or permission not in {"view", "import", "write", "admin"}:
            return JSONResponse({"error": "ip_id, grantee_user_id, permission required"}, status_code=400)
        try:
            with AtlasDB() as db:
                row = db.grant_ip_permission(
                    ip_id=ip_id,
                    grantee_user_id=grantee,
                    permission=permission,
                    granted_by_user_id=admin.get("id") or "",
                    expires_at=expires_at if expires_at else None,
                )
            return JSONResponse({"permission": row})
        except ValueError as exc:
            return JSONResponse({"error": str(exc)}, status_code=400)
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.delete("/api/admin/permissions")
    async def api_admin_permissions_revoke(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        ip_id = str((body or {}).get("ip_id") or "").strip()
        grantee = str((body or {}).get("grantee_user_id") or "").strip()
        permission = (body or {}).get("permission")
        if not ip_id or not grantee:
            return JSONResponse({"error": "ip_id and grantee_user_id required"}, status_code=400)
        with AtlasDB() as db:
            removed = db.revoke_ip_permission(ip_id, grantee, permission)
        return JSONResponse({"revoked": removed})

    @app.get("/api/admin/db/tables")
    async def api_admin_db_tables(request: Request):
        if _admin_required(request) is None:
            return _admin_denied(request)
        from core.atlas_admin_db import list_tables
        with AtlasDB() as db:
            return JSONResponse(list_tables(db))

    @app.get("/api/admin/db/preview")
    async def api_admin_db_preview(request: Request, per_table: int = 3):
        if _admin_required(request) is None:
            return _admin_denied(request)
        from core.atlas_admin_db import preview_all
        with AtlasDB() as db:
            return JSONResponse(preview_all(db, per_table=per_table))

    @app.get("/api/admin/db/table/{name}")
    async def api_admin_db_table(name: str, request: Request,
                                 limit: int = 50, offset: int = 0,
                                 order: str = "desc"):
        if _admin_required(request) is None:
            return _admin_denied(request)
        from core.atlas_admin_db import read_table
        with AtlasDB() as db:
            payload, err = read_table(db, name, limit=limit, offset=offset, order=order)
        if err:
            return JSONResponse({"error": err}, status_code=400)
        return JSONResponse(payload)

    @app.get("/api/admin/db/runtime/{session_uid}")
    async def api_admin_db_runtime(session_uid: str, request: Request,
                                   table: str = "", limit: int = 50,
                                   offset: int = 0, order: str = "desc"):
        """Inspect ONE session's per-session runtime DB.

        Hardened by the shared resolver (plan §2.11 / R14/R21/R24): session_uid
        ONLY (path-like input rejected), resolved through the control manifest +
        containment-checked under ATLAS_RUNTIME_DB_ROOT, OWNERSHIP enforced even
        under local-admin bypass, and NO filesystem path ever returned.
        """
        admin = _admin_required(request)
        if admin is None:
            return _admin_denied(request)
        from core.atlas_admin_db import inspect_runtime_table, RuntimeInspectError
        user = request.scope.get("user") or {}
        try:
            with AtlasDB() as db:
                payload = inspect_runtime_table(
                    db,
                    session_uid=session_uid,
                    requesting_user_id=str(user.get("id") or admin.get("id") or ""),
                    requesting_username=str(user.get("username") or admin.get("username") or ""),
                    is_admin=True,
                    table=(table or None),
                    limit=limit,
                    offset=offset,
                    order=order,
                )
            return JSONResponse(payload)
        except RuntimeInspectError as exc:
            return JSONResponse({"error": exc.message}, status_code=exc.status)
        except Exception:
            # Never echo str(exc): an unexpected error message could leak a
            # filesystem path. Path-free generic 500 (mirrors atlas_ui, R24).
            return JSONResponse({"error": "runtime inspect failed"}, status_code=500)

    @app.post("/api/admin/feedback/{fid}/resolve")
    async def api_admin_feedback_resolve(fid: str, request: Request):
        admin = _admin_required(request)
        if admin is None:
            return _admin_denied(request)
        try:
            body = await request.json()
        except Exception:
            body = {}
        notes = str((body or {}).get("notes") or "").strip()
        with AtlasDB() as db:
            db._execute(
                "UPDATE feedback SET status = 'resolved', resolved_at = ?, "
                "       resolved_by = ?, notes = ? WHERE id = ?",
                (time.time(), admin.get("username", ""), notes, fid),
            )
        return JSONResponse({"ok": True})

    # Static files (theme + admin.jsx fetched by inline scripts that
    # didn't get rewritten). Mount LAST so explicit routes win.
    frontend = project_root / "frontend" / "atlas"
    if frontend.is_dir():
        app.mount("/", StaticFiles(directory=str(frontend), html=False),
                  name="atlas-admin-static")

    return app


def main():
    ap = argparse.ArgumentParser(prog="atlas_admin",
                                 description="Standalone admin server for ATLAS")
    ap.add_argument("--port", type=int, default=3002)
    ap.add_argument("--host", default="127.0.0.1",
                    help="bind host (default 127.0.0.1 — keep admin off the LAN)")
    ap.add_argument("--root", default=None,
                    help="project root (defaults to repo root)")
    args = ap.parse_args()
    root = Path(args.root or _ROOT).expanduser().resolve()
    if not (root / "frontend" / "atlas" / "admin.html").is_file():
        sys.exit(f"frontend/atlas/admin.html not found under {root}")
    _assert_bind_target_available(args.host, args.port, "ATLAS admin")
    import uvicorn
    app = create_admin_app(root)
    print(f"\n  ATLAS Admin → {_access_url(args.host, args.port)}\n", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
