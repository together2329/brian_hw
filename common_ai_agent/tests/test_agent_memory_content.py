"""
Content-level tests for agent.memory DevUnit.

Covers:
  - lib/memory.py       : MemorySystem preferences, project context, rules
  - lib/procedural_memory.py : ProceduralMemory build/retrieve/update/persist
  - lib/curator.py      : KnowledgeCurator deletion / pruning decisions

All file I/O goes to tmp_path; no writes to repo tree or home dir.
LLM / network calls are replaced with fakes.
"""
from __future__ import annotations

import json
import os
import sys
import time
import unittest
import tempfile
from datetime import datetime, timedelta
from pathlib import Path
from typing import Any, Dict, List, Optional
from unittest.mock import patch, MagicMock

# ---------------------------------------------------------------------------
# Path setup — mirrors existing test files
# ---------------------------------------------------------------------------
_HERE = os.path.dirname(os.path.abspath(__file__))
_ROOT = os.path.dirname(_HERE)
sys.path.insert(0, _ROOT)
sys.path.insert(0, os.path.join(_ROOT, "src"))

from lib.memory import MemorySystem
from lib.procedural_memory import ProceduralMemory, Action, Trajectory
import config as _config
from core.graph_lite import GraphLite, Node
from lib.curator import KnowledgeCurator


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _mem(tmp_path: Path, user: Optional[str] = None) -> MemorySystem:
    """Return a MemorySystem scoped to a temp directory."""
    return MemorySystem(memory_dir=str(tmp_path / "memory"), user=user)


def _proc(tmp_path: Path) -> ProceduralMemory:
    """Return a ProceduralMemory scoped to a temp directory."""
    return ProceduralMemory(memory_dir=str(tmp_path / "proc_memory"))


def _graph(tmp_path: Path) -> GraphLite:
    return GraphLite(memory_dir=str(tmp_path / "graph"))


def _action(tool: str = "run_cmd", result: str = "success",
            obs: str = "") -> Action:
    return Action(tool=tool, args="arg1", result=result, observation=obs)


# ---------------------------------------------------------------------------
# MemorySystem — Preferences
# ---------------------------------------------------------------------------

