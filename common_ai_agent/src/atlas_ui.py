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
import queue
import sys
import threading
from pathlib import Path

# ── Paths ──────────────────────────────────────────────────────────
HERE      = Path(__file__).resolve().parent
ROOT      = HERE.parent                              # common_ai_agent/
FRONTEND  = ROOT / "frontend" / "atlas"


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

    @app.get("/healthz")
    async def healthz():
        return JSONResponse({"ok": True, "frontend": str(FRONTEND)})

    # ── REAL project data API ────────────────────────────────────
    # File-system backed endpoints. All paths are confined to ROOT and
    # rejected if they try to escape via .. or absolute paths.
    PROJECT_ROOT = ROOT
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
    async def api_files(path: str = ""):
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
        entries = []
        try:
            for child in sorted(target.iterdir(),
                                 key=lambda p: (p.is_file(), p.name.lower())):
                if child.name in SKIP_DIRS or child.name.startswith("."):
                    continue
                try:
                    stat = child.stat()
                except OSError:
                    continue
                entries.append({
                    "name": child.name,
                    "type": "dir" if child.is_dir() else "file",
                    "size": stat.st_size if child.is_file() else None,
                    "mtime": stat.st_mtime,
                })
        except PermissionError:
            return JSONResponse({"error": "permission denied"},
                                status_code=403)
        return JSONResponse({"type": "dir", "path": rel, "entries": entries})

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

        # Pump outbox → all sockets (one task shared per connection is fine)
        async def pump_out():
            while True:
                msg = await bridge.next_event()
                stale = []
                for client in list(clients):
                    try:
                        await client.send_json(msg)
                    except Exception:
                        stale.append(client)
                for c in stale:
                    clients.discard(c)

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
                    bridge.submit_prompt(msg["text"].strip())
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

    # Static assets — jsx, css, js, fonts (registered LAST so it doesn't shadow
    # the explicit routes above)
    app.mount("/", StaticFiles(directory=str(FRONTEND), html=False), name="atlas-static")

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

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=text, cls=cls)
    _main._textual_emit_reasoning_fn = lambda text, blank=False: bridge.emit("reasoning", text=text)
    _main._textual_emit_todo_fn      = lambda text: bridge.emit("todo_line", text=text)
    _main._textual_emit_flush_fn     = lambda: bridge.emit("flush")
    _main._textual_emit_tool_fn      = lambda text: bridge.emit("tool", text=text)
    _main._textual_emit_tool_result_fn = lambda obs, tool="": bridge.emit(
        "tool_result", text=obs[:8000], tool=tool, truncated=len(obs) > 8000
    )

    def _ctx_update(tokens, max_tok):
        bridge.emit("context", used=tokens, max=max_tok)
    _main._textual_emit_context_fn = _ctx_update
    _main._textual_emit_token_fn = lambda in_tok, cache_tok, out_tok: bridge.emit(
        "cost", input=in_tok, cached=cache_tok, output=out_tok
    )

    def _set_running(val: bool):
        bridge.agent_running = val
        bridge.emit("agent_state", running=val)
    _main._textual_set_agent_running_fn = _set_running

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
