"""
Workflow Orchestrator — Flexible sequential/parallel pipeline engine

Primary agent is the orchestrator. Each todo item can be assigned a workflow
(e.g., rtl-gen, tb-gen, sim, or any custom workflow). The orchestrator:
  - Discovers all available workflows dynamically (zero hardcoded names)
  - Runs todos sequentially, in parallel, or auto-grouped by workflow
  - Each sub-agent loads the full workspace config for its assigned workflow

Usage:
    from core.workflow_orchestrator import WorkflowOrchestrator
    orch = WorkflowOrchestrator(project_root=Path("."))
    result = orch.run_todo(todo_item)
    results = orch.run_parallel([todo1, todo2, todo3])
    results = orch.run_pipeline(all_todos)
"""

import os
import sys
import time
import json
import traceback
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional, Tuple
from concurrent.futures import ThreadPoolExecutor, as_completed

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)
if _script_dir not in sys.path:
    sys.path.insert(0, _script_dir)


@dataclass
class PipelineResult:
    """Result of a single todo execution within a pipeline."""
    index: int                        # 0-based index in the todo list
    content: str                      # todo content
    workflow: str                      # workflow name used
    delegate: str                      # backend used
    status: str = "completed"          # "completed" | "error"
    output: str = ""                   # result text
    error: Optional[str] = None
    execution_time_ms: int = 0


