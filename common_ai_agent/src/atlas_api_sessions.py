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
import threading
from pathlib import Path
from typing import Any, Callable, Optional

from fastapi import FastAPI
from fastapi.requests import Request
from fastapi.responses import JSONResponse

from core.atlas_context import AtlasContext
from core.atlas_exec_policy import EXEC_MODE_SINGLE, current_exec_mode
try:
    from atlas_session_delete import force_delete_requested, session_delete_response
except ModuleNotFoundError:  # imported package-style (src.atlas_api_sessions): src/ not on sys.path as bare
    from src.atlas_session_delete import force_delete_requested, session_delete_response
from src.atlas_workflow_switch import (
    WorkflowCheckpointRequest,
    schedule_workflow_checkpoint,
)


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
    admin_check: Optional[Callable[[Request], bool]] = None,
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

    def _env_flag(name: str, default: bool = False) -> bool:
        raw = os.environ.get(name)
        if raw is None or not str(raw).strip():
            return default
        return str(raw).strip().lower() in ("1", "true", "yes", "on")

    def _session_worker_keepalive_enabled() -> bool:
        if os.environ.get("ATLAS_SESSION_WORKER_KEEPALIVE") is not None:
            return _env_flag("ATLAS_SESSION_WORKER_KEEPALIVE", False)
        return current_exec_mode(os.environ) == EXEC_MODE_SINGLE

    def _session_worker_alive(session_id: str, *, process_mode: bool) -> bool:
        if not session_id:
            return False
        try:
            if process_mode:
                manager = getattr(bridge, "_process_manager", None)
                return bool(manager is not None and manager.is_alive(session_id))
            return bool(getattr(bridge.get_session(session_id), "agent_alive", False))
        except Exception:
            return False

    def _session_worker_pid(session_id: str) -> int:
        try:
            manager = getattr(bridge, "_process_manager", None)
            if manager is None:
                return 0
            get_pid = getattr(manager, "get_pid", None)
            if callable(get_pid):
                return int(get_pid(session_id) or 0)
        except Exception:
            pass
        return 0

    def _strict_mode() -> bool:
        try:
            getter = getattr(bridge, "session_worker_policy", None)
            if callable(getter):
                return bool(getattr(getter(), "is_strict", False))
        except Exception:
            pass
        return False

    def _cap_enabled() -> bool:
        # A global admission cap can be active even in session-scoped mode when
        # ATLAS_SESSION_WORKER_MAX_ACTIVE is set explicitly; warmup must then also
        # surface capacity_wait synchronously instead of a background "scheduled".
        try:
            getter = getattr(bridge, "session_worker_policy", None)
            if callable(getter):
                return bool(getattr(getter(), "cap_enabled", False))
        except Exception:
            pass
        return False

    def _schedule_session_worker_warmup(session_id: str, *, process_mode: bool) -> dict[str, Any]:
        mode = "process" if process_mode else "thread"
        if _session_worker_alive(session_id, process_mode=process_mode):
            payload: dict[str, Any] = {
                "enabled": True,
                "mode": mode,
                "session_id": session_id,
                "status": "ready",
                "alive": True,
            }
            if process_mode:
                payload["pid"] = _session_worker_pid(session_id)
            return payload
        warm_fn = getattr(bridge, "warm_session", None)
        if not callable(warm_fn):
            return {
                "enabled": False,
                "mode": mode,
                "session_id": session_id,
                "reason": "missing_warm_session",
            }

        # Strict single-active mode OR an explicit global cap (session-scoped +
        # ATLAS_SESSION_WORKER_MAX_ACTIVE): run ADMISSION synchronously so the
        # response can report ready / started / capacity_wait truthfully.
        # warm_session -> _spawn_process_session -> spawn_result already evaluates
        # the global cap (Task 4) and reserves/replaces the owner slot (Task 3), so
        # a blocking call here is the admission, not the slow model warmup. We never
        # claim "ready" unless the worker is actually alive (manager.is_alive).
        if process_mode and (_strict_mode() or _cap_enabled()):
            try:
                warm_result = warm_fn(session_id)
            except Exception as exc:
                return {
                    "enabled": False,
                    "mode": mode,
                    "session_id": session_id,
                    "error": str(exc),
                }
            warm_result = dict(warm_result or {})
            status = str(warm_result.get("status") or "")
            # warm_session returns status in {ready, started, capacity_wait, error}.
            # Demote a stale "ready/started" that did not actually leave a live
            # worker (defense in depth) and keep capacity_wait verbatim.
            alive_now = _session_worker_alive(session_id, process_mode=True)
            if status in ("ready", "started") and not alive_now:
                status = "error"
            warm_result.setdefault("enabled", True)
            warm_result.setdefault("mode", mode)
            warm_result.setdefault("session_id", session_id)
            warm_result["status"] = status or ("ready" if alive_now else "error")
            warm_result["alive"] = bool(alive_now)
            if "pid" not in warm_result:
                warm_result["pid"] = _session_worker_pid(session_id)
            return warm_result

        # Non-strict (session-scoped) mode: preserve the historical behavior —
        # background the warmup thread and return status="scheduled".
        def _run_background_warmup() -> None:
            try:
                warm_fn(session_id)
            except Exception as exc:
                print(
                    f"[Session] background session worker warmup({session_id!r}) failed: {exc}",
                    flush=True,
                )

        try:
            threading.Thread(
                target=_run_background_warmup,
                name=f"atlas-session-warmup:{session_id}",
                daemon=True,
            ).start()
        except Exception as exc:
            return {"enabled": False, "mode": mode, "session_id": session_id, "error": str(exc)}
        return {
            "enabled": True,
            "mode": mode,
            "session_id": session_id,
            "status": "scheduled",
            "alive": False,
            "background": True,
        }

    # ── /api/session/activate ──────────────────────────────────────
    @app.post("/api/session/activate")
    async def api_session_activate(req: Request):
        """Frontend → backend handshake to keep the canonical
        (owner, ip, workflow) namespace triple in sync.

        Body: {"owner": str, "ip": str, "workflow": str}
        Legacy {"session_id": str} is still accepted as the owner field.
        Each field is optional; missing/empty values default to "default".
        In in-process mode, mirrors ATLAS_ACTIVE_SESSION and ATLAS_ACTIVE_IP
        so legacy path resolvers pivot to the same triple. In process mode,
        keeps the main process globals unchanged and lets the selected worker
        receive the namespace in its own environment when spawned.

        The frontend calls this on page load (so URL params survive a
        restart) and any time the user changes a top dropdown.
        """
        try:
            body = await req.json()
        except Exception:
            body = {}
        body = body or {}
        sid = str(
            body.get("owner")
            or body.get("owner_id")
            or body.get("session_owner")
            or body.get("session_id")
            or ""
        ).strip() or "default"
        workspace_session = str(
            body.get("workspace_session")
            or body.get("workspaceSession")
            or body.get("workspace_id")
            or ""
        ).strip()
        user_name = str(body.get("user_name") or body.get("user") or "").strip()
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
        request_owner = _request_username(req)
        if workspace_session:
            sid = user_name or request_owner or sid
        multi_user_on = _multi_user_enabled()
        # Phantom-IP guard. A stale session (URL param, localStorage, or DB)
        # can restore an IP that no longer exists on disk — e.g. `uart` after
        # it was renamed to `uart_v2`. Activating that phantom IP (a) 404s the
        # file tree ("file tree error — not found"), AND (b) resurfaces the
        # phantom IP's stale saved workflow, emitting a spurious
        # "Switching workflow 'tb-gen' → 'fl-model-gen' (ip=uart)" that desyncs
        # the UI (which shows `default`) from the backend. If the requested IP
        # is neither "default" nor a real project-IP directory, fall back to
        # default/default so the whole stale triple is dropped at the source.
        if ip and ip != "default" and not multi_user_on:
            try:
                if not (project_root() / ip).is_dir():
                    print(
                        f"[Session] activate: IP {ip!r} not found on disk under "
                        f"{project_root()} — falling back to default/default "
                        f"(was workflow={wf!r})",
                        flush=True,
                    )
                    ip = "default"
                    wf = "default"
            except Exception:
                pass
        # Sanitize — refuse exotic path chars to avoid traversal. Usernames
        # may be numeric account ids, so the first segment cannot require a
        # letter.
        for label, val in (
            ("owner", sid),
            ("workspace_session", workspace_session or "default"),
            ("ip", ip),
            ("workflow", wf),
        ):
            if not re.match(r"^[A-Za-z0-9][A-Za-z0-9_-]*$", val):
                return JSONResponse(
                    {"error": f"invalid {label}: {val!r}"},
                    status_code=400,
                )
        if multi_user_on and not request_owner:
            return JSONResponse({"error": "login required"}, status_code=401)
        if multi_user_on and request_owner and sid != request_owner:
            return JSONResponse({"error": "session owner mismatch"}, status_code=403)
        sid = _session_owner_with_model(sid)
        atlas_root = Path(os.environ.get("ATLAS_ROOT") or project_root()).expanduser().resolve()
        if workspace_session:
            context = AtlasContext(
                user_name=sid,
                workspace_session=workspace_session,
                ip_name=ip,
                workflow=wf,
                atlas_root=atlas_root,
            )
        else:
            context = AtlasContext.from_session_key(f"{sid}/{ip}/{wf}", atlas_root=project_root())
        canonical = context.active_session_key
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

        def _using_processes() -> bool:
            try:
                fn = getattr(bridge, "_using_processes", None)
                return bool(fn()) if callable(fn) else False
            except Exception:
                return False

        process_mode = _using_processes()
        keep_session_worker_hot = _session_worker_keepalive_enabled()

        def _active_for_owner(owner: str) -> str:
            try:
                fn = getattr(bridge, "active_session_for_owner", None)
                if callable(fn):
                    return str(fn(owner) or "")
            except Exception:
                pass
            return ""

        def _session_running(session_id: str) -> bool:
            if not session_id:
                return False
            try:
                fn = getattr(bridge, "is_session_running", None)
                if callable(fn):
                    return bool(fn(session_id))
            except Exception:
                pass
            try:
                return bool(getattr(bridge.get_session(session_id), "agent_running", False))
            except Exception:
                return False

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
        prev = _active_for_owner(sid) if multi_user_on else ""
        if not prev:
            candidate_prev = active_session_value() or ""
            candidate_owner = candidate_prev.split("/", 1)[0] if candidate_prev else ""
            if not multi_user_on or not candidate_owner or candidate_owner == sid:
                prev = candidate_prev
        triple_changed = prev != canonical
        was_running = _session_running(prev) if prev else False
        strict_mode = _strict_mode()
        # Wave-3: in strict single-active mode preserve_running must NOT keep an
        # extra interactive worker alive for this owner slot. A real triple change
        # forces the interactive lane to terminate the previous worker regardless
        # of preserve_running (orchestrator job workers are a separate lane and are
        # untouched here).
        preserve_running_effective = preserve_running and not (strict_mode and triple_changed)
        switch_status = "noop"
        previous_session = ""
        terminated_session = ""
        if strict_mode and triple_changed:
            # Route the previous-worker teardown through the SAME strict switch
            # helper both activate endpoints use, so termination ordering /
            # owner-slot reservation is consistent (Task 3). Capture the
            # structured switch result for the response instead of parsing
            # emitted events.
            try:
                switch_result = bridge._prepare_owner_slot_for_session(
                    canonical, reason="activate"
                )
                switch_status = str(switch_result.get("switch_status") or "switched")
                previous_session = str(switch_result.get("previous_session") or "")
                terminated_session = str(switch_result.get("terminated_session") or "")
            except Exception:
                switch_status = "termination_failed"
        halted = bool(prev and triple_changed and was_running and not preserve_running_effective)
        if halted and not (strict_mode and switch_status in ("switched", "noop")):
            try:
                if process_mode and not keep_session_worker_hot:
                    bridge.exit_session(prev or canonical)
                else:
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
        session_worker_warmup: dict[str, Any] = {}
        try:
            bridge.activate_session(canonical)
        except Exception:
            session_worker_warmup = {
                "enabled": False,
                "reason": "activation_failed",
                "error": "bridge.activate_session failed",
            }
        atlas_active_session_cv.set(canonical)
        atlas_active_ip_cv.set(ip)
        # Mirror to os.environ only for in-process chat_loop mode — main.py's
        # chat_loop runs in its own
        # thread and can't see contextvars set inside the FastAPI
        # request task. Without this mirror the /wf prompt that fires
        # right after this handler reads a stale ATLAS_ACTIVE_SESSION
        # and pads the missing IP slot to "default", landing the
        # workspace in .session/default/default/<wf>/ instead of the
        # IP the user just picked. Process workers get a private env at
        # spawn time, so mutating the shared backend env there would be a
        # cross-user last-writer-wins race.
        if not process_mode:
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
        # availability so the user sees the new workspace immediately. In
        # process mode the actual setup runs inside core.session_worker for
        # that namespace; the main backend only emits UI state.
        prev_parts = [part for part in str(prev or "").split("/") if part]
        prev_wf = prev_parts[-1] if len(prev_parts) >= 3 else os.environ.get("ACTIVE_WORKSPACE", "")
        if setup_workspace is not None and wf and wf != prev_wf:
            # Emit via 'token'+'flush' — workspace.jsx subscribes to that
            # streaming channel, not to a bare 'agent' type.
            try:
                _emit_to_canonical(
                    "token",
                    text=f"🔄 Switching workflow '{prev_wf}' → '{wf}' (ip={ip})…\n",
                    source="api/session/activate",
                    control=True,
                    stream=False,
                )
                _emit_to_canonical("flush", source="api/session/activate", control=True)
                _emit_to_canonical("workspace_changing", workspace=wf, prev=prev_wf, ip=ip)
            except Exception:
                pass
            if process_mode:
                try:
                    _emit_to_canonical(
                        "workspace_changed",
                        workspace=wf,
                        prev=prev_wf,
                        ip=ip,
                        session=canonical,
                        source="api/session/activate",
                        process_scoped=True,
                    )
                    _emit_to_canonical(
                        "token",
                        text=f"✅ Workflow switched to '{wf}' (was '{prev_wf}') · ip={ip}\n",
                        source="api/session/activate",
                        control=True,
                        stream=False,
                    )
                    _emit_to_canonical("flush", source="api/session/activate", control=True)
                except Exception:
                    pass
            else:
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
                            source="api/session/activate",
                            control=True,
                            stream=False,
                        )
                        _emit_to_canonical("flush", source="api/session/activate", control=True)
                    except Exception:
                        pass
                except Exception as exc:
                    print(f"[Workflow] activate→setup_workspace({wf!r}) failed: {exc}",
                          flush=True)
            try:
                if not preserve_running:
                    _emit_to_canonical(
                        "agent_state",
                        running=False,
                        source="api/session/activate",
                    )
            except Exception:
                pass
        if triple_changed:
            try:
                _emit_to_canonical("commands_changed")
            except Exception:
                pass
        _root = context.workspace_root
        # Workflow transition marker commit on the per-IP repo. Closes
        # out the previous stage's work as a single labeled checkpoint
        # so the IP history reads like a workflow timeline. Skipped when
        # prev_wf is empty / default (no real work to seal).
        if wf and prev_wf and wf != prev_wf and prev_wf != "default":
            schedule_workflow_checkpoint(
                WorkflowCheckpointRequest(
                    ip_dir=context.ip_root,
                    previous_workflow=prev_wf,
                    next_workflow=wf,
                )
            )
        _session_dir = context.session_dir
        try:
            context.ip_root.mkdir(parents=True, exist_ok=True)
            _session_dir.mkdir(parents=True, exist_ok=True)
            _conv = _session_dir / "conversation.json"
            if not _conv.exists():
                _conv.write_text("[]", encoding="utf-8")
        except Exception:
            pass
        session_row: dict[str, Any] = {}
        try:
            summary = {
                "kind": "atlas_control_plane",
                "namespace": canonical,
                "owner": sid,
                "workspace_session": context.workspace_session,
                "context_key": context.context_key,
                "ip": ip,
                "workflow": wf,
                "workspace_root": str(context.workspace_root),
                "ip_root": str(context.ip_root),
            }
            with _atlas_db() as db:
                session_row = db.upsert_runtime_session(
                    canonical,
                    user_id,
                    owner=sid,
                    ip=ip,
                    workflow=wf,
                    project_id=ip,
                    directory=str(_session_dir),
                    title=f"{ip} / {wf}",
                    status="active",
                    summary=summary,
                )
        except Exception as exc:
            print(f"[Session] activate→db session upsert({canonical!r}) failed: {exc}",
                  flush=True)
        session_payload = _session_context_payload(session_row) if session_row else {}
        worker_warmup: dict[str, Any] = {}
        try:
            try:
                from atlas_api_jobs import schedule_worker_warmup  # noqa: WPS433
            except ImportError:
                from src.atlas_api_jobs import schedule_worker_warmup  # type: ignore  # noqa: WPS433

            worker_warmup = schedule_worker_warmup(
                ip=ip,
                owner=sid,
                db_user_id=user_id,
                session_name=canonical,
                active_workflow=wf,
                    project_root_value=str(_root),
                reason="session_activate",
                background=True,
            )
        except Exception as exc:
            worker_warmup = {"enabled": False, "error": str(exc)}
        if keep_session_worker_hot and "error" not in session_worker_warmup:
            session_worker_warmup = _schedule_session_worker_warmup(
                canonical,
                process_mode=process_mode,
            )
        # Activation may SUCCEED as a focus change even when warmup is
        # capacity-blocked: surface switch_status=active_no_worker +
        # session_worker_warmup.status=capacity_wait, HTTP 200, and NEVER "ready"
        # unless the worker is actually alive (warm_session already gates on
        # manager.is_alive). The owner-slot mapping has already been advanced to
        # the new canonical session by the strict switch helper above.
        if str((session_worker_warmup or {}).get("status") or "") == "capacity_wait":
            switch_status = "active_no_worker"
        try:
            _policy_view = bridge.session_worker_policy().to_status_dict()
            _single_active = bool(bridge.session_worker_policy().is_strict)
        except Exception:
            _policy_view = {}
            _single_active = False
        return JSONResponse({
            "ok": True,
            "active_session": canonical,
            "namespace": canonical,
            "context_key": context.context_key,
            "owner": sid,
            "owner_id": sid,
            "user_id": user_id,
            "session_id": sid,
            "workspace_session": context.workspace_session,
            "workspace_root": str(context.workspace_root),
            "ip_root": str(context.ip_root),
            "session_dir": str(context.session_dir),
            "db_session_id": canonical,
            "runtime_session_id": session_payload.get("session_uid") or "",
            "session_uid": session_payload.get("session_uid") or "",
            "session_label": session_payload.get("session_label") or "",
            "session": session_payload,
            "ip": ip,
            "workflow": wf,
            "halted": halted,
            "preserve_running": preserve_running,
            "preserve_running_effective": preserve_running_effective,
            "process_scoped": process_mode,
            "session_worker_policy": _policy_view,
            "single_active_owner": _single_active,
            "authenticated_owner": request_owner or sid,
            "owner_slot": sid,
            "previous_session": previous_session,
            "terminated_session": terminated_session,
            "switch_status": switch_status,
            "worker_warmup": worker_warmup,
            "session_worker_warmup": session_worker_warmup or {
                "enabled": False,
                "reason": "disabled",
            },
        })

    # ── /api/session/history ───────────────────────────────────────
    def _session_triple(session: str) -> tuple[str, str, str]:
        parts = [part for part in normalize_session_name(str(session or "")).split("/") if part]
        if len(parts) >= 3:
            return parts[0], parts[-2], parts[-1]
        return "", "", ""

    def _chat_row_to_conversation_message(row: dict[str, Any]) -> dict[str, Any]:
        payload = row.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        role = str((payload or {}).get("role") or "user").strip() or "user"
        content = str((payload or {}).get("content") or "")
        return {
            "id": row.get("id"),
            "role": role,
            "agent": str((payload or {}).get("display_name") or ""),
            "created_at": row.get("created_at"),
            "content": content,
            "text": content,
            "source": "orchestrator_chat",
        }

    def _orchestrator_chat_messages_for_session(
        session: str,
        user_id: str,
        limit: int,
    ) -> list[dict[str, Any]]:
        """Return per-IP orchestrator chat rows for an orchestrator namespace.

        Pipeline/orchestrator chat is stored as trace ``chat_message`` rows
        keyed by IP, while the normal workspace hydrate path reads
        ``.session/<owner>/<ip>/<workflow>/conversation.json`` or DB
        conversation messages.  Merging this read-side view keeps the
        orchestrator chat visible after workflow and pipeline screen switches.
        """
        _owner, ip, workflow = _session_triple(session)
        if workflow != "orchestrator" or not ip or ip == "default":
            return []
        if limit == 0:
            return []
        bound = 200 if limit < 0 else max(1, min(int(limit or 200), 500))
        try:
            PROJECT_ROOT = project_root()
            with _atlas_db() as db:
                workspace = db.upsert_workspace(
                    PROJECT_ROOT.name or "default",
                    owner_user_id=user_id or "default",
                    local_path=str(PROJECT_ROOT),
                )
                ip_row = db.upsert_ip_block(workspace["id"], ip)
                rows = db.list_chat_messages(ip_id=ip_row["id"], limit=bound)
        except Exception:
            return []
        rows = list(reversed(rows))
        return [_chat_row_to_conversation_message(row) for row in rows]

    def _merge_orchestrator_chat_messages(
        session: str,
        messages: list[dict[str, Any]],
        user_id: str,
        limit: int,
    ) -> tuple[list[dict[str, Any]], bool]:
        chat_messages = _orchestrator_chat_messages_for_session(session, user_id, limit)
        if not chat_messages:
            return messages, False
        seen = {
            (
                str(m.get("role") or ""),
                str(m.get("content") or m.get("text") or ""),
                str(m.get("id") or ""),
            )
            for m in messages
            if isinstance(m, dict)
        }
        merged = list(messages)
        for msg in chat_messages:
            key = (
                str(msg.get("role") or ""),
                str(msg.get("content") or msg.get("text") or ""),
                str(msg.get("id") or ""),
            )
            if key not in seen:
                merged.append(msg)
                seen.add(key)
        try:
            merged.sort(key=lambda m: float(m.get("created_at") or 0))
        except Exception:
            pass
        if limit == 0:
            merged = []
        elif limit > 0 and len(merged) > limit:
            merged = merged[-limit:]
        return merged, True

    def _db_conversation_messages(
        session_id: str,
        user_id: str = "",
    ) -> Optional[list[dict[str, Any]]]:
        """Return DB-backed conversation messages when *session_id* is a DB session.

        Read-path routing (plan §2.10 / Task 8 item 1): the session/ownership row
        is resolved from the CONTROL DB, but the per-session ``messages``/``parts``
        rows MOVE to the per-session runtime DB in ``ATLAS_RUNTIME_DB_MODE=session``.
        We therefore resolve the session against control, then read messages/parts
        through ``AtlasDBRouter().runtime_db(db_session_id, create=False)``. In
        central mode (default) the router returns the control path, so this is the
        unchanged behavior. A missing runtime DB is NOT treated as authoritative
        empty: we fall through to the control read so a freshly-activated session
        (manifest not yet created) still shows any control-side history.
        """
        try:
            with _atlas_db() as db:
                session_row = (
                    db.get_session_for_user(user_id, session_id)
                    if user_id else db.get_session(session_id)
                )
                if session_row is None:
                    return None
                db_session_id = str(session_row.get("id") or session_id)
                msg_db, close_msg_db = _runtime_read_db_for_messages(db, db_session_id)
                try:
                    return _collect_conversation_messages(msg_db, db_session_id)
                finally:
                    if close_msg_db and msg_db is not None:
                        try:
                            msg_db.close()
                        except Exception:
                            pass
        except Exception:
            return None

    def _runtime_read_db_for_messages(control_db: Any, db_session_id: str):
        """Resolve which DB holds this session's messages/parts.

        Returns ``(db, should_close)``. In central mode (or when the session has no
        runtime manifest yet) returns the already-open control ``db`` with
        should_close=False. In session mode with a resolvable runtime file, opens
        the per-session runtime DB read-only and returns it with should_close=True.
        """
        try:
            from core.atlas_db_router import AtlasDBRouter

            router = AtlasDBRouter()
            if router.mode() != "session":
                return control_db, False
            # Only route when a runtime DB actually exists for this session; a
            # not-yet-activated session has no manifest -> read control (which may
            # legitimately carry pre-split history) rather than fail closed.
            manifest = control_db.get_session_runtime_db(db_session_id)
            if not manifest:
                return control_db, False
            return router.runtime_db(db_session_id, create=False), True
        except Exception:
            return control_db, False

    def _collect_conversation_messages(
        db: Any,
        db_session_id: str,
    ) -> list[dict[str, Any]]:
        messages: list[dict[str, Any]] = []
        for msg in db.get_messages(db_session_id):
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

    def _conversation_message_key(msg: dict[str, Any]) -> tuple[str, str, str, str]:
        role = str(msg.get("role") or "")
        content = str(msg.get("content") or msg.get("text") or "")
        tool = str(msg.get("name") or msg.get("tool") or "")
        msg_id = str(msg.get("id") or "")
        return role, content, tool, msg_id

    def _merge_conversation_sources(
        file_messages: list[dict[str, Any]],
        db_messages: Optional[list[dict[str, Any]]],
    ) -> tuple[list[dict[str, Any]], str]:
        """Combine file-backed worker history with DB-backed chat/session rows.

        `/api/session/activate` creates DB runtime sessions even before that
        session has DB messages.  If an empty DB row wins unconditionally, the
        real worker `conversation.json` becomes invisible in the UI.
        """
        file_clean = [
            m for m in file_messages
            if isinstance(m, dict) and m.get("role") != "system"
        ]
        db_clean = [
            m for m in (db_messages or [])
            if isinstance(m, dict) and m.get("role") != "system"
        ]
        if not db_clean:
            return file_clean, "file"
        if not file_clean:
            return db_clean, "db"
        merged: list[dict[str, Any]] = []
        seen: set[tuple[str, str, str, str]] = set()
        for msg in [*file_clean, *db_clean]:
            key = _conversation_message_key(msg)
            if key in seen:
                continue
            merged.append(msg)
            seen.add(key)
        return merged, "file+db"

    @app.get("/api/session/history")
    async def api_session_history(request: Request, session: str, limit: int = 200):
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
        access_error = _authorize_session_request(request, session)
        if access_error is not None:
            return access_error
        hpath = sdir / "conversation.json"
        file_msgs: list[dict[str, Any]] = []
        if hpath.is_file():
            try:
                raw_msgs = json.loads(hpath.read_text(encoding="utf-8"))
                if isinstance(raw_msgs, list):
                    file_msgs = [m for m in raw_msgs if isinstance(m, dict)]
            except Exception as e:
                db_msgs = _db_conversation_messages(session, _request_user_id(request))
                if db_msgs is None:
                    return JSONResponse({"messages": [], "session": session,
                                         "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                         "error": f"parse: {e}"}, status_code=500)
        db_msgs = _db_conversation_messages(session, _request_user_id(request))
        if db_msgs is None and not hpath.is_file():
            return JSONResponse({"messages": [], "session": session,
                                 "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                 "exists": False, "source": "file"})
        msgs, source = _merge_conversation_sources(file_msgs, db_msgs)
        # `limit == 0` must return an empty list. The previous form
        # `msgs[-limit:]` becomes `msgs[-0:]` == `msgs[0:]` == full list
        # because Python collapses -0 to 0, so limit=0 paradoxically
        # returned everything. Guard explicitly. limit < 0 is also
        # treated as "no clamp" so callers can opt out with -1.
        if limit == 0:
            msgs = []
        elif limit > 0 and len(msgs) > limit:
            msgs = msgs[-limit:]
        msgs, chat_merged = _merge_orchestrator_chat_messages(
            session,
            msgs,
            _request_user_id(request),
            limit,
        )
        return JSONResponse({"messages": msgs, "session": session,
                             "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                             "exists": bool(db_msgs is not None or hpath.is_file()),
                             "source": f"{source}+orchestrator_chat" if chat_merged else source,
                             "truncated_to": limit})

    # ── /api/session/state ─────────────────────────────────────────
    @app.get("/api/session/state")
    async def api_session_state(request: Request, session: str, limit: int = 200, mode: str = "conversation"):
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
        access_error = _authorize_session_request(request, session)
        if access_error is not None:
            return access_error

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

        file_messages = _read_json(conv_path, [])
        if not isinstance(file_messages, list):
            file_messages = []
        db_messages = _db_conversation_messages(session, _request_user_id(request))
        messages, conversation_source = _merge_conversation_sources(
            [m for m in file_messages if isinstance(m, dict)],
            db_messages,
        )
        # `full` returns everything; `conversation` and `recent` cap at limit.
        # Same `-0 == 0` guard as /api/session/history above.
        if mode_norm != "full":
            if limit == 0:
                messages = []
            elif limit > 0 and len(messages) > limit:
                messages = messages[-limit:]
        messages, chat_merged = _merge_orchestrator_chat_messages(
            session,
            messages,
            _request_user_id(request),
            -1 if mode_norm == "full" else limit,
        )
        if chat_merged:
            conversation_source = f"{conversation_source}+orchestrator_chat"

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
        if multi_user_on and not owner:
            return JSONResponse({"error": "login required", "sessions": [], "count": 0}, status_code=401)
        db_by_namespace: dict[str, dict[str, Any]] = {}
        user_id = _request_user_id(request)
        try:
            with _atlas_db() as db:
                for item in db.list_sessions(user_id):
                    if not isinstance(item, dict):
                        continue
                    namespace = str(item.get("namespace") or item.get("id") or "").strip()
                    if namespace:
                        db_by_namespace[namespace] = item
        except Exception:
            db_by_namespace = {}
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
                db_session = db_by_namespace.get(session) or {}
                row = {
                    "session": session,
                    "path": p.relative_to(PROJECT_ROOT).as_posix(),
                    "mtime": p.stat().st_mtime,
                    "size": p.stat().st_size,
                }
                row.update(_session_context_payload(db_session))
                out.append(row)
        seen = {str(row.get("session") or "") for row in out}
        for namespace, db_session in db_by_namespace.items():
            if namespace in seen:
                continue
            if multi_user_on and owner:
                parts = [part for part in namespace.split("/") if part]
                if len(parts) >= 3 and parts[0] != owner:
                    continue
            row = {
                "session": namespace,
                "path": "",
                "mtime": db_session.get("updated_at") or 0,
                "size": 0,
            }
            row.update(_session_context_payload(db_session))
            out.append(row)
        return JSONResponse({"sessions": out, "count": len(out)})

    # ── Atlas SQLite session CRUD (/api/sessions*) ─────────────────

    def _atlas_db():
        db = atlas_db_factory()
        try:
            Path(str(db.db_path)).expanduser().parent.mkdir(parents=True, exist_ok=True)
        except Exception:
            pass
        return db

    def _session_label(session: dict) -> str:
        uid = str(session.get("session_uid") or "").strip()
        if uid:
            return f"S-{uid[:8]}"
        namespace = str(session.get("namespace") or session.get("id") or "").strip()
        return namespace or ""

    def _session_context_payload(session: Optional[dict]) -> dict[str, Any]:
        if not isinstance(session, dict) or not session:
            return {}
        summary = session.get("summary") if isinstance(session.get("summary"), dict) else {}
        namespace = str(session.get("namespace") or summary.get("namespace") or session.get("id") or "")
        owner = str(session.get("owner") or summary.get("owner") or "")
        ip = str(session.get("ip_id") or session.get("ip") or summary.get("ip") or session.get("project_id") or "")
        workflow = str(session.get("workflow") or summary.get("workflow") or "")
        return {
            "db_session_id": session.get("id") or "",
            "session_uid": session.get("session_uid") or "",
            "session_label": _session_label(session),
            "namespace": namespace,
            "owner": owner,
            "ip": ip,
            "workflow": workflow,
            "session_kind": session.get("session_kind") or "",
        }

    def _namespace_owner(session: str) -> str:
        parts = [part for part in normalize_session_name(str(session or "")).split("/") if part]
        return parts[0] if len(parts) >= 3 else ""

    def _authorize_session_request(request: Request, session: str) -> Optional[JSONResponse]:
        if not _multi_user_enabled():
            return None
        owner = _request_username(request)
        if not owner:
            return JSONResponse({"error": "login required"}, status_code=401)
        user_id = _request_user_id(request)
        namespace_owner = _namespace_owner(session)
        if namespace_owner and namespace_owner != owner:
            return JSONResponse({"error": "session owner mismatch"}, status_code=403)
        # FAIL CLOSED (plan §2.11 / R20): the ownership lookup is the authorization
        # decision, so a DB error must DENY, never allow. We keep the lookup on the
        # CONTROL DB (``_atlas_db``) — never a per-session runtime file — so a
        # corrupt/missing runtime DB can never affect who is allowed in.
        try:
            with _atlas_db() as db:
                owned = db.get_session_for_user(user_id, session)
                if owned is not None:
                    return None
                existing = db.find_session(session)
                if existing is not None and existing.get("user_id") != user_id:
                    return JSONResponse({"error": "session owner mismatch"}, status_code=403)
        except Exception:
            # Authz lookup failed -> we cannot prove ownership -> deny.
            return JSONResponse({"error": "authorization unavailable"}, status_code=403)
        return None

    def _public_session(session: dict, include_summary: bool = False) -> dict:
        fields = [
            "id", "session_uid", "user_id", "namespace", "owner", "title",
            "project_id", "workspace_id", "ip_id", "ip", "workflow",
            "session_kind", "status", "created_at", "updated_at",
        ]
        if include_summary:
            fields.append("summary")
        return {key: session.get(key) for key in fields}

    def _worker_policy_status() -> dict[str, Any]:
        """Resolved policy view for the status endpoint.

        Prefers the bridge's live policy (``bridge._policy``, wired in Task 2) and
        falls back to parsing the env so this endpoint reports the real active
        policy even if the bridge accessor is unavailable.
        """
        policy = getattr(bridge, "_policy", None)
        if policy is None:
            try:
                from core.session_worker_policy import SessionWorkerPolicy
                policy = SessionWorkerPolicy.from_env()
            except Exception:
                policy = None
        if policy is not None and hasattr(policy, "to_status_dict"):
            base = dict(policy.to_status_dict())
            base["idle_ttl_sec"] = getattr(policy, "idle_ttl_sec", None)
            return base
        return {
            "policy": "session-scoped",
            "single_active_owner": False,
            "cap_enabled": False,
            "max_active": 0,
        }

    def _process_mode_on() -> bool:
        fn = getattr(bridge, "_using_processes", None)
        try:
            return bool(fn()) if callable(fn) else False
        except Exception:
            return False

    def _active_worker_count() -> int:
        manager = getattr(bridge, "_process_manager", None)
        if manager is None:
            return 0
        try:
            return len(list(manager.list_active()))
        except Exception:
            return 0

    def _worker_view(session_id: str) -> Optional[dict[str, Any]]:
        """Per-worker status for one canonical session id, or None if no slot."""
        if not session_id:
            return None
        process_mode = _process_mode_on()
        alive = _session_worker_alive(session_id, process_mode=process_mode)
        running = False
        try:
            is_running = getattr(bridge, "is_session_running", None)
            if callable(is_running):
                running = bool(is_running(session_id))
            else:
                running = bool(getattr(bridge.get_session(session_id), "agent_running", False))
        except Exception:
            running = False
        if not alive and not running:
            return None
        view: dict[str, Any] = {
            "session_id": session_id,
            "alive": bool(alive),
            "running": bool(running),
            "pid": _session_worker_pid(session_id) if process_mode else 0,
            "state": "running" if running else ("ready" if alive else "starting"),
        }
        # idle_age_sec: prefer the bridge's Task-7 idle clock and fall back to the
        # session bridge's last_active so the field is present regardless.
        try:
            import time as _t
            idle_fn = getattr(bridge, "_worker_idle_age_sec", None)
            manager = getattr(bridge, "_process_manager", None)
            if callable(idle_fn) and manager is not None:
                view["idle_age_sec"] = round(float(idle_fn(manager, session_id, _t.time())), 3)
            else:
                sess = bridge.get_session(session_id)
                view["idle_age_sec"] = round(max(0.0, _t.time() - float(getattr(sess, "last_active", _t.time()))), 3)
        except Exception:
            pass
        return view

    @app.get("/api/session/worker/status")
    async def api_session_worker_status(request: Request):
        """Interactive session-worker status, scoped to the caller's owner slot.

        User-scoped by default (plan Status Endpoint Scope / Wave-3 H8): never
        exposes another owner's session ids. An all-owner inventory is returned
        ONLY when register_sessions_routes() was passed an ``admin_check``
        callback that returns True for this request. Independent of
        /api/orchestrator/workers (interactive workers != workflow workers).
        """
        try:
            payload: dict[str, Any] = _worker_policy_status()
            payload["active_count"] = _active_worker_count()

            authenticated_owner = _request_username(request)
            # The owner SLOT can differ from the raw login when
            # ATLAS_SESSION_PER_MODEL=1 (e.g. alice -> alice__gpt_5).
            owner_slot = _session_owner_with_model(authenticated_owner) if authenticated_owner else ""

            owner_active_session = ""
            try:
                active_fn = getattr(bridge, "active_session_for_owner", None)
                if callable(active_fn) and owner_slot:
                    owner_active_session = str(active_fn(owner_slot) or "")
            except Exception:
                owner_active_session = ""

            payload["owner"] = owner_slot or authenticated_owner
            payload["authenticated_owner"] = authenticated_owner
            # Only surface owner_slot explicitly when it diverges from the login
            # (acceptance: return both when they differ).
            if owner_slot and owner_slot != authenticated_owner:
                payload["owner_slot"] = owner_slot
            payload["owner_active_session"] = owner_active_session
            payload["worker"] = _worker_view(owner_active_session)

            # Admin all-owner inventory — ONLY behind an explicit admin_check.
            if admin_check is not None:
                try:
                    is_admin = bool(admin_check(request))
                except Exception:
                    is_admin = False
                if is_admin:
                    owners: list[dict[str, Any]] = []
                    seen: set[str] = set()
                    snapshot = dict(getattr(bridge, "_owner_active_sessions", {}) or {})
                    for owner, sess_id in snapshot.items():
                        if owner in seen:
                            continue
                        seen.add(owner)
                        owners.append({
                            "owner": owner,
                            "owner_active_session": str(sess_id or ""),
                            "worker": _worker_view(str(sess_id or "")),
                        })
                    payload["owners"] = owners

            return JSONResponse(payload)
        except Exception as e:
            print(f"api_session_worker_status error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

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
                session = db.get_session_for_user(user_id, session_id)
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
                session = db.get_session_for_user(user_id, session_id)
                if not _owns_session(session, user_id):
                    return _session_not_found()
                if fields:
                    db.update_session(session["id"], **fields)
                updated = db.get_session(session["id"])
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
                session = db.get_session_for_user(user_id, session_id)
                if not _owns_session(session, user_id):
                    return _session_not_found()
                # Thread the LIVE process manager so the per-session runtime DB
                # handle is evicted (no stale-inode reuse / fd leak) and the
                # runtime .db/-wal/-shm + manifest/rollup/offset rows are scrubbed
                # in session mode (T9 R12). Central mode = no-op.
                manager = getattr(bridge, "_process_manager", None)
                result = db.delete_session(
                    session["id"],
                    force=force_delete_requested(request),
                    process_manager=manager,
                )
                return session_delete_response(result)
        except Exception as e:
            print(f"api_delete_session error: {e}")
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.post("/api/sessions/{session_id}/activate")
    async def api_activate_session(session_id: str, request: Request):
        # Activate the session: verify the caller owns it, then make the
        # backend bridge actually point at it. BOTH activate endpoints route the
        # SAME strict switch helper (Wave-3 / Task 6): in single-active mode this
        # terminates the previous owner-slot worker before warming the new one
        # and may succeed as a focus change (active_no_worker) when capacity is
        # exhausted.
        try:
            user_id = _request_user_id(request)
            with _atlas_db() as db:
                session = db.get_session_for_user(user_id, session_id)
                if not _owns_session(session, user_id):
                    return JSONResponse(
                        {"error": "session not found or not owned by user"},
                        status_code=404,
                    )
            canonical = str(session["id"])
            owner_slot = str(
                session.get("owner")
                or (canonical.split("/", 1)[0] if "/" in canonical else canonical)
            )
            request_owner = _request_username(request)

            def _process_mode() -> bool:
                try:
                    fn = getattr(bridge, "_using_processes", None)
                    return bool(fn()) if callable(fn) else False
                except Exception:
                    return False

            process_mode = _process_mode()
            strict_mode = _strict_mode()
            switch_status = "noop"
            previous_session = ""
            terminated_session = ""
            if strict_mode:
                try:
                    switch_result = bridge._prepare_owner_slot_for_session(
                        canonical, reason="activate"
                    )
                    switch_status = str(switch_result.get("switch_status") or "switched")
                    previous_session = str(switch_result.get("previous_session") or "")
                    terminated_session = str(switch_result.get("terminated_session") or "")
                except Exception:
                    switch_status = "termination_failed"
            # Bind on the bridge so emit/inbox/outbox routing follows.
            bridge.activate_session(canonical)
            session_worker_warmup: dict[str, Any] = {}
            if _session_worker_keepalive_enabled():
                session_worker_warmup = _schedule_session_worker_warmup(
                    canonical, process_mode=process_mode
                )
            if str((session_worker_warmup or {}).get("status") or "") == "capacity_wait":
                switch_status = "active_no_worker"
            try:
                _policy_view = bridge.session_worker_policy().to_status_dict()
                _single_active = bool(bridge.session_worker_policy().is_strict)
            except Exception:
                _policy_view = {}
                _single_active = False
            return JSONResponse({
                "activated": True,
                "session_id": canonical,
                "active_session": canonical,
                "process_scoped": process_mode,
                "session_worker_policy": _policy_view,
                "single_active_owner": _single_active,
                "authenticated_owner": request_owner or owner_slot,
                "owner_slot": owner_slot,
                "previous_session": previous_session,
                "terminated_session": terminated_session,
                "switch_status": switch_status,
                "session_worker_warmup": session_worker_warmup or {
                    "enabled": False,
                    "reason": "disabled",
                },
            })
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
