# Orchestrator Mode Stabilization Execution Waves

## TL;DR
> Summary:      Stabilize ATLAS orchestrator mode around the production evidence contract: worker-reported completion is green only after deterministic stage evidence passes, missing or invalid evidence demotes the owner stage, downstream jobs block, and blocked remains distinct from failed through API and UI.
> Deliverables:
> - Backend evidence-gate and downstream-blocking fixes for mock and real worker paths.
> - Validator-real positive RTL fixtures that do not depend on `_patch_rtl_gate_for_fixture` for acceptance.
> - Pipeline state and UI blocked-vs-failed preservation, including owner route data where available.
> - Required evidence transcripts at `.omo/ulw-loop/evidence/orchestrator-positive-http.txt`, `.omo/ulw-loop/evidence/orchestrator-negative-http.txt`, and `.omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt`.
> Effort:       Medium
> Risk:         High - the positive RTL path currently relies on a test-only monkeypatch while production refresh/checker logic can rewrite or reject the fixture.

## Scope
### Must have
- Preserve `_enforce_completion_evidence_gate`; no worker path may mark a pipeline job `completed` only because `/status` returned `completed`.
- Positive mock-worker and real agent-server worker tests must complete only with deterministic stage evidence accepted by the real refresh/failure/recovery path.
- Missing evidence must demote the owner job to `error`, write the DB row as `error`, and block downstream jobs.
- Explicit deterministic `blocked` or `human_gate` evidence must demote the owner job to `blocked`, write the DB row as `blocked`, and block downstream jobs.
- `/api/pipeline/state` must preserve DB `blocked` as pipeline state `blocked`, preserve `error_summary`, and avoid collapsing blocked evidence to `failed`.
- Frontend stage cards, phase strip, worker strip, and rail summary must keep `blocked` visually and semantically distinct from `failed`.
- Single-worker policy, dispatch schedule, DB `exec_mode`, and picker behavior must remain unchanged.
- Capture the three required evidence transcripts named in `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:18`, `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:26`, and `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:34`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Must not bypass, delete, weaken, or short-circuit `_enforce_completion_evidence_gate` in `src/atlas_api_jobs.py:4480`.
- Must not use `_patch_rtl_gate_for_fixture` from `tests/test_pipeline_orchestrator_worker_integration.py:274` as the acceptance path for positive mock or real worker completion.
- Must not classify all blocked rows as failed just because filesystem artifact heuristics report a failure-like stage log.
- Must not change unrelated orchestrator route contracts, LLM loop behavior, or skipped Phase 3 chat tests.
- Must not change or delete unrelated dirty/untracked work, including `NEW_V5`.
- Must not add manual user verification; every scenario below is agent-executed and writes evidence.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: tests-after + pytest for backend, Vitest for frontend, Playwright/Chrome for browser smoke.
- QA policy: every task has agent-executed scenarios.
- Evidence: `.omo/ulw-loop/evidence/orchestrator-positive-http.txt`, `.omo/ulw-loop/evidence/orchestrator-negative-http.txt`, `.omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt`.

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Replace the positive RTL fixture contract with real evidence acceptance
- Task 2: Make `blocked` a terminal completion result in every refresh/finalization branch
- Task 3: Preserve blocked-vs-failed API state and owner route payloads
- Task 4: Harden frontend blocked/failed rendering and worker strip tests
- Task 5: Lock single-worker policy and dispatch invariants

Wave 2 (after Wave 1):
- Task 6: depends [1, 2] - stabilize positive mock-worker HTTP fanout
- Task 7: depends [1, 2] - stabilize positive real agent-server worker endpoints
- Task 8: depends [1, 2, 3] - stabilize negative missing/blocked evidence paths

Wave 3 (after Wave 2, final implementation/evidence capture):
- Task 9: depends [3, 4, 5, 6, 7, 8] - capture required HTTP/UI evidence transcripts

