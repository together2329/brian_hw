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
import time

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


# --------------------------------------------------------------------------- #
# Task 7 / RS-2: Session Flow fold (runtime flow rows -> control rollups)
# --------------------------------------------------------------------------- #


def _seed_flow_rows(
    runtime_path: str,
    session_id: str,
    *,
    n_inputs: int = 2,
    n_llm: int = 3,
    worker_status: str = "running",
    ip_id: str = "ip-test",
    workflow: str = "rtl-gen",
) -> None:
    """Seed runtime session_inputs / worker_runs / llm_calls / flow_events."""
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        for i in range(n_inputs):
            rdb.record_session_input(
                session_id=session_id, source="chat", source_ref_id=f"m{i}",
                char_count=10 * (i + 1), token_estimate=3 * (i + 1),
                user_id="u-test", ip_id=ip_id, workflow=workflow,
            )
        rdb.start_worker_run(
            session_id=session_id, ip_id=ip_id, workflow=workflow,
            worker_id="w1", status=worker_status,
        )
        for _ in range(n_llm):
            rdb.record_llm_call(
                session_id=session_id, ip_id=ip_id, workflow=workflow,
                model="m", call_role="worker",
                tokens_input=100, tokens_output=20, cost_usd=0.5, status="ok",
            )
        rdb.record_session_flow_event(
            event_type="worker_started", idempotency_key=f"{session_id}:ev1",
            session_id=session_id,
        )


def test_flow_runtime_db_can_record_three_tables(split_env):
    """(a) Runtime DB can record session_inputs/worker_runs/flow_events."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=1)
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        assert rdb._fetchone("SELECT COUNT(*) c FROM session_inputs")["c"] == 2
        assert rdb._fetchone("SELECT COUNT(*) c FROM worker_runs")["c"] == 1
        assert rdb._fetchone("SELECT COUNT(*) c FROM session_flow_events")["c"] == 1


def test_flow_fold_folds_into_control_rollups(split_env):
    """Fold writes a control session_flow_rollups row with summed counters."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=3)

    r = runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    assert r.status == "ok"
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["input_count"] == 2
    assert row["worker_runs"] == 1
    assert row["active_workers"] == 1
    assert row["llm_attempts"] == 3
    assert abs(row["cost_usd"] - 1.5) < 1e-9
    assert row["rollup_status"] == "ok"
    # STATE recomputed-from-latest (DM-2): LLM spent, no artifact -> warning.
    assert row["flow_state"] in ("running", "worker_started", "input_received")
    assert row["risk_level"] in ("warning", "critical", "ok")


def test_flow_fold_is_idempotent_high_water(split_env):
    """(b) Fold folds runtime rows EXACTLY ONCE (high-water idempotent)."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=3)

    router = AtlasDBRouter()
    runtime_rollup.rollup_session_flow(session_id, router=router)
    runtime_rollup.rollup_session_flow(session_id, router=router)  # repeat
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["input_count"] == 2, "idempotent: must NOT become 4"
    assert row["llm_attempts"] == 3, "idempotent: must NOT become 6"
    assert abs(row["cost_usd"] - 1.5) < 1e-9, "idempotent: cost must not double"


def test_flow_fold_picks_up_only_new_rows(split_env):
    """(d) Backfill/fold repeat-safe: only rows beyond the high-water are added."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=2)
    router = AtlasDBRouter()
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.list_session_flow_rollups(session_id=session_id)[0]["llm_attempts"] == 2

    # add 3 more llm_calls + 1 more input, re-fold
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        for i in range(3):
            rdb.record_llm_call(
                session_id=session_id, ip_id="ip-test", workflow="rtl-gen",
                model="m", call_role="worker", tokens_input=1, tokens_output=1,
                cost_usd=0.1, status="ok",
            )
        rdb.record_session_input(
            session_id=session_id, source="chat", source_ref_id="m-new",
            char_count=5, token_estimate=2, user_id="u-test",
            ip_id="ip-test", workflow="rtl-gen",
        )
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["llm_attempts"] == 5, "2 old + 3 new (not 7)"
    assert row["input_count"] == 2, "1 old + 1 new (not 3)"


