# Session Flow Dashboard Plan

## TL;DR
> **Summary**: Atlas admin의 중심을 User 목록에서 Session Flow로 옮긴다. Session 하나가 user input, worker, IP, workflow, LLM cost, artifact, outcome까지 이어졌는지 DB가 직접 증명하게 만든다.
> **Deliverables**:
> - Additive SQLite schema: `session_inputs`, `worker_runs`, `session_flow_events`, `session_flow_rollups`, `ip_flow_rollups`, plus provenance columns.
> - Write-path attribution for session creation, user inputs, worker runs, LLM calls, IP provenance, artifacts, and flow events.
> - New admin API: `/api/admin/session-flow`, registered in both admin route surfaces.
> - New Admin UI tab: `Session Flow`, with builder/team lead/executive lenses.
> - Backfill and confidence model for historical gaps.
> - Backend pytest, frontend Vitest, runtime-mode no-fanout checks, and wiki update.
> **Effort**: Large
> **Parallel**: YES - 4 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 3 -> Task 4 -> Tasks 5/6 -> Task 7 -> Task 8

## Context
### Original Request
- "Session 을 새로 신설하게 지금 쭉 만들고 있어. 이 관점에서 다시 한 번 나누어줘."
- "User가 Session 에서 얼마나 Input을 날렸는지? LLM Call 은 얼마나 했는지? IP 별로는 ? 뭐 이런 것도? IP는 언제 생성이 되었니? IP에 대해 어떤 worker가 어떤 일을 했는지?"
- "다 종합적으로 이 흐름이 잘 가고 있는지 어떻게 잘 사용하고 있는지 문제 없는지? 다시 리스트업좀"
- "그럼 UI로 한다면 어떻게?"
- "좋네. 이렇게 하기 위해 기반은 되어 있나? DB는 이걸 저장하나?"
- "어떻게 바꾸면 좋을지 planning 좀."

### Interview Summary
- 핵심 단위는 User가 아니라 Session이다.
- User, IP, workflow, worker, LLM call, artifact, todo, queue, trace는 Session에 붙는 차원이다.
- 3개 관점이 필요하다:
  - 만든 사람: attribution gap, write path, stale/routing 오류, worker/LLM/artifact lineage.
  - 팀장: 오늘 조치할 세션, 막힌 worker, 실패 workflow, IP별 진행/품질.
  - 사장: adoption, cost, output, risk, bottleneck.
- 기존 DB는 v1 관측은 가능하지만, full Session Flow truth에는 부족하다.

### Metis Review (gaps addressed)
- Session identity를 고정했다: backend join은 `sessions.id`, 화면/외부 식별은 `session_uid`와 `namespace`도 같이 노출한다.
- Input count 정의를 고정했다: 새 데이터는 `session_inputs`가 authoritative, 과거 데이터는 best-effort backfill + `attribution_confidence`.
- LLM count 정의를 고정했다: raw attempts, successful calls, failed calls, retries를 분리한다.
- Worker identity를 고정했다: `worker_runs`가 first-class ledger이고 `workflow_runs`, `orchestrator_runs`, `llm_calls`, `artifact_versions`와 연결한다.
- Runtime mode 리스크를 반영했다: admin read path는 일반 요청에서 runtime DB fanout을 하지 않는다. 필요한 값은 control-side flow rollup으로 접는다.
- API route 리스크를 반영했다: `/api/admin/session-flow`는 `src/atlas_admin.py`와 `src/atlas_ui.py` 양쪽에 등록한다.
- Historical backfill 리스크를 반영했다: inferred data는 `exact | inferred | missing | conflict`로 표시하고 UI에서 truth처럼 보이지 않게 한다.

## Work Objectives
### Core Objective
Admin이 "전체 유저 목록"이 아니라 "어떤 Session/IP/worker가 지금 문제인지, 흐름이 제대로 사용되고 있는지"를 즉시 판단할 수 있게 한다.

### Deliverables
- DB schema and helper methods for first-class Session Flow.
- Instrumented write paths that populate Session Flow data during normal operation.
- Repeat-safe backfill for historical records.
- Rollup builder and admin API payload.
- Admin UI `Session Flow` tab.
- Automated backend/frontend/runtime verification.
- Wiki/doc update explaining metric meaning and confidence limits.

### Definition of Done (verifiable conditions with commands)
- `pytest tests/test_db_schema_complete.py tests/test_atlas_session_flow_db.py`
- `pytest tests/test_atlas_observability_db.py tests/test_runtime_rollup.py`
- `pytest tests/test_db_full_stack_e2e_more.py`
- `cd frontend/atlas && npm test -- --run admin-session-flow.test.tsx`
- `cd frontend/atlas && npm run build`
- `git diff --check`
- The admin API returns `200` for `/api/admin/session-flow` with seeded data and `403` for non-admin access.
- The frontend `Session Flow` tab renders needs-attention cards, funnel, session rows, and a detail panel from mocked API data.

