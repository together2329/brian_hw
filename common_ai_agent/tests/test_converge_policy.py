"""
Tests for core/converge_policy.py — ConvergePolicy RPE learner.

Covers:
  - OutcomeRecord to_dict/from_dict
  - ConvergePolicy.record, record_iteration
  - get_average_delta, get_best_label_for_stage, get_sample_count
  - suggest_override (enough data, not enough data, better alternative, no better)
  - save/load round-trip
  - format_stats
  - Edge cases: empty history, single entry, negative deltas
"""

import os
import sys
import json
import pytest
from pathlib import Path

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.converge_policy import OutcomeRecord, ConvergePolicy


# ============================================================
# OutcomeRecord
# ============================================================

class TestOutcomeRecord:
    def test_to_dict(self):
        rec = OutcomeRecord(
            classifier_label="tb_bug",
            fix_workspace="tb-gen",
            score_delta=5.0,
            stage="sim",
            iteration=3,
        )
        d = rec.to_dict()
        assert d["classifier_label"] == "tb_bug"
        assert d["fix_workspace"] == "tb-gen"
        assert d["score_delta"] == 5.0
        assert d["stage"] == "sim"
        assert d["iteration"] == 3

    def test_to_dict_defaults(self):
        rec = OutcomeRecord(classifier_label="x", fix_workspace="y", score_delta=1.0)
        d = rec.to_dict()
        assert d["stage"] == ""
        assert d["iteration"] == 0

    def test_from_dict(self):
        data = {
            "classifier_label": "rtl_bug",
            "fix_workspace": "rtl-gen",
            "score_delta": -3.5,
            "stage": "lint",
            "iteration": 7,
        }
        rec = OutcomeRecord.from_dict(data)
        assert rec.classifier_label == "rtl_bug"
        assert rec.fix_workspace == "rtl-gen"
        assert rec.score_delta == -3.5
        assert rec.stage == "lint"
        assert rec.iteration == 7

    def test_from_dict_defaults(self):
        rec = OutcomeRecord.from_dict({})
        assert rec.classifier_label == ""
        assert rec.score_delta == 0.0

    def test_round_trip(self):
        rec = OutcomeRecord("tb_bug", "tb-gen", 5.0, "sim", 3)
        d = rec.to_dict()
        restored = OutcomeRecord.from_dict(d)
        assert restored.classifier_label == rec.classifier_label
        assert restored.fix_workspace == rec.fix_workspace
        assert restored.score_delta == rec.score_delta
        assert restored.stage == rec.stage
        assert restored.iteration == rec.iteration


# ============================================================
# ConvergePolicy: Recording
# ============================================================

