#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import sys
from pathlib import Path
from typing import Any, Final

WORKFLOW_ROOT = Path(__file__).resolve().parents[2]
if str(WORKFLOW_ROOT) not in sys.path:
    sys.path.insert(0, str(WORKFLOW_ROOT))

from behavioral_contracts import BehavioralContractError, behavioral_contract_ids, normalize_behavioral_contracts
from structural_contracts import StructuralContractError, normalize_structural_contracts, structural_contract_ids


JsonDoc = dict[str, Any]
REQ_GRAPH_FILES: Final[tuple[str, ...]] = (
    "req/behavioral_contracts.json",
    "req/contract_refs.json",
    "req/evidence_plan.json",
    "req/obligations.json",
    "req/requirements_index.json",
    "req/structural_contracts.json",
)
MANIFEST_HASHED_FILES: Final[tuple[str, ...]] = (*REQ_GRAPH_FILES, "req/locked_truth.md")
REQUIRED_FILES: Final[tuple[str, ...]] = (*MANIFEST_HASHED_FILES, "req/approval_manifest.json")
FUNCTION_CONTRACT_KEYS: Final[set[str]] = {
    "decision_table",
    "truth_table",
    "transactions",
    "state_transitions",
    "rules",
    "invariants",
    "outputs",
    "state_updates",
    "postconditions",
    "side_effects",
}
CYCLE_CONTRACT_KEYS: Final[set[str]] = {
    "cycle",
    "cycles",
    "cycle_model",
    "cycle_rules",
    "timing",
    "latency",
    "latencies",
    "clock",
    "reset",
    "handshake",
    "protocol",
    "ordering",
    "backpressure",
    "sample_condition",
}
CYCLE_WAIVER_KEYS: Final[set[str]] = {
    "cycle_model_waiver",
    "cycle_waiver",
    "cycle_model_not_applicable",
    "no_cycle_model",
}


def _load_json(path: Path, failures: list[str]) -> JsonDoc:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        failures.append(f"invalid JSON {path.name}: {exc}")
        return {}
    except OSError as exc:
        failures.append(f"cannot read {path}: {exc}")
        return {}
    if not isinstance(raw, dict):
        failures.append(f"{path.name} must contain a JSON object")
        return {}
    return raw


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _string_list(raw: Any) -> list[str]:
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if not isinstance(raw, list):
        return []
    return [item.strip() for item in raw if isinstance(item, str) and item.strip()]


def _collect_ids(entries: Any, key: str, failures: list[str], label: str) -> set[str]:
    if not isinstance(entries, list) or not entries:
        failures.append(f"{label} must be a non-empty list")
        return set()
    ids: set[str] = set()
    for entry in entries:
        if not isinstance(entry, dict):
            failures.append(f"{label} entries must be objects")
            continue
        item_id = entry.get(key)
        if not isinstance(item_id, str) or not item_id.strip():
            failures.append(f"{label} entry requires {key}")
            continue
        if item_id in ids:
            failures.append(f"duplicate {key} {item_id}")
        ids.add(item_id)
    return ids


def _check_refs(owner: str, refs: list[str], known: set[str], label: str, failures: list[str]) -> None:
    if not refs:
        failures.append(f"{owner} requires at least one {label} ref")
        return
    for ref in refs:
        if ref not in known:
            failures.append(f"{owner} references unknown {label} {ref}")


def _check_manifest_files(ip: str, root: Path, manifest: JsonDoc, failures: list[str]) -> None:
    files = manifest.get("files")
    if not isinstance(files, dict):
        failures.append("approval_manifest.json requires files object")
        return
    for rel in MANIFEST_HASHED_FILES:
        info = files.get(rel)
        path = root / ip / rel
        if not isinstance(info, dict):
            failures.append(f"manifest missing {rel}")
            continue
        expected_path = f"{ip}/{rel}"
        if info.get("path") != expected_path:
            failures.append(f"path mismatch for {rel}: {info.get('path')!r}")
        if not path.is_file():
            failures.append(f"missing {expected_path}")
            continue
        data = path.read_bytes()
        if info.get("bytes") != len(data):
            failures.append(f"byte count mismatch for {rel}")
        if info.get("sha256") != hashlib.sha256(data).hexdigest():
            failures.append(f"hash mismatch for {rel}")