### Must Have
- Use internal `sessions.id` as canonical join key.
- Expose `session_uid`, `namespace`, `owner`, `ip`, `workflow`, and `session_kind` in API rows.
- Count user input with `session_inputs`; do not depend on `messages`/`parts` being populated.
- Link LLM calls to Session/IP/workflow/worker when known.
- Link IP creation to `created_by_user_id`, `source_session_id`, and `source_type`.
- Link artifact versions to source session, worker run, and LLM call when known.
- Show attribution gaps explicitly.
- Keep existing admin tabs working; do not remove `Flow`, `Inputs`, `Usage`, or `Costs`.
- Support central DB mode and session runtime DB mode.
- Store counts/IDs/status/timestamps in admin flow rollups, not full raw prompts.

### Must NOT Have
- No destructive DB rewrite.
- No claim that inferred historical attribution is exact.
- No normal admin request that opens every runtime DB.
- No replacement of `/api/admin/usage`.
- No role-specific access changes in this pass. Builder/team lead/executive are UI lenses only.
- No unrelated cleanup of existing dirty files.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-first for backend schema/API/rollup invariants; tests-after smoke for frontend rendering and interactions.
- QA policy: Every task below includes happy and failure/edge scenarios.
- Evidence: save command output and screenshots/logs under `.omo/evidence/task-{N}-{slug}.{ext}` when implementing.

## Execution Strategy
### Parallel Execution Waves
Wave 1: Task 1 only. Schema, migrations, and helper contracts must land first.
Wave 2: Tasks 2 and 3 can run in parallel after Task 1, but coordinate on helper names.
Wave 3: Tasks 4, 5, and 6 can run after Task 3. API and UI should share the exact response contract from Task 4.
Wave 4: Tasks 7 and 8 run after Tasks 4-6.

### Dependency Matrix
- Task 1 blocks Tasks 2, 3, 7.
- Task 2 blocks Task 3 and Task 7.
- Task 3 blocks Task 4.
- Task 4 blocks Tasks 5 and 6.
- Task 5 blocks Task 6.
- Tasks 1-6 block Task 7.
- Tasks 1-7 block Task 8.

## TODOs

