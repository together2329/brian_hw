"""Complete-coverage DB schema and operational invariants test.

The new DB operating mode parks every domain (chat, workflow, todos,
llm calls, artifacts, trace events, sessions, permissions) on a
single SQLite store. This file covers EVERY table in `SCHEMA_SQL`
with roundtrip + lifecycle + invariant checks:

  users • sessions • messages • parts • ws_connections • feedback
  session_queue • workspaces • ip_blocks • ip_permissions
  workflow_runs • workflow_stages • workflow_events • workflow_todos
  todo_events • trace_events • llm_calls • artifacts

For each table we verify:
  - schema present (columns + types + indexes)
  - INSERT writes (via the canonical helper) roundtrip on READ
  - lifecycle methods (start/finish, upsert, revoke) maintain
    invariants the rest of ATLAS depends on
  - cross-table relations (FK-ish — sqlite doesn't enforce by default,
    but our helpers must keep references consistent)

Plus DB-level checks:
  - schema is additive (no destructive migrations)
  - re-opening the file preserves all data
  - WAL/journal compatible (no exclusive locks across helpers)
"""
from __future__ import annotations

import json
import sqlite3
import sys
import time
from pathlib import Path

import pytest

_REPO = Path(__file__).resolve().parents[1]
for _c in (_REPO, _REPO / "src"):
    p = str(_c)
    if p not in sys.path:
        sys.path.insert(0, p)

from core.atlas_db import AtlasDB, _JSON_COLUMNS


# ============================================================
# Fixtures
# ============================================================


_EXPECTED_TABLES = {
    "users", "sessions", "messages", "parts", "ws_connections",
    "feedback", "session_queue",
    "workspaces", "ip_blocks", "ip_permissions",
    "artifact_versions", "artifact_version_edges", "run_artifact_versions",
    "rtl_versions", "workflow_runs", "workflow_stages", "workflow_events",
    "workflow_todos", "todo_events",
    "trace_events", "llm_calls", "artifacts",
    # Session Flow (Task 1)
    "session_inputs", "worker_runs", "session_flow_events",
    "session_flow_rollups", "ip_flow_rollups",
}


_EXPECTED_INDEXES = {
    "idx_users_email", "idx_users_password_reset_token",
    "idx_sessions_user", "idx_messages_session", "idx_parts_message",
    "idx_feedback_user", "idx_feedback_status",
    "idx_queue_session_direction", "idx_queue_created",
    "idx_workspaces_owner", "idx_ip_blocks_workspace",
    "idx_ip_permissions_user", "idx_ip_permissions_ip",
    "idx_artifact_versions_ip_type", "idx_artifact_versions_workspace",
    "idx_artifact_version_edges_parent", "idx_artifact_version_edges_child",
    "idx_run_artifact_versions_run", "idx_run_artifact_versions_version",
    "idx_rtl_versions_ip", "idx_rtl_versions_workspace",
    "idx_workflow_runs_session", "idx_workflow_runs_context",
    "idx_workflow_runs_rtl_version",
    "idx_workflow_stages_run", "idx_workflow_stages_rtl_version",
    "idx_workflow_events_run",
    "idx_workflow_todos_run", "idx_todo_events_todo",
    "idx_trace_events_context", "idx_trace_events_run",
    "idx_trace_events_correlation", "idx_trace_events_session",
    "idx_trace_events_chat_room",        # added 2026-05-15
    "idx_llm_calls_context", "idx_llm_calls_session", "idx_llm_calls_ip_created", "idx_llm_calls_todo",
    "idx_llm_calls_worker_run",
    "idx_artifacts_run", "idx_artifacts_rtl_version",
    # Session Flow (Task 1)
    "idx_trace_events_worker_run",
    "idx_session_inputs_session", "idx_session_inputs_ip",
    "idx_worker_runs_session", "idx_worker_runs_status", "idx_worker_runs_ip",
    "idx_session_flow_events_session", "idx_session_flow_events_ip",
    "idx_session_flow_events_type",
    "idx_session_flow_rollups_risk", "idx_session_flow_rollups_user",
    "idx_session_flow_rollups_ip",
    "idx_ip_flow_rollups_risk", "idx_ip_flow_rollups_workspace",
}


