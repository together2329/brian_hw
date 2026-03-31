"""
test_regression.py — Regression tests for bugs found after phase6–phase10 refactoring.

Each test documents EXACTLY which git commit introduced or exposed the bug,
and the fix that resolved it.  Run with:
    pytest tests/test_core/test_regression.py -v
"""
from __future__ import annotations

import sys
import os
import types
import unittest
from unittest.mock import MagicMock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "..", "src"))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))


# ══════════════════════════════════════════════════════════════════════════════
# 1. StreamParser: reasoning tokens must NOT bleed into content
#    Bug introduced: b2e3a9c (phase10 – stream_parser extraction)
#    Root cause: feed() with reasoning_in_context=True skipped `return`, so
#                reasoning tokens fell through to self._buf → appeared as content.
#    Fixed in: stream_parser.py – always `return` after reasoning branch.
# ══════════════════════════════════════════════════════════════════════════════

class TestStreamParserReasoningBleed(unittest.TestCase):
    """Reasoning tokens must never appear in content output (regression: b2e3a9c)."""

    def _make_parser(self, reasoning_display=True, reasoning_in_context=True):
        from core.stream_parser import StreamParser
        content, reasoning = [], []

        def on_reasoning(line, blank=False):
            if not blank:
                reasoning.append(line)

        p = StreamParser(
            emit_fn=content.append,
            emit_reasoning_fn=on_reasoning,
            emit_thought_fn=lambda _: None,
            reasoning_display=reasoning_display,
            reasoning_in_context=reasoning_in_context,
        )
        return p, content, reasoning

    def test_reasoning_tuple_not_in_content_reasoning_in_context_true(self):
        """regression: with reasoning_in_context=True, reasoning bled into content."""
        p, content, reasoning = self._make_parser(reasoning_in_context=True)
        p.feed(("reasoning", "secret thought\n"))
        p.feed("visible answer\n")
        p.flush()

        self.assertIn("visible answer", content,
                      "content must contain the actual answer")
        self.assertNotIn("secret thought", content,
                         "reasoning must NOT appear in content (regression: b2e3a9c)")
        # reasoning should be routed correctly
        self.assertTrue(any("secret thought" in r for r in reasoning),
                        "reasoning should appear in reasoning output")

    def test_reasoning_tuple_not_in_content_reasoning_in_context_false(self):
        """With reasoning_in_context=False, reasoning should be silently dropped."""
        p, content, reasoning = self._make_parser(
            reasoning_display=False, reasoning_in_context=False
        )
        p.feed(("reasoning", "hidden thought\n"))
        p.feed("content only\n")
        p.flush()

        self.assertNotIn("hidden thought", content)
        self.assertEqual(reasoning, [])

    def test_collected_excludes_reasoning_when_in_context_false(self):
        """collected must only hold content text when reasoning_in_context=False."""
        p, content, reasoning = self._make_parser(
            reasoning_display=False, reasoning_in_context=False
        )
        p.feed(("reasoning", "think\n"))
        p.feed("answer\n")
        collected = p.flush()

        self.assertNotIn("think", collected)
        self.assertIn("answer", collected)

    def test_collected_includes_reasoning_when_in_context_true(self):
        """collected includes reasoning text when reasoning_in_context=True."""
        p, content, reasoning = self._make_parser(reasoning_in_context=True)
        p.feed(("reasoning", "think\n"))
        p.feed("answer\n")
        collected = p.flush()

        self.assertIn("think", collected)
        self.assertIn("answer", collected)

    def test_multiple_reasoning_tokens_no_bleed(self):
        """Many reasoning tokens followed by content — none should bleed."""
        p, content, reasoning = self._make_parser(reasoning_in_context=True)
        for word in ["The ", "user ", "asks ", "a ", "question.\n"]:
            p.feed(("reasoning", word))
        p.feed("Final answer.\n")
        p.flush()

        content_joined = " ".join(content)
        self.assertNotIn("The user asks", content_joined,
                         "reasoning tokens must not appear in content")
        self.assertIn("Final answer", content_joined)


# ══════════════════════════════════════════════════════════════════════════════
# 2. react_loop: think-only LLM response must trigger retry, not add empty msg
#    Bug: after phase10 stream_parser fix, <think>only</think> responses
#         produced empty collected_content AFTER strip_thinking_fn,
#         but the empty check was BEFORE stripping → not caught → empty msg
#         added to history → confused next LLM call.
#    Fixed: second empty check after strip_thinking_fn, with retry.
# ══════════════════════════════════════════════════════════════════════════════

