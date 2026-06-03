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

## Feedback Resolution Review - 2026-06-03

Current review of `feat/runtime-db-100users` shows real progress, but not a full
pass yet. Items #3 and #4 are fixed. Items #1 and #2 remain partial. The #2 gap
has narrowed: the user delete endpoint now propagates the runtime gate, but the
admin delete paths and runtime cleanup exception path still need closing.

1. **Hot poll path control write - PARTIAL.** `SessionProcessManager._runtime_path_cache`
   memoizes `session_id -> runtime_db_path`; a warm `poll_output()` resolves from
   the cache and does not call `runtime_route(create=True)`, so the steady-state
   fanout test now proves `session_runtime_dbs.updated_at` stays flat after
   warm-up.

   Remaining gap: the read paths still default to `create=True` on a cold cache.
   A fresh `SessionProcessManager.poll_output(session_id)` can call
   `runtime_db_path(... create=True)`, upsert `session_runtime_dbs`, and change
   `updated_at`. The same `_get_runtime_db()` path is used by `poll_output`,
   `reseed_output_cursor`, and `latest_output_id`. The existing negative control
   also demonstrates this by clearing `_runtime_path_cache` and observing fresh
   `upsert_session_runtime_db` calls.

   Required fix: hot/read-only paths should resolve with `create=False` or use a
   path cached at activation/spawn time. Manifest upsert should remain limited to
   activation, spawn, explicit create, or first runtime materialization.

   Verification: add a cold-manager read-path test asserting first
   `poll_output()`, `reseed_output_cursor()`, and `latest_output_id()` do not call
   `upsert_session_runtime_db` and do not move `session_runtime_dbs.updated_at`.

2. **Delete gate/API propagation - PARTIAL.** `AtlasDB.delete_session` now runs
   `delete_session_runtime` before deleting control rows, and the direct core
   pending-queue test correctly returns `deleted=False` with
   `runtime.force_required=True`. `DELETE /api/sessions/{id}` also now threads
   `force`, returns the full delete result, and maps a pending runtime queue to
   HTTP 409.

   Remaining gap 1: admin delete endpoints still discard the return value and
   always return `{"deleted": true}`. Affected call sites:
   `src/atlas_admin.py` and `src/atlas_ui.py`.

   Remaining gap 2: if `delete_session_runtime()` raises, `AtlasDB.delete_session`
   catches the exception and proceeds to delete control rows anyway, leaving the
   manifest/runtime file orphaned. Runtime cleanup errors should block control
   delete unless central mode or no manifest/no runtime file is proven.

   Required fix: propagate `deleted=False` / `runtime.force_required` through the
   admin delete APIs as a non-deleted response, preferably HTTP 409 for pending
   runtime queue. Treat runtime cleanup errors as delete failure, not permission
   to delete control rows.

   Verification: keep the user API pending-queue delete test, add admin
   pending-queue delete tests for both admin route modules, plus a direct
   `delete_session_runtime()` exception test proving the control session remains
   intact.

3. **Delivered-marking order - FIXED.** `mark_outputs_delivered` resolves
   `up_to_id` to its `(created_at, rowid)` boundary and marks with the matching
   tuple predicate `delivered_at IS NULL AND (created_at < :c OR (created_at = :c
   AND rowid <= :r))`, consistent with the `(created_at, rowid)` poll order — a
   backward wall-clock step no longer marks an undelivered row.

4. **Live streaming flush - FIXED.** `_OutputBatcher._add` checks the monotonic
   clock on the emit/add path and flushes the open buffer once `>= 50ms` has
   elapsed since its first chunk, so a long same-type token stream flushes mid-
   stream (not only at 4KB / event boundary / stream end). Uses the injectable
   `monotonic_fn` seam.

Review verification:

- `tests/test_runtime_delete_and_delivery_order.py`,
  `tests/test_output_coalescing.py`, `tests/test_runtime_db_100_user_scale.py`,
  and `tests/test_e2e_api.py` pass together: `33 passed, 1 skipped`.
- The passing `tests/test_e2e_api.py` coverage includes the user
  `DELETE /api/sessions/{id}` pending-queue HTTP 409 case.
- Static review still finds non-propagating admin delete paths in
  `src/atlas_admin.py` and `src/atlas_ui.py`, and
  `AtlasDB.delete_session` still treats a `delete_session_runtime()` exception as
  permission to continue with control-row deletion.

### Follow-up Resolution - 2026-06-03 (#1 and #2 now CLOSED)

The two PARTIAL items above were completed (each fix regression-proven; the broad
central+session suites stay green — 134 touched-surface + 202 central/DB tests).

- **#1 hot poll write — CLOSED.** The hot READ paths now resolve with
  `create=False`: `SessionProcessManager.poll_output` / `reseed_output_cursor` /
  `latest_output_id` call `_get_runtime_db(session_id, create=False)`, so a
  COLD-cache first read never calls `runtime_route(create=True)` and never upserts
  `session_runtime_dbs` (defense in depth on top of `_runtime_path_cache`). A
  session with no manifest yet reads empty (no crash, no upsert). Manifest upsert
  is now limited to the write/activation path (`send_input`, `create=True`).
  Tests: `test_router_feedback_followups.py::test_cold_manager_read_paths_do_not_upsert_manifest`
  (+ no-manifest-empty); the Task-10 steady-state teeth was upgraded to force a
  `create=True` read so it stays load-bearing.
- **#2 delete gate — CLOSED.**
  - Gap1 (API propagation): `src/atlas_admin.py` and `src/atlas_ui.py` admin
    delete endpoints now use `force_delete_requested` + `session_delete_response`
    (mirroring the user endpoint), so a pending runtime queue returns **409 /
    deleted=False** instead of a misleading `200 {"deleted": true}`.
  - Gap2 (exception swallow): `AtlasDB.delete_session` deletes control rows ONLY
    when the runtime side left nothing to orphan (runtime `deleted` OR
    `skipped_reason in {central_mode, no_manifest}`); a `delete_session_runtime()`
    EXCEPTION (or `queue_non_empty`) now BLOCKS the control delete and preserves
    the session. `session_delete_response` maps the outcome to honest codes
    (200 deleted / 409 force-required / 500 runtime error).
  Tests: `test_router_feedback_followups.py::test_runtime_cleanup_error_blocks_control_delete`,
  `::test_session_delete_response_status_codes`.
- Finding B (`core/session_manager.py:1108`) is N/A: that path uses
  `SessionStorage` (thread mode), not `AtlasDB` — no per-session runtime DB to
  orphan.

Status: all four review items (#1–#4) are now FIXED.

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
