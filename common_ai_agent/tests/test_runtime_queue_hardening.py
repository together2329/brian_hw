"""Wave 2 / Task 4 — runtime-queue hardening.

Covers the five Task-4 hardening sub-goals (plan §2.3/§2.4/§2.5/§2.12,
R4/R5/R22/R13):

1. worker runtime schema subset (no control tables in the runtime file);
2. runtime queue PLACEMENT — two sessions' in/out rows land ONLY in their own
   runtime files; the control DB holds 0 session_queue rows;
3. exactly-once delivery on spawn-then-retry (R4) — byte-identical path, one row;
4. non-silent absent-cursor + atomic re-seed with no duplicate delivery (R5);
5. cleanup excludes undelivered/unprocessed rows (R22).

These are pure-Python / direct-DB tests (no real subprocess) so they are fast
and deterministic. The real-subprocess co-location check lives in Task 10.
"""

from __future__ import annotations

import importlib
import sqlite3
import sys
from pathlib import Path

import pytest

PROJECT_ROOT = Path(__file__).resolve().parents[1]
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))
if str(PROJECT_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT / "src"))

from core.atlas_db import AtlasDB, QueueCursorNotFound
from core.atlas_db_router import AtlasDBRouter
from core.session_process_manager import SessionProcessManager


# ──────────────────────────────────────────────────────────────────────────
# helpers
# ──────────────────────────────────────────────────────────────────────────

def _runtime_env(monkeypatch, tmp_path):
    """Pin a session-mode router via env (control db + runtime root + mode)."""
    control_db = tmp_path / "control.db"
    runtime_root = tmp_path / "runtime"
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", str(control_db))
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", str(runtime_root))
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    monkeypatch.delenv("ATLAS_DB_PATH", raising=False)
    monkeypatch.setenv("ATLAS_SESSION_WORKER_PRUNE_ORPHANS", "0")
    return control_db, runtime_root


def _table_names(db_path) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(
            "SELECT name FROM sqlite_master WHERE type='table'"
        ).fetchall()
    finally:
        conn.close()
    return {r[0] for r in rows}


def _queue_rows(db_path, session_id=None, direction=None):
    conn = sqlite3.connect(db_path)
    conn.row_factory = sqlite3.Row
    try:
        sql = "SELECT id, session_id, direction, msg_type FROM session_queue"
        clauses, params = [], []
        if session_id is not None:
            clauses.append("session_id = ?")
            params.append(session_id)
        if direction is not None:
            clauses.append("direction = ?")
            params.append(direction)
        if clauses:
            sql += " WHERE " + " AND ".join(clauses)
        sql += " ORDER BY created_at ASC, rowid ASC"
        rows = conn.execute(sql, tuple(params)).fetchall()
    finally:
        conn.close()
    return [dict(r) for r in rows]


# ──────────────────────────────────────────────────────────────────────────
# 5. worker uses the runtime 5-table schema (no control tables)
# ──────────────────────────────────────────────────────────────────────────

def test_worker_opens_runtime_subset_schema_in_session_mode(monkeypatch, tmp_path):
    """In session mode the worker's queue DB must NOT contain control tables."""
    from core import session_worker

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    runtime_path = tmp_path / "wkr_runtime.db"
    monkeypatch.setenv("ATLAS_RUNTIME_DB_PATH", str(runtime_path))

    worker = session_worker.SessionWorker(
        session_id="alice/ip_a/rtl-gen", db_path=str(runtime_path)
    )
    try:
        assert worker._schema_set == "runtime"
        # The worker can still read/write the 5 IPC/trace tables.
        out_id = worker.db.enqueue_message(
            "alice/ip_a/rtl-gen", "out", "token", {"text": "x"}
        )
        assert out_id
        assert worker.db.poll_messages("alice/ip_a/rtl-gen", "out")
    finally:
        worker.close()

    tables = _table_names(runtime_path)
    # The 5-table runtime subset is present...
    for expected in {"session_queue", "messages", "parts", "trace_events", "llm_calls"}:
        assert expected in tables, f"missing runtime table {expected}"
    # ...and NO control-plane table leaked into the runtime file.
    for control_table in {"users", "workspaces", "ip_blocks", "workflow_runs", "sessions"}:
        assert control_table not in tables, (
            f"control table {control_table!r} must not exist in the runtime DB"
        )


