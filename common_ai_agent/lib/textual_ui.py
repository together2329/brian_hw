"""
lib/textual_ui.py — OpenCode-style Textual TUI for common_ai_agent
"""

from __future__ import annotations

import os
import queue
import re
import sys
import time
from typing import Callable

from rich.markdown import Markdown as _RichMarkdown
from rich.markdown import Heading as _RichHeading
from rich.text import Text as RichText
from rich.table import Table as RichTable
from textual.app import App, ComposeResult
from textual.containers import Vertical
from textual.message import Message
from textual.widgets import Input, OptionList, RichLog, Static
from textual.widgets._option_list import Option as _Option
from textual.suggester import Suggester
from textual.events import Key
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


# ── Autocomplete suggester ────────────────────────────────────────────────────

class _AgentSuggester(Suggester):
    """Suggest slash commands and @ file paths in the TUI input."""

    def __init__(self) -> None:
        super().__init__(use_cache=False, case_sensitive=False)
        self._get_registry = None
        self._init_registry()

    def _init_registry(self) -> None:
        try:
            from core.slash_commands import get_registry  # type: ignore
            self._get_registry = get_registry
        except ImportError:
            try:
                from slash_commands import get_registry  # type: ignore
                self._get_registry = get_registry
            except ImportError:
                pass

    def _live_cmds(self) -> list[str]:
        """Always fetch completions fresh from the live registry."""
        try:
            if self._get_registry is None:
                self._init_registry()
            if self._get_registry is not None:
                return self._get_registry().get_completions()
        except Exception:
            pass
        return []

    async def get_suggestion(self, value: str) -> str | None:
        try:
            # Slash command inline suggestion (first match preview)
            if value.startswith('/') and ' ' not in value:
                for cmd in self._live_cmds():
                    if cmd.lower().startswith(value.lower()) and cmd != value:
                        return cmd
        except Exception:
            pass

        # @ file completion is handled by the OptionList dropdown in on_input_changed
        return None


# ── Clipboard helpers ─────────────────────────────────────────────────────────

def _clipboard_paste() -> str:
    import subprocess
    try:
        if sys.platform == "darwin":
            return subprocess.run(["pbpaste"], capture_output=True, text=True).stdout
        for cmd in [["xclip", "-selection", "clipboard", "-o"],
                    ["xsel", "--clipboard", "--output"]]:
            try:
                return subprocess.run(cmd, capture_output=True, text=True).stdout
            except FileNotFoundError:
                continue
    except Exception:
        pass
    return ""


def _clipboard_copy(text: str) -> None:
    import subprocess
    try:
        if sys.platform == "darwin":
            subprocess.run(["pbcopy"], input=text.encode(), check=False)
            return
        for cmd in [["xclip", "-selection", "clipboard"],
                    ["xsel", "--clipboard", "--input"]]:
            try:
                subprocess.run(cmd, input=text.encode(), check=False)
                return
            except FileNotFoundError:
                continue
    except Exception:
        pass


# ── Custom Input: history + copy/paste + Tab completion ───────────────────────

