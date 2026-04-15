"""
core/converge_rules.py — Rule engine for converge loop overrides

Provides a simple rule engine that can override classifier decisions,
skip stages, force restarts, or inject messages based on runtime conditions.

Rules are expressed as Python callables or condition strings. Workspace-specific
rules can be added in workflow/<name>/rules/ directories.

Usage:
    engine = ConvergeRules()
    engine.add_rule("skip_lint_many_errors", skip_if_many_errors)
    result = engine.evaluate(stage="lint", metrics={"lint.errors": 25}, ...)
    # → RuleResult(action="skip_stage", reason="Too many errors, restart rtl")

Domain-agnostic — rules operate on generic stage names and metrics dicts.
"""

import os
import re
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Callable, Dict, List, Optional


# ============================================================
# Rule Result
# ============================================================

@dataclass
class RuleResult:
    """Result of evaluating a rule."""
    action: str = ""          # "skip_stage" | "force_restart" | "override_classifier" | "inject_message" | "abort"
    target: str = ""          # stage to restart from, or classifier label to force
    reason: str = ""          # human-readable explanation
    priority: int = 0         # higher = wins when multiple rules fire

    def is_noop(self) -> bool:
        return self.action == ""


# ============================================================
# Rule Definition
# ============================================================

@dataclass
class ConvergeRule:
    """
    A single rule: condition → action.

    Can be defined as:
      - A Python callable: fn(context) -> Optional[RuleResult]
      - A condition string + action config (loaded from JSON/YAML)
    """
    name: str
    description: str = ""

    # Either a callable or a condition string
    condition_fn: Optional[Callable] = None
    condition_expr: str = ""  # e.g., "metrics.lint.errors > 20"

    # Action config (used when condition_expr matches)
    action: str = ""
    target: str = ""
    reason_template: str = ""
    priority: int = 0

    def evaluate(self, context: Dict[str, Any]) -> Optional[RuleResult]:
        """Evaluate this rule against the given context."""
        if self.condition_fn:
            try:
                return self.condition_fn(context)
            except Exception:
                return None

        if self.condition_expr:
            if self._eval_expr(self.condition_expr, context):
                reason = self.reason_template
                # Simple template substitution
                for key, val in context.get("metrics_flat", {}).items():
                    reason = reason.replace(f"{{{key}}}", str(val))
                reason = reason.replace("{stage}", context.get("stage", ""))
                return RuleResult(
                    action=self.action,
                    target=self.target,
                    reason=reason,
                    priority=self.priority,
                )

        return None

    def _eval_expr(self, expr: str, context: Dict) -> bool:
        """
        Evaluate a simple condition expression.

        Supports: "metrics.lint.errors > 20", "iteration >= 5"
        Accesses context dict with dot notation.
        """
        for op in [">=", "<=", "!=", ">", "<", "=="]:
            if op in expr:
                parts = expr.split(op, 1)
                lhs_path = parts[0].strip()
                rhs_val = parts[1].strip()

                lhs_val = self._resolve_path(lhs_path, context)

                try:
                    if op == ">=": return float(lhs_val) >= float(rhs_val)
                    elif op == "<=": return float(lhs_val) <= float(rhs_val)
                    elif op == ">": return float(lhs_val) > float(rhs_val)
                    elif op == "<": return float(lhs_val) < float(rhs_val)
                    elif op == "==": return str(lhs_val) == rhs_val
                    elif op == "!=": return str(lhs_val) != rhs_val
                except (ValueError, TypeError):
                    return False

        return False

    @staticmethod
    def _resolve_path(path: str, context: Dict) -> Any:
        """Resolve a dot-notation path like 'metrics.lint.errors' from context."""
        parts = path.split(".")
        current = context
        for part in parts:
            if isinstance(current, dict):
                current = current.get(part, 0)
            else:
                return 0
        return current

    @classmethod
    def from_dict(cls, data: Dict) -> "ConvergeRule":
        """Create from a dict (e.g., loaded from JSON rule file)."""
        return cls(
            name=data.get("name", ""),
            description=data.get("description", ""),
            condition_expr=data.get("condition", ""),
            action=data.get("action", ""),
            target=data.get("target", ""),
            reason_template=data.get("reason", ""),
            priority=int(data.get("priority", 0)),
        )


# ============================================================
# Rule Engine
# ============================================================

