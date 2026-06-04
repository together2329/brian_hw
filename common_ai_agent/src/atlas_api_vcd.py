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
import os
import re
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from src.atlas_api_files import AtlasContext
from src.atlas_vcd_conversion import list_waveform_vcd_entries, read_vcd_target


def register_vcd_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    safe_path: Callable[[str], "Path | None"],
    skip_dirs: set[str],
    max_vcd_bytes: int,
    fs_authz: Any = None,
) -> None:
    """Mount the VCD waveform API onto *app*.

    project_root and safe_path are passed as callables rather than
    values so the routes always read the live state — the --root flag
    in atlas_ui main() rebinds PROJECT_ROOT after this module is
    imported.  skip_dirs and max_vcd_bytes are plain values (they do
    not change after startup).
    """

    # ── B1 read/write gate (injected by create_app). ─────────────────────
    def _gate_ip(request, ip, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.ip(request, ip, permission)

    def _gate_path(request, rel, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.path(request, rel, permission)

    def _filter_files(request, files):
        """Drop entries the caller may not access (the no-arg whole-root scan)."""
        if fs_authz is None:
            return files
        allowed = fs_authz.accessible_ips(request)
        if allowed is None:
            return files
        shared = getattr(fs_authz, "shared_roots", frozenset())
        kept = []
        for f in files or []:
            seg0 = str((f or {}).get("path") or "").split("/", 1)[0]
            if seg0 in shared or seg0 in allowed:
                kept.append(f)
        return kept

    def _context_for_session(session_id: str) -> AtlasContext | None:
        raw = str(session_id or "").strip()
        if not raw:
            return None
        try:
            return AtlasContext.from_session_key(
                raw,
                atlas_root=os.environ.get("ATLAS_ROOT") or str(project_root()),
            )
        except Exception:
            return None

    def _context_root(context: AtlasContext | None) -> Path:
        if context is not None and not context.legacy:
            return context.workspace_root
        return project_root()

    def _clean_rel_path(rel_path: str) -> str:
        return str(rel_path or "").replace("\\", "/").lstrip("/")

    def _safe_in_root(root: Path, rel_path: str) -> Path | None:
        rel = _clean_rel_path(rel_path)
        try:
            target = (root / rel).resolve()
            target.relative_to(root.resolve())
            return target
        except (OSError, ValueError):
            return None

    def _target_for_session(path: str, session_id: str) -> tuple[Path | None, Path, AtlasContext | None, str]:
        context = _context_for_session(session_id)
        root = _context_root(context)
        if root == project_root():
            target = safe_path(path)
        else:
            target = _safe_in_root(root, path)
        rel = _clean_rel_path(path)
        if target is not None:
            try:
                rel = target.resolve().relative_to(root.resolve()).as_posix()
            except (OSError, ValueError):
                pass
        return target, root, context, rel

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

    def _gate_context_ip(request: Request, ip: str, context: AtlasContext | None, permission: str = "view"):
        denied = _deny_context_request(request, context)
        if denied is not None:
            return denied
        if context is not None and not context.legacy:
            if ip and ip != context.ip_name:
                return JSONResponse({"error": "session ip mismatch"}, status_code=400)
            return None
        return _gate_ip(request, ip, permission)

    def _gate_context_path(
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
        return _gate_path(request, rel_path, permission)

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

    def _rc_dir(ip: str, session_id: str = "") -> Path | None:
        context = _context_for_session(session_id)
        root = _context_root(context)
        base = _safe_in_root(root, ip) if context is not None and not context.legacy else safe_path(ip)
        if base is None or not base.exists() or not base.is_dir():
            return None
        return base / "sim"

    def _rel(root: Path, path: Path) -> str | None:
        try:
            return path.resolve().relative_to(root.resolve()).as_posix()
        except ValueError:
            return None

    @app.get("/api/vcd/list")
    async def api_vcd_list(request: Request, ip: str = "", scope: str = "", session_id: str = "", session: str = ""):
        """Discover VCD files under PROJECT_ROOT.

        - `ip`    — restrict to VCD files under the active `<ip>/` tree.
        - `scope` — arbitrary sub-directory under PROJECT_ROOT to search.
        - neither — recursive scan up to depth 4 (cheap on typical projects).
        Returns: `{files: [{path, size, mtime}]}` sorted by mtime desc.
        """
        session_name = session_id or session
        context = _context_for_session(session_name)
        if ip:
            denied = _gate_context_ip(request, ip, context)
            if denied is not None:
                return denied
        elif scope:
            denied = _gate_context_path(request, scope, context)
            if denied is not None:
                return denied
        def _work():
            root = _context_root(context).resolve()
            if ip:
                base = _safe_in_root(root, ip) if context is not None and not context.legacy else safe_path(ip)
            elif scope:
                base = _safe_in_root(root, scope) if context is not None and not context.legacy else safe_path(scope)
            else:
                base = root
            if base is None or not base.is_dir():
                return 404, {"files": [], "error": "scope not found"}

            if ip:
                results, waveform_errors = list_waveform_vcd_entries(
                    root=root,
                    base=base,
                    skip_dirs=skip_dirs,
                    recursive=True,
                    max_depth=None,
                    convert_fst=True,
                )
            elif scope:
                results, waveform_errors = list_waveform_vcd_entries(
                    root=root,
                    base=base,
                    skip_dirs=skip_dirs,
                    recursive=False,
                    max_depth=None,
                    convert_fst=True,
                )
            else:
                results, waveform_errors = list_waveform_vcd_entries(
                    root=root,
                    base=base,
                    skip_dirs=skip_dirs,
                    recursive=True,
                    max_depth=5,
                    convert_fst=False,
                )
            return 200, {"files": results, "waveform_errors": waveform_errors, "project_root": str(root)}
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        if not ip and not scope and isinstance(payload, dict) and payload.get("files"):
            payload["files"] = _filter_files(request, payload["files"])
        return JSONResponse(payload, status_code=status_code)

    @app.get("/api/vcd/rc/list")
    async def api_vcd_rc_list(request: Request, ip: str, session_id: str = "", session: str = ""):
        """List saved sim_debug waveform rc snapshots under <ip>/sim/*.rc."""
        session_name = session_id or session
        context = _context_for_session(session_name)
        denied = _gate_context_ip(request, ip, context)
        if denied is not None:
            return denied
        def _work():
            root = _context_root(context).resolve()
            rc_dir = _rc_dir(ip, session_name)
            if rc_dir is None:
                return 404, {"files": [], "error": "ip not found"}
            if not rc_dir.exists():
                return 200, {"files": []}
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
    async def api_vcd_rc_load(request: Request, ip: str, name: str = "signal.rc", session_id: str = "", session: str = ""):
        """Load a saved sim_debug waveform rc snapshot."""
        session_name = session_id or session
        context = _context_for_session(session_name)
        denied = _gate_context_ip(request, ip, context)
        if denied is not None:
            return denied
        rc_file = _rc_name(name)
        if rc_file is None:
            return JSONResponse({"error": "invalid rc name"}, status_code=400)

        def _work():
            rc_dir = _rc_dir(ip, session_name)
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
    async def api_vcd_rc_save(request: Request, ip: str, name: str = "signal.rc", session_id: str = "", session: str = ""):
        """Save the current sim_debug waveform snapshot as <ip>/sim/<name>.rc."""
        session_name = session_id or session
        context = _context_for_session(session_name)
        denied = _gate_context_ip(request, ip, context, "write")
        if denied is not None:
            return denied
        rc_file = _rc_name(name)
        if rc_file is None:
            return JSONResponse({"error": "invalid rc name"}, status_code=400)
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid JSON body"}, status_code=400)

        def _work():
            root = _context_root(context).resolve()
            rc_dir = _rc_dir(ip, session_name)
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
    async def api_vcd_raw(request: Request, path: str, session_id: str = "", session: str = ""):
        """Return raw VCD content (UTF-8, replace errors). Capped at max_vcd_bytes."""
        target, root, context, rel_path = _target_for_session(path, session_id or session)
        denied = _gate_context_path(request, rel_path or path, context)
        if denied is not None:
            return denied
        def _work():
            if target is None or not target.is_file():
                return 404, {"error": "not found"}
            conversion, vcd_target = read_vcd_target(root.resolve(), target)
            if vcd_target is None:
                status = 503 if conversion.status in {"converter_missing", "conversion_timeout"} else 400
                return status, {"error": conversion.status, "message": conversion.message}
            st = vcd_target.stat()
            truncated = st.st_size > max_vcd_bytes
            data = vcd_target.read_bytes()[:max_vcd_bytes]
            content = data.decode("utf-8", errors="replace")
            payload = {
                "path": _rel(root, vcd_target) or path,
                "size": st.st_size,
                "mtime": st.st_mtime,
                "truncated": truncated,
                "content": content,
            }
            if target.suffix.lower() == ".fst":
                payload["source"] = "converted_fst"
                payload["converted_from"] = _rel(root, target) or path
            else:
                payload["source"] = "native_vcd"
            return 200, payload
        try:
            status_code, payload = await asyncio.to_thread(_work)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse(payload, status_code=status_code)
