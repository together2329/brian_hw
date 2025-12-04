import os
import subprocess
import json
import shlex

def read_file(path):
    """Reads the content of a file."""
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        with open(path, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"

def write_file(path, content):
    """Writes content to a file. Overwrites if exists."""
    try:
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        with open(path, 'w', encoding='utf-8') as f:
            f.write(content)
        return f"Successfully wrote to '{path}'."
    except Exception as e:
        return f"Error writing file: {e}"

def run_command(command):
    """Runs a shell command and returns output."""
    try:
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

def find_files(pattern, directory=".", max_depth=None):
    """
    Finds files matching a pattern in a directory.
    Args:
        pattern: Filename pattern (supports wildcards: *.py, test_*.v, etc.)
        directory: Directory to search in (default: current directory)
        max_depth: Maximum depth to search (None for unlimited)
    Returns:
        List of matching file paths
    """
    import fnmatch
    try:
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

def replace_in_file(path, old_text, new_text, count=-1):
    """
    Replaces occurrences of text in a file.
    Args:
        path: Path to the file
        old_text: Text to find and replace
        new_text: Text to replace with
        count: Maximum number of replacements (-1 for all occurrences)
    Returns:
        Success message with number of replacements made
    """
    try:
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        
        with open(path, 'r', encoding='utf-8') as f:
            content = f.read()
        
        # Count occurrences before replacement
        occurrences = content.count(old_text)
        
        if occurrences == 0:
            return f"No occurrences of '{old_text[:50]}...' found in {path}"
        
        # Perform replacement
        if count == -1:
            new_content = content.replace(old_text, new_text)
            replacements = occurrences
        else:
            new_content = content.replace(old_text, new_text, count)
            replacements = min(count, occurrences)
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.write(new_content)
        
        return f"Replaced {replacements} occurrence(s) in {path}"
    except Exception as e:
        return f"Error replacing text: {e}"

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
        
        # Write back
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)
        
        lines_removed = end_line - start_line + 1
        return f"Replaced lines {start_line}-{end_line} ({lines_removed} lines) in {path}"
    except Exception as e:
        return f"Error replacing lines: {e}"

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
    "replace_lines": replace_lines
}
