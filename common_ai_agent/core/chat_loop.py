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
import os
import re
from dataclasses import dataclass, field
from typing import Any, Callable, List, Optional, Tuple

from lib.iteration_control import IterationTracker
from core.plan_mode import PLAN_CONFIRM_EXECUTE_PROMPT, is_plan_confirm_input
from core.prompt_input import prompt_has_content


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
    # When set, the loop runs without interactive prompts: max-iterations is
    # never blocked by a `(y/n)` confirm, and EOFError on stdin is treated as
    # a clean termination signal rather than an abnormal exit. Designed so the
    # workflow can be driven from a CI job, a parent agent, or `--prompt-file`
    # without leaving a zombie process waiting on input.
    headless: bool = False


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


def _todo_has_open_items(todo_tracker: Any) -> bool:
    if not todo_tracker or not getattr(todo_tracker, "todos", None):
        return False
    has_open = getattr(todo_tracker, "has_open_items", None)
    if callable(has_open):
        try:
            return bool(has_open())
        except Exception:
            pass
    try:
        from lib.todo_tracker import todo_items_have_open_work
        return todo_items_have_open_work(getattr(todo_tracker, "todos", []))
    except Exception:
        return any(
            getattr(item, "status", "") != "approved"
            for item in getattr(todo_tracker, "todos", [])
        )


