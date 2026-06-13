import os
import subprocess
import json
import shlex
import sys
import re
import glob
import threading
from contextlib import contextmanager
from pathlib import Path

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


def _tool_cfg(attr: str, default: int) -> int:
    """Read a tool limit from the live config module."""
    cfg = sys.modules.get('config') or sys.modules.get('src.config')
    return int(getattr(cfg, attr, default))


_TODO_RUNTIME = threading.local()


def _paths_match(left, right) -> bool:
    if left is None or right is None:
        return False
    try:
        return Path(left).expanduser().resolve(strict=False) == Path(right).expanduser().resolve(strict=False)
    except Exception:
        return str(left) == str(right)


def _set_todo_tracker_error(message: str) -> None:
    _TODO_RUNTIME.todo_error = message


def _todo_tracker_unavailable_error() -> str:
    message = str(getattr(_TODO_RUNTIME, "todo_error", "") or "")
    if message:
        return f"Error: {message}"
    return (
        "Error: TodoTracker is not initialized. Check that ENABLE_TODO_TRACKING=true "
        "and config.TODO_FILE points to the active session todo.json."
    )


@contextmanager
def scoped_todo_runtime(todo_tracker=None, todo_file=None):
    """Bind todo tools to a per-run tracker without mutating process globals."""
    had_tracker = hasattr(_TODO_RUNTIME, "todo_tracker")
    had_file = hasattr(_TODO_RUNTIME, "todo_file")
    old_tracker = getattr(_TODO_RUNTIME, "todo_tracker", None)
    old_file = getattr(_TODO_RUNTIME, "todo_file", None)
    try:
        _TODO_RUNTIME.todo_tracker = todo_tracker
        _TODO_RUNTIME.todo_file = Path(todo_file) if todo_file else None
        yield
    finally:
        if had_tracker:
            _TODO_RUNTIME.todo_tracker = old_tracker
        elif hasattr(_TODO_RUNTIME, "todo_tracker"):
            delattr(_TODO_RUNTIME, "todo_tracker")
        if had_file:
            _TODO_RUNTIME.todo_file = old_file
        elif hasattr(_TODO_RUNTIME, "todo_file"):
            delattr(_TODO_RUNTIME, "todo_file")


_IP_SUBDIRS = frozenset({
    "rtl", "yaml", "tb", "tc", "sim", "sdc", "lint", "doc", "wiki",
    "req", "list", "model", "syn", "sta", "pnr", "cov", "verify",
    "todo", "sta-post",
})

_NON_IP_ROOTS = frozenset({
    ".codex", ".git", ".github", ".omx", ".pytest_cache", ".session",
    "__pycache__", "core", "docs", "frontend", "logs", "prompts", "rules",
    "scripts", "src", "tests", "tools", "workflow",
})


# ---------------------------------------------------------------------------
# LLM arg coercion — JSON tool calls deliver every value as a string,
# even for params with numeric / boolean defaults. The previous behavior
# relied on Python truthiness for bools (so recursive="false" silently
# evaluated to True) and on raw int passthrough (so count="3" crashed
# str.replace with "'str' object cannot be interpreted as an integer").
# These helpers normalize incoming strings before the body uses them.
# ---------------------------------------------------------------------------
def _as_bool(v, default: bool = False) -> bool:
    """Coerce LLM-supplied value to bool. Accepts real bools, ints,
    and the strings true/false/yes/no/on/off/1/0/y/n (case-insensitive,
    trimmed). Empty string and unrecognized values return *default*
    (treated as absence of value, not a false)."""
    if v is None:
        return default
    if isinstance(v, bool):
        return v
    if isinstance(v, (int, float)):
        return bool(v)
    if isinstance(v, str):
        s = v.strip().lower()
        if not s:
            return default
        if s in ('true', 't', '1', 'yes', 'y', 'on'):
            return True
        if s in ('false', 'f', '0', 'no', 'n', 'off'):
            return False
    return default


def _as_int(v, default=None):
    """Coerce LLM-supplied value to int. Accepts ints, "42", "  -1 "
    style strings, floats. Returns *default* (which may itself be None)
    if v is None or can't be parsed."""
    if v is None:
        return default
    if isinstance(v, bool):  # bool is a subclass of int — preserve intent
        return int(v)
    if isinstance(v, int):
        return v
    if isinstance(v, float):
        return int(v)
    if isinstance(v, str):
        s = v.strip()
        if not s:
            return default
        try:
            return int(s)
        except ValueError:
            try:
                return int(float(s))
            except ValueError:
                return default
    return default


def _reject_unsafe_hdl_sim_command(command: str, timeout: int):
    """Reject HDL simulation commands that hide hangs or skip staged proof.

    This is intentionally generic: it does not know an IP name, protocol, or
    expected result. It only enforces that cocotb/vvp proof runs are observable
    and staged so workflow prompts cannot paper over a stuck simulator with a
    shell truncation pipeline.
    """
    if not command:
        return None

    lowered = command.lower()

    python_runner = re.search(
        r"(?:^|[;&|]\s*|\b(?:g?timeout|timeout)\s+\d+\s+)"
        r"(?:[a-z_][a-z0-9_]*=\S+\s+)*"
        r"(?:\S*/)?python(?:\d+(?:\.\d+)?)?\s+[^;&|]*"
        r"(?:test_cocotb_runner\.py|run_sim\.py|test_runner\.py)\b",
        lowered,
    )
    make_sim = re.search(
        r"(?:^|[;&|]\s*|\b(?:g?timeout|timeout)\s+\d+\s+)"
        r"(?:[a-z_][a-z0-9_]*=\S+\s+)*make\b[^;&|]*\bsim=",
        lowered,
    )
    vvp_run = re.search(
        r"(?:^|[;&|]\s*|\b(?:g?timeout|timeout)\s+\d+\s+)"
        r"(?:\S*/)?vvp\b",
        lowered,
    )
    if not (python_runner or make_sim or vvp_run):
        return None

    if re.search(r"\|\s*(head|tail|grep|egrep|fgrep)\b", command):
        return (
            "Error: HDL simulation command rejected. Do not pipe cocotb/vvp "
            "runs through head/tail/grep because that can hide hangs and leave "
            "child simulators alive. Run the simulator directly with the "
            "run_command timeout parameter and capture stdout/stderr, or use "
            "workflow/tb-gen/scripts/sim.py."
        )

    is_cocotb_run = bool(python_runner or make_sim)
    has_single_test = (
        "cocotb_testcase=" in lowered
        or "testcase=" in lowered
        or "pytest" in lowered
        or "-k " in lowered
    )
    full_regression_ok = "full_regression_ok=1" in lowered

    if is_cocotb_run and not has_single_test and not full_regression_ok:
        return (
            "Error: HDL simulation command rejected. Cocotb runs must be staged: "
            "set COCOTB_TESTCASE=<single_test> for reset/default and one "
            "representative transfer/protocol scenario first. Use "
            "FULL_REGRESSION_OK=1 only after those bounded scenario runs have "
            "terminated cleanly."
        )

    if timeout > 300:
        return (
            "Error: HDL simulation command rejected. Use a bounded run_command "
            "timeout of 300s or less for HDL simulations."
        )

    return None


# ---------------------------------------------------------------------------
# File access log — tracks which paths were touched during the session
# ---------------------------------------------------------------------------
import builtins as _bi
if not hasattr(_bi, '_FILE_ACCESS_LOG'):
    _bi._FILE_ACCESS_LOG = {}  # {abs_path: {"op": "read"|"write"|"edit"|"grep", "seq": int, ...}}
if not hasattr(_bi, '_FILE_ACCESS_SEQ'):
    _bi._FILE_ACCESS_SEQ = 0


def _log_file_access(path: str, op: str):
    """Record a file access in the session log.

    Args:
        path: File path (will be resolved to absolute).
        op: One of 'read', 'write', 'edit', 'grep'.
    """
    if not path:
        return
    try:
        abs_path = os.path.abspath(os.path.expanduser(path))
    except Exception:
        abs_path = path
    # For display: use relative from CWD if possible
    cwd = os.getcwd()
    if abs_path.startswith(cwd + "/"):
        display = abs_path[len(cwd) + 1:]
    elif abs_path == cwd:
        display = "."
    else:
        display = abs_path

    _bi._FILE_ACCESS_SEQ += 1
    seq = _bi._FILE_ACCESS_SEQ

    existing = _bi._FILE_ACCESS_LOG.get(abs_path)
    if existing:
        existing["seq"] = seq  # update to latest access order
        existing["count"] = existing.get("count", 1) + 1
        existing["display"] = display
        # Upgrade op rank: grep < read < edit < write
        rank = {"grep": 0, "read": 1, "edit": 2, "write": 3}
        if rank.get(op, 0) > rank.get(existing.get("op", "read"), 0):
            existing["op"] = op
    else:
        _bi._FILE_ACCESS_LOG[abs_path] = {"op": op, "display": display, "count": 1, "seq": seq}


def get_file_access_summary() -> str:
    """Return a formatted summary of all file accesses for compression context."""
    log = getattr(_bi, '_FILE_ACCESS_LOG', {})
    if not log:
        return ""

    import os as _os
    # Group by directory
    dirs: dict[str, list[tuple[str, str, int]]] = {}  # dir -> [(display_name, op, count)]
    for abs_path, info in log.items():
        display = info.get("display", abs_path)
        op = info.get("op", "?")
        count = info.get("count", 1)
        parent = _os.path.dirname(abs_path)
        # Make parent relative too
        cwd = _os.getcwd()
        if parent.startswith(cwd + "/"):
            parent_display = parent[len(cwd) + 1:]
        elif parent == cwd:
            parent_display = "."
        else:
            parent_display = parent
        fname = _os.path.basename(abs_path)
        dirs.setdefault(parent_display, []).append((fname, op, count))

    lines = [f"Working Directory: {_os.getcwd()}"]
    for dir_path in sorted(dirs.keys()):
        files = dirs[dir_path]
        lines.append(f"\n  [{dir_path}/]")
        for fname, op, count in sorted(files, key=lambda x: x[0]):
            op_icon = {"read": "📖", "write": "✏️ ", "edit": "🔧"}.get(op, "•")
            lines.append(f"    {op_icon} {fname}  ({op}, {count}x)")

    return "\n".join(lines)


def _atlas_project_root() -> str:
    root = (
        os.environ.get("ATLAS_PROJECT_ROOT", "")
        or os.environ.get("PROJECT_ROOT", "")
    )
    return _normalize_tool_path(root) if root else ""


def _atlas_ip_root() -> str:
    root = os.environ.get("ATLAS_IP_ROOT", "")
    return _normalize_tool_path(root) if root else ""


def _normalize_tool_path(path) -> str:
    """Normalize tool-call path separators before filesystem resolution."""
    return os.path.expanduser(str(path or "").strip()).replace("\\", "/")


def _is_abs_tool_path(path) -> bool:
    norm = _normalize_tool_path(path)
    return (
        os.path.isabs(str(path or ""))
        or os.path.isabs(norm)
        or bool(re.match(r"^[A-Za-z]:/", norm))
        or norm.startswith("//")
    )


def _norm_rel_tool_path(path: str) -> str:
    norm = _normalize_tool_path(path)
    while norm.startswith("./"):
        norm = norm[2:]
    return norm


def _ip_name_from_ssot_leaf(leaf: str) -> str:
    name = os.path.basename(str(leaf or ""))
    for suffix in (".ssot.yaml", ".ssot.yml", "_ssot.yaml", "_ssot.yml"):
        if name.endswith(suffix):
            return name[: -len(suffix)]
    return ""


def _candidate_ip_bases(project_root: str, inferred_ip: str, first_subdir: str) -> list[str]:
    """Candidate roots for unprefixed IP-subdir paths such as yaml/foo.ssot.yaml."""
    bases: list[str] = []
    ip_root = _atlas_ip_root()
    if ip_root:
        ip_root_abs = os.path.abspath(os.path.expanduser(ip_root))
        if os.path.isdir(ip_root_abs):
            # ATLAS_IP_ROOT may be the active IP dir (<root>/<ip>) or a
            # collection root containing many IP dirs. Support both; the CLI
            # historically made this easy to confuse.
            if os.path.isdir(os.path.join(ip_root_abs, first_subdir)):
                bases.append(ip_root_abs)
            if inferred_ip:
                bases.append(os.path.join(ip_root_abs, inferred_ip))
    if project_root and inferred_ip:
        bases.append(os.path.join(project_root, inferred_ip))
    deduped: list[str] = []
    seen: set[str] = set()
    for base in bases:
        norm = os.path.abspath(base)
        if norm not in seen:
            seen.add(norm)
            deduped.append(norm)
    return deduped


def _atlas_ip_project_candidate(path: str) -> str:
    """Return the ATLAS project-root path for IP-scoped relative tool paths.

    ATLAS can run from COMMON_AI_AGENT_HOME while serving a different
    --root. In that mode, paths like ``uart/yaml/uart.ssot.yaml`` and
    ``yaml/uart.ssot.yaml`` must resolve under ATLAS_PROJECT_ROOT, even if
    a stale duplicate exists under the server cwd.
    """
    if not path or _is_abs_tool_path(path):
        return ""
    project_root = _atlas_project_root()
    if not project_root:
        return ""
    norm = _norm_rel_tool_path(path)
    parts = [p for p in norm.split("/") if p and p != "."]
    if not parts or any(p == ".." for p in parts):
        return ""

    active_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    first = parts[0]
    if active_ip and active_ip != "default":
        if first == active_ip:
            return os.path.join(project_root, *parts)
        if first in _IP_SUBDIRS:
            return os.path.join(project_root, active_ip, *parts)

    if len(parts) >= 2 and parts[1] in _IP_SUBDIRS and first not in _NON_IP_ROOTS:
        return os.path.join(project_root, *parts)
    if len(parts) >= 2 and first in _IP_SUBDIRS:
        inferred_ip = _ip_name_from_ssot_leaf(parts[1])
        for base in _candidate_ip_bases(project_root, inferred_ip, first):
            return os.path.join(base, *parts)
    return ""


def _resolve_asset_path(path):
    """Resolve a relative path against, in order:
      1. ATLAS_PROJECT_ROOT for IP-scoped paths, including
         `<ip>/<subdir>/...` and `<subdir>/...` when ATLAS_ACTIVE_IP is set
      2. cwd for non-IP paths (preserves user-intended layouts)
      3. ATLAS_PROJECT_ROOT for existing project-level paths
      4. COMMON_AI_AGENT_HOME (bundled-asset fallback — workflow/, rules/,
         and other install-anchored files referenced by prompts).

    Read-only. Returns the original path if no candidate exists, so the
    caller's existing not-found error message still fires correctly.
    """
    if not path:
        return path
    path = _normalize_tool_path(path)
    # Absolute paths bypass the search entirely.
    if _is_abs_tool_path(path):
        return path
    atlas_ip_candidate = _atlas_ip_project_candidate(path)
    if atlas_ip_candidate:
        return atlas_ip_candidate

    # cwd wins for non-IP-scoped paths if the file exists there
    # (preserves user-intended layouts).
    if os.path.exists(path):
        return path
    project_root = _atlas_project_root()
    if project_root:
        candidate = os.path.join(project_root, path)
        if os.path.exists(candidate):
            return candidate
    home = os.environ.get("COMMON_AI_AGENT_HOME", "")
    if home:
        candidate = os.path.join(home, path)
        if os.path.exists(candidate):
            return candidate
    return path


def _resolve_glob_path(path):
    """Resolve a glob-capable path while preserving wildcard segments."""
    if not path:
        return path
    path = _normalize_tool_path(path)
    if _is_abs_tool_path(path):
        return path
    atlas_ip_candidate = _atlas_ip_project_candidate(path)
    if atlas_ip_candidate:
        return atlas_ip_candidate
    project_root = _atlas_project_root()
    if project_root:
        candidate = os.path.join(project_root, path)
        if glob.glob(candidate, recursive=True):
            return candidate
    home = os.environ.get("COMMON_AI_AGENT_HOME", "")
    if home:
        candidate = os.path.join(home, path)
        if glob.glob(candidate, recursive=True):
            return candidate
    return path


def _resolve_write_path(path):
    """Write-side counterpart to _resolve_asset_path.

    Reads can often rely on os.path.exists() to pick a candidate; writes
    cannot because the target may not exist yet. Relative IP paths always
    route under ATLAS_PROJECT_ROOT:
      - `<ip>/<subdir>/...` -> `<PROJECT_ROOT>/<ip>/<subdir>/...`
      - `<subdir>/...` with ATLAS_ACTIVE_IP -> `<PROJECT_ROOT>/<active_ip>/<subdir>/...`

    Project-level paths (workflow/, .session/, anything outside the
    per-IP layout) fall through untouched and land in cwd.
    """
    if not path:
        return path
    path = _normalize_tool_path(path)
    if _is_abs_tool_path(path):
        return path
    atlas_ip_candidate = _atlas_ip_project_candidate(path)
    if atlas_ip_candidate:
        return atlas_ip_candidate
    if os.path.exists(path):
        return path
    project_root = _atlas_project_root()
    if not project_root:
        return path
    active_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if not active_ip or active_ip == "default":
        return path
    norm = _norm_rel_tool_path(path)
    first = norm.split("/", 1)[0]
    if first in _IP_SUBDIRS:
        return os.path.join(project_root, active_ip, norm)
    return path


def _locked_truth_tool_write_error(path):
    project_root_raw = _atlas_project_root()
    if not project_root_raw:
        return None
    try:
        project_root = Path(project_root_raw).expanduser().resolve(strict=False)
        candidate = Path(path).expanduser().resolve(strict=False)
        rel_path = candidate.relative_to(project_root)
    except (OSError, ValueError):
        return None
    if len(rel_path.parts) < 2 or rel_path.parts[1] != "req":
        return None
    ip = rel_path.parts[0]
    try:
        from core.locked_truth_guard import locked_truth_write_error
    except ModuleNotFoundError:
        from locked_truth_guard import locked_truth_write_error
    return locked_truth_write_error(project_root, ip, str(candidate))


def _active_ip_dot_search_root(directory):
    norm = _norm_rel_tool_path(str(directory or "."))
    if norm not in {"", "."}:
        return ""
    project_root = _atlas_project_root()
    active_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if not project_root or not active_ip or active_ip == "default":
        return ""
    active_root = os.path.join(project_root, active_ip)
    return active_root if os.path.isdir(active_root) else ""


def _summarize_atlas_rtl_ledger(path, total_lines):
    """Return a compact view for large ATLAS RTL ledgers."""
    basename = os.path.basename(path)
    if basename not in {"rtl_todo_plan.json", "rtl_todo_tracker.json", "rtl_authoring_plan.json"}:
        return ""
    norm = path.replace("\\", "/")
    if "/rtl/" not in norm:
        return ""

    try:
        with open(path, "r", encoding="utf-8") as f:
            data = json.load(f)
    except Exception as exc:
        return (
            f"[ATLAS RTL LEDGER SUMMARY unavailable: {exc}]\n"
            f"Use read_lines(path=\"{path}\", start_line=1, end_line=120) for a bounded preview."
        )

    def _pick(d, keys):
        if not isinstance(d, dict):
            return {}
        return {k: d.get(k) for k in keys if k in d}

    def _task_preview(tasks, limit=12):
        preview = []
        for item in (tasks or [])[:limit]:
            if not isinstance(item, dict):
                preview.append(str(item)[:160])
                continue
            preview.append(_pick(item, [
                "id", "content", "category", "owner_module", "owner_file",
                "source_ref", "priority", "required", "status",
            ]))
        return preview

    def _compact_summary(summary):
        if not isinstance(summary, dict):
            return {}
        compact_summary = _pick(summary, [
            "blocking_questions", "required_tasks", "orphan_tasks",
            "rtl_gate_todos", "ssot_workflow_todos", "rtl_quality_profile",
            "reference_profile_present", "pending_connection_contract_suggestions",
            "deferred_human_qa_allowed", "pass_allowed",
            "recommended_packet_batch_limit", "llm_actionable_packets",
            "llm_actionable_tasks", "human_locked_packets", "human_locked_tasks",
            "module_packets", "packets", "max_packet_required_tasks",
        ])
        if isinstance(summary.get("by_category"), dict):
            compact_summary["by_category"] = summary["by_category"]
        if isinstance(summary.get("owner_modules"), list):
            compact_summary["owner_module_count"] = len(summary["owner_modules"])
            compact_summary["owner_modules_preview"] = summary["owner_modules"][:16]
        if isinstance(summary.get("next_llm_packets"), list):
            compact_summary["next_llm_packets"] = summary["next_llm_packets"][:12]
        return compact_summary

    def _compact_gate(gate):
        if not isinstance(gate, dict):
            return {}
        compact_gate = _pick(gate, [
            "status", "audit_rtl", "all_required_todos_pass",
            "blocking_questions", "orphan_tasks",
        ])
        for key in ("open_required_todos", "static_missing"):
            val = gate.get(key)
            if isinstance(val, list):
                compact_gate[f"{key}_count"] = len(val)
                compact_gate[f"{key}_preview"] = val[:12]
            elif val is not None:
                compact_gate[key] = val
        return compact_gate

    compact = {
        "file": path,
        "total_lines": total_lines,
        "note": "Compact ATLAS RTL ledger view. Read rtl_authoring_status.md first, then targeted packet JSON/MD files.",
    }
    if basename == "rtl_todo_plan.json":
        tasks = data.get("tasks") if isinstance(data, dict) else []
        compact.update({
            "top": data.get("top"),
            "summary": _compact_summary(data.get("summary", {})),
            "gate": _compact_gate(data.get("gate", {})),
            "todo_completion": _pick(data.get("todo_completion", {}), [
                "status", "required_total", "required_passed", "required_open",
                "pass_count", "fail_count", "pending_count",
            ]),
            "task_count": len(tasks) if isinstance(tasks, list) else None,
            "first_tasks": _task_preview(tasks),
        })
    elif basename == "rtl_todo_tracker.json":
        tasks = data.get("tasks") if isinstance(data, dict) else []
        compact.update({
            "name": data.get("name"),
            "source_plan": data.get("source_plan"),
            "source_task_count": data.get("source_task_count"),
            "status_counts": data.get("status_counts", {}),
            "ui_grouping": data.get("ui_grouping", {}),
            "first_tasks": _task_preview(tasks),
        })
    elif basename == "rtl_authoring_plan.json":
        packets = data.get("packets") if isinstance(data, dict) else []
        packet_preview = []
        for pkt in (packets or [])[:16]:
            if not isinstance(pkt, dict):
                continue
            summary = pkt.get("summary") if isinstance(pkt.get("summary"), dict) else {}
            packet_preview.append({
                "packet_id": pkt.get("packet_id"),
                "kind": pkt.get("kind"),
                "owner_module": pkt.get("owner_module"),
                "owner_file": pkt.get("owner_file"),
                "json": pkt.get("json"),
                "markdown": pkt.get("markdown"),
                "open_required_count": summary.get("open_required_count"),
                "required_count": summary.get("required_count"),
                "categories": summary.get("categories"),
            })
        policy = data.get("execution_policy") if isinstance(data.get("execution_policy"), dict) else {}
        compact.update({
            "top": data.get("top"),
            "summary": _compact_summary(data.get("summary", {})),
            "execution_policy": _pick(policy, [
                "draft_allowed", "deferred_human_qa_allowed", "gate_status",
                "pass_allowed", "connection_contract_gap",
            ]),
            "packet_count": len(packets) if isinstance(packets, list) else None,
            "first_packets": packet_preview,
        })

    return (
        "[ATLAS RTL LEDGER COMPACT READ]\n"
        + json.dumps(compact, indent=2, ensure_ascii=False)
        + "\n\nDo not call read_file on this ledger again for full contents. "
        + f"Use grep_file/read_lines on {path}, or read specific files listed in "
        + "rtl_authoring_status.md and rtl/authoring_packets/.\n"
    )


def read_file(path):
    """
    Reads the content of a file with smart truncation for large files.
    Use this instead of run_command (cat/head/tail) for reading files.

    For files >500 lines, automatically truncates and suggests better alternatives:
    - Use grep_file to find specific sections
    - Use read_lines with offset/limit for targeted reading
    """
    try:
        path = _resolve_asset_path(path)

        # ATLAS has two roots — the user's IP_ROOT (cwd, where IPs live)
        # and the ATLAS source tree where workflow/ + src/ + core/ + ...
        # live. When the LLM passes a path that doesn't exist under cwd
        # but does exist under the ATLAS source tree, redirect there
        # instead of erroring. This is the structural fix for two-root
        # confusion — see the FILESYSTEM LAYOUT block in the system
        # prompt for the same split documented to the LLM.
        if not os.path.exists(path):
            try:
                # core/tools.py → core/ → parent = ATLAS source root.
                atlas_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
            except Exception:
                atlas_root = ""
            if atlas_root:
                # Strip any fabricated absolute prefix down to the first
                # recognized top-level subtree, then try under atlas_root.
                # Works for both "/Users/.../ROOT_IP/workflow/..." and the
                # already-relative "workflow/..." form.
                rel = path
                for anchor in ("workflow/", "src/", "core/", "frontend/",
                                "scripts/", "tools/", "tests/"):
                    idx = path.find("/" + anchor)
                    if idx >= 0:
                        rel = path[idx + 1:]
                        break
                    if path.startswith(anchor):
                        rel = path
                        break
                candidate = os.path.join(atlas_root, rel)
                if os.path.exists(candidate):
                    path = candidate

        if not os.path.exists(path):
            # Try to suggest similar files nearby (limited scope)
            import glob as _glob
            basename = os.path.basename(path)
            parent = os.path.dirname(path) or "."
            suggestions = []
            # Only search in parent directory and one level deep
            # Avoid recursive glob from root (e.g., /tmp -> /)
            search_dir = parent if os.path.isdir(parent) else os.path.dirname(parent)
            if search_dir and os.path.isdir(search_dir) and search_dir != "/":
                try:
                    # Shallow search: parent dir + one level of subdirs
                    found = _glob.glob(os.path.join(search_dir, "*", basename))[:3]
                    if not found:
                        found = _glob.glob(os.path.join(search_dir, basename))[:3]
                    suggestions.extend(found)
                except Exception:
                    pass
            if suggestions:
                hint = ", ".join(f"'{s}'" for s in suggestions[:3])
                return f"Error: File '{path}' does not exist. Did you mean: {hint}? Use find_files() to confirm."
            return f"Error: File '{path}' does not exist. Use find_files('{basename}') to locate it."

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        total_lines = len(lines)
        rtl_ledger_summary = _summarize_atlas_rtl_ledger(path, total_lines)
        if rtl_ledger_summary:
            _log_file_access(path, "read")
            return rtl_ledger_summary

        # Smart truncation for large files (Grep-first pattern)
        MAX_LINES = _tool_cfg('TOOL_READ_MAX_LINES', 500)
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
            _log_file_access(path, "read")
            return content + suggestion
        else:
            # Small file - read entire content
            _log_file_access(path, "read")
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
    """Call LLM to generate a short commit message. Returns '' on failure.

    Uses the same LLM_BASE_URL / LLM_API_KEY / LLM_MODEL_NAME as the main agent
    so no separate API key is needed.
    """
    try:
        import config as _cfg
        import sys as _sys
        import os as _os
        # Locate llm_client (src directory)
        _src = _os.path.join(_os.path.dirname(_os.path.dirname(_os.path.abspath(__file__))), 'src')
        if _src not in _sys.path:
            _sys.path.insert(0, _src)
        import llm_client as _lc
        # Use SECONDARY_MODEL (same endpoint/key as main LLM, no extra auth needed)
        model = getattr(_cfg, 'SECONDARY_MODEL', None) or getattr(_cfg, 'MODEL_NAME', None)
        temperature = getattr(_cfg, 'GIT_COMMIT_SUMMARY_TEMPERATURE', 0.3)
        prompt = (
            f"Write a git commit message in 60 chars or less (no quotes, no markdown) "
            f"describing this file change.\n"
            f"File: {path}\n"
            f"Preview:\n{content_hint[:600]}\n\n"
            f"Reply with ONLY the commit message."
        )
        result = _lc.call_llm_raw(prompt=prompt, model=model, temperature=temperature)
        if not result or result.startswith("Error"):
            raise ValueError(result)
        return result.strip()[:60]
    except Exception as e:
        # Silent failure — don't pollute console with LLM errors during commits
        if getattr(_cfg, 'DEBUG_MODE', False):
            print(f"[Git] commit summary LLM failed ({model}): {e}")
        # After 3 consecutive failures, disable summary mode for this session
        _commit_llm_failures[0] += 1
        if _commit_llm_failures[0] >= 3:
            os.environ['GIT_COMMIT_MSG_MODE'] = 'simple'
            if getattr(_cfg, 'DEBUG_MODE', False):
                print("[Git] Auto-switched to simple commit mode after 3 LLM failures")
        return ""


_git_lock = __import__('threading').Lock()
_commit_llm_failures = [0]  # Mutable counter for LLM commit failures


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
            # PROJECT_ROOT escape guard: if the walk-up landed at OR ABOVE the
            # project root (e.g. common_ai_agent has no .git of its own and
            # the search climbed to its parent's .git), don't commit there —
            # that pollutes the outer repo with per-task auto-commits. Atlas's
            # _auto_commit_for_path in atlas_ui.py already has this guard;
            # this is the mirror for tools.py.
            _proj_root = os.environ.get("ATLAS_PROJECT_ROOT") or os.getcwd()
            try:
                _proj_real = os.path.realpath(_proj_root)
                _git_real  = os.path.realpath(git_root)
                # Refuse if git_root is the project root itself OR an ancestor.
                if _git_real == _proj_real or _proj_real.startswith(_git_real + os.sep):
                    return
            except Exception:
                pass
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


def commit_ip(message: str = None, path: str = None) -> str:
    """
    Manually commit the working tree of an IP's per-IP git repo with a
    labeled checkpoint. Use this when:
      - You finished a meaningful unit of work (e.g. completed a sub-task,
        passed a lint stage, drafted a new RTL module) and want to seal it
        as a revertable checkpoint *before* moving on.
      - The auto-commit-per-file granularity is too noisy and you want a
        single labeled commit covering several recent edits.
      - The user asks "commit this", "snapshot it", "checkpoint", etc.

    The function walks up from `path` (or the current working dir) to find
    the nearest per-IP `.git`, stages everything tracked + untracked, and
    commits with the supplied `message`. Never escapes outside the
    project. Safe to call when there are no changes — produces an empty
    commit so the timeline still has a marker.

    Args:
        message: Short summary of what was done (1 line, <= 80 chars).
                 If empty, defaults to "atlas: manual checkpoint".
        path:    Any path inside the IP (defaults to cwd). The .git search
                 starts here and walks up.

    Returns:
        "✅ committed <short-hash>: <message>" on success, error string otherwise.
    """
    try:
        msg = (str(message) if message is not None else "").strip()
        if not msg:
            msg = "atlas: manual checkpoint"
        msg = msg.splitlines()[0][:120]
        start = os.path.abspath(path) if path else os.getcwd()
        git_root = _find_git_root(start)
        if git_root is None:
            return "⚠ commit_ip: no per-IP git repo found from " + start
        subprocess.run(["git", "add", "--", "."],
                       cwd=git_root, capture_output=True, timeout=15)
        out = subprocess.run(
            ["git", "commit", "--allow-empty", "-m", msg],
            cwd=git_root, capture_output=True, timeout=15,
        )
        if out.returncode != 0:
            return "⚠ commit_ip failed: " + out.stderr.decode("utf-8", "replace")[:200]
        head = subprocess.run(
            ["git", "rev-parse", "--short", "HEAD"],
            cwd=git_root, capture_output=True, timeout=5,
        )
        short = head.stdout.decode("utf-8", "replace").strip() or "?"
        return f"✅ committed {short}: {msg}"
    except Exception as exc:
        return "⚠ commit_ip error: " + str(exc)


def _ssot_yaml_write_unwrap(path: str, content: str, append: bool) -> str:
    """Auto-correct (do NOT reject) the one .ssot.yaml mistake this repo keeps
    hitting: an LLM writing the headless artifact JSON envelope
    ({"files":[{"path":...,"content":"<yaml>"}]}) verbatim instead of raw YAML.

    Rather than reject and force a retry loop, transparently unwrap the inner
    YAML and write THAT, so the file lands correct on the first try. Anything
    that is not this exact envelope passes through untouched — scalars, drafts,
    section content, normal YAML all write as-is. Appends are never touched.
    """
    base = os.path.basename(str(path or "")).lower()
    if append or not (base.endswith(".ssot.yaml") or base.endswith(".ssot.yml")):
        return content
    stripped = (content or "").lstrip()
    if not (stripped.startswith("{") and '"content"' in stripped and '"files"' in stripped[:200]):
        return content
    # Well-formed envelope: structurally extract the ssot file's content.
    try:
        import json as _json_uw
        obj = _json_uw.loads(stripped)
    except Exception:
        obj = None
    if isinstance(obj, dict) and isinstance(obj.get("files"), list):
        ssot_entry = first_entry = None
        for item in obj["files"]:
            if not isinstance(item, dict) or not isinstance(item.get("content"), str):
                continue
            if first_entry is None:
                first_entry = item
            kind = str(item.get("kind") or "").lower()
            p = str(item.get("path") or "")
            if kind == "ssot" or p.endswith((".ssot.yaml", ".ssot.yml", "_ssot.yaml")):
                ssot_entry = item
                break
        chosen = ssot_entry or first_entry
        if chosen is not None:
            return chosen["content"]
    # Truncated/invalid envelope (clipped stream): best-effort decode the first
    # "content":"..." JSON string prefix so the parseable YAML head survives.
    import re as _re_uw
    marker = _re_uw.search(r'"content"\s*:\s*"', stripped)
    if marker:
        s = stripped[marker.end():]
        out = []
        i, n = 0, len(s)
        simple = {"n": "\n", "t": "\t", "r": "\r", '"': '"', "\\": "\\", "/": "/", "b": "\b", "f": "\f"}
        while i < n:
            c = s[i]
            if c == "\\" and i + 1 < n:
                esc = s[i + 1]
                if esc == "u" and i + 5 < n:
                    try:
                        out.append(chr(int(s[i + 2:i + 6], 16)))
                        i += 6
                        continue
                    except ValueError:
                        pass
                out.append(simple.get(esc, esc))
                i += 2
            elif c == '"':
                break
            else:
                out.append(c)
                i += 1
        recovered = "".join(out)
        if recovered.strip():
            return recovered
    return content


