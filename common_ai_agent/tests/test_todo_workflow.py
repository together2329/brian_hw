
import pytest
import os
import json
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

# Add project root to sys.path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / 'src'))

from lib.todo_tracker import TodoTracker
from core.tools import todo_update, todo_write

def _todo(content, status="pending", **extra):
    """Build a schema-complete todo item for current todo_write validation."""
    data = {
        "content": content,
        "status": status,
        "detail": extra.pop("detail", f"Do {content}"),
        "criteria": extra.pop("criteria", f"{content} verified"),
    }
    data.update(extra)
    return data


def _todo_write_in_plan(*args, **kwargs):
    old_plan_mode = os.environ.get("PLAN_MODE")
    old_plan_count = os.environ.get("_PLAN_TODO_WRITE_COUNT")
    os.environ["PLAN_MODE"] = "true"
    try:
        return todo_write(*args, **kwargs)
    finally:
        if old_plan_mode is None:
            os.environ.pop("PLAN_MODE", None)
        else:
            os.environ["PLAN_MODE"] = old_plan_mode
        if old_plan_count is None:
            os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
        else:
            os.environ["_PLAN_TODO_WRITE_COUNT"] = old_plan_count

@pytest.fixture
def temp_todo_file(tmp_path, monkeypatch):
    todo_file = tmp_path / "test_todos.json"
    err_file = tmp_path / "todo_error.json"
    monkeypatch.setenv('TODO_FILE', str(todo_file))
    import config as cfg
    monkeypatch.setattr(cfg, "TODO_FILE", str(todo_file), raising=False)
    monkeypatch.setattr(cfg, "TODO_ERROR_FILE", str(err_file), raising=False)
    import lib.todo_tracker as todo_mod
    monkeypatch.setattr(todo_mod, "TODO_FILE", todo_file, raising=False)
    import core.tools as tools_mod
    monkeypatch.setattr(tools_mod, "commit_ip", lambda message: None)
    monkeypatch.setattr(tools_mod, "_git_tag_todo", lambda *args, **kwargs: None)
    tracker = TodoTracker(persist_path=todo_file)
    import main as main_mod
    monkeypatch.setattr(main_mod, "todo_tracker", tracker, raising=False)
    try:
        import src.main as src_main
        monkeypatch.setattr(src_main, "todo_tracker", tracker, raising=False)
    except Exception:
        pass
    yield todo_file
    if todo_file.exists():
        todo_file.unlink()

def test_todo_status_transitions(temp_todo_file):
    """Test the core approved/rejected logic in TodoTracker"""
    tracker = TodoTracker(persist_path=temp_todo_file)
    tracker.add_todos([
        _todo("Task 1"),
        _todo("Task 2"),
    ])
    
    # 1. Mark in progress
    tracker.mark_in_progress(0)
    assert tracker.todos[0].status == "in_progress"
    
    # 2. Mark completed (awaiting review)
    tracker.mark_completed(0)
    assert tracker.todos[0].status == "completed"
    
    # 3. Reject with reason
    tracker.mark_rejected(0, "Needs more detail")
    assert tracker.todos[0].status == "rejected"
    assert tracker.todos[0].rejection_reason == "Needs more detail"
    assert tracker.current_index == 0 # Must revert to this task
    
    # 4. Mark completed again
    tracker.mark_completed(0)
    
    # 5. Approve
    tracker.mark_approved(0, "Verified revised task output")
    assert tracker.todos[0].status == "approved"
    assert tracker.todos[0].rejection_reason == ""
    # Should point at the next actionable task without silently starting it.
    assert tracker.current_index == 1
    assert tracker.todos[1].status == "pending"

