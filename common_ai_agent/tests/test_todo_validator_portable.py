"""Todo templates hardcode `python3 ...` in validator/command strings, which
breaks on Windows (only `python`/`py` exist) and ignores the active venv.
The execution layer must rewrite the `python3` token to sys.executable so all
14 templates and every generated todo plan stay portable without data changes.
"""
from __future__ import annotations

import subprocess
import sys
from pathlib import Path

from lib.todo_tracker import TodoItem, TodoTracker


class _FakeResult:
    returncode = 0
    stdout = ""
    stderr = ""


def _capture_run(captured):
    def fake_run(cmd, *args, **kwargs):
        captured["cmd"] = cmd
        return _FakeResult()
    return fake_run


def test_run_validator_rewrites_python3_to_current_interpreter(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    item = TodoItem(content="x", active_form="x", validator='python3 workflow/foo/check.py ip --root .')
    assert item.run_validator() is None

    cmd = captured["cmd"]
    assert "python3 " not in cmd, f"python3 token must be rewritten, got: {cmd}"
    assert sys.executable in cmd.replace('"', ""), cmd


def test_run_validator_rewrites_every_python3_token(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    item = TodoItem(
        content="x",
        active_form="x",
        validator="python3 a.py && python3 b.py --flag",
    )
    item.run_validator()

    cmd = captured["cmd"]
    assert "python3" not in cmd, cmd
    assert cmd.replace('"', "").count(sys.executable) == 2, cmd


def test_run_validator_does_not_touch_similar_names(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    item = TodoItem(content="x", active_form="x", validator="python311 tool.py && echo python3x")
    item.run_validator()

    cmd = captured["cmd"]
    assert "python311 tool.py" in cmd, cmd
    assert "python3x" in cmd, cmd


def test_run_command_rewrites_python3(monkeypatch, tmp_path: Path):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    tracker = TodoTracker(persist_path=tmp_path / "todos.json")
    todo = TodoItem(content="x", active_form="x", command="python3 workflow/bar/run.py ip")
    ok, _tail, _lines = tracker._run_command(todo, tmp_path / "cmd.log")

    assert ok is True
    cmd = captured["cmd"]
    assert "python3 " not in cmd, cmd
    assert sys.executable in cmd.replace('"', ""), cmd
