
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
from typing import Any, Dict, Optional


# ── Public API ────────────────────────────────────────────────

# Coordinator URL for name resolution (set via set_coordinator())
_coordinator_url = ""
_coordinator_cache: Dict[str, str] = {}
_coordinator_cache_ts = 0.0
_COORDINATOR_CACHE_TTL = 30.0  # seconds


def set_coordinator(url: str = ""):
    """Set the coordinator URL for worker name resolution.
    Call once at startup if using named workers.

    Args:
        url: Coordinator URL (e.g. 'http://localhost:8000')
    """
    global _coordinator_url
    _coordinator_url = url.rstrip("/") if url else ""


def _resolve_worker(worker: str) -> str:
    """Resolve a worker name to a URL.
    - If it's already a URL (starts with 'http'), return as-is.
    - If a coordinator is configured, query /workers and cache.
    - Otherwise return as-is (caller handles).
    """
    if worker.startswith("http://") or worker.startswith("https://"):
        return worker

    global _coordinator_cache, _coordinator_cache_ts

    if not _coordinator_url:
        return worker  # No coordinator configured

    # Check cache
    now = time.time()
    if worker in _coordinator_cache:
        if (now - _coordinator_cache_ts) < _COORDINATOR_CACHE_TTL:
            return _coordinator_cache[worker]

    # Query coordinator
    try:
        resp = _get_json(f"{_coordinator_url}/workers", timeout=5)
        workers = resp.get("workers", [])
        _coordinator_cache = {}
        for w in workers:
            _coordinator_cache[w["name"]] = w["url"]
        _coordinator_cache_ts = now
        if worker in _coordinator_cache:
            return _coordinator_cache[worker]
    except Exception:
        pass

    return worker  # Fallback


def worker_call(
    worker: str = "http://localhost:8001",
    task: str = "",
    model: str = "",
    todos: list = None,
    template: str = "",
    workflow: str = "",
    reasoning_effort: str = "",
    system_prompt: str = "",
    allowed_tools: Any = None,
    custom_agent: str = "",
    custom_agent_owner_id: str = "",
    timeout: int = 600,
    poll_interval: float = 2.0,
    show_log: bool = True,
) -> Dict:
    """
    Dispatch a task to a Worker agent and wait for completion.

    POST /run → poll GET /status every poll_interval seconds
    → return GET /result when done.

    Args:
        worker: Worker URL (e.g. "http://localhost:8001") or name (e.g. 'lint_worker')
        task: Task description string
        model: Model override (empty = worker default)
        reasoning_effort: Optional reasoning effort override for this run
        system_prompt: Optional custom system prompt to append to the worker prompt
        allowed_tools: Optional custom tool allow-list
        custom_agent: Optional custom agent name for worker logs/metadata
        custom_agent_owner_id: Optional Atlas DB owner id for worker-side custom agent lookup
        timeout: Max seconds to wait (default 600 = 10 min)
        poll_interval: Seconds between status polls
        show_log: If True, prints Worker's ReAct log entries to console

    Returns:
        Dict with keys: status, result, files_modified, files_examined,
                        iterations, execution_time_ms, error
    """
    worker = _resolve_worker(worker).rstrip("/")
    start_time = time.time()

    # ── Step 1: POST /run ──────────────────────────────
    try:
        run_id = _post_run(
            worker, task, model, timeout, todos, template, workflow,
            reasoning_effort=reasoning_effort,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            custom_agent=custom_agent,
            custom_agent_owner_id=custom_agent_owner_id,
        )
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

        if status.get("status") in ("completed", "error", "cancelled"):
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


