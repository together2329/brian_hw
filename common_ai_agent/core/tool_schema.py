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
        (
            "Read the entire content of a file and return it with line numbers.\n"
            "Best for files under ~500 lines. For larger files, use grep_file first to locate the relevant "
            "section, then use read_lines to read only that section.\n"
            "Decision guide:\n"
            "  • Unknown content / small file → read_file\n"
            "  • Large file, need specific section → grep_file → read_lines\n"
            "  • Looking for a function/class name → grep_file\n"
            "Example: read_file(path='src/main.py')"
        ),
        {"path": {"type": "string", "description": "Absolute or relative file path to read. Examples: 'src/main.py', './config.json', '/home/user/project/lib.py'"}},
        required=["path"],
    ),
    "read_lines": _fn(
        "read_lines",
        (
            "Read a specific contiguous line range from a file.\n"
            "ALWAYS supply both start_line and end_line — omitting them is an error.\n"
            "Typical workflow: grep_file to find the line number → read_lines to read the surrounding context.\n"
            "Do NOT use to read the whole file — use read_file instead.\n"
            "Example: read_lines(path='src/main.py', start_line=42, end_line=80)"
        ),
        {
            "path": {"type": "string", "description": "File path to read"},
            "start_line": {"type": "integer", "description": "First line to read (1-based, inclusive). REQUIRED."},
            "end_line": {"type": "integer", "description": "Last line to read (1-based, inclusive). REQUIRED. Must be >= start_line."},
        },
        required=["path", "start_line", "end_line"],
    ),
    "write_file": _fn(
        "write_file",
        (
            "Create a NEW file with the given content. Overwrites if the file already exists — "
            "so ONLY use this to create brand-new files.\n"
            "For editing existing files use replace_in_file (text-based) or replace_lines (line-range).\n"
            "Always provide the complete file content including all imports/headers.\n"
            "Example: write_file(path='tests/test_foo.py', content='import pytest\\n...')"
        ),
        {
            "path": {"type": "string", "description": "Destination file path (will be created or overwritten)"},
            "content": {"type": "string", "description": "Complete file content to write"},
        },
        required=["path", "content"],
    ),
    "replace_in_file": _fn(
        "replace_in_file",
        (
            "Edit an EXISTING file by replacing an exact block of text with new text.\n"
            "Workflow: read_file → copy exact text including indentation → call replace_in_file.\n"
            "old_text MUST match the file exactly (whitespace, quotes, line endings). Include 5+ surrounding "
            "lines of context to ensure uniqueness — if the pattern appears multiple times, the replacement "
            "will fail.\n"
            "Use replace_lines instead when you know the exact line numbers and the text block is large.\n"
            "Example:\n"
            "  replace_in_file(path='app.py',\n"
            "    old_text='def foo():\\n    return 1',\n"
            "    new_text='def foo():\\n    return 42')"
        ),
        {
            "path": {"type": "string", "description": "Path to the file to edit (must exist)"},
            "old_text": {"type": "string", "description": "Exact text to search for and replace. Must be unique in the file. Include surrounding context lines for uniqueness."},
            "new_text": {"type": "string", "description": "Replacement text (can be empty string to delete)"},
        },
        required=["path", "old_text", "new_text"],
    ),
    "replace_lines": _fn(
        "replace_lines",
        (
            "Replace a contiguous range of lines in an existing file using line numbers.\n"
            "Use this when you have exact line numbers (e.g. from grep_file or read_file output) and "
            "the replaced block is large or contains repeated patterns that make replace_in_file ambiguous.\n"
            "new_content replaces lines start_line through end_line inclusive. Line count of new_content "
            "can differ from the replaced range.\n"
            "Example: replace_lines(path='main.py', start_line=10, end_line=15, new_content='x = 1\\ny = 2')"
        ),
        {
            "path": {"type": "string", "description": "Path to the file to edit (must exist)"},
            "start_line": {"type": "integer", "description": "First line to replace (1-based, inclusive)"},
            "end_line": {"type": "integer", "description": "Last line to replace (1-based, inclusive). Must be >= start_line."},
            "new_content": {"type": "string", "description": "New content that replaces lines start_line..end_line. May have more or fewer lines than the replaced range."},
        },
        required=["path", "start_line", "end_line", "new_content"],
    ),

    # ── Image Analysis ────────────────────────────────────────────────────
    "read_image": _fn(
        "read_image",
        (
            "Analyze an image file using a vision-capable AI model.\n"
            "Supports PNG, JPEG, GIF, WebP, BMP formats.\n"
            "Use this when:\n"
            "  • User shares a screenshot and asks what it shows\n"
            "  • Need to extract text from an image (OCR)\n"
            "  • Analyze a chart, diagram, or UI mockup\n"
            "  • Read error messages or logs from a screenshot\n"
            "The image can be a local file path (supports fuzzy matching for Korean filenames, "
            "Desktop screenshots, partial names).\n"
            "Examples:\n"
            "  read_image(path='screenshot.png', prompt='What errors are shown?')\n"
            "  read_image(path='스크린샷 2026-04-26.png', prompt='Extract all text')\n"
            "  read_image(path='diagram.png')"
        ),
        {
            "path": {"type": "string", "description": "Path to image file. Supports fuzzy matching: partial name, Korean filenames, Desktop screenshots."},
            "prompt": {"type": "string", "description": "What to ask about the image. Default: detailed description. Examples: 'Extract text', 'What errors?', 'Describe layout'."},
        },
        required=["path"],
    ),

    "run_command": _fn(
        "run_command",
        (
            "Execute a shell command and return stdout + stderr.\n"
            "Use for: running tests, compiling code, git commands, installing packages, checking tool output.\n"
            "Avoid running long-running interactive commands (they will time out).\n"
            "For file reading/searching, prefer read_file/grep_file/find_files over shell commands — "
            "those tools parse output and handle errors better.\n"
            "Examples:\n"
            "  run_command(command='pytest tests/ -v')\n"
            "  run_command(command='git log --oneline -10')\n"
            "  run_command(command='pip install requests')"
        ),
        {"command": {"type": "string", "description": "Shell command string to execute. Runs in project root. Supports pipes, &&, etc."}},
        required=["command"],
    ),
    "list_dir": _fn(
        "list_dir",
        (
            "List the immediate contents of a directory (files and subdirectories).\n"
            "Use '.' for the current working directory.\n"
            "For recursive file search by pattern, use find_files instead — it's faster and supports glob.\n"
            "Examples:\n"
            "  list_dir(path='.')  — current directory\n"
            "  list_dir(path='src/components')"
        ),
        {"path": {"type": "string", "description": "Directory path to list. Use '.' for current directory."}},
        required=["path"],
    ),

    # ── Search ───────────────────────────────────────────────────────────────
    "grep_file": _fn(
        "grep_file",
        (
            "Search for a regex pattern in a file or directory and return matching lines with line numbers.\n"
            "Use BEFORE read_file on large files to find the relevant section.\n"
            "Set recursive=true to search all files in a directory tree.\n"
            "Use context_lines to include surrounding lines for each match.\n"
            "Examples:\n"
            "  grep_file(pattern='def train', path='src/')  — find function definitions\n"
            "  grep_file(pattern='TODO|FIXME', path='.', recursive=true)  — find all todos\n"
            "  grep_file(pattern='import torch', path='model.py', context_lines=3)"
        ),
        {
            "pattern": {"type": "string", "description": "Python regex pattern to search for. Case-sensitive by default. Use (?i) prefix for case-insensitive."},
            "path": {"type": "string", "description": "File path or directory path to search in"},
            "recursive": {"type": "boolean", "description": "If true, search all files recursively under the directory (default: false for single file, true for directory)"},
            "context_lines": {"type": "integer", "description": "Number of lines of context to include before and after each match (default: 0)"},
        },
        required=["pattern", "path"],
    ),
    "find_files": _fn(
        "find_files",
        (
            "Find files matching a glob pattern under a directory.\n"
            "Much faster than repeated list_dir calls. Prefer this for locating files by name/extension.\n"
            "The 'directory' parameter is the root to search from (use '.' for current directory).\n"
            "Examples:\n"
            "  find_files(pattern='**/*.py', directory='.')  — all Python files\n"
            "  find_files(pattern='test_*.py', directory='tests/')  — test files\n"
            "  find_files(pattern='*.config', directory='/etc')"
        ),
        {
            "pattern": {"type": "string", "description": "Glob pattern to match filenames. Supports '**' for recursive match. Examples: '**/*.py', 'src/**/*.ts', '*.json'"},
            "directory": {"type": "string", "description": "Root directory to search from. Use '.' for current working directory."},
        },
        required=["pattern", "directory"],
    ),

    # ── Git ──────────────────────────────────────────────────────────────────
    "git_status": _fn(
        "git_status",
        (
            "Show the current git working tree status: staged files, unstaged changes, and untracked files.\n"
            "Run this first before any git operation to understand the current state.\n"
            "No parameters needed."
        ),
        {},
    ),
    "git_diff": _fn(
        "git_diff",
        (
            "Show unstaged changes (diff) for a specific file or all modified files.\n"
            "Use path='' (empty string) to see all uncommitted changes at once.\n"
            "Examples:\n"
            "  git_diff(path='src/main.py')  — diff for one file\n"
            "  git_diff(path='')  — diff for all files"
        ),
        {"path": {"type": "string", "description": "File path to diff. Pass empty string '' to diff all modified files."}},
        required=["path"],
    ),
    "git_revert": _fn(
        "git_revert",
        (
            "Revert all uncommitted changes to a file, restoring it to the last committed state.\n"
            "WARNING: This permanently discards all unsaved edits to the file.\n"
            "Example: git_revert(path='src/broken_file.py')"
        ),
        {"path": {"type": "string", "description": "File path to revert to HEAD. All uncommitted changes will be lost."}},
        required=["path"],
    ),

    # ── Task Management ───────────────────────────────────────────────────────
    "todo_write": _fn(
        "todo_write",
        (
            "Create or REPLACE the entire task list. Use at the start of a multi-step task.\n"
            "CRITICAL: Pass 'todos' as a real JSON array — NOT a JSON string.\n"
            "Every task MUST have 'detail' (how to implement) and 'criteria' (acceptance checklist) filled in — empty strings are rejected.\n"
            "After writing, immediately set the first task to in_progress using todo_update.\n"
            "\n"
            "SIZE LIMIT — keep the call small enough that the streaming\n"
            "tool-call argument JSON fits inside the model's output budget:\n"
            "  • At most 6 tasks per todo_write call.\n"
            "  • Each task's detail+criteria combined ≤ ~400 chars.\n"
            "If you need >6 tasks, write the first 6 with todo_write,\n"
            "then add the rest one at a time with todo_add. Splitting is\n"
            "MANDATORY — large todo_write calls get streaming-truncated\n"
            "and the trailing tasks are silently dropped.\n"
            "\n"
            "Example:\n"
            "  todo_write(todos=[\n"
            "    {\"content\": \"Write parser\", \"activeForm\": \"Writing parser\",\n"
            "     \"status\": \"pending\", \"priority\": \"high\",\n"
            "     \"detail\": \"Parse JSON input using stdlib json module\",\n"
            "     \"criteria\": \"Handles empty input\\nRaises ValueError on invalid JSON\"}\n"
            "  ])"
        ),
        {
            "todos": {
                "type": "array",
                "description": "List of task objects. Every task MUST have detail and criteria filled in.",
                "items": {
                    "type": "object",
                    "properties": {
                        "content":    {"type": "string", "description": "Imperative verb + deliverable (e.g. 'Write counter.sv — 8-bit up-counter')"},
                        "activeForm": {"type": "string", "description": "Present-continuous description (e.g. 'Writing counter.sv')"},
                        "status":     {"type": "string", "enum": ["pending", "in_progress", "completed", "approved", "rejected"], "description": "Task status. New tasks should default to pending; the agent flips to in_progress / completed / approved as it works through them."},
                        "priority":   {"type": "string", "enum": ["high", "medium", "low"], "description": "Task priority"},
                        "detail":     {"type": "string", "description": "REQUIRED: HOW to implement — specific implementation notes, constraints, approach. Must not be empty."},
                        "criteria":   {"type": "string", "description": "REQUIRED: Newline-separated acceptance criteria checklist. Each line is one verifiable condition. Must not be empty."},
                    },
                    "required": ["content", "activeForm", "status", "detail", "criteria"],
                },
            }
        },
        required=["todos"],
    ),
    "todo_update": _fn(
        "todo_update",
        (
            "Update the status (and optionally content/detail) of a single task by its index.\n"
            "index is 1-BASED — the first task is index=1, NOT 0.\n"
            "Typical flow: set in_progress when starting → completed when done → approved/rejected after verification.\n"
            "REQUIRED when status='approved' or 'rejected': 'reason' is mandatory and must be ≥15 chars — the call returns an error otherwise.\n"
            "Examples:\n"
            "  todo_update(index=1, status='in_progress')\n"
            "  todo_update(index=1, status='completed')\n"
            "  todo_update(index=1, status='approved', reason='ran pytest — all 12 tests passed')\n"
            "  todo_update(index=2, status='rejected', reason='output file missing expected header line')"
        ),
        {
            "index": {"type": "integer", "description": "Task index (1-based)"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "approved", "rejected"],
                "description": "New status for the task",
            },
            "reason": {"type": "string", "description": "REQUIRED when status is 'approved' or 'rejected' — call will be rejected with an error if omitted or too short (<15 chars). For 'approved': what you verified (e.g. 'ran pytest — 12/12 passed, output matches spec'). For 'rejected': exact problem and what must change (e.g. 'output.md missing Phase 5 section; regenerate with NVIC details'). Vague values like 'wrong', 'bad', 'failed' are also rejected."},
            "content": {"type": "string", "description": "Optional: update task content"},
            "detail": {"type": "string", "description": "Optional: update task detail"},
        },
        required=["index", "status"],
    ),
    "todo_add": _fn(
        "todo_add",
        (
            "Add a single new task to the list at a specified position.\n"
            "Use instead of todo_write when the list already exists and you just need to insert one task.\n"
            "index is 1-based. Omit index to append at the end.\n"
            "Examples:\n"
            "  todo_add(content='Write unit tests', priority='high')\n"
            "  todo_add(content='Update README', priority='low', index=3)"
        ),
        {
            "content": {"type": "string", "description": "Task description — use imperative verb + deliverable (e.g. 'Fix login bug in auth.py')"},
            "priority": {"type": "string", "enum": ["high", "medium", "low"], "description": "Task priority (default: medium)"},
            "index": {"type": "integer", "description": "Insert position (1-based). Omit to append at the end."},
        },
        required=["content"],
    ),
    "todo_remove": _fn(
        "todo_remove",
        (
            "Remove a task from the list by its 1-based index.\n"
            "Example: todo_remove(index=3)  — removes the 3rd task"
        ),
        {"index": {"type": "integer", "description": "1-based index of the task to remove"}},
        required=["index"],
    ),
    "todo_status": _fn(
        "todo_status",
        (
            "Show a summary of the current task list: how many are pending, in_progress, completed, approved, rejected.\n"
            "No parameters needed. Use to check overall progress at any time."
        ),
        {},
    ),
    "todo_note": _fn(
        "todo_note",
        (
            "Append a progress note to a task's work log. Use during execution to record findings, "
            "attempts, and criteria status — notes survive compression and appear during review/rejection.\n"
            "Call whenever you discover something important.\n"
            "Examples:\n"
            "  todo_note(index=2, text='found: burst_len=15 in instr_cache.sv:17')\n"
            "  todo_note(index=2, text='criteria \"compiles clean\" ✅ — iverilog exit 0')\n"
            "  todo_note(index=2, text='tried direct AXI → failed: missing handshake, switched to wrapper')"
        ),
        {
            "index": {"type": "integer", "description": "1-based task index to log to"},
            "text": {"type": "string", "description": "Note content — what you found, tried, or confirmed"},
        },
        required=["index", "text"],
    ),

    # ── Sub-Agents ────────────────────────────────────────────────────────────
    "background_task": _fn(
        "background_task",
        (
            "Spawn a background sub-agent to handle a long-running task in parallel.\n"
            "Agent types:\n"
            "  • 'explore' — read-only investigation: search code, read docs, analyze structure\n"
            "  • 'execute' — make changes: write/edit files, run commands, implement features\n"
            "  • 'review'  — check quality: verify correctness, run tests, review output\n"
            "Returns a task_id immediately. Use background_output(task_id) to get results.\n"
            "Use background_list() to see all running tasks.\n"
            "Example: background_task(agent='explore', prompt='Find all files that import module X and list line numbers')"
        ),
        {
            "agent": {
                "type": "string",
                "enum": ["explore", "execute", "review"],
                "description": "Sub-agent type: 'explore' (read-only), 'execute' (make changes), 'review' (verify)",
            },
            "prompt": {"type": "string", "description": "Detailed task description for the sub-agent. Be specific about what to find/do/verify."},
        },
        required=["agent", "prompt"],
    ),
    "background_output": _fn(
        "background_output",
        (
            "Retrieve the result of a previously spawned sub-agent task.\n"
            "Blocks until the task is complete or returns partial output if still running.\n"
            "Example: background_output(task_id='abc123')"
        ),
        {"task_id": {"type": "string", "description": "Task ID string returned by background_task"}},
        required=["task_id"],
    ),
    "background_cancel": _fn(
        "background_cancel",
        "Cancel a running sub-agent task before it completes.",
        {"task_id": {"type": "string", "description": "Task ID to cancel (from background_task return value)"}},
        required=["task_id"],
    ),
    "background_list": _fn(
        "background_list",
        "List all currently active or recently completed sub-agent tasks with their status and task IDs.",
        {},
    ),

    # ── Worker (Remote) ──────────────────────────────────────────────────────
    "worker_call": _fn(
        "worker_call",
        (
            "Dispatch a task to a remote Worker agent over HTTP and wait for completion.\n"
            "POST /run → poll /status → return /result when done.\n"
            "Worker runs the full ReAct loop independently.\n"
            "Returns dict with: status, result, files_modified, iterations, error.\n"
            "Example: worker_call(worker='http://localhost:8001', task='Write hello.txt with hello world')"
        ),
        {
            "worker": {"type": "string", "description": "Worker URL (e.g. http://localhost:8001)"},
            "task": {"type": "string", "description": "Task description string for the Worker"},
            "model": {"type": "string", "description": "Model override (empty = worker default)", "default": ""},
            "timeout": {"type": "integer", "description": "Max seconds to wait (default 600)", "default": 600},
            "poll_interval": {"type": "number", "description": "Seconds between status polls (default 2.0)", "default": 2.0},
            "show_log": {"type": "boolean", "description": "Print Worker log to console (default true)", "default": True},
        },
        required=["worker", "task"],
    ),
    "worker_status": _fn(
        "worker_status",
        "Get current status of a Worker run. Returns dict with run_id, status, log_entries, elapsed_s.",
        {
            "worker": {"type": "string", "description": "Worker URL"},
            "run_id": {"type": "string", "description": "Run ID from worker_call"},
        },
        required=["worker", "run_id"],
    ),
    "worker_result": _fn(
        "worker_result",
        "Get final result of a completed Worker run. Returns dict with status, result, files_modified, iterations.",
        {
            "worker": {"type": "string", "description": "Worker URL"},
            "run_id": {"type": "string", "description": "Run ID from worker_call"},
        },
        required=["worker", "run_id"],
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

    # ── Web Tools (Firecrawl) ────────────────────────────────────────────────
    "web_search": _fn(
        "web_search",
        "Search the web using Firecrawl. Returns scraped markdown content for each result. "
        "Use for finding current information, documentation, or answers not in local files.",
        {
            "query": {"type": "string", "description": "Search query string"},
            "limit": {"type": "integer", "description": "Maximum number of results (1-20, default: 5)"},
            "lang": {"type": "string", "description": "Language code (default: 'en', 'ko' for Korean)"},
            "tbs": {"type": "string", "description": "Time filter: 'qdr:d' (day), 'qdr:w' (week), 'qdr:m' (month), 'qdr:y' (year), '' (any)"},
        },
        required=["query"],
    ),
    "web_fetch": _fn(
        "web_fetch",
        "Fetch and scrape content from a specific URL. Returns page content in markdown (default), HTML, or raw HTML format. "
        "Waits for JavaScript rendering.",
        {
            "url": {"type": "string", "description": "URL to scrape"},
            "formats": {
                "type": "string",
                "enum": ["markdown", "html", "rawHtml"],
                "description": "Output format (default: 'markdown')",
            },
            "wait_for": {"type": "integer", "description": "Milliseconds to wait for JS rendering (default: 3000)"},
        },
        required=["url"],
    ),
    "web_extract": _fn(
        "web_extract",
        "Extract structured data from URLs using AI-powered extraction. "
        "Provide a natural language prompt describing what to extract and optional JSON schema for output structure.",
        {
            "urls": {"type": "string", "description": "URL(s) to extract from. Single URL or comma-separated list"},
            "prompt": {"type": "string", "description": "Natural language instruction for what to extract (e.g. 'Extract product name, price, and availability')"},
            "schema": {"type": "string", "description": "JSON schema defining output structure (optional)"},
        },
        required=["urls"],
    ),

    # ── Verilog / SystemVerilog Analysis ────────────────────────────────────
    "analyze_verilog_module": _fn(
        "analyze_verilog_module",
        "Parse a Verilog/SV file and extract module structure: name, ports, parameters, signals, submodule instances, and metrics. Use this before writing testbenches or making RTL changes.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
            "deep": {"type": "boolean", "description": "If true, also analyze timing paths and logic complexity (slower)"},
        },
        required=["path"],
    ),
    "find_signal_usage": _fn(
        "find_signal_usage",
        "Search all Verilog files in a directory for uses of a specific signal — shows declarations, drivers, and readers with file:line references.",
        {
            "directory": {"type": "string", "description": "Directory to search recursively"},
            "signal_name": {"type": "string", "description": "Signal name to search for"},
        },
        required=["directory", "signal_name"],
    ),
    "find_module_definition": _fn(
        "find_module_definition",
        "Search for where a module is defined across all .v/.sv files in a directory. Returns file path, line number, and port count.",
        {
            "module_name": {"type": "string", "description": "Module name to find"},
            "directory": {"type": "string", "description": "Directory to search (default: current directory)"},
        },
        required=["module_name"],
    ),
    "extract_module_hierarchy": _fn(
        "extract_module_hierarchy",
        "Build the instantiation hierarchy tree starting from a top module, scanning all .v/.sv files in a directory. Returns ASCII tree showing which modules instantiate which.",
        {
            "top_module": {"type": "string", "description": "Name of the top-level module"},
            "directory": {"type": "string", "description": "Directory to scan for module definitions"},
        },
        required=["top_module"],
    ),
    "find_potential_issues": _fn(
        "find_potential_issues",
        "Static analysis of a Verilog file to detect undriven signals, multiple drivers, and combinational loops. Returns list of warnings.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    "generate_module_testbench": _fn(
        "generate_module_testbench",
        "Auto-generate a SystemVerilog testbench from a module's port declarations. Handles clock/reset, DUT instantiation, and basic stimulus.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file to generate testbench for"},
            "tb_type": {"type": "string", "enum": ["basic", "random"], "description": "Testbench style: 'basic' (directed) or 'random' (constrained random)"},
        },
        required=["path"],
    ),
    "analyze_timing_paths": _fn(
        "analyze_timing_paths",
        "Estimate combinational logic depth from assign statements in a Verilog file. Warns about deep paths (>5 levels) that may cause timing violations.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    "generate_module_docs": _fn(
        "generate_module_docs",
        "Auto-generate Markdown documentation for a Verilog module: port table, parameters, description, and metrics.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    "suggest_optimizations": _fn(
        "suggest_optimizations",
        "Analyze a Verilog file for optimization opportunities: resource sharing, FSM encoding, expensive operators (division/modulo).",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    # ── pyslang-powered AST tools ────────────────────────────────────────────
    "sv_get_ports": _fn(
        "sv_get_ports",
        "Extract precise port information from a Verilog/SV file using pyslang AST — returns name, direction, type, and width for each port. More accurate than regex parsing.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    "sv_get_hierarchy": _fn(
        "sv_get_hierarchy",
        "Extract submodule instantiation hierarchy from a single Verilog/SV file using pyslang. Works without needing all dependent files to be present.",
        {
            "path": {"type": "string", "description": "Path to .v or .sv file"},
        },
        required=["path"],
    ),
    "sv_compile": _fn(
        "sv_compile",
        "Compile multiple Verilog/SV files together using pyslang and report all cross-reference errors and warnings. No VCS or iverilog needed.",
        {
            "files": {
                "type": "array",
                "items": {"type": "string"},
                "description": "List of .v or .sv file paths to compile together",
            },
        },
        required=["files"],
    ),

    # ── cmux tools ──────────────────────────────────────────────────────────
    "cmux_tree": _fn(
        "cmux_tree",
        "List all cmux surfaces and workspaces. Run first to find surface refs.",
        {},
    ),
    "cmux_capture": _fn(
        "cmux_capture",
        "Capture the modifiable_ai_agent screen text.",
        {"lines": {"type": "integer", "description": "Max lines to capture (default 200)"}},
    ),
    "cmux_send": _fn(
        "cmux_send",
        "Send text to modifiable_ai_agent (Enter is auto-appended). Returns screen after send.",
        {"text": {"type": "string", "description": "Text to send"}},
        required=["text"],
    ),
    "cmux_send_key": _fn(
        "cmux_send_key",
        "Send a special key to modifiable_ai_agent (e.g. 'ctrl+c', 'ctrl+q', 'escape', 'enter').",
        {"key": {"type": "string", "description": "Key to send"}},
        required=["key"],
    ),
    "cmux_restart_modifiable": _fn(
        "cmux_restart_modifiable",
        "Quit and restart modifiable_ai_agent.",
        {},
    ),
    "cmux_set_surface": _fn(
        "cmux_set_surface",
        "Save a surface ref to config so other cmux tools use it by default.",
        {"surface_ref": {"type": "string", "description": "Surface ref (e.g. 'surface:1')"}},
        required=["surface_ref"],
    ),
    "cmux_notify": _fn(
        "cmux_notify",
        "Send a macOS notification.",
        {
            "title": {"type": "string", "description": "Notification title"},
            "body":  {"type": "string", "description": "Notification body (optional)"},
        },
        required=["title"],
    ),
    "cmux_list_panes": _fn(
        "cmux_list_panes",
        "List panes in the current (or given) workspace.",
        {"workspace": {"type": "string", "description": "Workspace ref (optional)"}},
    ),
    "cmux_new_pane": _fn(
        "cmux_new_pane",
        "Split the current workspace to create a new pane.",
        {
            "direction": {"type": "string", "description": "Split direction: left|right|up|down (default right)"},
            "command":   {"type": "string", "description": "Command to run in the new pane (optional)"},
        },
    ),
    "cmux_new_workspace": _fn(
        "cmux_new_workspace",
        "Create a new cmux workspace, optionally running a command.",
        {
            "name":    {"type": "string", "description": "Workspace name (optional)"},
            "command": {"type": "string", "description": "Command to run (optional)"},
            "cwd":     {"type": "string", "description": "Working directory (optional)"},
        },
    ),
    "cmux_focus_pane": _fn(
        "cmux_focus_pane",
        "Move focus to a pane by ref (e.g. 'pane:1').",
        {"pane": {"type": "string", "description": "Pane ref"}},
        required=["pane"],
    ),
    "cmux_resize_pane": _fn(
        "cmux_resize_pane",
        "Resize a pane. direction: L|R|U|D, amount in cells.",
        {
            "pane":      {"type": "string",  "description": "Pane ref"},
            "direction": {"type": "string",  "description": "L|R|U|D"},
            "amount":    {"type": "integer", "description": "Cells to resize (default 5)"},
        },
        required=["pane", "direction"],
    ),
    "cmux_move_surface": _fn(
        "cmux_move_surface",
        "Drag a surface into a new split pane.",
        {
            "surface":   {"type": "string", "description": "Surface ref"},
            "direction": {"type": "string", "description": "left|right|up|down"},
        },
        required=["surface", "direction"],
    ),

    # ── GUI interaction (ask_user) ───────────────────────────────────────────
    "ask_user": _fn(
        "ask_user",
        (
            "Ask the user one or more questions through the GUI and BLOCK "
            "until they answer. Two modes:\n"
            "  • Single-question (default): pass `question` (+ options/kind/subtitle).\n"
            "  • Batched: pass `questions=[{question, kind, options, subtitle}, ...]` "
            "to ask multiple related questions in one round-trip. The user "
            "navigates between them with ←/→ and submits all answers at once. "
            "PREFER batched when you have N related TBDs to resolve in one "
            "iteration — far less disruptive than N sequential calls."
        ),
        properties={
            "question": {
                "type": "string",
                "description": "Single-mode: the main question text. Omit when using `questions`.",
            },
            "kind": {
                "type": "string",
                "enum": ["single", "multi", "input"],
                "description": (
                    "Single-mode: single = radio, multi = checkboxes, "
                    "input = free-form text only. Omit when using `questions`."
                ),
            },
            "options": {
                "type": "array",
                "description": (
                    "Single-mode: list of {id, label, detail?} for single/multi. "
                    "Omit or pass [] for kind='input'. Provide 2-6 options."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "id":     {"type": "string"},
                        "label":  {"type": "string"},
                        "detail": {"type": "string"},
                    },
                    "required": ["id", "label"],
                },
            },
            "subtitle": {
                "type": "string",
                "description": (
                    "Short explainer used as the breadcrumb tab label in "
                    "batch mode. Convention: "
                    "'§<N> <field path> — Suggest: <recommended value>'."
                ),
            },
            "id": {"type": "string", "description": "Optional SSOT QA stable id for single-mode questions."},
            "section_id": {"type": "string", "description": "Optional SSOT section bucket for QA preview."},
            "section_title": {"type": "string", "description": "Optional human-readable SSOT section title."},
            "decision_key": {"type": "string", "description": "Optional stable decision key for QA preview."},
            "decision_label": {"type": "string", "description": "Optional short decision label."},
            "field_path": {"type": "string", "description": "Optional SSOT field path this question resolves."},
            "qa_type": {
                "type": "string",
                "description": "Optional: human_decision | clarification | change_request | execution_blocker.",
            },
            "criteria": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional criteria for accepting and using this answer downstream.",
            },
            "source_refs": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Optional SSOT/doc/RTL references that caused this question.",
            },
            "content": {"type": "string", "description": "Optional concise QA content summary."},
            "detail": {"type": "string", "description": "Optional detailed context for QA preview."},
            "placeholder": {"type": "string", "description": "Optional free-form input placeholder."},
            "multiline": {"type": "boolean", "description": "Optional: render input as multiline."},
            "questions": {
                "type": "array",
                "description": (
                    "Batched mode: a list of question dicts, each with the "
                    "same {question, kind, options, subtitle} keys as a "
                    "single call, plus optional SSOT QA metadata "
                    "{id, section_id, section_title, decision_key, "
                    "decision_label, field_path, qa_type, criteria, source_refs}. "
                    "When set, the other top-level fields are ignored. Use 2-5 "
                    "questions per batch unless the IP genuinely needs more."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "kind":     {"type": "string", "enum": ["single", "multi", "input"]},
                        "subtitle": {"type": "string"},
                        "id": {"type": "string"},
                        "section_id": {"type": "string"},
                        "section_title": {"type": "string"},
                        "decision_key": {"type": "string"},
                        "decision_label": {"type": "string"},
                        "field_path": {"type": "string"},
                        "qa_type": {
                            "type": "string",
                            "description": "human_decision | clarification | change_request | execution_blocker",
                        },
                        "criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "source_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "content": {"type": "string"},
                        "detail": {"type": "string"},
                        "placeholder": {"type": "string"},
                        "multiline": {"type": "boolean"},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id":     {"type": "string"},
                                    "label":  {"type": "string"},
                                    "detail": {"type": "string"},
                                },
                                "required": ["id", "label"],
                            },
                        },
                    },
                    "required": ["question", "kind"],
                },
            },
        },
        required=[],  # validation done at runtime: either question or questions
    ),

    "record_ssot_qa": _fn(
        "record_ssot_qa",
        (
            "Record one or more generated SSOT QA items in the ATLAS QA "
            "preview WITHOUT blocking for an answer. Use this for deferred "
            "human gates, approvals, clarifications, or change requests that "
            "the user can review later. Use ask_user only when the answer is "
            "an immediate blocker."
        ),
        properties={
            "ip": {
                "type": "string",
                "description": "Optional IP name. Defaults to the active ATLAS SSOT IP.",
            },
            "session": {
                "type": "string",
                "description": "Optional session id/path. Defaults to the active ssot-gen session.",
            },
            "kind": {
                "type": "string",
                "description": "Optional IP kind label for QA grouping.",
            },
            "source": {
                "type": "string",
                "description": "Optional QA source tag. Defaults to llm-ssot-qna.",
            },
            "status": {
                "type": "string",
                "enum": ["pending", "approved", "answered", "resolved"],
                "description": "Stored QA status. Usually pending for deferred questions.",
            },
            "question": {
                "type": "string",
                "description": "Single-mode convenience question. Prefer questions=[...] for metadata-rich QA.",
            },
            "questions": {
                "type": "array",
                "description": (
                    "Deferred QA backlog items. Each item should be IP-specific "
                    "and section-specific, not from a fixed template."
                ),
                "items": {
                    "type": "object",
                    "properties": {
                        "question": {"type": "string"},
                        "kind": {"type": "string", "enum": ["single", "multi", "input"]},
                        "subtitle": {"type": "string"},
                        "id": {"type": "string"},
                        "section_id": {"type": "string"},
                        "section_title": {"type": "string"},
                        "section": {"type": "string"},
                        "section_name": {"type": "string"},
                        "decision_key": {"type": "string"},
                        "decision_label": {"type": "string"},
                        "field_path": {"type": "string"},
                        "qa_type": {
                            "type": "string",
                            "description": "human_decision | clarification | change_request | execution_blocker",
                        },
                        "criteria": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "source_refs": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "sources": {
                            "type": "array",
                            "items": {"type": "string"},
                        },
                        "content": {"type": "string"},
                        "detail": {"type": "string"},
                        "placeholder": {"type": "string"},
                        "multiline": {"type": "boolean"},
                        "options": {
                            "type": "array",
                            "items": {
                                "type": "object",
                                "properties": {
                                    "id": {"type": "string"},
                                    "label": {"type": "string"},
                                    "detail": {"type": "string"},
                                },
                                "required": ["id", "label"],
                            },
                        },
                    },
                    "required": [],
                },
            },
        },
        required=[],  # validation done at runtime: either question or questions
    ),

    # ── Document ingestion (Word / PDF / etc. → markdown) ────────────────────
    "read_doc": _fn(
        "read_doc",
        (
            "Convert a PDF, DOCX, PPTX, XLSX, or HTML document into markdown "
            "via Microsoft markitdown. Returns up to 32k chars of text "
            "content the agent can reason over. Use when the user references "
            "a spec / datasheet / requirement doc in a non-text format."
        ),
        properties={
            "path": {
                "type": "string",
                "description": "Filesystem path to the document (relative or absolute).",
            },
        },
        required=["path"],
    ),

    # ── IP scaffolder (canonical directory layout) ───────────────────────────
    "scaffold_ip": _fn(
        "scaffold_ip",
        (
            "Create the canonical IP directory layout under <root>/<name>/ "
            "with subdirs: yaml, rtl, list, tb, tc, sim, sdc, lint, doc, req. "
            "Idempotent — never overwrites existing files. Call this FIRST "
            "for any new IP request before writing the SSOT."
        ),
        properties={
            "name": {
                "type": "string",
                "description": (
                    "IP identifier (C-identifier rules: letters, digits, "
                    "underscore; must start with a letter)."
                ),
            },
            "root": {
                "type": "string",
                "description": (
                    "Where to root the IP. Defaults to '.' (cwd). Pass an "
                    "absolute path or relative subdir if needed."
                ),
            },
        },
        required=["name"],
    ),
}


