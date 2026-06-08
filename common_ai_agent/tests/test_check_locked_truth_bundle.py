from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
CHECK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "check_locked_truth_bundle.py"
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
                    }
                ],
                "stage_contracts": [
                    {"stage": "ssot", "check": "function_model transaction mirrors decision_table"},
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
    assert "evidence=2" in result.stdout
    closure = json.loads((tmp_path / ip / "req" / "contract_closure.json").read_text(encoding="utf-8"))
    assert closure["status"] == "pass"
    assert closure["summary"]["required_closed"] == 2


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
    assert any("check_locked_truth_bundle.py" in str(task.get("command", "")) for task in lock_template["tasks"])
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
    assert "[check_locked_truth_bundle] PASS brian_timer" in checker.stdout
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
    assert "[check_locked_truth_bundle] PASS brian_timer" in checker.stdout
    assert "mode=locked" in checker.stdout
