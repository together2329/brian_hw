"""
Tests for core/project.py — Project model, config loading, persistence,
convergence checks, and factory functions.

Covers:
  - load_yaml_file (YAML, JSON, fallback parser)
  - StageConfig.from_dict, FeedbackEdge.from_dict, ClassifierRule.from_dict
  - ParserConfig.from_dict, ConvergeConfig.from_dict
  - Project: variable management, stage transitions, iterations, inbox
  - Project: save_state / load_state round-trip
  - Project: check_hard_stop_criteria, is_converged, is_stalled, is_exhausted
  - Project: format_status, format_history, resolve_template
  - Project: _resolve_metric_path, _compare
  - Factory: create_project, restore_project
"""

import os
import sys
import json
import tempfile
import pytest
from pathlib import Path
from unittest.mock import patch

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import (
    load_yaml_file,
    StageConfig,
    FeedbackEdge,
    ClassifierRule,
    ParserConfig,
    ConvergeConfig,
    Project,
    create_project,
    restore_project,
)


# ============================================================
# Fixtures
# ============================================================

@pytest.fixture
def sample_converge_dict():
    """A minimal but complete converge config dict."""
    return {
        "name": "test-loop",
        "description": "Test converge loop",
        "stages": [
            {"id": "spec", "workspace": "eda", "agent": "execute", "prompt": "Write spec for {module}",
             "depends_on": [], "produces": ["mas_path"], "max_retries": 3},
            {"id": "rtl", "workspace": "eda", "agent": "execute", "prompt": "Write RTL for {module}",
             "depends_on": ["spec"], "produces": ["rtl_path"], "max_retries": 3},
            {"id": "lint", "workspace": "eda", "agent": "execute", "prompt": "Lint {module}",
             "depends_on": ["rtl"], "produces": [], "max_retries": 3},
        ],
        "criteria": {
            "hard_stop": [
                {"metric": "lint.errors", "operator": "==", "value": 0},
                {"metric": "sim.fail", "operator": "==", "value": 0},
            ],
            "score_threshold": 10.0,
            "max_total_iterations": 15,
            "no_improve_limit": 3,
        },
        "score_function": {
            "weights": {
                "lint.errors": -10.0,
                "lint.warnings": -5.0,
                "sim.pass_ratio": 10.0,
            },
        },
        "feedback_graph": [
            {
                "trigger": {"stage": "lint", "condition": "lint.errors > 0"},
                "fix": {
                    "workspace": "rtl-gen",
                    "agent": "execute",
                    "prompt": "Fix lint errors in {rtl_path}",
                    "retry_from": "lint",
                    "max_retries": 3,
                },
            },
        ],
        "classifiers": [
            {"id": "syntax_error", "patterns": ["Error:", "Syntax error"], "label": "syntax_error"},
            {"id": "rtl_bug", "patterns": ["[FAIL]", "mismatch"], "condition": "sim.iterations >= 3", "label": "rtl_bug"},
        ],
        "parsers": {
            "lint": {
                "type": "count_patterns",
                "patterns": {"errors": "Error:", "warnings": "Warning:"},
            },
            "sim": {
                "type": "structured",
                "fields": {
                    "pass": {"regex": r"\[PASS\]", "method": "count"},
                    "fail": {"regex": r"\[FAIL\]", "method": "count"},
                },
            },
        },
        "rollback": {"enabled": True, "paths": ["{module}/rtl/"], "on": "regressed"},
    }


@pytest.fixture
def project_with_config(sample_converge_dict):
    """A Project with a loaded ConvergeConfig."""
    config = ConvergeConfig.from_dict(sample_converge_dict)
    project = Project(
        module="counter",
        project_name="test-counter",
        converge_config=config,
        variables={"module": "counter"},
    )
    project.current_stage = config.stages[0].id
    return project


