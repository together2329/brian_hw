#!/usr/bin/env python3
"""Promote a reviewed requirement packet into the locked req/ authority.

This script intentionally requires an explicit approver. It is a small guard
against turning a draft/review packet into signoff evidence merely because a
file exists under req/.
"""

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
from typing import Any


def _sha256(path: Path) -> str:
    return hashlib.sha256(path.read_bytes()).hexdigest()


def _rel(path: Path, root: Path) -> str:
    try:
        return str(path.relative_to(root))
    except ValueError:
        return str(path)


def _default_source(root: Path, ip: str) -> Path:
    return root / ip / "doc" / f"{ip}_requirement_review.md"


def _target_paths(root: Path, ip: str) -> tuple[Path, Path]:
    req_dir = root / ip / "req"
    return req_dir / f"{ip}_requirements.md", req_dir / "approval_manifest.json"


def _review_decision_path(root: Path, ip: str) -> Path:
    return root / ip / "review" / "decision_needed_req_requirement_approval.json"


def _atomic_write_text(path: Path, text: str) -> None:
    tmp_suffix = f".tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}"
    tmp = path.with_suffix(path.suffix + tmp_suffix)
    tmp.write_text(text, encoding="utf-8")
    tmp.replace(path)


def _atomic_write_json(path: Path, doc: dict[str, Any]) -> None:
    _atomic_write_text(path, json.dumps(doc, indent=2, sort_keys=True) + "\n")


def _load_review_decision(root: Path, ip: str) -> tuple[Path, dict[str, Any] | None]:
    path = _review_decision_path(root, ip)
    if not path.is_file():
        return path, None
    try:
        record = json.loads(path.read_text(encoding="utf-8"))
    except (json.JSONDecodeError, OSError) as exc:
        raise SystemExit(f"cannot parse review decision {path}: {exc}") from exc
    if not isinstance(record, dict):
        raise SystemExit(f"review decision must be a JSON object: {path}")
    return path, record


def _placeholder_approver(value: str) -> bool:
    normalized = re.sub(r"[^a-z0-9]+", "", value.strip().lower())
    return normalized in {"dryrun", "test", "placeholder", "unknown", "none", "na"}


def _validate_approval_target(
    record: dict[str, Any] | None,
    *,
    root: Path,
    source_path: Path,
    source_hash: str,
) -> None:
    """Reject stale review approvals when the decision pins a source hash.

    Older review-decision records did not include an approval target. Keep
    those compatible. Newer records may pin the exact packet path and sha256 so
    a human approval cannot be accidentally applied to a modified review file.
    """
    if not record:
        return
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return
    target = evidence.get("approval_target")
    if not isinstance(target, dict):
        return

    expected_path = str(target.get("path") or "").strip()
    actual_path = _rel(source_path, root)
    if expected_path and expected_path != actual_path:
        raise SystemExit(
            "review decision approval_target path does not match source: "
            f"expected {expected_path}, got {actual_path}"
        )

    expected_hash = str(target.get("sha256") or "").strip().lower()
    if expected_hash and expected_hash != source_hash.lower():
        raise SystemExit(
            "review decision approval_target sha256 does not match source: "
            f"expected {expected_hash}, got {source_hash}"
        )


def _validate_machine_evidence_snapshot(
    record: dict[str, Any] | None,
    *,
    root: Path,
    ip: str,
) -> None:
    """Reject approval against stale machine-evidence snapshots when pinned."""
    if not record:
        return
    evidence = record.get("evidence")
    if not isinstance(evidence, dict):
        return
    snapshot = evidence.get("machine_evidence_snapshot")
    if not isinstance(snapshot, dict):
        return

    known_paths = {
        "completion_audit_sha256": root / ip / "doc" / f"{ip}_completion_audit.md",
        "ssot_sha256": root / ip / "yaml" / f"{ip}.ssot.yaml",
        "fl_rtl_compare_sha256": root / ip / "sim" / "fl_rtl_compare.json",
        "coverage_sha256": root / ip / "cov" / "coverage.json",
    }
    for key, path in known_paths.items():
        expected_hash = str(snapshot.get(key) or "").strip().lower()
        if not expected_hash:
            continue
        if not path.is_file():
            raise SystemExit(
                f"review decision machine_evidence_snapshot {key} points to missing file: "
                f"{_rel(path, root)}"
            )
        actual_hash = _sha256(path)
        if expected_hash != actual_hash.lower():
            raise SystemExit(
                f"review decision machine_evidence_snapshot {key} does not match: "
                f"expected {expected_hash}, got {actual_hash}"
            )


def _approved_body(source_text: str) -> str:
    """Return source review text suitable for an approved requirement artifact.

    The review packet is deliberately marked pending while it lives under
    `doc/`. Once promoted, the approval header and manifest carry authority, so
    stale "pending user review" status lines would make the approved artifact
    internally contradictory.
    """
    kept: list[str] = []
    skip_continuation = False
    for raw_line in source_text.splitlines():
        line = raw_line.strip()
        lowered = line.lower()
        if skip_continuation:
            if not line:
                skip_continuation = False
            continue
        if lowered.startswith("approval status: pending user review"):
            skip_continuation = True
            continue
        if "not a human-approved requirement artifact" in lowered:
            continue
        if "pending review" in lowered and "approval" in lowered:
            continue
        kept.append(raw_line)
    return "\n".join(kept).strip()


