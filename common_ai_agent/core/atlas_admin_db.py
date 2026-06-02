"""
Read-only raw-DB inspector for the admin panel.

Exposes a safe, allowlisted view of the SQLite tables behind ATLAS:
  - list_tables(db)         → catalog + per-table column schema + row count
  - read_table(db, name, …) → paginated row dump (LIMIT/OFFSET, ORDER BY rowid)

Why an allowlist instead of just sanitizing the identifier: SQLite has no
parameter binding for identifiers, so anything passed as a table name is
interpolated raw. Resolving the requested name against sqlite_master and
rejecting anything that isn't there keeps the query SQL-injection-proof
even if a future caller forgets to sanitize.
"""
from __future__ import annotations

import json
from pathlib import Path
from typing import Any, Dict, List, Optional, Tuple

# Hard cap so a careless caller can't pull a million rows in one shot.
_MAX_LIMIT = 500
_DEFAULT_LIMIT = 50

# Characters that must NEVER appear in a session_uid passed to the runtime
# raw-DB inspector. A legitimate session_uid is uuid4 hex (0-9a-f). Rejecting
# path separators / traversal / drive-colon up front is defense-in-depth so a
# crafted value can never reach the filesystem even if a later guard regresses
# (plan §2.11 / R14/R21).
_PATH_LIKE_CHARS = ("/", "\\", "..", ":")

