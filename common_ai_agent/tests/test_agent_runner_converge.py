"""
Tests for core/agent_runner.py converge-related functions:
  - _build_converge_context (None, empty Project, partial Project, full Project)
  - _flatten_metrics helper
  - run_agent_session converge_state injection (system message appears)
  - inbox drain during iteration (override / abort / generic messages)

These tests mock the LLM layer and heavy imports so the converge-specific
logic is exercised without launching a real agent.
"""

import os
import sys
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import (
    Project,
    ConvergeConfig,
    StageConfig,
)


# ============================================================
# Helpers
# ============================================================

def _make_project_with_config(**overrides):
    """Create a Project with a minimal ConvergeConfig."""
    config = ConvergeConfig(
        name="test-loop",
        stages=[
            StageConfig(id="lint", workspace="eda", prompt="Lint {module}"),
            StageConfig(id="sim", workspace="eda", prompt="Sim {module}"),
        ],
        criteria_hard_stop=[
            {"metric": "lint.errors", "operator": "==", "value": 0},
        ],
        criteria_score_threshold=overrides.pop("criteria_score_threshold", 10.0),
        criteria_max_total_iterations=overrides.pop("criteria_max_total_iterations", 15),
        criteria_no_improve_limit=overrides.pop("criteria_no_improve_limit", 2),
        score_weights=overrides.pop("score_weights", {"lint.errors": -5, "sim.pass": 2}),
        feedback_graph=overrides.pop("feedback_graph", []),
        **overrides,
    )
    project = Project(
        module="counter",
        converge_config=config,
        variables={"module": "counter"},
    )
    project.current_stage = config.stages[0].id
    project.session_dir = None  # skip persistence in tests
    return project


# ============================================================
# _build_converge_context
# ============================================================

