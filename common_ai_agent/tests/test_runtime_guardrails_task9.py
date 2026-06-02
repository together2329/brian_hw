"""Wave 3 / Task 9 — operational guardrails.

Covers plan §2.12 + R12/R13/R18/R25 for the runtime-DB lifecycle:

1. ORPHAN-FREE session delete (R12): after delete, ZERO runtime files
   (.db/-wal/-shm) and ZERO manifest/rollup/offset rows for the session; a
   delete with a NON-EMPTY queue is REFUSED without ``force`` and, with
   ``force=True``, deletes AND writes a ``force_delete`` audit row.
2. RESTART recovery (R13): a runtime DB with an undelivered out-row is REPLAYED
   (resume cursor = newest-already-delivered, NOT latest) after a simulated
   restart, with no duplicate of already-delivered rows; the _jobs-loss policy
   is documented.
3. IDEMPOTENT forced rollback (R18): run-twice rollback copies exactly one row
   per undelivered prompt (INSERT OR IGNORE on original id), the prompt is
   preserved, and history orphaning is documented.
4. FLEET health/audit JSON (R25): the shape the Task-10 harness consumes, with
   correct ``rollback_allowed`` (= all queue depths 0).

Pure-Python / direct-DB (no real subprocess), fast and deterministic.
"""

from __future__ import annotations

import os
import sqlite3
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
from core.session_process_manager import SessionProcessManager


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


def _control_bookkeeping(control_path, session_id):
    with AtlasDB(control_path, schema_set="full") as cdb:
        manifest = cdb.get_session_runtime_db(session_id)
        rollup = cdb.get_runtime_usage_rollup(session_id)
        offsets = cdb._fetchall(
            "SELECT * FROM runtime_rollup_offsets WHERE session_id = ?",
            (session_id,),
        )
    return manifest, rollup, list(offsets)


# ──────────────────────────────────────────────────────────────────────────
# 1. orphan-free session delete (R12)
# ──────────────────────────────────────────────────────────────────────────


