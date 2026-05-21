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
from typing import Any, Dict, List, Optional, Tuple

# Hard cap so a careless caller can't pull a million rows in one shot.
_MAX_LIMIT = 500
_DEFAULT_LIMIT = 50

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
