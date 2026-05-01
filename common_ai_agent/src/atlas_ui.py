"""
src/atlas_ui.py — Atlas frontend server for common_ai_agent

Serves the static frontend bundle at common_ai_agent/frontend/atlas/ and
bridges it to the existing main.py agent loop via:

  • GET  /                       → frontend/atlas/index.html
  • GET  /<asset>                → frontend/atlas/<asset>     (jsx, css, js)
  • WS   /ws/agent               → bidirectional event stream

Activation:
    UI_MODE=atlas  python3 src/textual_main.py        (preferred)
    or directly:   python3 -m src.atlas_ui --port 8765

This mirrors web_ui.py (SSE) but uses WebSockets so the frontend can both
push prompts AND receive token / stage / tool / cost / todo events.

Author: Atlas frontend
"""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import queue
import re
import sys
import threading
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
HERE         = Path(__file__).resolve().parent
SOURCE_ROOT  = HERE.parent                            # common_ai_agent/ (source)
FRONTEND     = SOURCE_ROOT / "frontend" / "atlas"
# PROJECT_ROOT is the user's cwd at launch, NOT the source repo. This
# lets the user run `python ../path/to/textual_main.py` from any
# project directory and have the file API + scope operate on THAT dir.
PROJECT_ROOT = Path(os.getcwd()).resolve()
# Backwards compat alias — older code references ROOT.
ROOT         = SOURCE_ROOT


# ── ask_user answer formatter ──────────────────────────────────────
def _format_answer(ans: dict, options: list) -> str:
    """Render a UI answer payload back into a tool observation string."""
    selected_ids = ans.get("selected") or []
    custom = (ans.get("custom") or "").strip()
    label_by_id = {o.get("id"): o.get("label", o.get("id")) for o in options or []}
    selected_labels = [label_by_id.get(sid, sid) for sid in selected_ids]
    parts = []
    if selected_labels:
        parts.append("selected: " + ", ".join(selected_labels))
    if custom:
        parts.append("note: " + custom)
    if not parts:
        return "(user submitted with no selection)"
    return " · ".join(parts)


# ── Bridge between agent thread and async WS handlers ──────────────
class _AtlasBridge:
    """Queues prompts from the WS into the sync agent loop and pushes
    agent events back out to all connected WS clients.
    """

    def __init__(self) -> None:
        self._inbox: queue.Queue[str] = queue.Queue()
        self._interrupts: queue.Queue[str] = queue.Queue()
        self._outbox: queue.Queue[dict] = queue.Queue()
        self._answer_qs: dict = {}            # flow_id → queue.Queue
        self._answer_lock = threading.Lock()
        self.agent_running: bool = False
        # Esc-style abort flag — checked once per poll by react_loop.
        # Set when the UI sends {type:'stop'}; cleared by check_stop().
        self._stop_flag: bool = False

    # — agent-side (sync) —
    def get_input(self, prompt: str = "") -> str:
        return self._inbox.get()

    def poll_interrupt(self):
        try:
            return self._interrupts.get_nowait()
        except queue.Empty:
            return None

    def emit(self, msg_type: str, **payload) -> None:
        self._outbox.put_nowait({"type": msg_type, **payload})

    # ask_user lifecycle (agent-side, sync) —
    def open_question(self, flow_id: str) -> "queue.Queue":
        q: queue.Queue = queue.Queue()
        with self._answer_lock:
            self._answer_qs[flow_id] = q
        return q

    def close_question(self, flow_id: str) -> None:
        with self._answer_lock:
            self._answer_qs.pop(flow_id, None)

    def wait_answer(self, flow_id: str, timeout=None):
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    # — ws-side (async) —
    def submit_prompt(self, text: str) -> None:
        if self.agent_running:
            self._interrupts.put(text)
        else:
            self._inbox.put(text)

    def submit_answer(self, flow_id: str, payload: dict) -> bool:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return False
        q.put(payload)
        return True

    # Esc / abort handling
    def request_stop(self) -> None:
        """Mark a stop request — react_loop will see it on its next poll."""
        self._stop_flag = True

    def check_stop(self) -> bool:
        """Read-and-clear the stop flag (drop-in for esc_check_fn)."""
        if self._stop_flag:
            self._stop_flag = False
            return True
        return False

    async def next_event(self) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._outbox.get)


