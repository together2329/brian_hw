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

    def test_stale_oracle_classification_routes_to_fl_model_gen(self):
        result = classify_failure(
            "sim",
            evidence={
                "mismatch_classification": {
                    "classifications": [
                        {
                            "classification": "stale_oracle",
                            "owner": "fl-model-gen",
                            "reason": "derived FL/equivalence oracle artifacts are older than the current SSOT",
                        }
                    ]
                }
            },
        )
        assert result["owner"] == "fl-model-gen"
        assert result["next_workflow"] == "equivalence"
        assert result["confidence"] == "high"

    def test_stale_oracle_read_artifact_payload_routes_to_fl_model_gen(self):
        result = classify_failure(
            "sim",
            evidence={
                "artifacts": [
                    {
                        "data": {
                            "status": "action_required",
                            "classifications": [
                                {
                                    "classification": "stale_oracle",
                                    "owner": "fl-model-gen",
                                }
                            ],
                        }
                    }
                ]
            },
        )
        assert result["owner"] == "fl-model-gen"
        assert result["next_workflow"] == "equivalence"

    def test_fl_model_bug_owner_routes_to_fl_model_gen(self):
        result = classify_failure(
            "sim_debug",
            evidence={
                "mismatch_classification": {
                    "status": "action_required",
                    "classifications": [
                        {
                            "classification": "fl_model_bug",
                            "owner": "fl-model-gen",
                            "reason": "FunctionalModel.apply failed: unknown rule name COUNT",
                        }
                    ],
                }
            },
        )
        assert result["owner"] == "fl-model-gen"
        assert result["next_workflow"] == "equivalence"

    def test_stale_compare_artifact_overrides_embedded_stale_oracle(self):
        result = classify_failure(
            "sim",
            evidence={
                "artifacts": [
                    {
                        "rel": "sim/fl_rtl_compare.json",
                        "freshness_status": "stale_artifact",
                        "stale_against": [{"rel": "sim/scoreboard_events.jsonl"}],
                        "data": {
                            "status": "stale",
                            "classifications": [
                                {
                                    "classification": "stale_oracle",
                                    "owner": "fl-model-gen",
                                }
                            ],
                        },
                    }
                ]
            },
        )
        assert result["owner"] == "sim-debug"
        assert result["next_workflow"] == "sim_debug"

    def test_nested_sim_debug_artifacts_route_to_rtl_gen(self):
        result = classify_failure(
            "sim_debug",
            evidence={
                "sim_debug_artifacts": {
                    "fl_rtl_compare": {
                        "status": "fail",
                        "summary": {"stale_oracle_evidence": []},
                    },
                    "mismatch_classification": {
                        "status": "action_required",
                        "classifications": [
                            {
                                "classification": "rtl_bug",
                                "owner": "rtl-gen",
                            }
                        ],
                    },
                }
            },
        )
        assert result["owner"] == "rtl-gen"
        assert result["next_workflow"] == "rtl-gen"

    def test_classification_without_owner_routes_to_rtl_gen(self):
        result = classify_failure(
            "sim-debug",
            evidence={
                "mismatch_classification": {
                    "status": "action_required",
                    "classifications": [
                        {
                            "classification": "rtl_bug",
                            "reason": "RTL observed 0 when oracle expected 1",
                        }
                    ],
                }
            },
        )
        assert result["owner"] == "rtl_bug"
        assert result["next_workflow"] == "rtl-gen"


