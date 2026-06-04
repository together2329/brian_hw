---
title: Session Flow Dashboard
type: operations
tags: [atlas, admin, dashboard, session-flow, attribution, rollup, runtime]
updated: 2026-06-04
related: [admin-operational-dashboard-db-snapshot-20260603, atlas-db-router-runtime-sharding-20260602, atlas-single-active-orchestrator-subworkers-20260603]
---

# Session Flow Dashboard - 2026-06-04

This page documents the **Session Flow** admin tab: what it measures, how to
interpret each metric, the confidence model for historical data, and the
runtime no-fanout design that keeps it safe at 100+ concurrent users.

## Primary Unit: Session

**Session is the primary observability unit.** A session groups every
user input, worker run, LLM call, artifact, queue message, todo, and trace
event that occurred in one execution context. The Session Flow dashboard asks:

```text
Which sessions need action today? How did each session actually flow?
```

This is a separate concern from the existing admin **Flow** tab, which shows
the todo/task-flow view per workflow run. The two tabs coexist and serve
different questions:

| Tab | Question | Source |
|---|---|---|
| **Session Flow** (new) | End-to-end session health, cost, attribution | `session_flow_rollups`, `ip_flow_rollups`, `session_flow_events` |
| **Flow** (existing) | Todo-flow per workflow run | workflow todo/queue state |

Do not rename or remove the existing Flow tab. The new Session Flow tab is
registered at `GET /api/admin/session-flow` in both `src/atlas_admin.py`
(standalone admin server) and `src/atlas_ui.py` (main UI server).

## Metric Definitions

All counts and amounts in the dashboard are derived from the read-model built
by `core/session_flow_usage.py:build_session_flow_payload`. Field names below
match the API response shape exactly.

### Input Count (`input_count`, `input_chars`, `input_tokens_est`)

The number of distinct user-originated input events recorded in the
`session_inputs` table for this session. Each row represents one inbound
prompt or answer message, captured at enqueue time.

- `input_count`: number of `session_inputs` rows linked to this session.
- `input_chars`: sum of `char_count` across those rows.
- `input_tokens_est`: sum of `token_estimate` across those rows.

**No raw prompt text is stored or surfaced.** Only counts, character counts,
token estimates, and hashes are kept. For sessions predating the Task 2
write-path instrumentation, `input_count` may be `0` with
`attribution_confidence='missing'` — this means no authoritative record
exists, not that no input was received.

### LLM Attempts, Success, Errors (`llm_attempts`, `llm_success`, `llm_errors`)

Aggregated from `llm_calls` rows linked to this session.

- `llm_attempts`: total rows in `llm_calls` for this session (includes
  retries, failures, and successes).
- `llm_success`: rows whose `status` is `ok`, `success`, or `completed`.
- `llm_errors`: rows whose `status` is `error`, `failed`, or `timeout`, OR
  where `error_type` is set and the row is not in a success status.

**`llm_success` and `llm_errors` are mutually exclusive.** A single call row
counts in at most one of the two buckets; the remaining calls (e.g. in-flight
or unknown status) are neither success nor error. The sum
`llm_success + llm_errors <= llm_attempts`.

### Cost (`cost_usd`)

Sum of `llm_calls.cost_usd` for all calls linked to this session. This is
direct cost from the LLM provider accounting, not an estimate.

### Worker Run (`worker_runs`, `active_workers`, `failed_workers`)

Counts from the `worker_runs` table. A worker run row is created when a
workflow job, headless worker, or interactive worker starts.

- `worker_runs`: total run rows for this session.
- `active_workers`: runs in `running`, `started`, `active`, or `in_progress`
  status at the time of the last rollup.
- `failed_workers`: runs in `failed`, `error`, `errored`, or `crashed` status.

### Flow State (`flow_state`)

The **recomputed** lifecycle stage of the session. It is a function of the
latest control state (DM-2: never accumulated by summing events). Legal values:

| `flow_state` | Meaning |
|---|---|
| `created` | Session exists; no input, worker, or artifact recorded yet |
| `input_received` | At least one `session_inputs` row exists |
| `worker_started` | At least one `worker_runs` row exists |
| `running` | A worker is currently active |
| `artifact_produced` | At least one artifact version linked to this session |
| `verification_seen` | A verification-type flow event has been recorded |
| `completed` | Session reached a terminal success state |
| `blocked` | Workflow is in a blocked/waiting state |
| `failed` | A worker run ended in failure |
| `stale` | Session is open/active but has had no activity for > 6 hours |
| `abandoned` | Session was explicitly abandoned |

