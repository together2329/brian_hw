"""
Unit Tests for TodoTracker

Tests for Phase 2: Todo Tracking System
"""

import unittest
import sys
import os

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

from lib.todo_tracker import TodoTracker, TodoItem, parse_todo_write_from_text


class TestTodoItem(unittest.TestCase):
    """Test TodoItem dataclass"""

    def test_create_todo_item(self):
        """Test creating a TodoItem"""
        item = TodoItem(
            content="Run tests",
            active_form="Running tests",
            status="pending"
        )

        self.assertEqual(item.content, "Run tests")
        self.assertEqual(item.active_form, "Running tests")
        self.assertEqual(item.status, "pending")
        self.assertIsNotNone(item.created_at)


class TestTodoTracker(unittest.TestCase):
    """Test TodoTracker class"""

    def setUp(self):
        """Set up test fixtures"""
        self.tracker = TodoTracker()

    def test_add_todos(self):
        """Test adding todos from dict list"""
        todos = [
            {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"},
        ]

        self.tracker.add_todos(todos)

        self.assertEqual(len(self.tracker.todos), 2)
        self.assertEqual(self.tracker.todos[0].content, "Step 1")
        self.assertEqual(self.tracker.todos[1].content, "Step 2")

    def test_mark_in_progress(self):
        """Test marking a todo as in_progress"""
        todos = [
            {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"},
        ]
        self.tracker.add_todos(todos)

        self.tracker.mark_in_progress(0)

        self.assertEqual(self.tracker.todos[0].status, "in_progress")
        self.assertEqual(self.tracker.current_index, 0)

    def test_only_one_in_progress(self):
        """Test that only one todo can be in_progress at a time"""
        todos = [
            {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"},
        ]
        self.tracker.add_todos(todos)

        # Mark first as in_progress
        self.tracker.mark_in_progress(0)
        self.assertEqual(self.tracker.todos[0].status, "in_progress")

        # Mark second as in_progress (should clear first)
        self.tracker.mark_in_progress(1)
        self.assertEqual(self.tracker.todos[0].status, "pending")  # Cleared
        self.assertEqual(self.tracker.todos[1].status, "in_progress")
        self.assertEqual(self.tracker.current_index, 1)

    def test_mark_completed(self):
        """Test marking a todo as completed"""
        todos = [
            {"content": "Step 1", "status": "in_progress", "activeForm": "Doing Step 1"},
        ]
        self.tracker.add_todos(todos)

        self.tracker.mark_completed(0)

        self.assertEqual(self.tracker.todos[0].status, "completed")

    def test_auto_advance(self):
        """Test auto-advance to next pending todo"""
        todos = [
            {"content": "Step 1", "status": "in_progress", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "pending", "activeForm": "Doing Step 2"},
            {"content": "Step 3", "status": "pending", "activeForm": "Doing Step 3"},
        ]
        self.tracker.add_todos(todos)
        self.tracker.current_index = 0

        self.tracker.auto_advance()

        # First should be completed
        self.assertEqual(self.tracker.todos[0].status, "completed")
        # Second should be in_progress
        self.assertEqual(self.tracker.todos[1].status, "in_progress")
        self.assertEqual(self.tracker.current_index, 1)

    def test_format_progress(self):
        """Test progress formatting"""
        todos = [
            {"content": "Step 1", "status": "completed", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "in_progress", "activeForm": "Doing Step 2"},
            {"content": "Step 3", "status": "pending", "activeForm": "Doing Step 3"},
        ]
        self.tracker.add_todos(todos)
        self.tracker.current_index = 1

        progress = self.tracker.format_progress()

        # Check icons
        self.assertIn("✅", progress)  # Completed
        self.assertIn("▶️", progress)  # In progress
        self.assertIn("⏸️", progress)  # Pending
        # Check progress summary
        self.assertIn("Progress: 1/3", progress)

    def test_get_current_todo(self):
        """Test getting current in_progress todo"""
        todos = [
            {"content": "Step 1", "status": "pending", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "in_progress", "activeForm": "Doing Step 2"},
        ]
        self.tracker.add_todos(todos)
        self.tracker.current_index = 1

        current = self.tracker.get_current_todo()

        self.assertIsNotNone(current)
        self.assertEqual(current.content, "Step 2")

    def test_is_all_completed(self):
        """Test checking if all todos are completed"""
        todos = [
            {"content": "Step 1", "status": "completed", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "completed", "activeForm": "Doing Step 2"},
        ]
        self.tracker.add_todos(todos)

        self.assertTrue(self.tracker.is_all_completed())

        # Add pending
        self.tracker.todos.append(TodoItem(
            content="Step 3",
            active_form="Doing Step 3",
            status="pending"
        ))

        self.assertFalse(self.tracker.is_all_completed())

    def test_get_completion_ratio(self):
        """Test completion ratio calculation"""
        todos = [
            {"content": "Step 1", "status": "completed", "activeForm": "Doing Step 1"},
            {"content": "Step 2", "status": "in_progress", "activeForm": "Doing Step 2"},
            {"content": "Step 3", "status": "pending", "activeForm": "Doing Step 3"},
        ]
        self.tracker.add_todos(todos)

        ratio = self.tracker.get_completion_ratio()

        self.assertAlmostEqual(ratio, 1/3, places=2)


class TestParseTodoWrite(unittest.TestCase):
    """Test parse_todo_write_from_text function"""

    def test_parse_explicit_todowrite(self):
        """Test parsing explicit TodoWrite format"""
        text = """
Thought: I'll create a todo list.
TodoWrite:
- [ ] Explore codebase
- [ ] Design interface
- [ ] Implement code
"""

        todos = parse_todo_write_from_text(text)

        self.assertIsNotNone(todos)
        self.assertEqual(len(todos), 3)
        self.assertEqual(todos[0]["content"], "Explore codebase")
        self.assertEqual(todos[1]["content"], "Design interface")
        self.assertEqual(todos[2]["content"], "Implement code")
        # All should be pending
        self.assertEqual(todos[0]["status"], "pending")

    def test_parse_completed_todos(self):
        """Test parsing completed todos"""
        text = """
TodoWrite:
- [x] Completed step
- [ ] Pending step
"""

        todos = parse_todo_write_from_text(text)

        self.assertEqual(len(todos), 2)
        self.assertEqual(todos[0]["status"], "completed")
        self.assertEqual(todos[1]["status"], "pending")

    def test_parse_numbered_list(self):
        """Test parsing numbered list as todos"""
        text = """
I'll follow these steps:
1. Explore the codebase
2. Design the interface
3. Implement the code
"""

        todos = parse_todo_write_from_text(text)

        self.assertIsNotNone(todos)
        self.assertEqual(len(todos), 3)
        self.assertEqual(todos[0]["content"], "Explore the codebase")

    def test_parse_no_todos(self):
        """Test text without todos returns None"""
        text = """
Thought: This is just a thought.
Action: read_file(path="test.py")
"""

        todos = parse_todo_write_from_text(text)

        self.assertIsNone(todos)

    def test_active_form_generation(self):
        """Test active_form is generated correctly"""
        text = """
TodoWrite:
- [ ] Run tests
- [ ] Build project
"""

        todos = parse_todo_write_from_text(text)

        # Should generate "Running tests", "Building project"
        self.assertIn("Running", todos[0]["activeForm"])
        self.assertIn("Building", todos[1]["activeForm"])


if __name__ == '__main__':
    unittest.main()
