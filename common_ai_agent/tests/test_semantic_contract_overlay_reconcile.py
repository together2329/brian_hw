from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import SEMANTIC_OVERLAY_SCRIPT, JsonMap, list_field, make_contract_ip, read_json, write_json


def _semantic_source(req_id: str, obligation_id: str, contract_ref: str) -> JsonMap:
    return {
        "contract_refs": [{"contract_ref": contract_ref}],
        "requirements": [
            {
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
                        "required": True,
                    }
                ],
                "required": True,
                "requirement_id": req_id,
            }
        ],
        "schema_version": 1,
        "type": "semantic_contracts",
    }


def _string_ids(path: Path, list_key: str, id_key: str) -> set[str]:
    out: set[str] = set()
    for item in list_field(read_json(path), list_key):
        if isinstance(item, dict):
            value = item.get(id_key)
            if isinstance(value, str):
                out.add(value)
    return out


def test_semantic_overlay_removes_stale_managed_entries_but_preserves_legacy(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_source("REQ_OLD", "OBL_OLD", "REF_OLD"))
    first = subprocess.run(["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_source("REQ_NEW", "OBL_NEW", "REF_NEW"))
    second = subprocess.run(["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE)

    assert first.returncode == 0, first.stdout
    assert second.returncode == 0, second.stdout
    requirements = _string_ids(ip_dir / "verify" / "requirements_index.json", "requirements", "requirement_id")
    obligations = _string_ids(ip_dir / "verify" / "evidence_contract.json", "obligations", "obligation_id")
    refs = _string_ids(ip_dir / "verify" / "contract_reflection.json", "contract_refs", "contract_ref")
    assert requirements == {"REQ_PAYLOAD", "REQ_NEW"}
    assert obligations == {"OBL_PAYLOAD_COUNT", "OBL_NEW"}
    assert refs == {"REF_NEW"}
