"""Handoff queue — durable cross-workflow handoff records.

Implements the on-disk side of the orchestrator/worker handoff design
documented in `doc/wiki/orchestrator-worker-handoff.md`. The queue lives
under `<ip>/handoff/{suggested,pending,claimed,done,review}/<handoff_id>.json`
and the state machine is:

    nothing  -> suggested        (worker proposes a handoff)
    suggested -> pending         (orchestrator promotes)
    pending  -> claimed          (worker claims via /take or live dispatch)
    claimed  -> done             (worker reports success)
    claimed  -> pending          (claim released or lease expired)
    pending  -> review           (orchestrator escalates)
    claimed  -> review           (orchestrator escalates)

Schema: `workflow_handoff.v1`. Every record requires a `scope` object with
`user_id`, `session_id`, and `pipeline_run_id` so multi-user routing can
attribute the handoff to the right orchestrator run context. `workspace_id`
is optional today but accepted for forward compatibility.

Atomicity contract: `claim()` and `claim_next()` use `os.replace()` to win
the pending → claimed transition in a single syscall. Two workers racing on
the same `handoff_id` are guaranteed to produce exactly one winner (the
other raises `FileNotFoundError`). Promotion to `pending` and escalation
to `review` use the same atomic rename.

Leases: every claim records `lease_expires_at`. `release_expired_leases()`
returns abandoned claims to the pending queue so another `/take` can pick
them up.
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

SCHEMA = "workflow_handoff.v1"

_STATE_DIRS = ("suggested", "pending", "claimed", "done", "review")

_VALID_HANDOFF_ID = re.compile(r"^[A-Za-z0-9][A-Za-z0-9_\-]*$")
_MAX_HANDOFF_ID_LEN = 200  # leaves headroom under the 255-byte filename limit
                           # after `<id>.json.tmp` and stat-cache prefixes

_REQUIRED_SCOPE_KEYS = ("user_id", "session_id", "pipeline_run_id")
_OPTIONAL_SCOPE_KEYS = ("workspace_id", "lease_id")

DEFAULT_LEASE_TTL_SECONDS = 600  # 10 minutes


def _now_iso() -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime())


def _iso_offset(seconds: int) -> str:
    return time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime(time.time() + max(seconds, 0)))


def _slug(value: str) -> str:
    """Filename-safe slug. Keeps ASCII letters, digits, `_`, `-`."""
    cleaned = re.sub(r"[^A-Za-z0-9_\-]+", "-", value.strip())
    return cleaned.strip("-_") or "x"


def make_handoff_id(
    ip: str,
    from_workflow: str,
    to_workflow: str,
    suffix: str = "",
) -> str:
    """`<ip>__<from>__<to>[__<suffix>]` — matches the doc example."""
    parts = [_slug(ip), _slug(from_workflow), _slug(to_workflow)]
    if suffix:
        parts.append(_slug(suffix))
    return "__".join(parts)


def _ensure_dirs(ip_dir: Path) -> Path:
    root = ip_dir / "handoff"
    for d in _STATE_DIRS:
        (root / d).mkdir(parents=True, exist_ok=True)
    return root


def _path(ip_dir: Path, state: str, handoff_id: str) -> Path:
    if state not in _STATE_DIRS:
        raise ValueError(f"unknown handoff state: {state!r}")
    if not _VALID_HANDOFF_ID.match(handoff_id):
        raise ValueError(f"invalid handoff_id: {handoff_id!r}")
    if len(handoff_id) > _MAX_HANDOFF_ID_LEN:
        raise ValueError(
            f"handoff_id exceeds {_MAX_HANDOFF_ID_LEN}-char filename limit: "
            f"{len(handoff_id)} chars"
        )
    return ip_dir / "handoff" / state / f"{handoff_id}.json"


def _validate_scope(scope: Any) -> None:
    if not isinstance(scope, dict):
        raise ValueError("handoff scope must be a dict with user_id/session_id/pipeline_run_id")
    missing = [k for k in _REQUIRED_SCOPE_KEYS if not scope.get(k)]
    if missing:
        raise ValueError(f"handoff scope missing required keys: {missing}")
    for key in _REQUIRED_SCOPE_KEYS + _OPTIONAL_SCOPE_KEYS:
        if key in scope and not isinstance(scope[key], str):
            raise ValueError(f"scope.{key} must be a string, got {type(scope[key]).__name__}")


def _validate(record: dict) -> None:
    required = ("schema", "handoff_id", "ip", "from_workflow", "to_workflow", "scope")
    missing = [k for k in required if record.get(k) in (None, "", {})]
    if missing:
        raise ValueError(f"handoff record missing required fields: {missing}")
    if record["schema"] != SCHEMA:
        raise ValueError(
            f"handoff schema mismatch: got {record['schema']!r}, expected {SCHEMA!r}"
        )
    if not _VALID_HANDOFF_ID.match(record["handoff_id"]):
        raise ValueError(f"invalid handoff_id format: {record['handoff_id']!r}")
    _validate_scope(record["scope"])


def make_scope(
    *,
    user_id: str,
    session_id: str,
    pipeline_run_id: str,
    workspace_id: str = "",
    lease_id: str = "",
) -> dict:
    """Convenience builder for the required scope object."""
    scope = {
        "user_id": user_id,
        "session_id": session_id,
        "pipeline_run_id": pipeline_run_id,
    }
    if workspace_id:
        scope["workspace_id"] = workspace_id
    if lease_id:
        scope["lease_id"] = lease_id
    return scope


def _write_json(path: Path, record: dict) -> None:
    """Atomic write: stage to a unique tmp file, then `os.replace`. The tmp
    name includes pid + thread id + a random hex so two callers writing the
    same `path` concurrently don't race on the rename (the loser would have
    written its content to a non-existent tmp after the winner already
    moved it). On macOS we observed `[Errno 2] No such file or directory`
    from the loser before this fix."""
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp_suffix = f".tmp.{os.getpid()}.{threading.get_ident()}.{uuid.uuid4().hex[:8]}"
    tmp = path.with_suffix(path.suffix + tmp_suffix)
    tmp.write_text(json.dumps(record, indent=2, sort_keys=True), encoding="utf-8")
    os.replace(tmp, path)


def _read_json(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def write_suggested(ip_dir: Path, record: dict) -> Path:
    """Worker-side: drop a proposal. Orchestrator decides later."""
    record = dict(record)
    record.setdefault("schema", SCHEMA)
    record.setdefault("created_at", _now_iso())
    _validate(record)
    _ensure_dirs(ip_dir)
    target = _path(ip_dir, "suggested", record["handoff_id"])
    _write_json(target, record)
    return target


def write_pending(ip_dir: Path, record: dict) -> Path:
    """Orchestrator-side: enqueue a pending handoff directly."""
    record = dict(record)
    record.setdefault("schema", SCHEMA)
    record.setdefault("created_at", _now_iso())
    _validate(record)
    _ensure_dirs(ip_dir)
    target = _path(ip_dir, "pending", record["handoff_id"])
    _write_json(target, record)
    return target


def _atomic_rename(
    ip_dir: Path,
    handoff_id: str,
    src_state: str,
    dst_state: str,
) -> Path | None:
    """Single-syscall move. Returns dst path on win, None when src is gone."""
    src = _path(ip_dir, src_state, handoff_id)
    dst = _path(ip_dir, dst_state, handoff_id)
    dst.parent.mkdir(parents=True, exist_ok=True)
    try:
        os.replace(src, dst)
    except FileNotFoundError:
        return None
    return dst


def _mutate_in_place(path: Path, mutate: dict) -> dict:
    record = _read_json(path)
    record.update(mutate)
    _write_json(path, record)
    return record


def promote_to_pending(ip_dir: Path, handoff_id: str) -> Path:
    """Atomically move a `suggested` proposal into the live `pending` queue."""
    dst = _atomic_rename(ip_dir, handoff_id, "suggested", "pending")
    if dst is None:
        raise FileNotFoundError(f"handoff not in suggested: {handoff_id}")
    _mutate_in_place(dst, {"promoted_at": _now_iso()})
    return dst


def claim(
    ip_dir: Path,
    handoff_id: str,
    *,
    claimant: str,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
) -> Path:
    """Atomic lease: rename pending → claimed in one syscall, then attach
    claim metadata to the now-uniquely-owned file. Raises if a competing
    claimer won the rename first."""
    dst = _atomic_rename(ip_dir, handoff_id, "pending", "claimed")
    if dst is None:
        raise FileNotFoundError(
            f"handoff not in pending (already claimed or never existed): {handoff_id}"
        )
    _mutate_in_place(dst, {
        "claimed_at": _now_iso(),
        "claimed_by": claimant,
        "lease_expires_at": _iso_offset(lease_ttl_seconds),
    })
    return dst


def claim_next(
    ip_dir: Path,
    workflow: str,
    *,
    claimant: str,
    lease_ttl_seconds: int = DEFAULT_LEASE_TTL_SECONDS,
    scope_filter: dict | None = None,
) -> dict | None:
    """Race-safe FIFO claim. Walks pending oldest-first; for each candidate
    attempts an atomic rename and returns the record of whichever rename
    wins. Two workers calling `claim_next` simultaneously will each get a
    different record (or one will get None if nothing is left).

    `scope_filter` restricts the candidate set to records whose `scope`
    matches every key/value in the filter — used so user_a's `/take`
    cannot claim user_b's handoff."""
    for candidate in list_pending_for_workflow(ip_dir, workflow, scope_filter=scope_filter):
        hid = candidate["handoff_id"]
        dst = _atomic_rename(ip_dir, hid, "pending", "claimed")
        if dst is None:
            continue  # another worker won this one; try the next
        record = _mutate_in_place(dst, {
            "claimed_at": _now_iso(),
            "claimed_by": claimant,
            "lease_expires_at": _iso_offset(lease_ttl_seconds),
        })
        return record
    return None


