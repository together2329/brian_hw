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

    # Optional Textual UI overrides (None = default sys.stdout behavior)
    emit_content_fn: Optional[Callable] = None    # (line: str) → None
    emit_reasoning_fn: Optional[Callable] = None  # (line: str, blank: bool) → None
    emit_todo_fn: Optional[Callable] = None       # (text: str) → None
    emit_flush_fn: Optional[Callable] = None      # () → None  (signal stream done → flush panel)


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
                messages.append({"role": "user", "content": guidance})
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
            messages.append({"role": "user", "content": engine.format_strategy_guidance(deep_think_result)})
            referenced_node_ids = deep_think_result.referenced_node_ids
        except Exception:
            pass

    # --- Start ESC watcher ---
    _esc_start()
    _llm_retry = 0
    _reasoning_recovery_done = False  # True after one compress-and-retry for reasoning overflow

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

        _perf = getattr(cfg, "PERF_TRACKING", False)
        _perf_iter_start = time.time()

        # Compress history if needed
        _t = time.time()
        messages = deps.compress_fn(messages, todo_tracker=todo_tracker)
        if _perf:
            print(f"  {Color.DIM}[PERF] compress: {time.time()-_t:.3f}s{Color.RESET}")

        # Refresh system prompt
        _t = time.time()
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
        if _perf:
            print(f"  {Color.DIM}[PERF] build_prompt: {time.time()-_t:.3f}s{Color.RESET}")

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

        # Per-turn todo state injection — ephemeral (appended to last user message copy,
        # never saved to history). Ensures LLM always knows the current todo state.
        if agent_mode in ("plan", "plan_q"):
            # Plan mode: show full list + strict instruction to call todo_write
            _todo_state = ""
            if todo_tracker and todo_tracker.todos:
                _lines = [f"[Current todo list — {len(todo_tracker.todos)} tasks]"]
                for _i, _t2 in enumerate(todo_tracker.todos, 1):
                    _icon = {"pending": "⏸", "in_progress": "▶", "completed": "✅", "approved": "✅", "rejected": "❌"}.get(_t2.status, "•")
                    _lines.append(f"  {_i}. {_icon} {_t2.content}")
                _todo_state = "\n" + "\n".join(_lines)
            else:
                _todo_state = "\n[No todo list yet — call todo_write() to create one]"
            _pre_llm_reminder = (
                "\n\n---\n"
                "⚠️  PLAN MODE REMINDER: Research and refine the task list.\n"
                "• Use todo_write / todo_add / todo_remove to manage tasks.\n"
                "🚫 todo_update is BLOCKED in plan mode — do not call it.\n"
                "• Do not write files or run commands — read only."
                + _todo_state
            )
        elif (todo_tracker and todo_tracker.todos
              and not todo_tracker.is_all_processed()):
            # Execution mode: inject current task reminder so the LLM always knows
            # what to work on next — critical after todo_write when no post-execution
            # reminder was injected (because _last_tool_was_todo skips it).
            _exec_reminder = todo_tracker.get_continuation_prompt()
            _recent_user = [
                m.get("content", "") for m in messages[-6:]
                if m.get("role") == "user"
            ]
            if _exec_reminder and not any(_exec_reminder in c for c in _recent_user):
                _pre_llm_reminder = "\n\n" + _exec_reminder
            else:
                _pre_llm_reminder = ""
        else:
            _pre_llm_reminder = ""

        # In ReAct text mode, append a one-line action-format hint so the model
        # knows it can emit an Action in THIS turn (no extra round-trip needed).
        _native = getattr(cfg, "ENABLE_NATIVE_TOOL_CALLS", False)
        if not _native and not plan_mode:
            _action_hint = "\n[If a tool is needed, output: Action: tool_name(param=value)]"
            _pre_llm_reminder = _pre_llm_reminder + _action_hint

        if _pre_llm_reminder:
            # Append to the last user message (ephemeral copy — avoids mutating history).
            # Skip if the reminder text is already present in that message (dedup).
            _user_idxs = [i for i, m in enumerate(messages) if m.get("role") == "user"]
            if _user_idxs:
                _ui = _user_idxs[-1]
                _uc = messages[_ui].get("content", "")
                if isinstance(_uc, str) and _pre_llm_reminder.strip() not in _uc:
                    messages[_ui] = dict(messages[_ui])  # shallow copy
                    messages[_ui]["content"] = _uc + _pre_llm_reminder

        # Hook: BEFORE_LLM_CALL
        _t = time.time()
        if deps.hook_registry:
            try:
                from core.hooks import HookContext, HookPoint
                hook_ctx = HookContext(
                    messages=messages,
                    max_context_chars=getattr(cfg, "MAX_CONTEXT_CHARS", 400000),
                    compression_threshold=getattr(cfg, "PREEMPTIVE_COMPRESSION_THRESHOLD", 0.85),
                    iteration=tracker.current,
                    metadata={"todo_tracker": todo_tracker} if todo_tracker else {},
                )
                hook_ctx = deps.hook_registry.run(HookPoint.BEFORE_LLM_CALL, hook_ctx)
                messages = hook_ctx.messages
                if hook_ctx.metadata.get("compression_needed"):
                    messages = deps.compress_fn(messages, todo_tracker=todo_tracker, force=True)
            except Exception as exc:
                import traceback
                print(f"  [Hook] Error in before_llm_call hook: {exc}")
                traceback.print_exc()
        if _perf:
            print(f"  {Color.DIM}[PERF] before_llm_hook: {time.time()-_t:.3f}s{Color.RESET}")

        # Update terminal title with current non-approved task (always visible above input)
        # Skip in TUI mode — the escape sequence would be captured by TextualCapture and
        # appear as garbled characters in the main log.
        if not deps.emit_content_fn and todo_tracker and todo_tracker.todos:
            _title_cur = next(
                (t for t in todo_tracker.todos if t.status != "approved"),
                None
            )
            if _title_cur:
                _title_idx = todo_tracker.todos.index(_title_cur) + 1
                _title_total = len(todo_tracker.todos)
                _title_icon = {"in_progress": "▶", "rejected": "✗", "completed": "✓"}.get(_title_cur.status, "•")
                _title_text = f"[{_title_idx}/{_title_total}] {_title_icon} {_title_cur.status} | {_title_cur.content[:60]}"
                sys.stdout.write(f"\033]0;{_title_text}\007")
                sys.stdout.flush()

        # Print iteration header (task label only in terminal mode — sidebar shows it in TUI)
        _todo_label = ""
        if not deps.emit_todo_fn and todo_tracker and todo_tracker.todos:
            _cur = todo_tracker.get_current_todo()
            if _cur and _cur.active_form and _cur.active_form != _cur.content:
                _todo_label = _cur.active_form
        print(format_iteration_header(
            tracker.current + 1, tracker.max_iterations,
            agent_name="primary", model=getattr(cfg, "MODEL_NAME", ""),
            todo_label=_todo_label,
        ), flush=True)

        # Notify Textual UI of current todo state
        if deps.emit_todo_fn and todo_tracker and todo_tracker.todos:
            deps.emit_todo_fn(todo_tracker.format_simple())

        # ----- Streaming LLM call -----
        from core.stream_parser import StreamParser

        # In native tool call mode, the LLM uses structured tool_calls (not Action: text),
        # so ReAct stop sequences are not needed.
        if getattr(cfg, "ENABLE_NATIVE_TOOL_CALLS", False):
            _stop_seqs = []
        else:
            _stop_seqs = ["Observation:", "<|call|>", "tool_call_begin",
                          "tool_calls_section_begin", "<|tool_call|>", "<tool_call>"]
        if _perf:
            print(f"  {Color.DIM}[PERF] >>> LLM call start{Color.RESET}")
        _stream_start = time.time()
        _aborted = False
        _debug = getattr(cfg, "DEBUG_MODE", False)

        # Terminal output buffer: batch writes every 30ms to reduce syscalls (#2 speedup)
        _out_buf: list = []
        _last_flush_t = [time.time()]
        _FLUSH_INTERVAL = 0.03  # 30ms

        def _flush_out():
            if _out_buf:
                sys.stdout.write("".join(_out_buf))
                _out_buf.clear()
                sys.stdout.flush()

        def _buf_write(text: str) -> None:
            _out_buf.append(text)
            now = time.time()
            if now - _last_flush_t[0] >= _FLUSH_INTERVAL:
                _flush_out()
                _last_flush_t[0] = now

        def _emit_content(line):
            if deps.emit_content_fn:
                deps.emit_content_fn(line)
            else:
                _buf_write(f"  {line}\n")

        def _emit_reasoning(line, blank=False):
            if deps.emit_reasoning_fn:
                deps.emit_reasoning_fn(line, blank)
            else:
                _buf_write("\n" if blank else f"  {Color.DIM}{line}{Color.RESET}\n")

        def _emit_thought(line):
            if deps.emit_content_fn:
                deps.emit_content_fn(f"Thought:{line}")
            else:
                _buf_write(f"  Thought:{line}\n")

        def _emit_blank():
            if deps.emit_content_fn:
                deps.emit_content_fn("")
            else:
                _buf_write("\n")

        _parser = StreamParser(
            emit_fn=_emit_content,
            emit_reasoning_fn=_emit_reasoning,
            emit_thought_fn=_emit_thought,
            emit_blank_fn=_emit_blank,
            reasoning_display=getattr(cfg, "REASONING_DISPLAY", False),
            reasoning_in_context=getattr(cfg, "REASONING_IN_CONTEXT", False),
            debug_mode=_debug,
        )

        _thinking_spinner = None
        # Skip stderr spinner in TUI mode — statusbar handles "generating…" feedback
        if not _debug and not deps.emit_content_fn:
            _thinking_spinner = Spinner("Thinking")
            if hasattr(_thinking_spinner, "start"):
                _thinking_spinner.start()
        elif deps.emit_content_fn:
            # Signal TUI "generating…" immediately — important for non-streaming mode
            # where the first real StreamChunk only arrives after the full response.
            deps.emit_content_fn("\x00")  # sentinel: activates statusbar without adding content
        _thinking_stopped = False

        _native_calls = []  # populated when ENABLE_NATIVE_TOOL_CALLS=true
        try:
            for chunk in deps.llm_call_fn(messages, stop=_stop_seqs):
                if not _thinking_stopped and _thinking_spinner:
                    if hasattr(_thinking_spinner, "stop"):
                        _thinking_spinner.stop()
                    _thinking_stopped = True

                if _esc_check():
                    _aborted = True
                    break

                if getattr(cfg, "STREAM_TOKEN_DELAY_MS", 0) > 0:
                    time.sleep(cfg.STREAM_TOKEN_DELAY_MS / 1000.0)

                # Native tool call sentinel: ("native_tool_calls", [...])
                if isinstance(chunk, tuple) and len(chunk) == 2 and chunk[0] == "native_tool_calls":
                    _native_calls = chunk[1]
                    continue

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
        _flush_out()  # drain any remaining buffered output

        llm_elapsed = time.time() - _stream_start

        if _aborted:
            print("\n  ⎋ Aborted by ESC. Returning to input prompt.")
            if deps.emit_flush_fn:
                deps.emit_flush_fn()   # signal TUI to flush + reset _generating
            break

        # Empty response → retry
        # Exception: native tool call mode — empty content + _native_calls is valid
        # (LLM called a tool without generating text content, which is normal)
        _has_native = bool(_native_calls)
        _use_native = _has_native  # True when native tool_calls were received
        if not collected_content.strip() and not _has_native:
            if _llm_retry < getattr(cfg, "LLM_RETRY_COUNT", 1):
                _llm_retry += 1
                print(f"\n  LLM empty response, retrying ({_llm_retry}/{cfg.LLM_RETRY_COUNT})...")
                continue
            # Recovery: reasoning likely consumed all output tokens → compress and retry
            if not _reasoning_recovery_done and deps.compress_fn:
                _reasoning_recovery_done = True
                _llm_retry = 0
                try:
                    from lib.display import Color as _C
                    print(_C.warning("\n  [Recovery] Empty response after reasoning — compressing context and retrying..."))
                except Exception:
                    print("\n  [Recovery] Empty response after reasoning — compressing context and retrying...")
                messages = deps.compress_fn(messages, force=True, quiet=False, todo_tracker=todo_tracker)
                continue
            _llm_retry = 0
            print(f"\n  LLM failed after {getattr(cfg, 'LLM_RETRY_COUNT', 1)} retry. Returning to input.")
            break
        _llm_retry = 0

        # Post-process content
        collected_content = deps.strip_tokens_fn(collected_content)
        if not getattr(cfg, "REASONING_IN_CONTEXT", False):
            collected_content = deps.strip_thinking_fn(collected_content).strip()

        # If stripping thinking tags left nothing, the model only produced reasoning.
        # Treat like an empty response (retry) rather than adding empty content to history.
        # Exception: native tool calls present = valid response with no text.
        if not collected_content.strip() and not _has_native:
            if _llm_retry < getattr(cfg, "LLM_RETRY_COUNT", 1):
                _llm_retry += 1
                # Native mode: inject a nudge so the model calls a tool instead of reasoning again.
                # Guard: if the last assistant message already has tool_calls, adding a user
                # message would violate the API contract (tool role messages must come first).
                # In that case skip the nudge — the tool execution path will handle it.
                if getattr(cfg, "ENABLE_NATIVE_TOOL_CALLS", False):
                    _last_has_tool_calls = bool(
                        messages and messages[-1].get("role") == "assistant"
                        and messages[-1].get("tool_calls")
                    )
                    if not _last_has_tool_calls:
                        messages.append({
                            "role": "user",
                            "content": "[System] You produced only reasoning with no tool call or answer. "
                                       "Please call the appropriate tool now, or provide your final answer directly."
                        })
                    print(f"\n  LLM reasoning-only, injecting nudge and retrying ({_llm_retry}/{cfg.LLM_RETRY_COUNT})...")
                else:
                    print(f"\n  LLM only generated reasoning (no content), retrying ({_llm_retry}/{cfg.LLM_RETRY_COUNT})...")
                continue

            # Recovery: reasoning overflow likely caused by full context window.
            # Force-compress history and retry once before giving up.
            if not _reasoning_recovery_done and deps.compress_fn:
                _reasoning_recovery_done = True
                _llm_retry = 0
                try:
                    from lib.display import Color as _C
                    print(_C.warning("\n  [Recovery] Reasoning overflow detected — compressing context and retrying..."))
                except Exception:
                    print("\n  [Recovery] Reasoning overflow — compressing context and retrying...")
                messages = deps.compress_fn(messages, force=True, quiet=False, todo_tracker=todo_tracker)
                continue

            _llm_retry = 0
            print(f"\n  LLM failed after retries. Returning to input.")
            break

        # Strip echoed system prompt prefix
        _first_marker = re.search(r"^(Thought:|Action:)", collected_content, re.MULTILINE)
        if _first_marker and _first_marker.start() > 0:
            prefix = collected_content[: _first_marker.start()]
            if "\n" not in prefix.strip():
                collected_content = collected_content[_first_marker.start():]

        # Token summary line
        _show_tok = getattr(cfg, "SHOW_TOKEN_STATS", True)
        _show_tok_sidebar = getattr(cfg, "SHOW_TOKEN_STATS_SIDEBAR", True)
        if not getattr(cfg, "DEBUG_MODE", False) and (_show_tok or _show_tok_sidebar):
            elapsed_str = f"{llm_elapsed:.1f}s" if llm_elapsed < 60 else f"{int(llm_elapsed//60)}m{int(llm_elapsed%60):02d}s"
            _in_tok, _out_tok = deps.get_llm_tokens_fn()
            _fk = lambda n: f"{n/1000:.1f}k" if n >= 1000 else str(n)
            if _in_tok > 0 and _out_tok > 0:
                _usage = deps.get_llm_usage_fn() if deps.get_llm_usage_fn else {}
                _cw = _usage.get("cache_created", 0)
                _cr = _usage.get("cache_read", 0)
                _in_str = f"{_fk(_in_tok)}"
                if _cw > 0 and _cr > 0:
                    _in_str += f" (cache write {_fk(_cw)} read {_fk(_cr)})"
                elif _cw > 0:
                    _in_str += f" (cache write {_fk(_cw)})"
                elif _cr > 0:
                    _in_str += f" (cache {_fk(_cr)})"
                token_str = f"in {_in_str} · out {_fk(_out_tok)} · sum {_fk(_in_tok + _out_tok)}"
            else:
                token_str = f"~{_fk(len(collected_content)//4)}"
            print(f"\n  {Color.DIM}✽ {token_str} tokens · {elapsed_str}{Color.RESET}")
        if _perf:
            print(f"  {Color.DIM}[PERF] <<< LLM call end: {llm_elapsed:.3f}s{Color.RESET}")

        # Signal TUI to flush accumulated content into a panel (guaranteed, no stdout dependency)
        if deps.emit_flush_fn:
            deps.emit_flush_fn()

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
        # Native mode: attach tool_calls to assistant message (required by API message format)
        if _use_native and _native_calls:
            assistant_msg["tool_calls"] = [
                {
                    "id": tc["id"],
                    "type": "function",
                    "function": {"name": tc["name"], "arguments": tc["arguments"]},
                }
                for tc in _native_calls
            ]
            # GLM/Z.AI requires content=null (not "") when tool_calls are present
            if not assistant_msg["content"]:
                assistant_msg["content"] = None
        messages.append(assistant_msg)

        # Hook: AFTER_LLM_CALL
        # In native mode: deferred until after tool role messages are added (below),
        # so hooks see a complete and valid assistant+tool message sequence.
        # In legacy mode: run now (no tool role messages to wait for).
        def _run_after_llm_hook():
            nonlocal messages
            if not deps.hook_registry:
                return
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

        _t = time.time()
        if not _use_native:
            _run_after_llm_hook()
        if _perf:
            print(f"  {Color.DIM}[PERF] after_llm_hook: {time.time()-_t:.3f}s{Color.RESET}")

        # Parse actions
        _t = time.time()
        if _use_native:
            # Native mode: tool calls already structured as {id, name, arguments}
            import json as _json
            actions = []
            for _tc in _native_calls:
                try:
                    _kwargs = _json.loads(_tc["arguments"] or "{}")
                    # Format as kwarg string for existing tool dispatcher
                    _args_str = ", ".join(f'{k}={_json.dumps(v, ensure_ascii=False)}' for k, v in _kwargs.items())
                except Exception:
                    _args_str = _tc.get("arguments", "")
                actions.append((_tc["name"], _args_str, "sequential"))
        else:
            try:
                from core.action_parser import parse_all_actions
            except ImportError:
                parse_all_actions = lambda text, debug=False: []
            actions = parse_all_actions(collected_content, debug=getattr(cfg, "DEBUG_MODE", False))
        if _perf:
            print(f"  {Color.DIM}[PERF] parse_actions: {time.time()-_t:.3f}s{Color.RESET}")

        # Debug: show parse result and full collected_content (including Action: block)
        if getattr(cfg, "DEBUG_MODE", False):
            _has_action_kw = "action:" in collected_content.lower()
            print(f"  {Color.DIM}[DEBUG] actions={actions}  has_action_kw={_has_action_kw}  "
                  f"detect_completion={deps.detect_completion_fn(collected_content)}{Color.RESET}")
            if _has_action_kw:
                print(f"  {Color.DIM}[DEBUG] collected_content ({len(collected_content)} chars):\n"
                      f"{collected_content}\n[DEBUG END]{Color.RESET}")

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

        # Completion signal check — skip if there are still incomplete todos
        _todo_still_active = (
            todo_tracker is not None
            and not todo_tracker.is_all_processed()
            and todo_tracker.todos
        )
        if not actions and deps.detect_completion_fn(collected_content) and not _todo_still_active:
            print(f"\n{Color.DIM}{Color.GRAY}Ending ReAct loop.{Color.RESET}\n")
            break

        # Hallucinated Observation check (legacy ReAct mode only — native mode never
        # outputs "Observation:" text, so this check is a safe no-op there)
        if not _use_native and "Observation:" in collected_content and not actions:
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
            # Track todo ops for plan mode flow control
            # Plan mode: allow research + todo ops together (don't restrict to single todo op)
            # Agent can read files AND update the plan in the same turn
            _todo_ops = {"todo_write", "todo_update", "todo_add", "todo_remove"}
            _has_todo_op = any(a[0] in _todo_ops for a in actions)
            _is_todo_write = any(a[0] == "todo_write" for a in actions)

            combined_results: List[str] = []
            _native_obs_pairs: List = []  # [(call_id, obs)] for native mode

            _SERIAL_ONLY = {"todo_update", "todo_write", "todo_add", "todo_remove"}
            _has_serial_only = any(a[0] in _SERIAL_ONLY for a in actions)

            if len(actions) > 1 and getattr(cfg, "ENABLE_REACT_PARALLEL", False) and not _has_serial_only:
                print(f"  ⚡ {len(actions)} actions (parallel)")
                
                # Pre-declare _INLINE_TOOLS to share with parallel rendering
                _INLINE_TOOLS = {"read_file", "read_lines", "grep_file", "find_files", "list_dir",
                                 "git_diff", "git_status", "todo_write", "todo_update",
                                 "todo_add", "todo_remove"}
                _DIFF_TOOLS   = {"replace_in_file", "replace_lines", "replace_file_content",
                               "git_commit", "git_push", "git_checkout", "git_branch"}
                _WRITE_TOOLS  = {"write_file", "write_to_file"}

                _write_preview_lines = getattr(cfg, "PARALLEL_WRITE_PREVIEW_LINES", 15)

                def _write_preview(obs: str) -> str:
                    """Show first N lines of written content (N from config)."""
                    if _write_preview_lines <= 0:
                        brief = format_tool_brief(tool_name, args_str, obs)
                        return f"  {Color.DIM}⎿  {brief}{Color.RESET}"
                    lines = obs.strip().splitlines()
                    shown = lines[:_write_preview_lines]
                    out = [f"  {Color.DIM}| {l}{Color.RESET}" for l in shown]
                    if len(lines) > _write_preview_lines:
                        out.append(f"  {Color.DIM}⎿ ... ({len(lines)} lines total){Color.RESET}")
                    elif out:
                        out[-1] = out[-1].replace("| ", "⎿ ", 1)
                    return "\n".join(out)

                action_results = deps.execute_parallel_fn(actions, tracker, agent_mode=agent_mode)
                for idx, tool_name, args_str, observation in action_results:
                    summary = _extract_tool_args_summary(tool_name, args_str)
                    print(format_tool_header(tool_name, summary))

                    if tool_name in _WRITE_TOOLS:
                        print(_write_preview(observation))
                    elif tool_name in _DIFF_TOOLS:
                        # Show full diff output same as sequential mode
                        print(format_tool_result(observation))
                    elif tool_name in _INLINE_TOOLS:
                        brief = format_tool_brief(tool_name, args_str, observation)
                        print(f"  {Color.DIM}⎿  {brief}{Color.RESET}")
                    else:
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
                    # Native mode: map result back to its tool_call_id using original action index
                    if _use_native and idx < len(_native_calls):
                        _native_obs_pairs.append((_native_calls[idx]["id"], observation))
            else:
                for i, action_tuple in enumerate(actions):
                    if _esc_check():
                        break

                    if len(action_tuple) == 3:
                        tool_name, args_str, _hint = action_tuple
                    else:
                        tool_name, args_str = action_tuple

                    summary = _extract_tool_args_summary(tool_name, args_str)
                    # For todo_update: inject previous status so header shows "#N prev → new"
                    if tool_name == "todo_update" and todo_tracker:
                        import re as _re
                        _idx_m = _re.search(r'index\s*=\s*(\d+)', args_str)
                        if _idx_m:
                            _idx = int(_idx_m.group(1)) - 1
                            if 0 <= _idx < len(todo_tracker.todos):
                                _prev = todo_tracker.todos[_idx].status
                                _new_m = _re.search(r'status\s*=\s*["\']([^"\']+)["\']', args_str)
                                if _new_m and _prev != _new_m.group(1):
                                    summary = f"#{_idx + 1} {_prev} → {_new_m.group(1)}"
                    tracker.record_tool(tool_name)
                    if _perf:
                        print(f"  {Color.DIM}[PERF] >>> tool/{tool_name} start{Color.RESET}")
                    tool_start = time.time()

                    _SLOW_TOOLS = {"run_command", "background_task", "background_output"}
                    _WRITE_TOOLS = {"write_file", "replace_in_file", "replace_lines"}
                    _debug = getattr(cfg, "DEBUG_MODE", False)
                    _is_plan_blocked = (
                        agent_mode in ("plan", "plan_q")
                        and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set())
                    )
                    _is_normal_blocked = (
                        agent_mode not in ("plan", "plan_q")
                        and tool_name in getattr(cfg, "NORMAL_MODE_BLOCKED_TOOLS", set())
                    )

                    # Show what we're about to do — before execution so long ops aren't silent
                    if not _debug and not _is_plan_blocked and not _is_normal_blocked:
                        print(format_tool_header(tool_name, summary))

                    if _is_plan_blocked:
                        if tool_name == "todo_update":
                            observation = (
                                "[Plan Mode] 'todo_update' is blocked in plan mode. "
                                "Use todo_write to replace the list, todo_add to add tasks, "
                                "or todo_remove to delete tasks. "
                                "todo_update is for execution mode only."
                            )
                        else:
                            observation = (
                                f"[Plan Mode] '{tool_name}' is blocked. "
                                "Only read/search and todo planning tools are available."
                            )
                    elif _is_normal_blocked:
                        observation = (
                            f"[Execution Mode] '{tool_name}' is blocked. "
                            "Use plan mode (todo_write) for task planning."
                        )
                    elif tool_name in _SLOW_TOOLS and not _debug:
                        # In TUI mode skip stderr spinner; terminal mode shows spinner
                        if deps.emit_content_fn:
                            observation = deps.execute_tool_fn(tool_name, args_str)
                        else:
                            with Spinner(f"  running…"):
                                observation = deps.execute_tool_fn(tool_name, args_str)
                    elif tool_name in _WRITE_TOOLS and not _debug:
                        if deps.emit_content_fn:
                            observation = deps.execute_tool_fn(tool_name, args_str)
                        else:
                            with Spinner(f"  writing…"):
                                observation = deps.execute_tool_fn(tool_name, args_str)
                    else:
                        observation = deps.execute_tool_fn(tool_name, args_str)

                    tool_elapsed = time.time() - tool_start
                    if _perf:
                        print(f"  {Color.DIM}[PERF] <<< tool/{tool_name}: {tool_elapsed:.3f}s{Color.RESET}")

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
                    if _is_plan_blocked or _is_normal_blocked:
                        print(format_tool_header(tool_name, summary))
                        print(format_tool_result(observation))
                    elif _debug:
                        if tool_name in ("replace_in_file", "replace_lines"):
                            print(format_tool_result(observation, max_lines=1000, max_chars=100000))
                    elif tool_name == "background_task":
                        first_line = observation.splitlines()[0] if observation.strip() else "started"
                        print(f"  {Color.DIM}{first_line}{elapsed_suffix}{Color.RESET}")
                    elif tool_name in ("replace_in_file", "replace_lines", "replace_file_content"):
                        _edit_max = getattr(cfg, "EDIT_PREVIEW_MAX_LINES", 1000)
                        if _edit_max <= 0:
                            brief = format_tool_brief(tool_name, args_str, observation)
                            print(f"  {Color.DIM}⎿  {brief}{elapsed_suffix}{Color.RESET}")
                        else:
                            print(format_tool_result(observation, max_lines=_edit_max, max_chars=_edit_max * 120))
                    elif tool_name in ("write_file", "write_to_file"):
                        _wr_lines = getattr(cfg, "WRITE_PREVIEW_LINES", 15)
                        if _wr_lines <= 0:
                            brief = format_tool_brief(tool_name, args_str, observation)
                            print(f"  {Color.DIM}⎿  {brief}{elapsed_suffix}{Color.RESET}")
                        else:
                            lines = observation.strip().splitlines()
                            shown = lines[:_wr_lines]
                            for ln in shown[:-1]:
                                print(f"  {Color.DIM}| {ln}{Color.RESET}")
                            if shown:
                                print(f"  {Color.DIM}⎿ {shown[-1]}{Color.RESET}" if len(lines) <= _wr_lines
                                      else f"  {Color.DIM}| {shown[-1]}{Color.RESET}")
                            if len(lines) > _wr_lines:
                                print(f"  {Color.DIM}⎿ ... ({len(lines)} lines total){Color.RESET}")
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
                    # Track native call ID → observation for tool role messages
                    if _use_native and i < len(_native_calls):
                        _native_obs_pairs.append((_native_calls[i]["id"], agent_observation))

                    # Refresh Textual sidebar immediately after todo changes
                    if deps.emit_todo_fn and tool_name in ("todo_update", "todo_write", "todo_add", "todo_remove") and todo_tracker:
                        # load() is a classmethod — must capture return value
                        _reloaded = type(todo_tracker).load()
                        if _reloaded.todos:
                            deps.emit_todo_fn(_reloaded.format_simple())

            observation = "\n\n".join(combined_results)

            # Native mode: ensure every tool_call_id in the assistant message has a
            # corresponding tool response. If the loop exited early (ESC, error, parallel
            # index mismatch), add placeholder messages for any unmatched calls so the
            # API message sequence remains valid.
            if _use_native and len(_native_obs_pairs) < len(_native_calls):
                _covered_ids = {cid for cid, _ in _native_obs_pairs}
                for _tc in _native_calls:
                    if _tc["id"] not in _covered_ids:
                        _native_obs_pairs.append((_tc["id"], "[Tool was not executed]"))

            # Snapshot on task approval
            if "✅ Task" in observation and "approved" in observation:
                _m = re.search(r"Task (\d+) approved", observation)
                if _m and deps.save_snapshot_fn:
                    try:
                        deps.save_snapshot_fn(int(_m.group(1)), messages)
                    except Exception:
                        pass

            # Plan mode: don't break after todo_write — agent may want to
            # continue researching or refining the changes in subsequent turns.
            # The loop will stop naturally when the agent produces text with no tool calls.

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
                    # Native mode: append pending tool messages first to keep
                    # message structure valid (assistant tool_calls must be matched)
                    if _use_native and _native_obs_pairs:
                        for _cid, _obs in _native_obs_pairs:
                            messages.append({"role": "tool", "content": _obs, "tool_call_id": _cid})
                        _native_obs_pairs = []
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

            # Build step header from todo_tracker (execution mode only)
            _step_header = ""
            if (todo_tracker and todo_tracker.todos
                and agent_mode not in ("plan", "plan_q")):
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
                    _step_header = "\n".join(header_parts) + "\n\n"

            if _use_native and _native_obs_pairs:
                # Native mode: add individual tool role messages with matching tool_call_id.
                # Inject the step header into the first tool message so the LLM knows
                # which task it is working on (in legacy mode this goes via process_obs_fn).
                for _i, (_call_id, _obs) in enumerate(_native_obs_pairs):
                    _content = (_step_header + _obs) if _i == 0 and _step_header else _obs
                    messages.append({
                        "role": "tool",
                        "content": _content,
                        "tool_call_id": _call_id,
                    })
                # Deferred AFTER_LLM_CALL hook: now that tool role messages are in place,
                # hooks see a complete and valid assistant+tool sequence.
                _run_after_llm_hook()
            else:
                observation = _step_header + observation
                messages = deps.process_obs_fn(observation, messages, todo_tracker=todo_tracker)

            # Todo continuation reminder — inject as a user message so the next LLM
            # call knows what to do. Apply in all modes (plan included).
            _last_tool_was_todo = tool_name in ("todo_update", "todo_write", "todo_add", "todo_remove")
            if (todo_tracker and todo_tracker.todos
                    and not todo_tracker.is_all_processed()
                    and not _last_tool_was_todo):
                reminder = todo_tracker.get_continuation_prompt()
                if reminder:
                    # Check all recent user messages to avoid duplicate injection
                    _recent_user_contents = [
                        m.get("content", "") for m in messages[-4:]
                        if m.get("role") == "user"
                    ]
                    if not any(reminder in c for c in _recent_user_contents):
                        messages.append({"role": "user", "content": reminder})

            if _perf:
                _iter_total = time.time() - _perf_iter_start
                print(f"  {Color.DIM}[PERF] === iteration total: {_iter_total:.3f}s ==={Color.RESET}")
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

            # Plan mode: no special iteration limit.
            # Agent stops naturally on no-tool turns (presenting plan to user).
            # Global MAX_ITERATIONS cap serves as ultimate safety net.

        else:
            # No actions branch
            if getattr(cfg, "EXECUTION_MODE", "agent") == "chat":
                if getattr(cfg, "CHAT_MAX_ITERATIONS", 1) > 0:
                    break

            # Plan mode: if no tools were called, break immediately to ask user
            if agent_mode in ("plan", "plan_q"):
                break

            if getattr(cfg, "ENABLE_TODO_TRACKING", False):
                try:
                    from lib.todo_tracker import TodoTracker
                    from pathlib import Path
                    todo_tracker = TodoTracker.load(Path(cfg.TODO_FILE))
                except Exception:
                    pass

            if todo_tracker and not todo_tracker.is_all_processed() and todo_tracker.todos:
                limit = getattr(cfg, "TODO_STAGNATION_LIMIT", 50)
                auto_advance_threshold = getattr(cfg, "TODO_AUTO_ADVANCE_THRESHOLD", max(3, limit // 10))
                count = getattr(todo_tracker, "stagnation_count", 0)
                current = todo_tracker.get_current_todo()
                # Stagnation: mark current task completed and let review prompt drive next step
                if count >= auto_advance_threshold and current and current.status == "in_progress":
                    idx = todo_tracker.current_index + 1
                    if not deps.emit_content_fn:
                        print(
                            f"\n[System] Stagnation detected on task {idx} after {count} turns — marking completed for review."
                        )
                    todo_tracker.mark_completed(todo_tracker.current_index)
                    todo_tracker.stagnation_count = 0
                    todo_tracker.save()
                    if deps.emit_todo_fn:
                        deps.emit_todo_fn(todo_tracker.format_simple())
                elif todo_tracker.check_stagnation(max_stagnation=limit):
                    hint = todo_tracker.get_stagnation_hint()
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
                if visible:
                    # Model gave a complete answer with no Action → accept and exit.
                    # The action hint is already injected into the user message
                    # (pre_llm_reminder), so no extra round-trip is needed.
                    break
                elif final_answer_attempts < 1:
                    final_answer_attempts += 1
                    messages.append({
                        "role": "user",
                        "content": "Please provide your final answer to the user based on your research so far.",
                    })
                else:
                    break

            if _perf:
                _iter_total = time.time() - _perf_iter_start
                print(f"  {Color.DIM}[PERF] === iteration total: {_iter_total:.3f}s ==={Color.RESET}")
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
