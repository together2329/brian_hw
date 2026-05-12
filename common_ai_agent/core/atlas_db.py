"""
Atlas SQLite Persistence Layer

Multi-user SQLite database for Atlas UI session management.
Replaces JSON file storage with concurrent-safe SQLite.

Zero external dependencies — uses only Python stdlib sqlite3.
"""

import json
import sqlite3
import threading
import time
import uuid
from pathlib import Path
from typing import Any, Dict, List, Optional


# ============================================================
# Schema
# ============================================================

SCHEMA_SQL = """
-- users
CREATE TABLE IF NOT EXISTS users (
    id TEXT PRIMARY KEY,
    username TEXT UNIQUE,
    display_name TEXT,
    password_hash TEXT,
    role TEXT DEFAULT 'user',
    created_at REAL,
    last_login_at REAL
);

-- sessions
CREATE TABLE IF NOT EXISTS sessions (
    id TEXT PRIMARY KEY,
    user_id TEXT NOT NULL,
    project_id TEXT,
    directory TEXT,
    title TEXT,
    status TEXT DEFAULT 'active',
    created_at REAL,
    updated_at REAL,
    archived_at REAL,
    summary TEXT
);
CREATE INDEX IF NOT EXISTS idx_sessions_user ON sessions(user_id, status);

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
"""

# Columns that should be serialized as JSON on write / deserialized on read
_JSON_COLUMNS = {
    "users": set(),
    "sessions": {"summary"},
    "messages": {"error"},
    "parts": {"tool_input", "patch_files"},
    "ws_connections": set(),
    "session_queue": {"payload"},
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

    def __init__(self, db_path: str = None):
        if db_path is None:
            db_path = str(Path.home() / ".common_ai_agent" / "atlas.db")
        self.db_path = db_path
        self._lock = threading.RLock()
        self._conn: Optional[sqlite3.Connection] = None
        # Ensure parent dir + schema exist on first instantiation.
        # SCHEMA_SQL is idempotent (CREATE TABLE IF NOT EXISTS).
        Path(self.db_path).parent.mkdir(parents=True, exist_ok=True)
        self.init_db()

    def _connect(self) -> sqlite3.Connection:
        """Open (or re-open) the SQLite connection."""
        if self._conn is None:
            self._conn = sqlite3.connect(
                self.db_path,
                check_same_thread=False,
            )
            self._conn.row_factory = sqlite3.Row
        return self._conn

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
        """Create tables and indexes if they don't exist."""
        with self._lock:
            conn = self._connect()
            conn.executescript(SCHEMA_SQL)
            conn.commit()

    def close(self):
        """Close the underlying connection."""
        with self._lock:
            if self._conn is not None:
                self._conn.close()
                self._conn = None

    def __enter__(self):
        self.init_db()
        return self

    def __exit__(self, exc_type, exc_val, exc_tb):
        self.close()
        return False

    # ---------- Users ----------

    def create_user(
        self,
        username: str,
        display_name: str,
        password_hash: str = None,
        role: str = "user",
    ) -> Dict[str, Any]:
        """Create a new user. Returns the user dict."""
        user_id = self._new_id()
        now = self._now()
        role = role or "user"
        self._execute(
            """
            INSERT INTO users (id, username, display_name, password_hash, role, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, display_name, password_hash, role, now, None),
        )
        return {
            "id": user_id,
            "username": username,
            "display_name": display_name,
            "password_hash": password_hash,
            "role": role,
            "created_at": now,
            "last_login_at": None,
        }

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

    def set_user_role(self, user_id: str, role: str) -> Optional[Dict[str, Any]]:
        """Update a user's role and return the refreshed user."""
        self._execute("UPDATE users SET role = ? WHERE id = ?", (role, user_id))
        return self.get_user(user_id)

    # ---------- Sessions ----------

    def create_session(
        self,
        user_id: str,
        title: str,
        project_id: str = "",
    ) -> Dict[str, Any]:
        """Create a new session. Returns the session dict."""
        session_id = self._new_id()
        now = self._now()
        directory = str(Path.cwd())
        self._execute(
            """
            INSERT INTO sessions (id, user_id, project_id, directory, title, status, created_at, updated_at, archived_at, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (session_id, user_id, project_id, directory, title, "active", now, now, None, None),
        )
        return {
            "id": session_id,
            "user_id": user_id,
            "project_id": project_id,
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
    ) -> Dict[str, Any]:
        now = created_at or self._now()
        self._execute(
            """
            INSERT OR IGNORE INTO users (id, username, display_name, password_hash, role, created_at, last_login_at)
            VALUES (?, ?, ?, ?, ?, ?, ?)
            """,
            (user_id, username, display_name, password_hash, role, now, last_login_at),
        )
        return self.get_user(user_id) or {
            "id": user_id,
            "username": username,
            "display_name": display_name,
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
    ) -> Dict[str, Any]:
        now = self._now()
        summary_json = self._dump_json(summary)
        self._execute(
            """
            INSERT OR IGNORE INTO sessions
            (id, user_id, project_id, directory, title, status, created_at, updated_at, archived_at, summary)
            VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                session_id,
                user_id,
                project_id,
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

    # ---------- Admin ----------

    def list_all_users(self) -> List[Dict[str, Any]]:
        """List all users (excludes password_hash)."""
        rows = self._fetchall(
            """
            SELECT id, username, display_name, role, created_at, last_login_at
            FROM users ORDER BY created_at DESC
            """
        )
        return [dict(row) for row in rows]

    def list_all_sessions(self) -> List[Dict[str, Any]]:
        """List all sessions with owner username."""
        rows = self._fetchall(
            """
            SELECT
                s.id, s.user_id, s.project_id, s.directory, s.title,
                s.status, s.created_at, s.updated_at, s.archived_at, s.summary,
                u.username as owner_username, u.display_name as owner_display_name
            FROM sessions s
            LEFT JOIN users u ON s.user_id = u.id
            ORDER BY s.updated_at DESC
            """
        )
        return [self._row_to_dict(row, "sessions") for row in rows]

    def count_sessions_by_user(self) -> Dict[str, int]:
        """Return {user_id: session_count} for all users."""
        rows = self._fetchall(
            "SELECT user_id, COUNT(*) as cnt FROM sessions GROUP BY user_id"
        )
        return {str(row["user_id"]): int(row["cnt"]) for row in rows}
