"""
lib/textual_ui.py — OpenCode-style Textual TUI for common_ai_agent
"""

from __future__ import annotations

import os
import queue
import re
import sys
from typing import Callable

from rich.markdown import Markdown as _RichMarkdown
from rich.markdown import Heading as _RichHeading
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

# ── Markdown post-processor ──────────────────────────────────────────────────

def _fix_md(text: str) -> str:
    """Fix common LLM markdown quirks before passing to Rich Markdown renderer.

    1. Lone backtick → triple fence (LLM sometimes writes ` instead of ```)
    2. Compact separators: |-|-| → |---|---| (Rich needs at least 3 dashes)
    3. Inline tables: '| A | B | | C | D |' → split into proper rows
    4. Blank lines around code fences so Rich parses them as blocks
    """
    lines: list[str] = []
    for line in text.splitlines():
        # Fix lone backtick used as fence opener/closer
        if line.strip() == "`":
            lines.append("```")
            continue

        # Expand compact table separators: |-| or |:-:| → |---|
        if re.match(r"^\|[-|: ]+\|$", line) and "---" not in line:
            parts = [c for c in line.split("|") if c]
            if all(re.match(r"^[:\-]+$", p.strip()) for p in parts):
                lines.append("|" + "|".join("---" for _ in parts) + "|")
                continue

        # Split inline table rows: '| A | B | | C | D |' on '| |' boundaries
        if re.match(r"^\|.+\|\s*\|", line):
            rows = re.split(r"\|\s*\|", line)
            for i, row in enumerate(rows):
                row = row.strip()
                if not row:
                    continue
                if not row.startswith("|"):
                    row = "| " + row
                if not row.endswith("|"):
                    row = row + " |"
                lines.append(row)
                if i == 0:
                    cols = row.count("|") - 1
                    lines.append("|" + "|".join(["---"] * cols) + "|")
            continue

        lines.append(line)

    # Ensure blank lines around code fences
    out: list[str] = []
    for i, line in enumerate(lines):
        if line.startswith("```"):
            if out and out[-1].strip():
                out.append("")
        out.append(line)
        if line.startswith("```") and i + 1 < len(lines) and lines[i + 1].strip():
            out.append("")
    return "\n".join(out)


# ── Left-aligned Markdown headings ───────────────────────────────────────────

class _LeftHeading(_RichHeading):
    """Override Rich Heading to render left-aligned instead of centered."""
    def __rich_console__(self, console, options):  # type: ignore[override]
        text = self.text
        text.justify = "left"
        if self.tag == "h1":
            yield RichText()
            yield text
            yield RichText()
        else:
            yield text

class _LeftMarkdown(_RichMarkdown):
    elements = {**_RichMarkdown.elements, "heading_open": _LeftHeading}


# ── Color palette (GitHub-dark inspired) ────────────────────────────────────
_BG         = "#0d1117"
_BG_INPUT   = "#161b22"
_BORDER     = "#484f58"   # brighter border
_BORDER_DIM = "#30363d"   # brighter dim border
_ACCENT     = "#58a6ff"   # blue
_GREEN      = "#3fb950"   # success
_YELLOW     = "#d29922"   # warning
_RED        = "#f85149"   # error
_TEXT       = "#e6edf3"   # normal text (brighter)
_TEXT_DIM   = "#8b949e"   # dim text (brighter)
_TEXT_FAINT = "#6e7681"   # very dim (was #3d444d)


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

class ContextUpdate(Message):
    def __init__(self, tokens: int, max_tokens: int, skill: str = "") -> None:
        self.tokens = tokens
        self.max_tokens = max_tokens
        self.skill = skill
        super().__init__()

