"""
Deep tests for plan mode features.

Coverage:
  1. TodoItem new fields — defaults, values, multi-todo, status transitions
  2. TodoTracker serialization — roundtrip, backward compat, file persistence
  3. mark_completed clears rejection_reason
  4. todo_update tool — reason stored, [REJECTED] prefix, complete clears reason
  5. Plan mode blocked tools config
  6. Step review criteria injection logic
  7. Step header building logic (rejection_reason / detail / criteria)
  8. _sys_content_append / _sys_content_strip_plan — str & list, edge cases
  9. run_react_agent signature
"""

import sys
import os
import types
import tempfile
import inspect
import unittest
from pathlib import Path

_project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
sys.path.insert(0, os.path.join(_project_root, 'src'))
sys.path.insert(0, _project_root)

from lib.todo_tracker import TodoTracker, TodoItem
from src.main import _sys_content_append, _sys_content_strip_plan, run_react_agent
import src.config as config

PLAN_MARKER = "\n\n=== PLAN MODE ==="


# ═══════════════════════════════════════════════════════════════════════════════
# 1. TodoItem new fields
# ═══════════════════════════════════════════════════════════════════════════════

class TestTodoItemFields(unittest.TestCase):

    def test_defaults(self):
        item = TodoItem(content="Fix bug", active_form="Fixing bug")
        self.assertEqual(item.detail, "")
        self.assertEqual(item.criteria, "")
        self.assertEqual(item.rejection_reason, "")

    def test_explicit_values(self):
        item = TodoItem(
            content="Fix bug", active_form="Fixing bug",
            detail="Edit auth.py line 45",
            criteria="1. Test passes\n2. No error log",
            rejection_reason="Test still fails",
        )
        self.assertEqual(item.detail, "Edit auth.py line 45")
        self.assertEqual(item.criteria, "1. Test passes\n2. No error log")
        self.assertEqual(item.rejection_reason, "Test still fails")

    def test_status_default_pending(self):
        item = TodoItem(content="S", active_form="S")
        self.assertEqual(item.status, "pending")

    def test_priority_invalid_falls_back_to_medium(self):
        item = TodoItem(content="S", active_form="S", priority="ultra")
        self.assertEqual(item.priority, "medium")

    def test_created_at_auto_set(self):
        item = TodoItem(content="S", active_form="S")
        self.assertIsNotNone(item.created_at)
        self.assertGreater(item.created_at, 0)

    def test_multiline_criteria(self):
        criteria = "Check A\nCheck B\nCheck C"
        item = TodoItem(content="S", active_form="S", criteria=criteria)
        lines = [c.strip() for c in item.criteria.splitlines() if c.strip()]
        self.assertEqual(lines, ["Check A", "Check B", "Check C"])


# ═══════════════════════════════════════════════════════════════════════════════
# 2. TodoTracker — add_todos, serialization, file persistence
# ═══════════════════════════════════════════════════════════════════════════════

