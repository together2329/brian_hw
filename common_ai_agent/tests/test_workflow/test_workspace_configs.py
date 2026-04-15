"""
Integration tests for real workspace configurations.

Calls load_workspace() against actual workspace directories on disk and
validates the returned WorkspaceConfig attributes.

No LLM calls, no subprocess execution — only asserts what load_workspace
*returns*, not what scripts *do*.
"""
import os
import sys
import unittest
from pathlib import Path

_this = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))

from workflow.loader import (
    load_workspace,
    TodoTemplateRegistry,
    TRIGGER_TO_HOOKPOINT_NAME,
)

PROJECT_ROOT = Path(_root)
WORKFLOW_DIR = PROJECT_ROOT / "workflow"

PRODUCTION_WORKSPACES = ["mas-gen", "rtl-gen", "tb-gen", "sim", "lint"]


# ─────────────────────────────────────────────────────────────
# TestMasGenWorkspace
# ─────────────────────────────────────────────────────────────

class TestMasGenWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("mas-gen", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "mas-gen")

    def test_description_not_empty(self):
        self.assertTrue(self.ws.description.strip())

    def test_max_iterations_300(self):
        self.assertEqual(self.ws.env_overrides.get("MAX_ITERATIONS"), "300")

    def test_markdown_render_enabled(self):
         self.assertEqual(self.ws.env_overrides.get("ENABLE_MARKDOWN_RENDER"), "true")

    def test_system_prompt_mode_prepend(self):
        self.assertEqual(self.ws.system_prompt_mode, "prepend")

    def test_plan_prompt_mode_prepend(self):
        self.assertEqual(self.ws.plan_prompt_mode, "prepend")

    def test_system_prompt_text_loaded(self):
        self.assertIsNotNone(self.ws.system_prompt_text)
        self.assertGreater(len(self.ws.system_prompt_text), 50)

    def test_verilog_expert_in_force_skills(self):
        self.assertIn("verilog-expert", self.ws.force_skills)

    def test_rules_dir_has_md_files(self):
        self.assertIsNotNone(self.ws.rules_dir)
        md_files = list(self.ws.rules_dir.glob("*.md"))
        self.assertGreater(len(md_files), 0)

    def test_todo_templates_dir_has_full_project(self):
        self.assertIsNotNone(self.ws.todo_templates_dir)
        self.assertTrue((self.ws.todo_templates_dir / "full-project.json").exists())

    def test_script_hooks_loaded(self):
        self.assertGreater(len(self.ws.script_hooks), 0)

    def test_script_hook_triggers_valid(self):
        for spec in self.ws.script_hooks:
            with self.subTest(script=spec.script.name):
                self.assertIn(spec.trigger, TRIGGER_TO_HOOKPOINT_NAME)

    def test_commands_dir_present(self):
        self.assertIsNotNone(self.ws.commands_dir)


# ─────────────────────────────────────────────────────────────
# TestRtlGenWorkspace
# ─────────────────────────────────────────────────────────────

class TestRtlGenWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("rtl-gen", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "rtl-gen")

    def test_max_iterations_150(self):
        self.assertEqual(self.ws.env_overrides.get("MAX_ITERATIONS"), "150")

    def test_system_prompt_mode_prepend(self):
        self.assertEqual(self.ws.system_prompt_mode, "prepend")

    def test_verilog_expert_in_force_skills(self):
        self.assertIn("verilog-expert", self.ws.force_skills)

    def test_rtl_impl_template_loadable(self):
        reg = TodoTemplateRegistry()
        reg.load_from_dir(self.ws.todo_templates_dir)
        self.assertIsNotNone(reg.get("rtl-impl"))

    def test_script_hooks_include_after_tool(self):
        after_tool = [s for s in self.ws.script_hooks if s.trigger == "after_tool"]
        self.assertGreater(len(after_tool), 0)

    def test_post_write_has_sv_extension_condition(self):
        post_write = next(
            (s for s in self.ws.script_hooks if "post_write" in s.script.name), None
        )
        self.assertIsNotNone(post_write, "post_write.sh hook not found")
        exts = post_write.conditions.get("file_extensions", [])
        self.assertIn(".sv", exts)

    def test_error_capture_has_output_contains(self):
        err_cap = next(
            (s for s in self.ws.script_hooks if "error_capture" in s.script.name), None
        )
        self.assertIsNotNone(err_cap, "error_capture.sh hook not found")
        self.assertIn("output_contains", err_cap.conditions)

    def test_commands_dir_has_lint(self):
        self.assertIsNotNone(self.ws.commands_dir)
        self.assertTrue((self.ws.commands_dir / "lint.json").exists())


# ─────────────────────────────────────────────────────────────
# TestTbGenWorkspace
# ─────────────────────────────────────────────────────────────

class TestTbGenWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("tb-gen", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "tb-gen")

    def test_max_iterations_200(self):
        self.assertEqual(self.ws.env_overrides.get("MAX_ITERATIONS"), "200")

    def test_tb_impl_template_loadable(self):
        reg = TodoTemplateRegistry()
        reg.load_from_dir(self.ws.todo_templates_dir)
        self.assertIsNotNone(reg.get("tb-impl"))

    def test_at_least_two_script_hooks(self):
        self.assertGreaterEqual(len(self.ws.script_hooks), 2)

    def test_commands_dir_has_gen_tc(self):
        self.assertIsNotNone(self.ws.commands_dir)
        self.assertTrue((self.ws.commands_dir / "gen-tc.json").exists())

    def test_verilog_expert_in_force_skills(self):
        self.assertIn("verilog-expert", self.ws.force_skills)


# ─────────────────────────────────────────────────────────────
# TestSimWorkspace
# ─────────────────────────────────────────────────────────────

class TestSimWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("sim", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "sim")

    def test_max_iterations_150(self):
        self.assertEqual(self.ws.env_overrides.get("MAX_ITERATIONS"), "150")

    def test_sim_debug_template_loadable(self):
        reg = TodoTemplateRegistry()
        reg.load_from_dir(self.ws.todo_templates_dir)
        self.assertIsNotNone(reg.get("sim-debug"))

    def test_commands_dir_has_sim(self):
        self.assertIsNotNone(self.ws.commands_dir)
        self.assertTrue((self.ws.commands_dir / "sim.json").exists())


# ─────────────────────────────────────────────────────────────
# TestLintWorkspace
# ─────────────────────────────────────────────────────────────

class TestLintWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("lint", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "lint")

    def test_max_iterations_100(self):
        self.assertEqual(self.ws.env_overrides.get("MAX_ITERATIONS"), "100")

    def test_lint_fix_template_loadable(self):
        reg = TodoTemplateRegistry()
        reg.load_from_dir(self.ws.todo_templates_dir)
        self.assertIsNotNone(reg.get("lint-fix"))

    def test_commands_dir_has_lint_all(self):
        self.assertIsNotNone(self.ws.commands_dir)
        self.assertTrue((self.ws.commands_dir / "lint-all.json").exists())


# ─────────────────────────────────────────────────────────────
# TestDefaultWorkspace
# ─────────────────────────────────────────────────────────────

class TestDefaultWorkspace(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.ws = load_workspace("default", PROJECT_ROOT)

    def test_loads_without_error(self):
        self.assertIsNotNone(self.ws)

    def test_name(self):
        self.assertEqual(self.ws.name, "default")

    def test_no_force_skills(self):
        self.assertEqual(self.ws.force_skills, [])

    def test_system_prompt_mode_append(self):
        # default workspace uses append (does not override base)
        self.assertEqual(self.ws.system_prompt_mode, "append")

    def test_rules_dir_present(self):
        self.assertIsNotNone(self.ws.rules_dir)

    def test_todo_templates_has_three(self):
        reg = TodoTemplateRegistry()
        reg.load_from_dir(self.ws.todo_templates_dir)
        self.assertEqual(len(reg.list()), 3)

    def test_hook_messages_todo_continuation_has_format_vars(self):
        msg = self.ws.hook_messages.get("todo_continuation", "")
        self.assertIn("{cur_idx}", msg)

    def test_hook_messages_todo_review_present(self):
        self.assertIn("todo_review", self.ws.hook_messages)


# ─────────────────────────────────────────────────────────────
# TestAllWorkspacesConsistency
# ─────────────────────────────────────────────────────────────

class TestAllWorkspacesConsistency(unittest.TestCase):

    @classmethod
    def setUpClass(cls):
        cls.workspaces = {
            name: load_workspace(name, PROJECT_ROOT)
            for name in PRODUCTION_WORKSPACES
        }

    def test_all_production_workspaces_load(self):
        for name in PRODUCTION_WORKSPACES:
            with self.subTest(workspace=name):
                self.assertIsNotNone(self.workspaces[name])

    def test_all_have_system_prompt_text(self):
        for name, ws in self.workspaces.items():
            with self.subTest(workspace=name):
                self.assertIsNotNone(ws.system_prompt_text,
                                     f"{name} missing system_prompt.md")
                self.assertGreater(len(ws.system_prompt_text), 10)

    def test_all_have_verilog_expert_skill(self):
        for name, ws in self.workspaces.items():
            with self.subTest(workspace=name):
                self.assertIn("verilog-expert", ws.force_skills)

    def test_all_have_max_iterations_env(self):
        for name, ws in self.workspaces.items():
            with self.subTest(workspace=name):
                self.assertIn("MAX_ITERATIONS", ws.env_overrides)

    def test_all_use_prepend_system_prompt(self):
        for name, ws in self.workspaces.items():
            with self.subTest(workspace=name):
                self.assertEqual(ws.system_prompt_mode, "prepend")

    def test_all_have_todo_templates_dir(self):
        for name, ws in self.workspaces.items():
            with self.subTest(workspace=name):
                self.assertIsNotNone(ws.todo_templates_dir)
                self.assertTrue(ws.todo_templates_dir.is_dir())

    def test_all_script_files_exist_on_disk(self):
        for name, ws in self.workspaces.items():
            for spec in ws.script_hooks:
                with self.subTest(workspace=name, script=spec.script.name):
                    self.assertTrue(
                        spec.script.exists(),
                        f"{name}: script {spec.script} not found on disk"
                    )


if __name__ == "__main__":
    unittest.main()
