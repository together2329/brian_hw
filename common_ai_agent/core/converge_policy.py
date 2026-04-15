"""
core/converge_policy.py — RPE (Reward Prediction Error) learning for converge loops

Tracks (classifier_label, fix_workspace, score_delta) tuples across loop
iterations. Over time, learns which classifier decisions led to score
improvement and which didn't.

Method: suggest_override(stage, output, context) → optional override string

Operates on generic classifier labels from YAML config, not hardcoded
domain-specific types.

Usage:
    policy = ConvergePolicy()
    # After each iteration, record the outcome:
    policy.record("tb_bug", "tb-gen", score_delta=+5.0)
    policy.record("tb_bug", "tb-gen", score_delta=-2.0)
    policy.record("rtl_bug", "rtl-gen", score_delta=+10.0)
    # Ask for suggestion:
    suggestion = policy.suggest_override("sim", "[FAIL] tests")
    # → "Consider using rtl_bug (avg delta: +10.0) over tb_bug (avg delta: +1.5)"
"""

import os
import json
from pathlib import Path
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional, Tuple
from collections import defaultdict


# ============================================================
# Outcome Record
# ============================================================

@dataclass
class OutcomeRecord:
    """Single observation: classifier decision → score change."""
    classifier_label: str
    fix_workspace: str
    score_delta: float       # positive = improvement, negative = regression
    stage: str = ""
    iteration: int = 0

    def to_dict(self) -> Dict:
        return {
            "classifier_label": self.classifier_label,
            "fix_workspace": self.fix_workspace,
            "score_delta": self.score_delta,
            "stage": self.stage,
            "iteration": self.iteration,
        }

    @classmethod
    def from_dict(cls, data: Dict) -> "OutcomeRecord":
        return cls(
            classifier_label=data.get("classifier_label", ""),
            fix_workspace=data.get("fix_workspace", ""),
            score_delta=float(data.get("score_delta", 0.0)),
            stage=data.get("stage", ""),
            iteration=int(data.get("iteration", 0)),
        )


# ============================================================
# RPE Learner
# ============================================================

