import os
import subprocess
import json
import shlex
import sys
import re

# Robust library path discovery
try:
    from lib.display import format_diff, format_diff_snippet, Color
except ModuleNotFoundError:
    # Fallback: Recursively search for 'lib/display.py' walking up the tree
    import os
    import sys
    
    current_dir = os.path.dirname(os.path.abspath(__file__))
    found_lib = False
    
    # Walk up 3 levels looking for 'lib' directory
    search_dir = current_dir
    for _ in range(4):
        possible_lib = os.path.join(search_dir, 'lib')
        possible_display = os.path.join(possible_lib, 'display.py')
        
        if os.path.isdir(possible_lib) and os.path.isfile(possible_display):
            # Found it! Add the parent of 'lib' to sys.path
            if search_dir not in sys.path:
                sys.path.insert(0, search_dir)
            found_lib = True
            break
        
        # Move up
        parent = os.path.dirname(search_dir)
        if parent == search_dir: # Reached root
            break
        search_dir = parent

    # Try import again
    try:
        from lib.display import format_diff, format_diff_snippet, Color
    except ModuleNotFoundError:
        try:
            from display import format_diff, format_diff_snippet, Color
        except ModuleNotFoundError:
            # Final fallback stubs
            def format_diff(*args, **kwargs):
                return ""
            def format_diff_snippet(*args, **kwargs):
                return ""

def read_file(path):
    """
    Reads the content of a file with smart truncation for large files.

    For files >500 lines, automatically truncates and suggests better alternatives:
    - Use grep_file to find specific sections
    - Use read_lines with offset/limit for targeted reading
    """
    try:
        if not os.path.exists(path):
            # Try to suggest similar files nearby
            import glob
            basename = os.path.basename(path)
            parent = os.path.dirname(path) or "."
            # Search up to 2 levels from parent
            suggestions = []
            for depth in ["", "*/"]:
                search_dir = os.path.dirname(parent) or "."
                found = glob.glob(os.path.join(search_dir, "**", basename), recursive=True)
                suggestions.extend(found[:3])
                if suggestions:
                    break
            if suggestions:
                hint = ", ".join(f"'{s}'" for s in suggestions[:3])
                return f"Error: File '{path}' does not exist. Did you mean: {hint}? Use find_files() to confirm."
            return f"Error: File '{path}' does not exist. Use find_files('{basename}') to locate it."

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)

        # Smart truncation for large files (Grep-first pattern)
        MAX_LINES = 500
        if total_lines > MAX_LINES:
            # Read first MAX_LINES only
            content = ''.join(lines[:MAX_LINES])

            # Add smart suggestion message
            suggestion = f"""

============================================================
⚠️  LARGE FILE DETECTED: {total_lines} lines total
============================================================

Showing first {MAX_LINES} lines only.
... [{total_lines - MAX_LINES} lines hidden (total {total_lines} lines)]

💡 RECOMMENDED NEXT ACTIONS (Grep-First Pattern):

Instead of reading the entire file, use targeted approach:

1. Find specific sections:
   Action: grep_file(pattern="<keyword>", path="{path}")

2. Read specific line ranges (after grep):
   Action: read_lines(path="{path}", start_line=<N>, end_line=<N+50>)

3. Search by concept (if indexed):
   Action: rag_search(query="<concept>", file="{path}")

Example workflow:
  Action: grep_file(pattern="module.*top", path="{path}")
  # → Find that module is at line 245
  Action: read_lines(path="{path}", start_line=240, end_line=290)
  # → Read just that module definition

============================================================
"""
            return content + suggestion
        else:
            # Small file - read entire content
            return ''.join(lines)

    except Exception as e:
        return f"Error reading file: {e}"

def _find_git_root(path: str):
    """Find nearest .git directory walking up from path. Returns root dir or None."""
    check = os.path.abspath(path) if os.path.isdir(path) else os.path.dirname(os.path.abspath(path))
    while True:
        if os.path.exists(os.path.join(check, '.git')):
            return check
        parent = os.path.dirname(check)
        if parent == check:
            return None
        check = parent


def _llm_commit_summary(path: str, content_hint: str) -> str:
    """Call cheap LLM to generate a short commit message. Returns '' on failure."""
    try:
        import config as _cfg
        import sys as _sys
        import os as _os
        # Locate llm_client (src directory)
        _src = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'src')
        if _src not in _sys.path:
            _sys.path.insert(0, _src)
        import llm_client as _lc
        model = getattr(_cfg, 'GIT_COMMIT_SUMMARY_MODEL', 'openrouter/qwen/qwen-2.5-7b-instruct')
        temperature = getattr(_cfg, 'GIT_COMMIT_SUMMARY_TEMPERATURE', 0.3)
        prompt = (
            f"Write a git commit message in 60 chars or less (no quotes, no markdown) "
            f"describing this file change.\n"
            f"File: {path}\n"
            f"Preview:\n{content_hint[:600]}\n\n"
            f"Reply with ONLY the commit message."
        )
        result = _lc.call_llm_raw(prompt=prompt, model=model, temperature=temperature)
        return result.strip()[:60]
    except Exception as e:
        print(f"[Git] commit summary LLM failed ({model}): {e}")
        return ""


_git_lock = __import__('threading').Lock()


def _git_auto_commit(path: str, operation: str, stats: str = "", content_hint: str = ""):
    """git add <path> && git commit after a write/replace operation. Silent on failure."""
    with _git_lock:
        try:
            import config as _cfg
            from datetime import datetime as _dt
            if not getattr(_cfg, 'GIT_VERSION_CONTROL_ENABLE', True):
                return
            abs_path = os.path.abspath(path)
            git_root = _find_git_root(abs_path)
            if git_root is None:
                return
            subprocess.run(['git', 'add', abs_path], capture_output=True, cwd=git_root)
            rel = os.path.relpath(abs_path, git_root)
            timestamp = _dt.now().strftime("%Y-%m-%d %H:%M:%S")
            # Omit diff stats (+N/-M lines) in Plan Mode as requested by user
            is_plan_mode = os.environ.get("PLAN_MODE") == "true"
            stats_part = f" ({stats})" if stats and not is_plan_mode else ""
            mode = getattr(_cfg, 'GIT_COMMIT_MSG_MODE', 'simple')
            if mode == 'summary' and content_hint:
                summary = _llm_commit_summary(rel, content_hint)
                if summary:
                    msg = f"{operation} {rel}{stats_part} — {summary}"
                else:
                    msg = f"{operation} {rel}{stats_part}"
            else:
                msg = f"{operation} {rel}{stats_part}"
            subprocess.run(['git', 'commit', '-m', msg], capture_output=True, cwd=git_root)
        except Exception:
            pass

def _git_tag_todo(index, status, content=""):
    """
    Creates a git tag for todo progress.
    Tag format: todo_{index}_{status}_{slug}
    """
    import re
    try:
        subprocess.run(["git", "rev-parse", "--is-inside-work-tree"], capture_output=True, check=True)
        if content:
            slug = re.sub(r'[^a-zA-Z0-9]+', '_', content).strip('_')[:40].rstrip('_')
            tag_name = f"todo_{index}_{status}_{slug}"
        else:
            tag_name = f"todo_{index}_{status}"
        subprocess.run(["git", "tag", "-f", tag_name], capture_output=True, check=True)
    except Exception:
        pass


def write_file(path: str, content: str) -> str:
    """
    Writes content to a file. Overwrites if exists.

    Args:
        path: File path to write to
        content: Content to write

    Returns:
        Success message with optional lint warnings
    """
    # Import config
    try:
        import config
        ENABLE_LINTING = config.ENABLE_LINTING
    except:
        ENABLE_LINTING = True  # Default to enabled

    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)

        result = f"Successfully wrote to '{path}'."

        # Optional linting
        if ENABLE_LINTING:
            try:
                from core.simple_linter import SimpleLinter
                linter = SimpleLinter()

                # Check file
                errors = linter.check_file(path)

                if errors:
                    # Format errors
                    error_msg = linter.format_errors(errors, max_errors=5)
                    result += f"\n\n⚠️  Linting results:\n{error_msg}\n"
            except Exception:
                # Linting failed, but file was written successfully
                pass

        import threading as _t
        _t.Thread(target=_git_auto_commit, args=(path, "write"), kwargs={"content_hint": content[:800]}, daemon=False).start()
        return result
    except Exception as e:
        return f"Error writing file: {e}"

def _translate_command_for_windows(command: str) -> str:
    """Translate common Unix commands to Windows equivalents."""
    import platform
    if platform.system() != "Windows":
        return command

    import shlex
    # Simple prefix-based translation for common commands
    # Handles: ls, cat, grep, head, tail, which, rm, cp, mv, mkdir -p, touch
    translations = {
        'ls ':     'dir ',
        'ls\n':    'dir',
        'cat ':    'type ',
        'grep ':   'findstr ',
        'head ':   'more ',
        'which ':  'where ',
        'rm ':     'del ',
        'cp ':     'copy ',
        'mv ':     'move ',
        'touch ':  'type nul > ',
        'clear':   'cls',
    }

    stripped = command.lstrip()

    # Exact match (e.g., "ls" alone)
    if stripped == 'ls':
        return 'dir'
    if stripped == 'clear':
        return 'cls'
    if stripped == 'pwd':
        return 'cd'

    # Compound commands first (before simple prefix match)
    # mkdir -p → mkdir (Windows mkdir creates parents by default)
    if stripped.startswith('mkdir -p '):
        return 'mkdir ' + stripped[len('mkdir -p '):]

    # rm -rf / rm -r → rmdir /s /q
    if stripped.startswith('rm -rf ') or stripped.startswith('rm -r '):
        path = stripped.split(' ', 2)[-1]
        return f'rmdir /s /q {path}'

    # Simple prefix match
    for unix_cmd, win_cmd in translations.items():
        if stripped.startswith(unix_cmd):
            return win_cmd + stripped[len(unix_cmd):]

    return command


