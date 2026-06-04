from __future__ import annotations

import json
from pathlib import Path
from typing import Final

from workflow.contract_reflection.evidence_contract_json import (
    JsonList,
    JsonMap,
    as_list as _as_list,
    as_map as _as_map,
    json_strings as _json_strings,
    load_json as _load_json,
    strings as _strings,
    text as _text,
)
from workflow.contract_reflection.semantic_source_validation import source_issues as semantic_source_issues
from workflow.contract_reflection.semantic_freshness import stamp_semantic_source


SEMANTIC_FILE: Final = "verify/semantic_contracts.json"
OVERLAY_SOURCE: Final = "semantic_contract_overlay"


def run_semantic_overlay(ip_dir: Path) -> int:
    verify_dir = ip_dir / "verify"
    source = _load_json(ip_dir / SEMANTIC_FILE, "semantic_overlay")
    requirements = _load_json_or_default(
        verify_dir / "requirements_index.json",
        "semantic_overlay",
        {"requirements": [], "schema_version": 1, "type": "requirements_index"},
    )
    contract = _load_json_or_default(
        verify_dir / "evidence_contract.json",
        "semantic_overlay",
        {"obligations": [], "schema_version": 1, "type": "evidence_contract"},
    )
    reflection = _load_json_or_default(
        verify_dir / "contract_reflection.json",
        "semantic_overlay",
        {"contract_refs": [], "schema_version": 1, "type": "contract_reflection"},
    )
    issues = [*semantic_source_issues(source), *_collision_issues(requirements, source), *_collision_issues(contract, source), *_collision_issues(reflection, source)]
    if issues:
        raise SystemExit("[semantic_overlay] FAIL: " + "; ".join(issues))
    requirements = stamp_semantic_source(_merge_requirements(requirements, source), ip_dir)
    contract = stamp_semantic_source(_merge_obligations(contract, source), ip_dir)
    reflection = stamp_semantic_source(_merge_reflections(reflection, source), ip_dir)
    _write_json(verify_dir / "requirements_index.json", requirements)
    _write_json(verify_dir / "evidence_contract.json", contract)
    _write_json(verify_dir / "contract_reflection.json", reflection)
    print(
        "[semantic_overlay] wrote "
        f"{len(_semantic_req_ids(source))} requirements, "
        f"{len(_semantic_obligation_ids(source))} obligations, "
        f"{len(_as_list(source.get('contract_refs')))} contract_refs"
    )
    return 0


def _load_json_or_default(path: Path, label: str, default: JsonMap) -> JsonMap:
    if path.is_file():
        return _load_json(path, label)
    return default


def _write_json(path: Path, payload: JsonMap) -> None:
    _ = path.write_text(json.dumps(payload, indent=2, sort_keys=True) + "\n", encoding="utf-8")


def _replace_by_id(items: JsonList, id_key: str, replacement: JsonMap) -> JsonList:
    out: JsonList = []
    for item in items:
        data = _as_map(item)
        if data.get(id_key) != replacement.get(id_key):
            out.append(data)
    out.append(replacement)
    return out


def _semantic_req_ids(source: JsonMap) -> set[str]:
    req_ids: set[str] = set()
    for item in _as_list(source.get("requirements")):
        rid = _text(_as_map(item).get("requirement_id"))
        if rid:
            req_ids.add(rid)
    return req_ids


def _semantic_obligation_ids(source: JsonMap) -> set[str]:
    out: set[str] = set()
    for item in _as_list(source.get("requirements")):
        req = _as_map(item)
        for obligation in _as_list(req.get("obligations")):
            oid = _text(_as_map(obligation).get("obligation_id"))
            if oid:
                out.add(oid)
    return out


def _managed(data: JsonMap) -> bool:
    return _text(data.get("source")) == OVERLAY_SOURCE


def _legacy_semantic_match(data: JsonMap, replacement: JsonMap) -> bool:
    legacy = dict(replacement)
    _ = legacy.pop("source", None)
    return data == legacy


def _safe_to_replace(data: JsonMap, replacement: JsonMap) -> bool:
    return _managed(data) or data == replacement or _legacy_semantic_match(data, replacement)