def write_file(path: str = None, content: str = None, append: bool = False) -> str:
    """
    Writes content to a file. Overwrites by default; set append=True to add to end.
    Use this instead of run_command (echo/tee/printf) for writing files.
    For large files, write in sections using append=True to avoid corruption.

    Args:
        path: File path to write to
        content: Content to write
        append: If True, append to existing file instead of overwriting (default: False)

    Returns:
        Success message with optional lint warnings
    """
    if path is None:
        return "Error: write_file() requires 'path'. Usage: write_file(path=\"out.sv\", content=\"...\")"
    if content is None:
        return "Error: write_file() requires 'content'. Usage: write_file(path=\"out.sv\", content=\"...\")"
    # Import config
    try:
        import config
        ENABLE_LINTING = config.ENABLE_LINTING
    except:
        ENABLE_LINTING = True  # Default to enabled

    try:
        # LLM may pass append="false" (string) — that's truthy and would
        # silently flip mode to append. Coerce explicitly.
        append = _as_bool(append, default=False)
        path = _resolve_write_path(path)
        locked_truth_error = _locked_truth_tool_write_error(path)
        if locked_truth_error is not None:
            return locked_truth_error
        content = _ssot_yaml_write_unwrap(path, content, append)
        dir_name = os.path.dirname(path)
        if dir_name:
            os.makedirs(dir_name, exist_ok=True)
        if os.path.exists(path):
            _auto_chmod_if_needed(path)
        mode = 'a' if append else 'w'
        # Cross-process lock at the IP-directory granularity. When
        # multiple HTTP workers run in parallel they may both target
        # the same IP — we serialise by sentinel file inside <ip>/.
        # Files outside any IP dir lock at the project root.
        from core.worker_lock import with_ip_lock
        with with_ip_lock(path, label=f"write_file:{os.path.basename(path)}"):
            with open(path, mode, encoding='utf-8') as f:
                f.write(content)

        result = f"Successfully {'appended to' if append else 'wrote to'} '{path}'."

        import threading as _t
        _t.Thread(target=_git_auto_commit, args=(path, "write"), kwargs={"content_hint": content[:800]}, daemon=False).start()
        _log_file_access(path, "write")
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


def _decode_robust(b):
    """Decode subprocess output with platform-aware fallback chain.

    Windows: many native binaries (dir, ipconfig, msvc cl.exe, gcc on Korean
    Windows, etc.) emit cp949 / cp1252, NOT utf-8. Forcing utf-8 produces
    mojibake. Try utf-8 first, then platform-typical legacy codepage, then
    cp1252, finally utf-8 with errors='replace' as last resort.
    """
    if isinstance(b, str):
        return b
    if not isinstance(b, (bytes, bytearray)):
        return str(b or "")
    candidates = ['utf-8']
    if sys.platform == 'win32':
        candidates += ['cp949', 'cp1252', 'mbcs']
    elif sys.platform.startswith('linux') or sys.platform == 'darwin':
        # macOS/Linux generally utf-8, but legacy tools may emit cp949 too
        candidates += ['cp949']
    for enc in candidates:
        try:
            return b.decode(enc)
        except (UnicodeDecodeError, LookupError):
            continue
    return b.decode('utf-8', errors='replace')


def _command_references_active_ip_path(command, active_ip):
    """Return true when a shell command names the active IP as a path prefix.

    Bare IP arguments, such as `derive_rtl_todos.py uart_v2 --root ...`, should
    still run from the active IP root. Path arguments, such as
    `uart_v2/rtl/foo.sv`, should run from the project root to avoid creating
    nested `<ip>/<ip>/...` artifacts.
    """
    if not command or not active_ip or active_ip == "default":
        return False
    command_text = str(command).replace("\\", "/")
    if "$ATLAS_ACTIVE_IP/" in command_text or "${ATLAS_ACTIVE_IP}/" in command_text:
        return True
    import re as _re

    ip_pat = _re.escape(str(active_ip).strip())
    if _re.search(rf'(?<![A-Za-z0-9_.-])(?:\./)?{ip_pat}/+', command_text):
        return True
    return bool(
        _re.search(
            rf'(?<![A-Za-z0-9_.-])cd\s+(?:--\s+)?(?:"(?:\./)?{ip_pat}"|\'(?:\./)?{ip_pat}\'|(?:\./)?{ip_pat})(?=$|[\s;&|])',
            command_text,
        )
    )


def _atlas_command_cwd_for(command=""):
    project_root = _atlas_project_root()
    active_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    command_cwd = None
    if project_root:
        uses_project_root_path = _command_references_active_ip_path(command, active_ip)
        if active_ip and active_ip != "default" and not uses_project_root_path:
            ip_path = os.path.join(project_root, active_ip)
            if os.path.isdir(ip_path):
                command_cwd = ip_path
        if command_cwd is None:
            command_cwd = project_root
    return command_cwd


def run_command(command, timeout=60):
    """
    Runs a shell command and returns output.

    Use for: compilation, simulation, tests, git, make, custom scripts.
    Do NOT use run_command to read files — use read_file instead.
    Do NOT use run_command to write files — use write_file instead.
    Do NOT use run_command to search code — use grep_file instead.
    Do NOT use run_command to list directories — use list_dir instead.
    In ATLAS IP sessions, commands run from the active IP root
    ($ATLAS_PROJECT_ROOT/$ATLAS_ACTIVE_IP). Use IP-root relative paths such as
    rtl/foo.sv or model/functional_model.py, not <ip>/rtl/foo.sv. If a legacy
    <ip>/... path is present, the tool runs from ATLAS_PROJECT_ROOT instead to
    avoid nested <ip>/<ip>/... artifacts.

    Args:
        command: The shell command to run.
        timeout: Optional timeout in seconds (default: 60).
    """
    import signal
    import time

    try:
        # subprocess.communicate(timeout=...) needs int/float — coerce
        # so the LLM can pass timeout="60" as a string without crashing.
        timeout = _as_int(timeout, default=60) or 60
        # Block destructive commands unless explicitly permitted via config
        _blocked = _is_dangerous_command(command)
        if _blocked:
            return f"Error: Command '{command.split()[0]}' is blocked. Enable it with /permission {command.split()[0]} on (or set ALLOW_{command.split()[0].upper()}=true in .config)."

        _sim_block = _reject_unsafe_hdl_sim_command(command, timeout)
        if _sim_block:
            return _sim_block

        # Translate Unix commands to Windows equivalents
        command = _translate_command_for_windows(command)

        # Pin cwd to ATLAS_PROJECT_ROOT/ATLAS_ACTIVE_IP so `pwd`, `ls`,
        # `git status`, etc. run from the active IP directory the user
        # explicitly set with --root + -ip. If the command already references
        # the active IP as a path prefix (`uart_v2/rtl/...`), run from
        # PROJECT_ROOT instead so legacy project-root paths do not create
        # nested `<ip>/<ip>/...` artifacts.
        _cmd_cwd = _atlas_command_cwd_for(command)

        # Receive raw bytes; decode with platform-aware fallback chain in
        # _decode_robust(). text=True + encoding='utf-8' breaks on Windows
        # cp949 / cp1252 native tool output (Korean Windows, msvc cl.exe).
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=False,
            cwd=_cmd_cwd,
            # Create new process group so we can kill the entire tree
            preexec_fn=os.setsid if hasattr(os, 'setsid') else None,
            # Windows: create new process group via CREATE_NEW_PROCESS_GROUP
            creationflags=subprocess.CREATE_NEW_PROCESS_GROUP if sys.platform == 'win32' else 0,
        )

        try:
            stdout_b, stderr_b = proc.communicate(timeout=timeout)
            stdout_str = _decode_robust(stdout_b)
            stderr_str = _decode_robust(stderr_b)
        except subprocess.TimeoutExpired:
            # Timeout — kill the entire process group first
            _kill_process_group(proc)

            # After kill, call communicate() again to join internal threads
            # and collect whatever partial output was produced.
            try:
                stdout_b, stderr_b = proc.communicate(timeout=5)
                stdout_str = _decode_robust(stdout_b)
                stderr_str = _decode_robust(stderr_b)
            except (subprocess.TimeoutExpired, Exception):
                stdout_str, stderr_str = "", ""

            stdout_str = stdout_str or ""
            stderr_str = stderr_str or ""

            partial_parts = []
            if stdout_str.strip():
                partial_parts.append(f"Partial STDOUT:\n{stdout_str.strip()}")
            if stderr_str.strip():
                partial_parts.append(f"Partial STDERR:\n{stderr_str.strip()}")

            partial_info = "\n".join(partial_parts)
            if partial_info:
                return f"Error: Command timed out after {timeout}s.\n{partial_info}"
            else:
                return f"Error: Command timed out after {timeout}s."

        stdout_str = stdout_str or ""
        stderr_str = stderr_str or ""

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
    except Exception as e:
        return f"Error running command: {e}"


def _kill_process_group(proc):
    """Kill a subprocess and its entire process group (children included)."""
    import signal
    try:
        pgid = os.getpgid(proc.pid)
        os.killpg(pgid, signal.SIGKILL)
    except (OSError, ProcessLookupError):
        pass
    try:
        proc.kill()
        proc.wait(timeout=3)
    except Exception:
        pass


def _auto_chmod_if_needed(path: str) -> bool:
    """chmod u+w on path if AUTO_CHMOD_WRITE is enabled. Returns True if chmod was applied."""
    import sys as _sys
    _cfg = _sys.modules.get('config') or _sys.modules.get('src.config')
    if not getattr(_cfg, 'AUTO_CHMOD_WRITE', False):
        return False
    try:
        import stat
        st = os.stat(path)
        if not (st.st_mode & stat.S_IWUSR):
            os.chmod(path, st.st_mode | stat.S_IWUSR)
            return True
    except Exception:
        pass
    return False


def _is_dangerous_command(command: str) -> bool:
    """
    Heuristic check for destructive commands.
    rm/mv are blocked unless ALLOW_RM/ALLOW_MV are enabled via config or /permission.
    """
    import sys as _sys
    cmd = (command or "").strip().lower()
    if not cmd:
        return False

    # Load config flags (runtime-patchable via /permission command)
    _cfg = _sys.modules.get('config') or _sys.modules.get('src.config')
    allow_rm = getattr(_cfg, 'ALLOW_RM', False) if _cfg else False
    allow_mv = getattr(_cfg, 'ALLOW_MV', False) if _cfg else False

    # Always-blocked patterns (regardless of permission flags)
    always_blocked = [
        r"\bsudo\b",
        r"\bshutdown\b|\breboot\b|\bhalt\b|\bpoweroff\b",
        r"\bmkfs\b|\bdd\b\s+if=",
        r"\bgit\b\s+reset\s+--hard\b",
        r"\bgit\b\s+clean\b.*-f",
    ]
    if any(re.search(pat, cmd) for pat in always_blocked):
        return True

    if not allow_rm and re.search(r"\brm\b", cmd):
        return True
    if not allow_mv and re.search(r"\bmv\b", cmd):
        return True

    return False

def list_dir(path=".", show_hidden=True, **kwargs):
    """
    Lists files in a directory.
    Use this instead of run_command (ls/dir) for listing directory contents.

    Args:
        path: Directory path (default: ".")
        show_hidden: Whether to show hidden files (starting with .)
    """
    try:
        # Coerce LLM-supplied "false"/"true" string → real bool.
        show_hidden = _as_bool(show_hidden, default=True)
        path = _resolve_asset_path(path)
        if os.path.isfile(path):
            return f"'{path}' is a file, not a directory. Use read_file() or grep_file() instead."
        if not os.path.exists(path):
            return f"'{path}' does not exist. Use find_files() to locate the correct path."
        entries = os.listdir(path)
        if not show_hidden:
            entries = [e for e in entries if not e.startswith('.')]
        sorted_entries = sorted(entries)
        if not sorted_entries:
            return f"(empty directory: {path})"
        max_entries = _tool_cfg('TOOL_LIST_MAX_ENTRIES', 200)

        # Distinguish directories from files — add '/' suffix for dirs
        dir_count = 0
        file_count = 0
        lines = []
        for entry in sorted_entries:
            full = os.path.join(path, entry)
            if os.path.isdir(full):
                lines.append(entry + "/")
                dir_count += 1
            else:
                lines.append(entry)
                file_count += 1

        # Truncate if too many entries
        if len(lines) > max_entries:
            shown = lines[:max_entries]
            summary = f"... ({len(lines) - max_entries} more entries — increase TOOL_LIST_MAX_ENTRIES to see all)"
        else:
            shown = lines
            summary = ""

        # Build output with directory/file count summary
        result = "\n".join(shown)
        if summary:
            result += "\n" + summary
        result += f"\nTotal: {dir_count} directories, {file_count} files"
        return result
    except Exception as e:
        return f"Error listing directory: {e}"

def grep_file(pattern=None, path=None, context_lines=2, recursive=False, **kwargs):
    """
    Searches for a pattern using system tools (git grep/grep) for performance.
    Use this instead of run_command (grep/ripgrep/ag) for searching code.

    Args:
        pattern: Regex pattern to search for
        path: Path to file or directory
        context_lines: Number of context lines (default: 2)
        recursive: Whether to search recursively (default: False)
        **kwargs: Additional arguments (ignored, for robustness)

    Returns:
        Formatted matches string
    """
    if pattern is None:
        return "Error: grep_file() requires 'pattern'. Usage: grep_file(pattern=\"def foo\", path=\"src/\")"
    if path is None:
        return "Error: grep_file() requires 'path'. Usage: grep_file(pattern=\"def foo\", path=\"src/\")"
    # LLM may pass numeric / bool args as JSON strings — coerce.
    context_lines = _as_int(context_lines, default=2) or 2
    recursive = _as_bool(recursive, default=False)
    # Fall back to COMMON_AI_AGENT_HOME for bundled assets (templates,
    # rules, schemas) when the user's cwd doesn't have them. Skip if path
    # already contains glob meta — those are user-intended patterns.
    if any(c in str(path) for c in ('*', '?', '[')):
        path = _resolve_glob_path(path)
    else:
        path = _resolve_asset_path(path)
    import subprocess
    import sys
    
    # Python fallback implementation (for backup)
    def _grep_python(pat, pth, ctx, rec):
        import re
        import glob
        # Auto-enable recursive when target is a directory
        if os.path.isdir(pth) and not rec:
            rec = True
        try:
            is_glob = any(char in pth for char in ['*', '?', '[', ']'])
            if rec and not is_glob and os.path.isdir(pth):
                pth = os.path.join(pth, '**', '*')
                is_glob = True

            if is_glob or rec:
                files = glob.glob(pth, recursive=True)
                if not files: return f"No files found matching '{pth}'"

                _max_files = _tool_cfg('TOOL_GREP_MAX_FILES', 20)
                _total_files = len(files)
                results = []
                count = 0
                for f in sorted(files):
                    if os.path.isdir(f): continue
                    res = _grep_python(pat, f, ctx, False)
                    if not res.startswith("No matches") and not res.startswith("Error"):
                        results.append(f"=== Matches in {f} ===\n{res}\n")
                        count += 1
                        if count >= _max_files:
                            results.append(f"... (Stopped after {_max_files} files with matches — increase TOOL_GREP_MAX_FILES to see more)")
                            break
                if results and _total_files > 100:
                    results.append(f"(Searched {_total_files} files, showing first {_max_files} with matches)")
                return "\n".join(results) if results else f"No matches found for '{pat}'"

            # File search
            if not os.path.exists(pth): return f"Error: '{pth}' not found. Use find_files() to locate the correct path."
            if os.path.isdir(pth): return f"Error: '{pth}' is a dir"

            with open(pth, 'r', encoding='utf-8', errors='replace') as f:
                lines = f.readlines()

            matches = []
            try:
                regex = re.compile(pat)
            except Exception:
                # Invalid regex (e.g. unterminated '[') — fall back to literal string search
                regex = re.compile(re.escape(pat))
            for i, line in enumerate(lines, 1):
                if regex.search(line):
                    start = max(1, i - ctx)
                    end = min(len(lines), i + ctx)
                    block = []
                    for j in range(start, end + 1):
                        prefix = ">>> " if j == i else "    "
                        block.append(f"{prefix}{j:4d}: {lines[j-1].rstrip()}")
                    matches.append("\n".join(block))
            
            _max_m = _tool_cfg('TOOL_GREP_MAX_MATCHES', 50)
            truncated = len(matches) > _max_m
            shown = matches[:_max_m]
            result = f"Found {len(matches)} matches in {pth}:\n\n" + "\n...\n".join(shown) if shown else f"No matches found for '{pat}' in {pth}"
            if truncated:
                result += f"\n... ({len(matches) - _max_m} more matches hidden — increase TOOL_GREP_MAX_MATCHES to see all)"
            return result
            
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
        
        # Auto-enable recursive when target is a directory
        if os.path.isdir(path) and not recursive:
            recursive = True
            cmd.append("-r")
            cmd.extend(["--exclude-dir=.git", "--exclude-dir=__pycache__", "--exclude-dir=.venv", "--exclude-dir=venv"])
        
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
            
            # Uniform width — no >>> / spaces prefix.
            # Some UIs (atlas web, textual) post-process the >>> marker for
            # match lines only, which broke alignment between match and
            # context rows. Right-align the line number in a fixed column
            # so every row lines up regardless of UI handling.
            current_matches.append(f"{lineno:>5d}: {content}")

        dump_current()
        
        if not formatted_output:
             # Fallback if parsing failed drastically (e.g. filename only output)
             return f"Raw Grep Output:\n{output}"

        return "\n".join(formatted_output)

    except Exception as e:
        # Final fallback
        return _grep_python(pattern, path, context_lines, recursive)

def read_lines(path=None, start_line=None, end_line=None):
    """
    Reads a specific range of lines from a file.
    Args:
        path: Path to the file
        start_line: Starting line number (1-based, inclusive)
        end_line: Ending line number (1-based, inclusive)
    Returns:
        Content of the specified line range with line numbers
    """
    if not path:
        return "Error: read_lines() requires 'path'. Usage: read_lines(path=\"file.sv\", start_line=10, end_line=50)"
    if start_line is None:
        return "Error: read_lines() requires 'start_line'. Usage: read_lines(path=\"file.sv\", start_line=10, end_line=50)"
    try:
        # Coerce to int — LLM sometimes passes quoted numbers e.g. "260"
        # or a range string e.g. start_line="345-380"
        import re as _re
        _range_m = _re.match(r'^(\d+)\s*[-–]\s*(\d+)$', str(start_line).strip())
        if _range_m:
            # "345-380" passed as start_line — split into start/end
            start_line = int(_range_m.group(1))
            end_line   = int(_range_m.group(2))
        else:
            try:
                start_line = int(start_line)
                end_line   = int(end_line) if end_line is not None else start_line + 50
            except (TypeError, ValueError):
                return f"Error: start_line and end_line must be integers (got start_line={start_line!r}, end_line={end_line!r})"

        path = _resolve_asset_path(path)
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

        _log_file_access(path, "read")
        return result
    except Exception as e:
        return f"Error reading lines: {e}"

def find_files(pattern=None, directory=".", max_depth=None, path=None, recursive=True):
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
    if pattern is None:
        return "Error: find_files() requires 'pattern'. Usage: find_files(pattern=\"*.sv\", directory=\".\")"
    import fnmatch
    try:
        # LLM args arrive stringified — coerce numeric / bool params or
        # "false" silently passes the truthiness check and we recurse
        # anyway, and "3" passed to range() / int comparison crashes.
        recursive = _as_bool(recursive, default=True)
        max_depth = _as_int(max_depth, default=None)
        # Support 'path' as alias for 'directory'
        if path is not None:
            directory = path

        # Handle recursive parameter
        if not recursive:
            max_depth = 0

        # In an Atlas IP-bound worker, the user's visible "." is the active IP
        # root, not the served project collection. Keep non-dot paths on the
        # normal asset resolver so workflow/ and explicit ip/subdir paths retain
        # their existing behavior.
        directory = _active_ip_dot_search_root(directory) or _resolve_asset_path(directory)
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
            # Empty result. Do NOT walk the parent for "smart hints" —
            # that surfaces sibling matches and tricks the agent into
            # probing every empty subdir in a row. The agent should
            # consult list_dir / the SSOT instead.
            try:
                is_empty = os.path.isdir(directory) and not os.listdir(directory)
            except OSError:
                is_empty = False
            suffix = " (directory exists but is empty)" if is_empty else ""
            return f"No files matching '{pattern}' found in {directory}{suffix}"
        
        MAX_RESULTS = _tool_cfg('TOOL_FIND_MAX_RESULTS', 100)
        sorted_matches = sorted(matches)
        result = f"Found {len(matches)} file(s) matching '{pattern}':\n"
        result += "\n".join(f"  - {m}" for m in sorted_matches[:MAX_RESULTS])
        if len(matches) > MAX_RESULTS:
            result += f"\n  ... and {len(matches) - MAX_RESULTS} more files (increase TOOL_FIND_MAX_RESULTS or narrow the pattern)"
        return result
    except Exception as e:
        return f"Error finding files: {e}"

def _is_path_inside(child, parent):
    try:
        child_abs = os.path.abspath(child)
        parent_abs = os.path.abspath(parent)
        return os.path.commonpath([child_abs, parent_abs]) == parent_abs
    except (OSError, ValueError):
        return False


def _git_diff_target(path):
    cwd = _atlas_command_cwd_for("git diff")
    if not path:
        return cwd, None, ""

    resolved_path = _resolve_asset_path(path)
    if not os.path.exists(resolved_path):
        return cwd, None, f"Error: Path '{_normalize_tool_path(resolved_path)}' does not exist."

    abs_path = os.path.abspath(resolved_path)
    git_root = _find_git_root(abs_path)
    if git_root:
        cwd = git_root
    if cwd and _is_path_inside(abs_path, cwd):
        pathspec = os.path.relpath(abs_path, cwd).replace(os.sep, "/")
    else:
        pathspec = _normalize_tool_path(resolved_path)
    return cwd, pathspec, ""


def git_diff(path=None):
    """
    Shows git diff for unstaged changes.
    Args:
        path: Optional specific file path (default: all changes)
    Returns:
        Git diff output
    """
    try:
        cwd, pathspec, error = _git_diff_target(path)
        if error:
            return error

        cmd = ["git", "diff"]
        if pathspec:
            cmd += ["--", pathspec]

        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
            cwd=cwd
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
        cwd = _atlas_command_cwd_for("git status")
        result = subprocess.run(
            ["git", "status", "--short"],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            timeout=10,
            cwd=cwd
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
            encoding='utf-8',
            errors='replace',
            cwd=git_root
        )

        if result.returncode == 0:
            return f"Successfully reverted changes to '{path}' using git restore."

        # Fallback to git checkout
        result = subprocess.run(
            ['git', 'checkout', 'HEAD', '--', abs_path],
            capture_output=True,
            text=True,
            encoding='utf-8',
            errors='replace',
            cwd=git_root
        )
        
        if result.returncode == 0:
            return f"Successfully reverted changes to '{path}' using git checkout."
        else:
            return f"Error reverting file: {result.stderr}"
            
    except Exception as e:
        return f"Error reverting file: {e}"

def replace_in_file(path=None, old_text=None, new_text=None, count=-1, start_line=None, end_line=None, fuzzy_whitespace=True):
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
    if path is None:
        return "Error: replace_in_file() requires 'path'. Usage: replace_in_file(path=\"file.sv\", old_text=\"...\", new_text=\"...\")"
    if old_text is None:
        return "Error: replace_in_file() requires 'old_text'. Usage: replace_in_file(path=\"file.sv\", old_text=\"...\", new_text=\"...\")"
    if new_text is None:
        return "Error: replace_in_file() requires 'new_text'. Usage: replace_in_file(path=\"file.sv\", old_text=\"...\", new_text=\"...\")"
    try:
        path = _resolve_asset_path(path)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        locked_truth_error = _locked_truth_tool_write_error(path)
        if locked_truth_error is not None:
            return locked_truth_error

        # LLM tool-call args arrive as JSON strings. Coerce numeric
        # params to int so `str.replace(text, new, count)` (which
        # requires int) and the `count == -1` sentinel comparison
        # both work even when the model passes count="3" or
        # start_line="42" as strings. fuzzy_whitespace can arrive as
        # the JSON string "false" — coerce that to a real bool.
        #
        # Some models occasionally leak a code token into `count`
        # (e.g. count="begin\n"). In that case, treat it as default
        # behavior (`count=-1`, replace all) instead of hard-failing.
        invalid_count = None
        if count is None:
            count = -1
        elif isinstance(count, str):
            _count_raw = count.strip()
            if _count_raw == "" or _count_raw.lower() in ("all", "auto", "default", "none"):
                count = -1
            else:
                try:
                    count = int(_count_raw)
                except (ValueError, TypeError):
                    invalid_count = count
                    count = -1
        else:
            try:
                count = int(count)
            except (ValueError, TypeError):
                invalid_count = count
                count = -1
        if isinstance(fuzzy_whitespace, str):
            fuzzy_whitespace = fuzzy_whitespace.strip().lower() not in ("false", "0", "no", "off", "")

        with open(path, 'r', encoding='utf-8') as f:
            lines = f.readlines()

        # Determine working range
        start_idx = 0
        end_idx = len(lines)

        if start_line is not None:
            try:
                start_idx = max(0, int(start_line) - 1)
            except (ValueError, TypeError):
                return f"Error: replace_in_file() 'start_line' must be an integer (got {start_line!r})"
        if end_line is not None:
            try:
                end_idx = min(len(lines), int(end_line))
            except (ValueError, TypeError):
                return f"Error: replace_in_file() 'end_line' must be an integer (got {end_line!r})"
            
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
                    # Only accept unique matches to avoid wrong replacements
                    candidate_count = target_content.count(candidate)
                    if candidate_count == 1:
                        # Perfect: unique match found
                        matched_text = candidate
                        matched_strategy = strategy_name
                        break

                # If we found a unique match, stop searching strategies
                if matched_text:
                    break

            if matched_text:
                actual_old_text = matched_text
                occurrences = 1  # Unique match guaranteed by check above
        
        if occurrences == 0:
            range_msg = f" in lines {start_line}-{end_line}" if start_line is not None else ""
            # Show actual file content near the likely match location to help LLM retry
            file_preview = ""
            try:
                # Search for partial keywords from old_text in the actual file
                _keywords = [w for w in old_text.strip().split() if len(w) > 3][:5]
                _full_content = "".join(lines)
                _best_line = -1
                _best_score = 0
                for _li, _line in enumerate(lines):
                    _score = sum(1 for kw in _keywords if kw in _line)
                    if _score > _best_score:
                        _best_score = _score
                        _best_line = _li
                if _best_line >= 0 and _best_score >= 1:
                    _ctx = 8
                    _s = max(0, _best_line - _ctx)
                    _e = min(len(lines), _best_line + _ctx + 1)
                    file_preview = "\n".join(
                        f"  {i+1:4d}: {lines[i].rstrip()}" for i in range(_s, _e)
                    )
                    file_preview = f"\n\n📄 Closest match area (line {_s+1}-{_e}):\n{file_preview}\n"
            except Exception:
                pass

            hint = f"""

❌ Text not found in {path}{range_msg}

💡 RECOVERY: Read the file and copy EXACT text:
   Action: read_lines(path="{path}", start_line=<N>, end_line=<M>)
{file_preview}
Common issues: wrong indentation, tabs vs spaces, text doesn't exist (verify with grep_file).
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
            # Build per-line indent mapping from old_text → actual_old_text
            # Maps leading whitespace prefixes directly to preserve tabs/spaces
            old_lines = old_text.split('\n')
            actual_lines = actual_old_text.split('\n')

            if old_lines and actual_lines:
                # Build mapping: old_leading_ws → actual_leading_ws
                ws_map = {}
                for i in range(min(len(old_lines), len(actual_lines))):
                    ol = old_lines[i]
                    al = actual_lines[i]
                    if ol.strip() and al.strip():
                        old_ws = ol[:len(ol) - len(ol.lstrip())]
                        actual_ws = al[:len(al) - len(al.lstrip())]
                        ws_map[old_ws] = actual_ws

                if ws_map:
                    adjusted_lines = []
                    for nl in new_text.split('\n'):
                        if not nl.strip():
                            # Empty or whitespace-only line: preserve as-is
                            adjusted_lines.append(nl)
                            continue

                        nl_ws = nl[:len(nl) - len(nl.lstrip())]
                        nl_content = nl.lstrip()

                        # Look up target whitespace from mapping
                        if nl_ws in ws_map:
                            target_ws = ws_map[nl_ws]
                        else:
                            # Find closest matching indent level by character length
                            nl_depth = len(nl_ws)
                            best_ws = nl_ws
                            best_diff = float('inf')
                            for old_ws, act_ws in ws_map.items():
                                diff = abs(len(old_ws) - nl_depth)
                                if diff < best_diff:
                                    best_diff = diff
                                    best_ws = act_ws
                            # Scale the actual whitespace to match the depth difference
                            if best_ws and len(best_ws) > 0:
                                # Compute indent delta from the matched pair
                                matched_old = [k for k, v in ws_map.items() if v == best_ws]
                                if matched_old:
                                    delta = len(nl_ws) - len(matched_old[0])
                                    if delta > 0:
                                        # Deeper: extend with same char type
                                        char = best_ws[0]
                                        target_ws = best_ws + char * delta
                                    elif delta < 0:
                                        # Shallower: trim from end
                                        target_ws = best_ws[:max(0, len(best_ws) + delta)]
                                    else:
                                        target_ws = best_ws
                                else:
                                    target_ws = best_ws
                            else:
                                target_ws = nl_ws

                        adjusted_lines.append(target_ws + nl_content)
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

        # Write back (under cross-process IP lock — see write_file).
        _auto_chmod_if_needed(path)
        from core.worker_lock import with_ip_lock
        with with_ip_lock(path, label=f"replace_in_file:{os.path.basename(path)}"):
            with open(path, 'w', encoding='utf-8') as f:
                f.write(new_full_content)

        # Generate diff snippet AFTER writing (so we show final state)
        diff_output = format_diff_snippet(path, old_full_content, new_full_content, context_lines=3)

        result = f"Replaced {replacements} occurrence(s) in {path}\n"
        if invalid_count is not None:
            result += f"(Ignored invalid count={invalid_count!r}; using count=-1)\n"
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
        _log_file_access(path, "edit")
        return result
    except Exception as e:
        return f"Error replacing text: {e}"

# ============================================================================
# OpenCode-style Fuzzy Matching Strategies (9 Replacers)
# Ported from: opencode/packages/opencode/src/tool/edit.ts
# Original sources: Cline, Gemini CLI edit correctors
# ============================================================================

# Constants for BlockAnchorReplacer
SINGLE_CANDIDATE_SIMILARITY_THRESHOLD = 0.5
MULTIPLE_CANDIDATES_SIMILARITY_THRESHOLD = 0.6

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
    Handles escaped characters like \\n, \\t, \\"\\", etc.
    Uses placeholder for \\\\ to prevent double-processing (\\\\\\\\" → \\\\").
    Single pass only — multi-pass would over-unescape.
    """
    def unescape_string(s):
        """Unescape common escape sequences. Single pass with placeholder."""
        # CRITICAL: Process \\\\ FIRST via placeholder, then single-char escapes.
        # This ensures \\\\\\" becomes \\" (not \\") and \\" becomes ".
        replacements = [
            ('\\\\', '\x00BACKSLASH\x00'),  # Placeholder prevents double-processing
            ('\\n', '\n'),
            ('\\t', '\t'),
            ('\\r', '\r'),
            ("\\'", "'"),
            ('\\"', '"'),
            ('\\`', '`'),
            ('\\$', '$'),
        ]
        result = s
        for escaped, unescaped in replacements:
            result = result.replace(escaped, unescaped)
        # Restore backslash placeholder → real backslash
        result = result.replace('\x00BACKSLASH\x00', '\\')
        return result

    unescaped_find = unescape_string(find)

    # Try direct match with unescaped
    if unescaped_find in content:
        yield unescaped_find

    # Try finding escaped versions in content
    lines = content.split('\n')
    find_lines = unescaped_find.split('\n')

    for i in range(len(lines) - len(find_lines) + 1):
        block = '\\n'.join(lines[i:i + len(find_lines)])
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