class FlushResponse(Message):
    """Sent by worker after LLM stream ends to ensure content panel is rendered."""
    pass


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
        color: {_TEXT};
        padding: 0 0 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #model-header {{
        height: auto;
        color: {_TEXT};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #model {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 0 0 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #context-header {{
        height: auto;
        color: {_TEXT};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #context {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 0 0 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #skill-header {{
        height: auto;
        color: {_TEXT};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #skill {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 0 0 1 0;
        border-bottom: solid {_BORDER_DIM};
    }}
    #todo-header {{
        height: auto;
        color: {_TEXT};
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
        color: {_TEXT_DIM};
        padding: 1 0 0 0;
        border-top: solid {_BORDER_DIM};
        dock: bottom;
    }}

    /* ── Status bar ── */
    #statusbar {{
        height: 1;
        dock: bottom;
        background: {_BG_INPUT};
        color: {_TEXT_DIM};
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

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
    ]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._response_buf = ""
        self._generating = False
        self._in_diff = False   # True after a write/replace tool call
        self._active_model = ""
        self._ctx_tokens = 0
        self._ctx_max_tokens = 65536
        self._ctx_skill = ""
        try:
            import config as _cfg
            self._model = getattr(_cfg, "MODEL_NAME", "")
            self._primary_model  = getattr(_cfg, "PRIMARY_MODEL",  self._model)
            self._secondary_model = getattr(_cfg, "SECONDARY_MODEL", self._model)
        except Exception:
            self._model = ""
            self._primary_model = ""
            self._secondary_model = ""

    def compose(self) -> ComposeResult:
        cwd_full = os.getcwd()
        home = os.path.expanduser("~")
        cwd = cwd_full.replace(home, "~") if cwd_full.startswith(home) else cwd_full

        yield RichLog(id="main", highlight=True, wrap=True, markup=False)
        with Vertical(id="sidebar"):
            yield Static("common_ai_agent", id="agent-label")
            yield Static("", id="task-title")
            yield Static("Model", id="model-header")
            yield Static("", id="model")
            yield Static("Context", id="context-header")
            yield Static("", id="context")
            yield Static("Skill", id="skill-header")
            yield Static("", id="skill")
            yield Static("Todo", id="todo-header")
            yield Static("", id="todo")
            yield Static(cwd, id="cwd-label")
        yield Static("", id="statusbar")
        yield Input(placeholder="")

    def on_mount(self) -> None:
        self._update_statusbar()
        self.query_one(Input).focus()
        self._start_agent()
        self.set_timer(0.1, self._init_sidebar)

    def _init_sidebar(self) -> None:
        """Populate sidebar from on-disk state before first agent response."""
        try:
            from lib.todo_tracker import TodoTracker
            import config as _cfg
            from pathlib import Path
            todo_path = Path(_cfg.TODO_FILE)
            if todo_path.exists():
                tt = TodoTracker.load(todo_path)
                if tt and tt.todos:
                    self.post_message(TodoUpdate(tt.format_simple()))
        except Exception:
            pass
        # Show model info immediately (doesn't need agent to have run yet)
        self._refresh_model_sidebar()

    def action_quit(self) -> None:
        # Unblock the worker thread if it's waiting for input, then exit cleanly
        try:
            self._input_bridge.submit("exit")
        except Exception:
            pass
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
            self._run_agent_fn(self)  # passes app instance; textual_main.py wires all callbacks
        finally:
            sys.stdout = _orig

    # ── Response buffer ───────────────────────────────────────────────────────

    def _flush_response(self) -> None:
        if not self._response_buf.strip():
            self._response_buf = ""
            self._generating = False
            return
        from rich.panel import Panel
        log = self.query_one("#main", RichLog)
        # OpenCode-style: response in a subtle bordered panel
        panel = Panel(
            _LeftMarkdown(_fix_md(self._response_buf)),
            title="[dim]assistant[/dim]",
            title_align="left",
            border_style=f"dim {_BORDER_DIM}",
            padding=(0, 1),
            expand=True,
        )
        log.write(panel)
        self._response_buf = ""
        self._generating = False
        self._update_statusbar()

    # ── Input ─────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        if text.lower() in ("quit", "exit", "/quit", "/exit"):
            self.exit()
            return
        self._flush_response()
        log = self.query_one("#main", RichLog)
        # Full-width turn separator (OpenCode style)
        from rich.rule import Rule
        log.write(Rule(style=f"dim {_BORDER_DIM}"))
        # User input line
        t = RichText()
        t.append(f"  {text}", style=f"bold {_ACCENT}")
        log.write(t)
        self._in_diff = False
        self._input_bridge.submit(text)

    # ── Message handlers ───────────────────────────────────────────────────────

    def on_stream_chunk(self, msg: StreamChunk) -> None:
        if not self._generating:
            self._generating = True
            self._update_statusbar("generating…")
        self._response_buf += msg.text + "\n"

    def on_flush_response(self, msg: FlushResponse) -> None:
        """Worker signals stream done — render whatever accumulated in _response_buf."""
        self._flush_response()

    def on_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        if msg.blank:
            return
        log = self.query_one("#main", RichLog)
        t = RichText()
        # OpenCode-style: dim left bar + italic faint text
        t.append("  ┆ ", style=f"dim {_BORDER}")
        t.append(msg.text, style=f"italic {_TEXT_FAINT}")
        log.write(t)

    def on_context_update(self, msg: ContextUpdate) -> None:
        self._ctx_tokens = msg.tokens
        self._ctx_max_tokens = msg.max_tokens
        self._ctx_skill = msg.skill
        self._redraw_context()

    def _redraw_context(self) -> None:
        """Redraw #context (tokens) and #skill widgets from stored state."""
        try:
            t = RichText()
            if self._ctx_max_tokens:
                pct = int(self._ctx_tokens / self._ctx_max_tokens * 100)
                cur_k = f"{self._ctx_tokens / 1000:.1f}k"
                max_k = f"{self._ctx_max_tokens / 1000:.0f}k"
                pct_color = _YELLOW if pct >= 50 else _TEXT_FAINT
                t.append(f"{cur_k} / {max_k}  ", style=_TEXT_DIM)
                t.append(f"{pct}%", style=f"dim {pct_color}")
            self.query_one("#context", Static).update(t)
        except Exception:
            pass
        try:
            s = RichText()
            if self._ctx_skill:
                s.append(self._ctx_skill, style=_ACCENT)
            self.query_one("#skill", Static).update(s)
        except Exception:
            pass

    def _refresh_model_sidebar(self) -> None:
        """Update #model widget with current active model name."""
        try:
            def _short(name: str) -> str:
                return name.split("/")[-1] if "/" in name else name

            active = _short(self._active_model) if self._active_model else _short(self._primary_model)
            t = RichText()
            if active:
                t.append(active, style=_TEXT_DIM)
            self.query_one("#model", Static).update(t)
        except Exception:
            pass

    def on_main_line(self, msg: MainLine) -> None:
        self._flush_response()
        log = self.query_one("#main", RichLog)
        text = msg.text

        # Iteration header — hide from log, extract active model for sidebar
        if _ITER.search(text):
            m_model = re.search(r"[·•]\s*(\S+)\s*$", text)
            if m_model:
                self._active_model = m_model.group(1)
                self._refresh_model_sidebar()
            return

        # Token stats → very faint + update sidebar token count
        if _TOKENS.search(text):
            log.write(RichText(f"  {text.strip()}", style=f"dim {_TEXT_FAINT}"))
            # Parse "sum 26.4k" or "in 26.3k" to update token counter
            m_tok = re.search(r"\bsum\s+([\d.]+)(k?)", text)
            if not m_tok:
                m_tok = re.search(r"\bin\s+([\d.]+)(k?)", text)
            if m_tok:
                val = float(m_tok.group(1))
                if m_tok.group(2) == "k":
                    val *= 1000
                self._ctx_tokens = int(val)
                self._redraw_context()
            return

        # Shorten long paths
        text = _shorten_path(text)

        # ── Color-coded lines ───────────────────────────────────────────────

        # Todo status bar: suppress from main log (shown in sidebar only)
        # Strip ANSI before checking so escape codes don't break the match
        _plain = _ANSI.sub("", text)
        if re.match(r"^\d+;\[(\d+/\d+)\]", _plain):
            return

        # System messages: [Plan Mode], [System], [Error]
        m_sys = re.match(r"^(\[(?:Plan Mode|System|Error|Warning)[^\]]*\])(.*)", text)
        if m_sys:
            tag, rest = m_sys.groups()
            t = RichText()
            if "Error" in tag:
                t.append(f"  {tag}", style=f"bold {_RED}")
            elif "Warning" in tag:
                t.append(f"  {tag}", style=f"bold {_YELLOW}")
            elif "Plan Mode" in tag:
                t.append(f"  {tag}", style=f"bold {_ACCENT}")
            else:
                t.append(f"  {tag}", style=f"dim {_ACCENT}")
            t.append(rest, style=_TEXT_DIM)
            log.write(t)
            return

        # Tool calls: "• tool_name(...)"
        m_tool = re.match(r"^\s*[•·]\s*(\w+)\((.*)$", text)
        if m_tool:
            self._in_diff = False  # reset diff state on every new tool call
            tool_name = m_tool.group(1)
            args_part = m_tool.group(2)
            _READ_TOOLS  = {"read_file","read_lines","grep_file","find_files","list_dir","git_diff","git_status","git_log"}
            _WRITE_TOOLS = {"write_file","write_to_file","replace_in_file","replace_lines","replace_file_content"}
            _EXEC_TOOLS  = {"run_command","background_task","background_output"}
            _TODO_TOOLS  = {"todo_update","todo_write","todo_add","todo_remove"}
            _GIT_TOOLS   = {"git_commit","git_push","git_checkout","git_branch","git_merge","git_stash"}
            if tool_name in _READ_TOOLS:
                color = _ACCENT
            elif tool_name in _WRITE_TOOLS:
                color, self._in_diff = _GREEN, True
            elif tool_name in _EXEC_TOOLS:
                color = "#e3b341"
            elif tool_name in _TODO_TOOLS:
                color = _GREEN
            elif tool_name in _GIT_TOOLS:
                color, self._in_diff = "#bc8cff", True
            else:
                color = _TEXT_DIM
            t = RichText()
            t.append(f"  {tool_name}", style=f"bold {color}")
            t.append(f"({args_part}", style=f"dim {color}")
            log.write(t)
            return

        # Diff lines (after write/replace/git tools)
        if self._in_diff:
            if re.match(r"^\+[^+]", text):
                log.write(RichText(f"  {text}", style=f"bold {_GREEN}"))
                return
            if re.match(r"^-[^-]", text):
                log.write(RichText(f"  {text}", style=f"bold {_RED}"))
                return
            if re.match(r"^@@", text):
                log.write(RichText(f"  {text}", style=f"bold {_ACCENT}"))
                return
            # Non-diff line ends the diff block
            if not re.match(r"^\s*[└|]", text):
                self._in_diff = False

        # Tool result lines: "└ ..."
        if re.match(r"^\s*[└|]", text):
            log.write(RichText(f"  {text.strip()}", style=f"dim {_TEXT_FAINT}"))
            return

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
                out.append("  ✓ ", style=_TEXT_FAINT)
                out.append(label + "\n", style=_TEXT_FAINT)
            elif kind == "active":
                if first_active:
                    out.append("  ◆ ", style=f"bold {_GREEN}")
                    out.append(label + "\n", style=f"bold {_TEXT}")
                    first_active = False
                else:
                    out.append("  ◆ ", style=_TEXT)
                    out.append(label + "\n", style=_TEXT)
            elif kind == "pending":
                out.append("  ○ ", style=_TEXT_DIM)
                out.append(label + "\n", style=_TEXT_DIM)
            elif kind == "rejected":
                out.append("  ✗ ", style=_RED)
                out.append(label + "\n", style=_RED)
            else:
                out.append("    · ", style=_TEXT_FAINT)
                out.append(label + "\n", style=_TEXT_FAINT)

        self.query_one("#todo", Static).update(out)
