"""
Unit tests for workflow/loader.py

Tests every public function and class in isolation.
No LLM calls, no subprocess execution — pure logic with tempfile I/O.
"""
import builtins
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

# ── path setup (redundant with conftest but makes the file runnable directly) ──
_this = os.path.dirname(os.path.abspath(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(_this)))  # project root

from workflow.loader import (
    _check_script_conditions,
    _load_script_hooks,
    _make_command_handler,
    apply_workspace_env_early,
    get_hook_message,
    load_workspace,
    merge_prompt,
    patch_todo_rules,
    register_workspace_commands,
    ScriptHookSpec,
    TodoTemplateRegistry,
    TRIGGER_TO_HOOKPOINT_NAME,
    WorkspaceConfig,
)


# ─────────────────────────────────────────────────────────────
# TestMergePrompt
# ─────────────────────────────────────────────────────────────

class TestMergePrompt(unittest.TestCase):

    def test_append_mode(self):
        self.assertEqual(merge_prompt("BASE", "EXTRA", "append"), "BASE\n\nEXTRA")

    def test_prepend_mode(self):
        self.assertEqual(merge_prompt("BASE", "EXTRA", "prepend"), "EXTRA\n\nBASE")

    def test_replace_mode(self):
        self.assertEqual(merge_prompt("BASE", "EXTRA", "replace"), "EXTRA")

    def test_empty_text_returns_base(self):
        self.assertEqual(merge_prompt("BASE", "", "append"), "BASE")

    def test_none_text_returns_base(self):
        self.assertEqual(merge_prompt("BASE", None, "prepend"), "BASE")

    def test_unknown_mode_falls_to_append(self):
        self.assertEqual(merge_prompt("BASE", "EXTRA", "invalid"), "BASE\n\nEXTRA")

    def test_separator_is_double_newline(self):
        result = merge_prompt("A", "B", "append")
        self.assertIn("\n\n", result)
        self.assertNotIn("\n\n\n", result)

    def test_both_empty_returns_empty(self):
        self.assertEqual(merge_prompt("", "", "append"), "")

    def test_unicode_content_preserved(self):
        result = merge_prompt("베이스", "추가텍스트", "append")
        self.assertIn("베이스", result)
        self.assertIn("추가텍스트", result)

    def test_whitespace_only_text_treated_as_falsy(self):
        # "   " is truthy in Python, but check actual behaviour
        result = merge_prompt("BASE", "   ", "append")
        # loader treats empty-ish strings as present — verify separator and content
        self.assertIn("BASE", result)


# ─────────────────────────────────────────────────────────────
# TestGetHookMessage
# ─────────────────────────────────────────────────────────────

class TestGetHookMessage(unittest.TestCase):

    def setUp(self):
        self._orig = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", None)

    def tearDown(self):
        if self._orig is None:
            if hasattr(builtins, "_WORKSPACE_HOOK_MESSAGES"):
                delattr(builtins, "_WORKSPACE_HOOK_MESSAGES")
        else:
            builtins._WORKSPACE_HOOK_MESSAGES = self._orig

    def _set_registry(self, d):
        builtins._WORKSPACE_HOOK_MESSAGES = d

    def test_returns_default_when_no_registry(self):
        if hasattr(builtins, "_WORKSPACE_HOOK_MESSAGES"):
            delattr(builtins, "_WORKSPACE_HOOK_MESSAGES")
        self.assertEqual(get_hook_message("k", "default_val"), "default_val")

    def test_returns_override_from_registry(self):
        self._set_registry({"k": "custom"})
        self.assertEqual(get_hook_message("k", "default_val"), "custom")

    def test_format_substitution(self):
        self._set_registry({"greet": "Hello {name}"})
        self.assertEqual(get_hook_message("greet", "", name="World"), "Hello World")

    def test_key_not_in_registry_returns_default(self):
        self._set_registry({"other": "x"})
        self.assertEqual(get_hook_message("missing", "fallback"), "fallback")

    def test_bad_format_key_returns_template(self):
        self._set_registry({"k": "Hello {missing_var}"})
        result = get_hook_message("k", "")
        self.assertEqual(result, "Hello {missing_var}")

    def test_format_applied_to_default(self):
        self._set_registry({})
        result = get_hook_message("absent", "iter={n}", n=5)
        self.assertEqual(result, "iter=5")


