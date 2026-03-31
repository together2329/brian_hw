"""
TDD tests for core/observation_processor.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import unittest

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'src'))

from observation_processor import process_observation


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_config(**overrides):
    """Return a simple namespace that mimics config attributes."""
    import types
    cfg = types.SimpleNamespace(
        MAX_CONTEXT_CHARS=400_000,
        COMPRESSION_THRESHOLD=0.8,
        LARGE_FILE_PREVIEW_LINES=50,
        MAX_OBSERVATION_CHARS=50_000,
        ENABLE_COMPRESSION=False,  # Off by default in tests
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _estimate_tokens(msg):
    """Minimal token estimator: len(content) // 4."""
    content = msg.get("content", "")
    if isinstance(content, str):
        return len(content) // 4
    return 0


# ---------------------------------------------------------------------------
# Small observation — no truncation
# ---------------------------------------------------------------------------

class TestSmallObservation(unittest.TestCase):

    def setUp(self):
        self.cfg = _make_config()

    def test_appends_observation_message(self):
        messages = []
        result = process_observation(
            "hello world",
            messages,
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        self.assertEqual(len(result), 1)
        self.assertIn("hello world", result[0]["content"])

    def test_observation_role_is_user(self):
        result = process_observation(
            "data",
            [],
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        self.assertEqual(result[0]["role"], "user")

    def test_existing_messages_preserved(self):
        existing = [{"role": "assistant", "content": "previous"}]
        result = process_observation(
            "new obs",
            existing,
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0]["content"], "previous")


# ---------------------------------------------------------------------------
# Large observation — triggers truncation
# ---------------------------------------------------------------------------

class TestLargeObservation(unittest.TestCase):

    def setUp(self):
        # Very tight limit so even small obs triggers truncation
        self.cfg = _make_config(
            MAX_CONTEXT_CHARS=1_000,
            MAX_OBSERVATION_CHARS=500,
            LARGE_FILE_PREVIEW_LINES=3,
        )

    def test_large_obs_triggers_preview(self):
        # Build obs that's > 30% of limit_tokens (limit_tokens = 1000//4 = 250)
        # 30% of 250 = 75 tokens = 300 chars → obs > 300 chars triggers preview
        big_obs = "\n".join([f"line {i}: " + "x" * 20 for i in range(50)])
        result = process_observation(
            big_obs,
            [],
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        content = result[0]["content"]
        self.assertIn("File Preview", content)
        self.assertIn("BEGIN PREVIEW", content)

    def test_preview_contains_first_lines(self):
        lines = [f"line_{i}" for i in range(20)]
        big_obs = "\n".join(lines) + "\n" + "x" * 1000
        result = process_observation(
            big_obs,
            [],
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        content = result[0]["content"]
        self.assertIn("line_0", content)

    def test_returns_list(self):
        result = process_observation(
            "x" * 2000,
            [],
            cfg=self.cfg,
            estimate_tokens_fn=_estimate_tokens,
        )
        self.assertIsInstance(result, list)


# ---------------------------------------------------------------------------
# compress_fn callback
# ---------------------------------------------------------------------------

class TestCompressFnCallback(unittest.TestCase):

    def test_compress_fn_called_when_threshold_exceeded(self):
        cfg = _make_config(
            MAX_CONTEXT_CHARS=400,   # limit_tokens = 100
            COMPRESSION_THRESHOLD=0.5,
            ENABLE_COMPRESSION=True,
        )
        compress_called = []

        def mock_compress(messages, todo_tracker=None, force=False, quiet=False):
            compress_called.append(True)
            return messages  # no-op

        # Build messages that are already near the threshold
        big_messages = [{"role": "user", "content": "x" * 100}]
        big_obs = "y" * 100

        process_observation(
            big_obs,
            big_messages,
            cfg=cfg,
            estimate_tokens_fn=_estimate_tokens,
            compress_fn=mock_compress,
        )
        self.assertTrue(len(compress_called) > 0)

    def test_no_compress_when_disabled(self):
        cfg = _make_config(ENABLE_COMPRESSION=False)
        compress_called = []

        def mock_compress(messages, **kw):
            compress_called.append(True)
            return messages

        process_observation(
            "small obs",
            [],
            cfg=cfg,
            estimate_tokens_fn=_estimate_tokens,
            compress_fn=mock_compress,
        )
        self.assertEqual(compress_called, [])


if __name__ == '__main__':
    unittest.main()
