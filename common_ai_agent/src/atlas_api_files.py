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
from collections import OrderedDict
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import Request
from fastapi.responses import JSONResponse


def register_file_routes(
    app: Any,
    *,
    safe_path_fn: Callable[[str], Optional[Path]],
    project_root: Path,
    skip_dirs: Any,
    is_hidden_artifact_fn: Callable[[Path, Path], bool],
    max_read_bytes: int,
    safe_ip_delete_fn: Callable[[str, str], tuple],
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
    fold_cache: "OrderedDict[str, tuple]" = OrderedDict()

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

    @app.get("/api/files")
    async def api_files(request: Request, path: str = "", recursive: int = 0,
                          max_depth: int = 4, max_entries: int = 800):
        target = safe_path_fn(path)
        if target is None:
            return JSONResponse({"error": "path outside project root"},
                                status_code=400)
        if not target.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        rel = "" if target == project_root else target.relative_to(project_root).as_posix()
        # A specific path must be readable by the caller; the project-root
        # listing is instead FILTERED to the caller's accessible top-level
        # entries (shared roots + owned/granted IPs) so the IP-rooted file tree
        # keeps working without leaking other tenants' IP directories.
        if rel:
            denied = _gate(request, rel)
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

        entries: list = []

        def _top_allowed(name: str) -> bool:
            return name in shared_roots or name in allowed_ips

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
    async def api_file(request: Request, path: str):
        denied = _gate(request, path)
        if denied is not None:
            return denied
        target = safe_path_fn(path)
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
            "path": path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    @app.delete("/api/file/delete")
    async def api_file_delete(request: Request, ip: str = "", path: str = ""):
        denied = _gate_ip(request, ip, "write")
        if denied is not None:
            return denied
        target, error = safe_ip_delete_fn(ip, path)
        if target is None:
            status = 404 if error in {"IP not found", "file not found"} else 400
            return JSONResponse({"error": error or "not found"}, status_code=status)
        clean_ip = str(ip or "").strip().strip("/")
        clean_path = str(path or "").strip().strip("/")
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
    async def api_file_raw(request: Request, path: str):
        """Serve a file's raw bytes with a guessed content-type.

        Used by the PreviewPane and inline-markdown rendering to display
        images (.png/.jpg/...) and other binary previews. Text files also
        flow through here when the caller wants the un-decoded bytes.
        """
        denied = _gate(request, path)
        if denied is not None:
            return denied
        target = safe_path_fn(path)
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
    async def api_fold_symbols(request: Request, path: str):
        denied = _gate(request, path)
        if denied is not None:
            return denied
        target = safe_path_fn(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        stat = target.stat()
        # mtime-keyed LRU
        cached = fold_cache.get(path)
        if cached and cached[0] == stat.st_mtime:
            fold_cache.move_to_end(path)
            return JSONResponse({"path": path, "ranges": cached[1], "cached": True})
        if stat.st_size > fold_max_bytes:
            return JSONResponse({
                "path": path, "ranges": [], "skipped": True,
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
                "path": path, "ranges": [], "skipped": True,
                "reason": f"more than {fold_max_lines} lines",
            })
        try:
            from core.fold_extractor import folds_for_path
            ranges = await asyncio.to_thread(folds_for_path, path, text)
        except Exception as e:
            return JSONResponse({
                "path": path, "ranges": [], "error": f"extractor failed: {e}",
            }, status_code=422)
        fold_cache[path] = (stat.st_mtime, ranges)
        fold_cache.move_to_end(path)
        while len(fold_cache) > fold_cache_cap:
            fold_cache.popitem(last=False)
        return JSONResponse({"path": path, "ranges": ranges, "cached": False})
