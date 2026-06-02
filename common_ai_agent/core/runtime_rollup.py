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


# Sentinel for IP-SCOPED readers (orchestrator ground-truth panel + worker
# prompt context) whose source rows (non-chat ``trace_events`` + ``llm_calls``)
# are now SHARDED across the many per-session runtime DBs that belong to one IP
# (plan §2.10 / R7). A single control-DB read can no longer reconstruct them, and
# there is no single runtime file to open (an IP has N sessions). Returning an
# EXPLICIT "unavailable in runtime mode" marker — instead of a silently-empty
# list — keeps the AGENT from being told "nothing happened" when the truth is
# "the data moved". The orchestrator/UI can render this honestly.
RUNTIME_UNAVAILABLE_MARKER = {
    "__runtime_unavailable__": True,
    "reason": (
        "runtime-db session mode: per-IP trace/llm rows are sharded across "
        "per-session runtime DBs and are not available from a single control read"
    ),
}


def runtime_unavailable_events() -> List[Dict[str, Any]]:
    """Explicit 'this IP-scoped runtime slice is unavailable in session mode' marker.

    Used by the omitted IP-scoped readers (``_recent_events_for_ip`` and the
    room-context summaries) so they NEVER false-empty when the runtime split is
    active. A reader can detect the marker via :func:`is_runtime_unavailable`.
    """
    return [dict(RUNTIME_UNAVAILABLE_MARKER)]


def is_runtime_unavailable(events: Any) -> bool:
    """True when *events* is the explicit runtime-unavailable marker list."""
    return (
        isinstance(events, list)
        and len(events) == 1
        and isinstance(events[0], dict)
        and bool(events[0].get("__runtime_unavailable__"))
    )


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


# --------------------------------------------------------------------------- #
# Operational guardrails: delete / restart-recovery / rollback / fleet health
# (Wave 3 / Task 9, plan §2.12 + R12/R13/R18/R25)
#
# These live here (NOT in atlas_db) because they need the ROUTER (path
# resolution + containment) and the FILESYSTEM (the on-disk runtime .db / -wal /
# -shm). atlas_db owns only the control-DB SQL primitives they call.
# --------------------------------------------------------------------------- #


# Runtime sidecar suffixes that must be removed alongside the main .db file.
_RUNTIME_DB_SIDECARS = ("", "-wal", "-shm")


@dataclass
class DeleteResult:
    """Outcome of a runtime-DB session delete (plan §2.12 / R12)."""

    session_id: str
    session_uid: Optional[str] = None
    deleted: bool = False
    forced: bool = False
    queue_depth: int = 0
    files_removed: List[str] = field(default_factory=list)
    control_counts: Dict[str, int] = field(default_factory=dict)
    skipped_reason: Optional[str] = None


def _runtime_files_for(runtime_path: str) -> List[str]:
    """Return the .db + -wal + -shm sidecar paths that EXIST on disk."""
    out: List[str] = []
    for suffix in _RUNTIME_DB_SIDECARS:
        candidate = runtime_path + suffix
        if os.path.exists(candidate):
            out.append(candidate)
    return out


def _safe_runtime_path(
    router: AtlasDBRouter, manifest: Dict[str, Any]
) -> Optional[str]:
    """Recompute the containment-checked runtime path from the manifest's uid.

    NEVER trusts the stored ``runtime_db_path`` blindly (plan §2.11 / R23): the
    path is recomputed from ``session_uid`` + root and rejected if it escapes the
    root. Returns None when the uid is missing/unsafe (caller treats as no file).
    """
    uid = manifest.get("session_uid")
    if not uid:
        return None
    try:
        return router._expected_runtime_path(uid)  # containment-guarded
    except RuntimeDBError:
        return None


