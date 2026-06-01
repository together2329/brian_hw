import json
import subprocess
import sys
from types import SimpleNamespace
from pathlib import Path

from fastapi.testclient import TestClient


PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))


def test_coverage_report_api_exposes_verilator_pyslang_vcd_and_fl_cl(tmp_path, monkeypatch):
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip_dir = tmp_path / "gpio" / "demo_ip"
    (ip_dir / "list").mkdir(parents=True)
    (ip_dir / "rtl").mkdir()
    (ip_dir / "cov").mkdir()
    (ip_dir / "sim").mkdir()
    (ip_dir / "list" / "demo_ip.f").write_text("rtl/demo_ip.sv\n", encoding="utf-8")
    (ip_dir / "rtl" / "demo_ip.sv").write_text(
        """module demo_ip(input logic clk, input logic rst_n, output logic done);
  always_ff @(posedge clk or negedge rst_n) begin
    if (!rst_n) done <= 1'b0;
    else done <= 1'b1;
  end
endmodule
""",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage.json").write_text(
        json.dumps({
            "source": "ssot_coverage_summary",
            "status": "blocked",
            "lines": {"hit": 1, "total": 2, "pct": 50.0, "target_pct": 90.0},
            "branches": {"hit": 1, "total": 2, "pct": 50.0, "target_pct": 80.0},
            "functions": {"hit": 1, "total": 1, "pct": 100.0},
            "function_coverage": {"hit": 1, "total": 2, "pct": 50.0, "target_pct": 100.0, "meets_target": False},
            "cycle_coverage": {"hit": 1, "total": 1, "pct": 100.0, "target_pct": 100.0, "meets_target": True},
            "functional_bins": {
                "fl.write": {"hit": True, "coverage_domain": "function", "description": "write scenario"},
                "fl.read": {"hit": False, "coverage_domain": "function", "description": "read scenario"},
                "cl.reset": {"hit": True, "coverage_domain": "cycle", "description": "reset cycle"},
            },
        }),
        encoding="utf-8",
    )
    (ip_dir / "cov" / "coverage.info").write_text(
        """TN:
SF:rtl/demo_ip.sv
FN:1,demo_ip
FNDA:1,demo_ip
FNF:1
FNH:1
DA:1,1
DA:2,0
LF:2
LH:1
BRDA:2,0,0,1
BRDA:2,0,1,0
BRF:2
BRH:1
end_of_record
""",
        encoding="utf-8",
    )
    (ip_dir / "cov" / "toggle.json").write_text(
        json.dumps({
            "vcd": "gpio/demo_ip/sim/demo_ip.vcd",
            "total_bits": 4,
            "toggled_bits": 2,
            "pct": 50.0,
            "nets": 3,
            "scopes": [
                {"scope": "demo_ip", "total": 4, "toggled": 2, "nets": 3, "pct": 50.0}
            ],
        }),
        encoding="utf-8",
    )
    (ip_dir / "sim" / "demo_ip.vcd").write_text("$date\nnow\n$end\n", encoding="utf-8")

    client = TestClient(atlas_ui.create_app())
    registered = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert registered.status_code == 200, registered.text

    response = client.get("/api/reports/cov", params={"ip": "demo_ip"})

    assert response.status_code == 200, response.text
    payload = response.json()
    assert payload["resolved_ip"] == "gpio/demo_ip"
    tools = {tool["id"]: tool for tool in payload["tools"]}
    assert set(tools) == {"verilator", "pyslang", "sim-vcd", "functional-fl", "functional-cl"}
    assert tools["verilator"]["metrics"][0]["hit"] == 1
    assert tools["verilator"]["metrics"][0]["total"] == 2
    assert tools["sim-vcd"]["metrics"][0]["pct"] == 50.0
    assert tools["functional-fl"]["metrics"][0]["hit"] == 1
    assert tools["functional-fl"]["metrics"][0]["total"] == 2
    assert tools["functional-fl"]["missing_bins"][0]["id"] == "fl.read"
    assert payload["static"]["metrics"]["modules"] == 1
    assert payload["vcd_paths"] == ["gpio/demo_ip/sim/demo_ip.vcd"]


