"""Control-DB usage rollups for per-session runtime DBs (Wave 3 / Task 7).

Once IPC/trace/llm rows live in per-session runtime files (plan §2.1), the
admin/dashboard usage that historically SELECTed the single control DB would
either go EMPTY or have to fan out across ~100 runtime files on every request.
The fix (plan §2.10, R1/R8) is a PERIODIC rollup that folds new runtime rows
INTO the control DB; readers then query ``runtime_usage_rollups`` and never open
a runtime file on a normal request.

Idempotency contract (R1):
  For each runtime source table we keep a MONOTONIC high-water key = the SQLite
  ``rowid`` (per-file, collision-free, strictly increasing). We aggregate ONLY
  rows with ``rowid > stored_offset``, fold their counts/sums into the rollup
  row, then advance the offset. Re-running NEVER double-counts. We deliberately
  do NOT key on ``(created_at, uuid)``: ``created_at`` is wall-clock
  ``time.time()`` (non-monotonic, tie-prone) and the row id is a random uuid.

Rowid-reuse contract (MEDIUM fix):
  SQLite ``rowid`` (for a table WITHOUT ``INTEGER PRIMARY KEY AUTOINCREMENT``) is
  REUSED after rows are deleted. ``session_queue`` is cleaned mid-life by
  ``cleanup_old_messages`` (atlas_db): once a queue is drained, new inserts get
  rowids <= the stored high-water offset and would be SILENTLY SKIPPED by the
  ``rowid > offset`` slice -> ``queue_in``/``queue_out`` (and potentially
  ``messages``) under-count. Guard: before aggregating a source table we read its
  current ``MAX(rowid)``; if it is BELOW the stored offset the table was
  drained/reset (rowids will be reused), so we RESET that table's offset to 0 and
  RECOUNT all current rows as an ABSOLUTE total, overwriting ONLY that table's
  columns in the rollup row. The append-only case (``MAX(rowid) >= offset``)
  keeps the incremental additive delta.

  Consequence: ``queue_in``/``queue_out`` are therefore CURRENT-WINDOW counts (an
  operational metric reflecting the live queue), NOT a strictly-cumulative
  lifetime total. ``llm_calls``/``tokens_*``/``cache_*``/``cost_usd`` and
  ``trace_events`` are append-only mid-life, so they remain strictly cumulative
  and exact.

Atomic fold (LOW#1 fix):
  The per-session counter write AND the offset advance happen in ONE control-DB
  transaction (``AtlasDB.fold_runtime_usage_rollup``): a crash between the two
  can no longer re-add the same slice on the next run (no double-count).

Failure contract (R7/R8):
  A MISSING or corrupt runtime DB marks that session's rollup row
  ``status='stale'`` / ``'error'`` with a ``rollup_lag_s`` so a reader surfaces a
  non-silent staleness signal instead of a false-empty. ``rollup_all_active``
  NEVER raises out of the per-session loop and NEVER deletes raw runtime rows.

Freshness (plan §2.10):
  Normal target ``rollup_lag_s <= 10s``. A stale rollup reports its lag rather
  than blocking a reader.

Central mode:
  In ``ATLAS_RUNTIME_DB_MODE=central`` (default) there are no per-session runtime
  files — every read still hits the control DB exactly as today. Callers should
  not invoke the rollup in central mode; ``runtime_mode_active()`` is provided so
  read paths can branch.
"""

from __future__ import annotations

import os
import sqlite3
import time
from dataclasses import dataclass, field
from typing import Any, Dict, List, Optional

from core.atlas_db import AtlasDB
from core.atlas_db_router import AtlasDBRouter, RuntimeDBError


# Source tables we roll up. Each entry carries TWO aggregate SQLs:
#   * incremental: applied to the NEW-rows slice (rowid > offset), folded as an
#     additive delta — the normal append-only case.
#   * recount: applied to ALL current rows (no rowid filter), used when a table's
#     MAX(rowid) regressed below the stored offset (drained/reused rowids) — the
#     result OVERWRITES that table's columns as an absolute current-window count.
# Both return a single row of named counters mapping 1:1 onto
# runtime_usage_rollups columns (plus ``max_rowid`` for the offset advance).
# ``None`` counters are coalesced to 0 by the caller.
_LLM_AGG_SQL = """
    SELECT
        COUNT(*)                              AS llm_calls,
        COALESCE(SUM(tokens_input), 0)        AS tokens_input,
        COALESCE(SUM(tokens_output), 0)       AS tokens_output,
        COALESCE(SUM(tokens_reasoning), 0)    AS tokens_reasoning,
        COALESCE(SUM(cache_read_tokens), 0)   AS cache_read_tokens,
        COALESCE(SUM(cache_write_tokens), 0)  AS cache_write_tokens,
        COALESCE(SUM(cost_usd), 0)            AS cost_usd,
        COALESCE(MAX(rowid), 0)              AS max_rowid
      FROM llm_calls
     WHERE rowid > ?
"""

