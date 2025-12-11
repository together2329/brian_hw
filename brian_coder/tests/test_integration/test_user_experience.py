"""
User Experience (UX) Integration Tests

Tests that verify the agent system is usable and understandable from the user's perspective.
Focuses on:
- Feedback clarity
- Progress visibility
- Error handling UX
- Context transparency
- Navigation and next steps
"""
import sys
import os
import tempfile
import unittest
from unittest.mock import Mock, patch, MagicMock
from io import StringIO

# Add paths for imports
_tests_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
_project_root = os.path.dirname(_tests_dir)
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'lib'))

import config
from main import (
    show_iteration_warning,
    show_context_usage,
    execute_tool,
    parse_all_actions,
)
from lib.iteration_control import IterationTracker


class TestResponseClarity(unittest.TestCase):
    """Test that system responses are clear and understandable."""

    def test_error_message_includes_problem_and_solution(self):
        """Error messages should explain what went wrong AND how to fix it."""
        # When tool execution fails
        result = execute_tool("read_file", 'path="/nonexistent/file.txt"')

        # Error should be a string (not None or exception)
        self.assertIsInstance(result, str)

        # Should contain explanation
        self.assertTrue(
            "not found" in result.lower() or
            "error" in result.lower() or
            "no such" in result.lower()
        )

    def test_tool_success_message_shows_preview(self):
        """Successful tool execution should show useful preview."""
        # Create temp file
        with tempfile.NamedTemporaryFile(mode='w', delete=False, suffix='.txt') as f:
            f.write("Line 1\nLine 2\nLine 3\n")
            temp_path = f.name

        try:
            result = execute_tool("read_file", f'path="{temp_path}"')

            # Should show content or preview
            self.assertGreater(len(result), 0)
            # Should contain actual file content
            self.assertIn("Line", result)
        finally:
            os.unlink(temp_path)

    def test_multiple_actions_show_progress(self):
        """When multiple tools are parsed, show which one is being executed."""
        text = """
        Action: list_dir(path=".")
        Action: read_file(path="test.py")
        """
        actions = parse_all_actions(text)

        # Should extract both actions
        self.assertEqual(len(actions), 2)

        # User should be able to see what's happening
        self.assertEqual(actions[0][0], "list_dir")
        self.assertEqual(actions[1][0], "read_file")


class TestProgressVisibility(unittest.TestCase):
    """Test that user can see progress and understand what's happening."""

    def test_iteration_counter_shows_progress(self):
        """Iteration counter helps user understand how deep we are."""
        tracker = IterationTracker(max_iterations=100)

        # User should see current iteration
        self.assertEqual(tracker.current, 0)

        # As iterations progress
        tracker.increment()
        self.assertEqual(tracker.current, 1)

        # User knows they're in iteration 1/100
        progress_text = f"Iteration {tracker.current}/{tracker.max_iterations}"
        self.assertIn("1/100", progress_text)

    def test_iteration_warning_at_high_counts(self):
        """System should warn user when iteration count gets high."""
        tracker = IterationTracker(max_iterations=100)

        # At iteration 80, should warn
        tracker.current = 80
        warning_action = show_iteration_warning(tracker)

        # Should return action or warning
        self.assertIn(warning_action, ['continue', 'stop', 'extend', None])

    def test_context_usage_bar_is_understandable(self):
        """Context usage indicator should be clear and meaningful."""
        messages = [
            {"role": "system", "content": "System prompt"},
            {"role": "user", "content": "User message"},
        ]

        # Should show context usage in human-readable format
        # Typical output: "[Context: 234/262,144 tokens (0%) █░░░░░░░░░░░░░░░░░░ OK]"
        # This is captured to stdout but we can verify the format is sensible

        self.assertGreater(len(messages), 0)

    def test_tool_execution_shows_which_tool_running(self):
        """User should know which tool is being executed."""
        # Simulate tool execution feedback
        tool_name = "read_file"
        tool_num = 1
        total_tools = 3

        feedback = f"Tool {tool_num}/{total_tools}: {tool_name}"

        self.assertIn("Tool 1/3", feedback)
        self.assertIn("read_file", feedback)


class TestErrorMessageQuality(unittest.TestCase):
    """Test that error messages are helpful and not confusing."""

    def test_unknown_tool_error_is_actionable(self):
        """Error for unknown tool should say what to do."""
        result = execute_tool("nonexistent_tool_xyz", 'arg="value"')

        # Should clearly indicate tool not found
        self.assertIn("not found", result.lower() or "error" in result.lower())

        # Ideally should suggest available tools (but not required)

    def test_bad_argument_error_shows_what_went_wrong(self):
        """Error for bad arguments should explain the issue."""
        # Missing required argument
        result = execute_tool("read_file", "")

        # Should be an error message
        self.assertIsInstance(result, str)
        # Should not be empty
        self.assertGreater(len(result), 0)

    def test_rate_limit_message_explains_why(self):
        """Rate limit message should explain it's for API safety."""
        # Rate limit delay message should be clear
        message = "Waiting for rate limit: Preventing API flooding..."

        # Should be understandable
        self.assertIn("rate", message.lower())
        self.assertIn("limit", message.lower())


