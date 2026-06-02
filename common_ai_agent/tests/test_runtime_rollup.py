"""Task 7 — control-DB usage rollups for per-session runtime DBs.

Covers plan §2.10 + R1 + R8 for the rollup write side and the read side that
consumes it:

1. IDEMPOTENT: seed a runtime DB with 3 llm_calls + 4 trace_events; run the
   rollup TWICE -> control rollup counts stay 3 and 4 (NOT 6/8). High-water is
   the monotonic SQLite rowid, so the second run sees no new rows.
2. STALE runtime DB: two sessions; delete one runtime file; run
   rollup_all_active -> the existing session rolls up, the missing one is marked
   stale, and the command SUCCEEDS (no raise, no deleted raw rows).
3. TOTALS PARITY: control rollup totals == sum of raw runtime rows.
4. READS USE ROLLUPS: admin usage / dashboard totals come from rollup rows, and
   NO runtime file is opened during the read (router.runtime_db / sqlite.connect
   are instrumented and asserted not-called on runtime paths).
5. CENTRAL MODE unchanged: the rollup read path is inert; admin/dashboard read
   the control DB exactly as today.

The tests pin the rollup CONTRACT directly against AtlasDB / AtlasDBRouter /
runtime_rollup, so they are fast and need no live UI or real subprocess.
"""

from __future__ import annotations

import sqlite3

import pytest

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter
from core import runtime_rollup


# --------------------------------------------------------------------------- #
# Fixtures / helpers
# --------------------------------------------------------------------------- #


@pytest.fixture
def split_env(tmp_path, monkeypatch):
    """Explicit control DB + runtime root in SESSION mode."""
    control_path = str(tmp_path / "atlas.db")
    runtime_root = str(tmp_path / "runtime")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_ROOT", runtime_root)
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "session")
    AtlasDB(control_path, schema_set="full").close()
    return control_path, runtime_root


def _seed_session(control_path: str, session_id: str, user_id: str = "u-test") -> str:
    """Create a control users + session row + manifest; return the runtime path.

    Inserts the ``users`` row directly with a FIXED id (create_user auto-mints
    its own) so the session's ``user_id`` matches a real user the admin/dashboard
    joins can resolve.
    """
    with AtlasDB(control_path, schema_set="full") as db:
        if db.find_session(session_id) is None and not db._fetchone(
            "SELECT 1 FROM users WHERE id = ?", (user_id,)
        ):
            db._execute(
                "INSERT OR IGNORE INTO users "
                "(id, username, display_name, role, created_at) "
                "VALUES (?, ?, ?, 'user', ?)",
                (user_id, user_id, user_id, db._now()),
            )
        db.upsert_runtime_session(
            session_id,
            user_id=user_id,
            ip_id="ip-test",
            workflow="rtl-gen",
            owner=user_id,
        )
    route = AtlasDBRouter().runtime_route(session_id, create=True)
    return route.runtime_db_path


def _seed_runtime_rows(
    runtime_path: str,
    session_id: str,
    *,
    n_llm: int = 3,
    n_trace: int = 4,
    tokens_in: int = 100,
    tokens_out: int = 20,
    cost: float = 0.5,
) -> None:
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        for _ in range(n_llm):
            rdb.record_llm_call(
                session_id=session_id,
                ip_id="ip-test",
                workflow="rtl-gen",
                model="claude-opus-4-7",
                call_role="worker",
                tokens_input=tokens_in,
                tokens_output=tokens_out,
                tokens_reasoning=5,
                cache_read_tokens=10,
                cache_write_tokens=2,
                cost_usd=cost,
            )
        for i in range(n_trace):
            rdb.record_trace_event(
                event_type="orchestrator_step",
                payload={"i": i},
                session_id=session_id,
            )


# --------------------------------------------------------------------------- #
# 1. Idempotent rollup
# --------------------------------------------------------------------------- #


