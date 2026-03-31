"""
TDD tests for core/text_utils.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import unittest

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'core'))

from text_utils import strip_thinking_tags, strip_metadata_tokens, estimate_tokens


class TestStripThinkingTags(unittest.TestCase):

    def test_removes_think_block(self):
        text = "<think>internal reasoning</think>Final answer."
        self.assertEqual(strip_thinking_tags(text), "Final answer.")

    def test_removes_multiline_think_block(self):
        text = "<think>\nline1\nline2\n</think>answer"
        self.assertNotIn("<think>", strip_thinking_tags(text))
        self.assertIn("answer", strip_thinking_tags(text))

    def test_removes_partial_open_tag(self):
        text = "hello <think> world"
        self.assertNotIn("<think>", strip_thinking_tags(text))

    def test_removes_partial_close_tag(self):
        text = "hello </think> world"
        self.assertNotIn("</think>", strip_thinking_tags(text))

    def test_no_tags_passthrough(self):
        text = "plain text with no tags"
        self.assertEqual(strip_thinking_tags(text), text)

    def test_multiple_think_blocks(self):
        text = "<think>a</think>mid<think>b</think>end"
        result = strip_thinking_tags(text)
        self.assertNotIn("<think>", result)
        self.assertIn("mid", result)
        self.assertIn("end", result)

    def test_empty_string(self):
        self.assertEqual(strip_thinking_tags(""), "")


class TestStripMetadataTokens(unittest.TestCase):

    def test_removes_final_pipe_token(self):
        text = "hello<|final<|something|>world"
        result = strip_metadata_tokens(text)
        self.assertNotIn("<|final", result)

    def test_removes_generic_pipe_token(self):
        text = "content<|end_of_text|>more"
        result = strip_metadata_tokens(text)
        self.assertNotIn("<|end_of_text|>", result)

    def test_removes_trailing_partial_token(self):
        # Partial token at end of string (stream cut)
        text = "content<|end_of"
        result = strip_metadata_tokens(text)
        self.assertNotIn("<|end_of", result)

    def test_no_tokens_passthrough(self):
        text = "plain response with no metadata"
        self.assertEqual(strip_metadata_tokens(text), text)

    def test_empty_string(self):
        self.assertEqual(strip_metadata_tokens(""), "")

    def test_multiple_tokens(self):
        text = "<|im_start|>hello<|im_end|>"
        result = strip_metadata_tokens(text)
        self.assertNotIn("<|im_start|>", result)
        self.assertNotIn("<|im_end|>", result)


class TestEstimateTokens(unittest.TestCase):

    def test_string_input(self):
        # 4 chars ≈ 1 token
        result = estimate_tokens("1234")
        self.assertEqual(result, 1)

    def test_string_input_longer(self):
        result = estimate_tokens("a" * 100)
        self.assertEqual(result, 25)

    def test_empty_string(self):
        self.assertEqual(estimate_tokens(""), 0)

    def test_messages_list(self):
        messages = [
            {"role": "user", "content": "a" * 40},
            {"role": "assistant", "content": "b" * 40},
        ]
        result = estimate_tokens(messages)
        self.assertEqual(result, 20)  # 80 chars // 4

    def test_messages_with_dict_content(self):
        messages = [
            {"role": "user", "content": [{"type": "text", "text": "a" * 40}]},
        ]
        result = estimate_tokens(messages)
        self.assertGreater(result, 0)

    def test_messages_empty_list(self):
        self.assertEqual(estimate_tokens([]), 0)


if __name__ == '__main__':
    unittest.main()
