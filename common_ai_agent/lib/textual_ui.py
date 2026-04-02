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

_ANSI   = re.compile(r"\x1b\[[0-9;]*[mK]")
_NOISE  = re.compile(r"^[\s•·\-─—=*]+$")
_ITER   = re.compile(r"primary\s+\d+/\d+")
_TOKENS = re.compile(r"(✽|in\s+[\d.]+k?)\s+.*tokens")

# ── Color palette (GitHub-dark inspired) ────────────────────────────────────
_BG         = "#0d1117"
_BG_INPUT   = "#161b22"
_BORDER     = "#30363d"
_BORDER_DIM = "#21262d"
_ACCENT     = "#58a6ff"   # blue
_GREEN      = "#3fb950"   # success
_YELLOW     = "#d29922"   # warning
_RED        = "#f85149"   # error
_TEXT       = "#c9d1d9"   # normal text
_TEXT_DIM   = "#6e7681"   # dim text
_TEXT_FAINT = "#3d444d"   # very dim


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

def _shorten_path(text: str, max_len: int = 76) -> str:
    if len(text) <= max_len:
        return text
    m = re.search(r"(/[^\s)\"']{30,})", text)
    if not m:
        return text
    path = m.group(1)
    parts = path.split("/")
    short = "/…/" + "/".join(parts[-3:]) if len(parts) > 3 else path
    return text.replace(path, short)


# ── App ───────────────────────────────────────────────────────────────────────