`flow_state` is recomputed on every rollup pass and represents the latest
known state. It is not an append-only log; reading it tells you the current
lifecycle position, not the full history.

### Risk Level (`risk_level`)

A three-value operational signal recomputed from the session's latest state:

| `risk_level` | Operator semantics |
|---|---|
| `critical` | **Inspect today.** The session has a blocker, active failure, or stale running state over 24 hours. Examples: `workflow_blocked`, `worker_failed`, `stale_gt_24h`, `queue_backlog_no_worker`. |
| `warning` | **Follow up / incomplete flow.** Something is missing or degraded but not an immediate blocker. Examples: `no_worker_after_input`, `no_artifact_after_llm`, `missing_ip_or_workflow`, `stale_gt_6h`, `pending_todos`. |
| `ok` | **No known action required.** Recent progress or completed with no open failure. |

The `next_action` field in each session row carries a bounded, human-readable
directive (e.g. `"resolve block"`, `"inspect failed/empty run"`,
`"assign/restart worker"`) derived from `risk_level` + `flow_state` +
`risk_reason`. It is pre-computed by the read-model and does not change
between API calls unless the underlying rollup changes.

### Attribution Confidence (`attribution_confidence`)

Indicates how reliably the session's metrics can be traced back to first-party
source rows. The confidence is **per-session**, not per-metric.

| `attribution_confidence` | Meaning |
|---|---|
| `exact` | Direct source-table linkage: `session_inputs`, `worker_runs`, or `llm_calls` carry this session's ID |
| `inferred` | Derived from temporal proximity, namespace matching, or earliest-linked record; not from a direct foreign key |
| `missing` | No defensible source row found for this session |
| `conflict` | **Defined in the schema but not yet produced.** Multiple incompatible source assignments were detected; deferred to a later task. Do not assume any current rollup row carries this value. |

**Confidence is not truth.** An `inferred` session may have correct counts
or incorrect counts depending on whether the temporal/namespace join was
accurate. Treat `inferred` metrics as directionally useful, not
audit-grade. Treat `missing` as a data gap that requires investigation before
acting on the numbers.

The `missing_reason` field records a bounded code explaining why confidence
is not `exact` (e.g. `no_source_session`, `no_worker_link`, `temporal_inferred`,
`namespace_inferred`).

## Attribution Gaps (`attribution_gaps`)

LLM calls whose `session_id` does not match any row in the `sessions` table
are surfaced as **attribution gaps**, never fabricated as a session row.

Each gap entry contains:
- `kind`: `unmatched_llm_spend` (session_id present but unresolvable) or
  `null_session_llm_spend` (session_id was empty/null).
- `llm_attempts`, `cost_usd`, `tokens`: aggregated totals for this unmatched
  group.
- `confidence`: always `missing`.
- `missing_reason`: always `no_source_session`.

High-cost gaps (single unmatched group >= $1.00) are also promoted to the
`needs_attention` list with `category='unmatched_cost'` so operators are not
silently billed. The underlying `llm_calls.session_id` values are **never
overwritten** regardless of attribution analysis results.

## Stakeholder Lenses

The three lenses are **client-side display filters only** — they do not cause
a refetch unless filter values also change. The API returns the full payload
and the UI suppresses or highlights fields based on the selected lens.

### Builder Lens (`lens=builder`)

Target: engineer or system owner investigating write-path health.

Shows: `attribution_confidence`, `missing_reason`, gap counts, raw IDs
(`session_id`, `ip_id`, `worker_runs` table IDs), rollup staleness
(`rollup_status`, `rollup_lag_s`), flow event gaps, route source. Designed for
diagnosing attribution problems and validating instrumentation coverage.

### Team Lead Lens (`lens=team_lead`) — default

Target: engineering lead triaging active work.

Shows: blocked and stale sessions, `owner`/`username`, `ip`, `workflow`,
worker status (`active_workers`, `failed_workers`), `next_action`. Focuses on
operational blockers and ownership rather than data-model internals.

### Executive Lens (`lens=executive`)

Target: engineering manager or product owner reviewing adoption and cost.

Shows: adoption counts, `cost_usd`, `artifact_count`, risk counts, trend
summaries from the `summary` block. Raw IDs are hidden by default. Designed
for high-level health assessment without system internals.

## Runtime No-Fanout Design

At 100+ concurrent users, Atlas can run in **session runtime DB mode** where
each active session has its own SQLite file for write isolation. A naive admin
read that opened all runtime files per request would add O(N) file opens per
admin page load.

