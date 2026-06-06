from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
LOCK_SCRIPT = ROOT / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"
CHECK_SCRIPT = ROOT / "workflow" / "ssot-gen" / "scripts" / "check_design_spec_trace.py"
SSOT_TEMPLATE = ROOT / "workflow" / "ssot-gen" / "todo_templates" / "atlas-pipeline-ssot.json"


def _draft(ip: str) -> dict[str, Any]:
    return {
        "ip": ip,
        "requirements": [
            {
                "requirement_id": "REQ_TIMER_APB_001",
                "title": "APB3 register interface",
                "statement": "The timer shall expose an APB3-style 32-bit APB slave.",
                "required": True,
                "obligation_refs": ["OBL_TIMER_APB_001"],
            }
        ],
        "obligations": [
            {
                "obligation_id": "OBL_TIMER_APB_001",
                "requirement_refs": ["REQ_TIMER_APB_001"],
                "statement": "APB accesses complete with an OK response.",
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
                "pass_condition": "apb_response == OK",
            }
        ],
    }


def _lock_bundle(tmp_path: Path, ip: str) -> dict[str, Any]:
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
    manifest_path = tmp_path / ip / "req" / "approval_manifest.json"
    return json.loads(manifest_path.read_text(encoding="utf-8"))


def _write_ssot(tmp_path: Path, ip: str, manifest: dict[str, Any], *, include_req_ref: bool = True) -> None:
    requirement_refs = ["REQ_TIMER_APB_001"] if include_req_ref else []
    doc = {
        "top_module": {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "type": "peripheral",
            "description": "APB timer",
        },
        "io_list": {
            "interfaces": [
                {
                    "name": "apb_slave",
                    "type": "APB3",
                    "role": "slave",
                    "source_refs": {
                        "requirements": requirement_refs,
                        "obligations": ["OBL_TIMER_APB_001"],
                    },
                    "contract_refs": {"central": ["C_TIMER_APB_IF"]},
                    "ports": [
                        {"name": "PCLK", "width": 1, "direction": "input"},
                        {"name": "PREADY", "width": 1, "direction": "output"},
                    ],
                }
            ]
        },
        "function_model": {
            "transactions": [
                {
                    "id": "FM_APB_ACCESS",
                    "source_refs": {
                        "requirements": requirement_refs,
                        "obligations": ["OBL_TIMER_APB_001"],
                    },
                    "contract_refs": {"central": ["C_TIMER_APB_IF"]},
                }
            ]
        },
        "custom": {
            "locked_truth_authority": {
                "kind": "locked_truth_projection",
                "approval_manifest": "req/approval_manifest.json",
                "bundle_sha256": manifest["bundle_sha256"],
            }
        },
        "traceability": {
            "locked_truth_projection": {
                "requirements": requirement_refs,
                "obligations": ["OBL_TIMER_APB_001"],
                "contract_refs": ["C_TIMER_APB_IF"],
            }
        },
    }
    ssot = tmp_path / ip / "yaml" / f"{ip}.ssot.yaml"
    ssot.parent.mkdir(parents=True)
    ssot.write_text(yaml.safe_dump(doc, sort_keys=False), encoding="utf-8")


def _check(tmp_path: Path, ip: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(CHECK_SCRIPT), ip, "--root", str(tmp_path)],
        check=False,
        text=True,
        capture_output=True,
    )


def test_check_design_spec_trace_accepts_locked_truth_projection(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    _write_ssot(tmp_path, ip, manifest)

    result = _check(tmp_path, ip)

    assert result.returncode == 0, result.stderr
    assert "[check_design_spec_trace] PASS brian_timer" in result.stdout
    assert "requirements=1" in result.stdout
    assert "contracts=1" in result.stdout


def test_check_design_spec_trace_rejects_stale_bundle_hash(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    stale = {**manifest, "bundle_sha256": "0" * 64}
    _write_ssot(tmp_path, ip, stale)

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "bundle_sha256 mismatch" in result.stdout


def test_check_design_spec_trace_rejects_missing_required_requirement_ref(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    _write_ssot(tmp_path, ip, manifest, include_req_ref=False)

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "missing required requirement refs: REQ_TIMER_APB_001" in result.stdout


def test_atlas_pipeline_ssot_template_runs_trace_checker_conditionally() -> None:
    template = json.loads(SSOT_TEMPLATE.read_text(encoding="utf-8"))
    validator = str(template["tasks"][1]["validator"])

    assert "verify_ssot.py" in validator
    assert "check_design_spec_trace.py" in validator
    assert "req/approval_manifest.json" in validator
    assert "$ATLAS_ACTIVE_IP" in validator
