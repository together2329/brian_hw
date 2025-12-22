"""
Interactive Plan Mode (text-only planning with optional exploration).

This module provides a separate planning loop where the user iteratively
refines a plan with the PlanAgent until approval, then saves the plan to
~/.brian_coder/plans.
"""
import os
import re
import time
from dataclasses import dataclass
from typing import Optional, List, Dict

import config
from agents.sub_agents.plan_agent import PlanAgent
from llm_client import call_llm_raw, chat_completion_stream
from lib.display import Color
from core import tools

_DEBUG_PREVIEW_CHARS = 800


@dataclass
class PlanModeResult:
    plan_path: str
    plan_content: str


def plan_mode_loop(
    task: str,
    max_rounds: int = 10,
    context_messages: Optional[List[Dict]] = None
) -> Optional[PlanModeResult]:
    """
    Interactive plan mode loop.

    Args:
        task: Initial task description.
        max_rounds: Max refinement rounds before stopping.

    Returns:
        PlanModeResult if approved, otherwise None.
    """
    task = (task or "").strip()
    if not task:
        print(Color.warning("[Plan Mode] Empty task."))
        return None

    print(Color.system("\n" + "=" * 60))
    print(Color.system("[Plan Mode] Entering interactive planning mode"))
    print(Color.system("Commands: approve | cancel | show"))
    print(Color.system("=" * 60 + "\n"))

    llm_call = _plan_llm_call
    context_text = _build_plan_context(context_messages)
    if _plan_debug_enabled():
        print(Color.info(
            f"[Plan Mode][Debug] Context mode={config.PLAN_MODE_CONTEXT_MODE}, "
            f"chars={len(context_text)}"
        ))

    plan_agent = PlanAgent(
        name="plan_mode",
        llm_call_func=llm_call,
        execute_tool_func=_execute_plan_tool,
        max_iterations=20
    )

    try:
        result = plan_agent.draft_plan(task, context=context_text)
    except Exception as e:
        print(Color.error(f"[Plan Mode] Exception during plan generation: {e}"))
        if _plan_debug_enabled():
            import traceback
            print(Color.DIM + traceback.format_exc() + Color.RESET)
        return None

    if result.status.value != "completed" or not result.output:
        print(Color.error("[Plan Mode] Failed to generate initial plan."))
        if result.errors:
            for err in result.errors:
                print(Color.error(f"[Plan Mode]   • {err}"))

        # Retry once with simpler prompt
        print(Color.warning("[Plan Mode] Retrying with simplified prompt..."))
        try:
            simple_task = f"Create a brief implementation plan for: {task}"
            result = plan_agent.draft_plan(simple_task, context="")
            if result.status.value == "completed" and result.output:
                print(Color.success("[Plan Mode] Retry succeeded with simplified prompt."))
            else:
                print(Color.error("[Plan Mode] Retry also failed. Aborting."))
                return None
        except Exception as e:
            print(Color.error(f"[Plan Mode] Retry exception: {e}"))
            return None

    current_plan = result.output
    print(Color.success("\n[Plan Mode] Draft plan created:\n"))
    print(Color.CYAN + current_plan + Color.RESET)

    rounds = 0
    while True:
        if rounds >= max_rounds:
            print(Color.warning("[Plan Mode] Max refinement rounds reached."))
            return None

        user_input = input(Color.user("\nPlan feedback (or approve/cancel/show): ") + Color.RESET).strip()
        command = user_input.lower()

        if command in ("approve", "approved", "ok", "done"):
            break
        if command in ("cancel", "quit", "exit"):
            print(Color.warning("[Plan Mode] Cancelled."))
            return None
        if command == "show":
            print(Color.CYAN + current_plan + Color.RESET)
            continue
        if not user_input:
            print(Color.warning("[Plan Mode] Please enter feedback or approve/cancel/show."))
            continue

        print(Color.info("[Plan Mode] Refining plan..."))
        try:
            refined = plan_agent.refine(user_input, current_plan, context=context_text)
        except Exception as e:
            print(Color.error(f"[Plan Mode] Exception during refinement: {e}"))
            if _plan_debug_enabled():
                import traceback
                print(Color.DIM + traceback.format_exc() + Color.RESET)
            print(Color.warning("[Plan Mode] Keeping previous plan. Try simpler feedback."))
            continue

        if refined.status.value != "completed" or not refined.output:
            print(Color.error("[Plan Mode] Failed to refine plan."))
            if refined.errors:
                for err in refined.errors:
                    print(Color.error(f"[Plan Mode]   • {err}"))
            print(Color.warning("[Plan Mode] Keeping previous plan. Try different feedback."))
            continue

        current_plan = refined.output
        rounds += 1
        print(Color.success("\n[Plan Mode] Updated plan:\n"))
        print(Color.CYAN + current_plan + Color.RESET)

    try:
        plan_path = _save_plan_to_file(task, current_plan)
    except Exception as e:
        print(Color.error(f"[Plan Mode] Failed to save plan: {e}"))
        if _plan_debug_enabled():
            import traceback
            print(Color.DIM + traceback.format_exc() + Color.RESET)
        # Still return result even if save failed (user has the plan content)
        print(Color.warning("[Plan Mode] Plan not saved to file, but continuing with in-memory plan."))
        return PlanModeResult(plan_path="", plan_content=current_plan)

    print(Color.success(f"\n[Plan Mode] Plan approved and saved: {plan_path}"))
    return PlanModeResult(plan_path=plan_path, plan_content=current_plan)