def release_claim(ip_dir: Path, handoff_id: str) -> Path:
    """Return an expired/dead claim to the pending queue."""
    dst = _atomic_rename(ip_dir, handoff_id, "claimed", "pending")
    if dst is None:
        raise FileNotFoundError(f"handoff not in claimed: {handoff_id}")
    _mutate_in_place(dst, {"released_at": _now_iso()})
    return dst


def release_expired_leases(ip_dir: Path) -> int:
    """Move every claimed handoff whose `lease_expires_at` is in the past
    back to `pending`. Returns the count moved."""
    now = _now_iso()
    moved = 0
    for record in list_state(ip_dir, "claimed"):
        expires = record.get("lease_expires_at") or ""
        if expires and expires < now:
            try:
                release_claim(ip_dir, record["handoff_id"])
                moved += 1
            except FileNotFoundError:
                # someone else released or completed it; that's fine
                continue
    return moved


def complete(ip_dir: Path, handoff_id: str, *, result: dict | None = None) -> Path:
    """Worker reports the claimed handoff finished successfully."""
    dst = _atomic_rename(ip_dir, handoff_id, "claimed", "done")
    if dst is None:
        raise FileNotFoundError(f"handoff not in claimed: {handoff_id}")
    mutate = {"completed_at": _now_iso()}
    if result is not None:
        mutate["result"] = result
    _mutate_in_place(dst, mutate)
    return dst


