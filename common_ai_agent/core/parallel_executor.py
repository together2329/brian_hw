"""
core/parallel_executor.py
Phase 8: extracted from main.py execute_actions_parallel() + _execute_batch_parallel()

Provides:
  execute_batch_parallel()    — run a pre-batched list of actions in parallel
  execute_actions_parallel()  — full orchestration (dependency analysis → batching → execution)
"""
import traceback
from concurrent.futures import ThreadPoolExecutor, wait
from typing import Any, Callable, List, Optional, Tuple

from core.action_dependency import ActionDependencyAnalyzer, FileConflictDetector

# ---------------------------------------------------------------------------
# Read-only tools eligible for automatic parallel execution (legacy mode)
# ---------------------------------------------------------------------------

# Tools that must NEVER execute in parallel with any other tool
SERIAL_ONLY_TOOLS = frozenset({"todo_update", "todo_write"})

PARALLEL_ELIGIBLE_TOOLS = frozenset({
    "read_file",
    "read_lines",
    "grep_file",
    "list_dir",
    "find_files",
    "git_status",
    "git_diff",
    "analyze_verilog_module",
    "find_signal_usage",
    "find_module_definition",
    "extract_module_hierarchy",
    "find_potential_issues",
    "analyze_timing_paths",
})


# ---------------------------------------------------------------------------
# execute_batch_parallel
# ---------------------------------------------------------------------------

def execute_batch_parallel(
    batch_actions: List[Tuple],
    *,
    execute_tool_fn: Callable,
    cfg: Any,
) -> List[Tuple[int, str, str, str]]:
    """
    Execute a list of (idx, tool_name, args_str[, kwargs_dict]) in parallel.

    If a 4-tuple (idx, tool_name, args_str, kwargs_dict) is provided,
    kwargs_dict is passed as pre_parsed_kwargs to execute_tool_fn to avoid
    lossy JSON round-trips for native tool calls with complex content.

    Returns:
        List of (idx, tool_name, args_str, observation) sorted by idx.
    """
    if not batch_actions:
        return []

    results = []
    max_workers = min(len(batch_actions), max(1, getattr(cfg, "REACT_MAX_WORKERS", 4)))
    timeout = getattr(cfg, "REACT_ACTION_TIMEOUT", 30)

    def _call(tool_name, args_str, kwargs_dict):
        if kwargs_dict is not None:
            try:
                return execute_tool_fn(tool_name, args_str, pre_parsed_kwargs=kwargs_dict)
            except TypeError:
                pass  # execute_tool_fn doesn't support pre_parsed_kwargs — fall through
        return execute_tool_fn(tool_name, args_str)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {}
        for entry in batch_actions:
            if len(entry) == 4:
                idx, tool_name, args_str, kwargs_dict = entry
            else:
                idx, tool_name, args_str = entry
                kwargs_dict = None
            future = executor.submit(_call, tool_name, args_str, kwargs_dict)
            future_map[future] = (idx, tool_name, args_str)

        done, not_done = wait(future_map.keys(), timeout=timeout)

        for future in done:
            idx, tool_name, args_str = future_map[future]
            try:
                observation = future.result()
            except Exception as e:
                observation = f"Error: Exception in parallel execution: {e}\n{traceback.format_exc()}"
            results.append((idx, tool_name, args_str, observation))

        for future in not_done:
            idx, tool_name, args_str = future_map[future]
            try:
                future.cancel()
            except Exception:
                pass
            results.append((idx, tool_name, args_str, f"Error: Timeout after {timeout}s"))

    results.sort(key=lambda x: x[0])
    return results


# ---------------------------------------------------------------------------
# execute_actions_parallel
# ---------------------------------------------------------------------------

