"""File serving + listing + folding API routes — extracted from src/atlas_ui.py.

Phase 8/9 of refactor/atlas-modular: convert FastAPI route closures inside
create_app() into a single factory function. All previously-captured
helpers/state are passed explicitly as keyword arguments so this module
holds no atlas_ui import (one-way dep: atlas_ui → atlas_api_files).

Endpoints registered:
- GET /api/files         — list a directory (recursive option)
- GET /api/file          — read text preview (capped at max_read_bytes)
- GET /api/file/raw      — serve raw bytes with mime-typed FileResponse
- DELETE /api/file/delete — delete a file under an IP root (guarded)
- GET /api/fold-symbols  — extractor-derived fold ranges (mtime-cached)
"""
from __future__ import annotations

import asyncio
import os
import subprocess
import sys
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Optional, cast

from fastapi import Request
from fastapi.responses import JSONResponse

from core.atlas_context import AtlasContext

IP_LOCAL_ROOTS = frozenset({
    "artifacts",
    "cov",
    "coverage",
    "doc",
    "lint",
    "list",
    "logs",
    "model",
    "mutation",
    "pnr",
    "req",
    "rtl",
    "signoff",
    "sim",
    "syn",
    "tb",
    "todo",
    "verify",
    "workflow",
    "yaml",
})


