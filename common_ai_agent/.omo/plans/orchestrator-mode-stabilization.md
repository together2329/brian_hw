# Orchestrator Mode Stabilization Plan

## Objective

Make ATLAS orchestrator mode reliable enough for user-facing experimentation
without weakening strict evidence semantics.

The goal is not "worker said completed, therefore green." The goal is:

```text
orchestrator dispatches owner workers
-> workers write or refresh required stage evidence
-> strict evidence gate decides completed/error/blocked
-> downstream jobs and DB state follow that decision
-> UI shows failed/blocked owner routing clearly
-> single-worker mode remains unchanged
```

## Non-Negotiable Rules

- Do not bypass `_enforce_completion_evidence_gate`.
- Do not mark a worker job `completed` unless required deterministic evidence exists and passes.
- Preserve distinct meanings:
  - `completed`: worker completed and evidence passed.
  - `error`: owning stage ran and produced failing or invalid evidence.
  - `blocked`: stage cannot proceed because upstream dependency, missing locked truth, human gate, or owner repair is required.
- Keep single-worker mode serial and unaffected.
- Test fixtures must create real minimal SSOT/stage evidence for positive green paths.
- Negative tests must deliberately create missing/invalid evidence and assert `error` or `blocked`.

## Current Evidence

Already passing:

```bash
cd frontend/atlas && ./node_modules/.bin/vitest run \
  __tests__/app-shell-font-select.test.tsx \
  __tests__/exec-policy.test.mjs \
  __tests__/session-routing.test.mjs
```

Observed result: 18 frontend tests passed.

Focused backend result:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_exec_policy.py \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_run_policy_get_post_and_state_payload \
  tests/test_atlas_api_pipeline_state.py::test_orchestrator_mode_post_toggles_env_and_state_payload \
  tests/test_orchestrator_workers_route.py \
  tests/test_pipeline_orchestrator_worker_integration.py -q
```

Observed result: 31 passed, 5 failed, 5 skipped.

The failures are not picker failures. They show a contract mismatch:

```text
test expects mock worker completion == completed
current production gate requires worker completion + stage evidence pass
```

## Key Files

Backend dispatch and gates:

- `src/atlas_api_jobs.py`
  - `_dispatch_job_to_worker`
  - `_dispatch_job_to_ipc_worker`
  - `_refresh_completed_stage_evidence`
  - `_job_artifact_failure`
  - `_job_artifact_recovery`
  - `_enforce_completion_evidence_gate`
  - `/api/pipeline/state` stage-state derivation
  - `/api/orchestrator/workers`

Stage engine:

- `src/workflow_stage_engine.py`
  - `WorkflowStageEngine.run_stage`
  - `_run_rtl`
  - `_write_stage_todo_evidence_plan`

Stage surface:

- `src/workflow_stage_surface.py`
  - `run_common_stage_surface`
  - blocked/human-gate prompt shaping

Integration tests:

- `tests/test_pipeline_orchestrator_worker_integration.py`
  - `_write_mock_stage_artifact`
  - `_mock_worker`
  - `_agent_server_worker`
  - failing dispatch/evidence tests

State/API tests:

- `tests/test_atlas_api_pipeline_state.py`
- `tests/test_orchestrator_workers_route.py`

Frontend:

- `frontend/atlas/app-helpers.tsx`
- `frontend/atlas/app.tsx`
- `frontend/atlas/pipeline-flow-stage.tsx`
- `frontend/atlas/pipeline-cards.tsx`
- `frontend/atlas/workspace-root-render.tsx`
- `frontend/atlas/workspace-feed-cards.tsx`
- `frontend/atlas/agent-worker-status.tsx`

## Implementation Tasks

### Task 1: Define the Status Contract in Tests First

Add or update tests so the expected backend status contract is explicit.

Files:

- `tests/test_pipeline_orchestrator_worker_integration.py`
- `tests/test_atlas_api_pipeline_state.py`

Required tests:

1. Positive orchestrator path:
   - Given valid minimal SSOT and valid RTL stage evidence.
   - When mock worker reports `completed`.
   - Then `rtl` job is `completed`.
   - Then downstream `lint` can run.
   - Then DB `workflow_runs.status` is `completed`.

2. Missing evidence path:
   - Given worker reports `completed` but no required stage evidence exists.
   - Then owning stage becomes `error`.
   - Then downstream stages become `blocked`.
   - Then DB stores `rtl-gen=error`, downstream `lint=blocked`.

3. Stage-engine blocked path:
   - Given `logs/stage_engine/ssot-rtl.json` exists with `status=blocked`.
   - Then job state is not green.
   - Preferred contract: owning job status becomes `blocked`, not `error`, if the stage engine explicitly reports blocked.
   - Downstream remains `blocked`.

4. Placeholder RTL path:
   - Given RTL contains `TODO`, `TBD`, `PLACEHOLDER`, or `stub`.
   - And the stage has actually run, proven by `rtl/rtl_compile.json` or `logs/stage_engine/ssot-rtl.json`.
   - Then `_job_artifact_failure` returns `True`.
   - If no verdict artifact exists, scaffold RTL should not be marked failed.

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_worker_completion_without_stage_evidence_is_not_marked_green \
  tests/test_pipeline_orchestrator_worker_integration.py::test_rtl_stage_evidence_gate_rejects_placeholder_sources \
  -q
```