def _punctuation_aware_replacer(content, find):
    # Strategy 8: Punctuation-aware matching.
    # Removes whitespace adjacent to punctuation chars ()[]{};,. before comparing.
    # Handles cases like: foo( "bar" ); -> foo("bar");
    # NOTE: Currently disabled (not in strategy loop) due to potential false positives.
    import re

    def strip_punct_ws(text):
        # Remove spaces before: ) ] } ; , .
        result = re.sub(r'\s+([)\]};,.])', r'\1', text)
        # Remove spaces after: ( [ {
        result = re.sub(r'([(\[{])\s+', r'\1', result)
        return result

    normalized_find = strip_punct_ws(find)

    # Try single-line matches
    lines = content.split('\n')
    for i, line in enumerate(lines):
        if strip_punct_ws(line) == normalized_find:
            yield line

    # Try multi-line block matches
    find_lines = find.split('\n')
    if len(find_lines) > 1:
        for i in range(len(lines) - len(find_lines) + 1):
            block = lines[i:i + len(find_lines)]
            if strip_punct_ws('\n'.join(block)) == normalized_find:
                yield '\n'.join(block)

def _context_aware_replacer(content, find):
    """
    Strategy 9: Context-aware matching.
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
                # Only break if block size matched (whether similarity passed or not)
                # Otherwise continue looking for another matching last line
                if len(block_lines) == len(find_lines):
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

def replace_lines(path=None, start_line=None, end_line=None, new_content=None):
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
    if path is None:
        return "Error: replace_lines() requires 'path'. Usage: replace_lines(path=\"file.sv\", start_line=10, end_line=20, new_content=\"...\")"
    if start_line is None or end_line is None:
        return "Error: replace_lines() requires 'start_line' and 'end_line'. Usage: replace_lines(path=\"file.sv\", start_line=10, end_line=20, new_content=\"...\")"
    if new_content is None:
        return "Error: replace_lines() requires 'new_content'. Usage: replace_lines(path=\"file.sv\", start_line=10, end_line=20, new_content=\"...\")"
    try:
        # Coerce to int — LLM sometimes passes quoted numbers e.g. "260"
        try:
            start_line = int(start_line)
            end_line = int(end_line)
        except (TypeError, ValueError):
            return f"Error: start_line and end_line must be integers (got start_line={start_line!r}, end_line={end_line!r})"

        path = _resolve_asset_path(path)
        if not os.path.exists(path):
            return f"Error: File '{path}' does not exist."
        locked_truth_error = _locked_truth_tool_write_error(path)
        if locked_truth_error is not None:
            return locked_truth_error

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
        _auto_chmod_if_needed(path)
        with open(path, 'w', encoding='utf-8') as f:
            f.writelines(new_lines)

        # Generate diff snippet AFTER writing (shows final state)
        diff_output = format_diff_snippet(path, old_content, new_content_full, context_lines=3)

        lines_removed = end_line - start_line + 1
        result = f"Replaced lines {start_line}-{end_line} ({lines_removed} lines) in {path}\n"
        result += f"\n{diff_output}"
        
        added = len(new_content.splitlines())
        old_snippet = "".join(lines[start_line-1:end_line])[:400]
        hint = f"--- old ---\n{old_snippet}\n--- new ---\n{new_content[:400]}"
        import threading as _t
        _t.Thread(target=_git_auto_commit, args=(path, "replace_lines"), kwargs={"stats": f"+{added}/-{lines_removed} lines", "content_hint": hint}, daemon=False).start()

        _log_file_access(path, "edit")
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
        _set_todo_tracker_error("")
        from lib.todo_tracker import TodoTracker
        import config as _cfg

        override_tracker = getattr(_TODO_RUNTIME, "todo_tracker", None)
        override_file = getattr(_TODO_RUNTIME, "todo_file", None)
        desired_path = Path(override_file or getattr(_cfg, "TODO_FILE", "current_todos.json"))
        strict_load = (
            override_file is not None
            or ".session" in desired_path.parts
            or os.environ.get("TODO_TEMPLATE_LOCK_ADDITIONS", "").strip().lower()
            in ("1", "true", "yes", "on")
        )

        modules = [
            sys.modules.get("main"),
            sys.modules.get("src.main"),
            sys.modules.get("__main__"),
        ]
        modules = [m for m in modules if m is not None and hasattr(m, "todo_tracker")]

        if override_tracker is not None:
            if override_file is None or _paths_match(getattr(override_tracker, "_persist_path", None), desired_path):
                for module in modules:
                    module.todo_tracker = override_tracker
                return override_tracker

        for module in modules:
            tracker = getattr(module, "todo_tracker", None)
            if tracker is not None and _paths_match(getattr(tracker, "_persist_path", None), desired_path):
                # Cross-process freshness: the Atlas server (a different process)
                # may have rewritten this session todo.json — slash template load,
                # auto-start seed, /api/todos edit — after this worker cached the
                # tracker at boot. Re-read when the file changed instead of serving
                # the stale (often empty) in-memory copy. This is the root of the
                # "No active todo list" while the file clearly exists on disk bug.
                if hasattr(tracker, "is_stale_vs_disk") and tracker.is_stale_vs_disk():
                    # Re-read INTO the cached object (preserve identity so
                    # react_loop's held reference and the module global stay in
                    # sync) instead of orphaning it with a fresh load.
                    tracker.reload_from_disk()
                return tracker

        tracker = TodoTracker.load(desired_path, strict=strict_load)
        if modules:
            for module in modules:
                module.todo_tracker = tracker
        else:
            try:
                import src.main as main_module
            except Exception:
                try:
                    import main as main_module
                except Exception:
                    main_module = None
            if main_module is not None:
                main_module.todo_tracker = tracker
        return tracker
    except (ImportError, OSError, ValueError, AttributeError) as exc:
        _set_todo_tracker_error(f"TodoTracker load failed: {exc}")
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


def _todo_template_lock_error(op_name: str) -> str:
    """Return an error when a canonical template disallows todo reshaping."""
    locked = os.environ.get("TODO_TEMPLATE_LOCK_ADDITIONS", "").strip().lower()
    tmpl = os.environ.get("TODO_TEMPLATE_LOCK_NAME", "").strip()
    is_locked = locked in ("1", "true", "yes", "on")
    if not is_locked:
        try:
            import config as _cfg
            from lib.todo_tracker import TodoTracker

            tracker = TodoTracker.load(Path(getattr(_cfg, "TODO_FILE", "current_todos.json")))
            is_locked = bool(getattr(tracker, "template_lock_additions", False))
            tmpl = tmpl or str(getattr(tracker, "template_name", "") or "")
        except Exception:
            is_locked = False
    if not is_locked:
        return ""
    tmpl = tmpl or "active"
    return (
        f"Error: todo template '{tmpl}' is locked; do not call {op_name} "
        "to add or replace tasks. Use the existing canonical tasks, repair "
        "inside the relevant task, or emit the workflow escalation requested "
        "by the template."
    )


def _trace_todo_tool_event(index: int, item, status: str, reason: str = "", note_text: str = "") -> None:
    """Best-effort mirror of todo tool transitions into Atlas trace storage."""
    try:
        from core.atlas_trace import record_todo_tool_event_from_env

        record_todo_tool_event_from_env(
            index,
            item,
            status,
            reason=reason or "",
            note_text=note_text or "",
        )
    except Exception:
        pass


def todo_write(todos=None, tasks=None, **kwargs):
    """
    Create or update task list to track multi-step task progress.

    Args:
        todos (list): List of task dicts or strings.
        tasks (list): Alias for todos (some agents use this name).

    Task fields:
        content (str):      Task description (required).
        activeForm (str):   Display text while in progress.
        status (str):       "pending" | "in_progress" | "approved" | "rejected"
        priority (str):     "high" | "medium" | "low"
        detail (str):       Implementation guidance for the LLM.
        criteria (str):     Newline-separated acceptance criteria.
        command (str|dict): Run WITHOUT LLM — shell string or tool-call dict.
                            Success → auto-approved. Failure → auto-rejected.
                            str:  "make lint", "verilator --lint-only rtl/*.sv"
                            dict: {"tool": "run_command", "args": {"command": "make sim"}}
        on_reject (int):    1-based task index to jump to when command fails.
                            Enables retry loops: failed task jumps back to impl task.
        on_success (int):   1-based task index to jump to when command succeeds.
                            0 = next sequential task. Enables skip-ahead flows.
        on_condition (list): Conditional branching — [{"if": "pattern", "goto": N}, ...].
                            Pattern matched against command output via regex. First match wins.
                            Overrides on_success/on_reject when matched.

    Static command pipeline example (LLM implements → static checks → LLM reviews):
        todo_write([
            {"content": "Implemented RTL module",
             "activeForm": "Implementing RTL module",
             "agent": "execute"},
            {"content": "Ran lint check",
             "activeForm": "Running lint check",
             "command": "verilator --lint-only rtl/*.sv 2>&1",
             "on_reject": 1},
            {"content": "Ran simulation",
             "activeForm": "Running simulation",
             "command": "make sim",
             "on_reject": 1},
            {"content": "Reviewed results",
             "activeForm": "Reviewing results"},
        ])

    Skip-ahead example (quick check passes → skip full check):
        todo_write([
            {"content": "Implemented feature",
             "activeForm": "Implementing feature"},
            {"content": "Ran quick lint",
             "activeForm": "Running quick lint",
             "command": "make quick-lint",
             "on_success": 4},
            {"content": "Ran full lint",
             "activeForm": "Running full lint",
             "command": "make full-lint",
             "on_reject": 1},
            {"content": "Ran simulation",
             "activeForm": "Running simulation",
             "command": "make sim"},
        ])

    Basic example:
        todo_write([
            {"content": "Analyze code", "activeForm": "Analyzing code", "status": "in_progress"},
            {"content": "Write tests", "activeForm": "Writing tests", "status": "pending"}
        ])
    """
    # Accept either parameter name. LLMs (especially gpt-5.x-codex)
    # sometimes emit the list under non-standard keys like `items`,
    # `list`, `todo_list`, `task_list`, `data`. Without this fallback
    # the call fails with "'todos' parameter is required" and the LLM
    # gets stuck in a retry loop emitting the same wrong key.
    todos = todos or tasks
    if not todos and kwargs:
        for _alias in ("items", "list", "todo_list", "task_list",
                       "tasks_list", "data", "body", "payload", "entries"):
            _v = kwargs.get(_alias)
            if _v:
                todos = _v
                break
        if not todos:
            # Last-resort: if exactly one kwarg holds a non-empty list,
            # treat it as the todos list.
            _list_kwargs = [v for v in kwargs.values() if isinstance(v, list) and v]
            if len(_list_kwargs) == 1:
                todos = _list_kwargs[0]
    _locked = _todo_template_lock_error("todo_write")
    if _locked:
        _save_todo_write_error(_locked, todos)
        return _locked

    # Import here to avoid circular dependency
    from typing import List, Dict

    todo_tracker = _get_todo_tracker()
    if todo_tracker is None:
        # Return an explicit error instead of silently succeeding with "".
        # The previous empty string made the LLM believe todo_write succeeded
        # when in fact nothing was written — same UX bug class as the
        # streaming-truncation silent drop.
        err = ("Error: TodoTracker is not initialized (main.todo_tracker is None "
               "and config.TODO_FILE could not be loaded). Check that "
               "ENABLE_TODO_TRACKING=true and that config.TODO_FILE points to a "
               "writable path.")
        _save_todo_write_error(err, todos)
        return err

    # Validate input
    if not todos:
        err = "Error: 'todos' parameter is required and must be a non-empty list"
        _save_todo_write_error(err, todos)
        return err

    if not isinstance(todos, list):
        # Try to recover: JSON string passed instead of list
        if isinstance(todos, str):
            try:
                import json as _json
                _parsed = _json.loads(todos)
                if isinstance(_parsed, list):
                    todos = _parsed
                elif isinstance(_parsed, dict) and "todos" in _parsed:
                    todos = _parsed["todos"]
                else:
                    return f"Error: 'todos' must be a list, got str. Usage: todo_write(todos=[{{\"content\": \"...\"}}, ...])"
            except Exception:
                return f"Error: 'todos' must be a list, got str. Usage: todo_write(todos=[{{\"content\": \"...\"}}, ...])"
        else:
            return f"Error: 'todos' must be a list, got {type(todos).__name__}"

    # Auto-convert string items to dict format. Backward-compat path:
    # legacy callers pass plain strings instead of full task dicts.
    # Seed detail/criteria with the content itself so the new
    # detail/criteria empty-rejection check below doesn't reject the
    # promoted item — the LLM is still encouraged to use the proper
    # dict form for new code, but old call sites keep working.
    from lib.todo_tracker import _generate_active_form
    for i, todo in enumerate(todos):
        if isinstance(todo, str):
            todos[i] = {
                "content":    todo,
                "activeForm": _generate_active_form(todo),
                "status":     "pending",
                "detail":     todo,
                "criteria":   todo,
            }

    # Plan mode anti-loop: cap todo_write calls to prevent repeated planning
    is_plan = os.environ.get("PLAN_MODE", "false").lower() == "true"
    if is_plan:
        _plan_write_count = int(os.environ.get("_PLAN_TODO_WRITE_COUNT", "0")) + 1
        os.environ["_PLAN_TODO_WRITE_COUNT"] = str(_plan_write_count)
        _plan_write_max = int(os.environ.get("PLAN_TODO_WRITE_MAX", "10"))
        if _plan_write_count > _plan_write_max:
            return (
                f"⚠️ Plan mode todo_write limit reached (max {_plan_write_max} calls).\n"
                "Your task list is ready. STOP calling todo_write and WAIT for user confirmation.\n"
                "The user will confirm with 'y' to execute or provide feedback."
            )

    # Validate each todo structure
    for i, todo in enumerate(todos):
        if not isinstance(todo, dict):
            return f"Error: todos[{i}] must be a dictionary, got {type(todo).__name__}"

        if "content" not in todo:
            return f"Error: todos[{i}] missing required key 'content'"

        # Auto-generate activeForm if missing
        if "activeForm" not in todo:
            todo["activeForm"] = _generate_active_form(todo["content"])

        if "status" not in todo:
            todo["status"] = "pending"

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
        if is_plan:
            todo["status"], todo["completed_at"] = "pending", None

        # Enforce the schema's "detail/criteria must be filled in" claim.
        # Until now this was advertised in the tool description but never
        # validated, so tasks landed with empty implementation guidance and
        # the LLM had no concrete plan to follow when it picked them up.
        for required_field in ("detail", "criteria"):
            val = todo.get(required_field, "")
            if not isinstance(val, str) or not val.strip():
                err = (f"Error: todos[{i}] ('{todo.get('content', '')[:60]}') has empty "
                       f"'{required_field}'. Every task MUST fill in detail (HOW to "
                       f"implement) and criteria (acceptance checklist). "
                       f"Skipping these defeats the point of the task list.")
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
    for _idx, _item in enumerate(todo_tracker.todos, 1):
        _trace_todo_tool_event(_idx, _item, getattr(_item, "status", "pending") or "pending", reason="todo_write")

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
        progress = todo_tracker.format_simple()
        return f"✅ Todo list created:\n{progress}"
    except Exception as e:
        return f"Error formatting progress: {e}"


def todo_update(index=None, id=None, status=None, reason="", content="", detail="", activeForm="", criteria="",
                command=None, on_reject=None, on_success=None, on_condition=None):
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
        command (str|dict): Shell command or tool call to set/update on this task.
        on_reject (int): 1-based task index to jump to on command failure (0=disabled).
        on_success (int): 1-based task index to jump to on command success (0=next sequential).
        on_condition (list): Conditional branching — [{"if": "pattern", "goto": N}, ...].
                             Overrides on_success/on_reject when matched.

    Example:
        todo_update(index=1, status="completed")
        todo_update(index=2, content="Updated task description")
        todo_update(index=3, status="pending", reason="Tests still failing")
        todo_update(index=4, command="make lint", on_reject=2)
        todo_update(index=5, on_success=7)
        todo_update(index=6, on_condition=[{"if": "TIMEOUT", "goto": 3}])
    """
    todo_tracker = _get_todo_tracker()

    if todo_tracker is None:
        return _todo_tracker_unavailable_error()
    if not todo_tracker.todos:
        return "Error: No active todo list."

    if index is None:
        index = id

    if index is None:
        return "Error: 'index' (1-based) is required. (Note: use 1-based indexing, not 0-based)."

    # 0-based recovery: if index=0 or results in -1, try to find current in_progress task
    try:
        _raw_idx = int(str(index).strip())
    except (ValueError, TypeError):
        _raw_idx = None

    if _raw_idx is not None and _raw_idx <= 0:
        # Find current in_progress task as the likely intended target
        _in_progress = [i for i, t in enumerate(todo_tracker.todos) if getattr(t, 'status', '') == 'in_progress']
        if _in_progress:
            index = _in_progress[0] + 1  # convert back to 1-based
        elif _raw_idx == 0:
            index = 1  # fallback: assume first task

    # Plan mode: block status changes, allow content/detail/criteria updates
    if status and os.environ.get("PLAN_MODE") == "true":
        return "Error: Changing status is blocked in plan mode. You can update content, detail, criteria, or priority."

    # Convert to 0-based
    try:
        idx = int(index) - 1
    except ValueError:
        return f"Error: index must be an integer, got '{index}'"

    if not (0 <= idx < len(todo_tracker.todos)):
        return f"Error: index {index} out of range (1-{len(todo_tracker.todos)})"

    item = todo_tracker.todos[idx]

    # Update content fields if provided.
    # IMPORTANT: detail and criteria should describe the TASK (what to do / how to verify).
    # They should NOT be overwritten during approval/completion — use 'reason' for that.
    _is_review_status = status in ("approved", "completed", "rejected")
    if content:
        item.content = content
        if not activeForm:
            from lib.todo_tracker import _generate_active_form
            item.active_form = _generate_active_form(content)
    if activeForm:
        item.active_form = activeForm
    if detail and not _is_review_status:
        # Only update detail for actionable statuses (pending/in_progress),
        # not during review (approved/completed/rejected) where the LLM
        # tends to pass approval notes as detail.
        item.detail = detail
    if criteria and not _is_review_status:
        # Same protection for criteria — don't lose original criteria during review.
        item.criteria = criteria
    if command is not None:
        item.command = command
    if on_reject is not None:
        item.on_reject = int(on_reject)
    if on_success is not None:
        item.on_success = int(on_success)
    if on_condition is not None:
        item.on_condition = on_condition if on_condition else None

    # Guard: status=None with no other field means LLM passed null — surface a clear error
    if status is None and not any([content, detail, activeForm, criteria, command is not None, on_reject is not None, on_success is not None, on_condition is not None]):
        return (
            f"Error: Nothing to update for Task {index}. "
            f"Provide at least one of: status ('in_progress'/'completed'/'approved'/'rejected'/'pending'), "
            f"content, detail, activeForm, or criteria."
        )

    # Update status if provided
    if status is not None and str(status).strip():
        status = str(status).strip()
        # Normalize common aliases and run the shared transition gate used by
        # Atlas web/UI as well. The prose/trace/git side effects below remain
        # local to this LLM tool wrapper.
        from lib.todo_transition import normalize_todo_status, validate_todo_status_transition
        valid = ["pending", "in_progress", "completed", "approved", "rejected"]
        if status not in valid:
            status = normalize_todo_status(status)
        if status not in valid:
            return f"Error: status must be one of {valid} (got '{status}')"
        import src.config as _cfg
        _cursor_mode = getattr(_cfg, "CURSOR_AGENT_ENABLE", False)
        _transition_check = validate_todo_status_transition(
            todo_tracker,
            idx,
            status,
            reason=reason,
            plan_mode=False,
            cursor_mode=_cursor_mode,
        )
        if not _transition_check.ok:
            return _transition_check.message

        # Enforce sequential execution: all prior tasks must be approved.
        # Skipped in cursor-agent mode — cursor-agent makes its own approval judgment
        # via text output; the approval event arrives after the next task's tool calls.
        #
        # Exception: rejected tasks with forward on_reject are NOT blocking.
        # When Task N has on_reject=M (M>N) and fails, the flow jumps to Task M.
        # Task M should be allowed to complete even though Task N is rejected,
        # because Task N's failure is "handled" by the on_reject jump path.
        if not _cursor_mode and status in ("in_progress", "completed", "approved"):
            blocking = [
                i + 1 for i in range(idx)
                if todo_tracker.todos[i].status not in ("approved",)
                # Skip rejected tasks that have a forward on_reject —
                # their failure is handled by jumping to the reject target.
                and not (
                    todo_tracker.todos[i].status == "rejected"
                    and getattr(todo_tracker.todos[i], 'on_reject', 0) > (i + 1)
                )
            ]
            if blocking:
                blocking_str = ", ".join(str(b) for b in blocking)
                # Auto-correct current_index to point at the first blocking task,
                # so get_continuation_prompt() generates the correct redirect.
                first_blocking_idx = blocking[0] - 1  # 0-based
                if todo_tracker.current_index != first_blocking_idx:
                    todo_tracker.current_index = first_blocking_idx
                    todo_tracker.save()
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

        # Protection: completed task must be reviewed (approved/rejected), not reset to in_progress
        if item.status == "completed" and status == "in_progress":
            return (
                f"Status Conflict: Task {index} is already 'completed' and awaiting review.\n"
                f"→ Approve: todo_update(index={index}, status='approved', reason='<evidence>')\n"
                f"→ Reject:  todo_update(index={index}, status='rejected', reason='<problem>')\n"
                "Do NOT reset to 'in_progress' without going through review."
            )

        # Enforce state machine: must go through 'completed' before 'approved'
        if status == "approved" and item.status not in ("completed", "approved"):
            return (
                f"Error: Task {index} is currently '{item.status}'. "
                f"You must call todo_update(index={index}, status='completed') first, "
                f"then review, then call todo_update(index={index}, status='approved')."
            )

        if status == "approved":
            _reason_stripped = (reason or "").strip()
            if not _reason_stripped:
                return (
                    f"Error: You MUST provide a concrete 'reason' when approving Task {index}.\n"
                    f"Describe what you actually verified — e.g. 'read output.md: contains all sections, matches spec' "
                    f"or 'ran pytest tests/foo.py — 14 passed, 0 failed'.\n"
                    f"→ todo_update(index={index}, status='approved', reason='<specific evidence>')"
                )
            # Review-gate: must have called at least one non-write evidence tool
            # since the task transitioned to "completed". Prevents the agent from
            # approving based on its own self-written summary file (sim_report.txt
            # etc.) — common false-approval pattern observed in tb-gen sessions
            # where the agent's report was stale/wrong but it approved anyway.
            # Counter is incremented in react_loop for both native and non-native
            # tool-call modes when current task is in review (status=completed)
            # and the tool isn't a write or todo tool.
            #
            # Escalation (Option F): tasks already rejected ≥2 times have shown
            # they're prone to bouncing — agent's review judgment is unreliable.
            # Require ≥2 evidence calls instead of ≥1 to break the livelock.
            # All approval guards below are opt-in via STRICT_TODO_APPROVAL=1.
            # Default OFF: trust the LLM's own verification (it reads the
            # rule files telling it to grep / re-read / run lint). The
            # strict variants were producing too many false rejections
            # when active-IP context didn't propagate to worker subprocesses.
            import os as _os_strict
            _strict = _os_strict.environ.get("STRICT_TODO_APPROVAL", "").lower() in ("1", "true", "yes", "on")
            if _strict:
                _evidence = int(getattr(item, "tools_since_completed", 0) or 0)
                _rej_count = int(getattr(item, "rejection_count", 0) or 0)
                _required = 2 if _rej_count >= 2 else 1
                if item.status == "completed" and _evidence < _required:
                    _esc = (
                        f"\n⚠ Escalated requirement: this task has been rejected "
                        f"{_rej_count} times — needs ≥{_required} verification calls."
                    ) if _rej_count >= 2 else ""
                    return (
                        f"Approval blocked: Task {index} has only {_evidence} verification tool call(s) "
                        f"since review started (need ≥{_required}).{_esc}\n"
                        f"Self-written summary/report files are NOT trustworthy evidence. You must\n"
                        f"verify against ground-truth artifacts.\n"
                        f"→ Re-read the actual source file(s) you produced (read_file / read_lines)\n"
                        f"→ OR run the test/build directly (run_command) and check the output\n"
                        f"→ OR grep for what should be there (grep_file / find_files)\n"
                        f"Then call todo_update(index={index}, status='approved', reason='<evidence with file:line>') again."
                    )
                if len(_reason_stripped) < 15:
                    return (
                        f"Error: You MUST provide a concrete 'reason' (≥15 chars) when approving Task {index}.\n"
                        f"Describe what you actually verified — e.g. 'read output.md: contains all 9 sections, matches spec' "
                        f"or 'ran pytest tests/foo.py — 14 passed, 0 failed'.\n"
                        f"Rejected reasons: empty, 'ok', 'done', 'looks good', 'approved' — these are not evidence.\n"
                        f"→ todo_update(index={index}, status='approved', reason='<specific evidence>')"
                    )
                _low = _reason_stripped.lower()
                _banned = {"ok", "okay", "done", "good", "fine", "lgtm", "approved",
                           "looks good", "all good", "seems ok", "seems good",
                           "no issues", "no problems", "complete", "completed"}
                if _low in _banned:
                    return (
                        f"Error: '{reason}' is not concrete evidence for Task {index}.\n"
                        f"Provide what you actually verified (files read, commands run, outputs checked).\n"
                        f"→ todo_update(index={index}, status='approved', reason='<what you checked, with specifics>')"
                    )

            # ── File-existence ground-truth check ──────────────────────────
            # The evidence/reason gates above are STRUCTURAL — they don't
            # verify that claimed deliverables actually exist on disk.
            # Common failure: agent writes a long convincing reason like
            # "Verified tc_uart.sv:47 contains all 17 tests" without ever
            # calling write_file. The tracker would let that through.
            #
            # This check scans the task content + criteria + detail for
            # file-path-like tokens (with hardware/sw extensions). Any
            # token that resolves to an absolute or relative path with
            # size < min_bytes blocks approval until the file is real.
            try:
                import re as _re
                import os as _os_fs
                _scan_text = " ".join([
                    str(item.content or ""),
                    str(getattr(item, "criteria", "") or ""),
                    str(getattr(item, "detail", "") or ""),
                ])
                # Match file paths ending in synthesizable / verification /
                # toolchain extensions. Greedy enough to catch nested paths
                # like "uart/rtl/uart_wrapper.v" but not URLs or domain names.
                _path_re = _re.compile(
                    r'(?<![/\w.-])'
                    r'((?:[\w.-]+/)+[\w.-]+\.'
                    r'(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|lib|lef|gds|spef|sdf|vcd|out|netlist))'
                    r'(?![\w/.-])'
                )
                _candidates = set(_path_re.findall(_scan_text))
                # Skip generic <ip> placeholders — content templates often
                # carry "<ip>/rtl/<ip>.sv" style examples that aren't real
                # deliverables for THIS task.
                _candidates = {p for p in _candidates if "<" not in p and ">" not in p}
                _cwd = _os_fs.getcwd()
                _known_artifact_dirs = {
                    "rtl", "list", "tb", "tc", "sim", "cov", "lint", "doc",
                    "req", "model", "verify", "yaml", "syn", "sta", "pnr",
                    "scripts",
                }
                _base_dirs = [_cwd]
                # Always also try `<cwd>/<active-ip>/` as a base dir so
                # the agent can declare `rtl/<ip>_wrapper.sv` (relative
                # to the IP root) without the validator rejecting it
                # because the file actually lives under
                # `<cwd>/<ip>/rtl/<ip>_wrapper.sv`. Without this, every
                # IP-rooted task declared a path the validator couldn't
                # resolve, producing the "Cannot approve … fake-DONE"
                # banner even when the file genuinely existed.
                # Prefer the per-thread contextvar (atlas_ui mode). Falls
                # back to env when main.py hasn't been wired or in CLI mode.
                _main_mod = sys.modules.get('main')
                _ip_resolver = getattr(_main_mod, "_get_active_ip_str", None) if _main_mod else None
                _active_ip = (_ip_resolver() if _ip_resolver
                              else _os_fs.environ.get("ATLAS_ACTIVE_IP") or "").strip()
                if _active_ip and _re.match(r"^[A-Za-z][A-Za-z0-9_-]*$", _active_ip):
                    _ip_base = _os_fs.path.join(_cwd, _active_ip)
                    if _ip_base not in _base_dirs and _os_fs.path.isdir(_ip_base):
                        _base_dirs.append(_ip_base)
                for _p in _candidates:
                    _parts = [part for part in _p.split("/") if part]
                    for _idx, _part in enumerate(_parts):
                        if _part in _known_artifact_dirs and _idx > 0:
                            _base = _os_fs.path.join(_cwd, *_parts[:_idx])
                            if _base not in _base_dirs:
                                _base_dirs.append(_base)
                            break

                _MIN_BYTES = 50  # filter out 1-2 line stubs; most real deliverables are larger

                def _resolve_existing(_p):
                    _tries = []
                    if _os_fs.path.isabs(_p):
                        _tries.append(_p)
                    else:
                        _tries.append(_os_fs.path.join(_cwd, _p))
                        for _base in _base_dirs:
                            _tries.append(_os_fs.path.join(_base, _p))
                    for _full in _tries:
                        if _os_fs.path.isfile(_full):
                            return _full
                    # Final fallback when active-IP/contextvar resolution
                    # didn't kick in (e.g. process-per-session worker that
                    # never received ATLAS_ACTIVE_IP in its spawn env): scan
                    # immediate cwd subdirs for `<sub>/<_p>`. Accept iff
                    # exactly one subdir contains the file. The original
                    # bug: gpio task declared `rtl/gpio_param.vh`, actual
                    # file lived at `gpio/rtl/gpio_param.vh`, validator
                    # rejected with "fake-DONE" because no _base_dir had
                    # been seeded for the gpio IP.
                    if not _os_fs.path.isabs(_p):
                        _skip = {".git", ".session", ".rag", ".venv", "__pycache__",
                                 ".sisyphus", ".omc", "node_modules", "build"}
                        _hits = []
                        try:
                            for _name in _os_fs.listdir(_cwd):
                                if _name.startswith(".") or _name in _skip:
                                    continue
                                _sub = _os_fs.path.join(_cwd, _name)
                                if not _os_fs.path.isdir(_sub):
                                    continue
                                _candidate = _os_fs.path.join(_sub, _p)
                                if _os_fs.path.isfile(_candidate):
                                    _hits.append(_candidate)
                        except OSError:
                            return None
                        if len(_hits) == 1:
                            return _hits[0]
                    return None

                def _filelist_entries_exist(_full):
                    _root = _os_fs.path.dirname(_os_fs.path.dirname(_full))
                    try:
                        _lines = open(_full, encoding="utf-8", errors="replace").read().splitlines()
                    except OSError:
                        return False
                    _entries = []
                    for _raw in _lines:
                        _line = _raw.strip()
                        if not _line or _line.startswith("#"):
                            continue
                        if _line.startswith(("+incdir+", "-I", "-y", "+define+")):
                            continue
                        _entries.append(_line)
                    if not _entries:
                        return False
                    for _entry in _entries:
                        if not _re.search(r"\.(?:sv|v|vh|svh)$", _entry):
                            continue
                        _entry_tries = [
                            _entry if _os_fs.path.isabs(_entry) else _os_fs.path.join(_root, _entry),
                            _entry if _os_fs.path.isabs(_entry) else _os_fs.path.join(_cwd, _entry),
                        ]
                        if not any(_os_fs.path.isfile(_candidate) for _candidate in _entry_tries):
                            return False
                    return True

                def _artifact_is_real(_full):
                    try:
                        _size = _os_fs.path.getsize(_full)
                    except OSError:
                        return False
                    _ext = _os_fs.path.splitext(_full)[1].lower()
                    if _ext == ".f":
                        return _filelist_entries_exist(_full)
                    if _ext in {".sdc", ".upf", ".tcl"}:
                        return _size > 0
                    return _size >= _MIN_BYTES

                # The strict path-existence block used to refuse approval
                # whenever a task description mentioned `rtl/<ip>.sv` but
                # the validator couldn't resolve the path (e.g. worker
                # subprocess didn't get ATLAS_ACTIVE_IP, so `gpio/rtl/
                # gpio_reg.sv` looked like just `rtl/gpio_reg.sv` and got
                # rejected as "fake-DONE"). Per user direction we trust
                # the LLM's own verification (grep / run_command / read_file)
                # plus the existing evidence-tool-count gate above — opt
                # into the strict block only via env STRICT_DELIVERABLE_CHECK=1.
                if _os_fs.environ.get("STRICT_DELIVERABLE_CHECK", "").lower() in ("1", "true", "yes", "on"):
                    _missing = []
                    for _p in _candidates:
                        _resolved = _resolve_existing(_p)
                        if _resolved is None or not _artifact_is_real(_resolved):
                            _missing.append(_p)
                    if _missing:
                        return (
                            f"Approval blocked: Task {index} declared deliverable(s) missing or too small on disk:\n"
                            + "\n".join(f"  • {p}" for p in _missing[:8])
                            + (f"\n  • … (+{len(_missing) - 8} more)" if len(_missing) > 8 else "")
                            + f"\nThe task content references these files but no `write_file` or `run_command` "
                            f"actually produced them (or they are < {_MIN_BYTES} bytes — likely stubs).\n"
                            f"This blocks fake-DONE loops where the agent claims completion without real artifacts.\n"
                            f"→ Action: write_file(path=\"<one of the above>\", content=\"...\")  ← actually create the file\n"
                            f"→ OR Action: run_command(\"...\")  ← if the file is produced by a build/sim tool\n"
                            f"→ Then call todo_update(index={index}, status='approved') again."
                        )
            except Exception:
                # Validator never blocks approval on its own exceptions.
                pass

            item.rejection_reason = ""
            todo_tracker.mark_approved(idx, _reason_stripped)  # internally calls save() + persists approved_reason
            _trace_todo_tool_event(index, item, "approved", reason=_reason_stripped)
            _git_tag_todo(index, "approved", item.content)
            # Per-IP commit checkpoint when a todo gets approved. The
            # auto-commit hook in atlas_ui only fires on file writes;
            # without this an "approve" decision (which itself doesn't
            # touch any tracked file) wouldn't leave a marker in the
            # IP's git timeline. commit_ip walks up to the nearest
            # per-IP .git and is silent if no IP repo is found.
            try:
                _slug = (item.content or "")[:60].replace("\n", " ")
                commit_ip(f"todo[{index}] approved: {_slug}")
            except Exception:
                pass
            _notes_section = ""
            try:
                import config as _cfg
                _notes_enabled = getattr(_cfg, "ENABLE_TODO_NOTES", True)
            except Exception:
                _notes_enabled = True
            if _notes_enabled and item.notes:
                _nlines = [f"  [{ni}] {n}" for ni, n in enumerate(item.notes, 1)]
                _notes_section = "\nWork log:\n" + "\n".join(_nlines)
            next_todo = todo_tracker.get_current_todo()
            if next_todo:
                next_idx = todo_tracker.current_index + 1
                return (
                    f"✅ Task {index} approved. [{reason}]"
                    f"{_notes_section}\n"
                    f"→ Next: todo_update(index={next_idx}, status='in_progress') — {next_todo.content}"
                )
            return f"✅ Task {index} approved. [{reason}]{_notes_section}\nAll tasks complete! 🏁"
        elif status == "completed":
            # Gate check: reject fake completions — require at least one non-todo tool call
            _tools_since_start = getattr(item, 'tools_since_in_progress', 0)
            if _tools_since_start == 0:
                # A blocked completion attempt can leave the task pending while
                # subsequent read/run/write actions are buffered on the tracker
                # as pending credit. Consume that credit here too, otherwise the
                # user-visible recovery instruction ("call a tool, then retry
                # completed") loops forever unless the LLM happens to restart
                # the task with status=in_progress.
                _pending_credit = int(getattr(todo_tracker, "_pending_tool_credit", 0) or 0)
                _current_idx = int(getattr(todo_tracker, "current_index", -1) or -1)
                if _pending_credit > 0 and (
                    _current_idx == idx or getattr(item, "status", "") in ("pending", "rejected")
                ):
                    item.tools_since_in_progress = _pending_credit
                    todo_tracker._pending_tool_credit = 0
                    _tools_since_start = _pending_credit
                    try:
                        todo_tracker.save()
                    except Exception:
                        pass
            if _tools_since_start == 0:
                return (
                    f"Completion blocked: Task {index} cannot be marked completed because no tools were called since starting this task.\n"
                    f"Produce a deliverable first (write a file, run a command, read evidence, etc.).\n"
                    f"→ Call a tool NOW (write_file, run_command, read_file, etc.)\n"
                    f"→ Then call todo_update(index={index}, status='completed') again."
                )
            item.rejection_reason = ""
            item.tools_since_in_progress = 0  # reset for potential re-work
            item.tools_since_completed = 0    # reset review-gate counter
            todo_tracker.mark_completed(idx)  # internally calls save()
            _trace_todo_tool_event(index, item, "completed", reason=reason or "")
            try:
                _slug = (item.content or "")[:60].replace("\n", " ")
                commit_ip(f"todo[{index}] completed: {_slug}")
            except Exception:
                pass
            review_steps = (
                f"Task {index} marked completed. Now perform a CRITICAL, ADVERSARIAL review.\n"
                f"You are a skeptical reviewer — your job is to find problems, not to approve.\n\n"
                f"MANDATORY before deciding (you MUST call at least one read tool before "
                f"approving or rejecting — the gate check enforces this):\n"
                f"  1. RE-READ the actual source artifacts you produced — never trust your\n"
                f"     own previous summary/report text from this conversation.\n"
                f"  2. If you wrote a report file (sim_report.txt, *.log, summary.md), it\n"
                f"     can be stale or inaccurate. Verify against ground-truth artifacts\n"
                f"     (results.xml, build output, the actual source file) FIRST.\n"
                f"  3. Does the result EXACTLY match the goal: \"{item.content}\"?\n"
                f"  4. Are there regressions, side effects, or edge cases broken?\n"
                f"  5. Is there anything incomplete, missing, or just partially done?\n"
                f"  6. Would a strict senior engineer be satisfied — or would they send it back?\n\n"
                f"⚠ Common failure mode: trusting your own self-written report. If you\n"
                f"   claim \"X is missing from file Y\", you MUST read Y first and quote\n"
                f"   the actual content as evidence — not paraphrase from memory.\n\n"
                f"DEFAULT to REJECT if there is ANY doubt. Approval requires concrete evidence.\n"
                f"→ All checks pass → todo_update(index={index}, status='approved', reason='<specific evidence: file:line you read, exact content quoted>')\n"
                f"→ Any issue found → todo_update(index={index}, status='rejected', reason='<exact problem with file:line evidence>')"
            )
            return review_steps
        elif status == "rejected":
            _reason_stripped = (reason or "").strip()
            _reason_lower = _reason_stripped.lower()
            _tracker_block_markers = (
                "no tools were called since starting this task",
                "completion blocked",
                "todo engine refuses completion",
                "todo tracker",
            )
            if item.status != "completed" and any(m in _reason_lower for m in _tracker_block_markers):
                _pending_credit = int(getattr(todo_tracker, "_pending_tool_credit", 0) or 0)
                if getattr(item, "tools_since_in_progress", 0) == 0 and _pending_credit > 0:
                    item.tools_since_in_progress = _pending_credit
                    todo_tracker._pending_tool_credit = 0
                    try:
                        todo_tracker.save()
                    except Exception:
                        pass
                return (
                    f"Rejection blocked: Task {index} was not rejected because this reason describes "
                    f"TodoTracker bookkeeping, not a failed task deliverable.\n"
                    f"Retry the valid completion transition now:\n"
                    f"→ todo_update(index={index}, status='completed')\n"
                    f"If the actual task output is wrong, reject only after reading/running ground-truth evidence "
                    f"and state the concrete unmet criterion."
                )
            # Review-gate (same as approved branch): must have called at least
            # one non-write evidence tool since this task entered review.
            # Prevents agents from rejecting based on their own stale summary
            # text — the false-rejection observed in tb-gen for Task 22 where
            # the agent claimed "SC2/SC4 missing from tb.py" but never re-read
            # tb.py (which actually contained all 9 scenarios).
            # Escalation matches the approved branch: ≥2 evidence required when
            # the task has already been rejected ≥2 times (livelock guard).
            _evidence = int(getattr(item, "tools_since_completed", 0) or 0)
            _rej_count = int(getattr(item, "rejection_count", 0) or 0)
            _required = 2 if _rej_count >= 2 else 1
            if item.status == "completed" and _evidence < _required:
                _esc = (
                    f"\n⚠ Escalated requirement: this task has been rejected "
                    f"{_rej_count} times — needs ≥{_required} verification calls before another reject."
                ) if _rej_count >= 2 else ""
                return (
                    f"Rejection blocked: Task {index} has only {_evidence} verification tool call(s) "
                    f"since review started (need ≥{_required}).{_esc}\n"
                    f"You may be looking at stale evidence (your own report file or a prior\n"
                    f"compressed summary). Verify against ground truth before rejecting:\n"
                    f"→ Re-read the source file(s) you claim are wrong (read_file / read_lines)\n"
                    f"→ OR run the test/check directly (run_command) to see real output\n"
                    f"→ OR grep for what you claim is missing (grep_file)\n"
                    f"Then call todo_update(index={index}, status='rejected', reason='<problem with file:line evidence>') again."
                )
            if not _reason_stripped:
                return (
                    f"Error: 'reason' is REQUIRED when rejecting Task {index}.\n"
                    f"You cannot reject without explaining what failed.\n"
                    f"Describe the exact problem and what must be fixed, e.g.:\n"
                    f"  'output.md missing Phase 5 interrupt section; regenerate with NVIC details'\n"
                    f"→ todo_update(index={index}, status='rejected', reason='<exact problem and fix needed>')"
                )
            if len(_reason_stripped) < 15:
                return (
                    f"Error: Rejection reason too vague for Task {index} (got: '{_reason_stripped}').\n"
                    f"Describe the exact problem and what must change — at least 15 characters.\n"
                    f"→ todo_update(index={index}, status='rejected', reason='<exact problem>')"
                )
            _low = _reason_stripped.lower()
            _rej_banned = {"bad", "wrong", "fail", "failed", "error", "broken",
                           "no", "nope", "not ok", "not good", "not done", "incomplete"}
            if _low in _rej_banned:
                return (
                    f"Error: '{reason}' is not a useful rejection reason for Task {index}.\n"
                    f"Specify WHAT is wrong and WHAT needs to change.\n"
                    f"→ todo_update(index={index}, status='rejected', reason='<specific problem and required fix>')"
                )
            todo_tracker.mark_rejected(idx, _reason_stripped)  # internally calls save()
            _trace_todo_tool_event(index, item, "rejected", reason=_reason_stripped)
            return f"❌ Task {index} rejected: {reason}"
        elif status == "in_progress":
            # NOTE: Do NOT store reason in rejection_reason — that field is
            # exclusively for rejected status. The step header will still show
            # the detail/criteria fields for context.
            todo_tracker.mark_in_progress(idx)
            _trace_todo_tool_event(index, item, "in_progress", reason=reason or "")

            # ── Static command execution (LLM-free) ──────────────────────────
            result = todo_tracker.auto_execute_command(idx)
            if result is not None:
                ok, tail = result
                cmd = item.command
                label = cmd if isinstance(cmd, str) else cmd.get("tool", "tool")
                last_log = item.command_logs[-1] if item.command_logs else {}
                log_file = last_log.get("log_file", "")
                total_lines = last_log.get("lines", 0)
                elapsed = last_log.get("elapsed", 0)
                log_info = f"Log: {log_file} ({total_lines} lines, {elapsed}s)\n" if log_file else ""

                if ok:
                    next_todo = todo_tracker.get_current_todo()
                    next_msg = (
                        f"\n→ Next: todo_update(index={todo_tracker.current_index + 1},"
                        f" status='in_progress') — {next_todo.content}"
                    ) if next_todo else "\nAll tasks complete! 🏁"
                    return (
                        f"✅ Task {index} [command: {label}] passed.\n"
                        f"{log_info}"
                        f"--- output tail ---\n{tail}"
                        f"{next_msg}"
                    )
                else:
                    # Use actual current_index to determine if a jump happened.
                    # on_reject field may still hold original value even if stagnation
                    # disabled the jump inside auto_execute_command().
                    jump_msg = ""
                    actually_jumped = todo_tracker.current_index != idx
                    if actually_jumped:
                        jump_idx = todo_tracker.current_index
                        jump_todo = todo_tracker.todos[jump_idx]
                        jump_msg = (
                            f"\n→ Jumping to Task {jump_idx + 1}: {jump_todo.content}"
                            f"\n→ todo_update(index={jump_idx + 1}, status='in_progress')"
                        )
                    # Surface the failure to the human watching the session. The
                    # tool result below only reaches the LLM; without this notice
                    # a looping gate (on_reject) looks like a silent hang.
                    _retries = getattr(item, "rejection_count", 0)
                    _notice_jump = (
                        f"\n↩ retrying from Task {todo_tracker.current_index + 1}"
                        if actually_jumped else ""
                    )
                    _emit_user_notice(
                        f"⚠️ Gate failed — Task {index} [{label}]"
                        f" (attempt {_retries}/3)\n"
                        f"{tail or '(no output)'}\n"
                        f"{('full log: ' + log_file) if log_file else ''}"
                        f"{_notice_jump}",
                        cls="gate-error",
                    )
                    return (
                        f"❌ Task {index} [command: {label}] failed.\n"
                        f"{log_info}"
                        f"--- output tail ---\n{tail}"
                        f"{jump_msg}"
                    )
            # ── End static command execution ──────────────────────────────────

            todo_tracker.save()
            # ── Reality-check audit on task entry ──────────────────────────
            # Surface ground-truth disk state for any file path tokens in the
            # task content/criteria. Without this, agents enter a task with no
            # awareness of what's actually on disk and tend to claim DONE
            # against fake state (esp. after compression). The audit lines
            # below are appended to the in_progress confirmation so the LLM
            # sees disk reality at the very moment the task begins.
            try:
                import re as _re_rc
                import os as _os_rc
                _scan_text = " ".join([
                    str(item.content or ""),
                    str(getattr(item, "criteria", "") or ""),
                    str(getattr(item, "detail", "") or ""),
                ])
                _path_re = _re_rc.compile(
                    r'(?<![/\w.-])'
                    r'((?:[\w.-]+/)+[\w.-]+\.'
                    r'(?:sv|v|vh|svh|yaml|yml|md|f|txt|log|json|py|sdc|upf|tcl|lib|lef|gds|spef|sdf|vcd|out|netlist))'
                    r'(?![\w/.-])'
                )
                _candidates = [p for p in set(_path_re.findall(_scan_text))
                               if "<" not in p and ">" not in p]
                _audit_lines = []
                for _p in _candidates[:10]:  # cap at 10 paths to keep output bounded
                    _resolved = None
                    for _base in (None, _os_rc.getcwd()):
                        _full = _p if _base is None else _os_rc.path.join(_base, _p)
                        if _os_rc.path.exists(_full):
                            try:
                                _sz = _os_rc.path.getsize(_full)
                                _resolved = (_full, _sz)
                                break
                            except OSError:
                                pass
                    if _resolved:
                        _f, _s = _resolved
                        _tag = "STUB" if _s < 50 else f"{_s}B"
                        _audit_lines.append(f"  ✓ {_p}: exists ({_tag})")
                    else:
                        _audit_lines.append(f"  ✗ {_p}: MISSING on disk")
                _audit_block = ""
                if _audit_lines:
                    _audit_block = (
                        "\n[Reality Check — disk audit at task start]\n"
                        + "\n".join(_audit_lines)
                        + "\nGround truth above. Do NOT claim done unless a real Action: write_file or run_command\n"
                          "actually transforms these paths from MISSING/STUB to the required state."
                    )
                return f"▶ Task {index} in progress: {item.content}{_audit_block}"
            except Exception:
                # Reality check is advisory — never fail the in_progress transition.
                return f"▶ Task {index} in progress: {item.content}"
        else:  # pending
            # NOTE: Do NOT store reason in rejection_reason for pending either.
            item.status = "pending"
            item.completed_at = None
            if getattr(todo_tracker, "current_index", -1) == idx:
                todo_tracker.current_index = -1
            todo_tracker.save()
            return f"⏸ Task {index} set to pending: {item.content}"

    todo_tracker.save()
    return f"✅ Task {index} updated."