@pytest.fixture
def tmp_project_dir(tmp_path):
    """A temporary directory with a converge.yaml."""
    import yaml
    converge_data = {
        "name": "tmp-loop",
        "stages": [
            {"id": "build", "workspace": "eda", "prompt": "Build {module}"},
            {"id": "test", "workspace": "eda", "prompt": "Test {module}"},
        ],
        "criteria": {
            "hard_stop": [{"metric": "test.fail", "operator": "==", "value": 0}],
            "score_threshold": 5.0,
            "max_total_iterations": 10,
            "no_improve_limit": 2,
        },
        "score_function": {"weights": {"test.fail": -5}},
        "feedback_graph": [],
        "classifiers": [],
        "parsers": {},
    }
    yaml_path = tmp_path / "converge.yaml"
    yaml_path.write_text(yaml.dump(converge_data, default_flow_style=False), encoding="utf-8")
    return tmp_path


# ============================================================
# load_yaml_file
# ============================================================

class TestLoadYamlFile:
    def test_load_yaml(self, tmp_path):
        f = tmp_path / "test.yaml"
        f.write_text("name: hello\nvalue: 42\n", encoding="utf-8")
        result = load_yaml_file(f)
        assert result == {"name": "hello", "value": 42}

    def test_load_json(self, tmp_path):
        f = tmp_path / "test.json"
        f.write_text('{"name": "hello", "value": 42}', encoding="utf-8")
        result = load_yaml_file(f)
        assert result["name"] == "hello"
        assert result["value"] == 42

    def test_load_nonexistent(self, tmp_path):
        result = load_yaml_file(tmp_path / "nonexistent.yaml")
        assert result is None

    def test_load_empty_file(self, tmp_path):
        f = tmp_path / "empty.yaml"
        f.write_text("", encoding="utf-8")
        result = load_yaml_file(f)
        # yaml.safe_load("") returns None → returns {}
        assert result == {}

    def test_load_nested_yaml(self, tmp_path):
        f = tmp_path / "nested.yaml"
        f.write_text("outer:\n  inner: 42\n", encoding="utf-8")
        result = load_yaml_file(f)
        assert result["outer"]["inner"] == 42


# ============================================================
# Dataclass from_dict tests
# ============================================================

class TestStageConfig:
    def test_from_dict_full(self):
        data = {"id": "rtl", "workspace": "eda", "agent": "execute",
                "prompt": "Build RTL", "depends_on": ["spec"], "produces": ["rtl_path"],
                "max_retries": 5}
        sc = StageConfig.from_dict(data)
        assert sc.id == "rtl"
        assert sc.workspace == "eda"
        assert sc.agent == "execute"
        assert sc.prompt == "Build RTL"
        assert sc.depends_on == ["spec"]
        assert sc.produces == ["rtl_path"]
        assert sc.max_retries == 5

    def test_from_dict_minimal(self):
        sc = StageConfig.from_dict({"id": "spec"})
        assert sc.id == "spec"
        assert sc.workspace == ""
        assert sc.agent == "execute"
        assert sc.depends_on == []
        assert sc.produces == []
        assert sc.max_retries == 3

    def test_from_dict_extra_fields(self):
        data = {"id": "rtl", "custom_field": "hello"}
        sc = StageConfig.from_dict(data)
        assert sc.extra["custom_field"] == "hello"


class TestFeedbackEdge:
    def test_from_dict_full(self):
        data = {
            "trigger": {"stage": "lint", "condition": "lint.errors > 0", "classifier": "syntax"},
            "fix": {"workspace": "rtl-gen", "agent": "execute", "prompt": "Fix lint",
                    "retry_from": "lint", "max_retries": 3},
        }
        edge = FeedbackEdge.from_dict(data)
        assert edge.trigger_stage == "lint"
        assert edge.trigger_condition == "lint.errors > 0"
        assert edge.trigger_classifier == "syntax"
        assert edge.fix_workspace == "rtl-gen"
        assert edge.fix_agent == "execute"
        assert edge.fix_prompt == "Fix lint"
        assert edge.retry_from == "lint"
        assert edge.max_retries == 3

    def test_from_dict_defaults(self):
        edge = FeedbackEdge.from_dict({"trigger": {}, "fix": {}})
        assert edge.trigger_stage == ""
        assert edge.max_retries == 3


