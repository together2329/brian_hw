"""Session Flow read-model builder and historical backfill owner (Task 3).

This module turns the Task 1/2 Session-Flow tables into a single admin
read-model and owns the repeat-safe backfill that recomputes the
``session_flow_rollups`` and ``ip_flow_rollups`` tables.

Design invariants (mirrors the plan + mandatory review fixes):

* **DM-2 — state is recomputed, never summed.** A session rollup splits cleanly
  into *additive counters* (input/LLM/worker/artifact counts, tokens, cost) and
  *non-additive STATE* (``flow_state``, ``risk_level``, ``stale_age_s``,
  ``rollup_status``). Counters are SUMmed/aggregated from source rows; STATE is
  RECOMPUTED-from-latest off the control ``sessions`` row + MAX(timestamps).

* **RS-3 — ip_flow is a DERIVED aggregate of the per-session rollups.** IP rows
  are computed AFTER the session rollups by GROUP BY ip_id over the freshly
  written ``session_flow_rollups`` rows. IP additive totals are the SUM of their
  constituent session rollups; IP state is recomputed from the worst-case
  member + IP provenance.

* **Attribution honesty.** Unmatched LLM spend / unroutable session_ids are
  surfaced in ``attribution_gaps`` with ``confidence='missing'``. A gap NEVER
  becomes a fabricated session row, and we NEVER overwrite ``llm_calls.session_id``.
  High-cost unmatched gaps also appear as top-level ``needs_attention`` entries
  (category ``unmatched_cost``) so operators are not silently billed.

* **Privacy.** No raw prompt text leaves this module. Only counts/ids/hashes/
  reason-codes from the Task 1/2 sanitized tables are read or surfaced.

* **Runtime no-fanout.** In runtime mode ``build_session_flow_payload`` reads the
  control-side rollups ONLY (``list_session_flow_rollups`` /
  ``list_ip_flow_rollups``) and never opens a per-session runtime DB. In central
  /full mode it reads source tables directly to recompute.

* **Backfill repeat-safe.** The backfill relies on the Task 1 UNIQUE keys and the
  recompute-overwrite rollup upserts (NOT Python double-count scans), so calling
  it twice converges to the same numbers.

* **``conflict`` confidence** — defined in ``CONFIDENCE_LEVELS`` for schema
  completeness; conflict detection (e.g. ip/workflow disagreement across source
  tables) is deferred to a later task. No code path currently produces it;
  callers must not assume it appears in rollup rows from this module.
"""

from __future__ import annotations

import time
from typing import Any, Dict, List, Optional, Tuple


# ---------------------------------------------------------------------------
# Enums (kept as module constants so callers/tests can import the legal sets)
# ---------------------------------------------------------------------------

# Ordered most-incomplete -> most-complete; used only as a label vocabulary
# (the actual state is recomputed, not derived by ordinal arithmetic).
FLOW_STATES: Tuple[str, ...] = (
    "created",
    "input_received",
    "worker_started",
    "running",
    "artifact_produced",
    "verification_seen",
    "completed",
    "blocked",
    "failed",
    "stale",
    "abandoned",
)

RISK_LEVELS: Tuple[str, ...] = ("critical", "warning", "ok")

CONFIDENCE_LEVELS: Tuple[str, ...] = ("exact", "inferred", "missing", "conflict")

# Missing-reason vocabulary (bounded; never free prose).
MISSING_REASONS: Tuple[str, ...] = (
    "no_source_session",
    "no_worker_link",
    "no_ip_link",
    "no_workflow_link",
    "temporal_inferred",
    "namespace_inferred",
    "conflict",
)

# Stale thresholds (seconds).
_STALE_CRITICAL_S = 24 * 3600.0
_STALE_WARNING_S = 6 * 3600.0

# A single unmatched LLM call costing at/above this is treated as a critical,
# high-cost attribution gap (per the plan "high-cost unmatched attribution").
_HIGH_COST_GAP_USD = 1.0

# Terminal session statuses that close the flow (no open-failure risk).
_TERMINAL_OK = frozenset({"completed", "archived", "done"})

# Active/open session statuses that can go stale.
_ACTIVE_STATUSES = frozenset({"active", "running", "open", "in_progress"})

# Worker statuses we count as failed / active.
_WORKER_FAILED = frozenset({"failed", "error", "errored", "crashed"})
_WORKER_ACTIVE = frozenset({"running", "started", "active", "in_progress"})

_DEFAULT_LIMIT = 100
_MAX_LIMIT = 500

# Range window vocabulary (API review NIT). ``all`` disables windowing. The
# window is measured against a session rollup's last activity (updated_at, or
# now - stale_age_s as a fallback). Default 7d.
_RANGE_WINDOW_S: Dict[str, Optional[float]] = {
    "24h": 24 * 3600.0,
    "7d": 7 * 24 * 3600.0,
    "30d": 30 * 24 * 3600.0,
    "all": None,
}
_DEFAULT_RANGE = "7d"


def _range_cutoff(rng: str, now: float) -> Optional[float]:
    """Return the oldest-allowed ``updated_at`` for a range, or None for ``all``.

    Unknown range values fall back to the default window (never silently 'all').
    """
    window = _RANGE_WINDOW_S.get(rng, _RANGE_WINDOW_S[_DEFAULT_RANGE])
    if window is None:
        return None
    return now - window


def _rollup_last_activity(r: Dict[str, Any], now: float) -> float:
    """Best-effort last-activity epoch for a session rollup row.

    Prefers ``updated_at``; falls back to ``now - stale_age_s`` (the fold records
    stale_age_s as time-since-last-activity), then ``created_at``. Returns 0.0
    when nothing is known (treated as out-of-window for a finite range).
    """
    ts = _num(r.get("updated_at"))
    if ts > 0:
        return ts
    stale = _num(r.get("stale_age_s"))
    if stale > 0:
        return max(0.0, now - stale)
    return _num(r.get("created_at"))


# ---------------------------------------------------------------------------
# Small value helpers (no DB access)
# ---------------------------------------------------------------------------


def _text(value: Any) -> str:
    return str(value or "").strip()


def _num(value: Any) -> float:
    try:
        return float(value or 0)
    except (TypeError, ValueError):
        return 0.0


def _int(value: Any) -> int:
    try:
        return int(value or 0)
    except (TypeError, ValueError):
        return 0


