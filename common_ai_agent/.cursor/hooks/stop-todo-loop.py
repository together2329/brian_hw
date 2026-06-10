#!/usr/bin/env python3
"""Cursor `stop` hook — todo-list 기반 작업 루프.

Claude Code의 "todo가 남아 있으면 멈추지 않는다" 규율을 Cursor로 이식한다.

계약 (Cursor hooks 스펙):
  stdin  : {"status": "completed"|"aborted"|"error", "loop_count": int, ...}
  stdout : {"followup_message": "..."}  → 자동 재투입 (hooks.json loop_limit 가 상한)
           {}                            → 정상 종료 허용

동작:
  - status != "completed" 이면 개입하지 않는다 (사용자 중단/에러에 루프 금지)
  - TODO_FILE (기본 <project>/current_todos.json, lib/todo_tracker.TodoTracker 스키마)
    에서 open todo (status ∉ DONE_STATUSES) 를 센다
  - open 이 남아 있으면 다음 todo 의 content/criteria 를 담아 followup_message 발행
  - 파일이 없거나 깨졌으면 {} (fail-open: 루프보다 종료가 안전)

검증: tests/test_cursor_pack.py (stdin/stdout 계약을 subprocess 로 테스트)
"""

import json
import os
import sys
from pathlib import Path

DONE_STATUSES = {"completed", "approved", "cancelled", "skipped"}
MAX_LISTED = 3


def _project_root() -> Path:
    for var in ("CURSOR_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        value = os.environ.get(var)
        if value:
            return Path(value)
    return Path.cwd()


def _todo_file() -> Path:
    override = os.environ.get("TODO_FILE")
    if override:
        return Path(override)
    return _project_root() / "current_todos.json"


def _open_todos(path: Path):
    try:
        data = json.loads(path.read_text(encoding="utf-8", errors="replace"))
    except (OSError, json.JSONDecodeError):
        return []
    todos = data.get("todos") or []
    return [t for t in todos
            if isinstance(t, dict)
            and str(t.get("status", "")).lower() not in DONE_STATUSES]


def main() -> None:
    try:
        payload = json.load(sys.stdin)
    except Exception:
        payload = {}

    if payload.get("status", "completed") != "completed":
        print("{}")
        return

    path = _todo_file()
    if not path.is_file():
        print("{}")
        return

    remaining = _open_todos(path)
    if not remaining:
        print("{}")
        return

    lines = []
    for t in remaining[:MAX_LISTED]:
        item = f"- [{t.get('status', 'pending')}] {t.get('content', '(no content)')}"
        criteria = str(t.get("criteria", "")).strip()
        if criteria:
            item += f" (완료 기준: {criteria.splitlines()[0][:80]})"
        lines.append(item)
    more = len(remaining) - MAX_LISTED
    if more > 0:
        lines.append(f"- … 외 {more}개")

    message = (
        f"Todo loop: open todo {len(remaining)}개가 남아 있습니다. 멈추지 말고 계속하세요.\n"
        + "\n".join(lines)
        + "\n규율: 한 번에 하나만 in_progress, 완료 주장 전에 validator/테스트의 신선한 증거 제시"
        + " (rule 80-todo-evidence). 전부 닫히면 루프가 자동 종료됩니다."
    )
    print(json.dumps({"followup_message": message}, ensure_ascii=False))


if __name__ == "__main__":
    main()