def test_rollup_is_idempotent_across_runs(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=3, n_trace=4)

    router = AtlasDBRouter()

    r1 = runtime_rollup.rollup_session(session_id, router=router)
    assert r1.status == "ok"

    with AtlasDB(control_path, schema_set="full") as cdb:
        row1 = cdb.get_runtime_usage_rollup(session_id)
    assert row1["llm_calls"] == 3
    assert row1["trace_events"] == 4

    # Second run: no NEW rows beyond the stored rowid offset -> counts unchanged.
    r2 = runtime_rollup.rollup_session(session_id, router=router)
    assert r2.status == "ok"

    with AtlasDB(control_path, schema_set="full") as cdb:
        row2 = cdb.get_runtime_usage_rollup(session_id)
    assert row2["llm_calls"] == 3, "idempotent: must NOT become 6"
    assert row2["trace_events"] == 4, "idempotent: must NOT become 8"


def test_rollup_picks_up_only_new_rows(split_env):
    """After a first rollup, only rows beyond the high-water are added next run."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=2, n_trace=1)

    router = AtlasDBRouter()
    runtime_rollup.rollup_session(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.get_runtime_usage_rollup(session_id)["llm_calls"] == 2

    # Add 3 more llm_calls, then re-run: total must be 5 (2 old + 3 new), not 7.
    _seed_runtime_rows(runtime_path, session_id, n_llm=3, n_trace=0)
    runtime_rollup.rollup_session(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.get_runtime_usage_rollup(session_id)["llm_calls"] == 5


# --------------------------------------------------------------------------- #
# 2. Stale / missing runtime DB
# --------------------------------------------------------------------------- #


def test_rollup_all_active_marks_missing_stale_and_succeeds(split_env):
    import os

    control_path, _root = split_env
    sid_ok = "u-test/ip-test/rtl-gen"
    sid_missing = "u-test/ip-test/sim"
    path_ok = _seed_session(control_path, sid_ok)
    path_missing = _seed_session(control_path, sid_missing)
    _seed_runtime_rows(path_ok, sid_ok, n_llm=2, n_trace=2)
    _seed_runtime_rows(path_missing, sid_missing, n_llm=1, n_trace=1)

    # Delete one runtime file (+ its wal/shm) to simulate a missing DB.
    for suffix in ("", "-wal", "-shm"):
        try:
            os.remove(path_missing + suffix)
        except OSError:
            pass
    assert not os.path.exists(path_missing)

    # Must NOT raise even though one runtime file is gone.
    results = runtime_rollup.rollup_all_active(router=AtlasDBRouter())
    by_sid = {r.session_id: r for r in results}

    assert by_sid[sid_ok].status == "ok"
    assert by_sid[sid_missing].status == "stale"

    with AtlasDB(control_path, schema_set="full") as cdb:
        ok_row = cdb.get_runtime_usage_rollup(sid_ok)
        missing_row = cdb.get_runtime_usage_rollup(sid_missing)
        manifest_missing = cdb.get_session_runtime_db(sid_missing)
    assert ok_row["llm_calls"] == 2
    assert missing_row["status"] == "stale"
    assert missing_row["rollup_lag_s"] is not None
    assert manifest_missing["status"] == "stale"

    # The healthy runtime DB still has its raw rows (never deleted by rollup).
    with AtlasDB(path_ok, schema_set="runtime") as rdb:
        raw = rdb._fetchone("SELECT COUNT(*) AS n FROM llm_calls")
    assert int(dict(raw)["n"]) == 2


def test_rollup_corrupt_runtime_db_marks_error(split_env, monkeypatch):
    """A corrupt/unreadable runtime DB -> status='error', no raise, no data loss.

    SQLite corruption is impractical to simulate deterministically IN-PROCESS
    (the OS page cache + WAL recovery resurrect the valid DB). The contract the
    rollup must honor is: a DatabaseError raised while opening/reading the runtime
    file is caught, the rollup row + manifest are flipped to ``status='error'``,
    and rollup_session returns instead of raising. We inject that DatabaseError at
    the router open seam, which is exactly what a corrupt file produces in prod.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=1, n_trace=1)

    def _boom(self, *a, **k):
        raise sqlite3.DatabaseError("file is not a database")

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _boom)

    result = runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())
    assert result.status == "error"
    assert result.error

    monkeypatch.undo()

    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.get_runtime_usage_rollup(session_id)
        manifest = cdb.get_session_runtime_db(session_id)
    assert row["status"] == "error"
    assert manifest["status"] == "error"

    # Raw rows are untouched (rollup NEVER deletes runtime data).
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        raw = int(dict(rdb._fetchone("SELECT COUNT(*) AS n FROM llm_calls"))["n"])
    assert raw == 1


