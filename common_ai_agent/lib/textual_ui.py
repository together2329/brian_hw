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
from rich.markdown import ListItem as _RichListItem
from rich.markdown import Paragraph as _RichParagraph
from rich.text import Text as RichText
from rich.table import Table as RichTable
from textual.app import App, ComposeResult
from textual.binding import Binding
from textual.containers import Horizontal, Vertical
from textual.message import Message
from textual.screen import ModalScreen
from textual.widgets import Input, OptionList, RichLog, Static, TextArea, Button
from textual.widgets._option_list import Option as _Option
from textual.suggester import Suggester
from textual.events import Key, Click
from textual import work, on

_ANSI   = re.compile(r"\x1b\[[0-9;]*[mK]")
_NOISE  = re.compile(r"^[\s•·\-─—=*]+$")
_ITER   = re.compile(r"primary\s+\d+/\d+")
_TOKENS = re.compile(r"(✽|in\s+[\d.]+k?)\s+.*tokens")

# ── Platform detection ─────────────────────────────────────────────────────
_IS_WINDOWS = sys.platform == "win32"
_IS_WINDOWS_TERMINAL = _IS_WINDOWS and os.environ.get("WT_SESSION", "") != ""
# Windows Terminal (wt.exe) supports ANSI + alternate screen.
# Legacy cmd.exe / conhost does NOT support alternate screen properly —
# enabling it causes duplicated/overlapping rendering.

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
    '''Fix common LLM markdown quirks before passing to Rich Markdown renderer.

    1. Lone backtick -> triple fence
    2. Table blocks: auto-insert separator, normalise sep cells, add blank lines around
    3. Split inline tables into separate rows
    4. Blank lines around code fences
    5. Collapse 2+ consecutive blank lines -> 1
    6. GFM task lists -> bullet + checkbox emoji
    7. Setext-style headers (underline === / ---) -> # heading
    8. Highlight syntax (==text==) -> **bold**
    9. Footnotes ([^N]) -> stripped
    10. Blank lines before/after list blocks
    '''
    raw_lines = text.splitlines()

    # -- Pass 0: wrap directory-tree blocks in code fences --
    # Box-drawing characters (├ └ │ ─ …) appear in shell `tree` / `find` output.
    # Rich's Markdown parser misinterprets them as list markers, table separators,
    # or horizontal rules, corrupting the rendered output mid-stream.
    # Detect contiguous runs of such lines and wrap them in ``` fences.
    _TREE_RE = re.compile(r'[├└│┌┐┘─┬┼┴┤]')
    _p0_in_fence = False
    _p0_out: list[str] = []
    _i0 = 0
    while _i0 < len(raw_lines):
        _ln = raw_lines[_i0]
        if _ln.strip().startswith("```"):
            _p0_in_fence = not _p0_in_fence
            _p0_out.append(_ln)
            _i0 += 1
            continue
        if _p0_in_fence or not _TREE_RE.search(_ln):
            _p0_out.append(_ln)
            _i0 += 1
            continue
        # Collect the full tree block (tree lines + blank separators within block)
        _j0 = _i0
        while _j0 < len(raw_lines):
            _bl = raw_lines[_j0]
            if _bl.strip() == "":
                # keep blanks that are followed by another tree line
                _nj = _j0 + 1
                while _nj < len(raw_lines) and raw_lines[_nj].strip() == "":
                    _nj += 1
                if _nj < len(raw_lines) and _TREE_RE.search(raw_lines[_nj]):
                    _j0 = _nj
                    continue
                break
            if _TREE_RE.search(_bl):
                _j0 += 1
            else:
                break
        # Strip trailing blank lines — they go outside the fence
        _blk_end = _j0
        while _blk_end > _i0 and not raw_lines[_blk_end - 1].strip():
            _blk_end -= 1
        _p0_out.append("```")
        _p0_out.extend(raw_lines[_i0:_blk_end])
        _p0_out.append("```")
        _p0_out.extend(raw_lines[_blk_end:_j0])  # trailing blanks outside fence
        _i0 = _j0
    raw_lines = _p0_out

    # -- Pass 1: per-line pre-fixes (uses index for lookahead) --
    #        NOTE: tracks code fences to avoid corrupting code content.
    pre: list[str] = []
    _p1_in_fence = False
    i = 0
    while i < len(raw_lines):
        line = raw_lines[i]
        stripped = line.strip()

        # Track code fence boundaries
        if stripped.startswith("```"):
            _p1_in_fence = not _p1_in_fence
            pre.append(line)
            i += 1
            continue

        # Inside a code fence: skip ALL transformations to preserve code content
        if _p1_in_fence:
            pre.append(line)
            i += 1
            continue

        # Lone backtick -> triple fence
        if stripped == "`":
            pre.append("```")
            i += 1
            continue

        # Setext-style header: next line is all === or ---
        if stripped and i + 1 < len(raw_lines):
            next_stripped = raw_lines[i + 1].strip()
            if next_stripped and not next_stripped.startswith("|"):
                if re.match(r"^=+\s*$", next_stripped):
                    pre.append("# " + stripped)
                    i += 2
                    continue
                if re.match(r"^-+\s*$", next_stripped) and not stripped.startswith("|"):
                    pre.append("## " + stripped)
                    i += 2
                    continue

        # GFM task lists: - [ ] text -> checkbox, - [x] text -> checkbox
        m_task = re.match(r"^(\s*)(-|\*|\+)\s+\[([ xX])\]\s+(.*)", line)
        if m_task:
            indent, bullet, checked, rest = m_task.groups()
            checkbox = "\u2611" if checked.lower() == "x" else "\u2610"
            pre.append(f"{indent}{bullet} {checkbox} {rest}")
            i += 1
            continue

        # Highlight syntax: ==text== -> **text**
        if "==" in line:
            line = re.sub(r"==([^=]+)==", r"**\1**", line)

        # Footnote references: [^N] -> strip them
        line = re.sub(r"\[\^\d+\]", "", line)

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
                i += 1
                continue

        pre.append(line)
        i += 1

    # -- Pass 2: structural fixes (tables, lists, code fences, blank lines) --
    out: list[str] = []
    i = 0
    _in_fence = False

    def _is_list_line(ln: str) -> bool:
        s = ln.lstrip()
        if not s:
            return False
        if re.match(r"^[-*+]\s+", s) and not re.match(r"^[-]{3,}\s*$", s) and not re.match(r"^[*]{3,}\s*$", s):
            return True
        if re.match(r"^\d+\.\s+", s):
            return True
        return False

    while i < len(pre):
        line = pre[i]

        # -- Table block --
        if _is_table_row(line) and not _in_fence:
            block: list[str] = []
            j = i
            while j < len(pre) and _is_table_row(pre[j]):
                block.append(pre[j])
                j += 1
            if out and out[-1].strip():
                out.append("")
            out.extend(_fix_table_block(block))
            if j < len(pre) and pre[j].strip():
                out.append("")
            i = j
            continue

        # -- Code fence --
        if line.startswith("```"):
            if _in_fence:
                _in_fence = False
                out.append(line)
                if i + 1 < len(pre) and pre[i + 1].strip():
                    out.append("")
                i += 1
                continue
            else:
                _in_fence = True
                if out and out[-1].strip():
                    out.append("")
                out.append(line)
                i += 1
                continue

        # -- List block: ensure blank line before first list item --
        if _is_list_line(line) and not _in_fence:
            if out and out[-1].strip() and not _is_list_line(out[-1]):
                out.append("")
            out.append(line)
            i += 1
            continue

        # -- Blank line after list block --
        if (out
                and _is_list_line(out[-1])
                and not _is_list_line(line)
                and line.strip()
                and not _in_fence):
            out.append("")

        # Collapse consecutive blank lines
        if not line.strip() and out and not out[-1].strip():
            i += 1
            continue

        out.append(line)
        i += 1

    # -- Pass 3: ensure blank line before headings for reliable parsing --
    # Rich's Markdown parser (and many others) parse headings more reliably
    # when preceded by a blank line. Without it, headings can be treated as
    # regular text when they follow content, causing `#` to appear raw.
    final: list[str] = []
    for line in out:
        if re.match(r"^#{1,6}\s", line) and final and final[-1].strip():
            # Heading follows non-blank content → insert blank line separator
            final.append("")
        final.append(line)

    # -- Pass 3b: auto-close unclosed code fences --
    # During live streaming, code fences may be opened but not yet closed.
    # This makes the Markdown parser treat everything after the opening fence
    # as code content (raw text with `#` visible). Auto-close to prevent this.
    _open_fences = sum(1 for l in final if l.strip().startswith("```"))
    if _open_fences % 2 != 0:
        final.append("```")

    # -- Pass 4: strip leading/trailing blank lines --
    while final and not final[0].strip():
        final.pop(0)
    while final and not final[-1].strip():
        final.pop()

    return "\n".join(final)