def worker_cancel(worker: str = "http://localhost:8001", run_id: str = "") -> Dict:
    """Cancel a pending or running Worker task."""
    worker = worker.rstrip("/")
    try:
        body = json.dumps({}).encode("utf-8")
        req = urllib.request.Request(
            f"{worker}/cancel/{run_id}", data=body,
            headers={"Content-Type": "application/json"}, method="POST")
        with urllib.request.urlopen(req, timeout=10) as resp:
            return json.loads(resp.read().decode("utf-8"))
    except urllib.error.HTTPError as e:
        try:
            detail = json.loads(e.read().decode("utf-8"))
            return {"error": str(detail.get("detail", str(e)))}
        except Exception:
            return {"error": str(e)}
    except Exception as e:
        return {"error": str(e)}


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


# ── Batch Parallel Dispatch ──────────────────────────────────

def worker_call_all(
    workers: list,
    task: str,
    model: str = "",
    timeout: int = 600,
    max_workers: int = 10,
    show_log: bool = False,
) -> Dict:
    """
    Dispatch the same task to N workers in parallel and collect all results.

    Uses ThreadPoolExecutor — fires all POST /run (sync=true) calls concurrently,
    then collects results.

    Args:
        workers:    List of worker URLs or names, or [{name, url}] dicts
        task:       Task description string
        model:      Model override (empty = worker default)
        timeout:    Max seconds per worker (default 600 = 10 min)
        max_workers: Max parallel threads
        show_log:   If True, print per-worker progress

    Returns:
        {results: [{worker, url, status, result, error, elapsed_s}],
         total, succeeded, failed}
    """
    from concurrent.futures import ThreadPoolExecutor, as_completed

    # Normalize workers list
    targets = []
    for w in workers:
        if isinstance(w, dict):
            name = w.get("name", w.get("worker", ""))
            url = w.get("url", "")
        else:
            name = str(w)
            url = ""
        if not url:
            url = _resolve_worker(name)
        targets.append({"name": name, "url": url})

    def _dispatch_one(w: dict) -> dict:
        """POST /run sync=true to one worker and return result."""
        start = time.time()
        try:
            result = worker_call(
                worker=w["url"],
                task=task,
                model=model,
                timeout=timeout,
                show_log=show_log,
            )
            elapsed = round(time.time() - start, 2)
            return {
                "worker": w["name"],
                "url": w["url"],
                "status": result.get("status", "error"),
                "result": result.get("result", ""),
                "error": result.get("error", ""),
                "elapsed_s": elapsed,
            }
        except Exception as e:
            elapsed = round(time.time() - start, 2)
            return {
                "worker": w["name"],
                "url": w["url"],
                "status": "error",
                "result": "",
                "error": str(e),
                "elapsed_s": elapsed,
            }

    results = []
    succeeded = 0
    failed = 0

    with ThreadPoolExecutor(max_workers=min(max_workers, len(targets))) as ex:
        futures = {ex.submit(_dispatch_one, w): w for w in targets}
        for future in as_completed(futures):
            r = future.result()
            results.append(r)
            if r["status"] == "completed":
                succeeded += 1
            else:
                failed += 1

    # Sort by worker name for determinism
    results.sort(key=lambda r: r["worker"])

    return {
        "results": results,
        "total": len(results),
        "succeeded": succeeded,
        "failed": failed,
    }


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


def _post_run(worker: str, task: str, model: str, timeout: int,
              todos: list = None, template: str = "", workflow: str = "",
              reasoning_effort: str = "", system_prompt: str = "",
              allowed_tools: Any = None, custom_agent: str = "",
              custom_agent_owner_id: str = "") -> str:
    """POST /run and return run_id."""
    data = {"task": task}
    if model:
        data["model"] = model
    if todos:
        data["todos"] = todos
    if template:
        data["template"] = template
    if workflow:
        data["workflow"] = workflow
    if reasoning_effort:
        data["reasoning_effort"] = reasoning_effort
    if system_prompt:
        data["system_prompt"] = system_prompt
    if allowed_tools:
        data["allowed_tools"] = allowed_tools
    if custom_agent:
        data["custom_agent"] = custom_agent
    if custom_agent_owner_id:
        data["custom_agent_owner_id"] = custom_agent_owner_id
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
