"""
Tests for Session Management System

Tests:
1. SessionStorage - CRUD operations
2. MessageWithParts - Message and part handling
3. SessionCompactor - History compression
4. SessionReverter - Revert functionality
5. SnapshotManager - File snapshots
"""

import os
import sys
import unittest
import tempfile
import shutil
from pathlib import Path

# Add paths
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
sys.path.insert(0, os.path.join(os.path.dirname(os.path.dirname(os.path.abspath(__file__))), 'core'))

from core.session_manager import (
    SessionStorage,
    SessionMetadata,
    MessageInfo,
    Part,
    MessageWithParts,
    TokenUsage,
    PartType,
    ToolStatus,
    MessageRole,
    SessionCompactor,
    SessionReverter,
    SnapshotManager,
    SessionManager,
    get_session_manager
)


class TestTokenUsage(unittest.TestCase):
    """Test TokenUsage dataclass"""

    def test_default_values(self):
        usage = TokenUsage()
        self.assertEqual(usage.input, 0)
        self.assertEqual(usage.output, 0)
        self.assertEqual(usage.total(), 0)

    def test_total(self):
        usage = TokenUsage(input=100, output=50, reasoning=25)
        self.assertEqual(usage.total(), 175)


class TestSessionMetadata(unittest.TestCase):
    """Test SessionMetadata"""

    def test_to_dict(self):
        session = SessionMetadata(
            id="test-123",
            project_id="proj-1",
            title="Test Session"
        )
        data = session.to_dict()

        self.assertEqual(data["id"], "test-123")
        self.assertEqual(data["project_id"], "proj-1")
        self.assertEqual(data["title"], "Test Session")

    def test_from_dict(self):
        data = {
            "id": "test-456",
            "project_id": "proj-2",
            "directory": str(Path.home()),
            "title": "Another Session"
        }
        session = SessionMetadata.from_dict(data)

        self.assertEqual(session.id, "test-456")
        self.assertEqual(session.project_id, "proj-2")
        self.assertEqual(session.directory, str(Path.home()))


