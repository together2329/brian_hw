"""
lib/textual_ui.py — OpenCode-style Textual TUI for common_ai_agent

Layout:
  ┌──────────────────────────────────────┬──────────────────────┐
  │ Main panel (75%)                     │ Sidebar (25%)        │
  │                                      │  Task title          │
  │  → Read file.v                       │  29,473 tokens       │
  │    12 lines                          │  15% used            │
  │                                      │                      │
  │  LLM response text...                │  ▼ Todo              │
  │                                      │  [x] Task 1          │
  │  ■ primary · model-name              │  [ ] Task 2          │
  ├──────────────────────────────────────│                      │
  │ > input                              │  ~/cwd               │
  │ primary  model  esc interrupt        └──────────────────────┘
  └──────────────────────────────────────────────────────────────
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


# ── Messages ─────────────────────────────────────────────────────────────────

class MainLine(Message):
    """stdout line → main panel."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

class StreamChunk(Message):
    """LLM streaming token → main panel."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()

class ReasoningChunk(Message):
    """LLM reasoning → main panel (dim)."""
    def __init__(self, text: str, blank: bool = False) -> None:
        self.text = text
        self.blank = blank
        super().__init__()

class TodoUpdate(Message):
    """Todo state → sidebar."""
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
            if clean.strip():
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


# ── App ───────────────────────────────────────────────────────────────────────

class AgentTUI(App):
    TITLE = "common_ai_agent"

    CSS = """
    Screen {
        background: #0f0f0f;
        color: #cccccc;
    }

    /* ── Main content panel ── */
    #main {
        width: 1fr;
        height: 1fr;
        background: #0f0f0f;
        scrollbar-size: 1 1;
        scrollbar-color: #333333;
        padding: 0 1;
    }

    /* ── Right sidebar ── */
    #sidebar {
        width: 26;
        height: 1fr;
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

    /* ── Status bar ── */
    #statusbar {
        height: 1;
        dock: bottom;
        background: #161616;
        color: #555555;
        padding: 0 1;
    }

    /* ── Input ── */
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

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._stream_buf = ""   # accumulates streaming tokens until newline

    def compose(self) -> ComposeResult:
        try:
            import config as _cfg
            model = getattr(_cfg, "MODEL_NAME", "")
        except Exception:
            model = ""

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
        yield Static(
            f" primary  {model}   esc interrupt",
            id="statusbar",
        )
        yield Input(placeholder="> ")

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self._start_agent()

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

    # ── Input ─────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        log = self.query_one("#main", RichLog)
        # Flush any partial stream line
        if self._stream_buf.strip():
            log.write(RichText(self._stream_buf, style="#cccccc"))
            self._stream_buf = ""
        log.write(RichText(f"\n> {text}", style="bold #5f87ff"))
        self._input_bridge.submit(text)

    # ── Message handlers ───────────────────────────────────────────────────────

    def on_stream_chunk(self, msg: StreamChunk) -> None:
        """Buffer streaming tokens; flush on newline."""
        log = self.query_one("#main", RichLog)
        self._stream_buf += msg.text
        # Flush complete lines
        while "\n" in self._stream_buf:
            line, self._stream_buf = self._stream_buf.split("\n", 1)
            log.write(RichText(line, style="#cccccc"))

    def on_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        log = self.query_one("#main", RichLog)
        if msg.blank:
            return
        log.write(RichText(f"  {msg.text}", style="italic #555555"))

    def on_main_line(self, msg: MainLine) -> None:
        """Tool output / system messages — render with ANSI → Rich."""
        log = self.query_one("#main", RichLog)
        try:
            log.write(RichText.from_ansi(msg.text))
        except Exception:
            log.write(RichText(msg.text, style="#888888"))

    def on_todo_update(self, msg: TodoUpdate) -> None:
        clean = _ANSI.sub("", msg.text).strip()
        lines = []
        task_title = ""
        for line in clean.splitlines():
            s = line.strip()
            if not s or "── TODO ──" in s:
                continue
            # Extract task title from in_progress item
            if s.startswith("▶") and not task_title:
                task_title = s[1:].strip()
                # Remove leading "N." if present
                task_title = re.sub(r"^\d+\.\s*", "", task_title)
            # Format each line
            if s.startswith("✅"):
                lines.append(f"[x] {s[1:].strip()}")
            elif s.startswith("▶"):
                lines.append(f"[ ] {s[1:].strip()}")   # active
            elif s.startswith("⏸"):
                lines.append(f"[ ] {s[1:].strip()}")   # pending
            elif s.startswith("•"):
                lines.append(f"    {s}")

        # Update task title in sidebar
        if task_title:
            self.query_one("#task-title", Static).update(task_title)

        # Render todo list with styles
        rendered = []
        for line in lines:
            if line.startswith("[x]"):
                rendered.append(f"[dim]{line}[/dim]")
            elif line.startswith("[ ]") and not rendered:
                # First pending = active task
                rendered.append(f"[bold #ffffff]{line}[/bold #ffffff]")
            elif line.startswith("[ ]"):
                rendered.append(f"[#555555]{line}[/#555555]")
            else:
                rendered.append(f"[dim #444444]{line}[/dim #444444]")

        self.query_one("#todo", Static).update("\n".join(rendered))
