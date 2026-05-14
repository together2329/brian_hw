"""ATLAS Orchestrator Chat API.

Per-IP rooms (one per ip_blocks row by ip_name) and one global room
('_global') for cross-IP guidance. Storage lives on `trace_events`
(no chat_messages table) so chat appears on the same observability
timeline as workflow_event / llm_call rows.

Permission model (delegated to PermissionPolicy.require_room_access):
  - per-IP room: caller needs `view` on the IP
  - _global room: caller needs at least one IP view grant or owns a
    workspace, or is admin

POST broadcasts via `bridge.broadcast_all` so every connected WS
client across every session receives chat_message events; the
frontend filters by room.
"""
from __future__ import annotations

from typing import Any, Callable, Optional

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse

from core.atlas_db import AtlasDB
from core.atlas_permissions import PermissionDenied, PermissionPolicy


_DEFAULT_LIMIT = 50
_MAX_LIMIT = 200
_MAX_CONTENT_BYTES = 8000


def _resolve_user(request: Request) -> Optional[dict]:
    """Auth is populated by core.atlas_auth.AuthMiddleware into
    request.scope['user']. Return that dict or None for anonymous."""
    user = request.scope.get("user") if hasattr(request, "scope") else None
    if isinstance(user, dict) and user.get("id"):
        return user
    return None


def _require_user(request: Request) -> Optional[dict]:
    user = _resolve_user(request)
    if user is None:
        return None
    return user


def _err(status: int, message: str) -> JSONResponse:
    return JSONResponse({"error": message}, status_code=status)


def _chat_row_to_message(row: dict) -> dict:
    payload = row.get("payload") or {}
    if isinstance(payload, str):
        # _row_to_dict already json-decodes, but be defensive.
        try:
            import json as _json
            payload = _json.loads(payload)
        except Exception:
            payload = {}
    return {
        "id": row.get("id"),
        "ip_id": row.get("ip_id") or None,
        "user_id": row.get("actor_user_id"),
        "display_name": payload.get("display_name") or "",
        "content": payload.get("content") or "",
        "created_at": row.get("created_at"),
    }


def register_chat_routes(
    app: FastAPI,
    *,
    db: AtlasDB,
    bridge: Any,
    permissions: Optional[PermissionPolicy] = None,
) -> None:
    """Mount Orchestrator Chat routes onto *app*.

    Parameters
    ----------
    app           : the FastAPI host
    db            : shared AtlasDB
    bridge        : the _MultiUserBridge (for broadcast_all)
    permissions   : optional PermissionPolicy; constructed from `db` when
                    omitted so test harnesses can skip the wiring.
    """
    policy = permissions or PermissionPolicy(db)

    def _check_access(request: Request, room: str):
        user = _require_user(request)
        if user is None:
            return None, _err(401, "authentication required")
        try:
            ctx = policy.require_room_access(user["id"], room)
        except PermissionDenied as exc:
            return None, _err(403, str(exc))
        return (user, ctx), None

    @app.get("/api/chat/rooms")
    async def api_chat_rooms(request: Request):
        user = _require_user(request)
        if user is None:
            return _err(401, "authentication required")
        rooms = policy.list_accessible_rooms(user["id"])
        # Decorate each room with an unread counter relative to nothing for
        # now — the frontend tracks unread per-client. Server-side delta
        # tracking lands when we wire bridge.last_chat_seen_id into a
        # per-user (not per-session) cursor.
        for r in rooms:
            r["unread"] = 0
        return JSONResponse({"rooms": rooms})

    @app.get("/api/chat/{room}/context")
    async def api_chat_room_context(room: str, request: Request):
        access, err = _check_access(request, room)
        if err is not None:
            return err
        user, ctx = access
        if room == policy.GLOBAL_ROOM:
            bundle = db.summarize_global_room_context(user_id=user["id"])
        else:
            ip = ctx.get("ip") or {}
            bundle = db.summarize_ip_room_context(ip["id"])
            if bundle is None:
                return _err(404, f"IP {room!r} has no context yet")
        return JSONResponse(bundle)

    @app.get("/api/chat/{room}/messages")
    async def api_chat_room_messages(
        room: str,
        request: Request,
        limit: int = _DEFAULT_LIMIT,
        after_id: str = "",
    ):
        access, err = _check_access(request, room)
        if err is not None:
            return err
        _, ctx = access
        ip_id = (ctx.get("ip") or {}).get("id") if ctx.get("ip") else None
        bound = max(1, min(int(limit or _DEFAULT_LIMIT), _MAX_LIMIT))
        rows = db.list_chat_messages(
            ip_id=ip_id,
            limit=bound,
            after_id=after_id or None,
        )
        return JSONResponse({
            "room": room,
            "messages": [_chat_row_to_message(r) for r in rows],
        })

    @app.post("/api/chat/{room}/send")
    async def api_chat_room_send(room: str, request: Request):
        access, err = _check_access(request, room)
        if err is not None:
            return err
        user, ctx = access

        try:
            body = await request.json()
        except Exception:
            return _err(400, "invalid JSON body")
        content = str((body or {}).get("content") or "").strip()
        if not content:
            return _err(400, "content is required")
        if len(content.encode("utf-8")) > _MAX_CONTENT_BYTES:
            return _err(413, f"content exceeds {_MAX_CONTENT_BYTES} bytes")

        ip = ctx.get("ip")
        ip_id = ip["id"] if ip else None
        workspace_id = ip.get("workspace_id") if ip else ""
        display_name = user.get("display_name") or user.get("username") or ""

        record = db.record_chat_message(
            ip_id=ip_id,
            user_id=user["id"],
            content=content,
            display_name=display_name,
            workspace_id=workspace_id or "",
        )
        msg = _chat_row_to_message(record)

        # Cross-session broadcast: rooms span all sessions, so use
        # broadcast_all instead of the active-session emit.
        try:
            bridge.broadcast_all(
                "chat_message",
                room=room,
                id=msg["id"],
                ip_id=msg["ip_id"],
                user_id=msg["user_id"],
                display_name=msg["display_name"],
                content=msg["content"],
                created_at=msg["created_at"],
            )
        except Exception:  # pragma: no cover — bridge is best-effort
            pass

        return JSONResponse({"ok": True, **msg})