_LLM_RECOUNT_SQL = """
    SELECT
        COUNT(*)                              AS llm_calls,
        COALESCE(SUM(tokens_input), 0)        AS tokens_input,
        COALESCE(SUM(tokens_output), 0)       AS tokens_output,
        COALESCE(SUM(tokens_reasoning), 0)    AS tokens_reasoning,
        COALESCE(SUM(cache_read_tokens), 0)   AS cache_read_tokens,
        COALESCE(SUM(cache_write_tokens), 0)  AS cache_write_tokens,
        COALESCE(SUM(cost_usd), 0)            AS cost_usd,
        COALESCE(MAX(rowid), 0)              AS max_rowid
      FROM llm_calls
"""

_TRACE_AGG_SQL = """
    SELECT COUNT(*) AS trace_events, COALESCE(MAX(rowid), 0) AS max_rowid
      FROM trace_events
     WHERE rowid > ?
"""

_TRACE_RECOUNT_SQL = """
    SELECT COUNT(*) AS trace_events, COALESCE(MAX(rowid), 0) AS max_rowid
      FROM trace_events
"""

_MESSAGES_AGG_SQL = """
    SELECT COUNT(*) AS messages, COALESCE(MAX(rowid), 0) AS max_rowid
      FROM messages
     WHERE rowid > ?
"""

_MESSAGES_RECOUNT_SQL = """
    SELECT COUNT(*) AS messages, COALESCE(MAX(rowid), 0) AS max_rowid
      FROM messages
"""

_QUEUE_AGG_SQL = """
    SELECT
        COALESCE(SUM(CASE WHEN direction = 'in' THEN 1 ELSE 0 END), 0)  AS queue_in,
        COALESCE(SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END), 0) AS queue_out,
        COALESCE(MAX(rowid), 0) AS max_rowid
      FROM session_queue
     WHERE rowid > ?
"""

_QUEUE_RECOUNT_SQL = """
    SELECT
        COALESCE(SUM(CASE WHEN direction = 'in' THEN 1 ELSE 0 END), 0)  AS queue_in,
        COALESCE(SUM(CASE WHEN direction = 'out' THEN 1 ELSE 0 END), 0) AS queue_out,
        COALESCE(MAX(rowid), 0) AS max_rowid
      FROM session_queue
"""

# MAX(rowid) probe per source table — used to detect a drained/reused table
# (current MAX(rowid) below the stored offset) before deciding incremental vs
# recount.
_MAX_ROWID_SQL = "SELECT COALESCE(MAX(rowid), 0) AS max_rowid FROM {table}"

# (source_table key, incremental agg SQL, recount SQL, counter columns produced)
_SOURCES = (
    ("llm_calls", _LLM_AGG_SQL, _LLM_RECOUNT_SQL, (
        "llm_calls", "tokens_input", "tokens_output", "tokens_reasoning",
        "cache_read_tokens", "cache_write_tokens", "cost_usd",
    )),
    ("trace_events", _TRACE_AGG_SQL, _TRACE_RECOUNT_SQL, ("trace_events",)),
    ("messages", _MESSAGES_AGG_SQL, _MESSAGES_RECOUNT_SQL, ("messages",)),
    ("session_queue", _QUEUE_AGG_SQL, _QUEUE_RECOUNT_SQL, ("queue_in", "queue_out")),
)

# Freshness target (plan §2.10). Exposed so harness/observability can assert it.
ROLLUP_LAG_TARGET_S = 10.0


@dataclass
class RollupResult:
    """Outcome of rolling up ONE session."""

    session_id: str
    session_uid: Optional[str] = None
    status: str = "ok"  # "ok" | "stale" | "error" | "skipped"
    rollup_lag_s: float = 0.0
    deltas: Dict[str, int] = field(default_factory=dict)
    error: Optional[str] = None


def runtime_mode_active(router: Optional[AtlasDBRouter] = None) -> bool:
    """True when the per-session runtime split is active (session mode)."""
    router = router or AtlasDBRouter()
    try:
        return router.mode() == "session"
    except RuntimeDBError:
        return False


