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


# ── Bridge between agent thread and async WS handlers ──────────────
class _AtlasBridge:
    """Queues prompts from the WS into the sync agent loop and pushes
    agent events back out to all connected WS clients.
    """

    def __init__(self) -> None:
        self._inbox: queue.Queue[str] = queue.Queue()
        self._interrupts: queue.Queue[str] = queue.Queue()
        self._outbox: queue.Queue[dict] = queue.Queue()
        self.agent_running: bool = False

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

    # — ws-side (async) —
    def submit_prompt(self, text: str) -> None:
        if self.agent_running:
            self._interrupts.put(text)
        else:
            self._inbox.put(text)

    async def next_event(self) -> dict:
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._outbox.get)


# ── App factory ────────────────────────────────────────────────────
def create_app():
    try:
        from fastapi import FastAPI, WebSocket, WebSocketDisconnect
        from fastapi.responses import FileResponse, JSONResponse
        from fastapi.staticfiles import StaticFiles
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

    # NOTE: WebSocket route MUST be registered BEFORE the catch-all StaticFiles
    # mount on "/", otherwise the mount intercepts /ws/agent upgrade requests.
    @app.websocket("/ws/agent")
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
                # Other types (e.g. run_stage, tool_call) can be wired later
        except WebSocketDisconnect:
            pass
        finally:
            clients.discard(websocket)
            pump_task.cancel()

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
    _main._textual_esc_check_fn = lambda: False
    _main._textual_poll_human_input_fn = bridge.poll_interrupt

    _main._textual_emit_content_fn   = lambda text, cls="": bridge.emit("token",     text=text, cls=cls)
    _main._textual_emit_reasoning_fn = lambda text, blank=False: bridge.emit("reasoning", text=text)
    _main._textual_emit_todo_fn      = lambda text: bridge.emit("todo_line", text=text)
    _main._textual_emit_flush_fn     = lambda: bridge.emit("flush")

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