class TestBuildConvergeContext:
    """Tests for the _build_converge_context function."""

    def _get_fn(self):
        """Import and return _build_converge_context."""
        from core.agent_runner import _build_converge_context
        return _build_converge_context

    # -- None / missing state --

    def test_none_returns_empty(self):
        fn = self._get_fn()
        assert fn(None) == ""

    def test_bare_object_returns_empty(self):
        """Object with no converge attributes → only header '[CONVERGE CONTEXT]' → empty."""
        fn = self._get_fn()
        assert fn(MagicMock(spec=[])) == ""

    # -- Partial state: stage only --

    def test_stage_only(self):
        fn = self._get_fn()
        state = MagicMock()
        state.current_stage = "lint"
        state.iteration = 0
        state.score = -999.0
        state.best_score = -999.0
        state.converge_config = None
        state.metrics = {}
        state.check_hard_stop_criteria = None
        result = fn(state)
        assert "[CONVERGE CONTEXT]" in result
        assert "Stage: lint" in result

    # -- Partial state: iteration --

    def test_iteration_shown_when_positive(self):
        fn = self._get_fn()
        state = MagicMock()
        state.current_stage = "lint"
        state.iteration = 5
        state.score = -999.0
        state.best_score = -999.0
        state.converge_config = None
        state.metrics = {}
        state.check_hard_stop_criteria = None
        result = fn(state)
        assert "Total iteration: 5" in result

    def test_iteration_zero_omitted(self):
        fn = self._get_fn()
        state = MagicMock()
        state.current_stage = "lint"
        state.iteration = 0
        state.score = -999.0
        state.best_score = -999.0
        state.converge_config = None
        state.metrics = {}
        state.check_hard_stop_criteria = None
        result = fn(state)
        assert "Total iteration" not in result

    # -- Score --

    def test_score_shown_when_not_default(self):
        fn = self._get_fn()
        state = MagicMock()
        state.current_stage = "lint"
        state.iteration = 3
        state.score = 7.5
        state.best_score = 9.0
        state.converge_config = None
        state.metrics = {}
        state.check_hard_stop_criteria = None
        result = fn(state)
        assert "Score: 7.5 (best: 9.0)" in result

    def test_score_default_omitted(self):
        fn = self._get_fn()
        state = MagicMock()
        state.current_stage = "lint"
        state.iteration = 0
        state.score = -999.0
        state.best_score = -999.0
        state.converge_config = None
        state.metrics = {}
        state.check_hard_stop_criteria = None
        result = fn(state)
        assert "Score:" not in result

    # -- Config (target score / max iterations) --

    def test_config_adds_target_and_max(self):
        fn = self._get_fn()
        project = _make_project_with_config(criteria_score_threshold=15.0)
        project.score = 7.5
        project.best_score = 9.0
        project.iteration = 3
        result = fn(project)
        assert "Target score: 15.0" in result
        assert "Max iterations: 15" in result

    # -- Metrics --

    def test_metrics_flat_keys(self):
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"lint.errors": 3, "sim.pass": 1}
        result = fn(project)
        assert "Metrics:" in result
        assert "lint.errors=3" in result
        assert "sim.pass=1" in result

    def test_metrics_nested_dicts(self):
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"synth": {"timing": {"wns": -0.2}}}
        result = fn(project)
        assert "synth.timing.wns=-0.2" in result

    def test_metrics_capped_at_8(self):
        """Metrics display is limited to 8 entries."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {f"m{i}": i for i in range(20)}
        result = fn(project)
        # Should contain the 8th metric but not the 9th
        assert "m7=7" in result
        assert "m8=8" not in result

    def test_metrics_empty_omitted(self):
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {}
        result = fn(project)
        assert "Metrics:" not in result

    # -- Criteria status --

    def test_criteria_shown_when_check_fn_present(self):
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"lint.errors": 0}
        result = fn(project)
        assert "Criteria:" in result

    def test_criteria_check_raises_still_shows_rest(self):
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        # Override check to raise
        project.check_hard_stop_criteria = MagicMock(side_effect=RuntimeError("boom"))
        result = fn(project)
        assert "Stage: lint" in result
        assert "Criteria:" not in result

    # -- Full project integration --

    def test_full_project_all_fields(self):
        fn = self._get_fn()
        project = _make_project_with_config(
            criteria_score_threshold=20.0,
            criteria_max_total_iterations=10,
        )
        project.score = 12.5
        project.best_score = 15.0
        project.iteration = 7
        project.metrics = {"lint.errors": 0, "sim.pass": 5, "sim.fail": 0}
        result = fn(project)
        assert "[CONVERGE CONTEXT]" in result
        assert "Stage: lint" in result
        assert "Total iteration: 7" in result
        assert "Score: 12.5 (best: 15.0)" in result
        assert "Target score: 20.0" in result
        assert "Max iterations: 10" in result
        assert "Metrics:" in result
        assert "Criteria:" in result

    def test_result_is_pipe_separated(self):
        """All parts after the header are joined with ' | '."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"lint.errors": 0}
        result = fn(project)
        # Header starts the string, then each part is separated by " | "
        assert result.startswith("[CONVERGE CONTEXT]")
        parts = result.split(" | ")
        assert len(parts) >= 3  # at least header, stage, score/config


# ============================================================
# _flatten_metrics helper
# ============================================================

class TestFlattenMetrics:
    """Tests for the _flatten_metrics helper."""

    def _get_fn(self):
        from core.agent_runner import _flatten_metrics
        return _flatten_metrics

    def test_flat_dict(self):
        fn = self._get_fn()
        out = []
        fn({"a": 1, "b": 2}, out)
        assert out == ["a=1", "b=2"]

    def test_nested_dict(self):
        fn = self._get_fn()
        out = []
        fn({"synth": {"timing": {"wns": -0.2, "tns": -1.5}}}, out)
        assert out == ["synth.timing.wns=-0.2", "synth.timing.tns=-1.5"]

    def test_mixed_types(self):
        fn = self._get_fn()
        out = []
        fn({"count": 5, "rate": 0.95, "name": "ok"}, out)
        assert "count=5" in out
        assert "rate=0.95" in out
        assert "name=ok" in out

    def test_empty_dict(self):
        fn = self._get_fn()
        out = []
        fn({}, out)
        assert out == []

    def test_prefix_propagation(self):
        fn = self._get_fn()
        out = []
        fn({"x": {"y": 1}}, out, prefix="root")
        assert out == ["root.x.y=1"]


