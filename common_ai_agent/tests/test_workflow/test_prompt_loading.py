"""
Integration tests for system prompt, plan prompt, and todo template loading.

Tests the _setup_workspace() pipeline (src/main.py) end-to-end:

  Step 2 — system prompt patch:
      build_system_prompt() is monkey-patched so workspace prompt is merged.
  Step 3 — plan prompt patch:
      config.PLAN_MODE_PROMPT is rewritten with workspace plan_prompt_text.
  Step 4 — compression prompt patch:
      compressor.STRUCTURED_SUMMARY_PROMPT replaced with workspace text.
  Step 7 — todo template registration:
      builtins._TODO_TEMPLATE_REGISTRY holds loaded templates; /todo template works.

All tests simulate the patching logic from _setup_workspace() directly so
we can verify each mechanism without spinning up a full chat_loop.
No LLM calls, no network, no subprocess.
"""
import builtins
import importlib
import json
import os
import shutil
import sys
import tempfile
import types
import unittest
from pathlib import Path

_this = os.path.dirname(os.path.abspath(__file__))
_root = os.path.dirname(os.path.dirname(_this))
sys.path.insert(0, _root)
sys.path.insert(0, os.path.join(_root, "src"))


# ─────────────────────────────────────────────────────────────
# Helpers
# ─────────────────────────────────────────────────────────────

def _make_fake_cfg(build_fn=None):
    """Minimal config namespace with build_base_system_prompt."""
    if build_fn is None:
        def build_fn(allowed_tools=None, plan_mode=False, todo_active=False):
            return "BASE_PROMPT"
    cfg = types.SimpleNamespace(
        build_base_system_prompt=build_fn,
        PLAN_MODE_PROMPT="DEFAULT_PLAN_PROMPT",
        PLAN_MODE_BLOCKED_TOOLS=set(),
        NORMAL_MODE_BLOCKED_TOOLS=set(),
        DEBUG_MODE=False,
        CACHE_OPTIMIZATION_MODE="legacy",
        ENABLE_SKILL_SYSTEM=False,
        ENABLE_SMART_RAG=False,
        PROCEDURAL_INJECT_GUIDANCE=False,
    )
    return cfg


def _build_prompt(ws_text, ws_mode, base="BASE_PROMPT"):
    """Simulate the _patched_build_system_prompt logic from _setup_workspace."""
    from workflow.loader import merge_prompt

    def orig_build(ctx=None, **kwargs):
        return base

    def patched(ctx=None, **kwargs):
        result = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
        if isinstance(result, dict):
            result = (result.get("static", "") + "\n\n" + result.get("dynamic", "")).strip()
        return merge_prompt(result, ws_text, ws_mode)

    return patched


# ─────────────────────────────────────────────────────────────
# TestSystemPromptPatch  —  Step 2 of _setup_workspace
# ─────────────────────────────────────────────────────────────