def _runtime_mode_active() -> bool:
    """True when the per-session runtime split is active (read lazily).

    Lazy import keeps this module importable without the router and lets a live
    server / test flip be observed.
    """
    try:
        from core.runtime_rollup import runtime_mode_active

        return runtime_mode_active()
    except Exception:
        return False


def derive_attribution_confidence(
    *,
    has_input: bool,
    has_worker: bool,
    llm_attempts: int,
    has_artifact: bool,
    has_ip: bool,
    has_workflow: bool,
) -> Tuple[str, str, int]:
    """Single source-of-truth for attribution confidence + gap_count (MINOR-1).

    Called by BOTH the central ``_build_session_rollup_fields`` and the runtime
    ``_recompute_flow_state_fields`` so both modes emit the same tier for the same
    logical session state.  Returns ``(confidence, missing_reason, gap_count)``.

    Confidence ladder:
      * ``exact``    — session has source-linked activity AND has ip+workflow.
      * ``inferred`` — session has activity but is missing its ip or workflow link
                       (real-but-incompletely-attributed).
      * ``missing``  — session has never been touched by any source table.

    ``attribution_gap_count`` is non-zero for ``inferred``/``missing``/``conflict``
    — the API review open question answered: it signals that SOME provenance for
    this real session is uncertain.
    """
    touched = has_input or has_worker or llm_attempts > 0 or has_artifact
    if not touched:
        confidence, missing_reason = "missing", "no_source_session"
    elif not has_ip or not has_workflow:
        confidence = "inferred"
        missing_reason = "no_ip_link" if not has_ip else "no_workflow_link"
    else:
        confidence, missing_reason = "exact", ""

    gap_count = 1 if confidence in ("inferred", "missing", "conflict") else 0
    return confidence, missing_reason, gap_count


# ---------------------------------------------------------------------------
# STATE recomputation (DM-2: never summed)
# ---------------------------------------------------------------------------


def recompute_flow_state(
    session_row: Dict[str, Any],
    *,
    has_input: bool,
    worker_started: bool,
    worker_active: bool,
    worker_failed: bool,
    workflow_blocked: bool,
    has_artifact: bool,
    verification_seen: bool,
    stale_age_s: float,
) -> str:
    """Recompute a session's ``flow_state`` from latest control state.

    This is the DM-2 contract: the state is a *function of the latest snapshot*,
    never an accumulation. Source signals (counts above) describe presence, not
    sums to add together.
    """
    status = _text(session_row.get("status")).lower()
    explicit = _text(session_row.get("flow_state")).lower()

    if session_row.get("abandoned_at") or status == "abandoned":
        return "abandoned"
    if status in _TERMINAL_OK or session_row.get("completed_at") or explicit == "completed":
        return "completed"
    if worker_failed or explicit == "failed":
        return "failed"
    if workflow_blocked or status == "blocked" or explicit == "blocked":
        return "blocked"
    # An open session that has been idle past the warning bound is stale.
    if status in _ACTIVE_STATUSES and stale_age_s >= _STALE_WARNING_S:
        return "stale"
    if verification_seen:
        return "verification_seen"
    if has_artifact:
        return "artifact_produced"
    if worker_active:
        return "running"
    if worker_started:
        return "worker_started"
    if has_input:
        return "input_received"
    return "created"


def recompute_risk_level(
    *,
    flow_state: str,
    status: str,
    stale_age_s: float,
    worker_active: bool,
    worker_failed: bool,
    workflow_blocked: bool,
    queue_in: int,
    has_active_worker: bool,
    has_input: bool,
    has_worker: bool,
    has_artifact: bool,
    llm_cost: float,
    has_ip: bool,
    has_workflow: bool,
    pending_todos: int,
    recent_progress: bool,
) -> Tuple[str, str]:
    """Recompute ``risk_level`` (+ a bounded reason code) from latest state.

    Rules (in evaluation order):
      1. Terminal benign states (completed, abandoned) short-circuit to ok
         BEFORE warning checks so a completed session with no artifact or no IP
         is never mis-classified as warning. Only critical signals (blocked,
         failed, stale-active) can override a terminal state because those
         represent data-model contradictions that need operator attention.
      2. critical: stale active/running >24h, blocked workflow, failed worker,
         queue backlog with no active worker.
         NOTE: high-cost unmatched LLM spend is a FLEET-level gap, not a
         per-session signal — it is surfaced in attribution_gaps and
         needs_attention (category unmatched_cost) by the payload builder,
         never by marking an individual session critical.
      3. warning:  no worker after input, no artifact after LLM spend, missing
         IP/workflow, stale >6h, pending todos.
      4. ok:       recent progress or completed with no open failure.
    """
    status_l = _text(status).lower()
    active = status_l in _ACTIVE_STATUSES

    # --- critical signals that override even terminal states ---
    # (A completed session whose worker is still marked failed or workflow still
    # marked blocked is a data-model inconsistency worth flagging.)
    if workflow_blocked or flow_state == "blocked":
        return "critical", "workflow_blocked"
    if worker_failed or flow_state == "failed":
        return "critical", "worker_failed"

    # --- MAJOR-1: short-circuit benign terminal states before warning block ---
    # completed/abandoned sessions are ok unless they hit one of the critical
    # signals above (blocked/failed are genuine data-model errors).
    if flow_state in ("completed", "abandoned"):
        return "ok", flow_state

    # --- remaining critical rules (only meaningful for active/open sessions) ---
    if active and stale_age_s >= _STALE_CRITICAL_S:
        return "critical", "stale_gt_24h"
    if queue_in > 0 and not has_active_worker:
        return "critical", "queue_backlog_no_worker"

    # --- warning ---
    if has_input and not has_worker:
        return "warning", "no_worker_after_input"
    if llm_cost > 0 and not has_artifact:
        return "warning", "no_artifact_after_llm"
    if not has_ip or not has_workflow:
        return "warning", "missing_ip_or_workflow"
    if active and stale_age_s >= _STALE_WARNING_S:
        return "warning", "stale_gt_6h"
    if pending_todos > 0:
        return "warning", "pending_todos"

    # --- ok ---
    if recent_progress:
        return "ok", "recent_progress"
    return "ok", "ok"


# ---------------------------------------------------------------------------
# Source-table recompute (central / full mode)
# ---------------------------------------------------------------------------


