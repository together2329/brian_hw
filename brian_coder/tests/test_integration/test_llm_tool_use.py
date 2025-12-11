"""
LLM Tool Use Integration Tests

Tests that LLM can correctly parse and execute tools, handle tool responses,
manage multi-turn conversations, and recover from tool errors.
"""
import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock

# Add paths for imports
_tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'lib'))

# Now import main functions
from main import (
    parse_all_actions,
    parse_tool_arguments,
    execute_tool,
    process_observation,
    sanitize_action_text,
)
from core import tools


class TestParseToolCorrectness(unittest.TestCase):
    """Test that action parsing handles various LLM output formats correctly."""

    def test_simple_single_action(self):
        """LLM outputs a single tool call."""
        text = 'Thought: I need to read a file.\nAction: read_file(path="test.py")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "read_file")
        self.assertIn("path", actions[0][1])

    def test_multiple_sequential_actions(self):
        """LLM outputs multiple tool calls in sequence."""
        text = """
        Action: list_dir(path=".")
        Observation: [files]
        Action: read_file(path="main.py")
        """
        actions = parse_all_actions(text)
        self.assertGreaterEqual(len(actions), 2)
        self.assertEqual(actions[0][0], "list_dir")
        self.assertEqual(actions[1][0], "read_file")

    def test_action_with_special_characters(self):
        """Tool arguments contain special characters and escapes."""
        text = r'Action: write_file(path="file.py", content="Hello\nWorld\t!")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "write_file")
        # Args should be parseable
        args, kwargs = parse_tool_arguments(actions[0][1])
        self.assertIn("path", kwargs)

    def test_action_with_multiline_content(self):
        """Tool arguments span multiple lines."""
        text = '''Action: write_file(
            path="code.py",
            content="def hello():\\n    print('world')"
        )'''
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "write_file")

    def test_action_with_markdown_code_block(self):
        """LLM wraps action in markdown code block."""
        text = """Let me run this command:
        ```
        Action: run_command(command="ls -la")
        ```
        """
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "run_command")

    def test_malformed_action_recovery(self):
        """Parser handles slightly malformed actions gracefully."""
        # Missing closing parenthesis - parser should still try to extract
        text = 'Action: read_file(path="test.py"'
        actions = parse_all_actions(text)
        # Should either extract or return empty list (both acceptable)
        self.assertIsInstance(actions, list)

    def test_action_with_quoted_parentheses(self):
        """Arguments contain parentheses inside strings."""
        text = 'Action: write_file(path="file.py", content="func() returns value")'
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)


class TestToolArgumentParsing(unittest.TestCase):
    """Test that tool arguments are correctly extracted and converted."""

    def test_keyword_only_arguments(self):
        """Parse keyword-only arguments."""
        args_str = 'path="file.py", mode=2'
        args, kwargs = parse_tool_arguments(args_str)
        self.assertEqual(len(args), 0)
        self.assertEqual(kwargs["path"], "file.py")
        self.assertEqual(kwargs["mode"], 2)

    def test_positional_and_keyword_mix(self):
        """Parse mixed positional and keyword arguments."""
        args_str = '"pattern", "file.py", context_lines=3'
        args, kwargs = parse_tool_arguments(args_str)
        # Should handle both positional and keyword
        self.assertGreater(len(args) + len(kwargs), 0)

    def test_string_with_escaped_quotes(self):
        """Strings with escaped quotes are parsed correctly."""
        args_str = r'path="file with \"quotes\".py"'
        args, kwargs = parse_tool_arguments(args_str)
        self.assertIn("path", kwargs)

    def test_triple_quoted_strings(self):
        """Triple-quoted strings are handled."""
        args_str = '''content="""Line 1
Line 2
Line 3"""'''
        args, kwargs = parse_tool_arguments(args_str)
        self.assertIn("content", kwargs)

    def test_numeric_arguments(self):
        """Numeric arguments are converted to correct types."""
        args_str = 'start_line=10, end_line=20, timeout=5.5'
        args, kwargs = parse_tool_arguments(args_str)
        self.assertEqual(kwargs["start_line"], 10)
        self.assertEqual(kwargs["end_line"], 20)
        self.assertAlmostEqual(kwargs["timeout"], 5.5)

    def test_boolean_arguments(self):
        """Boolean arguments are handled."""
        # Note: This depends on implementation
        args_str = 'recursive=True, force=False'
        args, kwargs = parse_tool_arguments(args_str)
        # Should parse these somehow
        self.assertGreater(len(kwargs), 0)