def test_todo_update_tool_logic(temp_todo_file):
    """Test the todo_update tool handler directly"""
    # Initialize file via todo_write
    _todo_write_in_plan(todos=[_todo("Tool Test")])
    
    import main as main_mod

    # 1. Start and complete it after simulated evidence/tool activity
    result = todo_update(index=1, status="in_progress")
    assert "in progress" in result.lower()
    main_mod.todo_tracker.todos[0].tools_since_in_progress = 1
    main_mod.todo_tracker.save()
    result = todo_update(index=1, status="completed")
    assert "marked completed" in result.lower()
    
    # 2. Try reject without reason (should return error message)
    main_mod.todo_tracker.todos[0].tools_since_completed = 1
    main_mod.todo_tracker.save()
    result = todo_update(index=1, status="rejected")
    assert "reason" in result and "REQUIRED" in result
        
    # 3. Reject with reason
    result = todo_update(index=1, status="rejected", reason="Test rejection reason")
    assert "rejected" in result.lower()
    
    # 4. Approve (using mapped 'reviewed' alias for backward compatibility)
    result = todo_update(index=1, status="in_progress")
    assert "in progress" in result.lower()
    main_mod.todo_tracker.todos[0].tools_since_in_progress = 1
    main_mod.todo_tracker.save()
    result = todo_update(index=1, status="completed")
    assert "marked completed" in result.lower()
    result = todo_update(index=1, status="reviewed", reason="Verified after rejection")
    assert "approved" in result.lower()

def test_todo_write_status_aliases(temp_todo_file):
    """Status aliases in todo_write should be auto-normalized, not rejected"""
    # "todo" -> "pending"
    result = _todo_write_in_plan(todos=[_todo("Task A", "todo")])
    assert "Error" not in result, f"Expected success but got: {result}"

    # "wip" -> "in_progress"  (will be first pending→in_progress anyway, but alias must not error)
    result = _todo_write_in_plan(todos=[
        _todo("Task B", "wip"),
        _todo("Task C", "todo"),
    ])
    assert "Error" not in result, f"Expected success but got: {result}"

    # "done" -> "completed"
    result = _todo_write_in_plan(todos=[
        _todo("Task D", "in_progress"),
        _todo("Task E", "done"),
    ])
    assert "Error" not in result, f"Expected success but got: {result}"


def test_todo_write_keeps_all_tasks_pending_in_plan_mode(temp_todo_file, monkeypatch):
    monkeypatch.setenv("PLAN_MODE", "true")

    result = _todo_write_in_plan(todos=[
        _todo("Write implementation plan", "wip"),
        _todo("Run verification", "completed"),
    ])

    assert "Error" not in result, f"Expected success but got: {result}"
    import main as main_mod
    assert [todo.status for todo in main_mod.todo_tracker.todos] == ["pending", "pending"]


def test_todo_update_blocks_status_changes_in_plan_mode(temp_todo_file, monkeypatch):
    monkeypatch.setenv("PLAN_MODE", "true")
    _todo_write_in_plan(todos=[_todo("Write implementation plan")])

    result = todo_update(index=1, status="in_progress")

    assert "blocked in plan mode" in result
    import main as main_mod
    assert main_mod.todo_tracker.todos[0].status == "pending"

    result = todo_update(index=1, detail="Expanded planning detail")

    assert "updated" in result
    assert main_mod.todo_tracker.todos[0].detail == "Expanded planning detail"


def test_todo_update_status_aliases(temp_todo_file):
    """Status aliases in todo_update should be auto-normalized"""
    _todo_write_in_plan(todos=[_todo("Alias Test")])

    # "done" -> "completed"
    result = todo_update(index=1, status="in_progress")
    assert "in progress" in result.lower()
    import main as main_mod
    main_mod.todo_tracker.todos[0].tools_since_in_progress = 1
    main_mod.todo_tracker.save()
    result = todo_update(index=1, status="done")
    assert "marked completed" in result.lower(), f"Expected completed but got: {result}"

    # "accepted" -> "approved"
    result = todo_update(index=1, status="accepted", reason="Verified alias approval path")
    assert "approved" in result.lower(), f"Expected approved but got: {result}"


def test_todo_tracker_progress_calculation(temp_todo_file):
    """Verify progress percentage only counts approved tasks"""
    tracker = TodoTracker(persist_path=temp_todo_file)
    tracker.add_todos([
        _todo("A", "approved"),
        _todo("B", "completed"),
        _todo("C", "rejected"),
        _todo("D"),
    ])
    
    # Only "A" is approved, so 1/4 = 0.25
    assert tracker.get_progress_pct() == 0.25
    
    tracker.mark_approved(1, "Verified B output") # B
    assert tracker.get_progress_pct() == 0.50