def test_delete_empty_queue_removes_all_runtime_state(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    # Roll up once so a rollup row + offsets exist (the orphan risk surface).
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.record_llm_call(
            session_id=session_id, ip_id="ip-test", workflow="rtl-gen",
            model="m", call_role="worker", tokens_input=10, tokens_output=5,
            cost_usd=0.1,
        )
    runtime_rollup.rollup_session(session_id)

    assert _runtime_files_exist(runtime_path)  # file is present pre-delete
    manifest, rollup, offsets = _control_bookkeeping(control_path, session_id)
    assert manifest is not None and rollup is not None and offsets

    result = runtime_rollup.delete_session_runtime(session_id)
    assert result.deleted is True
    assert result.forced is False

    # ZERO orphan files.
    assert _runtime_files_exist(runtime_path) == []
    # ZERO manifest / rollup / offset rows.
    manifest, rollup, offsets = _control_bookkeeping(control_path, session_id)
    assert manifest is None
    assert rollup is None
    assert offsets == []


def test_delete_via_atlasdb_delete_session_in_session_mode(split_env):
    """The control-table delete entrypoint also scrubs runtime state."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    with AtlasDB(control_path, schema_set="full") as cdb:
        out = cdb.delete_session(session_id)
    assert out["runtime"]["deleted"] is True
    assert _runtime_files_exist(runtime_path) == []
    manifest, rollup, offsets = _control_bookkeeping(control_path, session_id)
    assert manifest is None and rollup is None and offsets == []


def test_delete_non_empty_queue_refused_without_force(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    # Undelivered out-row => queue depth > 0.
    _enqueue(runtime_path, session_id, "out", "token", {"text": "hi"})

    result = runtime_rollup.delete_session_runtime(session_id, force=False)
    assert result.deleted is False
    assert result.skipped_reason == "queue_non_empty"
    assert result.queue_depth >= 1
    # Nothing was removed.
    assert _runtime_files_exist(runtime_path)
    manifest, _rollup, _offsets = _control_bookkeeping(control_path, session_id)
    assert manifest is not None


def test_force_delete_non_empty_queue_writes_audit(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _enqueue(runtime_path, session_id, "in", "prompt", {"text": "do it"})

    result = runtime_rollup.delete_session_runtime(session_id, force=True)
    assert result.deleted is True
    assert result.forced is True
    assert result.queue_depth >= 1
    assert _runtime_files_exist(runtime_path) == []

    with AtlasDB(control_path, schema_set="full") as cdb:
        audit = cdb.list_runtime_db_audit(session_id=session_id)
    assert len(audit) == 1
    assert audit[0]["action"] == "force_delete"
    assert audit[0]["forced"] == 1
    assert audit[0]["queue_depth"] >= 1
    # detail JSON round-trips.
    assert isinstance(audit[0]["detail"], dict)
    assert "files_removed" in audit[0]["detail"]


def test_delete_central_mode_is_noop(tmp_path, monkeypatch):
    control_path = str(tmp_path / "control.db")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    AtlasDB(control_path, schema_set="full").close()
    result = runtime_rollup.delete_session_runtime("any/session/id")
    assert result.deleted is False
    assert result.skipped_reason == "central_mode"


# ──────────────────────────────────────────────────────────────────────────
# 2. restart recovery replays undelivered, no dupes (R13)
# ──────────────────────────────────────────────────────────────────────────


def test_restart_replays_undelivered_no_dupes(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)

    # Three out-rows; mark the first two delivered, leave the third undelivered.
    id1 = _enqueue(runtime_path, session_id, "out", "token", {"text": "a"})
    id2 = _enqueue(runtime_path, session_id, "out", "token", {"text": "b"})
    id3 = _enqueue(runtime_path, session_id, "out", "token", {"text": "c"})
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.mark_outputs_delivered(session_id, id2, "out")  # marks id1+id2

    # Simulated restart: build the recovery plan from the manifest alone.
    plan = runtime_rollup.plan_session_recovery(session_id)
    assert plan.status == "ok"
    # Resume cursor is the newest ALREADY-DELIVERED row (id2), NOT the latest
    # (id3) — using latest would skip the buffered, undelivered id3.
    assert plan.resume_cursor == id2
    assert plan.undelivered_out == 1

    # A poll from the resume cursor returns exactly the undelivered id3, once.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        replayed = rdb.poll_messages(session_id, "out", since_id=plan.resume_cursor)
    assert [r["id"] for r in replayed] == [id3]
    # The already-delivered rows are NOT re-delivered.
    assert id1 not in [r["id"] for r in replayed]


def test_restart_nothing_delivered_replays_from_top(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    id1 = _enqueue(runtime_path, session_id, "out", "token", {"text": "a"})
    id2 = _enqueue(runtime_path, session_id, "out", "token", {"text": "b"})

    plan = runtime_rollup.plan_session_recovery(session_id)
    # Nothing delivered yet -> resume from the top (None), buffered output replays.
    assert plan.resume_cursor is None
    assert plan.undelivered_out == 2
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        replayed = rdb.poll_messages(session_id, "out", since_id=None)
    assert [r["id"] for r in replayed] == [id1, id2]


def test_recover_all_sessions_missing_file_marked(split_env):
    control_path, _root = split_env
    session_a = "u-test/ip-test/alpha"
    session_b = "u-test/ip-test/beta"
    path_a = _seed_session(control_path, session_a)
    _seed_session(control_path, session_b)
    _enqueue(path_a, session_a, "out", "token", {"text": "x"})
    # Delete session_b's runtime file out from under the manifest.
    route_b = AtlasDBRouter().runtime_route(session_b, create=False)
    for suffix in ("", "-wal", "-shm"):
        p = route_b.runtime_db_path + suffix
        if os.path.exists(p):
            os.remove(p)

    plans = {p.session_id: p for p in runtime_rollup.recover_all_sessions()}
    assert plans[session_a].status == "ok"
    assert plans[session_b].status == "missing"
    assert plans[session_b].resume_cursor is None


def test_jobs_loss_policy_documented():
    assert isinstance(runtime_rollup.JOBS_LOSS_POLICY, str)
    assert "runtime" in runtime_rollup.JOBS_LOSS_POLICY.lower()


# ──────────────────────────────────────────────────────────────────────────
# 3. idempotent forced rollback (R18)
# ──────────────────────────────────────────────────────────────────────────


def test_rollback_run_twice_copies_one_row(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    prompt_id = _enqueue(runtime_path, session_id, "in", "prompt", {"text": "rollback me"})

    # First rollback: copies the undelivered prompt into control.
    r1 = runtime_rollup.rollback_session_to_central(
        session_id, require_workers_stopped=False
    )
    assert r1.copied_rows == 1
    assert r1.skipped_existing == 0

    # Second rollback: INSERT OR IGNORE on the same id => nothing new.
    r2 = runtime_rollup.rollback_session_to_central(
        session_id, require_workers_stopped=False
    )
    assert r2.copied_rows == 0
    assert r2.skipped_existing == 1

    # Exactly ONE control-DB copy of the prompt, preserving the original id+text.
    with AtlasDB(control_path, schema_set="full") as cdb:
        rows = cdb._fetchall(
            "SELECT id, msg_type, payload FROM session_queue WHERE session_id = ?",
            (session_id,),
        )
    assert len(rows) == 1
    assert rows[0]["id"] == prompt_id
    assert "rollback me" in (rows[0]["payload"] or "")

    # Two audit rows (one per rollback run).
    with AtlasDB(control_path, schema_set="full") as cdb:
        audit = cdb.list_runtime_db_audit(session_id=session_id, action="rollback")
    assert len(audit) == 2


def test_rollback_only_undelivered(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    keep_id = _enqueue(runtime_path, session_id, "in", "prompt", {"text": "keep"})
    done_id = _enqueue(runtime_path, session_id, "out", "token", {"text": "done"})
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.mark_outputs_delivered(session_id, done_id, "out")

    r = runtime_rollup.rollback_session_to_central(
        session_id, require_workers_stopped=False
    )
    # Only the undelivered in-row is copied; the delivered out-row is left behind.
    assert r.copied_rows == 1
    with AtlasDB(control_path, schema_set="full") as cdb:
        ids = [row["id"] for row in cdb._fetchall(
            "SELECT id FROM session_queue WHERE session_id = ?", (session_id,)
        )]
    assert ids == [keep_id]


def test_rollback_history_policy_documented():
    assert isinstance(runtime_rollup.ROLLBACK_HISTORY_POLICY, str)
    assert "orphan" in runtime_rollup.ROLLBACK_HISTORY_POLICY.lower()


# ──────────────────────────────────────────────────────────────────────────
# 4. fleet health / audit JSON (R25)
# ──────────────────────────────────────────────────────────────────────────


def _assert_health_shape(report):
    for key in (
        "mode", "sessions", "manifest_count", "on_disk_file_count",
        "orphan_file_count", "total_runtime_bytes", "total_undelivered",
        "total_unprocessed", "oldest_undelivered_age_s", "max_rollup_lag_s",
        "open_init_failures", "locked_retry_count", "rollback_allowed",
    ):
        assert key in report, f"missing health key: {key}"
    assert isinstance(report["sessions"], list)
    assert isinstance(report["rollback_allowed"], bool)


def test_fleet_health_shape_and_rollback_allowed_true(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    # Delivered out-row => not in-flight => rollback allowed.
    out_id = _enqueue(runtime_path, session_id, "out", "token", {"text": "x"})
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.mark_outputs_delivered(session_id, out_id, "out")

    report = runtime_rollup.fleet_health()
    _assert_health_shape(report)
    assert report["mode"] == "session"
    assert report["manifest_count"] == 1
    assert report["on_disk_file_count"] == 1
    assert report["total_undelivered"] == 0
    assert report["rollback_allowed"] is True


def test_fleet_health_rollback_blocked_when_undelivered(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _enqueue(runtime_path, session_id, "out", "token", {"text": "buffered"})

    report = runtime_rollup.fleet_health()
    assert report["total_undelivered"] == 1
    assert report["rollback_allowed"] is False
    sess = report["sessions"][0]
    assert sess["undelivered"] == 1
    assert sess["oldest_undelivered_age_s"] >= 0.0


def test_fleet_health_counts_orphan_files(split_env):
    control_path, root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    _seed_session(control_path, session_id)
    # Drop an extra .db under the root with NO manifest row -> orphan.
    orphan_dir = Path(root) / "zz"
    orphan_dir.mkdir(parents=True, exist_ok=True)
    (orphan_dir / "deadbeef.db").write_bytes(b"")

    report = runtime_rollup.fleet_health()
    assert report["orphan_file_count"] >= 1


def test_fleet_health_locked_retry_counter_wired(split_env):
    control_path, _root = split_env
    mgr = SessionProcessManager(db_path=control_path)
    # Simulate a locked retry having occurred.
    with mgr._metrics_lock:
        mgr._locked_retry_count = 3
    report = runtime_rollup.fleet_health(process_manager=mgr)
    assert report["locked_retry_count"] == 3