def _check_requirement_status(manifest: JsonDoc, failures: list[str]) -> None:
    if manifest.get("status") != "requirements_locked":
        failures.append("manifest status must be requirements_locked")
    requirements = manifest.get("requirements")
    if not isinstance(requirements, list) or not requirements:
        failures.append("manifest requirements must be a non-empty list")
        return
    for item in requirements:
        if not isinstance(item, dict):
            failures.append("manifest requirement entries must be objects")
            continue
        status = str(item.get("status") or "").lower()
        if item.get("required") is not False and status not in {"locked", "approved"}:
            failures.append(f"required manifest requirement {item.get('requirement_id')} is not locked")


def _has_text(entry: JsonDoc, keys: tuple[str, ...]) -> bool:
    return any(isinstance(entry.get(key), str) and entry.get(key, "").strip() for key in keys)


def _present(value: Any) -> bool:
    if value is None or value is False:
        return False
    if isinstance(value, str):
        text = value.strip()
        return bool(text) and text.lower() not in {"none", "n/a", "na", "tbd", "todo", "unknown"}
    if isinstance(value, (list, tuple, set, dict)):
        return bool(value)
    return True


def _has_structured_value(value: Any) -> bool:
    if isinstance(value, dict):
        return any(_has_structured_value(child) for child in value.values())
    if isinstance(value, list):
        return any(_has_structured_value(child) for child in value)
    return _present(value)


def _has_machine_contract(entry: JsonDoc) -> bool:
    if _has_text(entry, ("contract_path", "observable", "signal", "register", "stage", "validator", "pass_condition")):
        return True
    for key in ("stage_contracts", "observables", "fields", "checks", "acceptance_criteria", "pass_conditions"):
        value = entry.get(key)
        if isinstance(value, list) and value:
            return True
    return False


def _has_function_semantics(entry: JsonDoc) -> bool:
    return any(_has_structured_value(entry.get(key)) for key in FUNCTION_CONTRACT_KEYS if key in entry)


def _has_cycle_waiver(entry: JsonDoc) -> bool:
    return any(_present(entry.get(key)) for key in CYCLE_WAIVER_KEYS)


def _stage_mentions_cycle_semantics(entry: JsonDoc) -> bool:
    for stage_contract in entry.get("stage_contracts") or []:
        if not isinstance(stage_contract, dict):
            continue
        stage = str(stage_contract.get("stage") or "").lower()
        blob = json.dumps(stage_contract, sort_keys=True).lower()
        if stage in {"cycle", "cycle_model", "cl", "timing", "protocol", "sva", "rtl", "tb", "sim"} and any(
            token in blob
            for token in (
                "cycle",
                "timing",
                "latency",
                "clock",
                "reset",
                "handshake",
                "ordering",
                "backpressure",
                "protocol",
            )
        ):
            return True
    return False


def _has_cycle_semantics(entry: JsonDoc) -> bool:
    if _has_cycle_waiver(entry):
        return True
    if any(_has_structured_value(entry.get(key)) for key in CYCLE_CONTRACT_KEYS if key in entry):
        return True
    for key in ("decision_table", "truth_table", "transactions", "state_transitions", "rules"):
        if isinstance(entry.get(key), list):
            for row in entry[key]:
                if isinstance(row, dict) and any(_has_structured_value(row.get(cycle_key)) for cycle_key in CYCLE_CONTRACT_KEYS):
                    return True
    return _stage_mentions_cycle_semantics(entry)