def _resolve_review_decision(root: Path, ip: str, *, approved_by: str, approved_at: str) -> str:
    path, record = _load_review_decision(root, ip)
    if record is None:
        return ""

    record["status"] = "resolved"
    record["resolved_at"] = approved_at
    record["resolution"] = {
        "decision": "approved",
        "approved_by": approved_by,
        "approved_at_utc": approved_at,
        "promoted_to": f"{ip}/req/{ip}_requirements.md",
    }
    _atomic_write_json(path, record)
    return _rel(path, root)


def promote(
    ip: str,
    root: Path,
    *,
    source: Path | None = None,
    approved_by: str,
    decision_note: str = "",
    force: bool = False,
    dry_run: bool = False,
) -> dict[str, Any]:
    root = root.resolve()
    if source is None:
        source_path = _default_source(root, ip).resolve()
    elif source.is_absolute():
        source_path = source.resolve()
    else:
        source_path = (root / source).resolve()
    approver = approved_by.strip()
    if not approver:
        raise SystemExit("--approved-by is required; requirement promotion is human-owned")
    if not dry_run and _placeholder_approver(approver):
        raise SystemExit("--approved-by must name the real human approver for non-dry-run promotion")
    if not source_path.is_file():
        raise SystemExit(f"missing review packet: {source_path}")
    _, review_decision = _load_review_decision(root, ip)

    target_path, manifest_path = _target_paths(root, ip)
    if target_path.exists() and not force:
        raise SystemExit(f"{_rel(target_path, root)} already exists; pass --force to replace")

    source_text = source_path.read_text(encoding="utf-8", errors="replace").strip()
    if len(source_text) < 1000:
        raise SystemExit(f"review packet is too small to be signoff evidence: {source_path}")
    approved_body = _approved_body(source_text)
    if len(approved_body) < 1000:
        raise SystemExit(f"approved requirement body is too small after removing review-only status text: {source_path}")

    approved_at = time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())
    source_hash = _sha256(source_path)
    _validate_approval_target(
        review_decision,
        root=root,
        source_path=source_path,
        source_hash=source_hash,
    )
    _validate_machine_evidence_snapshot(
        review_decision,
        root=root,
        ip=ip,
    )
    header = "\n".join(
        [
            f"# {ip} Human-Approved Requirements",
            "",
            "Approval status: approved",
            f"Approved by: {approver}",
            f"Approved at UTC: {approved_at}",
            f"Source review packet: `{_rel(source_path, root)}`",
            f"Source SHA256: `{source_hash}`",
            "",
        ]
    )
    if decision_note.strip():
        header += f"Approval note: {decision_note.strip()}\n\n"

    target_text = header + approved_body + "\n"
    target_hash = hashlib.sha256(target_text.encode("utf-8")).hexdigest()
    manifest = {
        "schema_version": 1,
        "type": "requirement_approval_manifest",
        "ip": ip,
        "approved_by": approver,
        "approved_at_utc": approved_at,
        "decision_note": decision_note.strip(),
        "source": _rel(source_path, root),
        "source_sha256": source_hash,
        "target": _rel(target_path, root),
        "target_sha256": target_hash,
    }
    if dry_run:
        manifest["dry_run"] = True
        manifest["target_sha256_preview"] = target_hash
        manifest["note"] = (
            "dry-run target_sha256 is a preview for the printed approved_at_utc, "
            "approved_by, and decision_note; real approval may produce a different "
            "target_sha256"
        )
        if review_decision is not None:
            manifest["would_resolve_review_decision"] = _rel(_review_decision_path(root, ip), root)
        return manifest

    req_dir = target_path.parent
    req_dir.mkdir(parents=True, exist_ok=True)
    _atomic_write_text(target_path, target_text)

    _atomic_write_json(manifest_path, manifest)
    resolved_review_decision = _resolve_review_decision(
        root,
        ip,
        approved_by=approver,
        approved_at=approved_at,
    )
    if resolved_review_decision:
        manifest["resolved_review_decision"] = resolved_review_decision
        _atomic_write_json(manifest_path, manifest)
    return manifest


def main() -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("ip")
    parser.add_argument("--root", default=".")
    parser.add_argument("--source", default="")
    parser.add_argument("--approved-by", default="")
    parser.add_argument("--decision-note", default="")
    parser.add_argument("--force", action="store_true")
    parser.add_argument("--dry-run", action="store_true", help="validate promotion inputs without writing req/ artifacts")
    parser.add_argument("--json", dest="json_output", action="store_true", help="print the promotion manifest as JSON")
    args = parser.parse_args()

    manifest = promote(
        args.ip,
        Path(args.root),
        source=Path(args.source) if args.source else None,
        approved_by=args.approved_by,
        decision_note=args.decision_note,
        force=args.force,
        dry_run=args.dry_run,
    )
    if args.json_output:
        print(json.dumps(manifest, indent=2, sort_keys=True))
        return 0
    if args.dry_run:
        print(f"[promote_requirement_review] dry-run ok; would write {manifest['target']}")
        print(f"[promote_requirement_review] dry-run approved_at_utc={manifest['approved_at_utc']}")
        print(f"[promote_requirement_review] dry-run source_sha256={manifest['source_sha256']}")
        print(f"[promote_requirement_review] dry-run target_sha256={manifest['target_sha256']}")
        if manifest.get("would_resolve_review_decision"):
            print(f"[promote_requirement_review] dry-run ok; would resolve {manifest['would_resolve_review_decision']}")
        return 0
    print(f"[promote_requirement_review] wrote {manifest['target']}")
    print(f"[promote_requirement_review] manifest {args.ip}/req/approval_manifest.json")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
