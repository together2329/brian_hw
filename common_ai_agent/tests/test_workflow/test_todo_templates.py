"""
Structural tests for workflow/*/todo_templates/*.json

Reads the real template files from disk and verifies:
- Schema: required fields, valid priority values
- Loop task completeness (max_loop_iterations, exit_condition, activeForm)
- Per-workspace step counts and ordering
- No empty task content

No tempfile, no LLM calls — pure JSON structure validation.
"""
import json
import os
import sys
import unittest
from pathlib import Path

_this = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)

WORKFLOW_DIR = Path(_root) / "workflow"

VALID_PRIORITIES = {"high", "normal", "low", "medium"}


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _load(workspace: str, stem: str) -> dict:
    p = WORKFLOW_DIR / workspace / "todo_templates" / f"{stem}.json"
    return json.loads(p.read_text(encoding="utf-8"))


def _all_templates():
    """Yield (workspace, stem, data) for every template in every workspace."""
    for ws_dir in sorted(WORKFLOW_DIR.iterdir()):
        tmpl_dir = ws_dir / "todo_templates"
        if tmpl_dir.is_dir():
            for f in sorted(tmpl_dir.glob("*.json")):
                data = json.loads(f.read_text(encoding="utf-8"))
                yield ws_dir.name, f.stem, data


# ─────────────────────────────────────────────────────────────
# TestTodoTemplateSchema — common checks across ALL templates
# ─────────────────────────────────────────────────────────────

class TestTodoTemplateSchema(unittest.TestCase):

    def test_all_templates_have_name_field(self):
        for ws, stem, data in _all_templates():
            with self.subTest(ws=ws, stem=stem):
                self.assertIn("name", data, f"{ws}/{stem} missing 'name'")
                self.assertIsInstance(data["name"], str)
                self.assertTrue(data["name"].strip(), f"{ws}/{stem} 'name' is empty")

    def test_all_templates_have_tasks_list(self):
        for ws, stem, data in _all_templates():
            with self.subTest(ws=ws, stem=stem):
                self.assertIn("tasks", data, f"{ws}/{stem} missing 'tasks'")
                self.assertIsInstance(data["tasks"], list)

    def test_all_tasks_have_content_field(self):
        for ws, stem, data in _all_templates():
            for i, task in enumerate(data.get("tasks", [])):
                with self.subTest(ws=ws, stem=stem, task_idx=i):
                    self.assertIn("content", task)
                    self.assertIsInstance(task["content"], str)

    def test_all_tasks_have_valid_priority(self):
        for ws, stem, data in _all_templates():
            for i, task in enumerate(data.get("tasks", [])):
                with self.subTest(ws=ws, stem=stem, task_idx=i):
                    self.assertIn("priority", task,
                                  f"{ws}/{stem}[{i}] missing priority")
                    self.assertIn(task["priority"], VALID_PRIORITIES,
                                  f"{ws}/{stem}[{i}] invalid priority '{task['priority']}'")

    def test_loop_tasks_have_required_fields(self):
        for ws, stem, data in _all_templates():
            for i, task in enumerate(data.get("tasks", [])):
                if not task.get("loop"):
                    continue
                with self.subTest(ws=ws, stem=stem, task_idx=i):
                    self.assertIn("max_loop_iterations", task)
                    self.assertIsInstance(task["max_loop_iterations"], int)
                    self.assertGreater(task["max_loop_iterations"], 0)
                    self.assertIn("exit_condition", task)
                    self.assertTrue(task["exit_condition"].strip())

    def test_loop_tasks_have_active_form_with_loop_count(self):
        for ws, stem, data in _all_templates():
            for i, task in enumerate(data.get("tasks", [])):
                if not task.get("loop"):
                    continue
                with self.subTest(ws=ws, stem=stem, task_idx=i):
                    self.assertIn("activeForm", task,
                                  f"loop task {ws}/{stem}[{i}] missing activeForm")
                    self.assertIn("{loop_count}", task["activeForm"],
                                  f"loop task {ws}/{stem}[{i}] activeForm missing {{loop_count}}")

    def test_no_empty_task_content(self):
        for ws, stem, data in _all_templates():
            for i, task in enumerate(data.get("tasks", [])):
                with self.subTest(ws=ws, stem=stem, task_idx=i):
                    content = task.get("content", "")
                    self.assertTrue(content.strip(),
                                    f"{ws}/{stem}[{i}] has empty content")


