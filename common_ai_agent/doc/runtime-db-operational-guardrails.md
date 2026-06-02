# Runtime-DB Operational Guardrails (Task 9)

Lifecycle, recovery, rollback, and observability for the per-session runtime-DB
split (`ATLAS_RUNTIME_DB_MODE=session`). Design background:
`doc/wiki/atlas-db-router-runtime-sharding-20260602.md`; plan §2.12 + R12/R13/R18/R25
in `plans/atlas-runtime-db-100-users-v2.md`. In `central` mode (default) every
function below is a no-op / behavior-preserving.

## Surfaces

- `core/atlas_db.py` — control-DB primitives:
  - `session_queue_depth(session_id)` → `{undelivered, unprocessed, rows_total, total}`.
  - `record_runtime_db_audit(...)` / `list_runtime_db_audit(...)` — append-only
    `runtime_db_audit` table (NEVER purged; outlives the deleted session).
  - `delete_runtime_db_manifest(session_id)` — atomic scrub of the
    `session_runtime_dbs` + `runtime_usage_rollups` + `runtime_rollup_offsets`
    rows in ONE transaction.
  - `delete_session(session_id, force=?, process_manager=?)` — control-table
    delete THEN routes through `runtime_rollup.delete_session_runtime`.
- `core/runtime_rollup.py` — router + filesystem operations:
  `delete_session_runtime`, `plan_session_recovery`, `recover_all_sessions`,
  `rollback_session_to_central`, `fleet_health`.
- `core/session_process_manager.py` — `recover_after_restart()`,
  `locked_retry_count()` (R25 metric), `_evict_db_handles()` (called before unlink).

## Session delete (R12)

`delete_session_runtime` (and the `AtlasDB.delete_session` entrypoint) in session mode:

1. resolve manifest → `session_uid` → **containment-checked** runtime path
   (recomputed from uid+root, never the stored path blindly — R23);
2. read queue depth (undelivered out-rows + unprocessed in-rows);
3. **GATE**: depth > 0 with `force=False` ⇒ **refuse** (`skipped_reason="queue_non_empty"`,
   nothing removed). `force=True` ⇒ delete AND write a `force_delete` audit row
   capturing the lost depth;
4. evict any cached runtime handle (`process_manager._evict_db_handles`);
5. remove `.db` + `-wal` + `-shm`;
6. atomically scrub manifest/rollup/offset rows.

Post-condition: ZERO orphan files, ZERO manifest/rollup/offset rows. A normal
(depth==0) delete still records a `delete` audit row.

## Restart recovery (R13)

`recover_after_restart()` → `recover_all_sessions()` builds one `RecoveryPlan`
per active/stale manifest session. The resume cursor is the **newest
already-delivered** out-row (`reseed_output_cursor`), NOT `latest_output_id`:
the next poll then replays exactly the still-undelivered rows after it with no
duplicate of delivered rows; `None` ⇒ replay from the top (nothing delivered).
Orphan worker PIDs are reconciled by matching **both** `--session-id` AND
`--db-path`.

**`_jobs`-loss policy** (`runtime_rollup.JOBS_LOSS_POLICY`): `_jobs` is volatile
main-process state with no DB backing. After a restart it is empty and is NOT
resurrected — the durable runtime `session_queue` + reseeded output cursor are
the source of truth, so undelivered output replays and in-flight prompts are
reconsumed by the (re)spawned worker.

## Forced rollback runtime → central (R18)

`rollback_session_to_central(session_id, require_workers_stopped=True)`:

- aborts if a live worker for the session is detected (PID scan on the runtime
  path) unless `require_workers_stopped=False` (tests only);
- copies UNDELIVERED `session_queue` rows into the control DB with
  `INSERT OR IGNORE` preserving the original TEXT id ⇒ **idempotent**
  (run-twice ⇒ one row);
- writes a `rollback` audit row.

**History policy** (`runtime_rollup.ROLLBACK_HISTORY_POLICY`): queue-only.
Historical runtime `messages`/`trace_events`/`llm_calls` are **left orphaned**
(NOT re-imported); control-mode history truncates at the rollback boundary. The
rollups already folded usage TOTALS into control, so accounting is preserved
even though per-row history is not.

## Fleet health / audit JSON (R25)

`runtime_rollup.fleet_health(process_manager=?)` returns the JSON the Task-10
harness consumes. Top-level keys: `mode`, `sessions[]`, `manifest_count`,
`on_disk_file_count`, `orphan_file_count`, `total_runtime_bytes`,
`total_undelivered`, `total_unprocessed`, `oldest_undelivered_age_s`,
`max_rollup_lag_s`, `open_init_failures`, `locked_retry_count`,
`rollback_allowed`. Each `sessions[]` entry: `session_id`, `session_uid`,
`status`, `file_present`, `file_bytes`, `undelivered`, `unprocessed`,
`queue_total`, `rollup_lag_s`, `oldest_undelivered_age_s`.

`rollback_allowed` is True iff every session's `queue_total == 0` (no in-flight
work — safe to flip back to central).

## Follow-up (out of Task-9 file scope)

R-Task6-carry: make the orchestrator router-routing failure observable —
`src/orchestrator/react_bridge.py::_runtime_db_for_session` currently
`except Exception: return control_db` (fail-soft, correct). A one-time
warning/metric should be emitted when the router raises and a session-scoped
write silently degrades to control, WITHOUT changing the fail-soft delivery.
Left unedited here because `src/orchestrator/react_bridge.py` is outside the
Task-9 file scope.

## Tests / evidence

`tests/test_runtime_guardrails_task9.py` (16 tests). Evidence:
`evidence/wave3-task9-{suite,delete,recovery,rollback,health}.txt`.