def move_to_review(ip_dir: Path, handoff_id: str, *, reason: str = "") -> Path:
    """Escalate a pending or claimed handoff to Review Decision Needed."""
    for src in ("pending", "claimed"):
        dst = _atomic_rename(ip_dir, handoff_id, src, "review")
        if dst is not None:
            _mutate_in_place(dst, {
                "escalated_at": _now_iso(),
                "escalation_reason": reason or "",
            })
            return dst
    raise FileNotFoundError(f"handoff not in pending or claimed: {handoff_id}")


def list_state(ip_dir: Path, state: str) -> list[dict]:
    """List records in a single state directory, newest first."""
    if state not in _STATE_DIRS:
        raise ValueError(f"unknown handoff state: {state!r}")
    state_dir = ip_dir / "handoff" / state
    if not state_dir.is_dir():
        return []
    rows = []
    for p in state_dir.glob("*.json"):
        try:
            rows.append(_read_json(p))
        except (json.JSONDecodeError, OSError):
            continue
    rows.sort(key=lambda r: r.get("created_at", ""), reverse=True)
    return rows


def list_pending_for_workflow(
    ip_dir: Path,
    workflow: str,
    *,
    scope_filter: dict | None = None,
) -> list[dict]:
    """Pending handoffs whose `to_workflow` matches; oldest first (FIFO).

    When `scope_filter` is given, only return records whose `scope` matches
    every key/value in the filter — used so one user's `/take` cannot claim
    another user's handoff.
    """
    rows = [r for r in list_state(ip_dir, "pending") if r.get("to_workflow") == workflow]
    if scope_filter:
        rows = [r for r in rows if _scope_matches(r.get("scope") or {}, scope_filter)]
    rows.sort(key=lambda r: r.get("created_at", ""))
    return rows