def todo_add(content="", activeForm="", priority="medium", detail="", criteria="", index=None,
             command="", on_reject=0, on_success=0, on_condition=None, **kwargs):
    """
    Add a single task to the existing todo list.
    More efficient than todo_write for adding tasks mid-execution.

    Default insert position: **end of the list (append)**. Do NOT pass
    `index=1` (or any small N) just to "add another todo" — that
    prepends in front of work the user is already running, which
    reorders the execution flow and is almost always wrong. Pass
    `index` only when you deliberately want the new task to jump
    ahead of pending items (e.g. an urgent dependency).

    Args:
        content (str): Task description (required).
        activeForm (str): Display text while in progress (auto-generated if omitted).
        priority (str): "high", "medium", or "low" (default: "medium").
        detail (str): Implementation details (required).
        criteria (str): Completion criteria, newline-separated (required).
        index (int, OPTIONAL): 1-based position to insert at. **Leave
            unset to append at the end** (correct 99% of the time).
            Only specify when the new task must run before existing
            pending items.
        command (str|dict): Shell command or tool call to auto-execute (no LLM needed).
        on_reject (int): 1-based task index to jump to on command failure (0=disabled).
        on_success (int): 1-based task index to jump to on command success (0=next sequential).
        on_condition (list): Conditional branching rules — [{"if": "pattern", "goto": N}, ...].
                             Pattern matched against command output via regex. First match wins.
                             Overrides on_success/on_reject when matched.

    Example:
        # ✅ Correct — appends after every existing task:
        todo_add(content="Fix lint errors", detail="Update lint issues.", criteria="lint passes", priority="low")
        todo_add(content="Run lint", detail="Run lint target.", criteria="make lint passes", command="make lint", on_reject=2)
        # ❌ Wrong — prepends to the top, reorders execution:
        todo_add(content="Run sim", detail="Run simulation.", criteria="simulation passes", index=1)
    """
    _locked = _todo_template_lock_error("todo_add")
    if _locked:
        return _locked

    todo_tracker = _get_todo_tracker()

    if todo_tracker is None:
        return _todo_tracker_unavailable_error()

    # Accept LLM-leaked alias names for `content` (Codex/gpt-5.x sometimes
    # emit `text=`, `task=`, `description=`, `title=` instead). Without
    # this the call returns "'content' is required" and the LLM retries
    # with the same wrong key.
    if not content and kwargs:
        for _alias in ("text", "task", "description", "title", "name", "label", "body"):
            _v = kwargs.get(_alias)
            if isinstance(_v, str) and _v.strip():
                content = _v
                break

    if not content:
        return "Error: 'content' is required."
    if not str(detail or "").strip():
        return "Error: 'detail' is required."
    if not str(criteria or "").strip():
        return "Error: 'criteria' is required."

    from lib.todo_tracker import TodoItem, _generate_active_form
    active = activeForm or _generate_active_form(content)

    new_item = TodoItem(
        content=content,
        active_form=active,
        status="pending",
        priority=priority,
        detail=str(detail).strip(),
        criteria=str(criteria).strip(),
        command=command,
        on_reject=int(on_reject),
        on_success=int(on_success),
        on_condition=on_condition if on_condition else None,
    )

    if index is not None:
        try:
            requested_index = int(index)
        except (TypeError, ValueError):
            return "Error: 'index' must be an integer."
        requested_index = max(1, requested_index)
        idx = requested_index - 1
        idx = max(0, min(idx, len(todo_tracker.todos)))
        todo_tracker.todos.insert(idx, new_item)
    else:
        todo_tracker.todos.append(new_item)

    todo_tracker.save()
    return todo_tracker.format_progress()


def todo_note(index=None, text=""):
    """
    Append a progress note to a task's work log.
    Call this anytime during execution to record findings, attempts, or criteria status.
    Notes are append-only, survive compression, and are shown during review and rejection.

    Args:
        index (int): 1-based task index (required).
        text (str): Note to append — e.g. "criteria 'compiles' ✅", "tried X → failed: reason"

    Example:
        todo_note(index=2, text="found: cache burst_len=15 in instr_cache.sv:17")
        todo_note(index=2, text="criteria 'compiles clean' ✅ — iverilog passed")
        todo_note(index=2, text="tried direct AXI → failed: missing handshake, switched to wrapper")
    """
    import src.config as _cfg
    if not getattr(_cfg, "ENABLE_TODO_NOTES", True):
        return "Todo notes are disabled (ENABLE_TODO_NOTES=false)."

    todo_tracker = _get_todo_tracker()
    if todo_tracker is None:
        return _todo_tracker_unavailable_error()
    if not todo_tracker.todos:
        return "Error: No active todo list."

    if index is None:
        return "Error: 'index' (1-based) is required."

    if not text or not str(text).strip():
        return "Error: 'text' is required."

    try:
        idx = int(index) - 1
    except (ValueError, TypeError):
        return f"Error: index must be an integer, got '{index}'"

    if not (0 <= idx < len(todo_tracker.todos)):
        return f"Error: index {index} out of range (1-{len(todo_tracker.todos)})"

    item = todo_tracker.todos[idx]
    if item.notes is None:
        item.notes = []
    item.notes.append(str(text).strip())
    todo_tracker.save()
    _trace_todo_tool_event(index, item, "note", note_text=str(text).strip())
    return f"📝 Note [{len(item.notes)}] added to Task {index}: {text.strip()}"


def todo_remove(index=None, id=None):
    """
    Remove a task from the todo list by index.

    Args:
        index (int): 1-based index of the task to remove (required).

    Example:
        todo_remove(index=3)
    """
    if os.environ.get("PLAN_MODE", "false").lower() != "true":
        return "Error: todo_remove is disabled outside plan mode. Mark stale or failed tasks rejected instead of deleting them."

    todo_tracker = _get_todo_tracker()

    if todo_tracker is None:
        return _todo_tracker_unavailable_error()
    if not todo_tracker.todos:
        return "Error: No active todo list."

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

    if todo_tracker is None:
        return _todo_tracker_unavailable_error()
    if not todo_tracker.todos:
        return "Error: No active todo list."
    return todo_tracker.format_progress()


# ============================================================
# cursor-agent Tool
# ============================================================

def cursor_agent(task="", yolo="false", mode=""):
    """
    Delegate a task to cursor-agent — a full agentic CLI that handles
    file reads, writes, shell commands, and code edits internally.

    Use this when you need complex multi-step file/code operations that
    benefit from cursor-agent's built-in tool access. The primary agent
    handles todo tracking and orchestration; cursor-agent handles execution.

    Args:
        task: Clear description of what cursor-agent should do.
              Include all relevant context (file paths, goal, constraints).
        yolo: "true" to allow write/shell tools without confirmation (default: "false").
              Set "true" for tasks that modify files or run commands.
        mode: "" (default, full agent), "ask" (Q&A only), "plan" (planning only).

    Returns:
        cursor-agent's final response text.

    Examples:
        Action: cursor_agent(task="Read src/main.py and summarize the chat_loop function")
        Action: cursor_agent(task="Refactor the serialize_messages function in src/cursor_agent_backend.py to handle empty content blocks", yolo="true")
        Action: cursor_agent(task="Run the test suite and report which tests fail", yolo="true")
    """
    import subprocess, json, sys as _sys

    if not task:
        return "Error: 'task' is required. Usage: cursor_agent(task=\"describe what to do\")"

    try:
        import config as _cfg
    except ImportError:
        import src.config as _cfg

    model = getattr(_cfg, "CURSOR_AGENT_MODEL", "auto")
    workspace = getattr(_cfg, "CURSOR_AGENT_WORKSPACE", "")
    _yolo = str(yolo).lower() in ("true", "1", "yes")

    cmd = ["cursor-agent", "--print", "--model", model or "auto",
           "--output-format", "stream-json", "--stream-partial-output"]
    if _yolo:
        cmd.append("--yolo")
    if mode:
        cmd += ["--mode", mode]
    if workspace:
        cmd += ["--workspace", workspace]
    cmd += ["-p", task]

    try:
        proc = subprocess.Popen(
            cmd,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            # Force UTF-8 (see run_command for why).
            encoding='utf-8',
            errors='replace',
            bufsize=1,
        )
    except FileNotFoundError:
        return "Error: cursor-agent not found. Install it or check PATH."

    collected = []
    tool_calls_seen = []

    try:
        for raw_line in proc.stdout:
            raw_line = raw_line.strip()
            if not raw_line:
                continue
            try:
                chunk = json.loads(raw_line)
            except json.JSONDecodeError:
                continue

            chunk_type = chunk.get("type")

            if chunk_type == "assistant" and "timestamp_ms" in chunk:
                content = chunk.get("message", {}).get("content", [])
                for block in content:
                    if isinstance(block, dict) and block.get("type") == "text":
                        text = block.get("text", "")
                        if text:
                            collected.append(text)
                            _sys.stdout.write(text)
                            _sys.stdout.flush()

            elif chunk_type == "tool_call" and chunk.get("subtype") == "started":
                # Show cursor-agent's internal tool calls
                tc = chunk.get("tool_call", {})
                for key, val in tc.items():
                    name = key.replace("ToolCall", "")
                    args = val.get("args", {}) if isinstance(val, dict) else {}
                    detail = args.get("path") or args.get("file_path") or args.get("command", "")[:60]
                    label = f"[cursor:{name}" + (f" {detail}" if detail else "") + "]"
                    tool_calls_seen.append(label)
                    _sys.stdout.write(f"\n  {label}")
                    _sys.stdout.flush()

    finally:
        proc.stdout.close()
        proc.wait()
        stderr = proc.stderr.read() if proc.stderr else ""

    if proc.returncode != 0 and not collected:
        err = stderr.strip() if stderr else f"exit code {proc.returncode}"
        return f"Error: cursor-agent failed — {err}"

    result = "".join(collected).strip()
    if tool_calls_seen:
        result = f"[Tools used: {', '.join(tool_calls_seen)}]\n\n" + result
    return result or "(no output)"


# ============================================================
# Background Agent Tools (v2 Architecture)
# ============================================================

def _custom_agent_dict(definition):
    from core.custom_agents import as_public_dict, custom_agent_dir
    data = as_public_dict(definition)
    if getattr(definition, "owner_user_id", ""):
        data["storage"] = "db"
        data["owner_user_id"] = definition.owner_user_id
        data["scope"] = getattr(definition, "scope", "private") or "private"
    else:
        data["storage"] = "file"
        data["path"] = str(custom_agent_dir() / f"{definition.name}.json")
    return data


def custom_agent_save(name="", system_prompt="", base_agent="explore",
                      allowed_tools="", description="", model="",
                      reasoning_effort="", effort="", scope="private"):
    """
    Save or update a reusable custom agent definition for the active Atlas user.

    When an Atlas DB user is active, definitions are stored per-user in DB.
    Legacy project-local file storage remains available without a DB user.
    They can be run with background_task(agent="<name>", prompt="...").
    """
    try:
        from core.custom_agents import custom_agent_dir, current_owner_user_id, save_custom_agent

        owner_user_id = current_owner_user_id()
        definition = save_custom_agent(
            name=name,
            system_prompt=system_prompt,
            base_agent=base_agent,
            allowed_tools=allowed_tools,
            description=description,
            model=model,
            reasoning_effort=reasoning_effort or effort,
            owner_user_id=owner_user_id,
            scope=scope or "private",
        )
        data = _custom_agent_dict(definition)
        location = (
            f"Storage: db (owner_user_id={definition.owner_user_id}, scope={definition.scope})"
            if definition.owner_user_id
            else f"Path: {custom_agent_dir() / (definition.name + '.json')}"
        )
        return (
            f"Custom agent saved: {definition.name}\n"
            f"{location}\n"
            f"Base agent: {definition.base_agent}\n"
            f"Allowed tools: {definition.allowed_tools or '(base default)'}\n"
            f"Model: {definition.model or '(default)'}\n"
            f"Reasoning effort: {definition.reasoning_effort or '(default)'}\n"
            f"JSON: {json.dumps(data, ensure_ascii=False)}"
        )
    except Exception as e:
        return f"Error saving custom agent: {e}"


def custom_agent_list():
    """List custom agents visible to the active Atlas user."""
    try:
        from core.custom_agents import custom_agent_dir, current_owner_user_id, list_custom_agents

        owner_user_id = current_owner_user_id()
        agents = [
            _custom_agent_dict(agent)
            for agent in list_custom_agents(owner_user_id=owner_user_id)
        ]
        if not agents:
            if owner_user_id:
                return "No custom agents found for the current user."
            return f"No custom agents found in {custom_agent_dir()}."
        return json.dumps({
            "storage": "db" if owner_user_id else "file",
            "owner_user_id": owner_user_id,
            "path": str(custom_agent_dir()),
            "agents": agents,
        }, indent=2, ensure_ascii=False)
    except Exception as e:
        return f"Error listing custom agents: {e}"


def _compose_agent_system_prompt(base_agent: str, custom_prompt: str) -> str:
    custom_prompt = str(custom_prompt or "").strip()
    if not custom_prompt:
        return ""
    try:
        from core.agent_runner import _load_agent_prompt
        base_prompt = _load_agent_prompt(base_agent)
    except Exception:
        base_prompt = f"You are a {base_agent} agent. Use the ReAct format."
    return (
        f"{base_prompt.rstrip()}\n\n"
        "## Custom Agent Instructions\n"
        f"{custom_prompt}"
    )


def _resolve_background_agent(agent, *, base_agent="", system_prompt="",
                              allowed_tools="", model="", reasoning_effort=""):
    from core.custom_agents import (
        BASE_AGENTS,
        current_owner_user_id,
        load_custom_agent,
        parse_allowed_tools,
        runtime_overrides_for_effort,
        validate_base_agent,
        validate_agent_name,
    )

    valid_agents = set(BASE_AGENTS)
    requested = str(agent or "explore").strip() or "explore"
    owner_user_id = current_owner_user_id()
    custom = load_custom_agent(requested, owner_user_id=owner_user_id)

    dynamic_prompt = str(system_prompt or "").strip()
    resolved_allowed_tools = parse_allowed_tools(allowed_tools)
    resolved_model = str(model or "").strip()
    resolved_effort = str(reasoning_effort or "").strip()
    display_agent = requested

    if custom:
        runner_agent = custom.base_agent
        prompts = [custom.system_prompt]
        if dynamic_prompt:
            prompts.append(dynamic_prompt)
        dynamic_prompt = "\n\n".join(prompts)
        if resolved_allowed_tools is None:
            resolved_allowed_tools = custom.allowed_tools
        resolved_model = resolved_model or custom.model
        resolved_effort = resolved_effort or custom.reasoning_effort
    elif requested in valid_agents:
        runner_agent = requested
    elif dynamic_prompt:
        runner_agent = validate_base_agent(base_agent or "explore")
        try:
            display_agent = validate_agent_name(requested, allow_reserved=True)
        except ValueError:
            display_agent = runner_agent
    else:
        return {
            "error": f"invalid agent '{requested}'",
            "valid_agents": sorted(valid_agents),
        }

    merged_system_prompt = _compose_agent_system_prompt(runner_agent, dynamic_prompt)
    allowed_set = set(resolved_allowed_tools) if resolved_allowed_tools is not None else None
    runtime_extra = runtime_overrides_for_effort(resolved_effort)
    return {
        "display_agent": display_agent,
        "runner_agent": runner_agent,
        "system_prompt": merged_system_prompt or None,
        "allowed_tools": allowed_set,
        "allowed_tools_list": resolved_allowed_tools,
        "model": resolved_model,
        "reasoning_effort": resolved_effort,
        "runtime_extra": runtime_extra,
        "is_custom": bool(custom or dynamic_prompt),
        "owner_user_id": owner_user_id,
    }