def _is_execution_resume_request(user_input: str) -> bool:
    text = str(user_input or "").strip().lower()
    if not text:
        return False
    # Anti-resume guards override positive cues: a STOP/negation or a progress-
    # status query must never read as a resume, even when it shares a prefix with
    # a resume word (e.g. "진행 상황" overlaps the "진행 " prefix below).
    negations = (
        "don't", "do not", "dont", "stop", "instead", "not this", "cancel",
        "그만", "말고", "하지마", "하지 마", "아니", "취소",
    )
    if any(neg in text for neg in negations):
        return False
    if "진행 상황" in text or "진행상황" in text:
        return False
    exact = {
        "continue",
        "keep going",
        "go ahead",
        "proceed",
        "resume",
        "run",
        "execute",
        "start",
        "진행",
        "계속",
        "계속해",
        "다시",
        "해",
        "시작",
    }
    if text in exact:
        return True
    prefixes = (
        "continue ",
        "keep going",
        "go ahead",
        "proceed ",
        "resume ",
        "run ",
        "execute ",
        "start ",
        "진행 ",
        "계속 ",
        "다시 ",
        "시작 ",
    )
    if text.startswith(prefixes):
        return True
    # Short natural-language resume nudge ("can you keep going?"). Anchor English
    # cues to word boundaries so "discontinue" never matches "continue"; long
    # messages are treated as new intent rather than a bare resume.
    if len(re.findall(r"[0-9a-z가-힣]+", text)) > 6:
        return False
    english_cues = ("keep going", "go ahead", "continue", "proceed", "resume")
    if any(re.search(r"\b" + re.escape(cue) + r"\b", text) for cue in english_cues):
        return True
    return "계속" in text or "진행" in text


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
    if not prompt_has_content(user_input):
        return state, "skip"

    # Atlas process workers receive the UI mode on every prompt envelope and
    # expose it through env before this function runs. Reconcile that runtime
    # truth with ChatLoopState so a plan-confirm reply (`y`/`yc`) is not treated
    # as ordinary chat when local state was stale.
    _env_plan = str(os.environ.get("PLAN_MODE", "")).strip().lower() == "true"
    _env_agent_mode = str(os.environ.get("AGENT_MODE_OVERRIDE", "")).strip()
    if (
        state.agent_mode not in ("plan", "plan_q")
        and (_env_plan or _env_agent_mode in ("plan", "plan_q"))
    ):
        state.agent_mode = _env_agent_mode if _env_agent_mode in ("plan", "plan_q") else "plan_q"

    # --- Plan mode confirmation ---
    if state.agent_mode in ("plan", "plan_q"):
        inp = user_input.lower().strip()

        # y / yes / confirm → execute plan
        if is_plan_confirm_input(inp):
            do_compress = (inp == "yc")
            state.agent_mode = "normal"
            import os as _os; _os.environ["PLAN_MODE"] = "false"
            # Also clear the cross-process plan override. In the Atlas web UI the
            # `y` prompt arrives with the envelope still stamped plan_mode=true
            # (the UI pill is still on PLAN), so session_worker.input() set
            # AGENT_MODE_OVERRIDE="plan_q". Without overwriting it to "normal"
            # here, react_loop's mid-loop override (pops AGENT_MODE_OVERRIDE at
            # the top of each iteration) immediately demotes this turn back to
            # plan_q — the "I can't start execution, still in PLAN MODE" bug.
            _os.environ["AGENT_MODE_OVERRIDE"] = "normal"
            _os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)

            # Notify the atlas / textual frontend so its mode pill flips.
            # Without this, backend silently transitions plan_q→normal but
            # the UI keeps showing "PLAN" and the user wonders why writes
            # are happening in what looks like read-only mode.
            try:
                import main as _main_mod  # type: ignore
                _emit_mode = getattr(_main_mod, "_textual_emit_mode_fn", None)
                if _emit_mode is not None:
                    _emit_mode("normal")
            except Exception:
                pass

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
                user_input = PLAN_CONFIRM_EXECUTE_PROMPT

            if state.messages:
                state.messages[-1]["content"] = user_input

            if do_compress:
                state.messages = deps.compress_fn(
                    state.messages,
                    todo_tracker=state.todo_tracker,
                    force=True,
                    emit_summary=False,
                )

        # n / no → cancel
        elif inp in ("n", "no", "cancel", "취소", "아니오", "ㄴㄴ"):
            user_input = (
                "I've reviewed the plan and I'm NOT ready to execute yet. "
                "Let's refine it further or address my concerns."
            )

        # Otherwise: treat as feedback and fall through to run_react_agent.
        # Short text such as "Hi" is still valid feedback in Atlas plan mode.

    # --- Keep-going signal ---
    if getattr(cfg, "ENABLE_TODO_TRACKING", False) and state.todo_tracker:
        inp = user_input.lower().strip()
        if any(x in inp for x in ("keep going", "continue", "진행", "계속")):
            unprocess_rejected = getattr(state.todo_tracker, "unprocess_rejected", None)
            if callable(unprocess_rejected) and unprocess_rejected():
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
                emit_summary=False,
            )
            if deps.context_tracker:
                deps.context_tracker.update_messages(state.messages, exclude_system=True)
            deps.save_history_fn(state.messages)

    # A STOP during execution pauses the active TODO loop. Until the user sends
    # an explicit resume-like prompt, let normal text act as normal chat/new
    # instruction instead of injecting the current TODO and tripping the
    # no-Action guard.
    if (
        os.environ.get("ATLAS_EXECUTION_PAUSED_AFTER_STOP") == "1"
        and state.agent_mode not in ("plan", "plan_q")
    ):
        if _is_execution_resume_request(user_input):
            os.environ.pop("ATLAS_EXECUTION_PAUSED_AFTER_STOP", None)
            os.environ.pop("ATLAS_EXECUTION_PAUSED_SESSION", None)
        elif _todo_has_open_items(state.todo_tracker):
            os.environ["ATLAS_SUPPRESS_TODO_EXECUTION_ONCE"] = "1"
        else:
            os.environ.pop("ATLAS_EXECUTION_PAUSED_AFTER_STOP", None)
            os.environ.pop("ATLAS_EXECUTION_PAUSED_SESSION", None)

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
            mode=("oneshot" if state.headless else "interactive"),
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
            mode=("oneshot" if state.headless else "interactive"),
            agent_mode=state.agent_mode,
            todo_tracker=state.todo_tracker,
        )

    state.is_first_turn = False

    # plan_q (first clarification turn) → plan (explore allowed next turn)
    if state.agent_mode == "plan_q":
        state.agent_mode = "plan"

    # --- Post-turn ---
    # Push fresh context-token estimate to the sidebar so the "Context"
    # panel actually moves after each LLM turn. The cost panel updates on
    # every emit_token_fn call (per-call delta) but context only refreshed
    # via /compact and /clear handlers — meaning a long conversation never
    # showed real token usage growth in the UI.
    try:
        import main as _main_mod  # type: ignore
        _ctx_emit = getattr(_main_mod, "_textual_emit_context_fn", None)
        if _ctx_emit is not None:
            from llm_client import estimate_message_tokens as _ctx_est  # type: ignore
            _ctx_max = getattr(cfg, "MAX_CONTEXT_TOKENS", 0)
            _ctx_used = sum(_ctx_est(m) for m in state.messages)
            _ctx_emit(_ctx_used, _ctx_max)
    except Exception:
        pass

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