- [ ] 1. Add Session Flow Schema, Migrations, and DB Helpers

  **What to do**: Add first-class flow tables and additive columns in `core/atlas_db.py`.
  - Add tables to `SCHEMA_SQL`:
    - `session_inputs`: `id`, `session_id`, `user_id`, `workspace_id`, `ip_id`, `workflow`, `source`, `source_ref_id`, `input_index`, `char_count`, `token_estimate`, `intent_type`, `input_hash`, `attribution_confidence`, `missing_reason`, `created_at`.
    - `worker_runs`: `id`, `session_id`, `user_id`, `workspace_id`, `ip_id`, `workflow`, `worker_id`, `worker_kind`, `worker_label`, `workflow_run_id`, `orchestrator_run_id`, `status`, `started_at`, `ended_at`, `duration_ms`, `task_label`, `output_summary`, `error_summary`, `created_at`, `updated_at`.
    - `session_flow_events`: `id`, `session_id`, `user_id`, `workspace_id`, `ip_id`, `workflow`, `workflow_run_id`, `stage_id`, `worker_run_id`, `llm_call_id`, `artifact_version_id`, `event_type`, `severity`, `attribution_confidence`, `missing_reason`, `idempotency_key`, `payload`, `created_at`.
    - `session_flow_rollups`: one row per session with flow state, input counts, LLM attempts/success/errors/tokens/cost, worker counts, workflow counts, artifact counts, queue counts, stale age, attribution gap count, risk level, rollup status, rollup lag, updated_at.
    - `ip_flow_rollups`: one row per IP with created provenance, sessions, active sessions, workflows, workers, artifacts, LLM cost, problem count, updated_at.
  - Add columns:
    - `sessions`: `objective`, `flow_state`, `success_condition`, `completed_at`, `abandoned_at`, `last_flow_event_at`.
    - `ip_blocks`: `created_by_user_id`, `source_session_id`, `source_type`, `source_confidence`.
    - `artifact_versions`: `source_session_id`, `source_worker_run_id`, `source_llm_call_id`, `attribution_confidence`.
    - `llm_calls`: `worker_run_id`, `attribution_confidence`, `missing_reason`.
    - `trace_events`: `worker_run_id`, `severity`, `attribution_confidence`, `missing_reason`.
  - Add indexes for session/time, IP/time, worker/status, idempotency, and rollup risk/updated_at.
  - Add all new JSON fields to `_JSON_COLUMNS`.
  - Extend `RUNTIME_SCHEMA_SQL` with `session_inputs`, `worker_runs`, `session_flow_events`, and the new columns needed for runtime writes.
  - Add helper methods: `record_session_input`, `start_worker_run`, `finish_worker_run`, `record_session_flow_event`, `upsert_session_flow_rollup`, `upsert_ip_flow_rollup`, `list_session_flow_rollups`, `list_ip_flow_rollups`.
  - Use `attribution_confidence` enum values only: `exact`, `inferred`, `missing`, `conflict`.

  **Must NOT do**: Do not add foreign-key enforcement that can break existing data. Do not store raw prompt text in `session_inputs`.

  **Parallelization**: Can Parallel: NO | Wave 1 | Blocks: Tasks 2,3,7 | Blocked By: none

  **References**:
  - Pattern: `core/atlas_db.py:108` - `sessions` schema.
  - Pattern: `core/atlas_db.py:277` - `ip_blocks` schema.
  - Pattern: `core/atlas_db.py:305` - `artifact_versions` schema.
  - Pattern: `core/atlas_db.py:388` - `workflow_runs` schema.
  - Pattern: `core/atlas_db.py:472` - `trace_events` schema.
  - Pattern: `core/atlas_db.py:504` - `llm_calls` schema.
  - Pattern: `core/atlas_db.py:620` - runtime rollup table and no-fanout rationale.
  - Pattern: `core/atlas_db.py:710` - `RUNTIME_SCHEMA_SQL`.
  - Pattern: `core/atlas_db.py:835` - `_JSON_COLUMNS`.
  - Pattern: `core/atlas_db.py:1269` - lightweight migrations.
  - Test pattern: `tests/test_db_schema_complete.py:50` - expected tables/indexes.

  **Acceptance Criteria**:
  - [ ] New full-schema DB contains all five new tables and indexes.
  - [ ] Legacy DB opened through `AtlasDB` gets all additive columns through `_run_lightweight_migrations`.
  - [ ] Runtime schema DB contains `session_inputs`, `worker_runs`, `session_flow_events`, and can insert/read those rows.
  - [ ] Helper methods are idempotent when called with the same `idempotency_key` or same `(session_id, source, source_ref_id)` input source.
  - [ ] `_JSON_COLUMNS` serializes/deserializes `session_flow_events.payload` and rollup JSON fields if any are added.

  **QA Scenarios**:
  ```text
  Scenario: New DB has Session Flow schema
    Tool: bash
    Steps: pytest tests/test_db_schema_complete.py tests/test_atlas_session_flow_db.py -k "schema or migration" -q
    Expected: Tests pass; new tables, columns, indexes, runtime schema parity are asserted.
    Evidence: .omo/evidence/task-1-schema.txt

  Scenario: Legacy DB migrates without destructive rewrite
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "legacy_migration" -q
    Expected: Existing rows remain; new columns exist; no table is dropped.
    Evidence: .omo/evidence/task-1-legacy-migration.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `core/atlas_db.py`, `tests/test_db_schema_complete.py`, `tests/test_atlas_session_flow_db.py`

- [ ] 2. Instrument Write Paths for Inputs, Workers, LLM Calls, IPs, Artifacts, and Flow Events

  **What to do**: Make the new schema authoritative for future data.
  - Extend `create_session` with optional metadata: `namespace`, `owner`, `workspace_id`, `ip_id`, `ip`, `workflow`, `session_kind`, `objective`, `success_condition`. Keep existing callers valid.
  - Record a `session_flow_events` row for session creation and session metadata changes.
  - Capture user inputs:
    - Authoritative capture: when inbound user prompts are enqueued, call `record_session_input` with char count, token estimate, input hash, and source ref id.
    - Treat `session_queue.direction='in'` with `msg_type in ('prompt', 'input_prompt', 'answer')` as user-input candidates.
    - Do not store raw `payload.text` in `session_inputs`.
  - Capture worker lifecycle:
    - Create `worker_runs` from workflow/job starts and interactive worker starts.
    - Update status on `worker_started`, `worker_stopped`, `worker_exited`, workflow finish, and error events.
  - Capture LLM linkage:
    - Extend `record_llm_call` to accept `worker_run_id`, `attribution_confidence`, `missing_reason`.
    - After a call is inserted, write a `session_flow_events` row linked by `llm_call_id`.
    - Keep attempts and failed calls as rows; do not collapse retries.
  - Capture IP provenance:
    - Extend `upsert_ip_block` and IP creation call sites with `created_by_user_id`, `source_session_id`, `source_type`.
    - Write an `ip.created` flow event exactly once per IP.
  - Capture artifact provenance:
    - Extend `register_artifact_version` with `source_session_id`, `source_worker_run_id`, `source_llm_call_id`.
    - Write `artifact.produced` flow event and link run artifacts as today.
  - Populate `trace_events.worker_run_id`, `trace_events.llm_call_id`, and `trace_events.artifact_id` when producer context knows them.

  **Must NOT do**: Do not make accounting writes throw user-facing failures except where existing code already treats unroutable session IDs as errors. Do not mutate historical rows in this task.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Tasks 3,7 | Blocked By: Task 1

  **References**:
  - Pattern: `core/atlas_db.py:2089` - `create_session`.
  - Pattern: `core/atlas_db.py:3536` - `enqueue_message`.
  - Pattern: `core/session_worker.py:771` - worker input prompt handling.
  - Pattern: `core/session_worker.py:1228` - interactive worker start event.
  - Pattern: `core/atlas_trace.py:140` - trace context from env and workflow run start.
  - Pattern: `core/atlas_trace.py:221` - trace event writer with idempotency.
  - Pattern: `core/atlas_trace.py:395` - trace-scoped LLM call recording.
  - Pattern: `src/orchestrator/react_bridge.py:738` - orchestrator LLM accounting.
  - Pattern: `src/headless_workflow.py:2030` - worker LLM accounting.
  - Pattern: `core/react_loop.py:1338` - worker LLM accounting in react loop.
  - Pattern: `src/atlas_api_jobs.py:639` - workflow run start in jobs API.
  - Pattern: `src/atlas_api_jobs.py:737` - workflow run finish.
  - Pattern: `src/atlas_api_jobs.py:1711` - artifact version registration.

  **Acceptance Criteria**:
  - [ ] Creating a session records a `session.created` flow event.
  - [ ] Enqueuing an inbound prompt records exactly one `session_inputs` row and one `input.received` event.
  - [ ] Starting/finishing a workflow records a `worker_runs` row with correct status transition.
  - [ ] Worker and orchestrator LLM calls include `worker_run_id` when resolvable and produce linked flow events.
  - [ ] IP creation stores direct provenance columns and emits exactly one IP creation event.
  - [ ] Artifact version registration stores session/worker/LLM provenance when provided.
  - [ ] Existing tests for LLM accounting, session worker, and workflow runs remain green.

  **QA Scenarios**:
  ```text
  Scenario: Future session has complete flow lineage
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "write_path_complete_lineage" -q
    Expected: Session input, worker run, LLM call, IP provenance, artifact provenance, and flow events link by session_id.
    Evidence: .omo/evidence/task-2-lineage.txt

  Scenario: Duplicate input/event writes are idempotent
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "idempotent" -q
    Expected: Replaying the same source ref/idempotency key does not double-count inputs or events.
    Evidence: .omo/evidence/task-2-idempotent.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `core/atlas_db.py`, `core/atlas_trace.py`, `core/session_worker.py`, `core/react_loop.py`, `src/orchestrator/react_bridge.py`, `src/headless_workflow.py`, `src/atlas_api_jobs.py`, tests

