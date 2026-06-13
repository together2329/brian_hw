"""
TDD tests for core/prompt_builder.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import json
import tempfile
import unittest
import types
from pathlib import Path

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'src'))

from prompt_builder import (
    MEMORY_OVERRIDE_START,
    PROJECT_WIKI_CONTEXT_START,
    PromptContext,
    apply_memory_override,
    build_system_prompt,
    prompt_injection_enabled,
    _build_system_prompt_str,
)


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_cfg(**overrides):
    """Minimal config namespace for testing."""
    cfg = types.SimpleNamespace(
        PLAN_MODE_BLOCKED_TOOLS=set(),
        DEBUG_MODE=False,
        CACHE_OPTIMIZATION_MODE="legacy",
        ENABLE_SKILL_SYSTEM=False,
        ENABLE_SMART_RAG=False,
        PROCEDURAL_INJECT_GUIDANCE=False,
        GRAPH_SEARCH_LIMIT=5,
        GRAPH_SIMILARITY_THRESHOLD=0.5,
    )
    for k, v in overrides.items():
        setattr(cfg, k, v)
    return cfg


def _make_base_prompt_fn(text="BASE PROMPT"):
    """Minimal build_base_system_prompt replacement."""
    def fn(allowed_tools=None, plan_mode=False, todo_active=False):
        return text
    return fn


# ---------------------------------------------------------------------------
# PromptContext dataclass
# ---------------------------------------------------------------------------

class TestPromptContext(unittest.TestCase):

    def test_all_defaults_none(self):
        ctx = PromptContext()
        self.assertIsNone(ctx.memory_system)
        self.assertIsNone(ctx.graph_lite)
        self.assertIsNone(ctx.procedural_memory)
        self.assertIsNone(ctx.hybrid_rag)
        self.assertIsNone(ctx.todo_tracker)

    def test_fields_settable(self):
        ctx = PromptContext(memory_system="ms", graph_lite="gl")
        self.assertEqual(ctx.memory_system, "ms")
        self.assertEqual(ctx.graph_lite, "gl")


# ---------------------------------------------------------------------------
# build_system_prompt — basic (no optional features)
# ---------------------------------------------------------------------------

class TestBuildSystemPromptBasic(unittest.TestCase):

    def setUp(self):
        self.cfg = _make_cfg()
        self.ctx = PromptContext()
        self.base_fn = _make_base_prompt_fn("TEST BASE PROMPT")

    def test_returns_string_in_legacy_mode(self):
        result = build_system_prompt(
            cfg=self.cfg,
            context=self.ctx,
            build_base_fn=self.base_fn,
        )
        self.assertIsInstance(result, str)

    def test_returns_dict_in_optimized_mode(self):
        cfg = _make_cfg(CACHE_OPTIMIZATION_MODE="optimized")
        result = build_system_prompt(
            cfg=cfg,
            context=self.ctx,
            build_base_fn=self.base_fn,
        )
        self.assertIsInstance(result, dict)
        self.assertIn("static", result)
        self.assertIn("dynamic", result)

    def test_base_prompt_included(self):
        result = build_system_prompt(
            cfg=self.cfg,
            context=self.ctx,
            build_base_fn=self.base_fn,
        )
        self.assertIn("TEST BASE PROMPT", result)

    def test_plan_mode_filter_applied(self):
        """Plan mode should filter PLAN_MODE_BLOCKED_TOOLS from allowed_tools."""
        cfg = _make_cfg(PLAN_MODE_BLOCKED_TOOLS={"write_file", "run_command"})
        captured = {}

        def capturing_base_fn(allowed_tools=None, plan_mode=False, todo_active=False):
            captured["allowed_tools"] = set(allowed_tools) if allowed_tools else set()
            return "BASE"

        build_system_prompt(
            allowed_tools={"read_file", "write_file", "run_command"},
            agent_mode="plan",
            cfg=cfg,
            context=self.ctx,
            build_base_fn=capturing_base_fn,
        )
        self.assertNotIn("write_file", captured.get("allowed_tools", set()))
        self.assertNotIn("run_command", captured.get("allowed_tools", set()))
        self.assertIn("read_file", captured.get("allowed_tools", set()))

    def test_no_context_returns_base_only(self):
        result = build_system_prompt(
            cfg=self.cfg,
            context=self.ctx,
            build_base_fn=_make_base_prompt_fn("ONLY BASE"),
        )
        self.assertEqual(result.strip(), "ONLY BASE")


# ---------------------------------------------------------------------------
# _build_system_prompt_str wrapper
# ---------------------------------------------------------------------------

class TestBuildSystemPromptStr(unittest.TestCase):

    def setUp(self):
        self.cfg = _make_cfg()
        self.ctx = PromptContext()
        self.base_fn = _make_base_prompt_fn("STRING BASE")

    def test_always_returns_string_from_legacy(self):
        result = _build_system_prompt_str(
            cfg=self.cfg,
            context=self.ctx,
            build_base_fn=self.base_fn,
        )
        self.assertIsInstance(result, str)

    def test_always_returns_string_from_optimized(self):
        cfg = _make_cfg(CACHE_OPTIMIZATION_MODE="optimized")
        result = _build_system_prompt_str(
            cfg=cfg,
            context=self.ctx,
            build_base_fn=self.base_fn,
        )
        self.assertIsInstance(result, str)
        self.assertIn("STRING BASE", result)

    def test_memory_context_injected_when_present(self):
        """When memory_system is provided, memory follows the base system text."""

        class MockMemory:
            def format_all_for_prompt(self, workflow=None):
                return "=== PREFERENCES ===\nkey: value"

        ctx = PromptContext(memory_system=MockMemory())
        result = build_system_prompt(
            cfg=_make_cfg(ENABLE_PROMPT_INJECTION=True),
            context=ctx,
            build_base_fn=self.base_fn,
            messages=[{"role": "user", "content": "hello"}],
        )
        self.assertIn("PREFERENCES", result)
        self.assertTrue(result.startswith("STRING BASE"))
        self.assertLess(result.index("STRING BASE"), result.index(MEMORY_OVERRIDE_START))

    def test_memory_override_sits_after_workspace_prompt_before_rules(self):
        """Re-applying memory after workspace merge keeps system text first."""

        class MockMemory:
            def format_all_for_prompt(self, workflow=None):
                return f"Workflow {workflow}: memory wins"

        prompt = (
            "WORKSPACE SYSTEM\n\n"
            "=== MEMORY OVERRIDES (HIGHEST PRIORITY) ===\n"
            "stale\n"
            "=== END MEMORY OVERRIDES ===\n\n"
            "RULES:\n"
            "- base"
        )
        result = apply_memory_override(prompt, MockMemory(), workflow="rtl-gen")

        self.assertTrue(result.startswith("WORKSPACE SYSTEM"))
        self.assertIn("Workflow rtl-gen: memory wins", result)
        self.assertNotIn("stale", result)
        self.assertLess(result.index("WORKSPACE SYSTEM"), result.index(MEMORY_OVERRIDE_START))
        self.assertLess(result.index(MEMORY_OVERRIDE_START), result.index("RULES:"))

    def test_memory_override_sits_before_workflow_absolute_rules(self):
        """Workflow system prompt stays first; memory lands before rule headings."""

        class MockMemory:
            def format_all_for_prompt(self, workflow=None):
                return "Memory Rules:\nGlobal:\n1. Keep answers compact"

        prompt = "# SSOT Generator\n\nYou write SSOT YAML.\n\n## ABSOLUTE RULES\n- Do not write RTL"
        result = apply_memory_override(prompt, MockMemory(), workflow="ssot-gen")

        self.assertTrue(result.startswith("# SSOT Generator"))
        self.assertLess(result.index("You write SSOT YAML."), result.index(MEMORY_OVERRIDE_START))
        self.assertLess(result.index(MEMORY_OVERRIDE_START), result.index("## ABSOLUTE RULES"))


class TestProjectWikiContext(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._env = {
            key: os.environ.get(key)
            for key in (
                "COMMON_AI_AGENT_HOME",
                "ACTIVE_WORKSPACE",
                "ATLAS_ACTIVE_SESSION",
                "ATLAS_ACTIVE_IP",
                "ATLAS_IP_ROOT",
                "ATLAS_PROJECT_WIKI_GRAPH",
                "ATLAS_PROJECT_WIKI_ROOT",
            )
        }

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_stage_tagged_project_wiki_pages_are_injected(self):
        root = Path(self.tmp.name)
        wiki = root / "doc" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "_graph.json").write_text(
            json.dumps(
                {
                    "schema_version": "wiki_graph.v1",
                    "node_count": 2,
                    "edge_count": 0,
                    "nodes": [
                        {
                            "id": "rtl-ownership",
                            "title": "RTL Ownership",
                            "type": "rule",
                            "tags": ["rtl-ownership", "rtl-gen"],
                            "path": "doc/wiki/rtl-ownership.md",
                            "summary": "RTL ownership lesson for repair routing.",
                        },
                        {
                            "id": "ssot-flags",
                            "title": "SSOT Flags",
                            "type": "reference",
                            "tags": ["ssot-flags"],
                            "path": "doc/wiki/ssot-flags.md",
                            "summary": "SSOT flag reference.",
                        },
                    ],
                }
            ),
            encoding="utf-8",
        )
        os.environ["COMMON_AI_AGENT_HOME"] = str(root)
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        os.environ["ATLAS_ACTIVE_IP"] = "demo_ip"
        cfg = _make_cfg(ENABLE_PROMPT_INJECTION=True, PROJECT_WIKI_CONTEXT_LIMIT=1)

        result = build_system_prompt(
            messages=[{"role": "user", "content": "fix rtl ownership"}],
            cfg=cfg,
            context=PromptContext(),
            build_base_fn=_make_base_prompt_fn("BASE"),
        )

        self.assertIn(PROJECT_WIKI_CONTEXT_START, result)
        self.assertIn("[[rtl-ownership]]", result)
        self.assertIn("doc/wiki/rtl-ownership.md", result)
        self.assertIn("RTL ownership lesson", result)
        self.assertNotIn("[[ssot-flags]]", result)


class TestPromptInjectionToggle(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.TemporaryDirectory()
        self._env = {
            key: os.environ.get(key)
            for key in (
                "ATLAS_PROMPT_INJECTION",
                "ENABLE_PROMPT_INJECTION",
                "COMMON_AI_AGENT_HOME",
                "ACTIVE_WORKSPACE",
                "ATLAS_ACTIVE_IP",
            )
        }

    def tearDown(self):
        for key, value in self._env.items():
            if value is None:
                os.environ.pop(key, None)
            else:
                os.environ[key] = value
        self.tmp.cleanup()

    def test_disabled_prompt_injection_keeps_base_but_suppresses_memory_and_wiki(self):
        class MockMemory:
            def format_all_for_prompt(self, workflow=None):
                return "Stored rule should not appear"

        root = Path(self.tmp.name)
        wiki = root / "doc" / "wiki"
        wiki.mkdir(parents=True)
        (wiki / "_graph.json").write_text(
            json.dumps(
                {
                    "schema_version": "wiki_graph.v1",
                    "nodes": [
                        {
                            "id": "rtl-ownership",
                            "title": "RTL Ownership",
                            "tags": ["rtl-gen"],
                            "path": "doc/wiki/rtl-ownership.md",
                            "summary": "Wiki rule should not appear.",
                        }
                    ],
                }
            ),
            encoding="utf-8",
        )
        os.environ["COMMON_AI_AGENT_HOME"] = str(root)
        os.environ["ACTIVE_WORKSPACE"] = "rtl-gen"
        os.environ["ATLAS_ACTIVE_IP"] = "demo_ip"
        cfg = _make_cfg(ENABLE_PROMPT_INJECTION=False, PROJECT_WIKI_CONTEXT_LIMIT=1)

        result = build_system_prompt(
            messages=[{"role": "user", "content": "fix rtl ownership"}],
            cfg=cfg,
            context=PromptContext(memory_system=MockMemory()),
            build_base_fn=_make_base_prompt_fn("BASE\n\nRULES:\n- base"),
        )

        self.assertEqual(result, "BASE\n\nRULES:\n- base")
        self.assertNotIn(MEMORY_OVERRIDE_START, result)
        self.assertNotIn(PROJECT_WIKI_CONTEXT_START, result)
        self.assertNotIn("Stored rule should not appear", result)
        self.assertNotIn("Wiki rule should not appear", result)

    def test_prompt_injection_enabled_accepts_env_alias(self):
        os.environ["ENABLE_PROMPT_INJECTION"] = "false"
        os.environ.pop("ATLAS_PROMPT_INJECTION", None)
        self.assertFalse(prompt_injection_enabled())

        os.environ["ATLAS_PROMPT_INJECTION"] = "on"
        self.assertTrue(prompt_injection_enabled())

    def test_prompt_injection_default_is_disabled(self):
        os.environ.pop("ATLAS_PROMPT_INJECTION", None)
        os.environ.pop("ENABLE_PROMPT_INJECTION", None)
        self.assertFalse(prompt_injection_enabled())


if __name__ == '__main__':
    unittest.main()