# ── App factory ────────────────────────────────────────────────────
def create_app():
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
        from starlette.routing import WebSocketRoute
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn websockets")
        sys.exit(1)

    if not FRONTEND.exists():
        print(f"ERROR: frontend bundle not found at {FRONTEND}")
        sys.exit(1)

    app = FastAPI(title="ATLAS · common_ai_agent")
    bridge = _AtlasBridge()
    clients: set = set()

    @app.get("/")
    async def index():
        return FileResponse(FRONTEND / "index.html")

    @app.get("/api/version")
    async def api_version():
        """Returns the latest mtime across the frontend bundle. The
        browser polls this every few seconds — if it bumps, the page
        reloads. Cheap server-side hot-reload without watchdog or
        websocket file-watcher complexity.
        """
        latest = 0.0
        try:
            for f in FRONTEND.iterdir():
                if f.is_file():
                    latest = max(latest, f.stat().st_mtime)
        except OSError:
            pass
        return JSONResponse({"mtime": latest})

    @app.get("/healthz")
    async def healthz():
        info = {
            "ok": True,
            "frontend": str(FRONTEND),
            "source_root":  str(SOURCE_ROOT),     # where atlas_ui.py lives
            "project_root": str(PROJECT_ROOT),    # = user's cwd at launch
            "cwd": os.getcwd(),
        }
        # Expose the real model + context window so the sidebar doesn't
        # have to invent values. Pull from src.config (the per-process
        # frozen settings); if config isn't importable yet, fall through
        # to env vars.
        try:
            import src.config as _cfg  # noqa: WPS433
        except Exception:
            try: import config as _cfg  # noqa: WPS433
            except Exception: _cfg = None
        # Pick up any .env edits made while the server has been running so
        # the sidebar (and dispatch on the next call) reflect the latest
        # active model / profile without a restart. mtime-cached → cheap.
        if _cfg is not None:
            try:
                _cfg.reload_env()
            except Exception:
                pass
        if _cfg is not None:
            model = ""
            try:
                from src.llm_client import get_active_model
                model = get_active_model() or ""
            except Exception:
                pass
            if not model:
                model = (
                    getattr(_cfg, "MODEL_NAME", None)
                    or getattr(_cfg, "PRIMARY_MODEL", None)
                    or getattr(_cfg, "LLM_MODEL_NAME", "")
                )
            info["model"] = model
            info["base_model"] = (
                getattr(_cfg, "PRIMARY_MODEL", "")
                or getattr(_cfg, "MODEL_NAME", "")
            )
            info["base_url"] = getattr(_cfg, "BASE_URL", "")
            info["provider"] = getattr(_cfg, "LLM_PROVIDER", "")
            info["max_context"] = getattr(_cfg, "MAX_CONTEXT_TOKENS", 0)
            info["max_iterations"] = getattr(_cfg, "MAX_ITERATIONS", 0)
            # Resolve the "active session" the user is looking at. When
            # the agent boots WITHOUT -w, ACTIVE_WORKSPACE is unset but
            # the session still maps to .session/default/. Prefer the
            # explicit workspace; fall back to the actual project the
            # session loader is using (config.ACTIVE_PROJECT) so the
            # UI can show "default" instead of an ambiguous "—".
            info["workspace"] = (os.environ.get("ACTIVE_WORKSPACE")
                                  or os.environ.get("WORKSPACE")
                                  or getattr(_cfg, "ACTIVE_PROJECT", "")
                                  or "default")
            # Per-model pricing (USD / 1M tokens) — input / cache / output.
            # get_active_pricing honors LLM_BASE_MODEL env first, falling
            # back to LLM_MODEL_NAME / config.MODEL_NAME, so the rate shown
            # in the sidebar always matches the model actually in use.
            info["pricing"] = None
            try:
                from lib.model_pricing import get_active_pricing
                p = get_active_pricing()
                if p is not None:
                    info["pricing"] = {
                        "input": p.input, "cache": p.cache, "output": p.output,
                    }
            except Exception:
                pass
            # Live cumulative token + cost totals (from session cost.json)
            try:
                import json as _json
                from pathlib import Path as _P
                _sess = os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()
                _candidates = [
                    _P(_sess) / ".session" / (info["workspace"] or "default") / "cost.json",
                    _P(_sess) / ".session" / "default" / "cost.json",
                ]
                for c in _candidates:
                    if c.exists():
                        d = _json.loads(c.read_text())
                        # cost.json schema (written by lib/textual_ui.py):
                        # {in_tok, cache_tok, out_tok, sum_tok}. The
                        # previous code read input/cached/output, which
                        # always missed and reported 0 — that wiped the
                        # live-accumulated tokens on every flush via the
                        # /healthz refresh path.
                        info["tokens_in"]    = d.get("in_tok",    d.get("input",  0))
                        info["tokens_cache"] = d.get("cache_tok", d.get("cached", 0))
                        info["tokens_out"]   = d.get("out_tok",   d.get("output", 0))
                        # Cost in USD
                        if info["pricing"]:
                            ti = info["tokens_in"]    or 0
                            tc = info["tokens_cache"] or 0
                            to = info["tokens_out"]   or 0
                            info["cost_usd"] = (
                                ti * info["pricing"]["input"]  / 1_000_000
                                + tc * info["pricing"]["cache"]  / 1_000_000
                                + to * info["pricing"]["output"] / 1_000_000
                            )
                        break
            except Exception:
                pass
        else:
            import os as _os
            info["model"] = _os.environ.get("LLM_MODEL_NAME", "") or _os.environ.get("MODEL_NAME", "")
            info["max_context"] = int(_os.environ.get("MAX_CONTEXT_TOKENS", "0") or "0")
            info["max_iterations"] = int(_os.environ.get("MAX_ITERATIONS", "0") or "0")
            info["workspace"] = _os.environ.get("ACTIVE_WORKSPACE", "") or _os.environ.get("WORKSPACE", "")
        return JSONResponse(info)

    @app.get("/api/workspaces")
    async def api_workspaces():
        """List every workspace under workflow/ with a workspace.json.

        Reads from the SOURCE repo (not the user's cwd) since workspace
        definitions ship with common_ai_agent itself.
        """
        workflow_dir = SOURCE_ROOT / "workflow"
        items = []
        if workflow_dir.is_dir():
            for d in sorted(workflow_dir.iterdir()):
                if not d.is_dir():
                    continue
                ws_json = d / "workspace.json"
                if not ws_json.exists():
                    continue
                try:
                    spec = json.loads(ws_json.read_text())
                except Exception:
                    spec = {}
                items.append({
                    "id": d.name,
                    "name": d.name,
                    "label": spec.get("name", d.name),
                    "description": spec.get("description", ""),
                })
        # Same fallback as /healthz — show the actual session name even
        # when ACTIVE_WORKSPACE is unset (boot without -w). Frontend
        # uses this to render the workflow strip's active highlight.
        active = (os.environ.get("ACTIVE_WORKSPACE")
                  or os.environ.get("ACTIVE_PROJECT")
                  or "default")
        return JSONResponse({"active": active, "items": items})

    # ── REAL project data API ────────────────────────────────────
    # File-system backed endpoints. All paths are confined to the user's
    # PROJECT_ROOT (= cwd at launch, computed at module import) and
    # rejected if they try to escape via .. or absolute paths. This is
    # NOT the source repo — when the user runs:
    #   cd Custom_IP && python ../brian_hw/common_ai_agent/src/textual_main.py
    # the file API operates on Custom_IP, not on common_ai_agent/.
    # We intentionally re-bind here as a local var so the module-level
    # PROJECT_ROOT survives even if the import gets reloaded weirdly.
    import sys as _sys_local
    _PROJECT_ROOT = globals().get("PROJECT_ROOT") or Path(os.getcwd()).resolve()
    PROJECT_ROOT = _PROJECT_ROOT
    MAX_READ_BYTES = 256 * 1024
    SKIP_DIRS = {".git", "__pycache__", "node_modules", ".session",
                 "ATLAS", "vendor", ".venv", ".pytest_cache"}

    def _safe(rel_path):
        rel = (rel_path or "").lstrip("/")
        candidate = (PROJECT_ROOT / rel).resolve()
        try:
            candidate.relative_to(PROJECT_ROOT)
        except ValueError:
            return None
        return candidate

    @app.get("/api/files")
    async def api_files(path: str = "", recursive: int = 0, max_depth: int = 4,
                          max_entries: int = 800):
        target = _safe(path)
        if target is None:
            return JSONResponse({"error": "path outside project root"},
                                status_code=400)
        if not target.exists():
            return JSONResponse({"error": "not found"}, status_code=404)
        rel = "" if target == PROJECT_ROOT else str(
            target.relative_to(PROJECT_ROOT))
        if target.is_file():
            stat = target.stat()
            return JSONResponse({
                "type": "file", "path": rel,
                "size": stat.st_size, "mtime": stat.st_mtime,
            })

        entries: list = []

        def _list_one(d, depth):
            try:
                children = sorted(d.iterdir(),
                                   key=lambda p: (p.is_file(), p.name.lower()))
            except PermissionError:
                return
            for child in children:
                if len(entries) >= max_entries:
                    return
                if child.name in SKIP_DIRS or child.name.startswith("."):
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    continue
                entries.append({
                    "name":  child.name if not recursive else str(child.relative_to(target)),
                    "type":  "dir" if child.is_dir() else "file",
                    "size":  stat.st_size if child.is_file() else None,
                    "mtime": stat.st_mtime,
                    "depth": depth,
                })
                if recursive and child.is_dir() and depth < max_depth:
                    _list_one(child, depth + 1)

        _list_one(target, 0)
        return JSONResponse({"type": "dir", "path": rel,
                              "entries": entries,
                              "truncated": len(entries) >= max_entries})

    @app.get("/api/file")
    async def api_file(path: str):
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        stat = target.stat()
        truncated = stat.st_size > MAX_READ_BYTES
        try:
            data = target.read_bytes()[:MAX_READ_BYTES]
            content = data.decode("utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    @app.post("/api/todos/clear")
    async def api_todos_clear():
        """Wipe both the in-memory tracker and the on-disk file."""
        try:
            import main as _main  # noqa: WPS433
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "todos"):
                tt.todos = []
                if hasattr(tt, "current_index"):
                    tt.current_index = -1
                if hasattr(tt, "save"):
                    try: tt.save()
                    except Exception: pass
        except Exception:
            pass
        # Remove the on-disk file too so the legacy fallback can't
        # re-surface old todos.
        try:
            from pathlib import Path as _P
            for cand in ("current_todos.json",
                         str(_P.home() / ".common_ai_agent" / "current_todos.json")):
                p = _P(cand)
                if p.exists():
                    try: p.unlink()
                    except Exception: pass
        except Exception:
            pass
        return JSONResponse({"ok": True})

    @app.get("/api/todos")
    async def api_todos():
        # Prefer the live tracker the agent is mutating in main.py — that's
        # the only way to see in-progress changes before they hit disk. Fall
        # back to TodoTracker.load() if main hasn't initialized one yet.
        try:
            import main as _main  # noqa: WPS433
            live = getattr(_main, "todo_tracker", None)
            if live is not None and getattr(live, "todos", None):
                return JSONResponse(live.to_dict())
        except Exception:
            pass
        try:
            from lib.todo_tracker import TodoTracker
            tt = TodoTracker.load()
            # If the on-disk file is in the legacy array shape (`[{...}]`),
            # to_dict() returns {todos: []}; try parsing the array directly.
            d = tt.to_dict()
            if not d.get("todos"):
                import json as _json
                p = Path("current_todos.json")
                if p.exists():
                    try:
                        raw = _json.loads(p.read_text())
                        if isinstance(raw, list):
                            d = {"todos": [
                                {"content": t.get("content", ""),
                                 "status": t.get("status", "pending"),
                                 "priority": t.get("priority", ""),
                                 "detail": t.get("detail", "")}
                                for t in raw if isinstance(t, dict)
                            ]}
                    except Exception:
                        pass
            return JSONResponse(d)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/commands")
    async def api_commands():
        """List every slash command currently registered, including the
        workspace-specific ones (e.g. /grill-me, /to-ssot for ssot-gen).
        """
        try:
            from core.slash_commands import get_registry as _gr
            reg = _gr()
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        # The registry stores commands in an internal dict; read it
        # defensively through whatever public surface is available.
        cmds = []
        seen = set()
        for attr in ("commands", "_commands"):
            entries = getattr(reg, attr, None)
            if isinstance(entries, dict):
                for name, spec in entries.items():
                    canonical = spec.get("name", name) if isinstance(spec, dict) else name
                    if canonical in seen:
                        continue
                    seen.add(canonical)
                    if isinstance(spec, dict):
                        cmds.append({
                            "cmd":     "/" + canonical,
                            "name":    canonical,
                            "aliases": spec.get("aliases", []) or [],
                            "hint":    spec.get("description", "") or "",
                            "usage":   spec.get("usage", f"/{canonical}"),
                        })
                break
        cmds.sort(key=lambda c: c["name"])
        return JSONResponse({"commands": cmds})

    @app.get("/api/ssot")
    async def api_ssot(file: str = ""):
        if file:
            target = _safe(file)
            if target is None or not target.is_file():
                return JSONResponse({"error": "not found"}, status_code=404)
            try:
                content = target.read_text(encoding="utf-8", errors="replace")
            except OSError as e:
                return JSONResponse({"error": str(e)}, status_code=500)
            return JSONResponse({"path": file, "content": content})
        # No specific file → list every *.ssot.yaml in the project
        results = []
        for p in PROJECT_ROOT.rglob("*.ssot.yaml"):
            if any(part in SKIP_DIRS or part.startswith(".")
                   for part in p.parts):
                continue
            try:
                rel = str(p.relative_to(PROJECT_ROOT))
                stat = p.stat()
                results.append({"path": rel, "size": stat.st_size,
                                 "mtime": stat.st_mtime})
            except OSError:
                continue
        return JSONResponse({"files": results})

    @app.get("/api/conversation")
    async def api_conversation(limit: int = 200):
        """Return the last N messages from the active workspace's
        conversation.json. Used by the Atlas frontend to hydrate the
        chat feed when the user switches workflow (/wf <name>) — without
        this the Atlas chat is browser-session-only and prior context
        from the workflow is invisible.

        config.HISTORY_FILE is already redirected per workspace by
        session_setup.setup_session, so we just read whichever file
        the live session points at right now.
        """
        try:
            try: import src.config as _cfg  # type: ignore
            except Exception:
                try: import config as _cfg  # type: ignore
                except Exception: _cfg = None
            if _cfg is None:
                return JSONResponse({"messages": [], "error": "config unavailable"})
            hpath = Path(getattr(_cfg, "HISTORY_FILE", "") or "")
            if not hpath.is_file():
                return JSONResponse({"messages": [], "path": str(hpath)})
            try:
                msgs = json.loads(hpath.read_text(encoding="utf-8"))
                if not isinstance(msgs, list):
                    msgs = []
            except Exception as e:
                return JSONResponse({"messages": [], "path": str(hpath),
                                       "error": f"parse: {e}"})
            # Drop system prompts (huge, useless in chat replay) and
            # keep only the last `limit` items.
            msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if len(msgs) > limit:
                msgs = msgs[-limit:]
            return JSONResponse({"messages": msgs, "path": str(hpath),
                                  "truncated_to": limit})
        except Exception as e:
            return JSONResponse({"messages": [], "error": str(e)},
                                 status_code=500)

    # ── Git API — status / diff / commit / push ─────────────────
    # All git commands run inside PROJECT_ROOT (the user's cwd at
    # launch). Read-only ops stream back; commit + push run sync
    # and return their stdout/stderr. Push includes an explicit
    # confirm flag because it's destructive (remote-visible).
    import subprocess as _sp_git
    def _git(*args, check_root: bool = True):
        try:
            r = _sp_git.run(
                ["git", *args], cwd=str(PROJECT_ROOT),
                capture_output=True, text=True, timeout=30,
            )
            return r.returncode, r.stdout, r.stderr
        except _sp_git.TimeoutExpired:
            return 124, "", "git command timed out"
        except FileNotFoundError:
            return 127, "", "git executable not found"

    @app.get("/api/git/status")
    async def api_git_status():
        # Branch
        rc, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch = branch.strip() if rc == 0 else ""
        # Porcelain status with numstat-ish summary
        rc, out, err = _git("status", "--porcelain=v1", "--branch")
        if rc != 0:
            return JSONResponse({"error": err.strip() or "git status failed",
                                 "branch": branch, "files": []}, status_code=200)
        files = []
        ahead = behind = 0
        for line in out.splitlines():
            if not line: continue
            if line.startswith("##"):
                # ## main...origin/main [ahead 1, behind 2]
                m = re.search(r"ahead (\d+)", line)
                if m: ahead = int(m.group(1))
                m = re.search(r"behind (\d+)", line)
                if m: behind = int(m.group(1))
                continue
            # XY <path>  (X=staged, Y=unstaged)
            xy = line[:2]; path = line[3:]
            # Renames: "old -> new"
            if " -> " in path:
                path = path.split(" -> ", 1)[1]
            files.append({
                "path": path,
                "status": xy,
                "staged":   xy[0] not in (" ", "?"),
                "unstaged": xy[1] != " ",
            })
        # Per-file numstat (added/removed lines) — best-effort
        rc, ns_out, _ = _git("diff", "--numstat", "HEAD")
        numstat = {}
        if rc == 0:
            for line in ns_out.splitlines():
                parts = line.split("\t")
                if len(parts) >= 3:
                    a, d, p = parts[0], parts[1], parts[2]
                    try:
                        numstat[p] = {"added": int(a) if a != "-" else 0,
                                       "removed": int(d) if d != "-" else 0}
                    except ValueError:
                        pass
        for f in files:
            ns = numstat.get(f["path"])
            if ns: f.update(ns)
        return JSONResponse({"branch": branch, "ahead": ahead,
                              "behind": behind, "files": files})

    @app.get("/api/git/diff")
    async def api_git_diff(path: str = "", staged: int = 0):
        if not path:
            rc, out, err = _git("diff" if not staged else "diff", "--cached" if staged else "HEAD")
        else:
            args = ["diff"]
            if staged: args.append("--cached")
            args.append("--")
            args.append(path)
            rc, out, err = _git(*args)
        if rc != 0 and not out:
            return JSONResponse({"error": err.strip() or "diff failed",
                                  "diff": ""}, status_code=200)
        return JSONResponse({"diff": out, "path": path})

    @app.post("/api/git/commit")
    async def api_git_commit(payload: dict):
        message = (payload or {}).get("message", "").strip()
        add_all = bool((payload or {}).get("add_all", True))
        if not message:
            return JSONResponse({"error": "commit message required"},
                                 status_code=400)
        if add_all:
            rc, _, err = _git("add", "-A")
            if rc != 0:
                return JSONResponse({"error": "git add -A failed: " + err.strip()},
                                     status_code=200)
        rc, out, err = _git("commit", "-m", message)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "returncode": rc})

    @app.post("/api/git/push")
    async def api_git_push(payload: dict = None):
        # Push current branch to origin. User must explicitly confirm
        # in the UI before this fires.
        rc, branch, _ = _git("rev-parse", "--abbrev-ref", "HEAD")
        branch = branch.strip()
        if not branch or branch == "HEAD":
            return JSONResponse({"error": "no current branch (detached HEAD?)"},
                                 status_code=400)
        rc, out, err = _git("push", "origin", branch)
        return JSONResponse({"ok": rc == 0, "stdout": out, "stderr": err,
                              "branch": branch, "returncode": rc})

    # NOTE: WebSocket endpoint is registered via Starlette's WebSocketRoute
    # (added to app.router.routes below) instead of the @app.websocket
    # decorator. The decorator routes through FastAPI's dependency-injection
    # layer, which can't resolve the `websocket: WebSocket` annotation when
    # `from __future__ import annotations` is active (PEP 563 turns all
    # annotations into strings) and rejects the handshake with HTTP 403.
    # Starlette's WebSocketRoute talks to the function directly and ignores
    # parameter annotations entirely.
    async def ws_agent(websocket: WebSocket):
        await websocket.accept()
        clients.add(websocket)
        # Greeting
        await websocket.send_json({"type": "hello", "frontend": "atlas",
                                    "running": bridge.agent_running})

        # Pump outbox → all sockets. Broadcast in parallel with a per-client
        # timeout so a single half-dead WS (browser tab closed but TCP FIN
        # not yet processed by uvicorn — send_json blocks instead of
        # raising) doesn't strand the message for the rest of the live
        # clients. The previous sequential loop made every emit hostage to
        # the slowest peer, which on browser-reload races caused token
        # frames to silently disappear while later events (agent_state,
        # done) still landed via a different pump_out task.
        async def _send_one(client, msg):
            # Scale the per-client send timeout with the message size so
            # large payloads (e.g. /context with a 50 kB full system prompt
            # + conversation dump) don't get killed mid-flight and strand
            # subsequent events (flush, slash_output, agent_state). Floor
            # at 4 s so tiny control frames still get a reasonable window.
            try:
                import json
                raw = json.dumps(msg, ensure_ascii=False)
                size_kb = max(len(raw.encode("utf-8", errors="replace")) / 1024, 1)
                timeout = max(4.0, size_kb * 0.25)  # 0.25 s per kB → 50 kB ≈ 12.5 s
                await asyncio.wait_for(client.send_json(msg), timeout=timeout)
                return None
            except Exception:
                return client

        async def pump_out():
            while True:
                msg = await bridge.next_event()
                snapshot = list(clients)
                if not snapshot:
                    continue
                results = await asyncio.gather(
                    *(_send_one(c, msg) for c in snapshot),
                    return_exceptions=False,
                )
                for stale_client in results:
                    if stale_client is not None:
                        clients.discard(stale_client)

        pump_task = asyncio.create_task(pump_out())
        try:
            while True:
                data = await websocket.receive_text()
                try:
                    msg = json.loads(data)
                except Exception:
                    continue
                t = msg.get("type")
                if t in ("prompt", "send") and msg.get("text"):
                    _txt = msg["text"].strip()
                    # ── Mode-flip slashes need to apply mid-loop ──
                    # `/mode normal` and `/plan` typed while the agent is
                    # running normally land in the _interrupts queue,
                    # which feeds the agent as conversational text — the
                    # slash dispatcher only runs against _inbox between
                    # turns. So agent_mode never actually flips and the
                    # agent stays trapped in plan_q forever, hitting
                    # `[Plan Mode] blocked` on every write_file. We
                    # intercept those four canonical forms here and set
                    # AGENT_MODE_OVERRIDE in the environment; react_loop
                    # reads it at the top of each iteration.
                    import os as _os
                    _low = _txt.lower()
                    if _low in ("/plan", "/mode plan", "/mode normal", "/normal"):
                        if _low in ("/plan", "/mode plan"):
                            _os.environ["AGENT_MODE_OVERRIDE"] = "plan_q"
                            _os.environ["PLAN_MODE"] = "true"
                        else:
                            _os.environ["AGENT_MODE_OVERRIDE"] = "normal"
                            _os.environ["PLAN_MODE"] = "false"
                            _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        # Two-pronged dispatch:
                        # (1) AGENT_MODE_OVERRIDE handles the MID-LOOP case
                        #     (agent currently iterating; react_loop top
                        #     pops it on the next pass and flips local
                        #     agent_mode for parallel_executor).
                        # (2) submit_prompt forwards the slash so main.py's
                        #     dispatcher can fire AGENT_MODE:normal/plan
                        #     when the loop is IDLE — that path is what
                        #     keeps main.py's local agent_mode + the
                        #     system prompt in messages[0] consistent
                        #     across turns. Without this submit, the
                        #     UI's "● NORMAL" pill could click without
                        #     ever telling main.py to flip — desync.
                        # The slash dispatcher in main.py emits its own
                        # "✅ <Mode> mode — tools enabled." banner, so we
                        # don't need to emit one here too (was creating
                        # duplicate confirmations on the idle path).
                        bridge.submit_prompt(_txt)
                        continue

                    # `y` / `yc` / `yes` / `confirm` mid-loop while agent
                    # is in plan mode → treat as plan confirmation. Without
                    # this, the input lands in the _interrupts queue and
                    # gets fed to the LLM as conversational text — the
                    # plan-confirmation handler in chat_loop only runs
                    # against _inbox between turns. So `y` after the
                    # agent shows the [Plan Mode] Plan ready prompt does
                    # nothing if the agent is still mid-iteration.
                    if (_os.environ.get("PLAN_MODE") == "true"
                            and bridge.agent_running
                            and _low in ("y", "yes", "yc", "confirm", "ok",
                                         "proceed", "ㅇㅇ", "확인", "진행")):
                        _os.environ["AGENT_MODE_OVERRIDE"] = "normal"
                        _os.environ["PLAN_MODE"] = "false"
                        _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
                        bridge.emit("token", text="\n✅ Plan confirmed (mid-loop): tools enabled. Executing.\n")
                        bridge.emit("flush")
                        # Inject an instruction so the agent knows to start
                        # executing the agreed-upon plan. This goes to
                        # _interrupts (since agent is running), fed mid-loop.
                        bridge.submit_prompt(
                            "Confirmed. Execute all tasks in order. "
                            "For EACH task: todo_update(in_progress) → do work "
                            "→ todo_update(completed) → verify → todo_update(approved)."
                        )
                        continue
                    bridge.submit_prompt(_txt)
                elif t == "interrupt":
                    bridge.submit_prompt(msg.get("text", ""))
                elif t == "answer" and msg.get("flow_id"):
                    bridge.submit_answer(msg["flow_id"], msg)
                elif t == "stop":
                    # Esc from the UI — abort the current iteration.
                    bridge.request_stop()
                    bridge.emit("agent_state", running=False)
                elif t == "shutdown":
                    # Exit button — kill the whole Python process so the
                    # user's terminal returns to a normal prompt.
                    bridge.emit("error", message="server is shutting down")
                    bridge.emit("done")
                    import os as _os, threading as _t
                    _t.Timer(0.4, lambda: _os._exit(0)).start()
                # Other types (e.g. run_stage, tool_call) can be wired later
        except WebSocketDisconnect:
            pass
        finally:
            clients.discard(websocket)
            pump_task.cancel()

    # Register the WebSocket endpoint via Starlette so we don't go through
    # FastAPI's DI layer (see the long comment above the ws_agent definition).
    app.router.routes.append(WebSocketRoute("/ws/agent", ws_agent))

    # Static assets — jsx, css, js, fonts (registered LAST so it doesn't
    # shadow the explicit routes above). Disable client-side caching so
    # a normal page refresh always picks up new JSX/CSS.
    class _NoCacheStatic(StaticFiles):
        async def get_response(self, path, scope):
            resp = await super().get_response(path, scope)
            resp.headers["Cache-Control"] = "no-store, max-age=0"
            return resp

    app.mount("/", _NoCacheStatic(directory=str(FRONTEND), html=False),
              name="atlas-static")

    app.state.bridge = bridge
    return app


