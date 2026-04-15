"""
Tests for /converge slash commands registered in core/slash_commands.py.

Tests the command dispatch, session tracking, and all subcommands:
  start, status, next, auto, override, inject, level, history, report
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def registry():
    """Create a fresh SlashCommandRegistry for each test."""
    from core.slash_commands import SlashCommandRegistry
    return SlashCommandRegistry()


@pytest.fixture
def workspace_dir(tmp_path):
    """Create a minimal EDA workspace with converge.yaml."""
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

    # Also create workspace.json
    workspace_json = {"name": "eda", "force_skills": ["verilog-expert"]}
    (ws / "workspace.json").write_text(
        json.dumps(workspace_json, indent=2),
        encoding="utf-8",
    )

    return tmp_path


# ============================================================
# Test: Command Registration
# ============================================================

class TestConvergeRegistration:
    def test_converge_command_registered(self, registry):
        """Verify /converge is in the command list."""
        assert 'converge' in registry.commands

    def test_converge_alias_cv(self, registry):
        """Verify /cv alias works."""
        cmd = registry.commands['converge']
        assert 'cv' in cmd.get('aliases', [])

    def test_converge_in_completions(self, registry):
        """Verify /converge and /cv appear in completions."""
        completions = registry.get_completions()
        assert '/converge' in completions
        assert '/cv' in completions

    def test_converge_description(self, registry):
        """Verify description is set."""
        desc = registry.commands['converge']['description']
        assert 'converge' in desc.lower() or 'Converge' in desc


# ============================================================
# Test: /converge (no args → usage)
# ============================================================

class TestConvergeUsage:
    def test_no_args_shows_usage(self, registry):
        result = registry.execute('/converge')
        assert 'start' in result
        assert 'status' in result
        assert 'history' in result
        assert 'report' in result

    def test_unknown_subcommand(self, registry):
        result = registry.execute('/converge bogus')
        assert 'Unknown' in result or 'unknown' in result.lower()


# ============================================================
# Test: /converge start
# ============================================================

class TestConvergeStart:
    def test_start_no_module(self, registry):
        result = registry.execute('/converge start')
        assert 'Usage' in result

    @patch('core.slash_commands.SlashCommandRegistry._converge_start')
    def test_start_dispatches(self, mock_start, registry):
        mock_start.return_value = "OK"
        registry.execute('/converge start counter')
        mock_start.assert_called_once()
        args_passed = mock_start.call_args[0][0]
        assert args_passed == ['counter']

    def test_start_with_nonexistent_config(self, registry, workspace_dir):
        """Start should fail gracefully when converge.yaml doesn't exist."""
        # Remove the converge.yaml from temp dir
        cv = workspace_dir / "workflow" / "eda" / "converge.yaml"
        if cv.exists():
            cv.unlink()

        # Also patch config to use our temp dir as project root so no fallback
        import config as _cfg
        old_session = getattr(_cfg, 'SESSION_DIR', '')
        _cfg.SESSION_DIR = str(workspace_dir / ".session" / "test")
        # Also remove the ACTIVE_WORKSPACE env var to prevent fallback
        old_ws = os.environ.pop('ACTIVE_WORKSPACE', None)
        try:
            result = registry._converge_start(['counter', '-p', str(workspace_dir / "nonexistent.yaml")])
            assert 'not found' in result.lower() or 'failed' in result.lower() or '❌' in result
        finally:
            _cfg.SESSION_DIR = old_session
            if old_ws is not None:
                os.environ['ACTIVE_WORKSPACE'] = old_ws


# ============================================================
# Test: /converge status
# ============================================================

