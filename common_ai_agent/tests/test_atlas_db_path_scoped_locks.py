"""Wave 1 / Unit A — path-scoped write locks.

Covers plan §2.2 and Task 2 (R11):
  (a) same path still serializes (a held write lock on A blocks a second writer
      on A)
  (b) two DIFFERENT paths are NOT serialized (a held write lock on A does not
      block a writer on B — completes under a hard bound)
  (c) NEGATIVE control: forcing a single global lock makes the cross-path test
      TIME OUT — proving the cross-path test actually detects de-serialization
      and is not vacuously green.
"""

from __future__ import annotations

import threading
import time

import pytest

from core.atlas_db import AtlasDB


# Hard bounds. The lock-hold duration is comfortably larger than the
# cross-path completion bound so a serialized (global-lock) world is clearly
# distinguishable from a de-serialized (path-lock) world.
HOLD_S = 2.0
CROSS_PATH_BOUND_S = 1.0


def _writer(db_path, started_evt, done_evt, errors):
    """Open a DB on db_path and perform one write, recording completion time."""
    try:
        db = AtlasDB(db_path=db_path)
        started_evt.set()
        db.enqueue_message("s1", "out", "token", {"x": 1})
        done_evt.set()
    except Exception as exc:  # noqa: BLE001
        errors.append(exc)
        done_evt.set()


# ──────────────────────────────────────────────────────────────
# (a) same path serializes
# ──────────────────────────────────────────────────────────────

def test_same_path_serializes(tmp_path):
    path_a = str(tmp_path / "a.db")
    # Prime schema so the writer thread doesn't race on init.
    AtlasDB(db_path=path_a)

    lock = AtlasDB._lock_for_path(path_a)
    # Hold the SAME path's lock for HOLD_S in a holder thread.
    release = threading.Event()
    holding = threading.Event()

    def holder():
        with lock:
            holding.set()
            release.wait(HOLD_S + 1.0)

    h = threading.Thread(target=holder, daemon=True)
    h.start()
    assert holding.wait(2.0)

    errors = []
    started = threading.Event()
    done = threading.Event()
    w = threading.Thread(
        target=_writer, args=(path_a, started, done, errors), daemon=True
    )
    t0 = time.monotonic()
    w.start()
    # The writer must NOT complete while the same-path lock is held.
    completed_early = done.wait(CROSS_PATH_BOUND_S)
    assert not completed_early, "same-path writer completed despite held lock"

    # Release the lock; the writer should now finish.
    release.set()
    assert done.wait(5.0), "same-path writer never completed after release"
    assert not errors, f"writer errors: {errors}"
    # Sanity: it actually waited roughly until release.
    assert time.monotonic() - t0 >= CROSS_PATH_BOUND_S


# ──────────────────────────────────────────────────────────────
# (b) different paths are NOT serialized
# ──────────────────────────────────────────────────────────────

def test_different_paths_not_serialized(tmp_path):
    path_a = str(tmp_path / "a.db")
    path_b = str(tmp_path / "b.db")
    AtlasDB(db_path=path_a)
    AtlasDB(db_path=path_b)

    lock_a = AtlasDB._lock_for_path(path_a)
    lock_b = AtlasDB._lock_for_path(path_b)
    assert lock_a is not lock_b, "distinct paths must have distinct locks"

    # Hold A's lock for a long time...
    release = threading.Event()
    holding = threading.Event()

    def holder():
        with lock_a:
            holding.set()
            release.wait(HOLD_S + 1.0)

    h = threading.Thread(target=holder, daemon=True)
    h.start()
    assert holding.wait(2.0)

    # ...a writer on B must complete WELL under the bound (not blocked by A).
    errors = []
    started = threading.Event()
    done = threading.Event()
    w = threading.Thread(
        target=_writer, args=(path_b, started, done, errors), daemon=True
    )
    w.start()
    completed = done.wait(CROSS_PATH_BOUND_S)
    release.set()
    assert completed, (
        f"writer on B did not complete within {CROSS_PATH_BOUND_S}s while A's "
        "lock was held — paths are being serialized together"
    )
    assert not errors, f"writer errors: {errors}"


