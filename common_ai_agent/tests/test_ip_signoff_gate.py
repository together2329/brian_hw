from __future__ import annotations

import importlib.util
import json
import subprocess
import sys
from collections.abc import Mapping
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


def _write_json(path: Path, payload: Mapping[str, object]) -> None:
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
    _write_json(
        ip_dir / "sim" / "simulation_quality.json",
        {"status": "pass", "summary": {"issues": 0}, "issues": []},
    )
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
        ip_dir / "signoff" / "truth_coverage.json",
        {
            "schema_version": 1,
            "type": "truth_coverage",
            "status": "pass",
            "source_mode": "direct_ssot",
            "summary": {"obligations": 1, "covered": 1, "uncovered_required": 0},
            "uncovered_required": [],
        },
    )
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


def test_ip_signoff_gate_requires_truth_coverage(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "missing_truth_ip")
    (ip_dir / "signoff" / "truth_coverage.json").unlink()

    result = subprocess.run(
        ["python3", str(SCRIPT), "missing_truth_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / "missing_truth_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["truth_coverage"]["status"] == "fail"
    assert "missing" in "; ".join(gates["truth_coverage"]["issues"])


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


def _clean_mutation_artifact() -> dict[str, object]:
    return {
        "type": "mutation_contract_check",
        "schema_version": 1,
        "ip": "x",
        "status": "pass",
        "tools": {"yosys": "Yosys 0.64", "sby": "0.40", "z3": "4.15.4", "verilator": "5.046"},
        "correct": {"verilator": "PASS", "formal": "PASS"},
        "targeted": {
            "total": 2,
            "killed": 2,
            "survivors": [],
            "all_killed": True,
            "contracts": [
                {"id": "C-1", "inject": "INJECT_A_BUG", "verilator": "ASSERT_FAIL", "formal": "FAIL", "killed": True},
                {"id": "C-2", "inject": "INJECT_B_BUG", "verilator": "ASSERT_FAIL", "formal": "FAIL", "killed": True},
            ],
        },
        "blanket": {
            "embedded_kill_rate": 0.9,
            "embedded_killed": 9,
            "scored": 10,
            "survivors": 1,
            "survivors_equivalent": 1,
            "survivors_sec_caught": 0,
            "survivors_unknown": 0,
            "all_survivors_classified": True,
            "survivor_list": [{"mode": "const1", "src": "rtl/x.sv:40", "embedded": "PASS", "sec": "equivalent"}],
        },
        "gate": {
            "correct_clean": True,
            "targeted_all_killed": True,
            "blanket_all_survivors_classified": True,
            "pass": True,
        },
    }


def test_ip_signoff_gate_contract_mutation_not_applicable_when_absent(tmp_path: Path) -> None:
    # Backward compatible: an IP with no mutation/contract_mutation.json still signs off.
    _make_ip(tmp_path, "no_mut_ip")
    result = subprocess.run(
        ["python3", str(SCRIPT), "no_mut_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    report = json.loads((tmp_path / "no_mut_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "pass"
    assert "not run" in gates["contract_mutation"]["summary"] + "".join(gates["contract_mutation"]["issues"])


def test_ip_signoff_gate_contract_mutation_passes_clean_artifact(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "mut_ok_ip")
    _write_json(ip_dir / "mutation" / "contract_mutation.json", _clean_mutation_artifact())
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_ok_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 0, result.stdout
    report = json.loads((tmp_path / "mut_ok_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "pass", gates["contract_mutation"]


def test_ip_signoff_gate_contract_mutation_rejects_unclassified_survivor(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "mut_unknown_ip")
    art = _clean_mutation_artifact()
    art["blanket"]["survivors_unknown"] = 1  # type: ignore[index]
    art["blanket"]["all_survivors_classified"] = False  # type: ignore[index]
    _write_json(ip_dir / "mutation" / "contract_mutation.json", art)
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_unknown_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "mut_unknown_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "fail"
    assert "unclassified survivor" in "; ".join(gates["contract_mutation"]["issues"])


def test_ip_signoff_gate_contract_mutation_rejects_targeted_survivor(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "mut_targeted_ip")
    art = _clean_mutation_artifact()
    art["targeted"]["contracts"][1]["killed"] = False  # a real surviving contract row  # type: ignore[index]
    art["targeted"]["killed"] = 1  # type: ignore[index]
    art["targeted"]["all_killed"] = False  # type: ignore[index]
    art["targeted"]["survivors"] = ["C-2"]  # type: ignore[index]
    _write_json(ip_dir / "mutation" / "contract_mutation.json", art)
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_targeted_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "mut_targeted_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "fail"
    assert "surviving mutants" in "; ".join(gates["contract_mutation"]["issues"])


def test_ip_signoff_gate_contract_mutation_rejects_missing_blanket(tmp_path: Path) -> None:
    # The blanket (SEC-classified sweep) section is the hard evidence; a targeted-only
    # artifact must NOT pass — this was the hand-forge seam the reviewer flagged.
    ip_dir = _make_ip(tmp_path, "mut_noblanket_ip")
    art = _clean_mutation_artifact()
    del art["blanket"]
    _write_json(ip_dir / "mutation" / "contract_mutation.json", art)
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_noblanket_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "mut_noblanket_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "fail"
    assert "blanket axis is mandatory" in "; ".join(gates["contract_mutation"]["issues"])


def test_ip_signoff_gate_contract_mutation_rejects_inconsistent_survivor_counts(tmp_path: Path) -> None:
    # Scalars must be re-derivable from survivor_list[]; a forged "survivors_unknown:0"
    # with an actually-unknown row in the list must fail.
    ip_dir = _make_ip(tmp_path, "mut_forged_ip")
    art = _clean_mutation_artifact()
    art["blanket"]["survivor_list"] = [{"mode": "inv", "src": "rtl/x.sv:17", "embedded": "PASS", "sec": "unknown"}]  # type: ignore[index]
    art["blanket"]["survivors"] = 1  # type: ignore[index]
    art["blanket"]["survivors_unknown"] = 0  # type: ignore[index]  # lie
    art["blanket"]["survivors_equivalent"] = 1  # type: ignore[index]  # lie
    art["blanket"]["all_survivors_classified"] = True  # type: ignore[index]  # lie
    _write_json(ip_dir / "mutation" / "contract_mutation.json", art)
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_forged_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "mut_forged_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "fail"
    joined = "; ".join(gates["contract_mutation"]["issues"])
    assert "disagrees with survivor_list" in joined or "unclassified survivor" in joined


def test_ip_signoff_gate_contract_mutation_rejects_missing_tools(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "mut_notools_ip")
    art = _clean_mutation_artifact()
    art["tools"] = {"yosys": "unavailable", "sby": ""}  # type: ignore[index]
    _write_json(ip_dir / "mutation" / "contract_mutation.json", art)
    result = subprocess.run(
        ["python3", str(SCRIPT), "mut_notools_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )
    assert result.returncode == 1
    report = json.loads((tmp_path / "mut_notools_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["contract_mutation"]["status"] == "fail"
    assert "unavailable" in "; ".join(gates["contract_mutation"]["issues"])


def test_ip_signoff_gate_rejects_failed_simulation_quality(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "bad_quality_ip")
    _write_json(
        ip_dir / "sim" / "simulation_quality.json",
        {
            "status": "fail",
            "summary": {"issues": 1},
            "issues": ["SC_MAX: payload evidence 16 below expected 4096"],
        },
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "bad_quality_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    report = json.loads((tmp_path / "bad_quality_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["simulation_quality"]["status"] == "fail"
    assert "payload evidence" in "; ".join(gates["simulation_quality"]["issues"])


# ---------------------------------------------------------------------------
# Survivor-classification closure: per-survivor evidence, not summary counts.
# classify_survivors.py used to rubber-stamp status="pass" with
# classified==total_survivors unconditionally; the gates must re-derive the
# verdict from the entries themselves.
# ---------------------------------------------------------------------------

def _write_mutation_with_survivors(ip_dir, survivors) -> None:
    _write_json(
        ip_dir / "mutation" / "mutation_report.json",
        {
            "status": "pass",
            "summary": {"killed": 1, "survived": len(survivors), "invalid": 0, "kill_rate": 0.25},
            "results": [{"status": "survived", **row} for row in survivors],
        },
    )


def _rubber_stamp_classification(entries):
    # The exact shape classify_survivors.py used to emit: status pass, counts
    # equal, dispositions test_hole/irrelevant with canned prose, no evidence.
    return {
        "schema_version": 1,
        "type": "survivor_classification",
        "status": "pass",
        "summary": {
            "total_survivors": len(entries),
            "classified": len(entries),
            "equivalent": 0,
            "irrelevant": sum(1 for e in entries if e["disposition"] == "irrelevant"),
            "test_hole": sum(1 for e in entries if e["disposition"] == "test_hole"),
        },
        "survivors": entries,
    }


def test_mutation_guard_rejects_rubber_stamped_survivors(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "rubber_ip")
    _write_mutation_with_survivors(
        ip_dir,
        [
            {"id": "m1", "category": "operator_flip", "relpath": "rtl/x.sv", "preview": "because"},
            {"id": "m2", "category": "state_update_drop", "relpath": "rtl/y.sv", "preview": "junk"},
        ],
    )
    _write_json(
        ip_dir / "mutation" / "survivor_classification.json",
        _rubber_stamp_classification(
            [
                {"id": "m1", "category": "operator_flip", "disposition": "irrelevant",
                 "rationale": "canned text", "next_action": "review someday"},
                {"id": "m2", "category": "state_update_drop", "disposition": "test_hole",
                 "rationale": "uncovered behavior", "next_action": "add scenario"},
            ]
        ),
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "rubber_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    report = json.loads((tmp_path / "rubber_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["mutation_guard"]["status"] == "fail", (
        "rubber-stamped survivor classification (test_hole/irrelevant, no evidence, "
        "no waiver) must not satisfy the mutation_guard gate"
    )
    joined = "; ".join(gates["mutation_guard"]["issues"])
    assert "m1" in joined or "m2" in joined or "closure" in joined.lower() or "waiv" in joined.lower()


def test_mutation_guard_accepts_evidence_backed_or_waived_survivors(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "justified_ip")
    _write_mutation_with_survivors(
        ip_dir,
        [
            {"id": "m1", "category": "constant_flip", "relpath": "rtl/x.sv", "preview": "p"},
            {"id": "m2", "category": "operator_flip", "relpath": "rtl/y.sv", "preview": "q"},
        ],
    )
    _write_json(
        ip_dir / "mutation" / "survivor_classification.json",
        {
            "schema_version": 1,
            "type": "survivor_classification",
            "status": "needs_human_review",
            "summary": {"total_survivors": 2, "classified": 2, "equivalent": 1,
                        "irrelevant": 0, "test_hole": 1},
            "survivors": [
                {"id": "m1", "category": "constant_flip", "disposition": "equivalent",
                 "evidence_ref": "mutation/sec/m1_miter.log",
                 "rationale": "SEC miter proves functional equivalence"},
                {"id": "m2", "category": "operator_flip", "disposition": "test_hole",
                 "waived_by": "brian", "waiver_reason": "boundary expression covered by formal P_AXI lane; accepted for this release"},
            ],
        },
    )

    result = subprocess.run(
        ["python3", str(SCRIPT), "justified_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    report = json.loads((tmp_path / "justified_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["mutation_guard"]["status"] == "pass", gates["mutation_guard"]["issues"]


def test_verification_hardening_rejects_rubber_stamped_survivors(tmp_path: Path) -> None:
    ip_dir = _make_ip(tmp_path, "hardening_rubber_ip")
    # Full hardening artifact set so the ONLY defect is the rubber-stamped
    # classification (the real-world mctp shape).
    _write_json(
        ip_dir / "sim" / "scenario_e2e_summary.json",
        {"status": "pass", "total_directed_scenarios": 26, "missing_scenarios": [],
         "failed_scenarios": []},
    )
    _write_json(
        ip_dir / "sim" / "monitor_evidence.json",
        {"status": "pass", "checks": {
            "sram_payload_no_holes": True, "sram_payload_only": True,
            "sram_no_header_or_pad_write": True, "axi_write_protocol_pass": True,
            "axi_read_protocol_pass": True, "apb_per_q_readback_pass": True}},
    )
    _write_json(
        ip_dir / "verify" / "formal_status.json",
        {"status": "optional_not_run", "properties": [{"id": f"P{i}"} for i in range(5)]},
    )
    (ip_dir / "verify" / "safety_properties.sva").write_text("// props\n", encoding="utf-8")
    _write_json(
        ip_dir / "mutation" / "survivor_classification.json",
        _rubber_stamp_classification(
            [{"id": "m1", "category": "operator_flip", "disposition": "test_hole",
              "rationale": "uncovered", "next_action": "add scenario"}]
        ),
    )

    subprocess.run(
        ["python3", str(SCRIPT), "hardening_rubber_ip", "--root", str(tmp_path)],
        text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT,
    )

    report = json.loads((tmp_path / "hardening_rubber_ip" / "signoff" / "ip_signoff.json").read_text(encoding="utf-8"))
    gates = {gate["name"]: gate for gate in report["gates"]}
    assert gates["verification_hardening"]["status"] == "fail", (
        "verification_hardening must not accept unwaived test_hole survivors as classified"
    )