def test_worker_uses_full_schema_in_central_mode(monkeypatch, tmp_path):
    """Without session mode the worker keeps the historical full schema."""
    from core import session_worker

    monkeypatch.delenv("ATLAS_RUNTIME_DB_MODE", raising=False)
    monkeypatch.delenv("ATLAS_RUNTIME_DB_PATH", raising=False)
    db_path = tmp_path / "central.db"

    worker = session_worker.SessionWorker(
        session_id="alice/ip_a/rtl-gen", db_path=str(db_path)
    )
    try:
        assert worker._schema_set == "full"
    finally:
        worker.close()
    tables = _table_names(db_path)
    assert "users" in tables  # control table present in full schema


def test_worker_full_schema_when_runtime_equals_control(monkeypatch, tmp_path):
    """CENTRAL mode env: build_worker_env sets ATLAS_RUNTIME_DB_PATH ==
    ATLAS_CONTROL_DB_PATH. The worker must NOT pick the runtime subset for the
    control DB (a non-empty runtime path alone must not imply session mode).
    """
    from core import session_worker

    db_path = tmp_path / "central_equal.db"
    monkeypatch.delenv("ATLAS_RUNTIME_DB_MODE", raising=False)
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", str(db_path))
    monkeypatch.setenv("ATLAS_RUNTIME_DB_PATH", str(db_path))  # equal => central

    assert session_worker._runtime_db_mode() is False
    worker = session_worker.SessionWorker(
        session_id="alice/ip_a/rtl-gen", db_path=str(db_path)
    )
    try:
        assert worker._schema_set == "full"
    finally:
        worker.close()
    assert "users" in _table_names(db_path)


# ──────────────────────────────────────────────────────────────────────────
# runtime queue PLACEMENT: each runtime file holds ONLY its own rows
# ──────────────────────────────────────────────────────────────────────────

def test_two_sessions_queue_rows_isolated_control_empty(monkeypatch, tmp_path):
    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    manager = SessionProcessManager(project_root=str(tmp_path))
    monkeypatch.setattr(manager, "is_alive", lambda session_id: True)

    sess_a = "alice/ip_a/rtl-gen"
    sess_b = "bob/ip_b/rtl-gen"

    a_path = manager._resolve_runtime_db_path(sess_a, create=True)
    b_path = manager._resolve_runtime_db_path(sess_b, create=True)
    assert a_path != b_path

    # Each session enqueues an inbound prompt...
    a_in = manager.send_input(sess_a, "prompt", {"text": "hi A"})
    b_in = manager.send_input(sess_b, "prompt", {"text": "hi B"})
    assert a_in and b_in

    # ...and emits an outbound row into its own runtime file.
    a_db = AtlasDB(a_path, schema_set="runtime")
    a_out = a_db.enqueue_message(sess_a, "out", "token", {"text": "out A"})
    b_db = AtlasDB(b_path, schema_set="runtime")
    b_out = b_db.enqueue_message(sess_b, "out", "token", {"text": "out B"})

    # A's runtime file holds ONLY A's rows (1 in + 1 out), no B rows.
    a_rows = _queue_rows(a_path)
    assert {r["id"] for r in a_rows} == {a_in, a_out}
    assert all(r["session_id"] == sess_a for r in a_rows)

    b_rows = _queue_rows(b_path)
    assert {r["id"] for r in b_rows} == {b_in, b_out}
    assert all(r["session_id"] == sess_b for r in b_rows)

    # The CONTROL DB has 0 session_queue rows at all.
    control_path = str(Path(control_db).resolve())
    assert _queue_rows(control_path) == []

    manager.stop_all()