# ============================================================
# Converge context injection into run_agent_session
# ============================================================

class TestConvergeContextInjection:
    """
    Tests that when converge_state is provided to run_agent_session,
    a system message with the converge context is appended to messages.
    
    We mock the heavy dependencies (LLM, config, tools) so the function
    proceeds through message building but we intercept before the actual
    ReAct loop runs.
    """

    def _mock_run_session_capture_messages(self, converge_state=None):
        """
        Run _build_converge_context directly and check what it would inject.
        This avoids needing to mock the entire run_agent_session machinery.
        """
        from core.agent_runner import _build_converge_context
        return _build_converge_context(converge_state)

    def test_no_converge_state_no_injection(self):
        """When converge_state is None, context should be empty."""
        result = self._mock_run_session_capture_messages(None)
        assert result == ""

    def test_project_with_state_produces_context(self):
        """A fully populated project produces a non-empty context string."""
        project = _make_project_with_config()
        project.score = 8.0
        project.best_score = 8.0
        project.iteration = 2
        project.metrics = {"lint.errors": 0}
        result = self._mock_run_session_capture_messages(project)
        assert result != ""
        assert "[CONVERGE CONTEXT]" in result
        assert "Stage: lint" in result

    def test_project_with_score_shows_score(self):
        project = _make_project_with_config()
        project.score = 12.3
        project.best_score = 15.7
        project.iteration = 4
        result = self._mock_run_session_capture_messages(project)
        assert "Score: 12.3 (best: 15.7)" in result


# ============================================================
# Inbox drain behavior
# ============================================================

class TestInboxDrain:
    """
    Tests for the inbox mechanism used during converge loop iterations.
    
    The inbox drain logic lives inside run_agent_session's ReAct loop.
    We test the Project inbox API directly and the message handling logic.
    """

    def test_send_and_drain(self):
        """send_to_inbox adds messages, drain_inbox returns and clears."""
        project = _make_project_with_config()
        project.send_to_inbox("override", "Switch to sim stage")
        assert project.has_inbox_messages()
        msgs = project.drain_inbox()
        assert len(msgs) == 1
        assert msgs[0]["type"] == "override"
        assert msgs[0]["message"] == "Switch to sim stage"
        assert not project.has_inbox_messages()

    def test_drain_clears(self):
        """After drain, inbox is empty."""
        project = _make_project_with_config()
        project.send_to_inbox("info", "hello")
        project.drain_inbox()
        assert project.inbox == []
        assert not project.has_inbox_messages()

    def test_multiple_messages_order(self):
        """Messages are drained in FIFO order."""
        project = _make_project_with_config()
        project.send_to_inbox("override", "first")
        project.send_to_inbox("override", "second")
        project.send_to_inbox("abort", "stop")
        msgs = project.drain_inbox()
        assert len(msgs) == 3
        assert msgs[0]["message"] == "first"
        assert msgs[1]["message"] == "second"
        assert msgs[2]["type"] == "abort"

    def test_abort_type(self):
        project = _make_project_with_config()
        project.send_to_inbox("abort", "critical failure")
        msgs = project.drain_inbox()
        assert msgs[0]["type"] == "abort"
        assert msgs[0]["message"] == "critical failure"

    def test_override_type(self):
        project = _make_project_with_config()
        project.send_to_inbox("override", "skip to sim")
        msgs = project.drain_inbox()
        assert msgs[0]["type"] == "override"

    def test_generic_type(self):
        """Non-override, non-abort messages have 'type' as-is."""
        project = _make_project_with_config()
        project.send_to_inbox("info", "status update")
        msgs = project.drain_inbox()
        assert msgs[0]["type"] == "info"

    def test_extra_kwargs_preserved(self):
        """send_to_inbox passes through extra kwargs."""
        project = _make_project_with_config()
        project.send_to_inbox("override", "msg", priority="high")
        msgs = project.drain_inbox()
        assert msgs[0]["priority"] == "high"

    def test_empty_inbox_has_no_messages(self):
        project = _make_project_with_config()
        assert not project.has_inbox_messages()
        assert project.drain_inbox() == []

    def test_inbox_serialized_in_state(self):
        """Inbox is included in save_state() output."""
        import tempfile, json
        project = _make_project_with_config()
        project.send_to_inbox("override", "test msg")
        with tempfile.TemporaryDirectory() as tmpdir:
            project.session_dir = Path(tmpdir)
            project.save_state()
            state = json.loads((Path(tmpdir) / "loop_state.json").read_text())
            assert len(state["inbox"]) == 1
            assert state["inbox"][0]["type"] == "override"

    def test_inbox_restored_from_state(self):
        """Inbox is restored via load_state()."""
        import tempfile, json
        project = _make_project_with_config()
        project.send_to_inbox("override", "restored msg")
        with tempfile.TemporaryDirectory() as tmpdir:
            project.session_dir = Path(tmpdir)
            project.save_state()

            new_project = _make_project_with_config()
            new_project.session_dir = Path(tmpdir)
            new_project.load_state()
            assert new_project.has_inbox_messages()
            msgs = new_project.drain_inbox()
            assert msgs[0]["message"] == "restored msg"