def test_rollup_all_active_does_not_raise_on_corrupt(split_env, monkeypatch):
    """One corrupt session must not abort rollup_all_active for the others."""
    control_path, _root = split_env
    sid_ok = "u-test/ip-test/rtl-gen"
    sid_bad = "u-test/ip-test/sim"
    path_ok = _seed_session(control_path, sid_ok)
    path_bad = _seed_session(control_path, sid_bad)
    _seed_runtime_rows(path_ok, sid_ok, n_llm=2, n_trace=1)
    # Give sid_bad an on-disk file so the rollup reaches the OPEN step (where the
    # injected DatabaseError fires) rather than the missing-file 'stale' branch.
    _seed_runtime_rows(path_bad, sid_bad, n_llm=1, n_trace=1)

    real_runtime_db = AtlasDBRouter.runtime_db

    def _maybe_boom(self, session_id, *a, **k):
        if session_id == sid_bad:
            raise sqlite3.DatabaseError("file is not a database")
        return real_runtime_db(self, session_id, *a, **k)

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _maybe_boom)

    # Must NOT raise.
    results = runtime_rollup.rollup_all_active(router=AtlasDBRouter())
    by_sid = {r.session_id: r for r in results}
    assert by_sid[sid_ok].status == "ok"
    assert by_sid[sid_bad].status == "error"


# --------------------------------------------------------------------------- #
# 3. Totals parity (rollup == raw)
# --------------------------------------------------------------------------- #


def test_rollup_totals_equal_raw_runtime_totals(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(
        runtime_path, session_id,
        n_llm=4, n_trace=3, tokens_in=111, tokens_out=22, cost=0.25,
    )

    runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())

    # Raw totals straight from the runtime file.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        raw = dict(rdb._fetchone(
            """
            SELECT COUNT(*) AS llm_calls,
                   COALESCE(SUM(tokens_input), 0) AS ti,
                   COALESCE(SUM(tokens_output), 0) AS to_,
                   COALESCE(SUM(tokens_reasoning), 0) AS tr,
                   COALESCE(SUM(cache_read_tokens), 0) AS cr,
                   COALESCE(SUM(cache_write_tokens), 0) AS cw,
                   COALESCE(SUM(cost_usd), 0) AS cost
              FROM llm_calls
            """
        ))
        raw_trace = int(dict(rdb._fetchone(
            "SELECT COUNT(*) AS n FROM trace_events"))["n"])

    with AtlasDB(control_path, schema_set="full") as cdb:
        roll = cdb.get_runtime_usage_rollup(session_id)

    assert roll["llm_calls"] == raw["llm_calls"]
    assert roll["tokens_input"] == raw["ti"]
    assert roll["tokens_output"] == raw["to_"]
    assert roll["tokens_reasoning"] == raw["tr"]
    assert roll["cache_read_tokens"] == raw["cr"]
    assert roll["cache_write_tokens"] == raw["cw"]
    assert abs(float(roll["cost_usd"]) - float(raw["cost"])) < 1e-9
    assert roll["trace_events"] == raw_trace


def test_rollup_queue_in_out_counts(split_env):
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.enqueue_message(session_id, "in", "prompt", {"text": "hi"})
        rdb.enqueue_message(session_id, "in", "prompt", {"text": "again"})
        rdb.enqueue_message(session_id, "out", "token", {"text": "ok"})

    runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())
    with AtlasDB(control_path, schema_set="full") as cdb:
        roll = cdb.get_runtime_usage_rollup(session_id)
    assert roll["queue_in"] == 2
    assert roll["queue_out"] == 1


# --------------------------------------------------------------------------- #
# 3b. Rowid-reuse: a drained-then-reused queue is recounted, not skipped (MEDIUM)
# --------------------------------------------------------------------------- #


