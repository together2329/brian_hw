from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
CHECK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "check_locked_truth_bundle.py"
CONTRACT_CHECK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "check_contract_bundle.py"
DRAFT_TEMPLATE = ROOT / "workflow" / "default" / "todo_templates" / "draft-req.json"
FINALIZE_TEMPLATE = ROOT / "workflow" / "default" / "todo_templates" / "finalize-req.json"
LOCK_TEMPLATE = ROOT / "workflow" / "default" / "todo_templates" / "lock-req.json"
DRAFT_COMMAND = ROOT / "workflow" / "default" / "commands" / "draft-req.json"
FINALIZE_COMMAND = ROOT / "workflow" / "default" / "commands" / "finalize-req.json"
LOCK_COMMAND = ROOT / "workflow" / "default" / "commands" / "lock-req.json"


def _draft(ip: str) -> dict[str, Any]:
    return {
        "ip": ip,
        "requirements": [
            {
                "requirement_id": "REQ_TIMER_APB_001",
                "title": "APB3 register interface",
                "statement": "The timer shall expose an APB3-style 32-bit register interface.",
                "required": True,
                "obligation_refs": ["OBL_TIMER_APB_001"],
            }
        ],
        "obligations": [
            {
                "obligation_id": "OBL_TIMER_APB_001",
                "requirement_refs": ["REQ_TIMER_APB_001"],
                "statement": "The APB interface shall complete every valid access with OK response.",
                "contract_refs": ["C_TIMER_APB_IF"],
                "structural_contract_refs": ["C_STRUCT_TIMER_IO"],
                "behavioral_contract_refs": ["BC_TIMER_ACCESS"],
            }
        ],
        "contract_refs": [
            {
                "contract_ref_id": "C_TIMER_APB_IF",
                "title": "APB interface contract",
                "obligation_refs": ["OBL_TIMER_APB_001"],
                "stage_contracts": [
                    {"stage": "ssot", "check": "project structural and behavioral contracts into Design Spec"},
                    {"stage": "rtl", "artifact": "rtl/brian_timer.sv", "check": "implement locked APB contract"},
                ],
            }
        ],
        "behavioral_contracts": [
            {
                "id": "BC_TIMER_ACCESS",
                "type": "decision_table",
                "obligations": ["OBL_TIMER_APB_001"],
                "inputs": ["cmd_valid", "cmd_ready", "cmd_addr", "cmd_wdata"],
                "outputs": ["rsp_rdata"],
                "decision_table": [
                    {
                        "when": "cmd_valid == 1 and cmd_ready == 1",
                        "then": {"accept_cmd": 1, "rsp_rdata": "selected register value"},
                        "latency": {"min_cycles": 0, "max_cycles": 1},
                    }
                ],
                "cycle": {
                    "clock": "clk",
                    "reset": "rst_n",
                    "sample": "rising_edge",
                    "latency": {"accept_to_response_cycles": "0..1"},
                },
                "stage_contracts": [
                    {"stage": "ssot", "check": "function_model transaction mirrors decision_table"},
                    {"stage": "cycle_model", "check": "cycle_model latency mirrors contract cycle latency"},
                    {"stage": "sim", "validator": "check_evidence_contract.py"},
                ],
            }
        ],
        "structural_contracts": [
            {
                "id": "C_STRUCT_TIMER_IO",
                "type": "structural_top",
                "obligations": ["OBL_TIMER_APB_001"],
                "module": ip,
                "clock_domains": [{"id": "main_clk", "clock_signal": "clk"}],
                "reset_domains": [{"id": "main_rst", "reset_signal": "rst_n", "clock_domain": "main_clk"}],
                "interfaces": [
                    {
                        "id": "ctrl_if",
                        "kind": "bus",
                        "protocol": "custom",
                        "role": "slave",
                        "clock_domain": "main_clk",
                        "signals": ["cmd_valid", "cmd_ready", "cmd_addr", "cmd_wdata", "rsp_rdata"],
                    },
                    {"id": "event_in", "kind": "event", "role": "sink", "signals": ["ext_event"]},
                ],
                "signals": [
                    {"name": "clk", "dir": "input", "width": 1, "role": "clock"},
                    {"name": "rst_n", "dir": "input", "width": 1, "role": "reset"},
                    {"name": "cmd_valid", "dir": "input", "width": 1, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "cmd_ready", "dir": "output", "width": 1, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "cmd_addr", "dir": "input", "width": 12, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "cmd_wdata", "dir": "input", "width": 32, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "rsp_rdata", "dir": "output", "width": 32, "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    {"name": "ext_event", "dir": "input", "width": 1, "timing": {"kind": "async", "sync_to": "main_clk"}},
                ],
            }
        ],
        "evidence_plan": [
            {
                "evidence_id": "E_TIMER_APB_DIRECTED_001",
                "contract_ref": "C_TIMER_APB_IF",
                "artifact": "sim/scoreboard_events.jsonl",
                "validator": "check_evidence_contract.py",
                "pass_condition": "observed_apb_response == OK",
            },
            {
                "evidence_id": "E_TIMER_BEHAVIOR_001",
                "contract_ref": "BC_TIMER_ACCESS",
                "artifact": "sim/scoreboard_events.jsonl",
                "validator": "check_evidence_contract.py",
                "pass_condition": "accepted command rows match BC_TIMER_ACCESS decision table",
            },
            {
                "evidence_id": "E_TIMER_STRUCTURAL_001",
                "contract_ref": "C_STRUCT_TIMER_IO",
                "artifact": "rtl/rtl_todo_plan.json",
                "validator": "derive_rtl_todos.py --audit-rtl",
                "pass_condition": "top IO direction/width/timing matches C_STRUCT_TIMER_IO",
            }
        ],
    }


def _lock_bundle(tmp_path: Path, ip: str) -> None:
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(_draft(ip)), encoding="utf-8")
    result = subprocess.run(
        [
            sys.executable,
            str(LOCK_SCRIPT),
            ip,
            "--root",
            str(tmp_path),
            "--draft",
            str(draft_path),
            "--approved-by",
            "brian",
        ],
        check=False,
        text=True,
        capture_output=True,
    )
    assert result.returncode == 0, result.stderr