def _table_exists(db, name: str) -> bool:
    row = db._fetchone(
        "SELECT 1 AS x FROM sqlite_master WHERE type='table' AND name = ?",
        (name,),
    )
    return bool(row)


def _collect_session_facts(db) -> Dict[str, Dict[str, Any]]:
    """Aggregate the additive counters + presence signals per session_id.

    Reads source tables in central/full mode ONLY. Returns a map keyed by the
    canonical ``sessions.id`` of partial fact dicts (counters + MAX timestamps +
    boolean presence signals). Sessions with no source row at all still get a
    bare entry so an empty session is classified as ``created``.
    """
    facts: Dict[str, Dict[str, Any]] = {}

    def _f(sid: str) -> Dict[str, Any]:
        if sid not in facts:
            facts[sid] = {
                "input_count": 0, "input_chars": 0, "input_tokens_est": 0,
                "llm_attempts": 0, "llm_success": 0, "llm_errors": 0,
                "tokens_input": 0, "tokens_output": 0, "tokens_reasoning": 0,
                "cost_usd": 0.0,
                "worker_runs": 0, "active_workers": 0, "failed_workers": 0,
                "artifact_count": 0, "queue_in": 0, "queue_out": 0,
                "workflow_runs": 0, "workflow_errors": 0,
                "pending_todos": 0,
                "last_input_at": None, "last_llm_at": None,
                "last_worker_at": None, "last_artifact_at": None,
                "last_event_at": None, "last_verification_at": None,
                "worker_started": False, "worker_active": False,
                "worker_failed": False, "workflow_blocked": False,
                "has_artifact": False, "verification_seen": False,
            }
        return facts[sid]

    # --- session_inputs (authoritative input counters) ---
    for r in db._fetchall(
        "SELECT session_id, COUNT(*) AS c, COALESCE(SUM(char_count),0) AS chars, "
        "COALESCE(SUM(token_estimate),0) AS toks, MAX(created_at) AS last_at "
        "FROM session_inputs GROUP BY session_id"
    ):
        sid = _text(r["session_id"])
        if not sid:
            continue
        f = _f(sid)
        f["input_count"] = _int(r["c"])
        f["input_chars"] = _int(r["chars"])
        f["input_tokens_est"] = _int(r["toks"])
        f["last_input_at"] = r["last_at"]

    # --- llm_calls (attempts/success/errors/tokens/cost) ---
    # MINOR-3: buckets are mutually exclusive. A row is an error when its status
    # is a failure code OR it has an error_type AND is not in a success status.
    # This prevents a row with status='ok' AND error_type set counting in both.
    for r in db._fetchall(
        "SELECT session_id, COUNT(*) AS attempts, "
        "SUM(CASE WHEN status IN ('ok','success','completed') THEN 1 ELSE 0 END) AS ok_c, "
        "SUM(CASE WHEN status IN ('error','failed','timeout') "
        "         OR (error_type IS NOT NULL AND status NOT IN ('ok','success','completed')) "
        "    THEN 1 ELSE 0 END) AS err_c, "
        "COALESCE(SUM(tokens_input),0) AS ti, COALESCE(SUM(tokens_output),0) AS to_, "
        "COALESCE(SUM(tokens_reasoning),0) AS tr, COALESCE(SUM(cost_usd),0) AS cost, "
        "MAX(created_at) AS last_at "
        "FROM llm_calls WHERE session_id IS NOT NULL AND session_id != '' "
        "GROUP BY session_id"
    ):
        sid = _text(r["session_id"])
        if not sid:
            continue
        f = _f(sid)
        f["llm_attempts"] = _int(r["attempts"])
        f["llm_success"] = _int(r["ok_c"])
        f["llm_errors"] = _int(r["err_c"])
        f["tokens_input"] = _int(r["ti"])
        f["tokens_output"] = _int(r["to_"])
        f["tokens_reasoning"] = _int(r["tr"])
        f["cost_usd"] = _num(r["cost"])
        f["last_llm_at"] = r["last_at"]

    # --- worker_runs (worker counters + status presence, single pass) ---
    if _table_exists(db, "worker_runs"):
        for r in db._fetchall(
            "SELECT session_id, COUNT(*) AS c, "
            "SUM(CASE WHEN status IN ('running','started','active','in_progress') THEN 1 ELSE 0 END) AS active_c, "
            "SUM(CASE WHEN status IN ('failed','error','errored','crashed') THEN 1 ELSE 0 END) AS failed_c, "
            "MAX(updated_at) AS last_at "
            "FROM worker_runs WHERE session_id IS NOT NULL AND session_id != '' "
            "GROUP BY session_id"
        ):
            sid = _text(r["session_id"])
            if not sid:
                continue
            f = _f(sid)
            f["worker_runs"] = _int(r["c"])
            f["active_workers"] = _int(r["active_c"])
            f["failed_workers"] = _int(r["failed_c"])
            f["last_worker_at"] = r["last_at"]
            f["worker_started"] = f["worker_runs"] > 0
            f["worker_active"] = f["active_workers"] > 0
            f["worker_failed"] = f["failed_workers"] > 0

    # --- workflow_runs (workflow counters + blocked signal) ---
    if _table_exists(db, "workflow_runs"):
        for r in db._fetchall(
            "SELECT session_id, COUNT(*) AS c, "
            "SUM(CASE WHEN status IN ('error','failed') THEN 1 ELSE 0 END) AS err_c, "
            "SUM(CASE WHEN status IN ('blocked','waiting') THEN 1 ELSE 0 END) AS blocked_c, "
            "MAX(updated_at) AS last_at "
            "FROM workflow_runs WHERE session_id IS NOT NULL AND session_id != '' "
            "GROUP BY session_id"
        ):
            sid = _text(r["session_id"])
            if not sid:
                continue
            f = _f(sid)
            f["workflow_runs"] = _int(r["c"])
            f["workflow_errors"] = _int(r["err_c"])
            if _int(r["blocked_c"]) > 0:
                f["workflow_blocked"] = True

    # --- artifact_versions (artifact counters) ---
    if _table_exists(db, "artifact_versions"):
        for r in db._fetchall(
            "SELECT source_session_id, COUNT(*) AS c, MAX(created_at) AS last_at "
            "FROM artifact_versions WHERE source_session_id IS NOT NULL "
            "AND source_session_id != '' GROUP BY source_session_id"
        ):
            sid = _text(r["source_session_id"])
            if not sid:
                continue
            f = _f(sid)
            f["artifact_count"] = _int(r["c"])
            f["last_artifact_at"] = r["last_at"]
            f["has_artifact"] = f["artifact_count"] > 0

    # --- session_queue (queue backlog) ---
    if _table_exists(db, "session_queue"):
        for r in db._fetchall(
            "SELECT session_id, "
            "SUM(CASE WHEN direction='in' AND processed_at IS NULL THEN 1 ELSE 0 END) AS in_c, "
            "SUM(CASE WHEN direction='out' AND delivered_at IS NULL THEN 1 ELSE 0 END) AS out_c "
            "FROM session_queue GROUP BY session_id"
        ):
            sid = _text(r["session_id"])
            if not sid:
                continue
            f = _f(sid)
            f["queue_in"] = _int(r["in_c"])
            f["queue_out"] = _int(r["out_c"])

    # --- session_flow_events (last event + verification signal) ---
    if _table_exists(db, "session_flow_events"):
        for r in db._fetchall(
            "SELECT session_id, MAX(created_at) AS last_at "
            "FROM session_flow_events WHERE session_id IS NOT NULL "
            "AND session_id != '' GROUP BY session_id"
        ):
            sid = _text(r["session_id"])
            if not sid:
                continue
            _f(sid)["last_event_at"] = r["last_at"]
        for r in db._fetchall(
            "SELECT DISTINCT session_id FROM session_flow_events "
            "WHERE event_type LIKE 'verification%' OR event_type LIKE '%verified%'"
        ):
            sid = _text(r["session_id"])
            if sid:
                f = _f(sid)
                f["verification_seen"] = True
                f["last_verification_at"] = f.get("last_event_at")

    # --- pending todos (linked via workflow_runs.id) ---
    if _table_exists(db, "workflow_todos") and _table_exists(db, "workflow_runs"):
        for r in db._fetchall(
            "SELECT wr.session_id AS session_id, COUNT(*) AS c "
            "FROM workflow_todos t JOIN workflow_runs wr ON wr.id = t.run_id "
            "WHERE t.status IN ('pending','open','in_progress','todo') "
            "AND wr.session_id IS NOT NULL AND wr.session_id != '' "
            "GROUP BY wr.session_id"
        ):
            sid = _text(r["session_id"])
            if sid:
                _f(sid)["pending_todos"] = _int(r["c"])

    return facts


