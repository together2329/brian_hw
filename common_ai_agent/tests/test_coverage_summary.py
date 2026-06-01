from __future__ import annotations

import importlib.util
import json
import sys
from pathlib import Path


def _load_module():
    path = Path(__file__).resolve().parents[1] / "workflow" / "coverage" / "scripts" / "ssot_coverage_summary.py"
    spec = importlib.util.spec_from_file_location(f"ssot_coverage_summary_test_{id(path)}", path)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def test_parse_lcov_counts_verilator_da_and_brda_records(tmp_path: Path):
    cov = _load_module()
    info = tmp_path / "coverage.info"
    info.write_text(
        "\n".join(
            [
                "TN:verilator_coverage",
                "SF:/tmp/dut.sv",
                "DA:10,0",
                "DA:11,3",
                "BRDA:11,0,0,0",
                "BRDA:11,0,1,2",
                "BRDA:12,0,0,-",
                "BRF:3",
                "BRH:0",
                "FN:20,do_work",
                "FNDA:7,do_work",
                "FNF:1",
                "FNH:0",
                "end_of_record",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = cov.parse_lcov(info)

    assert parsed["lines"] == {"hit": 1, "total": 2, "pct": 50.0}
    assert parsed["branches"] == {"hit": 1, "total": 3, "pct": 33.33}
    assert parsed["functions"] == {"hit": 1, "total": 1, "pct": 100.0}


def test_threshold_for_metric_handles_combined_line_branch_goal():
    cov = _load_module()
    goal = "line >= 90%, branch >= 85%"

    assert cov.threshold_for_metric(goal, ("line", "code")) == 90.0
    assert cov.threshold_for_metric(goal, ("branch",)) == 85.0


def test_main_waives_uninstrumented_lcov_when_rtl_observed_bins_close(tmp_path: Path, monkeypatch):
    cov = _load_module()
    ip_dir = tmp_path / "counter_ip"
    for subdir in ("yaml", "cov", "verify", "sim"):
        (ip_dir / subdir).mkdir(parents=True)
    (ip_dir / "yaml" / "counter_ip.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                "  name: counter_ip",
                "test_requirements:",
                "  scenarios:",
                "    - id: SC_COUNT",
                "      name: count",
                "      stimulus: enable",
                "      expected: count increments",
                "      checker: FL-vs-RTL scoreboard",
                "  coverage_goals:",
                "    function:",
                "      target_pct: 100",
                "      bins:",
                "        - id: FCOV_COUNT",
                "          coverage_domain: function",
                "    cycle:",
                "      target_pct: 100",
                "      bins:",
                "        - id: CCOV_COUNT",
                "          coverage_domain: cycle",
                "    code: line >= 95%, branch >= 95%",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "fcov_plan.json").write_text(
        json.dumps(
            {
                "bins": [
                    {"id": "FCOV_COUNT", "coverage_domain": "function"},
                    {"id": "CCOV_COUNT", "coverage_domain": "cycle"},
                ]
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage_functional.json").write_text(
        json.dumps(
            {
                "status": "pass",
                "functional": {
                    "bins": {
                        "FCOV_COUNT": {"hit": True},
                        "CCOV_COUNT": {"hit": True},
                    }
                },
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        json.dumps({"goals": [{"goal_id": "EQ_COUNT", "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"]}]}) + "\n",
        encoding="utf-8",
    )
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_COUNT",
                "scenario_id": "SC_COUNT",
                "coverage_refs": ["FCOV_COUNT", "CCOV_COUNT"],
                "passed": True,
                "fl_expected": {"model_result": {"count": 1}},
                "rtl_observed": {"count": 1},
            }
        )
        + "\n",
        encoding="utf-8",
    )

    monkeypatch.setattr(sys, "argv", ["ssot_coverage_summary.py", str(ip_dir)])

    assert cov.main() == 0
    payload = json.loads((ip_dir / "cov" / "coverage.json").read_text(encoding="utf-8"))
    assert payload["status"] == "pass"
    assert payload["limitations"] == {}
    assert payload["waived_limitations"].keys() == {"line", "branch"}
    assert payload["lines"]["status"] == "not_instrumented"
    assert payload["lines"]["measured"] is False
    assert payload["lines"]["meets_target"] is True
    assert payload["branches"]["status"] == "not_instrumented"
    assert payload["branches"]["measured"] is False
    assert payload["branches"]["meets_target"] is True


def test_parse_lcov_filters_verilator_toggle_bins_from_branch_metric(tmp_path: Path):
    cov = _load_module()
    src = tmp_path / "dut.sv"
    src.write_text(
        "\n".join(
            [
                "module dut;",
                "  logic [31:0] sync_compare_xor;",
                "  assign y = sel ? a : b;",
                "  always_comb begin",
                "    if (valid && ready) begin",
                "      y = a;",
                "    end",
                "  end",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    info = tmp_path / "coverage.info"
    info.write_text(
        "\n".join(
            [
                "TN:verilator_coverage",
                f"SF:{src}",
                "DA:2,0",
                "DA:3,3",
                "DA:5,1",
                "BRDA:2,0,0,0",
                "BRDA:2,0,1,0",
                "BRDA:3,0,0,1",
                "BRDA:3,0,1,1",
                "BRDA:5,0,0,1",
                "BRDA:5,0,1,0",
                "end_of_record",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    parsed = cov.parse_lcov(info)

    assert parsed["lines"] == {"hit": 2, "total": 3, "pct": 66.67}
    assert parsed["branches"] == {"hit": 3, "total": 4, "pct": 75.0}


def test_scoreboard_coverage_adds_ssot_aliases_only_from_rtl_observed_pass_rows(tmp_path: Path):
    cov = _load_module()
    ip_dir = tmp_path / "cpu_ip"
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        '{"goals":[{"goal_id":"EQ_TRANSACTION_TX_LOAD_STORE","coverage_refs":["function_single_transfer_memory_access"]}]}\n',
        encoding="utf-8",
    )
    rows = [
        {
            "goal_id": "EQ_TRANSACTION_TX_LOAD_STORE",
            "scenario_id": "SC_TX_LOAD_STORE",
            "coverage_refs": ["function_single_transfer_memory_access"],
            "passed": True,
            "fl_expected": {
                "goal_id": "EQ_TRANSACTION_TX_LOAD_STORE",
                "title": "Transaction load/store",
                "model_result": {"transaction_id": "TX_LOAD_STORE", "transaction_name": "single_transfer_memory_access"},
                "transaction": {"kind": "TX_LOAD_STORE"},
            },
            "rtl_observed": {"d_htrans": 2, "d_hwrite": 1},
        },
        {
            "goal_id": "EQ_TIMING_ORDERING_1",
            "scenario_id": "SC_ORDER",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {
                "goal_id": "EQ_TIMING_ORDERING_1",
                "title": "Ordering rule ordering_1",
                "model_result": {"transaction_id": "TX_DECODE_EXEC"},
                "transaction": {"kind": "TX_DECODE_EXEC", "transaction_order": 1},
                "pass_criteria": ["RTL response order matches cycle_model ordering"],
            },
            "rtl_observed": {"i_htrans": 2, "i_haddr": 4},
        },
        {
            "goal_id": "EQ_SCENARIO_SC_IF_STALL",
            "scenario_id": "SC_IF_STALL",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {
                "goal_id": "EQ_SCENARIO_SC_IF_STALL",
                "title": "Scenario SC_IF_STALL: Instruction fetch backpressure",
                "model_result": {"transaction_id": "TX_DECODE_EXEC"},
                "transaction": {"kind": "TX_DECODE_EXEC", "i_hready": 0},
            },
            "rtl_observed": {"i_htrans": 2, "i_haddr": 0, "pc": 0},
        },
        {
            "goal_id": "EQ_BAD_COPY",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {"model_result": {"transaction_id": "TX_FAKE"}},
            "rtl_observed": {"model_result": {"transaction_id": "TX_FAKE"}},
        },
    ]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        "\n".join(__import__("json").dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = cov.scoreboard_coverage(ip_dir)
    bins = result["bins"]

    assert bins["function_single_transfer_memory_access"]["hit"] is True
    assert bins["fcov_tx_load_store"]["hit"] is True
    assert bins["fcov_tx_decode_exec"]["hit"] is True
    assert bins["ccov_pipeline_order"]["hit"] is True
    assert bins["ccov_if_stall"]["hit"] is True
    assert "fcov_tx_fake" not in bins


def test_scoreboard_coverage_aliases_fm_transactions_to_ssot_fcov_bins(tmp_path: Path):
    cov = _load_module()
    ip_dir = tmp_path / "mctp_ip"
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        '{"goals":[{"goal_id":"EQ_TRANSACTION_FM_ACCEPT_AXI_TLP","coverage_refs":["function_accept_one_axi4_write_burst_as_one_pcie_vdm_tlp"]}]}\n',
        encoding="utf-8",
    )
    rows = [
        {
            "goal_id": "EQ_TRANSACTION_FM_ACCEPT_AXI_TLP",
            "coverage_refs": ["function_accept_one_axi4_write_burst_as_one_pcie_vdm_tlp"],
            "passed": True,
            "fl_expected": {
                "model_result": {"transaction_id": "FM_ACCEPT_AXI_TLP"},
                "transaction": {"kind": "FM_ACCEPT_AXI_TLP"},
            },
            "rtl_observed": {"m_axi_awready": 1, "m_axi_wready": 1},
        },
        {
            "goal_id": "EQ_TRANSACTION_FM_PACKET_DROP",
            "coverage_refs": ["function_packet_drop_without_sram_payload_write"],
            "passed": True,
            "fl_expected": {
                "model_result": {"transaction_id": "FM_PACKET_DROP"},
                "transaction": {"kind": "FM_PACKET_DROP"},
            },
            "rtl_observed": {"debug_drop_pulse": 1, "sram_wr_valid": 0},
        },
        {
            "goal_id": "EQ_TRANSACTION_FM_ASSEMBLY_DROP",
            "coverage_refs": ["function_assembly_drop_without_descriptor_push"],
            "passed": True,
            "fl_expected": {
                "model_result": {"transaction_id": "FM_ASSEMBLY_DROP"},
                "transaction": {"kind": "FM_ASSEMBLY_DROP"},
            },
            "rtl_observed": {"ctx_error": 1, "descriptor_count": 0},
        },
        {
            "goal_id": "EQ_TRANSACTION_FM_AXI_READBACK_COPY",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {"model_result": {"transaction_id": "FM_AXI_READBACK"}},
            "rtl_observed": {"model_result": {"transaction_id": "FM_AXI_READBACK"}},
        },
    ]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = cov.scoreboard_coverage(ip_dir)
    bins = result["bins"]

    assert bins["fcov_accept_axi_tlp"]["hit"] is True
    assert bins["fcov_packet_drops"]["hit"] is True
    assert bins["fcov_assembly_drops"]["hit"] is True
    assert "fcov_axi_readback" not in bins


def test_scoreboard_coverage_aliases_cycle_evidence_to_ssot_ccov_bins(tmp_path: Path):
    cov = _load_module()
    ip_dir = tmp_path / "mctp_ip"
    (ip_dir / "verify").mkdir(parents=True)
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "verify" / "equivalence_goals.json").write_text(
        '{"goals":[{"goal_id":"EQ_PROTOCOL_AXI_WRITE_CHANNELS","coverage_refs":["cycle_axi_write_channels"]}]}\n',
        encoding="utf-8",
    )
    rows = [
        {
            "goal_id": "EQ_PROTOCOL_AXI_WRITE_CHANNELS",
            "coverage_refs": ["cycle_axi_write_channels", "cycle_axi_read_channels"],
            "passed": True,
            "fl_expected": {
                "ssot_refs": ["cycle_model.handshake_rules.axi_write_channels"],
                "model_result": {"transaction_id": "FM_ACCEPT_AXI_TLP"},
            },
            "rtl_observed": {"axi_awready": 1, "axi_wready": 1},
        },
        {
            "goal_id": "EQ_MODULE_MCTP_SRAM_ARBITER",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {
                "title": "Module mctp_sram_arbiter functionality equals FunctionalModel",
                "ssot_refs": ["cycle_model.arbitration", "cycle_model.handshake_rules.sram_ready_valid"],
            },
            "rtl_observed": {"sram_wr_ready": 1, "sram_rd_valid": 0},
        },
        {
            "goal_id": "EQ_MODULE_MCTP_AXI_WRITE_INGRESS",
            "coverage_refs": [],
            "passed": True,
            "fl_expected": {"ssot_refs": ["cycle_model.backpressure.backpressure_0"]},
            "rtl_observed": {"axi_wready": 0},
        },
        {
            "goal_id": "EQ_STATE_CONTEXT_FSM_IDLE_TO_ASSEMBLING_0",
            "coverage_refs": ["fsm_context_fsm_idle_to_assembling_0"],
            "passed": True,
            "fl_expected": {"title": "FSM transition context_fsm: IDLE -> ASSEMBLING"},
            "rtl_observed": {"ctx_state": 1},
        },
        {
            "goal_id": "EQ_SCENARIO_SC_MAX_TU_4096_129_BEATS",
            "coverage_refs": ["SC_MAX_TU_4096_129_BEATS_executed"],
            "passed": True,
            "fl_expected": {"title": "Scenario SC_MAX_TU_4096_129_BEATS: Maximum 4096B transmission unit"},
            "rtl_observed": {"ctx_payload_count": 4096},
        },
    ]
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        "\n".join(json.dumps(row) for row in rows) + "\n",
        encoding="utf-8",
    )

    result = cov.scoreboard_coverage(ip_dir)
    bins = result["bins"]

    assert bins["ccov_axi_handshakes"]["hit"] is True
    assert bins["ccov_sram_arbitration"]["hit"] is True
    assert bins["ccov_backpressure"]["hit"] is True
    assert bins["ccov_context_fsm"]["hit"] is True
    assert bins["ccov_max_tlp_beats"]["hit"] is True