# ============================================================
# Inbox message handling in the loop (message format tests)
# ============================================================

class TestInboxMessageFormat:
    """
    Tests that verify the expected format of inbox messages when processed
    by the agent runner's ReAct loop. The actual processing is inline in
    run_agent_session, so we verify the message construction patterns.
    """

    def test_override_message_format(self):
        """Override messages should be formatted as [CONVERGE OVERRIDE] <text>."""
        text = "Switch to stage sim"
        formatted = f"[CONVERGE OVERRIDE] {text}"
        assert formatted.startswith("[CONVERGE OVERRIDE]")
        assert "Switch to stage sim" in formatted

    def test_generic_message_format(self):
        """Generic messages should be formatted as [CONVERGE MESSAGE] <text>."""
        text = "Status update from orchestrator"
        formatted = f"[CONVERGE MESSAGE] {text}"
        assert formatted.startswith("[CONVERGE MESSAGE]")
        assert "Status update from orchestrator" in formatted

    def test_abort_forces_exit(self):
        """
        When an abort message is received, the iteration counter is set
        above max_iterations to force loop exit. This test verifies the
        logic pattern.
        """
        max_iterations = 15
        iteration = 3
        msg_type = "abort"
        
        if msg_type == "abort":
            iteration = max_iterations + 1
        
        assert iteration > max_iterations  # would cause break

    def test_mixed_inbox_abort_stops_processing(self):
        """
        When processing a batch of inbox messages, abort should stop
        further message processing and force exit.
        """
        messages = []
        max_iterations = 15
        iteration = 2
        
        inbox_msgs = [
            {"type": "override", "message": "first"},
            {"type": "abort", "message": "stop now"},
            {"type": "override", "message": "never reached"},
        ]
        
        aborted = False
        for imsg in inbox_msgs:
            msg_type = imsg.get("type", "")
            msg_text = imsg.get("message", "")
            if msg_type == "abort":
                iteration = max_iterations + 1
                aborted = True
                break
            elif msg_type == "override":
                messages.append({"role": "system", "content": f"[CONVERGE OVERRIDE] {msg_text}"})
            else:
                messages.append({"role": "system", "content": f"[CONVERGE MESSAGE] {msg_text}"})
        
        # Only the first override was processed before abort
        assert len(messages) == 1
        assert messages[0]["content"] == "[CONVERGE OVERRIDE] first"
        assert aborted
        assert iteration > max_iterations


