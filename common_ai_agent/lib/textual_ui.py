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
from rich.table import Table as RichTable
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

def _is_table_row(line: str) -> bool:
    s = line.strip()
    return s.startswith("|") and s.endswith("|") and len(s) > 2

def _is_sep_row(line: str) -> bool:
    s = line.strip()
    return bool(s.startswith("|") and re.match(r"^\|[\s|:\-]+\|$", s))

def _col_count(line: str) -> int:
    return max(1, line.strip().strip("|").count("|") + 1)

def _make_sep(ncols: int) -> str:
    return "|" + "|".join(" --- " for _ in range(ncols)) + "|"

def _fix_table_block(rows: list) -> list:
    """Normalise a contiguous block of | lines into a valid GFM table.
    - Ensures separator row exists at position 1
    - Pads all rows to the same column count
    - Normalises any existing sep row to ` --- `
    """
    if not rows:
        return rows

    # Detect separator row among first three rows
    sep_idx = next((i for i in range(min(3, len(rows))) if _is_sep_row(rows[i])), None)

    if sep_idx is None:
        # No separator found — insert after first row
        ncols = _col_count(rows[0])
        rows = [rows[0], _make_sep(ncols)] + rows[1:]
        sep_idx = 1
    else:
        # Normalise existing separator
        ncols = _col_count(rows[0])
        rows[sep_idx] = _make_sep(ncols)

    # Pad every row to ncols columns
    fixed = []
    for i, row in enumerate(rows):
        s = row.strip()
        cells = s.strip("|").split("|")
        # Pad or trim to ncols
        while len(cells) < ncols:
            cells.append("")
        cells = cells[:ncols]
        if i == sep_idx:
            fixed.append("|" + "|".join(" --- " for _ in cells) + "|")
        else:
            fixed.append("|" + "|".join(f" {c.strip()} " for c in cells) + "|")
    return fixed


def _fix_md(text: str) -> str:
    """Fix common LLM markdown quirks before passing to Rich Markdown renderer.

    1. Lone backtick → triple fence
    2. Table blocks: auto-insert separator, normalise sep cells, add blank lines around
    3. Split inline tables ('| A | B | | C | D |') into separate rows
    4. Blank lines around code fences
    5. Collapse 2+ consecutive blank lines → 1
    """
    # ── Pass 1: per-line pre-fixes (lone backtick, inline table split) ────────
    pre: list[str] = []
    for line in text.splitlines():
        if line.strip() == "`":
            pre.append("```")
            continue
        # Split inline table rows joined with '| |'
        if re.match(r"^\|.+\|\s*\|", line) and not _is_sep_row(line):
            parts = re.split(r"\|\s*\|", line)
            merged: list[str] = []
            for k, part in enumerate(parts):
                part = part.strip()
                if not part:
                    continue
                if not part.startswith("|"):
                    part = "| " + part
                if not part.endswith("|"):
                    part = part + " |"
                merged.append(part)
            if len(merged) > 1:
                pre.extend(merged)
                continue
        pre.append(line)

    # ── Pass 2: table block fixing + blank-line insertion ─────────────────────
    out: list[str] = []
    i = 0
    while i < len(pre):
        line = pre[i]

        if _is_table_row(line):
            # Collect the whole table block
            block: list[str] = []
            j = i
            while j < len(pre) and _is_table_row(pre[j]):
                block.append(pre[j])
                j += 1

            # Blank line before table
            if out and out[-1].strip():
                out.append("")

            out.extend(_fix_table_block(block))

            # Blank line after table
            if j < len(pre) and pre[j].strip():
                out.append("")

            i = j
            continue

        # Code fence blank-line guard
        if line.startswith("```"):
            if out and out[-1].strip():
                out.append("")

        # Collapse consecutive blank lines
        if not line.strip() and out and not out[-1].strip():
            i += 1
            continue

        out.append(line)

        if line.startswith("```") and i + 1 < len(pre) and pre[i + 1].strip():
            out.append("")

        i += 1

    # ── Pass 3: strip blank lines right before headings (Rich adds its own) ──
    final: list[str] = []
    for line in out:
        if re.match(r"^#{1,6}\s", line) and final and not final[-1].strip():
            final.pop()  # remove blank line before heading
        final.append(line)

    return "\n".join(final)