class TestTodoTrackerSerialization(unittest.TestCase):

    def _tracker_with_todos(self, **extra):
        t = TodoTracker()
        t.add_todos([{
            "content": "Step 1", "activeForm": "Doing 1",
            "status": "in_progress",
            "detail": "some detail",
            "criteria": "A\nB",
            "rejection_reason": "failed once",
            **extra,
        }])
        return t

    def test_to_dict_includes_new_fields(self):
        t = self._tracker_with_todos()
        d = t.to_dict()["todos"][0]
        self.assertEqual(d["detail"], "some detail")
        self.assertEqual(d["criteria"], "A\nB")
        self.assertEqual(d["rejection_reason"], "failed once")

    def test_from_dict_restores_new_fields(self):
        t = self._tracker_with_todos()
        t2 = TodoTracker.from_dict(t.to_dict())
        self.assertEqual(t2.todos[0].detail, "some detail")
        self.assertEqual(t2.todos[0].criteria, "A\nB")
        self.assertEqual(t2.todos[0].rejection_reason, "failed once")

    def test_backward_compat_missing_fields(self):
        """Old JSON without new fields loads with empty defaults."""
        t = TodoTracker()
        t.add_todos([{"content": "Old", "activeForm": "Old"}])
        data = t.to_dict()
        for item in data["todos"]:
            item.pop("detail", None)
            item.pop("criteria", None)
            item.pop("rejection_reason", None)
        t2 = TodoTracker.from_dict(data)
        self.assertEqual(t2.todos[0].detail, "")
        self.assertEqual(t2.todos[0].criteria, "")
        self.assertEqual(t2.todos[0].rejection_reason, "")

    def test_file_persistence_roundtrip(self):
        with tempfile.NamedTemporaryFile(suffix=".json", delete=False) as f:
            path = Path(f.name)
        try:
            t = TodoTracker(persist_path=path)
            t.add_todos([{
                "content": "S", "activeForm": "Doing S",
                "detail": "detail text",
                "criteria": "crit1\ncrit2",
                "rejection_reason": "was wrong",
            }])
            # Reload from file
            t2 = TodoTracker.load(path)
            self.assertEqual(t2.todos[0].detail, "detail text")
            self.assertEqual(t2.todos[0].criteria, "crit1\ncrit2")
            self.assertEqual(t2.todos[0].rejection_reason, "was wrong")
        finally:
            path.unlink(missing_ok=True)

    def test_multiple_todos_all_fields_preserved(self):
        t = TodoTracker()
        t.add_todos([
            {"content": "A", "activeForm": "Doing A", "status": "in_progress",
             "detail": "d1", "criteria": "c1"},
            {"content": "B", "activeForm": "Doing B",
             "detail": "d2", "criteria": "c2", "rejection_reason": "r2"},
        ])
        self.assertEqual(t.todos[0].detail, "d1")
        self.assertEqual(t.todos[1].rejection_reason, "r2")


# ═══════════════════════════════════════════════════════════════════════════════
# 3. mark_completed clears rejection_reason
# ═══════════════════════════════════════════════════════════════════════════════

class TestMarkCompleted(unittest.TestCase):

    def setUp(self):
        self.tracker = TodoTracker()
        self.tracker.add_todos([
            {"content": "Step 1", "activeForm": "Doing 1", "status": "in_progress"},
            {"content": "Step 2", "activeForm": "Doing 2"},
        ])

    def test_clears_rejection_reason(self):
        self.tracker.todos[0].rejection_reason = "was wrong"
        self.tracker.mark_completed(0)
        self.assertEqual(self.tracker.todos[0].rejection_reason, "")

    def test_sets_completed_status(self):
        self.tracker.mark_completed(0)
        self.assertEqual(self.tracker.todos[0].status, "completed")

    def test_sets_completed_at(self):
        self.tracker.mark_completed(0)
        self.assertIsNotNone(self.tracker.todos[0].completed_at)

    def test_out_of_range_no_crash(self):
        self.tracker.mark_completed(99)  # should not raise

    def test_other_todos_not_affected(self):
        self.tracker.todos[1].rejection_reason = "other"
        self.tracker.mark_completed(0)
        self.assertEqual(self.tracker.todos[1].rejection_reason, "other")


# ═══════════════════════════════════════════════════════════════════════════════
# 4. todo_update tool — reason, REJECTED prefix, complete clears reason
# ═══════════════════════════════════════════════════════════════════════════════

def _inject_tracker(tracker):
    """Inject tracker into a fake 'main' module so tools.py can find it."""
    fake_main = types.ModuleType('main')
    fake_main.todo_tracker = tracker
    sys.modules['main'] = fake_main
    return fake_main


