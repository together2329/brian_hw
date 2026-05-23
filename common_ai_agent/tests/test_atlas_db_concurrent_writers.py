"""
Stress-tests for AtlasDB._WRITE_LOCK class-level serialization.

Confirms that 50 concurrent writer threads, each opening their own
AtlasDB() context manager, serialize cleanly without SQLite
"database is locked" errors or data corruption.
"""

from __future__ import annotations

import threading
import time
import uuid
from typing import List

import pytest

from core.atlas_db import AtlasDB

# ──────────────────────────────────────────────────────────────
# Helpers
# ──────────────────────────────────────────────────────────────

THREADS = 50
INSERTS_PER_THREAD = 20
EXPECTED_TOTAL = THREADS * INSERTS_PER_THREAD
TIMEOUT_S = 60


def _fake_session_id() -> str:
    return uuid.uuid4().hex


def _insert_messages(db_path: str, n: int, errors: list) -> None:
    """Worker: open one AtlasDB context and insert n messages."""
    try:
        session_id = _fake_session_id()
        with AtlasDB(db_path=db_path) as db:
            for _ in range(n):
                db.save_message(session_id=session_id, role="user")
    except Exception as exc:  # noqa: BLE001
        errors.append(exc)


# ──────────────────────────────────────────────────────────────
# Test 1 — 50 pure-writer threads, 20 inserts each
# ──────────────────────────────────────────────────────────────

def test_50_concurrent_writers_no_lock_errors(tmp_path, monkeypatch):
    """50 concurrent AtlasDB instances each insert 20 rows without database-is-locked errors."""
    db_path = str(tmp_path / "test.db")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)

    # Prime schema once so threads don't race on table creation.
    with AtlasDB(db_path=db_path):
        pass

    errors: List[Exception] = []
    threads = [
        threading.Thread(
            target=_insert_messages,
            args=(db_path, INSERTS_PER_THREAD, errors),
            daemon=True,
        )
        for _ in range(THREADS)
    ]

    start = time.monotonic()
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=TIMEOUT_S)
    elapsed = time.monotonic() - start

    # No thread should still be alive (join timed out).
    alive = [t for t in threads if t.is_alive()]
    assert not alive, f"{len(alive)} threads still running after {TIMEOUT_S}s"

    # No exceptions raised inside any worker thread.
    assert not errors, f"Thread errors: {errors}"

    # Total row count must equal 50 × 20.
    with AtlasDB(db_path=db_path) as db:
        row = db._fetchone("SELECT COUNT(*) AS cnt FROM messages")
        total = row["cnt"]

    assert total == EXPECTED_TOTAL, (
        f"Expected {EXPECTED_TOTAL} rows, got {total}"
    )

    # All primary keys must be unique (COUNT == COUNT DISTINCT).
    with AtlasDB(db_path=db_path) as db:
        row = db._fetchone("SELECT COUNT(DISTINCT id) AS cnt FROM messages")
        unique = row["cnt"]
    assert unique == EXPECTED_TOTAL, (
        f"Duplicate PKs detected: {EXPECTED_TOTAL - unique} collisions"
    )

    assert elapsed < TIMEOUT_S, f"Run took {elapsed:.1f}s, limit is {TIMEOUT_S}s"


# ──────────────────────────────────────────────────────────────
# Test 2 — 25 writers + 25 readers, mixed concurrency
# ──────────────────────────────────────────────────────────────

_WRITER_THREADS = 25
_READER_THREADS = 25
_WRITER_INSERTS = 5      # inserts per writer thread
_READER_SELECTS = 5      # SELECT COUNT(*) calls per reader thread
_MIXED_EXPECTED = _WRITER_THREADS * _WRITER_INSERTS


def _mixed_reader(db_path: str, errors: list) -> None:
    """Worker: open one AtlasDB context and run 5 SELECT COUNT(*) queries."""
    try:
        with AtlasDB(db_path=db_path) as db:
            for _ in range(_READER_SELECTS):
                db._fetchone("SELECT COUNT(*) AS cnt FROM messages")
    except Exception as exc:  # noqa: BLE001
        errors.append(exc)


def test_25_writers_25_readers_no_lock_errors(tmp_path, monkeypatch):
    """25 writer + 25 reader threads run concurrently with no lock errors and correct final count."""
    db_path = str(tmp_path / "mixed.db")
    monkeypatch.setenv("ATLAS_DB_PATH", db_path)

    # Prime schema.
    with AtlasDB(db_path=db_path):
        pass

    errors: List[Exception] = []
    writer_threads = [
        threading.Thread(
            target=_insert_messages,
            args=(db_path, _WRITER_INSERTS, errors),
            daemon=True,
        )
        for _ in range(_WRITER_THREADS)
    ]
    reader_threads = [
        threading.Thread(
            target=_mixed_reader,
            args=(db_path, errors),
            daemon=True,
        )
        for _ in range(_READER_THREADS)
    ]

    all_threads = writer_threads + reader_threads
    start = time.monotonic()
    for t in all_threads:
        t.start()
    for t in all_threads:
        t.join(timeout=TIMEOUT_S)
    elapsed = time.monotonic() - start

    alive = [t for t in all_threads if t.is_alive()]
    assert not alive, f"{len(alive)} threads still running after {TIMEOUT_S}s"

    assert not errors, f"Thread errors: {errors}"

    with AtlasDB(db_path=db_path) as db:
        row = db._fetchone("SELECT COUNT(*) AS cnt FROM messages")
        total = row["cnt"]

    assert total == _MIXED_EXPECTED, (
        f"Expected {_MIXED_EXPECTED} rows, got {total}"
    )

    assert elapsed < TIMEOUT_S, f"Run took {elapsed:.1f}s, limit is {TIMEOUT_S}s"