class TestStageRules:
    def test_rtl_compile_error_routes_to_rtl_gen(self):
        result = classify_failure(
            "rtl",
            error_text="error: syntax error near 'always'",
        )
        assert result["owner"] == "compile_error"
        assert result["next_workflow"] == "rtl-gen"

    def test_rtl_missing_filelist_routes_to_rtl_gen(self):
        result = classify_failure(
            "rtl",
            error_text=(
                "RTL validator failed: [check_rtl_disk] FAIL: "
                "filelist references missing file: rtl/demo.sv"
            ),
        )
        assert result["owner"] == "compile_error"
        assert result["next_workflow"] == "rtl-gen"
        assert result["confidence"] == "high"

    def test_rtl_llm_implementation_required_routes_to_rtl_gen(self):
        result = classify_failure(
            "rtl",
            error_text=(
                "demo/rtl/rtl_blocked.json LLM-authored RTL evidence is missing or stale.; "
                "questions=LLM_RTL_IMPLEMENTATION_REQUIRED; missing RTL files: rtl/demo.sv"
            ),
        )
        assert result["owner"] == "compile_error"
        assert result["next_workflow"] == "rtl-gen"
        assert result["confidence"] == "high"

    def test_rtl_stage_log_evidence_routes_to_rtl_gen(self):
        result = classify_failure(
            "rtl",
            evidence={
                "rtl_artifacts_read": {
                    "previews": [
                        {
                            "rel": "logs/stage_engine/ssot-rtl.json",
                            "headline": "[RTL RESULT] FAIL - LLM-authored RTL needs rtl-gen repair",
                            "metadata": {
                                "rtl_todo_gate": {
                                    "status": "fail",
                                    "open_required_todos": 4,
                                    "static_missing": 1,
                                }
                            },
                        }
                    ]
                }
            },
        )
        assert result["owner"] == "compile_error"
        assert result["next_workflow"] == "rtl-gen"
        assert result["confidence"] == "high"

    def test_rtl_contract_blocker_routes_to_ssot_gen(self):
        result = classify_failure(
            "rtl",
            error_text=(
                "rtl-gen BLOCKED: SSOT behavior is not concrete enough for "
                "production RTL implementation. RTL_MODULE_CONTRACTS required."
            ),
        )
        assert result["owner"] == "ssot_gap"
        assert result["next_workflow"] == "ssot-gen"
        assert result["confidence"] == "high"

    def test_rtl_dynamic_todo_ownership_routes_to_ssot_gen(self):
        result = classify_failure(
            "rtl",
            error_text=(
                "stage evidence failed: demo/rtl/rtl_blocked.json "
                "SSOT-derived dynamic RTL TODO gate is blocked; "
                "questions=RTL_DYNAMIC_TODO_OWNERSHIP,RTL_MODULE_CONTRACTS"
            ),
        )
        assert result["owner"] == "ssot_gap"
        assert result["next_workflow"] == "ssot-gen"
        assert result["confidence"] == "high"

    def test_lint_failure(self):
        result = classify_failure("lint")
        assert result["owner"] == "lint_violation"
        assert result["next_workflow"] == "rtl-gen"

    def test_sim_failure_routes_to_sim_debug(self):
        result = classify_failure("sim", error_text="scoreboard mismatch at cycle 42")
        assert result["next_workflow"] == "sim_debug"
        assert result["owner"] == "tb_bug"

    def test_sim_stale_oracle_text_routes_to_fl_model_gen(self):
        result = classify_failure(
            "sim",
            error_text=(
                "fl_rtl_compare.json status is stale; stale_oracle_evidence "
                "shows model/functional_model.py older than the current SSOT"
            ),
        )
        assert result["owner"] == "fl-model-gen"
        assert result["next_workflow"] == "equivalence"
        assert result["confidence"] == "high"

    def test_sim_stale_compare_text_routes_to_sim_debug(self):
        result = classify_failure(
            "sim",
            error_text="fl_rtl_compare.json older than sim/scoreboard_events.jsonl",
        )
        assert result["owner"] == "sim-debug"
        assert result["next_workflow"] == "sim_debug"
        assert result["confidence"] == "high"

    def test_empty_stale_oracle_evidence_key_does_not_route_to_equivalence(self):
        result = classify_failure(
            "sim_debug",
            error_text='fl_rtl_compare status=fail "stale_oracle_evidence": []',
        )
        assert result["owner"] == "frontier"
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_coverage_gap(self):
        result = classify_failure("coverage")
        assert result["owner"] == "coverage_gap"
        assert result["next_workflow"] == "tb-gen"

    def test_tb_missing_equivalence_goals_routes_to_equivalence(self):
        result = classify_failure(
            "tb",
            evidence={
                "tb_blocked": {
                    "questions": [
                        {
                            "id": "TB_GENERATOR_INPUT",
                            "evidence": "missing equivalence goals: /work/ip/verify/equivalence_goals.json",
                        }
                    ]
                }
            },
        )
        assert result["owner"] == "fl-model-gen"
        assert result["next_workflow"] == "equivalence"
        assert result["confidence"] == "high"

    def test_sta_setup_failure(self):
        result = classify_failure(
            "sta",
            error_text="WNS -0.123 ns on path hclk@10ns",
        )
        assert result["owner"] == "timing_setup"
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_sta_setup_failure_wins_over_hold_clean_context(self):
        result = classify_failure(
            "sta",
            evidence={
                "sta_out_wns": {
                    "clock": "clk",
                    "setup": {"wns": -1.29, "violations": 5},
                    "hold": {"wns": 0.14, "violations": 0},
                }
            },
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

    def test_syn_ssot_policy_gap_routes_to_ssot_gen(self):
        result = classify_failure(
            "syn",
            error_text=(
                "Synthesis worker status=error. [SSOT TBD REPORT] SSOT is "
                "missing required explicit synthesis technology/corner/library "
                "policy although SKY130_LIB and RTL filelist checks passed."
            ),
        )
        assert result["owner"] == "ssot_gap"
        assert result["next_workflow"] == "ssot-gen"
        assert result["confidence"] == "high"

    def test_pnr_failure_stays_in_pnr_loop(self):
        result = classify_failure(
            "pnr",
            error_text="[Error] command exited 127\n[PNR PREFLIGHT] openroad not found",
        )
        assert result["owner"] == "pnr_setup"
        assert result["next_workflow"] == "pnr"
        assert result["confidence"] == "medium"


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


class TestSilentFailDemotion:
    """Finding 38: a repair that wrote 0 files refutes its owner — don't loop."""

    def test_baseline_bare_mismatch_defaults_to_rtl_gen(self):
        # A pure value mismatch with no keyword still routes to rtl-gen by
        # default (unchanged behavior when nothing is excluded).
        result = classify_failure(
            "sim_debug",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
        )
        assert result["next_workflow"] == "rtl-gen"

    def test_excluded_owner_route_escalates(self):
        result = classify_failure(
            "sim_debug",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
            excluded_owners=["rtl-gen"],
        )
        assert result["next_workflow"] == HUMAN_ESCALATION
        assert result["owner"] == "frontier"
        assert result["refuted_owner"] == "rtl_bug"

    def test_excluded_owner_by_owner_name_escalates(self):
        # Excluding by the owner token (rtl_bug) also demotes.
        result = classify_failure(
            "sim_debug",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
            excluded_owners=["rtl_bug"],
        )
        assert result["next_workflow"] == HUMAN_ESCALATION

    def test_silent_fail_in_error_text_auto_demotes(self):
        # No explicit excluded_owners: the silent-fail signal in error_text is
        # parsed and the named workflow is demoted automatically.
        result = classify_failure(
            "sim",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
            error_text="silent-fail: workflow=rtl-gen ran 60 tool calls but wrote 0 files",
        )
        assert result["next_workflow"] == HUMAN_ESCALATION
        assert result["refuted_route"] == "rtl-gen"

    def test_unrelated_exclusion_does_not_change_route(self):
        # Excluding a workflow that is not the chosen route leaves it intact.
        result = classify_failure(
            "sim_debug",
            evidence={"mismatch_classification": {"owner": "rtl_bug"}},
            excluded_owners=["tb-gen"],
        )
        assert result["next_workflow"] == "rtl-gen"