class _AgentInput(Input):
    """
    Input with:
    - ↑/↓  input history
    - Ctrl+V  paste from system clipboard
    - Ctrl+C  copy selected text (or full value) to clipboard
    - Tab     cycle completion dropdown / accept inline suggestion
    """

    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self._hist: list[str] = []   # newest first
        self._hist_pos: int = -1     # -1 = not browsing
        self._hist_draft: str = ""   # saved draft before browsing
        self._skip_dropdown: bool = False  # suppress on_input_changed dropdown after accept
        self._load_history()

    def check_consume_key(self, key: str, character: str | None) -> bool:
        """Tell Textual we own Tab — prevents Screen's tab→focus_next binding from firing."""
        if key == "tab":
            return True
        return super().check_consume_key(key, character)

    # ── History persistence ───────────────────────────────────────────────────

    def _history_path(self):
        try:
            import config as _cfg
            from pathlib import Path
            return Path(_cfg.TODO_FILE).parent / "input_history.txt"
        except Exception:
            return None

    def _load_history(self) -> None:
        p = self._history_path()
        if p and p.exists():
            try:
                lines = p.read_text(encoding="utf-8").splitlines()
                self._hist = [l for l in reversed(lines) if l.strip()]
            except Exception:
                pass

    def save_to_history(self, text: str) -> None:
        if not text.strip():
            return
        # Skip duplicate of last entry
        if self._hist and self._hist[0] == text:
            return
        self._hist.insert(0, text)
        p = self._history_path()
        if p:
            try:
                with open(p, "a", encoding="utf-8") as f:
                    f.write(text + "\n")
            except Exception:
                pass

    # ── Completion dropdown ───────────────────────────────────────────────────

    def _get_completion_list(self) -> OptionList | None:
        try:
            return self.app.query_one("#completion-list", OptionList)
        except Exception:
            return None

    def _show_slash_dropdown(self, value: str, ol: OptionList, force: bool = False) -> None:
        """Populate and show the / command completion dropdown."""
        try:
            try:
                from core.slash_commands import get_registry  # type: ignore
            except ImportError:
                from slash_commands import get_registry  # type: ignore
            cmds = get_registry().get_completions()
            matches = [c for c in cmds if c.lower().startswith(value.lower())]
            non_exact = [c for c in matches if c != value]
            if non_exact:
                matches = non_exact
            elif not force:
                matches = []
            if matches:
                ol.clear_options()
                for m in matches:
                    ol.add_option(_Option(m))
                ol.highlighted = None
                ol.add_class("visible")
        except Exception:
            pass

    def _show_at_dropdown(self, value: str, ol: OptionList, force: bool = False) -> None:
        """Populate and show the @ file completion dropdown.

        force=True: show even if current value exactly matches one entry
                    (used when user explicitly presses Tab a second time).
        """
        try:
            at_pos = value.rfind('@')
            after_at = value[at_pos + 1:]
            if ' ' in after_at:
                return
            partial = after_at
            if '/' in partial:
                dir_part, stem = partial.rsplit('/', 1)
                base = dir_part or '.'
            else:
                dir_part, stem = '', partial
                base = '.'
            # Expand ~ and resolve relative paths so os.listdir always works
            base_abs = os.path.abspath(os.path.expanduser(base))
            if not os.path.isdir(base_abs):
                return
            file_matches: list[str] = []
            for name in sorted(os.listdir(base_abs)):
                if name.startswith('.'):
                    continue
                if stem and not name.lower().startswith(stem.lower()):
                    continue
                full = f"{dir_part}/{name}" if dir_part else name
                if os.path.isdir(os.path.join(base_abs, name)):
                    full += '/'
                full_replacement = value[:at_pos + 1] + full
                file_matches.append((full, full_replacement))  # (display, full_value)
            non_exact = [(d, v) for d, v in file_matches if v != value]
            if non_exact:
                file_matches = non_exact
            elif not force:
                file_matches = []
            if file_matches:
                ol.clear_options()
                for display, full_val in file_matches:
                    ol.add_option(_Option(display, id=full_val))
                ol.highlighted = None
                ol.add_class("visible")
        except Exception:
            pass

    # ── System clipboard actions (override Textual's internal-only versions) ──

    def action_copy(self) -> None:
        """Ctrl+C — copy selection (or full value) to SYSTEM clipboard."""
        sel = self.selection
        if not sel.is_empty:
            text = self.value[min(sel.start, sel.end):max(sel.start, sel.end)]
        else:
            text = self.value
        self.app.copy_to_clipboard(text)   # OSC 52 (iTerm2/Wezterm)
        _clipboard_copy(text)              # pbcopy / xclip

    def action_paste(self) -> None:
        """Ctrl+V — paste from SYSTEM clipboard."""
        text = _clipboard_paste()          # pbpaste / xclip
        if text:
            start, end = self.selection
            self.replace(text, start, end)
        else:
            super().action_paste()         # fallback: Textual internal clipboard

    # ── Key handler ──────────────────────────────────────────────────────────

    async def _on_key(self, event: Key) -> None:
        ol = self._get_completion_list()

        # ── Tab: highlight-only cycling / directory navigation ───────────────
        if event.key == "tab":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    next_idx = 0 if current is None else (current + 1) % count
                    opt = ol.get_option_at_index(next_idx)
                    # Use id (full replacement) when set, else prompt
                    opt_value = opt.id or str(opt.prompt)
                    opt_display = str(opt.prompt)

                    if current is not None and opt_display.endswith('/'):
                        # Already highlighted a directory → navigate into it
                        ol.remove_class("visible")
                        self._skip_dropdown = True   # suppress on_input_changed
                        self.value = opt_value
                        self.action_end()
                        # Directly refresh directory contents synchronously
                        self._skip_dropdown = False
                        ol_ref = self._get_completion_list()
                        if ol_ref is not None:
                            self._show_at_dropdown(opt_value, ol_ref, force=False)
                    else:
                        # First Tab on this item: just highlight (no value change)
                        ol.highlighted = next_idx
                event.prevent_default()
                event.stop()
                return
            if self._suggestion:
                self.value = self._suggestion
                self.action_end()
                event.prevent_default()
                event.stop()
                return
            # No dropdown, no inline suggestion — re-open with all matches
            if ol is not None:
                value = self.value
                if value.startswith('/') and ' ' not in value:
                    self._show_slash_dropdown(value, ol, force=True)
                    if "visible" in ol.classes:
                        event.prevent_default()
                        event.stop()
                        return
                elif '@' in value:
                    self._show_at_dropdown(value, ol, force=True)
                    if "visible" in ol.classes:
                        event.prevent_default()
                        event.stop()
                        return

        # ── ↑: history back / dropdown navigate up ───────────────────────────
        elif event.key == "up":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    prev_idx = (count - 1) if current is None else max(0, current - 1)
                    ol.highlighted = prev_idx
                event.prevent_default()
                event.stop()
                return
            elif self._hist:
                if self._hist_pos == -1:
                    self._hist_draft = self.value
                if self._hist_pos < len(self._hist) - 1:
                    self._hist_pos += 1
                    self.value = self._hist[self._hist_pos]
                    self.action_end()
                event.prevent_default()
                event.stop()
                return

        # ── ↓: history forward / dropdown navigate down ──────────────────────
        elif event.key == "down":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    next_idx = 0 if current is None else min(count - 1, current + 1)
                    ol.highlighted = next_idx
                event.prevent_default()
                event.stop()
                return
            elif self._hist_pos >= 0:
                if self._hist_pos > 0:
                    self._hist_pos -= 1
                    self.value = self._hist[self._hist_pos]
                else:
                    self._hist_pos = -1
                    self.value = self._hist_draft
                self.action_end()
                event.prevent_default()
                event.stop()
                return

        # ── Enter: accept highlighted dropdown item or submit ─────────────────
        elif event.key == "enter":
            if ol is not None and "visible" in ol.classes:
                highlighted = ol.highlighted
                if highlighted is not None:
                    opt = ol.get_option_at_index(highlighted)
                    opt_value = opt.id or str(opt.prompt)
                    ol.remove_class("visible")
                    self._skip_dropdown = True   # suppress on_input_changed re-show
                    self.value = opt_value
                    self.action_end()
                    event.prevent_default()
                    event.stop()
                    return
                ol.remove_class("visible")
            self._hist_pos = -1   # reset history browsing on submit

        # ── Escape: close dropdown — let event bubble to App BINDINGS → action_stop
        elif event.key == "escape":
            if ol is not None and "visible" in ol.classes:
                ol.remove_class("visible")
            # Do NOT call event.stop() — let Key bubble to App so BINDINGS fire action_stop

        # ── Ctrl+Q: let event bubble to App BINDINGS → action_quit ───────────
        elif event.key == "ctrl+q":
            pass  # Do NOT stop — let Key bubble to App BINDINGS → action_quit

        await super()._on_key(event)