def get_tool_schemas(allowed_tools: List[str], compact: bool = False) -> List[Dict]:
    """Return OpenAI-compatible tool schema list filtered to allowed_tools.

    Tools not in TOOL_SCHEMAS are silently skipped (e.g. verilog, cmux, tmux tools
    that are conditionally loaded — they won't be callable in native mode unless
    schemas are added above).

    MCP tools registered via register_dynamic_schema() are included automatically.

    Args:
        compact: If True, truncate descriptions to first sentence to reduce payload size.
                 Useful for servers that reject large tool schema payloads (HTTP 500).
                 Enable via TOOL_SCHEMA_COMPACT=true in .config.
    """
    import os as _os
    if not compact:
        compact = _os.getenv("TOOL_SCHEMA_COMPACT", "false").lower() in ("true", "1", "yes")

    merged = {**TOOL_SCHEMAS, **_dynamic_schemas}
    schemas = [merged[t] for t in allowed_tools if t in merged]

    if compact:
        import copy as _copy, re as _re
        # Tools to exclude in compact mode (bulky, rarely needed for basic tasks)
        _compact_exclude = {"background_task", "background_output", "background_cancel",
                            "background_list", "web_search", "web_fetch", "web_extract"}
        schemas = [s for s in _copy.deepcopy(schemas)
                   if s.get("function", {}).get("name") not in _compact_exclude]
        # Minimal description map — hand-tuned for brevity
        _short_desc: Dict[str, str] = {
            "read_file":      "Read file contents",
            "write_file":     "Create new file",
            "run_command":    "Run shell command",
            "list_dir":       "List directory",
            "grep_file":      "Search pattern in file(s)",
            "read_lines":     "Read line range from file",
            "find_files":     "Find files by glob pattern",
            "git_diff":       "Show git diff",
            "git_status":     "Show git status",
            "git_revert":     "Revert file changes",
            "replace_in_file":"Edit file: replace text block",
            "replace_lines":  "Edit file: replace line range",
            "read_image":     "Analyze image with vision AI",
            "todo_write":     "Create task list",
            "todo_update":    "Update task status",
            "todo_add":       "Add task",
            "todo_remove":    "Remove task",
            "todo_status":    "Show task list summary",
            "todo_note":      "Append note to task",
        }
        for s in schemas:
            fn = s.get("function", {})
            name = fn.get("name", "")
            if name in _short_desc:
                fn["description"] = _short_desc[name]
            else:
                desc = fn.get("description", "")
                fn["description"] = _re.split(r'[,\n]|\.\s', desc)[0].strip().rstrip(".")
            # Strip all parameter descriptions — type + required is enough
            for _p in fn.get("parameters", {}).get("properties", {}).values():
                _p.pop("description", None)
                _p.pop("examples", None)

    return schemas


# ── Dynamic schema registry (for MCP and other runtime-discovered tools) ──────

_dynamic_schemas: Dict[str, Dict] = {}


def register_dynamic_schema(name: str, schema: Dict) -> None:
    """Register a tool schema discovered at runtime (e.g. from an MCP server)."""
    _dynamic_schemas[name] = schema
