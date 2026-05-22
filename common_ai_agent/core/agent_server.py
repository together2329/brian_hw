"""Agent Server — HTTP API for Common AI Agent ↔ Common AI Agent communication.

Wraps the full ReAct loop into HTTP endpoints so independent agent processes
can send tasks to each other and collect results.

Usage:
    python main.py --serve --port 8001

Endpoints:
    POST /run          — Start a task (sync or async)
    GET  /status/{id}  — Poll progress
    GET  /result/{id}  — Get final output
    GET  /log/{id}     — Get ReAct transcript (real-time)
    GET  /health       — Liveness check

Zero breakage: this file is never imported unless --serve flag is used.
"""

import os
import sys
import json
import time
import uuid
import threading
import re
import traceback
import urllib.request
from pathlib import Path
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from concurrent.futures import ThreadPoolExecutor

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)
if os.path.join(_project_root, 'src') not in sys.path:
    sys.path.insert(0, os.path.join(_project_root, 'src'))

from core.session_names import normalize_session_name


def _configure_text_stdio() -> None:
    """Make redirected Windows consoles lossy instead of crashy."""

    os.environ.setdefault("PYTHONUTF8", "1")
    os.environ.setdefault("PYTHONIOENCODING", "utf-8:replace")
    for stream in (sys.stdout, sys.stderr):
        try:
            stream.reconfigure(errors="replace")
        except Exception:
            pass


def _safe_print(line: str = "") -> None:
    """Print terminal diagnostics without failing on legacy code pages."""

    try:
        print(line)
    except UnicodeEncodeError:
        encoding = getattr(sys.stdout, "encoding", None) or "utf-8"
        safe = str(line).encode(encoding, errors="replace").decode(encoding, errors="replace")
        print(safe)


_configure_text_stdio()


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class RunEntry:
    """Tracks a single /run invocation."""
    run_id: str
    status: str = "pending"          # pending → running → completed / error
    task: str = ""
    model: str = ""
    result: Optional[Dict[str, Any]] = None
    log: List[Dict[str, Any]] = field(default_factory=list)     # ReAct transcript
    created_at: float = 0.0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error: Optional[str] = None
    on_complete_url: str = ""        # Webhook callback URL
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _cancel_event: threading.Event = field(default_factory=threading.Event)
    _log_event: threading.Event = field(default_factory=threading.Event)

    def add_log(self, entry_type: str, content: str, role: str = "") -> None:
        """Thread-safe log append. Prints to terminal when _VERBOSE is on."""
        ts = time.time()
        with self._lock:
            idx = len(self.log)
            self.log.append({
                "index": idx,
                "type": entry_type,
                "role": role,
                "content": content,
                "timestamp": ts,
            })
        if _VERBOSE:
            _print_entry(self.run_id, entry_type, content)
        self._log_event.set()  # Wake SSE stream listeners

    def get_log(self, since: int = 0, tail: int = 0) -> List[Dict[str, Any]]:
        """Thread-safe log read with optional filters."""
        with self._lock:
            entries = list(self.log)
        if since > 0:
            entries = [e for e in entries if e["index"] >= since]
        if tail > 0:
            entries = entries[-tail:]
        return entries


# ─── In-Memory Run Store ────────────────────────────────────────────────

_runs: Dict[str, RunEntry] = {}
_runs_lock = threading.Lock()
_MAX_CONCURRENT = int(os.getenv("AGENT_SERVER_MAX_CONCURRENT", "8"))
_executor = ThreadPoolExecutor(max_workers=_MAX_CONCURRENT)
_concurrency_semaphore = threading.BoundedSemaphore(_MAX_CONCURRENT)

# Worker registry — name → {name, url, registered_at}
_worker_registry: Dict[str, Dict[str, Any]] = {}
_REGISTRY_FILE = Path(_project_root) / ".session" / "worker_registry.json"

# TTL for completed/error/cancelled runs (seconds)
_RUN_TTL = int(os.getenv("AGENT_SERVER_RUN_TTL", "600"))  # 10 minutes default
# How often the cleanup thread wakes up (seconds)
_CLEANUP_INTERVAL = int(os.getenv("AGENT_SERVER_CLEANUP_INTERVAL", "60"))
_cleanup_started = False
# Verbose mode — print each log entry to terminal in real-time
_VERBOSE = False
# Verbose filter — comma-separated run_ids to show ('' or '*' = all)
_VERBOSE_FILTER = ""

# Persistence — save runs to disk for survivability across restarts
_PERSISTENCE_ENABLED = os.getenv("AGENT_SERVER_PERSISTENCE", "true").lower() in ("1", "true", "yes")
_PERSISTENCE_FILE = Path(_project_root) / ".session" / "agent_runs.json"

# Server start time for uptime metric
_START_TIME = time.time()

# Per-worker state (set once in serve())
_SERVER_PORT: int = 8000
_SERVER_WORKFLOW: str = ""    # Workflow this worker was started with (--workflow). Empty = unrestricted.
_SERVER_ACCEPT_ANY_WORKFLOW: bool = False  # When True (--all-workflows), each /run sets up the requested workflow's workspace before executing, matching the May-12 single-main-loop pattern.
_worker_todo_tracker = None   # TodoTracker instance shared across all runs on this worker

# Log directory for persistent audit trail
_LOG_DIR = os.getenv("AGENT_SERVER_LOG_DIR", "")

def _on_status_change():
    """Callback after any run status transition. Triggers persistence save."""
    if _PERSISTENCE_ENABLED:
        _save_runs()

# Type-to-emoji mapping for terminal output
_VERBOSE_ICONS = {
    "system":      "⚙️",
    "task":        "📋",
    "context":     "📎",
    "plan":        "📝",
    "iteration":   "🔄",
    "thought":     "💭",
    "action":      "▶️",
    "tool_call":   "🔧",
    "observation": "👁️",
    "response":    "💬",
    "completion":  "✅",
    "error":       "❌",
    "done":        "🏁",
}


def _print_entry(run_id: str, entry_type: str, content: str):
    """Print a single log entry to terminal in a compact, readable format."""
    # Check filter
    if _VERBOSE_FILTER and _VERBOSE_FILTER != "*":
        allowed = [x.strip() for x in _VERBOSE_FILTER.split(",")]
        if run_id not in allowed:
            return
    short_id = run_id[-8:] if len(run_id) > 8 else run_id
    icon = _VERBOSE_ICONS.get(entry_type, "·")
    # Truncate long content for terminal readability
    preview = content.replace("\n", " ").strip()
    if len(preview) > 150:
        preview = preview[:147] + "..."
    # Add color/highlight for key entry types
    if entry_type in ("action", "tool_call"):
        _safe_print(f"  {icon} [{short_id}] \033[1;36m{preview}\033[0m")
    elif entry_type == "error":
        _safe_print(f"  {icon} [{short_id}] \033[1;31m{preview}\033[0m")
    elif entry_type in ("completion", "done"):
        _safe_print(f"  {icon} [{short_id}] \033[1;32m{preview}\033[0m")
    elif entry_type == "iteration":
        _safe_print(f"\n{icon} [{short_id}] {preview}")
    else:
        _safe_print(f"  {icon} [{short_id}] {preview}")


def _cleanup_expired_runs():
    """Remove runs that have been finished longer than _RUN_TTL seconds.
    Also cancel stale running runs that exceed 2x _RUN_TTL (stuck runs)."""
    changed = False
    with _runs_lock:
        now = time.time()
        expired = []
        for run_id, entry in list(_runs.items()):
            if entry.status in ("completed", "error", "cancelled"):
                if entry.finished_at and (now - entry.finished_at) > _RUN_TTL:
                    expired.append(run_id)
            elif entry.status == "running":
                if entry.started_at and (now - entry.started_at) > (_RUN_TTL * 2):
                    entry._cancel_event.set()
                    entry.status = "cancelled"
                    entry.finished_at = now
                    entry.add_log("system", "Run expired (exceeded 2x TTL)", role="system")
                    expired.append(run_id)
        for run_id in expired:
            del _runs[run_id]
        if expired:
            print(f"[cleanup] Removed {len(expired)} expired run(s)")
            changed = True
            # Also clean up log-dir files
            if _LOG_DIR:
                for run_id in expired:
                    try:
                        (Path(_LOG_DIR) / f"{run_id}.json").unlink(missing_ok=True)
                    except Exception:
                        pass
    if changed:
        _save_runs()