# ──────────────────────────────────────────────────────────────
# (c) NEGATIVE control: a forced single global lock makes (b) time out
# ──────────────────────────────────────────────────────────────

def test_global_lock_shim_makes_cross_path_test_time_out(tmp_path, monkeypatch):
    """Prove the cross-path test is not vacuously green.

    If we force every path to share ONE global RLock (the OLD behavior), the
    same scenario as test_different_paths_not_serialized must NOW block — i.e.
    the writer on B does NOT complete within the bound. This demonstrates the
    cross-path test genuinely detects de-serialization.
    """
    global_lock = threading.RLock()
    monkeypatch.setattr(AtlasDB, "_lock_for_path", staticmethod(lambda p: global_lock))

    path_a = str(tmp_path / "a.db")
    path_b = str(tmp_path / "b.db")
    AtlasDB(db_path=path_a)
    AtlasDB(db_path=path_b)

    # Both paths now map to the SAME global lock.
    assert AtlasDB._lock_for_path(path_a) is AtlasDB._lock_for_path(path_b)

    release = threading.Event()
    holding = threading.Event()

    def holder():
        with global_lock:
            holding.set()
            release.wait(HOLD_S + 1.0)

    h = threading.Thread(target=holder, daemon=True)
    h.start()
    assert holding.wait(2.0)

    errors = []
    started = threading.Event()
    done = threading.Event()
    w = threading.Thread(
        target=_writer, args=(path_b, started, done, errors), daemon=True
    )
    w.start()
    # Under a single global lock, the B writer is BLOCKED -> must time out here.
    completed = done.wait(CROSS_PATH_BOUND_S)
    release.set()
    assert not completed, (
        "cross-path writer completed even under a forced global lock — the "
        "cross-path test would be vacuously green and cannot detect "
        "de-serialization"
    )
    # After release it should finish (proves it was only blocked, not broken).
    assert done.wait(5.0)
    assert not errors, f"writer errors: {errors}"


# ──────────────────────────────────────────────────────────────
# lock identity / :memory: handling
# ──────────────────────────────────────────────────────────────

def test_same_resolved_path_shares_one_lock(tmp_path):
    path_a = str(tmp_path / "a.db")
    # Two spellings of the same file resolve to the same lock.
    spelled = str(tmp_path / "." / "a.db")
    assert AtlasDB._lock_for_path(path_a) is AtlasDB._lock_for_path(spelled)


def test_memory_db_gets_instance_local_lock():
    l1 = AtlasDB._lock_for_path(":memory:")
    l2 = AtlasDB._lock_for_path(":memory:")
    # Each :memory: request is unshareable -> distinct lock objects.
    assert l1 is not l2


def test_concurrent_writers_same_path_no_corruption(tmp_path):
    """Same-path concurrency still produces correct, collision-free rows."""
    path = str(tmp_path / "c.db")
    AtlasDB(db_path=path)
    errors = []

    def worker():
        try:
            db = AtlasDB(db_path=path)
            for _ in range(20):
                db.enqueue_message("s1", "out", "token", {"x": 1})
        except Exception as exc:  # noqa: BLE001
            errors.append(exc)

    threads = [threading.Thread(target=worker, daemon=True) for _ in range(10)]
    for t in threads:
        t.start()
    for t in threads:
        t.join(timeout=30)
    assert not errors, f"errors: {errors}"
    db = AtlasDB(db_path=path)
    total = db._fetchone("SELECT COUNT(*) AS c FROM session_queue")["c"]
    distinct = db._fetchone("SELECT COUNT(DISTINCT id) AS c FROM session_queue")["c"]
    assert total == 200
    assert distinct == 200