def register_file_routes(
    app: Any,
    *,
    safe_path_fn: Callable[[str], Optional[Path]],
    project_root: Path,
    skip_dirs: Any,
    is_hidden_artifact_fn: Callable[[Path, Path], bool],
    max_read_bytes: int,
    safe_ip_delete_fn: Callable[[str, str], tuple[Path | None, str | None]],
    bridge: Any,
    fs_authz: Any = None,
    fold_max_bytes: int = 5 * 1024 * 1024,
    fold_max_lines: int = 10_000,
    fold_cache_cap: int = 128,
) -> None:
    """Wire /api/files, /api/file, /api/file/raw, /api/file/delete, and
    /api/fold-symbols onto `app`. Each injected dep replaces what the
    original closure captured from create_app() scope.
    """

    # Module-private fold cache (mtime-keyed LRU).
    fold_cache: "OrderedDict[str, tuple[float, list[Any]]]" = OrderedDict()

    # ── B1 read/write gate (injected by create_app; None only in old/direct
    # callers, where it is a no-op to preserve their behavior). ──────────────
    def _gate(request, rel_path, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.path(request, rel_path, permission)

    def _gate_ip(request, ip, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.ip(request, ip, permission)

    def _context_for_session(session_id: str) -> AtlasContext | None:
        raw = str(session_id or "").strip()
        if not raw:
            return None
        try:
            return AtlasContext.from_session_key(
                raw,
                atlas_root=os.environ.get("ATLAS_ROOT") or str(project_root),
            )
        except Exception:
            return None

    def _context_base(context: AtlasContext | None) -> Path:
        if context is not None and not context.legacy:
            return context.workspace_root
        return project_root

    def _clean_rel_path(rel_path: str) -> str:
        return str(rel_path or "").replace("\\", "/").lstrip("/")

    def _session_rel_path(context: AtlasContext | None, rel_path: str) -> str:
        rel = _clean_rel_path(rel_path)
        if context is None or context.legacy or not rel or str(rel_path or "").startswith("/"):
            return rel
        prefix = f"{context.user_name}/{context.workspace_session}/"
        if rel.startswith(prefix):
            rel = rel[len(prefix):]
        ip_name = str(context.ip_name or "").strip()
        if not ip_name or ip_name == "default":
            return rel
        first = rel.split("/", 1)[0]
        if first == ip_name:
            return rel
        if first in IP_LOCAL_ROOTS:
            return f"{ip_name}/{rel}"
        candidate = context.workspace_root / ip_name / rel
        if candidate.exists():
            return f"{ip_name}/{rel}"
        return rel

    def _safe_in_base(base: Path, rel_path: str) -> Optional[Path]:
        rel = _clean_rel_path(rel_path)
        try:
            candidate = (base / rel).resolve()
            candidate.relative_to(base.resolve())
            return candidate
        except (OSError, ValueError):
            return None

    def _target_for_session(path: str, session_id: str) -> tuple[Optional[Path], Path, AtlasContext | None, str]:
        context = _context_for_session(session_id)
        base = _context_base(context)
        if base == project_root:
            target = safe_path_fn(path)
            rel = _clean_rel_path(path)
            if target is not None:
                try:
                    rel = target.resolve().relative_to(project_root.resolve()).as_posix()
                except (OSError, ValueError):
                    pass
            return target, project_root, context, rel
        rel = _session_rel_path(context, path)
        target = _safe_in_base(base, rel)
        if target is not None:
            try:
                rel = target.resolve().relative_to(base.resolve()).as_posix()
            except (OSError, ValueError):
                pass
        return target, base, context, rel

    def _deny_context_request(request: Request, context: AtlasContext | None):
        if context is None or context.legacy:
            return None
        try:
            user = request.scope.get("user") or {}
        except Exception:
            user = {}
        user_id = str((user or {}).get("id") or "").strip()
        if not user_id or user_id == "default":
            return JSONResponse({"error": "login required"}, status_code=401)
        if str((user or {}).get("role") or "").strip().lower() == "admin":
            return None
        username = str((user or {}).get("username") or "").strip().strip("/")
        if username == context.user_name:
            return None
        return JSONResponse({"error": "session owner mismatch"}, status_code=403)

    def _gate_for_context_path(
        request: Request,
        rel_path: str,
        context: AtlasContext | None,
        permission: str = "view",
    ):
        denied = _deny_context_request(request, context)
        if denied is not None:
            return denied
        if context is not None and not context.legacy:
            return None
        return _gate(request, rel_path, permission)

    @app.get("/api/files")
    async def api_files(request: Request, path: str = "", recursive: int = 0,
                          max_depth: int = 4, max_entries: int = 800,
                          session_id: str = "", session: str = ""):
        target, root, context, requested_rel = _target_for_session(path, session_id or session)
        if target is None:
            return JSONResponse({"error": "path outside project root"},
                                status_code=400)
        if not target.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        rel = "" if target == root else target.relative_to(root).as_posix()
        if not rel:
            requested_rel = ""
        denied = _deny_context_request(request, context)
        if denied is not None:
            return denied
        # A specific path must be readable by the caller; the project-root
        # listing is instead FILTERED to the caller's accessible top-level
        # entries (shared roots + owned/granted IPs) so the IP-rooted file tree
        # keeps working without leaking other tenants' IP directories.
        if rel:
            denied = _gate_for_context_path(request, requested_rel or rel, context)
            if denied is not None:
                return denied
        if target.is_file():
            stat = target.stat()
            return JSONResponse({
                "type": "file", "path": rel,
                "size": stat.st_size, "mtime": stat.st_mtime,
            })

        allowed_ips = fs_authz.accessible_ips(request) if fs_authz is not None else None
        shared_roots = getattr(fs_authz, "shared_roots", frozenset()) if fs_authz is not None else frozenset()
        shared_files = getattr(fs_authz, "shared_root_files", frozenset()) if fs_authz is not None else frozenset()
        restrict_top = (rel == "" and allowed_ips is not None)

        entries: list[dict[str, Any]] = []

        def _top_allowed(name: str) -> bool:
            return name in shared_roots or name in cast(set[str], allowed_ips)

        def _list_one(d, depth):
            try:
                children = sorted(d.iterdir(),
                                   key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return
            for child in children:
                if len(entries) >= max_entries:
                    return
                if child.name in skip_dirs or child.name.startswith("."):
                    continue
                # At the project root, hide top-level IP dirs the caller cannot
                # access, and non-shared root-level files (avoid filename
                # disclosure of, e.g., another tenant's stray exports).
                if restrict_top and depth == 0 and child.is_dir() and not _top_allowed(child.name):
                    continue
                if restrict_top and depth == 0 and child.is_file() and child.name not in shared_files:
                    continue
                if child.is_file() and is_hidden_artifact_fn(child, target):
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    continue
                entries.append({
                    "name":  child.name if not recursive else child.relative_to(target).as_posix(),
                    "type":  "dir" if child.is_dir() else "file",
                    "size":  stat.st_size if child.is_file() else None,
                    "mtime": stat.st_mtime,
                    "depth": depth,
                })
                if recursive and child.is_dir() and depth < max_depth:
                    _list_one(child, depth + 1)

        _list_one(target, 0)
        return JSONResponse({"type": "dir", "path": rel,
                              "entries": entries,
                              "truncated": len(entries) >= max_entries})

    @app.get("/api/file")
    async def api_file(request: Request, path: str, session_id: str = "", session: str = ""):
        target, _root, context, rel_path = _target_for_session(path, session_id or session)
        denied = _gate_for_context_path(request, rel_path, context)
        if denied is not None:
            return denied
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        try:
            def _read_preview():
                stat = target.stat()
                data = target.read_bytes()[:max_read_bytes]
                return stat, data.decode("utf-8", errors="replace")
            stat, content = await asyncio.to_thread(_read_preview)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        truncated = stat.st_size > max_read_bytes
        return JSONResponse({
            "path": rel_path or path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    @app.post("/api/vcm/emit")
    async def api_vcm_emit(request: Request, payload: Optional[dict] = None):
        # Generate <ip>/req/vcm_graph.json on demand for the VCM tab, resolving
        # the caller's session-scoped IP path (same resolution as /api/file) and
        # running the trusted emit_vcm_graph.py from the workflow root. The
        # script path is NEVER taken from the request — only ip + session are.
        body = payload or {}
        ip = str(body.get("ip") or "").strip()
        session_id = str(body.get("session_id") or body.get("session") or "").strip()
        if not ip:
            return JSONResponse({"ok": False, "error": "ip required"}, status_code=400)
        target, _base, context, rel = _target_for_session(ip, session_id)
        denied = _gate_for_context_path(request, rel or ip, context, permission="edit")
        if denied is not None:
            return denied
        if target is None:
            return JSONResponse({"ok": False, "error": "ip path outside workspace"}, status_code=400)
        ip_dir = target
        if not (ip_dir / "req").is_dir():
            return JSONResponse({"ok": False, "error": f"{ip} has no req/ bundle to graph"}, status_code=200)
        try:
            from src.atlas_runtime import _resolve_workflow_root
            wf_env = os.environ.get("ATLAS_WORKFLOW_ROOT", "").strip()
            wf_root = Path(wf_env).expanduser() if wf_env else _resolve_workflow_root()
        except Exception:
            wf_root = None
        emitter = (Path(wf_root) / "req-gen" / "scripts" / "emit_vcm_graph.py") if wf_root else None
        if emitter is None or not emitter.is_file():
            return JSONResponse({"ok": False, "error": "emit_vcm_graph.py not found (workflow root)"}, status_code=200)

        def _run():
            return subprocess.run(
                [sys.executable, str(emitter), ip_dir.name, "--root", str(ip_dir.parent)],
                capture_output=True, text=True, timeout=60, check=False,
            )
        try:
            proc = await asyncio.to_thread(_run)
        except subprocess.TimeoutExpired:
            return JSONResponse({"ok": False, "error": "emit timed out"}, status_code=200)
        out = ((proc.stdout or "") + (proc.stderr or "")).strip()
        if proc.returncode != 0 or not (ip_dir / "req" / "vcm_graph.json").is_file():
            return JSONResponse({"ok": False, "error": out or "emit failed"}, status_code=200)
        return JSONResponse({"ok": True, "stdout": out})

    @app.delete("/api/file/delete")
    async def api_file_delete(
        request: Request,
        ip: str = "",
        path: str = "",
        session_id: str = "",
        session: str = "",
    ):
        session_name = session_id or session
        context = _context_for_session(session_name)
        clean_ip = str(ip or "").strip().strip("/")
        clean_path = _clean_rel_path(path)
        rel_path = clean_path

        if context is not None and not context.legacy:
            denied = _deny_context_request(request, context)
            if denied is not None:
                return denied
            if not clean_ip or clean_ip == "default":
                clean_ip = context.ip_name
            # NOTE: deliberately do NOT require clean_ip == context.ip_name.
            # _deny_context_request above already proves the caller owns the
            # session (= their workspace), _target_for_session resolves the
            # file under that workspace_root, and the ip_root containment check
            # below confirms it sits in <workspace>/<clean_ip>. Requiring the
            # file's IP to match the active chat session's IP only blocked
            # legitimate deletes when the file tree shows a different IP than
            # the active session (the file is visible in the tree but undeletable).
            if not clean_ip or not clean_path:
                return JSONResponse({"error": "ip and path are required"}, status_code=400)
            parts = [part for part in clean_path.split("/") if part]
            if any(part in {".", ".."} for part in parts):
                return JSONResponse({"error": "invalid path"}, status_code=400)
            if any(part.startswith(".") for part in parts):
                return JSONResponse({"error": "hidden/internal files cannot be deleted from the UI"}, status_code=400)
            target, root, _context, rel_path = _target_for_session(clean_path, session_name)
            ip_root = (root / clean_ip).resolve()
            if target is None:
                return JSONResponse({"error": "path outside project root"}, status_code=400)
            try:
                resolved_target = target.resolve()
                resolved_target.relative_to(ip_root)
            except (OSError, ValueError):
                return JSONResponse({"error": "path is outside the selected IP"}, status_code=400)
            if resolved_target == ip_root:
                return JSONResponse({"error": "cannot delete the IP root"}, status_code=400)
            if not ip_root.is_dir():
                return JSONResponse({"error": "IP not found"}, status_code=404)
            if target.is_dir():
                return JSONResponse({"error": "directory delete is not supported from the UI"}, status_code=400)
            if not target.is_file():
                return JSONResponse({"error": "file not found"}, status_code=404)
            clean_path = rel_path or clean_path
        else:
            denied = _gate_ip(request, ip, "write")
            if denied is not None:
                return denied
            target, error = safe_ip_delete_fn(ip, path)
            if target is None:
                status = 404 if error in {"IP not found", "file not found"} else 400
                return JSONResponse({"error": error or "not found"}, status_code=status)
        try:
            await asyncio.to_thread(target.unlink)
        except OSError as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)
        try:
            bridge.emit("file_changed", path=clean_path, tool="delete_file", ip=clean_ip, deleted=True)
        except Exception:
            pass
        return JSONResponse({"deleted": True, "ip": clean_ip, "path": clean_path})

    @app.get("/api/file/raw")
    async def api_file_raw(request: Request, path: str, session_id: str = "", session: str = ""):
        """Serve a file's raw bytes with a guessed content-type.

        Used by the PreviewPane and inline-markdown rendering to display
        images (.png/.jpg/...) and other binary previews. Text files also
        flow through here when the caller wants the un-decoded bytes.
        """
        target, _root, context, rel_path = _target_for_session(path, session_id or session)
        denied = _gate_for_context_path(request, rel_path, context)
        if denied is not None:
            return denied
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        ext = target.suffix.lower().lstrip(".")
        mime = {
            "png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg",
            "gif": "image/gif", "webp": "image/webp", "bmp": "image/bmp",
            "svg": "image/svg+xml", "tif": "image/tiff", "tiff": "image/tiff",
            "ico": "image/x-icon", "pdf": "application/pdf",
            "md": "text/markdown; charset=utf-8",
            "txt": "text/plain; charset=utf-8",
            "html": "text/html; charset=utf-8", "htm": "text/html; charset=utf-8",
            "json": "application/json",
            "yaml": "application/x-yaml", "yml": "application/x-yaml",
        }.get(ext, "application/octet-stream")
        try:
            from fastapi.responses import FileResponse as _FR
            return _FR(target, media_type=mime, filename=target.name,
                       content_disposition_type="inline")
        except Exception as exc:
            return JSONResponse({"error": str(exc)}, status_code=500)

    @app.get("/api/fold-symbols")
    async def api_fold_symbols(request: Request, path: str, session_id: str = "", session: str = ""):
        target, _root, context, rel_path = _target_for_session(path, session_id or session)
        denied = _gate_for_context_path(request, rel_path, context)
        if denied is not None:
            return denied
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        stat = target.stat()
        payload_path = rel_path or path
        scope = context.active_session_key if context is not None else ""
        cache_key = f"{scope}\n{payload_path}" if scope else payload_path
        cached = fold_cache.get(cache_key)
        if cached and cached[0] == stat.st_mtime:
            fold_cache.move_to_end(cache_key)
            return JSONResponse({"path": payload_path, "ranges": cached[1], "cached": True})
        if stat.st_size > fold_max_bytes:
            return JSONResponse({
                "path": payload_path, "ranges": [], "skipped": True,
                "reason": f"file > {fold_max_bytes // (1024*1024)} MB",
            })
        try:
            text = await asyncio.to_thread(
                lambda: target.read_text(encoding="utf-8", errors="replace")
            )
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        if text.count("\n") > fold_max_lines:
            return JSONResponse({
                "path": payload_path, "ranges": [], "skipped": True,
                "reason": f"more than {fold_max_lines} lines",
            })
        try:
            from core.fold_extractor import folds_for_path
            ranges = await asyncio.to_thread(folds_for_path, payload_path, text)
        except Exception as e:
            return JSONResponse({
                "path": payload_path, "ranges": [], "error": f"extractor failed: {e}",
            }, status_code=422)
        fold_cache[cache_key] = (stat.st_mtime, ranges)
        fold_cache.move_to_end(cache_key)
        while len(fold_cache) > fold_cache_cap:
            fold_cache.popitem(last=False)
        return JSONResponse({"path": payload_path, "ranges": ranges, "cached": False})