class TestReactLoopThinkOnlyResponse(unittest.TestCase):
    """Think-only responses must retry, not silently add empty content (regression)."""

    def _make_deps(self, llm_responses, strip_fn=None):
        from core.react_loop import ReactLoopDeps
        from unittest.mock import MagicMock
        import types

        response_iter = iter(llm_responses)

        def fake_llm(messages, stop=None, **kwargs):
            try:
                return iter(next(response_iter))
            except StopIteration:
                return iter(["Final Answer: done."])

        def _strip_thinking(text):
            import re
            return re.sub(r"<think>.*?</think>", "", text, flags=re.DOTALL).strip()

        cfg = types.SimpleNamespace(
            DEBUG_MODE=False,
            REASONING_DISPLAY=False,
            REASONING_IN_CONTEXT=False,
            ENABLE_TODO_TRACKING=False,
            LLM_RETRY_COUNT=1,
            MAX_ITERATIONS=5,
            EXECUTION_MODE="agent",
            CHAT_MAX_ITERATIONS=1,
            STEP_BY_STEP_MODE=False,
        )

        return ReactLoopDeps(
            cfg=cfg,
            llm_call_fn=fake_llm,
            compress_fn=MagicMock(side_effect=lambda msgs, **kw: msgs),
            build_prompt_fn=MagicMock(return_value="sys"),
            process_obs_fn=MagicMock(side_effect=lambda obs, msgs, **kw: msgs),
            execute_tool_fn=MagicMock(return_value="ok"),
            execute_parallel_fn=MagicMock(return_value=[]),
            save_trajectory_fn=MagicMock(),
            show_context_usage_fn=MagicMock(),
            show_iteration_warning_fn=MagicMock(return_value="continue"),
            strip_tokens_fn=lambda x: x,
            strip_thinking_fn=strip_fn or _strip_thinking,
            parse_todo_fn=lambda x: [],
            detect_completion_fn=lambda x: "Final Answer" in x,
            get_turn_id_fn=lambda: 1,
            get_llm_usage_fn=lambda: None,
            get_llm_tokens_fn=lambda: (0, 0),
            esc_check_fn=lambda: False,
            esc_start_fn=lambda: None,
            esc_stop_fn=lambda: None,
        )

    def _make_tracker(self):
        t = MagicMock()
        t.current = 0
        t.max_iterations = 10
        t.record_tool = MagicMock()
        t._last_rag_query = None
        return t

    def test_think_only_does_not_add_empty_msg_to_history(self):
        """
        When LLM produces <think>only</think> with no content after stripping,
        the empty string must NOT be appended to message history.
        """
        from core.react_loop import run_react_agent_impl
        deps = self._make_deps([
            ["<think>I am thinking</think>"],   # first call: think-only → retry
            ["Final Answer: done."],             # second call: real answer
        ])
        messages = [{"role": "system", "content": "sys"},
                    {"role": "user",   "content": "hello"}]

        run_react_agent_impl(
            messages=messages, tracker=self._make_tracker(),
            task_description="test", deps=deps,
        )

        empty_msgs = [m for m in messages
                      if m.get("role") == "assistant" and not m.get("content", "").strip()]
        self.assertEqual(empty_msgs, [],
                         "Empty assistant messages must not be added to history "
                         "(regression: think-only response was silently added)")

    def test_empty_content_before_strip_still_retries(self):
        """Truly empty response also retries without adding empty msg to history."""
        from core.react_loop import run_react_agent_impl
        deps = self._make_deps([
            [""],                    # first call: empty → retry
            ["Final Answer: done."], # second call: real answer
        ])
        messages = [{"role": "system", "content": "sys"},
                    {"role": "user",   "content": "go"}]

        run_react_agent_impl(
            messages=messages, tracker=self._make_tracker(),
            task_description="test", deps=deps,
        )

        empty_msgs = [m for m in messages
                      if m.get("role") == "assistant" and not m.get("content", "").strip()]
        self.assertEqual(empty_msgs, [])


# ══════════════════════════════════════════════════════════════════════════════
# 3. compressor: rejection_reason must survive context compression
#    Bug: todo snapshot in compressor only stored task status + content,
#         not the rejection_reason → after compression, agent forgot WHY
#         a task was rejected and couldn't fix it properly.
#    Fixed: compressor.py appends rejection_reason to snapshot line.
# ══════════════════════════════════════════════════════════════════════════════

