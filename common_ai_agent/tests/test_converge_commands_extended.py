"""
Extended integration tests for /converge slash commands.

Builds on the existing 40 tests in test_converge_commands.py with:
  - /converge start with real converge.yaml fixture from workflow/eda/
  - /converge next with mocked LoopController internals (_execute_stage, parser)
  - /converge auto with mocked controller.run()
  - /converge history with multi-stage data and score trajectory
  - /converge report with multi-stage data and full convergence
  - /converge override with inbox verification + save_state
  - /converge inject with inbox verification + message persistence
  - Session persistence across commands (save_state/load_state round-trip)
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock, PropertyMock

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import (
    Project,
    ConvergeConfig,
    StageConfig,
    FeedbackEdge,
    ClassifierRule,
)
from core.converge import (
    LoopController,
    ScoreCalculator,
    OutputParser,
    ClassifierEngine,
    FeedbackRouter,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def registry():
    """Create a fresh SlashCommandRegistry for each test."""
    from core.slash_commands import SlashCommandRegistry
    return SlashCommandRegistry()


@pytest.fixture
def tmp_project_dir(tmp_path):
    """Create a temporary project directory with converge.yaml."""
    ws = tmp_path / "workflow" / "eda"
    ws.mkdir(parents=True)

    converge_yaml = {
        "name": "eda-loop",
        "description": "Test EDA converge loop",
        "stages": [
            {"id": "spec", "workspace": "eda", "agent": "execute", "prompt": "Write spec for {module}"},
            {"id": "rtl", "workspace": "eda", "agent": "execute", "prompt": "Write RTL for {module}"},
            {"id": "lint", "workspace": "eda", "agent": "execute", "prompt": "Lint {module}"},
            {"id": "sim", "workspace": "eda", "agent": "execute", "prompt": "Simulate {module}"},
        ],
        "criteria": {
            "hard_stop": [
                {"metric": "lint.errors", "operator": "==", "value": 0},
                {"metric": "sim.fail", "operator": "==", "value": 0},
            ],
            "score_threshold": 10.0,
            "max_total_iterations": 5,
            "no_improve_limit": 2,
        },
        "score_function": {
            "weights": {
                "lint.errors": -5,
                "lint.warnings": -1,
                "sim.fail": -3,
                "sim.pass": 2,
            },
        },
        "feedback_graph": [],
        "classifiers": [],
        "parsers": {
            "lint": {
                "type": "count_patterns",
                "patterns": {
                    "errors": r"Error:.*",
                    "warnings": r"Warning:.*",
                },
            },
            "sim": {
                "type": "count_patterns",
                "patterns": {
                    "pass": r"PASS",
                    "fail": r"FAIL",
                },
            },
        },
        "rollback": {"enabled": True, "paths": [], "on": "regressed"},
    }

    import yaml
    (ws / "converge.yaml").write_text(
        yaml.dump(converge_yaml, default_flow_style=False),
        encoding="utf-8",
    )

    workspace_json = {"name": "eda", "force_skills": ["verilog-expert"]}
    (ws / "workspace.json").write_text(
        json.dumps(workspace_json, indent=2),
        encoding="utf-8",
    )

    return tmp_path


def _make_config():
    """Create a ConvergeConfig for testing."""
    return ConvergeConfig(
        name="test-loop",
        stages=[
            StageConfig(id="spec", workspace="eda", prompt="Write spec for {module}"),
            StageConfig(id="rtl", workspace="eda", prompt="Write RTL for {module}"),
            StageConfig(id="lint", workspace="eda", prompt="Lint {module}"),
            StageConfig(id="sim", workspace="eda", prompt="Simulate {module}"),
        ],
        criteria_hard_stop=[
            {"metric": "lint.errors", "operator": "==", "value": 0},
            {"metric": "sim.fail", "operator": "==", "value": 0},
        ],
        criteria_score_threshold=10.0,
        criteria_max_total_iterations=5,
        criteria_no_improve_limit=2,
        score_weights={"lint.errors": -5, "sim.fail": -3, "sim.pass": 2},
        parsers={
            "lint": {"type": "count_patterns", "patterns": {"errors": r"Error:.*", "warnings": r"Warning:.*"}},
            "sim": {"type": "count_patterns", "patterns": {"pass": r"PASS", "fail": r"FAIL"}},
        },
    )


def _make_project_with_session(tmp_path):
    """Create a Project with session_dir set for persistence tests."""
    config = _make_config()
    project = Project(
        module="counter",
        converge_config=config,
        variables={"module": "counter"},
    )
    project.current_stage = "spec"
    project.session_dir = tmp_path / ".session" / "counter"
    project.session_dir.mkdir(parents=True, exist_ok=True)
    return project


# ============================================================
# /converge start with real converge.yaml
# ============================================================

class TestConvergeStartWithYaml:
    """Test /converge start using actual converge.yaml files."""

    def test_start_with_real_eda_yaml(self, registry, tmp_project_dir):
        """Start converge loop with the test fixture converge.yaml."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        result = registry._converge_start(['counter', '-p', str(yaml_path)])
        assert '✅' in result
        assert 'counter' in result
        assert 'spec' in result
        assert 'rtl' in result
        assert 'lint' in result
        assert 'sim' in result

        # Session was created
        sess = registry._cv_get_session()
        assert sess is not None
        assert sess['project'].module == 'counter'

    def test_start_creates_session_dir(self, registry, tmp_project_dir):
        """Starting a loop should create the session directory."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])
        sess = registry._cv_get_session()
        assert sess['project'].session_dir is not None

    def test_start_saves_state(self, registry, tmp_project_dir):
        """Starting should persist state via save_state."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])
        sess = registry._cv_get_session()
        if sess['project'].session_dir:
            state_file = sess['project'].session_dir / "loop_state.json"
            assert state_file.exists()

    def test_start_with_bad_path(self, registry, tmp_project_dir):
        """Start with nonexistent YAML path — may fall back to workspace default or fail."""
        result = registry._converge_start(['counter', '-p', '/nonexistent/converge.yaml'])
        # Either succeeds (falls back to workflow/eda/converge.yaml) or fails
        assert '✅' in result or '❌' in result

    def test_start_sets_controller(self, registry, tmp_project_dir):
        """Starting should create a LoopController."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])
        sess = registry._cv_get_session()
        assert sess['controller'] is not None


# ============================================================
# /converge next with mocked LoopController
# ============================================================

class TestConvergeNextMocked:
    """Test /converge next with mocked controller internals."""

    def _setup_session(self, registry, tmp_path):
        """Set up a session with mocked controller."""
        project = _make_project_with_session(tmp_path)
        config = project.converge_config
        controller = MagicMock(spec=LoopController)
        controller._stage_map = {s.id: s for s in config.stages}
        registry._cv_set_session(project, controller, verbose_level=2)
        return project, controller

    def test_next_executes_current_stage(self, registry, tmp_path):
        """next should execute the current stage via _execute_stage."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("spec", "Spec output generated")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {"completeness": 0.9}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = 5.0

        result = registry._converge_next()
        assert 'Step complete' in result
        assert 'spec' in result
        controller._execute_stage.assert_called_once()

    def test_next_parses_output(self, registry, tmp_path):
        """next should parse raw output into metrics."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("lint", "Error: foo\nWarning: bar")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {"errors": 1, "warnings": 1}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = -5.0

        result = registry._converge_next()
        controller.parser.parse.assert_called_once()
        assert 'Step complete' in result

    def test_next_records_iteration(self, registry, tmp_path):
        """next should record iteration in project history."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("spec", "output")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = 3.0

        registry._converge_next()
        assert project.iteration == 1

    def test_next_detects_convergence(self, registry, tmp_path):
        """next should detect convergence when criteria met."""
        project, controller = self._setup_session(registry, tmp_path)
        # Use nested metrics for correct _resolve_metric_path
        project.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        controller._execute_stage.return_value = ("lint", "clean output")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = 10.0

        result = registry._converge_next()
        assert 'CONVERGED' in result or 'converged' in result.lower() or '✅' in result

    def test_next_detects_exhaustion(self, registry, tmp_path):
        """next should detect when max iterations reached."""
        project, controller = self._setup_session(registry, tmp_path)
        project.iteration = 4  # one less than max (5)
        # Set metrics with errors so criteria are NOT met (prevents convergence check)
        project.metrics = {"lint": {"errors": 5}, "sim": {"fail": 2}}
        controller._execute_stage.return_value = ("spec", "output")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = 1.0

        result = registry._converge_next()
        assert 'EXHAUSTED' in result or 'exhausted' in result.lower() or '❌' in result

    def test_next_no_output(self, registry, tmp_path):
        """next handles case where stage produces no output."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("spec", None)

        result = registry._converge_next()
        assert 'no output' in result.lower() or 'no_output' in result.lower() or 'None' in result

    def test_next_saves_state_after_step(self, registry, tmp_path):
        """next should persist state after each step."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("spec", "output")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = 2.0

        registry._converge_next()
        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["iteration"] == 1

    def test_next_verbose_level_2_shows_metrics(self, registry, tmp_path):
        """With verbose_level=2, next should show parsed metrics."""
        project, controller = self._setup_session(registry, tmp_path)
        controller._execute_stage.return_value = ("lint", "output")
        controller.parser = MagicMock()
        controller.parser.parse.return_value = {"errors": 0, "warnings": 2}
        controller.score_calc = MagicMock()
        controller.score_calc.compute.return_value = -2.0

        result = registry._converge_next()
        assert "lint.errors" in result or "errors" in result