def background_task(agent="explore", prompt="", context="", foreground="true",
                    delegate="", workflow="", system_prompt="",
                    allowed_tools="", base_agent="", model="",
                    reasoning_effort="", effort=""):
    """
    Launch an agent to handle a sub-task.

    Runs in foreground (synchronous) by default. Set foreground="false" for background execution.

    Args:
        agent: Agent type - "explore" (read-only research), "execute" (full access),
               "review" (read-only verification), or a saved custom agent name.
        prompt: Clear description of what the agent should do
        context: Optional context from current conversation to pass to the agent
        foreground: "true" (default) for synchronous execution, "false" for background.
                    Honoured for `delegate` too — foreground="false" dispatches the
                    delegate/http-worker asynchronously (returns a task_id) so repeated
                    calls fan workers out in parallel.
        delegate: Delegate backend — "" (default in-process sub-agent),
                  "http-worker" to dispatch to a separate full-main-loop
                  worker process (configured via WORKER_URL_<workflow> /
                  WORKER_URL_DEFAULT env vars). Use this for multi-step
                  execution where the in-process sub-agent's reduced
                  loop tends to stall.
        workflow: Workflow name (e.g. "rtl-gen") to activate inside the
                  delegate. With delegate="http-worker" the worker
                  loads the matching workspace; in-process sub-agent
                  loads the system prompt from `workflow/<name>/`.
        system_prompt: Optional one-off custom instructions. Appended to the
                       base agent prompt so ReAct/tool rules stay intact.
        allowed_tools: Optional comma-separated tool allow-list for this run.
        base_agent: Base agent to use for one-off custom prompts.
        model: Optional model/profile override for this sub-agent/worker.
        reasoning_effort: Optional reasoning effort override.

    Returns:
        Foreground: Direct result from the agent.
        Background: task_id string. Use background_output(task_id=...) to get results.

    Example:
        Action: background_task(agent="explore", prompt="Find all Verilog modules in rtl/")
        Action: background_task(agent="execute", prompt="Fix the bug in src/main.py")
        Action: background_task(agent="review", prompt="Verify the fix in src/main.py is correct")
        Action: background_task(delegate="http-worker", workflow="rtl-gen", prompt="Generate counter.sv from counter.ssot.yaml")
    """
    try:
        import sys as _sys
        _cfg = _sys.modules.get('config') or _sys.modules.get('src.config')
        if not getattr(_cfg, 'ENABLE_SUB_AGENTS', False):
            return "Error: Sub-agents are disabled. Set ENABLE_SUB_AGENTS=true in .config to enable background_task."

        # Auto-fix: if agent looks like a prompt (not a valid agent name), shift args
        from core.custom_agents import BASE_AGENTS, current_owner_user_id, load_custom_agent
        valid_agents = set(BASE_AGENTS)
        owner_user_id = current_owner_user_id()
        has_custom_agent = bool(load_custom_agent(str(agent or ""), owner_user_id=owner_user_id))
        if agent not in valid_agents and not has_custom_agent and not prompt and not system_prompt:
            # LLM passed prompt as first arg: background_task("do something...")
            prompt = agent
            agent = "explore"  # default agent
        elif agent not in valid_agents and not has_custom_agent and prompt and not system_prompt:
            context = f"{agent}\n{context}" if context else agent
            agent = "explore"

        if not prompt:
            return "Error: 'prompt' is required. Usage: background_task(agent=\"explore\", prompt=\"your task description here\")"

        resolved = _resolve_background_agent(
            agent,
            base_agent=base_agent,
            system_prompt=system_prompt,
            allowed_tools=allowed_tools,
            model=model,
            reasoning_effort=reasoning_effort or effort,
        )
        if resolved.get("error"):
            return (
                f"Error: Invalid agent type '{agent}'. Must be one of: "
                f"{', '.join(resolved['valid_agents'])}, or a saved custom agent visible to this user."
            )

        is_foreground = str(foreground).lower() in ("true", "1", "yes")
        display_agent = resolved["display_agent"]
        runner_agent = resolved["runner_agent"]
        resolved_system_prompt = resolved["system_prompt"]
        resolved_allowed_tools = resolved["allowed_tools"]
        resolved_model = resolved["model"]
        resolved_effort = resolved["reasoning_effort"]

        # ── Delegate routing (http-worker etc.) ─────────────────────────
        # When `delegate` is non-empty, route through DelegateRunner
        # instead of the in-process sub-agent. http-worker dispatches to
        # a separate full-main-loop worker process — best for multi-step
        # execution. Other backends (cursor-agent, codex, gemini, api)
        # are handled the same way.
        if delegate:
            try:
                from core.delegate_runner import DelegateRunner
                runner = DelegateRunner()
                if delegate not in runner.list_backends():
                    return (f"Error: Invalid delegate '{delegate}'. "
                            f"Available: {', '.join(runner.list_backends())}")
                def _run_delegate():
                    return runner.run(
                        backend=delegate,
                        task=prompt,
                        context=context,
                        workflow_name=workflow,
                        model_override=resolved_model or None,
                        system_prompt=resolved_system_prompt,
                        allowed_tools=resolved["allowed_tools_list"],
                        reasoning_effort=resolved_effort,
                        custom_agent_name=display_agent if resolved["is_custom"] else "",
                    )

                # Background: dispatch async so repeated background_task(delegate=...)
                # calls fan workers out in parallel instead of blocking serially.
                # (Previously this branch always ran synchronously and ignored
                # `foreground`, so http-workers could never run in parallel.)
                if not is_foreground:
                    from core.background import get_background_manager

                    def _run_delegate_formatted():
                        out = _run_delegate()
                        return (
                            f"=== Delegate Result: {delegate} (workflow={workflow or '-'}, agent={display_agent}) ===\n"
                            f"{out}\n"
                            f"=== End ==="
                        )

                    task_id = get_background_manager().launch_callable(
                        _run_delegate_formatted,
                        label=f"{delegate}/{workflow or display_agent or '?'}",
                        prompt=prompt,
                    )
                    return (
                        f"Background delegate launched: {task_id}\n"
                        f"Delegate: {delegate} (workflow={workflow or '-'}, agent={display_agent})\n"
                        f"Prompt: {prompt[:100]}...\n\n"
                        f"Use background_output(task_id=\"{task_id}\") to collect the result. "
                        f"Issue more background_task(delegate=..., foreground=\"false\") calls to run workers in parallel."
                    )

                # Foreground (default): synchronous — unchanged behaviour.
                out = _run_delegate()
                from lib.display import Color
                print(f"\n  {Color.CYAN}◀ {delegate}/{workflow or display_agent or '?'} → primary{Color.RESET}")
                return (
                    f"=== Foreground Delegate Result: {delegate} (workflow={workflow or '-'}, agent={display_agent}) ===\n"
                    f"{out}\n"
                    f"=== End ==="
                )
            except Exception as e:
                return f"Error: delegate '{delegate}' failed: {e}"

        if is_foreground:
            # Foreground: synchronous execution
            import sys
            import config as _cfg
            from contextlib import nullcontext
            from core.agent_runner import run_agent_session

            model_ctx = _cfg.scoped_model_runtime(resolved_model) if resolved_model else nullcontext()
            with model_ctx, _cfg.scoped_runtime_extra(resolved["runtime_extra"]):
                active_model = getattr(_cfg, "MODEL_NAME", resolved_model) if resolved_model else None
                result = run_agent_session(
                    agent_name=runner_agent,
                    prompt=prompt,
                    model_override=active_model,
                    allowed_tools=resolved_allowed_tools,
                    system_prompt=resolved_system_prompt,
                    parent_context=context,
                    verbose=_cfg.DEBUG_MODE,
                )

            # Sync sub-agent completion to primary todo tracker
            _sync_subagent_todo(result.output)

            # Show sub-agent → primary handoff to user
            from lib.display import Color
            output_chars = len(result.output)
            output_tokens = output_chars // 4  # rough estimate
            print(f"\n  {Color.CYAN}◀ {display_agent} → primary{Color.RESET} ({result.status}, {result.execution_time_ms}ms, ~{output_tokens:,} tok)")
            if result.status == "error" and result.error:
                print(f"  {Color.RED}  error: {result.error}{Color.RESET}")
            if result.files_modified:
                print(f"  {Color.DIM}  modified: {result.files_modified}{Color.RESET}")

            return (
                f"=== Foreground Agent Result: {display_agent} ===\n"
                f"Base agent: {runner_agent}\n"
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
                agent=runner_agent,
                prompt=prompt,
                parent_context=context,
                model_override=resolved_model or None,
                allowed_tools=resolved_allowed_tools,
                system_prompt=resolved_system_prompt,
                reasoning_effort=resolved_effort,
            )

            return (
                f"Background task launched: {task_id}\n"
                f"Agent: {display_agent}\n"
                f"Base agent: {runner_agent}\n"
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


def parallel_todo_dispatch(
    todos=None,
    max_workers=3,
    models=None,
    timeout_s=1800,
    claude_tools=None,
    extra_overrides=None,
):
    """
    Dispatch a batch of TODOs to background sub-agent workers and wait for results.

    Args:
        todos: List of TODO strings/dicts, or a JSON/list-like string.
        max_workers: Auto-discovery worker cap when models is omitted.
        models: Optional explicit model/profile list. One worker is launched
                per listed model, capped by TODO count.
        timeout_s: Seconds to wait for all launched workers.
        claude_tools: Comma-separated tool names to grant to claude-cli
                workers (e.g. "WebSearch,WebFetch"). Empty/None keeps the
                default behaviour of disabling Claude Code's built-in
                tools so common_ai_agent stays the single executor.
        extra_overrides: Dict of additional thread-local config overrides
                (any key from src.config._THREAD_RUNTIME_KEYS) applied to
                every worker for this job — for advanced use cases.

    Returns:
        Aggregated worker results as JSON.
    """
    try:
        from core.parallel_todo_dispatcher import ParallelTodoDispatcher

        def _coerce_list(value):
            if value is None or value == "":
                return None
            if isinstance(value, list):
                return value
            if isinstance(value, tuple):
                return list(value)
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return None
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, list):
                        return parsed
                except Exception:
                    pass
                return [part.strip() for part in re.split(r"[\n,]+", text) if part.strip()]
            return [value]

        def _coerce_dict(value):
            if value is None or value == "":
                return None
            if isinstance(value, dict):
                return value
            if isinstance(value, str):
                text = value.strip()
                if not text:
                    return None
                try:
                    parsed = json.loads(text)
                    if isinstance(parsed, dict):
                        return parsed
                except Exception:
                    return None
            return None

        dispatcher = ParallelTodoDispatcher()
        job_id = dispatcher.dispatch(
            todos=_coerce_list(todos) or [],
            max_workers=_as_int(max_workers, 3) or 3,
            models=_coerce_list(models),
            claude_tools=str(claude_tools) if claude_tools else None,
            extra_overrides=_coerce_dict(extra_overrides),
        )
        result = dispatcher.wait(job_id, timeout_s=_as_int(timeout_s, 1800) or 1800)
        return json.dumps(result, ensure_ascii=False, indent=2)
    except Exception as e:
        import traceback
        return f"Error in parallel_todo_dispatch: {e}\n{traceback.format_exc()}"


# ============================================================
# Workflow Orchestration Tools
# ============================================================

def pipeline_execute(mode="auto", max_workers=3):
    """
    Execute pending todo items as a pipeline — sequential, parallel, or auto-grouped.

    Primary agent acts as orchestrator. Each todo is dispatched to its assigned
    workflow + delegate backend. Results are returned for primary to review.

    Args:
        mode: Execution mode — "sequential" (one-by-one, result feeds next),
              "parallel" (all simultaneously), "auto" (group by workflow, parallel within groups)
        max_workers: Maximum concurrent workers for parallel execution (default: 3)

    Example:
        Action: pipeline_execute(mode="auto")
        Action: pipeline_execute(mode="parallel", max_workers=5)
        Action: pipeline_execute(mode="sequential")
    """
    todo_tracker = _get_todo_tracker()
    if todo_tracker is None or not todo_tracker.todos:
        return "No todo list. Use todo_write() first."

    # Collect actionable todos (pending + rejected)
    actionable = [(i, t) for i, t in enumerate(todo_tracker.todos)
                  if t.status in ("pending", "rejected")]
    if not actionable:
        return "No pending/rejected tasks to execute."

    try:
        from core.workflow_orchestrator import WorkflowOrchestrator
        from pathlib import Path
        orch = WorkflowOrchestrator(project_root=Path.cwd())

        indices, todos = zip(*actionable)

        if mode == "sequential":
            results = orch.run_sequential(list(todos))
        elif mode == "parallel":
            results = orch.run_parallel(list(todos), max_workers=int(max_workers))
        else:  # auto
            results = orch.run_pipeline(list(todos), max_workers=int(max_workers))

        # Store delegate results back into todo items
        for r in results:
            if r.index < len(actionable):
                orig_idx = actionable[r.index][0]
                if orig_idx < len(todo_tracker.todos):
                    item = todo_tracker.todos[orig_idx]
                    item.delegate_result = r.output or r.error or ""
                    if r.status == "completed":
                        item.status = "completed"
                    elif r.status == "error":
                        item.status = "rejected"
                        item.rejection_reason = r.error or "Pipeline execution failed"

        todo_tracker.save()
        return orch.format_pipeline_results(results)

    except Exception as e:
        import traceback
        return f"Error in pipeline execution: {e}\n{traceback.format_exc()}"


def workflow_dispatch(index=None, workflow="", delegate=""):
    """
    Assign a workflow and/or delegate backend to a specific todo item.

    Args:
        index: 1-based index of the todo item
        workflow: Workflow name (must match a workflow/<name>/workspace.json)
        delegate: Backend to delegate to ("sub-agent", "cursor-agent", "codex", "gemini", "api")

    Example:
        Action: workflow_dispatch(index=1, workflow="rtl-gen", delegate="sub-agent")
        Action: workflow_dispatch(index=3, workflow="tb-gen")
        Action: workflow_dispatch(index=5, delegate="cursor-agent")
    """
    todo_tracker = _get_todo_tracker()
    if todo_tracker is None or not todo_tracker.todos:
        return "No todo list. Use todo_write() first."

    if index is None:
        return "Error: 'index' (1-based) is required."

    try:
        idx = int(index) - 1
    except ValueError:
        return f"Error: index must be an integer, got '{index}'"

    if not (0 <= idx < len(todo_tracker.todos)):
        return f"Error: index {index} out of range (1-{len(todo_tracker.todos)})"

    item = todo_tracker.todos[idx]

    # Validate workflow if specified
    if workflow:
        from core.workflow_orchestrator import WorkflowOrchestrator
        from pathlib import Path
        orch = WorkflowOrchestrator(project_root=Path.cwd())
        if not orch.workflow_exists(workflow):
            available = list(orch.discover_workflows().keys())
            return f"Error: Workflow '{workflow}' not found. Available: {available}"
        item.workflow = workflow

    # Validate delegate if specified
    if delegate:
        from core.delegate_runner import DelegateRunner
        valid_backends = DelegateRunner.list_backends()
        if delegate not in valid_backends:
            return f"Error: Unknown delegate '{delegate}'. Available: {valid_backends}"
        item.delegate = delegate

    todo_tracker.save()

    parts = [f"Task {index}: {item.content}"]
    if workflow:
        parts.append(f"  workflow → {workflow}")
    if delegate:
        parts.append(f"  delegate → {delegate}")
    return "✅ Assigned:\n" + "\n".join(parts)


def workflow_list():
    """
    List all available workflows discovered dynamically from workflow/*/workspace.json.

    Returns:
        Formatted list of workflow names and descriptions.

    Example:
        Action: workflow_list()
    """
    try:
        from core.workflow_orchestrator import WorkflowOrchestrator
        from pathlib import Path
        orch = WorkflowOrchestrator(project_root=Path.cwd())
        return orch.list_workflows()
    except Exception as e:
        return f"Error listing workflows: {e}"


# ─── Project Management Tools ──────────────────────────────────────────────

def project_list():
    """
    List all session projects (directories under .session/).

    Returns:
        Formatted list of project names with active marker, file counts, and sizes.

    Example:
        Action: project_list()
    """
    try:
        from pathlib import Path
        import os
        import config as _cfg

        session_root = Path.cwd() / '.session'
        if not session_root.is_dir():
            return "No .session/ directory found. No projects exist yet."

        active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
        lines = []
        for d in sorted(session_root.iterdir()):
            if not d.is_dir():
                continue
            # Count files and total size
            files = [f for f in d.rglob('*') if f.is_file()]
            total_size = sum(f.stat().st_size for f in files)
            marker = " ◀ active" if d.name == active else ""
            size_str = f"{total_size/1024:.0f}KB" if total_size > 1024 else f"{total_size}B"
            lines.append(f"  {d.name}/ ({len(files)} files, {size_str}){marker}")

        if not lines:
            return "No projects found in .session/."

        return "Projects:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing projects: {e}"


def project_switch(name=""):
    """
    Switch to a different project. Creates it if it doesn't exist.
    Changes the active session context — conversation history, todos, jobs all switch.

    Args:
        name (str): Project name to switch to.

    Returns:
        Confirmation message with new project info.

    Example:
        Action: project_switch(name="my-feature")
    """
    try:
        from pathlib import Path
        import config as _cfg

        name = str(name).strip()
        if not name:
            return project_list()

        if '/' in name or '\\' in name or '..' in name:
            return "Error: project name cannot contain '/', '\\', or '..'"

        # Lazy import to avoid circular dependency
        try:
            import main as _main
            _setup_fn = getattr(_main, '_setup_session', None)
        except ImportError:
            _setup_fn = None

        if _setup_fn is None:
            try:
                import sys, os
                for mod_name in list(sys.modules.keys()):
                    if 'main' in mod_name.lower():
                        _setup_fn = getattr(sys.modules[mod_name], '_setup_session', None)
                        if _setup_fn:
                            break
            except Exception:
                pass

        if _setup_fn is None:
            return f"Error: Cannot find _setup_session function. Start the agent normally first."

        old_project = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
        session_dir = _setup_fn(name)
        new_project = getattr(_cfg, 'ACTIVE_PROJECT', name)

        # Count what's in the new project
        files = list(session_dir.rglob('*')) if session_dir else []
        file_count = sum(1 for f in files if f.is_file())

        return (
            f"✅ Switched project: {old_project} → {new_project}\n"
            f"   Session dir: {session_dir}\n"
            f"   Files: {file_count}"
        )
    except Exception as e:
        return f"Error switching project: {e}"


def project_create(name=""):
    """
    Create a new empty project under .session/<name>/ without switching to it.

    Args:
        name (str): Project name to create.

    Returns:
        Confirmation message.

    Example:
        Action: project_create(name="experiment-1")
    """
    try:
        from pathlib import Path

        name = str(name).strip()
        if not name:
            return "Error: 'name' is required."

        if '/' in name or '\\' in name or '..' in name:
            return "Error: project name cannot contain '/', '\\', or '..'"

        session_dir = Path.cwd() / '.session' / name
        if session_dir.exists():
            return f"Project '{name}' already exists at {session_dir}"

        session_dir.mkdir(parents=True, exist_ok=True)
        return f"✅ Created project '{name}' at {session_dir}"
    except Exception as e:
        return f"Error creating project: {e}"


def project_delete(name=""):
    """
    Delete a project and all its data. Cannot delete the active project.

    Args:
        name (str): Project name to delete.

    Returns:
        Confirmation message.

    Example:
        Action: project_delete(name="old-experiment")
    """
    try:
        import shutil
        from pathlib import Path
        import config as _cfg

        name = str(name).strip()
        if not name:
            return "Error: 'name' is required."

        if name == 'default':
            return "Error: Cannot delete the 'default' project."

        active = getattr(_cfg, 'ACTIVE_PROJECT', 'default')
        if name == active:
            return f"Error: Cannot delete the active project '{name}'. Switch to another project first."

        session_dir = Path.cwd() / '.session' / name
        if not session_dir.exists():
            return f"Project '{name}' does not exist."

        # Count files before deletion for confirmation
        files = [f for f in session_dir.rglob('*') if f.is_file()]
        shutil.rmtree(str(session_dir))

        return f"✅ Deleted project '{name}' ({len(files)} files removed)"
    except Exception as e:
        return f"Error deleting project: {e}"


# ─── Job Management Tools ──────────────────────────────────────────────────

def _get_jobs_dir():
    """Return the jobs directory for the current project."""
    from pathlib import Path
    import config as _cfg
    session_dir = getattr(_cfg, 'SESSION_DIR', '')
    if not session_dir:
        return None
    return Path(session_dir) / 'jobs'


def job_list():
    """
    List all jobs in the current project's jobs/ directory.

    Returns:
        Formatted list of jobs with status and details.

    Example:
        Action: job_list()
    """
    try:
        from pathlib import Path
        import json

        jobs_dir = _get_jobs_dir()
        if jobs_dir is None or not jobs_dir.is_dir():
            return "No jobs directory found for current project."

        jobs = sorted([d for d in jobs_dir.iterdir()
                       if d.is_dir() and d.name.startswith('job')])
        if not jobs:
            return "No jobs found in current project."

        lines = []
        for job_dir in jobs:
            # Try to read status file
            status = "unknown"
            info = ""
            status_file = job_dir / 'status.json'
            if status_file.exists():
                try:
                    data = json.loads(status_file.read_text(encoding='utf-8'))
                    status = data.get('status', 'unknown')
                    info = data.get('description', data.get('prompt', ''))[:60]
                except Exception:
                    pass
            elif (job_dir / 'output.txt').exists():
                status = "completed"
            elif (job_dir / 'error.txt').exists():
                status = "failed"

            # Count files
            file_count = sum(1 for f in job_dir.iterdir() if f.is_file())
            icon = {"running": "🔄", "completed": "✅", "failed": "❌", "pending": "⏳"}.get(status, "📋")
            lines.append(f"  {icon} {job_dir.name}/ ({status}, {file_count} files)")
            if info:
                lines.append(f"     {info}")

        return f"Jobs in current project:\n" + "\n".join(lines)
    except Exception as e:
        return f"Error listing jobs: {e}"


def job_status(job_id=""):
    """
    Get detailed status of a specific job.

    Args:
        job_id (str): Job identifier (e.g., "job1", "1", or full path).

    Returns:
        Detailed job information including output if completed.

    Example:
        Action: job_status(job_id="job1")
        Action: job_status(job_id="1")
    """
    try:
        from pathlib import Path
        import json

        job_id = str(job_id).strip()
        if not job_id:
            return job_list()

        # Normalize: "1" → "job1"
        if job_id.isdigit():
            job_id = f"job{job_id}"

        jobs_dir = _get_jobs_dir()
        if jobs_dir is None:
            return "No session context. Start a session first."

        job_dir = jobs_dir / job_id
        if not job_dir.is_dir():
            return f"Job '{job_id}' not found in {jobs_dir}"

        lines = [f"Job: {job_id}", f"Path: {job_dir}"]

        # Status file
        status_file = job_dir / 'status.json'
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding='utf-8'))
                lines.append(f"Status: {data.get('status', 'unknown')}")
                for key in ('description', 'prompt', 'agent', 'started_at', 'completed_at', 'error'):
                    if key in data:
                        val = str(data[key])[:200]
                        lines.append(f"{key}: {val}")
            except Exception as e:
                lines.append(f"Status file parse error: {e}")

        # List all files in job dir
        files = sorted(job_dir.iterdir())
        lines.append(f"Files ({len(files)}):")
        for f in files:
            size = f.stat().st_size if f.is_file() else 0
            lines.append(f"  {f.name} ({size} bytes)")

        # Show output if exists and small
        output_file = job_dir / 'output.txt'
        if output_file.exists():
            content = output_file.read_text(encoding='utf-8', errors='replace')
            if len(content) > 2000:
                lines.append(f"\nOutput (truncated, {len(content)} bytes total):")
                lines.append(content[:2000] + "\n...")
            else:
                lines.append(f"\nOutput:")
                lines.append(content)

        return "\n".join(lines)
    except Exception as e:
        return f"Error getting job status: {e}"


def job_output(job_id=""):
    """
    Read the full output of a completed job.

    Args:
        job_id (str): Job identifier (e.g., "job1" or "1").

    Returns:
        Full job output text.

    Example:
        Action: job_output(job_id="job1")
    """
    try:
        from pathlib import Path

        job_id = str(job_id).strip()
        if not job_id:
            return "Error: 'job_id' is required. Use job_list() to see available jobs."

        if job_id.isdigit():
            job_id = f"job{job_id}"

        jobs_dir = _get_jobs_dir()
        if jobs_dir is None:
            return "No session context."

        job_dir = jobs_dir / job_id
        if not job_dir.is_dir():
            return f"Job '{job_id}' not found."

        # Try output.txt first, then result.json
        output_file = job_dir / 'output.txt'
        if output_file.exists():
            content = output_file.read_text(encoding='utf-8', errors='replace')
            if len(content) > 8000:
                return f"[Output truncated: {len(content)} bytes total]\n\n{content[:8000]}\n\n... ({len(content) - 8000} more bytes)"
            return content

        result_file = job_dir / 'result.json'
        if result_file.exists():
            return result_file.read_text(encoding='utf-8', errors='replace')

        # Fallback: list all text files
        text_files = [f for f in sorted(job_dir.iterdir())
                      if f.is_file() and f.suffix in ('.txt', '.json', '.md', '.log')]
        if text_files:
            parts = []
            for f in text_files:
                content = f.read_text(encoding='utf-8', errors='replace')
                if len(content) > 3000:
                    content = content[:3000] + "\n..."
                parts.append(f"=== {f.name} ===\n{content}")
            return "\n\n".join(parts)

        return f"No output files found in job '{job_id}'."
    except Exception as e:
        return f"Error reading job output: {e}"


def job_cancel(job_id=""):
    """
    Cancel a running job by writing a cancel marker file.

    Args:
        job_id (str): Job identifier (e.g., "job1" or "1").

    Returns:
        Confirmation message.

    Example:
        Action: job_cancel(job_id="job1")
    """
    try:
        from pathlib import Path
        import json
        import time

        job_id = str(job_id).strip()
        if not job_id:
            return "Error: 'job_id' is required."

        if job_id.isdigit():
            job_id = f"job{job_id}"

        jobs_dir = _get_jobs_dir()
        if jobs_dir is None:
            return "No session context."

        job_dir = jobs_dir / job_id
        if not job_dir.is_dir():
            return f"Job '{job_id}' not found."

        # Check if already completed
        status_file = job_dir / 'status.json'
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding='utf-8'))
                if data.get('status') in ('completed', 'failed'):
                    return f"Job '{job_id}' is already {data['status']}. Cannot cancel."
            except Exception:
                pass

        # Write cancel marker
        cancel_file = job_dir / 'cancel'
        cancel_file.write_text(str(int(time.time())), encoding='utf-8')

        # Update status
        if status_file.exists():
            try:
                data = json.loads(status_file.read_text(encoding='utf-8'))
                data['status'] = 'cancelled'
                status_file.write_text(json.dumps(data, indent=2), encoding='utf-8')
            except Exception:
                pass

        return f"✅ Cancel signal sent to job '{job_id}'."
    except Exception as e:
        return f"Error cancelling job: {e}"


# ─── Image Read Tool ────────────────────────────────────────────────────

def read_image(path=None, prompt="Describe this image in detail."):
    """Analyze an image file through the current multimodal LLM client."""
    from core.image_read import read_image as _read_image

    return _read_image(
        path=path,
        prompt=prompt,
        normalize_tool_path=_normalize_tool_path,
        resolve_asset_path=_resolve_asset_path,
        find_git_root=_find_git_root,
    )


# ── ask_user — interactive question/answer through the GUI ─────────
# The GUI (atlas_ui.py) installs a callback via set_ask_user_callback().
# When ask_user is invoked from the agent, the callback opens a question
# card on the frontend, blocks the agent thread until the user submits,
# and returns the submitted answer as the tool observation.
_ask_user_callback = None
_record_ssot_qa_callback = None
_dispatch_workflow_callback = None
_read_pipeline_state_callback = None
# Same callback pattern as `_dispatch_workflow_callback` /
# `_read_pipeline_state_callback`: atlas_api_jobs registers this during
# `register_jobs_routes` so the direct dispatch path can lazy-start a
# cold worker before `worker_call` opens its socket. Signature:
# (worker_url, workflow, project_root) -> None.
_ensure_lazy_worker_callback = None
# Installed by the worker (session_worker) so static command-gate failures can
# surface a human-facing notice in the chat content stream. Without this, a
# failed gate (e.g. a req finalize/lock checker) only returns its reason to the
# LLM as a tool result and silently loops via on_reject — the user watching the
# session never sees WHY it is stuck. Signature: (text, cls) -> None.
_emit_user_notice_callback = None


def _emit_user_notice(text: str, cls: str = "") -> None:
    """Best-effort: push a human-facing notice to the UI content stream.

    No-op when no callback is installed (CLI/headless). Never raises into the
    caller — surfacing a notice must not break the tool that triggered it.
    """
    cb = _emit_user_notice_callback
    if cb is None:
        return
    try:
        cb(str(text), cls)
    except TypeError:
        try:
            cb(str(text))
        except Exception:
            pass
    except Exception:
        pass


def _ask_user_exec_mode() -> str:
    """Return ask_user execution mode: interactive|pipeline|ci|auto-select."""
    mode = str(os.getenv("ASK_USER_EXEC_MODE", "interactive")).strip().lower()
    if mode in {"auto", "autoselect", "auto_select"}:
        mode = "auto-select"
    if mode not in ("interactive", "pipeline", "ci", "auto-select"):
        return "interactive"
    return mode


def _suggestion_from_text(text: str) -> str:
    match = re.search(r"\bSuggest:\s*([^\n.;]+)", str(text or ""), flags=re.IGNORECASE)
    return match.group(1).strip(" `\"'") if match else ""


def _contains_phrase(haystack: str, needle: str) -> bool:
    needle = str(needle or "").strip().lower()
    if not needle:
        return False
    return re.search(rf"(?<![a-z0-9_]){re.escape(needle)}(?![a-z0-9_])", str(haystack or "").lower()) is not None


def _option_rank(option: dict, suggestion: str) -> tuple[int, int]:
    label = str(option.get("label") or option.get("id") or "")
    detail = str(option.get("detail") or "")
    option_id = str(option.get("id") or "")
    text = f"{option_id} {label} {detail}".lower()
    suggested = str(suggestion or "").lower()
    if suggested and (
        _contains_phrase(text, suggested)
        or _contains_phrase(suggested, label)
        or _contains_phrase(suggested, option_id)
    ):
        return (0, 0)
    if option.get("recommended") is True or option.get("default") is True:
        return (1, 0)
    if "recommended" in text or "suggest" in text or "default" in text:
        return (2, 0)
    return (9, 0)


def _auto_select_one_question(question: dict) -> dict:
    """Return a synthetic ask_user answer for pipeline smoke tests.

    This is intentionally simple and reviewable: follow an explicit
    ``Suggest:`` hint when present, then any recommended/default option, then
    the first option. Free-form inputs use the suggestion/default text.
    """
    qkind = str(question.get("kind") or "single").lower()
    opts = _normalize_options(question.get("options"))
    suggestion = ""
    for key in ("subtitle", "detail", "criteria", "question"):
        suggestion = _suggestion_from_text(str(question.get(key) or ""))
        if suggestion:
            break
    reason = "suggestion" if suggestion else "first safe default"
    if qkind in {"single", "multi"} and opts:
        ranked = sorted(enumerate(opts), key=lambda item: (_option_rank(item[1], suggestion), item[0]))
        top_rank = _option_rank(ranked[0][1], suggestion)[0]
        if top_rank == 0:
            reason = "suggestion"
        elif top_rank <= 2:
            reason = "recommended/default"
        else:
            reason = "first safe default"
        if qkind == "multi":
            selected = [
                opt.get("id")
                for _idx, opt in ranked
                if _option_rank(opt, suggestion)[0] <= 2
            ] or [ranked[0][1].get("id")]
        else:
            selected = [ranked[0][1].get("id")]
        return {
            "selected": [str(item) for item in selected if item is not None],
            "custom": "",
            "auto_selected": True,
            "auto_select_reason": reason,
        }

    default_text = ""
    for key in ("default", "suggested_answer", "suggestion", "recommended", "value", "placeholder"):
        value = question.get(key)
        if isinstance(value, str) and value.strip():
            default_text = value.strip()
            reason = key
            break
    if not default_text:
        default_text = suggestion or "Auto-selected default; verify in QA Review before signoff."
    return {
        "selected": [],
        "custom": default_text,
        "auto_selected": True,
        "auto_select_reason": reason,
    }


def auto_select_ask_user_answer(
    question=None,
    options=None,
    kind="single",
    subtitle="",
    questions=None,
):
    """Build the synthetic answer payload used by ask_user auto-select mode."""
    if questions:
        return {"answers": [_auto_select_one_question(dict(q)) for q in questions]}
    return _auto_select_one_question({
        "question": question or "",
        "kind": kind,
        "options": options or [],
        "subtitle": subtitle or "",
    })


def _format_auto_answer(answer: dict, options=None) -> str:
    selected = answer.get("selected") or []
    labels = {
        str(opt.get("id")): str(opt.get("label") or opt.get("id"))
        for opt in (options or [])
        if isinstance(opt, dict)
    }
    parts = []
    if selected:
        parts.append("selected: " + ", ".join(labels.get(str(item), str(item)) for item in selected))
    custom = str(answer.get("custom") or "").strip()
    if custom:
        parts.append("note: " + custom)
    reason = str(answer.get("auto_select_reason") or "").strip()
    if reason:
        parts.append("auto_select_reason: " + reason)
    return " · ".join(parts) if parts else "(auto-selected with no explicit value)"


def set_ask_user_callback(cb):
    """Install the GUI bridge for ask_user. Call once at server boot."""
    global _ask_user_callback
    _ask_user_callback = cb


def set_record_ssot_qa_callback(cb):
    """Install the GUI bridge for deferred SSOT QA recording."""
    global _record_ssot_qa_callback
    _record_ssot_qa_callback = cb


def set_dispatch_workflow_callback(cb):
    """Install the ATLAS Pipeline bridge for orchestrator worker dispatch."""
    global _dispatch_workflow_callback
    _dispatch_workflow_callback = cb


def set_read_pipeline_state_callback(cb):
    """Install the ATLAS Pipeline bridge for in-process state reads."""
    global _read_pipeline_state_callback
    _read_pipeline_state_callback = cb


def set_ensure_lazy_worker_callback(cb):
    """Install the lazy-worker hook used by the direct dispatch path."""
    global _ensure_lazy_worker_callback
    _ensure_lazy_worker_callback = cb


def set_emit_user_notice_callback(cb):
    """Install the UI bridge for human-facing tool notices (gate failures)."""
    global _emit_user_notice_callback
    _emit_user_notice_callback = cb


# Pipeline stages copied into each IP folder + documented in its runbook.
# Order is the canonical SSOT→signoff flow. Only stages that exist in the
# central workflow/ tree are copied; missing ones are silently skipped.
_IP_WORKFLOW_STAGES = (
    "ssot-gen", "fl-model-gen", "rtl-gen", "tb-gen", "sim",
    "lint", "coverage", "syn", "sta", "pnr", "sta-post",
    "contract-reflection",
)
_IP_WIKI_GENERATED_DIR = "_generated"
_IP_WIKI_USER_DIR = "user"


def _central_workflow_root():
    """Resolve the central workflow/ script tree (single source of stages)."""
    from pathlib import Path
    raw = os.path.expandvars((os.environ.get("ATLAS_WORKFLOW_ROOT") or "").strip())
    if raw and "${" not in raw and os.path.isdir(raw):
        return Path(raw)
    home = os.environ.get("COMMON_AI_AGENT_HOME")
    base = Path(home) if home else Path(__file__).resolve().parents[1]
    return base / "workflow"


