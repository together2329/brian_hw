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
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
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