class _LeftHeading(_RichHeading):
    """Override Rich Heading to render left-aligned and compact (no extra blank lines)."""
    def __rich_console__(self, console, options):  # type: ignore[override]
        text = self.text
        text.justify = "left"
        yield text

class _TightListItem(_RichListItem):
    """ListItem with no blank line before it — tight bullet lists."""
    new_line = False


class _TightParagraph(_RichParagraph):
    """Paragraph with no blank line before it — keeps text close inside lists."""
    new_line = False


class _LeftMarkdown(_RichMarkdown):
    # Override list_item_open + paragraph_open so consecutive bullets
    # render without a blank line between each item. Rich's defaults
    # set new_line=True on every block element, which made multi-bullet
    # answers in the Textual TUI look double-spaced.
    elements = {
        **_RichMarkdown.elements,
        "heading_open":   _LeftHeading,
        "list_item_open": _TightListItem,
        "paragraph_open": _TightParagraph,
    }


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

class TokenUsage(Message):
    def __init__(self, in_tok: int, cache_tok: int, out_tok: int) -> None:
        self.in_tok    = in_tok
        self.cache_tok = cache_tok
        self.out_tok   = out_tok
        super().__init__()


class AskUserRequest(Message):
    """Agent thread → TUI: open an ask_user question card."""
    def __init__(self, flow_id: str, question: str, kind: str,
                 subtitle: str, options: list, answer_q) -> None:
        self.flow_id  = flow_id
        self.question = question
        self.kind     = kind         # 'single' | 'multi' | 'input'
        self.subtitle = subtitle
        self.options  = options      # list of {id, label, detail?}
        self.answer_q = answer_q     # queue.Queue — modal puts answer dict here
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
        if _IS_WINDOWS:
            r = subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Get-Clipboard -Raw"],
                capture_output=True, text=True,
            )
            return r.stdout
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
        if _IS_WINDOWS:
            subprocess.run(
                ["powershell", "-NoProfile", "-Command", "Set-Clipboard -Value $input"],
                input=text.encode(), check=False,
            )
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


class AgentInputSubmitted(Message):
    """Fired by _AgentInput when the user submits text."""
    def __init__(self, value: str) -> None:
        super().__init__()
        self.value = value


# ── Custom Input: history + copy/paste + Tab completion ───────────────────────