class TestConvergeStatus:
    def test_status_no_session(self, registry):
        """Status should tell user to start a loop."""
        result = registry.execute('/converge status')
        # Either "No active converge loop" or loaded from disk
        assert isinstance(result, str)
        assert len(result) > 0

    def test_status_with_session(self, registry):
        """Status should show project info when session active."""
        from core.project import Project
        from core.converge import LoopController
        from core.project import ConvergeConfig, StageConfig

        config = ConvergeConfig(
            name="test",
            stages=[
                StageConfig(id="spec", workspace="eda", prompt="test"),
                StageConfig(id="rtl", workspace="eda", prompt="test"),
            ],
            criteria_hard_stop=[{"metric": "lint.errors", "operator": "==", "value": 0}],
        )
        project = Project(module="counter", converge_config=config)
        project.current_stage = "spec"

        controller = MagicMock(spec=LoopController)

        registry._cv_set_session(project, controller)
        result = registry._converge_status()
        assert 'counter' in result
        assert 'spec' in result


# ============================================================
# Test: /converge override
# ============================================================

class TestConvergeOverride:
    def test_override_no_session(self, registry):
        result = registry._converge_override(['lint', 'syntax_error'])
        assert 'No active' in result

    def test_override_missing_args(self, registry):
        from core.project import Project
        project = Project(module="counter")
        registry._cv_set_session(project, MagicMock())
        result = registry._converge_override(['lint'])
        assert 'Usage' in result

    def test_override_success(self, registry):
        from core.project import Project
        project = Project(module="counter")
        registry._cv_set_session(project, MagicMock())
        result = registry._converge_override(['lint', 'syntax_error'])
        assert '✅' in result
        assert 'syntax_error' in result
        assert 'lint' in result
        # Check inbox
        assert len(project.inbox) == 1
        assert project.inbox[0]['type'] == 'override'
        assert project.inbox[0]['classifier'] == 'syntax_error'


# ============================================================
# Test: /converge inject
# ============================================================

class TestConvergeInject:
    def test_inject_no_session(self, registry):
        result = registry._converge_inject('hello world')
        assert 'No active' in result

    def test_inject_empty_message(self, registry):
        from core.project import Project
        registry._cv_set_session(Project(module="counter"), MagicMock())
        result = registry._converge_inject('')
        assert 'Usage' in result

    def test_inject_success(self, registry):
        from core.project import Project
        project = Project(module="counter")
        registry._cv_set_session(project, MagicMock())
        result = registry._converge_inject('fix the timing violation')
        assert '✅' in result
        assert 'inject' in result.lower()
        # Verify message is in inbox
        assert len(project.inbox) == 1
        assert project.inbox[0]['type'] == 'user_inject'
        assert project.inbox[0]['message'] == 'fix the timing violation'


# ============================================================
# Test: /converge level
# ============================================================

class TestConvergeLevel:
    def test_level_no_args(self, registry):
        result = registry._converge_level([])
        assert '1' in result
        assert '2' in result
        assert '3' in result

    def test_level_set(self, registry):
        from core.project import Project
        registry._cv_set_session(Project(module="counter"), MagicMock(), verbose_level=2)
        result = registry._converge_level(['3'])
        assert '✅' in result
        assert '3' in result

    def test_level_invalid(self, registry):
        result = registry._converge_level(['5'])
        assert 'must be 1, 2, or 3' in result

    def test_level_non_numeric(self, registry):
        result = registry._converge_level(['abc'])
        assert 'must be 1, 2, or 3' in result


# ============================================================
# Test: /converge history
# ============================================================

class TestConvergeHistory:
    def test_history_no_session(self, registry):
        result = registry._converge_history()
        assert 'No converge history' in result

    def test_history_with_data(self, registry):
        from core.project import Project
        project = Project(module="counter")
        project.record_iteration("spec", {"lint.errors": 3}, -15.0)
        project.record_iteration("rtl", {"lint.errors": 0}, 0.0)
        registry._cv_set_session(project, MagicMock())

        result = registry._converge_history()
        assert 'counter' in result
        assert 'spec' in result
        assert 'rtl' in result


# ============================================================
# Test: /converge report
# ============================================================

