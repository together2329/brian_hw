"""Implementation Review #2 + #3 — delete gate ordering & delivered-marking order.

These pin the two ordering bugs called out in
``doc/wiki/atlas-db-router-runtime-sharding-20260602.md`` under
"## Implementation Review Feedback - 2026-06-03":

  #2 DELETE GATE ORDERING. ``AtlasDB.delete_session`` used to DELETE the control
     parts/messages/sessions rows and COMMIT FIRST, then call
     ``runtime_rollup.delete_session_runtime`` which gates on runtime queue depth.
     A non-empty runtime queue with ``force=False`` skips the runtime delete, but
     the control session was already gone -> orphaned runtime file + manifest
     while the API can still report ``deleted``. The fix runs the runtime
     queue-depth gate BEFORE deleting control rows: a non-empty queue without
     force leaves BOTH the control session AND the runtime file intact and
     returns a not-deleted / force-required signal. ``force=True`` removes both
     and writes an audit row. Central mode stays byte-identical.

  #3 DELIVERED-MARKING ORDER. ``AtlasDB.mark_outputs_delivered`` marked rows with
     ``rowid <= rowid_of(up_to_id)``, but polling/dequeue use the strict total
     order ``(created_at, rowid)``. A backward wall-clock ``created_at`` can make
     a higher-rowid row sort EARLIER, so ``rowid<=`` would mark a row that was
     not yet delivered. The fix resolves ``up_to_id`` to its ``(created_at,
     rowid)`` boundary and marks with the matching tuple predicate.

Pure-Python / direct-DB; fast and deterministic.
"""

from __future__ import annotations

import os
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter
from core import runtime_rollup


# ──────────────────────────────────────────────────────────────────────────
# fixtures / helpers
# ──────────────────────────────────────────────────────────────────────────