def _attribution_gaps_from_llm(db, known_session_ids: set) -> Tuple[List[Dict[str, Any]], int]:
    """Unmatched LLM spend → attribution_gaps (confidence=missing).

    A session_id present in llm_calls but absent from ``sessions`` is unroutable.
    We surface it as a gap row (never a fabricated session) and NEVER write back
    to ``llm_calls.session_id``.
    """
    gaps: List[Dict[str, Any]] = []
    high_cost_session_ids: set = set()
    rows = db._fetchall(
        "SELECT session_id, COUNT(*) AS attempts, COALESCE(SUM(cost_usd),0) AS cost, "
        "COALESCE(SUM(tokens_input+tokens_output),0) AS tokens, MAX(created_at) AS last_at "
        "FROM llm_calls GROUP BY session_id"
    )
    for r in rows:
        sid = _text(r["session_id"])
        if sid and sid in known_session_ids:
            continue
        cost = _num(r["cost"])
        gap = {
            "session_id": sid or None,
            "kind": "unmatched_llm_spend" if sid else "null_session_llm_spend",
            "llm_attempts": _int(r["attempts"]),
            "cost_usd": cost,
            "tokens": _int(r["tokens"]),
            "last_at": r["last_at"],
            "confidence": "missing",
            "missing_reason": "no_source_session",
        }
        gaps.append(gap)
        if cost >= _HIGH_COST_GAP_USD and sid:
            high_cost_session_ids.add(sid)
    gaps.sort(key=lambda g: g["cost_usd"], reverse=True)
    return gaps, len(high_cost_session_ids)


# ---------------------------------------------------------------------------
# Rollup recompute (central / full mode) — writes both tables, repeat-safe
# ---------------------------------------------------------------------------


def recompute_rollups(db, *, now: Optional[float] = None) -> Dict[str, int]:
    """Recompute ``session_flow_rollups`` then derive ``ip_flow_rollups``.

    Returns a small stats dict. Repeat-safe: the per-session upsert OVERWRITES
    (recompute-from-latest), and the IP rollups are recomputed by GROUP BY over
    the freshly written session rollups (RS-3) — calling twice converges.
    """
    now = now if now is not None else time.time()

    sessions = {s["id"]: s for s in db.list_all_sessions()}
    known_ids = set(sessions.keys())
    facts = _collect_session_facts(db)

    gaps, _high_cost_gap_count = _attribution_gaps_from_llm(db, known_ids)

    n_sessions = 0
    for sid, srow in sessions.items():
        f = facts.get(sid) or _collect_empty_fact()
        rollup = _build_session_rollup_fields(srow, f, now=now)
        db.upsert_session_flow_rollup(sid, fields=rollup)
        n_sessions += 1

    # RS-3: derive IP rollups AFTER per-session rollups, by GROUP BY ip_id over
    # the freshly written session_flow_rollups rows.
    n_ip = _recompute_ip_rollups(db, sessions, now=now)
    return {"sessions": n_sessions, "ips": n_ip, "attribution_gaps": len(gaps)}


def _collect_empty_fact() -> Dict[str, Any]:
    return {
        "input_count": 0, "input_chars": 0, "input_tokens_est": 0,
        "llm_attempts": 0, "llm_success": 0, "llm_errors": 0,
        "tokens_input": 0, "tokens_output": 0, "tokens_reasoning": 0,
        "cost_usd": 0.0, "worker_runs": 0, "active_workers": 0,
        "failed_workers": 0, "artifact_count": 0, "queue_in": 0, "queue_out": 0,
        "workflow_runs": 0, "workflow_errors": 0, "pending_todos": 0,
        "last_input_at": None, "last_llm_at": None, "last_worker_at": None,
        "last_artifact_at": None, "last_event_at": None,
        "last_verification_at": None,
        "worker_started": False, "worker_active": False, "worker_failed": False,
        "workflow_blocked": False, "has_artifact": False,
        "verification_seen": False,
    }