def delete_session_runtime(
    session_id: str,
    *,
    force: bool = False,
    router: Optional[AtlasDBRouter] = None,
    process_manager: Any = None,
) -> DeleteResult:
    """Delete a session's runtime DB + control bookkeeping without orphaning state.

    Plan §2.12 / R12 + carried Task-7 LOW#2. In SESSION mode this:

      1. resolves the manifest -> session_uid -> containment-checked runtime path;
      2. reads the queue depth (undelivered out-rows + unprocessed in-rows);
      3. GATE: if depth > 0 and ``force`` is False, does NOT delete — returns a
         skipped result. The caller must pass ``force=True`` to proceed, which
         writes a ``force_delete`` audit row capturing the lost depth;
      4. evicts any cached runtime-DB handle via the process manager (so no stale
         connection survives to a now-unlinked inode);
      5. removes the on-disk .db + -wal + -shm files;
      6. atomically scrubs the manifest row + rollup row + ALL offset rows.

    After this returns ``deleted=True`` there are ZERO orphan files and ZERO
    manifest/rollup/offset rows for the session. A normal (depth==0) delete still
    writes a lightweight ``delete`` audit row. In CENTRAL mode there is no runtime
    file/manifest to remove: the function is a no-op returning ``deleted=False``
    with ``skipped_reason='central_mode'`` so the caller's existing control-table
    delete remains the whole story.
    """
    router = router or AtlasDBRouter()
    try:
        mode = router.mode()
    except RuntimeDBError:
        mode = "central"
    if mode != "session":
        return DeleteResult(
            session_id=session_id,
            deleted=False,
            skipped_reason="central_mode",
        )

    control = router.control_db()
    try:
        manifest = control.get_session_runtime_db(session_id)
        if not manifest:
            # No runtime DB was ever activated for this session: nothing to do.
            return DeleteResult(
                session_id=session_id,
                deleted=False,
                skipped_reason="no_manifest",
            )

        session_uid = manifest.get("session_uid")
        runtime_path = _safe_runtime_path(router, manifest)

        # Queue depth gate (R12): count in-flight work in the runtime file.
        depth = 0
        if runtime_path and os.path.exists(runtime_path):
            try:
                rdb = AtlasDB(runtime_path, schema_set="runtime")
                try:
                    depth = rdb.session_queue_depth(session_id).get("total", 0)
                finally:
                    rdb.close()
            except sqlite3.DatabaseError:
                # Corrupt file: treat as 0 in-flight work but still delete it.
                depth = 0

        if depth > 0 and not force:
            # NON-SILENT: refuse to delete, leaving everything intact. The
            # operator must re-issue with force=True (audited below).
            return DeleteResult(
                session_id=session_id,
                session_uid=session_uid,
                deleted=False,
                forced=False,
                queue_depth=depth,
                skipped_reason="queue_non_empty",
            )

        # Evict any cached handle BEFORE unlinking the file so a later reuse can
        # never hand back a connection to a stale/unlinked inode (R2 + R12).
        if process_manager is not None:
            try:
                process_manager._evict_db_handles(session_id)
            except Exception:
                pass

        files_removed: List[str] = []
        if runtime_path:
            for path in _runtime_files_for(runtime_path):
                try:
                    os.remove(path)
                    files_removed.append(path)
                except OSError:
                    pass

        control_counts = control.delete_runtime_db_manifest(session_id)

        # Audit: a forced delete (lost in-flight work) is the operationally
        # sensitive case, but record every runtime delete for traceability.
        control.record_runtime_db_audit(
            "force_delete" if (force and depth > 0) else "delete",
            session_id=session_id,
            session_uid=session_uid,
            forced=bool(force and depth > 0),
            queue_depth=depth,
            detail={
                "files_removed": files_removed,
                "control_counts": control_counts,
                "runtime_path": runtime_path,
            },
        )
        return DeleteResult(
            session_id=session_id,
            session_uid=session_uid,
            deleted=True,
            forced=bool(force and depth > 0),
            queue_depth=depth,
            files_removed=files_removed,
            control_counts=control_counts,
        )
    finally:
        try:
            control.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# UI-restart recovery (plan §2.12 / R13)
# --------------------------------------------------------------------------- #


@dataclass
class RecoveryPlan:
    """One session's restart-recovery decision (plan §2.12 / R13)."""

    session_id: str
    session_uid: Optional[str] = None
    runtime_db_path: Optional[str] = None
    # The cursor a restarted broadcaster should resume the OUT stream from:
    #   * an out-row id -> resume strictly AFTER it (already-delivered up to here)
    #   * None          -> poll from the TOP (nothing delivered yet -> replay all
    #                      buffered, undelivered output; correct, no dupes)
    resume_cursor: Optional[str] = None
    undelivered_out: int = 0
    unprocessed_in: int = 0
    status: str = "ok"  # ok | missing | error
    orphan_pids_pruned: List[int] = field(default_factory=list)