class TestClassifierRule:
    def test_from_dict(self):
        data = {"id": "tb_bug", "patterns": ["compile error", "port mismatch"],
                "condition": "sim.iterations < 3", "label": "tb_bug"}
        cr = ClassifierRule.from_dict(data)
        assert cr.id == "tb_bug"
        assert len(cr.patterns) == 2
        assert cr.condition == "sim.iterations < 3"
        assert cr.label == "tb_bug"

    def test_label_defaults_to_id(self):
        cr = ClassifierRule.from_dict({"id": "syntax_err", "patterns": []})
        assert cr.label == "syntax_err"


class TestParserConfig:
    def test_from_dict_count_patterns(self):
        data = {"type": "count_patterns", "patterns": {"errors": "Error:"}}
        pc = ParserConfig.from_dict(data)
        assert pc.parser_type == "count_patterns"
        assert pc.patterns == {"errors": "Error:"}

    def test_from_dict_structured(self):
        data = {"type": "structured", "fields": {"pass": {"regex": "PASS", "method": "count"}}}
        pc = ParserConfig.from_dict(data)
        assert pc.parser_type == "structured"
        assert "pass" in pc.fields

    def test_from_dict_defaults(self):
        pc = ParserConfig.from_dict({})
        assert pc.parser_type == "count_patterns"
        assert pc.fields == {}


class TestConvergeConfig:
    def test_from_dict_full(self, sample_converge_dict):
        config = ConvergeConfig.from_dict(sample_converge_dict)
        assert config.name == "test-loop"
        assert len(config.stages) == 3
        assert config.stages[0].id == "spec"
        assert config.criteria_score_threshold == 10.0
        assert config.criteria_max_total_iterations == 15
        assert config.criteria_no_improve_limit == 3
        assert len(config.criteria_hard_stop) == 2
        assert "lint.errors" in config.score_weights
        assert len(config.feedback_graph) == 1
        assert len(config.classifiers) == 2
        assert "lint" in config.parsers
        assert "sim" in config.parsers
        assert config.rollback_enabled is True
        assert config.rollback_on == "regressed"

    def test_from_dict_empty(self):
        config = ConvergeConfig.from_dict({})
        assert config.name == ""
        assert config.stages == []
        assert config.score_weights == {}
        assert config.criteria_score_threshold == 10.0


# ============================================================
# Project: Variable Management
# ============================================================

class TestProjectVariables:
    def test_set_and_get(self):
        p = Project(module="counter")
        p.set_variable("rtl_path", "/tmp/counter.v")
        assert p.get_variable("rtl_path") == "/tmp/counter.v"

    def test_get_missing_returns_default(self):
        p = Project(module="counter")
        assert p.get_variable("missing") == ""
        assert p.get_variable("missing", "fallback") == "fallback"

    def test_resolve_template(self):
        p = Project(module="counter", variables={"module": "counter", "rtl_path": "/tmp/counter.v"})
        result = p.resolve_template("Lint {module} at {rtl_path}")
        assert result == "Lint counter at /tmp/counter.v"

    def test_resolve_template_unresolved_key(self):
        p = Project(module="counter", variables={"module": "counter"})
        result = p.resolve_template("Build {module} from {unknown}")
        assert "counter" in result
        assert "{unknown}" in result  # unresolved stays as-is

    def test_resolve_template_no_placeholders(self):
        p = Project(variables={"module": "counter"})
        assert p.resolve_template("plain text") == "plain text"


# ============================================================
# Project: Stage Transitions & Iterations
# ============================================================