# ──────────────────────────────────────────────────────────────────────────
# 3. exactly-once on spawn-then-retry (R4)
# ──────────────────────────────────────────────────────────────────────────

def test_spawn_retry_delivers_prompt_exactly_once(monkeypatch, tmp_path):
    """Spawn fails once, retry succeeds -> prompt in EXACTLY one file, once."""
    import core.atlas_multiuser as atlas_multiuser

    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    monkeypatch.setenv("ATLAS_PROJECT_ROOT", str(tmp_path))

    bridge = atlas_multiuser._MultiUserBridge(use_processes=True)
    real_manager = SessionProcessManager(project_root=str(tmp_path))
    bridge._process_manager = real_manager

    session_id = "alice/ip_a/rtl-gen"

    # The runtime path the router derives must be byte-identical across calls
    # (manifest fast-path + resolve-or-mint-once, R4).
    path1 = real_manager._resolve_runtime_db_path(session_id, create=True)
    path2 = real_manager._resolve_runtime_db_path(session_id, create=True)
    assert path1 == path2

    # First spawn "fails" (worker not alive); the second succeeds.
    alive_state = {"alive": False}
    spawn_calls = {"n": 0}

    def fake_spawn(sid, db_path=None):
        spawn_calls["n"] += 1
        # First spawn leaves the worker dead; the retry brings it alive.
        if spawn_calls["n"] >= 2:
            alive_state["alive"] = True
        return True

    monkeypatch.setattr(real_manager, "spawn", fake_spawn)
    monkeypatch.setattr(
        real_manager, "is_alive", lambda sid: alive_state["alive"]
    )

    delivered = bridge.submit_prompt_for_session(session_id, "exactly once please")
    assert delivered is True

    # The prompt landed in the runtime file EXACTLY ONCE...
    runtime_in = _queue_rows(path1, session_id=session_id, direction="in")
    assert len(runtime_in) == 1, runtime_in
    assert runtime_in[0]["msg_type"] == "prompt"

    # ...and NOT in the control DB (no cross-DB duplicate / split-brain).
    control_path = str(Path(control_db).resolve())
    assert _queue_rows(control_path, session_id=session_id) == []

    # The manifest row + initialized runtime DB exist (init-before-accept, R4).
    control = AtlasDB(control_path, schema_set="full")
    manifest = control.get_session_runtime_db(session_id)
    assert manifest is not None
    assert manifest["session_uid"]
    assert "session_queue" in _table_names(path1)

    real_manager.stop_all()


def test_runtime_db_not_initialized_is_recoverable_not_silent_none(monkeypatch, tmp_path):
    """No resolvable uid -> router fails CLOSED (raises), never a silent None."""
    _runtime_env(monkeypatch, tmp_path)
    monkeypatch.delenv("ATLAS_RUNTIME_DB_ALLOW_DERIVED_KEY", raising=False)
    router = AtlasDBRouter()
    # An empty session id with no uid + derived-key disabled must FAIL CLOSED.
    from core.atlas_db_router import RuntimeDBError

    with pytest.raises(RuntimeDBError):
        router.runtime_route("", create=False)


# ──────────────────────────────────────────────────────────────────────────
# 4. absent-cursor non-silent + no duplicate (R5)
# ──────────────────────────────────────────────────────────────────────────

def test_poll_messages_absent_cursor_raises_when_requested(tmp_path):
    db = AtlasDB(str(tmp_path / "abs.db"), schema_set="runtime")
    db.enqueue_message("s1", "out", "token", {"i": 0})
    # default contract = silent empty (backward compat)
    assert db.poll_messages("s1", "out", since_id="nope") == []
    # opt-in non-silent signal
    with pytest.raises(QueueCursorNotFound) as ei:
        db.poll_messages("s1", "out", since_id="nope", on_absent_cursor="raise")
    assert ei.value.session_id == "s1"
    assert ei.value.direction == "out"
    assert ei.value.since_id == "nope"


