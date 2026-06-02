"""
src/web_ui.py — Browser-based UI for common_ai_agent
Single-file FastAPI + SSE backend. No Textual dependency.
Activate via .config: UI_MODE=web
"""

from __future__ import annotations

import asyncio
import json
import queue
import sys
import threading

HTML = r"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>ATLAS — Web UI</title>
<script src="https://unpkg.com/marked@9/marked.min.js"></script>
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
.md-block { white-space: normal; line-height: 1.6; }
.md-block table { border-collapse: collapse; margin: 4px 0; }
.md-block th, .md-block td { border: 1px solid var(--border); padding: 4px 10px; text-align: left; }
.md-block th { background: var(--bg-input); }
.md-block code { background: #1c2128; padding: 1px 5px; border-radius: 3px; font-family: inherit; font-size: 12px; }
.md-block pre { background: #1c2128; padding: 8px 12px; border-radius: 6px; overflow-x: auto; margin: 4px 0; white-space: pre; }
.md-block pre code { background: none; padding: 0; }
.md-block p { margin: 2px 0; }
.md-block ul, .md-block ol { padding-left: 20px; margin: 2px 0; }
.md-block h1, .md-block h2, .md-block h3 { color: var(--accent); margin: 6px 0 2px; font-size: inherit; }
</style>
</head>
<body>
<div id="output"><span class="banner">◆ ATLAS  ─  Web UI</span>
<span class="dim">Type a message and press Enter. /help for commands.</span>
</div>
<div id="input-wrap">
  <span id="prompt">❯</span>
  <input id="input" placeholder="Message ATLAS..." autofocus autocomplete="off">
</div>
<div id="status"><span id="status-left">⚪ Ready</span><span id="status-right"></span></div>
<script>
marked.use({ breaks: true, gfm: true });

const output = document.getElementById('output');
const input = document.getElementById('input');
const statusLeft = document.getElementById('status-left');
const statusRight = document.getElementById('status-right');
let evtSource = null;
let liveBuffer = '';
let liveDiv = null;

function scrollBottom() { output.scrollTop = output.scrollHeight; }

function getLiveDiv() {
  if (!liveDiv) {
    liveDiv = document.createElement('div');
    liveDiv.className = 'md-block live';
    output.appendChild(liveDiv);
  }
  return liveDiv;
}

function renderLive() {
  getLiveDiv().innerHTML = marked.parse(liveBuffer);
  scrollBottom();
}

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
        liveBuffer = '';
        if (liveDiv) { liveDiv.remove(); liveDiv = null; }
      }
      if (data.text !== undefined) {
        const cls = data.cls || '';
        if (cls && (cls.includes('dim') || cls.includes('accent') || cls.includes('yellow') || cls.includes('red') || cls.includes('green'))) {
          // Structural/status lines → styled plain-text divs
          appendLine(data.text, cls + ' live');
        } else {
          // Content lines → accumulate and render as markdown
          liveBuffer += data.text + '\n';
          renderLive();
        }
      }
      if (data.status) statusLeft.textContent = data.status;
      if (data.tokens) statusRight.textContent = data.tokens;
    } catch(_) {}
  });
  evtSource.addEventListener('done', () => {
    statusLeft.textContent = '⚪ Ready';
    input.disabled = false; input.focus();
    liveBuffer = '';
    liveDiv = null;
    output.querySelectorAll('.live').forEach(el => el.classList.remove('live'));
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
    """Thread-safe queue for SSE events — works across sync threads and async."""

    def __init__(self):
        self._q: queue.Queue = queue.Queue()

    def put_nowait(self, event: str, data: str) -> None:
        self._q.put_nowait(f"event: {event}\ndata: {data}\n\n")

    async def get(self) -> str:
        # Bridge sync queue → async via run_in_executor
        loop = asyncio.get_event_loop()
        return await loop.run_in_executor(None, self._q.get)


def create_app():
    """Build the FastAPI app with all routes."""
    try:
        from fastapi import FastAPI
        from fastapi.params import Body
        from fastapi.responses import HTMLResponse, StreamingResponse
    except ImportError:
        print("ERROR: fastapi not installed. Run: pip install fastapi uvicorn")
        sys.exit(1)

    app = FastAPI(title="ATLAS Web UI")
    bridge = _WebBridge()
    sse_queue = _SSEQueue()

    @app.get("/", response_class=HTMLResponse)
    async def index():
        return HTML

    @app.post("/submit")
    async def submit(body: str = Body("", media_type="text/plain")):
        text = body.strip()
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


def run_web_ui(port: int = 8080, host: str = "0.0.0.0"):
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
    def _ctx_update(tokens, max_tok, **_runtime):
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

    print(f"\n  Web UI → http://{host}:{port}\n")
    uvicorn.run(app, host=host, port=port, log_level="warning")