# Documented policy for the in-memory ``_jobs`` map lost on a UI restart.
# ``_jobs`` is volatile main-process state (no DB backing); after a restart it is
# EMPTY. The recovery policy is: do NOT attempt to resurrect ``_jobs`` — instead
# the durable runtime queues are the source of truth. A reconnecting client's
# next poll re-seeds its output cursor from the runtime DB (resume_cursor below),
# so buffered-but-undelivered output is replayed and in-flight prompts are still
# in the runtime ``session_queue`` for the (re)spawned worker to consume. Any
# job-level progress UI that depended on ``_jobs`` is rebuilt lazily from the
# rollups/manifest, never blocking delivery.
JOBS_LOSS_POLICY = (
    "drop-and-rebuild-from-runtime-queues: _jobs is volatile; after restart the "
    "runtime session_queue + reseeded output cursor are the source of truth, so "
    "undelivered output is replayed and in-flight prompts are reconsumed without "
    "resurrecting _jobs"
)


def plan_session_recovery(
    session_id: str,
    *,
    router: Optional[AtlasDBRouter] = None,
    process_manager: Any = None,
) -> RecoveryPlan:
    """Compute the restart-recovery decision for ONE session (plan §2.12 / R13).

    Key correctness point: the resume cursor is the OLDEST-undelivered boundary,
    NOT ``latest_output_id``. Using ``latest_output_id`` would skip every buffered
    out-row a disconnected client never received. We instead resume from the
    NEWEST ALREADY-DELIVERED row (``reseed_output_cursor``): the next poll then
    returns exactly the still-undelivered rows after it (replayed, no dupes). When
    nothing was ever delivered the cursor is None -> poll from the top (replay all
    buffered output, which is correct since no client saw it).

    Also reconciles orphan worker PIDs: a UI restart starts with an empty
    ``_processes`` map, so a worker left running by the previous server is a
    ghost that would consume prompts the new server never polls. The orphan prune
    matches BOTH ``--session-id`` AND ``--db-path`` (the runtime file), so it only
    kills the worker bound to THIS session's runtime DB.
    """
    router = router or AtlasDBRouter()
    control = router.control_db()
    try:
        manifest = control.get_session_runtime_db(session_id)
        session_uid = manifest.get("session_uid") if manifest else None
        runtime_path = _safe_runtime_path(router, manifest) if manifest else None

        if not runtime_path or not os.path.exists(runtime_path):
            return RecoveryPlan(
                session_id=session_id,
                session_uid=session_uid,
                runtime_db_path=runtime_path,
                resume_cursor=None,
                status="missing",
            )

        try:
            rdb = AtlasDB(runtime_path, schema_set="runtime")
        except sqlite3.DatabaseError:
            return RecoveryPlan(
                session_id=session_id,
                session_uid=session_uid,
                runtime_db_path=runtime_path,
                resume_cursor=None,
                status="error",
            )
        try:
            depth = rdb.session_queue_depth(session_id)
            # Resume from newest-already-delivered (None => from the top). This is
            # the oldest-undelivered boundary expressed as a "since" cursor.
            resume_cursor = rdb.reseed_output_cursor(session_id, "out")
        except sqlite3.DatabaseError:
            return RecoveryPlan(
                session_id=session_id,
                session_uid=session_uid,
                runtime_db_path=runtime_path,
                resume_cursor=None,
                status="error",
            )
        finally:
            try:
                rdb.close()
            except Exception:
                pass

        pruned: List[int] = []
        if process_manager is not None:
            try:
                pids = process_manager._external_worker_pids(session_id, runtime_path)
                if pids:
                    process_manager._terminate_external_session_workers(
                        session_id, runtime_path
                    )
                    pruned = list(pids)
            except Exception:
                pruned = []

        return RecoveryPlan(
            session_id=session_id,
            session_uid=session_uid,
            runtime_db_path=runtime_path,
            resume_cursor=resume_cursor,
            undelivered_out=int(depth.get("undelivered", 0)),
            unprocessed_in=int(depth.get("unprocessed", 0)),
            status="ok",
            orphan_pids_pruned=pruned,
        )
    finally:
        try:
            control.close()
        except Exception:
            pass


