"""Todo templates hardcode `python3 ...` in validator/command strings, which
breaks on Windows (only `python`/`py` exist) and ignores the active venv.
The execution layer must rewrite the `python3` token to sys.executable so all
14 templates and every generated todo plan stay portable without data changes.
"""
from __future__ import annotations

import shlex
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
        captured["shell"] = kwargs.get("shell", False)
        return _FakeResult()
    return fake_run


def test_run_validator_rewrites_python3_to_current_interpreter(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    item = TodoItem(content="x", active_form="x", validator='python3 workflow/foo/check.py ip --root .')
    assert item.run_validator() is None

    q = shlex.quote(sys.executable)
    assert captured["cmd"] == f"{q} workflow/foo/check.py ip --root ."


def test_run_validator_rewrites_every_python3_token(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))

    item = TodoItem(
        content="x",
        active_form="x",
        validator="python3 a.py && python3 b.py --flag",
    )
    item.run_validator()

    q = shlex.quote(sys.executable)
    assert captured["cmd"] == f"{q} a.py && {q} b.py --flag"


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
    q = shlex.quote(sys.executable)
    assert captured["cmd"] == f"{q} workflow/bar/run.py ip"


# ---------------------------------------------------------------------------
# Windows: shell=True means cmd.exe, which cannot run the POSIX syntax
# (`test -f ... || (...)`, `$VAR`) that todo templates use. With git-bash
# installed, validators/commands must be routed through `bash -c` instead.
# ---------------------------------------------------------------------------

_GIT_BASH = r"C:\Program Files\Git\bin\bash.exe"


def _fake_windows(monkeypatch, bash_path):
    # Patch the module seams (NOT os.name globally — pathlib would try to
    # instantiate WindowsPath on POSIX and explode).
    import lib.todo_tracker as tt
    monkeypatch.setattr(tt, "_is_windows", lambda: True, raising=False)
    monkeypatch.setattr(tt, "_windows_bash", lambda: bash_path, raising=False)


def test_windows_routes_validator_through_git_bash(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))
    _fake_windows(monkeypatch, _GIT_BASH)

    item = TodoItem(
        content="x", active_form="x",
        validator='python3 check.py && (test -f out.json || echo missing)',
    )
    item.run_validator()

    cmd = captured["cmd"]
    assert isinstance(cmd, list) and cmd[0] == _GIT_BASH and cmd[1] == "-c", cmd
    assert captured["shell"] is False
    # POSIX syntax preserved inside the bash -c payload; python3 rewritten.
    assert "test -f out.json" in cmd[2]
    assert "python3 check.py" not in cmd[2] or sys.executable.endswith("python3"), cmd[2]
    assert shlex.quote(sys.executable) in cmd[2]


def test_windows_without_bash_falls_back_to_cmd_shell(monkeypatch):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))
    _fake_windows(monkeypatch, None)

    item = TodoItem(content="x", active_form="x", validator="python3 check.py ip")
    item.run_validator()

    cmd = captured["cmd"]
    assert isinstance(cmd, str), cmd
    assert captured["shell"] is True
    assert f'"{sys.executable}" check.py ip' == cmd, cmd


def test_windows_run_command_routes_through_git_bash(monkeypatch, tmp_path: Path):
    captured: dict = {}
    monkeypatch.setattr(subprocess, "run", _capture_run(captured))
    _fake_windows(monkeypatch, _GIT_BASH)

    tracker = TodoTracker(persist_path=tmp_path / "todos.json")
    todo = TodoItem(content="x", active_form="x", command="bash workflow/sim/scripts/check_sim_pass.sh")
    ok, _tail, _lines = tracker._run_command(todo, tmp_path / "cmd.log")

    assert ok is True
    cmd = captured["cmd"]
    assert isinstance(cmd, list) and cmd[0] == _GIT_BASH and cmd[1] == "-c", cmd
    assert captured["shell"] is False
