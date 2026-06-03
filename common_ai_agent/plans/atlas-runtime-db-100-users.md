# Atlas Runtime DB Refactor for 100 Active Users

## TL;DR
> **Summary**: Keep SQLite, but stop treating one `atlas.db` as the live runtime bus. Add a router, split hot runtime traffic into per-session SQLite files, batch live output writes, remove process-wide DB serialization, and read admin usage through rollups.
> **Deliverables**:
> - `AtlasDBRouter` with control/runtime routing and a control DB runtime manifest.
> - Session queue input/output routed to per-session runtime SQLite DBs.
> - Output coalescing for live LLM token/reasoning streams.
> - `AtlasDB` locks keyed by resolved DB path.
> - Runtime persistence routing for `messages`, `trace_events`, and `llm_calls`.
> - Control DB usage rollups for admin/dashboard reads.
> - Automated verification including 100-session synthetic load.
> **Effort**: Large
> **Parallel**: YES - 4 waves
> **Critical Path**: Task 1 -> Task 3 -> Task 4 -> Task 7 -> Task 10

## Context
### Original Request
The user asked for a 100-user plan and verification plan for DB splitting and DB read/write coverage.

### Interview Summary
- Target scale is 50-100 active users/workers while keeping SQLite.
- Current `session_queue` is not just persistence; it is live IPC between the main UI server and worker subprocesses.
- LLM output streaming can write many `session_queue(direction='out')` rows.
- DB splitting alone is not enough because `AtlasDB._WRITE_LOCK` currently serializes all DB paths inside a process.
- Admin/dashboard reads must not fan out across all runtime DBs during normal requests.

### Metis Review (gaps addressed)
- Defined the exact 100-user workload and thresholds.
- Chose per-session runtime SQLite files as the SQLite scale model.
- Chose `session_uid` for runtime DB path generation, while hot tables keep `session_id` columns for local query compatibility.
- Chose 50ms / 4KB output batching for mergeable stream events only.
- Chose db-path-scoped locks and rollup freshness target of <= 10 seconds under normal load.
- Added rollback, corrupt runtime DB, cross-DB transaction, retention, and observability requirements.

## Work Objectives
### Core Objective
Support 100 active session namespaces using SQLite without central `atlas.db` write contention on live IPC, LLM output streaming, runtime traces, or worker accounting.

### Deliverables
- Runtime DB router and manifest.
- Per-session `session_queue` routing.
- Runtime DB mode flag with central-mode fallback.
- Output event coalescing.
- Runtime DB writes for runtime tables.
- Rollup-backed admin/dashboard reads.
- Automated 100-session load verification.

### Definition of Done (verifiable conditions with commands)
- `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions.py tests/test_atlas_input_deep_runtime.py tests/test_atlas_db_concurrent_writers.py tests/test_atlas_multiuser_session_scope.py tests/test_react_loop_worker_llm_call_persist.py -q` passes.
- New runtime-router tests prove `session_queue` rows for two sessions land in two different runtime DBs and not in the control DB when runtime mode is enabled.
- New coalescing tests prove 1,000 token emits create <= 30 queue rows while preserving output text order.
- New rollup tests prove admin usage reads control rollup rows and does not directly query all runtime DBs on request.
- New synthetic load command proves 100 sessions can enqueue/poll simulated stream output with p95 enqueue latency <= 250ms, p95 poll latency <= 500ms, zero lost prompts, and zero `database is locked` failures.

### Must Have
- Router-first behavior-preserving phase.
- Backward-compatible central mode.
- Runtime paths derived from stable generated IDs, not raw usernames/IP/workflow strings.
- No cross-DB transaction assumptions.
- Per-session queue ordering preserved.
- Ask-user, lifecycle, stop/interrupt, file-change, and error events must not be coalesced.

### Must NOT Have
- No Postgres, Redis, NATS, or Kafka migration in this plan.
- No 1500-user architecture work.
- No token-by-token runtime DB write path after coalescing is enabled.
- No admin endpoint that scans every runtime DB on normal page load.
- No raw user input in runtime DB filenames.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after with focused pytest coverage, plus synthetic load tests. Existing test infrastructure uses pytest; frontend session routing uses vitest under `frontend/atlas`.
- QA policy: Every task has agent-executed scenarios.
- Evidence: write command output and measured JSON/CSV artifacts under `evidence/`.