def test_reseed_output_cursor_resumes_without_redelivery(tmp_path):
    db = AtlasDB(str(tmp_path / "reseed.db"), schema_set="runtime")
    a = db.enqueue_message("s1", "out", "token", {"i": 0})
    b = db.enqueue_message("s1", "out", "token", {"i": 1})
    db.enqueue_message("s1", "out", "token", {"i": 2})

    # Deliver the first two rows (mark delivered_at).
    db.acknowledge_message(a)
    db.acknowledge_message(b)

    # Re-seed -> newest already-delivered row (b). A poll from there returns
    # only the still-undelivered tail (i=2), never re-delivering a/b.
    cursor = db.reseed_output_cursor("s1", "out")
    assert cursor == b
    tail = db.poll_messages("s1", "out", since_id=cursor)
    assert [r["payload"]["i"] for r in tail] == [2]

    # Nothing delivered yet on a fresh queue -> re-seed is None (poll from top).
    fresh = AtlasDB(str(tmp_path / "reseed_fresh.db"), schema_set="runtime")
    fresh.enqueue_message("s2", "out", "token", {"i": 9})
    assert fresh.reseed_output_cursor("s2", "out") is None


def test_recreated_runtime_db_midstream_no_stall_no_duplicate(monkeypatch, tmp_path):
    """Delete/recreate a runtime DB mid-stream: re-seed, no stall, no dupes."""
    import core.atlas_multiuser as atlas_multiuser

    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    bridge = atlas_multiuser._MultiUserBridge(use_processes=True)
    manager = SessionProcessManager(project_root=str(tmp_path))
    bridge._process_manager = manager

    session_id = "alice/ip_a/rtl-gen"
    runtime_path = manager._resolve_runtime_db_path(session_id, create=True)

    # Make the session "active" so the poll loop visits it.
    monkeypatch.setattr(manager, "list_active", lambda: [session_id])

    # Seed two output rows and run one poll pass -> both delivered to the outbox.
    rt = AtlasDB(runtime_path, schema_set="runtime")
    o1 = rt.enqueue_message(session_id, "out", "token", {"i": 0})
    o2 = rt.enqueue_message(session_id, "out", "token", {"i": 1})
    bridge._poll_process_outputs()

    session = bridge.get_session(session_id)
    drained_first = _drain_outbox(session)
    got_first = [e.get("i") for e in drained_first if e.get("type") == "token"]
    assert got_first == [0, 1]
    # The in-memory cursor now points at o2.
    assert bridge._process_output_cursors.get(session_id) == o2

    # Mid-stream: the runtime DB is recreated (cursor o2 no longer exists), with
    # the OLD output rows re-materialized (already delivered) + a NEW row o3.
    # Close the test's own handle + the manager's cached handle so neither keeps
    # a thread-local connection open to the about-to-be-unlinked inode.
    rt.close()
    manager._evict_db_handles(session_id)
    for suffix in ("", "-wal", "-shm"):
        p = Path(str(runtime_path) + suffix)
        if p.exists():
            p.unlink()
    # The process-wide one-time-init guard still thinks this path is bootstrapped
    # (it was, before we unlinked it). A genuine recreate must rebuild the schema,
    # so drop the guard entry for this (path, schema_set) — modelling a brand-new
    # file open after the inode was swapped.
    AtlasDB._INITIALIZED_PATHS.discard(
        (str(Path(runtime_path)), "runtime")
    )
    AtlasDB._INITIALIZED_PATHS.discard((runtime_path, "runtime"))
    rt2 = AtlasDB(runtime_path, schema_set="runtime")
    # Re-add the two prior rows AS ALREADY DELIVERED so a naive top-restart
    # would re-deliver them. Then a brand-new undelivered row o3.
    rt2.enqueue_message(session_id, "out", "token", {"i": 0})
    rt2.acknowledge_message(_last_out_id(rt2, session_id))
    rt2.enqueue_message(session_id, "out", "token", {"i": 1})
    rt2.acknowledge_message(_last_out_id(rt2, session_id))
    rt2.enqueue_message(session_id, "out", "token", {"i": 2})

    # Poll again: the absent cursor must be a non-silent re-seed (NOT a stall,
    # NOT a top-restart), delivering ONLY the new undelivered row o3 (i=2).
    bridge._poll_process_outputs()
    drained_second = _drain_outbox(session)
    tokens_second = [e.get("i") for e in drained_second if e.get("type") == "token"]
    assert tokens_second == [2], tokens_second  # no stall (got a row), no dupes

    # A non-silent recovery signal was emitted (never silent).
    assert any(
        e.get("type") == "runtime_db_recreated" for e in drained_second
    ), [e.get("type") for e in drained_second]

    manager.stop_all()


