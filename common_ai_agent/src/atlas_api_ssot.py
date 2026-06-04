"""ATLAS SSOT API — extracted from atlas_ui.py.

Phase 5 of the gradual atlas_ui.py decomposition: pull the
self-contained `/api/ssot*` routes (list/read ssot files, QA view,
QA sessions, QA answer) into their own module. The host (atlas_ui.py)
wires routes via `register_ssot_routes` and injects callables for
runtime values (PROJECT_ROOT, helpers) so this module never reaches
into the host's mutable globals.
"""
from __future__ import annotations

import asyncio
import os
import time
from pathlib import Path
from typing import Any, Callable

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from src.atlas_api_files import AtlasContext, IP_LOCAL_ROOTS


def register_ssot_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    safe_path: Callable[[str], Path | None],
    skip_dirs: set[str],
    max_read_bytes: int,
    valid_ip_name: Callable[[str], bool],
    active_ssot_ip: Callable[[], str],
    ssot_qa_view: Callable[..., dict[str, Any]],
    ssot_qa_sessions_view: Callable[[], dict[str, Any]],
    ssot_qa_path: Callable[..., Path],
    qa_slug: Callable[[str, str], str],
    upsert_ssot_qa_items: Callable[..., None],
    load_ssot_state: Callable[[str], dict[str, Any]],
    canonical_session_string: Callable[..., str],
    normalize_session_name: Callable[[str], str],
    append_session_message: Callable[[str, str, str], None],
    bridge: Any,
    fs_authz: Any = None,
) -> None:
    """Mount the SSOT API onto *app*.

    All mutable-state accessors are injected as callables so this module
    never reaches into atlas_ui's globals.
    """

    # ── B1 read/write gate (injected by create_app). ─────────────────────
    def _gate_path(request, rel, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.path(request, rel, permission)

    def _gate_ip(request, ip, permission="view"):
        if fs_authz is None:
            return None
        return fs_authz.ip(request, ip, permission)

    def _filter_files(request, files):
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

    def _context_base(context: AtlasContext | None) -> Path:
        if context is not None and not context.legacy:
            return context.workspace_root
        return project_root()

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

    def _safe_in_base(base: Path, rel_path: str) -> Path | None:
        rel = _clean_rel_path(rel_path)
        try:
            candidate = (base / rel).resolve()
            candidate.relative_to(base.resolve())
            return candidate
        except (OSError, ValueError):
            return None

    def _target_for_session(path: str, session_id: str) -> tuple[Path | None, Path, AtlasContext | None, str]:
        context = _context_for_session(session_id)
        base = _context_base(context)
        if base == project_root():
            target = safe_path(path)
            rel = _clean_rel_path(path)
            if target is not None:
                try:
                    rel = target.resolve().relative_to(project_root().resolve()).as_posix()
                except (OSError, ValueError):
                    pass
            return target, project_root(), context, rel
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
        return _gate_path(request, rel_path, permission)

    @app.get("/api/ssot")
    async def api_ssot(request: Request, file: str = "", session_id: str = "", session: str = ""):
        context = _context_for_session(session_id or session)
        root = _context_base(context)
        if file:
            target, root, context, rel_file = _target_for_session(file, session_id or session)
            denied = _gate_for_context_path(request, rel_file or file, context)
            if denied is not None:
                return denied
            if target is None or not target.is_file():
                return JSONResponse({"error": "not found"}, status_code=404)
            try:
                def _read_ssot_preview():
                    stat = target.stat()
                    data = target.read_bytes()[:max_read_bytes]
                    return stat, data.decode("utf-8", errors="replace")
                stat, content = await asyncio.to_thread(_read_ssot_preview)
            except OSError as e:
                return JSONResponse({"error": str(e)}, status_code=500)
            return JSONResponse({
                "path": rel_file or file,
                "size": stat.st_size,
                "mtime": stat.st_mtime,
                "truncated": stat.st_size > max_read_bytes,
                "content": content,
            })
        # No specific file → list every *.ssot.yaml in the project.
        # Path.rglob() is NOT resilient to concurrent directory creation/removal:
        # while many users scaffold IPs under the project root at once, a sibling
        # directory can vanish mid-walk and rglob raises FileNotFoundError → 500.
        # os.walk(onerror=...) skips a transient/again directory instead, and pruning
        # skip/hidden dirs in-place avoids descending into them at all.
        results = []
        denied = _deny_context_request(request, context)
        if denied is not None:
            return denied
        for dirpath, dirnames, filenames in os.walk(root, onerror=lambda _e: None):
            dirnames[:] = [d for d in dirnames
                           if d not in skip_dirs and not d.startswith(".")]
            for fn in filenames:
                if not fn.endswith(".ssot.yaml"):
                    continue
                p = Path(dirpath) / fn
                try:
                    rel = p.relative_to(root).as_posix()
                    stat = p.stat()
                    results.append({"path": rel, "size": stat.st_size,
                                     "mtime": stat.st_mtime})
                except OSError:
                    continue
        return JSONResponse({"files": _filter_files(request, results)})

    @app.get("/api/ssot/qa")
    async def api_ssot_qa(request: Request, ip: str = "", session: str = ""):
        session_name = normalize_session_name(session or "")
        target = str(ip or "").strip()
        if not target and session_name:
            parts = [p for p in session_name.split("/") if p]
            if len(parts) >= 2 and parts[-1] == "ssot-gen":
                target = parts[-2]
        if target and not valid_ip_name(target):
            return JSONResponse({"error": f"invalid ip {target!r}"}, status_code=400)
        if not target:
            target = active_ssot_ip()
        if not target or not valid_ip_name(target):
            return JSONResponse({
                "ip": "",
                "workflow": "ssot-gen",
                "toc": [],
                "sections": [],
                "summary": {"total": 0, "approved": 0, "pending": 0},
                "items": [],
            })
        denied = _gate_ip(request, target)
        if denied is not None:
            return denied
        return JSONResponse(ssot_qa_view(target, session=session_name))

    @app.get("/api/ssot/qa/sessions")
    async def api_ssot_qa_sessions():
        return JSONResponse(ssot_qa_sessions_view())

    @app.post("/api/ssot/qa/answer")
    async def api_ssot_qa_answer(req: Request):
        """Persist user-supplied answers for pending QA items to qa.json.

        Body shape (each item carries its OWN flow_id so this endpoint can
        update the pre-existing pending entry in-place, not create a new one):
          {
            "ip": "<ip_name>",
            "session": "<owner>/<ip>/<workflow>",   # optional
            "items": [
              {
                "flow_id": "<flow_id>",         # required — match existing entry
                "decision_key": "<key>",         # required
                "answer": "<text>",
                "selected": ["opt_label", ...],
                "section_id": "...", "section_title": "...",
                "decision_label": "...",
                "question": "...", "subtitle": "..."
              },
              ...
            ],
            "submitted_text": "<full prompt that was sent>"
          }
        """
        try:
            body = await req.json()
        except Exception:
            return JSONResponse({"error": "invalid json body"}, status_code=400)
        ip = str((body or {}).get("ip") or "").strip()
        if not ip or not valid_ip_name(ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        denied = _gate_ip(req, ip, "write")
        if denied is not None:
            return denied
        session_name = normalize_session_name(str((body or {}).get("session") or ""))
        if not session_name:
            session_name = canonical_session_string(ip)
        items_in = (body or {}).get("items") or []
        if not isinstance(items_in, list) or not items_in:
            return JSONResponse({"error": "items[] required"}, status_code=400)

        # Group by flow_id so existing pending entries get updated in-place.
        grouped: dict[str, dict[str, Any]] = {}
        fallback_flow_id = "atlas_qa_" + str(int(time.time() * 1000))
        for entry in items_in:
            if not isinstance(entry, dict):
                continue
            key_src = entry.get("decision_key") or entry.get("id") or entry.get("question")
            if not key_src:
                continue
            flow_id = str(entry.get("flow_id") or "").strip() or fallback_flow_id
            key = qa_slug(str(key_src), f"qa_{len(grouped.get(flow_id, {}).get('pairs', [])) + 1}")
            label = str(entry.get("decision_label") or entry.get("question") or key)[:240]
            qmeta = {
                "decision_key": key,
                "decision_label": label,
                "section_id": entry.get("section_id") or "",
                "section_title": entry.get("section_title") or entry.get("section") or "",
                "question": entry.get("question") or label,
                "subtitle": entry.get("subtitle") or "",
            }
            answer_text = str(entry.get("answer") or "").strip()
            selected_raw = entry.get("selected")
            selected: list[Any] = selected_raw if isinstance(selected_raw, list) else []
            if not answer_text and selected:
                answer_text = "; ".join(str(s) for s in selected if s)
            bucket = grouped.setdefault(flow_id, {"pairs": [], "answers": {}})
            bucket["pairs"].append((key, label or key, qmeta))
            bucket["answers"][key] = {
                "answer": answer_text,
                "selected": [str(s) for s in selected if s],
                "submitted_at": time.time(),
                "source": "atlas-ui",
            }

        if not grouped:
            return JSONResponse({"error": "no valid items to record"}, status_code=400)

        for flow_id, bucket in grouped.items():
            upsert_ssot_qa_items(
                ip,
                flow_id=flow_id,
                kind=str((load_ssot_state(ip) or {}).get("kind") or "general IP"),
                q_pairs=bucket["pairs"],
                status="approved",   # user explicitly answered → flip pending → approved
                answers=bucket["answers"],
                session=session_name,
                source="atlas-ui-pending",
            )
            # Notify all WS clients so the QA Preview live-flips pending→approved
            # without requiring a manual "refresh" click. Mirrors the emit calls
            # that _ask_user_cb / _record_ssot_qa_cb make for their own upserts.
            try:
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=session_name,
                )
            except Exception:
                pass

        # Mirror the submitted prompt into the conversation log for traceability.
        submitted_text = str((body or {}).get("submitted_text") or "").strip()
        if submitted_text:
            append_session_message(session_name, "user", submitted_text)

        return JSONResponse({
            "ok": True,
            "ip": ip,
            "session": session_name,
            "flow_ids": list(grouped.keys()),
            "count": sum(len(b["pairs"]) for b in grouped.values()),
            "qa_path": str(ssot_qa_path(ip, session_name).relative_to(project_root())),
        })