## Execution Strategy
### Parallel Execution Waves
Wave 1: Tasks 1, 2, 3 establish router, locks, and manager/worker contracts.
Wave 2: Tasks 4, 5, 6 route queue and runtime writes, then reduce output write rate.
Wave 3: Tasks 7, 8, 9 fix reads, rollups, cleanup, and observability.
Wave 4: Task 10 load harness and final verification.

### Dependency Matrix
- Task 1 blocks Tasks 3, 4, 6, 7, 8, 9, 10.
- Task 2 blocks Task 10 and should complete before meaningful load measurements.
- Task 3 blocks Task 4.
- Task 4 blocks Tasks 5 and 10.
- Task 5 blocks Task 10 latency/write-rate acceptance.
- Task 6 blocks Tasks 7 and 8.
- Task 7 blocks admin/dashboard verification in Task 10.
- Task 8 blocks end-to-end user history/chat verification.
- Task 9 blocks rollout readiness.
- Task 10 depends on all prior tasks.

## TODOs

- [ ] 1. Add `AtlasDBRouter` and Runtime DB Manifest

  **What to do**: Create `core/atlas_db_router.py` with `AtlasDBRouter`, `RuntimeDBRoute`, and helpers `control_db_path()`, `control_db()`, `runtime_route(session_id, create=True)`, `runtime_db_path(session_id, create=True)`, and `runtime_db(session_id, create=True)`. Add a control DB manifest table through `core/atlas_db.py` named `session_runtime_dbs(session_id TEXT PRIMARY KEY, session_uid TEXT NOT NULL, runtime_db_path TEXT NOT NULL, status TEXT NOT NULL DEFAULT 'active', schema_version INTEGER NOT NULL DEFAULT 1, created_at REAL NOT NULL, updated_at REAL NOT NULL, last_rollup_at REAL)`. Runtime DB paths must be generated as `<control-db-dir>/runtime/<session_uid[0:2]>/<session_uid>.db`. If a session has no DB row yet, create or upsert the runtime session first; only use `sha256(session_id)[:24]` as a temporary key in tests that intentionally bypass session activation. Add envs `ATLAS_CONTROL_DB_PATH`, `ATLAS_RUNTIME_DB_ROOT`, and `ATLAS_RUNTIME_DB_MODE=central|session`, with default `central`.
  **Must NOT do**: Do not move any table writes yet. Do not derive filenames from raw owner/IP/workflow. Do not require Postgres or Redis.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 3, 4, 6, 7, 8, 9, 10 | Blocked By: none

  **References**:
  - Pattern: `doc/wiki/atlas-db-router-runtime-sharding-20260602.md` - router-first strategy and control/runtime DB split.
  - Pattern: `core/atlas_db.py:593` - current `AtlasDB` initialization, schema bootstrap, and lock strategy.
  - Pattern: `src/atlas_api_sessions.py:472` - `upsert_runtime_session` already stores canonical session metadata and returns `session_uid`.
  - Pattern: `core/session_names.py:1` - existing session normalization rules.

  **Acceptance Criteria**:
  - [ ] `core/atlas_db_router.py` exposes typed route objects and deterministic paths.
  - [ ] `ATLAS_RUNTIME_DB_MODE=central` returns the existing control DB path for runtime paths.
  - [ ] `ATLAS_RUNTIME_DB_MODE=session` creates a manifest row and runtime DB path for `alice/ip_deep/rtl-gen`.
  - [ ] Manifest paths use generated IDs only and reject traversal-like session strings.
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_db.py tests/test_process_based_sessions.py -q` passes after new router tests are added.

  **QA Scenarios**:
  ```text
  Scenario: Runtime route creation
    Tool: bash
    Steps: Run new pytest test with temp control DB, ATLAS_RUNTIME_DB_MODE=session, session alice/ip_deep/rtl-gen.
    Expected: Manifest has one row; runtime path is under temp runtime root; path basename is not alice/ip_deep/rtl-gen.
    Evidence: evidence/task-1-router-route.txt

  Scenario: Central fallback
    Tool: bash
    Steps: Run new pytest test with ATLAS_RUNTIME_DB_MODE=central.
    Expected: runtime_db_path(session) == control_db_path(); no runtime manifest is required for queue operations.
    Evidence: evidence/task-1-router-central.txt
  ```

  **Commit**: YES | Message: `refactor(db): add runtime db router manifest` | Files: `core/atlas_db_router.py`, `core/atlas_db.py`, tests

- [ ] 2. Change `AtlasDB` Serialization from Global Lock to DB-Path Lock

  **What to do**: Replace `AtlasDB._WRITE_LOCK` usage with db-path-scoped locks. Add `_LOCKS_BY_PATH: dict[str, threading.RLock]` and `_LOCKS_GUARD`. Normalize lock keys with resolved paths except `:memory:` which gets an instance-local key. Keep thread-local connection caching keyed by `db_path`. Existing same-DB concurrent writer tests must still serialize. Add a two-DB concurrency test proving operations on different SQLite files are not serialized by one global lock.
  **Must NOT do**: Do not remove SQLite busy timeout/WAL setup. Do not make one shared sqlite connection cross threads.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 10 | Blocked By: none

  **References**:
  - Pattern: `core/atlas_db.py:601` - current process-wide `_WRITE_LOCK`.
  - Pattern: `core/atlas_db.py:640` - `_connect()` sets `busy_timeout` and WAL.
  - Test: `tests/test_atlas_db_concurrent_writers.py:49` - existing contention tests.
  - Test: `tests/test_db_concurrent_workflow_runs.py:43` - workflow run concurrency stress.

  **Acceptance Criteria**:
  - [ ] Same DB path writes are serialized and existing concurrency tests pass.
  - [ ] Different DB paths can execute writes concurrently in the same process.
  - [ ] WAL and busy timeout still apply to every opened DB.
  - [ ] No `database is locked` regressions in existing DB tests.

  **QA Scenarios**:
  ```text
  Scenario: Same DB path remains safe
    Tool: bash
    Steps: Run PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_db_concurrent_writers.py -q.
    Expected: All concurrent writer/read tests pass.
    Evidence: evidence/task-2-same-db-lock.txt

  Scenario: Different DB paths are independent
    Tool: bash
    Steps: Run new pytest test that holds a write transaction on db A while writing db B.
    Expected: db B write completes without waiting for db A lock release beyond a small threshold.
    Evidence: evidence/task-2-path-locks.txt
  ```

  **Commit**: YES | Message: `perf(db): scope atlas db locks by db path` | Files: `core/atlas_db.py`, tests

- [ ] 3. Inject Router into `SessionProcessManager` and Worker Environment

  **What to do**: Update `core/session_process_manager.py` so `_resolve_db_path`, `_get_db`, `spawn`, `build_worker_env`, `send_input`, `poll_output`, and `latest_output_id` use `AtlasDBRouter`. `spawn(session_id)` must set child env `ATLAS_CONTROL_DB_PATH=<control>`, `ATLAS_RUNTIME_DB_PATH=<runtime>`, `ATLAS_DB_PATH=<runtime>`, and `ATLAS_TRACE_DB_PATH=<runtime>` in runtime mode. Keep `--db-path` pointing at runtime DB for backward compatibility with `core/session_worker.py`. Add constructor injection `router: AtlasDBRouter | None = None` for tests.
  **Must NOT do**: Do not change queue placement yet in central mode. Do not spawn extra workers during routing tests.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4 | Blocked By: 1

  **References**:
  - Pattern: `core/session_process_manager.py:95` - current DB path resolution.
  - Pattern: `core/session_process_manager.py:111` - worker env construction.
  - Pattern: `core/session_process_manager.py:271` - worker spawn and `--db-path`.
  - Pattern: `core/session_process_manager.py:410` - `send_input` queue write.
  - Pattern: `core/session_process_manager.py:465` - output polling.
  - Test: `tests/test_process_based_sessions.py:111` - current env and `--db-path` assertions.

  **Acceptance Criteria**:
  - [ ] Central mode keeps existing test expectations.
  - [ ] Runtime mode passes runtime DB path to child process and keeps control DB path available separately.
  - [ ] `send_input`, `poll_output`, and `latest_output_id` open the same runtime DB for the same session.
  - [ ] Existing process-session tests pass.

  **QA Scenarios**:
  ```text
  Scenario: Worker env in runtime mode
    Tool: bash
    Steps: Run new process manager unit test with fake Popen and ATLAS_RUNTIME_DB_MODE=session.
    Expected: command has --db-path runtime DB; env has ATLAS_CONTROL_DB_PATH control DB and ATLAS_DB_PATH/ATLAS_TRACE_DB_PATH runtime DB.
    Evidence: evidence/task-3-worker-env.txt

  Scenario: Central mode compatibility
    Tool: bash
    Steps: Run PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions.py -q.
    Expected: Existing assertions pass without changing default behavior.
    Evidence: evidence/task-3-central-compat.txt
  ```

  **Commit**: YES | Message: `refactor(db): route process manager db paths` | Files: `core/session_process_manager.py`, tests

- [ ] 4. Move `session_queue` IPC to Runtime DBs

  **What to do**: Enable `SessionProcessManager` and `SessionWorker` queue operations to use runtime DBs in `ATLAS_RUNTIME_DB_MODE=session`. Keep `session_queue` schema unchanged with `session_id`, `direction`, `msg_type`, `payload`, and cursor fields. Add tests proving input prompt rows and output rows for two different sessions land in two different runtime DB files and that the control DB has zero `session_queue` rows for runtime-mode sessions. Ensure `cleanup_old_messages` runs against runtime DBs through the router.
  **Must NOT do**: Do not add `session_uid` to `session_queue` in this task. Do not remove central mode.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 5, 10 | Blocked By: 1, 3

  **References**:
  - Pattern: `core/atlas_db.py:208` - `session_queue` schema.
  - Pattern: `core/atlas_db.py:2388` - `enqueue_message`.
  - Pattern: `core/atlas_db.py:2440` - dequeue/poll implementation.
  - Pattern: `core/session_worker.py:349` - worker output emit path.
  - Test: `tests/test_atlas_input_deep_runtime.py:141` - durable process-mode prompt assertions.
  - Test: `tests/test_db_schema_complete.py:458` - queue semantics.

  **Acceptance Criteria**:
  - [ ] In runtime mode, `prompt`, `stop`, `interrupt`, and output events are read/written from the session runtime DB.
  - [ ] Control DB `session_queue` remains empty for runtime-mode sessions.
  - [ ] Two sessions can enqueue and poll independently without cross-session rows.
  - [ ] Existing durable prompt behavior remains unchanged from caller perspective.

  **QA Scenarios**:
  ```text
  Scenario: Runtime queue placement
    Tool: bash
    Steps: Run new pytest that creates sessions alice/ip_a/rtl-gen and bob/ip_b/rtl-gen, sends one prompt each, emits one output each.
    Expected: Each runtime DB has only its own in/out rows; control DB has no session_queue rows.
    Evidence: evidence/task-4-runtime-queue-placement.txt

  Scenario: Missing runtime DB recovery
    Tool: bash
    Steps: Delete one runtime DB file after manifest creation, then send a prompt.
    Expected: Router recreates initialized runtime DB or returns a clear recoverable error; no silent prompt loss.
    Evidence: evidence/task-4-runtime-recovery.txt
  ```

  **Commit**: YES | Message: `refactor(db): route session queue to runtime db` | Files: `core/session_process_manager.py`, `core/session_worker.py`, `core/atlas_db_router.py`, tests

- [ ] 5. Coalesce Live Output Writes

  **What to do**: Add a small worker-side output batcher in `core/session_worker.py`. Merge only `token` and `reasoning` events. Flush every 50ms, when buffered payload reaches 4KB, before any non-mergeable event, before `flush`, before `agent_state` changes, and at worker shutdown. Emit `token_batch` payloads as `{"chunks": [{"text": ..., "cls": ...}, ...]}` and `reasoning_batch` payloads as `{"chunks": [{"text": ..., "blank": ...}, ...]}`. Update `core/atlas_multiuser.py` process-output handling to expand batch events into ordered outbox events so the browser side does not need to change in this task. Never coalesce `ask_user`, `ask_user_answered`, `tool`, `tool_result`, `cost`, `token_usage`, `context`, `worker_started`, `worker_exited`, `error`, `file_changed`, `stop`, or `interrupt`.
  **Must NOT do**: Do not change visible output order. Do not buffer ask-user or lifecycle events. Do not require frontend changes for existing token rendering.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 10 | Blocked By: 4

  **References**:
  - Pattern: `core/session_worker.py:426` - `emit_content`.
  - Pattern: `core/session_worker.py:432` - `emit_reasoning`.
  - Pattern: `core/session_worker.py:512` - `emit_tool_result` must stay unmerged.
  - Pattern: `core/atlas_multiuser.py:346` - process output poller and outbox handoff.
  - Pattern: `core/react_loop.py:1059` - parser emits content/reasoning line callbacks.

  **Acceptance Criteria**:
  - [ ] 1,000 sequential `emit_content` calls produce <= 30 `session_queue` output rows with 50ms batching disabled through a deterministic test clock.
  - [ ] Expanded outbox events preserve exact concatenated output.
  - [ ] Non-mergeable events force a flush and retain order.
  - [ ] Existing token/reasoning UI event shape remains available after expansion.

  **QA Scenarios**:
  ```text
  Scenario: Token write reduction
    Tool: bash
    Steps: Run new pytest with fake clock, call worker.emit_content 1,000 times, then flush.
    Expected: session_queue output row count <= 30; concatenated expanded text equals input.
    Evidence: evidence/task-5-token-coalescing.txt

  Scenario: Ask-user ordering
    Tool: bash
    Steps: Emit token A, ask_user event, token B.
    Expected: Expanded outbox order is token A, ask_user, token B; ask_user is not delayed behind token B.
    Evidence: evidence/task-5-ordering.txt
  ```

  **Commit**: YES | Message: `perf(db): batch worker stream output rows` | Files: `core/session_worker.py`, `core/atlas_multiuser.py`, tests

- [ ] 6. Route Runtime Persistence for `messages`, `trace_events`, and `llm_calls`

  **What to do**: Add helper APIs that make runtime writes explicit: `router.runtime_db(session_id)` for session-scoped `messages`, `parts`, `trace_events`, and `llm_calls`; `router.control_db()` for users/auth/session registry/permissions. Update worker callsites that already have a session context to use runtime DB paths: `core/react_loop.py` worker `record_llm_call`, `src/headless_workflow.py` worker `record_llm_call`, process-mode session message save paths, and orchestrator runtime assistant/tool trace writes when a concrete `ctx.session_id` exists. Keep user-authored room/global chat messages in the control DB unless they are explicitly session-scoped. Hot tables keep `session_id` as their local query key; `session_uid` selects the DB file.
  **Must NOT do**: Do not attempt cross-DB transactions. Do not move auth, users, permissions, workspace/IP registry, or session registry into runtime DBs.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 7, 8 | Blocked By: 1

  **References**:
  - Pattern: `core/atlas_db.py:1928` - `save_message`.
  - Pattern: `core/atlas_db.py:3636` - `record_trace_event`.
  - Pattern: `core/atlas_db.py:3890` - `record_llm_call`.
  - Pattern: `core/react_loop.py:1339` - worker LLM persistence.
  - Pattern: `src/headless_workflow.py:1992` - headless workflow LLM persistence.
  - Pattern: `src/orchestrator/react_bridge.py:644` - orchestrator LLM accounting and chat writer.
  - Test: `tests/test_react_loop_worker_llm_call_persist.py:88` - worker LLM row persistence.

  **Acceptance Criteria**:
  - [ ] Worker `llm_calls` rows land in the session runtime DB in runtime mode.
  - [ ] Session-scoped runtime trace rows land in the session runtime DB.
  - [ ] User/global chat messages still land in control DB.
  - [ ] Central mode preserves existing behavior.
  - [ ] Tests prove central DB has no runtime `llm_calls` for runtime-mode worker calls except rollup rows added by Task 7.

  **QA Scenarios**:
  ```text
  Scenario: Worker LLM accounting routes to runtime DB
    Tool: bash
    Steps: Run updated tests/test_react_loop_worker_llm_call_persist.py with ATLAS_RUNTIME_DB_MODE=session.
    Expected: Runtime DB contains one llm_calls row for session alice/ip_deep/rtl-gen; control DB llm_calls count remains zero.
    Evidence: evidence/task-6-llm-runtime.txt

  Scenario: User chat remains control-scoped
    Tool: bash
    Steps: Use src/atlas_api_chat.py test client to send global chat and IP-room chat.
    Expected: Control DB trace_events contains user chat rows; runtime DB does not receive room/global chat rows.
    Evidence: evidence/task-6-chat-control.txt
  ```

  **Commit**: YES | Message: `refactor(db): route runtime event persistence` | Files: `core/react_loop.py`, `src/headless_workflow.py`, `src/orchestrator/react_bridge.py`, `core/atlas_db_router.py`, tests

- [ ] 7. Add Runtime Usage Rollups in the Control DB

  **What to do**: Add control DB tables `runtime_usage_rollups` and `runtime_rollup_offsets`. Rollup rows are keyed by `session_id` and include `session_uid`, `user_id`, `owner`, `ip`, `workflow`, `runtime_db_path`, `llm_calls`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `cache_read_tokens`, `cache_write_tokens`, `cost_usd`, `trace_events`, `messages`, `queue_in`, `queue_out`, `updated_at`, and `rollup_lag_s`. Add `core/runtime_rollup.py` with idempotent `rollup_session(session_id)` and `rollup_all_active(limit=...)`. Use high-water offsets per runtime table using `(created_at, id)`; never double count. Normal freshness target is <= 10 seconds; stale rollups must report `rollup_lag_s` instead of blocking admin pages.
  **Must NOT do**: Do not scan every runtime DB from admin request handlers. Do not delete raw runtime rows during rollup.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 8, 10 | Blocked By: 1, 6

  **References**:
  - Pattern: `core/atlas_admin_usage.py:115` - existing admin usage reads from central `llm_calls`.
  - Pattern: `core/atlas_user_dashboard.py:96` - user dashboard LLM summaries.
  - Pattern: `core/atlas_db.py:3180` - run summary aggregation over `llm_calls`.
  - Pattern: `core/atlas_db.py:3990` - visible user/IP LLM usage aggregation.

  **Acceptance Criteria**:
  - [ ] Rollup is idempotent across repeated runs.
  - [ ] Rollup does not block when one runtime DB is missing; it marks that session stale/error.
  - [ ] Control rollup totals equal raw runtime DB totals in tests.
  - [ ] Admin/user usage functions can read rollup rows without opening runtime DB files.

  **QA Scenarios**:
  ```text
  Scenario: Idempotent rollup
    Tool: bash
    Steps: Seed runtime DB with 3 llm_calls and 4 trace_events; run rollup twice.
    Expected: Control rollup counts remain 3 and 4, not 6 and 8.
    Evidence: evidence/task-7-idempotent-rollup.txt

  Scenario: Stale runtime DB
    Tool: bash
    Steps: Create manifest for two sessions, delete one runtime DB, run rollup_all_active.
    Expected: Existing session rolls up; missing session is marked stale/error; command exits successfully.
    Evidence: evidence/task-7-stale-runtime.txt
  ```

  **Commit**: YES | Message: `refactor(db): add runtime usage rollups` | Files: `core/atlas_db.py`, `core/runtime_rollup.py`, `core/atlas_admin_usage.py`, `core/atlas_user_dashboard.py`, tests

- [ ] 8. Update API/Admin Read Paths for Split Runtime Data

  **What to do**: Audit and update read paths that currently assume all runtime rows live in `AtlasDB()`. Session history APIs must route `get_messages` and session-scoped traces through `AtlasDBRouter.runtime_db(session_id)`. Admin overview/usage/dashboard endpoints must prefer `runtime_usage_rollups`. Raw DB browser must continue to expose the control DB by default and add an explicit `runtime_session_id` / `session_uid` parameter for inspecting one runtime DB at a time. Chat APIs must merge control user chat with session runtime assistant/tool rows only when a session filter is provided; global/IP room chat remains control-backed.
  **Must NOT do**: Do not perform all-runtime fanout reads during normal admin dashboard loads. Do not expose arbitrary filesystem DB paths to HTTP clients.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 10 | Blocked By: 6, 7

  **References**:
  - Pattern: `src/atlas_api_sessions.py:637` - DB-backed conversation message reads.
  - Pattern: `src/atlas_api_chat.py:102` - chat room context/message reads.
  - Pattern: `src/atlas_admin.py:253` - admin API read paths.
  - Pattern: `core/atlas_admin_db.py:79` - raw DB browser allowlist.
  - Pattern: `src/atlas_ui.py:9428` - mirrored admin/runtime reads in main UI.
  - Test: `tests/test_chat_full_multiuser_system.py:318` - multiuser system/chat isolation.

  **Acceptance Criteria**:
  - [ ] Session history reads runtime DB messages in runtime mode.
  - [ ] Admin overview and usage use control rollup rows by default.
  - [ ] Raw DB browser can inspect one runtime DB by owned `session_uid`, not arbitrary path.
  - [ ] Multiuser ownership checks still prevent cross-user session reads.
  - [ ] Central mode remains unchanged.

  **QA Scenarios**:
  ```text
  Scenario: Session history from runtime DB
    Tool: bash
    Steps: Seed runtime DB messages for alice/ip_deep/rtl-gen, call session history API as Alice.
    Expected: Response includes runtime messages; control DB messages table may be empty.
    Evidence: evidence/task-8-session-history.txt

  Scenario: Cross-user runtime DB access denied
    Tool: bash
    Steps: Alice owns runtime session; Bob requests raw runtime DB by Alice session_uid.
    Expected: HTTP 403 or equivalent auth failure; no runtime rows returned.
    Evidence: evidence/task-8-cross-user-deny.txt
  ```

  **Commit**: YES | Message: `refactor(db): route runtime read paths` | Files: `src/atlas_api_sessions.py`, `src/atlas_api_chat.py`, `src/atlas_admin.py`, `src/atlas_ui.py`, `core/atlas_admin_db.py`, tests

- [ ] 9. Add Operational Guardrails: Rollback, Cleanup, Metrics, and Failure Modes

  **What to do**: Add operational helpers and docs for runtime mode. Implement a runtime DB health/audit function that checks manifest rows, DB existence, schema initialization, queue depth, rollup lag, and lock/latency counters. Add metrics counters/logs for enqueue latency, poll latency, queue row count, output coalescing ratio, runtime DB open/init failures, rollup lag, and `database is locked` retries. Add cleanup/archive rules: session delete archives or deletes its runtime DB only after queue depth is zero; forced cleanup writes an audit row. Rollback policy: set `ATLAS_RUNTIME_DB_MODE=central` only after stopping workers and running a drain/audit command; forced rollback copies undelivered `session_queue` rows from runtime DBs to control DB before switching.
  **Must NOT do**: Do not silently delete runtime DB files. Do not hide corrupt/missing runtime DBs behind empty results.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 10 | Blocked By: 1, 4, 7

  **References**:
  - Pattern: `core/session_process_manager.py:410` - prompt enqueue latency logging.
  - Pattern: `core/atlas_db.py:2516` - queue cleanup.
  - Pattern: `core/atlas_db.py:4824` - existing session queue deletion during cleanup.
  - Pattern: `doc/wiki/db-concurrent-write-race-20260519.md` - WAL/busy_timeout concurrency history.

  **Acceptance Criteria**:
  - [ ] Health audit reports all runtime DBs and nonzero queue depths.
  - [ ] Forced cleanup/rollback requires explicit flag and records audit evidence.
  - [ ] Missing/corrupt runtime DB produces clear status and does not create false successful history responses.
  - [ ] Metrics are available in logs or JSON output for load verification.

  **QA Scenarios**:
  ```text
  Scenario: Runtime audit detects stale queue
    Tool: bash
    Steps: Seed one runtime DB with undelivered out messages, run audit helper.
    Expected: Audit JSON reports queue_out_depth > 0 and rollback_allowed=false.
    Evidence: evidence/task-9-audit-stale-queue.json

  Scenario: Forced rollback copies undelivered input
    Tool: bash
    Steps: Seed runtime DB with undelivered prompt, run forced rollback copy helper into control DB.
    Expected: Control DB receives the prompt row once; runtime row remains marked/copied or audit logs copy.
    Evidence: evidence/task-9-forced-rollback.txt
  ```

  **Commit**: YES | Message: `refactor(db): add runtime db operational guardrails` | Files: `core/atlas_db_router.py`, `core/runtime_rollup.py`, `core/atlas_db.py`, docs/tests

- [ ] 10. Build and Run the 100-Session Verification Harness

  **What to do**: Add an agent-executed synthetic load harness under `tests/` or `scripts/` that creates 100 active session namespaces, initializes runtime DBs, concurrently enqueues prompts, simulates worker output streams through the same queue APIs, polls outputs through `SessionProcessManager`/`_MultiUserBridge` paths where practical, runs rollup, and verifies placement and latency thresholds. No real LLM calls. No requirement to spawn 100 real Python workers in normal CI. Include an optional env-gated real-subprocess smoke with 10 workers: `ATLAS_RUNTIME_DB_REAL_SUBPROCESS_STRESS=1`.

  **Concrete workload**:
  - 100 sessions: `user000/ip000/rtl-gen` through `user099/ip099/rtl-gen`.
  - 100 concurrent prompt enqueues within one 60-second test window.
  - 100 synthetic output streams, each 200 token chunks and 10 reasoning chunks, through worker emit/batcher path.
  - Rollup after all streams complete.
  - Thresholds: p95 enqueue latency <= 250ms, p95 output poll latency <= 500ms, zero lost prompts, zero cross-session queue rows, zero `database is locked` exceptions, rollup lag <= 10s after rollup command.

  **Must NOT do**: Do not hit external LLM providers. Do not require 100 real subprocesses in default CI. Do not rely on arbitrary sleeps for pass/fail; collect measured latencies.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: final verification | Blocked By: 1-9

  **References**:
  - Pattern: `tests/test_lazy_worker_cold_start_storm.py:134` - subprocess stress fixture style, but keep this plan's default harness synthetic.
  - Pattern: `tests/test_atlas_input_deep_runtime.py:141` - process-mode durable prompt assertions.
  - Pattern: `tests/test_atlas_db_concurrent_writers.py:49` - concurrency test style.
  - Pattern: `tests/test_multiuser_bridge.py:47` - bridge process-mode plumbing.
  - Frontend optional: `frontend/atlas/__tests__/session-routing.test.mjs:14` - session/IP routing contract.

  **Acceptance Criteria**:
  - [ ] Synthetic 100-session load harness passes and writes JSON metrics.
  - [ ] Metrics prove no central control DB `session_queue` runtime rows.
  - [ ] Metrics prove each runtime DB contains only its own session rows.
  - [ ] p95 latency thresholds pass.
  - [ ] Rollup totals equal runtime raw totals.
  - [ ] Optional real-subprocess 10-worker smoke passes when env-gated.

  **QA Scenarios**:
  ```text
  Scenario: 100-session synthetic scale
    Tool: bash
    Steps: Run PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_runtime_db_100_user_scale.py -q.
    Expected: Test passes; evidence JSON includes p95 enqueue <= 250ms, p95 poll <= 500ms, locked_errors=0, lost_prompts=0.
    Evidence: evidence/task-10-100-session-scale.json

  Scenario: Rollup agrees with runtime raw rows
    Tool: bash
    Steps: Run the rollup section of the load harness after streams finish.
    Expected: Control DB rollup totals match sum of all runtime DB raw llm_calls/trace_events/messages/queue rows.
    Evidence: evidence/task-10-rollup-consistency.json
  ```

  **Commit**: YES | Message: `test(db): add runtime db 100 session scale harness` | Files: tests/scripts/evidence docs

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.
- [ ] F1. Plan Compliance Audit
  - Command: run a grep/static audit that verifies each task has its evidence file and each required runtime/control mode test has been executed.
  - Must confirm: Tasks 1-10 acceptance criteria are evidenced; central mode and runtime mode both pass.
  - Evidence: `evidence/final-plan-compliance.txt`
- [ ] F2. Code Quality Review
  - Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_process_based_sessions.py tests/test_atlas_input_deep_runtime.py tests/test_atlas_db_concurrent_writers.py tests/test_atlas_multiuser_session_scope.py tests/test_react_loop_worker_llm_call_persist.py tests/test_runtime_db_100_user_scale.py -q`
  - Must confirm: no regression in process sessions, queue semantics, DB concurrency, multiuser scope, or worker LLM accounting.
  - Evidence: `evidence/final-pytest.txt`