def _render_ip_workflow_runbook(name: str) -> str:
    """Executable per-IP runbook: SSOT→FL→RTL→TB→SIM→LINT→signoff.

    Commands reference the IP-local copy under <ip>/workflow/<stage>/scripts/
    and run from the project root with `<ip> --root .`. Cross-links the project
    wiki and (when configured) the external previous-project RTL DB wiki.
    """
    rtl_db = resolve_rtl_db_wiki()
    if rtl_db is not None:
        rtl_db_line = f"- **Previous-project RTL DB (external link):** [`{rtl_db}`]({rtl_db})"
    else:
        rtl_db_line = (
            "- **Previous-project RTL DB (external link):** _not configured_ — set "
            "`ATLAS_RTL_DB_WIKI` in `.config` to a prior project's RTL wiki "
            "(dir or .md) to link reference designs here."
        )
    stages = [
        ("ssot-gen", "SSOT", "Single Source of Truth from spec/import evidence.",
         f"python3 workflow/ssot-gen/scripts/check_ssot_disk.py {name}",
         f"yaml/{name}.ssot.yaml"),
        ("fl-model-gen", "FL-Model", "Functional/reference model + equivalence goals from SSOT.",
         f'python3 workflow/fl-model-gen/scripts/check_fl_model_artifacts.py {name} --root .',
         f"model/, equivalence goals"),
        ("rtl-gen", "RTL", "Synthesizable RTL authored from SSOT (+ FL equivalence).",
         f"python3 workflow/rtl-gen/scripts/check_rtl_disk.py {name}",
         f"rtl/{name}.sv, list/{name}.f, rtl/rtl_authoring_provenance.json"),
        ("tb-gen", "TB", "cocotb/pyuvm testbench from SSOT test_requirements.",
         f"python3 workflow/tb-gen/scripts/sim.py {name}",
         f"tb/cocotb/test_{name}.py, tb_manifest.json"),
        ("sim", "SIM", "Compile + run simulation, scoreboard, report.",
         f"python3 workflow/sim/scripts/run_sim.py {name} --root .",
         f"sim/ (waves, logs, results)"),
        ("lint", "LINT", "RTL lint — fix errors/warnings, emit report.",
         f"python3 workflow/lint/scripts/dut_lint_report.py {name} --root .",
         f"lint/ (lint report)"),
    ]
    lines = [
        f"# {name} — Workflow Runbook",
        "",
        f"Self-contained, executable flow for IP `{name}`. The full workflow "
        f"engine is copied into `../workflow/` at scaffold time — every stage's "
        f"scripts, prompts, `system_prompt.md`, rules, and todo templates, plus "
        f"the shared `scripts/`/`prompts/` and the flow guides. The IP runs "
        f"on its own, with no dependency on the central checkout's project wiki. "
        f"Run commands from the **project root** (the dir containing `{name}/`).",
        "",
        "## Pointers (all in-IP — only the RTL DB is an external link)",
        "- **Stage knowledge graph:** [[workflow-stages]] — per-stage how-to "
        "(SSOT structure, lint/sim method, scripts, prompts) as a queryable graph "
        "(`wiki_query(ip=\"" + name + "\")`).",
        "- **Flow guides (copied):** [`../workflow/GUIDE.md`](../workflow/GUIDE.md) · "
        "[`../workflow/COMMON_ENGINE_FLOW.md`](../workflow/COMMON_ENGINE_FLOW.md)",
        "- **Per-stage system prompts (copied):** `../workflow/<stage>/system_prompt.md`",
        f"- **This IP's wiki graph:** [`_graph.json`](./_graph.json) · "
        f"[`index.md`](./index.md)",
        rtl_db_line,
        "",
        "## Flow",
        "",
        "```",
        "SSOT → FL-Model → RTL → TB → SIM → LINT → (SYN → STA → PNR → STA-POST)",
        "```",
        "",
    ]
    for stage, label, purpose, cmd, outputs in stages:
        lines += [
            f"### {label} · `{stage}`",
            f"{purpose}",
            "",
            f"- **Scripts:** `workflow/{stage}/scripts/`",
            f"- **Run:** `{cmd}`",
            f"- **Outputs:** {outputs}",
            "",
        ]
    lines += [
        "## Signoff stages",
        "`coverage`, `syn`, `sta`, `pnr`, `sta-post` scripts are copied under "
        "`workflow/<stage>/scripts/` as well; drive them after SIM/LINT pass.",
        "",
        "## Provenance & versioning",
        "RTL/TB/SIM runs must reference immutable artifact versions "
        "(`rtl/rtl_authoring_provenance.json`, etc.). Do not overwrite old run "
        "results; new SSOT/RTL/TB gets new downstream runs.",
        "",
        "## Wiki ownership",
        f"- Refresh-owned pages live under `wiki/{_IP_WIKI_GENERATED_DIR}/`.",
        f"- User-authored development notes belong under `wiki/{_IP_WIKI_USER_DIR}/` "
        "or non-conflicting root `wiki/*.md` pages.",
        f"- `/refresh-wiki` overwrites only `wiki/{_IP_WIKI_GENERATED_DIR}/`; it "
        "never overwrites user-authored pages.",
        "",
    ]
    return "\n".join(lines) + "\n"


def _scaffold_ip_workflow(base, name, created_dirs, created_files, skipped_files):
    """Copy pipeline-stage workflow scripts into <ip>/workflow/ and write the
    per-IP execution runbook into <ip>/wiki/. Best-effort: missing central
    stages are skipped; existing destinations are preserved (never overwritten).
    Appends to the caller's created/skipped lists for the status report.
    """
    import shutil as _shutil
    from pathlib import Path

    central = _central_workflow_root()
    # ip_knowledge is copied FLAT into <ip>/wiki/ below (step 3), so keep it out
    # of the wholesale <ip>/workflow/ copy to avoid a redundant second copy.
    _ignore = _shutil.ignore_patterns("__pycache__", "*.pyc", "*.pyo", "ip_knowledge")

    # 1) Copy the WHOLE central workflow/ tree into <ip>/workflow/ so the IP is
    #    runnable on its own — every stage's scripts, prompts, system_prompt.md,
    #    rules, todo_templates, the shared scripts/ + prompts/, and the flow
    #    guides (GUIDE.md, COMMON_ENGINE_FLOW.md). Copy per top-level item so an
    #    existing destination is preserved rather than aborting the whole copy.
    if central.is_dir():
        dest_root = Path(base) / "workflow"
        dest_root.mkdir(parents=True, exist_ok=True)
        for item in sorted(central.iterdir()):
            if item.name == "__pycache__" or item.name.endswith((".pyc", ".pyo")):
                continue
            dst = dest_root / item.name
            if dst.exists():
                skipped_files.append(os.path.relpath(dst))
                continue
            if item.is_dir():
                _shutil.copytree(item, dst, ignore=_ignore)
                created_dirs.append(os.path.relpath(dst))
            else:
                _shutil.copy2(item, dst)
                created_files.append(os.path.relpath(dst))

    # 2) Write generated workflow wiki pages into <ip>/wiki/_generated/.
    #    User-authored development wiki pages live separately under
    #    <ip>/wiki/user/ (or non-conflicting root wiki/*.md pages). Refreshes
    #    overwrite only _generated/ so user notes are never clobbered.
    wiki_dir = Path(base) / "wiki"
    generated_dir = wiki_dir / _IP_WIKI_GENERATED_DIR
    user_dir = wiki_dir / _IP_WIKI_USER_DIR
    wiki_dir.mkdir(parents=True, exist_ok=True)
    for owned_dir in (generated_dir, user_dir):
        if owned_dir.exists():
            skipped_files.append(os.path.relpath(owned_dir))
        else:
            owned_dir.mkdir(parents=True, exist_ok=True)
            created_dirs.append(os.path.relpath(owned_dir))

    runbook = generated_dir / "workflow-runbook.md"
    if runbook.exists():
        skipped_files.append(os.path.relpath(runbook))
    else:
        runbook.write_text(_render_ip_workflow_runbook(name), encoding="utf-8")
        created_files.append(os.path.relpath(runbook))

    # 3) Copy the workflow knowledge-graph pages into the generated wiki area.
    #    build_graph.py reads this subdir recursively for IP graphs. Only the
    #    .md pages are copied — the IP rebuilds its own _graph.json.
    knowledge_src = central / "wiki" / "ip_knowledge"
    if knowledge_src.is_dir():
        for page in sorted(knowledge_src.glob("*.md")):
            dst = generated_dir / page.name
            if dst.exists():
                skipped_files.append(os.path.relpath(dst))
                continue
            _shutil.copy2(page, dst)
            created_files.append(os.path.relpath(dst))


def refresh_ip_wiki(name=None, root="."):
    """Refresh generated IP wiki pages without clobbering user wiki pages.

    Central workflow knowledge and the generated runbook are refresh-owned and
    live under <ip>/wiki/_generated/. User-authored development wiki belongs in
    <ip>/wiki/user/ or non-conflicting root <ip>/wiki/*.md pages. Refreshes only
    overwrite _generated/ and rebuild <ip>/wiki/_graph.json.
    """
    import re as _re
    import subprocess as _sp
    from pathlib import Path

    if not isinstance(name, str) or not name.strip():
        return "[refresh_ip_wiki: 'name' is required]"
    name = name.strip()
    if not _re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
        return f"[refresh_ip_wiki: invalid name {name!r} — letters, digits, underscore only]"
    if name == "default":
        # "default" is the agent's default workspace, not an IP. A caller that
        # resolves the active IP to "default" (e.g. no IP selected) must not
        # scaffold a bogus <root>/default/wiki tree — make it a no-op error.
        return ("[refresh_ip_wiki: 'default' is not an IP — open/select an IP "
                "first, or pass /refresh-wiki <ip>]")

    base = Path(os.path.abspath(os.path.join(root, name)))
    if not base.is_dir():
        return f"[refresh_ip_wiki: IP not found at {base} — create it with /new-ip first]"

    wiki_dir = base / "wiki"
    generated_dir = wiki_dir / _IP_WIKI_GENERATED_DIR
    user_dir = wiki_dir / _IP_WIKI_USER_DIR
    wiki_dir.mkdir(parents=True, exist_ok=True)
    generated_dir.mkdir(parents=True, exist_ok=True)
    user_dir.mkdir(parents=True, exist_ok=True)

    central = _central_workflow_root()
    knowledge_src = central / "wiki" / "ip_knowledge"
    written: list[str] = []
    migrated: list[str] = []

    def _preserve_flat_edit(page_name: str, generated_text: str) -> None:
        flat = wiki_dir / page_name
        user_copy = user_dir / page_name
        if not flat.is_file() or user_copy.exists():
            return
        try:
            flat_text = flat.read_text(encoding="utf-8")
        except Exception:
            return
        if flat_text == generated_text:
            return
        user_copy.write_text(flat_text, encoding="utf-8")
        migrated.append(page_name)

    if knowledge_src.is_dir():
        for page in sorted(knowledge_src.glob("*.md")):
            generated_text = page.read_text(encoding="utf-8")
            _preserve_flat_edit(page.name, generated_text)
            (generated_dir / page.name).write_text(generated_text, encoding="utf-8")
            written.append(f"{_IP_WIKI_GENERATED_DIR}/{page.name}")

    # Regenerate the runbook from the current template.
    runbook_text = _render_ip_workflow_runbook(name)
    _preserve_flat_edit("workflow-runbook.md", runbook_text)
    (generated_dir / "workflow-runbook.md").write_text(runbook_text, encoding="utf-8")
    written.append(f"{_IP_WIKI_GENERATED_DIR}/workflow-runbook.md")

    # Rebuild the IP wiki graph so wiki_query(ip=name) reflects the refresh.
    rebuilt = False
    builder = central / "wiki" / "build_graph.py"
    if builder.is_file():
        try:
            _sp.run(
                [sys.executable, str(builder), "--ip", name, "--project-root", str(base.parent)],
                check=False, capture_output=True, timeout=30,
            )
            rebuilt = True
        except Exception:
            pass

    preview = ", ".join(written[:6]) + ("…" if len(written) > 6 else "")
    return (
        f"✓ Refreshed {name}/wiki — overwrote {len(written)} generated file(s): {preview}"
        + (f"; preserved {len(migrated)} flat edit(s) under wiki/{_IP_WIKI_USER_DIR}/" if migrated else "")
        + (" + rebuilt graph index" if rebuilt else "")
    )


def scaffold_ip(name=None, root="."):
    """Create the canonical IP directory layout in the project root.

    Port placeholders use Verilog-2001 syntax while the file extension follows
    `config.RTL_FILE_EXT` and defaults to .sv by project convention:
      • .sv files, `input wire clk` / `reg`

    Layout (under `<root>/<name>/`, ext = .sv unless RTL_FILE_EXT overrides):
        yaml/<name>.ssot.yaml         # Single Source of Truth
        rtl/<name>.<ext>              # top-level RTL
        list/<name>.f                 # synthesis/sim filelist
        tb/cocotb/README.md           # tb-gen writes Python cocotb/pyuvm TB here
        tc/<name>_scenarios.py        # optional Python scenario notes
        sim/                          # simulation outputs (waves, logs)
        sdc/<name>.sdc                # synthesis constraints
        lint/                         # lint reports
        doc/<name>_mas.md             # micro-architecture spec
        req/<name>_requirements.md    # requirements

    Files are created with TBD/placeholder content; existing files are
    NOT overwritten — you can call this safely on an in-progress IP.

    Args:
        name: IP identifier (e.g. "axi_sram_bridge"). Required.
        root: Where to root the IP (default current dir, can be a subdir
              like "workflow" if your project nests IPs).
    """
    if not isinstance(name, str) or not name.strip():
        return "[scaffold_ip: 'name' is required]"
    name = name.strip()
    import re as __re
    if not __re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
        return f"[scaffold_ip: invalid name {name!r} — letters, digits, underscore only]"

    # Resolve project file extension. config is
    # imported lazily so this function works even when invoked outside the
    # main agent process (e.g. from a unit test).
    import sys as __sys
    _cfg = __sys.modules.get('config') or __sys.modules.get('src.config')
    _ext = getattr(_cfg, 'RTL_FILE_EXT', '.sv') if _cfg else '.sv'
    _ext = _ext if _ext in ('.v', '.sv') else '.sv'
    _dialect = 'verilog_2001'
    _port_kw = 'wire'

    base = os.path.abspath(os.path.join(root, name))
    layout = {
        "yaml": [(f"{name}.ssot.yaml",
                  f"# {name}.ssot.yaml — Single Source of Truth\n"
                  f"top_module:\n  name: {name}\n  type: \"<TBD>\"  # TBD\n"
                  f"  description: \"<TBD>\"  # TBD\n")],
        "rtl":  [(f"{name}{_ext}",
                  f"// {name}{_ext} — generated from {name}.ssot.yaml ({_dialect})\n"
                  f"// TODO: replace with Jinja2 / LLM output\n"
                  f"module {name} (\n  input  {_port_kw} clk,\n  input  {_port_kw} rst_n\n);\n"
                  f"  // TBD\nendmodule\n")],
        "list": [(f"{name}.f",
                  f"// {name}.f — filelist\nrtl/{name}{_ext}\n")],
        "tb/cocotb": [(f"README.md",
                  f"# {name} cocotb/pyuvm TB\n\n"
                  f"tb-gen owns this directory. Run `/tb {name}` or `/ssot-tb-cocotb {name}` "
                  f"after SSOT, FL, RTL, and equivalence goals exist.\n\n"
                  f"Expected generated files: `test_{name}.py`, `test_runner.py`, "
                  f"`tb_manifest.json`, and pyuvm support modules.\n")],
        "tc":   [(f"{name}_scenarios.py",
                  f"\"\"\"Scenario notes for {name}.\n\n"
                  f"tb-gen converts SSOT test_requirements into executable cocotb/pyuvm tests.\n"
                  f"Do not add SystemVerilog tc_* tasks in the default flow.\n"
                  f"\"\"\"\n\nSCENARIOS = []\n")],
        "sim":  [],
        "sdc":  [(f"{name}.sdc",
                  f"# {name}.sdc — timing constraints\n"
                  f"# TBD: create_clock, set_input_delay, ...\n")],
        "lint": [],
        "doc":  [(f"{name}_mas.md",
                  f"# {name} — Micro-Architecture Spec\n\n## TBD\n")],
        "req":  [(f"{name}_requirements.md",
                  f"# {name} — Requirements\n\n## TBD\n")],
    }

    created_dirs, created_files, skipped_files = [], [], []
    try:
        for sub, files in layout.items():
            d = os.path.join(base, sub)
            existed = os.path.isdir(d)
            os.makedirs(d, exist_ok=True)
            if not existed:
                created_dirs.append(os.path.relpath(d))
            for fn, body in files:
                fp = os.path.join(d, fn)
                if os.path.exists(fp):
                    skipped_files.append(os.path.relpath(fp))
                    continue
                # encoding="utf-8" is critical: the templates contain
                # em-dashes (—, U+2014). Without an explicit encoding,
                # Python falls back to locale.getpreferredencoding(),
                # which is cp949 on Korean macOS / Korean Windows and
                # can't encode em-dash → "cp949 codec can't encode
                # character —" crash from tool_dispatcher.
                with open(fp, "w", encoding="utf-8") as f:
                    f.write(body)
                created_files.append(os.path.relpath(fp))
    except OSError as e:
        return f"[scaffold_ip: filesystem error: {e}]"

    # Per-IP workflow scripts + execution runbook wiki. Non-fatal: a failure
    # here must not lose the canonical layout already written above.
    workflow_warn = ""
    try:
        _scaffold_ip_workflow(base, name, created_dirs, created_files, skipped_files)
    except Exception as e:  # noqa: BLE001 — best-effort enrichment
        workflow_warn = f"  ! workflow scripts/runbook skipped: {e}"

    # Display paths relative to the IP base (not cwd) so the listing
    # stays readable even when the user runs from far away.
    def _short(p):
        try:
            return os.path.relpath(p, base)
        except ValueError:
            return p
    out = [f"✓ Scaffolded IP '{name}' at {base}/"]
    if created_dirs:
        names = sorted(_short(d) for d in created_dirs)
        out.append(f"  + {len(created_dirs)} dirs: " + ", ".join(f"{n}/" for n in names))
    if created_files:
        out.append(f"  + {len(created_files)} files:")
        for fp in sorted(created_files):
            out.append(f"      {_short(fp)}")
    if skipped_files:
        out.append(f"  · {len(skipped_files)} kept (already existed):")
        for fp in sorted(skipped_files):
            out.append(f"      {_short(fp)}")
    if workflow_warn:
        out.append(workflow_warn)
    return "\n".join(out)


def ipxact_import(xml_path=None, ip_name=None, root=".", scaffold=True):
    """Import an IP-XACT (IEEE 1685) XML component into the project SSOT.

    Reads the XML at `xml_path`, converts the busInterfaces, parameters,
    memoryMap, model.ports → clocks/resets sections into our SSOT-lite
    YAML shape, and writes it under `<root>/<ip_name>/yaml/<ip_name>.ssot.yaml`.
    When `scaffold=True` (default) the surrounding IP layout (rtl/, sim/,
    tb/, list/, doc/, lint/) is created as well via scaffold_ip — but
    the SSOT YAML is overwritten by the imported content rather than the
    TBD placeholder.

    Args:
        xml_path: path to the source IP-XACT XML file. Required.
        ip_name:  override for top_module / IP directory name. Defaults
                  to the <ipxact:name> element from the XML.
        root:     where to root the IP (default: current dir).
        scaffold: also create the canonical IP layout (default: True).

    Returns:
        Human-readable status string with the resulting SSOT path.
    """
    if not isinstance(xml_path, str) or not xml_path.strip():
        return "[ipxact_import: 'xml_path' is required]"
    xml_path = _resolve_asset_path(xml_path)
    if not os.path.isfile(xml_path):
        return f"[ipxact_import: file not found: {xml_path}]"
    try:
        from core.ipxact_import import import_ipxact_file as _imp
    except Exception:
        try:
            from ipxact_import import import_ipxact_file as _imp  # type: ignore
        except Exception as e:
            return f"[ipxact_import: importer module unavailable: {e}]"

    # Peek at the SSOT first so we can derive the IP name when caller
    # didn't supply one (and the XML's <name> element is the canonical
    # source of truth in IP-XACT).
    try:
        peek = _imp(xml_path, ip_name=None)
    except Exception as e:
        return f"[ipxact_import: parse error: {e}]"
    name = (ip_name or peek.get("top_module") or "ipxact_import").strip()
    if not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", name):
        return f"[ipxact_import: invalid ip_name {name!r} — letters, digits, underscore only]"

    root = _normalize_tool_path(root)
    base = os.path.abspath(os.path.join(root, name))
    yaml_path = os.path.join(base, "yaml", f"{name}.ssot.yaml")

    # Optionally lay down the IP scaffold so RTL/sim/tb dirs exist for
    # subsequent rtl-gen / sim runs to drop their outputs into.
    scaffold_log = ""
    if _as_bool(scaffold, True):
        scaffold_log = scaffold_ip(name=name, root=root)

    # Now overwrite the placeholder SSOT YAML with the converted IP-XACT
    # content. import_ipxact_file does both the parse and the write.
    try:
        ssot = _imp(xml_path, ip_name=name, out_path=yaml_path)
    except Exception as e:
        return f"[ipxact_import: write error: {e}]"

    parts = [f"✓ Imported IP-XACT '{xml_path}' → {os.path.relpath(yaml_path)}"]
    origin = ssot.get("_ipxact_origin", {})
    if origin.get("vendor") or origin.get("library") or origin.get("version"):
        ident = ".".join(filter(None, [origin.get("vendor"), origin.get("library"),
                                       origin.get("name"), origin.get("version")]))
        if ident: parts.append(f"  origin: {ident}")
    parts.append(f"  top_module: {ssot.get('top_module')}")
    if ssot.get("busInterfaces"):
        parts.append(f"  busInterfaces: {len(ssot['busInterfaces'])}")
    if ssot.get("memoryMap"):
        parts.append(f"  memoryMap: {len(ssot['memoryMap'])}")
    if ssot.get("parameters"):
        parts.append(f"  parameters: {len(ssot['parameters'])}")
    if ssot.get("clocks"):
        parts.append(f"  clocks: {len(ssot['clocks'])}")
    if ssot.get("resets"):
        parts.append(f"  resets: {len(ssot['resets'])}")
    if scaffold_log:
        parts.append("")
        parts.append(scaffold_log)
    return "\n".join(parts)


# ────────────────────────────────────────────────────────────────────
# SoC Architect supervisor tools
# ────────────────────────────────────────────────────────────────────
# These operate on `<project_root>/soc.ssot.yaml` — the SoC-level SSOT
# the Architect supervisor owns. They read leaf SSOTs (per-IP) but
# never modify them.

def _arch_load_soc():
    """Load `<cwd>/soc.ssot.yaml` → dict, or {} if missing/unparseable."""
    try: import yaml as _yaml
    except ImportError:
        return None, "PyYAML not installed — install with `pip install pyyaml`"
    p = os.path.join(os.getcwd(), "soc.ssot.yaml")
    if not os.path.isfile(p):
        return None, f"soc.ssot.yaml not found at {p}"
    try:
        return _yaml.safe_load(open(p, "r", encoding="utf-8").read()) or {}, None
    except Exception as e:
        return None, f"parse error: {e}"


def _arch_parse_addr(s):
    """Parse '0x4000_2000' / '4000_2000' / 1073750016 → int, or None."""
    if isinstance(s, int): return s
    if not isinstance(s, str): return None
    t = s.strip().replace("_", "").replace("'", "")
    try:
        if t.lower().startswith("0x"): return int(t, 16)
        if t.lower().startswith("0b"): return int(t, 2)
        return int(t, 0)
    except (ValueError, TypeError):
        return None


def _arch_hex(n):
    """Pretty hex with 4-digit groups: 0x4000_2000."""
    if n is None: return "?"
    h = f"{n:x}"
    if len(h) > 4:
        rev = h[::-1]
        groups = [rev[i:i+4] for i in range(0, len(rev), 4)]
        h = "_".join(groups)[::-1]
    return f"0x{h}"


def addrmap_check():
    """Validate the SoC address map in `<cwd>/soc.ssot.yaml`.

    Runs the rules from `workflow/architect/rules/addrmap-checks.md`:
      • overlap detection
      • zero base reservation
      • range > 0
      • base alignment to range (power-of-2 decoder hygiene)
      • range power-of-2

    Returns a multi-line report. A single ✗ line indicates a hard error
    (the architect must halt and revert the offending edit).
    """
    soc, err = _arch_load_soc()
    if soc is None:
        return f"[addrmap_check: {err}]"
    addr_map = soc.get("addrMap") or []
    if not isinstance(addr_map, list) or not addr_map:
        return "[addrmap_check] addrMap is empty — nothing to validate"

    entries = []
    for e in addr_map:
        if not isinstance(e, dict): continue
        b = _arch_parse_addr(e.get("base"))
        r = _arch_parse_addr(e.get("range"))
        entries.append({"name": e.get("name") or "?", "base": b, "range": r, "raw": e})

    out = []
    hard = 0
    soft = 0

    # overlap
    es = sorted([e for e in entries if e["base"] is not None and e["range"]],
                key=lambda x: x["base"])
    overlap_msgs = []
    for i in range(len(es) - 1):
        a, b = es[i], es[i + 1]
        a_end = a["base"] + a["range"]
        if a_end > b["base"]:
            overlap_msgs.append(f"{a['name']} ({_arch_hex(a['base'])}+{_arch_hex(a['range'])}) "
                                f"overlaps {b['name']} ({_arch_hex(b['base'])})")
    if overlap_msgs:
        for m in overlap_msgs: out.append(f"✗ overlap        — {m}"); hard += 1
    else:
        out.append("✓ overlap        — clean")

    # zero base
    zb = [e for e in entries if e["base"] == 0]
    if zb:
        out.append(f"✗ zero base      — {zb[0]['name']} uses 0x0000_0000 (reserved)"); hard += 1
    else:
        out.append("✓ zero base      — clean")

    # range > 0
    bad_r = [e for e in entries if not e["range"] or e["range"] <= 0]
    if bad_r:
        out.append(f"✗ range > 0      — {bad_r[0]['name']} has range {bad_r[0]['raw'].get('range')}"); hard += 1
    else:
        out.append("✓ range > 0      — clean")

    # alignment: base % range == 0
    misalign = [e for e in entries
                if e["base"] is not None and e["range"]
                and (e["base"] % e["range"]) != 0]
    if misalign:
        for e in misalign:
            out.append(f"✗ alignment      — {e['name']} base {_arch_hex(e['base'])} "
                       f"not multiple of range {_arch_hex(e['range'])}"); hard += 1
    else:
        out.append("✓ alignment      — clean")

    # range power-of-2
    def _pow2(n): return n > 0 and (n & (n - 1)) == 0
    npo2 = [e for e in entries if e["range"] and not _pow2(e["range"])]
    if npo2:
        for e in npo2:
            out.append(f"⚠ range pow2     — {e['name']} range {_arch_hex(e['range'])} not power-of-2"); soft += 1
    else:
        out.append("✓ range pow2     — clean")

    # huge gap > 1 GiB
    gap_msgs = []
    for i in range(len(es) - 1):
        a, b = es[i], es[i + 1]
        gap = b["base"] - (a["base"] + a["range"])
        if gap > 0x4000_0000:
            gap_msgs.append(f"gap of {_arch_hex(gap)} between {a['name']} and {b['name']}")
    if gap_msgs:
        for m in gap_msgs: out.append(f"⚠ gap            — {m}"); soft += 1
    else:
        out.append("✓ gap            — clean")

    out.append("")
    out.append(f"summary: {hard} hard error(s), {soft} warning(s)" + (" — HALT" if hard else ""))
    return "\n".join(out)


def soc_status():
    """Print a one-screen overview of the current SoC composition.

    Shows clusters, instance count per cluster, address map summary,
    and per-IP pipeline status (ssot/rtl/sim derived from filesystem).
    Read-only. Useful as the architect's first move on any session.
    """
    soc, err = _arch_load_soc()
    if soc is None:
        return f"[soc_status: {err}]"
    name = soc.get("name") or "soc"
    version = soc.get("version") or "?"
    clusters = soc.get("clusters") or []
    instances = soc.get("instances") or []
    addr_map = soc.get("addrMap") or []
    connections = soc.get("connections") or []

    # Build inst lookup
    inst_by_id = {i.get("id"): i for i in instances if isinstance(i, dict) and i.get("id")}

    lines = [f"SoC: {name} v{version}",
             f"  clusters:    {len(clusters)}",
             f"  instances:   {len(instances)}",
             f"  connections: {len(connections)}",
             f"  addrMap:     {len(addr_map)} entries",
             ""]

    for c in clusters:
        if not isinstance(c, dict): continue
        cid = c.get("id") or c.get("name") or "?"
        members = c.get("members") or []
        role = c.get("role") or ""
        lines.append(f"┌── {cid} {('[' + role + ']') if role else ''} · {len(members)} IPs")
        for mid in members:
            inst = inst_by_id.get(mid) or {}
            leaf = inst.get("ssot") or ""
            addr = inst.get("addr") or ""
            # Status from leaf dir
            ip_dir = os.path.dirname(os.path.dirname(leaf)) if leaf else ""
            ssot_st = "ok" if (leaf and os.path.isfile(leaf)) else "·"
            rtl_dir = os.path.join(ip_dir, "rtl") if ip_dir else ""
            rtl_st = "ok" if (rtl_dir and os.path.isdir(rtl_dir) and
                              any(f.endswith(".sv") or f.endswith(".v") for f in os.listdir(rtl_dir))) else "·"
            sim_dir = os.path.join(ip_dir, "sim") if ip_dir else ""
            sim_st = "ok" if (sim_dir and os.path.isdir(sim_dir) and
                              any(f.endswith(".log") or f.endswith(".vcd")
                                  for f in os.listdir(sim_dir))) else "·"
            addr_n = _arch_parse_addr(addr) if isinstance(addr, str) else (addr if isinstance(addr, int) else None)
            addr_str = f" @ {_arch_hex(addr_n)}" if addr_n is not None else (f" @ {addr}" if addr else "")
            lines.append(f"│   {mid:<20s}  ssot:{ssot_st}  rtl:{rtl_st}  sim:{sim_st}{addr_str}")
        lines.append("└──")

    if addr_map:
        lines.append("")
        lines.append("addr map:")
        def _key(x):
            v = x.get("base")
            n = _arch_parse_addr(v) if isinstance(v, str) else (v if isinstance(v, int) else None)
            return n or 0
        for e in sorted([e for e in addr_map if isinstance(e, dict)], key=_key):
            b = e.get("base"); r = e.get("range")
            bn = _arch_parse_addr(b) if isinstance(b, str) else (b if isinstance(b, int) else None)
            rn = _arch_parse_addr(r) if isinstance(r, str) else (r if isinstance(r, int) else None)
            lines.append(f"  {(e.get('name') or '?'):<24s} {_arch_hex(bn)}  +{_arch_hex(rn)}")

    return "\n".join(lines)


def wrapper_gen(top_name=None):
    """Generate a top-level SystemVerilog wrapper from soc.ssot.yaml.

    Reads `instances`, their leaf SSOT `busInterfaces`, and `connections`,
    then emits a SystemVerilog top module that instantiates each IP and
    wires them per the connection list.

    Args:
        top_name: override for the top module name (defaults to
                  soc.ssot.yaml's `name` field).

    Output goes to `generators.top.output` from soc.ssot.yaml, falling
    back to `rtl/<top_name>.sv`.
    """
    soc, err = _arch_load_soc()
    if soc is None:
        return f"[wrapper_gen: {err}]"
    try: import yaml as _yaml
    except ImportError:
        return "[wrapper_gen: PyYAML not installed]"

    name = top_name or soc.get("name") or "soc_top"
    instances = soc.get("instances") or []
    connections = soc.get("connections") or []
    gen = (soc.get("generators") or {}).get("top") or {}
    out_path = gen.get("output") or f"rtl/{name}.sv"

    # Load each leaf SSOT to read busInterfaces.
    inst_ifaces = {}
    for inst in instances:
        if not isinstance(inst, dict): continue
        iid = inst.get("id"); leaf = inst.get("ssot")
        if not iid or not leaf or not os.path.isfile(leaf): continue
        try:
            doc = _yaml.safe_load(open(leaf, "r", encoding="utf-8").read()) or {}
        except Exception:
            doc = {}
        inst_ifaces[iid] = {
            "top": doc.get("top_module") or iid,
            "params": doc.get("parameters") or [],
            "ifaces": doc.get("busInterfaces") or [],
            "clocks": doc.get("clocks") or [],
            "resets": doc.get("resets") or [],
        }

    # Build the wrapper. This is a starter — generates instance
    # declarations + a comment block describing connections; users
    # iterate from here. (A full bus-matrix synthesis is a larger
    # effort tracked separately.)
    lines = [
        f"// Auto-generated top-level wrapper for SoC '{name}'.",
        f"// Source of truth: soc.ssot.yaml ({len(instances)} instances, "
        f"{len(connections)} connections)",
        "// Edit the SoC SSOT and re-run /wrapper-gen instead of editing this file.",
        "",
        f"module {name} (",
        "    input  wire clk,",
        "    input  wire rst_n",
        ");",
        "",
    ]
    for iid, info in inst_ifaces.items():
        lines.append(f"    // ─ {iid} ({info['top']})")
        lines.append(f"    {info['top']} u_{iid} (")
        lines.append(f"        .clk   (clk),")
        lines.append(f"        .rst_n (rst_n)")
        lines.append(f"        // TODO: hook bus interfaces ({len(info['ifaces'])} ifaces)")
        lines.append(f"    );")
        lines.append("")
    if connections:
        lines.append("    /* ─ connections (manual hookup pending) ─")
        for cn in connections:
            if not isinstance(cn, dict): continue
            lines.append(f"     *   {cn.get('from','?')} -> {cn.get('to','?')} "
                         f"({cn.get('proto','?')})")
        lines.append("     */")
        lines.append("")
    lines.append("endmodule")
    body = "\n".join(lines) + "\n"

    out_abs = os.path.abspath(out_path)
    os.makedirs(os.path.dirname(out_abs) or ".", exist_ok=True)
    try:
        with open(out_abs, "w", encoding="utf-8") as f:
            f.write(body)
    except OSError as e:
        return f"[wrapper_gen: write error: {e}]"
    return (f"✓ wrapper generated → {out_path}\n"
            f"  top module: {name}\n"
            f"  instances:  {len(instances)}\n"
            f"  connections (commented): {len(connections)}\n"
            f"  ⚠ bus hookup is TODO — review the file and fill in "
            f"the per-iface ports, then re-run.")


