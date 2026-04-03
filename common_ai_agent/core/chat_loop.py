"""
core/chat_loop.py
Phase 9: extracted per-turn processing logic from chat_loop() in main.py

Provides:
  ChatLoopState     — mutable turn-to-turn REPL state
  ChatLoopDeps      — injected callables / objects
  process_chat_turn — pure-ish function: one REPL iteration
                      returns (new_state, control)
                      control: "continue" | "break" | "skip"

The actual I/O loop (input(), readline) stays in main.py's chat_loop().
"""
from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from lib.iteration_control import IterationTracker


# ---------------------------------------------------------------------------
# State & Deps
# ---------------------------------------------------------------------------

@dataclass
class ChatLoopState:
    """All mutable state that persists across REPL iterations."""
    messages: List[dict]
    agent_mode: str = "normal"
    rolling_window_size: int = 0
    full_messages: Optional[List[dict]] = None
    auto_compression_threshold: int = 0
    conversation_count: int = 0
    is_first_turn: bool = True
    todo_tracker: Optional[Any] = None


@dataclass
class ChatLoopDeps:
    """Injected callables — no globals, fully testable."""
    cfg: Any
    run_react_agent_fn: Callable
    compress_fn: Callable
    save_history_fn: Callable
    on_conversation_end_fn: Callable
    build_system_prompt_fn: Callable
    show_context_usage_fn: Callable
    slash_registry: Optional[Any] = None
    context_tracker: Optional[Any] = None
    curator: Optional[Any] = None
    hook_registry: Optional[Any] = None   # phase9 gap: was missing, hooks not firing per-turn
    input_fn: Optional[Callable] = None   # override for Textual TUI (default: built-in input())


# "continue" | "break" | "skip"  (Literal not available in Python 3.7)
Control = str


# ---------------------------------------------------------------------------
# process_chat_turn
# ---------------------------------------------------------------------------