class AgentTUI(App):
    TITLE = "common_ai_agent"

    CSS = f"""
    Screen {{
        background: {_BG};
        color: {_TEXT};
    }}

    /* ── Main panel ── */
    #main {{
        width: 1fr;
        height: 1fr;
        background: {_BG};
        scrollbar-size: 1 1;
        scrollbar-color: {_BORDER};
        padding: 0 2;
    }}

    /* ── Sidebar ── */
    #sidebar {{
        width: 48;
        height: 100%;
        dock: right;
        border-left: solid {_BORDER_DIM};
        padding: 0 1;
        background: {_BG};
    }}
    #agent-label {{
        height: auto;
        color: {_ACCENT};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #task-title {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 0 0 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #context {{
        height: auto;
        color: {_TEXT_FAINT};
        padding: 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #todo-header {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #todo {{
        height: 1fr;
        overflow-y: auto;
        padding: 0;
    }}
    #cwd-label {{
        height: auto;
        color: {_TEXT_FAINT};
        padding: 1 0 0 0;
        border-top: solid {_BORDER_DIM};
        dock: bottom;
    }}

    /* ── Status bar ── */
    #statusbar {{
        height: 1;
        dock: bottom;
        background: {_BG_INPUT};
        color: {_TEXT_FAINT};
        padding: 0 2;
    }}

    /* ── Input ── */
    Input {{
        height: 3;
        dock: bottom;
        background: {_BG_INPUT};
        border: none;
        border-top: solid {_BORDER_DIM};
        padding: 0 2;
        color: {_TEXT};
    }}
    Input:focus {{
        border: none;
        border-top: solid {_BORDER};
        background: {_BG_INPUT};
    }}
    """

    BINDINGS = [("ctrl+q", "quit", "Quit")]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._response_buf = ""
        self._generating = False
        try:
            import config as _cfg
            self._model = getattr(_cfg, "MODEL_NAME", "")
        except Exception:
            self._model = ""

    def compose(self) -> ComposeResult:
        cwd_full = os.getcwd()
        home = os.path.expanduser("~")
        cwd = cwd_full.replace(home, "~") if cwd_full.startswith(home) else cwd_full

        yield RichLog(id="main", highlight=True, wrap=True, markup=False)
        with Vertical(id="sidebar"):
            yield Static("common_ai_agent", id="agent-label")
            yield Static("", id="task-title")
            yield Static("", id="context")
            yield Static("Todo", id="todo-header")
            yield Static("", id="todo")
            yield Static(cwd, id="cwd-label")
        yield Static("", id="statusbar")
        yield Input(placeholder="  ❯ ")

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
            t = RichText()
            t.append(" ◆ ", style=f"bold {_ACCENT}")
            t.append("primary", style=_TEXT_DIM)
            t.append("  ", style="")
            t.append(self._model, style=_TEXT_FAINT)
            t.append("   ctrl+q quit", style=_TEXT_FAINT)
            if extra:
                t.append(f"   {extra}", style=f"italic {_YELLOW}")
            sb.update(t)
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
        # Subtle "AI" gutter marker before response
        marker = RichText()
        marker.append("  ╭ ", style=f"dim {_ACCENT}")
        marker.append("response", style=f"dim {_ACCENT}")
        log.write(marker)
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
        t = RichText()
        t.append(f"\n  {text}", style=f"bold {_ACCENT}")
        log.write(t)
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
        t = RichText()
        t.append(f"  {msg.text}", style=f"italic {_TEXT_DIM}")
        log.write(t)

    def on_main_line(self, msg: MainLine) -> None:
        self._flush_response()
        log = self.query_one("#main", RichLog)
        text = msg.text

        # Iteration header → accent dim separator
        if _ITER.search(text):
            # Extract: "primary N/1000 · model"
            clean = re.sub(r"^[—\-\s]+|[—\-\s]+$", "", text).strip()
            t = RichText()
            t.append("\n  ")
            t.append("─" * 2, style=f"dim {_BORDER}")
            t.append(f"  {clean}  ", style=f"dim {_TEXT_FAINT}")
            t.append("─" * 2, style=f"dim {_BORDER}")
            log.write(t)
            return

        # Token stats → very faint
        if _TOKENS.search(text):
            log.write(RichText(f"  {text.strip()}", style=f"dim {_TEXT_FAINT}"))
            return

        # Shorten long paths
        text = _shorten_path(text)

        try:
            log.write(RichText.from_ansi(text))
        except Exception:
            log.write(RichText(text, style=_TEXT_DIM))

    def on_todo_update(self, msg: TodoUpdate) -> None:
        # Empty signal → clear sidebar
        if not msg.text.strip():
            self.query_one("#task-title", Static).update("")
            self.query_one("#todo", Static).update("")
            return
        clean = _ANSI.sub("", msg.text).strip()
        items: list[tuple[str, str]] = []
        task_title = ""

        for line in clean.splitlines():
            s = line.strip()
            if not s or "── TODO ──" in s:
                continue
            if s.startswith("▶") and not task_title:
                task_title = re.sub(r"^\d+\.\s*", "", s[1:].strip())
            if s.startswith("✅") or s.startswith("👀"):
                items.append(("done", s[1:].strip()))
            elif s.startswith("▶"):
                items.append(("active", s[1:].strip()))
            elif s.startswith("⏸"):
                items.append(("pending", s[1:].strip()))
            elif s.startswith("❌"):
                items.append(("rejected", s[1:].strip()))
            elif s.startswith("•"):
                items.append(("sub", s[1:].strip()))

        if task_title:
            # Update task title area
            t = RichText()
            t.append(task_title, style=_TEXT_DIM)
            self.query_one("#task-title", Static).update(t)

        _MAX = 40
        out = RichText()
        first_active = True
        for kind, label in items:
            if len(label) > _MAX:
                label = label[:_MAX - 1] + "…"
            if kind == "done":
                out.append("  ✓ ", style=f"dim {_TEXT_FAINT}")
                out.append(label + "\n", style=f"dim {_TEXT_FAINT}")
            elif kind == "active":
                if first_active:
                    out.append("  ◆ ", style=f"bold {_GREEN}")
                    out.append(label + "\n", style=f"bold {_TEXT}")
                    first_active = False
                else:
                    out.append("  ◆ ", style=_TEXT_DIM)
                    out.append(label + "\n", style=_TEXT_DIM)
            elif kind == "pending":
                out.append("  ○ ", style=_TEXT_FAINT)
                out.append(label + "\n", style=_TEXT_FAINT)
            elif kind == "rejected":
                out.append("  ✗ ", style=f"dim {_RED}")
                out.append(label + "\n", style=f"dim {_RED}")
            else:
                out.append("    · ", style=f"dim {_TEXT_FAINT}")
                out.append(label + "\n", style=f"dim {_TEXT_FAINT}")

        self.query_one("#todo", Static).update(out)
