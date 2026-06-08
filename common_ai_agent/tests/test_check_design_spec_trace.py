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
                    {"stage": "cycle_model", "check": "cycle_model captures command accept timing"},
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
                "pass_condition": "apb_response == OK",
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


def _write_ssot(
    tmp_path: Path,
    ip: str,
    manifest: dict[str, Any],
    *,
    include_req_ref: bool = True,
    cmd_addr_width: int = 12,
    include_cycle_model: bool = True,
    function_anchor_only: bool = False,
) -> None:
    requirement_refs = ["REQ_TIMER_APB_001"] if include_req_ref else []
    central_contract_refs = ["C_TIMER_APB_IF"]
    structural_contract_refs = ["C_STRUCT_TIMER_IO"]
    behavioral_contract_refs = ["BC_TIMER_ACCESS"]
    transaction: dict[str, Any] = {
        "id": "FM_APB_ACCESS",
        "source_refs": {
            "requirements": requirement_refs,
            "obligations": ["OBL_TIMER_APB_001"],
        },
        "contract_refs": {"central": central_contract_refs, "behavioral": behavioral_contract_refs},
    }
    if function_anchor_only:
        transaction["description"] = "anchor-only row without executable behavior"
    else:
        transaction.update(
            {
                "preconditions": ["cmd_valid == 1 and cmd_ready == 1"],
                "output_rules": [
                    {"name": "rsp_rdata", "port": "rsp_rdata", "expr": "selected_register_value", "width": 32}
                ],
                "state_updates": [{"name": "last_cmd_addr", "expr": "cmd_addr", "width": 12}],
                "decision_table": [
                    {
                        "when": "cmd_valid == 1 and cmd_ready == 1",
                        "then": {"accept_cmd": 1, "rsp_rdata": "selected_register_value"},
                    }
                ],
            }
        )

    doc = {
        "top_module": {
            "name": ip,
            "file": f"rtl/{ip}.sv",
            "type": "peripheral",
            "description": "APB timer",
        },
        "io_list": {
            "clock_domains": [
                {
                    "name": "main_clk",
                    "ports": [
                        {"name": "clk", "width": 1, "direction": "input", "role": "clock", "contract_refs": {"structural": structural_contract_refs}}
                    ],
                }
            ],
            "resets": [
                {
                    "name": "main_rst",
                    "clock_domain": "main_clk",
                    "ports": [
                        {"name": "rst_n", "width": 1, "direction": "input", "role": "reset", "contract_refs": {"structural": structural_contract_refs}}
                    ],
                }
            ],
            "interfaces": [
                {
                    "name": "ctrl_if",
                    "type": "custom",
                    "role": "slave",
                    "clock_domain": "main_clk",
                    "source_refs": {
                        "requirements": requirement_refs,
                        "obligations": ["OBL_TIMER_APB_001"],
                    },
                    "contract_refs": {"central": central_contract_refs, "structural": structural_contract_refs},
                    "ports": [
                        {"name": "cmd_valid", "width": 1, "direction": "input", "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                        {"name": "cmd_ready", "width": 1, "direction": "output", "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                        {"name": "cmd_addr", "width": cmd_addr_width, "direction": "input", "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                        {"name": "cmd_wdata", "width": 32, "direction": "input", "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                        {"name": "rsp_rdata", "width": 32, "direction": "output", "timing": {"kind": "sync", "clock_domain": "main_clk"}},
                    ],
                },
                {
                    "name": "event_in",
                    "type": "custom",
                    "role": "sink",
                    "source_refs": {
                        "requirements": requirement_refs,
                        "obligations": ["OBL_TIMER_APB_001"],
                    },
                    "contract_refs": {"structural": structural_contract_refs},
                    "ports": [
                        {"name": "ext_event", "width": 1, "direction": "input", "timing": {"kind": "async", "sync_to": "main_clk"}},
                    ],
                }
            ]
        },
        "function_model": {
            "transactions": [transaction]
        },
        "custom": {
            "locked_truth_authority": {
                "kind": "locked_truth_projection",
                "approval_manifest": "req/approval_manifest.json",
                "bundle_sha256": manifest["bundle_sha256"],
                "projected_files": [
                    "req/requirements_index.json",
                    "req/obligations.json",
                    "req/contract_refs.json",
                    "req/structural_contracts.json",
                    "req/behavioral_contracts.json",
                    "req/evidence_plan.json",
                ],
            }
        },
        "traceability": {
            "locked_truth_projection": {
                "requirements": requirement_refs,
                "obligations": ["OBL_TIMER_APB_001"],
                "contract_refs": central_contract_refs,
                "structural_contracts": structural_contract_refs,
                "behavioral_contracts": behavioral_contract_refs,
            }
        },
    }
    if include_cycle_model:
        doc["cycle_model"] = {
            "handshake_rules": [
                {
                    "id": "CM_CMD_ACCEPT",
                    "signal": "cmd_valid/cmd_ready",
                    "rule": "cmd_valid == 1 and cmd_ready == 1",
                    "contract_refs": {"behavioral": behavioral_contract_refs},
                }
            ],
            "latency": {
                "FM_APB_ACCESS": {
                    "min_cycles": 1,
                    "max_cycles": 1,
                    "contract_refs": {"behavioral": behavioral_contract_refs},
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
    assert "structural_contracts=1" in result.stdout
    assert "behavioral_contracts=1" in result.stdout


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


def test_check_design_spec_trace_rejects_structural_io_width_mismatch(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    _write_ssot(tmp_path, ip, manifest, cmd_addr_width=10)

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "io_list.cmd_addr width 10 != structural 12" in result.stdout


def test_check_design_spec_trace_rejects_anchor_only_function_model_contract(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    _write_ssot(tmp_path, ip, manifest, function_anchor_only=True)

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "anchor-only function_model projection" in result.stdout


def test_check_design_spec_trace_rejects_missing_cycle_model_contract(tmp_path: Path) -> None:
    ip = "brian_timer"
    manifest = _lock_bundle(tmp_path, ip)
    _write_ssot(tmp_path, ip, manifest, include_cycle_model=False)

    result = _check(tmp_path, ip)

    assert result.returncode == 1
    assert "is not projected into a cycle_model row" in result.stdout


def test_atlas_pipeline_ssot_template_runs_trace_checker_conditionally() -> None:
    template = json.loads(SSOT_TEMPLATE.read_text(encoding="utf-8"))
    validator = str(template["tasks"][1]["validator"])

    assert "verify_ssot.py" in validator
    assert "check_design_spec_trace.py" in validator
    assert "req/approval_manifest.json" in validator
    assert "$ATLAS_ACTIVE_IP" in validator
