#!/usr/bin/env python3
"""cursor_todo.py — 외부 관리형 todo (current_todos.json) CLI.

stop-todo-loop hook이 읽는 **바로 그 파일**을 우리가 직접 제어한다.
이것이 "done"의 단일 기준 — Cursor 네이티브(내부 상태) todo가 아니라 이 파일.
hook은 별개 프로세스라 에이전트 메모리를 못 본다 → 파일이 유일한 진실원.

파일: $TODO_FILE 또는 <project>/current_todos.json (lib.todo_tracker 호환 스키마)
상태: pending / in_progress = 열림(open) | completed / cancelled = 닫힘(done)
      (DONE_STATUSES는 stop-todo-loop.py와 일치해야 한다)

Usage:
  python3 cursor_todo.py add   "<내용>" [--criteria C] [--priority high|medium|low]
  python3 cursor_todo.py start <ref>     # ref = 1-based 번호 또는 내용 부분문자열
  python3 cursor_todo.py done  <ref>
  python3 cursor_todo.py cancel <ref>
  python3 cursor_todo.py list            # 전체 상태
  python3 cursor_todo.py status          # open/total 요약 (hook과 동일 계산)
  python3 cursor_todo.py clear           # 전체 비움
"""

from __future__ import annotations

import argparse
import json
import os
import sys
import time
from pathlib import Path

DONE_STATUSES = {"completed", "approved", "cancelled", "skipped"}
OPEN_STATUSES = {"pending", "in_progress"}


def _project_root() -> Path:
    for var in ("CURSOR_PROJECT_DIR", "CLAUDE_PROJECT_DIR"):
        v = os.environ.get(var)
        if v:
            return Path(v)
    return Path.cwd()


def _todo_file() -> Path:
    override = os.environ.get("TODO_FILE")
    return Path(override) if override else _project_root() / "current_todos.json"


def _load(path: Path) -> dict:
    if not path.is_file():
        return {"todos": []}
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return {"todos": []}
    if not isinstance(data, dict) or not isinstance(data.get("todos"), list):
        return {"todos": []}
    return data


def _save(path: Path, data: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(data, ensure_ascii=False, indent=2), encoding="utf-8")


def _find(todos: list, ref: str) -> int:
    """ref = 1-based 번호 또는 content 부분문자열 → 인덱스(없으면 -1)."""
    if ref.isdigit():
        i = int(ref) - 1
        return i if 0 <= i < len(todos) else -1
    low = ref.lower()
    for i, t in enumerate(todos):
        if low in str(t.get("content", "")).lower():
            return i
    return -1


def _print_list(todos: list) -> None:
    if not todos:
        print("(todo 없음)")
        return
    icon = {"pending": "○", "in_progress": "▶", "completed": "✅",
            "cancelled": "✗", "approved": "✅", "skipped": "⊘"}
    for i, t in enumerate(todos, 1):
        s = str(t.get("status", "pending"))
        crit = str(t.get("criteria", "")).strip()
        line = f"  {i}. {icon.get(s, '?')} [{s}] {t.get('content', '')}"
        if crit:
            line += f"  (기준: {crit.splitlines()[0][:60]})"
        print(line)


def cmd_add(path: Path, content: str, criteria: str, priority: str) -> int:
    data = _load(path)
    data["todos"].append({
        "content": content,
        "activeForm": content,
        "status": "pending",
        "priority": priority,
        "criteria": criteria,
        "created_at": time.time(),
    })
    _save(path, data)
    print(f"[todo] added: {content}")
    return 0


def _set_status(path: Path, ref: str, status: str, *, single_active: bool = False) -> int:
    data = _load(path)
    todos = data["todos"]
    idx = _find(todos, ref)
    if idx < 0:
        print(f"[todo] FAIL: ref 못 찾음: {ref!r}")
        return 1
    if single_active:  # 한 번에 하나만 in_progress — 다른 진행중은 pending으로
        for t in todos:
            if t.get("status") == "in_progress":
                t["status"] = "pending"
    todos[idx]["status"] = status
    if status in DONE_STATUSES:
        todos[idx]["completed_at"] = time.time()
    _save(path, data)
    print(f"[todo] {status}: {todos[idx].get('content', '')}")
    return 0


def cmd_status(path: Path) -> int:
    todos = _load(path)["todos"]
    open_n = sum(1 for t in todos if str(t.get("status", "")).lower() not in DONE_STATUSES)
    print(f"[todo] open={open_n} total={len(todos)} ({path})")
    return 0


def cmd_clear(path: Path) -> int:
    _save(path, {"todos": []})
    print("[todo] cleared")
    return 0


def main(argv) -> int:
    ap = argparse.ArgumentParser(description=__doc__,
                                 formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    a = sub.add_parser("add"); a.add_argument("content")
    a.add_argument("--criteria", default=""); a.add_argument("--priority", default="medium")
    for name in ("start", "done", "cancel"):
        p = sub.add_parser(name); p.add_argument("ref")
    sub.add_parser("list"); sub.add_parser("status"); sub.add_parser("clear")
    args = ap.parse_args(argv)
    path = _todo_file()

    if args.cmd == "add":
        return cmd_add(path, args.content, args.criteria, args.priority)
    if args.cmd == "start":
        return _set_status(path, args.ref, "in_progress", single_active=True)
    if args.cmd == "done":
        return _set_status(path, args.ref, "completed")
    if args.cmd == "cancel":
        return _set_status(path, args.ref, "cancelled")
    if args.cmd == "list":
        _print_list(_load(path)["todos"]); return 0
    if args.cmd == "status":
        return cmd_status(path)
    if args.cmd == "clear":
        return cmd_clear(path)
    return 2


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
