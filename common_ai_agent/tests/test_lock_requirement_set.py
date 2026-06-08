from __future__ import annotations

import hashlib
import importlib.util
import json
import subprocess
import sys
import time
from pathlib import Path
from typing import Any

import pytest


SCRIPT = Path(__file__).resolve().parents[1] / "workflow" / "req-gen" / "scripts" / "lock_requirement_set.py"


def _load_module():
    spec = importlib.util.spec_from_file_location(f"lock_requirement_set_{time.time_ns()}", SCRIPT)
    assert spec and spec.loader
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


def _draft(ip: str) -> dict[str, Any]:
    return {
        "ip": ip,
        "requirements": [
            {
                "requirement_id": "REQ_TIMER_APB_001",
                "title": "APB3 register interface",
                "statement": "The timer shall expose an APB3-style 32-bit register interface.",
                "status": "locked",
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
                    {"stage": "rtl", "artifact": "rtl/brian_timer.sv"},
                    {"stage": "tb", "artifact": "tb/cocotb/test_brian_timer.py"},
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
                "clock_domains": [{"id": "main_clk", "clock_signal": "clk", "edge": "rising"}],
                "reset_domains": [
                    {
                        "id": "main_rst",
                        "reset_signal": "rst_n",
                        "polarity": "active_low",
                        "assertion": "async",
                        "deassertion": "sync",
                        "clock_domain": "main_clk",
                    }
                ],
                "interfaces": [
                    {
                        "id": "ctrl_if",
                        "kind": "bus",
                        "protocol": "custom",
                        "role": "slave",
                        "clock_domain": "main_clk",
                        "signals": ["cmd_valid", "cmd_ready", "cmd_addr", "cmd_wdata", "rsp_rdata"],
                    },
                    {
                        "id": "event_in",
                        "kind": "event",
                        "protocol": "none",
                        "role": "sink",
                        "signals": ["ext_event"],
                    },
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


def test_lock_requirement_set_materializes_json_bundle_and_markdown(tmp_path: Path):
    mod = _load_module()
    ip = "brian_timer"
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(_draft(ip)), encoding="utf-8")

    manifest = mod.lock_requirement_set(ip, tmp_path, draft=draft_path, approved_by="brian")

    req_dir = tmp_path / ip / "req"
    expected_files = {
        "requirements_index.json",
        "obligations.json",
        "contract_refs.json",
        "structural_contracts.json",
        "behavioral_contracts.json",
        "evidence_plan.json",
        "approval_manifest.json",
        "locked_truth.md",
    }
    assert expected_files == {path.name for path in req_dir.iterdir()}
    assert manifest["status"] == "requirements_locked"
    assert manifest["requirements"] == [
        {"requirement_id": "REQ_TIMER_APB_001", "required": True, "status": "locked"}
    ]
    locked_md = (req_dir / "locked_truth.md").read_text(encoding="utf-8")
    assert "# Locked Truth - brian_timer" in locked_md
    assert "REQ_TIMER_APB_001" in locked_md
    assert "OBL_TIMER_APB_001" in locked_md
    assert "C_TIMER_APB_IF" in locked_md
    assert "C_STRUCT_TIMER_IO" in locked_md
    assert "BC_TIMER_ACCESS" in locked_md
    saved_manifest = json.loads((req_dir / "approval_manifest.json").read_text(encoding="utf-8"))
    md_hash = hashlib.sha256((req_dir / "locked_truth.md").read_bytes()).hexdigest()
    assert saved_manifest["files"]["req/locked_truth.md"]["sha256"] == md_hash


def test_lock_requirement_candidate_stamps_existing_review_candidate_bundle(tmp_path: Path):
    mod = _load_module()
    ip = "brian_timer"
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

    manifest = mod.lock_requirement_candidate(ip, tmp_path, approved_by="brian")

    assert manifest["status"] == "requirements_locked"
    assert manifest["approved_by"] == "brian"
    assert manifest["draft"] == f"{ip}/req"
    assert (req_dir / "locked_truth.md").is_file()
    assert (req_dir / "approval_manifest.json").is_file()
    requirements = json.loads((req_dir / "requirements_index.json").read_text(encoding="utf-8"))
    assert requirements["requirements"][0]["status"] == "locked"


def test_lock_requirement_set_rejects_missing_obligation_ref_before_writing(tmp_path: Path):
    mod = _load_module()
    ip = "brian_timer"
    bad = _draft(ip)
    bad["requirements"][0]["obligation_refs"] = ["OBL_MISSING"]
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(bad), encoding="utf-8")

    with pytest.raises(SystemExit) as exc:
        mod.lock_requirement_set(ip, tmp_path, draft=draft_path, approved_by="brian")

    assert "unknown obligation" in str(exc.value)
    assert not (tmp_path / ip / "req" / "approval_manifest.json").exists()


def test_lock_requirement_set_cli_writes_manifest_and_refuses_second_write(tmp_path: Path):
    ip = "brian_timer"
    draft_path = tmp_path / "draft.json"
    draft_path.write_text(json.dumps(_draft(ip)), encoding="utf-8")

    first = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
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
    assert first.returncode == 0, first.stderr
    assert f"[lock_requirement_set] manifest {ip}/req/approval_manifest.json" in first.stdout

    second = subprocess.run(
        [
            sys.executable,
            str(SCRIPT),
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
    assert second.returncode != 0
    assert "already exists" in second.stderr