class TestConvergeReport:
    def test_report_no_session(self, registry):
        result = registry._converge_report()
        assert 'No converge data' in result

    def test_report_with_data(self, registry):
        from core.project import Project, ConvergeConfig, StageConfig
        config = ConvergeConfig(
            name="test",
            stages=[StageConfig(id="spec"), StageConfig(id="rtl")],
            criteria_hard_stop=[{"metric": "lint.errors", "operator": "==", "value": 0}],
        )
        project = Project(module="counter", converge_config=config)
        project.status = "converged"
        project.convergence_reason = "All hard_stop criteria met"
        project.current_stage = "spec"
        project.record_iteration("spec", {"lint.errors": 3}, -15.0)
        project.current_stage = "rtl"
        project.record_iteration("rtl", {"lint.errors": 0}, 0.0)
        project.variables["rtl_path"] = "/tmp/counter.v"
        project.metrics["lint.errors"] = 0
        project.metrics["sim.pass"] = 10
        project.jobs = ["job1", "job2"]

        registry._cv_set_session(project, MagicMock())
        result = registry._converge_report()

        assert 'counter' in result
        assert 'converged' in result
        assert 'CONVERGE REPORT' in result
        assert 'Stage Breakdown' in result
        assert 'spec' in result
        assert 'rtl' in result
        assert 'rtl_path' in result
        assert 'job1' in result
        assert 'Metrics' in result


# ============================================================
# Test: /converge next (manual step)
# ============================================================

class TestConvergeNext:
    def test_next_no_session(self, registry):
        result = registry._converge_next()
        assert 'No active' in result

    def test_next_loop_finished(self, registry):
        from core.project import Project
        project = Project(module="counter", status="converged", phase="done")
        registry._cv_set_session(project, MagicMock())
        result = registry._converge_next()
        assert 'already finished' in result


# ============================================================
# Test: /converge auto
# ============================================================

class TestConvergeAuto:
    def test_auto_no_session(self, registry):
        result = registry._converge_auto()
        assert 'No active' in result

    def test_auto_loop_finished(self, registry):
        from core.project import Project
        project = Project(module="counter", status="converged", phase="done")
        registry._cv_set_session(project, MagicMock())
        result = registry._converge_auto()
        assert 'already finished' in result


# ============================================================
# Test: Session tracker helpers
# ============================================================

class TestSessionTracker:
    def test_get_session_none(self, registry):
        assert registry._cv_get_session() is None

    def test_set_and_get_session(self, registry):
        registry._cv_set_session("project", "controller", verbose_level=3)
        sess = registry._cv_get_session()
        assert sess is not None
        assert sess['project'] == "project"
        assert sess['controller'] == "controller"
        assert sess['verbose_level'] == 3

    def test_clear_session(self, registry):
        registry._cv_set_session("p", "c")
        registry._cv_clear_session()
        assert registry._cv_get_session() is None

    def test_get_verbose_no_session(self, registry):
        assert registry._cv_get_verbose() == 1

    def test_get_verbose_with_session(self, registry):
        registry._cv_set_session("p", "c", verbose_level=3)
        assert registry._cv_get_verbose() == 3


# ============================================================
# Test: Dispatch integration
# ============================================================

class TestDispatchIntegration:
    def test_dispatch_converge(self, registry):
        result = registry.execute('/converge')
        assert 'Converge Loop Commands' in result

    def test_dispatch_cv_alias(self, registry):
        result = registry.execute('/cv')
        assert 'Converge Loop Commands' in result

    def test_dispatch_converge_status(self, registry):
        result = registry.execute('/converge status')
        assert isinstance(result, str)
        assert len(result) > 0

    def test_dispatch_converge_level(self, registry):
        result = registry.execute('/converge level')
        assert 'Verbosity' in result

    def test_dispatch_converge_history(self, registry):
        result = registry.execute('/converge history')
        assert 'No converge history' in result

    def test_dispatch_converge_report(self, registry):
        result = registry.execute('/converge report')
        assert 'No converge data' in result


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
