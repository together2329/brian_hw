from __future__ import annotations

import json
import subprocess
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "reqcov" / "scripts" / "check_truth_coverage.py"


def _write_json(path: Path, payload: dict[str, object]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _write_direct_ssot_ip(root: Path, ip: str) -> Path:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                "  name: direct_truth_ip",
                "io_list:",
                "  ports: []",
                "function_model:",
                "  transactions:",
                "    - id: FM_ACCEPT",
                "      name: Accept packet",
                "cycle_model:",
                "  pipeline: []",
                "error_handling:",
                "  error_sources:",
                "    - id: ERR_BAD_PACKET",
                "registers:",
                "  register_list:",
                "    - name: CTRL",
                "interrupts:",
                "  sources:",
                "    - id: IRQ_DONE",
                "test_requirements:",
                "  coverage_goals:",
                "    function:",
                "      bins:",
                "        - id: FCOV_ACCEPT",
                "          source_ref: function_model.transactions.FM_ACCEPT",
                "        - id: FCOV_BAD_PACKET",
                "          source_ref: error_handling.error_sources.ERR_BAD_PACKET",
                "  scenarios:",
                "    - id: SC_ACCEPT",
                "      coverage: [FCOV_ACCEPT, FCOV_BAD_PACKET]",
                "workflow_todos:",
                "  tb-gen:",
                "    - content: Observe direct SSOT behavior.",
                "      criteria:",
                "        - SC_ACCEPT_passes",
                "        - CTRL_observed",
                "        - IRQ_DONE_observed",
                "      source_refs:",
                "        - test_requirements.scenarios.SC_ACCEPT",
                "        - registers.register_list.CTRL",
                "        - interrupts.sources.IRQ_DONE",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_TRANSACTION_FM_ACCEPT",
                "scenario_id": "SC_ACCEPT",
                "coverage_refs": ["FCOV_ACCEPT", "FCOV_BAD_PACKET"],
                "passed": True,
                "rtl_observed": {"CTRL": 1, "IRQ_DONE": 1},
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(
        ip_dir / "cov" / "coverage.json",
        {
            "status": "pass",
            "function_coverage": {
                "bins": {
                    "SC_ACCEPT_executed": {"hit": True},
                    "FCOV_ACCEPT": {"hit": True},
                    "FCOV_BAD_PACKET": {"hit": True},
                }
            },
        },
    )
    return ip_dir


def test_truth_coverage_passes_with_direct_ssot_and_no_req_file(tmp_path: Path) -> None:
    ip = "direct_truth_ip"
    _write_direct_ssot_ip(tmp_path, ip)

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((tmp_path / ip / "signoff" / "truth_coverage.json").read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["source_mode"] == "direct_ssot"
    assert report["summary"]["uncovered_required"] == 0


def test_truth_coverage_fails_when_direct_ssot_obligation_has_no_evidence(tmp_path: Path) -> None:
    ip = "direct_truth_ip"
    ip_dir = _write_direct_ssot_ip(tmp_path, ip)
    text = (ip_dir / "yaml" / f"{ip}.ssot.yaml").read_text(encoding="utf-8")
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        text.replace(
            "    - id: ERR_BAD_PACKET\n",
            "    - id: ERR_BAD_PACKET\n    - id: ERR_TIMEOUT\n",
        ),
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / ip / "signoff" / "truth_coverage.json").read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    uncovered = {item["id"] for item in report["uncovered_required"]}
    assert "ERR_TIMEOUT" in uncovered


def test_truth_coverage_includes_optional_req_ledger_when_present(tmp_path: Path) -> None:
    ip = "ledger_truth_ip"
    ip_dir = _write_direct_ssot_ip(tmp_path, ip)
    _write_json(
        ip_dir / "req" / "requirement_coverage.json",
        {
            "requirements": [
                {"id": "REQ_AXI_256", "required": True, "evidence_refs": ["SC_ACCEPT"]},
                {"id": "REQ_UNPROVEN", "required": True, "evidence_refs": ["SC_MISSING"]},
            ]
        },
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / ip / "signoff" / "truth_coverage.json").read_text(encoding="utf-8"))
    assert report["source_mode"] == "ssot_plus_req_ledger"
    uncovered = {item["id"] for item in report["uncovered_required"]}
    assert "REQ_UNPROVEN" in uncovered