# ─────────────────────────────────────────────────────────────
# TestMasGenTemplates
# ─────────────────────────────────────────────────────────────

class TestMasGenTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("mas_gen", "full-project")
        self.tasks = self.data["tasks"]

    def test_has_six_steps(self):
        self.assertEqual(len(self.tasks), 6)

    def test_step_order_by_prefix(self):
        prefixes = ["[MAS]", "[RTL]", "[RTL]", "[TB]", "[SIM]", "[DOC]"]
        for i, prefix in enumerate(prefixes):
            with self.subTest(idx=i):
                self.assertTrue(
                    self.tasks[i]["content"].startswith(prefix),
                    f"Step {i} should start with '{prefix}', got: {self.tasks[i]['content'][:20]}"
                )

    def test_sim_step_is_loop(self):
        self.assertTrue(self.tasks[4].get("loop"))

    def test_sim_max_loop_iterations(self):
        self.assertEqual(self.tasks[4]["max_loop_iterations"], 15)

    def test_sim_exit_condition(self):
        self.assertEqual(self.tasks[4]["exit_condition"], "0 errors, 0 warnings")

    def test_sim_has_validator(self):
        self.assertIn("validator", self.tasks[4])
        self.assertTrue(self.tasks[4]["validator"].strip())

    def test_steps_0_to_4_are_high_priority(self):
        for i in range(5):
            with self.subTest(idx=i):
                self.assertEqual(self.tasks[i]["priority"], "high")

    def test_doc_step_is_normal_priority(self):
        self.assertEqual(self.tasks[5]["priority"], "normal")


# ─────────────────────────────────────────────────────────────
# TestRtlGenTemplates
# ─────────────────────────────────────────────────────────────

class TestRtlGenTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("rtl_gen", "rtl-impl")
        self.tasks = self.data["tasks"]

    def test_has_eight_steps(self):
        self.assertEqual(len(self.tasks), 8)

    def test_first_step_reads_mas(self):
        self.assertIn("Read Micro Architecture Spec", self.tasks[0]["content"])

    def test_last_step_is_lint_check(self):
        self.assertIn("Lint check", self.tasks[7]["content"])

    def test_no_loop_tasks(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(loop_tasks, [])

    def test_all_steps_high_priority(self):
        for i, t in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(t["priority"], "high")

    def test_detail_fields_cover_key_rtl_sections(self):
        all_details = " ".join(t.get("detail", "") for t in self.tasks)
        for keyword in ["register", "FSM", "datapath", "interrupt", "memory"]:
            with self.subTest(keyword=keyword):
                self.assertIn(keyword.lower(), all_details.lower(),
                              f"rtl-impl missing '{keyword}' in task details")


# ─────────────────────────────────────────────────────────────
# TestTbGenTemplates
# ─────────────────────────────────────────────────────────────

class TestTbGenTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("tb_gen", "tb-impl")
        self.tasks = self.data["tasks"]

    def test_has_six_steps(self):
        self.assertEqual(len(self.tasks), 6)

    def test_first_step_reads_dv_plan(self):
        self.assertIn("DV Plan", self.tasks[0]["content"])

    def test_sim_step_is_loop(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(len(loop_tasks), 1)
        self.assertTrue(loop_tasks[0].get("loop"))

    def test_sim_max_loop_iterations(self):
        loop_task = next(t for t in self.tasks if t.get("loop"))
        self.assertEqual(loop_task["max_loop_iterations"], 15)

    def test_sim_has_validator(self):
        loop_task = next(t for t in self.tasks if t.get("loop"))
        self.assertIn("validator", loop_task)
        self.assertTrue(loop_task["validator"].strip())

    def test_last_step_is_coverage(self):
        last = self.tasks[-1]["content"].lower()
        self.assertIn("coverage", last)

    def test_last_step_normal_priority(self):
        self.assertEqual(self.tasks[-1]["priority"], "normal")


# ─────────────────────────────────────────────────────────────
# TestSimTemplates
# ─────────────────────────────────────────────────────────────

class TestSimTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("sim", "sim-debug")
        self.tasks = self.data["tasks"]

    def test_has_three_steps(self):
        self.assertEqual(len(self.tasks), 3)

    def test_first_step_is_compile(self):
        self.assertIn("Compile", self.tasks[0]["content"])

    def test_second_step_is_loop(self):
        self.assertTrue(self.tasks[1].get("loop"))

    def test_loop_max_iterations_is_20(self):
        self.assertEqual(self.tasks[1]["max_loop_iterations"], 20)

    def test_last_step_has_sim_report(self):
        self.assertIn("sim_report", self.tasks[2]["content"])

    def test_last_step_normal_priority(self):
        self.assertEqual(self.tasks[2]["priority"], "normal")


# ─────────────────────────────────────────────────────────────
# TestLintTemplates
# ─────────────────────────────────────────────────────────────

class TestLintTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("lint", "lint-fix")
        self.tasks = self.data["tasks"]

    def test_has_five_steps(self):
        self.assertEqual(len(self.tasks), 5)

    def test_first_step_runs_lint_all(self):
        self.assertIn("/lint-all", self.tasks[0]["content"])

    def test_second_step_fixes_errors(self):
        self.assertIn("errors", self.tasks[1]["content"].lower())

    def test_third_step_fixes_warnings(self):
        self.assertIn("warnings", self.tasks[2]["content"].lower())

    def test_fourth_step_is_lint_clean(self):
        self.assertIn("0 errors", self.tasks[3]["content"])

    def test_last_step_generates_report(self):
        self.assertIn("lint_report", self.tasks[4]["content"])

    def test_no_loop_tasks(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(loop_tasks, [])

    def test_last_step_normal_priority(self):
        self.assertEqual(self.tasks[4]["priority"], "normal")


# ─────────────────────────────────────────────────────────────
# TestDefaultTemplates
# ─────────────────────────────────────────────────────────────

class TestDefaultTemplates(unittest.TestCase):

    def setUp(self):
        self.feature  = _load("default", "feature")
        self.bugfix   = _load("default", "bugfix")
        self.refactor = _load("default", "refactor")

    def test_feature_parseable(self):
        self.assertIn("tasks", self.feature)

    def test_bugfix_parseable(self):
        self.assertIn("tasks", self.bugfix)

    def test_refactor_parseable(self):
        self.assertIn("tasks", self.refactor)

    def test_each_has_three_tasks(self):
        for name, data in [("feature", self.feature),
                           ("bugfix", self.bugfix),
                           ("refactor", self.refactor)]:
            with self.subTest(template=name):
                self.assertEqual(len(data["tasks"]), 3,
                                 f"default/{name} should have 3 tasks")

    def test_feature_has_trigger_keywords(self):
        self.assertIn("trigger_keywords", self.feature)
        self.assertIsInstance(self.feature["trigger_keywords"], list)
        self.assertTrue(len(self.feature["trigger_keywords"]) > 0)

    def test_bugfix_has_trigger_keywords(self):
        self.assertIn("trigger_keywords", self.bugfix)
        self.assertIsInstance(self.bugfix["trigger_keywords"], list)
        self.assertTrue(len(self.bugfix["trigger_keywords"]) > 0)

    def test_no_loop_tasks_in_default_templates(self):
        for name, data in [("feature", self.feature),
                           ("bugfix", self.bugfix),
                           ("refactor", self.refactor)]:
            for i, task in enumerate(data["tasks"]):
                with self.subTest(template=name, idx=i):
                    self.assertFalse(task.get("loop", False))

    def test_all_default_tasks_have_active_form(self):
        for name, data in [("feature", self.feature),
                           ("bugfix", self.bugfix),
                           ("refactor", self.refactor)]:
            for i, task in enumerate(data["tasks"]):
                with self.subTest(template=name, idx=i):
                    self.assertIn("activeForm", task,
                                  f"default/{name}[{i}] missing activeForm")


if __name__ == "__main__":
    unittest.main()