def _build_session_rollup_fields(
    srow: Dict[str, Any],
    f: Dict[str, Any],
    *,
    now: float,
) -> Dict[str, Any]:
    """Build the upsert fields for one session rollup.

    Additive counters come straight from the source aggregate (summed). STATE
    (flow_state, risk_level, stale_age) is RECOMPUTED-from-latest (DM-2).
    """
    status = _text(srow.get("status")).lower()

    # Latest activity timestamp across every dimension (recompute, not sum).
    last_candidates = [
        srow.get("updated_at"), srow.get("last_flow_event_at"),
        f.get("last_input_at"), f.get("last_llm_at"),
        f.get("last_worker_at"), f.get("last_artifact_at"),
        f.get("last_event_at"),
    ]
    last_activity = max((c for c in last_candidates if c is not None), default=None)
    if last_activity is not None:
        stale_age_s = max(0.0, now - _num(last_activity))
    else:
        stale_age_s = max(0.0, now - _num(srow.get("created_at")))

    has_input = f["input_count"] > 0
    has_worker = f["worker_runs"] > 0
    has_artifact = f["has_artifact"]
    has_ip = bool(_text(srow.get("ip_id")) or _text(srow.get("ip")))
    has_workflow = bool(_text(srow.get("workflow")))

    flow_state = recompute_flow_state(
        srow,
        has_input=has_input,
        worker_started=f["worker_started"],
        worker_active=f["worker_active"],
        worker_failed=f["worker_failed"],
        workflow_blocked=f["workflow_blocked"],
        has_artifact=has_artifact,
        verification_seen=f["verification_seen"],
        stale_age_s=stale_age_s,
    )

    # "recent progress" = some activity within the warning window.
    recent_progress = stale_age_s < _STALE_WARNING_S and (
        has_input or has_worker or has_artifact or f["llm_attempts"] > 0
    )

    risk_level, risk_reason = recompute_risk_level(
        flow_state=flow_state,
        status=status,
        stale_age_s=stale_age_s,
        worker_active=f["worker_active"],
        worker_failed=f["worker_failed"],
        workflow_blocked=f["workflow_blocked"],
        queue_in=f["queue_in"],
        has_active_worker=f["worker_active"],
        has_input=has_input,
        has_worker=has_worker,
        has_artifact=has_artifact,
        llm_cost=f["cost_usd"],
        has_ip=has_ip,
        has_workflow=has_workflow,
        pending_todos=f["pending_todos"],
        recent_progress=recent_progress,
    )

    # MINOR-1: shared helper (runtime fold also calls this so both modes agree).
    confidence, missing_reason, attribution_gap_count = derive_attribution_confidence(
        has_input=has_input, has_worker=has_worker,
        llm_attempts=f["llm_attempts"], has_artifact=has_artifact,
        has_ip=has_ip, has_workflow=has_workflow,
    )

    # MINOR-2: risk_reason is kept as a separate field distinct from
    # missing_reason so the operational cause (e.g. queue_backlog_no_worker)
    # is never masked by the attribution reason.
    return {
        "session_uid": srow.get("session_uid"),
        "user_id": srow.get("user_id"),
        "workspace_id": srow.get("workspace_id"),
        "ip_id": srow.get("ip_id"),
        "ip": srow.get("ip"),
        "workflow": srow.get("workflow"),
        # additive counters
        "input_count": f["input_count"],
        "input_chars": f["input_chars"],
        "input_tokens_est": f["input_tokens_est"],
        "llm_attempts": f["llm_attempts"],
        "llm_success": f["llm_success"],
        "llm_errors": f["llm_errors"],
        "tokens_input": f["tokens_input"],
        "tokens_output": f["tokens_output"],
        "tokens_reasoning": f["tokens_reasoning"],
        "cost_usd": f["cost_usd"],
        "worker_runs": f["worker_runs"],
        "active_workers": f["active_workers"],
        "failed_workers": f["failed_workers"],
        "workflow_runs": f["workflow_runs"],
        "workflow_errors": f["workflow_errors"],
        "artifact_count": f["artifact_count"],
        "queue_in": f["queue_in"],
        "queue_out": f["queue_out"],
        "attribution_gap_count": attribution_gap_count,
        # recomputed STATE (never summed)
        "flow_state": flow_state,
        "risk_level": risk_level,
        "stale_age_s": stale_age_s,
        "attribution_confidence": confidence,
        # missing_reason: attribution gap cause (kept separate from risk_reason)
        "missing_reason": missing_reason,
        "rollup_status": "ok",
        "rollup_lag_s": 0.0,
    }


