"""
lib/textual_ui.py — OpenCode-style Textual TUI for common_ai_agent
"""

from __future__ import annotations

import os
import queue
import re
import sys
from typing import Callable

from rich.text import Text as RichText
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, RichLog, Static
from textual import work

_ANSI = re.compile(r"\x1b\[[0-9;]*[mK]")

# Lines that are pure noise — single symbols, bare bullets, etc.
_NOISE = re.compile(r"^[\s•·\-─—=*]+$")

# Iteration header: "— primary N/1000 · model —"
_ITER_HDR = re.compile(r"primary\s+\d+/\d+")

# Token stats: "✽ in Xk · out Xk · sum Xk tokens · Xs"
_TOKEN_STATS = re.compile(r"(✽|in\s+[\d.]+k?)\s+.*tokens")


# ── Messages ─────────────────────────────────────────────────────────────────

class MainLine(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

class StreamChunk(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

class ReasoningChunk(Message):
    def __init__(self, text: str, blank: bool = False) -> None:
        self.text = text
        self.blank = blank
        super().__init__()

class TodoUpdate(Message):
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


# ── stdout capture ────────────────────────────────────────────────────────────

class TextualCapture:
    def __init__(self, app: App) -> None:
        self._app = app
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            clean = _ANSI.sub("", line)
            # Skip blank lines and pure-noise lines (stray bullets, etc.)
            if not clean.strip() or _NOISE.match(clean.strip()):
                continue
            self._app.post_message(MainLine(clean))
        return len(text)

    def flush(self) -> None: pass
    def isatty(self) -> bool: return False
    def fileno(self) -> int: raise OSError("no fd")


# ── Input bridge ──────────────────────────────────────────────────────────────

class InputBridge:
    def __init__(self) -> None:
        self._q: queue.Queue[str] = queue.Queue()

    def get_input(self, prompt: str = "") -> str:
        return self._q.get()

    def submit(self, text: str) -> None:
        self._q.put(text)


# ── Helpers ───────────────────────────────────────────────────────────────────

def _shorten_path(text: str, max_len: int = 72) -> str:
    """Shorten a line containing a long absolute path using …/tail."""
    if len(text) <= max_len:
        return text
    # Find the longest /…/ segment
    m = re.search(r"(/[^\s)\"']{30,})", text)
    if not m:
        return text
    path = m.group(1)
    parts = path.split("/")
    # Keep last 3 path components
    short = "/…/" + "/".join(parts[-3:]) if len(parts) > 3 else path
    return text.replace(path, short)


# ── App ───────────────────────────────────────────────────────────────────────

class AgentTUI(App):
    TITLE = "common_ai_agent"

    CSS = """
    Screen {
        background: #0f0f0f;
        color: #cccccc;
    }

    #main {
        width: 1fr;
        height: 1fr;
        background: #0f0f0f;
        scrollbar-size: 1 1;
        scrollbar-color: #333333;
        padding: 0 1;
    }

    #sidebar {
        width: 32;
        height: 100%;
        dock: right;
        border-left: solid #222222;
        padding: 0 1;
        background: #0f0f0f;
    }
    #task-title {
        height: auto;
        color: #aaaaaa;
        padding: 0 0 1 0;
        border-bottom: solid #222222;
    }
    #context {
        height: auto;
        color: #555555;
        padding: 1 0;
        border-bottom: solid #222222;
    }
    #todo-header {
        height: auto;
        color: #888888;
        padding: 1 0 0 0;
    }
    #todo {
        height: 1fr;
        color: #bbbbbb;
        overflow-y: auto;
        padding: 0;
    }
    #cwd-label {
        height: auto;
        color: #444444;
        padding: 1 0 0 0;
        border-top: solid #222222;
        dock: bottom;
    }

    #statusbar {
        height: 1;
        dock: bottom;
        background: #161616;
        color: #555555;
        padding: 0 1;
    }

    Input {
        height: 3;
        dock: bottom;
        background: #111111;
        border: none;
        border-top: solid #222222;
        padding: 0 1;
        color: #eeeeee;
    }
    Input:focus {
        border: none;
        border-top: solid #3a3a3a;
        background: #131313;
    }
    """

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._response_buf = ""
        self._generating = False
        # Cache model name for status bar
        try:
            import config as _cfg
            self._model = getattr(_cfg, "MODEL_NAME", "")
        except Exception:
            self._model = ""

    def compose(self) -> ComposeResult:
        cwd_full = os.getcwd()
        home = os.path.expanduser("~")
        cwd = cwd_full.replace(home, "~") if cwd_full.startswith(home) else cwd_full

        yield RichLog(id="main", highlight=False, wrap=True, markup=False)
        with Vertical(id="sidebar"):
            yield Static("", id="task-title")
            yield Static("", id="context")
            yield Static("▼ Todo", id="todo-header")
            yield Static("", id="todo")
            yield Static(cwd, id="cwd-label")
        yield Static("", id="statusbar")
        yield Input(placeholder="> ")

    def on_mount(self) -> None:
        self._update_statusbar()
        self.query_one(Input).focus()
        self._start_agent()

    def action_quit(self) -> None:
        self.exit()

    # ── Status bar ────────────────────────────────────────────────────────────

    def _update_statusbar(self, extra: str = "") -> None:
        try:
            sb = self.query_one("#statusbar", Static)
            base = f" primary  {self._model}   esc interrupt   ctrl+q quit"
            sb.update(RichText(f"{base}   {extra}" if extra else base, style="#555555"))
        except Exception:
            pass

    # ── Agent worker ─────────────────────────────────────────────────────────

    @work(exclusive=True, thread=True)
    def _start_agent(self) -> None:
        _orig = sys.stdout
        sys.stdout = TextualCapture(self)
        try:
            self._run_agent_fn(
                input_fn=self._input_bridge.get_input,
                emit_content_fn=lambda line: self.post_message(StreamChunk(line)),
                emit_reasoning_fn=lambda line, blank=False: self.post_message(ReasoningChunk(line, blank)),
                emit_todo_fn=lambda text: self.post_message(TodoUpdate(text)),
            )
        finally:
            sys.stdout = _orig

    # ── Response buffer ───────────────────────────────────────────────────────

    def _flush_response(self) -> None:
        if not self._response_buf.strip():
            self._response_buf = ""
            self._generating = False
            return
        from rich.markdown import Markdown
        log = self.query_one("#main", RichLog)
        log.write(Markdown(self._response_buf))
        self._response_buf = ""
        self._generating = False
        self._update_statusbar()

    # ── Input ─────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        self._flush_response()
        log = self.query_one("#main", RichLog)
        log.write(RichText(f"\n> {text}", style="bold #5f87ff"))
        self._input_bridge.submit(text)

    # ── Message handlers ───────────────────────────────────────────────────────

    def on_stream_chunk(self, msg: StreamChunk) -> None:
        if not self._generating:
            self._generating = True
            self._update_statusbar("generating…")
        self._response_buf += msg.text + "\n"

    def on_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        if msg.blank:
            return
        log = self.query_one("#main", RichLog)
        log.write(RichText(f"  {msg.text}", style="italic #555555"))

    def on_main_line(self, msg: MainLine) -> None:
        """System/tool output — flush pending response first, then style the line."""
        self._flush_response()
        log = self.query_one("#main", RichLog)
        text = msg.text

        # Iteration header → dim separator style
        if _ITER_HDR.search(text):
            log.write(RichText(""))
            log.write(RichText(text, style="dim #444444"))
            return

        # Token stats → dim right-aligned style
        if _TOKEN_STATS.search(text):
            log.write(RichText(text.strip(), style="dim #3a3a3a"))
            return

        # Shorten long paths (e.g. Read(...) lines)
        text = _shorten_path(text)

        try:
            log.write(RichText.from_ansi(text))
        except Exception:
            log.write(RichText(text, style="#888888"))

    def on_todo_update(self, msg: TodoUpdate) -> None:
        clean = _ANSI.sub("", msg.text).strip()
        lines = []
        task_title = ""
        for line in clean.splitlines():
            s = line.strip()
            if not s or "── TODO ──" in s:
                continue
            if s.startswith("▶") and not task_title:
                task_title = re.sub(r"^\d+\.\s*", "", s[1:].strip())
            if s.startswith("✅") or s.startswith("👀"):
                lines.append(("[x]", s[1:].strip()))
            elif s.startswith("▶"):
                lines.append(("[>]", s[1:].strip()))
            elif s.startswith("⏸"):
                lines.append(("[ ]", s[1:].strip()))
            elif s.startswith("❌"):
                lines.append(("[-]", s[1:].strip()))
            elif s.startswith("•"):
                lines.append(("  •", s[1:].strip()))

        if task_title:
            self.query_one("#task-title", Static).update(task_title)

        _MAX = 28  # max chars per todo line (sidebar width - padding)
        out = RichText()
        first_active = True
        for marker, label in lines:
            # Truncate label to fit sidebar
            if len(label) > _MAX:
                label = label[:_MAX - 1] + "…"
            line_str = f"{marker} {label}\n"
            if marker == "[x]":
                out.append(line_str, style="dim #555555")
            elif marker == "[>]":
                style = "bold white" if first_active else "#888888"
                out.append(line_str, style=style)
                first_active = False
            elif marker == "[ ]":
                out.append(line_str, style="#666666")
            elif marker == "[-]":
                out.append(line_str, style="dim red")
            else:
                out.append(line_str, style="dim #444444")

        self.query_one("#todo", Static).update(out)
