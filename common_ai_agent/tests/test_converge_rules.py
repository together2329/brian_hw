"""
Tests for core/converge_rules.py — RuleResult, ConvergeRule, ConvergeRules,
and built-in rules.

Covers:
  - RuleResult.is_noop
  - ConvergeRule.evaluate (callable, expr string, priority)
  - ConvergeRule._eval_expr (all comparison operators, dot-path)
  - ConvergeRule._resolve_path
  - ConvergeRule.from_dict
  - ConvergeRules: add_callable, add_expr_rule, load_from_dir (JSON/Python)
  - ConvergeRules.evaluate (priority ordering, no match)
  - ConvergeRules.list_rules, _flatten
  - Built-in rules: rule_abort_on_max_iterations, rule_skip_stage_on_zero_metrics
  - register_builtin_rules
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.converge_rules import (
    RuleResult,
    ConvergeRule,
    ConvergeRules,
    rule_abort_on_max_iterations,
    rule_skip_stage_on_zero_metrics,
    register_builtin_rules,
)


# ============================================================
# RuleResult
# ============================================================

class TestRuleResult:
    def test_is_noop_empty(self):
        r = RuleResult()
        assert r.is_noop() is True

    def test_is_noop_with_action(self):
        r = RuleResult(action="skip_stage")
        assert r.is_noop() is False

    def test_fields(self):
        r = RuleResult(action="override_classifier", target="rtl_bug",
                       reason="Better alternative", priority=10)
        assert r.action == "override_classifier"
        assert r.target == "rtl_bug"
        assert r.reason == "Better alternative"
        assert r.priority == 10


# ============================================================
# ConvergeRule: evaluate with callable
# ============================================================

class TestConvergeRuleCallable:
    def test_callable_match(self):
        def my_rule(ctx):
            if ctx.get("score", 0) < 0:
                return RuleResult(action="abort", reason="Negative score")
            return None

        rule = ConvergeRule(name="test", condition_fn=my_rule)
        result = rule.evaluate({"score": -5})
        assert result is not None
        assert result.action == "abort"

    def test_callable_no_match(self):
        def my_rule(ctx):
            return None

        rule = ConvergeRule(name="test", condition_fn=my_rule)
        result = rule.evaluate({"score": 10})
        assert result is None

    def test_callable_exception_returns_none(self):
        def bad_rule(ctx):
            raise RuntimeError("boom")

        rule = ConvergeRule(name="test", condition_fn=bad_rule)
        result = rule.evaluate({})
        assert result is None


# ============================================================
# ConvergeRule: evaluate with expression
# ============================================================

class TestConvergeRuleExpr:
    def test_expr_greater_than(self):
        rule = ConvergeRule(name="test", condition_expr="metrics.lint.errors > 20",
                            action="skip_stage", reason_template="Too many errors",
                            priority=5)
        result = rule.evaluate({"metrics": {"lint": {"errors": 25}}})
        assert result is not None
        assert result.action == "skip_stage"
        assert result.priority == 5

    def test_expr_no_match(self):
        rule = ConvergeRule(name="test", condition_expr="metrics.lint.errors > 20",
                            action="skip_stage")
        result = rule.evaluate({"metrics": {"lint": {"errors": 5}}})
        assert result is None

    def test_expr_equality(self):
        rule = ConvergeRule(name="test", condition_expr="stage == lint",
                            action="skip_stage")
        result = rule.evaluate({"stage": "lint"})
        assert result is not None

    def test_expr_no_operator(self):
        rule = ConvergeRule(name="test", condition_expr="no_operator_here",
                            action="skip_stage")
        result = rule.evaluate({})
        assert result is None  # no operator → False

    def test_expr_invalid_values(self):
        rule = ConvergeRule(name="test", condition_expr="score > abc",
                            action="skip_stage")
        result = rule.evaluate({"score": "not_a_number"})
        assert result is None  # ValueError → False

    def test_reason_template_substitution(self):
        rule = ConvergeRule(name="test",
                            condition_expr="iteration >= 3",
                            action="inject_message",
                            reason_template="Stage {stage} has high iteration count")
        result = rule.evaluate({"stage": "sim", "iteration": 5,
                                "metrics_flat": {}})
        assert result is not None
        assert "sim" in result.reason

    def test_no_condition(self):
        rule = ConvergeRule(name="test")
        result = rule.evaluate({})
        assert result is None


# ============================================================
# ConvergeRule: _eval_expr operators
# ============================================================

class TestConvergeRuleEvalExpr:
    def _eval(self, expr, ctx):
        rule = ConvergeRule(name="_", condition_expr=expr)
        return rule._eval_expr(expr, ctx)

    def test_ge(self):
        assert self._eval("x >= 5", {"x": 5}) is True
        assert self._eval("x >= 5", {"x": 4}) is False

    def test_le(self):
        assert self._eval("x <= 3", {"x": 3}) is True
        assert self._eval("x <= 3", {"x": 4}) is False

    def test_ne(self):
        assert self._eval("x != 0", {"x": 1}) is True
        assert self._eval("x != 0", {"x": 0}) is False

    def test_gt(self):
        assert self._eval("x > 5", {"x": 6}) is True
        assert self._eval("x > 5", {"x": 5}) is False

    def test_lt(self):
        assert self._eval("x < 5", {"x": 4}) is True
        assert self._eval("x < 5", {"x": 5}) is False

    def test_eq(self):
        assert self._eval("x == hello", {"x": "hello"}) is True
        assert self._eval("x == hello", {"x": "world"}) is False


# ============================================================
# ConvergeRule: _resolve_path
# ============================================================

class TestConvergeRuleResolvePath:
    def test_simple(self):
        assert ConvergeRule._resolve_path("x", {"x": 42}) == 42

    def test_nested(self):
        ctx = {"metrics": {"lint": {"errors": 5}}}
        assert ConvergeRule._resolve_path("metrics.lint.errors", ctx) == 5

    def test_missing_returns_zero(self):
        assert ConvergeRule._resolve_path("missing.path", {}) == 0

    def test_non_dict_returns_zero(self):
        assert ConvergeRule._resolve_path("x.y", {"x": "string"}) == 0


# ============================================================
# ConvergeRule: from_dict
# ============================================================

class TestConvergeRuleFromDict:
    def test_full(self):
        data = {
            "name": "skip_many_errors",
            "description": "Skip when too many errors",
            "condition": "metrics.lint.errors > 20",
            "action": "skip_stage",
            "target": "lint",
            "reason": "Too many errors",
            "priority": 10,
        }
        rule = ConvergeRule.from_dict(data)
        assert rule.name == "skip_many_errors"
        assert rule.condition_expr == "metrics.lint.errors > 20"
        assert rule.action == "skip_stage"
        assert rule.priority == 10

    def test_defaults(self):
        rule = ConvergeRule.from_dict({})
        assert rule.name == ""
        assert rule.priority == 0
        assert rule.action == ""


# ============================================================
# ConvergeRules: Adding Rules
# ============================================================

class TestConvergeRulesAdd:
    def test_add_callable(self):
        engine = ConvergeRules()
        engine.add_callable("test_rule", lambda ctx: None, description="test")
        assert len(engine.rules) == 1
        assert engine.rules[0].name == "test_rule"
        assert engine.rules[0].priority == 100  # default for callables

    def test_add_expr_rule(self):
        engine = ConvergeRules()
        engine.add_expr_rule({
            "name": "skip_many",
            "condition": "iteration >= 5",
            "action": "skip_stage",
        })
        assert len(engine.rules) == 1
        assert engine.rules[0].condition_expr == "iteration >= 5"


# ============================================================
# ConvergeRules: load_from_dir
# ============================================================

class TestConvergeRulesLoadDir:
    def test_load_json_single_rule(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "rule1.json").write_text(json.dumps({
            "name": "test",
            "condition": "score < 0",
            "action": "abort",
        }), encoding="utf-8")

        engine = ConvergeRules()
        count = engine.load_from_dir(rules_dir)
        assert count == 1
        assert len(engine.rules) == 1

    def test_load_json_list(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "rules.json").write_text(json.dumps([
            {"name": "r1", "condition": "x > 0", "action": "skip_stage"},
            {"name": "r2", "condition": "x < 0", "action": "abort"},
        ]), encoding="utf-8")

        engine = ConvergeRules()
        count = engine.load_from_dir(rules_dir)
        assert count == 2

    def test_load_json_with_rules_key(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "bundle.json").write_text(json.dumps({
            "rules": [
                {"name": "r1", "condition": "x > 0", "action": "skip_stage"},
            ]
        }), encoding="utf-8")

        engine = ConvergeRules()
        count = engine.load_from_dir(rules_dir)
        assert count == 1

    def test_load_corrupted_json(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        (rules_dir / "bad.json").write_text("{bad json", encoding="utf-8")

        engine = ConvergeRules()
        count = engine.load_from_dir(rules_dir)
        assert count == 0

    def test_load_nonexistent_dir(self, tmp_path):
        engine = ConvergeRules()
        count = engine.load_from_dir(tmp_path / "nonexistent")
        assert count == 0

    def test_load_python_file(self, tmp_path):
        rules_dir = tmp_path / "rules"
        rules_dir.mkdir()
        py_file = rules_dir / "my_rules.py"
        py_file.write_text(
            "def register_rules(engine):\n"
            "    engine.add_expr_rule({'name': 'py_rule', 'condition': 'x > 0', 'action': 'skip_stage'})\n",
            encoding="utf-8",
        )

        engine = ConvergeRules()
        count = engine.load_from_dir(rules_dir)
        assert count == 1
        assert engine.rules[0].name == "py_rule"


# ============================================================
# ConvergeRules: evaluate
# ============================================================

class TestConvergeRulesEvaluate:
    def test_no_rules(self):
        engine = ConvergeRules()
        result = engine.evaluate(stage="lint", metrics={})
        assert result.is_noop() is True

    def test_matching_rule(self):
        engine = ConvergeRules()
        engine.add_expr_rule({
            "name": "skip_many",
            "condition": "metrics.lint.errors > 20",
            "action": "skip_stage",
            "reason": "Too many errors",
        })
        result = engine.evaluate(
            stage="lint",
            metrics={"lint": {"errors": 25}},
        )
        assert result.action == "skip_stage"
        assert "Too many errors" in result.reason

    def test_no_matching_rule(self):
        engine = ConvergeRules()
        engine.add_expr_rule({
            "name": "skip_many",
            "condition": "metrics.lint.errors > 20",
            "action": "skip_stage",
        })
        result = engine.evaluate(
            stage="lint",
            metrics={"lint": {"errors": 5}},
        )
        assert result.is_noop() is True

    def test_priority_ordering(self):
        """Higher priority wins."""
        engine = ConvergeRules()

        def low_rule(ctx):
            return RuleResult(action="skip_stage", priority=10)

        def high_rule(ctx):
            return RuleResult(action="abort", priority=100)

        engine.add_callable("low", low_rule)
        engine.add_callable("high", high_rule)

        result = engine.evaluate(stage="lint", metrics={})
        assert result.action == "abort"  # higher priority wins

    def test_callable_over_expr(self):
        """Callable rules have priority 100 by default, expr rules can be higher."""
        engine = ConvergeRules()
        engine.add_callable("call_rule", lambda ctx: RuleResult(action="from_callable"))
        engine.add_expr_rule({"name": "expr_rule", "condition": "iteration >= 0",
                              "action": "from_expr", "priority": 200})
        # expr with priority 200 > callable with priority 100
        result = engine.evaluate(stage="lint", metrics={}, iteration=0)
        assert result.action == "from_expr"

    def test_flatten_metrics(self):
        """Evaluate can use iteration and other scalar context values."""
        engine = ConvergeRules()
        engine.add_expr_rule({
            "name": "test",
            "condition": "iteration >= 3",
            "action": "skip_stage",
        })
        result = engine.evaluate(
            stage="lint",
            metrics={"lint": {"errors": 5}},
            iteration=5,
        )
        assert result.action == "skip_stage"


# ============================================================
# ConvergeRules: list_rules, _flatten
# ============================================================

class TestConvergeRulesHelpers:
    def test_list_rules_empty(self):
        engine = ConvergeRules()
        assert "No rules" in engine.list_rules()

    def test_list_rules_with_data(self):
        engine = ConvergeRules()
        engine.add_callable("my_rule", lambda ctx: None, description="Test rule")
        engine.add_expr_rule({"name": "expr_rule", "condition": "x > 0"})
        text = engine.list_rules()
        assert "my_rule" in text
        assert "expr_rule" in text
        assert "callable" in text
        assert "expr" in text

    def test_flatten(self):
        out = {}
        ConvergeRules._flatten({"a": {"b": 1}, "c": 2}, out)
        assert out == {"a.b": 1, "c": 2}


# ============================================================
# Built-in Rules
# ============================================================

class TestBuiltinRules:
    def test_abort_on_max_iterations(self):
        ctx = {"iteration": 15, "max_iterations": 15}
        result = rule_abort_on_max_iterations(ctx)
        assert result is not None
        assert result.action == "abort"
        assert "15" in result.reason
        assert result.priority == 1000

    def test_abort_not_reached(self):
        ctx = {"iteration": 5, "max_iterations": 15}
        result = rule_abort_on_max_iterations(ctx)
        assert result is None

    def test_abort_no_max(self):
        ctx = {"iteration": 100}
        result = rule_abort_on_max_iterations(ctx)
        assert result is None

    def test_skip_on_zero_metrics(self):
        ctx = {
            "stage": "lint",
            "metrics_flat": {"lint.errors": 0, "lint.warnings": 0},
            "iteration": 3,
        }
        result = rule_skip_stage_on_zero_metrics(ctx)
        assert result is not None
        assert result.action == "skip_stage"
        assert result.priority == 50

    def test_skip_not_when_has_data(self):
        ctx = {
            "stage": "lint",
            "metrics_flat": {"lint.errors": 5},
            "iteration": 3,
        }
        result = rule_skip_stage_on_zero_metrics(ctx)
        assert result is None

    def test_skip_not_on_first_iteration(self):
        ctx = {
            "stage": "lint",
            "metrics_flat": {"lint.errors": 0},
            "iteration": 0,
        }
        result = rule_skip_stage_on_zero_metrics(ctx)
        assert result is None  # iteration must be > 0


class TestRegisterBuiltinRules:
    def test_registers_rules(self):
        engine = ConvergeRules()
        register_builtin_rules(engine)
        assert len(engine.rules) == 2
        names = [r.name for r in engine.rules]
        assert "abort_on_max_iterations" in names
        assert "skip_stage_on_zero_metrics" in names


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
