"""
Unit tests for src/main.py
Tests core parsing and context management functions.
"""
import sys
import os
import unittest

# Add paths for imports
_script_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = _script_dir
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

# Import after path setup
from src.main import (
    parse_value,
    parse_tool_arguments,
    parse_all_actions,
    sanitize_action_text,
    build_system_prompt
)


class TestParseValue(unittest.TestCase):
    """Test parse_value function"""

    def test_parse_string_double_quote(self):
        """Test parsing double-quoted string"""
        result, consumed = parse_value('"hello"')
        self.assertEqual(result, 'hello')
        self.assertEqual(consumed, 7)

    def test_parse_string_single_quote(self):
        """Test parsing single-quoted string"""
        result, consumed = parse_value("'world'")
        self.assertEqual(result, 'world')
        self.assertEqual(consumed, 7)

    def test_parse_integer(self):
        """Test parsing integer"""
        result, consumed = parse_value('123')
        self.assertEqual(result, 123)
        self.assertEqual(consumed, 3)

    def test_parse_float(self):
        """Test parsing float"""
        result, consumed = parse_value('45.67')
        self.assertEqual(result, 45.67)
        self.assertEqual(consumed, 5)

    def test_parse_identifier(self):
        """Test parsing identifier"""
        result, consumed = parse_value('myvar')
        self.assertEqual(result, 'myvar')
        self.assertEqual(consumed, 5)

    def test_parse_empty(self):
        """Test parsing empty string"""
        result, consumed = parse_value('')
        self.assertIsNone(result)
        self.assertEqual(consumed, 0)


class TestSanitizeActionText(unittest.TestCase):
    """Test sanitize_action_text function"""

    def test_remove_markdown_bold_action(self):
        """Test removing **Action:** markdown"""
        result = sanitize_action_text('**Action:** read_file()')
        self.assertEqual(result, 'Action: read_file()')

    def test_fix_quote_error_double(self):
        """Test fixing quote errors with double quotes"""
        result = sanitize_action_text('Action: func(arg=26")')
        self.assertEqual(result, 'Action: func(arg=26)')

    def test_fix_quote_error_single(self):
        """Test fixing quote errors with single quotes"""
        result = sanitize_action_text("Action: func(arg=26')")
        self.assertEqual(result, "Action: func(arg=26)")

    def test_preserve_normal_action(self):
        """Test that normal actions are unchanged"""
        result = sanitize_action_text('Action: read_file(path="test.py")')
        self.assertEqual(result, 'Action: read_file(path="test.py")')


class TestParseToolArguments(unittest.TestCase):
    """Test parse_tool_arguments function"""

    def test_single_keyword_arg(self):
        """Test parsing single keyword argument"""
        args, kwargs = parse_tool_arguments('path="test.py"')
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {'path': 'test.py'})

    def test_multiple_keyword_args(self):
        """Test parsing multiple keyword arguments"""
        args, kwargs = parse_tool_arguments('start=10, end=20')
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {'start': 10, 'end': 20})

    def test_mixed_args(self):
        """Test parsing mixed positional and keyword arguments"""
        args, kwargs = parse_tool_arguments('"file.py", mode="r"')
        self.assertEqual(len(args), 1)
        self.assertEqual(args[0], 'file.py')
        self.assertEqual(kwargs, {'mode': 'r'})

    def test_empty_args(self):
        """Test parsing empty arguments"""
        args, kwargs = parse_tool_arguments('')
        self.assertEqual(args, [])
        self.assertEqual(kwargs, {})


class TestParseAllActions(unittest.TestCase):
    """Test parse_all_actions function"""

    def test_single_action(self):
        """Test parsing single action"""
        result = parse_all_actions('Action: read_file(path="main.py")')
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'read_file')
        self.assertEqual(result[0][1], 'path="main.py"')

    def test_multiple_actions(self):
        """Test parsing multiple actions"""
        text = 'Action: tool1(arg=1)\n\nAction: tool2(arg=2)'
        result = parse_all_actions(text)
        self.assertEqual(len(result), 2)
        self.assertEqual(result[0][0], 'tool1')
        self.assertEqual(result[1][0], 'tool2')

    def test_markdown_action(self):
        """Test parsing markdown-formatted action"""
        text = '**Action:** read_file(path="test.py")'
        result = parse_all_actions(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'read_file')

    def test_action_with_triple_quotes(self):
        """Test parsing action with triple-quoted strings"""
        text = 'Action: create(content="""hello""")'
        result = parse_all_actions(text)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0][0], 'create')

    def test_no_actions(self):
        """Test parsing text without actions"""
        result = parse_all_actions('This is just text without any actions')
        self.assertEqual(len(result), 0)


class TestBuildSystemPrompt(unittest.TestCase):
    """Test build_system_prompt function"""

    def test_prompt_generated(self):
        """Test that system prompt is generated"""
        prompt = build_system_prompt()
        self.assertIsNotNone(prompt)
        self.assertGreater(len(prompt), 100)

    def test_prompt_contains_base_prompt(self):
        """Test that prompt contains base system prompt"""
        import config
        prompt = build_system_prompt()
        self.assertIn(config.SYSTEM_PROMPT[:50], prompt)

    def test_prompt_contains_rag_guidance(self):
        """Test that prompt contains RAG guidance"""
        prompt = build_system_prompt()
        self.assertIn("RAG", prompt)
        self.assertIn("rag_search", prompt)


class TestIntegration(unittest.TestCase):
    """Integration tests for main.py"""

    def test_full_parse_workflow(self):
        """Test complete parsing workflow"""
        # Simulate LLM output with errors
        llm_output = """
Thought: I need to read the file first.

**Action:** read_file(path="src/main.py")

I also need to check the config.
Action: read_file(path="src/config.py")
"""
        # Parse all actions
        actions = parse_all_actions(llm_output)

        # Should find 2 actions
        self.assertEqual(len(actions), 2)

        # First action
        self.assertEqual(actions[0][0], 'read_file')
        args, kwargs = parse_tool_arguments(actions[0][1])
        self.assertEqual(kwargs['path'], 'src/main.py')

        # Second action
        self.assertEqual(actions[1][0], 'read_file')
        args, kwargs = parse_tool_arguments(actions[1][1])
        self.assertEqual(kwargs['path'], 'src/config.py')

    def test_error_recovery(self):
        """Test that parser handles malformed actions gracefully"""
        # This has unmatched parentheses but should skip and find second action
        text = 'Action: bad(unclosed\n\nAction: good(arg=1)'
        result = parse_all_actions(text)

        # Should at least find the good action
        self.assertGreaterEqual(len(result), 1)
        self.assertEqual(result[-1][0], 'good')


class TestModuleImports(unittest.TestCase):
    """Test that all required modules can be imported"""

    def test_import_config(self):
        """Test importing config module"""
        import config
        self.assertIsNotNone(config.BASE_URL)
        self.assertIsNotNone(config.API_KEY)

    def test_import_llm_client(self):
        """Test importing llm_client module"""
        import llm_client
        self.assertTrue(hasattr(llm_client, 'chat_completion_stream'))

    def test_import_core_tools(self):
        """Test importing core tools"""
        from core import tools
        self.assertTrue(hasattr(tools, 'read_file'))
        self.assertTrue(hasattr(tools, 'write_file'))

    def test_import_lib_display(self):
        """Test importing display module"""
        from lib.display import Color
        self.assertIsNotNone(Color.RED)
        self.assertIsNotNone(Color.GREEN)


if __name__ == '__main__':
    # Run tests with verbose output
    unittest.main(verbosity=2)