def execute_actions_parallel(
    actions: List,
    *,
    tracker: Any,
    agent_mode: str = "normal",
    cfg: Any,
    execute_tool_fn: Callable[[str, str], str],
    print_fn: Callable = print,
) -> List[Tuple[int, str, str, str]]:
    """
    Execute actions with intelligent parallelism.

    Claude Code Style Strategy:
    - Analyze action dependencies via ActionDependencyAnalyzer
    - Read-only tools → parallel; write tools → sequential barrier
    - File conflict detection → automatic warning

    Args:
        actions:          List of (tool, args) or (tool, args, hint) tuples.
        tracker:          IterationTracker — record_tool() called for each action.
        agent_mode:       Current agent mode ('normal', 'plan', 'plan_q', …).
        cfg:              Config namespace.
        execute_tool_fn:  Callable(tool_name, args_str) → str.
        print_fn:         Output function (default: print). Inject for testing.

    Returns:
        List of (idx, tool_name, args_str, observation) sorted by original index.
    """
    if not actions:
        return []

    results: List[Tuple[int, str, str, str]] = []

    # Separate kwargs_dict (4th element) from the 3-tuple used by dependency analyzer.
    # kwargs_map: idx → kwargs_dict for native pre-parsed kwargs pass-through.
    _kwargs_map: dict = {}
    _indexed_actions = []  # (idx, tool_name, args_str) — always 3-tuple
    for entry in actions:
        if len(entry) == 4:
            idx, tool_name, args_str, kw = entry
            _kwargs_map[idx] = kw
        else:
            idx, tool_name, args_str = entry[:3]
        _indexed_actions.append((idx, tool_name, args_str))
        tracker.record_tool(tool_name)

    def _exec(tool_name, args_str, idx):
        kw = _kwargs_map.get(idx)
        if kw is not None:
            try:
                return execute_tool_fn(tool_name, args_str, pre_parsed_kwargs=kw)
            except TypeError:
                pass
        return execute_tool_fn(tool_name, args_str)

    use_enhanced = getattr(cfg, "ENABLE_ENHANCED_PARALLEL", True)

    if use_enhanced:
        # === Enhanced Mode: ActionDependencyAnalyzer ===
        # analyzer expects (tool_name, args_str, hint) and stores (enum_idx, tool_name, args_str)
        # in batch.actions. Build a map from enum_idx → orig_idx to restore after analysis.
        _analyzer_actions = [(tool_name, args_str, None) for orig_idx, tool_name, args_str in _indexed_actions]
        _enum_to_orig = {pos: orig_idx for pos, (orig_idx, _, _) in enumerate(_indexed_actions)}

        analyzer = ActionDependencyAnalyzer()
        batches = analyzer.analyze(_analyzer_actions)

        # batch.actions is (enum_idx, tool_name, args_str) — remap enum_idx → orig_idx
        for batch in batches:
            batch.actions = [
                (_enum_to_orig.get(enum_idx, enum_idx), tool_name, args_str)
                for enum_idx, tool_name, args_str in batch.actions
            ]

        detector = FileConflictDetector()
        all_indexed_actions = []
        for batch in batches:
            all_indexed_actions.extend(batch.actions)

        warnings = detector.check_conflicts(all_indexed_actions, analyzer)
        for warning in warnings:
            print_fn(warning)

        for batch in batches:
            if batch.parallel and len(batch.actions) > 1 and getattr(cfg, "ENABLE_REACT_PARALLEL", True):
                # todo_update/todo_write must never run in parallel — execute only the first action
                if any(tool_name in SERIAL_ONLY_TOOLS for _, tool_name, _ in batch.actions):
                    first_idx, first_tool, first_args = batch.actions[0]
                    observation = _exec(first_tool, first_args, first_idx)
                    results.append((first_idx, first_tool, first_args, observation))
                    for idx, tool_name, args_str in batch.actions[1:]:
                        results.append((idx, tool_name, args_str,
                            f"[Skipped] '{tool_name}' was queued in parallel with todo_update — "
                            "todo tools must run alone. Re-issue this call separately."))
                    continue

                allowed_actions = []
                for idx, tool_name, args_str in batch.actions:
                    is_any_plan = agent_mode in ("plan", "plan_q")
                    if is_any_plan and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set()):
                        observation = f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."
                        results.append((idx, tool_name, args_str, observation))
                    else:
                        kw = _kwargs_map.get(idx)
                        allowed_actions.append((idx, tool_name, args_str, kw) if kw is not None else (idx, tool_name, args_str))

                if allowed_actions:
                    if getattr(cfg, "DEBUG_MODE", False):
                        print_fn(f"  ⚡ Parallel batch: {len(allowed_actions)} action(s)")
                    batch_results = execute_batch_parallel(
                        allowed_actions,
                        execute_tool_fn=execute_tool_fn,
                        cfg=cfg,
                    )
                    results.extend(batch_results)
            else:
                for idx, tool_name, args_str in batch.actions:
                    is_any_plan = agent_mode in ("plan", "plan_q")
                    if is_any_plan and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set()):
                        observation = f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."
                    else:
                        observation = _exec(tool_name, args_str, idx)
                    results.append((idx, tool_name, args_str, observation))

    else:
        # === Legacy Mode: allowlist-based ===
        parallel_batch: List[Tuple[int, str, str]] = []

        def flush_parallel():
            nonlocal parallel_batch
            if not parallel_batch:
                return
            # todo_update/todo_write must never run in parallel — execute only the first action
            if any(t in SERIAL_ONLY_TOOLS for _, t, _ in parallel_batch):
                first_idx, first_tool, first_args = parallel_batch[0]
                observation = execute_tool_fn(first_tool, first_args)
                results.append((first_idx, first_tool, first_args, observation))
                for idx, tool_name, args_str in parallel_batch[1:]:
                    results.append((idx, tool_name, args_str,
                        f"[Skipped] '{tool_name}' was queued in parallel with todo_update — "
                        "todo tools must run alone. Re-issue this call separately."))
                parallel_batch = []
                return
            if len(parallel_batch) == 1 or not getattr(cfg, "ENABLE_REACT_PARALLEL", True):
                idx, tool_name, args_str = parallel_batch[0]
                observation = execute_tool_fn(tool_name, args_str)
                results.append((idx, tool_name, args_str, observation))
                parallel_batch = []
                return
            print_fn(f"  ⚡ Parallel batch: {len(parallel_batch)} action(s)")
            batch_results = execute_batch_parallel(
                parallel_batch,
                execute_tool_fn=execute_tool_fn,
                cfg=cfg,
            )
            results.extend(batch_results)
            parallel_batch = []

        for entry in _indexed_actions:
            idx, tool_name, args_str = entry

            # Mode-based tool blocking (legacy path)
            is_any_plan = agent_mode in ("plan", "plan_q")
            if is_any_plan and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set()):
                results.append((idx, tool_name, args_str,
                    f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."))
                continue
            if not is_any_plan and tool_name in getattr(cfg, "NORMAL_MODE_BLOCKED_TOOLS", set()):
                results.append((idx, tool_name, args_str,
                    f"[Execution Mode] '{tool_name}' is blocked. Use plan mode for task planning."))
                continue

            if tool_name in PARALLEL_ELIGIBLE_TOOLS:
                parallel_batch.append((idx, tool_name, args_str))
                continue

            flush_parallel()
            observation = _exec(tool_name, args_str, idx)
            results.append((idx, tool_name, args_str, observation))

        flush_parallel()

    results.sort(key=lambda x: x[0])
    return results