# Known JSON-encoded columns per table (mirrors core/atlas_db.py:_JSON_COLUMNS).
# Used to pretty-print stored JSON so admins see structured payloads instead
# of escaped strings.
_JSON_COLUMNS: Dict[str, set] = {
    "sessions": {"summary"},
    "messages": {"error"},
    "parts": {"tool_input", "patch_files"},
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


def _known_tables(db) -> List[str]:
    rows = db._fetchall(
        "SELECT name FROM sqlite_master "
        "WHERE type='table' AND name NOT LIKE 'sqlite_%' "
        "ORDER BY name"
    )
    return [r["name"] for r in rows]


def _columns_for(db, table: str) -> List[Dict[str, Any]]:
    # PRAGMA can't take parameters; safe because `table` came from sqlite_master.
    rows = db._fetchall(f'PRAGMA table_info("{table}")')
    cols: List[Dict[str, Any]] = []
    for r in rows:
        cols.append({
            "name": r["name"],
            "type": r["type"] or "",
            "notnull": bool(r["notnull"]),
            "pk": bool(r["pk"]),
            "default": r["dflt_value"],
        })
    return cols


def _row_count(db, table: str) -> int:
    rows = db._fetchall(f'SELECT COUNT(*) AS n FROM "{table}"')
    if not rows:
        return 0
    return int(rows[0]["n"])


def list_tables(db) -> Dict[str, Any]:
    """Return {tables: [{name, row_count, columns}, ...]} for the admin sidebar."""
    out: List[Dict[str, Any]] = []
    for name in _known_tables(db):
        try:
            count = _row_count(db, name)
        except Exception:
            count = -1
        try:
            cols = _columns_for(db, name)
        except Exception:
            cols = []
        out.append({"name": name, "row_count": count, "columns": cols})
    return {"tables": out}


def _coerce_value(table: str, col: str, value: Any) -> Any:
    if value is None:
        return None
    if isinstance(value, (int, float, bool)):
        return value
    if isinstance(value, bytes):
        try:
            return value.decode("utf-8", errors="replace")
        except Exception:
            return f"<{len(value)} bytes>"
    text = str(value)
    if col in _JSON_COLUMNS.get(table, set()) and text:
        try:
            return json.loads(text)
        except Exception:
            return text
    return text


def read_table(
    db,
    table: str,
    *,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
    order: str = "desc",
) -> Tuple[Optional[Dict[str, Any]], Optional[str]]:
    """
    Return (payload, error). error is non-None when the table is not allowlisted
    or some other recoverable issue happened; caller should surface it as 4xx.
    """
    known = set(_known_tables(db))
    if table not in known:
        return None, f"unknown table: {table!r}"

    try:
        limit_n = max(1, min(int(limit), _MAX_LIMIT))
    except Exception:
        limit_n = _DEFAULT_LIMIT
    try:
        offset_n = max(0, int(offset))
    except Exception:
        offset_n = 0

    direction = "DESC" if str(order).lower() != "asc" else "ASC"
    columns = _columns_for(db, table)
    total = _row_count(db, table)

    # Prefer an ordering key the user can reason about; fall back to rowid.
    if any(c["name"] == "created_at" for c in columns):
        order_clause = f"ORDER BY created_at {direction}"
    else:
        order_clause = f"ORDER BY rowid {direction}"

    sql = f'SELECT * FROM "{table}" {order_clause} LIMIT ? OFFSET ?'
    raw_rows = db._fetchall(sql, (limit_n, offset_n))
    rows: List[Dict[str, Any]] = []
    for raw in raw_rows:
        rec: Dict[str, Any] = {}
        for c in columns:
            rec[c["name"]] = _coerce_value(table, c["name"], raw[c["name"]])
        rows.append(rec)

    return {
        "table": table,
        "columns": columns,
        "rows": rows,
        "limit": limit_n,
        "offset": offset_n,
        "total": total,
        "order": direction.lower(),
    }, None


def preview_all(db, *, per_table: int = 3) -> Dict[str, Any]:
    """
    Return {tables: [{name, columns, rows, total}, ...]} with `per_table`
    most-recent rows per table — single round-trip for the overview pane.
    """
    try:
        per = max(1, min(int(per_table), 20))
    except Exception:
        per = 3

    out: List[Dict[str, Any]] = []
    for name in _known_tables(db):
        try:
            cols = _columns_for(db, name)
            total = _row_count(db, name)
            if any(c["name"] == "created_at" for c in cols):
                order_clause = "ORDER BY created_at DESC"
            else:
                order_clause = "ORDER BY rowid DESC"
            raw_rows = db._fetchall(
                f'SELECT * FROM "{name}" {order_clause} LIMIT ?',
                (per,),
            )
            rows = []
            for raw in raw_rows:
                rows.append({c["name"]: _coerce_value(name, c["name"], raw[c["name"]]) for c in cols})
            out.append({"name": name, "columns": cols, "rows": rows, "total": total})
        except Exception as exc:
            out.append({"name": name, "columns": [], "rows": [], "total": -1, "error": str(exc)})
    return {"tables": out, "per_table": per}


# --------------------------------------------------------------------------- #
# Hardened per-session RUNTIME-DB inspector (plan §2.11 / R14/R21/R24)
# --------------------------------------------------------------------------- #
#
# The control-DB browser above (list_tables/preview_all/read_table) takes NO
# path and only ever sees the single control file, so it has no traversal or
# cross-user surface. Inspecting a *per-session runtime* file is different: the
# request now selects WHICH file, which is a path-resolution + cross-user
# surface. This ONE helper is shared by both admin endpoint copies
# (src/atlas_admin.py and src/atlas_ui.py) so the security policy can never drift
# between them (R24). It NEVER accepts or echoes a filesystem path.


class RuntimeInspectError(Exception):
    """Raised when a runtime-DB inspect request cannot be safely authorized.

    Carries an HTTP-ish ``status`` (403/404) and a SAFE ``message`` that NEVER
    contains a filesystem path. The endpoint maps this straight to a JSON error.
    """

    def __init__(self, status: int, message: str) -> None:
        super().__init__(message)
        self.status = status
        self.message = message


def _reject_path_like(value: str) -> None:
    """Raise unless *value* is free of any path separator / traversal / colon."""
    text = str(value or "")
    if not text:
        raise RuntimeInspectError(404, "session not found")
    for bad in _PATH_LIKE_CHARS:
        if bad in text:
            # 404, not 400: do not confirm the value was 'almost' a path.
            raise RuntimeInspectError(404, "session not found")


def resolve_runtime_inspect_db(
    control_db,
    *,
    session_uid: str,
    requesting_user_id: str,
    requesting_username: str = "",
    is_admin: bool = False,
):
    """Resolve + authorize a per-session runtime DB for raw inspection.

    Security contract (plan §2.11 / R14/R21):

    1. ``session_uid`` ONLY — never a path. Any value containing ``/ \\ .. :`` is
       rejected as 404 (defense in depth; a real uid is uuid4 hex).
    2. Resolve THROUGH the control-DB manifest to find the owning session, then
       RECOMPUTE the expected runtime path from ``session_uid`` + the configured
       runtime root and assert the manifest path resolves to the SAME file AND is
       contained under ``Path(ATLAS_RUNTIME_DB_ROOT).resolve()``. A path that
       escapes the root, or a manifest path that disagrees with the recomputed
       one, is rejected (404) — the stored path is never trusted blindly (R23).
    3. OWNERSHIP is enforced even under local-admin/bypass: the requesting user
       must own the session that owns this runtime DB. A non-admin who does not
       own it gets 403; an admin still only gets sessions whose ownership we can
       verify (admins inspect their own; cross-user disclosure stays blocked).
    4. On ANY failure raise :class:`RuntimeInspectError` with a path-free message;
       the file path is NEVER returned to the caller.

    Returns an OPEN read-only ``AtlasDB`` on the runtime file (caller closes it).
    """
    from core.atlas_db import AtlasDB
    from core.atlas_db_router import AtlasDBRouter, RuntimeDBError

    uid = str(session_uid or "").strip().lower()
    _reject_path_like(uid)

    # The uid must be pure hex (the router's path primitive). Anything else can
    # never name a legitimate runtime file.
    if not AtlasDBRouter._is_safe_uid(uid):
        raise RuntimeInspectError(404, "session not found")

    # 1. Manifest lookup (control DB) -> owning session_id + stored path.
    manifest = control_db.get_session_runtime_db_by_uid(uid)
    if not manifest:
        raise RuntimeInspectError(404, "session not found")
    owning_session_id = str(manifest.get("session_id") or "")
    stored_path = str(manifest.get("runtime_db_path") or "")

    # 2. OWNERSHIP — even under is_local_admin_mode()/bypass. The session row in
    # control carries the canonical owner. A user may inspect ONLY a session they
    # own; an admin is still scoped to ownership we can verify (no cross-user
    # disclosure). The lookup stays on the control DB.
    session_row = control_db.get_session(owning_session_id) or control_db.find_session(
        owning_session_id
    )
    if session_row is None:
        raise RuntimeInspectError(404, "session not found")
    owner_user_id = str(session_row.get("user_id") or "")
    req_uid = str(requesting_user_id or "").strip()
    owns = bool(req_uid) and owner_user_id == req_uid
    if not owns:
        # Admin bypass does NOT grant cross-user runtime reads (R21). Deny.
        raise RuntimeInspectError(403, "not authorized for this session")

    # 3. Recompute expected path from uid+root and containment-check. The router
    # raises RuntimeDBError if the derived path would escape the root.
    router = AtlasDBRouter()
    try:
        expected_path = router._expected_runtime_path(uid)
    except RuntimeDBError:
        raise RuntimeInspectError(404, "session not found")

    runtime_root = Path(router.runtime_root()).resolve()
    try:
        resolved_expected = Path(expected_path).resolve()
        resolved_expected.relative_to(runtime_root)
    except ValueError:
        raise RuntimeInspectError(404, "session not found")

    # The manifest's stored path must agree with the recomputed one (never trust
    # a stored path that points elsewhere — R23).
    if stored_path:
        try:
            if Path(stored_path).resolve() != resolved_expected:
                raise RuntimeInspectError(404, "session not found")
        except RuntimeInspectError:
            raise
        except Exception:
            raise RuntimeInspectError(404, "session not found")

    if not resolved_expected.exists():
        # File missing/not yet created -> explicit, no path echoed.
        raise RuntimeInspectError(404, "runtime database unavailable")

    return AtlasDB(db_path=str(resolved_expected), schema_set="runtime")


def inspect_runtime_table(
    control_db,
    *,
    session_uid: str,
    requesting_user_id: str,
    requesting_username: str = "",
    is_admin: bool = False,
    table: Optional[str] = None,
    limit: int = _DEFAULT_LIMIT,
    offset: int = 0,
    order: str = "desc",
) -> Dict[str, Any]:
    """Authorize + read a per-session runtime DB.

    When *table* is None returns the table catalog (``list_tables``); otherwise a
    paginated row dump (``read_table``). The payload NEVER includes a filesystem
    path. Raises :class:`RuntimeInspectError` (path-free) on any auth/resolve
    failure; the caller maps ``.status``/``.message`` to a JSON error.
    """
    runtime_db = resolve_runtime_inspect_db(
        control_db,
        session_uid=session_uid,
        requesting_user_id=requesting_user_id,
        requesting_username=requesting_username,
        is_admin=is_admin,
    )
    try:
        if table is None:
            payload = list_tables(runtime_db)
            payload["session_uid"] = str(session_uid or "").strip().lower()
            return payload
        body, err = read_table(
            runtime_db, table, limit=limit, offset=offset, order=order
        )
        if err:
            raise RuntimeInspectError(400, err)
        assert body is not None  # read_table returns body when err is None
        body["session_uid"] = str(session_uid or "").strip().lower()
        return body
    finally:
        try:
            runtime_db.close()
        except Exception:
            pass
