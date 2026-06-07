from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import (
    EVIDENCE_SCRIPT,
    first_map,
    list_field,
    make_contract_ip,
    map_field,
    read_json,
    write_json,
    write_rows,
)


def test_evidence_contract_passes_when_required_obligation_has_row_observables_and_conditions(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "evidence_contract_coverage.json")
    assert report["status"] == "pass"
    summary = map_field(report, "summary")
    assert summary["passed"] == 1


def test_evidence_contract_applies_conditions_to_every_matching_row(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF},
            },
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 99, "sram_wr_strb": 0x1FFFF},
            },
        ],
    )

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "count_is_17: EQ_PAYLOAD/SC_PAYLOAD: payload_byte_count=99 expected 17" in result.stdout
    report = read_json(ip_dir / "signoff" / "evidence_contract_coverage.json")
    obligation = first_map(report, "obligations")
    conditions = map_field(obligation, "condition_results")
    assert conditions["count_is_17"] is False


def test_evidence_contract_fails_when_observable_is_missing(tmp_path: Path) -> None:
    _ = make_contract_ip(tmp_path)
    rows = tmp_path / "contract_ip" / "sim" / "scoreboard_events.jsonl"
    write_rows(rows, [{"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True, "rtl_observed": {}}])

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing observable payload_byte_count" in result.stdout


def test_evidence_contract_fails_when_required_requirement_obligation_is_missing(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    index_path = ip_dir / "verify" / "requirements_index.json"
    index = read_json(index_path)
    first_requirement = first_map(index, "requirements")
    first_requirement["obligation_ids"] = ["OBL_PAYLOAD_COUNT", "OBL_MISSING"]
    write_json(index_path, index)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "REQ_PAYLOAD: missing obligation OBL_MISSING" in result.stdout


def test_evidence_contract_passes_when_required_observable_is_in_vcd(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    obligation["required_observables"] = ["payload_byte_count", "sram_wr_strb", "descriptor_bytes"]
    pass_conditions = list_field(obligation, "pass_conditions")
    pass_conditions.append(
        {
            "artifact": "sim/contract_ip.vcd",
            "id": "descriptor_bytes_reaches_17",
            "kind": "vcd_signal_ever_equals",
            "signal": "descriptor_bytes",
            "value": 17,
        }
    )
    write_json(contract_path, contract)
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! descriptor_bytes [12:0] $end\n#0\nb0 !\n#10\nb10001 !\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "evidence_contract_coverage.json")
    assert report["status"] == "pass"


def test_evidence_contract_rejects_vcd_paths_outside_ip_root(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    pass_conditions = list_field(obligation, "pass_conditions")
    pass_conditions.append(
        {
            "artifact": "../outside.vcd",
            "id": "descriptor_bytes_reaches_17",
            "kind": "vcd_signal_ever_equals",
            "signal": "descriptor_bytes",
            "value": 17,
        }
    )
    write_json(contract_path, contract)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "VCD artifact path escapes IP root" in result.stdout


def test_evidence_contract_stable_while_requires_active_window(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    contract_path = ip_dir / "verify" / "evidence_contract.json"
    contract = read_json(contract_path)
    obligation = first_map(contract, "obligations")
    pass_conditions = list_field(obligation, "pass_conditions")
    pass_conditions.append(
        {
            "artifact": "sim/contract_ip.vcd",
            "id": "hold_under_backpressure",
            "kind": "vcd_stable_while",
            "stable_signals": ["sram_wr_data"],
            "when": {"signal": "sram_wr_valid", "value": 1},
            "while": {"signal": "sram_wr_ready", "value": 0},
        }
    )
    write_json(contract_path, contract)
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "\n".join(
            [
                "$var wire 1 ! sram_wr_valid $end",
                "$var wire 1 @ sram_wr_ready $end",
                "$var wire 32 # sram_wr_data [31:0] $end",
                "#0",
                "0!",
                "0@",
                "b1010 #",
            ]
        )
        + "\n",
        encoding="utf-8",
    )

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "no active window where sram_wr_valid=1 and sram_wr_ready=0" in result.stdout