class TestSystemPromptPatch(unittest.TestCase):
    """
    Verify that the system prompt monkey-patch works correctly:
    workspace text is merged into the result of build_system_prompt()
    according to the configured mode.
    """

    def test_append_mode_adds_workspace_text(self):
        patched = _build_prompt("WS_RULES", "append", base="BASE")
        result = patched()
        self.assertIn("BASE", result)
        self.assertIn("WS_RULES", result)
        # append → base comes first
        self.assertLess(result.index("BASE"), result.index("WS_RULES"))

    def test_prepend_mode_puts_workspace_first(self):
        patched = _build_prompt("WS_RULES", "prepend", base="BASE")
        result = patched()
        self.assertLess(result.index("WS_RULES"), result.index("BASE"))

    def test_replace_mode_only_workspace_text(self):
        patched = _build_prompt("WS_ONLY", "replace", base="BASE")
        result = patched()
        self.assertEqual(result, "WS_ONLY")
        self.assertNotIn("BASE", result)

    def test_empty_workspace_text_returns_base(self):
        patched = _build_prompt("", "append", base="BASE")
        result = patched()
        self.assertEqual(result, "BASE")

    def test_dict_base_merged_correctly(self):
        """When original build returns dict{static,dynamic}, must be merged to str first."""
        from workflow.loader import merge_prompt

        def orig_build(ctx=None, **kwargs):
            return {"static": "STATIC_PART", "dynamic": "DYNAMIC_PART"}

        def patched(ctx=None, **kwargs):
            result = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
            if isinstance(result, dict):
                result = (result.get("static", "") + "\n\n" + result.get("dynamic", "")).strip()
            return merge_prompt(result, "WS_TEXT", "append")

        final = patched()
        self.assertIsInstance(final, str)
        self.assertIn("STATIC_PART", final)
        self.assertIn("DYNAMIC_PART", final)
        self.assertIn("WS_TEXT", final)

    def test_real_mas-gen_system_prompt_appended(self):
        """Load real mas-gen workspace and verify system_prompt_text is non-trivial."""
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", Path(_root))
        patched = _build_prompt(ws.system_prompt_text, ws.system_prompt_mode)
        result = patched()
        self.assertIn("BASE_PROMPT", result)
        # mas-gen uses prepend — workspace text should come first
        self.assertLess(result.index(ws.system_prompt_text[:20]), result.index("BASE_PROMPT"))

    def test_real_rtl-gen_system_prompt_loaded(self):
        from workflow.loader import load_workspace
        ws = load_workspace("rtl-gen", Path(_root))
        self.assertIsNotNone(ws.system_prompt_text)
        # RTL coding rules should be in the text
        self.assertIn("always_ff", ws.system_prompt_text)

    def test_real_tb-gen_system_prompt_loaded(self):
        from workflow.loader import load_workspace
        ws = load_workspace("tb-gen", Path(_root))
        self.assertIsNotNone(ws.system_prompt_text)
        self.assertIn("testbench", ws.system_prompt_text.lower())

    def test_build_system_prompt_with_workflow_identity(self):
        """When ACTIVE_WORKSPACE is set, [Workflow: X] appears in the real builder output."""
        orig = os.environ.pop("ACTIVE_WORKSPACE", None)
        orig_desc = os.environ.pop("ACTIVE_WORKSPACE_DESC", None)
        try:
            os.environ["ACTIVE_WORKSPACE"] = "mas-gen"
            import core.prompt_builder as pb
            importlib.reload(pb)
            result = pb.build_system_prompt(build_base_fn=lambda **kw: "BASE")
            text = result if isinstance(result, str) else result.get("static", "")
            self.assertIn("[Workflow: mas-gen]", text)
        finally:
            if orig:
                os.environ["ACTIVE_WORKSPACE"] = orig
            else:
                os.environ.pop("ACTIVE_WORKSPACE", None)
            if orig_desc:
                os.environ["ACTIVE_WORKSPACE_DESC"] = orig_desc
            else:
                os.environ.pop("ACTIVE_WORKSPACE_DESC", None)

    def test_build_system_prompt_str_always_returns_string(self):
        """_build_system_prompt_str() must return str even when builder returns dict."""
        import core.prompt_builder as pb
        importlib.reload(pb)

        original = pb.build_system_prompt
        try:
            pb.build_system_prompt = lambda **kw: {"static": "S", "dynamic": "D"}
            result = pb._build_system_prompt_str()
            self.assertIsInstance(result, str)
            self.assertIn("S", result)
            self.assertIn("D", result)
        finally:
            pb.build_system_prompt = original


# ─────────────────────────────────────────────────────────────
# TestPlanPromptPatch  —  Step 3 of _setup_workspace
# ─────────────────────────────────────────────────────────────