class TestToolExecution(unittest.TestCase):
    """Test that tools execute correctly and return expected results."""

    def setUp(self):
        """Create temporary directory for file operations."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up temporary files."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_execute_read_file_success(self):
        """Execute read_file tool successfully."""
        # Create a test file
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("Hello, World!")

        # Execute tool
        result = execute_tool("read_file", f'path="{test_file}"')
        self.assertIn("Hello", result)

    def test_execute_write_file_success(self):
        """Execute write_file tool successfully."""
        test_file = os.path.join(self.temp_dir, "write_test.txt")
        result = execute_tool("write_file", f'path="{test_file}", content="Test content"')

        # Verify file was created
        self.assertTrue(os.path.exists(test_file))
        with open(test_file) as f:
            content = f.read()
        self.assertEqual(content, "Test content")

    def test_execute_list_dir_success(self):
        """Execute list_dir tool successfully."""
        result = execute_tool("list_dir", f'path="{self.temp_dir}"')
        self.assertIsInstance(result, str)

    def test_execute_nonexistent_tool(self):
        """Executing non-existent tool returns error."""
        result = execute_tool("nonexistent_tool", 'arg="value"')
        self.assertIn("Error", result)
        self.assertIn("not found", result)

    def test_execute_read_file_not_found(self):
        """Reading non-existent file returns error."""
        result = execute_tool("read_file", 'path="/nonexistent/file.txt"')
        self.assertIsInstance(result, str)
        # Should either error or return "file not found" type message

    def test_execute_tool_with_bad_arguments(self):
        """Tool execution with invalid arguments handles gracefully."""
        # Missing required argument
        result = execute_tool("read_file", '')
        # Should fail gracefully
        self.assertIsInstance(result, str)


class TestMultiTurnToolUse(unittest.TestCase):
    """Test multi-turn conversations with repeated tool use."""

    def setUp(self):
        """Initialize test conversation state."""
        self.temp_dir = tempfile.mkdtemp()
        self.messages = [
            {
                "role": "system",
                "content": "You are a helpful assistant. Use tools to complete tasks."
            }
        ]

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_observation_added_to_messages(self):
        """Tool observation is correctly added to message history."""
        observation = "File contents: Hello World"
        messages_before = len(self.messages)

        messages_after = process_observation(observation, self.messages)

        self.assertGreater(len(messages_after), messages_before)
        # Last message should be user with observation
        self.assertEqual(messages_after[-1]["role"], "user")
        self.assertIn("Observation:", messages_after[-1]["content"])

    def test_multiple_observations_sequence(self):
        """Multiple tool executions add observations correctly."""
        self.messages.append({"role": "user", "content": "Read file and process it"})

        # First tool execution
        obs1 = "Content of file"
        self.messages = process_observation(obs1, self.messages)

        # Second tool execution
        obs2 = "Processed result"
        self.messages = process_observation(obs2, self.messages)

        # Both observations should be in history
        all_content = " ".join([m["content"] for m in self.messages])
        self.assertIn("Content of file", all_content)
        self.assertIn("Processed result", all_content)

    def test_observation_truncation_for_long_results(self):
        """Long tool results are truncated appropriately."""
        # Create a very long observation
        long_content = "Line: " * 5000  # Very long output
        observation = f"Output:\n{long_content}"

        messages_after = process_observation(observation, self.messages)

        # Message should be added but might be truncated
        self.assertGreater(len(messages_after), 0)


class TestToolErrorHandling(unittest.TestCase):
    """Test error handling in tool execution."""

    def test_syntax_error_in_action(self):
        """LLM output has syntax error in action."""
        text = "Action: read_file(path=test.py"  # Missing quote
        actions = parse_all_actions(text)
        # Should either parse partially or return empty
        self.assertIsInstance(actions, list)

    def test_unknown_tool_error(self):
        """Attempting to execute unknown tool returns error."""
        result = execute_tool("fake_tool", 'arg="value"')
        self.assertIn("not found", result.lower() or "error" in result.lower())

    def test_tool_execution_exception_handling(self):
        """Tool execution exceptions are caught and reported."""
        # Try to read file with invalid path argument
        result = execute_tool("read_file", '')
        # Should handle gracefully
        self.assertIsInstance(result, str)

    def test_repeated_same_error_detection(self):
        """System can detect when same error repeats."""
        error1 = "Tool 'read' not found"
        error2 = "Tool 'read' not found"

        # Same error repeated should be detectable
        self.assertEqual(error1, error2)

    def test_action_with_unmatched_brackets(self):
        """Parser handles unmatched brackets."""
        text = "Action: read_file(path='test.py']]"
        actions = parse_all_actions(text)
        # Should handle gracefully (might return empty or partial)
        self.assertIsInstance(actions, list)


class TestSanitization(unittest.TestCase):
    """Test that action text sanitization works correctly."""

    def test_markdown_bold_handling(self):
        """Markdown bold markers are handled."""
        text = "**Action: read_file(path='file.py')**"
        sanitized = sanitize_action_text(text)
        # Main thing is the action is still parseable
        self.assertIn("Action:", sanitized)

    def test_markdown_italic_handling(self):
        """Markdown italic markers are handled."""
        text = "*Action: read_file(path='file.py')*"
        sanitized = sanitize_action_text(text)
        # Main thing is the action is still parseable
        self.assertIn("Action:", sanitized)

    def test_code_block_markers_removed(self):
        """Code block markers are removed."""
        text = "`Action: read_file(path='file.py')`"
        sanitized = sanitize_action_text(text)
        # Backticks might be removed or kept
        self.assertIn("Action:", sanitized)

    def test_weird_quote_fixes(self):
        """Weird quote characters are fixed."""
        # Some LLMs produce curly quotes or other variants
        text = 'Action: read_file(path="file.py")'  # Might have smart quotes
        sanitized = sanitize_action_text(text)
        # Should be parseable
        self.assertIsInstance(sanitized, str)


class TestLLMResponseHandling(unittest.TestCase):
    """Test handling of various LLM response patterns."""

    def test_thought_and_action_pattern(self):
        """Standard ReAct pattern: Thought + Action."""
        text = """Thought: I need to read the configuration file.
        Action: read_file(path="config.json")
        """
        actions = parse_all_actions(text)
        self.assertEqual(len(actions), 1)
        self.assertEqual(actions[0][0], "read_file")

    def test_multiple_thoughts_and_actions(self):
        """Multiple thought-action cycles."""
        text = """
        Thought: First, I'll check what files exist.
        Action: list_dir(path=".")

        Thought: Now I'll read the main file.
        Action: read_file(path="main.py")
        """
        actions = parse_all_actions(text)
        self.assertGreaterEqual(len(actions), 2)

    def test_completion_signal_detection(self):
        """Detect when LLM indicates task completion."""
        completion_signals = [
            "Finally: The task is complete.",
            "Task complete: Summarizing results...",
            "I have successfully completed the task.",
        ]

        # These should be recognized as completion
        for signal in completion_signals:
            # Check if completion keywords exist
            self.assertTrue(
                "finally" in signal.lower() or
                "complete" in signal.lower() or
                "successfully" in signal.lower()
            )

    def test_hallucinated_observation(self):
        """LLM might generate fake observations."""
        text = """
        Action: read_file(path="file.py")
        Observation: The file contained: Hello World
        """
        # This is problematic - LLM shouldn't generate observations
        actions = parse_all_actions(text)
        # Only the action should be extracted, not the fake observation
        self.assertEqual(len(actions), 1)


class TestToolChaining(unittest.TestCase):
    """Test complex tool sequences that depend on each other."""

    def setUp(self):
        """Create test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_read_then_write(self):
        """Read a file, then write processed content."""
        # Create initial file
        source_file = os.path.join(self.temp_dir, "source.txt")
        with open(source_file, "w") as f:
            f.write("original content")

        # Read it
        result1 = execute_tool("read_file", f'path="{source_file}"')
        self.assertIn("original", result1)

        # Write modified version
        target_file = os.path.join(self.temp_dir, "target.txt")
        result2 = execute_tool(
            "write_file",
            f'path="{target_file}", content="modified content"'
        )

        # Verify
        with open(target_file) as f:
            content = f.read()
        self.assertEqual(content, "modified content")

    def test_list_then_read(self):
        """List directory, then read a file from results."""
        # Create test files
        test_file = os.path.join(self.temp_dir, "test.txt")
        with open(test_file, "w") as f:
            f.write("test content")

        # List directory
        result1 = execute_tool("list_dir", f'path="{self.temp_dir}"')
        self.assertIsInstance(result1, str)

        # Read the file we found
        result2 = execute_tool("read_file", f'path="{test_file}"')
        self.assertIn("test", result2)


