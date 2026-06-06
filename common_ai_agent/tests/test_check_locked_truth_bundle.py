from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
CHECK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "check_locked_truth_bundle.py"
TEMPLATE = ROOT / "workflow" / "req-gen" / "todo_templates" / "locked-truth-finalize.json"
DEFAULT_TEMPLATE = ROOT / "workflow" / "default" / "todo_templates" / "locked-truth-finalize.json"
DEFAULT_COMMAND = ROOT / "workflow" / "default" / "commands" / "locked-truth-finalize.json"


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
            }
        ],
        "contract_refs": [
            {
                "contract_ref_id": "C_TIMER_APB_IF",
                "title": "APB interface contract",
                "obligation_refs": ["OBL_TIMER_APB_001"],
            }
        ],
        "evidence_plan": [
            {
                "evidence_id": "E_TIMER_APB_DIRECTED_001",
                "contract_ref": "C_TIMER_APB_IF",
                "artifact": "sim/scoreboard_events.jsonl",
                "validator": "check_evidence_contract.py",
                "pass_condition": "observed_apb_response == OK",
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


def _check(tmp_path: Path, ip: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), ip, "--root", str(tmp_path)],
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
    assert "evidence=1" in result.stdout


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


def test_locked_truth_finalize_template_has_command_gates() -> None:
    for template_path in (TEMPLATE, DEFAULT_TEMPLATE):
        template = json.loads(template_path.read_text(encoding="utf-8"))
        tasks = template["tasks"]

        assert template["name"] == "locked-truth-finalize"
        assert any("lock_requirement_set.py" in str(task.get("command", "")) for task in tasks)
        assert any("check_locked_truth_bundle.py" in str(task.get("command", "")) for task in tasks)
        assert any(int(task.get("on_reject") or 0) == 1 for task in tasks)


def test_default_locked_truth_finalize_command_injects_template() -> None:
    command = json.loads(DEFAULT_COMMAND.read_text(encoding="utf-8"))

    assert command["name"] == "locked-truth-finalize"
    assert command["handler"] == "todo:template:locked-truth-finalize"
    assert "truth-lock" in command["aliases"]


def test_locked_truth_finalize_template_commands_run_with_env(tmp_path: Path) -> None:
    ip = "brian_timer"
    draft_dir = tmp_path / ip / "req"
    draft_dir.mkdir(parents=True)
    (draft_dir / "locked_truth_draft.json").write_text(json.dumps(_draft(ip)), encoding="utf-8")
    template = json.loads(TEMPLATE.read_text(encoding="utf-8"))
    env = {
        **dict(),
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