class TestPlanPromptPatch(unittest.TestCase):
    """
    Verify that config.PLAN_MODE_PROMPT is patched correctly when
    a workspace provides plan_prompt_text.
    """

    def _apply_patch(self, original_plan_prompt, ws_plan_text, ws_plan_mode):
        """Replicate the _setup_workspace Step 3 logic."""
        from workflow.loader import merge_prompt
        import types
        cfg = types.SimpleNamespace(PLAN_MODE_PROMPT=original_plan_prompt)
        if ws_plan_text and hasattr(cfg, "PLAN_MODE_PROMPT"):
            cfg.PLAN_MODE_PROMPT = merge_prompt(
                cfg.PLAN_MODE_PROMPT, ws_plan_text, ws_plan_mode
            )
        return cfg.PLAN_MODE_PROMPT

    def test_plan_prompt_appended(self):
        result = self._apply_patch("ORIGINAL", "WS_PLAN", "append")
        self.assertIn("ORIGINAL", result)
        self.assertIn("WS_PLAN", result)
        self.assertLess(result.index("ORIGINAL"), result.index("WS_PLAN"))

    def test_plan_prompt_prepended(self):
        result = self._apply_patch("ORIGINAL", "WS_PLAN", "prepend")
        self.assertLess(result.index("WS_PLAN"), result.index("ORIGINAL"))

    def test_plan_prompt_replaced(self):
        result = self._apply_patch("ORIGINAL", "WS_PLAN", "replace")
        self.assertEqual(result, "WS_PLAN")
        self.assertNotIn("ORIGINAL", result)

    def test_none_plan_text_leaves_original(self):
        result = self._apply_patch("ORIGINAL", None, "append")
        self.assertEqual(result, "ORIGINAL")

    def test_empty_plan_text_leaves_original(self):
        result = self._apply_patch("ORIGINAL", "", "append")
        self.assertEqual(result, "ORIGINAL")

    def test_real_mas-gen_plan_prompt_text_loaded(self):
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", Path(_root))
        self.assertIsNotNone(ws.plan_prompt_text)
        self.assertGreater(len(ws.plan_prompt_text), 10)
        result = self._apply_patch("ORIGINAL_PLAN", ws.plan_prompt_text, ws.plan_prompt_mode)
        # mas-gen uses prepend — workspace rules first
        self.assertIn(ws.plan_prompt_text[:20], result)

    def test_real_rtl-gen_plan_prompt_text_loaded(self):
        from workflow.loader import load_workspace
        ws = load_workspace("rtl-gen", Path(_root))
        self.assertIsNotNone(ws.plan_prompt_text)
        # RTL plan prompt should mention reading spec or tasks
        self.assertTrue(len(ws.plan_prompt_text) > 5)

    def test_plan_prompt_injected_in_build_base(self):
        """build_base_system_prompt() with plan_mode=True includes PLAN_MODE_PROMPT text."""
        import config as cfg
        base = cfg.build_base_system_prompt(plan_mode=True)
        # The base prompt in plan mode must contain the plan mode instructions
        self.assertIn("PLAN MODE", base.upper())

    def test_plan_mode_blocked_tools_differ_from_normal(self):
        """Plan mode and normal mode should block different tool sets."""
        import config as cfg
        plan_blocked = getattr(cfg, "PLAN_MODE_BLOCKED_TOOLS", set())
        normal_blocked = getattr(cfg, "NORMAL_MODE_BLOCKED_TOOLS", set())
        # They shouldn't be identical (plan mode has different restrictions)
        self.assertNotEqual(plan_blocked, normal_blocked)

    def test_build_system_prompt_plan_mode_includes_plan_text(self):
        """build_system_prompt(agent_mode='plan') should produce a different prompt than normal."""
        import core.prompt_builder as pb
        importlib.reload(pb)
        import config as cfg

        plan_result = pb.build_system_prompt(
            agent_mode="plan",
            build_base_fn=cfg.build_base_system_prompt,
        )
        normal_result = pb.build_system_prompt(
            agent_mode=None,
            build_base_fn=cfg.build_base_system_prompt,
        )
        plan_text = plan_result if isinstance(plan_result, str) else plan_result.get("static", "")
        normal_text = normal_result if isinstance(normal_result, str) else normal_result.get("static", "")
        # Plan prompt must differ from normal
        self.assertNotEqual(plan_text, normal_text)


# ─────────────────────────────────────────────────────────────
# TestTodoPromptLoading  —  Step 7 of _setup_workspace
# ─────────────────────────────────────────────────────────────