Critical path: Task 1 -> Task 6 -> Task 9

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1 | none | 6, 7, 8, 9 | 2, 3, 4, 5 |
| 2 | none | 6, 7, 8, 9 | 1, 3, 4, 5 |
| 3 | none | 8, 9 | 1, 2, 4, 5 |
| 4 | none | 9 | 1, 2, 3, 5 |
| 5 | none | 9 | 1, 2, 3, 4 |
| 6 | 1, 2 | 9 | 7, 8 |
| 7 | 1, 2 | 9 | 6, 8 |
| 8 | 1, 2, 3 | 9 | 6, 7 |
| 9 | 3, 4, 5, 6, 7, 8 | final verification | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Replace the positive RTL fixture contract with real evidence acceptance

  What to do: Update the positive-path test fixture in `tests/test_pipeline_orchestrator_worker_integration.py` so `_write_minimal_valid_ssot_rtl_fixture(ip_dir, ip)` creates the smallest artifact set accepted by the production RTL refresh/checker path. Add a focused test such as `test_minimal_valid_ssot_rtl_fixture_passes_real_stage_engine_gate` that writes the fixture under `tmp_path`, calls the real `WorkflowStageEngine(...).run_stage("ssot-rtl", ip)` and the real `_enforce_completion_evidence_gate`, and asserts the job remains `completed` with an evidence summary. Remove `_patch_rtl_gate_for_fixture` from positive test acceptance paths, or keep it only for explicitly scoped unit tests that are not used as green-path acceptance.
  Must NOT do: Do not patch `_job_artifact_failure`, `_job_artifact_recovery`, or `_refresh_completed_stage_evidence` in positive mock/real worker tests. Do not weaken `check_rtl_disk.sh` or lower the default `MIN_RTL`.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 7, 8, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:143` - current minimal fixture and comment explaining that the real engine/checker can reject the cheap fixture.
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:274` - current `_patch_rtl_gate_for_fixture`; positive acceptance must stop depending on this.
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:306` - mock worker artifact writer that delegates RTL artifact creation.
  - API/Type: `src/workflow_stage_engine.py:853` - real `WorkflowStageEngine.run_stage` dispatch.
  - API/Type: `src/workflow_stage_engine.py:1078` - `_run_rtl` runs derive, preflight, compile, lint, TODO audit, and computes pass/blocked/fail.
  - API/Type: `src/workflow_stage_engine.py:1166` - real RTL `evidence_pass` requirements.
  - API/Type: `src/atlas_api_jobs.py:4220` - `_rtl_current_completion_evidence_passes` required disk evidence.
  - API/Type: `src/atlas_api_jobs.py:4480` - `_enforce_completion_evidence_gate` production gate.
  - API/Type: `workflow/rtl-gen/scripts/check_rtl_disk.sh:23` - filelist/IP directory checks.
  - API/Type: `workflow/rtl-gen/scripts/check_rtl_disk.sh:48` - default RTL file-size threshold.
  - External: `https://docs.pytest.org/en/stable/how-to/tmp_path.html` - pytest `tmp_path` fixture for per-test artifact roots.
  - External: `https://docs.pytest.org/en/stable/how-to/monkeypatch.html` - pytest monkeypatch fixture; use for environment isolation, not positive evidence bypass.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_minimal_valid_ssot_rtl_fixture_passes_real_stage_engine_gate -q` exits 0.
  - [ ] `python3 - <<'PY'\nfrom pathlib import Path\ntext = Path('tests/test_pipeline_orchestrator_worker_integration.py').read_text()\nfor name in ('test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state', 'test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints'):\n    start = text.index('def ' + name)\n    end = text.find('\\ndef test_', start + 1)\n    body = text[start:end if end != -1 else len(text)]\n    assert '_patch_rtl_gate_for_fixture' not in body, name\nprint('positive worker tests do not use _patch_rtl_gate_for_fixture')\nPY` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```text
  Scenario: real RTL fixture passes production evidence gate
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 1 happy: real RTL fixture"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_minimal_valid_ssot_rtl_fixture_passes_real_stage_engine_gate -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: pytest exits 0 and the evidence file contains the test name plus "passed".
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt

  Scenario: positive worker tests do not use the RTL gate monkeypatch
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 1 edge: no positive-path monkeypatch"; python3 - <<'"'"'PY'"'"'\nfrom pathlib import Path\ntext = Path("tests/test_pipeline_orchestrator_worker_integration.py").read_text()\nfor name in ("test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state", "test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints"):\n    start = text.index("def " + name)\n    end = text.find("\\ndef test_", start + 1)\n    body = text[start:end if end != -1 else len(text)]\n    assert "_patch_rtl_gate_for_fixture" not in body, name\nprint("no positive-path RTL monkeypatch")\nPY\n} 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: command exits 0 and prints "no positive-path RTL monkeypatch".
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt
  ```

  Commit: YES | Message: `test(orchestrator): require real rtl evidence fixture` | Files: [tests/test_pipeline_orchestrator_worker_integration.py]

- [ ] 2. Make `blocked` a terminal completion result in every refresh/finalization branch

  What to do: Audit completion finalization in `src/atlas_api_jobs.py` and include `blocked` anywhere a demoted completed job must finish its DB row and advance/block downstream. Add or update focused backend tests so a job that enters `_refresh_tracked_jobs` as `completed`, then gets demoted by `_enforce_completion_evidence_gate` to `blocked`, calls `_finish_job_db_run(..., "blocked")` and `_advance_pipeline_from`, causing all dependent queued/pending jobs to become `blocked`.
  Must NOT do: Do not change `blocked` to `error` to fit existing terminal sets. Do not make `blocked` dispatch children.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 7, 8, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_api_jobs.py:714` - `_finish_job_db_run` preserves final `blocked`.
  - Pattern:  `src/atlas_api_jobs.py:994` - `_mark_downstream_blocked_locked` recursively blocks queued/pending dependents.
  - Pattern:  `src/atlas_api_jobs.py:3759` - `_advance_pipeline_from` handles upstream `error`, `cancelled`, and `blocked`.
  - Pattern:  `src/atlas_api_jobs.py:4540` - HTTP worker poll path already enforces, finishes, and advances after terminal worker status.
  - Pattern:  `src/atlas_api_jobs.py:4620` - final refresh branch enforces the gate but currently terminalizes only `completed`, `error`, and `cancelled`.
  - Test:     `tests/test_atlas_pipeline_contract.py:419` - recovered evidence still honors gate failure before advancing downstream.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1485` - explicit blocked engine integration expectation.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_pipeline_contract.py::test_completed_refresh_demoted_to_blocked_finishes_db_and_blocks_downstream -q` exits 0.
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream -q` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: blocked demotion finishes DB and blocks downstream
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 2 happy: blocked terminalization"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_pipeline_contract.py::test_completed_refresh_demoted_to_blocked_finishes_db_and_blocks_downstream -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: pytest exits 0; assertions prove owner DB status is blocked and downstream job is blocked.
    Evidence: .omo/ulw-loop/evidence/orchestrator-negative-http.txt

  Scenario: completed status still advances children
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 2 edge: completed still advances"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_pipeline_contract.py::test_advance_pipeline_starts_all_ready_dag_children -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: pytest exits 0; lint, tb, and syn become pending after rtl completed.
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt
  ```

  Commit: YES | Message: `fix(orchestrator): terminalize blocked evidence demotions` | Files: [src/atlas_api_jobs.py, tests/test_atlas_pipeline_contract.py]

