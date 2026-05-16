from __future__ import annotations

import json
import sys
import threading
import time
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from src import handoff_queue as hq


def _scope(**overrides) -> dict:
    base = hq.make_scope(
        user_id="user_a",
        session_id="S1",
        pipeline_run_id="P1",
        workspace_id="workspace_1",
    )
    base.update(overrides)
    return base


def _make_record(
    ip: str = "simple_gpio_lite",
    from_workflow: str = "sim-debug",
    to_workflow: str = "rtl-gen",
    suffix: str = "EQ_READBACK",
    scope: dict | None = None,
    **extra,
) -> dict:
    rec = {
        "schema": hq.SCHEMA,
        "handoff_id": hq.make_handoff_id(ip, from_workflow, to_workflow, suffix),
        "ip": ip,
        "from_workflow": from_workflow,
        "to_workflow": to_workflow,
        "scope": scope if scope is not None else _scope(),
        "reason": "FL-vs-RTL mismatch",
    }
    rec.update(extra)
    return rec


# ── basics ────────────────────────────────────────────────────────────


def test_make_handoff_id_format() -> None:
    hid = hq.make_handoff_id("simple_gpio_lite", "sim-debug", "rtl-gen", "EQ_READBACK")
    assert hid == "simple_gpio_lite__sim-debug__rtl-gen__EQ_READBACK"
    assert hq.make_handoff_id("ip", "a", "b") == "ip__a__b"


def test_make_scope_required_keys() -> None:
    s = hq.make_scope(user_id="u", session_id="s", pipeline_run_id="p")
    assert s == {"user_id": "u", "session_id": "s", "pipeline_run_id": "p"}
    s2 = hq.make_scope(user_id="u", session_id="s", pipeline_run_id="p", workspace_id="w", lease_id="l")
    assert s2["workspace_id"] == "w"
    assert s2["lease_id"] == "l"


def test_write_pending_and_get(tmp_path: Path) -> None:
    ip_dir = tmp_path / "simple_gpio_lite"
    ip_dir.mkdir()
    rec = _make_record()
    path = hq.write_pending(ip_dir, rec)
    assert path.exists()
    assert path.parent.name == "pending"

    found = hq.get(ip_dir, rec["handoff_id"])
    assert found is not None
    state, loaded = found
    assert state == "pending"
    assert loaded["handoff_id"] == rec["handoff_id"]
    assert loaded["created_at"]
    assert loaded["scope"]["user_id"] == "user_a"


# ── validation ────────────────────────────────────────────────────────