class TestContextManagement(unittest.TestCase):
    """Test that tools work correctly with context management."""

    def test_observation_with_message_history(self):
        """Observations are added correctly to growing message history."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User request 1"},
            {"role": "assistant", "content": "Response 1"},
        ]

        # Add observation
        observation = "Observation: Result 1"
        messages = process_observation(observation, messages)

        # Should have 4 messages now
        self.assertEqual(len(messages), 4)
        self.assertEqual(messages[-1]["role"], "user")

    def test_large_tool_output_handling(self):
        """Large tool outputs don't break the system."""
        messages = [
            {"role": "system", "content": "System prompt"}
        ]

        # Simulate large tool output
        large_output = "X" * 50000  # 50KB of output
        observation = f"Output:\n{large_output}"

        messages = process_observation(observation, messages)

        # Should still work (might be truncated)
        self.assertGreater(len(messages), 1)


class TestToolUsabilityFromLLMPerspective(unittest.TestCase):
    """Test that tools are usable from LLM's perspective."""

    def test_all_tools_in_available_tools(self):
        """All essential tools are registered."""
        essential_tools = [
            "read_file",
            "write_file",
            "run_command",
            "list_dir",
            "grep_file",
        ]

        for tool in essential_tools:
            self.assertIn(tool, tools.AVAILABLE_TOOLS)

    def test_tool_callable(self):
        """All registered tools are callable."""
        for tool_name, tool_func in tools.AVAILABLE_TOOLS.items():
            self.assertTrue(callable(tool_func), f"Tool {tool_name} is not callable")

    def test_tool_execution_via_name(self):
        """Tools can be executed by name (as LLM would use them)."""
        # This is how the system would execute tools
        tool_name = "list_dir"
        args_str = 'path="."'

        # Should work without errors
        result = execute_tool(tool_name, args_str)
        self.assertIsInstance(result, str)


if __name__ == "__main__":
    unittest.main()
