"""
Tests for core/converge.py — ScoreCalculator, OutputParser, ClassifierEngine,
FeedbackRouter, LoopController, and run_converge_loop.

Covers:
  - ScoreCalculator.compute (weights, ratios, has_failures, flat/nested metrics)
  - ScoreCalculator._flatten, _compute_ratio
  - OutputParser.parse (count_patterns, structured, regex_groups, edge cases)
  - OutputParser._cast
  - ClassifierEngine.classify (pattern match, condition eval, priority ordering)
  - ClassifierEngine._eval_condition (all operators)
  - FeedbackRouter.lookup (exact classifier, condition, catch-all, no-match)
  - LoopController.run with mocked agent_runner (happy path, feedback loop)
  - run_converge_loop convenience function
"""

import os
import sys
import json
import pytest
from pathlib import Path
from unittest.mock import patch, MagicMock
from dataclasses import dataclass

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.converge import (
    ScoreCalculator,
    OutputParser,
    ClassifierEngine,
    FeedbackRouter,
    LoopController,
    run_converge_loop,
)
from core.project import (
    Project,
    ConvergeConfig,
    StageConfig,
    FeedbackEdge,
    ClassifierRule,
    ParserConfig,
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
        criteria_max_total_iterations=overrides.pop("criteria_max_total_iterations", 5),
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
# ScoreCalculator
# ============================================================

class TestScoreCalculator:
    def test_simple_weights(self):
        sc = ScoreCalculator({"lint.errors": -5, "sim.pass": 2})
        metrics = {"lint": {"errors": 3}, "sim": {"pass": 5}}
        score = sc.compute(metrics)
        assert score == 3 * (-5) + 5 * 2  # -15 + 10 = -5

    def test_zero_metrics(self):
        sc = ScoreCalculator({"lint.errors": -5})
        assert sc.compute({}) == 0.0

    def test_empty_weights(self):
        sc = ScoreCalculator({})
        assert sc.compute({"lint": {"errors": 3}}) == 0.0

    def test_flat_metrics(self):
        sc = ScoreCalculator({"lint.errors": -5})
        metrics = {"lint.errors": 3}
        # _flatten turns {"lint.errors": 3} → {"lint.errors": 3}
        score = sc.compute(metrics)
        assert score == -15.0

    def test_nested_metrics(self):
        sc = ScoreCalculator({"lint.errors": -5})
        metrics = {"lint": {"errors": 4}}
        score = sc.compute(metrics)
        assert score == -20.0

    def test_deeply_nested(self):
        sc = ScoreCalculator({"synth.timing.wns": 10})
        metrics = {"synth": {"timing": {"wns": -0.5}}}
        score = sc.compute(metrics)
        assert score == -5.0

    def test_has_failures_penalty(self):
        sc = ScoreCalculator({"sim.has_failures": -20})
        metrics = {"sim": {"fail": 2}}
        # "sim.has_failures" triggers the has_failures logic
        score = sc.compute(metrics)
        assert score == -20.0  # sim.fail > 0 → has_failures = 1

    def test_has_failures_zero(self):
        sc = ScoreCalculator({"sim.has_failures": -20})
        metrics = {"sim": {"fail": 0}}
        score = sc.compute(metrics)
        assert score == 0.0  # sim.fail = 0 → has_failures = 0

    def test_has_errors_penalty(self):
        sc = ScoreCalculator({"sim.has_errors": -10})
        metrics = {"sim": {"errors": 1}}
        score = sc.compute(metrics)
        assert score == -10.0

    def test_ratio_weight(self):
        sc = ScoreCalculator({"sim.pass_ratio": 10})
        metrics = {"sim": {"pass": 8, "fail": 2, "tests": 10}}
        score = sc.compute(metrics)
        assert score == pytest.approx(8.0, abs=0.1)  # 8/10 * 10

    def test_ratio_zero_total(self):
        sc = ScoreCalculator({"sim.pass_ratio": 10})
        metrics = {"sim": {"pass": 0, "fail": 0, "tests": 0}}
        score = sc.compute(metrics)
        assert score == 0.0

    def test_multiple_weights(self):
        sc = ScoreCalculator({
            "lint.errors": -10,
            "lint.warnings": -2,
            "sim.pass": 3,
        })
        metrics = {
            "lint": {"errors": 2, "warnings": 4},
            "sim": {"pass": 6},
        }
        score = sc.compute(metrics)
        assert score == 2 * (-10) + 4 * (-2) + 6 * 3  # -20 - 8 + 18 = -10

    def test_flatten(self):
        out = {}
        ScoreCalculator._flatten({"a": {"b": {"c": 1}, "d": 2}, "e": 3}, out)
        assert out == {"a.b.c": 1, "a.d": 2, "e": 3}


# ============================================================
# OutputParser
# ============================================================

class TestOutputParser:
    def test_count_patterns(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "count_patterns"
        config.patterns = {
            "errors": r"Error:",
            "warnings": r"Warning:",
        }
        output = "Error: line 5\nWarning: unused var\nError: line 10\nOK"
        result = parser.parse(output, config)
        assert result["errors"] == 2
        assert result["warnings"] == 1

    def test_count_patterns_no_matches(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "count_patterns"
        config.patterns = {"errors": r"Error:"}
        result = parser.parse("All clean", config)
        assert result["errors"] == 0

    def test_count_patterns_invalid_regex(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "count_patterns"
        config.patterns = {"bad": r"[invalid"}
        result = parser.parse("some text", config)
        assert result["bad"] == 0

    def test_structured_count(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "pass": {"regex": r"\[PASS\]", "method": "count"},
            "fail": {"regex": r"\[FAIL\]", "method": "count"},
        }
        output = "[PASS] test1\n[PASS] test2\n[FAIL] test3"
        result = parser.parse(output, config)
        assert result["pass"] == 2
        assert result["fail"] == 1

    def test_structured_extract(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "module_name": {"regex": r"Module:\s*(\S+)", "method": "extract"},
        }
        result = parser.parse("Module: counter_top", config)
        assert result["module_name"] == "counter_top"

    def test_structured_extract_no_match(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "module_name": {"regex": r"Module:\s*(\S+)", "method": "extract"},
        }
        result = parser.parse("No module here", config)
        assert result["module_name"] == ""

    def test_structured_extract_all(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "fail_tests": {"regex": r"\[FAIL\]\s*(.+)", "method": "extract_all"},
        }
        output = "[FAIL] test_reset\n[FAIL] test_overflow"
        result = parser.parse(output, config)
        assert result["fail_tests"] == ["test_reset", "test_overflow"]

    def test_structured_first(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "first_error": {"regex": r"Error:.*", "method": "first"},
        }
        output = "Some text\nError: bad thing\nMore text"
        result = parser.parse(output, config)
        assert "Error: bad thing" in result["first_error"]

    def test_structured_simple_string_regex(self):
        """Field spec as a simple string (not dict) defaults to method=count."""
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "structured"
        config.fields = {
            "hits": r"PASS",
        }
        result = parser.parse("PASS PASS PASS", config)
        assert result["hits"] == 3

    def test_regex_groups(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "regex_groups"
        config.fields = {
            "wns": {"regex": r"WNS:\s*(-?\d+\.?\d*)", "cast": "float"},
            "area": {"regex": r"Area:\s*(\d+)", "cast": "int"},
            "name": {"regex": r"Module:\s*(\S+)", "cast": "str"},
        }
        output = "Module: counter\nWNS: -0.45\nArea: 1234"
        result = parser.parse(output, config)
        assert result["wns"] == -0.45
        assert result["area"] == 1234
        assert result["name"] == "counter"

    def test_regex_groups_no_match(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "regex_groups"
        config.fields = {
            "wns": {"regex": r"WNS:\s*(-?\d+\.?\d*)", "cast": "float"},
        }
        result = parser.parse("No WNS here", config)
        assert result["wns"] == 0.0  # cast default

    def test_regex_groups_string_spec(self):
        """Field spec as string (no dict) defaults to cast=str."""
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "regex_groups"
        config.fields = {
            "name": r"Module:\s*(\S+)",
        }
        result = parser.parse("Module: alu", config)
        assert result["name"] == "alu"

    def test_none_config(self):
        parser = OutputParser()
        assert parser.parse("output", None) == {}

    def test_unknown_parser_type(self):
        parser = OutputParser()
        config = MagicMock()
        config.parser_type = "unknown_type"
        assert parser.parse("output", config) == {}


# ============================================================
# OutputParser._cast
# ============================================================

class TestOutputParserCast:
    def test_cast_int(self):
        assert OutputParser._cast("42", "int") == 42

    def test_cast_int_from_float_str(self):
        assert OutputParser._cast("42.7", "int") == 42

    def test_cast_float(self):
        assert OutputParser._cast("3.14", "float") == 3.14

    def test_cast_str(self):
        assert OutputParser._cast("hello", "str") == "hello"

    def test_cast_invalid_int(self):
        assert OutputParser._cast("abc", "int") == 0

    def test_cast_invalid_float(self):
        assert OutputParser._cast("abc", "float") == 0

    def test_cast_invalid_str(self):
        assert OutputParser._cast("", "str") == ""


# ============================================================
# ClassifierEngine
# ============================================================

class TestClassifierEngine:
    def test_classify_match(self):
        rules = [ClassifierRule(id="tb_bug", patterns=["compile error", "port mismatch"],
                                label="tb_bug")]
        engine = ClassifierEngine(rules)
        assert engine.classify("There was a compile error in the testbench") == "tb_bug"

    def test_classify_case_insensitive(self):
        rules = [ClassifierRule(id="err", patterns=["error"], label="err")]
        engine = ClassifierEngine(rules)
        assert engine.classify("ERROR: bad thing") == "err"

    def test_classify_no_match(self):
        rules = [ClassifierRule(id="tb_bug", patterns=["compile error"], label="tb_bug")]
        engine = ClassifierEngine(rules)
        assert engine.classify("All tests passed") == ""

    def test_classify_first_match_wins(self):
        rules = [
            ClassifierRule(id="rule1", patterns=["error"], label="first"),
            ClassifierRule(id="rule2", patterns=["error"], label="second"),
        ]
        engine = ClassifierEngine(rules)
        assert engine.classify("An error occurred") == "first"

    def test_classify_with_condition_pass(self):
        rules = [
            ClassifierRule(id="early", patterns=["[fail]"],
                           condition="sim.iterations < 3", label="early_bug"),
        ]
        engine = ClassifierEngine(rules)
        assert engine.classify("[fail] test", {"sim.iterations": 1}) == "early_bug"

    def test_classify_with_condition_fail(self):
        rules = [
            ClassifierRule(id="late", patterns=["[fail]"],
                           condition="sim.iterations >= 3", label="late_bug"),
        ]
        engine = ClassifierEngine(rules)
        assert engine.classify("[fail] test", {"sim.iterations": 1}) == ""

    def test_classify_empty_rules(self):
        engine = ClassifierEngine([])
        assert engine.classify("anything") == ""

    def test_classify_multiple_patterns_any_match(self):
        rules = [
            ClassifierRule(id="multi", patterns=["timeout", "hang", "deadlock"],
                           label="hang"),
        ]
        engine = ClassifierEngine(rules)
        assert engine.classify("System deadlock detected") == "hang"


class TestClassifierEvalCondition:
    def test_greater_than(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("sim.iterations > 3", {"sim.iterations": 5}) is True
        assert engine._eval_condition("sim.iterations > 3", {"sim.iterations": 2}) is False

    def test_greater_equal(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x >= 5", {"x": 5}) is True
        assert engine._eval_condition("x >= 5", {"x": 4}) is False

    def test_less_than(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x < 3", {"x": 2}) is True
        assert engine._eval_condition("x < 3", {"x": 5}) is False

    def test_less_equal(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x <= 3", {"x": 3}) is True
        assert engine._eval_condition("x <= 3", {"x": 4}) is False

    def test_equals(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x == 5", {"x": 5}) is True
        assert engine._eval_condition("x == 5", {"x": 3}) is False

    def test_not_equals(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x != 5", {"x": 3}) is True
        assert engine._eval_condition("x != 5", {"x": 5}) is False

    def test_dot_to_underscore_fallback(self):
        engine = ClassifierEngine([])
        # "sim.iterations" → tries both "sim.iterations" and "sim_iterations"
        assert engine._eval_condition("sim.iterations < 3", {"sim_iterations": 1}) is True

    def test_no_operator_returns_true(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("no_operator_here", {}) is True

    def test_invalid_values(self):
        engine = ClassifierEngine([])
        assert engine._eval_condition("x > abc", {"x": "not_a_number"}) is False


# ============================================================
# FeedbackRouter
# ============================================================

class TestFeedbackRouter:
    def _make_edge(self, stage, classifier="", condition=""):
        return FeedbackEdge(
            trigger_stage=stage,
            trigger_classifier=classifier,
            trigger_condition=condition,
            fix_workspace="fix-ws",
            fix_agent="execute",
            fix_prompt="Fix it",
            retry_from=stage,
            max_retries=3,
        )

    def test_exact_classifier_match(self):
        edge = self._make_edge("sim", classifier="tb_bug")
        router = FeedbackRouter([edge])
        result = router.lookup("sim", "tb_bug")
        assert result is edge

    def test_classifier_no_match(self):
        edge = self._make_edge("sim", classifier="tb_bug")
        router = FeedbackRouter([edge])
        result = router.lookup("sim", "rtl_bug")
        assert result is None

    def test_condition_match(self):
        edge = self._make_edge("lint", condition="lint.errors > 0")
        router = FeedbackRouter([edge])
        result = router.lookup("lint", context={"lint.errors": 5})
        assert result is edge

    def test_condition_no_match(self):
        edge = self._make_edge("lint", condition="lint.errors > 0")
        router = FeedbackRouter([edge])
        result = router.lookup("lint", context={"lint.errors": 0})
        assert result is None

    def test_catch_all(self):
        edge = self._make_edge("sim")  # no classifier, no condition
        router = FeedbackRouter([edge])
        result = router.lookup("sim")
        assert result is edge

    def test_stage_mismatch(self):
        edge = self._make_edge("sim", classifier="tb_bug")
        router = FeedbackRouter([edge])
        result = router.lookup("lint", "tb_bug")
        assert result is None

    def test_empty_edges(self):
        router = FeedbackRouter([])
        assert router.lookup("sim") is None

    def test_priority_ordering(self):
        """Classifier match > condition match > catch-all."""
        catch_all = self._make_edge("sim")
        cond_edge = self._make_edge("sim", condition="sim.iterations > 0")
        cls_edge = self._make_edge("sim", classifier="tb_bug")
        router = FeedbackRouter([catch_all, cond_edge, cls_edge])

        # With classifier → classifier match
        result = router.lookup("sim", "tb_bug", {"sim.iterations": 5})
        assert result is cls_edge

        # No classifier, condition met → condition match
        result = router.lookup("sim", "", {"sim.iterations": 5})
        assert result is cond_edge

        # No classifier, condition not met → catch-all
        result = router.lookup("sim", "", {"sim.iterations": 0})
        assert result is catch_all


# ============================================================
# LoopController (with mocked agent_runner)
# ============================================================

class TestLoopController:
    def _make_controller(self, project=None):
        if project is None:
            project = _make_project_with_config()
        return LoopController(project, verbose=False)

    def test_init(self):
        ctrl = self._make_controller()
        assert ctrl.score_calc is not None
        assert ctrl.parser is not None
        assert ctrl.classifier is not None
        assert ctrl.router is not None
        assert len(ctrl._stage_ids) == 2

    def test_init_no_config_raises(self):
        with pytest.raises(ValueError, match="converge_config"):
            LoopController(Project(module="test"))

    @patch('core.agent_runner.run_agent_session')
    def test_run_all_stages_pass(self, mock_run):
        """Happy path: all stages execute, no failures."""
        mock_result = MagicMock()
        mock_result.output = "All clean"
        mock_result.raw_output = "All clean"
        mock_result.tool_calls = []
        mock_run.return_value = mock_result

        project = _make_project_with_config(
            score_weights={"lint.errors": -5},
        )
        # Start with non-zero errors so convergence check fails initially
        project.metrics = {"lint": {"errors": 99}}
        ctrl = LoopController(project, verbose=False)
        result = ctrl.run()

        assert result.status in ("converged", "failed")
        assert result.phase == "done"
        assert result.iteration >= 1  # at least lint stage ran

    @patch('core.agent_runner.run_agent_session')
    def test_run_tracks_history(self, mock_run):
        """Each stage execution should be recorded in history."""
        mock_result = MagicMock()
        mock_result.output = "OK"
        mock_result.raw_output = "OK"
        mock_result.tool_calls = []
        mock_run.return_value = mock_result

        project = _make_project_with_config()
        project.metrics = {"lint": {"errors": 99}}
        ctrl = LoopController(project, verbose=False)
        ctrl.run()

        assert len(project.history) >= 1

    @patch('core.agent_runner.run_agent_session')
    def test_run_max_iterations(self, mock_run):
        """Should stop when max iterations reached."""
        mock_result = MagicMock()
        mock_result.output = "Error: bad"
        mock_result.raw_output = "Error: bad"
        mock_result.tool_calls = []
        mock_run.return_value = mock_result

        project = _make_project_with_config(
            criteria_max_total_iterations=2,
            feedback_graph=[],
        )
        project.metrics = {"lint": {"errors": 99}}
        ctrl = LoopController(project, verbose=False)
        result = ctrl.run()
        assert result.phase == "done"

    @patch('core.agent_runner.run_agent_session')
    def test_run_saves_state(self, mock_run, tmp_path):
        """Controller should save state after each iteration."""
        mock_result = MagicMock()
        mock_result.output = "OK"
        mock_result.raw_output = "OK"
        mock_result.tool_calls = []
        mock_run.return_value = mock_result

        project = _make_project_with_config()
        project.session_dir = tmp_path / ".session" / "test"
        ctrl = LoopController(project, verbose=False)
        ctrl.run()

        assert (project.session_dir / "loop_state.json").exists()

    def test_is_stage_failed(self):
        """_is_stage_failed detects error/fail metrics."""
        project = _make_project_with_config()
        ctrl = self._make_controller(project)

        assert ctrl._is_stage_failed("lint", {"errors": 3}) is True
        assert ctrl._is_stage_failed("lint", {"errors": 0}) is False
        assert ctrl._is_stage_failed("sim", {"fail": 1}) is True
        assert ctrl._is_stage_failed("sim", {"fail": 0}) is False

    def test_build_classifier_context(self):
        project = _make_project_with_config()
        project.iteration = 5
        project.score = 10.0
        project.stage_iterations = {"lint": 2}
        ctrl = self._make_controller(project)

        ctx = ctrl._build_classifier_context("lint")
        assert ctx["iteration"] == 5
        assert ctx["score"] == 10.0
        assert ctx["stage.retry"] == 2
        assert ctx["lint.iterations"] == 2

    @patch('core.agent_runner.run_agent_session')
    def test_run_keyboard_interrupt(self, mock_run):
        """Ctrl+C should set status to failed — KeyboardInterrupt bypasses _execute_stage's except."""
        mock_run.side_effect = KeyboardInterrupt()
        project = _make_project_with_config()
        project.metrics = {"lint": {"errors": 99}}
        ctrl = LoopController(project, verbose=False)
        result = ctrl.run()
        assert result.status == "failed"
        assert "Interrupted" in result.convergence_reason

    def test_run_exception_in_init(self):
        """If project has no config, LoopController.__init__ raises."""
        with pytest.raises(ValueError):
            LoopController(Project(module="test"), verbose=False)

    def test_extract_produced_variables(self):
        """_extract_produced_variables finds paths in output."""
        project = _make_project_with_config()
        ctrl = self._make_controller(project)

        ctrl._extract_produced_variables(
            ["rtl_path"],
            "Created: /tmp/counter.sv\nDone"
        )
        assert project.get_variable("rtl_path") == "/tmp/counter.sv"

    def test_extract_produced_variables_output_pattern(self):
        project = _make_project_with_config()
        ctrl = self._make_controller(project)

        ctrl._extract_produced_variables(
            ["rtl_path"],
            "Output: /home/user/rtl/counter.v"
        )
        assert project.get_variable("rtl_path") == "/home/user/rtl/counter.v"


# ============================================================
# run_converge_loop convenience
# ============================================================

class TestRunConvergeLoop:
    @patch('core.converge.LoopController')
    @patch('core.project.create_project')
    def test_creates_project_and_runs(self, mock_create, mock_ctrl_cls):
        mock_project = MagicMock()
        mock_create.return_value = mock_project
        mock_ctrl = MagicMock()
        mock_ctrl.run.return_value = mock_project
        mock_ctrl_cls.return_value = mock_ctrl

        result = run_converge_loop(module="counter")

        mock_create.assert_called_once()
        mock_ctrl_cls.assert_called_once_with(mock_project, verbose=False)
        mock_ctrl.run.assert_called_once()
        assert result == mock_project

    @patch('core.converge.LoopController')
    @patch('core.project.create_project')
    def test_passes_yaml_path(self, mock_create, mock_ctrl_cls):
        mock_project = MagicMock()
        mock_create.return_value = mock_project
        mock_ctrl = MagicMock()
        mock_ctrl.run.return_value = mock_project
        mock_ctrl_cls.return_value = mock_ctrl

        yaml_path = Path("/tmp/converge.yaml")
        run_converge_loop(module="counter", converge_yaml=yaml_path)

        _, kwargs = mock_create.call_args
        assert kwargs.get('converge_yaml') == yaml_path


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
