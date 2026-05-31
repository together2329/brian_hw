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
import json
import re
from pathlib import Path
from typing import Callable

from fastapi import FastAPI, Request
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

    def _rc_name(name: str) -> str | None:
        stem = Path(str(name or "signal.rc").strip()).name
        if not stem:
            stem = "signal.rc"
        if not stem.endswith(".rc"):
            stem += ".rc"
        if not re.fullmatch(r"[A-Za-z0-9_.-]+\.rc", stem):
            return None
        if stem.startswith("."):
            return None
        return stem

    def _rc_dir(ip: str) -> Path | None:
        base = safe_path(ip)
        if base is None or not base.exists() or not base.is_dir():
            return None
        return base / "sim"

    @app.get("/api/vcd/list")
    async def api_vcd_list(ip: str = "", scope: str = ""):
        """Discover VCD files under PROJECT_ROOT.

        - `ip`    — restrict to VCD files under the active `<ip>/` tree.
        - `scope` — arbitrary sub-directory under PROJECT_ROOT to search.
        - neither — recursive scan up to depth 4 (cheap on typical projects).
        Returns: `{files: [{path, size, mtime}]}` sorted by mtime desc.
        """
        def _work():
            if ip:
                base = safe_path(ip)
            elif scope:
                base = safe_path(scope)
            else:
                base = project_root()
            if base is None or not base.is_dir():
                return 404, {"files": [], "error": "scope not found"}

            results = []
            root = project_root().resolve()
            if ip:
                # Active-IP scoped recursive scan. Keep this broader than
                # `<ip>/sim/*.vcd` so cocotb build dirs and `sim/waves/`
                # still appear, but never leak another IP into the picker.
                for f in base.rglob("*.vcd"):
                    if not f.is_file():
                        continue
                    rel_path = f.resolve().relative_to(root)
                    if any(p in skip_dirs for p in rel_path.parts):
                        continue
                    st = f.stat()
                    rel = rel_path.as_posix()
                    results.append({"path": rel, "size": st.st_size, "mtime": st.st_mtime})
            elif scope:
                # Direct *.vcd in chosen dir.
                for f in base.glob("*.vcd"):
                    if f.is_file():
                        st = f.stat()
                        rel = f.resolve().relative_to(root).as_posix()
                        results.append({"path": rel, "size": st.st_size, "mtime": st.st_mtime})
            else:
                # Recursive scan (capped depth).
                for f in base.rglob("*.vcd"):
                    try:
                        rel = f.resolve().relative_to(root)
                    except ValueError:
                        continue
                    if any(p in skip_dirs for p in rel.parts):
                        continue
                    if len(rel.parts) > 5:
                        continue
                    st = f.stat()
                    results.append({"path": str(rel), "size": st.st_size, "mtime": st.st_mtime})
            results.sort(key=lambda x: x["mtime"], reverse=True)
            return 200, {"files": results, "project_root": str(project_root())}
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/vcd/rc/list")
    async def api_vcd_rc_list(ip: str):
        """List saved sim_debug waveform rc snapshots under <ip>/sim/*.rc."""
        def _work():
            rc_dir = _rc_dir(ip)
            if rc_dir is None:
                return 404, {"files": [], "error": "ip not found"}
            if not rc_dir.exists():
                return 200, {"files": []}
            root = project_root().resolve()
            files = []
            for f in rc_dir.glob("*.rc"):
                if not f.is_file():
                    continue
                st = f.stat()
                try:
                    rel = f.resolve().relative_to(root).as_posix()
                except ValueError:
                    rel = f.name
                files.append({"name": f.name, "path": rel, "size": st.st_size, "mtime": st.st_mtime})
            files.sort(key=lambda x: x["mtime"], reverse=True)
            return 200, {"files": files}
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/vcd/rc/load")
    async def api_vcd_rc_load(ip: str, name: str = "signal.rc"):
        """Load a saved sim_debug waveform rc snapshot."""
        rc_file = _rc_name(name)
        if rc_file is None:
            return JSONResponse({"error": "invalid rc name"}, status_code=400)

        def _work():
            rc_dir = _rc_dir(ip)
            if rc_dir is None:
                return 404, {"error": "ip not found"}
            target = rc_dir / rc_file
            if not target.is_file():
                return 404, {"error": "rc not found"}
            text = target.read_text(encoding="utf-8")
            try:
                payload = json.loads(text)
            except json.JSONDecodeError:
                payload = {"version": 0, "content": text}
            return 200, {"name": rc_file, "payload": payload}
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse(payload, status_code=status_code)

    @app.post("/api/vcd/rc/save")
    async def api_vcd_rc_save(request: Request, ip: str, name: str = "signal.rc"):
        """Save the current sim_debug waveform snapshot as <ip>/sim/<name>.rc."""
        rc_file = _rc_name(name)
        if rc_file is None:
            return JSONResponse({"error": "invalid rc name"}, status_code=400)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)

        def _work():
            rc_dir = _rc_dir(ip)
            if rc_dir is None:
                return 404, {"error": "ip not found"}
            rc_dir.mkdir(parents=True, exist_ok=True)
            target = rc_dir / rc_file
            envelope = {
                "version": 1,
                "kind": "sim_debug_wave_rc",
                "payload": body.get("payload", body) if isinstance(body, dict) else body,
            }
            text = json.dumps(envelope, indent=2, sort_keys=True)
            target.write_text(text + "\n", encoding="utf-8")
            st = target.stat()
            root = project_root().resolve()
            try:
                rel = target.resolve().relative_to(root).as_posix()
            except ValueError:
                rel = target.name
            return 200, {"name": rc_file, "path": rel, "size": st.st_size, "mtime": st.st_mtime}
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/vcd/raw")
    async def api_vcd_raw(path: str):
        """Return raw VCD content (UTF-8, replace errors). Capped at max_vcd_bytes."""
        def _work():
            target = safe_path(path)
            if target is None or not target.is_file():
                return 404, {"error": "not found"}
            if target.suffix.lower() != ".vcd":
                return 400, {"error": "not a .vcd file"}
            st = target.stat()
            truncated = st.st_size > max_vcd_bytes
            data = target.read_bytes()[:max_vcd_bytes]
            content = data.decode("utf-8", errors="replace")
            return 200, {
                "path": path,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "truncated": truncated,
                "content": content,
            }
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse(payload, status_code=status_code)
