"""
src/web_ui.py — Browser-based UI for common_ai_agent
Single-file FastAPI + SSE backend. No Textual dependency.
Activate via .config: UI_MODE=web
"""

from __future__ import annotations

import asyncio
import json
import os
import queue
import sys
import threading
import time
from pathlib import Path

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>UPD Agent — Web UI</title>
<style>
:root {
  --bg: #0d1117; --bg-input: #161b22; --border: #30363d;
  --accent: #58a6ff; --green: #3fb950; --yellow: #d29922;
  --red: #f85149; --text: #e6edf3; --text-dim: #8b949e; --text-faint: #6e7681;
}
* { box-sizing: border-box; margin: 0; padding: 0; }
body {
  font-family: 'SF Mono', 'Cascadia Code', 'Consolas', monospace;
  background: var(--bg); color: var(--text); height: 100vh;
  display: flex; flex-direction: column; overflow: hidden;
}
#output {
  flex: 1; overflow-y: auto; padding: 12px 16px;
  white-space: pre-wrap; word-break: break-word;
  font-size: 13px; line-height: 1.5;
}
#output .dim { color: var(--text-dim); }
#output .faint { color: var(--text-faint); }
#output .accent { color: var(--accent); }
#output .green { color: var(--green); }
#output .yellow { color: var(--yellow); }
#output .red { color: var(--red); }
#output .bold { font-weight: bold; }
#output .banner {
  color: var(--accent); font-weight: bold; font-size: 14px;
  border-bottom: 1px solid var(--border); padding-bottom: 8px; margin-bottom: 12px;
}
#input-wrap {
  border-top: 1px solid var(--border); background: var(--bg-input);
  padding: 8px 12px; display: flex; gap: 8px; align-items: center;
}
#prompt { color: #7ee787; font-weight: bold; font-size: 14px; }
#input {
  flex: 1; background: transparent; border: none; color: var(--text);
  font-family: inherit; font-size: 13px; outline: none;
}
#input::placeholder { color: var(--text-faint); }
#status {
  padding: 2px 16px; font-size: 11px; color: var(--text-faint);
  background: var(--bg-input); border-top: 1px solid var(--border);
  display: flex; justify-content: space-between;
}
.spinner { animation: spin 1s linear infinite; }
@keyframes spin { to { transform: rotate(360deg); } }
.markdown code { background: #1c2128; padding: 1px 4px; border-radius: 3px; }
.markdown pre { background: #1c2128; padding: 8px 12px; border-radius: 6px; overflow-x: auto; }
</style>
</head>
<body>
<div id="output"><span class="banner">◆ UPD Agent  ─  Web UI</span>
<span class="dim">Type a message and press Enter. /help for commands.</span>
</div>
<div id="input-wrap">
  <span id="prompt">❯</span>
  <input id="input" placeholder="Message UPD Agent..." autofocus autocomplete="off">
</div>
<div id="status"><span id="status-left">⚪ Ready</span><span id="status-right"></span></div>
<script>
const output = document.getElementById('output');
const input = document.getElementById('input');
const statusLeft = document.getElementById('status-left');
const statusRight = document.getElementById('status-right');
let evtSource = null;

function scrollBottom() { output.scrollTop = output.scrollHeight; }

function appendLine(text, cls) {
  const div = document.createElement('div');
  if (cls) div.className = cls;
  div.textContent = text;
  output.appendChild(div);
  scrollBottom();
}

function connectSSE() {
  if (evtSource) evtSource.close();
  evtSource = new EventSource('/stream');
  evtSource.addEventListener('line', e => {
    try {
      const data = JSON.parse(e.data);
      if (data.clear) {
        // flush: clear live area before writing final markdown
        const live = output.querySelectorAll('.live');
        live.forEach(el => el.remove());
      }
      if (data.text !== undefined) {
        appendLine(data.text, (data.cls || '') + ' live');
      }
      if (data.status) statusLeft.textContent = data.status;
      if (data.tokens) statusRight.textContent = data.tokens;
    } catch(_) {}
  });
  evtSource.addEventListener('done', () => {
    statusLeft.textContent = '⚪ Ready';
    input.disabled = false; input.focus();
    // Remove 'live' class so content persists (not cleared by next flush)
    const live = output.querySelectorAll('.live');
    live.forEach(el => el.classList.remove('live'));
  });
  evtSource.onerror = () => { setTimeout(connectSSE, 1000); };
}

input.addEventListener('keydown', e => {
  if (e.key === 'Enter' && input.value.trim()) {
    const text = input.value.trim();
    input.value = '';
    input.disabled = true;
    statusLeft.textContent = '⏳ Thinking...';
    fetch('/submit', { method: 'POST', body: text }).catch(() => {});
  }
});

connectSSE();
scrollBottom();
</script>
</body>
</html>
"""


class _WebBridge:
    """Replaces InputBridge for web mode. Queues input from HTTP POST."""

    def __init__(self):
        self._q: queue.Queue[str] = queue.Queue()
        self._interrupt_q: queue.Queue[str] = queue.Queue()
        self.agent_running: bool = False

    def get_input(self, prompt: str = "") -> str:
        return self._q.get()

    def poll_interrupt(self):
        try:
            return self._interrupt_q.get_nowait()
        except queue.Empty:
            return None

    def submit(self, text: str) -> None:
        self._q.put(text)

    def submit_interrupt(self, text: str) -> None:
        self._interrupt_q.put(text)


class _SSEQueue:
    """Thread-safe async queue for SSE events."""

    def __init__(self):
        self._q: asyncio.Queue = asyncio.Queue()

    def put_nowait(self, event: str, data: str) -> None:
        try:
            self._q.put_nowait(f"event: {event}\ndata: {data}\n\n")
        except asyncio.QueueFull:
            pass

    async def get(self) -> str:
        return await self._q.get()


def create_app():
    """Build the FastAPI app with all routes."""
    try:
        from fastapi import FastAPI, Request, Response
        from fastapi.responses import HTMLResponse, StreamingResponse
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(title="UPD Agent Web UI")
    bridge = _WebBridge()
    sse_queue = _SSEQueue()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML

    @app.post("/submit")
    async def submit(request: Request):
        text = (await request.body()).decode("utf-8", errors="replace").strip()
        if text:
            if bridge.agent_running:
                bridge.submit_interrupt(text)
            else:
                bridge.submit(text)
        return {"ok": True}

    @app.get("/stream")
    async def stream():
        async def _gen():
            while True:
                data = await sse_queue.get()
                yield data
        return StreamingResponse(_gen(), media_type="text/event-stream",
                                 headers={"Cache-Control": "no-cache",
                                          "X-Accel-Buffering": "no"})

    # Wire up the agent callbacks that main.py expects
    def _emit_line(text: str, cls: str = ""):
        sse_queue.put_nowait("line", json.dumps({"text": text, "cls": cls}))

    def _emit_flush():
        sse_queue.put_nowait("line", json.dumps({"clear": True}))

    def _emit_done():
        sse_queue.put_nowait("done", "{}")

    # Store bridge + callbacks so run_web_ui() can wire them into main.py
    app.state.bridge = bridge
    app.state.sse_queue = sse_queue
    app.state.emit_line = _emit_line
    app.state.emit_flush = _emit_flush
    app.state.emit_done = _emit_done

    return app


def run_web_ui(port: int = 8080):
    """Start the web UI server and run the agent.

    This wires the web bridge into main.py's _textual_* callbacks so the
    existing agent code works unchanged — output goes to SSE, input
    comes from HTTP POST.
    """
    import uvicorn
    import main as _main

    app = create_app()
    bridge = app.state.bridge

    # Wire ALL textual callbacks that main.py expects
    _main._textual_input_fn = bridge.get_input
    _main._textual_esc_check_fn = lambda: False

    # Streaming output → SSE
    _main._textual_emit_content_fn = app.state.emit_line
    _main._textual_emit_reasoning_fn = lambda text, blank=False: app.state.emit_line(text, "dim")
    _main._textual_emit_todo_fn = lambda text: app.state.emit_line(text, "dim")
    _main._textual_emit_flush_fn = app.state.emit_flush

    # Context/tokens — update SSE status bar
    def _ctx_update(tokens, max_tok):
        app.state.sse_queue.put_nowait("line", json.dumps({
            "tokens": f"✽ {tokens/1000:.0f}k / {max_tok/1000:.0f}k tokens"
        }))
    _main._textual_emit_context_fn = _ctx_update
    _main._textual_emit_token_fn = lambda in_tok, cache_tok, out_tok: None  # skip cost for now

    # Human-in-the-loop: poll interrupt queue
    _main._textual_poll_human_input_fn = bridge.poll_interrupt

    # Agent running state
    def _set_running(val: bool):
        bridge.agent_running = val
    _main._textual_set_agent_running_fn = _set_running

    # Run agent in background thread
    def _run_agent():
        # Let _textual_set_agent_running_fn manage the running flag —
        # setting it too early causes all /submit to route to interrupt queue
        try:
            _main.chat_loop()
        except Exception as e:
            app.state.emit_line(f"[ERROR] {e}", "red")
        finally:
            bridge.agent_running = False
            app.state.emit_done()

    agent_thread = threading.Thread(target=_run_agent, daemon=True)
    agent_thread.start()

    print(f"\n  Web UI → http://localhost:{port}\n")
    uvicorn.run(app, host="0.0.0.0", port=port, log_level="warning")