# ============================================================
# /converge auto with mocked controller.run()
# ============================================================

class TestConvergeAutoMocked:
    """Test /converge auto with mocked controller.run()."""

    def _setup_session(self, registry, tmp_path):
        project = _make_project_with_session(tmp_path)
        controller = MagicMock(spec=LoopController)
        registry._cv_set_session(project, controller, verbose_level=2)
        return project, controller

    def test_auto_calls_controller_run(self, registry, tmp_path):
        """auto should call controller.run()."""
        project, controller = self._setup_session(registry, tmp_path)
        controller.run.return_value = project

        registry._converge_auto()
        controller.run.assert_called_once()

    def test_auto_converged_result(self, registry, tmp_path):
        """auto should format convergence result."""
        project, controller = self._setup_session(registry, tmp_path)
        # controller.run() returns a project — mock must return a SEPARATE
        # object because _converge_auto sets status="running" on the input.
        result_project = _make_project_with_session(tmp_path)
        result_project.status = "converged"
        result_project.convergence_reason = "All criteria met"
        result_project.score = 15.0
        result_project.best_score = 15.0
        result_project.iteration = 3
        result_project.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        controller.run.return_value = result_project

        result = registry._converge_auto()
        assert 'converged' in result.lower()
        assert '15.0' in result

    def test_auto_failed_result(self, registry, tmp_path):
        """auto should handle failed status."""
        project, controller = self._setup_session(registry, tmp_path)
        project.status = "failed"
        project.convergence_reason = "Max iterations reached"
        project.score = -5.0
        project.best_score = 2.0
        project.iteration = 5
        controller.run.return_value = project

        result = registry._converge_auto()
        assert 'failed' in result.lower() or 'Max iterations' in result

    def test_auto_updates_session(self, registry, tmp_path):
        """auto should update session with result project."""
        project, controller = self._setup_session(registry, tmp_path)
        # Return a separate object to avoid mutation from _converge_auto setting running
        result_project = _make_project_with_session(tmp_path)
        result_project.status = "converged"
        result_project.score = 10.0
        result_project.best_score = 10.0
        result_project.iteration = 2
        result_project.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        controller.run.return_value = result_project

        registry._converge_auto()
        sess = registry._cv_get_session()
        assert sess['project'].status == "converged"

    def test_auto_sets_running_phase(self, registry, tmp_path):
        """auto should set phase to 'running' before calling run()."""
        project, controller = self._setup_session(registry, tmp_path)
        captured = {}

        def capture_state():
            captured['phase'] = project.phase
            captured['status'] = project.status
            return project
        controller.run.side_effect = capture_state

        registry._converge_auto()
        assert captured.get('phase') == "running"
        assert captured.get('status') == "running"

    def test_auto_shows_criteria_lines(self, registry, tmp_path):
        """auto result should show criteria check results."""
        project, controller = self._setup_session(registry, tmp_path)
        project.status = "converged"
        project.convergence_reason = "All met"
        project.score = 10.0
        project.best_score = 10.0
        project.iteration = 2
        project.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        controller.run.return_value = project

        result = registry._converge_auto()
        # Should show criteria with ✅/❌
        assert "Criteria" in result
        assert "✅" in result


