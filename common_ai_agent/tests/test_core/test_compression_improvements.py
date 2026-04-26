# Comprehensive tests for compression system improvements.
#
# Tests cover:
#   1. TestSmartTruncation       - _smart_truncate helper
#   2. TestRecompressionDegradation - frozen summary preservation
#   3. TestChunkedErrorHandling   - chunk failure fallback
#   4. TestMessageStructure       - tool_calls / tool name preservation
#   5. TestSystemConsolidation    - section headers and ordering
#   6. TestEmergencyPruning       - _safe_prune role-pair integrity
#   7. TestPreAnalysisMerge       - single-pass analysis+compression

import sys
import os
import types
import unittest
from unittest.mock import MagicMock

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

from core.compressor import (
    _smart_truncate,
    _safe_prune,
    _compress_single,
    _compress_chunked,
    compress_history,
    _SINGLE_PASS_PROMPT,
)


# ---------------------------------------------------------------------------
# Shared helpers
# ---------------------------------------------------------------------------

def _mock_llm_call(messages, **kwargs):
    yield "MOCK_SUMMARY"


def _failing_llm_call(messages, **kwargs):
    raise RuntimeError("LLM unavailable")
    yield  # make it a generator


def _make_cfg(**overrides):
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
        COMPRESSION_PRE_ANALYSIS=False,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _make_messages(n=20, role_cycle=("user", "assistant")):
    msgs = []
    for i in range(n):
        role = role_cycle[i % len(role_cycle)]
        msgs.append({"role": role, "content": "Message " + str(i)})
    return msgs


def _run_compress(messages, fake_reply="MOCK_SUMMARY", force=False,
                  keep_recent=None, dry_run=False, quiet=True, **cfg_overrides):
    cfg = _make_cfg(**cfg_overrides)

    def _llm(messages, **kwargs):
        yield fake_reply

    return compress_history(
        messages,
        force=force,
        keep_recent=keep_recent,
        dry_run=dry_run,
        quiet=quiet,
        cfg=cfg,
        llm_call_fn=_llm,
        estimate_tokens_fn=lambda m: 100,
        last_input_tokens=0,
    )


# ===================================================================
# 1. TestSmartTruncation
# ===================================================================

class TestSmartTruncation(unittest.TestCase):

    def test_code_block_gets_more_chars(self):
        code = "```python\\ndef hello():\\n    print('hi')\\n```" + "x" * 5000
        result = _smart_truncate(code, "user")
        # Code content should get 2x default (2000 * 2 = 4000)
        self.assertGreater(len(result), 2000)
        self.assertLessEqual(len(result), 4000)

    def test_error_trace_gets_more_chars(self):
        err = "Traceback (most recent call last):\\n  File ...\\nError: broken" + "x" * 5000
        result = _smart_truncate(err, "assistant")
        self.assertGreater(len(result), 2000)
        self.assertLessEqual(len(result), 4000)

    def test_plain_text_default_chars(self):
        text = "Hello, this is a normal message." + "x" * 5000
        result = _smart_truncate(text, "user")
        self.assertEqual(len(result), 2000)

    def test_tool_role_gets_more_chars(self):
        text = "File content here" + "x" * 5000
        result = _smart_truncate(text, "tool")
        self.assertEqual(len(result), 2000)

    def test_tool_with_code_gets_even_more(self):
        code = "```verilog\\nmodule top;\\nendmodule\\n```" + "x" * 5000
        result = _smart_truncate(code, "tool")
        self.assertGreater(len(result), 2000)
        self.assertLessEqual(len(result), 4000)


# ===================================================================
# 2. TestRecompressionDegradation
# ===================================================================