The Session Flow dashboard avoids this entirely through a two-tier design:

### Out-of-Band Fold Scheduler

A background thread (`core/runtime_rollup.py:start_rollup_scheduler`) runs
`run_rollup_pass` on a configurable interval. Each pass calls
`rollup_all_active_flow`, which for each active session:

1. Opens the per-session runtime DB once.
2. Reads new rows from `session_inputs`, `worker_runs`, `session_flow_events`,
   `llm_calls`, and `session_queue` using a monotonic high-water offset
   (prefix `flow:<table>`, stored in `runtime_rollup_offsets`).
3. Folds additive counters (input counts, worker counts, LLM attempts/cost)
   into the control-DB `session_flow_rollups` row for that session.
4. Recomputes non-additive STATE (`flow_state`, `risk_level`,
   `attribution_confidence`) from the latest control snapshot.
5. Advances the high-water offset atomically with the fold so a crash between
   steps cannot double-count.

The flow fold uses the `flow:` prefix so its offsets are isolated from the
existing usage fold offsets and the two never clobber each other.

### Admin Read Path

When `build_session_flow_payload` detects runtime mode (via
`runtime_mode_active()`), it reads **only** the control-DB rollup tables
(`list_session_flow_rollups`, `list_ip_flow_rollups`) and **never opens** a
per-session runtime DB file. The 100-user admin read therefore has a fixed,
small I/O cost independent of how many active runtime sessions exist.

### Freshness and Staleness

The fold scheduler interval is controlled by:
- `ATLAS_FLOW_ROLLUP_INTERVAL_S` (default: 30 seconds)
- `ATLAS_FLOW_ROLLUP_ENABLE` (default: enabled when runtime mode is active)

A session whose runtime DB has not been folded since the last pass has a
non-zero `rollup_lag_s` and a `rollup_status` of `stale`. The dashboard
surfaces stale sessions visibly rather than returning empty or silently
under-counted data. A `stale` rollup means the numbers are from the last
successful fold, not from the current instant; it does not mean the session
has no data.

If a runtime DB file is missing (e.g. the worker process has not yet created
it), the rollup row is marked `rollup_status='stale'` with a lag derived from
the manifest's `updated_at`. The session still appears in the dashboard with
its last-known state.

### Central / Full Mode

When runtime mode is not active (the default single-DB mode), the read path
calls `recompute_rollups` directly before projecting the payload. This
recomputes every session rollup from the live source tables
(`session_inputs`, `worker_runs`, `llm_calls`, etc.) and then reads back the
freshly written rows. No fold scheduler is needed in central mode.

## Historical Attribution Limitations

The Task 2 write-path instrumentation is authoritative for sessions created
after it was deployed. For older sessions:

- `session_inputs` may have `0` rows even if user input happened (it was not
  recorded before Task 2). The backfill (`backfill_session_flow`) attempts a
  best-effort reconstruction using `session_queue` direction-`in` rows and
  `trace_events` user-chat rows, but these are labeled `inferred`, not `exact`.
- LLM attribution for pre-instrumentation sessions relies on `llm_calls.session_id`
  matching `sessions.id`. Calls with missing or unresolvable session IDs become
  `attribution_gaps` with `confidence='missing'`.
- IP provenance (`created_by_user_id`, `source_session_id`, `source_type`) is
  read from `ip_blocks` provenance columns when present. When absent, the earliest
  session linked to the IP is used with `source_confidence='inferred'`. When no
  session link exists, it is `missing`.
- Worker activity before `worker_runs` was populated may be inferred from
  `workflow_runs` records with `attribution_confidence='inferred'`.

The backfill is repeat-safe: calling it multiple times converges to the same
result because rollup upserts overwrite (recompute-from-latest) rather than
accumulate. It never mutates `llm_calls`, `trace_events`, or `session_queue`
source rows.

**Do not treat `inferred` numbers as audit-grade.** They reflect the best
available reconstruction of historical state, not direct measurement.

## DB Tables

| Table | Location | Purpose |
|---|---|---|
| `session_inputs` | control + runtime | Authoritative input capture (no raw text) |
| `worker_runs` | control + runtime | First-class worker lifecycle ledger |
| `session_flow_events` | control + runtime | Append-only lineage events |
| `session_flow_rollups` | control only | One row per session; pre-aggregated for fast reads |
| `ip_flow_rollups` | control only | One row per IP; derived from session rollups |

