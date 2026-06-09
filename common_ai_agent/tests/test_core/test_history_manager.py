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

from history_manager import (
    load_conversation_history,
    sanitize_messages_for_history,
    save_conversation_history,
)


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

    def test_sanitizes_inline_prompt_images_without_mutating_input(self):
        cfg = _make_cfg(path=self.hist_path)
        messages = [
            {
                "role": "user",
                "content": [
                    {"type": "text", "text": "look at this"},
                    {
                        "type": "input_image",
                        "image_url": "data:image/png;base64,aGVsbG8=",
                        "detail": "high",
                    },
                ],
            }
        ]

        save_conversation_history(messages, cfg=cfg)

        with open(self.hist_path, encoding="utf-8") as f:
            active = json.load(f)
        with open(os.path.join(self.tmp_dir, "full_conversation.json"), encoding="utf-8") as f:
            full = json.load(f)
        active_text = json.dumps(active, ensure_ascii=False)
        full_text = json.dumps(full, ensure_ascii=False)

        self.assertNotIn("data:image", active_text)
        self.assertNotIn("base64", active_text)
        self.assertNotIn("data:image", full_text)
        self.assertNotIn("base64", full_text)
        self.assertEqual(
            active[0]["content"][1],
            {
                "type": "text",
                "text": "[Image omitted from saved conversation history] detail=high",
            },
        )
        self.assertIn("data:image/png;base64,aGVsbG8=", messages[0]["content"][1]["image_url"])

    def test_sanitizes_legacy_inline_image_strings(self):
        messages = [{"role": "user", "content": "before data:image/png;base64,aGVsbG8= after"}]

        sanitized = sanitize_messages_for_history(messages)

        self.assertEqual(
            sanitized,
            [{"role": "user", "content": "before [Image omitted from saved conversation history] after"}],
        )
        self.assertIn("data:image/png;base64,aGVsbG8=", messages[0]["content"])


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