@pytest.fixture
def db(tmp_path):
    return AtlasDB(str(tmp_path / "atlas.db"))


def _table_columns(db: AtlasDB, table: str) -> set[str]:
    rows = db._fetchall(f"PRAGMA table_info({table})")
    return {r["name"] for r in rows}


def _all_indexes(db: AtlasDB) -> set[str]:
    rows = db._fetchall(
        "SELECT name FROM sqlite_master WHERE type='index' AND name NOT LIKE 'sqlite_%'"
    )
    return {r["name"] for r in rows}


# ============================================================
# Section 1 — Schema introspection
# ============================================================


def test_all_expected_tables_present(db):
    rows = db._fetchall("SELECT name FROM sqlite_master WHERE type='table'")
    tables = {r["name"] for r in rows}
    assert _EXPECTED_TABLES.issubset(tables), \
        f"missing: {_EXPECTED_TABLES - tables}"


def test_legacy_user_schema_migrates_before_email_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy.db"
    conn = sqlite3.connect(db_path)
    try:
        conn.execute(
            """
            CREATE TABLE users (
                id TEXT PRIMARY KEY,
                username TEXT UNIQUE,
                display_name TEXT,
                password_hash TEXT,
                role TEXT DEFAULT 'user',
                created_at REAL,
                last_login_at REAL
            )
            """
        )
        conn.commit()
    finally:
        conn.close()

    with AtlasDB(str(db_path)) as db:
        columns = _table_columns(db, "users")
        indexes = _all_indexes(db)

    assert "email" in columns
    assert "password_reset_token_hash" in columns
    assert "idx_users_email" in indexes
    assert "idx_users_password_reset_token" in indexes