def _execute_plan_tool(tool_name: str, args_str: str) -> str:
    """
    Minimal execute_tool wrapper for PlanAgent.
    Only allows spawn_explore(query="...").
    """
    if tool_name != "spawn_explore":
        error_msg = f"Error: Tool '{tool_name}' not allowed for PlanAgent. Only 'spawn_explore' is permitted."
        print(Color.warning(f"[Plan Mode] {error_msg}"))
        return error_msg

    query = _extract_query_arg(args_str)
    if not query:
        error_msg = "Error: spawn_explore requires a non-empty query argument"
        print(Color.warning(f"[Plan Mode] {error_msg}"))
        return error_msg

    if _plan_debug_enabled():
        print(Color.info(f"[Plan Mode][Debug] Tool call: {tool_name}(query={query})"))

    try:
        result = tools.spawn_explore(query)
        if _plan_debug_enabled():
            preview = _truncate_text(str(result), _DEBUG_PREVIEW_CHARS)
            print(Color.info(f"[Plan Mode][Debug] Tool result ({len(str(result))} chars): {preview}"))
        return result
    except Exception as e:
        error_msg = f"Error: spawn_explore failed: {e}"
        print(Color.error(f"[Plan Mode] {error_msg}"))
        if _plan_debug_enabled():
            import traceback
            print(Color.DIM + traceback.format_exc() + Color.RESET)
        return error_msg


def _extract_query_arg(args_str: str) -> str:
    if not args_str:
        return ""
    match = re.search(r'query\\s*=\\s*["\\\']([^"\\\']+)["\\\']', args_str)
    if match:
        return match.group(1).strip()
    match = re.search(r'query\\s*=\\s*([^,]+)', args_str)
    if match:
        return match.group(1).strip().strip('"').strip("'")
    # Positional string
    match = re.search(r'^\\s*["\\\']([^"\\\']+)["\\\']', args_str.strip())
    if match:
        return match.group(1).strip()
    return args_str.strip().strip('"').strip("'")


def _save_plan_to_file(task: str, plan_content: str) -> str:
    plan_dir = os.path.expanduser(config.PLAN_DIR)
    os.makedirs(plan_dir, exist_ok=True)

    safe_task = re.sub(r"[^\w\s-]", "", task).strip().lower()
    safe_task = re.sub(r"[-\s]+", "-", safe_task)[:50]
    if not safe_task:
        safe_task = "plan"

    timestamp = time.strftime("%Y%m%d-%H%M%S")
    filename = f"{safe_task}-{timestamp}.md"
    plan_path = os.path.join(plan_dir, filename)

    content = (
        "# Plan\n\n"
        "## Task\n"
        f"{task}\n\n"
        "## Generated\n"
        f"{time.strftime('%Y-%m-%d %H:%M:%S')}\n\n"
        "---\n\n"
        f"{plan_content.strip()}\n"
    )

    with open(plan_path, "w", encoding="utf-8") as handle:
        handle.write(content)

    return plan_path


