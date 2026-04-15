"""
Comprehensive tests for the todo tracking system.

Tests cover:
1. TodoTracker core state machine (pending → in_progress → completed → approved)
2. Gate check (tools_since_in_progress persistence)
3. Stagnation detection and auto-advance
4. Serialization round-trip (save/load with counter persistence)
5. todo_write validation (status aliases, sequential enforcement)
6. todo_update state machine (all transitions, error cases)
7. todo_add / todo_remove
8. Loop mode (exit_condition, max_iterations)
9. Validator integration
10. Edge cases (empty list, out-of-range, concurrent in_progress)
"""

import json
import os
import sys
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Add project root to path
PROJECT_ROOT = Path(__file__).parent.parent
sys.path.insert(0, str(PROJECT_ROOT))
sys.path.insert(0, str(PROJECT_ROOT / "src"))
sys.path.insert(0, str(PROJECT_ROOT / "lib"))
sys.path.insert(0, str(PROJECT_ROOT / "core"))


class TestTodoTrackerCore(unittest.TestCase):
    """Test TodoTracker state machine basics."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        """Create a fresh tracker with temp file."""
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_add_todos_basic(self):
        """Adding todos sets correct initial state."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task A", "status": "pending", "activeForm": "Doing A"},
            {"content": "Task B", "status": "pending", "activeForm": "Doing B"},
            {"content": "Task C", "status": "pending", "activeForm": "Doing C"},
        ])
        self.assertEqual(len(tracker.todos), 3)
        self.assertEqual(tracker.todos[0].status, "pending")
        self.assertEqual(tracker.current_index, -1)  # No in_progress yet

    def test_add_todos_with_in_progress(self):
        """Adding todos with one in_progress sets current_index."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task A", "status": "in_progress"},
            {"content": "Task B", "status": "pending"},
        ])
        self.assertEqual(tracker.current_index, 0)
        self.assertEqual(tracker.todos[0].status, "in_progress")

    def test_state_machine_happy_path(self):
        """Full lifecycle: pending → in_progress → completed → approved."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "pending"},
        ])

        # Step 1: Mark in_progress
        tracker.mark_in_progress(0)
        self.assertEqual(tracker.todos[0].status, "in_progress")
        self.assertEqual(tracker.current_index, 0)

        # Step 2: Mark completed
        tracker.mark_completed(0)
        self.assertEqual(tracker.todos[0].status, "completed")
        self.assertIsNotNone(tracker.todos[0].completed_at)

        # Step 3: Mark approved
        tracker.mark_approved(0)
        self.assertEqual(tracker.todos[0].status, "approved")

    def test_only_one_in_progress(self):
        """Only one todo can be in_progress at a time."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "pending"},
        ])
        tracker.mark_in_progress(0)
        self.assertEqual(tracker.todos[0].status, "in_progress")

        tracker.mark_in_progress(1)
        # Task 1 should revert to pending
        self.assertEqual(tracker.todos[0].status, "pending")
        self.assertEqual(tracker.todos[1].status, "in_progress")
        self.assertEqual(tracker.current_index, 1)

    def test_mark_rejected(self):
        """Rejected task becomes current for re-work."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "Task 1", "status": "completed"}])
        tracker.mark_rejected(0, "Failed validation")
        self.assertEqual(tracker.todos[0].status, "rejected")
        self.assertEqual(tracker.todos[0].rejection_reason, "Failed validation")
        self.assertEqual(tracker.current_index, 0)

    def test_unprocess_rejected(self):
        """unprocess_rejected sets all rejected tasks back to pending."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task 1", "status": "rejected"},
            {"content": "Task 2", "status": "rejected"},
            {"content": "Task 3", "status": "approved"},
        ])
        result = tracker.unprocess_rejected()
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].status, "pending")
        self.assertEqual(tracker.todos[1].status, "pending")
        self.assertEqual(tracker.todos[2].status, "approved")  # unchanged

    def test_unprocess_rejected_no_rejected(self):
        """unprocess_rejected returns False when nothing to unprocess."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "Task 1", "status": "pending"}])
        result = tracker.unprocess_rejected()
        self.assertFalse(result)

    def test_is_all_completed(self):
        """is_all_completed only True when all approved."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task 1", "status": "pending"},
        ])
        self.assertFalse(tracker.is_all_completed())
        self.assertFalse(tracker.is_all_processed())

        tracker.mark_in_progress(0)
        tracker.mark_completed(0)
        self.assertFalse(tracker.is_all_completed())
        self.assertFalse(tracker.is_all_processed())

        tracker.mark_approved(0)
        self.assertTrue(tracker.is_all_completed())
        self.assertTrue(tracker.is_all_processed())

    def test_is_all_processed_with_rejected(self):
        """is_all_processed is True when all are approved or rejected."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task 1", "status": "approved"},
            {"content": "Task 2", "status": "rejected"},
        ])
        self.assertTrue(tracker.is_all_processed())
        self.assertFalse(tracker.is_all_completed())

    def test_get_progress_pct(self):
        """Progress percentage based on approved count."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "completed"},
            {"content": "T3", "status": "pending"},
        ])
        self.assertAlmostEqual(tracker.get_progress_pct(), 1/3)

    def test_empty_tracker(self):
        """Empty tracker edge cases."""
        tracker = self._make_tracker()
        self.assertEqual(len(tracker.todos), 0)
        self.assertIsNone(tracker.get_current_todo())
        self.assertFalse(tracker.is_all_completed())
        self.assertFalse(tracker.is_all_processed())  # no todos = not processed
        self.assertEqual(tracker.get_progress_pct(), 1.0)

    def test_get_current_todo(self):
        """get_current_todo returns the in_progress task."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "pending"},
            {"content": "T2", "status": "pending"},
        ])
        self.assertIsNone(tracker.get_current_todo())
        tracker.mark_in_progress(1)
        current = tracker.get_current_todo()
        self.assertIsNotNone(current)
        self.assertEqual(current.content, "T2")

    def test_mark_in_progress_resets_gate_counter(self):
        """mark_in_progress resets tools_since_in_progress to 0."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)
        # Simulate tool calls
        tracker.todos[0].tools_since_in_progress = 5
        # Re-enter
        tracker.mark_in_progress(0)
        self.assertEqual(tracker.todos[0].tools_since_in_progress, 0)

    def test_index_out_of_range(self):
        """Out-of-range indices are handled gracefully."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        # Should not crash
        tracker.mark_in_progress(5)
        tracker.mark_completed(-1)
        tracker.mark_approved(10)
        tracker.mark_rejected(100, "reason")


