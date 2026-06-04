from __future__ import annotations

import re
from pathlib import Path
from typing import Any

from .atlas_db import AtlasDB

_UUID_RE = re.compile(r"^[a-f0-9]{32}$")


def _canonical_user_id(db: AtlasDB, identifier: str) -> str:
    ident = str(identifier or "").strip()
    if not ident:
        return ident
    if _UUID_RE.match(ident):
        return ident
    try:
        row = db.get_user_by_username(ident) or db.get_user_by_email(ident)
    except (AttributeError, RuntimeError):
        return ident
    return str(row["id"]) if row and row.get("id") else ident


def read_orchestrator_chat_db_fallback(
    db_path: str | Path,
    *,
    user_id: str,
    ip_name: str,
    workspace_session: str,
    limit: int,
    since: float | None,
) -> list[dict[str, Any]]:
    db_file = Path(db_path)
    if not user_id or not ip_name or not db_file.is_file():
        return []
    workspace_name = str(workspace_session or "default").strip() or "default"
    bound = max(1, min(500, int(limit or 100)))
    rows: list[dict[str, Any]] = []
    with AtlasDB(str(db_file)) as db:
        db_user_id = _canonical_user_id(db, user_id)
        for workspace in db.list_workspaces(owner_user_id=db_user_id):
            if str(workspace.get("name") or "") != workspace_name:
                continue
            workspace_id = str(workspace.get("id") or "")
            if not workspace_id:
                continue
            ip_row = db.get_ip_block_by_name(ip_name, workspace_id=workspace_id)
            if not ip_row or not ip_row.get("id"):
                continue
            rows.extend(db.list_chat_messages(str(ip_row["id"]), limit=bound, since=since))
    rows.sort(
        key=lambda row: (float(row.get("created_at") or 0), str(row.get("id") or "")),
        reverse=True,
    )
    return rows[:bound]