def test_rollup_drained_queue_reuse_recounts_not_skipped(split_env):
    """session_queue drained mid-life (rowids reused) must NOT under-count.

    SQLite reuses rowids after DELETE when the table has no AUTOINCREMENT PK.
    cleanup_old_messages drains session_queue; new inserts then land at rowids
    <= the stored high-water offset. The rollup must detect MAX(rowid) < offset,
    recount the CURRENT queue rows absolutely, and reset the offset — so the new
    rows are reflected (not silently skipped) and not double-counted. Append-only
    llm_calls/tokens/cost must stay exact across the same sequence.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    router = AtlasDBRouter()

    # Seed N=5 queue rows (3 in / 2 out) + some append-only llm_calls.
    _seed_runtime_rows(runtime_path, session_id, n_llm=3, n_trace=0,
                       tokens_in=10, tokens_out=4, cost=0.2)
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 1})
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 2})
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 3})
        rdb.enqueue_message(session_id, "out", "token", {"t": 4})
        rdb.enqueue_message(session_id, "out", "token", {"t": 5})

    runtime_rollup.rollup_session(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        roll1 = cdb.get_runtime_usage_rollup(session_id)
        off1 = cdb.get_rollup_offset(session_id, "session_queue")
    assert roll1["queue_in"] == 3
    assert roll1["queue_out"] == 2
    assert off1 == 5, "high-water should be the 5th queue rowid"
    assert roll1["llm_calls"] == 3
    assert roll1["tokens_input"] == 30

    # Simulate cleanup: DELETE all queue rows, then insert M=2 NEW rows. SQLite
    # reuses rowids 1,2 (<= the stored offset 5) -> the plain ``rowid > 5`` slice
    # would skip them. The guard must recount.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb._execute("DELETE FROM session_queue")
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 6})
        rdb.enqueue_message(session_id, "out", "token", {"t": 7})
        reused = dict(rdb._fetchone(
            "SELECT COALESCE(MAX(rowid), 0) AS m FROM session_queue"))["m"]
    assert int(reused) <= off1, "rowids must have been REUSED below the offset"

    runtime_rollup.rollup_session(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        roll2 = cdb.get_runtime_usage_rollup(session_id)
        off2 = cdb.get_rollup_offset(session_id, "session_queue")
    # Current-window count of the M=2 live rows — NOT skipped (would stay 3/2),
    # NOT double-counted (would be 4/3 if added on top of the old totals).
    assert roll2["queue_in"] == 1, "recount: current live in-rows"
    assert roll2["queue_out"] == 1, "recount: current live out-rows"
    assert off2 == int(reused), "offset reset to the recounted high-water"
    # Append-only tables stay EXACT (strictly cumulative) across the sequence.
    assert roll2["llm_calls"] == 3
    assert roll2["tokens_input"] == 30
    assert abs(float(roll2["cost_usd"]) - 0.6) < 1e-9


def test_rollup_append_only_idempotent_after_queue_recount(split_env):
    """Re-running after a queue drain keeps append-only counts stable.

    The recount path only touches the drained table's columns; running the
    rollup twice with no further changes must not move llm_calls/trace_events
    (they remain at the high-water offset), and queue counts stay at the
    current-window recount.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    router = AtlasDBRouter()

    _seed_runtime_rows(runtime_path, session_id, n_llm=2, n_trace=3)
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 1})
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 2})
    runtime_rollup.rollup_session(session_id, router=router)

    # Drain + reuse, then roll up twice.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb._execute("DELETE FROM session_queue")
        rdb.enqueue_message(session_id, "in", "prompt", {"t": 3})
    runtime_rollup.rollup_session(session_id, router=router)
    runtime_rollup.rollup_session(session_id, router=router)

    with AtlasDB(control_path, schema_set="full") as cdb:
        roll = cdb.get_runtime_usage_rollup(session_id)
    # Append-only: run-twice keeps llm_calls/trace_events exact (idempotent).
    assert roll["llm_calls"] == 2
    assert roll["trace_events"] == 3
    # Queue: current-window recount of the single live row.
    assert roll["queue_in"] == 1
    assert roll["queue_out"] == 0


# --------------------------------------------------------------------------- #
# 3c. Atomic fold: counter-write + offset-advance are exactly-once (LOW#1)
# --------------------------------------------------------------------------- #


