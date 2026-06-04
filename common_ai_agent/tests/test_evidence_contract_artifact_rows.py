from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import EVIDENCE_SCRIPT, first_map, make_contract_ip, read_json, write_json, write_rows


def test_evidence_contract_uses_declared_evidence_row_artifact(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [{"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True, "rtl_observed": {}}],
    )
    write_rows(
        ip_dir / "sim" / "contract_v2_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["evidence_rows"] = [
        {
            "artifact": "sim/contract_v2_events.jsonl",
            "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
        }
    ]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout

def test_evidence_contract_rejects_declared_artifact_outside_sim(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": False,
                "rtl_observed": {"payload_byte_count": 0, "sram_wr_strb": 0},
            }
        ],
    )
    write_rows(
        ip_dir / "verify" / "forged_rows.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["evidence_rows"] = [
        {
            "artifact": "verify/forged_rows.jsonl",
            "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
        }
    ]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "evidence row artifact is not an allowed simulator scoreboard artifact" in result.stdout


def test_evidence_contract_rejects_unapproved_sim_jsonl_artifact(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": False,
                "rtl_observed": {"payload_byte_count": 0, "sram_wr_strb": 0},
            }
        ],
    )
    write_rows(
        ip_dir / "sim" / "forged_rows.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["evidence_rows"] = [
        {
            "artifact": "sim/forged_rows.jsonl",
            "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
        }
    ]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "evidence row artifact is not an allowed simulator scoreboard artifact" in result.stdout


def test_evidence_contract_passes_masked_observed_field(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "prdata": (1 << 18) | 17, "sram_wr_strb": 0x1FFFF},
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["required_observables"] = ["payload_byte_count", "prdata", "sram_wr_strb"]
    obligation["pass_conditions"] = [
        {"field": "payload_byte_count", "id": "count_is_17", "kind": "observed_equals", "value": 17},
        {
            "field": "prdata",
            "id": "prdata_low_bits_are_payload_count",
            "kind": "observed_masked_equals",
            "mask": 0x1FFF,
            "value": 17,
        },
    ]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
