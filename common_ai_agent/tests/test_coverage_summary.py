from __future__ import annotations

import importlib.util
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
