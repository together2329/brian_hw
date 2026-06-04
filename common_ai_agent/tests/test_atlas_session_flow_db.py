"""Session Flow Dashboard — Task 1 schema, migration, and DB-helper tests.

Covers the additive Session Flow data model in ``core/atlas_db.py``:

  - Fresh FULL DB has the 5 new tables + additive columns + new indexes.
  - Legacy FULL DB migrates additively via ``_run_lightweight_migrations``
    (existing rows preserved, no table dropped).
  - Legacy RUNTIME DB reopen (the B1 regression): a runtime DB built from the
    OLD runtime schema (llm_calls/trace_events WITHOUT the new columns) gains
    the new columns on reopen, and ``record_llm_call(..., worker_run_id=...)``
    succeeds without raising.
  - Runtime-schema DB can insert/read session_inputs, worker_runs,
    session_flow_events.
  - Idempotency is DB-enforced (UNIQUE keys), so replaying the same
    ``idempotency_key`` (events) and same ``(session_id, source, source_ref_id)``
    (inputs) does NOT double-count.
"""
from __future__ import annotations

import sqlite3
import sys
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from core.atlas_db import AtlasDB, _JSON_COLUMNS  # noqa: E402


# ============================================================
# helpers
# ============================================================


def _table_columns(db_path: str, table: str) -> set[str]:
    conn = sqlite3.connect(db_path)
    try:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
    finally:
        conn.close()
    return {r[1] for r in rows}


def _atlas_columns(db: AtlasDB, table: str) -> set[str]:
    return {r["name"] for r in db._fetchall(f"PRAGMA table_info({table})")}


def _all_tables(db: AtlasDB) -> set[str]:
    return {r["name"] for r in db._fetchall(
        "SELECT name FROM sqlite_master WHERE type='table'"
    )}


def _all_indexes(db: AtlasDB) -> set[str]:
    return {r["name"] for r in db._fetchall(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    )}


# ============================================================
# Section 1 — fresh FULL schema
# ============================================================


