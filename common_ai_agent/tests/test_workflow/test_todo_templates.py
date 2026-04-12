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

    def test_has_ten_steps(self):
        self.assertEqual(len(self.tasks), 10)

    def test_all_steps_are_mas(self):
        for i, t in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertTrue(
                    t["content"].startswith("[MAS]"),
                    f"Step {i} should start with '[MAS]', got: {t['content'][:30]}"
                )

    def test_no_rtl_tb_sim_doc_tasks(self):
        for prefix in ["[RTL]", "[TB]", "[SIM]", "[DOC]"]:
            found = [t for t in self.tasks if t["content"].startswith(prefix)]
            self.assertEqual(found, [], f"Should not have {prefix} tasks in mas_gen")

    def test_first_task_gathers_requirements(self):
        self.assertIn("requirement", self.tasks[0]["content"].lower())

    def test_last_task_covers_dv_plan(self):
        self.assertIn("DV Plan", self.tasks[-1]["content"])

    def test_each_section_has_own_task(self):
        contents = " ".join(t["content"] for t in self.tasks)
        for section in ["§1", "§2", "§3", "§4", "§5", "§6", "§7", "§8", "§9"]:
            with self.subTest(section=section):
                self.assertIn(section, contents)

    def test_all_steps_high_priority(self):
        for i, t in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(t["priority"], "high")


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

    def test_has_four_steps(self):
        self.assertEqual(len(self.tasks), 4)

    def test_first_step_reads_inputs(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("read", content)

    def test_first_step_references_rtl_tb_list(self):
        detail = self.tasks[0].get("detail", "")
        self.assertIn(".sv", detail)
        self.assertIn(".f", detail)

    def test_second_step_is_compile(self):
        self.assertIn("Compile", self.tasks[1]["content"])

    def test_compile_uses_filelist(self):
        detail = self.tasks[1].get("detail", "")
        self.assertIn(".f", detail)

    def test_third_step_is_loop(self):
        self.assertTrue(self.tasks[2].get("loop"))

    def test_loop_max_iterations_is_20(self):
        self.assertEqual(self.tasks[2]["max_loop_iterations"], 20)

    def test_last_step_has_sim_report(self):
        self.assertIn("sim_report", self.tasks[-1]["content"])

    def test_last_step_normal_priority(self):
        self.assertEqual(self.tasks[-1]["priority"], "normal")


# ─────────────────────────────────────────────────────────────
# TestLintTemplates
# ─────────────────────────────────────────────────────────────

class TestLintTemplates(unittest.TestCase):

    def setUp(self):
        self.data = _load("lint", "lint-fix")
        self.tasks = self.data["tasks"]

    def test_has_six_steps(self):
        self.assertEqual(len(self.tasks), 6)

    def test_first_step_reads_inputs(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("read", content)

    def test_first_step_references_rtl_and_filelist(self):
        detail = self.tasks[0].get("detail", "")
        self.assertIn(".sv", detail)
        self.assertIn(".f", detail)

    def test_second_step_runs_lint(self):
        content = self.tasks[1]["content"].lower()
        self.assertIn("lint", content)

    def test_lint_uses_filelist(self):
        detail = self.tasks[1].get("detail", "")
        self.assertIn(".f", detail)

    def test_third_step_fixes_errors(self):
        self.assertIn("errors", self.tasks[2]["content"].lower())

    def test_fourth_step_fixes_warnings(self):
        self.assertIn("warnings", self.tasks[3]["content"].lower())

    def test_fifth_step_confirms_clean(self):
        self.assertIn("0 errors", self.tasks[4]["content"])

    def test_last_step_generates_report(self):
        self.assertIn("lint_report", self.tasks[-1]["content"])

    def test_no_loop_tasks(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(loop_tasks, [])

    def test_last_step_normal_priority(self):
        self.assertEqual(self.tasks[-1]["priority"], "normal")


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


# ─────────────────────────────────────────────────────────────
# TestMasGenNewIpTemplate
# ─────────────────────────────────────────────────────────────

class TestMasGenNewIpTemplate(unittest.TestCase):
    """Tests for workflow/mas_gen/todo_templates/new-ip.json — MAS only"""

    def setUp(self):
        self.data = _load("mas_gen", "new-ip")
        self.tasks = self.data["tasks"]

    def test_name_is_new_ip(self):
        self.assertEqual(self.data["name"], "new-ip")

    def test_has_description(self):
        self.assertIn("description", self.data)

    def test_has_ten_tasks(self):
        self.assertEqual(len(self.tasks), 10)

    def test_first_task_gathers_requirements(self):
        content = self.tasks[0]["content"]
        self.assertIn("[MAS]", content)
        self.assertIn("requirement", content.lower())

    def test_all_tasks_are_mas(self):
        for i, t in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertTrue(
                    t["content"].startswith("[MAS]"),
                    f"Task {i} should start with [MAS], got: {t['content'][:30]}"
                )

    def test_no_rtl_tb_sim_doc_tasks(self):
        for prefix in ["[RTL]", "[TB]", "[SIM]", "[DOC]"]:
            found = [t for t in self.tasks if t["content"].startswith(prefix)]
            self.assertEqual(found, [], f"Should not have {prefix} tasks in mas_gen new-ip")

    def test_first_task_reads_requirement_files(self):
        detail = self.tasks[0].get("detail", "").lower()
        self.assertIn("requirement", detail)
        self.assertIn("search", detail)

    def test_requirements_detail_mentions_ports(self):
        self.assertIn("port", self.tasks[0].get("detail", "").lower())

    def test_each_section_has_own_task(self):
        contents = " ".join(t["content"] for t in self.tasks)
        for section in ["§1", "§2", "§3", "§4", "§5", "§6", "§7", "§8", "§9"]:
            with self.subTest(section=section):
                self.assertIn(section, contents)

    def test_last_task_covers_dv_plan(self):
        content = self.tasks[-1]["content"]
        detail  = self.tasks[-1].get("detail", "")
        self.assertIn("DV Plan", content)
        self.assertIn("§9", detail)

    def test_all_tasks_high_priority(self):
        for i, task in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(task["priority"], "high")


# ─────────────────────────────────────────────────────────────
# TestMasGenLegacyIpTemplate
# ─────────────────────────────────────────────────────────────

class TestMasGenLegacyIpTemplate(unittest.TestCase):
    """Tests for workflow/mas_gen/todo_templates/legacy-ip.json — MAS only"""

    def setUp(self):
        self.data = _load("mas_gen", "legacy-ip")
        self.tasks = self.data["tasks"]

    def test_name_is_legacy_ip(self):
        self.assertEqual(self.data["name"], "legacy-ip")

    def test_has_description(self):
        self.assertIn("description", self.data)
        desc = self.data["description"].lower()
        self.assertIn("legacy", desc)

    def test_has_seven_tasks(self):
        self.assertEqual(len(self.tasks), 7)

    def test_first_task_reads_existing_rtl(self):
        content = self.tasks[0]["content"]
        self.assertIn("[MAS]", content)
        self.assertIn("existing", content.lower())

    def test_all_tasks_are_mas(self):
        for i, t in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertTrue(
                    t["content"].startswith("[MAS]"),
                    f"Task {i} should start with [MAS], got: {t['content'][:30]}"
                )

    def test_no_rtl_tb_sim_doc_tasks(self):
        for prefix in ["[RTL]", "[TB]", "[SIM]", "[DOC]"]:
            found = [t for t in self.tasks if t["content"].startswith(prefix)]
            self.assertEqual(found, [], f"Should not have {prefix} tasks in mas_gen legacy-ip")

    def test_third_task_confirms_with_user(self):
        detail = self.tasks[2].get("detail", "").lower()
        self.assertIn("user", detail)
        self.assertIn("sign-off", detail)

    def test_delta_tasks_mention_annotations(self):
        # tasks 3-6 are delta sections — at least one should mention 'Changed in'
        delta_details = " ".join(t.get("detail", "") for t in self.tasks[3:])
        self.assertIn("Changed in", delta_details)

    def test_last_task_covers_dv_plan(self):
        content = self.tasks[-1]["content"]
        self.assertIn("§9", content)

    def test_all_tasks_high_priority(self):
        for i, task in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(task["priority"], "high")


# ─────────────────────────────────────────────────────────────
# TestRtlGenNewIpTemplate
# ─────────────────────────────────────────────────────────────

class TestRtlGenNewIpTemplate(unittest.TestCase):
    """Tests for workflow/rtl_gen/todo_templates/new-ip-rtl.json"""

    def setUp(self):
        self.data = _load("rtl_gen", "new-ip-rtl")
        self.tasks = self.data["tasks"]

    def test_name_is_new_ip_rtl(self):
        self.assertEqual(self.data["name"], "new-ip-rtl")

    def test_has_eight_tasks(self):
        self.assertEqual(len(self.tasks), 8)

    def test_first_task_reads_mas(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("read", content)
        self.assertIn("mas", content)

    def test_first_task_detail_covers_all_mas_sections(self):
        detail = self.tasks[0]["detail"]
        for section in ["§2", "§3", "§4", "§5", "§6", "§7", "§8"]:
            with self.subTest(section=section):
                self.assertIn(section, detail)

    def test_second_task_writes_module_header(self):
        content = self.tasks[1]["content"].lower()
        self.assertIn("module header", content)

    def test_third_task_implements_fsm(self):
        content = self.tasks[2]["content"].lower()
        self.assertIn("fsm", content)

    def test_fourth_task_implements_datapath(self):
        content = self.tasks[3]["content"].lower()
        self.assertIn("datapath", content)

    def test_fifth_task_implements_registers(self):
        content = self.tasks[4]["content"].lower()
        self.assertIn("register", content)

    def test_sixth_task_implements_interrupt(self):
        content = self.tasks[5]["content"].lower()
        self.assertIn("interrupt", content)

    def test_seventh_task_instantiates_memory(self):
        content = self.tasks[6]["content"].lower()
        self.assertIn("memory", content)

    def test_last_task_is_lint_check(self):
        content = self.tasks[7]["content"].lower()
        self.assertIn("lint", content)

    def test_no_loop_tasks(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(loop_tasks, [])

    def test_all_tasks_high_priority(self):
        for i, task in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(task["priority"], "high")

    def test_lint_task_mentions_mas_result(self):
        detail = self.tasks[7].get("detail", "")
        self.assertIn("[MAS RESULT]", detail)


# ─────────────────────────────────────────────────────────────
# TestRtlGenLegacyIpTemplate
# ─────────────────────────────────────────────────────────────

class TestRtlGenLegacyIpTemplate(unittest.TestCase):
    """Tests for workflow/rtl_gen/todo_templates/legacy-ip-rtl.json"""

    def setUp(self):
        self.data = _load("rtl_gen", "legacy-ip-rtl")
        self.tasks = self.data["tasks"]

    def test_name_is_legacy_ip_rtl(self):
        self.assertEqual(self.data["name"], "legacy-ip-rtl")

    def test_has_seven_tasks(self):
        self.assertEqual(len(self.tasks), 7)

    def test_first_task_reads_existing_rtl_and_mas_delta(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("existing", content)
        detail = self.tasks[0].get("detail", "").lower()
        self.assertIn("delta", detail)

    def test_new_ports_task_mentions_end_of_list(self):
        # task[1]: new ports must be added at END of port list
        detail = self.tasks[1].get("detail", "").lower()
        self.assertIn("end", detail)

    def test_new_ports_task_forbids_removing(self):
        detail = self.tasks[1].get("detail", "").lower()
        self.assertIn("never reorder", detail)

    def test_fsm_task_preserves_existing_transitions(self):
        detail = self.tasks[2].get("detail", "").lower()
        self.assertIn("never modify", detail)

    def test_datapath_task_uses_changed_annotation(self):
        detail = self.tasks[3].get("detail", "")
        self.assertIn("CHANGED", detail)

    def test_register_task_preserves_existing_offsets(self):
        detail = self.tasks[4].get("detail", "").lower()
        self.assertIn("never reuse", detail)

    def test_interrupt_task_preserves_existing_bits(self):
        detail = self.tasks[5].get("detail", "").lower()
        # "do NOT change existing interrupt bit positions"
        self.assertIn("not change", detail)

    def test_last_task_is_regression_lint(self):
        content = self.tasks[6]["content"].lower()
        self.assertIn("lint", content)
        self.assertIn("regression", content)

    def test_no_loop_tasks(self):
        loop_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(loop_tasks, [])

    def test_all_tasks_high_priority(self):
        for i, task in enumerate(self.tasks):
            with self.subTest(idx=i):
                self.assertEqual(task["priority"], "high")

    def test_backward_compat_mentioned(self):
        all_text = " ".join(t.get("detail", "") for t in self.tasks)
        self.assertIn("backward", all_text.lower())


# ─────────────────────────────────────────────────────────────
# TestTbGenNewIpTemplate
# ─────────────────────────────────────────────────────────────

class TestTbGenNewIpTemplate(unittest.TestCase):
    """Tests for workflow/tb_gen/todo_templates/new-ip-tb.json"""

    def setUp(self):
        self.data = _load("tb_gen", "new-ip-tb")
        self.tasks = self.data["tasks"]

    def test_name_is_new_ip_tb(self):
        self.assertEqual(self.data["name"], "new-ip-tb")

    def test_has_eight_tasks(self):
        self.assertEqual(len(self.tasks), 8)

    def test_first_task_reads_mas_and_dut(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("mas", content)
        detail = self.tasks[0].get("detail", "").lower()
        self.assertIn("dut", detail)

    def test_first_task_detail_covers_dv_plan(self):
        detail = self.tasks[0].get("detail", "")
        self.assertIn("§9", detail)

    def test_s1_s2_task_exists(self):
        # task[1]: S1 reset + S2 basic operation
        content = self.tasks[1]["content"].lower()
        self.assertIn("s1", content)
        self.assertIn("s2", content)

    def test_s3_interrupt_task_exists(self):
        content = self.tasks[2]["content"].lower()
        self.assertIn("interrupt", content)

    def test_s4_memory_task_exists(self):
        content = self.tasks[3]["content"].lower()
        self.assertIn("memory", content)

    def test_sva_assertions_task_exists(self):
        sva_tasks = [t for t in self.tasks if "sva" in t["content"].lower() or
                     "assertion" in t["content"].lower()]
        self.assertGreater(len(sva_tasks), 0)

    def test_tb_top_task_exists(self):
        # task that writes tb_<module>.sv top-level — check content title
        tb_top_tasks = [t for t in self.tasks
                        if "tb_" in t["content"].lower() and
                        "top" in t["content"].lower()]
        self.assertGreater(len(tb_top_tasks), 0)

    def test_sim_task_is_loop(self):
        sim_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(len(sim_tasks), 1)
        self.assertTrue(sim_tasks[0].get("loop"))

    def test_sim_max_loop_iterations(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        self.assertEqual(sim_task["max_loop_iterations"], 15)

    def test_sim_has_validator(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        self.assertIn("validator", sim_task)
        self.assertIn("check_sim_pass.sh", sim_task["validator"])

    def test_coverage_task_is_last(self):
        last = self.tasks[-1]
        self.assertIn("coverage", last["content"].lower())

    def test_coverage_task_normal_priority(self):
        last = self.tasks[-1]
        self.assertEqual(last["priority"], "normal")

    def test_all_tasks_except_coverage_are_high_priority(self):
        for i, task in enumerate(self.tasks[:-1]):
            with self.subTest(idx=i):
                self.assertEqual(task["priority"], "high")

    def test_sim_detail_mentions_mas_escalate(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        detail = sim_task.get("detail", "")
        self.assertIn("MAS ESCALATE", detail)


# ─────────────────────────────────────────────────────────────
# TestTbGenLegacyIpTemplate
# ─────────────────────────────────────────────────────────────

class TestTbGenLegacyIpTemplate(unittest.TestCase):
    """Tests for workflow/tb_gen/todo_templates/legacy-ip-tb.json"""

    def setUp(self):
        self.data = _load("tb_gen", "legacy-ip-tb")
        self.tasks = self.data["tasks"]

    def test_name_is_legacy_ip_tb(self):
        self.assertEqual(self.data["name"], "legacy-ip-tb")

    def test_has_eight_tasks(self):
        self.assertEqual(len(self.tasks), 8)

    def test_first_task_reads_existing_tb_and_mas_delta(self):
        content = self.tasks[0]["content"].lower()
        self.assertIn("existing", content)
        detail = self.tasks[0].get("detail", "").lower()
        self.assertIn("delta", detail)

    def test_first_task_detail_mentions_changed_annotations(self):
        detail = self.tasks[0].get("detail", "")
        self.assertIn("Changed in", detail)

    def test_dut_instantiation_task_preserves_ports(self):
        # task[1]: update DUT instantiation, do NOT reorder existing connections
        detail = self.tasks[1].get("detail", "").lower()
        self.assertIn("not reorder", detail)

    def test_new_sequences_task_uses_tc_naming(self):
        # task[2]: new sequences named tc_<SequenceID>_<name>
        detail = self.tasks[2].get("detail", "")
        self.assertIn("tc_", detail)

    def test_new_sequences_task_does_not_modify_existing(self):
        detail = self.tasks[2].get("detail", "").lower()
        self.assertIn("not modify", detail)

    def test_modified_sequences_task_adds_changed_comment(self):
        # task[3]: add // CHANGED: vX.Y comment
        detail = self.tasks[3].get("detail", "")
        self.assertIn("CHANGED", detail)

    def test_sva_task_keeps_existing_assertions(self):
        # task[4]: keep all existing assertions — do not remove
        detail = self.tasks[4].get("detail", "").lower()
        self.assertIn("do not remove", detail)

    def test_tb_top_task_preserves_call_order(self):
        # task[5]: do NOT reorder existing tc_ calls
        detail = self.tasks[5].get("detail", "").lower()
        self.assertIn("not reorder", detail)

    def test_sim_task_is_regression_loop(self):
        sim_tasks = [t for t in self.tasks if t.get("loop")]
        self.assertEqual(len(sim_tasks), 1)
        sim_task = sim_tasks[0]
        content = sim_task["content"].lower()
        self.assertIn("regression", content)

    def test_sim_max_loop_iterations(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        self.assertEqual(sim_task["max_loop_iterations"], 15)

    def test_sim_exit_condition(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        self.assertEqual(sim_task["exit_condition"], "0 errors, 0 warnings")

    def test_sim_has_validator(self):
        sim_task = next(t for t in self.tasks if t.get("loop"))
        self.assertIn("validator", sim_task)

    def test_coverage_task_is_last_and_normal_priority(self):
        last = self.tasks[-1]
        self.assertIn("coverage", last["content"].lower())
        self.assertEqual(last["priority"], "normal")

    def test_regression_baseline_mentioned(self):
        # Original sequences must still pass — regression baseline
        all_text = " ".join(t.get("detail", "") for t in self.tasks).lower()
        self.assertIn("regression", all_text)


# ─────────────────────────────────────────────────────────────
# TestNewVsLegacyContrast — Cross-template behavioral difference checks
# ─────────────────────────────────────────────────────────────

class TestNewVsLegacyContrast(unittest.TestCase):
    """Verify that new-IP and legacy-IP templates enforce different policies."""

    def test_mas_new_ip_is_longer_than_legacy(self):
        new_tasks  = _load("mas_gen", "new-ip")["tasks"]
        legacy_tasks = _load("mas_gen", "legacy-ip")["tasks"]
        # new-ip has more MAS authoring steps (full 9-section spec vs delta)
        new_mas_count = sum(1 for t in new_tasks if t["content"].startswith("[MAS]"))
        legacy_mas_count = sum(1 for t in legacy_tasks if t["content"].startswith("[MAS]"))
        self.assertGreater(new_mas_count, legacy_mas_count)

    def test_rtl_new_ip_more_tasks_than_legacy(self):
        new_tasks    = _load("rtl_gen", "new-ip-rtl")["tasks"]
        legacy_tasks = _load("rtl_gen", "legacy-ip-rtl")["tasks"]
        self.assertGreater(len(new_tasks), len(legacy_tasks))

    def test_legacy_rtl_mentions_backward_compat_new_ip_does_not(self):
        legacy_details = " ".join(
            t.get("detail", "") for t in _load("rtl_gen", "legacy-ip-rtl")["tasks"]
        ).lower()
        new_details = " ".join(
            t.get("detail", "") for t in _load("rtl_gen", "new-ip-rtl")["tasks"]
        ).lower()
        self.assertIn("backward", legacy_details)
        self.assertNotIn("backward compat", new_details)

    def test_legacy_tb_preserves_existing_sequences(self):
        legacy_details = " ".join(
            t.get("detail", "") for t in _load("tb_gen", "legacy-ip-tb")["tasks"]
        ).lower()
        self.assertIn("not modify", legacy_details)

    def test_legacy_mas_has_user_confirmation_step(self):
        legacy_tasks = _load("mas_gen", "legacy-ip")["tasks"]
        confirm_tasks = [t for t in legacy_tasks
                         if "confirm" in t["content"].lower() or "sign-off" in t.get("detail", "").lower()]
        self.assertGreater(len(confirm_tasks), 0,
                           "legacy-ip should have a user sign-off step before writing MAS")

    def test_new_ip_mas_no_explicit_user_confirmation_needed(self):
        new_tasks = _load("mas_gen", "new-ip")["tasks"]
        # new-ip gathers requirements in task[0] but no dedicated "sign-off" gate
        sign_off_tasks = [t for t in new_tasks if "sign-off" in t.get("detail", "").lower()]
        # new-ip may have one requirements gather with approval — that's fine (≤1)
        self.assertLessEqual(len(sign_off_tasks), 1)

    def test_both_sim_loops_use_same_validator(self):
        for ws, stem in [("mas_gen", "new-ip"), ("mas_gen", "legacy-ip"),
                          ("tb_gen", "new-ip-tb"), ("tb_gen", "legacy-ip-tb")]:
            with self.subTest(ws=ws, stem=stem):
                tasks = _load(ws, stem)["tasks"]
                loop_task = next((t for t in tasks if t.get("loop")), None)
                if loop_task:
                    self.assertIn("check_sim_pass.sh", loop_task.get("validator", ""))


if __name__ == "__main__":
    unittest.main()