def test_truth_coverage_credits_structured_evidence_aliases(tmp_path: Path) -> None:
    ip = "structured_truth_ip"
    ip_dir = tmp_path / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                "  name: structured_truth_ip",
                "registers:",
                "  register_list:",
                "    - name: CTRL",
                "interrupts:",
                "  sources:",
                "    - id: IRQ_DONE",
                "      cause: done_count_increment",
                "    - id: IRQ_READ_ERROR",
                "      cause: read_error_count_increment",
                "test_requirements:",
                "  coverage_goals:",
                "    cycle:",
                "      bins:",
                "        - id: CCOV_LATENCY",
                "          source_ref: cycle_model.pipeline",
                "workflow_todos:",
                "  rtl-gen:",
                "    - content: Close implementation criteria.",
                "      criteria:",
                "        - rtl_compile_passes",
                "        - lint_passes",
                "        - axi_write_module_present",
                "        - all_required_modules_in_filelist",
                "        - no_missing_declared_module",
                "        - per_q_state_visible",
                "  fl-model-gen:",
                "    - content: Close model artifacts.",
                "      criteria:",
                "        - model/fl_model_check.json_passed",
                "        - cov/fcov_plan.json_created",
                "  ssot-gen:",
                "    - content: Close SSOT approval.",
                "      criteria:",
                "        - approval_manifest_hash_refreshed",
                "        - verify_ssot_signoff_passes",
                "  tb-gen:",
                "    - content: Close drop monitor evidence.",
                "      criteria:",
                "        - no_sram_write_on_drop",
                "",
            ]
        ),
        encoding="utf-8",
    )
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        "\n".join(
            [
                json.dumps({"goal_id": "EQ_REGISTER_CTRL", "passed": True, "rtl_observed": {"pready": 1}}),
                json.dumps({"goal_id": "EQ_INTERRUPT_IRQ_DONE", "passed": True, "rtl_observed": {"irq": 1}}),
                json.dumps(
                    {
                        "goal_id": "EQ_SCENARIO_SC_AXI_READBACK_TRIM",
                        "passed": True,
                        "fl_expected": {"model_result": {"state_updates": {"read_error_count": 1}}},
                        "rtl_observed": {"irq": 1},
                    }
                ),
                json.dumps(
                    {
                        "goal_id": "EQ_SCENARIO_PD_BAD_PACKET",
                        "passed": True,
                        "rtl_observed": {"debug_drop_pulse": 1, "sram_wr_valid": 0},
                    }
                ),
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(
        ip_dir / "cov" / "coverage.json",
        {
            "status": "pass",
            "cycle_coverage": {"bins": {"CCOV_LATENCY": {"hit": True}}},
        },
    )
    _write_json(ip_dir / "model" / "fl_model_check.json", {"source": "model/functional_model.py"})
    _write_json(ip_dir / "cov" / "fcov_plan.json", {"summary": {"total_bins": 1}})
    _write_json(ip_dir / "req" / "approval_manifest.json", {"source": "req/source_references.md"})
    _write_json(
        ip_dir / "rtl" / "rtl_todo_plan.json",
        {"gate": {"status": "pass", "criteria": ["DUT-only RTL compile report passes"]}},
    )
    _write_json(
        ip_dir / "signoff" / "ip_signoff.json",
        {
            "status": "fail",
            "gates": [
                {"name": "ssot", "status": "pass"},
                {"name": "rtl_compile", "status": "pass"},
                {"name": "lint", "status": "pass"},
                {"name": "truth_coverage", "status": "fail"},
            ],
        },
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), ip, "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((ip_dir / "signoff" / "truth_coverage.json").read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["summary"]["uncovered_required"] == 0