def test_rollup_fold_row_and_offset_consistent(split_env):
    """After a normal rollup, the rollup row and the offset rows agree.

    The counter write and the offset advance commit in ONE transaction
    (AtlasDB.fold_runtime_usage_rollup), so the per-table high-water equals the
    raw runtime MAX(rowid) and the counters equal the raw totals.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=4, n_trace=2)

    runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())

    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        max_llm = dict(rdb._fetchone(
            "SELECT COALESCE(MAX(rowid), 0) AS m FROM llm_calls"))["m"]
        max_trace = dict(rdb._fetchone(
            "SELECT COALESCE(MAX(rowid), 0) AS m FROM trace_events"))["m"]
    with AtlasDB(control_path, schema_set="full") as cdb:
        roll = cdb.get_runtime_usage_rollup(session_id)
        off_llm = cdb.get_rollup_offset(session_id, "llm_calls")
        off_trace = cdb.get_rollup_offset(session_id, "trace_events")

    assert roll["llm_calls"] == 4
    assert roll["trace_events"] == 2
    assert off_llm == int(max_llm), "offset must match folded llm_calls high-water"
    assert off_trace == int(max_trace), "offset must match folded trace high-water"


def test_rollup_fold_failure_does_not_double_count(split_env, monkeypatch):
    """A crash during the fold must not double-count on re-run.

    The counter write and the offset advance share ONE control-DB transaction:
    if the commit fails, BOTH are rolled back, so the next run re-reads the same
    slice and folds it exactly once. We simulate a failure by forcing the fold
    to raise, assert the rollup did NOT partially apply, then let the retry
    succeed and assert the final counts are exact (not doubled).
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=3, n_trace=1)

    router = AtlasDBRouter()

    # First attempt: force the atomic fold to raise (simulated crash). Since the
    # counter write + offset advance are one transaction, NOTHING is committed.
    real_fold = AtlasDB.fold_runtime_usage_rollup
    calls = {"n": 0}

    def _boom_once(self, *a, **k):
        calls["n"] += 1
        if calls["n"] == 1:
            raise RuntimeError("simulated crash mid-fold")
        return real_fold(self, *a, **k)

    monkeypatch.setattr(AtlasDB, "fold_runtime_usage_rollup", _boom_once)

    with pytest.raises(RuntimeError):
        runtime_rollup.rollup_session(session_id, router=router)

    # The transaction rolled back: no rollup row, no advanced offset.
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.get_runtime_usage_rollup(session_id) is None
        assert cdb.get_rollup_offset(session_id, "llm_calls") == 0

    # Retry: now the fold succeeds and the slice is folded EXACTLY ONCE.
    runtime_rollup.rollup_session(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        roll = cdb.get_runtime_usage_rollup(session_id)
    assert roll["llm_calls"] == 3, "exactly-once: not doubled after crash+retry"
    assert roll["trace_events"] == 1


# --------------------------------------------------------------------------- #
# 4. Reads use rollups — no runtime file opened on a normal request
# --------------------------------------------------------------------------- #


def test_admin_usage_totals_come_from_rollups_no_runtime_open(split_env, monkeypatch):
    from core import atlas_admin_usage

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=3, n_trace=2,
                       tokens_in=100, tokens_out=20, cost=0.4)
    runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())

    # Instrument: assert NO runtime file is opened during the read. We track any
    # sqlite3.connect to a path under the runtime root.
    opened_runtime: list[str] = []
    real_connect = sqlite3.connect

    def _spy_connect(path, *args, **kwargs):
        if isinstance(path, str) and "/runtime/" in path.replace("\\", "/"):
            opened_runtime.append(path)
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)

    # Also fail loudly if the router is asked to open a runtime DB.
    real_runtime_db = AtlasDBRouter.runtime_db

    def _no_runtime_db(self, *a, **k):
        raise AssertionError("read path opened a runtime DB via the router")

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _no_runtime_db)

    with AtlasDB(control_path, schema_set="full") as cdb:
        payload = atlas_admin_usage.build_admin_usage_payload(cdb)

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", real_runtime_db)

    assert payload["runtime_mode"] is True
    assert not opened_runtime, f"runtime file opened on read: {opened_runtime}"

    # Totals reflect the rollup, not an empty control llm_calls table.
    user = next(u for u in payload["users"] if str(u["user_id"]) == "u-test")
    assert user["message_count"] == 3
    assert user["tokens_in"] == 300
    assert abs(user["total_cost_usd"] - 1.2) < 1e-9

    # The summary-only marker is explicit (never a silently-empty tab).
    assert payload["tool_usage"] and payload["tool_usage"][0].get("__summary_only__") is True
    assert payload["interventions"][0].get("__summary_only__") is True
    assert payload["todo_flow"][0].get("__summary_only__") is True