These tests should fail before implementation and pass after.

### Task 2: Build Minimal Valid Stage Evidence Fixtures

Do not weaken production gates. Instead, make positive test fixtures satisfy the
same gates production uses.

Files:

- `tests/test_pipeline_orchestrator_worker_integration.py`

Add helper:

```text
_write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)
```

It must create the smallest set of artifacts that `_job_artifact_failure`,
`_job_artifact_recovery`, and `_refresh_completed_stage_evidence` accept.

Required fixture content:

- `yaml/<ip>.ssot.yaml`
  - valid IP name
  - non-empty locked requirement or direct-SSOT claim
  - enough `function_model` / `cycle_model` shape for `ssot-rtl` to avoid "SSOT not found" or "missing locked truth"
- `rtl/<ip>.sv`
  - no placeholder markers
  - syntactically plausible module
- `list/<ip>.f`
  - points to `rtl/<ip>.sv` using the path convention expected by local validators
- `rtl/rtl_compile.json`
  - pass status
- `lint/dut_lint.json`
  - zero errors
- `rtl/rtl_todo_plan.json` or current stage todo artifact
  - all required todos pass
  - open required todos = 0
  - static missing = 0
  - blocking questions = 0
- `logs/stage_engine/ssot-rtl.json`
  - `status=pass`
  - headline or summary says RTL evidence is closed

Implementation detail:

- Prefer generating the fixture through existing helper scripts if cheap.
- If direct fixture JSON is used, keep it in test helper code only.
- Do not write these artifacts into tracked IP directories.

Update `_write_mock_stage_artifact`:

- For `workflow == "rtl-gen"` or `stage == "rtl"`, call the valid fixture helper when `write_artifacts=True`.
- Preserve `write_artifacts=False` for missing-evidence negative tests.
- Add a separate helper for blocked fixture:

```text
_write_blocked_ssot_rtl_fixture(ip_dir, ip, reason)
```

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints \
  -q
```

Both tests should pass without disabling the evidence gate.

### Task 3: Preserve `blocked` Separately from `failed`

Current risk: `/api/pipeline/state` maps DB statuses `error`, `failed`,
`blocked`, and `cancelled` into `failed`. That hides owner-routing semantics.

Files:

- `src/atlas_api_jobs.py`
- `tests/test_atlas_api_pipeline_state.py`

Change state mapping:

```text
DB completed/success/ok -> pipeline state passed
DB running -> pipeline state running
DB blocked -> pipeline state blocked
DB error/failed/cancelled -> pipeline state failed
```

Also preserve `error_summary`.

Add test:

```text
test_pipeline_state_preserves_blocked_db_row_as_blocked
```

Given latest DB row:

```text
workflow=rtl-gen
status=blocked
error_summary="blocked: SSOT not found"
```

Expect:

```text
state["stages"]["rtl"]["state"] == "blocked"
state["stages"]["rtl"]["error_summary"] contains "SSOT not found"
```

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_state_db_failed_propagates_error_summary \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_state_preserves_blocked_db_row_as_blocked \
  -q
```