class _AgentInput(TextArea):
    """
    Multiline input (TextArea) with:
    - Enter          submit
    - Shift+Enter    insert newline (expands box)
    - Alt+Enter      insert newline
    - ↑/↓            history navigation
    - Ctrl+V         paste from system clipboard
    - Ctrl+C         copy selection to clipboard
    - Tab            cycle completion dropdown
    - Shift+Tab      toggle plan/normal mode
    """

    BINDINGS = [
        Binding("enter",       "submit_input", "Submit",   show=False, priority=True),
        Binding("ctrl+j",      "newline",      "New line", show=False, priority=True),
        Binding("escape",      "stop_agent",   "Stop",     show=False, priority=True),
        Binding("ctrl+s",      "ask_submit",   "Submit ask", show=False, priority=True),
        Binding("shift+tab",    "toggle_plan",  "Plan",     show=False, priority=True),
        Binding("shift+insert", "paste",        "Paste",    show=False, priority=True),
    ]

    def __init__(self, **kwargs):
        kwargs.pop("placeholder", None)
        kwargs.pop("suggester", None)
        super().__init__("", **kwargs)
        self._hist: list[str] = []
        self._hist_pos: int = -1
        self._hist_draft: str = ""
        self._skip_dropdown: bool = False
        self._user_deleting: bool = False
        self._load_history()

    def action_submit_input(self) -> None:
        ol = self._get_completion_list()
        if ol is not None and "visible" in ol.classes:
            highlighted = ol.highlighted
            if highlighted is not None:
                opt = ol.get_option_at_index(highlighted)
                opt_value = opt.id or str(opt.prompt)
                ol.remove_class("visible")
                self._skip_dropdown = True
                self._set_text(opt_value)
                return
            ol.remove_class("visible")
        self._submit()

    def action_newline(self) -> None:
        self.insert("\n")

    def action_stop_agent(self) -> None:
        # If the inline ask_user panel is open, Esc cancels the question
        # rather than stopping the agent.
        if getattr(self, "_ask_active", None) is not None:
            self._cancel_ask()
            return
        ol = self._get_completion_list()
        if ol is not None and "visible" in ol.classes:
            ol.remove_class("visible")
            return
        try:
            self.app.action_stop()
        except Exception:
            pass

    def action_ask_submit(self) -> None:
        """Ctrl+S — submit the inline ask_user panel if open."""
        if getattr(self, "_ask_active", None) is not None:
            self._submit_ask()

    def action_toggle_plan(self) -> None:
        try:
            current_mode = getattr(self.app, "_ctx_mode", "normal")
            cmd = "/mode normal" if current_mode == "plan" else "/plan"
            self._hist_pos = -1
            self.load_text("")
            self.post_message(AgentInputSubmitted(cmd))
        except Exception:
            pass

    def check_consume_key(self, key: str, character: str | None) -> bool:
        if key in ("tab", "shift+tab", "enter", "shift+enter", "escape"):
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

    def _show_at_dropdown(self, value: str, ol: OptionList, force: bool = False) -> str | None:
        """Populate and show the @ file completion dropdown.

        force=True: show even if current value exactly matches one entry
                    (used when user explicitly presses Tab a second time).
        Returns the first match's full value (for auto-fill), or None.
        """
        try:
            at_pos = value.rfind('@')
            after_at = value[at_pos + 1:]
            if ' ' in after_at:
                return None
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
                return None
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
                ol.highlighted = 0
                ol.add_class("visible")
                return file_matches[0][1]  # first match full value
        except Exception:
            pass
        return None

    # ── System clipboard actions (override Textual's internal-only versions) ──

    def action_copy(self) -> None:
        """Ctrl+C — copy selection (or full text) to SYSTEM clipboard."""
        sel = self.selection
        if not sel.is_empty:
            text = self.selected_text
        else:
            text = self.text
        self.app.copy_to_clipboard(text)
        _clipboard_copy(text)

    def action_paste(self) -> None:
        """Ctrl+V — paste from SYSTEM clipboard."""
        text = _clipboard_paste()
        if text:
            self.insert(text)
        else:
            super().action_paste()

    def _submit(self) -> None:
        """Submit current text content."""
        text = self.text.strip()
        self._hist_pos = -1
        self.load_text("")
        if text:
            self.post_message(AgentInputSubmitted(text))

    def _set_text(self, value: str, at_end: bool = True) -> None:
        """Replace entire text content."""
        self.load_text(value)
        if at_end:
            self.move_cursor(self.document.end)
        else:
            self.move_cursor((0, 0))

    # ── Key handler ──────────────────────────────────────────────────────────

    async def _on_key(self, event: Key) -> None:
        ol = self._get_completion_list()
        value = self.text  # current text for completion checks

        # Track user-initiated deletion to suppress auto-fill
        if event.key in ("backspace", "delete"):
            self._user_deleting = True
        else:
            self._user_deleting = False

        # ── Space: close dropdown immediately ───────────────────────────────
        if event.key == "space":
            if ol is not None and "visible" in ol.classes:
                ol.remove_class("visible")
            # don't prevent default — let space insert normally

        # ── Tab: highlight-only cycling / directory navigation ───────────────
        if event.key == "tab":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    select_idx = 0 if current is None else current
                    opt = ol.get_option_at_index(select_idx)
                    opt_value = opt.id or str(opt.prompt)
                    opt_display = str(opt.prompt)
                    if opt_display.endswith('/'):
                        # directory: navigate into it
                        ol.remove_class("visible")
                        self._skip_dropdown = True
                        self._set_text(opt_value)
                        self._skip_dropdown = False
                        ol_ref = self._get_completion_list()
                        if ol_ref is not None:
                            self._show_at_dropdown(opt_value, ol_ref, force=False)
                    else:
                        # select and reopen popup (Claude Code style)
                        ol.remove_class("visible")
                        self._skip_dropdown = True
                        self._set_text(opt_value)
                        self._skip_dropdown = False
                        ol_ref = self._get_completion_list()
                        if ol_ref is not None:
                            self._show_at_dropdown(opt_value, ol_ref, force=True)
                event.prevent_default()
                event.stop()
                return
            # No dropdown — re-open with all matches
            if ol is not None:
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

        # ── ↑: history back (only on first line) / dropdown up ───────────────
        elif event.key == "up":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    ol.highlighted = (count - 1) if current is None else max(0, current - 1)
                event.prevent_default()
                event.stop()
                return
            row, col = self.cursor_location
            if row == 0 and col == 0 and self._hist:
                if self._hist_pos == -1:
                    self._hist_draft = self.text
                if self._hist_pos < len(self._hist) - 1:
                    self._hist_pos += 1
                    self._set_text(self._hist[self._hist_pos], at_end=False)
                event.prevent_default()
                event.stop()
                return

        # ── ↓: history forward (only on last line) / dropdown down ───────────
        elif event.key == "down":
            if ol is not None and "visible" in ol.classes:
                count = ol.option_count
                if count > 0:
                    current = ol.highlighted
                    ol.highlighted = 0 if current is None else min(count - 1, current + 1)
                event.prevent_default()
                event.stop()
                return
            row, col = self.cursor_location
            last_row = self.document.line_count - 1
            last_col = len(self.document.get_line(last_row))
            if row == last_row and col == last_col:
                if self._hist_pos > 0:
                    self._hist_pos -= 1
                    self._set_text(self._hist[self._hist_pos])
                elif self._hist_pos == 0:
                    self._hist_pos = -1
                    self._set_text(self._hist_draft)
                # _hist_pos == -1: already at draft, consume event only (no scroll)
                event.prevent_default()
                event.stop()
                return

        # ── Enter: handled by BINDING, stop here to prevent TextArea default ──
        elif event.key == "enter":
            event.prevent_default()
            event.stop()
            return

        # ── Ctrl+Q: bubble to App quit binding ───────────────────────────────
        elif event.key == "ctrl+q":
            return  # do NOT stop — let Key bubble to App BINDINGS

        await super()._on_key(event)


# ── ask_user modal ────────────────────────────────────────────────────────────

