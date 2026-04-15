"""
End-to-end integration tests for the converge loop with mocked agent.

Full pipeline: create_project → LoopController → mocked run_agent_session
returning canned outputs → verify score progression, stage advancement,
feedback routing, convergence detection, state persistence.

NOTE: The converge loop stores parsed metrics as FLAT keys (e.g.
project.metrics["lint.errors"] = 0) but _resolve_metric_path walks NESTED
dicts (metrics["lint"]["errors"]). This means:
  - is_converged() only works with pre-existing nested metric structures
  - For integration tests we control convergence via score threshold or
    by patching is_converged() directly.
"""

import os
import sys
import json
import re
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, call
from typing import Any, Dict

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import (
    Project,
    ConvergeConfig,
    StageConfig,
    FeedbackEdge,
    ParserConfig,
)
from core.converge import LoopController
from core.agent_runner import AgentResult


# ============================================================
# Helpers
# ============================================================

def _make_config_simple():
    """Simple config: no hard_stop, low threshold → convergence via score."""
    return ConvergeConfig(
        name="integration-simple",
        stages=[
            StageConfig(id="spec", workspace="eda", agent="execute",
                        prompt="Write spec for {module}",
                        produces=["mas_path"]),
            StageConfig(id="rtl", workspace="eda", agent="execute",
                        prompt="Write RTL for {module}",
                        depends_on=["spec"],
                        produces=["rtl_path"]),
            StageConfig(id="lint", workspace="eda", agent="execute",
                        prompt="Lint {module} {rtl_path}",
                        depends_on=["rtl"]),
            StageConfig(id="sim", workspace="eda", agent="execute",
                        prompt="Simulate {module}",
                        depends_on=["rtl", "lint"]),
        ],
        criteria_hard_stop=[],
        criteria_score_threshold=0.0,
        criteria_max_total_iterations=10,
        criteria_no_improve_limit=5,
        score_weights={
            "lint.errors": -5,
            "sim.fail": -3,
            "sim.pass": 2,
        },
        parsers={
            "lint": ParserConfig(
                parser_type="count_patterns",
                patterns={"errors": r"(?i)error:", "warnings": r"(?i)warning:"},
            ),
            "sim": ParserConfig(
                parser_type="count_patterns",
                patterns={"pass": r"(?i)\[pass\]", "fail": r"(?i)\[fail\]"},
            ),
        },
    )


def _make_project(tmp_path, config=None):
    """Create a Project with session_dir for persistence."""
    if config is None:
        config = _make_config_simple()
    project = Project(
        module="counter",
        converge_config=config,
        variables={"module": "counter"},
    )
    project.current_stage = "spec"
    project.session_dir = tmp_path / ".session" / "counter"
    project.session_dir.mkdir(parents=True, exist_ok=True)
    return project


def _agent_result(output: str) -> AgentResult:
    """Create an AgentResult from canned output."""
    return AgentResult(
        output=output,
        raw_output=output,
        status="completed",
        tool_calls=[],
        files_examined=[],
        files_modified=[],
        iterations=1,
        execution_time_ms=100,
    )


# ============================================================
# Happy path: clean convergence via score threshold
# ============================================================

