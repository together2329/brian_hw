"""
Tests for validating that workflow/eda/converge.yaml loads correctly.

Covers:
  - converge.yaml loads without error
  - All 5 stages present with correct IDs
  - Stage dependencies are valid (depends_on references exist)
  - Stage produces declarations are present where needed
  - Feedback graph edges valid (trigger stages exist, retry_from stages exist)
  - Classifiers have non-empty patterns
  - Parsers regex patterns compile
  - Criteria hard_stop metrics are valid
  - Score function weights are numeric
  - Template variables referenced in prompts are resolvable
"""

import os
import sys
import re
import pytest
import yaml
from pathlib import Path

# Ensure import path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from core.project import (
    ConvergeConfig,
    StageConfig,
    FeedbackEdge,
    ClassifierRule,
    ParserConfig,
    load_yaml_file,
)


# ============================================================
# Fixture: Load converge.yaml
# ============================================================

CONVERGE_YAML_PATH = Path(__file__).parent.parent / "workflow" / "eda" / "converge.yaml"


@pytest.fixture(scope="module")
def raw_yaml():
    """Load raw YAML dict from converge.yaml."""
    if not CONVERGE_YAML_PATH.exists():
        pytest.skip("workflow/eda/converge.yaml not found")
    with open(CONVERGE_YAML_PATH, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


@pytest.fixture(scope="module")
def config(raw_yaml):
    """Parse into ConvergeConfig."""
    return ConvergeConfig.from_dict(raw_yaml)


# ============================================================
# Load without error
# ============================================================

class TestYamlLoads:
    """Verify converge.yaml can be loaded and parsed."""

    def test_file_exists(self):
        assert CONVERGE_YAML_PATH.exists(), f"Missing: {CONVERGE_YAML_PATH}"

    def test_loads_as_dict(self, raw_yaml):
        assert isinstance(raw_yaml, dict)

    def test_config_parses_without_error(self, raw_yaml):
        config = ConvergeConfig.from_dict(raw_yaml)
        assert config is not None

    def test_config_name(self, config):
        assert config.name == "eda-fast-loop"

    def test_config_description(self, config):
        assert config.description != ""


# ============================================================
# Stages
# ============================================================

class TestStages:
    """Verify all 5 stages are present with correct IDs."""

    EXPECTED_STAGES = ["spec", "rtl", "lint", "tb", "sim"]

    def test_five_stages_present(self, config):
        assert len(config.stages) == 5

    def test_stage_ids_match(self, config):
        stage_ids = [s.id for s in config.stages]
        assert stage_ids == self.EXPECTED_STAGES

    @pytest.mark.parametrize("stage_id", EXPECTED_STAGES)
    def test_each_stage_has_id(self, config, stage_id):
        stages = {s.id: s for s in config.stages}
        assert stage_id in stages

    @pytest.mark.parametrize("stage_id", EXPECTED_STAGES)
    def test_each_stage_has_workspace(self, config, stage_id):
        stages = {s.id: s for s in config.stages}
        assert stages[stage_id].workspace != ""

    @pytest.mark.parametrize("stage_id", EXPECTED_STAGES)
    def test_each_stage_has_prompt(self, config, stage_id):
        stages = {s.id: s for s in config.stages}
        assert stages[stage_id].prompt.strip() != ""

    @pytest.mark.parametrize("stage_id", EXPECTED_STAGES)
    def test_each_stage_has_agent(self, config, stage_id):
        stages = {s.id: s for s in config.stages}
        assert stages[stage_id].agent != ""

    def test_stage_ordering(self, config):
        """Stages should be in pipeline order: spec → rtl → lint → tb → sim."""
        ids = [s.id for s in config.stages]
        assert ids.index("spec") < ids.index("rtl")
        assert ids.index("rtl") < ids.index("lint")
        assert ids.index("lint") < ids.index("tb")
        assert ids.index("tb") < ids.index("sim")


# ============================================================
# Stage dependencies
# ============================================================

class TestStageDependencies:
    """Verify stage depends_on references are valid."""

    def test_depends_on_references_exist(self, config):
        """All depends_on references should point to existing stage IDs."""
        stage_ids = {s.id for s in config.stages}
        for stage in config.stages:
            for dep in stage.depends_on:
                assert dep in stage_ids, (
                    f"Stage '{stage.id}' depends_on '{dep}' which doesn't exist"
                )

    def test_rtl_depends_on_spec(self, config):
        stages = {s.id: s for s in config.stages}
        assert "spec" in stages["rtl"].depends_on

    def test_lint_depends_on_rtl(self, config):
        stages = {s.id: s for s in config.stages}
        assert "rtl" in stages["lint"].depends_on

    def test_no_circular_deps(self, config):
        """No stage should eventually depend on itself."""
        stages = {s.id: s for s in config.stages}
        # Simple DFS cycle check
        def has_cycle(stage_id, visited=None):
            if visited is None:
                visited = set()
            if stage_id in visited:
                return True
            visited.add(stage_id)
            for dep in stages[stage_id].depends_on:
                if has_cycle(dep, visited.copy()):
                    return True
            return False

        for stage in config.stages:
            assert not has_cycle(stage.id), f"Circular dependency involving '{stage.id}'"


# ============================================================
# Stage produces
# ============================================================

class TestStageProduces:
    """Verify produces declarations."""

    def test_spec_produces_mas_path(self, config):
        stages = {s.id: s for s in config.stages}
        assert "mas_path" in stages["spec"].produces

    def test_rtl_produces_rtl_path(self, config):
        stages = {s.id: s for s in config.stages}
        assert "rtl_path" in stages["rtl"].produces

    def test_tb_produces_tb_path(self, config):
        stages = {s.id: s for s in config.stages}
        assert "tb_path" in stages["tb"].produces


# ============================================================
# Feedback graph
# ============================================================

class TestFeedbackGraph:
    """Verify feedback graph edges are valid."""

    def test_feedback_graph_not_empty(self, config):
        assert len(config.feedback_graph) > 0

    def test_trigger_stages_exist(self, config):
        """All trigger stages should reference existing stage IDs."""
        stage_ids = {s.id for s in config.stages}
        for edge in config.feedback_graph:
            assert edge.trigger_stage in stage_ids, (
                f"Feedback edge trigger stage '{edge.trigger_stage}' doesn't exist"
            )

    def test_retry_from_stages_exist(self, config):
        """All retry_from references should point to existing stage IDs."""
        stage_ids = {s.id for s in config.stages}
        for edge in config.feedback_graph:
            if edge.retry_from:
                assert edge.retry_from in stage_ids, (
                    f"Feedback edge retry_from '{edge.retry_from}' doesn't exist"
                )

    def test_fix_workspaces_not_empty(self, config):
        """All fix edges should have a workspace."""
        for edge in config.feedback_graph:
            assert edge.fix_workspace != "", (
                f"Feedback edge for trigger '{edge.trigger_stage}' missing fix workspace"
            )

    def test_fix_prompts_not_empty(self, config):
        """All fix edges should have a prompt."""
        for edge in config.feedback_graph:
            assert edge.fix_prompt.strip() != "", (
                f"Feedback edge for trigger '{edge.trigger_stage}' missing fix prompt"
            )

    def test_max_retries_positive(self, config):
        """All max_retries should be positive integers."""
        for edge in config.feedback_graph:
            assert edge.max_retries > 0, (
                f"Feedback edge for trigger '{edge.trigger_stage}' has max_retries={edge.max_retries}"
            )


# ============================================================
# Classifiers
# ============================================================

class TestClassifiers:
    """Verify classifiers have non-empty patterns."""

    def test_classifiers_not_empty(self, config):
        assert len(config.classifiers) > 0

    def test_each_classifier_has_id(self, config):
        for cls_rule in config.classifiers:
            assert cls_rule.id != "", f"Classifier missing id"

    def test_each_classifier_has_patterns(self, config):
        for cls_rule in config.classifiers:
            assert len(cls_rule.patterns) > 0, (
                f"Classifier '{cls_rule.id}' has no patterns"
            )

    def test_each_classifier_has_label(self, config):
        for cls_rule in config.classifiers:
            assert cls_rule.label != "", (
                f"Classifier '{cls_rule.id}' missing label"
            )

    def test_classifier_labels_unique(self, config):
        labels = [c.label for c in config.classifiers]
        assert len(labels) == len(set(labels)), f"Duplicate classifier labels: {labels}"

    def test_classifier_ids_unique(self, config):
        ids = [c.id for c in config.classifiers]
        assert len(ids) == len(set(ids)), f"Duplicate classifier ids: {ids}"


# ============================================================
# Parsers
# ============================================================

class TestParsers:
    """Verify parser regex patterns compile."""

    def test_parsers_not_empty(self, config):
        assert len(config.parsers) > 0

    def test_parser_stages_are_valid(self, config):
        """Parser stage IDs should reference existing stages."""
        stage_ids = {s.id for s in config.stages}
        for stage_id in config.parsers:
            assert stage_id in stage_ids, (
                f"Parser references unknown stage '{stage_id}'"
            )

    def test_parser_patterns_compile(self, config):
        """All regex patterns in parsers should compile."""
        for stage_id, parser in config.parsers.items():
            if parser.patterns:
                for field_name, pattern in parser.patterns.items():
                    try:
                        re.compile(pattern)
                    except re.error as e:
                        pytest.fail(
                            f"Parser '{stage_id}.{field_name}' has invalid regex: {pattern} ({e})"
                        )

    def test_parser_type_valid(self, config):
        """Parser types should be one of the known types."""
        valid_types = {"count_patterns", "structured", "regex_groups"}
        for stage_id, parser in config.parsers.items():
            assert parser.parser_type in valid_types, (
                f"Parser '{stage_id}' has unknown type '{parser.parser_type}'"
            )


# ============================================================
# Criteria
# ============================================================

class TestCriteria:
    """Verify criteria hard_stop metrics are valid."""

    def test_hard_stop_not_empty(self, config):
        assert len(config.criteria_hard_stop) > 0

    def test_hard_stop_has_required_fields(self, config):
        """Each hard_stop criterion must have metric, operator, value."""
        for criterion in config.criteria_hard_stop:
            assert "metric" in criterion, f"Hard-stop missing 'metric': {criterion}"
            assert "operator" in criterion, f"Hard-stop missing 'operator': {criterion}"
            assert "value" in criterion, f"Hard-stop missing 'value': {criterion}"

    def test_hard_stop_operators_valid(self, config):
        """Operators should be one of the supported comparison operators."""
        valid_ops = {"==", "!=", ">=", "<=", ">", "<"}
        for criterion in config.criteria_hard_stop:
            assert criterion["operator"] in valid_ops, (
                f"Invalid operator '{criterion['operator']}' in criterion"
            )

    def test_hard_stop_metric_paths_valid(self, config):
        """Metric paths should be non-empty strings."""
        for criterion in config.criteria_hard_stop:
            metric = criterion["metric"]
            assert isinstance(metric, str) and len(metric) > 0, (
                f"Invalid metric path: {metric}"
            )

    def test_score_threshold_positive(self, config):
        assert config.criteria_score_threshold > 0

    def test_max_iterations_positive(self, config):
        assert config.criteria_max_total_iterations > 0

    def test_no_improve_limit_positive(self, config):
        assert config.criteria_no_improve_limit > 0


# ============================================================
# Score function weights
# ============================================================

class TestScoreFunction:
    """Verify score function weights are numeric."""

    def test_weights_not_empty(self, config):
        assert len(config.score_weights) > 0

    def test_all_weights_numeric(self, config):
        for key, weight in config.score_weights.items():
            assert isinstance(weight, (int, float)), (
                f"Weight '{key}' is not numeric: {weight} ({type(weight)})"
            )

    def test_negative_weights_are_penalties(self, config):
        """At least one weight should be negative (penalty)."""
        has_negative = any(w < 0 for w in config.score_weights.values())
        assert has_negative, "No penalty weights found — score function needs at least one negative weight"

    def test_positive_weights_are_rewards(self, config):
        """At least one weight should be positive (reward)."""
        has_positive = any(w > 0 for w in config.score_weights.values())
        assert has_positive, "No reward weights found — score function needs at least one positive weight"

    def test_weight_keys_have_meaningful_names(self, config):
        """Weight keys should be meaningful metric identifiers (dotted or simple)."""
        for key in config.score_weights:
            assert isinstance(key, str) and len(key) > 0, f"Invalid weight key: '{key}'"


# ============================================================
# Template variables
# ============================================================

class TestTemplateVariables:
    """Verify template variables referenced in prompts are resolvable."""

    def test_all_prompts_use_template_variables(self, config):
        """All prompts should use at least one template variable ({...})."""
        for stage in config.stages:
            refs = re.findall(r'\{(\w+)\}', stage.prompt)
            assert len(refs) > 0, (
                f"Stage '{stage.id}' prompt doesn't use any template variables"
            )

    def test_produced_variables_used_downstream(self, config):
        """Variables produced by a stage should be used in later stages."""
        stage_map = {s.id: s for s in config.stages}
        all_produces = {}
        for stage in config.stages:
            for var in stage.produces:
                all_produces[var] = stage.id

        # Check that produced variables are referenced in later prompts
        for stage in config.stages:
            for var in stage.produces:
                var_ref = "{" + var + "}"
                found = False
                for later_stage in config.stages:
                    if config.stages.index(later_stage) > config.stages.index(stage):
                        if var_ref in later_stage.prompt:
                            found = True
                            break
                # Not all produced vars MUST be used (some are for feedback),
                # but we check that common ones are
                if var in ("mas_path", "rtl_path", "tb_path"):
                    assert found, (
                        f"Produced variable '{var}' from stage '{stage.id}' "
                        f"not referenced in any later stage prompt"
                    )

    def test_no_unknown_variables_in_prompts(self, config):
        """Template variables should reference known produces or built-in vars."""
        known_vars = {"module"}
        for stage in config.stages:
            for var in stage.produces:
                known_vars.add(var)
        # Also add common feedback/context vars
        known_vars.update({"lint_result", "sim_result", "lint_context"})

        for stage in config.stages:
            refs = set(re.findall(r'\{(\w+)\}', stage.prompt))
            for ref in refs:
                # Allow underscores and common suffixes
                assert ref in known_vars or ref.endswith("_path") or ref.endswith("_result") or ref.endswith("_context"), (
                    f"Stage '{stage.id}' references unknown variable '{{{ref}}}'"
                )


# ============================================================
# Rollback config
# ============================================================

class TestRollbackConfig:
    """Verify rollback configuration."""

    def test_rollback_enabled(self, config):
        assert isinstance(config.rollback_enabled, bool)

    def test_rollback_on_valid(self, config):
        valid_values = {"regressed", "stalled", "never"}
        assert config.rollback_on in valid_values


# ============================================================
# Run
# ============================================================

if __name__ == "__main__":
    pytest.main([__file__, "-v"])