- [ ] F3. Real Runtime QA
  - Command: start local Atlas UI with `ATLAS_RUNTIME_DB_MODE=session` and a temp control DB, then submit prompts for at least two different sessions through the available API/WebSocket test harness.
  - Must confirm: live output arrives, runtime DBs contain queue rows, control DB queue remains empty, and rollups populate control DB.
  - Evidence: `evidence/final-runtime-qa.txt`
- [ ] F4. Scope Fidelity Check
  - Command: grep/static audit for forbidden work: no Redis/Postgres dependency added, no arbitrary runtime DB path HTTP parameter accepted, no token-by-token output insert path remains for process-mode content/reasoning.
  - Must confirm: implementation stayed within SQLite 100-user scope and did not introduce 1500-user infrastructure.
  - Evidence: `evidence/final-scope-fidelity.txt`

## Commit Strategy
- Use one commit per completed task when task scope is independently testable.
- Commit messages should use `refactor(db): ...`, `test(db): ...`, or `perf(db): ...`.

## Success Criteria
- 100-session synthetic load meets latency and correctness thresholds.
- Central control DB contains no `session_queue` rows for runtime-mode sessions.
- Runtime DB files contain the correct queue and runtime rows for their own sessions only.
- Admin usage stays available through rollups without runtime fanout scans.
- Central mode remains available as a rollback switch.
