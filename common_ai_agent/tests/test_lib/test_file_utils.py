"""
TDD tests for lib/file_utils.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import json
import tempfile
import shutil
import unittest
from pathlib import Path

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'lib'))

from file_utils import read_json_file, atomic_write_json


class TestReadJsonFile(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_reads_valid_json(self):
        path = Path(self.tmp_dir) / "data.json"
        path.write_text(json.dumps({"key": "value"}), encoding="utf-8")
        result = read_json_file(path)
        self.assertEqual(result, {"key": "value"})

    def test_returns_default_on_missing_file(self):
        path = Path(self.tmp_dir) / "nonexistent.json"
        result = read_json_file(path)
        self.assertEqual(result, {})

    def test_custom_default_on_missing_file(self):
        path = Path(self.tmp_dir) / "nonexistent.json"
        result = read_json_file(path, default={"a": 1})
        self.assertEqual(result, {"a": 1})

    def test_returns_default_on_invalid_json(self):
        path = Path(self.tmp_dir) / "bad.json"
        path.write_text("not valid json{{", encoding="utf-8")
        result = read_json_file(path)
        self.assertEqual(result, {})

    def test_returns_default_if_root_is_not_dict(self):
        # Root is a list, not a dict
        path = Path(self.tmp_dir) / "list.json"
        path.write_text(json.dumps([1, 2, 3]), encoding="utf-8")
        result = read_json_file(path)
        self.assertEqual(result, {})

    def test_nested_dict_preserved(self):
        data = {"a": {"b": [1, 2, 3]}, "c": True}
        path = Path(self.tmp_dir) / "nested.json"
        path.write_text(json.dumps(data), encoding="utf-8")
        result = read_json_file(path)
        self.assertEqual(result, data)


class TestAtomicWriteJson(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_writes_and_reads_back(self):
        path = Path(self.tmp_dir) / "output.json"
        data = {"hello": "world", "num": 42}
        atomic_write_json(path, data)
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result, data)

    def test_creates_parent_dirs(self):
        path = Path(self.tmp_dir) / "subdir" / "deep" / "output.json"
        atomic_write_json(path, {"x": 1})
        self.assertTrue(path.exists())

    def test_overwrites_existing_file(self):
        path = Path(self.tmp_dir) / "overwrite.json"
        atomic_write_json(path, {"v": 1})
        atomic_write_json(path, {"v": 2})
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["v"], 2)

    def test_no_temp_file_left_behind(self):
        path = Path(self.tmp_dir) / "clean.json"
        atomic_write_json(path, {"ok": True})
        # Only the target file should exist
        files = list(Path(self.tmp_dir).iterdir())
        self.assertEqual(len(files), 1)
        self.assertEqual(files[0].name, "clean.json")

    def test_unicode_preserved(self):
        path = Path(self.tmp_dir) / "unicode.json"
        data = {"msg": "한국어 테스트 🎉"}
        atomic_write_json(path, data)
        result = json.loads(path.read_text(encoding="utf-8"))
        self.assertEqual(result["msg"], data["msg"])


if __name__ == '__main__':
    unittest.main()
