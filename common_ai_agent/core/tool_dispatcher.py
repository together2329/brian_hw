"""
core/tool_dispatcher.py
Phase 7: extracted from main.py execute_tool()

Provides dispatch_tool() — pure function with all dependencies injected.
main.py's execute_tool() becomes a thin wrapper that passes live globals.
"""
import json
import threading
import traceback
from typing import Any, Callable, Dict, Optional

from core.action_parser import parse_tool_arguments

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

def dispatch_tool(
    tool_name: str,
    args_str: str,
    *,
    available_tools: Dict[str, Callable],
    debug: bool = False,
    hook_registry: Any = None,
) -> str:
    """
    Dispatch a single tool call.

    Args:
        tool_name:       Name of the tool to invoke.
        args_str:        Raw argument string (e.g. 'path="a.py", start_line=1').
        available_tools: Mapping of tool_name → callable.
        debug:           If True, print parsed args before calling.
        hook_registry:   Optional HookRegistry for AFTER_TOOL_EXEC / ON_ERROR hooks.

    Returns:
        String result (tool output, converted if non-string, or error message).
    """
    if tool_name not in available_tools:
        return f"Error: Tool '{tool_name}' not found."

    func = available_tools[tool_name]

    try:
        parsed_args, parsed_kwargs = parse_tool_arguments(args_str)

        if debug:
            print(f"[DEBUG] Parsed args: {parsed_args}, kwargs: {parsed_kwargs}")

        result = func(*parsed_args, **parsed_kwargs)

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