def _drain_outbox(session):
    import queue as _queue
    out = []
    while True:
        try:
            out.append(session._outbox.get_nowait())
        except _queue.Empty:
            break
    return out


def _last_out_id(db, session_id):
    row = db._fetchone(
        "SELECT id FROM session_queue WHERE session_id=? AND direction='out' "
        "ORDER BY created_at DESC, rowid DESC LIMIT 1",
        (session_id,),
    )
    return row["id"]


def _delivered_at(db, msg_id):
    row = db._fetchone(
        "SELECT delivered_at FROM session_queue WHERE id = ?", (msg_id,)
    )
    return row["delivered_at"] if row is not None else None


# ──────────────────────────────────────────────────────────────────────────
# Task-4 delivery-marker fix: broadcaster marks polled out-rows delivered
# DURABLY (batched, not per-token), so reseed has a resume point and cleanup
# can purge them (plan §2.4/§2.12 / R5/R22).
# ──────────────────────────────────────────────────────────────────────────

def test_broadcaster_delivery_marks_out_rows_delivered(monkeypatch, tmp_path):
    """After a poll batch is pushed to the outbox, those out-rows carry a
    durable delivered_at; rows enqueued AFTER the batch stay undelivered."""
    import core.atlas_multiuser as atlas_multiuser

    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    bridge = atlas_multiuser._MultiUserBridge(use_processes=True)
    manager = SessionProcessManager(project_root=str(tmp_path))
    bridge._process_manager = manager

    session_id = "alice/ip_a/rtl-gen"
    runtime_path = manager._resolve_runtime_db_path(session_id, create=True)
    monkeypatch.setattr(manager, "list_active", lambda: [session_id])

    rt = AtlasDB(runtime_path, schema_set="runtime")
    o1 = rt.enqueue_message(session_id, "out", "token", {"i": 0})
    o2 = rt.enqueue_message(session_id, "out", "token", {"i": 1})

    bridge._poll_process_outputs()

    # The two polled rows now carry a durable delivered_at marker.
    assert _delivered_at(rt, o1) is not None
    assert _delivered_at(rt, o2) is not None

    # A later out-row not yet polled/delivered stays undelivered.
    o3 = rt.enqueue_message(session_id, "out", "token", {"i": 2})
    assert _delivered_at(rt, o3) is None

    # poll_messages (delivered_at IS NULL) now only returns the new tail.
    pending = rt.poll_messages(session_id, "out")
    assert [r["payload"]["i"] for r in pending] == [2]

    manager.stop_all()