def _semantic_requirement_entries(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in _as_list(source.get("requirements")):
        data = _requirement_entry(_as_map(item))
        rid = _text(data.get("requirement_id"))
        if rid:
            out[rid] = data
    return out


def _semantic_obligation_entries_by_id(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in _as_list(source.get("requirements")):
        for obligation in _obligation_entries(_as_map(item)):
            data = _as_map(obligation)
            oid = _text(data.get("obligation_id"))
            if oid:
                out[oid] = data
    return out


def _semantic_ref_entries_by_id(source: JsonMap) -> dict[str, JsonMap]:
    out: dict[str, JsonMap] = {}
    for item in _as_list(source.get("contract_refs")):
        data = dict(_as_map(item))
        contract_ref = _text(data.get("contract_ref"))
        if contract_ref:
            data["source"] = OVERLAY_SOURCE
            out[contract_ref] = data
    return out


def _collision_issues(existing: JsonMap, source: JsonMap) -> list[str]:
    req_ids = _semantic_req_ids(source)
    requirement_entries = _semantic_requirement_entries(source)
    obligation_entries = _semantic_obligation_entries_by_id(source)
    ref_entries = _semantic_ref_entries_by_id(source)
    issues: list[str] = []
    for item in _as_list(existing.get("requirements")):
        data = _as_map(item)
        rid = _text(data.get("requirement_id"))
        if rid in req_ids and not _safe_to_replace(data, requirement_entries[rid]):
            issues.append(f"semantic requirement collides with existing non-semantic requirement {rid}")
    for item in _as_list(existing.get("obligations")):
        data = _as_map(item)
        oid = _text(data.get("obligation_id"))
        refs = set(_strings(data.get("requirement_ids")))
        if oid in obligation_entries and not _safe_to_replace(data, obligation_entries[oid]):
            issues.append(f"semantic obligation collides with existing non-semantic obligation {oid}")
        elif refs.intersection(req_ids) and not _managed(data) and oid not in obligation_entries:
            issues.append(f"{oid or '<missing>'} references semantic requirement without semantic ownership")
    for item in _as_list(existing.get("contract_refs")):
        data = _as_map(item)
        ref = _text(data.get("contract_ref"))
        if ref in ref_entries and not _safe_to_replace(data, ref_entries[ref]):
            issues.append(f"semantic contract_ref collides with existing non-semantic contract_ref {ref}")
    return issues


def _without_semantic_obligations(items: JsonList, source: JsonMap) -> JsonList:
    obligation_entries = _semantic_obligation_entries_by_id(source)
    out: JsonList = []
    for item in items:
        data = _as_map(item)
        oid = _text(data.get("obligation_id"))
        replaces_source_obligation = oid in obligation_entries and _safe_to_replace(data, obligation_entries[oid])
        if _managed(data) or replaces_source_obligation:
            continue
        out.append(data)
    return out


def _without_managed(items: JsonList) -> JsonList:
    out: JsonList = []
    for item in items:
        data = _as_map(item)
        if not _managed(data):
            out.append(data)
    return out


def _requirement_entry(req: JsonMap) -> JsonMap:
    obligation_ids: list[str] = []
    for item in _as_list(req.get("obligations")):
        oid = _text(_as_map(item).get("obligation_id"))
        if oid:
            obligation_ids.append(oid)
    return {
        "claim": req.get("claim", ""),
        "obligation_ids": _json_strings(obligation_ids),
        "required": req.get("required", True),
        "requirement_id": req.get("requirement_id", ""),
        "source": OVERLAY_SOURCE,
        "source_refs": _json_strings(_strings(req.get("source_refs"))),
    }


def _obligation_entries(req: JsonMap) -> JsonList:
    rid = _text(req.get("requirement_id"))
    out: JsonList = []
    for item in _as_list(req.get("obligations")):
        data = dict(_as_map(item))
        data["requirement_ids"] = _json_strings([rid])
        data["source"] = OVERLAY_SOURCE
        out.append(data)
    return out


def _merge_requirements(existing: JsonMap, source: JsonMap) -> JsonMap:
    items = _without_managed(_as_list(existing.get("requirements")))
    for item in _as_list(source.get("requirements")):
        entry = _requirement_entry(_as_map(item))
        items = _replace_by_id(items, "requirement_id", entry)
    existing["requirements"] = items
    return existing


def _merge_obligations(existing: JsonMap, source: JsonMap) -> JsonMap:
    items = _without_semantic_obligations(_as_list(existing.get("obligations")), source)
    for item in _as_list(source.get("requirements")):
        items.extend(_obligation_entries(_as_map(item)))
    existing["obligations"] = items
    return existing


def _merge_reflections(existing: JsonMap, source: JsonMap) -> JsonMap:
    items = _without_managed(_as_list(existing.get("contract_refs")))
    for item in _as_list(source.get("contract_refs")):
        data = _as_map(item)
        if _text(data.get("contract_ref")):
            data["source"] = OVERLAY_SOURCE
            items = _replace_by_id(items, "contract_ref", data)
    existing["contract_refs"] = items
    return existing