class TestTodoPromptLoading(unittest.TestCase):
    """
    Verify the todo template registration pipeline:
    - builtins._TODO_TEMPLATE_REGISTRY is populated after workspace load
    - /todo template <name> writes tasks to a todo file
    - /todo templates shows the available template list
    """

    def setUp(self):
        self._orig_registry = getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None)
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        if self._orig_registry is None:
            if hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"):
                delattr(builtins, "_TODO_TEMPLATE_REGISTRY")
        else:
            builtins._TODO_TEMPLATE_REGISTRY = self._orig_registry
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _make_registry(self, templates: dict):
        """Create and install a TodoTemplateRegistry with given templates."""
        from workflow.loader import TodoTemplateRegistry
        reg = TodoTemplateRegistry()
        for stem, data in templates.items():
            (self.tmp / f"{stem}.json").write_text(json.dumps(data))
        reg.load_from_dir(self.tmp)
        builtins._TODO_TEMPLATE_REGISTRY = reg
        return reg

    # ── Registry population ──────────────────────────────────

    def test_registry_installed_in_builtins(self):
        self._make_registry({"foo": {"name": "foo", "tasks": []}})
        self.assertIsNotNone(getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None))

    def test_registry_lists_loaded_templates(self):
        self._make_registry({"tmpl-a": {"name": "a", "tasks": []},
                             "tmpl-b": {"name": "b", "tasks": []}})
        reg = builtins._TODO_TEMPLATE_REGISTRY
        self.assertIn("tmpl-a", reg.list())
        self.assertIn("tmpl-b", reg.list())

    def test_registry_get_tasks_returns_task_list(self):
        tasks = [{"content": "step 1", "priority": "high"}]
        self._make_registry({"my-tmpl": {"name": "my-tmpl", "tasks": tasks}})
        reg = builtins._TODO_TEMPLATE_REGISTRY
        self.assertEqual(reg.get_tasks("my-tmpl"), tasks)

    def test_real_mas-gen_full_project_registered(self):
        """After simulating workspace load, full-project template is accessible."""
        from workflow.loader import TodoTemplateRegistry, load_workspace
        ws = load_workspace("mas-gen", Path(_root))
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        builtins._TODO_TEMPLATE_REGISTRY = reg
        tasks = reg.get_tasks("full-project")
        self.assertIsNotNone(tasks)
        self.assertEqual(len(tasks), 10)

    def test_real_rtl_impl_template_registered(self):
        from workflow.loader import TodoTemplateRegistry, load_workspace
        ws = load_workspace("rtl-gen", Path(_root))
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        tasks = reg.get_tasks("rtl-impl")
        self.assertIsNotNone(tasks)
        self.assertEqual(len(tasks), 8)

    def test_real_tb_impl_template_registered(self):
        from workflow.loader import TodoTemplateRegistry, load_workspace
        ws = load_workspace("tb-gen", Path(_root))
        reg = TodoTemplateRegistry()
        reg.load_from_dir(ws.todo_templates_dir)
        tasks = reg.get_tasks("tb-impl")
        self.assertIsNotNone(tasks)
        self.assertEqual(len(tasks), 6)

    # ── /todo templates command ─────────────────────────────

    def test_todo_templates_cmd_lists_names(self):
        self._make_registry({"feature": {"name": "feature", "description": "feat desc",
                                         "tasks": [{"content": "t", "priority": "high"}]}})
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg.execute("/todo templates")
        self.assertIn("feature", result)

    def test_todo_templates_cmd_shows_task_count(self):
        tasks = [{"content": f"t{i}", "priority": "high"} for i in range(3)]
        self._make_registry({"my-flow": {"name": "my-flow", "description": "x", "tasks": tasks}})
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg.execute("/todo templates")
        self.assertIn("my-flow", result)
        self.assertIn("3", result)

    def test_todo_templates_cmd_no_registry_graceful(self):
        if hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"):
            delattr(builtins, "_TODO_TEMPLATE_REGISTRY")
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg.execute("/todo templates")
        # Should return a helpful message, not raise
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 0)

    # ── /todo template <name> loading ──────────────────────

    def test_todo_template_load_creates_tasks(self):
        tasks = [
            {"content": "[MAS] Write spec", "priority": "high", "activeForm": "Writing..."},
            {"content": "[RTL] Implement", "priority": "high", "activeForm": "Implementing..."},
        ]
        self._make_registry({"mini-flow": {"name": "mini-flow", "tasks": tasks}})
        todo_file = str(self.tmp / "todo.json")

        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        # Patch _get_todo_file to return our temp file
        reg._todo_file = todo_file

        result = reg._todo_load_template("mini-flow", todo_file)
        self.assertIn("mini-flow", result)
        self.assertIn("2 tasks", result)
        # Verify tasks were actually written
        import json as _json
        data = _json.loads(Path(todo_file).read_text())
        self.assertEqual(len(data.get("todos", data if isinstance(data, list) else [])), 2)

    def test_todo_template_load_unknown_name_returns_error(self):
        self._make_registry({"known": {"name": "known", "tasks": []}})
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg._todo_load_template("unknown", str(self.tmp / "todo.json"))
        self.assertIn("not found", result.lower())

    def test_todo_template_load_empty_name_returns_usage(self):
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg._todo_load_template("", str(self.tmp / "todo.json"))
        self.assertIn("Usage", result)

    def test_todo_template_load_no_registry_returns_error(self):
        if hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"):
            delattr(builtins, "_TODO_TEMPLATE_REGISTRY")
        from core.slash_commands import SlashCommandRegistry
        reg = SlashCommandRegistry()
        result = reg._todo_load_template("anything", str(self.tmp / "todo.json"))
        self.assertIn("not found", result.lower())


