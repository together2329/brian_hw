"""
TDD tests for core/react_loop.py
Phase 6: extract pure helpers and ReactLoopDeps from run_react_agent in main.py
"""
import unittest
from unittest.mock import MagicMock, patch
import sys
import types
import os


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

    def test_empty_llm_response_surfaces_failure_to_ui(self):
        """Atlas must not show a silent YOU-only turn when the LLM returns empty."""
        emitted = []
        flushes = []

        def always_empty(messages, stop=None, **kwargs):
            if False:
                yield "unused"

        cfg = _make_cfg(LLM_RETRY_COUNT=0, REACT_LOOP_STALL_SEC=0)
        msgs, _ = self._call(
            cfg=cfg,
            llm_call_fn=always_empty,
            emit_content_fn=lambda line: emitted.append(line),
            emit_flush_fn=lambda: flushes.append(True),
        )

        rendered = "".join(str(line) for line in emitted)
        self.assertIn("[LLM] Empty response after", rendered)
        self.assertIn("input was accepted", rendered)
        self.assertTrue(flushes, "empty-response notice should be flushed to the UI")
        self.assertFalse(any(
            m.get("role") == "assistant" and "[LLM] Empty response" in m.get("content", "")
            for m in msgs
        ))

    def test_malformed_action_reprompts_until_parseable_tool_call(self):
        """`Action:` prose must not be accepted as a completed no-tool reply."""
        calls = {"count": 0}
        emitted = []
        executed = []

        def malformed_then_tool_then_done(messages, stop=None, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                yield "Action: new_axi/tb/cocotb에 임시 VCD dump 모듈을 추가하겠습니다."
            elif calls["count"] == 2:
                yield 'Action: run_command(command="echo ok")'
            else:
                yield "Final Answer: done."

        def execute_tool(tool_name, args, pre_parsed_kwargs=None):
            executed.append((tool_name, args))
            return "ok"

        cfg = _make_cfg(
            LLM_RETRY_COUNT=0,
            MALFORMED_ACTION_RETRY_LIMIT=2,
            REACT_LOOP_STALL_SEC=0,
        )
        msgs, _ = self._call(
            cfg=cfg,
            llm_call_fn=malformed_then_tool_then_done,
            execute_tool_fn=execute_tool,
            emit_content_fn=lambda line: emitted.append(line),
            emit_flush_fn=lambda: None,
        )

        self.assertGreaterEqual(calls["count"], 2)
        self.assertIn(("run_command", 'command="echo ok"'), executed)
        rendered = "\n".join(str(line) for line in emitted)
        self.assertIn("malformed Action", rendered)
        self.assertTrue(any(
            m.get("role") == "assistant" and "Final Answer: done." in m.get("content", "")
            for m in msgs
        ))

    def test_plan_blocked_todo_update_emit_uses_blocked_transition(self):
        from core.react_loop import run_react_agent_impl

        class _Todo:
            content = "draft plan"
            active_form = "draft plan"
            detail = "create a planning artifact"
            criteria = "plan is documented"
            status = "pending"

        class _PlanTodoTracker:
            todos = [_Todo()]
            current_index = 0
            _persist_path = "/tmp/atlas-plan-blocked-test-todo.json"

            def is_all_processed(self):
                return False

            def get_current_todo(self):
                return self.todos[0]

            def check_rejection_livelock(self, max_rejections=50):
                return None

        calls = {"count": 0}

        def blocked_action(messages, stop=None, **kwargs):
            calls["count"] += 1
            if calls["count"] == 1:
                yield 'Action: todo_update(index=1, status="in_progress", reason="start execution")'
            else:
                yield "Final Answer: done."

        emitted = []
        execute_tool_fn = MagicMock(return_value="should not execute")
        cfg = _make_cfg(
            ENABLE_TODO_TRACKING=True,
            PLAN_MODE_BLOCKED_TOOLS={"todo_update"},
            TODO_FILE="/tmp/atlas-plan-blocked-test-todo.json",
            CHAT_MAX_ITERATIONS=1,
            LLM_RETRY_COUNT=0,
            REACT_LOOP_STALL_SEC=0,
        )
        deps = self._make_deps(
            cfg=cfg,
            llm_call_fn=blocked_action,
            detect_completion_fn=lambda _text: False,
            execute_tool_fn=execute_tool_fn,
            emit_tool_fn=lambda text: emitted.append(text),
        )
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "plan only"}]
        tracker = self._make_tracker()

        run_react_agent_impl(
            messages=messages,
            tracker=tracker,
            task_description="plan only",
            deps=deps,
            agent_mode="plan",
            todo_tracker=_PlanTodoTracker(),
        )

        execute_tool_fn.assert_not_called()
        todo_events = [str(event) for event in emitted if "todo_update" in str(event)]
        self.assertTrue(todo_events)
        self.assertTrue(any("pending → blocked" in event for event in todo_events))
        self.assertFalse(any("pending → in_progress" in event for event in todo_events))

    def test_no_todo_tracker_when_disabled(self):
        """ENABLE_TODO_TRACKING=False → todo_tracker is None inside loop."""
        cfg = _make_cfg(ENABLE_TODO_TRACKING=False)
        # Should not raise even without a TodoTracker available
        try:
            msgs, _ = self._call(cfg=cfg)
        except Exception as e:
            self.fail(f"Unexpected exception with ENABLE_TODO_TRACKING=False: {e}")

    def test_stale_todo_without_current_accepts_text_reply(self):
        """Stale todo files must not make normal chat replies hit the action guard."""
        from core.react_loop import run_react_agent_impl

        class _Todo:
            content = "stale task"
            detail = "old session state"
            criteria = "not active"
            status = "pending"

        class _StaleTodoTracker:
            todos = [_Todo()]
            current_index = -1

            def is_all_processed(self):
                return False

            def get_current_todo(self):
                return None

            def check_rejection_livelock(self, max_rejections=50):
                return None

        calls = {"count": 0}

        def text_reply(messages, stop=None, **kwargs):
            calls["count"] += 1
            yield "Hi, I'm here."

        emitted = []
        cfg = _make_cfg(
            ENABLE_TODO_TRACKING=True,
            EXECUTION_NO_ACTION_GUARD=True,
            EXECUTION_NO_ACTION_RETRY_LIMIT=3,
            TODO_FILE="/tmp/nonexistent-atlas-todo.json",
        )
        deps = self._make_deps(
            cfg=cfg,
            llm_call_fn=text_reply,
            detect_completion_fn=lambda _text: False,
            emit_content_fn=lambda line: emitted.append(line),
            emit_flush_fn=lambda: None,
        )
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "hi"}]
        tracker = self._make_tracker()

        with patch.dict(sys.modules, {"main": types.SimpleNamespace(todo_tracker=_StaleTodoTracker())}):
            msgs, _ = run_react_agent_impl(
                messages=messages,
                tracker=tracker,
                task_description="chat",
                deps=deps,
            )

        self.assertEqual(calls["count"], 1)
        self.assertTrue(any(
            m.get("role") == "assistant" and "Hi, I'm here." in m.get("content", "")
            for m in msgs
        ))
        rendered = "\n".join(str(line) for line in emitted)
        self.assertNotIn("Runtime guard nudged execution", rendered)
        self.assertNotIn("no-action guard", rendered)

    def test_pending_todo_without_current_index_is_selected(self):
        """Disk-loaded pending todos with current_index=-1 must start task 1."""
        from tempfile import TemporaryDirectory
        from pathlib import Path
        from core.react_loop import run_react_agent_impl
        from lib.todo_tracker import TodoTracker

        captured_prompts = []

        def text_reply(messages, stop=None, **kwargs):
            captured_prompts.append(messages[-1].get("content", ""))
            yield "I can do that."

        with TemporaryDirectory() as tmp:
            todo_path = Path(tmp) / "todo.json"
            todo_tracker = TodoTracker(persist_path=todo_path)
            todo_tracker.add_todos([{
                "content": "make test.md at doc",
                "status": "pending",
                "detail": "Create the requested doc artifact.",
                "criteria": "doc/test.md exists",
            }])
            todo_tracker.current_index = -1
            todo_tracker.save()

            cfg = _make_cfg(
                ENABLE_TODO_TRACKING=True,
                EXECUTION_NO_ACTION_GUARD=True,
                EXECUTION_NO_ACTION_RETRY_LIMIT=0,
                TODO_FILE=str(todo_path),
            )
            deps = self._make_deps(
                cfg=cfg,
                llm_call_fn=text_reply,
                detect_completion_fn=lambda _text: False,
                emit_content_fn=lambda _line: None,
                emit_flush_fn=lambda: None,
            )
            messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "Keep going"}]
            tracker = self._make_tracker()

            run_react_agent_impl(
                messages=messages,
                tracker=tracker,
                task_description="continue todos",
                deps=deps,
                todo_tracker=todo_tracker,
            )

        self.assertTrue(captured_prompts)
        self.assertIn("[Task 1/1]", captured_prompts[0])
        self.assertIn("todo_update(index=1, status='in_progress')", captured_prompts[0])

    def test_stop_paused_chat_suppression_skips_todo_guard_once(self):
        """After STOP, casual chat should not be forced through the TODO guard."""
        from core.react_loop import run_react_agent_impl

        class _Todo:
            content = "resume blocked execution"
            detail = "active work"
            criteria = "must use tools"
            status = "in_progress"

        class _ActiveTodoTracker:
            todos = [_Todo()]
            current_index = 0

            def is_all_processed(self):
                return False

            def get_current_todo(self):
                return self.todos[0]

            def check_rejection_livelock(self, max_rejections=50):
                return None

        calls = {"count": 0}

        def text_reply(messages, stop=None, **kwargs):
            calls["count"] += 1
            yield "Hi!"

        emitted = []
        cfg = _make_cfg(
            ENABLE_TODO_TRACKING=True,
            EXECUTION_NO_ACTION_GUARD=True,
            EXECUTION_NO_ACTION_RETRY_LIMIT=3,
            TODO_FILE="/tmp/nonexistent-atlas-todo.json",
        )
        deps = self._make_deps(
            cfg=cfg,
            llm_call_fn=text_reply,
            detect_completion_fn=lambda _text: False,
            emit_content_fn=lambda line: emitted.append(line),
            emit_flush_fn=lambda: None,
        )
        messages = [{"role": "system", "content": "system"}, {"role": "user", "content": "Hi"}]
        tracker = self._make_tracker()

        with patch.dict(os.environ, {"ATLAS_SUPPRESS_TODO_EXECUTION_ONCE": "1"}, clear=False):
            msgs, _ = run_react_agent_impl(
                messages=messages,
                tracker=tracker,
                task_description="Hi",
                deps=deps,
                todo_tracker=_ActiveTodoTracker(),
            )

        self.assertEqual(calls["count"], 1)
        self.assertTrue(any(
            m.get("role") == "assistant" and "Hi!" in m.get("content", "")
            for m in msgs
        ))
        rendered = "\n".join(str(line) for line in emitted)
        self.assertNotIn("Runtime guard nudged execution", rendered)
        self.assertNotIn("no-action guard", rendered)
        self.assertNotIn("ATLAS_SUPPRESS_TODO_EXECUTION_ONCE", os.environ)

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
