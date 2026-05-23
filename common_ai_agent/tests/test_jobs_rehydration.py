"""
tests/test_jobs_rehydration.py

Verify _rehydrate_jobs_from_db reconciles orphaned workflow_runs on boot.

Seeds the DB with 3 rows with status='running':
  - row A: worker URL returns healthy + running_count=1  → rescued into _jobs
  - row B: worker URL unreachable                        → marked error in DB
  - row C: worker URL healthy but running_count=0        → marked error in DB

After calling _rehydrate_jobs_from_db(db):
  - _jobs contains exactly 1 entry (row A) with status='running'
  - rows B and C have status='error' in the DB
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from unittest.mock import patch, MagicMock

import pytest

import src.atlas_api_jobs as _mod
from core.atlas_db import AtlasDB


# ── fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture()
def tmp_db(tmp_path):
    """Return an AtlasDB backed by a temp file (auto-closed after test)."""
    db_path = str(tmp_path / "test_atlas.db")
    with AtlasDB(db_path) as db:
        yield db


@pytest.fixture(autouse=True)
def clean_jobs():
    """Clear _jobs before/after each test."""
    with _mod._jobs_lock:
        _mod._jobs.clear()
    yield
    with _mod._jobs_lock:
        _mod._jobs.clear()


# ── helpers ───────────────────────────────────────────────────────────────────

_LIVE_URL   = "http://127.0.0.1:18801"
_DEAD_URL   = "http://127.0.0.1:18802"
_IDLE_URL   = "http://127.0.0.1:18803"


def _seed_run(db: AtlasDB, worker_url: str, tag: str) -> str:
    """Insert a workflow_run with status='running' and return its run_id."""
    workspace = db.upsert_workspace("test-ws", owner_user_id="local-admin")
    ip_row = db.upsert_ip_block(workspace["id"], f"ip_{tag}")
    session = db.create_session("local-admin", f"session_{tag}", f"ip_{tag}")
    summary = {
        "ip": f"ip_{tag}",
        "workflow": "rtl-gen",
        "project_root": ".",
        "user_id": "local-admin",
        "worker": worker_url,
    }
    run = db.start_workflow_run(
        session_id=session["id"],
        workspace_id=workspace["id"],
        ip_id=ip_row["id"],
        workflow="rtl-gen",
        status="running",
        input_summary=json.dumps(summary),
    )
    return run["id"]


def _fake_probe(url: str, **_kwargs) -> dict:
    """Fake health probe: live URL healthy+busy, dead URL unreachable, idle URL healthy+idle."""
    if url.rstrip("/") == _LIVE_URL.rstrip("/"):
        return {"status": "ok", "running_count": 1}
    if url.rstrip("/") == _IDLE_URL.rstrip("/"):
        return {"status": "ok", "running_count": 0}
    # _DEAD_URL — simulate network error
    return {"status": "unreachable", "error": "connection refused"}


# ── tests ─────────────────────────────────────────────────────────────────────

class TestRehydrateJobsFromDB:

    def test_rescued_rescued_and_error_counts(self, tmp_db):
        """1 rescued + 2 marked-error matches the 3-row seed."""
        run_a = _seed_run(tmp_db, _LIVE_URL,  "A")
        run_b = _seed_run(tmp_db, _DEAD_URL,  "B")
        run_c = _seed_run(tmp_db, _IDLE_URL,  "C")

        with patch.object(_mod, "_probe_worker_health", side_effect=_fake_probe):
            _mod._rehydrate_jobs_from_db(tmp_db)

        with _mod._jobs_lock:
            jobs_snapshot = dict(_mod._jobs)

        # Exactly 1 job rescued
        assert len(jobs_snapshot) == 1, (
            f"Expected 1 rescued job, got {len(jobs_snapshot)}: {list(jobs_snapshot)}"
        )
        assert run_a in jobs_snapshot, "run_a (live worker) must be in _jobs"
        assert jobs_snapshot[run_a]["status"] == "running"

    def test_dead_runs_marked_error_in_db(self, tmp_db):
        """Orphaned rows must have status='error' after rehydration."""
        _seed_run(tmp_db, _LIVE_URL, "A2")
        run_b = _seed_run(tmp_db, _DEAD_URL, "B2")
        run_c = _seed_run(tmp_db, _IDLE_URL, "C2")

        with patch.object(_mod, "_probe_worker_health", side_effect=_fake_probe):
            _mod._rehydrate_jobs_from_db(tmp_db)

        row_b = tmp_db.get_workflow_run(run_b)
        row_c = tmp_db.get_workflow_run(run_c)
        assert row_b is not None and row_b["status"] == "error", (
            f"run_b should be 'error' in DB, got {row_b}"
        )
        assert row_c is not None and row_c["status"] == "error", (
            f"run_c should be 'error' in DB, got {row_c}"
        )

    def test_old_runs_outside_1h_window_ignored(self, tmp_db):
        """Runs older than 1 hour must not be rehydrated."""
        workspace = tmp_db.upsert_workspace("old-ws", owner_user_id="local-admin")
        ip_row = tmp_db.upsert_ip_block(workspace["id"], "ip_old")
        session = tmp_db.create_session("local-admin", "old", "ip_old")
        run = tmp_db.start_workflow_run(
            session_id=session["id"],
            workspace_id=workspace["id"],
            ip_id=ip_row["id"],
            workflow="rtl-gen",
            status="running",
        )
        # Backdate started_at to 2 hours ago
        two_hours_ago = time.time() - 7200.0
        tmp_db._execute(
            "UPDATE workflow_runs SET started_at = ? WHERE id = ?",
            (two_hours_ago, run["id"]),
        )

        with patch.object(_mod, "_probe_worker_health", side_effect=_fake_probe):
            _mod._rehydrate_jobs_from_db(tmp_db)

        with _mod._jobs_lock:
            assert run["id"] not in _mod._jobs, "Old run must not be rehydrated"
        # DB row unchanged (still 'running') — rehydrate only touches recent rows
        row = tmp_db.get_workflow_run(run["id"])
        assert row["status"] == "running", "Old run status must remain unchanged"