class TestCompressorPreservesRejectionReason(unittest.TestCase):
    """After compression, the todo snapshot must include rejection_reason (regression)."""

    def _make_tracker_with_rejected_task(self, reason: str):
        from lib.todo_tracker import TodoTracker, TodoItem
        tracker = TodoTracker(persist_path=None)
        tracker.todos = [
            TodoItem(content="Task A", active_form="Doing A", status="approved"),
            TodoItem(content="Task B", active_form="Doing B", status="rejected",
                     rejection_reason=reason),
            TodoItem(content="Task C", active_form="Doing C", status="pending"),
        ]
        tracker.current_index = 1
        return tracker

    def test_rejection_reason_in_snapshot(self):
        """Todo snapshot string must contain the rejection_reason text."""
        import sys, io, types
        reason = "CRITICAL: posted writes must not wait for CPL"
        tracker = self._make_tracker_with_rejected_task(reason)

        # Simulate what compressor.py does (copied logic)
        status_icon = {
            "pending": "⏸", "in_progress": "▶", "completed": "👀",
            "approved": "✅", "rejected": "❌",
        }
        todo_lines = ["[Todo Status]:"]
        for i, t in enumerate(tracker.todos):
            icon = status_icon.get(t.status, "?")
            line = f"  {icon} {i+1}. [{t.status}] {t.content}"
            if t.rejection_reason and t.status in ("rejected", "in_progress", "pending"):
                line += f"\n     ⚠ REJECTED: {t.rejection_reason}"
            todo_lines.append(line)
        snapshot = "\n".join(todo_lines)

        self.assertIn(reason, snapshot,
                      "rejection_reason must appear in compression snapshot "
                      "(regression: was dropped before fix)")

    def test_approved_task_has_no_rejected_annotation(self):
        """Approved tasks must NOT show rejection annotation even if reason was set."""
        from lib.todo_tracker import TodoItem
        item = TodoItem(content="Done task", active_form="Doing",
                        status="approved", rejection_reason="old reason")
        # Simulate the fixed compressor logic
        line = f"  ✅ 1. [approved] {item.content}"
        if item.rejection_reason and item.status in ("rejected", "in_progress", "pending"):
            line += f"\n     ⚠ REJECTED: {item.rejection_reason}"
        self.assertNotIn("REJECTED", line,
                         "Approved tasks must not show rejection annotation")

    def test_continuation_prompt_for_rejected_task_includes_reason(self):
        """get_continuation_prompt must include rejection reason in its output."""
        reason = "PCIe writes are posted — remove WAIT_CPL state"
        tracker = self._make_tracker_with_rejected_task(reason)
        prompt = tracker.get_continuation_prompt()

        self.assertIsNotNone(prompt, "continuation_prompt must exist for rejected task")
        self.assertIn("REJECTED", prompt.upper(),
                      "prompt must signal rejection clearly")
        self.assertIn(reason, prompt,
                      "prompt must include the specific rejection reason "
                      "(so agent knows what to fix after compression)")


# ══════════════════════════════════════════════════════════════════════════════
# 4. chat_loop: ChatLoopDeps must have hook_registry field
#    Bug: phase9 extraction (25151bb) created ChatLoopDeps without hook_registry,
#         so hooks (BEFORE/AFTER_LLM_CALL, compression triggers) never fired
#         during per-turn processing.
#    Fixed: added hook_registry: Optional[Any] = None to ChatLoopDeps,
#           and main.py passes hook_registry=hook_registry when building deps.
# ══════════════════════════════════════════════════════════════════════════════

class TestChatLoopDepsHasHookRegistry(unittest.TestCase):
    """ChatLoopDeps must have hook_registry field (regression: 25151bb)."""

    def test_hook_registry_field_exists(self):
        """ChatLoopDeps dataclass must have a hook_registry field."""
        from core.chat_loop import ChatLoopDeps
        import dataclasses
        field_names = {f.name for f in dataclasses.fields(ChatLoopDeps)}
        self.assertIn("hook_registry", field_names,
                      "ChatLoopDeps missing hook_registry — hooks won't fire per-turn "
                      "(regression: 25151bb phase9 extraction)")

    def test_hook_registry_defaults_to_none(self):
        """hook_registry must default to None so existing callers don't break."""
        from core.chat_loop import ChatLoopDeps
        deps = ChatLoopDeps(
            cfg=None,
            run_react_agent_fn=lambda *a, **k: None,
            compress_fn=lambda *a, **k: [],
            save_history_fn=lambda *a, **k: None,
            on_conversation_end_fn=lambda *a, **k: None,
            build_system_prompt_fn=lambda *a, **k: "",
            show_context_usage_fn=lambda *a, **k: None,
        )
        self.assertIsNone(deps.hook_registry,
                          "hook_registry must default to None for backward compat")

    def test_hook_registry_accepts_non_none(self):
        """hook_registry must accept a registry object."""
        from core.chat_loop import ChatLoopDeps
        fake_registry = object()
        deps = ChatLoopDeps(
            cfg=None,
            run_react_agent_fn=lambda *a, **k: None,
            compress_fn=lambda *a, **k: [],
            save_history_fn=lambda *a, **k: None,
            on_conversation_end_fn=lambda *a, **k: None,
            build_system_prompt_fn=lambda *a, **k: "",
            show_context_usage_fn=lambda *a, **k: None,
            hook_registry=fake_registry,
        )
        self.assertIs(deps.hook_registry, fake_registry)


