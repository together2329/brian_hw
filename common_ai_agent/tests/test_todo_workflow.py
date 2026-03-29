
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

@pytest.fixture
def temp_todo_file(tmp_path):
    todo_file = tmp_path / "test_todos.json"
    os.environ['TODO_FILE'] = str(todo_file)
    yield todo_file
    if todo_file.exists():
        todo_file.unlink()

def test_todo_status_transitions(temp_todo_file):
    """Test the core approved/rejected logic in TodoTracker"""
    tracker = TodoTracker(persist_path=temp_todo_file)
    tracker.add_todos([
        {"content": "Task 1", "status": "pending"},
        {"content": "Task 2", "status": "pending"}
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
    tracker.mark_approved(0)
    assert tracker.todos[0].status == "approved"
    assert tracker.todos[0].rejection_reason == ""
    # Should automatically advance to next pending
    assert tracker.current_index == 1
    assert tracker.todos[1].status == "in_progress"

def test_todo_update_tool_logic(temp_todo_file):
    """Test the todo_update tool handler directly"""
    # Initialize file via todo_write
    todo_write(todos=[{"content": "Tool Test", "status": "pending"}])
    
    # 1. Complete it
    result = todo_update(index=1, status="completed")
    assert "marked as completed" in result.lower()
    
    # 2. Try reject without reason (should return error message)
    result = todo_update(index=1, status="rejected")
    assert "Error: You MUST provide a 'reason'" in result
        
    # 3. Reject with reason
    result = todo_update(index=1, status="rejected", reason="Test rejection")
    assert "rejected" in result.lower()
    
    # 4. Approve (using mapped 'reviewed' alias for backward compatibility)
    result = todo_update(index=1, status="reviewed")
    assert "approved" in result.lower()

def test_todo_write_status_aliases(temp_todo_file):
    """Status aliases in todo_write should be auto-normalized, not rejected"""
    # "todo" -> "pending"
    result = todo_write(todos=[{"content": "Task A", "status": "todo"}])
    assert "Error" not in result, f"Expected success but got: {result}"

    # "wip" -> "in_progress"  (will be first pending→in_progress anyway, but alias must not error)
    result = todo_write(todos=[
        {"content": "Task B", "status": "wip"},
        {"content": "Task C", "status": "todo"},
    ])
    assert "Error" not in result, f"Expected success but got: {result}"

    # "done" -> "completed"
    result = todo_write(todos=[
        {"content": "Task D", "status": "in_progress"},
        {"content": "Task E", "status": "done"},
    ])
    assert "Error" not in result, f"Expected success but got: {result}"


def test_todo_update_status_aliases(temp_todo_file):
    """Status aliases in todo_update should be auto-normalized"""
    todo_write(todos=[{"content": "Alias Test", "status": "pending"}])

    # "done" -> "completed"
    result = todo_update(index=1, status="done")
    assert "marked as completed" in result.lower(), f"Expected completed but got: {result}"

    # "accepted" -> "approved"
    result = todo_update(index=1, status="accepted")
    assert "approved" in result.lower(), f"Expected approved but got: {result}"


def test_todo_tracker_progress_calculation(temp_todo_file):
    """Verify progress percentage only counts approved tasks"""
    tracker = TodoTracker(persist_path=temp_todo_file)
    tracker.add_todos([
        {"content": "A", "status": "approved"},
        {"content": "B", "status": "completed"},
        {"content": "C", "status": "rejected"},
        {"content": "D", "status": "pending"}
    ])
    
    # Only "A" is approved, so 1/4 = 0.25
    assert tracker.get_progress_pct() == 0.25
    
    tracker.mark_approved(1) # B
    assert tracker.get_progress_pct() == 0.50
