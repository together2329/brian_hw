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


if __name__ == "__main__":
    unittest.main()
