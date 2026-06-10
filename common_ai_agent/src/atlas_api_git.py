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
import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.atlas_context_paths import AtlasContext
from core.scm import (
    configured_scm_provider,
    resolve_scm_adapter,
    scm_provider_allows_missing_git_dir,
)
from core.session_names import normalize_session_name


def register_git_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    active_ip_value: Callable[[], str],
    valid_ip_name: Callable[[str], bool],
    fs_authz=None,
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

    async def _scm_call(scm_root: str | None, method: str, *args, provider: str = "", **kwargs):
        # `cwd` lets callers target the per-IP SCM workspace
        # (PROJECT_ROOT/<ip>) instead of the outer project workspace.
        # The actual provider is resolved per request so a deployment can
        # switch from Git to Perforce via ATLAS_SCM_PROVIDER.
        adapter = resolve_scm_adapter(scm_root or str(project_root()), provider=_request_provider(provider) or None)
        func = getattr(adapter, method)
        return await asyncio.to_thread(func, *args, **kwargs)

    async def _scm_optional(scm_root: str | None, method: str, *args, provider: str = "", **kwargs):
        # Like _scm_call but for provider-specific methods (e.g. Perforce-only
        # sync_state/open_paths). Returns (result_or_None, provider, supported).
        adapter = resolve_scm_adapter(scm_root or str(project_root()), provider=_request_provider(provider) or None)
        if not hasattr(adapter, method):
            return None, adapter.provider, False
        func = getattr(adapter, method)
        return (await asyncio.to_thread(func, *args, **kwargs)), adapter.provider, True

    def _scm_provider_for_root(scm_root: str | None, provider: str = ""):
        return resolve_scm_adapter(scm_root or str(project_root()), provider=_request_provider(provider) or None).provider

    def _resolve_existing_root(value: str, label: str) -> tuple[Path | None, JSONResponse | None]:
        clean = str(value or "").strip()
        if not clean:
            return None, None
        candidate = Path(clean).expanduser()
        if not candidate.is_absolute():
            candidate = project_root() / candidate
        resolved = candidate.resolve()
        # SECURITY: a request-supplied scmRoot must not escape PROJECT_ROOT
        # (absolute-path / traversal escape). resolve()+relative_to is OS-neutral
        # — it handles Windows drive letters, UNC paths, and backslashes too.
        # Perforce workspaces that legitimately live elsewhere are configured via
        # env (ATLAS_SCM_ROOT_PERFORCE / _default_scm_root), not this param.
        try:
            resolved.relative_to(project_root().resolve())
        except ValueError:
            return None, JSONResponse({"error": f"{label} escapes project root"}, status_code=400)
        if not resolved.is_dir():
            return None, JSONResponse({"error": f"{label} not found", label: str(resolved)}, status_code=404)
        return resolved, None

    def _context_atlas_root() -> Path:
        raw = os.environ.get("ATLAS_ROOT", "").strip()
        return (Path(raw).expanduser() if raw else project_root()).resolve()

    def _context_for_session(session_id: str) -> tuple[AtlasContext | None, JSONResponse | None]:
        session = normalize_session_name(str(session_id or ""))
        if not session:
            return None, None
        parts = [part for part in session.split("/") if part]
        if len(parts) not in {3, 4}:
            return None, JSONResponse(
                {"error": "session_id must be owner/ip/workflow or user/session/ip/workflow"},
                status_code=400,
            )
        try:
            return AtlasContext.from_session_key(session, atlas_root=_context_atlas_root()), None
        except ValueError as exc:
            return None, JSONResponse({"error": str(exc)}, status_code=400)

    def _root_relative_base(local_root: Path) -> Path:
        project = project_root().resolve()
        try:
            local_root.resolve().relative_to(project)
            return project
        except ValueError:
            return local_root.resolve().parent

    def _default_scm_root(provider: str, local_root: Path) -> Path:
        selected = _request_provider(provider) or configured_scm_provider()
        if selected != "perforce":
            return local_root
        relative_base = _root_relative_base(local_root)
        configured = (
            os.environ.get("ATLAS_SCM_ROOT_PERFORCE", "").strip()
            or os.environ.get("ATLAS_PERFORCE_ROOT", "").strip()
            or os.environ.get("P4_WORKSPACE_ROOT", "").strip()
        )
        if configured:
            candidate = Path(configured).expanduser()
            if not candidate.is_absolute():
                candidate = relative_base / candidate
            if candidate.is_dir():
                return candidate.resolve()
        candidate = relative_base / "perforce"
        return candidate.resolve() if candidate.is_dir() else relative_base.resolve()

    def _scm_roots_for_ip(
        ip: str,
        provider: str = "",
        scm_root_value: str = "",
        session_id: str = "",
    ) -> tuple[str | None, str | None, JSONResponse | None, str]:
        """Resolve the cwd for a per-IP SCM workspace.

        Empty IP keeps the legacy project-root SCM view. A non-empty IP is
        explicit user intent, so never fall back to PROJECT_ROOT: returning the
        outer workspace for a missing per-IP workspace makes submit/push hit
        the wrong source-control root.
        """
        context, context_error = _context_for_session(session_id)
        if context_error is not None:
            return None, None, context_error, ""
        clean = str(ip or "").strip()
        if context is not None and not clean:
            clean = context.ip_name
        workspace_root = context.workspace_root.resolve() if context is not None else project_root().resolve()
        if not clean:
            local_root = workspace_root
            explicit_scm, explicit_error = _resolve_existing_root(scm_root_value, "scmRoot")
            if explicit_error is not None:
                return None, None, explicit_error, ""
            scm_root = explicit_scm or _default_scm_root(provider, local_root)
            return str(local_root), str(scm_root), None, ""
        if not valid_ip_name(clean):
            return None, None, JSONResponse({"error": "invalid ip", "ip": clean}, status_code=400), clean
        candidate = (workspace_root / clean).resolve()
        try:
            candidate.relative_to(workspace_root)
        except ValueError:
            return None, None, JSONResponse({"error": "ip path escapes project root", "ip": clean}, status_code=400), clean
        if not candidate.is_dir():
            return None, None, JSONResponse({"error": "ip not found", "ip": clean}, status_code=404), clean
        if (
            not scm_provider_allows_missing_git_dir(_request_provider(provider) or configured_scm_provider())
            and not (candidate / ".git").is_dir()
        ):
            return None, None, JSONResponse({"error": "ip has no .git", "ip": clean}, status_code=409), clean
        explicit_scm, explicit_error = _resolve_existing_root(scm_root_value, "scmRoot")
        if explicit_error is not None:
            return None, None, explicit_error, clean
        scm_root = explicit_scm or _default_scm_root(provider, candidate)
        return str(candidate), str(scm_root), None, clean

    def _route_roots(
        request: Request,
        ip: str,
        provider: str = "",
        scm_root_value: str = "",
        session_id: str = "",
        permission: str = "view",
    ) -> tuple[str | None, str | None, JSONResponse | None, str]:
        local_root, scm_root, error, resolved_ip = _scm_roots_for_ip(
            ip or active_ip_value(),
            provider=provider,
            scm_root_value=scm_root_value,
            session_id=session_id,
        )
        # SECURITY: per-IP tenant authz at the single chokepoint every SCM route
        # passes through. A non-empty resolved IP must be owned/granted to the
        # caller (view to read, write to mutate). The authz verdict takes
        # PRECEDENCE over _scm_roots_for_ip's own existence/'.git' errors — a
        # cross-tenant probe must get 403, never a 404/409 that would leak the
        # target IP's existence or repo status. resolved_ip is populated even on
        # those errors (it is the cleaned/ session-resolved ip name), so this
        # also closes the session_id-spoof vector. Empty IP = legacy project-root
        # SCM view, left ungated. Denials surface via the `error` slot.
        if resolved_ip and fs_authz is not None:
            denied = fs_authz.ip(request, resolved_ip, permission)
            if denied is not None:
                return None, None, denied, resolved_ip
        return local_root, scm_root, error, resolved_ip

    def _root_fields(local_root: str | None, scm_root: str | None) -> dict[str, str | None]:
        return {"cwd": local_root, "localRoot": local_root, "scmRoot": scm_root}

    @app.get("/api/scm/status")
    @app.get("/api/git/status")
    async def api_git_status(request: Request, ip: str = "", provider: str = "", scm_root: str = "", session_id: str = ""):
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, ip, provider=provider, scm_root_value=scm_root, session_id=session_id,
        )
        if error is not None:
            return error
        kwargs = {"local_root": local_root} if _request_provider(provider) == "perforce" else {}
        status = await _scm_call(scm_root_path, "status", provider=provider, **kwargs)
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
            **_root_fields(local_root, scm_root_path),
        }
        if not status.get("ok", True):
            payload["error"] = status.get("error") or "scm status failed"
        return JSONResponse(payload, status_code=200)

    @app.get("/api/scm/log")
    @app.get("/api/git/log")
    async def api_git_log(
        request: Request,
        ip: str = "",
        limit: int = 60,
        provider: str = "",
        scm_root: str = "",
        stream: str = "",
        session_id: str = "",
    ):
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, ip, provider=provider, scm_root_value=scm_root, session_id=session_id,
        )
        if error is not None:
            return error
        kwargs = {"stream": stream} if stream and _request_provider(provider) == "perforce" else {}
        log = await _scm_call(scm_root_path, "log", limit, provider=provider, **kwargs)
        if not log.get("ok", True):
            return JSONResponse({
                "error": log.get("error") or "scm log failed",
                "commits": [],
                "branch": log.get("branch", ""),
                "provider": log.get("provider", "git"),
                "ip": resolved_ip,
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return JSONResponse({
            "commits": log.get("commits", []),
            "branch": log.get("branch", ""),
            "provider": log.get("provider", "git"),
            "ip": resolved_ip, **_root_fields(local_root, scm_root_path),
        })

    @app.get("/api/scm/show")
    @app.get("/api/git/show")
    async def api_git_show(
        request: Request,
        sha: str = "",
        revision: str = "",
        ip: str = "",
        provider: str = "",
        scm_root: str = "",
        stream: str = "",
        session_id: str = "",
    ):
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, ip, provider=provider, scm_root_value=scm_root, session_id=session_id,
        )
        if error is not None:
            return error
        selected_revision = (sha or revision).strip()
        provider_name = _scm_provider_for_root(scm_root_path, provider=provider)
        if not selected_revision:
            return JSONResponse({"error": "invalid revision"}, status_code=400)
        if provider_name == "git" and not re.match(r"^[0-9a-f]{4,40}$", selected_revision):
            return JSONResponse({"error": "invalid sha"}, status_code=400)
        if provider_name != "git" and not re.match(r"^[0-9A-Za-z._/@#:+-]{1,160}$", selected_revision):
            return JSONResponse({"error": "invalid revision"}, status_code=400)
        kwargs = {"stream": stream} if stream and provider_name == "perforce" else {}
        result = await _scm_call(scm_root_path, "show", selected_revision, provider=provider, **kwargs)
        if not result.ok:
            return JSONResponse({
                "error": result.error or f"scm show {selected_revision} failed",
                "diff": "",
                "provider": result.provider,
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return JSONResponse({
            "sha": selected_revision,
            "revision": selected_revision,
            "diff": result.stdout,
            "provider": result.provider,
            "ip": resolved_ip,
            **_root_fields(local_root, scm_root_path),
        })

    @app.get("/api/scm/diff")
    @app.get("/api/git/diff")
    async def api_git_diff(
        request: Request,
        path: str = "",
        staged: int = 0,
        ip: str = "",
        provider: str = "",
        scm_root: str = "",
        stream: str = "",
        session_id: str = "",
    ):
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, ip, provider=provider, scm_root_value=scm_root, session_id=session_id,
        )
        if error is not None:
            return error
        kwargs = {"local_root": local_root} if _request_provider(provider) == "perforce" else {}
        if stream and _request_provider(provider) == "perforce":
            kwargs["stream"] = stream
        result = await _scm_call(scm_root_path, "diff", path, bool(staged), provider=provider, **kwargs)
        if not result.ok and not result.stdout:
            return JSONResponse({
                "error": result.error or "diff failed",
                "diff": "",
                "provider": result.provider,
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return JSONResponse({
            "diff": result.stdout,
            "path": path,
            "provider": result.provider,
            "ip": resolved_ip,
            **_root_fields(local_root, scm_root_path),
        })

    @app.post("/api/scm/submit")
    @app.post("/api/git/commit")
    async def api_git_commit(request: Request, payload: dict[str, Any]):
        body = payload or {}
        message = str(body.get("message", "")).strip()
        add_all = bool((payload or {}).get("add_all", True))
        provider = str(body.get("provider") or "")
        stream = str(body.get("stream") or "")
        changelist = str(body.get("changelist") or body.get("change") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        if not message:
            return JSONResponse({"error": "commit message required"},
                                 status_code=400)
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        kwargs = {"stream": stream} if stream and _request_provider(provider) == "perforce" else {}
        if changelist and _request_provider(provider) == "perforce":
            kwargs["changelist"] = changelist
        result = await _scm_call(scm_root_path, "submit", message, add_all=add_all, provider=provider, **kwargs)
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
            **_root_fields(local_root, scm_root_path),
        })

    @app.post("/api/scm/push")
    @app.post("/api/git/push")
    async def api_git_push(request: Request, payload: Optional[dict[str, Any]] = None):
        body = payload or {}
        provider = str(body.get("provider") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        status = await _scm_call(scm_root_path, "status", provider=provider)
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
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        branch = str(status.get("branch", "")).strip()
        if not branch or branch == "HEAD":
            return JSONResponse({"error": "no current branch (detached HEAD?)"},
                                 status_code=400)
        result = await _scm_call(scm_root_path, "push", branch, provider=provider)
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "branch": branch,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
            **_root_fields(local_root, scm_root_path),
        })

    def _scm_result_json(result, resolved_ip: str, local_root: str | None, scm_root: str | None):
        return JSONResponse({
            "ok": result.ok,
            "stdout": result.stdout,
            "stderr": result.stderr,
            "error": result.error,
            "returncode": result.returncode,
            "provider": result.provider,
            "ip": resolved_ip,
            **_root_fields(local_root, scm_root),
        })

    @app.post("/api/scm/sync")
    @app.post("/api/git/sync")
    async def api_scm_sync(request: Request, payload: Optional[dict[str, Any]] = None):
        # Pull from the server, overwriting local (force). Optional `paths` for a
        # selective sync; `revision` to pin a changelist. sync() is part of the
        # base SCM contract, so this works for any provider.
        body = payload or {}
        provider = str(body.get("provider") or "")
        revision = str(body.get("revision") or "")
        stream = str(body.get("stream") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        target_paths = body.get("targetPaths") or body.get("target_paths") or []
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        paths = body.get("paths") or []
        if paths:
            kwargs = {"local_root": local_root, "target_paths": target_paths}
            if stream:
                kwargs["stream"] = stream
            result, _prov, supported = await _scm_optional(
                scm_root_path, "sync_paths", paths, revision, provider=provider, **kwargs,
            )
            if not supported:
                result = await _scm_call(scm_root_path, "sync", revision, provider=provider)
        elif _request_provider(provider) == "perforce" and target_paths:
            return JSONResponse({
                "ok": False,
                "provider": "perforce",
                "ip": resolved_ip,
                "error": "no Perforce files selected to sync",
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        else:
            kwargs = {"stream": stream} if stream and _request_provider(provider) == "perforce" else {}
            result = await _scm_call(scm_root_path, "sync", revision, provider=provider, **kwargs)
        return _scm_result_json(result, resolved_ip, local_root, scm_root_path)

    @app.get("/api/scm/pane")
    async def api_scm_pane(
        request: Request,
        ip: str = "",
        provider: str = "",
        stream: str = "",
        scm_root: str = "",
        session_id: str = "",
        local_dir: str = "",
        depot_dir: str = "",
    ):
        # Two-pane Perforce Sync view: local / depot / pending. Provider-specific.
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, ip, provider=provider, scm_root_value=scm_root, session_id=session_id,
        )
        if error is not None:
            return error
        kwargs = {"local_root": local_root}
        if stream:
            kwargs["stream"] = stream
        if _request_provider(provider) == "perforce":
            kwargs["local_dir"] = local_dir
            kwargs["depot_dir"] = depot_dir
        state, prov, supported = await _scm_optional(scm_root_path, "sync_state", provider=provider, **kwargs)
        if not supported:
            return JSONResponse({
                "ok": False,
                "provider": prov,
                "ip": resolved_ip,
                "error": f"pane view is not supported for provider '{prov}'",
                "local": [], "depot": [], "pending": [],
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        state = dict(state or {})
        state["ip"] = resolved_ip
        state.update(_root_fields(local_root, scm_root_path))
        return JSONResponse(state, status_code=200)

    @app.post("/api/scm/add")
    async def api_scm_add(request: Request, payload: dict[str, Any]):
        # Open selected local paths for add/edit/delete (p4 reconcile) into the
        # pending changelist. Provider-specific (Perforce).
        body = payload or {}
        provider = str(body.get("provider") or "")
        stream = str(body.get("stream") or "")
        paths = body.get("paths") or []
        target_paths = body.get("targetPaths") or body.get("target_paths") or []
        changelist = str(body.get("changelist") or body.get("change") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        kwargs = {"local_root": local_root, "target_paths": target_paths, "changelist": changelist}
        if stream:
            kwargs["stream"] = stream
        result, prov, supported = await _scm_optional(scm_root_path, "open_paths", paths, provider=provider, **kwargs)
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"add/open is not supported for provider '{prov}'",
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return _scm_result_json(result, resolved_ip, local_root, scm_root_path)

    @app.post("/api/scm/revert")
    async def api_scm_revert(request: Request, payload: dict[str, Any]):
        # Revert selected pending paths (p4 revert). Provider-specific (Perforce).
        body = payload or {}
        provider = str(body.get("provider") or "")
        stream = str(body.get("stream") or "")
        paths = body.get("paths") or []
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        kwargs = {"stream": stream} if stream else {}
        result, prov, supported = await _scm_optional(scm_root_path, "revert_paths", paths, provider=provider, **kwargs)
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"revert is not supported for provider '{prov}'",
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return _scm_result_json(result, resolved_ip, local_root, scm_root_path)

    @app.post("/api/scm/edit")
    async def api_scm_edit(request: Request, payload: dict[str, Any]):
        body = payload or {}
        provider = str(body.get("provider") or "")
        stream = str(body.get("stream") or "")
        paths = body.get("paths") or []
        target_paths = body.get("targetPaths") or body.get("target_paths") or []
        source_root = str(body.get("sourceRoot") or body.get("source_root") or "local").strip().lower()
        changelist = str(body.get("changelist") or body.get("change") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        kwargs = {"target_paths": target_paths, "changelist": changelist}
        if source_root != "scm":
            kwargs["local_root"] = local_root
        if stream:
            kwargs["stream"] = stream
        result, prov, supported = await _scm_optional(scm_root_path, "edit_paths", paths, provider=provider, **kwargs)
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"edit/open is not supported for provider '{prov}'",
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return _scm_result_json(result, resolved_ip, local_root, scm_root_path)

    def _scm_ui_prefs_path() -> Path:
        override = os.environ.get("ATLAS_SCM_UI_PREFS_PATH", "").strip()
        if override:
            return Path(override).expanduser()
        return Path.home() / ".common_ai_agent" / "perforce_ui_state.json"

    def _scm_ui_prefs_key(ip: str, session_id: str) -> str:
        owner = ""
        session = normalize_session_name(str(session_id or ""))
        if session:
            owner = session.split("/", 1)[0]
        clean_ip = str(ip or "").strip()
        if not valid_ip_name(clean_ip):  # invalid/empty ip shares the default bucket
            clean_ip = ""
        return f"{owner or 'default'}::{clean_ip or 'default'}"

    def _scm_ui_prefs_load() -> dict[str, Any]:
        path = _scm_ui_prefs_path()
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            return data if isinstance(data, dict) else {}
        except (OSError, ValueError):
            return {}

    @app.get("/api/scm/uiprefs")
    async def api_scm_ui_prefs_get(ip: str = "", session_id: str = ""):
        # Last-visited pane locations for the Perforce Sync tab, persisted in
        # the home directory so the user does not re-navigate on every visit.
        prefs = _scm_ui_prefs_load().get(_scm_ui_prefs_key(ip, session_id), {})
        if not isinstance(prefs, dict):
            prefs = {}
        return JSONResponse({"ok": True, "prefs": prefs})

    @app.post("/api/scm/uiprefs")
    async def api_scm_ui_prefs_set(payload: dict[str, Any]):
        body = payload or {}
        ip = str(body.get("ip") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or "")
        prefs = {
            key: str(body.get(key) or "")[:512]
            for key in ("localDir", "depotDir", "stream", "scmRoot")
            if str(body.get(key) or "")
        }
        path = _scm_ui_prefs_path()
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            # exclusive lock over read-modify-write: concurrent users must not
            # drop each other's just-saved locations (lost update)
            try:
                import fcntl
            except ImportError:  # Windows: atomic replace only, no flock
                fcntl = None
            with open(path.with_suffix(".lock"), "w", encoding="utf-8") as lock_file:
                if fcntl is not None:
                    fcntl.flock(lock_file, fcntl.LOCK_EX)
                data = _scm_ui_prefs_load()
                key = _scm_ui_prefs_key(ip, session_id)
                data.pop(key, None)  # re-insert at the end = most recent
                data[key] = prefs
                while len(data) > 200:  # bound junk-key growth (drop oldest)
                    data.pop(next(iter(data)))
                tmp = path.with_suffix(".tmp")
                tmp.write_text(json.dumps(data, indent=2), encoding="utf-8")
                tmp.replace(path)
        except OSError as exc:
            return JSONResponse({"ok": False, "error": str(exc)}, status_code=200)
        return JSONResponse({"ok": True, "prefs": prefs})

    @app.post("/api/scm/change/delete")
    async def api_scm_change_delete(request: Request, payload: dict[str, Any]):
        # Delete a numbered pending changelist (revert -k its files, then
        # p4 change -d). Provider-specific (Perforce).
        body = payload or {}
        provider = str(body.get("provider") or "")
        stream = str(body.get("stream") or "")
        changelist = str(body.get("changelist") or body.get("change") or "")
        scm_root_value = str(body.get("scmRoot") or body.get("scm_root") or "")
        session_id = str(body.get("session_id") or body.get("sessionId") or body.get("active_session") or "")
        local_root, scm_root_path, error, resolved_ip = _route_roots(
            request, str(body.get("ip") or ""), provider=provider, scm_root_value=scm_root_value, session_id=session_id, permission="write",
        )
        if error is not None:
            return error
        kwargs = {"stream": stream} if stream else {}
        result, prov, supported = await _scm_optional(
            scm_root_path, "delete_pending_changelist", changelist, provider=provider, **kwargs,
        )
        if not supported:
            return JSONResponse({
                "ok": False, "provider": prov, "ip": resolved_ip,
                "error": f"changelist delete is not supported for provider '{prov}'",
                **_root_fields(local_root, scm_root_path),
            }, status_code=200)
        return _scm_result_json(result, resolved_ip, local_root, scm_root_path)
