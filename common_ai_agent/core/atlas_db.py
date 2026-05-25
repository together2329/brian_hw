"""
Atlas SQLite Persistence Layer

Multi-user SQLite database for Atlas UI session management.
Replaces JSON file storage with concurrent-safe SQLite.

Zero external dependencies — uses only Python stdlib sqlite3.
"""

import hmac
import json
import os
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional

_IP_PERMISSION_LEVELS = {
    "view": 1,
    "import": 2,
    "write": 3,
    "admin": 4,
}


# ============================================================
# Schema
# ============================================================

SCHEMA_SQL = """
-- users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE,
    display_name TEXT,
    email TEXT,
    password_hash TEXT,
    role TEXT DEFAULT 'user',
    created_at REAL,
    last_login_at REAL,
    password_reset_token_hash TEXT,
    password_reset_expires_at REAL,
    password_reset_requested_at REAL,
    password_reset_used_at REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
    ON users(email) WHERE email IS NOT NULL AND email != '';
CREATE INDEX IF NOT EXISTS idx_users_password_reset_token
    ON users(password_reset_token_hash) WHERE password_reset_token_hash IS NOT NULL;

-- auth_email_codes
CREATE TABLE IF NOT EXISTS auth_email_codes (
    id TEXT PRIMARY KEY,
    purpose TEXT NOT NULL,
    email TEXT NOT NULL,
    code_hash TEXT NOT NULL,
    username TEXT,
    identifier TEXT,
    created_at REAL,
    expires_at REAL,
    used_at REAL,
    attempts INT DEFAULT 0
);
CREATE INDEX IF NOT EXISTS idx_auth_email_codes_lookup
    ON auth_email_codes(purpose, email, created_at);
CREATE INDEX IF NOT EXISTS idx_auth_email_codes_expiry
    ON auth_email_codes(expires_at, used_at);

-- sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    session_uid TEXT,
    user_id TEXT NOT NULL,
    namespace TEXT,
    owner TEXT,
    project_id TEXT,
    workspace_id TEXT,
    ip_id TEXT,
    ip TEXT,
    workflow TEXT,
    session_kind TEXT DEFAULT 'chat',
    directory TEXT,
    title TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL,
    updated_at REAL,
    archived_at REAL,
    summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, status);
CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_uid
    ON sessions(session_uid) WHERE session_uid IS NOT NULL AND session_uid != '';
CREATE INDEX IF NOT EXISTS idx_sessions_user_namespace ON sessions(user_id, namespace);
CREATE INDEX IF NOT EXISTS idx_sessions_user_context ON sessions(user_id, ip_id, workflow, status);

-- messages
CREATE TABLE IF NOT EXISTS messages (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    role TEXT,
    agent TEXT,
    model_id TEXT,
    provider_id TEXT,
    created_at REAL,
    completed_at REAL,
    cost REAL DEFAULT 0,
    tokens_input INT DEFAULT 0,
    tokens_output INT DEFAULT 0,
    tokens_reasoning INT DEFAULT 0,
    error TEXT
);
CREATE INDEX IF NOT EXISTS idx_messages_session ON messages(session_id, created_at);

-- parts
CREATE TABLE IF NOT EXISTS parts (
    id TEXT PRIMARY KEY,
    message_id TEXT,
    session_id TEXT,
    type TEXT,
    created_at REAL,
    text TEXT,
    tool_name TEXT,
    call_id TEXT,
    tool_status TEXT,
    tool_input TEXT,
    tool_output TEXT,
    tool_error TEXT,
    tool_title TEXT,
    start_time REAL,
    end_time REAL,
    compacted_at REAL,
    snapshot_hash TEXT,
    patch_hash TEXT,
    patch_files TEXT,
    step_reason TEXT,
    step_cost REAL,
    step_tokens_input INT,
    step_tokens_output INT
);
CREATE INDEX IF NOT EXISTS idx_parts_message ON parts(message_id);

-- ws_connections (ephemeral)
CREATE TABLE IF NOT EXISTS ws_connections (
    connection_id TEXT PRIMARY KEY,
    user_id TEXT,
    session_id TEXT,
    client_ip TEXT,
    user_agent TEXT,
    connected_at REAL,
    last_ping_at REAL
);

-- feedback (user-submitted via /feedback slash command,
-- visible to admins in the admin dashboard)
CREATE TABLE IF NOT EXISTS feedback (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    content TEXT NOT NULL,
    status TEXT DEFAULT 'open',
    created_at REAL,
    resolved_at REAL,
    resolved_by TEXT,
    notes TEXT
);
CREATE INDEX IF NOT EXISTS idx_feedback_user ON feedback(user_id, created_at);
CREATE INDEX IF NOT EXISTS idx_feedback_status ON feedback(status, created_at);

-- user_memory_rules (per-user system-prompt rules managed by /memory)
CREATE TABLE IF NOT EXISTS user_memory_rules (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    scope TEXT DEFAULT 'global',
    workflow TEXT DEFAULT '',
    rule TEXT NOT NULL,
    position INT DEFAULT 0,
    created_at REAL,
    updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_user_memory_rules_user_scope
    ON user_memory_rules(user_id, scope, workflow, position);
CREATE INDEX IF NOT EXISTS idx_user_memory_rules_updated
    ON user_memory_rules(updated_at);

-- custom_agents (per-user reusable sub-agent / worker prompts)
CREATE TABLE IF NOT EXISTS custom_agents (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT NOT NULL,
    name TEXT NOT NULL,
    scope TEXT DEFAULT 'private',
    base_agent TEXT NOT NULL,
    system_prompt TEXT NOT NULL,
    allowed_tools TEXT,
    model TEXT DEFAULT '',
    reasoning_effort TEXT DEFAULT '',
    description TEXT DEFAULT '',
    created_at REAL,
    updated_at REAL
);
CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_agents_owner_name
    ON custom_agents(owner_user_id, name);
CREATE INDEX IF NOT EXISTS idx_custom_agents_scope_name
    ON custom_agents(scope, name);
CREATE INDEX IF NOT EXISTS idx_custom_agents_updated
    ON custom_agents(updated_at);

-- session_queue (IPC between Atlas UI and agent workers)
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
CREATE INDEX IF NOT EXISTS idx_queue_session_direction ON session_queue(session_id, direction, created_at);
CREATE INDEX IF NOT EXISTS idx_queue_created ON session_queue(created_at);

-- workspaces (git/filesystem registry; DB stores pointers, not artifact bytes)
CREATE TABLE IF NOT EXISTS workspaces (
    id TEXT PRIMARY KEY,
    owner_user_id TEXT,
    name TEXT NOT NULL,
    local_path TEXT,
    git_remote TEXT,
    git_branch TEXT,
    base_commit TEXT,
    head_commit TEXT,
    dirty_state TEXT,
    created_at REAL,
    updated_at REAL,
    UNIQUE(owner_user_id, name)
);
CREATE INDEX IF NOT EXISTS idx_workspaces_owner ON workspaces(owner_user_id, updated_at);

-- ip_blocks (IP catalog within a workspace)
CREATE TABLE IF NOT EXISTS ip_blocks (
    id TEXT PRIMARY KEY,
    workspace_id TEXT NOT NULL,
    ip_name TEXT NOT NULL,
    ip_type TEXT,
    ssot_path TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL,
    updated_at REAL,
    UNIQUE(workspace_id, ip_name)
);
CREATE INDEX IF NOT EXISTS idx_ip_blocks_workspace ON ip_blocks(workspace_id, ip_name);

-- ip_permissions (per-IP sharing/import ACL)
CREATE TABLE IF NOT EXISTS ip_permissions (
    id TEXT PRIMARY KEY,
    ip_id TEXT NOT NULL,
    grantee_user_id TEXT NOT NULL,
    granted_by_user_id TEXT,
    permission TEXT NOT NULL,
    created_at REAL,
    expires_at REAL,
    UNIQUE(ip_id, grantee_user_id, permission)
);
CREATE INDEX IF NOT EXISTS idx_ip_permissions_user ON ip_permissions(grantee_user_id, permission);
CREATE INDEX IF NOT EXISTS idx_ip_permissions_ip ON ip_permissions(ip_id, permission);

-- artifact_versions (immutable SSOT/RTL/TB/model/netlist snapshots)
CREATE TABLE IF NOT EXISTS artifact_versions (
    id TEXT PRIMARY KEY,
    workspace_id TEXT,
    ip_id TEXT NOT NULL,
    artifact_type TEXT NOT NULL,
    version TEXT NOT NULL,
    label TEXT,
    root_path TEXT,
    primary_path TEXT,
    manifest TEXT,
    sha256_tree TEXT,
    git_commit TEXT,
    git_tag TEXT,
    status TEXT DEFAULT 'active',
    source_run_id TEXT,
    source_stage_id TEXT,
    metadata TEXT,
    created_at REAL,
    UNIQUE(ip_id, artifact_type, version)
);
CREATE INDEX IF NOT EXISTS idx_artifact_versions_ip_type
    ON artifact_versions(ip_id, artifact_type, created_at);
CREATE INDEX IF NOT EXISTS idx_artifact_versions_workspace
    ON artifact_versions(workspace_id, artifact_type, created_at);

-- artifact_version_edges (artifact dependency graph)
CREATE TABLE IF NOT EXISTS artifact_version_edges (
    id TEXT PRIMARY KEY,
    parent_version_id TEXT NOT NULL,
    child_version_id TEXT NOT NULL,
    relation TEXT NOT NULL,
    metadata TEXT,
    created_at REAL,
    UNIQUE(parent_version_id, child_version_id, relation)
);
CREATE INDEX IF NOT EXISTS idx_artifact_version_edges_parent
    ON artifact_version_edges(parent_version_id, relation);
CREATE INDEX IF NOT EXISTS idx_artifact_version_edges_child
    ON artifact_version_edges(child_version_id, relation);

-- run_artifact_versions (which artifact versions a run used or produced)
CREATE TABLE IF NOT EXISTS run_artifact_versions (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_id TEXT,
    artifact_version_id TEXT NOT NULL,
    role TEXT NOT NULL,
    required INT DEFAULT 1,
    metadata TEXT,
    created_at REAL,
    UNIQUE(run_id, artifact_version_id, role)
);
CREATE INDEX IF NOT EXISTS idx_run_artifact_versions_run
    ON run_artifact_versions(run_id, role);
CREATE INDEX IF NOT EXISTS idx_run_artifact_versions_version
    ON run_artifact_versions(artifact_version_id, role);

-- rtl_versions (immutable RTL handoff snapshots)
CREATE TABLE IF NOT EXISTS rtl_versions (
    id TEXT PRIMARY KEY,
    artifact_version_id TEXT,
    ip_id TEXT NOT NULL,
    workspace_id TEXT,
    source_run_id TEXT,
    source_stage_id TEXT,
    version TEXT NOT NULL,
    label TEXT,
    rtl_root TEXT,
    filelist_path TEXT,
    top_module TEXT,
    artifact_manifest TEXT,
    sha256_tree TEXT,
    git_commit TEXT,
    git_tag TEXT,
    status TEXT DEFAULT 'active',
    metadata TEXT,
    created_at REAL,
    UNIQUE(ip_id, version)
);
CREATE INDEX IF NOT EXISTS idx_rtl_versions_ip ON rtl_versions(ip_id, created_at);
CREATE INDEX IF NOT EXISTS idx_rtl_versions_workspace ON rtl_versions(workspace_id, created_at);

-- workflow_runs (one executable workflow invocation)
CREATE TABLE IF NOT EXISTS workflow_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    workspace_id TEXT,
    ip_id TEXT,
    rtl_version_id TEXT,
    workflow TEXT,
    mode TEXT,
    model_profile TEXT,
    reasoning_effort TEXT,
    status TEXT,
    started_at REAL,
    ended_at REAL,
    duration_ms REAL,
    trigger TEXT,
    input_summary TEXT,
    error_summary TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_session ON workflow_runs(session_id, started_at);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_context ON workflow_runs(workspace_id, ip_id, workflow, started_at);
CREATE INDEX IF NOT EXISTS idx_workflow_runs_rtl_version ON workflow_runs(rtl_version_id, workflow, started_at);

-- workflow_stages (stage-level status inside a run)
CREATE TABLE IF NOT EXISTS workflow_stages (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    rtl_version_id TEXT,
    stage_name TEXT NOT NULL,
    status TEXT,
    attempt INT DEFAULT 1,
    started_at REAL,
    ended_at REAL,
    duration_ms REAL,
    error_summary TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_workflow_stages_run ON workflow_stages(run_id, stage_name, attempt);
CREATE INDEX IF NOT EXISTS idx_workflow_stages_rtl_version ON workflow_stages(rtl_version_id, stage_name, started_at);

-- workflow_events (append-only run timeline)
CREATE TABLE IF NOT EXISTS workflow_events (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    stage_id TEXT,
    event_type TEXT NOT NULL,
    payload TEXT,
    created_at REAL
);
CREATE INDEX IF NOT EXISTS idx_workflow_events_run ON workflow_events(run_id, created_at);

-- workflow_todos (DB mirror of todo tracker state)
CREATE TABLE IF NOT EXISTS workflow_todos (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    source TEXT,
    title TEXT NOT NULL,
    detail TEXT,
    criteria TEXT,
    notes TEXT,
    status TEXT,
    owner_file TEXT,
    owner_module TEXT,
    source_refs TEXT,
    evidence TEXT,
    created_at REAL,
    updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_workflow_todos_run ON workflow_todos(run_id, status, updated_at);

-- todo_events (append-only todo status changes)
CREATE TABLE IF NOT EXISTS todo_events (
    id TEXT PRIMARY KEY,
    todo_id TEXT NOT NULL,
    event_type TEXT NOT NULL,
    reason TEXT,
    evidence TEXT,
    created_at REAL
);
CREATE INDEX IF NOT EXISTS idx_todo_events_todo ON todo_events(todo_id, created_at);

-- trace_events (canonical append-only ledger for workflow/session actions)
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
CREATE INDEX IF NOT EXISTS idx_trace_events_context ON trace_events(workspace_id, ip_id, workflow, created_at);
CREATE INDEX IF NOT EXISTS idx_trace_events_run ON trace_events(run_id, stage_id, todo_id, created_at);
CREATE INDEX IF NOT EXISTS idx_trace_events_correlation ON trace_events(correlation_id, created_at);
CREATE INDEX IF NOT EXISTS idx_trace_events_session ON trace_events(session_id, created_at);
-- Chat read path: list_chat_messages and list_chat_unconsumed_for both
-- filter on (event_type, ip_id) and order by created_at. Without this
-- index sqlite does a full scan + temp B-tree sort, which becomes the
-- bottleneck once a room has thousands of chat rows.
CREATE INDEX IF NOT EXISTS idx_trace_events_chat_room
  ON trace_events(event_type, ip_id, created_at);

-- llm_calls (canonical token/cost trace)
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
CREATE INDEX IF NOT EXISTS idx_llm_calls_context ON llm_calls(workspace_id, ip_id, workflow, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_calls_session ON llm_calls(session_id, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_calls_ip_created ON llm_calls(ip_id, created_at);
CREATE INDEX IF NOT EXISTS idx_llm_calls_todo ON llm_calls(todo_id, created_at);

-- artifacts (metadata/pointers only; content remains in filesystem/git/object storage)
CREATE TABLE IF NOT EXISTS artifacts (
    id TEXT PRIMARY KEY,
    run_id TEXT,
    stage_id TEXT,
    ip_id TEXT,
    rtl_version_id TEXT,
    workflow TEXT,
    kind TEXT,
    path TEXT,
    storage_backend TEXT DEFAULT 'filesystem',
    sha256 TEXT,
    size_bytes INT,
    git_commit TEXT,
    orchestrator_run_id TEXT,
    trigger_source TEXT,
    created_at REAL
);
CREATE INDEX IF NOT EXISTS idx_artifacts_run ON artifacts(run_id, kind, created_at);
CREATE INDEX IF NOT EXISTS idx_artifacts_rtl_version ON artifacts(rtl_version_id, kind, created_at);

-- orchestrator_runs (one LLM-driven control loop instance per user/ip)
CREATE TABLE IF NOT EXISTS orchestrator_runs (
    id TEXT PRIMARY KEY,
    session_id TEXT,
    workspace_id TEXT,
    ip_id TEXT,
    user_id TEXT,
    chat_message_id TEXT,
    pipeline_run_id TEXT,
    model TEXT,
    reasoning_effort TEXT,
    status TEXT,
    final_state TEXT,
    started_at REAL,
    ended_at REAL,
    updated_at REAL
);
CREATE INDEX IF NOT EXISTS idx_orchestrator_runs_scope
    ON orchestrator_runs(user_id, ip_id, status, started_at);
CREATE INDEX IF NOT EXISTS idx_orchestrator_runs_session
    ON orchestrator_runs(session_id, started_at);

-- orchestrator_steps (append-only decision/action log for one run)
CREATE TABLE IF NOT EXISTS orchestrator_steps (
    id TEXT PRIMARY KEY,
    run_id TEXT NOT NULL,
    step_index INT,
    tool_name TEXT,
    observed_state_json TEXT,
    decision_json TEXT,
    dispatched_workflow TEXT,
    dispatched_job_id TEXT,
    evidence_read_json TEXT,
    verdict TEXT,
    retry_budget_state_json TEXT,
    user_reply TEXT,
    created_at REAL
);
CREATE INDEX IF NOT EXISTS idx_orchestrator_steps_run
    ON orchestrator_steps(run_id, step_index);
"""

