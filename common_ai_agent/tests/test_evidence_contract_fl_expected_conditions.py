from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import EVIDENCE_SCRIPT, first_map, make_contract_ip, read_json, write_json, write_rows


def test_evidence_contract_compares_observed_field_to_fl_expected_path(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "fl_expected": {
                    "model_result": {
                        "state_updates": {
                            "payload_bytes_written_count": 17,
                        }
                    }
                },
                "goal_id": "EQ_PAYLOAD",
                "mismatch": "",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
                "scenario_id": "SC_PAYLOAD",
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["pass_conditions"] = [
        {
            "expected_path": "fl_expected.model_result.state_updates.payload_bytes_written_count",
            "field": "payload_byte_count",
            "id": "payload_count_matches_fl",
            "kind": "observed_equals_fl_expected",
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


def test_evidence_contract_rejects_missing_fl_expected_path(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["pass_conditions"] = [
        {
            "expected_path": "fl_expected.model_result.state_updates.payload_bytes_written_count",
            "field": "payload_byte_count",
            "id": "payload_count_matches_fl",
            "kind": "observed_equals_fl_expected",
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
    assert "missing FL expected path fl_expected.model_result.state_updates.payload_bytes_written_count" in result.stdout


def test_evidence_contract_requires_row_passed_with_fl_expected_for_semantic_rows(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "fl_expected": {"model_result": {"payload_byte_count": 17}},
                "goal_id": "EQ_PAYLOAD",
                "mismatch": "",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
                "scenario_id": "SC_PAYLOAD",
            }
        ],
    )
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["pass_conditions"] = [{"id": "row_has_fl_expected", "kind": "row_passed_with_fl_expected"}]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout


def test_evidence_contract_rejects_semantic_row_pass_without_fl_expected(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["pass_conditions"] = [{"id": "row_has_fl_expected", "kind": "row_passed_with_fl_expected"}]
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "scoreboard row lacks FL expected model_result" in result.stdout