## API Response Shape

`GET /api/admin/session-flow` returns:

```json
{
  "generated_at": <unix epoch float>,
  "runtime_mode": <bool>,
  "range": "7d",
  "lens": "team_lead",
  "summary": {
    "session_count": <int>,
    "critical": <int>,
    "warning": <int>,
    "ok": <int>,
    "ip_count": <int>,
    "total_cost_usd": <float>,
    "total_llm_attempts": <int>,
    "total_artifacts": <int>,
    "total_inputs": <int>,
    "attribution_gap_count": <int>,
    "unmatched_cost_usd": <float>
  },
  "needs_attention": [...],
  "funnel": [
    {"stage": "created", "count": <int>},
    {"stage": "input", "count": <int>},
    {"stage": "worker", "count": <int>},
    {"stage": "llm", "count": <int>},
    {"stage": "artifact", "count": <int>},
    {"stage": "verified", "count": <int>},
    {"stage": "completed", "count": <int>}
  ],
  "sessions": [
    {
      "session_id": "...", "session_uid": "...", "namespace": "...",
      "title": "...", "user_id": "...", "username": "...",
      "ip_id": "...", "ip": "...", "workflow": "...",
      "flow_state": "...", "risk_level": "...", "risk_reason": "...",
      "next_action": "...",
      "input_count": <int>, "input_chars": <int>, "input_tokens_est": <int>,
      "llm_attempts": <int>, "llm_success": <int>, "llm_errors": <int>,
      "tokens_input": <int>, "tokens_output": <int>, "tokens_reasoning": <int>,
      "cost_usd": <float>,
      "worker_runs": <int>, "active_workers": <int>, "failed_workers": <int>,
      "workflow_runs": <int>, "workflow_errors": <int>,
      "artifact_count": <int>,
      "stale_age_s": <float>,
      "attribution_confidence": "exact|inferred|missing",
      "missing_reason": "...",
      "created_at": "...", "updated_at": "..."
    }
  ],
  "ip_flow": [...],
  "attribution_gaps": [...],
  "limits": {
    "limit": 100, "offset": 0, "max_limit": 500,
    "total_sessions": <int>, "returned": <int>
  }
}
```

Query parameters: `range=24h|7d|30d|all` (default `7d`),
`lens=builder|team_lead|executive` (default `team_lead`),
`risk=all|critical|warning|ok` (default `all`), `ip_id`, `workflow`,
`user_id`, `session_id` (optional exact filters), `limit` (default 100,
max 500), `offset` (default 0).

The funnel stages are **independent per-stage counts**, not a strict
monotonic drop-off. A session can appear in `worker` without appearing in
`input` if inputs were never recorded (e.g. a headless job). Render these as
independent bars or counts; do not assume `count[n] <= count[n-1]`.

## Operator Quick Reference

| Signal | What to do |
|---|---|
| `risk_level='critical'` | Inspect today. Check `next_action` for the specific directive. |
| `risk_level='warning'` | Follow up. Incomplete flow or degraded state; not blocking today but requires attention. |
| `risk_level='ok'` | No known action required. |
| `attribution_confidence='inferred'` | Numbers are directionally useful but not audit-grade. |
| `attribution_confidence='missing'` | No defensible source record. Data gap; do not act on these numbers without manual investigation. |
| `attribution_confidence='conflict'` | Not produced yet (deferred). If seen in a future release, it means multiple incompatible source assignments were detected. |
| `rollup_status='stale'` | The last fold pass did not complete for this session. Numbers reflect the prior fold. Check `rollup_lag_s`. |
| High `cost_usd` in `attribution_gaps` | Unattributed LLM spend. Check the `unmatched_cost` entry in `needs_attention`. |

## Privacy Contract

The Session Flow dashboard **never exposes raw prompt text**. The tables it
reads (`session_inputs`, `session_flow_rollups`, `ip_flow_rollups`) contain
only counts, character counts, token estimates, hashes, status codes, and
timestamps. The API payload and the three UI lenses all inherit this constraint.

## Related

- [[admin-operational-dashboard-db-snapshot-20260603]] — prior admin
  dashboard priorities from the real local DB snapshot; Session Flow addresses
  the unattributed cost and stale session gaps identified there.
- [[atlas-db-router-runtime-sharding-20260602]] — runtime DB sharding design
  that motivates the no-fanout rollup architecture.
- [[atlas-single-active-orchestrator-subworkers-20260603]] — single active
  session worker policy that Session Flow's `active_workers` count reflects.
