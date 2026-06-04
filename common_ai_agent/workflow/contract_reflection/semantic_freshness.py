from __future__ import annotations

import hashlib
from dataclasses import dataclass
from pathlib import Path
from typing import Final

from workflow.contract_reflection.evidence_contract_json import JsonList, JsonMap, as_list, as_map, json_strings, load_json, strings, text


SEMANTIC_SOURCE_REL: Final = "verify/semantic_contracts.json"
FINGERPRINT_KEY: Final = "semantic_source_fingerprint"
OVERLAY_SOURCE: Final = "semantic_contract_overlay"


@dataclass(frozen=True)
class SemanticSourceFingerprint:
    artifact: str
    sha256: str

    def as_json(self) -> JsonMap:
        return {"artifact": self.artifact, "sha256": self.sha256}


def semantic_source_exists(ip_dir: Path) -> bool:
    return (ip_dir / SEMANTIC_SOURCE_REL).is_file()


def semantic_source_fingerprint(ip_dir: Path) -> SemanticSourceFingerprint:
    path = ip_dir / SEMANTIC_SOURCE_REL
    digest = hashlib.sha256(path.read_bytes()).hexdigest()
    return SemanticSourceFingerprint(SEMANTIC_SOURCE_REL, digest)


def stamp_semantic_source(payload: JsonMap, ip_dir: Path) -> JsonMap:
    if semantic_source_exists(ip_dir):
        payload[FINGERPRINT_KEY] = semantic_source_fingerprint(ip_dir).as_json()
    return payload


def semantic_freshness_issues(ip_dir: Path, artifact_rel: str, payload: JsonMap) -> list[str]:
    if not semantic_source_exists(ip_dir):
        return []
    expected = semantic_source_fingerprint(ip_dir)
    observed = as_map(payload.get(FINGERPRINT_KEY))
    issues: list[str] = []
    if not observed:
        issues.append(f"missing semantic source fingerprint in {artifact_rel}")
    else:
        artifact = text(observed.get("artifact"))
        sha256 = text(observed.get("sha256"))
        if artifact != expected.artifact:
            issues.append(f"semantic source artifact mismatch in {artifact_rel}: {artifact}")
        if sha256 != expected.sha256:
            issues.append(f"semantic source fingerprint mismatch in {artifact_rel}")
    source = load_json(ip_dir / SEMANTIC_SOURCE_REL, "semantic_freshness")
    issues.extend(_semantic_content_issues(artifact_rel, payload, source))
    return issues


def _semantic_content_issues(artifact_rel: str, payload: JsonMap, source: JsonMap) -> list[str]:
    if artifact_rel == "verify/requirements_index.json":
        return _missing_or_changed(payload, "requirements", "requirement_id", _requirement_entries(source), "semantic requirement")
    if artifact_rel == "verify/evidence_contract.json":
        return _missing_or_changed(payload, "obligations", "obligation_id", _obligation_entries(source), "semantic obligation")
    if artifact_rel == "verify/contract_reflection.json":
        return _missing_or_changed(payload, "contract_refs", "contract_ref", _ref_entries(source), "semantic contract_ref")
    return []


def _missing_or_changed(payload: JsonMap, list_key: str, id_key: str, expected: dict[str, JsonMap], label: str) -> list[str]:
    actual = _entries_by_id(payload, list_key, id_key)
    issues: list[str] = []
    for item_id, expected_item in expected.items():
        actual_item = actual.get(item_id)
        if actual_item is None:
            issues.append(f"missing {label} {item_id}")
        elif actual_item != expected_item:
            issues.append(f"changed {label} {item_id}")
    return issues


def _entries_by_id(payload: JsonMap, list_key: str, id_key: str) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in as_list(payload.get(list_key)):
        data = as_map(item)
        item_id = text(data.get(id_key))
        if item_id:
            out[item_id] = data
    return out


def _requirement_entries(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in as_list(source.get("requirements")):
        req = as_map(item)
        obligation_ids: list[str] = []
        for obligation in as_list(req.get("obligations")):
            oid = text(as_map(obligation).get("obligation_id"))
            if oid:
                obligation_ids.append(oid)
        entry: JsonMap = {
            "claim": req.get("claim", ""),
            "obligation_ids": json_strings(obligation_ids),
            "required": req.get("required", True),
            "requirement_id": req.get("requirement_id", ""),
            "source": OVERLAY_SOURCE,
            "source_refs": json_strings(strings(req.get("source_refs"))),
        }
        rid = text(entry.get("requirement_id"))
        if rid:
            out[rid] = entry
    return out


def _obligation_entries(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in as_list(source.get("requirements")):
        req = as_map(item)
        rid = text(req.get("requirement_id"))
        for obligation in as_list(req.get("obligations")):
            data = dict(as_map(obligation))
            data["requirement_ids"] = json_strings([rid])
            data["source"] = OVERLAY_SOURCE
            oid = text(data.get("obligation_id"))
            if oid:
                out[oid] = data
    return out


def _ref_entries(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in as_list(source.get("contract_refs")):
        data = dict(as_map(item))
        data["source"] = OVERLAY_SOURCE
        ref = text(data.get("contract_ref"))
        if ref:
            out[ref] = data
    return out


def require_fresh_semantic_artifact(ip_dir: Path, artifact_rel: str, payload: JsonMap, label: str) -> None:
    issues = semantic_freshness_issues(ip_dir, artifact_rel, payload)
    if issues:
        raise SystemExit(f"[{label}] FAIL: {'; '.join(issues)}")