- [ ] 3. Build Backfill and Rollup Logic with Explicit Confidence

  **What to do**: Add `core/session_flow_usage.py` as the read-model builder and backfill owner.
  - Implement flow state enum:
    - `created`, `input_received`, `worker_started`, `running`, `artifact_produced`, `verification_seen`, `completed`, `blocked`, `failed`, `stale`, `abandoned`.
  - Implement risk levels:
    - `critical`: stale active/running over 24h, blocked workflow, failed worker, queue backlog with no active worker, or high-cost unmatched attribution.
    - `warning`: no worker after input, no artifact after LLM spend, missing IP/workflow, stale over 6h, pending todos.
    - `ok`: recent progress or completed result with no open failure.
  - Implement confidence enum and missing reasons:
    - `exact`: direct source table has session/IP/worker linkage.
    - `inferred`: derived from temporal join or namespace.
    - `missing`: no defensible source.
    - `conflict`: multiple incompatible sources.
  - Implement `build_session_flow_payload(db, filters)` returning:
    - `generated_at`, `runtime_mode`, `summary`, `lenses`, `needs_attention`, `funnel`, `sessions`, `ip_flow`, `attribution_gaps`, `limits`.
  - Implement backfill function:
    - Future rows remain authoritative.
    - Historical inputs derive from existing `session_inputs` first, then `session_queue`, then `trace_events` user chat messages only when session-linked, then `messages/parts` if present.
    - Historical LLM stats derive from `llm_calls` and mark unmatched session IDs as attribution gaps.
    - Historical IP provenance derives from earliest exact workflow/session link only as `inferred`; otherwise `missing`.
    - Historical worker activity derives from `worker_runs` first, then `workflow_runs`/orchestrator runs as `inferred`.
  - Implement rollup upserts:
    - `session_flow_rollups` and `ip_flow_rollups` are recomputable and repeat-safe.
    - Use high-water or idempotency where runtime source rows are folded.
  - Do not surface raw prompt payloads in payload rows.

  **Must NOT do**: Do not overwrite existing `llm_calls.session_id` values. Do not hide unmatched cost; surface it as `attribution_gaps`.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: Task 4 | Blocked By: Tasks 1,2

  **References**:
  - Pattern: `core/atlas_admin_usage.py:126` - runtime-mode summary-only read pattern.
  - Pattern: `core/atlas_admin_usage.py:251` - public admin usage payload builder.
  - Pattern: `core/atlas_admin_usage.py:601` - existing best-effort input history query.
  - Pattern: `core/atlas_admin_usage.py:667` - workflow stage aggregation.
  - Pattern: `core/atlas_admin_usage.py:1005` - artifact version projection.
  - Pattern: `core/atlas_db.py:620` - runtime rollup rationale.
  - Test pattern: `tests/test_runtime_rollup.py:1` - idempotent rollup contract.
  - Test pattern: `tests/test_runtime_rollup.py:553` - no runtime DB open on read.

  **Acceptance Criteria**:
  - [ ] Seeded complete session returns `risk_level='ok'`, populated input/LLM/worker/IP/artifact counts, and `attribution_confidence='exact'`.
  - [ ] Seeded stale running workflow returns `risk_level='critical'` and appears in `needs_attention`.
  - [ ] Seeded LLM call without matching session appears in `attribution_gaps`, not a fake session row.
  - [ ] Backfill is repeat-safe and does not double-count.
  - [ ] Runtime mode reads control-side rollups and does not open runtime DB files on normal admin read.

  **QA Scenarios**:
  ```text
  Scenario: Rollup classifies complete, warning, critical sessions
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "rollup_classifies" -q
    Expected: Three seeded sessions map to ok/warning/critical and needs_attention contains only warning/critical.
    Evidence: .omo/evidence/task-3-rollup-classifies.txt

  Scenario: Historical unmatched LLM spend remains an attribution gap
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "unmatched_llm_gap" -q
    Expected: Unmatched calls are counted in attribution_gaps with confidence missing; no session row claims them.
    Evidence: .omo/evidence/task-3-unmatched-llm.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `core/session_flow_usage.py`, `core/atlas_db.py`, `tests/test_atlas_session_flow_db.py`, `tests/test_runtime_rollup.py`

- [ ] 4. Add `/api/admin/session-flow` in Both Admin Route Surfaces

  **What to do**: Expose the Session Flow payload through admin-only HTTP routes.
  - Add endpoint in `src/atlas_admin.py`.
  - Add matching endpoint in `src/atlas_ui.py`.
  - Import `build_session_flow_payload` lazily inside route handlers.
  - Preserve existing admin auth behavior:
    - `401` when login is required.
    - `403` when authenticated user is not admin.
  - Supported query params:
    - `range=24h|7d|30d|all`, default `7d`.
    - `lens=builder|team_lead|executive`, default `team_lead`.
    - `risk=all|critical|warning|ok`, default `all`.
    - `ip_id`, `workflow`, `user_id`, `session_id`, optional exact filters.
    - `limit`, default `100`, max `500`.
    - `offset`, default `0`.
  - Response top-level shape:
    - `generated_at`, `runtime_mode`, `range`, `lens`, `summary`, `needs_attention`, `funnel`, `sessions`, `ip_flow`, `attribution_gaps`, `pagination`.
  - `sessions[]` row required fields:
    - `session_id`, `session_uid`, `namespace`, `title`, `user_id`, `username`, `ip_id`, `ip`, `workflow`, `flow_state`, `risk_level`, `input_count`, `input_chars`, `input_tokens_est`, `llm_attempts`, `llm_success`, `llm_errors`, `tokens_input`, `tokens_output`, `tokens_reasoning`, `cost_usd`, `worker_runs`, `active_workers`, `failed_workers`, `workflow_runs`, `workflow_errors`, `artifact_count`, `attribution_confidence`, `missing_reason`, `created_at`, `updated_at`.
  - Keep endpoint read-only.

  **Must NOT do**: Do not change `/api/admin/usage` response shape. Do not expose this endpoint to non-admin users.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Tasks 5,6 | Blocked By: Task 3

  **References**:
  - Pattern: `src/atlas_admin.py:328` - standalone `/api/admin/usage`.
  - Pattern: `src/atlas_admin.py:269` - `/api/admin/sessions`.
  - Pattern: `src/atlas_ui.py:9823` - main UI `/api/admin/usage`.
  - Pattern: `tests/test_db_full_stack_e2e_more.py:176` - HTTP admin usage payload test.
  - Pattern: `tests/test_atlas_admin_auth.py` - admin auth expectations.

  **Acceptance Criteria**:
  - [ ] Standalone admin server returns `200` and expected payload keys for admin request.
  - [ ] Main UI server returns the same route and payload keys.
  - [ ] Non-admin request returns existing denied behavior.
  - [ ] Query filters constrain rows without changing summary semantics.
  - [ ] `limit > 500` is clamped to `500`.

  **QA Scenarios**:
  ```text
  Scenario: Admin can read Session Flow payload
    Tool: bash
    Steps: pytest tests/test_db_full_stack_e2e_more.py -k "admin_session_flow" -q
    Expected: /api/admin/session-flow returns summary, needs_attention, funnel, sessions, ip_flow, attribution_gaps.
    Evidence: .omo/evidence/task-4-http-admin.txt

  Scenario: Non-admin cannot read Session Flow payload
    Tool: bash
    Steps: pytest tests/test_atlas_admin_auth.py -k "session_flow_denied" -q
    Expected: Non-admin receives 403 or existing auth-denied status; no flow rows are returned.
    Evidence: .omo/evidence/task-4-http-auth.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `src/atlas_admin.py`, `src/atlas_ui.py`, `tests/test_db_full_stack_e2e_more.py`, `tests/test_atlas_admin_auth.py`