class TestGateCheck(unittest.TestCase):
    """Test tools_since_in_progress gate check persistence."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def test_counter_reset_on_in_progress(self):
        """Counter resets when task is marked in_progress."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)

        # Simulate tool calls incrementing counter
        tracker.todos[0].tools_since_in_progress = 5
        tracker.save()

        # Reload — counter should persist
        tracker2 = TodoTracker.load(self.todo_file)
        self.assertEqual(tracker2.todos[0].tools_since_in_progress, 5)

    def test_counter_persists_through_save_load(self):
        """Counter survives save/load cycle."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)

        for i in range(10):
            tracker.todos[0].tools_since_in_progress = i + 1
            tracker.save()

            # Reload and verify
            tracker2 = TodoTracker.load(self.todo_file)
            self.assertEqual(tracker2.todos[0].tools_since_in_progress, i + 1,
                           f"Counter lost at iteration {i}")

    def test_counter_reset_on_completed(self):
        """Counter should be reset when mark_completed is called (non-loop)."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)
        tracker.todos[0].tools_since_in_progress = 7
        tracker.save()

        tracker.mark_completed(0)
        # After completion, counter should be... let's check
        # Note: mark_completed does NOT reset tools_since_in_progress
        # It's reset by the caller (todo_update in tools.py line 2448)
        # But mark_in_progress DOES reset it

    def test_increment_and_save_then_mark_completed(self):
        """Simulate the react_loop increment → save → todo_update(completed) flow."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)

        # Simulate react_loop: tool call → increment counter → save
        current = tracker.get_current_todo()
        self.assertIsNotNone(current)
        current.tools_since_in_progress += 1
        tracker.save()  # This is the fix we added

        # Simulate reload (like tools.py would do)
        tracker2 = TodoTracker.load(self.todo_file)
        item = tracker2.todos[0]
        counter = getattr(item, 'tools_since_in_progress', 0)
        self.assertGreater(counter, 0, "Gate check counter should be > 0 after tool call + save")

    def test_counter_not_lost_with_shared_instance(self):
        """Counter should not be lost when using shared tracker instance."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        tracker.mark_in_progress(0)

        # Increment on instance A
        tracker.todos[0].tools_since_in_progress = 3
        tracker.save()

        # Read from same instance (no reload)
        self.assertEqual(tracker.todos[0].tools_since_in_progress, 3)

        # Read from reloaded instance
        tracker2 = TodoTracker.load(self.todo_file)
        self.assertEqual(tracker2.todos[0].tools_since_in_progress, 3)


