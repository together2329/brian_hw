
"""
Agent Client — HTTP client for Commander → Worker communication

Zero-dependency tools (stdlib only) for Commander to dispatch tasks
to Worker agents running agent_server.py.

Usage from Commander's ReAct loop:
    Action: worker_call(worker="http://localhost:8001", task="Write hello.txt")
    Action: worker_status(worker="http://localhost:8002", run_id="abc123")
    Action: worker_result(worker="http://localhost:8002", run_id="abc123")
"""

import json
import time
import urllib.request
import urllib.error
from typing import Dict, Optional


# ── Public API ────────────────────────────────────────────────

def worker_call(
    worker: str = "http://localhost:8001",
    task: str = "",
    model: str = "",
    timeout: int = 600,
    poll_interval: float = 2.0,
    show_log: bool = True,
) -> Dict:
    """
    Dispatch a task to a Worker agent and wait for completion.

    POST /run → poll GET /status every poll_interval seconds
    → return GET /result when done.

    Args:
        worker: Worker URL (e.g. "http://localhost:8001")
        task: Task description string
        model: Model override (empty = worker default)
        timeout: Max seconds to wait (default 600 = 10 min)
        poll_interval: Seconds between status polls
        show_log: If True, prints Worker's ReAct log entries to console

    Returns:
        Dict with keys: status, result, files_modified, files_examined,
                        iterations, execution_time_ms, error
    """
    worker = worker.rstrip("/")
    start_time = time.time()

    # ── Step 1: POST /run ──────────────────────────────
    try:
        run_id = _post_run(worker, task, model, timeout)
    except Exception as e:
        return {
            "status": "error",
            "result": "",
            "files_modified": [],
            "files_examined": [],
            "iterations": 0,
            "execution_time_ms": 0,
            "error": f"Failed to contact Worker at {worker}: {e}",
        }

    if not run_id:
        return {
            "status": "error",
            "result": "",
            "files_modified": [],
            "files_examined": [],
            "iterations": 0,
            "execution_time_ms": 0,
            "error": f"Worker {worker} did not return a run_id",
        }

    # ── Step 2: Poll GET /status until done ─────────────
    last_log_idx = 0
    while True:
        elapsed = time.time() - start_time
        if elapsed > timeout:
            return {
                "status": "timeout",
                "result": "",
                "files_modified": [],
                "files_examined": [],
                "iterations": 0,
                "execution_time_ms": int(elapsed * 1000),
                "error": f"Worker {worker} timed out after {timeout}s. Run ID: {run_id}",
            }

        status = worker_status(worker, run_id)

        if status.get("status") == "error":
            result = worker_result(worker, run_id)
            result["status"] = "error"
            return result

        if status.get("status") in ("completed", "error"):
            break

        # Show log entries in real-time
        if show_log:
            last_log_idx = _print_new_log_entries(worker, run_id, last_log_idx)

        time.sleep(poll_interval)

    # ── Step 3: GET /result ─────────────────────────────
    if show_log:
        _print_new_log_entries(worker, run_id, last_log_idx, force_all=True)

    result = worker_result(worker, run_id)
    return result


def worker_status(worker: str = "http://localhost:8001", run_id: str = "") -> Dict:
    """
    Get current status of a Worker run.

    Args:
        worker: Worker URL
        run_id: Run ID from worker_call

    Returns:
        Dict with: run_id, status, started_at, completed_at, elapsed_ms, error
    """
    worker = worker.rstrip("/")
    return _get_json(f"{worker}/status/{run_id}")


def worker_result(worker: str = "http://localhost:8001", run_id: str = "") -> Dict:
    """
    Get final result of a completed Worker run.

    Args:
        worker: Worker URL
        run_id: Run ID from worker_call

    Returns:
        Dict with: run_id, status, result, files_modified, files_examined,
                   iterations, execution_time_ms, error
    """
    worker = worker.rstrip("/")
    return _get_json(f"{worker}/result/{run_id}")


# ── Internal Helpers ─────────────────────────────────────────

def _post_json(url: str, data: Dict, timeout: int = 30) -> Dict:
    """POST JSON to url, return parsed JSON response."""
    body = json.dumps(data).encode("utf-8")
    req = urllib.request.Request(
        url,
        data=body,
        headers={"Content-Type": "application/json"},
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        return json.loads(resp.read().decode("utf-8"))


def _get_json(url: str, timeout: int = 10) -> Dict:
    """GET JSON from url, return parsed JSON response."""
    req = urllib.request.Request(url, headers={"Accept": "application/json"})
    try:
        with urllib.request.urlopen(req, timeout=timeout) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        # Return error details from response body if available
        try:
            body = e.read().decode("utf-8")
            return json.loads(body) if body else {"status": "error", "error": str(e)}
        except Exception:
            return {"status": "error", "error": str(e)}
    except Exception as e:
        return {"status": "error", "error": str(e)}


def _post_run(worker: str, task: str, model: str, timeout: int) -> str:
    """POST /run and return run_id."""
    data = {"task": task}
    if model:
        data["model"] = model
    resp = _post_json(f"{worker}/run", data, timeout=30)
    return resp.get("run_id", "")


def _print_new_log_entries(
    worker: str, run_id: str, last_idx: int, force_all: bool = False
) -> int:
    """Fetch new log entries from Worker and print them. Returns new last index."""
    try:
        url = f"{worker}/log/{run_id}"
        resp = _get_json(url, timeout=5)
    except Exception:
        return last_idx

    # The /log endpoint returns {"entries": [...], "total_entries": N, ...}
    if isinstance(resp, dict):
        log = resp.get("entries", [])
    elif isinstance(resp, list):
        log = resp
    else:
        return last_idx

    if not log:
        return last_idx

    new_entries = log[last_idx:] if not force_all else log[last_idx:]

    for entry in new_entries:
        entry_type = entry.get("type", entry.get("role", "?"))
        content = entry.get("content", "")

        if entry_type == "task":
            print(f"\n  [Worker Task] {content[:200]}")
        elif entry_type in ("thought", "action", "response", "system",
                            "completion", "error", "done", "tool_call"):
            # Print key ReAct steps
            prefix = {
                "thought": "Thought", "action": "Action",
                "response": "Resp", "completion": "Done",
                "error": "ERROR", "done": "Done",
                "tool_call": "Tool", "system": "Info",
            }.get(entry_type, entry_type)
            print(f"  [Worker {prefix}] {content[:200]}")
        elif entry_type == "observation":
            # Print first 200 chars of observation
            obs_short = content[:200].replace("\n", " ")
            print(f"  [Worker Obs] {obs_short}")

    return len(log)