- [ ] 5. Wire Admin Data Loading and Tab Registration

  **What to do**: Add `Session Flow` tab state and lazy loading in the admin React root.
  - Keep existing tabs unchanged.
  - Add `sessionFlow` state in `frontend/atlas/admin.tsx`.
  - Load `/api/admin/session-flow` lazily when `activeTab === 'session-flow'` or when filters/lens change.
  - Do not add `/api/admin/session-flow` to the initial `Promise.all` in `loadAdminData`; this avoids slowing initial admin load.
  - Add `sessionFlow` count to `AdminTabCounts`.
  - Add a new tab button label: `Session Flow ({counts.sessionFlowNeedsAttention})`.
  - Keep existing `Flow` tab as todo-flow; do not rename it.
  - Add filter passthrough: range, ip, workspace, workflow, user. Add lens state local to Session Flow tab.
  - Handle loading/error/empty state specifically for Session Flow.

  **Must NOT do**: Do not refactor the whole admin page. Do not nest cards inside cards.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Task 6 | Blocked By: Task 4

  **References**:
  - Pattern: `frontend/atlas/admin.tsx:58` - admin root state.
  - Pattern: `frontend/atlas/admin.tsx:137` - existing admin data loading.
  - Pattern: `frontend/atlas/admin.tsx:773` - tab row render.
  - Pattern: `frontend/atlas/admin.tsx:805` - tab panel conditional rendering.
  - Pattern: `frontend/atlas/admin-chrome.tsx:14` - tab count type.
  - Pattern: `frontend/atlas/admin-chrome.tsx:48` - tab button pattern.
  - Test pattern: `frontend/atlas/__tests__/user-dashboard-render-smoke.test.tsx:75` - real component smoke import/render pattern.

  **Acceptance Criteria**:
  - [ ] Admin page has a `Session Flow` tab without changing existing tab labels.
  - [ ] Endpoint is fetched only when tab is active or tab filters change.
  - [ ] `401`/`403` behavior remains consistent with existing admin load.
  - [ ] Loading, error, and empty states render without throwing.
  - [ ] Tab count uses `needs_attention.length` from API payload.

  **QA Scenarios**:
  ```text
  Scenario: Session Flow tab lazy-loads
    Tool: bash
    Steps: cd frontend/atlas && npm test -- --run admin-session-flow.test.tsx -t "lazy-loads"
    Expected: Initial render does not fetch /api/admin/session-flow; clicking Session Flow does fetch it once.
    Evidence: .omo/evidence/task-5-lazy-load.txt

  Scenario: Existing Flow tab remains todo-flow
    Tool: bash
    Steps: cd frontend/atlas && npm test -- --run admin-session-flow.test.tsx -t "keeps existing flow tab"
    Expected: Existing Flow tab label/render still uses todo flow data, and new Session Flow tab is separate.
    Evidence: .omo/evidence/task-5-existing-flow.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `frontend/atlas/admin.tsx`, `frontend/atlas/admin-chrome.tsx`, `frontend/atlas/__tests__/admin-session-flow.test.tsx`

- [ ] 6. Build the Session Flow UI Components and Three Lenses

  **What to do**: Add focused UI components for the new tab.
  - Create `frontend/atlas/admin-session-flow.tsx`.
  - Export `AdminSessionFlowTab`.
  - Layout:
    - Top band: `Needs Attention` with counts for critical sessions, stale workers, unmatched cost, attribution gaps.
    - Funnel: `Created -> Input -> Worker -> LLM -> Artifact -> Verified -> Completed`.
    - Main split: triage table on left/center, detail panel on right.
    - IP section: IP creation/provenance and IP-level worker/cost/outcome rows.
  - Lenses:
    - `builder`: show attribution confidence, missing reasons, event gaps, raw IDs, rollup lag, route source.
    - `team_lead`: show blocked/stale sessions, owner/user, IP, workflow, worker status, next action.
    - `executive`: show adoption, cost, output count, risk count, trend summaries; hide raw IDs by default.
  - Triage row required columns:
    - risk, session title/namespace, user, IP, workflow, flow state, input count, LLM calls/cost, worker status, artifact count, age, next action.
  - Detail panel required sections:
    - Session identity.
    - Input metrics.
    - LLM metrics.
    - Worker timeline.
    - IP provenance.
    - Artifacts/outcomes.
    - Attribution gaps.
  - Visual constraints:
    - Dense operational dashboard, no marketing hero.
    - Use existing styles from `admin-styles.tsx`.
    - No nested cards.
    - Buttons/toggles use existing admin button style; add icons only if current icon library is already present.

  **Must NOT do**: Do not use raw prompt content. Do not create a separate landing page. Do not make a one-color decorative redesign.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Task 7 | Blocked By: Tasks 4,5

  **References**:
  - Pattern: `frontend/atlas/admin-overview.tsx:1` - extracted admin tab style.
  - Pattern: `frontend/atlas/admin-tables-a.tsx:179` - sessions table component pattern.
  - Pattern: `frontend/atlas/admin-tables-b.tsx:1` - table-heavy admin tabs.
  - Pattern: `frontend/atlas/admin-runtime.tsx:1` - runtime/feedback/admin-chat tab split.
  - Pattern: `frontend/atlas/admin-helpers.tsx:15` - shared `AdminRow` and formatting helpers.
  - Pattern: `frontend/atlas/admin-styles.tsx:1` - existing admin styles.
  - Test pattern: `frontend/atlas/__tests__/user-dashboard-render-smoke.test.tsx:95` - render smoke assertions.

  **Acceptance Criteria**:
  - [ ] The tab renders from a mocked payload with at least one critical, warning, and ok session.
  - [ ] Switching lenses changes visible fields without refetching unless filter values change.
  - [ ] Clicking a session row opens detail panel with input, LLM, worker, IP, artifact, and gap sections.
  - [ ] Empty payload renders a clear operational empty state.
  - [ ] Error payload renders an error state and leaves other admin tabs usable.
  - [ ] Text does not overflow table cells or buttons at desktop and mobile test widths.

  **QA Scenarios**:
  ```text
  Scenario: Session Flow tab renders operational view
    Tool: bash
    Steps: cd frontend/atlas && npm test -- --run admin-session-flow.test.tsx -t "renders session flow payload"
    Expected: Needs Attention, funnel, triage table, and detail panel all render from mock payload.
    Evidence: .omo/evidence/task-6-render.txt

  Scenario: Lens switching changes visible priorities
    Tool: bash
    Steps: cd frontend/atlas && npm test -- --run admin-session-flow.test.tsx -t "lenses"
    Expected: Builder lens shows attribution gaps/raw IDs; executive lens shows cost/outcome/risk summary and hides raw IDs by default.
    Evidence: .omo/evidence/task-6-lenses.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `frontend/atlas/admin-session-flow.tsx`, `frontend/atlas/admin.tsx`, `frontend/atlas/__tests__/admin-session-flow.test.tsx`