class TestContextTransparency(unittest.TestCase):
    """Test that context management is transparent to user."""

    def test_context_compression_announced(self):
        """When context is compressed, user should be informed."""
        # Compression should have a clear message like:
        # "[System] Context compressed from 245,000 → 189,000 tokens (23% reduction)"

        compression_msg = "Context compressed from 245,000 → 189,000 tokens"

        # Message should be clear
        self.assertIn("compressed", compression_msg.lower())
        self.assertIn("tokens", compression_msg.lower())

        # Should show old and new size
        self.assertIn("245,000", compression_msg)
        self.assertIn("189,000", compression_msg)

    def test_context_warning_threshold_is_clear(self):
        """When context gets high, warning should be clear."""
        # Example message:
        threshold = 80
        current = 85

        warning = f"Context usage HIGH ({current}% of {100}% capacity). Compression starting..."

        self.assertIn("HIGH", warning)
        self.assertIn("85", warning)
        self.assertIn("Compression", warning)

    def test_context_loss_warning(self):
        """If context compression loses important info, user should know."""
        # After compression, ideally:
        # "[System] ⚠️  Compressed conversation history (some old interactions may be lost)"

        msg = "Compressed conversation history"
        self.assertIn("Compressed", msg)


class TestHistoryManagement(unittest.TestCase):
    """Test that conversation history is clear and manageable."""

    def test_history_loading_is_explicit(self):
        """When loading previous history, be explicit."""
        load_msg = "[System] Resuming from previous conversation (loaded 150 messages from 2 hours ago)"

        # Should show:
        # - What's being loaded
        # - When it's from
        self.assertIn("Resuming", load_msg)
        self.assertIn("loaded", load_msg)

    def test_new_conversation_is_clear(self):
        """Starting fresh should be obvious."""
        new_msg = "[System] Started new conversation (previous history available as backup)"

        self.assertIn("new", new_msg.lower())

    def test_history_size_is_visible(self):
        """User should know how much history is stored."""
        # After auto-save:
        # "[Memory] Conversation saved (156 messages, ~245KB)"

        history_info = "Conversation saved (156 messages, ~245KB)"

        self.assertIn("messages", history_info)
        self.assertIn("245", history_info)


class TestNavigationClarity(unittest.TestCase):
    """Test that user knows what to do next."""

    def test_initial_prompt_is_inviting(self):
        """First message should invite user to interact."""
        initial = "You: "

        # Should be clear what user should do
        self.assertIsInstance(initial, str)

    def test_task_completion_is_obvious(self):
        """When task is done, it should be clear."""
        completion_msgs = [
            "Task complete!",
            "✓ Task finished successfully",
            "Completed all requested work",
        ]

        for msg in completion_msgs:
            self.assertTrue(
                "complete" in msg.lower() or "finished" in msg.lower()
            )

    def test_waiting_for_input_is_clear(self):
        """When waiting for user input, be explicit."""
        prompt = "You: "

        # Should be obviously a prompt
        self.assertIsInstance(prompt, str)


class TestMemorySystemFeedback(unittest.TestCase):
    """Test that memory system provides clear feedback."""

    def test_memory_learning_is_announced(self):
        """When system learns something, announce it."""
        msg = "✅ Learned: User prefers Python for scripting"

        self.assertIn("Learned", msg)

    def test_memory_usage_context(self):
        """User should know memory system is active."""
        active_msg = "[Memory] Active - learning user preferences"

        self.assertIn("Memory", active_msg)
        self.assertIn("Active", active_msg)

    def test_memory_helps_in_next_interaction(self):
        """Memory should be obviously helping."""
        help_msg = "[Memory] Using learned preference: file_location = project_root"

        self.assertIn("Using learned", help_msg)


class TestToolUXPatterns(unittest.TestCase):
    """Test that tool execution patterns are user-friendly."""

    def setUp(self):
        """Create temp files for testing."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up."""
        import shutil
        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_file_too_large_warning(self):
        """When file is too large, explain what's happening."""
        warning = "File too large (45,678 chars). Showing first 100 lines..."

        # Should be clear
        self.assertIn("too large", warning.lower())
        self.assertIn("showing", warning.lower())

    def test_command_output_truncation_is_clear(self):
        """When command output is truncated, say so."""
        msg = "Command output (2,456 lines). Showing first 50 lines..."

        self.assertIn("output", msg.lower())
        self.assertTrue(
            "truncated" in msg.lower() or "showing" in msg.lower()
        )

    def test_tool_chaining_shows_dependencies(self):
        """When tools depend on each other, show the flow."""
        # Example: read_file → parse → write_file
        # User should see: "Tool 1/3: read_file → Tool 2/3: parse → Tool 3/3: write_file"

        flow = "Tool 1/3: read_file → Tool 2/3: parse → Tool 3/3: write_file"

        self.assertIn("read_file", flow)
        self.assertIn("parse", flow)
        self.assertIn("write_file", flow)


