"""
Todo Tracking System for Common AI Agent

명시적 tool 호출(todo_write, todo_update)로만 관리되는 task tracking 시스템.
파일 기반 persistence로 세션 간 상태 유지.
"""

import json
import time
from pathlib import Path
from typing import List, Dict, Optional
from dataclasses import dataclass, field

# Default persistence path
TODO_FILE = Path.home() / ".common_ai_agent" / "current_todos.json"

# Priority ordering
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}


def _fmt_elapsed(seconds: float) -> str:
    """Format elapsed seconds as human-readable string."""
    if seconds < 60:
        return f"{int(seconds)}s"
    elif seconds < 3600:
        m, s = divmod(int(seconds), 60)
        return f"{m}m{s:02d}s"
    else:
        h, rem = divmod(int(seconds), 3600)
        m = rem // 60
        return f"{h}h{m:02d}m"


@dataclass
class TodoItem:
    """
    개별 todo item

    Attributes:
        content: Todo 내용 (예: "Run tests")
        active_form: 진행 중일 때 표시할 내용 (예: "Running tests")
        status: 현재 상태 ("pending", "in_progress", "completed")
        priority: 우선순위 ("high", "medium", "low")
        created_at: 생성 시간 (timestamp)
        completed_at: 완료 시간 (timestamp, None if not completed)
        detail: 구체적 구현 내용/방법 (선택)
        criteria: 완료 판단 기준 체크리스트 (줄바꿈 구분, 선택)
        rejection_reason: 가장 최근 거절 이유 (step header에 표시)
    """
    content: str
    active_form: str
    status: str = "pending"       # "pending", "in_progress", "completed"
    priority: str = "medium"      # "high", "medium", "low"
    created_at: float = None
    completed_at: Optional[float] = None
    detail: str = ""
    criteria: str = ""
    rejection_reason: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.priority not in _PRIORITY_ORDER:
            self.priority = "medium"

    @property
    def elapsed(self) -> Optional[float]:
        """Elapsed seconds from creation to completion (or now if in_progress)."""
        if self.status == "completed" and self.completed_at:
            return self.completed_at - self.created_at
        if self.status == "in_progress":
            return time.time() - self.created_at
        return None