# ── Input bridge ──────────────────────────────────────────────────────────────

class InputBridge:
    def __init__(self, on_idle=None) -> None:
        self._q: queue.Queue[str] = queue.Queue()
        self._on_idle = on_idle

    def get_input(self, prompt: str = "") -> str:
        # Agent thread is back at the input prompt → idle signal
        if self._on_idle:
            self._on_idle()
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
    _saved_tty_attrs = None  # saved in on_mount; used by _restore_terminal staticmethod

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
    }}
    #mode {{
        height: 2;
        color: {_TEXT_DIM};
        padding: 1 0 0 0;
        text-style: bold;
    }}
    #activity {{
        height: 3;
        color: {_TEXT_DIM};
        padding: 0 0 1 0;
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
        scrollbar-size: 0 0;
        padding: 0;
    }}
    #cwd-label {{
        height: auto;
        color: {_TEXT_DIM};
        padding: 1 0 0 0;
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

    /* ── Completion dropdown ── */
    #completion-list {{
        dock: bottom;
        margin-bottom: 3;
        display: none;
        max-height: 12;
        background: {_BG_INPUT};
        border: solid {_BORDER_DIM};
        padding: 0 1;
    }}
    #completion-list.visible {{
        display: block;
    }}
    #completion-list > .option-list--option {{
        background: {_BG_INPUT};
        color: {_TEXT};
        padding: 0 1;
    }}
    #completion-list > .option-list--option-highlighted {{
        background: {_BORDER_DIM};
        color: white;
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
    Input > .input--cursor {{
        background: {_BORDER};
        color: {_TEXT};
    }}
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("ctrl+y", "copy_last", "Copy last response"),
        ("escape", "stop", "Stop"),
    ]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        self._esc_fired = False  # True from ESC until agent returns to get_input()
        self._input_bridge = InputBridge(on_idle=self._on_agent_idle)
        self._response_buf = ""
        self._last_response_text = ""  # plain text of last flushed response
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
        self._compressing = False  # True during context compression — suppresses proactive
        # ── Proactive mode state ─────────────────────────────────────
        self._proactive_enabled = False
        self._proactive_idle_seconds = 30
        self._proactive_message = ''
        self._proactive_max_cycles = 3
        self._proactive_cycle_count = 0
        self._last_input_time = 0.0
        self._proactive_timer = None
        self._last_blur_time = 0.0  # track focus-loss for spurious ESC debounce
        try:
            import config as _cfg
            self._model = getattr(_cfg, "MODEL_NAME", "")
            self._primary_model  = getattr(_cfg, "PRIMARY_MODEL",  self._model)
            self._secondary_model = getattr(_cfg, "SECONDARY_MODEL", self._model)
            # Load proactive mode config
            self._proactive_enabled = getattr(_cfg, "PROACTIVE_ENABLED", False)
            self._proactive_idle_seconds = getattr(_cfg, "PROACTIVE_IDLE_SECONDS", 30)
            self._proactive_message = getattr(_cfg, "PROACTIVE_MESSAGE", '🤔 Still here? Need help with anything?')
            self._proactive_max_cycles = getattr(_cfg, "PROACTIVE_MAX_CYCLES", 3)
        except Exception:
            self._model = ""
            self._primary_model = ""
            self._secondary_model = ""
        self._last_input_time = time.time()

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
        yield OptionList(id="completion-list")
        yield _AgentInput(placeholder="", suggester=_AgentSuggester())

    def on_mount(self) -> None:
        # Save original tty settings (class-level) so the staticmethod
        # _restore_terminal can do an exact restore instead of relying on stty sane.
        try:
            import termios, sys as _sys, os as _os
            fd = _sys.stdin.fileno()
            if _os.isatty(fd):
                AgentTUI._saved_tty_attrs = termios.tcgetattr(fd)
        except Exception:
            pass
        self._update_statusbar()
        log = self.query_one("#main", RichLog)
        # ── Banner ────────────────────────────────────────────────────────────
        from rich.panel import Panel
        from rich.align import Align
        _wf = os.environ.get("ACTIVE_WORKSPACE", "").strip()
        banner_text = RichText()
        banner_text.append("◆ ", style=f"bold {_ACCENT}")
        banner_text.append("UPD Agent", style=f"bold white")
        if _wf:
            banner_text.append(f"  [{_wf}]", style=f"bold {_ACCENT}")
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
        self.query_one(_AgentInput).focus()
        self._start_agent()
        self.set_timer(0.1, self._init_sidebar)
        # Proactive timer does NOT start here — it starts after first user input

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

            # Max tokens from config
            max_tok = getattr(_cfg, "MAX_CONTEXT_TOKENS", 128000)

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

    @staticmethod
    def _restore_terminal() -> None:
        """Exit alternate screen and reset terminal before force-kill."""
        import subprocess
        _ESC_RESET = (
            "\x1b[?1000l"   # disable mouse button events
            "\x1b[?1002l"   # disable mouse button+drag events
            "\x1b[?1003l"   # disable all mouse motion events
            "\x1b[?1006l"   # disable SGR mouse mode
            "\x1b[?1049l"   # exit alternate screen
            "\x1b[?25h"     # show cursor
            "\x1b[0m"       # reset colors/attrs
            "\x1b[2J"       # clear screen
            "\x1b[H"        # cursor home
        )
        try:
            # Write directly to /dev/tty — bypasses Textual's stdout capture
            with open("/dev/tty", "w") as _tty:
                _tty.write(_ESC_RESET)
                _tty.flush()
        except Exception:
            try:
                import sys as _sys
                _sys.stdout.write(_ESC_RESET)
                _sys.stdout.flush()
            except Exception:
                pass
        # Restore terminal line discipline (echo, canonical mode, etc.)
        # Textual puts the terminal into raw mode; _os._exit() bypasses the
        # normal Textual cleanup, leaving the tty in raw mode and causing
        # zsh to print "command not found" on every keystroke.
        # Try termios restore first (exact saved state), fall back to stty sane.
        _restored = False
        try:
            import termios, sys as _sys
            _attrs = getattr(AgentTUI, "_saved_tty_attrs", None)
            if _attrs is not None:
                fd = _sys.stdin.fileno()
                termios.tcsetattr(fd, termios.TCSANOW, _attrs)
                _restored = True
        except Exception:
            pass
        if not _restored:
            try:
                subprocess.run(["stty", "sane"], timeout=2)
            except Exception:
                pass

    def action_quit(self) -> None:
        """Ctrl+Q: immediate force-exit."""
        import os as _os
        self._interrupt = True
        self._update_statusbar("Exiting…")
        try:
            self._input_bridge.submit("exit")
        except Exception:
            pass
        self._restore_terminal()
        _os._exit(0)

    def _force_exit(self) -> None:
        import os as _os
        self._restore_terminal()
        _os._exit(0)

    def _do_exit(self) -> None:
        """Clean exit path (called from /quit, /exit commands)."""
        self._update_statusbar("Saving and exiting...")
        try:
            self._input_bridge.submit("exit")
        except Exception:
            self.exit()

    def action_copy_last(self) -> None:
        """Copy the last assistant response to system clipboard (Ctrl+Y)."""
        text = self._last_response_text.strip()
        if not text:
            return
        # OSC 52 via Textual driver (iTerm2, Wezterm, Alacritty …)
        self.copy_to_clipboard(text)
        # Also pbcopy/xclip for macOS Terminal.app fallback
        _clipboard_copy(text)
        self._update_statusbar("  ✓ Copied to clipboard  (Ctrl+Y)")
        self.set_timer(2.0, self._update_statusbar)

    def _on_agent_idle(self) -> None:
        """Called from InputBridge.get_input() when agent thread is back at prompt."""
        self._esc_fired = False
        self._generating = False
        try:
            self.query_one(_AgentInput).focus()
        except Exception:
            pass

    def on_app_blur(self) -> None:
        """Record when the terminal loses focus — used to debounce spurious ESC."""
        import time
        self._last_blur_time = time.time()

    def on_app_focus(self) -> None:
        """Restore input focus when terminal window is refocused.
        Also extend the ESC debounce window — tab drags send FOCUSIN
        AFTER the spurious ESC fires, so this catches the trailing edge."""
        import time
        self._last_blur_time = time.time()
        try:
            self.query_one(_AgentInput).focus()
        except Exception:
            pass

    def action_stop(self) -> None:
        """ESC: interrupt current agent execution."""
        if not self._generating:
            # No active generation — ESC is a no-op (avoids poisoning next command)
            return
        # Ignore ESC events that arrive within 300ms of a focus-loss event.
        # Moving the terminal window sends \x1b[O (FOCUSOUT) which can cause
        # Textual's xterm parser to time out and fire a spurious ESC key.
        import time
        if time.time() - self._last_blur_time < 1.0:
            return
        self._interrupt = True
        self._esc_fired = True
        self.set_timer(5.0, self._esc_watchdog)  # safety net if thread stays blocked
        # Cancel active LLM HTTP stream so the agent thread unblocks immediately
        try:
            from llm_client import cancel_current_stream
            cancel_current_stream()
        except Exception:
            pass
        # Reset all activity flags so sidebar shows "Waiting for input..." immediately
        self._reasoning_open = False
        self._generating = False
        self._compressing = False
        self._in_edit = False
        self._in_diff = False
        self._in_parallel = False
        self._current_tool = ""
        # Clear live preview
        try:
            live = self.query_one("#live", Static)
            live.update("")
            live.remove_class("active")
        except Exception:
            pass
        log = self.query_one("#main", RichLog)
        t = RichText()
        t.append("\n  [ESC] ", style=f"bold {_YELLOW}")
        t.append("Interrupted.", style=_TEXT_DIM)
        log.write(t)
        self._update_activity()   # sidebar: → "Waiting for input..."
        self._update_statusbar()
        self._scroll_down()
        try:
            self.query_one(_AgentInput).focus()
        except Exception:
            pass

    def _esc_watchdog(self) -> None:
        """Warn if agent thread is still blocked 5s after ESC; Ctrl+Q to force-quit."""
        if not self._esc_fired:
            return
        # Thread is still running — show hint instead of force-killing
        try:
            log = self.query_one("#main", RichLog)
            t = RichText()
            t.append("  [still processing... press ", style=_TEXT_DIM)
            t.append("Ctrl+Q", style=f"bold {_YELLOW}")
            t.append(" to force quit]", style=_TEXT_DIM)
            log.write(t)
            self._scroll_down()
        except Exception:
            pass

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
        # If we're coming straight from a result block, insert a blank line separator
        if self._in_result:
            log.write(RichText(""))
            self._in_result = False
        log.write(Panel(
            _LeftMarkdown(_fix_md(self._response_buf)),
            border_style=f"dim {_BORDER_DIM}",
            padding=(0, 1),
            expand=True,
        ))
        self._last_response_text = self._response_buf  # ← save for copy
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

    def on_input_changed(self, event: Input.Changed) -> None:
        """Show/hide completion dropdown while typing."""
        value = event.value
        ol = self.query_one("#completion-list", OptionList)

        inp = self.query_one(_AgentInput)

        # Suppress dropdown immediately after accepting a completion
        if inp._skip_dropdown:
            inp._skip_dropdown = False
            ol.remove_class("visible")
            return

        # ── Slash command dropdown ────────────────────────────────────────────
        if value.startswith('/') and ' ' not in value:
            inp._show_slash_dropdown(value, ol, force=False)
            if "visible" in ol.classes:
                return

        # ── @ file/folder dropdown ────────────────────────────────────────────
        elif '@' in value:
            inp._show_at_dropdown(value, ol, force=False)
            if "visible" in ol.classes:
                return

        ol.remove_class("visible")

    def on_option_list_option_selected(self, event: OptionList.OptionSelected) -> None:
        """Accept a completion from the dropdown (mouse click)."""
        inp = self.query_one(_AgentInput)
        self.query_one("#completion-list", OptionList).remove_class("visible")
        inp._skip_dropdown = True   # suppress on_input_changed re-show
        inp.value = event.option.id or str(event.option.prompt)
        inp.action_end()
        inp.focus()

    def on_input_submitted(self, event: Input.Submitted) -> None:
        text = event.value.strip()
        event.input.value = ""
        if not text:
            return
        # Reset proactive idle timer and cycle counter on user input
        self._last_input_time = time.time()
        self._proactive_cycle_count = 0  # Reset cycles on real user input
        self._start_proactive_timer()
        # Save to history
        try:
            self.query_one(_AgentInput).save_to_history(text)
        except Exception:
            pass
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
        # Slash commands (/plan, /compact, etc.) don't always trigger an LLM call.
        # Don't eagerly set Reasoning... for them — the \x00 sentinel handles it
        # when an LLM call actually starts.  For normal input, set it immediately
        # so reasoning models show feedback right away.
        _is_slash_cmd = text.startswith("/")
        if not _is_slash_cmd:
            self._reasoning_open = True
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
        # End of compression — LLM is responding again
        if self._compressing:
            self._compressing = False
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
        # Clear compression state after LLM response completes
        self._compressing = False


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
        t = RichText()
        t.append("  ┆ ", style=f"dim {_BORDER_DIM}")
        t.append(msg.text, style=f"italic {_TEXT_DIM}")
        log.write(t)

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

    # ── Proactive idle timer ────────────────────────────────────────────

    def _start_proactive_timer(self) -> None:
        """Cancel any running proactive timer and schedule a new one."""
        if not self._proactive_enabled or self._compressing:
            return
        if self._proactive_timer is not None:
            try:
                self._proactive_timer.stop()
            except Exception:
                pass
            self._proactive_timer = None
        self._proactive_timer = self.set_timer(
            self._proactive_idle_seconds, self._check_proactive_idle
        )

    def _check_proactive_idle(self) -> None:
        """Callback after idle threshold: inject proactive prompt to trigger LLM call."""
        if not self._proactive_enabled:
            return
        self._proactive_timer = None
        # If agent is still generating (LLM call / tool use / reasoning),
        # or compressing context — don't inject, reschedule instead.
        if self._generating or self._compressing:
            self._start_proactive_timer()
            return
        # Check cycle limit (0 = unlimited)
        if self._proactive_max_cycles > 0 and self._proactive_cycle_count >= self._proactive_max_cycles:
            print(f"[Proactive] Max cycles ({self._proactive_max_cycles}) reached — stopping.")
            return
        elapsed = time.time() - self._last_input_time
        if elapsed < self._proactive_idle_seconds:
            # User typed something recently; reschedule
            self._start_proactive_timer()
            return
        # Still idle — inject proactive prompt into agent input queue
        # This triggers an actual LLM call
        self._last_input_time = time.time()
        self._proactive_cycle_count += 1
        print(f"[Proactive] Injecting ({self._proactive_cycle_count}/{self._proactive_max_cycles}): {self._proactive_message!r}")
        try:
            self._input_bridge.submit(self._proactive_message)
        except Exception:
            pass
        # Schedule next proactive check after this injection's response completes
        # Use a longer delay to account for response generation time
        self.set_timer(self._proactive_idle_seconds, self._check_proactive_idle)

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

        # Strip emoji variation selectors (U+FE0F) that break terminal column width
        text = text.replace("\ufe0f", "")
        # Strip ANSI for pattern matching; keep raw for rendering
        _plain = _ANSI.sub("", text)

        # Detect compression start/end to suppress proactive mode during compression
        if re.search(r'\[Compress\]', _plain) or 'Preemptive compression' in _plain:
            self._compressing = True
            if self._proactive_timer is not None:
                try:
                    self._proactive_timer.stop()
                except Exception:
                    pass
                self._proactive_timer = None

        # Model switched → immediately update sidebar (before path shortening)
        m_model_switch = re.search(r"Model switched to:\s*(\S+)", _plain)
        if m_model_switch:
            self._active_model = m_model_switch.group(1)
            self._refresh_model_sidebar()
        # "  Model: <name>" line from LLM calls (chat mode has no iteration header)
        elif re.match(r"^\s*Model:\s*(\S+)", _plain):
            m_ml = re.match(r"^\s*Model:\s*(\S+)", _plain)
            self._active_model = m_ml.group(1)
            self._refresh_model_sidebar()

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
            # Match BOTH original names (write_file) and friendly names (Write/Edit)
            # since format_tool_header uses _friendly_tool_name()
            _WRITE_TOOLS = {"write_file", "write_to_file", "Write"}
            _EDIT_TOOLS  = {"replace_in_file", "replace_lines", "replace_file_content", "Edit"}
            _GIT_TOOLS   = {"git_commit","git_push","git_checkout","git_branch","git_merge","git_stash",
                           "Git_Commit","Git_Push","Git_Checkout","Git_Branch","Git_Merge","Git_Stash"}
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
        # Use _plain (ANSI-stripped) for matching since ANSI codes obscure markers
        if self._in_diff:
            if re.match(r"^\+[^+]", _plain):
                log.write(RichText(f"  {text}", style=f"bold {_GREEN}"))
                return
            if re.match(r"^-[^-]", _plain):
                log.write(RichText(f"  {text}", style=f"bold {_RED}"))
                return
            if re.match(r"^@@", _plain):
                log.write(RichText(f"  {text}", style=f"bold {_ACCENT}"))
                return
            # Non-diff line ends the diff block (check _plain for tree chars)
            if not re.match(r"^\s*[└|│⎿]", _plain):
                self._in_diff = False

        # Tool result lines: "└", "|", "│", or "⎿" (check _plain for tree chars)
        if re.match(r"^\s*[└|│⎿]", _plain):
            self._in_result = True
            # Strip tree prefix, then line-number prefix (e.g. "    42 " or "    42→"),
            # using _plain to reveal +/- markers from format_diff_snippet output
            inner = re.sub(r"^\s*[└|│⎿─]+\s*", "", _plain)
            inner = re.sub(r"^\s*\d+\s*[→ ]?\s*", "", inner)
            if self._in_diff and re.match(r"^\+[^+]", inner):
                log.write(RichText(f"  {_plain.strip()}", style=f"bold {_GREEN}"))
            elif self._in_diff and re.match(r"^-[^-]", inner):
                log.write(RichText(f"  {_plain.strip()}", style=f"bold {_RED}"))
            elif self._in_diff and re.match(r"^@@", inner):
                log.write(RichText(f"  {_plain.strip()}", style=f"bold {_ACCENT}"))
            else:
                log.write(RichText(f"  {_plain.strip()}", style=f"dim {_TEXT_FAINT}"))
            # Clear tool indicator after writing so sidebar update doesn't race with log write
            if self._current_tool:
                self._current_tool = ""
                self._update_activity()
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