def _write_candidate_bundle(tmp_path: Path, ip: str) -> None:
    draft = _draft(ip)
    req_dir = tmp_path / ip / "req"
    req_dir.mkdir(parents=True)
    docs = {
        "requirements_index.json": {
            "schema_version": 1,
            "type": "requirements_index",
            "ip": ip,
            "requirements": draft["requirements"],
        },
        "obligations.json": {
            "schema_version": 1,
            "type": "obligations",
            "ip": ip,
            "obligations": draft["obligations"],
        },
        "contract_refs.json": {
            "schema_version": 1,
            "type": "contract_refs",
            "ip": ip,
            "contract_refs": draft["contract_refs"],
        },
        "structural_contracts.json": {
            "schema_version": 1,
            "type": "structural_contracts",
            "ip": ip,
            "contracts": draft["structural_contracts"],
        },
        "behavioral_contracts.json": {
            "schema_version": 1,
            "type": "behavioral_contracts",
            "ip": ip,
            "contracts": draft["behavioral_contracts"],
        },
        "evidence_plan.json": {
            "schema_version": 1,
            "type": "evidence_plan",
            "ip": ip,
            "evidence_plan": draft["evidence_plan"],
        },
    }
    for name, doc in docs.items():
        (req_dir / name).write_text(json.dumps(doc, indent=2, sort_keys=True), encoding="utf-8")


def _check(tmp_path: Path, ip: str, *, review_candidate: bool = False) -> subprocess.CompletedProcess[str]:
    command = [sys.executable, str(CHECK_SCRIPT), ip, "--root", str(tmp_path)]
    if review_candidate:
        command.append("--review-candidate")
    return subprocess.run(
        command,
        check=False,
        text=True,
        capture_output=True,
    )


def test_check_locked_truth_bundle_passes_writer_output(tmp_path: Path) -> None:
    ip = "brian_timer"
    _lock_bundle(tmp_path, ip)

    result = _check(tmp_path, ip)

    assert result.returncode == 0, result.stderr
    assert "[check_locked_truth_bundle] PASS brian_timer" in result.stdout
    assert "requirements=1" in result.stdout
    assert "structural_contracts=1" in result.stdout
    assert "behavioral_contracts=1" in result.stdout
    assert "evidence=3" in result.stdout
    closure = json.loads((tmp_path / ip / "req" / "contract_closure.json").read_text(encoding="utf-8"))
    assert closure["status"] == "pass"
    assert closure["summary"]["required_closed"] == 3
    assert (tmp_path / ip / "req" / "contract_authority_report.json").is_file()


