"""Deterministic admin dashboard query helper.

This is intentionally DB-backed and non-LLM: admins can ask operational
questions without creating extra token/cost noise in the same dashboard.
"""

from __future__ import annotations

import time
from collections import defaultdict
from typing import Any

from core.atlas_admin_usage import build_admin_usage_payload


def _text(value: Any) -> str:
    return str(value or "").strip()


def _money(value: Any) -> str:
    return f"${float(value or 0):.4f}"


def _fmt_int(value: Any) -> str:
    return f"{int(value or 0):,}"


def _when(ts: Any) -> str:
    if not ts:
        return "-"
    try:
        return time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(float(ts)))
    except Exception:
        return str(ts)


def _add_count(bucket: dict[str, dict[str, Any]], key: str, **values: Any) -> None:
    name = key or "unknown"
    item = bucket.setdefault(name, defaultdict(float))
    item["name"] = name
    for field, value in values.items():
        item[field] += float(value or 0)


def _top(bucket: dict[str, dict[str, Any]], metric: str, limit: int = 8) -> list[dict[str, Any]]:
    return sorted(bucket.values(), key=lambda row: row.get(metric, 0), reverse=True)[:limit]


def _feedback_rows(db) -> list[dict[str, Any]]:
    rows = db._fetchall(
        """
        SELECT f.id, f.user_id, u.username, f.content, f.status,
               f.created_at, f.resolved_at, f.resolved_by, f.notes
          FROM feedback f
          LEFT JOIN users u ON u.id = f.user_id
         ORDER BY f.created_at DESC
         LIMIT 200
        """
    )
    return [dict(row) for row in rows]


def _question_intents(question: str) -> set[str]:
    q = question.lower()
    intents: set[str] = set()
    if any(k in q for k in ("feedback", "피드백")):
        intents.add("feedback")
    if any(k in q for k in ("memory", "메모리", "/memory")):
        intents.add("memory")
    if any(k in q for k in ("input", "history", "chat", "질의", "질문", "입력", "대화")):
        intents.add("inputs")
    if any(k in q for k in ("tool", "툴", "tool call")):
        intents.add("tools")
    if any(k in q for k in ("cost", "token", "usage", "비용", "토큰", "사용량")):
        intents.add("cost")
    if any(k in q for k in ("하루", "daily", "date", "날짜", "일별", "언제", "기간")):
        intents.add("daily")
    if any(k in q for k in ("model", "모델")):
        intents.add("models")
    if any(k in q for k in ("workflow", "워크플로우")):
        intents.add("workflows")
    if any(k in q for k in ("stage", "stages", "단계", "스테이지")):
        intents.add("stages")
    if any(k in q for k in ("ip", "아이피")):
        intents.add("ips")
    if not intents:
        intents = {"summary", "cost", "tools", "models", "workflows", "ips"}
    return intents