def test_validate_rejects_missing_fields(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    with pytest.raises(ValueError, match="missing required"):
        hq.write_pending(ip_dir, {"schema": hq.SCHEMA, "handoff_id": "x__a__b"})


def test_validate_rejects_missing_scope(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    del rec["scope"]
    with pytest.raises(ValueError, match="scope|missing required"):
        hq.write_pending(ip_dir, rec)


def test_validate_rejects_scope_missing_required_keys(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record(scope={"user_id": "u"})  # missing session_id, pipeline_run_id
    with pytest.raises(ValueError, match="scope missing required keys"):
        hq.write_pending(ip_dir, rec)


def test_validate_rejects_scope_wrong_type(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record(scope="not-a-dict")  # type: ignore[arg-type]
    with pytest.raises(ValueError, match="scope must be a dict"):
        hq.write_pending(ip_dir, rec)


def test_validate_rejects_bad_handoff_id(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    rec["handoff_id"] = "bad id with spaces"
    with pytest.raises(ValueError, match="invalid handoff_id"):
        hq.write_pending(ip_dir, rec)


def test_validate_rejects_schema_mismatch(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    rec["schema"] = "workflow_handoff.v999"
    with pytest.raises(ValueError, match="schema mismatch"):
        hq.write_pending(ip_dir, rec)


# ── state machine ───────────────────────────────────────────────────────


def test_promote_then_claim_then_complete(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_suggested(ip_dir, rec)
    assert hq.get(ip_dir, rec["handoff_id"])[0] == "suggested"

    hq.promote_to_pending(ip_dir, rec["handoff_id"])
    state, loaded = hq.get(ip_dir, rec["handoff_id"])
    assert state == "pending"
    assert loaded["promoted_at"]

    hq.claim(ip_dir, rec["handoff_id"], claimant="worker-rtl-gen-0")
    state, loaded = hq.get(ip_dir, rec["handoff_id"])
    assert state == "claimed"
    assert loaded["claimed_by"] == "worker-rtl-gen-0"
    assert loaded["claimed_at"]
    assert loaded["lease_expires_at"] > loaded["claimed_at"]

    hq.complete(ip_dir, rec["handoff_id"], result={"rtl_files": ["a.sv"]})
    state, loaded = hq.get(ip_dir, rec["handoff_id"])
    assert state == "done"
    assert loaded["completed_at"]
    assert loaded["result"]["rtl_files"] == ["a.sv"]


def test_release_claim_returns_to_pending(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    hq.claim(ip_dir, rec["handoff_id"], claimant="w")
    hq.release_claim(ip_dir, rec["handoff_id"])
    assert hq.get(ip_dir, rec["handoff_id"])[0] == "pending"


def test_move_to_review_from_pending(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    hq.move_to_review(ip_dir, rec["handoff_id"], reason="retry budget exhausted")
    state, loaded = hq.get(ip_dir, rec["handoff_id"])
    assert state == "review"
    assert loaded["escalation_reason"] == "retry budget exhausted"


def test_move_to_review_from_claimed(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    hq.claim(ip_dir, rec["handoff_id"], claimant="w")
    hq.move_to_review(ip_dir, rec["handoff_id"], reason="worker died mid-task")
    assert hq.get(ip_dir, rec["handoff_id"])[0] == "review"


# ── atomic claim race ──────────────────────────────────────────────────


def test_claim_twice_raises_second_caller(tmp_path: Path) -> None:
    """Sequential double-claim — exercise the FileNotFoundError contract."""
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    hq.claim(ip_dir, rec["handoff_id"], claimant="worker-a")
    with pytest.raises(FileNotFoundError):
        hq.claim(ip_dir, rec["handoff_id"], claimant="worker-b")


def test_concurrent_claim_produces_exactly_one_winner(tmp_path: Path) -> None:
    """Two threads racing on the same handoff_id — only one wins."""
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)

    winners: list[str] = []
    losers: list[str] = []
    barrier = threading.Barrier(2)

    def attempt(name: str) -> None:
        barrier.wait()
        try:
            hq.claim(ip_dir, rec["handoff_id"], claimant=name)
            winners.append(name)
        except FileNotFoundError:
            losers.append(name)

    t1 = threading.Thread(target=attempt, args=("w1",))
    t2 = threading.Thread(target=attempt, args=("w2",))
    t1.start(); t2.start(); t1.join(); t2.join()
    assert len(winners) == 1
    assert len(losers) == 1


def test_claim_next_returns_oldest_atomically(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    older = _make_record(suffix="OLDER")
    older["created_at"] = "2026-05-16T09:00:00Z"
    newer = _make_record(suffix="NEWER")
    newer["created_at"] = "2026-05-16T12:00:00Z"
    hq.write_pending(ip_dir, older)
    hq.write_pending(ip_dir, newer)

    rec = hq.claim_next(ip_dir, "rtl-gen", claimant="w")
    assert rec is not None
    assert rec["handoff_id"] == older["handoff_id"]
    assert rec["lease_expires_at"]
    assert hq.get(ip_dir, older["handoff_id"])[0] == "claimed"
    assert hq.get(ip_dir, newer["handoff_id"])[0] == "pending"


def test_claim_next_returns_none_when_empty(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    assert hq.claim_next(ip_dir, "rtl-gen", claimant="w") is None


def test_claim_next_concurrent_two_workers_pick_different_handoffs(tmp_path: Path) -> None:
    """Two workers calling claim_next simultaneously must end up with
    different handoffs (or one with None if only one was available)."""
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    a = _make_record(suffix="A")
    a["created_at"] = "2026-05-16T10:00:00Z"
    b = _make_record(suffix="B")
    b["created_at"] = "2026-05-16T11:00:00Z"
    hq.write_pending(ip_dir, a)
    hq.write_pending(ip_dir, b)

    claimed: list[dict] = []
    barrier = threading.Barrier(2)

    def take() -> None:
        barrier.wait()
        rec = hq.claim_next(ip_dir, "rtl-gen", claimant="w")
        if rec is not None:
            claimed.append(rec)

    t1 = threading.Thread(target=take); t2 = threading.Thread(target=take)
    t1.start(); t2.start(); t1.join(); t2.join()
    ids = {r["handoff_id"] for r in claimed}
    assert ids == {a["handoff_id"], b["handoff_id"]}


# ── lease expiry ────────────────────────────────────────────────────────


def test_release_expired_leases_returns_old_claims_to_pending(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    # Short-TTL lease, then sleep past expiry. We sleep TTL+1 to clear
    # the ISO-8601 second-resolution boundary deterministically.
    hq.claim(ip_dir, rec["handoff_id"], claimant="w", lease_ttl_seconds=1)
    time.sleep(2.1)
    moved = hq.release_expired_leases(ip_dir)
    assert moved == 1
    assert hq.get(ip_dir, rec["handoff_id"])[0] == "pending"


def test_release_expired_leases_ignores_active_claims(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    hq.write_pending(ip_dir, rec)
    hq.claim(ip_dir, rec["handoff_id"], claimant="w", lease_ttl_seconds=3600)
    moved = hq.release_expired_leases(ip_dir)
    assert moved == 0
    assert hq.get(ip_dir, rec["handoff_id"])[0] == "claimed"


# ── scope filtering ─────────────────────────────────────────────────────


def test_list_pending_for_workflow_filters_by_scope(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    a = _make_record(suffix="A", scope=_scope(user_id="user_a"))
    b = _make_record(suffix="B", scope=_scope(user_id="user_b"))
    hq.write_pending(ip_dir, a)
    hq.write_pending(ip_dir, b)

    rows = hq.list_pending_for_workflow(ip_dir, "rtl-gen", scope_filter={"user_id": "user_a"})
    assert [r["handoff_id"] for r in rows] == [a["handoff_id"]]
    rows = hq.list_pending_for_workflow(ip_dir, "rtl-gen", scope_filter={"user_id": "user_b"})
    assert [r["handoff_id"] for r in rows] == [b["handoff_id"]]
    # No filter → both
    assert len(hq.list_pending_for_workflow(ip_dir, "rtl-gen")) == 2


def test_summary_and_totals_respect_scope_filter(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    a = _make_record(suffix="A", scope=_scope(user_id="user_a"))
    b = _make_record(suffix="B", scope=_scope(user_id="user_b"))
    hq.write_pending(ip_dir, a)
    hq.write_pending(ip_dir, b)

    totals_a = hq.queue_totals(ip_dir, scope_filter={"user_id": "user_a"})
    assert totals_a["pending_handoffs"] == 1
    totals_all = hq.queue_totals(ip_dir)
    assert totals_all["pending_handoffs"] == 2

    summary_a = hq.summary_by_workflow(ip_dir, scope_filter={"user_id": "user_a"})
    assert summary_a["rtl-gen"]["pending"] == 1


# ── misc ────────────────────────────────────────────────────────────────


def test_list_pending_is_fifo(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    a = _make_record(suffix="A")
    a["created_at"] = "2026-05-16T10:00:00Z"
    b = _make_record(suffix="B")
    b["created_at"] = "2026-05-16T11:00:00Z"
    c = _make_record(suffix="C", to_workflow="tb-gen")
    c["created_at"] = "2026-05-16T10:30:00Z"
    for r in (a, b, c):
        hq.write_pending(ip_dir, r)

    rtl = hq.list_pending_for_workflow(ip_dir, "rtl-gen")
    assert [r["handoff_id"] for r in rtl] == [a["handoff_id"], b["handoff_id"]]


def test_summary_by_workflow_and_totals(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    a = _make_record(suffix="A")
    a["created_at"] = "2026-05-16T10:00:00Z"
    b = _make_record(suffix="B")
    b["created_at"] = "2026-05-16T11:00:00Z"
    hq.write_pending(ip_dir, a)
    hq.write_pending(ip_dir, b)
    hq.claim(ip_dir, b["handoff_id"], claimant="w")

    c = _make_record(suffix="C", to_workflow="tb-gen")
    hq.write_pending(ip_dir, c)
    claimed = hq.claim(ip_dir, c["handoff_id"], claimant="w")
    hq.complete(ip_dir, claimed.stem, result={"ok": True})

    summary = hq.summary_by_workflow(ip_dir)
    assert summary["rtl-gen"]["pending"] == 1
    assert summary["rtl-gen"]["claimed"] == 1
    assert summary["rtl-gen"]["latest"]["handoff_id"] == a["handoff_id"]
    assert summary["tb-gen"]["done"] == 1

    totals = hq.queue_totals(ip_dir)
    assert totals["pending_handoffs"] == 1
    assert totals["claimed_handoffs"] == 1
    assert totals["review_decisions"] == 0


def test_get_returns_none_when_missing(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    assert hq.get(ip_dir, "no__such__handoff") is None


def test_atomic_write_round_trip(tmp_path: Path) -> None:
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    path = hq.write_pending(ip_dir, rec)
    assert path.exists()
    leftovers = list(path.parent.glob("*.tmp"))
    assert leftovers == []
    json.loads(path.read_text(encoding="utf-8"))


def test_validate_rejects_overlong_handoff_id(tmp_path: Path) -> None:
    """Reject handoff_ids that would exceed the per-filename byte limit on
    typical filesystems (255 bytes). Surfaced by T18 of deep-deep-deep test."""
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    rec = _make_record()
    rec["handoff_id"] = "a" + "x" * 250  # 251 chars
    with pytest.raises(ValueError, match="exceeds"):
        hq.write_pending(ip_dir, rec)


def test_claim_next_respects_scope_filter(tmp_path: Path) -> None:
    """claim_next must not steal another user's older handoff. Surfaced
    by T20 of deep-deep-deep test."""
    ip_dir = tmp_path / "ip"
    ip_dir.mkdir()
    older_b = _make_record(suffix="B_OLD", scope=_scope(user_id="user_b"))
    older_b["created_at"] = "2026-05-16T08:00:00Z"
    newer_a = _make_record(suffix="A_NEW", scope=_scope(user_id="user_a"))
    newer_a["created_at"] = "2026-05-16T12:00:00Z"
    hq.write_pending(ip_dir, older_b)
    hq.write_pending(ip_dir, newer_a)

    # user_a's worker uses scope_filter; must skip user_b's older record
    record = hq.claim_next(
        ip_dir, "rtl-gen",
        claimant="user_a-worker",
        scope_filter={"user_id": "user_a"},
    )
    assert record is not None
    assert record["scope"]["user_id"] == "user_a"
    assert record["handoff_id"] == newer_a["handoff_id"]
    # user_b's record is still pending
    assert hq.get(ip_dir, older_b["handoff_id"])[0] == "pending"