class TestConvergePolicyRecording:
    def test_record(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim", iteration=1)
        assert len(policy.history) == 1
        assert policy.history[0].classifier_label == "tb_bug"
        assert policy.history[0].score_delta == 5.0

    def test_record_multiple(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", -2.0)
        policy.record("rtl_bug", "rtl-gen", 10.0)
        assert len(policy.history) == 3

    def test_record_iteration(self):
        policy = ConvergePolicy()
        policy.record_iteration("tb_bug", "tb-gen", 5.0, 10.0, stage="sim")
        assert len(policy.history) == 1
        assert policy.history[0].score_delta == 5.0  # 10 - 5

    def test_record_iteration_negative_delta(self):
        policy = ConvergePolicy()
        policy.record_iteration("tb_bug", "tb-gen", 10.0, 5.0)
        assert policy.history[0].score_delta == -5.0

    def test_record_builds_stats(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", -2.0)
        policy.record("rtl_bug", "rtl-gen", 10.0)
        key1 = "tb_bug::tb-gen"
        key2 = "rtl_bug::rtl-gen"
        assert policy._stats[key1] == [5.0, -2.0]
        assert policy._stats[key2] == [10.0]


# ============================================================
# ConvergePolicy: Statistics
# ============================================================

class TestConvergePolicyStats:
    def test_get_average_delta(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", -2.0)
        # Average = (5 + -2) / 2 = 1.5
        assert policy.get_average_delta("tb_bug", "tb-gen") == 1.5

    def test_get_average_delta_no_data(self):
        policy = ConvergePolicy()
        assert policy.get_average_delta("unknown", "unknown") == 0.0

    def test_get_average_delta_single(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 7.0)
        assert policy.get_average_delta("tb_bug", "tb-gen") == 7.0

    def test_get_sample_count(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", 3.0)
        policy.record("rtl_bug", "rtl-gen", 1.0)
        assert policy.get_sample_count("tb_bug", "tb-gen") == 2
        assert policy.get_sample_count("rtl_bug", "rtl-gen") == 1
        assert policy.get_sample_count("unknown", "unknown") == 0

    def test_get_best_label_for_stage(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 3.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 10.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 8.0, stage="sim")
        best = policy.get_best_label_for_stage("sim")
        assert best == "rtl_bug"  # avg 9.0 > avg 4.0

    def test_get_best_label_filtered(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 10.0, stage="sim")
        best = policy.get_best_label_for_stage("sim", labels=["tb_bug"])
        assert best == "tb_bug"  # only tb_bug considered

    def test_get_best_label_no_data(self):
        policy = ConvergePolicy()
        assert policy.get_best_label_for_stage("sim") is None

    def test_get_best_label_wrong_stage(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        assert policy.get_best_label_for_stage("lint") is None

    def test_get_best_label_filtered_no_match(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        best = policy.get_best_label_for_stage("sim", labels=["nonexistent"])
        assert best is None


# ============================================================
# ConvergePolicy: Suggest Override
# ============================================================

class TestConvergePolicySuggestOverride:
    def test_no_data(self):
        policy = ConvergePolicy()
        assert policy.suggest_override("sim", "output") is None

    def test_too_few_samples(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 10.0, stage="sim")
        # Only 2 records total, need >= 3
        assert policy.suggest_override("sim", "output") is None

    def test_only_one_label_with_enough_samples(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 3.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 4.0, stage="sim")
        # Only 1 label, need >= 2 to compare
        assert policy.suggest_override("sim", "output", current_label="tb_bug") is None

    def test_suggests_better_alternative(self):
        policy = ConvergePolicy()
        # tb_bug: avg delta = 1.0 (bad)
        policy.record("tb_bug", "tb-gen", 2.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 0.0, stage="sim")
        # rtl_bug: avg delta = 8.0 (good)
        policy.record("rtl_bug", "rtl-gen", 10.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 6.0, stage="sim")
        # Add one more to reach >= 3 total
        policy.record("tb_bug", "tb-gen", 1.0, stage="sim")

        suggestion = policy.suggest_override(
            "sim", "output", current_label="tb_bug"
        )
        assert suggestion is not None
        assert "rtl_bug" in suggestion
        assert "tb_bug" in suggestion
        assert "+" in suggestion or "-" in suggestion

    def test_no_suggestion_when_current_is_best(self):
        policy = ConvergePolicy()
        # tb_bug: avg delta = 10.0 (best)
        policy.record("tb_bug", "tb-gen", 10.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 10.0, stage="sim")
        # rtl_bug: avg delta = 1.0 (worse)
        policy.record("rtl_bug", "rtl-gen", 1.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 1.0, stage="sim")

        suggestion = policy.suggest_override(
            "sim", "output", current_label="tb_bug"
        )
        assert suggestion is None  # tb_bug is already best

    def test_no_suggestion_when_improvement_too_small(self):
        policy = ConvergePolicy()
        # tb_bug: avg = 5.0
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim")
        # rtl_bug: avg = 6.0 (only 1.0 better, threshold is >2.0)
        policy.record("rtl_bug", "rtl-gen", 6.0, stage="sim")
        policy.record("rtl_bug", "rtl-gen", 6.0, stage="sim")

        suggestion = policy.suggest_override(
            "sim", "output", current_label="tb_bug"
        )
        assert suggestion is None  # improvement not large enough


# ============================================================
# ConvergePolicy: Persistence
# ============================================================

class TestConvergePolicyPersistence:
    def test_save_and_load(self, tmp_path):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0, stage="sim", iteration=1)
        policy.record("rtl_bug", "rtl-gen", -3.0, stage="lint", iteration=2)

        path = tmp_path / "policy.json"
        policy.save(path)

        assert path.exists()

        loaded = ConvergePolicy()
        assert loaded.load(path) is True
        assert len(loaded.history) == 2
        assert loaded.history[0].classifier_label == "tb_bug"
        assert loaded.history[1].classifier_label == "rtl_bug"
        assert loaded.history[0].score_delta == 5.0
        # Stats should be rebuilt
        assert loaded.get_sample_count("tb_bug", "tb-gen") == 1
        assert loaded.get_sample_count("rtl_bug", "rtl-gen") == 1

    def test_save_creates_directory(self, tmp_path):
        policy = ConvergePolicy()
        path = tmp_path / "deep" / "nested" / "policy.json"
        policy.save(path)
        assert path.exists()

    def test_load_nonexistent(self, tmp_path):
        policy = ConvergePolicy()
        assert policy.load(tmp_path / "nonexistent.json") is False

    def test_load_corrupted(self, tmp_path):
        path = tmp_path / "bad.json"
        path.write_text("{bad json", encoding="utf-8")
        policy = ConvergePolicy()
        assert policy.load(path) is False

    def test_save_load_preserves_stats(self, tmp_path):
        """After load, stats index is rebuilt from history."""
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", 3.0)
        policy.record("rtl_bug", "rtl-gen", 10.0)

        path = tmp_path / "policy.json"
        policy.save(path)

        loaded = ConvergePolicy()
        loaded.load(path)
        assert loaded.get_average_delta("tb_bug", "tb-gen") == 4.0
        assert loaded.get_average_delta("rtl_bug", "rtl-gen") == 10.0


# ============================================================
# ConvergePolicy: Display
# ============================================================

class TestConvergePolicyDisplay:
    def test_format_stats_empty(self):
        policy = ConvergePolicy()
        assert "No policy data" in policy.format_stats()

    def test_format_stats_with_data(self):
        policy = ConvergePolicy()
        policy.record("tb_bug", "tb-gen", 5.0)
        policy.record("tb_bug", "tb-gen", -2.0)
        text = policy.format_stats()
        assert "tb_bug::tb-gen" in text
        assert "avg_delta" in text
        assert "n=2" in text

    def test_format_stats_positive_icon(self):
        policy = ConvergePolicy()
        policy.record("good", "ws", 10.0)
        text = policy.format_stats()
        assert "[+]" in text

    def test_format_stats_negative_icon(self):
        policy = ConvergePolicy()
        policy.record("bad", "ws", -10.0)
        text = policy.format_stats()
        assert "[-]" in text

    def test_format_stats_neutral_icon(self):
        policy = ConvergePolicy()
        policy.record("neutral", "ws", 0.0)
        text = policy.format_stats()
        assert "[=]" in text


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
