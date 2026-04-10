"""
TDD tests for core/tool_dispatcher.py
Phase 7: extract execute_tool from main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import threading


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_tool(return_value="ok"):
    """Minimal tool function stub."""
    fn = MagicMock(return_value=return_value)
    fn.__name__ = "mock_tool"
    return fn


def _make_hook_registry(after_output=None, raise_on_error=False):
    """Minimal HookRegistry stub."""
    registry = MagicMock()

    def run(point, ctx):
        if after_output is not None:
            ctx.tool_output = after_output
        return ctx

    registry.run.side_effect = run
    return registry


# ---------------------------------------------------------------------------
# TestDispatchTool — core dispatch logic
# ---------------------------------------------------------------------------

class TestDispatchTool(unittest.TestCase):
    def setUp(self):
        from core.tool_dispatcher import dispatch_tool
        self._fn = dispatch_tool

    def _call(self, tool_name="my_tool", args_str='x="hello"', available_tools=None, **kwargs):
        if available_tools is None:
            available_tools = {"my_tool": _make_tool("result")}
        return self._fn(tool_name, args_str, available_tools=available_tools, **kwargs)

    # --- unknown tool ---

    def test_unknown_tool_returns_error(self):
        result = self._call(tool_name="ghost", available_tools={})
        self.assertIn("not found", result.lower())

    def test_unknown_tool_mentions_name(self):
        result = self._call(tool_name="ghost", available_tools={})
        self.assertIn("ghost", result)

    # --- successful dispatch ---

    def test_known_tool_calls_function(self):
        fn = _make_tool("hello")
        result = self._call(available_tools={"my_tool": fn})
        fn.assert_called_once()

    def test_returns_string(self):
        result = self._call()
        self.assertIsInstance(result, str)

    def test_non_string_result_converted(self):
        fn = _make_tool({"key": "value"})
        result = self._call(available_tools={"my_tool": fn})
        self.assertIsInstance(result, str)
        self.assertIn("key", result)

    def test_list_result_converted(self):
        fn = _make_tool([1, 2, 3])
        result = self._call(available_tools={"my_tool": fn})
        self.assertIsInstance(result, str)

    def test_none_result_converted(self):
        fn = _make_tool(None)
        result = self._call(available_tools={"my_tool": fn})
        self.assertIsInstance(result, str)

    # --- debug mode ---

    def test_debug_mode_does_not_crash(self):
        result = self._call(debug=True)
        self.assertIsInstance(result, str)

    # --- error handling ---

    def test_exception_returns_error_string(self):
        fn = MagicMock(side_effect=ValueError("bad input"))
        result = self._call(available_tools={"my_tool": fn})
        self.assertIn("Error", result)

    def test_exception_includes_args_str(self):
        fn = MagicMock(side_effect=RuntimeError("boom"))
        result = self._call(args_str='x="hello"', available_tools={"my_tool": fn})
        self.assertIn("hello", result)

    # --- hook integration ---

    def test_hook_registry_after_tool_exec_called(self):
        hook = _make_hook_registry()
        self._call(hook_registry=hook)
        hook.run.assert_called()

    def test_hook_registry_can_modify_output(self):
        hook = _make_hook_registry(after_output="hook-modified")
        result = self._call(hook_registry=hook)
        self.assertEqual(result, "hook-modified")

    def test_hook_registry_on_error_called(self):
        fn = MagicMock(side_effect=RuntimeError("fail"))
        hook = _make_hook_registry()
        self._call(available_tools={"my_tool": fn}, hook_registry=hook)
        hook.run.assert_called()

    def test_no_hook_registry_does_not_crash(self):
        result = self._call(hook_registry=None)
        self.assertIsInstance(result, str)


# ---------------------------------------------------------------------------
# TestAgentMetadata — thread-local metadata storage
# ---------------------------------------------------------------------------

class TestAgentMetadata(unittest.TestCase):
    def setUp(self):
        from core.tool_dispatcher import dispatch_tool, get_last_agent_metadata, clear_agent_metadata
        self._dispatch = dispatch_tool
        self._get_meta = get_last_agent_metadata
        self._clear = clear_agent_metadata

    def test_metadata_cleared_for_normal_tool(self):
        fn = _make_tool("plain result")
        self._dispatch("t", "", available_tools={"t": fn})
        self.assertIsNone(self._get_meta())

    def test_metadata_cleared_on_error(self):
        fn = MagicMock(side_effect=RuntimeError("err"))
        self._dispatch("t", "", available_tools={"t": fn})
        self.assertIsNone(self._get_meta())

    def test_clear_sets_none(self):
        self._clear()
        self.assertIsNone(self._get_meta())

    def test_thread_isolation(self):
        """Metadata set in one thread should not bleed into another."""
        from core.tool_dispatcher import _agent_metadata
        results = {}

        def set_meta():
            _agent_metadata.last_result = {"agent": "thread-local"}
            results["thread"] = _agent_metadata.last_result

        t = threading.Thread(target=set_meta)
        t.start()
        t.join()

        # Main thread should not see child thread's value
        main_val = getattr(_agent_metadata, "last_result", "NOT_SET")
        self.assertNotEqual(main_val, {"agent": "thread-local"})


# ---------------------------------------------------------------------------
# TestPreParsedKwargs — native mode direct dict dispatch
# ---------------------------------------------------------------------------

class TestPreParsedKwargs(unittest.TestCase):
    """Tests for pre_parsed_kwargs parameter (native tool call mode)."""

    def setUp(self):
        from core.tool_dispatcher import dispatch_tool
        self._fn = dispatch_tool

    def test_pre_parsed_kwargs_bypass_string_parsing(self):
        """pre_parsed_kwargs dict is passed directly to the tool function."""
        fn = _make_tool("native_result")
        result = self._fn(
            "my_tool",
            pre_parsed_kwargs={"x": "hello", "y": 42},
            available_tools={"my_tool": fn},
        )
        self.assertEqual(result, "native_result")
        fn.assert_called_once_with(x="hello", y=42)

    def test_pre_parsed_kwargs_with_complex_content(self):
        """Content with newlines/backslashes passes through uncorrupted."""
        captured = {}
        def capture_tool(path="", content=""):
            captured["content"] = content
            return "ok"

        original = "line1\nline2\ttab\\slash\nend"
        self._fn(
            "write",
            pre_parsed_kwargs={"path": "/tmp/t.txt", "content": original},
            available_tools={"write": capture_tool},
        )
        self.assertEqual(captured["content"], original)

    def test_pre_parsed_kwargs_empty_dict(self):
        """Empty dict is a valid pre_parsed_kwargs (no args)."""
        fn = _make_tool("ok")
        result = self._fn(
            "my_tool",
            pre_parsed_kwargs={},
            available_tools={"my_tool": fn},
        )
        self.assertEqual(result, "ok")
        fn.assert_called_once_with()

    def test_pre_parsed_kwargs_builds_display_args_str(self):
        """When args_str is empty, builds one from kwargs for logging."""
        fn = MagicMock(side_effect=RuntimeError("boom"))
        result = self._fn(
            "my_tool",
            pre_parsed_kwargs={"x": "hello"},
            available_tools={"my_tool": fn},
        )
        # Error message should include the display args_str
        self.assertIn("hello", result)

    def test_pre_parsed_kwargs_preserves_existing_args_str(self):
        """When args_str is provided, it's used for display/error context."""
        fn = MagicMock(side_effect=RuntimeError("custom_err"))
        result = self._fn(
            "my_tool",
            args_str="custom_display=true",
            pre_parsed_kwargs={"x": "hello"},
            available_tools={"my_tool": fn},
        )
        self.assertIn("custom_display", result)