def test_flow_fold_populates_attribution_gap_count(split_env):
    """(f) attribution_gap_count populated by fold for incomplete-attribution sessions.

    A session with activity but NO ip/workflow link is a real-but-inferred
    session, so its own attribution_gap_count must be non-zero.
    """
    control_path, _root = split_env
    session_id = "u-noattr/ip-x/wf-x"
    # Seed a session WITHOUT ip/workflow on the control sessions row.
    with AtlasDB(control_path, schema_set="full") as db:
        db._execute(
            "INSERT OR IGNORE INTO users (id, username, display_name, role, created_at) "
            "VALUES (?, ?, ?, 'user', ?)",
            ("u-noattr", "u-noattr", "u-noattr", db._now()),
        )
        db.upsert_runtime_session(session_id, user_id="u-noattr", owner="u-noattr")
    runtime_path = AtlasDBRouter().runtime_route(session_id, create=True).runtime_db_path
    # Inputs/LLM with no ip/workflow attribution.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.record_session_input(
            session_id=session_id, source="chat", source_ref_id="m0",
            char_count=10, token_estimate=3, user_id="u-noattr",
        )
        rdb.record_llm_call(
            session_id=session_id, model="m", call_role="worker",
            tokens_input=10, tokens_output=2, cost_usd=0.2, status="ok",
        )
    runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["attribution_gap_count"] >= 1
    assert row["attribution_confidence"] in ("inferred", "missing")


def test_flow_all_active_derives_ip_rollups(split_env):
    """rollup_all_active_flow derives ip_flow_rollups (RS-3) from session rollups."""
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=3)

    results = runtime_rollup.rollup_all_active_flow(router=AtlasDBRouter())
    assert any(r.session_id == session_id and r.status == "ok" for r in results)
    with AtlasDB(control_path, schema_set="full") as cdb:
        ips = cdb.list_ip_flow_rollups()
    ip = next(i for i in ips if i["ip_id"] == "ip-test")
    assert ip["sessions"] == 1
    assert ip["llm_attempts"] == 3
    assert abs(ip["cost_usd"] - 1.5) < 1e-9


def test_flow_fold_marks_missing_runtime_stale(split_env):
    """A missing runtime file marks the flow rollup STALE (not silent-empty)."""
    import os as _os

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=1)
    runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    # Delete the runtime file, re-fold -> stale.
    _os.remove(runtime_path)
    r = runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    assert r.status == "stale"
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["rollup_status"] == "stale"
    assert row["rollup_lag_s"] is not None


def test_session_flow_no_runtime_open(split_env, monkeypatch):
    """(c) NO-FANOUT: a normal admin Session Flow read opens ZERO runtime sqlite files.

    The fold (out-of-band) opens the runtime DB; the admin READ then consumes the
    control-side rollups ONLY. We spy on sqlite3.connect AND the router's
    runtime_db opener and assert neither touches a runtime file on the read path.
    """
    from core import session_flow_usage

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=3)
    # Fold out-of-band (this DOES open the runtime DB — expected).
    runtime_rollup.rollup_all_active_flow(router=AtlasDBRouter())

    opened_runtime: list[str] = []
    real_connect = sqlite3.connect

    def _spy_connect(path, *args, **kwargs):
        if isinstance(path, str) and "/runtime/" in path.replace("\\", "/"):
            opened_runtime.append(path)
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)

    real_runtime_db = AtlasDBRouter.runtime_db

    def _no_runtime_db(self, *a, **k):
        raise AssertionError("read path opened a runtime DB via the router")

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _no_runtime_db)
    try:
        with AtlasDB(control_path, schema_set="full") as cdb:
            payload = session_flow_usage.build_session_flow_payload(
                cdb, {"limit": 100, "range": "all"}
            )
    finally:
        monkeypatch.setattr(AtlasDBRouter, "runtime_db", real_runtime_db)

    assert payload["runtime_mode"] is True
    assert not opened_runtime, f"runtime file opened on read: {opened_runtime}"
    # Totals come from the folded rollup, not an empty control table.
    sess = next(s for s in payload["sessions"] if s["session_id"] == session_id)
    assert sess["llm_attempts"] == 3
    assert sess["input_count"] == 2


