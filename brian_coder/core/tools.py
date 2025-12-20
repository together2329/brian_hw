import os
import subprocess
import json
import shlex
import sys
import re

# Robust library path discovery
try:
    from lib.display import format_diff
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
        from lib.display import format_diff
    except ModuleNotFoundError:
        try:
            from display import format_diff
        except ModuleNotFoundError:
            # Final fallback stub
            def format_diff(*args, **kwargs):
                return ""

def read_file(path):
    """Reads the content of a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

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

        return result
    except Exception as e:
        return f"Error writing file: {e}"

def run_command(command):
    """Runs a shell command and returns output."""
    try:
        # Optional safe-mode guardrail to avoid destructive commands.
        safe_mode_env = os.getenv("SAFE_MODE", "false").lower() in ("true", "1", "yes")
        if safe_mode_env and _is_dangerous_command(command):
            return "Error: Command blocked by SAFE_MODE."

        # Security Note: In a real production agent, you'd want to sandbox this.
        # Since this is for internal use by a developer, we use subprocess directly.
        # Updated to use shell=False for better security
        args = shlex.split(command)
        result = subprocess.run(
            args, 
            shell=False, 
            capture_output=True, 
            text=True, 
            timeout=30
        )
        output = result.stdout
        if result.stderr:
            output += f"\nSTDERR:\n{result.stderr}"
        return output.strip()
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
        r"\brm\b.*\s-\w*r\w*f\b",          # rm -rf / rm -fr variants
        r"\bsudo\b",                      # privilege escalation
        r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b",
        r"\bmkfs\b|\bdd\b\s+if=",
        r"\bgit\b\s+reset\s+--hard\b",
        r"\bgit\b\s+clean\b.*-f",
    ]

    return any(re.search(pat, cmd) for pat in dangerous_patterns)

def list_dir(path="."):
    """Lists files in a directory."""
    try:
        return "\n".join(os.listdir(path))
    except Exception as e:
        return f"Error listing directory: {e}"

def create_plan(task_description, steps):
    """
    Creates a plan file with numbered steps for a complex task.
    Args:
        task_description: Description of the overall task
        steps: Newline-separated list of steps
    Returns:
        Success message with plan file path
    """
    try:
        plan_content = f"""# Task Plan
## Task: {task_description}

## Steps:
"""
        step_list = [s.strip() for s in steps.split('\n') if s.strip()]
        for i, step in enumerate(step_list, 1):
            plan_content += f"{i}. {step}\n"

        plan_file = "current_plan.md"
        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write(plan_content)

        return f"Plan created successfully in '{plan_file}' with {len(step_list)} steps."
    except Exception as e:
        return f"Error creating plan: {e}"

def get_plan():
    """
    Reads the current plan file.
    Returns:
        Plan content or error message
    """
    try:
        plan_file = "current_plan.md"
        if not os.path.exists(plan_file):
            return "No plan file found. Use create_plan() first."
        with open(plan_file, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading plan: {e}"

def mark_step_done(step_number):
    """
    Marks a step as completed in the plan.
    Args:
        step_number: The step number to mark as done (1-based)
    Returns:
        Success message
    """
    try:
        plan_file = "current_plan.md"
        if not os.path.exists(plan_file):
            return "No plan file found."

        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        lines = content.split('\n')
        for i, line in enumerate(lines):
            if line.strip().startswith(f"{step_number}."):
                if not line.strip().endswith("✅"):
                    lines[i] = line + " ✅"
                break

        with open(plan_file, 'w', encoding='utf-8') as f:
            f.write('\n'.join(lines))

        return f"Step {step_number} marked as done."
    except Exception as e:
        return f"Error marking step: {e}"

def wait_for_plan_approval():
    """
    Pauses execution and waits for user to review and approve the plan.
    User should edit current_plan.md and add 'APPROVED' at the top when ready.
    Returns:
        Approval status message
    """
    try:
        plan_file = "current_plan.md"
        if not os.path.exists(plan_file):
            return "No plan file found. Create a plan first."

        # Add instruction to the plan file
        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "USER INSTRUCTION" not in content:
            instruction = """# USER INSTRUCTION:
# Review this plan and make any changes you want.
# When ready to proceed, add 'APPROVED' on the line below:
# STATUS:

---

"""
            with open(plan_file, 'w', encoding='utf-8') as f:
                f.write(instruction + content)

        return f"""Plan saved to '{plan_file}'.

NEXT STEPS FOR USER:
1. Open and review: {plan_file}
2. Edit the plan as needed (add/remove/modify steps)
3. When satisfied, add 'APPROVED' after 'STATUS:' in the file
4. Then tell me to continue with: 'execute the plan' or 'check plan status'