# ─────────────────────────────────────────────────────────────
# TestCheckScriptConditions
# ─────────────────────────────────────────────────────────────

class TestCheckScriptConditions(unittest.TestCase):

    def _spec(self, conditions):
        return ScriptHookSpec(
            script=Path("/fake/script.sh"),
            trigger="after_tool",
            conditions=conditions,
        )

    def _ctx(self, **kwargs):
        defaults = dict(iteration=0, tool_name="", tool_args="", tool_output="")
        defaults.update(kwargs)
        return types.SimpleNamespace(**defaults)

    def test_no_conditions_always_true(self):
        self.assertTrue(_check_script_conditions(self._spec({}), self._ctx()))

    def test_tool_names_match(self):
        s = self._spec({"tool_names": ["write_file"]})
        self.assertTrue(_check_script_conditions(s, self._ctx(tool_name="write_file")))

    def test_tool_names_no_match(self):
        s = self._spec({"tool_names": ["write_file"]})
        self.assertFalse(_check_script_conditions(s, self._ctx(tool_name="run_command")))

    def test_file_extensions_match(self):
        s = self._spec({"file_extensions": [".sv", ".v"]})
        self.assertTrue(_check_script_conditions(s, self._ctx(tool_args="module.sv")))

    def test_file_extensions_no_match(self):
        s = self._spec({"file_extensions": [".sv"]})
        self.assertFalse(_check_script_conditions(s, self._ctx(tool_args="script.sh")))

    def test_every_n_iterations_pass(self):
        s = self._spec({"every_n_iterations": 5})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=10)))

    def test_every_n_iterations_fail(self):
        s = self._spec({"every_n_iterations": 5})
        self.assertFalse(_check_script_conditions(s, self._ctx(iteration=7)))

    def test_every_n_zero_always_pass(self):
        s = self._spec({"every_n_iterations": 0})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=7)))

    def test_min_iteration_pass(self):
        s = self._spec({"min_iteration": 5})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=5)))

    def test_min_iteration_fail(self):
        s = self._spec({"min_iteration": 5})
        self.assertFalse(_check_script_conditions(s, self._ctx(iteration=4)))

    def test_max_iteration_pass(self):
        s = self._spec({"max_iteration": 10})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=9)))

    def test_max_iteration_fail(self):
        s = self._spec({"max_iteration": 10})
        self.assertFalse(_check_script_conditions(s, self._ctx(iteration=11)))

    def test_output_contains_match(self):
        s = self._spec({"output_contains": ["Error"]})
        self.assertTrue(_check_script_conditions(s, self._ctx(tool_output="Error: undefined")))

    def test_output_contains_no_match(self):
        s = self._spec({"output_contains": ["Error"]})
        self.assertFalse(_check_script_conditions(s, self._ctx(tool_output="All OK")))

    def test_output_not_contains_pass(self):
        s = self._spec({"output_not_contains": ["Error"]})
        self.assertTrue(_check_script_conditions(s, self._ctx(tool_output="All OK")))

    def test_output_not_contains_fail(self):
        s = self._spec({"output_not_contains": ["Error"]})
        self.assertFalse(_check_script_conditions(s, self._ctx(tool_output="Error found")))

    def test_all_conditions_and_logic(self):
        # tool_names matches but min_iteration fails → False
        s = self._spec({"tool_names": ["write_file"], "min_iteration": 5})
        self.assertFalse(_check_script_conditions(
            s, self._ctx(tool_name="write_file", iteration=3)
        ))

    def test_output_contains_any_of_list(self):
        s = self._spec({"output_contains": ["PASS", "FAIL"]})
        self.assertTrue(_check_script_conditions(s, self._ctx(tool_output="[PASS] test")))

    def test_min_and_max_iteration_both_pass(self):
        # iteration exactly between min and max
        s = self._spec({"min_iteration": 3, "max_iteration": 10})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=5)))

    def test_min_iteration_at_boundary_passes(self):
        s = self._spec({"min_iteration": 5})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=5)))

    def test_max_iteration_at_boundary_passes(self):
        s = self._spec({"max_iteration": 5})
        self.assertTrue(_check_script_conditions(s, self._ctx(iteration=5)))

    def test_max_iteration_exceeded_fails(self):
        s = self._spec({"min_iteration": 3, "max_iteration": 10})
        self.assertFalse(_check_script_conditions(s, self._ctx(iteration=11)))


