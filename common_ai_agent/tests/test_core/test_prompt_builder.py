"""
TDD tests for core/prompt_builder.py
Written BEFORE the module exists (Red phase).
"""
import sys
import os
import unittest
import types

_tests_dir = os.path.dirname(os.path.abspath(__file__))
_project_root = os.path.dirname(os.path.dirname(_tests_dir))
sys.path.insert(0, os.path.join(_project_root, 'core'))
sys.path.insert(0, os.path.join(_project_root, 'src'))

from prompt_builder import build_system_prompt, _build_system_prompt_str, PromptContext


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
        """When memory_system is provided and returns content, it's in the prompt."""

        class MockMemory:
            def format_all_for_prompt(self):
                return "=== PREFERENCES ===\nkey: value"

        ctx = PromptContext(memory_system=MockMemory())
        result = build_system_prompt(
            cfg=self.cfg,
            context=ctx,
            build_base_fn=self.base_fn,
            messages=[{"role": "user", "content": "hello"}],
        )
        self.assertIn("PREFERENCES", result)


if __name__ == '__main__':
    unittest.main()
