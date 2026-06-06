#!/usr/bin/env python3
from __future__ import annotations

import argparse
import hashlib
import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Final


JsonDoc = dict[str, Any]
DESCRIPTION: Final[str] = "Lock a reviewed requirement set into deterministic req/ authority files."
OUTPUT_FILES: Final[tuple[str, ...]] = ("requirements_index.json", "obligations.json", "contract_refs.json", "evidence_plan.json", "locked_truth.md", "approval_manifest.json")
CANDIDATE_FILES: Final[tuple[str, ...]] = ("requirements_index.json", "obligations.json", "contract_refs.json", "evidence_plan.json")
LOCK_OUTPUT_FILES: Final[tuple[str, ...]] = ("locked_truth.md", "approval_manifest.json")
PLACEHOLDER_APPROVERS: Final[set[str]] = {"dryrun", "test", "placeholder", "unknown", "none", "na"}


def _atomic_write_text(path: Path, text: str) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    suffix = f".tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}"
    tmp = path.with_suffix(path.suffix + suffix)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _canonical_json(doc: JsonDoc) -> str:
    return json.dumps(doc, indent=2, sort_keys=True) + "\n"


def _sha256_bytes(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _load_json(path: Path) -> JsonDoc:
    try:
        raw = json.loads(path.read_text(encoding="utf-8"))
    except json.JSONDecodeError as exc:
        raise SystemExit(f"cannot parse draft JSON {path}: {exc}") from exc
    except OSError as exc:
        raise SystemExit(f"cannot read draft JSON {path}: {exc}") from exc
    if not isinstance(raw, dict):
        raise SystemExit("draft must be a JSON object")
    return raw


def _placeholder_approver(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    return normalized in PLACEHOLDER_APPROVERS


def _require_str(entry: JsonDoc, key: str, label: str) -> str:
    value = entry.get(key)
    if not isinstance(value, str) or not value.strip():
        raise SystemExit(f"{label} requires non-empty {key}")
    return value.strip()


def _list_of_dicts(raw: Any, label: str) -> list[JsonDoc]:
    if not isinstance(raw, list) or not raw:
        raise SystemExit(f"draft requires non-empty {label}")
    result = []
    for item in raw:
        if not isinstance(item, dict):
            raise SystemExit(f"{label} entries must be objects")
        result.append(dict(item))
    return result


def _string_list(entry: JsonDoc, key: str) -> list[str]:
    raw = entry.get(key)
    if raw is None:
        return []
    if isinstance(raw, str) and raw.strip():
        return [raw.strip()]
    if not isinstance(raw, list):
        raise SystemExit(f"{key} must be a list of strings")
    values: list[str] = []
    for item in raw:
        if not isinstance(item, str) or not item.strip():
            raise SystemExit(f"{key} must be a list of strings")
        values.append(item.strip())
    return sorted(dict.fromkeys(values))


def _unique_ids(entries: list[JsonDoc], key: str, label: str) -> set[str]:
    seen: set[str] = set()
    for entry in entries:
        item_id = _require_str(entry, key, label)
        if item_id in seen:
            raise SystemExit(f"duplicate {key}: {item_id}")
        seen.add(item_id)
    return seen


def _check_refs(owner: str, refs: list[str], known: set[str], label: str) -> None:
    for ref in refs:
        if ref not in known:
            raise SystemExit(f"{owner} references unknown {label} {ref}")


def _normalize_requirements(entries: list[JsonDoc], obligation_ids: set[str]) -> list[JsonDoc]:
    normalized: list[JsonDoc] = []
    for entry in entries:
        req_id = _require_str(entry, "requirement_id", "requirement")
        _require_str(entry, "title", req_id)
        _require_str(entry, "statement", req_id)
        required = entry.get("required") is not False
        refs = _string_list(entry, "obligation_refs")
        if required and not refs:
            raise SystemExit(f"{req_id} requires at least one obligation_ref")
        _check_refs(req_id, refs, obligation_ids, "obligation")
        item = dict(entry)
        item["requirement_id"] = req_id
        item["required"] = required
        item["status"] = "locked" if required else str(item.get("status") or "draft").strip().lower()
        item["obligation_refs"] = refs
        normalized.append(item)
    return sorted(normalized, key=lambda item: str(item["requirement_id"]))


def _normalize_ref_entries(
    entries: list[JsonDoc],
    *,
    id_key: str,
    refs_key: str,
    known_ids: set[str],
    known_label: str,
) -> list[JsonDoc]:
    normalized: list[JsonDoc] = []
    for entry in entries:
        item_id = _require_str(entry, id_key, id_key)
        refs = _string_list(entry, refs_key)
        if not refs:
            raise SystemExit(f"{item_id} requires {refs_key}")
        _check_refs(item_id, refs, known_ids, known_label)
        item = dict(entry)
        item[id_key] = item_id
        item[refs_key] = refs
        normalized.append(item)
    return sorted(normalized, key=lambda item: str(item[id_key]))


def _normalize_obligations(entries: list[JsonDoc], requirement_ids: set[str]) -> list[JsonDoc]:
    normalized = _normalize_ref_entries(entries, id_key="obligation_id", refs_key="requirement_refs", known_ids=requirement_ids, known_label="requirement")
    for item in normalized:
        _require_str(item, "statement", str(item["obligation_id"]))
        item["contract_refs"] = _string_list(item, "contract_refs")
    return normalized


def _normalize_contracts(entries: list[JsonDoc], obligation_ids: set[str]) -> list[JsonDoc]:
    return _normalize_ref_entries(entries, id_key="contract_ref_id", refs_key="obligation_refs", known_ids=obligation_ids, known_label="obligation")


def _normalize_evidence(entries: list[JsonDoc], contract_ids: set[str]) -> list[JsonDoc]:
    normalized: list[JsonDoc] = []
    for entry in entries:
        evidence_id = _require_str(entry, "evidence_id", "evidence")
        contract_ref = _require_str(entry, "contract_ref", evidence_id)
        _check_refs(evidence_id, [contract_ref], contract_ids, "contract_ref")
        _require_str(entry, "artifact", evidence_id)
        _require_str(entry, "validator", evidence_id)
        _require_str(entry, "pass_condition", evidence_id)
        item = dict(entry)
        item["evidence_id"] = evidence_id
        item["contract_ref"] = contract_ref
        normalized.append(item)
    return sorted(normalized, key=lambda item: str(item["evidence_id"]))


def _file_hashes(root: Path, ip: str, file_texts: dict[str, str]) -> JsonDoc:
    result: JsonDoc = {}
    for name in sorted(file_texts):
        rel = f"{ip}/req/{name}"
        data = file_texts[name].encode("utf-8")
        result[f"req/{name}"] = {"path": rel, "sha256": _sha256_bytes(data), "bytes": len(data)}
    return result


def _render_locked_truth(ip: str, approved_by: str, approved_at: str, docs: dict[str, JsonDoc], hashes: JsonDoc) -> str:
    lines = [
        f"# Locked Truth - {ip}",
        "",
        "## Approval",
        "- status: requirements_locked",
        f"- approved_by: {approved_by}",
        f"- approved_at_utc: {approved_at}",
        "",
    ]
    for title, key in (
        ("Requirements", "requirements_index"),
        ("Obligations", "obligations"),
        ("Contract Refs", "contract_refs"),
        ("Evidence Plan", "evidence_plan"),
    ):
        lines.extend([f"## {title}", "```json", _canonical_json(docs[key]).rstrip(), "```", ""])
    lines.append("## Source Hashes")
    for rel_path, info in sorted(hashes.items()):
        lines.append(f"- {rel_path}: sha256:{info['sha256']}")
    return "\n".join(lines).rstrip() + "\n"


def _build_docs(ip: str, draft_doc: JsonDoc) -> dict[str, JsonDoc]:
    if draft_doc.get("ip") not in (None, ip):
        raise SystemExit(f"draft ip mismatch: expected {ip}, got {draft_doc.get('ip')!r}")
    requirements_raw = _list_of_dicts(draft_doc.get("requirements"), "requirements")
    obligations_raw = _list_of_dicts(draft_doc.get("obligations"), "obligations")
    contracts_raw = _list_of_dicts(draft_doc.get("contract_refs"), "contract_refs")
    evidence_raw = _list_of_dicts(draft_doc.get("evidence_plan"), "evidence_plan")
    requirement_ids = _unique_ids(requirements_raw, "requirement_id", "requirement")
    obligation_ids = _unique_ids(obligations_raw, "obligation_id", "obligation")
    contract_ids = _unique_ids(contracts_raw, "contract_ref_id", "contract_ref")
    _unique_ids(evidence_raw, "evidence_id", "evidence")
    obligations = _normalize_obligations(obligations_raw, requirement_ids)
    requirements = _normalize_requirements(requirements_raw, obligation_ids)
    contracts = _normalize_contracts(contracts_raw, obligation_ids)
    evidence = _normalize_evidence(evidence_raw, contract_ids)
    for obligation in obligations:
        _check_refs(
            str(obligation["obligation_id"]),
            _string_list(obligation, "contract_refs"),
            contract_ids,
            "contract_ref",
        )
    return {
        "requirements_index": {"schema_version": 1, "type": "requirements_index", "ip": ip, "requirements": requirements},
        "obligations": {"schema_version": 1, "type": "obligations", "ip": ip, "obligations": obligations},
        "contract_refs": {"schema_version": 1, "type": "contract_refs", "ip": ip, "contract_refs": contracts},
        "evidence_plan": {"schema_version": 1, "type": "evidence_plan", "ip": ip, "evidence_plan": evidence},
    }


def _build_docs_from_candidate(ip: str, req_dir: Path) -> dict[str, JsonDoc]:
    docs = {
        "requirements": _load_json(req_dir / "requirements_index.json").get("requirements"),
        "obligations": _load_json(req_dir / "obligations.json").get("obligations"),
        "contract_refs": _load_json(req_dir / "contract_refs.json").get("contract_refs"),
        "evidence_plan": _load_json(req_dir / "evidence_plan.json").get("evidence_plan"),
    }
    return _build_docs(ip, {"ip": ip, **docs})


def _write_locked_docs(
    ip: str,
    root: Path,
    *,
    docs: dict[str, JsonDoc],
    approved_by: str,
    decision_note: str,
    source_rel: str,
    source_sha256: str,
) -> JsonDoc:
    req_dir = root / ip / "req"
    approved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    file_texts = {"requirements_index.json": _canonical_json(docs["requirements_index"]), "obligations.json": _canonical_json(docs["obligations"]), "contract_refs.json": _canonical_json(docs["contract_refs"]), "evidence_plan.json": _canonical_json(docs["evidence_plan"])}
    hashes = _file_hashes(root, ip, file_texts)
    locked_text = _render_locked_truth(ip, approved_by, approved_at, docs, hashes)
    file_texts["locked_truth.md"] = locked_text
    hashes = _file_hashes(root, ip, file_texts)
    bundle_hash = _sha256_bytes(_canonical_json(hashes).encode("utf-8"))
    requirements = [
        {"requirement_id": item["requirement_id"], "required": item["required"], "status": item["status"]}
        for item in docs["requirements_index"]["requirements"]
    ]
    manifest: JsonDoc = {"schema_version": 1, "type": "locked_truth_approval_manifest", "status": "requirements_locked", "ip": ip, "approved_by": approved_by, "approved_at_utc": approved_at, "decision_note": decision_note.strip(), "draft": source_rel, "draft_sha256": source_sha256, "bundle_sha256": bundle_hash, "requirements": requirements, "files": hashes}
    file_texts["approval_manifest.json"] = _canonical_json(manifest)
    for name, text in file_texts.items():
        _atomic_write_text(req_dir / name, text)
    return manifest


def lock_requirement_set(
    ip: str,
    root: Path,
    *,
    draft: Path,
    approved_by: str,
    decision_note: str = "",
    force: bool = False,
) -> JsonDoc:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", ip):
        raise SystemExit(f"invalid ip {ip!r}")
    approver = approved_by.strip()
    if not approver:
        raise SystemExit("--approved-by is required")
    if _placeholder_approver(approver):
        raise SystemExit("--approved-by must name the real human approver")
    root = root.resolve()
    req_dir = root / ip / "req"
    existing = [name for name in OUTPUT_FILES if (req_dir / name).exists()]
    if existing and not force:
        raise SystemExit(f"{ip}/req already exists; pass --force to replace: {', '.join(existing)}")
    draft_path = draft if draft.is_absolute() else root / draft
    draft_doc = _load_json(draft_path.resolve())
    docs = _build_docs(ip, draft_doc)
    return _write_locked_docs(
        ip,
        root,
        docs=docs,
        approved_by=approver,
        decision_note=decision_note,
        source_rel=_rel(draft_path.resolve(), root),
        source_sha256=_sha256_bytes(draft_path.read_bytes()),
    )


def lock_requirement_candidate(
    ip: str,
    root: Path,
    *,
    approved_by: str,
    decision_note: str = "",
    force: bool = False,
) -> JsonDoc:
    if not re.fullmatch(r"[A-Za-z][A-Za-z0-9_]*", ip):
        raise SystemExit(f"invalid ip {ip!r}")
    approver = approved_by.strip()
    if not approver:
        raise SystemExit("--approved-by is required")
    if _placeholder_approver(approver):
        raise SystemExit("--approved-by must name the real human approver")
    root = root.resolve()
    req_dir = root / ip / "req"
    missing = [name for name in CANDIDATE_FILES if not (req_dir / name).is_file()]
    if missing:
        raise SystemExit(f"{ip}/req candidate missing: {', '.join(missing)}")
    existing_lock = [name for name in LOCK_OUTPUT_FILES if (req_dir / name).exists()]
    if existing_lock and not force:
        raise SystemExit(f"{ip}/req already locked; pass --force to replace: {', '.join(existing_lock)}")
    docs = _build_docs_from_candidate(ip, req_dir)
    source_hashes = {
        name: _sha256_bytes((req_dir / name).read_bytes())
        for name in CANDIDATE_FILES
    }
    return _write_locked_docs(
        ip,
        root,
        docs=docs,
        approved_by=approver,
        decision_note=decision_note,
        source_rel=f"{ip}/req",
        source_sha256=_sha256_bytes(_canonical_json(source_hashes).encode("utf-8")),
    )


def main() -> int:
    parser = argparse.ArgumentParser(description=DESCRIPTION)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--draft")
    parser.add_argument("--from-candidate", action="store_true")
    parser.add_argument("--approved-by", required=True)
    parser.add_argument("--decision-note", default="")
    parser.add_argument("--force", action="store_true")
    args = parser.parse_args()
    if args.from_candidate:
        lock_requirement_candidate(args.ip, Path(args.root), approved_by=args.approved_by, decision_note=args.decision_note, force=args.force)
    else:
        if not args.draft:
            parser.error("--draft is required unless --from-candidate is set")
        lock_requirement_set(args.ip, Path(args.root), draft=Path(args.draft), approved_by=args.approved_by, decision_note=args.decision_note, force=args.force)
    print(f"[lock_requirement_set] wrote {args.ip}/req/locked_truth.md")
    print(f"[lock_requirement_set] manifest {args.ip}/req/approval_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
