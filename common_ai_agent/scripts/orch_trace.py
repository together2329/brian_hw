#!/usr/bin/env python3
"""Replay one orchestrator run as a step-by-step decision trace.

The orchestrator already persists its observable choices in the control DB:
``orchestrator_steps`` stores tool calls, arguments, results, verdicts, and
retry-budget snapshots.  This CLI joins that data into the one view needed
when debugging autonomy: "what did it read, what did it decide, what did it
dispatch, what woke it up, and why did it stop?"

Usage:
  python3 scripts/orch_trace.py <run_id>
  python3 scripts/orch_trace.py <run_id> --root /path/to/project/root
  python3 scripts/orch_trace.py <run_id> --json
"""
from __future__ import annotations

import argparse
import json
import sqlite3
import sys
import time
from pathlib import Path
from typing import Any


DEFAULT_DB = Path.home() / ".common_ai_agent" / "atlas.db"


def _load_json(value: Any) -> Any:
    if value is None or value == "":
        return None
    if isinstance(value, (dict, list)):
        return value
    try:
        return json.loads(str(value))
    except Exception:
        return None


def _truncate(value: Any, limit: int = 160) -> str:
    text = str(value or "").replace("\n", " ").strip()
    if len(text) <= limit:
        return text
    return text[: max(0, limit - 1)].rstrip() + "…"


def _fmt_ts(value: Any) -> str:
    try:
        ts = float(value)
    except Exception:
        return "?"
    return time.strftime("%H:%M:%S", time.localtime(ts))


def _age(value: Any) -> str:
    try:
        delta = max(0.0, time.time() - float(value))
    except Exception:
        return "?"
    if delta >= 3600:
        return f"{delta / 3600:.1f}h ago"
    if delta >= 60:
        return f"{delta / 60:.0f}m ago"
    return f"{delta:.0f}s ago"


def _connect(path: Path) -> sqlite3.Connection:
    con = sqlite3.connect(path)
    con.row_factory = sqlite3.Row
    return con


def _fetch_run(con: sqlite3.Connection, run_id: str) -> sqlite3.Row | None:
    try:
        return con.execute("SELECT * FROM orchestrator_runs WHERE id = ?", (run_id,)).fetchone()
    except sqlite3.Error:
        return None


def _fetch_steps(con: sqlite3.Connection, run_id: str, limit: int | None) -> list[sqlite3.Row]:
    sql = "SELECT * FROM orchestrator_steps WHERE run_id = ? ORDER BY step_index"
    params: tuple[Any, ...] = (run_id,)
    if limit is not None:
        sql += " LIMIT ?"
        params = (run_id, int(limit))
    return list(con.execute(sql, params))


def _result_from(row: sqlite3.Row) -> dict[str, Any]:
    evidence = _load_json(row["evidence_read_json"]) or {}
    if isinstance(evidence, dict) and isinstance(evidence.get("result"), dict):
        return evidence["result"]
    return {}


def _summary_from(row: sqlite3.Row) -> str:
    evidence = _load_json(row["evidence_read_json"]) or {}
    if isinstance(evidence, dict):
        summary = evidence.get("summary")
        if isinstance(summary, str):
            decoded = _load_json(summary)
            if isinstance(decoded, dict):
                return _truncate(decoded, 220)
            return _truncate(summary, 220)
    return ""


def _args_from(row: sqlite3.Row) -> dict[str, Any]:
    decision = _load_json(row["decision_json"]) or {}
    if isinstance(decision, dict) and isinstance(decision.get("args"), dict):
        return decision["args"]
    return {}


def _dispatch_jobs(result: dict[str, Any]) -> list[str]:
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


def _dispatch_workflow(args: dict[str, Any], result: dict[str, Any]) -> str:
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


def _action_summary(row: sqlite3.Row) -> dict[str, Any]:
    tool = str(row["tool_name"] or "")
    args = _args_from(row)
    result = _result_from(row)
    verdict = str(row["verdict"] or "")
    detail = ""
    why = ""
    extra: dict[str, Any] = {}

    if tool == "dispatch_workflow":
        workflow = _dispatch_workflow(args, result)
        jobs = _dispatch_jobs(result)
        detail = f"dispatch {workflow or '?'}"
        if jobs:
            detail += f" jobs={','.join(jobs)}"
        if args.get("payload"):
            payload = args["payload"]
            if isinstance(payload, dict) and payload.get("state"):
                detail += f" state={payload['state']}"
        reset = result.get("reset_downstream_budgets")
        if isinstance(reset, list) and reset:
            extra["reset_budgets"] = [str(x) for x in reset]
        why = str(args.get("reason") or "")
    elif tool == "classify_failure":
        stage = str(args.get("stage") or "?")
        owner = result.get("owner")
        nxt = result.get("next_workflow")
        conf = result.get("confidence")
        detail = f"classify {stage} -> owner={owner or '?'} next={nxt or '?'}"
        if conf:
            detail += f" confidence={conf}"
        excluded = args.get("excluded_owners")
        if excluded:
            extra["excluded_owners"] = excluded
        why = str(result.get("reason") or args.get("error_text") or "")
    elif tool == "yield_run":
        detail = f"wait -> {verdict or '?'}"
        why = str(args.get("reason") or "")
    elif tool == "read_pipeline_state":
        detail = "read pipeline"
        summary = _read_pipeline_summary(result)
        if summary:
            detail += f" {summary}"
    elif tool == "read_artifact":
        detail = "read artifact " + _read_artifact_summary(args, result)
    else:
        detail = tool or "?"
        why = _summary_from(row)

    budget = _load_json(row["retry_budget_state_json"])
    if budget is not None:
        extra["retry_budget"] = budget
    return {
        "step": row["step_index"],
        "time": _fmt_ts(row["created_at"]),
        "tool": tool,
        "verdict": verdict,
        "detail": _truncate(detail, 260),
        "why": _truncate(why, 260),
        "extra": extra,
    }