_DIRECT_WORKFLOW_FALLBACKS = {
    "ssot-gen",
    "fl-model-gen",
    "rtl-gen",
    "lint",
    "tb-gen",
    "sim",
    "coverage",
    "sim_debug",
    "syn",
    "sta",
    "pnr",
    "sta-post",
    "contract-reflection",
}

_DIRECT_WORKFLOW_ALIASES = {
    "fl-model": "fl-model-gen",
    "ssot-fl-model": "fl-model-gen",
    "cl": "fl-model-gen",
    "cl-model": "fl-model-gen",
    "cl-model-gen": "fl-model-gen",
    "cycle-model": "fl-model-gen",
    "ssot-cycle-model": "fl-model-gen",
    "equiv": "fl-model-gen",
    "equivalence": "fl-model-gen",
    "equiv-goals": "fl-model-gen",
    "equivalence-goals": "fl-model-gen",
    "ssot-equiv-goals": "fl-model-gen",
    "contract": "contract-reflection",
    "contract-check": "contract-reflection",
    "evidence-contract": "contract-reflection",
}

_DIRECT_STAGE_COMMANDS = {
    "fl-model": (),
    "fl-model-gen": (),
    "ssot-fl-model": (),
    "cl": ("ssot-cycle-model", "ssot-dual-fcov"),
    "cl-model": ("ssot-cycle-model", "ssot-dual-fcov"),
    "cl-model-gen": ("ssot-cycle-model", "ssot-dual-fcov"),
    "cycle-model": ("ssot-cycle-model", "ssot-dual-fcov"),
    "ssot-cycle-model": ("ssot-cycle-model", "ssot-dual-fcov"),
    "equiv": ("ssot-equiv-goals",),
    "equivalence": ("ssot-equiv-goals",),
    "equiv-goals": ("ssot-equiv-goals",),
    "equivalence-goals": ("ssot-equiv-goals",),
    "ssot-equiv-goals": ("ssot-equiv-goals",),
    "contract": ("contract-check",),
    "contract-check": ("contract-check",),
    "contract-reflection": ("contract-check",),
    "evidence-contract": ("contract-check",),
}


def _direct_needs_fl_authoring_instruction(workflow=None, stages=None):
    names = _normalize_dispatch_stages(stages)
    if workflow:
        names.insert(0, str(workflow).strip())
    return any(
        str(name or "").strip().lower()
        in {"fl-model", "fl-model-gen", "ssot-fl-model", "model-equivalence"}
        for name in names
    )


def _direct_needs_cl_symbol_contract_instruction(workflow=None, stages=None):
    names = _normalize_dispatch_stages(stages)
    if workflow:
        names.insert(0, str(workflow).strip())
    return any(
        str(name or "").strip().lower()
        in {"cl", "cl-model", "cl-model-gen", "cycle-model", "ssot-cycle-model", "model-equivalence"}
        for name in names
    )


def _normalize_dispatch_stages(stages):
    if not stages:
        return []
    if isinstance(stages, str):
        return [s.strip() for s in re.split(r"[,\s]+", stages) if s.strip()]
    if isinstance(stages, (list, tuple)):
        return [str(s).strip() for s in stages if str(s).strip()]
    return [str(stages).strip()]


def _direct_dispatch_target_for_name(name):
    key = str(name or "").strip()
    if not key:
        return ""
    return _DIRECT_WORKFLOW_ALIASES.get(key) or _DIRECT_WORKFLOW_ALIASES.get(key.lower()) or key


def _direct_dispatch_target(workflow, stages):
    workflow = str(workflow or "").strip()
    stage_list = _normalize_dispatch_stages(stages)
    stage_targets = [_direct_dispatch_target_for_name(s) for s in stage_list]
    stage_targets = [s for s in stage_targets if s]
    workflow_target = _direct_dispatch_target_for_name(workflow)
    if stage_targets:
        unique_targets = []
        for item in stage_targets:
            if item not in unique_targets:
                unique_targets.append(item)
        if len(unique_targets) != 1:
            return "", "direct fallback supports one concrete workflow only"
        if workflow_target and workflow_target in _DIRECT_WORKFLOW_FALLBACKS and workflow_target != unique_targets[0]:
            return "", "direct fallback supports one concrete workflow only"
        target = unique_targets[0]
    elif workflow_target:
        target = workflow_target
    elif stage_list:
        return "", "direct fallback supports one concrete workflow only"
    else:
        return "", "workflow is required"
    if target not in _DIRECT_WORKFLOW_FALLBACKS:
        return "", f"unknown direct workflow target: {target}"
    return target, ""


def _string_payload_value(payload, keys):
    if not isinstance(payload, dict):
        return ""
    for key in keys:
        value = payload.get(key)
        if isinstance(value, str) and value.strip():
            return value.strip()
    return ""


def _direct_stage_commands(workflow=None, stages=None):
    names = _normalize_dispatch_stages(stages)
    if workflow:
        names.insert(0, str(workflow).strip())
    commands = []
    for name in names:
        for command in _DIRECT_STAGE_COMMANDS.get(str(name or "").strip().lower(), ()):
            if command not in commands:
                commands.append(command)
    return commands


def _build_direct_dispatch_task(target, scope, prompt, ip, payload, schedule, run_mode, exec_mode, reason, workflow=None, stages=None):
    body = payload if isinstance(payload, dict) else {}
    task = str(prompt or "").strip() or _string_payload_value(
        body,
        (
            "prompt",
            "task",
            "user_goal",
            "goal",
            "requirement",
            "requirements",
            "context",
        ),
    )
    if not task:
        subject = ip or scope or "current scope"
        task = f"Run {target} for {subject}."

    if ip and target == "fl-model-gen" and _direct_needs_fl_authoring_instruction(workflow=workflow, stages=stages):
        fl_instruction = (
            f"FL authoring rule for {ip}: do not run /ssot-fl-model or emit_fl_model.py as the "
            f"authoring path. Read yaml/{ip}.ssot.yaml, author model/functional_model.py, "
            "model/decomposition.json, model/fl_model_check.json, and cov/fcov_plan.json directly "
            "from the SSOT, then run "
            f"python3 \"$ATLAS_WORKFLOW_ROOT/fl-model-gen/scripts/check_fl_model_artifacts.py\" {ip} "
            "--root \"$ATLAS_PROJECT_ROOT\" as the gate. Fix authored artifacts until that gate passes; "
            "if the SSOT is underspecified, emit [SSOT TBD REPORT] -> ssot-gen with exact YAML paths."
        )
        if fl_instruction not in task:
            task = f"{fl_instruction}\n\n{task}"

    if ip and target == "fl-model-gen" and _direct_needs_cl_symbol_contract_instruction(workflow=workflow, stages=stages):
        cl_instruction = (
            f"CL symbol contract rule for {ip}: every FL/CL rule symbol must be declared in "
            "required_fields, function_model.derived_signals, symbol_table, input_symbols, "
            "sample_context, state_variables, registers, or io_list before use. Do not invent "
            "undeclared cycle_model symbols. If "
            "model/cl_model_check.json reports symbol_contract.status=blocked, report "
            "failure_owner=fl-model-gen, stage=cl-model, and required_rerun instead of claiming DONE."
        )
        if cl_instruction not in task:
            task = f"{cl_instruction}\n\n{task}"

    commands = _direct_stage_commands(workflow=workflow, stages=stages)
    if commands and ip:
        command_lines = [f"/{command} {ip}" for command in commands]
        command_text = "\n".join(command_lines)
        if not any(line in task for line in command_lines):
            task = (
                "Run these stage command(s) on the target workflow before reporting DONE:\n"
                f"{command_text}\n\n"
                f"{task}"
            )

    header = []
    if ip:
        header.append(f"IP: {ip}")
    if scope:
        header.append(f"Scope: {scope}")
    if run_mode:
        header.append(f"Run mode: {run_mode}")
    if exec_mode:
        header.append(f"Exec mode: {exec_mode}")
    if schedule and schedule != "auto":
        header.append(f"Schedule: {schedule}")
    if reason:
        header.append(f"Reason: {reason}")
    if header:
        return "\n".join(header + ["", task])
    return task


def _direct_dispatch_session(target, ip="", scope=""):
    active = os.environ.get("ATLAS_ACTIVE_SESSION", "").strip()
    parts = [p for p in active.split("/") if p]
    owner = (
        os.environ.get("ATLAS_DEFAULT_SESSION_ID", "").strip()
        or os.environ.get("ATLAS_USER_SESSION_ID", "").strip()
        or (parts[0] if parts else "")
        or "default"
    )
    ip_name = str(ip or "").strip()
    if not ip_name and len(parts) >= 2:
        ip_name = parts[-2]
    if not ip_name and scope:
        ip_name = Path(str(scope).rstrip("/")).name
    ip_name = ip_name or "default"
    if len(parts) >= 4:
        workspace = parts[1]
        return f"{owner}/{workspace}/{ip_name}/{target}"
    return f"{owner}/{ip_name}/{target}"


def _truthy_env(name):
    return os.environ.get(name, "").strip().lower() in {"1", "true", "yes", "on"}


def _dispatch_workflow_direct_fallback(
    workflow=None,
    scope=None,
    prompt=None,
    ip=None,
    stages=None,
    payload=None,
    schedule="auto",
    model="",
    run_mode="",
    exec_mode="",
    reason="",
    force=False,
):
    target, reject_reason = _direct_dispatch_target(workflow, stages)
    if not target:
        return None, reject_reason

    try:
        try:
            from core.agent_client import _resolve_worker, worker_call, worker_start
        except Exception:
            from agent_client import worker_call, worker_start  # type: ignore
            _resolve_worker = None  # type: ignore
        try:
            from core.atlas_exec_policy import current_exec_mode, normalize_exec_mode
        except Exception:
            from atlas_exec_policy import current_exec_mode, normalize_exec_mode  # type: ignore

        effective_exec_mode = normalize_exec_mode(exec_mode) or current_exec_mode(os.environ)

        timeout_raw = os.environ.get("ATLAS_DIRECT_WORKER_TIMEOUT", "600")
        try:
            timeout = max(1, int(timeout_raw))
        except ValueError:
            timeout = 600
        task = _build_direct_dispatch_task(
            target=target,
            scope=scope or "",
            prompt=prompt or "",
            ip=ip or "",
            payload=payload,
            schedule=schedule or "auto",
            run_mode=run_mode or "",
            exec_mode=effective_exec_mode,
            reason=reason or "",
            workflow=workflow or "",
            stages=stages,
        )
        # Lazy-spawn the per-workflow worker if the orchestrator is the
        # first caller. Prefer the registered bridge; when the bridge was
        # never installed, fall back to atlas_api_jobs' small direct helper.
        session_name = _direct_dispatch_session(target, ip=ip or "", scope=scope or "")
        session_parts = [p for p in session_name.split("/") if p]
        session_owner = session_parts[0] if session_parts else ""
        resolved_url = target
        if callable(_resolve_worker):
            try:
                resolved_url = _resolve_worker(target)
            except Exception:
                resolved_url = target
        try:
            try:
                from src import atlas_api_jobs as _atlas_api_jobs  # type: ignore
            except Exception:
                import atlas_api_jobs as _atlas_api_jobs  # type: ignore
            resolve_for_job = getattr(_atlas_api_jobs, "_resolve_worker_url_for_job", None)
            if callable(resolve_for_job):
                scoped_url = resolve_for_job(
                    target,
                    session_name=session_name,
                    user_id=session_owner,
                    db_user_id=(
                        os.environ.get("ATLAS_ACTIVE_DB_USER_ID", "")
                        or os.environ.get("ATLAS_DB_USER_ID", "")
                    ),
                    exec_mode=effective_exec_mode,
                )
                if scoped_url:
                    resolved_url = scoped_url
        except Exception:
            pass
        lazy_project_root = _atlas_project_root() or os.getcwd()
        if _ensure_lazy_worker_callback is not None:
            try:
                _ensure_lazy_worker_callback(resolved_url, target, lazy_project_root)
            except Exception as exc:
                return {
                    "ok": False,
                    "source": "direct_worker_lazy_spawn_failed",
                    "workflow": target,
                    "worker": resolved_url,
                    "ip": ip or "",
                    "scope": scope or "",
                    "status": "error",
                    "result": {"error": f"lazy worker spawn failed: {exc}"},
                }, ""
        else:
            try:
                try:
                    from src import atlas_api_jobs as _atlas_api_jobs  # type: ignore
                except Exception:
                    import atlas_api_jobs as _atlas_api_jobs  # type: ignore
                ensure_direct = getattr(
                    _atlas_api_jobs,
                    "_ensure_lazy_worker_for_direct_dispatch",
                    None,
                )
                if callable(ensure_direct):
                    ensure_direct(resolved_url, target, lazy_project_root)
            except Exception as exc:
                return {
                    "ok": False,
                    "source": "direct_worker_lazy_spawn_failed",
                    "workflow": target,
                    "worker": resolved_url,
                    "ip": ip or "",
                    "scope": scope or "",
                    "status": "error",
                    "result": {"error": f"lazy worker spawn failed: {exc}"},
                }, ""
        project_root = lazy_project_root
        scope_path = ""
        if ip:
            scope_path = str(ip)
        elif scope:
            scope_path = str(scope)
        if _truthy_env("ATLAS_DIRECT_WORKER_SYNC"):
            result = worker_call(
                worker=resolved_url,
                task=task,
                model=model or "",
                workflow=target,
                timeout=timeout,
                show_log=False,
            )
            ok = isinstance(result, dict) and result.get("status") == "completed"
            status = result.get("status") if isinstance(result, dict) else ""
            run_id = result.get("run_id", "") if isinstance(result, dict) else ""
        else:
            result = worker_start(
                worker=resolved_url,
                task=task,
                model=model or "",
                workflow=target,
                session=session_name,
                ip=ip or "",
                project_root=project_root,
                source_root=os.environ.get("ATLAS_WORKFLOW_ROOT", ""),
                context=task.split("\n\n", 1)[0],
                run_mode=run_mode or "",
                exec_mode=effective_exec_mode,
                stage_id=_normalize_dispatch_stages(stages)[0] if _normalize_dispatch_stages(stages) else target,
                scope_path=scope_path,
                timeout=min(timeout, 30),
            )
            run_id = result.get("run_id", "") if isinstance(result, dict) else ""
            status = result.get("status", "") if isinstance(result, dict) else ""
            ok = bool(run_id) and status != "error"
        return {
            "ok": ok,
            "source": "direct_worker_fallback",
            "workflow": target,
            "worker": target,
            "worker_url": resolved_url,
            "ip": ip or "",
            "scope": scope or "",
            "session": session_name,
            "run_id": run_id,
            "status": status,
            "exec_mode": effective_exec_mode,
            "result": result,
        }, ""
    except Exception as exc:
        return None, f"direct worker fallback failed: {type(exc).__name__}: {exc}"


def dispatch_workflow(
    workflow=None,
    scope=None,
    prompt=None,
    ip=None,
    stages=None,
    payload=None,
    schedule="auto",
    model="",
    run_mode="",
    exec_mode="",
    reason="",
    force=False,
):
    """Hand a focused task to an ATLAS pipeline worker workflow.

    The Architect supervisor uses this to delegate per-IP work
    (rtl-gen, sim, lint, syn, sta, …) without leaving its own
    workflow. The sub-agent runs in its own conversation, returns its
    final summary, and the supervisor folds that summary into its
    own todo tracker.

    Args:
        workflow: target sub-workflow name (e.g. 'rtl-gen', 'sim').
        scope:    optional `/scope` path — typically the IP directory.
        prompt:   the user-facing instruction the sub-agent receives.

    In the Atlas UI this is bridged to the same job creator used by
    /api/pipeline/dispatch, so the orchestrator can dispatch workers
    without asking the user to switch workflows manually.
    """
    if not workflow and not stages:
        return "[dispatch_workflow: 'workflow' is required]"
    dispatch_payload = dict(payload) if isinstance(payload, dict) else {}
    if force:
        dispatch_payload["force"] = True
    if _dispatch_workflow_callback is not None:
        try:
            result = _dispatch_workflow_callback(
                workflow=workflow or "",
                scope=scope or "",
                prompt=prompt or "",
                ip=ip or "",
                stages=stages,
                payload=dispatch_payload,
                schedule=schedule or "auto",
                model=model or "",
                run_mode=run_mode or "",
                exec_mode=exec_mode or "",
                reason=reason or "",
            )
            try:
                return json.dumps(result, indent=2, sort_keys=True)
            except Exception:
                return str(result)
        except Exception as exc:
            return f"[dispatch_workflow error: {exc}]"
    direct_result, direct_skip_reason = _dispatch_workflow_direct_fallback(
        workflow=workflow or "",
        scope=scope or "",
        prompt=prompt or "",
        ip=ip or "",
        stages=stages,
        payload=dispatch_payload,
        schedule=schedule or "auto",
        model=model or "",
        run_mode=run_mode or "",
        exec_mode=exec_mode or "",
        reason=reason or "",
    )
    if direct_result is not None:
        try:
            return json.dumps(direct_result, indent=2, sort_keys=True)
        except Exception:
            return str(direct_result)
    parts = [f"⏵ Sub-workflow dispatch requested:",
             f"    workflow: {workflow}",
             f"    scope:    {scope or '(none)'}",
             f"    prompt:   {prompt or '(none)'}",
             "",
             *([f"Direct worker fallback skipped: {direct_skip_reason}", ""] if direct_skip_reason else []),
             "Currently this is a manual handoff — switch with:",
             f"    /workflow {workflow}",
             *([f"    /scope {scope}"] if scope else []),
             "    " + (prompt or "<user prompt>"),
             "",
             "Once the sub-agent dispatch path lands, the architect",
             "will run this in a child agent and fold the result back",
             "into its own conversation automatically."]
    return "\n".join(parts)


def _read_pipeline_state_env_fallback(ip="", scope="", include_jobs=True):
    ip_name = str(ip or "").strip()
    if not ip_name and scope:
        ip_name = os.path.basename(str(scope).rstrip("/"))
    if not ip_name or ip_name == "default":
        ip_name = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if not ip_name or not re.match(r"^[A-Za-z][A-Za-z0-9_]*$", ip_name):
        return None
    project_root = _atlas_project_root() or os.getcwd()
    ip_dir = os.path.join(project_root, ip_name)
    ssot_files = []
    yaml_dir = os.path.join(ip_dir, "yaml")
    if os.path.isdir(yaml_dir):
        for root, _dirs, files in os.walk(yaml_dir):
            for filename in files:
                if filename.endswith((".ssot.yaml", ".ssot.yml", "_ssot.yaml", "_ssot.yml")):
                    ssot_files.append(
                        _norm_rel_tool_path(os.path.relpath(os.path.join(root, filename), ip_dir))
                    )
    ssot_files = sorted(set(ssot_files))
    state = "passed" if ssot_files else "idle"
    return {
        "ok": True,
        "source": "read_pipeline_state_env_fallback",
        "ip": ip_name,
        "project_root": project_root,
        "ip_dir": ip_dir,
        "ip_exists": os.path.isdir(ip_dir),
        "active_jobs": [] if _as_bool(include_jobs, True) else [],
        "stages": {
            "ssot": {
                "state": state,
                "workflow": "ssot-gen",
                "evidence_paths": ssot_files,
                "active_jobs": [] if _as_bool(include_jobs, True) else [],
            }
        },
    }


def read_pipeline_state(ip=None, scope=None, include_jobs=True):
    """Read ATLAS Pipeline state through the in-process UI bridge.

    This avoids guessing localhost ports or using browser cookies from the LLM.
    In the Atlas UI, the callback returns DB/job/artifact-backed state for the
    requested IP. Outside the UI it returns a clear unavailable message.
    """
    requested_ip = str(ip or "").strip()
    env_ip = (os.environ.get("ATLAS_ACTIVE_IP", "") or "").strip()
    if (not requested_ip or requested_ip == "default") and env_ip and env_ip != "default":
        requested_ip = env_ip
    if _read_pipeline_state_callback is None:
        fallback = _read_pipeline_state_env_fallback(
            ip=requested_ip,
            scope=scope or "",
            include_jobs=include_jobs,
        )
        if fallback is None:
            return "[read_pipeline_state unavailable — running outside Atlas UI mode]"
        try:
            return json.dumps(fallback, indent=2, sort_keys=True)
        except Exception:
            return str(fallback)
    try:
        result = _read_pipeline_state_callback(
            ip=requested_ip,
            scope=scope or "",
            include_jobs=_as_bool(include_jobs, True),
        )
        try:
            return json.dumps(result, indent=2, sort_keys=True)
        except Exception:
            return str(result)
    except Exception as exc:
        return f"[read_pipeline_state error: {type(exc).__name__}: {exc}]"


def read_doc(path):
    """Convert a Word, PDF, PowerPoint, Excel, or HTML doc to markdown.

    Wraps Microsoft's `markitdown` so the agent can ingest PDFs and
    Office docs without dropping into a bespoke parser. Returns the
    extracted text as a single markdown string. Falls back to a clear
    error message when the library or file is missing.

    Args:
        path: relative or absolute filesystem path. Tilde expansion
              and absolute paths are honoured.
    """
    if not isinstance(path, str) or not path.strip():
        return "[read_doc: 'path' must be a non-empty string]"
    try:
        from markitdown import MarkItDown
    except Exception as e:
        return ("[read_doc: markitdown not available — pip install markitdown. "
                f"Underlying error: {e}]")
    p = _resolve_asset_path(path)
    if not os.path.exists(p):
        return f"[read_doc: file not found: {path}]"
    if not os.path.isfile(p):
        return f"[read_doc: not a file: {path}]"
    try:
        md = MarkItDown(enable_plugins=False)
        result = md.convert(p)
        text = (result.text_content or "").strip()
    except Exception as e:
        return f"[read_doc: conversion failed: {type(e).__name__}: {e}]"
    if not text:
        return f"[read_doc: empty result — file may be unsupported or scanned]"
    # Cap at ~32k chars so the response doesn't blow context.
    cap = 32_000
    if len(text) > cap:
        return text[:cap] + f"\n\n[…truncated, full doc {len(text)} chars]"
    return text


def _normalize_options(options):
    """Normalize options into a list of {id, label, detail?}."""
    norm = []
    for i, o in enumerate(options or []):
        if isinstance(o, str):
            norm.append({"id": f"opt_{i}", "label": o})
        elif isinstance(o, dict) and o.get("label"):
            item = {
                "id": str(o.get("id", f"opt_{i}")),
                "label": str(o["label"]),
                "detail": str(o.get("detail", "")) or None,
            }
            if "recommended" in o:
                item["recommended"] = bool(o.get("recommended"))
            if "default" in o:
                item["default"] = bool(o.get("default"))
            norm.append(item)
    return norm


def ask_user(question=None, options=None, kind="single", subtitle="",
             questions=None, id=None, section_id=None, section_title=None,
             section=None, section_name=None, decision_key=None,
             decision_label=None, field_path=None, qa_type=None,
             criteria=None, source_refs=None, sources=None, content=None,
             detail=None, placeholder=None, multiline=None):
    """Ask the user one or more questions through the GUI and wait for
    their answer(s).

    Two modes:
      • Single-question (default): pass `question` (+ optional `options`,
        `kind`, `subtitle`).
      • Batched: pass `questions=[{question, kind, options, subtitle},
        ...]` to ask multiple related questions at once. The user
        navigates between them with ← / → and submits all answers in
        one click. Use this when you have N related TBDs to resolve in
        one round-trip — much less disruptive than N sequential calls.

    Args:
        question:  Single-mode: the main question text.
        options:   Single-mode: list of strings or {id, label, detail?}.
        kind:      Single-mode: 'single' | 'multi' | 'input'.
        subtitle:  Single-mode: short explainer used as the breadcrumb
                   tab label in batch mode too.
        questions: Batched mode: list of dicts. Each dict has the same
                   keys as a single-question call.

    Returns:
        Plain-text summary of the user's answer(s).
    """
    _exec_mode = _ask_user_exec_mode()
    if _exec_mode == "auto-select" and _ask_user_callback is None:
        if questions:
            answer = auto_select_ask_user_answer(questions=questions)
            return "Auto-selected answers:\n" + "\n".join(
                f"  • {str(q.get('subtitle') or q.get('question') or '')[:40]}\n    "
                f"{_format_auto_answer(ans, _normalize_options(q.get('options')))}"
                for q, ans in zip(questions, answer.get("answers") or [])
            )
        answer = auto_select_ask_user_answer(question, _normalize_options(options), kind, subtitle)
        return "Auto-selected answer: " + _format_auto_answer(answer, _normalize_options(options))
    if _exec_mode == "pipeline":
        _label = (subtitle or question or "ask_user").strip()
        return (
            f"[ask_user blocked in pipeline mode: {_label}. "
            "Recorded as pending human input. Continue with non-blocking stages.]"
        )
    if _exec_mode == "ci":
        _label = (subtitle or question or "ask_user").strip()
        return (
            f"[ask_user blocked in ci mode: {_label}. "
            "Fail-fast required. Replace with deterministic defaults or pre-seeded answers.]"
        )

    if _ask_user_callback is None:
        return ("[ask_user unavailable — running outside GUI mode. "
                "Restate the question to the user in your reply instead.]")

    # ── Batched mode ─────────────────────────────────────────────────
    if questions:
        if not isinstance(questions, list) or not questions:
            return "[ask_user: 'questions' must be a non-empty list]"
        norm_qs = []
        for i, q in enumerate(questions):
            if not isinstance(q, dict):
                return f"[ask_user: questions[{i}] must be a dict]"
            qtext = q.get("question", "")
            if not isinstance(qtext, str) or not qtext.strip():
                return f"[ask_user: questions[{i}].question must be a non-empty string]"
            qkind = (q.get("kind") or "single").lower()
            if qkind not in ("single", "multi", "input"):
                return f"[ask_user: questions[{i}].kind invalid; use single|multi|input]"
            qopts = _normalize_options(q.get("options"))
            if qkind in ("single", "multi") and not qopts:
                return f"[ask_user: questions[{i}].kind={qkind!r} requires options]"
            norm_q = {
                "question": qtext,
                "kind": qkind,
                "options": qopts,
                "subtitle": q.get("subtitle", "") or "",
            }
            for meta_key in (
                "id", "section_id", "section_title", "section", "section_name",
                "decision_key", "decision_label", "field_path", "qa_type",
                "criteria", "source_refs", "sources", "content", "detail",
                "placeholder", "multiline",
            ):
                if meta_key in q:
                    norm_q[meta_key] = q.get(meta_key)
            norm_qs.append(norm_q)
        try:
            # Pass batch through the callback. Callbacks that don't
            # support batched mode receive only the first question to
            # stay backward-compatible.
            try:
                return _ask_user_callback(
                    norm_qs[0]["question"], norm_qs[0]["options"],
                    norm_qs[0]["kind"], norm_qs[0]["subtitle"],
                    questions=norm_qs,
                )
            except TypeError:
                # Callback doesn't accept questions kwarg → fall back to
                # sequential single-question calls and concatenate.
                parts = []
                for q in norm_qs:
                    r = _ask_user_callback(
                        q["question"], q["options"], q["kind"], q["subtitle"]
                    )
                    parts.append(f"[{q.get('subtitle') or q['question'][:30]}] {r}")
                return "\n".join(parts)
        except Exception as e:
            return f"[ask_user error: {type(e).__name__}: {e}]"

    # ── Single-question mode (legacy + optional metadata) ────────────
    if not isinstance(question, str) or not question.strip():
        return "[ask_user: 'question' must be a non-empty string]"
    kind = (kind or "single").lower()
    if kind not in ("single", "multi", "input"):
        return f"[ask_user: invalid kind={kind!r}; use single|multi|input]"
    norm_opts = _normalize_options(options)
    if kind in ("single", "multi") and not norm_opts:
        return f"[ask_user: kind={kind!r} requires non-empty options list]"
    try:
        meta = {
            "id": id,
            "section_id": section_id,
            "section_title": section_title,
            "section": section,
            "section_name": section_name,
            "decision_key": decision_key,
            "decision_label": decision_label,
            "field_path": field_path,
            "qa_type": qa_type,
            "criteria": criteria,
            "source_refs": source_refs,
            "sources": sources,
            "content": content,
            "detail": detail,
            "placeholder": placeholder,
            "multiline": multiline,
        }
        if any(value is not None for value in meta.values()):
            q = {
                "question": question,
                "kind": kind,
                "options": norm_opts,
                "subtitle": subtitle or "",
                **{k: v for k, v in meta.items() if v is not None},
            }
            return _ask_user_callback(question, norm_opts, kind, subtitle, questions=[q])
        return _ask_user_callback(question, norm_opts, kind, subtitle)
    except Exception as e:
        return f"[ask_user error: {type(e).__name__}: {e}]"


def record_ssot_qa(questions=None, ip=None, session=None, kind="",
                   source="llm-ssot-qna", status="pending",
                   question=None, options=None, subtitle="", id=None,
                   section_id=None, section_title=None, section=None,
                   section_name=None, decision_key=None, decision_label=None,
                   field_path=None, qa_type=None, criteria=None,
                   source_refs=None, sources=None, content=None, detail=None,
                   placeholder=None, multiline=None):
    """Record SSOT QA items in the GUI backlog without blocking for answers.

    This is the non-interrupting counterpart to ask_user. Use it when an
    SSOT agent has discovered questions, approvals, or change requests that
    should appear in the ATLAS SSOT QA preview but do not need to stop the
    current generation pass.
    """
    if _record_ssot_qa_callback is None:
        return ("[record_ssot_qa unavailable — running outside GUI mode. "
                "Summarize the deferred SSOT QA items in your reply instead.]")

    if questions is None and isinstance(question, str) and question.strip():
        meta = {
            "id": id,
            "section_id": section_id,
            "section_title": section_title,
            "section": section,
            "section_name": section_name,
            "decision_key": decision_key,
            "decision_label": decision_label,
            "field_path": field_path,
            "qa_type": qa_type,
            "criteria": criteria,
            "source_refs": source_refs,
            "sources": sources,
            "content": content,
            "detail": detail,
            "placeholder": placeholder,
            "multiline": multiline,
        }
        questions = [{
            "question": question,
            "kind": kind or "input",
            "options": options or [],
            "subtitle": subtitle or "",
            **{k: v for k, v in meta.items() if v is not None},
        }]

    if not isinstance(questions, list) or not questions:
        return "[record_ssot_qa: 'questions' must be a non-empty list]"

    norm_qs = []
    for i, q in enumerate(questions):
        if not isinstance(q, dict):
            return f"[record_ssot_qa: questions[{i}] must be a dict]"
        qtext = (
            q.get("question")
            or q.get("decision_label")
            or q.get("content")
            or q.get("detail")
            or ""
        )
        if not isinstance(qtext, str) or not qtext.strip():
            return f"[record_ssot_qa: questions[{i}] needs question/content/detail text]"
        qkind = str(q.get("kind") or "input").lower()
        if qkind not in ("single", "multi", "input"):
            qkind = "input"
        qopts = _normalize_options(q.get("options"))
        if qkind in ("single", "multi") and not qopts:
            qkind = "input"
        norm_q = {
            "question": qtext.strip(),
            "kind": qkind,
            "options": qopts,
            "subtitle": q.get("subtitle", "") or "",
        }
        for meta_key in (
            "id", "section_id", "section_title", "section", "section_name",
            "decision_key", "decision_label", "field_path", "qa_type",
            "criteria", "source_refs", "sources", "content", "detail",
            "placeholder", "multiline",
        ):
            if meta_key in q:
                norm_q[meta_key] = q.get(meta_key)
        norm_qs.append(norm_q)

    try:
        return _record_ssot_qa_callback(
            questions=norm_qs,
            ip=ip,
            session=session,
            kind=kind,
            source=source,
            status=status or "pending",
        )
    except Exception as e:
        return f"[record_ssot_qa error: {type(e).__name__}: {e}]"


def resolve_project_wiki_root(project_root):
    """Locate the project/dev wiki root.

    The dev wiki lives beside the central workflow/ tree (both under the
    common_ai_agent source root that --workflow-root / ATLAS_WORKFLOW_ROOT
    points at), so it is derived from there rather than a dedicated env var.
    Falls back to <project_root>/doc/wiki when that sibling does not exist.
    """
    from pathlib import Path as _Path

    cand = _central_workflow_root().parent / "doc" / "wiki"
    if cand.is_dir():
        return cand.resolve()
    return (_Path(project_root) / "doc" / "wiki").resolve()


def resolve_rtl_db_wiki():
    """Resolve the external 'previous project' RTL database wiki pointer.

    Reads ATLAS_RTL_DB_WIKI (.config). Returns a Path (dir or .md) when set and
    present on disk, else None. The per-IP workflow runbook links to this so RTL
    generation can consult prior-project reference designs.
    """
    import os as _os
    from pathlib import Path as _Path

    raw = _os.path.expandvars(
        (_os.environ.get("ATLAS_EXTERNAL_DB_WIKI") or _os.environ.get("ATLAS_RTL_DB_WIKI") or "").strip()
    )
    if not raw or "${" in raw:
        return None
    p = _Path(raw).expanduser()
    return p if p.exists() else None


