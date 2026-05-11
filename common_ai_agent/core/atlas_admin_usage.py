"""Admin usage aggregation helpers for ATLAS."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _short_id(value: Any) -> str:
    text = _text(value)
    return text[:8] if text else ""


def _dir_name(value: Any) -> str:
    text = _text(value)
    if not text:
        return ""
    try:
        return Path(text).name or text
    except Exception:
        return text


def _cost_context(row: dict[str, Any]) -> dict[str, str]:
    project_id = _text(row.get("project_id"))
    title = _text(row.get("title"))
    directory = _text(row.get("directory"))
    directory_name = _dir_name(directory)
    session_id = _text(row.get("session_id"))

    # Historical rows only have session/project metadata. Treat project_id
    # as the IP/project label, then fall back to the user-facing title.
    ip = project_id or title or "unknown"
    workspace = directory_name or title or project_id or "default"
    session_label = title or _short_id(session_id) or "session"
    return {"ip": ip, "workspace": workspace, "session": session_label}


def build_admin_usage_payload(db) -> dict[str, Any]:
    """Return all admin usage tables consumed by the React admin page."""

    totals_sql = (
        "SELECT u.id AS user_id, u.username, u.role, u.created_at, u.last_login_at, "
        "       COUNT(DISTINCT s.id) AS session_count, "
        "       COUNT(m.id) AS message_count, "
        "       COALESCE(SUM(m.cost), 0) AS total_cost_usd, "
        "       COALESCE(SUM(m.tokens_input), 0) AS tokens_in, "
        "       COALESCE(SUM(m.tokens_output), 0) AS tokens_out, "
        "       COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning, "
        "       MAX(m.created_at) AS last_message_at "
        "  FROM users u LEFT JOIN sessions s ON s.user_id = u.id "
        "  LEFT JOIN messages m ON m.session_id = s.id "
        " GROUP BY u.id, u.username, u.role, u.created_at, u.last_login_at "
        " ORDER BY total_cost_usd DESC, message_count DESC"
    )
    models_sql = (
        "SELECT s.user_id, m.model_id, COUNT(*) AS calls, "
        "       COALESCE(SUM(m.cost), 0) AS cost, "
        "       COALESCE(SUM(m.tokens_input + m.tokens_output), 0) AS tokens "
        "  FROM messages m JOIN sessions s ON s.id = m.session_id "
        " WHERE m.model_id IS NOT NULL AND m.model_id != '' "
        " GROUP BY s.user_id, m.model_id ORDER BY s.user_id, calls DESC"
    )
    tools_sql = (
        "SELECT s.user_id, p.tool_name, COUNT(*) AS calls "
        "  FROM parts p JOIN sessions s ON s.id = p.session_id "
        " WHERE p.tool_name IS NOT NULL AND p.tool_name != '' "
        " GROUP BY s.user_id, p.tool_name ORDER BY s.user_id, calls DESC"
    )
    context_sql = (
        "SELECT s.id AS session_id, s.user_id, u.username, "
        "       s.project_id, s.directory, s.title, "
        "       COUNT(m.id) AS calls, "
        "       COALESCE(SUM(m.cost), 0) AS cost, "
        "       COALESCE(SUM(m.tokens_input + m.tokens_output), 0) AS tokens, "
        "       COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning, "
        "       MAX(m.created_at) AS last_message_at "
        "  FROM messages m JOIN sessions s ON s.id = m.session_id "
        "  LEFT JOIN users u ON u.id = s.user_id "
        " GROUP BY s.id, s.user_id, u.username, s.project_id, s.directory, s.title "
        " ORDER BY cost DESC, calls DESC"
    )
    date_sql = (
        "SELECT COALESCE(strftime('%Y-%m-%d', m.created_at, 'unixepoch', 'localtime'), 'unknown') AS day, "
        "       s.id AS session_id, s.user_id, u.username, "
        "       s.project_id, s.directory, s.title, "
        "       COUNT(m.id) AS calls, "
        "       COALESCE(SUM(m.cost), 0) AS cost, "
        "       COALESCE(SUM(m.tokens_input + m.tokens_output), 0) AS tokens, "
        "       COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning "
        "  FROM messages m JOIN sessions s ON s.id = m.session_id "
        "  LEFT JOIN users u ON u.id = s.user_id "
        " GROUP BY day, s.id, s.user_id, u.username, s.project_id, s.directory, s.title "
        " ORDER BY day DESC, cost DESC, calls DESC"
    )

    totals = [dict(r) for r in db._fetchall(totals_sql)]
    models_rows = [dict(r) for r in db._fetchall(models_sql)]
    tools_rows = [dict(r) for r in db._fetchall(tools_sql)]
    context_rows = [dict(r) for r in db._fetchall(context_sql)]
    date_rows = [dict(r) for r in db._fetchall(date_sql)]

    models_by_user: dict[str, list[dict[str, Any]]] = {}
    for row in models_rows:
        models_by_user.setdefault(row["user_id"], []).append({
            "model_id": row["model_id"],
            "calls": row["calls"],
            "cost": row["cost"],
            "tokens": row["tokens"],
        })

    tools_by_user: dict[str, list[dict[str, Any]]] = {}
    for row in tools_rows:
        tools_by_user.setdefault(row["user_id"], []).append({
            "tool_name": row["tool_name"],
            "calls": row["calls"],
        })

    for user in totals:
        user["models"] = models_by_user.get(user["user_id"], [])
        user["tools"] = tools_by_user.get(user["user_id"], [])[:10]

    def _context_item(row: dict[str, Any]) -> dict[str, Any]:
        context = _cost_context(row)
        return {
            **context,
            "session_id": row.get("session_id"),
            "user_id": row.get("user_id"),
            "username": row.get("username") or "unknown",
            "calls": row.get("calls") or 0,
            "tokens": row.get("tokens") or 0,
            "tokens_reasoning": row.get("tokens_reasoning") or 0,
            "cost": row.get("cost") or 0,
            "last_message_at": row.get("last_message_at"),
        }

    cost_by_context = [_context_item(row) for row in context_rows]
    cost_by_date = []
    for row in date_rows:
        item = _context_item(row)
        item["day"] = row.get("day") or "unknown"
        cost_by_date.append(item)

    return {
        "users": totals,
        "cost_by_context": cost_by_context,
        "cost_by_date": cost_by_date,
        "generated_at": time.time(),
    }