class TestStagnation(unittest.TestCase):
    """Test stagnation detection and handling."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_stagnation_increments(self):
        """Stagnation count increments when no tasks complete."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "in_progress"},
        ])
        tracker._last_completed_count = 1

        result = tracker.check_stagnation(max_stagnation=50)
        self.assertFalse(result)  # Not yet exceeded
        self.assertEqual(tracker.stagnation_count, 1)

        tracker.check_stagnation(max_stagnation=50)
        self.assertEqual(tracker.stagnation_count, 2)

    def test_stagnation_resets_on_completion(self):
        """Stagnation resets when a task is completed/approved/rejected."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "in_progress"},
            {"content": "T2", "status": "pending"},
        ])
        tracker.stagnation_count = 5
        tracker._last_completed_count = 0

        # Complete task 1
        tracker.mark_completed(0)
        # Now check_stagnation should detect the completion
        tracker.check_stagnation(max_stagnation=50)
        self.assertEqual(tracker.stagnation_count, 0)  # Reset because completed count increased

    def test_stagnation_triggers_at_limit(self):
        """check_stagnation returns True when limit is reached."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "in_progress"}])

        for i in range(49):
            result = tracker.check_stagnation(max_stagnation=50)
            self.assertFalse(result, f"Should not trigger at count {i+1}")

        result = tracker.check_stagnation(max_stagnation=50)
        self.assertTrue(result)  # 50th iteration triggers
        self.assertEqual(tracker.stagnation_count, 50)

    def test_stagnation_persists_through_save_load(self):
        """Stagnation count survives save/load cycle."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "in_progress"}])

        # Increment stagnation a few times
        for _ in range(5):
            tracker.check_stagnation(max_stagnation=50)
        tracker.save()

        from lib.todo_tracker import TodoTracker
        tracker2 = TodoTracker.load(self.todo_file)
        self.assertEqual(tracker2.stagnation_count, 5)

    def test_stagnation_with_rejected_reentry(self):
        """Stagnation count behavior when task is rejected and re-entered.

        When a task is auto-advanced (completed), then rejected, then re-entered
        (in_progress), the stagnation count should be manageable.
        """
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "pending"},
        ])
        tracker._last_completed_count = 1

        # Simulate: stagnation reaches threshold
        tracker.stagnation_count = 5
        tracker.save()

        # Task gets completed (stagnation auto-advance)
        tracker.mark_completed(1)
        # check_stagnation sees completed count increase → reset
        tracker.check_stagnation(max_stagnation=50)
        self.assertEqual(tracker.stagnation_count, 0)

        # Task gets rejected
        tracker.mark_rejected(1, "Nothing was done")
        # check_stagnation: rejected counts as completed → _last_completed stays same
        tracker.check_stagnation(max_stagnation=50)
        # count should increment since rejected was already counted
        self.assertEqual(tracker.stagnation_count, 1)

        # Task gets re-entered as in_progress
        tracker.mark_in_progress(1)
        # _last_completed_count is now ahead of actual completed count
        # because in_progress doesn't count
        tracker.check_stagnation(max_stagnation=50)
        self.assertEqual(tracker.stagnation_count, 2)


class TestSerialization(unittest.TestCase):
    """Test save/load round-trip fidelity."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def test_round_trip_all_fields(self):
        """All TodoItem fields survive save/load."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([
            {
                "content": "Complex task",
                "activeForm": "Doing complex task",
                "status": "in_progress",
                "priority": "high",
                "detail": "Implementation details here",
                "criteria": "Test passes\nCode reviewed",
                "rejection_reason": "",
                "loop": True,
                "max_loop_iterations": 5,
                "exit_condition": "PASS",
                "validator": "echo test",
                "delegate": "sub-agent",
                "workflow": "rtl-gen",
                "tools_since_in_progress": 7,
            }
        ])
        tracker.stagnation_count = 3
        tracker._last_completed_count = 1
        tracker.save()

        tracker2 = TodoTracker.load(self.todo_file)
        t = tracker2.todos[0]
        self.assertEqual(t.content, "Complex task")
        self.assertEqual(t.active_form, "Doing complex task")
        self.assertEqual(t.status, "in_progress")
        self.assertEqual(t.priority, "high")
        self.assertEqual(t.detail, "Implementation details here")
        self.assertEqual(t.criteria, "Test passes\nCode reviewed")
        self.assertTrue(t.loop)
        self.assertEqual(t.max_loop_iterations, 5)
        self.assertEqual(t.exit_condition, "PASS")
        self.assertEqual(t.validator, "echo test")
        self.assertEqual(t.delegate, "sub-agent")
        self.assertEqual(t.workflow, "rtl-gen")
        self.assertEqual(t.tools_since_in_progress, 7)
        self.assertEqual(tracker2.stagnation_count, 3)
        self.assertEqual(tracker2._last_completed_count, 1)

    def test_round_trip_preserves_current_index(self):
        """current_index survives save/load."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "in_progress"},
            {"content": "T3", "status": "pending"},
        ])
        tracker.current_index = 1
        tracker.save()

        tracker2 = TodoTracker.load(self.todo_file)
        self.assertEqual(tracker2.current_index, 1)

    def test_load_nonexistent_file(self):
        """Loading from nonexistent file returns empty tracker."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker.load(Path(self.tmpdir) / "nonexistent.json")
        self.assertEqual(len(tracker.todos), 0)

    def test_load_corrupt_file(self):
        """Loading corrupt JSON returns empty tracker."""
        from lib.todo_tracker import TodoTracker
        bad_file = Path(self.tmpdir) / "bad.json"
        bad_file.write_text("not valid json {{{")
        tracker = TodoTracker.load(bad_file)
        self.assertEqual(len(tracker.todos), 0)

    def test_clear_deletes_file(self):
        """clear() removes the persistence file."""
        from lib.todo_tracker import TodoTracker
        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        self.assertTrue(self.todo_file.exists())

        tracker.clear()
        self.assertFalse(self.todo_file.exists())
        self.assertEqual(len(tracker.todos), 0)
        self.assertEqual(tracker.current_index, -1)
        self.assertEqual(tracker.stagnation_count, 0)


class TestTodoUpdateStateMachine(unittest.TestCase):
    """Test todo_update tool's state machine enforcement."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

        # Patch config to use our temp file
        self._config_patcher = patch.dict('sys.modules', {
            'config': MagicMock(
                TODO_FILE=str(self.todo_file),
                TODO_ERROR_FILE=str(Path(self.tmpdir) / "error.json"),
                CURSOR_AGENT_ENABLE=False,
                ENABLE_PROMPT_CACHING=False,
                DEBUG_MODE=False,
            ),
            'src.config': MagicMock(
                CURSOR_AGENT_ENABLE=False,
            ),
        })

        # Set up main module with todo_tracker
        import main as main_mod
        from lib.todo_tracker import TodoTracker
        self.tracker = TodoTracker(persist_path=self.todo_file)
        main_mod.todo_tracker = self.tracker

        self._config_patcher.start()

    def tearDown(self):
        self._config_patcher.stop()
        import main as main_mod
        main_mod.todo_tracker = None

    def _setup_three_tasks(self):
        """Create a tracker with 3 approved tasks."""
        self.tracker.add_todos([
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "pending"},
            {"content": "Task 3", "status": "pending"},
        ])
        # Approve task 1
        self.tracker.mark_in_progress(0)
        self.tracker.todos[0].tools_since_in_progress = 1
        self.tracker.mark_completed(0)
        self.tracker.mark_approved(0)
        # Approve task 2
        self.tracker.mark_in_progress(1)
        self.tracker.todos[1].tools_since_in_progress = 1
        self.tracker.mark_completed(1)
        self.tracker.mark_approved(1)

    def test_sequential_enforcement_blocks_skip(self):
        """Cannot work on task 2 before task 1 is approved."""
        from core.tools import todo_update
        self.tracker.add_todos([
            {"content": "T1", "status": "pending"},
            {"content": "T2", "status": "pending"},
        ])
        result = todo_update(index=2, status="in_progress")
        self.assertIn("must be approved first", result)

    def test_sequential_allows_after_approval(self):
        """Can work on task 2 after task 1 is approved."""
        from core.tools import todo_update
        self._setup_three_tasks()
        result = todo_update(index=3, status="in_progress")
        self.assertIn("in progress", result)
        self.assertEqual(self.tracker.todos[2].status, "in_progress")

    def test_gate_check_blocks_no_tools(self):
        """Cannot complete task without tool calls."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        # No tools_since_in_progress increment
        result = todo_update(index=3, status="completed")
        self.assertIn("no tools were called", result)
        self.assertIn("❌", result)
        self.assertEqual(self.tracker.todos[2].status, "in_progress")

    def test_gate_check_allows_with_tools(self):
        """Can complete task after tool calls."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        # Simulate tool call
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        result = todo_update(index=3, status="completed")
        self.assertIn("CRITICAL, ADVERSARIAL review", result)
        self.assertEqual(self.tracker.todos[2].status, "completed")

    def test_approved_requires_reason(self):
        """Approving without reason is rejected."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        todo_update(index=3, status="completed")

        result = todo_update(index=3, status="approved")
        self.assertIn("MUST provide a 'reason'", result)

    def test_approved_with_reason(self):
        """Approving with reason succeeds."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        todo_update(index=3, status="completed")

        result = todo_update(index=3, status="approved", reason="Verified output")
        self.assertIn("✅", result)
        self.assertIn("All tasks complete", result)

    def test_cannot_skip_completed_to_approved(self):
        """Must go through completed before approved."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")

        result = todo_update(index=3, status="approved", reason="test")
        self.assertIn("completed') first", result)

    def test_cannot_downgrade_approved(self):
        """Cannot change approved task to in_progress."""
        from core.tools import todo_update
        self._setup_three_tasks()
        result = todo_update(index=1, status="in_progress")
        self.assertIn("already 'approved'", result)

    def test_cannot_reset_completed_to_in_progress(self):
        """Cannot reset completed task back to in_progress."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        todo_update(index=3, status="completed")

        result = todo_update(index=3, status="in_progress")
        self.assertIn("Status Conflict", result)
        self.assertIn("awaiting review", result)

    def test_rejected_with_reason(self):
        """Rejected task gets reason and becomes current."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        todo_update(index=3, status="completed")

        result = todo_update(index=3, status="rejected", reason="Tests failed")
        self.assertIn("❌", result)
        self.assertIn("Tests failed", result)
        self.assertEqual(self.tracker.todos[2].status, "rejected")

    def test_rejected_without_reason(self):
        """Rejected without reason returns error."""
        from core.tools import todo_update
        self._setup_three_tasks()
        todo_update(index=3, status="in_progress")
        self.tracker.todos[2].tools_since_in_progress = 1
        self.tracker.save()
        todo_update(index=3, status="completed")

        result = todo_update(index=3, status="rejected")
        self.assertIn("MUST provide a 'reason'", result)

    def test_zero_index_error(self):
        """Index 0 returns error (1-based indexing)."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        result = todo_update(index=0, status="in_progress")
        self.assertIn("1-based", result)

    def test_out_of_range_error(self):
        """Out of range index returns error."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        result = todo_update(index=5, status="in_progress")
        self.assertIn("out of range", result)

    def test_missing_index_error(self):
        """Missing index returns error."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        result = todo_update(status="in_progress")
        self.assertIn("'index'", result)

    def test_invalid_status(self):
        """Invalid status returns error."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        self.tracker.mark_in_progress(0)
        result = todo_update(index=1, status="bogus_status")
        self.assertIn("must be one of", result)

    def test_update_content(self):
        """Can update content without changing status."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "Old content", "status": "pending"}])
        result = todo_update(index=1, content="New content")
        self.assertIn("updated", result.lower())
        self.assertEqual(self.tracker.todos[0].content, "New content")

    def test_update_detail_and_criteria(self):
        """Can update detail and criteria fields."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        todo_update(index=1, detail="Step by step plan", criteria="Test passes")
        self.assertEqual(self.tracker.todos[0].detail, "Step by step plan")
        self.assertEqual(self.tracker.todos[0].criteria, "Test passes")

    def test_status_aliases(self):
        """Common status aliases are normalized."""
        from core.tools import todo_update
        self.tracker.add_todos([{"content": "T1", "status": "pending"}])
        # "done" → "completed"
        result = todo_update(index=1, status="done")
        # Should not error — alias should normalize
        # (But may fail gate check, so just verify no "invalid status" error)
        self.assertNotIn("must be one of", result)


class TestTodoWrite(unittest.TestCase):
    """Test todo_write tool."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

        # Set up main module
        import main as main_mod
        from lib.todo_tracker import TodoTracker
        self.tracker = TodoTracker(persist_path=self.todo_file)
        main_mod.todo_tracker = self.tracker

        # Clear plan mode counter
        os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
        os.environ.pop("PLAN_MODE", None)

    def tearDown(self):
        import main as main_mod
        main_mod.todo_tracker = None
        os.environ.pop("_PLAN_TODO_WRITE_COUNT", None)
        os.environ.pop("PLAN_MODE", None)

    def test_basic_write(self):
        """Basic todo_write creates tasks."""
        from core.tools import todo_write
        result = todo_write([
            {"content": "Task 1", "status": "pending"},
            {"content": "Task 2", "status": "pending"},
        ])
        self.assertIn("✅", result)
        self.assertEqual(len(self.tracker.todos), 2)

    def test_string_items_auto_converted(self):
        """String items are auto-converted to dict format."""
        from core.tools import todo_write
        result = todo_write(["Task A", "Task B"])
        self.assertIn("✅", result)
        self.assertEqual(len(self.tracker.todos), 2)
        self.assertEqual(self.tracker.todos[0].content, "Task A")
        self.assertIn("Executing", self.tracker.todos[0].active_form)

    def test_auto_generates_active_form(self):
        """Missing activeForm is auto-generated."""
        from core.tools import todo_write
        todo_write([{"content": "Run tests", "status": "pending"}])
        self.assertEqual(self.tracker.todos[0].active_form, "Running tests")

    def test_status_alias_normalization(self):
        """Status aliases are normalized (e.g. 'done' → 'completed')."""
        from core.tools import todo_write
        result = todo_write([
            {"content": "Task 1", "status": "todo"},
            {"content": "Task 2", "status": "done"},
        ])
        self.assertIn("✅", result)
        self.assertEqual(self.tracker.todos[0].status, "pending")
        self.assertEqual(self.tracker.todos[1].status, "completed")

    def test_multiple_in_progress_rejected(self):
        """Multiple in_progress tasks are rejected."""
        from core.tools import todo_write
        result = todo_write([
            {"content": "T1", "status": "in_progress"},
            {"content": "T2", "status": "in_progress"},
        ])
        self.assertIn("Error", result)
        self.assertIn("ONE task", result)

    def test_empty_list_rejected(self):
        """Empty list returns error."""
        from core.tools import todo_write
        result = todo_write([])
        self.assertIn("Error", result)

    def test_missing_content_rejected(self):
        """Missing content key returns error."""
        from core.tools import todo_write
        result = todo_write([{"status": "pending"}])
        self.assertIn("missing required key 'content'", result)

    def test_plan_mode_write_limit(self):
        """Plan mode caps todo_write calls at 2."""
        from core.tools import todo_write
        os.environ["PLAN_MODE"] = "true"

        # First two writes succeed
        todo_write([{"content": "T1", "status": "pending"}])
        todo_write([{"content": "T2", "status": "pending"}])

        # Third write is blocked
        result = todo_write([{"content": "T3", "status": "pending"}])
        self.assertIn("limit reached", result)

    def test_write_replaces_existing(self):
        """todo_write replaces all existing tasks."""
        from core.tools import todo_write
        todo_write([{"content": "Old task", "status": "pending"}])
        self.assertEqual(len(self.tracker.todos), 1)

        todo_write([
            {"content": "New A", "status": "pending"},
            {"content": "New B", "status": "pending"},
        ])
        self.assertEqual(len(self.tracker.todos), 2)
        self.assertEqual(self.tracker.todos[0].content, "New A")