def run_command(command, timeout=60):
    """
    Runs a shell command and returns output.

    Args:
        command: The shell command to run.
        timeout: Optional timeout in seconds (default: 60).
    """
    try:
        # Strictly block mv and rm as per user request
        if _is_dangerous_command(command):
            return f"Error: Command '{command.split()[0]}' is blocked (mv and rm are not allowed in run_command)."

        # Translate Unix commands to Windows equivalents
        command = _translate_command_for_windows(command)

        import time

        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            timeout=timeout
        )
        
        stdout_str = result.stdout or ""
        stderr_str = result.stderr or ""
        
        full_output = stdout_str
        if stderr_str:
            full_output += f"\nSTDERR:\n{stderr_str}"
        
        full_output = full_output.strip()
        
        # Output Truncation Logic
        MAX_CHARS = 2000
        if len(full_output) > MAX_CHARS:
            timestamp = int(time.time())
            log_filename = f"cmd_output_{timestamp}.txt"
            log_path = os.path.abspath(log_filename)
            
            try:
                with open(log_path, "w", encoding="utf-8") as f:
                    f.write(full_output)
                
                summary = full_output[:500] + f"\n\n... (Output truncated via run_command tool) ...\n... (Total extracted chars: {len(full_output)}) ...\n\n[Full output saved to: {log_path}]\n"
                if stderr_str:
                     summary += f"[STDERR was present check log for details]"
                return summary
            except Exception as write_err:
                return full_output[:MAX_CHARS] + f"\n... (Truncated, and failed to write log: {write_err})"
        
        return full_output
    except subprocess.TimeoutExpired:
        return "Error: Command timed out."
    except Exception as e:
        return f"Error running command: {e}"


def _is_dangerous_command(command: str) -> bool:
    """
    Heuristic check for destructive commands.
    Used only when SAFE_MODE=true.
    """
    cmd = (command or "").strip().lower()
    if not cmd:
        return False

    # Block common destructive patterns.
    dangerous_patterns = [
        r"\brm\b",                        # block all rm commands
        r"\bmv\b",                        # block all mv commands
        r"\bsudo\b",                      # privilege escalation
        r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b",
        r"\bmkfs\b|\bdd\b\s+if=",
        r"\bgit\b\s+reset\s+--hard\b",
        r"\bgit\b\s+clean\b.*-f",
    ]

    return any(re.search(pat, cmd) for pat in dangerous_patterns)

def list_dir(path=".", show_hidden=True, **kwargs):
    """
    Lists files in a directory.
    Args:
        path: Directory path (default: ".")
        show_hidden: Whether to show hidden files (starting with .)
    """
    try:
        if os.path.isfile(path):
            return f"'{path}' is a file, not a directory. Use read_file() or grep_file() instead."
        if not os.path.exists(path):
            return f"'{path}' does not exist. Use find_files() to locate the correct path."
        files = os.listdir(path)
        if not show_hidden:
            files = [f for f in files if not f.startswith('.')]
        return "\n".join(sorted(files))
    except Exception as e:
        return f"Error listing directory: {e}"

