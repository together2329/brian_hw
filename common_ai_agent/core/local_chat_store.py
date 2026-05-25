"""core/local_chat_store.py — local-file chat persistence under .session.

Per the "local .session, minimize SQLite" decision: chat for one (owner, ip)
lives in an append-only JSONL file under .session rather than the SQLite DB.
This is safe because there is no concurrent multi-user work on the same IP, so
atomic line appends are sufficient (no cross-process write lock needed).

Each row mirrors the AtlasDB ``chat_message`` trace-event shape so existing
readers and the UI work unchanged:

    {
      "id": <hex>, "event_type": "chat_message",
      "ip_id": <ip name>, "actor_user_id": <owner>, "workspace_id": <ws>,
      "created_at": <unix float>,
      "payload": {"content": ..., "display_name": ..., "role": ...},
    }

Keyed by (owner, ip *name*) — the human-stable identifiers — not DB row ids.
"""
from __future__ import annotations

import json
import time
import uuid
from pathlib import Path
from typing import Any, Optional


def _safe(part: str, fallback: str) -> str:
    s = "".join(c if (c.isalnum() or c in "._-") else "_" for c in str(part or "").strip())
    return s or fallback


def chat_path(project_root: Any, owner: str, ip: str) -> Path:
    """Reuse the existing per-scope conversation log:
    ``.session/<owner>/<ip>/full_conversation.json`` (the append-only history
    file already used elsewhere) — chat *is* the conversation, no new store."""
    return (
        Path(project_root)
        / ".session"
        / _safe(owner, "default")
        / _safe(ip, "soc")
        / "full_conversation.json"
    )


def _load_rows(path: Path) -> list[dict]:
    if not path.exists():
        return []
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        return data if isinstance(data, list) else []
    except Exception:
        return []


def append_chat(
    project_root: Any,
    owner: str,
    ip: str,
    content: str,
    *,
    role: str = "user",
    display_name: str = "",
    workspace_id: str = "",
) -> dict:
    """Append one chat row to the local conversation log and return it.
    Row shape mirrors AtlasDB ``chat_message`` so existing readers/UI are
    unchanged."""
    path = chat_path(project_root, owner, ip)
    path.parent.mkdir(parents=True, exist_ok=True)
    row = {
        "id": uuid.uuid4().hex,
        "event_type": "chat_message",
        "ip_id": ip or "",
        "actor_user_id": owner or "",
        "workspace_id": workspace_id or "",
        "created_at": time.time(),
        "payload": {
            "content": content,
            "display_name": display_name or "",
            "role": role or "user",
        },
    }
    rows = _load_rows(path)
    rows.append(row)
    tmp = path.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(rows, ensure_ascii=False), encoding="utf-8")
    tmp.replace(path)  # atomic; single writer per IP
    return row


def read_chat(
    project_root: Any,
    owner: str,
    ip: str,
    *,
    limit: int = 100,
    since: Optional[float] = None,
) -> list[dict]:
    """Return chat rows for (owner, ip), newest-first, matching
    ``AtlasDB.list_chat_messages``'s contract (limit + since filter)."""
    rows = _load_rows(chat_path(project_root, owner, ip))
    if since is not None:
        rows = [r for r in rows if float(r.get("created_at") or 0) > float(since)]
    rows.sort(key=lambda r: float(r.get("created_at") or 0), reverse=True)
    return rows[: max(1, int(limit))]


def has_local_chat(project_root: Any, owner: str, ip: str) -> bool:
    """True if a local chat file with at least one row exists for (owner, ip)."""
    path = chat_path(project_root, owner, ip)
    try:
        return path.exists() and path.stat().st_size > 0
    except OSError:
        return False


# ── mid-run injection: file-based consumed watermark ────────────────────────
# Replaces the DB chat_consumed ledger. A session consumes user messages up to
# a timestamp; the watermark file records per-session cursors so the same
# feedback is not re-injected on every iteration. No DB, no cross-process lock
# needed (single writer per IP).

def _watermark_path(project_root: Any, owner: str, ip: str) -> Path:
    return chat_path(project_root, owner, ip).parent / "chat_consumed.json"


def _read_watermark(project_root: Any, owner: str, ip: str) -> dict:
    p = _watermark_path(project_root, owner, ip)
    if not p.exists():
        return {}
    try:
        data = json.loads(p.read_text(encoding="utf-8"))
        return data if isinstance(data, dict) else {}
    except Exception:
        return {}


def read_unconsumed(
    project_root: Any,
    owner: str,
    ip: str,
    session_id: str,
    *,
    roles: tuple = ("user",),
) -> list[dict]:
    """User-authored chat rows newer than this session's consumed watermark,
    oldest-first (injection order). Only ``roles`` (default human ``user``) are
    returned so the agent never re-ingests its own assistant/tool output."""
    wm = float(_read_watermark(project_root, owner, ip).get(session_id or "", 0) or 0)
    rows = read_chat(project_root, owner, ip, limit=10_000, since=wm)
    rows = [r for r in rows if str((r.get("payload") or {}).get("role") or "user") in roles]
    rows.sort(key=lambda r: float(r.get("created_at") or 0))
    return rows


def owner_for_ip(project_root: Any, ip: str) -> Optional[str]:
    """Find the owner dir holding chat for ``ip`` by globbing
    ``.session/*/<ip>/full_conversation.json``. Relies on the invariant that one
    IP has a single owner (no concurrent multi-user work on the same IP), so the
    injector can locate the chat file without resolving the owner UUID itself.
    Returns the owner dir name, or None if no chat file exists yet."""
    safe_ip = _safe(ip, "soc")
    base = Path(project_root) / ".session"
    if not base.is_dir():
        return None
    for cand in sorted(base.glob(f"*/{safe_ip}/full_conversation.json")):
        if cand.is_file() and cand.stat().st_size > 0:
            return cand.parent.parent.name
    return None


def mark_consumed(project_root: Any, owner: str, ip: str, session_id: str, last_ts: float) -> None:
    """Advance this session's consumed cursor to ``last_ts`` (monotonic)."""
    if not session_id:
        return
    p = _watermark_path(project_root, owner, ip)
    p.parent.mkdir(parents=True, exist_ok=True)
    wm = _read_watermark(project_root, owner, ip)
    prev = float(wm.get(session_id, 0) or 0)
    wm[session_id] = max(prev, float(last_ts or 0))
    tmp = p.with_suffix(".json.tmp")
    tmp.write_text(json.dumps(wm, ensure_ascii=False), encoding="utf-8")
    tmp.replace(p)  # atomic