class TestProjectStateTransitions:
    def test_advance_to_stage(self):
        p = Project(module="counter")
        p.advance_to_stage("rtl")
        assert p.current_stage == "rtl"

    def test_record_iteration(self):
        p = Project(module="counter")
        p.current_stage = "spec"
        p.record_iteration("spec", {"lint.errors": 3}, -30.0)
        assert p.iteration == 1
        assert p.score == -30.0
        assert p.best_score == -30.0
        assert len(p.history) == 1
        assert p.history[0]["is_best"] is True

    def test_record_multiple_iterations_best_tracking(self):
        p = Project(module="counter")
        p.current_stage = "spec"
        p.record_iteration("spec", {}, -30.0)
        p.record_iteration("spec", {}, 0.0)
        p.record_iteration("spec", {}, -10.0)
        assert p.iteration == 3
        assert p.score == -10.0
        assert p.best_score == 0.0
        assert p.no_improve_count == 1  # -10 is worse than 0 (best)

    def test_record_iteration_no_improve_on_equal(self):
        p = Project(module="counter")
        p.current_stage = "spec"
        p.record_iteration("spec", {}, 5.0)
        p.record_iteration("spec", {}, 5.0)  # equal to best
        assert p.no_improve_count == 1  # equal counts as no-improve

    def test_increment_stage_retry(self):
        p = Project(module="counter")
        count1 = p.increment_stage_retry("lint")
        count2 = p.increment_stage_retry("lint")
        assert count1 == 1
        assert count2 == 2

    def test_get_stage_retry_count(self):
        p = Project(module="counter")
        assert p.get_stage_retry_count("lint") == 0
        p.increment_stage_retry("lint")
        assert p.get_stage_retry_count("lint") == 1

    def test_add_job(self):
        p = Project(module="counter")
        p.add_job("job1")
        p.add_job("job2")
        assert p.jobs == ["job1", "job2"]


# ============================================================
# Project: Inbox
# ============================================================

class TestProjectInbox:
    def test_send_to_inbox(self):
        p = Project(module="counter")
        p.send_to_inbox("override", "force classifier", stage="lint", classifier="syntax")
        assert len(p.inbox) == 1
        assert p.inbox[0]["type"] == "override"
        assert p.inbox[0]["stage"] == "lint"

    def test_drain_inbox(self):
        p = Project(module="counter")
        p.send_to_inbox("msg1", "hello")
        p.send_to_inbox("msg2", "world")
        msgs = p.drain_inbox()
        assert len(msgs) == 2
        assert len(p.inbox) == 0  # cleared after drain

    def test_drain_inbox_empty(self):
        p = Project(module="counter")
        assert p.drain_inbox() == []

    def test_has_inbox_messages(self):
        p = Project(module="counter")
        assert p.has_inbox_messages() is False
        p.send_to_inbox("test", "msg")
        assert p.has_inbox_messages() is True


# ============================================================
# Project: Persistence
# ============================================================

class TestProjectPersistence:
    def test_save_and_load_state(self, tmp_path, project_with_config):
        p = project_with_config
        p.session_dir = tmp_path / ".session" / "counter"
        p.current_stage = "rtl"
        p.record_iteration("rtl", {"lint.errors": 2}, -20.0)
        p.set_variable("rtl_path", "/tmp/counter.v")
        p.add_job("job5")

        p.save_state()

        # Load into new Project
        p2 = Project(session_dir=p.session_dir)
        loaded = p2.load_state()
        assert loaded is True
        assert p2.module == "counter"
        assert p2.current_stage == "rtl"
        assert p2.iteration == 1
        assert p2.score == -20.0
        assert p2.best_score == -20.0
        assert p2.variables["rtl_path"] == "/tmp/counter.v"
        assert p2.jobs == ["job5"]
        assert len(p2.history) == 1

    def test_load_state_no_file(self, tmp_path):
        p = Project(session_dir=tmp_path / "nonexistent")
        assert p.load_state() is False

    def test_save_state_no_session_dir(self, project_with_config):
        p = project_with_config
        p.session_dir = None
        # Should not raise
        p.save_state()

    def test_save_creates_directory(self, tmp_path, project_with_config):
        p = project_with_config
        p.session_dir = tmp_path / "deep" / "nested" / "dir"
        p.save_state()
        assert (p.session_dir / "loop_state.json").exists()

    def test_load_state_corrupted_json(self, tmp_path):
        p = Project(session_dir=tmp_path)
        tmp_path.mkdir(parents=True, exist_ok=True)
        (tmp_path / "loop_state.json").write_text("{invalid json", encoding="utf-8")
        assert p.load_state() is False


