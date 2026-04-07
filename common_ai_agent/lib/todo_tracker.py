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
try:
    import config
    TODO_FILE = Path(config.TODO_FILE)
except (ImportError, AttributeError):
    TODO_FILE = Path.home() / ".common_ai_agent" / "current_todos.json"

# Import Color for display
try:
    from lib.display import Color
except ImportError:
    class Color:
        CYAN = ""
        YELLOW = ""
        RED = ""
        BOLD = ""
        DIM = ""
        STRIKETHROUGH = ""
        RESET = ""
        @staticmethod
        def success(s): return s
        @staticmethod
        def warning(s): return s

# Priority ordering
_PRIORITY_ORDER = {"high": 0, "medium": 1, "low": 2}

# Status aliases for normalizing common alternative values
STATUS_ALIASES = {
    "todo": "pending",
    "open": "pending",
    "not_started": "pending",
    "new": "pending",
    "done": "completed",
    "finish": "completed",
    "finished": "completed",
    "complete": "completed",
    "wip": "in_progress",
    "in-progress": "in_progress",
    "active": "in_progress",
    "started": "in_progress",
    "reviewed": "approved",
    "accepted": "approved",
    "verified": "approved",
    "passed": "approved",
    "failed": "rejected",
    "blocked": "rejected",
}


def _load_todo_rule() -> str:
    """
    Load todo rules from project rules/ folder only.
    Reads all *.md files sorted alphabetically.
    """
    import os
    rules_dir = Path(os.getcwd()) / "rules"
    parts = []
    if rules_dir.is_dir():
        for f in sorted(rules_dir.glob("*.md")):
            content = f.read_text(encoding="utf-8").strip()
            if content:
                parts.append(f"## [{f.stem}]\n{content}")
    return "\n\n".join(parts)


