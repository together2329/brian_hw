"""Orchestrator chat injector wired into the ReAct loop.

The injector pulls a fresh per-iteration snapshot from AtlasDB —
- the same per-IP / global context bundle the OrchestratorPanel
  shows the user, and
- the list of chat_message rows the running session has not yet
  recorded `chat_consumed` for
— and appends them as a system-side block on `messages[0]` so the
LLM sees humans' feedback and the live ground truth on the next
turn. After injection it writes `chat_consumed` rows to the trace
ledger and advances the bridge watermark so the same feedback is
not replayed every iteration.

Wiring: callers (src/main.py, core/agent_server.py) build the
callable with `build_orchestrator_inject_fn(db, bridge)` and pass
it as `ReactLoopDeps.orchestrator_inject_fn`.
"""
from __future__ import annotations

import json
import os
from typing import Any, Callable, List, Optional


_MAX_CTX_EVENTS_RENDERED = 8
_MAX_BLOCKERS_RENDERED = 5


# Bridge registry — atlas_ui.py calls register_bridge(bridge) after
# constructing the multi-user bridge so the injector (which is built
# inside main.py before bridge exists in some flows) can resolve it
# lazily on first iteration without circular imports.
_REGISTERED_BRIDGE: Any = None


def register_bridge(bridge: Any) -> None:
    global _REGISTERED_BRIDGE
    _REGISTERED_BRIDGE = bridge


def get_registered_bridge() -> Any:
    return _REGISTERED_BRIDGE


def _resolve_active_ip(db: Any) -> Optional[dict]:
    """ATLAS_ACTIVE_IP holds the ip_name the session is bound to."""
    name = os.environ.get("ATLAS_ACTIVE_IP") or os.environ.get("ACTIVE_IP")
    if not name or name in {"default", ""}:
        return None
    try:
        return db.get_ip_block_by_name(name)
    except Exception:
        return None


def _render_orchestrator_block(ctx: dict, room: str) -> str:
    """Compact text rendering — keep the LLM-facing block small. The
    JSON form goes to the UI; the agent gets a flattened summary so
    token cost stays bounded even when an IP has many stages."""
    lines: List[str] = [f"<orchestrator-context room={room!r}>"]
    ip = ctx.get("ip") or {}
    if ip:
        lines.append(
            f"ip: {ip.get('name')} ({ip.get('type') or '?'})"
        )
    wf = (ctx.get("workflow") or {}).get("latest_run") or {}
    if wf:
        lines.append(
            f"workflow: {wf.get('workflow')} / {wf.get('status')}"
            f" / stage={wf.get('current_stage') or '?'}"
            f" / mode={wf.get('mode') or '?'}"
            f" / model={wf.get('model_profile') or '?'}"
        )
    todos = ctx.get("todos") or {}
    counts = todos.get("counts") or {}
    if counts:
        rendered_counts = ", ".join(f"{k}={v}" for k, v in counts.items())
        lines.append(f"todos: {rendered_counts}")
    blockers = (todos.get("top_blockers") or [])[:_MAX_BLOCKERS_RENDERED]
    for b in blockers:
        lines.append(
            f"  - blocker[{b.get('status')}] {b.get('title')}"
        )
    gates = ctx.get("gates") or {}
    for name, info in gates.items():
        if info is None:
            continue
        if isinstance(info, dict) and "errors" in info:
            lines.append(
                f"gate.{name}: errors={info.get('errors')} warnings={info.get('warnings')}"
            )
        elif isinstance(info, dict) and "status" in info:
            lines.append(f"gate.{name}: {info.get('status')}")
    recent = ctx.get("recent_events") or []
    for ev in recent[:_MAX_CTX_EVENTS_RENDERED]:
        if ev.get("kind") == "llm":
            lines.append(
                f"  llm {ev.get('model')} in={ev.get('tokens_input')}"
                f" out={ev.get('tokens_output')} cost=${ev.get('cost_usd') or 0}"
            )
        else:
            lines.append(f"  {ev.get('event_type') or ev.get('kind')}")
    lines.append("</orchestrator-context>")
    return "\n".join(lines)


def _render_global_block(ctx: dict) -> str:
    lines: List[str] = ["<orchestrator-context room='_global'>"]
    for ip in (ctx.get("ips") or [])[:25]:
        lines.append(
            f"  {ip.get('name')}: {ip.get('latest_workflow') or '-'}"
            f"/{ip.get('run_status') or '-'}"
            f"  open={ip.get('open_blockers')}  done={ip.get('completed')}"
        )
    lines.append("</orchestrator-context>")
    return "\n".join(lines)


def _render_chat_block(messages: List[dict], room: str) -> str:
    lines = [f"<team-chat-feedback room={room!r}>"]
    for m in messages:
        payload = m.get("payload") or {}
        if isinstance(payload, str):
            try:
                payload = json.loads(payload)
            except Exception:
                payload = {}
        content = (payload.get("content") or "").strip()
        if not content:
            continue
        display = payload.get("display_name") or m.get("actor_user_id") or "user"
        lines.append(f"[{display}] {content}")
    lines.append("</team-chat-feedback>")
    lines.append(
        "(humans → agent feedback. Treat as authoritative guidance from"
        " teammates on this IP. Acknowledge in your next action, do not"
        " ask the orchestrator to repeat it.)"
    )
    return "\n".join(lines)