def test_coverage_report_api_runs_selected_vcd_path(tmp_path, monkeypatch):
    import src.atlas_api_coverage_report as coverage_api
    import src.atlas_ui as atlas_ui

    monkeypatch.setenv("HOME", str(tmp_path / "home"))
    monkeypatch.setenv("ATLAS_DB_PATH", str(tmp_path / "atlas.db"))
    monkeypatch.setenv("ATLAS_MULTI_USER_PROC", "0")
    monkeypatch.chdir(tmp_path)
    monkeypatch.setattr(atlas_ui, "PROJECT_ROOT", tmp_path)

    ip_dir = tmp_path / "gpio" / "demo_ip"
    (ip_dir / "cov").mkdir(parents=True)
    (ip_dir / "sim" / "nested").mkdir(parents=True)
    (ip_dir / "tb").mkdir()
    (ip_dir / "sim" / "demo_ip.vcd").write_text("$date\nbase\n$end\n", encoding="utf-8")
    (ip_dir / "tb" / "capture.vcd").write_text("$date\ntb\n$end\n", encoding="utf-8")
    selected_vcd = ip_dir / "sim" / "nested" / "alt.vcd"
    selected_vcd.write_text("$date\nalt\n$end\n", encoding="utf-8")

    calls = []

    def fake_run(cmd, *, cwd, text, encoding, errors, stdout, stderr, timeout):
        calls.append(cmd)
        assert cwd == tmp_path
        assert text is True
        assert encoding == "utf-8"
        assert errors == "replace"
        assert stdout is coverage_api.subprocess.PIPE
        assert stderr is coverage_api.subprocess.STDOUT
        assert timeout == 180
        (ip_dir / "cov" / "toggle.json").write_text(
            json.dumps({
                "vcd": "gpio/demo_ip/sim/nested/alt.vcd",
                "total_bits": 2,
                "toggled_bits": 2,
                "pct": 100.0,
                "nets": 1,
                "scopes": [],
            }),
            encoding="utf-8",
        )
        return SimpleNamespace(returncode=0, stdout="ok")

    monkeypatch.setattr(coverage_api.subprocess, "run", fake_run)

    client = TestClient(atlas_ui.create_app())
    registered = client.post("/api/auth/register", json={"username": "u", "password": "pw"})
    assert registered.status_code == 200, registered.text

    response = client.get(
        "/api/reports/cov",
        params={
            "ip": "demo_ip",
            "vcd": "1",
            "vcd_path": "gpio/demo_ip/sim/nested/alt.vcd",
        },
    )

    assert response.status_code == 200, response.text
    payload = response.json()
    assert calls
    assert calls[0][-2:] == ["--vcd", "gpio/demo_ip/sim/nested/alt.vcd"]
    assert payload["toggle"]["vcd"] == "gpio/demo_ip/sim/nested/alt.vcd"
    assert payload["selected_vcd_path"] == "gpio/demo_ip/sim/nested/alt.vcd"
    assert "gpio/demo_ip/tb/capture.vcd" in payload["vcd_paths"]


def test_coverage_vcd_toggle_rejects_selected_vcd_outside_dut(tmp_path: Path):
    ip_dir = tmp_path / "demo_ip"
    ip_dir.mkdir()
    outside_vcd = tmp_path / "other.vcd"
    outside_vcd.write_text("$date\noutside\n$end\n", encoding="utf-8")
    script = PROJECT_ROOT / "workflow" / "coverage" / "scripts" / "coverage_vcd_toggle.sh"

    result = subprocess.run(
        ["bash", str(script), "demo_ip", "--vcd", str(outside_vcd), "--json"],
        cwd=tmp_path,
        text=True,
        encoding="utf-8",
        errors="replace",
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        timeout=30,
        check=False,
    )

    assert result.returncode == 1
    assert "outside DUT" in result.stdout