def test_reseed_resumes_from_newest_delivered_after_real_delivery(monkeypatch, tmp_path):
    """A real broadcaster delivery gives reseed a true resume point: re-seed
    returns the newest-delivered id and a poll from there delivers ONLY the
    still-undelivered tail (no re-delivery of already-pushed rows, no stall)."""
    import core.atlas_multiuser as atlas_multiuser

    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    bridge = atlas_multiuser._MultiUserBridge(use_processes=True)
    manager = SessionProcessManager(project_root=str(tmp_path))
    bridge._process_manager = manager

    session_id = "alice/ip_a/rtl-gen"
    runtime_path = manager._resolve_runtime_db_path(session_id, create=True)
    monkeypatch.setattr(manager, "list_active", lambda: [session_id])

    rt = AtlasDB(runtime_path, schema_set="runtime")
    rt.enqueue_message(session_id, "out", "token", {"i": 0})
    o2 = rt.enqueue_message(session_id, "out", "token", {"i": 1})

    bridge._poll_process_outputs()  # delivers o1, o2 durably

    # Reseed now returns the newest-delivered row (o2), NOT None (no stall).
    cursor = manager.reseed_output_cursor(session_id)
    assert cursor == o2

    # A new undelivered row arrives; a poll from the reseed cursor returns ONLY
    # the new tail — the already-pushed o1/o2 are not re-delivered.
    o3 = rt.enqueue_message(session_id, "out", "token", {"i": 2})
    tail = rt.poll_messages(session_id, "out", since_id=cursor)
    assert [r["payload"]["i"] for r in tail] == [2]
    assert tail[0]["id"] == o3

    manager.stop_all()


def test_cleanup_purges_old_delivered_out_rows_keeps_undelivered(monkeypatch, tmp_path):
    """After a real delivery, cleanup_old_messages purges OLD DELIVERED out-rows
    (runtime DB bounded) but KEEPS old UNDELIVERED out-rows (R22)."""
    import core.atlas_multiuser as atlas_multiuser

    control_db, runtime_root = _runtime_env(monkeypatch, tmp_path)
    bridge = atlas_multiuser._MultiUserBridge(use_processes=True)
    manager = SessionProcessManager(project_root=str(tmp_path))
    bridge._process_manager = manager

    session_id = "alice/ip_a/rtl-gen"
    runtime_path = manager._resolve_runtime_db_path(session_id, create=True)
    monkeypatch.setattr(manager, "list_active", lambda: [session_id])

    rt = AtlasDB(runtime_path, schema_set="runtime")
    o1 = rt.enqueue_message(session_id, "out", "token", {"i": 0})
    o2 = rt.enqueue_message(session_id, "out", "token", {"i": 1})

    bridge._poll_process_outputs()  # delivers o1, o2 durably
    assert _delivered_at(rt, o1) is not None
    assert _delivered_at(rt, o2) is not None

    # A later out-row that has NOT been delivered (e.g. produced after the poll
    # and never pushed) must survive the age purge.
    o3 = rt.enqueue_message(session_id, "out", "token", {"i": 2})
    assert _delivered_at(rt, o3) is None

    # Age every row past the cutoff, then purge.
    conn = rt._connect()
    conn.execute("UPDATE session_queue SET created_at = ?", (1.0,))
    conn.commit()

    deleted = rt.cleanup_old_messages(age_seconds=1.0)

    # The old DELIVERED out-rows are purged; the old UNDELIVERED one survives.
    assert rt.get_message(o1) is None
    assert rt.get_message(o2) is None
    assert rt.get_message(o3) is not None
    assert deleted == 2

    manager.stop_all()


# ──────────────────────────────────────────────────────────────────────────
# 2. cleanup excludes undelivered (R22)
# ──────────────────────────────────────────────────────────────────────────