# ─────────────────────────────────────────────────────────────
# TestCompressionPromptPatch  —  Step 4 of _setup_workspace
# ─────────────────────────────────────────────────────────────

class TestCompressionPromptPatch(unittest.TestCase):
    """
    Step 4: compressor.STRUCTURED_SUMMARY_PROMPT is replaced with the
    workspace's compression_prompt_text.
    """

    def setUp(self):
        import core.compressor as comp
        importlib.reload(comp)
        self._orig = comp.STRUCTURED_SUMMARY_PROMPT

    def tearDown(self):
        import core.compressor as comp
        comp.STRUCTURED_SUMMARY_PROMPT = self._orig

    def _apply_patch(self, ws_compression_text, original=None):
        """Simulate Step 4 of _setup_workspace."""
        import core.compressor as comp
        from workflow.loader import merge_prompt
        if original:
            comp.STRUCTURED_SUMMARY_PROMPT = original
        if ws_compression_text:
            comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                comp.STRUCTURED_SUMMARY_PROMPT, ws_compression_text, "replace"
            )
        return comp.STRUCTURED_SUMMARY_PROMPT

    def test_compression_prompt_replaced(self):
        result = self._apply_patch("CUSTOM_SUMMARY_PROMPT", original="ORIGINAL")
        self.assertEqual(result, "CUSTOM_SUMMARY_PROMPT")

    def test_none_compression_text_leaves_original(self):
        result = self._apply_patch(None, original="ORIGINAL")
        self.assertEqual(result, "ORIGINAL")

    def test_real_mas-gen_compression_prompt_applied(self):
        from workflow.loader import load_workspace
        ws = load_workspace("mas-gen", Path(_root))
        self.assertIsNotNone(ws.compression_prompt_text)
        result = self._apply_patch(ws.compression_prompt_text)
        self.assertEqual(result, ws.compression_prompt_text)

    def test_compression_prompt_also_stored_in_hook_messages(self):
        """Step 4 also stores the patched prompt in builtins._WORKSPACE_HOOK_MESSAGES."""
        orig_hm = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", None)
        try:
            import core.compressor as comp
            ws_text = "CUSTOM_COMPRESS"
            from workflow.loader import merge_prompt
            comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                comp.STRUCTURED_SUMMARY_PROMPT, ws_text, "replace"
            )
            # Simulate the second assignment in _setup_workspace
            hm = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", {})
            hm["compression_system"] = comp.STRUCTURED_SUMMARY_PROMPT
            builtins._WORKSPACE_HOOK_MESSAGES = hm

            from workflow.loader import get_hook_message
            stored = get_hook_message("compression_system", "DEFAULT")
            self.assertEqual(stored, "CUSTOM_COMPRESS")
        finally:
            if orig_hm is None:
                if hasattr(builtins, "_WORKSPACE_HOOK_MESSAGES"):
                    delattr(builtins, "_WORKSPACE_HOOK_MESSAGES")
            else:
                builtins._WORKSPACE_HOOK_MESSAGES = orig_hm

    def test_all_production_workspaces_have_compression_prompt(self):
        from workflow.loader import load_workspace
        for ws_name in ["mas-gen", "rtl-gen", "tb-gen"]:
            ws = load_workspace(ws_name, Path(_root))
            with self.subTest(workspace=ws_name):
                self.assertIsNotNone(ws.compression_prompt_text,
                                     f"{ws_name} missing compression_prompt.md")