class WorkflowOrchestrator:
    """
    Orchestrates todo execution across multiple workflows.

    Zero hardcoded workflow names — discovers all workflow/<name>/workspace.json
    directories at runtime. Users can add new workflows with zero code changes.
    """

    def __init__(self, project_root: Optional[Path] = None):
        self.project_root = project_root or Path.cwd()
        self._workflow_cache: Dict[str, Any] = {}

    # ─────────────────────────────────────────────────────────
    # Workflow Discovery
    # ─────────────────────────────────────────────────────────

    def discover_workflows(self) -> Dict[str, Path]:
        """
        Scan workflow/ directory for all workspace.json files.

        Returns:
            Dict mapping workflow name → workspace directory path.
            e.g. {"rtl-gen": Path("workflow/rtl-gen"), "tb-gen": Path("workflow/tb-gen"), ...}
        """
        workflows = {}
        workflow_root = self.project_root / "workflow"
        if not workflow_root.is_dir():
            return workflows

        for d in sorted(workflow_root.iterdir()):
            if d.is_dir() and (d / "workspace.json").exists():
                workflows[d.name] = d
        return workflows

    def workflow_exists(self, name: str) -> bool:
        """Check if a workflow name is valid (has workspace.json)."""
        return name in self.discover_workflows()

    def get_workflow_config(self, name: str) -> Optional[Any]:
        """Load and cache a WorkspaceConfig for the given workflow name."""
        if name in self._workflow_cache:
            return self._workflow_cache[name]

        try:
            from workflow.loader import load_workspace
            ws = load_workspace(name, self.project_root)
            self._workflow_cache[name] = ws
            return ws
        except Exception:
            return None

    def list_workflows(self) -> str:
        """Return formatted list of all available workflows."""
        workflows = self.discover_workflows()
        if not workflows:
            return "No workflows found. Create workflow/<name>/workspace.json to add one."

        lines = ["=== Available Workflows ==="]
        for name, path in sorted(workflows.items()):
            # Read description from workspace.json
            desc = ""
            try:
                data = json.loads((path / "workspace.json").read_text(encoding="utf-8"))
                desc = data.get("description", data.get("meta", {}).get("description", ""))
            except Exception:
                pass
            desc_part = f" — {desc}" if desc else ""
            lines.append(f"  {name}{desc_part}")

        return "\n".join(lines)

    # ─────────────────────────────────────────────────────────
    # Single Todo Execution
    # ─────────────────────────────────────────────────────────

    def run_todo(self, todo_item: Any, parent_context: str = "",
                tier: str = "sub") -> PipelineResult:
        """
        Execute a single todo item via its assigned workflow + delegate backend.

        Args:
            todo_item: TodoItem with .workflow, .delegate, .content fields
            parent_context: Additional context from primary agent

        Returns:
            PipelineResult with output/status
        """
        start_time = time.time()

        workflow_name = getattr(todo_item, 'workflow', '') or ''
        delegate = getattr(todo_item, 'delegate', '') or ''
        content = getattr(todo_item, 'content', '') or ''

        # Resolve delegate: fallback to workflow default, then no delegation
        if not delegate:
            delegate = self._get_workflow_default_delegate(workflow_name)

        if not delegate:
            return PipelineResult(
                index=0,
                content=content,
                workflow=workflow_name,
                delegate="none",
                status="error",
                error=f"No delegate backend set for task. Set via todo_write(delegate='sub-agent') or workspace default_delegate.",
            )

        # Validate workflow if specified
        if workflow_name and not self.workflow_exists(workflow_name):
            return PipelineResult(
                index=0,
                content=content,
                workflow=workflow_name,
                delegate=delegate,
                status="error",
                error=f"Workflow '{workflow_name}' not found. Available: {list(self.discover_workflows().keys())}",
            )

        # Execute via DelegateRunner
        try:
            from core.delegate_runner import DelegateRunner
            runner = DelegateRunner(project_root=self.project_root)
            output = runner.run(
                backend=delegate,
                task=content,
                context=parent_context,
                workflow_name=workflow_name,
                tier=tier,
            )

            elapsed_ms = int((time.time() - start_time) * 1000)
            return PipelineResult(
                index=0,
                content=content,
                workflow=workflow_name,
                delegate=delegate,
                status="completed",
                output=output,
                execution_time_ms=elapsed_ms,
            )
        except Exception as e:
            elapsed_ms = int((time.time() - start_time) * 1000)
            return PipelineResult(
                index=0,
                content=content,
                workflow=workflow_name,
                delegate=delegate,
                status="error",
                error=f"{e}\n{traceback.format_exc()}",
                execution_time_ms=elapsed_ms,
            )

    # ─────────────────────────────────────────────────────────
    # Sequential Pipeline
    # ─────────────────────────────────────────────────────────

    def run_sequential(self, todos: List[Any], parent_context: str = "",
                       tier: str = "sub") -> List[PipelineResult]:
        """
        Run todos one-by-one. Each result feeds into the next todo's context.

        Args:
            todos: List of TodoItem objects
            parent_context: Initial context

        Returns:
            List of PipelineResult, one per todo
        """
        results = []
        accumulated_context = parent_context

        for i, todo in enumerate(todos):
            result = self.run_todo(todo, parent_context=accumulated_context, tier=tier)
            result.index = i
            results.append(result)

            # Feed result into next iteration's context
            if result.status == "completed" and result.output:
                accumulated_context = f"{accumulated_context}\n\n[Previous task result: {todo.content}]\n{result.output[:2000]}"
            elif result.error:
                accumulated_context = f"{accumulated_context}\n\n[Previous task error: {todo.content}]\n{result.error[:500]}"

        return results

    # ─────────────────────────────────────────────────────────
    # Parallel Pipeline
    # ─────────────────────────────────────────────────────────

    def run_parallel(self, todos: List[Any], max_workers: int = 3,
                     parent_context: str = "", tier: str = "sub") -> List[PipelineResult]:
        """
        Run independent todos simultaneously via ThreadPoolExecutor.

        Args:
            todos: List of TodoItem objects
            max_workers: Maximum concurrent workers
            parent_context: Shared context for all workers

        Returns:
            List of PipelineResult, sorted by original index
        """
        if not todos:
            return []

        results: List[Optional[PipelineResult]] = [None] * len(todos)
        workers = min(len(todos), max(1, max_workers))

        with ThreadPoolExecutor(max_workers=workers) as executor:
            future_map = {}
            for i, todo in enumerate(todos):
                future = executor.submit(self.run_todo, todo, parent_context, tier)
                future_map[future] = i

            for future in as_completed(future_map):
                idx = future_map[future]
                try:
                    result = future.result()
                    result.index = idx
                    results[idx] = result
                except Exception as e:
                    results[idx] = PipelineResult(
                        index=idx,
                        content=getattr(todos[idx], 'content', ''),
                        workflow=getattr(todos[idx], 'workflow', ''),
                        delegate=getattr(todos[idx], 'delegate', ''),
                        status="error",
                        error=str(e),
                    )

        return [r for r in results if r is not None]

    # ─────────────────────────────────────────────────────────
    # Auto Pipeline (smart grouping)
    # ─────────────────────────────────────────────────────────

    def run_pipeline(self, todos: List[Any], max_workers: int = 3,
                     parent_context: str = "", tier: str = "sub") -> List[PipelineResult]:
        """
        Auto-analyze todos and run with optimal parallelism.

        Strategy:
        1. Group todos by their 'workflow' field
        2. Within each workflow group, run in parallel
        3. Between different workflow groups, run sequentially
        4. Todos with no workflow run sequentially as a final group

        This allows e.g.:
          - All rtl-gen tasks run in parallel
          - All tb-gen tasks run in parallel
          - But tb-gen waits for rtl-gen to complete

        Args:
            todos: List of TodoItem objects
            max_workers: Maximum concurrent workers per group
            parent_context: Shared context

        Returns:
            List of PipelineResult, sorted by original index
        """
        if not todos:
            return []

        # Group by workflow, preserving original indices
        workflow_groups: Dict[str, List[Tuple[int, Any]]] = {}
        no_workflow: List[Tuple[int, Any]] = []

        for i, todo in enumerate(todos):
            wf = getattr(todo, 'workflow', '') or ''
            if wf:
                workflow_groups.setdefault(wf, []).append((i, todo))
            else:
                no_workflow.append((i, todo))

        all_results: Dict[int, PipelineResult] = {}
        accumulated_context = parent_context

        # Run each workflow group sequentially, parallel within
        for wf_name, group_items in workflow_groups.items():
            group_todos = [todo for _, todo in group_items]
            group_indices = [idx for idx, _ in group_items]

            group_results = self.run_parallel(
                group_todos, max_workers=max_workers,
                parent_context=accumulated_context, tier=tier,
            )

            # Map results back to original indices
            for j, result in enumerate(group_results):
                orig_idx = group_indices[j]
                result.index = orig_idx
                all_results[orig_idx] = result

            # Feed group results into context for next group
            group_outputs = []
            for r in group_results:
                if r.output:
                    group_outputs.append(f"[{r.workflow}: {r.content}] → {r.output[:500]}")
            if group_outputs:
                accumulated_context += "\n\n[Completed workflow group: " + wf_name + "]\n" + "\n".join(group_outputs)

        # Run no-workflow todos sequentially
        if no_workflow:
            seq_todos = [todo for _, todo in no_workflow]
            seq_indices = [idx for idx, _ in no_workflow]

            seq_results = self.run_sequential(seq_todos, parent_context=accumulated_context)
            for j, result in enumerate(seq_results):
                orig_idx = seq_indices[j]
                result.index = orig_idx
                all_results[orig_idx] = result

        # Return sorted by original index
        return [all_results[i] for i in sorted(all_results.keys())]

    # ─────────────────────────────────────────────────────────
    # Helpers
    # ─────────────────────────────────────────────────────────

    def _get_workflow_default_delegate(self, workflow_name: str) -> str:
        """Get the default_delegate for a workflow from its workspace.json."""
        if not workflow_name:
            return ""
        try:
            ws = self.get_workflow_config(workflow_name)
            if ws and hasattr(ws, 'default_delegate'):
                return ws.default_delegate
        except Exception:
            pass
        return ""

    def format_pipeline_results(self, results: List[PipelineResult]) -> str:
        """Format pipeline results for display."""
        if not results:
            return "No results."

        lines = ["=== Pipeline Results ==="]
        for r in results:
            icon = "✅" if r.status == "completed" else "❌"
            wf_part = f" [{r.workflow}]" if r.workflow else ""
            delegate_part = f" via {r.delegate}" if r.delegate else " (no delegate)"
            time_part = f" ({r.execution_time_ms}ms)" if r.execution_time_ms else ""
            lines.append(f"  {icon} Task {r.index + 1}: {r.content}{wf_part}{delegate_part}{time_part}")

            if r.output:
                # Show first 200 chars of output
                preview = r.output[:200]
                if len(r.output) > 200:
                    preview += "..."
                lines.append(f"     {preview}")
            if r.error:
                lines.append(f"     Error: {r.error[:200]}")

        completed = sum(1 for r in results if r.status == "completed")
        total = len(results)
        lines.append(f"\n  Summary: {completed}/{total} completed")
        return "\n".join(lines)