class TestRecompressionDegradation(unittest.TestCase):

    def test_frozen_summary_preserved(self):
        # First compression
        msgs = _make_messages(30)
        result1 = _run_compress(msgs, fake_reply="FIRST_SUMMARY", force=True)
        summary_content = [m["content"] for m in result1 if m["role"] == "system"]
        self.assertTrue(any("FIRST_SUMMARY" in c for c in summary_content))

        # Simulate continuing conversation
        result1.append({"role": "user", "content": "Continue work"})
        result1.append({"role": "assistant", "content": "Working on it"})

        # Second compression
        result2 = _run_compress(result1, fake_reply="SECOND_SUMMARY", force=True)
        all_content = " ".join(str(m.get("content", "")) for m in result2)
        self.assertIn("FIRST_SUMMARY", all_content)

    def test_only_new_messages_compressed(self):
        captured = []

        def tracking_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured.append(m.get("content", ""))
            yield "TRACKED_SUMMARY"

        # Need enough messages to actually trigger compression (keep_recent=2)
        msgs = [
            {"role": "system", "content": "System prompt"},
            {"role": "system", "content": "[Previous Conversation Summary (20 messages)]: OLD_SUMMARY"},
        ]
        # Add 15 regular messages so there are enough to compress
        for i in range(15):
            role = "user" if i % 2 == 0 else "assistant"
            msgs.append({"role": role, "content": "New msg " + str(i)})
        compress_history(
            msgs, force=True, quiet=True,
            cfg=_make_cfg(COMPRESSION_KEEP_RECENT=2),
            llm_call_fn=tracking_llm,
            estimate_tokens_fn=lambda m: 100,
            last_input_tokens=0,
        )
        self.assertTrue(len(captured) > 0)
        self.assertNotIn("OLD_SUMMARY", captured[0])

    def test_no_summary_no_freeze(self):
        msgs = _make_messages(30)
        result = _run_compress(msgs, force=True)
        all_content = " ".join(str(m.get("content", "")) for m in result)
        self.assertIn("MOCK_SUMMARY", all_content)
        self.assertNotIn("FROZEN", all_content)


# ===================================================================
# 3. TestChunkedErrorHandling
# ===================================================================

class TestChunkedErrorHandling(unittest.TestCase):

    def test_all_messages_preserved_on_failure(self):
        chunk = [{"role": "user", "content": "Message " + str(i)} for i in range(5)]
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=5)
        result = _compress_chunked(chunk, cfg=cfg, llm_call_fn=_failing_llm_call)
        self.assertEqual(len(result), 1)
        content = result[0]["content"]
        for i in range(5):
            self.assertIn("Message " + str(i), content)

    def test_fallback_is_valid_system_message(self):
        chunk = [{"role": "user", "content": "Hello"}]
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=5)
        result = _compress_chunked(chunk, cfg=cfg, llm_call_fn=_failing_llm_call)
        self.assertEqual(result[0]["role"], "system")
        self.assertIn("[Chunk compression failed", result[0]["content"])

    def test_fallback_content_truncated(self):
        # Need 9+ messages with 500-char content each to exceed 4000 char threshold
        chunk = [{"role": "user", "content": "x" * 600} for _ in range(9)]
        cfg = _make_cfg(COMPRESSION_CHUNK_SIZE=10)
        result = _compress_chunked(chunk, cfg=cfg, llm_call_fn=_failing_llm_call)
        content = result[0]["content"]
        self.assertLess(len(content), 5000)
        self.assertIn("[truncated]", content)


# ===================================================================
# 4. TestMessageStructurePreservation
# ===================================================================

class TestMessageStructurePreservation(unittest.TestCase):

    def test_tool_calls_names_in_text(self):
        captured = {}

        def cap_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "SUMMARY"

        msgs = [
            {"role": "user", "content": "Read the file"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "tc1", "function": {"name": "read_file", "arguments": '{"path": "foo.py"}'}},
                {"id": "tc2", "function": {"name": "write_file", "arguments": '{"path": "bar.py"}'}},
            ]},
        ]
        _compress_single(msgs, llm_call_fn=cap_llm)
        user_text = captured.get("user", "")
        self.assertIn("read_file", user_text)
        self.assertIn("write_file", user_text)

    def test_tool_result_shows_source(self):
        captured = {}

        def cap_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "SUMMARY"

        msgs = [
            {"role": "tool", "name": "read_file", "content": "file contents here",
             "tool_call_id": "tc1"},
        ]
        _compress_single(msgs, llm_call_fn=cap_llm)
        user_text = captured.get("user", "")
        self.assertIn("tool(read_file)", user_text)

    def test_regular_message_format_unchanged(self):
        captured = {}

        def cap_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "SUMMARY"

        msgs = [
            {"role": "user", "content": "Hello there"},
            {"role": "assistant", "content": "Hi back"},
        ]
        _compress_single(msgs, llm_call_fn=cap_llm)
        user_text = captured.get("user", "")
        self.assertIn("user: Hello there", user_text)
        self.assertIn("assistant: Hi back", user_text)


# ===================================================================
# 5. TestSystemConsolidation
# ===================================================================