def test_session_flow_range_windowing_filters(split_env):
    """(e) range windowing filters by last activity; default 7d; 'all' keeps stale."""
    from core import session_flow_usage

    control_path, _root = split_env
    fresh = "u-test/ip-test/fresh"
    old = "u-test/ip-test/old"
    for sid, wf in ((fresh, "fresh"), (old, "old")):
        rp = _seed_session(control_path, sid)
        _seed_flow_rows(rp, sid, n_inputs=1, n_llm=1, workflow=wf)
    runtime_rollup.rollup_all_active_flow(router=AtlasDBRouter())

    # Force the OLD session's rollup updated_at to 40 days ago.
    old_ts = time.time() - 40 * 24 * 3600
    with AtlasDB(control_path, schema_set="full") as cdb:
        cdb._execute(
            "UPDATE session_flow_rollups SET updated_at = ?, stale_age_s = ? "
            "WHERE session_id = ?",
            (old_ts, 40 * 24 * 3600, old),
        )
        # 7d (default): old session excluded.
        p7 = session_flow_usage.build_session_flow_payload(cdb, {"range": "7d"})
        ids7 = {s["session_id"] for s in p7["sessions"]}
        assert fresh in ids7 and old not in ids7
        # 30d: still excludes the 40-day-old session.
        p30 = session_flow_usage.build_session_flow_payload(cdb, {"range": "30d"})
        ids30 = {s["session_id"] for s in p30["sessions"]}
        assert old not in ids30
        # all: includes the old session.
        pall = session_flow_usage.build_session_flow_payload(cdb, {"range": "all"})
        idsall = {s["session_id"] for s in pall["sessions"]}
        assert fresh in idsall and old in idsall


# --------------------------------------------------------------------------- #
# Task 7 / B2 / RS-1: production trigger (scheduler) wiring
# --------------------------------------------------------------------------- #


def test_run_rollup_pass_folds_both(split_env):
    """run_rollup_pass folds BOTH the usage rollup AND the session-flow rollup."""
    import time as _t

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_runtime_rows(runtime_path, session_id, n_llm=2, n_trace=1)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=0)

    summary = runtime_rollup.run_rollup_pass(router=AtlasDBRouter())
    assert summary["usage"] >= 1
    assert summary["flow"] >= 1
    with AtlasDB(control_path, schema_set="full") as cdb:
        assert cdb.get_runtime_usage_rollup(session_id)["llm_calls"] == 2
        assert cdb.list_session_flow_rollups(session_id=session_id)[0]["input_count"] == 1
    _ = _t


def test_scheduler_guard_disabled_under_pytest(split_env, monkeypatch):
    """(g) The background scheduler does NOT spin up under pytest unless forced."""
    # PYTEST_CURRENT_TEST is set by pytest during this test, so the guard declines.
    monkeypatch.delenv("ATLAS_FLOW_ROLLUP_ENABLE", raising=False)
    assert runtime_rollup.scheduler_should_run() is False
    assert runtime_rollup.start_rollup_scheduler() is None
    # Forced on: returns True (and a real thread) even under pytest.
    monkeypatch.setenv("ATLAS_FLOW_ROLLUP_ENABLE", "1")
    assert runtime_rollup.scheduler_should_run() is True
    t = runtime_rollup.start_rollup_scheduler(interval_s=3600)
    assert t is not None and t.daemon is True
    # Hard-disabled wins everywhere.
    monkeypatch.setenv("ATLAS_FLOW_ROLLUP_ENABLE", "0")
    assert runtime_rollup.scheduler_should_run() is False


def test_scheduler_registered_at_bootstrap(monkeypatch):
    """(g) The production trigger is wired into create_app() bootstrap.

    Asserts WIRING (the bootstrap calls start_rollup_scheduler); the thread need
    not actually run. We verify the source wires it and that the symbol is the
    one create_app imports.
    """
    import inspect
    import src.atlas_ui as atlas_ui
    from core import runtime_rollup as rr

    src = inspect.getsource(atlas_ui.create_app)
    assert "start_rollup_scheduler" in src, "bootstrap must wire the rollup scheduler"
    assert hasattr(rr, "start_rollup_scheduler")
    assert callable(rr.start_rollup_scheduler)