def _control_dir(root: Path | None, run_id: str) -> Path | None:
    if root is None:
        return None
    candidate = root / ".session" / "orchestrators-ipc" / run_id
    return candidate if candidate.exists() else None


def _read_response(ctrl: Path | None) -> dict[str, Any] | None:
    if not ctrl:
        return None
    path = ctrl / "response.json"
    if not path.is_file():
        return None
    data = _load_json(path.read_text(errors="replace"))
    return data if isinstance(data, dict) else None


def _wake_tail(ctrl: Path | None, limit: int) -> list[str]:
    if not ctrl or limit <= 0:
        return []
    path = ctrl / "wake.jsonl"
    if not path.is_file():
        return []
    lines = path.read_text(errors="replace").splitlines()[-limit:]
    out = []
    for line in lines:
        doc = _load_json(line)
        if isinstance(doc, dict):
            out.append(_truncate(doc, 220))
        else:
            out.append(_truncate(line, 220))
    return out


def _run_doc(run: sqlite3.Row | None, response: dict[str, Any] | None) -> dict[str, Any]:
    doc: dict[str, Any] = {}
    if run is not None:
        doc.update({key: run[key] for key in run.keys()})
    if response:
        doc["supervisor_status"] = response.get("status")
        doc["supervisor_final_state"] = response.get("final_state")
        doc["supervisor_steps_taken"] = response.get("steps_taken")
        doc["supervisor_duration_ms"] = response.get("duration_ms")
    return doc


def _print_text(run_id: str, run_doc: dict[str, Any], steps: list[dict[str, Any]], wake: list[str]) -> None:
    status = run_doc.get("final_state") or run_doc.get("status") or run_doc.get("supervisor_status") or "?"
    model = run_doc.get("model") or "?"
    print(f"== orchestrator trace {run_id} ==")
    print(f"status={status} model={model} steps={len(steps)}")
    if run_doc.get("started_at"):
        print(f"started={_fmt_ts(run_doc.get('started_at'))} age={_age(run_doc.get('started_at'))}")
    print()

    for item in steps:
        prefix = f"{int(item['step']):03d} {item['time']} {item['tool']:<18}"
        print(f"{prefix} {item['detail']}")
        if item["why"]:
            print(f"      why: {item['why']}")
        extra = item.get("extra") or {}
        if extra.get("excluded_owners"):
            print(f"      excluded: {extra['excluded_owners']}")
        if extra.get("reset_budgets"):
            print(f"      reset budgets: {','.join(extra['reset_budgets'])}")
        if extra.get("retry_budget") is not None:
            print(f"      retry budget: {_truncate(extra['retry_budget'], 220)}")

    if wake:
        print("\n== wake tail ==")
        for line in wake:
            print(f"  {line}")


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("run_id")
    ap.add_argument("--db", default=str(DEFAULT_DB))
    ap.add_argument("--root", help="project root containing .session/orchestrators-ipc/<run_id>")
    ap.add_argument("--limit", type=int, default=None)
    ap.add_argument("--wake", type=int, default=5, help="wake.jsonl tail lines when --root is provided")
    ap.add_argument("--json", action="store_true", help="emit machine-readable trace")
    ns = ap.parse_args()

    db_path = Path(ns.db).expanduser()
    if not db_path.is_file():
        print(f"error: DB not found: {db_path}", file=sys.stderr)
        return 2
    con = _connect(db_path)
    run = _fetch_run(con, ns.run_id)
    steps = [_action_summary(row) for row in _fetch_steps(con, ns.run_id, ns.limit)]
    if run is None and not steps:
        print(f"error: run not found: {ns.run_id}", file=sys.stderr)
        return 1

    root = Path(ns.root).resolve() if ns.root else None
    ctrl = _control_dir(root, ns.run_id)
    response = _read_response(ctrl)
    run_doc = _run_doc(run, response)
    wake = _wake_tail(ctrl, ns.wake)

    if ns.json:
        print(json.dumps({"run_id": ns.run_id, "run": run_doc, "steps": steps, "wake": wake}, indent=2, sort_keys=True))
    else:
        _print_text(ns.run_id, run_doc, steps, wake)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