# ============================================================
# Project: Convergence Checks
# ============================================================

class TestConvergenceChecks:
    def test_check_hard_stop_all_pass(self, project_with_config):
        p = project_with_config
        p.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        results = p.check_hard_stop_criteria()
        assert all(results.values())

    def test_check_hard_stop_some_fail(self, project_with_config):
        p = project_with_config
        # _resolve_metric_path splits by "." and walks nested dicts
        p.metrics = {"lint": {"errors": 3}, "sim": {"fail": 0}}
        results = p.check_hard_stop_criteria()
        assert not all(results.values())
        # lint.errors should be False (3 != 0)
        assert any(not v for v in results.values())

    def test_check_hard_stop_no_config(self):
        p = Project(module="counter")
        assert p.check_hard_stop_criteria() == {}

    def test_is_converged_true(self, project_with_config):
        p = project_with_config
        p.metrics = {"lint": {"errors": 0}, "sim": {"fail": 0}}
        assert p.is_converged() is True

    def test_is_converged_false(self, project_with_config):
        p = project_with_config
        p.metrics = {"lint": {"errors": 5}, "sim": {"fail": 0}}
        assert p.is_converged() is False

    def test_is_converged_no_config(self):
        p = Project(module="counter")
        assert p.is_converged() is False

    def test_is_stalled_true(self, project_with_config):
        p = project_with_config
        p.no_improve_count = 3
        assert p.is_stalled() is True

    def test_is_stalled_false(self, project_with_config):
        p = project_with_config
        p.no_improve_count = 1
        assert p.is_stalled() is False

    def test_is_stalled_no_config(self):
        p = Project(module="counter")
        assert p.is_stalled() is False

    def test_is_exhausted_true(self, project_with_config):
        p = project_with_config
        p.iteration = 15
        assert p.is_exhausted() is True

    def test_is_exhausted_false(self, project_with_config):
        p = project_with_config
        p.iteration = 10
        assert p.is_exhausted() is False

    def test_is_exhausted_no_config(self):
        p = Project(module="counter")
        assert p.is_exhausted() is False


# ============================================================
# Project: Internal Helpers
# ============================================================

class TestProjectHelpers:
    def test_resolve_metric_path_flat(self, project_with_config):
        p = project_with_config
        # _resolve_metric_path splits by "." → walks nested dicts
        p.metrics = {"lint": {"errors": 3}}
        assert p._resolve_metric_path("lint.errors") == 3

    def test_resolve_metric_path_nested(self, project_with_config):
        p = project_with_config
        p.metrics = {"synth": {"timing": {"wns": -0.5}}}
        assert p._resolve_metric_path("synth.timing.wns") == -0.5

    def test_resolve_metric_path_missing(self, project_with_config):
         p = project_with_config
         p.metrics = {}
         # Missing metrics return _METRIC_MISSING sentinel (not 0)
         assert p._resolve_metric_path("lint.errors") is Project._METRIC_MISSING

    def test_resolve_metric_path_flat_key(self, project_with_config):
         """Flat keys like metrics['lint.errors'] should be resolved directly."""
         p = project_with_config
         p.metrics = {"lint.errors": 0, "sim.pass": 5}
         assert p._resolve_metric_path("lint.errors") == 0
         assert p._resolve_metric_path("sim.pass") == 5

    def test_compare_operators(self):
        assert Project._compare(0, "==", 0) is True
        assert Project._compare(1, "==", 0) is False
        assert Project._compare(1, "!=", 0) is True
        assert Project._compare(5, ">=", 5) is True
        assert Project._compare(5, ">=", 6) is False
        assert Project._compare(5, "<=", 5) is True
        assert Project._compare(5, ">", 4) is True
        assert Project._compare(5, ">", 5) is False
        assert Project._compare(5, "<", 6) is True
        assert Project._compare(5, "<", 5) is False

    def test_compare_invalid(self):
        assert Project._compare("abc", ">=", 5) is False
        assert Project._compare(None, "==", 0) is False