def grep_file(pattern, path, context_lines=2, recursive=False, **kwargs):
    """
    Searches for a pattern using system tools (git grep/grep) for performance.
    
    Args:
        pattern: Regex pattern to search for
        path: Path to file or directory
        context_lines: Number of context lines (default: 2)
        recursive: Whether to search recursively (default: False)
        **kwargs: Additional arguments (ignored, for robustness)
        
    Returns:
        Formatted matches string
    """
    import subprocess
    import sys
    
    # Python fallback implementation (for backup)
    def _grep_python(pat, pth, ctx, rec):
        import re
        import glob
        try:
            is_glob = any(char in pth for char in ['*', '?', '[', ']'])
            if rec and not is_glob and os.path.isdir(pth):
                pth = os.path.join(pth, '**', '*')
                is_glob = True

            if is_glob or rec:
                files = glob.glob(pth, recursive=True)
                if not files: return f"No files found matching '{pth}'"
                if len(files) > 1000: return f"Error: Too many files ({len(files)})"
                
                results = []
                count = 0
                for f in sorted(files):
                    if os.path.isdir(f): continue
                    res = _grep_python(pat, f, ctx, False)
                    if not res.startswith("No matches") and not res.startswith("Error"):
                        results.append(f"=== Matches in {f} ===\n{res}\n")
                        count += 1
                        if count >= 20: 
                            results.append("... (Stopped after 20 files) ...")
                            break
                return "\n".join(results) if results else f"No matches found for '{pat}'"

            # File search
            if not os.path.exists(pth): return f"Error: '{pth}' not found. Use find_files() to locate the correct path."
            if os.path.isdir(pth): return f"Error: '{pth}' is a dir"
            
            with open(pth, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()
            
            matches = []
            regex = re.compile(pat)
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    start = max(1, i - ctx)
                    end = min(len(lines), i + ctx)
                    block = []
                    for j in range(start, end + 1):
                        prefix = ">>> " if j == i else "    "
                        block.append(f"{prefix}{j:4d}: {lines[j-1].rstrip()}")
                    matches.append("\n".join(block))
            
            return f"Found {len(matches)} matches in {pth}:\n\n" + "\n...\n".join(matches) if matches else f"No matches found for '{pat}' in {pth}"
            
        except Exception as e:
            return f"Error (Python grep): {e}"

    # Try system tools
    try:
        cmd = []
        # is_git = os.path.isdir(".git") and not os.path.isabs(path) # Removed git check priority
        
        # 1. Choose Tool - SYSTEM GREP PRIORITY (User Request)
        # Try system grep (BSD/GNU) first
        cmd = ["grep", "-I", "-n", f"-C{context_lines}", "-E", "-e", pattern]
        if recursive:
            cmd.append("-r")
            # Smart excludes to avoid cluttering results
            cmd.extend(["--exclude-dir=.git", "--exclude-dir=__pycache__", "--exclude-dir=.venv", "--exclude-dir=venv"])
        
        # Handle directory target for non-recursive grep
        if os.path.isdir(path) and not recursive:
             # grep without -r on dir will error or do nothing.
             # Fallback to Python for non-recursive dir search
             return _grep_python(pattern, path, context_lines, recursive)
        
        cmd.append(path)

        # 2. Run Command
        process = subprocess.run(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            timeout=10,
            encoding='utf-8',
            errors='replace'
        )
        
        if process.returncode > 1:
            # Error occurred (1 is just no matches)
            # Fallback if tool failed options
            return _grep_python(pattern, path, context_lines, recursive)
            
        output = process.stdout
        if not output:
             return f"No matches found for pattern '{pattern}'"

        # 3. Formatter
        # We need to parse grep output to match our friendly format
        # Grep format: filename:line:content OR filename-line-content (context)
        # But wait, our tools need to be robust.
        
        # Let's just return the raw grep output if it's readable, BUT the user expects the specific format 
        # for other tools to consume it? 
        # Actually, the agent reads it. Standard grep output is fine, but let's make it slightly nicer.
        
        # Split by file
        lines = output.splitlines()
        formatted_output = []
        current_file = None
        current_matches = []
        
        # Helper to dump matches for a file
        def dump_current():
            if current_file and current_matches:
                formatted_output.append(f"=== Matches in {current_file} ===")
                formatted_output.append("\n".join(current_matches))
                formatted_output.append("")

        for line in lines:
            # Parse typical grep output: file:line:content or file-line-content
            # Special handling for "--" separators
            if line == "--":
                current_matches.append("...")
                continue
                
            # ATTEMPT 1: Recursive/Multi-file output (filename:line:content)
            parts = line.split(':', 2)
            is_match = True
            
            if len(parts) >= 3 and parts[1].isdigit():
                # Format: filename:123:content
                fname = parts[0]
                lineno = int(parts[1])
                content = parts[2]
            elif len(parts) == 2 and parts[0].isdigit():
                 # ATTEMPT 2: Single file output (line:content) - Grep behavior on single file
                 # In this case, filename is 'path'
                 fname = path
                 lineno = int(parts[0])
                 content = parts[1]
            else:
                # Context lines? (filename-123-content or 123-content)
                parts_ctx = line.split('-', 2)
                is_match = False
                if len(parts_ctx) >= 3 and parts_ctx[1].isdigit():
                    fname = parts_ctx[0]
                    lineno = int(parts_ctx[1])
                    content = parts_ctx[2]
                elif len(parts_ctx) == 2 and parts_ctx[0].isdigit():
                    fname = path
                    lineno = int(parts_ctx[0])
                    content = parts_ctx[1]
                else:
                    # Parse failed, preserve line
                    if current_file: current_matches.append(line)
                    elif not current_file and lines:
                         # Single file mode, treat as content if we can't parse
                         # But wait, we need to start a block
                         current_file = path
                         current_matches.append(line)
                    continue

            # If we parsed successfully
            if fname != current_file:
                dump_current()
                current_file = fname
                current_matches = []
            
            prefix = ">>> " if is_match else "    "
            current_matches.append(f"{prefix}{lineno:4d}: {content}")

        dump_current()
        
        if not formatted_output:
             # Fallback if parsing failed drastically (e.g. filename only output)
             return f"Raw Grep Output:\n{output}"

        return "\n".join(formatted_output)

    except Exception as e:
        # Final fallback
        return _grep_python(pattern, path, context_lines, recursive)

def read_lines(path, start_line, end_line):
    """
    Reads a specific range of lines from a file.
    Args:
        path: Path to the file
        start_line: Starting line number (1-based, inclusive)
        end_line: Ending line number (1-based, inclusive)
    Returns:
        Content of the specified line range with line numbers
    """
    try:
        if not os.path.exists(path):
            import glob
            basename = os.path.basename(path)
            suggestions = glob.glob(os.path.join("**", basename), recursive=True)[:3]
            if suggestions:
                hint = ", ".join(f"'{s}'" for s in suggestions)
                return f"Error: File '{path}' does not exist. Did you mean: {hint}?"
            return f"Error: File '{path}' does not exist. Use find_files('{basename}') to locate it."

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Validate line numbers
        if start_line < 1 or end_line < 1:
            return "Error: Line numbers must be >= 1"
        if start_line > end_line:
            return "Error: start_line must be <= end_line"
        if start_line > total_lines:
            return f"Error: start_line {start_line} is beyond file length ({total_lines} lines)"
        
        # Adjust end_line if it exceeds file length
        end_line = min(end_line, total_lines)
        
        # Build output
        result = f"Lines {start_line}-{end_line} of {path} (total: {total_lines} lines):\n\n"
        for i in range(start_line - 1, end_line):
            result += f"{i+1:4d}: {lines[i].rstrip()}\n"
        
        return result
    except Exception as e:
        return f"Error reading lines: {e}"

def find_files(pattern, directory=".", max_depth=None, path=None, recursive=True):
    """
    Finds files matching a pattern in a directory.
    Args:
        pattern: Filename pattern (supports wildcards: *.py, test_*.v, etc.)
        directory: Directory to search in (default: current directory)
        max_depth: Maximum depth to search (None for unlimited)
        path: Alias for 'directory' (for LLM compatibility)
        recursive: Whether to search recursively (default: True)
    Returns:
        List of matching file paths
    """
    import fnmatch
    try:
        # Support 'path' as alias for 'directory'
        if path is not None:
            directory = path
            
        # Handle recursive parameter
        if not recursive:
            max_depth = 0
        
        if not os.path.exists(directory):
            return f"Error: Directory '{directory}' does not exist."
        
        matches = []
        
        for root, dirs, files in os.walk(directory):
            # Calculate current depth
            depth = root[len(directory):].count(os.sep)
            if max_depth is not None and depth > max_depth:
                dirs.clear()  # Don't recurse deeper
                continue
            
            for filename in files:
                if fnmatch.fnmatch(filename, pattern):
                    full_path = os.path.join(root, filename)
                    # Make path relative to directory for cleaner output
                    rel_path = os.path.relpath(full_path, directory)
                    matches.append(rel_path)
        
        if not matches:
            # Smart Fallback: Check parent directory (1 level up)
            # Only if directory is relative or not root
            msg = f"No files matching '{pattern}' found in {directory}"
            
            try:
                parent_dir = os.path.join(directory, "..")
                # Normalize to avoid scanning same dir if directory was "."
                if os.path.abspath(directory) != os.path.abspath(parent_dir) and os.path.exists(parent_dir):
                    parent_matches = []
                    # Shallow search in parent (depth 2 to avoid huge scans)
                    for root, dirs, files in os.walk(parent_dir):
                        depth = root[len(parent_dir):].count(os.sep)
                        if depth > 2:
                            dirs.clear()
                            continue
                        
                        for filename in files:
                            if fnmatch.fnmatch(filename, pattern):
                                full_path = os.path.join(root, filename)
                                rel_path = os.path.relpath(full_path, directory) # Relative to ORIGINAL search dir (so starts with ../)
                                parent_matches.append(rel_path)
                                
                    if parent_matches:
                        msg += f"\n\n💡 Hint: Found {len(parent_matches)} matching file(s) in parent directory ('..'):\n"
                        # Limit hint output
                        limit = 10
                        msg += "\n".join(f"  - {m}" for m in sorted(parent_matches)[:limit])
                        if len(parent_matches) > limit:
                            msg += f"\n  ...and {len(parent_matches)-limit} more"
            except Exception:
                pass # Fallback shouldn't break the original error
                
            return msg
        
        MAX_RESULTS = 100
        sorted_matches = sorted(matches)
        result = f"Found {len(matches)} file(s) matching '{pattern}':\n"
        result += "\n".join(f"  - {m}" for m in sorted_matches[:MAX_RESULTS])
        if len(matches) > MAX_RESULTS:
            result += f"\n  ... and {len(matches) - MAX_RESULTS} more files (narrow your search with a more specific path or pattern)"
        return result
    except Exception as e:
        return f"Error finding files: {e}"

def git_diff(path=None):
    """
    Shows git diff for unstaged changes.
    Args:
        path: Optional specific file path (default: all changes)
    Returns:
        Git diff output
    """
    try:
        cmd = "git diff"
        if path:
            if not os.path.exists(path):
                return f"Error: Path '{path}' does not exist."
            cmd += f" {path}"
        
        result = subprocess.run(
            cmd,
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return f"Git error: {result.stderr}"
        
        output = result.stdout.strip()
        if not output:
            return "No changes detected (working tree is clean)."
        
        return output
    except subprocess.TimeoutExpired:
        return "Error: Git diff timed out."
    except Exception as e:
        return f"Error running git diff: {e}"

def git_status():
    """
    Shows current git status in short format.
    Returns:
        Git status output
    """
    try:
        result = subprocess.run(
            "git status --short",
            shell=True,
            capture_output=True,
            text=True,
            timeout=10
        )
        
        if result.returncode != 0:
            return f"Git error: {result.stderr}"
        
        output = result.stdout.strip()
        if not output:
            return "Working tree is clean (no changes)."
        
        return f"Git status:\n{output}"
    except subprocess.TimeoutExpired:
        return "Error: Git status timed out."
    except Exception as e:
        return f"Error running git status: {e}"

def git_revert(path: str) -> str:
    """
    Reverts uncommitted changes to a file using git.
    Args:
        path: Path to the file to revert.
    """
    try:
        # Use abspath to correctly find git root
        abs_path = os.path.abspath(path)
        if not os.path.exists(abs_path):
            return f"Error: Path '{path}' does not exist."
            
        git_root = _find_git_root(abs_path)
        if git_root is None:
            return f"Error: '{path}' is not in a git repository."

        # Attempt git restore (modern)
        result = subprocess.run(
            ['git', 'restore', abs_path],
            capture_output=True,
            text=True,
            cwd=git_root
        )
        
        if result.returncode == 0:
            return f"Successfully reverted changes to '{path}' using git restore."
        
        # Fallback to git checkout
        result = subprocess.run(
            ['git', 'checkout', 'HEAD', '--', abs_path],
            capture_output=True,
            text=True,
            cwd=git_root
        )
        
        if result.returncode == 0:
            return f"Successfully reverted changes to '{path}' using git checkout."
        else:
            return f"Error reverting file: {result.stderr}"
            
    except Exception as e:
        return f"Error reverting file: {e}"

def replace_in_file(path, old_text, new_text, count=-1, start_line=None, end_line=None, fuzzy_whitespace=True):
    """
    Replaces occurrences of text in a file.
    Args:
        path: Path to the file
        old_text: Text to find and replace
        new_text: Text to replace with
        count: Maximum number of replacements (-1 for all occurrences)
        start_line: Optional starting line number (1-indexed, inclusive)
        end_line: Optional ending line number (1-indexed, inclusive)
        fuzzy_whitespace: If True (default), normalize leading whitespace for matching
                         This helps when LLM provides slightly wrong indentation
    Returns:
        Success message with number of replacements made
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        # Determine working range
        start_idx = 0
        end_idx = len(lines)
        
        if start_line is not None:
            start_idx = max(0, int(start_line) - 1)
        if end_line is not None:
            end_idx = min(len(lines), int(end_line))
            
        target_lines = lines[start_idx:end_idx]
        target_content = "".join(target_lines)
        
        # Count occurrences before replacement
        occurrences = target_content.count(old_text)
        
        # OpenCode-style fuzzy matching: try 8 strategies in order
        actual_old_text = old_text
        matched_strategy = None

        if occurrences == 0 and fuzzy_whitespace:
            # Try each replacer strategy in order (skip SimpleReplacer as we already tried exact match)
            matched_text = None

            for strategy_name, replacer in [
                ("LineTrimmedReplacer", _line_trimmed_replacer),
                ("BlockAnchorReplacer", _block_anchor_replacer),
                ("WhitespaceNormalizedReplacer", _whitespace_normalized_replacer),
                ("IndentationFlexibleReplacer", _indentation_flexible_replacer),
                ("EscapeNormalizedReplacer", _escape_normalized_replacer),
                ("TrimmedBoundaryReplacer", _trimmed_boundary_replacer),
                ("ContextAwareReplacer", _context_aware_replacer),
            ]:
                for candidate in replacer(target_content, old_text):
                    # Check if this candidate is unique
                    candidate_count = target_content.count(candidate)
                    if candidate_count == 1:
                        # Perfect: unique match found
                        matched_text = candidate
                        matched_strategy = strategy_name
                        break
                    elif candidate_count > 0 and matched_text is None:
                        # Store as potential match but keep trying for unique one
                        matched_text = candidate
                        matched_strategy = strategy_name

                # If we found a unique match, stop searching
                if matched_text and target_content.count(matched_text) == 1:
                    break

            if matched_text:
                actual_old_text = matched_text
                occurrences = target_content.count(actual_old_text)
        
        if occurrences == 0:
            range_msg = f" in lines {start_line}-{end_line}" if start_line is not None else ""
            # Provide helpful recovery steps
            hint = f"""

❌ Text not found in {path}{range_msg}

💡 RECOVERY STEPS (ALWAYS READ FIRST):

1. Read the file to see exact formatting:
   Action: read_file(path="{path}")
   # OR for specific range:
   Action: read_lines(path="{path}", start_line=<N>, end_line=<M>)

2. Copy EXACT text from output (after → symbol):
   - Remove line number prefix (e.g., '42→')
   - Preserve exact indentation/spacing
   - Include 5-10 lines of context

3. Try replacement again with exact copy

Common issues:
- Wrong indentation (tabs vs spaces)
- Missing/extra whitespace
- Text doesn't exist in file (verify with grep_file first)
"""
            return hint
        
        # IMPROVEMENT: Uniqueness Safety Check
        # Strict logic: range required for multi-match unless count is specified.
        if start_line is None and end_line is None and occurrences > 1 and count == -1:
             return f"""
❌ Ambiguous replacement: Found {occurrences} occurrences in {path}

💡 SOLUTION OPTIONS:

1. Make old_text MORE SPECIFIC (add context):
   - Include 5-10 lines of surrounding code
   - Add unique function/class name above
   - Use read_file() to see full context

2. Use line range to narrow scope:
   Action: replace_in_file(
       path="{path}",
       old_text="...",
       new_text="...",
       start_line=<start>,
       end_line=<end>
   )

3. Replace only first N occurrences:
   Action: replace_in_file(..., count=1)  # First only
   Action: replace_in_file(..., count={occurrences})  # All {occurrences}

⚠️  Replacing all {occurrences} occurrences requires confirmation.
"""
        
        # Auto-adjust indentation: if fuzzy matched, align new_text indent to actual match
        if actual_old_text != old_text:
            # Detect indent difference between what LLM gave and what's actually in file
            old_lines = old_text.split('\n')
            actual_lines = actual_old_text.split('\n')
            if old_lines and actual_lines:
                old_indent = len(old_lines[0]) - len(old_lines[0].lstrip())
                actual_indent = len(actual_lines[0]) - len(actual_lines[0].lstrip())
                indent_diff = actual_indent - old_indent
                if indent_diff != 0:
                    # Apply indent adjustment to new_text
                    adjusted_lines = []
                    for nl in new_text.split('\n'):
                        if indent_diff > 0:
                            adjusted_lines.append(' ' * indent_diff + nl)
                        else:
                            # Remove indent (but don't go negative)
                            strip_n = min(-indent_diff, len(nl) - len(nl.lstrip()))
                            adjusted_lines.append(nl[strip_n:])
                    new_text = '\n'.join(adjusted_lines)

        # Perform replacement
        if count == -1:
            new_target_content = target_content.replace(actual_old_text, new_text)
            replacements = occurrences
        else:
            new_target_content = target_content.replace(actual_old_text, new_text, count)
            replacements = min(count, occurrences)
            
        # Reconstruct full content
        full_prefix = "".join(lines[:start_idx])
        full_suffix = "".join(lines[end_idx:])
        new_full_content = full_prefix + new_target_content + full_suffix
        
        # Generate clean snippet diff before writing
        old_full_content = "".join(lines)

        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_full_content)

        # Generate diff snippet AFTER writing (so we show final state)
        diff_output = format_diff_snippet(path, old_full_content, new_full_content, context_lines=3)

        result = f"Replaced {replacements} occurrence(s) in {path}\n"
        if actual_old_text != old_text:
            if matched_strategy:
                result += f"(Fuzzy matched using: {matched_strategy})\n"
            else:
                result += f"(Fuzzy matched: adjusted whitespace)\n"
        result += f"\n{diff_output}"
        added = len(new_text.splitlines())
        removed = len(actual_old_text.splitlines())
        hint = f"--- old ---\n{actual_old_text[:400]}\n--- new ---\n{new_text[:400]}"
        import threading as _t
        _t.Thread(target=_git_auto_commit, args=(path, "replace"), kwargs={"stats": f"+{added}/-{removed} lines", "content_hint": hint}, daemon=False).start()
        return result
    except Exception as e:
        return f"Error replacing text: {e}"

# ============================================================================
# OpenCode-style Fuzzy Matching Strategies (9 Replacers)
# Ported from: opencode/packages/opencode/src/tool/edit.ts
# Original sources: Cline, Gemini CLI edit correctors
# ============================================================================

# Constants for BlockAnchorReplacer
SINGLE_CANDIDATE_SIMILARITY_THRESHOLD = 0.0
MULTIPLE_CANDIDATES_SIMILARITY_THRESHOLD = 0.3

def _levenshtein(a, b):
    """
    Levenshtein distance algorithm implementation.
    Calculates the minimum edit distance between two strings.
    """
    if not a or not b:
        return max(len(a), len(b))

    # Create matrix
    matrix = [[0] * (len(b) + 1) for _ in range(len(a) + 1)]

    # Initialize first row and column
    for i in range(len(a) + 1):
        matrix[i][0] = i
    for j in range(len(b) + 1):
        matrix[0][j] = j

    # Fill matrix
    for i in range(1, len(a) + 1):
        for j in range(1, len(b) + 1):
            cost = 0 if a[i-1] == b[j-1] else 1
            matrix[i][j] = min(
                matrix[i-1][j] + 1,      # deletion
                matrix[i][j-1] + 1,      # insertion
                matrix[i-1][j-1] + cost  # substitution
            )

    return matrix[len(a)][len(b)]

def _simple_replacer(content, find):
    """Strategy 1: Exact match."""
    yield find

def _line_trimmed_replacer(content, find):
    """
    Strategy 2: Line-by-line trimmed matching.
    Matches when each line is trimmed but structure is preserved.
    """
    original_lines = content.split('\n')
    search_lines = find.split('\n')

    # Remove trailing empty line if present
    if search_lines and search_lines[-1] == '':
        search_lines.pop()

    # Try to find matching blocks
    for i in range(len(original_lines) - len(search_lines) + 1):
        matches = True

        for j in range(len(search_lines)):
            original_trimmed = original_lines[i + j].strip()
            search_trimmed = search_lines[j].strip()

            if original_trimmed != search_trimmed:
                matches = False
                break

        if matches:
            # Calculate the exact substring from content
            match_start = sum(len(original_lines[k]) + 1 for k in range(i))
            match_end = match_start

            for k in range(len(search_lines)):
                match_end += len(original_lines[i + k])
                if k < len(search_lines) - 1:
                    match_end += 1  # newline

            yield content[match_start:match_end]

def _block_anchor_replacer(content, find):
    """
    Strategy 3: Block anchor matching with Levenshtein similarity.
    Matches blocks by first/last line anchors, validates middle with similarity.
    """
    original_lines = content.split('\n')
    search_lines = find.split('\n')

    if len(search_lines) < 3:
        return  # Need at least 3 lines for meaningful anchoring

    if search_lines and search_lines[-1] == '':
        search_lines.pop()

    first_line_search = search_lines[0].strip()
    last_line_search = search_lines[-1].strip()
    search_block_size = len(search_lines)

    # Find all candidate blocks where first and last lines match
    candidates = []
    for i in range(len(original_lines)):
        if original_lines[i].strip() != first_line_search:
            continue

        # Look for matching last line
        for j in range(i + 2, len(original_lines)):
            if original_lines[j].strip() == last_line_search:
                candidates.append({'start_line': i, 'end_line': j})
                break  # Only first occurrence

    if not candidates:
        return

    # Single candidate - use relaxed threshold
    if len(candidates) == 1:
        candidate = candidates[0]
        start_line = candidate['start_line']
        end_line = candidate['end_line']
        actual_block_size = end_line - start_line + 1

        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_block_size - 2)

        if lines_to_check > 0:
            for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                original_line = original_lines[start_line + j].strip()
                search_line = search_lines[j].strip()
                max_len = max(len(original_line), len(search_line))

                if max_len == 0:
                    continue

                distance = _levenshtein(original_line, search_line)
                similarity += (1 - distance / max_len) / lines_to_check

                if similarity >= SINGLE_CANDIDATE_SIMILARITY_THRESHOLD:
                    break
        else:
            similarity = 1.0

        if similarity >= SINGLE_CANDIDATE_SIMILARITY_THRESHOLD:
            match_start = sum(len(original_lines[k]) + 1 for k in range(start_line))
            match_end = match_start
            for k in range(start_line, end_line + 1):
                match_end += len(original_lines[k])
                if k < end_line:
                    match_end += 1
            yield content[match_start:match_end]
        return

    # Multiple candidates - find best match
    best_match = None
    max_similarity = -1

    for candidate in candidates:
        start_line = candidate['start_line']
        end_line = candidate['end_line']
        actual_block_size = end_line - start_line + 1

        similarity = 0.0
        lines_to_check = min(search_block_size - 2, actual_block_size - 2)

        if lines_to_check > 0:
            for j in range(1, min(search_block_size - 1, actual_block_size - 1)):
                original_line = original_lines[start_line + j].strip()
                search_line = search_lines[j].strip()
                max_len = max(len(original_line), len(search_line))

                if max_len == 0:
                    continue

                distance = _levenshtein(original_line, search_line)
                similarity += 1 - distance / max_len

            similarity /= lines_to_check
        else:
            similarity = 1.0

        if similarity > max_similarity:
            max_similarity = similarity
            best_match = candidate

    if max_similarity >= MULTIPLE_CANDIDATES_SIMILARITY_THRESHOLD and best_match:
        start_line = best_match['start_line']
        end_line = best_match['end_line']
        match_start = sum(len(original_lines[k]) + 1 for k in range(start_line))
        match_end = match_start
        for k in range(start_line, end_line + 1):
            match_end += len(original_lines[k])
            if k < end_line:
                match_end += 1
        yield content[match_start:match_end]

def _whitespace_normalized_replacer(content, find):
    """
    Strategy 4: Whitespace normalization.
    Collapses consecutive whitespace to single space for matching.
    """
    import re

    def normalize_whitespace(text):
        return re.sub(r'\s+', ' ', text).strip()

    normalized_find = normalize_whitespace(find)

    # Try single-line matches
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if normalize_whitespace(line) == normalized_find:
            yield line
        else:
            # Check substring match
            normalized_line = normalize_whitespace(line)
            if normalized_find in normalized_line:
                # Find actual substring with regex
                words = find.strip().split()
                if words:
                    pattern = r'\s+'.join(re.escape(word) for word in words)
                    try:
                        match = re.search(pattern, line)
                        if match:
                            yield match.group(0)
                    except re.error:
                        pass

    # Try multi-line matches
    find_lines = find.split('\n')
    if len(find_lines) > 1:
        for i in range(len(lines) - len(find_lines) + 1):
            block = lines[i:i + len(find_lines)]
            if normalize_whitespace('\n'.join(block)) == normalized_find:
                yield '\n'.join(block)

def _indentation_flexible_replacer(content, find):
    """
    Strategy 5: Indentation-flexible matching.
    Ignores absolute indentation, preserves relative indentation.
    """
    def remove_indentation(text):
        lines = text.split('\n')
        non_empty_lines = [line for line in lines if line.strip()]

        if not non_empty_lines:
            return text

        # Find minimum indentation
        min_indent = min(
            len(line) - len(line.lstrip())
            for line in non_empty_lines
        )

        # Remove minimum indentation from all lines
        result_lines = []
        for line in lines:
            if line.strip():
                result_lines.append(line[min_indent:] if len(line) >= min_indent else line)
            else:
                result_lines.append(line)

        return '\n'.join(result_lines)

    normalized_find = remove_indentation(find)
    content_lines = content.split('\n')
    find_lines = find.split('\n')

    for i in range(len(content_lines) - len(find_lines) + 1):
        block = '\n'.join(content_lines[i:i + len(find_lines)])
        if remove_indentation(block) == normalized_find:
            yield block

def _escape_normalized_replacer(content, find):
    """
    Strategy 6: Escape sequence normalization.
    Handles escaped characters like \\n, \\t, etc.
    """
    def unescape_string(s):
        """Unescape common escape sequences."""
        replacements = {
            '\\n': '\n',
            '\\t': '\t',
            '\\r': '\r',
            "\\'": "'",
            '\\"': '"',
            '\\`': '`',
            '\\\\': '\\',
            '\\$': '$'
        }
        result = s
        for escaped, unescaped in replacements.items():
            result = result.replace(escaped, unescaped)
        return result

    unescaped_find = unescape_string(find)

    # Try direct match with unescaped
    if unescaped_find in content:
        yield unescaped_find

    # Try finding escaped versions in content
    lines = content.split('\n')
    find_lines = unescaped_find.split('\n')

    for i in range(len(lines) - len(find_lines) + 1):
        block = '\n'.join(lines[i:i + len(find_lines)])
        if unescape_string(block) == unescaped_find:
            yield block

def _trimmed_boundary_replacer(content, find):
    """
    Strategy 7: Trimmed boundary matching.
    Tries matching after trimming leading/trailing whitespace.
    """
    trimmed_find = find.strip()

    if trimmed_find == find:
        return  # Already trimmed, no point trying

    # Try exact trimmed match
    if trimmed_find in content:
        yield trimmed_find

    # Try finding blocks where trimmed content matches
    lines = content.split('\n')
    find_lines = find.split('\n')

    for i in range(len(lines) - len(find_lines) + 1):
        block = '\n'.join(lines[i:i + len(find_lines)])
        if block.strip() == trimmed_find:
            yield block

def _context_aware_replacer(content, find):
    """
    Strategy 8: Context-aware matching.
    Uses first and last lines as anchors, validates middle with 50% similarity.
    """
    find_lines = find.split('\n')

    if len(find_lines) < 3:
        return  # Need at least 3 lines

    # Remove trailing empty line
    if find_lines and find_lines[-1] == '':
        find_lines.pop()

    content_lines = content.split('\n')

    # Extract anchor lines
    first_line = find_lines[0].strip()
    last_line = find_lines[-1].strip()

    # Find blocks starting and ending with anchors
    for i in range(len(content_lines)):
        if content_lines[i].strip() != first_line:
            continue

        # Look for matching last line
        for j in range(i + 2, len(content_lines)):
            if content_lines[j].strip() == last_line:
                # Found potential block
                block_lines = content_lines[i:j + 1]

                # Check if block size matches
                if len(block_lines) == len(find_lines):
                    # Check middle line similarity (at least 50%)
                    matching_lines = 0
                    total_non_empty = 0

                    for k in range(1, len(block_lines) - 1):
                        block_line = block_lines[k].strip()
                        find_line = find_lines[k].strip()

                        if block_line or find_line:
                            total_non_empty += 1
                            if block_line == find_line:
                                matching_lines += 1

                    if total_non_empty == 0 or matching_lines / total_non_empty >= 0.5:
                        yield '\n'.join(block_lines)
                        return  # Only first match
                break

# End of OpenCode-style Replacers
# ============================================================================

def _fuzzy_find_text(content, pattern):
    """
    Find pattern in content with fuzzy whitespace matching.
    Returns the actual text found in content, or None if not found.
    """
    import re
    
    # Split pattern into lines
    pattern_lines = pattern.split('\n')
    if not pattern_lines:
        return None
    
    # Create regex pattern that matches any leading whitespace
    # For each line, escape special chars but allow flexible leading whitespace
    regex_parts = []
    for line in pattern_lines:
        stripped = line.lstrip()
        if stripped:
            # Allow any amount of leading whitespace
            escaped = re.escape(stripped)
            regex_parts.append(r'[ \t]*' + escaped)
        else:
            # Empty or whitespace-only line
            regex_parts.append(r'[ \t]*')
    
    # Join with newline matching (allow \n or \r\n)
    full_regex = r'\n'.join(regex_parts)
    
    try:
        match = re.search(full_regex, content)
        if match:
            return match.group(0)
    except re.error:
        pass
    
    return None

def replace_lines(path, start_line, end_line, new_content):
    """
    Replaces a range of lines in a file with new content.
    Args:
        path: Path to the file
        start_line: Starting line number (1-based, inclusive)
        end_line: Ending line number (1-based, inclusive)
        new_content: New content to replace the lines with
    Returns:
        Success message
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        
        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()
        
        total_lines = len(lines)
        
        # Validate line numbers
        if start_line < 1 or end_line < 1:
            return "Error: Line numbers must be >= 1"
        if start_line > end_line:
            return "Error: start_line must be <= end_line"
        if start_line > total_lines:
            return f"Error: start_line {start_line} is beyond file length ({total_lines} lines)"
        
        # Adjust end_line if it exceeds file length
        end_line = min(end_line, total_lines)
        
        # Ensure new_content ends with newline if it doesn't already
        if new_content and not new_content.endswith('\n'):
            new_content += '\n'
        
        # Build new file content
        new_lines = (
            lines[:start_line - 1] +  # Lines before replacement
            [new_content] +            # New content
            lines[end_line:]           # Lines after replacement
        )
        
        # Generate clean snippet diff
        old_content = "".join(lines)
        new_content_full = "".join(new_lines)

        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        # Generate diff snippet AFTER writing (shows final state)
        diff_output = format_diff_snippet(path, old_content, new_content_full, context_lines=3)

        lines_removed = end_line - start_line + 1
        result = f"Replaced lines {start_line}-{end_line} ({lines_removed} lines) in {path}\n"
        result += f"\n{diff_output}"
        return result
    except Exception as e:
        return f"Error replacing lines: {e}"

# ==================== RAG Tools ====================

# Phase B: Helper functions for cross-reference following

def _is_acronym_query(query: str) -> bool:
    """
    Check if query is asking for an acronym definition.

    Patterns:
    - "What does OHC stand for?"
    - "OHC stands for"
    - "Define TLP"
    - "What is ECRC?"

    Returns:
        True if query appears to be asking for acronym definition
    """
    import re

    patterns = [
        r"\bwhat (?:does|is) \w+ stand for\b",
        r"\b\w+ (?:stands for|means|definition)\b",
        r"\bdefine \w+\b",
        r"\bwhat is \w+\b",
        r"\bwhat does \w+ mean\b",
    ]
    query_lower = query.lower()
    return any(re.search(p, query_lower) for p in patterns)


def _extract_references(text):
    """
    Extract cross-references from text using pattern matching.

    Patterns:
    - "See Section X.Y"
    - "Refer to §X.Y"
    - "Table X-Y"
    - "[Related: name]"

    Returns:
        List of reference strings
    """
    import re

    references = []

    # Pattern 1: Section references (e.g., "Section 2.3", "§3.1")
    section_patterns = [
        r'[Ss]ection\s+(\d+(?:\.\d+)*)',
        r'§\s*(\d+(?:\.\d+)*)',
        r'\$\s*(\d+(?:\.\d+)*)',  # Alternative section marker
    ]
    for pattern in section_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            references.append(f"Section {match}")

    # Pattern 2: Table references (e.g., "Table 2-1", "Table 3.2")
    table_patterns = [
        r'[Tt]able\s+(\d+[\-\.]\d+)',
        r'[Tt]able\s+(\d+)',
    ]
    for pattern in table_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            references.append(f"Table {match}")

    # Pattern 3: Figure references
    figure_patterns = [
        r'[Ff]igure\s+(\d+[\-\.]\d+)',
        r'[Ff]ig\.\s+(\d+)',
    ]
    for pattern in figure_patterns:
        matches = re.findall(pattern, text)
        for match in matches:
            references.append(f"Figure {match}")

    # Pattern 4: [Related: ...] or [See: ...]
    related_pattern = r'\[(?:Related|See):\s*([^\]]+)\]'
    matches = re.findall(related_pattern, text, re.IGNORECASE)
    references.extend(matches)

    return list(set(references))  # Remove duplicates


def _follow_cross_references(results, original_query, categories, max_follow=3):
    """
    Follow cross-references found in search results.

    Args:
        results: List of (score, chunk) tuples from initial search
        original_query: Original search query
        categories: Category filter
        max_follow: Maximum number of top results to extract references from

    Returns:
        List of (score, chunk) tuples from referenced documents
    """
    from hybrid_rag import get_hybrid_rag
    from rag_db import get_rag_db

    extended_results = []
    visited_refs = set()

    # Extract references from top results
    for i, (score, chunk) in enumerate(results[:max_follow]):
        refs = _extract_references(chunk.content)

        for ref in refs[:5]:  # Limit to 5 refs per chunk
            if ref in visited_refs:
                continue

            visited_refs.add(ref)

            try:
                # Search for the reference
                hybrid = get_hybrid_rag()
                ref_search_results = hybrid.search(
                    ref,
                    limit=2,
                    graph_hops=1  # Shallow search for references
                )

                # Convert to (score, chunk) format
                db = get_rag_db()
                for result in ref_search_results:
                    chunk = db.chunks.get(result.id)
                    if chunk and (categories == "all" or chunk.category in categories.split(",")):
                        # Penalize referenced results slightly (multiply score by 0.8)
                        extended_results.append((result.score * 0.8, chunk))

            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"[RAG] Failed to follow reference '{ref}': {e}")

    return extended_results


def rag_search(query, categories="all", limit=5, depth=2, follow_references=False):
    """
    Semantic search across indexed Verilog/Testbench/Spec documents.

    Args:
        query: Natural language search query (e.g., "AXI burst error handling")
        categories: Category filter - "verilog", "testbench", "spec", "verilog,testbench", or "all"
        limit: Maximum number of results (default: 5)
        depth: Graph traversal depth (1-5 hops, default: 2). Higher values find more related sections.
        follow_references: If True, automatically follow cross-references found in results (default: False)

    Returns:
        Formatted search results with code snippets and similarity scores

    Example:
        rag_search("FIFO overflow handling", categories="verilog,testbench", limit=3)
        rag_search("PCIe TLP Header", categories="spec", limit=5, depth=4, follow_references=True)
    """
    try:
        from config import ENABLE_SMART_RAG
        if not ENABLE_SMART_RAG:
            return "RAG is disabled. Use grep_file() or find_files() instead."
        from rag_db import get_rag_db
        from hybrid_rag import get_hybrid_rag

        # Phase 1: Acronym query expansion
        # For queries like "What does OHC stand for?", expand with definition keywords
        # to boost chunks with explicit definitions
        if _is_acronym_query(query):
            query = f"{query} stands for definition meaning"

        # Use HybridRAG for better results (Embedding + BM25 + Graph)
        hybrid = get_hybrid_rag()

        # Convert depth to graph_hops (1-5 range, clamped)
        graph_hops = max(1, min(5, int(depth)))

        # Perform hybrid search
        search_results = hybrid.search(
            query,
            limit=int(limit),
            graph_hops=graph_hops
        )

        # Convert HybridRAG results to (score, chunk) format
        results = []
        for result in search_results:
            # Try to get chunk from RAG DB
            db = get_rag_db()
            chunk = db.chunks.get(result.id)
            if chunk and (categories == "all" or chunk.category in categories.split(",")):
                results.append((result.score, chunk))

        if not results:
            # Check if DB is empty vs just no matches for this query
            if len(db.chunks) == 0:
                return f"No results found for '{query}' in categories: {categories}\n\nTip: Run rag_index() first to index files."
            else:
                return f"No results found for '{query}' in categories: {categories}\n\nNote: {len(db.chunks)} chunks indexed. Try different search terms or check category filter."

        # Phase B: Follow cross-references if requested
        if follow_references and results:
            try:
                extended_results = _follow_cross_references(results, query, categories, max_follow=3)
                results.extend(extended_results)
                # Remove duplicates by chunk ID
                seen_ids = set()
                unique_results = []
                for score, chunk in results:
                    if chunk.id not in seen_ids:
                        seen_ids.add(chunk.id)
                        unique_results.append((score, chunk))
                results = unique_results
            except Exception as e:
                if config.DEBUG_MODE:
                    print(f"[RAG] Follow references failed: {e}")

        output = f"Found {len(results)} result(s) for '{query}'"
        if follow_references and len(results) > int(limit):
            output += f" (including {len(results) - int(limit)} from references)"
        output += ":\n\n"

        # Track if any results have low scores
        low_score_count = 0
        for i, (score, chunk) in enumerate(results, 1):
            output += f"[{i}] {chunk.category.upper()} | {os.path.basename(chunk.source_file)}"
            output += f" (L{chunk.start_line}-{chunk.end_line}) | Score: {score:.3f}\n"

            # Add summary/metadata
            if chunk.metadata.get("summary"):
                output += f"    📝 {chunk.metadata['summary']}\n"
            if chunk.metadata.get("module_name"):
                output += f"    📦 Module: {chunk.metadata['module_name']}\n"

            # Show content preview (first 200 chars)
            preview = chunk.content[:200].replace('\n', ' ').strip()
            if len(chunk.content) > 200:
                preview += "..."
            output += f"    ```\n    {preview}\n    ```\n\n"

            # Track low scores (weak matches)
            if score < 0.3:
                low_score_count += 1

        # Add warning if scores are generally low
        if low_score_count == len(results):
            output += "⚠️  All results have low similarity scores. Consider:\n"
            output += "  - Refining your search query\n"
            output += "  - Checking if files are indexed (use rag_status())\n"
            output += "  - Using more specific terms\n\n"

        return output
    except Exception as e:
        return f"Error in rag_search: {e}"


def rag_explore(start_node, max_depth=3, max_results=20, explore_type="related"):
    """
    Explore related documents starting from a specific node.

    Args:
        start_node: Starting node ID (e.g., "spec_section_2_1_1", "file:module.v")
        max_depth: Maximum traversal depth (default: 3, range: 1-5)
        max_results: Maximum number of results (default: 20)
        explore_type: Exploration type - "related" (all), "hierarchy" (parent/child), "references" (cross-refs)

    Returns:
        Formatted exploration results with distance and path information

    Example:
        rag_explore(start_node="spec_section_2_1_1", max_depth=3, explore_type="related")
        rag_explore(start_node="file:pcie_msg_receiver.v", max_depth=2, explore_type="hierarchy")
    """
    try:
        from config import ENABLE_SMART_RAG
        if not ENABLE_SMART_RAG:
            return "RAG is disabled. Use grep_file() or find_files() instead."
        from spec_graph import get_spec_graph
        from rag_db import get_rag_db

        spec_graph = get_spec_graph()
        db = get_rag_db()

        # Clamp max_depth to valid range
        max_depth = max(1, min(5, int(max_depth)))
        max_results = int(max_results)

        # Determine edge types based on explore_type
        edge_types = None
        if explore_type == "hierarchy":
            edge_types = ["parent", "child"]
        elif explore_type == "references":
            edge_types = ["cross_ref", "related"]
        # "related" uses all edge types (None)

        # Traverse graph
        related_nodes = spec_graph.traverse_related(
            start_node,
            hops=max_depth,
            edge_types=edge_types
        )

        if not related_nodes:
            return f"No related nodes found for '{start_node}'.\n\nTips:\n  - Check node ID format (e.g., 'spec_section_X_Y' for sections)\n  - Use rag_search() first to find relevant starting points"

        # Limit results
        related_nodes = related_nodes[:max_results]

        # Format output
        output = f"Explored from '{start_node}' (depth={max_depth}, type={explore_type}):\n"
        output += f"Found {len(related_nodes)} related node(s):\n\n"

        for i, (node_id, distance, path) in enumerate(related_nodes, 1):
            node = spec_graph.nodes.get(node_id)
            if not node:
                continue

            # Format path (e.g., "A → B → C")
            path_str = " → ".join([p.split("_")[-1] if "_" in p else p for p in path[:3]])
            if len(path) > 3:
                path_str += f" ... ({len(path)} steps)"

            output += f"[{i}] Distance: {distance} | Path: {path_str}\n"
            output += f"    📍 Node: {node_id}\n"
            output += f"    📦 Type: {node.node_type}\n"

            # Show content preview
            if node.content_preview:
                preview = node.content_preview[:150].replace('\n', ' ').strip()
                if len(node.content_preview) > 150:
                    preview += "..."
                output += f"    ```\n    {preview}\n    ```\n\n"

        output += f"\n💡 Tip: Use rag_search() with found sections to get full content."

        return output
    except Exception as e:
        return f"Error in rag_explore: {e}"


def rag_index(path=".", category=None, pattern=None, fine_grained=False, rate_limit_delay_ms=None):
    """
    Index files for RAG search.

    Args:
        path: File or directory path to index (default: current directory)
        category: Force category - "verilog", "testbench", "spec" (auto-detect if None)
        pattern: File pattern for directories (e.g., "*.v", "*.sv")
        fine_grained: If True, create detailed chunks for individual signals/case statements
                     (more precise search but 10x more chunks). Default: False
        rate_limit_delay_ms: Delay between API calls in milliseconds. Default: uses config
                            Higher values help with rate limiting in corporate networks
                            Example: 100 (10 calls/sec), 500 (2 calls/sec), 1000 (1 call/sec)

    Returns:
        Indexing summary with chunk counts and stats

    Example:
        rag_index("src/", category="verilog")
        rag_index(".", fine_grained=True)  # Detailed chunking
        rag_index(".", rate_limit_delay_ms=500)  # For rate-limited environments
    """
    try:
        from config import ENABLE_SMART_RAG
        if not ENABLE_SMART_RAG:
            return "RAG is disabled. Set ENABLE_SMART_RAG=true to enable."
        import rag_db as rag_module
        import config

        # Create DB with fine_grained option
        db = rag_module.RAGDatabase(fine_grained=fine_grained)

        # Adjust rate limiting for network conditions (use provided value or config)
        if rate_limit_delay_ms is not None:
            db.rate_limit_delay = float(rate_limit_delay_ms) / 1000.0  # ms to seconds
        # else: use the value already loaded from config in RAGDatabase.__init__

        # Update global instance so rag_search/rag_status see new index
        rag_module._rag_db = db

        if os.path.isfile(path):
            # Index single file
            chunks = db.index_file(path, category=category)
            db.save()
            mode = "(fine-grained)" if fine_grained else ""
            return f"Indexed {path}: {chunks} chunks created {mode}"

        elif os.path.isdir(path):
            # Index directory - patterns from .ragconfig if not specified
            patterns = [pattern] if pattern else None
            total = db.index_directory(path, patterns=patterns, category=category)
            mode = "(fine-grained)" if fine_grained else ""

            output = f"Indexed {path}: {total} total chunks created {mode}\n"
            output += f"  API calls: {db.api_call_count}\n"
            output += f"  Rate limit: {db.rate_limit_delay * 1000:.0f}ms between calls\n"
            return output

        else:
            return f"Error: Path '{path}' not found"
    except Exception as e:
        return f"Error in rag_index: {e}"

def rag_status():
    """
    Show RAG database status and statistics.
    
    Returns:
        Summary of indexed files, chunks, and categories
    """
    try:
        from config import ENABLE_SMART_RAG
        if not ENABLE_SMART_RAG:
            return "RAG is disabled."
        from rag_db import get_rag_db

        db = get_rag_db()
        stats = db.get_stats()
        
        output = "=== RAG Database Status ===\n\n"
        output += f"📁 Indexed files: {stats['indexed_files']}\n"
        output += f"📦 Total chunks: {stats['total_chunks']}\n\n"
        
        if stats['by_category']:
            output += "By category:\n"
            for cat, count in stats['by_category'].items():
                output += f"  • {cat}: {count} chunks\n"
        
        if stats['by_level']:
            output += "\nBy level (Verilog hierarchy):\n"
            level_names = {
                "level_1": "Module (full)",
                "level_2": "Ports",
                "level_3": "Wire/Reg",
                "level_4": "Always blocks",
                "level_5": "Assigns"
            }
            for lvl, count in sorted(stats['by_level'].items()):
                name = level_names.get(lvl, lvl)
                output += f"  • {name}: {count}\n"
        
        # Show category info for agent
        output += "\n" + db.get_categories_info()
        
        return output
    except Exception as e:
        return f"Error in rag_status: {e}"

def rag_clear():
    """
    Clear all indexed RAG data.
    
    Returns:
        Confirmation message
    """
    try:
        from config import ENABLE_SMART_RAG
        if not ENABLE_SMART_RAG:
            return "RAG is disabled."
        from rag_db import get_rag_db

        db = get_rag_db()
        db.clear()
        return "RAG database cleared. Run rag_index() to re-index files."
    except Exception as e:
        return f"Error in rag_clear: {e}"

# ============================================================
# On-Demand Sub-Agent Tools (Claude Code Style)
# ============================================================

class AgentResult(dict):
    """
    Special dict that auto-formats to readable string for LLM.

    Allows both structured access (result['files_examined']) and
    readable string display (str(result)) for LLM consumption.
    """
    def __str__(self):
        """Format as readable string for LLM"""
        if 'error' in self:
            return self['error']

        lines = []
        if 'header' in self:
            lines.append(self['header'])
            lines.append("")

        if 'output' in self:
            lines.append(self['output'])

        if 'metadata' in self:
            lines.append("")
            lines.append("[Metadata]")
            for key, value in self['metadata'].items():
                if isinstance(value, list) and value:
                    lines.append(f"  {key}: {len(value)} items")
                elif isinstance(value, (int, float)):
                    lines.append(f"  {key}: {value}")

        if 'footer' in self:
            lines.append("")
            lines.append(self['footer'])

        return "\n".join(lines)

    def __repr__(self):
        return f"AgentResult({dict.__repr__(self)})"



def _sync_subagent_todo(output: str):
    """
    Sub-agent 결과에서 완료된 step을 파싱하여 primary TodoTracker에 반영.
    <result> 태그 안의 "✅" 마킹된 항목을 찾아서 매칭되는 todo를 completed로 변경.
    """
    try:
        import sys, re
        main_mod = sys.modules.get('main')
        if not main_mod:
            return
        tracker = getattr(main_mod, 'todo_tracker', None)
        if not tracker or not tracker.todos:
            return

        # Find "✅" lines in result
        completed_lines = re.findall(r'✅\s*(.+)', output)
        if not completed_lines:
            return

        for todo_item in tracker.todos:
            if todo_item.status == "completed":
                continue
            for line in completed_lines:
                # Fuzzy match: check if todo content appears in the completed line
                if todo_item.content.lower()[:30] in line.lower() or line.lower()[:30] in todo_item.content.lower():
                    idx = tracker.todos.index(todo_item)
                    tracker.mark_completed(idx)
                    break
    except Exception:
        pass  # Best-effort sync


def _get_todo_tracker():
    """Helper to lazily load and return the global TodoTracker instance."""
    try:
        import sys
        main_module = sys.modules.get('main')
        if main_module is None:
            import main as main_module

        if not hasattr(main_module, 'todo_tracker') or main_module.todo_tracker is None:
            from lib.todo_tracker import TodoTracker
            from pathlib import Path
            import config as _cfg
            main_module.todo_tracker = TodoTracker.load(Path(_cfg.TODO_FILE))

        return main_module.todo_tracker
    except Exception:
        # Silently fail if tracker cannot be accessed
        return None


def _save_todo_write_error(error_msg: str, attempted_todos=None):
    """Save todo_write failure info so /todo can surface it."""
    import json
    import time
    try:
        import config
        from pathlib import Path
        error_file = Path(config.TODO_ERROR_FILE)
        payload = {
            "error": error_msg,
            "timestamp": time.time(),
            "attempted_count": len(attempted_todos) if attempted_todos else 0,
        }
        error_file.write_text(json.dumps(payload, ensure_ascii=False, indent=2), encoding="utf-8")
    except Exception:
        pass  # Best-effort; never block the main error return


def todo_write(todos=None, tasks=None):
    """
    Create or update task list to track multi-step task progress.

    Args:
        todos (list): List of task dicts or strings.
        tasks (list): Alias for todos (some agents use this name).

    Example:
        todo_write([
            {"content": "Analyze code", "activeForm": "Analyzing code", "status": "in_progress"},
            {"content": "Write tests", "activeForm": "Writing tests", "status": "pending"}
        ])
    """
    # Accept either parameter name
    todos = todos or tasks
    # Import here to avoid circular dependency
    from typing import List, Dict

    todo_tracker = _get_todo_tracker()
    if todo_tracker is None:
        return ""

    # Validate input
    if not todos:
        return "Error: 'todos' parameter is required and must be a non-empty list"

    if not isinstance(todos, list):
        return f"Error: 'todos' must be a list, got {type(todos).__name__}"

    # Auto-convert string items to dict format
    from lib.todo_tracker import _generate_active_form
    for i, todo in enumerate(todos):
        if isinstance(todo, str):
            todos[i] = {
                "content": todo,
                "activeForm": _generate_active_form(todo),
                "status": "pending",
            }

    # Validate each todo structure
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict):
            return f"Error: todos[{i}] must be a dictionary, got {type(todo).__name__}"

        if "content" not in todo:
            return f"Error: todos[{i}] missing required key 'content'"

        # Auto-generate activeForm if missing
        if "activeForm" not in todo:
            todo["activeForm"] = _generate_active_form(todo["content"])

        # Default status to pending if not provided
        if "status" not in todo:
            todo["status"] = "pending"

        # Normalize status aliases (e.g. "todo" → "pending", "done" → "completed")
        from lib.todo_tracker import STATUS_ALIASES
        valid_statuses = ["pending", "in_progress", "completed", "approved", "rejected"]
        raw_status = todo["status"]
        if raw_status not in valid_statuses:
            normalized = STATUS_ALIASES.get(raw_status)
            if normalized:
                todo["status"] = normalized
            else:
                err = f"Error: todos[{i}] has invalid status '{raw_status}'. Must be one of: {', '.join(valid_statuses)}"
                _save_todo_write_error(err, todos)
                return err

    # Validate exactly ONE in_progress task
    in_progress_count = sum(1 for t in todos if t.get("status") == "in_progress")

    if in_progress_count > 1:
        err = (
            "Error: Only ONE task can be 'in_progress' at a time.\n\n"
            "Please mark completed tasks as 'completed' and future tasks as 'pending'.\n"
            f"Currently {in_progress_count} tasks are marked as 'in_progress'."
        )
        _save_todo_write_error(err, todos)
        return err

    # Update tracker with new todos
    try:
        todo_tracker.add_todos(todos)
    except Exception as e:
        return f"Error updating todo tracker: {e}"

    # Clear any previous write error on success
    try:
        import config as _cfg
        from pathlib import Path as _Path
        _error_file = _Path(getattr(_cfg, "TODO_ERROR_FILE", "current_todos_error.json"))
        if _error_file.exists():
            _error_file.unlink()
    except Exception:
        pass

    # Return formatted progress
    try:
        progress = todo_tracker.format_progress()
        return f"✅ Todo list created successfully:\n\n{progress}"
    except Exception as e:
        return f"Error formatting progress: {e}"