class ConvergePolicy:
    """
    Reward Prediction Error learner for converge loop classifier decisions.

    Tracks which (classifier_label → fix_workspace) pairs produce positive
    score deltas. When a classifier decision produces a negative RPE
    (outcome worse than expected), suggests trying alternatives.

    The policy is domain-agnostic — it works with any classifier labels
    defined in converge.yaml.
    """

    def __init__(self):
        self.history: List[OutcomeRecord] = []
        self._stats: Dict[str, List[float]] = defaultdict(list)
        # key = f"{classifier_label}::{fix_workspace}", value = list of score_deltas

    # ============================================================
    # Recording
    # ============================================================

    def record(self, classifier_label: str, fix_workspace: str,
               score_delta: float, stage: str = "",
               iteration: int = 0) -> None:
        """
        Record an outcome: after applying a fix, how much did score change?

        Args:
            classifier_label: The classifier label that was used
            fix_workspace: The workspace that was used for the fix
            score_delta: Change in score (positive = improvement)
            stage: The stage where the fix was applied
            iteration: The loop iteration number
        """
        rec = OutcomeRecord(
            classifier_label=classifier_label,
            fix_workspace=fix_workspace,
            score_delta=score_delta,
            stage=stage,
            iteration=iteration,
        )
        self.history.append(rec)
        key = f"{classifier_label}::{fix_workspace}"
        self._stats[key].append(score_delta)

    def record_iteration(self, classifier_label: str, fix_workspace: str,
                         score_before: float, score_after: float,
                         stage: str = "", iteration: int = 0) -> None:
        """Record with explicit before/after scores."""
        self.record(
            classifier_label=classifier_label,
            fix_workspace=fix_workspace,
            score_delta=score_after - score_before,
            stage=stage,
            iteration=iteration,
        )

    # ============================================================
    # Statistics
    # ============================================================

    def get_average_delta(self, classifier_label: str,
                          fix_workspace: str) -> float:
        """Get average score delta for a (label, workspace) pair."""
        key = f"{classifier_label}::{fix_workspace}"
        deltas = self._stats.get(key, [])
        if not deltas:
            return 0.0
        return sum(deltas) / len(deltas)

    def get_best_label_for_stage(self, stage: str,
                                  labels: Optional[List[str]] = None) -> Optional[str]:
        """
        Find the classifier label with the highest average score delta
        for a given stage.
        """
        stage_records = [r for r in self.history if r.stage == stage]
        if not stage_records:
            return None

        label_deltas: Dict[str, List[float]] = defaultdict(list)
        for r in stage_records:
            if labels is None or r.classifier_label in labels:
                label_deltas[r.classifier_label].append(r.score_delta)

        if not label_deltas:
            return None

        best_label = max(label_deltas.keys(),
                         key=lambda l: sum(label_deltas[l]) / len(label_deltas[l]))
        return best_label

    def get_sample_count(self, classifier_label: str,
                         fix_workspace: str) -> int:
        """How many observations for this (label, workspace) pair."""
        key = f"{classifier_label}::{fix_workspace}"
        return len(self._stats.get(key, []))

    # ============================================================
    # Override Suggestion
    # ============================================================

    def suggest_override(self, stage: str, output: str,
                         current_label: str = "",
                         context: Optional[Dict] = None) -> Optional[str]:
        """
        Suggest a classifier override based on learned RPE.

        Logic:
          1. Find all labels used for this stage
          2. If current_label has negative average delta AND there's a
             better alternative, suggest it
          3. Require minimum 3 samples before suggesting

        Returns:
            Override suggestion string, or None if no override suggested
        """
        context = context or {}

        # Collect per-label stats for this stage
        stage_records = [r for r in self.history if r.stage == stage]
        if len(stage_records) < 3:
            return None  # Not enough data

        label_avg: Dict[str, float] = {}
        label_count: Dict[str, int] = {}
        for r in stage_records:
            label_avg.setdefault(r.classifier_label, [])
            label_avg[r.classifier_label].append(r.score_delta)
            label_count[r.classifier_label] = label_count.get(r.classifier_label, 0) + 1

        # Compute averages
        label_means = {}
        for label, deltas in label_avg.items():
            if len(deltas) >= 2:  # need at least 2 samples
                label_means[label] = sum(deltas) / len(deltas)

        if len(label_means) < 2:
            return None  # need at least 2 labels to compare

        # Find best alternative
        best_label = max(label_means, key=label_means.get)
        current_avg = label_means.get(current_label, 0.0)
        best_avg = label_means[best_label]

        # Only suggest if best is meaningfully better (>2.0 delta improvement)
        if best_label != current_label and (best_avg - current_avg) > 2.0:
            return (
                f"Consider using {best_label} "
                f"(avg delta: {best_avg:+.1f}) "
                f"over {current_label} "
                f"(avg delta: {current_avg:+.1f})"
            )

        return None

    # ============================================================
    # Persistence
    # ============================================================

    def save(self, path: Path) -> None:
        """Save policy history to JSON."""
        data = {
            "history": [r.to_dict() for r in self.history],
        }
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(
            json.dumps(data, indent=2, ensure_ascii=False),
            encoding="utf-8",
        )

    def load(self, path: Path) -> bool:
        """Load policy history from JSON. Returns True if loaded."""
        if not path.exists():
            return False
        try:
            data = json.loads(path.read_text(encoding="utf-8"))
            self.history = [OutcomeRecord.from_dict(d) for d in data.get("history", [])]
            # Rebuild stats index
            self._stats.clear()
            for rec in self.history:
                key = f"{rec.classifier_label}::{rec.fix_workspace}"
                self._stats[key].append(rec.score_delta)
            return True
        except (json.JSONDecodeError, KeyError):
            return False

    # ============================================================
    # Display
    # ============================================================

    def format_stats(self) -> str:
        """Format current policy statistics."""
        if not self._stats:
            return "No policy data yet."

        lines = ["=== Converge Policy Stats ==="]
        for key, deltas in sorted(self._stats.items()):
            avg = sum(deltas) / len(deltas) if deltas else 0.0
            icon = "+" if avg > 0 else "-" if avg < 0 else "="
            lines.append(f"  [{icon}] {key}: avg_delta={avg:+.1f}, n={len(deltas)}")
        return "\n".join(lines)
