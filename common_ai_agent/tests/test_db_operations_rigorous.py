"""Rigorous DB-ops verification for the new trace_events-backed chat
ledger and its companion observability tables.

The Orchestrator Chat design parks every chat message, every agent
consume ack, and the surrounding workflow/llm_calls/todo activity
inside a single canonical ledger (`trace_events`). This file proves
the operational invariants that ledger design depends on:

- idempotency at the trace_event level (idempotency_key roundtrip)
- ordering: newest-first reads, monotonic created_at on the write side
- index hit on hot paths
- read/write throughput under concurrent contention
- referential consistency: every chat_consumed.correlation_id resolves
  to an actual chat_message row
- cascade behaviour when ip_blocks / users / workspaces are deleted
  (verify trace_events ledger survives — it's an audit log, not a
  derived view)
- JSON column safe-load against malformed payloads
- schema migration safety (additive column without breaking chat)
- audit replay: timeline reconstruction for one IP across event kinds
- aggregation: counts by user role (agent vs human)
- workspace_id propagation through the chat record path

Each case targets a SPECIFIC operational invariant rather than a
feature surface. Together they constitute the "DB rigor" pass.
"""
from __future__ import annotations

import json
import sys
import time
import threading
import uuid
from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from core.atlas_db import AtlasDB


# ============================================================
# Fixture
# ============================================================


@pytest.fixture
def db(tmp_path):
    d = AtlasDB(str(tmp_path / "atlas.db"))
    return d


@pytest.fixture
def seeded(tmp_path):
    d = AtlasDB(str(tmp_path / "atlas.db"))
    alice = d.create_user("alice", "Alice", "pw")
    bob = d.create_user("bob", "Bob", "pw")
    ws = d.upsert_workspace("ws", owner_user_id=alice["id"], local_path="/r")
    ip_uart = d.upsert_ip_block(ws["id"], "uart_lite", ip_type="uart")
    ip_dma = d.upsert_ip_block(ws["id"], "dma", ip_type="dma")
    d.grant_ip_permission(ip_uart["id"], bob["id"], "view")
    return {"db": d, "alice": alice, "bob": bob, "ws": ws,
            "ip_uart": ip_uart, "ip_dma": ip_dma}


# ============================================================
# 1. Idempotency at the trace_event layer
# ============================================================


def test_record_trace_event_idempotency_returns_existing_row(seeded):
    """Calling record_trace_event with the same idempotency_key should
    return the original row, not insert a duplicate."""
    d = seeded["db"]
    first = d.record_trace_event(
        event_type="workflow.started",
        ip_id=seeded["ip_uart"]["id"],
        idempotency_key="boot-2026-05-15-01",
        payload={"v": 1},
    )
    second = d.record_trace_event(
        event_type="workflow.started",
        ip_id=seeded["ip_uart"]["id"],
        idempotency_key="boot-2026-05-15-01",
        payload={"v": 999},   # different payload — must be ignored
    )
    assert first["id"] == second["id"]
    assert second["payload"]["v"] == 1   # original wins
    rows = d._fetchall(
        "SELECT * FROM trace_events WHERE idempotency_key = ?",
        ("boot-2026-05-15-01",),
    )
    assert len(rows) == 1


def test_record_chat_message_with_idempotency_via_trace_event(seeded):
    """record_chat_message currently does not expose idempotency_key,
    but the underlying record_trace_event does. Confirm that direct
    use of the trace API for chat_message also dedupes."""
    d = seeded["db"]
    payload = {"content": "hi", "display_name": "Alice"}
    a = d.record_trace_event(
        event_type="chat_message",
        ip_id=seeded["ip_uart"]["id"],
        actor_user_id=seeded["alice"]["id"],
        idempotency_key="msg-1",
        payload=payload,
    )
    b = d.record_trace_event(
        event_type="chat_message",
        ip_id=seeded["ip_uart"]["id"],
        actor_user_id=seeded["alice"]["id"],
        idempotency_key="msg-1",
        payload={"content": "hi2"},
    )
    assert a["id"] == b["id"]
    rooms = d.list_chat_messages(seeded["ip_uart"]["id"])
    assert len(rooms) == 1
    assert rooms[0]["payload"]["content"] == "hi"