class TestMemoryPreferences(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mem = _mem(Path(self.tmp))

    def test_round_trip_string_preference(self):
        """update_preference then get_preference returns the same value."""
        self.mem.update_preference("coding_style", "snake_case")
        self.assertEqual(self.mem.get_preference("coding_style"), "snake_case")

    def test_round_trip_bool_preference(self):
        self.mem.update_preference("add_comments", False)
        self.assertIs(self.mem.get_preference("add_comments"), False)

    def test_preference_missing_key_returns_default(self):
        result = self.mem.get_preference("nonexistent_key", "fallback")
        self.assertEqual(result, "fallback")

    def test_remove_preference_returns_true_and_removes(self):
        self.mem.update_preference("lang", "en")
        removed = self.mem.remove_preference("lang")
        self.assertTrue(removed)
        self.assertIsNone(self.mem.get_preference("lang"))

    def test_remove_nonexistent_preference_returns_false(self):
        removed = self.mem.remove_preference("does_not_exist")
        self.assertFalse(removed)

    def test_persistence_across_instances(self):
        """Preference written by one instance is visible to a new instance."""
        self.mem.update_preference("theme", "dark")
        mem2 = MemorySystem(memory_dir=str(Path(self.tmp) / "memory"))
        self.assertEqual(mem2.get_preference("theme"), "dark")

    def test_format_preferences_for_prompt_contains_key(self):
        self.mem.update_preference("variable_naming", "camelCase")
        output = self.mem.format_preferences_for_prompt()
        self.assertIn("Variable Naming", output)
        self.assertIn("camelCase", output)

    def test_format_preferences_for_prompt_empty_returns_empty_string(self):
        output = self.mem.format_preferences_for_prompt()
        self.assertEqual(output, "")


# ---------------------------------------------------------------------------
# MemorySystem — Project Context
# ---------------------------------------------------------------------------

class TestMemoryProjectContext(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mem = _mem(Path(self.tmp))

    def test_round_trip_list_context(self):
        modules = ["pcie_rx", "pcie_tx"]
        self.mem.update_project_context("main_modules", modules)
        self.assertEqual(self.mem.get_project_context("main_modules"), modules)

    def test_format_context_for_prompt_lists_as_csv(self):
        self.mem.update_project_context("chips", ["a", "b", "c"])
        output = self.mem.format_project_context_for_prompt()
        self.assertIn("a, b, c", output)

    def test_remove_project_context(self):
        self.mem.update_project_context("foo", "bar")
        self.assertTrue(self.mem.remove_project_context("foo"))
        self.assertIsNone(self.mem.get_project_context("foo"))

    def test_remove_nonexistent_project_context_returns_false(self):
        self.assertFalse(self.mem.remove_project_context("not_here"))


# ---------------------------------------------------------------------------
# MemorySystem — Rules
# ---------------------------------------------------------------------------

class TestMemoryRules(unittest.TestCase):

    def setUp(self):
        self.tmp = tempfile.mkdtemp()
        self.mem = _mem(Path(self.tmp))

    def test_add_global_rule_returns_index(self):
        idx = self.mem.add_rule("always use type hints")
        self.assertEqual(idx, 1)
        idx2 = self.mem.add_rule("never skip docstrings")
        self.assertEqual(idx2, 2)

    def test_list_rules_reflects_additions(self):
        self.mem.add_rule("rule_alpha")
        self.mem.add_rule("rule_beta")
        rules = self.mem.list_rules()
        self.assertEqual(rules["global"], ["rule_alpha", "rule_beta"])

    def test_add_workflow_rule_separate_from_global(self):
        self.mem.add_rule("global_rule")
        self.mem.add_rule("workflow_rule", workflow="my_flow")
        rules = self.mem.list_rules(workflow="my_flow")
        self.assertEqual(rules["global"], ["global_rule"])
        self.assertEqual(rules["workflow"]["rules"], ["workflow_rule"])

    def test_remove_rule_by_index(self):
        self.mem.add_rule("keep_this")
        self.mem.add_rule("remove_this")
        removed = self.mem.remove_rule(2)
        self.assertTrue(removed)
        rules = self.mem.list_rules()
        self.assertEqual(rules["global"], ["keep_this"])

    def test_remove_rule_out_of_range_returns_false(self):
        self.mem.add_rule("only_rule")
        self.assertFalse(self.mem.remove_rule(5))

    def test_clear_rules_removes_all_global(self):
        self.mem.add_rule("r1")
        self.mem.add_rule("r2")
        count = self.mem.clear_rules()
        self.assertEqual(count, 2)
        self.assertEqual(self.mem.list_rules()["global"], [])

    def test_format_rules_for_prompt_contains_rule_text(self):
        self.mem.add_rule("always use snake_case")
        output = self.mem.format_rules_for_prompt()
        self.assertIn("always use snake_case", output)
        self.assertIn("Memory Rules", output)

    def test_format_rules_for_prompt_empty_returns_empty_string(self):
        self.assertEqual(self.mem.format_rules_for_prompt(), "")

    def test_add_empty_rule_raises_value_error(self):
        with self.assertRaises(ValueError):
            self.mem.add_rule("   ")

    def test_corrupt_rules_file_falls_back_to_empty(self):
        rules_file = self.mem.memory_rules_file
        rules_file.write_text("{this is not json}", encoding="utf-8")
        mem2 = MemorySystem(memory_dir=str(Path(self.tmp) / "memory"))
        rules = mem2.list_rules()
        self.assertEqual(rules.get("global", []), [])


# ---------------------------------------------------------------------------
# MemorySystem — normalize_user / user isolation
# ---------------------------------------------------------------------------

class TestMemoryUserNormalization(unittest.TestCase):

    def test_normalize_strips_path_prefix(self):
        norm = MemorySystem._normalize_user("/sessions/alice/run1")
        self.assertEqual(norm, "sessions")

    def test_normalize_strips_model_suffix(self):
        norm = MemorySystem._normalize_user("bob__gpt4")
        self.assertEqual(norm, "bob")

    def test_normalize_anonymous_becomes_empty(self):
        norm = MemorySystem._normalize_user("anonymous")
        self.assertEqual(norm, "")

    def test_user_isolation_separate_files(self):
        tmp = Path(tempfile.mkdtemp())
        mem_alice = _mem(tmp, user="alice")
        mem_bob = _mem(tmp, user="bob")
        mem_alice.update_preference("style", "alice_style")
        mem_bob.update_preference("style", "bob_style")
        self.assertEqual(mem_alice.get_preference("style"), "alice_style")
        self.assertEqual(mem_bob.get_preference("style"), "bob_style")
        # Reload to confirm persistence
        mem_alice2 = MemorySystem(memory_dir=str(tmp / "memory"), user="alice")
        self.assertEqual(mem_alice2.get_preference("style"), "alice_style")


# ---------------------------------------------------------------------------
# MemorySystem — export / import round-trip
# ---------------------------------------------------------------------------

class TestMemoryExportImport(unittest.TestCase):

    def test_export_import_round_trip(self):
        tmp = Path(tempfile.mkdtemp())
        mem = _mem(tmp)
        mem.update_preference("key1", "val1")
        mem.update_project_context("ctx_key", [1, 2, 3])
        mem.add_rule("be concise")

        data = mem.export_to_dict()

        tmp2 = Path(tempfile.mkdtemp())
        mem2 = _mem(tmp2)
        mem2.import_from_dict(data)

        self.assertEqual(mem2.get_preference("key1"), "val1")
        self.assertEqual(mem2.get_project_context("ctx_key"), [1, 2, 3])
        self.assertIn("be concise", mem2.list_rules()["global"])


# ---------------------------------------------------------------------------
# MemorySystem — auto_extract_and_update (LLM stubbed)
# ---------------------------------------------------------------------------

class TestMemoryAutoExtract(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.mem = _mem(self.tmp)

    def _fake_llm_add(self, prompt: str) -> str:
        """Returns a single preference extraction."""
        return '[{"key": "naming", "value": "snake_case", "confidence": 0.9}]'

    def _fake_llm_keep(self, prompt: str) -> str:
        return "KEEP"

    def test_auto_extract_adds_new_preference(self):
        result = self.mem.auto_extract_and_update(
            "please always use snake_case", llm_call_func=self._fake_llm_add
        )
        self.assertEqual(result.get("extracted"), 1)
        actions = result.get("actions", [])
        self.assertTrue(any(a["action"] == "ADD" for a in actions))
        self.assertEqual(self.mem.get_preference("naming"), "snake_case")

    def test_auto_extract_conflict_resolved_to_keep(self):
        self.mem.update_preference("naming", "camelCase")

        def fake_llm(prompt: str) -> str:
            # first call is extraction, second is conflict
            if "[{" in prompt or "[]" in prompt or "Preferences" in prompt:
                return '[{"key": "naming", "value": "snake_case", "confidence": 0.8}]'
            return "KEEP"

        result = self.mem.auto_extract_and_update(
            "use snake_case from now on", llm_call_func=fake_llm
        )
        # Regardless of KEEP/UPDATE, we should have an action recorded
        self.assertIn("actions", result)

    def test_auto_extract_without_explicit_llm_does_not_raise(self):
        # When no llm_call_func is supplied the method either imports one from
        # main (returns {"extracted": N, "actions": [...]}) or returns
        # {"error": ...} if main is not importable. Either way it must not
        # raise and must return a dict.
        result = self.mem.auto_extract_and_update("hello world")
        self.assertIsInstance(result, dict)
        # The result must carry either an "error" key or both expected keys.
        has_error_path = "error" in result
        has_success_path = "extracted" in result and "actions" in result
        self.assertTrue(has_error_path or has_success_path,
                        f"Unexpected result shape: {result}")


# ---------------------------------------------------------------------------
# ProceduralMemory — build / retrieve
# ---------------------------------------------------------------------------

class TestProceduralMemoryBuild(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pm = _proc(self.tmp)

    def test_build_stores_trajectory_and_returns_id(self):
        actions = [_action("compile", "success", "ok")]
        tid = self.pm.build("compile the verilog file", actions, "success", 1)
        self.assertIn(tid, self.pm.trajectories)

    def test_build_success_sets_success_rate_one(self):
        tid = self.pm.build("run python tests", [_action()], "success", 1)
        self.assertEqual(self.pm.trajectories[tid].success_rate, 1.0)

    def test_build_failure_sets_success_rate_zero(self):
        tid = self.pm.build("run python tests", [_action()], "failure", 2)
        self.assertEqual(self.pm.trajectories[tid].success_rate, 0.0)

    def test_classify_task_verilog(self):
        tid = self.pm.build("compile verilog module with iverilog", [], "success", 1)
        self.assertEqual(self.pm.trajectories[tid].task_type, "compile_verilog")

    def test_classify_task_python_test(self):
        tid = self.pm.build("run python test suite", [], "success", 1)
        self.assertEqual(self.pm.trajectories[tid].task_type, "test_python")

    def test_extract_errors_captures_failure_observation(self):
        actions = [Action("cmd", "args", "failure", "error: missing semicolon")]
        tid = self.pm.build("debug task", actions, "failure", 1)
        errors = self.pm.trajectories[tid].errors_encountered
        self.assertTrue(len(errors) > 0, "Expected at least one error extracted")
        self.assertTrue(any("error" in e.lower() for e in errors))

    def test_retrieve_returns_most_similar_first(self):
        self.pm.build("compile verilog design", [_action()], "success", 1)
        self.pm.build("run python unit tests", [_action()], "success", 1)
        results = self.pm.retrieve("compile a verilog file", limit=2)
        self.assertTrue(len(results) >= 1)
        # Top result score should be highest
        scores = [score for score, _ in results]
        self.assertEqual(scores, sorted(scores, reverse=True))

    def test_retrieve_empty_store_returns_empty_list(self):
        results = self.pm.retrieve("any task")
        self.assertEqual(results, [])

    def test_retrieve_respects_limit(self):
        for i in range(5):
            self.pm.build(f"task {i}", [_action()], "success", 1)
        results = self.pm.retrieve("some task", limit=2)
        self.assertLessEqual(len(results), 2)


# ---------------------------------------------------------------------------
# ProceduralMemory — update / increment_usage
# ---------------------------------------------------------------------------

class TestProceduralMemoryUpdate(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.pm = _proc(self.tmp)
        self.tid = self.pm.build("read files", [_action()], "success", 1)

    def test_update_success_rate(self):
        self.pm.update(self.tid, "reflection text", new_success_rate=0.5)
        self.assertEqual(self.pm.trajectories[self.tid].success_rate, 0.5)

    def test_update_nonexistent_returns_false(self):
        result = self.pm.update("fake_id", "reflection")
        self.assertFalse(result)

    def test_increment_usage_increments_by_one(self):
        self.pm.increment_usage(self.tid)
        self.pm.increment_usage(self.tid)
        self.assertEqual(self.pm.trajectories[self.tid].usage_count, 2)

    def test_increment_usage_nonexistent_returns_false(self):
        self.assertFalse(self.pm.increment_usage("no_such_id"))


# ---------------------------------------------------------------------------
# ProceduralMemory — save / load persistence
# ---------------------------------------------------------------------------

class TestProceduralMemoryPersistence(unittest.TestCase):

    def test_save_and_reload_preserves_trajectory(self):
        tmp = Path(tempfile.mkdtemp())
        pm = _proc(tmp)
        tid = pm.build("write code file", [_action("write_file")], "success", 1)
        pm.save()

        pm2 = _proc(tmp)
        self.assertIn(tid, pm2.trajectories)
        self.assertEqual(pm2.trajectories[tid].outcome, "success")

    def test_save_preserves_usage_count(self):
        tmp = Path(tempfile.mkdtemp())
        pm = _proc(tmp)
        tid = pm.build("analyze logs", [_action()], "success", 1)
        pm.increment_usage(tid)
        pm.increment_usage(tid)
        pm.save()

        pm2 = _proc(tmp)
        self.assertEqual(pm2.trajectories[tid].usage_count, 2)

    def test_corrupt_trajectories_file_loads_empty(self):
        tmp = Path(tempfile.mkdtemp())
        proc_dir = tmp / "proc_memory"
        proc_dir.mkdir(parents=True)
        traj_file = proc_dir / "procedural_trajectories.json"
        traj_file.write_text("not json at all", encoding="utf-8")

        pm = _proc(tmp)
        self.assertEqual(len(pm.trajectories), 0)

    def test_get_stats_reflects_stored_trajectories(self):
        tmp = Path(tempfile.mkdtemp())
        pm = _proc(tmp)
        pm.build("compile verilog design", [_action()], "success", 1)
        pm.build("run python tests", [_action()], "failure", 3)
        stats = pm.get_stats()
        self.assertEqual(stats["total_trajectories"], 2)
        self.assertAlmostEqual(stats["avg_success_rate"], 0.5)


# ---------------------------------------------------------------------------
# KnowledgeCurator — harmful node deletion
# ---------------------------------------------------------------------------

class TestCuratorDeleteHarmful(unittest.TestCase):

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.graph = _graph(self.tmp)

    def _add_node(self, node_id: str, helpful: int = 0, harmful: int = 0,
                  days_old: int = 0) -> Node:
        created = (datetime.now() - timedelta(days=days_old)).isoformat()
        node = Node(
            id=node_id, type="Episodic",
            data={"content": f"node {node_id}"},
            helpful_count=helpful, harmful_count=harmful,
            created_at=created,
        )
        self.graph.nodes[node_id] = node
        return node

    def test_harmful_node_is_deleted(self):
        """harmful_count > helpful_count AND >= threshold causes deletion."""
        self._add_node("bad_node", helpful=1, harmful=3)
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["deleted_harmful"], 1)
        self.assertNotIn("bad_node", self.graph.nodes)

    def test_node_below_harmful_threshold_not_deleted(self):
        """harmful_count < CURATOR_HARMFUL_THRESHOLD (2) is not deleted."""
        self._add_node("borderline", helpful=0, harmful=1)
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["deleted_harmful"], 0)
        self.assertIn("borderline", self.graph.nodes)

    def test_healthy_node_not_deleted(self):
        self._add_node("good_node", helpful=5, harmful=1)
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["deleted_harmful"], 0)
        self.assertIn("good_node", self.graph.nodes)

    def test_never_used_old_node_is_pruned(self):
        """Node with usage_count==0 and created 40+ days ago should be pruned."""
        self._add_node("stale_node", days_old=40)
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["pruned_unused"], 1)
        self.assertNotIn("stale_node", self.graph.nodes)

    def test_never_used_new_node_not_pruned(self):
        """Node with usage_count==0 but created recently should NOT be pruned."""
        self._add_node("fresh_node", days_old=5)
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["pruned_unused"], 0)
        self.assertIn("fresh_node", self.graph.nodes)

    def test_get_candidates_for_deletion_identifies_harmful(self):
        self._add_node("target", helpful=0, harmful=4)
        curator = KnowledgeCurator(self.graph)
        candidates = curator.get_candidates_for_deletion()
        reasons = [c["reason"] for c in candidates]
        self.assertIn("harmful", reasons)
        node_ids = [c["node_id"] for c in candidates]
        self.assertIn("target", node_ids)

    def test_empty_graph_curate_returns_zero_counts(self):
        curator = KnowledgeCurator(self.graph)
        stats = curator.curate(save=False)
        self.assertEqual(stats["deleted_harmful"], 0)
        self.assertEqual(stats["pruned_unused"], 0)
        self.assertEqual(stats["total_before"], 0)
        self.assertEqual(stats["total_after"], 0)