def test_cleanup_keeps_old_undelivered_prompt_purges_delivered(tmp_path):
    db = AtlasDB(str(tmp_path / "cleanup.db"), schema_set="runtime")

    # An OLD inbound prompt, never delivered AND never processed: waiting for a
    # cold worker. cleanup_old_messages MUST NOT purge it (R22).
    old_undelivered = db.enqueue_message("s1", "in", "prompt", {"text": "cold"})
    # An OLD delivered out-row: safe to purge.
    old_delivered = db.enqueue_message("s1", "out", "token", {"text": "shown"})
    # An OLD processed in-row (consumed by the worker): safe to purge.
    old_processed = db.enqueue_message("s1", "in", "prompt", {"text": "done"})

    # Set delivered/processed markers explicitly, then age every row.
    conn = db._connect()
    conn.execute(
        "UPDATE session_queue SET delivered_at=? WHERE id=?", (1.0, old_delivered)
    )
    conn.execute(
        "UPDATE session_queue SET processed_at=? WHERE id=?", (1.0, old_processed)
    )
    conn.execute("UPDATE session_queue SET created_at=?", (1.0,))
    conn.commit()

    deleted = db.cleanup_old_messages(age_seconds=1.0)

    surviving = {r["id"] for r in _queue_rows_from_conn(conn)}
    # The old-but-undelivered prompt SURVIVES.
    assert old_undelivered in surviving
    # The old delivered + old processed rows are purged.
    assert old_delivered not in surviving
    assert old_processed not in surviving
    assert deleted == 2


def test_cleanup_purges_expired_regardless_of_delivery(tmp_path):
    db = AtlasDB(str(tmp_path / "expire.db"), schema_set="runtime")
    # An expired row (explicit TTL) is purged even if undelivered: TTL is an
    # enqueuer choice, not the age heuristic.
    expired = db.enqueue_message(
        "s1", "out", "token", {"text": "ttl"}, expires_at=1.0
    )
    conn = db._connect()
    conn.execute("UPDATE session_queue SET created_at=? WHERE id=?", (1.0, expired))
    conn.commit()
    db.cleanup_old_messages(age_seconds=10_000_000_000)  # age branch won't fire
    assert db.get_message(expired) is None


def _queue_rows_from_conn(conn):
    conn.row_factory = sqlite3.Row
    return [dict(r) for r in conn.execute("SELECT * FROM session_queue").fetchall()]


# ──────────────────────────────────────────────────────────────────────────
# 1/5. recovery contract: missing -> recreate+signal; corrupt -> quarantine+error
# ──────────────────────────────────────────────────────────────────────────

def test_missing_runtime_db_recreated_with_nonsilent_signal(monkeypatch, tmp_path):
    _runtime_env(monkeypatch, tmp_path)
    manager = SessionProcessManager(project_root=str(tmp_path))
    session_id = "alice/ip_a/rtl-gen"
    runtime_path = Path(manager._resolve_runtime_db_path(session_id, create=True))

    # No file yet -> first open recreates + records a non-silent recreate event.
    assert not runtime_path.exists()
    db = manager._get_runtime_db(session_id)
    assert runtime_path.exists()
    assert "session_queue" in _table_names(runtime_path)
    events = [e["event"] for e in manager.runtime_recovery_events()]
    assert "runtime_db_recreated" in events
    _ = db
    manager.stop_all()


def test_corrupt_runtime_db_is_quarantined_and_surfaced(monkeypatch, tmp_path):
    _runtime_env(monkeypatch, tmp_path)
    manager = SessionProcessManager(project_root=str(tmp_path))
    session_id = "alice/ip_a/rtl-gen"
    runtime_path = Path(manager._resolve_runtime_db_path(session_id, create=True))

    # Write garbage so SQLite rejects it as a database.
    runtime_path.parent.mkdir(parents=True, exist_ok=True)
    runtime_path.write_bytes(b"this is not a sqlite database file at all" * 8)

    with pytest.raises(RuntimeError) as ei:
        manager._get_runtime_db(session_id)
    assert "corrupt" in str(ei.value).lower()

    # The corrupt file was quarantined aside (renamed), not left in place.
    quarantined = list(runtime_path.parent.glob(f"{runtime_path.name}.corrupt-*"))
    assert quarantined, "corrupt runtime file should be quarantined"

    # The control manifest row was flipped to status='error' (non-silent).
    control = manager._get_db()
    manifest = control.get_session_runtime_db(session_id)
    assert manifest is not None
    assert manifest["status"] == "error"

    events = [e["event"] for e in manager.runtime_recovery_events()]
    assert "runtime_db_error" in events
    manager.stop_all()