# ── Left-aligned Markdown headings (compact) ────────────────────────────────

class _LeftHeading(_RichHeading):
    """Override Rich Heading to render left-aligned and compact (no extra blank lines)."""
    def __rich_console__(self, console, options):  # type: ignore[override]
        text = self.text
        text.justify = "left"
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
_ORANGE     = "#e5872d"   # tool action highlight


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
    def __init__(self, tokens: int, max_tokens: int, skill: str = "", mode: str = "") -> None:
        self.tokens = tokens
        self.max_tokens = max_tokens
        self.skill = skill
        self.mode = mode
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
            has_ansi = (clean != line)
            # Skip empty lines; for non-ANSI lines, also skip noise (pure separators)
            if not clean.strip():
                continue
            if not has_ansi and _NOISE.match(clean.strip()):
                continue
            self._app.post_message(MainLine(line))  # pass raw line (preserve ANSI for RichText.from_ansi)
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

def _shorten_path(text: str, max_len: int = 140) -> str:
    if len(text) <= max_len:
        return text
    m = re.search(r"(/[^\s)\"']{40,})", text)
    if not m:
        return text
    path = m.group(1)
    parts = path.split("/")
    short = "/…/" + "/".join(parts[-4:]) if len(parts) > 4 else path
    return text.replace(path, short)


# ── App ───────────────────────────────────────────────────────────────────────