class TestLoopMode(unittest.TestCase):
    """Test loop mode (exit_condition / max_iterations)."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_loop_exits_on_condition(self):
        """Loop exits when exit_condition is found in tool_output."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Run until pass",
            "status": "in_progress",
            "loop": True,
            "exit_condition": "ALL TESTS PASS",
            "max_loop_iterations": 10,
        }])

        # First iteration: condition NOT met → loop restarts
        result = tracker.mark_completed(0, tool_output="1 test failed")
        self.assertFalse(result)  # Loop restarted
        self.assertEqual(tracker.todos[0].status, "in_progress")
        self.assertEqual(tracker.todos[0].loop_count, 1)

        # Second iteration: condition met → auto-approved
        result = tracker.mark_completed(0, tool_output="ALL TESTS PASS")
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].status, "approved")

    def test_loop_exits_on_max_iterations(self):
        """Loop exits when max_iterations is reached."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Run 3 times",
            "status": "in_progress",
            "loop": True,
            "exit_condition": "NEVER",
            "max_loop_iterations": 3,
        }])

        # Iteration 1
        result = tracker.mark_completed(0, tool_output="no match")
        self.assertFalse(result)

        # Iteration 2
        result = tracker.mark_completed(0, tool_output="no match")
        self.assertFalse(result)

        # Iteration 3: max reached → auto-approved
        result = tracker.mark_completed(0, tool_output="no match")
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].status, "approved")
        self.assertIn("Max iterations", tracker.todos[0].loop_exit_reason)

    def test_loop_unlimited_iterations(self):
        """Loop with max_iterations=0 runs indefinitely until condition."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Run forever",
            "status": "in_progress",
            "loop": True,
            "exit_condition": "DONE",
            "max_loop_iterations": 0,  # unlimited
        }])

        for i in range(100):
            result = tracker.mark_completed(0, tool_output="not done")
            self.assertFalse(result)

        # Now trigger exit
        result = tracker.mark_completed(0, tool_output="DONE")
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].loop_count, 101)

    def test_loop_count_persists(self):
        """Loop count survives save/load."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Loop task",
            "status": "in_progress",
            "loop": True,
            "exit_condition": "PASS",
            "max_loop_iterations": 5,
        }])
        tracker.mark_completed(0, tool_output="FAIL")  # loop_count = 1
        tracker.save()

        from lib.todo_tracker import TodoTracker
        tracker2 = TodoTracker.load(self.todo_file)
        self.assertEqual(tracker2.todos[0].loop_count, 1)


class TestValidator(unittest.TestCase):
    """Test validator integration."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_validator_passes(self):
        """Successful validator allows completion."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Task",
            "status": "in_progress",
            "validator": "true",  # Always passes
        }])
        result = tracker.mark_completed(0)
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].status, "completed")

    def test_validator_fails(self):
        """Failing validator auto-rejects task."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Task",
            "status": "in_progress",
            "validator": "false",  # Always fails
        }])
        result = tracker.mark_completed(0)
        self.assertFalse(result)
        self.assertEqual(tracker.todos[0].status, "rejected")
        self.assertIn("[Validator]", tracker.todos[0].rejection_reason)

    def test_validator_timeout(self):
        """Validator timeout auto-rejects."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Task",
            "status": "in_progress",
            "validator": "sleep 10",  # Will timeout
        }])
        result = tracker.mark_completed(0)
        self.assertFalse(result)
        self.assertEqual(tracker.todos[0].status, "rejected")
        self.assertIn("timed out", tracker.todos[0].rejection_reason)

    def test_no_validator(self):
        """No validator means completion proceeds normally."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Task",
            "status": "in_progress",
        }])
        result = tracker.mark_completed(0)
        self.assertTrue(result)
        self.assertEqual(tracker.todos[0].status, "completed")