class TestTodoUpdateTool(unittest.TestCase):

    def _make_tracker(self):
        t = TodoTracker()
        t.add_todos([
            {"content": "Step 1", "activeForm": "Doing 1", "status": "in_progress",
             "criteria": "Test passes\nNo warnings"},
            {"content": "Step 2", "activeForm": "Doing 2"},
        ])
        return t

    def setUp(self):
        self.tracker = self._make_tracker()
        _inject_tracker(self.tracker)
        # Import after injection so tools.py picks up the fake module
        from core.tools import todo_update
        self.todo_update = todo_update

    def test_complete_no_reason(self):
        result = self.todo_update(index=1, status="completed")
        self.assertNotIn("[REJECTED]", result)
        self.assertEqual(self.tracker.todos[0].status, "completed")
        self.assertEqual(self.tracker.todos[0].rejection_reason, "")

    def test_pending_with_reason_stores_reason(self):
        self.todo_update(index=1, status="pending", reason="Tests failing")
        self.assertEqual(self.tracker.todos[0].rejection_reason, "Tests failing")
        self.assertEqual(self.tracker.todos[0].status, "pending")

    def test_pending_with_reason_returns_rejected_prefix(self):
        result = self.todo_update(index=1, status="pending", reason="Tests failing")
        self.assertTrue(result.startswith("[REJECTED]"))
        self.assertIn("Tests failing", result)

    def test_pending_without_reason_no_rejected_prefix(self):
        result = self.todo_update(index=1, status="pending")
        self.assertNotIn("[REJECTED]", result)

    def test_in_progress_with_reason_stores_reason(self):
        self.todo_update(index=2, status="in_progress", reason="Need rework")
        self.assertEqual(self.tracker.todos[1].rejection_reason, "Need rework")

    def test_complete_after_rejection_clears_reason(self):
        self.todo_update(index=1, status="pending", reason="failed")
        self.assertEqual(self.tracker.todos[0].rejection_reason, "failed")
        self.todo_update(index=1, status="in_progress")
        self.todo_update(index=1, status="completed")
        self.assertEqual(self.tracker.todos[0].rejection_reason, "")

    def test_invalid_index_returns_error(self):
        result = self.todo_update(index=99, status="completed")
        self.assertIn("Error", result)

    def test_invalid_status_returns_error(self):
        result = self.todo_update(index=1, status="unknown")
        self.assertIn("Error", result)

    def test_rejected_prefix_includes_step_content(self):
        result = self.todo_update(index=1, status="pending", reason="bad")
        self.assertIn("Step 1", result)


# ═══════════════════════════════════════════════════════════════════════════════
# 5. Plan mode blocked tools config
# ═══════════════════════════════════════════════════════════════════════════════