@pytest.fixture
def split_env(tmp_path, monkeypatch):
    """Pin a session-mode router (control db + runtime root + mode)."""
    control_path = str(tmp_path / "control.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    AtlasDB(control_path, schema_set="full").close()
    return control_path, runtime_root


def _seed_session(control_path: str, session_id: str, user_id: str = "u-test") -> str:
    """Create control user + session + manifest; return the runtime path."""
    with AtlasDB(control_path, schema_set="full") as db:
        if not db._fetchone("SELECT 1 FROM users WHERE id = ?", (user_id,)):
            db._execute(
                "INSERT OR IGNORE INTO users "
                "(id, username, display_name, role, created_at) "
                "VALUES (?, ?, ?, 'user', ?)",
                (user_id, user_id, user_id, db._now()),
            )
        db.upsert_runtime_session(
            session_id, user_id=user_id, ip_id="ip-test", workflow="rtl-gen",
            owner=user_id,
        )
    route = AtlasDBRouter().runtime_route(session_id, create=True)
    # Materialize the runtime file with the runtime schema.
    AtlasDB(route.runtime_db_path, schema_set="runtime").close()
    return route.runtime_db_path


def _enqueue(runtime_path, session_id, direction, msg_type, payload=None):
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        return rdb.enqueue_message(session_id, direction, msg_type, payload)


def _runtime_files_exist(runtime_path) -> list:
    return [
        runtime_path + suffix
        for suffix in ("", "-wal", "-shm")
        if os.path.exists(runtime_path + suffix)
    ]


# ──────────────────────────────────────────────────────────────────────────
# #2 — delete gate ordering
# ──────────────────────────────────────────────────────────────────────────


def test_delete_pending_queue_keeps_control_and_runtime_without_force(split_env):
    """A pending (undelivered) prompt -> non-force delete is a FULL no-op.

    Both the control ``sessions`` row AND the runtime file must remain, and the
    return dict must signal not-deleted / force-required so the API can surface a
    409 instead of reporting a deleted session whose runtime work was orphaned.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    # Undelivered inbound prompt => runtime queue depth > 0.
    _enqueue(runtime_path, session_id, "in", "prompt", {"text": "pending"})

    with AtlasDB(control_path, schema_set="full") as cdb:
        out = cdb.delete_session(session_id)
        # Control session row STILL present (gate ran before control delete).
        assert cdb.get_session(session_id) is not None
        # Runtime manifest STILL present.
        assert cdb.get_session_runtime_db(session_id) is not None

    # Top-level not-deleted signal + force-required surface for the API.
    assert out["deleted"] is False
    assert out["runtime"]["deleted"] is False
    assert out["runtime"]["skipped_reason"] == "queue_non_empty"
    assert out["runtime"]["force_required"] is True
    assert out["runtime"]["queue_depth"] >= 1

    # Runtime file (and sidecars) intact on disk.
    assert _runtime_files_exist(runtime_path)


def test_force_delete_pending_queue_removes_both_and_audits(split_env):
    """``force=True`` with a pending prompt removes BOTH + writes an audit row."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _enqueue(runtime_path, session_id, "in", "prompt", {"text": "do it"})

    with AtlasDB(control_path, schema_set="full") as cdb:
        out = cdb.delete_session(session_id, force=True)
        assert cdb.get_session(session_id) is None
        assert cdb.get_session_runtime_db(session_id) is None
        audit = cdb.list_runtime_db_audit(session_id=session_id)

    assert out["deleted"] is True
    assert out["runtime"]["deleted"] is True
    assert out["runtime"]["forced"] is True
    assert _runtime_files_exist(runtime_path) == []

    assert len(audit) == 1
    assert audit[0]["action"] == "force_delete"
    assert audit[0]["forced"] == 1
    assert audit[0]["queue_depth"] >= 1


def test_empty_queue_delete_removes_both(split_env):
    """A clean (depth==0) delete still removes control + runtime in order."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    with AtlasDB(control_path, schema_set="full") as cdb:
        out = cdb.delete_session(session_id)
        assert cdb.get_session(session_id) is None
        assert cdb.get_session_runtime_db(session_id) is None

    assert out["deleted"] is True
    assert out["runtime"]["deleted"] is True
    assert _runtime_files_exist(runtime_path) == []


def test_central_mode_delete_still_works(tmp_path, monkeypatch):
    """Central mode: runtime step is a no-op; control delete proceeds as before."""
    control_path = str(tmp_path / "central.db")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ROOT", raising=False)
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)

    with AtlasDB(control_path, schema_set="full") as cdb:
        user = cdb.create_user("zoe", "Zoe")
        session = cdb.create_session(user["id"], "central")
        msg = cdb.save_message(session["id"], "user", agent="t")
        cdb.save_part(msg["id"], session["id"], "text", text="hello")

        out = cdb.delete_session(session["id"])

        assert cdb.get_session(session["id"]) is None
        assert cdb.get_messages(session["id"]) == []
        assert cdb.get_parts(msg["id"]) == []

    assert out["deleted"] is True
    assert out["runtime"]["deleted"] is False
    assert out["runtime"]["skipped_reason"] == "central_mode"


# ──────────────────────────────────────────────────────────────────────────
# #3 — delivered-marking order matches polling order
# ──────────────────────────────────────────────────────────────────────────


def _set_created_at(db: AtlasDB, msg_id: str, created_at: float) -> None:
    """Force a queue row's created_at to simulate a backward wall-clock step."""
    db._execute(
        "UPDATE session_queue SET created_at = ? WHERE id = ?",
        (created_at, msg_id),
    )


def _runtime_db(tmp_path, name: str) -> AtlasDB:
    """A fresh on-disk runtime DB.

    NOT ``:memory:``: AtlasDB caches a per-(path, schema_set) schema-init guard,
    so a second ``:memory:`` AtlasDB in the same process opens a brand-new empty
    in-memory database but SKIPS the bootstrap -> ``no such table: session_queue``.
    A unique on-disk path per test sidesteps that.
    """
    return AtlasDB(str(tmp_path / name), schema_set="runtime")


def test_mark_delivered_uses_created_at_rowid_order_not_bare_rowid(tmp_path):
    """Backward wall-clock: marking up to the FIRST visible row must not over-mark.

    Two out-rows: rowid=1 has created_at=100 (inserted first), rowid=2 has
    created_at=90 (a backward wall-clock step). Polling orders by
    ``(created_at, rowid)`` so rowid=2 (created_at=90) comes FIRST. After marking
    delivered "up to" that first visible row (rowid=2), the still-undelivered,
    later-sorting rowid=1 (created_at=100) MUST NOT be marked — the old bare
    ``rowid <= 2`` predicate would have wrongly marked it.
    """
    db = _runtime_db(tmp_path, "order.db")
    try:
        session_id = "s-order"
        a = db.enqueue_message(session_id, "out", "token", {"i": "a"})  # rowid 1
        b = db.enqueue_message(session_id, "out", "token", {"i": "b"})  # rowid 2
        # Backward wall-clock skew: a is "later", b is "earlier".
        _set_created_at(db, a, 100.0)
        _set_created_at(db, b, 90.0)

        # Poll order is (created_at, rowid) -> b (90) BEFORE a (100).
        rows = db.poll_messages(session_id, "out", since_id=None, limit=10)
        ids = [r["id"] for r in rows]
        assert ids[0] == b, "lower created_at must poll first"
        assert ids == [b, a]

        # Mark delivered UP TO the first visible row (b). With the tuple
        # predicate only b is marked; a (higher rowid but later created_at) stays
        # undelivered. The bare-rowid bug would mark BOTH (rowid 1 and 2 <= 2).
        marked = db.mark_outputs_delivered(session_id, b, direction="out")
        assert marked == 1, "only the first visible row (b) is delivered"

        a_row = db.get_message(a)
        b_row = db.get_message(b)
        assert b_row["delivered_at"] is not None, "b was delivered"
        assert a_row["delivered_at"] is None, (
            "a (rowid 1, created_at 100) was NOT yet delivered and must stay "
            "undelivered despite its lower rowid"
        )

        # A subsequent poll of UNDELIVERED rows must still return a.
        remaining = db.poll_messages(session_id, "out", since_id=None, limit=10)
        assert [r["id"] for r in remaining] == [a]
    finally:
        db.close()


def test_mark_delivered_in_order_marks_both_when_monotonic(tmp_path):
    """Sanity: with monotonic created_at, marking up to the last row marks all."""
    db = _runtime_db(tmp_path, "mono.db")
    try:
        session_id = "s-mono"
        a = db.enqueue_message(session_id, "out", "token", {"i": "a"})
        b = db.enqueue_message(session_id, "out", "token", {"i": "b"})
        _set_created_at(db, a, 100.0)
        _set_created_at(db, b, 101.0)

        marked = db.mark_outputs_delivered(session_id, b, direction="out")
        assert marked == 2, "both rows up to and including b are delivered"
        assert db.get_message(a)["delivered_at"] is not None
        assert db.get_message(b)["delivered_at"] is not None
    finally:
        db.close()


def test_reseed_cursor_consistent_with_marking_order(tmp_path):
    """``reseed_output_cursor`` resumes from the newest delivered row in (ca,rowid).

    After the backward-skew delivery above, only b (created_at=90) is delivered.
    The resume cursor must therefore be b, and a subsequent poll since b returns
    exactly the still-undelivered a — no duplicate, no stall.
    """
    db = _runtime_db(tmp_path, "reseed.db")
    try:
        session_id = "s-reseed"
        a = db.enqueue_message(session_id, "out", "token", {"i": "a"})
        b = db.enqueue_message(session_id, "out", "token", {"i": "b"})
        _set_created_at(db, a, 100.0)
        _set_created_at(db, b, 90.0)

        db.mark_outputs_delivered(session_id, b, direction="out")
        cursor = db.reseed_output_cursor(session_id, direction="out")
        assert cursor == b, "newest already-delivered row in (created_at, rowid)"

        after = db.poll_messages(session_id, "out", since_id=cursor, limit=10)
        assert [r["id"] for r in after] == [a], "resume yields exactly a, no dupes"
    finally:
        db.close()
