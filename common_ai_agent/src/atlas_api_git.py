"""ATLAS SCM API — extracted from atlas_ui.py.

The `/api/git/*` routes remain for UI compatibility, while `/api/scm/*`
aliases expose the provider-neutral contract. Git is the built-in adapter;
Perforce can be supplied later by implementing the `core.scm` adapter surface.
The host (atlas_ui.py) wires routes via `register_git_routes` and injects
callables for runtime values (PROJECT_ROOT, active IP, IP-name validator) so
this module never reaches into the host's mutable globals.
"""
from __future__ import annotations

import asyncio
import re
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI
from fastapi.responses import JSONResponse

from core.scm import (
    configured_scm_provider,
    resolve_scm_adapter,
    scm_provider_allows_missing_git_dir,
)


def register_git_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    active_ip_value: Callable[[], str],
    valid_ip_name: Callable[[str], bool],
) -> None:
    """Mount the Git-compatible SCM API onto *app*.

    project_root, active_ip_value, valid_ip_name are passed as callables
    rather than values so the routes always read the live state — the
    --root flag in atlas_ui main() rebinds PROJECT_ROOT after this
    module is imported.
    """

    def _request_provider(value: str | None) -> str:
        provider = str(value or "").strip().lower()
        return "" if provider in {"", "auto", "default"} else provider

    async def _scm_call(cwd: str | None, method: str, *args, provider: str = "", **kwargs):
        # `cwd` lets callers target the per-IP SCM workspace
        # (PROJECT_ROOT/<ip>) instead of the outer project workspace.
        # The actual provider is resolved per request so a deployment can
        # switch from Git to Perforce via ATLAS_SCM_PROVIDER.
        adapter = resolve_scm_adapter(cwd or str(project_root()), provider=_request_provider(provider) or None)
        func = getattr(adapter, method)
        return await asyncio.to_thread(func, *args, **kwargs)

    async def _scm_optional(cwd: str | None, method: str, *args, provider: str = "", **kwargs):
        # Like _scm_call but for provider-specific methods (e.g. Perforce-only
        # sync_state/open_paths). Returns (result_or_None, provider, supported).
        adapter = resolve_scm_adapter(cwd or str(project_root()), provider=_request_provider(provider) or None)
        if not hasattr(adapter, method):
            return None, adapter.provider, False
        func = getattr(adapter, method)
        return (await asyncio.to_thread(func, *args, **kwargs)), adapter.provider, True

    def _scm_provider_for_cwd(cwd: str | None, provider: str = ""):
        return resolve_scm_adapter(cwd or str(project_root()), provider=_request_provider(provider) or None).provider

    def _scm_cwd_for_ip(ip: str, provider: str = "") -> tuple[str | None, JSONResponse | None, str]:
        """Resolve the cwd for a per-IP SCM workspace.

        Empty IP keeps the legacy project-root SCM view. A non-empty IP is
        explicit user intent, so never fall back to PROJECT_ROOT: returning the
        outer workspace for a missing per-IP workspace makes submit/push hit
        the wrong source-control root.
        """
        clean = str(ip or "").strip()
        if not clean:
            return str(project_root()), None, ""
        if not valid_ip_name(clean):
            return None, JSONResponse({"error": "invalid ip", "ip": clean}, status_code=400), clean
        candidate = (project_root() / clean).resolve()
        try:
            candidate.relative_to(project_root().resolve())
        except ValueError:
            return None, JSONResponse({"error": "ip path escapes project root", "ip": clean}, status_code=400), clean
        if not candidate.is_dir():
            return None, JSONResponse({"error": "ip not found", "ip": clean}, status_code=404), clean
        if (
            not scm_provider_allows_missing_git_dir(_request_provider(provider) or configured_scm_provider())
            and not (candidate / ".git").is_dir()
        ):
            return None, JSONResponse({"error": "ip has no .git", "ip": clean}, status_code=409), clean
        return str(candidate), None, clean

    def _route_cwd(ip: str, provider: str = "") -> tuple[str | None, JSONResponse | None, str]:
        return _scm_cwd_for_ip(ip or active_ip_value(), provider=provider)

    @app.get("/api/scm/status")
    @app.get("/api/git/status")
    async def api_git_status(ip: str = "", provider: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip, provider=provider)
        if error is not None:
            return error
        status = await _scm_call(cwd, "status", provider=provider)
        payload = {
            "provider": status.get("provider", "git"),
            "branch": status.get("branch", ""),
            "head": status.get("head", ""),
            "head_full": status.get("head_full", ""),
            "ahead": int(status.get("ahead", 0) or 0),
            "behind": int(status.get("behind", 0) or 0),
            "dirty": bool(status.get("dirty", False)),
            "files": status.get("files", []),
            "ip": resolved_ip,
            "cwd": cwd,
        }
        if not status.get("ok", True):
            payload["error"] = status.get("error") or "scm status failed"
        return JSONResponse(payload, status_code=200)

    @app.get("/api/scm/log")
    @app.get("/api/git/log")
    async def api_git_log(ip: str = "", limit: int = 60, provider: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip, provider=provider)
        if error is not None:
            return error
        log = await _scm_call(cwd, "log", limit, provider=provider)
        if not log.get("ok", True):
            return JSONResponse({
                "error": log.get("error") or "scm log failed",
                "commits": [],
                "branch": log.get("branch", ""),
                "provider": log.get("provider", "git"),
                "ip": resolved_ip,
            }, status_code=200)
        return JSONResponse({
            "commits": log.get("commits", []),
            "branch": log.get("branch", ""),
            "provider": log.get("provider", "git"),
            "ip": resolved_ip, "cwd": cwd,
        })

    @app.get("/api/scm/show")
    @app.get("/api/git/show")
    async def api_git_show(sha: str = "", revision: str = "", ip: str = "", provider: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip, provider=provider)
        if error is not None:
            return error
        selected_revision = (sha or revision).strip()
        provider_name = _scm_provider_for_cwd(cwd, provider=provider)
        if not selected_revision:
            return JSONResponse({"error": "invalid revision"}, status_code=400)
        if provider_name == "git" and not re.match(r"^[0-9a-f]{4,40}$", selected_revision):
            return JSONResponse({"error": "invalid sha"}, status_code=400)
        if provider_name != "git" and not re.match(r"^[0-9A-Za-z._/@#:+-]{1,160}$", selected_revision):
            return JSONResponse({"error": "invalid revision"}, status_code=400)
        result = await _scm_call(cwd, "show", selected_revision, provider=provider)
        if not result.ok:
            return JSONResponse({
                "error": result.error or f"scm show {selected_revision} failed",
                "diff": "",
                "provider": result.provider,
            }, status_code=200)
        return JSONResponse({
            "sha": selected_revision,
            "revision": selected_revision,
            "diff": result.stdout,
            "provider": result.provider,
            "ip": resolved_ip,
        })

    @app.get("/api/scm/diff")
    @app.get("/api/git/diff")
    async def api_git_diff(path: str = "", staged: int = 0, ip: str = "", provider: str = ""):
        cwd, error, resolved_ip = _route_cwd(ip, provider=provider)
        if error is not None:
            return error
        result = await _scm_call(cwd, "diff", path, bool(staged), provider=provider)
        if not result.ok and not result.stdout:
            return JSONResponse({
                "error": result.error or "diff failed",
                "diff": "",
                "provider": result.provider,
            }, status_code=200)
        return JSONResponse({
            "diff": result.stdout,
            "path": path,
            "provider": result.provider,
            "ip": resolved_ip,
        })

    @app.post("/api/scm/submit")
    @app.post("/api/git/commit")
    async def api_git_commit(payload: dict[str, Any]):
        body = payload or {}
        message = str(body.get("message", "")).strip()
        add_all = bool((payload or {}).get("add_all", True))
        provider = str(body.get("provider") or "")
        if not message:
            return JSONResponse({"error": "commit message required"},
                                 status_code=400)
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""), provider=provider)
        if error is not None:
            return error
        result = await _scm_call(cwd, "submit", message, add_all=add_all, provider=provider)
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
        })

    @app.post("/api/scm/push")
    @app.post("/api/git/push")
    async def api_git_push(payload: Optional[dict[str, Any]] = None):
        body = payload or {}
        provider = str(body.get("provider") or "")
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""), provider=provider)
        if error is not None:
            return error
        status = await _scm_call(cwd, "status", provider=provider)
        if not status.get("ok", True):
            return JSONResponse({
                "ok": False,
                "stdout": "",
                "stderr": "",
                "error": status.get("error") or "scm status failed",
                "branch": "",
                "returncode": 78,
                "provider": status.get("provider", "git"),
                "ip": resolved_ip,
            }, status_code=200)
        branch = str(status.get("branch", "")).strip()
        if not branch or branch == "HEAD":
            return JSONResponse({"error": "no current branch (detached HEAD?)"},
                                 status_code=400)
        result = await _scm_call(cwd, "push", branch, provider=provider)
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "branch": branch,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
        })

    def _scm_result_json(result, resolved_ip: str):
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
        })

    @app.post("/api/scm/sync")
    @app.post("/api/git/sync")
    async def api_scm_sync(payload: Optional[dict[str, Any]] = None):
        # Pull from the server, overwriting local (force). Optional `paths` for a
        # selective sync; `revision` to pin a changelist. sync() is part of the
        # base SCM contract, so this works for any provider.
        body = payload or {}
        provider = str(body.get("provider") or "")
        revision = str(body.get("revision") or "")
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""), provider=provider)
        if error is not None:
            return error
        paths = body.get("paths") or []
        if paths:
            result, _prov, supported = await _scm_optional(cwd, "sync_paths", paths, revision, provider=provider)
            if not supported:
                result = await _scm_call(cwd, "sync", revision, provider=provider)
        else:
            result = await _scm_call(cwd, "sync", revision, provider=provider)
        return _scm_result_json(result, resolved_ip)

    @app.get("/api/scm/pane")
    async def api_scm_pane(ip: str = "", provider: str = ""):
        # Two-pane Perforce Sync view: local / depot / pending. Provider-specific.
        cwd, error, resolved_ip = _route_cwd(ip, provider=provider)
        if error is not None:
            return error
        state, prov, supported = await _scm_optional(cwd, "sync_state", provider=provider)
        if not supported:
            return JSONResponse({
                "ok": False,
                "provider": prov,
                "ip": resolved_ip,
                "error": f"pane view is not supported for provider '{prov}'",
                "local": [], "depot": [], "pending": [],
            }, status_code=200)
        state = dict(state or {})
        state["ip"] = resolved_ip
        state["cwd"] = cwd
        return JSONResponse(state, status_code=200)

    @app.post("/api/scm/add")
    async def api_scm_add(payload: dict[str, Any]):
        # Open selected local paths for add/edit/delete (p4 reconcile) into the
        # pending changelist. Provider-specific (Perforce).
        body = payload or {}
        provider = str(body.get("provider") or "")
        paths = body.get("paths") or []
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""), provider=provider)
        if error is not None:
            return error
        result, prov, supported = await _scm_optional(cwd, "open_paths", paths, provider=provider)
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"add/open is not supported for provider '{prov}'",
            }, status_code=200)
        return _scm_result_json(result, resolved_ip)

    @app.post("/api/scm/revert")
    async def api_scm_revert(payload: dict[str, Any]):
        # Revert selected pending paths (p4 revert). Provider-specific (Perforce).
        body = payload or {}
        provider = str(body.get("provider") or "")
        paths = body.get("paths") or []
        cwd, error, resolved_ip = _route_cwd(str(body.get("ip") or ""), provider=provider)
        if error is not None:
            return error
        result, prov, supported = await _scm_optional(cwd, "revert_paths", paths, provider=provider)
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"revert is not supported for provider '{prov}'",
            }, status_code=200)
        return _scm_result_json(result, resolved_ip)
