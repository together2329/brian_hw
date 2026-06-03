from __future__ import annotations

import subprocess
from pathlib import Path

from src.orchestrator import tools as orch_tools
from src.workflow_stage_engine import WorkflowStageEngine, canonical_stage

from .contract_reflection_helpers import CONTRACT_CHECK_SCRIPT, make_contract_ip, read_json, write_json, write_rows


def _write_stage_artifacts(ip_dir: Path) -> None:
    for rel in (
        "yaml/contract_ip.ssot.yaml",
        "model/functional_model.py",
        "model/cycle_model.py",
        "rtl/contract_ip.sv",
        "tb/cocotb/test_contract_ip.py",
    ):
        path = ip_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text("// marker\n" if rel.endswith(".sv") else "# marker\n", encoding="utf-8")
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n"
        "$var wire 17 @ sram_wr_strb [16:0] $end\n"
        "#0\nb10001 !\nb11111111111111111 @\n",
        encoding="utf-8",
    )
    write_json(
        ip_dir / "verify" / "contract_reflection.json",
        {
            "contract_refs": [
                {
                    "contract_ref": "STATE_PAYLOAD_COUNT",
                    "fl": {"path": "model/functional_model.py"},
                    "cl": {"path": "model/cycle_model.py"},
                    "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                    "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                    "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                    "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
                }
            ],
            "schema_version": 1,
            "type": "contract_reflection",
        },
    )


def test_contract_check_command_passes_closed_contract_fixture(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)

    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    assert "Contract Check: PASS" in result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] == "pass"
    assert report["summary"] == {
        "evidence_failed": 0,
        "evidence_passed": 1,
        "evidence_total": 1,
        "reflection_failed": 0,
        "reflection_passed": 1,
        "reflection_total": 1,
    }


def test_contract_check_routes_missing_observable_to_tb_gen(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [{"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True, "rtl_observed": {"sram_wr_strb": 0x1FFFF}}],
    )

    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "Contract Check: BLOCKED" in result.stdout
    assert "Owner: tb-gen" in result.stdout
    route = read_json(ip_dir / "signoff" / "contract_owner_routing.json")
    assert route["owner_workflow"] == "tb-gen"
    assert "tb-gen" in str(route["suggested_commands"])


def test_contract_check_rejects_stale_pass_when_child_checker_fails(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    first = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert first.returncode == 0, first.stdout
    (ip_dir / "verify" / "evidence_contract.json").unlink()

    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "Contract Check: PASS" not in result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] != "pass"


def test_contract_check_treats_malformed_cached_signoff_as_missing(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    (ip_dir / "verify" / "contract_reflection.json").unlink()
    malformed = ip_dir / "signoff" / "contract_reflection_coverage.json"
    malformed.parent.mkdir(parents=True, exist_ok=True)
    _ = malformed.write_text("{not-json", encoding="utf-8")

    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "Traceback" not in result.stdout
    assert "Contract Check: PASS" not in result.stdout


def test_contract_check_stage_engine_runs_same_serial_gate(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)

    result = WorkflowStageEngine(tmp_path).run_stage("contract-check", "contract_ip")

    assert result.status == "pass", result.message
    assert canonical_stage("contract") == "contract-check"
    assert (ip_dir / "logs" / "stage_engine" / "contract-check.json").is_file()
    assert (ip_dir / "signoff" / "contract_check.json").is_file()


def test_orchestrator_read_artifact_exposes_contract_check_reports(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout

    payload, summary = orch_tools.read_artifact(ip="contract_ip", stage="contract-check", project_root=tmp_path)

    assert payload["ok"] is True
    assert any(item["rel"] == "signoff/contract_check.json" and item["exists"] for item in payload["artifacts"])
    assert "contract_check.json" in summary
    assert "evidence_contract_coverage.json" in summary