def todo_update(index=None, id=None, status=None, reason="", content="", detail="", activeForm="", criteria=""):
    """
    Update a specific todo item's status and/or content.

    Args:
        index (int): 1-based index of the todo to update (required).
        status (str): New status — "in_progress", "completed", "approved", "rejected", or "pending" (optional).
        reason (str): Rejection reason when reverting to pending/in_progress.
        content (str): New task description (optional, updates if provided).
        detail (str): New implementation detail (optional, updates if provided).
        activeForm (str): New display text while in progress (optional).
        criteria (str): New completion criteria (optional).

    Example:
        todo_update(index=1, status="completed")
        todo_update(index=2, content="Updated task description")
        todo_update(index=3, status="pending", reason="Tests still failing")
    """
    todo_tracker = _get_todo_tracker()

    if todo_tracker is None or not todo_tracker.todos:
        return ""

    if index is None:
        index = id

    if index is None:
        return "Error: 'index' (1-based) is required. (Note: use 1-based indexing, not 0-based)."

    if str(index).strip() == "0":
        return "Error: Todo indices are 1-based (1, 2, 3...). Please use index 1 for the first task."

    # Convert to 0-based
    try:
        idx = int(index) - 1
    except ValueError:
        return f"Error: index must be an integer, got '{index}'"

    if not (0 <= idx < len(todo_tracker.todos)):
        return f"Error: index {index} out of range (1-{len(todo_tracker.todos)})"

    item = todo_tracker.todos[idx]

    # Update content fields if provided
    if content:
        item.content = content
        if not activeForm:
            from lib.todo_tracker import _generate_active_form
            item.active_form = _generate_active_form(content)
    if activeForm:
        item.active_form = activeForm
    if detail:
        item.detail = detail
    if criteria:
        item.criteria = criteria

    # Update status if provided
    if status:
        # Normalize common aliases
        from lib.todo_tracker import STATUS_ALIASES
        valid = ["pending", "in_progress", "completed", "approved", "rejected"]
        if status not in valid:
            status = STATUS_ALIASES.get(status, status)
        if status not in valid:
            return f"Error: status must be one of {valid} (got '{status}')"

        # Enforce sequential execution: all prior tasks must be approved
        if status in ("in_progress", "completed", "approved"):
            blocking = [
                i + 1 for i in range(idx)
                if todo_tracker.todos[i].status not in ("approved",)
            ]
            if blocking:
                blocking_str = ", ".join(str(b) for b in blocking)
                return (
                    f"Error: Cannot update Task {index} — "
                    f"Task(s) {blocking_str} must be approved first.\n"
                    f"Tasks must be completed in order. Finish Task {blocking[0]} before moving to Task {index}."
                )

        # Protection: Do not allow downgrading "approved" tasks
        if item.status == "approved" and status in ("completed", "in_progress"):
            return (
                f"Status Conflict: Task {index} is already 'approved' (fully complete).\n"
                "If you intended to update a DIFFERENT task, please check the 1-based index in the todo list.\n"
                "If you truly need to re-work this task, use status='rejected' with a specific reason."
            )

        # Enforce state machine: must go through 'completed' before 'approved'
        if status == "approved" and item.status not in ("completed", "approved"):
            return (
                f"Error: Task {index} is currently '{item.status}'. "
                f"You must call todo_update(index={index}, status='completed') first, "
                f"then review, then call todo_update(index={index}, status='approved')."
            )

        if status == "approved":
            if not reason:
                return (
                    f"Error: You MUST provide a 'reason' when approving a task.\n"
                    f"Describe what you actually verified (e.g. 'read output file — correct, ran tests — all passed').\n"
                    f"→ todo_update(index={index}, status='approved', reason='<what you checked>')"
                )
            item.rejection_reason = ""
            todo_tracker.mark_approved(idx)
            _git_tag_todo(index, "approved", item.content)
            todo_tracker.save()
            next_todo = todo_tracker.get_current_todo()
            if next_todo:
                next_idx = todo_tracker.current_index + 1
                return (
                    f"✅ Task {index} approved. [{reason}]\n"
                    f"→ Next: todo_update(index={next_idx}, status='in_progress') — {next_todo.content}"
                )
            return f"✅ Task {index} approved. [{reason}] All tasks complete! 🏁"
        elif status == "completed":
            item.rejection_reason = ""
            todo_tracker.mark_completed(idx)
            todo_tracker.save()
            review_steps = (
                f"Task {index} marked completed. Now perform a CRITICAL, ADVERSARIAL review.\n"
                f"You are a skeptical reviewer — your job is to find problems, not to approve.\n\n"
                f"MANDATORY checks before approving:\n"
                f"  1. Actually READ the changed files / run the command / check the output\n"
                f"  2. Does the result EXACTLY match the goal: \"{item.content}\"?\n"
                f"  3. Are there regressions, side effects, or edge cases broken?\n"
                f"  4. Is there anything incomplete, missing, or just partially done?\n"
                f"  5. Would a strict senior engineer be satisfied — or would they send it back?\n\n"
                f"DEFAULT to REJECT if there is ANY doubt. Approval requires concrete evidence.\n"
                f"→ All checks pass → todo_update(index={index}, status='approved', reason='<specific evidence: what you read/ran and what you confirmed>')\n"
                f"→ Any issue found → todo_update(index={index}, status='rejected', reason='<exact problem and what needs to be fixed>')"
            )
            return review_steps
        elif status == "rejected":
            if not reason:
                return "Error: You MUST provide a 'reason' when marking a task as 'rejected'. What needs to be fixed?"
            todo_tracker.mark_rejected(idx, reason)
            todo_tracker.save()
            return (
                f"❌ Task {index} rejected: {reason}\n"
                f"→ Fix, then: todo_update(index={index}, status='in_progress')"
            )
        elif status == "in_progress":
            if reason:
                item.rejection_reason = reason
            todo_tracker.mark_in_progress(idx)
            todo_tracker.save()
            return f"▶ Task {index} in progress: {item.content}"
        else:  # pending
            if reason:
                item.rejection_reason = reason
            item.status = "pending"
            todo_tracker.save()
            return f"⏸ Task {index} set to pending: {item.content}"

    todo_tracker.save()
    return f"✅ Task {index} updated."