# --------------------------------------------------------------------------- #
# Task 7 perf: build_session_flow_payload(limit=100) over a synthetic
# 100-user / 1000-session fixture stays no-fanout. Timing is LOGGED evidence
# (not a flaky hard assert); no-runtime-open is the HARD assert.
# --------------------------------------------------------------------------- #


def test_session_flow_read_scale_no_runtime_open(split_env, monkeypatch, capsys):
    from core import session_flow_usage

    control_path, _root = split_env
    n_users, n_sessions = 100, 1000
    # Seed 1000 control session_flow_rollups directly (the READ consumes these
    # only — no runtime files are needed for a no-fanout read).
    with AtlasDB(control_path, schema_set="full") as cdb:
        for i in range(n_sessions):
            uid = f"u{i % n_users:03d}"
            sid = f"{uid}/ip{i % 50:03d}/rtl-gen/{i:04d}"
            cdb.upsert_session_flow_rollup(sid, fields={
                "user_id": uid, "ip_id": f"ip{i % 50:03d}", "workflow": "rtl-gen",
                "input_count": 2, "llm_attempts": 3, "cost_usd": 0.5,
                "worker_runs": 1, "active_workers": 1,
                "flow_state": "running",
                "risk_level": "critical" if i % 7 == 0 else ("warning" if i % 3 == 0 else "ok"),
                "stale_age_s": 60.0, "attribution_confidence": "exact",
                "rollup_status": "ok", "rollup_lag_s": 1.0,
            })

    opened_runtime: list[str] = []
    real_connect = sqlite3.connect

    def _spy_connect(path, *args, **kwargs):
        if isinstance(path, str) and "/runtime/" in path.replace("\\", "/"):
            opened_runtime.append(path)
        return real_connect(path, *args, **kwargs)

    monkeypatch.setattr(sqlite3, "connect", _spy_connect)
    real_runtime_db = AtlasDBRouter.runtime_db

    def _no_runtime_db(self, *a, **k):
        raise AssertionError("read path opened a runtime DB via the router")

    monkeypatch.setattr(AtlasDBRouter, "runtime_db", _no_runtime_db)
    try:
        with AtlasDB(control_path, schema_set="full") as cdb:
            t0 = time.perf_counter()
            payload = session_flow_usage.build_session_flow_payload(
                cdb, {"limit": 100, "range": "all"}
            )
            elapsed_ms = (time.perf_counter() - t0) * 1000.0
    finally:
        monkeypatch.setattr(AtlasDBRouter, "runtime_db", real_runtime_db)

    # HARD asserts: no fanout; page sliced to 100 in Python; total_sessions is
    # full filtered count (summary/funnel/needs_attention use all rows).
    # SQL pushes down WHERE filters + ORDER BY (risk-sort); page boundary is
    # applied in Python so aggregates are correct over the full filtered set.
    assert not opened_runtime, f"runtime file opened on read: {opened_runtime}"
    assert payload["runtime_mode"] is True
    assert payload["limits"]["returned"] == 100
    assert payload["limits"]["total_sessions"] == n_sessions
    # MINOR-2: assert a timing ceiling so a future regression fails CI.
    # Budget is 500 ms (plan Task 7); we assert a generous 1000 ms ceiling
    # so the test is not flaky on slow CI machines while still catching
    # catastrophic regressions (e.g. WHERE/ORDER-BY SQL push-down removed).
    assert elapsed_ms < 1000, (
        f"build_session_flow_payload too slow: {elapsed_ms:.0f} ms >= 1000 ms ceiling "
        f"({n_sessions} sessions, limit=100). SQL filter/sort push-down may have regressed."
    )
    with capsys.disabled():
        print(f"\n[task7-perf] build_session_flow_payload(limit=100) over "
              f"{n_sessions} sessions: {elapsed_ms:.1f} ms "
              f"(budget <500ms; ceiling 1000ms)")


# --------------------------------------------------------------------------- #
# MAJOR-1: signal stability — verification_seen must not flicker on repeat fold
# --------------------------------------------------------------------------- #


