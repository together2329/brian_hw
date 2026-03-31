"""
core/react_loop.py — Phase 6 extraction

Provides:
  - _dedup_line(text)          : pure helper — remove intra-line repetition
  - _make_is_dup()             : factory returning (seen_set, is_dup_fn)
  - ReactLoopDeps              : dataclass bundling all injected dependencies
  - run_react_agent_impl(...)  : extracted ReAct loop body with injected deps
"""
from __future__ import annotations

import re
import sys
import time
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Set, Tuple

from lib.display import Color


# ---------------------------------------------------------------------------
# Pure stream-display helpers (extracted from the nested closures in main.py)
# ---------------------------------------------------------------------------

def _dedup_line(text: str) -> str:
    """Remove intra-line repetition using a 50-char sliding window.

    If a 50-char segment appears more than once in *text*, truncate at the
    second occurrence.  Strings shorter than 100 chars are returned unchanged.
    """
    if len(text) < 100:
        return text
    for i in range(min(len(text) // 2, 600)):
        seg = text[i:i + 50]
        if len(seg) < 50:
            break
        j = text.find(seg, i + 50)
        if j > i:
            return text[:j].rstrip()
    return text


def _make_is_dup() -> Tuple[Set[str], Callable[[str], bool]]:
    """Return *(seen, is_dup_fn)* sharing the same dedup set.

    *seen*      — the mutable set of already-printed lines.
    *is_dup_fn* — checks whether *text* is already in *seen* (exact or
                  70%-substring overlap for long strings).
    """
    seen: Set[str] = set()

    def is_dup(text: str) -> bool:
        if text in seen:
            return True
        if len(text) > 60:
            for prev in seen:
                shorter, longer = (text, prev) if len(text) <= len(prev) else (prev, text)
                if len(shorter) > len(longer) * 0.7 and shorter in longer:
                    return True
        return False

    return seen, is_dup


# ---------------------------------------------------------------------------
# Dependency injection dataclass
# ---------------------------------------------------------------------------

@dataclass
class ReactLoopDeps:
    """All external dependencies for run_react_agent_impl.

    Callers (main.py wrapper) inject live globals at call time so the
    implementation stays pure and testable.
    """
    # Config namespace (must expose all config.X attributes used by the loop)
    cfg: Any

    # LLM streaming call: (messages, stop=...) → Iterator[str | tuple]
    llm_call_fn: Callable

    # Core operations
    compress_fn: Callable          # compress_history(messages, **kwargs) → messages
    build_prompt_fn: Callable      # build_system_prompt(messages, ...) → str | dict
    process_obs_fn: Callable       # process_observation(obs, messages, **kwargs) → messages
    execute_tool_fn: Callable      # execute_tool(tool_name, args_str) → str
    execute_parallel_fn: Callable  # execute_actions_parallel(actions, tracker, ...) → list
    save_trajectory_fn: Callable   # save_procedural_trajectory(...) → None

    # Display helpers
    show_context_usage_fn: Callable           # show_context_usage(messages) → None
    show_iteration_warning_fn: Callable       # show_iteration_warning(tracker, mode) → str

    # Content processing (pure-ish, but injected for testability)
    strip_tokens_fn: Callable      # _strip_native_tool_tokens(text) → str
    strip_thinking_fn: Callable    # _strip_thinking_tags(text) → str
    parse_todo_fn: Callable        # _parse_todo_markdown(text) → list
    detect_completion_fn: Callable # detect_completion_signal(text) → bool

    # Accessors for global state (read-only)
    get_turn_id_fn: Callable       # () → int (current_turn_id)
    get_llm_usage_fn: Callable     # () → dict | None (llm_client.get_last_usage())
    get_llm_tokens_fn: Callable    # () → (input_tokens, output_tokens)

    # Optional subsystems (None if not enabled)
    orchestrator: Optional[Any] = None
    procedural_memory: Optional[Any] = None
    graph_lite: Optional[Any] = None
    hook_registry: Optional[Any] = None

    # Tool registry
    available_tools: Dict[str, Callable] = field(default_factory=dict)

    # Optional helpers (None = feature disabled)
    inject_strategy_fn: Optional[Callable] = None    # _maybe_inject_exploration_strategy
    save_snapshot_fn: Optional[Callable] = None      # _save_conv_snapshot
    load_snapshot_fn: Optional[Callable] = None      # _load_conv_snapshot
    build_prompt_str_fn: Optional[Callable] = None   # _build_system_prompt_str()

    # Session recovery state accessors
    get_recovery_state_fn: Optional[Callable] = None
    # () → (recovery_point, session_manager, session_id) or (None, None, None)

    # ESC key abort (injectable for testing; defaults to EscapeWatcher)
    esc_check_fn: Optional[Callable] = None  # () → bool
    esc_start_fn: Optional[Callable] = None  # () → None
    esc_stop_fn: Optional[Callable] = None   # () → None


# ---------------------------------------------------------------------------
# Main ReAct loop implementation
# ---------------------------------------------------------------------------

def run_react_agent_impl(
    messages: List[Dict],
    tracker: Any,
    task_description: str,
    deps: ReactLoopDeps,
    mode: str = "interactive",
    preface_enabled: bool = True,
    agent_mode: str = "normal",
    todo_tracker: Any = None,
) -> Tuple[List[Dict], str]:
    """Extracted ReAct agent loop body with all dependencies injected.

    Args:
        messages:         Conversation history (mutated in-place style, returned).
        tracker:          IterationTracker instance.
        task_description: Human-readable task description.
        deps:             All external dependencies (see ReactLoopDeps).
        mode:             'interactive' or 'oneshot'.
        preface_enabled:  Whether to run orchestrator/deep-think prelude.
        agent_mode:       'normal', 'plan', 'plan_q', or 'chat'.
        todo_tracker:     Pre-existing TodoTracker (overridden if ENABLE_TODO_TRACKING).

    Returns:
        (updated_messages, agent_mode)
    """
    cfg = deps.cfg

    # --- Resolve display helpers ---
    try:
        from lib.display import (
            EscapeWatcher, Spinner,
            format_iteration_header, format_tool_header, format_tool_result,
            format_tool_brief, _extract_tool_args_summary, _friendly_tool_name,
        )
    except ImportError:
        # Minimal stubs for environments without lib.display
        class _NoopEsc:
            @staticmethod
            def start(): pass
            @staticmethod
            def stop(): pass
            @staticmethod
            def check(): return False
        EscapeWatcher = _NoopEsc  # type: ignore

        class Spinner:  # type: ignore
            def __init__(self, *a, **kw): pass
            def __enter__(self): return self
            def __exit__(self, *a): pass
            def start(self): pass
            def stop(self): pass

        def format_iteration_header(*a, **kw): return ""
        def format_tool_header(*a, **kw): return ""
        def format_tool_result(*a, **kw): return ""
        def format_tool_brief(*a, **kw): return ""
        def _extract_tool_args_summary(*a, **kw): return ""
        def _friendly_tool_name(n): return n

    # Use injected ESC functions if provided (for testing), else use EscapeWatcher
    _esc_check = deps.esc_check_fn if deps.esc_check_fn is not None else EscapeWatcher.check
    _esc_start = deps.esc_start_fn if deps.esc_start_fn is not None else EscapeWatcher.start
    _esc_stop  = deps.esc_stop_fn  if deps.esc_stop_fn  is not None else EscapeWatcher.stop

    try:
        from lib.iteration_control import show_iteration_warning as _show_iter_warn
    except ImportError:
        _show_iter_warn = deps.show_iteration_warning_fn

    # --- State ---
    consecutive_errors = 0
    last_error_observation = None
    MAX_CONSECUTIVE_ERRORS = getattr(cfg, "MAX_CONSECUTIVE_ERRORS", 3)
    recovery_attempts = 0
    final_answer_attempts = 0
    _chat_iter_count = 0
    actions_taken: List[Any] = []
    referenced_node_ids: List[str] = []

    # --- Todo tracker setup ---
    if getattr(cfg, "ENABLE_TODO_TRACKING", False):
        try:
            from lib.todo_tracker import TodoTracker
            from pathlib import Path
            todo_tracker = TodoTracker.load(Path(cfg.TODO_FILE))
        except Exception:
            todo_tracker = None
    else:
        todo_tracker = None

    # --- Accumulated context (sub-agent communication) ---
    accumulated_context: Dict[str, list] = {
        "explored_files": [],
        "planned_steps": [],
        "agent_artifacts": {},
        "exploration_summaries": [],
        "plan_summaries": [],
    }

    # --- Prelude: strategy injection ---
    if preface_enabled and deps.inject_strategy_fn:
        if deps.inject_strategy_fn(messages, task_description):
            print("[System] Agent delegation strategy injected.\n")

    # --- Prelude: orchestrator ---
    if preface_enabled and getattr(cfg, "ENABLE_SUB_AGENTS", False) and deps.orchestrator:
        try:
            context_parts = []
            for msg in messages[-5:]:
                if msg.get("role") != "system":
                    content = str(msg.get("content", ""))[:200]
                    context_parts.append(f"{msg['role']}: {content}")
            import os as _os
            try:
                context_parts.append(f"Current directory: {', '.join(_os.listdir('.')[:20])}")
            except Exception:
                pass
            ctx = {"recent_messages": "\n".join(context_parts)}
            result = deps.orchestrator.run(task=task_description, context=ctx)
            if result.final_output:
                guidance = (
                    f"=== SUB-AGENT ANALYSIS ===\n{result.final_output[:2000]}\n"
                    "===========================\n\n"
                    "Use the above analysis to guide your response. "
                    "Continue with the ReAct loop if more actions are needed."
                )
                messages.append({"role": "system", "content": guidance})
        except Exception:
            pass

    # --- Prelude: deep think (legacy, no orchestrator) ---
    elif preface_enabled and getattr(cfg, "ENABLE_DEEP_THINK", False) and not getattr(cfg, "ENABLE_SUB_AGENTS", False):
        try:
            from core.deep_think import DeepThinkEngine, format_deep_think_output
            engine = DeepThinkEngine(
                procedural_memory=deps.procedural_memory,
                graph_lite=deps.graph_lite,
                llm_call_func=deps.llm_call_fn,
                execute_tool_func=deps.execute_tool_fn,
            )
            context_parts = []
            for msg in messages[-5:]:
                if msg.get("role") != "system":
                    context_parts.append(f"{msg['role']}: {str(msg.get('content',''))[:200]}")
            deep_think_result = engine.think(task=task_description, context="\n".join(context_parts))
            messages.append({"role": "system", "content": engine.format_strategy_guidance(deep_think_result)})
            referenced_node_ids = deep_think_result.referenced_node_ids
        except Exception:
            pass

    # --- Start ESC watcher ---
    _esc_start()
    _llm_retry = 0

    # ======================================================================
    # Main loop
    # ======================================================================
    while True:
        # ESC abort check
        if _esc_check():
            print("\n  ⎋ Aborted by ESC. Returning to input prompt.")
            break

        # Iteration limit
        warning_action = deps.show_iteration_warning_fn(tracker, mode=mode)
        if warning_action == "stop":
            break
        elif warning_action == "extend":
            tracker.extend(20)

        # Compress history if needed
        messages = deps.compress_fn(messages, todo_tracker=todo_tracker)

        # Refresh system prompt
        if getattr(cfg, "ENABLE_SMART_RAG", False) or getattr(cfg, "DEBUG_MODE", False) or getattr(cfg, "ENABLE_SKILL_SYSTEM", False):
            user_messages = [m for m in messages if m.get("role") == "user"]
            current_query = user_messages[-1].get("content", "")[:100] if user_messages else ""
            last_rag_query = getattr(tracker, "_last_rag_query", None)
            if tracker.current == 0 or current_query != last_rag_query:
                tracker._last_rag_query = current_query
                system_prompt_data = deps.build_prompt_fn(
                    messages,
                    allowed_tools=set(deps.available_tools.keys()) if deps.available_tools else None,
                    agent_mode=agent_mode,
                )
                if messages and messages[0].get("role") == "system":
                    if getattr(cfg, "CACHE_OPTIMIZATION_MODE", "legacy") == "optimized" and isinstance(system_prompt_data, dict):
                        blocks = []
                        if system_prompt_data.get("static"):
                            blocks.append({"type": "text", "text": system_prompt_data["static"], "cache_control": {"type": "ephemeral"}})
                        if system_prompt_data.get("dynamic"):
                            blocks.append({"type": "text", "text": system_prompt_data["dynamic"]})
                        messages[0]["content"] = blocks if blocks else system_prompt_data.get("static", "")
                    else:
                        messages[0]["content"] = system_prompt_data

        # Inject accumulated context
        if accumulated_context and any(v for v in accumulated_context.values() if v):
            ctx_lines: List[str] = []
            if accumulated_context.get("explored_files"):
                files = accumulated_context["explored_files"]
                ctx_lines.append(f"Files examined: {len(files)}")
            if accumulated_context.get("planned_steps"):
                ctx_lines.append(f"Planned steps: {len(accumulated_context['planned_steps'])}")
            if ctx_lines and messages and messages[0].get("role") == "system":
                ctx_msg = "\n\n[Agent Communication Context]\n" + "\n".join(ctx_lines)
                content = messages[0].get("content", "")
                if isinstance(content, str):
                    messages[0]["content"] = content + ctx_msg
                elif isinstance(content, list):
                    messages[0]["content"].append({"type": "text", "text": ctx_msg})

        # Hook: BEFORE_LLM_CALL
        if deps.hook_registry:
            try:
                from core.hooks import HookContext, HookPoint
                hook_ctx = HookContext(
                    messages=messages,
                    max_context_chars=getattr(cfg, "MAX_CONTEXT_CHARS", 400000),
                    compression_threshold=getattr(cfg, "CONTEXT_COMPRESSION_THRESHOLD", 0.80),
                    iteration=tracker.current,
                    metadata={"todo_tracker": todo_tracker} if todo_tracker else {},
                )
                hook_ctx = deps.hook_registry.run(HookPoint.BEFORE_LLM_CALL, hook_ctx)
                messages = hook_ctx.messages
                if hook_ctx.metadata.get("compression_needed"):
                    messages = deps.compress_fn(messages, todo_tracker=todo_tracker, force=True)
            except Exception:
                pass

        # Print iteration header
        print(format_iteration_header(
            tracker.current + 1, tracker.max_iterations,
            agent_name="primary", model=getattr(cfg, "MODEL_NAME", ""),
        ), flush=True)

        # ----- Streaming LLM call -----
        from core.stream_parser import StreamParser

        _stop_seqs = ["Observation:", "<|call|>", "tool_call_begin",
                      "tool_calls_section_begin", "<|tool_call|>", "<tool_call>"]
        _stream_start = time.time()
        _aborted = False
        _debug = getattr(cfg, "DEBUG_MODE", False)

        def _emit_content(line):
            sys.stdout.write(f"  {line}\n")
            sys.stdout.flush()

        def _emit_reasoning(line, blank=False):
            if blank:
                sys.stdout.write("\n")
            else:
                sys.stdout.write(f"  {Color.DIM}{line}{Color.RESET}\n")
            sys.stdout.flush()

        def _emit_thought(line):
            sys.stdout.write(f"  Thought:{line}\n")
            sys.stdout.flush()

        def _emit_blank():
            sys.stdout.write("\n")
            sys.stdout.flush()

        _parser = StreamParser(
            emit_fn=_emit_content,
            emit_reasoning_fn=_emit_reasoning,
            emit_thought_fn=_emit_thought,
            emit_blank_fn=_emit_blank,
            reasoning_display=getattr(cfg, "REASONING_DISPLAY", False),
            reasoning_in_context=getattr(cfg, "REASONING_IN_CONTEXT", False),
        )

        _thinking_spinner = None
        if not _debug:
            _thinking_spinner = Spinner("Thinking")
            if hasattr(_thinking_spinner, "start"):
                _thinking_spinner.start()
        _thinking_stopped = False

        try:
            for chunk in deps.llm_call_fn(messages, stop=_stop_seqs):
                if not _thinking_stopped and _thinking_spinner:
                    if hasattr(_thinking_spinner, "stop"):
                        _thinking_spinner.stop()
                    _thinking_stopped = True

                if _esc_check():
                    _aborted = True
                    break

                if _debug:
                    # In debug mode just collect, skip display
                    if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "reasoning":
                        if getattr(cfg, "REASONING_IN_CONTEXT", False):
                            _parser.collected += chunk[1]
                    else:
                        _parser.collected += chunk  # type: ignore[operator]
                    continue

                if getattr(cfg, "STREAM_TOKEN_DELAY_MS", 0) > 0:
                    time.sleep(cfg.STREAM_TOKEN_DELAY_MS / 1000.0)

                _parser.feed(chunk)

        except Exception as e:
            if _thinking_spinner and not _thinking_stopped:
                if hasattr(_thinking_spinner, "stop"):
                    _thinking_spinner.stop()
                _thinking_stopped = True
            if not _parser.collected:
                print(f"\n  LLM call failed: {e}")
                break

        # Guarantee spinner is stopped
        if _thinking_spinner and not _thinking_stopped:
            if hasattr(_thinking_spinner, "stop"):
                _thinking_spinner.stop()
            _thinking_stopped = True

        collected_content = _parser.flush()

        llm_elapsed = time.time() - _stream_start

        if _aborted:
            print("\n  ⎋ Aborted by ESC. Returning to input prompt.")
            break

        # Empty response → retry
        if not collected_content.strip():
            if _llm_retry < getattr(cfg, "LLM_RETRY_COUNT", 1):
                _llm_retry += 1
                print(f"\n  LLM empty response, retrying ({_llm_retry}/{cfg.LLM_RETRY_COUNT})...")
                continue
            _llm_retry = 0
            print(f"\n  LLM failed after {getattr(cfg, 'LLM_RETRY_COUNT', 1)} retry. Returning to input.")
            break
        _llm_retry = 0

        # Post-process content
        collected_content = deps.strip_tokens_fn(collected_content)
        if not getattr(cfg, "REASONING_IN_CONTEXT", False):
            collected_content = deps.strip_thinking_fn(collected_content).strip()

        # Strip echoed system prompt prefix
        _first_marker = re.search(r"^(Thought:|Action:)", collected_content, re.MULTILINE)
        if _first_marker and _first_marker.start() > 0:
            prefix = collected_content[: _first_marker.start()]
            if "\n" not in prefix.strip():
                collected_content = collected_content[_first_marker.start():]

        # Token summary line
        if not getattr(cfg, "DEBUG_MODE", False):
            elapsed_str = f"{llm_elapsed:.1f}s" if llm_elapsed < 60 else f"{int(llm_elapsed//60)}m{int(llm_elapsed%60):02d}s"
            _in_tok, _out_tok = deps.get_llm_tokens_fn()
            _fk = lambda n: f"{n/1000:.1f}k" if n >= 1000 else str(n)
            if _in_tok > 0 and _out_tok > 0:
                token_str = f"in {_fk(_in_tok)} · out {_fk(_out_tok)} · sum {_fk(_in_tok + _out_tok)}"
            else:
                token_str = f"~{_fk(len(collected_content)//4)}"
            print(f"  ✽ {token_str} tokens")

        print()

        # Build assistant message
        assistant_msg: Dict[str, Any] = {
            "role": "assistant",
            "content": collected_content,
            "turn_id": deps.get_turn_id_fn(),
            "timestamp": time.time(),
        }
        usage = deps.get_llm_usage_fn()
        if usage:
            assistant_msg["_tokens"] = usage
        messages.append(assistant_msg)

        # Hook: AFTER_LLM_CALL
        if deps.hook_registry:
            try:
                from core.hooks import HookContext, HookPoint
                hook_ctx = HookContext(
                    messages=messages,
                    iteration=tracker.current,
                    metadata={"todo_tracker": todo_tracker} if todo_tracker else {},
                )
                hook_ctx = deps.hook_registry.run(HookPoint.AFTER_LLM_CALL, hook_ctx)
                messages = hook_ctx.messages
            except Exception:
                pass

        # Parse actions
        try:
            from core.action_parser import parse_all_actions
        except ImportError:
            parse_all_actions = lambda text, debug=False: []

        actions = parse_all_actions(collected_content, debug=getattr(cfg, "DEBUG_MODE", False))

        # Chat mode 0: respond only
        if getattr(cfg, "EXECUTION_MODE", "agent") == "chat":
            if getattr(cfg, "CHAT_MAX_ITERATIONS", 1) == 0:
                break

        # Todo tracking: auto-parse markdown plans
        markdown_tasks = deps.parse_todo_fn(collected_content)
        if markdown_tasks and not any(a[0] == "todo_write" for a in actions):
            _todo_write_func = deps.available_tools.get("todo_write") if deps.available_tools else None
            if _todo_write_func:
                observation = _todo_write_func(markdown_tasks)
                print(format_tool_header("todo_write", "Auto-parsed from markdown plan"))
                print(format_tool_result(observation, max_lines=1000, max_chars=100000))

        # Completion signal check
        if not actions and deps.detect_completion_fn(collected_content):
            print("\n[System] ✅ Task completion detected. Ending ReAct loop.\n")
            break

        # Hallucinated Observation check
        if "Observation:" in collected_content and not actions:
            print("  [System] ⚠️  Agent hallucinated an Observation. Correcting...")
            messages.append({
                "role": "user",
                "content": (
                    "[System] You generated 'Observation:' yourself. "
                    "PLEASE DO NOT DO THIS. You must output an Action, wait for me to "
                    "execute it, and then I will give you the Observation. Now, please "
                    "output the correct Action."
                ),
            })
            continue

        if actions:
            # Plan mode: restrict to single todo op
            _todo_ops = {"todo_write", "todo_update", "todo_add", "todo_remove"}
            _has_todo_op = any(a[0] in _todo_ops for a in actions)
            _is_todo_write = any(a[0] == "todo_write" for a in actions)
            if _has_todo_op and agent_mode in ("plan", "plan_q"):
                _todo_action = next(a for a in actions if a[0] in _todo_ops)
                actions = [_todo_action]

            combined_results: List[str] = []

            if len(actions) > 1 and getattr(cfg, "ENABLE_REACT_PARALLEL", False):
                print(f"  ⚡ {len(actions)} actions (parallel)")
                action_results = deps.execute_parallel_fn(actions, tracker, agent_mode=agent_mode)
                for idx, tool_name, args_str, observation in action_results:
                    summary = _extract_tool_args_summary(tool_name, args_str)
                    print(format_tool_header(tool_name, summary))
                    print(format_tool_result(observation))

                    if deps.procedural_memory is not None:
                        try:
                            from lib.procedural_memory import Action
                            obs_lower = observation.lower()
                            is_error = any(x in obs_lower for x in ["error:", "exception:", "traceback"])
                            action_result = "error" if is_error else "success"
                            actions_taken.append(Action(
                                tool=tool_name, args=args_str[:100],
                                result=action_result, observation=observation[:200],
                            ))
                        except Exception:
                            pass

                    combined_results.append(f"--- [Action {idx+1}] {tool_name} ---\n{observation}")
            else:
                for i, action_tuple in enumerate(actions):
                    if _esc_check():
                        break

                    if len(action_tuple) == 3:
                        tool_name, args_str, _hint = action_tuple
                    else:
                        tool_name, args_str = action_tuple

                    summary = _extract_tool_args_summary(tool_name, args_str)
                    tracker.record_tool(tool_name)
                    tool_start = time.time()

                    _SLOW_TOOLS = {"run_command", "background_task", "background_output"}
                    _debug = getattr(cfg, "DEBUG_MODE", False)
                    _is_plan_blocked = (
                        agent_mode in ("plan", "plan_q")
                        and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set())
                    )

                    # Show what we're about to do — before execution so long ops aren't silent
                    if not _debug and not _is_plan_blocked:
                        print(format_tool_header(tool_name, summary))

                    if _is_plan_blocked:
                        observation = (
                            f"[Plan Mode] '{tool_name}' is blocked. "
                            "Only read/search tools are available."
                        )
                    elif tool_name in _SLOW_TOOLS and not _debug:
                        friendly = _friendly_tool_name(tool_name)
                        with Spinner(f"  running…"):
                            observation = deps.execute_tool_fn(tool_name, args_str)
                    else:
                        observation = deps.execute_tool_fn(tool_name, args_str)

                    tool_elapsed = time.time() - tool_start

                    # Lint error warning for todo_update(completed)
                    if tool_name == "todo_update" and "completed" in args_str:
                        _has_lint = any(
                            "❌" in r and ("error" in r.lower() or "linting" in r.lower())
                            for r in combined_results
                        )
                        if _has_lint:
                            observation += "\n⚠️ LINT ERRORS detected — fix before approving."

                    obs_lower = observation.lower()
                    is_error = any(x in obs_lower for x in ["error:", "exception:", "traceback", "syntax error", "compilation failed"])
                    if tool_name in ["read_file", "read_lines", "grep_file"] and "error" in obs_lower:
                        if not observation.strip().lower().startswith("error:"):
                            is_error = False

                    if deps.procedural_memory is not None:
                        try:
                            from lib.procedural_memory import Action
                            action_result = "error" if is_error else "success"
                            actions_taken.append(Action(
                                tool=tool_name, args=args_str[:100],
                                result=action_result, observation=observation[:200],
                            ))
                        except Exception:
                            pass

                    # Display result (header already printed before execution above)
                    _INLINE_TOOLS = {"read_file", "read_lines", "grep_file", "find_files", "list_dir",
                                     "git_diff", "git_status", "write_file", "todo_write", "todo_update",
                                     "todo_add", "todo_remove"}
                    elapsed_suffix = f" · {tool_elapsed:.1f}s" if tool_elapsed >= 1.0 else ""
                    if _is_plan_blocked:
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation))
                    elif _debug:
                        if tool_name in ("replace_in_file", "replace_lines"):
                            print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name == "background_task":
                        first_line = observation.splitlines()[0] if observation.strip() else "started"
                        print(f"  {Color.DIM}{first_line}{elapsed_suffix}{Color.RESET}")
                    elif tool_name in ("replace_in_file", "replace_lines"):
                        print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name in ("todo_update", "todo_write") and agent_mode in ("plan", "plan_q"):
                        print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name in _INLINE_TOOLS:
                        brief = format_tool_brief(tool_name, args_str, observation)
                        print(f"  {Color.DIM}⎿  {brief}{elapsed_suffix}{Color.RESET}")
                    else:
                        print(format_tool_result(observation))

                    # Truncate write tool results for LLM context
                    agent_observation = observation
                    _WRITE_TOOLS = {"write_to_file", "replace_file_content", "multi_replace_file_content",
                                    "replace_in_file", "replace_lines", "todo_write"}
                    if tool_name in _WRITE_TOOLS and not is_error:
                        _obs_lines = observation.splitlines()
                        if len(_obs_lines) > 5:
                            agent_observation = "\n".join(_obs_lines[:5]) + "\n\n(Remaining output truncated.)"

                    combined_results.append(f"--- [Action {i+1}] {tool_name} ---\n{agent_observation}")

            observation = "\n\n".join(combined_results)

            # Snapshot on task approval
            if "✅ Task" in observation and "approved" in observation:
                _m = re.search(r"Task (\d+) approved", observation)
                if _m and deps.save_snapshot_fn:
                    try:
                        deps.save_snapshot_fn(int(_m.group(1)), messages)
                    except Exception:
                        pass

            # Break after todo_write (plan step-by-step)
            if _is_todo_write:
                break

            # Consecutive error tracking
            if observation == last_error_observation:
                consecutive_errors += 1
                print(f"  [System] ⚠️  Consecutive error #{consecutive_errors}/{MAX_CONSECUTIVE_ERRORS}")

                # Session recovery
                if (consecutive_errors >= 2 and
                        recovery_attempts < getattr(cfg, "MAX_RECOVERY_ATTEMPTS", 2) and
                        getattr(cfg, "ENABLE_SESSION_RECOVERY", False) and
                        deps.get_recovery_state_fn):
                    try:
                        recovery_point, session_mgr, session_id = deps.get_recovery_state_fn()
                        if recovery_point and session_mgr:
                            recovery_attempts += 1
                            success = session_mgr.recovery.rollback_to_point(session_id, recovery_point)
                            if success:
                                messages = messages[:recovery_point.message_count]
                                consecutive_errors = 0
                    except Exception:
                        pass

                if consecutive_errors >= MAX_CONSECUTIVE_ERRORS:
                    messages.append({
                        "role": "user",
                        "content": (
                            f"Observation: {observation}\n\n"
                            f"[System] The same error occurred {MAX_CONSECUTIVE_ERRORS} times. "
                            "Please ask the user for help or try a different approach."
                        ),
                    })
                    break
            else:
                consecutive_errors = 0
                recovery_attempts = 0
                last_error_observation = observation if "error" in observation.lower() else None

            # Reload todo_tracker after tool execution
            if getattr(cfg, "ENABLE_TODO_TRACKING", False):
                try:
                    from lib.todo_tracker import TodoTracker
                    from pathlib import Path
                    todo_tracker = TodoTracker.load(Path(cfg.TODO_FILE))
                except Exception:
                    pass

            # Prepend step header from todo_tracker
            if todo_tracker and todo_tracker.todos:
                current_todo = todo_tracker.get_current_todo()
                total = len(todo_tracker.todos)
                completed = sum(1 for t in todo_tracker.todos if t.status == "approved")
                if current_todo:
                    header_parts = [f"[Step {completed + 1}/{total}: {current_todo.content}]"]
                    if current_todo.rejection_reason:
                        header_parts.append(f"⚠️  Previously rejected: {current_todo.rejection_reason}")
                    if current_todo.detail:
                        header_parts.append(f"Detail: {current_todo.detail}")
                    if current_todo.criteria:
                        header_parts.append(f"Criteria: {current_todo.criteria}")
                    header_parts.append("→ Interpret the result below in context of the current goal")
                    observation = "\n".join(header_parts) + "\n\n" + observation

            messages = deps.process_obs_fn(observation, messages, todo_tracker=todo_tracker)

            # Todo continuation reminder
            _last_tool_was_todo = tool_name in ("todo_update", "todo_write", "todo_add")
            if (todo_tracker and todo_tracker.todos
                    and not todo_tracker.is_all_processed()
                    and not _last_tool_was_todo):
                reminder = todo_tracker.get_continuation_prompt()
                if reminder:
                    last_content = messages[-1].get("content", "") if messages else ""
                    if reminder not in last_content:
                        messages.append({"role": "user", "content": reminder})

            tracker.increment()

            # Step-by-step mode
            if getattr(cfg, "STEP_BY_STEP_MODE", False) and (combined_results or _is_todo_write):
                break

            # Chat mode N≥1
            if getattr(cfg, "EXECUTION_MODE", "agent") == "chat":
                _chat_max = getattr(cfg, "CHAT_MAX_ITERATIONS", 1)
                if _chat_max > 0:
                    _chat_iter_count += 1
                    if _chat_iter_count >= _chat_max:
                        break

        else:
            # No actions branch
            if getattr(cfg, "EXECUTION_MODE", "agent") == "chat":
                if getattr(cfg, "CHAT_MAX_ITERATIONS", 1) > 0:
                    break

            if getattr(cfg, "ENABLE_TODO_TRACKING", False):
                try:
                    from lib.todo_tracker import TodoTracker
                    from pathlib import Path
                    todo_tracker = TodoTracker.load(Path(cfg.TODO_FILE))
                except Exception:
                    pass

            if todo_tracker and not todo_tracker.is_all_processed() and todo_tracker.todos:
                if todo_tracker.check_stagnation(max_stagnation=getattr(cfg, "TODO_STAGNATION_LIMIT", 50)):
                    hint = todo_tracker.get_stagnation_hint()
                    limit = getattr(cfg, "TODO_STAGNATION_LIMIT", 50)
                    count = getattr(todo_tracker, "stagnation_count", limit)
                    print(
                        f"\n[System] Todo stagnation: tried {count}/{limit} times without progress.\n"
                        f"  {hint}\n"
                        f"  Waiting for user feedback."
                    )
                    break
                reminder = todo_tracker.get_continuation_prompt()
                if reminder:
                    last_content = messages[-1].get("content", "") if messages else ""
                    if reminder not in last_content:
                        messages.append({"role": "user", "content": reminder})
                # Don't break — continue
            else:
                visible = deps.strip_thinking_fn(collected_content).strip()
                if len(visible) < 10 and final_answer_attempts < 2:
                    final_answer_attempts += 1
                    messages.append({
                        "role": "user",
                        "content": "Please provide your final answer to the user based on your research so far.",
                    })
                else:
                    break

            tracker.increment()

            if getattr(cfg, "EXECUTION_MODE", "agent") == "chat":
                _chat_max = getattr(cfg, "CHAT_MAX_ITERATIONS", 1)
                if _chat_max > 0:
                    _chat_iter_count += 1
                    if _chat_iter_count >= _chat_max:
                        break

    # ======================================================================
    # Post-loop cleanup
    # ======================================================================
    _esc_stop()

    # Save procedural trajectory
    if deps.procedural_memory is not None and actions_taken:
        has_errors = any(a.result == "error" for a in actions_taken)
        outcome = "failure" if has_errors else "success"
        try:
            deps.save_trajectory_fn(
                task_description=task_description,
                actions_taken=actions_taken,
                outcome=outcome,
                iterations=tracker.current,
            )
        except Exception:
            pass

    # ACE credit assignment
    if deps.graph_lite and referenced_node_ids and getattr(cfg, "ENABLE_CREDIT_TRACKING", False):
        has_errors = any(a.result == "error" for a in actions_taken) if actions_taken else False
        tag = "harmful" if has_errors else "helpful"
        try:
            updated = deps.graph_lite.update_node_credits(referenced_node_ids, tag)
            if updated > 0:
                deps.graph_lite.save()
        except Exception:
            pass

    return messages, agent_mode