def _append_to_system_message(messages: List[dict], block: str) -> None:
    head = messages[0] if messages else None
    if not head or head.get("role") != "system":
        return
    content = head.get("content", "")
    sep = "\n\n" + block
    if isinstance(content, str):
        head["content"] = content + sep
    elif isinstance(content, list):
        # Native multimodal/blocks form — append as a text block. Do
        # not give it a cache_control hint so it stays mutable.
        content.append({"type": "text", "text": sep})


def build_orchestrator_inject_fn(db: Any, bridge: Any) -> Callable[[List[dict], str], None]:
    """Return a callable suitable for ReactLoopDeps.orchestrator_inject_fn.

    `db`     is an AtlasDB (or compatible) handle.
    `bridge` is a _MultiUserBridge (or single _SessionBridge) — used to
             resolve the current session_id and store the watermark on
             `last_chat_seen_id`. Pass None if neither is available
             yet; the injector becomes a no-op in that case.
    """
    def _resolve_session() -> Any:
        # Late-bind to the registry so a bridge registered after the
        # injector was built (typical when atlas_ui wires the bridge
        # mid-boot) is still picked up.
        live_bridge = bridge if bridge is not None else _REGISTERED_BRIDGE
        if live_bridge is None:
            return None
        # Prefer the context-bound session if set (atlas_ui bridge model).
        try:
            from core.atlas_multiuser import get_atlas_bridge_session_id  # type: ignore
            sid = get_atlas_bridge_session_id() or ""
            if sid and hasattr(live_bridge, "_ensure_session"):
                return live_bridge._ensure_session(sid)
        except Exception:
            pass
        if hasattr(live_bridge, "_active_session"):
            try:
                return live_bridge._active_session()
            except Exception:
                return None
        return live_bridge  # already a _SessionBridge

    def _inject(messages: List[dict], agent_mode: str) -> None:
        if not messages or messages[0].get("role") != "system":
            return

        session = _resolve_session()
        session_id = getattr(session, "session_id", "") or ""

        ip = _resolve_active_ip(db)
        ip_id = ip["id"] if ip else None
        room = ip["ip_name"] if ip else "_global"

        # Seed watermark from the trace ledger on first run after a
        # restart so we do not re-inject already-consumed chats.
        if session is not None and not getattr(session, "last_chat_seen_id", ""):
            try:
                last = db.latest_chat_consumed_id(
                    session_id=session_id, ip_id=ip_id
                )
                if last:
                    session.last_chat_seen_id = last
            except Exception:
                pass

        after_id = getattr(session, "last_chat_seen_id", "") or None

        # Pull unread for THIS agent's room AND the cross-cutting
        # _global room. A per-IP agent owes attention to both: IP-room
        # posts are local guidance; _global posts are workspace-wide
        # policy/announcement (the user spec was explicit: "each ip
        # → ip's flow meta data; global ip → need all meta data").
        unread_ip: list = []
        unread_global: list = []
        try:
            if ip_id:
                unread_ip = db.list_chat_unconsumed_for(
                    session_id=session_id, ip_id=ip_id, after_id=after_id
                )
            unread_global = db.list_chat_unconsumed_for(
                session_id=session_id, ip_id=None, after_id=None
            )
        except Exception:
            unread_ip = []
            unread_global = []

        # Context bundle (shown to UI + the agent on every iteration so
        # the live ground truth stays in front of the model).
        try:
            if ip_id:
                ctx = db.summarize_ip_room_context(ip_id)
                if ctx:
                    _append_to_system_message(
                        messages, _render_orchestrator_block(ctx, room)
                    )
            else:
                ctx = db.summarize_global_room_context()
                if ctx:
                    _append_to_system_message(
                        messages, _render_global_block(ctx)
                    )
        except Exception:
            pass

        if unread_ip:
            _append_to_system_message(
                messages, _render_chat_block(unread_ip, room)
            )
        if unread_global:
            _append_to_system_message(
                messages, _render_chat_block(unread_global, "_global")
            )

        # Mark each chat as consumed by this session, then advance the
        # in-memory IP-room watermark so a fast subsequent iteration
        # without DB re-read still skips them. (The _global watermark
        # is owned by chat_consumed rows in the ledger keyed on
        # session_id + correlation_id; no separate in-memory cursor.)
        for m in list(unread_ip) + list(unread_global):
            try:
                db.record_chat_consumed(
                    chat_id=m["id"],
                    session_id=session_id,
                    ip_id=(m.get("ip_id") or None),
                )
            except Exception:
                continue
        if session is not None and unread_ip:
            try:
                session.last_chat_seen_id = unread_ip[-1]["id"]
            except Exception:
                pass

    return _inject