# ─────────────────────────────────────────────────────────────
# TestLoadWorkspace
# ─────────────────────────────────────────────────────────────

class TestLoadWorkspace(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.project_root = Path(self.tmp)
        self.ws_dir = self.project_root / "workflow" / "myws"
        self.ws_dir.mkdir(parents=True)

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_json(self, data):
        (self.ws_dir / "workspace.json").write_text(json.dumps(data), encoding="utf-8")

    def _write_file(self, name, content):
        (self.ws_dir / name).write_text(content, encoding="utf-8")

    def _mkdir(self, name):
        (self.ws_dir / name).mkdir(exist_ok=True)

    def test_raises_if_workspace_not_found(self):
        with self.assertRaises(FileNotFoundError):
            load_workspace("nonexistent", self.project_root)

    def test_returns_workspace_config(self):
        ws = load_workspace("myws", self.project_root)
        self.assertIsInstance(ws, WorkspaceConfig)

    def test_name_set(self):
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.name, "myws")

    def test_workspace_dir_set(self):
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.workspace_dir, self.ws_dir)

    def test_description_from_json(self):
        self._write_json({"description": "Test WS"})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.description, "Test WS")

    def test_env_overrides_from_json(self):
        self._write_json({"env": {"MAX_ITERATIONS": "100"}})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.env_overrides, {"MAX_ITERATIONS": "100"})

    def test_system_prompt_mode_from_flat_json(self):
        self._write_json({"system_prompt_mode": "prepend"})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.system_prompt_mode, "prepend")

    def test_system_prompt_mode_from_nested_prompt_block(self):
        self._write_json({"prompt": {"system_prompt_mode": "replace"}})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.system_prompt_mode, "replace")

    def test_default_mode_is_append(self):
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.system_prompt_mode, "append")

    def test_system_prompt_text_loaded(self):
        self._write_file("system_prompt.md", "Hello agent")
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.system_prompt_text, "Hello agent")

    def test_plan_prompt_text_loaded(self):
        self._write_file("plan_prompt.md", "Plan rules")
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.plan_prompt_text, "Plan rules")

    def test_compression_prompt_loaded(self):
        self._write_file("compression_prompt.md", "Compress this")
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.compression_prompt_text, "Compress this")

    def test_no_prompt_files_gives_none(self):
        ws = load_workspace("myws", self.project_root)
        self.assertIsNone(ws.system_prompt_text)
        self.assertIsNone(ws.plan_prompt_text)
        self.assertIsNone(ws.compression_prompt_text)

    def test_hook_messages_loaded(self):
        self._write_file("hook_messages.json", json.dumps({"k": "v"}))
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.hook_messages, {"k": "v"})

    def test_no_hook_messages_gives_empty_dict(self):
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.hook_messages, {})

    def test_rules_dir_detected(self):
        self._mkdir("rules")
        ws = load_workspace("myws", self.project_root)
        self.assertIsNotNone(ws.rules_dir)

    def test_rules_dir_absent_gives_none(self):
        ws = load_workspace("myws", self.project_root)
        self.assertIsNone(ws.rules_dir)

    def test_todo_templates_dir_detected(self):
        self._mkdir("todo_templates")
        ws = load_workspace("myws", self.project_root)
        self.assertIsNotNone(ws.todo_templates_dir)

    def test_scripts_dir_detected(self):
        self._mkdir("scripts")
        ws = load_workspace("myws", self.project_root)
        self.assertIsNotNone(ws.scripts_dir)

    def test_hooks_module_path_detected(self):
        self._write_file("hooks.py", "# hooks")
        ws = load_workspace("myws", self.project_root)
        self.assertIsNotNone(ws.hooks_module_path)

    def test_hooks_module_path_absent_gives_none(self):
        ws = load_workspace("myws", self.project_root)
        self.assertIsNone(ws.hooks_module_path)

    def test_force_skills_loaded(self):
        self._write_json({"skills": {"force_activate": ["verilog-expert"]}})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.force_skills, ["verilog-expert"])

    def test_disable_skills_loaded(self):
        self._write_json({"skills": {"disable": ["memory"]}})
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.disable_skills, ["memory"])

    def test_commands_dir_detected(self):
        self._mkdir("commands")
        ws = load_workspace("myws", self.project_root)
        self.assertIsNotNone(ws.commands_dir)

    def test_no_workspace_json_still_loads(self):
        # workspace.json absent — should use defaults, not raise
        ws = load_workspace("myws", self.project_root)
        self.assertEqual(ws.name, "myws")
        self.assertEqual(ws.env_overrides, {})