def _load_upd_rule() -> str:
    """
    Load .UPD_RULE.md (project-level execution rules).
    Checked in: cwd, cwd/.., global ~/.common_ai_agent/
    """
    import os
    candidates = [
        Path(os.getcwd()) / ".UPD_RULE.md",
        Path(os.getcwd()).parent / ".UPD_RULE.md",
        Path.home() / ".common_ai_agent" / ".UPD_RULE.md",
    ]
    for p in candidates:
        if p.exists():
            try:
                return p.read_text(encoding="utf-8").strip()
            except Exception:
                pass
    return ""


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
        status: 현재 상태 ("pending", "in_progress", "completed", "reviewed")
        priority: 우선순위 ("high", "medium", "low")
        created_at: 생성 시간 (timestamp)
        completed_at: 완료 시간 (timestamp, None if not completed)
        detail: 구체적 구현 내용/방법 (선택)
        criteria: 완료 판단 기준 체크리스트 (줄바꿈 구분, 선택)
        rejection_reason: 가장 최근 거절 이유 (step header에 표시)
    """
    content: str
    active_form: str
    status: str = "pending"       # "pending", "in_progress", "completed", "approved", "rejected"
    priority: str = "medium"      # "high", "medium", "low"
    created_at: float = None
    completed_at: Optional[float] = None
    detail: str = ""
    criteria: str = ""
    rejection_reason: str = ""
    approved_reason: str = ""

    def __post_init__(self):
        if self.created_at is None:
            self.created_at = time.time()
        if self.priority not in _PRIORITY_ORDER:
            self.priority = "medium"

    @property
    def elapsed(self) -> Optional[float]:
        """Elapsed seconds from creation to completion (or now if in_progress)."""
        if self.status in ("completed", "approved") and self.completed_at:
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
    
    Convention: External tool interactions (todo_update, todo_add) use 1-based indexing
    to match the user display, then convert to 0-based for internal List access.
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
                approved_reason=todo_dict.get("approved_reason", ""),
            ))

        # Find current in_progress item
        self.current_index = -1
        for i, todo in enumerate(self.todos):
            if todo.status == "in_progress":
                self.current_index = i
                break

        self.stagnation_count = 0
        self._last_completed_count = 0
        self.save()

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
        self.save()

    def mark_completed(self, index: int):
        """특정 todo를 completed로 변경하고 완료 시간 기록."""
        if not (0 <= index < len(self.todos)):
            return

        self.todos[index].status = "completed"
        self.todos[index].completed_at = time.time()
        self.todos[index].rejection_reason = ""
        # Keep current_index pointing at this task so review prompt targets it
        self.current_index = index
        self.save()

    def mark_approved(self, index: int):
        """특정 todo를 approved로 변경 (완전 완료).
        LLM이 명시적으로 다음 task를 in_progress로 전환해야 함 — 자동 전환 없음.
        """
        if not (0 <= index < len(self.todos)):
            return

        self.todos[index].status = "approved"
        self.todos[index].rejection_reason = ""
        if self.current_index == index:
            # Point current_index at next actionable task, but do NOT
            # auto-call mark_in_progress — the tool return value already
            # instructs the LLM to call todo_update(status='in_progress').
            next_idx = self._get_next_pending()
            self.current_index = next_idx if next_idx is not None else -1
        # completed_at shouldn't change
        self.save()

    def mark_rejected(self, index: int, reason: str):
        """특정 todo를 rejected로 변경 (재작업 필요)."""
        if not (0 <= index < len(self.todos)):
            return

        self.todos[index].status = "rejected"
        self.todos[index].rejection_reason = reason
        # Set it as the current active task so it must be worked on
        self.current_index = index
        self.save()

    def unprocess_rejected(self):
        """'rejected' 상태인 모든 todo를 'pending'으로 되돌림."""
        modified = False
        first_rejected = None
        for i, todo in enumerate(self.todos):
            if todo.status == "rejected":
                todo.status = "pending"
                todo.rejection_reason = ""
                modified = True
                if first_rejected is None:
                    first_rejected = i
        
        if modified:
            if first_rejected is not None:
                self.current_index = first_rejected
            self.save()
            return True
        return False

    def auto_advance(self):
        """현재 todo를 completed로 표시 — 다음 task 전환은 review 후 LLM이 명시적으로 수행."""
        if self.current_index >= 0 and self.current_index < len(self.todos):
            self.mark_completed(self.current_index)
        # Do NOT auto-call mark_in_progress — state machine requires
        # completed → approved before next task can become in_progress.

    def _get_next_pending(self) -> Optional[int]:
        """
        다음 actionable todo 인덱스 반환.
        우선순위: rejected > completed (review needed) > pending.
        같은 priority 내에서는 원래 순서(index 오름차순) 유지.
        """
        # Status priority: rejected=0 (must fix first), completed=1 (review needed), pending=2
        # completed IS included — it still needs explicit approve/reject from LLM.
        STATUS_ORDER = {"rejected": 0, "completed": 1, "pending": 2}
        candidates = [
            (i, todo) for i, todo in enumerate(self.todos)
            if todo.status in ("pending", "rejected", "completed")
        ]
        if not candidates:
            return None

        # Sort by status priority first, then task priority, then original index
        candidates.sort(key=lambda x: (
            STATUS_ORDER.get(x[1].status, 9),
            _PRIORITY_ORDER.get(x[1].priority, 1),
            x[0]
        ))
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

        from lib.display import get_terminal_width
        term_width = get_terminal_width()
        # Adjusted max length based on terminal width (with some padding for icons/timing)
        max_text_len = max(40, term_width - 35)

        _BAR_BG = Color.DIM + "░" + Color.RESET
        _BAR_FG = Color.success("█")

        lines = ["", f"  {Color.BOLD}{Color.CYAN}── PLAN & PROGRESS ──{Color.RESET}"]

        for i, todo in enumerate(self.todos):
            # Icon and explicit status label [Approved], [In Progress], etc.
            status_info = {
                "pending":     (f"{Color.dim('⏸')} ", "[Pending]"),
                "in_progress": (f"{Color.warning('▶')} ", "[In Progress]"),
                "completed":   (f"{Color.warning('👀')} ", "[Completed]"),
                "approved":    (f"{Color.success('✅')} ", f"{Color.success('[Approved]')}"),
                "rejected":    (f"{Color.error('❌')} ", f"{Color.error('[Rejected]')} ")
            }.get(todo.status, ("❓ ", "[?] "))
            
            icon, label = status_info

            # Priority badge
            priority_badge = ""
            if todo.priority == "high":
                priority_badge = f"{Color.RED}[HIGH]{Color.RESET} "
            elif todo.priority == "low":
                priority_badge = f"{Color.dim('[LOW]')} "

            # Text with status-based coloring
            content_style = Color.RESET
            if todo.status == "approved":
                content_style = getattr(Color, "DIM", "") + getattr(Color, "STRIKETHROUGH", "")
            elif todo.status == "completed":
                content_style = Color.RESET
            elif todo.status == "in_progress":
                content_style = Color.BOLD + Color.YELLOW
            elif todo.status == "rejected":
                content_style = Color.BOLD + Color.RED

            text = todo.active_form if todo.status in ("in_progress", "rejected") else todo.content
            
            # Elapsed / completion time
            time_str = ""
            if todo.status in ("completed", "approved") and todo.elapsed is not None:
                secs = abs(todo.elapsed)
                time_str = f" {Color.dim(f'({_fmt_elapsed(secs)})')}{Color.RESET}"
            elif todo.status in ("in_progress", "rejected") and todo.elapsed is not None:
                secs = abs(todo.elapsed)
                time_str = f" {Color.dim(f'({_fmt_elapsed(secs)} elapsed)')}{Color.RESET}"

            lines.append(f"  {icon}{Color.CYAN}{i+1}.{Color.RESET} {label} {priority_badge}{content_style}{text}{Color.RESET}{time_str}")
            
            # Show detail if available
            if todo.detail and todo.status != 'completed':
                prefix = "   " if todo.status == "in_progress" else "   "
                lines.append(f"{prefix}{Color.DIM}└ 📝 {todo.detail}{Color.RESET}")
                
            # Show rejection reason if available
            if todo.rejection_reason and todo.status in ('rejected', 'in_progress', 'pending'):
                lines.append(f"     {Color.error('⚠ REJECTED:')} {Color.RED}{todo.rejection_reason}{Color.RESET}")

            # Show approved reason if available
            if todo.approved_reason and todo.status == 'approved':
                lines.append(f"     {Color.success('✔ APPROVED:')} {Color.DIM}{todo.approved_reason}{Color.RESET}")
                
            # Show criteria if available
            if todo.criteria and todo.status != 'completed':
                for c in todo.criteria.splitlines():
                    if c.strip():
                        lines.append(f"     {Color.DIM}• {c.strip()}{Color.RESET}")

        lines.append("")

        return "\n".join(lines)

    def format_simple(self) -> str:
        """Simple list view — content + criteria. Used by /todo (no -v)."""
        if not self.todos:
            return ""
        icons = {
            "pending":     Color.dim("⏸"),
            "in_progress": Color.warning("▶"),
            "completed":   Color.warning("👀"),
            "approved":    Color.success("✅"),
            "rejected":    Color.error("❌"),
        }
        lines = ["", f"  {Color.BOLD}{Color.CYAN}── TODO ──{Color.RESET}"]
        for i, todo in enumerate(self.todos):
            icon = icons.get(todo.status, "?")
            lines.append(f"  {icon} {Color.CYAN}{i+1}.{Color.RESET} {todo.content}")
            if todo.criteria:
                for c in todo.criteria.splitlines():
                    if c.strip():
                        lines.append(f"       {Color.DIM}• {c.strip()}{Color.RESET}")
                lines.append("")
        lines.append("")
        return "\n".join(lines)

    def print_debug_status(self):
        """[Debug] Print current todo list status to terminal."""
        if not self.todos:
            # print(Color.DIM + "  [Todo] No tasks." + Color.RESET)
            return

        print(f"\n  {Color.BOLD}{Color.CYAN}--- TODO STATUS ---{Color.RESET}")
        for i, t in enumerate(self.todos):
            # Status icon & label
            status_info = {
                "pending": ("⚪ ", "[Pending]"),
                "in_progress": ("🔵 ", "[In Progress]"),
                "completed": ("🟡 ", "[Completed]"),
                "approved": (Color.success("✅ "), Color.success("[Approved]")),
                "rejected": (Color.error("❌ "), Color.error("[Rejected]"))
            }.get(t.status, ("❓ ", "[?]"))
            
            icon, label = status_info
            
            # Text style
            style = Color.RESET
            if t.status == "approved": style = Color.success("") # Green
            if t.status == "in_progress": style = Color.BOLD + Color.YELLOW
            if t.status == "rejected": style = Color.BOLD + Color.RED
            if t.status == "pending": style = Color.DIM
            
            print(f"  {icon}{i+1}. {label} {style}{t.content}{Color.RESET}")
        print(f"  {Color.BOLD}{Color.CYAN}-------------------{Color.RESET}\n")

    def get_current_todo(self) -> Optional[TodoItem]:
        """현재 in_progress인 todo 반환."""
        if self.current_index >= 0 and self.current_index < len(self.todos):
            return self.todos[self.current_index]
        return None

    def is_all_completed(self) -> bool:
        """모든 todo가 approved(완전히 완료)되었는지 확인."""
        return bool(self.todos) and all(t.status == "approved" for t in self.todos)

    def is_all_processed(self) -> bool:
        """모든 todo가 처리(approved 또는 rejected)되었는지 확인."""
        return bool(self.todos) and all(t.status in ("approved", "rejected") for t in self.todos)

    def get_progress_pct(self) -> float:
        """완료 비율 계산 (0.0 ~ 1.0)."""
        if not self.todos:
            return 1.0
        completed = sum(1 for t in self.todos if t.status == "approved")
        return completed / len(self.todos)

    def get_completion_ratio(self) -> float:
        return self.get_progress_pct()

    def _auto_recover_current_index(self) -> bool:
        """
        current_index가 -1이거나 invalid할 때 자동 복구.
        rejected > completed > pending 순으로 첫 번째 actionable task를 current로 설정.
        Returns True if recovered.
        """
        if self.current_index >= 0 and self.current_index < len(self.todos):
            status = self.todos[self.current_index].status
            if status in ("in_progress", "rejected", "completed", "pending"):
                return False  # already valid

        # Find first actionable task
        next_idx = self._get_next_pending()
        if next_idx is not None:
            self.current_index = next_idx
            return True
        return False

    def get_continuation_prompt(self) -> Optional[str]:
        """미완료 todo가 있으면 1-line 리마인더 반환. .TODO_RULE.md가 있으면 태스크 시작 시 주입."""
        if not self.todos or self.is_all_completed():
            return None

        # Auto-recover if current_index is broken (-1 or pointing at approved task)
        self._auto_recover_current_index()

        current = self.get_current_todo()
        total = len(self.todos)

        if current:
            idx = self.current_index + 1
            if current.status == "rejected":
                prompt = (
                    f"[Task {idx}/{total} REJECTED] {current.rejection_reason}\n"
                    f"Fix the issue, then call: todo_update(index={idx}, status='in_progress')"
                )
            elif current.status == "completed":
                # Inject review reminder — LLM must explicitly approve or reject
                prompt = (
                    f"[Task {idx}/{total} REVIEW REQUIRED] \"{current.content}\"\n"
                    f"You marked this task completed. Now perform a CRITICAL review before approving.\n"
                    f"→ Pass → todo_update(index={idx}, status='approved', reason='<concrete evidence>')\n"
                    f"→ Issue → todo_update(index={idx}, status='rejected', reason='<exact problem>')"
                )
            else:
                in_prog = current.status == "in_progress"
                first_action = (
                    f"⚠️ MANDATORY: When task is done, you MUST call todo_update(index={idx}, status='completed') as your FIRST Action — before writing any file or starting the next task."
                    if in_prog else
                    f"⚠️ MANDATORY: Start by calling todo_update(index={idx}, status='in_progress'), then do the work, then call todo_update(index={idx}, status='completed')."
                )
                prompt = (
                    f"[Task {idx}/{total}] {current.content}\n"
                    f"{first_action}"
                )
            # Append TODO_RULE if present
            rule = _load_todo_rule()
            if rule:
                prompt += f"\n\n=== TODO RULES ===\n{rule}"
            # Append UPD_RULE (project execution rules) — periodic re-injection
            try:
                import config as _cfg
                _periodic = getattr(_cfg, "UPD_RULE_PERIODIC_INJECT", True)
            except Exception:
                _periodic = True
            if _periodic:
                upd_rule = _load_upd_rule()
                if upd_rule:
                    prompt += f"\n\n=== PROJECT RULES (reminder) ===\n{upd_rule}"
            return prompt

        # No current task set — check for unreviewed completed tasks
        unreviewed = [(i, t) for i, t in enumerate(self.todos) if t.status == "completed"]
        if unreviewed:
            i, t = unreviewed[0]
            idx = i + 1
            prompt = (
                f"[Task {idx}/{total} REVIEW REQUIRED] \"{t.content}\"\n"
                f"→ Pass → todo_update(index={idx}, status='approved', reason='<concrete evidence>')\n"
                f"→ Issue → todo_update(index={idx}, status='rejected', reason='<exact problem>')"
            )
            rule = _load_todo_rule()
            if rule:
                prompt += f"\n\n=== TODO RULES ===\n{rule}"
            return prompt

        return None

    def get_minimal_context(self, step_idx: int) -> str:
        """특정 step 실행에 필요한 최소 context 반환."""
        if not self.todos or step_idx >= len(self.todos):
            return ""

        lines = []

        completed_steps = [
            f"  {i+1}. {t.content} [DONE]"
            for i, t in enumerate(self.todos[:step_idx])
            if t.status in ("completed", "approved")
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
                    "approved_reason": t.approved_reason,
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

    def save(self):
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

    def check_stagnation(self, max_stagnation: int = 50) -> bool:
        """
        Continuation 주입 전 stagnation 체크.

        Returns:
            True = 포기해야 함 (stagnation 초과)
            False = 계속 진행 가능
        """
        completed = sum(1 for t in self.todos if t.status in ("completed", "approved", "rejected"))
        if completed > self._last_completed_count:
            self.stagnation_count = 0
            self._last_completed_count = completed
        else:
            self.stagnation_count += 1

        self.save()

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
