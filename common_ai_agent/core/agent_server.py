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
    _lock: threading.Lock = field(default_factory=threading.Lock)

    def add_log(self, entry_type: str, content: str, role: str = ""):
        """Thread-safe log append."""
        with self._lock:
            self.log.append({
                "index": len(self.log),
                "type": entry_type,
                "role": role,
                "content": content,
                "timestamp": time.time(),
            })

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
_executor = ThreadPoolExecutor(max_workers=8)


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


# ─── ReAct Loop Wrapper ────────────────────────────────────────────────

def _run_react_task(entry: RunEntry, task: str, model: str = "",
                     todos: list = None, context: str = "") -> None:
    """
    Execute a full ReAct loop for the given task, logging each step into entry.log.
    This runs in a worker thread so the HTTP endpoint can return immediately.
    """
    entry.status = "running"
    entry.started_at = time.time()
    entry.add_log("system", "ReAct loop starting...", role="system")

    try:
        import config
        from llm_client import call_llm_raw
        from core import tools as tools_module
        from core.action_parser import parse_all_actions, _strip_native_tool_tokens
        from core.tool_dispatcher import dispatch_tool
        from lib.todo_tracker import TodoTracker
        from lib.iteration_control import detect_completion_signal

        # Override model if specified
        effective_model = model or config.MODEL_NAME

        # Build system prompt
        system_prompt = "You are an AI coding agent. Execute the task using available tools.\n"
        system_prompt += "Use the ReAct format:\nThought: <reasoning>\nAction: tool_name(args)\n"
        system_prompt += "When done, provide a final summary without any Action:."

        # Build messages
        messages = [{"role": "system", "content": system_prompt}]
        if context:
            messages.append({"role": "user", "content": f"[Context]\n{context}"})
            entry.add_log("context", context[:500], role="user")

        # If todos provided, format as task plan
        full_task = task
        if todos:
            todo_text = "\n".join(f"  {i+1}. {t.get('content', t) if isinstance(t, dict) else t}"
                                  for i, t in enumerate(todos))
            full_task += f"\n\nTask plan:\n{todo_text}"
            entry.add_log("plan", todo_text, role="user")

        messages.append({"role": "user", "content": full_task})
        entry.add_log("task", full_task, role="user")

        # ReAct loop
        max_iterations = int(os.getenv("AGENT_SERVER_MAX_ITERATIONS", "30"))
        iteration = 0
        files_modified = []
        files_examined = []
        all_observations = []

        while iteration < max_iterations:
            iteration += 1
            entry.add_log("iteration", f"--- Iteration {iteration}/{max_iterations} ---")

            # Call LLM
            try:
                collected = call_llm_raw(
                    prompt="",
                    messages=messages,
                    stop=["Observation:"],
                    model=effective_model,
                ) or ""
            except Exception as e:
                entry.add_log("error", f"LLM call failed: {e}")
                break

            # Clean native tool tokens
            collected = _strip_native_tool_tokens(collected)

            # Log the LLM response (split Thought/Action for readability)
            for line in collected.split("\n"):
                line_stripped = line.strip()
                if line_stripped.startswith("Thought:"):
                    entry.add_log("thought", line_stripped, role="assistant")
                elif line_stripped.startswith("Action:"):
                    entry.add_log("action", line_stripped, role="assistant")
                elif line_stripped.startswith("Final Answer:") or (not line_stripped.startswith("Observation:") and line_stripped):
                    if not any(k in line_stripped for k in ["Thought:", "Action:"]):
                        entry.add_log("response", line_stripped[:200], role="assistant")

            messages.append({"role": "assistant", "content": collected})

            # Parse actions
            actions = parse_all_actions(collected)

            # Check for completion
            if not actions:
                if detect_completion_signal(collected):
                    entry.add_log("completion", "Agent signaled completion.")
                    break
                else:
                    entry.add_log("completion", "No actions found. Assuming done.")
                    break

            # Execute actions
            combined_results = []
            for tool_name, args_str, *hint in actions:
                entry.add_log("tool_call", f"{tool_name}({args_str[:100]})", role="assistant")

                try:
                    observation = dispatch_tool(
                        tool_name, args_str,
                        available_tools=tools_module.AVAILABLE_TOOLS,
                        global_timeout=300,
                    )
                except Exception as e:
                    observation = f"Error: {e}"

                # Track file ops
                import re
                # Extract file path from args — handles:
                #   path="foo.txt"    (keyword style)
                #   "path": "foo.txt" (JSON style)
                #   "foo.txt"         (positional — first quoted string)
                # Match: path="f" | "path": "f" | path=f (unquoted)
                path_match = re.search(r'(?:path\s*=\s*|"path"\s*:\s*)(?:["\']([^"\']+)["\']|(\S+))', args_str)
                if not path_match:
                    # Fallback: first quoted string (positional arg)
                    path_match = re.search(r'["\']([^"\']+)["\']', args_str)
                if path_match:
                    fp = path_match.group(1) or path_match.group(2) or ''
                    # Only count if it looks like a file path (has extension or /)
                    if fp and ('.' in fp or '/' in fp):
                        if tool_name in ("write_file", "replace_in_file", "replace_lines"):
                            files_modified.append(fp)
                        elif tool_name in ("read_file", "read_lines", "grep_file"):
                            files_examined.append(fp)

                # Log observation (truncated)
                obs_preview = str(observation)[:300]
                entry.add_log("observation", obs_preview, role="tool")

                combined_results.append(f"[{tool_name}] {observation}")

                # If todo_write was called, log the plan
                if tool_name == "todo_write":
                    entry.add_log("plan", "Todo list created/updated", role="system")

            # Add observation to messages
            obs_text = "\n\n".join(combined_results)
            all_observations.append(obs_text)
            messages.append({"role": "user", "content": f"Observation: {obs_text}"})

        # Extract final answer
        final_output = ""
        for msg in reversed(messages):
            if msg.get("role") == "assistant":
                final_output = msg.get("content", "")
                break

        # Build result
        entry.result = {
            "run_id": entry.run_id,
            "status": "completed",
            "result": final_output[:10000],
            "files_modified": list(set(files_modified)),
            "files_examined": list(set(files_examined)),
            "iterations": iteration,
            "todos_summary": [],
        }
        entry.status = "completed"
        entry.finished_at = time.time()
        elapsed = round(entry.finished_at - entry.started_at, 2)
        entry.add_log("done", f"Completed in {elapsed}s, {iteration} iterations, {len(files_modified)} files modified.")

    except Exception as e:
        entry.status = "error"
        entry.error = f"{e}\n{traceback.format_exc()}"
        entry.finished_at = time.time()
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


# ─── FastAPI App ────────────────────────────────────────────────────────

def create_app():
    """Create and return the FastAPI application."""
    try:
        from fastapi import FastAPI, HTTPException, Query
        from fastapi.responses import JSONResponse
    except ImportError:
        print("[agent_server] ERROR: fastapi not installed. Install with: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(title="Common AI Agent Server", version="1.0.0")

    @app.get("/health")
    async def health():
        """Liveness check."""
        return {"status": "ok", "runs": len(_runs)}

    @app.post("/run")
    async def run_task(request: dict):
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
        if not task:
            raise HTTPException(status_code=400, detail="'task' is required")

        model = request.get("model", "")
        todos = request.get("todos")
        context = request.get("context", "")
        sync = request.get("sync", False)

        entry = _create_run(task, model)

        if sync:
            # Run synchronously in current thread
            _run_react_task(entry, task, model, todos, context)
            return entry.result
        else:
            # Run async in thread pool
            _executor.submit(_run_react_task, entry, task, model, todos, context)
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

    return app


# ─── Server Entrypoint ──────────────────────────────────────────────────

def serve(port: int = 8000, host: str = "0.0.0.0"):
    """
    Start the agent HTTP server.

    This is called by main.py when --serve flag is used.
    """
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
