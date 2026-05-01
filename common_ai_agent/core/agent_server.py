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


# ─── Data Models ─────────────────────────────────────────────────────────

@dataclass
class RunEntry:
    """Tracks a single /run invocation."""
    run_id: str
    status: str = "pending"          # pending → running → completed / error
    task: str = ""
    model: str = ""
    result: Optional[Dict] = None
    log: List[Dict] = field(default_factory=list)     # ReAct transcript
    created_at: float = 0.0
    started_at: Optional[float] = None
    finished_at: Optional[float] = None
    error: Optional[str] = None
    on_complete_url: str = ""        # Webhook callback URL
    _lock: threading.Lock = field(default_factory=threading.Lock)
    _cancel_event: threading.Event = field(default_factory=threading.Event)
    _log_event: threading.Event = field(default_factory=threading.Event)

    def add_log(self, entry_type: str, content: str, role: str = ""):
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

    def get_log(self, since: int = 0, tail: int = 0) -> List[Dict]:
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
_worker_registry: Dict[str, dict] = {}
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
        print(f"  {icon} [{short_id}] \033[1;36m{preview}\033[0m")
    elif entry_type == "error":
        print(f"  {icon} [{short_id}] \033[1;31m{preview}\033[0m")
    elif entry_type in ("completion", "done"):
        print(f"  {icon} [{short_id}] \033[1;32m{preview}\033[0m")
    elif entry_type == "iteration":
        print(f"\n{icon} [{short_id}] {preview}")
    else:
        print(f"  {icon} [{short_id}] {preview}")


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


def _fire_callback(entry: RunEntry):
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


def _write_run_log(entry: RunEntry):
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
        }, indent=2, default=str))
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
        tmp.write_text(json.dumps(data, indent=2, default=str))
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
        data = json.loads(_PERSISTENCE_FILE.read_text())
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
        tmp.write_text(json.dumps(data, indent=2))
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
        data = json.loads(_REGISTRY_FILE.read_text())
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