# ---------------------------------------------------------------------------
# MemorySystem — all_for_prompt combined output
# ---------------------------------------------------------------------------

class TestMemoryFormatAllForPrompt(unittest.TestCase):

    def test_format_all_includes_all_sections(self):
        tmp = Path(tempfile.mkdtemp())
        mem = _mem(tmp)
        mem.add_rule("never use tabs")
        mem.update_preference("indent", "4spaces")
        mem.update_project_context("framework", "fastapi")

        output = mem.format_all_for_prompt()
        self.assertIn("Memory Rules", output)
        self.assertIn("never use tabs", output)
        self.assertIn("Indent", output)
        self.assertIn("4spaces", output)
        self.assertIn("Framework", output)
        self.assertIn("fastapi", output)

    def test_format_all_empty_returns_empty_string(self):
        tmp = Path(tempfile.mkdtemp())
        mem = _mem(tmp)
        self.assertEqual(mem.format_all_for_prompt(), "")


# ---------------------------------------------------------------------------
# DEFECT A — ProceduralMemory absolute path handling
# ---------------------------------------------------------------------------

class TestProceduralMemoryAbsolutePath(unittest.TestCase):
    """Defect A: ProceduralMemory.__init__ must respect absolute paths."""

    def test_absolute_memory_dir_used_as_is(self):
        """An absolute tmp dir must be used directly, not prepended with home."""
        tmp = Path(tempfile.mkdtemp())
        abs_dir = tmp / "proc_abs"
        pm = ProceduralMemory(memory_dir=str(abs_dir))
        # The resolved memory_dir must equal the absolute path we passed in.
        self.assertEqual(pm.memory_dir.resolve(), abs_dir.resolve())
        # And the trajectories file must exist inside that absolute dir.
        self.assertTrue(pm.trajectories_file.parent.resolve() == abs_dir.resolve())

    def test_tilde_path_is_expanded_not_literal(self):
        """A '~/.memory_xyz' arg must expand to home/.memory_xyz, not home/~/.memory_xyz."""
        fake_home = Path(tempfile.mkdtemp())
        rel_tilde = "~/.memory_test_tilde_xyz"
        with patch("lib.procedural_memory.Path.home", return_value=fake_home):
            pm = ProceduralMemory(memory_dir=rel_tilde)
        # With correct expanduser() the tilde resolves to fake_home/.memory_test_tilde_xyz.
        # With the buggy Path.home() / rel_tilde it would be fake_home/~/.memory_test_tilde_xyz.
        wrong = fake_home / rel_tilde
        self.assertNotEqual(
            pm.memory_dir.resolve(), wrong.resolve(),
            "memory_dir must not contain a literal '~' component"
        )
        expected = Path(rel_tilde).expanduser()
        self.assertEqual(pm.memory_dir.resolve(), expected.resolve())

    def test_relative_path_still_goes_under_home(self):
        """Relative paths must continue to resolve under Path.home()."""
        rel = ".memory_test_rel_xyz"
        fake_home = Path(tempfile.mkdtemp())
        with patch("lib.procedural_memory.Path.home", return_value=fake_home):
            pm = ProceduralMemory(memory_dir=rel)
        expected = fake_home / rel
        self.assertEqual(pm.memory_dir.resolve(), expected.resolve())