def test_flow_fold_verification_seen_stable_on_repeat(split_env):
    """MAJOR-1: flow_state stays verification_seen after a no-new-rows fold pass.

    The bug: verification_count was read from the incremental slice (rowid >
    offset), so a repeat fold with no new events got verification_count=0 and
    flow_state dropped to running. The fix uses a full-recount signal query.
    """
    from core import session_flow_usage as sf

    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=1)
    # Add a verification event to the runtime DB.
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.record_session_flow_event(
            event_type="verification.passed",
            idempotency_key=f"{session_id}:verif-stable",
            session_id=session_id,
        )

    router = AtlasDBRouter()
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row1 = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row1["flow_state"] == "verification_seen", (
        f"Expected verification_seen after first fold, got {row1['flow_state']}"
    )

    # Second fold: no new rows added. flow_state must NOT reset to running.
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row2 = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row2["flow_state"] == "verification_seen", (
        f"MAJOR-1: flow_state flickered to {row2['flow_state']} on no-new-rows pass"
    )

    # Third fold: still no new rows.
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row3 = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row3["flow_state"] == "verification_seen", (
        f"MAJOR-1: flow_state flickered on third pass: {row3['flow_state']}"
    )


def test_flow_fold_last_activity_stable_on_repeat(split_env):
    """MAJOR-1: stale_age_s does not regress on no-new-rows fold passes.

    last_*_at signals were read from the incremental slice, so a repeat fold
    got None and stale_age fell back to sess.updated_at (older), causing
    stale_age_s to jump and potentially flip risk_level.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=2, n_llm=2)

    router = AtlasDBRouter()
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row1 = cdb.list_session_flow_rollups(session_id=session_id)[0]
    stale1 = row1["stale_age_s"]

    # Repeat fold: stale_age_s must stay <= stale1 + small epsilon (1s clock drift)
    runtime_rollup.rollup_session_flow(session_id, router=router)
    with AtlasDB(control_path, schema_set="full") as cdb:
        row2 = cdb.list_session_flow_rollups(session_id=session_id)[0]
    stale2 = row2["stale_age_s"]
    # stale_age_s grows with wall time but must NOT jump by more than a few
    # seconds (the fold takes <1s); a large jump signals last_*_at reset to None.
    assert stale2 - stale1 < 5.0, (
        f"MAJOR-1: stale_age_s jumped {stale1:.1f}s -> {stale2:.1f}s on no-new-rows fold"
    )


# --------------------------------------------------------------------------- #
# MAJOR-2: artifact_count + workflow_blocked from control DB
# --------------------------------------------------------------------------- #


def test_flow_fold_reads_artifact_count_from_control(split_env):
    """MAJOR-2: artifact_count is read from the control-DB artifact_versions table.

    artifact_versions is a full-schema control-only table (not in the runtime
    subset). Before the fix, artifact_count was always 0 in runtime mode.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=1)

    # Insert an artifact in the control DB.
    with AtlasDB(control_path, schema_set="full") as cdb:
        cdb._execute(
            "INSERT INTO artifact_versions "
            "(id, source_session_id, ip_id, artifact_type, version, created_at) "
            "VALUES (?,?,?,?,?,?)",
            ("art-ctrl", session_id, "ip-test", "rtl", "v1", cdb._now()),
        )

    runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["artifact_count"] == 1, (
        f"MAJOR-2: expected artifact_count=1, got {row['artifact_count']}"
    )
    # With input + llm + artifact, flow_state should reach artifact_produced or
    # verification_seen (not stuck at running).
    assert row["flow_state"] in ("artifact_produced", "verification_seen", "completed"), (
        f"MAJOR-2: flow_state should reflect artifact, got {row['flow_state']}"
    )