def test_dashboard_totals_come_from_rollups_no_runtime_open(split_env, monkeypatch):
    from core import atlas_user_dashboard

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=2, n_trace=1,
                       tokens_in=50, tokens_out=10, cost=0.3)
    runtime_rollup.rollup_session(session_id, router=AtlasDBRouter())

    opened_runtime: list[str] = []
    real_connect = sqlite3.connect

    def _spy_connect(path, *args, **kwargs):
        if isinstance(path, str) and "/runtime/" in path.replace("\\", "/"):
            opened_runtime.append(path)
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)

    with AtlasDB(control_path, schema_set="full") as cdb:
        payload = atlas_user_dashboard.build_user_dashboard_payload(
            cdb, {"id": "u-test", "username": "tester", "role": "user"}
        )

    assert not opened_runtime, f"runtime file opened on read: {opened_runtime}"
    metrics = payload["metrics"]
    assert metrics["llm_calls"] == 2
    assert metrics["tokens_in"] == 100
    assert abs(metrics["total_cost_usd"] - 0.6) < 1e-9


# --------------------------------------------------------------------------- #
# 5. Central mode unchanged
# --------------------------------------------------------------------------- #


def test_central_mode_admin_usage_reads_control_db(tmp_path, monkeypatch):
    from core import atlas_admin_usage

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    control_path = str(tmp_path / "atlas.db")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)

    session_id = "u-test/ip-test/rtl-gen"
    with AtlasDB(control_path, schema_set="full") as db:
        user = db.create_user(username="tester", display_name="Tester", password_hash="x")
        uid = user["id"]
        db.upsert_runtime_session(
            session_id, user_id=uid, ip_id="ip-test", workflow="rtl-gen",
        )
        db.record_llm_call(
            session_id=session_id, ip_id="ip-test", workflow="rtl-gen",
            model="m", call_role="primary",
            tokens_input=10, tokens_output=2, cost_usd=0.1,
        )
        payload = atlas_admin_usage.build_admin_usage_payload(db)

    # Central mode: NOT summary-only; reads the control llm_calls directly.
    assert payload["runtime_mode"] is False
    assert isinstance(payload["tool_usage"], list)
    if payload["tool_usage"]:
        assert not payload["tool_usage"][0].get("__summary_only__")
    user_row = next(u for u in payload["users"] if str(u["user_id"]) == uid)
    assert user_row["message_count"] == 1


def test_central_mode_dashboard_reads_control_db(tmp_path, monkeypatch):
    from core import atlas_user_dashboard

    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    control_path = str(tmp_path / "atlas.db")
    monkeypatch.setenv("ATLAS_CONTROL_DB_PATH", control_path)

    session_id = "u-test/ip-test/rtl-gen"
    with AtlasDB(control_path, schema_set="full") as db:
        user = db.create_user(username="tester", display_name="Tester", password_hash="x")
        uid = user["id"]
        db.upsert_runtime_session(
            session_id, user_id=uid, ip_id="ip-test", workflow="rtl-gen",
        )
        db.record_llm_call(
            session_id=session_id, ip_id="ip-test", workflow="rtl-gen",
            model="m", call_role="primary",
            tokens_input=10, tokens_output=2, cost_usd=0.1,
        )
        payload = atlas_user_dashboard.build_user_dashboard_payload(
            db, {"id": uid, "username": "tester", "role": "user"}
        )
    assert payload["metrics"]["llm_calls"] == 1
    assert abs(payload["metrics"]["total_cost_usd"] - 0.1) < 1e-9
