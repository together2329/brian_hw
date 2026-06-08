from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml


ROOT = Path(__file__).resolve().parents[1]
TRACE_SCRIPT = ROOT / "workflow" / "fl-model-gen" / "scripts" / "check_model_contract_trace.py"
SIGNATURE_SCRIPT = ROOT / "workflow" / "fl-model-gen" / "scripts" / "emit_model_signature.py"


def _write_req_and_ssot(tmp_path: Path, ip: str, *, anchor_only: bool = False) -> Path:
    ip_dir = tmp_path / ip
    req_dir = ip_dir / "req"
    yaml_dir = ip_dir / "yaml"
    req_dir.mkdir(parents=True)
    yaml_dir.mkdir(parents=True)
    (req_dir / "obligations.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "obligations": [{"obligation_id": "OBL_ACCESS", "requirement_refs": ["REQ_ACCESS"]}],
            }
        ),
        encoding="utf-8",
    )
    (req_dir / "behavioral_contracts.json").write_text(
        json.dumps(
            {
                "ip": ip,
                "contracts": [
                    {
                        "id": "BC_ACCESS",
                        "obligations": ["OBL_ACCESS"],
                        "decision_table": [
                            {"when": "valid == 1 and ready == 1", "then": {"data_o": "state_q"}}
                        ],
                        "stage_contracts": [
                            {"stage": "ssot", "check": "function_model transaction mirrors BC_ACCESS"},
                            {"stage": "cycle_model", "check": "cycle_model accept timing mirrors BC_ACCESS"},
                            {"stage": "rtl-gen", "check": "RTL implements BC_ACCESS"},
                        ],
                    }
                ],
            }
        ),
        encoding="utf-8",
    )
    tx: dict[str, Any] = {
        "id": "FM_ACCESS",
        "contract_refs": {"behavioral": ["BC_ACCESS"]},
    }
    if anchor_only:
        tx["description"] = "anchor only"
    else:
        tx.update(
            {
                "preconditions": ["valid == 1 and ready == 1"],
                "output_rules": [{"name": "data_o", "port": "data_o", "expr": "state_q", "width": 32}],
                "state_updates": [{"name": "state_q", "expr": "state_q + 1", "width": 32}],
            }
        )
    ssot = {
        "top_module": {"name": ip},
        "function_model": {"transactions": [tx]},
        "cycle_model": {
            "handshake_rules": [
                {
                    "id": "CM_ACCEPT",
                    "signal": "valid/ready",
                    "rule": "valid == 1 and ready == 1",
                    "contract_refs": {"behavioral": ["BC_ACCESS"]},
                }
            ],
        },
    }
    (yaml_dir / f"{ip}.ssot.yaml").write_text(yaml.safe_dump(ssot, sort_keys=False), encoding="utf-8")
    return ip_dir


def _write_model_artifacts(ip_dir: Path) -> None:
    model_dir = ip_dir / "model"
    model_dir.mkdir()
    (model_dir / "functional_model.py").write_text(
        "class FunctionalModel:\n"
        "    def apply(self, txn):\n"
        "        return {'BC_ACCESS': 'FM_ACCESS'}\n"
        "\n"
        "def run_self_check():\n"
        "    return {'passed': True, 'transaction_results': [{'id': 'FM_ACCESS', 'contract': 'BC_ACCESS'}]}\n",
        encoding="utf-8",
    )
    (model_dir / "fl_model_check.json").write_text(
        json.dumps(
            {
                "passed": True,
                "transaction_results": [{"id": "FM_ACCESS", "contract_refs": ["BC_ACCESS"]}],
            }
        )
        + "\n",
        encoding="utf-8",
    )
    (model_dir / "cycle_model.py").write_text(
        "class CycleModel:\n"
        "    def run_self_check(self):\n"
        "        return {'passed': True, 'coverage': ['CM_ACCEPT', 'BC_ACCESS']}\n",
        encoding="utf-8",
    )
    (model_dir / "cl_model_check.json").write_text(
        json.dumps({"passed": True, "coverage": ["CM_ACCEPT", "BC_ACCESS"]}) + "\n",
        encoding="utf-8",
    )
    subprocess.run(
        [sys.executable, str(SIGNATURE_SCRIPT), ip_dir.name, "--root", str(ip_dir.parent)],
        check=True,
        text=True,
        capture_output=True,
    )


def _run_trace(tmp_path: Path, ip: str, *extra: str) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        [sys.executable, str(TRACE_SCRIPT), ip, "--root", str(tmp_path), *extra],
        check=False,
        text=True,
        capture_output=True,
    )


def test_model_contract_trace_passes_when_fl_cl_artifacts_cover_contract_rows(tmp_path: Path) -> None:
    ip = "trace_ip"
    ip_dir = _write_req_and_ssot(tmp_path, ip)
    _write_model_artifacts(ip_dir)

    result = _run_trace(tmp_path, ip)

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((ip_dir / "logs" / "gates" / "model_contract_trace.json").read_text(encoding="utf-8"))
    assert report["mode"] == "fl_cl_model"
    assert report["passed"] is True
    assert report["artifact_closure"]["cycle_required_contracts"] == ["BC_ACCESS"]


def test_model_contract_trace_allows_explicit_direct_rtl_without_model_artifacts(tmp_path: Path) -> None:
    ip = "direct_ip"
    ip_dir = _write_req_and_ssot(tmp_path, ip)

    result = _run_trace(tmp_path, ip, "--allow-direct-rtl")

    assert result.returncode == 0, result.stdout + result.stderr
    report = json.loads((ip_dir / "logs" / "gates" / "model_contract_trace.json").read_text(encoding="utf-8"))
    assert report["mode"] == "direct_rtl"
    assert report["passed"] is True
    assert report["artifact_closure"]["status"] == "skipped_direct_rtl"


def test_model_contract_trace_rejects_direct_rtl_when_ssot_projection_is_anchor_only(tmp_path: Path) -> None:
    ip = "anchor_ip"
    _write_req_and_ssot(tmp_path, ip, anchor_only=True)

    result = _run_trace(tmp_path, ip, "--allow-direct-rtl")

    assert result.returncode == 1
    assert "anchor-only function_model projection" in result.stdout