def _runtime_age_seconds(runtime_db_path: str) -> float:
    """Best-effort age of the newest write to the runtime file (for lag).

    Uses the file mtime as a cheap proxy for "how long ago did this session
    last write". When the file is missing we return 0 and let the caller set the
    lag from the manifest ``updated_at`` instead.
    """
    try:
        mtime = os.path.getmtime(runtime_db_path)
        return max(0.0, time.time() - mtime)
    except OSError:
        return 0.0


def _identity_from_manifest(
    control: AtlasDB, session_id: str, manifest: Dict[str, Any]
) -> Dict[str, Any]:
    """Build the descriptive columns for the rollup row.

    session_uid + runtime_db_path come from the manifest; user_id/owner/ip/
    workflow come from the control ``sessions`` row (the source of truth for
    identity — a runtime DB does not carry it).
    """
    identity: Dict[str, Any] = {
        "session_uid": manifest.get("session_uid"),
        "runtime_db_path": manifest.get("runtime_db_path"),
    }
    sess = control.find_session(session_id)
    if sess:
        identity["user_id"] = sess.get("user_id")
        identity["owner"] = sess.get("owner")
        identity["ip"] = sess.get("ip") or sess.get("ip_id")
        identity["workflow"] = sess.get("workflow")
    return identity


def rollup_session(
    session_id: str,
    router: Optional[AtlasDBRouter] = None,
    *,
    control: Optional[AtlasDB] = None,
) -> RollupResult:
    """Idempotently fold NEW runtime rows for *session_id* into the control rollup.

    Steps:
      1. Resolve the manifest row (control DB) -> session_uid + runtime path.
      2. Open the runtime DB read-only via the router (``create=False``).
      3. For each source table, aggregate rows with ``rowid > stored_offset``,
         add the deltas to the rollup row, then advance the offset.
      4. Set ``status='ok'`` + ``rollup_lag_s`` (file age) on success.

    A MISSING/corrupt runtime DB does NOT raise: it marks the rollup row
    ``status='stale'`` (missing) / ``'error'`` (corrupt) with a lag derived from
    the manifest age, and returns a RollupResult describing it.
    """
    router = router or AtlasDBRouter()
    own_control = control is None
    control = control or router.control_db()
    try:
        manifest = control.get_session_runtime_db(session_id)
        if not manifest:
            # No manifest row -> nothing to roll up (session never activated a
            # runtime DB). Not an error; just skipped.
            return RollupResult(session_id=session_id, status="skipped")

        session_uid = manifest.get("session_uid")
        runtime_path = manifest.get("runtime_db_path") or ""
        identity = _identity_from_manifest(control, session_id, manifest)

        # Missing file -> stale (recoverable: the worker may recreate it).
        if not runtime_path or not os.path.exists(runtime_path):
            lag = _manifest_lag(manifest)
            control.mark_runtime_usage_rollup_status(
                session_id,
                status="stale",
                rollup_lag_s=lag,
                identity=identity,
            )
            try:
                control.update_session_runtime_db_status(session_id, "stale")
            except Exception:
                pass
            return RollupResult(
                session_id=session_id,
                session_uid=session_uid,
                status="stale",
                rollup_lag_s=lag,
                error="runtime DB file missing",
            )

        # Open the runtime DB read-only (create=False). A corrupt file surfaces
        # as a sqlite error here (init/schema preflight on open) OR on first query
        # below -> mark error, continue. Catch sqlite errors AND RuntimeDBError so
        # neither aborts rollup_all_active (plan §2.10 / R7: never raise out).
        try:
            runtime_db = router.runtime_db(session_id, create=False)
        except (RuntimeDBError, sqlite3.DatabaseError) as exc:
            return _mark_error(control, session_id, identity, manifest, str(exc))

        deltas: Dict[str, float] = {}
        absolutes: Dict[str, float] = {}
        offset_updates: Dict[str, int] = {}
        try:
            for source_table, agg_sql, recount_sql, counters in _SOURCES:
                offset = control.get_rollup_offset(session_id, source_table)
                # Detect a drained/reused table: SQLite reuses rowids after rows
                # are deleted (cleanup_old_messages drains session_queue), so a
                # current MAX(rowid) BELOW the stored offset means new rows landed
                # at rowids <= offset and would be silently skipped by the
                # ``rowid > offset`` slice. Recount that table's CURRENT rows as an
                # absolute total and reset its offset to the recounted MAX(rowid).
                probe = runtime_db._fetchone(
                    _MAX_ROWID_SQL.format(table=source_table)
                )
                cur_max = int(dict(probe).get("max_rowid") or 0) if probe else 0
                if cur_max < offset:
                    row = runtime_db._fetchone(recount_sql)
                    rowd = dict(row) if row is not None else {}
                    for col in counters:
                        # Overwrite ONLY this table's columns (absolute recount).
                        absolutes[col] = _num(rowd.get(col))
                    # Reset offset DOWN to the recounted high-water (may be 0).
                    offset_updates[source_table] = int(rowd.get("max_rowid") or 0)
                else:
                    row = runtime_db._fetchone(agg_sql, (offset,))
                    rowd = dict(row) if row is not None else {}
                    for col in counters:
                        deltas[col] = deltas.get(col, 0) + _num(rowd.get(col))
                    max_rowid = int(rowd.get("max_rowid") or 0)
                    # Only advance past the offset (MAX returns 0 on empty slice).
                    new_offset = max(offset, max_rowid)
                    if new_offset > offset:
                        offset_updates[source_table] = new_offset
        except sqlite3.DatabaseError as exc:
            return _mark_error(control, session_id, identity, manifest, str(exc))
        finally:
            try:
                runtime_db.close()
            except Exception:
                pass

        lag = _runtime_age_seconds(runtime_path)
        # Atomic fold (LOW#1): the counter write AND the offset advances happen in
        # ONE control-DB transaction, so a crash cannot re-add the same slice next
        # run. ``absolutes`` overwrites only the recounted (drained/reused) tables'
        # columns; ``deltas`` is the additive append-only fold for the rest.
        control.fold_runtime_usage_rollup(
            session_id,
            deltas=deltas,
            absolutes=absolutes,
            offsets=offset_updates,
            identity=identity,
            status="ok",
            rollup_lag_s=lag,
        )

        # Reflect freshness on the manifest too (best-effort).
        try:
            if manifest.get("status") in ("stale", "error"):
                control.update_session_runtime_db_status(session_id, "active")
        except Exception:
            pass

        # Report what this run contributed: additive deltas for append-only
        # tables plus the absolute recount for any drained/reused table.
        reported = dict(deltas)
        reported.update(absolutes)
        int_deltas = {k: int(round(v)) if k != "cost_usd" else v
                      for k, v in reported.items()}
        return RollupResult(
            session_id=session_id,
            session_uid=session_uid,
            status="ok",
            rollup_lag_s=lag,
            deltas=int_deltas,
        )
    finally:
        if own_control:
            try:
                control.close()
            except Exception:
                pass


