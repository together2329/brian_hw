---
title: Atlas DB Router Runtime Sharding
type: architecture
tags: [atlas, db, sqlite, multi-user, worker-ipc, session-queue, runtime-db]
updated: 2026-06-03
related: [multi-user-worker-isolation, multi-user-worker-conflicts, db-concurrent-write-race-20260519, atlas-pipeline-db-state, provider-and-llm-call-accounting]
---

# Atlas DB Router Runtime Sharding - 2026-06-02

This page records the concept for making Atlas DB ownership safer under
multi-user and multi-worker use.

> STATUS (2026-06-03): IMPLEMENTED on branch `feat/runtime-db-100users` behind
> `ATLAS_RUNTIME_DB_MODE=session` (default `central` = byte-identical to before).
> `core/atlas_db_router.py` + per-session runtime DBs + rollups + lifecycle
> guardrails + a 100-session SLA harness shipped. The four review-feedback items
> below were all resolved — see "Feedback Resolution" at the end.

## Problem

Today Atlas effectively has one default SQLite path:

```text
ATLAS_DB_PATH or ~/.common_ai_agent/atlas.db
```

That single DB currently holds both low-frequency control data and high-frequency
runtime data:

```text
control-ish:
  users / auth / workspaces / ip_blocks / ip_permissions

runtime-ish:
  session_queue / messages / parts / trace_events / llm_calls
```

The ownership problem and the bottleneck problem are different:

- Ownership needs one authority for user, workspace, IP block, and ACL decisions.
- Runtime write load needs to avoid forcing all sessions through one SQLite writer.

The hot path is not "many users" by itself. The hot path is prompt input,
worker IPC, messages, trace events, and LLM usage records all writing through
the same SQLite file and writer queue.

## Recommendation

Use one Control DB plus session/run-scoped Runtime DBs.

```text
atlas_control.db
  users
  auth
  workspaces
  ip_blocks
  ip_permissions
  db_manifest
  session registry

runtime/<user_id>/<session_uid>.db
  session_queue
  messages
  parts
  trace_events
  llm_calls
  worker IPC state
```

This is better than immediately choosing "DB per user" or "DB per IP":

- DB per user still serializes multiple active sessions from the same user.
- DB per IP still serializes collaborators and workers attached to the same IP.
- DB per session/run isolates the actual high-write workload.
- Control DB remains the single place to answer ownership and permission
  questions.

## Safe First Step

Do not split the DB first. Add a router first.

```text
AtlasDBRouter
  control_db_path() -> current atlas.db
  runtime_db_path(session_uid) -> current atlas.db
```

Phase 1 should have no behavior change:

- Add `AtlasDBRouter`.
- Keep every route pointing at the current central `ATLAS_DB_PATH`.
- Make `SessionProcessManager` ask the router for the DB path instead of
  resolving it directly.
- Store or derive `runtime_db_path`, but initially set it to the same central DB.
- Verify existing input, history, worker, and admin usage tests still pass.

This creates a switch without turning it on.

## Migration Order

1. Router-only, central DB fallback.
2. Route only `session_queue` to the Runtime DB for process workers.
3. Move `messages` and `parts` after prompt delivery is stable.
4. Move `trace_events` and `llm_calls` after admin aggregation is ready.
5. Add optional IP DBs only if shared IP artifacts and workflow state become
   too large or too write-heavy for the Control DB.

The important ordering is `session_queue` first. It is the prompt-delivery and
worker-IPC bottleneck, and it is easiest to verify directly.

## Verification Contract

The concept is testable with visible DB state.

Router-only checks:

- Existing tests pass with all routes pointing to central DB.
- Worker environment receives the router-selected DB path.
- Input accepted behavior does not change.
- Admin usage and history still read the same data.

Runtime `session_queue` checks:

- Prompt submit creates a `session_queue` row in the selected Runtime DB.
- The Control DB does not receive that queue row.
- Worker dequeue reads from the same Runtime DB.
- A dead worker returns failed delivery and does not persist a dropped prompt.
- Switching the router back to central restores current behavior without schema
  migration.

Load checks:

- Create multiple sessions.
- Submit prompts concurrently.
- Confirm each session's queue rows land in its selected Runtime DB.
- Track enqueue latency and `database is locked` failures before and after.

## Implementation Review Feedback - 2026-06-03

After reviewing the `feat/runtime-db-100users` implementation, the split is
directionally right but is not yet enough to count as a clean 100-active-user
SQLite proof. Treat these as fix-before-scale items.

1. Hot poll path still writes the Control DB.

   `_MultiUserBridge._poll_process_outputs` iterates every active session,
   `SessionProcessManager.poll_output` calls `_get_runtime_db`, and
   `_get_runtime_db` resolves the path with `create=True`. That causes
   `AtlasDBRouter.runtime_route(... create=True)` to upsert
   `session_runtime_dbs` on every poll pass. At 100 active sessions, this
   reintroduces a central write queue even though queue rows are sharded.

   Required fix: memoize `session_uid -> runtime_db_path` and use a read-only
   or no-refresh resolution path for poll, reseed, and latest-output reads.
   Manifest upsert should happen only on activation, spawn, or first create.

   Verification: repeated `poll_output()` calls must not change
   `session_runtime_dbs.updated_at` or increment a Control DB write counter.