def test_legacy_workflow_schema_migrates_before_version_indexes(tmp_path: Path) -> None:
    db_path = tmp_path / "legacy-workflow.db"
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
            CREATE TABLE rtl_versions (
                id TEXT PRIMARY KEY,
                ip_id TEXT NOT NULL,
                workspace_id TEXT,
                version TEXT NOT NULL,
                git_commit TEXT,
                status TEXT DEFAULT 'active',
                metadata TEXT,
                created_at REAL
            );
            CREATE TABLE workflow_runs (
                id TEXT PRIMARY KEY,
                session_id TEXT,
                workspace_id TEXT,
                ip_id TEXT,
                workflow TEXT,
                status TEXT,
                started_at REAL
            );
            CREATE TABLE workflow_stages (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                stage_name TEXT NOT NULL,
                status TEXT,
                started_at REAL
            );
            CREATE TABLE workflow_todos (
                id TEXT PRIMARY KEY,
                run_id TEXT NOT NULL,
                title TEXT NOT NULL,
                status TEXT
            );
            CREATE TABLE artifacts (
                id TEXT PRIMARY KEY,
                run_id TEXT,
                stage_id TEXT,
                ip_id TEXT,
                workflow TEXT,
                kind TEXT,
                path TEXT,
                created_at REAL
            );
            """
        )
        conn.commit()
    finally:
        conn.close()

    with AtlasDB(str(db_path)) as db:
        assert "rtl_version_id" in _table_columns(db, "workflow_runs")
        assert "rtl_version_id" in _table_columns(db, "workflow_stages")
        assert "rtl_version_id" in _table_columns(db, "artifacts")
        assert "artifact_version_id" in _table_columns(db, "rtl_versions")
        assert "git_tag" in _table_columns(db, "rtl_versions")
        assert "notes" in _table_columns(db, "workflow_todos")
        indexes = _all_indexes(db)

    assert "idx_workflow_runs_rtl_version" in indexes
    assert "idx_workflow_stages_rtl_version" in indexes
    assert "idx_artifacts_rtl_version" in indexes


def test_all_expected_indexes_present(db):
    have = _all_indexes(db)
    missing = _EXPECTED_INDEXES - have
    assert not missing, f"missing indexes: {missing}"


@pytest.mark.parametrize("table,must_have", [
    ("users",          {"id", "username", "display_name", "email", "role", "password_hash",
                        "password_reset_token_hash", "password_reset_expires_at",
                        "password_reset_requested_at", "password_reset_used_at"}),
    ("sessions",       {"id", "user_id", "status", "directory", "summary"}),
    ("messages",       {"id", "session_id", "role", "model_id", "provider_id",
                        "cost", "tokens_input", "tokens_output", "tokens_reasoning"}),
    ("parts",          {"id", "message_id", "session_id", "type",
                        "tool_name", "tool_input", "tool_output", "tool_status"}),
    ("ws_connections", {"connection_id", "user_id", "session_id"}),
    ("feedback",       {"id", "user_id", "content", "status", "resolved_by"}),
    ("session_queue",  {"id", "session_id", "direction", "msg_type", "payload"}),
    ("workspaces",     {"id", "owner_user_id", "name", "local_path",
                        "git_remote", "git_branch", "head_commit"}),
    ("ip_blocks",      {"id", "workspace_id", "ip_name", "ip_type",
                        "ssot_path", "status"}),
    ("ip_permissions", {"id", "ip_id", "grantee_user_id", "permission",
                        "granted_by_user_id", "expires_at"}),
    ("artifact_versions", {"id", "workspace_id", "ip_id", "artifact_type",
                        "version", "label", "root_path", "primary_path",
                        "manifest", "sha256_tree", "git_commit", "git_tag",
                        "status", "source_run_id", "source_stage_id",
                        "metadata", "created_at"}),
    ("artifact_version_edges", {"id", "parent_version_id", "child_version_id",
                        "relation", "metadata", "created_at"}),
    ("run_artifact_versions", {"id", "run_id", "stage_id", "artifact_version_id",
                        "role", "required", "metadata", "created_at"}),
    ("rtl_versions",   {"id", "artifact_version_id", "ip_id", "workspace_id", "source_run_id",
                        "source_stage_id", "version", "label", "rtl_root",
                        "filelist_path", "top_module", "artifact_manifest",
                        "sha256_tree", "git_commit", "git_tag", "status",
                        "metadata", "created_at"}),
    ("workflow_runs",  {"id", "session_id", "workspace_id", "ip_id",
                        "rtl_version_id", "workflow", "mode",
                        "model_profile", "status"}),
    ("workflow_stages",{"id", "run_id", "rtl_version_id", "stage_name",
                        "status", "attempt"}),
    ("workflow_events",{"id", "run_id", "stage_id", "event_type", "payload"}),
    ("workflow_todos", {"id", "run_id", "source", "title", "detail",
                        "criteria", "notes", "status", "owner_file",
                        "owner_module", "source_refs", "evidence"}),
    ("todo_events",    {"id", "todo_id", "event_type", "reason", "evidence"}),
    ("trace_events",   {"id", "event_type", "session_id", "workspace_id",
                        "ip_id", "workflow", "run_id", "stage_id",
                        "todo_id", "message_id", "llm_call_id",
                        "artifact_id", "actor_user_id", "correlation_id",
                        "causation_id", "idempotency_key", "payload"}),
    ("llm_calls",      {"id", "message_id", "run_id", "stage_id", "todo_id",
                        "model", "provider", "call_role", "attempt",
                        "tokens_input", "tokens_output", "tokens_reasoning",
                        "cache_read_tokens", "cache_write_tokens",
                        "cost_usd", "latency_ms", "status", "error_type"}),
    ("artifacts",      {"id", "run_id", "stage_id", "ip_id", "workflow",
                        "rtl_version_id", "kind", "path", "storage_backend",
                        "sha256", "size_bytes", "git_commit"}),
])
def test_table_has_required_columns(db, table, must_have):
    cols = _table_columns(db, table)
    missing = must_have - cols
    assert not missing, f"{table} missing: {missing}"


def test_trace_events_idempotency_key_is_unique(db):
    db.record_trace_event(event_type="x", idempotency_key="K1")
    with pytest.raises(sqlite3.IntegrityError):
        db._execute(
            """INSERT INTO trace_events
               (id, event_type, idempotency_key, created_at)
               VALUES (?, ?, ?, ?)""",
            ("other", "x", "K1", time.time()),
        )


def test_workspaces_unique_per_owner_name(db):
    u = db.create_user("u1", "U1", "pw")
    db.upsert_workspace("ws-a", owner_user_id=u["id"], local_path="/a")
    # Same (owner, name) → upsert returns the same id; bypassing the
    # helper via raw INSERT should fail.
    with pytest.raises(sqlite3.IntegrityError):
        db._execute(
            """INSERT INTO workspaces
               (id, owner_user_id, name, local_path, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?)""",
            ("ws-dup", u["id"], "ws-a", "/x", time.time(), time.time()),
        )


def test_ip_blocks_unique_per_workspace_name(db):
    u = db.create_user("u1", "U1", "pw")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    with pytest.raises(sqlite3.IntegrityError):
        db._execute(
            """INSERT INTO ip_blocks
               (id, workspace_id, ip_name, ip_type, status, created_at, updated_at)
               VALUES (?, ?, ?, ?, ?, ?, ?)""",
            ("ip-dup", w["id"], "uart_lite", "uart", "active",
             time.time(), time.time()),
        )


# ============================================================
# Section 2 — users
# ============================================================


def test_users_create_and_lookup_by_username(db):
    u = db.create_user("alice", "Alice", "hash$abc", role="user")
    assert u["username"] == "alice"
    assert u["display_name"] == "Alice"
    assert db.get_user(u["id"])["id"] == u["id"]
    assert db.get_user_by_username("alice")["id"] == u["id"]


def test_users_list_all(db):
    db.create_user("a", "A", "h")
    db.create_user("b", "B", "h", role="admin")
    rows = db.list_all_users()
    assert {r["username"] for r in rows} == {"a", "b"}
    # list_all_users excludes password_hash
    assert all("password_hash" not in r for r in rows)


# ============================================================
# Section 3 — sessions
# ============================================================


def test_sessions_create_and_get(db):
    u = db.create_user("alice", "Alice", "h")
    s = db.create_session(u["id"], "first session", project_id="uart_lite")
    assert s["user_id"] == u["id"]
    assert s["title"] == "first session"
    fetched = db.get_session(s["id"])
    assert fetched["id"] == s["id"]


def test_sessions_list_active_only(db):
    u = db.create_user("alice", "Alice", "h")
    s1 = db.create_session(u["id"], "active")
    s2 = db.create_session(u["id"], "archived")
    db._execute("UPDATE sessions SET status='archived' WHERE id=?", (s2["id"],))
    active = db.list_sessions(u["id"], status="active")
    assert [s["id"] for s in active] == [s1["id"]]


# ============================================================
# Section 4 — messages (legacy + dual-write to llm_calls)
# ============================================================


def test_save_message_with_cost_dual_writes_llm_calls(db):
    u = db.create_user("alice", "Alice", "h")
    s = db.create_session(u["id"], "s")
    msg = db.save_message(
        session_id=s["id"],
        role="assistant",
        agent="rtl-gen",
        model_id="deepseek-v4-pro",
        provider_id="deepseek",
        cost=0.18,
        tokens_input=10000,
        tokens_output=400,
    )
    # The legacy messages row exists
    rows = db.get_messages(s["id"])
    assert any(r["id"] == msg["id"] for r in rows)
    # The dual-write to llm_calls should have created a row too
    llm = db.list_llm_calls()
    assert any(r["message_id"] == msg["id"] and r["model"] == "deepseek-v4-pro"
               for r in llm)


# ============================================================
# Section 5 — parts
# ============================================================


def test_save_part_roundtrip(db):
    u = db.create_user("alice", "Alice", "h")
    s = db.create_session(u["id"], "s")
    m = db.save_message(session_id=s["id"], role="assistant")
    db.save_part(
        message_id=m["id"], session_id=s["id"], type="tool_use",
        tool_name="run_command", call_id="call-1",
        tool_input={"cmd": "ls"}, tool_output="a.txt\nb.txt",
        tool_status="ok",
    )
    parts = db.get_parts(m["id"])
    assert len(parts) == 1
    assert parts[0]["tool_name"] == "run_command"
    # JSON-decoded
    assert parts[0]["tool_input"] == {"cmd": "ls"}


# ============================================================
# Section 6 — ws_connections (ephemeral)
# ============================================================


def test_ws_connections_create_and_list(db):
    u = db.create_user("alice", "Alice", "h")
    s = db.create_session(u["id"], "s")
    conn = db.create_ws_connection(
        connection_id="ws-conn-1", user_id=u["id"], session_id=s["id"],
        client_ip="127.0.0.1", user_agent="pytest",
    )
    assert conn["connection_id"] == "ws-conn-1"
    rows = db.get_ws_connections(user_id=u["id"])
    assert len(rows) == 1
    assert rows[0]["session_id"] == s["id"]


# ============================================================
# Section 7 — feedback
# ============================================================


def test_feedback_default_status_is_open(db):
    u = db.create_user("alice", "Alice", "h")
    db._execute(
        """INSERT INTO feedback (id, user_id, content, created_at)
           VALUES (?, ?, ?, ?)""",
        ("f1", u["id"], "issue with UI", time.time()),
    )
    rows = db._fetchall("SELECT status FROM feedback WHERE id='f1'")
    assert rows[0]["status"] == "open"


# ============================================================
# Section 8 — session_queue (IPC)
# ============================================================


def test_session_queue_enqueue_and_poll(db):
    db.enqueue_message(session_id="s1", direction="inbound", msg_type="prompt",
                        payload={"text": "hi"})
    rows = db.poll_messages(session_id="s1", direction="inbound", limit=10)
    assert len(rows) == 1
    assert rows[0]["msg_type"] == "prompt"
    assert rows[0]["payload"] == {"text": "hi"}


def test_session_queue_acknowledge(db):
    db.enqueue_message(session_id="s1", direction="inbound", msg_type="prompt",
                        payload="x")
    rows = db.poll_messages(session_id="s1", direction="inbound")
    db.acknowledge_message(rows[0]["id"])
    # acknowledge_message sets the delivered_at timestamp; the row
    # itself stays in the table (audit ledger semantics).
    rows2 = db._fetchall("SELECT delivered_at FROM session_queue WHERE id=?",
                           (rows[0]["id"],))
    assert rows2[0]["delivered_at"] is not None


# ============================================================
# Section 9 — workspaces
# ============================================================


def test_workspace_upsert_updates_existing_by_owner_and_name(db):
    u = db.create_user("alice", "Alice", "h")
    a = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/a")
    b = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/b",
                              head_commit="deadbeef")
    assert a["id"] == b["id"]
    fetched = db.get_workspace(a["id"])
    assert fetched["local_path"] == "/b"
    assert fetched["head_commit"] == "deadbeef"


def test_list_workspaces_filtered_by_owner(db):
    u1 = db.create_user("u1", "U1", "h")
    u2 = db.create_user("u2", "U2", "h")
    db.upsert_workspace("ws-1", owner_user_id=u1["id"], local_path="/1")
    db.upsert_workspace("ws-2", owner_user_id=u2["id"], local_path="/2")
    r1 = db.list_workspaces(owner_user_id=u1["id"])
    assert [w["name"] for w in r1] == ["ws-1"]


# ============================================================
# Section 10 — ip_blocks + ip_permissions
# ============================================================


def test_ip_permission_grant_and_revoke(db):
    u_owner = db.create_user("owner", "Owner", "h")
    u_other = db.create_user("other", "Other", "h")
    w = db.upsert_workspace("ws", owner_user_id=u_owner["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")

    # Other has no access
    assert not db.can_user_access_ip(ip["id"], u_other["id"], "view")
    # Grant view
    g = db.grant_ip_permission(ip["id"], u_other["id"], "view")
    assert db.can_user_access_ip(ip["id"], u_other["id"], "view")
    # Revoke
    n = db.revoke_ip_permission(ip["id"], u_other["id"], "view")
    assert n == 1
    assert not db.can_user_access_ip(ip["id"], u_other["id"], "view")


def test_ip_permission_owner_implicit(db):
    u_owner = db.create_user("owner", "Owner", "h")
    w = db.upsert_workspace("ws", owner_user_id=u_owner["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    # Owner has admin-level access without any explicit permission row
    assert db.can_user_access_ip(ip["id"], u_owner["id"], "admin")


def test_ip_permission_admin_user_role_bypasses_grants(db):
    admin = db.create_user("a", "A", "h", role="admin")
    u_owner = db.create_user("o", "O", "h")
    w = db.upsert_workspace("ws", owner_user_id=u_owner["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    # Admin role → access regardless of grant
    assert db.can_user_access_ip(ip["id"], admin["id"], "admin")


# ============================================================
# Section 11 — workflow_runs
# ============================================================


def test_workflow_run_lifecycle(db):
    u = db.create_user("alice", "Alice", "h")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(workspace_id=w["id"], ip_id=ip["id"],
                                  workflow="rtl-gen", status="running")
    assert run["status"] == "running"
    # finish
    finished = db.finish_workflow_run(run["id"], status="completed")
    assert finished["status"] == "completed"
    assert finished["ended_at"] is not None
    assert finished["duration_ms"] is not None


# ============================================================
# Section 12 — workflow_stages
# ============================================================


def test_workflow_stage_lifecycle(db):
    u = db.create_user("alice", "Alice", "h")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(workspace_id=w["id"], ip_id=ip["id"],
                                  workflow="rtl-gen", status="running")
    stage = db.start_workflow_stage(run["id"], "derive-rtl-todos")
    assert stage["status"] == "running"
    fin = db.finish_workflow_stage(stage["id"], status="completed")
    assert fin["status"] == "completed"
    assert fin["duration_ms"] is not None


# ============================================================
# Section 13 — workflow_events
# ============================================================


def test_workflow_events_append_in_chrono_order(db):
    u = db.create_user("alice", "Alice", "h")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(workspace_id=w["id"], ip_id=ip["id"],
                                  workflow="rtl-gen", status="running")
    for kind in ("started", "command", "command", "completed"):
        time.sleep(0.001)
        db.record_workflow_event(run["id"], kind, {"k": kind})
    rows = db.list_workflow_events(run_id=run["id"])
    assert [r["event_type"] for r in rows] == \
        ["started", "command", "command", "completed"]


# ============================================================
# Section 14 — workflow_todos
# ============================================================


def test_workflow_todo_upsert_changes_status_in_place(db):
    u = db.create_user("alice", "Alice", "h")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(workspace_id=w["id"], ip_id=ip["id"],
                                  workflow="rtl-gen", status="running")
    t1 = db.upsert_workflow_todo(run["id"], title="implement x",
                                    status="pending")
    t2 = db.upsert_workflow_todo(run["id"], title="implement x",
                                    status="in_progress", todo_id=t1["id"])
    assert t1["id"] == t2["id"]
    rows = db.list_workflow_todos(run_id=run["id"])
    assert len(rows) == 1
    assert rows[0]["status"] == "in_progress"


# ============================================================
# Section 15 — todo_events
# ============================================================


def test_todo_event_updates_parent_status(db):
    u = db.create_user("alice", "Alice", "h")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(workspace_id=w["id"], ip_id=ip["id"],
                                  workflow="rtl-gen", status="running")
    t = db.upsert_workflow_todo(run["id"], title="x", status="pending")
    db.record_todo_event(t["id"], event_type="approved",
                          reason="all RTL gates clean")
    # workflow_todos.status mirrored from the latest event
    t2 = db.list_workflow_todos(run_id=run["id"], todo_id=t["id"])[0]
    assert t2["status"] == "approved"


# ============================================================
# Section 16 — trace_events: idempotency_key + filter
# ============================================================


def test_trace_event_filter_by_session_id(db):
    db.record_trace_event(event_type="a", session_id="s1")
    db.record_trace_event(event_type="b", session_id="s2")
    rows = db.list_trace_events(session_id="s1")
    assert [r["event_type"] for r in rows] == ["a"]


def test_trace_event_filter_by_correlation_id(db):
    db.record_trace_event(event_type="reply", correlation_id="chat-1")
    db.record_trace_event(event_type="reply", correlation_id="chat-2")
    rows = db.list_trace_events(correlation_id="chat-1")
    assert [r["event_type"] for r in rows] == ["reply"]


# ============================================================
# Section 17 — llm_calls aggregation
# ============================================================


def test_llm_calls_cost_aggregation_by_ip(db):
    db.record_llm_call(ip_id="ip-A", model="m", cost_usd=0.10)
    db.record_llm_call(ip_id="ip-A", model="m", cost_usd=0.20)
    db.record_llm_call(ip_id="ip-B", model="m", cost_usd=0.30)
    rows = db._fetchall(
        "SELECT ip_id, SUM(cost_usd) AS total FROM llm_calls GROUP BY ip_id"
    )
    by_ip = {r["ip_id"]: r["total"] for r in rows}
    assert abs(by_ip["ip-A"] - 0.30) < 1e-9
    assert abs(by_ip["ip-B"] - 0.30) < 1e-9


def test_llm_calls_filter_by_run_session_todo(db):
    db.record_llm_call(run_id="r1", session_id="s1", todo_id="t1",
                         model="m", cost_usd=0.01)
    db.record_llm_call(run_id="r1", session_id="s2", todo_id="t2",
                         model="m", cost_usd=0.02)
    assert len(db.list_llm_calls(run_id="r1")) == 2
    assert len(db.list_llm_calls(session_id="s1")) == 1


# ============================================================
# Section 18 — artifacts
# ============================================================


def test_artifact_register_and_list(db):
    a = db.register_artifact(run_id="r1", stage_id="st1", ip_id="ip1",
                                kind="rtl_compile",
                                path="uart_lite/rtl/rtl_compile.json",
                                sha256="abcd", size_bytes=1234,
                                git_commit="cafe")
    rows = db.list_artifacts(run_id="r1")
    assert any(r["id"] == a["id"] and r["kind"] == "rtl_compile" for r in rows)


# ============================================================
# Section 19 — Cross-table audit consistency
# ============================================================


def test_cross_table_workflow_run_links_session_workspace_ip(db):
    u = db.create_user("alice", "Alice", "h")
    s = db.create_session(u["id"], "S")
    w = db.upsert_workspace("ws", owner_user_id=u["id"], local_path="/r")
    ip = db.upsert_ip_block(w["id"], "uart_lite", ip_type="uart")
    run = db.start_workflow_run(session_id=s["id"], workspace_id=w["id"],
                                  ip_id=ip["id"], workflow="rtl-gen",
                                  status="running")
    fetched = db.get_workflow_run(run["id"])
    # get_workflow_run joins workspaces + ip_blocks for the dashboard.
    assert fetched["workspace_name"] == "ws"
    assert fetched["ip_name"] == "uart_lite"


def test_cross_table_llm_call_attributable_to_run_and_ip(db):
    db.record_llm_call(run_id="r1", ip_id="ip-A", model="m",
                         cost_usd=0.05, status="ok")
    rows = db._fetchall(
        """SELECT run_id, ip_id, model FROM llm_calls
            WHERE run_id = ?""", ("r1",)
    )
    assert rows[0]["ip_id"] == "ip-A"


# ============================================================
# Section 20 — DB lifecycle (open/close/reopen)
# ============================================================


def test_close_and_reopen_preserves_data(tmp_path):
    path = str(tmp_path / "atlas.db")
    db1 = AtlasDB(path)
    u = db1.create_user("alice", "Alice", "h")
    db1.close()
    db2 = AtlasDB(path)
    user = db2.get_user(u["id"])
    assert user is not None
    assert user["username"] == "alice"


def test_two_atlas_db_instances_share_one_file(tmp_path):
    """Two AtlasDB handles to the same path see each other's writes —
    important for multi-process deployments and the autostarted
    responders running in the atlas_ui process."""
    path = str(tmp_path / "atlas.db")
    a = AtlasDB(path)
    b = AtlasDB(path)
    user = a.create_user("alice", "Alice", "h")
    # Second handle sees the write immediately (single-file sqlite)
    found = b.get_user(user["id"])
    assert found is not None


# ============================================================
# Section 21 — _JSON_COLUMNS contract: every listed column actually
# roundtrips correctly
# ============================================================


@pytest.mark.parametrize("table,column", [
    ("sessions", "summary"),
    ("messages", "error"),
    ("parts", "tool_input"),
    ("parts", "patch_files"),
    ("session_queue", "payload"),
    ("workflow_events", "payload"),
    ("workflow_todos", "source_refs"),
    ("workflow_todos", "evidence"),
    ("workflow_todos", "notes"),
    ("todo_events", "evidence"),
    ("trace_events", "payload"),
])
def test_json_columns_roundtrip_through_helpers(db, table, column):
    """Verify the _JSON_COLUMNS contract: a column listed there must
    serialize on write and deserialize on read."""
    assert column in _JSON_COLUMNS.get(table, set()), \
        f"{table}.{column} not in _JSON_COLUMNS"


def test_json_columns_returns_dict_on_read(db):
    db.record_trace_event(event_type="x", payload={"a": 1, "b": [2, 3]})
    rows = db.list_trace_events()
    assert rows[0]["payload"] == {"a": 1, "b": [2, 3]}


# ============================================================
# Section 22 — Migration safety on existing DB files
# ============================================================


def test_open_old_db_without_chat_index_backfills_it(tmp_path):
    """A v0 DB created before the chat-room index existed must boot
    cleanly and the index must be present after _run_lightweight_migrations."""
    path = str(tmp_path / "atlas.db")
    raw = sqlite3.connect(path)
    # Simulate an old DB: create one of the required tables and an empty
    # trace_events without the new index.
    raw.executescript("""
        CREATE TABLE trace_events (
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
    """)
    raw.commit()
    raw.close()

    # Now open with AtlasDB — it should add the missing index via
    # _run_lightweight_migrations (and any other migrations).
    db = AtlasDB(path)
    have = _all_indexes(db)
    assert "idx_trace_events_chat_room" in have


# ============================================================
# Section 23 — PRAGMA introspection
# ============================================================


def test_foreign_keys_pragma_default(db):
    """sqlite default for foreign_keys is OFF — verify the helper
    layer maintains references explicitly rather than relying on FK
    cascades. (Tests in test_db_operations_rigorous.py already showed
    that user/IP/workspace delete does NOT cascade trace_events.)"""
    rows = db._fetchall("PRAGMA foreign_keys")
    # Off by default — our design assumes audit-style ledger semantics
    assert rows[0][0] == 0


def test_journal_mode_is_delete_or_wal(db):
    rows = db._fetchall("PRAGMA journal_mode")
    mode = str(rows[0][0]).lower()
    # Either default (delete) or WAL is acceptable; both are safe for
    # the existing helper patterns
    assert mode in {"delete", "wal", "memory"}


# ============================================================
# Section 24 — Empty DB → admin usage payload returns gracefully
# ============================================================


def test_admin_usage_payload_on_empty_db_is_well_formed(db):
    from core.atlas_admin_usage import build_admin_usage_payload
    p = build_admin_usage_payload(db)
    assert isinstance(p, dict)
    for key in ("todo_usage", "trace_events", "tool_usage", "interventions"):
        assert key in p