# ─────────────────────────────────────────────────────────────
# TestFullSetupWorkspacePipeline  —  end-to-end simulation
# ─────────────────────────────────────────────────────────────

class TestFullSetupWorkspacePipeline(unittest.TestCase):
    """
    Simulate all 4 prompt-related steps of _setup_workspace() in sequence
    and verify the cumulative state is correct.
    """

    def setUp(self):
        # Save all state that will be mutated
        import core.prompt_builder as pb
        import core.compressor as comp
        self._orig_build = pb.build_system_prompt
        self._orig_compress = comp.STRUCTURED_SUMMARY_PROMPT
        self._orig_hm = getattr(builtins, "_WORKSPACE_HOOK_MESSAGES", None)
        self._orig_todo_reg = getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None)
        self._orig_ws = os.environ.pop("ACTIVE_WORKSPACE", None)
        self._orig_ws_desc = os.environ.pop("ACTIVE_WORKSPACE_DESC", None)
        self.tmp = Path(tempfile.mkdtemp())

    def tearDown(self):
        import core.prompt_builder as pb
        import core.compressor as comp
        pb.build_system_prompt = self._orig_build
        comp.STRUCTURED_SUMMARY_PROMPT = self._orig_compress
        if self._orig_hm is None:
            if hasattr(builtins, "_WORKSPACE_HOOK_MESSAGES"):
                delattr(builtins, "_WORKSPACE_HOOK_MESSAGES")
        else:
            builtins._WORKSPACE_HOOK_MESSAGES = self._orig_hm
        if self._orig_todo_reg is None:
            if hasattr(builtins, "_TODO_TEMPLATE_REGISTRY"):
                delattr(builtins, "_TODO_TEMPLATE_REGISTRY")
        else:
            builtins._TODO_TEMPLATE_REGISTRY = self._orig_todo_reg
        if self._orig_ws:
            os.environ["ACTIVE_WORKSPACE"] = self._orig_ws
        else:
            os.environ.pop("ACTIVE_WORKSPACE", None)
        if self._orig_ws_desc:
            os.environ["ACTIVE_WORKSPACE_DESC"] = self._orig_ws_desc
        else:
            os.environ.pop("ACTIVE_WORKSPACE_DESC", None)
        shutil.rmtree(self.tmp, ignore_errors=True)

    def _simulate_setup(self, ws_name):
        """Run the prompt-patching steps of _setup_workspace for a real workspace."""
        from workflow.loader import (
            load_workspace, merge_prompt, get_todo_template_registry,
        )
        import core.prompt_builder as pb
        import core.compressor as comp
        import types as _types

        ws = load_workspace(ws_name, Path(_root))

        # Step 1: hook messages
        if ws.hook_messages:
            builtins._WORKSPACE_HOOK_MESSAGES = dict(ws.hook_messages)

        # Step 2: system prompt patch
        if ws.system_prompt_text:
            orig_build = pb.build_system_prompt
            ws_text = ws.system_prompt_text
            ws_mode = ws.system_prompt_mode

            def _patched(ctx=None, **kwargs):
                base = orig_build(ctx, **kwargs) if ctx is not None else orig_build(**kwargs)
                if isinstance(base, dict):
                    base = (base.get("static", "") + "\n\n" + base.get("dynamic", "")).strip()
                return merge_prompt(base, ws_text, ws_mode)

            pb.build_system_prompt = _patched

        # Step 3: plan prompt patch
        fake_cfg = _types.SimpleNamespace(PLAN_MODE_PROMPT="ORIGINAL_PLAN")
        if ws.plan_prompt_text:
            fake_cfg.PLAN_MODE_PROMPT = merge_prompt(
                fake_cfg.PLAN_MODE_PROMPT, ws.plan_prompt_text, ws.plan_prompt_mode
            )

        # Step 4: compression prompt patch
        if ws.compression_prompt_text:
            comp.STRUCTURED_SUMMARY_PROMPT = merge_prompt(
                comp.STRUCTURED_SUMMARY_PROMPT, ws.compression_prompt_text, "replace"
            )

        # Step 7: todo templates
        if ws.todo_templates_dir:
            reg = get_todo_template_registry()
            reg.load_from_dir(ws.todo_templates_dir)
            builtins._TODO_TEMPLATE_REGISTRY = reg

        # Step description env
        if ws.description:
            os.environ["ACTIVE_WORKSPACE_DESC"] = ws.description

        return ws, fake_cfg

    def test_mas-gen_system_prompt_is_patched(self):
        ws, _ = self._simulate_setup("mas-gen")
        import core.prompt_builder as pb
        result = pb.build_system_prompt(build_base_fn=lambda **kw: "BASE")
        text = result if isinstance(result, str) else result.get("static", "")
        # mas-gen uses prepend — workspace content comes before BASE
        self.assertIn(ws.system_prompt_text[:30], text)
        self.assertIn("BASE", text)
        self.assertLess(text.index(ws.system_prompt_text[:20]), text.index("BASE"))

    def test_mas-gen_plan_prompt_patched(self):
        ws, fake_cfg = self._simulate_setup("mas-gen")
        # The plan prompt should contain both original and workspace text
        self.assertIn("ORIGINAL_PLAN", fake_cfg.PLAN_MODE_PROMPT)
        self.assertIn(ws.plan_prompt_text[:20], fake_cfg.PLAN_MODE_PROMPT)

    def test_mas-gen_compression_prompt_replaced(self):
        ws, _ = self._simulate_setup("mas-gen")
        import core.compressor as comp
        # mas-gen uses replace mode for compression
        self.assertEqual(comp.STRUCTURED_SUMMARY_PROMPT, ws.compression_prompt_text)

    def test_mas-gen_todo_templates_accessible(self):
        _, _ = self._simulate_setup("mas-gen")
        reg = getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None)
        self.assertIsNotNone(reg)
        tasks = reg.get_tasks("full-project")
        self.assertIsNotNone(tasks)
        self.assertEqual(len(tasks), 10)

    def test_description_stored_in_env(self):
        ws, _ = self._simulate_setup("rtl-gen")
        self.assertEqual(os.environ.get("ACTIVE_WORKSPACE_DESC"), ws.description)

    def test_rtl-gen_full_pipeline_state(self):
        _, _ = self._simulate_setup("rtl-gen")
        import core.prompt_builder as pb
        result = pb.build_system_prompt(build_base_fn=lambda **kw: "BASE")
        text = result if isinstance(result, str) else result.get("static", "")
        # rtl-gen's system_prompt includes RTL coding rules
        self.assertIn("always_ff", text)

    def test_tb-gen_full_pipeline_state(self):
        _, _ = self._simulate_setup("tb-gen")
        reg = getattr(builtins, "_TODO_TEMPLATE_REGISTRY", None)
        self.assertIsNotNone(reg)
        tasks = reg.get_tasks("tb-impl")
        self.assertIsNotNone(tasks)
        # First task should be about reading the DV Plan
        self.assertIn("DV Plan", tasks[0]["content"])


if __name__ == "__main__":
    unittest.main()
