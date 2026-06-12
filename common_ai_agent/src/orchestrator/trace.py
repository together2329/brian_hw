"""Shared orchestrator run trace normalization.

This module is the single source for replaying ``orchestrator_steps`` into the
operator-facing decision trace.  The CLI, Atlas API/UI, and terminal-state guard
all consume the same normalized shape so a run cannot look healthy in one
surface and failed in another.
"""

from __future__ import annotations

import json
import sqlite3
import time
from pathlib import Path
from typing import Any, Iterable, Mapping


DEFAULT_DB = Path.home() / ".common_ai_agent" / "atlas.db"


def load_json(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return None


def truncate(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "..."


def fmt_ts(value: Any) -> str:
    try:
        ts = float(value)
    except Exception:
        return "?"
    return time.strftime("%H:%M:%S", time.localtime(ts))


def age(value: Any) -> str:
    try:
        delta = max(0.0, time.time() - float(value))
    except Exception:
        return "?"
    if delta >= 3600:
        return f"{delta / 3600:.1f}h ago"
    if delta >= 60:
        return f"{delta / 60:.0f}m ago"
    return f"{delta:.0f}s ago"


def connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _keys(row: Any) -> set[str]:
    if row is None:
        return set()
    if isinstance(row, Mapping):
        return set(str(k) for k in row.keys())
    keys = getattr(row, "keys", None)
    if callable(keys):
        try:
            return set(str(k) for k in keys())
        except Exception:
            return set()
    return set()


def _get(row: Any, key: str, default: Any = None) -> Any:
    if row is None:
        return default
    if isinstance(row, Mapping):
        return row.get(key, default)
    if key not in _keys(row):
        return default
    try:
        return row[key]
    except Exception:
        return default


def _row_to_dict(row: Any) -> dict[str, Any]:
    if row is None:
        return {}
    if isinstance(row, Mapping):
        return dict(row)
    return {key: _get(row, key) for key in _keys(row)}


def fetch_run(con: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
    try:
        return con.execute("SELECT * FROM orchestrator_runs WHERE id = ?", (run_id,)).fetchone()
    except sqlite3.Error:
        return None


def fetch_latest_run_id(
    con: sqlite3.Connection,
    *,
    workspace_id: str,
    ip_id: str,
    user_ids: Iterable[str] = (),
) -> str | None:
    users = [str(u).strip() for u in user_ids if str(u).strip()]
    where = ["workspace_id = ?", "ip_id = ?"]
    params: list[Any] = [workspace_id, ip_id]
    if users:
        where.append("user_id IN (" + ",".join("?" for _ in users) + ")")
        params.extend(users)
    sql = (
        "SELECT id FROM orchestrator_runs WHERE "
        + " AND ".join(where)
        + " ORDER BY COALESCE(updated_at, started_at, 0) DESC, started_at DESC LIMIT 1"
    )
    try:
        row = con.execute(sql, tuple(params)).fetchone()
    except sqlite3.Error:
        return None
    return str(row["id"]) if row and _get(row, "id") else None


def fetch_steps(
    con: sqlite3.Connection,
    run_id: str,
    limit: int | None,
) -> list[sqlite3.Row]:
    sql = "SELECT * FROM orchestrator_steps WHERE run_id = ? ORDER BY step_index"
    params: tuple[Any, ...] = (run_id,)
    if limit is not None:
        sql += " LIMIT ?"
        params = (run_id, int(limit))
    return list(con.execute(sql, params))


def result_from(row: Any) -> dict[str, Any]:
    evidence = load_json(_get(row, "evidence_read_json")) or {}
    if isinstance(evidence, dict) and isinstance(evidence.get("result"), dict):
        return evidence["result"]
    return {}


def summary_from(row: Any) -> str:
    evidence = load_json(_get(row, "evidence_read_json")) or {}
    if isinstance(evidence, dict):
        summary = evidence.get("summary")
        if isinstance(summary, str):
            decoded = load_json(summary)
            if isinstance(decoded, dict):
                return truncate(decoded, 220)
            return truncate(summary, 220)
    return ""


def args_from(row: Any) -> dict[str, Any]:
    decision = load_json(_get(row, "decision_json")) or {}
    if isinstance(decision, dict) and isinstance(decision.get("args"), dict):
        return decision["args"]
    return {}


def dispatch_jobs(result: dict[str, Any]) -> list[str]:
    jobs = result.get("jobs")
    if isinstance(jobs, list):
        out = []
        for item in jobs:
            if isinstance(item, dict) and item.get("job_id"):
                out.append(str(item["job_id"]))
        return out
    ids = result.get("job_ids")
    if isinstance(ids, list):
        return [str(x) for x in ids]
    return []


def dispatch_workflow(args: dict[str, Any], result: dict[str, Any]) -> str:
    if args.get("workflow"):
        return str(args["workflow"])
    stages = args.get("stages")
    if isinstance(stages, list) and stages:
        return ",".join(str(x) for x in stages)
    result_stages = result.get("stages")
    if isinstance(result_stages, list) and result_stages:
        workflows = []
        for item in result_stages:
            if isinstance(item, dict):
                workflows.append(str(item.get("workflow") or item.get("id") or ""))
        return ",".join(x for x in workflows if x)
    return ""


def _read_pipeline_summary(result: dict[str, Any]) -> str:
    failed = result.get("failed")
    running = result.get("running")
    passed = result.get("passed")
    chunks = []
    if isinstance(failed, dict):
        chunks.append("failed=" + ",".join(sorted(failed)) if failed else "failed=0")
    if isinstance(running, list):
        chunks.append("running=" + ",".join(str(x) for x in running) if running else "running=0")
    if isinstance(passed, list):
        chunks.append(f"passed={len(passed)}")
    return " ".join(chunks)


def _read_artifact_summary(args: dict[str, Any], result: dict[str, Any]) -> str:
    stage = str(args.get("stage") or "?")
    files = result.get("files")
    missing = result.get("missing")
    bits = [f"stage={stage}"]
    if isinstance(files, list):
        bits.append("files=" + ",".join(str(x) for x in files))
    if isinstance(missing, list) and missing:
        bits.append("missing=" + ",".join(str(x) for x in missing))
    previews = result.get("previews")
    if isinstance(previews, list) and previews:
        statuses = []
        for item in previews:
            if isinstance(item, dict) and item.get("status"):
                statuses.append(str(item["status"]))
        if statuses:
            bits.append("status=" + ",".join(statuses))
    return " ".join(bits)


def action_summary(row: Any) -> dict[str, Any]:
    tool = str(_get(row, "tool_name") or "")
    args = args_from(row)
    result = result_from(row)
    verdict = str(_get(row, "verdict") or "")
    detail = ""
    why = ""
    extra: dict[str, Any] = {}
    error = ""
    failed = verdict == "tool_failed" or result.get("ok") is False
    no_job_dispatch = False

    if tool == "dispatch_workflow":
        workflow = dispatch_workflow(args, result)
        jobs = dispatch_jobs(result)
        detail = f"dispatch {workflow or '?'}"
        if jobs:
            detail += f" jobs={','.join(jobs)}"
        if args.get("payload"):
            payload = args["payload"]
            if isinstance(payload, dict) and payload.get("state"):
                detail += f" state={payload['state']}"
        no_job_dispatch = bool(workflow and workflow != "__final__" and not jobs)
        if no_job_dispatch:
            detail += " [NO JOB]"
            extra["no_job_dispatch"] = True
        if failed:
            detail += " [FAILED]"
        reset = result.get("reset_downstream_budgets")
        if isinstance(reset, list) and reset:
            extra["reset_budgets"] = [str(x) for x in reset]
        why = str(args.get("reason") or "")
        error = str(result.get("error") or result.get("message") or "")
    elif tool == "classify_failure":
        stage = str(args.get("stage") or "?")
        owner = result.get("owner")
        nxt = result.get("next_workflow")
        conf = result.get("confidence")
        detail = f"classify {stage} -> owner={owner or '?'} next={nxt or '?'}"
        if conf:
            detail += f" confidence={conf}"
        if failed:
            detail += " [FAILED]"
        excluded = args.get("excluded_owners")
        if excluded:
            extra["excluded_owners"] = excluded
        why = str(result.get("reason") or args.get("error_text") or "")
        error = str(result.get("error") or "")
    elif tool == "yield_run":
        detail = f"wait -> {verdict or '?'}"
        why = str(args.get("reason") or "")
        if failed:
            detail += " [FAILED]"
    elif tool == "read_pipeline_state":
        detail = "read pipeline"
        summary = _read_pipeline_summary(result)
        if summary:
            detail += f" {summary}"
        if failed:
            detail += " [FAILED]"
        error = str(result.get("error") or result.get("message") or "")
    elif tool == "read_artifact":
        detail = "read artifact " + _read_artifact_summary(args, result)
        if failed:
            detail += " [FAILED]"
        error = str(result.get("error") or result.get("message") or "")
    else:
        detail = tool or "?"
        why = summary_from(row)
        if failed:
            detail += " [FAILED]"
        error = str(result.get("error") or result.get("message") or "")

    budget = load_json(_get(row, "retry_budget_state_json"))
    if budget is not None:
        extra["retry_budget"] = budget
    if result.get("ok") is not None:
        extra["ok"] = result.get("ok")
    if error:
        extra["error"] = error
    status = "failed" if failed else ("waiting" if tool == "yield_run" else "ok")
    return {
        "step": _get(row, "step_index"),
        "created_at": _get(row, "created_at"),
        "time": fmt_ts(_get(row, "created_at")),
        "tool": tool,
        "verdict": verdict,
        "status": status,
        "detail": truncate(detail, 260),
        "why": truncate(why, 260),
        "error": truncate(error, 260),
        "workflow": dispatch_workflow(args, result) if tool == "dispatch_workflow" else "",
        "jobs": dispatch_jobs(result) if tool == "dispatch_workflow" else [],
        "extra": extra,
    }


def control_dir(root: Path | None, run_id: str) -> Path | None:
    if root is None:
        return None
    candidate = root / ".session" / "orchestrators-ipc" / run_id
    return candidate if candidate.exists() else None


def read_response(ctrl: Path | None) -> dict[str, Any] | None:
    if not ctrl:
        return None
    path = ctrl / "response.json"
    if not path.is_file():
        return None
    data = load_json(path.read_text(errors="replace"))
    return data if isinstance(data, dict) else None


def wake_tail(ctrl: Path | None, limit: int) -> list[str]:
    if not ctrl or limit <= 0:
        return []
    path = ctrl / "wake.jsonl"
    if not path.is_file():
        return []
    lines = path.read_text(errors="replace").splitlines()[-limit:]
    out = []
    for line in lines:
        doc = load_json(line)
        if isinstance(doc, dict):
            out.append(truncate(json.dumps(doc, sort_keys=True), 220))
        else:
            out.append(truncate(line, 220))
    return out


def terminal_blocker_from_steps(raw_steps: Iterable[Any]) -> dict[str, Any] | None:
    summaries = [action_summary(row) for row in raw_steps]
    if not summaries:
        return None
    latest = summaries[-1]
    tool = str(latest.get("tool") or "")
    workflow = str(latest.get("workflow") or "")
    if tool == "dispatch_workflow" and workflow == "__final__" and latest.get("status") == "ok":
        return None
    if latest.get("status") == "failed":
        return {
            "kind": "tool_failed",
            "step": latest.get("step"),
            "tool": tool,
            "workflow": workflow,
            "reason": latest.get("error") or latest.get("verdict") or latest.get("detail"),
        }
    if tool == "dispatch_workflow" and workflow and workflow != "__final__" and not latest.get("jobs"):
        return {
            "kind": "dispatch_no_job",
            "step": latest.get("step"),
            "tool": tool,
            "workflow": workflow,
            "reason": "dispatch_workflow returned no worker job",
        }
    return None


def effective_terminal_state(run_doc: Mapping[str, Any], raw_steps: Iterable[Any]) -> dict[str, Any]:
    recorded_status = str(run_doc.get("status") or run_doc.get("supervisor_status") or "")
    recorded_final = str(run_doc.get("final_state") or run_doc.get("supervisor_final_state") or "")
    blocker = terminal_blocker_from_steps(raw_steps)
    if recorded_status == "completed" and blocker:
        return {
            "effective_status": "blocked",
            "effective_final_state": blocker["kind"],
            "terminal_anomaly": (
                f"run recorded completed after {blocker['kind']} at step "
                f"{blocker.get('step')}: {blocker.get('reason')}"
            ),
        }
    return {
        "effective_status": recorded_status or recorded_final or "?",
        "effective_final_state": recorded_final or recorded_status or "?",
        "terminal_anomaly": "",
    }


def run_doc(run: Any, response: dict[str, Any] | None, raw_steps: Iterable[Any]) -> dict[str, Any]:
    doc = _row_to_dict(run)
    if response:
        doc["supervisor_status"] = response.get("status")
        doc["supervisor_final_state"] = response.get("final_state")
        doc["supervisor_steps_taken"] = response.get("steps_taken")
        doc["supervisor_duration_ms"] = response.get("duration_ms")
    doc.update(effective_terminal_state(doc, raw_steps))
    return doc


def build_trace_from_records(
    run_id: str,
    *,
    run: Any,
    raw_steps: Iterable[Any],
    project_root: Path | None = None,
    wake_limit: int = 5,
) -> dict[str, Any]:
    step_rows = list(raw_steps)
    ctrl = control_dir(project_root, run_id)
    response = read_response(ctrl)
    doc = run_doc(run, response, step_rows)
    steps = [action_summary(row) for row in step_rows]
    return {
        "run_id": run_id,
        "run": doc,
        "steps": steps,
        "wake": wake_tail(ctrl, wake_limit),
    }


def build_trace(
    run_id: str,
    *,
    db_path: Path = DEFAULT_DB,
    project_root: Path | None = None,
    limit: int | None = None,
    wake_limit: int = 5,
) -> dict[str, Any]:
    con = connect(db_path)
    try:
        run = fetch_run(con, run_id)
        steps = fetch_steps(con, run_id, limit)
    finally:
        con.close()
    return build_trace_from_records(
        run_id,
        run=run,
        raw_steps=steps,
        project_root=project_root,
        wake_limit=wake_limit,
    )


def build_latest_trace_for_scope(
    *,
    db_path: Path,
    workspace_id: str,
    ip_id: str,
    user_ids: Iterable[str] = (),
    project_root: Path | None = None,
    limit: int | None = 200,
    wake_limit: int = 5,
) -> dict[str, Any] | None:
    con = connect(db_path)
    try:
        run_id = fetch_latest_run_id(
            con,
            workspace_id=workspace_id,
            ip_id=ip_id,
            user_ids=user_ids,
        )
        if not run_id:
            return None
        run = fetch_run(con, run_id)
        steps = fetch_steps(con, run_id, limit)
    finally:
        con.close()
    return build_trace_from_records(
        run_id,
        run=run,
        raw_steps=steps,
        project_root=project_root,
        wake_limit=wake_limit,
    )


def format_trace(trace: Mapping[str, Any]) -> str:
    run_id = str(trace.get("run_id") or "?")
    run = trace.get("run") if isinstance(trace.get("run"), Mapping) else {}
    steps = trace.get("steps") if isinstance(trace.get("steps"), list) else []
    wake = trace.get("wake") if isinstance(trace.get("wake"), list) else []
    status = (
        run.get("effective_final_state")
        or run.get("final_state")
        or run.get("status")
        or run.get("supervisor_status")
        or "?"
    )
    model = run.get("model") or "?"
    lines = [
        f"== orchestrator trace {run_id} ==",
        f"status={status} model={model} steps={len(steps)}",
    ]
    if run.get("terminal_anomaly"):
        lines.append(f"terminal anomaly: {run['terminal_anomaly']}")
    if run.get("started_at"):
        lines.append(f"started={fmt_ts(run.get('started_at'))} age={age(run.get('started_at'))}")
    lines.append("")

    for item in steps:
        try:
            step = int(item.get("step"))
        except Exception:
            step = -1
        prefix = f"{step:03d} {item.get('time') or '?'} {str(item.get('tool') or ''):<18}"
        lines.append(f"{prefix} {item.get('detail') or ''}")
        if item.get("why"):
            lines.append(f"      why: {item['why']}")
        if item.get("error"):
            lines.append(f"      error: {item['error']}")
        extra = item.get("extra") if isinstance(item.get("extra"), Mapping) else {}
        if extra.get("excluded_owners"):
            lines.append(f"      excluded: {extra['excluded_owners']}")
        if extra.get("reset_budgets"):
            lines.append(f"      reset budgets: {','.join(extra['reset_budgets'])}")
        if extra.get("retry_budget") is not None:
            lines.append(f"      retry budget: {truncate(extra['retry_budget'], 220)}")

    if wake:
        lines.append("")
        lines.append("== wake tail ==")
        for line in wake:
            lines.append(f"  {line}")
    return "\n".join(lines) + "\n"