class AskUserModal(ModalScreen):
    """Pop-up question card the agent's `ask_user` tool drives.

    Layout:
      ┌── Question ─────────────────────────────────────────┐
      │  <question>                                         │
      │  <subtitle>                                         │
      │                                                     │
      │  [option list — single (radio) or multi (✓/☐)]      │
      │                                                     │
      │  Note: [free-form Input]                            │
      │                                                     │
      │  [Cancel]                                  [Submit] │
      └─────────────────────────────────────────────────────┘

    Key bindings:
      ↑ / ↓        move highlight
      space        toggle (multi only — single uses arrow + enter)
      enter        submit (single mode picks current; multi mode submits)
      esc          cancel — returns empty answer
    """

    DEFAULT_CSS = """
    AskUserModal {
        align: center middle;
    }
    AskUserModal #card {
        width: 80;
        max-width: 95%;
        height: auto;
        max-height: 80%;
        padding: 1 2;
        background: $surface;
        border: round $accent;
    }
    AskUserModal #q-question { text-style: bold; color: $accent; padding-bottom: 0; }
    AskUserModal #q-subtitle { color: $text-muted; padding-bottom: 1; }
    AskUserModal #q-opts { height: auto; max-height: 12; border: tall $panel; padding: 0 1; }
    AskUserModal #q-note-label { padding-top: 1; color: $text-muted; }
    AskUserModal #q-note { margin-bottom: 1; }
    AskUserModal #q-buttons { height: 3; align-horizontal: right; }
    AskUserModal #q-buttons Button { margin-left: 1; }
    AskUserModal .selected-tag { color: $accent; }
    """

    BINDINGS = [
        Binding("escape", "cancel", "Cancel"),
        Binding("ctrl+s", "submit",  "Submit"),
    ]

    def __init__(self, request: "AskUserRequest") -> None:
        super().__init__()
        self.request = request
        # For multi mode we track our own selection set since OptionList is
        # single-highlight by default.
        self._selected_ids: set = set()

    # ── compose ─────────────────────────────────────────────────────
    def compose(self) -> ComposeResult:
        r = self.request
        with Vertical(id="card"):
            yield Static(r.question or "(no question)", id="q-question")
            if r.subtitle:
                yield Static(r.subtitle, id="q-subtitle")
            if r.kind in ("single", "multi"):
                opts = []
                for o in r.options or []:
                    label = o.get("label", o.get("id", ""))
                    if o.get("detail"):
                        label = f"{label}  ─  [dim]{o['detail']}[/dim]"
                    opts.append(_Option(label, id=o.get("id", label)))
                ol = OptionList(*opts, id="q-opts")
                yield ol
            yield Static("Custom note (optional):", id="q-note-label")
            yield Input(placeholder="Free-form answer or override…", id="q-note")
            with Horizontal(id="q-buttons"):
                yield Button("Cancel", id="q-cancel", variant="default")
                yield Button("Submit (Ctrl+S)", id="q-submit", variant="primary")

    # ── lifecycle ───────────────────────────────────────────────────
    def on_mount(self) -> None:
        if self.request.kind in ("single", "multi"):
            try:
                self.query_one("#q-opts", OptionList).focus()
            except Exception:
                pass
        else:
            try:
                self.query_one("#q-note", Input).focus()
            except Exception:
                pass

    # ── selection ───────────────────────────────────────────────────
    def _refresh_multi_labels(self) -> None:
        """Re-render option labels with ☑ / ☐ checkbox prefix in multi mode."""
        if self.request.kind != "multi":
            return
        try:
            ol = self.query_one("#q-opts", OptionList)
        except Exception:
            return
        for i, o in enumerate(self.request.options or []):
            oid = o.get("id", o.get("label"))
            mark = "☑" if oid in self._selected_ids else "☐"
            label = o.get("label", oid)
            if o.get("detail"):
                label = f"{label}  ─  [dim]{o['detail']}[/dim]"
            try:
                ol.replace_option_prompt_at_index(i, f"{mark} {label}")
            except Exception:
                pass

    @on(OptionList.OptionSelected, "#q-opts")
    def _on_option_selected(self, event: OptionList.OptionSelected) -> None:
        oid = event.option.id
        if self.request.kind == "single":
            # Auto-submit on Enter for single-pick — same UX as the web qcard
            self._selected_ids = {oid} if oid else set()
            self._submit_now()
        elif self.request.kind == "multi":
            if oid in self._selected_ids:
                self._selected_ids.discard(oid)
            else:
                self._selected_ids.add(oid)
            self._refresh_multi_labels()

    # ── actions ─────────────────────────────────────────────────────
    @on(Button.Pressed, "#q-submit")
    def _btn_submit(self, _: Button.Pressed) -> None:
        self.action_submit()

    @on(Button.Pressed, "#q-cancel")
    def _btn_cancel(self, _: Button.Pressed) -> None:
        self.action_cancel()

    def action_submit(self) -> None:
        # If single-mode and user pressed Ctrl+S without selecting, take the
        # currently-highlighted option as their answer.
        if self.request.kind == "single" and not self._selected_ids:
            try:
                ol = self.query_one("#q-opts", OptionList)
                hi = ol.highlighted
                if hi is not None and ol.option_count > hi:
                    self._selected_ids = {ol.get_option_at_index(hi).id}
            except Exception:
                pass
        self._submit_now()

    def action_cancel(self) -> None:
        # Empty answer → ask_user callback treats as "use default".
        self.request.answer_q.put({
            "type": "answer",
            "flow_id": self.request.flow_id,
            "selected": [],
            "custom": "",
        })
        self.dismiss()

    def _submit_now(self) -> None:
        try:
            note = self.query_one("#q-note", Input).value or ""
        except Exception:
            note = ""
        self.request.answer_q.put({
            "type": "answer",
            "flow_id": self.request.flow_id,
            "selected": list(self._selected_ids),
            "custom": note,
        })
        self.dismiss()


# ── Input bridge ──────────────────────────────────────────────────────────────