class TestSessionStorage(unittest.TestCase):
    """Test SessionStorage"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SessionStorage(Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_create_session(self):
        session = self.storage.create_session(
            project_id="test-project",
            title="My Session"
        )

        self.assertIsNotNone(session.id)
        self.assertEqual(session.project_id, "test-project")
        self.assertEqual(session.title, "My Session")

    def test_get_session(self):
        session = self.storage.create_session(title="Test")
        retrieved = self.storage.get_session(session.id)

        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.id, session.id)
        self.assertEqual(retrieved.title, "Test")

    def test_get_nonexistent_session(self):
        result = self.storage.get_session("nonexistent")
        self.assertIsNone(result)

    def test_update_session(self):
        session = self.storage.create_session(title="Original")

        self.storage.update_session(
            session.id,
            lambda s: setattr(s, 'title', 'Updated')
        )

        retrieved = self.storage.get_session(session.id)
        self.assertEqual(retrieved.title, "Updated")

    def test_list_sessions(self):
        self.storage.create_session(project_id="proj-1", title="Session 1")
        self.storage.create_session(project_id="proj-1", title="Session 2")
        self.storage.create_session(project_id="proj-2", title="Session 3")

        all_sessions = self.storage.list_sessions()
        self.assertEqual(len(all_sessions), 3)

        proj1_sessions = self.storage.list_sessions(project_id="proj-1")
        self.assertEqual(len(proj1_sessions), 2)

    def test_delete_session(self):
        session = self.storage.create_session(title="To Delete")
        self.storage.delete_session(session.id)

        result = self.storage.get_session(session.id)
        self.assertIsNone(result)


class TestMessageOperations(unittest.TestCase):
    """Test message operations"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SessionStorage(Path(self.temp_dir))
        self.session = self.storage.create_session(title="Test")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_and_get_message(self):
        message = MessageInfo(
            id="msg-1",
            session_id=self.session.id,
            role=MessageRole.USER.value,
            agent="build"
        )
        self.storage.save_message(message)

        retrieved = self.storage.get_message(self.session.id, "msg-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.role, "user")
        self.assertEqual(retrieved.agent, "build")

    def test_list_messages(self):
        for i in range(3):
            msg = MessageInfo(
                id=f"msg-{i}",
                session_id=self.session.id,
                role=MessageRole.USER.value if i % 2 == 0 else MessageRole.ASSISTANT.value
            )
            self.storage.save_message(msg)

        messages = self.storage.list_messages(self.session.id)
        self.assertEqual(len(messages), 3)


class TestPartOperations(unittest.TestCase):
    """Test part operations"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SessionStorage(Path(self.temp_dir))
        self.session = self.storage.create_session(title="Test")
        self.message = MessageInfo(
            id="msg-1",
            session_id=self.session.id,
            role=MessageRole.ASSISTANT.value
        )
        self.storage.save_message(self.message)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_save_text_part(self):
        part = Part(
            id="part-1",
            message_id=self.message.id,
            session_id=self.session.id,
            type=PartType.TEXT.value,
            text="Hello, world!"
        )
        self.storage.save_part(part)

        retrieved = self.storage.get_part(self.message.id, "part-1")
        self.assertIsNotNone(retrieved)
        self.assertEqual(retrieved.type, "text")
        self.assertEqual(retrieved.text, "Hello, world!")

    def test_save_tool_part(self):
        part = Part(
            id="part-2",
            message_id=self.message.id,
            session_id=self.session.id,
            type=PartType.TOOL.value,
            tool_name="read_file",
            call_id="call-123",
            tool_status=ToolStatus.COMPLETED.value,
            tool_input={"path": "test.py"},
            tool_output="file content here"
        )
        self.storage.save_part(part)

        retrieved = self.storage.get_part(self.message.id, "part-2")
        self.assertEqual(retrieved.tool_name, "read_file")
        self.assertEqual(retrieved.tool_status, "completed")
        self.assertEqual(retrieved.tool_output, "file content here")

    def test_list_parts(self):
        for i in range(3):
            part = Part(
                id=f"part-{i}",
                message_id=self.message.id,
                session_id=self.session.id,
                type=PartType.TEXT.value,
                text=f"Part {i}"
            )
            self.storage.save_part(part)

        parts = self.storage.list_parts(self.message.id)
        self.assertEqual(len(parts), 3)


class TestSnapshotManager(unittest.TestCase):
    """Test SnapshotManager"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.work_dir = Path(self.temp_dir) / "work"
        self.work_dir.mkdir()
        self.snapshot_dir = Path(self.temp_dir) / "snapshots"
        self.manager = SnapshotManager(self.work_dir, self.snapshot_dir)

        # Create test files
        (self.work_dir / "test.txt").write_text("Hello")
        (self.work_dir / "code.py").write_text("print('hello')")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_track_creates_snapshot(self):
        files = ["test.txt", "code.py"]
        snapshot_hash = self.manager.track(files)

        self.assertIsNotNone(snapshot_hash)
        self.assertEqual(len(snapshot_hash), 16)

    def test_get_snapshot(self):
        files = ["test.txt"]
        snapshot_hash = self.manager.track(files)

        snapshot = self.manager.get_snapshot(snapshot_hash)
        self.assertIsNotNone(snapshot)
        self.assertIn("test.txt", snapshot["files"])

    def test_diff_detects_changes(self):
        # Create initial snapshot
        snapshot1 = self.manager.track(["test.txt"])

        # Modify file
        (self.work_dir / "test.txt").write_text("Modified")

        # Get diff
        diffs = self.manager.diff(snapshot1)

        self.assertEqual(len(diffs), 1)
        self.assertEqual(diffs[0]["file"], "test.txt")
        self.assertEqual(diffs[0]["action"], "modified")


class TestSessionCompactor(unittest.TestCase):
    """Test SessionCompactor"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SessionStorage(Path(self.temp_dir))
        self.compactor = SessionCompactor(self.storage)
        self.session = self.storage.create_session(title="Test")

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_estimate_tokens(self):
        text = "A" * 400  # 400 chars = 100 tokens
        tokens = self.compactor.estimate_tokens(text)
        self.assertEqual(tokens, 100)

    def test_is_overflow(self):
        # Under limit
        usage = TokenUsage(input=50000, output=5000)
        self.assertFalse(
            self.compactor.is_overflow(usage, context_limit=128000)
        )

        # Over limit
        usage = TokenUsage(input=120000, output=10000)
        self.assertTrue(
            self.compactor.is_overflow(usage, context_limit=128000)
        )


class TestSessionReverter(unittest.TestCase):
    """Test SessionReverter"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.storage = SessionStorage(Path(self.temp_dir))
        self.snapshot = SnapshotManager(
            Path(self.temp_dir) / "work",
            Path(self.temp_dir) / "snapshots"
        )
        self.reverter = SessionReverter(self.storage, self.snapshot)
        self.session = self.storage.create_session(title="Test")

        # Create test messages
        for i in range(5):
            msg = MessageInfo(
                id=f"msg-{i}",
                session_id=self.session.id,
                role=MessageRole.USER.value if i % 2 == 0 else MessageRole.ASSISTANT.value
            )
            self.storage.save_message(msg)

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_revert_to_message(self):
        result = self.reverter.revert_to_message(
            self.session.id,
            "msg-2"
        )
        self.assertTrue(result)

        session = self.storage.get_session(self.session.id)
        self.assertIsNotNone(session.revert)
        self.assertEqual(session.revert["message_id"], "msg-2")

    def test_cleanup_revert(self):
        self.reverter.revert_to_message(self.session.id, "msg-2")
        result = self.reverter.cleanup_revert(self.session.id)

        self.assertTrue(result)

        # Check messages after revert point were deleted
        messages = self.storage.list_messages(self.session.id)
        self.assertEqual(len(messages), 3)  # msg-0, msg-1, msg-2

    def test_cancel_revert(self):
        self.reverter.revert_to_message(self.session.id, "msg-2")
        result = self.reverter.cancel_revert(self.session.id)

        self.assertTrue(result)

        session = self.storage.get_session(self.session.id)
        self.assertIsNone(session.revert)


class TestSessionManager(unittest.TestCase):
    """Test SessionManager integration"""

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        # Reset singleton
        SessionManager._instance = None
        self.manager = SessionManager(Path(self.temp_dir))

    def tearDown(self):
        shutil.rmtree(self.temp_dir, ignore_errors=True)
        SessionManager._instance = None

    def test_create_and_get_session(self):
        session = self.manager.create_session(title="Integration Test")
        retrieved = self.manager.get_session(session.id)

        self.assertEqual(retrieved.title, "Integration Test")

    def test_add_message(self):
        session = self.manager.create_session(title="Test")
        message = self.manager.add_message(
            session.id,
            role="user",
            content="Hello!",
            agent="build"
        )

        messages = self.manager.get_messages(session.id)
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0].info.role, "user")
        self.assertEqual(len(messages[0].parts), 1)
        self.assertEqual(messages[0].parts[0].text, "Hello!")

    def test_add_tool_call(self):
        session = self.manager.create_session(title="Test")
        message = self.manager.add_message(
            session.id,
            role="assistant"
        )

        part = self.manager.add_tool_call(
            message.id,
            session.id,
            tool_name="read_file",
            call_id="call-1",
            tool_input={"path": "test.py"}
        )

        self.assertEqual(part.tool_name, "read_file")
        self.assertEqual(part.tool_status, "running")

    def test_current_session(self):
        session = self.manager.create_session(title="Current")
        self.manager.set_current_session(session.id)

        current = self.manager.current_session
        self.assertEqual(current.id, session.id)


if __name__ == "__main__":
    unittest.main()