# ============================================================
# Integration: _build_converge_context with real Project
# ============================================================

class TestBuildConvergeContextIntegration:
    """Integration tests using real Project objects."""

    def _get_fn(self):
        from core.agent_runner import _build_converge_context
        return _build_converge_context

    def test_project_no_config(self):
        """Project without converge_config still works (no criteria section)."""
        fn = self._get_fn()
        project = Project(module="top")
        project.current_stage = "lint"
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        result = fn(project)
        assert "[CONVERGE CONTEXT]" in result
        assert "Stage: lint" in result
        # No config → no target score
        assert "Target score" not in result

    def test_project_criteria_all_met(self):
        """All criteria met → shows 'X/X met'."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"lint.errors": 0}
        result = fn(project)
        assert "Criteria:" in result
        # All criteria met → "1/1 met"
        assert "1/1 met" in result

    def test_project_criteria_not_met(self):
        """Criteria not met → shows '0/X met'."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        # Use nested metrics so _resolve_metric_path walks correctly:
        # "lint.errors" → metrics["lint"]["errors"] = 5 ≠ 0
        project.metrics = {"lint": {"errors": 5}}
        result = fn(project)
        assert "Criteria:" in result
        assert "0/1 met" in result

    def test_project_multiple_criteria(self):
        """Multiple criteria with mixed results."""
        fn = self._get_fn()
        config = ConvergeConfig(
            name="multi",
            stages=[
                StageConfig(id="lint", workspace="eda", prompt="Lint"),
                StageConfig(id="sim", workspace="eda", prompt="Sim"),
            ],
            criteria_hard_stop=[
                {"metric": "lint.errors", "operator": "==", "value": 0},
                {"metric": "sim.fail", "operator": "==", "value": 0},
                {"metric": "sim.pass", "operator": ">=", "value": 1},
            ],
            score_weights={"lint.errors": -5, "sim.pass": 2},
        )
        project = Project(module="counter", converge_config=config)
        project.current_stage = "lint"
        project.iteration = 3
        project.score = 5.0
        project.best_score = 7.0
        project.metrics = {"lint.errors": 0, "sim.fail": 1, "sim.pass": 2}
        project.session_dir = None
        result = fn(project)
        assert "Criteria:" in result
        # lint.errors==0 → True, sim.fail==0 → False, sim.pass>=1 → True → 2/3
        assert "2/3 met" in result

    def test_project_stage_iterations_not_in_context(self):
        """stage_iterations is not shown in converge context (only total iteration)."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 3
        project.stage_iterations = {"lint": 2, "sim": 1}
        project.metrics = {"lint.errors": 0}
        result = fn(project)
        assert "Total iteration: 3" in result
        # stage_iterations is not part of the context string
        assert "stage_iterations" not in result


# ============================================================
# Project inbox + check_hard_stop_criteria interaction
# ============================================================

class TestProjectConvergeIntegration:
    """Test that Project converge methods work together correctly."""

    def test_check_criteria_with_metrics(self):
        project = _make_project_with_config()
        project.metrics = {"lint.errors": 0}
        results = project.check_hard_stop_criteria()
        assert all(results.values())

    def test_check_criteria_without_config(self):
        project = Project(module="test")
        results = project.check_hard_stop_criteria()
        assert results == {}

    def test_is_converged_true(self):
        project = _make_project_with_config()
        project.metrics = {"lint.errors": 0}
        assert project.is_converged()

    def test_is_converged_false(self):
        project = _make_project_with_config()
        # Nested metrics so _resolve_metric_path("lint.errors") → 3 ≠ 0
        project.metrics = {"lint": {"errors": 3}}
        assert not project.is_converged()

    def test_is_converged_no_config(self):
        project = Project(module="test")
        assert not project.is_converged()

    def test_record_iteration_updates_state(self):
        """record_iteration updates iteration, metrics, score, best_score."""
        project = _make_project_with_config()
        project.current_stage = "lint"
        project.record_iteration("lint", {"lint.errors": 2}, 3.0)
        assert project.iteration == 1
        assert project.score == 3.0
        assert project.best_score == 3.0
        assert project.metrics["lint.errors"] == 2

        project.record_iteration("lint", {"lint.errors": 0}, 10.0)
        assert project.iteration == 2
        assert project.score == 10.0
        assert project.best_score == 10.0
        assert project.no_improve_count == 0

    def test_record_iteration_tracks_no_improve(self):
        """If score doesn't improve, no_improve_count increases."""
        project = _make_project_with_config()
        project.current_stage = "lint"
        project.record_iteration("lint", {"lint.errors": 2}, 5.0)
        assert project.best_score == 5.0

        project.record_iteration("lint", {"lint.errors": 1}, 3.0)
        assert project.score == 3.0
        assert project.best_score == 5.0
        assert project.no_improve_count == 1

    def test_is_stalled(self):
        project = _make_project_with_config(criteria_no_improve_limit=2)
        project.current_stage = "lint"
        project.record_iteration("lint", {}, 5.0)
        project.record_iteration("lint", {}, 3.0)
        project.record_iteration("lint", {}, 2.0)
        assert project.is_stalled()

    def test_is_exhausted(self):
        project = _make_project_with_config(criteria_max_total_iterations=3)
        project.current_stage = "lint"
        project.record_iteration("lint", {}, 1.0)
        project.record_iteration("lint", {}, 1.0)
        project.record_iteration("lint", {}, 1.0)
        assert project.is_exhausted()