def _check_graph(
    ip: str,
    req_doc: JsonDoc,
    obl_doc: JsonDoc,
    con_doc: JsonDoc,
    structural_doc: JsonDoc,
    behavioral_doc: JsonDoc,
    ev_doc: JsonDoc,
    failures: list[str],
    *,
    require_locked_status: bool,
) -> JsonDoc:
    requirements = req_doc.get("requirements")
    obligations = obl_doc.get("obligations")
    contracts = con_doc.get("contract_refs")
    evidence = ev_doc.get("evidence_plan")
    req_ids = _collect_ids(requirements, "requirement_id", failures, "requirements")
    obl_ids = _collect_ids(obligations, "obligation_id", failures, "obligations")
    con_ids = _collect_ids(contracts, "contract_ref_id", failures, "contract_refs")
    structural_failed = False
    behavioral_failed = False
    try:
        normalized_structural = normalize_structural_contracts(
            str(req_doc.get("ip") or structural_doc.get("ip") or ""),
            structural_doc,
            known_obligation_ids=obl_ids,
        )
        structural_ids = structural_contract_ids(normalized_structural)
    except StructuralContractError as exc:
        failures.append(str(exc))
        structural_ids = set()
        structural_failed = True
    try:
        normalized_behavioral = normalize_behavioral_contracts(
            str(req_doc.get("ip") or behavioral_doc.get("ip") or ""),
            behavioral_doc,
            known_obligation_ids=obl_ids,
        )
        behavioral_ids = behavioral_contract_ids(normalized_behavioral)
    except BehavioralContractError as exc:
        failures.append(str(exc))
        behavioral_ids = set()
        behavioral_failed = True

    # Shape tolerance (validators are liberal in shape, strict in semantics):
    # a cross-link carries identical information in either direction, so a
    # link declared on ONE side is derived for the other instead of failing
    # the bundle, and synonym key names are accepted and normalized here.
    def _refs_of(entry: JsonDoc, *keys: str) -> list[str]:
        for key in keys:
            values = _string_list(entry.get(key))
            if values:
                return values
        return []

    req_to_obls: dict[str, set[str]] = {}
    obl_to_reqs: dict[str, set[str]] = {}
    obl_to_cons: dict[str, set[str]] = {}
    con_to_obls: dict[str, set[str]] = {}
    for entry in requirements if isinstance(requirements, list) else []:
        if isinstance(entry, dict):
            rid = str(entry.get("requirement_id") or "")
            for ref in _refs_of(entry, "obligation_refs", "obligations", "obligation_ids"):
                req_to_obls.setdefault(rid, set()).add(ref)
                obl_to_reqs.setdefault(ref, set()).add(rid)
    for entry in obligations if isinstance(obligations, list) else []:
        if isinstance(entry, dict):
            oid = str(entry.get("obligation_id") or "")
            for ref in _refs_of(entry, "requirement_refs", "requirements", "requirement_ids"):
                obl_to_reqs.setdefault(oid, set()).add(ref)
                req_to_obls.setdefault(ref, set()).add(oid)
            for ref in _refs_of(entry, "contract_refs", "contracts", "contract_ref_ids"):
                obl_to_cons.setdefault(oid, set()).add(ref)
                con_to_obls.setdefault(ref, set()).add(oid)
    for entry in contracts if isinstance(contracts, list) else []:
        if isinstance(entry, dict):
            cid = str(entry.get("contract_ref_id") or "")
            for ref in _refs_of(entry, "obligation_refs", "obligations", "obligation_ids"):
                con_to_obls.setdefault(cid, set()).add(ref)
                obl_to_cons.setdefault(ref, set()).add(cid)
    all_contract_ids = con_ids | structural_ids | behavioral_ids
    evidence_entries = evidence if isinstance(evidence, list) else []
    evidence_contract_ids = {
        str(entry.get("contract_ref")).strip()
        for entry in evidence_entries
        if isinstance(entry, dict) and isinstance(entry.get("contract_ref"), str) and str(entry.get("contract_ref")).strip()
    }
    for entry in requirements if isinstance(requirements, list) else []:
        if isinstance(entry, dict):
            req_id = str(entry.get("requirement_id") or "<missing requirement_id>")
            if not _has_text(entry, ("title",)):
                failures.append(f"{req_id} requires title")
            if not _has_text(entry, ("statement", "requirement")):
                failures.append(f"{req_id} requires statement")
            _check_refs(
                req_id,
                _refs_of(entry, "obligation_refs", "obligations", "obligation_ids")
                or sorted(req_to_obls.get(req_id, set())),
                obl_ids, "obligation", failures,
            )
            if (
                require_locked_status
                and entry.get("required") is not False
                and str(entry.get("status") or "").lower() not in {"locked", "approved"}
            ):
                failures.append(f"required requirement {req_id} is not locked")
    for entry in obligations if isinstance(obligations, list) else []:
        if isinstance(entry, dict):
            obl_id = str(entry.get("obligation_id") or "<missing obligation_id>")
            if not _has_text(entry, ("statement", "obligation")):
                failures.append(f"{obl_id} requires statement")
            _check_refs(
                obl_id,
                _refs_of(entry, "requirement_refs", "requirements", "requirement_ids")
                or sorted(obl_to_reqs.get(obl_id, set())),
                req_ids, "requirement", failures,
            )
            _check_refs(
                obl_id,
                _refs_of(entry, "contract_refs", "contracts", "contract_ref_ids")
                or sorted(obl_to_cons.get(obl_id, set())),
                con_ids, "contract_ref", failures,
            )
            structural_refs = _refs_of(entry, "structural_contract_refs", "structural_contracts")
            behavioral_refs = _refs_of(entry, "behavioral_contract_refs", "behavioral_contracts")
            if not structural_refs and not behavioral_refs:
                failures.append(
                    f"{obl_id} requires at least one structural_contract_ref or behavioral_contract_ref; "
                    "contract_refs alone are anchor refs, not implementation authority"
                )
            # When the contract doc itself failed normalization the ID set is
            # empty and every ref would cascade into a misleading
            # "unknown ..." failure; the normalization failure already says
            # what to fix, so suppress the dependent errors.
            if not structural_failed:
                for ref in structural_refs:
                    if ref not in structural_ids:
                        failures.append(f"{obl_id} references unknown structural_contract {ref}")
            if not behavioral_failed:
                for ref in behavioral_refs:
                    if ref not in behavioral_ids:
                        failures.append(f"{obl_id} references unknown behavioral_contract {ref}")
    for entry in contracts if isinstance(contracts, list) else []:
        if isinstance(entry, dict):
            con_id = str(entry.get("contract_ref_id") or "<missing contract_ref_id>")
            if not _has_machine_contract(entry):
                failures.append(
                    f"{con_id} requires machine-checkable contract detail "
                    "(stage_contracts/checks/observables/validator/pass_condition, not title-only anchor text)"
                )
            _check_refs(
                con_id,
                _refs_of(entry, "obligation_refs", "obligations", "obligation_ids")
                or sorted(con_to_obls.get(con_id, set())),
                obl_ids, "obligation", failures,
            )
    for entry in behavioral_doc.get("contracts") or []:
        if not isinstance(entry, dict):
            continue
        contract_id = str(entry.get("id") or entry.get("behavioral_contract_id") or entry.get("contract_ref_id") or "").strip()
        label = contract_id or "<missing behavioral contract id>"
        if not _has_function_semantics(entry):
            failures.append(f"{label} requires function semantics in decision_table/truth_table/transactions/rules/state effects")
        if not _has_cycle_semantics(entry):
            failures.append(f"{label} requires cycle/timing semantics or an explicit cycle waiver")
    for entry in evidence if isinstance(evidence, list) else []:
        if not isinstance(entry, dict):
            failures.append("evidence_plan entries must be objects")
            continue
        evidence_id = str(entry.get("evidence_id") or "<missing evidence_id>")
        contract_ref = entry.get("contract_ref")
        if not isinstance(contract_ref, str) or not contract_ref.strip():
            failures.append(f"{evidence_id} requires contract_ref")
        elif contract_ref not in all_contract_ids:
            failures.append(f"{evidence_id} references unknown contract_ref {contract_ref}")
        for key in ("artifact", "validator", "pass_condition"):
            if not isinstance(entry.get(key), str) or not entry.get(key, "").strip():
                failures.append(f"{evidence_id} requires {key}")
    for contract_id in sorted(all_contract_ids - evidence_contract_ids):
        failures.append(f"{contract_id} lacks evidence_plan closure")
    closure = _build_contract_closure(
        ip,
        con_doc,
        structural_doc,
        behavioral_doc,
        ev_doc,
        central_ids=con_ids,
        structural_ids=structural_ids,
        behavioral_ids=behavioral_ids,
    )
    for item in closure.get("contracts", []):
        if not isinstance(item, dict):
            continue
        if item.get("status") != "closed":
            failures.append(f"{item.get('contract_ref')} lacks evidence closure")
    return closure


