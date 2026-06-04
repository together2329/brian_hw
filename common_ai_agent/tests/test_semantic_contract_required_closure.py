from __future__ import annotations

import copy
import subprocess
from pathlib import Path

import pytest

from .contract_reflection_helpers import (
    CONTRACT_CHECK_SCRIPT,
    SEMANTIC_OVERLAY_SCRIPT,
    JsonMap,
    JsonValue,
    first_map,
    list_field,
    make_contract_ip,
    map_field,
    read_json,
    write_json,
    write_rows,
)


def _write_stage_artifacts(ip_dir: Path) -> None:
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
    _ = (ip_dir / "sim" / "contract_ip.vcd").write_text(
        "$var wire 13 ! payload_byte_count [12:0] $end\n"
        "$var wire 17 @ sram_wr_strb [16:0] $end\n"
        "#0\nb10001 !\nb11111111111111111 @\n",
        encoding="utf-8",
    )


def _reflection_entry(contract_ref: str = "STATE_PAYLOAD_COUNT") -> JsonMap:
    return {
        "contract_ref": contract_ref,
        "fl": {"path": "model/functional_model.py"},
        "cl": {"path": "model/cycle_model.py"},
        "rtl": {"owner_files": ["rtl/contract_ip.sv"], "observable_via": ["payload_byte_count"]},
        "sim": {"scoreboard": "sim/scoreboard_events.jsonl", "wave": "sim/contract_ip.vcd"},
        "ssot": {"path": "yaml/contract_ip.ssot.yaml"},
        "tb": {"path": "tb/cocotb/test_contract_ip.py", "monitor": "payload_monitor"},
    }


def _write_legacy_reflection(ip_dir: Path) -> None:
    write_json(
        ip_dir / "verify" / "contract_reflection.json",
        {"contract_refs": [_reflection_entry()], "schema_version": 1, "type": "contract_reflection"},
    )


def _semantic_contracts() -> JsonMap:
    return {
        "contract_refs": [_reflection_entry("SEMANTIC_STATE_PAYLOAD_COUNT")],
        "requirements": [
            {
                "claim": "Semantic payload count closure is required.",
                "obligations": [
                    {
                        "contract_refs": ["SEMANTIC_STATE_PAYLOAD_COUNT"],
                        "evidence_rows": [
                            {
                                "artifact": "sim/scoreboard_events.jsonl",
                                "match": {"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD"},
                            }
                        ],
                        "obligation_id": "OBL_SEMANTIC_PAYLOAD_COUNT",
                        "pass_conditions": [
                            {"id": "semantic_row_passed", "kind": "row_passed"},
                            {"field": "payload_byte_count", "id": "semantic_count_is_17", "kind": "observed_equals", "value": 17},
                        ],
                        "required": True,
                        "required_observables": ["payload_byte_count"],
                        "scenario_ids": ["SC_PAYLOAD"],
                    }
                ],
                "required": True,
                "requirement_id": "REQ_SEMANTIC_PAYLOAD",
                "source_refs": ["yaml/contract_ip.ssot.yaml"],
            }
        ],
        "schema_version": 1,
        "type": "semantic_contracts",
    }


def _run_contract_check(root: Path, require_contract_closure: bool = False) -> subprocess.CompletedProcess[str]:
    cmd = ["python3", str(CONTRACT_CHECK_SCRIPT), "contract_ip", "--root", str(root)]
    if require_contract_closure:
        cmd.append("--require-contract-closure")
    return subprocess.run(cmd, text=True, stdout=subprocess.PIPE, stderr=subprocess.STDOUT)