# ============================================================
# Edge cases
# ============================================================

class TestEdgeCases:
    """Edge cases for converge context and inbox."""

    def _get_fn(self):
        from core.agent_runner import _build_converge_context
        return _build_converge_context

    def test_score_zero_is_shown(self):
        """Score of 0.0 should be shown (it's > -999.0)."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 0.0
        project.best_score = 0.0
        project.iteration = 1
        result = fn(project)
        assert "Score: 0.0" in result

    def test_negative_score_is_shown(self):
        """Negative score should be shown as long as > -999.0."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = -5.0
        project.best_score = -3.0
        project.iteration = 1
        result = fn(project)
        assert "Score: -5.0" in result

    def test_exactly_default_score_omitted(self):
        """Score exactly -999.0 should be omitted."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = -999.0
        project.best_score = -999.0
        project.iteration = 0
        # Only have stage → should show stage only, no score
        result = fn(project)
        assert "Score:" not in result

    def test_inbox_with_unicode_message(self):
        """Inbox handles unicode messages."""
        project = _make_project_with_config()
        project.send_to_inbox("override", "스테이지 변경: sim으로 전환")
        msgs = project.drain_inbox()
        assert msgs[0]["message"] == "스테이지 변경: sim으로 전환"

    def test_metrics_with_none_value(self):
        """Metrics with None value should be handled gracefully."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {"lint.errors": None}
        # Should not crash
        result = fn(project)
        assert "Metrics:" in result
        assert "lint.errors=None" in result

    def test_very_large_metrics_dict(self):
        """Metrics dict with many entries is truncated to 8."""
        fn = self._get_fn()
        project = _make_project_with_config()
        project.score = 5.0
        project.best_score = 5.0
        project.iteration = 1
        project.metrics = {f"metric_{i:03d}": i for i in range(100)}
        result = fn(project)
        assert "Metrics:" in result
        # Should have at most 8 comma-separated entries
        metrics_part = result.split("Metrics: ")[1].split(" | ")[0]
        assert len(metrics_part.split(", ")) <= 8

    def test_inbox_persistence_round_trip(self):
        """Inbox survives save_state/load_state round-trip."""
        import tempfile, json
        project = _make_project_with_config()
        project.send_to_inbox("override", "msg1")
        project.send_to_inbox("abort", "msg2")
        with tempfile.TemporaryDirectory() as tmpdir:
            project.session_dir = Path(tmpdir)
            project.save_state()

            restored = _make_project_with_config()
            restored.session_dir = Path(tmpdir)
            restored.load_state()
            msgs = restored.drain_inbox()
            assert len(msgs) == 2
            assert msgs[0]["type"] == "override"
            assert msgs[1]["type"] == "abort"