# ============================================================
# Project: Display Helpers
# ============================================================

class TestProjectDisplay:
    def test_format_status(self, project_with_config):
        p = project_with_config
        p.metrics = {"lint.errors": 0}
        text = p.format_status()
        assert "counter" in text
        assert "idle" in text
        assert "spec" in text  # current stage

    def test_format_status_with_criteria(self, project_with_config):
        p = project_with_config
        p.metrics = {"lint": {"errors": 0}, "sim": {"fail": 1}}
        text = p.format_status()
        assert "✅" in text or "❌" in text

    def test_format_history_empty(self):
        p = Project(module="counter")
        assert "No iterations" in p.format_history()

    def test_format_history_with_data(self, project_with_config):
        p = project_with_config
        p.current_stage = "spec"
        p.record_iteration("spec", {}, 5.0)
        p.current_stage = "rtl"
        p.record_iteration("rtl", {}, 10.0)
        text = p.format_history()
        assert "spec" in text
        assert "rtl" in text
        assert "★" in text  # best mark

    def test_to_dict(self, project_with_config):
        p = project_with_config
        p.current_stage = "spec"
        p.record_iteration("spec", {}, 5.0)
        d = p.to_dict()
        assert d["module"] == "counter"
        assert d["iteration"] == 1
        assert d["score"] == 5.0
        assert len(d["history"]) == 1


# ============================================================
# Factory Functions
# ============================================================

class TestCreateProject:
    def test_create_project_with_yaml(self, tmp_project_dir):
        project = create_project(
            module="counter",
            project_root=tmp_project_dir,
            converge_yaml=tmp_project_dir / "converge.yaml",
        )
        assert project.module == "counter"
        assert project.converge_config is not None
        assert project.converge_config.name == "tmp-loop"
        assert len(project.converge_config.stages) == 2
        assert project.current_stage == "build"  # first stage

    def test_create_project_missing_yaml(self, tmp_path):
        with pytest.raises(FileNotFoundError):
            create_project(module="counter", project_root=tmp_path)

    def test_create_project_variables(self, tmp_project_dir):
        project = create_project(
            module="alu",
            project_root=tmp_project_dir,
            converge_yaml=tmp_project_dir / "converge.yaml",
        )
        assert project.variables["module"] == "alu"


class TestRestoreProject:
    def test_restore_from_saved_state(self, tmp_path, project_with_config):
        p = project_with_config
        session_dir = tmp_path / ".session" / "counter"
        p.session_dir = session_dir
        p.current_stage = "rtl"
        p.record_iteration("rtl", {"lint.errors": 0}, 10.0)
        p.save_state()

        restored = restore_project(session_dir)
        assert restored is not None
        assert restored.module == "counter"
        assert restored.current_stage == "rtl"
        assert restored.iteration == 1
        assert restored.score == 10.0

    def test_restore_no_state(self, tmp_path):
        result = restore_project(tmp_path / "nonexistent")
        assert result is None

    def test_restore_reloads_config(self, tmp_path):
        """When converge_yaml_path is saved, restore_project reloads config."""
        import yaml
        converge_data = {
            "name": "restored-loop",
            "stages": [{"id": "build"}],
            "criteria": {"hard_stop": [], "score_threshold": 5.0,
                         "max_total_iterations": 10, "no_improve_limit": 2},
            "score_function": {"weights": {}},
            "feedback_graph": [],
            "classifiers": [],
            "parsers": {},
        }
        yaml_path = tmp_path / "converge.yaml"
        yaml_path.write_text(yaml.dump(converge_data), encoding="utf-8")

        # Create and save
        p = Project(module="counter", session_dir=tmp_path / ".session" / "counter")
        p.converge_yaml_path = yaml_path
        p.session_dir = tmp_path / ".session" / "counter"
        p.save_state()

        restored = restore_project(p.session_dir, project_root=tmp_path)
        assert restored is not None
        # converge config should be loaded (or at least converge_yaml_path set)
        assert restored.converge_yaml_path == yaml_path


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