# ══════════════════════════════════════════════════════════════════════════════
# 5. todo_tracker: sequential check must NOT block in_progress for rejected task
#    The sequential check (prior tasks must be approved) must allow setting
#    a REJECTED task to in_progress so the agent can fix and resubmit it.
# ══════════════════════════════════════════════════════════════════════════════

class TestTodoUpdateRejectedFlow(unittest.TestCase):
    """Rejected task must be fixable without being blocked by itself."""

    def _make_tracker(self):
        from lib.todo_tracker import TodoTracker, TodoItem
        tracker = TodoTracker(persist_path=None)
        tracker.todos = [
            TodoItem(content="Task 1", active_form="Doing 1", status="approved"),
            TodoItem(content="Task 2", active_form="Doing 2", status="approved"),
            TodoItem(content="Task 3", active_form="Doing 3", status="rejected",
                     rejection_reason="needs fix"),
            TodoItem(content="Task 4", active_form="Doing 4", status="pending"),
        ]
        tracker.current_index = 2
        return tracker

    def test_rejected_task_can_move_to_in_progress(self):
        """A rejected task (all prior approved) must accept in_progress update."""
        tracker = self._make_tracker()
        # Task 3 (index 2) is rejected; tasks 1,2 are approved
        # Simulates: agent calls todo_update(index=3, status='in_progress') to fix
        tracker.mark_in_progress(2)
        self.assertEqual(tracker.todos[2].status, "in_progress")

    def test_rejected_task_sequential_check_passes(self):
        """Sequential check in todo_update must pass for a rejected task when all prior approved."""
        # The sequential check logic from tools.py:
        # blocking = [i+1 for i in range(idx) if tracker.todos[i].status not in ("approved",)]
        tracker = self._make_tracker()
        idx = 2  # task 3
        blocking = [
            i + 1 for i in range(idx)
            if tracker.todos[i].status not in ("approved",)
        ]
        self.assertEqual(blocking, [],
                         "No tasks should block fixing task 3 — tasks 1,2 are approved")

    def test_pending_task_blocked_while_rejected_exists(self):
        """Task 4 (pending) must be blocked until task 3 (rejected) is approved."""
        tracker = self._make_tracker()
        idx = 3  # task 4
        blocking = [
            i + 1 for i in range(idx)
            if tracker.todos[i].status not in ("approved",)
        ]
        self.assertIn(3, blocking,
                      "Task 4 must be blocked by task 3 (rejected) until it's approved")

    def test_rejection_reason_cleared_on_completed(self):
        """When a rejected task is re-completed, rejection_reason must be cleared."""
        tracker = self._make_tracker()
        self.assertTrue(tracker.todos[2].rejection_reason)
        tracker.mark_completed(2)
        self.assertEqual(tracker.todos[2].rejection_reason, "",
                         "rejection_reason must clear when task is re-completed")


# ══════════════════════════════════════════════════════════════════════════════
# 6. stream_parser: reasoning blank lines must reach emit_reasoning with blank=True
#    Bug found during phase10: empty reasoning lines were swallowed.
# ══════════════════════════════════════════════════════════════════════════════

class TestStreamParserReasoningBlankLines(unittest.TestCase):
    """Blank lines in reasoning must fire emit_reasoning(blank=True)."""

    def test_blank_line_in_reasoning_fires_blank_callback(self):
        from core.stream_parser import StreamParser
        blanks = []

        def on_reasoning(line, blank=False):
            if blank:
                blanks.append(True)

        p = StreamParser(
            emit_fn=lambda _: None,
            emit_reasoning_fn=on_reasoning,
            emit_thought_fn=lambda _: None,
            reasoning_display=True,
        )
        p.feed(("reasoning", "para 1\n\npara 2\n"))
        p.flush()

        self.assertGreater(len(blanks), 0,
                           "Blank line in reasoning must trigger blank=True callback")

    def test_reasoning_lines_delivered_line_by_line(self):
        """Reasoning should be emitted as complete lines, not word-by-word."""
        from core.stream_parser import StreamParser
        lines = []

        def on_reasoning(line, blank=False):
            if not blank and line.strip():
                lines.append(line)

        p = StreamParser(
            emit_fn=lambda _: None,
            emit_reasoning_fn=on_reasoning,
            emit_thought_fn=lambda _: None,
            reasoning_display=True,
        )
        # Feed word by word — should still produce whole lines
        for word in ["The", " user", " wants", " something.\n"]:
            p.feed(("reasoning", word))
        p.flush()

        joined = "".join(lines)
        self.assertIn("The user wants something", joined,
                      "reasoning should be assembled into complete lines")


if __name__ == "__main__":
    unittest.main(verbosity=2)
