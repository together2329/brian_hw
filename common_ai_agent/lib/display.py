"""
Display utilities for Common AI Agent.
Handles ANSI color codes and terminal output formatting.
Zero-dependency — pure ANSI escape sequences.
"""

import os
import platform
import shutil
import sys
import threading
import time

IS_WINDOWS = platform.system() == "Windows"


def enable_windows_virtual_terminal() -> bool:
    """
    Enable Virtual Terminal Processing on Windows so ANSI escape sequences
    (color codes, cursor movement, etc.) are interpreted by the console
    instead of being printed as raw text like '?[92m'.

    Calls SetConsoleMode on stdout and stderr handles to set the
    ENABLE_VIRTUAL_TERMINAL_PROCESSING (0x0004) flag.

    Returns True if the flag was set (or was already set), False otherwise.
    On non-Windows platforms this is a no-op and returns True.

    Must be called early — before any Color/ANSI output to stdout/stderr.
    """
    if not IS_WINDOWS:
        return True

    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32

        # Console mode flag
        ENABLE_VIRTUAL_TERMINAL_PROCESSING = 0x0004

        success = True
        for stream_handle_func, name in [
            (kernel32.GetStdHandle, -11),  # STD_OUTPUT_HANDLE
            (kernel32.GetStdHandle, -12),  # STD_ERROR_HANDLE
        ]:
            handle = stream_handle_func(name)
            if not handle or handle == -1:
                continue

            # Read current mode
            mode = ctypes.c_ulong()
            if not kernel32.GetConsoleMode(handle, ctypes.byref(mode)):
                continue

            # Already enabled — skip
            if mode.value & ENABLE_VIRTUAL_TERMINAL_PROCESSING:
                continue

            # Set the flag
            new_mode = mode.value | ENABLE_VIRTUAL_TERMINAL_PROCESSING
            if not kernel32.SetConsoleMode(handle, new_mode):
                success = False

        return success

    except Exception:
        return False


# Auto-enable on import when running on Windows.
# This ensures that merely importing display.py activates ANSI support,
# covering scripts that don't call the entry points (e.g. tests, utilities).
enable_windows_virtual_terminal()


class Color:
    """ANSI color codes for terminal output"""
    # Basic colors
    RED = '\033[91m'
    GREEN = '\033[92m'
    YELLOW = '\033[93m'
    BLUE = '\033[94m'
    MAGENTA = '\033[95m'
    CYAN = '\033[96m'
    WHITE = '\033[97m'
    GRAY = '\033[90m'

    # Styles
    BOLD = '\033[1m'
    DIM = '\033[2m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'
    STRIKETHROUGH = '\033[9m'
    RESET = '\033[0m'

    @staticmethod
    def system(text):
        """System messages - Cyan"""
        return f"{Color.CYAN}{text}{Color.RESET}"

    @staticmethod
    def user(text):
        """User messages - Green"""
        return f"{Color.GREEN}{text}{Color.RESET}"

    @staticmethod
    def agent(text):
        """Agent messages - Blue"""
        return f"{Color.BLUE}{text}{Color.RESET}"

    @staticmethod
    def tool(text):
        """Tool names - Magenta"""
        return f"{Color.MAGENTA}{text}{Color.RESET}"

    @staticmethod
    def success(text):
        """Success messages - Green + Bold"""
        return f"{Color.BOLD}{Color.GREEN}{text}{Color.RESET}"

    @staticmethod
    def warning(text):
        """Warning messages - Yellow"""
        return f"{Color.YELLOW}{text}{Color.RESET}"

    @staticmethod
    def error(text):
        """Error messages - Red + Bold"""
        return f"{Color.BOLD}{Color.RED}{text}{Color.RESET}"

    @staticmethod
    def info(text):
        """Info messages - Cyan + Dim"""
        return f"{Color.DIM}{Color.CYAN}{text}{Color.RESET}"

    @staticmethod
    def debug(text):
        """Debug messages - Purple/Magenta"""
        return f"{Color.MAGENTA}{text}{Color.RESET}"

    @staticmethod
    def action(text):
        """Action messages (e.g. key decisions) - Green + Bold + Underline"""
        return f"{Color.BOLD}{Color.GREEN}\033[4m{text}{Color.RESET}"

    @staticmethod
    def dim(text):
        """Dimmed text"""
        return f"{Color.DIM}{text}{Color.RESET}"

    @staticmethod
    def bold(text):
        """Bold text"""
        return f"{Color.BOLD}{text}{Color.RESET}"

    @staticmethod
    def diff_add(text):
        """Added lines in diff - Green background"""
        return f"{Color.GREEN}+ {text}{Color.RESET}"

    @staticmethod
    def diff_remove(text):
        """Removed lines in diff - Red"""
        return f"{Color.RED}- {text}{Color.RESET}"

    @staticmethod
    def diff_context(text):
        """Context lines in diff - Dim"""
        return f"{Color.DIM}  {text}{Color.RESET}"