def rollup_all_active(
    limit: Optional[int] = None,
    router: Optional[AtlasDBRouter] = None,
    *,
    status_filter: Optional[str] = None,
) -> List[RollupResult]:
    """Roll up every active session listed in the manifest.

    NEVER raises out of the per-session loop: a missing/corrupt runtime DB for
    one session is recorded as stale/error and the loop CONTINUES (plan §2.10 /
    R7). Returns one RollupResult per session attempted.

    ``limit`` caps how many sessions are processed in one pass (the manifest is
    ordered newest-first, so the freshest sessions roll up first). ``status_filter``
    restricts to manifest rows of a given status (default: active rows).
    """
    router = router or AtlasDBRouter()
    control = router.control_db()
    results: List[RollupResult] = []
    try:
        rows = control.list_session_runtime_dbs(
            status=status_filter if status_filter is not None else None
        )
        if status_filter is None:
            # Default: skip rows already hard-deleted/archived; keep active+stale
            # (a stale row should be retried — its file may have come back).
            rows = [r for r in rows if r.get("status") in ("active", "stale", "error")]
        if limit is not None:
            rows = rows[: max(0, int(limit))]
        for manifest in rows:
            session_id = manifest.get("session_id")
            if not session_id:
                continue
            try:
                results.append(
                    rollup_session(session_id, router=router, control=control)
                )
            except Exception as exc:  # defensive: never let one session abort the pass
                results.append(
                    RollupResult(
                        session_id=session_id,
                        session_uid=manifest.get("session_uid"),
                        status="error",
                        error=f"unexpected: {exc}",
                    )
                )
        return results
    finally:
        try:
            control.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Read-side helpers (used by atlas_admin_usage / atlas_user_dashboard)
# --------------------------------------------------------------------------- #


# Sentinel a UI can show for admin tabs that a count-only rollup CANNOT
# reconstruct (per-tool usage, interventions, todo-flow) in runtime mode. The
# read path returns this list-of-one marker instead of a silently-empty list so
# the operator KNOWS the tab is summary-only, not just idle (plan §2.10 / R8).
SUMMARY_ONLY_MARKER = {
    "__summary_only__": True,
    "reason": "runtime-db mode: this tab needs per-row data not in count-only rollups",
}