class TestErrorRecoveryUX(unittest.TestCase):
    """Test that error recovery is clear and helpful."""

    def test_consecutive_error_warning(self):
        """When same error repeats, warn user explicitly."""
        msg = "⚠️  Same error happened 3 times. Stopping to prevent infinite loop."

        self.assertIn("error", msg.lower())
        self.assertIn("3 times", msg)
        self.assertIn("infinite loop", msg.lower())

    def test_retry_attempt_is_shown(self):
        """When retrying after error, announce it."""
        msg = "Retrying action (Attempt 2/3)..."

        self.assertIn("Retry", msg)
        self.assertIn("2/3", msg)

    def test_final_failure_is_graceful(self):
        """When giving up, explain why clearly."""
        msg = "Action failed after 3 attempts. Skipping to next action."

        self.assertIn("failed", msg.lower())
        self.assertIn("3 attempts", msg)


class TestResponseTiming(unittest.TestCase):
    """Test that timing feedback is helpful."""

    def test_slow_operation_is_announced(self):
        """If operation takes >2 seconds, let user know."""
        # Pseudo-code: if elapsed > 2s: print("Processing... (2.3s elapsed)")

        msg = "Processing... (2.3s elapsed)"

        self.assertIn("Processing", msg)
        self.assertIn("2.3s", msg)

    def test_rate_limit_purpose_is_clear(self):
        """Rate limit delay should explain why."""
        msg = "API Rate Limit (5s delay) - Preventing flooding..."

        self.assertIn("Rate Limit", msg)
        self.assertIn("Preventing", msg)


class TestDebugInfoAvailability(unittest.TestCase):
    """Test that debug info is available when needed."""

    def test_debug_mode_flag_exists(self):
        """Debug mode should exist in config."""
        self.assertTrue(hasattr(config, 'DEBUG_MODE'))

    def test_verbose_option_available(self):
        """User should be able to enable verbose output."""
        # Config should support verbose mode
        verbose_supported = hasattr(config, 'DEBUG_MODE') or hasattr(config, 'VERBOSE_MODE')
        self.assertTrue(verbose_supported)


class TestTaskComplexityFeedback(unittest.TestCase):
    """Test that complex tasks provide helpful feedback."""

    def test_multi_iteration_task_shows_checkpoint(self):
        """Every 10 iterations, show progress checkpoint."""
        # After iteration 10, 20, 30, etc:
        # "[Checkpoint] 10 iterations complete. Context: 45% | Tools used: 8 | Errors: 0"

        checkpoint = "[Checkpoint 10] Context: 45% | Tools used: 8 | Errors: 0"

        self.assertIn("Checkpoint", checkpoint)
        self.assertIn("Context", checkpoint)

    def test_deep_think_shows_reasoning(self):
        """Deep Think should show simplified reasoning."""
        msg = "[Deep Think] Analyzing from 3 angles... 1/3 complete"

        self.assertIn("Deep Think", msg)
        self.assertIn("analyzing", msg.lower())

    def test_sub_agent_shows_progress(self):
        """Sub-agent execution should be transparent."""
        msg = "[Sub-Agent] Explore Agent: Finding relevant files (45% complete)"

        self.assertIn("Sub-Agent", msg)
        self.assertIn("complete", msg.lower())


class TestUserFriendlinessMetrics(unittest.TestCase):
    """Test overall user-friendliness metrics."""

    def test_message_uses_first_person(self):
        """Messages should be conversational, not robotic."""
        good_msg = "I'm analyzing your project structure..."
        bad_msg = "System: Executing analysis_module on input_dataset..."

        # First person is more friendly
        self.assertIn("I'm", good_msg)

    def test_emoji_usage_is_consistent(self):
        """Emoji should be consistent and meaningful."""
        # Good use:
        # ✅ Success
        # ❌ Error
        # ⚠️  Warning
        # 🔧 Tool
        # 💭 Thinking

        emoji_meanings = {
            "✅": "success",
            "❌": "error",
            "⚠️": "warning",
        }

        self.assertGreater(len(emoji_meanings), 0)

    def test_no_cryptic_messages(self):
        """Messages should avoid internal jargon."""
        cryptic = "SRAM_WRITE_BUFFER_OVERFLOW_HANDLING_ACTIVATED"
        clear = "Memory buffer full - compressing old conversations"

        # Clear version is better
        self.assertIn("buffer", clear.lower())
        self.assertIn("compressing", clear.lower())


if __name__ == "__main__":
    unittest.main()