def process_chat_turn(
    user_input: str,
    state: ChatLoopState,
    deps: ChatLoopDeps,
) -> Tuple[ChatLoopState, Control]:
    """
    Process one REPL turn.

    Args:
        user_input: Raw string from stdin (already stripped of trailing newline).
        state:      Current loop state.
        deps:       Injected dependencies.

    Returns:
        (new_state, control) where control is "continue", "break", or "skip".
        The original state object is mutated in place AND returned for convenience.
    """
    cfg = deps.cfg

    # --- Exit ---
    if user_input.lower() in ("exit", "quit"):
        deps.save_history_fn(state.messages)
        return state, "break"

    # --- Empty input ---
    if not user_input.strip():
        return state, "skip"

    # --- Plan mode confirmation ---
    if state.agent_mode in ("plan", "plan_q"):
        inp = user_input.lower().strip()

        # y / yes / confirm → execute plan
        if inp in ("y", "yes", "confirm", "proceed", "진행", "확인", "ok", "네", "예", "ㅇㅇ", "yc"):
            do_compress = (inp == "yc")
            state.agent_mode = "normal"

            # Rebuild system prompt to restore full toolset
            if state.messages and state.messages[0].get("role") == "system":
                system_prompt_data = deps.build_system_prompt_fn(
                    state.messages, agent_mode="normal"
                )
                if isinstance(system_prompt_data, dict):
                    new_content = system_prompt_data.get("static", "") + system_prompt_data.get("dynamic", "")
                else:
                    new_content = system_prompt_data
                state.messages[0]["content"] = new_content

            if getattr(cfg, "STEP_BY_STEP_MODE", False):
                user_input = (
                    "Confirmed. Perform ONLY the first task (Step 1) now.\n"
                    "Workflow: todo_update(index=1, status='in_progress') → do work → "
                    "todo_update(index=1, status='completed') → verify → "
                    "todo_update(index=1, status='approved', reason='...')"
                )
            else:
                user_input = (
                    "Confirmed. Execute all tasks in order. For EACH task follow this workflow:\n"
                    "  1. todo_update(index=N, status='in_progress')\n"
                    "  2. Do the work\n"
                    "  3. todo_update(index=N, status='completed')\n"
                    "  4. Verify the result\n"
                    "  5. todo_update(index=N, status='approved', reason='what you verified')\n"
                    "Start now: todo_update(index=1, status='in_progress')"
                )

            if state.messages:
                state.messages[-1]["content"] = user_input

            if do_compress:
                state.messages = deps.compress_fn(
                    state.messages, todo_tracker=state.todo_tracker, force=True
                )

        # n / no → cancel
        elif inp in ("n", "no", "cancel", "취소", "아니오", "ㄴㄴ"):
            user_input = (
                "I've reviewed the plan and I'm NOT ready to execute yet. "
                "Let's refine it further or address my concerns."
            )

        # Short non-slash token → likely a typo, skip
        elif len(inp) <= 2 and not inp.startswith("/"):
            if state.messages:
                state.messages.pop()
            return state, "skip"

        # Otherwise: treat as feedback and fall through to run_react_agent

    # --- Keep-going signal ---
    if getattr(cfg, "ENABLE_TODO_TRACKING", False) and state.todo_tracker:
        inp = user_input.lower().strip()
        if any(x in inp for x in ("keep going", "continue", "진행", "계속")):
            if state.todo_tracker.unprocess_rejected():
                reminder = state.todo_tracker.get_continuation_prompt()
                if reminder:
                    user_input = f"{user_input}\n\n{reminder}"
                    if state.messages:
                        state.messages[-1]["content"] = user_input

    # --- Auto-compression ---
    if state.auto_compression_threshold > 0:
        non_sys = sum(1 for m in state.messages if m.get("role") != "system")
        if non_sys > state.auto_compression_threshold:
            state.messages = deps.compress_fn(
                state.messages,
                todo_tracker=state.todo_tracker,
                force=True,
                quiet=True,
            )
            if deps.context_tracker:
                deps.context_tracker.update_messages(state.messages, exclude_system=True)
            deps.save_history_fn(state.messages)

    # --- Run ReAct agent (rolling window or normal) ---
    tracker = IterationTracker(max_iterations=getattr(cfg, "MAX_ITERATIONS", 30))

    if state.rolling_window_size > 0 and state.full_messages is not None:
        if state.messages is not state.full_messages:
            state.full_messages.append(state.messages[-1])
        sys_msgs = [m for m in state.full_messages if m.get("role") == "system"]
        non_sys = [m for m in state.full_messages if m.get("role") != "system"]
        window = sys_msgs + non_sys[-(state.rolling_window_size * 2):]
        result_msgs, new_mode = deps.run_react_agent_fn(
            window, tracker, user_input,
            mode="interactive",
            agent_mode=state.agent_mode,
            todo_tracker=state.todo_tracker,
        )
        new_msgs = result_msgs[len(window):]
        state.full_messages.extend(new_msgs)
        state.messages = state.full_messages
        state.agent_mode = new_mode
    else:
        state.messages, state.agent_mode = deps.run_react_agent_fn(
            state.messages, tracker, user_input,
            mode="interactive",
            agent_mode=state.agent_mode,
            todo_tracker=state.todo_tracker,
        )

    state.is_first_turn = False

    # plan_q (first clarification turn) → plan (explore allowed next turn)
    if state.agent_mode == "plan_q":
        state.agent_mode = "plan"

    # --- Post-turn ---
    try:
        deps.on_conversation_end_fn(state.messages)
    except Exception:
        pass

    state.conversation_count += 1
    curator_interval = getattr(cfg, "CURATOR_INTERVAL", 5)
    if deps.curator and state.conversation_count % curator_interval == 0:
        try:
            deps.curator.curate()
        except Exception:
            pass

    deps.save_history_fn(state.messages)

    return state, "continue"