def _load_todo_template(name: str, workflow: str = "") -> Optional[list]:
    """Load tasks from a todo template JSON file.

    Search order:
      1. workflow/<workflow>/todo_templates/<name>.json  (if workflow given)
      2. todo_templates/<name>.json                      (CWD fallback)

    Returns the tasks list on success, None if not found.
    """
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
                tasks = data.get("tasks", data if isinstance(data, list) else None)
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
                     todos: list = None, context: str = "",
                     workflow: str = "") -> None:
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

    _ws_hook_registry = None  # populated by workspace activation if script_hooks defined

    # ── Activate workspace if specified (full main-agent parity) ─────────
    if workflow:
        try:
            from workflow.loader import (
                load_workspace, merge_prompt, patch_todo_rules,
                register_script_hooks, get_todo_template_registry,
            )
            import builtins as _b
            import core.compressor as _comp

            ws = load_workspace(workflow, project_root=Path(_project_root))

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
                        return merge_prompt(base, _ws_sys_text, _ws_sys_mode)

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
        import config
        from core.react_loop import ReactLoopDeps, run_react_agent_impl
        from core.compressor import compress_history as _compress_history
        from core.prompt_builder import build_system_prompt
        from core.observation_processor import process_observation
        from core.action_parser import _strip_native_tool_tokens, _strip_thinking_tags
        from core.tools import AVAILABLE_TOOLS
        from core.tool_dispatcher import dispatch_tool as _dispatch_tool
        from core.parallel_executor import execute_actions_parallel
        from lib.iteration_control import (
            IterationTracker, detect_completion_signal,
        )
        from lib.todo_tracker import _parse_todo_markdown
        from src.llm_client import (
            chat_completion_stream, get_last_usage,
            last_input_tokens, last_output_tokens,
        )

        # ── Model override ──
        effective_model = model or config.MODEL_NAME

        # ── Build config wrapper (override MODEL_NAME for this run) ──
        class _RunCfg:
            """Delegate all config lookups to the real config module,
            with MODEL_NAME overridden for per-run model selection."""
            def __getattr__(self, name):
                if name == "MODEL_NAME":
                    return effective_model
                return getattr(config, name)

        run_cfg = _RunCfg()

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
                )
                if isinstance(prompt, str):
                    return worker_guidance + "\n" + prompt
                elif isinstance(prompt, dict):
                    # CACHE_OPTIMIZATION_MODE
                    if "static" in prompt:
                        prompt["static"] = worker_guidance + "\n" + prompt.get("static", "")
                    if "dynamic" in prompt:
                        prompt["dynamic"] = prompt.get("dynamic", "")
                    return prompt
                return prompt
            except Exception:
                return worker_guidance  # fallback

        # ── LLM call wrapper (inject model override) ──
        def _llm_call_fn(messages, stop=None, **kwargs):
            """Streaming LLM call with model override.

            Yields ('reasoning', text) tuples and content strings.
            Forwards suppress_spinner, caller_tag, etc. to chat_completion_stream.
            """
            try:
                for chunk in chat_completion_stream(
                    messages, stop=stop, model=effective_model,
                    caller_tag="worker", **kwargs,
                ):
                    yield chunk
            except Exception as e:
                entry.add_log("error", f"LLM call failed: {e}")
                raise

        # ── Compress wrapper ──
        def _compress_fn(messages, **kwargs):
            return _compress_history(
                messages, cfg=run_cfg,
                llm_call_fn=_llm_call_fn,
                todo_tracker=_worker_todo_tracker,
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

        # ── Execute tool wrapper (bake in AVAILABLE_TOOLS like main.py does) ──
        def _execute_tool_fn(tool_name, args_str="", *, pre_parsed_kwargs=None):
            return _dispatch_tool(
                tool_name, args_str,
                pre_parsed_kwargs=pre_parsed_kwargs,
                available_tools=AVAILABLE_TOOLS,
                global_timeout=int(os.getenv("AGENT_SERVER_TOOL_TIMEOUT", "300")),
            )

        # ── Snapshot / recovery (wired to per-worker session) ──
        def _noop_load(*a, **kw): return None
        def _noop_recovery(): return (None, None, None)

        # ── Build ReactLoopDeps ──
        max_iterations = int(os.getenv("AGENT_SERVER_MAX_ITERATIONS", "60"))
        tracker = IterationTracker(max_iterations=max_iterations)

        deps = ReactLoopDeps(
            cfg=run_cfg,
            llm_call_fn=_llm_call_fn,
            compress_fn=_compress_fn,
            build_prompt_fn=_worker_build_prompt,
            process_obs_fn=lambda obs, messages, todo_tracker=None, **kw: process_observation(
                obs, messages, todo_tracker=todo_tracker),
            execute_tool_fn=_execute_tool_fn,
            execute_parallel_fn=execute_actions_parallel,
            save_trajectory_fn=_save_history,
            show_context_usage_fn=lambda messages: None,
            show_iteration_warning_fn=_worker_iteration_warning,
            strip_tokens_fn=_strip_native_tool_tokens,
            strip_thinking_fn=_strip_thinking_tags,
            parse_todo_fn=_parse_todo_markdown,
            detect_completion_fn=detect_completion_signal,
            get_turn_id_fn=lambda: 0,
            get_llm_usage_fn=get_last_usage,
            get_llm_tokens_fn=lambda: (last_input_tokens, last_output_tokens),
            available_tools=AVAILABLE_TOOLS,
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
            # ESC key — wire to cancel event
            esc_check_fn=_esc_check,
            esc_start_fn=_esc_start,
            esc_stop_fn=_esc_stop,
            # emit_* callbacks — route stream output to entry.add_log()
            emit_content_fn=None,    # worker: stdout goes to log via _flush hook
            emit_reasoning_fn=None,
            emit_todo_fn=None,
            emit_flush_fn=None,
            emit_token_fn=None,
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

        if context:
            messages.append({"role": "user", "content": f"[Context]\n{context}"})
            entry.add_log("context", context[:500], role="user")

        # If todos provided, load into tracker and format as task plan
        full_task = task
        if todos:
            entry._todos = todos
            if _worker_todo_tracker is not None:
                _worker_todo_tracker.clear()
                _worker_todo_tracker.add_todos(todos)
                _worker_todo_tracker.save()
            todo_text = "\n".join(
                f"  {i+1}. {t.get('content', t) if isinstance(t, dict) else t}"
                for i, t in enumerate(todos)
            )
            full_task += f"\n\nTask plan:\n{todo_text}"
            entry.add_log("plan", todo_text, role="user")

        messages.append({"role": "user", "content": full_task})
        entry.add_log("task", full_task, role="user")

        # ── Run the full ReAct loop ──
        updated_messages, final_agent_mode = run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description=task,
            deps=deps,
            mode="oneshot",
            preface_enabled=False,   # No orchestrator/deep-think in worker
            agent_mode="normal",
            todo_tracker=_worker_todo_tracker,
        )

        # ── Populate entry.log from messages (observations, tool calls) ──
        files_modified = []
        files_examined = []
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
                    func = tc.get("function", {})
                    tname = func.get("name", "")
                    targs = func.get("arguments", "{}")
                    entry.add_log("tool_call", f"{tname}({str(targs)[:100]})",
                                  role="assistant")

            elif role == "tool":
                tname = msg.get("name", "")
                entry.add_log("observation", str(content)[:500], role="tool")
                # Track files
                if isinstance(content, str):
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

        # Build result
        entry.result = {
            "run_id": entry.run_id,
            "status": "completed",
            "result": final_output[:10000],
            "files_modified": list(set(files_modified)),
            "files_examined": list(set(files_examined)),
            "iterations": tracker.current,
            "todos_summary": _build_todos_summary(todos or [], entry),
        }
        entry.status = "completed"
        entry.finished_at = time.time()
        _on_status_change()
        elapsed = round(entry.finished_at - entry.started_at, 2)
        entry.add_log("done",
                      f"Completed in {elapsed}s, {tracker.current} iterations, "
                      f"{len(files_modified)} files modified.")

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
            todos: Optional[list] = None
            template: str = ""    # todo template name — loaded from workflow or CWD
            workflow: str = ""    # workflow name (e.g. "rtl-gen") — activates workspace
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
        """Liveness check."""
        return {"status": "ok", "runs": len(_runs)}

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
    async def register_worker(request: 'RegisterRequest' if BaseModel else dict):
        """
        Register a worker with the coordinator.

        Request body:
            name (str): Worker name (e.g. 'lint_worker')
            url  (str): Worker URL (e.g. 'http://localhost:18797')

        Returns:
            {name, url, status: "registered"}
        """
        if BaseModel and isinstance(request, BaseModel):
            name = request.name
            url = request.url
        else:
            name = request.get("name", "").strip()
            url = request.get("url", "").strip()
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

    if BaseModel:

        @app.post("/run")
        async def run_task(request: RunRequest):
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
            task = request.task
            model = request.model
            todos = request.todos
            template = request.template
            workflow = request.workflow
            context = request.context
            sync = request.sync
            if not task:
                raise HTTPException(status_code=400, detail="'task' is required")
            if template and not todos:
                todos = _load_todo_template(template, workflow)
                if todos is None:
                    raise HTTPException(status_code=404, detail=f"Template '{template}' not found")
            entry = _create_run(task, model)
            entry.on_complete_url = getattr(request, "on_complete_url", "")
            if sync:
                _run_react_task(entry, task, model, todos, context, workflow)
                return entry.result
            else:
                acquired = _concurrency_semaphore.acquire(blocking=False)
                if not acquired:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many concurrent runs. Try again later.",
                        headers={"Retry-After": "5"},
                    )
                def _wrapped_run():
                    try:
                        _run_react_task(entry, task, model, todos, context, workflow)
                    finally:
                        _concurrency_semaphore.release()
                _executor.submit(_wrapped_run)
                return {"run_id": entry.run_id, "status": "pending"}

    else:

        @app.post("/run")
        async def run_task(request: dict = Body(...)):
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
            task = request.get("task", "")
            model = request.get("model", "")
            todos = request.get("todos")
            template = request.get("template", "")
            workflow = request.get("workflow", "")
            context = request.get("context", "")
            sync = request.get("sync", False)
            if not task:
                raise HTTPException(status_code=400, detail="'task' is required")
            if template and not todos:
                todos = _load_todo_template(template, workflow)
                if todos is None:
                    raise HTTPException(status_code=404, detail=f"Template '{template}' not found")
            entry = _create_run(task, model)
            entry.on_complete_url = request.get("on_complete_url", "")
            if sync:
                _run_react_task(entry, task, model, todos, context, workflow)
                return entry.result
            else:
                acquired = _concurrency_semaphore.acquire(blocking=False)
                if not acquired:
                    raise HTTPException(
                        status_code=429,
                        detail="Too many concurrent runs. Try again later.",
                        headers={"Retry-After": "5"},
                    )
                def _wrapped_run():
                    try:
                        _run_react_task(entry, task, model, todos, context, workflow)
                    finally:
                        _concurrency_semaphore.release()
                _executor.submit(_wrapped_run)
                return {"run_id": entry.run_id, "status": "pending"}

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
          coordinator: str = "", worker_name: str = ""):
    """
    Start the agent HTTP server.

    This is called by main.py when --serve flag is used.

    Args:
        port:        HTTP port
        host:        Bind address
        verbose:     Print ReAct log to terminal in real-time
        coordinator: Coordinator URL to register with (e.g. http://localhost:8000)
        worker_name: Name this worker registers as (e.g. 'lint_worker')
    """
    global _VERBOSE, _VERBOSE_FILTER, _SERVER_PORT, _worker_todo_tracker
    _VERBOSE = verbose or os.getenv("AGENT_SERVER_VERBOSE", "").lower() in ("1", "true", "yes")
    _VERBOSE_FILTER = os.getenv("AGENT_SERVER_VERBOSE_FILTER", "")
    _SERVER_PORT = port

    # ── Session setup (same as main agent) ──
    try:
        from core.session_setup import setup_session
        import config as _cfg
        from lib.todo_tracker import TodoTracker
        setup_session(f"worker_{port}")
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
        print(f"[worker_{port}] Session: .session/worker_{port}/")
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