- [ ] 3. Preserve blocked-vs-failed API state and owner route payloads

  What to do: Verify and harden `/api/pipeline/state` so DB `blocked` remains state `blocked`, `error`/`failed`/`cancelled` remain state `failed`, `error_summary` is preserved for both, and filesystem failure heuristics do not override a latest DB `blocked` row. Add an API bridge for owner-routed blocked stages only when a real owner source exists, such as a latest handoff for the workflow or structured blame object; do not invent a `blame` owner from only the stage name.
  Must NOT do: Do not emit `blame` for blocked stages with no owner source. Do not remove existing bare-string `blame` support for failed sim stages.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [8, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_api_jobs.py:5396` - `_state_from_db` mapping for `blocked` and failed statuses.
  - Pattern:  `src/atlas_api_jobs.py:5572` - stage state assembly with DB-first/FS fallback.
  - Pattern:  `src/atlas_api_jobs.py:5579` - DB `blocked` overrides filesystem failure heuristic.
  - Pattern:  `src/atlas_api_jobs.py:5661` - current `blame` assignment is limited to failed sim stages.
  - Pattern:  `src/atlas_api_jobs.py:5670` - per-workflow handoff summary is available while building each stage payload.
  - Pattern:  `src/atlas_api_jobs.py:5692` - `error_summary` emission for failed/blocked states.
  - Test:     `tests/test_atlas_api_pipeline_state.py:324` - DB blocked row maps to blocked stage state.
  - Test:     `frontend/atlas/__tests__/pipeline-stage-blocked.test.tsx:140` - frontend tolerates backend bare-string blame shape.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_api_pipeline_state.py::test_pipeline_state_preserves_blocked_db_row_as_blocked tests/test_atlas_api_pipeline_state.py::test_pipeline_state_db_failed_propagates_error_summary -q` exits 0.
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_api_pipeline_state.py::test_pipeline_state_exposes_owner_route_for_blocked_stage_with_handoff -q` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: DB blocked stays blocked in pipeline state
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 3 happy: blocked state API"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_api_pipeline_state.py::test_pipeline_state_preserves_blocked_db_row_as_blocked -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: pytest exits 0; response stage `rtl.state` is `blocked`, `source` is `db`, and summary contains "SSOT not found".
    Evidence: .omo/ulw-loop/evidence/orchestrator-negative-http.txt

  Scenario: failed DB row remains failed, not blocked
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 3 edge: failed state API"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_api_pipeline_state.py::test_pipeline_state_db_failed_propagates_error_summary -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: pytest exits 0; response stage state is `failed` and preserves the DB error summary.
    Evidence: .omo/ulw-loop/evidence/orchestrator-negative-http.txt
  ```

  Commit: YES | Message: `fix(pipeline-state): preserve blocked owner routing` | Files: [src/atlas_api_jobs.py, tests/test_atlas_api_pipeline_state.py]

- [ ] 4. Harden frontend blocked/failed rendering and worker strip tests

  What to do: Keep `blocked` visually distinct from `failed` in `PipelineFlowMap`, `StageCard`, `pipeline-rail`, and worker status summaries. Ensure owner route text and save-handoff actions appear for failed or blocked stages when `blame` exists, while no owner UI appears when no owner exists. Keep component tests focused and deterministic.
  Must NOT do: Do not collapse blocked into failed for simpler CSS/test assertions. Do not add visible instructional copy about how to use the UI.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:318` - phase strip counts `blocked` separately.
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:486` - DAG node pill maps `blocked` and `stale` to "blocked".
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:591` - `StageCard` status rendering.
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:603` - blocked/stale grouping for owner routing.
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:803` - owner/blame route display for failed or blocked.
  - Pattern:  `frontend/atlas/pipeline-flow-stage.tsx:848` - save-handoff action for failed or blocked owner-routed stages.
  - Pattern:  `frontend/atlas/pipeline-rail.tsx:155` - readiness summary counts blocked separately.
  - Test:     `frontend/atlas/__tests__/pipeline-stage-blocked.test.tsx:70` - blocked distinct from failed.
  - Test:     `frontend/atlas/__tests__/agent-worker-status.test.tsx:33` - blocked worker counts are visible.
  - API/Type: `frontend/atlas/package.json:5` - Vitest scripts.
  - API/Type: `frontend/atlas/vitest.config.js:4` - jsdom test environment.

  Acceptance criteria (agent-executable only):
  - [ ] `cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/pipeline-stage-blocked.test.tsx __tests__/agent-worker-status.test.tsx` exits 0.
  - [ ] `cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/pipeline-render-smoke.test.tsx __tests__/workers-sidebar-panel.test.jsx` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: blocked StageCard exposes owner route and save handoff
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 4 happy: blocked UI"; cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/pipeline-stage-blocked.test.tsx __tests__/agent-worker-status.test.tsx; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt'
    Expected: Vitest exits 0; assertions cover blocked glyph/label, owner route, save-handoff, bare-string blame, and blocked worker counts.
    Evidence: .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt

  Scenario: no owner means no blame or save-handoff UI
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 4 edge: no owner UI"; cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/pipeline-stage-blocked.test.tsx -t "shows NO blame UI"; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt'
    Expected: Vitest exits 0 and the focused test proves failed/blocked stages without owner do not render blame or save-handoff controls.
    Evidence: .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt
  ```

  Commit: YES | Message: `fix(frontend): show blocked owner routing distinctly` | Files: [frontend/atlas/pipeline-flow-stage.tsx, frontend/atlas/pipeline-rail.tsx, frontend/atlas/agent-worker-status.tsx, frontend/atlas/__tests__/pipeline-stage-blocked.test.tsx, frontend/atlas/__tests__/agent-worker-status.test.tsx]

- [ ] 5. Lock single-worker policy and dispatch invariants

  What to do: Preserve single-worker mode across backend policy, dispatch scheduling, DB job fields, frontend picker, and session-routing helpers. Add regression coverage if any invariant is not already explicit.
  Must NOT do: Do not make orchestrator mode the implicit default when legacy `ATLAS_SINGLE_MAIN_LOOP=1` is set. Do not make single-worker auto schedule fan out just because multiple workflow URLs are configured.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Test:     `tests/test_atlas_exec_policy.py:14` - exec-mode normalization and aliases.
  - Test:     `tests/test_atlas_exec_policy.py:26` - default single-worker behavior.
  - Test:     `tests/test_atlas_api_pipeline_state.py:722` - orchestrator toggle starts from single-worker legacy flag.
  - Test:     `tests/test_atlas_api_pipeline_state.py:782` - run policy GET/POST and state payload.
  - Test:     `tests/test_atlas_api_pipeline_state.py:866` - dispatch records `exec_mode=single-worker`.
  - Test:     `tests/test_atlas_pipeline_contract.py:236` - auto schedule is serial in single-worker mode.
  - Test:     `frontend/atlas/__tests__/app-shell-font-select.test.tsx:126` - shell picker allows orchestrator selection.
  - Test:     `frontend/atlas/__tests__/exec-policy.test.mjs:11` - frontend policy helper.
  - Test:     `frontend/atlas/__tests__/session-routing.test.mjs:14` - session routing invariants.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_exec_policy.py tests/test_atlas_api_pipeline_state.py::test_pipeline_run_policy_get_post_and_state_payload tests/test_atlas_api_pipeline_state.py::test_pipeline_dispatch_records_run_and_exec_mode tests/test_atlas_pipeline_contract.py::test_pipeline_auto_schedule_is_serial_in_single_worker_mode -q` exits 0.
  - [ ] `cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/app-shell-font-select.test.tsx __tests__/exec-policy.test.mjs __tests__/session-routing.test.mjs` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: backend single-worker policy remains serial and persisted
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 5 happy: backend single-worker"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_exec_policy.py tests/test_atlas_api_pipeline_state.py::test_pipeline_run_policy_get_post_and_state_payload tests/test_atlas_api_pipeline_state.py::test_pipeline_dispatch_records_run_and_exec_mode tests/test_atlas_pipeline_contract.py::test_pipeline_auto_schedule_is_serial_in_single_worker_mode -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt'
    Expected: pytest exits 0; output covers policy default, run_policy POST, dispatch `exec_mode`, and serial single-worker schedule.
    Evidence: .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt

  Scenario: frontend picker can still select orchestrator without breaking single-worker helpers
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 5 edge: frontend picker and policy"; cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/app-shell-font-select.test.tsx __tests__/exec-policy.test.mjs __tests__/session-routing.test.mjs; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt'
    Expected: Vitest exits 0; picker options are `single-worker` and `orchestrator`, and policy/session helpers retain expected routing.
    Evidence: .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt
  ```

  Commit: YES | Message: `test(exec-policy): lock single worker invariants` | Files: [tests/test_atlas_exec_policy.py, tests/test_atlas_api_pipeline_state.py, tests/test_atlas_pipeline_contract.py, frontend/atlas/__tests__/app-shell-font-select.test.tsx, frontend/atlas/__tests__/exec-policy.test.mjs, frontend/atlas/__tests__/session-routing.test.mjs]

- [ ] 6. Stabilize positive mock-worker HTTP fanout

  What to do: Update the mock-worker positive fanout test to rely on the real evidence fixture from Task 1 and the terminal semantics from Task 2. The test must dispatch via `POST /api/pipeline/dispatch`, poll `GET /api/jobs` until selected stages complete, assert owner worker routing, assert DB `workflow_runs.status` rows are `completed`, and assert no positive path uses `_patch_rtl_gate_for_fixture`.
  Must NOT do: Do not mark all rows completed immediately without polling the HTTP worker `/status` and `/result` path. Do not ignore DB status.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [9] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:361` - `_mock_worker` HTTP `/run`, `/status`, `/result` helper.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:526` - positive mock-worker fanout test.
  - API/Type: `src/atlas_api_jobs.py:3431` - HTTP worker dispatch sends `/run`.
  - API/Type: `src/atlas_api_jobs.py:4540` - worker poll reads `/status` and `/result`.
  - API/Type: `src/atlas_api_jobs.py:4572` - poll path enforces evidence gate before DB finish/advance.
  - API/Type: `src/atlas_api_jobs.py:3759` - downstream dispatch/blocked advancement.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state -q` exits 0.
  - [ ] The test asserts `rtl`, `lint`, `tb`, and `syn` rows are `completed`, worker request counts match owner routing, and DB statuses are `completed`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: mock workers complete selected DAG stages with valid evidence
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 6 happy: mock worker positive HTTP"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: pytest exits 0; `/api/jobs` reaches completed selected stages and owner workers receive expected workflow requests.
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt

  Scenario: positive test fails if the RTL monkeypatch is reintroduced
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 6 edge: mock fanout no monkeypatch"; python3 - <<'"'"'PY'"'"'\nfrom pathlib import Path\ntext = Path("tests/test_pipeline_orchestrator_worker_integration.py").read_text()\nstart = text.index("def test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state")\nend = text.find("\\ndef test_", start + 1)\nbody = text[start:end if end != -1 else len(text)]\nassert "_patch_rtl_gate_for_fixture" not in body\nprint("mock positive fanout uses real gate path")\nPY\n} 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: command exits 0 and prints "mock positive fanout uses real gate path".
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt
  ```

  Commit: YES | Message: `test(orchestrator): stabilize mock worker green path` | Files: [tests/test_pipeline_orchestrator_worker_integration.py]

- [ ] 7. Stabilize positive real agent-server worker endpoints

  What to do: Update the real agent-server endpoint integration test to use the Task 1 real evidence fixture, drive actual local `/run`, `/status/<run_id>`, and `/result/<run_id>` endpoints, and assert both `rtl` and `lint` complete with DB `completed` rows. Preserve assertions that `rtl_version_id` is carried into lint context and workflow order is `rtl-gen`, then `lint`.
  Must NOT do: Do not replace the real agent-server endpoint test with the mock worker helper. Do not skip the test because of timing; use bounded polling.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [9] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:431` - `_agent_server_worker` helper spins real FastAPI/uvicorn worker endpoints.
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:608` - real endpoint integration test.
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:645` - existing bounded polling loop for real worker completion.
  - API/Type: `src/atlas_api_jobs.py:3431` - HTTP worker dispatch.
  - API/Type: `src/atlas_api_jobs.py:4540` - HTTP worker polling/finalization.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints -q` exits 0.
  - [ ] The test asserts `worker_calls` workflows equal `["rtl-gen", "lint"]`, lint receives a non-empty `rtl_version_id`, and both job rows are `completed`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: real agent-server endpoints complete rtl and lint
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 7 happy: real worker positive HTTP"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: pytest exits 0; evidence contains real endpoint test output and completed rtl/lint statuses.
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt

  Scenario: endpoint test still proves HTTP shape, not mock-only path
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 7 edge: real endpoint symbols present"; python3 - <<'"'"'PY'"'"'\nfrom pathlib import Path\ntext = Path("tests/test_pipeline_orchestrator_worker_integration.py").read_text()\nbody_start = text.index("def test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints")\nbody_end = text.find("\\ndef test_", body_start + 1)\nbody = text[body_start:body_end if body_end != -1 else len(text)]\nassert "_agent_server_worker" in body\nassert "worker_calls" in body\nassert "rtl_version_id" in body\nassert "_mock_worker" not in body\nprint("real endpoint test still uses _agent_server_worker")\nPY\n} 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt'
    Expected: command exits 0 and prints "real endpoint test still uses _agent_server_worker".
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt
  ```

  Commit: YES | Message: `test(orchestrator): stabilize real worker endpoint path` | Files: [tests/test_pipeline_orchestrator_worker_integration.py]

- [ ] 8. Stabilize negative missing/blocked evidence paths

  What to do: Make the negative evidence contract explicit: worker-reported completion with no worker-written evidence is `error`; worker-reported completion with deterministic stage engine `blocked` or `human_gate` is `blocked`; downstream jobs become `blocked` in both cases; DB and pipeline state mirror the owner result. Keep a separate placeholder/scaffold regression so fresh RTL scaffolds do not show failed before a verdict artifact exists.
  Must NOT do: Do not use a positive fixture in missing-evidence tests. Do not map explicit `blocked` stage logs to `error`.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [9] | Blocked by: [1, 2, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:237` - blocked RTL fixture helper.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1353` - upstream worker error blocks downstream and records DB status.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1413` - completed-without-evidence becomes error and blocks downstream.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1485` - completed-with-blocked-stage-engine becomes blocked and blocks downstream.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1567` - placeholder source rejection after verdict artifact.
  - Test:     `tests/test_pipeline_orchestrator_worker_integration.py:1597` - scaffold without verdict is not marked failed.
  - API/Type: `src/atlas_api_jobs.py:4140` - RTL gate failure reason reads blocked/human_gate statuses.
  - API/Type: `src/atlas_api_jobs.py:4485` - gate demotes failure to `blocked` or `error`.
  - API/Type: `src/atlas_api_jobs.py:1004` - downstream queued/pending dependents become blocked.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_worker_completion_without_stage_evidence_is_not_marked_green tests/test_pipeline_orchestrator_worker_integration.py::test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream tests/test_pipeline_orchestrator_worker_integration.py::test_rtl_stage_evidence_gate_rejects_placeholder_sources tests/test_pipeline_orchestrator_worker_integration.py::test_rtl_scaffold_without_verdict_is_not_marked_failed -q` exits 0.
  - [ ] Missing-evidence test asserts `rtl=error`, `lint=blocked`, DB `rtl-gen=error`, DB `lint=blocked`, and error contains "missing required evidence for rtl".
  - [ ] Blocked-stage test asserts `rtl=blocked`, `lint=blocked`, DB `rtl-gen=blocked`, DB `lint=blocked`, and `/api/pipeline/state` returns `rtl.state == "blocked"`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: missing evidence becomes error and blocks downstream
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 8 happy-negative: missing evidence"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_worker_completion_without_stage_evidence_is_not_marked_green -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: pytest exits 0; assertions prove owner `rtl` is error, downstream `lint` is blocked, and DB mirrors both.
    Evidence: .omo/ulw-loop/evidence/orchestrator-negative-http.txt

  Scenario: explicit blocked stage evidence remains blocked and scaffold stays non-failed
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 8 edge: blocked and scaffold"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream tests/test_pipeline_orchestrator_worker_integration.py::test_rtl_stage_evidence_gate_rejects_placeholder_sources tests/test_pipeline_orchestrator_worker_integration.py::test_rtl_scaffold_without_verdict_is_not_marked_failed -q; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: pytest exits 0; blocked owner remains blocked, placeholder verdict is rejected, and fresh scaffold is not failed.
    Evidence: .omo/ulw-loop/evidence/orchestrator-negative-http.txt
  ```

  Commit: YES | Message: `test(orchestrator): lock negative evidence demotions` | Files: [tests/test_pipeline_orchestrator_worker_integration.py, tests/test_atlas_pipeline_contract.py]

- [ ] 9. Capture required HTTP/UI evidence transcripts

  What to do: After Tasks 3-8 pass, capture the three required evidence transcripts. The positive file must include focused positive pytest output and a TestClient HTTP transcript proving `/api/pipeline/dispatch` plus `/api/jobs` completed only after valid evidence exists. The negative file must include focused negative pytest output and a TestClient HTTP/state/DB transcript proving owner error/blocked and downstream blocked. The UI file must include backend single-worker pytest output, frontend Vitest output, and a Chrome/Playwright smoke selecting orchestrator, observing blocked/failed UI state, switching back to single-worker, and recording cleanup.
  Must NOT do: Do not hand-write fake JSON into evidence files. Do not leave dev servers or browser processes running.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [final verification] | Blocked by: [3, 4, 5, 6, 7, 8]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:18` - positive HTTP evidence requirement.
  - Pattern:  `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:26` - negative HTTP evidence requirement.
  - Pattern:  `.omo/ulw-loop/019e8b3d-eb18-7c21-83d3-c959d41844ae/goals.json:34` - browser/API/CLI UI and single-worker evidence requirement.
  - Pattern:  `tests/test_pipeline_orchestrator_worker_integration.py:506` - TestClient setup helper for backend HTTP tests.
  - Pattern:  `tests/test_atlas_api_pipeline_state.py:23` - TestClient setup helper for state API tests.
  - Pattern:  `frontend/atlas/package.json:5` - frontend test scripts.
  - External: `https://playwright.dev/docs/screenshots` - screenshot capture.
  - External: `https://playwright.dev/docs/browsers` - Chrome channel/browser selection.
  - External: `https://playwright.dev/docs/trace-viewer-intro` - trace artifact evidence.

  Acceptance criteria (agent-executable only):
  - [ ] `test -s .omo/ulw-loop/evidence/orchestrator-positive-http.txt` exits 0 and the file contains `test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state`, `test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints`, and `completed`.
  - [ ] `test -s .omo/ulw-loop/evidence/orchestrator-negative-http.txt` exits 0 and the file contains `test_worker_completion_without_stage_evidence_is_not_marked_green`, `test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream`, `blocked`, and `error`.
  - [ ] `test -s .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt` exits 0 and the file contains `app-shell-font-select`, `exec-policy`, `session-routing`, `pipeline-stage-blocked`, and `single-worker`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```text
  Scenario: required positive and negative HTTP transcripts are complete
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence; { echo "Task 9 happy: final backend evidence"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_fans_out_to_other_worker_and_surfaces_handoff_state tests/test_pipeline_orchestrator_worker_integration.py::test_pipeline_dispatch_can_drive_real_agent_server_worker_endpoints -q; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_pipeline_orchestrator_worker_integration.py::test_worker_completion_without_stage_evidence_is_not_marked_green tests/test_pipeline_orchestrator_worker_integration.py::test_worker_reported_completed_with_blocked_stage_engine_blocks_downstream -q; echo "cleanup: mock workers closed by context managers; tmp_path IP roots removed by pytest"; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-positive-http.txt | tee -a .omo/ulw-loop/evidence/orchestrator-negative-http.txt'
    Expected: command exits 0; both evidence files include pytest output and cleanup receipt.
    Evidence: .omo/ulw-loop/evidence/orchestrator-positive-http.txt and .omo/ulw-loop/evidence/orchestrator-negative-http.txt

  Scenario: UI and single-worker smoke with Chrome or agent-browser fallback
    Tool:     playwright(real Chrome)
    Steps:    bash -lc 'set -o pipefail; mkdir -p .omo/ulw-loop/evidence /tmp/atlas-orch-smoke; { echo "Task 9 edge: UI/single-worker evidence"; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_exec_policy.py tests/test_atlas_api_pipeline_state.py::test_pipeline_run_policy_get_post_and_state_payload tests/test_atlas_api_pipeline_state.py::test_pipeline_dispatch_records_run_and_exec_mode -q; cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/app-shell-font-select.test.tsx __tests__/exec-policy.test.mjs __tests__/session-routing.test.mjs __tests__/pipeline-stage-blocked.test.tsx __tests__/agent-worker-status.test.tsx; echo "browser-smoke: start atlas_ui on 127.0.0.1:8765 with temp root, register user u/pw, open shell, select orchestrator in exec picker, assert /api/pipeline/run_policy exec_mode=orchestrator, render blocked and failed StageCard states from pipeline-state payload or component fixture, switch picker back to single-worker, assert /api/pipeline/run_policy exec_mode=single-worker"; echo "cleanup: terminate atlas_ui server, close Chrome context, remove /tmp/atlas-orch-smoke"; } 2>&1 | tee -a .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt'
    Expected: backend pytest and Vitest exit 0; evidence file contains browser-smoke action log, `orchestrator`, `blocked`, `failed`, and `single-worker`. If local Chrome is unavailable, executor must download and use agent-browser from https://github.com/vercel-labs/agent-browser and append the fallback command/result to the same evidence file.
    Evidence: .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt
  ```

  Commit: NO | Message: `test(orchestrator): capture stabilization evidence` | Files: [.omo/ulw-loop/evidence/orchestrator-positive-http.txt, .omo/ulw-loop/evidence/orchestrator-negative-http.txt, .omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
  - Command: `python3 - <<'PY'\nfrom pathlib import Path\nrequired = [\n'.omo/ulw-loop/evidence/orchestrator-positive-http.txt',\n'.omo/ulw-loop/evidence/orchestrator-negative-http.txt',\n'.omo/ulw-loop/evidence/orchestrator-ui-single-worker.txt',\n]\nfor path in required:\n    p = Path(path)\n    assert p.is_file() and p.stat().st_size > 0, path\nprint('plan evidence files present')\nPY`
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
  - Command: `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_exec_policy.py tests/test_atlas_api_pipeline_state.py tests/test_atlas_pipeline_contract.py tests/test_orchestrator_workers_route.py tests/test_pipeline_orchestrator_worker_integration.py -q`
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
  - Command: `cd frontend/atlas && ./node_modules/.bin/vitest run __tests__/app-shell-font-select.test.tsx __tests__/exec-policy.test.mjs __tests__/session-routing.test.mjs __tests__/agent-worker-status.test.tsx __tests__/pipeline-stage-blocked.test.tsx __tests__/pipeline-render-smoke.test.tsx __tests__/workers-sidebar-panel.test.jsx`
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced
  - Command: `git diff -- src/atlas_api_jobs.py tests/test_pipeline_orchestrator_worker_integration.py tests/test_atlas_api_pipeline_state.py tests/test_atlas_pipeline_contract.py frontend/atlas/pipeline-flow-stage.tsx frontend/atlas/pipeline-rail.tsx frontend/atlas/agent-worker-status.tsx frontend/atlas/__tests__ | sed -n '1,260p'`

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: .omo/plans/orchestrator-mode-stabilization-execution-waves.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