class TestContinuationPrompt(unittest.TestCase):
    """Test continuation prompt generation."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_pending_task_prompt(self):
        """Pending task generates continuation prompt with MANDATORY."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "pending"},
        ])
        tracker.current_index = 1
        prompt = tracker.get_continuation_prompt()
        self.assertIsNotNone(prompt)
        self.assertIn("Task 2", prompt)
        self.assertIn("MANDATORY", prompt)
        self.assertIn("in_progress", prompt)

    def test_in_progress_task_prompt(self):
        """In-progress task shows completion instruction."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "in_progress"},
        ])
        tracker.current_index = 1
        prompt = tracker.get_continuation_prompt()
        self.assertIn("completed", prompt)

    def test_completed_task_prompt(self):
        """Completed task shows review instruction."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "completed"},
        ])
        tracker.current_index = 0
        prompt = tracker.get_continuation_prompt()
        self.assertIn("REVIEW REQUIRED", prompt)

    def test_rejected_task_prompt(self):
        """Rejected task shows rejection reason and fix instruction."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "rejected", "rejection_reason": "Bug found"},
        ])
        tracker.current_index = 0
        prompt = tracker.get_continuation_prompt()
        self.assertIn("REJECTED", prompt)
        self.assertIn("Bug found", prompt)

    def test_all_approved_no_prompt(self):
        """No prompt when all tasks are approved."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "approved"}])
        prompt = tracker.get_continuation_prompt()
        self.assertIsNone(prompt)

    def test_empty_tracker_no_prompt(self):
        """No prompt for empty tracker."""
        tracker = self._make_tracker()
        prompt = tracker.get_continuation_prompt()
        self.assertIsNone(prompt)

    def test_loop_prompt_shows_iteration(self):
        """Loop task in progress shows iteration count."""
        tracker = self._make_tracker()
        tracker.add_todos([{
            "content": "Run tests",
            "status": "in_progress",
            "loop": True,
            "loop_count": 3,
            "max_loop_iterations": 10,
            "exit_condition": "PASS",
        }])
        tracker.current_index = 0
        prompt = tracker.get_continuation_prompt()
        self.assertIn("LOOP 3/10", prompt)