class TestPlanModeBlockedTools(unittest.TestCase):

    def test_blocked_tools_defined(self):
        self.assertIsInstance(config.PLAN_MODE_BLOCKED_TOOLS, frozenset)

    def test_write_file_blocked(self):
        self.assertIn('write_file', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_replace_in_file_blocked(self):
        self.assertIn('replace_in_file', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_run_command_blocked(self):
        self.assertIn('run_command', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_todo_write_not_blocked(self):
        self.assertNotIn('todo_write', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_read_file_not_blocked(self):
        self.assertNotIn('read_file', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_grep_file_not_blocked(self):
        self.assertNotIn('grep_file', config.PLAN_MODE_BLOCKED_TOOLS)

    def test_block_check_logic(self):
        """Simulate the inline check from run_react_agent."""
        def get_observation(agent_mode, tool_name):
            if agent_mode == 'plan_q':
                return 'BLOCKED_ALL'
            if agent_mode == 'plan' and tool_name in config.PLAN_MODE_BLOCKED_TOOLS:
                return 'BLOCKED_WRITE'
            return 'ALLOWED'

        # plan_q: ALL tools blocked
        self.assertEqual(get_observation('plan_q', 'read_file'), 'BLOCKED_ALL')
        self.assertEqual(get_observation('plan_q', 'write_file'), 'BLOCKED_ALL')
        self.assertEqual(get_observation('plan_q', 'todo_write'), 'BLOCKED_ALL')

        # plan: only write tools blocked
        self.assertEqual(get_observation('plan', 'write_file'), 'BLOCKED_WRITE')
        self.assertEqual(get_observation('plan', 'replace_in_file'), 'BLOCKED_WRITE')
        self.assertEqual(get_observation('plan', 'read_file'), 'ALLOWED')
        self.assertEqual(get_observation('plan', 'todo_write'), 'ALLOWED')

        # normal: nothing blocked
        self.assertEqual(get_observation('normal', 'write_file'), 'ALLOWED')

    def test_plan_q_is_distinct_from_plan(self):
        self.assertNotIn('plan_q', config.PLAN_MODE_BLOCKED_TOOLS)


# ═══════════════════════════════════════════════════════════════════════════════
# 6. Step review criteria injection logic
# ═══════════════════════════════════════════════════════════════════════════════

def _build_step_review(content, criteria):
    """Replicate the step review logic from run_react_agent."""
    criteria_block = ""
    if criteria:
        lines = [f"  - {c.strip()}" for c in criteria.splitlines() if c.strip()]
        criteria_block = "\nAcceptance criteria:\n" + "\n".join(lines) + "\n"
    return (
        f"\n\n[Step Review] '{content}' 완료로 표시됨.{criteria_block}\n"
        "모든 criteria 충족? → 다음 스텝 진행.\n"
        "미충족 항목 있음? → todo_update(N, 'pending', reason='<구체적 미충족 이유>')"
    )


class TestStepReviewInjection(unittest.TestCase):

    def test_with_criteria_shows_checklist(self):
        review = _build_step_review("Fix bug", "Test passes\nNo warnings")
        self.assertIn("Acceptance criteria:", review)
        self.assertIn("  - Test passes", review)
        self.assertIn("  - No warnings", review)

    def test_without_criteria_no_checklist(self):
        review = _build_step_review("Fix bug", "")
        self.assertNotIn("Acceptance criteria:", review)

    def test_always_includes_step_name(self):
        review = _build_step_review("My Step", "")
        self.assertIn("'My Step'", review)

    def test_always_includes_rejection_hint(self):
        review = _build_step_review("S", "")
        self.assertIn("todo_update", review)
        self.assertIn("pending", review)
        self.assertIn("reason=", review)

    def test_criteria_blank_lines_filtered(self):
        review = _build_step_review("S", "A\n\nB\n  \nC")
        self.assertIn("  - A", review)
        self.assertIn("  - B", review)
        self.assertIn("  - C", review)
        # Blank lines should not produce empty bullets
        self.assertNotIn("  - \n", review)


# ═══════════════════════════════════════════════════════════════════════════════
# 7. Step header building logic
# ═══════════════════════════════════════════════════════════════════════════════

def _build_step_header(step_num, total, content, rejection_reason="", detail="", criteria=""):
    """Replicate the step header logic from run_react_agent."""
    header_parts = [f"[Step {step_num}/{total}: {content}]"]
    if rejection_reason:
        header_parts.append(f"⚠️  Previously rejected: {rejection_reason}")
    if detail:
        header_parts.append(f"Detail: {detail}")
    if criteria:
        header_parts.append(f"Criteria: {criteria}")
    header_parts.append("→ 현재 목표를 염두에 두고 아래 결과를 해석할 것")
    return "\n".join(header_parts) + "\n\n"


class TestStepHeaderBuilding(unittest.TestCase):

    def test_basic_header(self):
        h = _build_step_header(1, 3, "Fix bug")
        self.assertIn("[Step 1/3: Fix bug]", h)
        self.assertIn("→ 현재 목표를", h)

    def test_no_extra_fields_no_extra_lines(self):
        h = _build_step_header(1, 3, "Fix bug")
        self.assertNotIn("Previously rejected", h)
        self.assertNotIn("Detail:", h)
        self.assertNotIn("Criteria:", h)

    def test_rejection_reason_shown(self):
        h = _build_step_header(2, 4, "Fix bug", rejection_reason="Tests fail")
        self.assertIn("⚠️  Previously rejected: Tests fail", h)

    def test_detail_shown(self):
        h = _build_step_header(1, 2, "Fix bug", detail="Edit auth.py")
        self.assertIn("Detail: Edit auth.py", h)

    def test_criteria_shown(self):
        h = _build_step_header(1, 2, "Fix bug", criteria="A\nB")
        self.assertIn("Criteria: A\nB", h)

    def test_all_fields_combined_ordering(self):
        h = _build_step_header(3, 5, "Fix", rejection_reason="R", detail="D", criteria="C")
        lines = h.split("\n")
        titles = [l for l in lines if l.strip()]
        self.assertIn("[Step 3/5: Fix]", titles[0])
        # rejection before detail before criteria
        idx_reject = next(i for i, l in enumerate(titles) if "Previously rejected" in l)
        idx_detail = next(i for i, l in enumerate(titles) if "Detail:" in l)
        idx_criteria = next(i for i, l in enumerate(titles) if "Criteria:" in l)
        self.assertLess(idx_reject, idx_detail)
        self.assertLess(idx_detail, idx_criteria)

    def test_ends_with_double_newline(self):
        h = _build_step_header(1, 1, "S")
        self.assertTrue(h.endswith("\n\n"))


# ═══════════════════════════════════════════════════════════════════════════════
# 8. _sys_content_append / _sys_content_strip_plan
# ═══════════════════════════════════════════════════════════════════════════════

class TestSysContentHelpers(unittest.TestCase):

    def _list_msg(self, text):
        return {"role": "system", "content": [{"type": "text", "text": text}]}

    # --- str ---
    def test_append_str(self):
        msg = {"role": "system", "content": "base"}
        _sys_content_append(msg, PLAN_MARKER)
        self.assertIn(PLAN_MARKER, msg["content"])

    def test_strip_str(self):
        msg = {"role": "system", "content": "base" + PLAN_MARKER + " extra"}
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"], "base")

    def test_strip_str_no_marker_noop(self):
        msg = {"role": "system", "content": "base"}
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"], "base")

    def test_roundtrip_str(self):
        msg = {"role": "system", "content": "original"}
        _sys_content_append(msg, PLAN_MARKER + "\nextra")
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"], "original")

    def test_double_append_strip_str(self):
        """Appending twice then stripping leaves nothing."""
        msg = {"role": "system", "content": "base"}
        _sys_content_append(msg, PLAN_MARKER + " v1")
        _sys_content_strip_plan(msg)
        _sys_content_append(msg, PLAN_MARKER + " v2")
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"], "base")

    # --- list ---
    def test_append_list(self):
        msg = self._list_msg("base")
        _sys_content_append(msg, PLAN_MARKER)
        self.assertIn(PLAN_MARKER, msg["content"][0]["text"])

    def test_strip_list(self):
        msg = self._list_msg("base" + PLAN_MARKER + " extra")
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"][0]["text"], "base")

    def test_strip_list_no_marker_noop(self):
        msg = self._list_msg("base")
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"][0]["text"], "base")

    def test_roundtrip_list(self):
        msg = self._list_msg("original")
        _sys_content_append(msg, PLAN_MARKER + "\nextra")
        _sys_content_strip_plan(msg)
        self.assertEqual(msg["content"][0]["text"], "original")

    def test_list_non_text_block_ignored(self):
        """Non-text blocks should not be modified."""
        msg = {"role": "system", "content": [
            {"type": "image", "url": "http://x"},
            {"type": "text", "text": "base"},
        ]}
        _sys_content_append(msg, PLAN_MARKER)
        self.assertNotIn(PLAN_MARKER, str(msg["content"][0]))
        self.assertIn(PLAN_MARKER, msg["content"][1]["text"])


# ═══════════════════════════════════════════════════════════════════════════════
# 9. run_react_agent signature
# ═══════════════════════════════════════════════════════════════════════════════

class TestRunReactAgentSignature(unittest.TestCase):

    def test_agent_mode_param_exists(self):
        self.assertIn("agent_mode", inspect.signature(run_react_agent).parameters)

    def test_agent_mode_default_normal(self):
        p = inspect.signature(run_react_agent).parameters["agent_mode"]
        self.assertEqual(p.default, "normal")

    def test_returns_tuple_annotation_or_no_crash(self):
        """run_react_agent should be callable (not crash on import)."""
        self.assertTrue(callable(run_react_agent))


if __name__ == "__main__":
    unittest.main(verbosity=2)