def test_flow_fold_workflow_blocked_critical(split_env):
    """MAJOR-2: a blocked workflow_run in the control DB yields risk=critical.

    workflow_runs is a full-schema control-only table. Before the fix, the fold
    always passed workflow_blocked=False so a blocked workflow never made the
    session critical in runtime mode.
    """
    control_path, _root = split_env
    session_id = "u-test/ip-test/rtl-gen"
    runtime_path = _seed_session(control_path, session_id)
    _seed_flow_rows(runtime_path, session_id, n_inputs=1, n_llm=1)

    # Insert a blocked workflow_run in the control DB.
    with AtlasDB(control_path, schema_set="full") as cdb:
        cdb._execute(
            "INSERT INTO workflow_runs "
            "(id, session_id, ip_id, workflow, status, created_at, updated_at) "
            "VALUES (?,?,?,?,?,?,?)",
            ("wf-blk", session_id, "ip-test", "rtl-gen", "blocked",
             cdb._now(), cdb._now()),
        )

    runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    with AtlasDB(control_path, schema_set="full") as cdb:
        row = cdb.list_session_flow_rollups(session_id=session_id)[0]
    assert row["flow_state"] == "blocked", (
        f"MAJOR-2: expected flow_state=blocked, got {row['flow_state']}"
    )
    assert row["risk_level"] == "critical", (
        f"MAJOR-2: expected risk_level=critical for blocked workflow, got {row['risk_level']}"
    )


# --------------------------------------------------------------------------- #
# MINOR-1: shared confidence helper — runtime and central agree on attribution
# --------------------------------------------------------------------------- #


def test_attribution_confidence_consistent_across_modes(split_env, monkeypatch):
    """MINOR-1: same session gets identical attribution_confidence in both modes.

    The bug was a ladder divergence: runtime fold had an extra 'inferred' tier
    (activity but missing ip/workflow) while central only had exact/missing.
    The fix extracts derive_attribution_confidence() as a shared helper.
    """
    from core import session_flow_usage as sf

    control_path, _root = split_env
    session_id = "u-nip/ip-x/wf-x"

    # Session with NO ip/workflow on the control sessions row.
    with AtlasDB(control_path, schema_set="full") as db:
        db._execute(
            "INSERT OR IGNORE INTO users (id,username,display_name,role,created_at) "
            "VALUES (?,?,?,'user',?)",
            ("u-nip", "u-nip", "u-nip", db._now()),
        )
        db.upsert_runtime_session(session_id, user_id="u-nip", owner="u-nip")

    runtime_path = AtlasDBRouter().runtime_route(session_id, create=True).runtime_db_path
    with AtlasDB(runtime_path, schema_set="runtime") as rdb:
        rdb.record_session_input(
            session_id=session_id, source="chat", source_ref_id="m0",
            char_count=5, token_estimate=2, user_id="u-nip",
        )
        rdb.record_llm_call(
            session_id=session_id, model="m", call_role="worker",
            tokens_input=5, tokens_output=2, cost_usd=0.1, status="ok",
        )

    # Runtime fold.
    runtime_rollup.rollup_session_flow(session_id, router=AtlasDBRouter())
    with AtlasDB(control_path, schema_set="full") as cdb:
        rt_row = cdb.list_session_flow_rollups(session_id=session_id)[0]

    # Central recompute (switch to central mode for the recompute call).
    monkeypatch.setenv("ATLAS_RUNTIME_DB_MODE", "central")
    with AtlasDB(control_path, schema_set="full") as cdb:
        # Manually copy runtime rows to control so central recompute can see them.
        for r in AtlasDB(runtime_path, schema_set="runtime")._fetchall(
            "SELECT * FROM session_inputs"
        ):
            rd = dict(r)
            try:
                cdb._execute(
                    "INSERT OR IGNORE INTO session_inputs "
                    "(id,session_id,user_id,source,source_ref_id,char_count,token_estimate,created_at) "
                    "VALUES (?,?,?,?,?,?,?,?)",
                    (rd["id"], rd["session_id"], rd["user_id"], rd["source"],
                     rd["source_ref_id"], rd["char_count"], rd["token_estimate"],
                     rd["created_at"]),
                )
            except Exception:
                pass
        sf.recompute_rollups(cdb)
        central_row = cdb.list_session_flow_rollups(session_id=session_id)[0]

    # Both modes must agree on attribution_confidence and attribution_gap_count.
    assert rt_row["attribution_confidence"] == central_row["attribution_confidence"], (
        f"MINOR-1: runtime={rt_row['attribution_confidence']} "
        f"central={central_row['attribution_confidence']}"
    )
    assert rt_row["attribution_gap_count"] == central_row["attribution_gap_count"], (
        f"MINOR-1: gap_count runtime={rt_row['attribution_gap_count']} "
        f"central={central_row['attribution_gap_count']}"
    )