### Task 4: Make Evidence-Demoted Completion Route Downstream Correctly

When a worker reports completed but evidence fails, the upstream job must be
demoted and downstream jobs must stop.

Files:

- `src/atlas_api_jobs.py`
- `tests/test_pipeline_orchestrator_worker_integration.py`

Required behavior:

```text
worker /status says completed
_enforce_completion_evidence_gate runs
gate fails
owning job status becomes error or blocked, depending on evidence result
downstream pending jobs become blocked
DB rows mirror the same statuses
```

Add or update tests:

- `test_worker_completion_without_stage_evidence_is_not_marked_green`
- `test_pipeline_dependency_failure_blocks_downstream_and_records_db_status`
- Add one explicit evidence-demotion test if needed:

```text
test_worker_reported_completed_with_invalid_evidence_blocks_downstream
```

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_worker_completion_without_stage_evidence_is_not_marked_green \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dependency_failure_blocks_downstream_and_records_db_status \
  -q
```

### Task 5: Stabilize Real Agent-Server Worker Test

The real worker endpoint test currently fails because the worker path reaches
the strict stage engine and the fixture lacks valid SSOT/stage evidence.

Files:

- `tests/test_pipeline_orchestrator_worker_integration.py`

Update:

- Before dispatch, create the same minimal valid SSOT/RTL evidence fixture for the IP.
- Ensure the agent-server worker writes or preserves the evidence needed after `/run`.
- Keep the test checking real endpoint shape:
  - `/run`
  - `/status/<run_id>`
  - `/result/<run_id>`
  - `workflow` ordering
  - `rtl_version_id` carried into lint context

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints \
  -q
```

### Task 6: UI Blocked/Failed Owner Visibility

The UI must show orchestrator mode failures as actionable owner-routed states,
not just silent red cards.

Files:

- `frontend/atlas/pipeline-flow-stage.tsx`
- `frontend/atlas/pipeline-cards.tsx`
- `frontend/atlas/workspace-root-render.tsx`
- `frontend/atlas/workspace-feed-cards.tsx`
- `frontend/atlas/agent-worker-status.tsx`
- frontend test files under `frontend/atlas/__tests__/`

Required UI behavior:

1. Stage card:
   - `state=blocked` renders blocked label/glyph.
   - `state=failed` renders failed label/glyph.
   - If `blame.owner_workflow` exists for failed or blocked stages, show owner route text.
   - Save-handoff action should be available for failed and blocked owner-routed stages.

2. Worker strip:
   - running jobs show as running.
   - error/failed/cancelled/blocked show as non-green.
   - blocked count is visible when supplied by `/api/orchestrator/workers`.

3. Handoff feed:
   - `dispatch_workflow` result with `status=blocked` displays blocked status and error/reason.
   - `write_handoff` card displays target workflow, IP, task, and reason.

Add tests:

```text
frontend/atlas/__tests__/pipeline-stage-blocked.test.tsx
frontend/atlas/__tests__/agent-worker-status.test.tsx update if needed
frontend/atlas/__tests__/handoff-format.test.mjs update if needed
```

Acceptance:

```bash
cd frontend/atlas && ./node_modules/.bin/vitest run \
  __tests__/app-shell-font-select.test.tsx \
  __tests__/exec-policy.test.mjs \
  __tests__/session-routing.test.mjs \
  __tests__/agent-worker-status.test.tsx \
  __tests__/handoff-format.test.mjs \
  __tests__/pipeline-stage-blocked.test.tsx
```