def _recompute_ip_rollups(db, sessions: Dict[str, Dict[str, Any]], *, now: float) -> int:
    """RS-3: derive ip_flow_rollups from the per-session rollups (GROUP BY ip_id).

    Additive IP totals are the SUM of constituent session rollups. IP STATE
    (risk_level, provenance) is recomputed from the worst member + ip_blocks
    provenance — never summed.
    """
    session_rollups = db.list_session_flow_rollups()

    groups: Dict[str, List[Dict[str, Any]]] = {}
    for r in session_rollups:
        ip_id = _text(r.get("ip_id"))
        if not ip_id:
            continue
        groups.setdefault(ip_id, []).append(r)

    # IP provenance (exact when ip_blocks carries it; inferred from earliest
    # session link otherwise; missing as last resort).
    ip_meta: Dict[str, Dict[str, Any]] = {}
    if _table_exists(db, "ip_blocks"):
        for r in db._fetchall(
            "SELECT id, workspace_id, ip_name, created_by_user_id, "
            "source_session_id, source_type, source_confidence, created_at "
            "FROM ip_blocks"
        ):
            ip_meta[_text(r["id"])] = dict(r)

    n = 0
    for ip_id, members in groups.items():
        meta = ip_meta.get(ip_id, {})
        # Additive totals = SUM of session rollups (RS-3).
        sessions_n = len(members)
        active_n = sum(1 for m in members
                       if _text(m.get("flow_state")) in ("running", "worker_started",
                                                          "input_received"))
        worker_runs = sum(_int(m.get("worker_runs")) for m in members)
        artifact_count = sum(_int(m.get("artifact_count")) for m in members)
        llm_attempts = sum(_int(m.get("llm_attempts")) for m in members)
        cost_usd = sum(_num(m.get("cost_usd")) for m in members)
        workflows = len({_text(m.get("workflow")) for m in members if _text(m.get("workflow"))})
        problem_count = sum(1 for m in members
                            if _text(m.get("risk_level")) in ("critical", "warning"))

        # Recomputed STATE: worst member risk.
        if any(_text(m.get("risk_level")) == "critical" for m in members):
            ip_risk = "critical"
        elif any(_text(m.get("risk_level")) == "warning" for m in members):
            ip_risk = "warning"
        else:
            ip_risk = "ok"

        # Provenance: exact from ip_blocks; else inferred from earliest exact
        # session link; else missing.
        src_conf = _text(meta.get("source_confidence"))
        src_session = _text(meta.get("source_session_id"))
        created_by = _text(meta.get("created_by_user_id"))
        source_type = _text(meta.get("source_type"))
        if src_conf in CONFIDENCE_LEVELS and (src_session or created_by):
            provenance_conf = src_conf
        elif src_session or created_by:
            provenance_conf = "inferred"
        else:
            # Infer from the earliest session linked to this IP, if any.
            linked = [m for m in members if _text(m.get("user_id"))]
            if linked:
                provenance_conf = "inferred"
                created_by = created_by or _text(linked[0].get("user_id"))
            else:
                provenance_conf = "missing"

        db.upsert_ip_flow_rollup(ip_id, fields={
            "workspace_id": meta.get("workspace_id") or (members[0].get("workspace_id")),
            "ip": meta.get("ip_name") or (members[0].get("ip")),
            "created_by_user_id": created_by or None,
            "source_session_id": src_session or None,
            "source_type": source_type or None,
            "source_confidence": provenance_conf,
            "ip_created_at": meta.get("created_at"),
            "risk_level": ip_risk,
            "sessions": sessions_n,
            "active_sessions": active_n,
            "workflows": workflows,
            "worker_runs": worker_runs,
            "artifact_count": artifact_count,
            "llm_attempts": llm_attempts,
            "cost_usd": cost_usd,
            "problem_count": problem_count,
            "rollup_status": "ok",
            "rollup_lag_s": 0.0,
        })
        n += 1
    return n


# Backfill is just a (re)compute of the rollups from whatever authoritative +
# historical source rows exist. It is repeat-safe by construction (Task 1 UNIQUE
# keys + recompute-overwrite upserts), so it is an alias for recompute_rollups.
def backfill_session_flow(db, *, now: Optional[float] = None) -> Dict[str, int]:
    """Repeat-safe historical backfill.

    Future rows stay authoritative (Task 2 already wrote them). Historical rows
    are folded by the same recompute that reads source tables in priority order
    (session_inputs first, then session_queue/trace/messages via the source
    aggregate; llm_calls for spend with unmatched ids → attribution_gaps; IP
    provenance from ip_blocks/earliest link). Calling twice converges because the
    rollup upserts OVERWRITE rather than accumulate.
    """
    return recompute_rollups(db, now=now)


# ---------------------------------------------------------------------------
# Payload projection (rows from the recomputed rollups; privacy-safe)
# ---------------------------------------------------------------------------


def _derive_risk_reason(r: Dict[str, Any]) -> str:
    """Derive a bounded risk-reason code from stored rollup fields.

    MINOR-2: risk_reason is a separate field from missing_reason so the
    operational cause (e.g. queue_backlog_no_worker) is never masked by
    the attribution gap reason (e.g. no_source_session).
    """
    flow_state = _text(r.get("flow_state"))
    risk_level = _text(r.get("risk_level"))
    if risk_level == "ok":
        return flow_state if flow_state in ("completed", "abandoned") else "ok"
    stale_age_s = _num(r.get("stale_age_s"))
    if flow_state == "blocked":
        return "workflow_blocked"
    if flow_state == "failed" or _int(r.get("failed_workers")) > 0:
        return "worker_failed"
    if stale_age_s >= _STALE_CRITICAL_S and risk_level == "critical":
        return "stale_gt_24h"
    if _int(r.get("queue_in")) > 0 and _int(r.get("active_workers")) == 0:
        return "queue_backlog_no_worker"
    if stale_age_s >= _STALE_WARNING_S and risk_level == "warning":
        return "stale_gt_6h"
    return _text(r.get("missing_reason")) or risk_level


# Bounded next-action vocabulary keyed by the operational risk_reason code.
# C2: the UI (Task 6) renders ONE next_action per session and it must come from
# this single source (never recomputed in the route). The map is keyed on the
# risk_reason produced by _derive_risk_reason so API and UI agree exactly.
_NEXT_ACTION_BY_REASON: Dict[str, str] = {
    "workflow_blocked": "resolve block",
    "worker_failed": "inspect failed/empty run",
    "stale_gt_24h": "inspect or close",
    "queue_backlog_no_worker": "assign/restart worker",
    "no_worker_after_input": "assign/restart worker",
    "no_artifact_after_llm": "inspect failed/empty run",
    "missing_ip_or_workflow": "link IP/workflow",
    "stale_gt_6h": "inspect or close",
    "pending_todos": "resolve pending todos",
}


def _derive_next_action(risk_level: str, flow_state: str, risk_reason: str) -> str:
    """Derive a bounded operator next-action from risk_level + flow_state + risk_reason.

    C2: ok sessions get an empty action; critical/warning sessions get a short,
    bounded directive. Lives here (not in the route) so the API and UI (Task 6)
    share ONE source of truth.
    """
    if _text(risk_level) == "ok":
        return ""
    reason = _text(risk_reason)
    action = _NEXT_ACTION_BY_REASON.get(reason)
    if action:
        return action
    # Fallback by flow_state for any reason code not explicitly mapped.
    state = _text(flow_state)
    if state == "blocked":
        return "resolve block"
    if state == "failed":
        return "inspect failed/empty run"
    if state == "stale":
        return "inspect or close"
    return "review session"


