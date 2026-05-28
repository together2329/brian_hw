"""File serving API routes — extracted from src/atlas_ui.py.

PoC for closure extraction (Phase 8): convert FastAPI route closures into
a factory function (`register_file_routes`) that takes the previously-
captured helpers as keyword arguments. atlas_ui's create_app() calls
`register_file_routes(app, safe_path_fn=_safe)` at construction time, so
the routes wire to the same `_safe` resolver that captured PROJECT_ROOT.

This pattern is the template for the remaining route-cluster extractions
(Q&A board, workspace API, etc.).
"""
from __future__ import annotations

from pathlib import Path
from typing import Any, Callable, Optional

from fastapi.responses import JSONResponse


def register_file_routes(app: Any, *, safe_path_fn: Callable[[str], Optional[Path]]) -> None:
    """Wire /api/file/raw onto `app`.

    `safe_path_fn(path)` returns a Path inside PROJECT_ROOT or None if the
    path escapes / is rejected. Kept as an injected dep so this module
    stays free of atlas_ui imports.
    """

    @app.get("/api/file/raw")
    async def api_file_raw(path: str):
        """Serve a file's raw bytes with a guessed content-type.

        Used by the PreviewPane and inline-markdown rendering to display
        images (.png/.jpg/...) and other binary previews. Text files also
        flow through here when the caller wants the un-decoded bytes.
        """
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