def test_check_locked_truth_bundle_rejects_corrupt_manifest_hash(tmp_path: Path) -> None:
    ip = "brian_timer"
    _lock_bundle(tmp_path, ip)
    locked_truth = tmp_path / ip / "req" / "locked_truth.md"
    locked_truth.write_text(locked_truth.read_text(encoding="utf-8") + "\ncorrupt\n", encoding="utf-8")

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "hash mismatch for req/locked_truth.md" in result.stdout


def test_check_locked_truth_bundle_rejects_broken_contract_ref(tmp_path: Path) -> None:
    ip = "brian_timer"
    _lock_bundle(tmp_path, ip)
    evidence_path = tmp_path / ip / "req" / "evidence_plan.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["evidence_plan"][0]["contract_ref"] = "C_MISSING"
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "unknown contract_ref C_MISSING" in result.stdout


def test_check_locked_truth_bundle_rejects_broken_structural_clock_domain(tmp_path: Path) -> None:
    ip = "brian_timer"
    _lock_bundle(tmp_path, ip)
    structural_path = tmp_path / ip / "req" / "structural_contracts.json"
    structural = json.loads(structural_path.read_text(encoding="utf-8"))
    structural["contracts"][0]["signals"][2]["timing"]["clock_domain"] = "missing_clk"
    structural_path.write_text(json.dumps(structural, indent=2, sort_keys=True), encoding="utf-8")

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "unknown clock_domain missing_clk" in result.stdout


def test_check_locked_truth_bundle_passes_review_candidate_without_manifest(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)

    result = _check(tmp_path, ip, review_candidate=True)

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[check_locked_truth_bundle] PASS brian_timer" in result.stdout
    assert "mode=review_candidate" in result.stdout


def test_check_contract_bundle_wrapper_passes_review_candidate(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)

    result = subprocess.run(
        [sys.executable, str(CONTRACT_CHECK_SCRIPT), ip, "--root", str(tmp_path), "--review-candidate"],
        check=False,
        text=True,
        capture_output=True,
    )

    assert result.returncode == 0, result.stdout + result.stderr
    assert "[check_contract_bundle] PASS brian_timer" in result.stdout
    assert (tmp_path / ip / "req" / "contract_authority_report.json").is_file()


def test_check_locked_truth_bundle_rejects_anchor_only_obligation(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)
    obligations_path = tmp_path / ip / "req" / "obligations.json"
    obligations = json.loads(obligations_path.read_text(encoding="utf-8"))
    obligations["obligations"][0]["structural_contract_refs"] = []
    obligations["obligations"][0]["behavioral_contract_refs"] = []
    obligations_path.write_text(json.dumps(obligations, indent=2, sort_keys=True), encoding="utf-8")

    result = _check(tmp_path, ip, review_candidate=True)

    assert result.returncode == 1
    assert "contract_refs alone are anchor refs" in result.stdout


def test_check_locked_truth_bundle_rejects_behavior_without_cycle_semantics(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)
    behavioral_path = tmp_path / ip / "req" / "behavioral_contracts.json"
    behavioral = json.loads(behavioral_path.read_text(encoding="utf-8"))
    contract = behavioral["contracts"][0]
    contract.pop("cycle", None)
    for row in contract["decision_table"]:
        row.pop("latency", None)
    contract["stage_contracts"] = [
        item for item in contract["stage_contracts"] if str(item.get("stage") or "") != "cycle_model"
    ]
    behavioral_path.write_text(json.dumps(behavioral, indent=2, sort_keys=True), encoding="utf-8")

    result = _check(tmp_path, ip, review_candidate=True)

    assert result.returncode == 1
    assert "BC_TIMER_ACCESS requires cycle/timing semantics" in result.stdout