- [ ] 7. Harden Runtime Mode, Performance, and Backfill Safety

  **What to do**: Make Session Flow safe at 100+ users and session-runtime mode.
  - Extend `core/runtime_rollup.py` or adjacent rollup code so runtime `session_inputs`, `worker_runs`, and `session_flow_events` fold into control-side `session_flow_rollups` and `ip_flow_rollups`.
  - Use monotonic high-water offsets for runtime source tables, matching existing `runtime_rollup_offsets`.
  - Add no-fanout test: normal `/api/admin/session-flow` read must not open runtime DB files.
  - Add indexes used by Session Flow filters:
    - session risk/updated_at.
    - IP/workflow/updated_at.
    - attribution confidence/missing reason.
  - Add pagination and limit clamping tests.
  - Add repeat-safe backfill command/helper:
    - It can be called multiple times with no double-count.
    - It never mutates raw historical `llm_calls`, `trace_events`, or `session_queue`.
    - It only writes flow tables/rollups and provenance columns when confidence is `exact` or `inferred`.
  - Add performance budget for seeded data:
    - `build_session_flow_payload(limit=100)` completes under 500 ms on a synthetic 100-user/1000-session fixture in local tests.
    - If 500 ms is unstable in CI, assert query count/no-runtime-open and keep timing as logged evidence, not a hard flaky assertion.

  **Must NOT do**: Do not scan all runtime DB files per admin request. Do not write inferred source attribution without `source_confidence='inferred'`.

  **Parallelization**: Can Parallel: YES | Wave 4 | Blocks: Task 8 | Blocked By: Tasks 1,2,3,4,5,6

  **References**:
  - Pattern: `core/atlas_db.py:657` - runtime rollup offsets.
  - Pattern: `tests/test_runtime_rollup.py:117` - idempotent rollup test.
  - Pattern: `tests/test_runtime_rollup.py:553` - admin read no runtime open test.
  - Pattern: `tests/test_runtime_db_100_user_scale.py` - 100-user runtime scale patterns.
  - Pattern: `tests/test_runtime_queue_hardening.py:6` - runtime schema subset invariant.
  - Pattern: `core/atlas_db.py:917` - `schema_set` full/runtime behavior.

  **Acceptance Criteria**:
  - [ ] Runtime DB writes can record session inputs, worker runs, and flow events.
  - [ ] Rollup folds runtime rows exactly once.
  - [ ] Admin Session Flow read opens zero runtime DB files in runtime mode.
  - [ ] Backfill is repeat-safe.
  - [ ] Query filters work with seeded 100-user/1000-session fixture.

  **QA Scenarios**:
  ```text
  Scenario: Runtime mode Session Flow reads rollups only
    Tool: bash
    Steps: pytest tests/test_runtime_rollup.py -k "session_flow_no_runtime_open" -q
    Expected: Payload totals come from control rollups; runtime sqlite files are not opened.
    Evidence: .omo/evidence/task-7-runtime-no-open.txt

  Scenario: Backfill can run twice without double-counting
    Tool: bash
    Steps: pytest tests/test_atlas_session_flow_db.py -k "backfill_repeat_safe" -q
    Expected: Counts and rollups are identical after second run.
    Evidence: .omo/evidence/task-7-backfill-repeat.txt
  ```

  **Commit**: NO | Message: final combined commit | Files: `core/runtime_rollup.py`, `core/session_flow_usage.py`, `core/atlas_db.py`, `tests/test_runtime_rollup.py`, `tests/test_runtime_db_100_user_scale.py`, `tests/test_atlas_session_flow_db.py`

