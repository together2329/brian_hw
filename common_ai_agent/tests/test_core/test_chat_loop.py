"""
TDD tests for core/chat_loop.py
Phase 9: extract per-turn processing from chat_loop() in main.py

Strategy:
  - ChatLoopState  : mutable turn-to-turn state (messages, agent_mode, ...)
  - ChatLoopDeps   : injected callables (run_react_agent_fn, compress_fn, ...)
  - process_chat_turn(user_input, state, deps) → (new_state, control)
      control: "continue" | "break" | "skip"
"""
import unittest
from unittest.mock import MagicMock
import types


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(**overrides):
    defaults = dict(
        DEBUG_MODE=False,
        ENABLE_TODO_TRACKING=False,
        ENABLE_COMPRESSION=False,
        PLAN_MODE_BLOCKED_TOOLS=set(),
        STEP_BY_STEP_MODE=False,
        MAX_ITERATIONS=10,
        CURATOR_INTERVAL=5,
    )
    defaults.update(overrides)
    return types.SimpleNamespace(**defaults)


def _make_deps(**overrides):
    from core.chat_loop import ChatLoopDeps

    def _mock_react(messages, tracker, task, **kw):
        messages = list(messages) + [{"role": "assistant", "content": "done"}]
        return messages, kw.get("agent_mode", "normal")

    defaults = dict(
        cfg=_make_cfg(),
        run_react_agent_fn=_mock_react,
        compress_fn=MagicMock(side_effect=lambda msgs, **kw: msgs),
        save_history_fn=MagicMock(),
        on_conversation_end_fn=MagicMock(),
        build_system_prompt_fn=MagicMock(return_value="system"),
        show_context_usage_fn=MagicMock(),
        slash_registry=None,
        context_tracker=None,
        curator=None,
    )
    defaults.update(overrides)
    return ChatLoopDeps(**defaults)


def _make_state(**overrides):
    from core.chat_loop import ChatLoopState
    defaults = dict(
        messages=[{"role": "user", "content": "hi"}],
        agent_mode="normal",
    )
    defaults.update(overrides)
    return ChatLoopState(**defaults)


def _call(user_input, state=None, deps=None):
    from core.chat_loop import process_chat_turn
    if state is None:
        state = _make_state()
    if deps is None:
        deps = _make_deps()
    return process_chat_turn(user_input, state, deps)


# ---------------------------------------------------------------------------
# TestChatLoopState
# ---------------------------------------------------------------------------

class TestChatLoopState(unittest.TestCase):
    def test_construction(self):
        from core.chat_loop import ChatLoopState
        s = ChatLoopState(messages=[])
        self.assertEqual(s.agent_mode, "normal")

    def test_default_fields(self):
        from core.chat_loop import ChatLoopState
        s = ChatLoopState(messages=[])
        self.assertEqual(s.rolling_window_size, 0)
        self.assertEqual(s.conversation_count, 0)
        self.assertTrue(s.is_first_turn)
        self.assertIsNone(s.full_messages)
        self.assertIsNone(s.todo_tracker)


# ---------------------------------------------------------------------------
# TestChatLoopDeps
# ---------------------------------------------------------------------------

class TestChatLoopDeps(unittest.TestCase):
    def test_construction_succeeds(self):
        deps = _make_deps()
        self.assertIsNotNone(deps)

    def test_optional_fields_default_none(self):
        deps = _make_deps()
        self.assertIsNone(deps.curator)
        self.assertIsNone(deps.context_tracker)


# ---------------------------------------------------------------------------
# TestProcessChatTurn — control flow
# ---------------------------------------------------------------------------

class TestControlFlow(unittest.TestCase):

    def test_exit_returns_break(self):
        _, ctrl = _call("exit")
        self.assertEqual(ctrl, "break")

    def test_quit_returns_break(self):
        _, ctrl = _call("quit")
        self.assertEqual(ctrl, "break")

    def test_exit_case_insensitive(self):
        _, ctrl = _call("EXIT")
        self.assertEqual(ctrl, "break")

    def test_empty_input_returns_skip(self):
        _, ctrl = _call("")
        self.assertEqual(ctrl, "skip")

    def test_whitespace_only_returns_skip(self):
        _, ctrl = _call("   ")
        self.assertEqual(ctrl, "skip")

    def test_normal_input_returns_continue(self):
        _, ctrl = _call("do something")
        self.assertEqual(ctrl, "continue")

    def test_returns_tuple(self):
        result = _call("hello")
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)

    def test_new_state_returned(self):
        state = _make_state()
        new_state, _ = _call("hello", state=state)
        self.assertIsNotNone(new_state)