def recover_all_sessions(
    *,
    router: Optional[AtlasDBRouter] = None,
    process_manager: Any = None,
) -> List[RecoveryPlan]:
    """Scan the manifest and build a RecoveryPlan per active/stale session.

    Called once on UI startup (plan §2.12 / R13). Never raises out of the loop.
    """
    router = router or AtlasDBRouter()
    control = router.control_db()
    try:
        rows = control.list_session_runtime_dbs()
        rows = [r for r in rows if r.get("status") in ("active", "stale", "error")]
    finally:
        try:
            control.close()
        except Exception:
            pass
    plans: List[RecoveryPlan] = []
    for manifest in rows:
        session_id = manifest.get("session_id")
        if not session_id:
            continue
        try:
            plans.append(
                plan_session_recovery(
                    session_id, router=router, process_manager=process_manager
                )
            )
        except Exception as exc:
            plans.append(
                RecoveryPlan(
                    session_id=session_id,
                    session_uid=manifest.get("session_uid"),
                    status="error",
                    resume_cursor=None,
                    orphan_pids_pruned=[],
                )
            )
            _ = exc
    return plans


# --------------------------------------------------------------------------- #
# Forced rollback: runtime -> control (plan §2.12 / R18)
# --------------------------------------------------------------------------- #


@dataclass
class RollbackResult:
    """Outcome of a forced runtime->control queue rollback (plan §2.12 / R18)."""

    session_id: str
    session_uid: Optional[str] = None
    copied_rows: int = 0
    skipped_existing: int = 0
    workers_running: int = 0
    aborted: bool = False
    reason: Optional[str] = None


# What rollback copies, and the documented decision on what it does NOT.
ROLLBACK_HISTORY_POLICY = (
    "queue-only: a forced runtime->control rollback copies ONLY undelivered "
    "session_queue rows (the in-flight prompts/outputs that must not be lost). "
    "Historical runtime messages / trace_events / llm_calls are LEFT ORPHANED in "
    "the runtime files and are NOT re-imported into control — control-mode "
    "history therefore truncates at the rollback boundary. This keeps rollback "
    "idempotent and cheap; the rollups already folded the runtime usage TOTALS "
    "into control before the rollback, so accounting is preserved even though the "
    "per-row history is not."
)