def _fire_callback(entry: RunEntry) -> None:
    """Fire webhook callback on run completion (background, with retry)."""
    url = entry.on_complete_url
    if not url:
        return
    body = json.dumps(entry.result).encode("utf-8")
    for attempt in range(3):
        try:
            req = urllib.request.Request(
                url, data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            urllib.request.urlopen(req, timeout=30)
            return  # Success
        except Exception as e:
            if attempt < 2:
                time.sleep(1 * (attempt + 1))  # Backoff: 1s, 2s
            else:
                print(f"[webhook] Failed to deliver callback to {url}: {e}")


def _write_run_log(entry: RunEntry) -> None:
    """Write completed run log to disk if _LOG_DIR is set."""
    if not _LOG_DIR:
        return
    try:
        log_dir = Path(_LOG_DIR)
        log_dir.mkdir(parents=True, exist_ok=True)
        out_path = log_dir / f"{entry.run_id}.json"
        out_path.write_text(json.dumps({
            "run_id": entry.run_id,
            "task": entry.task,
            "status": entry.status,
            "created_at": entry.created_at,
            "started_at": entry.started_at,
            "finished_at": entry.finished_at,
            "error": entry.error,
            "result": entry.result,
            "entries": entry.log,
        }, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
    except Exception as e:
        print(f"[log-dir] WARNING: Failed to write {entry.run_id}: {e}")


def _save_runs():
    """Persist _runs to disk atomically (write-then-rename)."""
    if not _PERSISTENCE_ENABLED:
        return
    try:
        _PERSISTENCE_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _PERSISTENCE_FILE.with_suffix(".tmp")
        now = time.time()
        with _runs_lock:
            data = {
                "saved_at": now,
                "runs": {}
            }
            for run_id, entry in _runs.items():
                data["runs"][run_id] = {
                    "run_id": entry.run_id,
                    "status": entry.status,
                    "task": entry.task,
                    "model": entry.model,
                    "created_at": entry.created_at,
                    "started_at": entry.started_at,
                    "finished_at": entry.finished_at,
                    "error": entry.error,
                    "result": entry.result,
                    "log": entry.log,  # Full transcript
                }
        tmp.write_text(json.dumps(data, indent=2, default=str, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_PERSISTENCE_FILE)
    except Exception as e:
        print(f"[persist] WARNING: Failed to save runs: {e}")


def _load_runs():
    """Restore _runs from disk on startup. Skip stale runs (>TTL)."""
    if not _PERSISTENCE_ENABLED:
        return
    if not _PERSISTENCE_FILE.exists():
        return
    try:
        data = json.loads(_PERSISTENCE_FILE.read_text(encoding="utf-8", errors="replace"))
        runs_data = data.get("runs", {})
        now = time.time()
        restored = 0
        skipped = 0
        with _runs_lock:
            for run_id, rdict in runs_data.items():
                status = rdict.get("status", "completed")
                finished_at = rdict.get("finished_at")
                # Skip stale completed/error/cancelled runs
                if status in ("completed", "error", "cancelled") and finished_at:
                    if (now - finished_at) > _RUN_TTL:
                        skipped += 1
                        continue
                # Skip running runs that would be stale
                if status == "running":
                    started_at = rdict.get("started_at")
                    if started_at and (now - started_at) > (_RUN_TTL * 2):
                        skipped += 1
                        continue
                    # Reset running runs to cancelled (server restarted)
                    status = "cancelled"
                # Reconstruct RunEntry
                entry = RunEntry(
                    run_id=rdict.get("run_id", run_id),
                    status=status,
                    task=rdict.get("task", ""),
                    model=rdict.get("model", ""),
                    result=rdict.get("result"),
                    error=rdict.get("error"),
                    created_at=rdict.get("created_at", now),
                    started_at=rdict.get("started_at"),
                    finished_at=rdict.get("finished_at") or (now if status == "cancelled" else None),
                )
                # Restore log
                log_data = rdict.get("log", [])
                if log_data:
                    entry.log = log_data
                _runs[run_id] = entry
                restored += 1
        if restored or skipped:
            print(f"[persist] Loaded {restored} run(s) from disk, skipped {skipped} stale")
    except Exception as e:
        print(f"[persist] WARNING: Failed to load runs: {e}")


def _save_registry():
    """Persist worker registry to disk atomically."""
    if not _PERSISTENCE_ENABLED:
        return
    try:
        _REGISTRY_FILE.parent.mkdir(parents=True, exist_ok=True)
        tmp = _REGISTRY_FILE.with_suffix(".tmp")
        with _runs_lock:
            data = {"saved_at": time.time(), "workers": dict(_worker_registry)}
        tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False), encoding="utf-8")
        tmp.replace(_REGISTRY_FILE)
    except Exception as e:
        print(f"[persist] WARNING: Failed to save registry: {e}")


def _load_registry():
    """Restore worker registry from disk on startup."""
    if not _PERSISTENCE_ENABLED:
        return
    if not _REGISTRY_FILE.exists():
        return
    try:
        data = json.loads(_REGISTRY_FILE.read_text(encoding="utf-8", errors="replace"))
        workers_data = data.get("workers", {})
        with _runs_lock:
            for name, entry in workers_data.items():
                _worker_registry[name] = entry
        if workers_data:
            print(f"[persist] Loaded {len(workers_data)} worker(s) from registry")
    except Exception as e:
        print(f"[persist] WARNING: Failed to load registry: {e}")


def _resolve_worker_name(name: str) -> str:
    """Resolve a worker name to its URL via the local registry.
    If name is already a URL (starts with 'http'), return as-is.
    Returns the resolved URL or the original name if not found."""
    if name.startswith("http://") or name.startswith("https://"):
        return name
    with _runs_lock:
        entry = _worker_registry.get(name)
    if entry:
        return entry["url"]
    return name  # fallback: return as-is (caller may handle as URL)


def _start_cleanup_thread():
    """Start a background daemon thread that periodically calls _cleanup_expired_runs."""
    def _loop():
        while True:
            time.sleep(_CLEANUP_INTERVAL)
            try:
                _cleanup_expired_runs()
            except Exception:
                pass

    t = threading.Thread(target=_loop, daemon=True, name="run-cleanup")
    t.start()
    return t


def _build_todos_summary(todos: list, entry) -> list:
    """Build a summary of todo items with completion status."""
    summary = []
    for i, t in enumerate(todos):
        if isinstance(t, dict):
            content = t.get("content", str(t))
        else:
            content = str(t)
        # Check log for todo_update calls matching this item index (1-based)
        completed = False
        idx_pat = re.compile(r"index\s*=\s*" + str(i + 1))
        for log_entry in entry.log:
            if log_entry.get("type") in ("tool_call", "action"):
                c2 = log_entry.get("content", "")
                if idx_pat.search(c2) and "todo_update" in c2:
                    if '"completed"' in c2 or "'completed'" in c2:
                        completed = True
                    break
        summary.append({"index": i + 1, "content": content, "completed": completed})
    return summary


def _load_todo_template(name: str, workflow: str = "", ip: str = "") -> Optional[list]:
    """Load tasks from a todo template JSON file.

    Search order:
      1. workflow/<workflow>/todo_templates/<name>.json  (if workflow given)
      2. todo_templates/<name>.json                      (CWD fallback)

    Returns the tasks list on success, None if not found.
    """
    if ip:
        try:
            from workflow.loader import load_dynamic_todo_template
            tasks, source, _ = load_dynamic_todo_template(name, ip, project_root=Path(_project_root))
            if tasks and source:
                print(f"[template] Loaded dynamic '{name}' for {ip} ({len(tasks)} tasks) from {source}")
                return tasks
        except Exception as e:
            print(f"[template] WARNING: Failed to load dynamic template {name} for {ip}: {e}")

    candidates: list[Path] = []

    if workflow:
        # Search workflow directory relative to the project root
        _root = Path(_project_root)
        for wf_root in [
            _root / "workflow" / workflow / "todo_templates",
            _root.parent / "workflow" / workflow / "todo_templates",
        ]:
            candidates.append(wf_root / f"{name}.json")
            candidates.append(wf_root / name)

    # CWD fallback
    candidates.append(Path.cwd() / "todo_templates" / f"{name}.json")
    candidates.append(Path.cwd() / "todo_templates" / name)

    for path in candidates:
        if path.exists():
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                tasks = (
                    data.get("tasks")
                    or data.get("items")
                    or (data if isinstance(data, list) else None)
                )
                if tasks:
                    print(f"[template] Loaded '{name}' ({len(tasks)} tasks) from {path}")
                    return tasks
            except Exception as e:
                print(f"[template] WARNING: Failed to load {path}: {e}")
    return None


def _create_run(task: str, model: str = "") -> RunEntry:
    run_id = f"run_{uuid.uuid4().hex[:8]}"
    entry = RunEntry(
        run_id=run_id,
        task=task,
        model=model,
        created_at=time.time(),
    )
    with _runs_lock:
        _runs[run_id] = entry
    return entry


def _snapshot_scope_files(project_root: str, ip: str) -> Dict[str, tuple[int, int]]:
    """Return a cheap file snapshot for the IP scope.

    Worker slash commands are deterministic stage entrypoints.  Capturing the
    scope before/after lets the worker result expose modified files without
    requiring a full LLM transcript scan.
    """
    if not ip:
        return {}
    root = Path(project_root or _project_root).resolve()
    scope = (root / ip).resolve()
    try:
        scope.relative_to(root)
    except ValueError:
        return {}
    if not scope.exists():
        return {}
    out: Dict[str, tuple[int, int]] = {}
    for path in scope.rglob("*"):
        if not path.is_file():
            continue
        try:
            st = path.stat()
        except OSError:
            continue
        try:
            rel = str(path.relative_to(root))
        except ValueError:
            rel = str(path)
        out[rel] = (int(st.st_mtime_ns), int(st.st_size))
    return out


def _changed_scope_files(before: Dict[str, tuple[int, int]], after: Dict[str, tuple[int, int]]) -> List[str]:
    return sorted(path for path, sig in after.items() if before.get(path) != sig)


def _extract_direct_slash_commands(task: str) -> List[str]:
    """Extract coordinator-sent workflow slash commands from a worker task.

    ATLAS dispatch prompts intentionally include canonical drivers such as
    ``run /ssot-rtl <ip>``.  Treat those as worker commands, not prose for an
    LLM to reinterpret.  The parser is deliberately conservative: it only
    accepts commands at line starts or after common command separators.
    """
    if os.getenv("AGENT_SERVER_DIRECT_SLASH", "true").lower() not in {"1", "true", "yes", "on"}:
        return []
    text = str(task or "")
    if "/" not in text:
        return []
    text = re.sub(r"\s+(?:and|then)\s+/", "\n/", text, flags=re.IGNORECASE)
    text = text.replace(";", "\n")
    commands: List[str] = []
    for raw in text.splitlines():
        line = raw.strip()
        if not line:
            continue
        if line.lower().startswith("run "):
            line = line[4:].strip()
        match = re.match(r"^(/[A-Za-z0-9][A-Za-z0-9_-]*(?:\s+.*)?)$", line)
        if not match:
            continue
        command = match.group(1).strip().rstrip(".")
        # Drop obvious prose suffixes while preserving normal command args.
        command = re.split(r"\s+(?:generate|using|after|before)\s+", command, maxsplit=1, flags=re.IGNORECASE)[0].strip()
        if command and command not in commands:
            commands.append(command)
    return commands


def _slash_command_failed(output: str) -> bool:
    text = str(output or "")
    lowered = text.lower()
    return (
        "[error]" in lowered
        or re.search(r"\[[^\]\n]*(?:blocked|fail|failed)[^\]\n]*\]", lowered) is not None
        or re.search(r"\[[^\]\n]+\]\s*(?:blocked|fail|failed)\b", lowered) is not None
        or re.search(r"(^|\n)\s*(?:blocked|blocker):", lowered) is not None
        or "status=error" in lowered
        or "❌" in text
        or "unknown command" in lowered
        or "script timed out" in lowered
        or "traceback" in lowered
    )


def _slash_command_needs_llm_followup(command: str, output: str) -> bool:
    """Return true when a deterministic stage driver asks the worker LLM to continue.

    Some ATLAS slash commands are preflight drivers, not terminal producers. In
    particular, /ssot-rtl can derive RTL TODOs and then intentionally emit an
    LLM_RTL_IMPLEMENTATION_REQUIRED blocker. That is a handoff to rtl-gen's LLM
    authoring loop, not a worker-run failure.
    """
    cmd = str(command or "").lower()
    text = str(output or "").lower()
    return (
        "/ssot-rtl" in cmd
        and (
            "llm_rtl_implementation_required" in text
            or "llm-authored rtl evidence is missing or stale" in text
            or "llm-authored rtl needs rtl-gen repair" in text
            or "rtl-gen repair" in text
            or "open_required_todos" in text
            or "static_missing" in text
        )
    )


def _execute_direct_slash_commands(
    entry: RunEntry,
    commands: List[str],
    *,
    project_root: str,
    ip: str,
) -> tuple[bool, str]:
    """Execute extracted slash commands.

    Returns ``(closed_run, output)``. Most direct slash commands are terminal
    and close the worker run. Preflight commands that explicitly request LLM
    follow-up return ``closed_run=False`` so the caller can continue into the
    ReAct loop with the command observations attached.
    """
    from core.slash_commands import get_registry

    before = _snapshot_scope_files(project_root, ip)
    registry = get_registry()
    outputs: List[str] = []
    failed = False
    needs_llm_followup = False
    for command in commands:
        entry.add_log("action", f"slash:{command}", role="assistant")
        result = registry.execute(command)
        rendered = "" if result is None else str(result)
        outputs.append(f"$ {command}\n{rendered}".rstrip())
        entry.add_log("observation", rendered[:2000], role="tool")
        if _slash_command_needs_llm_followup(command, rendered):
            needs_llm_followup = True
        else:
            failed = failed or _slash_command_failed(rendered)

    after = _snapshot_scope_files(project_root, ip)
    files_modified = _changed_scope_files(before, after)
    final_output = "\n\n".join(outputs)
    if needs_llm_followup and not failed:
        entry.add_log(
            "system",
            f"Direct slash command requested LLM follow-up; continuing ReAct loop with {len(files_modified)} preflight file(s) modified.",
            role="system",
        )
        return False, final_output

    entry.status = "error" if failed else "completed"
    entry.error = "direct slash command failed" if failed else None
    entry.finished_at = time.time()
    entry.result = {
        "run_id": entry.run_id,
        "status": entry.status,
        "result": final_output[:10000],
        "files_modified": files_modified,
        "files_examined": [],
        "iterations": 0,
        "todos_summary": _build_todos_summary(getattr(entry, "_todos", []) or [], entry),
        "direct_slash_commands": commands,
    }
    _on_status_change()
    entry.add_log(
        "done" if not failed else "error",
        f"Direct slash command path {'failed' if failed else 'completed'}; {len(files_modified)} files modified.",
        role="system",
    )
    _fire_callback(entry)
    _write_run_log(entry)
    return True, final_output


def _get_run(run_id: str) -> Optional[RunEntry]:
    with _runs_lock:
        return _runs.get(run_id)


def _cancel_run(run_id: str) -> bool:
    """Cancel a pending or running run."""
    entry = _get_run(run_id)
    if not entry:
        return False
    if entry.status in ("completed", "error", "cancelled"):
        return False
    entry._cancel_event.set()
    entry.status = "cancelled"
    entry.finished_at = time.time()
    entry.add_log("system", "Run cancelled by client request", role="system")
    _on_status_change()
    return True


# ─── ReAct Loop Wrapper (uses run_react_agent_impl from core/react_loop.py) ──


def _run_react_task(entry: RunEntry, task: str, model: str = "",
                    todos: Optional[List[Any]] = None, context: str = "",
                    workflow: str = "", session_name: str = "",
                    ip: str = "", rtl_version_id: str = "",
                    project_root: str = "", artifact_versions: Any = None,
                    reasoning_effort: str = "") -> None:
    """
    Execute a full ReAct loop using run_react_agent_impl from core/react_loop.py.

    This replaces the old ~200-line hand-rolled loop with the full production
    ReAct loop, giving worker agents: compression, hooks, todo tracking,
    parallel execution, ESC abort, and native tool calls.

    All output is captured into entry.log for HTTP polling.
    Runs in a worker thread so the HTTP endpoint can return immediately.
    """
    entry.status = "running"
    entry.started_at = time.time()
    _on_status_change()
    entry.add_log("system", "ReAct loop starting (full run_react_agent_impl)...", role="system")
    _trace_runtime_prev = None

    _ws_hook_registry = None  # populated by workspace activation if script_hooks defined

    # ── Activate workspace if specified (full main-agent parity) ─────────
    if workflow:
        try:
            from workflow.loader import (
                load_workspace, merge_prompt, patch_todo_rules,
                register_script_hooks, register_workspace_commands,
                get_todo_template_registry,
            )
            import builtins as _b
            import core.compressor as _comp

            ws = load_workspace(workflow, project_root=Path(_project_root))
            if (
                workflow == "ssot-gen"
                and "[ATLAS_PIPELINE_SSOT_DIRECT_WRITE]" in task
            ):
                compact_prompt = (
                    Path(_project_root)
                    / "workflow"
                    / "ssot-gen"
                    / "system_prompt_pipeline.md"
                )
                if compact_prompt.exists():
                    ws.system_prompt_text = compact_prompt.read_text(encoding="utf-8").strip()
                    ws.system_prompt_mode = "replace"
                    ws.force_skills = []
                    ws.disable_skills = []
                    entry.add_log(
                        "system",
                        "ATLAS compact SSOT pipeline prompt active",
                        role="system",
                    )

            # ── 1. Hook messages ──
            _b._WORKSPACE_HOOK_MESSAGES = {"_workspace_dir": str(ws.workspace_dir)}
            if ws.hook_messages:
                _b._WORKSPACE_HOOK_MESSAGES.update(ws.hook_messages)

            # ── 2. System prompt patch (build_system_prompt called inside _worker_build_prompt) ──
            if ws.system_prompt_text:
                try:
                    import core.prompt_builder as _pb
                    _orig_bsp = _pb.build_system_prompt
                    _ws_sys_text = ws.system_prompt_text
                    _ws_sys_mode = ws.system_prompt_mode

                    def _ws_patched_bsp(ctx=None, **kw):
                        base = _orig_bsp(ctx, **kw) if ctx is not None else _orig_bsp(**kw)
                        if isinstance(base, dict):
                            base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
                        merged = merge_prompt(base, _ws_sys_text, _ws_sys_mode)
                        try:
                            from lib.memory import MemorySystem
                            merged = _pb.apply_memory_override(
                                merged,
                                MemorySystem(memory_dir=getattr(config, "MEMORY_DIR", ".memory")),
                                workflow=workflow,
                            )
                        except Exception:
                            pass
                        return merged

                    _pb.build_system_prompt = _ws_patched_bsp
                except Exception:
                    pass

            # ── 3. Compression prompt patch ──
            # Default mode is "append" so workflow prompts EXTEND the rich default
            # (with universal preservation rules). Workflows can opt back to
            # "replace" via workspace.json if they really want a fully custom format.
            #
            # Both "compression_user_instruction" (new canonical) and
            # "compression_system" (legacy) keys are written so existing
            # consumers keep working. compressor._load_default_compression_prompt
            # prefers the new key.
            if ws.compression_prompt_text:
                try:
                    _orig_comp_prompt = getattr(_comp, 'STRUCTURED_SUMMARY_PROMPT', "")
                    _comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                        _orig_comp_prompt,
                        ws.compression_prompt_text,
                        getattr(ws, "compression_prompt_mode", "append"),
                    )
                    _b._WORKSPACE_HOOK_MESSAGES["compression_user_instruction"] = _comp.STRUCTURED_SUMMARY_PROMPT
                    _b._WORKSPACE_HOOK_MESSAGES["compression_system"] = _comp.STRUCTURED_SUMMARY_PROMPT
                except Exception:
                    pass

            # ── 4. Env overrides ──
            for k, v in ws.env_overrides.items():
                os.environ[k] = str(v)

            # ── 5. Script hooks (local registry passed into ReactLoopDeps below) ──
            if ws.script_hooks:
                try:
                    from core.hooks import HookRegistry
                    _ws_hook_registry = HookRegistry()
                    register_script_hooks(ws, _ws_hook_registry)
                except Exception as _she:
                    entry.add_log("system", f"WARNING: script hooks setup failed: {_she}", role="system")

            # ── 5b. Slash commands ──
            # ATLAS orchestrator dispatches canonical workflow entrypoints as
            # slash commands (for example, `run /ssot-rtl <ip>`).  Register the
            # workspace commands in worker mode too, otherwise those drivers
            # are forced through the LLM instead of the stage engine.
            try:
                from core.slash_commands import get_registry as _get_slash_registry
                _slash_reg = _get_slash_registry()
                _registered = register_workspace_commands(ws, _slash_reg)
                if _registered:
                    entry.add_log(
                        "system",
                        f"Registered {len(_registered)} workspace slash commands",
                        role="system",
                    )
            except Exception as _cmd_exc:
                entry.add_log("system", f"WARNING: command setup failed: {_cmd_exc}", role="system")

            # ── 6. Todo rules ──
            try:
                patch_todo_rules(ws)
            except Exception:
                pass

            # ── 7. Todo template registry ──
            try:
                _t_reg = get_todo_template_registry()
                _t_reg._templates.clear()
                _t_reg.load_global_templates(Path.cwd())
                if ws.todo_templates_dir:
                    _t_reg.load_from_dir(ws.todo_templates_dir)
                _b._TODO_TEMPLATE_REGISTRY = _t_reg
            except Exception:
                pass

            # ── 8. Extra skills dir ──
            try:
                import core.skill_system as _ss
                if ws.extra_skills_dir and hasattr(_ss, '_loader') and hasattr(_ss._loader, 'extra_dirs'):
                    _ws_skill_str = str(ws.extra_skills_dir)
                    _ss._loader.extra_dirs = [
                        d for d in _ss._loader.extra_dirs
                        if '/workflow/' not in d.replace('\\', '/')
                    ]
                    _ss._loader.extra_dirs.append(_ws_skill_str)
            except Exception:
                pass

            # ── 9. Force / disable skills ──
            if ws.force_skills:
                os.environ["FORCE_SKILLS"] = ",".join(ws.force_skills)
            else:
                os.environ.pop("FORCE_SKILLS", None)
            if ws.disable_skills:
                os.environ["DISABLE_SKILLS"] = ",".join(ws.disable_skills)
            else:
                os.environ.pop("DISABLE_SKILLS", None)

            entry.add_log("system", f"Workspace '{workflow}' activated (full parity)", role="system")
        except Exception as _we:
            entry.add_log("system", f"WARNING: workspace '{workflow}' load failed: {_we}", role="system")

    try:
        try:
            from core.atlas_trace import push_trace_runtime as _push_trace_runtime
            _trace_runtime_prev = _push_trace_runtime(
                ATLAS_ACTIVE_SESSION=normalize_session_name(session_name),
                ATLAS_ACTIVE_IP=ip,
                ATLAS_DEFAULT_WORKFLOW=workflow,
                ATLAS_ACTIVE_RTL_VERSION_ID=rtl_version_id,
                ATLAS_ACTIVE_ARTIFACT_VERSIONS=artifact_versions or [],
                ATLAS_ACTIVE_RUN_ID="",
                ATLAS_PROJECT_ROOT=project_root or os.environ.get("ATLAS_PROJECT_ROOT") or _project_root,
            )
        except Exception:
            _trace_runtime_prev = None

        import config
        from core.react_loop import ReactLoopDeps, run_react_agent_impl
        from core.compressor import compress_history as _compress_history
        from core.prompt_builder import PromptContext, apply_memory_override, build_system_prompt
        from core.observation_processor import process_observation
        from core.action_parser import _strip_native_tool_tokens, _strip_thinking_tags
        from core.tools import AVAILABLE_TOOLS, filtered_available_tools
        from core.tool_dispatcher import dispatch_tool as _dispatch_tool
        from core.parallel_executor import execute_actions_parallel as _execute_actions_parallel_impl
        from lib.iteration_control import (
            IterationTracker, detect_completion_signal,
        )
        from src.main import _parse_todo_markdown
        import src.llm_client as _worker_llm_client

        try:
            config.reload_env()
        except Exception:
            pass

        # ── Model override ──
        effective_model = model or config.MODEL_NAME
        effective_effort = str(reasoning_effort or "").strip().lower()
        effort_aliases = {
            "l": "low",
            "m": "medium",
            "med": "medium",
            "mid": "medium",
            "h": "high",
            "hi": "high",
            "x": "xhigh",
            "xh": "xhigh",
            "xhi": "xhigh",
            "max": "xhigh",
        }
        effective_effort = effort_aliases.get(effective_effort, effective_effort)
        if effective_effort not in {"", "none", "low", "medium", "high", "xhigh"}:
            entry.add_log(
                "system",
                f"WARNING: ignoring unsupported reasoning_effort={reasoning_effort!r}",
                role="system",
            )
            effective_effort = ""

        # ── Per-run session override ──
        # Server startup still initializes a default worker session, but ATLAS
        # dispatches each workflow/job with its own session namespace so logs
        # can be reopened after worker restart via .session/<ip>/<workflow>.
        session_overrides: Dict[str, str] = {}
        run_todo_tracker = _worker_todo_tracker
        active_session = normalize_session_name(session_name)
        if active_session:
            session_dir = Path(_project_root) / ".session" / active_session
            session_dir.mkdir(parents=True, exist_ok=True)
            session_overrides = {
                "HISTORY_FILE": str(session_dir / "conversation.json"),
                "TODO_FILE": str(session_dir / "todo.json"),
                "TODO_ERROR_FILE": str(session_dir / "todo_error.json"),
                "COST_FILE": str(session_dir / "cost.json"),
                "SESSION_DIR": str(session_dir),
                "ACTIVE_PROJECT": active_session,
            }
            try:
                from lib.todo_tracker import TodoTracker
                run_todo_tracker = TodoTracker.load(session_dir / "todo.json") if config.ENABLE_TODO_TRACKING else None
            except Exception:
                run_todo_tracker = _worker_todo_tracker
            entry.add_log("system", f"Session '.session/{active_session}' active", role="system")

        # ── Build config mirror (all .config values + run overrides) ──
        def _snapshot_config_module() -> Dict[str, Any]:
            snap: Dict[str, Any] = {}
            for key in dir(config):
                if key.startswith("__"):
                    continue
                try:
                    snap[key] = getattr(config, key)
                except Exception:
                    continue
            return snap

        class _RunCfg:
            """Mirror src.config for worker runs, then layer run overrides.

            Worker execution should behave like the textual/main ReAct path.
            Keep a full snapshot of config.py/.config-derived attributes so
            code using direct attribute access, getattr(), dir(), or get() sees
            the same shape as the real module.  Only explicit per-run values
            such as MODEL_NAME and session files are overridden.
            """
            def __init__(self, base: Dict[str, Any], overrides: Dict[str, Any]):
                object.__setattr__(self, "_base", dict(base))
                object.__setattr__(self, "_overrides", dict(overrides))

            def __getattr__(self, name):
                overrides = object.__getattribute__(self, "_overrides")
                if name in overrides:
                    return overrides[name]
                base = object.__getattribute__(self, "_base")
                if name in base:
                    return base[name]
                return getattr(config, name)

            def __setattr__(self, name, value):
                object.__getattribute__(self, "_overrides")[name] = value

            def __dir__(self):
                return sorted(
                    set(object.__getattribute__(self, "_base"))
                    | set(object.__getattribute__(self, "_overrides"))
                )

            def get(self, name, default=None):
                try:
                    return getattr(self, name)
                except AttributeError:
                    return default

            def as_dict(self) -> Dict[str, Any]:
                data = dict(object.__getattribute__(self, "_base"))
                data.update(object.__getattribute__(self, "_overrides"))
                return data

        run_overrides: Dict[str, Any] = {
            "MODEL_NAME": effective_model,
            "LLM_MODEL_NAME": effective_model,
            "ATLAS_SESSION_ID": active_session,
            "ATLAS_ACTIVE_SESSION": active_session,
            "ATLAS_MEMORY_USER": active_session.split("/", 1)[0] if active_session else "",
            "ATLAS_IP_ID": ip,
            "ATLAS_ACTIVE_IP": ip,
            "ATLAS_WORKFLOW": workflow,
            "ACTIVE_WORKSPACE": workflow,
        }
        if effective_effort:
            run_overrides.update({
                "REASONING_MODE": effective_effort,
                "REASONING_EFFORT": effective_effort,
                "GLM_THINKING_TYPE": "disabled" if effective_effort == "none" else "enabled",
            })
        run_overrides.update(session_overrides)
        run_cfg = _RunCfg(_snapshot_config_module(), run_overrides)

        worker_memory_system = None
        if getattr(run_cfg, "ENABLE_MEMORY", False) or getattr(run_cfg, "ENABLE_MEMORY_RULES", True):
            try:
                from lib.memory import MemorySystem
                worker_memory_system = MemorySystem(
                    memory_dir=getattr(run_cfg, "MEMORY_DIR", ".memory"),
                    user=active_session,
                )
            except Exception as e:
                entry.add_log("system", f"memory unavailable: {e}", role="system")

        native_tools = None
        if getattr(run_cfg, "ENABLE_NATIVE_TOOL_CALLS", False):
            try:
                from core.tool_schema import get_tool_schemas
                native_tools = get_tool_schemas(
                    list(AVAILABLE_TOOLS.keys()),
                    compact=getattr(run_cfg, "TOOL_SCHEMA_COMPACT", False),
                )
            except Exception as e:
                entry.add_log("system", f"native tool schema unavailable: {e}", role="system")

        # ── System prompt (worker-appropriate) ──
        def _worker_build_prompt(messages, allowed_tools=None, agent_mode="normal"):
            """Build system prompt for worker: inject strong tool-calling
            instructions then delegate to the real prompt builder."""
            worker_guidance = (
                "You are an AI coding agent running as a headless Worker. "
                "Execute tasks using available tools.\n\n"
                "## CRITICAL: Final Answer REQUIRED\n\n"
                "Your VERY LAST response MUST contain EXACTLY:\n"
                "  Final Answer: <one-line summary of what you did>\n\n"
                "Without \"Final Answer:\" the coordinator sees an empty result.\n"
            )
            try:
                prompt = build_system_prompt(
                    messages,
                    cfg=run_cfg,
                    allowed_tools=allowed_tools,
                    agent_mode=agent_mode,
                    context=PromptContext(
                        memory_system=worker_memory_system,
                        todo_tracker=run_todo_tracker,
                    ),
                )
                if isinstance(prompt, str):
                    return apply_memory_override(
                        worker_guidance + "\n" + prompt,
                        worker_memory_system,
                        workflow=workflow,
                    )
                elif isinstance(prompt, dict):
                    # CACHE_OPTIMIZATION_MODE
                    if "static" in prompt:
                        prompt["static"] = apply_memory_override(
                            worker_guidance + "\n" + prompt.get("static", ""),
                            worker_memory_system,
                            workflow=workflow,
                        )
                    if "dynamic" in prompt:
                        prompt["dynamic"] = prompt.get("dynamic", "")
                    return prompt
                return prompt
            except Exception:
                return worker_guidance  # fallback

        # ── LLM call wrapper (inject model override) ──
        def _llm_call_fn(messages, stop=None, **kwargs):
            """Streaming LLM call with model/profile override.

            Yields ('reasoning', text) tuples and content strings.
            Forwards suppress_spinner, caller_tag, etc. to chat_completion_stream.
            """
            try:
                call_kwargs = dict(kwargs)
                if native_tools:
                    call_kwargs["tools"] = native_tools
                runtime_extra: Dict[str, Any] = {}
                if effective_effort:
                    runtime_extra.update({
                        "REASONING_MODE": effective_effort,
                        "REASONING_EFFORT": effective_effort,
                        "GLM_THINKING_TYPE": "disabled" if effective_effort == "none" else "enabled",
                    })
                # The orchestrator sends model identifiers such as "deepseek",
                # "kimi", and "gpt-5.3-codex".  Those are runtime profiles or
                # OAuth-backed model names, not necessarily valid model IDs for
                # the worker process' current provider.  Apply the same
                # thread-local runtime switch used by in-process subagents so
                # BASE_URL/API_KEY/MODEL_NAME move together per request.
                with config.scoped_model_runtime(effective_model):
                    with config.scoped_runtime_extra(runtime_extra):
                        active_model = getattr(config, "MODEL_NAME", effective_model)
                        entry.add_log(
                            "system",
                            f"LLM runtime active: model={active_model}"
                            + (f" effort={effective_effort}" if effective_effort else ""),
                            role="system",
                        )
                        for chunk in _worker_llm_client.chat_completion_stream(
                            messages, stop=stop, caller_tag="worker", **call_kwargs,
                        ):
                            yield chunk
            except Exception as e:
                entry.add_log("error", f"LLM call failed: {e}")
                raise

        # ── Compress wrapper ──
        def _compress_fn(messages, **kwargs):
            kwargs.pop("todo_tracker", None)
            return _compress_history(
                messages, cfg=run_cfg,
                llm_call_fn=_llm_call_fn,
                todo_tracker=run_todo_tracker,
                **kwargs,
            )

        # ── History save/load (same as main agent, per-worker session) ──
        from core.history_manager import (
            save_conversation_history as _save_hist,
            load_conversation_history as _load_hist,
        )

        def _save_history(messages, silent=True):
            _save_hist(messages, cfg=run_cfg, silent=silent)

        def _load_history():
            return _load_hist(cfg=run_cfg)

        # ── Show iteration warning (worker-adapted, no stdin) ──
        def _worker_iteration_warning(tracker, mode="oneshot"):
            """Simplified iteration warning: just stop at limit (no stdin)."""
            from lib.display import Color
            if tracker.should_warn():
                print(Color.warning(
                    f"\n[System] ⚠️  Approaching iteration limit "
                    f"({tracker.current}/{tracker.max_iterations})"
                ))
                print(Color.info(f"  {tracker.get_activity_summary()}"))
                print(Color.info("  Please wrap up the task.\n"))
                return "continue"
            elif tracker.is_limit_reached():
                print(Color.error(
                    f"\n[System] ❌ Maximum iterations reached "
                    f"({tracker.current}/{tracker.max_iterations})"
                ))
                print(Color.warning("  Stopping (worker mode).\n"))
                return "stop"
            return "continue"

        # ── ESC check: wire to cancel event ──
        def _esc_check():
            return entry._cancel_event.is_set()

        def _esc_start():
            pass  # No ESC watcher in worker

        def _esc_stop():
            pass

        # ── Build system prompt string (hardcoded for worker) ──
        def _worker_prompt_str(messages, **kwargs):
            worker_text = (
                "You are a headless Worker agent. "
                "Complete the task using available tools. "
                "Output 'Final Answer:' when done."
            )
            try:
                from core.prompt_builder import _build_system_prompt_str as _bsp
                return worker_text + "\n" + _bsp(messages, **kwargs)
            except Exception:
                return worker_text

        def _worker_get_llm_tokens():
            return (
                int(getattr(_worker_llm_client, "last_input_tokens", 0) or 0),
                int(getattr(_worker_llm_client, "last_output_tokens", 0) or 0),
            )

        def _worker_emit_tool_line(text: str) -> None:
            entry.add_log("action", str(text or ""), role="assistant")

        def _worker_emit_tool_result(obs, tool: str = "") -> None:
            entry.add_log("observation", str(obs or "")[:2000], role="tool")

        def _worker_emit_token(in_tok: int, cache_tok: int, out_tok: int) -> None:
            model_name = str(getattr(run_cfg, "MODEL_NAME", "") or effective_model or "")
            cost_delta = 0.0
            try:
                from lib.model_pricing import get_active_pricing
                price = get_active_pricing(model_name)
            except Exception:
                price = None
            if price is not None:
                billable_in = max(0, int(in_tok or 0) - int(cache_tok or 0))
                cost_delta = (
                    billable_in * float(price.input)
                    + int(cache_tok or 0) * float(price.cache)
                    + int(out_tok or 0) * float(price.output)
                ) / 1_000_000.0
            try:
                cost_file = str(getattr(run_cfg, "COST_FILE", "") or "")
                if cost_file:
                    cost_path = Path(cost_file)
                    cost_path.parent.mkdir(parents=True, exist_ok=True)
                    existing: Dict[str, Any] = {}
                    if cost_path.exists():
                        try:
                            existing = json.loads(cost_path.read_text(encoding="utf-8", errors="replace"))
                        except Exception:
                            existing = {}
                    cumulative_in = int(existing.get("in_tok", 0) or 0) + int(in_tok or 0)
                    cumulative_cache = int(existing.get("cache_tok", 0) or 0) + int(cache_tok or 0)
                    cumulative_out = int(existing.get("out_tok", 0) or 0) + int(out_tok or 0)
                    cumulative_cost = float(existing.get("cost_usd", 0) or 0) + float(cost_delta or 0)
                    cost_path.write_text(
                        json.dumps({
                            "in_tok": cumulative_in,
                            "cache_tok": cumulative_cache,
                            "out_tok": cumulative_out,
                            "sum_tok": cumulative_in + cumulative_out,
                            "cost_usd": cumulative_cost,
                            "last_in_tok": int(in_tok or 0),
                            "last_cache_tok": int(cache_tok or 0),
                            "last_out_tok": int(out_tok or 0),
                            "last_at": time.time(),
                            "model": model_name,
                            "updated_at": time.time(),
                        }, indent=2, ensure_ascii=False),
                        encoding="utf-8",
                    )
            except Exception:
                pass
            entry.add_log(
                "cost",
                (
                    f"tokens input={int(in_tok or 0)} cached={int(cache_tok or 0)} "
                    f"output={int(out_tok or 0)} cost_usd_delta={cost_delta:.8f} "
                    f"model={model_name}"
                ),
                role="system",
            )

        # ── Execute tool wrapper (bake in AVAILABLE_TOOLS like main.py does) ──
        def _execute_tool_fn(tool_name, args_str="", *, pre_parsed_kwargs=None):
            return _dispatch_tool(
                tool_name, args_str,
                pre_parsed_kwargs=pre_parsed_kwargs,
                available_tools=filtered_available_tools(),
                global_timeout=int(os.getenv("AGENT_SERVER_TOOL_TIMEOUT", "300")),
            )

        def _execute_parallel_fn(actions, tracker, agent_mode="normal"):
            return _execute_actions_parallel_impl(
                actions,
                tracker=tracker,
                agent_mode=agent_mode,
                cfg=run_cfg,
                execute_tool_fn=_execute_tool_fn,
            )

        # ── Snapshot / recovery (wired to per-worker session) ──
        def _noop_load(*a, **kw): return None
        def _noop_recovery(): return (None, None, None)

        # ── Build ReactLoopDeps ──
        max_iterations = int(os.getenv("AGENT_SERVER_MAX_ITERATIONS", "60"))
        tracker = IterationTracker(max_iterations=max_iterations)

        # Orchestrator chat injector — best-effort. Workers in process
        # mode have no direct bridge handle; the injector falls back to
        # the chat_consumed ledger and runs DB-only.
        try:
            from core.atlas_db import AtlasDB as _OrchDB
            from core.orchestrator_inject import (
                build_orchestrator_inject_fn,
                get_registered_bridge,
            )
            _orch_inject = build_orchestrator_inject_fn(
                _OrchDB(), get_registered_bridge()
            )
        except Exception:
            _orch_inject = None

        deps = ReactLoopDeps(
            cfg=run_cfg,
            llm_call_fn=_llm_call_fn,
            compress_fn=_compress_fn,
            build_prompt_fn=_worker_build_prompt,
            process_obs_fn=lambda obs, messages, todo_tracker=None, **kw: process_observation(
                obs, messages, todo_tracker=todo_tracker),
            execute_tool_fn=_execute_tool_fn,
            execute_parallel_fn=_execute_parallel_fn,
            save_trajectory_fn=_save_history,
            show_context_usage_fn=lambda messages: None,
            show_iteration_warning_fn=_worker_iteration_warning,
            strip_tokens_fn=_strip_native_tool_tokens,
            strip_thinking_fn=_strip_thinking_tags,
            parse_todo_fn=_parse_todo_markdown,
            detect_completion_fn=detect_completion_signal,
            get_turn_id_fn=lambda: 0,
            get_llm_usage_fn=_worker_llm_client.get_last_usage,
            get_llm_tokens_fn=_worker_get_llm_tokens,
            available_tools=filtered_available_tools(),
            # Optional subsystems — None for worker
            orchestrator=None,
            procedural_memory=None,
            graph_lite=None,
            hook_registry=_ws_hook_registry,
            inject_strategy_fn=None,
            save_snapshot_fn=None,
            load_snapshot_fn=None,
            build_prompt_str_fn=None,
            get_recovery_state_fn=None,
            poll_human_input_fn=None,
            orchestrator_inject_fn=_orch_inject,
            # ESC key — wire to cancel event
            esc_check_fn=_esc_check,
            esc_start_fn=_esc_start,
            esc_stop_fn=_esc_stop,
            # emit_* callbacks — route live worker telemetry to entry.add_log()
            emit_content_fn=None,    # worker: stdout goes to log via _flush hook
            emit_reasoning_fn=None,
            emit_todo_fn=None,
            emit_flush_fn=None,
            emit_token_fn=_worker_emit_token,
            emit_tool_fn=_worker_emit_tool_line,
            emit_tool_result_fn=_worker_emit_tool_result,
        )

        # ── Build initial messages (resume from saved history if available) ──
        messages = []
        existing = _load_history()
        if existing:
            messages = existing
            # Refresh system prompt in case workspace changed
            sys_prompt = _worker_build_prompt(messages, agent_mode="normal")
            if messages and messages[0].get("role") == "system":
                messages[0]["content"] = sys_prompt
            else:
                messages.insert(0, {"role": "system", "content": sys_prompt})
            entry.add_log("system", f"Resumed from saved history ({len(messages)} messages)", role="system")
        else:
            sys_prompt = _worker_build_prompt(messages, agent_mode="normal")
            messages.append({"role": "system", "content": sys_prompt})

        # ── Build single user message (merge context + task to avoid
        #    consecutive same-role messages that Z.AI rejects with code 1214) ──
        user_parts = []
        if context:
            user_parts.append(f"[Context]\n{context}")
            entry.add_log("context", context[:500], role="user")

        # If todos provided, load into tracker and format as task plan
        full_task = task
        if todos:
            entry._todos = todos
            if run_todo_tracker is not None:
                run_todo_tracker.clear()
                run_todo_tracker.add_todos(todos)
                run_todo_tracker.save()
            todo_text = "\n".join(
                f"  {i+1}. {t.get('content', t) if isinstance(t, dict) else t}"
                for i, t in enumerate(todos)
            )
            full_task += f"\n\nTask plan:\n{todo_text}"
            entry.add_log("plan", todo_text, role="user")

        user_parts.append(full_task)
        messages.append({"role": "user", "content": "\n\n".join(user_parts)})
        entry.add_log("task", full_task, role="user")

        direct_commands = _extract_direct_slash_commands(full_task)
        if direct_commands:
            closed_run, direct_output = _execute_direct_slash_commands(
                entry,
                direct_commands,
                project_root=project_root or _project_root,
                ip=ip,
            )
            if closed_run:
                return
            if direct_output:
                followup_context = (
                    "[Direct slash command observations]\n"
                    f"{direct_output[:8000]}\n\n"
                    "Continue this worker task using these observations. If the "
                    "stage driver requested LLM-authored RTL, author the missing "
                    "RTL artifacts now before finalizing."
                )
                messages[-1]["content"] += f"\n\n{followup_context}"
                entry.add_log("context", followup_context[:1200], role="system")

        # ── Run the full ReAct loop ──
        updated_messages, final_agent_mode = run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description=task,
            deps=deps,
            mode="oneshot",
            preface_enabled=False,   # No orchestrator/deep-think in worker
            agent_mode="normal",
            todo_tracker=run_todo_tracker,
        )

        # ── Populate entry.log from messages (observations, tool calls) ──
        files_modified = []
        files_examined = []
        tool_call_names: Dict[str, str] = {}

        def _extract_path_from_tool_args(raw_args: Any) -> str:
            """Best-effort path extraction from native JSON or ReAct args."""
            if isinstance(raw_args, dict):
                value = raw_args.get("path") or raw_args.get("file") or raw_args.get("directory")
                return str(value or "")
            raw = str(raw_args or "").strip()
            if not raw:
                return ""
            if raw.startswith("{"):
                try:
                    parsed = json.loads(raw)
                    if isinstance(parsed, dict):
                        value = parsed.get("path") or parsed.get("file") or parsed.get("directory")
                        if value:
                            return str(value)
                except Exception:
                    pass
            try:
                from core.action_parser import parse_tool_arguments
                parsed_args, parsed_kwargs = parse_tool_arguments(raw)
                value = parsed_kwargs.get("path") or parsed_kwargs.get("file") or parsed_kwargs.get("directory")
                if value:
                    return str(value)
                if parsed_args and isinstance(parsed_args[0], str):
                    return parsed_args[0]
            except Exception:
                pass
            match = _re.search(r'(?:path|file|directory)\s*[:=]\s*["\']([^"\']+)["\']', raw)
            if match:
                return match.group(1)
            return ""

        def _record_tool_path(tool_name: str, raw_args: Any, *, from_action: bool = False) -> None:
            path = _extract_path_from_tool_args(raw_args)
            if not path:
                return
            if tool_name in ("write_file", "write_to_file", "replace_in_file", "replace_lines", "replace_file_content"):
                files_modified.append(path)
            elif tool_name in ("read_file", "read_lines", "grep_file", "list_dir", "find_files"):
                files_examined.append(path)
            elif from_action and tool_name == "run_command":
                # Shell commands may generate reports. Keep them examined-only
                # here; actual modified-file detection is handled by write tools
                # or output parsing below.
                files_examined.append(path)

        def _record_wrote_paths_from_observation(text: str) -> None:
            # Tool scripts commonly report either "wrote path" or
            # "Successfully wrote to 'path'"; count both so producers are not
            # misclassified as silent failures after valid disk writes.
            patterns = (
                r'\bSuccessfully\s+wrote\s+to\s+[\'"]([^\'"]+)[\'"]',
                r'\bwrote\s+(?:to\s+)?[\'"]?([^\s\'",]+(?:\.[A-Za-z0-9_]+))[\'"]?',
            )
            for pattern in patterns:
                for match in _re.finditer(pattern, text, flags=_re.IGNORECASE):
                    path = match.group(1).strip().strip('",')
                    if path and not path.startswith("http"):
                        files_modified.append(path)

        # Scan messages for tool observations
        import re as _re
        for msg in updated_messages:
            role = msg.get("role", "")
            content = msg.get("content", "")

            if role == "assistant" and content:
                # Split into thought/action lines for log readability
                for line in str(content).split("\n"):
                    ls = line.strip()
                    if ls.startswith("Thought:"):
                        entry.add_log("thought", ls, role="assistant")
                    elif ls.startswith("Action:"):
                        entry.add_log("action", ls, role="assistant")
                    elif ls.startswith("Final Answer:") and ls.strip():
                        entry.add_log("response", ls[:300], role="assistant")
                    elif ls and not any(
                        k in ls for k in ["Thought:", "Action:"]
                    ):
                        entry.add_log("response", ls[:300], role="assistant")

                # Detect tool_calls in message dict
                tool_calls = msg.get("tool_calls", [])
                for tc in tool_calls:
                    tc_id = str(tc.get("id") or tc.get("tool_call_id") or "")
                    func = tc.get("function", {})
                    tname = func.get("name", "")
                    targs = func.get("arguments", "{}")
                    if tc_id and tname:
                        tool_call_names[tc_id] = tname
                    entry.add_log("tool_call", f"{tname}({str(targs)[:100]})",
                                  role="assistant")
                    _record_tool_path(tname, targs)

                # ReAct workers may emit textual Action: calls that are parsed
                # and executed by the loop without being stored as native
                # tool_calls. Count those too so producing workers are not
                # falsely marked as silent failures.
                try:
                    from core.action_parser import parse_all_actions
                    for tname, targs, _hint in parse_all_actions(str(content), debug=False):
                        _record_tool_path(tname, targs, from_action=True)
                except Exception:
                    pass

            elif role == "tool":
                tname = msg.get("name", "")
                if not tname:
                    tc_id = str(msg.get("tool_call_id") or "")
                    tname = tool_call_names.get(tc_id, "")
                entry.add_log("observation", str(content)[:500], role="tool")
                # Track files
                if isinstance(content, str):
                    _record_wrote_paths_from_observation(content)
                    fp_match = _re.search(r'["\']([^"\']+\.[a-zA-Z]+)["\']', content)
                    if fp_match:
                        fp = fp_match.group(1)
                        if tname in ("write_file", "replace_in_file", "replace_lines"):
                            files_modified.append(fp)
                        elif tname in ("read_file", "read_lines", "grep_file"):
                            files_examined.append(fp)

        # Extract final answer
        final_output = ""
        for msg in reversed(updated_messages):
            if msg.get("role") == "assistant":
                content = str(msg.get("content", ""))
                # Prefer "Final Answer:" line
                fa_match = _re.search(
                    r'Final Answer:\s*(.+)', content, _re.IGNORECASE
                )
                if fa_match:
                    final_output = fa_match.group(1).strip()
                else:
                    final_output = content[-2000:]  # Last 2k chars
                break

        # Silent-fail detection: producing workflows that emit 0 file writes
        # are almost always misclassified as "completed" — surface them as errors.
        _PRODUCING_WORKFLOWS = {
            "ssot-gen", "rtl-gen", "tb-gen", "fl-gen", "cl-gen",
            "sim", "sim_debug", "lint", "cov",
        }
        terminal_status = "completed"
        silent_fail_reason = ""
        wf_norm = (workflow or _SERVER_WORKFLOW or "").strip()
        had_writes = len(files_modified) > 0
        is_producing = wf_norm in _PRODUCING_WORKFLOWS
        leaked_action = bool(_re.search(
            r'(?im)^\s*(?:Thought:\s*)?Action:\s*(?:multi_tool_use\.parallel|[\w.]+)\s*\(',
            final_output,
        ))
        if is_producing and not had_writes:
            if leaked_action:
                terminal_status = "error"
                silent_fail_reason = (
                    f"action-leak: workflow={wf_norm} emitted unexecuted "
                    "Action text with 0 file writes"
                )
            elif tracker.current == 0:
                terminal_status = "error"
                silent_fail_reason = (
                    f"silent-fail: workflow={wf_norm} produced 0 tool calls "
                    f"and 0 file writes"
                )
            elif tracker.current >= 3:
                terminal_status = "error"
                silent_fail_reason = (
                    f"silent-fail: workflow={wf_norm} ran {tracker.current} "
                    f"tool calls but wrote 0 files"
                )

        # Build result
        entry.result = {
            "run_id": entry.run_id,
            "status": terminal_status,
            "result": final_output[:10000],
            "files_modified": list(set(files_modified)),
            "files_examined": list(set(files_examined)),
            "iterations": tracker.current,
            "todos_summary": _build_todos_summary(todos or [], entry),
        }
        if silent_fail_reason:
            entry.result["silent_fail_reason"] = silent_fail_reason
            entry.error = silent_fail_reason
        entry.status = terminal_status
        entry.finished_at = time.time()
        _on_status_change()
        elapsed = round(entry.finished_at - entry.started_at, 2)
        done_msg = (
            f"Completed in {elapsed}s, {tracker.current} iterations, "
            f"{len(files_modified)} files modified."
        )
        if silent_fail_reason:
            done_msg += f" [{silent_fail_reason}]"
        entry.add_log("done", done_msg)

        # Persist conversation history for next run / crash recovery
        _save_history(updated_messages, silent=False)

        # Fire webhook callback in background
        _fire_callback(entry)
        _write_run_log(entry)

    except Exception as e:
        entry.status = "error"
        entry.error = f"{e}\n{traceback.format_exc()}"
        entry.finished_at = time.time()
        _on_status_change()
        entry.add_log("error", f"Run failed: {e}")
        entry.result = {
            "run_id": entry.run_id,
            "status": "error",
            "result": "",
            "error": str(e),
            "files_modified": [],
            "files_examined": [],
            "iterations": 0,
        }
        _fire_callback(entry)
        _write_run_log(entry)
    finally:
        if _trace_runtime_prev is not None:
            try:
                from core.atlas_trace import pop_trace_runtime as _pop_trace_runtime
                _pop_trace_runtime(_trace_runtime_prev)
            except Exception:
                pass


