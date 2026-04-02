"""
lib/textual_ui.py — Textual TUI for common_ai_agent

Layout:
  ┌─────────────────────────────────────────────────────┐
  │ Header                                              │
  ├──────────────────────────────┬──────────────────────┤
  │ Markdown (좌) — LLM 스트리밍 │ Todo Panel (우상)    │
  │                              ├──────────────────────┤
  │                              │ Log Panel (우하)      │
  ├──────────────────────────────┴──────────────────────┤
  │ Input: >                                            │
  └─────────────────────────────────────────────────────┘

Usage:
  from lib.textual_ui import AgentTUI
  AgentTUI(run_agent_fn).run()

  run_agent_fn(input_fn, emit_content_fn, emit_reasoning_fn, emit_todo_fn)
  is called in a background thread.
"""

from __future__ import annotations

import queue
import re
import sys
from typing import Callable

from textual.app import App, ComposeResult
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.widgets import Footer, Header, Input, LoadingIndicator, Log, Markdown, Static
from textual import work


# ---------------------------------------------------------------------------
# Message classes (background thread → UI event loop)
# ---------------------------------------------------------------------------

class StreamChunk(Message):
    """Streaming LLM content chunk → Markdown panel."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class ReasoningChunk(Message):
    """LLM reasoning/thought → Log panel (dim italic)."""
    def __init__(self, text: str, blank: bool = False) -> None:
        self.text = text
        self.blank = blank
        super().__init__()


class LogLine(Message):
    """Generic stdout line → Log panel."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class TodoUpdate(Message):
    """Todo tracker state changed → Todo panel."""
    def __init__(self, text: str) -> None:
        self.text = text
        super().__init__()


class SpinnerState(Message):
    """Show/hide the loading indicator."""
    def __init__(self, active: bool) -> None:
        self.active = active
        super().__init__()


# ---------------------------------------------------------------------------
# stdout capture  (tool results, system messages → Log panel)
# ---------------------------------------------------------------------------

_ANSI_ESCAPE = re.compile(r"\x1b\[[0-9;]*m")


class TextualCapture:
    """Replaces sys.stdout; routes lines to Textual's LogLine messages."""

    def __init__(self, app: App) -> None:
        self._app = app
        self._buf = ""

    def write(self, text: str) -> int:
        self._buf += text
        while "\n" in self._buf:
            line, self._buf = self._buf.split("\n", 1)
            clean = _ANSI_ESCAPE.sub("", line)
            self._app.post_message(LogLine(clean))
        return len(text)

    def flush(self) -> None:
        pass

    def isatty(self) -> bool:
        return False

    def fileno(self) -> int:
        raise OSError("TextualCapture has no file descriptor")


# ---------------------------------------------------------------------------
# Input bridge  (Textual Input widget → blocking get() in worker thread)
# ---------------------------------------------------------------------------

class InputBridge:
    """Thread-safe bridge: worker thread blocks on get(), UI pushes via submit()."""

    def __init__(self) -> None:
        self._q: queue.Queue[str] = queue.Queue()

    def get_input(self, prompt: str = "") -> str:
        """Called from worker thread — blocks until user submits."""
        return self._q.get()

    def submit(self, text: str) -> None:
        """Called from Textual event loop — unblocks get_input()."""
        self._q.put(text)


# ---------------------------------------------------------------------------
# Main Textual Application
# ---------------------------------------------------------------------------

class AgentTUI(App):
    """
    Textual TUI shell for common_ai_agent.

    Args:
        run_agent_fn: Callable that takes
            (input_fn, emit_content_fn, emit_reasoning_fn, emit_todo_fn)
            and runs the agent loop (blocking — runs in a worker thread).
    """

    CSS = """
    Screen {
        layers: base;
    }
    Input {
        dock: bottom;
        height: 3;
    }
    #left {
        width: 65%;
        dock: left;
        border: solid $primary-darken-2;
    }
    #right {
        width: 35%;
        dock: right;
    }
    #todo {
        height: 40%;
        border: solid yellow;
        background: $surface-darken-1;
        overflow-y: auto;
    }
    #log {
        height: 60%;
        border: solid $panel;
    }
    LoadingIndicator {
        display: none;
        dock: bottom;
        height: 1;
        layer: base;
    }
    LoadingIndicator.active {
        display: block;
    }
    """

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._md_buf = ""

    def compose(self) -> ComposeResult:
        yield Header(show_clock=True)
        yield Markdown("*Agent 대기 중...*", id="left")
        with Vertical(id="right"):
            yield Static("*Todo 없음*", id="todo", markup=True)
            yield Log(id="log", highlight=True)
        yield LoadingIndicator()
        yield Input(placeholder="> 명령을 입력하세요")
        yield Footer()

    def on_mount(self) -> None:
        self.query_one(Input).focus()
        self._start_agent()

    @work(exclusive=True, thread=True)
    def _start_agent(self) -> None:
        """Run the agent loop in a background thread."""
        _orig_stdout = sys.stdout
        sys.stdout = TextualCapture(self)
        try:
            self._run_agent_fn(
                input_fn=self._input_bridge.get_input,
                emit_content_fn=lambda line: self.post_message(StreamChunk(line)),
                emit_reasoning_fn=lambda line, blank=False: self.post_message(ReasoningChunk(line, blank)),
                emit_todo_fn=lambda text: self.post_message(TodoUpdate(text)),
            )
        finally:
            sys.stdout = _orig_stdout

    # ── User input ─────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        # Echo to Log
        self.query_one("#log", Log).write_line(f"[bold cyan]> {text}[/]")
        # Reset Markdown buffer on new turn
        self._md_buf = ""
        # Unblock worker thread
        self._input_bridge.submit(text)

    # ── Message handlers (run on UI event loop — thread-safe) ───────────────

    async def on_stream_chunk(self, msg: StreamChunk) -> None:
        self._md_buf += msg.text + "\n"
        await self.query_one("#left", Markdown).update(self._md_buf)

    def on_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        log = self.query_one("#log", Log)
        if msg.blank:
            log.write_line("")
        else:
            log.write_line(f"[dim italic]{msg.text}[/]")

    def on_log_line(self, msg: LogLine) -> None:
        if msg.text.strip():
            self.query_one("#log", Log).write_line(msg.text)

    def on_todo_update(self, msg: TodoUpdate) -> None:
        # Strip ANSI codes (format_simple uses Color.*) — already done in capture
        clean = _ANSI_ESCAPE.sub("", msg.text)
        self.query_one("#todo", Static).update(clean)

    def on_spinner_state(self, msg: SpinnerState) -> None:
        ind = self.query_one(LoadingIndicator)
        if msg.active:
            ind.add_class("active")
        else:
            ind.remove_class("active")