# ---------------------------------------------------------------------------
# TestProcessChatTurn — normal turn
# ---------------------------------------------------------------------------

class TestNormalTurn(unittest.TestCase):

    def test_run_react_agent_called(self):
        called = []
        def mock_react(msgs, tracker, task, **kw):
            called.append(task)
            return msgs + [{"role": "assistant", "content": "ok"}], "normal"
        deps = _make_deps(run_react_agent_fn=mock_react)
        _call("do the task", deps=deps)
        self.assertEqual(len(called), 1)

    def test_assistant_message_added(self):
        state, _ = _call("do task")
        roles = [m.get("role") for m in state.messages]
        self.assertIn("assistant", roles)

    def test_conversation_count_incremented(self):
        state = _make_state()
        state.conversation_count = 3
        new_state, _ = _call("hello", state=state)
        self.assertEqual(new_state.conversation_count, 4)

    def test_is_first_turn_set_false_after_turn(self):
        state = _make_state()
        self.assertTrue(state.is_first_turn)
        new_state, _ = _call("first message", state=state)
        self.assertFalse(new_state.is_first_turn)

    def test_save_history_called(self):
        save_fn = MagicMock()
        deps = _make_deps(save_history_fn=save_fn)
        _call("do task", deps=deps)
        save_fn.assert_called()

    def test_plan_q_transitions_to_plan(self):
        """After a turn in plan_q mode, agent_mode should become 'plan'."""
        def mock_react(msgs, tracker, task, **kw):
            return msgs + [{"role": "assistant", "content": "plan ready"}], "plan_q"
        deps = _make_deps(run_react_agent_fn=mock_react)
        state = _make_state(agent_mode="plan_q")
        new_state, _ = _call("start plan", state=state, deps=deps)
        self.assertEqual(new_state.agent_mode, "plan")


# ---------------------------------------------------------------------------
# TestPlanModeConfirmation
# ---------------------------------------------------------------------------

class TestPlanModeConfirmation(unittest.TestCase):

    def _plan_state(self):
        return _make_state(agent_mode="plan", messages=[
            {"role": "system", "content": "sys"},
            {"role": "user", "content": "plan something"},
        ])

    def test_y_confirms_and_switches_to_normal(self):
        state = self._plan_state()
        new_state, ctrl = _call("y", state=state)
        self.assertEqual(new_state.agent_mode, "normal")

    def test_yes_confirms(self):
        state = self._plan_state()
        new_state, _ = _call("yes", state=state)
        self.assertEqual(new_state.agent_mode, "normal")

    def test_n_cancels_stays_plan(self):
        state = self._plan_state()
        new_state, ctrl = _call("n", state=state)
        self.assertEqual(new_state.agent_mode, "plan")

    def test_typo_returns_skip(self):
        """Single char non-slash, non-y/n → skip (don't waste LLM call)."""
        state = self._plan_state()
        _, ctrl = _call("]", state=state)
        self.assertEqual(ctrl, "skip")

    def test_feedback_text_passes_to_react(self):
        """Long feedback text in plan mode should call run_react_agent."""
        called = []
        def mock_react(msgs, tracker, task, **kw):
            called.append(True)
            return msgs + [{"role": "assistant", "content": "updated plan"}], "plan"
        deps = _make_deps(run_react_agent_fn=mock_react)
        state = self._plan_state()
        _call("Please change the approach to use async", state=state, deps=deps)
        self.assertTrue(len(called) > 0)


# ---------------------------------------------------------------------------
# TestAutoCompression
# ---------------------------------------------------------------------------

class TestAutoCompression(unittest.TestCase):

    def test_compress_called_when_threshold_exceeded(self):
        compress_fn = MagicMock(side_effect=lambda msgs, **kw: msgs)
        deps = _make_deps(compress_fn=compress_fn)
        state = _make_state()
        state.auto_compression_threshold = 1
        # Add enough non-system messages to exceed threshold
        state.messages = [
            {"role": "user", "content": "a"},
            {"role": "assistant", "content": "b"},
            {"role": "user", "content": "c"},
        ]
        _call("new message", state=state, deps=deps)
        compress_fn.assert_called()

    def test_compress_not_called_when_threshold_zero(self):
        compress_fn = MagicMock(side_effect=lambda msgs, **kw: msgs)
        deps = _make_deps(compress_fn=compress_fn)
        state = _make_state()
        state.auto_compression_threshold = 0
        _call("new message", state=state, deps=deps)
        compress_fn.assert_not_called()


if __name__ == "__main__":
    unittest.main()
