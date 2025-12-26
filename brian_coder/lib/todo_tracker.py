"""
Todo Tracking System for Brian Coder

Claude Code 스타일의 TodoWrite 기능 구현.
복잡한 다단계 작업의 진행 상황을 실시간으로 추적하고 표시합니다.
"""

import time
from typing import List, Dict, Optional
from dataclasses import dataclass


@dataclass
class TodoItem:
    """
    개별 todo item

    Attributes:
        content: Todo 내용 (예: "Run tests")
        active_form: 진행 중일 때 표시할 내용 (예: "Running tests")
        status: 현재 상태 ("pending", "in_progress", "completed")
        created_at: 생성 시간 (timestamp)
    """
    content: str
    active_form: str
    status: str = "pending"  # "pending", "in_progress", "completed"
    created_at: float = None

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

    def __init__(self):
        """Initialize empty todo tracker"""
        self.todos: List[TodoItem] = []
        self.current_index: int = -1  # Index of current in_progress todo

    def add_todos(self, todos: List[Dict]):
        """
        LLM이 생성한 todo list를 추가

        Args:
            todos: List of dicts with keys: content, status, activeForm
                  Example: [
                      {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1"},
                      {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"}
                  ]
        """
        self.todos = []
        for todo_dict in todos:
            self.todos.append(TodoItem(
                content=todo_dict.get("content", ""),
                active_form=todo_dict.get("activeForm", todo_dict.get("content", "")),
                status=todo_dict.get("status", "pending")
            ))

        # Find current in_progress item
        self.current_index = -1
        for i, todo in enumerate(self.todos):
            if todo.status == "in_progress":
                self.current_index = i
                break

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

        # Clear previous in_progress (한 번에 하나만)
        for todo in self.todos:
            if todo.status == "in_progress":
                todo.status = "pending"

        # Set new in_progress
        self.todos[index].status = "in_progress"
        self.current_index = index

    def mark_completed(self, index: int):
        """
        특정 todo를 completed로 변경

        Args:
            index: Todo index (0-based)
        """
        if not (0 <= index < len(self.todos)):
            return

        self.todos[index].status = "completed"

    def auto_advance(self):
        """
        현재 todo 완료 후 자동으로 다음 pending todo로 이동

        동작:
        1. 현재 in_progress todo를 completed로 변경
        2. 다음 pending todo를 찾아 in_progress로 변경
        """
        # Complete current
        if self.current_index >= 0 and self.current_index < len(self.todos):
            self.mark_completed(self.current_index)

        # Find next pending
        for i, todo in enumerate(self.todos):
            if todo.status == "pending":
                self.mark_in_progress(i)
                return

        # No more pending todos
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
                    "created_at": t.created_at
                }
                for t in self.todos
            ],
            "current_index": self.current_index
        }

    @classmethod
    def from_dict(cls, data: Dict) -> 'TodoTracker':
        """
        역직렬화 (로드용)

        Args:
            data: Dict from to_dict()

        Returns:
            TodoTracker instance
        """
        tracker = cls()
        if "todos" in data:
            tracker.add_todos(data["todos"])
        tracker.current_index = data.get("current_index", -1)
        return tracker


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
        matches = re.findall(r'^\s*\d+\.\s*(.+)$', text, re.MULTILINE)
        if len(matches) >= 3:  # At least 3 items (more substantial tasks)
            for content in matches:
                content = content.strip()
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
