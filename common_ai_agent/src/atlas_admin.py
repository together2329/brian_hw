"""
ATLAS admin server — standalone process serving /admin + /api/admin/*.

Reads from the same DB (~/.common_ai_agent/atlas.db) and shares the
HMAC cookie secret (~/.common_ai_agent/atlas_cookie_secret) with the
main atlas_ui backend, so a user logged in via the main UI's
/api/auth/login can hit this admin server with the same cookie.

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
import os
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

# `from __future__ import annotations` stores `request: Request` as a
# string. FastAPI resolves that string against module globals, not the
# local imports inside create_admin_app(), so expose Request here or
# pydantic treats `request` as a required query parameter and returns 422.
if TYPE_CHECKING:
    from fastapi import Request
else:
    try:
        from fastapi import Request  # noqa: F401  (runtime forward-ref target)
    except ImportError:
        class Request:  # fallback name for annotations when FastAPI is absent
            pass


def create_admin_app(project_root: Path):
    from fastapi import FastAPI, Request
    from fastapi.responses import JSONResponse, HTMLResponse
    from starlette.staticfiles import StaticFiles

    from core.atlas_db import AtlasDB
    from core.atlas_auth import GuestAuth, AuthMiddleware, create_auth_endpoints

    app = FastAPI(title="ATLAS Admin")

    auth = GuestAuth(AtlasDB())
    app.state.auth = auth
    app.add_middleware(AuthMiddleware, auth=auth)
    # Lets admins log in directly on the admin port if they want a
    # dedicated cookie jar (login/register/logout endpoints).
    create_auth_endpoints(app, auth)

    def _admin_required(request: Request):
        user = request.scope.get("user")
        if not user or user.get("role") != "admin":
            return None
        return user

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

    @app.get("/api/admin/users")
    async def api_admin_users(request: Request):
        if _admin_required(request) is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        with AtlasDB() as db:
            users = db.list_all_users()
            counts = db.count_sessions_by_user()
            for u in users:
                u["session_count"] = counts.get(u["id"], 0)
            return JSONResponse({"users": users})

    @app.get("/api/admin/sessions")
    async def api_admin_sessions(request: Request):
        if _admin_required(request) is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        with AtlasDB() as db:
            return JSONResponse({"sessions": db.list_all_sessions()})

    @app.delete("/api/admin/sessions/{session_id}")
    async def api_admin_delete_session(session_id: str, request: Request):
        if _admin_required(request) is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        with AtlasDB() as db:
            if db.get_session(session_id) is None:
                return JSONResponse({"error": "session not found"}, status_code=404)
            db.delete_session(session_id)
        return JSONResponse({"deleted": True})

    @app.get("/api/admin/usage")
    async def api_admin_usage(request: Request):
        if _admin_required(request) is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        with AtlasDB() as db:
            from core.atlas_admin_usage import build_admin_usage_payload
            return JSONResponse(build_admin_usage_payload(db))

    @app.get("/api/admin/feedback")
    async def api_admin_feedback(request: Request):
        if _admin_required(request) is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
        with AtlasDB() as db:
            rows = db._fetchall(
                "SELECT f.id, f.user_id, u.username, f.content, f.status, "
                "       f.created_at, f.resolved_at, f.resolved_by, f.notes "
                "  FROM feedback f LEFT JOIN users u ON u.id = f.user_id "
                " ORDER BY f.created_at DESC"
            )
            items = [dict(r) for r in rows]
        return JSONResponse({"feedback": items})

    @app.post("/api/admin/feedback/{fid}/resolve")
    async def api_admin_feedback_resolve(fid: str, request: Request):
        admin = _admin_required(request)
        if admin is None:
            return JSONResponse({"error": "Forbidden"}, status_code=403)
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
    import uvicorn
    app = create_admin_app(root)
    print(f"\n  ATLAS Admin → http://{args.host}:{args.port}/admin\n", flush=True)
    uvicorn.run(app, host=args.host, port=args.port, log_level="warning")


if __name__ == "__main__":
    main()