def test_check_locked_truth_bundle_rejects_structural_contract_without_evidence(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)
    evidence_path = tmp_path / ip / "req" / "evidence_plan.json"
    evidence = json.loads(evidence_path.read_text(encoding="utf-8"))
    evidence["evidence_plan"] = [
        item for item in evidence["evidence_plan"] if item["contract_ref"] != "C_STRUCT_TIMER_IO"
    ]
    evidence_path.write_text(json.dumps(evidence, indent=2, sort_keys=True), encoding="utf-8")

    result = _check(tmp_path, ip, review_candidate=True)

    assert result.returncode == 1
    assert "C_STRUCT_TIMER_IO lacks evidence_plan closure" in result.stdout


def test_req_lifecycle_templates_have_expected_command_gates() -> None:
    draft_template = json.loads(DRAFT_TEMPLATE.read_text(encoding="utf-8"))
    finalize_template = json.loads(FINALIZE_TEMPLATE.read_text(encoding="utf-8"))
    lock_template = json.loads(LOCK_TEMPLATE.read_text(encoding="utf-8"))

    assert draft_template["name"] == "draft-req"
    assert finalize_template["name"] == "finalize-req"
    assert lock_template["name"] == "lock-req"
    assert any("--review-candidate" in str(task.get("command", "")) for task in finalize_template["tasks"])
    assert any("lock_requirement_set.py" in str(task.get("command", "")) for task in lock_template["tasks"])
    assert any("--from-candidate" in str(task.get("command", "")) for task in lock_template["tasks"])
    assert any("check_contract_bundle.py" in str(task.get("command", "")) for task in lock_template["tasks"])
    assert any(int(task.get("on_reject") or 0) == 1 for task in finalize_template["tasks"])
    assert any(int(task.get("on_reject") or 0) == 1 for task in lock_template["tasks"])


def test_default_req_lifecycle_commands_inject_templates() -> None:
    commands = {
        path.name: json.loads(path.read_text(encoding="utf-8"))
        for path in (DRAFT_COMMAND, FINALIZE_COMMAND, LOCK_COMMAND)
    }

    assert commands["draft-req.json"]["handler"] == "todo:template:draft-req"
    assert commands["finalize-req.json"]["handler"] == "todo:template:finalize-req"
    assert commands["lock-req.json"]["handler"] == "todo:template:lock-req"
    assert "locked-truth-finalize" not in commands["finalize-req.json"]["aliases"]
    assert "req-finalize" in commands["finalize-req.json"]["aliases"]
    assert "truth-lock" in commands["lock-req.json"]["aliases"]


def test_finalize_req_review_candidate_command_runs_without_approval_env(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)
    template = json.loads(FINALIZE_TEMPLATE.read_text(encoding="utf-8"))
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "ATLAS_WORKFLOW_ROOT": str(ROOT / "workflow"),
        "ATLAS_PROJECT_ROOT": str(tmp_path),
        "ATLAS_ACTIVE_IP": ip,
    }

    checker = subprocess.run(
        str(template["tasks"][1]["command"]),
        shell=True,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert checker.returncode == 0, checker.stdout + checker.stderr
    assert "[check_contract_bundle] PASS brian_timer" in checker.stdout
    assert "mode=review_candidate" in checker.stdout


def test_lock_req_template_commands_run_with_env(tmp_path: Path) -> None:
    ip = "brian_timer"
    _write_candidate_bundle(tmp_path, ip)
    template = json.loads(LOCK_TEMPLATE.read_text(encoding="utf-8"))
    env = {
        "PATH": "/usr/bin:/bin:/usr/sbin:/sbin",
        "ATLAS_WORKFLOW_ROOT": str(ROOT / "workflow"),
        "ATLAS_PROJECT_ROOT": str(tmp_path),
        "ATLAS_ACTIVE_IP": ip,
        "ATLAS_APPROVED_BY": "brian",
    }

    writer = subprocess.run(
        str(template["tasks"][1]["command"]),
        shell=True,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )
    checker = subprocess.run(
        str(template["tasks"][2]["command"]),
        shell=True,
        text=True,
        capture_output=True,
        env=env,
        check=False,
    )

    assert writer.returncode == 0, writer.stderr
    assert checker.returncode == 0, checker.stdout + checker.stderr
    assert "[check_contract_bundle] PASS brian_timer" in checker.stdout
    assert "mode=locked" in checker.stdout