def _scope_matches(record_scope: dict, filter_scope: dict) -> bool:
    for k, v in filter_scope.items():
        if not v:
            continue
        if record_scope.get(k) != v:
            return False
    return True


def get(ip_dir: Path, handoff_id: str) -> tuple[str, dict] | None:
    """Find a handoff across all state dirs. Returns (state, record) or None."""
    for state in _STATE_DIRS:
        path = _path(ip_dir, state, handoff_id)
        if path.exists():
            return state, _read_json(path)
    return None


def summary_by_workflow(
    ip_dir: Path,
    *,
    scope_filter: dict | None = None,
) -> dict[str, dict[str, Any]]:
    """Aggregate counts per workflow per state, plus newest-pending preview.

    Shape matches `handoffs_by_workflow` from the UI contract in
    `doc/wiki/orchestrator-worker-handoff.md`. When `scope_filter` is given,
    only counts records whose scope matches every filter key.
    """
    summary: dict[str, dict[str, Any]] = {}
    for state in _STATE_DIRS:
        if state == "suggested":
            continue
        for record in list_state(ip_dir, state):
            if scope_filter and not _scope_matches(record.get("scope") or {}, scope_filter):
                continue
            wf = record.get("to_workflow") or "unknown"
            slot = summary.setdefault(wf, {"pending": 0, "claimed": 0, "done": 0, "review": 0, "latest": None})
            if state in slot:
                slot[state] += 1
            if state == "pending" and slot["latest"] is None:
                slot["latest"] = {
                    "handoff_id": record.get("handoff_id"),
                    "from_workflow": record.get("from_workflow"),
                    "reason": record.get("reason"),
                    "goal_ids": record.get("goal_ids", []),
                }
    return summary


def queue_totals(
    ip_dir: Path,
    *,
    scope_filter: dict | None = None,
) -> dict[str, int]:
    """Cross-workflow totals for the top-level `orchestrator` block."""
    def _count(state: str) -> int:
        if not scope_filter:
            return len(list_state(ip_dir, state))
        return sum(
            1 for r in list_state(ip_dir, state)
            if _scope_matches(r.get("scope") or {}, scope_filter)
        )
    return {
        "pending_handoffs": _count("pending"),
        "claimed_handoffs": _count("claimed"),
        "review_decisions": _count("review"),
    }
