#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
from pathlib import Path
from typing import Any, Final


JsonDoc = dict[str, Any]
REQ_GRAPH_FILES: Final[tuple[str, ...]] = (
    "req/contract_refs.json",
    "req/evidence_plan.json",
    "req/obligations.json",
    "req/requirements_index.json",
)
MANIFEST_HASHED_FILES: Final[tuple[str, ...]] = (*REQ_GRAPH_FILES, "req/locked_truth.md")
REQUIRED_FILES: Final[tuple[str, ...]] = (*MANIFEST_HASHED_FILES, "req/approval_manifest.json")


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


def _has_machine_contract(entry: JsonDoc) -> bool:
    if _has_text(entry, ("statement", "title", "contract_path", "observable", "signal", "register", "stage")):
        return True
    for key in ("stage_contracts", "observables", "fields"):
        value = entry.get(key)
        if isinstance(value, list) and value:
            return True
    return False


def _check_graph(
    req_doc: JsonDoc,
    obl_doc: JsonDoc,
    con_doc: JsonDoc,
    ev_doc: JsonDoc,
    failures: list[str],
    *,
    require_locked_status: bool,
) -> None:
    requirements = req_doc.get("requirements")
    obligations = obl_doc.get("obligations")
    contracts = con_doc.get("contract_refs")
    evidence = ev_doc.get("evidence_plan")
    req_ids = _collect_ids(requirements, "requirement_id", failures, "requirements")
    obl_ids = _collect_ids(obligations, "obligation_id", failures, "obligations")
    con_ids = _collect_ids(contracts, "contract_ref_id", failures, "contract_refs")
    for entry in requirements if isinstance(requirements, list) else []:
        if isinstance(entry, dict):
            req_id = str(entry.get("requirement_id") or "<missing requirement_id>")
            if not _has_text(entry, ("title",)):
                failures.append(f"{req_id} requires title")
            if not _has_text(entry, ("statement", "requirement")):
                failures.append(f"{req_id} requires statement")
            _check_refs(req_id, _string_list(entry.get("obligation_refs")), obl_ids, "obligation", failures)
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
            _check_refs(obl_id, _string_list(entry.get("requirement_refs")), req_ids, "requirement", failures)
            _check_refs(obl_id, _string_list(entry.get("contract_refs")), con_ids, "contract_ref", failures)
    for entry in contracts if isinstance(contracts, list) else []:
        if isinstance(entry, dict):
            con_id = str(entry.get("contract_ref_id") or "<missing contract_ref_id>")
            if not _has_machine_contract(entry):
                failures.append(f"{con_id} requires machine-checkable contract detail")
            _check_refs(con_id, _string_list(entry.get("obligation_refs")), obl_ids, "obligation", failures)
    for entry in evidence if isinstance(evidence, list) else []:
        if not isinstance(entry, dict):
            failures.append("evidence_plan entries must be objects")
            continue
        evidence_id = str(entry.get("evidence_id") or "<missing evidence_id>")
        contract_ref = entry.get("contract_ref")
        if not isinstance(contract_ref, str) or not contract_ref.strip():
            failures.append(f"{evidence_id} requires contract_ref")
        elif contract_ref not in con_ids:
            failures.append(f"{evidence_id} references unknown contract_ref {contract_ref}")
        for key in ("artifact", "validator", "pass_condition"):
            if not isinstance(entry.get(key), str) or not entry.get(key, "").strip():
                failures.append(f"{evidence_id} requires {key}")


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
    ev_doc = _load_json(req_dir / "evidence_plan.json", failures)
    manifest: JsonDoc = {}
    if not review_candidate:
        manifest = _load_json(req_dir / "approval_manifest.json", failures)
        if manifest:
            _check_requirement_status(manifest, failures)
            _check_manifest_files(ip, root, manifest, failures)
    _check_graph(req_doc, obl_doc, con_doc, ev_doc, failures, require_locked_status=not review_candidate)
    summary: JsonDoc = {
        "mode": "review_candidate" if review_candidate else "locked",
        "requirements": len(req_doc.get("requirements") or []),
        "obligations": len(obl_doc.get("obligations") or []),
        "contract_refs": len(con_doc.get("contract_refs") or []),
        "evidence": len(ev_doc.get("evidence_plan") or []),
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