def wiki_query(ip: str = "", topic: str = "", depth: int = 2, max_nodes: int = 12) -> str:
    """Read-only summary of the project wiki or a specific IP knowledge graph.

    ip="" → project/dev wiki (derived from --workflow-root, default common_ai_agent/doc/wiki)/_graph.json.
    ip="<name>" → <ip>/wiki/_graph.json. Falls back to ATLAS_ACTIVE_IP env.
                  Lazy-builds the graph by invoking
                  workflow/wiki/build_graph.py when the index is missing
                  or older than the IP directory.
    ip="rtl-db" → external previous-project RTL DB wiki configured by
                  ATLAS_RTL_DB_WIKI. If the env points at a corpus root with
                  a wiki/ child, the child is used.
    topic = case-insensitive keyword query matched against id / title / tags /
            path / status / digest / summary; empty matches everything.
    depth = 1 (id + title), 2 (+ status digest + meta), 3 (+ summary).
    max_nodes caps the rendered output to keep token cost predictable.
    Returns a compact markdown block. Read-only — never mutates wiki content.
    """
    import json as _json
    import os as _os
    import subprocess as _sp
    from pathlib import Path as _Path

    project_root = _Path(
        _os.environ.get("ATLAS_PROJECT_ROOT")
        or _os.environ.get("COMMON_AI_AGENT_HOME")
        or _os.getcwd()
    ).resolve()
    # Resolve the graph builder via the workflow root (--workflow-root), not
    # project_root — in split-root setups (--root=IP parent, --workflow-root=
    # the common_ai_agent checkout) build_graph.py is not under project_root.
    builder = _central_workflow_root() / "wiki" / "build_graph.py"

    ip = (ip or _os.environ.get("ATLAS_ACTIVE_IP") or "").strip()
    scope_kind = "project"
    scope_label = "scope=project"
    single_md_path: _Path | None = None
    graph: dict | None = None
    external_aliases = {
        "rtl-db",
        "rtl_db",
        "external-rtl-db",
        "external_rtl_db",
        "previous-rtl-db",
        "previous_rtl_db",
        "external-db",
        "external_db",
        "andes",
    }
    if ip.lower() in external_aliases:
        scope_kind = "rtl-db"
        scope_label = "scope=rtl-db"
        # External query adapter (maximum freedom — everything handled outside).
        # ATLAS_RTL_DB_QUERY points at an executable that OWNS the entire lookup:
        # its own structure, search, and transport (local files, a DB, an HTTP
        # service, a vector store…). ATLAS hands it the query as JSON on stdin and
        # returns its stdout verbatim — no _graph.json / wiki_graph schema needed.
        # Any language: a `.py` runs via python3, anything else runs directly
        # (e.g. a 3-line shell+curl wrapper to a remote service).
        query_cmd = _os.path.expandvars(
            (_os.environ.get("ATLAS_EXTERNAL_DB_QUERY") or _os.environ.get("ATLAS_RTL_DB_QUERY") or "").strip()
        )
        if query_cmd:
            cmd_path = _Path(query_cmd).expanduser()
            argv = ["python3", str(cmd_path)] if cmd_path.suffix == ".py" else [str(cmd_path)]
            payload = _json.dumps(
                {"ip": ip, "topic": topic, "depth": depth, "max_nodes": max_nodes}
            )
            try:
                proc = _sp.run(argv, input=payload, capture_output=True, text=True, timeout=90)
            except Exception as exc:
                return f"[wiki_query] external RTL DB query command failed: {exc}"
            out = (proc.stdout or "").strip()
            if proc.returncode != 0 and not out:
                err = (proc.stderr or "").strip()[:300]
                return f"[wiki_query] external RTL DB query exited {proc.returncode}: {err}"
            header = f"# wiki_query [scope=rtl-db · external query] topic={topic!r} depth={depth}\n"
            return header + (out or "(external RTL DB query returned no output)")
        rtl_db = resolve_rtl_db_wiki()
        if rtl_db is None:
            return "[wiki_query] ATLAS_RTL_DB_WIKI is not configured or the path does not exist."
        if rtl_db.is_file():
            single_md_path = rtl_db
            graph_path = rtl_db
            rebuild_cmd: list[str] = []
        else:
            candidates = []
            wiki_child = rtl_db / "wiki"
            if wiki_child.is_dir():
                candidates.append(wiki_child)
            candidates.append(rtl_db)
            wiki_root = next(
                (
                    cand
                    for cand in candidates
                    if (cand / "_graph.json").is_file() or any(cand.glob("*.md"))
                ),
                candidates[0],
            )
            graph_path = wiki_root / "_graph.json"
            # External override: ATLAS_RTL_DB_BUILDER points at a converter that
            # understands THIS wiki's (possibly foreign) structure and writes
            # <wiki_root>/_graph.json in the wiki_graph.v1 node schema. ATLAS runs
            # it instead of the built-in build_graph.py. Mirrors ATLAS_SCM_UI_OVERRIDE.
            ext_builder = _os.path.expandvars(
                (_os.environ.get("ATLAS_EXTERNAL_DB_BUILDER") or _os.environ.get("ATLAS_RTL_DB_BUILDER") or "").strip()
            )
            if ext_builder:
                ext_path = _Path(ext_builder).expanduser()
                if ext_path.suffix == ".py":
                    rebuild_cmd = ["python3", str(ext_path), "--wiki", str(wiki_root)]
                else:
                    rebuild_cmd = [str(ext_path), "--wiki", str(wiki_root)]
            else:
                rebuild_cmd = ["python3", str(builder), "--wiki", str(wiki_root), "--quiet"]
            # Bail only when there is nothing to read AND no way to produce it:
            # no graph, no markdown, and no external builder to convert the source.
            if not graph_path.is_file() and not any(wiki_root.glob("*.md")) and not ext_builder:
                return f"[wiki_query] external RTL DB wiki has no markdown files: {wiki_root}"
    elif ip:
        scope_kind = "ip"
        scope_label = f"ip={ip}"
        ip_root = project_root / ip
        if not ip_root.is_dir():
            return f"[wiki_query] IP directory not found: {ip}"
        graph_path = ip_root / "wiki" / "_graph.json"
        rebuild_cmd = [
            "python3",
            str(builder),
            "--ip",
            ip,
            "--project-root",
            str(project_root),
            "--quiet",
        ]
    else:
        wiki_root = resolve_project_wiki_root(project_root)
        graph_path = wiki_root / "_graph.json"
        rebuild_cmd = ["python3", str(builder), "--wiki", str(wiki_root), "--quiet"]

    if single_md_path is not None:
        try:
            raw = single_md_path.read_text(encoding="utf-8", errors="replace")
        except Exception as exc:
            return f"[wiki_query] cannot read {single_md_path}: {exc}"
        title = single_md_path.stem
        for line in raw.splitlines():
            if line.startswith("# "):
                title = line[2:].strip() or title
                break
        summary = " ".join(line.strip() for line in raw.splitlines() if line.strip() and not line.startswith("#"))[:360]
        graph = {
            "schema_version": "wiki_graph.v1",
            "node_count": 1,
            "edge_count": 0,
            "nodes": [
                {
                    "id": single_md_path.stem.lower(),
                    "title": title,
                    "type": "reference",
                    "tags": ["rtl-db", "external"],
                    "path": str(single_md_path),
                    "summary": summary,
                    "outgoing": [],
                }
            ],
        }
    else:
        # External override: ATLAS_RTL_DB_NO_REBUILD=1 → trust the _graph.json the
        # external system shipped (built by its own pipeline); never (re)build or
        # clobber it, even if its source files look newer to us.
        no_rebuild = (
            scope_kind == "rtl-db"
            and (_os.environ.get("ATLAS_EXTERNAL_DB_NO_REBUILD") or _os.environ.get("ATLAS_RTL_DB_NO_REBUILD") or "").strip().lower()
            in ("1", "true", "yes", "on")
        )
        needs_build = (not no_rebuild) and (not graph_path.is_file())
        if not no_rebuild and not needs_build:
            try:
                graph_mtime = graph_path.stat().st_mtime
                if scope_kind == "ip":
                    for sub in ("wiki", "yaml", "rtl", "sim", "lint", "cov", "verify", "logs", "model"):
                        sub_dir = project_root / ip / sub
                        if not sub_dir.is_dir():
                            continue
                        for child in sub_dir.rglob("*"):
                            if child.is_file() and child.stat().st_mtime > graph_mtime:
                                needs_build = True
                                break
                        if needs_build:
                            break
                else:
                    if scope_kind == "project":
                        wiki_root = resolve_project_wiki_root(project_root)
                    for child in wiki_root.glob("*.md"):
                        if child.is_file() and child.stat().st_mtime > graph_mtime:
                            needs_build = True
                            break
            except Exception:
                needs_build = True
        # rtl-db may use an external builder (rebuild_cmd already points to it);
        # other scopes require the built-in builder to exist.
        if needs_build and rebuild_cmd and (scope_kind == "rtl-db" or builder.is_file()):
            try:
                _sp.run(
                    rebuild_cmd,
                    check=False,
                    capture_output=True,
                    timeout=60 if scope_kind == "rtl-db" else 30,
                )
            except Exception:
                pass

        if not graph_path.is_file():
            return f"[wiki_query] graph index not found: {graph_path.relative_to(project_root) if project_root in graph_path.parents else graph_path}"
        try:
            graph = _json.loads(graph_path.read_text(encoding="utf-8"))
        except Exception as exc:
            return f"[wiki_query] cannot parse {graph_path.name}: {exc}"

    depth = max(1, min(3, int(depth) if isinstance(depth, int) else 2))
    max_nodes = max(1, min(40, int(max_nodes) if isinstance(max_nodes, int) else 12))
    topic_l = str(topic or "").strip().lower()
    topic_terms = [t for t in topic_l.replace("/", " ").replace("_", " ").split() if t]
    nodes = graph.get("nodes") or []

    def _match(node: dict) -> bool:
        if not topic_terms:
            return True
        haystack = " ".join(
            [
                str(node.get("id") or ""),
                str(node.get("title") or ""),
                " ".join(str(t) for t in node.get("tags") or []),
                str(node.get("type") or ""),
                str(node.get("path") or ""),
                str(node.get("status") or ""),
                str(node.get("digest") or ""),
                str(node.get("summary") or ""),
            ]
        ).replace("/", " ").replace("_", " ").lower()
        return all(term in haystack for term in topic_terms)

    def _score(node: dict) -> int:
        if not topic_terms:
            return 0
        nid = str(node.get("id") or "").replace("_", " ").lower()
        title = str(node.get("title") or "").replace("_", " ").lower()
        path = str(node.get("path") or "").replace("/", " ").replace("_", " ").lower()
        tags = " ".join(str(t) for t in node.get("tags") or []).replace("_", " ").lower()
        meta = " ".join(
            [
                str(node.get("type") or ""),
                str(node.get("status") or ""),
                str(node.get("digest") or ""),
            ]
        ).replace("_", " ").lower()
        summary = str(node.get("summary") or "").replace("/", " ").replace("_", " ").lower()
        score = 0
        for term in topic_terms:
            if term in nid:
                score += 8
            if term in title:
                score += 7
            if term in path:
                score += 5
            if term in tags:
                score += 4
            if term in meta:
                score += 3
            if term in summary:
                score += 2
        raw_path = str(node.get("path") or "")
        if node.get("id") == "index" or raw_path.endswith("/wiki/index.md") or raw_path.endswith("doc/wiki/index.md"):
            score += 20
        if "readme" in topic_terms and "README.md" in raw_path:
            score += 15
        return score

    matched = [n for n in nodes if _match(n)]
    matched.sort(
        key=lambda n: (
            _score(n),
            str(n.get("updated") or ""),
            str(n.get("id") or ""),
        ),
        reverse=True,
    )
    capped = matched[:max_nodes]

    lines: list[str] = [
        f"# wiki_query [{scope_label}] depth={depth} "
        f"matches={len(matched)}/{graph.get('node_count', len(nodes))} "
        f"shown={len(capped)}"
    ]
    for node in capped:
        nid = node.get("id") or "?"
        ntitle = node.get("title") or nid
        ntype = node.get("type") or "reference"
        status = node.get("status")
        digest = node.get("digest") or ""
        updated = node.get("updated") or ""
        path = node.get("path") or ""
        head = f"## {nid} [{ntype}]"
        if status:
            head += f" · status={status}"
        if updated:
            head += f" · updated={updated}"
        lines.append(head)
        if depth >= 2:
            meta_parts = [f"title: {ntitle}"]
            if path:
                meta_parts.append(f"path: {path}")
            if digest:
                meta_parts.append(f"digest: {digest}")
            tags = node.get("tags") or []
            if tags:
                meta_parts.append("tags: " + ", ".join(str(t) for t in tags))
            lines.append(" · ".join(meta_parts))
            outgoing = node.get("outgoing") or []
            if outgoing:
                lines.append("links: " + " ".join(f"[[{t}]]" for t in outgoing[:8]))
        if depth >= 3:
            summary = node.get("summary") or ""
            if summary:
                lines.append(summary)
    if len(matched) > len(capped):
        lines.append(
            f"\n…{len(matched) - len(capped)} more matches truncated. "
            f"Re-query with a narrower topic= or higher max_nodes."
        )
    if scope_kind == "rtl-db":
        drill_ip = "rtl-db"
        rebuild_hint = 'python3 workflow/wiki/build_graph.py --wiki "$ATLAS_RTL_DB_WIKI" --quiet'
    elif scope_kind == "ip":
        drill_ip = ip
        rebuild_hint = f"python3 workflow/wiki/build_graph.py --ip {ip}"
    else:
        drill_ip = ""
        rebuild_hint = "python3 workflow/wiki/build_graph.py --check"
    lines.append(
        f"\nDrill deeper with `wiki_query(ip={drill_ip!r}, topic=\"<keyword>\", depth=3)` "
        f"or re-run `{rebuild_hint}`."
    )
    return "\n".join(lines)


def external_db_query(topic: str = "", depth: int = 3, max_nodes: int = 12) -> str:
    return wiki_query(ip="external-db", topic=topic, depth=depth, max_nodes=max_nodes)


def verify_ssot(ip: str = "", mode: str = "engineering", root: str = "", preview: str = "strict") -> str:
    """Run the script-backed SSOT validator used by ssot-gen.

    The verifier checks canonical top-level YAML shape, ATLAS SSOT Preview
    fields, and check_ssot_disk.py. It writes <ip>/req/ssot_validation.json.
    """
    from pathlib import Path as _Path

    ip = str(ip or os.environ.get("ATLAS_ACTIVE_IP") or os.environ.get("IP_NAME") or "").strip()
    if not ip:
        return "[verify_ssot] IP name is required. Pass ip=... or set ATLAS_ACTIVE_IP."
    mode = str(mode or os.environ.get("ATLAS_RUN_MODE") or "engineering").strip()
    preview = str(preview or "strict").strip().lower()
    if preview not in {"strict", "warn", "off"}:
        preview = "strict"
    project_root = _Path(
        root
        or os.environ.get("ATLAS_PROJECT_ROOT")
        or os.environ.get("PROJECT_ROOT")
        or os.getcwd()
    ).resolve()
    source_root = _Path(os.environ.get("COMMON_AI_AGENT_HOME") or _Path(__file__).resolve().parents[1]).resolve()
    script = source_root / "workflow" / "ssot-gen" / "scripts" / "verify_ssot.py"
    if not script.is_file():
        return f"[verify_ssot] verifier script not found: {script}"
    try:
        proc = subprocess.run(
            [
                sys.executable,
                str(script),
                ip,
                "--root",
                str(project_root),
                "--mode",
                mode,
                "--preview",
                preview,
            ],
            cwd=str(project_root),
            text=True,
            encoding="utf-8",
            errors="replace",
            capture_output=True,
            timeout=120,
        )
    except Exception as exc:
        return f"[verify_ssot] failed to run verifier: {exc}"
    out = (proc.stdout or proc.stderr or "").strip()
    if len(out) > 12000:
        out = out[:12000] + "\n...[verify_ssot output truncated]"
    return out or f"[verify_ssot] verifier exited {proc.returncode} with no output"


def _sim_debug_siglist(signals, signal):
    """Normalize signals="a, b" + signal="c" into an ordered, deduped list."""
    out = []
    if signal:
        out.append(str(signal).strip())
    if signals:
        out += [t.strip() for t in re.split(r"[,\s]+", str(signals)) if t.strip()]
    seen, res = set(), []
    for x in out:
        if x and x not in seen:
            seen.add(x)
            res.append(x)
    return res


def sim_debug(action="", ip="", signals="", signal="", t_start=None, t_end=None,
              cursor_a=None, cursor_b=None, edge="rising", nth=1, at=None,
              group="", color="", scope="", radix=""):
    """Drive and query the ATLAS Sim Debug waveform panel from chat.

    The action both (a) returns analysis text to you and (b) updates the open
    Sim Debug panel (it polls for the latest intent). Use the active IP unless
    `ip` is given.

    Actions:
      show    — add signal(s) to the waveform. signals="a,b" or signal="a";
                optional scope="<VCD/instance scope>" disambiguates duplicates.
      goto    — zoom the view to [t_start, t_end] (ns); optional cursor_a/cursor_b.
      cursor  — place cursor A/B (cursor_a, cursor_b in ns).
      fit     — reset the view to the whole VCD.
      reorder — set the top-to-bottom row order. signals="a,b,c" (the listed
                signals lead in that order; the rest follow).
      group   — tag signals into a named, foldable group ABOVE them.
                group="name", signals="a,b", optional color="#rrggbb".
      ungroup — remove signal(s) from their group. signals="a,b".
      color   — recolor signal(s). color="#rrggbb", signals="a,b".
      radix   — set how a bus is rendered. radix=hex|dec|bin|fsm|off, signals="a,b".
                radix=fsm shows the parameter/enum NAME for matching values (the
                FSM/parameter-value display); radix=off clears the override.
      remove  — remove signal(s) from the waveform. signals="a,b".
      keep    — show ONLY the listed signals, removing every other currently
                displayed row (use for "I need only X"). signals="a,b".
      clear   — remove ALL signals from the waveform.
      fold / unfold — collapse / expand a group. group="name".
      trace   — pyslang: report a signal's driver + load sites (file:line) and
                show the trace in the panel. (signal=…)
      find    — VCD: time of a signal's edge (edge=rising|falling|any, nth=1),
                then jump the panel there with the signal shown. (signal=…, optional scope=…)
      value   — VCD: value of a signal at time `at` ns. (signal=…, at=…, optional scope=…)
    """
    from core.sim_debug_intent import push_intent
    act = str(action or "").strip().lower()
    ip = str(ip or os.environ.get("ATLAS_ACTIVE_IP", "")).strip()
    sig_scope = str(scope or "").strip()
    where = ip or "active IP"

    if act in ("show", "add"):
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug show: no signals given — pass signals=\"a,b\" or signal=\"a\"]"
        shown, not_dumped, notes = [], [], []
        try:
            from core.sim_debug_analyze import resolve_wave_signal
        except Exception:
            resolve_wave_signal = None
        for s in sigs:
            r = resolve_wave_signal(ip, s, sig_scope) if resolve_wave_signal else {"status": "unresolved"}
            status = r.get("status")
            if status == "resolved":
                shown.append(r.get("resolved_signal") or s)
                if r.get("resolved_signal") and r.get("resolved_signal") != s:
                    notes.append(f"{s}→{r.get('resolved_signal')}")
            elif status == "rtl_not_dumped":
                # Resolved in RTL but absent from the VCD. We still PUSH it: the
                # panel renders a "⚠ not in VCD" placeholder row (buildWaveTraceList)
                # so the user gets visible feedback instead of a silent no-op —
                # the message below says clearly it is a placeholder, not real data.
                not_dumped.append(r.get("resolved_signal") or s)
            elif status == "ambiguous":
                cands = [c.get("resolved_signal", "") for c in r.get("candidates", []) if c.get("resolved_signal")]
                notes.append(f"{s}: ambiguous ({', '.join(cands[:4])})")
            else:
                hints = r.get("did_you_mean") or []
                if hints:
                    notes.append(f"{s}: not resolved; candidates {', '.join(hints[:4])}")
                else:
                    notes.append(f"{s}: not resolved")
        # Push real + not-dumped so not-dumped pins render as "⚠ not in VCD"
        # placeholders (visible feedback); only ambiguous/unresolved are dropped.
        to_push = shown + not_dumped
        if not to_push:
            return f"[sim_debug show: no signal could be shown ({'; '.join(notes)})]"
        push_intent(ip, "show", signals=to_push, scope=(sig_scope or None))
        scoped = f" @ {sig_scope}" if sig_scope else ""
        parts = []
        if shown:
            parts.append(f"added {', '.join(shown)}{scoped}")
        if not_dumped:
            parts.append(f"⚠ {', '.join(not_dumped)} not dumped in this VCD "
                         "(shown as placeholder — re-run /sim to dump for real data)")
        if notes:
            parts.append("; ".join(notes))
        return f"✓ Sim Debug ({where}): " + "; ".join(parts) + "."

    if act in ("goto", "zoom", "view"):
        if t_start is None or t_end is None:
            return "[sim_debug goto: t_start and t_end (ns) required]"
        try:
            a, b = int(float(t_start)), int(float(t_end))
        except (TypeError, ValueError):
            return "[sim_debug goto: t_start/t_end must be numbers (ns)]"
        push_intent(ip, "goto", t_start=min(a, b), t_end=max(a, b),
                    cursor_a=cursor_a, cursor_b=cursor_b)
        return f"✓ Sim Debug: zoomed to {min(a, b)}–{max(a, b)} ns ({where})."

    if act == "cursor":
        if cursor_a is None and cursor_b is None:
            return "[sim_debug cursor: cursor_a and/or cursor_b (ns) required]"
        push_intent(ip, "cursor", cursor_a=cursor_a, cursor_b=cursor_b)
        parts = []
        if cursor_a is not None:
            parts.append(f"A={int(float(cursor_a))}")
        if cursor_b is not None:
            parts.append(f"B={int(float(cursor_b))}")
        return f"✓ Sim Debug cursor: {' '.join(parts)} ns ({where})."

    if act == "fit":
        push_intent(ip, "fit")
        return f"✓ Sim Debug: fit whole VCD ({where})."

    if act == "reorder":
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug reorder: pass signals=\"a,b,c\" in the desired top-to-bottom order]"
        push_intent(ip, "reorder", signals=sigs, scope=(sig_scope or None))
        return f"✓ Sim Debug: reordered {', '.join(sigs)} ({where})."

    if act == "group":
        sigs = _sim_debug_siglist(signals, signal)
        grp = str(group or "").strip()
        if not grp or not sigs:
            return "[sim_debug group: pass group=\"name\" and signals=\"a,b\"]"
        push_intent(ip, "group", group=grp, signals=sigs, scope=(sig_scope or None), color=(str(color).strip() or None))
        cs = f" [{color}]" if str(color).strip() else ""
        return f"✓ Sim Debug: grouped {', '.join(sigs)} under '{grp}'{cs} ({where})."

    if act == "ungroup":
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug ungroup: pass signals=\"a,b\"]"
        push_intent(ip, "ungroup", signals=sigs, scope=(sig_scope or None))
        return f"✓ Sim Debug: ungrouped {', '.join(sigs)} ({where})."

    if act == "color":
        sigs = _sim_debug_siglist(signals, signal)
        col = str(color or "").strip()
        if not sigs or not col:
            return "[sim_debug color: pass color=\"#rrggbb\" and signals=\"a,b\"]"
        push_intent(ip, "color", signals=sigs, scope=(sig_scope or None), color=col)
        return f"✓ Sim Debug: colored {', '.join(sigs)} {col} ({where})."

    if act == "radix":
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug radix: pass signals=\"a,b\" and radix=hex|dec|bin|fsm|off]"
        # fsm/param → show the parameter/enum NAME for matching values.
        # off/none/reset/default → clear the override (frontend default render).
        radix_map = {
            "hex": "HEX", "h": "HEX", "dec": "DEC", "d": "DEC", "decimal": "DEC",
            "bin": "BIN", "b": "BIN", "binary": "BIN",
            "fsm": "FSM", "param": "FSM", "parameter": "FSM", "enum": "FSM",
            "off": None, "none": None, "reset": None, "default": None, "raw": None,
        }
        rv = str(radix or "").strip().lower()
        if rv not in radix_map:
            return ("[sim_debug radix: radix must be hex|dec|bin|fsm|off "
                    f"(got {radix!r})]")
        norm = radix_map[rv]
        # None is dropped by push_intent, so the panel sees no radix → reset.
        push_intent(ip, "radix", signals=sigs, scope=(sig_scope or None), radix=norm)
        return (f"✓ Sim Debug: set radix {norm or 'default'} on "
                f"{', '.join(sigs)} ({where}).")

    if act in ("remove", "delete", "rm"):
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug remove: pass signals=\"a,b\"]"
        push_intent(ip, "remove", signals=sigs, scope=(sig_scope or None))
        return f"✓ Sim Debug: removed {', '.join(sigs)} from the waveform ({where})."

    if act in ("keep", "only", "isolate", "keeponly"):
        # "show ONLY these" — the panel removes every other CURRENTLY-DISPLAYED
        # row (incl. the default rows the agent never explicitly added and can't
        # enumerate), so "I need only X" actually clears the rest.
        sigs = _sim_debug_siglist(signals, signal)
        if not sigs:
            return "[sim_debug keep: pass signals=\"a,b\" to keep ONLY those]"
        push_intent(ip, "keep", signals=sigs, scope=(sig_scope or None))
        return f"✓ Sim Debug: keeping only {', '.join(sigs)} ({where})."

    if act in ("clear", "clearall", "remove_all", "removeall"):
        push_intent(ip, "clear")
        return f"✓ Sim Debug: cleared all signals from the waveform ({where})."

    if act in ("fold", "unfold"):
        grp = str(group or "").strip()
        if not grp:
            return f"[sim_debug {act}: pass group=\"name\"]"
        push_intent(ip, act, group=grp)
        return f"✓ Sim Debug: {act}ed group '{grp}' ({where})."

    if act in ("trace", "find", "value"):
        # Implemented in Phase B/C via core.sim_debug_analyze.
        try:
            from core.sim_debug_analyze import run_sim_debug_analysis
        except Exception:
            return f"[sim_debug {act}: analysis module unavailable]"
        return run_sim_debug_analysis(
            act, ip=ip, signal=signal, edge=edge, nth=nth, at=at,
            push_intent=push_intent, scope=sig_scope)

    return ("[sim_debug: unknown action '" + act + "'. "
            "Use: show, goto, cursor, fit, reorder, group, ungroup, color, "
            "radix, remove, keep, clear, fold, unfold, trace, find, value]")


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
    "commit_ip": commit_ip,
    "replace_in_file": replace_in_file,
    "replace_lines": replace_lines,
    "wiki_query": wiki_query,
    "external_db_query": external_db_query,
    "verify_ssot": verify_ssot,
    # Image Analysis (conditional — requires ENABLE_IMAGE_READ=true)
    "read_image": read_image,
    # Task Management
    "todo_write": todo_write,
    "todo_update": todo_update,
    "todo_add": todo_add,
    "todo_remove": todo_remove,
    "todo_status": todo_status,
    "todo_note": todo_note,
    # RAG Tools (disabled — uncomment to enable)
    # "rag_search": rag_search,
    # "rag_index": rag_index,
    # "rag_explore": rag_explore,
    # "rag_status": rag_status,
    # "rag_clear": rag_clear,
    # Background Agent Tools (v2)
    "custom_agent_save": custom_agent_save,
    "custom_agent_list": custom_agent_list,
    "background_task": background_task,
    "background_output": background_output,
    "background_cancel": background_cancel,
    "background_list": background_list,
    "parallel_todo_dispatch": parallel_todo_dispatch,
    # cursor-agent tool (delegates to cursor-agent CLI)
    "cursor_agent": cursor_agent,
    # Workflow Orchestration Tools
    "pipeline_execute": pipeline_execute,
    "workflow_dispatch": workflow_dispatch,
    "workflow_list": workflow_list,
    # Project Management Tools
    "project_list": project_list,
    "project_switch": project_switch,
    "project_create": project_create,
    "project_delete": project_delete,
    # Job Management Tools
    "job_list": job_list,
    "job_status": job_status,
    "job_output": job_output,
    "job_cancel": job_cancel,
    # GUI interaction
    "ask_user": ask_user,
    "record_ssot_qa": record_ssot_qa,
    # Document ingestion (markitdown — pdf/docx/pptx/xlsx/html → md)
    "read_doc": read_doc,
    # IP layout scaffolder
    "scaffold_ip": scaffold_ip,
    # IP-XACT (IEEE 1685) → SSOT YAML importer
    "ipxact_import": ipxact_import,
    # Architect supervisor tools (whole-SoC level)
    "addrmap_check": addrmap_check,
    "soc_status": soc_status,
    "wrapper_gen": wrapper_gen,
    "dispatch_workflow": dispatch_workflow,
    "read_pipeline_state": read_pipeline_state,
    # Sim Debug waveform panel driver/analysis (VCD + pyslang)
    "sim_debug": sim_debug,
}


def filtered_available_tools(extra_disable=None):
    """Return AVAILABLE_TOOLS minus any entries listed in the
    WORKFLOW_DISABLED_TOOLS env var (comma-separated). Workflows set
    this via workspace.json `env` to remove tools that don't make sense
    for their stage (e.g., rtl-gen disables ask_user / record_ssot_qa
    because the stage engine already auto-runs derive_rtl_todos.py and
    the agent should consult on-disk artifacts instead of pinging the
    user). Optional `extra_disable` is merged in for callers that want
    to filter beyond the env var.
    """
    import os as _os
    raw = _os.environ.get("WORKFLOW_DISABLED_TOOLS", "")
    disabled = {x.strip() for x in raw.split(",") if x.strip()}
    if extra_disable:
        disabled.update(extra_disable)
    if not disabled:
        return AVAILABLE_TOOLS
    return {k: v for k, v in AVAILABLE_TOOLS.items() if k not in disabled}

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
        # pyslang-powered AST tools
        "sv_get_ports": tools_verilog.sv_get_ports,
        "sv_get_hierarchy": tools_verilog.sv_get_hierarchy,
        "sv_compile": tools_verilog.sv_compile,
    })
except ImportError:
    pass  # tools_verilog not available

# Import and register generic spec navigation tool (pcie/ucie/nvme 등 모든 스펙)
try:
    from tools_spec import spec_navigate
    AVAILABLE_TOOLS["spec_navigate"] = spec_navigate
except ImportError:
    pass  # spec_navigate_tool not available

# tmux integration tools — observe/control modifiable_ai_agent pane.
# OPT-IN (TMUX_ENABLE=true): tmux is a POSIX-only control surface (absent on
# native Windows) and config always had ENABLE_TMUX_TOOLS — this block just
# never honored it (cmux below always did).
try:
    import config as _tmux_cfg
    _tmux_enabled = getattr(_tmux_cfg, "ENABLE_TMUX_TOOLS", False)
except Exception:
    _tmux_enabled = False
if _tmux_enabled:
    try:
        from core.tools_tmux import TMUX_TOOLS
        AVAILABLE_TOOLS.update(TMUX_TOOLS)
    except ImportError:
        try:
            from tools_tmux import TMUX_TOOLS
            AVAILABLE_TOOLS.update(TMUX_TOOLS)
        except ImportError:
            pass  # tools_tmux not available

# cmux integration tools — observe/control modifiable_ai_agent via cmux socket
try:
    import config as _cmux_cfg
    _cmux_enabled = getattr(_cmux_cfg, "ENABLE_CMUX_TOOLS", False)
except Exception:
    _cmux_enabled = False
if _cmux_enabled:
    try:
        from core.tools_cmux import CMUX_TOOLS
        AVAILABLE_TOOLS.update(CMUX_TOOLS)
    except ImportError:
        try:
            from tools_cmux import CMUX_TOOLS
            AVAILABLE_TOOLS.update(CMUX_TOOLS)
        except ImportError:
            pass  # tools_cmux not available

# web tools — Firecrawl-powered search, fetch, extract
try:
    from core.tools_web import WEB_TOOLS
    AVAILABLE_TOOLS.update(WEB_TOOLS)
except ImportError:
    try:
        from tools_web import WEB_TOOLS
        AVAILABLE_TOOLS.update(WEB_TOOLS)
    except ImportError:
        pass  # tools_web not available

# Worker tools — Commander → Worker agent dispatch over HTTP
try:
    from core.agent_client import worker_call, worker_status, worker_result, worker_cancel, worker_call_all
    AVAILABLE_TOOLS.update({
        "worker_call": worker_call,
        "worker_status": worker_status,
        "worker_result": worker_result,
        "worker_cancel": worker_cancel,
        "worker_call_all": worker_call_all,
    })
except ImportError:
    pass  # agent_client not available

# MCP tools — dynamically loaded from .mcp.json
_MCP_MANAGER = None
try:
    import config as _config
    if getattr(_config, 'ENABLE_MCP', False):
        try:
            import sys as _sys
            import os as _os
            # Ensure mcp/ package is importable from project root
            _mcp_root = _os.path.dirname(_os.path.dirname(_os.path.abspath(__file__)))
            if _mcp_root not in _sys.path:
                _sys.path.insert(0, _mcp_root)
            import mcp as _mcp_module
            from core.tool_schema import register_dynamic_schema
            _mcp_config = getattr(_config, 'MCP_CONFIG_PATH', '.mcp.json')
            _MCP_MANAGER = _mcp_module.init(_mcp_config)
            AVAILABLE_TOOLS.update(_MCP_MANAGER.get_tools())
            for _schema in _MCP_MANAGER.get_schemas():
                register_dynamic_schema(_schema["function"]["name"], _schema)
        except Exception as _e:
            import sys as _sys
            print(f"[MCP] Failed to load: {_e}", file=_sys.stderr)
except ImportError:
    pass  # config not available in this context