def todo_add(content="", activeForm="", priority="medium", detail="", criteria="", index=None):
    """
    Add a single task to the existing todo list.
    More efficient than todo_write for adding tasks mid-execution.

    Args:
        content (str): Task description (required).
        activeForm (str): Display text while in progress (auto-generated if omitted).
        priority (str): "high", "medium", or "low" (default: "medium").
        detail (str): Implementation details (optional).
        criteria (str): Completion criteria, newline-separated (optional).
        index (int): 1-based position to insert at. If omitted, appends to end.

    Example:
        todo_add(content="Fix lint errors", priority="low")
        todo_add(content="Add error handler", index=3)
    """
    todo_tracker = _get_todo_tracker()

    if todo_tracker is None:
        return ""

    if not content:
        return "Error: 'content' is required."

    from lib.todo_tracker import TodoItem, _generate_active_form
    active = activeForm or _generate_active_form(content)

    new_item = TodoItem(
        content=content,
        active_form=active,
        status="pending",
        priority=priority,
        detail=detail,
        criteria=criteria,
    )

    if str(index) == "0":
        return "Error: Todo indices are 1-based. To insert at the beginning, use index 1."

    if index is not None:
        idx = int(index) - 1
        idx = max(0, min(idx, len(todo_tracker.todos)))
        todo_tracker.todos.insert(idx, new_item)
    else:
        todo_tracker.todos.append(new_item)

    todo_tracker.save()
    return todo_tracker.format_progress()