def answer_admin_question(db, question: str) -> dict[str, Any]:
    """Answer an admin operational question from atlas.db only."""
    usage = build_admin_usage_payload(db)
    feedback = _feedback_rows(db)
    sessions = db.list_all_sessions()
    intents = _question_intents(question)

    users = usage.get("users", [])
    cost_rows = usage.get("cost_by_context", [])
    date_rows = usage.get("cost_by_date", [])
    tool_rows = usage.get("tool_usage", [])
    memory_rules = usage.get("memory_rules", [])
    input_history = usage.get("input_history", [])
    workflow_stages = usage.get("workflow_stages", [])

    total_cost = sum(float(row.get("total_cost_usd") or 0) for row in users)
    total_tokens = sum(
        int(row.get("tokens_in") or 0)
        + int(row.get("tokens_out") or 0)
        + int(row.get("tokens_reasoning") or 0)
        for row in users
    )
    total_llm_calls = sum(int(row.get("message_count") or 0) for row in users)
    total_tool_calls = sum(int(row.get("calls") or 0) for row in tool_rows)

    lines: list[str] = []
    sections: list[dict[str, Any]] = []

    if "summary" in intents:
        lines.append(
            f"Summary: users={len(users)}, sessions={len(sessions)}, "
            f"LLM calls={_fmt_int(total_llm_calls)}, tools={_fmt_int(total_tool_calls)}, "
            f"tokens={_fmt_int(total_tokens)}, cost={_money(total_cost)}."
        )

    if "daily" in intents or "cost" in intents:
        daily: dict[str, dict[str, Any]] = {}
        for row in date_rows:
            _add_count(
                daily,
                _text(row.get("day")) or "unknown",
                calls=row.get("calls"),
                tokens=row.get("tokens"),
                cost=row.get("cost"),
            )
        top_daily = _top(daily, "cost", 10)
        if top_daily:
            known_days = [row["name"] for row in daily.values() if row.get("name") != "unknown"]
            first = min(known_days) if known_days else "unknown"
            last = max(known_days) if known_days else "unknown"
            lines.append(f"Usage window: {first} to {last}. Total cost {_money(total_cost)}.")
            lines.append("Daily usage: " + "; ".join(
                f"{row['name']} {_money(row.get('cost'))} / {_fmt_int(row.get('tokens'))} tok / {_fmt_int(row.get('calls'))} calls"
                for row in top_daily[:5]
            ))
            sections.append({"title": "Daily Usage", "rows": top_daily})
        elif "daily" in intents:
            lines.append("No daily usage rows yet.")

    if "models" in intents:
        models: dict[str, dict[str, Any]] = {}
        for user in users:
            for model in user.get("models") or []:
                _add_count(
                    models,
                    _text(model.get("model_id")) or "unknown",
                    calls=model.get("calls"),
                    tokens=model.get("tokens"),
                    cost=model.get("cost"),
                )
        rows = _top(models, "calls", 10)
        lines.append("Models: " + ("; ".join(
            f"{row['name']} {_fmt_int(row.get('calls'))} calls / {_money(row.get('cost'))}"
            for row in rows[:5]
        ) if rows else "no model usage yet."))
        sections.append({"title": "Models", "rows": rows})

    if "tools" in intents:
        tools: dict[str, dict[str, Any]] = {}
        for row in tool_rows:
            _add_count(
                tools,
                _text(row.get("tool_name")) or "unknown",
                calls=row.get("calls"),
                failures=row.get("failed_calls"),
                observation_tokens=row.get("observation_tokens_est"),
            )
        rows = _top(tools, "calls", 10)
        lines.append("Tool calls: " + ("; ".join(
            f"{row['name']} {_fmt_int(row.get('calls'))} calls"
            for row in rows[:6]
        ) if rows else "no tool calls yet."))
        sections.append({"title": "Tool Calls", "rows": rows})

    if "workflows" in intents:
        workflows: dict[str, dict[str, Any]] = {}
        for row in cost_rows:
            _add_count(
                workflows,
                _text(row.get("workflow")) or "unknown",
                calls=row.get("calls"),
                tokens=row.get("tokens"),
                cost=row.get("cost"),
            )
        rows = _top(workflows, "cost", 10)
        lines.append("Workflows: " + ("; ".join(
            f"{row['name']} {_money(row.get('cost'))} / {_fmt_int(row.get('calls'))} calls"
            for row in rows[:6]
        ) if rows else "no workflow usage yet."))
        sections.append({"title": "Workflows", "rows": rows})

    if "stages" in intents:
        status_counts: dict[str, int] = defaultdict(int)
        for row in workflow_stages:
            status_counts[_text(row.get("status")) or "unknown"] += 1
        if workflow_stages:
            summary = ", ".join(
                f"{status}={_fmt_int(count)}"
                for status, count in sorted(status_counts.items())
            )
            recent = workflow_stages[:10]
            lines.append(
                f"Stages: {len(workflow_stages)} recent rows loaded"
                + (f" ({summary})." if summary else ".")
            )
            lines.append("Recent stages: " + "; ".join(
                f"{_text(row.get('ip')) or 'unknown'} "
                f"{_text(row.get('workflow')) or 'workflow'}:"
                f"{_text(row.get('stage_name')) or 'stage'} "
                f"{_text(row.get('status')) or 'unknown'}"
                for row in recent[:5]
            ))
        else:
            lines.append("Stages: no workflow stage rows yet.")
            recent = []
        sections.append({"title": "Workflow Stages", "rows": recent})

    if "ips" in intents:
        ips: dict[str, dict[str, Any]] = {}
        for row in cost_rows:
            _add_count(
                ips,
                _text(row.get("ip")) or "unknown",
                calls=row.get("calls"),
                tokens=row.get("tokens"),
                cost=row.get("cost"),
            )
        for session in sessions:
            name = _text(session.get("ip") or session.get("project_id") or session.get("title")) or "unknown"
            _add_count(ips, name, sessions=1)
        rows = _top(ips, "cost", 10)
        lines.append("IPs: " + ("; ".join(
            f"{row['name']} {_money(row.get('cost'))} / {_fmt_int(row.get('sessions'))} sessions"
            for row in rows[:6]
        ) if rows else "no IP/session rows yet."))
        sections.append({"title": "IPs", "rows": rows})

    if "feedback" in intents:
        open_count = sum(1 for row in feedback if row.get("status") != "resolved")
        lines.append(f"Feedback: {open_count} open / {len(feedback)} total.")
        sections.append({"title": "Latest Feedback", "rows": feedback[:10]})

    if "memory" in intents:
        lines.append(f"Memory rules: {len(memory_rules)} total across users.")
        sections.append({"title": "Memory Rules", "rows": memory_rules[:20]})

    if "inputs" in intents:
        lines.append(f"User input history: {len(input_history)} recent rows loaded from DB.")
        sections.append({"title": "Latest User Inputs", "rows": input_history[:20]})

    if not lines:
        lines.append("No matching DB activity yet.")

    return {
        "answer": "\n".join(lines),
        "sections": sections,
        "generated_at": time.time(),
    }