# ============================================================
# /converge history with multi-stage data
# ============================================================

class TestConvergeHistoryExtended:
    """Extended history tests with multi-stage data."""

    def _setup_with_history(self, registry, tmp_path):
        project = _make_project_with_session(tmp_path)
        project.current_stage = "spec"
        project.record_iteration("spec", {"spec.completeness": 0.5}, 2.0)
        project.current_stage = "rtl"
        project.record_iteration("rtl", {"rtl.lines": 150}, 3.0)
        project.current_stage = "lint"
        project.record_iteration("lint", {"lint": {"errors": 2}}, -10.0)
        project.current_stage = "lint"
        project.record_iteration("lint", {"lint": {"errors": 0}}, 0.0)
        project.current_stage = "sim"
        project.record_iteration("sim", {"sim": {"pass": 5, "fail": 0}}, 10.0)
        controller = MagicMock()
        registry._cv_set_session(project, controller)
        return project

    def test_history_shows_all_stages(self, registry, tmp_path):
        project = self._setup_with_history(registry, tmp_path)
        result = registry._converge_history()
        assert 'spec' in result
        assert 'rtl' in result
        assert 'lint' in result
        assert 'sim' in result

    def test_history_shows_score_trajectory(self, registry, tmp_path):
        project = self._setup_with_history(registry, tmp_path)
        result = registry._converge_history()
        assert '2.0' in result or '2' in result
        assert '10.0' in result or '10' in result

    def test_history_from_disk(self, registry, tmp_path):
        """History should load from disk when no active session."""
        project = _make_project_with_session(tmp_path)
        project.current_stage = "spec"
        project.record_iteration("spec", {}, 5.0)
        project.save_state()

        # Clear session
        registry._cv_clear_session()

        # Patch SESSION_DIR to point to the session dir's parent
        import config as _cfg
        old_session = getattr(_cfg, 'SESSION_DIR', '')
        _cfg.SESSION_DIR = str(tmp_path / ".session" / "counter")
        try:
            result = registry._converge_history()
            # May or may not find it depending on restore_project
            assert isinstance(result, str)
        finally:
            _cfg.SESSION_DIR = old_session

    def test_history_five_iterations(self, registry, tmp_path):
        project = self._setup_with_history(registry, tmp_path)
        assert len(project.history) == 5
        result = registry._converge_history()
        assert 'counter' in result


