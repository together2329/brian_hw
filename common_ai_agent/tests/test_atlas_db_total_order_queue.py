"""Wave 1 / Unit A — strict total-order session queue.

Covers plan §2.3, §2.4 and Task 2 (R1/R5):
  - rows enqueued at an artificially EQUAL created_at dequeue/poll exactly once,
    lowest rowid first (no skip, no reorder)
  - value-based since_id cursor makes forward progress and never skips an
    equal-timestamp row
  - dequeue marks processed-once (no double dequeue)
"""

from __future__ import annotations

from unittest import mock

import pytest

from core.atlas_db import AtlasDB


@pytest.fixture()
def db(tmp_path):
    return AtlasDB(db_path=str(tmp_path / "queue.db"))


def _equal_timestamp_enqueue(db, session_id, direction, count, ts=1000.0):
    """Insert `count` rows all sharing the SAME wall-clock created_at."""
    ids = []
    with mock.patch.object(AtlasDB, "_now", staticmethod(lambda: ts)):
        for i in range(count):
            ids.append(
                db.enqueue_message(session_id, direction, "token", {"i": i})
            )
    return ids


# ──────────────────────────────────────────────────────────────
# poll: equal-timestamp total order
# ──────────────────────────────────────────────────────────────

def test_poll_returns_all_equal_timestamp_rows_in_rowid_order(db):
    _equal_timestamp_enqueue(db, "s1", "out", 5)
    rows = db.poll_messages("s1", "out")
    assert len(rows) == 5
    # inserted in i-order; rowid is monotonic -> i must come back in order.
    assert [r["payload"]["i"] for r in rows] == [0, 1, 2, 3, 4]
    # all share the same created_at (this is the hazard the tiebreaker fixes).
    assert {r["created_at"] for r in rows} == {1000.0}


def test_dequeue_returns_equal_timestamp_rows_lower_id_first(db):
    _equal_timestamp_enqueue(db, "s1", "in", 3)
    got = [db.dequeue_message("s1", "in", timeout=0.1) for _ in range(3)]
    assert [g["payload"]["i"] for g in got] == [0, 1, 2]
    # queue now drained.
    assert db.dequeue_message("s1", "in", timeout=0.05) is None


def test_dequeue_processes_each_row_exactly_once(db):
    _equal_timestamp_enqueue(db, "s1", "in", 4)
    seen = []
    while True:
        m = db.dequeue_message("s1", "in", timeout=0.05)
        if m is None:
            break
        seen.append(m["id"])
    # no id delivered twice.
    assert len(seen) == len(set(seen)) == 4


# ──────────────────────────────────────────────────────────────
# value-based cursor: forward progress, no skip across equal ts
# ──────────────────────────────────────────────────────────────

def test_value_based_cursor_does_not_skip_equal_timestamp_row(db):
    ids = _equal_timestamp_enqueue(db, "s1", "out", 5)
    # Walk the queue one row at a time using since_id; must visit ALL rows.
    visited = []
    cursor = None
    for _ in range(10):  # safety bound
        batch = db.poll_messages("s1", "out", since_id=cursor, limit=1)
        if not batch:
            break
        row = batch[0]
        visited.append(row["payload"]["i"])
        cursor = row["id"]
    assert visited == [0, 1, 2, 3, 4]
    # the cursor walk visited every enqueued id once.
    assert len(visited) == len(ids)


def test_cursor_after_first_returns_rest_in_order(db):
    _equal_timestamp_enqueue(db, "s1", "out", 4)
    first = db.poll_messages("s1", "out", limit=1)
    assert first[0]["payload"]["i"] == 0
    rest = db.poll_messages("s1", "out", since_id=first[0]["id"])
    assert [r["payload"]["i"] for r in rest] == [1, 2, 3]


def test_cursor_forward_progress_across_distinct_timestamps(db):
    # mix: two rows at ts=1000, two at a LATER ts; ensure ordering holds.
    with mock.patch.object(AtlasDB, "_now", staticmethod(lambda: 1000.0)):
        db.enqueue_message("s1", "out", "token", {"i": 0})
        db.enqueue_message("s1", "out", "token", {"i": 1})
    with mock.patch.object(AtlasDB, "_now", staticmethod(lambda: 2000.0)):
        db.enqueue_message("s1", "out", "token", {"i": 2})
        db.enqueue_message("s1", "out", "token", {"i": 3})
    rows = db.poll_messages("s1", "out")
    assert [r["payload"]["i"] for r in rows] == [0, 1, 2, 3]
    # cursor at the i=1 row must yield only the later-ts rows.
    rest = db.poll_messages("s1", "out", since_id=rows[1]["id"])
    assert [r["payload"]["i"] for r in rest] == [2, 3]


def test_cursor_at_last_row_returns_empty(db):
    _equal_timestamp_enqueue(db, "s1", "out", 3)
    rows = db.poll_messages("s1", "out")
    rest = db.poll_messages("s1", "out", since_id=rows[-1]["id"])
    assert rest == []


def test_absent_cursor_id_returns_empty_backward_compat(db):
    """Unit A preserves the historical 0-rows-on-absent-cursor contract.

    (Task 4 / Unit B replaces this with a non-silent recoverable status.)
    """
    _equal_timestamp_enqueue(db, "s1", "out", 2)
    assert db.poll_messages("s1", "out", since_id="does-not-exist") == []


def test_no_internal_rowid_leaks_into_results(db):
    _equal_timestamp_enqueue(db, "s1", "out", 2)
    rows = db.poll_messages("s1", "out")
    assert all("_rowid" not in r for r in rows)
    m = db.dequeue_message("s1", "in", timeout=0.01)
    assert m is None  # different direction
