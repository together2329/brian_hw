"""Storage facade for ATLAS runtime state.

This module is intentionally thin: the current Atlas UI already depends on
``AtlasDB`` behavior, so the first storage layer must delegate to it instead of
redefining session semantics. Future backends can implement the same surface.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import Any, Optional, Protocol

from core.atlas_admin_usage import build_admin_usage_payload
from core.atlas_db import AtlasDB


class AtlasStorage(Protocol):
    """Runtime-state operations used by Atlas UI and workflow integrations."""

    def create_user(
        self,
        username: str,
        display_name: str,
        password_hash: Optional[str] = None,
        role: str = "user",
    ) -> dict[str, Any]:
        ...

    def create_session(
        self,
        user_id: str,
        title: str,
        project_id: str = "",
    ) -> dict[str, Any]:
        ...

    def append_message(self, session_id: str, role: str, **fields: Any) -> dict[str, Any]:
        ...

    def append_part(
        self,
        message_id: str,
        session_id: str,
        part_type: str,
        **fields: Any,
    ) -> dict[str, Any]:
        ...

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        ...

    def get_admin_usage(self) -> dict[str, Any]:
        ...


class SQLiteStorage:
    """AtlasStorage implementation backed by the existing SQLite AtlasDB."""

    def __init__(self, db_path: str | Path | None = None, db: AtlasDB | None = None):
        self._db = db if db is not None else AtlasDB(str(db_path) if db_path is not None else None)
        self._owns_db = db is None

    def close(self) -> None:
        if self._owns_db:
            self._db.close()

    def __enter__(self) -> "SQLiteStorage":
        self._db.init_db()
        return self

    def __exit__(self, exc_type: Any, exc_val: Any, exc_tb: Any) -> bool:
        self.close()
        return False

    def create_user(
        self,
        username: str,
        display_name: str,
        password_hash: Optional[str] = None,
        role: str = "user",
    ) -> dict[str, Any]:
        return self._db.create_user(username, display_name, password_hash=password_hash, role=role)

    def create_session(
        self,
        user_id: str,
        title: str,
        project_id: str = "",
    ) -> dict[str, Any]:
        return self._db.create_session(user_id, title, project_id=project_id)

    def update_session(self, session_id: str, **fields: Any) -> None:
        self._db.update_session(session_id, **fields)

    def get_session(self, session_id: str) -> dict[str, Any] | None:
        return self._db.get_session(session_id)

    def list_sessions(self, user_id: str, status: str = "active") -> list[dict[str, Any]]:
        return self._db.list_sessions(user_id, status=status)

    def append_message(self, session_id: str, role: str, **fields: Any) -> dict[str, Any]:
        return self._db.save_message(session_id, role, **fields)

    def append_part(
        self,
        message_id: str,
        session_id: str,
        part_type: str,
        **fields: Any,
    ) -> dict[str, Any]:
        return self._db.save_part(message_id, session_id, part_type, **fields)

    def get_session_state(self, session_id: str) -> dict[str, Any]:
        session = self._db.get_session(session_id)
        messages = []
        for message in self._db.get_messages(session_id):
            messages.append({
                **message,
                "parts": self._db.get_parts(message["id"]),
            })
        return {"session": session, "messages": messages}

    def enqueue_message(
        self,
        session_id: str,
        direction: str,
        msg_type: str,
        payload: Any = None,
        expires_at: Optional[float] = None,
    ) -> str:
        return self._db.enqueue_message(session_id, direction, msg_type, payload, expires_at)

    def dequeue_message(
        self,
        session_id: str,
        direction: str,
        timeout: Optional[float] = None,
    ) -> dict[str, Any] | None:
        return self._db.dequeue_message(session_id, direction, timeout=timeout)

    def poll_messages(
        self,
        session_id: str,
        direction: str,
        since_id: Optional[str] = None,
        limit: int = 100,
    ) -> list[dict[str, Any]]:
        return self._db.poll_messages(session_id, direction, since_id=since_id, limit=limit)

    def acknowledge_message(self, msg_id: str) -> None:
        self._db.acknowledge_message(msg_id)

    def get_admin_usage(self) -> dict[str, Any]:
        return build_admin_usage_payload(self._db)


LegacyAtlasStorage = SQLiteStorage


def create_atlas_storage(
    db_path: str | Path | None = None,
    *,
    backend: str | None = None,
    db: AtlasDB | None = None,
) -> AtlasStorage:
    """Create the configured Atlas storage backend.

    The default deliberately preserves the existing AtlasDB-backed behavior.
    New backends must be selected explicitly and should be introduced behind
    this factory before any UI route is switched over.
    """

    selected = (backend or os.environ.get("ATLAS_STORAGE_BACKEND") or "legacy").strip().lower()
    if selected in {"legacy", "atlasdb", "sqlite"}:
        return SQLiteStorage(db_path=db_path, db=db)
    if selected == "supabase":
        raise NotImplementedError("ATLAS_STORAGE_BACKEND=supabase is not implemented yet")
    raise ValueError(f"Unsupported ATLAS_STORAGE_BACKEND: {selected}")