# ─── FastAPI App ────────────────────────────────────────────────────────

def create_app():
    """Create and return the FastAPI application."""
    try:
        from fastapi import FastAPI, HTTPException, Query, Body
        from fastapi.responses import JSONResponse
    except ImportError:
        print("[agent_server] ERROR: fastapi not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(title="Common AI Agent Server", version="1.0.0")

    # ── API Key Auth (optional, opt-in via env var) ─────────────────
    _API_KEY = os.getenv("AGENT_SERVER_API_KEY", "")

    @app.middleware("http")
    async def auth_middleware(request, call_next):
        if _API_KEY and request.url.path != "/health":
            api_key = request.headers.get("X-API-Key", "")
            if api_key != _API_KEY:
                return JSONResponse(
                    status_code=401,
                    content={"detail": "Invalid or missing X-API-Key"},
                )
        return await call_next(request)

    # ── Pydantic models (auto-validates, generates OpenAPI) ────────
    try:
        from pydantic import BaseModel, Field
    except ImportError:
        BaseModel = None
        Field = None

    if BaseModel:
        class TodoItem(BaseModel):
            content: str
            status: str = "pending"

        class RunRequest(BaseModel):
            task: str
            model: str = ""
            reasoning_effort: str = ""
            todos: Optional[List[Any]] = None
            template: str = ""    # todo template name — loaded from workflow or CWD
            workflow: str = ""    # workflow name (e.g. "rtl-gen") — activates workspace
            session: str = ""     # per-run .session/<name> namespace
            ip: str = ""          # IP name for trace/workflow context
            project_root: str = ""
            rtl_version_id: str = ""
            artifact_versions: Any = None
            context: str = ""
            sync: bool = False

        class RegisterRequest(BaseModel):
            name: str
            url: str

    # Start cleanup thread (idempotent via module-level guard)
    global _cleanup_started
    if not _cleanup_started:
        _start_cleanup_thread()
        _cleanup_started = True

    # Restore runs from disk (survives server restart)
    _load_runs()
    _load_registry()

    @app.get("/health")
    async def health():
        """Liveness check.

        Exposes the worker's startup `workflow` binding plus a compact
        activity snapshot so the orchestrator UI can render live status
        without having to follow up with /runs and /metrics calls.
        """
        with _runs_lock:
            running_runs = [
                {
                    "run_id": r.run_id,
                    "iter": getattr(r, "iter_count", None) or getattr(r, "iter", None),
                    "started_at": getattr(r, "started_at", None),
                }
                for r in _runs.values()
                if getattr(r, "status", "") in ("running", "run", "pending")
            ]
            total_runs = len(_runs)
        body = {
            "status": "ok",
            "runs": total_runs,
            "running": running_runs[:3],
            "uptime_s": round(time.time() - _START_TIME, 1),
        }
        if _SERVER_WORKFLOW:
            body["workflow"] = _SERVER_WORKFLOW
        if _SERVER_ACCEPT_ANY_WORKFLOW:
            body["all_workflows"] = True
        # Best-effort model name — read from common env vars set at startup.
        model_name = (
            os.environ.get("LLM_MODEL_NAME", "")
            or os.environ.get("OPENCODE_MODEL", "")
            or os.environ.get("ATLAS_MODEL", "")
        ).strip()
        if model_name:
            body["model"] = model_name
        provider = os.environ.get("LLM_PROFILE", "").strip()
        if provider:
            body["profile"] = provider
        return body

    @app.get("/metrics")
    async def metrics():
        """
        Operational metrics.

        Returns run counts, success rate, uptime, and event counters.
        """
        now = time.time()
        uptime = round(now - _START_TIME, 2)
        with _runs_lock:
            total = len(_runs)
            running = pending = completed = error = cancelled = 0
            durations = []
            llm_calls = 0
            tool_calls = 0
            errors_count = 0
            for entry in _runs.values():
                if entry.status == "running":
                    running += 1
                elif entry.status == "pending":
                    pending += 1
                elif entry.status == "completed":
                    completed += 1
                    if entry.started_at and entry.finished_at:
                        durations.append(entry.finished_at - entry.started_at)
                elif entry.status == "error":
                    error += 1
                    errors_count += 1
                elif entry.status == "cancelled":
                    cancelled += 1
                # Count LLM and tool calls from log
                for log_entry in entry.log:
                    t = log_entry.get("type", "")
                    if t in ("thought", "action", "response", "completion", "tool_call"):
                        llm_calls += 1
                    if t == "tool_call":
                        tool_calls += 1
                    if t == "error":
                        errors_count += 1

        avg_duration_ms = 0.0
        if durations:
            avg_duration_ms = round(sum(durations) / len(durations) * 1000, 1)

        success_rate = 0.0
        successful = completed
        finished = completed + error + cancelled
        if finished > 0:
            success_rate = round(successful / finished * 100, 1)

        return {
            "uptime_s": uptime,
            "runs": {
                "total": total,
                "pending": pending,
                "running": running,
                "completed": completed,
                "error": error,
                "cancelled": cancelled,
            },
            "success_rate_pct": success_rate,
            "avg_duration_ms": avg_duration_ms,
            "events": {
                "llm_calls": llm_calls,
                "tool_calls": tool_calls,
                "errors": errors_count,
            },
        }

    @app.get("/runs")
    async def list_runs():
        """
        List all active runs (pending, running, completed, error, cancelled).

        Returns:
            {total, runs: [{run_id, status, task, elapsed_s, error}]}
        """
        now = time.time()
        with _runs_lock:
            run_list = []
            for run_id, entry in _runs.items():
                elapsed = 0.0
                if entry.started_at:
                    end = entry.finished_at or now
                    elapsed = round(end - entry.started_at, 2)
                run_list.append({
                    "run_id": entry.run_id,
                    "status": entry.status,
                    "task": entry.task[:120],
                    "elapsed_s": elapsed,
                    "error": entry.error[:200] if entry.error else None,
                })
        # Sort by created_at (oldest first) via run_id prefix
        run_list.sort(key=lambda r: r["run_id"])
        return {"total": len(run_list), "runs": run_list}

    @app.post("/cancel/{run_id}")
    async def cancel_run(run_id: str):
        """Cancel a pending or running task."""
        entry = _get_run(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")
        if entry.status in ("completed", "error", "cancelled"):
            raise HTTPException(status_code=409, detail=f"Run '{run_id}' already {entry.status}")
        _cancel_run(run_id)
        return {"run_id": run_id, "status": "cancelled"}

    @app.get("/workers")
    async def list_workers():
        """
        List all registered workers in the coordinator registry.

        Returns:
            {total, workers: [{name, url, registered_at}]}
        """
        with _runs_lock:
            workers = list(_worker_registry.values())
        return {"total": len(workers), "workers": workers}

    @app.post("/register")
    async def register_worker(request: Dict[str, Any] = Body(...)):
        """
        Register a worker with the coordinator.

        Request body:
            name (str): Worker name (e.g. 'lint_worker')
            url  (str): Worker URL (e.g. 'http://localhost:18797')

        Returns:
            {name, url, status: "registered"}
        """
        name = str(request.get("name", "")).strip()
        url = str(request.get("url", "")).strip()
        if not name:
            raise HTTPException(status_code=400, detail="'name' is required")
        if not url:
            raise HTTPException(status_code=400, detail="'url' is required")
        url = url.rstrip("/")
        entry = {"name": name, "url": url, "registered_at": time.time()}
        with _runs_lock:
            _worker_registry[name] = entry
        # Save registry alongside runs
        _save_registry()
        return {"name": name, "url": url, "status": "registered"}

    @app.post("/run")
    async def run_task(request: Dict[str, Any] = Body(...)):
        """
        Start a task on this worker agent.

        Request body:
            task (str):     Task description (required)
            model (str):    Model override (optional)
            todos (list):   Todo list to execute (optional)
            context (str):  Additional context (optional)
            sync (bool):    If true, block until done (default: false)

        Returns:
            {run_id, status} or full result if sync=true
        """
        task = str(request.get("task", ""))
        model = str(request.get("model", ""))
        reasoning_effort = str(request.get("reasoning_effort", "")).strip()
        todos = request.get("todos")
        template = str(request.get("template", ""))
        workflow = str(request.get("workflow", ""))
        session_raw = str(request.get("session", ""))
        session_name = normalize_session_name(session_raw)
        context = str(request.get("context", ""))
        sync = bool(request.get("sync", False))
        corr_in = str(request.get("trace_corr", "")).strip()
        ip_for_trace = str(request.get("ip", "")).strip() or "_unknown"
        try:
            from core.orchestrator_trace import record_trace, new_corr as _new_corr
            corr_eff = corr_in or _new_corr()
            actor_self = f"{_SERVER_WORKFLOW or 'worker'}-worker"
            record_trace(
                ip_for_trace, lens="interaction", actor=actor_self, peer="orchestrator",
                kind="http_recv", corr=corr_eff,
                requested_workflow=workflow or None, task_preview=task[:80],
                sync=sync, has_todos=bool(todos), template=template or None,
            )
        except Exception:
            corr_eff = corr_in or ""
        if not task:
            try:
                from core.orchestrator_trace import record_trace
                record_trace(ip_for_trace, lens="result", actor=actor_self, kind="http_rejected",
                             corr=corr_eff, status=400, detail="'task' is required")
            except Exception:
                pass
            raise HTTPException(status_code=400, detail="'task' is required")
        if session_raw.strip() and not session_name:
            raise HTTPException(status_code=400, detail="invalid 'session'")
        # Workflow binding guard: when this worker was started with
        # --workflow=<wf>, refuse /run requests for a different workflow so the
        # worker can be addressed as "the rtl-gen worker" or "the tb-gen worker"
        # without silently accepting cross-workflow work. See
        # doc/wiki/multi-user-worker-conflicts.md F3.
        if _SERVER_WORKFLOW and workflow.strip() and workflow.strip() != _SERVER_WORKFLOW:
            try:
                from core.orchestrator_trace import record_trace
                record_trace(ip_for_trace, lens="result", actor=actor_self, kind="http_rejected",
                             corr=corr_eff, status=403, bound=_SERVER_WORKFLOW,
                             requested=workflow.strip())
            except Exception:
                pass
            raise HTTPException(
                status_code=403,
                detail=(
                    f"worker is bound to workflow '{_SERVER_WORKFLOW}'; "
                    f"request asked for '{workflow.strip()}'"
                ),
            )
        # May-12 single-main-loop pattern: when --all-workflows is on, each
        # dispatch carries its own workflow; activate the workspace at the
        # process level (env + workflow.loader) before _run_react_task so the
        # same main loop transitions to the new workflow's context on the
        # next iteration. The per-run workspace activation inside
        # _run_react_task still runs and patches prompt/hooks for this task.
        if _SERVER_ACCEPT_ANY_WORKFLOW and workflow.strip():
            try:
                _wf_norm = workflow.strip()
                os.environ["ATLAS_WORKFLOW"] = _wf_norm
                os.environ["ACTIVE_WORKSPACE"] = _wf_norm
                try:
                    import src.main as _main_mod
                    _setup_ws = getattr(_main_mod, "_setup_workspace", None)
                except Exception:
                    _setup_ws = None
                if _setup_ws is None:
                    try:
                        import main as _main_mod
                        _setup_ws = getattr(_main_mod, "_setup_workspace", None)
                    except Exception:
                        _setup_ws = None
                if callable(_setup_ws):
                    _setup_ws(_wf_norm)
            except SystemExit:
                # _setup_workspace calls sys.exit() on unknown workflow;
                # convert that into an HTTP 400 so the worker keeps running.
                raise HTTPException(
                    status_code=400,
                    detail=f"unknown workflow '{workflow.strip()}'",
                )
            except Exception as _ws_exc:
                # Workspace activation is best-effort; _run_react_task will
                # still attempt its own activation. Log to trace and continue.
                try:
                    from core.orchestrator_trace import record_trace
                    record_trace(ip_for_trace, lens="result", actor=actor_self,
                                 kind="workspace_setup_warn", corr=corr_eff,
                                 workflow=workflow.strip(), detail=str(_ws_exc)[:200])
                except Exception:
                    pass
        template_ip = str(request.get("ip", "")).strip()
        project_root = str(request.get("project_root", "")).strip()
        rtl_version_id = str(request.get("rtl_version_id", "")).strip()
        artifact_versions = request.get("artifact_versions") or []
        if (
            not todos
            and template == "ssot-rtl"
            and (workflow.strip() == "rtl-gen" or str(request.get("stage_id", "")).strip() == "rtl")
        ):
            print(
                "[template] Skipping dynamic 'ssot-rtl' todo preload for rtl-gen; "
                "worker will execute /ssot-rtl and read RTL ledgers from disk"
            )
            template = ""
        if not template_ip and session_name:
            parts = [p for p in session_name.split("/") if p]
            known = {
                "architect", "coverage", "fl-model-gen", "goal-audit", "lint",
                "mas-gen", "rtl-gen", "signoff", "sim", "sim_debug", "ssot-gen", "tb-gen",
            }
            if len(parts) >= 3 and parts[-1] in known:
                template_ip = parts[-2].strip()
            elif len(parts) >= 2 and parts[-1] in known:
                template_ip = parts[0].strip()
            else:
                template_ip = parts[0].strip() if parts else ""
        if template and not todos:
            todos = _load_todo_template(template, workflow, template_ip)
            if todos is None:
                raise HTTPException(status_code=404, detail=f"Template '{template}' not found")
        entry = _create_run(task, model)
        entry.on_complete_url = str(request.get("on_complete_url", ""))
        if sync:
            _run_react_task(
                entry, task, model, todos, context, workflow, session_name,
                template_ip, rtl_version_id, project_root, artifact_versions,
                reasoning_effort,
            )
            return entry.result
        acquired = _concurrency_semaphore.acquire(blocking=False)
        if not acquired:
            raise HTTPException(
                status_code=429,
                detail="Too many concurrent runs. Try again later.",
                headers={"Retry-After": "5"},
            )
        def _wrapped_run():
            try:
                _run_react_task(
                    entry, task, model, todos, context, workflow, session_name,
                    template_ip, rtl_version_id, project_root, artifact_versions,
                    reasoning_effort,
                )
                try:
                    from core.orchestrator_trace import record_trace
                    record_trace(template_ip or ip_for_trace, lens="result",
                                 actor=actor_self, kind="run_completed",
                                 corr=corr_eff, run_id=entry.run_id,
                                 status=getattr(entry, "status", "unknown"))
                except Exception:
                    pass
            finally:
                _concurrency_semaphore.release()
        _executor.submit(_wrapped_run)
        try:
            from core.orchestrator_trace import record_trace
            record_trace(template_ip or ip_for_trace, lens="interaction",
                         actor=actor_self, peer="orchestrator",
                         kind="http_accepted", corr=corr_eff,
                         status=200, run_id=entry.run_id)
        except Exception:
            pass
        return {"run_id": entry.run_id, "status": "pending", "trace_corr": corr_eff}

    @app.get("/status/{run_id}")
    async def get_status(run_id: str):
        """Get current progress of a run."""
        entry = _get_run(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        elapsed = 0.0
        if entry.started_at:
            end = entry.finished_at or time.time()
            elapsed = round(end - entry.started_at, 2)

        return {
            "run_id": entry.run_id,
            "status": entry.status,
            "task": entry.task[:100],
            "log_entries": len(entry.log),
            "elapsed_s": elapsed,
            "error": entry.error,
        }

    @app.get("/result/{run_id}")
    async def get_result(run_id: str):
        """Get final result of a completed run."""
        entry = _get_run(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        if entry.status in ("pending", "running"):
            return {
                "run_id": entry.run_id,
                "status": entry.status,
                "result": None,
                "message": "Still running. Poll /status or wait for completion.",
            }

        return entry.result

    @app.get("/log/{run_id}")
    async def get_log(run_id: str, tail: int = Query(default=0, ge=0),
                      since: int = Query(default=0, ge=0)):
        """
        Get the ReAct transcript for a run.

        Query params:
            tail (int):  Return only last N entries (0 = all)
            since (int): Return entries with index >= N (for delta polling)
        """
        entry = _get_run(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        entries = entry.get_log(since=since, tail=tail)
        return {
            "run_id": entry.run_id,
            "status": entry.status,
            "total_entries": len(entry.log),
            "entries": entries,
        }

    @app.get("/log/{run_id}/stream")
    async def stream_log(run_id: str):
        """
        Server-Sent Events stream of the ReAct transcript.

        Real-time push — no polling. Connect with:
            curl -N http://localhost:8000/log/{run_id}/stream

        Each event is a JSON line: data: {type, content, ...}
        """
        entry = _get_run(run_id)
        if not entry:
            raise HTTPException(status_code=404, detail=f"Run '{run_id}' not found")

        from fastapi.responses import StreamingResponse

        async def event_generator():
            sent_idx = 0
            while True:
                # Send any new entries since last check
                entries = entry.get_log(since=sent_idx)
                for e in entries:
                    data = json.dumps({
                        "index": e["index"],
                        "type": e["type"],
                        "role": e.get("role", ""),
                        "content": e["content"],
                        "timestamp": e["timestamp"],
                    })
                    yield f"data: {data}\n\n"
                    sent_idx = e["index"] + 1

                # If run is done, send final event and exit
                if entry.status in ("completed", "error", "cancelled"):
                    yield f"event: done\ndata: {{\"status\": \"{entry.status}\"}}\n\n"
                    break

                # Wait for new entries (wake every 1s to check for timeout)
                entry._log_event.wait(timeout=1.0)
                entry._log_event.clear()

        return StreamingResponse(
            event_generator(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
                "X-Accel-Buffering": "no",  # Disable nginx buffering
            },
        )

    return app


# ─── Server Entrypoint ──────────────────────────────────────────────────

def serve(port: int = 8000, host: str = "0.0.0.0", verbose: bool = False,
          coordinator: str = "", worker_name: str = "",
          session_name: str = "", startup_workflow: str = "",
          all_workflows: bool = False):
    """
    Start the agent HTTP server.

    This is called by main.py when --serve flag is used.

    Args:
        port:             HTTP port
        host:             Bind address
        verbose:          Print ReAct log to terminal in real-time
        coordinator:      Coordinator URL to register with (e.g. http://localhost:8000)
        worker_name:      Name this worker registers as (e.g. 'lint_worker')
        startup_workflow: Workflow this worker is bound to (`--workflow` arg).
                          When set, /run requests whose `workflow` field does not
                          match are rejected with 403 to prevent cross-workflow
                          worker reuse (multi-user-worker-conflicts F3).
        all_workflows:    When True (`--all-workflows`), the worker is workflow-
                          agnostic: the 403 workflow-mismatch gate is bypassed
                          and each /run dispatches into _setup_workspace(workflow)
                          before running, restoring the May-12 single-main-loop
                          pattern where one worker handles every workflow.
    """
    global _VERBOSE, _VERBOSE_FILTER, _SERVER_PORT, _SERVER_WORKFLOW
    global _SERVER_ACCEPT_ANY_WORKFLOW, _worker_todo_tracker
    _SERVER_ACCEPT_ANY_WORKFLOW = bool(all_workflows)
    # --all-workflows is mutually exclusive with workflow binding: an
    # any-workflow worker must not reject mismatched dispatches.
    _SERVER_WORKFLOW = "" if _SERVER_ACCEPT_ANY_WORKFLOW else (startup_workflow or "").strip()
    _VERBOSE = verbose or os.getenv("AGENT_SERVER_VERBOSE", "").lower() in ("1", "true", "yes")
    _VERBOSE_FILTER = os.getenv("AGENT_SERVER_VERBOSE_FILTER", "")
    _SERVER_PORT = port

    # ── Session setup (same as main agent) ──
    try:
        from core.session_setup import setup_session
        import config as _cfg
        from lib.todo_tracker import TodoTracker
        active_session = session_name or f"worker_{port}"
        setup_session(active_session)
        _worker_todo_tracker = TodoTracker.load(Path(_cfg.TODO_FILE)) if _cfg.ENABLE_TODO_TRACKING else None
        # Expose via main module so _get_todo_tracker() in tools.py finds it
        try:
            import src.main as _main_mod
        except Exception:
            try:
                import main as _main_mod
            except Exception:
                _main_mod = None
        if _main_mod is not None:
            _main_mod.todo_tracker = _worker_todo_tracker
        print(f"[worker_{port}] Session: .session/{active_session}/")
    except Exception as _e:
        print(f"[worker_{port}] WARNING: session init failed: {_e}")

    # Auto-register with coordinator on startup
    if coordinator and worker_name:
        coordinator = coordinator.rstrip("/")
        this_url = f"http://localhost:{port}"
        try:
            body = json.dumps({"name": worker_name, "url": this_url}).encode("utf-8")
            req = urllib.request.Request(
                f"{coordinator}/register", data=body,
                headers={"Content-Type": "application/json"}, method="POST")
            with urllib.request.urlopen(req, timeout=5) as resp:
                result = json.loads(resp.read().decode("utf-8"))
            print(f"[registry] Registered as '{worker_name}' → {coordinator}")
        except Exception as e:
            print(f"[registry] WARNING: Failed to register with {coordinator}: {e}")
    try:
        import uvicorn
    except ImportError:
        print("[agent_server] ERROR: uvicorn not installed. Install with: pip install uvicorn")
        sys.exit(1)

    print(f"""
╔══════════════════════════════════════════════════╗
║       Common AI Agent Server                     ║
║                                                  ║
║   Host: {host:<40s}║
║   Port: {port:<40d}║
║                                                  ║
║   Endpoints:                                     ║
║     POST /run          Start a task              ║
║     GET  /runs          List all runs             ║
║     GET  /status/{{id}}  Poll progress            ║
║     GET  /result/{{id}}  Get final output          ║
║     GET  /log/{{id}}     Get ReAct transcript     ║
║     GET  /health        Liveness check            ║
║                                                  ║
║   Waiting for tasks...                           ║
╚══════════════════════════════════════════════════╝
""")
    try:
        import config
        print(f"  Model: {config.MODEL_NAME}")
        print(f"  Provider: {config.BASE_URL}")
    except Exception:
        pass

    app = create_app()
    uvicorn.run(app, host=host, port=port, log_level="info")
