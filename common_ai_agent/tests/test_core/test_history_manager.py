"""
TDD tests for core/history_manager.py
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
sys.path.insert(0, os.path.join(_project_root, 'core'))

from history_manager import save_conversation_history, load_conversation_history


def _make_cfg(save=True, path=None):
    import types
    return types.SimpleNamespace(
        SAVE_HISTORY=save,
        HISTORY_FILE=path or "/tmp/test_history.json",
    )


class TestSaveConversationHistory(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.hist_path = os.path.join(self.tmp_dir, "history.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_saves_messages_to_file(self):
        cfg = _make_cfg(path=self.hist_path)
        messages = [{"role": "user", "content": "hello"}]
        save_conversation_history(messages, cfg=cfg)
        self.assertTrue(os.path.exists(self.hist_path))
        with open(self.hist_path) as f:
            loaded = json.load(f)
        self.assertEqual(loaded, messages)

    def test_skips_when_save_history_false(self):
        cfg = _make_cfg(save=False, path=self.hist_path)
        save_conversation_history([{"role": "user", "content": "x"}], cfg=cfg)
        self.assertFalse(os.path.exists(self.hist_path))

    def test_saves_unicode(self):
        cfg = _make_cfg(path=self.hist_path)
        messages = [{"role": "user", "content": "한국어 테스트 🎉"}]
        save_conversation_history(messages, cfg=cfg)
        with open(self.hist_path, encoding="utf-8") as f:
            loaded = json.load(f)
        self.assertEqual(loaded[0]["content"], "한국어 테스트 🎉")

    def test_no_crash_on_permission_error(self):
        cfg = _make_cfg(path="/nonexistent/path/history.json")
        # Should not raise — just print error
        save_conversation_history([{"role": "user", "content": "x"}], cfg=cfg)


class TestLoadConversationHistory(unittest.TestCase):

    def setUp(self):
        self.tmp_dir = tempfile.mkdtemp()
        self.hist_path = os.path.join(self.tmp_dir, "history.json")

    def tearDown(self):
        shutil.rmtree(self.tmp_dir)

    def test_loads_existing_file(self):
        messages = [{"role": "user", "content": "hello"}]
        with open(self.hist_path, "w") as f:
            json.dump(messages, f)
        cfg = _make_cfg(path=self.hist_path)
        result = load_conversation_history(cfg=cfg)
        self.assertEqual(result, messages)

    def test_returns_none_when_file_missing(self):
        cfg = _make_cfg(path=self.hist_path)
        result = load_conversation_history(cfg=cfg)
        self.assertIsNone(result)

    def test_returns_none_when_disabled(self):
        cfg = _make_cfg(save=False, path=self.hist_path)
        result = load_conversation_history(cfg=cfg)
        self.assertIsNone(result)

    def test_returns_none_on_invalid_json(self):
        with open(self.hist_path, "w") as f:
            f.write("not valid json")
        cfg = _make_cfg(path=self.hist_path)
        result = load_conversation_history(cfg=cfg)
        self.assertIsNone(result)


if __name__ == '__main__':
    unittest.main()
