"""
Todo Tracking System for Common AI Agent

명시적 tool 호출(todo_write, todo_update)로만 관리되는 task tracking 시스템.
파일 기반 persistence로 세션 간 상태 유지.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional, Set
from dataclasses import dataclass, field
from datetime import datetime

# Default persistence path
TODO_FILE = Path.home() / ".common_ai_agent" / "current_todos.json"


@dataclass
class TodoItem:
    """
    개별 todo item

    Attributes:
        content: Todo 내용 (예: "Run tests")
        active_form: 진행 중일 때 표시할 내용 (예: "Running tests")
        status: 현재 상태 ("pending", "in_progress", "completed")
        created_at: 생성 시간 (timestamp)
        priority: 우선순위 ("low", "medium", "high", "critical")
        tags: 태그 목록 (예: ["bugfix", "urgent"])
        estimate: 예상 소요 시간 (분 단위)
        due_date: 마감일시 (timestamp)
        prereqs: 선행 작업 인덱스 목록 (이 작업 전에 완료되어야 하는 todo들의 인덱스)
        started_at: 작업 시작 시간 (timestamp)
        completed_at: 작업 완료 시간 (timestamp)
        total_time_spent: 총 소요 시간 (초 단위)
    """
    content: str
    active_form: str
    status: str = "pending"  # "pending", "in_progress", "completed"
    created_at: float = None
    priority: str = "medium"  # "low", "medium", "high", "critical"
    tags: List[str] = field(default_factory=list)
    estimate: Optional[int] = None  # estimated time in minutes
    due_date: Optional[float] = None  # due date timestamp
    prereqs: Set[int] = field(default_factory=set)  # indices of prerequisite todos
    started_at: Optional[float] = None  # when work started
    completed_at: Optional[float] = None  # when work completed
    total_time_spent: float = 0.0  # total time spent in seconds

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()


class TodoTracker:
    """
    ReAct 루프와 통합된 Todo tracking 시스템

    Claude Code의 TodoWrite 동작을 모방합니다:
    - 여러 step의 진행 상황 추적
    - 한 번에 하나의 step만 in_progress
    - Auto-advance: 현재 step 완료 시 자동으로 다음 step 진행
    - Progress visualization (✅ ▶️ ⏸️)

    Example:
        tracker = TodoTracker()
        tracker.add_todos([
            {"content": "Explore code", "status": "pending", "activeForm": "Exploring code"},
            {"content": "Write tests", "status": "pending", "activeForm": "Writing tests"}
        ])
        tracker.mark_in_progress(0)  # Start first todo
        print(tracker.format_progress())  # Show progress
        tracker.mark_completed(0)  # Complete first
        tracker.auto_advance()  # Move to next
    """

    def __init__(self, persist_path: Optional[Path] = None):
        """Initialize todo tracker with optional file persistence"""
        self.todos: List[TodoItem] = []
        self.current_index: int = -1  # Index of current in_progress todo
        self.stagnation_count: int = 0  # Consecutive continuation attempts without progress
        self._last_completed_count: int = 0
        self._persist_path: Optional[Path] = persist_path or TODO_FILE
        # Undo/Redo stacks
        self._undo_stack: List[Dict] = []  # Stack of past states
        self._redo_stack: List[Dict] = []  # Stack of undone states
        self._undo_limit: int = 50  # Max undo states to keep

    def add_todos(self, todos: List[Dict]):
        """
        LLM이 생성한 todo list를 추가

        Args:
            todos: List of dicts with keys: content, status, activeForm, priority, tags, estimate, due_date, prereqs
                  Example: [
                      {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1",
                       "priority": "high", "tags": ["urgent"], "estimate": 30},
                      {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2",
                       "prereqs": [0]}  # Depends on Step 1
                  ]
        """
        self._save_state()  # Save state before modification
        self.todos = []
        for todo_dict in todos:
            self.todos.append(TodoItem(
                content=todo_dict.get("content", ""),
                active_form=todo_dict.get("activeForm", todo_dict.get("content", "")),
                status=todo_dict.get("status", "pending"),
                priority=todo_dict.get("priority", "medium"),
                tags=todo_dict.get("tags", []),
                estimate=todo_dict.get("estimate"),
                due_date=todo_dict.get("due_date"),
                prereqs=set(todo_dict.get("prereqs", [])),
                started_at=todo_dict.get("started_at"),
                completed_at=todo_dict.get("completed_at"),
                total_time_spent=todo_dict.get("total_time_spent", 0.0)
            ))

        # Find current in_progress item
        self.current_index = -1
        for i, todo in enumerate(self.todos):
            if todo.status == "in_progress":
                self.current_index = i
                break

        self.stagnation_count = 0
        self._last_completed_count = 0
        self._save()

    def mark_in_progress(self, index: int):
        """
        특정 todo를 in_progress로 변경

        중요: 한 번에 하나의 todo만 in_progress 가능
        이전 in_progress는 자동으로 pending으로 변경

        Args:
            index: Todo index (0-based)
        """
        if not (0 <= index < len(self.todos)):
            return

        self._save_state()  # Save state before modification

        # Clear previous in_progress (한 번에 하나만)
        for todo in self.todos:
            if todo.status == "in_progress":
                todo.status = "pending"
                # Note: Don't reset time tracking for paused tasks

        # Set new in_progress
        self.todos[index].status = "in_progress"
        if self.todos[index].started_at is None:
            self.todos[index].started_at = time.time()
        self.current_index = index
        self._save()

    def mark_completed(self, index: int):
        """
        특정 todo를 completed로 변경

        Args:
            index: Todo index (0-based)
        """
        if not (0 <= index < len(self.todos)):
            return

        self._save_state()  # Save state before modification

        # Track time spent
        todo = self.todos[index]
        todo.status = "completed"
        todo.completed_at = time.time()
        if todo.started_at is not None:
            time_spent = todo.completed_at - todo.started_at
            todo.total_time_spent += time_spent
        self._save()

    def auto_advance(self):
        """
        현재 todo 완료 후 자동으로 다음 pending todo로 이동

        동작:
        1. 현재 in_progress todo를 completed로 변경
        2. 다음 pending todo를 찾아 in_progress로 변경 (의존성 확인)
        """
        # Complete current
        if self.current_index >= 0 and self.current_index < len(self.todos):
            self.mark_completed(self.current_index)

        # Find next available (respects dependencies)
        next_idx = self.get_next_available()
        if next_idx is not None:
            self.mark_in_progress(next_idx)
            return

        # No more available todos
        self.current_index = -1

    def format_progress(self) -> str:
        """
        Progress를 시각화된 문자열로 포맷

        Format:
            === TODO PROGRESS ===
            ✅ 1. Completed task
            ▶️ 2. Current task in progress...
            ⏸️ 3. Pending task
            Progress: 1/3

        Returns:
            Formatted progress string
        """
        if not self.todos:
            return ""

        lines = ["=== TODO PROGRESS ==="]

        for i, todo in enumerate(self.todos):
            # Icon based on status
            icon = {
                "pending": "⏸️",
                "in_progress": "▶️",
                "completed": "✅"
            }.get(todo.status, "❓")

            # Text: active_form for in_progress, content otherwise
            if todo.status == "in_progress":
                text = todo.active_form
            else:
                text = todo.content

            lines.append(f"{icon} {i+1}. {text}")

        # Progress summary
        completed_count = sum(1 for t in self.todos if t.status == "completed")
        lines.append(f"\nProgress: {completed_count}/{len(self.todos)}")

        return "\n".join(lines)

    def get_current_todo(self) -> Optional[TodoItem]:
        """
        현재 in_progress인 todo 반환

        Returns:
            TodoItem or None
        """
        if self.current_index >= 0 and self.current_index < len(self.todos):
            return self.todos[self.current_index]
        return None

    def is_all_completed(self) -> bool:
        """
        모든 todo가 완료되었는지 확인

        Returns:
            True if all todos are completed
        """
        return all(todo.status == "completed" for todo in self.todos)

    def get_completion_ratio(self) -> float:
        """
        완료 비율 계산 (0.0 ~ 1.0)

        Returns:
            Completion ratio
        """
        if not self.todos:
            return 1.0

        completed = sum(1 for t in self.todos if t.status == "completed")
        return completed / len(self.todos)

    # ==================== Dependency Management ====================

    def are_prereqs_met(self, index: int) -> bool:
        """
        Check if all prerequisites for a todo are completed.

        Args:
            index: Todo index (0-based)

        Returns:
            True if all prerequisites are completed or if no prerequisites
        """
        if not (0 <= index < len(self.todos)):
            return False

        prereqs = self.todos[index].prereqs
        if not prereqs:
            return True

        # Check if all prerequisite todos are completed
        for prereq_idx in prereqs:
            if prereq_idx >= len(self.todos):
                continue  # Invalid prereq, skip
            if self.todos[prereq_idx].status != "completed":
                return False

        return True

    def get_blocked_by(self, index: int) -> List[int]:
        """
        Get list of prerequisite indices that are blocking this todo.

        Args:
            index: Todo index (0-based)

        Returns:
            List of indices of incomplete prerequisites
        """
        if not (0 <= index < len(self.todos)):
            return []

        blocked = []
        prereqs = self.todos[index].prereqs

        for prereq_idx in prereqs:
            if prereq_idx >= len(self.todos):
                continue
            if self.todos[prereq_idx].status != "completed":
                blocked.append(prereq_idx)

        return blocked

    def get_next_available(self) -> Optional[int]:
        """
        Get the next pending todo whose prerequisites are met.

        Returns:
            Index of next available todo, or None if none available
        """
        for i, todo in enumerate(self.todos):
            if todo.status == "pending" and self.are_prereqs_met(i):
                return i
        return None

    def get_continuation_prompt(self) -> Optional[str]:
        """
        미완료 todo가 있으면 continuation 리마인더 프롬프트 반환.

        Returns:
            리마인더 문자열 또는 None (모두 완료 시)
        """
        if not self.todos or self.is_all_completed():
            return None

        current = self.get_current_todo()
        completed_count = sum(1 for t in self.todos if t.status == "completed")
        remaining = len(self.todos) - completed_count

        lines = [
            f"[Todo Reminder] {completed_count}/{len(self.todos)} completed, {remaining} remaining.",
            self.format_progress(),
        ]

        if current:
            lines.append(f"\nCurrent task: {current.content}")
            lines.append("Continue working on this task.")
        else:
            # No current in_progress, find next pending
            for i, todo in enumerate(self.todos):
                if todo.status == "pending":
                    lines.append(f"\nNext task: {todo.content}")
                    lines.append("Start working on this task.")
                    break

        return "\n".join(lines)

    def get_minimal_context(self, step_idx: int) -> str:
        """
        특정 step 실행에 필요한 최소 context 반환.

        이전 step의 결과와 현재 step의 내용만 포함.

        Args:
            step_idx: Step index (0-based)

        Returns:
            최소 context 문자열
        """
        if not self.todos or step_idx >= len(self.todos):
            return ""

        lines = []

        # Previous completed steps (brief summary)
        completed_steps = [
            f"  {i+1}. {t.content} [DONE]"
            for i, t in enumerate(self.todos[:step_idx])
            if t.status == "completed"
        ]
        if completed_steps:
            lines.append("Completed steps:")
            lines.extend(completed_steps)

        # Current step
        current = self.todos[step_idx]
        lines.append(f"\nCurrent step ({step_idx + 1}/{len(self.todos)}):")
        lines.append(f"  {current.content}")

        # Remaining steps (brief)
        remaining = [
            f"  {i+1}. {t.content}"
            for i, t in enumerate(self.todos[step_idx + 1:], start=step_idx + 1)
            if t.status == "pending"
        ]
        if remaining:
            lines.append(f"\nRemaining ({len(remaining)} steps):")
            lines.extend(remaining[:3])  # Show max 3
            if len(remaining) > 3:
                lines.append(f"  ... and {len(remaining) - 3} more")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """
        직렬화 (저장용)

        Returns:
            Dict representation
        """
        return {
            "todos": [
                {
                    "content": t.content,
                    "activeForm": t.active_form,
                    "status": t.status,
                    "created_at": t.created_at,
                    "priority": t.priority,
                    "tags": t.tags,
                    "estimate": t.estimate,
                    "due_date": t.due_date,
                    "prereqs": list(t.prereqs),
                    "started_at": t.started_at,
                    "completed_at": t.completed_at,
                    "total_time_spent": t.total_time_spent
                }
                for t in self.todos
            ],
            "current_index": self.current_index
        }

    @classmethod
    def from_dict(cls, data: Dict, persist_path: Optional[Path] = None) -> 'TodoTracker':
        """역직렬화 (로드용)"""
        tracker = cls(persist_path=persist_path)
        if "todos" in data:
            tracker.add_todos(data["todos"])
        tracker.current_index = data.get("current_index", -1)
        tracker.stagnation_count = data.get("stagnation_count", 0)
        tracker._last_completed_count = data.get("_last_completed_count", 0)
        return tracker

    def _save(self):
        """파일에 현재 상태 저장"""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = self.to_dict()
            data["stagnation_count"] = self.stagnation_count
            data["_last_completed_count"] = self._last_completed_count
            self._persist_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            pass  # Persistence is best-effort

    @classmethod
    def load(cls, persist_path: Optional[Path] = None) -> 'TodoTracker':
        """파일에서 로드. 없으면 빈 tracker 반환."""
        path = persist_path or TODO_FILE
        if path.exists():
            try:
                data = json.loads(path.read_text())
                return cls.from_dict(data, persist_path=path)
            except Exception:
                pass
        return cls(persist_path=path)

    def clear(self):
        """Todo 초기화 + 파일 삭제"""
        self.todos = []
        self.current_index = -1
        self.stagnation_count = 0
        self._last_completed_count = 0
        if self._persist_path and self._persist_path.exists():
            self._persist_path.unlink()

    def check_stagnation(self, max_stagnation: int = 3) -> bool:
        """
        Continuation 주입 전 stagnation 체크.

        Returns:
            True = 포기해야 함 (stagnation 초과)
            False = 계속 진행 가능
        """
        completed = sum(1 for t in self.todos if t.status == "completed")
        if completed > self._last_completed_count:
            # 진전 있음 → 리셋
            self.stagnation_count = 0
            self._last_completed_count = completed
        else:
            # 진전 없음
            self.stagnation_count += 1

        self._save()
        return self.stagnation_count >= max_stagnation

    # ==================== Undo/Redo Stack ====================

    def _save_state(self):
        """Save current state to undo stack before making changes."""
        # Capture current state
        state = {
            "todos": [t.__dict__.copy() for t in self.todos],
            "current_index": self.current_index,
            "stagnation_count": self.stagnation_count,
            "_last_completed_count": self._last_completed_count
        }
        
        # Add to undo stack
        self._undo_stack.append(state)
        
        # Limit stack size
        if len(self._undo_stack) > self._undo_limit:
            self._undo_stack.pop(0)
        
        # Clear redo stack on new action
        self._redo_stack.clear()

    def _restore_state(self, state: Dict):
        """Restore tracker state from saved state dict."""
        self.todos = [
            TodoItem(**t) for t in state["todos"]
        ]
        self.current_index = state["current_index"]
        self.stagnation_count = state["stagnation_count"]
        self._last_completed_count = state["_last_completed_count"]
        self._save()

    def undo(self) -> bool:
        """
        Undo the last state change.

        Returns:
            True if undo was successful, False if nothing to undo
        """
        if not self._undo_stack:
            return False
        
        # Save current state to redo stack
        current_state = {
            "todos": [t.__dict__.copy() for t in self.todos],
            "current_index": self.current_index,
            "stagnation_count": self.stagnation_count,
            "_last_completed_count": self._last_completed_count
        }
        self._redo_stack.append(current_state)
        
        # Pop and restore previous state
        previous_state = self._undo_stack.pop()
        self._restore_state(previous_state)
        return True

    def redo(self) -> bool:
        """
        Redo the last undone action.

        Returns:
            True if redo was successful, False if nothing to redo
        """
        if not self._redo_stack:
            return False
        
        # Save current state to undo stack
        current_state = {
            "todos": [t.__dict__.copy() for t in self.todos],
            "current_index": self.current_index,
            "stagnation_count": self.stagnation_count,
            "_last_completed_count": self._last_completed_count
        }
        self._undo_stack.append(current_state)
        
        # Pop and restore next state
        next_state = self._redo_stack.pop()
        self._restore_state(next_state)
        return True

    def can_undo(self) -> bool:
        """Check if undo is available."""
        return len(self._undo_stack) > 0

    def can_redo(self) -> bool:
        """Check if redo is available."""
        return len(self._redo_stack) > 0

    def clear_undo_history(self):
        """Clear undo/redo stacks."""
        self._undo_stack.clear()
        self._redo_stack.clear()

    # ==================== Time Logging ====================

    def get_time_spent(self, index: int) -> float:
        """
        Get time spent on a todo (in seconds).

        For completed todos, returns total_time_spent.
        For in-progress todos, returns elapsed time so far.
        For pending todos, returns total_time_spent (for resuming).

        Args:
            index: Todo index (0-based)

        Returns:
            Time spent in seconds
        """
        if not (0 <= index < len(self.todos)):
            return 0.0

        todo = self.todos[index]
        
        if todo.status == "completed":
            return todo.total_time_spent
        elif todo.status == "in_progress" and todo.started_at is not None:
            return time.time() - todo.started_at + todo.total_time_spent
        else:
            return todo.total_time_spent

    def get_total_time_spent(self) -> float:
        """
        Get total time spent across all todos (in seconds).

        Returns:
            Total time in seconds
        """
        total = 0.0
        for i, todo in enumerate(self.todos):
            total += self.get_time_spent(i)
        return total

    def format_time(self, seconds: float) -> str:
        """
        Format seconds into human-readable string.

        Args:
            seconds: Time in seconds

        Returns:
            Formatted time string (e.g., "2h 30m", "45s")
        """
        if seconds < 60:
            return f"{int(seconds)}s"
        elif seconds < 3600:
            minutes = int(seconds / 60)
            return f"{minutes}m"
        else:
            hours = int(seconds / 3600)
            minutes = int((seconds % 3600) / 60)
            if minutes > 0:
                return f"{hours}h {minutes}m"
            return f"{hours}h"

    # ==================== Report Generators ====================

    def generate_summary_report(self) -> str:
        """
        Generate a comprehensive summary report of todos.

        Returns:
            Formatted summary report string
        """
        if not self.todos:
            return "No todos to report."

        lines = ["=" * 60]
        lines.append("TODO SUMMARY REPORT")
        lines.append("=" * 60)
        lines.append("")

        # Basic stats
        completed = sum(1 for t in self.todos if t.status == "completed")
        in_progress = sum(1 for t in self.todos if t.status == "in_progress")
        pending = sum(1 for t in self.todos if t.status == "pending")

        lines.append(f"Total Todos: {len(self.todos)}")
        lines.append(f"Completed: {completed} ({self.get_completion_ratio()*100:.1f}%)")
        lines.append(f"In Progress: {in_progress}")
        lines.append(f"Pending: {pending}")
        lines.append("")

        # Time stats
        total_time = self.get_total_time_spent()
        lines.append(f"Total Time Spent: {self.format_time(total_time)}")
        if completed > 0:
            avg_time = total_time / completed
            lines.append(f"Avg Time per Completed: {self.format_time(avg_time)}")
        lines.append("")

        # Priority breakdown
        priority_counts = {"critical": 0, "high": 0, "medium": 0, "low": 0}
        for todo in self.todos:
            priority_counts[todo.priority] += 1
        lines.append("Priority Distribution:")
        for prio, count in sorted(priority_counts.items(), key=lambda x: x[0]):
            if count > 0:
                lines.append(f"  {prio.capitalize()}: {count}")
        lines.append("")

        # Pending with blockers
        blocked = []
        for i, todo in enumerate(self.todos):
            if todo.status == "pending" and not self.are_prereqs_met(i):
                blockers = self.get_blocked_by(i)
                blocked.append((i, blockers))

        if blocked:
            lines.append("Blocked Todos (prerequisites not met):")
            for idx, blockers in blocked:
                blocker_names = [self.todos[b].content for b in blockers]
                lines.append(f"  {idx+1}. {self.todos[idx].content}")
                lines.append(f"     Waiting for: {', '.join(blocker_names)}")
            lines.append("")

        # Overdue
        now = time.time()
        overdue = []
        for i, todo in enumerate(self.todos):
            if todo.due_date and todo.status != "completed" and todo.due_date < now:
                overdue.append((i, todo.due_date))

        if overdue:
            lines.append("Overdue Todos:")
            for idx, due in overdue:
                lines.append(f"  {idx+1}. {self.todos[idx].content}")
                lines.append(f"     Due: {datetime.fromtimestamp(due).strftime('%Y-%m-%d %H:%M')}")
            lines.append("")

        lines.append("=" * 60)
        return "\n".join(lines)

    def generate_priority_report(self) -> str:
        """
        Generate report sorted by priority.

        Returns:
            Priority-sorted report string
        """
        priority_order = {"critical": 0, "high": 1, "medium": 2, "low": 3}
        sorted_todos = sorted(
            [(i, t) for i, t in enumerate(self.todos)],
            key=lambda x: (priority_order.get(x[1].priority, 99), x[0])
        )

        lines = ["PRIORITY REPORT"]
        lines.append("=" * 40)
        lines.append("")

        current_prio = None
        for idx, todo in sorted_todos:
            if todo.priority != current_prio:
                current_prio = todo.priority
                lines.append(f"[{current_prio.upper()}]")
            lines.append(f"  {idx+1}. {todo.content} [{todo.status}]")
            if todo.estimate:
                lines.append(f"     Est: {todo.estimate}m")

        return "\n".join(lines)

    def generate_time_report(self) -> str:
        """
        Generate time tracking report.

        Returns:
            Time-focused report string
        """
        lines = ["TIME TRACKING REPORT"]
        lines.append("=" * 40)
        lines.append("")

        for i, todo in enumerate(self.todos):
            time_spent = self.get_time_spent(i)
            status_icon = {"completed": "✅", "in_progress": "▶️", "pending": "⏸️"}.get(todo.status, "❓")
            lines.append(f"{status_icon} {i+1}. {todo.content}")
            lines.append(f"   Time: {self.format_time(time_spent)}")

            if todo.estimate:
                est_sec = todo.estimate * 60
                if todo.status == "completed":
                    over_under = time_spent - est_sec
                    if over_under > 0:
                        lines.append(f"   Est: {todo.estimate}m (over by {self.format_time(over_under)})")
                    else:
                        lines.append(f"   Est: {todo.estimate}m (under by {self.format_time(abs(over_under))})")
                else:
                    lines.append(f"   Est: {todo.estimate}m")

            lines.append("")

        total = self.get_total_time_spent()
        lines.append(f"Total: {self.format_time(total)}")
        return "\n".join(lines)

    def generate_tag_report(self, tags: Optional[List[str]] = None) -> str:
        """
        Generate report filtered by tags.

        Args:
            tags: Optional list of tags to filter by. If None, shows all tags.

        Returns:
            Tag-filtered report string
        """
        lines = ["TAG REPORT"]
        lines.append("=" * 40)
        lines.append("")

        # Collect all tags
        all_tags = set()
        for todo in self.todos:
            all_tags.update(todo.tags)

        if tags:
            # Filter by specified tags
            target_tags = set(tags)
            matching = [(i, t) for i, t in enumerate(self.todos) if target_tags.intersection(set(t.tags))]
        else:
            # Show tag distribution
            lines.append("Tag Distribution:")
            tag_counts = {}
            for todo in self.todos:
                for tag in todo.tags:
                    tag_counts[tag] = tag_counts.get(tag, 0) + 1
            for tag, count in sorted(tag_counts.items()):
                lines.append(f"  {tag}: {count}")
            lines.append("")
            matching = [(i, t) for i, t in enumerate(self.todos) if t.tags]

        for idx, todo in matching:
            status_icon = {"completed": "✅", "in_progress": "▶️", "pending": "⏸️"}.get(todo.status, "❓")
            lines.append(f"{status_icon} {idx+1}. {todo.content}")
            lines.append(f"   Tags: {', '.join(todo.tags) if todo.tags else 'none'}")
            lines.append("")

        return "\n".join(lines)

    def generate_dependency_graph(self) -> str:
        """
        Generate text-based dependency graph visualization.

        Returns:
            ASCII graph string showing dependencies
        """
        if not self.todos:
            return "No todos to display."

        lines = ["DEPENDENCY GRAPH"]
        lines.append("=" * 40)
        lines.append("")

        for i, todo in enumerate(self.todos):
            status_icon = {"completed": "✅", "in_progress": "▶️", "pending": "⏸️"}.get(todo.status, "❓")
            line = f"{status_icon} [{i+1}] {todo.content}"

            if todo.prereqs:
                prereq_nums = [str(p+1) for p in todo.prereqs]
                line += f" <- depends on [{', '.join(prereq_nums)}]"

            lines.append(line)

        return "\n".join(lines)

    def export_to_markdown(self) -> str:
        """
        Export todos to markdown format.

        Returns:
            Markdown-formatted string
        """
        lines = ["# Todo List"]
        lines.append("")
        lines.append(f"**Progress:** {sum(1 for t in self.todos if t.status == 'completed')}/{len(self.todos)} completed")
        lines.append("")

        for i, todo in enumerate(self.todos):
            status_char = "x" if todo.status == "completed" else " "
            lines.append(f"- [{status_char}] {todo.content}")

            if todo.tags:
                lines.append(f"  Tags: {', '.join(todo.tags)}")
            if todo.estimate:
                lines.append(f"  Est: {todo.estimate}m")
            if todo.priority != "medium":
                lines.append(f"  Priority: {todo.priority}")

            time_spent = self.get_time_spent(i)
            if time_spent > 0:
                lines.append(f"  Time: {self.format_time(time_spent)}")

            lines.append("")

        return "\n".join(lines)


# ============================================================
# Utility Functions
# ============================================================

def parse_todo_write_from_text(text: str) -> Optional[List[Dict]]:
    """
    LLM 응답에서 TodoWrite 파싱

    지원 형식:
    1. Explicit TodoWrite:
       TodoWrite:
       - [ ] Step 1
       - [ ] Step 2

    2. Implicit todo list:
       Todo:
       1. Step 1
       2. Step 2

    Args:
        text: LLM response text

    Returns:
        List of todo dicts or None if no todos found
    """
    import re

    todos = []

    # Pattern 1: TodoWrite: 형식
    if "TodoWrite:" in text or "Todo:" in text:
        # Extract todo section
        match = re.search(r'(TodoWrite|Todo):\s*\n((?:[-*]\s*\[.\]\s*.+\n?)+)', text, re.IGNORECASE)
        if match:
            todo_text = match.group(2)
            # Parse each line: - [ ] content
            for line in todo_text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                # Match: - [ ] content or - [x] content
                item_match = re.match(r'[-*]\s*\[(.)\]\s*(.+)', line)
                if item_match:
                    status_char = item_match.group(1).strip().lower()
                    content = item_match.group(2).strip()

                    # Determine status
                    if status_char in ['x', 'v', '✓']:
                        status = "completed"
                    else:
                        status = "pending"

                    # Generate active_form (content + "ing" 형태)
                    active_form = _generate_active_form(content)

                    todos.append({
                        "content": content,
                        "status": status,
                        "activeForm": active_form
                    })

    # Pattern 2: Numbered list (1. 2. 3.)
    if not todos:
        content_text = text
        # Also skip lines that look like analysis, not tasks
        # (e.g., "1. message_classifier.py - ..." or "1. Use background_task...")
        matches = re.findall(r'^\s*\d+\.\s*(.+)$', content_text, re.MULTILINE)
        if len(matches) >= 3:  # At least 3 items
            # Heuristic: real todos are short action items, not descriptions
            # Filter out lines that are too long (>80 chars) or look like analysis
            task_matches = [
                m.strip() for m in matches
                if len(m.strip()) <= 80
                and not re.match(r'^(The |I |We |This |According |Let me )', m.strip(), re.IGNORECASE)
                and not re.match(r'^\*\*', m.strip())  # Skip markdown bold items
            ]
            if len(task_matches) >= 3:
                for content in task_matches:
                    active_form = _generate_active_form(content)
                    todos.append({
                        "content": content,
                        "status": "pending",
                        "activeForm": active_form
                    })

    return todos if todos else None


def _generate_active_form(content: str) -> str:
    """
    Content에서 active_form 생성

    Example:
        "Run tests" → "Running tests"
        "Build project" → "Building project"
        "Fix bug" → "Fixing bug"

    Args:
        content: Todo content

    Returns:
        Active form string
    """
    # Simple heuristic: Add -ing or "Executing: " prefix
    content_lower = content.lower()

    # Common verbs that change to -ing
    verb_map = {
        "run": "Running",
        "build": "Building",
        "test": "Testing",
        "fix": "Fixing",
        "implement": "Implementing",
        "create": "Creating",
        "write": "Writing",
        "read": "Reading",
        "analyze": "Analyzing",
        "explore": "Exploring",
        "design": "Designing",
        "compile": "Compiling",
        "debug": "Debugging",
    }

    # Find verb at start (case-insensitive)
    for verb, verb_ing in verb_map.items():
        if content_lower.startswith(verb):
            # Replace first occurrence, preserving case of rest
            return verb_ing + content[len(verb):]

    # Default: prefix with "Executing: "
    return f"Executing: {content}"