def _session_row_from_rollup(r: Dict[str, Any], session_meta: Dict[str, Any]) -> Dict[str, Any]:
    sid = _text(r.get("session_id"))
    meta = session_meta.get(sid, {})
    risk_reason = _derive_risk_reason(r)
    return {
        "session_id": sid,
        "session_uid": r.get("session_uid") or meta.get("session_uid"),
        "namespace": meta.get("namespace"),
        "title": meta.get("title"),
        "user_id": r.get("user_id") or meta.get("user_id"),
        "username": meta.get("username"),
        "ip_id": r.get("ip_id"),
        "ip": r.get("ip") or meta.get("ip"),
        "workflow": r.get("workflow"),
        "flow_state": r.get("flow_state"),
        "risk_level": r.get("risk_level"),
        # MINOR-2: risk_reason is the operational cause, distinct from
        # missing_reason (the attribution gap cause).
        "risk_reason": risk_reason,
        # C2: bounded operator directive derived from risk_level + flow_state +
        # risk_reason. Computed here (single source) so the route never recomputes it.
        "next_action": _derive_next_action(
            _text(r.get("risk_level")), _text(r.get("flow_state")), risk_reason
        ),
        "input_count": _int(r.get("input_count")),
        "input_chars": _int(r.get("input_chars")),
        "input_tokens_est": _int(r.get("input_tokens_est")),
        "llm_attempts": _int(r.get("llm_attempts")),
        "llm_success": _int(r.get("llm_success")),
        "llm_errors": _int(r.get("llm_errors")),
        "tokens_input": _int(r.get("tokens_input")),
        "tokens_output": _int(r.get("tokens_output")),
        "tokens_reasoning": _int(r.get("tokens_reasoning")),
        "cost_usd": _num(r.get("cost_usd")),
        "worker_runs": _int(r.get("worker_runs")),
        "active_workers": _int(r.get("active_workers")),
        "failed_workers": _int(r.get("failed_workers")),
        "workflow_runs": _int(r.get("workflow_runs")),
        "workflow_errors": _int(r.get("workflow_errors")),
        "artifact_count": _int(r.get("artifact_count")),
        "stale_age_s": _num(r.get("stale_age_s")),
        "attribution_confidence": r.get("attribution_confidence"),
        "missing_reason": r.get("missing_reason"),
        "created_at": r.get("created_at"),
        "updated_at": r.get("updated_at"),
    }


def _ip_row_from_rollup(r: Dict[str, Any]) -> Dict[str, Any]:
    return {
        "ip_id": _text(r.get("ip_id")),
        "ip": r.get("ip"),
        "workspace_id": r.get("workspace_id"),
        "created_by_user_id": r.get("created_by_user_id"),
        "source_session_id": r.get("source_session_id"),
        "source_type": r.get("source_type"),
        "source_confidence": r.get("source_confidence"),
        "ip_created_at": r.get("ip_created_at"),
        "risk_level": r.get("risk_level"),
        "sessions": _int(r.get("sessions")),
        "active_sessions": _int(r.get("active_sessions")),
        "workflows": _int(r.get("workflows")),
        "worker_runs": _int(r.get("worker_runs")),
        "artifact_count": _int(r.get("artifact_count")),
        "llm_attempts": _int(r.get("llm_attempts")),
        "cost_usd": _num(r.get("cost_usd")),
        "problem_count": _int(r.get("problem_count")),
        "updated_at": r.get("updated_at"),
    }


def _session_meta_map(db) -> Dict[str, Dict[str, Any]]:
    """Cheap join of sessions->users for display fields (control tables only)."""
    if not _table_exists(db, "sessions"):
        return {}
    meta: Dict[str, Dict[str, Any]] = {}
    rows = db._fetchall(
        "SELECT s.id AS id, s.session_uid, s.namespace, s.title, s.user_id, "
        "s.ip, s.ip_id, u.username AS username "
        "FROM sessions s LEFT JOIN users u ON u.id = s.user_id"
    )
    for r in rows:
        meta[_text(r["id"])] = dict(r)
    return meta


