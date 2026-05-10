"""ATLAS VCD API — extracted from atlas_ui.py.

Second step of the gradual atlas_ui.py decomposition: pull the
self-contained `/api/vcd/*` routes (list, raw) into their own module.
The host (atlas_ui.py) wires routes via `register_vcd_routes` and
injects callables/values for runtime state (PROJECT_ROOT, _safe,
SKIP_DIRS, MAX_VCD_BYTES) so this module never reaches into the host's
mutable globals.
"""
from __future__ import annotations

import asyncio
from pathlib import Path
from typing import Callable

from fastapi import FastAPI
from fastapi.responses import JSONResponse


def register_vcd_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    safe_path: Callable[[str], "Path | None"],
    skip_dirs: set,
    max_vcd_bytes: int,
) -> None:
    """Mount the VCD waveform API onto *app*.

    project_root and safe_path are passed as callables rather than
    values so the routes always read the live state — the --root flag
    in atlas_ui main() rebinds PROJECT_ROOT after this module is
    imported.  skip_dirs and max_vcd_bytes are plain values (they do
    not change after startup).
    """

    @app.get("/api/vcd/list")
    async def api_vcd_list(ip: str = "", scope: str = ""):
        """Discover VCD files under PROJECT_ROOT.

        - `ip`    — restrict to `<ip>/sim/*.vcd` (matches the IP-tree convention).
        - `scope` — arbitrary sub-directory under PROJECT_ROOT to search.
        - neither — recursive scan up to depth 4 (cheap on typical projects).
        Returns: `{files: [{path, size, mtime}]}` sorted by mtime desc.
        """
        if ip:
            base = safe_path(ip + "/sim")
        elif scope:
            base = safe_path(scope)
        else:
            base = project_root()
        if base is None or not base.is_dir():
            return JSONResponse({"files": [], "error": "scope not found"}, status_code=404)

        results = []
        try:
            if ip or scope:
                # Direct *.vcd in chosen dir.
                for f in base.glob("*.vcd"):
                    if f.is_file():
                        st = f.stat()
                        rel = f.relative_to(project_root()).as_posix()
                        results.append({"path": rel, "size": st.st_size, "mtime": st.st_mtime})
            else:
                # Recursive scan (capped depth).
                for f in base.rglob("*.vcd"):
                    try:
                        rel = f.relative_to(project_root())
                    except ValueError:
                        continue
                    if any(p in skip_dirs for p in rel.parts):
                        continue
                    if len(rel.parts) > 5:
                        continue
                    st = f.stat()
                    results.append({"path": str(rel), "size": st.st_size, "mtime": st.st_mtime})
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        results.sort(key=lambda x: x["mtime"], reverse=True)
        return JSONResponse({"files": results, "project_root": str(project_root())})

    @app.get("/api/vcd/raw")
    async def api_vcd_raw(path: str):
        """Return raw VCD content (UTF-8, replace errors). Capped at max_vcd_bytes."""
        target = safe_path(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        if target.suffix.lower() != ".vcd":
            return JSONResponse({"error": "not a .vcd file"}, status_code=400)
        st = target.stat()
        truncated = st.st_size > max_vcd_bytes
        try:
            data = target.read_bytes()[:max_vcd_bytes]
            content = data.decode("utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "truncated": truncated,
            "content": content,
        })
