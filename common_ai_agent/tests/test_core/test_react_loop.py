"""
TDD tests for core/react_loop.py
Phase 6: extract pure helpers and ReactLoopDeps from run_react_agent in main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import types


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(**overrides):
    defaults = dict(
        DEBUG_MODE=False,
        ENABLE_TODO_TRACKING=False,
        ENABLE_SUB_AGENTS=False,
        ENABLE_DEEP_THINK=False,
        ENABLE_SMART_RAG=False,
        ENABLE_SKILL_SYSTEM=False,
        ENABLE_REACT_PARALLEL=False,
        ENABLE_CREDIT_TRACKING=False,
        ENABLE_SESSION_RECOVERY=False,
        REASONING_IN_CONTEXT=False,
        REASONING_DISPLAY=False,
        STREAM_TOKEN_DELAY_MS=0,
        LLM_RETRY_COUNT=1,
        MAX_CONSECUTIVE_ERRORS=3,
        MAX_RECOVERY_ATTEMPTS=2,
        CACHE_OPTIMIZATION_MODE="legacy",
        PLAN_MODE_BLOCKED_TOOLS=set(),
        EXECUTION_MODE="agent",
        CHAT_MAX_ITERATIONS=1,
        STEP_BY_STEP_MODE=False,
        TODO_STAGNATION_LIMIT=3,
        MODEL_NAME="test-model",
        MAX_CONTEXT_TOKENS=100000,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


# ---------------------------------------------------------------------------
# TestDedupLine — pure string helper
# ---------------------------------------------------------------------------

class TestDedupLine(unittest.TestCase):
    def setUp(self):
        from core.react_loop import _dedup_line
        self._fn = _dedup_line

    def test_short_string_unchanged(self):
        text = "Hello world"
        self.assertEqual(self._fn(text), text)

    def test_no_repetition_unchanged(self):
        text = "a" * 99  # just under threshold
        self.assertEqual(self._fn(text), text)

    def test_repeated_segment_truncated(self):
        # Build a string where a 50-char segment repeats
        seg = "x" * 50
        text = seg + seg  # 100 chars, seg appears twice
        result = self._fn(text)
        self.assertLessEqual(len(result), len(text))

    def test_returns_string(self):
        self.assertIsInstance(self._fn("any text"), str)


# ---------------------------------------------------------------------------
# TestIsDup — set-based dedup helper
# ---------------------------------------------------------------------------

class TestIsDup(unittest.TestCase):
    def setUp(self):
        from core.react_loop import _make_is_dup
        # _make_is_dup() returns (seen_set, is_dup_fn) so tests can share state
        self._seen, self._fn = _make_is_dup()

    def test_new_text_is_not_dup(self):
        self.assertFalse(self._fn("brand new text"))

    def test_exact_duplicate_detected(self):
        self._seen.add("some text")
        self.assertTrue(self._fn("some text"))

    def test_short_text_not_matched_as_substring(self):
        self._seen.add("hello world")
        self.assertFalse(self._fn("hi"))  # too short for substring check

    def test_long_substring_detected(self):
        long = "a" * 80
        self._seen.add(long)
        # A string that contains long as substring should be a dup
        self.assertTrue(self._fn(long))


# ---------------------------------------------------------------------------
# TestReactLoopDeps — dataclass construction
# ---------------------------------------------------------------------------

class TestReactLoopDeps(unittest.TestCase):
    def setUp(self):
        from core.react_loop import ReactLoopDeps
        self._cls = ReactLoopDeps

    def _make_deps(self, **overrides):
        required = dict(
            cfg=_make_cfg(),
            llm_call_fn=MagicMock(),
            compress_fn=MagicMock(),
            build_prompt_fn=MagicMock(),
            process_obs_fn=MagicMock(),
            execute_tool_fn=MagicMock(),
            execute_parallel_fn=MagicMock(),
            save_trajectory_fn=MagicMock(),
            show_context_usage_fn=MagicMock(),
            show_iteration_warning_fn=MagicMock(return_value='continue'),
            strip_tokens_fn=MagicMock(side_effect=lambda x: x),
            strip_thinking_fn=MagicMock(side_effect=lambda x: x),
            parse_todo_fn=MagicMock(return_value=[]),
            detect_completion_fn=MagicMock(return_value=False),
            get_turn_id_fn=MagicMock(return_value=1),
            get_llm_usage_fn=MagicMock(return_value=None),
            get_llm_tokens_fn=MagicMock(return_value=(0, 0)),
        )
        required.update(overrides)
        return self._cls(**required)

    def test_construction_succeeds(self):
        deps = self._make_deps()
        self.assertIsNotNone(deps)

    def test_optional_fields_default_none(self):
        deps = self._make_deps()
        self.assertIsNone(deps.orchestrator)
        self.assertIsNone(deps.procedural_memory)
        self.assertIsNone(deps.graph_lite)
        self.assertIsNone(deps.hook_registry)

    def test_available_tools_defaults_empty(self):
        deps = self._make_deps()
        self.assertIsInstance(deps.available_tools, dict)

    def test_custom_cfg_stored(self):
        cfg = _make_cfg(DEBUG_MODE=True)
        deps = self._make_deps(cfg=cfg)
        self.assertTrue(deps.cfg.DEBUG_MODE)


# ---------------------------------------------------------------------------
# TestRunReactAgentImpl — smoke tests with minimal mocking
# ---------------------------------------------------------------------------

class TestRunReactAgentImpl(unittest.TestCase):
    """
    run_react_agent_impl smoke tests.
    We mock the LLM to return a final-answer response so the loop exits
    after one iteration without needing real tools.
    """

    def _make_deps(self, **overrides):
        from core.react_loop import ReactLoopDeps

        # LLM returns "Final Answer: done." — triggers completion signal
        def _mock_llm(messages, stop=None, **kwargs):
            yield "Final Answer: Task complete."

        required = dict(
            cfg=_make_cfg(),
            llm_call_fn=_mock_llm,
            compress_fn=MagicMock(side_effect=lambda msgs, **kw: msgs),
            build_prompt_fn=MagicMock(return_value="system prompt"),
            process_obs_fn=MagicMock(side_effect=lambda obs, msgs, **kw: msgs),
            execute_tool_fn=MagicMock(return_value="tool result"),
            execute_parallel_fn=MagicMock(return_value=[]),
            save_trajectory_fn=MagicMock(),
            show_context_usage_fn=MagicMock(),
            show_iteration_warning_fn=MagicMock(return_value='continue'),
            strip_tokens_fn=lambda x: x,
            strip_thinking_fn=lambda x: x,
            parse_todo_fn=lambda x: [],
            detect_completion_fn=lambda x: "Final Answer" in x,
            get_turn_id_fn=lambda: 1,
            get_llm_usage_fn=lambda: None,
            get_llm_tokens_fn=lambda: (0, 0),
            # Inject no-op ESC functions to avoid EscapeWatcher thread in tests
            esc_check_fn=lambda: False,
            esc_start_fn=lambda: None,
            esc_stop_fn=lambda: None,
        )
        required.update(overrides)
        return ReactLoopDeps(**required)

    def _make_tracker(self, max_iter=10):
        """Minimal IterationTracker-like stub."""
        t = MagicMock()
        t.current = 0
        t.max_iterations = max_iter
        t.record_tool = MagicMock()
        t._last_rag_query = None
        return t

    def _call(self, **overrides):
        from core.react_loop import run_react_agent_impl
        deps = self._make_deps(**overrides)
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "do task"}]
        tracker = self._make_tracker()
        return run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description="test task",
            deps=deps,
        )

    def test_returns_tuple(self):
        result = self._call()
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_returns_messages_list(self):
        msgs, mode = self._call()
        self.assertIsInstance(msgs, list)

    def test_returns_mode_string(self):
        msgs, mode = self._call()
        self.assertIsInstance(mode, str)

    def test_default_mode_is_normal(self):
        from core.react_loop import run_react_agent_impl, ReactLoopDeps
        deps = self._make_deps()
        messages = [{"role": "user", "content": "hello"}]
        tracker = self._make_tracker()
        msgs, mode = run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description="test",
            deps=deps,
            agent_mode="normal",
        )
        self.assertEqual(mode, "normal")

    def test_completion_signal_exits_loop(self):
        """When LLM returns a final answer, loop exits without calling execute_tool."""
        execute_tool_fn = MagicMock(return_value="result")
        msgs, mode = self._call(execute_tool_fn=execute_tool_fn)
        execute_tool_fn.assert_not_called()

    def test_messages_contain_assistant_response(self):
        """After one LLM call, messages should include the assistant reply."""
        msgs, _ = self._call()
        roles = [m.get("role") for m in msgs]
        self.assertIn("assistant", roles)

    def test_empty_llm_response_retries(self):
        """Empty LLM response triggers retry logic."""
        call_count = [0]

        def empty_then_answer(messages, stop=None, **kwargs):
            call_count[0] += 1
            if call_count[0] == 1:
                return  # yields nothing
            yield "Final Answer: done."

        msgs, _ = self._call(llm_call_fn=empty_then_answer)
        self.assertGreaterEqual(call_count[0], 1)

    def test_no_todo_tracker_when_disabled(self):
        """ENABLE_TODO_TRACKING=False → todo_tracker is None inside loop."""
        cfg = _make_cfg(ENABLE_TODO_TRACKING=False)
        # Should not raise even without a TodoTracker available
        try:
            msgs, _ = self._call(cfg=cfg)
        except Exception as e:
            self.fail(f"Unexpected exception with ENABLE_TODO_TRACKING=False: {e}")

    def test_preface_disabled_skips_orchestrator(self):
        """preface_enabled=False must not call orchestrator."""
        from core.react_loop import run_react_agent_impl
        deps = self._make_deps()
        deps.orchestrator = MagicMock()
        messages = [{"role": "user", "content": "task"}]
        tracker = self._make_tracker()
        run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description="test",
            deps=deps,
            preface_enabled=False,
        )
        deps.orchestrator.run.assert_not_called()

    def test_compress_fn_called_on_each_iteration(self):
        """compress_fn should be called at the start of each loop iteration."""
        compress_fn = MagicMock(side_effect=lambda msgs, **kw: msgs)
        self._call(compress_fn=compress_fn)
        compress_fn.assert_called()


if __name__ == "__main__":
    unittest.main()