- [ ] 8. Update Wiki, Operator Semantics, and Final Commit

  **What to do**: Document what the dashboard means and how to trust it.
  - Add or update wiki page under `doc/wiki/`:
    - Session is the primary unit.
    - Define each metric: input count, LLM attempts/success/errors, cost, worker run, flow state, risk level, attribution confidence.
    - Explain stakeholder lenses.
    - Explain historical limitations: inferred/missing/conflict.
    - Explain runtime mode no-fanout design.
  - Update wiki index/log/graph if local wiki convention requires it.
  - Add a short operator note:
    - `critical` means admin should inspect today.
    - `warning` means follow-up or incomplete flow.
    - `ok` means no known action.
  - Run full verification commands.
  - Commit only files touched for Session Flow work. Do not add unrelated dirty files.

  **Must NOT do**: Do not commit unrelated existing dirty files. Do not overstate historical accuracy.

  **Parallelization**: Can Parallel: NO | Wave 4 | Blocks: final verification | Blocked By: Task 7

  **References**:
  - Existing wiki pattern: `doc/wiki/admin-operational-dashboard-db-snapshot-20260603.md`.
  - Existing wiki index: `doc/wiki/index.md`.
  - Existing wiki log: `doc/wiki/log.md`.
  - Existing wiki graph: `doc/wiki/_graph.json`.
  - Worktree guard: run `git status --short` before staging.

  **Acceptance Criteria**:
  - [ ] Wiki explains metrics and confidence clearly.
  - [ ] Full backend/frontend verification commands pass or failures are documented with root cause.
  - [ ] `git diff --check` passes.
  - [ ] `git status --short` is reviewed before staging.
  - [ ] Commit includes only Session Flow files.

  **QA Scenarios**:
  ```text
  Scenario: Documentation matches API fields
    Tool: bash
    Steps: rg "attribution_confidence|flow_state|llm_attempts|worker_runs|Session Flow" doc/wiki frontend/atlas core tests
    Expected: Wiki names match implemented API/UI/test field names.
    Evidence: .omo/evidence/task-8-doc-field-match.txt

  Scenario: Final staged files are scoped
    Tool: bash
    Steps: git status --short && git diff --cached --name-only
    Expected: Only Session Flow source/tests/wiki files are staged.
    Evidence: .omo/evidence/task-8-git-scope.txt
  ```

  **Commit**: YES | Message: `feat(admin): add session flow dashboard` | Files: Session Flow source, tests, and wiki only