def _entry_obligation_refs(entry: JsonDoc) -> list[str]:
    return _string_list(entry.get("obligation_refs")) or _string_list(entry.get("obligations"))


def _build_contract_closure(
    ip: str,
    con_doc: JsonDoc,
    structural_doc: JsonDoc,
    behavioral_doc: JsonDoc,
    ev_doc: JsonDoc,
    *,
    central_ids: set[str],
    structural_ids: set[str],
    behavioral_ids: set[str],
) -> JsonDoc:
    evidence = [item for item in (ev_doc.get("evidence_plan") or []) if isinstance(item, dict)]
    evidence_by_contract: dict[str, list[JsonDoc]] = {}
    for entry in evidence:
        ref = entry.get("contract_ref")
        if isinstance(ref, str) and ref.strip():
            evidence_by_contract.setdefault(ref.strip(), []).append(entry)

    contracts: list[JsonDoc] = []
    for entry in con_doc.get("contract_refs") or []:
        if not isinstance(entry, dict):
            continue
        contract_id = str(entry.get("contract_ref_id") or "").strip()
        if not contract_id or contract_id not in central_ids:
            continue
        contracts.append(_closure_entry(contract_id, "contract_ref", _entry_obligation_refs(entry), evidence_by_contract))
    for entry in structural_doc.get("contracts") or []:
        if not isinstance(entry, dict):
            continue
        contract_id = str(entry.get("id") or entry.get("contract_id") or entry.get("contract_ref_id") or "").strip()
        if not contract_id or contract_id not in structural_ids:
            continue
        contracts.append(_closure_entry(contract_id, "structural_contract", _entry_obligation_refs(entry), evidence_by_contract))
    for entry in behavioral_doc.get("contracts") or []:
        if not isinstance(entry, dict):
            continue
        contract_id = str(entry.get("id") or entry.get("behavioral_contract_id") or entry.get("contract_ref_id") or "").strip()
        if not contract_id or contract_id not in behavioral_ids:
            continue
        contracts.append(_closure_entry(contract_id, "behavioral_contract", _entry_obligation_refs(entry), evidence_by_contract))

    closed = sum(1 for item in contracts if item.get("status") == "closed")
    required = [item for item in contracts if item.get("kind") in {"contract_ref", "structural_contract", "behavioral_contract"}]
    required_closed = sum(1 for item in required if item.get("status") == "closed")
    return {
        "schema_version": 1,
        "type": "contract_authority_closure",
        "ip": ip,
        "authority": "req/ structural_contracts + behavioral_contracts + evidence_plan",
        "function_cycle_policy": "behavioral contracts require function semantics plus cycle/timing semantics or explicit waiver",
        "status": "pass" if required_closed == len(required) else "open",
        "summary": {
            "contracts": len(contracts),
            "closed": closed,
            "required_contracts": len(required),
            "required_closed": required_closed,
        },
        "contracts": sorted(contracts, key=lambda item: str(item["contract_ref"])),
    }