# ─────────────────────────────────────────────────────────────
# TestLoadScriptHooks
# ─────────────────────────────────────────────────────────────

class TestLoadScriptHooks(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write_sh(self, name, content="#!/bin/bash\n"):
        p = self.tmp / name
        p.write_text(content)
        return p

    def _write_hooks_json(self, hooks):
        (self.tmp / "hooks.json").write_text(json.dumps({"hooks": hooks}))

    def test_empty_dir_returns_empty_list(self):
        result = _load_script_hooks(self.tmp)
        self.assertEqual(result, [])

    def test_hooks_json_parsed(self):
        self._write_sh("post.sh")
        self._write_hooks_json([{"script": "post.sh", "trigger": "after_tool"}])
        result = _load_script_hooks(self.tmp)
        self.assertEqual(len(result), 1)

    def test_hooks_json_trigger_set(self):
        self._write_sh("post.sh")
        self._write_hooks_json([{"script": "post.sh", "trigger": "after_tool"}])
        self.assertEqual(_load_script_hooks(self.tmp)[0].trigger, "after_tool")

    def test_hooks_json_conditions_set(self):
        self._write_sh("post.sh")
        conds = {"tool_names": ["write_file"]}
        self._write_hooks_json([{"script": "post.sh", "trigger": "after_tool", "conditions": conds}])
        self.assertEqual(_load_script_hooks(self.tmp)[0].conditions, conds)

    def test_hooks_json_skips_missing_script(self):
        # hooks.json references a script that does not exist on disk
        self._write_hooks_json([{"script": "missing.sh", "trigger": "after_tool"}])
        self.assertEqual(_load_script_hooks(self.tmp), [])

    def test_fallback_filename_pattern_after_tool(self):
        self._write_sh("post_tool_exec.sh")
        result = _load_script_hooks(self.tmp)
        self.assertEqual(len(result), 1)
        self.assertEqual(result[0].trigger, "after_tool")

    def test_fallback_unknown_filename_skipped(self):
        self._write_sh("unknown_script.sh")
        self.assertEqual(_load_script_hooks(self.tmp), [])

    def test_multiple_hooks_loaded(self):
        self._write_sh("a.sh")
        self._write_sh("b.sh")
        self._write_hooks_json([
            {"script": "a.sh", "trigger": "after_tool"},
            {"script": "b.sh", "trigger": "before_llm"},
        ])
        self.assertEqual(len(_load_script_hooks(self.tmp)), 2)

    def test_script_path_is_absolute(self):
        self._write_sh("post.sh")
        self._write_hooks_json([{"script": "post.sh", "trigger": "after_tool"}])
        spec = _load_script_hooks(self.tmp)[0]
        self.assertTrue(spec.script.is_absolute())


# ─────────────────────────────────────────────────────────────
# TestTodoTemplateRegistry
# ─────────────────────────────────────────────────────────────

class TestTodoTemplateRegistry(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.reg = TodoTemplateRegistry()

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _write(self, stem, data):
        (self.tmp / f"{stem}.json").write_text(json.dumps(data), encoding="utf-8")

    def test_empty_registry_list_is_empty(self):
        self.assertEqual(self.reg.list(), [])

    def test_load_from_dir_populates(self):
        self._write("foo", {"name": "foo", "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.assertIn("foo", self.reg.list())

    def test_get_returns_parsed_dict(self):
        data = {"name": "foo", "tasks": []}
        self._write("foo", data)
        self.reg.load_from_dir(self.tmp)
        self.assertEqual(self.reg.get("foo"), data)

    def test_get_nonexistent_returns_none(self):
        self.assertIsNone(self.reg.get("missing"))

    def test_get_tasks_returns_task_list(self):
        tasks = [{"content": "do it", "priority": "high"}]
        self._write("bar", {"name": "bar", "tasks": tasks})
        self.reg.load_from_dir(self.tmp)
        self.assertEqual(self.reg.get_tasks("bar"), tasks)

    def test_get_tasks_missing_key_returns_none(self):
        self._write("bar", {"name": "bar"})
        self.reg.load_from_dir(self.tmp)
        self.assertIsNone(self.reg.get_tasks("bar"))

    def test_get_template_alias_works(self):
        self._write("foo", {"name": "foo", "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.assertEqual(self.reg.get_template("foo"), self.reg.get("foo"))

    def test_list_templates_alias_works(self):
        self._write("foo", {"name": "foo", "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.assertEqual(self.reg.list_templates(), self.reg.list())

    def test_invalid_json_skipped(self):
        (self.tmp / "bad.json").write_text("not valid json")
        self._write("good", {"name": "good", "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.assertIn("good", self.reg.list())
        self.assertNotIn("bad", self.reg.list())

    def test_multiple_files_loaded(self):
        for name in ["a", "b", "c"]:
            self._write(name, {"name": name, "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.assertEqual(len(self.reg.list()), 3)

    def test_get_tasks_none_when_registry_empty(self):
        self.assertIsNone(self.reg.get_tasks("anything"))

    def test_load_is_idempotent(self):
        self._write("foo", {"name": "foo", "tasks": []})
        self.reg.load_from_dir(self.tmp)
        self.reg.load_from_dir(self.tmp)
        # Duplicate load overwrites — still only one entry
        self.assertEqual(self.reg.list().count("foo"), 1)


# ─────────────────────────────────────────────────────────────
# TestApplyWorkspaceEnvEarly
# ─────────────────────────────────────────────────────────────

class TestApplyWorkspaceEnvEarly(unittest.TestCase):

    def setUp(self):
        self._orig_argv = sys.argv[:]
        self.tmp = Path(tempfile.mkdtemp())
        self._injected_keys = []

    def tearDown(self):
        sys.argv = self._orig_argv
        for k in self._injected_keys:
            os.environ.pop(k, None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_ws(self, name, env_data):
        ws_dir = self.tmp / "workflow" / name
        ws_dir.mkdir(parents=True)
        (ws_dir / "workspace.json").write_text(json.dumps({"env": env_data}))

    def test_no_workspace_arg_returns_none(self):
        sys.argv = ["main.py"]
        result = apply_workspace_env_early(self.tmp)
        self.assertIsNone(result)

    def test_w_flag_returns_name(self):
        self._make_ws("myws", {})
        sys.argv = ["main.py", "-w", "myws"]
        result = apply_workspace_env_early(self.tmp)
        self.assertEqual(result, "myws")

    def test_workspace_eq_flag_returns_name(self):
        self._make_ws("myws", {})
        sys.argv = ["main.py", "--workspace=myws"]
        result = apply_workspace_env_early(self.tmp)
        self.assertEqual(result, "myws")

    def test_env_vars_injected(self):
        key = "_TEST_WS_VAR_XYZ"
        self._injected_keys.append(key)
        os.environ.pop(key, None)
        self._make_ws("myws", {key: "42"})
        sys.argv = ["main.py", "-w", "myws"]
        apply_workspace_env_early(self.tmp)
        self.assertEqual(os.environ.get(key), "42")

    def test_shell_env_takes_priority(self):
        key = "_TEST_WS_PRIO_XYZ"
        self._injected_keys.append(key)
        os.environ[key] = "shell_value"
        self._make_ws("myws", {key: "ws_value"})
        sys.argv = ["main.py", "-w", "myws"]
        apply_workspace_env_early(self.tmp)
        self.assertEqual(os.environ[key], "shell_value")

    def test_missing_workspace_json_returns_name_only(self):
        # workspace dir absent — should not raise
        sys.argv = ["main.py", "-w", "ghost"]
        result = apply_workspace_env_early(self.tmp)
        self.assertEqual(result, "ghost")


# ─────────────────────────────────────────────────────────────
# TestMakeCommandHandler
# ─────────────────────────────────────────────────────────────

class TestMakeCommandHandler(unittest.TestCase):

    def _ws(self, scripts_dir=None):
        """Minimal WorkspaceConfig stub."""
        return types.SimpleNamespace(scripts_dir=scripts_dir, name="test")

    def test_todo_template_handler_returns_signal(self):
        h = _make_command_handler({"handler": "todo:template:mytempl"}, self._ws())
        self.assertEqual(h(""), "INJECT_TODO_TEMPLATE:mytempl")

    def test_prompt_handler_returns_signal(self):
        h = _make_command_handler({"handler": "prompt:run lint now"}, self._ws())
        self.assertEqual(h(""), "INJECT_PROMPT:run lint now")

    def test_unknown_handler_returns_error(self):
        h = _make_command_handler({"handler": "unknown:foo"}, self._ws())
        result = h("")
        self.assertIn("[Error]", result)

    def test_bash_handler_missing_scripts_dir_returns_error(self):
        h = _make_command_handler({"handler": "bash:nonexistent.sh"}, self._ws(scripts_dir=None))
        result = h("")
        self.assertIn("[Error]", result)

    def test_todo_template_ignores_args(self):
        h = _make_command_handler({"handler": "todo:template:x"}, self._ws())
        self.assertEqual(h("some args"), "INJECT_TODO_TEMPLATE:x")


# ─────────────────────────────────────────────────────────────
# TestWorkspaceConfigDefaults
# ─────────────────────────────────────────────────────────────

class TestWorkspaceConfigDefaults(unittest.TestCase):
    """WorkspaceConfig dataclass field defaults."""

    def _minimal(self):
        return WorkspaceConfig(name="test", workspace_dir=Path("/tmp/test"))

    def test_force_skills_defaults_to_empty_list(self):
        self.assertEqual(self._minimal().force_skills, [])

    def test_disable_skills_defaults_to_empty_list(self):
        self.assertEqual(self._minimal().disable_skills, [])

    def test_script_hooks_defaults_to_empty_list(self):
        self.assertEqual(self._minimal().script_hooks, [])

    def test_env_overrides_defaults_to_empty_dict(self):
        self.assertEqual(self._minimal().env_overrides, {})

    def test_hook_messages_defaults_to_empty_dict(self):
        self.assertEqual(self._minimal().hook_messages, {})

    def test_system_prompt_mode_defaults_to_append(self):
        self.assertEqual(self._minimal().system_prompt_mode, "append")

    def test_plan_prompt_mode_defaults_to_append(self):
        self.assertEqual(self._minimal().plan_prompt_mode, "append")

    def test_optional_dirs_default_to_none(self):
        ws = self._minimal()
        for attr in ("rules_dir", "todo_templates_dir", "scripts_dir",
                     "hooks_module_path", "extra_skills_dir", "commands_dir"):
            with self.subTest(attr=attr):
                self.assertIsNone(getattr(ws, attr))

    def test_optional_prompts_default_to_none(self):
        ws = self._minimal()
        for attr in ("system_prompt_text", "plan_prompt_text", "compression_prompt_text"):
            with self.subTest(attr=attr):
                self.assertIsNone(getattr(ws, attr))

    def test_name_and_workspace_dir_set(self):
        ws = self._minimal()
        self.assertEqual(ws.name, "test")
        self.assertEqual(ws.workspace_dir, Path("/tmp/test"))

    def test_description_defaults_to_empty_string(self):
        self.assertEqual(self._minimal().description, "")


# ─────────────────────────────────────────────────────────────
# TestTriggerConstants
# ─────────────────────────────────────────────────────────────

class TestTriggerConstants(unittest.TestCase):
    """TRIGGER_TO_HOOKPOINT_NAME and _FILENAME_TO_TRIGGER completeness."""

    def test_all_expected_trigger_keys_present(self):
        expected = {
            "before_llm", "after_llm", "before_tool", "after_tool",
            "on_error", "on_session_start", "on_session_end",
        }
        self.assertEqual(set(TRIGGER_TO_HOOKPOINT_NAME.keys()), expected)

    def test_hookpoint_values_are_uppercase(self):
        for trigger, hookpoint in TRIGGER_TO_HOOKPOINT_NAME.items():
            with self.subTest(trigger=trigger):
                self.assertEqual(hookpoint, hookpoint.upper())

    def test_filename_trigger_covers_expected_stems(self):
        from workflow.loader import _FILENAME_TO_TRIGGER
        expected_stems = {
            "pre_tool_exec", "post_tool_exec", "pre_llm", "post_llm",
            "on_error", "on_session_start", "on_session_end",
        }
        self.assertTrue(expected_stems.issubset(set(_FILENAME_TO_TRIGGER.keys())))

    def test_all_filename_triggers_are_valid_trigger_keys(self):
        from workflow.loader import _FILENAME_TO_TRIGGER
        for stem, trigger in _FILENAME_TO_TRIGGER.items():
            with self.subTest(stem=stem):
                self.assertIn(trigger, TRIGGER_TO_HOOKPOINT_NAME)

    def test_trigger_to_hookpoint_has_no_duplicate_values(self):
        values = list(TRIGGER_TO_HOOKPOINT_NAME.values())
        self.assertEqual(len(values), len(set(values)))


# ─────────────────────────────────────────────────────────────
# TestPatchTodoRules
# ─────────────────────────────────────────────────────────────

class TestPatchTodoRules(unittest.TestCase):
    """patch_todo_rules() monkey-patches lib.todo_tracker._load_todo_rule."""

    def setUp(self):
        import lib.todo_tracker as _tt
        self._tt = _tt
        self._orig_load = _tt._load_todo_rule
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        # Always restore original function
        self._tt._load_todo_rule = self._orig_load
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _ws(self, rules_dir=None):
        return types.SimpleNamespace(rules_dir=rules_dir)

    def _write_rule(self, rules_dir, stem, content):
        (rules_dir / f"{stem}.md").write_text(content, encoding="utf-8")

    def test_no_rules_dir_is_noop(self):
        ws = self._ws(rules_dir=None)
        patch_todo_rules(ws)
        self.assertIs(self._tt._load_todo_rule, self._orig_load)

    def test_nonexistent_rules_dir_is_noop(self):
        ws = self._ws(rules_dir=self.tmp / "no_such_dir")
        patch_todo_rules(ws)
        self.assertIs(self._tt._load_todo_rule, self._orig_load)

    def test_rules_dir_replaces_load_function(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "rule1", "# Rule 1\ndo X")
        ws = self._ws(rules_dir=rules_dir)
        patch_todo_rules(ws)
        self.assertIsNot(self._tt._load_todo_rule, self._orig_load)

    def test_extra_rules_appended_to_base(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "my_rule", "# MyRule\nextra-content")
        ws = self._ws(rules_dir=rules_dir)
        self._tt._load_todo_rule = lambda: "BASE_RULE"
        patch_todo_rules(ws)
        result = self._tt._load_todo_rule()
        self.assertIn("BASE_RULE", result)
        self.assertIn("extra-content", result)

    def test_multiple_md_files_all_merged(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "a_rule", "# A\nalpha-content")
        self._write_rule(rules_dir, "b_rule", "# B\nbeta-content")
        ws = self._ws(rules_dir=rules_dir)
        self._tt._load_todo_rule = lambda: ""
        patch_todo_rules(ws)
        result = self._tt._load_todo_rule()
        self.assertIn("alpha-content", result)
        self.assertIn("beta-content", result)

    def test_files_sorted_alphabetically(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "z_rule", "# Z\nz-content")
        self._write_rule(rules_dir, "a_rule", "# A\na-content")
        ws = self._ws(rules_dir=rules_dir)
        self._tt._load_todo_rule = lambda: ""
        patch_todo_rules(ws)
        result = self._tt._load_todo_rule()
        self.assertLess(result.index("a-content"), result.index("z-content"))

    def test_empty_md_file_skipped(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "empty", "   \n\n  ")   # whitespace only
        ws = self._ws(rules_dir=rules_dir)
        self._tt._load_todo_rule = lambda: "BASE"
        patch_todo_rules(ws)
        result = self._tt._load_todo_rule()
        # Whitespace-only file has no content → base returned unchanged
        self.assertEqual(result.strip(), "BASE")

    def test_when_base_empty_returns_extra_only(self):
        rules_dir = self.tmp / "rules"
        rules_dir.mkdir()
        self._write_rule(rules_dir, "r", "# R\nmy-rule-text")
        ws = self._ws(rules_dir=rules_dir)
        self._tt._load_todo_rule = lambda: ""
        patch_todo_rules(ws)
        result = self._tt._load_todo_rule()
        self.assertIn("my-rule-text", result)


# ─────────────────────────────────────────────────────────────
# TestRegisterWorkspaceCommands
# ─────────────────────────────────────────────────────────────

class TestRegisterWorkspaceCommands(unittest.TestCase):
    """register_workspace_commands() loads commands/*.json → slash registry."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.registered = []

    def tearDown(self):
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _mock_registry(self):
        outer = self

        class _Reg:
            def register(self, name, handler, description="", aliases=[], usage=""):
                outer.registered.append({
                    "name": name,
                    "handler": handler,
                    "aliases": list(aliases),
                })

        return _Reg()

    def _ws(self, commands_dir=None, scripts_dir=None):
        return types.SimpleNamespace(
            commands_dir=commands_dir,
            scripts_dir=scripts_dir,
            name="testws",
            workspace_dir=self.tmp,
        )

    def _write_cmd(self, stem, spec):
        cmd_dir = self.tmp / "commands"
        cmd_dir.mkdir(exist_ok=True)
        (cmd_dir / f"{stem}.json").write_text(json.dumps(spec), encoding="utf-8")
        return cmd_dir

    def test_no_commands_dir_noop(self):
        register_workspace_commands(self._ws(commands_dir=None), self._mock_registry())
        self.assertEqual(self.registered, [])

    def test_empty_commands_dir_noop(self):
        cmd_dir = self.tmp / "commands"
        cmd_dir.mkdir()
        register_workspace_commands(self._ws(commands_dir=cmd_dir), self._mock_registry())
        self.assertEqual(self.registered, [])

    def test_valid_command_registered(self):
        cmd_dir = self._write_cmd("lint", {
            "name": "lint",
            "handler": "todo:template:lint-fix",
        })
        register_workspace_commands(self._ws(commands_dir=cmd_dir), self._mock_registry())
        self.assertEqual(len(self.registered), 1)
        self.assertEqual(self.registered[0]["name"], "lint")

    def test_aliases_passed_to_registry(self):
        cmd_dir = self._write_cmd("sim", {
            "name": "sim",
            "handler": "todo:template:sim-debug",
            "aliases": ["s", "simulate"],
        })
        register_workspace_commands(self._ws(commands_dir=cmd_dir), self._mock_registry())
        self.assertEqual(self.registered[0]["aliases"], ["s", "simulate"])

    def test_invalid_json_continues_loading_others(self):
        cmd_dir = self.tmp / "commands"
        cmd_dir.mkdir()
        (cmd_dir / "bad.json").write_text("not valid json")
        (cmd_dir / "good.json").write_text(json.dumps({
            "name": "good", "handler": "todo:template:x",
        }))
        register_workspace_commands(self._ws(commands_dir=cmd_dir), self._mock_registry())
        self.assertEqual(len(self.registered), 1)
        self.assertEqual(self.registered[0]["name"], "good")

    def test_multiple_commands_all_registered(self):
        cmd_dir = self.tmp / "commands"
        cmd_dir.mkdir()
        for name in ["sim", "lint", "gen-tc"]:
            (cmd_dir / f"{name}.json").write_text(json.dumps({
                "name": name, "handler": f"todo:template:{name}",
            }))
        register_workspace_commands(self._ws(commands_dir=cmd_dir), self._mock_registry())
        self.assertEqual(len(self.registered), 3)
        names = {r["name"] for r in self.registered}
        self.assertEqual(names, {"sim", "lint", "gen-tc"})

    def test_prompt_handler_callable(self):
        """Handler wired as prompt: type returns INJECT_PROMPT signal."""
        handlers = {}

        class _Reg:
            def register(self, name, handler, description="", aliases=[], usage=""):
                handlers[name] = handler

        cmd_dir = self._write_cmd("hello", {
            "name": "hello",
            "handler": "prompt:run the lint check now",
        })
        register_workspace_commands(self._ws(commands_dir=cmd_dir), _Reg())
        self.assertIn("hello", handlers)
        self.assertEqual(handlers["hello"](""), "INJECT_PROMPT:run the lint check now")

    def test_todo_template_handler_callable(self):
        """Handler wired as todo:template: type returns INJECT_TODO_TEMPLATE signal."""
        handlers = {}

        class _Reg:
            def register(self, name, handler, description="", aliases=[], usage=""):
                handlers[name] = handler

        cmd_dir = self._write_cmd("full", {
            "name": "full",
            "handler": "todo:template:full-project",
        })
        register_workspace_commands(self._ws(commands_dir=cmd_dir), _Reg())
        self.assertEqual(handlers["full"](""), "INJECT_TODO_TEMPLATE:full-project")

    def test_bash_handler_missing_scripts_dir_returns_error(self):
        """bash: handler with no scripts_dir → [Error] immediately."""
        handlers = {}

        class _Reg:
            def register(self, name, handler, description="", aliases=[], usage=""):
                handlers[name] = handler

        cmd_dir = self._write_cmd("run", {
            "name": "run",
            "handler": "bash:run.sh",
        })
        ws = self._ws(commands_dir=cmd_dir, scripts_dir=None)
        register_workspace_commands(ws, _Reg())
        result = handlers["run"]("")
        self.assertIn("[Error]", result)


if __name__ == "__main__":
    unittest.main()