2. Delete gate is ordered incorrectly.

   `AtlasDB.delete_session` deletes Control DB rows before
   `delete_session_runtime` checks runtime queue depth. If the runtime queue is
   non-empty, runtime deletion skips but the control session is already gone,
   leaving the runtime manifest/file orphaned while API responses can still say
   `deleted=true`.

   Required fix: run the runtime queue-depth gate before deleting Control DB
   rows. Return a force-required response when `queue_non_empty`; delete the
   control session only after runtime cleanup succeeds or a central/no-manifest
   path is confirmed.

   Verification: with a pending prompt, non-force delete must leave both the
   control session and runtime file intact and return non-deleted/409.

3. Delivered marking must use the same order as polling.

   Polling uses `(created_at, rowid)` but marking delivered uses
   `rowid <= up_to_rowid`. A backward wall-clock step can mark rows that were
   not delivered yet.

   Required fix: fetch the cursor boundary as `(created_at, rowid)` and mark
   delivered with a matching tuple predicate.

   Verification: insert output rows with `rowid=1, created_at=100` and
   `rowid=2, created_at=90`; after polling the first visible row, marking
   delivered must not mark `rowid=1`.

4. Coalescing timer is not a live streaming timer yet.

   The 50 ms timer is only checked while the worker waits for input;
   `emit_content` does not check it during LLM streaming. Long same-type token
   streams can flush only at 4 KB, event boundary, or stream end.

   Required fix: call timer flush from the emit/add path or add a real periodic
   flush loop.

   Verification: use a fake monotonic clock through `SessionWorker.emit_content`
   and assert a small token stream flushes after the interval without manually
   calling `batcher.maybe_flush_timer()`.

Task 10 should add a steady-state assertion that Control DB writes remain zero
while active sessions are being polled. Queue placement and latency checks are
necessary but not sufficient for the 100-user claim.

## Feedback Resolution - 2026-06-03

All four items above are resolved on `feat/runtime-db-100users` (each fix is
regression-proven: reverting the fix makes its new test fail).

1. **Hot poll path control write — FIXED.** `SessionProcessManager._runtime_path_cache`
   memoizes `session_id -> runtime_db_path`; a warm `poll_output()` resolves from
   the cache and never calls `runtime_route(create=True)`, so `session_runtime_dbs`
   is no longer upserted per poll (upsert happens only on activation / first
   resolve). Proof: a steady-state test asserts `session_runtime_dbs.updated_at`
   does not change and control-DB upsert writes == 0 across many broadcaster
   passes (teeth-checked: forcing re-resolve per poll makes it fail).
2. **Delete gate ordering — FIXED.** `AtlasDB.delete_session` now runs the runtime
   queue-depth gate (`delete_session_runtime`) BEFORE deleting any control row. A
   non-empty runtime queue with `force=False` aborts the control delete and
   returns `{deleted:False, runtime:{skipped_reason:'queue_non_empty',
   force_required:True}}` so the API can surface 409; `force=True` removes both +
   writes an audit row. Central mode unchanged.
3. **Delivered-marking order — FIXED.** `mark_outputs_delivered` resolves
   `up_to_id` to its `(created_at, rowid)` boundary and marks with the matching
   tuple predicate `delivered_at IS NULL AND (created_at < :c OR (created_at = :c
   AND rowid <= :r))`, consistent with the `(created_at, rowid)` poll order — a
   backward wall-clock step no longer marks an undelivered row.
4. **Live streaming flush — FIXED.** `_OutputBatcher._add` checks the monotonic
   clock on the emit/add path and flushes the open buffer once `>= 50ms` has
   elapsed since its first chunk, so a long same-type token stream flushes mid-
   stream (not only at 4KB / event boundary / stream end). Uses the injectable
   `monotonic_fn` seam.

Tests: `tests/test_runtime_delete_and_delivery_order.py` (#2, #3),
`tests/test_output_coalescing.py` (#4 live timer),
`tests/test_runtime_db_100_user_scale.py` (#1 steady-state zero control writes).

## Policy

Accepted input should always be durable.

Process mode already uses `session_queue`. In-process mode currently can fall
back to memory inbox behavior; if this architecture is adopted, the long-term
policy should be:

```text
accepted prompt -> persisted queue/event -> worker consumes
```

In-memory inbox should be treated as a development fallback, not the product
contract.

## Risks

- Admin usage becomes a fanout/aggregation problem once runtime records leave
  the Control DB.
- SQLite has no simple cross-DB transaction story; avoid designs that require
  atomic writes across Control DB and Runtime DB.
- Runtime DB paths must be generated from stable IDs, not user-provided paths.
- Session identity should use stable user/session/IP IDs, not parsed display
  strings.

## Decision Summary

Best direction:

```text
Do not immediately split by user.
Do not immediately split by IP.
Add DB routing first.
Then move session_queue to session/run Runtime DBs.
Keep ownership and ACL in one Control DB.
```

This gives rollback safety while targeting the real bottleneck.

Related pages: [[multi-user-worker-isolation]], [[multi-user-worker-conflicts]],
[[db-concurrent-write-race-20260519]], [[atlas-pipeline-db-state]],
[[provider-and-llm-call-accounting]].
