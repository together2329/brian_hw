"""
Background Agent Manager

Primary Agent가 background_task tool로 sub-agent를 spawn하고,
background_output tool로 결과를 수신하는 매니저.

ThreadPoolExecutor 기반으로 최대 3개의 동시 실행 지원.
"""

import os
import sys
import time
import uuid
import threading
from concurrent.futures import ThreadPoolExecutor, Future
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional

# Ensure import paths
_script_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(_script_dir)
if _project_root not in sys.path:
    sys.path.insert(0, _project_root)


@dataclass
class BackgroundTask:
    """Background agent task 정보"""
    id: str                                   # "bg_xxxxxxxx"
    agent: str                                # "explore", "plan", "execute", "review"
    prompt: str                               # 작업 설명
    status: str = "running"                   # "running" | "completed" | "error" | "cancelled"
    result: Optional[str] = None              # 압축된 결과 (≤2000 tokens)
    error: Optional[str] = None               # 에러 메시지
    created_at: float = field(default_factory=time.time)
    completed_at: Optional[float] = None
    execution_time_ms: int = 0
    token_usage: Dict[str, int] = field(default_factory=dict)
    # Internal
    _future: Optional[Any] = field(default=None, repr=False)


class BackgroundManager:
    """
    Background agent task 관리.

    Primary Agent가 tool로 사용:
    - background_task(agent, prompt) → task_id
    - background_output(task_id) → 결과
    - background_cancel(task_id) → 취소
    - background_list() → 모든 task 상태

    Usage:
        manager = BackgroundManager(max_workers=3)
        task_id = manager.launch("explore", "Find all Verilog modules")
        # ... later ...
        output = manager.get_output(task_id)
    """

    def __init__(self, max_workers: int = 3):
        self._executor = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="bg_agent"
        )
        self._tasks: Dict[str, BackgroundTask] = {}
        self._lock = threading.Lock()

    def launch(
        self,
        agent: str,
        prompt: str,
        parent_context: str = "",
        model_override: Optional[str] = None,
        max_iterations: Optional[int] = None,
    ) -> str:
        """
        Background agent 실행.

        Args:
            agent: Agent 타입 (explore, plan, execute, review)
            prompt: 작업 설명
            parent_context: Primary agent에서 전달하는 context
            model_override: 모델 오버라이드
            max_iterations: 최대 반복 횟수

        Returns:
            task_id (str): "bg_xxxxxxxx" 형식
        """
        task_id = f"bg_{uuid.uuid4().hex[:8]}"

        task = BackgroundTask(
            id=task_id,
            agent=agent,
            prompt=prompt,
        )

        # Submit to thread pool
        future = self._executor.submit(
            self._run_agent,
            task_id,
            agent,
            prompt,
            parent_context,
            model_override,
            max_iterations,
        )
        task._future = future

        with self._lock:
            self._tasks[task_id] = task

        return task_id

    def get_output(self, task_id: str) -> str:
        """
        Task 결과 조회.

        Returns:
            - Running: "Task {id} is still running (elapsed: Xs)"
            - Completed: 압축된 결과
            - Error: 에러 메시지
        """
        with self._lock:
            task = self._tasks.get(task_id)

        if not task:
            return f"Error: Task '{task_id}' not found."

        if task.status == "running":
            elapsed = time.time() - task.created_at
            return (
                f"Task {task_id} ({task.agent}) is still running.\n"
                f"Elapsed: {elapsed:.1f}s\n"
                f"Prompt: {task.prompt[:100]}...\n"
                f"[Try again later with background_output(task_id=\"{task_id}\")]"
            )
        elif task.status == "completed":
            return (
                f"=== Background Task Result: {task_id} ({task.agent}) ===\n"
                f"Status: completed in {task.execution_time_ms}ms\n\n"
                f"{task.result}"
            )
        elif task.status == "error":
            return (
                f"=== Background Task Error: {task_id} ({task.agent}) ===\n"
                f"Error: {task.error}\n"
                f"Elapsed: {task.execution_time_ms}ms"
            )
        elif task.status == "cancelled":
            return f"Task {task_id} was cancelled."
        else:
            return f"Task {task_id} has unknown status: {task.status}"

    def cancel(self, task_id: str) -> str:
        """Task 취소"""
        with self._lock:
            task = self._tasks.get(task_id)

        if not task:
            return f"Error: Task '{task_id}' not found."

        if task.status != "running":
            return f"Task {task_id} is already {task.status}."

        if task._future:
            task._future.cancel()

        task.status = "cancelled"
        task.completed_at = time.time()
        return f"Task {task_id} cancelled."

    def list_tasks(self) -> str:
        """모든 task 상태 목록"""
        with self._lock:
            tasks = list(self._tasks.values())

        if not tasks:
            return "No background tasks."

        lines = ["=== Background Tasks ==="]
        for task in tasks:
            elapsed = (task.completed_at or time.time()) - task.created_at
            status_icon = {
                "running": "⏳",
                "completed": "✅",
                "error": "❌",
                "cancelled": "🚫",
            }.get(task.status, "❓")

            lines.append(
                f"{status_icon} {task.id} | {task.agent} | {task.status} | "
                f"{elapsed:.1f}s | {task.prompt[:60]}..."
            )

        return "\n".join(lines)

    def _run_agent(
        self,
        task_id: str,
        agent: str,
        prompt: str,
        parent_context: str,
        model_override: Optional[str],
        max_iterations: Optional[int],
    ):
        """Thread에서 실행되는 agent runner"""
        try:
            import config
            from core.agent_runner import run_agent_session

            max_iter = max_iterations or getattr(config, 'BACKGROUND_MAX_ITERATIONS', 15)

            result = run_agent_session(
                agent_name=agent,
                prompt=prompt,
                model_override=model_override,
                max_iterations=max_iter,
                parent_context=parent_context,
                verbose=getattr(config, 'DEBUG_MODE', False),
            )

            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    if result.status == "completed":
                        task.status = "completed"
                        task.result = result.output
                    else:
                        task.status = "error"
                        task.error = result.error or result.output
                    task.completed_at = time.time()
                    task.execution_time_ms = result.execution_time_ms
                    task.token_usage = result.token_usage

        except Exception as e:
            import traceback
            with self._lock:
                task = self._tasks.get(task_id)
                if task:
                    task.status = "error"
                    task.error = f"{e}\n{traceback.format_exc()}"
                    task.completed_at = time.time()
                    task.execution_time_ms = int(
                        (time.time() - task.created_at) * 1000
                    )

    def shutdown(self):
        """Executor 종료"""
        self._executor.shutdown(wait=False)

    def get_completed_count(self) -> int:
        """완료된 task 수"""
        return sum(1 for t in self._tasks.values() if t.status == "completed")

    def get_running_count(self) -> int:
        """실행 중인 task 수"""
        return sum(1 for t in self._tasks.values() if t.status == "running")


# ============================================================
# Singleton
# ============================================================

_background_manager: Optional[BackgroundManager] = None


def get_background_manager(max_workers: int = 3) -> BackgroundManager:
    """BackgroundManager 싱글톤 반환"""
    global _background_manager
    if _background_manager is None:
        _background_manager = BackgroundManager(max_workers=max_workers)
    return _background_manager
