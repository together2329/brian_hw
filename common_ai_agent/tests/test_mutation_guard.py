from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "mutation" / "scripts" / "mutation_guard.py"


def test_mutation_guard_lists_deterministic_rtl_candidates(tmp_path: Path) -> None:
    ip_dir = tmp_path / "mut_ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "mut_ip.sv").write_text(
        "\n".join(
            [
                "module mut_ip(input logic a, input logic b, output logic y);",
                "  assign y = a ^ b;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "4"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "listed"
    assert report["summary"]["candidates"] >= 1
    assert any(candidate["rule"] == "xor_to_and" for candidate in report["candidates"])
    assert report["source_rels"] == ["rtl/mut_ip.sv"]


def test_mutation_guard_records_contract_mutation_obligations(tmp_path: Path) -> None:
    ip_dir = tmp_path / "contract_mut_ip"
    rtl_dir = ip_dir / "rtl"
    verify_dir = ip_dir / "verify"
    rtl_dir.mkdir(parents=True)
    verify_dir.mkdir(parents=True)
    (rtl_dir / "contract_mut_ip.sv").write_text(
        "module contract_mut_ip(input logic a, input logic b, output logic y);\n"
        "  assign y = a == b;\n"
        "endmodule\n",
        encoding="utf-8",
    )
    (verify_dir / "ip_contract.json").write_text(
        json.dumps(
            {
                "type": "ip_evidence_contract",
                "required_mutations": [
                    {"id": "comparator_flip", "required": True},
                    {"id": "handshake_hold_drop", "required": True},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "contract_mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "2"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    obligations = report["contract_mutation_obligations"]
    assert obligations["supported_by_current_guard"] == ["comparator_flip", "handshake_hold_drop"]
    assert obligations["unsupported_by_current_guard"] == []


def test_mutation_guard_prioritizes_contract_serial_mutations(tmp_path: Path) -> None:
    ip_dir = tmp_path / "serial_mut_ip"
    rtl_dir = ip_dir / "rtl"
    verify_dir = ip_dir / "verify"
    rtl_dir.mkdir(parents=True)
    verify_dir.mkdir(parents=True)
    (rtl_dir / "serial_mut_ip.sv").write_text(
        "\n".join(
            [
                "module serial_mut_ip(input logic sclk, input logic cpol, input logic [7:0] data_i, output logic cs_n, output logic mosi);",
                "  wire active_edge = sclk == cpol;",
                "  assign mosi = data_i[7];",
                "  assign cs_n = 1'b0;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (verify_dir / "ip_contract.json").write_text(
        json.dumps(
            {
                "type": "ip_evidence_contract",
                "required_mutations": [
                    {"id": "bit_order_flip", "required": True},
                    {"id": "serial_clock_edge_flip", "required": True},
                    {"id": "chip_select_polarity_flip", "required": True},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "serial_mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "3"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    categories = {candidate["category"] for candidate in report["candidates"]}
    assert {"bit_order_flip", "serial_clock_edge_flip", "chip_select_polarity_flip"} <= categories
    assert report["contract_mutation_obligations"]["unsupported_by_current_guard"] == []


def test_mutation_guard_prioritizes_ready_valid_contract_mutations(tmp_path: Path) -> None:
    ip_dir = tmp_path / "rv_mut_ip"
    rtl_dir = ip_dir / "rtl"
    verify_dir = ip_dir / "verify"
    rtl_dir.mkdir(parents=True)
    verify_dir.mkdir(parents=True)
    (rtl_dir / "rv_mut_ip.sv").write_text(
        "\n".join(
            [
                "module rv_mut_ip(input logic s_valid_i, input logic m_ready_i, input logic [1:0] level_q, output logic s_ready_o);",
                "  wire has_data = level_q != 2'd0;",
                "  wire full = level_q == 2'd2;",
                "  wire pop = has_data & m_ready_i;",
                "  wire push_allowed = ~full | pop;",
                "  wire push = s_valid_i & push_allowed;",
                "  assign s_ready_o = push_allowed;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (verify_dir / "ip_contract.json").write_text(
        json.dumps(
            {
                "type": "ip_evidence_contract",
                "required_mutations": [
                    {"id": "handshake_hold_drop", "required": True},
                    {"id": "state_update_drop", "required": True},
                ],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "rv_mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "4"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    categories = [candidate["category"] for candidate in report["candidates"]]
    assert categories
    assert set(categories) == {"handshake_hold_drop"}
    assert report["contract_mutation_obligations"]["unsupported_by_current_guard"] == []


def test_mutation_guard_prefers_nonliteral_state_updates_when_capped(tmp_path: Path) -> None:
    ip_dir = tmp_path / "state_mut_ip"
    rtl_dir = ip_dir / "rtl"
    verify_dir = ip_dir / "verify"
    rtl_dir.mkdir(parents=True)
    verify_dir.mkdir(parents=True)
    (rtl_dir / "state_mut_ip.sv").write_text(
        "\n".join(
            [
                "module state_mut_ip(input logic clk, input logic [7:0] data_i);",
                "  logic [7:0] q0_q;",
                "  logic [7:0] q1_q;",
                "  always @(posedge clk) begin",
                "    q0_q <= 8'd0;",
                "    q1_q <= data_i;",
                "  end",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (verify_dir / "ip_contract.json").write_text(
        json.dumps(
            {
                "type": "ip_evidence_contract",
                "required_mutations": [{"id": "state_update_drop", "required": True}],
            },
            indent=2,
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "state_mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "1"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["candidates"] == 1
    assert report["candidates"][0]["before"] == "data_i"


def test_mutation_guard_reports_category_kill_rates(tmp_path: Path) -> None:
    ip_dir = tmp_path / "cat_report_ip"
    rtl_dir = ip_dir / "rtl"
    tb_dir = ip_dir / "tb" / "cocotb"
    rtl_dir.mkdir(parents=True)
    tb_dir.mkdir(parents=True)
    (rtl_dir / "cat_report_ip.sv").write_text(
        "\n".join(
            [
                "module cat_report_ip(input logic a, input logic b, output logic y);",
                "  assign y = a ^ b;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tb_dir / "test_runner.py").write_text(
        "from pathlib import Path\n"
        "Path(__file__).resolve().parents[2].joinpath('sim').mkdir(exist_ok=True)\n"
        "raise SystemExit(0)\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "cat_report_ip", "--root", str(tmp_path), "--max-mutants", "1"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["summary"]["executed"] == 1
    assert report["category_summary"] == [
        {
            "category": "operator_flip",
            "executed": 1,
            "killed": 0,
            "survived": 1,
            "invalid": 0,
            "kill_rate": 0.0,
        }
    ]
    markdown = (ip_dir / "mutation" / "mutation_report.md").read_text(encoding="utf-8")
    assert "## Category Kill Rate" in markdown
    assert "| `operator_flip` | 1 | 0 | 1 | 0 | `0.0` |" in markdown


def test_mutation_guard_blocks_when_baseline_compare_is_failing(tmp_path: Path) -> None:
    ip_dir = tmp_path / "baseline_fail_ip"
    rtl_dir = ip_dir / "rtl"
    sim_dir = ip_dir / "sim"
    tb_dir = ip_dir / "tb" / "cocotb"
    rtl_dir.mkdir(parents=True)
    sim_dir.mkdir(parents=True)
    tb_dir.mkdir(parents=True)
    (rtl_dir / "baseline_fail_ip.sv").write_text(
        "\n".join(
            [
                "module baseline_fail_ip(input logic a, input logic b, output logic y);",
                "  assign y = a ^ b;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (tb_dir / "test_runner.py").write_text("raise SystemExit(0)\n", encoding="utf-8")
    (sim_dir / "fl_rtl_compare.json").write_text(
        json.dumps({"status": "fail", "summary": {"failed": 1}}, indent=2) + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "baseline_fail_ip", "--root", str(tmp_path), "--max-mutants", "4"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    assert report["status"] == "blocked_baseline"
    assert report["summary"]["executed"] == 0
    assert report["baseline"]["status"] == "fail"
    assert report["category_summary"][0]["category"] == "operator_flip"
    assert report["category_summary"][0]["kill_rate"] is None
    markdown = (ip_dir / "mutation" / "mutation_report.md").read_text(encoding="utf-8")
    assert "baseline FL-vs-RTL compare is not green" in markdown


def test_mutation_guard_skips_noop_unused_evidence_lines(tmp_path: Path) -> None:
    ip_dir = tmp_path / "noop_mut_ip"
    rtl_dir = ip_dir / "rtl"
    rtl_dir.mkdir(parents=True)
    (rtl_dir / "noop_mut_ip.sv").write_text(
        "\n".join(
            [
                "module noop_mut_ip(input logic a, input logic b, output logic y);",
                "  assign unused_inputs = ^{a, b};",
                "  assign unused_descriptor_evidence = ^{a, b};",
                "  assign y = a ^ b;",
                "endmodule",
                "",
            ]
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "noop_mut_ip", "--root", str(tmp_path), "--list-only", "--max-mutants", "8"],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "mutation" / "mutation_report.json").read_text(encoding="utf-8"))
    previews = [candidate["preview"] for candidate in report["candidates"]]
    assert "assign y = a ^ b;" in previews
    assert all("unused_" not in preview and "evidence" not in preview for preview in previews)