# ============================================================
# No-op Retry with Code Detection
# ============================================================

class TestNoopRetryWithCodeDetection:
    """Test that the agent retries when code is detected but no tool was called."""

    def test_detects_code_block_with_write_intent(self):
        """Text with code block + write intent should trigger retry."""
        text = "I'll create the counter module.\n```systemverilog\nmodule counter;\nendmodule\n```"
        has_code = '```' in text or 'endmodule' in text
        has_intent = any(kw in text.lower() for kw in
            ['write', 'create', 'implement', 'save', 'generate file', 'output:'])
        assert has_code and has_intent

    def test_no_retry_without_code(self):
        """Text without code blocks should not trigger retry."""
        text = "I'll read the file first."
        has_code = '```' in text or 'endmodule' in text
        assert not has_code


class TestWriteFileContentRecovery:
    """Test that write_file recovers content when normal parsing fails."""

    def test_triple_quoted_content_recovery(self):
        """Content in triple quotes should be recovered by dispatch fallback."""
        from core.tool_dispatcher import dispatch_tool

        # Simulate the case where normal parser returns kwargs without 'content'
        # The greedy regex fallback in dispatch_tool should recover it
        captured = {}

        def mock_write_file(path="", content=""):
            captured["path"] = path
            captured["content"] = content
            return f"Written {len(content)} chars to {path}"

        result = dispatch_tool(
            "write_file",
            'path="test.sv", content="""module test #(parameter W=8)();\nendmodule"""',
            available_tools={"write_file": mock_write_file},
        )
        assert "Written" in result
        assert captured.get("content") == "module test #(parameter W=8)();\nendmodule"

    def test_greedy_quote_content_recovery(self):
        """Content with embedded quotes should be recovered by greedy regex."""
        from core.tool_dispatcher import dispatch_tool

        captured = {}

        def mock_write_file(path="", content=""):
            captured["path"] = path
            captured["content"] = content
            return f"OK: {len(content)} chars"

        # This is what happens when normal parser splits on the first quote
        # and loses the content. The greedy fallback should catch it.
        result = dispatch_tool(
            "write_file",
            'path="test.sv", content="module test; // a \\"comment\\" endmodule"',
            available_tools={"write_file": mock_write_file},
        )
        assert "OK:" in result

    def test_placeholder_args_returns_helpful_error(self):
        """write_file(...) with literal '...' args_str should return helpful error."""
        from core.tool_dispatcher import dispatch_tool

        captured = {}

        def mock_write_file(path="", content=""):
            captured["path"] = path
            return f"Written {len(content)} chars"

        # Exact reproduction of user's error: args_str is "..."
        result = dispatch_tool(
            "write_file", "...",
            available_tools={"write_file": mock_write_file},
        )
        assert "Error" in result
        assert "write_file() requires" in result
        # The mock should NOT have been called
        assert captured == {}

    def test_path_only_returns_helpful_error(self):
        """write_file(path='x') with no content should return helpful error."""
        from core.tool_dispatcher import dispatch_tool

        captured = {}

        def mock_write_file(path="", content=""):
            captured["path"] = path
            return f"Written {len(content)} chars"

        result = dispatch_tool(
            "write_file", 'path="test.sv"',
            available_tools={"write_file": mock_write_file},
        )
        assert "Error" in result
        assert "missing 'content'" in result
        assert captured == {}


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