def todo_remove(index=None, id=None):
    """
    Remove a task from the todo list by index.

    Args:
        index (int): 1-based index of the task to remove (required).

    Example:
        todo_remove(index=3)
    """
    todo_tracker = _get_todo_tracker()

    if todo_tracker is None or not todo_tracker.todos:
        return ""

    if index is None:
        index = id

    if index is None:
        return "Error: 'index' (1-based) is required. (Note: use 1-based indexing, not 0-based)."

    if str(index).strip() == "0":
        return "Error: Todo indices are 1-based. Use index 1 for the first task."

    idx = int(index) - 1
    if not (0 <= idx < len(todo_tracker.todos)):
        return f"Error: index {index} out of range (1-{len(todo_tracker.todos)})"

    removed = todo_tracker.todos.pop(idx)

    # Fix current_index if needed
    if todo_tracker.current_index == idx:
        todo_tracker.current_index = -1
    elif todo_tracker.current_index > idx:
        todo_tracker.current_index -= 1

    todo_tracker.save()
    return f"Removed: \"{removed.content}\"\n\n{todo_tracker.format_progress()}"


def todo_status():
    """
    Returns current todo list progress.
    Use this to check what tasks are pending, in progress, or completed.
    """
    todo_tracker = _get_todo_tracker()

    if todo_tracker is None or not todo_tracker.todos:
        return ""
    return todo_tracker.format_progress()


