"""Tests for Phase 1: Static command execution in TodoItem."""
import sys
import os
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

sys.path.insert(0, str(Path(__file__).parent.parent))

from lib.todo_tracker import TodoItem, TodoTracker


def make_tracker(todos_data, tmp_path):
    tracker = TodoTracker(persist_path=tmp_path / "todo.json")
    tracker.add_todos(todos_data)
    return tracker


# ── Step 1: Field defaults ─────────────────────────────────────────────────────

class TestTodoItemFields:
    def test_command_defaults_to_empty(self):
        t = TodoItem(content="x", active_form="x")
        assert t.command == ""

    def test_on_reject_defaults_to_zero(self):
        t = TodoItem(content="x", active_form="x")
        assert t.on_reject == 0

    def test_command_logs_defaults_to_empty_list(self):
        t = TodoItem(content="x", active_form="x")
        assert t.command_logs == []

    def test_command_logs_not_shared_between_instances(self):
        a = TodoItem(content="a", active_form="a")
        b = TodoItem(content="b", active_form="b")
        a.command_logs.append({"cmd": "echo"})
        assert b.command_logs == []


# ── Step 2: Serialization roundtrip ───────────────────────────────────────────

class TestSerialization:
    def test_command_str_roundtrip(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint", "activeForm": "linting",
             "command": "make lint", "on_reject": 2}
        ], tmp_path)
        data = tracker.to_dict()
        t = data["todos"][0]
        assert t["command"] == "make lint"
        assert t["on_reject"] == 2
        assert t["command_logs"] == []

    def test_command_dict_roundtrip(self, tmp_path):
        cmd = {"tool": "run_command", "args": {"command": "echo hi"}}
        tracker = make_tracker([
            {"content": "run", "activeForm": "running", "command": cmd}
        ], tmp_path)
        data = tracker.to_dict()
        assert data["todos"][0]["command"] == cmd

    def test_command_logs_roundtrip(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t",
             "command_logs": [{"cmd": "echo", "ok": True, "tail": "hi", "lines": 1}]}
        ], tmp_path)
        assert tracker.todos[0].command_logs[0]["cmd"] == "echo"

    def test_persist_and_reload(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint", "activeForm": "linting",
             "command": "echo ok", "on_reject": 3}
        ], tmp_path)
        tracker.save()
        import json
        raw = json.loads((tmp_path / "todo.json").read_text())
        assert raw["todos"][0]["command"] == "echo ok"
        assert raw["todos"][0]["on_reject"] == 3


# ── Step 3: _run_command ──────────────────────────────────────────────────────