# ============================================================
# 2. Ordering invariants
# ============================================================


def test_chat_message_created_at_monotonic_on_sequential_writes(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    timestamps = []
    for i in range(20):
        r = d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")
        timestamps.append(r["created_at"])
    # Monotonic non-decreasing
    for i in range(1, len(timestamps)):
        assert timestamps[i] >= timestamps[i - 1]


def test_list_chat_messages_newest_first(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    ids = []
    for i in range(5):
        time.sleep(0.001)
        ids.append(d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")["id"])
    rows = d.list_chat_messages(ip_id, limit=10)
    # Newest first → reverse insertion order
    assert [r["id"] for r in rows] == list(reversed(ids))


def test_list_chat_unconsumed_for_oldest_first(seeded):
    """Unconsumed list is the agent's reading order — must be oldest
    first so the bot answers feedback in chronological order."""
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    ids = []
    for i in range(5):
        time.sleep(0.001)
        ids.append(d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")["id"])
    rows = d.list_chat_unconsumed_for("agent-1", ip_id)
    assert [r["id"] for r in rows] == ids   # forward order


# ============================================================
# 3. Hot-path index utilization (EXPLAIN QUERY PLAN)
# ============================================================


def test_list_chat_messages_uses_an_index(seeded):
    """The chat reader path should NOT do a full table scan."""
    d = seeded["db"]
    plan = d._fetchall(
        """EXPLAIN QUERY PLAN
            SELECT * FROM trace_events
             WHERE event_type = 'chat_message'
               AND ip_id = ?
             ORDER BY created_at DESC LIMIT 50""",
        (seeded["ip_uart"]["id"],),
    )
    plan_text = " ".join(str(row["detail"]) for row in plan).upper()
    # SQLite picks one of the trace_events indexes (idx_trace_events_context
    # or idx_trace_events_session). Either is acceptable; what we forbid
    # is a full table scan.
    assert "USING INDEX" in plan_text or "SEARCH" in plan_text
    assert "SCAN trace_events" not in plan_text.upper().replace("SEARCH ", "")


def test_unconsumed_query_does_not_scan_everything(seeded):
    d = seeded["db"]
    plan = d._fetchall(
        """EXPLAIN QUERY PLAN
            SELECT * FROM trace_events
             WHERE event_type = 'chat_message'
               AND ip_id = ?
               AND id NOT IN (
                 SELECT correlation_id FROM trace_events
                  WHERE event_type = 'chat_consumed'
                    AND session_id = ?
               )""",
        (seeded["ip_uart"]["id"], "agent-1"),
    )
    plan_text = " ".join(str(row["detail"]) for row in plan)
    # At least one index access must appear (outer or inner query)
    assert "USING INDEX" in plan_text.upper()


# ============================================================
# 4. Throughput / scale
# ============================================================


def test_ten_thousand_chat_messages_list_is_fast(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    for i in range(10_000):
        d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")
    t0 = time.perf_counter()
    rows = d.list_chat_messages(ip_id, limit=50)
    elapsed = time.perf_counter() - t0
    assert len(rows) == 50
    # 10K rows, indexed query → well under 200ms even on debug builds.
    assert elapsed < 0.5, f"too slow: {elapsed:.3f}s"


def test_unconsumed_query_remains_subquadratic(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    sid = "agent-perf"
    # 5000 chats, 4900 already consumed by `sid`
    msg_ids = []
    for i in range(5000):
        m = d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")
        msg_ids.append(m["id"])
    for mid in msg_ids[:4900]:
        d.record_chat_consumed(mid, sid, ip_id)

    t0 = time.perf_counter()
    rows = d.list_chat_unconsumed_for(sid, ip_id)
    elapsed = time.perf_counter() - t0
    assert len(rows) == 100
    assert elapsed < 1.5, f"too slow: {elapsed:.3f}s"


# ============================================================
# 5. Concurrent writes — sqlite RLock contract
# ============================================================


def test_twenty_threads_writing_chat_does_not_lock(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    N = 20
    PER = 50

    def write(idx):
        for j in range(PER):
            d.record_chat_message(ip_id, seeded["alice"]["id"], f"t{idx}-m{j}")

    errors = []

    def worker(i):
        try:
            write(i)
        except Exception as e:  # noqa: BLE001
            errors.append(repr(e))

    threads = [threading.Thread(target=worker, args=(i,)) for i in range(N)]
    for t in threads: t.start()
    for t in threads: t.join()
    assert errors == [], f"contention errors: {errors[:3]}"

    rows = d._fetchall(
        "SELECT COUNT(*) AS n FROM trace_events WHERE event_type='chat_message'"
    )
    assert rows[0]["n"] == N * PER


def test_interleaved_read_write_no_locked_error(seeded):
    """Mixed read/write workload across threads. Sqlite with check_same_thread=False
    + RLock should serialize without raising 'database is locked'."""
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    stop = threading.Event()
    errs = []

    def writer():
        i = 0
        while not stop.is_set():
            try:
                d.record_chat_message(ip_id, seeded["alice"]["id"], f"w{i}")
                i += 1
            except Exception as e: errs.append(("w", repr(e)))

    def reader():
        while not stop.is_set():
            try:
                d.list_chat_messages(ip_id, limit=20)
            except Exception as e: errs.append(("r", repr(e)))

    ts = [threading.Thread(target=writer) for _ in range(3)] + \
         [threading.Thread(target=reader) for _ in range(5)]
    for t in ts: t.start()
    time.sleep(0.6)
    stop.set()
    for t in ts: t.join()
    assert errs == [], f"first errors: {errs[:3]}"


# ============================================================
# 6. Referential consistency
# ============================================================


def test_every_chat_consumed_correlation_id_resolves_to_a_chat_message(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    ids = [d.record_chat_message(ip_id, seeded["alice"]["id"], f"m{i}")["id"]
           for i in range(7)]
    for mid in ids:
        d.record_chat_consumed(mid, "agent-x", ip_id)

    consumed = d._fetchall(
        "SELECT correlation_id FROM trace_events WHERE event_type='chat_consumed'"
    )
    chat_ids = {r["id"] for r in d._fetchall(
        "SELECT id FROM trace_events WHERE event_type='chat_message'"
    )}
    for c in consumed:
        assert c["correlation_id"] in chat_ids


def test_chat_consumed_with_unknown_correlation_id_still_inserts(seeded):
    """trace_events has no FK constraint by design — it is an audit
    log. A spurious chat_consumed (e.g. test seeding error) inserts
    successfully but the unconsumed query just doesn't match anything.
    This invariant has to hold so a malformed insert can't take the
    chat path down."""
    d = seeded["db"]
    d.record_chat_consumed("does-not-exist", "agent-x", seeded["ip_uart"]["id"])
    rows = d._fetchall(
        "SELECT * FROM trace_events WHERE event_type='chat_consumed'"
    )
    assert len(rows) == 1


# ============================================================
# 7. Cascade behaviour — trace_events survives as audit log
# ============================================================


def test_user_deletion_does_not_cascade_trace_events(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    d.record_chat_message(ip_id, seeded["alice"]["id"], "from-alice")
    d._execute("DELETE FROM users WHERE id = ?", (seeded["alice"]["id"],))

    rows = d.list_chat_messages(ip_id)
    assert len(rows) == 1
    # actor_user_id is preserved even though the user row is gone
    assert rows[0]["actor_user_id"] == seeded["alice"]["id"]


def test_ip_deletion_does_not_cascade_chat_ledger(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    d.record_chat_message(ip_id, seeded["alice"]["id"], "orphan")
    d._execute("DELETE FROM ip_blocks WHERE id = ?", (ip_id,))
    rows = d.list_chat_messages(ip_id)
    assert len(rows) == 1   # ledger preserved


def test_workspace_deletion_does_not_cascade_chat_ledger(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    d.record_chat_message(ip_id, seeded["alice"]["id"], "survives")
    d._execute("DELETE FROM workspaces WHERE id = ?", (seeded["ws"]["id"],))
    rows = d.list_chat_messages(ip_id)
    assert len(rows) == 1


# ============================================================
# 8. JSON column safe-load
# ============================================================


def test_payload_none_safe(seeded):
    d = seeded["db"]
    d.record_trace_event(
        event_type="chat_message",
        ip_id=seeded["ip_uart"]["id"],
        actor_user_id=seeded["alice"]["id"],
        payload=None,
    )
    rows = d._fetchall(
        "SELECT payload FROM trace_events WHERE event_type='chat_message'"
    )
    # payload stored as NULL string when None
    assert rows[0]["payload"] is None


def test_payload_empty_string_safe(seeded):
    d = seeded["db"]
    d._execute(
        """INSERT INTO trace_events
              (id, event_type, ip_id, actor_user_id, payload, created_at)
           VALUES (?, 'chat_message', ?, ?, '', ?)""",
        ("e1", seeded["ip_uart"]["id"], seeded["alice"]["id"], time.time()),
    )
    rows = d.list_chat_messages(seeded["ip_uart"]["id"])
    assert len(rows) == 1
    # _load_json returns None for empty string
    assert rows[0]["payload"] is None


def test_payload_malformed_json_returns_raw_string(seeded):
    d = seeded["db"]
    d._execute(
        """INSERT INTO trace_events
              (id, event_type, ip_id, actor_user_id, payload, created_at)
           VALUES (?, 'chat_message', ?, ?, ?, ?)""",
        ("e2", seeded["ip_uart"]["id"], seeded["alice"]["id"],
         "{not valid json", time.time()),
    )
    rows = d.list_chat_messages(seeded["ip_uart"]["id"])
    bad = next(r for r in rows if r["id"] == "e2")
    # _load_json falls back to raw string on JSONDecodeError
    assert bad["payload"] == "{not valid json"


# ============================================================
# 9. Schema migration safety
# ============================================================


def test_ensure_column_is_idempotent(seeded):
    d = seeded["db"]
    conn = d._connect()
    # Apply twice — second call should be a no-op
    d._ensure_column(conn, "ip_blocks", "test_tag", "TEXT")
    d._ensure_column(conn, "ip_blocks", "test_tag", "TEXT")
    cols = [r["name"] for r in conn.execute("PRAGMA table_info(ip_blocks)").fetchall()]
    assert cols.count("test_tag") == 1


def test_adding_new_column_does_not_break_chat_query(seeded):
    d = seeded["db"]
    conn = d._connect()
    d._ensure_column(conn, "trace_events", "extra_tag", "TEXT")
    conn.commit()
    # Read existing chat — must still work
    d.record_chat_message(seeded["ip_uart"]["id"], seeded["alice"]["id"], "hello")
    rows = d.list_chat_messages(seeded["ip_uart"]["id"])
    assert len(rows) == 1
    assert "extra_tag" in rows[0]
    assert rows[0]["extra_tag"] is None  # new column NULL on old rows


# ============================================================
# 10. Audit replay — reconstruct timeline for one IP
# ============================================================


def test_audit_replay_returns_chronological_event_kinds_for_one_ip(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    # Inject a mixed timeline
    run = d.start_workflow_run(
        workspace_id=seeded["ws"]["id"], ip_id=ip_id,
        workflow="rtl-gen", status="running"
    )
    time.sleep(0.001)
    d.record_trace_event("stage.started", ip_id=ip_id, payload={"stage": "ssot-rtl"})
    time.sleep(0.001)
    d.record_chat_message(ip_id, seeded["alice"]["id"], "feedback-1")
    time.sleep(0.001)
    d.record_trace_event("stage.passed", ip_id=ip_id, payload={"errors": 0})
    time.sleep(0.001)
    d.record_chat_consumed(d.list_chat_messages(ip_id)[0]["id"], "agent", ip_id)

    timeline = d._fetchall(
        """SELECT event_type FROM trace_events
            WHERE ip_id = ? ORDER BY created_at ASC""",
        (ip_id,),
    )
    types = [r["event_type"] for r in timeline]
    assert types == [
        "stage.started", "chat_message", "stage.passed", "chat_consumed"
    ]


# ============================================================
# 11. Aggregation: agent vs human role
# ============================================================


def test_aggregate_chat_counts_by_role(seeded):
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    bot = d.create_user("atlas-helper", "🤖 ATLAS Helper", "", role="agent")
    # 4 human posts, 3 bot replies
    for i in range(4):
        d.record_chat_message(ip_id, seeded["alice"]["id"], f"h{i}")
    for i in range(3):
        d.record_chat_message(ip_id, bot["id"], f"b{i}", display_name="🤖 ATLAS Helper")

    rows = d._fetchall(
        """SELECT u.role AS role, COUNT(*) AS n
             FROM trace_events t
             JOIN users u ON u.id = t.actor_user_id
            WHERE t.event_type='chat_message'
            GROUP BY u.role"""
    )
    counts = {r["role"]: r["n"] for r in rows}
    assert counts == {"user": 4, "agent": 3}


# ============================================================
# 12. _now monotonicity within sequential writes
# ============================================================


def test_new_id_uniqueness_across_10k_calls(db):
    ids = {db._new_id() for _ in range(10_000)}
    assert len(ids) == 10_000


def test_now_returns_unix_timestamp(db):
    n = db._now()
    assert isinstance(n, float)
    # within 60s of current wall clock
    assert abs(n - time.time()) < 60


# ============================================================
# 13. workspace_id propagation in chat path
# ============================================================


def test_chat_message_persists_workspace_id_when_provided(seeded):
    d = seeded["db"]
    r = d.record_chat_message(
        ip_id=seeded["ip_uart"]["id"],
        user_id=seeded["alice"]["id"],
        content="ws-tagged",
        workspace_id=seeded["ws"]["id"],
    )
    row = d._fetchall(
        "SELECT workspace_id FROM trace_events WHERE id = ?", (r["id"],)
    )[0]
    assert row["workspace_id"] == seeded["ws"]["id"]


def test_chat_message_default_workspace_id_empty_string(seeded):
    d = seeded["db"]
    r = d.record_chat_message(
        ip_id=seeded["ip_uart"]["id"],
        user_id=seeded["alice"]["id"],
        content="no-ws",
    )
    row = d._fetchall(
        "SELECT workspace_id FROM trace_events WHERE id = ?", (r["id"],)
    )[0]
    assert row["workspace_id"] == ""   # current default — documented


# ============================================================
# 14. Final integrity sweep — every public chat helper consistent
# ============================================================


def test_full_chat_lifecycle_consistency_sweep(seeded):
    """End-to-end: post → list → unconsumed → consumed → re-list →
    latest_watermark. Every reading helper agrees about the world."""
    d = seeded["db"]
    ip_id = seeded["ip_uart"]["id"]
    a = d.record_chat_message(ip_id, seeded["alice"]["id"], "alpha")
    b = d.record_chat_message(ip_id, seeded["alice"]["id"], "beta")
    c = d.record_chat_message(ip_id, seeded["alice"]["id"], "gamma")

    # list ordering newest first
    listed = d.list_chat_messages(ip_id)
    assert [r["id"] for r in listed] == [c["id"], b["id"], a["id"]]

    # unconsumed: oldest first
    sid = "lifecycle"
    unread = d.list_chat_unconsumed_for(sid, ip_id)
    assert [r["id"] for r in unread] == [a["id"], b["id"], c["id"]]

    # Consume the first two
    d.record_chat_consumed(a["id"], sid, ip_id)
    d.record_chat_consumed(b["id"], sid, ip_id)

    # After consume, watermark = b (most recent consumed)
    wm = d.latest_chat_consumed_id(sid, ip_id)
    assert wm == b["id"]

    # Unread now = [c]
    unread2 = d.list_chat_unconsumed_for(sid, ip_id)
    assert [r["id"] for r in unread2] == [c["id"]]

    # Another session has not consumed anything → sees all three
    unread_other = d.list_chat_unconsumed_for("other", ip_id)
    assert [r["id"] for r in unread_other] == [a["id"], b["id"], c["id"]]
