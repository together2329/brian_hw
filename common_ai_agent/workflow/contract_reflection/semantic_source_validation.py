from __future__ import annotations

from typing import Final

from workflow.contract_reflection.evidence_contract_json import JsonMap, as_list, as_map, strings, text


DOWNGRADED_STATUSES: Final = {"deferred", "optional", "waived"}


def source_issues(source: JsonMap) -> list[str]:
    issues: list[str] = []
    if text(source.get("type")) != "semantic_contracts":
        issues.append("semantic_contracts type must be semantic_contracts")
    schema_version = source.get("schema_version")
    if not isinstance(schema_version, int) or isinstance(schema_version, bool) or schema_version != 1:
        issues.append("semantic_contracts schema_version must be 1")
    declared_refs = _declared_ref_issues(source, issues)
    _requirement_issues(source, declared_refs, issues)
    return issues


def _declared_ref_issues(source: JsonMap, issues: list[str]) -> set[str]:
    declared_refs: set[str] = set()
    for item in as_list(source.get("contract_refs")):
        ref = text(as_map(item).get("contract_ref"))
        if not ref:
            issues.append("semantic contract_ref missing contract_ref")
        elif ref in declared_refs:
            issues.append(f"duplicate semantic contract_ref {ref}")
        else:
            declared_refs.add(ref)
    return declared_refs


def _requirement_issues(source: JsonMap, declared_refs: set[str], issues: list[str]) -> None:
    requirements = [as_map(item) for item in as_list(source.get("requirements"))]
    if not requirements:
        issues.append("semantic_contracts requires at least one requirement")
    req_ids: set[str] = set()
    obligation_ids: set[str] = set()
    for req in requirements:
        rid = text(req.get("requirement_id"))
        _requirement_id_issues(rid, req_ids, issues)
        if req.get("required") is False:
            issues.append(f"{rid or '<missing>'} cannot set required=false in semantic overlay")
        obligations = [as_map(obligation) for obligation in as_list(req.get("obligations"))]
        if not obligations:
            issues.append(f"{rid or '<missing>'}: missing obligation_ids")
        for obligation in obligations:
            _obligation_issues(rid, obligation, obligation_ids, declared_refs, issues)


def _requirement_id_issues(rid: str, req_ids: set[str], issues: list[str]) -> None:
    if not rid:
        issues.append("semantic requirement missing requirement_id")
    elif rid in req_ids:
        issues.append(f"duplicate semantic requirement {rid}")
    else:
        req_ids.add(rid)


def _obligation_issues(
    rid: str,
    obligation: JsonMap,
    obligation_ids: set[str],
    declared_refs: set[str],
    issues: list[str],
) -> None:
    oid = text(obligation.get("obligation_id"))
    _obligation_id_issues(rid, oid, obligation_ids, issues)
    if obligation.get("required") is False:
        issues.append(f"{oid or '<missing>'} cannot set required=false in semantic overlay")
    status = text(obligation.get("status")).lower()
    if status in DOWNGRADED_STATUSES:
        issues.append(f"{oid or '<missing>'} cannot set status={status} in semantic overlay")
    refs = strings(obligation.get("contract_refs"))
    if not refs:
        issues.append(f"{oid or '<missing>'}: missing contract_refs")
    evidence_rows = [as_map(row) for row in as_list(obligation.get("evidence_rows"))]
    if not evidence_rows:
        issues.append(f"{oid or '<missing>'}: missing evidence_rows")
    for ref in refs:
        if ref not in declared_refs:
            issues.append(f"{oid or '<missing>'}: references undeclared contract_ref {ref}")
    for row in evidence_rows:
        match = as_map(row.get("match"))
        if not (text(match.get("goal_id")) or text(match.get("scenario_id"))):
            issues.append(f"{oid or '<missing>'}: evidence row match must include goal_id or scenario_id")


def _obligation_id_issues(rid: str, oid: str, obligation_ids: set[str], issues: list[str]) -> None:
    if not oid:
        issues.append(f"{rid or '<missing>'} contains obligation without obligation_id")
    elif oid in obligation_ids:
        issues.append(f"duplicate semantic obligation {oid}")
    else:
        obligation_ids.add(oid)
