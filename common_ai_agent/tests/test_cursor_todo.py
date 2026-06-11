"""cursor_todo CLI 검증 + stop-todo-loop hook과의 통합.

핵심: 우리가 cursor_todo.py로 쓴 파일을 hook이 그대로 읽어 done 판정한다.
(외부 관리형 todo = current_todos.json 단일 진실원)
evidence for: OBL_CURSOR_TODO_EXTERNAL_FILE
"""

from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path

REPO = Path(__file__).resolve().parent.parent
TODO_CLI = REPO / "scripts" / "cursor_todo.py"
HOOK = REPO / ".cursor" / "hooks" / "stop-todo-loop.py"

_spec = importlib.util.spec_from_file_location("cursor_todo", TODO_CLI)
ct = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(ct)


def _run(args, todo_file):
    return ct.main([*args]) if False else _subrun(args, todo_file)


def _subrun(args, todo_file):
    proc = subprocess.run(
        [sys.executable, str(TODO_CLI), *args],
        capture_output=True, text=True, timeout=15,
        env={"PATH": "/usr/bin:/bin", "TODO_FILE": str(todo_file)})
    return proc


def _todos(todo_file):
    return json.loads(Path(todo_file).read_text(encoding="utf-8"))["todos"]


def test_add_start_done_roundtrip(tmp_path):
    tf = tmp_path / "current_todos.json"
    assert _subrun(["add", "RTL 컴파일", "--criteria", "lint PASS"], tf).returncode == 0
    assert _subrun(["add", "sim 실행"], tf).returncode == 0
    todos = _todos(tf)
    assert [t["content"] for t in todos] == ["RTL 컴파일", "sim 실행"]
    assert all(t["status"] == "pending" for t in todos)
    assert todos[0]["criteria"] == "lint PASS"

    _subrun(["start", "RTL"], tf)           # 부분문자열 매칭
    assert _todos(tf)[0]["status"] == "in_progress"
    _subrun(["done", "1"], tf)              # 1-based 번호
    t = _todos(tf)
    assert t[0]["status"] == "completed" and "completed_at" in t[0]


def test_single_active_demotes_others(tmp_path):
    tf = tmp_path / "current_todos.json"
    _subrun(["add", "a"], tf); _subrun(["add", "b"], tf)
    _subrun(["start", "1"], tf)
    _subrun(["start", "2"], tf)             # 두번째 시작 → 첫번째는 pending으로 강등
    s = {t["content"]: t["status"] for t in _todos(tf)}
    assert s == {"a": "pending", "b": "in_progress"}


def test_status_and_cancel(tmp_path):
    tf = tmp_path / "current_todos.json"
    _subrun(["add", "x"], tf); _subrun(["add", "y"], tf)
    out = _subrun(["status"], tf).stdout
    assert "open=2 total=2" in out
    _subrun(["cancel", "x"], tf)            # cancel = 닫힘
    assert "open=1 total=2" in _subrun(["status"], tf).stdout


def test_bad_ref_fails(tmp_path):
    tf = tmp_path / "current_todos.json"
    _subrun(["add", "only"], tf)
    assert _subrun(["done", "ghost"], tf).returncode == 1
    assert _subrun(["done", "99"], tf).returncode == 1


def test_hook_reads_what_cli_writes(tmp_path):
    """통합: cursor_todo가 쓴 파일을 stop-todo-loop hook이 그대로 읽는다."""
    tf = tmp_path / "current_todos.json"
    _subrun(["add", "남은 일", "--criteria", "게이트 PASS"], tf)
    _subrun(["add", "끝낼 일"], tf)
    _subrun(["done", "끝낼 일"], tf)
    # hook 호출 (open 1개 남음 → followup 발행해야 함)
    hook = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"status": "completed"}),
        capture_output=True, text=True, timeout=15,
        env={"PATH": "/usr/bin:/bin", "TODO_FILE": str(tf)})
    out = json.loads(hook.stdout)
    assert "남은 일" in out.get("followup_message", "")
    assert "끝낼 일" not in out["followup_message"]
    # 마지막 todo까지 done → hook 침묵
    _subrun(["done", "남은 일"], tf)
    hook2 = subprocess.run(
        [sys.executable, str(HOOK)], input=json.dumps({"status": "completed"}),
        capture_output=True, text=True, timeout=15,
        env={"PATH": "/usr/bin:/bin", "TODO_FILE": str(tf)})
    assert json.loads(hook2.stdout) == {}


def test_done_statuses_match_hook():
    """cursor_todo와 hook의 DONE_STATUSES가 일치 (드리프트 방지)."""
    hook_src = HOOK.read_text(encoding="utf-8")
    assert 'DONE_STATUSES = {"completed", "approved", "cancelled", "skipped"}' in hook_src
    assert ct.DONE_STATUSES == {"completed", "approved", "cancelled", "skipped"}