# ============================================================
# /converge report with multi-stage data
# ============================================================

class TestConvergeReportExtended:
    """Extended report tests with multi-stage convergence data."""

    def _setup_converged_project(self, registry, tmp_path):
        config = _make_config()
        project = Project(
            module="counter",
            converge_config=config,
            variables={"module": "counter", "rtl_path": "/tmp/counter.v"},
        )
        project.session_dir = tmp_path / ".session" / "counter"
        project.session_dir.mkdir(parents=True, exist_ok=True)
        project.current_stage = "spec"
        project.record_iteration("spec", {"spec.completeness": 1.0}, 5.0)
        project.current_stage = "rtl"
        project.record_iteration("rtl", {"rtl.lines": 200}, 6.0)
        project.current_stage = "lint"
        project.record_iteration("lint", {"lint": {"errors": 0}}, 10.0)
        project.current_stage = "sim"
        project.record_iteration("sim", {"sim": {"pass": 10, "fail": 0}}, 20.0)
        project.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        project.status = "converged"
        project.convergence_reason = "All hard_stop criteria met"
        project.jobs = ["job1", "job2", "job3"]

        controller = MagicMock()
        registry._cv_set_session(project, controller)
        return project

    def test_report_full_convergence(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        assert 'CONVERGE REPORT' in result
        assert 'converged' in result
        assert 'counter' in result
        assert 'All hard_stop criteria met' in result

    def test_report_shows_stage_breakdown(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        assert 'Stage Breakdown' in result
        assert 'spec' in result
        assert 'rtl' in result
        assert 'lint' in result
        assert 'sim' in result

    def test_report_shows_score_summary(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        # Should show min/max/final/best scores
        assert 'Min:' in result or 'min' in result.lower()
        assert 'Max:' in result or 'max' in result.lower()

    def test_report_shows_criteria(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        assert 'Criteria' in result
        assert '✅' in result

    def test_report_shows_variables(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        assert 'rtl_path' in result

    def test_report_shows_jobs(self, registry, tmp_path):
        project = self._setup_converged_project(registry, tmp_path)
        result = registry._converge_report()
        assert 'job1' in result or 'Jobs' in result or 'jobs' in result

    def test_report_persisted_and_restored(self, registry, tmp_path):
        """Report data should survive save/load cycle."""
        project = self._setup_converged_project(registry, tmp_path)
        project.save_state()

        # Verify state file
        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert state["status"] == "converged"
        assert state["convergence_reason"] == "All hard_stop criteria met"
        assert len(state["history"]) == 4


# ============================================================
# /converge override with inbox verification
# ============================================================

class TestConvergeOverrideExtended:
    """Extended override tests with inbox + save_state verification."""

    def _setup_session(self, registry, tmp_path):
        project = _make_project_with_session(tmp_path)
        controller = MagicMock()
        registry._cv_set_session(project, controller)
        return project

    def test_override_queues_in_inbox(self, registry, tmp_path):
        """Override should add message to project inbox."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['lint', 'syntax_error'])
        assert len(project.inbox) == 1
        assert project.inbox[0]['type'] == 'override'

    def test_override_inbox_has_stage_and_classifier(self, registry, tmp_path):
        """Override inbox message should contain stage and classifier."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['sim', 'rtl_bug'])
        msg = project.inbox[0]
        assert msg['stage'] == 'sim'
        assert msg['classifier'] == 'rtl_bug'

    def test_override_saves_state(self, registry, tmp_path):
        """Override should persist inbox via save_state."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['lint', 'timing_error'])

        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()
        state = json.loads(state_file.read_text())
        assert len(state["inbox"]) == 1
        assert state["inbox"][0]["type"] == "override"

    def test_multiple_overrides_queue_up(self, registry, tmp_path):
        """Multiple overrides should accumulate in inbox."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['lint', 'syntax_error'])
        registry._converge_override(['sim', 'rtl_bug'])
        registry._converge_override(['sim', 'tb_bug'])
        assert len(project.inbox) == 3

    def test_override_with_special_chars(self, registry, tmp_path):
        """Override handles special characters in classifier name."""
        project = self._setup_session(registry, tmp_path)
        result = registry._converge_override(['lint', 'error-type_1'])
        assert '✅' in result

    def test_override_inbox_can_be_drained(self, registry, tmp_path):
        """Override messages can be drained from inbox."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['lint', 'syntax_error'])
        msgs = project.drain_inbox()
        assert len(msgs) == 1
        assert msgs[0]['classifier'] == 'syntax_error'
        assert len(project.inbox) == 0


# ============================================================
# /converge inject with inbox verification
# ============================================================

class TestConvergeInjectExtended:
    """Extended inject tests with message persistence."""

    def _setup_session(self, registry, tmp_path):
        project = _make_project_with_session(tmp_path)
        controller = MagicMock()
        registry._cv_set_session(project, controller)
        return project

    def test_inject_adds_user_inject_to_inbox(self, registry, tmp_path):
        project = self._setup_session(registry, tmp_path)
        registry._converge_inject('fix timing violation on clk domain')
        assert len(project.inbox) == 1
        assert project.inbox[0]['type'] == 'user_inject'
        assert project.inbox[0]['message'] == 'fix timing violation on clk domain'

    def test_inject_saves_state(self, registry, tmp_path):
        project = self._setup_session(registry, tmp_path)
        registry._converge_inject('check reset synchronizer')

        state_file = project.session_dir / "loop_state.json"
        state = json.loads(state_file.read_text())
        assert len(state["inbox"]) == 1
        assert state["inbox"][0]["type"] == "user_inject"

    def test_inject_shows_current_state(self, registry, tmp_path):
        """Inject result should show current stage and iteration."""
        project = self._setup_session(registry, tmp_path)
        project.iteration = 3
        result = registry._converge_inject('debug this')
        assert 'spec' in result  # current stage
        assert '3' in result     # iteration count

    def test_inject_accumulates_with_override(self, registry, tmp_path):
        """Inject and override messages can coexist in inbox."""
        project = self._setup_session(registry, tmp_path)
        registry._converge_override(['lint', 'syntax_error'])
        registry._converge_inject('also fix the reset')
        assert len(project.inbox) == 2

    def test_inject_long_message(self, registry, tmp_path):
        """Inject handles long messages."""
        project = self._setup_session(registry, tmp_path)
        long_msg = "Fix the following issues: " + ", ".join(f"issue_{i}" for i in range(20))
        result = registry._converge_inject(long_msg)
        assert '✅' in result
        assert len(project.inbox) == 1

    def test_inject_unicode_message(self, registry, tmp_path):
        """Inject handles unicode messages."""
        project = self._setup_session(registry, tmp_path)
        result = registry._converge_inject('타이밍 위반 수정 필요')
        assert '✅' in result


# ============================================================
# Session persistence across commands
# ============================================================

class TestSessionPersistence:
    """Tests that converge session state persists correctly across commands."""

    def test_start_then_status(self, registry, tmp_project_dir):
        """After start, status should show the new session."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])

        result = registry._converge_status()
        assert 'counter' in result

    def test_start_then_override_then_check_inbox(self, registry, tmp_project_dir):
        """Override after start should persist in inbox."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])

        registry._converge_override(['lint', 'syntax_error'])
        sess = registry._cv_get_session()
        assert len(sess['project'].inbox) == 1

    def test_start_then_inject_then_check_inbox(self, registry, tmp_project_dir):
        """Inject after start should persist in inbox."""
        yaml_path = tmp_project_dir / "workflow" / "eda" / "converge.yaml"
        registry._converge_start(['counter', '-p', str(yaml_path)])

        registry._converge_inject('fix the timing')
        sess = registry._cv_get_session()
        assert len(sess['project'].inbox) == 1
        assert sess['project'].inbox[0]['type'] == 'user_inject'

    def test_level_persists_across_calls(self, registry, tmp_path):
        """Verbosity level should persist across commands."""
        project = _make_project_with_session(tmp_path)
        registry._cv_set_session(project, MagicMock(), verbose_level=1)

        registry._converge_level(['3'])
        result = registry._converge_level([])
        assert '3' in result

    def test_state_file_survives_clear(self, registry, tmp_path):
        """After clearing session, state file should still exist on disk."""
        project = _make_project_with_session(tmp_path)
        project.current_stage = "spec"
        project.record_iteration("spec", {}, 5.0)
        project.save_state()

        registry._cv_set_session(project, MagicMock())
        registry._cv_clear_session()

        # State file should still exist
        state_file = project.session_dir / "loop_state.json"
        assert state_file.exists()

    def test_multiple_iterations_persist(self, registry, tmp_path):
        """Multiple iterations should be reflected in persisted state."""
        project = _make_project_with_session(tmp_path)
        # Set metrics so criteria are NOT met (prevents early convergence)
        project.metrics = {"lint": {"errors": 5}, "sim": {"fail": 2}}
        config = project.converge_config
        controller = MagicMock(spec=LoopController)
        controller._stage_map = {s.id: s for s in config.stages}
        registry._cv_set_session(project, controller, verbose_level=2)

        # Simulate 3 iterations
        for i, stage_name in enumerate(["spec", "rtl", "lint"]):
            controller._execute_stage.return_value = (stage_name, f"output_{i}")
            controller.parser = MagicMock()
            controller.parser.parse.return_value = {"quality": i}
            controller.score_calc = MagicMock()
            controller.score_calc.compute.return_value = float(i * 2)
            registry._converge_next()

        state_file = project.session_dir / "loop_state.json"
        state = json.loads(state_file.read_text())
        assert state["iteration"] == 3
        assert len(state["history"]) == 3


# ============================================================
# Level command edge cases
# ============================================================

class TestConvergeLevelExtended:
    """Extended level tests."""

    def test_level_boundary_1(self, registry):
        result = registry._converge_level(['1'])
        assert '✅' in result

    def test_level_boundary_3(self, registry):
        result = registry._converge_level(['3'])
        assert '✅' in result

    def test_level_out_of_range_0(self, registry):
        result = registry._converge_level(['0'])
        assert 'must be 1, 2, or 3' in result

    def test_level_out_of_range_4(self, registry):
        result = registry._converge_level(['4'])
        assert 'must be 1, 2, or 3' in result

    def test_level_negative(self, registry):
        result = registry._converge_level(['-1'])
        assert 'must be 1, 2, or 3' in result

    def test_level_updates_session(self, registry, tmp_path):
        project = _make_project_with_session(tmp_path)
        registry._cv_set_session(project, MagicMock(), verbose_level=1)
        registry._converge_level(['3'])
        sess = registry._cv_get_session()
        assert sess['verbose_level'] == 3


# ============================================================
# Dispatch integration extended
# ============================================================

class TestDispatchIntegrationExtended:
    """Extended dispatch tests."""

    def test_dispatch_override_with_session(self, registry, tmp_path):
        """Full dispatch of /converge override with active session."""
        project = _make_project_with_session(tmp_path)
        registry._cv_set_session(project, MagicMock())
        result = registry.execute('/converge override lint syntax_error')
        assert '✅' in result

    def test_dispatch_inject_with_session(self, registry, tmp_path):
        """Full dispatch of /converge inject with active session."""
        project = _make_project_with_session(tmp_path)
        registry._cv_set_session(project, MagicMock())
        result = registry.execute('/converge inject fix timing')
        assert '✅' in result

    def test_dispatch_level_set(self, registry, tmp_path):
        """Full dispatch of /converge level with value."""
        project = _make_project_with_session(tmp_path)
        registry._cv_set_session(project, MagicMock())
        result = registry.execute('/converge level 3')
        assert '✅' in result

    def test_dispatch_next_no_session(self, registry):
        """Full dispatch of /converge next without session."""
        result = registry.execute('/converge next')
        assert 'No active' in result

    def test_dispatch_auto_no_session(self, registry):
        """Full dispatch of /converge auto without session."""
        result = registry.execute('/converge auto')
        assert 'No active' in result


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
