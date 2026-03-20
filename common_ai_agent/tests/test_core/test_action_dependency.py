"""
Unit Tests for ActionDependencyAnalyzer

Tests for Phase 1: Enhanced Parallel Execution
"""

import unittest
import sys
import os

# Add project root to path
_test_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_test_dir))
sys.path.insert(0, _project_root)

from core.action_dependency import (
    ActionDependencyAnalyzer,
    FileConflictDetector,
    FileAccess,
    ActionBatch
)


class TestActionDependencyAnalyzer(unittest.TestCase):
    """Test ActionDependencyAnalyzer class"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ActionDependencyAnalyzer()

    def test_parallel_reads(self):
        """Test: Multiple read actions should be in one parallel batch"""
        actions = [
            ("read_file", 'path="a.v"'),
            ("read_file", 'path="b.v"'),
            ("grep_file", 'pattern="clk", path="c.v"'),
        ]

        batches = self.analyzer.analyze(actions)

        # Should be 1 batch (all read-only)
        self.assertEqual(len(batches), 1)
        # Batch should be parallel
        self.assertTrue(batches[0].parallel)
        # Batch should contain all 3 actions
        self.assertEqual(len(batches[0].actions), 3)

    def test_write_barrier(self):
        """Test: Write action creates a barrier"""
        actions = [
            ("read_file", 'path="a.v"'),
            ("write_file", 'path="b.v", content="..."'),
            ("read_file", 'path="b.v"'),
        ]

        batches = self.analyzer.analyze(actions)

        # Should be 3 batches: [read], [write], [read]
        self.assertEqual(len(batches), 3)

        # Batch 0: read (parallel)
        self.assertTrue(batches[0].parallel)
        self.assertEqual(len(batches[0].actions), 1)
        self.assertEqual(batches[0].actions[0][1], "read_file")

        # Batch 1: write (sequential barrier)
        self.assertFalse(batches[1].parallel)
        self.assertEqual(len(batches[1].actions), 1)
        self.assertEqual(batches[1].actions[0][1], "write_file")

        # Batch 2: read (parallel)
        self.assertTrue(batches[2].parallel)
        self.assertEqual(len(batches[2].actions), 1)
        self.assertEqual(batches[2].actions[0][1], "read_file")

    def test_extract_file_access_read(self):
        """Test: Extract file access for read tools"""
        access = self.analyzer.extract_file_access("read_file", 'path="test.v"')

        self.assertIsNotNone(access)
        self.assertEqual(access.access_type, "read")
        self.assertEqual(access.file_path, "test.v")
        self.assertIsNone(access.glob_pattern)

    def test_extract_file_access_write(self):
        """Test: Extract file access for write tools"""
        access = self.analyzer.extract_file_access("write_file", 'path="output.v", content="..."')

        self.assertIsNotNone(access)
        self.assertEqual(access.access_type, "write")
        self.assertEqual(access.file_path, "output.v")

    def test_extract_file_access_glob(self):
        """Test: Detect glob patterns"""
        access = self.analyzer.extract_file_access("grep_file", 'pattern="test", path="*.v"')

        self.assertIsNotNone(access)
        self.assertIsNone(access.file_path)
        self.assertEqual(access.glob_pattern, "*.v")

    def test_multiple_writes_sequential(self):
        """Test: Multiple write actions should be sequential"""
        actions = [
            ("write_file", 'path="a.v", content="1"'),
            ("write_file", 'path="b.v", content="2"'),
        ]

        batches = self.analyzer.analyze(actions)

        # Should be 2 batches (each write is a barrier)
        self.assertEqual(len(batches), 2)
        # Both should be sequential
        self.assertFalse(batches[0].parallel)
        self.assertFalse(batches[1].parallel)

    def test_mixed_operations(self):
        """Test: Mixed read/write operations"""
        actions = [
            ("read_file", 'path="a.v"'),
            ("read_file", 'path="b.v"'),
            ("write_file", 'path="output.v", content="..."'),
            ("read_file", 'path="output.v"'),
            ("grep_file", 'pattern="module", path="*.v"'),
        ]

        batches = self.analyzer.analyze(actions)

        # Expected: [read, read] | [write] | [read, grep]
        self.assertEqual(len(batches), 3)

        # Batch 0: 2 reads (parallel)
        self.assertTrue(batches[0].parallel)
        self.assertEqual(len(batches[0].actions), 2)

        # Batch 1: 1 write (sequential)
        self.assertFalse(batches[1].parallel)
        self.assertEqual(len(batches[1].actions), 1)

        # Batch 2: 2 reads (parallel)
        self.assertTrue(batches[2].parallel)
        self.assertEqual(len(batches[2].actions), 2)


class TestFileConflictDetector(unittest.TestCase):
    """Test FileConflictDetector class"""

    def setUp(self):
        """Set up test fixtures"""
        self.analyzer = ActionDependencyAnalyzer()
        self.detector = FileConflictDetector()

    def test_no_conflict_different_files(self):
        """Test: Different files, no conflict"""
        actions = [
            (0, "write_file", 'path="a.v", content="1"'),
            (1, "write_file", 'path="b.v", content="2"'),
        ]

        warnings = self.detector.check_conflicts(actions, self.analyzer)

        # No conflicts
        self.assertEqual(len(warnings), 0)

    def test_conflict_same_file(self):
        """Test: Same file modified by multiple writes"""
        actions = [
            (0, "write_file", 'path="test.v", content="1"'),
            (1, "replace_in_file", 'path="test.v", old="a", new="b"'),
        ]

        warnings = self.detector.check_conflicts(actions, self.analyzer)

        # Should detect conflict
        self.assertEqual(len(warnings), 1)
        self.assertIn("test.v", warnings[0])
        self.assertIn("conflict", warnings[0].lower())

    def test_no_conflict_read_write(self):
        """Test: Read and write on same file is OK"""
        actions = [
            (0, "read_file", 'path="test.v"'),
            (1, "write_file", 'path="test.v", content="new"'),
        ]

        warnings = self.detector.check_conflicts(actions, self.analyzer)

        # No conflict (read + write is fine, only write + write conflicts)
        self.assertEqual(len(warnings), 0)


class TestFileAccess(unittest.TestCase):
    """Test FileAccess class"""

    def test_conflicts_with_both_write(self):
        """Test: Two writes to same file conflict"""
        access1 = FileAccess(access_type="write", file_path="test.v")
        access2 = FileAccess(access_type="write", file_path="test.v")

        self.assertTrue(access1.conflicts_with(access2))
        self.assertTrue(access2.conflicts_with(access1))

    def test_no_conflict_different_files(self):
        """Test: Writes to different files don't conflict"""
        access1 = FileAccess(access_type="write", file_path="a.v")
        access2 = FileAccess(access_type="write", file_path="b.v")

        self.assertFalse(access1.conflicts_with(access2))

    def test_no_conflict_read_write(self):
        """Test: Read and write don't conflict"""
        access1 = FileAccess(access_type="read", file_path="test.v")
        access2 = FileAccess(access_type="write", file_path="test.v")

        self.assertFalse(access1.conflicts_with(access2))
        self.assertFalse(access2.conflicts_with(access1))


if __name__ == '__main__':
    unittest.main()