# ============================================================
# Background Agent Tools (v2 Architecture)
# ============================================================

def background_task(agent="explore", prompt="", context="", foreground="true"):
    """
    Launch an agent to handle a sub-task.

    Runs in foreground (synchronous) by default. Set foreground="false" for background execution.

    Args:
        agent: Agent type - "explore" (read-only, fast), "execute" (full access), "review" (read-only)
        prompt: Clear description of what the agent should do
        context: Optional context from current conversation to pass to the agent
        foreground: "true" (default) for synchronous execution, "false" for background

    Returns:
        Foreground: Direct result from the agent.
        Background: task_id string. Use background_output(task_id=...) to get results.

    Example:
        Action: background_task(agent="explore", prompt="Find all Verilog modules in rtl/")
        Action: background_task(agent="execute", prompt="Fix the bug in src/main.py", foreground="false")
    """
    try:
        valid_agents = {"explore", "execute", "review", "task"}

        # Auto-fix: if agent looks like a prompt (not a valid agent name), shift args
        if agent not in valid_agents and not prompt:
            # LLM passed prompt as first arg: background_task("do something...")
            prompt = agent
            agent = "explore"  # default agent
        elif agent not in valid_agents and prompt:
            # Maybe agent contains extra text, try context shift
            context = f"{agent}\n{context}" if context else agent
            agent = "explore"

        if not prompt:
            return "Error: 'prompt' is required. Usage: background_task(agent=\"explore\", prompt=\"your task description here\")"

        if agent not in valid_agents:
            return f"Error: Invalid agent type '{agent}'. Must be one of: {', '.join(valid_agents)}"

        is_foreground = str(foreground).lower() in ("true", "1", "yes")

        if is_foreground:
            # Foreground: synchronous execution
            import sys
            import config as _cfg
            from core.agent_runner import run_agent_session

            result = run_agent_session(
                agent_name=agent,
                prompt=prompt,
                parent_context=context,
                verbose=_cfg.DEBUG_MODE,
            )

            # Sync sub-agent completion to primary todo tracker
            _sync_subagent_todo(result.output)

            # Show sub-agent → primary handoff to user
            from lib.display import Color
            output_chars = len(result.output)
            output_tokens = output_chars // 4  # rough estimate
            print(f"\n  {Color.CYAN}◀ {agent} → primary{Color.RESET} ({result.status}, {result.execution_time_ms}ms, ~{output_tokens:,} tok)")
            if result.status == "error" and result.error:
                print(f"  {Color.RED}  error: {result.error}{Color.RESET}")
            if result.files_modified:
                print(f"  {Color.DIM}  modified: {result.files_modified}{Color.RESET}")

            return (
                f"=== Foreground Agent Result: {agent} ===\n"
                f"Status: {result.status} | {result.execution_time_ms}ms | {result.iterations} iterations\n"
                f"Files examined: {result.files_examined}\n"
                f"Files modified: {result.files_modified}\n\n"
                f"{result.output}"
            )
        else:
            # Background: async execution
            from core.background import get_background_manager
            manager = get_background_manager()

            task_id = manager.launch(
                agent=agent,
                prompt=prompt,
                parent_context=context,
            )

            return (
                f"Background task launched: {task_id}\n"
                f"Agent: {agent}\n"
                f"Prompt: {prompt[:100]}...\n\n"
                f"Use background_output(task_id=\"{task_id}\") to get results when ready."
            )
    except Exception as e:
        import traceback
        return f"Error in background_task: {e}\n{traceback.format_exc()}"


