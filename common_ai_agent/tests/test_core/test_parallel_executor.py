"""
TDD tests for core/parallel_executor.py
Phase 8: extract execute_actions_parallel + _execute_batch_parallel from main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import time


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(**overrides):
    import types
    defaults = dict(
        ENABLE_REACT_PARALLEL=True,
        ENABLE_ENHANCED_PARALLEL=True,
        REACT_MAX_WORKERS=4,
        REACT_ACTION_TIMEOUT=30,
        PLAN_MODE_BLOCKED_TOOLS=set(),
        DEBUG_MODE=False,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _tool_fn(name, delay=0):
    """Return a tool function that records calls."""
    calls = []
    def fn(*args, **kwargs):
        if delay:
            time.sleep(delay)
        calls.append((args, kwargs))
        return f"result:{name}"
    fn.calls = calls
    fn.__name__ = name
    return fn


# ---------------------------------------------------------------------------
# TestExecuteBatchParallel
# ---------------------------------------------------------------------------

class TestExecuteBatchParallel(unittest.TestCase):
    def setUp(self):
        from core.parallel_executor import execute_batch_parallel
        self._fn = execute_batch_parallel

    def _call(self, batch, execute_tool_fn=None, cfg=None):
        if cfg is None:
            cfg = _make_cfg()
        if execute_tool_fn is None:
            execute_tool_fn = lambda name, args: f"ok:{name}"
        return self._fn(batch, execute_tool_fn=execute_tool_fn, cfg=cfg)

    def test_empty_batch_returns_empty(self):
        self.assertEqual(self._call([]), [])

    def test_returns_all_results(self):
        batch = [(0, "read_file", 'path="a.py"'), (1, "read_file", 'path="b.py"')]
        results = self._call(batch)
        self.assertEqual(len(results), 2)

    def test_result_tuple_has_4_elements(self):
        batch = [(0, "tool", "arg=1")]
        results = self._call(batch)
        self.assertEqual(len(results[0]), 4)

    def test_preserves_original_index(self):
        batch = [(5, "tool", "arg=1")]
        results = self._call(batch)
        self.assertEqual(results[0][0], 5)

    def test_tool_fn_called_with_name_and_args(self):
        called = []
        def track_fn(name, args):
            called.append((name, args))
            return "ok"
        batch = [(0, "my_tool", 'x="hello"')]
        self._call(batch, execute_tool_fn=track_fn)
        self.assertEqual(called[0], ("my_tool", 'x="hello"'))

    def test_exception_returns_error_string(self):
        def failing_fn(name, args):
            raise RuntimeError("boom")
        batch = [(0, "bad_tool", "")]
        results = self._call(batch, execute_tool_fn=failing_fn)
        self.assertIn("Error", results[0][3])

    def test_timeout_returns_error_string(self):
        cfg = _make_cfg(REACT_ACTION_TIMEOUT=0.01, REACT_MAX_WORKERS=1)
        def slow_fn(name, args):
            time.sleep(1)
            return "done"
        batch = [(0, "slow_tool", "")]
        results = self._call(batch, execute_tool_fn=slow_fn, cfg=cfg)
        self.assertIn("Timeout", results[0][3])

    def test_results_sorted_by_index(self):
        """Results should be in original index order."""
        batch = [(2, "c", ""), (0, "a", ""), (1, "b", "")]
        results = self._call(batch)
        indices = [r[0] for r in results]
        self.assertEqual(indices, sorted(indices))


# ---------------------------------------------------------------------------
# TestExecuteActionsParallel
# ---------------------------------------------------------------------------

class TestExecuteActionsParallel(unittest.TestCase):
    def setUp(self):
        from core.parallel_executor import execute_actions_parallel
        self._fn = execute_actions_parallel

    def _make_tracker(self):
        t = MagicMock()
        t.record_tool = MagicMock()
        return t

    def _call(self, actions, agent_mode="normal", cfg=None, execute_tool_fn=None, **kwargs):
        if cfg is None:
            cfg = _make_cfg()
        if execute_tool_fn is None:
            execute_tool_fn = lambda name, args: f"ok:{name}"
        tracker = self._make_tracker()
        return self._fn(
            actions,
            tracker=tracker,
            agent_mode=agent_mode,
            cfg=cfg,
            execute_tool_fn=execute_tool_fn,
            **kwargs,
        )

    def test_empty_actions_returns_empty(self):
        self.assertEqual(self._call([]), [])

    def test_returns_list(self):
        actions = [("read_file", 'path="a.py"', None)]
        result = self._call(actions)
        self.assertIsInstance(result, list)

    def test_result_has_correct_count(self):
        actions = [("read_file", 'path="a.py"', None), ("grep_file", 'pattern="x"', None)]
        results = self._call(actions)
        self.assertEqual(len(results), 2)

    def test_result_tuple_structure(self):
        actions = [("read_file", 'path="a.py"', None)]
        results = self._call(actions)
        idx, tool, args, obs = results[0]
        self.assertEqual(tool, "read_file")
        self.assertIsInstance(obs, str)

    def test_tracker_record_tool_called(self):
        actions = [("read_file", 'path="a.py"', None)]
        tracker = self._make_tracker()
        cfg = _make_cfg()
        self._fn(actions, tracker=tracker, agent_mode="normal", cfg=cfg,
                 execute_tool_fn=lambda n, a: "ok")
        tracker.record_tool.assert_called()

    def test_plan_mode_blocks_write_tools(self):
        cfg = _make_cfg(PLAN_MODE_BLOCKED_TOOLS={"write_file"})
        actions = [("write_file", 'path="x.py"', None)]
        results = self._call(actions, agent_mode="plan", cfg=cfg)
        self.assertIn("Plan Mode", results[0][3])

    def test_plan_mode_allows_read_tools(self):
        cfg = _make_cfg(PLAN_MODE_BLOCKED_TOOLS={"write_file"})
        actions = [("read_file", 'path="a.py"', None)]
        results = self._call(actions, agent_mode="plan", cfg=cfg)
        self.assertNotIn("Plan Mode", results[0][3])

    def test_results_sorted_by_index(self):
        actions = [("read_file", 'path="a.py"', None), ("grep_file", 'pattern="x"', None)]
        results = self._call(actions)
        indices = [r[0] for r in results]
        self.assertEqual(indices, sorted(indices))

    def test_parallel_disabled_uses_sequential(self):
        """ENABLE_REACT_PARALLEL=False → all tools run sequentially."""
        cfg = _make_cfg(ENABLE_REACT_PARALLEL=False)
        call_order = []
        def track_fn(name, args):
            call_order.append(name)
            return "ok"
        actions = [("read_file", 'path="a.py"', None), ("read_file", 'path="b.py"', None)]
        self._call(actions, cfg=cfg, execute_tool_fn=track_fn)
        self.assertEqual(len(call_order), 2)

    def test_action_tuple_without_hint(self):
        """Support (tool, args) 2-tuples as well as (tool, args, hint) 3-tuples."""
        actions = [("read_file", 'path="a.py"')]
        results = self._call(actions)
        self.assertEqual(len(results), 1)


if __name__ == "__main__":
    unittest.main()