I will wait for your approval before proceeding."""
    except Exception as e:
        return f"Error in wait_for_plan_approval: {e}"

def check_plan_status():
    """
    Checks if the plan has been approved by the user.
    Returns:
        Approval status and plan content
    """
    try:
        plan_file = "current_plan.md"
        if not os.path.exists(plan_file):
            return "No plan file found."

        with open(plan_file, 'r', encoding='utf-8') as f:
            content = f.read()

        if "STATUS: APPROVED" in content:
            return f"✅ Plan is APPROVED! Ready to execute.\n\n{content}"
        else:
            return f"⏳ Plan is NOT YET APPROVED. User needs to review.\n\n{content}"
    except Exception as e:
        return f"Error checking plan status: {e}"

def grep_file(pattern, path, context_lines=2):
    """
    Searches for a pattern in a file and returns matching lines with context.
    Args:
        pattern: Regular expression pattern to search for
        path: Path to the file
        context_lines: Number of lines to show before and after each match (default: 2)
    Returns:
        Formatted output with line numbers and context
    """
    import re
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        if os.path.isdir(path):
            return f"Error: '{path}' is a directory. Use find_files() or list_dir() for directories."

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        matches = []
        regex = re.compile(pattern)
        
        for i, line in enumerate(lines, 1):
            if regex.search(line):
                # Calculate context range
                start = max(1, i - context_lines)
                end = min(len(lines), i + context_lines)
                
                # Build context block
                context_block = []
                for j in range(start, end + 1):
                    prefix = ">>> " if j == i else "    "
                    context_block.append(f"{prefix}{j:4d}: {lines[j-1].rstrip()}")
                
                matches.append("\n".join(context_block))
        
        if not matches:
            return f"No matches found for pattern '{pattern}' in {path}"
        
        result = f"Found {len(matches)} match(es) in {path}:\n\n"
        result += "\n...\n".join(matches)
        return result
    except re.error as e:
        return f"Error: Invalid regex pattern '{pattern}': {e}"
    except Exception as e:
        return f"Error searching file: {e}"

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
        
        # Build output
        result = f"Lines {start_line}-{end_line} of {path} (total: {total_lines} lines):\n\n"
        for i in range(start_line - 1, end_line):
            result += f"{i+1:4d}: {lines[i].rstrip()}\n"
        
        return result
    except Exception as e:
        return f"Error reading lines: {e}"

def find_files(pattern, directory=".", max_depth=None, path=None):
    """
    Finds files matching a pattern in a directory.
    Args:
        pattern: Filename pattern (supports wildcards: *.py, test_*.v, etc.)
        directory: Directory to search in (default: current directory)
        max_depth: Maximum depth to search (None for unlimited)
        path: Alias for 'directory' (for LLM compatibility)
    Returns:
        List of matching file paths
    """
    import fnmatch
    try:
        # Support 'path' as alias for 'directory'
        if path is not None:
            directory = path
        
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
            return f"No files matching '{pattern}' found in {directory}"
        
        result = f"Found {len(matches)} file(s) matching '{pattern}':\n"
        result += "\n".join(f"  - {m}" for m in sorted(matches))
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
            # Provide helpful hint
            hint = "\nHint: Check exact whitespace/indentation. Use read_lines() first to see actual content."
            return f"No occurrences of '{old_text[:50]}...' found in {path}{range_msg}{hint}"
        
        # IMPROVEMENT: Uniqueness Safety Check
        # Strict logic: range required for multi-match unless count is specified.
        if start_line is None and end_line is None and occurrences > 1 and count == -1:
             return f"Error: Found {occurrences} occurrences of '{old_text[:30]}...' in {path}. " \
                   f"To prevent accidental edits, please specify start_line/end_line OR provide a more unique text context."
        
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
        
        # Generate visual diff before writing
        old_full_content = "".join(lines)
        diff_output = format_diff(old_full_content, new_full_content, context_lines=2)
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_full_content)
        
        result = f"Replaced {replacements} occurrence(s) in {path}\n\n"
        if actual_old_text != old_text:
            if matched_strategy:
                result += f"(Fuzzy matched using: {matched_strategy})\n"
            else:
                result += f"(Fuzzy matched: adjusted whitespace)\n"
        result += "=== Visual Diff ==="
        result += f"\n{diff_output}"
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
        
        # Generate visual diff before writing
        old_content = "".join(lines)
        new_content_full = "".join(new_lines)
        diff_output = format_diff(old_content, new_content_full, context_lines=2)
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        lines_removed = end_line - start_line + 1
        result = f"Replaced lines {start_line}-{end_line} ({lines_removed} lines) in {path}\n\n"
        result += "=== Visual Diff ==="
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
            return f"No results found for '{query}' in categories: {categories}\n\nTip: Run rag_index() first to index files."

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
        from rag_db import get_rag_db
        
        db = get_rag_db()
        db.clear()
        return "RAG database cleared. Run rag_index() to re-index files."
    except Exception as e:
        return f"Error in rag_clear: {e}"

# ============================================================
# On-Demand Sub-Agent Tools (Claude Code Style)
# ============================================================

def spawn_explore(query):
    """
    Spawn an explore agent to search the codebase.
    Use this when you need to find files, understand structure, or gather information.

    Args:
        query: What to explore/find (e.g., "find all FIFO implementations", "understand AXI protocol usage")

    Returns:
        Exploration results - files found, patterns identified, structure analysis
    """
    try:
        try:
            # Tests may add `agents/` to sys.path (so `sub_agents` is importable).
            from sub_agents.explore_agent import ExploreAgent
        except ImportError:
            # Runtime default: import via namespace package under `agents/`.
            from agents.sub_agents.explore_agent import ExploreAgent
        from llm_client import call_llm_raw

        # Create a simple execute_tool wrapper
        def execute_tool(tool_name, args):
            if tool_name in AVAILABLE_TOOLS:
                # Parse args if string
                if isinstance(args, str):
                    import re
                    kwargs = {}
                    for match in re.finditer(r'(\w+)\s*=\s*["\']([^"\']*)["\']', args):
                        kwargs[match.group(1)] = match.group(2)
                    for match in re.finditer(r'(\w+)\s*=\s*(\d+)', args):
                        kwargs[match.group(1)] = int(match.group(2))
                    return AVAILABLE_TOOLS[tool_name](**kwargs) if kwargs else AVAILABLE_TOOLS[tool_name](args)
                return AVAILABLE_TOOLS[tool_name](**args) if isinstance(args, dict) else AVAILABLE_TOOLS[tool_name](args)
            return f"Tool {tool_name} not found"

        agent = ExploreAgent(
            name="explore",
            llm_call_func=call_llm_raw,
            execute_tool_func=execute_tool
        )

        result = agent.run(query, {"task": query})

        if result.status.value == "completed":
            return f"=== EXPLORATION RESULTS ===\n{result.output}\n==========================="
        else:
            return f"Exploration failed: {result.errors}"

    except Exception as e:
        return f"Error spawning explore agent: {e}"

def spawn_plan(task_description):
    """
    Spawn a planning agent to create an implementation plan.
    Use this for complex tasks that need architectural planning before implementation.

    Args:
        task_description: What to plan (e.g., "design async FIFO with CDC", "implement AXI master")

    Returns:
        Text-only implementation plan with interface specs and steps
    """
    try:
        try:
            # Tests may add `agents/` to sys.path (so `sub_agents` is importable).
            from sub_agents.plan_agent import PlanAgent
        except ImportError:
            # Runtime default: import via namespace package under `agents/`.
            from agents.sub_agents.plan_agent import PlanAgent
        from llm_client import call_llm_raw

        agent = PlanAgent(
            name="plan",
            llm_call_func=call_llm_raw,
            execute_tool_func=lambda t, a: "Plan agent does not execute tools"
        )

        result = agent.run(task_description, {"task": task_description})

        if result.status.value == "completed":
            return f"=== IMPLEMENTATION PLAN ===\n{result.output}\n==========================="
        else:
            return f"Planning failed: {result.errors}"

    except Exception as e:
        return f"Error spawning plan agent: {e}"

# Registry of available tools
AVAILABLE_TOOLS = {
    "read_file": read_file,
    "write_file": write_file,
    "run_command": run_command,
    "list_dir": list_dir,
    "create_plan": create_plan,
    "get_plan": get_plan,
    "mark_step_done": mark_step_done,
    "wait_for_plan_approval": wait_for_plan_approval,
    "check_plan_status": check_plan_status,
    "grep_file": grep_file,
    "read_lines": read_lines,
    "find_files": find_files,
    "git_diff": git_diff,
    "git_status": git_status,
    "replace_in_file": replace_in_file,
    "replace_lines": replace_lines,
    # RAG Tools
    "rag_search": rag_search,
    "rag_index": rag_index,
    "rag_explore": rag_explore,  # Phase C: New exploration tool
    "rag_status": rag_status,
    "rag_clear": rag_clear,
    # On-Demand Sub-Agent Tools
    "spawn_explore": spawn_explore,
    "spawn_plan": spawn_plan,
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
