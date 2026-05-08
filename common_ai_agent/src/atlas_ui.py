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
import hashlib
import json
import os
import queue
import re
import sys
import threading
import time
from pathlib import Path
from typing import Any, Callable, TYPE_CHECKING

# `from __future__ import annotations` turns every type annotation into
# a string. FastAPI's `get_type_hints()` then needs to resolve those
# strings in the *module globals*. The inner endpoint functions live
# inside create_app() (they import fastapi locally), so without a
# module-level alias of `Request`, the annotation `request: Request`
# becomes an unresolvable ForwardRef and pydantic v2 falls back to
# treating `request` as a query parameter (→ 422 on every POST).
# This conditional import keeps the script usable even when fastapi is
# missing — `Request` just becomes None and the endpoint won't be
# registered (the local import inside create_app sys.exits first).
if TYPE_CHECKING:
    from fastapi import Request
else:
    try:
        from fastapi import Request  # noqa: F401  (runtime forward-ref target)
    except ImportError:
        class Request:  # fallback name for annotations when FastAPI is absent
            pass

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

try:
    from .workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress
except Exception:
    try:
        from workflow_stage_engine import _rtl_manifest_progress as _shared_rtl_manifest_progress  # type: ignore
    except Exception:
        _shared_rtl_manifest_progress = None  # type: ignore

try:
    from core.session_names import normalize_session_name
except Exception:
    from session_names import normalize_session_name  # type: ignore


# ── ask_user answer formatter ──────────────────────────────────────
def _format_answer(ans: dict[str, Any], options: list[dict[str, Any]]) -> str:
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
        self._outbox: queue.Queue[dict[str, Any]] = queue.Queue()
        self._answer_qs: dict[str, queue.Queue[Any]] = {}            # flow_id → queue.Queue
        self._answer_lock = threading.Lock()
        self._pending_ask_user: dict[str, dict[str, Any]] = {}
        self._pending_ask_user_lock = threading.Lock()
        self.agent_running: bool = False
        self.agent_alive: bool = False
        self._agent_lock = threading.Lock()
        self._agent_starter: Callable[[], None] | None = None
        # Esc-style abort flag — checked once per poll by react_loop.
        # Set when the UI sends {type:'stop'}; cleared by check_stop().
        self._stop_flag: bool = False

    # — agent-side (sync) —
    def get_input(self, prompt: str = "") -> str:
        return self._inbox.get()

    def poll_interrupt(self) -> str | None:
        try:
            return self._interrupts.get_nowait()
        except queue.Empty:
            return None

    def emit(self, msg_type: str, **payload: Any) -> None:
        msg = {"type": msg_type, **payload}
        if msg_type == "ask_user":
            session = normalize_session_name(str(msg.get("session") or os.environ.get("ATLAS_ACTIVE_SESSION") or ""))
            if session:
                msg.setdefault("session", session)
            ip = str(msg.get("ip") or os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
            if ip:
                msg.setdefault("ip", ip)
        flow_id = str(payload.get("flow_id") or "")
        if flow_id:
            with self._pending_ask_user_lock:
                if msg_type == "ask_user":
                    self._pending_ask_user[flow_id] = dict(msg)
                elif msg_type in {"ask_user_answered", "ask_user_closed"}:
                    self._pending_ask_user.pop(flow_id, None)
        self._outbox.put_nowait(msg)

    def pending_ask_user_events(self) -> list[dict[str, Any]]:
        with self._pending_ask_user_lock:
            return [dict(event) for event in self._pending_ask_user.values()]

    # ask_user lifecycle (agent-side, sync) —
    def open_question(self, flow_id: str) -> "queue.Queue[Any]":
        q: queue.Queue[Any] = queue.Queue()
        with self._answer_lock:
            self._answer_qs[flow_id] = q
        return q

    def close_question(self, flow_id: str) -> None:
        with self._answer_lock:
            self._answer_qs.pop(flow_id, None)
        self.emit("ask_user_closed", flow_id=flow_id)

    def wait_answer(self, flow_id: str, timeout: float | None = None) -> Any | None:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return None
        try:
            return q.get(timeout=timeout)
        except queue.Empty:
            return None

    # — ws-side (async) —
    def set_agent_starter(self, fn: Callable[[], None]) -> None:
        self._agent_starter = fn

    def ensure_agent_alive(self) -> None:
        starter = self._agent_starter
        if starter is None:
            return
        with self._agent_lock:
            if self.agent_alive:
                return
            self.agent_alive = True
        starter()

    def submit_prompt(self, text: str) -> None:
        self.ensure_agent_alive()
        # Slash-prefixed input always lands in the _inbox so the slash
        # dispatcher can pick it up on the next turn boundary —
        # otherwise mid-run /wf, /mode, /plan etc. were treated as
        # conversational interrupts (they ended up as a free-form
        # user message dumped into the agent's context instead of
        # being executed as commands). Only non-slash text goes to
        # _interrupts when the agent is running.
        if (text or "").lstrip().startswith("/"):
            self._inbox.put(text)
            return
        if self.agent_running:
            self._interrupts.put(text)
        else:
            self._inbox.put(text)

    def queue_prompt(self, text: str) -> None:
        """Queue a prompt for the next top-level turn.

        Slash/workflow commands must go through `_inbox`, not
        `_interrupts`, because main.py only runs the slash dispatcher
        between turns. This keeps Web UI workflow commands from being
        interpreted as conversational text when a prior agent turn is
        still running.
        """
        self.ensure_agent_alive()
        self._inbox.put(text)

    def submit_answer(self, flow_id: str, payload: dict[str, Any]) -> bool:
        with self._answer_lock:
            q = self._answer_qs.get(flow_id)
        if q is None:
            return False
        q.put(payload)
        self.emit("ask_user_answered", flow_id=flow_id)
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

    async def next_event(self, timeout: float = 0.25) -> dict[str, Any] | None:
        loop = asyncio.get_event_loop()
        def _poll() -> dict[str, Any] | None:
            try:
                return self._outbox.get(timeout=timeout)
            except queue.Empty:
                return None

        return await loop.run_in_executor(None, _poll)


# ── App factory ────────────────────────────────────────────────────
def create_app():
    try:
        from fastapi import FastAPI, Request, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, HTMLResponse, JSONResponse
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
    clients: set[Any] = set()
    broadcaster_task: asyncio.Task | None = None

    def _input_history_path() -> Path:
        try:
            try:
                from . import config as _config
            except Exception:
                import config as _config  # type: ignore
            base = str(getattr(_config, "SESSION_DIR", "") or "").strip()
        except Exception:
            base = ""
        return Path(base) / "input_history.txt" if base else PROJECT_ROOT / ".session" / "input_history.txt"

    def _read_input_history(limit: int = 200) -> list[str]:
        path = _input_history_path()
        if not path.is_file():
            return []
        entries: list[str] = []
        cur: list[str] = []
        try:
            for raw in path.read_text(encoding="utf-8", errors="replace").splitlines():
                if raw.startswith("+"):
                    cur.append(raw[1:])
                elif raw.startswith("#"):
                    if cur:
                        entries.append("\n".join(cur))
                        cur = []
            if cur:
                entries.append("\n".join(cur))
        except OSError:
            return []
        return [e for e in entries if e.strip()][-max(1, min(int(limit or 200), 1000)):]

    def _append_input_history(text: str) -> None:
        body = str(text or "").replace("\r\n", "\n").replace("\r", "\n").strip()
        if not body:
            return
        path = _input_history_path()
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open("a", encoding="utf-8") as fh:
            fh.write(f"\n# {time.ctime()}\n")
            for line in body.split("\n"):
                fh.write("+" + line + "\n")

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
            timeout = max(4.0, size_kb * 0.25)  # 0.25 s per kB -> 50 kB ~= 12.5 s
            await asyncio.wait_for(client.send_json(msg), timeout=timeout)
            return None
        except Exception:
            return client

    async def _broadcast_outbox():
        """Single consumer for bridge events, broadcast to every live WS.

        Each websocket used to start its own consumer on the same queue. With
        a browser tab plus an automation client, events were load-balanced
        between clients instead of broadcast, so ask_user cards and slash
        output could disappear from one surface.
        """
        while True:
            msg = await bridge.next_event()
            if msg is None:
                continue
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

    def _ensure_broadcaster() -> None:
        nonlocal broadcaster_task
        if broadcaster_task is None or broadcaster_task.done():
            broadcaster_task = asyncio.create_task(_broadcast_outbox())

    @app.get("/")
    async def index():
        """Serve index.html with local JSX inlined.

        Babel standalone loads `type=text/babel src=...` via XHR.  The
        in-app browser can intermittently fail those localhost XHRs even
        when the same asset is directly reachable.  Inlining keeps the
        dev-time Babel path but removes the fragile second fetch.
        """
        html = (FRONTEND / "index.html").read_text(encoding="utf-8")

        def _inline_script(match):
            attrs = match.group("attrs")
            src = match.group("src").split("?", 1)[0]
            if not src.endswith((".jsx", ".js")):
                return match.group(0)
            path = (FRONTEND / src).resolve()
            try:
                path.relative_to(FRONTEND.resolve())
            except Exception:
                return match.group(0)
            if not path.is_file():
                return match.group(0)
            code = path.read_text(encoding="utf-8")
            return f'<script type="text/babel" {attrs}>{code}</script>'

        html = re.sub(
            r'<script\s+type="text/babel"\s+(?P<attrs>[^>]*?)src="(?P<src>[^"]+)"[^>]*>\s*</script>',
            _inline_script,
            html,
        )
        return HTMLResponse(html)

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

    @app.post("/api/control/stop")
    async def api_control_stop():
        """HTTP fallback for the UI Stop button and Escape key.

        The primary control plane is the WebSocket, but control buttons
        should still work when the WS is reconnecting or its outbound queue
        is wedged behind a larger message.
        """
        bridge.request_stop()
        bridge.emit("agent_state", running=False)
        return JSONResponse({"ok": True, "action": "stop"})

    @app.post("/api/control/shutdown")
    async def api_control_shutdown():
        """HTTP fallback for the UI Exit button."""
        bridge.emit("error", message="server is shutting down")
        bridge.emit("done")
        import os as _os, threading as _t
        _t.Timer(0.4, lambda: _os._exit(0)).start()
        return JSONResponse({"ok": True, "action": "shutdown"})

    @app.get("/healthz")
    async def healthz(request: Request):
        info = {
            "ok": True,
            "frontend": str(FRONTEND),
            "source_root":  str(SOURCE_ROOT),     # where atlas_ui.py lives
            "project_root": str(PROJECT_ROOT),    # = user's cwd at launch
            "cwd": os.getcwd(),
        }
        # Multi-user IPv4-seeded session — opt-in via ATLAS_MULTI_USER.
        # Off by default so single-user installs keep the existing
        # 'default' namespace. When enabled, /healthz exposes the
        # requesting client's IPv4 + a derived `u-<ipv4-dashed>`
        # session id; the frontend's first-visit seed in data.jsx
        # only fires when these fields are present.
        if os.environ.get("ATLAS_MULTI_USER", "").strip().lower() in ("1", "true", "yes", "on"):
            client_host = (request.client.host if request.client else "") or "127.0.0.1"
            if client_host.startswith("::ffff:"):  # IPv4-mapped IPv6
                client_host = client_host[7:]
            _user_safe = client_host.replace(":", "-").replace(".", "-")
            info["client_ip"] = client_host
            info["user_session"] = f"u-{_user_safe}"
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
            # Use the active dispatch model as the primary display value.
            # PRIMARY_MODEL can remain stale after --model/profile overrides
            # (for example glm in .env while --model deepseek is active),
            # which made the ATLAS sidebar look like it was calling the wrong
            # backend even though dispatch was already using MODEL_NAME.
            info["base_model"] = model or getattr(_cfg, "MODEL_NAME", "")
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
                        # Cost in USD. tokens_in is total prompt_tokens
                        # (includes cached subset); tokens_cache is that
                        # cached subset, NOT additive. Subtract cached
                        # before applying p.input or we'd bill the cache
                        # twice (once at input, once at cache rate).
                        if info["pricing"]:
                            ti = info["tokens_in"]    or 0
                            tc = info["tokens_cache"] or 0
                            to = info["tokens_out"]   or 0
                            ti_billable = max(0, ti - tc)
                            info["cost_usd"] = (
                                ti_billable * info["pricing"]["input"]  / 1_000_000
                                + tc        * info["pricing"]["cache"]  / 1_000_000
                                + to        * info["pricing"]["output"] / 1_000_000
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
        rel = "" if target == PROJECT_ROOT else target.relative_to(PROJECT_ROOT).as_posix()
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
                    "name":  child.name if not recursive else child.relative_to(target).as_posix(),
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
        try:
            def _read_preview():
                stat = target.stat()
                data = target.read_bytes()[:MAX_READ_BYTES]
                return stat, data.decode("utf-8", errors="replace")
            stat, content = await asyncio.to_thread(_read_preview)
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        truncated = stat.st_size > MAX_READ_BYTES
        return JSONResponse({
            "path": path, "size": stat.st_size, "mtime": stat.st_mtime,
            "truncated": truncated, "content": content,
        })

    # ── VCD (waveform) endpoints — sim_debug workspace ────────────
    # VCD files can be MB+ so we bypass MAX_READ_BYTES with a separate
    # ceiling. Path resolution still goes through _safe() so the user
    # can't escape PROJECT_ROOT.
    MAX_VCD_BYTES = 32 * 1024 * 1024  # 32 MB

    @app.get("/api/vcd/list")
    async def api_vcd_list(ip: str = "", scope: str = ""):
        """Discover VCD files under PROJECT_ROOT.

        - `ip`    — restrict to `<ip>/sim/*.vcd` (matches the IP-tree convention).
        - `scope` — arbitrary sub-directory under PROJECT_ROOT to search.
        - neither — recursive scan up to depth 4 (cheap on typical projects).
        Returns: `{files: [{path, size, mtime}]}` sorted by mtime desc.
        """
        if ip:
            base = _safe(ip + "/sim")
        elif scope:
            base = _safe(scope)
        else:
            base = PROJECT_ROOT
        if base is None or not base.is_dir():
            return JSONResponse({"files": [], "error": "scope not found"}, status_code=404)

        results = []
        try:
            if ip or scope:
                # Direct *.vcd in chosen dir.
                for f in base.glob("*.vcd"):
                    if f.is_file():
                        st = f.stat()
                        rel = f.relative_to(PROJECT_ROOT).as_posix()
                        results.append({"path": rel, "size": st.st_size, "mtime": st.st_mtime})
            else:
                # Recursive scan (capped depth).
                for f in base.rglob("*.vcd"):
                    try:
                        rel = f.relative_to(PROJECT_ROOT)
                    except ValueError:
                        continue
                    if any(p in SKIP_DIRS for p in rel.parts):
                        continue
                    if len(rel.parts) > 5:
                        continue
                    st = f.stat()
                    results.append({"path": str(rel), "size": st.st_size, "mtime": st.st_mtime})
        except OSError as e:
            return JSONResponse({"error": str(e), "files": []}, status_code=500)
        results.sort(key=lambda x: x["mtime"], reverse=True)
        return JSONResponse({"files": results, "project_root": str(PROJECT_ROOT)})

    @app.get("/api/vcd/raw")
    async def api_vcd_raw(path: str):
        """Return raw VCD content (UTF-8, replace errors). Capped at 32 MB."""
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        if target.suffix.lower() != ".vcd":
            return JSONResponse({"error": "not a .vcd file"}, status_code=400)
        st = target.stat()
        truncated = st.st_size > MAX_VCD_BYTES
        try:
            data = target.read_bytes()[:MAX_VCD_BYTES]
            content = data.decode("utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path,
            "size": st.st_size,
            "mtime": st.st_mtime,
            "truncated": truncated,
            "content": content,
        })

    # ── Source endpoint — sim_debug signal→driver + cocotb test view ─
    # Accepts SV/V plus the text extensions that show up in the
    # cocotb tab (Python tests, sequences, agents, env, Makefile,
    # YAML/JSON, etc.). Rejects binaries to avoid shipping .vvp / .out
    # contents over WS.
    _SOURCE_EXTS = {
        ".sv", ".v", ".svh", ".vh",          # SystemVerilog
        ".py",                                # cocotb / Python testbench
        ".sdc", ".tcl", ".f",                 # constraints / filelists
        ".yaml", ".yml", ".json", ".md",      # config / docs
        ".txt", ".log", ".rpt",               # reports
        ".sh", ".bash",                       # scripts
        ".c", ".h", ".cpp", ".hpp",           # firmware
        ".xml",                               # results.xml
    }
    _SOURCE_NO_EXT_NAMES = {"Makefile", "makefile", "Dockerfile"}

    @app.get("/api/source")
    async def api_source(path: str):
        """Read a source file. Accepts SV / V / Python / Make /
        constraints / YAML / JSON / Markdown / shell / firmware /
        results.xml. Returns split-by-line array for the SourceViewer
        component."""
        target = _safe(path)
        if target is None or not target.is_file():
            return JSONResponse({"error": "not found"}, status_code=404)
        suffix = target.suffix.lower()
        if suffix not in _SOURCE_EXTS and target.name not in _SOURCE_NO_EXT_NAMES:
            return JSONResponse({
                "error": f"unsupported extension '{suffix or target.name}'",
                "allowed": sorted(_SOURCE_EXTS) + sorted(_SOURCE_NO_EXT_NAMES),
            }, status_code=400)
        try:
            content = target.read_text(encoding="utf-8", errors="replace")
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)
        return JSONResponse({
            "path": path,
            "size": len(content),
            "content": content,
            "lines": content.split("\n"),
        })

    # ── sim_debug elab module loader ─────────────────────────────
    # Lives at workflow/sim_debug/elab.py — co-located with the rest
    # of the sim_debug workspace (system_prompt.md, commands/, rules/,
    # scripts/). Loaded via importlib so we don't have to add
    # workflow/sim_debug/ to sys.path globally.
    _ELAB_CACHE = {}
    def _load_sim_debug_elab():
        if "mod" in _ELAB_CACHE:
            return _ELAB_CACHE["mod"]
        import importlib.util as _ilu
        elab_path = SOURCE_ROOT / "workflow" / "sim_debug" / "elab.py"
        if not elab_path.is_file():
            raise FileNotFoundError(f"sim_debug elab module not found at {elab_path}")
        spec = _ilu.spec_from_file_location("sim_debug_elab", str(elab_path))
        mod = _ilu.module_from_spec(spec)
        spec.loader.exec_module(mod)
        _ELAB_CACHE["mod"] = mod
        return mod

    # ── Elab endpoints (pyslang / Verilator / slang) — sim_debug hierarchy + trace ─
    @app.get("/api/elab/status")
    async def api_elab_status():
        try:
            mod = _load_sim_debug_elab()
            return JSONResponse(mod.status())
        except Exception as e:
            return JSONResponse({"error": str(e), "pyslang": False, "verilator": False, "slang": False}, status_code=500)

    def _elab_resolve_sources(sources_glob: str, ip: str = "") -> list:
        """Resolve a comma-separated glob list (or a single ip-tree default).
        Each pattern is interpreted relative to PROJECT_ROOT and clipped to
        files that pass _safe(). Default: `<ip>/rtl/*.sv`.
        """
        from pathlib import Path as _P
        out: list = []
        if not sources_glob and ip:
            sources_glob = f"{ip}/rtl/*.sv"
        for pat in (sources_glob or "").split(","):
            pat = pat.strip().lstrip("/")
            if not pat:
                continue
            for f in PROJECT_ROOT.glob(pat):
                try:
                    f.resolve().relative_to(PROJECT_ROOT)
                except ValueError:
                    continue
                if f.is_file() and f.suffix.lower() in (".sv", ".v", ".svh", ".vh"):
                    out.append(f)
        return out

    @app.get("/api/hierarchy")
    async def api_hierarchy(top: str, sources: str = "", ip: str = "",
                            backend: str = ""):
        """Return the elaborated instance tree.

        Query params:
          - top      : top module name (required)
          - sources  : comma-separated globs of SV/V files (relative to PROJECT_ROOT)
          - ip       : shorthand — equivalent to sources=`<ip>/rtl/*.sv`
          - backend  : 'verilator' (default) or 'slang'; falls back if unavailable
        """
        try:
            mod = _load_sim_debug_elab()
            build_hierarchy_cached = mod.build_hierarchy_cached
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched", "sources_tried": sources or ip}, status_code=400)
        try:
            return JSONResponse(build_hierarchy_cached(backend, top, srcs))
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    @app.get("/api/trace")
    async def api_trace(signal: str, top: str = "", scope: str = "",
                        sources: str = "", ip: str = "",
                        backend: str = ""):
        """Trace driver/sinks for a signal. Top module resolution priority:
        explicit `top` > scope[0] > `ip` > signal[0]. Same source resolution
        as /api/hierarchy."""
        try:
            mod = _load_sim_debug_elab()
            trace_driver_cached = mod.trace_driver_cached
        except Exception as e:
            return JSONResponse({"error": f"elab module: {e}"}, status_code=500)
        srcs = _elab_resolve_sources(sources, ip)
        if not srcs:
            return JSONResponse({"error": "no SV sources matched"}, status_code=400)
        # Prefer explicit top > scope's first segment > ip > signal's first segment.
        resolved_top = (
            top
            or (scope.split(".", 1)[0] if scope else "")
            or ip
            or signal.split(".", 1)[0]
        )
        try:
            return JSONResponse(trace_driver_cached(backend, resolved_top, signal, srcs))
        except ValueError as e:
            return JSONResponse({"error": str(e)}, status_code=503)
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

    # ── cocotb / TB env browsing — sim_debug "TB" tab ─────────────
    @app.get("/api/cocotb")
    async def api_cocotb(ip: str = ""):
        """Inspect a cocotb testbench environment under <ip>/cocotb/ or <ip>/tb/cocotb/.
        Returns a categorised file tree + parsed results.xml summary
        so the sim_debug UI can show 'TB' alongside the RTL hierarchy.
        """
        if not ip:
            return JSONResponse({"error": "ip parameter required"}, status_code=400)
        base = _safe(ip + "/cocotb")
        if base is None or not base.is_dir():
            base = _safe(ip + "/tb/cocotb")
        if base is None or not base.is_dir():
            return JSONResponse({"error": f"no cocotb dir under {ip}/ or {ip}/tb/", "exists": False})
        out = {
            "exists": True,
            "ip": ip,
            "tests":     [],   # tests/*.py
            "sequences": [],
            "env":       [],
            "agent":     [],
            "other":     [],   # Makefile, __init__.py, sim_dump.v, etc.
            "build":     [],   # sim_build/*
            "results":   None, # parsed results.xml
        }
        bucket_dirs = {
            "tests": "tests", "sequences": "sequences",
            "env": "env", "agent": "agent",
        }

        def _parse_py(p):
            """Static-analyse a cocotb Python file via the `ast` module.
            Returns { classes, tests, functions } with file:line locs.
            Same idea as pyslang for SV — no execution, fast, accurate."""
            import ast as _ast
            try:
                src = p.read_text(encoding="utf-8", errors="replace")
                tree = _ast.parse(src, filename=str(p))
            except Exception as e:
                return {"error": str(e)}
            classes, tests, funcs = [], [], []
            for node in tree.body:
                if isinstance(node, _ast.ClassDef):
                    bases = [_ast.unparse(b) if hasattr(_ast, "unparse") else "" for b in node.bases]
                    methods = []
                    for sub in node.body:
                        if isinstance(sub, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                            methods.append({"name": sub.name, "line": sub.lineno, "is_async": isinstance(sub, _ast.AsyncFunctionDef)})
                    classes.append({"name": node.name, "line": node.lineno, "bases": bases, "methods": methods})
                elif isinstance(node, (_ast.FunctionDef, _ast.AsyncFunctionDef)):
                    decorators = []
                    is_test = False
                    for d in node.decorator_list:
                        try:
                            ds = _ast.unparse(d) if hasattr(_ast, "unparse") else ""
                        except Exception:
                            ds = ""
                        decorators.append(ds)
                        if "cocotb.test" in ds:
                            is_test = True
                    entry = {
                        "name": node.name, "line": node.lineno,
                        "is_async": isinstance(node, _ast.AsyncFunctionDef),
                        "decorators": decorators,
                    }
                    (tests if is_test else funcs).append(entry)
            return {"classes": classes, "tests": tests, "functions": funcs}

        try:
            for sub in sorted(base.iterdir()):
                if sub.is_file():
                    rel = sub.relative_to(PROJECT_ROOT).as_posix()
                    entry = {"path": rel, "name": sub.name, "size": sub.stat().st_size}
                    if sub.suffix == ".py" and sub.name.startswith("test_"):
                        entry["parsed"] = _parse_py(sub)
                        out["tests"].append(entry)
                    else:
                        out["other"].append(entry)
                    continue
                if sub.is_dir():
                    bucket = next((k for k, v in bucket_dirs.items() if v == sub.name), None)
                    if bucket:
                        for f in sorted(sub.rglob("*.py")):
                            if "__pycache__" in f.parts or f.name == "__init__.py":
                                rel = f.relative_to(PROJECT_ROOT).as_posix()
                                if f.name == "__init__.py":
                                    out[bucket].append({"path": rel, "name": f.name, "size": f.stat().st_size, "parsed": None})
                                continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out[bucket].append({
                                "path": rel, "name": f.name,
                                "size": f.stat().st_size,
                                "parsed": _parse_py(f),
                            })
                    elif sub.name == "sim_build":
                        for f in sorted(sub.iterdir()):
                            if not f.is_file(): continue
                            rel = f.relative_to(PROJECT_ROOT).as_posix()
                            out["build"].append({"path": rel, "name": f.name, "size": f.stat().st_size})
        except OSError as e:
            return JSONResponse({"error": str(e)}, status_code=500)

        # Build TB hierarchy: aggregate class definitions across files.
        tb_hier = {"agents": [], "envs": [], "scoreboards": [], "sequences": [], "tests": []}
        for bucket in ("agent", "env", "sequences", "tests"):
            for f in out.get(bucket, []):
                p = f.get("parsed") or {}
                for c in p.get("classes", []):
                    info = {"name": c["name"], "line": c["line"], "file": f["path"], "bases": c["bases"], "methods": [m["name"] for m in c["methods"]]}
                    bases_blob = " ".join(c["bases"]).lower()
                    if "scoreboard" in c["name"].lower() or "scoreboard" in bases_blob:
                        tb_hier["scoreboards"].append(info)
                    elif bucket == "agent" or "agent" in c["name"].lower() or "driver" in c["name"].lower() or "monitor" in c["name"].lower():
                        tb_hier["agents"].append(info)
                    elif bucket == "env" or "env" in c["name"].lower() or "tb" in c["name"].lower():
                        tb_hier["envs"].append(info)
                    elif bucket == "sequences" or "sequence" in c["name"].lower() or "seq" in c["name"].lower():
                        tb_hier["sequences"].append(info)
                for t in p.get("tests", []):
                    tb_hier["tests"].append({"name": t["name"], "line": t["line"], "file": f["path"], "decorators": t["decorators"]})
        out["tb_hierarchy"] = tb_hier

        # Parse results.xml (cocotb format) for test pass/fail summary.
        rx = base / "results.xml"
        if rx.is_file():
            try:
                import xml.etree.ElementTree as _ET
                root_xml = _ET.parse(str(rx)).getroot()
                cases = []
                pass_n = 0; fail_n = 0; skip_n = 0
                for tc in root_xml.iter("testcase"):
                    name = tc.attrib.get("name", "")
                    classname = tc.attrib.get("classname", "")
                    time_s = tc.attrib.get("time", "0")
                    sim_t  = tc.attrib.get("sim_time_ns", "")
                    file_attr = tc.attrib.get("file", "")
                    line_attr = tc.attrib.get("lineno", "0")
                    failure = tc.find("failure") is not None or tc.find("error") is not None
                    skipped = tc.find("skipped") is not None
                    if failure: fail_n += 1
                    elif skipped: skip_n += 1
                    else: pass_n += 1
                    rel_file = ""
                    if file_attr:
                        try:
                            fp = Path(file_attr)
                            if fp.is_absolute():
                                rel_file = str(fp.resolve().relative_to(PROJECT_ROOT))
                            else:
                                safe_fp = _safe(file_attr)
                                rel_file = safe_fp.relative_to(PROJECT_ROOT).as_posix() if safe_fp else file_attr
                        except Exception:
                            try:
                                rel_file = str(Path(file_attr).resolve().relative_to(PROJECT_ROOT))
                            except Exception:
                                rel_file = file_attr
                    cases.append({
                        "name": name, "classname": classname,
                        "time_s": float(time_s) if time_s else 0,
                        "sim_time_ns": sim_t,
                        "file": rel_file, "line": int(line_attr) if line_attr.isdigit() else 0,
                        "status": "fail" if failure else ("skip" if skipped else "pass"),
                    })
                out["results"] = {
                    "total": pass_n + fail_n + skip_n,
                    "pass": pass_n, "fail": fail_n, "skip": skip_n,
                    "cases": cases,
                    "mtime": rx.stat().st_mtime,
                }
            except Exception as e:
                out["results"] = {"error": f"parse failed: {e}"}
        return JSONResponse(out)

    @app.post("/api/todos/clear")
    async def api_todos_clear():
        """Wipe both the in-memory tracker and the on-disk file."""
        import os as _os
        _os.environ.pop("TODO_TEMPLATE_LOCK_ADDITIONS", None)
        _os.environ.pop("TODO_TEMPLATE_LOCK_NAME", None)
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
        # back to the on-disk file if main hasn't initialized one yet.
        candidates: list[Path] = []
        try:
            import main as _main  # noqa: WPS433
            live = getattr(_main, "todo_tracker", None)
            if live is not None and getattr(live, "todos", None):
                return JSONResponse(live.to_dict())
            live_path = getattr(live, "_persist_path", None) if live is not None else None
            if live_path:
                candidates.append(Path(live_path))
        except Exception:
            pass
        # On-disk fallback. Two persistence paths exist in this repo:
        #   1. <PROJECT_ROOT>/current_todos.json    (relative TODO_FILE,
        #                                            agent's actual writes)
        #   2. ~/.common_ai_agent/current_todos.json (HOME default for
        #                                            stand-alone scripts)
        # When `import config` succeeds at module load, TodoTracker module
        # caches TODO_FILE as Path("current_todos.json") — relative — and
        # whether `.exists()` resolves depends on the server's cwd at
        # request time. Resolve them *both* explicitly so the panel never
        # silently falls through to "no todos" when the file is right
        # there in PROJECT_ROOT.
        try:
            import json as _json
            from lib.todo_tracker import TodoTracker
            try:
                import config as _cfg
                cfg_todo = Path(str(getattr(_cfg, "TODO_FILE", "current_todos.json")))
                candidates.append(cfg_todo if cfg_todo.is_absolute() else PROJECT_ROOT / cfg_todo)
            except Exception:
                pass
            active_session = normalize_session_name(os.environ.get("ATLAS_ACTIVE_SESSION", ""))
            if active_session:
                candidates.append(PROJECT_ROOT / ".session" / active_session / "todo.json")
            candidates.extend([
                PROJECT_ROOT / "current_todos.json",
                Path.cwd() / "current_todos.json",
                Path.home() / ".common_ai_agent" / "current_todos.json",
            ])
            deduped: list[Path] = []
            seen_paths: set[str] = set()
            for cand in candidates:
                try:
                    key = str(cand.expanduser().resolve())
                except Exception:
                    key = str(cand)
                if key not in seen_paths:
                    seen_paths.add(key)
                    deduped.append(cand)
            picked = next((p for p in deduped if p.exists()), None)
            if picked is None:
                return JSONResponse({"todos": []})
            tt = TodoTracker.load(picked)
            d = tt.to_dict()
            if d.get("todos"):
                return JSONResponse(d)
            # Legacy array shape: `[{...}]` instead of `{"todos": [...]}`.
            try:
                raw = _json.loads(picked.read_text())
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

    @app.get("/api/input-history")
    async def api_input_history(limit: int = 200):
        try:
            history = _read_input_history(limit)
            return JSONResponse({
                "history": history,
                "path": _relative_project_path(_input_history_path()),
            })
        except Exception as e:
            return JSONResponse({"error": str(e), "history": []}, status_code=500)

    @app.post("/api/input-history")
    async def api_append_input_history(request: Request):
        try:
            payload = await request.json()
        except Exception:
            payload = {}
        text = str(payload.get("text") or "").strip()
        if not text:
            return JSONResponse({"ok": True, "stored": False})
        try:
            _append_input_history(text)
            return JSONResponse({"ok": True, "stored": True})
        except Exception as e:
            return JSONResponse({"ok": False, "error": str(e)}, status_code=500)

    @app.get("/api/ssot")
    async def api_ssot(file: str = ""):
        if file:
            target = _safe(file)
            if target is None or not target.is_file():
                return JSONResponse({"error": "not found"}, status_code=404)
            try:
                content = await asyncio.to_thread(
                    target.read_text,
                    encoding="utf-8",
                    errors="replace",
                )
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
                rel = p.relative_to(PROJECT_ROOT).as_posix()
                stat = p.stat()
                results.append({"path": rel, "size": stat.st_size,
                                 "mtime": stat.st_mtime})
            except OSError:
                continue
        return JSONResponse({"files": results})

    @app.get("/api/ssot/qa")
    async def api_ssot_qa(ip: str = "", session: str = ""):
        session_name = normalize_session_name(session or "")
        target = str(ip or "").strip()
        if not target and session_name:
            parts = [p for p in session_name.split("/") if p]
            if len(parts) >= 2 and parts[-1] == "ssot-gen":
                target = parts[-2]
        if target and not _valid_ip_name(target):
            return JSONResponse({"error": f"invalid ip {target!r}"}, status_code=400)
        if not target:
            target = _active_ssot_ip()
        if not target or not _valid_ip_name(target):
            return JSONResponse({
                "ip": "",
                "workflow": "ssot-gen",
                "toc": [],
                "sections": [],
                "summary": {"total": 0, "approved": 0, "pending": 0},
                "items": [],
            })
        return JSONResponse(_ssot_qa_view(target, session=session_name))

    @app.get("/api/ssot/qa/sessions")
    async def api_ssot_qa_sessions():
        return JSONResponse(_ssot_qa_sessions_view())

    @app.get("/api/soc")
    async def api_soc():
        """Build a SoC-Architect-friendly view of the project's IPs.

        Two-tier source-of-truth model:
          1. SoC-level SSOT  — `<project_root>/soc.ssot.yaml`
             Owned by the Architect supervisor. Lists clusters, IP
             instances (with overrides + addresses), connections, and
             generators. When present, drives the architect view.
          2. Per-IP leaf SSOT — `<ip>/yaml/<ip>.ssot.yaml`
             Each instance points to its leaf SSOT for parameters,
             busInterfaces, model.ports → clocks/resets, memoryMap.

        When the SoC SSOT is missing we fall back to the directory walk
        (every `*.ssot.yaml` under the project becomes a module under a
        single `ips` cluster) so existing projects keep working without
        an explicit SoC file.

        Status (ssot/rtl/sim) is derived from filesystem presence:
          ssot = ok  if yaml file parses
          rtl  = ok  if <ip>/rtl/*.sv exists, partial if dir exists empty,
                     pending otherwise
          sim  = ok  if <ip>/sim/ has any *.log or *.vcd, pending otherwise
        Used by the Atlas Architect screen to replace the mock SOC.
        """
        try:
            try: import yaml as _yaml  # type: ignore
            except Exception: _yaml = None

            def _kind_for(name: str) -> str:
                """Infer module kind from its name. Used as a fallback
                when no cluster.role is available (dir-walk mode) or
                when the cluster lists a generic role. Heuristic patterns
                broaden to catch real-world IP names: cortexa15, riscv,
                cci550, ccn508, nic400, etc."""
                n = (name or "").lower()
                if any(s in n for s in ("cpu", "core", "rv", "cortex", "riscv",
                                         "arm", "neoverse", "amba_a", "hart")): return "cpu"
                if any(s in n for s in ("mem", "ram", "ddr", "cache", "sram",
                                         "rom", "flash", "ocm")): return "mem"
                if any(s in n for s in ("noc", "bus", "axi", "apb", "ahb", "xbar",
                                         "cci", "ccn", "nic", "nip", "interconnect",
                                         "crossbar", "smmu", "iommu")): return "bus"
                if any(s in n for s in ("phy", "ana", "pll", "ldo", "vco",
                                         "adc", "dac", "afe", "rf")): return "analog"
                return "periph"

            # Cluster role string from soc.ssot.yaml → module kind. The
            # role is more authoritative than the name heuristic; we let
            # it win when present so cortexa15_0 under a CPU cluster is
            # always classified `cpu` regardless of name.
            _ROLE_TO_KIND = {
                "CPU": "cpu", "MEM": "mem", "BUS": "bus",
                "PERIPH": "periph", "ANALOG": "analog",
                "INTERCONNECT": "bus", "FABRIC": "bus", "NOC": "bus",
                "PERIPHERAL": "periph", "MISC": "periph",
            }
            def _kind_from_role(role):
                if not isinstance(role, str): return None
                return _ROLE_TO_KIND.get(role.strip().upper())

            # YAML hex literals like `0x8000_0000` are parsed by PyYAML
            # to a Python int. Re-format as a hex string with 4-digit
            # underscore groups so the architect UI shows the canonical
            # SoC notation (`0x8000_0000`, `0x4000_2000`) instead of a
            # raw decimal (`2147483648`).
            def _hex_addr(v):
                if v is None: return ""
                if isinstance(v, int):
                    h = f"{v:x}"
                    # Zero-pad to at least 8 hex digits (32-bit address
                    # convention) so 0x0800_0000 doesn't collapse to
                    # 0x800_0000 after grouping. Larger values use the
                    # next multiple of 4.
                    target = max(8, ((len(h) - 1) // 4 + 1) * 4)
                    h = h.zfill(target)
                    if len(h) > 4:
                        rev = h[::-1]
                        groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                        h = "_".join(groups)[::-1]
                    return f"0x{h}"
                # Already a string (might or might not be hex-prefixed).
                s = str(v).strip()
                if s.startswith("0x") or s.startswith("0X"): return s
                # Try parse as int — covers decimal-string cases.
                try:
                    return _hex_addr(int(s))
                except ValueError:
                    return s

            def _has_live_content(value: Any) -> bool:
                if value is None:
                    return False
                if isinstance(value, str):
                    text = value.strip()
                    return bool(text) and text.upper() not in {"TBD", "TODO", "NONE", "NULL"}
                if isinstance(value, (list, tuple, set)):
                    return any(_has_live_content(v) for v in value)
                if isinstance(value, dict):
                    return any(_has_live_content(v) for v in value.values())
                return True

            def _contains_tbd(value: Any) -> bool:
                if isinstance(value, str):
                    return bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", value, re.I))
                if isinstance(value, list):
                    return any(_contains_tbd(v) for v in value)
                if isinstance(value, dict):
                    return any(_contains_tbd(v) for v in value.values())
                return False

            _SSOT_SECTIONS = [
                ("top_module", "top module"),
                ("sub_modules", "sub modules"),
                ("parameters", "parameters"),
                ("io_list", "I/O"),
                ("features", "features"),
                ("dataflow", "dataflow"),
                ("function_model", "function model"),
                ("cycle_model", "cycle model"),
                ("clock_reset_domains", "clock/reset"),
                ("cdc_requirements", "CDC"),
                ("rdc_requirements", "RDC"),
                ("registers", "registers"),
                ("memory", "memory"),
                ("interrupts", "interrupts"),
                ("fsm", "FSM"),
                ("timing", "timing"),
                ("power", "power"),
                ("security", "security"),
                ("error_handling", "errors"),
                ("debug_observability", "debug"),
                ("integration", "integration"),
                ("dft", "DFT"),
                ("synthesis", "synthesis"),
                ("coding_rules", "coding rules"),
                ("reuse_modules", "reuse modules"),
                ("custom", "custom"),
                ("dir_structure", "dir structure"),
                ("filelist", "filelist"),
                ("test_requirements", "DV plan"),
                ("quality_gates", "quality gates"),
                ("traceability", "traceability"),
                ("workflow_todos", "workflow TODOs"),
                ("generation_flow", "generation flow"),
            ]
            _SSOT_SECTION_ALIASES = {
                "clock_reset_domains": ["clock_reset_domains", "reset_behavior", "clocks", "resets"],
                "function_model": ["function_model", "functional_model", "behavior_model", "reference_model"],
                "cycle_model": ["cycle_model", "cycle_accurate_model", "timing_model", "pipeline_model"],
                "debug_observability": ["debug_observability", "debug", "observability", "trace_debug"],
                "dft": ["dft", "dfd", "testability"],
                "synthesis": ["synthesis", "implementation_constraints", "physical_constraints"],
                "coding_rules": ["coding_rules", "constraints"],
                "test_requirements": ["test_requirements", "verification"],
                "quality_gates": ["quality_gates", "acceptance_criteria", "pass_criteria", "signoff_criteria"],
                "workflow_todos": ["workflow_todos", "next_step_todos"],
            }

            def _pct(done: int, total: int) -> int:
                return int(round((100.0 * done / total))) if total else 0

            _SSOT_EMPTY_IS_DECLARED = {
                "reuse_modules",
            }

            def _is_non_empty_mapping(value: Any) -> bool:
                return isinstance(value, dict) and bool(value)

            def _is_non_empty_list(value: Any) -> bool:
                return isinstance(value, list) and bool(value)

            def _has_required_fields(value: Any, fields: list[str]) -> bool:
                if not isinstance(value, dict):
                    return False
                for field in fields:
                    item = value.get(field)
                    if item is None or item == "" or item == [] or item == {}:
                        return False
                return True

            def _scenario_complete(item: Any) -> bool:
                return _has_required_fields(item, ["id", "name", "stimulus", "expected", "checker", "coverage"])

            def _gate_complete(item: Any) -> bool:
                return _has_required_fields(item, ["pass", "evidence"])

            def _ssot_section_complete(key: str, value: Any, present: bool) -> bool:
                if not present or _contains_tbd(value):
                    return False
                if key in _SSOT_EMPTY_IS_DECLARED and isinstance(value, (list, tuple, set, dict)):
                    return True
                if key == "function_model":
                    if not isinstance(value, dict):
                        return False
                    state_variables = value.get("state_variables") if isinstance(value.get("state_variables"), list) else []
                    transactions = value.get("transactions") if isinstance(value.get("transactions"), list) else []
                    invariants = value.get("invariants") if isinstance(value.get("invariants"), list) else []
                    return (
                        _has_required_fields(value, ["state_variables", "transactions", "invariants"])
                        and _is_non_empty_list(state_variables)
                        and _is_non_empty_list(transactions)
                        and _is_non_empty_list(invariants)
                        and all(
                            _has_required_fields(tx, ["id", "name", "preconditions", "outputs"])
                            and bool(tx.get("side_effects") or tx.get("error_cases"))
                            for tx in transactions
                        )
                    )
                if key == "cycle_model":
                    return (
                        _has_required_fields(value, ["clock", "reset", "latency", "handshake_rules", "pipeline", "ordering"])
                        and _is_non_empty_list(value.get("handshake_rules"))
                        and _is_non_empty_list(value.get("pipeline"))
                        and _is_non_empty_list(value.get("ordering"))
                    )
                if key == "timing":
                    return _has_required_fields(value, ["target_clocks", "latency_budget"]) and _is_non_empty_list(value.get("target_clocks"))
                if key == "power":
                    return _has_required_fields(value, ["domains", "power_states"]) and _is_non_empty_list(value.get("domains"))
                if key == "security":
                    return (
                        _has_required_fields(value, ["classification", "assets", "threat_model"])
                        and _is_non_empty_list(value.get("assets"))
                        and _is_non_empty_list(value.get("threat_model"))
                    )
                if key == "error_handling":
                    return _has_required_fields(value, ["error_sources", "propagation", "recovery"]) and _is_non_empty_list(value.get("error_sources"))
                if key == "debug_observability":
                    return _has_required_fields(value, ["waveform_must_probe", "trace_events"]) and _is_non_empty_list(value.get("waveform_must_probe"))
                if key == "integration":
                    return _has_required_fields(value, ["bus_attachment", "dependencies"])
                if key == "dft":
                    return _has_required_fields(value, ["scan_required", "controllability", "observability"])
                if key == "synthesis":
                    return _has_required_fields(value, ["dialect", "constraints", "required_outputs"])
                if key == "test_requirements":
                    scenarios = value.get("scenarios") if isinstance(value, dict) else None
                    return (
                        _has_required_fields(value, ["scenarios", "scoreboard_checks", "coverage_goals"])
                        and _is_non_empty_list(scenarios)
                        and all(_scenario_complete(item) for item in scenarios)
                    )
                if key == "quality_gates":
                    if not _is_non_empty_mapping(value):
                        return False
                    return all(_gate_complete(value.get(gate)) for gate in ["ssot", "rtl", "dv", "coverage", "eda", "signoff"])
                if key == "traceability":
                    return _has_required_fields(value, ["yaml_to_output"]) and _is_non_empty_list(value.get("yaml_to_output"))
                return _has_live_content(value)

            def _count_list(value: Any) -> int:
                return len(value) if isinstance(value, list) else 0

            def _ssot_metrics(doc: dict) -> dict:
                io_list = doc.get("io_list") if isinstance(doc, dict) else {}
                interfaces = io_list.get("interfaces") if isinstance(io_list, dict) else []
                ports = 0
                if isinstance(interfaces, list):
                    for iface in interfaces:
                        if isinstance(iface, dict) and isinstance(iface.get("ports"), list):
                            ports += len(iface["ports"])
                registers = doc.get("registers") if isinstance(doc, dict) else {}
                register_list = registers.get("register_list") if isinstance(registers, dict) else []
                memory = doc.get("memory") if isinstance(doc, dict) else {}
                memory_instances = memory.get("instances") if isinstance(memory, dict) else []
                fsm = doc.get("fsm") if isinstance(doc, dict) else {}
                fsm_states = 0
                fsm_transitions = 0
                if isinstance(fsm, dict):
                    for item in fsm.values():
                        if isinstance(item, dict):
                            fsm_states += _count_list(item.get("states"))
                            fsm_transitions += _count_list(item.get("transitions"))
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                function_model = doc.get("function_model") if isinstance(doc, dict) else {}
                fm_transactions = function_model.get("transactions") if isinstance(function_model, dict) else []
                fm_state = function_model.get("state_variables") if isinstance(function_model, dict) else []
                cycle_model = doc.get("cycle_model") if isinstance(doc, dict) else {}
                cm_handshakes = cycle_model.get("handshake_rules") if isinstance(cycle_model, dict) else []
                cm_pipeline = cycle_model.get("pipeline") if isinstance(cycle_model, dict) else []
                quality_gates = doc.get("quality_gates") if isinstance(doc, dict) else {}
                timing = doc.get("timing") if isinstance(doc, dict) else {}
                security = doc.get("security") if isinstance(doc, dict) else {}
                error_handling = doc.get("error_handling") if isinstance(doc, dict) else {}
                submods = doc.get("sub_modules") if isinstance(doc, dict) else []
                return {
                    "submodules": _count_list(submods),
                    "parameters": _count_list(doc.get("parameters") if isinstance(doc, dict) else []),
                    "interfaces": _count_list(interfaces),
                    "ports": ports,
                    "registers": _count_list(register_list),
                    "memories": _count_list(memory_instances),
                    "fsm_states": fsm_states,
                    "fsm_transitions": fsm_transitions,
                    "dv_scenarios": _count_list(scenarios),
                    "function_transactions": _count_list(fm_transactions),
                    "function_state_variables": _count_list(fm_state),
                    "cycle_handshake_rules": _count_list(cm_handshakes),
                    "cycle_pipeline_stages": _count_list(cm_pipeline),
                    "timing_clocks": _count_list(timing.get("target_clocks") if isinstance(timing, dict) else []),
                    "security_assets": _count_list(security.get("assets") if isinstance(security, dict) else []),
                    "error_sources": _count_list(error_handling.get("error_sources") if isinstance(error_handling, dict) else []),
                    "scoreboard_checks": tr.get("scoreboard_checks") if isinstance(tr, dict) else None,
                    "coverage_goals": len(coverage_goals) if isinstance(coverage_goals, dict) else 0,
                    "quality_gates": len(quality_gates) if isinstance(quality_gates, dict) else 0,
                }

            def _ssot_progress(doc: dict) -> dict:
                sections = []
                canonical_keys = {k for k, _ in _SSOT_SECTIONS}
                section_defs = list(_SSOT_SECTIONS)
                if isinstance(doc, dict) and doc:
                    known = set(canonical_keys)
                    known.update(a for aliases in _SSOT_SECTION_ALIASES.values() for a in aliases)
                    for key in doc.keys():
                        if key not in known:
                            section_defs.append((str(key), str(key).replace("_", " ")))
                for key, label in section_defs:
                    keys = _SSOT_SECTION_ALIASES.get(key, [key])
                    actual_key = next((k for k in keys if isinstance(doc, dict) and k in doc), key)
                    val = doc.get(actual_key) if isinstance(doc, dict) else None
                    present = actual_key in doc if isinstance(doc, dict) else False
                    complete = _ssot_section_complete(key, val, present)
                    status = "approved" if complete else ("incomplete" if present else "missing")
                    sections.append({
                        "key": key,
                        "actual_key": actual_key if present else "",
                        "label": label,
                        "status": status,
                        "canonical": key in canonical_keys,
                    })
                approved = sum(1 for s in sections if s.get("canonical") and s["status"] == "approved")
                total = sum(1 for s in sections if s.get("canonical"))
                return {
                    "approved": approved,
                    "total": total,
                    "pct": _pct(approved, total),
                    "sections": sections,
                    "metrics": _ssot_metrics(doc if isinstance(doc, dict) else {}),
                }

            def _extract_expected_rtl(doc: dict) -> list[dict[str, str]]:
                expected: list[dict[str, str]] = []
                seen: set[str] = set()
                subs = doc.get("sub_modules") if isinstance(doc, dict) else []
                if isinstance(subs, list):
                    for idx, item in enumerate(subs):
                        if not isinstance(item, dict):
                            continue
                        name = str(item.get("name") or f"module_{idx}")
                        file_name = str(item.get("file") or "").strip()
                        if file_name and file_name not in seen:
                            expected.append({"name": name, "file": file_name})
                            seen.add(file_name)
                fl = doc.get("filelist") if isinstance(doc, dict) else {}
                rtl_list = fl.get("rtl") if isinstance(fl, dict) else []
                if isinstance(rtl_list, list):
                    for raw in rtl_list:
                        file_name = str(raw or "").strip()
                        if not file_name or file_name in seen:
                            continue
                        expected.append({"name": Path(file_name).stem, "file": file_name})
                        seen.add(file_name)
                return expected

            def _resolve_ip_file(ip_dir: Path, rel: str) -> Path:
                p = Path(rel)
                if p.is_absolute():
                    return p
                cand = ip_dir / rel
                if cand.is_file():
                    return cand
                return PROJECT_ROOT / rel

            def _filelist_entries(ip_dir: Path) -> tuple[list[str], Path | None]:
                f = ip_dir / "list" / f"{ip_dir.name}.f"
                if not f.is_file():
                    return [], None
                entries: list[str] = []
                try:
                    for raw in f.read_text(encoding="utf-8", errors="replace").splitlines():
                        line = raw.split("//", 1)[0].strip()
                        if line and line.endswith((".v", ".sv", ".vh", ".svh")):
                            entries.append(line)
                except OSError:
                    pass
                return entries, f

            def _rtl_progress(ip_dir: Path, doc: dict) -> dict:
                if _shared_rtl_manifest_progress is not None:
                    try:
                        return _shared_rtl_manifest_progress(ip_dir, doc if isinstance(doc, dict) else {})
                    except Exception:
                        pass
                blocked_path = ip_dir / "rtl" / "rtl_blocked.json"
                blocked_doc: dict[str, Any] = {}
                if blocked_path.is_file():
                    try:
                        blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                    except Exception:
                        blocked_doc = {
                            "status": "blocked",
                            "reason": "rtl_blocked.json is present but could not be parsed",
                        }
                entries, fpath = _filelist_entries(ip_dir)
                entry_set = set(entries)
                top_doc = doc.get("top_module") if isinstance(doc, dict) else {}
                top_name = ""
                if isinstance(top_doc, dict):
                    top_name = str(top_doc.get("name") or "").strip()
                if not top_name:
                    top_name = ip_dir.name
                listed_text = ""
                listed_sources: list[Path] = []
                for ent in entries:
                    src = _resolve_ip_file(ip_dir, ent)
                    if src.is_file():
                        listed_sources.append(src)
                        try:
                            listed_text += "\n" + src.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            pass
                modules = []
                expected = _extract_expected_rtl(doc)
                if not expected:
                    rtl_dir = ip_dir / "rtl"
                    expected = [
                        {"name": p.stem, "file": p.relative_to(ip_dir).as_posix()}
                        for p in sorted(list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")))
                    ] if rtl_dir.is_dir() else []
                for item in expected:
                    rel = item["file"]
                    path = _resolve_ip_file(ip_dir, rel)
                    resolved_rel = rel
                    manifest_mismatch = False
                    # SSOTs often describe the integration wrapper as
                    # `<ip>_top.sv` while the real top module is `<ip>`.
                    # Verilator's DECLFILENAME rule requires the file stem
                    # to match the module name, so accept `rtl/<top>.sv`
                    # when the canonical filelist has already been repaired.
                    if (
                        not path.is_file()
                        and top_name
                        and item.get("name") in {f"{top_name}_top", "top", "wrapper"}
                    ):
                        alias_rel = f"rtl/{top_name}.sv"
                        alias_path = _resolve_ip_file(ip_dir, alias_rel)
                        if alias_rel in entry_set and alias_path.is_file():
                            path = alias_path
                            resolved_rel = alias_rel
                            manifest_mismatch = True
                    exists = path.is_file()
                    size = path.stat().st_size if exists else 0
                    text = ""
                    if exists:
                        try:
                            text = path.read_text(encoding="utf-8", errors="replace")[:200000]
                        except OSError:
                            text = ""
                    scaffold_only = bool(
                        re.search(r"Auto-generated manifest submodule", text, re.I)
                        or re.search(r"\balive_q\b", text)
                        or re.search(r"\bheartbeat_q\b", text)
                    )
                    placeholder = bool(re.search(r"\b(TBD|TODO:|FIXME|HACK)\b", text, re.I)) or scaffold_only
                    listed = rel in entry_set or resolved_rel in entry_set
                    if exists:
                        try:
                            listed = listed or path.relative_to(PROJECT_ROOT).as_posix() in entry_set
                        except Exception:
                            pass
                    include_header = False
                    if exists and not listed and path.suffix in {".sv", ".svh", ".vh"}:
                        include_name = path.name
                        include_header = (
                            bool(re.search(rf'`include\s+"{re.escape(include_name)}"', listed_text))
                            or path.stem.endswith("_pkg")
                            or "include header" in text[:2000].lower()
                        )
                    approved = exists and size >= 200 and (listed or include_header) and not placeholder
                    modules.append({
                        "name": item["name"],
                        "file": rel,
                        "resolved_file": resolved_rel,
                        "manifest_mismatch": manifest_mismatch or (resolved_rel != rel),
                        "status": "approved" if approved else ("partial" if exists else "missing"),
                        "exists": exists,
                        "listed": listed,
                        "include_header": include_header,
                        "bytes": size,
                        "placeholder": placeholder,
                        "scaffold_only": scaffold_only,
                    })
                approved = sum(1 for m in modules if m["status"] == "approved")
                mismatches = [m for m in modules if m.get("manifest_mismatch")]
                return {
                    "approved": approved,
                    "total": len(modules),
                    "pct": _pct(approved, len(modules)),
                    "filelist": fpath.relative_to(PROJECT_ROOT).as_posix() if fpath else "",
                    "manifest_mismatches": len(mismatches),
                    "manifest_mismatch_details": mismatches,
                    "blocked": bool(blocked_doc),
                    "blocker": str(blocked_doc.get("reason") or "") if blocked_doc else "",
                    "blocker_source": blocked_path.relative_to(PROJECT_ROOT).as_posix() if blocked_doc else "",
                    "questions": blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else [],
                    "next_action": str(blocked_doc.get("next_action") or "") if blocked_doc else "",
                    "modules": modules,
                }

            def _compile_progress(ip_dir: Path) -> dict:
                report_path = ip_dir / "rtl" / "rtl_compile.json"
                if not report_path.is_file():
                    return {
                        "status": "unknown",
                        "errors": 0,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": "",
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                try:
                    report = json.loads(report_path.read_text(encoding="utf-8"))
                except Exception:
                    return {
                        "status": "fail",
                        "errors": 1,
                        "diagnostics": 0,
                        "style_violations": 0,
                        "source": report_path.relative_to(PROJECT_ROOT).as_posix(),
                        "tool": "",
                        "command": "",
                        "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json",
                    }
                if report.get("dut_only") is not True or str(report.get("type") or "") != "rtl_compile":
                    status = "fail"
                elif report.get("passed") is True:
                    status = "pass"
                else:
                    status = "fail"
                return {
                    "status": status,
                    "errors": int(report.get("errors") or 0),
                    "diagnostics": int(report.get("diagnostics") or report.get("warnings") or 0),
                    "style_violations": int(report.get("style_violations") or 0),
                    "style_violation_details": report.get("style_violation_details") or [],
                    "returncode": int(report.get("returncode") or 0),
                    "source": report_path.relative_to(PROJECT_ROOT).as_posix(),
                    "tool": str(report.get("tool") or ""),
                    "command": str(report.get("command") or ""),
                    "criteria": "fresh DUT RTL compile report from <ip>/rtl/rtl_compile.json; warnings, Icarus sorry diagnostics, and procedural parameterized part-selects are blockers",
                }

            def _waived_warning_kinds(waivers: list[str]) -> set[str]:
                kinds: set[str] = set()
                for raw in waivers:
                    for token in re.findall(r"\b[A-Z][A-Z0-9_]{2,}\b", str(raw).upper()):
                        kinds.add(token)
                return kinds

            def _count_log_diagnostics(text: str, waivers: list[str] | None = None) -> dict:
                summary = re.search(
                    r"%Error:\s+Exiting due to\s+(\d+)\s+error\(s\),\s+(\d+)\s+warning\(s\)",
                    text,
                    re.I,
                )
                if summary:
                    return {
                        "errors": int(summary.group(1)),
                        "warnings": int(summary.group(2)),
                        "waived_warnings": 0,
                    }
                waived = _waived_warning_kinds(waivers or [])
                lines = text.splitlines()
                error_re = re.compile(r"(%ERROR\b|(^|\s)(ERROR|FATAL)(:|-)|\b\d+\s+ERROR\(S\))", re.I)
                errors = 0
                warnings = 0
                waived_warnings = 0
                for line in lines:
                    line_u = line.upper()
                    if re.search(r"%ERROR:\s+EXITING DUE TO \d+ WARNING", line_u):
                        continue
                    warning_kind = ""
                    m = re.search(r"%WARNING-([A-Z0-9_]+)", line_u)
                    if m:
                        warning_kind = m.group(1)
                    is_waived_warning = bool(warning_kind and warning_kind in waived)
                    is_warning_line = bool(
                        warning_kind
                        or re.search(r":\s*warning:", line, re.I)
                        or re.search(r"\bsorry:", line, re.I)
                    )
                    if is_warning_line and not error_re.search(line):
                        if is_waived_warning:
                            waived_warnings += 1
                        else:
                            warnings += 1
                    elif error_re.search(line):
                        errors += 1
                return {"errors": errors, "warnings": warnings, "waived_warnings": waived_warnings}

            def _lint_progress(ip_dir: Path, doc: dict) -> dict:
                lint_dir = ip_dir / "lint"
                latest: Path | None = None
                latest_mtime = -1.0
                diag = {"errors": 0, "warnings": 0, "waived_warnings": 0, "suppression_violations": 0}
                source_kind = ""
                command = ""
                tool = ""
                coding_rules = doc.get("coding_rules") if isinstance(doc, dict) else {}
                waivers = []
                if isinstance(coding_rules, dict):
                    raw_waivers = coding_rules.get("lint_waivers") or coding_rules.get("waivers") or []
                    if isinstance(raw_waivers, list):
                        waivers = [str(w) for w in raw_waivers]

                def _canonical_report_ok(report: dict) -> bool:
                    if not isinstance(report, dict):
                        return False
                    if report.get("dut_only") is not True:
                        return False
                    scope = str(report.get("scope") or report.get("type") or "").lower()
                    if scope not in {"dut", "rtl", "dut_lint", "rtl_lint"}:
                        return False
                    cmd = str(report.get("command") or "").lower()
                    if "cocotb" in cmd or "pytest" in cmd or "vvp" in cmd:
                        return False
                    return any(tok in cmd for tok in ("verilator", "pyslang", "iverilog", "slang"))

                def _reject_sim_log(text_l: str, pth: Path) -> bool:
                    parts_l = {part.lower() for part in pth.parts}
                    if {"tb", "cocotb", "sim", "sim_build"} & parts_l:
                        return True
                    sim_markers = (
                        "cocotb", "pytest", "results.xml", "module not found",
                        "vvp ", "make sim", "sim_build", "test_runner.py",
                    )
                    return any(marker in text_l for marker in sim_markers)

                report_candidates: list[Path] = []
                if lint_dir.is_dir():
                    report_candidates.extend(lint_dir.rglob("dut_lint.json"))
                    report_candidates.extend(lint_dir.rglob("rtl_lint.json"))
                    report_candidates.extend(lint_dir.rglob("*lint*.json"))
                for pth in report_candidates:
                    try:
                        report = json.loads(pth.read_text(encoding="utf-8"))
                    except Exception:
                        continue
                    if not _canonical_report_ok(report):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime <= latest_mtime:
                        continue
                    latest = pth
                    latest_mtime = mtime
                    diag = {
                        "errors": int(report.get("errors") or 0),
                        "warnings": int(report.get("warnings") or 0),
                        "waived_warnings": int(report.get("waived_warnings") or 0),
                        "suppression_violations": int(report.get("suppression_violation_count") or 0),
                    }
                    command = str(report.get("command") or "")
                    tool = str(report.get("tool") or "")
                    source_kind = "canonical-dut-lint-json"

                text_candidates: list[Path] = []
                if lint_dir.is_dir():
                    for suffix in ("*.log", "*.txt", "*.out"):
                        text_candidates.extend(lint_dir.rglob(suffix))
                for pth in text_candidates:
                    name_l = pth.name.lower()
                    if name_l.startswith("sim_report") or name_l.startswith("coverage_report") or "results" in name_l:
                        continue
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    text_l = text.lower()
                    if _reject_sim_log(text_l, pth):
                        continue
                    if not any(tok in text_l for tok in ("verilator", "pyslang", "iverilog", "slang", "lint-only")):
                        continue
                    mtime = pth.stat().st_mtime
                    if mtime > latest_mtime:
                        latest = pth
                        latest_mtime = mtime
                        diag = _count_log_diagnostics(text, waivers)
                        command = ""
                        tool = ""
                        source_kind = "lint-dir-text"
                warning_budget = 0
                status = "unknown" if latest is None else (
                    "pass" if (
                        diag["errors"] == 0
                        and diag["warnings"] == 0
                        and diag.get("suppression_violations", 0) == 0
                    ) else "fail"
                )
                return {
                    "status": status,
                    "errors": diag["errors"],
                    "warnings": diag["warnings"],
                    "suppression_violations": diag.get("suppression_violations", 0),
                    "warning_budget": warning_budget,
                    "waivers": waivers,
                    "source": latest.relative_to(PROJECT_ROOT).as_posix() if latest else "",
                    "source_kind": source_kind,
                    "tool": tool,
                    "command": command,
                    "criteria": "DUT RTL-only lint report from <ip>/lint; sim/cocotb/root cmd_output logs are not valid lint evidence",
                }

            def _sim_progress(ip_dir: Path, doc: dict) -> dict:
                tr = doc.get("test_requirements") if isinstance(doc, dict) else {}
                scenarios = tr.get("scenarios") if isinstance(tr, dict) else []
                scenario_count = len(scenarios) if isinstance(scenarios, list) else 0
                scoreboard = tr.get("scoreboard_checks") if isinstance(tr, dict) else None
                coverage_goals = tr.get("coverage_goals") if isinstance(tr, dict) else {}
                coverage_goal_count = len(coverage_goals) if isinstance(coverage_goals, dict) else 0
                scenario_rows = []
                if isinstance(scenarios, list):
                    for sc in scenarios:
                        if isinstance(sc, dict):
                            scenario_rows.append({
                                "id": str(sc.get("id") or ""),
                                "name": str(sc.get("name") or sc.get("title") or ""),
                                "expected": str(sc.get("expected") or ""),
                                "status": "pending",
                            })
                tb_dir = ip_dir / "tb"
                tests = []
                tb_text = ""
                if tb_dir.is_dir():
                    for pth in tb_dir.rglob("test*.py"):
                        try:
                            text = pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                        tb_text += "\n" + text
                        tests.extend(re.findall(r"@cocotb\.test|def\s+test_", text))
                    for pth in list(tb_dir.rglob("*.sv")) + list(tb_dir.rglob("*.v")):
                        try:
                            tb_text += "\n" + pth.read_text(encoding="utf-8", errors="replace")
                        except OSError:
                            continue
                for row in scenario_rows:
                    sid = row.get("id") or ""
                    if sid and re.search(rf"\b{re.escape(sid)}\b", tb_text):
                        row["status"] = "implemented"
                def _result_xml_paths() -> list[Path]:
                    canonical = ip_dir / "sim" / "results.xml"
                    roots = [
                        ip_dir / "sim",
                        ip_dir / "tb" / "cocotb",
                        ip_dir / "tb",
                    ]
                    out: list[Path] = []
                    seen: set[Path] = set()
                    for root in roots:
                        if not root.is_dir():
                            continue
                        for pth in root.rglob("*results.xml"):
                            rp = pth.resolve()
                            if rp not in seen:
                                out.append(pth)
                                seen.add(rp)
                    if not out:
                        return [canonical] if canonical.is_file() else []
                    canonical_rp = canonical.resolve() if canonical.exists() else None
                    noncanonical = [p for p in out if canonical_rp is None or p.resolve() != canonical_rp]
                    if not noncanonical:
                        return sorted(out, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)[:1]
                    newest_noncanonical = max(p.stat().st_mtime for p in noncanonical if p.exists())
                    # Cocotb often writes one result XML per config/run. Keep the latest
                    # result from each run directory, and ignore stale canonical summaries.
                    latest_by_dir: dict[Path, Path] = {}
                    for pth in noncanonical:
                        parent = pth.parent
                        cur = latest_by_dir.get(parent)
                        if cur is None or pth.stat().st_mtime > cur.stat().st_mtime:
                            latest_by_dir[parent] = pth
                    selected = [
                        p for p in latest_by_dir.values()
                        if p.exists() and p.stat().st_mtime >= newest_noncanonical - 10.0
                    ]
                    if canonical.is_file() and canonical.stat().st_mtime >= newest_noncanonical - 2.0:
                        selected.append(canonical)
                    return sorted(selected, key=lambda pth: pth.stat().st_mtime if pth.exists() else 0, reverse=True)

                results = []
                result_text = ""
                has_valid_result_xml = False
                testcase_names: set[str] = set()
                failed_names: set[str] = set()
                testcase_failed: dict[str, bool] = {}
                for pth in _result_xml_paths():
                    try:
                        text = pth.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        continue
                    if not text.strip():
                        continue
                    result_text += "\n" + text
                    parsed_xml = False
                    try:
                        import xml.etree.ElementTree as _ET
                        root_xml = _ET.fromstring(text)
                        cases = list(root_xml.iter("testcase"))
                        if cases:
                            parsed_xml = True
                            has_valid_result_xml = True
                            source_fail = 0
                            source_err = 0
                            for tc in cases:
                                name = tc.attrib.get("name") or ""
                                if not name:
                                    continue
                                testcase_names.add(name)
                                has_failure = tc.find("failure") is not None
                                has_error = tc.find("error") is not None
                                if has_failure or has_error:
                                    failed_names.add(name)
                                if has_failure:
                                    source_fail += 1
                                if has_error:
                                    source_err += 1
                                # Result files can be mirrored under sim/ and tb/cocotb/.
                                # _result_xml_paths() returns newest first, so keep the
                                # first observation for a testcase name to avoid double
                                # counting the same run.
                                testcase_failed.setdefault(name, has_failure or has_error)
                            results.append({
                                "tests": len(cases),
                                "failures": source_fail,
                                "errors": source_err,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                    except Exception:
                        parsed_xml = False
                    if not parsed_xml:
                        names = re.findall(r'<testcase[^>]*name="([^"]+)"', text)
                        testcase_names.update(names)
                        source_failed: set[str] = set()
                        for m in re.finditer(r'<testcase[^>]*name="([^"]+)"[^>]*>(.*?)</testcase>', text, re.S):
                            if re.search(r'<(?:failure|error)\b', m.group(2)):
                                source_failed.add(m.group(1))
                        failed_names.update(source_failed)
                        for name in names:
                            testcase_failed.setdefault(name, name in source_failed)
                        tests_attr = re.search(r'tests="(\d+)"', text)
                        fail_attr = re.search(r'failures="(\d+)"', text)
                        err_attr = re.search(r'errors="(\d+)"', text)
                        if tests_attr:
                            has_valid_result_xml = True
                            results.append({
                                "tests": int(tests_attr.group(1)),
                                "failures": int(fail_attr.group(1)) if fail_attr else 0,
                                "errors": int(err_attr.group(1)) if err_attr else 0,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                        elif names:
                            has_valid_result_xml = True
                            results.append({
                                "tests": len(names),
                                "failures": len(source_failed),
                                "errors": 0,
                                "source": pth.relative_to(PROJECT_ROOT).as_posix(),
                            })
                def _sid_matches_name(sid: str, name: str) -> bool:
                    if not sid:
                        return False
                    sid_l = sid.lower()
                    name_l = name.lower()
                    if sid_l in name_l:
                        return True
                    m = re.match(r"sc(\d+)$", sid_l)
                    return bool(m and f"sc{int(m.group(1)):02d}" in name_l)

                if has_valid_result_xml:
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in testcase_names):
                            row["status"] = "pass"
                    for row in scenario_rows:
                        sid = row.get("id") or ""
                        if any(_sid_matches_name(sid, name) for name in failed_names):
                            row["status"] = "fail"
                if testcase_failed:
                    total = len(testcase_failed)
                    fail = sum(1 for failed in testcase_failed.values() if failed)
                else:
                    total = sum(r["tests"] for r in results)
                    fail = sum(r["failures"] + r["errors"] for r in results)
                cov_pct = None
                cov_doc = {}
                cov_bins: dict[str, object] = {}
                coverage_limitations: dict[str, object] = {}
                coverage_static: dict[str, object] = {}
                check_total = None
                check_pass = None
                check_fail = None
                escalations = []
                cov_paths = sorted((ip_dir / "cov").glob("coverage*.json"), key=lambda p: p.stat().st_mtime if p.exists() else 0)
                for cov_json in cov_paths:
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict):
                            cov_pct = functional.get("pct", cov_pct)
                        if isinstance(cov_doc, dict):
                            bins = cov_doc.get("functional_bins")
                            if isinstance(bins, dict):
                                cov_bins.update(bins)
                        if isinstance(cov_doc, dict):
                            if isinstance(cov_doc.get("total_checks"), int):
                                check_total = (check_total or 0) + cov_doc.get("total_checks")
                            if isinstance(cov_doc.get("passed"), int):
                                check_pass = (check_pass or 0) + cov_doc.get("passed")
                            if isinstance(cov_doc.get("failed"), int):
                                check_fail = (check_fail or 0) + cov_doc.get("failed")
                            static_limits = cov_doc.get("static_universe_not_instrumented")
                            if isinstance(static_limits, dict):
                                for k, v in static_limits.items():
                                    coverage_limitations[k] = v
                            explicit_limits = cov_doc.get("limitations")
                            if isinstance(explicit_limits, dict):
                                for k, v in explicit_limits.items():
                                    coverage_limitations[k] = v
                            for metric_key in ("lines", "branches", "functions", "fsm_state"):
                                metric_doc = cov_doc.get(metric_key)
                                if isinstance(metric_doc, dict):
                                    coverage_static[metric_key] = metric_doc
                            raw_escalations = cov_doc.get("escalations")
                            if isinstance(raw_escalations, list):
                                escalations.extend(e for e in raw_escalations if isinstance(e, dict))
                    except Exception:
                        pass
                if cov_bins:
                    hit = sum(1 for v in cov_bins.values() if bool(v))
                    total_bins = max(scenario_count, len(cov_bins))
                    cov_pct = _pct(hit, total_bins)
                    for row in scenario_rows:
                        sid = str(row.get("id") or "")
                        if not sid or row.get("status") == "fail":
                            continue
                        prefix = f"{sid}_".lower()
                        if any(str(k).lower().startswith(prefix) and bool(v) for k, v in cov_bins.items()):
                            row["status"] = "pass"
                escalation_by_sid: dict[str, list[dict]] = {}
                for esc in escalations:
                    sid = str(esc.get("test_id") or esc.get("scenario") or esc.get("id") or "").strip()
                    if not sid:
                        text = json.dumps(esc, ensure_ascii=False)
                        m = re.search(r"\b(SC\d+)\b", text, re.I)
                        sid = m.group(1) if m else ""
                    if sid:
                        escalation_by_sid.setdefault(sid.lower(), []).append(esc)
                for row in scenario_rows:
                    sid = str(row.get("id") or "").lower()
                    row_escalations = escalation_by_sid.get(sid, [])
                    if not row_escalations:
                        continue
                    text = json.dumps(row_escalations, ensure_ascii=False).lower()
                    row["status"] = "blocked" if (
                        "blocked" in text or "infrastructure" in text or "parameter override" in text
                    ) else "fail"
                    row["escalation"] = row_escalations[0]
                if isinstance(check_fail, int) and check_fail > fail:
                    fail = check_fail
                has_sim_evidence = total > 0
                sim_pass_evidence = has_sim_evidence and fail == 0
                passed_scenarios = sum(1 for r in scenario_rows if r["status"] == "pass")
                failed_scenarios = sum(1 for r in scenario_rows if r["status"] == "fail")
                all_scenarios_passed = scenario_count == 0 or passed_scenarios >= scenario_count
                has_coverage_numbers = cov_pct is not None or isinstance(check_total, int)
                functional_closed = cov_pct is not None and float(cov_pct) >= 100.0
                if not has_sim_evidence:
                    coverage_status = "pending"
                elif fail:
                    coverage_status = "fail"
                elif not all_scenarios_passed:
                    coverage_status = "pending"
                elif not cov_paths:
                    coverage_status = "pending"
                elif not has_coverage_numbers:
                    coverage_status = "pending"
                elif coverage_limitations:
                    coverage_status = "blocked"
                elif not functional_closed:
                    coverage_status = "fail"
                else:
                    coverage_status = "pass"
                return {
                    "dv_plan": {
                        "scenarios": scenario_count,
                        "scoreboard_checks": scoreboard,
                        "coverage_goals": coverage_goal_count,
                        "scenario_rows": scenario_rows,
                    },
                    "implemented_scenarios": sum(1 for r in scenario_rows if r["status"] in ("implemented", "pass")),
                    "passed_scenarios": passed_scenarios,
                    "failed_scenarios": failed_scenarios,
                    "implemented_tests": len(tests),
                    "results": {
                        "total": total,
                        "pass": max(total - fail, 0),
                        "fail": fail,
                        "sources": [r["source"] for r in results],
                        "check_total": check_total,
                        "check_pass": check_pass,
                        "check_fail": check_fail,
                    },
                    "coverage": {
                        "status": coverage_status,
                        "functional_pct": cov_pct,
                        "static": coverage_static,
                        "criteria": coverage_goals if isinstance(coverage_goals, dict) else {},
                        "limitations": coverage_limitations,
                    },
                    "escalations": escalations,
                }

            def _req_progress(ip_dir: Path) -> dict:
                req_dir = ip_dir / "req"
                files = []
                if req_dir.is_dir():
                    files = [
                        p for p in sorted(req_dir.rglob("*"))
                        if p.is_file() and p.suffix.lower() in {".md", ".txt", ".yaml", ".yml", ".json"}
                    ]
                total_bytes = sum(p.stat().st_size for p in files if p.exists())
                text = ""
                for p in files[:12]:
                    try:
                        text += "\n" + p.read_text(encoding="utf-8", errors="replace")[:200000]
                    except OSError:
                        pass
                placeholder = bool(re.search(r"\b(TBD|TODO|FIXME|HACK)\b", text, re.I))
                enough = total_bytes >= 1000 and not placeholder
                return {
                    "status": "ok" if files and enough else ("partial" if files else "pending"),
                    "files": [p.relative_to(PROJECT_ROOT).as_posix() for p in files[:12]],
                    "bytes": total_bytes,
                    "placeholder": placeholder,
                    "criteria": "REQ capture exists under <ip>/req, has substantive content, and contains no TBD/TODO/FIXME placeholders",
                }

            def _fl_model_progress(ip_dir: Path, doc: dict | None = None) -> dict:
                model_path = ip_dir / "model" / "functional_model.py"
                check_path = ip_dir / "model" / "fl_model_check.json"
                exists = model_path.is_file()
                size = model_path.stat().st_size if exists else 0
                text = ""
                if exists:
                    try:
                        text = model_path.read_text(encoding="utf-8", errors="replace")
                    except OSError:
                        text = ""
                check = {}
                if check_path.is_file():
                    try:
                        check = json.loads(check_path.read_text(encoding="utf-8"))
                    except Exception:
                        check = {"passed": False}
                has_api = "class FunctionalModel" in text and "def apply" in text
                imports_ok = bool(check.get("passed") is True)
                fm = doc.get("function_model") if isinstance(doc, dict) and isinstance(doc.get("function_model"), dict) else {}
                txns = fm.get("transactions") if isinstance(fm.get("transactions"), list) else []
                expected_txns = [
                    str(tx.get("id") or tx.get("name") or "").strip()
                    for tx in txns
                    if isinstance(tx, dict) and (tx.get("id") or tx.get("name"))
                ]
                trace_sources = [
                    check.get("transaction_results"),
                    check.get("transaction_traceability"),
                    (check.get("self_check") or {}).get("transaction_results") if isinstance(check.get("self_check"), dict) else None,
                    (check.get("self_check") or {}).get("transaction_traceability") if isinstance(check.get("self_check"), dict) else None,
                ]
                trace_text = json.dumps(trace_sources, ensure_ascii=False).lower()
                traced_txns = [
                    txn for txn in expected_txns
                    if txn.lower() in trace_text
                ]
                trace_complete = not expected_txns or len(traced_txns) == len(expected_txns)
                status = "pass" if exists and size >= 500 and has_api and imports_ok and trace_complete else (
                    "partial" if exists else "pending"
                )
                return {
                    "status": status,
                    "source": model_path.relative_to(PROJECT_ROOT).as_posix() if exists else "",
                    "check_source": check_path.relative_to(PROJECT_ROOT).as_posix() if check_path.is_file() else "",
                    "bytes": size,
                    "has_apply": has_api,
                    "self_check": check,
                    "transactions_expected": expected_txns,
                    "transactions_traced": traced_txns,
                    "trace_complete": trace_complete,
                    "criteria": "executable Python FL model generated from SSOT with FunctionalModel.apply(txn), passing self-check, and tracing every SSOT function_model transaction",
                }

            def _fl_decomp_progress(ip_dir: Path) -> dict:
                path = ip_dir / "model" / "decomposition.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                units = doc.get("units") if isinstance(doc, dict) else []
                if not isinstance(units, list):
                    units = []
                kinds = sorted({str(u.get("kind")) for u in units if isinstance(u, dict) and u.get("kind")})
                status = "pass" if path.is_file() and isinstance(units, list) and len(units) >= 2 and doc.get("complete") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": path.relative_to(PROJECT_ROOT).as_posix() if path.is_file() else "",
                    "units": len(units) if isinstance(units, list) else 0,
                    "kinds": kinds,
                    "criteria": "FL model decomposition traces protocol/register/memory/datapath/FSM/error/security units to SSOT sections",
                }

            def _fcov_plan_progress(ip_dir: Path) -> dict:
                path = ip_dir / "cov" / "fcov_plan.json"
                doc = {}
                if path.is_file():
                    try:
                        doc = json.loads(path.read_text(encoding="utf-8"))
                    except Exception:
                        doc = {}
                bins = doc.get("bins") if isinstance(doc, dict) else []
                if not isinstance(bins, list):
                    bins = []
                classes = sorted({str(b.get("class")) for b in bins if isinstance(b, dict) and b.get("class")})
                status = "pass" if path.is_file() and isinstance(bins, list) and len(bins) > 0 and doc.get("planned_before_rtl") is True else (
                    "partial" if path.is_file() else "pending"
                )
                return {
                    "status": status,
                    "source": path.relative_to(PROJECT_ROOT).as_posix() if path.is_file() else "",
                    "bins": len(bins) if isinstance(bins, list) else 0,
                    "classes": classes,
                    "summary": doc.get("summary") if isinstance(doc, dict) else {},
                    "criteria": "functional coverage bins are planned from SSOT/FL model before RTL signoff",
                }

            def _equivalence_progress(ip_dir: Path) -> dict:
                goals_path = ip_dir / "verify" / "equivalence_goals.json"
                compare_path = ip_dir / "sim" / "fl_rtl_compare.json"
                classify_path = ip_dir / "sim" / "mismatch_classification.json"
                goals_doc: dict[str, Any] = {}
                compare_doc: dict[str, Any] = {}
                classify_doc: dict[str, Any] = {}
                if goals_path.is_file():
                    try:
                        loaded = json.loads(goals_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            goals_doc = loaded
                    except Exception:
                        goals_doc = {}
                if compare_path.is_file():
                    try:
                        loaded = json.loads(compare_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            compare_doc = loaded
                    except Exception:
                        compare_doc = {}
                if classify_path.is_file():
                    try:
                        loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            classify_doc = loaded
                    except Exception:
                        classify_doc = {}

                goals = goals_doc.get("goals") if isinstance(goals_doc.get("goals"), list) else []
                goal_summary = goals_doc.get("summary") if isinstance(goals_doc.get("summary"), dict) else {}
                source_of_truth = goals_doc.get("source_of_truth") if isinstance(goals_doc.get("source_of_truth"), dict) else {}
                authority_contract = source_of_truth.get("authority_contract") if isinstance(source_of_truth.get("authority_contract"), dict) else {}
                compare_summary = compare_doc.get("summary") if isinstance(compare_doc.get("summary"), dict) else {}
                classifications = classify_doc.get("classifications") if isinstance(classify_doc.get("classifications"), list) else []
                classification_counts: dict[str, int] = {}
                owner_counts: dict[str, int] = {}
                loopable_repairs = 0
                human_gated_repairs = 0
                for item in classifications:
                    if not isinstance(item, dict):
                        continue
                    cls = str(item.get("classification") or "unknown")
                    owner = str(item.get("owner") or "unknown")
                    classification_counts[cls] = classification_counts.get(cls, 0) + 1
                    owner_counts[owner] = owner_counts.get(owner, 0) + 1
                    if item.get("llm_loop_allowed") is True:
                        loopable_repairs += 1
                    elif item.get("llm_loop_allowed") is False:
                        human_gated_repairs += 1
                total = int(goal_summary.get("total") or len(goals) or 0)
                generated = total
                checked = int(compare_summary.get("goals_checked") or 0)
                passed = int(compare_summary.get("goals_passed") or 0)
                failed = int(compare_summary.get("goals_failed") or 0)
                blocked = int(compare_summary.get("goals_blocked") or goal_summary.get("blocked") or 0)
                untested = int(compare_summary.get("goals_untested") or 0)
                compare_status = str(compare_doc.get("status") or "")
                stale_evidence = compare_summary.get("stale_evidence") if isinstance(compare_summary.get("stale_evidence"), list) else []
                if compare_status == "pass":
                    status = "pass"
                elif compare_status == "fail":
                    status = "fail"
                elif compare_status == "stale" or stale_evidence:
                    status = "stale"
                elif blocked:
                    status = "blocked"
                elif goals_path.is_file() and total:
                    status = "partial"
                else:
                    status = "pending"
                failed_ids = []
                blocked_ids = []
                untested_ids = []
                for item in compare_doc.get("goals") if isinstance(compare_doc.get("goals"), list) else []:
                    if not isinstance(item, dict):
                        continue
                    goal_id = str(item.get("goal_id") or "")
                    if item.get("status") == "fail":
                        failed_ids.append(goal_id)
                    elif item.get("status") == "blocked":
                        blocked_ids.append(goal_id)
                    elif item.get("status") == "untested":
                        untested_ids.append(goal_id)
                return {
                    "status": status,
                    "total": total,
                    "generated": generated,
                    "checked": checked,
                    "passed": passed,
                    "failed": failed,
                    "blocked": blocked,
                    "untested": untested,
                    "failed_goal_ids": [x for x in failed_ids if x][:12],
                    "blocked_goal_ids": [x for x in blocked_ids if x][:12],
                    "untested_goal_ids": [x for x in untested_ids if x][:12],
                    "classifications": len(classifications),
                    "loopable_repairs": loopable_repairs,
                    "human_gated_repairs": human_gated_repairs,
                    "classification_counts": classification_counts,
                    "owner_counts": owner_counts,
                    "module_total": int(goal_summary.get("module_total") or 0),
                    "module_required": int(goal_summary.get("module_required") or 0),
                    "module_blocked": int(goal_summary.get("module_blocked") or 0),
                    "authority_contract": authority_contract,
                    "general_evaluation_criteria": authority_contract.get("general_evaluation_criteria") if isinstance(authority_contract.get("general_evaluation_criteria"), list) else [],
                    "locked_artifacts": authority_contract.get("locked_artifacts") if isinstance(authority_contract.get("locked_artifacts"), list) else [],
                    "llm_editable_artifacts": authority_contract.get("llm_editable_artifacts") if isinstance(authority_contract.get("llm_editable_artifacts"), list) else [],
                    "loopable_evidence_points": authority_contract.get("loopable_evidence_points") if isinstance(authority_contract.get("loopable_evidence_points"), list) else [],
                    "loopable_oracles": authority_contract.get("loopable_oracles") if isinstance(authority_contract.get("loopable_oracles"), list) else [],
                    "missing_evidence": compare_summary.get("missing_evidence") if isinstance(compare_summary.get("missing_evidence"), list) else [],
                    "stale_evidence": stale_evidence,
                    "evidence": goals_path.relative_to(PROJECT_ROOT).as_posix() if goals_path.is_file() else "",
                    "compare_evidence": compare_path.relative_to(PROJECT_ROOT).as_posix() if compare_path.is_file() else "",
                    "classification_evidence": classify_path.relative_to(PROJECT_ROOT).as_posix() if classify_path.is_file() else "",
                    "next_action": (
                        "none; all equivalence goals passed"
                        if status == "pass" else
                        "rerun /sim <ip> and /sim-debug <ip>; existing evidence is stale"
                        if status == "stale" else
                        "answer SSOT/human gate questions from mismatch_classification.json"
                        if status == "blocked" else
                        "repair classified FL/RTL/TB/coverage owner from mismatch_classification.json"
                        if status == "fail" else
                        "run sim_debug comparator after TB emits scoreboard_events.jsonl"
                        if goals_path.is_file() else
                        "run /ssot-equiv-goals <ip>"
                    ),
                    "owner": (
                        "human gate" if status == "blocked" else
                        "LLM loop" if status in {"fail", "partial", "pending"} else
                        "LLM loop"
                    ),
                    "criteria": "SSOT-derived equivalence goals exist, TB scoreboard checks them, sim_debug compare passes every required goal, and all mismatches are classified",
                }

            def _goal_audit_progress(ip_dir: Path) -> dict:
                audit_path = ip_dir / "sim" / "fl_rtl_goal_audit.json"
                doc: dict[str, Any] = {}
                if audit_path.is_file():
                    try:
                        loaded = json.loads(audit_path.read_text(encoding="utf-8"))
                        if isinstance(loaded, dict):
                            doc = loaded
                    except Exception:
                        doc = {}
                summary = doc.get("summary") if isinstance(doc.get("summary"), dict) else {}
                checks = doc.get("checks") if isinstance(doc.get("checks"), list) else []
                blockers = [str(x) for x in summary.get("blockers") or []] if isinstance(summary, dict) else []
                source_paths = [
                    ip_dir / "yaml" / f"{ip_dir.name}.ssot.yaml",
                    ip_dir / "model" / "functional_model.py",
                    ip_dir / "model" / "fl_model_check.json",
                    ip_dir / "model" / "decomposition.json",
                    ip_dir / "cov" / "fcov_plan.json",
                    ip_dir / "verify" / "equivalence_goals.json",
                    ip_dir / "sim" / "scoreboard_events.jsonl",
                    ip_dir / "sim" / "results.xml",
                    ip_dir / "tb" / "cocotb" / "results.xml",
                    ip_dir / "cov" / "coverage.json",
                    ip_dir / "sim" / "fl_rtl_compare.json",
                    ip_dir / "sim" / "mismatch_classification.json",
                    ip_dir / "rtl" / "rtl_compile.json",
                    ip_dir / "lint" / "dut_lint.json",
                    ip_dir / "lint" / "rtl_lint.json",
                ]
                stale_evidence: list[str] = []
                if audit_path.is_file():
                    existing_sources = [p for p in source_paths if p.is_file()]
                    if existing_sources:
                        newest = max(existing_sources, key=lambda p: p.stat().st_mtime)
                        if audit_path.stat().st_mtime + 0.5 < newest.stat().st_mtime:
                            try:
                                stale_evidence.append(
                                    f"{audit_path.relative_to(PROJECT_ROOT)} older than {newest.relative_to(PROJECT_ROOT)}"
                                )
                            except ValueError:
                                stale_evidence.append("goal audit artifact is older than a source artifact")
                raw_status = str(doc.get("status") or "") if doc else ""
                if stale_evidence:
                    status = "stale"
                elif raw_status == "pass":
                    status = "pass"
                elif raw_status == "fail":
                    status = "fail"
                elif audit_path.is_file():
                    status = "partial"
                else:
                    status = "pending"
                return {
                    "status": status,
                    "source": audit_path.relative_to(PROJECT_ROOT).as_posix() if audit_path.is_file() else "",
                    "total_checks": int(summary.get("total_checks") or 0) if isinstance(summary, dict) else 0,
                    "passed_checks": int(summary.get("passed_checks") or 0) if isinstance(summary, dict) else 0,
                    "failed_checks": int(summary.get("failed_checks") or 0) if isinstance(summary, dict) else 0,
                    "blockers": blockers,
                    "stale_evidence": stale_evidence,
                    "generated_at": doc.get("generated_at") if isinstance(doc, dict) else "",
                    "checks": [
                        {
                            "id": str(item.get("id") or ""),
                            "status": str(item.get("status") or ""),
                            "owner": str(item.get("owner") or ""),
                            "next_action": str(item.get("next_action") or ""),
                        }
                        for item in checks[:20]
                        if isinstance(item, dict)
                    ],
                    "next_action": (
                        "none; goal audit passed"
                        if status == "pass" else
                        "rerun /goal-audit <ip>; existing audit is stale"
                        if status == "stale" else
                        "inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage"
                        if status == "fail" else
                        "run /goal-audit <ip> after sim-debug and coverage evidence exist"
                    ),
                    "owner": "LLM loop",
                    "criteria": "single disk-truth audit proves REQ, SSOT, FL, cycle model, RTL DUT-only compile/lint, TB scoreboard, sim, compare, coverage, and signoff evidence",
                }

            def _strict_gate_from_progress(progress: dict) -> dict:
                ssot = progress.get("ssot") if isinstance(progress, dict) else {}
                req = progress.get("req") if isinstance(progress, dict) else {}
                fl_model = progress.get("fl_model") if isinstance(progress, dict) else {}
                fl_decomp = progress.get("fl_decomp") if isinstance(progress, dict) else {}
                fcov_plan = progress.get("fcov_plan") if isinstance(progress, dict) else {}
                equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                rtl = progress.get("rtl") if isinstance(progress, dict) else {}
                compile_st = progress.get("compile") if isinstance(progress, dict) else {}
                lint = progress.get("lint") if isinstance(progress, dict) else {}
                sim = progress.get("sim") if isinstance(progress, dict) else {}
                dv = sim.get("dv_plan") if isinstance(sim, dict) else {}
                results = sim.get("results") if isinstance(sim, dict) else {}
                coverage = sim.get("coverage") if isinstance(sim, dict) else {}

                ssot_total = int(ssot.get("total") or 0) if isinstance(ssot, dict) else 0
                ssot_approved = int(ssot.get("approved") or 0) if isinstance(ssot, dict) else 0
                req_status = str(req.get("status") or "pending") if isinstance(req, dict) else "pending"
                fl_model_status = str(fl_model.get("status") or "pending") if isinstance(fl_model, dict) else "pending"
                fl_decomp_status = str(fl_decomp.get("status") or "pending") if isinstance(fl_decomp, dict) else "pending"
                fcov_plan_status = str(fcov_plan.get("status") or "pending") if isinstance(fcov_plan, dict) else "pending"
                equivalence_status = str(equivalence.get("status") or "pending") if isinstance(equivalence, dict) else "pending"
                goal_audit_status = str(goal_audit.get("status") or "pending") if isinstance(goal_audit, dict) else "pending"
                rtl_total = int(rtl.get("total") or 0) if isinstance(rtl, dict) else 0
                rtl_approved = int(rtl.get("approved") or 0) if isinstance(rtl, dict) else 0
                rtl_mismatches = int(rtl.get("manifest_mismatches") or 0) if isinstance(rtl, dict) else 0
                rtl_quality = int(rtl.get("quality_issue_count") or 0) if isinstance(rtl, dict) else 0
                rtl_quality_issues = rtl.get("quality_issues") if isinstance(rtl, dict) and isinstance(rtl.get("quality_issues"), list) else []
                rtl_blocked = bool(rtl.get("blocked")) if isinstance(rtl, dict) else False
                rtl_blocker = str(rtl.get("blocker") or "") if isinstance(rtl, dict) else ""
                compile_status = str(compile_st.get("status") or "unknown") if isinstance(compile_st, dict) else "unknown"
                scenario_total = int(dv.get("scenarios") or 0) if isinstance(dv, dict) else 0
                implemented = int(sim.get("implemented_scenarios") or 0) if isinstance(sim, dict) else 0
                passed_scenarios = int(sim.get("passed_scenarios") or 0) if isinstance(sim, dict) else 0
                failed_scenarios = int(sim.get("failed_scenarios") or 0) if isinstance(sim, dict) else 0
                result_total = int(results.get("total") or 0) if isinstance(results, dict) else 0
                result_fail = int(results.get("fail") or 0) if isinstance(results, dict) else 0
                lint_status = str(lint.get("status") or "unknown") if isinstance(lint, dict) else "unknown"
                raw_cov_status = str(coverage.get("status") or "unknown") if isinstance(coverage, dict) else "unknown"
                all_scenarios_passed = scenario_total == 0 or passed_scenarios >= scenario_total
                sim_pass_evidence = result_total > 0 and result_fail == 0 and failed_scenarios == 0 and all_scenarios_passed
                if result_total <= 0:
                    cov_status = "pending"
                elif result_fail:
                    cov_status = "fail"
                elif not all_scenarios_passed:
                    cov_status = "pending"
                else:
                    cov_status = raw_cov_status

                ssot_status = "ok" if ssot_total and ssot_approved == ssot_total else (
                    "partial" if ssot_approved else "pending"
                )
                rtl_modules_status = "blocked" if rtl_blocked else ("ok" if rtl_total and rtl_approved == rtl_total else (
                    "partial" if rtl_approved else "pending"
                ))
                if rtl_blocked:
                    rtl_status = "blocked"
                elif lint_status == "fail":
                    rtl_status = "fail"
                elif compile_status == "fail":
                    rtl_status = "fail"
                elif rtl_mismatches:
                    rtl_status = "fail"
                elif rtl_modules_status == "ok" and compile_status == "pass" and lint_status == "pass":
                    rtl_status = "ok"
                elif rtl_modules_status == "pending":
                    rtl_status = "pending"
                else:
                    rtl_status = "partial"

                tb_status = "ok" if scenario_total and implemented >= scenario_total else (
                    "partial" if implemented else "pending"
                )
                if result_total <= 0:
                    sim_status = "pending"
                elif result_fail or failed_scenarios:
                    sim_status = "fail"
                elif not all_scenarios_passed:
                    sim_status = "partial"
                else:
                    sim_status = "ok"

                blockers: list[str] = []
                if ssot_status != "ok":
                    blockers.append(f"SSOT sections {ssot_approved}/{ssot_total} approved")
                if req_status != "ok":
                    blockers.append(f"REQ capture {req_status}")
                if fl_model_status != "pass":
                    blockers.append(f"FL model {fl_model_status}")
                if fl_decomp_status != "pass":
                    blockers.append(f"FL decomposition {fl_decomp_status}")
                if fcov_plan_status != "pass":
                    blockers.append(f"FCOV plan {fcov_plan_status}")
                if equivalence_status != "pass":
                    blockers.append(
                        "equivalence goals "
                        f"{equivalence_status} "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} passed"
                    )
                if goal_audit_status != "pass":
                    audit_blockers = goal_audit.get("blockers", []) if isinstance(goal_audit, dict) else []
                    blockers.append(
                        "goal audit "
                        f"{goal_audit_status}"
                        + (f" blockers={','.join(str(x) for x in audit_blockers[:6])}" if audit_blockers else "")
                    )
                if rtl_blocked:
                    blockers.append(f"RTL blocked: {rtl_blocker or 'SSOT decision required'}")
                elif rtl_modules_status != "ok":
                    blockers.append(f"RTL modules {rtl_approved}/{rtl_total} approved")
                if rtl_mismatches:
                    blockers.append(f"SSOT/RTL manifest mismatch {rtl_mismatches}")
                if rtl_quality:
                    first_issue = ""
                    if rtl_quality_issues and isinstance(rtl_quality_issues[0], dict):
                        first_issue = str(rtl_quality_issues[0].get("issue") or "")
                    blockers.append(
                        f"RTL quality issues {rtl_quality}"
                        + (f": {first_issue}" if first_issue else "")
                    )
                if compile_status != "pass":
                    comp_err = compile_st.get("errors", 0) if isinstance(compile_st, dict) else 0
                    comp_diag = compile_st.get("diagnostics", 0) if isinstance(compile_st, dict) else 0
                    comp_style = compile_st.get("style_violations", 0) if isinstance(compile_st, dict) else 0
                    blockers.append(f"RTL compile {compile_status} E{comp_err}/D{comp_diag}/S{comp_style}")
                if lint_status != "pass":
                    err = lint.get("errors", 0) if isinstance(lint, dict) else 0
                    warn = lint.get("warnings", 0) if isinstance(lint, dict) else 0
                    suppressions = lint.get("suppression_violations", 0) if isinstance(lint, dict) else 0
                    suffix = f"/S{suppressions}" if suppressions else ""
                    blockers.append(f"lint {lint_status} E{err}/W{warn}{suffix}")
                if tb_status != "ok":
                    blockers.append(f"DV scenarios implemented {implemented}/{scenario_total}")
                if result_total <= 0:
                    blockers.append("no fresh sim result XML found")
                elif result_fail:
                    blockers.append(f"simulation failures {result_fail}/{result_total}")
                if scenario_total and passed_scenarios < scenario_total:
                    blockers.append(f"sim scenarios passed {passed_scenarios}/{scenario_total}")
                if cov_status != "pass":
                    if not sim_pass_evidence:
                        blockers.append("coverage requires fresh passing simulation result")
                    else:
                        blockers.append(f"coverage {cov_status}")

                if any(v in {"fail"} for v in (rtl_status, sim_status, lint_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "fail"
                elif any(v in {"blocked", "stale"} for v in (rtl_status, sim_status, cov_status, equivalence_status, goal_audit_status)):
                    signoff = "blocked"
                elif not blockers:
                    signoff = "pass"
                elif ssot_approved or rtl_approved or implemented or result_total:
                    signoff = "partial"
                else:
                    signoff = "pending"

                status = {
                    "req": req_status,
                    "ssot": ssot_status,
                    "fl_model": fl_model_status,
                    "fl_decomp": fl_decomp_status,
                    "fcov_plan": fcov_plan_status,
                    "equivalence_goals": equivalence_status,
                    "goal_audit": goal_audit_status,
                    "rtl": rtl_status,
                    "lint": lint_status,
                    "tb": tb_status,
                    "sim_debug": sim_status,
                    "coverage": cov_status,
                    "signoff": signoff,
                }
                detail = {
                    "req": f"{req_status}: {len(req.get('files', [])) if isinstance(req, dict) else 0} requirement artifact(s)",
                    "ssot": f"{ssot_approved}/{ssot_total} canonical sections approved",
                    "fl_model": (
                        f"{fl_model_status}: "
                        f"{fl_model.get('source', '') if isinstance(fl_model, dict) else ''} "
                        f"self_check={bool(fl_model.get('self_check', {}).get('passed')) if isinstance(fl_model, dict) else False}"
                    ),
                    "fl_decomp": (
                        f"{fl_decomp_status}: "
                        f"{fl_decomp.get('units', 0) if isinstance(fl_decomp, dict) else 0} unit(s)"
                    ),
                    "fcov_plan": (
                        f"{fcov_plan_status}: "
                        f"{fcov_plan.get('bins', 0) if isinstance(fcov_plan, dict) else 0} bin(s)"
                    ),
                    "equivalence_goals": (
                        f"{equivalence_status}: "
                        f"{equivalence.get('passed', 0) if isinstance(equivalence, dict) else 0}/"
                        f"{equivalence.get('total', 0) if isinstance(equivalence, dict) else 0} pass; "
                        f"checked {equivalence.get('checked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"failed {equivalence.get('failed', 0) if isinstance(equivalence, dict) else 0}; "
                        f"blocked {equivalence.get('blocked', 0) if isinstance(equivalence, dict) else 0}; "
                        f"untested {equivalence.get('untested', 0) if isinstance(equivalence, dict) else 0}"
                    ),
                    "goal_audit": (
                        f"{goal_audit_status}: "
                        f"{goal_audit.get('passed_checks', 0) if isinstance(goal_audit, dict) else 0}/"
                        f"{goal_audit.get('total_checks', 0) if isinstance(goal_audit, dict) else 0} checks; "
                        f"blockers {', '.join(goal_audit.get('blockers', [])[:6]) if isinstance(goal_audit.get('blockers', []), list) else ''}"
                    ),
                    "rtl": (
                        f"{rtl_approved}/{rtl_total} RTL files approved; "
                        f"blocked {rtl_blocked}; "
                        f"manifest mismatch {rtl_mismatches}; "
                        f"quality issues {rtl_quality}; "
                        f"compile {compile_status} "
                        f"E{compile_st.get('errors', 0) if isinstance(compile_st, dict) else 0}/"
                        f"D{compile_st.get('diagnostics', 0) if isinstance(compile_st, dict) else 0}/"
                        f"S{compile_st.get('style_violations', 0) if isinstance(compile_st, dict) else 0}; "
                        f"lint {lint_status} E{lint.get('errors', 0) if isinstance(lint, dict) else 0}/"
                        f"W{lint.get('warnings', 0) if isinstance(lint, dict) else 0}"
                        f"/S{lint.get('suppression_violations', 0) if isinstance(lint, dict) else 0}"
                    ),
                    "tb": f"{implemented}/{scenario_total} SSOT DV scenarios implemented",
                    "sim_debug": (
                        f"results {max(result_total - result_fail, 0)} pass / "
                        f"{result_fail} fail / {result_total} total; coverage {cov_status}"
                    ),
                    "coverage": f"coverage {cov_status}",
                    "signoff": "pass" if signoff == "pass" else "; ".join(blockers[:6]),
                }

                def _first_source(*values: Any) -> str:
                    for value in values:
                        if isinstance(value, str) and value:
                            return value
                        if isinstance(value, list) and value:
                            return str(value[0])
                    return ""

                def _owner(stage: str, stage_status: str) -> str:
                    if stage == "req" and stage_status != "ok":
                        return "human gate"
                    if stage == "rtl" and stage_status == "blocked":
                        return "human gate" if rtl_blocked else "blocked"
                    if stage == "signoff":
                        if stage_status == "pass":
                            return "human gate"
                        if req_status != "ok" or cov_status == "blocked" or equivalence_status == "blocked":
                            return "human gate"
                    if stage == "equivalence_goals" and stage_status == "blocked":
                        return "human gate"
                    if stage == "coverage" and stage_status == "blocked":
                        return "human gate"
                    if stage_status in {"blocked"}:
                        return "blocked"
                    return "LLM loop"

                def _next_action(stage: str, stage_status: str) -> str:
                    if stage_status in {"ok", "pass"}:
                        if stage == "signoff":
                            return "tool evidence passed; human final acceptance may proceed"
                        return "none; evidence accepted"
                    if stage == "req":
                        return "answer missing requirement questions or refresh req-gen ledger"
                    if stage == "ssot":
                        return "repair SSOT sections or ask human for undefined behavior"
                    if stage == "fl_model":
                        return "run fl-model-gen and repair FunctionalModel self-check"
                    if stage == "fl_decomp":
                        return "generate SSOT-traced FL decomposition units"
                    if stage == "fcov_plan":
                        return "generate planned functional coverage bins from SSOT/FL"
                    if stage == "equivalence_goals":
                        return equivalence.get("next_action", "run /ssot-equiv-goals and sim_debug compare") if isinstance(equivalence, dict) else "run /ssot-equiv-goals"
                    if stage == "goal_audit":
                        return goal_audit.get("next_action", "run /goal-audit after evidence exists") if isinstance(goal_audit, dict) else "run /goal-audit"
                    if stage == "rtl":
                        if stage_status == "blocked":
                            return "answer rtl_blocked SSOT questions, refresh SSOT/FL model, then rerun /ssot-rtl"
                        return "run rtl-gen repair from SSOT, compile, and lint evidence"
                    if stage == "lint":
                        return "repair DUT-only lint diagnostics or request explicit waiver"
                    if stage == "tb":
                        return "generate missing cocotb/pyuvm scenario checkers"
                    if stage == "sim_debug":
                        return "classify mismatch owner, then repair RTL/FL/TB or ask on SSOT ambiguity"
                    if stage == "coverage":
                        return "close missing planned bins or request explicit waiver"
                    if stage == "signoff":
                        return "resolve blockers before evidence signoff can pass"
                    return "inspect stage evidence"

                def _stage_entry(stage: str, stage_status: str, validator: str, evidence: str = "") -> dict:
                    blocker = detail.get(stage, "")
                    if stage_status in {"ok", "pass"}:
                        blocker = ""
                    elif stage == "rtl" and rtl_blocked and rtl_blocker:
                        blocker = rtl_blocker
                    return {
                        "stage": stage,
                        "status": stage_status,
                        "owner": _owner(stage, stage_status),
                        "validator": validator,
                        "evidence": evidence,
                        "blocker": blocker,
                        "next_action": _next_action(stage, stage_status),
                    }

                ownership = {
                    "req": _stage_entry("req", req_status, "REQ ledger placeholder/substance check", _first_source(req.get("files") if isinstance(req, dict) else "")),
                    "ssot": _stage_entry("ssot", ssot_status, "canonical SSOT section checker", "yaml/<ip>.ssot.yaml"),
                    "fl_model": _stage_entry("fl_model", fl_model_status, "FunctionalModel API + self-check", _first_source(fl_model.get("source", "") if isinstance(fl_model, dict) else "")),
                    "fl_decomp": _stage_entry("fl_decomp", fl_decomp_status, "decomposition completeness checker", _first_source(fl_decomp.get("source", "") if isinstance(fl_decomp, dict) else "")),
                    "fcov_plan": _stage_entry("fcov_plan", fcov_plan_status, "planned coverage-bin checker", _first_source(fcov_plan.get("source", "") if isinstance(fcov_plan, dict) else "")),
                    "equivalence_goals": _stage_entry("equivalence_goals", equivalence_status, "FL-vs-RTL equivalence goal + scoreboard comparator", _first_source(equivalence.get("compare_evidence", "") if isinstance(equivalence, dict) else "", equivalence.get("evidence", "") if isinstance(equivalence, dict) else "")),
                    "goal_audit": _stage_entry("goal_audit", goal_audit_status, "fl_rtl_goal_audit disk-truth verifier", _first_source(goal_audit.get("source", "") if isinstance(goal_audit, dict) else "")),
                    "rtl": _stage_entry("rtl", rtl_status, "SSOT filelist + DUT compile/lint", _first_source(rtl.get("blocker_source", "") if isinstance(rtl, dict) else "", rtl.get("filelist", "") if isinstance(rtl, dict) else "")),
                    "lint": _stage_entry("lint", lint_status, "DUT-only lint report", _first_source(lint.get("source", "") if isinstance(lint, dict) else "")),
                    "tb": _stage_entry("tb", tb_status, "SSOT scenario implementation checker", "tb/cocotb"),
                    "sim_debug": _stage_entry("sim_debug", sim_status, "fresh cocotb results.xml + scenario pass map", _first_source(results.get("sources", []) if isinstance(results, dict) else [])),
                    "coverage": _stage_entry("coverage", cov_status, "planned functional coverage closure", "cov/coverage.json"),
                    "signoff": _stage_entry("signoff", signoff, "strict SSOT progress gate", "ATLAS /api/progress"),
                }
                return {
                    "status": status,
                    "blockers": blockers,
                    "ownership": ownership,
                    "criteria": {
                        "req": "requirements captured before SSOT",
                        "ssot": "all canonical SSOT sections approved",
                        "fl_model": "executable FL model exists and self-check passes",
                        "fl_decomp": "FL model decomposition exists and drives RTL/TB planning",
                        "fcov_plan": "functional coverage plan exists before RTL signoff",
                        "equivalence_goals": "equivalence goals exist, scoreboard events cover them, and FL-vs-RTL compare passes",
                        "goal_audit": "single audit artifact proves all required REQ->SSOT->FL->RTL->TB->sim->coverage evidence",
                        "rtl": "all expected RTL files approved and compile/lint pass",
                        "tb": "all SSOT DV scenarios have implemented tests",
                        "sim_debug": "latest result XML has tests and zero failures/errors",
                        "coverage": "coverage report is pass with no limitations",
                        "signoff": "SSOT, FL/equivalence, RTL/lint, TB, sim, and coverage all pass",
                    },
                    "detail": detail,
                    "source": "strict-ssot-progress-gate",
                }

            def _build_module(leaf_ssot_path):
                """Read a leaf <ip>/yaml/<ip>.ssot.yaml → architect module dict."""
                p = leaf_ssot_path
                ip_dir = p.parent
                if ip_dir.name == "yaml":
                    ip_dir = ip_dir.parent
                ip_name = ip_dir.name
                top = ip_name
                params, interfaces = [], []
                clocks_n, resets_n = 0, 0
                addr = ""
                doc: dict[str, Any] = {}

                def _top_name(v):
                    if isinstance(v, str) and v.strip():
                        return v.strip()
                    if isinstance(v, dict):
                        for key in ("name", "module", "top", "id"):
                            val = v.get(key)
                            if isinstance(val, str) and val.strip():
                                return val.strip()
                    return ip_name

                def _param_value(it):
                    for key in ("value", "default", "v"):
                        if key in it:
                            return it.get(key)
                    return ""

                def _iface_proto(it):
                    return (
                        it.get("proto") or it.get("protocol") or it.get("type")
                        or it.get("busType") or it.get("bus_type") or "AXI4"
                    )

                def _iface_side(role, idx):
                    role_s = str(role or "").lower()
                    if role_s == "master":
                        return "right"
                    if role_s == "slave":
                        return "left"
                    return ["right", "left", "top", "bottom"][idx % 4]

                if _yaml is not None:
                    try:
                        loaded_doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
                        if isinstance(loaded_doc, dict):
                            doc = loaded_doc
                            top = _top_name(doc.get("top_module") or top)
                            io_list = doc.get("io_list") if isinstance(doc.get("io_list"), dict) else {}
                            cl = doc.get("clocks") or io_list.get("clock_domains") or []
                            rs = doc.get("resets") or io_list.get("resets") or []
                            clocks_n, resets_n = len(cl), len(rs)
                            for k in ("parameters", "params"):
                                if isinstance(doc.get(k), list):
                                    for it in doc[k][:6]:
                                        if isinstance(it, dict):
                                            nm = it.get("name") or it.get("k")
                                            vv = _param_value(it)
                                            if nm is not None:
                                                params.append({"k": str(nm), "v": str(vv)})
                            bif = (
                                doc.get("busInterfaces")
                                or doc.get("bus_interfaces")
                                or doc.get("interfaces")
                                or io_list.get("interfaces")
                                or []
                            )
                            if isinstance(bif, list):
                                for i, it in enumerate(bif[:8]):
                                    if not isinstance(it, dict): continue
                                    role = str(it.get("role") or "slave")
                                    interfaces.append({
                                        "name": str(it.get("name") or f"if{i}"),
                                        "proto": str(_iface_proto(it)),
                                        "role":  role,
                                        "side":  str(it.get("side") or _iface_side(role, i)),
                                        "width": int(it.get("width") or 0) or None,
                                    })
                            for c in cl[:2]:
                                if isinstance(c, dict):
                                    interfaces.append({"name": c.get("name") or "clk",
                                                       "proto": "CLK", "role": "slave", "side": "left"})
                            for r in rs[:2]:
                                if isinstance(r, dict):
                                    interfaces.append({"name": r.get("name") or "rst_n",
                                                       "proto": "RST", "role": "slave", "side": "left"})
                            mm = doc.get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base is not None: addr = _hex_addr(base)
                    except Exception:
                        pass
                rtl_dir = ip_dir / "rtl"
                rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
                list_path = ip_dir / "list" / f"{ip_dir.name}.f"
                rtl_detail = ""
                if not rtl_files:
                    rtl_st = "partial" if rtl_dir.is_dir() else "pending"
                    rtl_detail = "rtl directory exists but no RTL files" if rtl_dir.is_dir() else "no rtl directory"
                elif not list_path.is_file():
                    rtl_st = "partial"
                    rtl_detail = f"RTL files exist but filelist missing: {list_path.relative_to(PROJECT_ROOT)}"
                else:
                    missing = []
                    try:
                        for raw in list_path.read_text(encoding="utf-8", errors="replace").splitlines():
                            line = raw.split("//", 1)[0].strip()
                            if not line or not line.endswith((".v", ".sv", ".vh", ".svh")):
                                continue
                            candidate = ip_dir / line
                            if not candidate.is_file():
                                candidate = PROJECT_ROOT / line
                            if not candidate.is_file():
                                missing.append(line)
                    except OSError as e:
                        missing.append(f"{list_path}: {e}")
                    if missing:
                        rtl_st = "partial"
                        rtl_detail = "filelist has missing entries: " + ", ".join(missing[:3])
                    else:
                        rtl_st = "ok"
                        rtl_detail = f"filelist OK: {list_path.relative_to(PROJECT_ROOT)}"
                sim_dir = ip_dir / "sim"
                sim_files = []
                if sim_dir.is_dir():
                    sim_files = list(sim_dir.rglob("*.log")) + list(sim_dir.rglob("*.vcd"))
                sim_history = []
                hist = sim_dir / "history.json"
                if hist.is_file():
                    try:
                        h = json.loads(hist.read_text(encoding="utf-8"))
                        if isinstance(h, dict) and isinstance(h.get("runs"), list):
                            sim_history = h["runs"][-12:]
                    except Exception:
                        pass
                tb_dir = ip_dir / "tb"
                cocotb_dir = tb_dir / "cocotb"
                tb_files = []
                if tb_dir.is_dir():
                    tb_files = (
                        list(tb_dir.rglob("*.py"))
                        + list(tb_dir.rglob("*.sv"))
                        + list(tb_dir.rglob("*.v"))
                    )
                cov_json = ip_dir / "cov" / "coverage.json"
                cov_detail = ""
                sim_debug_st = "pending"
                sim_debug_detail = "no VCD or coverage artifacts"
                if cov_json.is_file():
                    try:
                        cov_doc = json.loads(cov_json.read_text(encoding="utf-8"))
                        functional = cov_doc.get("functional") if isinstance(cov_doc, dict) else {}
                        lines = cov_doc.get("lines") if isinstance(cov_doc, dict) else {}
                        branches = cov_doc.get("branches") if isinstance(cov_doc, dict) else {}
                        fsm = cov_doc.get("fsm") if isinstance(cov_doc, dict) else {}
                        if isinstance(functional, dict) and functional.get("pct") is not None:
                            cov_detail = f", functional coverage {functional.get('pct')}%"
                        static_bits = []
                        for name, item in (("line", lines), ("branch", branches), ("fsm", fsm)):
                            if isinstance(item, dict):
                                source = item.get("source") or "unknown"
                                total = item.get("total")
                                pct = item.get("pct")
                                if str(source).startswith("static"):
                                    static_bits.append(f"{name} static {total}")
                                elif pct is not None:
                                    static_bits.append(f"{name} {pct}%")
                        if static_bits:
                            cov_detail += "; " + ", ".join(static_bits)
                    except Exception:
                        pass
                ssot_state = _load_ssot_state(ip_name)
                ssot_st = "ok"
                if ssot_state.get("approved") and not p.is_file():
                    ssot_st = "approved"
                elif ssot_state.get("status") == "planned" and not p.is_file():
                    ssot_st = "planned"
                tb_st = "ok" if tb_files else ("partial" if tb_dir.is_dir() else "pending")
                sim_debug_artifacts = []
                sim_wave_artifacts = []
                sim_result_artifacts = []
                sim_coverage_artifacts = []
                if sim_dir.is_dir():
                    sim_wave_artifacts.extend(list(sim_dir.rglob("*.vcd")))
                    sim_wave_artifacts.extend(list(sim_dir.rglob("*.fst")))
                    sim_coverage_artifacts.extend(list(sim_dir.rglob("coverage_report.*")))
                    sim_result_artifacts.extend(list(sim_dir.rglob("*results.xml")))
                cocotb_build = ip_dir / "tb" / "cocotb"
                if cocotb_build.is_dir():
                    sim_wave_artifacts.extend(list(cocotb_build.rglob("*.vcd")))
                    sim_wave_artifacts.extend(list(cocotb_build.rglob("*.fst")))
                    sim_result_artifacts.extend(list(cocotb_build.rglob("*results.xml")))
                cov_dir = ip_dir / "cov"
                if cov_dir.is_dir():
                    sim_coverage_artifacts.extend(list(cov_dir.rglob("coverage.json")))
                    sim_coverage_artifacts.extend(list(cov_dir.rglob("toggle.json")))
                sim_debug_artifacts = sim_wave_artifacts + sim_result_artifacts + sim_coverage_artifacts
                if sim_result_artifacts and (sim_wave_artifacts or sim_coverage_artifacts):
                    sim_debug_st = "ok"
                    sim_debug_detail = f"{len(sim_debug_artifacts)} debug artifact(s)"
                    if cov_detail:
                        sim_debug_detail += cov_detail
                elif sim_debug_artifacts:
                    sim_debug_st = "partial"
                    sim_debug_detail = (
                        f"{len(sim_debug_artifacts)} debug artifact(s); "
                        "needs result XML plus waveform or coverage artifact"
                    )
                req_prog = _req_progress(ip_dir)
                fl_model_prog = _fl_model_progress(ip_dir, doc)
                fl_decomp_prog = _fl_decomp_progress(ip_dir)
                fcov_plan_prog = _fcov_plan_progress(ip_dir)
                equivalence_prog = _equivalence_progress(ip_dir)
                goal_audit_prog = _goal_audit_progress(ip_dir)
                artifact_status = {
                    "req": req_prog["status"],
                    "ssot": ssot_st,
                    "fl_model": fl_model_prog["status"],
                    "fl_decomp": fl_decomp_prog["status"],
                    "fcov_plan": fcov_plan_prog["status"],
                    "equivalence_goals": equivalence_prog["status"],
                    "goal_audit": goal_audit_prog["status"],
                    "rtl": rtl_st,
                    "tb": tb_st,
                    "sim_debug": sim_debug_st,
                }
                artifact_detail = {
                    "req": f"{len(req_prog.get('files', []))} requirement artifact(s), {req_prog.get('bytes', 0)}B",
                    "ssot": (
                        f"parsed {p.relative_to(PROJECT_ROOT)}"
                        + ("; approved via .session state" if ssot_state.get("approved") else "")
                    ),
                    "fl_model": fl_model_prog.get("source") or "no executable FL model",
                    "fl_decomp": (
                        f"{fl_decomp_prog.get('units', 0)} unit(s): "
                        + ", ".join(fl_decomp_prog.get("kinds") or [])
                    ),
                    "fcov_plan": f"{fcov_plan_prog.get('bins', 0)} bin(s)",
                    "equivalence_goals": (
                        f"{equivalence_prog.get('passed', 0)}/"
                        f"{equivalence_prog.get('total', 0)} pass, "
                        f"{equivalence_prog.get('blocked', 0)} blocked, "
                        f"{equivalence_prog.get('untested', 0)} untested"
                    ),
                    "goal_audit": (
                        f"{goal_audit_prog.get('passed_checks', 0)}/"
                        f"{goal_audit_prog.get('total_checks', 0)} checks, "
                        f"{goal_audit_prog.get('failed_checks', 0)} failed"
                    ),
                    "rtl": rtl_detail,
                    "tb": (
                        f"{len(tb_files)} TB artifact(s)"
                        + (" under tb/cocotb" if cocotb_dir.is_dir() else "")
                        + cov_detail
                        if tb_files else "no tb artifacts"
                    ),
                    "sim_debug": sim_debug_detail,
                }
                progress = {
                    "req": req_prog,
                    "ssot": _ssot_progress(doc),
                    "fl_model": fl_model_prog,
                    "fl_decomp": fl_decomp_prog,
                    "fcov_plan": fcov_plan_prog,
                    "equivalence_goals": equivalence_prog,
                    "goal_audit": goal_audit_prog,
                    "rtl": _rtl_progress(ip_dir, doc),
                    "compile": _compile_progress(ip_dir),
                    "lint": _lint_progress(ip_dir, doc),
                    "sim": _sim_progress(ip_dir, doc),
                }
                gate = _strict_gate_from_progress(progress)
                artifact_status["rtl"] = gate["status"].get("rtl", rtl_st)
                artifact_detail["rtl"] = gate["detail"].get("rtl", rtl_detail)
                top_meta = doc.get("top_module") if isinstance(doc.get("top_module"), dict) else {}
                ssot_kind = str(top_meta.get("type") or "").strip()
                return {
                    "id": ip_name,
                    "name": top,
                    "label": top,
                    "kind": _kind_for(ssot_kind or ip_name),
                    "params": params,
                    "status": gate["status"],
                    "status_detail": gate["detail"],
                    "status_source": {
                        "req": gate["source"],
                        "ssot": gate["source"],
                        "fl_model": gate["source"],
                        "fl_decomp": gate["source"],
                        "fcov_plan": gate["source"],
                        "equivalence_goals": gate["source"],
                        "goal_audit": gate["source"],
                        "rtl": gate["source"],
                        "compile": gate["source"],
                        "lint": gate["source"],
                        "tb": gate["source"],
                        "sim_debug": gate["source"],
                        "coverage": gate["source"],
                        "signoff": gate["source"],
                    },
                    "artifact_status": artifact_status,
                    "artifact_detail": artifact_detail,
                    "artifact_source": {
                        "req": "filesystem-artifact",
                        "ssot": "yaml-parse",
                        "fl_model": "model/fl_model_check.json",
                        "fl_decomp": "model/decomposition.json",
                        "fcov_plan": "cov/fcov_plan.json",
                        "equivalence_goals": "verify/equivalence_goals.json",
                        "goal_audit": "sim/fl_rtl_goal_audit.json",
                        "rtl": "rtl-filelist",
                        "tb": "filesystem-artifact",
                        "sim_debug": "filesystem-artifact",
                    },
                    "interfaces": interfaces,
                    "addr": addr,
                    "rtl_files": [f.relative_to(PROJECT_ROOT).as_posix() for f in rtl_files],
                    "ssot_path": p.relative_to(PROJECT_ROOT).as_posix(),
                    "ip_dir": ip_dir.relative_to(PROJECT_ROOT).as_posix(),
                    "clocks": clocks_n,
                    "resets": resets_n,
                    "sim_history": sim_history,
                    "ssot_mtime": p.stat().st_mtime,
                    "progress": progress,
                    "signoff": gate,
                }

            def _aggregate_status(modules):
                if not modules:
                    return {
                        "req": "pending", "ssot": "pending", "fl_model": "pending",
                        "fl_decomp": "pending", "fcov_plan": "pending",
                        "equivalence_goals": "pending", "goal_audit": "pending",
                        "rtl": "pending", "lint": "unknown",
                        "tb": "pending", "sim_debug": "pending", "coverage": "unknown",
                        "signoff": "pending",
                    }
                def _all(stage: str, value: str) -> bool:
                    return all(m.get("status", {}).get(stage) == value for m in modules)
                def _any(stage: str, *values: str) -> bool:
                    return any(m.get("status", {}).get(stage) in values for m in modules)
                return {
                    "req": "ok" if _all("req", "ok") else (
                        "partial" if _any("req", "ok", "partial") else "pending"
                    ),
                    "ssot": "ok" if _all("ssot", "ok") else (
                        "partial" if _any("ssot", "ok", "partial") else "pending"
                    ),
                    "fl_model": "pass" if _all("fl_model", "pass") else (
                        "partial" if _any("fl_model", "pass", "partial") else "pending"
                    ),
                    "fl_decomp": "pass" if _all("fl_decomp", "pass") else (
                        "partial" if _any("fl_decomp", "pass", "partial") else "pending"
                    ),
                    "fcov_plan": "pass" if _all("fcov_plan", "pass") else (
                        "partial" if _any("fcov_plan", "pass", "partial") else "pending"
                    ),
                    "equivalence_goals": "fail" if _any("equivalence_goals", "fail") else (
                        "blocked" if _any("equivalence_goals", "blocked") else (
                            "pass" if _all("equivalence_goals", "pass") else (
                                "partial" if _any("equivalence_goals", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "goal_audit": "fail" if _any("goal_audit", "fail") else (
                        "blocked" if _any("goal_audit", "blocked", "stale") else (
                            "pass" if _all("goal_audit", "pass") else (
                                "partial" if _any("goal_audit", "pass", "partial") else "pending"
                            )
                        )
                    ),
                    "rtl": "fail" if _any("rtl", "fail") else (
                        "ok" if _all("rtl", "ok") else ("partial" if _any("rtl", "ok", "partial") else "pending")
                    ),
                    "lint": "fail" if _any("lint", "fail") else (
                        "pass" if _all("lint", "pass") else "unknown"
                    ),
                    "tb": "ok" if _all("tb", "ok") else (
                        "partial" if _any("tb", "ok", "partial") else "pending"
                    ),
                    "sim_debug": "fail" if _any("sim_debug", "fail") else (
                        "blocked" if _any("sim_debug", "blocked") else (
                            "ok" if _all("sim_debug", "ok") else (
                                "partial" if _any("sim_debug", "ok", "partial") else "pending"
                            )
                        )
                    ),
                    "coverage": "fail" if _any("coverage", "fail") else (
                        "blocked" if _any("coverage", "blocked") else (
                            "pass" if _all("coverage", "pass") else "unknown"
                        )
                    ),
                    "signoff": "fail" if _any("signoff", "fail") else (
                        "blocked" if _any("signoff", "blocked") else (
                            "pass" if _all("signoff", "pass") else (
                                "partial" if _any("signoff", "partial") else "pending"
                            )
                        )
                    ),
                }

            project_name = PROJECT_ROOT.name or "project"
            soc_path = PROJECT_ROOT / "soc.ssot.yaml"

            # ── Tier 1: SoC-level SSOT exists → use it as the spine ──
            if _yaml is not None and soc_path.is_file():
                try:
                    soc_doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8", errors="replace")) or {}
                except Exception as e:
                    return JSONResponse({"error": f"soc.ssot.yaml parse: {e}", "clusters": []},
                                        status_code=500)
                if not isinstance(soc_doc, dict): soc_doc = {}

                instances = soc_doc.get("instances") or []
                clusters_def = soc_doc.get("clusters") or []
                connections = soc_doc.get("connections") or []
                addr_map = soc_doc.get("addrMap") or []

                # Build module dict per instance, looking up its leaf SSOT.
                inst_to_mod = {}
                for inst in instances:
                    if not isinstance(inst, dict): continue
                    iid = inst.get("id")
                    if not iid: continue
                    leaf = inst.get("ssot")
                    leaf_path = (PROJECT_ROOT / leaf) if leaf else None
                    if leaf_path and leaf_path.is_file():
                        m = _build_module(leaf_path)
                    else:
                        # No leaf SSOT yet — minimal stub.
                        m = {
                            "id": iid, "name": iid, "label": iid,
                            "kind": _kind_for(inst.get("kind") or iid),
                            "params": [], "interfaces": [],
                            "status": {"ssot": "pending", "rtl": "pending", "sim": "pending"},
                            "rtl_files": [], "ssot_path": leaf or "",
                            "ip_dir": "", "addr": "",
                            "clocks": 0, "resets": 0, "sim_history": [], "ssot_mtime": 0,
                        }
                    # Apply instance-level overrides.
                    m["id"] = iid
                    if inst.get("name"):  m["name"] = inst["name"]; m["label"] = inst["name"]
                    if inst.get("addr") is not None: m["addr"] = _hex_addr(inst["addr"])
                    if inst.get("kind"):  m["kind"] = inst["kind"]
                    # Saved layout: `instances[].x/y` from soc.ssot.yaml
                    # (set by /api/soc/layout). Surfaces as module.savedX/Y
                    # so the frontend can use it as the default block
                    # position when localStorage doesn't override.
                    if isinstance(inst.get("x"), (int, float)): m["savedX"] = float(inst["x"])
                    if isinstance(inst.get("y"), (int, float)): m["savedY"] = float(inst["y"])
                    # Separate full-SoC canvas placement. Cluster/module
                    # views use x/y in a different coordinate system.
                    if isinstance(inst.get("top_x"), (int, float)): m["savedTopX"] = float(inst["top_x"])
                    if isinstance(inst.get("top_y"), (int, float)): m["savedTopY"] = float(inst["top_y"])
                    if isinstance(inst.get("overrides"), dict):
                        # Surface overrides as extra params.
                        for k, v in inst["overrides"].items():
                            m["params"].append({"k": str(k), "v": str(v)})
                    inst_to_mod[iid] = m

                # Group modules by cluster membership. Anything not in a
                # cluster falls into a synthetic "uncategorized" cluster.
                # While we're walking, propagate `cluster.role` → each
                # member's `kind` (CPU/BUS/MEM/PERIPH/ANALOG). The role
                # is the architect's explicit declaration and beats the
                # name heuristic (e.g. cortexa15_0 has no "cpu" in its
                # name; without role propagation it would fall through
                # to "periph").
                claimed = set()
                clusters_out = []
                for c in clusters_def:
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name")
                    if not cid: continue
                    members = c.get("members") or []
                    role_kind = _kind_from_role(c.get("role"))
                    cmods = []
                    for mid in members:
                        if mid not in inst_to_mod: continue
                        mod = inst_to_mod[mid]
                        # Role-from-cluster wins UNLESS the instance had
                        # an explicit `kind:` override in soc.ssot.yaml
                        # (set above when applying instance overrides).
                        # We detect "explicit override" by checking the
                        # raw instance dict, not the heuristic-derived
                        # value already in mod.
                        inst_def = next((i for i in instances
                                         if isinstance(i, dict) and i.get("id") == mid), {})
                        if not inst_def.get("kind") and role_kind:
                            mod["kind"] = role_kind
                        cmods.append(mod)
                    for m in members: claimed.add(m)
                    clusters_out.append({
                        "id": cid,
                        "name": cid,
                        "label": c.get("label") or cid,
                        "x": c.get("x", 60), "y": c.get("y", 80),
                        "w": c.get("w", 1200), "h": c.get("h", 600),
                        "role": c.get("role"),
                        "status": _aggregate_status(cmods),
                        "modules": cmods,
                    })
                stray = [m for iid, m in inst_to_mod.items() if iid not in claimed]
                if stray:
                    clusters_out.append({
                        "id": "uncategorized", "name": "uncategorized",
                        "label": "Uncategorized",
                        "x": 60, "y": 80, "w": 1200, "h": 600,
                        "status": _aggregate_status(stray),
                        "modules": stray,
                    })

                # Normalize connections — frontend renderer expects
                # {from: 'inst/iface', to: 'inst/iface', proto: 'AXI4'}.
                norm_conns = []
                for cn in connections:
                    if not isinstance(cn, dict): continue
                    if cn.get("from") and cn.get("to"):
                        norm_conns.append({
                            "from": str(cn["from"]),
                            "to":   str(cn["to"]),
                            "proto": str(cn.get("proto") or "AXI4"),
                        })

                return JSONResponse({
                    "name": soc_doc.get("name") or project_name,
                    "version": str(soc_doc.get("version") or "live"),
                    "clusters": clusters_out,
                    "busses": norm_conns,
                    "connections": norm_conns,        # alias for clarity
                    "addrMap": [
                        {**e, "base": _hex_addr(e.get("base")), "range": _hex_addr(e.get("range"))}
                        for e in (addr_map if isinstance(addr_map, list) else [])
                        if isinstance(e, dict)
                    ],
                    "module_count": len(inst_to_mod),
                    "source": "soc.ssot.yaml",
                    "soc_ssot_path": soc_path.relative_to(PROJECT_ROOT).as_posix(),
                    "soc_ssot_mtime": soc_path.stat().st_mtime,
                })

            # ── Tier 2: no soc.ssot.yaml → fall back to dir-walk ──
            modules = []
            for p in PROJECT_ROOT.rglob("*.ssot.yaml"):
                if any(part in SKIP_DIRS or part.startswith(".")
                       for part in p.parts):
                    continue
                if p.name == "soc.ssot.yaml": continue  # handled above
                modules.append(_build_module(p))
            seen_ids = {m.get("id") for m in modules}
            session_root = PROJECT_ROOT / ".session"
            if session_root.is_dir():
                for state_path in session_root.rglob("ssot-gen/state.json"):
                    # Only accept owner-scoped trees:
                    #     .session/<owner>/<ip>/ssot-gen/state.json   (4 parts)
                    # Legacy bare-IP layouts written by pre-owner
                    # backends:
                    #     .session/<ip>/ssot-gen/state.json           (3 parts)
                    # used to leak ip_name = '<ip>' into the SoC view
                    # forever, even after the user wiped that owner
                    # from disk. Skip anything shorter than 4 segments.
                    try:
                        rel_parts = state_path.relative_to(session_root).parts
                    except Exception:
                        continue
                    if len(rel_parts) != 4 or rel_parts[2] != "ssot-gen":
                        continue
                    ip_name = rel_parts[1]
                    if ip_name in seen_ids or not _valid_ip_name(ip_name):
                        continue
                    try:
                        state = json.loads(state_path.read_text(encoding="utf-8"))
                        if not isinstance(state, dict):
                            state = {}
                    except Exception:
                        state = {}
                    status = (
                        "approved" if state.get("approved")
                        else "answered" if str(state.get("status") or "").lower() == "answered"
                        else "planned"
                    )
                    raw_kind = str(state.get("kind") or ip_name)
                    low_kind = raw_kind.lower()
                    if any(s in low_kind for s in (
                        "i2c", "uart", "spi", "gpio", "timer", "pwm",
                        "peripheral", "controller",
                    )):
                        module_kind = "periph"
                    else:
                        module_kind = _kind_for(raw_kind)
                    modules.append({
                        "id": ip_name,
                        "name": ip_name,
                        "label": ip_name,
                        "kind": module_kind,
                        "params": [],
                        "status": {
                            "ssot": status,
                            "rtl": "pending",
                            "tb": "pending",
                            "sim": "pending",
                        },
                        "status_detail": {
                            "ssot": (
                                f"{status}; waiting for /to-ssot {ip_name}"
                                if status == "approved"
                                else f"answered; waiting for approve {ip_name}"
                                if status == "answered"
                                else f"planned; answer Web Q&A, then approve {ip_name}"
                            ),
                            "rtl": "blocked until SSOT ok",
                            "tb": "blocked until RTL/TB generation",
                            "sim": "blocked until TB/SIM generation",
                        },
                        "status_source": {
                            "ssot": ".session-state",
                            "rtl": "filesystem-artifact",
                            "tb": "filesystem-artifact",
                            "sim": "filesystem-artifact",
                        },
                        "interfaces": [],
                        "addr": "",
                        "rtl_files": [],
                        "ssot_path": f"{ip_name}/yaml/{ip_name}.ssot.yaml",
                        "ip_dir": ip_name,
                        "clocks": 0,
                        "resets": 0,
                        "sim_history": [],
                        "ssot_mtime": state_path.stat().st_mtime,
                    })
            modules.sort(key=lambda m: m["id"])
            cluster = {
                "id": "ips", "name": "ips", "label": "Project IPs",
                "x": 60, "y": 80, "w": 1200, "h": 600,
                "status": _aggregate_status(modules),
                "modules": modules,
            }
            return JSONResponse({
                "name": project_name,
                "version": "live",
                "clusters": [cluster] if modules else [],
                "busses": [],
                "addrMap": [],
                "module_count": len(modules),
                "source": "dir-walk",
            })
        except Exception as e:
            return JSONResponse({"error": str(e), "clusters": []}, status_code=500)

    @app.get("/api/progress")
    async def api_progress(scope: str = "", ip: str = ""):
        """Return SSOT-derived implementation progress for the Atlas sidebar.

        The heavy lifting already lives in /api/soc because the architect
        canvas needs the same SSOT/RTL/TB/sim evidence. This endpoint flattens
        that structure into a compact shape for the normal chat workspace:
        one selected module plus the full module list. All metrics are derived
        from the canonical leaf SSOT YAML and disk artifacts, not from fixed IP
        templates or assistant prose.
        """
        resp = await api_soc()
        try:
            data = json.loads(resp.body.decode("utf-8"))
        except Exception as e:
            return JSONResponse({"error": f"soc progress parse: {e}", "modules": []}, status_code=500)

        modules: list[dict[str, Any]] = []
        for cluster in data.get("clusters", []) if isinstance(data, dict) else []:
            if not isinstance(cluster, dict):
                continue
            for mod in cluster.get("modules", []) or []:
                if not isinstance(mod, dict):
                    continue
                entry = {
                    "id": mod.get("id") or mod.get("name") or "",
                    "name": mod.get("name") or mod.get("id") or "",
                    "label": mod.get("label") or mod.get("name") or mod.get("id") or "",
                    "kind": mod.get("kind") or "",
                    "ip_dir": mod.get("ip_dir") or "",
                    "ssot_path": mod.get("ssot_path") or "",
                    "status": mod.get("status") or {},
                    "status_detail": mod.get("status_detail") or {},
                    "status_source": mod.get("status_source") or {},
                    "artifact_status": mod.get("artifact_status") or {},
                    "artifact_detail": mod.get("artifact_detail") or {},
                    "artifact_source": mod.get("artifact_source") or {},
                    "progress": mod.get("progress") or {},
                    "signoff": mod.get("signoff") or {},
                }
                modules.append(entry)

        want = (ip or scope or "").strip().strip("/")
        selected = None
        if want:
            selected = next((
                m for m in modules
                if want in {str(m.get("id") or ""), str(m.get("name") or ""), str(m.get("ip_dir") or "")}
            ), None)
            if selected is None:
                selected = next((
                    m for m in modules
                    if str(m.get("ip_dir") or "").startswith(want + "/")
                    or str(m.get("ssot_path") or "").startswith(want + "/")
                ), None)
        if selected is None and modules:
            selected = modules[0]

        return JSONResponse({
            "project": data.get("name") if isinstance(data, dict) else PROJECT_ROOT.name,
            "source": data.get("source") if isinstance(data, dict) else "",
            "scope": want,
            "selected": selected,
            "modules": modules,
            "module_count": len(modules),
        })

    # ── Jobs (HTTP-worker dispatch tracker) ────────────────────────
    # Atlas UI tracks jobs the user dispatched from the Architect screen
    # via the block ⚡ button. We fire-and-forget POST /run (sync=False)
    # to the matching worker, store the run_id locally, and the
    # frontend's JobTracker polls /api/jobs which in turn polls each
    # worker's /status/{run_id}. The atlas_ui process never blocks on
    # a worker; the worker carries the full main-loop ReAct work.
    _jobs_lock = threading.Lock()
    _jobs: dict[str, dict[str, Any]] = {}     # job_id (uuid) → job metadata

    _PIPELINE_STAGES = [
        {"id": "ssot", "workflow": "ssot-gen", "label": "SSOT gen"},
        {"id": "equivalence", "workflow": "fl-model-gen", "label": "Equiv goals"},
        {"id": "rtl", "workflow": "rtl-gen", "label": "RTL gen"},
        {"id": "tb", "workflow": "tb-gen", "label": "TB gen"},
        {"id": "sim", "workflow": "sim", "label": "Simulation"},
        {"id": "sim-debug", "workflow": "sim_debug", "label": "Sim debug"},
        {"id": "coverage", "workflow": "coverage", "label": "Coverage"},
        {"id": "goal-audit", "workflow": "sim_debug", "label": "Goal audit"},
    ]
    _PIPELINE_BY_ID = {s["id"]: s for s in _PIPELINE_STAGES}
    _PIPELINE_BY_WORKFLOW = {s["workflow"]: s for s in _PIPELINE_STAGES}

    _WORKFLOW_SLASHES = {
        "/wf", "/workflow",
        "/new-ip", "/ni",
        "/import", "/imp",
        "/grill-me", "/grill", "/g",
        "/to-ssot", "/ssot", "/ts",
        "/resolve-rtl-blockers", "/rrb",
        "/validate-yaml",
        "/ssot-fl-model", "/sfm",
        "/ssot-equiv-goals", "/equiv-goals", "/seg",
        "/repair-equiv", "/repair-equivalence", "/reqv",
        "/ssot-rtl", "/sr",
        "/repair-rtl", "/rrtl",
        "/lint", "/l",
        "/tb",
        "/ssot-tb", "/stb",
        "/ssot-tb-cocotb", "/stb-cocotb",
        "/ssot-tb-uvm", "/stb-uvm",
        "/ssot-tb-verilog", "/stb-verilog", "/ssot-tb-sv", "/stb-sv",
        "/sim", "/s",
        "/sim-debug", "/sd",
        "/coverage", "/cov",
        "/goal-audit", "/audit", "/ga",
        "/signoff",
    }

    _STAGE_RUNNERS = {
        "ssot-rtl": {
            "workflow": "rtl-gen",
            "template": "ssot-rtl",
            "artifact_hint": "rtl/",
        },
        "ssot-fl-model": {
            "workflow": "fl-model-gen",
            "template": "ssot-fl-model",
            "artifact_hint": "model/ and cov/fcov_plan.json",
        },
        "ssot-equiv-goals": {
            "workflow": "fl-model-gen",
            "template": "ssot-equiv-goals",
            "artifact_hint": "verify/equivalence_goals.json",
        },
        "lint": {
            "workflow": "lint",
            "template": "lint-fix",
            "artifact_hint": "lint/dut_lint.json",
        },
        "ssot-tb": {
            "workflow": "tb-gen",
            "template": "ssot-tb-cocotb",
            "artifact_hint": "tb/cocotb/ and sim/",
        },
        "ssot-tb-cocotb": {
            "workflow": "tb-gen",
            "template": "ssot-tb-cocotb",
            "artifact_hint": "tb/cocotb/ and sim/",
        },
        "ssot-tb-uvm": {
            "workflow": "tb-gen",
            "template": "ssot-tb-uvm",
            "artifact_hint": "tb/uvm/ and sim/",
        },
        "ssot-tb-verilog": {
            "workflow": "tb-gen",
            "template": "ssot-tb-verilog",
            "artifact_hint": "tb/tb_*.sv and sim/",
        },
        "sim": {
            "workflow": "sim",
            "template": "sim-debug",
            "artifact_hint": "sim/results.xml, sim/scoreboard_events.jsonl, and waveform/coverage artifacts",
        },
        "sim-debug": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "sim/fl_rtl_compare.json and sim/mismatch_classification.json",
        },
        "coverage": {
            "workflow": "coverage",
            "template": "coverage_iter",
            "artifact_hint": "cov/coverage.json and sim/coverage_report.md",
        },
        "goal-audit": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "sim/fl_rtl_goal_audit.json",
        },
        "signoff": {
            "workflow": "sim_debug",
            "template": "sim-debug",
            "artifact_hint": "ATLAS /api/progress signoff gate",
        },
    }

    _SSOT_REQUIRED_DECISIONS = [
        ("purpose", "IP purpose / one sentence behavior"),
        ("bus_interface", "bus interface and role, e.g. APB4 slave"),
        ("register_map", "register map, address offsets, access policies"),
        ("clock_reset", "clock/reset names, frequency, reset polarity"),
        ("interrupt", "interrupt behavior, or explicit none"),
        ("memory_map", "memory map/base address requirement, or explicit none"),
        ("parameters", "parameters and defaults, or explicit none"),
        ("submodule_structure", "leaf submodule hierarchy and ownership"),
        ("test_expectation", "minimum cocotb/pyuvm TB/SIM acceptance expectations"),
    ]

    _SSOT_IMPORT_SECTION_TODO_SPECS = [
        ("top_module", "00 Top Module Identity", ("purpose", "submodule_structure")),
        ("sub_modules", "01 Sub-Module List", ("submodule_structure", "purpose")),
        ("parameters", "02 Parameters", ("parameters", "clock_reset", "memory_map")),
        ("io_list", "03 IO List", ("bus_interface", "clock_reset", "interrupt")),
        ("features", "04 Main Features", ("purpose", "register_map", "memory_map", "interrupt")),
        ("dataflow", "05 Data Flow", ("purpose", "bus_interface", "memory_map", "submodule_structure")),
        ("function_model", "06 Function Model", ("purpose", "register_map", "memory_map", "test_expectation")),
        ("cycle_model", "07 Cycle Model", ("clock_reset", "bus_interface", "test_expectation")),
        ("clock_reset_domains", "08 Clock & Reset Domain", ("clock_reset",)),
        ("cdc_requirements", "09 CDC Requirements", ("clock_reset", "bus_interface")),
        ("rdc_requirements", "10 RDC Requirements", ("clock_reset",)),
        ("registers", "11 Registers", ("register_map", "bus_interface")),
        ("memory", "12 Memory Requirements", ("memory_map", "parameters")),
        ("interrupts", "13 Interrupt", ("interrupt", "register_map")),
        ("fsm", "14 FSM", ("submodule_structure", "purpose", "test_expectation")),
        ("timing", "15 Timing & Performance", ("clock_reset", "parameters", "test_expectation")),
        ("power", "16 Power Intent", ("clock_reset", "parameters")),
        ("security", "17 Security & Safety", ("purpose", "bus_interface", "register_map")),
        ("error_handling", "18 Error Handling", ("interrupt", "register_map", "test_expectation")),
        ("debug_observability", "19 Debug & Observability", ("test_expectation", "interrupt", "clock_reset")),
        ("integration", "20 Integration Contract", ("bus_interface", "memory_map", "submodule_structure")),
        ("dft", "21 DFT / DFD", ("test_expectation", "clock_reset")),
        ("synthesis", "22 Synthesis / Implementation Constraints", ("parameters", "clock_reset", "submodule_structure")),
        ("coding_rules", "23 Coding Rules", ("parameters", "submodule_structure")),
        ("reuse_modules", "24 Reuse Modules", ("submodule_structure", "purpose")),
        ("custom", "25 Custom Extensions", ("purpose", "parameters", "test_expectation")),
        ("dir_structure", "26 Dir Structure", ("submodule_structure", "purpose")),
        ("filelist", "27 Filelist", ("submodule_structure", "purpose")),
        ("test_requirements", "28 Test Requirements / DV Plan", ("test_expectation", "bus_interface", "register_map", "interrupt")),
        ("quality_gates", "29 Quality Gates / Pass Criteria", ("test_expectation", "clock_reset", "parameters")),
        ("traceability", "30 Traceability", ("purpose", "test_expectation", "submodule_structure")),
        ("workflow_todos", "31 Workflow TODOs / Downstream Task Contract", ("test_expectation", "submodule_structure", "purpose")),
        ("generation_flow", "32 Generation Flow", ("purpose", "test_expectation")),
    ]

    _SSOT_IMPORT_EXTENSIONS = {
        ".md", ".txt", ".rst", ".yaml", ".yml", ".json", ".sv", ".svh",
        ".v", ".vh", ".py", ".csv", ".tsv", ".xml", ".f", ".sdc",
        ".tcl", ".rpt", ".log", ".h", ".c", ".cpp",
    }
    _SSOT_IMPORT_SKIP_DIRS = {
        ".git", ".session", ".omx", "__pycache__", "node_modules",
        ".pytest_cache", ".mypy_cache", ".ruff_cache",
    }

    def _valid_ip_name(name: str) -> bool:
        return bool(re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name or ""))

    def _slash_head(text: str) -> str:
        return (text.strip().split(None, 1)[0] if text and text.strip() else "").lower()

    def _is_workflow_slash(text: str) -> bool:
        head = _slash_head(text)
        return head in _WORKFLOW_SLASHES

    def _split_slash(text: str) -> tuple[str, str]:
        raw = (text or "").strip()
        if not raw:
            return "", ""
        parts = raw.split(None, 1)
        return parts[0].lstrip("/").lower(), (parts[1] if len(parts) > 1 else "").strip()

    def _session_json_path(session: str) -> Path:
        clean = normalize_session_name(session)
        return PROJECT_ROOT / ".session" / clean / "conversation.json"

    def _append_session_message(session: str, role: str, content: str) -> None:
        session = normalize_session_name(session)
        if not session:
            return
        path = _session_json_path(session)
        try:
            path.parent.mkdir(parents=True, exist_ok=True)
            try:
                msgs = json.loads(path.read_text(encoding="utf-8")) if path.exists() else []
                if not isinstance(msgs, list):
                    msgs = []
            except Exception:
                msgs = []
            msgs.append({"role": role, "content": content})
            path.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _append_active_history(role: str, content: str) -> None:
        """Mirror direct Web workflow command output into the currently
        hydrated chat history. Without this, commands like `/new-ip` can
        emit a visible WS event and then disappear when data.jsx reloads
        `/api/conversation` for the active workspace.
        """
        try:
            try:
                import src.config as _cfg_hist  # type: ignore
            except Exception:
                try:
                    import config as _cfg_hist  # type: ignore
                except Exception:
                    _cfg_hist = None
            if _cfg_hist is None:
                return
            hpath = Path(getattr(_cfg_hist, "HISTORY_FILE", "") or "")
            if not hpath:
                return
            hpath.parent.mkdir(parents=True, exist_ok=True)
            try:
                msgs = json.loads(hpath.read_text(encoding="utf-8")) if hpath.exists() else []
                if not isinstance(msgs, list):
                    msgs = []
            except Exception:
                msgs = []
            msgs.append({"role": role, "content": content})
            hpath.write_text(json.dumps(msgs, ensure_ascii=False, indent=2), encoding="utf-8")
        except Exception:
            pass

    def _append_workflow_history(workflow: str, role: str, content: str) -> None:
        """Persist a message in the workflow-level session as well as the
        per-IP session. The actual slash dispatcher reloads `.session/<wf>`
        after `/wf <name>`, so approved Web Q&A must be visible there before
        `/to-ssot` runs.
        """
        _append_session_message(workflow, role, content)

    def _ssot_state_path(ip: str) -> Path:
        return PROJECT_ROOT / ".session" / ip / "ssot-gen" / "state.json"

    def _load_ssot_state(ip: str) -> dict[str, Any]:
        path = _ssot_state_path(ip)
        if not path.is_file():
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            return doc if isinstance(doc, dict) else {}
        except Exception:
            return {}

    def _save_ssot_state(ip: str, state: dict[str, Any]) -> None:
        path = _ssot_state_path(ip)
        path.parent.mkdir(parents=True, exist_ok=True)
        state["updated_at"] = time.time()
        path.write_text(json.dumps(state, ensure_ascii=False, indent=2), encoding="utf-8")

    _SSOT_QA_SECTIONS = {
        "purpose": ("00_overview", "0. Overview / Intent"),
        "parameters": ("01_parameters", "1. Parameters"),
        "clock_reset": ("02_clock_reset", "2. Clock / Reset"),
        "bus_interface": ("03_interface", "3. Interface"),
        "submodule_structure": ("04_architecture", "4. Architecture / Decomposition"),
        "memory_map": ("05_memory", "5. Memory / Buffering"),
        "register_map": ("06_registers", "6. Register Map"),
        "interrupt": ("07_interrupt_error", "7. Interrupt / Error Policy"),
        "test_expectation": ("18_verification", "18. Verification / Gates"),
    }

    def _ssot_session_dir(ip: str, session: str | None = None) -> Path:
        clean = normalize_session_name(str(session or os.environ.get("ATLAS_ACTIVE_SESSION") or ""))
        parts = [p for p in clean.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and parts[-2] == ip:
            return PROJECT_ROOT / ".session" / clean
        return PROJECT_ROOT / ".session" / ip / "ssot-gen"

    def _legacy_ssot_session_dir(ip: str) -> Path:
        return PROJECT_ROOT / ".session" / ip / "ssot-gen"

    def _ssot_qa_path(ip: str, session: str | None = None) -> Path:
        return _ssot_session_dir(ip, session) / "qa.json"

    def _ssot_qa_section(decision_key: str) -> tuple[str, str]:
        return _SSOT_QA_SECTIONS.get(
            decision_key,
            ("99_other", "99. Other / Open Decisions"),
        )

    def _load_ssot_qa_items(ip: str, session: str | None = None) -> list[dict[str, Any]]:
        path = _ssot_qa_path(ip, session)
        if not path.is_file() and session:
            path = _legacy_ssot_session_dir(ip) / "qa.json"
        if not path.is_file():
            return []
        try:
            raw = json.loads(path.read_text(encoding="utf-8"))
        except Exception:
            return []
        items = raw.get("items") if isinstance(raw, dict) else raw
        if not isinstance(items, list):
            return []
        return [dict(x) for x in items if isinstance(x, dict)]

    def _save_ssot_qa_items(ip: str, items: list[dict[str, Any]], session: str | None = None) -> None:
        path = _ssot_qa_path(ip, session)
        path.parent.mkdir(parents=True, exist_ok=True)
        doc = {
            "ip": ip,
            "workflow": "ssot-gen",
            "updated_at": time.time(),
            "items": items,
        }
        path.write_text(json.dumps(doc, ensure_ascii=False, indent=2), encoding="utf-8")

    def _status_group(status: str) -> str:
        return "approved" if str(status or "").lower() in {"approved", "answered", "resolved"} else "pending"

    def _qa_slug(value: str, fallback: str) -> str:
        slug = re.sub(r"[^a-z0-9_]+", "_", str(value or "").strip().lower())
        slug = re.sub(r"_+", "_", slug).strip("_")
        return (slug[:72] or fallback)

    def _ssot_q_pairs_from_questions(questions: list[dict[str, Any]] | None) -> list[tuple[str, str, dict[str, Any]]]:
        pairs: list[tuple[str, str, dict[str, Any]]] = []
        for idx, raw in enumerate(questions or []):
            if not isinstance(raw, dict):
                continue
            question = dict(raw)
            key_src = (
                question.get("decision_key")
                or question.get("id")
                or question.get("field_path")
                or question.get("section_id")
                or question.get("question")
            )
            key = _qa_slug(str(key_src or ""), f"qa_{idx + 1}")
            label = str(
                question.get("decision_label")
                or question.get("field_path")
                or question.get("subtitle")
                or question.get("question")
                or key
            ).strip()
            pairs.append((key, label[:240] or key, question))
        return pairs

    def _active_ssot_qa_context() -> tuple[str, str]:
        session = normalize_session_name(str(os.environ.get("ATLAS_ACTIVE_SESSION") or ""))
        parts = [p for p in session.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and _valid_ip_name(parts[-2]):
            return parts[-2], session
        ip = str(os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
        if _valid_ip_name(ip):
            return ip, f"{ip}/ssot-gen"
        return "", ""

    def _upsert_ssot_qa_items(
        ip: str,
        *,
        flow_id: str,
        kind: str,
        q_pairs: list[tuple[str, str, dict[str, Any]]],
        status: str,
        answers: dict[str, dict[str, Any]] | None = None,
        session: str | None = None,
        source: str = "ssot-qna",
    ) -> None:
        items = _load_ssot_qa_items(ip, session)
        index = {
            (str(item.get("flow_id") or ""), str(item.get("decision_key") or "")): idx
            for idx, item in enumerate(items)
        }
        now = time.time()
        answers = answers or {}
        for order, (key, label, question) in enumerate(q_pairs):
            default_section_id, default_section_title = _ssot_qa_section(key)
            section_id = str(
                question.get("section_id")
                or question.get("section")
                or default_section_id
            ).strip()
            section_title = str(
                question.get("section_title")
                or question.get("section_name")
                or question.get("section")
                or default_section_title
            ).strip()
            answer = answers.get(key) if isinstance(answers.get(key), dict) else {}
            answer_text = str(answer.get("answer") or "").strip()
            existing_idx = index.get((flow_id, key))
            prior = items[existing_idx] if existing_idx is not None else {}
            prior_answer_text = str(prior.get("answer") or "").strip()
            item_status = "approved" if answer_text or prior_answer_text else status
            item = {
                **prior,
                "ip": ip,
                "workflow": "ssot-gen",
                "kind": kind or "simple APB peripheral",
                "flow_id": flow_id,
                "source": source or "ssot-qna",
                "section_id": section_id,
                "section_title": section_title,
                "decision_key": key,
                "decision_label": label,
                "question": str(question.get("question") or ""),
                "subtitle": str(question.get("subtitle") or ""),
                "question_kind": str(question.get("kind") or "single"),
                "options": question.get("options") or [],
                "qa_type": str(question.get("qa_type") or question.get("type") or "human_decision"),
                "content": question.get("content") or "",
                "detail": question.get("detail") or "",
                "criteria": question.get("criteria") or [],
                "source_refs": question.get("source_refs") or question.get("sources") or [],
                "field_path": question.get("field_path") or "",
                "order": order,
                "status": item_status,
                "status_group": _status_group(item_status),
                "answer": answer_text or str(prior.get("answer") or ""),
                "selected": answer.get("selected") or prior.get("selected") or [],
                "custom": answer.get("custom") or prior.get("custom") or "",
                "updated_at": now,
                "created_at": prior.get("created_at") or now,
            }
            if existing_idx is None:
                items.append(item)
            else:
                items[existing_idx] = item
        _save_ssot_qa_items(ip, items, session)

    def _ssot_qa_view(ip: str, session: str | None = None) -> dict[str, Any]:
        state = _load_ssot_state(ip)
        decisions = _ssot_decisions(ip, state)
        items = _load_ssot_qa_items(ip, session)
        required_index = {key: idx for idx, (key, _label) in enumerate(_SSOT_REQUIRED_DECISIONS)}
        seen_keys = {str(item.get("decision_key") or "") for item in items}
        for key, label in _SSOT_REQUIRED_DECISIONS:
            if key in seen_keys:
                continue
            answer = str(decisions.get(key) or "").strip()
            if not answer:
                continue
            section_id, section_title = _ssot_qa_section(key)
            items.append({
                "ip": ip,
                "workflow": "ssot-gen",
                "kind": state.get("kind") or "simple APB peripheral",
                "flow_id": f"decision:{key}",
                "source": "ssot-decision",
                "section_id": section_id,
                "section_title": section_title,
                "decision_key": key,
                "decision_label": label,
                "question": label,
                "subtitle": key,
                "question_kind": "derived",
                "options": [],
                "order": required_index.get(key, 999),
                "status": "approved",
                "status_group": "approved",
                "answer": answer,
                "selected": [],
                "custom": "",
                "created_at": state.get("created_at") or 0,
                "updated_at": state.get("updated_at") or 0,
            })
        for item in items:
            key = str(item.get("decision_key") or "")
            answer = str(item.get("answer") or decisions.get(key) or "").strip()
            status = "approved" if answer else _status_group(str(item.get("status") or "pending"))
            item["answer"] = answer
            item["status_group"] = "approved" if status == "approved" else "pending"
            if item["status_group"] == "approved":
                item["status"] = "approved"
        items.sort(key=lambda item: (
            str(item.get("section_id") or ""),
            required_index.get(str(item.get("decision_key") or ""), 999),
            float(item.get("created_at") or 0),
        ))
        groups: dict[str, dict[str, Any]] = {}
        for item in items:
            section_id = str(item.get("section_id") or "99_other")
            section = groups.setdefault(section_id, {
                "id": section_id,
                "title": str(item.get("section_title") or "99. Other / Open Decisions"),
                "approved": [],
                "pending": [],
                "items": [],
            })
            copied = dict(item)
            section["items"].append(copied)
            bucket = "approved" if copied.get("status_group") == "approved" else "pending"
            section[bucket].append(copied)
        sections = list(groups.values())
        toc = [
            {
                "id": section["id"],
                "title": section["title"],
                "approved": len(section["approved"]),
                "pending": len(section["pending"]),
                "total": len(section["items"]),
            }
            for section in sections
        ]
        approved = sum(1 for item in items if item.get("status_group") == "approved")
        pending = sum(1 for item in items if item.get("status_group") != "approved")
        return {
            "ip": ip,
            "workflow": "ssot-gen",
            "session": normalize_session_name(str(session or os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen")),
            "approved": bool(state.get("approved")),
            "state_status": state.get("status") or "",
            "toc": toc,
            "sections": sections,
            "summary": {"total": approved + pending, "approved": approved, "pending": pending},
            "items": items,
            "path": str(_ssot_qa_path(ip, session).relative_to(PROJECT_ROOT)),
        }

    def _ssot_qa_sessions_view() -> dict[str, Any]:
        root = PROJECT_ROOT / ".session"
        sessions: list[dict[str, Any]] = []
        if not root.is_dir():
            return {"sessions": sessions, "count": 0}
        seen: set[str] = set()
        for sdir in root.rglob("ssot-gen"):
            if not sdir.is_dir():
                continue
            try:
                rel = sdir.relative_to(root)
            except Exception:
                continue
            parts = [p for p in rel.parts if p]
            if len(parts) < 2 or parts[-1] != "ssot-gen":
                continue
            ip = parts[-2]
            if not _valid_ip_name(ip):
                continue
            session = str(rel)
            if session in seen:
                continue
            seen.add(session)
            files = [sdir / name for name in ("state.json", "qa.json", "conversation.json")]
            if not any(p.is_file() for p in files):
                continue
            mtimes = []
            for p in files:
                try:
                    if p.is_file():
                        mtimes.append(p.stat().st_mtime)
                except Exception:
                    pass
            state = {}
            state_path = sdir / "state.json"
            if state_path.is_file():
                try:
                    loaded = json.loads(state_path.read_text(encoding="utf-8"))
                    state = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    state = {}
            if not state:
                state = _load_ssot_state(ip)
            view = _ssot_qa_view(ip, session=session)
            summary = view.get("summary") if isinstance(view.get("summary"), dict) else {}
            sessions.append({
                "session": session,
                "owner": "/".join(parts[:-2]),
                "ip": ip,
                "workflow": "ssot-gen",
                "status": state.get("status") or view.get("state_status") or "draft",
                "approved": bool(state.get("approved") or view.get("approved")),
                "summary": {
                    "total": int(summary.get("total") or 0),
                    "approved": int(summary.get("approved") or 0),
                    "pending": int(summary.get("pending") or 0),
                },
                "updated_at": max(mtimes) if mtimes else float(state.get("updated_at") or 0),
                "qa_path": view.get("path") or "",
            })
        sessions.sort(key=lambda row: float(row.get("updated_at") or 0), reverse=True)
        return {"sessions": sessions, "count": len(sessions)}

    def _ssot_yaml_path(ip: str) -> Path:
        return PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"

    def _load_ssot_draft(ip: str) -> dict[str, Any]:
        path = _ssot_yaml_path(ip)
        if not path.is_file():
            return {}
        try:
            import yaml as _yaml  # type: ignore

            doc = _yaml.safe_load(path.read_text(encoding="utf-8", errors="replace")) or {}
            return doc if isinstance(doc, dict) else {}
        except Exception:
            return {}

    def _save_ssot_draft(ip: str, doc: dict[str, Any]) -> None:
        path = _ssot_yaml_path(ip)
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            import yaml as _yaml  # type: ignore
        except Exception as exc:
            raise RuntimeError(f"PyYAML is required to update SSOT draft: {exc}") from exc
        path.write_text(_yaml.safe_dump(doc, sort_keys=False, allow_unicode=True, width=120), encoding="utf-8")

    def _ensure_ssot_draft(ip: str, kind: str = "simple APB peripheral") -> dict[str, Any]:
        doc = _load_ssot_draft(ip)
        if not doc:
            doc = {
                "top_module": {
                    "name": ip,
                    "type": "draft",
                    "description": kind or "simple APB peripheral",
                    "version": "draft",
                },
                "custom": {},
            }
        top = doc.setdefault("top_module", {})
        if isinstance(top, dict):
            top.setdefault("name", ip)
            top.setdefault("type", "draft")
            top.setdefault("description", kind or "simple APB peripheral")
            top.setdefault("version", "draft")
        custom = doc.setdefault("custom", {})
        if not isinstance(custom, dict):
            custom = {}
            doc["custom"] = custom
        workflow = custom.setdefault("atlas_workflow", {})
        if isinstance(workflow, dict):
            workflow.setdefault("status", "draft")
            workflow.setdefault("source", "atlas-ui")
            workflow["updated_at"] = time.time()
        custom.setdefault("atlas_decisions", {})
        custom.setdefault("atlas_decision_sources", {})
        custom.setdefault("atlas_imports", [])
        custom.setdefault("atlas_import_conflicts", [])
        _save_ssot_draft(ip, doc)
        return doc

    def _ssot_custom(ip: str, kind: str = "simple APB peripheral") -> tuple[dict[str, Any], dict[str, Any]]:
        doc = _ensure_ssot_draft(ip, kind)
        custom = doc.setdefault("custom", {})
        if not isinstance(custom, dict):
            custom = {}
            doc["custom"] = custom
        return doc, custom

    def _ssot_decisions(ip: str, state: dict[str, Any] | None = None) -> dict[str, str]:
        doc = _load_ssot_draft(ip)
        custom = doc.get("custom") if isinstance(doc.get("custom"), dict) else {}
        raw = custom.get("atlas_decisions") if isinstance(custom, dict) else {}
        if not isinstance(raw, dict) or not raw:
            legacy = state if isinstance(state, dict) else _load_ssot_state(ip)
            raw = legacy.get("decisions") if isinstance(legacy.get("decisions"), dict) else {}
        return {str(k): str(v).strip() for k, v in (raw or {}).items() if str(v or "").strip()}

    def _missing_ssot_decisions(ip: str, state: dict[str, Any] | None = None) -> list[str]:
        decisions = _ssot_decisions(ip, state)
        return [key for key, _ in _SSOT_REQUIRED_DECISIONS if not str(decisions.get(key) or "").strip()]

    def _record_ssot_decisions(
        ip: str,
        kind: str,
        updates: dict[str, str],
        sources: dict[str, list[dict[str, str]]] | None = None,
    ) -> tuple[list[str], list[dict[str, Any]]]:
        doc, custom = _ssot_custom(ip, kind)
        decisions = custom.get("atlas_decisions")
        if not isinstance(decisions, dict):
            decisions = {}
            custom["atlas_decisions"] = decisions
        decision_sources = custom.get("atlas_decision_sources")
        if not isinstance(decision_sources, dict):
            decision_sources = {}
            custom["atlas_decision_sources"] = decision_sources
        filled: list[str] = []
        conflicts: list[dict[str, Any]] = []
        source_map = sources or {}
        for key, value in updates.items():
            candidate = str(value or "").strip()
            if not candidate:
                continue
            existing = str(decisions.get(key) or "").strip()
            if existing:
                if re.sub(r"\s+", " ", existing).lower() != re.sub(r"\s+", " ", candidate).lower():
                    conflicts.append({
                        "key": key,
                        "existing": existing[:500],
                        "candidate": candidate[:500],
                        "sources": source_map.get(key, [])[:5],
                    })
                continue
            decisions[key] = candidate
            decision_sources[key] = source_map.get(key, [])[:8]
            filled.append(key)
        if conflicts:
            prior = custom.get("atlas_import_conflicts")
            if not isinstance(prior, list):
                prior = []
            custom["atlas_import_conflicts"] = prior + conflicts
        _save_ssot_draft(ip, doc)
        return filled, conflicts

    def _latest_pending_ssot_ip() -> str:
        root = PROJECT_ROOT / ".session"
        candidates: list[tuple[float, str]] = []
        if root.is_dir():
            for p in root.rglob("ssot-gen/state.json"):
                try:
                    doc = json.loads(p.read_text(encoding="utf-8"))
                    if isinstance(doc, dict) and not doc.get("approved"):
                        candidates.append((p.stat().st_mtime, p.parent.parent.name))
                except Exception:
                    continue
        candidates.sort(reverse=True)
        return candidates[0][1] if candidates else ""

    def _set_active_ssot_ip(ip: str) -> None:
        if not _valid_ip_name(ip):
            return
        owner = ""
        current = normalize_session_name(str(os.environ.get("ATLAS_ACTIVE_SESSION") or ""))
        current_parts = [p for p in current.split("/") if p]
        if len(current_parts) >= 3:
            owner = current_parts[0]
        elif len(current_parts) >= 2 and current_parts[-1] == "default":
            owner = current_parts[0]
        os.environ["ATLAS_ACTIVE_IP"] = ip
        os.environ["ATLAS_ACTIVE_SESSION"] = f"{owner}/{ip}/ssot-gen" if owner else f"{ip}/ssot-gen"

    def _active_ssot_ip() -> str:
        env_ip = str(os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
        if _valid_ip_name(env_ip):
            return env_ip
        session = normalize_session_name(str(os.environ.get("ATLAS_ACTIVE_SESSION") or ""))
        parts = [p for p in session.split("/") if p]
        if len(parts) >= 2 and parts[-1] == "ssot-gen" and _valid_ip_name(parts[-2]):
            return parts[-2]
        if len(parts) == 1 and _valid_ip_name(parts[0]) and _ssot_state_path(parts[0]).is_file():
            return parts[0]
        return _latest_pending_ssot_ip()

    def _render_new_ip_plan(ip: str, kind: str, state: dict[str, Any]) -> str:
        missing = _missing_ssot_decisions(ip, state)
        lines = [
            f"[SSOT PLAN] {ip}",
            f"kind: {kind or 'simple APB peripheral'}",
            "mode: structure only; no document import is run by /new-ip",
            "",
            "Created structure:",
            f"- {ip}/doc, {ip}/req, {ip}/yaml",
            f"- {ip}/rtl, {ip}/list, {ip}/tb/cocotb",
            f"- {ip}/tc, {ip}/sim, {ip}/cov, {ip}/lint",
            "",
            "SSOT decisions still needed before production YAML write:",
        ]
        for key, label in _SSOT_REQUIRED_DECISIONS:
            mark = "✓" if key not in missing else "·"
            lines.append(f"- {mark} `{key}`: {label}")
        lines += [
            "",
            "Short flow:",
            f"1. Put source docs, RTL, specs, logs, or notes anywhere under `{ip}/`",
            f"2. Run `/import {ip}` or `/import @path` to scan the workspace into SSOT section TODOs",
            f"3. Run `/to-ssot {ip}`; use `/grill-me` only for gaps or conflicts",
        ]
        if missing:
            lines.append("")
            lines.append("missing decisions: " + ", ".join(missing))
        return "\n".join(lines)

    def _parse_new_ip_args(args: str) -> tuple[str, str, list[str], str]:
        import shlex

        try:
            tokens = [t.strip().strip("\"'") for t in shlex.split(args or "", posix=False) if t.strip()]
        except ValueError as exc:
            return "", "", [], f"cannot parse /new-ip arguments: {exc}"
        if not tokens:
            return "", "", [], ""
        ip = tokens[0]
        import_paths: list[str] = []
        kind_tokens: list[str] = []
        idx = 1
        while idx < len(tokens):
            tok = tokens[idx]
            if tok in ("--import", "--doc", "--docs"):
                if idx + 1 >= len(tokens):
                    return "", "", [], f"missing value after {tok}"
                import_paths.append(tokens[idx + 1])
                idx += 2
                continue
            if tok.startswith("@"):
                import_paths.append(tok)
                idx += 1
                continue
            kind_tokens.append(tok)
            idx += 1
        kind = " ".join(kind_tokens).strip() or "simple APB peripheral"
        return ip, kind, import_paths, ""

    def _render_ssot_llm_qna_prompt(ip: str, kind: str, state: dict[str, Any]) -> str:
        session = normalize_session_name(str(os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen"))
        imported = state.get("imported_artifacts") if isinstance(state.get("imported_artifacts"), list) else []
        imported_paths = [
            str(item.get("path") or "").strip()
            for item in imported
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        ]
        missing = _missing_ssot_decisions(ip, state)
        lang = os.environ.get("ATLAS_UI_LANG") or "English"
        path_lines = "\n".join(f"- {p}" for p in imported_paths[:24]) or "- (none recorded; inspect the IP directory and draft SSOT)"
        missing_line = ", ".join(missing) if missing else "(backend baseline decisions already filled; still inspect for SSOT TBD/conflicts)"
        return "\n".join([
            f"You are ssot-gen for IP `{ip}` in ATLAS UI.",
            f"Session: `{session}`",
            f"Preferred visible language: {lang}. Default to English when no explicit language is requested.",
            "",
            "Goal: create IP-specific SSOT Q&A from the current evidence, not from a fixed template.",
            "This is a general-IP flow. Do not assume APB/register-only/simple peripheral structure unless evidence says so.",
            "",
            "Truth ownership model:",
            "- Human owns requirement/spec/interface/FL golden model/coverage goals/performance targets/sign-off.",
            "- LLM owns drafting, import analysis, QA generation, SSOT patch proposals, and downstream workflow_todos.",
            "- Do not change locked truth to make downstream RTL pass; make a change-request question instead.",
            "- TODOs are execution work, not substitutes for unresolved human decisions.",
            "",
            "Current backend baseline missing keys, for orientation only:",
            f"- {missing_line}",
            "",
            "Evidence paths imported or known:",
            path_lines,
            "",
            "Required action:",
            f"1. Read `{ip}/yaml/{ip}.ssot.yaml` if it exists, plus relevant docs/RTL under `{ip}/` and the evidence paths above.",
            "2. Detect unresolved SSOT decisions, contradictions, assumptions, TBD/null/placeholders, and any truth that needs human approval.",
            "3. Generate ONLY the questions needed for this IP. The question set may be 0, 1, 4, 20, or more depending on complexity.",
            "4. If the answer is not an immediate blocker, use `record_ssot_qa(questions=[...])` to save deferred QA cards.",
            "5. Use `ask_user(questions=[...])` only when the answer blocks the next SSOT write or import pass.",
            "   Do not ask plain prose questions in chat. Both tools preserve SSOT QA metadata.",
            "6. Each question object must carry metadata so ATLAS can save it in SSOT QA preview:",
            "   - id: stable snake_case id",
            "   - section_id: canonical section bucket such as 00_overview, 03_interface, 06_registers, 18_verification, 19_workflow_todos, or a specific section number",
            "   - section_title: human-readable SSOT section title",
            "   - decision_key: stable key for the decision",
            "   - decision_label: short label",
            "   - qa_type: human_decision | clarification | change_request | execution_blocker",
            "   - question, subtitle, kind, options when useful",
            "   - criteria: pass/fail criteria for using the answer downstream",
            "   - source_refs: SSOT paths, doc paths, or RTL paths that caused the question",
            "7. Prefer section-specific QA cards. Group by SSOT section and ask concrete decisions, not generic template prompts.",
            "8. If downstream RTL needs explicit decomposition, write `workflow_todos.rtl-gen[]` with content/detail/criteria/source_refs.",
            "9. If no immediate answer is needed after recording deferred QA, say `[SSOT Q&A] deferred questions recorded` with a short evidence summary.",
            "10. If no human decision is needed at all, say `[SSOT Q&A] no generated questions required` and explain the evidence briefly.",
            "",
            "Important: fixed question templates are forbidden here. Derive the QA from this IP's evidence and current SSOT only.",
        ])

    def _render_approved_ssot_spec(ip: str, state: dict[str, Any]) -> str:
        decisions = _ssot_decisions(ip, state)
        lines = [
            f"[APPROVED WEB SSOT SPEC] {ip}",
            f"kind: {state.get('kind') or 'simple APB peripheral'}",
            "source: Web UI Plan Mode + SSOT draft decisions",
            "",
            "Use this as the source of truth for /to-ssot. Do not invent over missing fields.",
        ]
        for key, _label in _SSOT_REQUIRED_DECISIONS:
            lines.append(f"- {key}: {decisions.get(key) or '(missing)'}")
        return "\n".join(lines)

    def _emit_ssot_approval_ready(ip: str, state: dict[str, Any], missing: list[str] | None = None) -> None:
        decisions = _ssot_decisions(ip, state)
        miss = missing if missing is not None else _missing_ssot_decisions(ip, state)
        bridge.emit(
            "ssot_approval_ready",
            ip=ip,
            kind=state.get("kind") or "simple APB peripheral",
            status=state.get("status") or ("approved" if state.get("approved") else "answered"),
            approved=bool(state.get("approved")),
            missing=miss,
            decisions=decisions,
            approve_cmd=f"approve {ip}",
            generate_cmd=f"/to-ssot {ip}",
        )

    def _answer_text(answer: dict[str, Any], question: dict[str, Any]) -> str:
        custom = str(answer.get("custom") or "").strip()
        if custom:
            return custom
        selected = answer.get("selected") or []
        by_id = {str(o.get("id")): str(o.get("label") or o.get("id"))
                 for o in (question.get("options") or []) if isinstance(o, dict)}
        labels = [by_id.get(str(s), str(s)) for s in selected]
        return ", ".join([x for x in labels if x]).strip()

    def _new_ssot_state(ip: str, kind: str = "simple APB peripheral") -> dict[str, Any]:
        return {
            "ip": ip,
            "kind": kind,
            "approved": False,
            "approved_at": 0,
            "status": "planned",
            "active_session": os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen",
            "last_step": "new-ip",
            "created_at": time.time(),
        }

    def _ensure_new_ip_structure(ip: str) -> list[str]:
        dirs = [
            "doc",
            "req",
            "yaml",
            "rtl",
            "list",
            "tb/cocotb",
            "tc",
            "sim",
            "cov",
            "lint",
        ]
        created: list[str] = []
        for rel in dirs:
            path = PROJECT_ROOT / ip / rel
            path.mkdir(parents=True, exist_ok=True)
            created.append(f"{ip}/{rel}")
        return created

    def _relative_project_path(path: Path) -> str:
        try:
            return str(path.resolve().relative_to(PROJECT_ROOT.resolve()))
        except Exception:
            return str(path)

    def _strip_import_marker(raw: str) -> str:
        token = str(raw or "").strip().strip("\"'")
        return token[1:] if token.startswith("@") else token

    def _safe_import_path(raw: str) -> Path | None:
        token = _strip_import_marker(raw)
        if not token:
            return None
        if os.name != "nt":
            token = token.replace("\\", "/")
        try:
            p = Path(token).expanduser()
            if not p.is_absolute():
                p = PROJECT_ROOT / token
            resolved = p.resolve()
            resolved.relative_to(PROJECT_ROOT.resolve())
            return resolved
        except Exception:
            return None

    def _resolve_import_path(ip: str, raw: str) -> tuple[Path | None, str]:
        token = _strip_import_marker(raw)
        if not token:
            return None, "empty import path"
        candidates = [token]
        maybe_path = Path(token)
        if not maybe_path.is_absolute():
            norm = token.replace("\\", "/")
            if not norm.startswith(f"{ip}/"):
                candidates.append(f"{ip}/{token}")
        first_safe: Path | None = None
        for candidate in candidates:
            p = _safe_import_path(candidate)
            if p is None:
                continue
            if first_safe is None:
                first_safe = p
            if p.exists():
                return p, ""
        if first_safe is None:
            return None, f"unsafe import path: {token}"
        return first_safe, f"import path not found: {_relative_project_path(first_safe)}"

    def _parse_import_args(args: str) -> tuple[str, list[str], str]:
        import shlex

        try:
            raw_tokens = shlex.split(args or "", posix=False)
        except ValueError as exc:
            return "", [], f"cannot parse /import arguments: {exc}"
        tokens = []
        for raw in raw_tokens:
            tok = _strip_import_marker(raw)
            if tok:
                tokens.append(tok)
        ip = ""
        paths: list[str] = []
        idx = 0
        while idx < len(tokens):
            tok = tokens[idx]
            if tok in ("--ip", "-i"):
                if idx + 1 >= len(tokens):
                    return "", [], "missing value after --ip"
                ip = tokens[idx + 1]
                idx += 2
                continue
            paths.append(tok)
            idx += 1
        if not ip and len(paths) > 1 and _valid_ip_name(paths[0]):
            maybe_ip = paths[0]
            if _ssot_state_path(maybe_ip).is_file() or (PROJECT_ROOT / maybe_ip).exists():
                ip = maybe_ip
                paths = paths[1:]
        if not ip:
            ip = _active_ssot_ip()
        if not _valid_ip_name(ip):
            return "", [], (
                "[SSOT IMPORT] no active IP found\n"
                "usage: /new-ip <ip_name> first, then /import [path ...]\n"
                "or: /import --ip <ip_name> [path ...]"
            )
        return ip, paths, ""

    def _default_import_roots(ip: str) -> list[Path]:
        ip_dir = PROJECT_ROOT / ip
        return [ip_dir] if ip_dir.exists() else []

    def _collect_import_files(ip: str, raw_paths: list[str]) -> tuple[list[Path], list[str]]:
        roots: list[Path] = []
        errors: list[str] = []
        if raw_paths:
            for raw in raw_paths:
                p, err = _resolve_import_path(ip, raw)
                if err:
                    errors.append(err)
                if p is not None and p.exists():
                    roots.append(p)
        else:
            roots = _default_import_roots(ip)

        files: list[Path] = []
        seen: set[Path] = set()
        for root in roots:
            candidates = [root]
            if root.is_dir():
                candidates = sorted(root.rglob("*"), key=lambda p: p.as_posix())
            for p in candidates:
                try:
                    rp = p.resolve()
                    rel_parts = rp.relative_to(PROJECT_ROOT.resolve()).parts
                except Exception:
                    continue
                if any(part in _SSOT_IMPORT_SKIP_DIRS or part.startswith(".") for part in rel_parts[:-1]):
                    continue
                if not rp.is_file() or rp.suffix.lower() not in _SSOT_IMPORT_EXTENSIONS:
                    continue
                if rp in seen:
                    continue
                seen.add(rp)
                files.append(rp)
                if len(files) >= 256:
                    errors.append("import file limit reached at 256 files")
                    return files, errors
        return files, errors

    def _clean_import_line(line: str) -> str:
        line = re.sub(r"\s+", " ", str(line or "").strip())
        line = line.lstrip("#/*- ").rstrip("*/ ")
        return line[:260]

    def _snippet_lines(text: str, pattern: str, *, limit: int = 5) -> list[str]:
        out: list[str] = []
        seen: set[str] = set()
        for raw in text.splitlines():
            line = _clean_import_line(raw)
            if len(line) < 4 or line in seen:
                continue
            if re.search(pattern, line, re.IGNORECASE):
                seen.add(line)
                out.append(line)
                if len(out) >= limit:
                    break
        return out

    def _purpose_lines(ip: str, path: Path, text: str) -> list[str]:
        out: list[str] = []
        module_names = re.findall(r"\bmodule\s+([A-Za-z_][A-Za-z0-9_]*)\b", text)
        if module_names:
            out.append("RTL modules: " + ", ".join(module_names[:8]))
        for raw in text.splitlines():
            line = _clean_import_line(raw)
            if len(line) < 12:
                continue
            if re.search(r"\b(purpose|overview|summary|objective|function|module|ip)\b", line, re.IGNORECASE):
                out.append(line)
            elif ip.lower() in line.lower():
                out.append(line)
            elif path.suffix.lower() in {".md", ".txt", ".rst"} and not out:
                out.append(line)
            if len(out) >= 5:
                break
        return out

    def _extract_import_candidates(
        ip: str,
        files: list[Path],
    ) -> tuple[list[dict[str, Any]], dict[str, str], dict[str, list[dict[str, str]]]]:
        patterns = {
            "bus_interface": r"\b(APB|APB4|AXI|AXI4|AXI4[- ]?Lite|AHB|Wishbone|I2C|I3C|SMBus|SPI|UART|PCIe|VDM)\b",
            "register_map": r"\b(register|csr|offset|address|addr|0x[0-9a-f]+|CTRL|STATUS|DATA|CMD|PRESCALE|IRQ|W1C|RO|RW)\b",
            "clock_reset": r"\b(clock|clk|reset|rst|rst_n|resetn|frequency|MHz|active[- ]?(low|high))\b",
            "interrupt": r"\b(interrupt|irq|int_|level|pulse|w1c|done|error)\b",
            "memory_map": r"\b(memory map|base address|base|range|window|SRAM|RAM|FIFO|buffer|address map)\b",
            "parameters": r"\b(parameter|localparam|define|configurable|width|depth|DATA_WIDTH|ADDR_WIDTH|FIFO_DEPTH|default)\b",
            "submodule_structure": r"\b(submodule|hierarchy|block|fsm|module|parser|core|regs|fifo|engine|controller)\b",
            "test_expectation": r"\b(test|verify|verification|coverage|scenario|assert|scoreboard|cocotb|uvm|regression|acceptance)\b",
        }
        snippets: dict[str, list[str]] = {key: [] for key, _ in _SSOT_REQUIRED_DECISIONS}
        sources: dict[str, list[dict[str, str]]] = {key: [] for key, _ in _SSOT_REQUIRED_DECISIONS}
        artifacts: list[dict[str, Any]] = []

        for path in files:
            try:
                raw = path.read_text(encoding="utf-8", errors="ignore")
            except Exception as exc:
                artifacts.append({
                    "path": _relative_project_path(path),
                    "error": f"read failed: {exc}",
                    "bytes": 0,
                })
                continue
            text = raw[:262_144]
            rel = _relative_project_path(path)
            artifacts.append({
                "path": rel,
                "bytes": len(raw.encode("utf-8", errors="ignore")),
                "truncated": len(raw) > len(text),
            })
            for line in _purpose_lines(ip, path, text):
                if line not in snippets["purpose"]:
                    snippets["purpose"].append(line)
                    sources["purpose"].append({"path": rel, "excerpt": line})
            for key, pattern in patterns.items():
                for line in _snippet_lines(text, pattern):
                    if line not in snippets[key]:
                        snippets[key].append(line)
                        sources[key].append({"path": rel, "excerpt": line})

        candidates: dict[str, str] = {}
        for key, _label in _SSOT_REQUIRED_DECISIONS:
            vals = snippets.get(key) or []
            if vals:
                candidates[key] = "; ".join(vals[:8])[:1200]
        return artifacts, candidates, sources

    def _merge_unique_records(
        existing: list[Any],
        incoming: list[dict[str, Any]],
        key_fields: tuple[str, ...],
        *,
        limit: int = 128,
    ) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [dict(x) for x in existing if isinstance(x, dict)]
        index: dict[tuple[str, ...], int] = {}
        for idx, item in enumerate(out):
            key = tuple(str(item.get(field) or "") for field in key_fields)
            if any(key):
                index[key] = idx
        for item in incoming:
            key = tuple(str(item.get(field) or "") for field in key_fields)
            if any(key) and key in index:
                out[index[key]].update(item)
            else:
                if any(key):
                    index[key] = len(out)
                out.append(dict(item))
        return out[-limit:]

    def _merge_todos_by_id(existing: Any, incoming: list[dict[str, Any]]) -> list[dict[str, Any]]:
        out: list[dict[str, Any]] = [dict(x) for x in existing if isinstance(x, dict)] if isinstance(existing, list) else []
        index = {str(item.get("id") or ""): idx for idx, item in enumerate(out) if str(item.get("id") or "")}
        for item in incoming:
            tid = str(item.get("id") or "").strip()
            if not tid:
                continue
            if tid in index:
                prior = out[index[tid]]
                status = prior.get("status")
                prior.update(item)
                if status:
                    prior["status"] = status
            else:
                index[tid] = len(out)
                out.append(dict(item))
        return out

    def _import_evidence_rows(
        artifacts: list[dict[str, Any]],
        sources: dict[str, list[dict[str, str]]],
    ) -> list[dict[str, Any]]:
        paths = [
            str(item.get("path") or "").strip()
            for item in artifacts
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        ]
        by_path: dict[str, list[dict[str, str]]] = {path: [] for path in paths}
        for key, entries in sources.items():
            for entry in entries or []:
                if not isinstance(entry, dict):
                    continue
                path = str(entry.get("path") or "").strip()
                excerpt = str(entry.get("excerpt") or "").strip()
                if not path or not excerpt:
                    continue
                by_path.setdefault(path, []).append({"decision_key": key, "excerpt": excerpt[:500]})
        rows: list[dict[str, Any]] = []
        for artifact in artifacts:
            if not isinstance(artifact, dict):
                continue
            path = str(artifact.get("path") or "").strip()
            if not path:
                continue
            rows.append({
                "path": path,
                "bytes": int(artifact.get("bytes") or 0),
                "truncated": bool(artifact.get("truncated")),
                "excerpts": by_path.get(path, [])[:24],
            })
        return rows

    def _import_section_todos(
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> list[dict[str, Any]]:
        todos: list[dict[str, Any]] = []
        all_refs = sorted({
            str(item.get("path") or "").strip()
            for entries in sources.values()
            for item in (entries or [])
            if isinstance(item, dict) and str(item.get("path") or "").strip()
        })
        for section, title, keys in _SSOT_IMPORT_SECTION_TODO_SPECS:
            evidence_keys = [key for key in keys if str(candidates.get(key) or "").strip()]
            refs = sorted({
                str(item.get("path") or "").strip()
                for key in keys
                for item in sources.get(key, [])
                if isinstance(item, dict) and str(item.get("path") or "").strip()
            })
            evidence_note = ", ".join(evidence_keys) if evidence_keys else "no direct heuristic hit"
            todos.append({
                "id": f"IMPORT_SSOT_SECTION_{section.upper()}",
                "content": f"Review imported workspace evidence for SSOT `{section}`",
                "detail": (
                    f"Section {title}: inspect the imported workspace inventory and promote only "
                    f"source-backed facts into `{section}`. Current heuristic evidence keys: {evidence_note}. "
                    "If the workspace lacks this information, leave a precise SSOT QA/TBD item instead of "
                    "inventing fixed-template content."
                ),
                "criteria": [
                    f"`{section}` contains only source-backed values or explicit TBD/none markers",
                    "Every promoted field has a source_ref back to imported workspace evidence",
                    "Contradictions are listed under custom.atlas_import_conflicts or SSOT QA",
                    "No fixed-template behavior is added without evidence",
                ],
                "source_refs": refs or all_refs[:24] or ["custom.atlas_workspace_inventory"],
                "section": section,
                "decision_keys": list(keys),
                "evidence_keys": evidence_keys,
                "priority": "high" if evidence_keys else "normal",
                "required": True,
            })
        return todos

    def _import_downstream_todos(ip: str, source_refs: list[str], has_dv: bool) -> dict[str, list[dict[str, Any]]]:
        refs = source_refs[:24] or ["custom.atlas_import_doc_evidence"]
        todos: dict[str, list[dict[str, Any]]] = {
            "rtl-gen": [
                {
                    "id": "IMPORT_RTL_FROM_DOC_EVIDENCE",
                    "content": "Implement RTL only from imported doc-backed SSOT facts",
                    "detail": (
                        "Use custom.atlas_import_doc_evidence, custom.atlas_decisions, and the canonical "
                        "SSOT sections derived from them. If a required RTL behavior is only implied or "
                        "contradictory in the docs, emit an SSOT question instead of filling a template."
                    ),
                    "criteria": [
                        "RTL TODO plan references imported source_refs for doc-derived behavior",
                        "No RTL behavior is implemented from a fixed template when the import lacks evidence",
                        "DUT compile/lint evidence is fresh after doc-derived RTL edits",
                    ],
                    "source_refs": refs,
                    "owner_module": f"{ip}_core",
                    "owner_file": f"rtl/{ip}.sv",
                    "priority": "high",
                    "required": True,
                }
            ],
            "tb-gen": [
                {
                    "id": "IMPORT_TB_FROM_DOC_EVIDENCE",
                    "content": "Generate cocotb/pyuvm tests from imported verification evidence",
                    "detail": (
                        "Convert imported scenarios, acceptance criteria, protocol timing, and coverage notes "
                        "into SSOT test_requirements and executable cocotb/pyuvm tests. Use Python/pyuvm by default; "
                        "do not create SV tc/tb files unless the SSOT explicitly requests that backend."
                    ),
                    "criteria": [
                        "Every imported scenario has a cocotb/pyuvm test or a precise blocker",
                        "Scoreboard expectations trace to function_model or imported source_refs",
                        "Simulation emits results.xml, scoreboard_events.jsonl, VCD, and coverage evidence",
                    ],
                    "source_refs": refs,
                    "priority": "high" if has_dv else "normal",
                    "required": True,
                }
            ],
            "sim_debug": [
                {
                    "id": "IMPORT_SIM_DEBUG_EVIDENCE_MAP",
                    "content": "Use imported doc evidence to classify simulation failures",
                    "detail": (
                        "When cocotb/pyuvm results or waveforms disagree with expected behavior, classify the "
                        "mismatch against imported source_refs, SSOT function/cycle model, RTL, or TB ownership."
                    ),
                    "criteria": [
                        "Every failure report cites expected/got evidence and an imported or SSOT source_ref",
                        "Waveform/VCD checks cover imported timing, reset, interrupt, and protocol expectations when present",
                        "Escalations name the owning workflow: ssot-gen, rtl-gen, tb-gen, or coverage",
                    ],
                    "source_refs": refs,
                    "priority": "normal",
                    "required": True,
                }
            ],
        }
        return todos

    def _apply_import_yaml_todos(
        ip: str,
        doc: dict[str, Any],
        custom: dict[str, Any],
        artifacts: list[dict[str, Any]],
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> dict[str, Any]:
        evidence_rows = _import_evidence_rows(artifacts, sources)
        source_refs = [
            str(row.get("path") or "").strip()
            for row in evidence_rows
            if str(row.get("path") or "").strip()
        ]
        section_todos = _import_section_todos(candidates, sources)
        downstream = _import_downstream_todos(ip, source_refs, bool(candidates.get("test_expectation")))

        custom["atlas_import_doc_evidence"] = _merge_unique_records(
            custom.get("atlas_import_doc_evidence") if isinstance(custom.get("atlas_import_doc_evidence"), list) else [],
            evidence_rows,
            ("path",),
            limit=256,
        )
        custom["atlas_workspace_inventory"] = _merge_unique_records(
            custom.get("atlas_workspace_inventory") if isinstance(custom.get("atlas_workspace_inventory"), list) else [],
            evidence_rows,
            ("path",),
            limit=256,
        )
        prior_draft = custom.get("atlas_import_todo_draft") if isinstance(custom.get("atlas_import_todo_draft"), dict) else {}
        merged_section_todos = _merge_todos_by_id(
            prior_draft.get("section_todos") if isinstance(prior_draft, dict) else [],
            section_todos,
        )
        custom["atlas_import_section_todos"] = merged_section_todos
        custom["atlas_import_todo_draft"] = {
            "updated_at": time.time(),
            "source_refs": source_refs[:64],
            "section_todos": merged_section_todos,
            "downstream_todos": {
                stage: _merge_todos_by_id(
                    (prior_draft.get("downstream_todos") or {}).get(stage) if isinstance(prior_draft.get("downstream_todos"), dict) else [],
                    items,
                )
                for stage, items in downstream.items()
            },
        }

        workflow_todos = doc.get("workflow_todos")
        if not isinstance(workflow_todos, dict):
            workflow_todos = {}
            doc["workflow_todos"] = workflow_todos
        workflow_todos["ssot-gen"] = _merge_todos_by_id(workflow_todos.get("ssot-gen"), section_todos)
        for stage, items in downstream.items():
            workflow_todos[stage] = _merge_todos_by_id(workflow_todos.get(stage), items)

        return {
            "evidence_rows": len(evidence_rows),
            "section_todos": len(section_todos),
            "downstream_todos": {stage: len(items) for stage, items in downstream.items()},
        }

    def _merge_import_candidates(
        ip: str,
        kind: str,
        state: dict[str, Any],
        artifacts: list[dict[str, Any]],
        candidates: dict[str, str],
        sources: dict[str, list[dict[str, str]]],
    ) -> tuple[list[str], list[dict[str, Any]]]:
        filled, conflicts = _record_ssot_decisions(ip, kind, candidates, sources)
        doc, custom = _ssot_custom(ip, kind)
        todo_summary = _apply_import_yaml_todos(ip, doc, custom, artifacts, candidates, sources)
        imports = custom.get("atlas_imports")
        if not isinstance(imports, list):
            imports = []
        imports.append({
            "imported_at": time.time(),
            "artifacts": artifacts,
            "filled": filled,
            "conflicts": conflicts,
            "yaml_todos": todo_summary,
        })
        custom["atlas_imports"] = imports
        _save_ssot_draft(ip, doc)
        imported_artifacts = state.get("imported_artifacts")
        if not isinstance(imported_artifacts, list):
            imported_artifacts = []
        imported_artifacts.extend({
            "path": str(a.get("path") or ""),
            "imported_at": time.time(),
        } for a in artifacts if a.get("path"))
        state["imported_artifacts"] = imported_artifacts[-64:]
        state["last_import_yaml_todos"] = todo_summary
        state["last_step"] = "import"
        if conflicts:
            state["last_issue"] = "import_conflicts"
        if filled or conflicts:
            state["approved"] = False
            state["approved_at"] = 0
        state["status"] = "answered" if not _missing_ssot_decisions(ip, state) else "planned"
        return filled, conflicts

    def _import_defaults_if_available(ip: str, kind: str, state: dict[str, Any]) -> tuple[list[str], list[dict[str, Any]], list[dict[str, Any]], list[str]]:
        """Import the current IP workspace into the SSOT draft when requested."""
        files, errors = _collect_import_files(ip, [])
        if not files:
            return [], [], [], errors
        artifacts, candidates, sources = _extract_import_candidates(ip, files)
        filled, conflicts = _merge_import_candidates(ip, kind, state, artifacts, candidates, sources)
        state.setdefault("ip", ip)
        state.setdefault("kind", kind)
        state["active_session"] = os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen"
        _save_ssot_state(ip, state)
        return filled, conflicts, artifacts, errors

    def _auto_approve_if_complete(ip: str, state: dict[str, Any], *, reason: str) -> bool:
        if state.get("approved"):
            return False
        if _missing_ssot_decisions(ip, state):
            return False
        doc = _load_ssot_draft(ip)
        custom = doc.get("custom") if isinstance(doc.get("custom"), dict) else {}
        conflicts = custom.get("atlas_import_conflicts") if isinstance(custom, dict) else []
        if conflicts:
            return False
        state["approved"] = True
        state["approved_at"] = time.time()
        state["status"] = "approved"
        state["last_step"] = reason
        _save_ssot_state(ip, state)
        return True

    def _rtl_blocker_path(ip: str) -> Path:
        return PROJECT_ROOT / ip / "rtl" / "rtl_blocked.json"

    def _load_rtl_blocker(ip: str) -> dict[str, Any]:
        path = _rtl_blocker_path(ip)
        if not path.is_file():
            return {}
        try:
            doc = json.loads(path.read_text(encoding="utf-8"))
            return doc if isinstance(doc, dict) else {}
        except Exception as exc:
            return {"reason": f"rtl_blocked.json parse failed: {exc}", "questions": []}

    def _rtl_module_contract_placeholder(q: dict[str, Any]) -> str:
        missing = q.get("missing_modules") if isinstance(q.get("missing_modules"), list) else []
        if not missing and isinstance(q.get("candidate_modules"), list):
            missing = q.get("candidate_modules") or []
        available = q.get("available_refs") if isinstance(q.get("available_refs"), dict) else {}
        rows: list[str] = []
        orphan_refs = q.get("orphan_refs") if isinstance(q.get("orphan_refs"), list) else []
        if orphan_refs:
            rows.append("# orphan refs needing an RTL owner: " + ", ".join(str(v) for v in orphan_refs[:16]))
        if available:
            for key in ("source_sections", "function_model_refs", "decomposition_refs", "cycle_model_refs", "feature_refs", "dataflow_refs", "register_refs", "fsm_refs", "test_refs", "ports"):
                vals = available.get(key) if isinstance(available.get(key), list) else []
                if vals:
                    rows.append(f"# available {key}: " + ", ".join(str(v) for v in vals[:10]))
        rows.append("module_contracts:")
        for item in missing[:8]:
            if not isinstance(item, dict):
                continue
            name = str(item.get("name") or "").strip()
            file = str(item.get("file") or "").strip()
            rows += [
                f"  - name: {name}",
                f"    file: {file}",
                "    implements:",
                "      - <specific behavior this module owns>",
                "    source_sections: [<ssot section names>]",
                "    function_model_refs: [<function_model paths>]",
                "    decomposition_refs: [<decomposition paths>]",
                "    cycle_model_refs: [<cycle_model paths>]",
                "    feature_refs: [<feature names or paths>]",
                "    dataflow_refs: [<dataflow paths>]",
                "    register_refs: [<register names or paths>]",
                "    fsm_refs: [<fsm paths>]",
                "    ports: [<owned ports or internal interface ports>]",
                "    connections: {<local_port>: <ssot/interface signal>}",
            ]
        return "\n".join(rows)

    _RTL_OWNERSHIP_BLOCKER_IDS = {
        "RTL_DYNAMIC_TODO_OWNERSHIP",
        "RTL_MODULE_CONTRACTS",
        "RTL_MODULE_BEHAVIOR_MATCH",
        "SSOT_BEHAVIOR_OWNERSHIP",
    }
    _RTL_CONNECTION_BLOCKER_IDS = {
        "RTL_RESOLVE_CONNECTION_CONTRACTS",
        "RTL_CONNECTION_CONTRACTS",
        "RTL_MANIFEST_CONNECTION_CONTRACTS",
    }
    _RTL_IMPL_BLOCKER_IDS = {
        "RTL_TODO_PLAN_MISSING",
        "DETERMINISTIC_RTL_ARTIFACT_NOT_APPROVED",
        "LLM_RTL_IMPLEMENTATION_REQUIRED",
        "COMMON_AI_AGENT_RTL_PROVENANCE_REQUIRED",
    }

    def _rtl_blocker_qa_section(qid: str, raw: dict[str, Any]) -> tuple[str, str, str]:
        text = " ".join(
            [
                qid,
                str(raw.get("decision_needed") or ""),
                str(raw.get("evidence") or ""),
                " ".join(str(ref) for ref in raw.get("source_refs") or [] if isinstance(raw.get("source_refs"), list)),
                " ".join(str(field) for field in raw.get("required_fields") or [] if isinstance(raw.get("required_fields"), list)),
            ]
        ).lower()
        if qid == "RTL_TARGET_SCALE_POLICY" or "target_scale" in text or "target scale" in text:
            return "19_workflow_todos", "19. Workflow / Human Gates", "quality_gates.rtl_gen.target_scale"
        if qid in _RTL_CONNECTION_BLOCKER_IDS or "connection_contract" in text or "integration.connections" in text:
            return "17_integration", "17. Integration / Connection Contracts", "integration.connections"
        if qid in _RTL_OWNERSHIP_BLOCKER_IDS or "sub_modules" in text or "ownership" in text:
            return "04_architecture", "4. Architecture / Decomposition", "sub_modules"
        if "interface" in text or "port" in text or "clock" in text or "reset" in text:
            return "03_interface", "3. Interface", "io_list"
        if "coverage" in text or "test_requirements" in text or "verification" in text:
            return "18_verification", "18. Verification / Gates", "test_requirements"
        return "19_workflow_todos", "19. Workflow / Human Gates", "workflow_todos.rtl-gen"

    def _rtl_blocker_cards(blocker: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        for q in blocker.get("questions") if isinstance(blocker.get("questions"), list) else []:
            if not isinstance(q, dict):
                continue
            qid = str(q.get("id") or "").strip() or "RTL_BLOCKER"
            if qid in _RTL_IMPL_BLOCKER_IDS:
                continue
            raw_options = q.get("options") if isinstance(q.get("options"), list) else []
            options = [
                {
                    "id": f"{qid}_opt{idx}",
                    "label": str(opt)[:96],
                    "detail": str(opt),
                }
                for idx, opt in enumerate(raw_options, start=1)
                if str(opt).strip()
            ]
            subtitle_parts = [qid]
            if q.get("evidence"):
                subtitle_parts.append(str(q.get("evidence"))[:220])
            if q.get("recommended_default"):
                subtitle_parts.append("Recommended: " + str(q.get("recommended_default"))[:220])
            card = {
                "id": qid,
                "question": str(q.get("decision_needed") or qid),
                "kind": "single" if options else "input",
                "subtitle": " · ".join(subtitle_parts),
                "options": options,
                "blocker": q,
            }
            if qid in _RTL_OWNERSHIP_BLOCKER_IDS:
                card["kind"] = "input"
                card["multiline"] = True
                card["subtitle"] = (
                    str(card.get("subtitle") or "")
                    + " · Paste YAML/JSON with module_contracts; option clicks alone do not approve RTL ownership."
                )[:900]
                card["placeholder"] = _rtl_module_contract_placeholder(q)
            cards.append(card)
        return cards

    def _rtl_blocker_flow_id(blocker: dict[str, Any]) -> str:
        payload = json.dumps(blocker.get("questions") or blocker, ensure_ascii=False, sort_keys=True, default=str)
        digest = hashlib.sha256(payload.encode("utf-8")).hexdigest()[:12]
        return f"rtl_blocker_{digest}"

    def _rtl_blocker_qa_questions(
        ip: str,
        blocker: dict[str, Any],
        cards: list[dict[str, Any]],
        *,
        reason: str,
    ) -> list[dict[str, Any]]:
        source_path = str(_rtl_blocker_path(ip).relative_to(PROJECT_ROOT))
        questions: list[dict[str, Any]] = []
        for card in cards:
            qid = str(card.get("id") or "RTL_BLOCKER").strip() or "RTL_BLOCKER"
            raw = card.get("blocker") if isinstance(card.get("blocker"), dict) else {}
            orphan_refs = raw.get("orphan_refs") if isinstance(raw.get("orphan_refs"), list) else []
            required_fields = raw.get("required_fields") if isinstance(raw.get("required_fields"), list) else []
            candidate_modules = raw.get("candidate_modules") if isinstance(raw.get("candidate_modules"), list) else []
            section_id, section_title, field_path = _rtl_blocker_qa_section(qid, raw)
            criteria = [
                "Resolve the blocker by updating SSOT-owned authority artifacts, not by hand-editing generated RTL.",
                f"Rerun rtl-gen preflight until `{qid}` no longer appears in `{source_path}`.",
            ]
            if qid in _RTL_OWNERSHIP_BLOCKER_IDS:
                criteria.append("Every orphan source_ref must be covered by an exact or dotted-parent ref in one RTL module contract.")
            elif qid == "RTL_TARGET_SCALE_POLICY":
                criteria.append("Lock positive quality_gates.rtl_gen.target_scale minima or approve target_scale_waiver with owner and reason.")
            elif qid in _RTL_CONNECTION_BLOCKER_IDS:
                criteria.append("Answer with machine-readable module/port/signal connection contracts before top integration signoff.")
            source_refs = [source_path]
            source_refs.extend(str(ref) for ref in orphan_refs[:64])
            if raw.get("evidence"):
                source_refs.append(str(raw.get("evidence")))
            questions.append({
                "id": qid,
                "decision_key": qid,
                "decision_label": str(card.get("question") or raw.get("decision_needed") or qid),
                "question": str(card.get("question") or raw.get("decision_needed") or qid),
                "kind": str(card.get("kind") or "input"),
                "subtitle": str(card.get("subtitle") or ""),
                "options": card.get("options") or [],
                "qa_type": "rtl_blocker",
                "source": reason,
                "source_refs": source_refs,
                "field_path": field_path,
                "section_id": section_id,
                "section_title": section_title,
                "content": f"Resolve rtl-gen blocker `{qid}` for `{ip}`.",
                "detail": (
                    f"Evidence: {raw.get('evidence') or blocker.get('reason') or source_path}. "
                    f"Required fields: {', '.join(str(v) for v in required_fields[:12]) or 'SSOT module contract fields'}. "
                    f"Orphan refs: {len(orphan_refs)}. Candidate modules: {len(candidate_modules)}."
                ),
                "criteria": criteria,
                "placeholder": card.get("placeholder") or "",
                "multiline": bool(card.get("multiline")),
            })
        return questions

    def _run_rtl_blocker_resolution(ip: str, blocker: dict[str, Any], answer_entries: list[dict[str, Any]]) -> str:
        import subprocess

        state = _load_ssot_state(ip)
        state.setdefault("ip", ip)
        state.setdefault("kind", "rtl blocker resolution")
        state["approved"] = True
        state["status"] = "rtl_blocker_answered"
        state["rtl_blocker_source"] = str(_rtl_blocker_path(ip).relative_to(PROJECT_ROOT))
        state["rtl_blocker_answers"] = answer_entries
        _save_ssot_state(ip, state)

        scripts = {
            "resolve": SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "resolve_rtl_blockers.py",
            "check": SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh",
            "fl": SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py",
            "preflight": SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py",
        }
        runs: list[dict[str, Any]] = []

        def _run(label: str, cmd: list[str], timeout_s: int = 180) -> int:
            proc = subprocess.run(
                cmd,
                cwd=str(PROJECT_ROOT),
                text=True,
                capture_output=True,
                timeout=timeout_s,
            )
            runs.append({
                "label": label,
                "cmd": " ".join(cmd),
                "returncode": proc.returncode,
                "stdout": (proc.stdout or "").strip()[:12000],
                "stderr": (proc.stderr or "").strip()[:12000],
            })
            return int(proc.returncode)

        resolve_rc = _run("resolve_rtl_blockers", [sys.executable, str(scripts["resolve"]), ip, "--root", str(PROJECT_ROOT)])
        check_rc = _run("check_ssot_disk", ["bash", str(scripts["check"]), ip]) if resolve_rc == 0 else None
        fl_rc = _run("emit_fl_model", [sys.executable, str(scripts["fl"]), ip, "--root", str(PROJECT_ROOT)]) if check_rc == 0 else None
        preflight_rc = _run("rtl_preflight", [sys.executable, str(scripts["preflight"]), ip, "--root", str(PROJECT_ROOT), "--preflight-only"]) if fl_rc == 0 else None

        if preflight_rc == 0:
            headline = "[SSOT RESULT] rtl blocker decisions applied; rtl-gen preflight PASS"
        elif preflight_rc == 2:
            headline = "[SSOT QUESTION] rtl-gen still needs SSOT decisions"
        else:
            headline = "[SSOT BLOCKED] rtl blocker resolution failed validation"

        lines = [
            headline,
            f"module: {ip}",
            f"source blocker: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}",
            f"answers captured: {len(answer_entries)}",
            "",
            "runs:",
        ]
        for run in runs:
            lines.append(f"- {run['label']}: exit {run['returncode']}")
            lines.append(f"  cmd: {run['cmd']}")
            if run["stdout"]:
                lines.append("  stdout:")
                lines.append(run["stdout"])
            if run["stderr"]:
                lines.append("  stderr:")
                lines.append(run["stderr"])
        lines += [
            "",
            "artifacts:",
            f"- {ip}/yaml/{ip}.ssot.yaml",
            f"- {ip}/rtl/rtl_blocked_resolved.json",
            f"- {ip}/model/functional_model.py",
            f"- {ip}/model/decomposition.json",
            f"- {ip}/cov/fcov_plan.json",
        ]
        if preflight_rc == 0:
            lines.append("")
            lines.append("next: queued /ssot-rtl to start RTL implementation from the repaired SSOT")
            bridge.queue_prompt(f"/ssot-rtl {ip}")
        return "\n".join(lines)

    def _start_rtl_blocker_qna(
        ip: str,
        *,
        reason: str = "rtl-gen preflight",
        interactive: bool = True,
    ) -> bool:
        blocker = _load_rtl_blocker(ip)
        cards = _rtl_blocker_cards(blocker)
        if not blocker or not cards:
            _emit_workflow_result(
                f"[RTL BLOCKER Q&A] no rtl_blocked.json questions found for {ip}",
                "resolve-rtl-blockers",
            )
            return True

        ctx_ip, ctx_session = _active_ssot_qa_context()
        ssot_session = ctx_session if ctx_ip == ip and ctx_session else f"{ip}/ssot-gen"
        qa_flow_id = _rtl_blocker_flow_id(blocker)
        qa_questions = _rtl_blocker_qa_questions(ip, blocker, cards, reason=reason)
        qa_pairs = _ssot_q_pairs_from_questions(qa_questions)
        if qa_pairs:
            _upsert_ssot_qa_items(
                ip,
                flow_id=qa_flow_id,
                kind=str((_load_ssot_state(ip) or {}).get("kind") or "general IP"),
                q_pairs=qa_pairs,
                status="pending",
                session=ssot_session,
                source="rtl-blocker",
            )
            bridge.emit(
                "ssot_qa_updated",
                ip=ip,
                workflow="ssot-gen",
                flow_id=qa_flow_id,
                session=ssot_session,
            )

        if not interactive:
            msg = (
                f"[RTL BLOCKER Q&A] recorded {len(qa_pairs)} pending SSOT QA card(s) for {ip}\n"
                f"source: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}\n"
                f"session: {ssot_session}\n"
                "next: answer from SSOT QA/Preview, or run /resolve-rtl-blockers "
                f"{ip} when ready to apply the decisions."
            )
            _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "resolve-rtl-blockers")
            return True

        def _worker() -> None:
            import uuid as _uuid

            flow_id = "rtlq_" + _uuid.uuid4().hex[:10]
            bridge.open_question(flow_id)
            bridge.emit("ask_user", flow_id=flow_id, questions=cards)
            bridge.emit("agent_state", running=True)
            try:
                ans = bridge.wait_answer(flow_id, timeout=900)
            finally:
                bridge.close_question(flow_id)
            if not isinstance(ans, dict) or not isinstance(ans.get("answers"), list):
                msg = (
                    f"[RTL BLOCKER Q&A] {ip}: no answer received; SSOT remains blocked.\n"
                    f"source: {_rtl_blocker_path(ip).relative_to(PROJECT_ROOT)}"
                )
                _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
                _append_workflow_history("ssot-gen", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, "resolve-rtl-blockers")
                return

            answer_entries: list[dict[str, Any]] = []
            qa_answers: dict[str, dict[str, Any]] = {}
            for qa_pair, card, raw_answer in zip(qa_pairs, cards, ans.get("answers") or []):
                qa = raw_answer if isinstance(raw_answer, dict) else {}
                key, _label, question = qa_pair
                answer_text = _answer_text(qa, question)
                answer_entries.append({
                    "id": card.get("id"),
                    "decision_needed": card.get("question"),
                    "answer": answer_text,
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                    "source": reason,
                })
                qa_answers[key] = {
                    "answer": answer_text,
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                }
            if qa_pairs:
                _upsert_ssot_qa_items(
                    ip,
                    flow_id=qa_flow_id,
                    kind=str((_load_ssot_state(ip) or {}).get("kind") or "general IP"),
                    q_pairs=qa_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                    source="rtl-blocker",
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ip,
                    workflow="ssot-gen",
                    flow_id=qa_flow_id,
                    session=ssot_session,
                )
            try:
                msg = _run_rtl_blocker_resolution(ip, blocker, answer_entries)
            except Exception as exc:
                msg = f"[RTL BLOCKER Q&A] {ip}: failed to apply answers: {exc}"
            _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "resolve-rtl-blockers")

        threading.Thread(target=_worker, daemon=True).start()
        return True

    def _sim_human_gate_cards(ip: str, classify_doc: dict[str, Any]) -> list[dict[str, Any]]:
        cards: list[dict[str, Any]] = []
        classifications = classify_doc.get("classifications")
        for item in classifications if isinstance(classifications, list) else []:
            if not isinstance(item, dict) or item.get("llm_loop_allowed") is not False:
                continue
            goal_id = str(item.get("goal_id") or "EQ_HUMAN_GATE").strip() or "EQ_HUMAN_GATE"
            human_question = str(item.get("human_question") or "").strip()
            evidence = item.get("evidence") if isinstance(item.get("evidence"), dict) else {}
            ssot_refs = evidence.get("ssot_refs") if isinstance(evidence.get("ssot_refs"), list) else []
            fl_expected = evidence.get("fl_expected") if isinstance(evidence.get("fl_expected"), dict) else {}
            rtl_observed = evidence.get("rtl_observed") if isinstance(evidence.get("rtl_observed"), dict) else {}
            evidence_bits = [
                f"class={item.get('classification') or 'unknown'}",
                f"owner={item.get('owner') or 'human'}",
            ]
            if ssot_refs:
                evidence_bits.append("SSOT " + ", ".join(str(x) for x in ssot_refs[:3]))
            if fl_expected:
                evidence_bits.append("FL " + json.dumps(fl_expected, sort_keys=True)[:180])
            if rtl_observed:
                evidence_bits.append("RTL " + json.dumps(rtl_observed, sort_keys=True)[:180])
            cards.append({
                "id": goal_id,
                "question": f"Decision needed for {goal_id}: define expected behavior or approve waiver",
                "kind": "single",
                "subtitle": " · ".join(evidence_bits)[:500],
                "options": [
                    {
                        "id": f"{goal_id}_update_ssot",
                        "label": "Update SSOT",
                        "detail": "Record the intended behavior in SSOT/requirements, then regenerate FL, equivalence goals, TB, and coverage.",
                    },
                    {
                        "id": f"{goal_id}_waiver",
                        "label": "Waiver",
                        "detail": "Record an explicit waiver/rationale; signoff remains human-owned until the waiver is reviewed.",
                    },
                ],
                "human_question": human_question,
                "classification": item,
            })
        return cards

    def _persist_sim_human_gate_answers(
        ip: str,
        classify_doc: dict[str, Any],
        cards: list[dict[str, Any]],
        answer_entries: list[dict[str, Any]],
    ) -> Path:
        sim_dir = PROJECT_ROOT / ip / "sim"
        sim_dir.mkdir(parents=True, exist_ok=True)
        out_path = sim_dir / "human_gate_answers.json"
        doc = {
            "schema_version": 1,
            "type": "fl_rtl_human_gate_answers",
            "ip": ip,
            "captured_at": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
            "source": str((PROJECT_ROOT / ip / "sim" / "mismatch_classification.json").relative_to(PROJECT_ROOT)),
            "answers": answer_entries,
        }
        out_path.write_text(json.dumps(doc, ensure_ascii=False, indent=2) + "\n", encoding="utf-8")

        state = _load_ssot_state(ip)
        state.setdefault("ip", ip)
        state.setdefault("kind", "equivalence human gate")
        state["status"] = "equivalence_human_gate_answered"
        state["equivalence_human_gate_source"] = doc["source"]
        state["equivalence_human_gate_answers"] = answer_entries
        state["equivalence_human_gate_classifications"] = [
            card.get("classification") for card in cards if isinstance(card.get("classification"), dict)
        ]
        _save_ssot_state(ip, state)

        return out_path

    def _start_sim_human_gate_qna(ip: str, classify_doc: dict[str, Any], *, reason: str = "sim-debug") -> bool:
        cards = _sim_human_gate_cards(ip, classify_doc)
        if not cards:
            return False

        def _worker() -> None:
            import uuid as _uuid

            flow_id = "simq_" + _uuid.uuid4().hex[:10]
            bridge.open_question(flow_id)
            bridge.emit("ask_user", flow_id=flow_id, questions=cards)
            bridge.emit("agent_state", running=True)
            try:
                ans = bridge.wait_answer(flow_id, timeout=900)
            finally:
                bridge.close_question(flow_id)
            if not isinstance(ans, dict) or not isinstance(ans.get("answers"), list):
                msg = (
                    f"[SIM HUMAN GATE] {ip}: no answer received; mismatch remains human-gated.\n"
                    f"source: {ip}/sim/mismatch_classification.json"
                )
                _append_session_message(f"{ip}/sim_debug", "assistant", msg)
                _append_workflow_history("sim_debug", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, "sim-debug")
                return

            answer_entries: list[dict[str, Any]] = []
            for card, raw_answer in zip(cards, ans.get("answers") or []):
                qa = raw_answer if isinstance(raw_answer, dict) else {}
                classification = card.get("classification") if isinstance(card.get("classification"), dict) else {}
                answer_entries.append({
                    "goal_id": card.get("id"),
                    "decision_needed": card.get("question"),
                    "answer": _answer_text(qa, card),
                    "selected": qa.get("selected") or [],
                    "custom": str(qa.get("custom") or "").strip(),
                    "source": reason,
                    "classification": classification.get("classification"),
                    "owner": classification.get("owner"),
                    "evidence": classification.get("evidence") if isinstance(classification.get("evidence"), dict) else {},
                    "human_question": card.get("human_question") or "",
                })
            try:
                out_path = _persist_sim_human_gate_answers(ip, classify_doc, cards, answer_entries)
                msg = (
                    f"[SIM HUMAN GATE] captured {len(answer_entries)} answer(s) for {ip}\n"
                    f"answers: {out_path.relative_to(PROJECT_ROOT)}\n"
                    "next: rerun SSOT/FL/equivalence generation if behavior changed, or keep signoff human-owned for waivers"
                )
            except Exception as exc:
                msg = f"[SIM HUMAN GATE] {ip}: failed to persist answers: {exc}"
            _append_session_message(f"{ip}/sim_debug", "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "sim-debug")

        threading.Thread(target=_worker, daemon=True).start()
        return True

    def _handle_resolve_rtl_blockers_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("resolve-rtl-blockers", "rrb"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[resolve-rtl-blockers] missing or invalid IP name\n"
                "usage: /resolve-rtl-blockers <ip_name>",
                "resolve-rtl-blockers",
            )
            return True
        return _start_rtl_blocker_qna(ip, reason="manual /resolve-rtl-blockers")

    app.state.atlas_bridge = bridge
    app.state.start_rtl_blocker_qna = _start_rtl_blocker_qna
    app.state.active_ssot_qa_context = _active_ssot_qa_context
    app.state.valid_ip_name = _valid_ip_name
    app.state.ssot_q_pairs_from_questions = _ssot_q_pairs_from_questions
    app.state.load_ssot_state = _load_ssot_state
    app.state.upsert_ssot_qa_items = _upsert_ssot_qa_items
    app.state.status_group = _status_group

    def _emit_workflow_result(text: str, tool: str = "workflow") -> None:
        body = (text or "").strip() or "(no output)"
        payload = "```\n" + body + "\n```"
        bridge.emit("tool_result", text=payload, tool=tool, truncated=False)
        bridge.emit("slash_output", text=payload)
        bridge.emit("flush")
        bridge.emit("commands_changed")
        bridge.emit("agent_state", running=False)

    def _handle_import_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("import", "imp"):
            return False

        ip, raw_paths, err = _parse_import_args(args)
        if err:
            _emit_workflow_result(err, "import")
            return True
        _set_active_ssot_ip(ip)
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT IMPORT] failed to scaffold {ip}: {exc}", "import")
            return True

        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        kind = str(state.get("kind") or "imported IP evidence")
        _ensure_ssot_draft(ip, kind)
        files, errors = _collect_import_files(ip, raw_paths)
        if not files:
            msg = (
                f"[SSOT IMPORT] {ip}: no importable files found\n"
                f"searched: {', '.join(raw_paths) if raw_paths else ip + '/'}\n"
                "usage: /import [path ...]  or  /import --ip <ip_name> [path ...]"
            )
            if errors:
                msg += "\n\nnotes:\n" + "\n".join(f"- {e}" for e in errors[:8])
            _append_session_message(f"{ip}/ssot-gen", "user", text)
            _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "import")
            _emit_ssot_approval_ready(ip, state)
            return True

        artifacts, candidates, sources = _extract_import_candidates(ip, files)
        filled, conflicts = _merge_import_candidates(ip, kind, state, artifacts, candidates, sources)
        state.setdefault("ip", ip)
        state.setdefault("kind", kind)
        state["active_session"] = os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen"
        _save_ssot_state(ip, state)

        missing = _missing_ssot_decisions(ip, state)
        todo_summary = state.get("last_import_yaml_todos") if isinstance(state.get("last_import_yaml_todos"), dict) else {}
        downstream_summary = todo_summary.get("downstream_todos") if isinstance(todo_summary.get("downstream_todos"), dict) else {}
        todo_parts = [f"ssot-gen sections={todo_summary.get('section_todos', 0)}"]
        todo_parts.extend(f"{stage}={count}" for stage, count in downstream_summary.items())
        todo_parts.append(f"evidence rows={todo_summary.get('evidence_rows', 0)}")
        lines = [
            f"[SSOT IMPORT] {ip}",
            f"imported files: {len(files)}",
            "yaml TODO draft: " + ", ".join(todo_parts),
        ]
        if filled:
            lines.append("filled decisions: " + ", ".join(filled))
        else:
            lines.append("filled decisions: (none)")
        if conflicts:
            lines.append("conflicts needing /grill-me review: " + ", ".join(c["key"] for c in conflicts[:8]))
        if missing:
            lines.append("missing decisions: " + ", ".join(missing))
        else:
            lines.append("missing decisions: (none)")
        if errors:
            lines += ["", "notes:"]
            lines.extend(f"- {e}" for e in errors[:8])
        lines += [
            "",
            "evidence:",
        ]
        lines.extend(f"- {a.get('path')}" for a in artifacts[:12])
        if len(artifacts) > 12:
            lines.append(f"- ... {len(artifacts) - 12} more")
        lines += [
            "",
            "Next:",
            "  /grill-me" if missing or conflicts else "  approve",
            "  /to-ssot after approval",
        ]
        msg = "\n".join(lines)
        _append_session_message(f"{ip}/ssot-gen", "user", text)
        _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "import")
        _emit_ssot_approval_ready(ip, state, missing)
        return True

    def _handle_grill_me_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("grill-me", "grill", "g"):
            return False
        ip_arg = args.split(None, 1)[0] if args else ""
        if ip_arg and not _valid_ip_name(ip_arg):
            _emit_workflow_result(
                "[SSOT GRILL] invalid IP name\nusage: /grill-me [<ip_name>]",
                "grill-me",
            )
            return True
        ip = ip_arg or _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GRILL] no active IP found\n"
                "usage: /new-ip <ip_name> first, then /grill-me",
                "grill-me",
            )
            return True
        _set_active_ssot_ip(ip)
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as exc:
            _emit_workflow_result(f"[SSOT GRILL] failed to scaffold {ip}: {exc}", "grill-me")
            return True
        state = _load_ssot_state(ip) or _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "simple APB peripheral"))
        state["active_session"] = os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen"
        state["last_step"] = "grill-me"
        _save_ssot_state(ip, state)
        missing = _missing_ssot_decisions(ip, state)
        msg = (
            f"[SSOT GRILL] {ip}: queued ssot-gen LLM to generate IP-specific Q&A.\n"
            f"backend baseline missing keys: {', '.join(missing) if missing else '(none)'}\n"
            "Fixed question templates are bypassed; questions must be derived from the current SSOT/imported evidence."
        )
        _append_session_message(f"{ip}/ssot-gen", "user", text)
        _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "grill-me")
        bridge.queue_prompt("/mode normal")
        bridge.queue_prompt("/wf ssot-gen")
        bridge.queue_prompt(_render_ssot_llm_qna_prompt(ip, str(state.get("kind") or "simple APB peripheral"), state))
        bridge.emit("agent_state", running=True)
        return True

    def _handle_new_ip_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("new-ip", "ni"):
            return False
        ip, kind, import_paths, parse_err = _parse_new_ip_args(args)
        if parse_err:
            _emit_workflow_result(parse_err, "new-ip")
            return True
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT PLAN] missing or invalid IP name\n"
                "usage: /new-ip <ip_name> [kind]\n"
                "example: /new-ip demo_i2c APB4 I2C controller\n"
                "then: /import <ip_name> or /import @path",
                "new-ip",
            )
            return True

        # Approval gate allows scaffold/session creation and draft SSOT
        # accumulation only. Production SSOT canonicalization remains
        # blocked until explicit approval.
        try:
            (PROJECT_ROOT / ip).mkdir(parents=True, exist_ok=True)
        except OSError as e:
            _emit_workflow_result(f"[SSOT PLAN] failed to scaffold {ip}: {e}", "new-ip")
            return True

        _set_active_ssot_ip(ip)
        state = _new_ssot_state(ip, kind)
        _ensure_new_ip_structure(ip)
        _ensure_ssot_draft(ip, kind)
        import_notes = []
        if import_paths:
            import_notes.append(
                "/new-ip is structure-only; import markers were not scanned. "
                "Run `/import " + ip + " " + " ".join(import_paths) + "` to populate SSOT TODOs."
            )
        _save_ssot_state(ip, state)
        session = f"{ip}/ssot-gen"
        plan = _render_new_ip_plan(ip, kind, state)
        if import_notes:
            plan += "\n\nImport:\n" + "\n".join(f"- {line}" for line in import_notes)
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", plan)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", plan)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + plan + "\n```")
        _emit_workflow_result(plan, "new-ip")
        _emit_ssot_approval_ready(ip, state)
        return True

    def _handle_approval_command(text: str) -> bool:
        raw = (text or "").strip()
        low = raw.lower()
        if not (low.startswith("approve") or raw.startswith("승인")):
            return False
        parts = raw.split()
        ip = parts[1] if len(parts) > 1 else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT APPROVAL] no pending IP found\n"
                "usage: approve [<ip_name>]  or  승인 [<ip_name>]",
                "approve",
            )
            return True
        _set_active_ssot_ip(ip)
        state = _load_ssot_state(ip)
        if not state:
            state = _new_ssot_state(ip)
        _ensure_ssot_draft(ip, str(state.get("kind") or "simple APB peripheral"))
        missing = _missing_ssot_decisions(ip, state)
        if missing:
            msg = (
                f"[SSOT APPROVAL] blocked: {ip} still has missing decisions\n"
                f"missing decisions: {', '.join(missing)}\n"
                "Use /import to seed existing evidence, then /grill-me to answer only the gaps."
            )
            _append_session_message(f"{ip}/ssot-gen", "user", text)
            _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
            _append_workflow_history("ssot-gen", "user", text)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "approve")
            _emit_ssot_approval_ready(ip, state, missing)
            return True
        state["approved"] = True
        state["approved_at"] = time.time()
        state["status"] = "approved"
        state["active_session"] = os.environ.get("ATLAS_ACTIVE_SESSION") or f"{ip}/ssot-gen"
        state["last_step"] = "approve"
        _save_ssot_state(ip, state)
        spec = _render_approved_ssot_spec(ip, state)
        msg = (
            f"[SSOT APPROVED] {ip}\n"
            f"YAML write is now allowed.\n"
            "Next: type /to-ssot in the Web UI when the summary looks correct."
        )
        session = f"{ip}/ssot-gen"
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", spec)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "approve")
        _emit_ssot_approval_ready(ip, state, [])
        return True

    def _handle_to_ssot_gate(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("to-ssot", "ssot", "ts"):
            return False
        ip = args.split(None, 1)[0] if args else _active_ssot_ip()
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[SSOT GATE] missing IP name\n"
                "usage: /to-ssot [<ip_name>]",
                "to-ssot",
            )
            return True
        _set_active_ssot_ip(ip)
        state = _load_ssot_state(ip)
        if state:
            kind = str(state.get("kind") or "imported IP evidence")
            filled, conflicts, artifacts, errors = _import_defaults_if_available(ip, kind, state)
            state = _load_ssot_state(ip)
            if artifacts:
                note = (
                    f"[SSOT IMPORT] auto-imported {len(artifacts)} file(s) before /to-ssot {ip}\n"
                    f"filled decisions: {', '.join(filled) if filled else '(none)'}\n"
                    f"conflicts: {', '.join(str(c.get('key') or '') for c in conflicts[:8]) if conflicts else '(none)'}"
                )
                if errors:
                    note += "\nnotes:\n" + "\n".join(f"- {err}" for err in errors[:8])
                _append_session_message(f"{ip}/ssot-gen", "assistant", note)
                _append_workflow_history("ssot-gen", "assistant", note)
                _append_active_history("assistant", "```\n" + note + "\n```")
            if _auto_approve_if_complete(ip, state, reason="auto_approve_from_import_before_to_ssot"):
                state = _load_ssot_state(ip)
                note = f"[SSOT APPROVED] {ip}: auto-approved because imported evidence filled all required decisions."
                _append_session_message(f"{ip}/ssot-gen", "assistant", note)
                _append_workflow_history("ssot-gen", "assistant", note)
                _append_active_history("assistant", "```\n" + note + "\n```")
        if not state.get("approved"):
            missing = _missing_ssot_decisions(ip, state) if state else [k for k, _ in _SSOT_REQUIRED_DECISIONS]
            msg = (
                f"[SSOT GATE] blocked: {ip} is not approved yet\n"
                "YAML writes need either complete imported evidence or explicit approval.\n"
                f"missing decisions: {', '.join(missing) if missing else '(review not approved)'}\n\n"
                f"Put files under {ip}/doc/ or run /import @doc, then /to-ssot again. Use /grill-me only for the listed gaps."
            )
            _append_session_message(f"{ip}/ssot-gen", "user", text)
            _append_session_message(f"{ip}/ssot-gen", "assistant", msg)
            _append_active_history("user", text)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "to-ssot")
            if state:
                _emit_ssot_approval_ready(ip, state, missing)
            return True
        spec = _render_approved_ssot_spec(ip, state)
        _append_session_message(f"{ip}/ssot-gen", "user", text)
        _append_session_message(f"{ip}/ssot-gen", "assistant", spec)
        _append_workflow_history("ssot-gen", "user", text)
        _append_workflow_history("ssot-gen", "assistant", spec)
        _append_active_history("user", text)
        script_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "approved_to_ssot.py"
        validator_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        template_path = SOURCE_ROOT / "workflow" / "ssot-gen" / "rules" / "ssot-template.yaml"
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"

        try:
            import subprocess

            draft = subprocess.run(
                [sys.executable, str(script_path), ip, "--root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                text=True,
                capture_output=True,
                timeout=60,
            )
            validate = subprocess.run(
                ["bash", str(validator_path), ip],
                cwd=str(PROJECT_ROOT),
                text=True,
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            draft = None
            validate = None
            bridge_msg = f"[to-ssot] generic bridge failed before validation: {exc}"
        else:
            bridge_parts = [
                f"[to-ssot] generic approved-state SSOT bridge for {ip}",
                f"script: {script_path}",
                f"ssot: {ssot_path}",
                f"bridge exit: {draft.returncode}",
            ]
            if draft.stdout.strip():
                bridge_parts += ["", "bridge stdout:", draft.stdout.strip()]
            if draft.stderr.strip():
                bridge_parts += ["", "bridge stderr:", draft.stderr.strip()]
            bridge_parts += ["", f"validator exit: {validate.returncode}"]
            if validate.stdout.strip():
                bridge_parts += ["", "validator stdout:", validate.stdout.strip()]
            if validate.stderr.strip():
                bridge_parts += ["", "validator stderr:", validate.stderr.strip()]
            bridge_msg = "\n".join(bridge_parts)

        _append_session_message(f"{ip}/ssot-gen", "assistant", bridge_msg)
        _append_workflow_history("ssot-gen", "assistant", bridge_msg)
        _append_active_history("assistant", "```\n" + bridge_msg + "\n```")
        _emit_workflow_result(bridge_msg, "to-ssot")

        if draft is not None and validate is not None and draft.returncode == 0 and validate.returncode == 0:
            return True

        bridge.queue_prompt("/mode normal")
        bridge.queue_prompt("/wf ssot-gen")
        bridge.queue_prompt("/clear")
        bridge.queue_prompt(
            f"/to-ssot {ip}\n\n"
            f"Hard workspace boundary for this run:\n"
            f"- Project root / IP artifacts: `{PROJECT_ROOT}`\n"
            f"- Common agent source root: `{SOURCE_ROOT}`\n"
            f"- SSOT path to edit: `{ssot_path}`\n"
            "Do not search or read outside those two roots. Ignore similarly named "
            "directories such as NEW_IP, NEW_CPU, brian_home, or other legacy projects.\n\n"
            "The generic approved-state bridge attempted to write the SSOT first. "
            "Its exact disk-truth result was:\n"
            "```text\n"
            f"{bridge_msg}\n"
            "```\n\n"
            "Approved Web SSOT Spec, copied inline so this fresh run does not depend "
            "on stale workflow chat history:\n"
            "```text\n"
            f"{spec}\n"
            "```\n\n"
            "Execute this as the approved SSOT write step. Do not call todo_write; "
            "it is Plan Mode only. Use the approved Web SSOT Spec above as source truth, "
            "replace scaffold-only placeholders, "
            "write the complete production canonical SSOT, and run the exact validator "
            f"`bash {validator_path} {ip}` before emitting [SSOT HANDOFF]. "
            f"The authoritative 33-section template is `{template_path}`. "
            "Do not use an inline/stale 20/25-section validator, and do not claim "
            "PASS unless that exact script exits 0.\n\n"
            "Bounded execution requirement: read the template, existing SSOT, and "
            "validator at most once each. After identifying missing/weak sections, "
            "your next tool action must be write_file, replace_in_file, or the "
            "validator run if the file is already complete. Do not reread the same "
            "files or draft the full YAML in prose before using the file tool."
        )
        bridge.emit("agent_state", running=True)
        return True

    def _handle_repair_ssot_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-ssot", "rs"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-ssot] missing or invalid IP name\nusage: /repair-ssot <ip_name>",
                "repair-ssot",
            )
            return True

        script = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "repair_ssot_schema.py"
        validator = SOURCE_ROOT / "workflow" / "ssot-gen" / "scripts" / "check_ssot_disk.sh"
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        session = f"{ip}/ssot-gen"
        _append_session_message(session, "user", text)
        _append_workflow_history("ssot-gen", "user", text)
        _append_active_history("user", text)
        bridge.emit("agent_state", running=True)

        if not ssot_path.is_file():
            msg = (
                f"[repair-ssot] blocked: SSOT not found at {ssot_path}\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first."
            )
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        try:
            import subprocess

            repair = subprocess.run(
                [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                cwd=str(PROJECT_ROOT),
                text=True,
                capture_output=True,
                timeout=60,
            )
            validate = subprocess.run(
                ["bash", str(validator), ip],
                cwd=str(PROJECT_ROOT),
                text=True,
                capture_output=True,
                timeout=60,
            )
        except Exception as exc:
            msg = f"[repair-ssot] failed: {exc}"
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("ssot-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, "repair-ssot")
            return True

        parts = [
            f"[repair-ssot] {ip}",
            f"source: {ssot_path}",
            f"repair exit: {repair.returncode}",
        ]
        if repair.stdout.strip():
            parts += ["", "repair stdout:", repair.stdout.strip()]
        if repair.stderr.strip():
            parts += ["", "repair stderr:", repair.stderr.strip()]
        parts += ["", f"validator exit: {validate.returncode}"]
        if validate.stdout.strip():
            parts += ["", "validator stdout:", validate.stdout.strip()]
        if validate.stderr.strip():
            parts += ["", "validator stderr:", validate.stderr.strip()]
        msg = "\n".join(parts)
        _append_session_message(session, "assistant", msg)
        _append_workflow_history("ssot-gen", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-ssot")
        return True

    def _handle_repair_rtl_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-rtl", "rrtl"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-rtl] missing or invalid IP name\nusage: /repair-rtl <ip_name>",
                "repair-rtl",
            )
            return True
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[repair-rtl] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first.",
                "repair-rtl",
            )
            return True
        session = f"{ip}/rtl-gen"
        compile_report = PROJECT_ROOT / ip / "rtl" / "rtl_compile.json"
        lint_report = PROJECT_ROOT / ip / "lint" / "dut_lint.json"
        queued = (
            f"[repair-rtl] queued through rtl-gen\n"
            f"module: {ip}\n"
            f"ssot: {ip}/yaml/{ip}.ssot.yaml\n"
            f"compile report: {ip}/rtl/rtl_compile.json\n"
            f"lint report: {ip}/lint/dut_lint.json"
        )
        _append_session_message(session, "user", text)
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        bridge.queue_prompt("/mode normal")
        bridge.queue_prompt("/wf rtl-gen")
        bridge.queue_prompt("/clear")
        bridge.queue_prompt(f"/todo template ssot-rtl {ip}")
        bridge.queue_prompt(
            f"Repair RTL for {ip} using only SSOT-driven rtl-gen ownership.\n\n"
            f"Read these evidence files first:\n"
            f"- SSOT: `{ssot_path}`\n"
            f"- compile report: `{compile_report}`\n"
            f"- compile log: `{PROJECT_ROOT / ip / 'rtl' / 'rtl_compile.log'}`\n"
            f"- lint report: `{lint_report}`\n"
            f"- filelist: `{PROJECT_ROOT / ip / 'list' / f'{ip}.f'}`\n\n"
            "Repair only files under `<ip>/rtl/` and `<ip>/list/` unless the evidence "
            "proves the SSOT manifest itself is wrong. If SSOT/filelist/top-module "
            "naming is inconsistent, emit `[SSOT QUESTION] -> ssot-gen` with the exact "
            "YAML fields to repair instead of silently changing the YAML. Do not edit TB, "
            "sim, cov, or unrelated IPs.\n\n"
            "Current required repair classes:\n"
            "- Eliminate all `rtl_compile.json.style_violation_details`; especially no "
            "parameterized part-selects inside `always`, `always_comb`, `always_ff`, or "
            "`always_latch`. Use helper wires and continuous assigns.\n"
            "- Eliminate all Icarus `sorry:` diagnostics and any compile warnings/errors.\n"
            "- Preserve Verilator DUT-only lint pass with zero suppressions.\n"
            "- Reconcile filelist and top wrapper naming with SSOT, or escalate to ssot-gen "
            "if the SSOT source of truth must change.\n\n"
            "After the final RTL edit, run exactly:\n"
            f"`python3 {SOURCE_ROOT / 'workflow' / 'rtl-gen' / 'scripts' / 'rtl_compile_report.py'} {ip} --top {ip}`\n"
            f"`python3 {SOURCE_ROOT / 'workflow' / 'lint' / 'scripts' / 'dut_lint_report.py'} {ip} --top {ip}`\n\n"
            "DONE requires compile pass E0/D0/S0, lint pass E0/W0/S0, and no hidden "
            "waivers/suppressions. If any part cannot be fixed from RTL alone, stop with "
            "a precise `[SSOT QUESTION]` or `[RTL BLOCKED]` rather than claiming DONE."
        )
        bridge.emit("agent_state", running=True)
        _emit_workflow_result(queued, "repair-rtl")
        bridge.emit("agent_state", running=True)
        return True

    def _handle_repair_equiv_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        if cmd not in ("repair-equiv", "repair-equivalence", "reqv"):
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                "[repair-equiv] missing or invalid IP name\nusage: /repair-equiv <ip_name>",
                "repair-equiv",
            )
            return True
        classify_path = PROJECT_ROOT / ip / "sim" / "mismatch_classification.json"
        if not classify_path.is_file():
            _emit_workflow_result(
                f"[repair-equiv] blocked: missing {ip}/sim/mismatch_classification.json\n"
                f"Run /sim-debug {ip} first.",
                "repair-equiv",
            )
            return True
        try:
            classify_doc = json.loads(classify_path.read_text(encoding="utf-8"))
            if not isinstance(classify_doc, dict):
                classify_doc = {}
        except Exception as exc:
            _emit_workflow_result(
                f"[repair-equiv] blocked: cannot parse {ip}/sim/mismatch_classification.json: {exc}",
                "repair-equiv",
            )
            return True
        classifications = classify_doc.get("classifications")
        if not isinstance(classifications, list):
            classifications = []

        loopable = [
            item for item in classifications
            if isinstance(item, dict)
            and item.get("llm_loop_allowed") is True
            and str(item.get("owner") or "").strip()
            and str(item.get("repair_prompt") or "").strip()
        ]
        human_only = [
            item for item in classifications
            if isinstance(item, dict) and item.get("llm_loop_allowed") is False
        ]
        if not loopable:
            lines = [
                "[repair-equiv] no loopable classifications found",
                f"module: {ip}",
                f"classification status: {classify_doc.get('status') or 'unknown'}",
                f"human-gated: {len(human_only)}",
                f"source: {ip}/sim/mismatch_classification.json",
            ]
            if human_only:
                lines.append("next: answer ATLAS human-gate questions from /sim-debug before repair")
            else:
                lines.append("next: rerun /sim-debug after a failing sim to create repair classifications")
            _emit_workflow_result("\n".join(lines), "repair-equiv")
            return True

        route = {
            "rtl-gen": ("rtl-gen", "ssot-rtl"),
            "rtl": ("rtl-gen", "ssot-rtl"),
            "fl-model-gen": ("fl-model-gen", "ssot-fl-model"),
            "fl_model": ("fl-model-gen", "ssot-fl-model"),
            "tb-gen": ("tb-gen", "ssot-tb-cocotb"),
            "tb": ("tb-gen", "ssot-tb-cocotb"),
            "coverage": ("coverage", "coverage_iter"),
            "sim_debug": ("sim_debug", "sim-debug"),
            "sim-debug": ("sim_debug", "sim-debug"),
        }
        grouped: dict[tuple[str, str], list[dict[str, Any]]] = {}
        unrouted: list[dict[str, Any]] = []
        for item in loopable:
            owner = str(item.get("owner") or "").strip()
            key = route.get(owner)
            if key is None:
                unrouted.append(item)
                continue
            grouped.setdefault(key, []).append(item)

        session = f"{ip}/sim_debug"
        _append_session_message(session, "user", text)
        _append_active_history("user", text)
        queued_lines = [
            "[repair-equiv] queued loopable equivalence repairs",
            f"module: {ip}",
            f"source: {ip}/sim/mismatch_classification.json",
            f"loopable: {len(loopable)}",
            f"human-gated: {len(human_only)}",
        ]
        for (workflow, template), items in grouped.items():
            queued_lines.append(f"- {workflow}: {len(items)} classification(s)")
            bridge.queue_prompt("/mode normal")
            bridge.queue_prompt(f"/wf {workflow}")
            bridge.queue_prompt("/clear")
            bridge.queue_prompt(f"/todo template {template} {ip}")
            payload = json.dumps(items, indent=2, ensure_ascii=False)[:12000]
            bridge.queue_prompt(
                f"Execute classified FL-vs-RTL repair for {ip}.\n\n"
                "Hard rules:\n"
                "- Use SSOT YAML, FunctionalModel, equivalence_goals.json, scoreboard_events.jsonl, "
                "fl_rtl_compare.json, and mismatch_classification.json as evidence.\n"
                "- Repair only this workflow owner's artifacts. Do not change SSOT semantics unless "
                "the classification explicitly routes to ssot-gen and a human answer exists.\n"
                "- Do not copy wrong RTL observed behavior into expected values.\n"
                "- After repair, rerun the smallest owning validator, then tell the user to rerun "
                f"/sim {ip}, /sim-debug {ip}, and /goal-audit {ip}.\n\n"
                f"Classifications for this owner:\n```json\n{payload}\n```"
            )
        if unrouted:
            queued_lines.append(f"unrouted owners: {', '.join(str(i.get('owner')) for i in unrouted[:8] if isinstance(i, dict))}")
        if human_only:
            queued_lines.append("human gate remains required for non-loopable classifications")
        msg = "\n".join(queued_lines)
        _append_session_message(session, "assistant", "```\n" + msg + "\n```")
        _append_workflow_history("sim_debug", "assistant", msg)
        _append_active_history("assistant", "```\n" + msg + "\n```")
        _emit_workflow_result(msg, "repair-equiv")
        bridge.emit("agent_state", running=True)
        return True

    def _run_stage_command(text: str) -> bool:
        cmd, args = _split_slash(text)
        alias = {
            "sr": "ssot-rtl",
            "sfm": "ssot-fl-model",
            "seg": "ssot-equiv-goals",
            "equiv-goals": "ssot-equiv-goals",
            "tb": "ssot-tb-cocotb",
            "stb": "ssot-tb",
            "stb-cocotb": "ssot-tb-cocotb",
            "stb-uvm": "ssot-tb-uvm",
            "stb-verilog": "ssot-tb-verilog",
            "ssot-tb-sv": "ssot-tb-verilog",
            "stb-sv": "ssot-tb-verilog",
            "s": "sim",
            "sd": "sim-debug",
            "cov": "coverage",
            "l": "lint",
            "audit": "goal-audit",
            "ga": "goal-audit",
        }.get(cmd, cmd)
        spec = _STAGE_RUNNERS.get(alias)
        if not spec:
            return False
        ip = args.split(None, 1)[0] if args else ""
        if not _valid_ip_name(ip):
            _emit_workflow_result(
                f"[{alias}] missing or invalid IP name\nusage: /{alias} <ip_name>",
                alias,
            )
            return True
        ssot_path = PROJECT_ROOT / ip / "yaml" / f"{ip}.ssot.yaml"
        if not ssot_path.is_file():
            _emit_workflow_result(
                f"[{alias}] blocked: SSOT not found at {ip}/yaml/{ip}.ssot.yaml\n"
                f"Run /new-ip {ip}, approve {ip}, and /to-ssot {ip} first.",
                alias,
            )
            return True
        if alias == "signoff":
            session = f"{ip}/signoff"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)

            async def _emit_signoff_snapshot() -> None:
                try:
                    resp = await api_progress(scope=ip)
                    data = json.loads(resp.body.decode("utf-8"))
                    selected = data.get("selected") if isinstance(data, dict) else {}
                    signoff = selected.get("signoff") if isinstance(selected, dict) else {}
                    status = signoff.get("status") if isinstance(signoff, dict) else {}
                    blockers = signoff.get("blockers") if isinstance(signoff, dict) else []
                    progress = selected.get("progress") if isinstance(selected, dict) else {}
                    equivalence = progress.get("equivalence_goals") if isinstance(progress, dict) else {}
                    goal_audit = progress.get("goal_audit") if isinstance(progress, dict) else {}
                    lines = [
                        "[signoff] strict SSOT progress gate",
                        f"module: {ip}",
                        f"status: {status.get('signoff', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"equivalence: {status.get('equivalence_goals', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"goal_audit: {status.get('goal_audit', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"coverage: {status.get('coverage', 'unknown') if isinstance(status, dict) else 'unknown'}",
                        f"evidence: /api/progress?scope={ip}",
                    ]
                    if isinstance(equivalence, dict):
                        lines.append(
                            "equivalence_counts: "
                            f"{equivalence.get('passed', 0)}/{equivalence.get('total', 0)} pass, "
                            f"failed={equivalence.get('failed', 0)}, "
                            f"blocked={equivalence.get('blocked', 0)}, "
                            f"untested={equivalence.get('untested', 0)}"
                        )
                    if isinstance(goal_audit, dict):
                        lines.append(
                            "goal_audit_checks: "
                            f"{goal_audit.get('passed_checks', 0)}/{goal_audit.get('total_checks', 0)} pass, "
                            f"failed={goal_audit.get('failed_checks', 0)}"
                        )
                    if blockers:
                        lines.append("")
                        lines.append("blockers:")
                        for blocker in blockers[:12]:
                            lines.append(f"- {blocker}")
                    msg = "\n".join(lines)
                except Exception as exc:
                    msg = f"[signoff] failed to read ATLAS progress gate for {ip}: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim_debug", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)

            asyncio.create_task(_emit_signoff_snapshot())
            return True

        try:
            from src.workflow_stage_surface import is_common_stage, run_common_stage_surface
        except ModuleNotFoundError:  # pragma: no cover - direct script execution fallback
            from workflow_stage_surface import is_common_stage, run_common_stage_surface

        if is_common_stage(alias):
            template = str(spec.get("template") or alias)
            surface = run_common_stage_surface(
                project_root=PROJECT_ROOT,
                source_root=SOURCE_ROOT,
                alias=alias,
                ip=ip,
                template=template,
            )
            if not surface.handled:
                return False
            session = surface.session
            workflow = surface.workflow
            msg = surface.message
            engine_alias = surface.alias
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history(workflow, "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, engine_alias)

            if surface.rtl_blocked:
                _start_rtl_blocker_qna(ip, reason="automatic /ssot-rtl preflight", interactive=False)
                return True
            for prompt in surface.queue_prompts:
                bridge.queue_prompt(prompt)
            if surface.queue_prompts:
                bridge.emit("agent_state", running=True)
                return True
            if surface.sim_human_gate_doc is not None:
                opened_human_gate = _start_sim_human_gate_qna(
                    ip,
                    surface.sim_human_gate_doc,
                    reason="automatic /sim-debug",
                )
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history(workflow, "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    bridge.emit("tool_result", text="```\n" + note + "\n```", tool=engine_alias, truncated=False)
                    bridge.emit("slash_output", text="```\n" + note + "\n```")
                    bridge.emit("flush")
                    return True
            bridge.emit("agent_state", running=False)
            return True
        if alias == "sim":
            session = f"{ip}/sim"
            script = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "sim.sh"
            validator = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "check_tb_sim_evidence.sh"
            coverage_script = SOURCE_ROOT / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"
            runner_candidates = [
                PROJECT_ROOT / ip / "tb" / "cocotb" / "test_runner.py",
                PROJECT_ROOT / ip / "tb" / "cocotb" / "run_tests.py",
                PROJECT_ROOT / ip / "tb" / "test_runner.py",
                PROJECT_ROOT / ip / "tb" / "run_tests.py",
                PROJECT_ROOT / ip / "sim" / f"test_{ip}.py",
            ]
            runner = next((p for p in runner_candidates if p.is_file()), None)
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            if runner is None:
                msg = (
                    f"[sim] blocked: no executable TB runner found for {ip}\n"
                    "expected one of:\n"
                    f"- {ip}/tb/cocotb/test_runner.py\n"
                    f"- {ip}/tb/cocotb/run_tests.py\n"
                    f"- {ip}/tb/test_runner.py\n"
                    f"- {ip}/tb/run_tests.py\n"
                    "Run /tb <ip> first."
                )
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True
            try:
                import subprocess

                sim_run = subprocess.run(
                    ["bash", str(script), runner.relative_to(PROJECT_ROOT).as_posix()],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    capture_output=True,
                    timeout=180,
                )
                validate_run = subprocess.run(
                    ["bash", str(validator), ip],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    capture_output=True,
                    timeout=180,
                )
                coverage_run = subprocess.CompletedProcess(
                    args=[sys.executable, str(coverage_script), str(PROJECT_ROOT / ip)],
                    returncode=0,
                    stdout="",
                    stderr="",
                )
                if sim_run.returncode == 0 and validate_run.returncode == 0:
                    coverage_run = subprocess.run(
                        [sys.executable, str(coverage_script), str(PROJECT_ROOT / ip)],
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        capture_output=True,
                        timeout=90,
                    )
            except Exception as exc:
                msg = f"[sim] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_workflow_history("sim", "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                return True

            status_word = "PASS" if sim_run.returncode == 0 and validate_run.returncode == 0 and coverage_run.returncode == 0 else "FAIL"
            parts = [
                f"[sim] {status_word}",
                f"script: {script}",
                f"validator: {validator}",
                f"coverage: {coverage_script}",
                f"module: {ip}",
                f"runner: {runner.relative_to(PROJECT_ROOT)}",
                f"sim exit: {sim_run.returncode}",
            ]
            if sim_run.stdout.strip():
                parts += ["", "sim stdout:", sim_run.stdout.strip()]
            if sim_run.stderr.strip():
                parts += ["", "sim stderr:", sim_run.stderr.strip()]
            parts += ["", f"validator exit: {validate_run.returncode}"]
            if validate_run.stdout.strip():
                parts += ["", "validator stdout:", validate_run.stdout.strip()]
            if validate_run.stderr.strip():
                parts += ["", "validator stderr:", validate_run.stderr.strip()]
            parts += ["", f"coverage exit: {coverage_run.returncode}"]
            if coverage_run.stdout.strip():
                parts += ["", "coverage stdout:", coverage_run.stdout.strip()]
            if coverage_run.stderr.strip():
                parts += ["", "coverage stderr:", coverage_run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/results.xml or {ip}/tb/cocotb/results.xml",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/cov/coverage.json",
                f"- {ip}/sim/sim_report.txt",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            return True
        if alias == "ssot-rtl":
            session = f"{ip}/rtl-gen"
            script = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "ssot_to_rtl.py"
            top = ip
            try:
                import yaml as _yaml  # type: ignore
                ssot_doc = _yaml.safe_load(ssot_path.read_text(encoding="utf-8", errors="replace")) or {}
                top_doc = ssot_doc.get("top_module") if isinstance(ssot_doc, dict) else {}
                if isinstance(top_doc, dict) and top_doc.get("name"):
                    top = str(top_doc.get("name"))
                elif isinstance(top_doc, str) and top_doc.strip():
                    top = top_doc.strip()
            except Exception:
                top = ip

            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _clip(s: str, limit: int = 12000) -> str:
                if len(s) <= limit:
                    return s
                return s[:limit] + f"\n... <truncated {len(s) - limit} chars>"

            def _run_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": _clip((proc.stdout or "").strip()),
                        "stderr": _clip((proc.stderr or "").strip()),
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "command": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tool("rtl_generate", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)])
            compile_rc: int | None = None
            lint_rc: int | None = None
            if gen_rc == 0:
                compile_script = SOURCE_ROOT / "workflow" / "rtl-gen" / "scripts" / "rtl_compile_report.py"
                lint_script = SOURCE_ROOT / "workflow" / "lint" / "scripts" / "dut_lint_report.py"
                compile_rc = _run_tool(
                    "dut_compile",
                    [
                        sys.executable,
                        str(compile_script),
                        ip,
                        "--top",
                        top,
                        "--project-root",
                        str(PROJECT_ROOT),
                    ],
                )
                lint_rc = _run_tool("dut_lint", [sys.executable, str(lint_script), ip, "--top", top])

            blocked_path = PROJECT_ROOT / ip / "rtl" / "rtl_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    blocked_doc = json.loads(blocked_path.read_text(encoding="utf-8"))
                except Exception as exc:
                    blocked_doc = {"reason": f"rtl_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc:
                headline = "[SSOT QUESTION] rtl-gen BLOCKED"
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                headline = "[RTL RESULT] PASS - generated RTL and DUT-only compile/lint evidence"
            elif gen_rc == 0:
                headline = "[RTL RESULT] FAIL - generated RTL needs rtl-gen repair"
            else:
                headline = "[RTL BLOCKED] rtl-gen failed before producing approved evidence"

            parts = [
                headline,
                f"module: {ip}",
                f"top: {top}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT decision required'}",
                    f"evidence: {ip}/rtl/rtl_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'answer SSOT questions and rerun /ssot-rtl'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts.append("")
            parts.append("runs:")
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['command']}")
                if run.get("stdout"):
                    parts.append("  stdout:")
                    parts.append(str(run["stdout"]))
                if run.get("stderr"):
                    parts.append("  stderr:")
                    parts.append(str(run["stderr"]))
            parts += [
                "",
                "artifacts:",
                f"- {ip}/yaml/{ip}.ssot.yaml",
                f"- {ip}/list/{ip}.f",
                f"- {ip}/rtl/rtl_compile.json",
                f"- {ip}/lint/dut_lint.json",
                f"- {ip}/rtl/rtl_blocked.json (only when SSOT decision is required)",
            ]
            if blocked_doc:
                parts.append("")
                parts.append("next: ATLAS opened an SSOT decision Q&A card for the RTL blocker.")
            elif gen_rc == 0 and compile_rc == 0 and lint_rc == 0:
                parts += [
                    "",
                    "next: run /tb, /sim, /sim-debug, and /goal-audit to prove FL-vs-RTL behavior.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued rtl-gen repair with compile/lint diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("rtl-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            if blocked_doc:
                _start_rtl_blocker_qna(ip, reason="automatic /ssot-rtl preflight", interactive=False)
            elif gen_rc == 0 and (compile_rc != 0 or lint_rc != 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or alias)
                bridge.queue_prompt("/mode normal")
                bridge.queue_prompt(f"/wf {workflow}")
                bridge.queue_prompt("/clear")
                bridge.queue_prompt(f"/todo template {template} {ip}")
                bridge.queue_prompt(
                    f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
                    "The SSOT-driven RTL generator produced artifacts but compile/lint did not approve them. "
                    "Repair only the generated RTL against function_model, cycle_model, interfaces, "
                    "error_handling, and test_requirements. Then run the canonical DUT-only compile and "
                    "lint commands, repair diagnostics, and report exact artifact evidence. If new behavior "
                    "is still ambiguous, emit a precise "
                    "[SSOT QUESTION] and stop."
                )
            bridge.emit("agent_state", running=False)
            return True
        if alias == "ssot-equiv-goals":
            session = f"{ip}/fl-model-gen"
            fl_script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_equivalence_goals.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _run_local(label: str, cmdline: list[str], timeout_s: int = 60) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        cmdline,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(cmdline),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            fl_rc = _run_local("emit_fl_model", [sys.executable, str(fl_script), ip, "--root", str(PROJECT_ROOT)])
            eq_rc = _run_local("emit_equivalence_goals", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)]) if fl_rc == 0 else 999
            goals_path = PROJECT_ROOT / ip / "verify" / "equivalence_goals.json"
            goal_summary = ""
            if goals_path.is_file():
                try:
                    gdoc = json.loads(goals_path.read_text(encoding="utf-8"))
                    summary = gdoc.get("summary") if isinstance(gdoc, dict) else {}
                    if isinstance(summary, dict):
                        goal_summary = (
                            f"total={summary.get('total', 0)} "
                            f"required={summary.get('required', 0)} "
                            f"blocked={summary.get('blocked', 0)}"
                        )
                except Exception:
                    goal_summary = "unparseable equivalence_goals.json"
            headline = (
                "[ssot-equiv-goals] PASS"
                if eq_rc == 0 else
                "[ssot-equiv-goals] BLOCKED"
            )
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"goals: {goal_summary or '(not generated)'}",
                "",
                "runs:",
            ]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/verify/equivalence_goals.json",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            if eq_rc != 0:
                parts.append("")
                parts.append("next: inspect blocked goals and answer/repair SSOT behavior before TB signoff")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        if alias in {"ssot-tb", "ssot-tb-cocotb"}:
            canonical_alias = "ssot-tb-cocotb"
            session = f"{ip}/tb-gen"
            script = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "emit_goal_scoreboard_cocotb.py"
            validator = SOURCE_ROOT / "workflow" / "tb-gen" / "scripts" / "check_pyuvm_structure.sh"
            scoreboard = SOURCE_ROOT / "workflow" / "tb-gen" / "runtime" / "equivalence_scoreboard.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            runs: list[dict[str, Any]] = []

            def _run_tb_tool(label: str, command: list[str], timeout_s: int = 180) -> int:
                try:
                    import subprocess

                    proc = subprocess.run(
                        command,
                        cwd=str(PROJECT_ROOT),
                        text=True,
                        capture_output=True,
                        timeout=timeout_s,
                    )
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": proc.returncode,
                        "stdout": (proc.stdout or "").strip()[:12000],
                        "stderr": (proc.stderr or "").strip()[:12000],
                    })
                    return int(proc.returncode)
                except Exception as exc:
                    runs.append({
                        "label": label,
                        "cmd": " ".join(command),
                        "returncode": 999,
                        "stdout": "",
                        "stderr": str(exc),
                    })
                    return 999

            gen_rc = _run_tb_tool("emit_goal_scoreboard_cocotb", [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)])
            structure_rc: int | None = None
            self_check_rc: int | None = None
            if gen_rc == 0:
                structure_rc = _run_tb_tool("check_pyuvm_structure", ["bash", str(validator), ip])
                self_check_rc = _run_tb_tool(
                    "equivalence_scoreboard_self_check",
                    [sys.executable, str(scoreboard), ip, "--root", str(PROJECT_ROOT), "--self-check"],
                )

            blocked_path = PROJECT_ROOT / ip / "tb" / "cocotb" / "tb_blocked.json"
            blocked_doc: dict[str, Any] = {}
            if blocked_path.is_file():
                try:
                    loaded = json.loads(blocked_path.read_text(encoding="utf-8"))
                    blocked_doc = loaded if isinstance(loaded, dict) else {}
                except Exception as exc:
                    blocked_doc = {"reason": f"tb_blocked.json parse failed: {exc}", "questions": []}

            if blocked_doc or gen_rc == 2:
                headline = "[ssot-tb-cocotb] BLOCKED - SSOT/RTL contract needs repair"
            elif gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                headline = "[ssot-tb-cocotb] PASS - generated goal-driven pyuvm/cocotb scoreboard"
            elif gen_rc == 0:
                headline = "[ssot-tb-cocotb] FAIL - generated TB needs tb-gen repair"
            else:
                headline = "[ssot-tb-cocotb] FAIL - generator did not produce approved TB artifacts"

            parts = [
                headline,
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"generator: {script}",
                f"validator: {validator}",
            ]
            if blocked_doc:
                parts += [
                    f"blocker: {blocked_doc.get('reason') or 'SSOT/RTL decision required'}",
                    f"evidence: {ip}/tb/cocotb/tb_blocked.json",
                    f"next: {blocked_doc.get('next_action') or 'repair SSOT/RTL contract and rerun /tb'}",
                ]
                questions = blocked_doc.get("questions") if isinstance(blocked_doc.get("questions"), list) else []
                if questions:
                    parts.append("")
                    parts.append("questions:")
                    for q in questions:
                        if not isinstance(q, dict):
                            continue
                        parts.append(f"- {q.get('id')}: {q.get('decision_needed')}")
                        if q.get("recommended_default"):
                            parts.append(f"  recommended: {q.get('recommended_default')}")
            parts += ["", "runs:"]
            for run in runs:
                parts.append(f"- {run['label']}: exit {run['returncode']}")
                parts.append(f"  cmd: {run['cmd']}")
                if run["stdout"]:
                    parts.append("  stdout:")
                    parts.append(run["stdout"])
                if run["stderr"]:
                    parts.append("  stderr:")
                    parts.append(run["stderr"])
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/tb/cocotb/test_{ip}.py",
                f"- {ip}/tb/cocotb/test_runner.py",
                f"- {ip}/tb/cocotb/tb_manifest.json",
                f"- {ip}/tb/cocotb/tb_generation.json",
                f"- {ip}/sim/scoreboard_events.jsonl after /sim",
                f"- {ip}/cov/coverage.json after /sim",
            ]
            if gen_rc == 0 and structure_rc == 0 and self_check_rc == 0:
                parts += [
                    "",
                    "next: run /sim, /sim-debug, and /goal-audit to collect FL-vs-RTL evidence.",
                ]
            elif gen_rc == 0:
                parts += [
                    "",
                    "next: queued tb-gen repair with structure/self-check diagnostics as evidence.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("tb-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, canonical_alias)
            if gen_rc == 0 and not (structure_rc == 0 and self_check_rc == 0):
                workflow = str(spec["workflow"])
                template = str(spec.get("template") or canonical_alias)
                bridge.queue_prompt("/mode normal")
                bridge.queue_prompt(f"/wf {workflow}")
                bridge.queue_prompt("/clear")
                bridge.queue_prompt(f"/todo template {template} {ip}")
                bridge.queue_prompt(
                    f"Repair generated pyuvm/cocotb TB for {ip} using SSOT, FunctionalModel, "
                    "equivalence_goals.json, rtl_contract.json, and the validator output below. "
                    "Do not use fixed IP templates. Keep the TB goal-driven, instantiate "
                    "EquivalenceScoreboard, preserve all required scoreboard row fields, and rerun "
                    f"`bash {validator} {ip}` plus the scoreboard self-check before reporting DONE.\n\n"
                    "ATLAS direct-generation evidence:\n```text\n"
                    f"{msg}\n"
                    "```"
                )
                bridge.emit("agent_state", running=True)
            else:
                bridge.emit("agent_state", running=False)
            return True
        if alias == "sim-debug":
            session = f"{ip}/sim_debug"
            script = SOURCE_ROOT / "workflow" / "sim_debug" / "scripts" / "compare_fl_rtl_results.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[sim-debug] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            compare_path = PROJECT_ROOT / ip / "sim" / "fl_rtl_compare.json"
            classify_path = PROJECT_ROOT / ip / "sim" / "mismatch_classification.json"
            summary_line = ""
            if compare_path.is_file():
                try:
                    cdoc = json.loads(compare_path.read_text(encoding="utf-8"))
                    summary = cdoc.get("summary") if isinstance(cdoc, dict) else {}
                    if isinstance(summary, dict):
                        summary_line = (
                            f"status={cdoc.get('status')} total={summary.get('total', 0)} "
                            f"checked={summary.get('goals_checked', 0)} passed={summary.get('goals_passed', 0)} "
                            f"failed={summary.get('goals_failed', 0)} blocked={summary.get('goals_blocked', 0)} "
                            f"untested={summary.get('goals_untested', 0)}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_compare.json"
            parts = [
                "[sim-debug] FL-vs-RTL compare",
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/sim/fl_rtl_compare.json",
                f"- {ip}/sim/mismatch_classification.json",
                f"- {ip}/sim/scoreboard_events.jsonl",
                f"- {ip}/verify/equivalence_goals.json",
            ]
            if run.returncode != 0 and classify_path.is_file():
                parts.append("")
                parts.append("next: repair classified owner or answer human-gate questions from mismatch_classification.json")
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            opened_human_gate = False
            if classify_path.is_file():
                try:
                    loaded = json.loads(classify_path.read_text(encoding="utf-8"))
                    classify_doc = loaded if isinstance(loaded, dict) else {}
                except Exception:
                    classify_doc = {}
                opened_human_gate = _start_sim_human_gate_qna(ip, classify_doc, reason="automatic /sim-debug")
                if opened_human_gate:
                    note = f"[sim-debug] opened ATLAS human-gate question(s) from {ip}/sim/mismatch_classification.json"
                    _append_session_message(session, "assistant", note)
                    _append_workflow_history("sim_debug", "assistant", note)
                    _append_active_history("assistant", "```\n" + note + "\n```")
                    bridge.emit("tool_result", text="```\n" + note + "\n```", tool=alias, truncated=False)
                    bridge.emit("slash_output", text="```\n" + note + "\n```")
                    bridge.emit("flush")
            if not opened_human_gate:
                bridge.emit("agent_state", running=False)
            return True
        if alias == "goal-audit":
            session = f"{ip}/goal-audit"
            script = SOURCE_ROOT / "workflow" / "sim_debug" / "scripts" / "audit_fl_rtl_equivalence_goal.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[goal-audit] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            audit_path = PROJECT_ROOT / ip / "sim" / "fl_rtl_goal_audit.json"
            summary_line = ""
            blockers: list[str] = []
            if audit_path.is_file():
                try:
                    audit_doc = json.loads(audit_path.read_text(encoding="utf-8"))
                    summary = audit_doc.get("summary") if isinstance(audit_doc, dict) else {}
                    if isinstance(summary, dict):
                        blockers = [str(x) for x in summary.get("blockers") or []]
                        summary_line = (
                            f"status={audit_doc.get('status')} "
                            f"passed={summary.get('passed_checks', 0)}/{summary.get('total_checks', 0)} "
                            f"blockers={', '.join(blockers) if blockers else 'none'}"
                        )
                except Exception:
                    summary_line = "unparseable fl_rtl_goal_audit.json"
            headline = "[goal-audit] PASS" if run.returncode == 0 else "[goal-audit] FAIL"
            parts = [
                headline,
                f"script: {script}",
                f"module: {ip}",
                f"exit: {run.returncode}",
                f"summary: {summary_line or '(not generated)'}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifact:",
                f"- {ip}/sim/fl_rtl_goal_audit.json",
            ]
            if blockers:
                parts += ["", "blockers:"]
                parts += [f"- {blocker}" for blocker in blockers[:12]]
            if run.returncode != 0:
                parts += [
                    "",
                    "next: inspect fl_rtl_goal_audit.json and rerun the owning ATLAS stage; do not bypass with a fixed IP template.",
                ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("sim_debug", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        if alias == "ssot-fl-model":
            session = f"{ip}/fl-model-gen"
            script = SOURCE_ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_fl_model.py"
            _append_session_message(session, "user", text)
            _append_active_history("user", text)
            bridge.emit("agent_state", running=True)
            try:
                import subprocess

                run = subprocess.run(
                    [sys.executable, str(script), ip, "--root", str(PROJECT_ROOT)],
                    cwd=str(PROJECT_ROOT),
                    text=True,
                    capture_output=True,
                    timeout=60,
                )
            except Exception as exc:
                msg = f"[ssot-fl-model] failed: {exc}"
                _append_session_message(session, "assistant", msg)
                _append_active_history("assistant", "```\n" + msg + "\n```")
                _emit_workflow_result(msg, alias)
                bridge.emit("agent_state", running=False)
                return True

            parts = [
                "[ssot-fl-model] generic SSOT-driven FL model stage",
                f"script: {script}",
                f"module: {ip}",
                f"source: {ip}/yaml/{ip}.ssot.yaml",
                f"exit: {run.returncode}",
            ]
            if run.stdout.strip():
                parts += ["", "stdout:", run.stdout.strip()]
            if run.stderr.strip():
                parts += ["", "stderr:", run.stderr.strip()]
            parts += [
                "",
                "expected artifacts:",
                f"- {ip}/model/functional_model.py",
                f"- {ip}/model/decomposition.json",
                f"- {ip}/model/fl_model_check.json",
                f"- {ip}/cov/fcov_plan.json",
            ]
            msg = "\n".join(parts)
            _append_session_message(session, "assistant", msg)
            _append_workflow_history("fl-model-gen", "assistant", msg)
            _append_active_history("assistant", "```\n" + msg + "\n```")
            _emit_workflow_result(msg, alias)
            bridge.emit("agent_state", running=False)
            return True
        workflow = str(spec["workflow"])
        template = str(spec.get("template") or alias)
        session = f"{ip}/{workflow}"
        _append_session_message(session, "user", text)
        queued = (
            f"[{alias}] queued through workflow agent\n"
            f"workflow: {workflow}\n"
            f"template: {template}\n"
            f"module: {ip}\n"
            f"source: {ip}/yaml/{ip}.ssot.yaml\n"
            f"expected artifacts: {ip}/{spec['artifact_hint']}"
        )
        _append_session_message(session, "assistant", "```\n" + queued + "\n```")
        _append_active_history("user", text)
        _append_active_history("assistant", "```\n" + queued + "\n```")
        bridge.queue_prompt("/mode normal")
        bridge.queue_prompt(f"/wf {workflow}")
        # Per-IP stage runs must not inherit stale workflow-level chat/todo
        # context from a previous IP. The concrete SSOT path and rerun prompt
        # below re-establish the only context the worker should use.
        bridge.queue_prompt("/clear")
        bridge.queue_prompt(f"/todo template {template} {ip}")
        bridge.queue_prompt(
            f"Execute {alias} for {ip} from {ip}/yaml/{ip}.ssot.yaml. "
            "Use the workflow todo detail/criteria. Do not use fixed IP templates; "
            "derive implementation from SSOT and verify with real commands. "
            "After reading the SSOT, keep the ledger bounded and move to "
            "write_file/replace_in_file/run_command; do not loop on architecture "
            "debate before producing artifacts. Do not publish the ledger as a long "
            "chat answer; if work remains, the next response must start with an "
            "Action line. Use small action chunks: one file or one validation command "
            "per response, prefer dependency/leaf files before the top wrapper, and "
            "split any file that would exceed about 180 lines into replace_in_file "
            "or replace_lines follow-up actions."
        )
        bridge.emit("agent_state", running=True)
        _emit_workflow_result(queued, alias)
        bridge.emit("agent_state", running=True)
        return True

    def _resolve_worker_url(workflow: str) -> str:
        """Same precedence as core.delegate_runner.HTTPWorkerDelegate."""
        if workflow:
            key = "WORKER_URL_" + workflow.upper().replace("-", "_")
            url = os.environ.get(key)
            if url:
                return url
        return os.environ.get("WORKER_URL_DEFAULT", "http://localhost:8001")

    def _default_workflow_prompt(workflow: str, ip: str) -> str:
        prompt_for = {
            "architect": f"review and update the SoC architecture contract for {ip or 'the whole SoC'}; emit handoff notes for ssot-gen",
            "ssot-gen": f"refresh SSOT for {ip} from the architect handoff and current SoC context",
            "rtl-gen": f"regenerate RTL for {ip} from {ip}/yaml/{ip}.ssot.yaml",
            "lint": f"lint {ip}/rtl/*.sv and fix root-cause errors and warnings",
            "tb-gen": f"generate or update the testbench for {ip}",
            "sim": f"run simulation for {ip} and report pass/fail counts",
            "syn": f"synthesise {ip} and emit gate netlist plus area/timing summary",
            "dft": f"run DFT checks or scan-insertion preparation for {ip}",
            "sta": f"run pre-route STA for {ip} using the synthesized netlist and SDC",
            "pnr": f"run PnR for {ip}, producing routed DEF/netlist/SPEF reports",
            "sta-post": f"run post-route STA for {ip} using routed netlist and SPEF",
        }
        return prompt_for.get(workflow, f"run {workflow}" + (f" on {ip}" if ip else ""))

    def _default_todo_template_for_job(workflow: str, stage_id: str, ip: str) -> str:
        if ip and (workflow == "rtl-gen" or stage_id == "rtl"):
            return "ssot-rtl"
        return ""

    def _dispatch_job_to_worker(job: dict[str, Any]) -> None:
        try:
            import urllib.request as _u
            body = {
                "task": job["prompt"],
                "workflow": job["workflow"],
                "session": job.get("session", ""),
                "model": job.get("model", ""),
                "context": job["prompt"].split("\n\n", 1)[0],
                "sync": False,
            }
            if job.get("template"):
                body["template"] = job["template"]
            if job.get("ip"):
                body["ip"] = job["ip"]
            payload = json.dumps(body).encode("utf-8")
            req = _u.Request(
                f"{job['worker'].rstrip('/')}/run",
                data=payload, method="POST",
                headers={"Content-Type": "application/json"},
            )
            with _u.urlopen(req, timeout=10) as resp:
                resp_data = json.loads(resp.read().decode("utf-8"))
            run_id = resp_data.get("run_id", "")
            if not run_id:
                raise RuntimeError(f"worker did not return run_id: {resp_data}")
            with _jobs_lock:
                live = _jobs.get(job["job_id"], job)
                live["run_id"] = run_id
                live["status"] = "running"
                live["started_at"] = time.time()
                live["error"] = ""
        except Exception as e:
            with _jobs_lock:
                live = _jobs.get(job["job_id"], job)
                live["status"] = "error"
                live["error"] = f"worker dispatch failed at {job.get('worker')}: {e}"
                live["finished_at"] = time.time()

    def _make_job_record(
        *, workflow: str, ip: str, prompt: str, model: str = "",
        session_name: str = "", stage_id: str = "", pipeline_id: str = "",
        pipeline_index: int = 0, depends_on: str = "",
        worker_override: str = "", auto_start: bool = True, template: str = "",
    ) -> dict[str, Any]:
        import uuid
        stage_id = stage_id or (_PIPELINE_BY_WORKFLOW.get(workflow, {}).get("id") or workflow)
        template = template or _default_todo_template_for_job(workflow, stage_id, ip)
        session_name = normalize_session_name(session_name or (f"{ip}/{workflow}" if ip else workflow))
        if not session_name:
            raise ValueError("invalid session namespace")
        scope_path = str((PROJECT_ROOT / ip).resolve()) if ip else str(PROJECT_ROOT)
        try:
            rel_scope = str(Path(scope_path).relative_to(PROJECT_ROOT))
        except Exception:
            rel_scope = ip or "."
        session_dir = PROJECT_ROOT / ".session" / session_name
        try:
            session_dir.mkdir(parents=True, exist_ok=True)
        except OSError:
            pass
        worker_url = worker_override or _resolve_worker_url(workflow)
        boundary = (
            f"[ATLAS ARCHITECT WORKFLOW CONTEXT]\n"
            f"- ip: {ip or '(soc)'}\n"
            f"- workflow: {workflow}\n"
            f"- stage_id: {stage_id or workflow}\n"
            f"- pipeline_id: {pipeline_id or '(single-job)'}\n"
            f"- session_namespace: .session/{session_name}\n"
            f"- scope_path: {rel_scope}\n"
            f"- write_boundary: only modify files under {rel_scope}/, "
            f"except workflow-owned status/session files under .session/{session_name}/. "
            f"Do not edit other IP directories or unrelated workflows.\n"
            f"- parallelism: assume other IP/workflow jobs may be running; never revert or overwrite their files.\n\n"
        )
        job: dict[str, Any] = {
            "job_id": uuid.uuid4().hex[:12],
            "run_id": "",
            "worker": worker_url,
            "workflow": workflow,
            "stage_id": stage_id,
            "template": template,
            "ip": ip,
            "model": model,
            "session": session_name,
            "session_dir": session_dir.relative_to(PROJECT_ROOT).as_posix(),
            "scope_path": rel_scope,
            "worker_command": f"python src/main.py --serve --port {worker_url.rsplit(':', 1)[-1]} --worker-name {workflow} --session {session_name}",
            "prompt": boundary + (prompt or _default_workflow_prompt(workflow, ip)),
            "started_at": time.time() if auto_start else 0.0,
            "status": "pending" if auto_start else "queued",
            "iterations": 0,
            "files_modified": [],
            "result_summary": "",
            "error": "",
            "pipeline_id": pipeline_id,
            "pipeline_index": pipeline_index,
            "depends_on": depends_on,
            "_last_polled": 0.0,
        }
        with _jobs_lock:
            _jobs[job["job_id"]] = job
        if auto_start:
            _dispatch_job_to_worker(job)
        return job

    def _advance_pipeline_from(job: dict[str, Any]) -> None:
        pipeline_id = job.get("pipeline_id") or ""
        if not pipeline_id:
            return
        if job.get("status") in ("error", "cancelled"):
            with _jobs_lock:
                for queued in _jobs.values():
                    if queued.get("pipeline_id") == pipeline_id and queued.get("status") == "queued":
                        queued["status"] = "blocked"
                        queued["error"] = f"blocked by {job.get('workflow')} {job.get('status')}"
                        queued["finished_at"] = time.time()
            return
        if job.get("status") != "completed":
            return
        next_job = None
        with _jobs_lock:
            candidates = [j for j in _jobs.values()
                          if j.get("pipeline_id") == pipeline_id and j.get("status") == "queued"]
            candidates.sort(key=lambda j: j.get("pipeline_index", 0))
            if candidates and candidates[0].get("depends_on") == job.get("job_id"):
                next_job = candidates[0]
                next_job["status"] = "pending"
        if next_job:
            _dispatch_job_to_worker(next_job)

    def _public_job(job: dict[str, Any]) -> dict[str, Any]:
        return {k: v for k, v in job.items() if not k.startswith("_")}

    def _job_artifact_recovery(job: dict[str, Any]) -> tuple[bool, str]:
        """Recover UI job state when an HTTP worker forgot an old run_id.

        Worker runs are in-memory, while Architect state is filesystem-backed.
        If a worker restarts or drops a run, /status/{run_id} returns 404 even
        though the stage may have already produced valid artifacts. Use the same
        coarse filesystem contract as /api/soc so the web UI does not leave
        completed work blinking as "running" forever.
        """
        ip = str(job.get("ip") or "").strip()
        if not ip or ".." in ip or "/" in ip:
            return False, ""
        ip_dir = PROJECT_ROOT / ip
        if not ip_dir.is_dir():
            return False, ""
        stage = str(job.get("stage_id") or job.get("workflow") or "").strip()
        workflow = str(job.get("workflow") or "").strip()
        if stage == "ssot" or workflow == "ssot-gen":
            ok = (ip_dir / "yaml" / f"{ip}.ssot.yaml").is_file()
            return ok, f"recovered from artifact: {ip}/yaml/{ip}.ssot.yaml"
        if stage == "rtl" or workflow == "rtl-gen":
            filelist = ip_dir / "list" / f"{ip}.f"
            rtl_dir = ip_dir / "rtl"
            rtl_files = list(rtl_dir.glob("*.sv")) + list(rtl_dir.glob("*.v")) if rtl_dir.is_dir() else []
            return bool(filelist.is_file() and rtl_files), f"recovered from artifact: {ip}/list/{ip}.f"
        if stage == "tb" or workflow == "tb-gen":
            tb_dir = ip_dir / "tb"
            if not tb_dir.is_dir():
                return False, ""
            artifacts = (
                list(tb_dir.rglob("*.py"))
                + list(tb_dir.rglob("*.sv"))
                + list(tb_dir.rglob("*.v"))
            )
            return bool(artifacts), f"recovered from artifact: {ip}/tb"
        if stage == "sim-debug" or workflow == "sim_debug":
            sim_dir = ip_dir / "sim"
            cov_dir = ip_dir / "cov"
            artifacts = []
            if sim_dir.is_dir():
                artifacts.extend(list(sim_dir.rglob("*.vcd")))
                artifacts.extend(list(sim_dir.rglob("coverage_report.*")))
            if cov_dir.is_dir():
                artifacts.extend(list(cov_dir.rglob("coverage.json")))
                artifacts.extend(list(cov_dir.rglob("toggle.json")))
            return bool(artifacts), f"recovered from artifact: {ip}/sim + {ip}/cov"
        return False, ""

    @app.post("/api/job/dispatch")
    async def api_job_dispatch(request: Request):
        """Dispatch a workflow onto an IP via an HTTP worker.

        Body: `{workflow: 'rtl-gen', ip: 'counter', prompt?: '...',
                model?: '...', session?: 'counter/rtl-gen',
                worker?: 'http://127.0.0.1:8001'}`

        Defaults the prompt to a workflow-specific template so the user
        can just click the block menu without typing. Returns
        `{job_id, run_id, worker, status: 'queued'}` immediately; the
        frontend polls /api/jobs to track progress.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        workflow = (body.get("workflow") or "").strip()
        ip       = (body.get("ip") or "").strip()
        prompt   = (body.get("prompt") or "").strip()
        model    = (body.get("model") or "").strip()
        template = (body.get("template") or "").strip()
        session_raw = (body.get("session") or "").strip()
        session_name = normalize_session_name(session_raw)
        worker_override = (body.get("worker") or "").strip()
        if not workflow:
            return JSONResponse({"error": "missing 'workflow'"}, status_code=400)
        if not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
            return JSONResponse({"error": f"invalid workflow {workflow!r}"}, status_code=400)
        if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
            return JSONResponse({"error": f"invalid template {template!r}"}, status_code=400)
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
            return JSONResponse({"error": f"invalid model {model!r}"}, status_code=400)
        if session_raw and not session_name:
            return JSONResponse({"error": f"invalid session {session_raw!r}"}, status_code=400)
        if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
            return JSONResponse({"error": f"invalid worker {worker_override!r}"}, status_code=400)

        stage_id = (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
        job = _make_job_record(
            workflow=workflow, ip=ip, prompt=prompt, model=model,
            session_name=session_name, stage_id=stage_id,
            worker_override=worker_override, auto_start=True, template=template,
        )
        if job.get("status") == "error":
            return JSONResponse({"error": job.get("error"), "worker": job.get("worker")}, status_code=502)
        return JSONResponse({
            "ok": True,
            "job_id": job["job_id"],
            "run_id": job["run_id"],
            "worker": job["worker"],
            "session": job["session"],
            "session_dir": job["session_dir"],
            "scope_path": job["scope_path"],
            "model": model,
            "worker_command": job["worker_command"],
            "status": job["status"],
        })

    @app.post("/api/jobs/dispatch_many")
    async def api_jobs_dispatch_many(request: Request):
        """Dispatch multiple independent jobs in parallel.

        Body:
          `{jobs: [{workflow, ip, prompt?, model?, session?, worker?}, ...]}`

        This is the API shape the Architect/orchestrator should use for
        "run ssot/rtl on these IPs with different models" requests.  Each job
        still keeps its own `.session/<ip>/<workflow>` namespace and write
        boundary; the only shared object is this top-level tracker.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        items = body.get("jobs") if isinstance(body, dict) else None
        if not isinstance(items, list) or not items:
            return JSONResponse({"error": "expected non-empty jobs list"}, status_code=400)
        if len(items) > 32:
            return JSONResponse({"error": "too many jobs; max 32"}, status_code=400)

        created = []
        errors = []
        for idx, item in enumerate(items):
            if not isinstance(item, dict):
                errors.append({"index": idx, "error": "job must be an object"})
                continue
            workflow = (item.get("workflow") or "").strip()
            ip = (item.get("ip") or "").strip()
            prompt = (item.get("prompt") or "").strip()
            model = (item.get("model") or "").strip()
            template = (item.get("template") or "").strip()
            session_raw = (item.get("session") or "").strip()
            session_name = normalize_session_name(session_raw)
            worker_override = (item.get("worker") or "").strip()

            if not workflow or not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", workflow):
                errors.append({"index": idx, "error": f"invalid workflow {workflow!r}"})
                continue
            if template and not re.match(r"^[A-Za-z][A-Za-z0-9_\-]*$", template):
                errors.append({"index": idx, "error": f"invalid template {template!r}"})
                continue
            if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
                errors.append({"index": idx, "error": f"invalid ip {ip!r}"})
                continue
            if model and not re.match(r"^[A-Za-z0-9_.:/@+\-]+$", model):
                errors.append({"index": idx, "error": f"invalid model {model!r}"})
                continue
            if session_raw and not session_name:
                errors.append({"index": idx, "error": f"invalid session {session_raw!r}"})
                continue
            if worker_override and not re.match(r"^https?://[A-Za-z0-9_.:\-/]+$", worker_override):
                errors.append({"index": idx, "error": f"invalid worker {worker_override!r}"})
                continue

            stage_id = (_PIPELINE_BY_WORKFLOW.get(workflow) or {}).get("id", workflow)
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=prompt, model=model,
                session_name=session_name, stage_id=stage_id,
                worker_override=worker_override, auto_start=True, template=template,
            )
            created.append(_public_job(job))

        status = 207 if errors else 200
        return JSONResponse(
            {"ok": not errors, "jobs": created, "errors": errors, "count": len(created)},
            status_code=status,
        )

    @app.get("/api/pipeline/stages")
    async def api_pipeline_stages():
        return JSONResponse({"stages": _PIPELINE_STAGES})

    @app.post("/api/pipeline/dispatch")
    async def api_pipeline_dispatch(request: Request):
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected JSON object"}, status_code=400)
        ip = (body.get("ip") or "").strip()
        model = (body.get("model") or "").strip()
        user_prompt = (body.get("prompt") or "").strip()
        if ip and not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip):
            return JSONResponse({"error": f"invalid ip {ip!r}"}, status_code=400)
        requested = body.get("stages") or [s["id"] for s in _PIPELINE_STAGES]
        if not isinstance(requested, list) or not requested:
            return JSONResponse({"error": "stages must be a non-empty list"}, status_code=400)
        resolved = []
        for item in requested:
            key = str(item).strip()
            stage = _PIPELINE_BY_ID.get(key) or _PIPELINE_BY_WORKFLOW.get(key)
            if not stage:
                return JSONResponse({"error": f"unknown pipeline stage {key!r}"}, status_code=400)
            if not any(s["id"] == stage["id"] for s in resolved):
                resolved.append(stage)
        import uuid
        pipeline_id = uuid.uuid4().hex[:12]
        jobs = []
        previous_job_id = ""
        for idx, stage in enumerate(resolved):
            workflow = stage["workflow"]
            stage_prompt = _default_workflow_prompt(workflow, ip)
            if user_prompt:
                stage_prompt += f"\n\n[User pipeline goal]\n{user_prompt}"
            session = f"{ip or 'soc'}/pipeline/{pipeline_id}/{idx + 1:02d}-{workflow}"
            job = _make_job_record(
                workflow=workflow, ip=ip, prompt=stage_prompt, model=model,
                session_name=session, stage_id=stage["id"], pipeline_id=pipeline_id,
                pipeline_index=idx, depends_on=previous_job_id,
                auto_start=(idx == 0),
            )
            previous_job_id = job["job_id"]
            jobs.append(_public_job(job))
        return JSONResponse({
            "ok": True,
            "pipeline_id": pipeline_id,
            "ip": ip,
            "stages": resolved,
            "jobs": jobs,
        })

    @app.get("/api/jobs")
    async def api_jobs():
        """Aggregate job status across all dispatched workers.

        For each tracked job, poll the worker's /status/{run_id} (with a
        small 1.5s per-job cache to avoid hammering during a 2-second
        frontend poll cycle) and return the merged list. Sorted by
        started_at descending so the most-recent job is first.
        """
        out = []
        now = time.time()
        with _jobs_lock:
            snapshot = list(_jobs.values())
        for job in snapshot:
            if job["status"] in ("running",) and (now - job.get("_last_polled", 0)) > 1.5:
                # Poll worker for fresh state.
                try:
                    import urllib.request as _u
                    req = _u.Request(
                        f"{job['worker'].rstrip('/')}/status/{job['run_id']}",
                        method="GET",
                    )
                    with _u.urlopen(req, timeout=5) as resp:
                        s = json.loads(resp.read().decode("utf-8"))
                    job["_last_polled"] = now
                    job["status"] = s.get("status", job["status"])
                    if isinstance(s.get("iterations"), int):
                        job["iterations"] = s["iterations"]
                    if s.get("status") in ("completed", "error", "cancelled"):
                        # Fetch full result body once on completion.
                        try:
                            req2 = _u.Request(
                                f"{job['worker'].rstrip('/')}/result/{job['run_id']}",
                                method="GET",
                            )
                            with _u.urlopen(req2, timeout=5) as r2:
                                rr = json.loads(r2.read().decode("utf-8"))
                            job["files_modified"] = rr.get("files_modified") or []
                            job["result_summary"] = (rr.get("result") or "")[:600]
                            job["error"] = rr.get("error") or ""
                            job["finished_at"] = now
                            if rr.get("execution_time_ms"):
                                job["duration_ms"] = rr["execution_time_ms"]
                        except Exception:
                            pass
                        _advance_pipeline_from(job)
                except Exception as e:
                    recovered, detail = _job_artifact_recovery(job)
                    if recovered:
                        job["status"] = "completed"
                        job["error"] = ""
                        job["result_summary"] = detail
                        job["finished_at"] = now
                        _advance_pipeline_from(job)
                    else:
                        job["error"] = f"poll failed: {e}"
            if job.get("status") in ("completed", "error", "cancelled"):
                _advance_pipeline_from(job)
            out.append(_public_job(job))
        out.sort(key=lambda j: j.get("started_at", 0), reverse=True)
        return JSONResponse({"jobs": out, "count": len(out)})

    @app.get("/api/job/{job_id}/log")
    async def api_job_log(job_id: str, since: int = 0, tail: int = 0):
        """Proxy a worker run transcript into the Architect chat.

        The frontend knows Atlas job ids, not worker run ids. Keep that
        mapping server-side so users can click a job/status-grid pill and
        inspect the live ReAct transcript without leaving the Architect view.
        """
        with _jobs_lock:
            job = dict(_jobs.get(job_id) or {})
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)
        def _session_history_log():
            session = normalize_session_name(str(job.get("session") or ""))
            if not session:
                return None
            path = PROJECT_ROOT / ".session" / session / "conversation.json"
            if not path.is_file():
                return None
            try:
                messages = json.loads(path.read_text(encoding="utf-8", errors="replace"))
            except Exception:
                return None
            if isinstance(messages, dict):
                messages = messages.get("messages") or []
            if not isinstance(messages, list):
                return None
            entries = []
            for i, m in enumerate(messages[-120:]):
                if not isinstance(m, dict):
                    continue
                role = m.get("role") or ""
                content = str(m.get("content") or "")
                stripped = content.strip()
                if not stripped:
                    continue
                typ = "response"
                if role == "user":
                    if stripped.startswith("Observation:"):
                        typ = "observation"
                    elif stripped.startswith("[Context]"):
                        typ = "context"
                    else:
                        typ = "task"
                elif role == "assistant" and stripped.startswith("Action:"):
                    typ = "action"
                entries.append({
                    "index": i,
                    "type": typ,
                    "role": role,
                    "content": content,
                    "timestamp": m.get("timestamp") or job.get("finished_at") or job.get("started_at") or 0,
                    "source": "session",
                })
            if since > 0:
                entries = [e for e in entries if e["index"] >= since]
            if tail > 0:
                entries = entries[-tail:]
            return {
                "run_id": job.get("run_id") or "",
                "status": job.get("status") or "unknown",
                "total_entries": len(entries),
                "entries": entries,
                "source": "session",
                "session_path": path.relative_to(PROJECT_ROOT).as_posix(),
                "job": {k: v for k, v in job.items() if not k.startswith("_")},
            }

        try:
            import urllib.parse as _p
            import urllib.request as _u
            qs = _p.urlencode({k: v for k, v in {"since": since, "tail": tail}.items() if v})
            url = f"{job['worker'].rstrip('/')}/log/{job['run_id']}" + (f"?{qs}" if qs else "")
            req = _u.Request(url, method="GET")
            with _u.urlopen(req, timeout=5) as resp:
                data = json.loads(resp.read().decode("utf-8"))
        except Exception as e:
            fallback = _session_history_log()
            if fallback is not None:
                fallback["worker_log_error"] = str(e)
                return JSONResponse(fallback)
            return JSONResponse({"error": f"log fetch failed: {e}", "job": job}, status_code=502)
        data["job"] = {k: v for k, v in job.items() if not k.startswith("_")}
        return JSONResponse(data)

    @app.post("/api/job/{job_id}/cancel")
    async def api_job_cancel(job_id: str):
        with _jobs_lock:
            job = _jobs.get(job_id)
        if not job:
            return JSONResponse({"error": "job not found"}, status_code=404)
        if job["status"] != "running":
            return JSONResponse({"error": f"job already {job['status']}"}, status_code=400)
        try:
            import urllib.request as _u
            req = _u.Request(
                f"{job['worker'].rstrip('/')}/cancel/{job['run_id']}",
                method="POST",
            )
            with _u.urlopen(req, timeout=5) as resp:
                resp.read()
        except Exception as e:
            return JSONResponse({"error": f"cancel failed: {e}"}, status_code=502)
        with _jobs_lock:
            job["status"] = "cancelled"
        return JSONResponse({"ok": True})

    @app.post("/api/jobs/clear")
    async def api_jobs_clear():
        """Drop completed/cancelled/failed jobs from the tracker."""
        with _jobs_lock:
            for jid in list(_jobs.keys()):
                if _jobs[jid]["status"] != "running":
                    _jobs.pop(jid, None)
        return JSONResponse({"ok": True})

    @app.get("/api/catalog/models")
    async def api_catalog_models():
        """Return available IP models/templates discoverable in the project.

        Catalog models are reusable sources that can be instantiated.
        /api/soc remains the actual placed instance hierarchy.
        """
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"models": [], "count": 0,
                                 "error": "PyYAML not installed"})
        models = []
        seen = set()
        def _catalog_kind(name: str) -> str:
            n = (name or "").lower()
            if any(x in n for x in ["cpu", "core", "cortex", "riscv"]): return "cpu"
            if any(x in n for x in ["noc", "axi", "crossbar", "interconnect", "cci"]): return "bus"
            if any(x in n for x in ["ddr", "sram", "mem", "dram"]): return "mem"
            if any(x in n for x in ["pll", "adc", "dac", "phy"]): return "analog"
            return "periph"
        for p in sorted(PROJECT_ROOT.glob("*/yaml/*.ssot.yaml")):
            try:
                doc = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            except Exception:
                doc = {}
            if not isinstance(doc, dict):
                doc = {}
            ip_dir = p.parents[1]
            top = doc.get("top_module")
            name = top if isinstance(top, str) and top.strip() else ip_dir.name
            if name in seen:
                continue
            seen.add(name)
            ports = []
            for bi in (doc.get("busInterfaces") or []):
                if isinstance(bi, dict):
                    ports.append({
                        "name": bi.get("name"),
                        "proto": bi.get("proto"),
                        "role": bi.get("role"),
                        "side": bi.get("side"),
                    })
            models.append({
                "name": name,
                "id": ip_dir.name,
                "kind": _catalog_kind(name),
                "source": "project",
                "ssot_path": p.relative_to(PROJECT_ROOT).as_posix(),
                "ports": ports,
            })
        return JSONResponse({"models": models, "count": len(models)})

    @app.get("/api/workspace/tree")
    async def api_workspace_tree(depth: int = 2):
        """Return the real project directory hierarchy for Architect.

        This is separate from /api/catalog/models: catalog is reusable IP
        models; workspace tree is the on-disk project shape.
        """
        max_depth = max(1, min(int(depth or 2), 4))
        skip = {
            ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", "node_modules", ".venv", "venv", "vendor",
            ".session", ".rag", ".claude", ".omc", ".benchmark",
            ".benchmarks", ".common_ai_agent", ".session_debug",
        }
        ip_artifacts = {"yaml", "rtl", "tb", "sim", "lint", "syn", "sta", "sta-post", "pnr", "dft", "doc", "req", "list"}

        def _meta(p: Path) -> dict:
            child_names = set()
            try:
                child_names = {c.name for c in p.iterdir() if c.is_dir()}
            except OSError:
                pass
            ssot_count = 0
            try:
                ssot_count = len(list((p / "yaml").glob("*.ssot.yaml"))) if (p / "yaml").is_dir() else 0
            except OSError:
                ssot_count = 0
            artifacts = sorted(child_names & ip_artifacts)
            return {
                "is_ip": ssot_count > 0,
                "ssot_count": ssot_count,
                "artifacts": artifacts,
            }

        def _node(p: Path, level: int) -> dict | None:
            name = p.name or str(p)
            if name in skip or name.startswith("."):
                return None
            node = {
                "name": name,
                "path": p.relative_to(PROJECT_ROOT).as_posix(),
                "kind": "dir",
                **_meta(p),
                "children": [],
            }
            if level >= max_depth:
                return node
            try:
                dirs = sorted([c for c in p.iterdir() if c.is_dir()],
                              key=lambda c: (not ((c / "yaml").is_dir()), c.name.lower()))
            except OSError:
                dirs = []
            for child in dirs:
                child_node = _node(child, level + 1)
                if child_node is not None:
                    node["children"].append(child_node)
            return node

        root = {
            "name": PROJECT_ROOT.name,
            "path": ".",
            "kind": "root",
            "children": [],
        }
        try:
            top_dirs = sorted([p for p in PROJECT_ROOT.iterdir() if p.is_dir()],
                              key=lambda p: (not ((p / "yaml").is_dir()), p.name.lower()))
        except OSError:
            top_dirs = []
        for p in top_dirs:
            n = _node(p, 1)
            if n is not None:
                root["children"].append(n)
        return JSONResponse({"root": root, "count": len(root["children"]),
                             "project_root": str(PROJECT_ROOT)})

    @app.get("/api/workspace/download.zip")
    async def api_workspace_download(subpath: str = ""):
        """Stream a zip of the workspace (or an optional sub-directory).

        subpath: optional path relative to PROJECT_ROOT. Defaults to the
        whole workspace. Refuses anything that escapes PROJECT_ROOT.
        Skips heavy/cache/secret folders (same skip-set as /tree, plus .env).
        """
        import io
        import zipfile
        from fastapi.responses import StreamingResponse

        skip_dirs = {
            ".git", "__pycache__", ".pytest_cache", ".mypy_cache",
            ".ruff_cache", "node_modules", ".venv", "venv", "vendor",
            ".session", ".rag", ".claude", ".omc", ".benchmark",
            ".benchmarks", ".common_ai_agent", ".session_debug", "logs",
        }
        skip_files = {".env", ".env.local", ".env.production",
                      ".env.example", ".DS_Store"}

        try:
            base = PROJECT_ROOT
            if subpath:
                target = (PROJECT_ROOT / subpath).resolve()
                try:
                    target.relative_to(PROJECT_ROOT)
                except ValueError:
                    return JSONResponse(
                        {"error": "subpath outside project root"},
                        status_code=400,
                    )
                if target.is_dir():
                    base = target

            buf = io.BytesIO()
            file_count = 0
            with zipfile.ZipFile(buf, mode="w",
                                 compression=zipfile.ZIP_DEFLATED) as z:
                for root_dir, dirs, files in os.walk(base):
                    dirs[:] = [
                        d for d in dirs
                        if d not in skip_dirs and not d.startswith(".")
                    ]
                    for f in files:
                        if f in skip_files or f.startswith("."):
                            continue
                        full = Path(root_dir) / f
                        try:
                            rel = full.relative_to(base)
                            z.write(full, arcname=str(rel))
                            file_count += 1
                        except (OSError, ValueError):
                            continue
            buf.seek(0)
            name = f"{base.name or 'workspace'}.zip"

            def _iter():
                while True:
                    chunk = buf.read(64 * 1024)
                    if not chunk:
                        break
                    yield chunk

            return StreamingResponse(
                _iter(),
                media_type="application/zip",
                headers={
                    "Content-Disposition": f'attachment; filename="{name}"',
                    "X-Workspace-File-Count": str(file_count),
                },
            )
        except Exception as exc:
            return JSONResponse(
                {"error": f"zip failed: {exc}"},
                status_code=500,
            )

    @app.post("/api/soc/layout")
    async def api_soc_layout(request: Request):
        """Persist user-dragged block positions back into soc.ssot.yaml.

        Body (JSON): `{"layout": {"<cluster>/<inst>": {"x": <num>, "y": <num>}, …}}`

        For each entry, find the matching `instances[].id` (`<cluster>/<inst>`
        is split on `/`; we use just the inst id since SoC SSOT instance
        ids are unique) and set its `x:` / `y:` keys. Other fields are
        left untouched. The file is rewritten in-place with
        `yaml.safe_dump`. Empty layout `{}` clears all x/y from every
        instance (paired with the frontend's [reset] button).

        Architect screen reads these on the next /api/soc fetch and
        uses them as the default block position (overriding the
        auto-grid). LocalStorage layout still wins as the most-local
        cache, so a user can preview drag-arounds before committing.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        layout = body.get("layout") if isinstance(body, dict) else None
        if not isinstance(layout, dict):
            return JSONResponse({"error": "missing 'layout' object"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)

        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                 status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"parse: {e}"}, status_code=500)
        if not isinstance(doc, dict): doc = {}
        instances = doc.get("instances")
        if not isinstance(instances, list):
            return JSONResponse({"error": "soc.ssot.yaml has no instances[]"},
                                 status_code=400)

        # Build lookup `inst_id → ref` from layout keys.
        ref_for_inst = {}
        for ref in layout.keys():
            if not isinstance(ref, str) or "/" not in ref: continue
            inst_id = ref.split("/", 1)[1]
            ref_for_inst[inst_id] = ref

        touched = 0
        cleared = 0
        for inst in instances:
            if not isinstance(inst, dict): continue
            iid = inst.get("id")
            if not iid: continue
            ref = ref_for_inst.get(iid)
            if ref is None:
                # Instance not in incoming layout: if it has stale x/y
                # AND the incoming layout was empty `{}`, clear them.
                if not layout:
                    if "x" in inst: inst.pop("x"); cleared += 1
                    if "y" in inst: inst.pop("y"); cleared += 1
                    if "top_x" in inst: inst.pop("top_x"); cleared += 1
                    if "top_y" in inst: inst.pop("top_y"); cleared += 1
                continue
            pos = layout.get(ref)
            if isinstance(pos, dict) and isinstance(pos.get("x"), (int, float)) \
               and isinstance(pos.get("y"), (int, float)):
                if ref.startswith("top:"):
                    inst["top_x"] = round(float(pos["x"]), 1)
                    inst["top_y"] = round(float(pos["y"]), 1)
                else:
                    inst["x"] = round(float(pos["x"]), 1)
                    inst["y"] = round(float(pos["y"]), 1)
                touched += 1

        # Preserve hex formatting on address fields. PyYAML parses
        # `0x4000_2000` to int 1073750016 on load; safe_dump would write
        # it back as decimal. Walk the doc and stringify any int in
        # known address slots so the rewritten file keeps the canonical
        # `0x4000_2000` notation the user wrote.
        def _hex8(n):
            h = f"{n:x}"
            target = max(8, ((len(h) - 1) // 4 + 1) * 4)
            h = h.zfill(target)
            if len(h) > 4:
                rev = h[::-1]
                groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                h = "_".join(groups)[::-1]
            return f"0x{h}"
        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int):  e["base"]  = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])

        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "touched": touched, "cleared": cleared,
                              "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/connect")
    async def api_soc_connect(request: Request):
        """Append a port-to-port connection to soc.ssot.yaml.

        Body: {"from": "ip/PORT", "to": "ip/PORT", "proto": "AXI4"}
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected json object"}, status_code=400)
        src = str(body.get("from") or "").strip()
        dst = str(body.get("to") or "").strip()
        proto = str(body.get("proto") or "").strip().upper()
        if "/" not in src or "/" not in dst:
            return JSONResponse({"error": "from/to must look like ip/PORT"},
                                status_code=400)
        if src == dst:
            return JSONResponse({"error": "cannot connect a port to itself"},
                                status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)

        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        conns = doc.setdefault("connections", [])
        if not isinstance(conns, list):
            return JSONResponse({"error": "soc.ssot.yaml connections is not a list"},
                                status_code=400)
        for c in conns:
            if isinstance(c, dict) and c.get("from") == src and c.get("to") == dst:
                return JSONResponse({"ok": True, "duplicate": True,
                                     "connection": c,
                                     "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})
        entry = {"from": src, "to": dst}
        if proto:
            entry["proto"] = proto
        conns.append(entry)

        def _hex8(n):
            h = f"{n:x}"
            target = max(8, ((len(h) - 1) // 4 + 1) * 4)
            h = h.zfill(target)
            if len(h) > 4:
                rev = h[::-1]
                groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
                h = "_".join(groups)[::-1]
            return f"0x{h}"
        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int):  e["base"]  = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])
        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "connection": entry,
                             "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/instance/add")
    async def api_soc_instance_add(request: Request):
        """Instantiate a catalog model into soc.ssot.yaml.

        Body: {"model":"spi_master", "id":"spi_master_0",
               "cluster":"periph_ss", "addr":"0x4000_3000"}
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        if not isinstance(body, dict):
            return JSONResponse({"error": "expected json object"}, status_code=400)
        model = str(body.get("model") or body.get("name") or "").strip()
        req_id = str(body.get("id") or "").strip()
        cluster_id = str(body.get("cluster") or "").strip()
        addr = body.get("addr")
        if not model:
            return JSONResponse({"error": "missing model"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)

        catalog = []
        for p in sorted(PROJECT_ROOT.glob("*/yaml/*.ssot.yaml")):
            try:
                d = _yaml.safe_load(p.read_text(encoding="utf-8", errors="replace")) or {}
            except Exception:
                d = {}
            if not isinstance(d, dict):
                d = {}
            ip_dir = p.parents[1]
            top = d.get("top_module")
            name = top if isinstance(top, str) and top.strip() else ip_dir.name
            catalog.append({"name": name, "id": ip_dir.name,
                            "ssot": p.relative_to(PROJECT_ROOT).as_posix()})
        found = next((m for m in catalog
                      if m["name"] == model or m["id"] == model), None)
        if not found:
            return JSONResponse({"error": f"model not found: {model}"}, status_code=404)

        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        instances = doc.setdefault("instances", [])
        clusters = doc.setdefault("clusters", [])
        if not isinstance(instances, list) or not isinstance(clusters, list):
            return JSONResponse({"error": "soc.ssot.yaml instances/clusters must be lists"},
                                status_code=400)
        existing_ids = {str(i.get("id")) for i in instances if isinstance(i, dict) and i.get("id")}
        base = req_id or found["name"]
        inst_id = base
        if inst_id in existing_ids:
            i = 0
            while f"{base}_{i}" in existing_ids:
                i += 1
            inst_id = f"{base}_{i}"

        def _role_for_name(name):
            n = (name or "").lower()
            if any(x in n for x in ["cpu", "core", "cortex", "riscv"]): return ("cpu_ss", "CPU")
            if any(x in n for x in ["noc", "axi", "crossbar", "interconnect", "cci"]): return ("noc", "BUS")
            if any(x in n for x in ["ddr", "sram", "mem", "dram"]): return ("mem_ss", "MEM")
            return ("periph_ss", "PERIPH")

        default_cluster, default_role = _role_for_name(found["name"])
        cluster_id = cluster_id or default_cluster
        cluster = next((c for c in clusters
                        if isinstance(c, dict) and (c.get("id") or c.get("name")) == cluster_id), None)
        if cluster is None:
            cluster = {"id": cluster_id, "role": default_role, "members": []}
            clusters.append(cluster)
        members = cluster.setdefault("members", [])
        if isinstance(members, list) and inst_id not in members:
            members.append(inst_id)

        inst = {"id": inst_id, "ssot": found["ssot"]}
        if addr not in (None, ""):
            inst["addr"] = str(addr)
        if isinstance(body.get("x"), (int, float)): inst["top_x"] = round(float(body["x"]), 1)
        if isinstance(body.get("y"), (int, float)): inst["top_y"] = round(float(body["y"]), 1)
        instances.append(inst)

        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "instance": inst, "cluster": cluster_id,
                             "model": found, "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/soc/instance/delete")
    async def api_soc_instance_delete(request: Request):
        """Remove an instance from the SoC hierarchy without deleting model files.

        Body: {"id":"counter"}
        Removes:
          - instances[] entry
          - clusters[].members[] reference
          - connections touching <id>/*
          - addrMap entry matching id/name
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        inst_id = str((body or {}).get("id") or "").strip()
        if not inst_id:
            return JSONResponse({"error": "missing id"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        removed = {"instances": 0, "members": 0, "connections": 0, "addrMap": 0}
        instances = doc.get("instances") or []
        if isinstance(instances, list):
            kept = []
            for inst in instances:
                if isinstance(inst, dict) and str(inst.get("id") or "") == inst_id:
                    removed["instances"] += 1
                else:
                    kept.append(inst)
            doc["instances"] = kept
        for c in (doc.get("clusters") or []):
            if not isinstance(c, dict) or not isinstance(c.get("members"), list):
                continue
            before = len(c["members"])
            c["members"] = [m for m in c["members"] if str(m) != inst_id]
            removed["members"] += before - len(c["members"])
        conns = doc.get("connections") or []
        if isinstance(conns, list):
            kept = []
            prefix = f"{inst_id}/"
            for conn in conns:
                if isinstance(conn, dict) and (
                    str(conn.get("from") or "").startswith(prefix) or
                    str(conn.get("to") or "").startswith(prefix)
                ):
                    removed["connections"] += 1
                else:
                    kept.append(conn)
            doc["connections"] = kept
        amap = doc.get("addrMap") or []
        if isinstance(amap, list):
            kept = []
            for ent in amap:
                if isinstance(ent, dict) and str(ent.get("name") or "") == inst_id:
                    removed["addrMap"] += 1
                else:
                    kept.append(ent)
            doc["addrMap"] = kept
        if removed["instances"] == 0:
            return JSONResponse({"error": f"instance not found: {inst_id}",
                                 "removed": removed}, status_code=404)

        def _hex8(n):
            if isinstance(n, int):
                return "0x" + format(n, "08x")
            s = str(n)
            if s.startswith("0x"):
                return s
            return n

        for inst in (doc.get("instances") or []):
            if isinstance(inst, dict) and isinstance(inst.get("addr"), int):
                inst["addr"] = _hex8(inst["addr"])
        for e in (doc.get("addrMap") or []):
            if isinstance(e, dict):
                if isinstance(e.get("base"), int): e["base"] = _hex8(e["base"])
                if isinstance(e.get("range"), int): e["range"] = _hex8(e["range"])
        try:
            with open(soc_path, "w", encoding="utf-8") as f:
                _yaml.safe_dump(doc, f, sort_keys=False,
                                default_flow_style=False, allow_unicode=True)
        except OSError as e:
            return JSONResponse({"error": f"write: {e}"}, status_code=500)
        return JSONResponse({"ok": True, "id": inst_id, "removed": removed,
                             "path": soc_path.relative_to(PROJECT_ROOT).as_posix()})

    @app.post("/api/diagram/plan")
    async def api_diagram_plan(request: Request):
        """Plan diagram edits with the configured LLM.

        The model returns a narrow action JSON. The frontend owns actual
        application through existing layout/connect APIs.
        """
        try:
            body = await request.json()
        except Exception as e:
            return JSONResponse({"error": f"bad json: {e}"}, status_code=400)
        prompt = str((body or {}).get("prompt") or "").strip()
        if not prompt:
            return JSONResponse({"error": "missing prompt"}, status_code=400)
        try:
            import yaml as _yaml
        except ImportError:
            return JSONResponse({"error": "PyYAML not installed"}, status_code=500)
        soc_path = PROJECT_ROOT / "soc.ssot.yaml"
        if not soc_path.is_file():
            return JSONResponse({"error": "soc.ssot.yaml not found at project root"},
                                status_code=404)
        try:
            doc = _yaml.safe_load(soc_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            return JSONResponse({"error": f"soc parse: {e}"}, status_code=500)
        if not isinstance(doc, dict):
            doc = {}
        modules = []
        for inst in (doc.get("instances") or []):
            if not isinstance(inst, dict) or not inst.get("id"):
                continue
            mid = str(inst["id"])
            ports = []
            leaf = inst.get("ssot")
            if leaf:
                p = PROJECT_ROOT / str(leaf)
                if p.is_file():
                    try:
                        leaf_doc = _yaml.safe_load(p.read_text(encoding="utf-8")) or {}
                        for bi in (leaf_doc.get("busInterfaces") or []):
                            if isinstance(bi, dict):
                                ports.append({
                                    "name": bi.get("name"),
                                    "proto": bi.get("proto"),
                                    "role": bi.get("role"),
                                    "side": bi.get("side"),
                                })
                    except Exception:
                        pass
            modules.append({"id": mid, "name": inst.get("name") or mid,
                            "addr": inst.get("addr"),
                            "x": inst.get("top_x") or inst.get("x"),
                            "y": inst.get("top_y") or inst.get("y"),
                            "ports": ports})
        context = {
            "soc": doc.get("name") or PROJECT_ROOT.name,
            "clusters": doc.get("clusters") or [],
            "modules": modules,
            "connections": doc.get("connections") or [],
            "current_layout": (body or {}).get("layout") or {},
            "canvas": {"w": 1180, "h": 720},
        }

        def _quick_architect_plan(text: str, ctx: dict):
            """Small deterministic command layer before the LLM planner.

            This is intentionally narrow: it gives the Architect chat a
            reliable tool-call surface for common diagram edits, while the
            LLM still handles freer natural language.
            """
            raw = (text or "").strip()
            if not raw:
                return None
            low = raw.lower()
            mods = {str(m.get("id")): m for m in (ctx.get("modules") or [])}
            layout = ctx.get("current_layout") or {}

            def _ref_for(mid: str) -> str:
                for c in (ctx.get("clusters") or []):
                    if not isinstance(c, dict): continue
                    cid = c.get("id") or c.get("name") or "uncategorized"
                    for member in (c.get("members") or []):
                        if str(member) == mid:
                            return f"{cid}/{mid}"
                return f"uncategorized/{mid}"

            def _pos(mid: str):
                ref = _ref_for(mid)
                p = layout.get(f"top:{ref}") or layout.get(ref) or {}
                m = mods.get(mid) or {}
                x = p.get("x", m.get("x"))
                y = p.get("y", m.get("y"))
                try: x = float(x)
                except Exception: x = 170.0
                try: y = float(y)
                except Exception: y = 240.0
                return x, y

            def _move_action(mid: str, where: str = "", x=None, y=None):
                if mid not in mods:
                    return None
                cx, cy = _pos(mid)
                w = (where or "").lower()
                if x is None or y is None:
                    if w in ("left", "좌", "왼쪽"): x, y = 80, cy
                    elif w in ("right", "우", "오른쪽"): x, y = 850, cy
                    elif w in ("top", "up", "위", "상단"): x, y = cx, 70
                    elif w in ("bottom", "down", "아래", "하단"): x, y = cx, 540
                    elif w in ("center", "middle", "중앙", "가운데"): x, y = 470, 280
                    else: return None
                return {"type": "move_block", "id": mid, "x": x, "y": y}

            if low in ("/arch", "/arch help", "/diagram help", "help", "도움말"):
                return {
                    "summary": "Architect commands: /move <inst> <x> <y>|left|right|top|bottom|center; /connect <inst/port> <inst/port> [proto]; /add <model> [id] [cluster]; /delete <inst>; /layout",
                    "actions": [],
                }

            if re.match(r"^/(layout|auto-?layout)\b", low) or low in ("자동배치", "자동 배치"):
                return {"summary": "Reset to automatic top-level layout", "actions": [{"type": "auto_layout"}]}

            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+(-?\d+(?:\.\d+)?)\s+(-?\d+(?:\.\d+)?)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), x=float(m.group(2)), y=float(m.group(3)))
                return {"summary": f"Move {m.group(1)}", "actions": [act] if act else []}
            m = re.match(r"^/(?:move|mv)\s+([A-Za-z_][\w]*)\s+([A-Za-z가-힣]+)\s*$", raw, re.I)
            if m:
                act = _move_action(m.group(1), m.group(2))
                return {"summary": f"Move {m.group(1)} {m.group(2)}", "actions": [act] if act else []}

            for mid in mods:
                if re.search(rf"\b{re.escape(mid)}\b", raw):
                    where = None
                    if re.search(r"(left|왼쪽|좌측|좌로)", low): where = "left"
                    elif re.search(r"(right|오른쪽|우측|우로)", low): where = "right"
                    elif re.search(r"(top|up|위|상단)", low): where = "top"
                    elif re.search(r"(bottom|down|아래|하단)", low): where = "bottom"
                    elif re.search(r"(center|middle|중앙|가운데)", low): where = "center"
                    if where and re.search(r"(move|옮겨|움직|배치|놓|보내)", low):
                        act = _move_action(mid, where)
                        return {"summary": f"Move {mid} {where}", "actions": [act] if act else []}

            m = re.match(r"^/(?:connect|cn)\s+([\w.-]+/[\w.-]+)\s+([\w.-]+/[\w.-]+)(?:\s+([A-Za-z0-9_]+))?\s*$", raw, re.I)
            if m:
                proto = m.group(3) or ""
                return {"summary": f"Connect {m.group(1)} to {m.group(2)}",
                        "actions": [{"type": "connect_ports", "from": m.group(1), "to": m.group(2), "proto": proto}]}

            m = re.match(r"^/(?:add|add-instance|instantiate)\s+([A-Za-z_][\w]*)(?:\s+([A-Za-z_][\w]*))?(?:\s+([A-Za-z_][\w]*))?\s*$", raw, re.I)
            if m:
                model, inst_id, cluster = m.group(1), m.group(2), m.group(3)
                return {"summary": f"Add {model}",
                        "actions": [{"type": "add_instance", "model": model, "id": inst_id, "cluster": cluster, "x": 170, "y": 560}]}

            m = re.match(r"^/(?:delete|del|remove|rm)\s+([A-Za-z_][\w]*)\s*$", raw, re.I)
            if m:
                return {"summary": f"Delete {m.group(1)}",
                        "actions": [{"type": "delete_instance", "id": m.group(1)}]}

            return None

        quick_plan = _quick_architect_plan(prompt, context)
        if quick_plan is not None:
            return JSONResponse({"ok": True, "plan": quick_plan, "raw": "quick_architect_command"})

        try:
            arch_prompt = (PROJECT_ROOT / "workflow/architect/system_prompt.md").read_text(encoding="utf-8")[:4500]
            arch_commands = (PROJECT_ROOT / "workflow/architect/commands/architect.json").read_text(encoding="utf-8")[:2500]
        except Exception:
            arch_prompt = ""
            arch_commands = ""
        sys_prompt = (
            "You are an SoC Architect diagram planner. Convert the user request "
            "into ONLY strict JSON. No markdown. No prose. Schema: "
            "{\"summary\":\"...\",\"actions\":[...]}. "
            "Allowed actions: "
            "{\"type\":\"move_block\",\"id\":\"<module id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"connect_ports\",\"from\":\"<module>/<port>\",\"to\":\"<module>/<port>\",\"proto\":\"ACE|AXI4|APB|IRQ|...\"}; "
            "{\"type\":\"auto_layout\"}; "
            "{\"type\":\"add_instance\",\"model\":\"<catalog model>\",\"id\":\"<new instance id>\",\"cluster\":\"<cluster id>\",\"x\":number,\"y\":number}; "
            "{\"type\":\"delete_instance\",\"id\":\"<instance id>\"}. "
            "Use only module ids and ports present in context. For vague placement, choose reasonable canvas coordinates. "
            "You are attached to the workflow/architect supervisor contract below, but your output is still ONLY the diagram action JSON."
        )
        user_prompt = (
            "WORKFLOW ARCHITECT PROMPT EXCERPT:\n" + arch_prompt +
            "\n\nARCHITECT COMMANDS:\n" + arch_commands +
            "\n\nCONTEXT JSON:\n" + json.dumps(context, ensure_ascii=False, default=str) +
            "\n\nUSER REQUEST:\n" + prompt
        )
        try:
            from src.llm_client import call_llm_raw
            raw = await asyncio.to_thread(
                call_llm_raw,
                messages=[
                    {"role": "system", "content": sys_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=0.1,
                max_tokens=1200,
                caller_tag="atlas_diagram_plan",
            )
        except Exception as e:
            return JSONResponse({"error": f"llm: {e}"}, status_code=500)
        txt = str(raw or "").strip()
        if txt.startswith("```"):
            txt = re.sub(r"^```(?:json)?\s*", "", txt)
            txt = re.sub(r"\s*```$", "", txt)
        try:
            plan = json.loads(txt)
        except Exception:
            m = re.search(r"\{.*\}", txt, re.S)
            if not m:
                return JSONResponse({"error": "llm returned non-json", "raw": txt},
                                    status_code=500)
            try:
                plan = json.loads(m.group(0))
            except Exception as e:
                return JSONResponse({"error": f"json parse: {e}", "raw": txt},
                                    status_code=500)
        if not isinstance(plan, dict):
            return JSONResponse({"error": "plan must be object", "raw": txt},
                                status_code=500)
        actions = plan.get("actions")
        if not isinstance(actions, list):
            return JSONResponse({"error": "plan.actions must be list", "plan": plan},
                                status_code=500)
        allowed = {"move_block", "connect_ports", "auto_layout", "add_instance", "delete_instance"}
        plan["actions"] = [a for a in actions[:12]
                           if isinstance(a, dict) and a.get("type") in allowed]
        return JSONResponse({"ok": True, "plan": plan, "raw": txt})

    @app.post("/api/ipxact/import")
    async def api_ipxact_import(request: Request):
        """Import an IP-XACT XML payload into the project as a new IP.

        Accepts either:
          • multipart/form-data with a `xml` file part + optional `name`
          • application/json: {"xml": "<XML…>", "name": "spi_master"}
          • application/xml or text/xml body + ?name=<ip_name> query

        Writes <project_root>/<name>/yaml/<name>.ssot.yaml and scaffolds
        the surrounding IP layout. Returns the parsed SSOT + path.
        """
        try:
            ct = (request.headers.get("content-type") or "").lower()
            xml_text: str = ""
            ip_name: str = ""
            if ct.startswith("multipart/form-data"):
                form = await request.form()
                up = form.get("xml")
                if up is None:
                    return JSONResponse({"error": "missing 'xml' file part"}, status_code=400)
                if hasattr(up, "read"):
                    raw = await up.read()
                    xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                else:
                    xml_text = str(up)
                ip_name = (form.get("name") or "").strip()
            elif "json" in ct:
                body = await request.json()
                xml_text = body.get("xml", "") or ""
                ip_name = (body.get("name") or "").strip()
            else:
                raw = await request.body()
                xml_text = raw.decode("utf-8", errors="replace") if isinstance(raw, (bytes, bytearray)) else str(raw)
                ip_name = (request.query_params.get("name") or "").strip()
            if not xml_text.strip():
                return JSONResponse({"error": "empty XML payload"}, status_code=400)

            try:
                from core.ipxact_import import import_ipxact as _conv
            except Exception:
                try: from ipxact_import import import_ipxact as _conv  # type: ignore
                except Exception as e:
                    return JSONResponse({"error": f"importer unavailable: {e}"}, status_code=500)
            try:
                ssot = _conv(xml_text, ip_name=ip_name or None)
            except Exception as e:
                return JSONResponse({"error": f"parse error: {e}"}, status_code=400)
            name = (ip_name or ssot.get("top_module") or "").strip()
            if not name or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
                return JSONResponse({"error": f"invalid ip name {name!r}"}, status_code=400)

            # Write into <project_root>/<name>/yaml/<name>.ssot.yaml.
            ip_dir = PROJECT_ROOT / name
            (ip_dir / "yaml").mkdir(parents=True, exist_ok=True)
            for sub in ("rtl", "sim", "tb", "list", "lint", "doc"):
                (ip_dir / sub).mkdir(parents=True, exist_ok=True)
            yaml_path = ip_dir / "yaml" / f"{name}.ssot.yaml"
            try:
                import yaml as _yaml
                with open(yaml_path, "w", encoding="utf-8") as f:
                    f.write("# Auto-imported from IP-XACT — review and edit as needed.\n")
                    _yaml.safe_dump(ssot, f, sort_keys=False, default_flow_style=False, allow_unicode=True)
            except ImportError:
                # No PyYAML → write a JSON sidecar so the import still
                # produces something usable.
                with open(yaml_path.with_suffix(".json"), "w", encoding="utf-8") as f:
                    json.dump(ssot, f, indent=2)
                yaml_path = yaml_path.with_suffix(".json")
            except OSError as e:
                return JSONResponse({"error": f"write error: {e}"}, status_code=500)

            # Auto-register into soc.ssot.yaml when Tier-1 is active so
            # the new IP appears in the architect tree on the next
            # /api/soc fetch (was P1 bug — yaml on disk but tree empty).
            registered = False
            try:
                soc_path = PROJECT_ROOT / "soc.ssot.yaml"
                if soc_path.is_file():
                    import yaml as _y
                    sd = _y.safe_load(soc_path.read_text(encoding="utf-8")) or {}
                    if isinstance(sd, dict):
                        instances = sd.setdefault("instances", [])
                        # Skip if an instance with this id already exists.
                        existing = next((i for i in instances
                                          if isinstance(i, dict) and i.get("id") == name), None)
                        if existing is None:
                            new_inst = {
                                "id": name,
                                "ssot": yaml_path.relative_to(PROJECT_ROOT).as_posix(),
                            }
                            # Pull addr from the imported IP's memoryMap
                            # so addrmap_check can validate it.
                            mm = (ssot or {}).get("memoryMap") or []
                            if isinstance(mm, list) and mm and isinstance(mm[0], dict):
                                base = mm[0].get("base")
                                if base: new_inst["addr"] = base
                            instances.append(new_inst)
                            # Drop into a synthetic "uncategorized" cluster
                            # if nothing else claims it (clusters[].members
                            # is the source of truth — auto-add a stub).
                            clusters = sd.setdefault("clusters", [])
                            uncat = next((c for c in clusters
                                          if isinstance(c, dict) and c.get("id") == "uncategorized"),
                                          None)
                            if uncat is None:
                                clusters.append({
                                    "id": "uncategorized",
                                    "role": "PERIPH",
                                    "label": "Uncategorized (auto-imported)",
                                    "members": [name],
                                })
                            else:
                                members = uncat.setdefault("members", [])
                                if name not in members: members.append(name)
                            with open(soc_path, "w", encoding="utf-8") as f:
                                _y.safe_dump(sd, f, sort_keys=False,
                                             default_flow_style=False, allow_unicode=True)
                            registered = True
            except Exception as e:
                # Non-fatal — IP file is on disk, just couldn't auto-register.
                # Frontend will still see it via Tier-2 fallback.
                pass

            return JSONResponse({
                "ok": True,
                "name": name,
                "path": yaml_path.relative_to(PROJECT_ROOT).as_posix(),
                "registered_in_soc": registered,
                "ssot": ssot,
            })
        except Exception as e:
            return JSONResponse({"error": str(e)}, status_code=500)

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

            def _read_history(path: Path) -> list[dict[str, Any]]:
                if not path.is_file():
                    return []
                raw = json.loads(path.read_text(encoding="utf-8"))
                return raw if isinstance(raw, list) else []

            fallback_session = ""
            try:
                msgs = _read_history(hpath)
            except Exception as e:
                return JSONResponse({"messages": [], "path": str(hpath),
                                       "error": f"parse: {e}"})
            non_system = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if not non_system:
                root = PROJECT_ROOT / ".session"
                candidates = []
                if root.is_dir():
                    for p in root.rglob("conversation.json"):
                        try:
                            candidates.append((p.stat().st_mtime, p))
                        except Exception:
                            pass
                for _, p in sorted(candidates, reverse=True):
                    try:
                        alt = _read_history(p)
                    except Exception:
                        continue
                    alt_non_system = [
                        m for m in alt
                        if isinstance(m, dict) and m.get("role") != "system"
                    ]
                    if alt_non_system:
                        msgs = alt
                        hpath = p
                        try:
                            fallback_session = p.parent.relative_to(root).as_posix()
                        except Exception:
                            fallback_session = str(p.parent)
                        break
            # Drop system prompts (huge, useless in chat replay) and
            # keep only the last `limit` items.
            msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
            if len(msgs) > limit:
                msgs = msgs[-limit:]
            return JSONResponse({"messages": msgs, "path": str(hpath),
                                  "fallback_session": fallback_session,
                                  "truncated_to": limit})
        except Exception as e:
            return JSONResponse({"messages": [], "error": str(e)},
                                 status_code=500)

    @app.get("/api/session/history")
    async def api_session_history(session: str, limit: int = 200):
        """Read a specific .session/<session>/conversation.json.

        Architect uses this to reload per-IP/per-workflow agent history,
        e.g. `.session/spi_master/rtl-gen/conversation.json`.
        """
        session_raw = session or ""
        session = normalize_session_name(session_raw)
        if not session:
            status = 400
            error = "missing session" if not str(session_raw).strip() else f"invalid session {session_raw!r}"
            return JSONResponse({"error": error}, status_code=status)
        root = (PROJECT_ROOT / ".session").resolve()
        sdir = (root / session).resolve()
        try:
            sdir.relative_to(root)
        except Exception:
            return JSONResponse({"error": "session path escapes .session"}, status_code=400)
        hpath = sdir / "conversation.json"
        if not hpath.is_file():
            return JSONResponse({"messages": [], "session": session,
                                 "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                 "exists": False})
        try:
            msgs = json.loads(hpath.read_text(encoding="utf-8"))
            if not isinstance(msgs, list):
                msgs = []
        except Exception as e:
            return JSONResponse({"messages": [], "session": session,
                                 "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                                 "error": f"parse: {e}"}, status_code=500)
        msgs = [m for m in msgs if isinstance(m, dict) and m.get("role") != "system"]
        if len(msgs) > limit:
            msgs = msgs[-limit:]
        return JSONResponse({"messages": msgs, "session": session,
                             "path": hpath.relative_to(PROJECT_ROOT).as_posix(),
                             "exists": True, "truncated_to": limit})

    @app.get("/api/session/state")
    async def api_session_state(session: str, limit: int = 200, mode: str = "conversation"):
        """Return all UI state owned by a specific session namespace.

        This is the session-scoped hydrate endpoint for IP/sub-top/SoC
        workflow panes.  The frontend can switch screens or selected
        modules without losing chat/todo state because the authoritative
        data lives under `.session/<session>/`.

        `mode` controls which file the conversation messages come from:
          • conversation (default) — recent rolling window from
            conversation.json (already capped server-side at `limit`).
          • full        — every message ever written to
            full_conversation.json (no limit cap).
          • recent      — last `limit` messages from
            full_conversation.json (deeper history than conversation.json
            but trimmed to a manageable size).
        """
        session_raw = session or ""
        session = normalize_session_name(session_raw)
        if not session:
            status = 400
            error = "missing session" if not str(session_raw).strip() else f"invalid session {session_raw!r}"
            return JSONResponse({"error": error}, status_code=status)
        root = (PROJECT_ROOT / ".session").resolve()
        sdir = (root / session).resolve()
        try:
            sdir.relative_to(root)
        except Exception:
            return JSONResponse({"error": "session path escapes .session"}, status_code=400)

        def _read_json(path: Path, fallback: Any) -> Any:
            if not path.is_file():
                return fallback
            try:
                data = json.loads(path.read_text(encoding="utf-8"))
                return data
            except Exception:
                return fallback

        mode_norm = (mode or "conversation").strip().lower()
        if mode_norm not in ("conversation", "full", "recent"):
            mode_norm = "conversation"
        if mode_norm == "conversation":
            conv_path = sdir / "conversation.json"
        else:
            conv_path = sdir / "full_conversation.json"
            # Fall back to conversation.json when full_conversation.json is missing
            if not conv_path.is_file():
                conv_path = sdir / "conversation.json"

        messages = _read_json(conv_path, [])
        if not isinstance(messages, list):
            messages = []
        messages = [m for m in messages if isinstance(m, dict) and m.get("role") != "system"]
        # `full` returns everything; `conversation` and `recent` cap at limit.
        if mode_norm != "full" and len(messages) > limit:
            messages = messages[-limit:]

        todo_state = _read_json(sdir / "todo.json", {"todos": []})
        if isinstance(todo_state, list):
            todo_state = {"todos": todo_state}
        if not isinstance(todo_state, dict):
            todo_state = {"todos": []}
        todos = todo_state.get("todos")
        if not isinstance(todos, list):
            todo_state["todos"] = []
        # Session-scoped <session>/todo.json doesn't always get written —
        # session_setup re-pinning of config.TODO_FILE only happens for
        # workspaces that go through that path; runs that started under
        # the global default keep persisting to PROJECT_ROOT/current_todos.json.
        # When the session file is missing or empty, fall back to the
        # live main.todo_tracker (in-memory, freshest) and then the
        # global file. Without this the panel would render empty even
        # though the agent has 3+ active tasks on disk.
        if not todo_state["todos"]:
            try:
                import main as _live_main  # noqa: WPS433
                _live = getattr(_live_main, "todo_tracker", None)
                if _live is not None and getattr(_live, "todos", None):
                    todo_state = _live.to_dict()
            except Exception:
                pass
        if not todo_state.get("todos"):
            global_todo = PROJECT_ROOT / "current_todos.json"
            if global_todo.is_file():
                try:
                    g = json.loads(global_todo.read_text(encoding="utf-8"))
                    if isinstance(g, dict) and isinstance(g.get("todos"), list):
                        todo_state = g
                    elif isinstance(g, list):
                        todo_state = {"todos": g}
                except Exception:
                    pass

        cost_state = _read_json(sdir / "cost.json", {})
        if not isinstance(cost_state, dict):
            cost_state = {}

        with _jobs_lock:
            jobs = [
                _public_job(j)
                for j in _jobs.values()
                if str(j.get("session") or "").strip("/") == session
            ]
        jobs.sort(key=lambda j: j.get("started_at") or 0, reverse=True)

        return JSONResponse({
            "session": session,
            "session_dir": sdir.relative_to(PROJECT_ROOT).as_posix(),
            "exists": sdir.is_dir(),
            "conversation": {
                "messages": messages,
                "path": conv_path.relative_to(PROJECT_ROOT).as_posix(),
                "exists": conv_path.is_file(),
                "mode": mode_norm,
                "truncated_to": (None if mode_norm == "full" else limit),
            },
            "todos": todo_state,
            "cost": cost_state,
            "jobs": jobs,
        })

    @app.get("/api/session/list")
    async def api_session_list():
        """List reloadable session namespaces under .session/."""
        root = PROJECT_ROOT / ".session"
        out = []
        if root.is_dir():
            for p in sorted(root.rglob("conversation.json")):
                try:
                    rel = p.parent.relative_to(root)
                except Exception:
                    continue
                session = str(rel)
                if session == ".":
                    continue
                out.append({
                    "session": session,
                    "path": p.relative_to(PROJECT_ROOT).as_posix(),
                    "mtime": p.stat().st_mtime,
                    "size": p.stat().st_size,
                })
        return JSONResponse({"sessions": out, "count": len(out)})

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
        _ensure_broadcaster()
        # Greeting — surface user-tunable layout settings so the frontend
        # can pick its center-column shape (classic vs tabbed Chat/Preview/Q&A).
        try:
            import src.config as _cfg_hello
            _center_layout = getattr(_cfg_hello, "ATLAS_CENTER_LAYOUT", "classic")
        except Exception:
            _center_layout = "classic"
        await websocket.send_json({"type": "hello", "frontend": "atlas",
                                    "running": bridge.agent_running,
                                    "center_layout": _center_layout})
        for pending_event in bridge.pending_ask_user_events():
            await websocket.send_json(pending_event)
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
                    import os as _os
                    _ui_lang_raw = str(msg.get("ui_lang") or _os.environ.get("ATLAS_UI_LANG") or "").strip().lower()
                    _ui_lang = {
                        "ko": "ko",
                        "kr": "ko",
                        "korean": "ko",
                        "한국어": "ko",
                        "en": "en",
                        "eng": "en",
                        "english": "en",
                    }.get(_ui_lang_raw, "")
                    if _ui_lang:
                        _os.environ["ATLAS_UI_LANG"] = _ui_lang
                    _session_raw = str(msg.get("session") or "").strip()
                    _session = normalize_session_name(_session_raw)
                    if _session_raw:
                        if not _session:
                            bridge.emit("error", message=f"invalid session: {_session_raw!r}")
                            continue
                        _os.environ["ATLAS_ACTIVE_SESSION"] = _session
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
                    _low = _txt.lower()
                    if _handle_new_ip_command(_txt):
                        continue
                    if _handle_import_command(_txt):
                        continue
                    if _handle_grill_me_command(_txt):
                        continue
                    if _handle_approval_command(_txt):
                        continue
                    if _handle_resolve_rtl_blockers_command(_txt):
                        continue
                    if _handle_repair_ssot_command(_txt):
                        continue
                    if _handle_repair_rtl_command(_txt):
                        continue
                    if _handle_repair_equiv_command(_txt):
                        continue
                    if _handle_to_ssot_gate(_txt):
                        continue
                    if _run_stage_command(_txt):
                        continue
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
                    _control_heads = {"approve", "y", "yes", "yc", "confirm", "ok", "proceed", "ㅇㅇ", "확인", "진행"}
                    _head = (_txt.split(None, 1)[0] if _txt else "").lower()
                    if _ui_lang and _txt and not _txt.startswith("/") and _head not in _control_heads:
                        if _ui_lang == "ko":
                            _txt = (
                                "[Atlas UI language preference]\n"
                                "User-visible explanations, status summaries, questions, and reports should be written in Korean as much as possible. "
                                "Keep code, file paths, commands, signal names, protocol names, and exact identifiers unchanged.\n\n"
                                + _txt
                            )
                        elif _ui_lang == "en":
                            _txt = (
                                "[Atlas UI language preference]\n"
                                "User-visible explanations, status summaries, questions, and reports should be written in English as much as possible. "
                                "Keep code, file paths, commands, signal names, protocol names, and exact identifiers unchanged.\n\n"
                                + _txt
                            )
                    bridge.submit_prompt(_txt)
                elif t == "interrupt":
                    bridge.submit_prompt(msg.get("text", ""))
                elif t == "answer" and msg.get("flow_id"):
                    accepted = bridge.submit_answer(msg["flow_id"], msg)
                    if accepted:
                        bridge.emit("agent_state", running=True)
                    else:
                        bridge.emit(
                            "error",
                            message=(
                                "answer rejected: no pending ask_user flow "
                                f"for {msg['flow_id']}"
                            ),
                        )
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

    # Expose SSOT-QA helpers so run_atlas_ui's nested callbacks
    # (_ask_user_cb, _record_ssot_qa_cb) can reach them across function
    # scopes — these helpers live in create_app's local closure and were
    # otherwise invisible from run_atlas_ui, causing NameError at the
    # first ask_user / record_ssot_qa invocation.
    app.state.active_ssot_qa_context = _active_ssot_qa_context
    app.state.ssot_q_pairs_from_questions = _ssot_q_pairs_from_questions
    app.state.upsert_ssot_qa_items = _upsert_ssot_qa_items
    app.state.load_ssot_state = _load_ssot_state
    app.state.valid_ip_name = _valid_ip_name
    app.state.status_group = _status_group
    app.state.answer_text = _answer_text
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

    # Rebind SSOT-QA helpers from create_app's closure (exposed via
    # app.state) so the nested _ask_user_cb / _record_ssot_qa_cb defined
    # below can reference them by their original local names without
    # raising NameError. See create_app return block for the export side.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _load_ssot_state = app.state.load_ssot_state
    _valid_ip_name = app.state.valid_ip_name
    _status_group = app.state.status_group
    _answer_text = app.state.answer_text

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
    # First branch: full CSI/OSC sequences w/ the leading ESC byte.
    # Last branch: ORPHAN SGR codes whose ESC was stripped upstream
    # (common on Windows when the console host or codec drops 0x1b),
    # leaving visible garbage like `[2m 187 [0m` in the chat. Match
    # them only when they look like real SGR — `[<digits[;digits]*>m`.
    _ANSI_RE = _re_ansi.compile(
        r"\x1b\[[0-9;?]*[a-zA-Z]"
        r"|\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)"
        r"|\[(?:\d{1,3};)*\d{0,3}m"
    )
    def _clean(s):
        return _ANSI_RE.sub("", s) if isinstance(s, str) else s

    def _current_todo_state() -> dict[str, Any]:
        """Return the freshest structured todo state for browser rendering."""
        try:
            tt = getattr(_main, "todo_tracker", None)
            if tt is not None and hasattr(tt, "to_dict"):
                state = tt.to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list) and state.get("todos"):
                    return state
        except Exception:
            pass
        try:
            import config as _cfg
            from lib.todo_tracker import TodoTracker
            todo_path = Path(str(getattr(_cfg, "TODO_FILE", "current_todos.json")))
            if not todo_path.is_absolute():
                todo_path = PROJECT_ROOT / todo_path
            if todo_path.exists():
                state = TodoTracker.load(todo_path).to_dict()
                if isinstance(state, dict) and isinstance(state.get("todos"), list):
                    return state
        except Exception:
            pass
        return {"todos": []}

    def _emit_todo_line(text: str) -> None:
        state = {"todos": []} if not str(text or "").strip() else _current_todo_state()
        bridge.emit(
            "todo_line",
            text=_clean(text),
            todo_state=state,
            todos=state.get("todos", []),
        )

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=_clean(text), cls=cls)

    def _atlas_emit_reasoning(text, blank=False):
        cleaned = _clean(text)
        # Browser side via the live WS bridge (chat feed renders this
        # as a CollapsibleThought block — see workspace.jsx).
        bridge.emit("reasoning", text=cleaned)
        # Server-console mirror: an operator running textual_main.py
        # in a terminal needs to see what the model is thinking too,
        # not just the tool calls. Mirror to stderr with a CYAN ┃
        # prefix so reasoning lines are scannable amid debug output.
        if cleaned:
            try:
                import sys as _sys_re
                if blank:
                    _sys_re.stderr.write("\n")
                else:
                    _sys_re.stderr.write(
                        f"  \033[36m┃\033[0m \033[2m{cleaned}\033[0m\n"
                    )
                _sys_re.stderr.flush()
            except Exception:
                pass

    _main._textual_emit_reasoning_fn = _atlas_emit_reasoning
    _main._textual_emit_todo_fn      = _emit_todo_line
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
            # in_tok from react_loop is the FULL prompt_tokens (includes
            # the cached subset). cache_tok is that cached subset only.
            # Charging both `in_tok * input` and `cache_tok * cache` would
            # bill the cached portion twice — once at the input rate and
            # once at the cache rate. Subtract the cache slice first so
            # billable_input = prompt − cached.
            _in = max(0, (in_tok or 0) - (cache_tok or 0))
            cost_delta = (
                _in              * p.input  +
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

    # Helpers are defined as closures inside create_app(); pull them off
    # app.state so this module-level function can reach them.
    _active_ssot_qa_context = app.state.active_ssot_qa_context
    _valid_ip_name = app.state.valid_ip_name
    _ssot_q_pairs_from_questions = app.state.ssot_q_pairs_from_questions
    _load_ssot_state = app.state.load_ssot_state
    _upsert_ssot_qa_items = app.state.upsert_ssot_qa_items
    _status_group = app.state.status_group

    def _record_ssot_qa_cb(questions=None, ip=None, session=None, kind="",
                           source="llm-ssot-qna", status="pending"):
        """Record deferred SSOT QA without blocking the agent thread."""
        ctx_ip, ctx_session = _active_ssot_qa_context()
        target_ip = str(ip or ctx_ip or "").strip()
        if not _valid_ip_name(target_ip):
            return "[record_ssot_qa: no active valid SSOT IP]"
        target_session = normalize_session_name(str(session or ctx_session or f"{target_ip}/ssot-gen"))
        flow_id = "qa_backlog_" + uuid.uuid4().hex[:10]
        q_pairs = _ssot_q_pairs_from_questions(questions or [])
        if not q_pairs:
            return "[record_ssot_qa: no valid QA items to record]"
        state = _load_ssot_state(target_ip) or {}
        ip_kind = str(kind or "").strip()
        if ip_kind.lower() in {"single", "multi", "input"}:
            ip_kind = ""
        _upsert_ssot_qa_items(
            target_ip,
            flow_id=flow_id,
            kind=str(ip_kind or state.get("kind") or "general IP"),
            q_pairs=q_pairs,
            status=str(status or "pending"),
            session=target_session,
            source=str(source or "llm-ssot-qna"),
        )
        bridge.emit(
            "ssot_qa_updated",
            ip=target_ip,
            workflow="ssot-gen",
            flow_id=flow_id,
            session=target_session,
        )
        return (
            f"[record_ssot_qa] recorded {len(q_pairs)} "
            f"{_status_group(str(status or 'pending'))} SSOT QA item(s) "
            f"for {target_session}"
        )

    def _ask_user_cb(question, options, kind, subtitle, questions=None):
        """ask_user UI bridge.

        Single-question mode: pass `question/options/kind/subtitle`.
        Batched mode (mirrors textual UI): pass `questions=[{...}, ...]`
        and the frontend renders a tab strip — one breadcrumb per
        question, ☐/☒ answered marker, plus a final 'Submit' tab — so
        the user fills N answers in one round-trip.
        """
        flow_id = "qa_" + uuid.uuid4().hex[:10]
        ssot_ip, ssot_session = _active_ssot_qa_context()
        ssot_q_pairs: list[tuple[str, str, dict[str, Any]]] = []
        if ssot_ip:
            if questions:
                ssot_q_pairs = _ssot_q_pairs_from_questions(questions)
            elif question:
                ssot_q_pairs = _ssot_q_pairs_from_questions([{
                    "id": "question",
                    "decision_key": "question",
                    "decision_label": subtitle or question,
                    "question": question,
                    "kind": kind,
                    "subtitle": subtitle or "",
                    "options": options or [],
                }])
            if ssot_q_pairs:
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="pending",
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                )
        ssot_emit = (
            {"session": ssot_session, "ip": ssot_ip, "workflow": "ssot-gen", "source": "llm-ssot-qna"}
            if ssot_ip else {}
        )
        bridge.open_question(flow_id)
        if questions:
            # Batched payload — frontend (workspace.jsx) detects the
            # `questions` array and switches to tabbed render.
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                questions=questions,
                **ssot_emit,
            )
        else:
            bridge.emit(
                "ask_user",
                flow_id=flow_id,
                question=question,
                kind=kind,
                subtitle=subtitle or "",
                options=options or [],
                **ssot_emit,
            )
        try:
            ans = bridge.wait_answer(flow_id, timeout=900)  # 15 min ceiling
        finally:
            bridge.close_question(flow_id)
        if ans is None:
            return "[ask_user: no answer received within 15 min]"
        # Cancel-all from the user — match textual UI wording.
        if isinstance(ans, dict) and ans.get("type") == "cancel":
            return "User declined to answer questions"
        # Batched answer format: {"answers": [{...}, ...]} aligned with questions.
        if questions and isinstance(ans, dict) and "answers" in ans:
            blocks = []
            qa_answers: dict[str, dict[str, Any]] = {}
            for q, qa in zip(questions, ans.get("answers") or []):
                label = (q.get("subtitle") or q.get("question", ""))[:40]
                blocks.append(
                    f"  • {label}\n    {_format_answer(qa, q.get('options'))}"
                )
            if ssot_ip and ssot_q_pairs:
                for (key, _label, q), qa in zip(ssot_q_pairs, ans.get("answers") or []):
                    qa_dict = qa if isinstance(qa, dict) else {}
                    qa_answers[key] = {
                        "answer": _answer_text(qa_dict, q),
                        "selected": qa_dict.get("selected") or [],
                        "custom": str(qa_dict.get("custom") or "").strip(),
                    }
                _upsert_ssot_qa_items(
                    ssot_ip,
                    flow_id=flow_id,
                    kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                    q_pairs=ssot_q_pairs,
                    status="approved",
                    answers=qa_answers,
                    session=ssot_session,
                )
                bridge.emit(
                    "ssot_qa_updated",
                    ip=ssot_ip,
                    workflow="ssot-gen",
                    flow_id=flow_id,
                    session=ssot_session,
                )
            return "Batched answers:\n" + "\n".join(blocks) if blocks else "(no answers)"
        if ssot_ip and ssot_q_pairs and isinstance(ans, dict):
            key, _label, q = ssot_q_pairs[0]
            _upsert_ssot_qa_items(
                ssot_ip,
                flow_id=flow_id,
                kind=str((_load_ssot_state(ssot_ip) or {}).get("kind") or "general IP"),
                q_pairs=ssot_q_pairs,
                status="approved",
                answers={
                    key: {
                        "answer": _answer_text(ans, q),
                        "selected": ans.get("selected") or [],
                        "custom": str(ans.get("custom") or "").strip(),
                    }
                },
                session=ssot_session,
            )
            bridge.emit(
                "ssot_qa_updated",
                ip=ssot_ip,
                workflow="ssot-gen",
                flow_id=flow_id,
                session=ssot_session,
            )
        return _format_answer(ans, options or [])

    if _tools and hasattr(_tools, "set_ask_user_callback"):
        _tools.set_ask_user_callback(_ask_user_cb)
    if _tools and hasattr(_tools, "set_record_ssot_qa_callback"):
        _tools.set_record_ssot_qa_callback(_record_ssot_qa_cb)

    def _run_agent():
        try:
            _main.chat_loop()
        except Exception as e:
            bridge.emit("error", message=str(e))
        finally:
            with bridge._agent_lock:
                bridge.agent_alive = False
            bridge.agent_running = False
            bridge.emit("agent_state", running=False)
            bridge.emit("done")

    def _start_agent_thread():
        threading.Thread(target=_run_agent, daemon=True).start()

    bridge.set_agent_starter(_start_agent_thread)
    bridge.ensure_agent_alive()

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
