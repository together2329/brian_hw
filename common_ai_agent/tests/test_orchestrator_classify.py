from src.orchestrator.classify import HUMAN_ESCALATION, classify_failure


class TestExplicitOwner:
    def test_owner_from_sim_debug_dict(self):
        result = classify_failure(
            "sim_debug",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
        )
        assert result["owner"] == "rtl_bug"
        assert result["next_workflow"] == "rtl-gen"
        assert result["confidence"] == "high"

    def test_owner_from_sim_debug_list_uses_precedence(self):
        result = classify_failure(
            "sim_debug",
            evidence={
                "mismatch_classification": [
                    {"owner": "tb_bug"},
                    {"owner": "frontier"},
                    {"owner": "rtl_bug"},
                ]
            },
        )
        # frontier outranks tb_bug and rtl_bug in the precedence list
        assert result["owner"] == "frontier"
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_owner_field_direct(self):
        result = classify_failure(
            "sim", evidence={"owner": "tb_bug"}
        )
        assert result["owner"] == "tb_bug"
        assert result["next_workflow"] == "tb-gen"


class TestStageRules:
    def test_rtl_compile_error_routes_to_rtl_gen(self):
        result = classify_failure(
            "rtl",
            error_text="error: syntax error near 'always'",
        )
        assert result["owner"] == "compile_error"
        assert result["next_workflow"] == "rtl-gen"

    def test_lint_failure(self):
        result = classify_failure("lint")
        assert result["owner"] == "lint_violation"
        assert result["next_workflow"] == "rtl-gen"

    def test_sim_failure_routes_to_sim_debug(self):
        result = classify_failure("sim", error_text="scoreboard mismatch at cycle 42")
        assert result["next_workflow"] == "sim_debug"
        assert result["owner"] == "tb_bug"

    def test_coverage_gap(self):
        result = classify_failure("coverage")
        assert result["owner"] == "coverage_gap"
        assert result["next_workflow"] == "tb-gen"

    def test_sta_setup_failure(self):
        result = classify_failure(
            "sta",
            error_text="WNS -0.123 ns on path hclk@10ns",
        )
        assert result["owner"] == "timing_setup"
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_sta_hold_failure(self):
        result = classify_failure(
            "sta",
            error_text="hold violation: min delay -0.05 ns",
        )
        assert result["owner"] == "timing_hold"
        assert result["next_workflow"] == "rtl-gen"

    def test_ssot_gap_escalates(self):
        result = classify_failure("ssot")
        assert result["owner"] == "ssot_gap"
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_syn_failure_routes_to_rtl(self):
        result = classify_failure("syn", error_text="cannot infer latch")
        assert result["next_workflow"] == "rtl-gen"


class TestDefault:
    def test_unknown_stage_escalates(self):
        result = classify_failure("magic-stage-99")
        assert result["owner"] == "frontier"
        assert result["next_workflow"] == HUMAN_ESCALATION
        assert result["confidence"] == "low"

    def test_sim_debug_without_owner_escalates(self):
        result = classify_failure("sim_debug")
        assert result["next_workflow"] == HUMAN_ESCALATION
        assert result["owner"] == "frontier"