def test_schema_fresh_full_db_has_session_flow_tables(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    tables = _all_tables(db)
    for t in (
        "session_inputs", "worker_runs", "session_flow_events",
        "session_flow_rollups", "ip_flow_rollups",
    ):
        assert t in tables, f"missing flow table {t}"


def test_schema_fresh_full_db_has_additive_columns(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    assert {"objective", "flow_state", "success_condition", "completed_at",
            "abandoned_at", "last_flow_event_at"} <= _atlas_columns(db, "sessions")
    assert {"created_by_user_id", "source_session_id", "source_type",
            "source_confidence"} <= _atlas_columns(db, "ip_blocks")
    assert {"source_session_id", "source_worker_run_id", "source_llm_call_id",
            "attribution_confidence"} <= _atlas_columns(db, "artifact_versions")
    assert {"worker_run_id", "attribution_confidence", "missing_reason"} \
        <= _atlas_columns(db, "llm_calls")
    assert {"worker_run_id", "severity", "attribution_confidence",
            "missing_reason"} <= _atlas_columns(db, "trace_events")


def test_schema_fresh_full_db_has_new_indexes(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    have = _all_indexes(db)
    for idx in (
        "idx_session_inputs_session", "idx_worker_runs_session",
        "idx_session_flow_events_session", "idx_session_flow_rollups_risk",
        "idx_ip_flow_rollups_risk", "idx_llm_calls_worker_run",
        "idx_trace_events_worker_run",
    ):
        assert idx in have, f"missing index {idx}"


def test_session_flow_events_payload_in_json_columns(tmp_path):
    assert "payload" in _JSON_COLUMNS.get("session_flow_events", set())
    db = AtlasDB(str(tmp_path / "full.db"))
    ev = db.record_session_flow_event(
        event_type="session.created",
        idempotency_key="k-json-1",
        session_id="s1",
        payload={"input_count": 2, "reason": "seed"},
    )
    # JSON-decoded on read
    assert ev["payload"] == {"input_count": 2, "reason": "seed"}


def test_attribution_confidence_enum_enforced(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    for good in ("exact", "inferred", "missing", "conflict"):
        row = db.record_session_input(
            "s-enum", source="enqueue", source_ref_id=f"r-{good}",
            attribution_confidence=good,
        )
        assert row["attribution_confidence"] == good
    with pytest.raises(ValueError):
        db.record_session_input(
            "s-enum", source="enqueue", source_ref_id="bad",
            attribution_confidence="totally_sure",
        )


# ============================================================
# Section 2 — legacy FULL DB migration (additive, non-destructive)
# ============================================================


def test_legacy_migration_full_db_is_additive(tmp_path):
    """A minimal OLD full DB gains the new columns/tables via
    _run_lightweight_migrations, with existing rows preserved and no drop."""
    db_path = tmp_path / "legacy-full.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.executescript(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                display_name TEXT,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                created_at REAL,
                last_login_at REAL
            );
            CREATE TABLE sessions (
                id TEXT PRIMARY KEY,
                user_id TEXT NOT NULL,
                title TEXT,
                status TEXT DEFAULT 'active',
                created_at REAL,
                updated_at REAL
            );
            CREATE TABLE ip_blocks (
                id TEXT PRIMARY KEY,
                workspace_id TEXT NOT NULL,
                ip_name TEXT NOT NULL,
                ip_type TEXT,
                status TEXT DEFAULT 'active',
                created_at REAL,
                updated_at REAL
            );
            CREATE TABLE artifact_versions (
                id TEXT PRIMARY KEY,
                workspace_id TEXT,
                ip_id TEXT NOT NULL,
                artifact_type TEXT NOT NULL,
                version TEXT NOT NULL,
                created_at REAL
            );
            CREATE TABLE llm_calls (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                model TEXT,
                cost_usd REAL DEFAULT 0,
                status TEXT,
                created_at REAL
            );
            CREATE TABLE trace_events (
                id TEXT PRIMARY KEY,
                event_type TEXT NOT NULL,
                session_id TEXT,
                idempotency_key TEXT UNIQUE,
                payload TEXT,
                created_at REAL
            );
            INSERT INTO users (id, username, display_name, created_at)
                VALUES ('u-old', 'olduser', 'Old User', 1.0);
            INSERT INTO sessions (id, user_id, title, status, created_at)
                VALUES ('s-old', 'u-old', 'old session', 'active', 2.0);
            INSERT INTO llm_calls (id, session_id, model, cost_usd, status, created_at)
                VALUES ('llm-old', 's-old', 'm', 0.5, 'ok', 3.0);
            """
        )
        conn.commit()
    finally:
        conn.close()

    with AtlasDB(str(db_path)) as db:
        # Additive columns now present on EXISTING tables.
        assert "flow_state" in _atlas_columns(db, "sessions")
        assert "created_by_user_id" in _atlas_columns(db, "ip_blocks")
        assert "source_session_id" in _atlas_columns(db, "artifact_versions")
        assert "worker_run_id" in _atlas_columns(db, "llm_calls")
        assert "severity" in _atlas_columns(db, "trace_events")
        # New tables created.
        tables = _all_tables(db)
        for t in ("session_inputs", "worker_runs", "session_flow_events",
                  "session_flow_rollups", "ip_flow_rollups"):
            assert t in tables
        # Existing rows preserved.
        assert db.get_user("u-old")["username"] == "olduser"
        assert db.get_session("s-old")["title"] == "old session"
        kept = db._fetchall("SELECT cost_usd FROM llm_calls WHERE id = 'llm-old'")
        assert abs(kept[0]["cost_usd"] - 0.5) < 1e-9
        # No table was dropped — the old llm_calls row count is intact.
        cnt = db._fetchall("SELECT COUNT(*) AS c FROM llm_calls")[0]["c"]
        assert cnt == 1


# ============================================================
# Section 3 — legacy RUNTIME DB reopen (B1 regression)
# ============================================================


_OLD_RUNTIME_SCHEMA = """
CREATE TABLE IF NOT EXISTS session_queue (
    id TEXT PRIMARY KEY,
    session_id TEXT NOT NULL,
    direction TEXT NOT NULL,
    msg_type TEXT NOT NULL,
    payload TEXT,
    created_at REAL NOT NULL,
    processed_at REAL,
    delivered_at REAL,
    expires_at REAL
);
CREATE TABLE IF NOT EXISTS trace_events (
    id TEXT PRIMARY KEY,
    event_type TEXT NOT NULL,
    session_id TEXT,
    workspace_id TEXT,
    ip_id TEXT,
    workflow TEXT,
    run_id TEXT,
    stage_id TEXT,
    todo_id TEXT,
    message_id TEXT,
    llm_call_id TEXT,
    artifact_id TEXT,
    actor_user_id TEXT,
    correlation_id TEXT,
    causation_id TEXT,
    idempotency_key TEXT UNIQUE,
    payload TEXT,
    created_at REAL
);
CREATE TABLE IF NOT EXISTS llm_calls (
    id TEXT PRIMARY KEY,
    message_id TEXT,
    run_id TEXT,
    stage_id TEXT,
    todo_id TEXT,
    session_id TEXT,
    workspace_id TEXT,
    ip_id TEXT,
    workflow TEXT,
    model TEXT,
    provider TEXT,
    base_url_hash TEXT,
    call_role TEXT,
    attempt INT DEFAULT 1,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    tokens_reasoning INT DEFAULT 0,
    cache_read_tokens INT DEFAULT 0,
    cache_write_tokens INT DEFAULT 0,
    cost_usd REAL DEFAULT 0,
    latency_ms REAL,
    status TEXT,
    error_type TEXT,
    created_at REAL,
    completed_at REAL
);
"""


def test_b1_legacy_runtime_reopen_adds_columns_and_inserts(tmp_path):
    """B1 regression: a pre-existing runtime DB without the new columns must
    gain them on reopen via AtlasDB(schema_set='runtime'), and a write that
    references a new column (llm_calls.worker_run_id) must NOT raise."""
    db_path = tmp_path / "legacy-runtime.db"
    raw = sqlite3.connect(db_path)
    try:
        raw.executescript(_OLD_RUNTIME_SCHEMA)
        raw.commit()
    finally:
        raw.close()

    # Before reopen: the new columns are absent (proves the regression setup).
    assert "worker_run_id" not in _table_columns(str(db_path), "llm_calls")
    assert "worker_run_id" not in _table_columns(str(db_path), "trace_events")

    db = AtlasDB(str(db_path), schema_set="runtime")

    # (a) new columns now exist on the EXISTING runtime tables.
    assert {"worker_run_id", "attribution_confidence", "missing_reason"} \
        <= _atlas_columns(db, "llm_calls")
    assert {"worker_run_id", "severity", "attribution_confidence",
            "missing_reason"} <= _atlas_columns(db, "trace_events")
    # New flow tables present too.
    tables = _all_tables(db)
    for t in ("session_inputs", "worker_runs", "session_flow_events"):
        assert t in tables

    # (b) an INSERT referencing a new column succeeds without raising.
    call = db.record_llm_call(
        session_id="s-rt", model="m", cost_usd=0.1,
        worker_run_id="wr-1", attribution_confidence="exact",
    )
    assert call["worker_run_id"] == "wr-1"
    assert call["attribution_confidence"] == "exact"


def test_b1_runtime_subset_excludes_control_tables(tmp_path):
    """The runtime subset must add the 3 shared flow tables but NOT the
    control-only rollup tables nor existing control tables."""
    db = AtlasDB(str(tmp_path / "rt.db"), schema_set="runtime")
    tables = _all_tables(db)
    for t in ("session_inputs", "worker_runs", "session_flow_events"):
        assert t in tables
    for t in ("session_flow_rollups", "ip_flow_rollups", "users", "sessions",
              "ip_blocks", "workflow_runs"):
        assert t not in tables, f"{t} must not exist in runtime subset"


# ============================================================
# Section 4 — runtime DB insert/read for the 3 shared flow tables
# ============================================================


def test_runtime_db_inserts_and_reads_flow_tables(tmp_path):
    db = AtlasDB(str(tmp_path / "rt.db"), schema_set="runtime")

    inp = db.record_session_input(
        "s-rt", source="enqueue", source_ref_id="q-1",
        char_count=42, token_estimate=10, attribution_confidence="exact",
    )
    assert inp["char_count"] == 42
    assert inp["source_ref_id"] == "q-1"

    run = db.start_worker_run(session_id="s-rt", worker_kind="workflow",
                              workflow="rtl-gen", status="running")
    assert run["status"] == "running"
    fin = db.finish_worker_run(run["id"], status="completed")
    assert fin["status"] == "completed"
    assert fin["ended_at"] is not None
    assert fin["duration_ms"] is not None and fin["duration_ms"] >= 0

    ev = db.record_session_flow_event(
        event_type="worker.started", idempotency_key="ev-rt-1",
        session_id="s-rt", worker_run_id=run["id"],
        payload={"worker_kind": "workflow"},
    )
    assert ev["event_type"] == "worker.started"
    # Reads back from the runtime file.
    rows = db._fetchall("SELECT COUNT(*) AS c FROM session_inputs")
    assert rows[0]["c"] == 1
    rows = db._fetchall("SELECT COUNT(*) AS c FROM worker_runs")
    assert rows[0]["c"] == 1
    rows = db._fetchall("SELECT COUNT(*) AS c FROM session_flow_events")
    assert rows[0]["c"] == 1


# ============================================================
# Section 5 — DB-enforced idempotency (no double-count)
# ============================================================


def test_idempotent_session_flow_event_by_key(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    # Use an ALLOWLISTED payload key (Task 2 PS-1 guard drops unknown keys).
    first = db.record_session_flow_event(
        event_type="session.created", idempotency_key="dup-key",
        session_id="s1", payload={"input_count": 1},
    )
    second = db.record_session_flow_event(
        event_type="session.created", idempotency_key="dup-key",
        session_id="s1", payload={"input_count": 2},
    )
    # Same row returned; the second insert was a no-op (ON CONFLICT DO NOTHING).
    assert first["id"] == second["id"]
    assert first["payload"] == {"input_count": 1}
    cnt = db._fetchall(
        "SELECT COUNT(*) AS c FROM session_flow_events WHERE session_id = 's1'"
    )[0]["c"]
    assert cnt == 1


def test_idempotent_session_input_by_source_ref(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    a = db.record_session_input("s1", source="enqueue", source_ref_id="q-1",
                                char_count=10)
    b = db.record_session_input("s1", source="enqueue", source_ref_id="q-1",
                                char_count=999)
    assert a["id"] == b["id"]
    # The first write wins; replay did not overwrite or duplicate.
    assert b["char_count"] == 10
    cnt = db._fetchall(
        "SELECT COUNT(*) AS c FROM session_inputs WHERE session_id = 's1'"
    )[0]["c"]
    assert cnt == 1


def test_session_input_synthesizes_stable_ref_when_absent(tmp_path):
    """When the caller gives no source_ref_id, a deterministic ref is
    synthesized so replaying the SAME logical input still dedupes."""
    db = AtlasDB(str(tmp_path / "full.db"))
    a = db.record_session_input("s1", source="enqueue", input_hash="h-abc",
                                char_count=10)
    b = db.record_session_input("s1", source="enqueue", input_hash="h-abc",
                                char_count=10)
    assert a["id"] == b["id"]
    assert a["source_ref_id"]  # non-null
    cnt = db._fetchall(
        "SELECT COUNT(*) AS c FROM session_inputs WHERE session_id = 's1'"
    )[0]["c"]
    assert cnt == 1


def test_flow_rollups_upsert_is_idempotent_recompute(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    db.upsert_session_flow_rollup("s1", fields={
        "user_id": "u1", "ip_id": "ip1", "input_count": 3,
        "llm_attempts": 5, "risk_level": "warning", "flow_state": "running",
    })
    # Recompute-from-latest overwrites (NOT sums) — counters reflect the
    # latest snapshot, state is replaced.
    db.upsert_session_flow_rollup("s1", fields={
        "input_count": 4, "llm_attempts": 7, "risk_level": "critical",
        "flow_state": "blocked",
    })
    rows = db.list_session_flow_rollups(session_id="s1")
    assert len(rows) == 1
    row = rows[0]
    assert row["input_count"] == 4  # replaced, not 3+4
    assert row["llm_attempts"] == 7
    assert row["risk_level"] == "critical"
    assert row["flow_state"] == "blocked"
    assert row["user_id"] == "u1"  # preserved across upsert

    db.upsert_ip_flow_rollup("ip1", fields={
        "workspace_id": "ws1", "sessions": 2, "cost_usd": 1.25,
        "risk_level": "ok", "source_confidence": "inferred",
    })
    iprows = db.list_ip_flow_rollups(ip_id="ip1")
    assert len(iprows) == 1
    assert iprows[0]["sessions"] == 2
    assert abs(iprows[0]["cost_usd"] - 1.25) < 1e-9
    assert iprows[0]["source_confidence"] == "inferred"


# ============================================================
# Section 6 — Task 2 instrumented write paths
# ============================================================


def _flow_events(db: AtlasDB, event_type: str | None = None):
    sql = "SELECT * FROM session_flow_events"
    params: tuple = ()
    if event_type is not None:
        sql += " WHERE event_type = ?"
        params = (event_type,)
    return [db._row_to_dict(r, "session_flow_events") for r in db._fetchall(sql, params)]


def test_create_session_emits_session_created_event(tmp_path):
    """create_session writes the head-of-funnel session.created flow event and
    seeds the new metadata columns without breaking the legacy 3-arg call."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("alice", "Alice")
    # Legacy positional call still valid.
    legacy = db.create_session(u["id"], "legacy title", "proj-x")
    assert legacy["flow_state"] == "created"
    # New metadata call.
    s = db.create_session(
        u["id"], "new title", "proj-y",
        namespace="ns/ip/wf", owner="alice", workspace_id="ws1",
        ip_id="ip1", ip="ipname", workflow="rtl-gen", session_kind="runtime",
        objective="build rtl", success_condition="all gates green",
    )
    assert s["namespace"] == "ns/ip/wf"
    assert s["objective"] == "build rtl"
    assert s["workflow"] == "rtl-gen"
    created = _flow_events(db, "session.created")
    ids = {e["session_id"] for e in created}
    assert legacy["id"] in ids and s["id"] in ids
    # Re-creation cannot duplicate the event for the same session id.
    again = db.record_session_flow_event(
        event_type="session.created",
        idempotency_key=f"session-created:{s['id']}",
        session_id=s["id"],
    )
    assert again["id"] == next(e["id"] for e in created if e["session_id"] == s["id"])


def test_write_path_complete_lineage_links_by_session_id(tmp_path):
    """Session -> input -> worker_run -> llm_call -> ip -> artifact all carry the
    same session_id (or link to it), proving end-to-end lineage."""
    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("bob", "Bob")
    s = db.create_session(u["id"], "lineage", workflow="rtl-gen", ip="ipL")
    sid = s["id"]

    inp = db.record_session_input(
        sid, source="enqueue", source_ref_id="q-1", user_id=u["id"],
        char_count=12, token_estimate=3, input_hash="h1",
        attribution_confidence="exact",
    )
    db.record_session_flow_event(
        event_type="input.received", idempotency_key=f"input-received:{sid}:q-1",
        session_id=sid, attribution_confidence="exact",
        payload={"char_count": 12, "input_hash": "h1"},
    )

    wr = db.start_worker_run(session_id=sid, user_id=u["id"], workflow="rtl-gen",
                             worker_kind="workflow", status="running")
    call = db.record_llm_call(
        session_id=sid, model="m", cost_usd=0.2, worker_run_id=wr["id"],
        attribution_confidence="exact",
    )
    ip = db.upsert_ip_block(
        "ws1", "ipL", created_by_user_id=u["id"], source_session_id=sid,
        source_type="workflow", source_confidence="exact",
    )
    art = db.register_artifact_version(
        ip["id"], "ssot", workspace_id="ws1", version="v1",
        source_session_id=sid, source_worker_run_id=wr["id"],
        source_llm_call_id=call["id"], attribution_confidence="exact",
    )
    db.finish_worker_run(wr["id"], status="completed")

    # Everything resolves back to the same session.
    assert inp["session_id"] == sid
    assert wr["session_id"] == sid
    assert call["session_id"] == sid
    assert call["worker_run_id"] == wr["id"]
    assert ip["source_session_id"] == sid
    assert art["source_session_id"] == sid
    assert art["source_worker_run_id"] == wr["id"]
    assert art["source_llm_call_id"] == call["id"]
    # Flow events for session.created + input.received + ip.created +
    # artifact.produced all carry sid.
    for et in ("session.created", "input.received", "ip.created", "artifact.produced"):
        evs = [e for e in _flow_events(db, et) if e["session_id"] == sid]
        assert evs, f"missing {et} event for session {sid}"


def test_worker_run_id_threaded_into_llm_calls(tmp_path):
    """record_llm_call persists worker_run_id and normalizes confidence."""
    db = AtlasDB(str(tmp_path / "full.db"))
    wr = db.start_worker_run(session_id="s1", worker_kind="workflow")
    call = db.record_llm_call(
        session_id="s1", model="m", worker_run_id=wr["id"],
        attribution_confidence="EXACT",  # case-insensitive normalize
    )
    assert call["worker_run_id"] == wr["id"]
    assert call["attribution_confidence"] == "exact"
    # An out-of-enum confidence fails loud on the llm path too (MINOR-2).
    with pytest.raises(ValueError):
        db.record_llm_call(session_id="s1", model="m",
                           attribution_confidence="pretty_sure")


def test_ip_created_exactly_once_on_double_upsert(tmp_path):
    """WP-3: ip.created fires once; provenance is write-once (UPDATE never
    overwrites a set provenance column)."""
    db = AtlasDB(str(tmp_path / "full.db"))
    first = db.upsert_ip_block(
        "ws1", "ipX", created_by_user_id="u1", source_session_id="sess-1",
        source_type="workflow", source_confidence="exact",
    )
    # Second upsert (UPDATE branch) with DIFFERENT provenance must not clobber.
    second = db.upsert_ip_block(
        "ws1", "ipX", created_by_user_id="u2", source_session_id="sess-2",
        source_type="manual", source_confidence="inferred", status="archived",
    )
    assert first["id"] == second["id"]
    assert second["created_by_user_id"] == "u1"  # preserved
    assert second["source_session_id"] == "sess-1"  # preserved
    assert second["source_type"] == "workflow"  # preserved
    assert second["status"] == "archived"  # non-provenance field still updates
    ip_events = _flow_events(db, "ip.created")
    matching = [e for e in ip_events if e["ip_id"] == first["id"]]
    assert len(matching) == 1, matching


def test_ip_created_backfills_empty_provenance_write_once(tmp_path):
    """A first INSERT with NO provenance, then a later upsert WITH provenance:
    the empty columns are backfilled (write-once allows fill, not overwrite)."""
    db = AtlasDB(str(tmp_path / "full.db"))
    a = db.upsert_ip_block("ws1", "ipY")  # no provenance
    assert not a.get("created_by_user_id")
    b = db.upsert_ip_block(
        "ws1", "ipY", created_by_user_id="u9", source_session_id="sess-9",
        source_type="workflow",
    )
    assert b["created_by_user_id"] == "u9"
    assert b["source_session_id"] == "sess-9"
    # Still only ONE ip.created (it only fires on the INSERT branch).
    assert len([e for e in _flow_events(db, "ip.created") if e["ip_id"] == a["id"]]) <= 1


def test_artifact_produced_event_and_provenance(tmp_path):
    db = AtlasDB(str(tmp_path / "full.db"))
    ip = db.upsert_ip_block("ws1", "ipA")
    art = db.register_artifact_version(
        ip["id"], "rtl", workspace_id="ws1", version="v1",
        source_session_id="sess-A", source_worker_run_id="wr-A",
        source_llm_call_id="llm-A", attribution_confidence="exact",
    )
    assert art["attribution_confidence"] == "exact"
    evs = [e for e in _flow_events(db, "artifact.produced")
           if e["artifact_version_id"] == art["id"]]
    assert len(evs) == 1
    assert evs[0]["worker_run_id"] == "wr-A"
    assert evs[0]["llm_call_id"] == "llm-A"


def test_idempotent_input_and_event_replay_via_manager(tmp_path, monkeypatch):
    """The manager's user-input capture writes EXACTLY one session_inputs row +
    one input.received event per inbound prompt, even on replay (same msg_id)."""
    import core.session_process_manager as spm

    db = AtlasDB(str(tmp_path / "rt.db"), schema_set="runtime")
    mgr = spm.SessionProcessManager(db_path=str(tmp_path / "ctrl.db"))
    session_id = "bob/ipL/rtl-gen"
    payload = {"text": "please generate the rtl"}

    # Two calls with the SAME msg_id (a retry/replay) -> still one row/event.
    mgr._record_user_input(db, session_id, "msg-1", payload, "prompt")
    mgr._record_user_input(db, session_id, "msg-1", payload, "prompt")

    rows = db._fetchall("SELECT * FROM session_inputs WHERE session_id = ?", (session_id,))
    assert len(rows) == 1
    assert rows[0]["char_count"] == len(payload["text"])
    assert rows[0]["source_ref_id"] == "msg-1"
    evs = [e for e in _flow_events(db, "input.received") if e["session_id"] == session_id]
    assert len(evs) == 1


# ============================================================
# Section 7 — PS-1 raw-prompt write guard
# ============================================================


# Longer than _FLOW_SUMMARY_MAX_LEN (120) so a truncated free-text column can
# never hold the FULL seeded string — the PS-1 invariant we assert below.
_SEEDED_PROMPT = (
    "SUPER_SECRET_PROMPT_payload_that_must_never_persist_anywhere_"
    "in_any_flow_table_or_event_payload_or_summary_or_label_field_"
    "because_it_is_raw_user_prompt_text_and_privacy_forbids_it_xyz"
)


def test_ps1_no_raw_prompt_in_any_flow_table(tmp_path):
    """PS-1: a known seeded prompt string must NEVER appear in any flow table or
    flow-event payload, even when callers try to smuggle it via payload/summary
    free-text fields."""
    db = AtlasDB(str(tmp_path / "full.db"))

    # 1) flow event with the prompt in a NON-allowlisted key -> dropped.
    db.record_session_flow_event(
        event_type="input.received", idempotency_key="ps1-evt",
        session_id="s1", payload={"text": _SEEDED_PROMPT, "char_count": 5},
    )
    # 2) flow event with the prompt mis-bucketed into an allowed label -> truncated
    #    (the seeded constant is >120 chars only if we pad it; assert it is not
    #    stored verbatim regardless by using a long value).
    db.record_session_flow_event(
        event_type="worker.note", idempotency_key="ps1-evt2",
        session_id="s1", payload={"worker_label": _SEEDED_PROMPT * 5},
    )
    # 3) worker_run free-text summary/label -> truncated.
    wr = db.start_worker_run(session_id="s1", task_label=_SEEDED_PROMPT * 5)
    db.finish_worker_run(wr["id"], status="completed",
                         output_summary=_SEEDED_PROMPT * 5,
                         error_summary=_SEEDED_PROMPT * 5)

    # Pin the truncation BOUND explicitly: full-string absence alone would pass
    # even if truncation trimmed only a single char. Every free-text column must
    # be clamped to the cap.
    from core.atlas_db import _FLOW_SUMMARY_MAX_LEN
    wr_row = dict(db._fetchall(
        "SELECT task_label, output_summary, error_summary FROM worker_runs "
        f"WHERE id = '{wr['id']}'"
    )[0])
    for col, val in wr_row.items():
        assert isinstance(val, str) and len(val) <= _FLOW_SUMMARY_MAX_LEN, (
            f"{col} not clamped to {_FLOW_SUMMARY_MAX_LEN}: len={len(val or '')}"
        )

    # Scan EVERY column of EVERY flow table for the seeded prompt.
    flow_tables = ["session_inputs", "worker_runs", "session_flow_events",
                   "session_flow_rollups", "ip_flow_rollups"]
    for table in flow_tables:
        rows = db._fetchall(f"SELECT * FROM {table}")
        for row in rows:
            for value in dict(row).values():
                if isinstance(value, str):
                    assert _SEEDED_PROMPT not in value, (
                        f"raw prompt leaked into {table}: {value!r}"
                    )

    # The allowlisted count survived; the smuggled text key did not.
    evt = db._fetchall(
        "SELECT payload FROM session_flow_events WHERE idempotency_key = 'ps1-evt'"
    )[0]
    assert _SEEDED_PROMPT not in (evt["payload"] or "")
    assert "char_count" in (evt["payload"] or "")


# ============================================================
# Section 7 — Task 7 hardening: indexes + repeat-safe backfill/fold
# ============================================================


def test_schema_has_task7_filter_indexes(tmp_path):
    """Task 7: attribution + range-windowing filter indexes exist."""
    db = AtlasDB(str(tmp_path / "full.db"))
    have = _all_indexes(db)
    for idx in (
        "idx_session_flow_rollups_attribution",
        "idx_session_flow_rollups_updated",
        "idx_session_flow_rollups_user",
        "idx_session_flow_rollups_ip",
    ):
        assert idx in have, f"missing Task-7 filter index {idx}"


def test_backfill_repeat_safe(tmp_path):
    """QA: backfill can run twice without double-counting (central-mode recompute).

    The recompute-overwrite upserts converge, so counts + rollups are identical
    after a second run.
    """
    import core.session_flow_usage as sf

    db = AtlasDB(str(tmp_path / "full.db"))
    u = db.create_user("alice", "Alice")
    s = db.create_session(u["id"], "bf", workflow="rtl-gen", ip="ipBF")
    sid = s["id"]
    db.record_session_input(
        session_id=sid, source="chat", source_ref_id="m1", char_count=12,
        token_estimate=4, user_id=u["id"], ip_id="ipBF", workflow="rtl-gen",
    )
    for i in range(3):
        db.record_llm_call(
            session_id=sid, ip_id="ipBF", workflow="rtl-gen", model="m",
            call_role="worker", tokens_input=10, tokens_output=2,
            cost_usd=0.4, status="ok",
        )

    r1 = sf.backfill_session_flow(db)
    row1 = db.list_session_flow_rollups(session_id=sid)[0]
    r2 = sf.backfill_session_flow(db)  # repeat
    row2 = db.list_session_flow_rollups(session_id=sid)[0]

    assert r1["sessions"] == r2["sessions"]
    assert row1["input_count"] == row2["input_count"] == 1, "no double-count"
    assert row1["llm_attempts"] == row2["llm_attempts"] == 3, "no double-count"
    assert abs(row1["cost_usd"] - row2["cost_usd"]) < 1e-9
    assert abs(row2["cost_usd"] - 1.2) < 1e-9


def test_fold_session_flow_rollup_offset_isolated_from_usage_fold(tmp_path):
    """The flow fold uses 'flow:'-prefixed offset keys, isolated from the usage fold.

    Folding the same physical llm_calls table by BOTH folds must keep INDEPENDENT
    high-water marks (no cross-clobber), so both stay correct.
    """
    db = AtlasDB(str(tmp_path / "full.db"))
    db.fold_session_flow_rollup(
        "s-iso",
        deltas={"llm_attempts": 2, "cost_usd": 0.5},
        offsets={"flow:llm_calls": 7},
        state={"flow_state": "running", "risk_level": "ok"},
    )
    # usage-fold offset key is the bare table name; flow-fold is 'flow:llm_calls'.
    assert db.get_rollup_offset("s-iso", "flow:llm_calls") == 7
    assert db.get_rollup_offset("s-iso", "llm_calls") == 0
    row = db.list_session_flow_rollups(session_id="s-iso")[0]
    assert row["llm_attempts"] == 2
    assert abs(row["cost_usd"] - 0.5) < 1e-9
    assert row["flow_state"] == "running"

    # Second fold ADDS deltas (caller is responsible for high-water slicing).
    db.fold_session_flow_rollup(
        "s-iso", deltas={"llm_attempts": 3}, offsets={"flow:llm_calls": 12},
    )
    row2 = db.list_session_flow_rollups(session_id="s-iso")[0]
    assert row2["llm_attempts"] == 5  # 2 + 3
    assert db.get_rollup_offset("s-iso", "flow:llm_calls") == 12