# Columns that should be serialized as JSON on write / deserialized on read
_JSON_COLUMNS = {
    "users": set(),
    "sessions": {"summary"},
    "messages": {"error"},
    "parts": {"tool_input", "patch_files"},
    "custom_agents": {"allowed_tools"},
    "ws_connections": set(),
    "session_queue": {"payload"},
    "artifact_versions": {"manifest", "metadata"},
    "artifact_version_edges": {"metadata"},
    "run_artifact_versions": {"metadata"},
    "rtl_versions": {"artifact_manifest", "metadata"},
    "workflow_events": {"payload"},
    "workflow_todos": {"source_refs", "evidence", "notes"},
    "todo_events": {"evidence"},
    "trace_events": {"payload"},
    "orchestrator_steps": {
        "observed_state_json",
        "decision_json",
        "evidence_read_json",
        "retry_budget_state_json",
    },
}


# ============================================================
# AtlasDB
# ============================================================

class AtlasDB:
    """
    Thread-safe SQLite persistence layer for Atlas UI.

    Uses a single shared connection with check_same_thread=False
    and an RLock to serialize access across threads.
    """

    # Process-wide serialization. Every AtlasDB(...) opens its own
    # sqlite3 connection, so a per-instance lock cannot serialize
    # writers across threads that each `with AtlasDB(...) as db:`. Without
    # this class-level RLock, N concurrent writers all hit SQLite's WAL
    # single-writer queue and compete on busy_timeout (30s). All
    # instances now share `_WRITE_LOCK` as their `_lock`, so SQLite only
    # ever sees one writer at a time per process. RLock is reentrant so
    # nested method calls within the same thread are safe. Reads incur
    # a tiny lock overhead but the SQLite call dominates.
    _WRITE_LOCK = threading.RLock()

    # Schema bootstrap is idempotent but not free: the full DDL script
    # (~80 CREATE statements) plus the preflight/migration PRAGMA scans cost
    # ~3 ms per run under _WRITE_LOCK. Hot paths build `with AtlasDB(...)`
    # thousands of times, so re-running it on every construction serialized
    # the LLM loop behind redundant re-initialization. Track which db files
    # this process has already initialized and skip the work after the first
    # pass. Guarded by _WRITE_LOCK (set mutation happens inside the lock).
    _INITIALIZED_PATHS: set = set()

    # Per-thread connection cache keyed by db_path. Opening + WAL-configuring
    # a connection costs ~0.4 ms; hot paths build `with AtlasDB(...)` thousands
    # of times, so each block paid that to open and then close again. Reusing
    # one connection per (thread, db_path) drops the per-block cost to ~0.002 ms.
    # Thread-local (not a single shared connection) so a connection is only ever
    # touched by its owning thread — cursors returned from _execute() can be
    # iterated after the lock releases without colliding with another thread.
    _TLS = threading.local()

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = os.environ.get("ATLAS_DB_PATH") or str(Path.home() / ".common_ai_agent" / "atlas.db")
        self.db_path = db_path
        self._lock = AtlasDB._WRITE_LOCK
        self._conn: Optional[sqlite3.Connection] = None
        # Ensure parent dir + schema exist on first instantiation.
        # SCHEMA_SQL is idempotent (CREATE TABLE IF NOT EXISTS).
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        """Return this thread's connection for db_path, opening it once."""
        cache = getattr(AtlasDB._TLS, "conns", None)
        if cache is None:
            cache = {}
            AtlasDB._TLS.conns = cache
        conn = cache.get(self.db_path)
        if conn is not None:
            self._conn = conn
            return conn
        try:
            timeout_s = float(os.environ.get("ATLAS_SQLITE_TIMEOUT", "30") or 30)
        except Exception:
            timeout_s = 30.0
        conn = sqlite3.connect(
            self.db_path,
            check_same_thread=False,
            timeout=timeout_s,
        )
        conn.row_factory = sqlite3.Row
        # WAL mode allows concurrent reads + single queued writer (no reader/writer blocking).
        # busy_timeout must be set before journal_mode because multiple
        # worker processes can initialize the same DB at once.
        conn.execute(f"PRAGMA busy_timeout={int(timeout_s * 1000)}")
        deadline = time.monotonic() + timeout_s
        while True:
            try:
                conn.execute("PRAGMA journal_mode=WAL")
                break
            except sqlite3.OperationalError as exc:
                if "database is locked" not in str(exc).lower() or time.monotonic() >= deadline:
                    raise
                time.sleep(0.05)
        cache[self.db_path] = conn
        self._conn = conn
        return conn

    def _execute(self, sql: str, parameters: tuple = ()) -> sqlite3.Cursor:
        """Execute SQL inside the lock."""
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(sql, parameters)
            conn.commit()
            return cursor

    def _fetchone(self, sql: str, parameters: tuple = ()) -> Optional[sqlite3.Row]:
        """Fetch a single row inside the lock."""
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(sql, parameters)
            return cursor.fetchone()

    def _fetchall(self, sql: str, parameters: tuple = ()) -> List[sqlite3.Row]:
        """Fetch all rows inside the lock."""
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(sql, parameters)
            return cursor.fetchall()

    @staticmethod
    def _new_id() -> str:
        return uuid.uuid4().hex

    @staticmethod
    def _now() -> float:
        return time.time()

    @staticmethod
    def _dump_json(value: Any) -> Optional[str]:
        if value is None:
            return None
        return json.dumps(value, ensure_ascii=False)

    @staticmethod
    def _load_json(value: Any) -> Any:
        if value is None or value == "":
            return None
        if isinstance(value, str):
            try:
                return json.loads(value)
            except (json.JSONDecodeError, TypeError):
                return value
        return value

    def _row_to_dict(self, row: sqlite3.Row, table: str) -> Dict[str, Any]:
        """Convert a sqlite3.Row to a plain dict, handling JSON columns."""
        json_cols = _JSON_COLUMNS.get(table, set())
        result: Dict[str, Any] = {}
        for key in row.keys():
            val = row[key]
            if key in json_cols:
                val = self._load_json(val)
            result[key] = val
        return result

    # ---------- Lifecycle ----------

    def init_db(self):
        """Create tables and indexes if they don't exist.

        Runs the full schema bootstrap once per db file per process; later
        calls return immediately (see _INITIALIZED_PATHS).
        """
        with self._lock:
            if self.db_path in AtlasDB._INITIALIZED_PATHS:
                return
            conn = self._connect()
            self._preflight_legacy_schema(conn)
            conn.executescript(SCHEMA_SQL)
            self._run_lightweight_migrations(conn)
            conn.commit()
            AtlasDB._INITIALIZED_PATHS.add(self.db_path)

    def _preflight_legacy_schema(self, conn: sqlite3.Connection) -> None:
        """Add columns needed by indexes before running idempotent DDL.

        SQLite does not alter existing tables for ``CREATE TABLE IF NOT EXISTS``.
        Any new index in ``SCHEMA_SQL`` that references a newly-added column can
        therefore fail before the normal migration pass runs. Keep this preflight
        limited to additive columns that DDL indexes depend on.
        """
        def table_exists(table: str) -> bool:
            return bool(conn.execute(
                "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = ?",
                (table,),
            ).fetchone())

        def ensure_if_exists(table: str, column: str, definition: str) -> None:
            if table_exists(table):
                self._ensure_column(conn, table, column, definition)

        ddl_index_columns = {
            "users": {
                "email": "TEXT",
                "password_reset_token_hash": "TEXT",
                "password_reset_expires_at": "REAL",
                "password_reset_requested_at": "REAL",
                "password_reset_used_at": "REAL",
            },
            "sessions": {
                "session_uid": "TEXT",
                "user_id": "TEXT",
                "namespace": "TEXT",
                "ip_id": "TEXT",
                "workflow": "TEXT",
                "status": "TEXT",
            },
            "messages": {"session_id": "TEXT", "created_at": "REAL"},
            "parts": {"message_id": "TEXT"},
            "feedback": {"user_id": "TEXT", "status": "TEXT", "created_at": "REAL"},
            "user_memory_rules": {
                "user_id": "TEXT",
                "scope": "TEXT DEFAULT 'global'",
                "workflow": "TEXT DEFAULT ''",
                "position": "INT DEFAULT 0",
                "updated_at": "REAL",
            },
            "custom_agents": {
                "owner_user_id": "TEXT",
                "name": "TEXT",
                "scope": "TEXT DEFAULT 'private'",
                "base_agent": "TEXT",
                "system_prompt": "TEXT",
                "allowed_tools": "TEXT",
                "model": "TEXT DEFAULT ''",
                "reasoning_effort": "TEXT DEFAULT ''",
                "description": "TEXT DEFAULT ''",
                "created_at": "REAL",
                "updated_at": "REAL",
            },
            "session_queue": {
                "session_id": "TEXT",
                "direction": "TEXT",
                "created_at": "REAL",
            },
            "workspaces": {"owner_user_id": "TEXT", "updated_at": "REAL"},
            "ip_blocks": {"workspace_id": "TEXT", "ip_name": "TEXT"},
            "ip_permissions": {
                "grantee_user_id": "TEXT",
                "ip_id": "TEXT",
                "permission": "TEXT",
            },
            "rtl_versions": {
                "artifact_version_id": "TEXT",
                "git_tag": "TEXT",
                "ip_id": "TEXT",
                "workspace_id": "TEXT",
                "created_at": "REAL",
            },
            "workflow_runs": {
                "session_id": "TEXT",
                "workspace_id": "TEXT",
                "ip_id": "TEXT",
                "rtl_version_id": "TEXT",
                "workflow": "TEXT",
                "started_at": "REAL",
            },
            "workflow_stages": {
                "run_id": "TEXT",
                "rtl_version_id": "TEXT",
                "stage_name": "TEXT",
                "attempt": "INT DEFAULT 1",
                "started_at": "REAL",
            },
            "workflow_events": {"run_id": "TEXT", "created_at": "REAL"},
            "workflow_todos": {
                "run_id": "TEXT",
                "status": "TEXT",
                "updated_at": "REAL",
                "notes": "TEXT",
            },
            "todo_events": {"todo_id": "TEXT", "created_at": "REAL"},
            "trace_events": {
                "session_id": "TEXT",
                "workspace_id": "TEXT",
                "ip_id": "TEXT",
                "workflow": "TEXT",
                "run_id": "TEXT",
                "stage_id": "TEXT",
                "todo_id": "TEXT",
                "correlation_id": "TEXT",
                "event_type": "TEXT",
                "created_at": "REAL",
            },
            "llm_calls": {
                "session_id": "TEXT",
                "workspace_id": "TEXT",
                "ip_id": "TEXT",
                "workflow": "TEXT",
                "todo_id": "TEXT",
                "tokens_input": "INT DEFAULT 0",
                "tokens_output": "INT DEFAULT 0",
                "tokens_reasoning": "INT DEFAULT 0",
                "cache_read_tokens": "INT DEFAULT 0",
                "cache_write_tokens": "INT DEFAULT 0",
                "cost_usd": "REAL DEFAULT 0",
                "created_at": "REAL",
            },
            "artifacts": {
                "run_id": "TEXT",
                "rtl_version_id": "TEXT",
                "kind": "TEXT",
                "created_at": "REAL",
            },
            "orchestrator_runs": {
                "user_id": "TEXT",
                "ip_id": "TEXT",
                "status": "TEXT",
                "session_id": "TEXT",
                "started_at": "REAL",
            },
            "orchestrator_steps": {
                "run_id": "TEXT",
                "step_index": "INT",
            },
        }

        for table, columns in ddl_index_columns.items():
            for column, definition in columns.items():
                ensure_if_exists(table, column, definition)

        # Older DBs may have run/workflow tables but not the generic artifact
        # lineage tables. They are created by SCHEMA_SQL after this preflight, so
        # no column backfill is needed here for those brand-new tables.

    def _run_lightweight_migrations(self, conn: sqlite3.Connection) -> None:
        """Apply additive SQLite migrations for existing local databases."""
        self._ensure_column(conn, "users", "email", "TEXT")
        self._ensure_column(conn, "users", "password_reset_token_hash", "TEXT")
        self._ensure_column(conn, "users", "password_reset_expires_at", "REAL")
        self._ensure_column(conn, "users", "password_reset_requested_at", "REAL")
        self._ensure_column(conn, "users", "password_reset_used_at", "REAL")
        session_columns = {
            "session_uid": "TEXT",
            "namespace": "TEXT",
            "owner": "TEXT",
            "workspace_id": "TEXT",
            "ip_id": "TEXT",
            "ip": "TEXT",
            "workflow": "TEXT",
            "session_kind": "TEXT DEFAULT 'chat'",
        }
        for column, definition in session_columns.items():
            self._ensure_column(conn, "sessions", column, definition)
        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_sessions_uid
                  ON sessions(session_uid) WHERE session_uid IS NOT NULL AND session_uid != ''"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_sessions_user_namespace
                  ON sessions(user_id, namespace)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_sessions_user_context
                  ON sessions(user_id, ip_id, workflow, status)"""
        )
        for row in conn.execute(
            "SELECT id FROM sessions WHERE session_uid IS NULL OR session_uid = ''"
        ).fetchall():
            conn.execute(
                "UPDATE sessions SET session_uid = ? WHERE id = ?",
                (self._new_id(), row["id"]),
            )
        conn.execute(
            """
            UPDATE sessions
               SET namespace = id
             WHERE (namespace IS NULL OR namespace = '')
               AND instr(id, '/') > 0
            """
        )
        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_users_email
                  ON users(email) WHERE email IS NOT NULL AND email != ''"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_users_password_reset_token
                  ON users(password_reset_token_hash) WHERE password_reset_token_hash IS NOT NULL"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_auth_email_codes_lookup
                  ON auth_email_codes(purpose, email, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_auth_email_codes_expiry
                  ON auth_email_codes(expires_at, used_at)"""
        )
        self._ensure_column(conn, "workflow_todos", "notes", "TEXT")
        self._ensure_column(conn, "rtl_versions", "artifact_version_id", "TEXT")
        self._ensure_column(conn, "workflow_runs", "rtl_version_id", "TEXT")
        self._ensure_column(conn, "workflow_stages", "rtl_version_id", "TEXT")
        self._ensure_column(conn, "artifacts", "rtl_version_id", "TEXT")
        self._ensure_column(conn, "rtl_versions", "git_tag", "TEXT")
        self._ensure_column(conn, "workflow_runs", "orchestrator_run_id", "TEXT")
        self._ensure_column(conn, "workflow_runs", "trigger_source", "TEXT")
        self._ensure_column(conn, "artifacts", "orchestrator_run_id", "TEXT")
        self._ensure_column(conn, "artifacts", "trigger_source", "TEXT")
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_artifact_versions_ip_type
                  ON artifact_versions(ip_id, artifact_type, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_artifact_versions_workspace
                  ON artifact_versions(workspace_id, artifact_type, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_artifact_version_edges_parent
                  ON artifact_version_edges(parent_version_id, relation)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_artifact_version_edges_child
                  ON artifact_version_edges(child_version_id, relation)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_run_artifact_versions_run
                  ON run_artifact_versions(run_id, role)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_run_artifact_versions_version
                  ON run_artifact_versions(artifact_version_id, role)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_workflow_runs_rtl_version
                  ON workflow_runs(rtl_version_id, workflow, started_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_workflow_stages_rtl_version
                  ON workflow_stages(rtl_version_id, stage_name, started_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_artifacts_rtl_version
                  ON artifacts(rtl_version_id, kind, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_rtl_versions_ip
                  ON rtl_versions(ip_id, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_rtl_versions_workspace
                  ON rtl_versions(workspace_id, created_at)"""
        )
        # Backfill the chat-room index on databases created before
        # 2026-05-15. CREATE INDEX IF NOT EXISTS is idempotent so this
        # is safe to re-run on every boot.
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_trace_events_chat_room
                  ON trace_events(event_type, ip_id, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_llm_calls_ip_created
                  ON llm_calls(ip_id, created_at)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_user_memory_rules_user_scope
                  ON user_memory_rules(user_id, scope, workflow, position)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_user_memory_rules_updated
                  ON user_memory_rules(updated_at)"""
        )
        conn.execute(
            """CREATE UNIQUE INDEX IF NOT EXISTS idx_custom_agents_owner_name
                  ON custom_agents(owner_user_id, name)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_custom_agents_scope_name
                  ON custom_agents(scope, name)"""
        )
        conn.execute(
            """CREATE INDEX IF NOT EXISTS idx_custom_agents_updated
                  ON custom_agents(updated_at)"""
        )

    @staticmethod
    def _ensure_column(
        conn: sqlite3.Connection,
        table: str,
        column: str,
        definition: str,
    ) -> None:
        rows = conn.execute(f"PRAGMA table_info({table})").fetchall()
        if any(row["name"] == column for row in rows):
            return
        try:
            conn.execute(f"ALTER TABLE {table} ADD COLUMN {column} {definition}")
        except sqlite3.OperationalError as exc:
            if "duplicate column name" in str(exc).lower():
                return
            raise

    def close(self):
        """Close and evict this thread's cached connection for db_path."""
        with self._lock:
            cache = getattr(AtlasDB._TLS, "conns", None)
            conn = cache.pop(self.db_path, None) if cache else None
            if conn is None:
                conn = self._conn
            if conn is not None:
                try:
                    conn.close()
                except Exception:
                    pass
            self._conn = None

    def __enter__(self):
        # __init__ already ran init_db(); no need to repeat it on every `with`.
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        # Keep the thread-local connection cached for reuse; explicit close()
        # or process exit releases it. Closing here would defeat reuse.
        return False

    # ---------- Users ----------

    def create_user(
        self,
        username: str,
        display_name: str,
        password_hash: str = None,
        role: str = "user",
        email: str = None,
    ) -> Dict[str, Any]:
        """Create a new user. Returns the user dict."""
        user_id = self._new_id()
        now = self._now()
        role = role or "user"
        email = self._normalize_email(email)
        self._execute(
            """
            INSERT INTO users (id, username, display_name, email, password_hash, role, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, display_name, email, password_hash, role, now, None),
        )
        return {
            "id": user_id,
            "username": username,
            "display_name": display_name,
            "email": email,
            "password_hash": password_hash,
            "role": role,
            "created_at": now,
            "last_login_at": None,
        }

    @staticmethod
    def _normalize_email(email: str = None) -> Optional[str]:
        value = str(email or "").strip().lower()
        return value or None

    def get_user(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by ID. Returns user dict or None."""
        row = self._fetchone("SELECT * FROM users WHERE id = ?", (user_id,))
        if row is None:
            return None
        return self._row_to_dict(row, "users")

    def get_user_by_username(self, username: str) -> Optional[Dict[str, Any]]:
        """Get user by username. Returns user dict or None."""
        row = self._fetchone("SELECT * FROM users WHERE username = ?", (username,))
        if row is None:
            return None
        return self._row_to_dict(row, "users")

    def ensure_user_by_username(
        self,
        username: str,
        display_name: str = None,
        role: str = "user",
    ) -> Dict[str, Any]:
        """Return an existing user or create a lightweight local user row."""
        name = str(username or "").strip()
        if not name:
            raise ValueError("username required")
        existing = self.get_user_by_username(name)
        if existing is not None:
            return existing
        return self.create_user(
            username=name,
            display_name=display_name or name,
            role=role or "user",
        )

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by normalized email. Returns user dict or None."""
        normalized = self._normalize_email(email)
        if not normalized:
            return None
        row = self._fetchone("SELECT * FROM users WHERE email = ?", (normalized,))
        if row is None:
            return None
        return self._row_to_dict(row, "users")

    def get_user_by_password_reset_token_hash(self, token_hash: str) -> Optional[Dict[str, Any]]:
        """Get user by password reset token hash. Returns user dict or None."""
        if not token_hash:
            return None
        row = self._fetchone(
            "SELECT * FROM users WHERE password_reset_token_hash = ?",
            (token_hash,),
        )
        if row is None:
            return None
        return self._row_to_dict(row, "users")

    def set_user_role(self, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        """Update a user's role and return the refreshed user."""
        self._execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        return self.get_user(user_id)

    def set_user_password_reset(
        self,
        user_id: str,
        token_hash: str,
        expires_at: float,
        requested_at: float = None,
    ) -> Optional[Dict[str, Any]]:
        """Store a password-reset token hash and expiry for a user."""
        requested_at = requested_at if requested_at is not None else self._now()
        self._execute(
            """
            UPDATE users
               SET password_reset_token_hash = ?,
                   password_reset_expires_at = ?,
                   password_reset_requested_at = ?,
                   password_reset_used_at = NULL
             WHERE id = ?
            """,
            (token_hash, expires_at, requested_at, user_id),
        )
        return self.get_user(user_id)

    def update_user_password(self, user_id: str, password_hash: str) -> Optional[Dict[str, Any]]:
        """Update password and consume any outstanding password-reset token."""
        now = self._now()
        self._execute(
            """
            UPDATE users
               SET password_hash = ?,
                   password_reset_token_hash = NULL,
                   password_reset_expires_at = NULL,
                   password_reset_requested_at = NULL,
                   password_reset_used_at = ?
             WHERE id = ?
            """,
            (password_hash, now, user_id),
        )
        return self.get_user(user_id)

    def create_auth_email_code(
        self,
        purpose: str,
        email: str,
        code_hash: str,
        expires_at: float,
        username: str = "",
        identifier: str = "",
    ) -> Dict[str, Any]:
        """Store a one-time email verification code for an auth flow."""
        normalized = self._normalize_email(email)
        if not normalized:
            raise ValueError("email required")
        clean_purpose = str(purpose or "").strip().lower()
        if not clean_purpose:
            raise ValueError("purpose required")
        code_id = self._new_id()
        now = self._now()
        with self._lock:
            conn = self._connect()
            conn.execute(
                """
                UPDATE auth_email_codes
                   SET used_at = ?
                 WHERE purpose = ? AND email = ? AND used_at IS NULL
                """,
                (now, clean_purpose, normalized),
            )
            conn.execute(
                """
                INSERT INTO auth_email_codes
                (id, purpose, email, code_hash, username, identifier,
                 created_at, expires_at, used_at, attempts)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, NULL, 0)
                """,
                (
                    code_id,
                    clean_purpose,
                    normalized,
                    code_hash,
                    str(username or "").strip(),
                    str(identifier or "").strip(),
                    now,
                    float(expires_at),
                ),
            )
            conn.commit()
        return {
            "id": code_id,
            "purpose": clean_purpose,
            "email": normalized,
            "code_hash": code_hash,
            "username": str(username or "").strip(),
            "identifier": str(identifier or "").strip(),
            "created_at": now,
            "expires_at": float(expires_at),
            "used_at": None,
            "attempts": 0,
        }

    def consume_auth_email_code(
        self,
        purpose: str,
        email: str,
        code_hash: str,
        max_attempts: int = 6,
        now: float = None,
    ) -> bool:
        """Consume the latest active email code if the hash matches."""
        normalized = self._normalize_email(email)
        clean_purpose = str(purpose or "").strip().lower()
        if not normalized or not clean_purpose or not code_hash:
            return False
        now = self._now() if now is None else float(now)
        max_attempts = max(1, int(max_attempts or 6))
        with self._lock:
            conn = self._connect()
            row = conn.execute(
                """
                SELECT *
                  FROM auth_email_codes
                 WHERE purpose = ?
                   AND email = ?
                   AND used_at IS NULL
                   AND expires_at >= ?
                 ORDER BY created_at DESC
                 LIMIT 1
                """,
                (clean_purpose, normalized, now),
            ).fetchone()
            if row is None:
                return False
            attempts = int(row["attempts"] or 0)
            if attempts >= max_attempts:
                conn.execute(
                    "UPDATE auth_email_codes SET used_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
                conn.commit()
                return False
            if hmac.compare_digest(str(row["code_hash"] or ""), str(code_hash)):
                conn.execute(
                    "UPDATE auth_email_codes SET used_at = ? WHERE id = ?",
                    (now, row["id"]),
                )
                conn.commit()
                return True
            conn.execute(
                "UPDATE auth_email_codes SET attempts = attempts + 1 WHERE id = ?",
                (row["id"],),
            )
            conn.commit()
            return False

    # ---------- User Memory Rules ----------

    @staticmethod
    def _normalize_memory_workflow(workflow: str = None) -> str:
        text = str(workflow or "").strip().strip("/")
        if not text:
            return ""
        parts = [part for part in text.split("/") if part]
        return parts[-1] if parts else ""

    def add_user_memory_rule(
        self,
        user_id: str,
        rule: str,
        workflow: str = None,
    ) -> Dict[str, Any]:
        """Add a per-user prompt memory rule and return the inserted row."""
        uid = str(user_id or "").strip()
        text = str(rule or "").strip()
        if not uid:
            raise ValueError("user_id required")
        if not text:
            raise ValueError("memory rule cannot be empty")
        workflow_name = self._normalize_memory_workflow(workflow)
        scope = "workflow" if workflow_name else "global"
        now = self._now()
        row = self._fetchone(
            """
            SELECT COALESCE(MAX(position), 0) + 1 AS next_position
              FROM user_memory_rules
             WHERE user_id = ? AND scope = ? AND workflow = ?
            """,
            (uid, scope, workflow_name),
        )
        position = int(row["next_position"] if row is not None and row["next_position"] else 1)
        rid = self._new_id()
        self._execute(
            """
            INSERT INTO user_memory_rules
            (id, user_id, scope, workflow, rule, position, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (rid, uid, scope, workflow_name, text, position, now, now),
        )
        return self.get_user_memory_rule(rid) or {
            "id": rid,
            "user_id": uid,
            "scope": scope,
            "workflow": workflow_name,
            "rule": text,
            "position": position,
            "created_at": now,
            "updated_at": now,
        }

    def get_user_memory_rule(self, rule_id: str) -> Optional[Dict[str, Any]]:
        """Return one memory rule by id."""
        row = self._fetchone(
            """
            SELECT r.*, u.username, u.display_name
              FROM user_memory_rules r
              LEFT JOIN users u ON u.id = r.user_id
             WHERE r.id = ?
            """,
            (str(rule_id or "").strip(),),
        )
        return dict(row) if row else None

    def list_user_memory_rules(
        self,
        user_id: str,
        workflow: str = None,
        include_global: bool = True,
        include_all_workflows: bool = False,
    ) -> List[Dict[str, Any]]:
        """List memory rules visible to a user for prompt injection/listing."""
        uid = str(user_id or "").strip()
        if not uid:
            return []
        workflow_name = self._normalize_memory_workflow(workflow)
        clauses = ["r.user_id = ?"]
        values: list[Any] = [uid]
        if include_all_workflows:
            pass
        elif workflow_name:
            if include_global:
                clauses.append(
                    "((r.scope = 'global' AND r.workflow = '') OR "
                    "(r.scope = 'workflow' AND r.workflow = ?))"
                )
                values.append(workflow_name)
            else:
                clauses.append("r.scope = 'workflow' AND r.workflow = ?")
                values.append(workflow_name)
        else:
            clauses.append("r.scope = 'global' AND r.workflow = ''")
        where = " WHERE " + " AND ".join(clauses)
        rows = self._fetchall(
            f"""
            SELECT r.*, u.username, u.display_name
              FROM user_memory_rules r
              LEFT JOIN users u ON u.id = r.user_id
             {where}
             ORDER BY
               CASE r.scope WHEN 'global' THEN 0 ELSE 1 END,
               r.workflow COLLATE NOCASE,
               r.position ASC,
               r.created_at ASC
            """,
            tuple(values),
        )
        return [dict(row) for row in rows]

    def list_all_user_memory_rules(self, limit: int = 500) -> List[Dict[str, Any]]:
        """Admin list of all per-user memory rules."""
        rows = self._fetchall(
            """
            SELECT r.*, u.username, u.display_name, u.role
              FROM user_memory_rules r
              LEFT JOIN users u ON u.id = r.user_id
             ORDER BY r.updated_at DESC, r.created_at DESC
             LIMIT ?
            """,
            (int(limit),),
        )
        return [dict(row) for row in rows]

    def delete_user_memory_rule(self, user_id: str, rule_id: str) -> bool:
        """Delete one memory rule owned by user_id."""
        before = self._fetchone(
            "SELECT COUNT(*) AS cnt FROM user_memory_rules WHERE id = ? AND user_id = ?",
            (str(rule_id or "").strip(), str(user_id or "").strip()),
        )
        if int(before["cnt"] if before is not None else 0) <= 0:
            return False
        self._execute(
            "DELETE FROM user_memory_rules WHERE id = ? AND user_id = ?",
            (str(rule_id or "").strip(), str(user_id or "").strip()),
        )
        return True

    def clear_user_memory_rules(
        self,
        user_id: str,
        workflow: str = None,
        all_scopes: bool = False,
    ) -> int:
        """Clear a user's memory rules. Defaults to global scope only."""
        uid = str(user_id or "").strip()
        if not uid:
            return 0
        workflow_name = self._normalize_memory_workflow(workflow)
        clauses = ["user_id = ?"]
        values: list[Any] = [uid]
        if all_scopes:
            pass
        elif workflow_name:
            clauses.append("scope = 'workflow' AND workflow = ?")
            values.append(workflow_name)
        else:
            clauses.append("scope = 'global' AND workflow = ''")
        where = " WHERE " + " AND ".join(clauses)
        before = self._fetchone(
            f"SELECT COUNT(*) AS cnt FROM user_memory_rules{where}",
            tuple(values),
        )
        removed = int(before["cnt"] if before is not None else 0)
        if removed:
            self._execute(f"DELETE FROM user_memory_rules{where}", tuple(values))
        return removed

    # ---------- Custom Agents ----------

    @staticmethod
    def _normalize_custom_agent_scope(scope: str = None) -> str:
        normalized = str(scope or "private").strip().lower()
        return normalized if normalized in {"private", "shared", "system"} else "private"

    def upsert_custom_agent(
        self,
        owner_user_id: str,
        name: str,
        base_agent: str,
        system_prompt: str,
        allowed_tools: Any = None,
        model: str = "",
        reasoning_effort: str = "",
        description: str = "",
        scope: str = "private",
    ) -> Dict[str, Any]:
        """Create or update a reusable custom agent owned by one user."""
        owner = str(owner_user_id or "").strip()
        agent_name = str(name or "").strip()
        base = str(base_agent or "explore").strip() or "explore"
        prompt = str(system_prompt or "").strip()
        normalized_scope = self._normalize_custom_agent_scope(scope)
        if not owner:
            raise ValueError("owner_user_id required")
        if not agent_name:
            raise ValueError("custom agent name required")
        if not prompt:
            raise ValueError("system_prompt required")
        if normalized_scope in {"shared", "system"}:
            owner_row = self.get_user(owner)
            if not owner_row or str(owner_row.get("role") or "").strip().lower() != "admin":
                normalized_scope = "private"

        now = self._now()
        existing = self._fetchone(
            "SELECT * FROM custom_agents WHERE owner_user_id = ? AND name = ?",
            (owner, agent_name),
        )
        allowed_json = self._dump_json(allowed_tools)
        if existing is None:
            agent_id = self._new_id()
            created_at = now
            self._execute(
                """
                INSERT INTO custom_agents
                (id, owner_user_id, name, scope, base_agent, system_prompt,
                 allowed_tools, model, reasoning_effort, description, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    agent_id,
                    owner,
                    agent_name,
                    normalized_scope,
                    base,
                    prompt,
                    allowed_json,
                    str(model or "").strip(),
                    str(reasoning_effort or "").strip(),
                    str(description or "").strip(),
                    created_at,
                    now,
                ),
            )
        else:
            agent_id = str(existing["id"])
            self._execute(
                """
                UPDATE custom_agents
                   SET scope = ?,
                       base_agent = ?,
                       system_prompt = ?,
                       allowed_tools = ?,
                       model = ?,
                       reasoning_effort = ?,
                       description = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    normalized_scope,
                    base,
                    prompt,
                    allowed_json,
                    str(model or "").strip(),
                    str(reasoning_effort or "").strip(),
                    str(description or "").strip(),
                    now,
                    agent_id,
                ),
            )
        return self.get_custom_agent(owner, agent_name, include_shared=False) or {
            "id": agent_id,
            "owner_user_id": owner,
            "name": agent_name,
            "scope": normalized_scope,
            "base_agent": base,
            "system_prompt": prompt,
            "allowed_tools": allowed_tools,
            "model": str(model or "").strip(),
            "reasoning_effort": str(reasoning_effort or "").strip(),
            "description": str(description or "").strip(),
            "created_at": now,
            "updated_at": now,
        }

    def get_custom_agent(
        self,
        owner_user_id: str,
        name: str,
        include_shared: bool = True,
    ) -> Optional[Dict[str, Any]]:
        """Return an owner's custom agent, falling back to shared/system names."""
        owner = str(owner_user_id or "").strip()
        agent_name = str(name or "").strip()
        if not owner or not agent_name:
            return None
        row = self._fetchone(
            """
            SELECT a.*, u.username, u.display_name
              FROM custom_agents a
              LEFT JOIN users u ON u.id = a.owner_user_id
             WHERE a.owner_user_id = ? AND a.name = ?
             LIMIT 1
            """,
            (owner, agent_name),
        )
        if row is None and include_shared:
            row = self._fetchone(
                """
                SELECT a.*, u.username, u.display_name
                  FROM custom_agents a
                  LEFT JOIN users u ON u.id = a.owner_user_id
                 WHERE a.name = ? AND a.scope IN ('system', 'shared')
                 ORDER BY CASE a.scope WHEN 'system' THEN 0 ELSE 1 END,
                          a.updated_at DESC
                 LIMIT 1
                """,
                (agent_name,),
            )
        return self._row_to_dict(row, "custom_agents") if row else None

    def list_custom_agents(
        self,
        owner_user_id: str,
        include_shared: bool = True,
    ) -> List[Dict[str, Any]]:
        """List custom agents visible to one user."""
        owner = str(owner_user_id or "").strip()
        if not owner:
            return []
        if include_shared:
            rows = self._fetchall(
                """
                SELECT a.*, u.username, u.display_name
                  FROM custom_agents a
                  LEFT JOIN users u ON u.id = a.owner_user_id
                 WHERE a.owner_user_id = ? OR a.scope IN ('system', 'shared')
                   AND NOT EXISTS (
                         SELECT 1
                           FROM custom_agents owned
                          WHERE owned.owner_user_id = ?
                            AND owned.name = a.name
                       )
                 ORDER BY CASE WHEN a.owner_user_id = ? THEN 0 ELSE 1 END,
                          a.scope COLLATE NOCASE,
                          a.name COLLATE NOCASE
                """,
                (owner, owner, owner),
            )
        else:
            rows = self._fetchall(
                """
                SELECT a.*, u.username, u.display_name
                  FROM custom_agents a
                  LEFT JOIN users u ON u.id = a.owner_user_id
                 WHERE a.owner_user_id = ?
                 ORDER BY a.name COLLATE NOCASE
                """,
                (owner,),
            )
        return [self._row_to_dict(row, "custom_agents") for row in rows]

    def delete_custom_agent(self, owner_user_id: str, name_or_id: str) -> bool:
        """Delete one custom agent owned by user by name or id."""
        owner = str(owner_user_id or "").strip()
        key = str(name_or_id or "").strip()
        if not owner or not key:
            return False
        before = self._fetchone(
            """
            SELECT COUNT(*) AS cnt
              FROM custom_agents
             WHERE owner_user_id = ? AND (name = ? OR id = ?)
            """,
            (owner, key, key),
        )
        if int(before["cnt"] if before is not None else 0) <= 0:
            return False
        self._execute(
            "DELETE FROM custom_agents WHERE owner_user_id = ? AND (name = ? OR id = ?)",
            (owner, key, key),
        )
        return True

    # ---------- Sessions ----------

    def create_session(
        self,
        user_id: str,
        title: str,
        project_id: str = "",
    ) -> Dict[str, Any]:
        """Create a new session. Returns the session dict."""
        session_id = self._new_id()
        session_uid = self._new_id()
        now = self._now()
        directory = str(Path.cwd())
        self._execute(
            """
            INSERT INTO sessions
            (id, session_uid, user_id, project_id, session_kind, directory, title, status, created_at, updated_at, archived_at, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session_uid,
                user_id,
                project_id,
                "chat",
                directory,
                title,
                "active",
                now,
                now,
                None,
                None,
            ),
        )
        return {
            "id": session_id,
            "session_uid": session_uid,
            "user_id": user_id,
            "project_id": project_id,
            "session_kind": "chat",
            "directory": directory,
            "title": title,
            "status": "active",
            "created_at": now,
            "updated_at": now,
            "archived_at": None,
            "summary": None,
        }

    def get_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get session by ID. Returns session dict or None."""
        row = self._fetchone("SELECT * FROM sessions WHERE id = ?", (session_id,))
        if row is None:
            return None
        return self._row_to_dict(row, "sessions")

    def get_session_for_user(self, user_id: str, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by DB id, runtime namespace, or public uid for one user."""
        row = self._fetchone(
            """
            SELECT * FROM sessions
             WHERE user_id = ?
               AND (id = ? OR namespace = ? OR session_uid = ?)
             ORDER BY updated_at DESC
             LIMIT 1
            """,
            (user_id, session_id, session_id, session_id),
        )
        if row is None:
            return None
        return self._row_to_dict(row, "sessions")

    def find_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get a session by DB id, runtime namespace, or public uid."""
        row = self._fetchone(
            """
            SELECT * FROM sessions
             WHERE id = ? OR namespace = ? OR session_uid = ?
             ORDER BY updated_at DESC
             LIMIT 1
            """,
            (session_id, session_id, session_id),
        )
        if row is None:
            return None
        return self._row_to_dict(row, "sessions")

    def list_sessions(self, user_id: str, status: str = "active") -> List[Dict[str, Any]]:
        """List sessions for a user, optionally filtered by status."""
        rows = self._fetchall(
            "SELECT * FROM sessions WHERE user_id = ? AND status = ? ORDER BY updated_at DESC",
            (user_id, status),
        )
        return [self._row_to_dict(row, "sessions") for row in rows]

    def update_session(self, session_id: str, **fields):
        """Update arbitrary fields on a session."""
        if not fields:
            return

        fields.pop("id", None)
        fields["updated_at"] = self._now()

        if "summary" in fields:
            fields["summary"] = self._dump_json(fields["summary"])

        columns = ", ".join(f"{k} = ?" for k in fields.keys())
        values = list(fields.values()) + [session_id]
        self._execute(
            f"UPDATE sessions SET {columns} WHERE id = ?",
            tuple(values),
        )

    def upsert_runtime_session(
        self,
        session_id: str,
        user_id: str,
        *,
        owner: str = "",
        ip: str = "",
        workflow: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        project_id: str = "",
        directory: str = "",
        title: str = "",
        status: str = "active",
        summary: Any = None,
    ) -> Dict[str, Any]:
        """Create/update the DB row that backs one active User/IP/Workflow runtime."""
        existing = self.get_session(session_id)
        if existing is not None and existing.get("user_id") != user_id:
            raise ValueError("runtime session belongs to a different user")
        session_uid = (existing or {}).get("session_uid") or self._new_id()
        ip_value = ip_id or ip
        if existing is None:
            self.import_session(
                session_id,
                user_id,
                project_id=project_id or ip_value,
                directory=directory,
                title=title,
                status=status,
                summary=summary,
                session_uid=session_uid,
                namespace=session_id,
                owner=owner,
                workspace_id=workspace_id,
                ip_id=ip_value,
                ip=ip or ip_value,
                workflow=workflow,
                session_kind="runtime",
            )
        self.update_session(
            session_id,
            session_uid=session_uid,
            user_id=user_id,
            namespace=session_id,
            owner=owner,
            project_id=project_id or ip_value,
            workspace_id=workspace_id,
            ip_id=ip_value,
            ip=ip or ip_value,
            workflow=workflow,
            session_kind="runtime",
            directory=directory,
            title=title,
            status=status,
            summary=summary,
        )
        return self.get_session(session_id) or {
            "id": session_id,
            "session_uid": session_uid,
            "user_id": user_id,
            "namespace": session_id,
            "owner": owner,
            "ip_id": ip_value,
            "ip": ip or ip_value,
            "workflow": workflow,
            "session_kind": "runtime",
        }

    def archive_session(self, session_id: str):
        """Mark a session as archived."""
        self._execute(
            """
            UPDATE sessions
            SET status = ?, archived_at = ?, updated_at = ?
            WHERE id = ?
            """,
            ("archived", self._now(), self._now(), session_id),
        )

    def delete_session(self, session_id: str):
        """Delete a session and all associated messages and parts."""
        with self._lock:
            conn = self._connect()
            conn.execute("DELETE FROM parts WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM messages WHERE session_id = ?", (session_id,))
            conn.execute("DELETE FROM sessions WHERE id = ?", (session_id,))
            conn.commit()

    # ---------- Messages ----------

    def save_message(
        self,
        session_id: str,
        role: str,
        agent: str = "",
        model_id: str = "",
        provider_id: str = "",
        cost: float = 0.0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_reasoning: int = 0,
        error: Any = None,
        workflow: str = "",
        run_id: str = "",
        stage_id: str = "",
        todo_id: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        latency_ms: float = None,
        call_role: str = "primary",
        attempt: int = 1,
    ) -> Dict[str, Any]:
        """Save a message. Returns the message dict."""
        message_id = self._new_id()
        now = self._now()
        error_json = self._dump_json(error)
        self._execute(
            """
            INSERT INTO messages
            (id, session_id, role, agent, model_id, provider_id, created_at, completed_at, cost, tokens_input, tokens_output, tokens_reasoning, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                role,
                agent,
                model_id,
                provider_id,
                now,
                None,
                cost,
                tokens_input,
                tokens_output,
                tokens_reasoning,
                error_json,
            ),
        )
        if (
            role == "assistant"
            and (
                model_id
                or provider_id
                or cost
                or tokens_input
                or tokens_output
                or tokens_reasoning
            )
        ):
            self.record_llm_call(
                message_id=message_id,
                session_id=session_id,
                run_id=run_id,
                stage_id=stage_id,
                todo_id=todo_id,
                workspace_id=workspace_id,
                ip_id=ip_id,
                workflow=workflow or agent,
                model=model_id,
                provider=provider_id,
                call_role=call_role,
                attempt=attempt,
                tokens_input=tokens_input,
                tokens_output=tokens_output,
                tokens_reasoning=tokens_reasoning,
                cost_usd=cost,
                latency_ms=latency_ms,
                status="error" if error else "ok",
                error_type=str(error.get("code", "")) if isinstance(error, dict) else "",
                created_at=now,
            )
        return {
            "id": message_id,
            "session_id": session_id,
            "role": role,
            "agent": agent,
            "model_id": model_id,
            "provider_id": provider_id,
            "created_at": now,
            "completed_at": None,
            "cost": cost,
            "tokens_input": tokens_input,
            "tokens_output": tokens_output,
            "tokens_reasoning": tokens_reasoning,
            "error": error,
        }

    def get_messages(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all messages for a session, ordered by created_at."""
        rows = self._fetchall(
            "SELECT * FROM messages WHERE session_id = ? ORDER BY created_at ASC",
            (session_id,),
        )
        return [self._row_to_dict(row, "messages") for row in rows]

    # ---------- Parts ----------

    def save_part(
        self,
        message_id: str,
        session_id: str,
        type: str,
        text: str = "",
        tool_name: str = "",
        call_id: str = "",
        tool_status: str = "pending",
        tool_input: Any = None,
        tool_output: str = None,
        tool_error: str = None,
        tool_title: str = None,
        start_time: float = None,
        end_time: float = None,
        compacted_at: float = None,
        snapshot_hash: str = None,
        patch_hash: str = None,
        patch_files: Any = None,
        step_reason: str = "",
        step_cost: float = 0.0,
        step_tokens_input: int = 0,
        step_tokens_output: int = 0,
    ) -> Dict[str, Any]:
        """Save a message part. Returns the part dict."""
        part_id = self._new_id()
        now = self._now()
        tool_input_json = self._dump_json(tool_input)
        patch_files_json = self._dump_json(patch_files)
        self._execute(
            """
            INSERT INTO parts
            (id, message_id, session_id, type, created_at, text, tool_name, call_id, tool_status, tool_input, tool_output, tool_error, tool_title, start_time, end_time, compacted_at, snapshot_hash, patch_hash, patch_files, step_reason, step_cost, step_tokens_input, step_tokens_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                message_id,
                session_id,
                type,
                now,
                text,
                tool_name,
                call_id,
                tool_status,
                tool_input_json,
                tool_output,
                tool_error,
                tool_title,
                start_time,
                end_time,
                compacted_at,
                snapshot_hash,
                patch_hash,
                patch_files_json,
                step_reason,
                step_cost,
                step_tokens_input,
                step_tokens_output,
            ),
        )
        return {
            "id": part_id,
            "message_id": message_id,
            "session_id": session_id,
            "type": type,
            "created_at": now,
            "text": text,
            "tool_name": tool_name,
            "call_id": call_id,
            "tool_status": tool_status,
            "tool_input": tool_input,
            "tool_output": tool_output,
            "tool_error": tool_error,
            "tool_title": tool_title,
            "start_time": start_time,
            "end_time": end_time,
            "compacted_at": compacted_at,
            "snapshot_hash": snapshot_hash,
            "patch_hash": patch_hash,
            "patch_files": patch_files,
            "step_reason": step_reason,
            "step_cost": step_cost,
            "step_tokens_input": step_tokens_input,
            "step_tokens_output": step_tokens_output,
        }

    def get_parts(self, message_id: str) -> List[Dict[str, Any]]:
        """Get all parts for a message, ordered by created_at."""
        rows = self._fetchall(
            "SELECT * FROM parts WHERE message_id = ? ORDER BY created_at ASC",
            (message_id,),
        )
        return [self._row_to_dict(row, "parts") for row in rows]

    # ---------- WebSocket Connections ----------

    def create_ws_connection(
        self,
        connection_id: str,
        user_id: str,
        session_id: str,
        client_ip: str = "",
        user_agent: str = "",
    ) -> Dict[str, Any]:
        """Register a new WebSocket connection."""
        now = self._now()
        self._execute(
            """
            INSERT INTO ws_connections (connection_id, user_id, session_id, client_ip, user_agent, connected_at, last_ping_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (connection_id, user_id, session_id, client_ip, user_agent, now, now),
        )
        return {
            "connection_id": connection_id,
            "user_id": user_id,
            "session_id": session_id,
            "client_ip": client_ip,
            "user_agent": user_agent,
            "connected_at": now,
            "last_ping_at": now,
        }

    def update_ws_ping(self, connection_id: str):
        """Update the last_ping_at timestamp for a connection."""
        self._execute(
            "UPDATE ws_connections SET last_ping_at = ? WHERE connection_id = ?",
            (self._now(), connection_id),
        )

    def delete_ws_connection(self, connection_id: str):
        """Remove a WebSocket connection record."""
        self._execute(
            "DELETE FROM ws_connections WHERE connection_id = ?",
            (connection_id,),
        )

    def get_ws_connections(self, user_id: str = None, session_id: str = None) -> List[Dict[str, Any]]:
        """List WebSocket connections, optionally filtered."""
        if user_id and session_id:
            rows = self._fetchall(
                "SELECT * FROM ws_connections WHERE user_id = ? AND session_id = ? ORDER BY connected_at DESC",
                (user_id, session_id),
            )
        elif user_id:
            rows = self._fetchall(
                "SELECT * FROM ws_connections WHERE user_id = ? ORDER BY connected_at DESC",
                (user_id,),
            )
        elif session_id:
            rows = self._fetchall(
                "SELECT * FROM ws_connections WHERE session_id = ? ORDER BY connected_at DESC",
                (session_id,),
            )
        else:
            rows = self._fetchall(
                "SELECT * FROM ws_connections ORDER BY connected_at DESC"
            )
        return [dict(row) for row in rows]

    def import_user(
        self,
        user_id: str,
        username: str,
        display_name: str = None,
        password_hash: str = None,
        role: str = "user",
        created_at: float = None,
        last_login_at: float = None,
        email: str = None,
    ) -> Dict[str, Any]:
        now = created_at or self._now()
        email = self._normalize_email(email)
        self._execute(
            """
            INSERT OR IGNORE INTO users (id, username, display_name, email, password_hash, role, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, display_name, email, password_hash, role, now, last_login_at),
        )
        return self.get_user(user_id) or {
            "id": user_id,
            "username": username,
            "display_name": display_name,
            "email": email,
            "role": role,
        }

    def import_session(
        self,
        session_id: str,
        user_id: str,
        project_id: str = "",
        directory: str = "",
        title: str = "",
        status: str = "active",
        created_at: Optional[float] = None,
        updated_at: Optional[float] = None,
        archived_at: Optional[float] = None,
        summary: Any = None,
        session_uid: Optional[str] = None,
        namespace: str = "",
        owner: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        ip: str = "",
        workflow: str = "",
        session_kind: str = "chat",
    ) -> Dict[str, Any]:
        now = self._now()
        summary_json = self._dump_json(summary)
        session_uid = session_uid or self._new_id()
        self._execute(
            """
            INSERT OR IGNORE INTO sessions
            (id, session_uid, user_id, namespace, owner, project_id, workspace_id, ip_id, ip, workflow, session_kind,
             directory, title, status, created_at, updated_at, archived_at, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                session_uid,
                user_id,
                namespace,
                owner,
                project_id,
                workspace_id,
                ip_id,
                ip,
                workflow,
                session_kind,
                directory,
                title,
                status,
                created_at or now,
                updated_at or now,
                archived_at,
                summary_json,
            ),
        )
        return self.get_session(session_id) or {
            "id": session_id,
            "session_uid": session_uid,
            "user_id": user_id,
            "title": title,
        }

    def import_message(
        self,
        message_id: str,
        session_id: str,
        role: str,
        agent: str = "",
        model_id: str = "",
        provider_id: str = "",
        created_at: Optional[float] = None,
        completed_at: Optional[float] = None,
        cost: float = 0.0,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_reasoning: int = 0,
        error: Any = None,
    ) -> Dict[str, Any]:
        error_json = self._dump_json(error)
        self._execute(
            """
            INSERT OR IGNORE INTO messages
            (id, session_id, role, agent, model_id, provider_id, created_at, completed_at, cost, tokens_input, tokens_output, tokens_reasoning, error)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                message_id,
                session_id,
                role,
                agent,
                model_id,
                provider_id,
                created_at or self._now(),
                completed_at,
                cost,
                tokens_input,
                tokens_output,
                tokens_reasoning,
                error_json,
            ),
        )
        return {"id": message_id, "session_id": session_id, "role": role}

    def import_part(
        self,
        part_id: str,
        message_id: str,
        session_id: str,
        part_type: str,
        created_at: Optional[float] = None,
        text: Optional[str] = None,
        tool_name: Optional[str] = None,
        call_id: Optional[str] = None,
        tool_status: str = "pending",
        tool_input: Any = None,
        tool_output: Optional[str] = None,
        tool_error: Optional[str] = None,
        tool_title: Optional[str] = None,
        start_time: Optional[float] = None,
        end_time: Optional[float] = None,
        compacted_at: Optional[float] = None,
        snapshot_hash: Optional[str] = None,
        patch_hash: Optional[str] = None,
        patch_files: Any = None,
        step_reason: Optional[str] = None,
        step_cost: Optional[float] = None,
        step_tokens_input: Optional[int] = None,
        step_tokens_output: Optional[int] = None,
    ) -> Dict[str, Any]:
        tool_input_json = self._dump_json(tool_input)
        patch_files_json = self._dump_json(patch_files)
        self._execute(
            """
            INSERT OR IGNORE INTO parts
            (id, message_id, session_id, type, created_at, text, tool_name, call_id, tool_status, tool_input, tool_output, tool_error, tool_title, start_time, end_time, compacted_at, snapshot_hash, patch_hash, patch_files, step_reason, step_cost, step_tokens_input, step_tokens_output)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                part_id,
                message_id,
                session_id,
                part_type,
                created_at or self._now(),
                text,
                tool_name,
                call_id,
                tool_status,
                tool_input_json,
                tool_output,
                tool_error,
                tool_title,
                start_time,
                end_time,
                compacted_at,
                snapshot_hash,
                patch_hash,
                patch_files_json,
                step_reason,
                step_cost,
                step_tokens_input,
                step_tokens_output,
            ),
        )
        return {"id": part_id, "message_id": message_id, "type": part_type}

    # ---------- Session Queue ----------

    def enqueue_message(
        self,
        session_id: str,
        direction: str,
        msg_type: str,
        payload: Any = None,
        expires_at: Optional[float] = None,
    ) -> str:
        """Insert a message into the session queue. Returns the message id."""
        msg_id = self._new_id()
        now = self._now()
        payload_json = self._dump_json(payload)
        self._execute(
            """
            INSERT INTO session_queue
            (id, session_id, direction, msg_type, payload, created_at, processed_at, delivered_at, expires_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (msg_id, session_id, direction, msg_type, payload_json, now, None, None, expires_at),
        )
        return msg_id

    def dequeue_message(
        self,
        session_id: str,
        direction: str,
        timeout: Optional[float] = None,
    ) -> Optional[Dict[str, Any]]:
        """Blocking poll for the next unprocessed message in the given direction.

        Atomically marks the message as processed and returns it.
        Retries until a message arrives or timeout expires.
        """
        deadline = None
        if timeout is not None:
            deadline = self._now() + timeout

        while True:
            with self._lock:
                conn = self._connect()
                # Use IMMEDIATE to acquire the write lock early for atomicity
                conn.execute("BEGIN IMMEDIATE")
                try:
                    row = conn.execute(
                        """
                        SELECT * FROM session_queue
                        WHERE session_id = ? AND direction = ? AND processed_at IS NULL
                        ORDER BY created_at ASC
                        LIMIT 1
                        """,
                        (session_id, direction),
                    ).fetchone()

                    if row is not None:
                        now = self._now()
                        conn.execute(
                            "UPDATE session_queue SET processed_at = ? WHERE id = ?",
                            (now, row["id"]),
                        )
                        conn.commit()
                        result = self._row_to_dict(row, "session_queue")
                        result["processed_at"] = now
                        return result

                    conn.commit()
                except Exception:
                    conn.rollback()
                    raise

            if deadline is not None and self._now() >= deadline:
                return None
            time.sleep(0.05)

    def poll_messages(
        self,
        session_id: str,
        direction: str,
        since_id: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Non-blocking fetch of undelivered messages for a session and direction.

        Filters messages where delivered_at IS NULL, optionally after since_id.
        """
        if since_id is not None:
            rows = self._fetchall(
                """
                SELECT * FROM session_queue
                WHERE session_id = ? AND direction = ? AND delivered_at IS NULL
                AND created_at > (SELECT created_at FROM session_queue WHERE id = ?)
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, direction, since_id, limit),
            )
        else:
            rows = self._fetchall(
                """
                SELECT * FROM session_queue
                WHERE session_id = ? AND direction = ? AND delivered_at IS NULL
                ORDER BY created_at ASC
                LIMIT ?
                """,
                (session_id, direction, limit),
            )
        return [self._row_to_dict(row, "session_queue") for row in rows]

    def acknowledge_message(self, msg_id: str) -> None:
        """Mark a message as delivered."""
        self._execute(
            "UPDATE session_queue SET delivered_at = ? WHERE id = ?",
            (self._now(), msg_id),
        )

    def cleanup_old_messages(self, age_seconds: float = 3600) -> int:
        """Delete expired or old messages. Returns the number of rows deleted."""
        now = self._now()
        cutoff = now - age_seconds
        with self._lock:
            conn = self._connect()
            cursor = conn.execute(
                """
                DELETE FROM session_queue
                WHERE expires_at IS NOT NULL AND expires_at < ?
                OR created_at < ?
                """,
                (now, cutoff),
            )
            conn.commit()
            return cursor.rowcount

    def get_message(self, msg_id: str) -> Optional[Dict[str, Any]]:
        """Fetch a single queue message by id."""
        row = self._fetchone("SELECT * FROM session_queue WHERE id = ?", (msg_id,))
        if row is None:
            return None
        return self._row_to_dict(row, "session_queue")

    # ---------- Workflow observability ----------

    def upsert_workspace(
        self,
        name: str,
        owner_user_id: str = "",
        local_path: str = "",
        git_remote: str = "",
        git_branch: str = "",
        base_commit: str = "",
        head_commit: str = "",
        dirty_state: str = "",
        workspace_id: str = None,
    ) -> Dict[str, Any]:
        """Create or update a workspace registry row."""
        now = self._now()
        if workspace_id:
            existing = self.get_workspace(workspace_id)
        else:
            existing = None
            row = self._fetchone(
                "SELECT id FROM workspaces WHERE owner_user_id = ? AND name = ?",
                (owner_user_id, name),
            )
            if row is not None:
                existing = self.get_workspace(row["id"])

        if existing is None:
            workspace_id = workspace_id or self._new_id()
            self._execute(
                """
                INSERT INTO workspaces
                (id, owner_user_id, name, local_path, git_remote, git_branch,
                 base_commit, head_commit, dirty_state, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    workspace_id,
                    owner_user_id,
                    name,
                    local_path,
                    git_remote,
                    git_branch,
                    base_commit,
                    head_commit,
                    dirty_state,
                    now,
                    now,
                ),
            )
        else:
            workspace_id = existing["id"]
            self._execute(
                """
                UPDATE workspaces
                   SET local_path = ?, git_remote = ?, git_branch = ?,
                       base_commit = ?, head_commit = ?, dirty_state = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    local_path,
                    git_remote,
                    git_branch,
                    base_commit,
                    head_commit,
                    dirty_state,
                    now,
                    workspace_id,
                ),
            )
        return self.get_workspace(workspace_id)

    def get_workspace(self, workspace_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT * FROM workspaces WHERE id = ?", (workspace_id,))
        return dict(row) if row is not None else None

    def list_workspaces(self, owner_user_id: str = None) -> List[Dict[str, Any]]:
        if owner_user_id is None:
            rows = self._fetchall("SELECT * FROM workspaces ORDER BY updated_at DESC")
        else:
            rows = self._fetchall(
                "SELECT * FROM workspaces WHERE owner_user_id = ? ORDER BY updated_at DESC",
                (owner_user_id,),
            )
        return [dict(row) for row in rows]

    def upsert_ip_block(
        self,
        workspace_id: str,
        ip_name: str,
        ip_type: str = "",
        ssot_path: str = "",
        status: str = "active",
        ip_id: str = None,
    ) -> Dict[str, Any]:
        """Create or update an IP catalog row for a workspace."""
        now = self._now()
        if ip_id:
            existing = self.get_ip_block(ip_id)
        else:
            existing = None
            row = self._fetchone(
                "SELECT id FROM ip_blocks WHERE workspace_id = ? AND ip_name = ?",
                (workspace_id, ip_name),
            )
            if row is not None:
                existing = self.get_ip_block(row["id"])

        if existing is None:
            ip_id = ip_id or self._new_id()
            self._execute(
                """
                INSERT INTO ip_blocks
                (id, workspace_id, ip_name, ip_type, ssot_path, status, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (ip_id, workspace_id, ip_name, ip_type, ssot_path, status, now, now),
            )
        else:
            ip_id = existing["id"]
            self._execute(
                """
                UPDATE ip_blocks
                   SET ip_type = ?, ssot_path = ?, status = ?, updated_at = ?
                 WHERE id = ?
                """,
                (ip_type, ssot_path, status, now, ip_id),
            )
        return self.get_ip_block(ip_id)

    def get_ip_block(self, ip_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT * FROM ip_blocks WHERE id = ?", (ip_id,))
        return dict(row) if row is not None else None

    def list_ip_blocks(self, workspace_id: str) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            "SELECT * FROM ip_blocks WHERE workspace_id = ? ORDER BY ip_name",
            (workspace_id,),
        )
        return [dict(row) for row in rows]

    def get_ip_block_by_name(
        self,
        ip_name: str,
        workspace_id: str = None,
    ) -> Optional[Dict[str, Any]]:
        """Look up an IP row by its name. Without a workspace_id, returns the
        first match across workspaces (deterministic by created_at). Used by
        room-based APIs where the URL carries ip_name, not ip_id."""
        if workspace_id is not None:
            row = self._fetchone(
                "SELECT * FROM ip_blocks WHERE workspace_id = ? AND ip_name = ?",
                (workspace_id, ip_name),
            )
        else:
            row = self._fetchone(
                "SELECT * FROM ip_blocks WHERE ip_name = ? ORDER BY created_at ASC LIMIT 1",
                (ip_name,),
            )
        return dict(row) if row is not None else None

    @staticmethod
    def _permission_rank(permission: str) -> int:
        return _IP_PERMISSION_LEVELS.get(str(permission or "").strip().lower(), 0)

    def grant_ip_permission(
        self,
        ip_id: str,
        grantee_user_id: str,
        permission: str,
        granted_by_user_id: str = "",
        expires_at: float = None,
    ) -> Dict[str, Any]:
        """Grant a user permission to view/import/write/admin an IP."""
        normalized = str(permission or "").strip().lower()
        if normalized not in _IP_PERMISSION_LEVELS:
            raise ValueError(f"Invalid IP permission: {permission}")

        now = self._now()
        existing = self._fetchone(
            """
            SELECT id FROM ip_permissions
             WHERE ip_id = ? AND grantee_user_id = ? AND permission = ?
            """,
            (ip_id, grantee_user_id, normalized),
        )
        if existing is None:
            permission_id = self._new_id()
            self._execute(
                """
                INSERT INTO ip_permissions
                (id, ip_id, grantee_user_id, granted_by_user_id, permission, created_at, expires_at)
                VALUES (?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    permission_id,
                    ip_id,
                    grantee_user_id,
                    granted_by_user_id,
                    normalized,
                    now,
                    expires_at,
                ),
            )
        else:
            permission_id = existing["id"]
            self._execute(
                """
                UPDATE ip_permissions
                   SET granted_by_user_id = ?, created_at = ?, expires_at = ?
                 WHERE id = ?
                """,
                (granted_by_user_id, now, expires_at, permission_id),
            )
        return self.get_ip_permission(permission_id)

    def get_ip_permission(self, permission_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT * FROM ip_permissions WHERE id = ?", (permission_id,))
        return dict(row) if row is not None else None

    def list_ip_permissions(
        self,
        ip_id: str = None,
        grantee_user_id: str = None,
    ) -> List[Dict[str, Any]]:
        now = self._now()
        if ip_id is not None:
            rows = self._fetchall(
                """
                SELECT * FROM ip_permissions
                 WHERE ip_id = ? AND (expires_at IS NULL OR expires_at > ?)
                 ORDER BY created_at DESC
                """,
                (ip_id, now),
            )
        elif grantee_user_id is not None:
            rows = self._fetchall(
                """
                SELECT * FROM ip_permissions
                 WHERE grantee_user_id = ? AND (expires_at IS NULL OR expires_at > ?)
                 ORDER BY created_at DESC
                """,
                (grantee_user_id, now),
            )
        else:
            rows = self._fetchall(
                """
                SELECT * FROM ip_permissions
                 WHERE expires_at IS NULL OR expires_at > ?
                 ORDER BY created_at DESC
                """,
                (now,),
            )
        return [dict(row) for row in rows]

    def revoke_ip_permission(
        self,
        ip_id: str,
        grantee_user_id: str,
        permission: str = None,
    ) -> int:
        """Revoke one permission, or all IP permissions for a user when omitted."""
        if permission is None:
            cursor = self._execute(
                "DELETE FROM ip_permissions WHERE ip_id = ? AND grantee_user_id = ?",
                (ip_id, grantee_user_id),
            )
        else:
            cursor = self._execute(
                """
                DELETE FROM ip_permissions
                 WHERE ip_id = ? AND grantee_user_id = ? AND permission = ?
                """,
                (ip_id, grantee_user_id, str(permission or "").strip().lower()),
            )
        return int(cursor.rowcount or 0)

    def can_user_access_ip(
        self,
        ip_id: str,
        user_id: str,
        permission: str = "view",
    ) -> bool:
        """Return whether a user owns or has a sufficient grant for an IP."""
        requested_rank = self._permission_rank(permission)
        if requested_rank == 0:
            return False

        user = self.get_user(user_id)
        if user and user.get("role") == "admin":
            return True

        ip = self.get_ip_block(ip_id)
        if ip is None:
            return False
        workspace = self.get_workspace(ip["workspace_id"])
        if workspace and workspace.get("owner_user_id") == user_id:
            return True

        now = self._now()
        rows = self._fetchall(
            """
            SELECT permission FROM ip_permissions
             WHERE ip_id = ? AND grantee_user_id = ?
               AND (expires_at IS NULL OR expires_at > ?)
            """,
            (ip_id, user_id, now),
        )
        return any(self._permission_rank(row["permission"]) >= requested_rank for row in rows)

    def list_accessible_ip_blocks(
        self,
        user_id: str,
        permission: str = "view",
    ) -> List[Dict[str, Any]]:
        """List owned and shared IPs visible to a user at the requested level."""
        requested_rank = self._permission_rank(permission)
        if requested_rank == 0:
            return []

        rows = self._fetchall(
            """
            SELECT i.*, w.owner_user_id, w.name AS workspace_name, w.local_path AS workspace_path,
                   'owner' AS permission, 4 AS permission_rank
              FROM ip_blocks i
              JOIN workspaces w ON w.id = i.workspace_id
             WHERE w.owner_user_id = ?
            UNION ALL
            SELECT i.*, w.owner_user_id, w.name AS workspace_name, w.local_path AS workspace_path,
                   p.permission AS permission,
                   CASE p.permission
                       WHEN 'view' THEN 1
                       WHEN 'import' THEN 2
                       WHEN 'write' THEN 3
                       WHEN 'admin' THEN 4
                       ELSE 0
                   END AS permission_rank
              FROM ip_permissions p
              JOIN ip_blocks i ON i.id = p.ip_id
              JOIN workspaces w ON w.id = i.workspace_id
             WHERE p.grantee_user_id = ?
               AND (p.expires_at IS NULL OR p.expires_at > ?)
             ORDER BY ip_name
            """,
            (user_id, user_id, self._now()),
        )
        seen: set[str] = set()
        result: List[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            if int(item.get("permission_rank") or 0) < requested_rank:
                continue
            ip_id = item.get("id")
            if ip_id in seen:
                continue
            seen.add(ip_id)
            result.append(item)
        return result

    def register_artifact_version(
        self,
        ip_id: str,
        artifact_type: str,
        workspace_id: str = "",
        source_run_id: str = "",
        source_stage_id: str = "",
        version: str = "",
        label: str = "",
        root_path: str = "",
        primary_path: str = "",
        manifest: Any = None,
        sha256_tree: str = "",
        git_commit: str = "",
        git_tag: str = "",
        status: str = "active",
        metadata: Any = None,
    ) -> Dict[str, Any]:
        """Register an immutable artifact snapshot such as SSOT, RTL, or TB."""
        artifact_type = str(artifact_type or "").strip()
        version = str(version or "").strip()
        if not ip_id:
            raise ValueError("ip_id is required")
        if not artifact_type:
            raise ValueError("artifact_type is required")
        if not version:
            raise ValueError("version is required")
        artifact_version_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO artifact_versions
            (id, workspace_id, ip_id, artifact_type, version, label,
             root_path, primary_path, manifest, sha256_tree, git_commit,
             git_tag, status, source_run_id, source_stage_id, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_version_id,
                workspace_id,
                ip_id,
                artifact_type,
                version,
                label,
                root_path,
                primary_path,
                self._dump_json(manifest if manifest is not None else []),
                sha256_tree,
                git_commit,
                git_tag,
                status,
                source_run_id,
                source_stage_id,
                self._dump_json(metadata if metadata is not None else {}),
                now,
            ),
        )
        return self.get_artifact_version(artifact_version_id)

    def get_artifact_version(self, artifact_version_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT av.*, w.name AS workspace_name, w.local_path AS workspace_path,
                   i.ip_name AS ip_name
              FROM artifact_versions av
              LEFT JOIN workspaces w ON w.id = av.workspace_id
              LEFT JOIN ip_blocks i ON i.id = av.ip_id
             WHERE av.id = ?
            """,
            (artifact_version_id,),
        )
        return self._row_to_dict(row, "artifact_versions") if row is not None else None

    def list_artifact_versions(
        self,
        ip_id: str = None,
        workspace_id: str = None,
        artifact_type: str = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if ip_id is not None:
            clauses.append("av.ip_id = ?")
            values.append(ip_id)
        if workspace_id is not None:
            clauses.append("av.workspace_id = ?")
            values.append(workspace_id)
        if artifact_type is not None:
            clauses.append("av.artifact_type = ?")
            values.append(artifact_type)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"""
            SELECT av.*, w.name AS workspace_name, w.local_path AS workspace_path,
                   i.ip_name AS ip_name
              FROM artifact_versions av
              LEFT JOIN workspaces w ON w.id = av.workspace_id
              LEFT JOIN ip_blocks i ON i.id = av.ip_id
            {where}
             ORDER BY av.created_at DESC, av.artifact_type ASC, av.version DESC
            """,
            tuple(values),
        )
        return [self._row_to_dict(row, "artifact_versions") for row in rows]

    def link_artifact_versions(
        self,
        parent_version_id: str,
        child_version_id: str,
        relation: str = "generated_from",
        metadata: Any = None,
    ) -> Dict[str, Any]:
        """Create an idempotent edge in the artifact version graph."""
        if not parent_version_id or not child_version_id:
            raise ValueError("parent_version_id and child_version_id are required")
        relation = str(relation or "generated_from").strip()
        row = self._fetchone(
            """
            SELECT id FROM artifact_version_edges
             WHERE parent_version_id = ? AND child_version_id = ? AND relation = ?
            """,
            (parent_version_id, child_version_id, relation),
        )
        if row is None:
            edge_id = self._new_id()
            self._execute(
                """
                INSERT INTO artifact_version_edges
                (id, parent_version_id, child_version_id, relation, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?)
                """,
                (
                    edge_id,
                    parent_version_id,
                    child_version_id,
                    relation,
                    self._dump_json(metadata if metadata is not None else {}),
                    self._now(),
                ),
            )
        else:
            edge_id = row["id"]
        return self.get_artifact_version_edge(edge_id)

    def get_artifact_version_edge(self, edge_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT * FROM artifact_version_edges WHERE id = ?", (edge_id,))
        return self._row_to_dict(row, "artifact_version_edges") if row is not None else None

    def list_artifact_version_edges(
        self,
        parent_version_id: str = None,
        child_version_id: str = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if parent_version_id is not None:
            clauses.append("e.parent_version_id = ?")
            values.append(parent_version_id)
        if child_version_id is not None:
            clauses.append("e.child_version_id = ?")
            values.append(child_version_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"""
            SELECT e.*,
                   p.artifact_type AS parent_type, p.version AS parent_version,
                   c.artifact_type AS child_type, c.version AS child_version
              FROM artifact_version_edges e
              LEFT JOIN artifact_versions p ON p.id = e.parent_version_id
              LEFT JOIN artifact_versions c ON c.id = e.child_version_id
            {where}
             ORDER BY e.created_at ASC
            """,
            tuple(values),
        )
        return [self._row_to_dict(row, "artifact_version_edges") for row in rows]

    def attach_run_artifact_version(
        self,
        run_id: str,
        artifact_version_id: str,
        stage_id: str = "",
        role: str = "input",
        required: bool = True,
        metadata: Any = None,
    ) -> Dict[str, Any]:
        """Attach an artifact version to a workflow run as input/output/reference."""
        if not run_id or not artifact_version_id:
            raise ValueError("run_id and artifact_version_id are required")
        role = str(role or "input").strip()
        row = self._fetchone(
            """
            SELECT id FROM run_artifact_versions
             WHERE run_id = ? AND artifact_version_id = ? AND role = ?
            """,
            (run_id, artifact_version_id, role),
        )
        if row is None:
            link_id = self._new_id()
            self._execute(
                """
                INSERT INTO run_artifact_versions
                (id, run_id, stage_id, artifact_version_id, role, required, metadata, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    link_id,
                    run_id,
                    stage_id,
                    artifact_version_id,
                    role,
                    1 if required else 0,
                    self._dump_json(metadata if metadata is not None else {}),
                    self._now(),
                ),
            )
        else:
            link_id = row["id"]
        rows = self.list_run_artifact_versions(run_id=run_id)
        for item in rows:
            if item.get("id") == link_id:
                return item
        return {"id": link_id}

    def list_run_artifact_versions(
        self,
        run_id: str = None,
        artifact_type: str = None,
        role: str = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if run_id is not None:
            clauses.append("rav.run_id = ?")
            values.append(run_id)
        if artifact_type is not None:
            clauses.append("av.artifact_type = ?")
            values.append(artifact_type)
        if role is not None:
            clauses.append("rav.role = ?")
            values.append(role)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"""
            SELECT rav.*, r.session_id, r.workflow, r.status AS run_status,
                   r.started_at, r.ended_at, r.duration_ms, r.error_summary,
                   av.workspace_id, av.ip_id, av.artifact_type, av.version,
                   av.label, av.root_path, av.primary_path, av.sha256_tree,
                   av.git_commit, av.git_tag, av.status AS artifact_status,
                   w.name AS workspace_name, i.ip_name AS ip_name
              FROM run_artifact_versions rav
              JOIN artifact_versions av ON av.id = rav.artifact_version_id
              LEFT JOIN workflow_runs r ON r.id = rav.run_id
              LEFT JOIN workspaces w ON w.id = av.workspace_id
              LEFT JOIN ip_blocks i ON i.id = av.ip_id
            {where}
             ORDER BY r.started_at DESC, rav.created_at ASC
            """,
            tuple(values),
        )
        return [self._row_to_dict(row, "run_artifact_versions") for row in rows]

    def list_run_artifact_version_sets(
        self,
        workflows: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """Return one row per run with artifact versions grouped by type."""
        clauses: list[str] = []
        values: list[Any] = []
        if workflows:
            placeholders = ", ".join(["?"] * len(workflows))
            clauses.append(f"r.workflow IN ({placeholders})")
            values.extend(workflows)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"""
            SELECT r.id AS run_id, r.session_id, r.workspace_id, r.ip_id,
                   r.workflow, r.mode, r.model_profile, r.reasoning_effort,
                   r.status, r.started_at, r.ended_at, r.duration_ms,
                   r.error_summary, w.name AS workspace_name, i.ip_name AS ip_name,
                   COALESCE(llm.llm_calls, 0) AS llm_calls,
                   COALESCE(llm.tokens_input, 0) AS tokens_input,
                   COALESCE(llm.tokens_output, 0) AS tokens_output,
                   COALESCE(llm.tokens_reasoning, 0) AS tokens_reasoning,
                   COALESCE(llm.cost, 0) AS cost
              FROM workflow_runs r
              LEFT JOIN workspaces w ON w.id = r.workspace_id
              LEFT JOIN ip_blocks i ON i.id = r.ip_id
              LEFT JOIN (
                  SELECT run_id,
                         COUNT(*) AS llm_calls,
                         SUM(tokens_input) AS tokens_input,
                         SUM(tokens_output) AS tokens_output,
                         SUM(tokens_reasoning) AS tokens_reasoning,
                         SUM(cost_usd) AS cost
                    FROM llm_calls
                   WHERE run_id IS NOT NULL AND run_id != ''
                   GROUP BY run_id
              ) llm ON llm.run_id = r.id
            {where}
             ORDER BY r.started_at DESC, r.created_at DESC
            """,
            tuple(values),
        )
        result: list[Dict[str, Any]] = []
        for row in rows:
            item = dict(row)
            links = self.list_run_artifact_versions(run_id=item["run_id"])
            versions_by_type: dict[str, list[Dict[str, Any]]] = {}
            for link in links:
                artifact_type = link.get("artifact_type") or "unknown"
                versions_by_type.setdefault(artifact_type, []).append(link)
            item["artifact_versions"] = versions_by_type
            result.append(item)
        return result

    def register_rtl_version(
        self,
        ip_id: str,
        workspace_id: str = "",
        source_run_id: str = "",
        source_stage_id: str = "",
        version: str = "",
        label: str = "",
        rtl_root: str = "",
        filelist_path: str = "",
        top_module: str = "",
        artifact_manifest: Any = None,
        sha256_tree: str = "",
        git_commit: str = "",
        git_tag: str = "",
        status: str = "active",
        metadata: Any = None,
    ) -> Dict[str, Any]:
        """Register an immutable RTL handoff snapshot."""
        version = str(version or "").strip()
        if not ip_id:
            raise ValueError("ip_id is required")
        if not version:
            raise ValueError("version is required")
        artifact_version = self.register_artifact_version(
            ip_id=ip_id,
            workspace_id=workspace_id,
            source_run_id=source_run_id,
            source_stage_id=source_stage_id,
            artifact_type="rtl",
            version=version,
            label=label,
            root_path=rtl_root,
            primary_path=filelist_path,
            manifest=artifact_manifest if artifact_manifest is not None else [],
            sha256_tree=sha256_tree,
            git_commit=git_commit,
            git_tag=git_tag,
            status=status,
            metadata=metadata if metadata is not None else {},
        )
        rtl_version_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO rtl_versions
            (id, artifact_version_id, ip_id, workspace_id, source_run_id, source_stage_id, version,
             label, rtl_root, filelist_path, top_module, artifact_manifest,
             sha256_tree, git_commit, git_tag, status, metadata, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                rtl_version_id,
                artifact_version["id"],
                ip_id,
                workspace_id,
                source_run_id,
                source_stage_id,
                version,
                label,
                rtl_root,
                filelist_path,
                top_module,
                self._dump_json(artifact_manifest if artifact_manifest is not None else []),
                sha256_tree,
                git_commit,
                git_tag,
                status,
                self._dump_json(metadata if metadata is not None else {}),
                now,
            ),
        )
        return self.get_rtl_version(rtl_version_id)

    def get_rtl_version(self, rtl_version_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT rv.*, w.name AS workspace_name, w.local_path AS workspace_path,
                   i.ip_name AS ip_name
              FROM rtl_versions rv
              LEFT JOIN workspaces w ON w.id = rv.workspace_id
              LEFT JOIN ip_blocks i ON i.id = rv.ip_id
             WHERE rv.id = ?
            """,
            (rtl_version_id,),
        )
        return self._row_to_dict(row, "rtl_versions") if row is not None else None

    def list_rtl_versions(
        self,
        ip_id: str = None,
        workspace_id: str = None,
    ) -> List[Dict[str, Any]]:
        clauses: list[str] = []
        values: list[Any] = []
        if ip_id is not None:
            clauses.append("rv.ip_id = ?")
            values.append(ip_id)
        if workspace_id is not None:
            clauses.append("rv.workspace_id = ?")
            values.append(workspace_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"""
            SELECT rv.*, w.name AS workspace_name, w.local_path AS workspace_path,
                   i.ip_name AS ip_name
              FROM rtl_versions rv
              LEFT JOIN workspaces w ON w.id = rv.workspace_id
              LEFT JOIN ip_blocks i ON i.id = rv.ip_id
            {where}
             ORDER BY rv.created_at DESC, rv.version DESC
            """,
            tuple(values),
        )
        return [self._row_to_dict(row, "rtl_versions") for row in rows]

    def start_workflow_run(
        self,
        session_id: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        rtl_version_id: str = "",
        workflow: str = "",
        mode: str = "interactive",
        model_profile: str = "",
        reasoning_effort: str = "",
        trigger: str = "",
        input_summary: str = "",
        status: str = "running",
        trigger_source: str = "",
        orchestrator_run_id: str = "",
    ) -> Dict[str, Any]:
        run_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO workflow_runs
            (id, session_id, workspace_id, ip_id, rtl_version_id, workflow, mode, model_profile,
             reasoning_effort, status, started_at, ended_at, duration_ms,
             trigger, input_summary, error_summary, created_at, updated_at,
             trigger_source, orchestrator_run_id)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                session_id,
                workspace_id,
                ip_id,
                rtl_version_id,
                workflow,
                mode,
                model_profile,
                reasoning_effort,
                status,
                now,
                None,
                None,
                trigger,
                input_summary,
                None,
                now,
                now,
                trigger_source,
                orchestrator_run_id,
            ),
        )
        return self.get_workflow_run(run_id)

    def finish_workflow_run(
        self,
        run_id: str,
        status: str,
        error_summary: str = None,
    ) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT started_at FROM workflow_runs WHERE id = ?", (run_id,))
        if row is None:
            return None
        now = self._now()
        started = row["started_at"] or now
        self._execute(
            """
            UPDATE workflow_runs
               SET status = ?, ended_at = ?, duration_ms = ?,
                   error_summary = ?, updated_at = ?
             WHERE id = ?
            """,
            (status, now, (now - started) * 1000, error_summary, now, run_id),
        )
        return self.get_workflow_run(run_id)

    def get_workflow_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT r.*, w.name AS workspace_name, w.local_path AS workspace_path,
                   i.ip_name AS ip_name, i.ssot_path AS ssot_path,
                   rv.version AS rtl_version,
                   rv.sha256_tree AS rtl_sha256_tree,
                   rv.git_commit AS rtl_git_commit,
                   rv.git_tag AS rtl_git_tag,
                   rv.filelist_path AS rtl_filelist_path,
                   rv.top_module AS rtl_top_module
              FROM workflow_runs r
              LEFT JOIN workspaces w ON w.id = r.workspace_id
              LEFT JOIN ip_blocks i ON i.id = r.ip_id
              LEFT JOIN rtl_versions rv ON rv.id = r.rtl_version_id
             WHERE r.id = ?
            """,
            (run_id,),
        )
        return dict(row) if row is not None else None

    def start_workflow_stage(
        self,
        run_id: str,
        stage_name: str,
        status: str = "running",
        attempt: int = 1,
        rtl_version_id: str = "",
    ) -> Dict[str, Any]:
        stage_id = self._new_id()
        now = self._now()
        if not rtl_version_id:
            row = self._fetchone(
                "SELECT rtl_version_id FROM workflow_runs WHERE id = ?",
                (run_id,),
            )
            rtl_version_id = row["rtl_version_id"] if row is not None else ""
        self._execute(
            """
            INSERT INTO workflow_stages
            (id, run_id, rtl_version_id, stage_name, status, attempt, started_at, ended_at,
             duration_ms, error_summary, created_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                stage_id,
                run_id,
                rtl_version_id,
                stage_name,
                status,
                attempt,
                now,
                None,
                None,
                None,
                now,
                now,
            ),
        )
        return self.get_workflow_stage(stage_id)

    def finish_workflow_stage(
        self,
        stage_id: str,
        status: str,
        error_summary: str = None,
    ) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT started_at FROM workflow_stages WHERE id = ?", (stage_id,))
        if row is None:
            return None
        now = self._now()
        started = row["started_at"] or now
        self._execute(
            """
            UPDATE workflow_stages
               SET status = ?, ended_at = ?, duration_ms = ?,
                   error_summary = ?, updated_at = ?
             WHERE id = ?
            """,
            (status, now, (now - started) * 1000, error_summary, now, stage_id),
        )
        return self.get_workflow_stage(stage_id)

    def get_workflow_stage(self, stage_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone("SELECT * FROM workflow_stages WHERE id = ?", (stage_id,))
        return dict(row) if row is not None else None

    def record_workflow_event(
        self,
        run_id: str,
        event_type: str,
        payload: Any = None,
        stage_id: str = "",
    ) -> Dict[str, Any]:
        event_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO workflow_events (id, run_id, stage_id, event_type, payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, run_id, stage_id, event_type, self._dump_json(payload), now),
        )
        return self.list_workflow_events(run_id=run_id, event_id=event_id)[0]

    def list_workflow_events(
        self,
        run_id: str = None,
        event_id: str = None,
    ) -> List[Dict[str, Any]]:
        if event_id is not None:
            rows = self._fetchall("SELECT * FROM workflow_events WHERE id = ?", (event_id,))
        elif run_id is not None:
            rows = self._fetchall(
                "SELECT * FROM workflow_events WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
        else:
            rows = self._fetchall("SELECT * FROM workflow_events ORDER BY created_at ASC")
        return [self._row_to_dict(row, "workflow_events") for row in rows]

    def upsert_workflow_todo(
        self,
        run_id: str,
        title: str,
        detail: str = "",
        criteria: str = "",
        notes: Any = None,
        status: str = "pending",
        source: str = "",
        owner_file: str = "",
        owner_module: str = "",
        source_refs: Any = None,
        evidence: Any = None,
        todo_id: str = None,
    ) -> Dict[str, Any]:
        now = self._now()
        if todo_id and self._fetchone("SELECT id FROM workflow_todos WHERE id = ?", (todo_id,)):
            self._execute(
                """
                UPDATE workflow_todos
                   SET source = ?, title = ?, detail = ?, criteria = ?, notes = ?, status = ?,
                       owner_file = ?, owner_module = ?, source_refs = ?, evidence = ?,
                       updated_at = ?
                 WHERE id = ?
                """,
                (
                    source,
                    title,
                    detail,
                    criteria,
                    self._dump_json(notes),
                    status,
                    owner_file,
                    owner_module,
                    self._dump_json(source_refs),
                    self._dump_json(evidence),
                    now,
                    todo_id,
                ),
            )
        else:
            todo_id = todo_id or self._new_id()
            self._execute(
                """
                INSERT INTO workflow_todos
                (id, run_id, source, title, detail, criteria, notes, status, owner_file,
                 owner_module, source_refs, evidence, created_at, updated_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    todo_id,
                    run_id,
                    source,
                    title,
                    detail,
                    criteria,
                    self._dump_json(notes),
                    status,
                    owner_file,
                    owner_module,
                    self._dump_json(source_refs),
                    self._dump_json(evidence),
                    now,
                    now,
                ),
            )
        rows = self.list_workflow_todos(run_id=run_id, todo_id=todo_id)
        return rows[0]

    def list_workflow_todos(
        self,
        run_id: str = None,
        todo_id: str = None,
    ) -> List[Dict[str, Any]]:
        if todo_id is not None:
            rows = self._fetchall("SELECT * FROM workflow_todos WHERE id = ?", (todo_id,))
        elif run_id is not None:
            rows = self._fetchall(
                "SELECT * FROM workflow_todos WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
        else:
            rows = self._fetchall("SELECT * FROM workflow_todos ORDER BY created_at ASC")
        return [self._row_to_dict(row, "workflow_todos") for row in rows]

    def record_todo_event(
        self,
        todo_id: str,
        event_type: str,
        reason: str = "",
        evidence: Any = None,
    ) -> Dict[str, Any]:
        event_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO todo_events (id, todo_id, event_type, reason, evidence, created_at)
            VALUES (?, ?, ?, ?, ?, ?)
            """,
            (event_id, todo_id, event_type, reason, self._dump_json(evidence), now),
        )
        if event_type in {"pending", "in_progress", "completed", "approved", "rejected", "blocked"}:
            self._execute(
                "UPDATE workflow_todos SET status = ?, evidence = ?, updated_at = ? WHERE id = ?",
                (event_type, self._dump_json(evidence), now, todo_id),
            )
        rows = self._fetchall("SELECT * FROM todo_events WHERE id = ?", (event_id,))
        return self._row_to_dict(rows[0], "todo_events")

    def record_trace_event(
        self,
        event_type: str,
        payload: Any = None,
        session_id: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        workflow: str = "",
        run_id: str = "",
        stage_id: str = "",
        todo_id: str = "",
        message_id: str = "",
        llm_call_id: str = "",
        artifact_id: str = "",
        actor_user_id: str = "",
        correlation_id: str = "",
        causation_id: str = "",
        idempotency_key: str = "",
        created_at: float = None,
    ) -> Dict[str, Any]:
        """Append a canonical trace event, returning an existing row for duplicate keys."""
        key = str(idempotency_key or "").strip()
        if key:
            existing = self._fetchone(
                "SELECT * FROM trace_events WHERE idempotency_key = ?",
                (key,),
            )
            if existing is not None:
                return self._row_to_dict(existing, "trace_events")

        event_id = self._new_id()
        now = created_at if created_at is not None else self._now()
        self._execute(
            """
            INSERT INTO trace_events
            (id, event_type, session_id, workspace_id, ip_id, workflow, run_id,
             stage_id, todo_id, message_id, llm_call_id, artifact_id,
             actor_user_id, correlation_id, causation_id, idempotency_key,
             payload, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                event_id,
                event_type,
                session_id,
                workspace_id,
                ip_id,
                workflow,
                run_id,
                stage_id,
                todo_id,
                message_id,
                llm_call_id,
                artifact_id,
                actor_user_id,
                correlation_id,
                causation_id,
                key or None,
                self._dump_json(payload),
                now,
            ),
        )
        return self.list_trace_events(event_id=event_id)[0]

    def list_trace_events(
        self,
        event_id: str = None,
        session_id: str = None,
        run_id: str = None,
        todo_id: str = None,
        correlation_id: str = None,
    ) -> List[Dict[str, Any]]:
        """List canonical trace events in append order with optional narrow filters."""
        clauses: list[str] = []
        values: list[Any] = []
        if event_id is not None:
            clauses.append("id = ?")
            values.append(event_id)
        if session_id is not None:
            clauses.append("session_id = ?")
            values.append(session_id)
        if run_id is not None:
            clauses.append("run_id = ?")
            values.append(run_id)
        if todo_id is not None:
            clauses.append("todo_id = ?")
            values.append(todo_id)
        if correlation_id is not None:
            clauses.append("correlation_id = ?")
            values.append(correlation_id)
        where = f" WHERE {' AND '.join(clauses)}" if clauses else ""
        rows = self._fetchall(
            f"SELECT * FROM trace_events{where} ORDER BY created_at ASC, id ASC",
            tuple(values),
        )
        return [self._row_to_dict(row, "trace_events") for row in rows]

    # ---------- Orchestrator chat (over trace_events) ----------
    #
    # Chat is stored on the canonical trace ledger, not a separate table:
    #   - event_type='chat_message' is a human-authored post.
    #       ip_id IS NULL  => the special _global room
    #       ip_id = <id>   => the per-IP room
    #       payload      = {"content": str, "display_name": str}
    #       actor_user_id is the poster.
    #   - event_type='chat_consumed' marks an agent having read a chat in its
    #     next ReAct iteration. correlation_id = the original chat message id.
    #
    # This keeps room-based reads on the existing
    # idx_trace_events_context(workspace_id, ip_id, workflow, created_at)
    # and lets the observability dashboard show feedback alongside workflow
    # events on the same timeline.

    def record_chat_message(
        self,
        ip_id: Optional[str],
        user_id: str,
        content: str,
        display_name: str = "",
        workspace_id: str = "",
        role: str = "user",
    ) -> Dict[str, Any]:
        """Append a chat post for either an IP room (ip_id set) or the
        global room (ip_id is None / falsy).

        ``role`` distinguishes posters on the same chat_message timeline:
        - ``"user"`` (default): human-authored — preserves prior behavior.
        - ``"assistant"``: orchestrator LLM natural-language reply.
        - ``"thought"``: exposed reasoning text.
        - ``"tool"``: raw terminal-style tool-call line.
        - ``"tool_result"``: raw terminal-style tool result/observation.
        Stored in the payload so existing readers ignoring it still work."""
        ip_value = ip_id or ""
        payload = {
            "content": content,
            "display_name": display_name or "",
            "role": role or "user",
        }
        return self.record_trace_event(
            event_type="chat_message",
            payload=payload,
            workspace_id=workspace_id,
            ip_id=ip_value,
            actor_user_id=user_id,
        )

    def record_chat_consumed(
        self,
        chat_id: str,
        session_id: str,
        ip_id: Optional[str] = None,
    ) -> Dict[str, Any]:
        """Mark a chat as read by the agent on a given session bridge."""
        return self.record_trace_event(
            event_type="chat_consumed",
            payload={"by": "agent"},
            session_id=session_id,
            ip_id=ip_id or "",
            correlation_id=chat_id,
        )

    def list_chat_messages(
        self,
        ip_id: Optional[str],
        limit: int = 50,
        after_id: str = None,
        since: Optional[float] = None,
    ) -> List[Dict[str, Any]]:
        """Return chat messages for a room, newest first. ip_id=None or ""
        selects the global room (ip_id IS NULL or = '').
        since: unix timestamp (float); only rows with created_at > since are returned."""
        clauses = ["event_type = ?"]
        values: list[Any] = ["chat_message"]
        if ip_id:
            clauses.append("ip_id = ?")
            values.append(ip_id)
        else:
            clauses.append("(ip_id IS NULL OR ip_id = '')")
        if after_id:
            clauses.append(
                "created_at > (SELECT created_at FROM trace_events WHERE id = ?)"
            )
            values.append(after_id)
        if since is not None:
            clauses.append("created_at > ?")
            values.append(float(since))
        where = " WHERE " + " AND ".join(clauses)
        rows = self._fetchall(
            f"SELECT * FROM trace_events{where} ORDER BY created_at DESC, id DESC LIMIT ?",
            tuple(values + [int(limit)]),
        )
        return [self._row_to_dict(row, "trace_events") for row in rows]

    def list_chat_unconsumed_for(
        self,
        session_id: str,
        ip_id: Optional[str],
        after_id: str = None,
    ) -> List[Dict[str, Any]]:
        """Return chat messages the given session bridge has NOT yet
        recorded as consumed. Ordered oldest-first so the agent reads them
        in chronological order on its next iteration."""
        clauses = ["event_type = ?"]
        values: list[Any] = ["chat_message"]
        if ip_id:
            clauses.append("ip_id = ?")
            values.append(ip_id)
        else:
            clauses.append("(ip_id IS NULL OR ip_id = '')")
        if after_id:
            clauses.append(
                "created_at > (SELECT created_at FROM trace_events WHERE id = ?)"
            )
            values.append(after_id)
        clauses.append(
            """id NOT IN (
                SELECT correlation_id FROM trace_events
                 WHERE event_type = 'chat_consumed'
                   AND session_id = ?
                   AND correlation_id IS NOT NULL
            )"""
        )
        values.append(session_id)
        where = " WHERE " + " AND ".join(clauses)
        rows = self._fetchall(
            f"SELECT * FROM trace_events{where} ORDER BY created_at ASC, id ASC",
            tuple(values),
        )
        return [self._row_to_dict(row, "trace_events") for row in rows]

    def latest_chat_consumed_id(
        self,
        session_id: str,
        ip_id: Optional[str] = None,
    ) -> Optional[str]:
        """Last chat message id this session has marked consumed — used to
        seed the bridge watermark when the agent restarts."""
        clauses = ["event_type = 'chat_consumed'", "session_id = ?"]
        values: list[Any] = [session_id]
        if ip_id:
            clauses.append("ip_id = ?")
            values.append(ip_id)
        else:
            clauses.append("(ip_id IS NULL OR ip_id = '')")
        where = " WHERE " + " AND ".join(clauses)
        row = self._fetchone(
            f"SELECT correlation_id FROM trace_events{where} "
            "ORDER BY created_at DESC, id DESC LIMIT 1",
            tuple(values),
        )
        if row is None:
            return None
        return row["correlation_id"]

    def record_llm_call(
        self,
        session_id: str = "",
        message_id: str = "",
        run_id: str = "",
        stage_id: str = "",
        todo_id: str = "",
        workspace_id: str = "",
        ip_id: str = "",
        workflow: str = "",
        model: str = "",
        provider: str = "",
        base_url_hash: str = "",
        call_role: str = "primary",
        attempt: int = 1,
        tokens_input: int = 0,
        tokens_output: int = 0,
        tokens_reasoning: int = 0,
        cache_read_tokens: int = 0,
        cache_write_tokens: int = 0,
        cost_usd: float = 0.0,
        latency_ms: float = None,
        status: str = "ok",
        error_type: str = "",
        created_at: float = None,
        completed_at: float = None,
    ) -> Dict[str, Any]:
        call_id = self._new_id()
        now = self._now()
        created = created_at or now
        completed = completed_at if completed_at is not None else now
        self._execute(
            """
            INSERT INTO llm_calls
            (id, message_id, run_id, stage_id, todo_id, session_id, workspace_id,
             ip_id, workflow, model, provider, base_url_hash, call_role, attempt,
             tokens_input, tokens_output, tokens_reasoning, cache_read_tokens,
             cache_write_tokens, cost_usd, latency_ms, status, error_type,
             created_at, completed_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                call_id,
                message_id,
                run_id,
                stage_id,
                todo_id,
                session_id,
                workspace_id,
                ip_id,
                workflow,
                model,
                provider,
                base_url_hash,
                call_role,
                attempt,
                tokens_input,
                tokens_output,
                tokens_reasoning,
                cache_read_tokens,
                cache_write_tokens,
                cost_usd,
                latency_ms,
                status,
                error_type,
                created,
                completed,
            ),
        )
        return self.list_llm_calls(call_id=call_id)[0]

    def list_llm_calls(
        self,
        session_id: str = None,
        run_id: str = None,
        call_id: str = None,
    ) -> List[Dict[str, Any]]:
        if call_id is not None:
            rows = self._fetchall("SELECT * FROM llm_calls WHERE id = ?", (call_id,))
        elif run_id is not None:
            rows = self._fetchall(
                "SELECT * FROM llm_calls WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
        elif session_id is not None:
            rows = self._fetchall(
                "SELECT * FROM llm_calls WHERE session_id = ? ORDER BY created_at ASC",
                (session_id,),
            )
        else:
            rows = self._fetchall("SELECT * FROM llm_calls ORDER BY created_at ASC")
        return [dict(row) for row in rows]

    def summarize_llm_usage_for_user_ip(
        self,
        *,
        user_id: str = "",
        username: str = "",
        ip: str = "",
    ) -> Dict[str, Any]:
        """Aggregate LLM usage for one visible user/IP scope.

        Runtime worker calls sometimes store the runtime namespace in
        llm_calls.session_id (``owner/ip/workflow``), while DB-backed workflow
        rows may store an internal IP id. Join sessions when possible and keep
        the namespace-prefix fallback so live/local worker accounting still
        resolves to the active user's IP.
        """
        uid = str(user_id or "").strip()
        owner = str(username or "").strip()
        ip_name = str(ip or "").strip()

        def like_escape(value: str) -> str:
            return (
                str(value or "")
                .replace("\\", "\\\\")
                .replace("%", "\\%")
                .replace("_", "\\_")
            )

        def prefix_upper_bound(value: str) -> str:
            if not value:
                return ""
            return value[:-1] + chr(ord(value[-1]) + 1)

        # No authenticated owner means legacy/local-admin visibility. Keep it
        # simple and avoid the old OR-join that made /healthz CPU-bound.
        if ip_name and not uid and not owner:
            row = self._fetchone(
                """
                SELECT COUNT(*) AS calls,
                       COALESCE(SUM(tokens_input), 0) AS tokens_input,
                       COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens,
                       COALESCE(SUM(tokens_output), 0) AS tokens_output,
                       COALESCE(SUM(tokens_reasoning), 0) AS tokens_reasoning,
                       COALESCE(SUM(cost_usd), 0.0) AS cost_usd
                  FROM llm_calls
                 WHERE ip_id = ?
                    OR session_id LIKE ? ESCAPE '\\'
                """,
                (ip_name, f"%/{like_escape(ip_name)}/%"),
            )
            data = dict(row) if row is not None else {}
            return {
                "calls": int(data.get("calls") or 0),
                "tokens_input": int(data.get("tokens_input") or 0),
                "cache_read_tokens": int(data.get("cache_read_tokens") or 0),
                "tokens_output": int(data.get("tokens_output") or 0),
                "tokens_reasoning": int(data.get("tokens_reasoning") or 0),
                "cost_usd": float(data.get("cost_usd") or 0.0),
            }

        runtime_exact = f"{owner}/{ip_name}" if owner and ip_name else ""
        runtime_prefix = (
            f"{owner}/{ip_name}/"
            if owner and ip_name
            else (f"{owner}/" if owner else "")
        )
        runtime_upper = prefix_upper_bound(runtime_prefix)

        session_user_clauses: list[str] = []
        session_user_values: list[Any] = []
        if uid:
            session_user_clauses.append("user_id = ?")
            session_user_values.append(uid)
        if owner:
            owner_prefix = f"{owner}/"
            session_user_clauses.append("owner = ?")
            session_user_values.append(owner)
            session_user_clauses.append("namespace = ?")
            session_user_values.append(owner)
            session_user_clauses.append("(namespace >= ? AND namespace < ?)")
            session_user_values.extend([owner_prefix, prefix_upper_bound(owner_prefix)])

        session_ip_clauses: list[str] = []
        session_ip_values: list[Any] = []
        if ip_name:
            session_ip_clauses.extend(["ip_id = ?", "ip = ?"])
            session_ip_values.extend([ip_name, ip_name])
            if runtime_exact:
                session_ip_clauses.append("namespace = ?")
                session_ip_values.append(runtime_exact)
            if runtime_prefix:
                session_ip_clauses.append("(namespace >= ? AND namespace < ?)")
                session_ip_values.extend([runtime_prefix, runtime_upper])

        session_clauses: list[str] = []
        session_values: list[Any] = []
        if session_user_clauses:
            session_clauses.append("(" + " OR ".join(session_user_clauses) + ")")
            session_values.extend(session_user_values)
        if session_ip_clauses:
            session_clauses.append("(" + " OR ".join(session_ip_clauses) + ")")
            session_values.extend(session_ip_values)
        session_where = " AND ".join(session_clauses) if session_clauses else "0 = 1"

        row = self._fetchone(
            f"""
            WITH target_sessions AS (
                    SELECT id, namespace, session_uid
                      FROM sessions
                     WHERE {session_where}
                 ),
                 target_keys(key) AS (
                    SELECT id FROM target_sessions WHERE id IS NOT NULL AND id != ''
                    UNION
                    SELECT namespace FROM target_sessions WHERE namespace IS NOT NULL AND namespace != ''
                    UNION
                    SELECT session_uid FROM target_sessions WHERE session_uid IS NOT NULL AND session_uid != ''
                 ),
                 scoped AS (
                    SELECT l.id,
                           l.tokens_input,
                           l.cache_read_tokens,
                           l.tokens_output,
                           l.tokens_reasoning,
                           l.cost_usd
                      FROM llm_calls l
                     WHERE ? != '' AND l.session_id = ?
                    UNION
                    SELECT l.id,
                           l.tokens_input,
                           l.cache_read_tokens,
                           l.tokens_output,
                           l.tokens_reasoning,
                           l.cost_usd
                      FROM llm_calls l
                     WHERE ? != '' AND l.session_id >= ? AND l.session_id < ?
                    UNION
                    SELECT l.id,
                           l.tokens_input,
                           l.cache_read_tokens,
                           l.tokens_output,
                           l.tokens_reasoning,
                           l.cost_usd
                      FROM llm_calls l
                     WHERE l.session_id IN (SELECT key FROM target_keys)
                 )
            SELECT COUNT(*) AS calls,
                   COALESCE(SUM(tokens_input), 0) AS tokens_input,
                   COALESCE(SUM(cache_read_tokens), 0) AS cache_read_tokens,
                   COALESCE(SUM(tokens_output), 0) AS tokens_output,
                   COALESCE(SUM(tokens_reasoning), 0) AS tokens_reasoning,
                   COALESCE(SUM(cost_usd), 0.0) AS cost_usd
              FROM scoped
            """,
            tuple([
                *session_values,
                runtime_exact,
                runtime_exact,
                runtime_prefix,
                runtime_prefix,
                runtime_upper,
            ]),
        )
        data = dict(row) if row is not None else {}
        return {
            "calls": int(data.get("calls") or 0),
            "tokens_input": int(data.get("tokens_input") or 0),
            "cache_read_tokens": int(data.get("cache_read_tokens") or 0),
            "tokens_output": int(data.get("tokens_output") or 0),
            "tokens_reasoning": int(data.get("tokens_reasoning") or 0),
            "cost_usd": float(data.get("cost_usd") or 0.0),
        }

    def register_artifact(
        self,
        run_id: str = "",
        stage_id: str = "",
        ip_id: str = "",
        rtl_version_id: str = "",
        workflow: str = "",
        kind: str = "",
        path: str = "",
        storage_backend: str = "filesystem",
        sha256: str = "",
        size_bytes: int = None,
        git_commit: str = "",
    ) -> Dict[str, Any]:
        artifact_id = self._new_id()
        now = self._now()
        if not rtl_version_id and stage_id:
            row = self._fetchone(
                "SELECT rtl_version_id FROM workflow_stages WHERE id = ?",
                (stage_id,),
            )
            rtl_version_id = row["rtl_version_id"] if row is not None else ""
        if not rtl_version_id and run_id:
            row = self._fetchone(
                "SELECT rtl_version_id FROM workflow_runs WHERE id = ?",
                (run_id,),
            )
            rtl_version_id = row["rtl_version_id"] if row is not None else ""
        self._execute(
            """
            INSERT INTO artifacts
            (id, run_id, stage_id, ip_id, rtl_version_id, workflow, kind, path, storage_backend,
             sha256, size_bytes, git_commit, created_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                artifact_id,
                run_id,
                stage_id,
                ip_id,
                rtl_version_id,
                workflow,
                kind,
                path,
                storage_backend,
                sha256,
                size_bytes,
                git_commit,
                now,
            ),
        )
        return self.list_artifacts(artifact_id=artifact_id)[0]

    def list_artifacts(
        self,
        run_id: str = None,
        artifact_id: str = None,
    ) -> List[Dict[str, Any]]:
        if artifact_id is not None:
            rows = self._fetchall("SELECT * FROM artifacts WHERE id = ?", (artifact_id,))
        elif run_id is not None:
            rows = self._fetchall(
                "SELECT * FROM artifacts WHERE run_id = ? ORDER BY created_at ASC",
                (run_id,),
            )
        else:
            rows = self._fetchall("SELECT * FROM artifacts ORDER BY created_at ASC")
        return [dict(row) for row in rows]

    def list_rtl_run_history(
        self,
        ip_id: str = None,
        rtl_version_id: str = None,
        workflows: List[str] = None,
    ) -> List[Dict[str, Any]]:
        """List downstream workflow runs tied to registered RTL versions."""
        selected = workflows or ["lint", "sim", "coverage", "syn", "sta", "pnr", "sta-post"]
        placeholders = ", ".join(["?"] * len(selected))
        clauses = [f"r.workflow IN ({placeholders})", "r.rtl_version_id IS NOT NULL", "r.rtl_version_id != ''"]
        values: list[Any] = list(selected)
        if ip_id is not None:
            clauses.append("COALESCE(NULLIF(r.ip_id, ''), rv.ip_id) = ?")
            values.append(ip_id)
        if rtl_version_id is not None:
            clauses.append("r.rtl_version_id = ?")
            values.append(rtl_version_id)
        where = " WHERE " + " AND ".join(clauses)
        rows = self._fetchall(
            f"""
            SELECT r.id AS run_id, r.session_id, r.workspace_id, r.ip_id,
                   r.rtl_version_id, r.workflow, r.mode, r.model_profile,
                   r.reasoning_effort, r.status, r.started_at, r.ended_at,
                   r.duration_ms, r.trigger, r.input_summary, r.error_summary,
                   r.created_at, r.updated_at,
                   rv.version AS rtl_version,
                   rv.label AS rtl_label,
                   rv.sha256_tree AS rtl_sha256_tree,
                   rv.git_commit AS rtl_git_commit,
                   rv.git_tag AS rtl_git_tag,
                   rv.filelist_path AS rtl_filelist_path,
                   rv.top_module AS rtl_top_module,
                   COALESCE(llm.llm_calls, 0) AS llm_calls,
                   COALESCE(llm.tokens_input, 0) AS tokens_input,
                   COALESCE(llm.tokens_output, 0) AS tokens_output,
                   COALESCE(llm.tokens_reasoning, 0) AS tokens_reasoning,
                   COALESCE(llm.cost, 0) AS cost,
                   w.name AS workspace_name,
                   w.local_path AS workspace_path,
                   i.ip_name AS ip_name
              FROM workflow_runs r
              JOIN rtl_versions rv ON rv.id = r.rtl_version_id
              LEFT JOIN (
                  SELECT run_id,
                         COUNT(*) AS llm_calls,
                         SUM(tokens_input) AS tokens_input,
                         SUM(tokens_output) AS tokens_output,
                         SUM(tokens_reasoning) AS tokens_reasoning,
                         SUM(cost_usd) AS cost
                    FROM llm_calls
                   WHERE run_id IS NOT NULL AND run_id != ''
                   GROUP BY run_id
              ) llm ON llm.run_id = r.id
              LEFT JOIN workspaces w ON w.id = COALESCE(NULLIF(r.workspace_id, ''), rv.workspace_id)
              LEFT JOIN ip_blocks i ON i.id = COALESCE(NULLIF(r.ip_id, ''), rv.ip_id)
            {where}
             ORDER BY r.started_at DESC, r.created_at DESC, r.id DESC
            """,
            tuple(values),
        )
        return [dict(row) for row in rows]

    # ---------- Orchestrator room context ----------
    #
    # These two helpers assemble the "current ground truth" panel that the
    # OrchestratorPanel renders above the chat thread. The same JSON is also
    # injected into the agent's next ReAct iteration so humans and the agent
    # are reasoning from the same snapshot.

    def _latest_run_for_ip(self, ip_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT * FROM workflow_runs
             WHERE ip_id = ?
             ORDER BY started_at DESC, created_at DESC
             LIMIT 1
            """,
            (ip_id,),
        )
        return dict(row) if row is not None else None

    def _todo_counts_for_run(self, run_id: str) -> Dict[str, int]:
        rows = self._fetchall(
            "SELECT status, COUNT(*) AS n FROM workflow_todos WHERE run_id = ? GROUP BY status",
            (run_id,),
        )
        return {str(row["status"] or "unknown"): int(row["n"] or 0) for row in rows}

    def _top_blockers_for_run(self, run_id: str, limit: int = 5) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT id, title, criteria, status FROM workflow_todos
             WHERE run_id = ? AND status IN ('blocked', 'pending', 'in_progress')
             ORDER BY
               CASE status WHEN 'blocked' THEN 0 WHEN 'in_progress' THEN 1 ELSE 2 END,
               updated_at DESC
             LIMIT ?
            """,
            (run_id, int(limit)),
        )
        return [
            {
                "id": row["id"],
                "title": row["title"],
                "criteria": row["criteria"],
                "status": row["status"],
            }
            for row in rows
        ]

    def _recent_events_for_ip(self, ip_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Mixed slice of recent trace_events + llm_calls scoped to one IP."""
        trace_rows = self._fetchall(
            """
            SELECT id, event_type, payload, created_at FROM trace_events
             WHERE ip_id = ? AND event_type NOT IN ('chat_message', 'chat_consumed')
             ORDER BY created_at DESC LIMIT ?
            """,
            (ip_id, int(limit)),
        )
        llm_rows = self._fetchall(
            """
            SELECT id, model, cost_usd, tokens_input, tokens_output, status, created_at
              FROM llm_calls
             WHERE ip_id = ?
             ORDER BY created_at DESC LIMIT ?
            """,
            (ip_id, int(limit)),
        )
        events: List[Dict[str, Any]] = []
        for row in trace_rows:
            events.append({
                "kind": "trace",
                "id": row["id"],
                "event_type": row["event_type"],
                "ts": row["created_at"],
                "payload": self._load_json(row["payload"]),
            })
        for row in llm_rows:
            events.append({
                "kind": "llm",
                "id": row["id"],
                "ts": row["created_at"],
                "model": row["model"],
                "cost_usd": row["cost_usd"] or 0,
                "tokens_input": row["tokens_input"] or 0,
                "tokens_output": row["tokens_output"] or 0,
                "status": row["status"],
            })
        events.sort(key=lambda e: e.get("ts") or 0, reverse=True)
        return events[:limit]

    def summarize_ip_room_context(self, ip_id: str) -> Optional[Dict[str, Any]]:
        """Assemble the per-IP orchestrator context bundle."""
        ip = self.get_ip_block(ip_id)
        if ip is None:
            return None

        latest_run = self._latest_run_for_ip(ip_id)
        run_block: Optional[Dict[str, Any]] = None
        stages: List[Dict[str, Any]] = []
        todos_counts: Dict[str, int] = {}
        top_blockers: List[Dict[str, Any]] = []
        if latest_run is not None:
            run_id = latest_run["id"]
            stage_rows = self._fetchall(
                """
                SELECT stage_name, status, attempt, started_at, ended_at
                  FROM workflow_stages
                 WHERE run_id = ?
                 ORDER BY started_at ASC, created_at ASC
                """,
                (run_id,),
            )
            stages = [
                {
                    "name": r["stage_name"],
                    "status": r["status"],
                    "attempt": r["attempt"],
                    "started_at": r["started_at"],
                    "ended_at": r["ended_at"],
                }
                for r in stage_rows
            ]
            current_stage = next(
                (s["name"] for s in reversed(stages) if s["status"] == "running"),
                stages[-1]["name"] if stages else None,
            )
            run_block = {
                "id": run_id,
                "workflow": latest_run.get("workflow"),
                "status": latest_run.get("status"),
                "mode": latest_run.get("mode"),
                "model_profile": latest_run.get("model_profile"),
                "started_at": latest_run.get("started_at"),
                "ended_at": latest_run.get("ended_at"),
                "current_stage": current_stage,
            }
            todos_counts = self._todo_counts_for_run(run_id)
            top_blockers = self._top_blockers_for_run(run_id)

        return {
            "ip": {
                "id": ip["id"],
                "name": ip["ip_name"],
                "type": ip.get("ip_type"),
                "ssot_path": ip.get("ssot_path"),
                "workspace_id": ip.get("workspace_id"),
            },
            "workflow": {
                "latest_run": run_block,
                "stages": stages,
            },
            "todos": {
                "counts": todos_counts,
                "top_blockers": top_blockers,
            },
            "recent_events": self._recent_events_for_ip(ip_id),
        }

    def summarize_global_room_context(
        self,
        user_id: str = "",
    ) -> Dict[str, Any]:
        """Cross-IP snapshot. If user_id is given, restrict to IPs the user
        can view; otherwise list every IP (server-side admin use)."""
        if user_id:
            ip_rows = self.list_accessible_ip_blocks(user_id, "view")
        else:
            ip_rows = self._fetchall("SELECT * FROM ip_blocks ORDER BY ip_name")
            ip_rows = [dict(r) for r in ip_rows]

        ip_summaries: List[Dict[str, Any]] = []
        for ip in ip_rows:
            ip_id = ip["id"]
            latest_run = self._latest_run_for_ip(ip_id)
            counts = self._todo_counts_for_run(latest_run["id"]) if latest_run else {}
            ip_summaries.append({
                "id": ip_id,
                "name": ip["ip_name"],
                "type": ip.get("ip_type"),
                "latest_workflow": latest_run.get("workflow") if latest_run else None,
                "run_status": latest_run.get("status") if latest_run else None,
                "open_blockers": counts.get("blocked", 0)
                                  + counts.get("pending", 0)
                                  + counts.get("in_progress", 0),
                "completed": counts.get("completed", 0) + counts.get("approved", 0),
            })

        ip_id_filter = {ip["id"] for ip in ip_rows}
        if ip_id_filter:
            placeholders = ",".join("?" for _ in ip_id_filter)
            recent_rows = self._fetchall(
                f"""
                SELECT id, event_type, ip_id, payload, created_at
                  FROM trace_events
                 WHERE ip_id IN ({placeholders})
                   AND event_type NOT IN ('chat_message', 'chat_consumed')
                 ORDER BY created_at DESC LIMIT 20
                """,
                tuple(ip_id_filter),
            )
            recent = [
                {
                    "id": r["id"],
                    "event_type": r["event_type"],
                    "ip_id": r["ip_id"],
                    "ts": r["created_at"],
                    "payload": self._load_json(r["payload"]),
                }
                for r in recent_rows
            ]
        else:
            recent = []

        return {
            "ips": ip_summaries,
            "recent_cross_ip_events": recent,
        }

    # ---------- Orchestrator runs / steps ----------

    def create_orchestrator_run(
        self,
        user_id: str,
        ip_id: str,
        session_id: str = "",
        workspace_id: str = "",
        chat_message_id: str = "",
        pipeline_run_id: str = "",
        model: str = "",
        reasoning_effort: str = "",
        status: str = "running",
    ) -> Dict[str, Any]:
        run_id = self._new_id()
        now = self._now()
        self._execute(
            """
            INSERT INTO orchestrator_runs
            (id, session_id, workspace_id, ip_id, user_id, chat_message_id,
             pipeline_run_id, model, reasoning_effort, status, final_state,
             started_at, ended_at, updated_at)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                run_id,
                session_id,
                workspace_id,
                ip_id,
                user_id,
                chat_message_id,
                pipeline_run_id,
                model,
                reasoning_effort,
                status,
                None,
                now,
                None,
                now,
            ),
        )
        return self.get_orchestrator_run(run_id)

    def get_orchestrator_run(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            "SELECT * FROM orchestrator_runs WHERE id = ?", (run_id,)
        )
        return self._row_to_dict(row, "orchestrator_runs") if row else None

    def update_orchestrator_run(
        self,
        run_id: str,
        status: Optional[str] = None,
        final_state: Optional[str] = None,
        ended: bool = False,
    ) -> Optional[Dict[str, Any]]:
        sets: List[str] = []
        values: List[Any] = []
        if status is not None:
            sets.append("status = ?")
            values.append(status)
        if final_state is not None:
            sets.append("final_state = ?")
            values.append(final_state)
        now = self._now()
        sets.append("updated_at = ?")
        values.append(now)
        if ended:
            sets.append("ended_at = ?")
            values.append(now)
        if not sets:
            return self.get_orchestrator_run(run_id)
        values.append(run_id)
        self._execute(
            f"UPDATE orchestrator_runs SET {', '.join(sets)} WHERE id = ?",
            tuple(values),
        )
        return self.get_orchestrator_run(run_id)

    def find_active_run_for(
        self, user_id: str, ip_id: str
    ) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT * FROM orchestrator_runs
             WHERE user_id = ? AND ip_id = ?
               AND status IN ('running', 'paused')
             ORDER BY started_at DESC
             LIMIT 1
            """,
            (user_id, ip_id),
        )
        return self._row_to_dict(row, "orchestrator_runs") if row else None

    def append_orchestrator_step(
        self,
        run_id: str,
        tool_name: str = "",
        observed_state: Any = None,
        decision: Any = None,
        dispatched_workflow: str = "",
        dispatched_job_id: str = "",
        evidence_read: Any = None,
        verdict: str = "",
        retry_budget_state: Any = None,
        user_reply: str = "",
    ) -> Dict[str, Any]:
        step_id = self._new_id()
        now = self._now()
        with self._lock:
            conn = self._connect()
            cur = conn.execute(
                "SELECT COALESCE(MAX(step_index), -1) + 1 AS next_idx "
                "FROM orchestrator_steps WHERE run_id = ?",
                (run_id,),
            )
            next_idx = cur.fetchone()["next_idx"]
            conn.execute(
                """
                INSERT INTO orchestrator_steps
                (id, run_id, step_index, tool_name, observed_state_json,
                 decision_json, dispatched_workflow, dispatched_job_id,
                 evidence_read_json, verdict, retry_budget_state_json,
                 user_reply, created_at)
                VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
                """,
                (
                    step_id,
                    run_id,
                    next_idx,
                    tool_name,
                    self._dump_json(observed_state),
                    self._dump_json(decision),
                    dispatched_workflow,
                    dispatched_job_id,
                    self._dump_json(evidence_read),
                    verdict,
                    self._dump_json(retry_budget_state),
                    user_reply,
                    now,
                ),
            )
            conn.commit()
        return self.get_orchestrator_step(step_id)

    def get_orchestrator_step(self, step_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            "SELECT * FROM orchestrator_steps WHERE id = ?", (step_id,)
        )
        return self._row_to_dict(row, "orchestrator_steps") if row else None

    def list_orchestrator_steps(
        self, run_id: str, limit: int = 200
    ) -> List[Dict[str, Any]]:
        rows = self._fetchall(
            """
            SELECT * FROM orchestrator_steps
             WHERE run_id = ?
             ORDER BY step_index ASC
             LIMIT ?
            """,
            (run_id, limit),
        )
        return [self._row_to_dict(r, "orchestrator_steps") for r in rows]

    def latest_orchestrator_step(self, run_id: str) -> Optional[Dict[str, Any]]:
        row = self._fetchone(
            """
            SELECT * FROM orchestrator_steps
             WHERE run_id = ?
             ORDER BY step_index DESC
             LIMIT 1
            """,
            (run_id,),
        )
        return self._row_to_dict(row, "orchestrator_steps") if row else None

    # ---------- Admin ----------

    def list_all_users(self) -> List[Dict[str, Any]]:
        """List all users (excludes password_hash)."""
        rows = self._fetchall(
            """
            SELECT id, username, display_name, email, role, created_at, last_login_at
            FROM users ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in rows]

    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with owner username."""
        rows = self._fetchall(
            """
            SELECT
                s.id, s.session_uid, s.user_id, s.namespace, s.owner,
                s.project_id, s.workspace_id, s.ip_id, s.ip, s.workflow,
                s.session_kind, s.directory, s.title, s.status,
                s.created_at, s.updated_at, s.archived_at, s.summary,
                u.username as owner_username, u.display_name as owner_display_name,
                r.id as latest_workflow_run_id,
                r.workflow as latest_workflow,
                r.status as latest_workflow_status,
                r.started_at as latest_workflow_started_at,
                r.ended_at as latest_workflow_ended_at
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.id
            LEFT JOIN workflow_runs r ON r.id = (
                SELECT rr.id
                  FROM workflow_runs rr
                 WHERE rr.session_id = s.id
                 ORDER BY rr.started_at DESC, rr.created_at DESC
                 LIMIT 1
            )
            ORDER BY s.updated_at DESC
            """
        )
        sessions: List[Dict[str, Any]] = []
        for row in rows:
            item = self._row_to_dict(row, "sessions")
            summary = item.get("summary") if isinstance(item.get("summary"), dict) else {}
            item["ip"] = item.get("ip_id") or item.get("ip") or summary.get("ip") or item.get("project_id") or ""
            item["workflow"] = item.get("workflow") or item.get("latest_workflow") or summary.get("workflow") or ""
            item["pipeline_run_id"] = summary.get("pipeline_run_id") or item.get("latest_workflow_run_id") or ""
            sessions.append(item)
        return sessions

    def count_sessions_by_user(self) -> Dict[str, int]:
        """Return {user_id: session_count} for all users."""
        rows = self._fetchall(
            "SELECT user_id, COUNT(*) as cnt FROM sessions GROUP BY user_id"
        )
        return {str(row["user_id"]): int(row["cnt"]) for row in rows}
