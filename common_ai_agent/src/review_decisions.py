"""Pipeline-level Review Decision Needed records.

These are signoff blockers that the orchestrator writes when automation
cannot safely decide whether a repeated mismatch is caused by missing
SSOT semantics, wrong owner classification, a false evidence gate, or
insufficient workflow capability.

File contract documented in `doc/wiki/orchestrator-worker-handoff.md`:

    <ip>/review/decision_needed_pipeline_repeated_<owner>_mismatch.json

When a `signature` is supplied (the mismatch signature that repeated),
the filename is extended to keep separate files per signature:

    <ip>/review/decision_needed_pipeline_repeated_<owner>_<signature>_mismatch.json

This is distinct from `<ip>/handoff/review/*.json`, which is the
per-handoff escalation lane managed by `src/handoff_queue.py`.
"""
from __future__ import annotations

import json
import os
import re
import threading
import time
import uuid
from pathlib import Path
from typing import Any

SCHEMA = "pipeline_decision_needed.v1"

DECISION_OPTIONS = (
    "missing_ssot_semantics",
    "wrong_owner_classification",
    "false_evidence_gate",
    "insufficient_workflow_capability",
)


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _slug(value: str) -> str:
    """Filename-safe slug. Matches `headless_workflow._safe_name()` so the
    legacy review-decision filename layout (`rtl-gen` → `rtl_gen`) is
    preserved across the two writers."""
    cleaned = re.sub(r"[^A-Za-z0-9_]+", "_", str(value or "")).strip("_")
    return cleaned or "x"


def decision_filename(owner: str, signature: str = "") -> str:
    """Return the doc-contract filename for the given owner/signature."""
    owner_slug = _slug(owner)
    if signature:
        return f"decision_needed_pipeline_repeated_{owner_slug}_{_slug(signature)}_mismatch.json"
    return f"decision_needed_pipeline_repeated_{owner_slug}_mismatch.json"


def decision_path(ip_dir: Path, owner: str, signature: str = "") -> Path:
    return ip_dir / "review" / decision_filename(owner, signature)


def write_repeated_mismatch_decision(
    ip_dir: Path,
    *,
    ip: str,
    owner: str,
    signature: str = "",
    retry_attempts: int = 0,
    evidence: dict[str, Any] | None = None,
    next_actions: list[str] | None = None,
    reason: str = "",
) -> Path:
    """Write or refresh the Review Decision Needed record for this owner.

    Re-running with the same `(owner, signature)` updates `retry_attempts`,
    `last_seen_at`, and the evidence pointers rather than creating a new file
    — the record is the live escalation state, not a historical log.
    """
    target = decision_path(ip_dir, owner, signature)
    target.parent.mkdir(parents=True, exist_ok=True)

    existing: dict[str, Any] = {}
    if target.exists():
        try:
            existing = json.loads(target.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            existing = {}

    resolved_at = existing.get("resolved_at")
    evidence_block = dict(evidence) if evidence else {}
    evidence_block.setdefault("owner", owner)
    if signature and "signature" not in evidence_block:
        evidence_block["signature"] = signature
    record: dict[str, Any] = {
        "schema": SCHEMA,
        "type": "review_decision_needed",  # legacy compat field, matches old writer
        "status": "resolved" if resolved_at else "review_decision_needed",
        "ip": ip,
        "owner": owner,
        "signature": signature,
        "retry_attempts": retry_attempts,
        "reason": reason,
        "options": list(DECISION_OPTIONS),
        "next_actions": list(next_actions) if next_actions else [],
        "evidence": evidence_block,
        "created_at": existing.get("created_at") or _now_iso(),
        "last_seen_at": _now_iso(),
        "resolved_at": resolved_at,
        "resolution": existing.get("resolution"),
    }

    _atomic_write_json(target, record)
    return target


def _atomic_write_json(target: Path, record: dict) -> None:
    """Per-thread unique tmp filename so two concurrent rewrites of the same
    review-decision file don't race on the rename. See handoff_queue for the
    same fix; both modules share the failure mode."""
    tmp_suffix = f".tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}"
    tmp = target.with_suffix(target.suffix + tmp_suffix)
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, target)


def resolve_decision(
    ip_dir: Path,
    *,
    owner: str,
    signature: str = "",
    resolution: str,
) -> Path:
    """Mark a Review Decision Needed record as resolved.

    `resolution` should be one of the documented option strings (e.g.
    `"missing_ssot_semantics"`) or a free-form reviewer note. Resolved
    records remain on disk as audit trail.
    """
    target = decision_path(ip_dir, owner, signature)
    if not target.exists():
        raise FileNotFoundError(f"no decision record at {target}")
    record = json.loads(target.read_text(encoding="utf-8"))
    record["resolved_at"] = _now_iso()
    record["resolution"] = resolution
    record["status"] = "resolved"
    _atomic_write_json(target, record)
    return target


def list_open_decisions(ip_dir: Path) -> list[dict[str, Any]]:
    """All unresolved decision records under `<ip>/review/`."""
    review_dir = ip_dir / "review"
    if not review_dir.is_dir():
        return []
    records: list[dict[str, Any]] = []
    for path in review_dir.glob("decision_needed_pipeline_repeated_*.json"):
        try:
            record = json.loads(path.read_text(encoding="utf-8"))
        except (json.JSONDecodeError, OSError):
            continue
        if record.get("resolved_at"):
            continue
        records.append(record)
    records.sort(key=lambda r: r.get("created_at", ""))
    return records


def count_open_decisions(ip_dir: Path) -> int:
    return len(list_open_decisions(ip_dir))
