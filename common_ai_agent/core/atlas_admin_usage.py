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


def _json_any(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


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
    trace_rows = [dict(r) for r in db._fetchall(
        """
        SELECT e.id AS event_id, e.event_type, e.session_id, e.workspace_id,
               e.ip_id, e.workflow, e.run_id, e.stage_id, e.todo_id,
               e.message_id, e.llm_call_id, e.artifact_id, e.actor_user_id,
               e.correlation_id, e.causation_id, e.idempotency_key,
               e.payload, e.created_at,
               COALESCE(us.username, ua.username) AS username,
               s.project_id, s.directory, s.title,
               w.name AS workspace_name, w.local_path AS workspace_path,
               i.ip_name
          FROM trace_events e
          LEFT JOIN sessions s ON s.id = e.session_id
          LEFT JOIN users us ON us.id = s.user_id
          LEFT JOIN users ua ON ua.id = e.actor_user_id
          LEFT JOIN workspaces w ON w.id = e.workspace_id
          LEFT JOIN ip_blocks i ON i.id = e.ip_id
         ORDER BY e.created_at DESC
         LIMIT 500
        """
    )]
    tool_rows = [dict(r) for r in db._fetchall(
        """
        WITH tool_parts AS (
            SELECT p.*,
                   r.workflow AS run_workflow,
                   r.workspace_id AS run_workspace_id,
                   r.ip_id AS run_ip_id
              FROM parts p
              LEFT JOIN workflow_runs r ON r.id = (
                   SELECT rr.id
                     FROM workflow_runs rr
                    WHERE rr.session_id = p.session_id
                      AND (rr.started_at IS NULL OR p.created_at >= rr.started_at)
                      AND (rr.ended_at IS NULL OR p.created_at <= rr.ended_at)
                    ORDER BY rr.started_at DESC, rr.created_at DESC
                    LIMIT 1
              )
             WHERE p.tool_name IS NOT NULL AND p.tool_name != ''
        )
        SELECT tp.session_id, s.user_id, u.username,
               s.project_id, s.directory, s.title,
               tp.run_workflow AS workflow,
               w.name AS workspace_name, w.local_path AS workspace_path,
               i.ip_name, tp.tool_name,
               COUNT(*) AS calls,
               SUM(CASE
                   WHEN tp.tool_status IN ('error', 'failed')
                        OR (tp.tool_error IS NOT NULL AND tp.tool_error != '')
                   THEN 1 ELSE 0 END) AS failed_calls,
               SUM(LENGTH(COALESCE(tp.tool_output, ''))) AS observation_chars,
               SUM(CAST((LENGTH(COALESCE(tp.tool_output, '')) + 3) / 4 AS INTEGER))
                   AS observation_tokens_est,
               SUM(LENGTH(COALESCE(tp.tool_input, ''))) AS input_chars,
               SUM(CASE
                   WHEN tp.start_time IS NOT NULL AND tp.end_time IS NOT NULL
                   THEN MAX(0, (tp.end_time - tp.start_time) * 1000)
                   ELSE 0 END) AS latency_ms,
               SUM(CASE
                   WHEN tp.start_time IS NOT NULL AND tp.end_time IS NOT NULL
                   THEN 1 ELSE 0 END) AS timed_calls,
               MAX(tp.created_at) AS last_tool_at
          FROM tool_parts tp
          LEFT JOIN sessions s ON s.id = tp.session_id
          LEFT JOIN users u ON u.id = s.user_id
          LEFT JOIN workspaces w ON w.id = tp.run_workspace_id
          LEFT JOIN ip_blocks i ON i.id = tp.run_ip_id
         GROUP BY tp.session_id, s.user_id, u.username, s.project_id,
                  s.directory, s.title, tp.run_workflow, w.name,
                  w.local_path, i.ip_name, tp.tool_name
         ORDER BY calls DESC, observation_tokens_est DESC, last_tool_at DESC
        """
    )]
    intervention_rows = [dict(r) for r in db._fetchall(
        """
        WITH raw_interventions AS (
            SELECT m.id AS intervention_id, m.session_id, '' AS workflow,
                   '' AS workspace_id, '' AS ip_id, '' AS actor_user_id,
                   'message.user' AS source, m.created_at
              FROM messages m
             WHERE m.role = 'user'
            UNION ALL
            SELECT e.id AS intervention_id, e.session_id, e.workflow,
                   e.workspace_id, e.ip_id, e.actor_user_id,
                   e.event_type AS source, e.created_at
              FROM trace_events e
             WHERE e.event_type IN (
                   'ask_user.answered',
                   'chat_message',
                   'ssot_qa.answered',
                   'ssot_qa.approved',
                   'human.intervention'
             )
        ),
        scoped AS (
            SELECT ri.*,
                   COALESCE(NULLIF(ri.workflow, ''), r.workflow, '') AS resolved_workflow,
                   COALESCE(NULLIF(ri.workspace_id, ''), r.workspace_id, '') AS resolved_workspace_id,
                   COALESCE(NULLIF(ri.ip_id, ''), r.ip_id, '') AS resolved_ip_id
              FROM raw_interventions ri
              LEFT JOIN workflow_runs r ON r.id = (
                   SELECT rr.id
                     FROM workflow_runs rr
                    WHERE rr.session_id = ri.session_id
                      AND (rr.started_at IS NULL OR ri.created_at >= rr.started_at)
                      AND (rr.ended_at IS NULL OR ri.created_at <= rr.ended_at)
                    ORDER BY rr.started_at DESC, rr.created_at DESC
                    LIMIT 1
              )
        )
        SELECT sc.session_id, s.user_id, COALESCE(ua.username, u.username) AS username,
               s.project_id, s.directory, s.title,
               sc.resolved_workflow AS workflow,
               w.name AS workspace_name, w.local_path AS workspace_path,
               i.ip_name,
               COUNT(*) AS intervention_count,
               SUM(CASE WHEN sc.source = 'message.user' THEN 1 ELSE 0 END) AS user_messages,
               SUM(CASE WHEN sc.source = 'chat_message' THEN 1 ELSE 0 END) AS chat_messages,
               SUM(CASE WHEN sc.source = 'ask_user.answered' THEN 1 ELSE 0 END)
                   AS ask_user_answers,
               SUM(CASE WHEN sc.source LIKE 'ssot_qa.%' THEN 1 ELSE 0 END) AS ssot_qa_answers,
               SUM(CASE WHEN sc.source = 'human.intervention' THEN 1 ELSE 0 END)
                   AS explicit_human_events,
               MIN(sc.created_at) AS first_intervention_at,
               MAX(sc.created_at) AS last_intervention_at
          FROM scoped sc
          LEFT JOIN sessions s ON s.id = sc.session_id
          LEFT JOIN users u ON u.id = s.user_id
          LEFT JOIN users ua ON ua.id = sc.actor_user_id
          LEFT JOIN workspaces w ON w.id = sc.resolved_workspace_id
          LEFT JOIN ip_blocks i ON i.id = sc.resolved_ip_id
         GROUP BY sc.session_id, s.user_id, COALESCE(ua.username, u.username),
                  s.project_id, s.directory, s.title, sc.resolved_workflow,
                  w.name, w.local_path, i.ip_name
         ORDER BY intervention_count DESC, last_intervention_at DESC
        """
    )]
    rtl_history_rows = db.list_rtl_run_history()
    artifact_version_rows = db.list_artifact_versions()
    run_artifact_set_rows = db.list_run_artifact_version_sets()

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

    trace_events = []
    for row in trace_rows:
        context = _cost_context(row)
        trace_events.append({
            **context,
            "event_id": row.get("event_id"),
            "event_type": row.get("event_type") or "",
            "session_id": row.get("session_id") or "",
            "workspace_id": row.get("workspace_id") or "",
            "ip_id": row.get("ip_id") or "",
            "workflow": row.get("workflow") or "",
            "run_id": row.get("run_id") or "",
            "stage_id": row.get("stage_id") or "",
            "todo_id": row.get("todo_id") or "",
            "message_id": row.get("message_id") or "",
            "llm_call_id": row.get("llm_call_id") or "",
            "artifact_id": row.get("artifact_id") or "",
            "actor_user_id": row.get("actor_user_id") or "",
            "username": row.get("username") or "unknown",
            "correlation_id": row.get("correlation_id") or "",
            "causation_id": row.get("causation_id") or "",
            "idempotency_key": row.get("idempotency_key") or "",
            "payload": _json_any(row.get("payload")),
            "created_at": row.get("created_at"),
        })

    tool_usage = []
    for row in tool_rows:
        context = _cost_context(row)
        timed_calls = int(row.get("timed_calls") or 0)
        latency_ms = float(row.get("latency_ms") or 0)
        tool_usage.append({
            **context,
            "session_id": row.get("session_id") or "",
            "user_id": row.get("user_id") or "",
            "username": row.get("username") or "unknown",
            "workflow": row.get("workflow") or "",
            "tool_name": row.get("tool_name") or "",
            "calls": row.get("calls") or 0,
            "failed_calls": row.get("failed_calls") or 0,
            "observation_chars": row.get("observation_chars") or 0,
            "observation_tokens_est": row.get("observation_tokens_est") or 0,
            "input_chars": row.get("input_chars") or 0,
            "latency_ms": latency_ms,
            "avg_latency_ms": (latency_ms / timed_calls) if timed_calls else None,
            "last_tool_at": row.get("last_tool_at"),
        })

    interventions = []
    for row in intervention_rows:
        context = _cost_context(row)
        interventions.append({
            **context,
            "session_id": row.get("session_id") or "",
            "user_id": row.get("user_id") or "",
            "username": row.get("username") or "unknown",
            "workflow": row.get("workflow") or "",
            "intervention_count": row.get("intervention_count") or 0,
            "user_messages": row.get("user_messages") or 0,
            "chat_messages": row.get("chat_messages") or 0,
            "ask_user_answers": row.get("ask_user_answers") or 0,
            "ssot_qa_answers": row.get("ssot_qa_answers") or 0,
            "explicit_human_events": row.get("explicit_human_events") or 0,
            "first_intervention_at": row.get("first_intervention_at"),
            "last_intervention_at": row.get("last_intervention_at"),
        })

    rtl_run_history = []
    for row in rtl_history_rows:
        context = _cost_context(row)
        tokens_input = int(row.get("tokens_input") or 0)
        tokens_output = int(row.get("tokens_output") or 0)
        rtl_run_history.append({
            **context,
            "run_id": row.get("run_id") or "",
            "session_id": row.get("session_id") or "",
            "workspace_id": row.get("workspace_id") or "",
            "ip_id": row.get("ip_id") or "",
            "rtl_version_id": row.get("rtl_version_id") or "",
            "rtl_version": row.get("rtl_version") or "",
            "rtl_label": row.get("rtl_label") or "",
            "rtl_sha256_tree": row.get("rtl_sha256_tree") or "",
            "rtl_git_commit": row.get("rtl_git_commit") or "",
            "rtl_git_tag": row.get("rtl_git_tag") or "",
            "rtl_filelist_path": row.get("rtl_filelist_path") or "",
            "rtl_top_module": row.get("rtl_top_module") or "",
            "workflow": row.get("workflow") or "",
            "mode": row.get("mode") or "",
            "model_profile": row.get("model_profile") or "",
            "reasoning_effort": row.get("reasoning_effort") or "",
            "status": row.get("status") or "",
            "duration_ms": row.get("duration_ms") or 0,
            "error_summary": row.get("error_summary") or "",
            "started_at": row.get("started_at"),
            "ended_at": row.get("ended_at"),
            "llm_calls": row.get("llm_calls") or 0,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_reasoning": row.get("tokens_reasoning") or 0,
            "tokens": tokens_input + tokens_output,
            "cost": row.get("cost") or 0,
        })

    artifact_versions = []
    for row in artifact_version_rows:
        context = _cost_context(row)
        artifact_versions.append({
            **context,
            "artifact_version_id": row.get("id") or "",
            "workspace_id": row.get("workspace_id") or "",
            "ip_id": row.get("ip_id") or "",
            "artifact_type": row.get("artifact_type") or "",
            "version": row.get("version") or "",
            "label": row.get("label") or "",
            "root_path": row.get("root_path") or "",
            "primary_path": row.get("primary_path") or "",
            "sha256_tree": row.get("sha256_tree") or "",
            "git_commit": row.get("git_commit") or "",
            "git_tag": row.get("git_tag") or "",
            "status": row.get("status") or "",
            "source_run_id": row.get("source_run_id") or "",
            "source_stage_id": row.get("source_stage_id") or "",
            "created_at": row.get("created_at"),
        })

    run_artifact_sets = []
    for row in run_artifact_set_rows:
        context = _cost_context(row)
        grouped = {}
        for artifact_type, versions in (row.get("artifact_versions") or {}).items():
            grouped[artifact_type] = [{
                "artifact_version_id": item.get("artifact_version_id") or "",
                "version": item.get("version") or "",
                "role": item.get("role") or "",
                "required": bool(item.get("required", True)),
                "sha256_tree": item.get("sha256_tree") or "",
                "git_commit": item.get("git_commit") or "",
                "git_tag": item.get("git_tag") or "",
                "root_path": item.get("root_path") or "",
                "primary_path": item.get("primary_path") or "",
                "status": item.get("artifact_status") or "",
            } for item in versions]
        tokens_input = int(row.get("tokens_input") or 0)
        tokens_output = int(row.get("tokens_output") or 0)
        run_artifact_sets.append({
            **context,
            "run_id": row.get("run_id") or "",
            "session_id": row.get("session_id") or "",
            "workspace_id": row.get("workspace_id") or "",
            "ip_id": row.get("ip_id") or "",
            "workflow": row.get("workflow") or "",
            "mode": row.get("mode") or "",
            "model_profile": row.get("model_profile") or "",
            "reasoning_effort": row.get("reasoning_effort") or "",
            "status": row.get("status") or "",
            "duration_ms": row.get("duration_ms") or 0,
            "error_summary": row.get("error_summary") or "",
            "started_at": row.get("started_at"),
            "ended_at": row.get("ended_at"),
            "llm_calls": row.get("llm_calls") or 0,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_reasoning": row.get("tokens_reasoning") or 0,
            "tokens": tokens_input + tokens_output,
            "cost": row.get("cost") or 0,
            "artifact_versions": grouped,
        })

    return {
        "users": totals,
        "cost_by_context": cost_by_context,
        "cost_by_date": cost_by_date,
        "todo_usage": todo_usage,
        "todo_flow": todo_flow,
        "trace_events": trace_events,
        "tool_usage": tool_usage,
        "interventions": interventions,
        "rtl_run_history": rtl_run_history,
        "artifact_versions": artifact_versions,
        "run_artifact_sets": run_artifact_sets,
        "generated_at": time.time(),
    }