def _run_semantic_overlay(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _ids(payload: JsonMap, list_key: str, id_key: str) -> list[str]:
    out: list[str] = []
    for item in list_field(payload, list_key):
        if isinstance(item, dict):
            value = item.get(id_key)
            if isinstance(value, str):
                out.append(value)
    return out


def test_default_contract_check_keeps_legacy_generated_contract_usable(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)

    result = _run_contract_check(tmp_path)

    assert result.returncode == 0, result.stdout
    assert "skipped: verify/semantic_contracts.json not present" in str(read_json(ip_dir / "signoff" / "contract_check.json")["runs"])


def test_required_contract_closure_rejects_missing_semantic_source_even_when_generated_artifacts_pass(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] == "fail"
    assert "required: missing verify/semantic_contracts.json" in str(report["runs"])
    summary = map_field(report, "summary")
    assert summary["evidence_passed"] == 1
    assert summary["reflection_passed"] == 1


def test_required_contract_closure_passes_when_semantic_source_closes(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 0, result.stdout
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    assert report["status"] == "pass"
    assert map_field(report, "summary")["evidence_total"] == 2


def test_required_contract_closure_rejects_empty_semantic_source(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    empty_source: JsonMap = {"contract_refs": [], "requirements": [], "schema_version": 1, "type": "semantic_contracts"}
    write_json(ip_dir / "verify" / "semantic_contracts.json", empty_source)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    assert "semantic_contracts requires at least one requirement" in result.stdout


def test_required_contract_closure_rejects_semantic_obligation_using_undeclared_ref(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    source = copy.deepcopy(_semantic_contracts())
    obligation = first_map(first_map(source, "requirements"), "obligations")
    legacy_ref: list[JsonValue] = ["STATE_PAYLOAD_COUNT"]
    empty_refs: list[JsonValue] = []
    obligation["contract_refs"] = legacy_ref
    source["contract_refs"] = empty_refs
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    assert "references undeclared contract_ref STATE_PAYLOAD_COUNT" in result.stdout


def test_overlay_failure_routes_to_contract_reflection_even_with_downstream_owner(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    write_rows(
        ip_dir / "sim" / "scoreboard_events.jsonl",
        [{"goal_id": "EQ_PAYLOAD", "scenario_id": "SC_PAYLOAD", "passed": True, "rtl_observed": {"sram_wr_strb": 0x1FFFF}}],
    )
    source = _semantic_contracts()
    first_map(source, "contract_refs")["contract_ref"] = "STATE_PAYLOAD_COUNT"
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    report = read_json(ip_dir / "signoff" / "contract_check.json")
    route = map_field(report, "owner_route")
    routing_artifact = read_json(ip_dir / "signoff" / "contract_owner_routing.json")
    assert route["owner_workflow"] == "contract-reflection"
    assert routing_artifact["owner_workflow"] == "contract-reflection"
    assert "semantic_contract_overlay" in str(route["reason"])
    assert "semantic_contract_overlay" in str(routing_artifact["reason"])


def test_semantic_overlay_reconciles_removed_managed_entries_without_deleting_legacy(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    first = _run_semantic_overlay(tmp_path)
    assert first.returncode == 0, first.stdout
    source = copy.deepcopy(_semantic_contracts())
    requirement = first_map(source, "requirements")
    obligation = first_map(requirement, "obligations")
    reflection = first_map(source, "contract_refs")
    requirement["requirement_id"] = "REQ_SEMANTIC_PAYLOAD_RENAMED"
    obligation["obligation_id"] = "OBL_SEMANTIC_PAYLOAD_COUNT_RENAMED"
    semantic_ref: list[JsonValue] = ["SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED"]
    obligation["contract_refs"] = semantic_ref
    reflection["contract_ref"] = "SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED"
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    second = _run_semantic_overlay(tmp_path)

    assert second.returncode == 0, second.stdout
    requirements = read_json(ip_dir / "verify" / "requirements_index.json")
    contract = read_json(ip_dir / "verify" / "evidence_contract.json")
    reflection_report = read_json(ip_dir / "verify" / "contract_reflection.json")
    requirement_ids = _ids(requirements, "requirements", "requirement_id")
    obligation_ids = _ids(contract, "obligations", "obligation_id")
    contract_refs = _ids(reflection_report, "contract_refs", "contract_ref")
    assert "REQ_PAYLOAD" in requirement_ids
    assert "REQ_SEMANTIC_PAYLOAD" not in requirement_ids
    assert "REQ_SEMANTIC_PAYLOAD_RENAMED" in requirement_ids
    assert "OBL_PAYLOAD_COUNT" in obligation_ids
    assert "OBL_SEMANTIC_PAYLOAD_COUNT" not in obligation_ids
    assert "OBL_SEMANTIC_PAYLOAD_COUNT_RENAMED" in obligation_ids
    assert "STATE_PAYLOAD_COUNT" in contract_refs
    assert "SEMANTIC_STATE_PAYLOAD_COUNT" not in contract_refs
    assert "SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED" in contract_refs


@pytest.mark.parametrize(
    ("mutation", "expected"),
    [
        ("missing_obligations", "missing obligation_ids"),
        ("missing_evidence_rows", "missing evidence_rows"),
        ("missing_obligation_contract_ref", "missing contract_refs"),
        ("missing_matching_evidence", "no matching scoreboard row"),
        ("empty_evidence_match", "evidence row match must include goal_id or scenario_id"),
        ("undeclared_contract_ref", "references undeclared contract_ref SEMANTIC_REF_WITHOUT_REFLECTION"),
    ],
)
def test_required_contract_closure_fails_missing_semantic_coverage(tmp_path: Path, mutation: str, expected: str) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    _write_legacy_reflection(ip_dir)
    source = copy.deepcopy(_semantic_contracts())
    requirement = first_map(source, "requirements")
    obligation = first_map(requirement, "obligations")
    if mutation == "missing_obligations":
        requirement["obligations"] = []
    elif mutation == "missing_evidence_rows":
        obligation.pop("evidence_rows", None)
    elif mutation == "missing_obligation_contract_ref":
        obligation["contract_refs"] = []
    elif mutation == "missing_matching_evidence":
        evidence_row: JsonMap = {"artifact": "sim/scoreboard_events.jsonl", "match": {"goal_id": "NO_MATCH"}}
        evidence_rows: list[JsonValue] = [evidence_row]
        obligation["evidence_rows"] = evidence_rows
    elif mutation == "empty_evidence_match":
        evidence_row = {"artifact": "sim/scoreboard_events.jsonl", "match": {}}
        obligation["evidence_rows"] = [evidence_row]
    elif mutation == "undeclared_contract_ref":
        contract_refs: list[JsonValue] = ["SEMANTIC_REF_WITHOUT_REFLECTION"]
        empty_refs: list[JsonValue] = []
        obligation["contract_refs"] = contract_refs
        source["contract_refs"] = empty_refs
    write_json(ip_dir / "verify" / "semantic_contracts.json", source)

    result = _run_contract_check(tmp_path, require_contract_closure=True)

    assert result.returncode == 1
    assert expected in result.stdout
