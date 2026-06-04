from __future__ import annotations

import copy
import hashlib
import subprocess
from pathlib import Path

from .contract_reflection_helpers import EVIDENCE_SCRIPT, REFLECTION_SCRIPT, SEMANTIC_OVERLAY_SCRIPT, JsonMap, first_map, make_contract_ip, read_json, write_json
from .test_semantic_contract_required_closure import _reflection_entry, _semantic_contracts, _write_stage_artifacts


def _run_overlay(root: Path) -> subprocess.CompletedProcess[str]:
    return subprocess.run(
        ["python3", str(SEMANTIC_OVERLAY_SCRIPT), "contract_ip", "--root", str(root)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )


def _mutate_semantic_source(source: JsonMap) -> JsonMap:
    changed = copy.deepcopy(source)
    requirement = first_map(changed, "requirements")
    requirement["claim"] = "Semantic payload count closure changed after generated artifacts were written."
    return changed


def _rename_semantic_source(source: JsonMap) -> JsonMap:
    changed = copy.deepcopy(source)
    requirement = first_map(changed, "requirements")
    obligation = first_map(requirement, "obligations")
    ref = first_map(changed, "contract_refs")
    requirement["requirement_id"] = "REQ_SEMANTIC_PAYLOAD_RENAMED"
    obligation["obligation_id"] = "OBL_SEMANTIC_PAYLOAD_COUNT_RENAMED"
    obligation["contract_refs"] = ["SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED"]
    ref["contract_ref"] = "SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED"
    return changed


def _source_hash(ip_dir: Path) -> str:
    return hashlib.sha256((ip_dir / "verify" / "semantic_contracts.json").read_bytes()).hexdigest()


def _set_artifact_hash(ip_dir: Path, rel: str, sha256: str) -> None:
    path = ip_dir / rel
    artifact = read_json(path)
    fingerprint = artifact["semantic_source_fingerprint"]
    assert isinstance(fingerprint, dict)
    fingerprint["sha256"] = sha256
    write_json(path, artifact)


def test_semantic_overlay_stamps_source_fingerprint_on_generated_artifacts(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())

    result = _run_overlay(tmp_path)

    assert result.returncode == 0, result.stdout
    for rel in ("requirements_index.json", "evidence_contract.json", "contract_reflection.json"):
        artifact = read_json(ip_dir / "verify" / rel)
        fingerprint = artifact["semantic_source_fingerprint"]
        assert isinstance(fingerprint, dict)
        assert fingerprint["artifact"] == "verify/semantic_contracts.json"
        assert fingerprint["sha256"] == _source_hash(ip_dir)


def test_evidence_checker_rejects_stale_semantic_contract_artifact(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    overlay = _run_overlay(tmp_path)
    assert overlay.returncode == 0, overlay.stdout
    write_json(ip_dir / "verify" / "semantic_contracts.json", _mutate_semantic_source(_semantic_contracts()))

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "semantic source fingerprint mismatch in verify/evidence_contract.json" in result.stdout


def test_evidence_checker_rejects_stale_requirements_index_fingerprint(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    overlay = _run_overlay(tmp_path)
    assert overlay.returncode == 0, overlay.stdout
    _set_artifact_hash(ip_dir, "verify/requirements_index.json", "0" * 64)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "semantic source fingerprint mismatch in verify/requirements_index.json" in result.stdout


def test_evidence_checker_rejects_forged_current_fingerprint_on_stale_semantic_content(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    overlay = _run_overlay(tmp_path)
    assert overlay.returncode == 0, overlay.stdout
    write_json(ip_dir / "verify" / "semantic_contracts.json", _rename_semantic_source(_semantic_contracts()))
    current_hash = _source_hash(ip_dir)
    _set_artifact_hash(ip_dir, "verify/requirements_index.json", current_hash)
    _set_artifact_hash(ip_dir, "verify/evidence_contract.json", current_hash)

    result = subprocess.run(
        ["python3", str(EVIDENCE_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing semantic obligation OBL_SEMANTIC_PAYLOAD_COUNT_RENAMED" in result.stdout


def test_reflection_checker_rejects_stale_semantic_reflection_artifact(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    legacy_reflection: JsonMap = {"contract_refs": [_reflection_entry()], "schema_version": 1, "type": "contract_reflection"}
    write_json(ip_dir / "verify" / "contract_reflection.json", legacy_reflection)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    overlay = _run_overlay(tmp_path)
    assert overlay.returncode == 0, overlay.stdout
    write_json(ip_dir / "verify" / "semantic_contracts.json", _mutate_semantic_source(_semantic_contracts()))

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "semantic source fingerprint mismatch in verify/contract_reflection.json" in result.stdout


def test_reflection_checker_rejects_forged_current_fingerprint_on_stale_semantic_content(tmp_path: Path) -> None:
    ip_dir = make_contract_ip(tmp_path)
    _write_stage_artifacts(ip_dir)
    legacy_reflection: JsonMap = {"contract_refs": [_reflection_entry()], "schema_version": 1, "type": "contract_reflection"}
    write_json(ip_dir / "verify" / "contract_reflection.json", legacy_reflection)
    write_json(ip_dir / "verify" / "semantic_contracts.json", _semantic_contracts())
    overlay = _run_overlay(tmp_path)
    assert overlay.returncode == 0, overlay.stdout
    write_json(ip_dir / "verify" / "semantic_contracts.json", _rename_semantic_source(_semantic_contracts()))
    current_hash = _source_hash(ip_dir)
    _set_artifact_hash(ip_dir, "verify/evidence_contract.json", current_hash)
    _set_artifact_hash(ip_dir, "verify/contract_reflection.json", current_hash)

    result = subprocess.run(
        ["python3", str(REFLECTION_SCRIPT), "contract_ip", "--root", str(tmp_path)],
        text=True,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )

    assert result.returncode == 1
    assert "missing semantic contract_ref SEMANTIC_STATE_PAYLOAD_COUNT_RENAMED" in result.stdout