def _closure_entry(
    contract_id: str,
    kind: str,
    obligation_refs: list[str],
    evidence_by_contract: dict[str, list[JsonDoc]],
) -> JsonDoc:
    evidence = evidence_by_contract.get(contract_id, [])
    return {
        "contract_ref": contract_id,
        "kind": kind,
        "obligation_refs": obligation_refs,
        "evidence_refs": [
            str(entry.get("evidence_id"))
            for entry in evidence
            if isinstance(entry.get("evidence_id"), str) and str(entry.get("evidence_id")).strip()
        ],
        "artifacts": [
            str(entry.get("artifact"))
            for entry in evidence
            if isinstance(entry.get("artifact"), str) and str(entry.get("artifact")).strip()
        ],
        "validators": [
            str(entry.get("validator"))
            for entry in evidence
            if isinstance(entry.get("validator"), str) and str(entry.get("validator")).strip()
        ],
        "pass_conditions": [
            str(entry.get("pass_condition"))
            for entry in evidence
            if isinstance(entry.get("pass_condition"), str) and str(entry.get("pass_condition")).strip()
        ],
        "status": "closed" if evidence else "open",
    }


def check_locked_truth_bundle(ip: str, root: Path, *, review_candidate: bool = False) -> tuple[bool, list[str], JsonDoc]:
    root = root.resolve()
    req_dir = root / ip / "req"
    failures: list[str] = []
    required_files = REQ_GRAPH_FILES if review_candidate else REQUIRED_FILES
    for rel in required_files:
        if not (root / ip / rel).is_file():
            failures.append(f"missing {ip}/{rel}")
    req_doc = _load_json(req_dir / "requirements_index.json", failures)
    obl_doc = _load_json(req_dir / "obligations.json", failures)
    con_doc = _load_json(req_dir / "contract_refs.json", failures)
    structural_doc = _load_json(req_dir / "structural_contracts.json", failures)
    behavioral_doc = _load_json(req_dir / "behavioral_contracts.json", failures)
    ev_doc = _load_json(req_dir / "evidence_plan.json", failures)
    manifest: JsonDoc = {}
    if not review_candidate:
        manifest = _load_json(req_dir / "approval_manifest.json", failures)
        if manifest:
            _check_requirement_status(manifest, failures)
            _check_manifest_files(ip, root, manifest, failures)
    closure = _check_graph(
        ip,
        req_doc,
        obl_doc,
        con_doc,
        structural_doc,
        behavioral_doc,
        ev_doc,
        failures,
        require_locked_status=not review_candidate,
    )
    if closure:
        try:
            text = json.dumps(closure, indent=2, sort_keys=True) + "\n"
            (req_dir / "contract_closure.json").write_text(text, encoding="utf-8")
            (req_dir / "contract_authority_report.json").write_text(text, encoding="utf-8")
        except OSError as exc:
            failures.append(f"cannot write contract_closure.json: {exc}")
    summary: JsonDoc = {
        "mode": "review_candidate" if review_candidate else "locked",
        "requirements": len(req_doc.get("requirements") or []),
        "obligations": len(obl_doc.get("obligations") or []),
        "contract_refs": len(con_doc.get("contract_refs") or []),
        "structural_contracts": len(structural_doc.get("contracts") or []),
        "behavioral_contracts": len(behavioral_doc.get("contracts") or []),
        "evidence": len(ev_doc.get("evidence_plan") or []),
        "closed_contracts": (closure.get("summary") or {}).get("closed", 0) if isinstance(closure, dict) else 0,
    }
    return not failures, failures, summary


def main() -> int:
    parser = argparse.ArgumentParser(description="Validate deterministic locked-truth req bundle.")
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--review-candidate", action="store_true")
    args = parser.parse_args()
    ok, failures, summary = check_locked_truth_bundle(
        args.ip,
        Path(args.root),
        review_candidate=args.review_candidate,
    )
    counts = " ".join(f"{key}={value}" for key, value in summary.items())
    if ok:
        print(f"[check_locked_truth_bundle] PASS {args.ip}: {counts}")
        return 0
    print(f"[check_locked_truth_bundle] FAIL {args.ip}: {counts}")
    for failure in failures:
        print(f"- {failure}")
    return 1


if __name__ == "__main__":
    raise SystemExit(main())
