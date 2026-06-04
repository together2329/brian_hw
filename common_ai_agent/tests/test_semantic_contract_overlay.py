from __future__ import annotations

import subprocess
from pathlib import Path

from .contract_reflection_helpers import (
    CONTRACT_CHECK_SCRIPT,
    EVIDENCE_SCRIPT,
    REFLECTION_SCRIPT,
    SEMANTIC_OVERLAY_SCRIPT,
    JsonMap,
    first_map,
    list_field,
    make_contract_ip,
    read_json,
    write_json,
    write_rows,
)


def _write_stage_files(ip_dir: Path) -> None:
    for rel in (
        "yaml/contract_ip.ssot.yaml",
        "model/functional_model.py",
        "model/cycle_model.py",
        "rtl/contract_ip.sv",
        "tb/cocotb/test_contract_ip.py",
    ):
        path = ip_dir / rel
        path.parent.mkdir(parents=True, exist_ok=True)
        _ = path.write_text("// marker\n" if rel.endswith(".sv") else "# marker\n", encoding="utf-8")


def _write_wave(ip_dir: Path) -> None:
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n"
        "$var wire 1 @ sram_wr_valid $end\n"
        "$var wire 17 # sram_wr_strb [16:0] $end\n"
        "#0\nb0 !\n0@\nb0 #\n"
        "#5\nb10001 !\n"
        "#10\n1@\nb11111111111111111 #\n",
        encoding="utf-8",
    )


def _semantic_contracts() -> JsonMap:
    return {
        "contract_refs": [
            {
                "contract_ref": "STATE_PAYLOAD_COUNT",
                "fl": {"path": "model/functional_model.py"},
                "cl": {"path": "model/cycle_model.py"},
                "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
                "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
            },
            {
                "contract_ref": "MEM_SRAM_PAYLOAD_PACK",
                "fl": {"path": "model/functional_model.py"},
                "cl": {"path": "model/cycle_model.py"},
                "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["sram_wr_valid", "sram_wr_strb"]},
                "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
                "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
                "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "sram_monitor"},
            },
        ],
        "requirements": [
            {
                "claim": "Payload count and SRAM pack are independently closed by semantic predicates.",
                "obligations": [
                    {
                        "contract_refs": ["STATE_PAYLOAD_COUNT"],
                        "evidence_rows": [
                            {
                                "artifact": "sim/scoreboard_events.jsonl",
                                "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
                            }
                        ],
                        "obligation_id": "OBL_SEMANTIC_PAYLOAD_COUNT",
                        "pass_conditions": [
                            {"id": "scoreboard_row_passed", "kind": "row_passed"},
                            {"field": "payload_byte_count", "id": "payload_count_is_17", "kind": "observed_equals", "value": 17},
                            {
                                "artifact": "sim/contract_ip.vcd",
                                "id": "payload_count_reaches_17_in_wave",
                                "kind": "vcd_signal_ever_equals",
                                "signal": "payload_byte_count",
                                "value": 17,
                            },
                        ],
                        "required": True,
                        "required_observables": ["payload_byte_count"],
                        "scenario_ids": ["SC_PAYLOAD"],
                    },
                    {
                        "contract_refs": ["MEM_SRAM_PAYLOAD_PACK"],
                        "evidence_rows": [
                            {
                                "artifact": "sim/scoreboard_events.jsonl",
                                "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
                            }
                        ],
                        "obligation_id": "OBL_SEMANTIC_SRAM_PACK",
                        "pass_conditions": [
                            {"field": "sram_wr_valid", "id": "sram_valid_asserted", "kind": "observed_equals", "value": 1},
                            {"field": "sram_wr_strb", "id": "sram_strobe_contiguous", "kind": "strobe_contiguous"},
                            {
                                "artifact": "sim/contract_ip.vcd",
                                "first": {"signal": "payload_byte_count", "value": 17},
                                "id": "sram_write_after_count_visible",
                                "kind": "vcd_event_order",
                                "relation": "same_or_after",
                                "second": {"signal": "sram_wr_valid", "value": 1},
                            },
                        ],
                        "required": True,
                        "required_observables": ["payload_byte_count", "sram_wr_valid", "sram_wr_strb"],
                        "scenario_ids": ["SC_PAYLOAD"],
                    },
                ],
                "required": True,
                "requirement_id": "REQ_SEMANTIC_PAYLOAD",
                "source_refs": ["yaml/contract_ip.ssot.yaml"],
            }
        ],
        "schema_version": 1,
        "type": "semantic_contracts",
    }


def test_semantic_contract_overlay_adds_requirement_obligations_and_reflections(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_files(ip_dir)
    _write_wave(ip_dir)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF, "sram_wr_valid": 1},
            }
        ],
    )
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())

    result = subprocess.run(
        ["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    requirements = read_json(ip_dir / "verify" / "requirements_index.json")
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    reflection = read_json(ip_dir / "verify" / "contract_reflection.json")
    assert "REQ_SEMANTIC_PAYLOAD" in str(requirements)
    assert "OBL_SEMANTIC_SRAM_PACK" in str(contract)
    assert "MEM_SRAM_PAYLOAD_PACK" in str(reflection)

    evidence = subprocess.run(["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)
    reflected = subprocess.run(["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    assert evidence.returncode == 0, evidence.stdout
    assert reflected.returncode == 0, reflected.stdout


def test_contract_check_runs_semantic_overlay_before_validation(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_files(ip_dir)
    _write_wave(ip_dir)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF, "sram_wr_valid": 1},
            }
        ],
    )
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())

    result = subprocess.run(
        ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["summary"] == {
        "evidence_failed": 0,
        "evidence_passed": 3,
        "evidence_total": 3,
        "reflection_failed": 0,
        "reflection_passed": 2,
        "reflection_total": 2,
    }
    assert "semantic_contract_overlay" in str(report["runs"])


def test_vcd_event_order_fails_when_second_event_happens_first(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_files(ip_dir)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n"
        "$var wire 1 @ sram_wr_valid $end\n"
        "$var wire 17 # sram_wr_strb [16:0] $end\n"
        "#0\nb0 !\n0@\nb0 #\n"
        "#5\n1@\nb11111111111111111 #\n"
        "#10\nb10001 !\n",
        encoding="utf-8",
    )
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [
            {
                "goal_id": "EQ_PAYLOAD",
                "scenario_id": "SC_PAYLOAD",
                "passed": True,
                "rtl_observed": {"payload_byte_count": 17, "sram_wr_strb": 0x1FFFF, "sram_wr_valid": 1},
            }
        ],
    )
    overlay = subprocess.run(["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)], text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert overlay.returncode == 0, overlay.stdout
    assert result.returncode == 1
    assert "sram_write_after_count_visible" in result.stdout
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    assert first_map(contract, "obligations")["obligation_id"] == "OBL_PAYLOAD_COUNT"
    assert "OBL_SEMANTIC_SRAM_PACK" in str(list_field(contract, "obligations"))


def test_semantic_overlay_rejects_collision_with_existing_required_requirement(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_files(ip_dir)
    _write_wave(ip_dir)
    source = _semantic_contracts()
    requirements = list_field(source, "requirements")
    first_requirement = requirements[0]
    assert isinstance(first_requirement, dict)
    first_requirement["requirement_id"] = "REQ_PAYLOAD"
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = subprocess.run(
        ["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "collides with existing non-semantic requirement" in result.stdout