def rollback_session_to_central(
    session_id: str,
    *,
    router: Optional[AtlasDBRouter] = None,
    process_manager: Any = None,
    require_workers_stopped: bool = True,
) -> RollbackResult:
    """Copy a session's UNDELIVERED runtime queue rows back into the control DB.

    Plan §2.12 / R18. Contract:

      * Workers MUST be stopped/drained first. If a live worker for this session
        is detected (orphan PID scan on the runtime path) and
        ``require_workers_stopped`` is True, the rollback ABORTS (no partial copy)
        rather than racing a writer. Pass ``require_workers_stopped=False`` only
        in tests with no real subprocess.
      * Copies undelivered ``session_queue`` rows from the runtime DB into the
        control DB with ``INSERT OR IGNORE`` PRESERVING the original TEXT row id,
        so a re-run copies nothing new (idempotent: run-twice => one row).
      * Writes a ``rollback`` audit row capturing copied/skipped counts.
      * Historical messages/traces/llm_calls are LEFT ORPHANED (documented in
        ``ROLLBACK_HISTORY_POLICY``); they are NOT re-imported.

    Returns a RollbackResult. Safe in central mode (nothing to copy -> 0 rows).
    """
    router = router or AtlasDBRouter()
    try:
        mode = router.mode()
    except RuntimeDBError:
        mode = "central"
    if mode != "session":
        return RollbackResult(
            session_id=session_id,
            copied_rows=0,
            reason="central_mode",
        )

    control = router.control_db()
    runtime_db: Optional[AtlasDB] = None
    try:
        manifest = control.get_session_runtime_db(session_id)
        if not manifest:
            return RollbackResult(session_id=session_id, reason="no_manifest")
        session_uid = manifest.get("session_uid")
        runtime_path = _safe_runtime_path(router, manifest)
        if not runtime_path or not os.path.exists(runtime_path):
            return RollbackResult(
                session_id=session_id,
                session_uid=session_uid,
                reason="no_runtime_file",
            )

        # Workers-stopped guard (R18): refuse to copy while a writer is live.
        workers_running = 0
        if process_manager is not None:
            try:
                pids = process_manager._external_worker_pids(session_id, runtime_path)
                workers_running = len(pids)
            except Exception:
                workers_running = 0
        if workers_running > 0 and require_workers_stopped:
            return RollbackResult(
                session_id=session_id,
                session_uid=session_uid,
                workers_running=workers_running,
                aborted=True,
                reason="workers_running",
            )

        try:
            runtime_db = AtlasDB(runtime_path, schema_set="runtime")
        except sqlite3.DatabaseError as exc:
            return RollbackResult(
                session_id=session_id,
                session_uid=session_uid,
                aborted=True,
                reason=f"runtime_open_failed: {exc}",
            )

        # Read undelivered rows in strict total order (created_at, rowid) so the
        # control DB receives them in the same order they would have been polled.
        rows = runtime_db._fetchall(
            """
            SELECT id, session_id, direction, msg_type, payload, created_at,
                   processed_at, delivered_at, expires_at
              FROM session_queue
             WHERE session_id = ? AND delivered_at IS NULL
             ORDER BY created_at ASC, rowid ASC
            """,
            (session_id,),
        )

        copied = 0
        skipped = 0
        with control._lock:
            conn = control._connect()
            try:
                for row in rows:
                    cursor = conn.execute(
                        """
                        INSERT OR IGNORE INTO session_queue
                            (id, session_id, direction, msg_type, payload,
                             created_at, processed_at, delivered_at, expires_at)
                        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                        """,
                        (
                            row["id"], row["session_id"], row["direction"],
                            row["msg_type"], row["payload"], row["created_at"],
                            row["processed_at"], row["delivered_at"],
                            row["expires_at"],
                        ),
                    )
                    if cursor.rowcount and cursor.rowcount > 0:
                        copied += 1
                    else:
                        skipped += 1
                conn.commit()
            except Exception:
                conn.rollback()
                raise

        control.record_runtime_db_audit(
            "rollback",
            session_id=session_id,
            session_uid=session_uid,
            forced=True,
            queue_depth=len(rows),
            detail={
                "copied_rows": copied,
                "skipped_existing": skipped,
                "history_policy": "queue-only; messages/traces/llm_calls orphaned",
            },
        )
        return RollbackResult(
            session_id=session_id,
            session_uid=session_uid,
            copied_rows=copied,
            skipped_existing=skipped,
            workers_running=workers_running,
        )
    finally:
        if runtime_db is not None:
            try:
                runtime_db.close()
            except Exception:
                pass
        try:
            control.close()
        except Exception:
            pass


# --------------------------------------------------------------------------- #
# Fleet health / audit (plan §2.12 / R25 — JSON the Task-10 harness consumes)
# --------------------------------------------------------------------------- #