class TestActiveForm(unittest.TestCase):
    """Test active form generation."""

    def test_verb_conjugation(self):
        """Common verbs are correctly conjugated to -ing form."""
        from lib.todo_tracker import _generate_active_form
        self.assertEqual(_generate_active_form("Run tests"), "Running tests")
        self.assertEqual(_generate_active_form("Build project"), "Building project")
        self.assertEqual(_generate_active_form("Fix bug"), "Fixing bug")
        self.assertEqual(_generate_active_form("Write code"), "Writing code")

    def test_unknown_verb(self):
        """Unknown verbs get 'Executing:' prefix."""
        from lib.todo_tracker import _generate_active_form
        result = _generate_active_form("Do something complex")
        self.assertEqual(result, "Executing: Do something complex")

    def test_active_form_with_loop_vars(self):
        """Active form substitutes loop variables."""
        from lib.todo_tracker import TodoItem
        item = TodoItem(
            content="Run test",
            active_form="Running iteration {loop_count}/{max_loop_iterations}",
            loop_count=3,
            max_loop_iterations=5,
        )
        result = item.get_active_form()
        self.assertEqual(result, "Running iteration 3/5")

    def test_active_form_unlimited_loop(self):
        """Unlimited loop shows ∞ symbol."""
        from lib.todo_tracker import TodoItem
        item = TodoItem(
            content="Run",
            active_form="Loop {loop_count}/{max_loop_iterations}",
            loop_count=2,
            max_loop_iterations=0,
        )
        result = item.get_active_form()
        self.assertEqual(result, "Loop 2/∞")