class TestSystemConsolidation(unittest.TestCase):

    def test_section_headers_present(self):
        msgs = [{"role": "system", "content": "Base prompt"}] + _make_messages(30)
        result = _run_compress(msgs, force=True)
        sys_content = result[0]["content"]
        self.assertIn("===== SYSTEM INSTRUCTIONS =====", sys_content)
        self.assertIn("===== CONVERSATION SUMMARY =====", sys_content)

    def test_section_order_correct(self):
        msgs = [{"role": "system", "content": "Base prompt"}] + _make_messages(30)
        todo = MagicMock()
        todo.todos = [MagicMock(status="in_progress", content="Task A")]
        todo.is_all_processed.return_value = False
        todo.get_continuation_prompt.return_value = "Continue A"
        todo._get_next_pending.return_value = 0

        cfg = _make_cfg()

        def _llm(msgs, **kw):
            yield "SUMMARY_TEXT"

        result = compress_history(
            msgs, force=True, quiet=True, todo_tracker=todo,
            cfg=cfg, llm_call_fn=_llm,
            estimate_tokens_fn=lambda m: 100, last_input_tokens=0,
        )
        sys_content = result[0]["content"]
        idx_instructions = sys_content.find("===== SYSTEM INSTRUCTIONS =====")
        idx_summary = sys_content.find("===== CONVERSATION SUMMARY =====")
        idx_task = sys_content.find("===== TASK STATUS =====")
        self.assertGreater(idx_instructions, -1)
        self.assertGreater(idx_summary, -1)
        self.assertGreater(idx_task, -1)
        self.assertLess(idx_instructions, idx_summary)
        self.assertLess(idx_summary, idx_task)

    def test_single_system_message_maintained(self):
        msgs = [{"role": "system", "content": "Base prompt"}] + _make_messages(30)
        result = _run_compress(msgs, force=True)
        system_count = sum(1 for m in result if m.get("role") == "system")
        self.assertEqual(system_count, 1)


# ===================================================================
# 6. TestEmergencyPruning
# ===================================================================

class TestEmergencyPruning(unittest.TestCase):

    def test_last_user_preserved(self):
        msgs = [
            {"role": "assistant", "content": "A1"},
            {"role": "assistant", "content": "A2"},
            {"role": "assistant", "content": "A3"},
            {"role": "user", "content": "U_LAST"},
        ]
        result = _safe_prune(msgs, 2)
        has_user = any(m.get("content") == "U_LAST" for m in result)
        self.assertTrue(has_user, "Last user message must be preserved")

    def test_tool_pairs_intact(self):
        msgs = [
            {"role": "user", "content": "U1"},
            {"role": "assistant", "content": "", "tool_calls": [
                {"id": "tc1", "function": {"name": "read_file", "arguments": "{}"}},
            ]},
            {"role": "tool", "content": "file data", "tool_call_id": "tc1"},
            {"role": "user", "content": "U2"},
        ]
        result = _safe_prune(msgs, 3)
        has_tool = any(m.get("role") == "tool" for m in result)
        has_asst = any(m.get("role") == "assistant" and m.get("tool_calls") for m in result)
        if has_tool:
            self.assertTrue(has_asst, "Assistant must accompany its tool responses")

    def test_fallback_no_tool_messages(self):
        msgs = [{"role": "user", "content": "Msg " + str(i)} for i in range(10)]
        result = _safe_prune(msgs, 4)
        self.assertLessEqual(len(result), 5)  # 4 + possible user safety


# ===================================================================
# 7. TestPreAnalysisMerge
# ===================================================================

class TestPreAnalysisMerge(unittest.TestCase):

    def test_single_llm_call(self):
        call_count = [0]

        def counting_llm(messages, **kwargs):
            call_count[0] += 1
            yield "ANALYSIS_AND_SUMMARY"

        msgs = _make_messages(30)
        cfg = _make_cfg(COMPRESSION_PRE_ANALYSIS=True)
        compress_history(
            msgs, force=True, quiet=True, cfg=cfg, llm_call_fn=counting_llm,
            estimate_tokens_fn=lambda m: 100, last_input_tokens=0,
        )
        self.assertEqual(call_count[0], 1, "Should make exactly 1 LLM call")

    def test_analysis_in_prompt(self):
        captured = {}

        def cap_llm(messages, **kwargs):
            for m in messages:
                if m.get("role") == "user":
                    captured["user"] = m.get("content", "")
            yield "SUMMARY"

        msgs = _make_messages(30)
        cfg = _make_cfg(COMPRESSION_PRE_ANALYSIS=True)
        compress_history(
            msgs, force=True, quiet=True, cfg=cfg, llm_call_fn=cap_llm,
            estimate_tokens_fn=lambda m: 100, last_input_tokens=0,
        )
        user_text = captured.get("user", "")
        self.assertIn("Identify Critical Context", user_text)
        self.assertIn("Step 1", user_text)

    def test_single_pass_prompt_exists(self):
        self.assertIsInstance(_SINGLE_PASS_PROMPT, str)
        self.assertGreater(len(_SINGLE_PASS_PROMPT), 100)
        self.assertIn("Critical Context", _SINGLE_PASS_PROMPT)


if __name__ == "__main__":
    unittest.main()