def summary_only_payload() -> List[Dict[str, Any]]:
    """Return the explicit 'summary-only in runtime mode' marker list."""
    return [dict(SUMMARY_ONLY_MARKER)]


def rollup_totals_by_user(control: AtlasDB) -> Dict[str, Dict[str, Any]]:
    """Aggregate rollup rows into per-user totals (control DB read, no fanout).

    Returns ``{user_id: {llm_calls, tokens_in, tokens_out, tokens_reasoning,
    total_cost_usd, session_count, stale_sessions, max_rollup_lag_s}}``. Used by
    admin/dashboard totals so a NORMAL request never opens a runtime file.
    """
    rows = control.list_runtime_usage_rollups()
    by_user: Dict[str, Dict[str, Any]] = {}
    for row in rows:
        uid = str(row.get("user_id") or "")
        agg = by_user.setdefault(uid, {
            "user_id": uid,
            "llm_calls": 0,
            "tokens_in": 0,
            "tokens_out": 0,
            "tokens_reasoning": 0,
            "total_cost_usd": 0.0,
            "session_count": 0,
            "stale_sessions": 0,
            "max_rollup_lag_s": 0.0,
        })
        agg["llm_calls"] += int(row.get("llm_calls") or 0)
        agg["tokens_in"] += int(row.get("tokens_input") or 0)
        agg["tokens_out"] += int(row.get("tokens_output") or 0)
        agg["tokens_reasoning"] += int(row.get("tokens_reasoning") or 0)
        agg["total_cost_usd"] += float(row.get("cost_usd") or 0)
        agg["session_count"] += 1
        if str(row.get("status") or "ok") != "ok":
            agg["stale_sessions"] += 1
        agg["max_rollup_lag_s"] = max(
            agg["max_rollup_lag_s"], float(row.get("rollup_lag_s") or 0)
        )
    return by_user


def rollup_grand_totals(control: AtlasDB) -> Dict[str, Any]:
    """Single aggregate of ALL rollup rows (fleet-wide totals)."""
    row = control._fetchone(
        """
        SELECT
            COALESCE(SUM(llm_calls), 0)         AS llm_calls,
            COALESCE(SUM(tokens_input), 0)      AS tokens_in,
            COALESCE(SUM(tokens_output), 0)     AS tokens_out,
            COALESCE(SUM(tokens_reasoning), 0)  AS tokens_reasoning,
            COALESCE(SUM(cost_usd), 0)         AS total_cost_usd,
            COALESCE(SUM(trace_events), 0)      AS trace_events,
            COALESCE(SUM(messages), 0)          AS messages,
            COUNT(*)                            AS session_count,
            COALESCE(SUM(CASE WHEN status != 'ok' THEN 1 ELSE 0 END), 0) AS stale_sessions,
            COALESCE(MAX(rollup_lag_s), 0)      AS max_rollup_lag_s
          FROM runtime_usage_rollups
        """
    )
    return dict(row) if row is not None else {
        "llm_calls": 0, "tokens_in": 0, "tokens_out": 0, "tokens_reasoning": 0,
        "total_cost_usd": 0.0, "trace_events": 0, "messages": 0,
        "session_count": 0, "stale_sessions": 0, "max_rollup_lag_s": 0.0,
    }


# --------------------------------------------------------------------------- #
# Internals
# --------------------------------------------------------------------------- #


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _manifest_lag(manifest: Dict[str, Any]) -> float:
    """Lag derived from the manifest's last activity timestamp."""
    try:
        last = float(manifest.get("updated_at") or manifest.get("created_at") or 0)
    except (TypeError, ValueError):
        last = 0.0
    if last <= 0:
        return 0.0
    return max(0.0, time.time() - last)


def _mark_error(
    control: AtlasDB,
    session_id: str,
    identity: Dict[str, Any],
    manifest: Dict[str, Any],
    message: str,
) -> RollupResult:
    """Quarantine a corrupt/unreadable runtime DB (status='error'), no raise."""
    lag = _manifest_lag(manifest)
    control.mark_runtime_usage_rollup_status(
        session_id,
        status="error",
        rollup_lag_s=lag,
        identity=identity,
    )
    try:
        control.update_session_runtime_db_status(session_id, "error")
    except Exception:
        pass
    return RollupResult(
        session_id=session_id,
        session_uid=manifest.get("session_uid"),
        status="error",
        rollup_lag_s=lag,
        error=message,
    )