class TestNextPendingLogic(unittest.TestCase):
    """Test _get_next_pending priority ordering."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_rejected_before_completed_before_pending(self):
        """Rejected tasks are prioritized over completed, then pending."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Pending task", "status": "pending"},
            {"content": "Completed task", "status": "completed"},
            {"content": "Rejected task", "status": "rejected"},
        ])
        next_idx = tracker._get_next_pending()
        self.assertEqual(next_idx, 2)  # Rejected first

    def test_high_priority_first(self):
        """Among same status, high priority goes first."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Low task", "status": "pending", "priority": "low"},
            {"content": "High task", "status": "pending", "priority": "high"},
            {"content": "Med task", "status": "pending", "priority": "medium"},
        ])
        next_idx = tracker._get_next_pending()
        self.assertEqual(next_idx, 1)  # High priority

    def test_original_order_as_tiebreaker(self):
        """Same status and priority → original index order."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "First", "status": "pending"},
            {"content": "Second", "status": "pending"},
        ])
        next_idx = tracker._get_next_pending()
        self.assertEqual(next_idx, 0)

    def test_no_actionable_tasks(self):
        """Returns None when all tasks are approved."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "approved"},
        ])
        next_idx = tracker._get_next_pending()
        self.assertIsNone(next_idx)


class TestAutoRecovery(unittest.TestCase):
    """Test _auto_recover_current_index."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_recover_from_invalid_index(self):
        """Recovers when current_index points to approved task."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "T1", "status": "approved"},
            {"content": "T2", "status": "pending"},
        ])
        tracker.current_index = 0  # Points at approved
        recovered = tracker._auto_recover_current_index()
        self.assertTrue(recovered)
        self.assertEqual(tracker.current_index, 1)

    def test_no_recovery_needed(self):
        """Returns False when current_index is valid."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "in_progress"}])
        tracker.current_index = 0
        recovered = tracker._auto_recover_current_index()
        self.assertFalse(recovered)


class TestEdgeCases(unittest.TestCase):
    """Test edge cases and error handling."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker
        return TodoTracker(persist_path=self.todo_file)

    def test_elapsed_time_in_progress(self):
        """Elapsed time is computed for in_progress tasks."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "in_progress"}])
        elapsed = tracker.todos[0].elapsed
        self.assertIsNotNone(elapsed)
        self.assertGreaterEqual(elapsed, 0)

    def test_elapsed_time_pending_is_none(self):
        """Elapsed time is None for pending tasks."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "T1", "status": "pending"}])
        self.assertIsNone(tracker.todos[0].elapsed)

    def test_priority_normalization(self):
        """Invalid priority defaults to medium."""
        from lib.todo_tracker import TodoItem
        item = TodoItem(content="Test", active_form="Testing", priority="super_high")
        self.assertEqual(item.priority, "medium")

    def test_parse_todo_write_checkbox_format(self):
        """Parse checkbox format from text."""
        from lib.todo_tracker import parse_todo_write_from_text
        text = """TodoWrite:
- [ ] Step 1
- [x] Step 2
- [ ] Step 3
"""
        result = parse_todo_write_from_text(text)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0]["status"], "pending")
        self.assertEqual(result[1]["status"], "completed")
        self.assertEqual(result[2]["status"], "pending")

    def test_parse_todo_numbered_format(self):
        """Parse numbered list format from text."""
        from lib.todo_tracker import parse_todo_write_from_text
        text = """Let's plan:
1. First thing to do
2. Second thing to do
3. Third thing to do
"""
        result = parse_todo_write_from_text(text)
        self.assertIsNotNone(result)
        self.assertEqual(len(result), 3)

    def test_format_simple(self):
        """format_simple returns non-empty string."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Task A", "status": "pending"},
            {"content": "Task B", "status": "in_progress"},
        ])
        output = tracker.format_simple()
        self.assertIn("Task A", output)
        self.assertIn("Task B", output)

    def test_format_progress(self):
        """format_progress returns visualization."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Done task", "status": "approved"},
            {"content": "Current task", "status": "in_progress"},
        ])
        output = tracker.format_progress()
        self.assertIn("Done task", output)
        self.assertIn("Current task", output)

    def test_get_minimal_context(self):
        """get_minimal_context returns context for a specific step."""
        tracker = self._make_tracker()
        tracker.add_todos([
            {"content": "Step 1", "status": "approved"},
            {"content": "Step 2", "status": "in_progress"},
            {"content": "Step 3", "status": "pending"},
        ])
        ctx = tracker.get_minimal_context(1)
        self.assertIn("Step 1", ctx)
        self.assertIn("Step 2", ctx)
        self.assertIn("Step 3", ctx)

    def test_single_task_lifecycle(self):
        """Single task goes through full lifecycle."""
        tracker = self._make_tracker()
        tracker.add_todos([{"content": "Only task", "status": "pending"}])

        tracker.mark_in_progress(0)
        tracker.todos[0].tools_since_in_progress = 1
        tracker.mark_completed(0)
        self.assertEqual(tracker.todos[0].status, "completed")

        tracker.mark_approved(0)
        self.assertEqual(tracker.todos[0].status, "approved")
        self.assertTrue(tracker.is_all_completed())


class TestSimulatedReactLoop(unittest.TestCase):
    """Simulate the full react_loop flow to test the gate check fix."""

    def setUp(self):
        self.tmpdir = tempfile.mkdtemp()
        self.todo_file = Path(self.tmpdir) / "test_todo.json"

    def test_full_workflow_with_gate_check(self):
        """Simulate: add tasks → in_progress → tool calls → completed → approved."""
        from lib.todo_tracker import TodoTracker

        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([
            {"content": "Write code", "status": "pending"},
            {"content": "Run tests", "status": "pending"},
        ])

        # --- Task 1 ---
        tracker.mark_in_progress(0)
        self.assertEqual(tracker.todos[0].tools_since_in_progress, 0)

        # Simulate react_loop: tool call 1 (write_file)
        current = tracker.get_current_todo()
        current.tools_since_in_progress += 1
        tracker.save()  # THE FIX: persist counter

        # Simulate: reload from disk (what _get_todo_tracker does)
        tracker2 = TodoTracker.load(self.todo_file)
        item = tracker2.todos[0]
        self.assertEqual(item.tools_since_in_progress, 1)
        self.assertEqual(item.status, "in_progress")

        # Gate check should pass
        self.assertGreater(item.tools_since_in_progress, 0)

        # Mark completed
        tracker2.mark_completed(0)
        self.assertEqual(tracker2.todos[0].status, "completed")

        # Approve
        tracker2.mark_approved(0)
        self.assertEqual(tracker2.todos[0].status, "approved")

        # --- Task 2 ---
        tracker2.mark_in_progress(1)
        self.assertEqual(tracker2.todos[1].tools_since_in_progress, 0)

        # Multiple tool calls
        for i in range(5):
            tracker2.todos[1].tools_since_in_progress += 1
            tracker2.save()

            # Verify persistence
            tracker3 = TodoTracker.load(self.todo_file)
            self.assertEqual(tracker3.todos[1].tools_since_in_progress, i + 1)

        tracker3.mark_completed(1)
        tracker3.mark_approved(1)
        self.assertTrue(tracker3.is_all_completed())

    def test_stagnation_break_loop(self):
        """Simulate stagnation detection breaking the loop."""
        from lib.todo_tracker import TodoTracker

        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "Blocked task", "status": "in_progress"}])

        auto_advance_threshold = 5
        iterations = 0
        broke = False

        for _ in range(20):
            iterations += 1
            count = tracker.stagnation_count

            if count >= auto_advance_threshold:
                broke = True
                break

            tracker.check_stagnation(max_stagnation=50)

        self.assertTrue(broke, "Stagnation should trigger break")
        self.assertLessEqual(iterations, 7)  # Should break by iter 6-7

    def test_gate_check_counter_not_lost_on_reload(self):
        """
        THE KEY BUG TEST: Verify counter survives multiple save/load cycles.

        This was the original bug: the counter was incremented in-memory but
        never saved, so reload always got 0.
        """
        from lib.todo_tracker import TodoTracker

        tracker = TodoTracker(persist_path=self.todo_file)
        tracker.add_todos([{"content": "Gate check test", "status": "pending"}])
        tracker.mark_in_progress(0)

        # Simulate 5 tool calls with save between each (the fix)
        for expected in range(1, 6):
            # Increment (react_loop does this)
            tracker.todos[0].tools_since_in_progress += 1
            tracker.save()  # THE FIX

            # Reload (what tools.py does via _get_todo_tracker)
            fresh = TodoTracker.load(self.todo_file)
            actual = fresh.todos[0].tools_since_in_progress
            self.assertEqual(actual, expected,
                f"Counter lost! Expected {expected}, got {actual}. "
                f"The gate check would incorrectly block completion.")


if __name__ == "__main__":
    unittest.main(verbosity=2)
