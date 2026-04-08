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
        "Create or replace the task list. Pass todos as a real array (not a JSON string).",
        {
            "todos": {
                "type": "array",
                "description": "List of task objects",
                "items": {
                    "type": "object",
                    "properties": {
                        "content":    {"type": "string", "description": "Imperative description (e.g. 'Run tests')"},
                        "activeForm": {"type": "string", "description": "Present-continuous description (e.g. 'Running tests')"},
                        "status":     {"type": "string", "enum": ["pending", "in_progress", "completed"], "description": "Task status"},
                    },
                    "required": ["content", "activeForm", "status"],
                },
            }
        },
        required=["todos"],
    ),
    "todo_update": _fn(
        "todo_update",
        "Update task status. index is 1-based. IMPORTANT: status='approved' or 'rejected' REQUIRES a 'reason' argument describing what was verified.",
        {
            "index": {"type": "integer", "description": "Task index (1-based)"},
            "status": {
                "type": "string",
                "enum": ["pending", "in_progress", "completed", "approved", "rejected"],
                "description": "New status for the task",
            },
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
            "agent": {
                "type": "string",
                "enum": ["explore", "execute", "review"],
                "description": "Agent type",
            },
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
}


def get_tool_schemas(allowed_tools: List[str]) -> List[Dict]:
    """Return OpenAI-compatible tool schema list filtered to allowed_tools.

    Tools not in TOOL_SCHEMAS are silently skipped (e.g. verilog, cmux, tmux tools
    that are conditionally loaded — they won't be callable in native mode unless
    schemas are added above).

    MCP tools registered via register_dynamic_schema() are included automatically.
    """
    merged = {**TOOL_SCHEMAS, **_dynamic_schemas}
    return [merged[t] for t in allowed_tools if t in merged]


# ── Dynamic schema registry (for MCP and other runtime-discovered tools) ──────

_dynamic_schemas: Dict[str, Dict] = {}


def register_dynamic_schema(name: str, schema: Dict) -> None:
    """Register a tool schema discovered at runtime (e.g. from an MCP server)."""
    _dynamic_schemas[name] = schema
