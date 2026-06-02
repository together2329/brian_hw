"""User-scoped dashboard aggregation helpers for ATLAS."""

from __future__ import annotations

import json
from typing import Any


def _text(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _json_any(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, str):
        try:
            return json.loads(value)
        except (json.JSONDecodeError, TypeError):
            return value
    return value


def _session_parts(session_id: str) -> tuple[str, str, str]:
    parts = [p for p in _text(session_id).split("/") if p]
    owner = parts[0] if len(parts) > 0 else ""
    ip = parts[1] if len(parts) > 1 else ""
    workflow = parts[2] if len(parts) > 2 else ""
    return owner, ip, workflow


def _session_summary(session: dict[str, Any]) -> dict[str, Any]:
    summary = _json_any(session.get("summary"))
    return summary if isinstance(summary, dict) else {}


def _session_ip(session: dict[str, Any]) -> str:
    _, namespace_ip, _ = _session_parts(_text(session.get("id")))
    summary = _session_summary(session)
    return _text(summary.get("ip")) or _text(session.get("project_id")) or namespace_ip or _text(session.get("title")) or "unknown"


def _session_workflow(session: dict[str, Any], latest_run: dict[str, Any] | None = None) -> str:
    _, _, namespace_workflow = _session_parts(_text(session.get("id")))
    summary = _session_summary(session)
    return (
        _text((latest_run or {}).get("workflow"))
        or _text(summary.get("workflow"))
        or namespace_workflow
        or "default"
    )


def _context_ip(row: dict[str, Any]) -> str:
    return (
        _text(row.get("ip_name"))
        or _text(row.get("project_id"))
        or _session_parts(_text(row.get("session_id")))[1]
        or _text(row.get("title"))
        or "unknown"
    )


def _context_workspace(row: dict[str, Any]) -> str:
    return _text(row.get("workspace_name")) or _text(row.get("project_id")) or "default"


def _safe_user(user: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": _text(user.get("id")),
        "username": _text(user.get("username")),
        "display_name": _text(user.get("display_name")),
        "email": _text(user.get("email")),
        "role": _text(user.get("role")) or "user",
    }


def _runtime_mode_active() -> bool:
    """True when the per-session runtime split is active (session mode)."""
    try:
        from core.runtime_rollup import runtime_mode_active

        return runtime_mode_active()
    except Exception:
        return False


def _usage_context_rows_runtime(db: Any, user_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    """Usage rows + totals from control-DB rollups (runtime mode, no fanout).

    Mirrors the shape of :func:`_usage_context_rows` so the rest of the
    dashboard builder is unchanged. TOTALS and per-session/context cost come from
    ``runtime_usage_rollups`` so a NORMAL request never opens a runtime file
    (plan §2.10 / R8).
    """
    rollups = db.list_runtime_usage_rollups(user_id=user_id)
    contexts: list[dict[str, Any]] = []
    totals = {
        "llm_calls": 0,
        "total_cost_usd": 0.0,
        "tokens_in": 0,
        "tokens_out": 0,
        "tokens_reasoning": 0,
        "last_activity": None,
    }
    max_activity = 0.0
    for row in rollups:
        tokens = _int(row.get("tokens_input")) + _int(row.get("tokens_output"))
        item = {
            "session_id": row.get("session_id"),
            "project_id": "",
            "title": "",
            "workflow": _text(row.get("workflow")),
            "workspace_name": "",
            "ip_name": _text(row.get("ip")),
            "calls": _int(row.get("llm_calls")),
            "cost": _num(row.get("cost_usd")),
            "tokens": tokens,
            "tokens_reasoning": _int(row.get("tokens_reasoning")),
            "last_activity": row.get("updated_at"),
            "rollup_status": _text(row.get("status")) or "ok",
            "rollup_lag_s": _num(row.get("rollup_lag_s")),
        }
        item["ip"] = _context_ip(item)
        item["workspace"] = _context_workspace(item)
        item["workflow"] = _text(item.get("workflow")) or _session_parts(_text(item.get("session_id")))[2] or "default"
        contexts.append(item)
        totals["llm_calls"] += _int(row.get("llm_calls"))
        totals["total_cost_usd"] += _num(row.get("cost_usd"))
        totals["tokens_in"] += _int(row.get("tokens_input"))
        totals["tokens_out"] += _int(row.get("tokens_output"))
        totals["tokens_reasoning"] += _int(row.get("tokens_reasoning"))
        max_activity = max(max_activity, _num(row.get("updated_at")))
    if max_activity > 0:
        totals["last_activity"] = max_activity
    contexts.sort(key=lambda r: (_num(r.get("cost")), _int(r.get("calls"))), reverse=True)
    return contexts, totals


def _usage_context_rows(db: Any, user_id: str) -> tuple[list[dict[str, Any]], dict[str, Any]]:
    if _runtime_mode_active():
        return _usage_context_rows_runtime(db, user_id)
    llm_count = db._fetchone(
        """
        SELECT COUNT(*) AS cnt
          FROM llm_calls c
          JOIN sessions s ON s.id = c.session_id
         WHERE s.user_id = ?
        """,
        (user_id,),
    )
    use_llm = bool(llm_count and _int(llm_count["cnt"]) > 0)
    if use_llm:
        totals_row = db._fetchone(
            """
            SELECT COUNT(c.id) AS calls,
                   COALESCE(SUM(c.cost_usd), 0) AS cost,
                   COALESCE(SUM(c.tokens_input), 0) AS tokens_in,
                   COALESCE(SUM(c.tokens_output), 0) AS tokens_out,
                   COALESCE(SUM(c.tokens_reasoning), 0) AS tokens_reasoning,
                   MAX(c.created_at) AS last_activity
              FROM llm_calls c
              JOIN sessions s ON s.id = c.session_id
             WHERE s.user_id = ?
            """,
            (user_id,),
        )
        rows = db._fetchall(
            """
            SELECT s.id AS session_id, s.project_id, s.title,
                   c.workflow, w.name AS workspace_name, i.ip_name,
                   COUNT(c.id) AS calls,
                   COALESCE(SUM(c.cost_usd), 0) AS cost,
                   COALESCE(SUM(c.tokens_input + c.tokens_output), 0) AS tokens,
                   COALESCE(SUM(c.tokens_reasoning), 0) AS tokens_reasoning,
                   MAX(c.created_at) AS last_activity
              FROM llm_calls c
              JOIN sessions s ON s.id = c.session_id
              LEFT JOIN workspaces w ON w.id = c.workspace_id
              LEFT JOIN ip_blocks i ON i.id = c.ip_id
             WHERE s.user_id = ?
             GROUP BY s.id, s.project_id, s.title, c.workflow, w.name, i.ip_name
             ORDER BY cost DESC, calls DESC
            """,
            (user_id,),
        )
    else:
        totals_row = db._fetchone(
            """
            SELECT COUNT(m.id) AS calls,
                   COALESCE(SUM(m.cost), 0) AS cost,
                   COALESCE(SUM(m.tokens_input), 0) AS tokens_in,
                   COALESCE(SUM(m.tokens_output), 0) AS tokens_out,
                   COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning,
                   MAX(m.created_at) AS last_activity
              FROM messages m
              JOIN sessions s ON s.id = m.session_id
             WHERE s.user_id = ?
            """,
            (user_id,),
        )
        rows = db._fetchall(
            """
            SELECT s.id AS session_id, s.project_id, s.title,
                   '' AS workflow, '' AS workspace_name, '' AS ip_name,
                   COUNT(m.id) AS calls,
                   COALESCE(SUM(m.cost), 0) AS cost,
                   COALESCE(SUM(m.tokens_input + m.tokens_output), 0) AS tokens,
                   COALESCE(SUM(m.tokens_reasoning), 0) AS tokens_reasoning,
                   MAX(m.created_at) AS last_activity
              FROM messages m
              JOIN sessions s ON s.id = m.session_id
             WHERE s.user_id = ?
             GROUP BY s.id, s.project_id, s.title
             ORDER BY cost DESC, calls DESC
            """,
            (user_id,),
        )
    totals = dict(totals_row or {})
    contexts: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["ip"] = _context_ip(item)
        item["workspace"] = _context_workspace(item)
        item["workflow"] = _text(item.get("workflow")) or _session_parts(_text(item.get("session_id")))[2] or "default"
        contexts.append(item)
    return contexts, {
        "llm_calls": _int(totals.get("calls")),
        "total_cost_usd": _num(totals.get("cost")),
        "tokens_in": _int(totals.get("tokens_in")),
        "tokens_out": _int(totals.get("tokens_out")),
        "tokens_reasoning": _int(totals.get("tokens_reasoning")),
        "last_activity": totals.get("last_activity"),
    }


def _workflow_runs_runtime(db: Any, user_id: str) -> list[dict[str, Any]]:
    """Workflow runs in runtime (session) mode: control rows, NO llm join.

    The per-run usage aggregate is unjoinable from control (llm_calls is sharded
    to runtime DBs), so calls/cost/tokens are 0 and each row carries an explicit
    ``runtime_usage_unavailable`` flag so the UI/agent does not read 0 as fact.
    """
    rows = db._fetchall(
        """
        SELECT r.id AS run_id, r.session_id, r.workflow, r.mode,
               r.status, r.started_at, r.ended_at, r.duration_ms,
               r.error_summary, r.created_at, r.updated_at,
               s.project_id, s.title, w.name AS workspace_name, i.ip_name,
               0 AS calls, 0 AS cost, 0 AS tokens
          FROM workflow_runs r
          JOIN sessions s ON s.id = r.session_id
          LEFT JOIN workspaces w ON w.id = r.workspace_id
          LEFT JOIN ip_blocks i ON i.id = r.ip_id
         WHERE s.user_id = ?
         ORDER BY r.started_at DESC, r.created_at DESC
        """,
        (user_id,),
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["ip"] = _context_ip(item)
        item["workspace"] = _context_workspace(item)
        item["runtime_usage_unavailable"] = True
        result.append(item)
    return result


def _workflow_runs(db: Any, user_id: str) -> list[dict[str, Any]]:
    # Read-path routing (plan §2.10 / R7): workflow_runs rows stay in CONTROL,
    # but the per-run llm_calls aggregate (calls/cost/tokens) MOVES to per-session
    # runtime DBs in session mode. A control-side join there silently reports 0 —
    # a false ground truth. In session mode we skip the llm join and tag rows with
    # an explicit ``runtime_usage_unavailable`` flag so 0 is never read as fact.
    if _runtime_mode_active():
        return _workflow_runs_runtime(db, user_id)
    rows = db._fetchall(
        """
        SELECT r.id AS run_id, r.session_id, r.workflow, r.mode,
               r.status, r.started_at, r.ended_at, r.duration_ms,
               r.error_summary, r.created_at, r.updated_at,
               s.project_id, s.title, w.name AS workspace_name, i.ip_name,
               COALESCE(llm.calls, 0) AS calls,
               COALESCE(llm.cost, 0) AS cost,
               COALESCE(llm.tokens, 0) AS tokens
          FROM workflow_runs r
          JOIN sessions s ON s.id = r.session_id
          LEFT JOIN workspaces w ON w.id = r.workspace_id
          LEFT JOIN ip_blocks i ON i.id = r.ip_id
          LEFT JOIN (
              SELECT run_id, COUNT(*) AS calls,
                     COALESCE(SUM(cost_usd), 0) AS cost,
                     COALESCE(SUM(tokens_input + tokens_output), 0) AS tokens
                FROM llm_calls
               WHERE run_id IS NOT NULL AND run_id != ''
               GROUP BY run_id
          ) llm ON llm.run_id = r.id
         WHERE s.user_id = ?
         ORDER BY r.started_at DESC, r.created_at DESC
        """,
        (user_id,),
    )
    result: list[dict[str, Any]] = []
    for row in rows:
        item = dict(row)
        item["ip"] = _context_ip(item)
        item["workspace"] = _context_workspace(item)
        result.append(item)
    return result


def _aggregate_ip_workload(sessions: list[dict[str, Any]], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for session in sessions:
        ip = _session_ip(session)
        item = grouped.setdefault(ip, {
            "ip": ip,
            "sessions": 0,
            "calls": 0,
            "cost": 0.0,
            "tokens": 0,
            "workflows": set(),
            "last_activity": 0,
        })
        item["sessions"] += 1
        item["workflows"].add(_session_workflow(session))
        item["last_activity"] = max(_num(item["last_activity"]), _num(session.get("updated_at")))
    for row in contexts:
        ip = _text(row.get("ip")) or "unknown"
        item = grouped.setdefault(ip, {
            "ip": ip,
            "sessions": 0,
            "calls": 0,
            "cost": 0.0,
            "tokens": 0,
            "workflows": set(),
            "last_activity": 0,
        })
        item["calls"] += _int(row.get("calls"))
        item["cost"] += _num(row.get("cost"))
        item["tokens"] += _int(row.get("tokens"))
        item["workflows"].add(_text(row.get("workflow")) or "default")
        item["last_activity"] = max(_num(item["last_activity"]), _num(row.get("last_activity")))
    rows = []
    for item in grouped.values():
        rows.append({
            **item,
            "workflows": sorted(w for w in item["workflows"] if w),
        })
    rows.sort(key=lambda r: (_num(r.get("cost")), _int(r.get("calls")), _num(r.get("last_activity"))), reverse=True)
    return rows


def _ip_inventory(
    db: Any,
    user_id: str,
    sessions: list[dict[str, Any]],
    contexts: list[dict[str, Any]],
    runs: list[dict[str, Any]],
) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}

    def ensure(ip_name: str) -> dict[str, Any]:
        ip = _text(ip_name) or "unknown"
        return grouped.setdefault(ip, {
            "ip": ip,
            "ip_ids": set(),
            "workspace_ids": set(),
            "workspaces": set(),
            "workspace_paths": set(),
            "permissions": set(),
            "ip_type": "",
            "status": "",
            "ssot_path": "",
            "sessions": 0,
            "runs": 0,
            "running": 0,
            "failed": 0,
            "calls": 0,
            "cost": 0.0,
            "tokens": 0,
            "workflows": set(),
            "last_workflow": "",
            "last_status": "",
            "last_activity": 0,
        })

    try:
        ip_rows = db.list_accessible_ip_blocks(user_id, "view")
    except Exception:
        ip_rows = []

    for row in ip_rows:
        item = ensure(row.get("ip_name"))
        if row.get("id"):
            item["ip_ids"].add(_text(row.get("id")))
        if row.get("workspace_id"):
            item["workspace_ids"].add(_text(row.get("workspace_id")))
        if row.get("workspace_name"):
            item["workspaces"].add(_text(row.get("workspace_name")))
        if row.get("workspace_path"):
            item["workspace_paths"].add(_text(row.get("workspace_path")))
        if row.get("permission"):
            item["permissions"].add(_text(row.get("permission")))
        if not item["ip_type"] and row.get("ip_type"):
            item["ip_type"] = _text(row.get("ip_type"))
        if not item["ssot_path"] and row.get("ssot_path"):
            item["ssot_path"] = _text(row.get("ssot_path"))
        if _num(row.get("updated_at")) >= _num(item["last_activity"]):
            item["status"] = _text(row.get("status")) or item["status"]
            item["last_activity"] = _num(row.get("updated_at"))

    for session in sessions:
        ip = _session_ip(session)
        item = ensure(ip)
        item["sessions"] += 1
        workflow = _session_workflow(session)
        if workflow:
            item["workflows"].add(workflow)
        if _num(session.get("updated_at")) >= _num(item["last_activity"]):
            item["last_activity"] = _num(session.get("updated_at"))
            item["last_workflow"] = workflow
            item["last_status"] = _text(session.get("status"))

    for row in contexts:
        item = ensure(row.get("ip"))
        item["calls"] += _int(row.get("calls"))
        item["cost"] += _num(row.get("cost"))
        item["tokens"] += _int(row.get("tokens"))
        workflow = _text(row.get("workflow"))
        if workflow:
            item["workflows"].add(workflow)
        if _num(row.get("last_activity")) >= _num(item["last_activity"]):
            item["last_activity"] = _num(row.get("last_activity"))
            if workflow:
                item["last_workflow"] = workflow

    for run in runs:
        item = ensure(run.get("ip"))
        status = _text(run.get("status")).lower()
        workflow = _text(run.get("workflow"))
        item["runs"] += 1
        if workflow:
            item["workflows"].add(workflow)
        if status in {"running", "in_progress", "queued"}:
            item["running"] += 1
        elif status in {"failed", "fail", "error", "blocked", "cancelled", "canceled"}:
            item["failed"] += 1
        last_at = _num(run.get("started_at") or run.get("created_at") or run.get("updated_at"))
        if last_at >= _num(item["last_activity"]):
            item["last_activity"] = last_at
            if workflow:
                item["last_workflow"] = workflow
            item["last_status"] = status

    rows: list[dict[str, Any]] = []
    for item in grouped.values():
        rows.append({
            "ip": item["ip"],
            "ip_type": item["ip_type"],
            "status": item["status"] or item["last_status"] or "active",
            "ssot_path": item["ssot_path"],
            "permission": ", ".join(sorted(item["permissions"])) or "",
            "workspaces": sorted(w for w in item["workspaces"] if w),
            "workspace_paths": sorted(w for w in item["workspace_paths"] if w),
            "workspace_count": len(item["workspace_ids"]),
            "ip_row_count": len(item["ip_ids"]),
            "sessions": item["sessions"],
            "runs": item["runs"],
            "running": item["running"],
            "failed": item["failed"],
            "calls": item["calls"],
            "cost": item["cost"],
            "tokens": item["tokens"],
            "workflows": sorted(w for w in item["workflows"] if w),
            "last_workflow": item["last_workflow"],
            "last_status": item["last_status"],
            "last_activity": item["last_activity"],
        })
    rows.sort(
        key=lambda r: (
            _num(r.get("last_activity")),
            _num(r.get("cost")),
            _int(r.get("runs")) + _int(r.get("sessions")) + _int(r.get("calls")),
            _text(r.get("ip")),
        ),
        reverse=True,
    )
    return rows


def _aggregate_workflows(runs: list[dict[str, Any]], contexts: list[dict[str, Any]]) -> list[dict[str, Any]]:
    grouped: dict[str, dict[str, Any]] = {}
    for run in runs:
        workflow = _text(run.get("workflow")) or "default"
        item = grouped.setdefault(workflow, {
            "workflow": workflow,
            "runs": 0,
            "running": 0,
            "passed": 0,
            "failed": 0,
            "idle": 0,
            "calls": 0,
            "cost": 0.0,
            "tokens": 0,
            "last_run_at": 0,
            "last_status": "",
        })
        status = _text(run.get("status")).lower()
        item["runs"] += 1
        if status in {"running", "in_progress", "queued"}:
            item["running"] += 1
        elif status in {"passed", "pass", "ok", "completed", "done", "success"}:
            item["passed"] += 1
        elif status in {"failed", "fail", "error", "blocked", "cancelled", "canceled"}:
            item["failed"] += 1
        else:
            item["idle"] += 1
        item["last_run_at"] = max(_num(item["last_run_at"]), _num(run.get("started_at") or run.get("created_at")))
        if _num(run.get("started_at") or run.get("created_at")) >= _num(item.get("last_run_at")):
            item["last_status"] = status
    for row in contexts:
        workflow = _text(row.get("workflow")) or "default"
        item = grouped.setdefault(workflow, {
            "workflow": workflow,
            "runs": 0,
            "running": 0,
            "passed": 0,
            "failed": 0,
            "idle": 0,
            "calls": 0,
            "cost": 0.0,
            "tokens": 0,
            "last_run_at": 0,
            "last_status": "",
        })
        item["calls"] += _int(row.get("calls"))
        item["cost"] += _num(row.get("cost"))
        item["tokens"] += _int(row.get("tokens"))
    rows = list(grouped.values())
    rows.sort(key=lambda r: (_num(r.get("last_run_at")), _num(r.get("cost")), _int(r.get("calls"))), reverse=True)
    return rows


def _needs_attention(db: Any, user_id: str, runs: list[dict[str, Any]]) -> list[dict[str, Any]]:
    items: list[dict[str, Any]] = []
    for run in runs:
        status = _text(run.get("status")).lower()
        if status in {"failed", "fail", "error", "blocked", "cancelled", "canceled"}:
            items.append({
                "kind": "workflow",
                "severity": "error",
                "title": f"{_text(run.get('workflow')) or 'workflow'} {status}",
                "ip": _text(run.get("ip")),
                "workflow": _text(run.get("workflow")),
                "session_id": _text(run.get("session_id")),
                "updated_at": run.get("ended_at") or run.get("updated_at") or run.get("started_at"),
                "detail": _text(run.get("error_summary")),
            })
    todo_rows = db._fetchall(
        """
        SELECT t.id AS todo_id, t.title, t.status, t.updated_at,
               r.session_id, r.workflow, s.project_id, i.ip_name,
               (
                   SELECT e.reason FROM todo_events e
                    WHERE e.todo_id = t.id AND e.event_type = 'rejected'
                    ORDER BY e.created_at DESC LIMIT 1
               ) AS reason
          FROM workflow_todos t
          JOIN workflow_runs r ON r.id = t.run_id
          JOIN sessions s ON s.id = r.session_id
          LEFT JOIN ip_blocks i ON i.id = r.ip_id
         WHERE s.user_id = ?
           AND (LOWER(COALESCE(t.status, '')) = 'rejected'
                OR EXISTS (
                    SELECT 1 FROM todo_events e
                     WHERE e.todo_id = t.id AND e.event_type = 'rejected'
                ))
         ORDER BY t.updated_at DESC
         LIMIT 10
        """,
        (user_id,),
    )
    for row in todo_rows:
        item = dict(row)
        items.append({
            "kind": "todo",
            "severity": "warning",
            "title": _text(item.get("title")) or _text(item.get("todo_id")),
            "ip": _context_ip(item),
            "workflow": _text(item.get("workflow")),
            "session_id": _text(item.get("session_id")),
            "updated_at": item.get("updated_at"),
            "detail": _text(item.get("reason")),
        })
    trace_rows = db._fetchall(
        """
        SELECT t.event_type, t.session_id, t.workflow, t.payload, t.created_at,
               s.project_id
          FROM trace_events t
          JOIN sessions s ON s.id = t.session_id
         WHERE s.user_id = ?
           AND t.event_type IN ('ask_user.opened', 'ask_user.answered')
         ORDER BY t.created_at DESC
         LIMIT 200
        """,
        (user_id,),
    )
    opened: dict[str, dict[str, Any]] = {}
    answered: set[str] = set()
    for row in trace_rows:
        item = dict(row)
        payload = _json_any(item.get("payload"))
        flow_id = ""
        if isinstance(payload, dict):
            flow_id = _text(payload.get("flow_id") or payload.get("id"))
        flow_id = flow_id or f"{item.get('session_id')}:{item.get('created_at')}"
        if item.get("event_type") == "ask_user.answered":
            answered.add(flow_id)
        elif flow_id not in opened:
            opened[flow_id] = item
    for flow_id, item in opened.items():
        if flow_id in answered:
            continue
        items.append({
            "kind": "ask_user",
            "severity": "warning",
            "title": "User input pending",
            "ip": _context_ip(item),
            "workflow": _text(item.get("workflow")),
            "session_id": _text(item.get("session_id")),
            "updated_at": item.get("created_at"),
            "detail": flow_id,
        })
    items.sort(key=lambda r: _num(r.get("updated_at")), reverse=True)
    return items[:12]


def build_user_dashboard_payload(
    db: Any,
    user: dict[str, Any],
    *,
    run_mode: str = "",
    exec_mode: str = "",
) -> dict[str, Any]:
    """Return a dashboard payload scoped to one authenticated user."""

    user_id = _text(user.get("id")) or "default"
    sessions = [db._row_to_dict(row, "sessions") for row in db._fetchall(
        "SELECT * FROM sessions WHERE user_id = ? ORDER BY updated_at DESC",
        (user_id,),
    )]
    active_sessions = [s for s in sessions if _text(s.get("status")).lower() == "active"]
    runs = _workflow_runs(db, user_id)
    latest_run_by_session: dict[str, dict[str, Any]] = {}
    for run in runs:
        latest_run_by_session.setdefault(_text(run.get("session_id")), run)
    contexts, totals = _usage_context_rows(db, user_id)

    recent_sessions = []
    for session in sessions[:12]:
        latest = latest_run_by_session.get(_text(session.get("id")))
        recent_sessions.append({
            "id": _text(session.get("id")),
            "title": _text(session.get("title")),
            "ip": _session_ip(session),
            "workflow": _session_workflow(session, latest),
            "status": _text(session.get("status")),
            "workflow_status": _text((latest or {}).get("status")),
            "updated_at": session.get("updated_at"),
            "created_at": session.get("created_at"),
        })
    current_session = active_sessions[0] if active_sessions else (sessions[0] if sessions else {})
    current_latest = latest_run_by_session.get(_text(current_session.get("id")))
    ip_workload = _aggregate_ip_workload(sessions, contexts)
    ip_inventory = _ip_inventory(db, user_id, sessions, contexts, runs)
    workflow_progress = _aggregate_workflows(runs, contexts)
    needs_attention = _needs_attention(db, user_id, runs)

    ip_count = len({_text(row.get("ip")) for row in ip_inventory if _text(row.get("ip"))})
    workflow_count = len({_text(row.get("workflow")) for row in workflow_progress if _text(row.get("workflow"))})
    return {
        "user": _safe_user(user),
        "current": {
            "session_id": _text(current_session.get("id")),
            "title": _text(current_session.get("title")),
            "ip": _session_ip(current_session) if current_session else "",
            "workflow": _session_workflow(current_session, current_latest) if current_session else "",
            "session_status": _text(current_session.get("status")),
            "workflow_status": _text((current_latest or {}).get("status")),
            "updated_at": current_session.get("updated_at"),
            "run_mode": _text(run_mode),
            "exec_mode": _text(exec_mode),
        },
        "metrics": {
            "session_count": len(sessions),
            "active_sessions": len(active_sessions),
            "ip_count": ip_count,
            "workflow_count": workflow_count,
            "llm_calls": totals["llm_calls"],
            "tokens_in": totals["tokens_in"],
            "tokens_out": totals["tokens_out"],
            "tokens_reasoning": totals["tokens_reasoning"],
            "total_cost_usd": totals["total_cost_usd"],
            "needs_attention": len(needs_attention),
            "failed_runs": sum(1 for r in runs if _text(r.get("status")).lower() in {"failed", "fail", "error", "blocked"}),
        },
        "ip_inventory": ip_inventory[:24],
        "ip_workload": ip_workload[:12],
        "workflow_progress": workflow_progress[:12],
        "recent_sessions": recent_sessions,
        "recent_runs": runs[:12],
        "needs_attention": needs_attention,
        "cost_by_context": contexts[:20],
    }
