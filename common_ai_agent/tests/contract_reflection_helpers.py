from __future__ import annotations

import json
from pathlib import Path
from typing import Union

REPO = Path(__file__).resolve().parents[1]
EVIDENCE_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "check_evidence_contract.py"
REFLECTION_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "check_contract_reflection.py"
CONTRACT_CHECK_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "run_contract_check.py"
OWNER_ROUTE_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "classify_contract_owner.py"
SEMANTIC_OVERLAY_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "emit_semantic_contract_overlay.py"
STAMP_SIM_FRESHNESS_SCRIPT = REPO / "workflow" / "contract-reflection" / "scripts" / "stamp_sim_evidence_freshness.py"
JsonValue = Union[None, bool, int, float, str, list["JsonValue"], dict[str, "JsonValue"]]
JsonMap = dict[str, JsonValue]


def _coerce_json(value) -> JsonValue:
    if value is None or isinstance(value, (bool, int, float, str)):
        return value
    if isinstance(value, list):
        return [_coerce_json(item) for item in value]
    if isinstance(value, dict):
        return {str(key): _coerce_json(item) for key, item in value.items()}
    raise AssertionError(f"unsupported JSON value {type(value).__name__}")


def write_json(path: Path, payload: JsonMap) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def write_rows(path: Path, rows: list[JsonMap]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    _ = path.write_text("".join(json.dumps(row, sort_keys=True) + "\n" for row in rows), encoding="utf-8")


def read_json(path: Path) -> JsonMap:
    try:
        value = _coerce_json(json.loads(path.read_text(encoding="utf-8")))
    except json.JSONDecodeError as exc:
        raise AssertionError(f"invalid JSON in {path}: {exc}") from exc
    if not isinstance(value, dict):
        raise AssertionError(f"{path} root must be an object")
    return value


def map_field(value: JsonMap, key: str) -> JsonMap:
    field = value.get(key)
    if not isinstance(field, dict):
        raise AssertionError(f"{key} must be an object")
    return field


def list_field(value: JsonMap, key: str) -> list[JsonValue]:
    field = value.get(key)
    if not isinstance(field, list):
        raise AssertionError(f"{key} must be a list")
    return field


def first_map(value: JsonMap, key: str) -> JsonMap:
    items = list_field(value, key)
    if not items or not isinstance(items[0], dict):
        raise AssertionError(f"{key} must contain an object")
    return items[0]


def make_contract_ip(root: Path) -> Path:
    ip_dir = root / "contract_ip"
    write_json(
        ip_dir / "verify" / "requirements_index.json",
        {
            "requirements": [
                {
                    "requirement_id": "REQ_PAYLOAD",
                    "required": True,
                    "obligation_ids": ["OBL_PAYLOAD_COUNT"],
                }
            ],
            "schema_version": 1,
            "type": "requirements_index",
        },
    )
    write_json(
        ip_dir / "verify" / "evidence_contract.json",
        {
            "obligations": [
                {
                    "contract_refs": ["STATE_PAYLOAD_COUNT"],
                    "evidence_rows": [
                        {
                            "artifact": "sim/scoreboard_events.jsonl",
                            "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
                        }
                    ],
                    "obligation_id": "OBL_PAYLOAD_COUNT",
                    "pass_conditions": [
                        {"field": "payload_byte_count", "id": "count_is_17", "kind": "observed_equals", "value": 17},
                        {"field": "sram_wr_strb", "id": "strobe_contiguous", "kind": "strobe_contiguous"},
                    ],
                    "required": True,
                    "required_observables": ["payload_byte_count", "sram_wr_strb"],
                    "requirement_ids": ["REQ_PAYLOAD"],
                    "scenario_ids": ["SC_PAYLOAD"],
                }
            ],
            "schema_version": 1,
            "type": "evidence_contract",
        },
    )
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            }
        ],
    )
    return ip_dir