class TodoTracker:
    """
    ReAct 루프와 통합된 Todo tracking 시스템

    Features:
    - 여러 step의 진행 상황 추적
    - 한 번에 하나의 step만 in_progress
    - Priority-aware scheduling (high → medium → low)
    - Progress bar visualization
    - Completion timestamps & elapsed time
    - Stagnation detection with task-level detail
    """

    def __init__(self, persist_path: Optional[Path] = None):
        """Initialize todo tracker with optional file persistence"""
        self.todos: List[TodoItem] = []
        self.current_index: int = -1
        self.stagnation_count: int = 0
        self._last_completed_count: int = 0
        self._persist_path: Optional[Path] = persist_path or TODO_FILE

    def add_todos(self, todos: List[Dict]):
        """
        LLM이 생성한 todo list를 추가

        Args:
            todos: List of dicts with keys: content, status, activeForm, priority
                  Example: [
                      {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1", "priority": "high"},
                      {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"},
                  ]
        """
        self.todos = []
        for todo_dict in todos:
            self.todos.append(TodoItem(
                content=todo_dict.get("content", ""),
                active_form=todo_dict.get("activeForm", todo_dict.get("active_form", todo_dict.get("content", ""))),
                status=todo_dict.get("status", "pending"),
                priority=todo_dict.get("priority", "medium"),
                completed_at=todo_dict.get("completed_at"),
                detail=todo_dict.get("detail", ""),
                criteria=todo_dict.get("criteria", ""),
                rejection_reason=todo_dict.get("rejection_reason", ""),
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
        특정 todo를 in_progress로 변경.
        한 번에 하나의 todo만 in_progress 가능 — 이전 것은 pending으로 복귀.
        """
        if not (0 <= index < len(self.todos)):
            return

        for todo in self.todos:
            if todo.status == "in_progress":
                todo.status = "pending"

        self.todos[index].status = "in_progress"
        self.current_index = index
        self._save()

    def mark_completed(self, index: int):
        """특정 todo를 completed로 변경하고 완료 시간 기록."""
        if not (0 <= index < len(self.todos)):
            return

        self.todos[index].status = "completed"
        self.todos[index].completed_at = time.time()
        self.todos[index].rejection_reason = ""
        self._save()

    def auto_advance(self):
        """현재 todo 완료 후 자동으로 다음 pending todo로 이동 (priority 반영)."""
        if self.current_index >= 0 and self.current_index < len(self.todos):
            self.mark_completed(self.current_index)

        next_idx = self._get_next_pending()
        if next_idx is not None:
            self.mark_in_progress(next_idx)
            return

        self.current_index = -1

    def _get_next_pending(self) -> Optional[int]:
        """
        다음 pending todo 인덱스 반환.
        Priority 순서: high → medium → low.
        같은 priority 내에서는 원래 순서(index 오름차순) 유지.
        """
        candidates = [
            (i, todo) for i, todo in enumerate(self.todos)
            if todo.status == "pending"
        ]
        if not candidates:
            return None

        # Sort by priority first, then by original index
        candidates.sort(key=lambda x: (_PRIORITY_ORDER.get(x[1].priority, 1), x[0]))
        return candidates[0][0]

    def format_progress(self) -> str:
        """
        Progress를 시각화된 문자열로 포맷.

        Format:
            === TODO PROGRESS ===
            ✅ 1. Completed task                (12s)
            ▶️ 2. [HIGH] Current task...        (5s elapsed)
            ⏸️ 3. Next task
            ⏸️ 4. [LOW] Low priority task

            [████████░░░░░░░░░░░░] 40%  (2/5 done)
        """
        if not self.todos:
            return ""

        lines = ["=== TODO PROGRESS ==="]

        for i, todo in enumerate(self.todos):
            icon = {
                "pending":     "⏸️",
                "in_progress": "▶️",
                "completed":   "✅"
            }.get(todo.status, "❓")

            # Priority badge (only for non-medium)
            priority_badge = ""
            if todo.priority == "high":
                priority_badge = "[HIGH] "
            elif todo.priority == "low":
                priority_badge = "[LOW] "

            # Text
            text = todo.active_form if todo.status == "in_progress" else todo.content

            # Elapsed / completion time
            time_str = ""
            if todo.status == "completed" and todo.elapsed is not None:
                time_str = f"  ({_fmt_elapsed(todo.elapsed)})"
            elif todo.status == "in_progress" and todo.elapsed is not None:
                time_str = f"  ({_fmt_elapsed(todo.elapsed)} elapsed)"

            lines.append(f"{icon} {i+1}. {priority_badge}{text}{time_str}")

        # Progress bar
        completed_count = sum(1 for t in self.todos if t.status == "completed")
        total = len(self.todos)
        ratio = completed_count / total if total > 0 else 0
        bar_len = 20
        filled = int(bar_len * ratio)
        bar = "█" * filled + "░" * (bar_len - filled)
        pct = int(ratio * 100)
        lines.append(f"\n[{bar}] {pct}%  ({completed_count}/{total} done)")

        return "\n".join(lines)

    def get_current_todo(self) -> Optional[TodoItem]:
        """현재 in_progress인 todo 반환."""
        if self.current_index >= 0 and self.current_index < len(self.todos):
            return self.todos[self.current_index]
        return None

    def is_all_completed(self) -> bool:
        """모든 todo가 완료되었는지 확인."""
        return bool(self.todos) and all(t.status == "completed" for t in self.todos)

    def get_completion_ratio(self) -> float:
        """완료 비율 계산 (0.0 ~ 1.0)."""
        if not self.todos:
            return 1.0
        completed = sum(1 for t in self.todos if t.status == "completed")
        return completed / len(self.todos)

    def get_continuation_prompt(self) -> Optional[str]:
        """미완료 todo가 있으면 continuation 리마인더 프롬프트 반환."""
        if not self.todos or self.is_all_completed():
            return None

        current = self.get_current_todo()
        completed_count = sum(1 for t in self.todos if t.status == "completed")
        remaining = len(self.todos) - completed_count

        # Brief reminder only — full progress shown on todo_update/todo_write
        lines = [
            f"[Todo Reminder] {completed_count}/{len(self.todos)} completed, {remaining} remaining.",
        ]

        if current:
            lines.append(f"Current task: {current.content}")
            lines.append("Continue working on this task.")
        else:
            next_idx = self._get_next_pending()
            if next_idx is not None:
                todo = self.todos[next_idx]
                lines.append(f"Next task: {todo.content}")
                lines.append("Start working on this task.")

        return "\n".join(lines)

    def get_minimal_context(self, step_idx: int) -> str:
        """특정 step 실행에 필요한 최소 context 반환."""
        if not self.todos or step_idx >= len(self.todos):
            return ""

        lines = []

        completed_steps = [
            f"  {i+1}. {t.content} [DONE]"
            for i, t in enumerate(self.todos[:step_idx])
            if t.status == "completed"
        ]
        if completed_steps:
            lines.append("Completed steps:")
            lines.extend(completed_steps)

        current = self.todos[step_idx]
        lines.append(f"\nCurrent step ({step_idx + 1}/{len(self.todos)}):")
        lines.append(f"  {current.content}")

        remaining = [
            f"  {i+1}. {t.content}"
            for i, t in enumerate(self.todos[step_idx + 1:], start=step_idx + 1)
            if t.status == "pending"
        ]
        if remaining:
            lines.append(f"\nRemaining ({len(remaining)} steps):")
            lines.extend(remaining[:3])
            if len(remaining) > 3:
                lines.append(f"  ... and {len(remaining) - 3} more")

        return "\n".join(lines)

    def to_dict(self) -> Dict:
        """직렬화 (저장용)."""
        return {
            "todos": [
                {
                    "content": t.content,
                    "activeForm": t.active_form,
                    "status": t.status,
                    "priority": t.priority,
                    "created_at": t.created_at,
                    "completed_at": t.completed_at,
                    "detail": t.detail,
                    "criteria": t.criteria,
                    "rejection_reason": t.rejection_reason,
                }
                for t in self.todos
            ],
            "current_index": self.current_index
        }

    @classmethod
    def from_dict(cls, data: Dict, persist_path: Optional[Path] = None) -> 'TodoTracker':
        """역직렬화 (로드용)."""
        tracker = cls(persist_path=persist_path)
        if "todos" in data:
            tracker.add_todos(data["todos"])
        tracker.current_index = data.get("current_index", -1)
        tracker.stagnation_count = data.get("stagnation_count", 0)
        tracker._last_completed_count = data.get("_last_completed_count", 0)
        return tracker

    def _save(self):
        """파일에 현재 상태 저장."""
        if not self._persist_path:
            return
        try:
            self._persist_path.parent.mkdir(parents=True, exist_ok=True)
            data = self.to_dict()
            data["stagnation_count"] = self.stagnation_count
            data["_last_completed_count"] = self._last_completed_count
            self._persist_path.write_text(json.dumps(data, ensure_ascii=False, indent=2))
        except Exception:
            pass

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
        """Todo 초기화 + 파일 삭제."""
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
            self.stagnation_count = 0
            self._last_completed_count = completed
        else:
            self.stagnation_count += 1

        self._save()

        if self.stagnation_count >= max_stagnation:
            current = self.get_current_todo()
            if current:
                elapsed_str = f" ({_fmt_elapsed(current.elapsed)} elapsed)" if current.elapsed else ""
                # Warn about stuck task but don't give up — return True signals caller
            return True
        return False

    def get_stagnation_hint(self) -> str:
        """현재 막힌 task에 대한 힌트 메시지 반환."""
        current = self.get_current_todo()
        if not current:
            return "[Stagnation] No active task. Use todo_write to set tasks."

        elapsed_str = f" ({_fmt_elapsed(current.elapsed)} elapsed)" if current.elapsed else ""
        priority_str = f" [{current.priority.upper()}]" if current.priority != "medium" else ""
        completed = sum(1 for t in self.todos if t.status == "completed")

        return (
            f"[Stagnation x{self.stagnation_count}] Stuck on task {self.current_index + 1}/{len(self.todos)}"
            f"{priority_str}: \"{current.content}\"{elapsed_str}\n"
            f"Progress: {completed}/{len(self.todos)} completed. "
            f"Try a different approach or use todo_update to mark it completed if done."
        )


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
    """
    import re

    todos = []

    # Pattern 1: TodoWrite: 형식
    if "TodoWrite:" in text or "Todo:" in text:
        match = re.search(r'(TodoWrite|Todo):\s*\n((?:[-*]\s*\[.\]\s*.+\n?)+)', text, re.IGNORECASE)
        if match:
            todo_text = match.group(2)
            for line in todo_text.split('\n'):
                line = line.strip()
                if not line:
                    continue

                item_match = re.match(r'[-*]\s*\[(.)\]\s*(.+)', line)
                if item_match:
                    status_char = item_match.group(1).strip().lower()
                    content = item_match.group(2).strip()

                    status = "completed" if status_char in ['x', 'v', '✓'] else "pending"
                    active_form = _generate_active_form(content)

                    todos.append({
                        "content": content,
                        "status": status,
                        "activeForm": active_form
                    })

    # Pattern 2: Numbered list (1. 2. 3.)
    if not todos:
        matches = re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)
        if len(matches) >= 3:
            task_matches = [
                m.strip() for m in matches
                if len(m.strip()) <= 80
                and not re.match(r'^(The |I |We |This |According |Let me )', m.strip(), re.IGNORECASE)
                and not re.match(r'^\*\*', m.strip())
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
    """Content에서 active_form 생성 (e.g. "Run tests" → "Running tests")."""
    content_lower = content.lower()

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
        "verify": "Verifying",
        "check": "Checking",
        "update": "Updating",
        "refactor": "Refactoring",
        "add": "Adding",
        "remove": "Removing",
        "integrate": "Integrating",
    }

    for verb, verb_ing in verb_map.items():
        if content_lower.startswith(verb):
            return verb_ing + content[len(verb):]

    return f"Executing: {content}"