class AgentTUI(App):
    TITLE = "UPD Agent"

    CSS = f"""
    Screen {{
        background: {_BG};
        color: {_TEXT};
    }}

    /* ── Main column (RichLog + live streaming area) ── */
    #main-col {{
        width: 1fr;
        height: 1fr;
        overflow-y: scroll;
        scrollbar-size: 1 1;
        scrollbar-color: {_BORDER_DIM};
    }}

    /* ── Main panel ── */
    #main {{
        width: 1fr;
        height: auto;
        background: {_BG};
        padding: 0 2 2 2;
        overflow-y: hidden;
    }}

    /* ── Sidebar ── */
    #sidebar {{
        width: 48;
        height: 100%;
        dock: right;
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
    #mode {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #activity {{
        height: auto;
        color: {_TEXT_DIM};
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
    #cost-header {{
        height: auto;
        color: {_TEXT};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #cost {{
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

    /* ── Live streaming preview (flows naturally downwards) ── */
    #live {{
        height: auto;
        max-height: 100%;
        background: {_BG};
        color: {_TEXT};
        padding: 0 2;
        display: none;
    }}
    #live.active {{
        display: block;
    }}

    /* ── Input ── */
    Input {{
        height: 3;
        dock: bottom;
        background: {_BG_INPUT};
        border: none;
        padding: 1 2;
        color: {_TEXT};
    }}
    Input:focus {{
        border: none;
        background: {_BG_INPUT};
    }}
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+c", "quit", "Quit"),
        ("escape", "stop", "Stop"),
    ]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._input_bridge = InputBridge()
        self._response_buf = ""
        self._generating = False
        self._in_diff = False   # True after a write/replace tool call
        self._in_edit = False   # True for edit/replace tools (subset of _in_diff)
        self._current_tool = ""  # Name of currently executing tool (non-write/edit)
        self._in_result = False # True while showing └/| result lines
        self._in_parallel = False  # True during parallel action block
        self._reasoning_open = False  # True while a reasoning block is open
        self._active_model = ""
        self._ctx_tokens = 0
        self._ctx_max_tokens = 65536
        self._ctx_skill = ""
        self._ctx_mode = "normal"
        self._mode_locked = False   # True = ignore mode from ContextUpdate temporarily
        # Session cost tracking (reset on /clear)
        self._sess_in_tok = 0
        self._sess_cache_tok = 0
        self._sess_out_tok = 0
        self._sess_sum_tok = 0
        self._cost_in_pm = self._cost_cch_pm = self._cost_out_pm = 0.0
        self._interrupt = False
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

        with Vertical(id="main-col"):
            yield RichLog(id="main", highlight=True, wrap=True, markup=False, auto_scroll=True)
            yield Static("", id="live")
        with Vertical(id="sidebar"):
            yield Static("UPD Agent", id="agent-label")
            yield Static("", id="task-title")
            yield Static("", id="mode")
            yield Static("", id="activity")
            yield Static("Model", id="model-header")
            yield Static("", id="model")
            yield Static("Context", id="context-header")
            yield Static("", id="context")
            yield Static("Cost", id="cost-header")
            yield Static("", id="cost")
            yield Static("Skill", id="skill-header")
            yield Static("", id="skill")
            yield Static("Todo", id="todo-header")
            yield Static("", id="todo")
            yield Static(cwd, id="cwd-label")
        yield Static("", id="statusbar")
        yield Input(placeholder="")

    def on_mount(self) -> None:
        self._update_statusbar()
        log = self.query_one("#main", RichLog)
        # ── Banner ────────────────────────────────────────────────────────────
        from rich.panel import Panel
        from rich.align import Align
        banner_text = RichText()
        banner_text.append("◆ ", style=f"bold {_ACCENT}")
        banner_text.append("UPD Agent", style=f"bold white")
        banner_text.append("  ─  Intelligent Coding Agent", style=f"dim {_TEXT_DIM}")
        log.write(Panel(
            banner_text,
            border_style=f"dim {_BORDER_DIM}",
            padding=(0, 2),
        ))
        hint = RichText()
        hint.append("  /help", style=f"bold {_ACCENT}")
        hint.append(" commands  ·  ", style=_TEXT_FAINT)
        hint.append("exit", style=f"bold {_ACCENT}")
        hint.append(" to quit  ·  ", style=_TEXT_FAINT)
        hint.append("ctrl+q", style=f"bold {_ACCENT}")
        log.write(hint)
        log.write(RichText(""))
        self.query_one(Input).focus()
        self._start_agent()
        self.set_timer(0.1, self._init_sidebar)

    def _init_sidebar(self) -> None:
        """Populate sidebar from on-disk state before first agent response."""
        # ── Model ────────────────────────────────────────────────────────────
        self._refresh_model_sidebar()

        # ── Todo ─────────────────────────────────────────────────────────────
        try:
            import config as _cfg
            from lib.todo_tracker import TodoTracker
            from pathlib import Path
            todo_path = Path(_cfg.TODO_FILE)
            if todo_path.exists():
                tt = TodoTracker.load(todo_path)
                if tt and tt.todos:
                    self.post_message(TodoUpdate(tt.format_simple()))
        except Exception:
            pass

        # ── Context + Skill ───────────────────────────────────────────────────
        try:
            import config as _cfg
            from core.history_manager import load_conversation_history as _load_hist
            from llm_client import estimate_message_tokens

            # Max tokens: config uses chars ÷ 4
            max_tok = getattr(_cfg, "MAX_CONTEXT_CHARS", 512000) // 4

            saved_msgs = _load_hist(silent=True)
            ctx_tokens = sum(estimate_message_tokens(m) for m in saved_msgs) if saved_msgs else 0

            # Skill: read from already-imported main module (no re-execution)
            skill = ""
            try:
                import sys as _sys
                _m = _sys.modules.get("main")
                if _m:
                    fn = getattr(_m, "load_active_skills", None)
                    active_list = getattr(fn, "active_skills", []) or []
                    forced      = getattr(fn, "forced_skills", set()) or set()
                    auto        = getattr(fn, "_active_skill", None)
                    names: list = list(active_list) or sorted(forced) or ([auto] if auto else [])
                    skill = (f"{names[0]}, +{len(names)-1}" if len(names) > 2
                             else ", ".join(names))
            except Exception:
                pass

            # Plan mode badge
            if os.environ.get("PLAN_MODE") == "true":
                skill = f"[plan] {skill}" if skill else "[plan]"

            self.post_message(ContextUpdate(ctx_tokens, max_tok, skill))
        except Exception:
            pass

    def action_quit(self) -> None:
        self._do_exit()

    def _do_exit(self) -> None:
        """Unblock worker thread then force-kill the process."""
        self._update_statusbar("Saving and exiting...")
        try:
            self._input_bridge.submit("exit")
        except Exception:
            self.exit()

    def action_stop(self) -> None:
        """Interrupt current agent execution."""
        if self._generating:
            self._interrupt = True
            log = self.query_one("#main", RichLog)
            t = RichText()
            t.append("\n  ⎋ ", style=f"bold {_YELLOW}")
            t.append("ESC — Stopping generation after current chunk…", style=_TEXT_DIM)
            log.write(t)
            self._scroll_down()
        else:
            self._update_statusbar("No active generation to stop")

    def check_and_reset_interrupt(self) -> bool:
        """Thread-safe check for interrupt flag."""
        if self._interrupt:
            self._interrupt = False
            return True
        return False

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

    def _scroll_down(self) -> None:
        """Scroll #main-col to the bottom so latest content is visible."""
        try:
            self.query_one("#main-col").scroll_end(animate=False)
        except Exception:
            pass

    def _flush_response(self) -> None:
        if not self._response_buf.strip():
            self._response_buf = ""
            self._generating = False
            return
        from rich.panel import Panel
        log = self.query_one("#main", RichLog)
        log.write(Panel(
            _LeftMarkdown(_fix_md(self._response_buf)),
            border_style=f"dim {_BORDER_DIM}",
            padding=(0, 1),
            expand=True,
        ))
        self._response_buf = ""
        self._generating = False
        self._reasoning_open = False
        self._current_tool = ""
        self._update_activity()
        self._update_statusbar()
        self._scroll_down()
        # Clear live preview
        try:
            live = self.query_one("#live", Static)
            live.update("")
            live.remove_class("active")
        except Exception:
            pass

    # ── Input ─────────────────────────────────────────────────────────────────

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        if text.lower() in ("quit", "exit", "/quit", "/exit"):
            self._do_exit()
            return
        self._flush_response()
        log = self.query_one("#main", RichLog)
        # Blank line + full-width turn separator (OpenCode style)
        log.write(RichText(""))
        from rich.rule import Rule
        log.write(Rule(style=f"dim {_BORDER_DIM}"))
        t = RichText()
        t.append(f"  {text}", style=f"bold {_ACCENT}")
        log.write(t)
        log.write(RichText(""))
        self._in_diff = False
        self._in_edit = False
        self._reasoning_open = True  # reasoning model starts reasoning immediately on submit
        self._update_activity()
        # Immediately reflect plan/normal mode from slash command or plan confirmation
        _cmd = text.strip().lower().split()[0] if text.strip() else ""
        _in_plan = os.environ.get("PLAN_MODE") == "true" or "plan" in self._ctx_mode.lower()
        if _cmd in ("/plan", "plan"):
            self._ctx_mode = "plan"
            self._mode_locked = True
            self.set_timer(2.0, lambda: setattr(self, "_mode_locked", False))
            self._redraw_mode()
        elif (_cmd in ("/mode",) and "normal" in text.lower()) or \
             (_cmd in ("y", "yc", "yes", "confirm", "n") and _in_plan):
            self._ctx_mode = "normal"
            self._mode_locked = True
            self.set_timer(2.0, lambda: setattr(self, "_mode_locked", False))
            self._redraw_mode()
        self._input_bridge.submit(text)
        self._scroll_down()

    # ── Message handlers ───────────────────────────────────────────────────────

    def on_stream_chunk(self, msg: StreamChunk) -> None:
        if not self._generating:
            self._generating = True
            self._update_statusbar("generating…")
        # \x00 sentinel = new LLM call started → Reasoning... first
        if msg.text == "\x00":
            self._reasoning_open = True
            self._update_activity()
            return
        # First content chunk: reasoning done → Generating...
        if self._reasoning_open:
            self._reasoning_open = False
            self._update_activity()
        import config as _cfg
        if not getattr(_cfg, "ENABLE_MARKDOWN_RENDER", True):
            log = self.query_one("#main", RichLog)
            log.write(msg.text)
            self._scroll_down()
            return
        self._response_buf += msg.text + "\n"
        # Debounced live Markdown preview — at most one render per 300 ms
        if not getattr(self, "_live_timer_pending", False):
            self._live_timer_pending = True
            self.set_timer(0.3, self._do_live_update)

    def _do_live_update(self) -> None:
        self._live_timer_pending = False
        if not self._response_buf.strip():
            return
        try:
            from rich.panel import Panel
            live = self.query_one("#live", Static)
            live.update(Panel(
                _LeftMarkdown(_fix_md(self._response_buf)),
                border_style=f"dim {_BORDER_DIM}",
                padding=(0, 1),
                expand=True,
            ))
            live.add_class("active")
            self._scroll_down()
        except Exception:
            pass

    def on_flush_response(self, msg: FlushResponse) -> None:
        """Worker signals stream done — render whatever accumulated in _response_buf."""
        self._flush_response()

    def on_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        self._handle_reasoning_chunk(msg)
        self._scroll_down()

    def _handle_reasoning_chunk(self, msg: ReasoningChunk) -> None:
        log = self.query_one("#main", RichLog)
        if msg.blank:
            # blank = paragraph separator within reasoning (not block end)
            # just add spacing, keep header open
            log.write(RichText(""))
            return
        # First chunk of a reasoning block: print "Reasoning" header
        if not self._reasoning_open:
            if self._in_parallel:
                self._in_parallel = False
                log.write(RichText(""))
            self._reasoning_open = True
            self._update_activity()
            hdr = RichText()
            hdr.append("  Reasoning", style=f"italic {_TEXT_DIM}")
            log.write(hdr)
        # Hanging-indent grid: "  ┆ " fixed col + wrapping text col
        grid = RichTable.grid(padding=0)
        grid.add_column(width=4, no_wrap=True)
        grid.add_column(overflow="fold")
        grid.add_row(
            RichText("  ┆ ", style=f"dim {_BORDER_DIM}"),
            RichText(msg.text, style=f"italic {_TEXT_DIM}"),
        )
        log.write(grid)

    def on_context_update(self, msg: ContextUpdate) -> None:
        self._ctx_tokens = msg.tokens
        self._ctx_max_tokens = msg.max_tokens
        self._ctx_skill = msg.skill
        if msg.mode and not getattr(self, "_mode_locked", False):
            self._ctx_mode = msg.mode
        self._redraw_context()
        self._redraw_mode()

    def _redraw_mode(self) -> None:
        try:
            mode = (self._ctx_mode or "normal").capitalize()
            style = _TEXT
            m = RichText()
            m.append(mode, style=style)
            self.query_one("#mode", Static).update(m)
        except Exception:
            pass

    def _update_activity(self) -> None:
        try:
            if self._reasoning_open:
                label = "Reasoning..."
            elif self._in_edit:
                label = "Editing..."
            elif self._in_diff:
                label = "Writing..."
            elif self._in_parallel:
                label = "Executing..."
            elif self._current_tool:
                label = f"Action ({self._current_tool})"
            elif self._generating:
                label = "Generating..."
            else:
                label = "Waiting for input..."
            a = RichText()
            if label:
                a.append(label, style=f"italic dim {_TEXT_DIM}")
            self.query_one("#activity", Static).update(a)
        except Exception:
            pass

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

    def _redraw_cost(self) -> None:
        """Redraw #cost widget with session token usage and cost."""
        try:
            pricing_on = self._cost_in_pm > 0 or self._cost_out_pm > 0

            def _fk(n: int) -> str:
                return f"{n/1000:.1f}k" if n >= 1000 else str(n)

            def _fc(tok: int, rate: float) -> str:
                return f"${tok / 1_000_000 * rate:.4f}"

            t = RichText()
            _non_cch = max(0, self._sess_in_tok - self._sess_cache_tok)
            in_str  = _fk(_non_cch)
            cch_str = _fk(self._sess_cache_tok)
            out_str = _fk(self._sess_out_tok)
            tot     = self._sess_sum_tok

            if pricing_on:
                # non-cached input billed at full rate; cached portion at cache rate
                cost_in  = _non_cch             / 1_000_000 * self._cost_in_pm
                cost_cch = self._sess_cache_tok  / 1_000_000 * self._cost_cch_pm
                cost_out = self._sess_out_tok    / 1_000_000 * self._cost_out_pm
                cost_tot = cost_in + cost_cch + cost_out

                t.append(f"Input         {in_str:>6}  ${cost_in:.4f}\n",  style=_TEXT_DIM)
                if self._sess_cache_tok > 0:
                    t.append(f"Cached Input  {cch_str:>6}  ${cost_cch:.4f}\n", style=_TEXT_DIM)
                t.append(f"Output        {out_str:>6}  ${cost_out:.4f}\n", style=_TEXT_DIM)
                t.append(f"Total         {_fk(tot):>6}  ", style=_TEXT_DIM)
                t.append(f"${cost_tot:.4f}", style=f"bold {_ACCENT}")
            else:
                t.append(f"Input         {in_str}\n",  style=_TEXT_DIM)
                if self._sess_cache_tok > 0:
                    t.append(f"Cached Input  {cch_str}\n", style=_TEXT_DIM)
                t.append(f"Output        {out_str}\n", style=_TEXT_DIM)
                t.append(f"Total         {_fk(tot)}",  style=_TEXT_DIM)

            self.query_one("#cost", Static).update(t)
        except Exception:
            pass

    def _refresh_model_sidebar(self) -> None:
        """Update #model widget with current active model name, and reload pricing."""
        try:
            def _short(name: str) -> str:
                return name.split("/")[-1] if "/" in name else name

            active = _short(self._active_model) if self._active_model else _short(self._primary_model)
            t = RichText()
            if active:
                t.append(active, style=_TEXT_DIM)
            self.query_one("#model", Static).update(t)

            # Load pricing from model_pricing.py based on active model
            try:
                from lib.model_pricing import get_pricing
                p = get_pricing(active)
                if p:
                    self._cost_in_pm  = p.input
                    self._cost_cch_pm = p.cache
                    self._cost_out_pm = p.output
            except Exception:
                pass
        except Exception:
            pass

    def on_main_line(self, msg: MainLine) -> None:
        self._handle_main_line(msg)
        self._scroll_down()

    def _handle_main_line(self, msg: MainLine) -> None:
        self._flush_response()
        log = self.query_one("#main", RichLog)
        text = msg.text

        # Iteration header — hide from log, extract active model for sidebar
        if _ITER.search(text):
            self._in_parallel = False
            m_model = re.search(r"[·•]\s*(\S+)", text)
            if m_model:
                self._active_model = m_model.group(1)
                self._refresh_model_sidebar()
            return

        # Token stats → very faint + update sidebar token count + cost
        if _TOKENS.search(text):
            try:
                import config as _tcfg
                _show_tok = getattr(_tcfg, "SHOW_TOKEN_STATS", True)
            except Exception:
                _show_tok = True
            if _show_tok:
                log.write(RichText(f"  {text.strip()}", style=f"dim {_TEXT_FAINT}"))

            def _parse_tok(pattern: str) -> int:
                m = re.search(pattern, text)
                if not m:
                    return 0
                v = float(m.group(1))
                if m.group(2) == "k":
                    v *= 1000
                return int(v)

            # Update context token counter (sum or fallback to in)
            m_tok = re.search(r"\bsum\s+([\d.]+)(k?)", text)
            if not m_tok:
                m_tok = re.search(r"\bin\s+([\d.]+)(k?)", text)
            if m_tok:
                val = float(m_tok.group(1))
                if m_tok.group(2) == "k":
                    val *= 1000
                self._ctx_tokens = int(val)
                self._redraw_context()

            # Accumulate session tokens for cost tracking
            # Format: ✽ in 1.5k (cache 1.4k) · out 136 · sum 1.6k ...
            # _sess_in_tok = total input (matches token line display)
            # cost is split in _redraw_cost: non-cached at full rate, cached at cache rate
            _in  = _parse_tok(r"\bin\s+([\d.]+)(k?)")
            _cch = _parse_tok(r"\bcache\s+([\d.]+)(k?)")
            _out = _parse_tok(r"\bout\s+([\d.]+)(k?)")
            _sum = _parse_tok(r"\bsum\s+([\d.]+)(k?)")
            if _in > 0 or _out > 0:
                self._sess_in_tok    += _in   # total input (includes cached portion)
                self._sess_cache_tok += _cch
                self._sess_out_tok   += _out
                # Use parsed sum for total to avoid k-rounding compounding error
                self._sess_sum_tok   += _sum if _sum > 0 else (_in + _out)
                self._redraw_cost()
            return

        # /clear → cost counters intentionally NOT reset (accumulate for entire session)

        # Strip ANSI for pattern matching; keep raw for rendering
        _plain = _ANSI.sub("", text)

        # If line contains ANSI codes, skip path shortening (would corrupt escape sequences)
        if _plain != text:
            # ANSI present — use _plain for all pattern matching below
            pass
        else:
            text = _shorten_path(text)
            _plain = text

        # ── Color-coded lines ───────────────────────────────────────────────

        # Todo status bar: suppress from main log (shown in sidebar only)
        if re.match(r"^\d+;\[(\d+/\d+)\]", _plain):
            return

        # System messages: [Plan Mode], [System], [Error]
        m_sys = re.match(r"^(\[(?:Plan Mode|System|Error|Warning)[^\]]*\])(.*)", _plain)
        if m_sys:
            tag, rest = m_sys.groups()
            # Blank line before Plan Mode to visually separate from previous output
            if "Plan Mode" in tag:
                log.write(RichText(""))
                self._ctx_mode = "plan"
                self._redraw_mode()
            t = RichText()
            if "Error" in tag:
                t.append(f"  {tag}", style=f"bold {_RED}")
            elif "Warning" in tag:
                t.append(f"  {tag}", style=f"bold {_YELLOW}")
            elif "Plan Mode" in tag:
                t.append(f"  {tag}", style=f"bold {_ACCENT}")
            else:
                t.append(f"  {tag}", style=f"dim {_TEXT_FAINT}")
            t.append(rest, style=f"dim {_TEXT_DIM}")
            log.write(t)
            return

        # Parallel run header
        m_parallel = re.match(r"^\s*⚡\s+(.*)", _plain)
        if m_parallel:
            self._in_parallel = True
            log.write(RichText(""))
            t = RichText()
            t.append(f"  ⚡ {m_parallel.group(1)}", style=f"bold {_YELLOW}")
            log.write(t)
            return

        # Tool calls: "⏺ tool_name(...)" or "• tool_name(...)"
        m_tool = re.match(r"^\s*[⏺•·]\s*(\w+)\((.*)$", _plain)
        if m_tool:
            self._in_diff = False  # reset diff state on every new tool call
            self._in_edit = False
            tool_name = m_tool.group(1)
            args_part = m_tool.group(2)
            _WRITE_TOOLS = {"write_file", "write_to_file"}
            _EDIT_TOOLS  = {"replace_in_file", "replace_lines", "replace_file_content"}
            _GIT_TOOLS   = {"git_commit","git_push","git_checkout","git_branch","git_merge","git_stash"}
            self._current_tool = ""
            if tool_name in _WRITE_TOOLS:
                self._in_diff = True
                self._in_edit = False
            elif tool_name in _EDIT_TOOLS:
                self._in_diff = True
                self._in_edit = True
            elif tool_name in _GIT_TOOLS:
                self._in_diff = True
                self._in_edit = False
            else:
                self._current_tool = tool_name
            self._update_activity()
            if self._in_result:
                self._in_result = False
            if not self._in_parallel:
                log.write(RichText(""))
            t = RichText()
            t.append(f"  {tool_name}", style=f"bold {_ORANGE}")
            t.append(f"({args_part}", style=f"dim {_ORANGE}")
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
            if not re.match(r"^\s*[└|│⎿]", text):
                self._in_diff = False

        # Tool result lines: "└", "|", "│", or "⎿"
        if re.match(r"^\s*[└|│⎿]", text):
            self._in_result = True
            if self._current_tool:
                self._current_tool = ""
                self._update_activity()
            # Strip tree prefix to check if content is a diff line
            inner = re.sub(r"^\s*[└|│⎿─]+\s*", "", text)
            if self._in_diff and re.match(r"^\+[^+]", inner):
                log.write(RichText(f"  {text.strip()}", style=f"bold {_GREEN}"))
            elif self._in_diff and re.match(r"^-[^-]", inner):
                log.write(RichText(f"  {text.strip()}", style=f"bold {_RED}"))
            elif self._in_diff and re.match(r"^@@", inner):
                log.write(RichText(f"  {text.strip()}", style=f"bold {_ACCENT}"))
            else:
                log.write(RichText(f"  {text.strip()}", style=f"dim {_TEXT_FAINT}"))
            return

        # Non-result line after result block → trailing blank
        if self._in_result:
            log.write(RichText(""))
            self._in_result = False

        # Plan mode exit detection ("✅ Normal mode.")
        if "Normal mode" in _plain:
            self._ctx_mode = "normal"
            self._redraw_mode()

        try:
            ansi_text = RichText.from_ansi(text)
            # Prepend 2-space indent to match all other line types
            indented = RichText("  ")
            indented.append_text(ansi_text)
            log.write(indented)
        except Exception:
            log.write(RichText(f"  {text}", style=_TEXT_DIM))

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
                task_title = s[1:].strip()
            if s.startswith("✅"):
                items.append(("approved", s[1:].strip()))
            elif s.startswith("👀"):
                items.append(("completed", s[1:].strip()))
            elif s.startswith("▶"):
                items.append(("active", s[1:].strip()))
            elif s.startswith("⏸"):
                items.append(("pending", s[1:].strip()))
            elif s.startswith("❌"):
                items.append(("rejected", s[1:].strip()))
            elif s.startswith("•"):
                items.append(("sub", s[1:].strip()))

        # All tasks done → hide todo section entirely
        if items and all(k == "approved" for k, _ in items):
            self.query_one("#task-title", Static).update("")
            self.query_one("#todo-header", Static).update("")
            self.query_one("#todo", Static).update("")
            return

        if task_title:
            t = RichText()
            t.append(task_title, style=_TEXT_DIM)
            self.query_one("#task-title", Static).update(t)
        # Restore header in case it was hidden before
        self.query_one("#todo-header", Static).update("Todo")

        _MAX = 38
        out = RichText()
        for kind, label in items:
            if len(label) > _MAX:
                label = label[:_MAX - 1] + "…"
            if kind == "approved":
                out.append(" ✓ ", style=_TEXT_FAINT)
                out.append(label + "\n", style=_TEXT_FAINT)
            elif kind == "completed":
                out.append(" ✓ ", style=f"bold {_GREEN}")
                out.append(label + "\n", style=_GREEN)
            elif kind == "active":
                out.append(" ▶ ", style=f"bold {_TEXT}")
                out.append(label + "\n", style=f"bold {_TEXT}")
            elif kind == "pending":
                out.append(" · ", style=_TEXT_DIM)
                out.append(label + "\n", style=_TEXT_DIM)
            elif kind == "rejected":
                out.append(" ✗ ", style=_RED)
                out.append(label + "\n", style=_RED)
            else:
                out.append("   · ", style=_TEXT_FAINT)
                out.append(label + "\n", style=_TEXT_FAINT)

        self.query_one("#todo", Static).update(out)
