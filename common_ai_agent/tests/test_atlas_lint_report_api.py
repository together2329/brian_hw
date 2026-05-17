import json
import sys
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_lint_report_api_exposes_pyslang_and_verilator_results(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_MULTI_USER", "1")
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.setenv("ATLAS_ADMIN_AUTH_MODE", "db")
    monkeypatch.setenv("ATLAS_ADMIN_LOGIN_REQUIRED", "1")
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.delenv("ATLAS_LOCAL_ADMIN", raising=False)
    monkeypatch.delenv("ATLAS_ADMIN_BYPASS", raising=False)
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip_dir = tmp_path / "gpio" / "demo_ip"
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "lint").mkdir()
    (ip_dir / "list" / "demo_ip.f").write_text("rtl/demo_ip.sv\n", encoding="utf-8")
    (ip_dir / "lint" / "dut_lint.json").write_text(
        json.dumps({
            "type": "dut_lint",
            "scope": "dut",
            "dut_only": True,
            "tool": "pyslang+verilator",
            "command": "pyslang rtl/demo_ip.sv && verilator --lint-only -f list/demo_ip.f",
            "passed": True,
            "errors": 0,
            "warnings": 0,
            "tool_results": [
                {"tool": "pyslang", "passed": True, "returncode": 0, "errors": 0, "warnings": 0},
                {
                    "tool": "verilator",
                    "passed": True,
                    "returncode": 0,
                    "errors": 0,
                    "warnings": 0,
                    "diagnostics": [
                        {
                            "severity": "warning",
                            "file": "rtl/demo_ip.sv",
                            "line": 7,
                            "column": 3,
                            "message": "demo warning",
                        }
                    ],
                },
            ],
        }),
        encoding="utf-8",
    )

    client = TestClient(atlas_ui.create_app())
    registered = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert registered.status_code == 200, registered.text
    response = client.get("/api/lint/report", params={"ip": "demo_ip"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolved_ip"] == "gpio/demo_ip"
    assert payload["tool"] == "pyslang+verilator"
    assert payload["passed"] is True
    assert [row["tool"] for row in payload["tool_results"]] == ["pyslang", "verilator"]
    assert payload["tool_results"][1]["diagnostics"][0]["path"] == "gpio/demo_ip/rtl/demo_ip.sv"


def test_verilator_lint_parser_maps_warning_to_source_location():
    from workflow.lint.scripts import dut_lint_report

    output = """%Warning-UNUSEDSIGNAL: rtl/simple_gpio_lite.sv:4:15: Signal is not used: 'clk'
                                                   : ... note: In instance 'simple_gpio_lite'
    4 |   input  wire clk,
      |               ^~~
%Error: Exiting due to 1 warning(s)
"""

    diagnostics = dut_lint_report._parse_verilator_diagnostics(output)

    assert diagnostics == [
        {
            "severity": "warning",
            "rule": "UNUSEDSIGNAL",
            "file": "rtl/simple_gpio_lite.sv",
            "line": 4,
            "column": 15,
            "message": "Signal is not used: 'clk'",
            "source": "  input  wire clk,",
        }
    ]


def test_dut_lint_policy_allows_project_logic_subset(tmp_path):
    from workflow.lint.scripts import dut_lint_report

    ip_dir = tmp_path / "logic_subset_ip"
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "list").mkdir()
    (ip_dir / "rtl" / "logic_subset_ip.sv").write_text(
        "\n".join(
            [
                "module logic_subset_ip(",
                "    input logic clk,",
                "    input logic rst_n,",
                "    output logic done",
                ");",
                "  logic state_q;",
                "  always @(posedge clk or negedge rst_n) begin",
                "    if (!rst_n) state_q <= 1'b0;",
                "    else state_q <= 1'b1;",
                "  end",
                "  assign done = state_q;",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )
    entries = ["rtl/logic_subset_ip.sv"]

    assert dut_lint_report._style_violations(ip_dir, entries) == []


def test_dut_lint_report_entries_include_generated_param_headers(tmp_path):
    from workflow.lint.scripts import dut_lint_report

    ip_dir = tmp_path / "param_header_ip"
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "rtl" / "param_header_ip.sv").write_text(
        "module param_header_ip(input logic clk, output logic done); assign done = clk; endmodule\n",
        encoding="utf-8",
    )
    (ip_dir / "rtl" / "param_header_ip_param.vh").write_text(
        "`ifndef PARAM_HEADER_IP_PARAM_VH\n`define PARAM_HEADER_IP_PARAM_VH\n`define PARAM_WIDTH 8\n`endif\n",
        encoding="utf-8",
    )

    entries = dut_lint_report._report_rtl_entries(ip_dir, ["rtl/param_header_ip.sv"])

    assert entries == ["rtl/param_header_ip.sv", "rtl/param_header_ip_param.vh"]
    assert dut_lint_report._style_violations(ip_dir, entries) == []


def test_dut_lint_policy_still_rejects_nonportable_sv_constructs(tmp_path):
    from workflow.lint.scripts import dut_lint_report

    ip_dir = tmp_path / "bad_sv_ip"
    (ip_dir / "rtl").mkdir(parents=True)
    (ip_dir / "rtl" / "bad_sv_ip.sv").write_text(
        "\n".join(
            [
                "module bad_sv_ip(input logic clk, output logic done);",
                "  typedef enum logic [0:0] {S0, S1} state_e;",
                "  always_ff @(posedge clk) begin",
                "  end",
                "endmodule",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    rules = {item["rule"] for item in dut_lint_report._style_violations(ip_dir, ["rtl/bad_sv_ip.sv"])}

    assert "no_typedef_enum" in rules
    assert "no_always_ff_comb" in rules
