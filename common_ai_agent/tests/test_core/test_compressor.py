"""
TDD tests for core/compressor.py
Phase 5: extract compress_history, _compress_single, _compress_chunked from main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import types


def _make_cfg(**overrides):
    """Build a minimal config-like namespace."""
    defaults = dict(
        ENABLE_COMPRESSION=True,
        MAX_CONTEXT_TOKENS=100000,
        PREEMPTIVE_COMPRESSION_THRESHOLD=0.85,
        COMPRESSION_THRESHOLD=0.95,
        COMPRESSION_KEEP_RECENT=10,
        COMPRESSION_MODE="traditional",
        COMPRESSION_CHUNK_SIZE=20,
        ENABLE_TURN_PROTECTION=False,
        TURN_PROTECTION_COUNT=3,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _make_messages(n=20, role_cycle=("user", "assistant")):
    msgs = []
    for i in range(n):
        role = role_cycle[i % len(role_cycle)]
        msgs.append({"role": role, "content": f"Message {i}"})
    return msgs


def _mock_llm_call(messages, **kwargs):
    """Yield a single text chunk then stop."""
    yield "SUMMARY_TEXT"


class TestCompressSingle(unittest.TestCase):
    def setUp(self):
        from core.compressor import _compress_single
        self._fn = _compress_single

    def test_returns_system_message(self):
        msgs = _make_messages(5)
        result = self._fn(msgs, llm_call_fn=_mock_llm_call)
        self.assertEqual(result["role"], "system")

    def test_content_contains_summary_prefix(self):
        msgs = _make_messages(5)
        result = self._fn(msgs, llm_call_fn=_mock_llm_call)
        self.assertIn("[Previous Conversation Summary", result["content"])

    def test_content_contains_llm_output(self):
        msgs = _make_messages(5)
        result = self._fn(msgs, llm_call_fn=_mock_llm_call)
        self.assertIn("SUMMARY_TEXT", result["content"])

    def test_message_count_in_prefix(self):
        msgs = _make_messages(7)
        result = self._fn(msgs, llm_call_fn=_mock_llm_call)
        self.assertIn("7", result["content"])

    def test_custom_instruction_passed(self):
        captured = []
        def tracking_llm(messages, **kwargs):
            captured.extend(messages)
            yield "DONE"
        msgs = _make_messages(3)
        self._fn(msgs, llm_call_fn=tracking_llm, instruction="CUSTOM_INST")
        user_msg = next(m for m in captured if m["role"] == "user")
        self.assertIn("CUSTOM_INST", user_msg["content"])

    def test_llm_exception_returns_fallback(self):
        def failing_llm(messages, **kwargs):
            raise RuntimeError("LLM unavailable")
            yield
        msgs = _make_messages(3)
        result = self._fn(msgs, llm_call_fn=failing_llm)
        # Should not raise; return something dict-like
        self.assertIsInstance(result, dict)
        self.assertIn("role", result)

    def test_skips_reasoning_tuples(self):
        """Tuples ('reasoning', ...) must be filtered out of summary text."""
        def llm_with_reasoning(messages, **kwargs):
            yield ("reasoning", "internal thought")
            yield "ACTUAL_SUMMARY"
        msgs = _make_messages(3)
        result = self._fn(msgs, llm_call_fn=llm_with_reasoning)
        self.assertIn("ACTUAL_SUMMARY", result["content"])
        self.assertNotIn("internal thought", result["content"])


class TestCompressChunked(unittest.TestCase):
    def setUp(self):
        from core.compressor import _compress_chunked
        self._fn = _compress_chunked

    def test_returns_list(self):
        msgs = _make_messages(10)
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=5)
        result = self._fn(msgs, cfg=cfg, llm_call_fn=_mock_llm_call)
        self.assertIsInstance(result, list)

    def test_chunk_count_correct(self):
        msgs = _make_messages(10)
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=5)
        result = self._fn(msgs, cfg=cfg, llm_call_fn=_mock_llm_call)
        self.assertEqual(len(result), 2)  # 10 / 5 = 2 chunks

    def test_each_chunk_is_system_message(self):
        msgs = _make_messages(6)
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=3)
        result = self._fn(msgs, cfg=cfg, llm_call_fn=_mock_llm_call)
        for chunk_msg in result:
            self.assertEqual(chunk_msg["role"], "system")

    def test_chunk_summary_prefix(self):
        msgs = _make_messages(4)
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=2)
        result = self._fn(msgs, cfg=cfg, llm_call_fn=_mock_llm_call)
        self.assertIn("[Summary chunk", result[0]["content"])

    def test_llm_failure_falls_back_to_first_message(self):
        def failing_llm(messages, **kwargs):
            raise RuntimeError("fail")
            yield
        msgs = _make_messages(4)
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=2)
        result = self._fn(msgs, cfg=cfg, llm_call_fn=failing_llm)
        self.assertEqual(len(result), 2)


class TestCompressHistory(unittest.TestCase):
    def setUp(self):
        from core.compressor import compress_history
        self._fn = compress_history

    def _call(self, messages, **kwargs):
        defaults = dict(
            cfg=_make_cfg(),
            llm_call_fn=_mock_llm_call,
            estimate_tokens_fn=lambda m: 100,
            last_input_tokens=0,
        )
        defaults.update(kwargs)
        return self._fn(messages, **defaults)

    def test_disabled_compression_returns_original(self):
        msgs = _make_messages(50)
        result = self._call(msgs, cfg=_make_cfg(ENABLE_COMPRESSION=False))
        self.assertIs(result, msgs)

    def test_too_short_returns_original(self):
        msgs = _make_messages(3)
        # small token count → under threshold
        result = self._call(msgs, estimate_tokens_fn=lambda m: 1)
        self.assertIs(result, msgs)

    def test_force_compresses_even_short(self):
        msgs = _make_messages(30)
        result = self._call(msgs, force=True, estimate_tokens_fn=lambda m: 1)
        # history should be shorter
        self.assertLess(len(result), len(msgs))

    def test_dry_run_returns_original_unchanged(self):
        msgs = _make_messages(50)
        result = self._call(msgs, force=True, dry_run=True)
        self.assertIs(result, msgs)

    def test_system_messages_preserved(self):
        sys_msg = {"role": "system", "content": "System prompt"}
        msgs = [sys_msg] + _make_messages(30)
        result = self._call(msgs, force=True)
        self.assertEqual(result[0]["role"], "system")
        self.assertEqual(result[0]["content"], "System prompt")

    def test_important_messages_preserved(self):
        important = {"role": "user", "content": "do this !important"}
        msgs = _make_messages(30) + [important]
        result = self._call(msgs, force=True)
        contents = [m["content"] for m in result]
        self.assertTrue(any("do this" in c for c in contents))

    def test_chunked_mode_used_when_configured(self):
        cfg = _make_cfg(COMPRESSION_MODE="chunked", COMPRESSION_CHUNK_SIZE=5)
        msgs = _make_messages(30)
        result = self._call(msgs, cfg=cfg, force=True)
        # chunked produces multiple summary messages; result should still be list
        self.assertIsInstance(result, list)

    def test_on_compressed_callback_called(self):
        called = []
        msgs = _make_messages(30)
        self._call(msgs, force=True, on_compressed_fn=lambda: called.append(True))
        self.assertTrue(len(called) > 0)

    def test_todo_tracker_state_injected(self):
        todo_tracker = MagicMock()
        todo_tracker.todos = [MagicMock(status="in_progress", content="task1")]
        todo_tracker.is_all_processed.return_value = False
        todo_tracker.get_continuation_prompt.return_value = "Continue task1"
        todo_tracker._get_next_pending.return_value = 0

        msgs = _make_messages(30)
        result = self._call(msgs, force=True, todo_tracker=todo_tracker)
        # A system message with todo state should be in result
        sys_contents = [m["content"] for m in result if m["role"] == "system"]
        self.assertTrue(any("Todo Status" in c or "Ongoing Task" in c for c in sys_contents))

    def test_keep_recent_respected(self):
        msgs = _make_messages(20)
        result = self._call(msgs, force=True, keep_recent=5)
        # After compression: system(0) + summary(1) + recent(5) = 6 non-todo msgs max
        non_system = [m for m in result if m["role"] != "system"]
        self.assertLessEqual(len(non_system), 6)


if __name__ == "__main__":
    unittest.main()