class TestRunCommand:
    def _make_todo(self, cmd):
        return TodoItem(content="t", active_form="t", command=cmd)

    def test_shell_success(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        todo = self._make_todo("echo hello")
        log = tmp_path / "out.log"
        ok, tail, lines = tracker._run_command(todo, log)
        assert ok is True
        assert "hello" in tail
        assert log.read_text() == "hello"

    def test_shell_failure(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        todo = self._make_todo("exit 1")
        log = tmp_path / "out.log"
        ok, tail, lines = tracker._run_command(todo, log)
        assert ok is False
        assert "[exit 1]" in tail
        assert "[exit 1]" in log.read_text()

    def test_shell_writes_log_file(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        todo = self._make_todo("echo hello world")
        log = tmp_path / "out.log"
        tracker._run_command(todo, log)
        assert log.exists()
        assert "hello world" in log.read_text()

    def test_tail_truncation(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        # Generate 30 lines
        cmd = "python3 -c \"for i in range(30): print(f'line {i}')\""
        todo = self._make_todo(cmd)
        log = tmp_path / "out.log"
        ok, tail, lines = tracker._run_command(todo, log)
        assert ok is True
        assert lines == 30
        tail_lines = tail.strip().splitlines()
        assert len(tail_lines) <= 15

    def test_invalid_command_format(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        todo = self._make_todo(12345)  # invalid type
        log = tmp_path / "out.log"
        ok, tail, lines = tracker._run_command(todo, log)
        assert ok is False
        assert "Invalid command format" in tail

    def test_dict_unknown_tool(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        todo = self._make_todo({"tool": "nonexistent_tool_xyz", "args": {}})
        log = tmp_path / "out.log"
        ok, tail, lines = tracker._run_command(todo, log)
        assert ok is False
        assert "Unknown tool" in tail

    def test_dict_known_tool(self, tmp_path):
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        mock_fn = MagicMock(return_value="tool output ok")
        todo = self._make_todo({"tool": "mock_tool", "args": {"x": 1}})
        log = tmp_path / "out.log"
        with patch("core.tools.AVAILABLE_TOOLS", {"mock_tool": mock_fn}):
            ok, tail, lines = tracker._run_command(todo, log)
        assert ok is True
        mock_fn.assert_called_once_with(x=1)


# ── Step 4: auto_execute_command ──────────────────────────────────────────────

class TestAutoExecuteCommand:
    def test_no_command_returns_none(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        result = tracker.auto_execute_command(0)
        assert result is None

    def test_success_sets_approved(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint", "activeForm": "linting", "command": "echo ok"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        ok, tail = tracker.auto_execute_command(0)
        assert ok is True
        assert tracker.todos[0].status == "approved"
        assert "[auto-command]" in tracker.todos[0].approved_reason

    def test_failure_sets_rejected(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint", "activeForm": "linting", "command": "exit 1"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        ok, tail = tracker.auto_execute_command(0)
        assert ok is False
        assert tracker.todos[0].status == "rejected"
        assert "[command failed]" in tracker.todos[0].rejection_reason

    def test_command_log_appended(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t", "command": "echo hi"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        logs = tracker.todos[0].command_logs
        assert len(logs) == 1
        assert logs[0]["cmd"] == "echo hi"
        assert logs[0]["ok"] is True
        assert "hi" in logs[0]["tail"]
        assert logs[0]["lines"] >= 1
        assert "log_file" in logs[0]

    def test_log_file_created_in_session_dir(self, tmp_path):
        tracker = make_tracker([
            {"content": "run lint", "activeForm": "linting", "command": "echo ok"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        with patch("src.config.SESSION_DIR", str(tmp_path)):
            tracker.auto_execute_command(0)
        log_dir = tmp_path / "command_logs"
        assert log_dir.exists()
        logs = list(log_dir.glob("task_1_*.log"))
        assert len(logs) == 1

    def test_run_number_increments(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t", "command": "echo hi"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        # Second run (simulate retry)
        tracker.todos[0].status = "in_progress"
        tracker.auto_execute_command(0)
        logs = tracker.todos[0].command_logs
        assert len(logs) == 2
        assert "_1.log" in logs[0]["log_file"]
        assert "_2.log" in logs[1]["log_file"]

    def test_on_reject_jumps_current_index(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        tracker.mark_in_progress(1)
        ok, _ = tracker.auto_execute_command(1)
        assert ok is False
        assert tracker.current_index == 0  # jumped to task 1 (0-based)

    def test_on_reject_out_of_range_stays(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint", "activeForm": "linting",
             "command": "exit 1", "on_reject": 999},
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        assert tracker.current_index == 0  # stays on current

    def test_success_advances_current_index(self, tmp_path):
        tracker = make_tracker([
            {"content": "lint",   "activeForm": "linting",   "command": "echo ok"},
            {"content": "review", "activeForm": "reviewing"},
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        # current_index should point to next pending task
        assert tracker.current_index == 1

    def test_out_of_range_index_returns_none(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t", "command": "echo hi"}
        ], tmp_path)
        assert tracker.auto_execute_command(99) is None

    def test_rejection_count_incremented_on_failure(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t", "command": "exit 1"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        assert tracker.todos[0].rejection_count == 1


# ── Step 5: tools.py integration ─────────────────────────────────────────────

class TestToolsIntegration:
    """Test todo_update(status='in_progress') with command field."""

    def _setup(self, tmp_path, todos_data):
        tracker = make_tracker(todos_data, tmp_path)
        import types, sys
        fake_main = types.ModuleType("main")
        fake_main.todo_tracker = tracker
        sys.modules["main"] = fake_main
        return tracker

    def teardown_method(self):
        import sys
        sys.modules.pop("main", None)

    def test_in_progress_with_command_returns_checkmark(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "lint", "activeForm": "linting", "command": "echo ok"}
        ])
        result = todo_update(index=1, status="in_progress")
        assert "✅" in result
        assert "command: echo ok" in result

    def test_in_progress_without_command_returns_arrow(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "implement", "activeForm": "implementing"}
        ])
        result = todo_update(index=1, status="in_progress")
        assert "▶" in result
        assert "in progress" in result

    def test_failed_command_returns_cross(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "lint", "activeForm": "linting", "command": "exit 1"}
        ])
        result = todo_update(index=1, status="in_progress")
        assert "❌" in result

    def test_failed_command_with_on_reject_shows_jump(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ])
        # Must approve task 1 first for sequential enforcement
        import sys
        sys.modules["main"].todo_tracker.mark_approved(0, reason="done for test purposes here")
        result = todo_update(index=2, status="in_progress")
        assert "❌" in result
        assert "Jumping to Task 1" in result

    def test_log_info_in_success_result(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "lint", "activeForm": "linting", "command": "echo hello"}
        ])
        with patch("src.config.SESSION_DIR", str(tmp_path)):
            result = todo_update(index=1, status="in_progress")
        assert "Log:" in result
        assert ".log" in result


# ── Step 6: Cascade reset ─────────────────────────────────────────────────────

class TestCascadeReset:
    def test_cascade_resets_approved_tasks(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        tracker.mark_approved(0, reason="implementation done and verified")
        tracker.mark_in_progress(1)
        tracker.auto_execute_command(1)
        assert tracker.todos[0].status == "pending"

    def test_cascade_sets_rejection_reason(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        tracker.mark_approved(0, reason="implementation done and verified")
        tracker.mark_in_progress(1)
        tracker.auto_execute_command(1)
        assert "cascade reset" in tracker.todos[0].rejection_reason

    def test_cascade_appends_notes(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        tracker.mark_approved(0, reason="implementation done and verified")
        tracker.mark_in_progress(1)
        tracker.auto_execute_command(1)
        assert len(tracker.todos[0].notes) >= 1
        assert "cascade reset" in tracker.todos[0].notes[-1]

    def test_cascade_includes_pending_tasks(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        # Task 1 stays pending (never approved)
        tracker.mark_in_progress(1)
        tracker.auto_execute_command(1)
        # failure context should also be appended to pending tasks
        assert len(tracker.todos[0].notes) >= 1
        assert "cascade reset" in tracker.todos[0].notes[-1]

    def test_cascade_only_resets_range(self, tmp_path):
        tracker = make_tracker([
            {"content": "explore",   "activeForm": "exploring"},
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 2},
        ], tmp_path)
        tracker.mark_approved(0, reason="exploration done thoroughly")
        tracker.mark_approved(1, reason="implementation complete and tested")
        tracker.mark_in_progress(2)
        tracker.auto_execute_command(2)
        # Task 1 (explore) should NOT be reset (out of jump range)
        assert tracker.todos[0].status == "approved"
        # Task 2 (implement) should be reset
        assert tracker.todos[1].status == "pending"

    def test_approved_reason_contains_tail(self, tmp_path):
        tracker = make_tracker([
            {"content": "echo task", "activeForm": "echoing",
             "command": "echo hello_world"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        assert "hello_world" in tracker.todos[0].approved_reason

    def test_empty_output_shows_no_output_message(self, tmp_path):
        tracker = make_tracker([
            {"content": "silent task", "activeForm": "running",
             "command": "true"}
        ], tmp_path)
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        assert "no output" in tracker.todos[0].approved_reason

    def test_rejection_reason_cleared_on_success(self, tmp_path):
        tracker = make_tracker([
            {"content": "t", "activeForm": "t", "command": "echo ok"}
        ], tmp_path)
        tracker.todos[0].rejection_reason = "previous failure"
        tracker.mark_in_progress(0)
        tracker.auto_execute_command(0)
        assert tracker.todos[0].rejection_reason == ""

    def test_stagnation_keeps_on_reject_jump_after_max_retries(self, tmp_path):
        tracker = make_tracker([
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ], tmp_path)
        tracker.mark_approved(0, reason="implementation done and verified")
        # Simulate 2 prior rejections
        tracker.todos[1].rejection_count = 2
        tracker.mark_in_progress(1)
        tracker.auto_execute_command(1)
        # After 3rd failure, stagnation is noted but jump target is preserved
        assert "stagnation" in tracker.todos[1].rejection_reason
        assert "continuing jump to configured on_reject target" in tracker.todos[1].rejection_reason
        # current_index should jump to task 1 (index 0)
        assert tracker.current_index == 0


# ── Step 7: todo_add / todo_update command fields ─────────────────────────────

class TestTodoAddCommand:
    def _setup(self, tmp_path, todos_data=None):
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=tmp_path / "todo.json")
        if todos_data:
            tracker.add_todos(todos_data)
        import types, sys
        fake_main = types.ModuleType("main")
        fake_main.todo_tracker = tracker
        sys.modules["main"] = fake_main
        return tracker

    def teardown_method(self):
        import sys
        sys.modules.pop("main", None)

    def test_stagnation_no_jump_message(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "implement", "activeForm": "implementing"},
            {"content": "lint",      "activeForm": "linting",
             "command": "exit 1", "on_reject": 1},
        ])
        import sys
        tracker = sys.modules["main"].todo_tracker
        tracker.mark_approved(0, reason="implementation done and verified")
        # Simulate 2 prior rejections so 3rd triggers stagnation
        tracker.todos[1].rejection_count = 2
        result = todo_update(index=2, status="in_progress")
        assert "❌" in result
        # stagnation: current_index stays on task 2 (index 1), no jump
        assert "Jumping to Task 1" not in result

    def test_todo_add_with_command(self, tmp_path):
        from core.tools import scoped_todo_runtime, todo_add
        tracker = self._setup(tmp_path)
        with scoped_todo_runtime(todo_tracker=tracker, todo_file=tracker._persist_path):
            todo_add(
                content="Run lint",
                activeForm="linting",
                detail="Run the lint target from the project root.",
                criteria="make lint exits successfully.",
                command="make lint",
                on_reject=0,
            )
        import sys
        tracker = sys.modules["main"].todo_tracker
        assert tracker.todos[0].command == "make lint"

    def test_todo_add_with_on_reject(self, tmp_path):
        from core.tools import scoped_todo_runtime, todo_add
        tracker = self._setup(tmp_path)
        with scoped_todo_runtime(todo_tracker=tracker, todo_file=tracker._persist_path):
            todo_add(
                content="Run lint",
                activeForm="linting",
                detail="Run the lint command and capture failure output.",
                criteria="Failure jumps to the configured rejection target.",
                command="exit 1",
                on_reject=1,
            )
        import sys
        tracker = sys.modules["main"].todo_tracker
        assert tracker.todos[0].on_reject == 1

    def test_todo_add_requires_detail_and_criteria(self, tmp_path):
        from core.tools import scoped_todo_runtime, todo_add
        tracker = self._setup(tmp_path)
        with scoped_todo_runtime(todo_tracker=tracker, todo_file=tracker._persist_path):
            assert todo_add(content="Run lint", criteria="lint passes") == "Error: 'detail' is required."
            assert todo_add(content="Run lint", detail="Run lint") == "Error: 'criteria' is required."
        import sys
        tracker = sys.modules["main"].todo_tracker
        assert tracker.todos == []

    def test_todo_update_sets_command(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [{"content": "t", "activeForm": "t"}])
        todo_update(index=1, command="echo updated")
        import sys
        tracker = sys.modules["main"].todo_tracker
        assert tracker.todos[0].command == "echo updated"

    def test_todo_update_sets_on_reject(self, tmp_path):
        from core.tools import todo_update
        self._setup(tmp_path, [
            {"content": "a", "activeForm": "a"},
            {"content": "b", "activeForm": "b"},
        ])
        todo_update(index=2, on_reject=1)
        import sys
        tracker = sys.modules["main"].todo_tracker
        assert tracker.todos[1].on_reject == 1
