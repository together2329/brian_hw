"""ATLAS workspaces API — extracted from atlas_ui.py.

Phase 3 of the gradual atlas_ui.py decomposition: pull the
`/api/workspaces` (list workflow definitions) and
`/api/workspace/download.zip` (streaming zip handler) routes into
their own module.  The host (atlas_ui.py) wires routes via
`register_workspaces_routes` and injects callables for runtime values
so this module never reaches into the host's mutable globals.
"""
from __future__ import annotations

import io
import json
import os
import zipfile
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse, StreamingResponse


def register_workspaces_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    source_root: Path,
    safe_path: Callable[[str], Path | None],
) -> None:
    """Mount the workspaces API onto *app*.

    project_root  — callable returning the live PROJECT_ROOT (rebindable
                    via --root after import).
    source_root   — the common_ai_agent/ source directory (module-level
                    constant, does not change at runtime).
    safe_path     — the _safe() helper from atlas_ui; validates that a
                    relative path does not escape PROJECT_ROOT.
    """

    @app.get("/api/workspaces")
    async def api_workspaces():
        """List every workspace under workflow/ with a workspace.json.

        Reads from the SOURCE repo (not the user's cwd) since workspace
        definitions ship with common_ai_agent itself.
        """
        workflow_dir = source_root / "workflow"
        items = []
        if workflow_dir.is_dir():
            for d in sorted(workflow_dir.iterdir()):
                if not d.is_dir():
                    continue
                ws_json = d / "workspace.json"
                if not ws_json.exists():
                    continue
                try:
                    spec = json.loads(ws_json.read_text())
                except Exception:
                    spec = {}
                items.append({
                    "id": d.name,
                    "name": d.name,
                    "label": spec.get("name", d.name),
                    "description": spec.get("description", ""),
                })
        # Same fallback as /healthz — show the actual session name even
        # when ACTIVE_WORKSPACE is unset (boot without -w). Frontend
        # uses this to render the workflow strip's active highlight.
        active = (os.environ.get("ACTIVE_WORKSPACE")
                  or os.environ.get("ACTIVE_PROJECT")
                  or "default")
        return JSONResponse({"active": active, "items": items})

    @app.get("/api/workspace/download.zip")
    async def api_workspace_download(subpath: str = ""):
        """Stream a zip of the workspace (or an optional sub-directory).

        subpath: optional path relative to PROJECT_ROOT. Defaults to the
        whole workspace. Refuses anything that escapes PROJECT_ROOT.
        Skips heavy/cache/secret folders (same skip-set as /tree, plus .env).
        """
        skip_dirs = {
            ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", "node_modules", ".venv", "venv", "vendor",
            ".session", ".rag", ".claude", ".omc", ".benchmark",
            ".benchmarks", ".common_ai_agent", ".session_debug", "logs",
        }
        skip_files = {".env", ".env.local", ".env.production",
                      ".env.example", ".DS_Store"}

        try:
            base = project_root()
            if subpath:
                target = (project_root() / subpath).resolve()
                try:
                    target.relative_to(project_root())
                except ValueError:
                    return JSONResponse(
                        {"error": "subpath outside project root"},
                        status_code=400,
                    )
                if target.is_dir():
                    base = target

            buf = io.BytesIO()
            file_count = 0
            with zipfile.ZipFile(buf, mode="w",
                                 compression=zipfile.ZIP_DEFLATED) as z:
                for root_dir, dirs, files in os.walk(base):
                    dirs[:] = [
                        d for d in dirs
                        if d not in skip_dirs and not d.startswith(".")
                    ]
                    for f in files:
                        if f in skip_files or f.startswith("."):
                            continue
                        full = Path(root_dir) / f
                        try:
                            rel = full.relative_to(base)
                            z.write(full, arcname=str(rel))
                            file_count += 1
                        except (OSError, ValueError):
                            continue
            buf.seek(0)
            name = f"{base.name or 'workspace'}.zip"

            def _iter():
                while True:
                    chunk = buf.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk

            return StreamingResponse(
                _iter(),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{name}"',
                    "X-Workspace-File-Count": str(file_count),
                },
            )
        except Exception as exc:
            return JSONResponse(
                {"error": f"zip failed: {exc}"},
                status_code=500,
            )