class InputBridge:
    def __init__(self, on_idle=None) -> None:
        self._q: queue.Queue[str] = queue.Queue()
        self._interrupt_q: queue.Queue[str] = queue.Queue()  # mid-run human messages
        self._on_idle = on_idle
        self.agent_running: bool = False  # True while react loop is executing

    def get_input(self, prompt: str = "") -> str:
        # Agent thread is back at the input prompt → idle signal
        if self._on_idle:
            self._on_idle()
        return self._q.get()

    def poll_interrupt(self) -> Optional[str]:
        """Non-blocking: return queued human message if any, else None."""
        try:
            return self._interrupt_q.get_nowait()
        except queue.Empty:
            return None

    def submit(self, text: str) -> None:
        self._q.put(text)

    def submit_interrupt(self, text: str) -> None:
        """Queue a human message to be injected mid-run."""
        self._interrupt_q.put(text)


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

    # On legacy Windows cmd.exe (conhost), alternate screen buffer causes
    # duplicated/overlapping rendering. Windows Terminal (wt.exe) is fine.
    ENABLE_ALTERNATE_SCREEN = not (_IS_WINDOWS and not _IS_WINDOWS_TERMINAL)

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

    /* ── Input wrap ── */
    #input-wrap {{
        height: auto;
        dock: bottom;
        background: {_BG_INPUT};
    }}
    #input-topline {{
        height: 1;
        color: {_BORDER_DIM};
        background: {_BG_INPUT};
        padding: 0 0;
    }}
    #input-bottomline {{
        height: 1;
        color: {_BORDER_DIM};
        background: {_BG_INPUT};
    }}
    #input-row {{
        height: auto;
        background: {_BG_INPUT};
        padding: 0 0;
    }}
    #input-prompt {{
        width: 2;
        height: auto;
        color: #7ee787;
        background: {_BG_INPUT};
        padding: 0 0;
    }}
    /* ── Status bar ── */
    #statusbar {{
        height: 1;
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
        margin-bottom: 5;
        display: none;
        max-height: 12;
        background: {_BG_INPUT};
        border: solid {_BORDER_DIM};
        padding: 0 1;
    }}
    #completion-list.visible {{
        display: block;
    }}
    /* ── Inline ask_user panel — sits just above the input row ─── */
    #ask-user-panel {{
        dock: bottom;
        margin-bottom: 4;
        display: none;
        height: auto;
        max-height: 16;
        background: {_BG_INPUT};
        border: round {_ACCENT};
        padding: 0 1;
    }}
    #ask-user-panel.visible {{
        display: block;
    }}
    #ask-q {{
        color: {_ACCENT};
        text-style: bold;
        padding-bottom: 0;
    }}
    #ask-sub {{
        color: {_TEXT_DIM};
        padding-bottom: 1;
    }}
    #ask-opts {{
        height: auto;
        max-height: 8;
        background: {_BG_INPUT};
        border: tall {_BORDER_DIM};
    }}
    #ask-note {{
        margin-top: 1;
        background: {_BG_INPUT};
    }}
    #ask-hint {{
        color: {_TEXT_DIM};
        padding-top: 0;
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

    /* ── Input (TextArea) ── */
    _AgentInput {{
        height: auto;
        min-height: 1;
        max-height: 12;
        background: {_BG_INPUT};
        border: none;
        padding: 0 1 0 0;
        color: {_TEXT};
        scrollbar-size: 0 0;
    }}
    _AgentInput:focus {{
        border: none;
        background: {_BG_INPUT};
    }}
    _AgentInput > .text-area--cursor {{
        background: {_BORDER};
        color: {_TEXT};
    }}
    _AgentInput > .text-area--gutter {{
        display: none;
    }}
    """

    BINDINGS = [
        ("ctrl+q", "quit", "Quit"),
        ("escape", "stop", "Stop"),
    ]

    def __init__(self, run_agent_fn: Callable) -> None:
        super().__init__()
        self._run_agent_fn = run_agent_fn
        # ── Responsive sidebar width ──────────────────────────────────────
        # On narrow terminals (80-col cmd.exe), use a compact 34-col sidebar.
        # On wider terminals, keep the standard 48-col sidebar.
        try:
            _tw = os.get_terminal_size().columns
        except Exception:
            _tw = 120
        self._sidebar_width = 34 if _tw <= 90 else 48 if _tw <= 140 else 54
        self._esc_fired = False  # True from ESC until agent returns to get_input()
        self._input_bridge = InputBridge(on_idle=self._on_agent_idle)
        self._response_buf = ""
        self._last_response_text = ""  # plain text of last flushed response
        self._response_history: list[tuple[int, int, str]] = []  # (start_line, end_line, text)
        self._generating = False
        self._in_diff = False   # True after a write/replace tool call
        self._in_edit = False   # True for edit/replace tools (subset of _in_diff)
        self._current_tool = ""  # Name of currently executing tool (non-write/edit)
        self._in_result = False # True while showing └/| result lines
        self._in_parallel = False  # True during parallel action block
        self._reasoning_open = False  # True while a reasoning block is open
        self._reasoning_header_written = False  # True after "Reasoning" header written
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
        self._has_direct_emit = False   # True when emit_token_fn is wired (avoids text-parse double-count)
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
            try:
                from src.llm_client import get_active_model as _get_active_model
                self._model = _get_active_model()
            except Exception:
                self._model = getattr(_cfg, "MODEL_NAME", "")
            self._primary_model  = self._model
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
        yield OptionList(id="completion-list")
        # Inline ask_user panel — sits just above the input row, hidden by
        # default. Replaces the old modal-screen popup.
        with Vertical(id="ask-user-panel", classes="hidden"):
            yield Static("", id="ask-q")
            yield Static("", id="ask-sub")
            yield OptionList(id="ask-opts")
            yield Input(placeholder="Custom note (optional)…", id="ask-note")
            yield Static("", id="ask-hint")
        with Vertical(id="input-wrap"):
            yield Static("", id="input-topline")
            with Horizontal(id="input-row"):
                yield Static("❯", id="input-prompt")
                yield _AgentInput()
            yield Static("", id="input-bottomline")
            yield Static("", id="statusbar")

    def on_mount(self) -> None:
        # ── Windows: enable ANSI virtual terminal processing ──────────────
        # Without this, legacy cmd.exe renders ANSI escapes as garbage,
        # causing duplicated/overlapping text rendering.
        if _IS_WINDOWS and not _IS_WINDOWS_TERMINAL:
            try:
                import ctypes
                _kernel32 = ctypes.windll.kernel32
                _handle = _kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                _mode = ctypes.c_ulong()
                _kernel32.GetConsoleMode(_handle, ctypes.byref(_mode))
                _ENABLE_VT = 0x0004  # ENABLE_VIRTUAL_TERMINAL_PROCESSING
                _kernel32.SetConsoleMode(_handle, _mode.value | _ENABLE_VT)
            except Exception:
                pass
        # ── Responsive sidebar width ──────────────────────────────────────
        try:
            self.query_one("#sidebar").styles.width = f"{self._sidebar_width}"
        except Exception:
            pass
        # Save original tty settings (class-level) so the staticmethod
        # _restore_terminal can do an exact restore instead of relying on stty sane.
        try:
            import termios, sys as _sys, os as _os
            fd = _sys.stdin.fileno()
            if _os.isatty(fd):
                AgentTUI._saved_tty_attrs = termios.tcgetattr(fd)
        except Exception:
            pass
        self._git_branch = self._get_git_branch()
        self._update_input_lines()
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
        # ── Activity: show "Waiting for input..." immediately ─────────────────
        self._update_activity()

        # ── Workspace / Mode label ─────────────────────────────────────────────
        try:
            _wf = os.environ.get("ACTIVE_WORKSPACE", "").strip()
            _desc = os.environ.get("ACTIVE_WORKSPACE_DESC", "").strip()
            if _wf:
                m = RichText()
                m.append(f"[{_wf}]", style=f"bold {_ACCENT}")
                if _desc:
                    short_desc = _desc[:40] + ("…" if len(_desc) > 40 else "")
                    m.append(f"\n{short_desc}", style=_TEXT_DIM)
                self.query_one("#mode", Static).update(m)
        except Exception:
            pass

        # ── Cost: restore accumulated totals from previous session ───────────
        self._load_cost_file()

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

            # Skill: try main module first, then fall back to ACTIVE_WORKSPACE env
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

            # Fallback: read forced skills from workspace config
            if not skill:
                try:
                    _wf = os.environ.get("ACTIVE_WORKSPACE", "").strip()
                    if _wf:
                        from pathlib import Path as _Path
                        import json as _json
                        _ws_json = _Path(__file__).parent.parent / "workflow" / _wf / "workspace.json"
                        if _ws_json.exists():
                            _ws_data = _json.loads(_ws_json.read_text())
                            _forced = (_ws_data.get("skills") or {}).get("force_activate") or []
                            if _forced:
                                skill = ", ".join(_forced[:2])
                                if len(_forced) > 2:
                                    skill += f", +{len(_forced)-2}"
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
            if _IS_WINDOWS:
                # Windows: write ESC reset to CONOUT$ (console output handle)
                import ctypes
                _kernel32 = ctypes.windll.kernel32
                _handle = _kernel32.GetStdHandle(-11)  # STD_OUTPUT_HANDLE
                _buf = _ESC_RESET.encode()
                _written = ctypes.c_ulong(0)
                _kernel32.WriteConsoleA(_handle, _buf, len(_buf), ctypes.byref(_written), None)
            else:
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

        # Restore terminal line discipline.
        if _IS_WINDOWS:
            # Windows: no termios — console mode is restored by the OS on exit
            pass
        else:
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
                    import subprocess as _sp
                    _sp.run(["stty", "sane"], check=False)
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
        """Copy the last assistant response as plain text to clipboard (Ctrl+Y)."""
        raw = self._last_response_text.strip()
        if not raw:
            return
        try:
            from io import StringIO
            from rich.console import Console as _Console
            _sio = StringIO()
            _con = _Console(file=_sio, force_terminal=False, no_color=True,
                            width=self.size.width or 80)
            _con.print(_LeftMarkdown(_fix_md(raw)))
            text = _sio.getvalue().strip()
        except Exception:
            text = raw
        self.copy_to_clipboard(text)
        _clipboard_copy(text)

    @on(Click, "#main")
    def on_output_click(self, event: Click) -> None:
        """Click on output area → copy clicked response (config: ENABLE_CLICK_TO_COPY)."""
        import config as _cfg
        if not getattr(_cfg, "ENABLE_CLICK_TO_COPY", False):
            return
        output = self.query_one("#main", RichLog)
        # Determine which response was clicked using Y coordinate + scroll offset
        click_line = int(event.y + output.scroll_y)
        text = None
        for start, end, resp_text in self._response_history:
            if start <= click_line < end:
                text = resp_text
                break
        if text is None and self._response_history:
            # Fallback: last response
            text = self._response_history[-1][2]
        if text:
            try:
                from io import StringIO
                from rich.console import Console as _Console
                _sio = StringIO()
                _con = _Console(file=_sio, force_terminal=False, no_color=True,
                                width=self.size.width or 80)
                _con.print(_LeftMarkdown(_fix_md(text)))
                plain = _sio.getvalue().strip()
            except Exception:
                plain = text
            self.copy_to_clipboard(plain)
            _clipboard_copy(plain)
            self._update_statusbar("  ✓ Copied to clipboard")
            self.set_timer(2.0, self._update_statusbar)
        # Return focus to input
        self.query_one(_AgentInput).focus()

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
        """Restore input focus when terminal window is refocused."""
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
        if time.time() - self._last_blur_time < 0.3:
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
        self._reasoning_header_written = False
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
        try:
            import config as _cfg
            _cfg._esc_interrupted = True
        except Exception:
            pass
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
            in_plan = self._ctx_mode == "plan"
            if in_plan:
                t.append("  ⏸ ", style=f"bold {_ACCENT}")
                t.append("plan mode on", style=_TEXT_DIM)
                t.append("  (shift+tab to exit)", style=_TEXT_FAINT)
            else:
                t.append("  ◆ ", style=f"bold {_ACCENT}")
                t.append(self._model or "normal", style=_TEXT_FAINT)
                t.append("  shift+tab plan", style=_TEXT_FAINT)
            t.append("  ·  esc interrupt", style=_TEXT_FAINT)
            t.append("  ·  ctrl+q quit", style=_TEXT_FAINT)
            t.append("  ·  ctrl+j newline", style=_TEXT_FAINT)
            t.append("  ·  shift+drag copy", style=_TEXT_FAINT)
            t.append("  ·  shift+insert paste", style=_TEXT_FAINT)
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
        log = self.query_one("#main", RichLog)
        if self._in_result:
            log.write(RichText(""))
            self._in_result = False
        from rich.panel import Panel
        start_line = len(log.lines)
        log.write(Panel(
            _LeftMarkdown(_fix_md(self._response_buf)),
            border_style=f"dim {_BORDER_DIM}",
            padding=(0, 1),
            expand=True,
        ))
        self._response_history.append((start_line, len(log.lines), self._response_buf))
        self._last_response_text = self._response_buf  # ← save for copy
        self._response_buf = ""
        self._generating = False
        self._reasoning_open = False
        self._reasoning_header_written = False
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

    def on_text_area_changed(self, event: TextArea.Changed) -> None:
        """Show/hide completion dropdown while typing."""
        value = event.text_area.text
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
        inp._skip_dropdown = True
        inp._set_text(event.option.id or str(event.option.prompt))
        inp.focus()

    def on_agent_input_submitted(self, event: AgentInputSubmitted) -> None:
        text = event.value.strip()
        # TextArea is already cleared in _submit()
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
        _indented = "\n  ".join(text.splitlines())
        t.append(f"  {_indented}", style=f"bold {_ACCENT}")
        log.write(t)
        self._in_diff = False
        self._in_edit = False
        # Slash commands (/plan, /compact, etc.) don't always trigger an LLM call.
        # Don't eagerly set Reasoning... for them — the \x00 sentinel handles it
        # when an LLM call actually starts.  For normal input, set it immediately
        # so reasoning models show feedback right away.
        self._reasoning_header_written = False
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
        # Route input: auto-interrupt if generating, then submit normally
        import os as _os
        _hitl = _os.getenv("ENABLE_HUMAN_IN_THE_LOOP", "false").lower() in ("true", "1", "yes")
        if self._generating:
            # Auto-interrupt: stop current agent run, then process new input immediately
            self.action_stop()
            self._input_bridge.submit(text)
        elif _hitl and self._input_bridge.agent_running and not _is_slash_cmd:
            # HITL mode: non-slash text goes to interrupt queue; slash commands bypass
            self._input_bridge.submit_interrupt(text)
        else:
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
            self._reasoning_header_written = False
            self._update_activity()
            log = self.query_one("#main", RichLog)
            log.write(RichText(""))
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

    def on_ask_user_request(self, msg: AskUserRequest) -> None:
        """Agent thread asked a question via the ask_user tool —
        populate the inline panel below the chat (Claude-style).

        If a previous request is still open, it is queued; the panel
        only displays one request at a time.
        """
        if not hasattr(self, "_ask_queue"):
            self._ask_queue = []
            self._ask_active = None
            self._ask_selected = set()
        if self._ask_active is not None:
            self._ask_queue.append(msg)
            return
        self._open_ask_panel(msg)

    def _open_ask_panel(self, msg: "AskUserRequest") -> None:
        self._ask_active = msg
        self._ask_selected = set()
        try:
            q = self.query_one("#ask-q", Static)
            sub = self.query_one("#ask-sub", Static)
            opts = self.query_one("#ask-opts", OptionList)
            note = self.query_one("#ask-note", Input)
            hint = self.query_one("#ask-hint", Static)
            panel = self.query_one("#ask-user-panel")
        except Exception:
            return

        q.update(msg.question or "(no question)")
        sub.update(msg.subtitle or "")
        opts.clear_options()
        note.value = ""

        if msg.kind in ("single", "multi"):
            for o in (msg.options or []):
                label = o.get("label", o.get("id", ""))
                if msg.kind == "multi":
                    label = "☐ " + label
                if o.get("detail"):
                    label = f"{label}  ─  [dim]{o['detail']}[/dim]"
                opts.add_option(_Option(label, id=o.get("id", label)))

        if msg.kind == "single":
            hint.update("[dim]↑/↓ navigate · ↵ select & submit · esc cancel[/dim]")
        elif msg.kind == "multi":
            hint.update("[dim]↑/↓ navigate · ↵ toggle · ctrl+s submit · esc cancel[/dim]")
        else:
            hint.update("[dim]type your answer · ctrl+s submit · esc cancel[/dim]")

        panel.add_class("visible")
        # Focus the right widget for the kind
        if msg.kind in ("single", "multi"):
            self.set_focus(opts)
        else:
            self.set_focus(note)

    def _close_ask_panel(self) -> None:
        try:
            self.query_one("#ask-user-panel").remove_class("visible")
        except Exception:
            pass
        self._ask_active = None
        self._ask_selected = set()
        # Pop the next queued request, if any
        if hasattr(self, "_ask_queue") and self._ask_queue:
            nxt = self._ask_queue.pop(0)
            self._open_ask_panel(nxt)
        else:
            # Refocus the main input
            try:
                self.query_one(_AgentInput).focus()
            except Exception:
                pass

    def _refresh_multi_marks(self) -> None:
        """Re-render multi-mode option labels with ☑/☐ prefixes."""
        msg = getattr(self, "_ask_active", None)
        if not msg or msg.kind != "multi":
            return
        try:
            opts = self.query_one("#ask-opts", OptionList)
        except Exception:
            return
        for i, o in enumerate(msg.options or []):
            oid = o.get("id", o.get("label"))
            mark = "☑" if oid in self._ask_selected else "☐"
            label = o.get("label", oid)
            if o.get("detail"):
                label = f"{mark} {label}  ─  [dim]{o['detail']}[/dim]"
            else:
                label = f"{mark} {label}"
            try:
                opts.replace_option_prompt_at_index(i, label)
            except Exception:
                pass

    def _submit_ask(self) -> None:
        msg = getattr(self, "_ask_active", None)
        if not msg:
            return
        try:
            note_val = self.query_one("#ask-note", Input).value or ""
        except Exception:
            note_val = ""
        # In single mode the user submits via Enter on a row, which already
        # populates _ask_selected; if Ctrl+S was pressed without a row pick,
        # take the highlighted option.
        if msg.kind == "single" and not self._ask_selected:
            try:
                opts = self.query_one("#ask-opts", OptionList)
                if opts.highlighted is not None and opts.option_count > opts.highlighted:
                    self._ask_selected = {opts.get_option_at_index(opts.highlighted).id}
            except Exception:
                pass
        msg.answer_q.put({
            "type": "answer",
            "flow_id": msg.flow_id,
            "selected": list(self._ask_selected),
            "custom": note_val,
        })
        self._close_ask_panel()

    def _cancel_ask(self) -> None:
        msg = getattr(self, "_ask_active", None)
        if not msg:
            return
        msg.answer_q.put({
            "type": "answer",
            "flow_id": msg.flow_id,
            "selected": [],
            "custom": "",
        })
        self._close_ask_panel()

    @on(OptionList.OptionSelected, "#ask-opts")
    def _on_ask_opt_selected(self, event: OptionList.OptionSelected) -> None:
        msg = getattr(self, "_ask_active", None)
        if not msg:
            return
        oid = event.option.id
        if msg.kind == "single":
            self._ask_selected = {oid} if oid else set()
            self._submit_ask()
        elif msg.kind == "multi":
            if oid in self._ask_selected:
                self._ask_selected.discard(oid)
            else:
                self._ask_selected.add(oid)
            self._refresh_multi_marks()

    def on_token_usage(self, msg: TokenUsage) -> None:
        self._has_direct_emit = True    # text-parse path will skip to avoid double-count
        self._sess_in_tok    += msg.in_tok
        self._sess_cache_tok += msg.cache_tok
        self._sess_out_tok   += msg.out_tok
        self._sess_sum_tok   += msg.in_tok + msg.out_tok
        self._ctx_tokens      = msg.in_tok
        self._redraw_context()
        self._redraw_cost()
        self._save_cost_file()

    def _load_cost_file(self) -> None:
        """Load accumulated token counts from session cost.json on startup."""
        try:
            import config as _cfg, json as _json
            from pathlib import Path
            path = Path(getattr(_cfg, "COST_FILE", "") or "")
            if not path.name or not path.exists():
                return
            data = _json.loads(path.read_text())
            self._sess_in_tok    = int(data.get("in_tok", 0))
            self._sess_cache_tok = int(data.get("cache_tok", 0))
            self._sess_out_tok   = int(data.get("out_tok", 0))
            self._sess_sum_tok   = int(data.get("sum_tok", 0))
        except Exception:
            pass

    def _save_cost_file(self) -> None:
        """Persist accumulated token counts to session cost.json."""
        try:
            import config as _cfg, json as _json, time as _time
            from pathlib import Path
            path = Path(getattr(_cfg, "COST_FILE", "") or "")
            if not path.name:
                return
            path.parent.mkdir(parents=True, exist_ok=True)
            path.write_text(_json.dumps({
                "in_tok":    self._sess_in_tok,
                "cache_tok": self._sess_cache_tok,
                "out_tok":   self._sess_out_tok,
                "sum_tok":   self._sess_sum_tok,
                "updated_at": _time.time(),
            }, indent=2))
        except Exception:
            pass


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
        if not self._reasoning_header_written:
            if self._in_parallel:
                self._in_parallel = False
                log.write(RichText(""))
            self._reasoning_open = True
            self._reasoning_header_written = True
            self._update_activity()
            hdr = RichText()
            hdr.append("  ┆ ", style=f"dim {_BORDER_DIM}")
            hdr.append("Reasoning", style=f"italic {_TEXT_DIM}")
            log.write(hdr)
        import textwrap as _tw
        try:
            avail = max(20, self.query_one("#main", RichLog).size.width - 4)
        except Exception:
            avail = 76
        parts = _tw.wrap(msg.text, width=avail) or [msg.text]
        for idx, part in enumerate(parts):
            t = RichText()
            t.append("  ┆ " if idx == 0 else "    ", style=f"dim {_BORDER_DIM}")
            t.append(part, style=f"italic {_TEXT_DIM}")
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
            m = RichText()
            m.append(mode, style=_TEXT)
            self.query_one("#mode", Static).update(m)
        except Exception:
            pass
        self._update_input_lines()
        self._update_statusbar()

    def _get_git_branch(self) -> str:
        try:
            import subprocess
            r = subprocess.run(
                ["git", "rev-parse", "--abbrev-ref", "HEAD"],
                capture_output=True, text=True, timeout=2
            )
            b = r.stdout.strip()
            return b if r.returncode == 0 and b and b != "HEAD" else ""
        except Exception:
            return ""

    def _update_input_lines(self) -> None:
        in_plan = self._ctx_mode == "plan"
        line_color  = "#d29922" if in_plan else _BORDER_DIM
        prompt_color = "#d29922" if in_plan else "#7ee787"  # orange / light green
        try:
            branch = getattr(self, "_git_branch", "") or ""
            w = self.size.width or 80
            if branch:
                label = f" {branch} "
                fill = max(4, w - len(label) - 2)
                top = "─" * fill + label + "──"
            else:
                top = "─" * max(4, w - 2)
            self.query_one("#input-topline", Static).update(
                RichText(top, style=line_color)
            )
            self.query_one("#input-bottomline", Static).update(
                RichText("─" * max(4, w - 2), style=line_color)
            )
            self.query_one("#input-prompt", Static).update(
                RichText("❯", style=f"bold {prompt_color}")
            )
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
                if n >= 1_000_000:
                    return f"{n/1_000_000:.1f}M"
                if n >= 1000:
                    return f"{n/1000:.1f}k"
                return str(n)

            _non_cch = max(0, self._sess_in_tok - self._sess_cache_tok)
            in_str  = _fk(_non_cch)
            cch_str = _fk(self._sess_cache_tok)
            out_str = _fk(self._sess_out_tok)
            tot     = self._sess_sum_tok

            lines = []
            if pricing_on:
                # Show pricing rates per 1M tokens
                rate_line = f"$/1M  In {self._cost_in_pm:.2f}"
                if self._cost_cch_pm > 0:
                    rate_line += f"  Cached In {self._cost_cch_pm:.3f}"
                rate_line += f"  Out {self._cost_out_pm:.2f}"
                lines.append(rate_line)

                # non-cached input billed at full rate; cached portion at cache rate
                cost_in  = _non_cch             / 1_000_000 * self._cost_in_pm
                cost_cch = self._sess_cache_tok  / 1_000_000 * self._cost_cch_pm
                cost_out = self._sess_out_tok    / 1_000_000 * self._cost_out_pm
                cost_tot = cost_in + cost_cch + cost_out

                lines.append(f"Input    {in_str:>7}  ${cost_in:.4f}")
                if self._sess_cache_tok > 0:
                    lines.append(f"Cached   {cch_str:>7}  ${cost_cch:.4f}")
                lines.append(f"Output   {out_str:>7}  ${cost_out:.4f}")
                lines.append(f"Total    {_fk(tot):>7}  ${cost_tot:.4f}")
            else:
                lines.append(f"Input    {in_str}")
                if self._sess_cache_tok > 0:
                    lines.append(f"Cached   {cch_str}")
                lines.append(f"Output   {out_str}")
                lines.append(f"Total    {_fk(tot)}")

            self.query_one("#cost", Static).update("\n".join(lines))
        except Exception as _e:
            import sys
            print(f"[Sidebar Cost] Error: {_e}", file=sys.stderr)

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
                    self._redraw_cost()  # Show rates immediately on model change
                else:
                    # No pricing found — clear rates so cost shows token counts only
                    self._cost_in_pm = self._cost_cch_pm = self._cost_out_pm = 0.0
                    self._redraw_cost()
            except Exception as _e:
                import sys
                print(f"[Sidebar Pricing] Error for model={active!r}: {_e}", file=sys.stderr)
        except Exception as _e:
            import sys
            print(f"[Sidebar Model] Error: {_e}", file=sys.stderr)

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
            # Capture everything after · up to the trailing ─── or ANSI reset
            # Handles both "glm-4.7" and "Cursor (Auto)" (names with spaces)
            m_model = re.search(r"[·•]\s*(.+?)\s*(?:─{2,}|\x1b|$)", text)
            if m_model:
                self._active_model = m_model.group(1).strip()
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
                log.write(RichText(f"{text.strip()}", style=f"dim {_TEXT_FAINT}"))

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

            # Accumulate session tokens for cost tracking — only when direct emit is not wired.
            # If emit_token_fn is active, on_token_usage already updated the counters; skip here
            # to avoid double-counting the same call.
            if not self._has_direct_emit:
                _in  = _parse_tok(r"\bin\s+([\d.]+)(k?)")
                # Token line formats:
                #   "cache 0.8k"              → cache_read only
                #   "cache write 0.3k read 0.8k" → both; we want cache_read
                #   "cache write 0.3k"         → no cache_read
                _cch = _parse_tok(r"\bcache read\s+([\d.]+)(k?)")
                if _cch == 0:
                    # Fallback: "cache N" (no "write" keyword) means cache_read
                    _plain_text = re.sub(r"\x1b\[[0-9;]*m", "", text)
                    if "cache write" not in _plain_text:
                        _cch = _parse_tok(r"\bcache\s+([\d.]+)(k?)")
                _out = _parse_tok(r"\bout\s+([\d.]+)(k?)")
                _sum = _parse_tok(r"\bsum\s+([\d.]+)(k?)")
                if _in > 0 or _out > 0:
                    self._sess_in_tok    += _in   # total input (includes cached portion)
                    self._sess_cache_tok += _cch
                    self._sess_out_tok   += _out
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

        # Skill dynamically routed: "  [skill] <name> (llm-routed)" or "[skill] <name>"
        m_skill = re.search(r"\[skill\]\s+(\S+)", _plain)
        if m_skill:
            _routed = m_skill.group(1).strip(".,)")
            if _routed and _routed != self._ctx_skill:
                self._ctx_skill = _routed
                self._redraw_context()

        # Workflow switched: "[Workflow: <name>]" from /workflow command output
        m_wf = re.search(r"\[Workflow:\s*(\S+)\]", _plain)
        if m_wf:
            _wf_name = m_wf.group(1).strip("]")
            try:
                m = RichText()
                m.append(f"[{_wf_name}]", style=f"bold {_ACCENT}")
                self.query_one("#mode", Static).update(m)
            except Exception:
                pass

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

        # Debug blocks: [Request Debug ...], [Response ...], [Inject], [Reasoning], [Retry ...]
        m_debug = re.match(r"^\s*(\[(?:Request Debug|Response|Inject|Reasoning|Retry|Perf|Cache|RateLimiter|Agent)[^\]]*\])(.*)", _plain)
        if m_debug:
            tag, rest = m_debug.groups()
            t = RichText()
            t.append(f"{tag}", style=f"dim {_ACCENT}")
            if rest.strip():
                t.append(rest, style=f"dim {_TEXT_FAINT}")
            log.write(t)
            return

        # Debug block body lines (indented with spaces, part of [Request Debug]/[Response] block)
        if re.match(r"^\s{2,}(?:URL|Model|Stream|Messages|Est\.tokens|Caching|Temperature|Max tokens|Stop|Tools|Tool choice|Store|Reasoning|Finish|Latency|Input|Output|Total|Tool calls|Effort|Summary|Rsn tokens|─{3,})[\s:─]", _plain):
            log.write(RichText(f"{_plain.strip()}", style=f"dim {_TEXT_FAINT}"))
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
            t = RichText("  ")
            if "Error" in tag:
                t.append(f"{tag}", style=f"bold {_RED}")
            elif "Warning" in tag:
                t.append(f"{tag}", style=f"bold {_YELLOW}")
            elif "Plan Mode" in tag:
                t.append(f"{tag}", style=f"bold {_ACCENT}")
            else:
                t.append(f"{tag}", style=f"dim {_TEXT_FAINT}")
            t.append(rest, style=f"dim {_TEXT_DIM}")
            log.write(t)
            return

        # Parallel run header
        m_parallel = re.match(r"^\s*⚡\s+(.*)", _plain)
        if m_parallel:
            self._in_parallel = True
            log.write(RichText(""))
            t = RichText()
            t.append(f"⚡ {m_parallel.group(1)}", style=f"bold {_YELLOW}")
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
            t.append(f"  {tool_name}", style=f"bold {_YELLOW}")
            t.append(f"({args_part}", style=f"dim {_YELLOW}")
            log.write(t)
            return


        # Diff lines (after write/replace/git tools)
        # Use _plain (ANSI-stripped) for matching since ANSI codes obscure markers
        if self._in_diff:
            if re.match(r"^\+[^+]", _plain):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_GREEN}"))
                return
            if re.match(r"^-[^-]", _plain):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_RED}"))
                return
            if re.match(r"^@@", _plain):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_ACCENT}"))
                return
            # Non-diff line ends the diff block (check _plain for tree chars)
            if not re.match(r"^\s*[└|│⎿]", _plain):
                self._in_diff = False

        # Tool result lines: "└", "|", "│", or "⎿" (check _plain for tree chars)
        if re.match(r"^\s*[└|│⎿]", _plain):
            self._in_result = True
            # Syntax-highlighted code lines from read_file preview start with "│"
            # and contain ANSI color codes — render with from_ansi to preserve colors
            if text.startswith("│") and _plain != text:
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(_plain.lstrip("│").strip(), style=f"dim {_TEXT_FAINT}"))
                if self._current_tool:
                    self._current_tool = ""
                    self._update_activity()
                return
            # Strip tree prefix, then line-number prefix (e.g. "    42 " or "    42→"),
            # using _plain to reveal +/- markers from format_diff_snippet output
            inner = re.sub(r"^\s*[└|│⎿─]+\s*", "", _plain)
            inner = re.sub(r"^\s*\d+\s*[→ ]?\s*", "", inner)
            if self._in_diff and re.match(r"^\+[^+]", inner):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_GREEN}"))
            elif self._in_diff and re.match(r"^-[^-]", inner):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_RED}"))
            elif self._in_diff and re.match(r"^@@", inner):
                try:
                    log.write(RichText.from_ansi(text))
                except Exception:
                    log.write(RichText(f"  {_plain.strip()}", style=f"bold {_ACCENT}"))
            else:
                log.write(RichText(f"  {_plain.strip()}", style=f"dim {_TEXT_FAINT}"))
            # Clear tool indicator after writing so sidebar update doesn't race with log write
            if self._current_tool:
                self._current_tool = ""
                self._update_activity()
            return

        # Syntax-highlighted lines following a tool result (e.g. read_file preview)
        # These have ANSI color codes — render with from_ansi to preserve syntax colors
        if self._in_result and _plain != text:
            try:
                log.write(RichText.from_ansi(text))
            except Exception:
                log.write(RichText(_plain, style=f"dim {_TEXT_FAINT}"))
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
