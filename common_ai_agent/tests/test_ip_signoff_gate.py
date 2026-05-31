from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from pathlib import Path


REPO = Path(__file__).resolve().parents[1]
SCRIPT = REPO / "workflow" / "signoff" / "scripts" / "check_ip_signoff.py"


def _load_signoff_module():
    spec = importlib.util.spec_from_file_location("check_ip_signoff_under_test", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = module
    spec.loader.exec_module(module)
    return module


def _write_json(path: Path, payload: dict) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _make_ip(root: Path, ip: str, *, bad_provenance: bool = False, missing_observable: bool = False) -> Path:
    ip_dir = root / ip
    (ip_dir / "yaml").mkdir(parents=True)
    (ip_dir / "yaml" / f"{ip}.ssot.yaml").write_text(
        "\n".join(
            [
                "top_module:",
                f"  name: {ip}",
                "io_list:",
                "  ports: []",
                "function_model:",
                "  transactions: []",
                "cycle_model:",
                "  pipeline: []",
                "",
            ]
        ),
        encoding="utf-8",
    )
    _write_json(ip_dir / "model" / "fl_model_check.json", {"passed": True})
    _write_json(ip_dir / "model" / "cl_model_check.json", {"passed": True, "self_check": {"passed": True}})
    _write_json(
        ip_dir / "verify" / "equivalence_goals.json",
        {
            "goals": [
                {
                    "goal_id": "EQ_1",
                    "blocked": False,
                    "expected_contract": {"observables": ["x", *([] if not missing_observable else ["y"])]},
                }
            ]
        },
    )
    _write_json(
        ip_dir / "verify" / "ip_contract.json",
        {
            "schema_version": 1,
            "type": "ip_evidence_contract",
            "generation": "derived_from_ip_artifacts_not_static_profile",
            "ip": ip,
            "capabilities": [{"id": "interface_protocol", "sources": ["io_list"], "evidence": ["test"]}],
            "observability": {"required_rtl_observed": ["x"], "debug_optional": [], "sources": ["test"]},
            "required_monitors": [{"id": "clock_reset_monitor", "required": True}],
            "required_mutations": [{"id": "operator_flip", "required": True}],
            "required_evidence": [
                {"id": "ssot", "required": True},
                {"id": "fl_equivalence", "required": True},
                {"id": "cl_contract", "required": True},
                {"id": "equivalence_goals", "required": True},
                {"id": "rtl_compile", "required": True},
                {"id": "dut_lint", "required": True},
                {"id": "tb_python_compile", "required": True},
                {"id": "simulation", "required": True},
                {"id": "scoreboard_schema", "required": True},
                {"id": "coverage", "required": True},
            ],
            "policy": {
                "locked_truth_changes_require_human": True,
                "no_static_profile_selection": True,
                "mutation_enforcement_requires_human_policy": True,
            },
        },
    )
    todo = {
        "gate": {
            "status": "pass",
            "all_required_todos_pass": True,
            "blocking_questions": 0,
            "orphan_tasks": 0,
            "open_required_todos": 0,
            "static_missing": 0,
        },
        "tasks": [],
    }
    _write_json(ip_dir / "rtl" / "rtl_todo_plan.json", todo)
    signoff_module = _load_signoff_module()
    todo_hash = signoff_module._stable_json_sha256(ip_dir / "rtl" / "rtl_todo_plan.json")
    _write_json(
        ip_dir / "rtl" / "rtl_authoring_provenance.json",
        {
            "type": "rtl_authoring_provenance",
            "agent": "common_ai_agent",
            "workflow": "rtl-gen",
            "surface": "headless_common_engine",
            "todo_plan_sha256": "bad-hash" if bad_provenance else todo_hash,
            "rtl_files": [f"rtl/{ip}.sv"],
        },
    )
    _write_json(
        ip_dir / "rtl" / "rtl_compile.json",
        {"passed": True, "dut_only": True, "errors": 0, "diagnostics": 0, "style_violations": 0},
    )
    _write_json(
        ip_dir / "lint" / "dut_lint.json",
        {
            "passed": True,
            "dut_only": True,
            "errors": 0,
            "warnings": 0,
            "suppression_violation_count": 0,
            "style_violation_count": 0,
            "waived_warnings": 0,
        },
    )
    _write_json(
        ip_dir / "tb" / "cocotb" / "tb_py_compile.json",
        {"passed": True, "errors": [], "files": [f"{ip}/tb/cocotb/test_{ip}.py"]},
    )
    (ip_dir / "sim").mkdir(parents=True)
    (ip_dir / "sim" / "results.xml").write_text(
        '<testsuite tests="1" failures="0" errors="0"><testcase name="smoke"/></testsuite>\n',
        encoding="utf-8",
    )
    (ip_dir / "sim" / "sim_report.txt").write_text("TESTS=1 PASS=1 FAIL=0\n", encoding="utf-8")
    (ip_dir / "sim" / "scoreboard_events.jsonl").write_text(
        json.dumps(
            {
                "goal_id": "EQ_1",
                "scenario_id": "SC_1",
                "cycle": 0,
                "stimulus": {"kind": "READ"},
                "fl_expected": {"model_api": "FunctionalModel.apply", "model_result": {"x": 1}},
                "rtl_observed": {"x": 1},
                "passed": True,
                "mismatch": "",
                "coverage_refs": ["bin_1"],
            },
            sort_keys=True,
        )
        + "\n",
        encoding="utf-8",
    )
    _write_json(ip_dir / "cov" / "coverage.json", {"status": "pass", "limitations": []})
    _write_json(
        ip_dir / "signoff" / "goal_ledger.json",
        {"status": "approved_by_local_evidence", "human_review_needed": [], "known_waivers": []},
    )
    return ip_dir


def test_ip_signoff_gate_passes_complete_local_evidence(tmp_path: Path) -> None:
    _make_ip(tmp_path, "ok_ip")

    result = subprocess.run(
        ["python3", str(SCRIPT), "ok_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = json.loads((tmp_path / "ok_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    assert report["status"] == "pass"
    assert report["summary"]["failed"] == 0
    assert report["summary"]["blocked"] == 0


def test_ip_signoff_gate_rejects_stale_rtl_provenance(tmp_path: Path) -> None:
    _make_ip(tmp_path, "bad_ip", bad_provenance=True)

    result = subprocess.run(
        ["python3", str(SCRIPT), "bad_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / "bad_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    assert report["status"] == "fail"
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["rtl_provenance"]["status"] == "fail"
    assert "todo_plan_sha256" in "; ".join(gates["rtl_provenance"]["issues"])


def test_ip_signoff_gate_requires_derived_ip_contract(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "missing_contract_ip")
    (ip_dir / "verify" / "ip_contract.json").unlink()

    result = subprocess.run(
        ["python3", str(SCRIPT), "missing_contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / "missing_contract_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["ip_contract"]["status"] == "fail"
    assert "missing" in "; ".join(gates["ip_contract"]["issues"])


def test_ip_signoff_gate_rejects_scoreboard_missing_expected_observable(tmp_path: Path) -> None:
    _make_ip(tmp_path, "bad_scoreboard_ip", missing_observable=True)

    result = subprocess.run(
        ["python3", str(SCRIPT), "bad_scoreboard_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / "bad_scoreboard_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["scoreboard"]["status"] == "fail"
    assert "y" in "; ".join(gates["scoreboard"]["issues"])