def background_output(task_id):
    """
    Get the output of a background agent task.

    If the task is still running, returns status info.
    If completed, returns the compressed result.

    Args:
        task_id: The task ID returned by background_task (e.g., "bg_a1b2c3d4")

    Returns:
        Task result or status message.
    """
    try:
        from core.background import get_background_manager
        manager = get_background_manager()
        return manager.get_output(task_id)
    except Exception as e:
        return f"Error getting background output: {e}"


def background_cancel(task_id):
    """
    Cancel a running background agent task.

    Args:
        task_id: The task ID to cancel

    Returns:
        Cancellation status message.
    """
    try:
        from core.background import get_background_manager
        manager = get_background_manager()
        return manager.cancel(task_id)
    except Exception as e:
        return f"Error cancelling background task: {e}"


def background_list():
    """
    List all background agent tasks and their statuses.

    Returns:
        Formatted list of all tasks with status, elapsed time, and prompts.
    """
    try:
        from core.background import get_background_manager
        manager = get_background_manager()
        return manager.list_tasks()
    except Exception as e:
        return f"Error listing background tasks: {e}"


# Registry of available tools
AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_dir": list_dir,
    "grep_file": grep_file,
    "read_lines": read_lines,
    "find_files": find_files,
    "git_diff": git_diff,
    "git_status": git_status,
    "git_revert": git_revert,
    "replace_in_file": replace_in_file,
    "replace_lines": replace_lines,
    # Task Management
    "todo_write": todo_write,
    "todo_update": todo_update,
    "todo_add": todo_add,
    "todo_remove": todo_remove,
    "todo_status": todo_status,
    # RAG Tools (disabled — uncomment to enable)
    # "rag_search": rag_search,
    # "rag_index": rag_index,
    # "rag_explore": rag_explore,
    # "rag_status": rag_status,
    # "rag_clear": rag_clear,
    # Background Agent Tools (v2)
    "background_task": background_task,
    "background_output": background_output,
    "background_cancel": background_cancel,
    "background_list": background_list,
}

# Import and register Verilog analysis tools
try:
    import tools_verilog
    AVAILABLE_TOOLS.update({
        "analyze_verilog_module": tools_verilog.analyze_verilog_module,
        "find_signal_usage": tools_verilog.find_signal_usage,
        "find_module_definition": tools_verilog.find_module_definition,
        "extract_module_hierarchy": tools_verilog.extract_module_hierarchy,
        "generate_module_testbench": tools_verilog.generate_module_testbench,
        "find_potential_issues": tools_verilog.find_potential_issues,
        "analyze_timing_paths": tools_verilog.analyze_timing_paths,
        "generate_module_docs": tools_verilog.generate_module_docs,
        "suggest_optimizations": tools_verilog.suggest_optimizations,
    })
except ImportError:
    pass  # tools_verilog not available

# Import and register generic spec navigation tool (pcie/ucie/nvme 등 모든 스펙)
try:
    from tools_spec import spec_navigate
    AVAILABLE_TOOLS["spec_navigate"] = spec_navigate
except ImportError:
    pass  # spec_navigate_tool not available