# ---------------------------------------------------------------------------
# DEFECT B — MemorySystem.auto_extract_and_update LLM error marker
# ---------------------------------------------------------------------------

class TestAutoExtractLLMErrorMarker(unittest.TestCase):
    """Defect B: LLM failure must carry llm_error; valid empty list must not."""

    def setUp(self):
        self.tmp = Path(tempfile.mkdtemp())
        self.mem = _mem(self.tmp)

    def test_llm_raises_produces_llm_error_key(self):
        """When the LLM callable raises, result must have 'llm_error' key."""
        def raising_llm(prompt: str) -> str:
            raise RuntimeError("connection refused")

        result = self.mem.auto_extract_and_update(
            "I like Python", llm_call_func=raising_llm
        )
        self.assertIn("llm_error", result,
                      "Expected 'llm_error' key when LLM raises, got: " + str(result))
        self.assertIsInstance(result["llm_error"], str)
        self.assertGreater(len(result["llm_error"]), 0)

    def test_llm_returns_empty_list_no_llm_error_key(self):
        """When the LLM returns a valid empty list, result must NOT have 'llm_error'."""
        def empty_llm(prompt: str) -> str:
            return "[]"

        result = self.mem.auto_extract_and_update(
            "Hello world", llm_call_func=empty_llm
        )
        self.assertNotIn("llm_error", result,
                         "Unexpected 'llm_error' on successful-but-empty LLM response")
        self.assertEqual(result.get("extracted"), 0)
        self.assertEqual(result.get("actions"), [])


if __name__ == "__main__":
    unittest.main()