## Final Verification Wave (MANDATORY - after ALL implementation tasks)
> ALL must APPROVE. Present consolidated results to user and get explicit okay before completing.
- [ ] F1. Plan Compliance Audit
  - Confirm every task acceptance criterion is either passed or explicitly documented.
  - Confirm no existing unrelated dirty file was staged.
- [ ] F2. Code Quality Review
  - Run targeted review of schema migrations, runtime mode, API route registration, and frontend state/loading.
  - Check no raw prompt text is exposed in admin rollups or UI.
- [ ] F3. Real Manual QA
  - Start local server.
  - Open admin page in Browser.
  - Log in as admin or use existing admin bypass if test env supports it.
  - Click `Session Flow`.
  - Capture screenshot showing Needs Attention, funnel, triage table, and detail panel.
- [ ] F4. Scope Fidelity Check
  - Confirm existing `Overview`, `Usage`, `Flow`, `Inputs`, and `Runtime` tabs still render.
  - Confirm `/api/admin/usage` response shape did not change.

## Commit Strategy
- Use one final feature commit after all tasks pass: `feat(admin): add session flow dashboard`.
- Do not stage existing unrelated dirty files.
- If implementation spans multiple days or many agents, task owners may create local partial commits only if user explicitly requests that workflow; otherwise keep one final scoped commit.

## Success Criteria
- Admin can answer these from DB/API/UI:
  - Which sessions need action today?
  - How many user inputs happened per session?
  - How many LLM attempts/success/errors and how much cost happened per session/IP?
  - Which IP was created when, by whom/source session, and with what confidence?
  - Which worker did what for an IP/session/workflow?
  - Which sessions are stale, blocked, high-cost, artifact-less, worker-less, or attribution-broken?
- Builder lens exposes system health and attribution problems.
- Team lead lens exposes operational blockers and ownership.
- Executive lens exposes adoption, spend, output, and risk.
- Historical uncertainty is visible, not hidden.
