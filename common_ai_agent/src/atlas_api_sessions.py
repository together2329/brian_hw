"""ATLAS sessions API — extracted from atlas_ui.py (phase 4 of split).

Holds all /api/session* and /api/sessions* routes. The host
(atlas_ui.py) wires routes via ``register_sessions_routes`` and injects
callables for runtime values so this module never reaches into the
host's mutable globals.
"""
from __future__ import annotations

import json
import os
import re
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse


def register_sessions_routes(
    app: FastAPI,
    *,
    project_root: Callable[[], Path],
    normalize_session_name: Callable[[str], str],
    active_session_value: Callable[[], str],
    atlas_active_session_cv: Any,
    atlas_active_ip_cv: Any,
    bridge: Any,
    get_jobs_state: Callable[[], tuple[dict, Any]],
    atlas_db_factory: Callable[[], Any],
    setup_session: Optional[Callable[[str], Any]] = None,
    setup_workspace: Optional[Callable[[str], None]] = None,
) -> None:
    """Register all /api/session* and /api/sessions* routes onto *app*.

    Parameters
    ----------
    project_root:
        Callable returning the current PROJECT_ROOT Path (changes with --root).
    normalize_session_name:
        Callable that sanitises a raw session string.
    active_session_value:
        Callable returning the current active session canonical string.
    atlas_active_session_cv:
        The ``contextvars.ContextVar`` for the active session triple.
    atlas_active_ip_cv:
        The ``contextvars.ContextVar`` for the active IP.
    bridge:
        The live AtlasBridge instance.
    get_jobs_state:
        Callable returning (_jobs, _jobs_lock) from atlas_api_jobs.
    atlas_db_factory:
        Callable that creates and returns an AtlasDB context-manager instance.
    """

    def _multi_user_enabled() -> bool:
        raw = os.environ.get("ATLAS_MULTI_USER", "1").strip().lower()
        return raw not in ("0", "false", "no", "off")

    # ── /api/session/activate ──────────────────────────────────────
    @app.post("/api/session/activate")
    async def api_session_activate(req: Request):
        """Frontend → backend handshake to keep the canonical
        (session_id, ip, workflow) triple in sync.

        Body: {"session_id": str, "ip": str, "workflow": str}
        Each field is optional; missing/empty values default to "default".
        Updates ATLAS_ACTIVE_SESSION and ATLAS_ACTIVE_IP env vars so all
        path resolvers in this process pivot to the same triple.

        The frontend calls this on page load (so URL params survive a
        restart) and any time the user changes a top dropdown.
        """
        try:
            body = await req.json()
        except Exception:
            body = {}
        sid = str((body or {}).get("session_id") or "").strip() or "default"
        ip = str((body or {}).get("ip") or "").strip() or "default"
        wf = str((body or {}).get("workflow") or "").strip() or "default"
        raw_preserve = (body or {}).get("preserve_running")
        if raw_preserve is None:
            raw_preserve = (body or {}).get("preserveRunning")
        preserve_running = (
            bool(raw_preserve)
            if isinstance(raw_preserve, bool)
            else str(raw_preserve or "").strip().lower() in ("1", "true", "yes", "on")
        )
        # Sanitize — refuse exotic path chars to avoid traversal.
        for label, val in (("session_id", sid), ("ip", ip), ("workflow", wf)):
            if not re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", val):
                return JSONResponse(
                    {"error": f"invalid {label}: {val!r}"},
                    status_code=400,
                )
        owner = _request_username(req)
        multi_user_on = _multi_user_enabled()
        if multi_user_on and owner and sid != owner:
            return JSONResponse({"error": "session owner mismatch"}, status_code=403)
        sid = _session_owner_with_model(sid)
        canonical = f"{sid}/{ip}/{wf}"
        user_id = _request_user_id(req)
        try:
            with _atlas_db() as db:
                existing_session = db.get_session(canonical)
                if (
                    existing_session is not None
                    and existing_session.get("user_id") != user_id
                    and multi_user_on
                ):
                    return JSONResponse({"error": "session owner mismatch"}, status_code=403)
        except Exception:
            pass
        def _emit_to_canonical(msg_type: str, **payload: Any) -> None:
            bridge.emit(msg_type, session_id=canonical, **payload)

        # Halt the running agent + drain queued prompts BEFORE flipping
        # env vars whenever the active triple actually changes. Without
        # this, an in-flight react_loop keeps reading from the OLD IP's
        # paths even after env has pivoted, producing the "switched IP
        # but tools still hit GPIO_NEW_2" surprise. The frontend's own
        # POST /api/control/stop is fire-and-forget and races with the
        # /wf prompt sent on the same flip — anchoring the halt here
        # makes the transition deterministic regardless of order.
        #
        # Orchestrator + multi-worker mode is different: workflow changes are
        # deliberate focus switches between per-session workers. In that mode
        # the frontend sends preserve_running=true so an already-running worker
        # can continue while the user jumps to another worker and sends input.
        prev = active_session_value() or ""
        triple_changed = prev != canonical
        was_running = bool(getattr(bridge, "agent_running", False))
        halted = bool(triple_changed and was_running and not preserve_running)
        if halted:
            try:
                bridge.request_stop_for_session(prev or canonical)
                try:
                    bridge.get_session(prev or canonical).agent_running = False
                except Exception:
                    pass
                bridge.emit("agent_state", running=False, session_id=prev or canonical)
                if prev and prev != canonical:
                    bridge.emit("agent_state", running=False, session_id=canonical)
            except Exception:
                pass
        atlas_active_session_cv.set(canonical)
        atlas_active_ip_cv.set(ip)
        # Mirror to os.environ — main.py's chat_loop runs in its own
        # thread and can't see contextvars set inside the FastAPI
        # request task. Without this mirror the /wf prompt that fires
        # right after this handler reads a stale ATLAS_ACTIVE_SESSION
        # and pads the missing IP slot to "default", landing the
        # workspace in .session/default/default/<wf>/ instead of the
        # IP the user just picked.
        os.environ["ATLAS_ACTIVE_SESSION"] = canonical
        os.environ["ATLAS_ACTIVE_IP"] = ip
        os.environ["ATLAS_DEFAULT_SESSION_ID"] = sid
        os.environ["ATLAS_DEFAULT_WORKFLOW"] = wf
        if setup_session is not None:
            try:
                setup_session(canonical)
                os.environ["ATLAS_SESSION_APPLIED"] = canonical
            except Exception as exc:
                print(f"[Session] activate→setup_session({canonical!r}) failed: {exc}",
                      flush=True)
        # Synchronously update the workspace too. /api/session/activate was
        # only mirroring path-resolution env vars; the actual workflow
        # config (system prompt, skills, hooks, todo template) is loaded
        # by main.py's `_setup_workspace`, which previously only ran when
        # the WS-bound `/wf <name>` slash command was processed by the
        # chat_loop. That introduced a race where the dropdown flip
        # activated env but workflow stayed pinned to the previous
        # workflow until the chat_loop got around to it — and if the
        # loop was busy on an LLM call, it never did. Calling
        # _setup_workspace from here decouples the FE flip from chat_loop
        # availability so the user sees the new workspace immediately.
        prev_wf = os.environ.get("ACTIVE_WORKSPACE", "")
        if setup_workspace is not None and wf and wf != prev_wf:
            # Emit via 'token'+'flush' — workspace.jsx subscribes to that
            # streaming channel, not to a bare 'agent' type.
            try:
                _emit_to_canonical(
                    "token",
                    text=f"🔄 Switching workflow '{prev_wf}' → '{wf}' (ip={ip})…\n",
                )
                _emit_to_canonical("flush")
                _emit_to_canonical("workspace_changing", workspace=wf, prev=prev_wf, ip=ip)
            except Exception:
                pass
            try:
                setup_workspace(wf)
                os.environ["ACTIVE_WORKSPACE"] = wf
                print(
                    f"[Workflow] {wf!r} loaded via /api/session/activate "
                    f"(prev={prev_wf!r}, ip={ip!r}, owner={sid!r})",
                    flush=True,
                )
                try:
                    _emit_to_canonical(
                        "workspace_changed",
                        workspace=wf,
                        prev=prev_wf,
                        ip=ip,
                        session=canonical,
                        source="api/session/activate",
                    )
                    _emit_to_canonical(
                        "token",
                        text=f"✅ Workflow switched to '{wf}' (was '{prev_wf}') · ip={ip}\n",
                    )
                    _emit_to_canonical("flush")
                except Exception:
                    pass
            except Exception as exc:
                print(f"[Workflow] activate→setup_workspace({wf!r}) failed: {exc}",
                      flush=True)
        if triple_changed:
            try:
                _emit_to_canonical("commands_changed")
            except Exception:
                pass
        _root = project_root()
        # Workflow transition marker commit on the per-IP repo. Closes
        # out the previous stage's work as a single labeled checkpoint
        # so the IP history reads like a workflow timeline. Skipped when
        # prev_wf is empty / default (no real work to seal).
        if wf and prev_wf and wf != prev_wf and prev_wf != "default":
            _ip_dir = _root / ip
            if (_ip_dir / ".git").is_dir():
                try:
                    import subprocess as _sp_wf
                    _sp_wf.run(["git", "add", "--", "."],
                               cwd=str(_ip_dir), capture_output=True, timeout=10)
                    _sp_wf.run(["git", "commit", "--allow-empty",
                                "-m", f"workflow: {prev_wf} → {wf}"],
                               cwd=str(_ip_dir), capture_output=True, timeout=10)
                except Exception:
                    pass
        _session_dir = _root / ".session" / sid / ip / wf
        try:
            _session_dir.mkdir(parents=True, exist_ok=True)
            _conv = _session_dir / "conversation.json"
            if not _conv.exists():
                _conv.write_text("[]", encoding="utf-8")
        except Exception:
            pass
        try:
            summary = {
                "kind": "atlas_control_plane",
                "namespace": canonical,
                "owner": sid,
                "ip": ip,
                "workflow": wf,
            }
            with _atlas_db() as db:
                db.import_session(
                    canonical,
                    user_id,
                    project_id=ip,
                    directory=str(_session_dir),
                    title=f"{ip} / {wf}",
                    status="active",
                    summary=summary,
                )
                db.update_session(
                    canonical,
                    user_id=user_id,
                    project_id=ip,
                    directory=str(_session_dir),
                    title=f"{ip} / {wf}",
                    status="active",
                    summary=summary,
                )
        except Exception as exc:
            print(f"[Session] activate→db session upsert({canonical!r}) failed: {exc}",
                  flush=True)
        return JSONResponse({
            "ok": True,
            "active_session": canonical,
            "session_id": sid,
            "ip": ip,
            "workflow": wf,
            "halted": halted,
            "preserve_running": preserve_running,
        })

    # ── /api/session/history ───────────────────────────────────────
    def _db_conversation_messages(session_id: str) -> Optional[list[dict[str, Any]]]:
        """Return DB-backed conversation messages when *session_id* is a DB session."""
        try:
            with _atlas_db() as db:
                if db.get_session(session_id) is None:
                    return None
                messages: list[dict[str, Any]] = []
                for msg in db.get_messages(session_id):
                    if msg.get("role") == "system":
                        continue
                    parts = db.get_parts(msg["id"])
                    text_chunks = [
                        str(part.get("text") or "")
                        for part in parts
                        if part.get("type") == "text" and part.get("text")
                    ]
                    text = "\n".join(chunk for chunk in text_chunks if chunk)
                    item = {
                        "id": msg.get("id"),
                        "role": msg.get("role"),
                        "agent": msg.get("agent") or "",
                        "model_id": msg.get("model_id") or "",
                        "created_at": msg.get("created_at"),
                        "cost": msg.get("cost") or 0,
                        "tokens_input": msg.get("tokens_input") or 0,
                        "tokens_output": msg.get("tokens_output") or 0,
                        "tokens_reasoning": msg.get("tokens_reasoning") or 0,
                        "parts": parts,
                    }
                    if text:
                        item["text"] = text
                        item["content"] = text
                    messages.append(item)
                return messages
        except Exception:
            return None

    @app.get("/api/session/history")
    async def api_session_history(session: str, limit: int = 200):
        """Read a specific .session/<session>/conversation.json.

        Architect uses this to reload per-IP/per-workflow agent history,
        e.g. `.session/spi_master/rtl-gen/conversation.json`.
        """
        PROJECT_ROOT = project_root()
        session_raw = session or ""
        session = normalize_session_name(session_raw)
        if not session:
            status = 400
            error = "missing session" if not str(session_raw).strip() else f"invalid session {session_raw!r}"
            return JSONResponse({"error": error}, status_code=status)
        root = (PROJECT_ROOT / ".session").resolve()
        sdir = (root / session).resolve()
        try:
            sdir.relative_to(root)
        except Exception:
            return JSONResponse({"error": "session path escapes .session"}, status_code=400)
        db_msgs = _db_conversation_messages(session)
        if db_msgs is not None:
            if limit == 0:
                db_msgs = []
            elif limit > 0 and len(db_msgs) > limit:
                db_msgs = db_msgs[-limit:]
            return JSONResponse({
                "messages": db_msgs,
                "session": session,
                "path": "",
                "exists": True,
                "source": "db",
                "truncated_to": limit,
            })
        hpath = sdir / "conversation.json"
        if not hpath.is_file():
            return JSONResponse({"messages": [], "session": session,
                                 "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                 "exists": False, "source": "file"})
        try:
            msgs = json.loads(hpath.read_text(encoding="utf-8"))
            if not isinstance(msgs, list):
                msgs = []
        except Exception as e:
            return JSONResponse({"messages": [], "session": session,
                                 "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                 "error": f"parse: {e}"}, status_code=500)
        msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
        # `limit == 0` must return an empty list. The previous form
        # `msgs[-limit:]` becomes `msgs[-0:]` == `msgs[0:]` == full list
        # because Python collapses -0 to 0, so limit=0 paradoxically
        # returned everything. Guard explicitly. limit < 0 is also
        # treated as "no clamp" so callers can opt out with -1.
        if limit == 0:
            msgs = []
        elif limit > 0 and len(msgs) > limit:
            msgs = msgs[-limit:]
        return JSONResponse({"messages": msgs, "session": session,
                             "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                             "exists": True, "source": "file", "truncated_to": limit})

    # ── /api/session/state ─────────────────────────────────────────
    @app.get("/api/session/state")
    async def api_session_state(session: str, limit: int = 200, mode: str = "conversation"):
        """Return all UI state owned by a specific session namespace.

        This is the session-scoped hydrate endpoint for IP/sub-top/SoC
        workflow panes.  The frontend can switch screens or selected
        modules without losing chat/todo state because the authoritative
        data lives under `.session/<session>/`.

        `mode` controls which file the conversation messages come from:
          • conversation (default) — recent rolling window from
            conversation.json (already capped server-side at `limit`).
          • full        — every message ever written to
            full_conversation.json (no limit cap).
          • recent      — last `limit` messages from
            full_conversation.json (deeper history than conversation.json
            but trimmed to a manageable size).
        """
        PROJECT_ROOT = project_root()
        session_raw = session or ""
        session = normalize_session_name(session_raw)
        if not session:
            status = 400
            error = "missing session" if not str(session_raw).strip() else f"invalid session {session_raw!r}"
            return JSONResponse({"error": error}, status_code=status)
        root = (PROJECT_ROOT / ".session").resolve()
        sdir = (root / session).resolve()
        try:
            sdir.relative_to(root)
        except Exception:
            return JSONResponse({"error": "session path escapes .session"}, status_code=400)

        def _read_json(path: Path, fallback: Any) -> Any:
            if not path.is_file():
                return fallback
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data
            except Exception:
                return fallback

        mode_norm = (mode or "conversation").strip().lower()
        if mode_norm not in ("conversation", "full", "recent"):
            mode_norm = "conversation"
        if mode_norm == "conversation":
            conv_path = sdir / "conversation.json"
        else:
            conv_path = sdir / "full_conversation.json"
            # Fall back to conversation.json when full_conversation.json is missing
            if not conv_path.is_file():
                conv_path = sdir / "conversation.json"

        db_messages = _db_conversation_messages(session)
        conversation_source = "db" if db_messages is not None else "file"
        if db_messages is not None:
            messages = db_messages
        else:
            messages = _read_json(conv_path, [])
            if not isinstance(messages, list):
                messages = []
            messages = [m for m in messages if isinstance(m, dict) and m.get("role") != "system"]
        # `full` returns everything; `conversation` and `recent` cap at limit.
        # Same `-0 == 0` guard as /api/session/history above.
        if mode_norm != "full":
            if limit == 0:
                messages = []
            elif limit > 0 and len(messages) > limit:
                messages = messages[-limit:]

        todo_state = _read_json(sdir / "todo.json", {"todos": []})
        if isinstance(todo_state, list):
            todo_state = {"todos": todo_state}
        if not isinstance(todo_state, dict):
            todo_state = {"todos": []}
        todos = todo_state.get("todos")
        if not isinstance(todos, list):
            todo_state["todos"] = []
        # Do not fall back to PROJECT_ROOT/current_todos.json here. This
        # endpoint hydrates a specific .session/<session>/ pane; returning
        # process-global todos for an empty session makes fast workflow
        # switches look like todos were copied, lost, or saved under the
        # wrong IP. /api/session/activate now pins config.TODO_FILE before
        # slash commands run, so the authoritative source is the session file.

        cost_state = _read_json(sdir / "cost.json", {})
        if not isinstance(cost_state, dict):
            cost_state = {}

        _jobs_state, _jobs_state_lock = get_jobs_state()
        with _jobs_state_lock:
            jobs = [
                {k: v for k, v in j.items() if not k.startswith("_")}
                for j in _jobs_state.values()
                if str(j.get("session") or "").strip("/") == session
            ]
        jobs.sort(key=lambda j: j.get("started_at") or 0, reverse=True)

        return JSONResponse({
            "session": session,
            "session_dir": sdir.relative_to(PROJECT_ROOT).as_posix(),
            "exists": sdir.is_dir(),
            "conversation": {
                "messages": messages,
                "path": conv_path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": bool(db_messages is not None or conv_path.is_file()),
                "source": conversation_source,
                "mode": mode_norm,
                "truncated_to": (None if mode_norm == "full" else limit),
            },
            "todos": todo_state,
            "cost": cost_state,
            "jobs": jobs,
        })

    # ── /api/session/list ──────────────────────────────────────────
    @app.get("/api/session/list")
    async def api_session_list(request: Request):
        """List reloadable session namespaces under .session/."""
        PROJECT_ROOT = project_root()
        root = PROJECT_ROOT / ".session"
        out = []
        owner = _request_username(request)
        multi_user_on = _multi_user_enabled()
        if root.is_dir():
            for p in sorted(root.rglob("conversation.json")):
                try:
                    rel = p.parent.relative_to(root)
                except Exception:
                    continue
                parts = rel.parts
                if multi_user_on and owner and (not parts or parts[0] != owner):
                    continue
                session = str(rel)
                if session == ".":
                    continue
                out.append({
                    "session": session,
                    "path": p.relative_to(PROJECT_ROOT).as_posix(),
                    "mtime": p.stat().st_mtime,
                    "size": p.stat().st_size,
                })
        return JSONResponse({"sessions": out, "count": len(out)})

    # ── Atlas SQLite session CRUD (/api/sessions*) ─────────────────

    def _atlas_db():
        db = atlas_db_factory()
        try:
            Path(str(db.db_path)).expanduser().parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return db

    def _public_session(session: dict, include_summary: bool = False) -> dict:
        fields = ["id", "user_id", "title", "project_id", "status", "created_at", "updated_at"]
        if include_summary:
            fields.append("summary")
        return {key: session.get(key) for key in fields}

    def _request_user_id(request: Request) -> str:
        user = request.scope.get("user") or {}
        return str(user.get("id") or "default").strip() or "default"

    def _request_username(request: Request) -> str:
        user = request.scope.get("user") or {}
        return normalize_session_name(str(user.get("username") or ""))

    def _session_not_found() -> JSONResponse:
        return JSONResponse({"error": "session not found"}, status_code=404)

    def _owns_session(session: Optional[dict], user_id: str) -> bool:
        return session is not None and session.get("user_id") == user_id

    @app.get("/api/sessions")
    async def api_sessions(request: Request):
        user_id = _request_user_id(request)
        try:
            with _atlas_db() as db:
                listed = db.list_sessions(user_id)
                sessions = []
                for item in listed:
                    session_id = item.get("id") if isinstance(item, dict) else None
                    session = db.get_session(session_id) if session_id else None
                    if session is not None:
                        sessions.append(_public_session(session))
                return JSONResponse({"sessions": sessions})
        except Exception as e:
            print(f"api_sessions error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/sessions")
    async def api_create_session(request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid json body"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        user_id = _request_user_id(request)
        title = str(body.get("title") or "").strip()
        project_id = str(body.get("project_id") or "").strip()
        if not title:
            return JSONResponse({"error": "title required"}, status_code=400)
        try:
            with _atlas_db() as db:
                created = db.create_session(user_id, title, project_id)
                session_id = created.get("id") if isinstance(created, dict) else created
                return JSONResponse({"session_id": session_id, "status": "created"})
        except Exception as e:
            print(f"api_create_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/sessions/{session_id}")
    async def api_get_session(session_id: str, request: Request):
        user_id = _request_user_id(request)
        try:
            with _atlas_db() as db:
                session = db.get_session(session_id)
                if not _owns_session(session, user_id):
                    return _session_not_found()
                return JSONResponse(_public_session(session, include_summary=True))
        except Exception as e:
            print(f"api_get_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.patch("/api/sessions/{session_id}")
    async def api_update_session(session_id: str, request: Request):
        try:
            body = await request.json()
        except Exception:
            return JSONResponse({"error": "invalid json body"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        allowed = {"title", "project_id", "status", "summary"}
        fields = {key: body[key] for key in allowed if key in body}
        user_id = _request_user_id(request)
        try:
            with _atlas_db() as db:
                session = db.get_session(session_id)
                if not _owns_session(session, user_id):
                    return _session_not_found()
                if fields:
                    db.update_session(session_id, **fields)
                updated = db.get_session(session_id)
                if not _owns_session(updated, user_id):
                    return _session_not_found()
                return JSONResponse(_public_session(updated, include_summary=True))
        except Exception as e:
            print(f"api_update_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.delete("/api/sessions/{session_id}")
    async def api_delete_session(session_id: str, request: Request):
        user_id = _request_user_id(request)
        try:
            with _atlas_db() as db:
                session = db.get_session(session_id)
                if not _owns_session(session, user_id):
                    return _session_not_found()
                db.delete_session(session_id)
                return JSONResponse({"deleted": True})
        except Exception as e:
            print(f"api_delete_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/sessions/{session_id}/activate")
    async def api_activate_session(session_id: str, request: Request):
        # Activate the session: verify the caller owns it, then make the
        # backend bridge actually point at it. The previous version was a
        # no-op stub that returned {"activated": True} without binding
        # anything — UI session-switcher believed the swap took effect
        # while subsequent prompts still routed to the stale session.
        try:
            user_id = _request_user_id(request)
            with _atlas_db() as db:
                session = db.get_session(session_id)
                if not _owns_session(session, user_id):
                    return JSONResponse(
                        {"error": "session not found or not owned by user"},
                        status_code=404,
                    )
            # Bind on the bridge so emit/inbox/outbox routing follows.
            bridge.activate_session(session_id)
            return JSONResponse({"activated": True, "session_id": session_id})
        except Exception as e:
            print(f"api_activate_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)
    def _session_owner_with_model(owner: str) -> str:
        base = str(owner or "default").strip() or "default"
        enabled = os.environ.get("ATLAS_SESSION_PER_MODEL", "0").strip().lower() in ("1", "true", "yes", "on")
        if not enabled:
            return base
        raw_model = (
            os.environ.get("LLM_ACTIVE_MODEL_NAME")
            or os.environ.get("MODEL_NAME")
            or os.environ.get("LLM_MODEL_NAME")
            or ""
        ).strip()
        if not raw_model:
            return base
        model_slug = re.sub(r"[^A-Za-z0-9_-]+", "_", raw_model).strip("_")
        if not model_slug:
            return base
        if base.endswith(f"__{model_slug}"):
            return base
        return f"{base}__{model_slug}"