# ============================================================
# Spinner — Claude Code style status line with coordinated output
# ============================================================

class Spinner:
    """
    Claude Code style inline spinner with elapsed time.
    Coordinates with live_print() so sub-agent output doesn't collide.

    Usage:
        with Spinner("Inferring"):
            result = call_llm(...)

    Shows:  ✽ Inferring… (12s)
    """

    FRAMES = ["✽", "✦", "✶", "✧", "✹", "✷"]
    INTERVAL = 0.15  # seconds per frame

    # Class-level coordination
    _active: 'Spinner' = None
    _lock = threading.Lock()

    def __init__(self, label: str = "Inferring", stream=None):
        self.label = label
        self.stream = stream or sys.stderr
        self._stop_event = threading.Event()
        self._thread = None
        self._start_time = 0.0
        self._frame_idx = 0
        self._last_len = 0  # rendered line length for portable clearing

    def _format_elapsed(self, elapsed: float) -> str:
        if elapsed < 60:
            return f"{elapsed:.0f}s"
        minutes = int(elapsed // 60)
        seconds = int(elapsed % 60)
        return f"{minutes}m{seconds:02d}s"

    def _render_line(self) -> str:
        elapsed = time.time() - self._start_time
        frame = self.FRAMES[self._frame_idx % len(self.FRAMES)]
        elapsed_str = self._format_elapsed(elapsed)
        return f"  {Color.CYAN}{frame}{Color.RESET} {Color.DIM}{self.label}…{Color.RESET}"

    def _render(self):
        """Render the spinner on the current line (no newline)."""
        line = self._render_line()
        # Portable: overwrite previous content with spaces then write new line
        pad = max(0, self._last_len - len(line))
        self.stream.write(f"\r{line}{' ' * pad}")
        self.stream.flush()
        self._last_len = len(line)

    def _clear_line(self):
        """Clear the spinner line portably (no \\033[2K)."""
        self.stream.write(f"\r{' ' * (self._last_len + 4)}\r")
        self.stream.flush()
        self._last_len = 0

    def _spin(self):
        while not self._stop_event.is_set():
            with Spinner._lock:
                self._render()
                self._frame_idx += 1
            self._stop_event.wait(self.INTERVAL)

    def start(self):
        self._start_time = time.time()
        self._stop_event.clear()
        Spinner._active = self
        self._thread = threading.Thread(target=self._spin, daemon=True)
        self._thread.start()
        return self

    def stop(self):
        self._stop_event.set()
        if self._thread:
            self._thread.join(timeout=1.0)
        with Spinner._lock:
            self._clear_line()
            Spinner._active = None

    @property
    def elapsed(self) -> float:
        return time.time() - self._start_time if self._start_time else 0.0

    def __enter__(self):
        self.start()
        return self

    def __exit__(self, *args):
        self.stop()


def live_print(*args, **kwargs):
    """
    Thread-safe print that coordinates with an active Spinner.
    Clears spinner → prints → re-renders spinner.
    Use this instead of print() when a Spinner might be running.
    """
    with Spinner._lock:
        if Spinner._active:
            Spinner._active._clear_line()
        print(*args, **kwargs)
        sys.stdout.flush()
        if Spinner._active:
            Spinner._active._render()


# ============================================================
# EscapeWatcher — ESC key to abort ReAct loop
# ============================================================

class EscapeWatcher:
    """
    Background thread that watches for ESC key press.
    When ESC is detected, sets a flag that the ReAct loop checks
    at each iteration boundary to break back to the input prompt.

    Usage:
        EscapeWatcher.start()
        while running:
            if EscapeWatcher.check():
                break
            ...
        EscapeWatcher.stop()
    """

    _active = False
    _pressed = False
    _thread = None
    _old_settings = None
    _lock = threading.Lock()

    @classmethod
    def start(cls):
        """Start watching for ESC. Call before entering ReAct loop."""
        with cls._lock:
            cls._pressed = False
            cls._active = True
        cls._thread = threading.Thread(target=cls._watch, daemon=True)
        cls._thread.start()

    @classmethod
    def _watch(cls):
        if IS_WINDOWS:
            cls._watch_windows()
        else:
            cls._watch_unix()

    @classmethod
    def _watch_windows(cls):
        import msvcrt
        while cls._active:
            if msvcrt.kbhit():
                ch = msvcrt.getch()
                if ch == b'\x1b':  # ESC
                    with cls._lock:
                        cls._pressed = True
                    live_print(f"\n  {Color.YELLOW}⎋ ESC — aborting after current step…{Color.RESET}")
                    break
            time.sleep(0.1)

    @classmethod
    def _watch_unix(cls):
        try:
            import select
            import tty, termios
        except ImportError:
            return  # Not a Unix terminal

        fd = sys.stdin.fileno()
        try:
            cls._old_settings = termios.tcgetattr(fd)
        except termios.error:
            return  # Not a real terminal (e.g., piped input)

        try:
            # cbreak mode: read char-by-char, output still works normally
            tty.setcbreak(fd)
            while cls._active:
                # Poll stdin with 0.2s timeout
                ready, _, _ = select.select([sys.stdin], [], [], 0.2)
                if ready:
                    ch = sys.stdin.read(1)
                    if ch == '\x1b':  # ESC
                        with cls._lock:
                            cls._pressed = True
                        live_print(f"\n  {Color.YELLOW}⎋ ESC — aborting after current step…{Color.RESET}")
                        break
        except (OSError, ValueError):
            pass  # stdin closed or not readable
        finally:
            try:
                termios.tcsetattr(fd, termios.TCSADRAIN, cls._old_settings)
            except (termios.error, ValueError):
                pass

    @classmethod
    def stop(cls):
        """Stop watching. Call after ReAct loop exits."""
        with cls._lock:
            cls._active = False
        if cls._thread:
            cls._thread.join(timeout=1.0)
            cls._thread = None

    @classmethod
    def check(cls) -> bool:
        """Check if ESC was pressed. Non-blocking."""
        with cls._lock:
            return cls._pressed

    @classmethod
    def reset(cls):
        """Reset the pressed flag."""
        with cls._lock:
            cls._pressed = False


# ============================================================
# Tree Characters (oh-my-opencode inspired)
# ============================================================

TREE = {
    'pipe':   '│',    # vertical pipe
    'branch': '├─',   # mid-branch
    'end':    '└─',   # end-branch
    'indent': '   ',  # indentation
    'bar':    '┃',    # thick pipe (for thinking blocks)
}


# ============================================================
# Tool Icons (per-tool-type, oh-my-opencode inspired)
# ============================================================

TOOL_ICONS = {
    # Read operations
    'read_file':     '→',
    'read_lines':    '→',
    'grep_file':     '✱',
    'find_files':    '✱',
    'list_dir':      '✱',
    'rag_search':    '✱',
    'rag_explore':   '✱',
    'rag_index':     '✱',
    'rag_status':    '✱',
    'rag_clear':     '✱',
    # Write operations
    'write_file':       '←',
    'replace_in_file':  '←',
    'replace_lines':    '←',
    # Command execution
    'run_command':   '$',
    # Git
    'git_diff':      '±',
    'git_status':    '±',
    # Agent delegation
    'background_task':   '#',
    'background_output': '#',
    'background_cancel': '#',
    'background_list':   '#',
    # Todo
    'todo_write':    '☐',
    'todo_update':   '☐',
    'todo_add':      '☐',
    'todo_remove':   '☐',
    'todo_status':   '☐',
    'todo_read':     '☐',
    # Verilog
    'analyze_verilog_module': '⊞',
    'find_signal_usage':      '⊞',
    'find_module_definition': '⊞',
    'extract_module_hierarchy': '⊞',
    'find_potential_issues':  '⊞',
    'analyze_timing_paths':   '⊞',
}

DEFAULT_TOOL_ICON = '⚙'


def tool_icon(tool_name: str) -> str:
    """Get icon for a tool name"""
    return TOOL_ICONS.get(tool_name, DEFAULT_TOOL_ICON)


# ============================================================
# Formatting Utilities
# ============================================================

def get_terminal_width() -> int:
    """Get terminal width, default 80"""
    try:
        return shutil.get_terminal_size().columns
    except Exception:
        return 80


def format_tool_header(tool_name: str, args_summary: str = "", idx: int = 0, total: int = 1) -> str:
    """
    Format a tool execution header line (Claude Code style).
    Example: "⏺ Read(core/hooks.py)"
    Example: "⏺ Read(core/hooks.py · lines 10-50)"
    Example: "⏺ Grep("pattern" in core/)"
    """
    name = _friendly_tool_name(tool_name)
    if args_summary:
        return f"⏺ {Color.BOLD}{name}{Color.RESET}{Color.DIM}({args_summary}){Color.RESET}"
    return f"⏺ {Color.BOLD}{name}{Color.RESET}"


def _ansi_safe_truncate(text, max_visible):
    import re as _re
    _ANSI_RE = _re.compile(r"\x1b\[[0-9;]*[mK]")
    result = []
    visible = 0
    i = 0
    while i < len(text) and visible < max_visible:
        m2 = _ANSI_RE.match(text, i)
        if m2:
            result.append(m2.group())
            i = m2.end()
        else:
            result.append(text[i])
            visible += 1
            i += 1
    if i < len(text):
        result.append(Color.RESET)
    return ''.join(result)


def format_tool_result(output: str, max_lines: int = 5, max_chars: int = 300) -> str:
    """
    Format tool result with tree structure.
    Shows preview with dim tree end marker.
    """
    if not output:
        return f"  {Color.DIM}{TREE['end']} (empty){Color.RESET}"

    lines = output.strip().split('\n')
    total_chars = len(output)

    # Short output — show inline
    if len(lines) <= max_lines and total_chars <= max_chars:
        result_lines = []
        for i, line in enumerate(lines):
            prefix = TREE['end'] if i == len(lines) - 1 else TREE['pipe']
            result_lines.append(f"  {Color.DIM}{prefix} {_ansi_safe_truncate(line, 120)}{Color.RESET}")
        return '\n'.join(result_lines)

    # Long output — show preview
    preview_lines = lines[:max_lines]
    result_lines = []
    for line in preview_lines:
        result_lines.append(f"  {Color.DIM}{TREE['pipe']} {_ansi_safe_truncate(line, 120)}{Color.RESET}")
    result_lines.append(f"  {Color.DIM}{TREE['end']} ... ({len(lines)} lines, {total_chars:,} chars){Color.RESET}")
    return '\n'.join(result_lines)


def format_tool_brief(tool_name: str, args_str: str, observation: str) -> str:
    """
    Return a short inline suffix describing the tool result.
    Appended to the tool header on the same line.

    Examples:
      ✱ Read core/hooks.py                    245 lines
      ✱ Find "*.v"                            28 file(s)
      ✱ Grep "pattern" in src/                3 match(es)
      ✱ List path="."                         15 entries
    """
    import re
    line_count = observation.count('\n') + 1 if observation else 0
    is_error = observation.lower().startswith('error') if observation else False
    # Treat system/plan-mode messages as errors so they surface visibly
    is_system_msg = bool(observation and observation.startswith('[') and
                         any(observation.startswith(p) for p in ('[Plan Mode]', '[System]', '[Error')))

    if is_system_msg:
        first_line = observation.split('\n')[0][:80]
        return f"{Color.YELLOW}{first_line}{Color.RESET}"

    if is_error:
        first_line = observation.split('\n')[0][:60]
        # Softer display: yellow instead of red, shorter message
        short = first_line.replace("Error: ", "").replace("Error listing directory: ", "")
        if "not found" in short.lower() or "does not exist" in short.lower() or "not a directory" in short.lower():
            return f"{Color.YELLOW}Not found{Color.RESET}"
        return f"{Color.YELLOW}{short}{Color.RESET}"

    if tool_name in ('read_file', 'read_lines'):
        return f"{line_count} lines"

    if tool_name == 'grep_file':
        match_count = len([l for l in observation.split('\n') if l.strip()]) if observation else 0
        return f"{match_count} matches"

    if tool_name == 'find_files':
        found_m = re.search(r'Found (\d+) file', observation) if observation else None
        count = found_m.group(1) if found_m else str(line_count)
        return f"{count} files"

    if tool_name == 'list_dir':
        entries = len([l for l in observation.split('\n') if l.strip()]) if observation else 0
        return f"{entries} entries"

    if tool_name == 'write_file':
        # Count lines from content arg, not from the 1-line observation message
        content_m = re.search(r'content\s*=\s*"""(.*?)"""', args_str, re.DOTALL)
        if not content_m:
            content_m = re.search(r'content\s*=\s*["\'](.+)', args_str, re.DOTALL)
        if content_m:
            n = content_m.group(1).count('\n') + 1
            return f"{n} lines written"
        # Fallback: extract from observation ("wrote N lines" / "N lines")
        obs_m = re.search(r'(\d+)\s+line', observation) if observation else None
        if obs_m:
            return f"{obs_m.group(1)} lines written"
        return "written"

    if tool_name in ('replace_in_file', 'replace_lines'):
        repl_m = re.search(r'(\d+) replacement', observation) if observation else None
        if repl_m:
            return f"{repl_m.group(1)} replacements"
        return "updated"

    if tool_name == 'run_command':
        exit_m = re.search(r'exit code[:\s]*(\d+)', observation.lower()) if observation else None
        if exit_m:
            return f"exit {exit_m.group(1)}"
        return f"{line_count} lines output"

    if tool_name == 'rag_search':
        result_m = re.search(r'(\d+) result', observation) if observation else None
        count = result_m.group(1) if result_m else "?"
        return f"{count} results"

    if tool_name == 'background_task':
        status_m = re.search(r'Status:\s*(\w+)', observation) if observation else None
        return status_m.group(1) if status_m else "done"

    if tool_name in ('git_diff', 'git_status'):
        return f"{line_count} lines"

    if tool_name == 'todo_write':
        count = observation.count('⏸') + observation.count('▶') + observation.count('✅')
        return f"{count} tasks"

    if tool_name == 'todo_update':
        # Match on the leading status marker, not anywhere in the text
        # (the "completed" response body contains "approved" as a future action reference)
        if observation:
            first = observation.lstrip()
            if first.startswith("✅") and "approved" in first.split("\n")[0].lower():
                return f"{Color.GREEN}approved{Color.RESET}"
            if "marked completed" in first.lower() or first.startswith("Task") and "completed" in first.split("\n")[0]:
                return f"{Color.CYAN}completed{Color.RESET}"
            if first.startswith("❌"):
                return f"{Color.RED}rejected{Color.RESET}"
            if first.startswith("▶"):
                return "in_progress"
            if first.startswith("⏸"):
                return "pending"
        return "updated"

    if tool_name == 'todo_add':
        return "added"

    if tool_name == 'todo_remove':
        return "removed"

    return f"{line_count} lines"


def _extract_path(args_str: str) -> str:
    """Extract file path from tool args string."""
    import re
    match = re.search(r'(?:path\s*=\s*)?["\']([^"\']+)["\']', args_str)
    return match.group(1) if match else ""


def format_agent_banner(agent_name: str, model: str = "", action: str = "Starting") -> str:
    """
    Format sub-agent banner.
    Example:
      ┌─ execute · qwen3-next-80b · Starting
      │
    """
    model_short = _short_model_name(model)
    parts = [f"{Color.CYAN}{agent_name}{Color.RESET}"]
    if model_short:
        parts.append(f"{Color.DIM}{model_short}{Color.RESET}")
    parts.append(f"{Color.DIM}{action}{Color.RESET}")

    line = " · ".join(parts)
    return f"\n  {Color.CYAN}┌─{Color.RESET} {line}\n  {Color.CYAN}│{Color.RESET}"


def format_agent_done(agent_name: str, model: str = "", elapsed_sec: float = 0,
                      iterations: int = 0, tool_count: int = 0) -> str:
    """
    Format sub-agent completion footer.
    Example:
      └─ execute · qwen3 · 6.1s · 3 tools · 2 iters
    """
    model_short = _short_model_name(model)
    parts = [f"{Color.CYAN}{agent_name}{Color.RESET}"]
    if model_short:
        parts.append(f"{Color.DIM}{model_short}{Color.RESET}")
    if elapsed_sec > 0:
        parts.append(f"{Color.DIM}{elapsed_sec:.1f}s{Color.RESET}")
    if tool_count > 0:
        parts.append(f"{Color.DIM}{tool_count} tools{Color.RESET}")
    if iterations > 0:
        parts.append(f"{Color.DIM}{iterations} iters{Color.RESET}")

    line = " · ".join(parts)
    return f"  {Color.CYAN}│{Color.RESET}\n  {Color.CYAN}{TREE['end']}{Color.RESET} {line}\n"


def format_context_bar(current_tokens: int, max_tokens: int, label: str = "") -> str:
    """
    Compact context usage bar.
    Example: "[Context: 12K/32K ████░░░░ 38%]"
    """
    pct = int(current_tokens / max_tokens * 100) if max_tokens > 0 else 0

    # Color by usage
    if pct >= 100:
        color = Color.RED
    elif pct >= 80:
        color = Color.YELLOW
    elif pct >= 50:
        color = Color.CYAN
    else:
        color = Color.GREEN

    bar_len = 8
    filled = min(bar_len, int(bar_len * pct / 100))
    bar = '█' * filled + '░' * (bar_len - filled)

    cur_str = _format_tokens(current_tokens)
    max_str = _format_tokens(max_tokens)

    prefix = f"{label} " if label else ""
    return f"{color}{prefix}[{cur_str}/{max_str} {bar} {pct}%]{Color.RESET}"


def format_startup_banner(base_url: str, model: str, features: dict) -> str:
    """
    Compact startup banner.
    Example:
      Common AI Agent · openrouter/glm-4.7
      Rate: 5s │ Iter: 100 │ Cache: on │ Compress: on
    """
    model_short = _short_model_name(model)
    line1 = f"{Color.BOLD}{Color.CYAN}Common AI Agent{Color.RESET} {Color.DIM}· {model_short}{Color.RESET}"

    parts = []
    if features.get('rate_limit'):
        parts.append(f"Rate: {features['rate_limit']}s")
    if features.get('max_iter'):
        parts.append(f"Iter: {features['max_iter']}")
    if features.get('cache'):
        parts.append(f"Cache: {'on' if features['cache'] else 'off'}")
    if features.get('compress'):
        parts.append(f"Compress: {'on' if features['compress'] else 'off'}")
    if features.get('memory'):
        parts.append(f"Memory: {'on' if features['memory'] else 'off'}")
    if features.get('rag'):
        parts.append(f"RAG: {'on' if features['rag'] else 'off'}")

    line2 = f"{Color.DIM}{' │ '.join(parts)}{Color.RESET}" if parts else ""

    return f"{line1}\n{line2}" if line2 else line1


def format_iteration_header(iteration: int, max_iter: int, agent_name: str = "", model: str = "", todo_label: str = "") -> str:
    """
    Minimal iteration header.
    Example: "─── primary 3/100 · glm-4.7 ───"
    Optional todo_label shows active_form of current todo task below the header line.
    """
    prefix = f"{agent_name} " if agent_name else ""
    model_str = f" · {_short_model_name(model)}" if model else ""
    header = f"\n{Color.DIM}─── {prefix}{iteration}/{max_iter}{model_str} ───{Color.RESET}"
    if todo_label:
        header += f"\n  {Color.DIM}{todo_label}{Color.RESET}"
    return header


def format_thought(text: str) -> str:
    """Format thought text with dim bar prefix"""
    lines = text.strip().split('\n')
    formatted = []
    for line in lines:
        formatted.append(f"  {Color.DIM}{TREE['bar']}  {line}{Color.RESET}")
    return '\n'.join(formatted)


# ============================================================
# Internal Helpers
# ============================================================

def _friendly_tool_name(tool_name: str) -> str:
    """Convert tool_name to friendly display name"""
    names = {
        'read_file': 'Read',
        'read_lines': 'Read',
        'write_file': 'Write',
        'replace_in_file': 'Edit',
        'replace_lines': 'Edit',
        'grep_file': 'Grep',
        'find_files': 'Find',
        'list_dir': 'List',
        'run_command': 'Run',
        'rag_search': 'RAG Search',
        'rag_explore': 'RAG Explore',
        'rag_index': 'RAG Index',
        'rag_status': 'RAG Status',
        'rag_clear': 'RAG Clear',
        'git_diff': 'Git Diff',
        'git_status': 'Git Status',
        'background_task': 'Agent',
        'background_output': 'Agent Output',
        'background_cancel': 'Agent Cancel',
        'background_list': 'Agent List',
        'todo_write': 'Todo',
        'todo_read': 'Todo',
        'analyze_verilog_module': 'Analyze Module',
        'find_signal_usage': 'Signal Usage',
        'find_module_definition': 'Module Def',
        'extract_module_hierarchy': 'Hierarchy',
        'find_potential_issues': 'Issues',
        'analyze_timing_paths': 'Timing',
    }
    return names.get(tool_name, tool_name)


def _short_model_name(model: str) -> str:
    """Shorten model name for display"""
    if not model:
        return ""
    # Remove provider prefix for common providers
    for prefix in ('openrouter/', 'anthropic/', 'openai/', 'google/'):
        if model.startswith(prefix):
            model = model[len(prefix):]
            break
    # Shorten common model names
    shortcuts = {
        'qwen/qwen3-next-80b-a3b-instruct': 'qwen3-80b',
        'qwen3-next-80b-a3b-instruct': 'qwen3-80b',
        'z-ai/glm-4.7': 'glm-4.7',
        'glm-4.7': 'glm-4.7',
        'claude-3-5-sonnet': 'claude-3.5-sonnet',
        'claude-3-opus': 'claude-3-opus',
    }
    return shortcuts.get(model, model[:30])


def _format_tokens(n: int) -> str:
    """Format token count: 1234 → '1.2K', 123456 → '123K'"""
    if n >= 1_000_000:
        return f"{n/1_000_000:.1f}M"
    if n >= 10_000:
        return f"{n//1000}K"
    if n >= 1_000:
        return f"{n/1000:.1f}K"
    return str(n)


def _extract_tool_args_summary(tool_name: str, args_str) -> str:
    """Extract a human-readable summary from tool args"""
    import re

    # Handle dict kwargs (native mode) by normalizing to string
    if isinstance(args_str, dict):
        import json as _json
        args_str = ", ".join(
            f'{k}={_json.dumps(v, ensure_ascii=False)}'
            for k, v in args_str.items()
        )

    def _get_val(key_pat, text):
        # Robustly extract quoted string (handles triple and escaped quotes)
        m = re.search(key_pat + r'(?:"""(.*?)"""|\'\'\'(.*?)\'\'\'|"((?:[^"\\]|\\.)*)"|\'((?:[^\'\\]|\\.)*)\')', text, re.DOTALL)
        if m: return next((g for g in m.groups() if g is not None), "")
        return ""

    # Extract path (+ optional line range / content preview) for file tools
    if tool_name in ('read_file', 'read_lines', 'write_file', 'replace_in_file', 'replace_lines'):
        path = _get_val(r'(?:path\s*=\s*)?', args_str)
        if path:
            if tool_name == 'read_lines':
                start_m = re.search(r'start(?:_line)?\s*=\s*(\d+)', args_str)
                end_m   = re.search(r'end(?:_line)?\s*=\s*(\d+)', args_str)
                if start_m and end_m:
                    return f"{path} · lines {start_m.group(1)}-{end_m.group(1)}"
            if tool_name == 'write_file':
                content_m = re.search(r'content\s*=\s*"""(.*?)"""', args_str, re.DOTALL)
                if not content_m:
                    content_m = re.search(r'content\s*=\s*["\'](.{0,200})', args_str, re.DOTALL)
                if content_m:
                    preview = content_m.group(1)[:80].replace('\n', '↵')
                    return f'{path} · "{preview}…"'
            if tool_name in ('replace_in_file', 'replace_lines'):
                old_m = re.search(r'old_string\s*=\s*"""(.*?)"""', args_str, re.DOTALL)
                if not old_m:
                    old_m = re.search(r'old_string\s*=\s*["\'](.{0,120})', args_str, re.DOTALL)
                if old_m:
                    preview = old_m.group(1)[:60].replace('\n', '↵').strip()
                    return f'{path} · "{preview}…"'
            return path

    # Extract pattern + path for grep/find
    if tool_name in ('grep_file', 'find_files'):
        pattern = _get_val(r'(?:pattern\s*=\s*)?', args_str)
        path = _get_val(r'path\s*=\s*', args_str)
        parts = []
        if pattern:
            parts.append(f'"{pattern}"')
        if path:
            parts.append(f'in {path}')
        return ' '.join(parts) if parts else args_str[:60]

    # Extract command for run_command
    if tool_name == 'run_command':
        cmd = _get_val(r'(?:command\s*=\s*)?', args_str)
        if cmd:
            return cmd[:60] + ('...' if len(cmd) > 60 else '')

    # Extract agent + prompt for background_task
    if tool_name == 'background_task':
        agent = _get_val(r'agent\s*=\s*', args_str)
        prompt = _get_val(r'prompt\s*=\s*', args_str)
        parts = []
        if agent:
            parts.append(f'→ {agent}')
        if prompt:
            parts.append(f'"{prompt[:40]}..."')
        return ' '.join(parts) if parts else args_str[:60]

    # Extract tasks/todos count for todo_write
    if tool_name == 'todo_write':
        # Minimal attempt to count items in the tasks/todos list
        tasks_m = re.search(r'(?:tasks|todos)\s*=\s*\[', args_str)
        if tasks_m:
            # Count the number of dictionaries in the list by looking for "content" or "{"
            count = args_str.count('"content":') or args_str.count('{')
            return f"{count} tasks"
        return "..."

    # Extract index/status for todo_update
    if tool_name == 'todo_update':
        idx_m = re.search(r'index\s*=\s*(\d+)', args_str)
        status_m = re.search(r'status\s*=\s*["\']([^"\']+)["\']', args_str)
        content_m = re.search(r'content\s*=\s*["\']([^"\']{0,30})', args_str)
        parts = []
        if idx_m:
            parts.append(f"#{int(idx_m.group(1))}")
        if status_m:
            parts.append(f"→ {status_m.group(1)}")
        if content_m and not status_m:
            parts.append(f"→ \"{content_m.group(1)}...\"")
        return ' '.join(parts) if parts else args_str[:60]

    # Extract content for todo_add
    if tool_name == 'todo_add':
        content_m = re.search(r'content\s*=\s*["\']([^"\']{0,40})', args_str)
        return f'"{content_m.group(1)}..."' if content_m else args_str[:60]

    # Extract index for todo_remove
    if tool_name == 'todo_remove':
        idx_m = re.search(r'index\s*=\s*(\d+)', args_str)
        return f"#{idx_m.group(1)}" if idx_m else args_str[:60]

    # Default: truncate
    return args_str[:60] + ('...' if len(args_str) > 60 else '') if args_str else ""


def format_diff(old_text, new_text, context_lines=3):
    """
    Generate a visual unified diff between old and new text.
    Uses Python standard library only (no external dependencies).

    Args:
        old_text: Original text content
        new_text: New text content
        context_lines: Number of context lines around changes

    Returns:
        Formatted diff string with colors
    """
    import difflib

    old_lines = old_text.splitlines(keepends=True)
    new_lines = new_text.splitlines(keepends=True)

    diff = difflib.unified_diff(
        old_lines, new_lines,
        fromfile='before',
        tofile='after',
        n=context_lines
    )

    result = []
    for line in diff:
        line_stripped = line.rstrip('\n')
        if line.startswith('+++') or line.startswith('---'):
            result.append(f"{Color.BOLD}{Color.CYAN}{line_stripped}{Color.RESET}")
        elif line.startswith('@@'):
            result.append(f"{Color.MAGENTA}{line_stripped}{Color.RESET}")
        elif line.startswith('+'):
            result.append(Color.diff_add(line_stripped[1:]))
        elif line.startswith('-'):
            result.append(Color.diff_remove(line_stripped[1:]))
        else:
            result.append(Color.diff_context(line_stripped[1:] if line.startswith(' ') else line_stripped))

    return '\n'.join(result) if result else "[No changes detected]"


def format_diff_snippet(file_path, old_text, new_text, context_lines=3):
    """
    Generate a clean diff with line numbers like Claude Code.

    Shows changes with:
    - Line numbers on the left
    - Red (-) for deleted lines
    - Green (+) for added lines
    - Context lines without +/-

    Args:
        file_path: Path to the file being edited
        old_text: Original text content
        new_text: New text content
        context_lines: Number of context lines around changes

    Returns:
        Formatted diff string with colors and line numbers
    """
    import difflib

    old_lines = old_text.splitlines(keepends=False)
    new_lines = new_text.splitlines(keepends=False)

    # Find changed region using difflib
    matcher = difflib.SequenceMatcher(None, old_lines, new_lines)
    opcodes = matcher.get_opcodes()

    # Find first and last change
    first_change = None
    last_change = None

    for tag, i1, i2, j1, j2 in opcodes:
        if tag != 'equal':
            if first_change is None:
                first_change = (i1, i2, j1, j2)
            last_change = (i1, i2, j1, j2)

    if first_change is None:
        return "[No changes detected]"

    # Calculate snippet boundaries (with context)
    old_start = max(0, first_change[0] - context_lines)
    old_end = min(len(old_lines), last_change[1] + context_lines)
    new_start = max(0, first_change[2] - context_lines)
    new_end = min(len(new_lines), last_change[3] + context_lines)

    # Build diff with line numbers
    result = []
    result.append(f"The file {Color.CYAN}{file_path}{Color.RESET} has been updated. Here's the result of running `cat -n` on a snippet:")
    result.append("")

    # Process opcodes to show changes with line numbers
    # Context uses NEW file line numbers, changes show both old and new
    for tag, i1, i2, j1, j2 in opcodes:
        # Skip if completely outside our view range
        if i2 <= old_start or i1 >= old_end:
            continue

        if tag == 'equal':
            # Show context lines with NEW file line numbers
            for j in range(max(j1, new_start), min(j2, new_end)):
                line_num = j + 1
                line_content = new_lines[j]
                result.append(f"{Color.DIM}{line_num:6d}→{Color.RESET}{line_content}")

        elif tag == 'replace':
            # Show deleted lines in RED with OLD file line numbers
            for i in range(max(i1, old_start), min(i2, old_end)):
                line_num = i + 1  # OLD file line number
                line_content = old_lines[i]
                result.append(f"{Color.DIM}{line_num:6d} {Color.RESET}{Color.RED}-{line_content}{Color.RESET}")
            # Show added lines in GREEN with NEW file line numbers
            for j in range(max(j1, new_start), min(j2, new_end)):
                line_num = j + 1  # NEW file line number
                line_content = new_lines[j]
                result.append(f"{Color.DIM}{line_num:6d} {Color.RESET}{Color.GREEN}+{line_content}{Color.RESET}")

        elif tag == 'delete':
            # Show deleted lines in RED with OLD file line numbers
            for i in range(max(i1, old_start), min(i2, old_end)):
                line_num = i + 1  # OLD file line number
                line_content = old_lines[i]
                result.append(f"{Color.DIM}{line_num:6d} {Color.RESET}{Color.RED}-{line_content}{Color.RESET}")

        elif tag == 'insert':
            # Show added lines in GREEN with NEW file line numbers
            for j in range(max(j1, new_start), min(j2, new_end)):
                line_num = j + 1  # NEW file line number
                line_content = new_lines[j]
                result.append(f"{Color.DIM}{line_num:6d} {Color.RESET}{Color.GREEN}+{line_content}{Color.RESET}")

    return '\n'.join(result)
