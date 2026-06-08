"""Shared Plan Mode confirmation helpers."""

from __future__ import annotations


PLAN_CONFIRM_INPUTS = frozenset({
    "y",
    "yes",
    "confirm",
    "proceed",
    "진행",
    "확인",
    "ok",
    "네",
    "예",
    "ㅇㅇ",
    "yc",
})

PLAN_CONFIRM_EXECUTE_PROMPT = (
    "Confirmed. Execute all tasks in order. For EACH task follow this workflow:\n"
    "  1. todo_update(index=N, status='in_progress')\n"
    "  2. Do the work\n"
    "  3. todo_update(index=N, status='completed')\n"
    "  4. Verify the result\n"
    "  5. todo_update(index=N, status='approved', reason='what you verified')\n"
    "Start now: todo_update(index=1, status='in_progress')"
)


def is_plan_confirm_input(text: object) -> bool:
    return str(text or "").strip().lower() in PLAN_CONFIRM_INPUTS
