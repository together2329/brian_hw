"""
Concurrent SQLite write-race tests for AtlasDB workflow_runs.

Tests that 10 threads can simultaneously start and finish workflow runs
without deadlocks, data loss, or "database is locked" errors.
Also verifies WAL journal mode and busy_timeout are configured.
"""

import tempfile
import threading
import concurrent.futures
import sqlite3
from pathlib import Path

import pytest

from core.atlas_db import AtlasDB


@pytest.fixture()
def db(tmp_path):
    db_path = str(tmp_path / "test_atlas.db")
    return AtlasDB(db_path=db_path)


# ---------------------------------------------------------------------------
# Helper
# ---------------------------------------------------------------------------

def _start_one(db: AtlasDB, workspace_id: str, ip_id: str) -> dict:
    return db.start_workflow_run(
        workspace_id=workspace_id,
        ip_id=ip_id,
        workflow="ssot-gen",
        trigger_source="test",
    )


# ---------------------------------------------------------------------------
# Core concurrency test
# ---------------------------------------------------------------------------

class TestConcurrentWorkflowRuns:
    def test_10_threads_start_workflow_runs(self, db):
        """10 threads concurrently insert workflow runs; all must succeed."""
        errors = []
        results = [None] * 10

        def worker(n):
            try:
                results[n] = _start_one(db, workspace_id="ws-main", ip_id=f"ip-{n}")
            except Exception as exc:
                errors.append(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(worker, n) for n in range(10)]
            concurrent.futures.wait(futs)

        assert not errors, f"Exceptions during concurrent starts: {errors}"

        # All 10 rows must have been inserted
        assert all(r is not None for r in results), "Some start_workflow_run calls returned None"
        assert len(results) == 10

        # All must have status='running'
        for r in results:
            assert r["status"] == "running", f"Expected 'running', got {r['status']}"

        # All ids must be distinct
        ids = [r["id"] for r in results]
        assert len(set(ids)) == 10, "Duplicate run IDs detected"

    def test_10_threads_finish_workflow_runs(self, db):
        """10 threads concurrently finish previously started runs; all must reach completed."""
        # Start 10 runs sequentially so we have known IDs
        run_ids = []
        for n in range(10):
            row = _start_one(db, workspace_id="ws-finish", ip_id=f"ip-{n}")
            run_ids.append(row["id"])

        errors = []
        finished = [None] * 10

        def finish_worker(idx):
            try:
                finished[idx] = db.finish_workflow_run(run_ids[idx], status="completed")
            except Exception as exc:
                errors.append(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(finish_worker, i) for i in range(10)]
            concurrent.futures.wait(futs)

        assert not errors, f"Exceptions during concurrent finishes: {errors}"
        assert all(f is not None for f in finished), "Some finish_workflow_run calls returned None"

        for f in finished:
            assert f["status"] == "completed", f"Expected 'completed', got {f['status']}"

    def test_start_and_finish_interleaved(self, db):
        """Start + finish all 10 runs in a single concurrent wave."""
        errors = []
        start_results = [None] * 10
        finish_results = [None] * 10
        barrier = threading.Barrier(10)

        def worker(n):
            try:
                row = _start_one(db, workspace_id="ws-interleaved", ip_id=f"ip-{n}")
                start_results[n] = row
                barrier.wait(timeout=10)  # all must have started before any finishes
                finish_results[n] = db.finish_workflow_run(row["id"], status="completed")
            except Exception as exc:
                errors.append(exc)

        with concurrent.futures.ThreadPoolExecutor(max_workers=10) as pool:
            futs = [pool.submit(worker, n) for n in range(10)]
            concurrent.futures.wait(futs, timeout=30)

        assert not errors, f"Exceptions during interleaved test: {errors}"
        assert all(r is not None for r in start_results)
        assert all(f is not None for f in finish_results)
        for f in finish_results:
            assert f["status"] == "completed"


# ---------------------------------------------------------------------------
# SQLite pragma tests
# ---------------------------------------------------------------------------

class TestSQLitePragmas:
    def test_busy_timeout_is_set(self, db):
        """Verify SQLite busy_timeout is configured (> 0) to queue writers."""
        conn = sqlite3.connect(db.db_path)
        try:
            row = conn.execute("PRAGMA busy_timeout").fetchone()
            timeout_val = row[0] if row else 0
            assert timeout_val > 0, (
                f"busy_timeout is {timeout_val}. "
                "Set PRAGMA busy_timeout = <ms> in AtlasDB._connect() to avoid "
                "'database is locked' errors under concurrent writes."
            )
        finally:
            conn.close()

    def test_wal_journal_mode(self, db):
        """Verify WAL journal mode is active (allows concurrent reads + queued writers)."""
        conn = sqlite3.connect(db.db_path)
        try:
            row = conn.execute("PRAGMA journal_mode").fetchone()
            mode = row[0] if row else "unknown"
            assert mode.lower() == "wal", (
                f"journal_mode is '{mode}', expected 'wal'. "
                "Enable WAL with: conn.execute('PRAGMA journal_mode=WAL') in AtlasDB._connect()."
            )
        finally:
            conn.close()