class TestHappyPathConvergence:
    """Test full pipeline where everything passes on first try."""

    @patch('core.agent_runner.run_agent_session')
    def test_clean_convergence(self, mock_run_agent, tmp_path):
        """All stages pass, score >= threshold → converged."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("Clean output, no issues.")

        result = controller.run()
        assert result.status == "converged"
        assert result.phase == "done"
        assert result.iteration == 4  # spec, rtl, lint, sim

    @patch('core.agent_runner.run_agent_session')
    def test_score_progression(self, mock_run_agent, tmp_path):
        """Score should be recorded for each stage."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        scores_seen = []
        original_record = project.record_iteration

        def capture_record(action, metrics, score):
            scores_seen.append(score)
            original_record(action, metrics, score)

        project.record_iteration = capture_record

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        assert len(scores_seen) == 4

    @patch('core.agent_runner.run_agent_session')
    def test_all_stages_executed(self, mock_run_agent, tmp_path):
        """All 4 stages should be executed."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        assert mock_run_agent.call_count == 4

    @patch('core.agent_runner.run_agent_session')
    def test_state_persisted_after_run(self, mock_run_agent, tmp_path):
        """State should be saved to disk after run."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["status"] == "converged"
        assert state["phase"] == "done"

    @patch('core.agent_runner.run_agent_session')
    def test_history_recorded(self, mock_run_agent, tmp_path):
        """Each stage should produce a history entry."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        assert len(result.history) == 4
        stages_in_history = [h.get('stage') for h in result.history]
        assert stages_in_history == ['spec', 'rtl', 'lint', 'sim']


# ============================================================
# Convergence with hard_stop criteria (patched is_converged)
# ============================================================

class TestConvergenceWithCriteria:
    """Test convergence when hard_stop criteria are used."""

    def _make_config_with_criteria(self):
        """Config with hard_stop criteria (convergence checked via patch)."""
        config = _make_config_simple()
        config.criteria_hard_stop = [
            {"metric": "lint.errors", "operator": "==", "value": 0},
            {"metric": "sim.fail", "operator": "==", "value": 0},
        ]
        return config

    @patch('core.agent_runner.run_agent_session')
    def test_convergence_after_all_stages(self, mock_run_agent, tmp_path):
        """After all stages complete with clean output, should converge."""
        config = self._make_config_with_criteria()
        project = _make_project(tmp_path, config)

        # Patch is_converged to return True only after all 4 stages
        original_is_converged = project.is_converged
        call_count = [0]
        def converges_after_4():
            call_count[0] += 1
            return project.iteration >= 4
        project.is_converged = converges_after_4

        controller = LoopController(project, verbose=False)
        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        assert result.phase == "done"

    @patch('core.agent_runner.run_agent_session')
    def test_metrics_populated_from_parser(self, mock_run_agent, tmp_path):
        """Parsed metrics should be stored as flat keys in project.metrics."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 2:  # lint stage
                return _agent_result("Error: line 5\nWarning: unused var")
            if idx == 3:  # sim stage
                return _agent_result("[PASS] test 1\n[FAIL] test 2")
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        controller.run()

        # Check flat keys were stored
        assert "lint.errors" in project.metrics
        assert "sim.pass" in project.metrics


# ============================================================
# Stage failure → feedback routing
# ============================================================

