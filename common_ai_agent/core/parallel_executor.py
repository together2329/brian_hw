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
    batch_actions: List[Tuple[int, str, str]],
    *,
    execute_tool_fn: Callable[[str, str], str],
    cfg: Any,
) -> List[Tuple[int, str, str, str]]:
    """
    Execute a list of (idx, tool_name, args_str) in parallel using ThreadPoolExecutor.

    Returns:
        List of (idx, tool_name, args_str, observation) sorted by idx.
    """
    if not batch_actions:
        return []

    results = []
    max_workers = min(len(batch_actions), max(1, getattr(cfg, "REACT_MAX_WORKERS", 4)))
    timeout = getattr(cfg, "REACT_ACTION_TIMEOUT", 30)

    with ThreadPoolExecutor(max_workers=max_workers) as executor:
        future_map = {
            executor.submit(execute_tool_fn, tool_name, args_str): (idx, tool_name, args_str)
            for idx, tool_name, args_str in batch_actions
        }

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

    for action in actions:
        tool_name = action[0]
        tracker.record_tool(tool_name)

    use_enhanced = getattr(cfg, "ENABLE_ENHANCED_PARALLEL", True)

    if use_enhanced:
        # === Enhanced Mode: ActionDependencyAnalyzer ===
        analyzer = ActionDependencyAnalyzer()
        batches = analyzer.analyze(actions)

        detector = FileConflictDetector()
        all_indexed_actions = []
        for batch in batches:
            all_indexed_actions.extend(batch.actions)

        warnings = detector.check_conflicts(all_indexed_actions, analyzer)
        for warning in warnings:
            print_fn(warning)

        for batch in batches:
            if batch.parallel and len(batch.actions) > 1 and getattr(cfg, "ENABLE_REACT_PARALLEL", True):
                allowed_actions = []
                for idx, tool_name, args_str in batch.actions:
                    is_any_plan = agent_mode in ("plan", "plan_q")
                    if is_any_plan and tool_name in getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set()):
                        observation = f"[Plan Mode] '{tool_name}' is blocked. Only read/search tools are available."
                        results.append((idx, tool_name, args_str, observation))
                    else:
                        allowed_actions.append((idx, tool_name, args_str))

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
                        observation = execute_tool_fn(tool_name, args_str)
                    results.append((idx, tool_name, args_str, observation))

    else:
        # === Legacy Mode: allowlist-based ===
        parallel_batch: List[Tuple[int, str, str]] = []

        def flush_parallel():
            nonlocal parallel_batch
            if not parallel_batch:
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

        for idx, action_tuple in enumerate(actions):
            if len(action_tuple) == 3:
                tool_name, args_str, hint = action_tuple
            else:
                tool_name, args_str = action_tuple

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
            observation = execute_tool_fn(tool_name, args_str)
            results.append((idx, tool_name, args_str, observation))

        flush_parallel()

    results.sort(key=lambda x: x[0])
    return results
