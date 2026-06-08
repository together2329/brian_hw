import re

from lib.display import format_tool_brief


ANSI_RE = re.compile(r"\x1b\[[0-9;]*m")


def _plain(text: str) -> str:
    return ANSI_RE.sub("", text)


def test_blocked_todo_update_is_not_rendered_as_rejected():
    observation = (
        "Completion blocked: Task 1 cannot be marked completed because no tools were called since starting this task.\n"
        "Produce a deliverable first."
    )

    rendered = _plain(
        format_tool_brief(
            "todo_update",
            'index=1, status="completed"',
            observation,
        )
    )

    normalized = " ".join(rendered.split())
    assert "update blocked" in rendered
    assert "[BLOCKED] update blocked" in rendered
    assert "[ERROR] update blocked" not in rendered
    assert "[X] rejected" not in rendered
    assert "no tools were called" in normalized


def test_actual_todo_rejection_is_still_rendered_as_rejected():
    observation = "❌ Task 1 rejected. [missing tests]"

    rendered = _plain(
        format_tool_brief(
            "todo_update",
            'index=1, status="rejected"',
            observation,
        )
    )

    assert "[X] rejected" in rendered or "rejected" in rendered
    assert "missing tests" in rendered