def build_session_flow_payload(db, filters: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
    """Build the admin Session Flow read-model payload.

    Runtime mode: reads control-side rollups ONLY (no per-session runtime fanout).
    Central/full mode: recomputes the rollups from source tables first, then reads
    them back (so a fresh read always reflects current source state).
    """
    filters = dict(filters or {})
    now = time.time()
    runtime_mode = _runtime_mode_active()

    risk = _text(filters.get("risk")) or "all"
    lens = _text(filters.get("lens")) or "team_lead"
    rng = _text(filters.get("range")) or _DEFAULT_RANGE
    if rng not in _RANGE_WINDOW_S:
        rng = _DEFAULT_RANGE
    range_cutoff = _range_cutoff(rng, now)
    limit = filters.get("limit")
    try:
        limit = int(limit) if limit is not None else _DEFAULT_LIMIT
    except (TypeError, ValueError):
        limit = _DEFAULT_LIMIT
    limit = max(1, min(limit, _MAX_LIMIT))
    try:
        offset = max(0, int(filters.get("offset") or 0))
    except (TypeError, ValueError):
        offset = 0

    ip_id_f = _text(filters.get("ip_id")) or None
    workflow_f = _text(filters.get("workflow")) or None
    user_id_f = _text(filters.get("user_id")) or None
    session_id_f = _text(filters.get("session_id")) or None

    attribution_gaps: List[Dict[str, Any]] = []

    # MINOR-2: build the SQL filter kwargs used for both list and count calls.
    # Filters pushed into SQL so the DB engine bounds work before Python sees rows.
    _sql_kw: Dict[str, Any] = {}
    if ip_id_f:
        _sql_kw["ip_id"] = ip_id_f
    if workflow_f:
        _sql_kw["workflow"] = workflow_f
    if user_id_f:
        _sql_kw["user_id"] = user_id_f
    if risk != "all":
        _sql_kw["risk_level"] = risk
    if range_cutoff is not None:
        _sql_kw["updated_at_min"] = range_cutoff

    if runtime_mode:
        # No fanout: read the control-side rollups the runtime fold (Task 7)
        # maintains. Source tables / runtime files are NOT opened here.
        #
        # For summary/funnel/needs_attention we need all matching rows (no page
        # limit). For the page we use LIMIT/OFFSET. total_sessions uses COUNT.
        all_rollups = db.list_session_flow_rollups(**_sql_kw)
        ip_rollups = db.list_ip_flow_rollups()
        session_meta = _session_meta_map(db)
        # Gaps that were persisted into the rollups surface as a count; the
        # detailed per-call gap list requires source reads which runtime mode
        # avoids, so we summarize from the rollup counters.
        gap_count = sum(_int(r.get("attribution_gap_count")) for r in all_rollups)
        if gap_count:
            attribution_gaps.append({
                "kind": "unmatched_llm_spend",
                "count": gap_count,
                "confidence": "missing",
                "missing_reason": "no_source_session",
            })
    else:
        # Central/full: recompute from source, then read back.
        recompute_rollups(db, now=now)
        all_rollups = db.list_session_flow_rollups(**_sql_kw)
        ip_rollups = db.list_ip_flow_rollups()
        session_meta = _session_meta_map(db)
        known_ids = set(session_meta.keys()) or {r.get("session_id") for r in all_rollups}
        attribution_gaps, _ = _attribution_gaps_from_llm(db, set(known_ids))

    # session_id point-filter is not pushed to SQL (rare; keep Python-side).
    if session_id_f:
        all_rollups = [r for r in all_rollups
                       if _text(r.get("session_id")) == session_id_f]

    # Project all matching rows (needed for summary/funnel/needs_attention).
    sessions_out: List[Dict[str, Any]] = [
        _session_row_from_rollup(r, session_meta) for r in all_rollups
    ]

    # SQL ORDER BY already sorts by risk/cost; Python sort kept as a tie-break
    # only when session_id filter changed the set (cheap on a single row).
    # For the normal path the SQL order is authoritative.
    total_sessions = len(sessions_out)

    # MINOR-2: page is a Python slice of sessions_out. The full filtered set is
    # intentionally fetched from SQL (no LIMIT in the DB query) so that
    # summary/funnel/needs_attention aggregate over ALL matching rows, not just
    # the current page. SQL pushes down WHERE filters + ORDER BY (risk-sort) for
    # efficiency; the page boundary is applied here in Python.
    page = sessions_out[offset:offset + limit]

    ip_out = [_ip_row_from_rollup(r) for r in ip_rollups]
    if ip_id_f:
        ip_out = [r for r in ip_out if r["ip_id"] == ip_id_f]
    _risk_rank = {"critical": 0, "warning": 1, "ok": 2}
    ip_out.sort(key=lambda r: (_risk_rank.get(_text(r.get("risk_level")), 3),
                               -_num(r.get("cost_usd"))))

    # Session-level needs_attention: sessions with critical or warning risk.
    needs_attention: List[Any] = [
        s for s in sessions_out
        if _text(s.get("risk_level")) in ("critical", "warning")
    ]
    # MAJOR-2(b): high-cost unmatched spend is a FLEET-level gap, not a
    # per-session signal. Surface it as a top-level needs_attention entry
    # with category 'unmatched_cost' so operators are not silently billed.
    # It also stays in attribution_gaps and summary.unmatched_cost_usd.
    high_cost_gaps = [g for g in attribution_gaps if _num(g.get("cost_usd")) >= _HIGH_COST_GAP_USD]
    if high_cost_gaps:
        total_unmatched_cost = sum(_num(g.get("cost_usd")) for g in high_cost_gaps)
        needs_attention.append({
            "category": "unmatched_cost",
            "kind": "unmatched_llm_spend",
            "gap_count": len(high_cost_gaps),
            "cost_usd": total_unmatched_cost,
            "confidence": "missing",
            "missing_reason": "no_source_session",
        })

    summary = _summary(sessions_out, ip_out, attribution_gaps)
    funnel = _funnel(sessions_out)

    return {
        "generated_at": now,
        "runtime_mode": runtime_mode,
        "range": rng,
        "lens": lens,
        "summary": summary,
        "lenses": {
            "builder": "attribution + write-path health",
            "team_lead": "operational blockers + ownership",
            "executive": "adoption + spend + output + risk",
        },
        "needs_attention": needs_attention,
        "funnel": funnel,
        "sessions": page,
        "ip_flow": ip_out,
        "attribution_gaps": attribution_gaps,
        "limits": {
            "limit": limit,
            "offset": offset,
            "max_limit": _MAX_LIMIT,
            "total_sessions": total_sessions,
            "returned": len(page),
        },
    }


def _summary(sessions: List[Dict[str, Any]], ips: List[Dict[str, Any]],
             gaps: List[Dict[str, Any]]) -> Dict[str, Any]:
    critical = sum(1 for s in sessions if _text(s.get("risk_level")) == "critical")
    warning = sum(1 for s in sessions if _text(s.get("risk_level")) == "warning")
    ok = sum(1 for s in sessions if _text(s.get("risk_level")) == "ok")
    return {
        "session_count": len(sessions),
        "critical": critical,
        "warning": warning,
        "ok": ok,
        "ip_count": len(ips),
        "total_cost_usd": round(sum(_num(s.get("cost_usd")) for s in sessions), 6),
        "total_llm_attempts": sum(_int(s.get("llm_attempts")) for s in sessions),
        "total_artifacts": sum(_int(s.get("artifact_count")) for s in sessions),
        "total_inputs": sum(_int(s.get("input_count")) for s in sessions),
        "attribution_gap_count": len(gaps),
        "unmatched_cost_usd": round(sum(_num(g.get("cost_usd")) for g in gaps), 6),
    }


def _funnel(sessions: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Return per-stage tallies for the session funnel.

    MINOR-4: each ``count`` is an INDEPENDENT per-stage tally of how many
    sessions have reached that stage, NOT a strict monotonic drop-off funnel.
    A session can appear in ``worker`` without appearing in ``input`` if inputs
    were never recorded (e.g. a headless job). Task 6 must render these as
    independent bars/counts, not assume count[n] <= count[n-1].

    Stages: Created -> Input -> Worker -> LLM -> Artifact -> Verified -> Completed.
    """
    created = len(sessions)
    with_input = sum(1 for s in sessions if _int(s.get("input_count")) > 0)
    with_worker = sum(1 for s in sessions if _int(s.get("worker_runs")) > 0)
    with_llm = sum(1 for s in sessions if _int(s.get("llm_attempts")) > 0)
    with_artifact = sum(1 for s in sessions if _int(s.get("artifact_count")) > 0)
    verified = sum(1 for s in sessions
                   if _text(s.get("flow_state")) in ("verification_seen", "completed"))
    completed = sum(1 for s in sessions if _text(s.get("flow_state")) == "completed")
    return [
        {"stage": "created", "count": created},
        {"stage": "input", "count": with_input},
        {"stage": "worker", "count": with_worker},
        {"stage": "llm", "count": with_llm},
        {"stage": "artifact", "count": with_artifact},
        {"stage": "verified", "count": verified},
        {"stage": "completed", "count": completed},
    ]