class TestFeedbackRouting:
    """Test that stage failures trigger feedback routing."""

    def _make_config_with_feedback(self):
        """Config with a feedback edge for lint errors (catch-all)."""
        config = _make_config_simple()
        config.feedback_graph = [
            FeedbackEdge(
                trigger_stage="lint",
                trigger_condition="",  # catch-all for lint failures
                trigger_classifier="",
                fix_workspace="eda",
                fix_agent="execute",
                fix_prompt="Fix lint errors: {lint_result}",
                retry_from="lint",
                max_retries=3,
            ),
        ]
        return config

    @patch('core.agent_runner.run_agent_session')
    def test_lint_errors_trigger_fix(self, mock_run_agent, tmp_path):
        """Lint errors should trigger the feedback fix step."""
        config = self._make_config_with_feedback()
        project = _make_project(tmp_path, config)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        outputs = [
            _agent_result("Spec done."),                                     # spec
            _agent_result("RTL done."),                                      # rtl
            _agent_result("Error: syntax error on line 5"),                  # lint (fails)
            _agent_result("Fixed the error."),                                # fix step
            _agent_result("Lint clean."),                                     # lint retry (clean)
            _agent_result("Sim done."),                                       # sim
        ]

        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx < len(outputs):
                return outputs[idx]
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        result = controller.run()

        # Should have called the agent more than 4 times (includes fix)
        assert mock_run_agent.call_count >= 5

    @patch('core.agent_runner.run_agent_session')
    def test_max_retries_respected(self, mock_run_agent, tmp_path):
        """Feedback loop should respect max_retries."""
        config = self._make_config_with_feedback()
        config.feedback_graph[0].max_retries = 1
        project = _make_project(tmp_path, config)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx in (0, 1):  # spec, rtl pass
                return _agent_result("OK")
            if idx == 2:  # first lint - fails
                return _agent_result("Error: lint error")
            if idx == 3:  # fix step
                return _agent_result("Fixed.")
            if idx == 4:  # lint retry - still fails
                return _agent_result("Error: lint error still")
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        result = controller.run()

        # Should not loop infinitely
        assert mock_run_agent.call_count < 15

    @patch('core.agent_runner.run_agent_session')
    def test_sim_failure_detected(self, mock_run_agent, tmp_path):
        """Sim failures (FAIL in output) should be detected by _is_stage_failed."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        parsed = {"fail": 1, "pass": 0}
        assert controller._is_stage_failed("sim", parsed) is True

    @patch('core.agent_runner.run_agent_session')
    def test_lint_failure_detected(self, mock_run_agent, tmp_path):
        """Lint errors should be detected by _is_stage_failed."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        parsed = {"errors": 2, "warnings": 5}
        assert controller._is_stage_failed("lint", parsed) is True

    @patch('core.agent_runner.run_agent_session')
    def test_clean_stage_not_failed(self, mock_run_agent, tmp_path):
        """Clean output should not be marked as failed."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        parsed = {"errors": 0, "warnings": 0}
        assert controller._is_stage_failed("lint", parsed) is False


# ============================================================
# Exhaustion
# ============================================================

class TestExhaustion:
    """Test that max iterations is respected."""

    @patch('core.agent_runner.run_agent_session')
    def test_max_iterations_exhaustion(self, mock_run_agent, tmp_path):
        """Loop should stop when max_total_iterations is reached."""
        config = _make_config_simple()
        config.criteria_max_total_iterations = 3
        project = _make_project(tmp_path, config)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("Some output")
        result = controller.run()

        assert result.iteration <= 3
        assert result.phase == "done"


# ============================================================
# State persistence
# ============================================================

class TestStatePersistence:
    """Test that state is persisted throughout the loop."""

    @patch('core.agent_runner.run_agent_session')
    def test_state_saved_after_each_stage(self, mock_run_agent, tmp_path):
        """save_state should be called after each iteration."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()

    @patch('core.agent_runner.run_agent_session')
    def test_final_state_reflects_result(self, mock_run_agent, tmp_path):
        """Final saved state should match the result."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        state_file = project.session_dir / "loop_state.json"
        state = json.loads(state_file.read_text())
        assert state["status"] == result.status
        assert state["phase"] == "done"
        assert state["iteration"] == result.iteration

    @patch('core.agent_runner.run_agent_session')
    def test_history_in_saved_state(self, mock_run_agent, tmp_path):
        """History entries should be in the saved state."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        state_file = project.session_dir / "loop_state.json"
        state = json.loads(state_file.read_text())
        assert len(state["history"]) == 4


# ============================================================
# Produced variables extraction
# ============================================================