### Task 7: Keep Single-Worker Mode Stable

Orchestrator stabilization must not change serial/single-worker behavior.

Files:

- `core/atlas_exec_policy.py`
- `src/atlas_api_jobs.py`
- `frontend/atlas/app-helpers.tsx`
- `tests/test_atlas_exec_policy.py`
- `tests/test_atlas_api_pipeline_state.py`
- `frontend/atlas/__tests__/app-shell-font-select.test.tsx`

Required checks:

- `exec_mode=single-worker` remains valid.
- `exec_mode=orchestrator` remains selectable.
- `single-worker` pipeline dispatch records `exec_mode=single-worker`.
- single-worker path does not fan out across owner workers.

Acceptance:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_exec_policy.py \
  tests/test_atlas_api_pipeline_state.py::test_pipeline_dispatch_records_run_and_exec_mode \
  -q
```

```bash
cd frontend/atlas && ./node_modules/.bin/vitest run \
  __tests__/app-shell-font-select.test.tsx \
  __tests__/exec-policy.test.mjs
```

### Task 8: Optional Browser Smoke for User Experiment

Run this only after unit/integration tests pass.

Start the app:

```bash
python3 src/atlas_ui.py --port 8765
```

Browser scenario:

1. Open Atlas UI.
2. Confirm exec picker shows:
   - `Single Worker`
   - `Orchestrator`
3. Select `Orchestrator`.
4. Confirm `/api/pipeline/run_policy` returns `exec_mode=orchestrator`.
5. Dispatch a small pipeline with mocked or local worker endpoints.
6. Confirm UI shows:
   - dispatched jobs
   - completed stages for valid fixture
   - blocked/failed stages for invalid fixture
   - owner route or handoff action when applicable

If browser automation is available, write the result as a small evidence file:

```text
evidence/orchestrator-mode-smoke-YYYYMMDD.txt
```

Do not commit browser screenshots unless the repo already tracks comparable UI evidence.

## Final Verification Wave

Run from `common_ai_agent`:

```bash
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
  tests/test_atlas_exec_policy.py \
  tests/test_atlas_api_pipeline_state.py \
  tests/test_orchestrator_workers_route.py \
  tests/test_pipeline_orchestrator_worker_integration.py \
  -q
```

Run frontend:

```bash
cd frontend/atlas && ./node_modules/.bin/vitest run \
  __tests__/app-shell-font-select.test.tsx \
  __tests__/exec-policy.test.mjs \
  __tests__/session-routing.test.mjs \
  __tests__/agent-worker-status.test.tsx \
  __tests__/handoff-format.test.mjs
```

Run build:

```bash
cd frontend/atlas && ./node_modules/.bin/vite build
```

Optional broader smoke:

```bash
./scripts/run_tests.sh quick
```

## Done Criteria

The work is done only when all are true:

- Picker remains unlocked.
- Orchestrator mode can be selected and persisted.
- Positive orchestrator dispatch completes only when evidence passes.
- Worker-reported completion without evidence is rejected.
- Stage-engine blocked state remains blocked through job, DB, pipeline state, and UI.
- Downstream stages are blocked after upstream error/blocked.
- UI visibly distinguishes blocked from failed.
- UI exposes owner/handoff actions for owner-routed failed or blocked stages.
- Single-worker mode still passes its policy and dispatch tests.
- Final verification commands pass or any remaining skips are documented as pre-existing async-orchestrator contract skips.

## Risks to Watch

- `WorkflowStageEngine.run_stage("ssot-rtl")` may rewrite temp artifacts during job refresh. Keep all positive/negative fixtures in `tmp_path`.
- Existing evidence transcript files contain trailing whitespace; do not use whole-branch `git diff --check` as the only quality signal unless those tracked evidence files are intentionally cleaned.
- The large `src/atlas_api_jobs.py` file is high-risk. Keep changes surgical and covered by targeted tests.
- Do not silently convert blocked to failed just because frontend already handles failed. The purpose of this stabilization is to make blocked actionable.