# ── Entry point ────────────────────────────────────────────────────
def run_atlas_ui(port: int = 8765, host: str = "127.0.0.1") -> None:
    """Start the Atlas web UI server and run the agent in a worker thread.

    Wires brian_hw/common_ai_agent/src/main.py's _textual_* callbacks so the
    existing ReAct loop streams to all connected WS clients.
    """
    import uvicorn
    import main as _main  # noqa: WPS433  (intentional runtime import)

    app = create_app()
    bridge: _AtlasBridge = app.state.bridge

    # ── Wire main.py callbacks → bridge.emit ───────────────────────
    _main._textual_input_fn = bridge.get_input
    # Esc from the UI sets bridge._stop_flag; react_loop polls this
    # via esc_check_fn and aborts the current iteration cleanly.
    _main._textual_esc_check_fn = bridge.check_stop
    _main._textual_poll_human_input_fn = bridge.poll_interrupt

    # Strip ANSI escape sequences from ANY text destined for the browser.
    # The terminal-targeting Color class wraps lines in \x1b[2m … \x1b[0m;
    # the browser renders the ESC byte invisibly but happily prints the
    # leftover "[2m" / "[0m" markers, which leaked into the chat as visible
    # garbage. Doing the strip once here covers every emit path.
    import re as _re_ansi
    _ANSI_RE = _re_ansi.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
    )
    def _clean(s):
        return _ANSI_RE.sub("", s) if isinstance(s, str) else s

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=_clean(text), cls=cls)
    _main._textual_emit_reasoning_fn = lambda text, blank=False: bridge.emit("reasoning", text=_clean(text))
    _main._textual_emit_todo_fn      = lambda text: bridge.emit("todo_line", text=_clean(text))
    _main._textual_emit_flush_fn     = lambda: (
        bridge.emit("flush"),
        # Workspace switches happen behind a slash command and re-register
        # the slash registry. Nudge the UI to re-fetch /api/commands so the
        # autocomplete dropdown picks up new workspace commands.
        bridge.emit("commands_changed"),
    )
    _main._textual_emit_tool_fn      = lambda text: bridge.emit("tool", text=_clean(text))
    # Browser-side tool_result cap. Display-only — LLM still gets the
    # full obs upstream; this just trims what we ship over the WS so a
    # 200KB grep doesn't drown the chat. Configurable in .config via
    # WS_TOOL_RESULT_MAX_CHARS (default 8000).
    _ws_tool_max = 8000
    try:
        try: import src.config as _cfg2  # type: ignore  # noqa: WPS433
        except Exception:
            try: import config as _cfg2  # type: ignore  # noqa: WPS433
            except Exception: _cfg2 = None
        if _cfg2 is not None:
            _ws_tool_max = int(getattr(_cfg2, "WS_TOOL_RESULT_MAX_CHARS", 8000))
    except Exception:
        _ws_tool_max = 8000
    def _emit_tool_result(obs, tool=""):
        cleaned = _clean(obs)
        bridge.emit(
            "tool_result",
            text=cleaned[:_ws_tool_max],
            tool=tool,
            truncated=len(cleaned) > _ws_tool_max,
        )
    _main._textual_emit_tool_result_fn = _emit_tool_result

    def _ctx_update(tokens, max_tok):
        bridge.emit("context", used=tokens, max=max_tok)
    _main._textual_emit_context_fn = _ctx_update
    def _emit_token(in_tok, cache_tok, out_tok):
        # Resolve pricing at LLM-call time so the rate matches the model
        # actually used for THIS call (LLM_BASE_MODEL env can pin the base
        # model; otherwise fall back to MODEL_NAME / LLM_MODEL_NAME).
        # Computing the USD delta on the backend keeps frontend math simple
        # and avoids drift between page-load /healthz pricing and the
        # current call's model.
        try:
            from lib.model_pricing import get_active_pricing
            p = get_active_pricing()
        except Exception:
            p = None
        cost_delta = 0.0
        if p is not None:
            cost_delta = (
                (in_tok or 0)    * p.input  +
                (cache_tok or 0) * p.cache  +
                (out_tok or 0)   * p.output
            ) / 1_000_000.0
        # Resolve display model name for the frontend cost panel.
        try:
            import os as _os_cost
            _model_now = (
                _os_cost.getenv("LLM_BASE_MODEL", "").strip()
                or _os_cost.getenv("LLM_MODEL_NAME", "").strip()
            )
            if not _model_now:
                try:
                    from src.llm_client import get_active_model as _gam
                    _model_now = _gam() or ""
                except Exception:
                    _model_now = ""
        except Exception:
            _model_now = ""
        bridge.emit(
            "cost",
            input=in_tok, cached=cache_tok, output=out_tok,
            cost_usd_delta=cost_delta,
            pricing={"input": p.input, "cache": p.cache, "output": p.output} if p else None,
            model=_model_now,
        )
    _main._textual_emit_token_fn = _emit_token

    def _set_running(val: bool):
        bridge.agent_running = val
        bridge.emit("agent_state", running=val)
    _main._textual_set_agent_running_fn = _set_running

    # Safety-net emit for slash command output. The token+flush pipeline has
    # shown intermittent delivery for slash payloads (frontend gets the
    # subsequent agent_state but no token frame), leaving the user with a
    # missing /context / /help / /skills response. This event lands the
    # payload directly in the feed via workspace.jsx's slash_output handler.
    _main._textual_emit_slash_output_fn = lambda text: bridge.emit(
        "slash_output", text=_clean(text)
    )

    # Mode-change notification — chat_loop auto-promotes plan_q→normal when
    # the user types "y" to confirm. Without this signal the React mode pill
    # stays on PLAN even though the agent is now executing.
    _main._textual_emit_mode_fn = lambda mode: bridge.emit("mode_change", mode=mode)

    # ── ask_user → emit qcard event, block on answer queue ────────
    import uuid
    try:
        from core import tools as _tools
    except ImportError:
        _tools = None

    def _ask_user_cb(question, options, kind, subtitle):
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        bridge.open_question(flow_id)
        bridge.emit(
            "ask_user",
            flow_id=flow_id,
            question=question,
            kind=kind,
            subtitle=subtitle or "",
            options=options or [],
        )
        try:
            ans = bridge.wait_answer(flow_id, timeout=900)  # 15 min ceiling
        finally:
            bridge.close_question(flow_id)
        if ans is None:
            return "[ask_user: no answer received within 15 min]"
        return _format_answer(ans, options or [])

    if _tools and hasattr(_tools, "set_ask_user_callback"):
        _tools.set_ask_user_callback(_ask_user_cb)

    def _run_agent():
        try:
            _main.chat_loop()
        except Exception as e:
            bridge.emit("error", message=str(e))
        finally:
            bridge.agent_running = False
            bridge.emit("agent_state", running=False)
            bridge.emit("done")

    threading.Thread(target=_run_agent, daemon=True).start()

    # Surface the source-repo path to the agent so it can locate
    # workflow/, rules/, templates/, etc. when running from a non-source
    # cwd (e.g. user runs `cd Custom_IP && python ../…/textual_main.py`).
    os.environ["ATLAS_SOURCE_ROOT"] = str(SOURCE_ROOT)
    os.environ["ATLAS_PROJECT_ROOT"] = str(PROJECT_ROOT)
    # Inject a system-prompt note so the LLM knows about both roots.
    _root_note = (
        f"\n\n[Atlas Runtime] You are running with cwd = {PROJECT_ROOT}. "
        f"All file reads/writes default to here. The source repo "
        f"(workflow templates, ssot-template.yaml, skills) lives at "
        f"{SOURCE_ROOT} — reference those by absolute path, not by "
        f"relative path from cwd."
    )
    try:
        # Append to whatever the existing system prompt builder produces
        # so the hint is part of every system-prompt rebuild (workspace
        # switches included).
        _orig_builder = getattr(_main, "_build_system_prompt_str", None)
        if callable(_orig_builder):
            def _patched_builder(*a, _orig=_orig_builder, _note=_root_note, **kw):
                return _orig(*a, **kw) + _note
            _main._build_system_prompt_str = _patched_builder
    except Exception:
        pass

    print(f"\n  ATLAS UI → http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")


def main() -> None:
    ap = argparse.ArgumentParser(prog="atlas_ui",
                                  description="Atlas frontend for common_ai_agent")
    ap.add_argument("--port", type=int, default=8765)
    ap.add_argument("--host", default="127.0.0.1")
    args = ap.parse_args()
    run_atlas_ui(port=args.port, host=args.host)


if __name__ == "__main__":
    main()
