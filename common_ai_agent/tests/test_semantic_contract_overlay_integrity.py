from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from .contract_reflection_helpers import SEMANTIC_OVERLAY_SCRIPT, JsonMap, list_field, make_contract_ip, read_json, write_json


def _source(req_id: str, obligation_id: str, contract_ref: str) -> JsonMap:
    return {
        "contract_refs": [
            {
                "contract_ref": contract_ref,
                "fl": {"path": "model/functional_model.py"},
                "cl": {"path": "model/cycle_model.py"},
                "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
            }
        ],
        "requirements": [
            {
                "claim": "semantic source",
                "obligations": [
                    {
                        "contract_refs": [contract_ref],
                        "evidence_rows": [
                            {
                                "artifact": "sim/scoreboard_events.jsonl",
                                "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
                            }
                        ],
                        "obligation_id": obligation_id,
                        "pass_conditions": [{"id": "scoreboard_row_passed", "kind": "row_passed"}],
                        "required": True,
                        "required_observables": ["payload_byte_count"],
                        "scenario_ids": ["SC_PAYLOAD"],
                    }
                ],
                "required": True,
                "requirement_id": req_id,
                "source_refs": ["yaml/contract_ip.ssot.yaml"],
            }
        ],
        "schema_version": 1,
        "type": "semantic_contracts",
    }


def _run_overlay(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _ids(doc: JsonMap, field: str, key: str) -> list[str]:
    out: list[str] = []
    for item in list_field(doc, field):
        if isinstance(item, dict):
            value = item.get(key)
            if isinstance(value, str):
                out.append(value)
    return out


def test_semantic_overlay_reconciles_removed_managed_entries_without_deleting_legacy(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _source("REQ_SEM_OLD", "OBL_SEM_OLD", "REF_SEM_OLD"))
    first = _run_overlay(tmp_path)
    assert first.returncode == 0, first.stdout

    write_json(ip_dir / "verify" / "semantic_contracts.json", _source("REQ_SEM_NEW", "OBL_SEM_NEW", "REF_SEM_NEW"))
    second = _run_overlay(tmp_path)

    assert second.returncode == 0, second.stdout
    requirements = read_json(ip_dir / "verify" / "requirements_index.json")
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    reflection = read_json(ip_dir / "verify" / "contract_reflection.json")
    assert _ids(requirements, "requirements", "requirement_id") == ["REQ_PAYLOAD", "REQ_SEM_NEW"]
    assert _ids(contract, "obligations", "obligation_id") == ["OBL_PAYLOAD_COUNT", "OBL_SEM_NEW"]
    assert _ids(reflection, "contract_refs", "contract_ref") == ["REF_SEM_NEW"]


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("duplicate_requirement", "duplicate semantic requirement REQ_SEM"),
        ("duplicate_obligation", "duplicate semantic obligation OBL_SEM"),
        ("duplicate_ref", "duplicate semantic contract_ref REF_SEM"),
        ("optional_obligation", "OBL_SEM cannot set required=false in semantic overlay"),
        ("waived_obligation", "OBL_SEM cannot set status=waived in semantic overlay"),
        ("missing_evidence_rows", "OBL_SEM: missing evidence_rows"),
        ("wrong_type", "semantic_contracts type must be semantic_contracts"),
        ("missing_schema_version", "semantic_contracts schema_version must be 1"),
    ],
)
def test_semantic_overlay_rejects_duplicate_ids_and_obligation_downgrades(
    tmp_path: Path,
    mutation: str,
    expected: str,
) -> None:
    ip_dir = make_contract_ip(tmp_path)
    source = _source("REQ_SEM", "OBL_SEM", "REF_SEM")
    requirements = list_field(source, "requirements")
    contract_refs = list_field(source, "contract_refs")
    requirement = requirements[0]
    ref = contract_refs[0]
    assert isinstance(requirement, dict)
    assert isinstance(ref, dict)
    obligations = list_field(requirement, "obligations")
    obligation = obligations[0]
    assert isinstance(obligation, dict)
    if mutation == "duplicate_requirement":
        requirements.append(copy.deepcopy(requirement))
    elif mutation == "duplicate_obligation":
        obligations.append(copy.deepcopy(obligation))
    elif mutation == "duplicate_ref":
        contract_refs.append(copy.deepcopy(ref))
    elif mutation == "optional_obligation":
        obligation["required"] = False
    elif mutation == "waived_obligation":
        obligation["status"] = "waived"
    elif mutation == "missing_evidence_rows":
        obligation["evidence_rows"] = []
    elif mutation == "wrong_type":
        source["type"] = "evidence_contract"
    elif mutation == "missing_schema_version":
        _ = source.pop("schema_version", None)
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = _run_overlay(tmp_path)

    assert result.returncode == 1
    assert expected in result.stdout
