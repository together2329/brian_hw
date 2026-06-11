#!/usr/bin/env python3
"""Stop hook: remind the agent to report in ROCEV shape when evidence todos remain."""

import json
import os
import sys
from pathlib import Path


DONE = {"completed", "approved", "cancelled", "skipped"}


def project_root() -> Path:
    for key in ("CURSOR_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(key)
        if value:
            return Path(value)
    return Path.cwd()


def todo_file() -> Path:
    override = os.environ.get("TODO_FILE")
    if override:
        return Path(override)
    return project_root() / "current_todos.json"


def open_evidence_todos(path: Path) -> list[dict]:
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except Exception:
        return []

    todos = data.get("todos") or []
    result = []
    for todo in todos:
        if not isinstance(todo, dict):
            continue
        status = str(todo.get("status", "")).lower()
        if status in DONE:
            continue
        text = " ".join(
            str(todo.get(key, ""))
            for key in ("content", "criteria", "detail", "approval_policy")
        ).lower()
        if "evidence" in text or "validation" in text or "rocev" in text:
            result.append(todo)
    return result


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if payload.get("status", "completed") != "completed":
        print("{}")
        return

    remaining = open_evidence_todos(todo_file())
    if not remaining:
        print("{}")
        return

    lines = []
    for todo in remaining[:3]:
        lines.append(f"- {todo.get('content', '(no content)')}")

    message = (
        "ROCEV reminder: evidence/validation todo가 남아 있습니다.\n"
        + "\n".join(lines)
        + "\n완료 전 Requirement, Obligation, Contract, Evidence, Validation 형태로 닫아주세요."
    )
    print(json.dumps({"followup_message": message}, ensure_ascii=False))


if __name__ == "__main__":
    main()

