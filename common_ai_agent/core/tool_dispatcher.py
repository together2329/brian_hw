"""
core/tool_dispatcher.py
Phase 7: extracted from main.py execute_tool()

Provides dispatch_tool() — pure function with all dependencies injected.
main.py's execute_tool() becomes a thin wrapper that passes live globals.
"""
import inspect
import json
import os
import threading
import traceback
from typing import Any, Callable, Dict, Optional

from core.action_parser import parse_tool_arguments

# ---------------------------------------------------------------------------
# Tool aliases — common LLM hallucinations mapped to real tool names
# ---------------------------------------------------------------------------
_TOOL_ALIASES: Dict[str, str] = {
    "apply_patch":   "replace_in_file",
    "patch_file":    "replace_in_file",
    "edit_file":     "replace_in_file",
    "run_shell":     "run_command",
    "shell":         "run_command",
    "bash":          "run_command",
    "execute":       "run_command",
    "search_file":   "grep_file",
    "search":        "grep_file",
    "ls":            "list_dir",
    "cat":           "read_file",
}

# ---------------------------------------------------------------------------
# Thread-local agent metadata (mirrors main.py _agent_metadata)
# ---------------------------------------------------------------------------

_agent_metadata = threading.local()


def get_last_agent_metadata() -> Optional[dict]:
    return getattr(_agent_metadata, "last_result", None)


def clear_agent_metadata() -> None:
    _agent_metadata.last_result = None


# ---------------------------------------------------------------------------
# Core dispatch
# ---------------------------------------------------------------------------

class _ToolTimeoutError(Exception):
    """Raised when a tool exceeds the global timeout."""
    pass


def _call_with_timeout(
    func: Callable,
    args: list,
    kwargs: dict,
    *,
    timeout: int,
    tool_name: str,
):
    """
    Call *func* with a hard timeout.  Uses a worker thread so we can enforce
    a wall-clock limit even for blocking / C-extension calls that don't
    cooperate with Python-level interrupts.

    Returns the function result, or raises _ToolTimeoutError on timeout.
    """
    if timeout <= 0:
        return func(*args, **kwargs)

    result_container = [None]
    error_container = [None]

    def _worker():
        try:
            result_container[0] = func(*args, **kwargs)
        except Exception as exc:
            error_container[0] = exc

    import concurrent.futures
    with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
        future = executor.submit(_worker)
        try:
            future.result(timeout=timeout)
        except concurrent.futures.TimeoutError:
            raise _ToolTimeoutError(
                f"Tool '{tool_name}' exceeded global timeout of {timeout}s"
            )

    if error_container[0] is not None:
        raise error_container[0]
    return result_container[0]


def dispatch_tool(
    tool_name: str,
    args_str: str,
    *,
    available_tools: Dict[str, Callable],
    debug: bool = False,
    hook_registry: Any = None,
    global_timeout: int = 0,
) -> str:
    """
    Dispatch a single tool call.

    Args:
        tool_name:       Name of the tool to invoke.
        args_str:        Raw argument string (e.g. 'path="a.py", start_line=1').
        available_tools: Mapping of tool_name → callable.
        debug:           If True, print parsed args before calling.
        hook_registry:   Optional HookRegistry for AFTER_TOOL_EXEC / ON_ERROR hooks.
        global_timeout:  Max seconds for any single tool call. 0 = no limit.

    Returns:
        String result (tool output, converted if non-string, or error message).
    """
    # Resolve aliases before lookup
    resolved_name = _TOOL_ALIASES.get(tool_name, tool_name)
    if resolved_name != tool_name:
        print(f"  [System] Tool '{tool_name}' → alias resolved to '{resolved_name}'")
        tool_name = resolved_name

    if tool_name not in available_tools:
        # Suggest closest match from aliases
        suggestions = [v for k, v in _TOOL_ALIASES.items() if tool_name.lower() in k.lower()]
        hint = f" Did you mean: {suggestions[0]!r}?" if suggestions else ""
        return f"Error: Tool '{tool_name}' not found.{hint}"

    func = available_tools[tool_name]

    try:
        parsed_args, parsed_kwargs = parse_tool_arguments(args_str)

        # Auto-fix: grep_file(path, ...) — LLM swapped pattern and path
        if tool_name == "grep_file" and parsed_args:
            first = parsed_args[0]
            # If first arg looks like a file path (has / or known extension) and not a regex
            if (("/" in str(first) or os.path.splitext(str(first))[1])
                    and "pattern" not in parsed_kwargs):
                # Swap: first arg is path, second is pattern (or pull pattern from kwargs)
                if len(parsed_args) >= 2:
                    parsed_args = [parsed_args[1], parsed_args[0]] + list(parsed_args[2:])
                elif "path" in parsed_kwargs:
                    pass  # path already in kwargs, first arg must be pattern — keep as-is
                else:
                    parsed_kwargs["path"] = parsed_args[0]
                    parsed_args = []

        # Auto-fix: positional arg duplicates a keyword arg ("got multiple values")
        if parsed_args:
            try:
                sig = inspect.signature(func)
                param_names = list(sig.parameters.keys())
                # Remove positional args that are already in kwargs
                fixed_positional = []
                for i, val in enumerate(parsed_args):
                    name = param_names[i] if i < len(param_names) else None
                    if name and name in parsed_kwargs:
                        pass  # skip — kwargs already has this
                    else:
                        fixed_positional.append(val)
                parsed_args = fixed_positional
            except (ValueError, TypeError):
                pass

        if debug:
            print(f"[DEBUG] Parsed args: {parsed_args}, kwargs: {parsed_kwargs}")

        # Execute tool with optional global timeout
        result = _call_with_timeout(
            func, parsed_args, parsed_kwargs,
            timeout=global_timeout,
            tool_name=tool_name,
        )

        # Store AgentResult metadata in thread-local; clear for normal tools
        if hasattr(result, "__class__") and result.__class__.__name__ == "AgentResult":
            _agent_metadata.last_result = {
                "tool_name": tool_name,
                "files_examined": result.get("files_examined", []),
                "planned_steps": result.get("planned_steps", []),
                "summary": result.get("summary", ""),
                "tool_calls_count": result.get("tool_calls_count", 0),
                "execution_time_ms": result.get("execution_time_ms", 0),
                "agent_type": result.get("metadata", {}).get("agent_type", ""),
            }
        else:
            _agent_metadata.last_result = None

        # Ensure string output
        if not isinstance(result, str):
            try:
                result = json.dumps(result, indent=2, ensure_ascii=False)
            except Exception:
                result = str(result)

        # Hook: AFTER_TOOL_EXEC
        if hook_registry:
            from core.hooks import HookContext, HookPoint
            hook_ctx = HookContext(
                tool_name=tool_name,
                tool_args=args_str,
                tool_output=result,
            )
            hook_ctx = hook_registry.run(HookPoint.AFTER_TOOL_EXEC, hook_ctx)
            result = hook_ctx.tool_output

        return result

    except _ToolTimeoutError as e:
        _agent_metadata.last_result = None
        return f"Error: {e}"

    except Exception as e:
        error_detail = traceback.format_exc()
        _agent_metadata.last_result = None

        # Hook: ON_ERROR
        if hook_registry:
            from core.hooks import HookContext, HookPoint
            hook_ctx = HookContext(
                tool_name=tool_name,
                tool_args=args_str,
                error=e,
                error_traceback=error_detail,
            )
            hook_registry.run(HookPoint.ON_ERROR, hook_ctx)

        return (
            f"Error parsing/executing arguments: {e}\n"
            f"{error_detail}\n"
            f"args_str was: {args_str[:200]}"
        )