def _build_plan_context(messages: Optional[List[Dict]]) -> str:
    if not messages:
        return ""

    include_system = bool(config.PLAN_MODE_CONTEXT_INCLUDE_SYSTEM)
    filtered = [
        msg for msg in messages
        if include_system or msg.get("role") != "system"
    ]

    mode = config.PLAN_MODE_CONTEXT_MODE
    if mode == "recent":
        recent_n = max(0, int(config.PLAN_MODE_CONTEXT_RECENT_N))
        if recent_n > 0:
            filtered = filtered[-recent_n:]

    text = _messages_to_text(filtered)
    if mode == "summary":
        return _summarize_context(text)
    return _apply_max_chars(text)


def _messages_to_text(messages: List[Dict]) -> str:
    parts = []
    for msg in messages:
        role = msg.get("role", "unknown")
        content = _normalize_content(msg.get("content", ""))
        parts.append(f"{role}: {content}")
    return "\n\n".join(parts).strip()


def _summarize_context(text: str) -> str:
    if not text:
        return ""

    try:
        prompt = [
            {"role": "system", "content": "Summarize conversation context for planning."},
            {"role": "user", "content": (
                "Summarize key requirements, constraints, decisions, and open items.\n\n"
                f"{_apply_max_chars(text)}"
            )},
        ]
        summary = call_llm_raw(prompt, temperature=0.2)
        if not summary or summary.startswith("Error calling LLM:"):
            print(Color.warning("[Plan Mode] Context summarization failed, using truncated text"))
            return _apply_max_chars(text)
        return summary
    except Exception as e:
        print(Color.warning(f"[Plan Mode] Exception during context summarization: {e}"))
        return _apply_max_chars(text)


def _apply_max_chars(text: str) -> str:
    max_chars = int(getattr(config, "PLAN_MODE_CONTEXT_MAX_CHARS", 0) or 0)
    if max_chars <= 0 or len(text) <= max_chars:
        return text
    return text[:max_chars] + f"... [truncated {len(text) - max_chars} chars]"


def _plan_debug_enabled() -> bool:
    return bool(config.PLAN_MODE_DEBUG or config.PLAN_MODE_DEBUG_FULL or config.FULL_PROMPT_DEBUG)


def _plan_llm_call(messages):
    if _plan_debug_enabled():
        _print_debug_messages(messages)
    if config.PLAN_MODE_STREAM:
        response = _stream_llm_call(messages)
        if _plan_debug_enabled():
            print(Color.system(f"[Plan Mode][Debug] LLM response length: {len(response)}"))
        return response
    response = call_llm_raw(messages)
    if _plan_debug_enabled():
        _print_debug_response(response)
    return response


def _stream_llm_call(messages) -> str:
    output = ""
    print(Color.system("[Plan Mode][Stream] LLM response:"))
    try:
        for chunk in chat_completion_stream(messages):
            if not chunk:
                continue
            output += chunk
            # If DEBUG_MODE is on, llm_client already prints the chunks with color
            if not config.DEBUG_MODE:
                print(chunk, end="", flush=True)
    finally:
        print()
    return output.strip()


def _print_debug_messages(messages):
    full = bool(config.PLAN_MODE_DEBUG_FULL or config.FULL_PROMPT_DEBUG)
    print(Color.system(f"[Plan Mode][Debug] LLM messages: {len(messages)}"))
    for idx, msg in enumerate(messages):
        role = msg.get("role", "unknown")
        content = _normalize_content(msg.get("content", ""))
        preview = content if full else _truncate_text(content, _DEBUG_PREVIEW_CHARS)
        print(Color.DIM + f"  [{idx}] {role}: " + Color.RESET + preview)


def _print_debug_response(response):
    full = bool(config.PLAN_MODE_DEBUG_FULL or config.FULL_PROMPT_DEBUG)
    text = _normalize_content(response)
    preview = text if full else _truncate_text(text, _DEBUG_PREVIEW_CHARS)
    print(Color.system(f"[Plan Mode][Debug] LLM response ({len(text)} chars):"))
    print(preview)


def _normalize_content(content) -> str:
    if isinstance(content, list):
        return str(content)
    return str(content)


def _truncate_text(text: str, limit: int) -> str:
    if len(text) <= limit:
        return text
    return text[:limit] + f"... [truncated {len(text) - limit} chars]"