# ---------------------------------------------------------------------------
# TestArgumentSafetyNets — excess positional & unknown kwargs
# ---------------------------------------------------------------------------

class TestArgumentSafetyNets(unittest.TestCase):
    """Tests for truncating excess positional args and stripping unknown kwargs."""

    def setUp(self):
        from core.tool_dispatcher import dispatch_tool
        self._fn = dispatch_tool

    def test_excess_positional_args_truncated(self):
        """5 positional args to a 3-param function should be truncated."""
        def three_params(a, b, c=None):
            return f"a={a}, b={b}, c={c}"

        result = self._fn(
            "three_params",
            "1, 2, 3, 4, 5",
            available_tools={"three_params": three_params},
        )
        # Should NOT crash with "takes 3 positional arguments but 5 were given"
        self.assertNotIn("Error", result)
        self.assertIn("a=1", result)

    def test_unknown_kwargs_stripped(self):
        """Unknown kwargs are silently removed before calling the function."""
        def strict_params(path, start_line=None, end_line=None):
            return f"path={path}"

        result = self._fn(
            "strict_params",
            'path="foo.py", start_line=1, end_line=10, bogus_param="hello"',
            available_tools={"strict_params": strict_params},
        )
        # Should NOT crash with "got an unexpected keyword argument"
        self.assertNotIn("Error", result)

    def test_unknown_kwargs_stripped_with_no_positional(self):
        """Kwargs stripping works when there are zero positional args."""
        def strict_params(path=""):
            return f"path={path}"

        result = self._fn(
            "strict_params",
            'path="foo.py", extra_kwarg=True',
            available_tools={"strict_params": strict_params},
        )
        self.assertNotIn("Error", result)

    def test_var_keyword_function_keeps_all_kwargs(self):
        """Functions with **kwargs should NOT have kwargs stripped."""
        def flexible(path="", **kwargs):
            return f"path={path}, extra={kwargs.get('extra', 'none')}"

        result = self._fn(
            "flexible",
            'path="foo.py", extra="kept"',
            available_tools={"flexible": flexible},
        )
        self.assertNotIn("Error", result)
        self.assertIn("kept", result)

    def test_combined_excess_positional_and_unknown_kwargs(self):
        """Both fixes work together: excess positional + unknown kwargs."""
        def tool(a, b=None):
            return f"a={a}, b={b}"

        result = self._fn(
            "tool",
            '"val", 1, 2, 3, bogus=True',
            available_tools={"tool": tool},
        )
        self.assertNotIn("Error", result)

    def test_read_lines_with_5_positional_no_crash(self):
        """Regression: read_lines('10, 20, 30, 40, 50') must not crash."""
        from core.tools import AVAILABLE_TOOLS
        result = self._fn(
            "read_lines",
            "10, 20, 30, 40, 50",
            available_tools=AVAILABLE_TOOLS,
        )
        # Should get a meaningful error about invalid path, not a TypeError
        self.assertNotIn("positional argument", result)

    def test_read_lines_with_unknown_kwarg_no_crash(self):
        """Regression: read_lines(..., bogus=True) must not crash."""
        from core.tools import AVAILABLE_TOOLS
        result = self._fn(
            "read_lines",
            'path="core/tools.py", start_line=1, end_line=5, bogus=True',
            available_tools=AVAILABLE_TOOLS,
        )
        self.assertNotIn("unexpected keyword", result)


# ---------------------------------------------------------------------------
# TestDisplayArgSummary — dict args in _extract_tool_args_summary
# ---------------------------------------------------------------------------

class TestDisplayArgSummary(unittest.TestCase):
    """Tests for _extract_tool_args_summary handling both str and dict."""

    def test_string_args(self):
        from lib.display import _extract_tool_args_summary
        result = _extract_tool_args_summary("read_file", 'path="foo.py"')
        self.assertIn("foo.py", result)

    def test_dict_args(self):
        from lib.display import _extract_tool_args_summary
        result = _extract_tool_args_summary("read_file", {"path": "foo.py"})
        self.assertIn("foo.py", result)

    def test_dict_args_read_lines(self):
        from lib.display import _extract_tool_args_summary
        result = _extract_tool_args_summary(
            "read_lines",
            {"path": "foo.py", "start_line": 10, "end_line": 20},
        )
        self.assertIn("foo.py", result)
        self.assertIn("10", result)
        self.assertIn("20", result)


if __name__ == "__main__":
    unittest.main()
