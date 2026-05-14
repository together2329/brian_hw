"""Admin usage aggregation helpers for ATLAS."""

from __future__ import annotations

import json
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


def _json_list(value: Any) -> list[Any]:
    if value is None or value == "":
        return []
    if isinstance(value, list):
        return value
    if isinstance(value, str):
        try:
            parsed = json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return [value]
        return parsed if isinstance(parsed, list) else [parsed]
    return [value]


def _cost_context(row: dict[str, Any]) -> dict[str, str]:
    ip_name = _text(row.get("ip_name"))
    workspace_name = _text(row.get("workspace_name"))
    workspace_path = _text(row.get("workspace_path"))
    project_id = _text(row.get("project_id"))
    title = _text(row.get("title"))
    directory = _text(row.get("directory"))
    directory_name = _dir_name(directory)
    session_id = _text(row.get("session_id"))

    # Historical rows only have session/project metadata. Treat project_id
    # as the IP/project label, then fall back to the user-facing title.
    ip = ip_name or project_id or title or "unknown"
    workspace = workspace_name or _dir_name(workspace_path) or directory_name or title or project_id or "default"
    session_label = title or _short_id(session_id) or "session"
    return {"ip": ip, "workspace": workspace, "session": session_label}


def build_admin_usage_payload(db) -> dict[str, Any]:
    """Return all admin usage tables consumed by the React admin page."""

    llm_call_count = db._fetchone("SELECT COUNT(*) AS cnt FROM llm_calls")
    use_llm_calls = bool(llm_call_count and int(llm_call_count["cnt"] or 0) > 0)
    if use_llm_calls:
        totals_sql = (
            "SELECT u.id AS user_id, u.username, u.role, u.created_at, u.last_login_at, "
            "       COUNT(DISTINCT s.id) AS session_count, "
            "       COUNT(c.id) AS message_count, "
            "       COALESCE(SUM(c.cost_usd), 0) AS total_cost_usd, "
            "       COALESCE(SUM(c.tokens_input), 0) AS tokens_in, "
            "       COALESCE(SUM(c.tokens_output), 0) AS tokens_out, "
            "       COALESCE(SUM(c.tokens_reasoning), 0) AS tokens_reasoning, "
            "       MAX(c.created_at) AS last_message_at "
            "  FROM users u LEFT JOIN sessions s ON s.user_id = u.id "
            "  LEFT JOIN llm_calls c ON c.session_id = s.id "
            " GROUP BY u.id, u.username, u.role, u.created_at, u.last_login_at "
            " ORDER BY total_cost_usd DESC, message_count DESC"
        )
        models_sql = (
            "SELECT s.user_id, c.model AS model_id, COUNT(*) AS calls, "
            "       COALESCE(SUM(c.cost_usd), 0) AS cost, "
            "       COALESCE(SUM(c.tokens_input + c.tokens_output), 0) AS tokens "
            "  FROM llm_calls c JOIN sessions s ON s.id = c.session_id "
            " WHERE c.model IS NOT NULL AND c.model != '' "
            " GROUP BY s.user_id, c.model ORDER BY s.user_id, calls DESC"
        )
        context_sql = (
            "SELECT s.id AS session_id, s.user_id, u.username, "
            "       s.project_id, s.directory, s.title, "
            "       c.workflow, w.name AS workspace_name, w.local_path AS workspace_path, "
            "       i.ip_name, "
            "       COUNT(c.id) AS calls, "
            "       COALESCE(SUM(c.cost_usd), 0) AS cost, "
            "       COALESCE(SUM(c.tokens_input + c.tokens_output), 0) AS tokens, "
            "       COALESCE(SUM(c.tokens_reasoning), 0) AS tokens_reasoning, "
            "       MAX(c.created_at) AS last_message_at "
            "  FROM llm_calls c JOIN sessions s ON s.id = c.session_id "
            "  LEFT JOIN users u ON u.id = s.user_id "
            "  LEFT JOIN workspaces w ON w.id = c.workspace_id "
            "  LEFT JOIN ip_blocks i ON i.id = c.ip_id "
            " GROUP BY s.id, s.user_id, u.username, s.project_id, s.directory, "
            "          s.title, c.workflow, w.name, w.local_path, i.ip_name "
            " ORDER BY cost DESC, calls DESC"
        )
        date_sql = (
            "SELECT COALESCE(strftime('%Y-%m-%d', c.created_at, 'unixepoch', 'localtime'), 'unknown') AS day, "
            "       s.id AS session_id, s.user_id, u.username, "
            "       s.project_id, s.directory, s.title, "
            "       c.workflow, w.name AS workspace_name, w.local_path AS workspace_path, "
            "       i.ip_name, "
            "       COUNT(c.id) AS calls, "
            "       COALESCE(SUM(c.cost_usd), 0) AS cost, "
            "       COALESCE(SUM(c.tokens_input + c.tokens_output), 0) AS tokens, "
            "       COALESCE(SUM(c.tokens_reasoning), 0) AS tokens_reasoning "
            "  FROM llm_calls c JOIN sessions s ON s.id = c.session_id "
            "  LEFT JOIN users u ON u.id = s.user_id "
            "  LEFT JOIN workspaces w ON w.id = c.workspace_id "
            "  LEFT JOIN ip_blocks i ON i.id = c.ip_id "
            " GROUP BY day, s.id, s.user_id, u.username, s.project_id, s.directory, "
            "          s.title, c.workflow, w.name, w.local_path, i.ip_name "
            " ORDER BY day DESC, cost DESC, calls DESC"
        )
    else:
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
        context_sql = (
            "SELECT s.id AS session_id, s.user_id, u.username, "
            "       s.project_id, s.directory, s.title, "
            "       '' AS workflow, '' AS workspace_name, '' AS workspace_path, '' AS ip_name, "
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
            "       '' AS workflow, '' AS workspace_name, '' AS workspace_path, '' AS ip_name, "
            "       COUNT(m.id) AS calls, "
            "       COALESCE(SUM(m.cost), 0) AS cost, "
            "       COALESCE(SUM(m.tokens_input + m.tokens_output), 0) AS tokens, "
            "       COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning "
            "  FROM messages m JOIN sessions s ON s.id = m.session_id "
            "  LEFT JOIN users u ON u.id = s.user_id "
            " GROUP BY day, s.id, s.user_id, u.username, s.project_id, s.directory, s.title "
            " ORDER BY day DESC, cost DESC, calls DESC"
        )
    tools_sql = (
        "SELECT s.user_id, p.tool_name, COUNT(*) AS calls "
        "  FROM parts p JOIN sessions s ON s.id = p.session_id "
        " WHERE p.tool_name IS NOT NULL AND p.tool_name != '' "
        " GROUP BY s.user_id, p.tool_name ORDER BY s.user_id, calls DESC"
    )

    totals = [dict(r) for r in db._fetchall(totals_sql)]
    models_rows = [dict(r) for r in db._fetchall(models_sql)]
    tools_rows = [dict(r) for r in db._fetchall(tools_sql)]
    context_rows = [dict(r) for r in db._fetchall(context_sql)]
    date_rows = [dict(r) for r in db._fetchall(date_sql)]
    todo_rows = [dict(r) for r in db._fetchall(
        """
        SELECT t.id AS todo_id, t.run_id, r.session_id, s.user_id, u.username,
               r.workflow, w.name AS workspace_name, w.local_path AS workspace_path,
               i.ip_name, t.title AS content, t.detail, t.criteria, t.notes,
               t.status, t.owner_file, t.owner_module, t.source,
               COALESCE(ev.event_count, 0) AS event_count,
               COALESCE(ev.rejected_count, 0) AS rejected_count,
               COALESCE(ev.approved_count, 0) AS approved_count,
               COALESCE(llm.llm_calls, 0) AS llm_calls,
               COALESCE(llm.tokens_input, 0) AS tokens_input,
               COALESCE(llm.tokens_output, 0) AS tokens_output,
               COALESCE(llm.tokens_reasoning, 0) AS tokens_reasoning,
               COALESCE(llm.cost, 0) AS cost,
               COALESCE(llm.latency_ms, 0) AS latency_ms,
               (
                   SELECT e.reason FROM todo_events e
                    WHERE e.todo_id = t.id AND e.event_type = 'rejected'
                    ORDER BY e.created_at DESC LIMIT 1
               ) AS last_rejected_reason,
               (
                   SELECT e.event_type FROM todo_events e
                    WHERE e.todo_id = t.id ORDER BY e.created_at DESC LIMIT 1
               ) AS last_event_type,
               (
                   SELECT e.reason FROM todo_events e
                    WHERE e.todo_id = t.id ORDER BY e.created_at DESC LIMIT 1
               ) AS last_event_reason,
               (
                   SELECT e.created_at FROM todo_events e
                    WHERE e.todo_id = t.id ORDER BY e.created_at DESC LIMIT 1
               ) AS last_event_at
          FROM workflow_todos t
          JOIN workflow_runs r ON r.id = t.run_id
          LEFT JOIN sessions s ON s.id = r.session_id
          LEFT JOIN users u ON u.id = s.user_id
          LEFT JOIN workspaces w ON w.id = r.workspace_id
          LEFT JOIN ip_blocks i ON i.id = r.ip_id
          LEFT JOIN (
              SELECT todo_id,
                     COUNT(*) AS event_count,
                     SUM(CASE WHEN event_type = 'rejected' THEN 1 ELSE 0 END) AS rejected_count,
                     SUM(CASE WHEN event_type = 'approved' THEN 1 ELSE 0 END) AS approved_count
                FROM todo_events
               GROUP BY todo_id
          ) ev ON ev.todo_id = t.id
          LEFT JOIN (
              SELECT todo_id,
                     COUNT(*) AS llm_calls,
                     SUM(tokens_input) AS tokens_input,
                     SUM(tokens_output) AS tokens_output,
                     SUM(tokens_reasoning) AS tokens_reasoning,
                     SUM(cost_usd) AS cost,
                     SUM(COALESCE(latency_ms, 0)) AS latency_ms
                FROM llm_calls
               WHERE todo_id IS NOT NULL AND todo_id != ''
               GROUP BY todo_id
          ) llm ON llm.todo_id = t.id
         ORDER BY cost DESC, rejected_count DESC, last_event_at DESC
        """
    )]
    todo_flow_rows = [dict(r) for r in db._fetchall(
        """
        SELECT e.id AS event_id, e.todo_id, e.event_type, e.reason,
               e.evidence, e.created_at, t.run_id, r.session_id, s.user_id,
               u.username, r.workflow, w.name AS workspace_name,
               w.local_path AS workspace_path, i.ip_name,
               t.title AS content, t.detail, t.criteria, t.status
          FROM todo_events e
          JOIN workflow_todos t ON t.id = e.todo_id
          JOIN workflow_runs r ON r.id = t.run_id
          LEFT JOIN sessions s ON s.id = r.session_id
          LEFT JOIN users u ON u.id = s.user_id
          LEFT JOIN workspaces w ON w.id = r.workspace_id
          LEFT JOIN ip_blocks i ON i.id = r.ip_id
         ORDER BY e.created_at ASC
        """
    )]

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
            "workflow": row.get("workflow") or "",
            "last_message_at": row.get("last_message_at"),
        }

    cost_by_context = [_context_item(row) for row in context_rows]
    cost_by_date = []
    for row in date_rows:
        item = _context_item(row)
        item["day"] = row.get("day") or "unknown"
        cost_by_date.append(item)

    todo_usage = []
    for row in todo_rows:
        context = _cost_context(row)
        tokens_input = int(row.get("tokens_input") or 0)
        tokens_output = int(row.get("tokens_output") or 0)
        todo_usage.append({
            **context,
            "todo_id": row.get("todo_id"),
            "run_id": row.get("run_id"),
            "session_id": row.get("session_id"),
            "user_id": row.get("user_id"),
            "username": row.get("username") or "unknown",
            "workflow": row.get("workflow") or "",
            "content": row.get("content") or "",
            "detail": row.get("detail") or "",
            "criteria": row.get("criteria") or "",
            "notes": _json_list(row.get("notes")),
            "status": row.get("status") or "",
            "source": row.get("source") or "",
            "owner_file": row.get("owner_file") or "",
            "owner_module": row.get("owner_module") or "",
            "event_count": row.get("event_count") or 0,
            "rejected_count": row.get("rejected_count") or 0,
            "approved_count": row.get("approved_count") or 0,
            "last_rejected_reason": row.get("last_rejected_reason") or "",
            "last_event_type": row.get("last_event_type") or "",
            "last_event_reason": row.get("last_event_reason") or "",
            "last_event_at": row.get("last_event_at"),
            "llm_calls": row.get("llm_calls") or 0,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_reasoning": row.get("tokens_reasoning") or 0,
            "tokens": tokens_input + tokens_output,
            "cost": row.get("cost") or 0,
            "latency_ms": row.get("latency_ms") or 0,
        })

    todo_flow = []
    for row in todo_flow_rows:
        context = _cost_context(row)
        todo_flow.append({
            **context,
            "event_id": row.get("event_id"),
            "todo_id": row.get("todo_id"),
            "run_id": row.get("run_id"),
            "session_id": row.get("session_id"),
            "user_id": row.get("user_id"),
            "username": row.get("username") or "unknown",
            "workflow": row.get("workflow") or "",
            "content": row.get("content") or "",
            "detail": row.get("detail") or "",
            "criteria": row.get("criteria") or "",
            "status": row.get("status") or "",
            "event_type": row.get("event_type") or "",
            "reason": row.get("reason") or "",
            "evidence": row.get("evidence") or "",
            "created_at": row.get("created_at"),
        })

    return {
        "users": totals,
        "cost_by_context": cost_by_context,
        "cost_by_date": cost_by_date,
        "todo_usage": todo_usage,
        "todo_flow": todo_flow,
        "generated_at": time.time(),
    }
