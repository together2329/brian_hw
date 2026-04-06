"""
core/tool_schema.py — OpenAI-compatible JSON schema definitions for all agent tools.

Used when ENABLE_NATIVE_TOOL_CALLS=true to pass tool schemas via API `tools` parameter
instead of embedding tool descriptions in the system prompt as text.

get_tool_schemas(allowed_tools) returns a filtered list ready for the API request.
"""
from typing import Dict, List, Any


def _fn(name: str, description: str, properties: Dict[str, Any], required: List[str] = None) -> Dict:
    return {
        "type": "function",
        "function": {
            "name": name,
            "description": description,
            "parameters": {
                "type": "object",
                "properties": properties,
                "required": required or [],
            },
        },
    }


TOOL_SCHEMAS: Dict[str, Dict] = {

    # ── File I/O ────────────────────────────────────────────────────────────
    "read_file": _fn(
        "read_file",
        "Read entire file content. For large files (>500 lines) prefer grep_file first.",
        {"path": {"type": "string", "description": "File path to read"}},
        required=["path"],
    ),
    "read_lines": _fn(
        "read_lines",
        "Read a specific line range from a file. Use after grep_file to target sections.",
        {
            "path": {"type": "string", "description": "File path"},
            "start_line": {"type": "integer", "description": "First line to read (1-based)"},
            "end_line": {"type": "integer", "description": "Last line to read (inclusive, 1-based)"},
        },
        required=["path", "start_line", "end_line"],
    ),
    "write_file": _fn(
        "write_file",
        "Create NEW files only. NEVER use on existing files — use replace_in_file instead.",
        {
            "path": {"type": "string", "description": "File path to create"},
            "content": {"type": "string", "description": "Full file content"},
        },
        required=["path", "content"],
    ),
    "replace_in_file": _fn(
        "replace_in_file",
        "Edit existing files by replacing exact text. ALWAYS read the file first to get exact text including indentation.",
        {
            "path": {"type": "string", "description": "File path to edit"},
            "old_text": {"type": "string", "description": "Exact text to find (include 5+ lines of context for uniqueness)"},
            "new_text": {"type": "string", "description": "Replacement text"},
        },
        required=["path", "old_text", "new_text"],
    ),
    "replace_lines": _fn(
        "replace_lines",
        "Replace a range of lines in an existing file.",
        {
            "path": {"type": "string", "description": "File path to edit"},
            "start_line": {"type": "integer", "description": "First line to replace (1-based)"},
            "end_line": {"type": "integer", "description": "Last line to replace (inclusive)"},
            "new_content": {"type": "string", "description": "New content for the replaced lines"},
        },
        required=["path", "start_line", "end_line", "new_content"],
    ),
    "run_command": _fn(
        "run_command",
        "Execute a shell command and return its output.",
        {"command": {"type": "string", "description": "Shell command to execute"}},
        required=["command"],
    ),
    "list_dir": _fn(
        "list_dir",
        "List directory contents.",
        {"path": {"type": "string", "description": "Directory path to list"}},
        required=["path"],
    ),

    # ── Search ───────────────────────────────────────────────────────────────
    "grep_file": _fn(
        "grep_file",
        "Regex search in file(s). Use before read_file on large files.",
        {
            "pattern": {"type": "string", "description": "Regex pattern to search for"},
            "path": {"type": "string", "description": "File or directory path to search"},
        },
        required=["pattern", "path"],
    ),
    "find_files": _fn(
        "find_files",
        "Glob search for files. Prefer over repeated list_dir calls.",
        {
            "pattern": {"type": "string", "description": "Glob pattern (e.g. '**/*.py')"},
            "path": {"type": "string", "description": "Root directory to search from"},
        },
        required=["pattern", "path"],
    ),

    # ── Git ──────────────────────────────────────────────────────────────────
    "git_status": _fn(
        "git_status",
        "Show working tree git status.",
        {},
    ),
    "git_diff": _fn(
        "git_diff",
        "Show unstaged git changes for a file or all files.",
        {"path": {"type": "string", "description": "File path (empty string for all files)"}},
        required=["path"],
    ),
    "git_revert": _fn(
        "git_revert",
        "Revert uncommitted changes to a file.",
        {"path": {"type": "string", "description": "File path to revert"}},
        required=["path"],
    ),

    # ── Task Management ───────────────────────────────────────────────────────
    "todo_write": _fn(
        "todo_write",
        "Create a task list (Plan Mode only). tasks is a JSON array of {content, activeForm, status} objects.",
        {"tasks": {"type": "string", "description": "JSON array of task objects"}},
        required=["tasks"],
    ),
    "todo_update": _fn(
        "todo_update",
        "Update task status. index is 1-based. IMPORTANT: status='approved' or 'rejected' REQUIRES a 'reason' argument describing what was verified.",
        {
            "index": {"type": "integer", "description": "Task index (1-based)"},
            "status": {"type": "string", "description": "New status: pending/active/completed/approved/rejected"},
            "reason": {"type": "string", "description": "REQUIRED when status is 'approved' or 'rejected'. Describe what you verified (e.g. 'read output — correct, tests passed')."},
            "content": {"type": "string", "description": "Optional: update task content"},
            "detail": {"type": "string", "description": "Optional: update task detail"},
        },
        required=["index", "status"],
    ),
    "todo_add": _fn(
        "todo_add",
        "Add a new task. index is the target position (1-based).",
        {
            "content": {"type": "string", "description": "Task description"},
            "priority": {"type": "string", "description": "Priority: high/normal/low"},
            "index": {"type": "integer", "description": "Position to insert (1-based, optional)"},
        },
        required=["content"],
    ),
    "todo_remove": _fn(
        "todo_remove",
        "Remove a task by index (1-based).",
        {"index": {"type": "integer", "description": "Task index to remove (1-based)"}},
        required=["index"],
    ),
    "todo_status": _fn(
        "todo_status",
        "Show current task progress summary.",
        {},
    ),

    # ── Sub-Agents ────────────────────────────────────────────────────────────
    "background_task": _fn(
        "background_task",
        "Delegate a task to a sub-agent (explore/execute/review).",
        {
            "agent": {"type": "string", "description": "Agent type: explore, execute, or review"},
            "prompt": {"type": "string", "description": "Task description for the sub-agent"},
        },
        required=["agent", "prompt"],
    ),
    "background_output": _fn(
        "background_output",
        "Get the result of a sub-agent task by task_id.",
        {"task_id": {"type": "string", "description": "Task ID returned by background_task"}},
        required=["task_id"],
    ),
    "background_cancel": _fn(
        "background_cancel",
        "Cancel a running sub-agent task.",
        {"task_id": {"type": "string", "description": "Task ID to cancel"}},
        required=["task_id"],
    ),
    "background_list": _fn(
        "background_list",
        "List all active sub-agent tasks.",
        {},
    ),

    # ── Spec Navigation ───────────────────────────────────────────────────────
    "spec_navigate": _fn(
        "spec_navigate",
        "Navigate PCIe/UCIe/NVMe spec by section ID. "
        "Start with node_id='root' for TOC, drill into sections. "
        "Leaf nodes contain full spec text. Use for ALL spec questions.",
        {
            "spec": {"type": "string", "description": "Spec name: pcie, ucie, nvme, etc."},
            "node_id": {"type": "string", "description": "Section node ID (default: 'root' for TOC)"},
        },
        required=["spec"],
    ),
}


def get_tool_schemas(allowed_tools: List[str]) -> List[Dict]:
    """Return OpenAI-compatible tool schema list filtered to allowed_tools.

    Tools not in TOOL_SCHEMAS are silently skipped (e.g. verilog, cmux, tmux tools
    that are conditionally loaded — they won't be callable in native mode unless
    schemas are added above).
    """
    return [TOOL_SCHEMAS[t] for t in allowed_tools if t in TOOL_SCHEMAS]