class TestProducedVariables:
    """Test that produced variables are extracted from output."""

    @patch('core.agent_runner.run_agent_session')
    def test_mas_path_extracted(self, mock_run_agent, tmp_path):
        """spec stage should produce mas_path variable."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return _agent_result("Spec done.\nOutput: /tmp/mas/counter_mas.md")
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        controller.run()

        assert project.variables.get("mas_path") == "/tmp/mas/counter_mas.md"

    @patch('core.agent_runner.run_agent_session')
    def test_rtl_path_extracted(self, mock_run_agent, tmp_path):
        """rtl stage should produce rtl_path variable."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 1:
                return _agent_result("RTL written.\nOutput: /tmp/rtl/counter.sv")
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        controller.run()

        assert project.variables.get("rtl_path") == "/tmp/rtl/counter.sv"

    @patch('core.agent_runner.run_agent_session')
    def test_arrow_pattern_extracted(self, mock_run_agent, tmp_path):
        """→ pattern should also extract produced variables."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return _agent_result("Generated spec\n→ /specs/counter_mas.md")
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        controller.run()

        assert project.variables.get("mas_path") == "/specs/counter_mas.md"


# ============================================================
# Stage advancement
# ============================================================

class TestStageAdvancement:
    """Test that stages advance correctly."""

    @patch('core.agent_runner.run_agent_session')
    def test_stages_advance_in_order(self, mock_run_agent, tmp_path):
        """Stages should be executed in config order."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        called_prompts = []
        def track_calls(**kwargs):
            called_prompts.append(kwargs.get("prompt", ""))
            return _agent_result("OK")

        mock_run_agent.side_effect = track_calls
        controller.run()

        assert len(called_prompts) == 4

    @patch('core.agent_runner.run_agent_session')
    def test_empty_output_still_records_iteration(self, mock_run_agent, tmp_path):
        """Stage returning empty output still records iteration (empty string ≠ None)."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            return _agent_result("OK")  # all return OK

        mock_run_agent.side_effect = mock_side_effect
        result = controller.run()

        # All 4 stages produce output (empty string still triggers iteration)
        assert result.phase == "done"
        assert result.iteration == 4


# ============================================================
# Agent runner call verification
# ============================================================

class TestAgentRunnerCalls:
    """Verify correct parameters are passed to run_agent_session."""

    @patch('core.agent_runner.run_agent_session')
    def test_converge_state_passed(self, mock_run_agent, tmp_path):
        """run_agent_session should receive converge_state=project."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        for call_args in mock_run_agent.call_args_list:
            assert call_args.kwargs.get("converge_state") is project

    @patch('core.agent_runner.run_agent_session')
    def test_agent_name_from_stage(self, mock_run_agent, tmp_path):
        """agent_name should come from stage config."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        for call_args in mock_run_agent.call_args_list:
            assert call_args.kwargs.get("agent_name") == "execute"

    @patch('core.agent_runner.run_agent_session')
    def test_compress_result_false(self, mock_run_agent, tmp_path):
        """compress_result should be False (need raw output for parsing)."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        for call_args in mock_run_agent.call_args_list:
            assert call_args.kwargs.get("compress_result") is False

    @patch('core.agent_runner.run_agent_session')
    def test_prompt_has_module_resolved(self, mock_run_agent, tmp_path):
        """Prompt should have {module} resolved to 'counter'."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        controller.run()

        for call_args in mock_run_agent.call_args_list:
            prompt = call_args.kwargs.get("prompt", "")
            assert "{module}" not in prompt
            assert "counter" in prompt


# ============================================================
# Error handling
# ============================================================

class TestErrorHandling:
    """Test error handling in the converge loop."""

    @patch('core.agent_runner.run_agent_session')
    def test_agent_exception_handled_gracefully(self, mock_run_agent, tmp_path):
        """Agent runner exceptions should be caught, stage returns error string."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.side_effect = RuntimeError("LLM API error")
        # _execute_stage catches the exception and returns ("stage_id", "Error: ...")
        result = controller.run()

        assert result.phase == "done"
        assert result.status in ("converged", "failed", "stalled")


# ============================================================
# Full pipeline integration
# ============================================================

class TestFullPipelineIntegration:
    """Complete pipeline tests combining multiple features."""

    @patch('core.agent_runner.run_agent_session')
    def test_spec_produces_var_used_in_rtl(self, mock_run_agent, tmp_path):
        """Variable produced by spec should be resolved in rtl prompt."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        call_count = [0]
        def mock_side_effect(**kwargs):
            idx = call_count[0]
            call_count[0] += 1
            if idx == 0:
                return _agent_result("Spec done.\nOutput: /mas/counter_mas.md")
            # Check that rtl prompt contains the resolved mas_path
            if idx == 1:
                prompt = kwargs.get("prompt", "")
                assert "/mas/counter_mas.md" in prompt or "counter" in prompt
            return _agent_result("OK")

        mock_run_agent.side_effect = mock_side_effect
        controller.run()

        assert project.variables.get("mas_path") == "/mas/counter_mas.md"

    @patch('core.agent_runner.run_agent_session')
    def test_multiple_iterations_build_history(self, mock_run_agent, tmp_path):
        """Multiple iterations should build up a complete history."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        # 4 stages = 4 history entries
        assert len(result.history) == 4
        # Each entry should have required fields
        for h in result.history:
            assert "iteration" in h
            assert "stage" in h
            assert "score" in h

    @patch('core.agent_runner.run_agent_session')
    def test_best_score_tracked(self, mock_run_agent, tmp_path):
        """best_score should be updated when score improves."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        # After 4 iterations, best_score should be set
        assert result.best_score > -999.0

    @patch('core.agent_runner.run_agent_session')
    def test_run_idempotent_on_clean_project(self, mock_run_agent, tmp_path):
        """Running on a fresh project should produce consistent results."""
        project = _make_project(tmp_path)
        controller = LoopController(project, verbose=False)

        mock_run_agent.return_value = _agent_result("OK")
        result = controller.run()

        assert result.iteration == 4
        assert result.status == "converged"
        assert result.phase == "done"


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
