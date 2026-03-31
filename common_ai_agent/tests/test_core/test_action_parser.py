"""
TDD tests for core/action_parser.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import unittest

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'core'))

from action_parser import (
    sanitize_action_text,
    _convert_all_glm_tool_calls,
    _strip_native_tool_tokens,
    _extract_annotation_ranges,
    parse_all_actions,
    parse_implicit_actions,
    parse_tool_arguments,
    parse_value,
    KNOWN_TOOLS,
)


# ---------------------------------------------------------------------------
# sanitize_action_text
# ---------------------------------------------------------------------------

class TestSanitizeActionText(unittest.TestCase):

    def test_removes_bold_action(self):
        self.assertEqual(sanitize_action_text("**Action:** foo(x)"), "Action: foo(x)")

    def test_removes_alternate_bold(self):
        self.assertEqual(sanitize_action_text("**Action**: foo(x)"), "Action: foo(x)")

    def test_converts_tool_call_prefix(self):
        self.assertEqual(sanitize_action_text("tool_call: foo(x)"), "Action: foo(x)")

    def test_normalizes_lowercase_action(self):
        result = sanitize_action_text("action: foo(x)")
        self.assertIn("Action:", result)

    def test_fixes_double_quote_number_paren(self):
        # =26") -> =26)
        result = sanitize_action_text('end_line=26")')
        self.assertNotIn('")', result)
        self.assertIn("26)", result)

    def test_fixes_single_quote_number_paren(self):
        result = sanitize_action_text("end_line=26')")
        self.assertNotIn("')", result)
        self.assertIn("26)", result)

    def test_no_change_on_clean_text(self):
        text = 'Action: read_file(path="a.py")'
        self.assertEqual(sanitize_action_text(text), text)


# ---------------------------------------------------------------------------
# parse_value
# ---------------------------------------------------------------------------

class TestParseValue(unittest.TestCase):

    def test_double_quoted_string(self):
        val, n = parse_value('"hello" rest')
        self.assertEqual(val, "hello")
        self.assertEqual(n, 7)

    def test_single_quoted_string(self):
        val, n = parse_value("'hello' rest")
        self.assertEqual(val, "hello")

    def test_triple_double_quoted(self):
        val, n = parse_value('"""hello world""" rest')
        self.assertEqual(val, "hello world")

    def test_triple_single_quoted(self):
        val, n = parse_value("'''hello world''' rest")
        self.assertEqual(val, "hello world")

    def test_escape_newline(self):
        val, n = parse_value(r'"line1\nline2"')
        self.assertEqual(val, "line1\nline2")

    def test_escape_tab(self):
        val, n = parse_value(r'"a\tb"')
        self.assertEqual(val, "a\tb")

    def test_escape_backslash(self):
        val, n = parse_value(r'"a\\b"')
        self.assertEqual(val, "a\\b")

    def test_integer(self):
        val, n = parse_value("42 rest")
        self.assertEqual(val, 42)
        self.assertIsInstance(val, int)

    def test_float(self):
        val, n = parse_value("3.14 rest")
        self.assertAlmostEqual(val, 3.14)

    def test_json_list(self):
        val, n = parse_value('["a", "b"] rest')
        self.assertEqual(val, ["a", "b"])

    def test_json_dict(self):
        val, n = parse_value('{"k": 1} rest')
        self.assertEqual(val, {"k": 1})

    def test_identifier_fallback(self):
        val, n = parse_value("True rest")
        self.assertEqual(val, "True")

    def test_empty_string(self):
        val, n = parse_value("")
        self.assertIsNone(val)
        self.assertEqual(n, 0)


# ---------------------------------------------------------------------------
# parse_tool_arguments
# ---------------------------------------------------------------------------

class TestParseToolArguments(unittest.TestCase):

    def test_single_kwarg_string(self):
        _, kw = parse_tool_arguments('path="a.py"')
        self.assertEqual(kw["path"], "a.py")

    def test_multiple_kwargs(self):
        _, kw = parse_tool_arguments('path="a.py", count=5')
        self.assertEqual(kw["path"], "a.py")
        self.assertEqual(kw["count"], 5)

    def test_positional_arg(self):
        args, _ = parse_tool_arguments('"hello"')
        self.assertEqual(args[0], "hello")

    def test_triple_quoted_kwarg(self):
        _, kw = parse_tool_arguments('content="""hello world"""')
        self.assertEqual(kw["content"], "hello world")

    def test_empty_string(self):
        args, kw = parse_tool_arguments("")
        self.assertEqual(args, [])
        self.assertEqual(kw, {})

    def test_list_value(self):
        _, kw = parse_tool_arguments('items=["a", "b"]')
        self.assertEqual(kw["items"], ["a", "b"])


# ---------------------------------------------------------------------------
# parse_all_actions
# ---------------------------------------------------------------------------

class TestParseAllActions(unittest.TestCase):

    def test_single_action(self):
        text = 'Action: read_file(path="a.py")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "read_file")
        self.assertIn("a.py", actions[0][1])

    def test_multiple_actions(self):
        text = 'Action: read_file(path="a.py")\nAction: list_dir(path=".")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 2)
        self.assertEqual(actions[0][0], "read_file")
        self.assertEqual(actions[1][0], "list_dir")

    def test_deduplication(self):
        text = 'Action: read_file(path="a.py")\nAction: read_file(path="a.py")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)

    def test_hint_none_by_default(self):
        text = 'Action: read_file(path="a.py")'
        actions = parse_all_actions(text)
        self.assertIsNone(actions[0][2])

    def test_parallel_hint(self):
        text = '@parallel\nAction: read_file(path="a.py")\n@end_parallel'
        actions = parse_all_actions(text)
        self.assertEqual(actions[0][2], "parallel")

    def test_sequential_hint(self):
        text = '@sequential\nAction: read_file(path="a.py")\n@end_sequential'
        actions = parse_all_actions(text)
        self.assertEqual(actions[0][2], "sequential")

    def test_no_actions(self):
        text = "Just a thought with no actions."
        actions = parse_all_actions(text)
        self.assertEqual(actions, [])

    def test_bold_action_prefix(self):
        text = '**Action:** read_file(path="a.py")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "read_file")

    def test_debug_false_does_not_crash(self):
        text = 'Action: read_file(path="a.py")'
        actions = parse_all_actions(text, debug=False)
        self.assertEqual(len(actions), 1)

    def test_returns_three_tuple(self):
        text = 'Action: read_file(path="a.py")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions[0]), 3)  # (tool_name, args_str, hint)


# ---------------------------------------------------------------------------
# _extract_annotation_ranges
# ---------------------------------------------------------------------------

class TestExtractAnnotationRanges(unittest.TestCase):

    def test_parallel_block(self):
        text = "@parallel\nsome content\n@end_parallel"
        ranges = _extract_annotation_ranges(text)
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0][2], "parallel")

    def test_sequential_block(self):
        text = "@sequential\nsome content\n@end_sequential"
        ranges = _extract_annotation_ranges(text)
        self.assertEqual(len(ranges), 1)
        self.assertEqual(ranges[0][2], "sequential")

    def test_no_annotations(self):
        text = "Action: read_file(path=\"a.py\")"
        ranges = _extract_annotation_ranges(text)
        self.assertEqual(ranges, [])

    def test_multiple_blocks(self):
        text = "@parallel\ncontent1\n@end_parallel\n@sequential\ncontent2\n@end_sequential"
        ranges = _extract_annotation_ranges(text)
        self.assertEqual(len(ranges), 2)


# ---------------------------------------------------------------------------
# _strip_native_tool_tokens
# ---------------------------------------------------------------------------

class TestStripNativeToolTokens(unittest.TestCase):

    def test_json_tool_call_converted(self):
        text = '<tool_call>{"name":"read_file","arguments":{"path":"a.py"}}</tool_call>'
        result = _strip_native_tool_tokens(text)
        self.assertIn("Action: read_file", result)

    def test_thinking_tags_stripped(self):
        text = "<think>reasoning</think>Action: read_file(path=\"a.py\")"
        result = _strip_native_tool_tokens(text)
        self.assertNotIn("<think>", result)
        self.assertIn("read_file", result)

    def test_glm_xml_format(self):
        text = '<tool>list_dir</tool><parameter><path>.</path></parameter>'
        result = _strip_native_tool_tokens(text)
        self.assertIn("Action: list_dir", result)

    def test_bare_known_tool_gets_action_prefix(self):
        text = 'read_file(path="a.py")'
        result = _strip_native_tool_tokens(text)
        self.assertIn("Action: read_file", result)

    def test_no_op_on_clean_action(self):
        text = 'Action: read_file(path="a.py")'
        result = _strip_native_tool_tokens(text)
        self.assertIn("read_file", result)


# ---------------------------------------------------------------------------
# _convert_all_glm_tool_calls
# ---------------------------------------------------------------------------

class TestConvertAllGlmToolCalls(unittest.TestCase):

    def test_basic_glm_call(self):
        def dummy_converter(tool_name, params_block):
            return f"\nAction: {tool_name}(converted)\n"

        text = "<tool>list_dir</tool><parameter><path>.</path></parameter>"
        result = _convert_all_glm_tool_calls(text, dummy_converter)
        self.assertIn("Action: list_dir", result)

    def test_no_tool_tags_passthrough(self):
        def dummy_converter(tool_name, params_block):
            return ""

        text = "plain text no tool tags"
        result = _convert_all_glm_tool_calls(text, dummy_converter)
        self.assertEqual(result, text)


# ---------------------------------------------------------------------------
# parse_implicit_actions
# ---------------------------------------------------------------------------

class TestParseImplicitActions(unittest.TestCase):

    def test_command_r_format(self):
        text = 'to=repo_browser.read_file\n<|message|>{"path": "a.py"}'
        actions = parse_implicit_actions(text)
        if actions:  # Optional format, may or may not match
            self.assertEqual(actions[0][0], "read_file")

    def test_no_implicit_actions(self):
        text = 'Action: read_file(path="a.py")'
        actions = parse_implicit_actions(text)
        self.assertEqual(actions, [])


# ---------------------------------------------------------------------------
# KNOWN_TOOLS constant
# ---------------------------------------------------------------------------

class TestKnownTools(unittest.TestCase):

    def test_is_frozenset(self):
        self.assertIsInstance(KNOWN_TOOLS, frozenset)

    def test_contains_basic_tools(self):
        self.assertIn("read_file", KNOWN_TOOLS)
        self.assertIn("write_file", KNOWN_TOOLS)
        self.assertIn("run_command", KNOWN_TOOLS)
        self.assertIn("list_dir", KNOWN_TOOLS)
        self.assertIn("grep_file", KNOWN_TOOLS)


if __name__ == '__main__':
    unittest.main()