def fleet_health(
    *,
    router: Optional[AtlasDBRouter] = None,
    process_manager: Any = None,
) -> Dict[str, Any]:
    """Return a JSON-serializable fleet health/audit report (plan §2.12 / R25).

    Per-session: queue depth (undelivered/unprocessed), rollup_lag_s,
    runtime-file presence + size, oldest-undelivered age. Fleet-wide:
    manifest-row-count vs on-disk-file-count, total runtime bytes, total
    undelivered rows, orphan-file count (files under the root with NO manifest
    row), runtime-DB open/init failure count, and the 'database is locked' retry
    count surfaced by the process manager (when wired). ``rollback_allowed`` is
    True iff EVERY session's in-flight queue depth is 0 (safe to flip back to
    central). The Task-10 harness asserts on this shape.

    Never raises: a per-session probe failure is captured as that session's
    ``status='error'`` and incremented into ``open_init_failures``.
    """
    router = router or AtlasDBRouter()
    control = router.control_db()
    report: Dict[str, Any] = {
        "mode": "central",
        "sessions": [],
        "manifest_count": 0,
        "on_disk_file_count": 0,
        "orphan_file_count": 0,
        "total_runtime_bytes": 0,
        "total_undelivered": 0,
        "total_unprocessed": 0,
        "oldest_undelivered_age_s": 0.0,
        "max_rollup_lag_s": 0.0,
        "open_init_failures": 0,
        "locked_retry_count": 0,
        "rollback_allowed": True,
    }
    try:
        try:
            report["mode"] = router.mode()
        except RuntimeDBError:
            report["mode"] = "central"

        # locked-retry counter from the process manager when available (cheap
        # wire-up; absent in central / direct-DB tests).
        if process_manager is not None:
            getter = getattr(process_manager, "locked_retry_count", None)
            try:
                if callable(getter):
                    report["locked_retry_count"] = int(getter())
            except Exception:
                pass

        manifests = control.list_session_runtime_dbs()
        report["manifest_count"] = len(manifests)

        # Map rollup rows by session for lag reporting (no runtime open).
        rollups = {
            r.get("session_id"): r for r in control.list_runtime_usage_rollups()
        }

        known_paths: set[str] = set()
        now = time.time()
        max_lag = 0.0
        oldest_undelivered_age = 0.0

        for manifest in manifests:
            session_id = manifest.get("session_id")
            session_uid = manifest.get("session_uid")
            runtime_path = _safe_runtime_path(router, manifest)
            entry: Dict[str, Any] = {
                "session_id": session_id,
                "session_uid": session_uid,
                "status": manifest.get("status"),
                "file_present": False,
                "file_bytes": 0,
                "undelivered": 0,
                "unprocessed": 0,
                "queue_total": 0,
                "rollup_lag_s": float(
                    (rollups.get(session_id) or {}).get("rollup_lag_s") or 0
                ),
                "oldest_undelivered_age_s": 0.0,
            }
            if runtime_path:
                known_paths.add(os.path.abspath(runtime_path))
                if os.path.exists(runtime_path):
                    entry["file_present"] = True
                    report["on_disk_file_count"] += 1
                    try:
                        size = os.path.getsize(runtime_path)
                        for suffix in ("-wal", "-shm"):
                            sc = runtime_path + suffix
                            if os.path.exists(sc):
                                size += os.path.getsize(sc)
                        entry["file_bytes"] = size
                        report["total_runtime_bytes"] += size
                    except OSError:
                        pass
                    try:
                        rdb = AtlasDB(runtime_path, schema_set="runtime")
                        try:
                            depth = rdb.session_queue_depth(session_id)
                            entry["undelivered"] = depth["undelivered"]
                            entry["unprocessed"] = depth["unprocessed"]
                            entry["queue_total"] = depth["total"]
                            oldest = rdb._fetchone(
                                """
                                SELECT MIN(created_at) AS oldest
                                  FROM session_queue
                                 WHERE session_id = ? AND direction = 'out'
                                   AND delivered_at IS NULL
                                """,
                                (session_id,),
                            )
                            oldest_ts = (dict(oldest).get("oldest")
                                         if oldest is not None else None)
                            if oldest_ts:
                                age = max(0.0, now - float(oldest_ts))
                                entry["oldest_undelivered_age_s"] = age
                                oldest_undelivered_age = max(
                                    oldest_undelivered_age, age
                                )
                        finally:
                            rdb.close()
                    except sqlite3.DatabaseError:
                        entry["status"] = "error"
                        report["open_init_failures"] += 1
                else:
                    entry["status"] = entry["status"] or "missing"

            report["total_undelivered"] += int(entry["undelivered"])
            report["total_unprocessed"] += int(entry["unprocessed"])
            max_lag = max(max_lag, entry["rollup_lag_s"])
            report["sessions"].append(entry)

        report["max_rollup_lag_s"] = max_lag
        report["oldest_undelivered_age_s"] = oldest_undelivered_age
        # rollback_allowed = no session has in-flight queue work.
        report["rollback_allowed"] = all(
            int(s["queue_total"]) == 0 for s in report["sessions"]
        )

        # Orphan files: .db files physically under the root with NO manifest row.
        report["orphan_file_count"] = _count_orphan_runtime_files(
            router, known_paths
        )

        return report
    finally:
        try:
            control.close()
        except Exception:
            pass


def _count_orphan_runtime_files(
    router: AtlasDBRouter, known_paths: set
) -> int:
    """Count *.db files under the runtime root that no manifest row points to."""
    try:
        root = router.runtime_root()
    except RuntimeDBError:
        return 0
    root_path = os.path.abspath(root)
    if not os.path.isdir(root_path):
        return 0
    orphans = 0
    for dirpath, _dirs, files in os.walk(root_path):
        for name in files:
            if not name.endswith(".db"):
                continue
            full = os.path.abspath(os.path.join(dirpath, name))
            if full not in known_paths:
                orphans += 1
    return orphans