class ConvergeRules:
    """
    Rule engine for converge loop overrides.

    Rules are evaluated in priority order (highest first).
    The first matching rule wins.

    Usage:
        engine = ConvergeRules()
        engine.add_callable("skip_lint", my_rule_fn)
        engine.add_expr_rule({"name": "skip_many", "condition": "metrics.lint.errors > 20", ...})
        result = engine.evaluate(context)
    """

    def __init__(self):
        self.rules: List[ConvergeRule] = []

    # ============================================================
    # Adding Rules
    # ============================================================

    def add_callable(self, name: str, fn: Callable,
                     description: str = "") -> None:
        """Add a Python callable rule."""
        self.rules.append(ConvergeRule(
            name=name,
            description=description,
            condition_fn=fn,
            priority=100,  # callable rules have high priority by default
        ))

    def add_expr_rule(self, rule_data: Dict) -> None:
        """Add a rule from a dict (condition string + action config)."""
        self.rules.append(ConvergeRule.from_dict(rule_data))

    def load_from_dir(self, rules_dir: Path) -> int:
        """
        Load all rule files from a directory.

        Supports:
          - .json files: each file is a rule dict or list of rule dicts
          - .py files: must export register_rules(engine) function
        """
        if not rules_dir.is_dir():
            return 0

        count = 0
        for f in sorted(rules_dir.iterdir()):
            if f.suffix == ".json":
                count += self._load_json_rules(f)
            elif f.suffix == ".py":
                count += self._load_python_rules(f)

        # Sort by priority (highest first)
        self.rules.sort(key=lambda r: r.priority, reverse=True)
        return count

    def _load_json_rules(self, path: Path) -> int:
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            if isinstance(data, list):
                for rule_data in data:
                    self.add_expr_rule(rule_data)
                return len(data)
            elif isinstance(data, dict):
                if "rules" in data:
                    for rule_data in data["rules"]:
                        self.add_expr_rule(rule_data)
                    return len(data["rules"])
                else:
                    self.add_expr_rule(data)
                    return 1
        except (json.JSONDecodeError, KeyError):
            pass
        return 0

    def _load_python_rules(self, path: Path) -> int:
        """Load rules from a Python file with register_rules(engine) function."""
        try:
            import importlib.util
            spec = importlib.util.spec_from_file_location(f"_rules_{path.stem}", path)
            mod = importlib.util.module_from_spec(spec)
            spec.loader.exec_module(mod)
            if hasattr(mod, "register_rules"):
                before = len(self.rules)
                mod.register_rules(self)
                return len(self.rules) - before
        except Exception:
            pass
        return 0

    # ============================================================
    # Evaluation
    # ============================================================

    def evaluate(self, stage: str, metrics: Dict[str, Any],
                 iteration: int = 0,
                 score: float = 0.0,
                 classifier_label: str = "",
                 extra: Optional[Dict] = None) -> RuleResult:
        """
        Evaluate all rules against the current context.

        Returns the highest-priority matching RuleResult,
        or a no-op RuleResult if no rules match.
        """
        # Flatten metrics for template substitution
        metrics_flat = {}
        self._flatten(metrics, metrics_flat)

        context = {
            "stage": stage,
            "metrics": metrics,
            "metrics_flat": metrics_flat,
            "iteration": iteration,
            "score": score,
            "classifier_label": classifier_label,
            **(extra or {}),
        }

        best_result = RuleResult()  # no-op

        for rule in self.rules:
            result = rule.evaluate(context)
            if result and not result.is_noop():
                if result.priority >= best_result.priority:
                    best_result = result

        return best_result

    # ============================================================
    # Helpers
    # ============================================================

    @staticmethod
    def _flatten(d: Dict, out: Dict, prefix: str = "") -> None:
        for k, v in d.items():
            full = f"{prefix}.{k}" if prefix else k
            if isinstance(v, dict):
                ConvergeRules._flatten(v, out, full)
            else:
                out[full] = v

    def list_rules(self) -> str:
        """List all registered rules."""
        if not self.rules:
            return "No rules registered."

        lines = ["=== Converge Rules ==="]
        for r in self.rules:
            rule_type = "callable" if r.condition_fn else "expr"
            lines.append(f"  [{r.priority:3d}] {r.name} ({rule_type}): {r.description or r.condition_expr}")
        return "\n".join(lines)


# ============================================================
# Built-in Rules (domain-agnostic)
# ============================================================

def rule_abort_on_max_iterations(context: Dict) -> Optional[RuleResult]:
    """Abort if iteration exceeds max (safety net)."""
    max_iter = context.get("max_iterations", 0)
    if max_iter and context.get("iteration", 0) >= max_iter:
        return RuleResult(
            action="abort",
            reason=f"Max iterations ({max_iter}) reached",
            priority=1000,
        )
    return None


def rule_skip_stage_on_zero_metrics(context: Dict) -> Optional[RuleResult]:
    """Skip a stage if all relevant metrics are zero (nothing to fix)."""
    stage = context.get("stage", "")
    metrics_flat = context.get("metrics_flat", {})

    # Check if stage has any non-zero metrics
    has_data = any(
        v != 0 for k, v in metrics_flat.items()
        if k.startswith(f"{stage}.") and isinstance(v, (int, float))
    )

    if not has_data and context.get("iteration", 0) > 0:
        return RuleResult(
            action="skip_stage",
            target=stage,
            reason=f"Stage {stage} has no actionable metrics, skipping",
            priority=50,
        )
    return None


def register_builtin_rules(engine: ConvergeRules) -> None:
    """Register built-in rules on an engine instance."""
    engine.add_callable(
        "abort_on_max_iterations",
        rule_abort_on_max_iterations,
        description="Abort if max iterations reached",
    )
    engine.add_callable(
        "skip_stage_on_zero_metrics",
        rule_skip_stage_on_zero_metrics,
        description="Skip stage if no actionable metrics",
    )
