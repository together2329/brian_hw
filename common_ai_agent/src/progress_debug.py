from __future__ import annotations

import argparse
import json
import os
import time
from datetime import datetime, timezone
from pathlib import Path
from typing import Any


def _read_json(path: Path) -> dict[str, Any]:
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except Exception:
        return {}
    return data if isinstance(data, dict) else {}


def _read_jsonl(path: Path, *, limit: int = 500) -> list[dict[str, Any]]:
    if not path.is_file():
        return []
    rows: list[dict[str, Any]] = []
    try:
        lines = path.read_text(encoding="utf-8", errors="replace").splitlines()
    except Exception:
        return []
    for line in lines[-limit:]:
        line = line.strip()
        if not line:
            continue
        try:
            item = json.loads(line)
        except Exception:
            continue
        if isinstance(item, dict):
            rows.append(item)
    return rows


def _parse_utc(value: Any) -> float | None:
    if not isinstance(value, str) or not value:
        return None
    try:
        text = value.replace("Z", "+00:00")
        return datetime.fromisoformat(text).timestamp()
    except Exception:
        return None


def _age_sec(ts: Any, now: float) -> float | None:
    parsed = _parse_utc(ts)
    if parsed is None:
        return None
    return round(max(0.0, now - parsed), 3)


def _artifact_status(ip_dir: Path, ip: str) -> dict[str, dict[str, Any]]:
    candidates = {
        "headless_run": ip_dir / "logs" / "headless_run.json",
        "heartbeat": ip_dir / "logs" / "heartbeat.json",
        "progress_log": ip_dir / "logs" / "run_progress.jsonl",
        "ssot_yaml": ip_dir / "yaml" / f"{ip}.ssot.yaml",
        "ssot_llm_log": ip_dir / "logs" / "llm" / "ssot-gen.json",
        "rtl_todo_plan": ip_dir / "rtl" / "rtl_todo_plan.json",
        "rtl_compile": ip_dir / "rtl" / "rtl_compile.json",
        "lint_report": ip_dir / "lint" / "dut_lint.json",
        "sim_results": ip_dir / "sim" / "results.xml",
        "coverage_report": ip_dir / "cov" / "coverage.json",
    }
    out: dict[str, dict[str, Any]] = {}
    for name, path in candidates.items():
        exists = path.exists()
        item: dict[str, Any] = {
            "exists": exists,
            "path": str(path),
        }
        if exists:
            try:
                stat = path.stat()
                item["size_bytes"] = stat.st_size
                item["mtime"] = datetime.fromtimestamp(stat.st_mtime, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")
            except Exception:
                pass
        out[name] = item
    return out


def _active_llm_call(events: list[dict[str, Any]], now: float) -> dict[str, Any]:
    active: dict[str, Any] | None = None
    started = 0
    finished = 0
    last_finished: dict[str, Any] | None = None
    for event in events:
        name = event.get("event")
        if name == "llm_call_start":
            started += 1
            active = dict(event)
        elif name == "llm_call_end":
            finished += 1
            last_finished = dict(event)
            if active and (
                not event.get("stage")
                or event.get("stage") == active.get("stage")
                or event.get("log_stage") == active.get("log_stage")
            ):
                active = None

    result: dict[str, Any] = {
        "started": started,
        "finished": finished,
        "open": max(0, started - finished),
        "active": False,
        "last_finished": last_finished,
    }
    if active:
        elapsed = _age_sec(active.get("ts"), now)
        result.update(
            {
                "active": True,
                "stage": active.get("stage"),
                "log_stage": active.get("log_stage"),
                "model": active.get("model"),
                "started_at": active.get("ts"),
                "elapsed_sec": elapsed,
                "prompt_chars": active.get("prompt_chars"),
                "system_prompt_chars": active.get("system_prompt_chars"),
            }
        )
    return result


def summarize_headless_progress(
    root: str | Path,
    ip: str,
    *,
    now: float | None = None,
    stale_after_sec: float | None = None,
    tail: int = 20,
) -> dict[str, Any]:
    """Return a compact, UI-safe diagnosis for a headless workflow run.

    This intentionally reads only the stable on-disk progress contract:
    logs/heartbeat.json, logs/run_progress.jsonl, logs/llm_call_trace.jsonl,
    logs/headless_run.json, and well-known artifact paths.
    """

    now = time.time() if now is None else now
    stale_after_sec = (
        float(os.getenv("ATLAS_PROGRESS_STALE_AFTER_SEC", "180"))
        if stale_after_sec is None
        else float(stale_after_sec)
    )
    root_path = Path(root).resolve()
    ip_dir = root_path / ip
    logs_dir = ip_dir / "logs"
    heartbeat_path = logs_dir / "heartbeat.json"
    progress_path = logs_dir / "run_progress.jsonl"
    headless_run_path = logs_dir / "headless_run.json"
    llm_trace_path = logs_dir / "llm_call_trace.jsonl"

    heartbeat = _read_json(heartbeat_path)
    headless_run = _read_json(headless_run_path)
    events = _read_jsonl(progress_path, limit=1000)
    llm_trace = _read_jsonl(llm_trace_path, limit=200)
    last_event = events[-1] if events else {}
    active_llm = _active_llm_call(events, now)
    artifacts = _artifact_status(ip_dir, ip)

    heartbeat_age = _age_sec(heartbeat.get("ts"), now)
    last_event_age = _age_sec(last_event.get("ts"), now)
    finished = bool(headless_run.get("status")) or (heartbeat.get("state") == "done")
    current_stage = (
        heartbeat.get("current_stage")
        or heartbeat.get("stage")
        or last_event.get("stage")
        or ""
    )
    phase = heartbeat.get("phase") or ""

    severity = "info"
    diagnosis_state = "unknown"
    message = "No headless progress files found."
    if not ip_dir.exists():
        severity = "error"
        diagnosis_state = "missing_ip_dir"
        message = f"{ip} directory does not exist under {root_path}."
    elif finished:
        diagnosis_state = "finished"
        message = f"Headless run finished with status={headless_run.get('status') or heartbeat.get('status') or 'done'}."
    elif active_llm.get("active"):
        elapsed = float(active_llm.get("elapsed_sec") or 0.0)
        if elapsed >= stale_after_sec:
            severity = "warning"
            diagnosis_state = "stuck_llm_call"
            message = (
                f"{current_stage or active_llm.get('stage') or 'workflow'} is still inside "
                f"LLM call for {round(elapsed)}s; no llm_call_end event or LLM log artifact yet."
            )
        else:
            diagnosis_state = "running_llm_call"
            message = (
                f"{current_stage or active_llm.get('stage') or 'workflow'} is inside "
                f"LLM call for {round(elapsed)}s."
            )
    elif heartbeat and heartbeat_age is not None and heartbeat_age >= stale_after_sec:
        severity = "warning"
        diagnosis_state = "stale_heartbeat"
        message = f"Heartbeat has not updated for {round(heartbeat_age)}s."
    elif heartbeat:
        diagnosis_state = "running"
        message = f"Workflow is running phase={phase or 'unknown'} stage={current_stage or 'unknown'}."
    elif events:
        diagnosis_state = "progress_without_heartbeat"
        message = "Progress log exists but heartbeat.json is missing."

    return {
        "root": str(root_path),
        "ip": ip,
        "diagnosis": {
            "state": diagnosis_state,
            "severity": severity,
            "message": message,
            "stale_after_sec": stale_after_sec,
        },
        "current": {
            "state": heartbeat.get("state") or ("done" if finished else ""),
            "status": headless_run.get("status") or heartbeat.get("status") or "",
            "phase": phase,
            "stage": current_stage,
            "model": heartbeat.get("model") or active_llm.get("model") or "",
            "pid": heartbeat.get("pid"),
            "heartbeat_at": heartbeat.get("ts"),
            "heartbeat_age_sec": heartbeat_age,
        },
        "last_event": {
            **last_event,
            "age_sec": last_event_age,
        } if last_event else {},
        "llm": {
            **active_llm,
            "trace_tail": llm_trace[-5:],
        },
        "artifacts": artifacts,
        "events_tail": events[-tail:],
    }


def _format_text(summary: dict[str, Any]) -> str:
    diagnosis = summary.get("diagnosis", {})
    current = summary.get("current", {})
    llm = summary.get("llm", {})
    lines = [
        f"{summary.get('ip')} @ {summary.get('root')}",
        f"diagnosis: {diagnosis.get('state')} ({diagnosis.get('severity')}) - {diagnosis.get('message')}",
        (
            "current: "
            f"state={current.get('state') or '-'} phase={current.get('phase') or '-'} "
            f"stage={current.get('stage') or '-'} model={current.get('model') or '-'} "
            f"heartbeat_age={current.get('heartbeat_age_sec')}"
        ),
        (
            "llm: "
            f"started={llm.get('started', 0)} finished={llm.get('finished', 0)} "
            f"open={llm.get('open', 0)} active={llm.get('active', False)} "
            f"elapsed={llm.get('elapsed_sec')}"
        ),
    ]
    artifacts = summary.get("artifacts", {})
    visible = [name for name, item in artifacts.items() if isinstance(item, dict) and item.get("exists")]
    lines.append("artifacts: " + (", ".join(visible) if visible else "none"))
    return "\n".join(lines)


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description="Summarize ATLAS headless workflow progress.")
    parser.add_argument("--root", required=True, help="Workspace root that contains <ip>/")
    parser.add_argument("--ip", required=True, help="IP directory name")
    parser.add_argument("--json", action="store_true", help="Emit JSON instead of text")
    parser.add_argument("--stale-after-sec", type=float, default=None)
    args = parser.parse_args(argv)
    summary = summarize_headless_progress(args.root, args.ip, stale_after_sec=args.stale_after_sec)
    if args.json:
        print(json.dumps(summary, indent=2, sort_keys=True))
    else:
        print(_format_text(summary))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
