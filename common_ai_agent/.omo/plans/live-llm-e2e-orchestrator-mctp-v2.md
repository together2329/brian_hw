# Live LLM E2E Orchestrator MCTP Contract V2

## TL;DR
> **Summary**: Add a gated live E2E lane that proves a real Atlas orchestrator LLM can run the MCTP contract-v2 closure path through real server/worker processes, inspect deterministic validator evidence, and route a controlled failure to the owning workflow.
> **Deliverables**:
> - Live E2E pytest for command/headless orchestrator path.
> - Live E2E Playwright/API smoke for UI orchestrator mode.
> - Isolated MCTP fixture copy with freshness checks.
> - Positive contract-v2 closure assertion: `contract_check=pass`, reflection `7/7`, evidence `91/91`.
> - Negative owner-routing assertion: controlled missing observable routes to `tb-gen`.
> - Runbook command for local live LLM execution.
> **Effort**: Medium
> **Parallel**: YES - 3 waves
> **Critical Path**: Task 1 -> Task 2 -> Task 4 -> Task 6 -> Task 8 -> Final Verification

## Context

### Original Request
Plan a live LLM-based E2E test that checks whether the orchestrator mode and MCTP contract-v2 loop really work end to end.

### Interview Summary
- User wants to prove the concept we discussed: locked truth closes through requirement, obligation, contract_ref, stage reflection, evidence, and deterministic validation.
- User previously clarified that mock-only proof is not enough.
- User wants orchestrator mode and UI behavior included, but the first live E2E must be bounded enough to run locally without turning into full production signoff.

### Metis Review (gaps addressed)
- **Live boundary clarified**: this plan requires real Atlas server, real worker dispatch, and real model call. In-process mocks are only allowed in existing unit tests, not this E2E.
- **Freshness risk addressed**: the live test copies `mctp_assembler_scratch` into an isolated temp root, deletes old signoff reports in the copy, runs `contract-check`, and asserts report timestamps/mtimes are new.
- **Owner routing addressed**: positive pass cannot prove owner routing because `run_contract_check.py` only classifies owners on non-pass. A separate broken-copy negative case is mandatory.
- **Cost/flakiness addressed**: live lane is skipped unless `ATLAS_RUN_LIVE_LLM_ORCH_E2E=1`; max wall time, max steps, and no retry-repair loops are required.
- **Authority clarified**: final pass/fail is from `run_contract_check.py` exit code plus JSON reports, not the LLM final prose.

## Work Objectives

### Core Objective
Prove that a live LLM orchestrator can dispatch and interpret the existing MCTP contract-v2 gate while deterministic validators remain the source of pass/fail truth.

### Deliverables
- `tests/test_live_llm_orchestrator_contract_v2_e2e.py`
- Optional helper under `tests/live_e2e_helpers.py` only if it prevents duplication.
- Optional runbook under `doc/wiki/live-llm-orchestrator-contract-v2-e2e.md`
- Evidence output under `.omo/evidence/live-llm-e2e/`

### Definition of Done
All of these must pass in a clean local run with live flag enabled:

```bash
ATLAS_RUN_LIVE_LLM_ORCH_E2E=1 \
PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
python3 -m pytest tests/test_live_llm_orchestrator_contract_v2_e2e.py -q
```

The test must prove:
- `src/atlas_ui.py` or `src/atlas_runtime_run.py --exec orchestrator` starts as a real subprocess.
- A real orchestrator run is created through `/api/pipeline/orchestrator/chat`.
- The orchestrator run detail endpoint returns persisted steps from `/api/orchestrator/runs/{run_id}`.
- Steps include `read_pipeline_state`, `dispatch_workflow`, and `read_artifact` or equivalent persisted tool evidence for `contract-check`.
- A real contract-check worker/stage runs and writes fresh reports.
- Positive fixture reports:
  - `contract_check.json.status == "pass"`
  - `contract_check.json.summary.reflection_passed == 7`
  - `contract_check.json.summary.reflection_total == 7`
  - `contract_check.json.summary.evidence_passed == 91`
  - `contract_check.json.summary.evidence_total == 91`
  - `contract_reflection_coverage.json.status == "pass"`
  - `evidence_contract_coverage.json.status == "pass"`
- Negative fixture reports:
  - `contract_check.json.status != "pass"`
  - `contract_owner_routing.json.owner_workflow == "tb-gen"`
  - `contract_owner_routing.json.rerun_after_repair` includes `tb`, `sim`, and `contract-check`.

### Must Have
- Test is skipped unless `ATLAS_RUN_LIVE_LLM_ORCH_E2E=1`.
- Test must never print API key values.
- Test must run in a temp `HOME`, temp project root, and temp DB path.
- Test must copy `mctp_assembler_scratch`; it must not mutate tracked reference artifacts.
- Test must remove old copied `signoff/contract_check.json`, `signoff/contract_reflection_coverage.json`, `signoff/evidence_contract_coverage.json`, and `signoff/contract_owner_routing.json` before running.
- Test must assert freshness by comparing report mtimes to a captured `run_started_at`.
- Test must cap wall time at 20 minutes and orchestrator steps at 20.
- Test must capture server logs and scrub secrets before writing evidence.

### Must NOT Have
- No default CI execution.
- No fake model, scripted LLM, TestClient, or monkeypatched worker dispatch in the live E2E.
- No hand-editing generated signoff artifacts to force green.
- No full STA/PNR/DFT/CDC/PPA/formal production claim.
- No infinite repair loop. A failed or blocked owner route is acceptable evidence if deterministic and correctly routed.

## Verification Strategy
> ZERO HUMAN INTERVENTION - all verification is agent-executed.
- Test decision: tests-after for live E2E, because deterministic contract-v2 unit tests already exist and live LLM behavior is expensive/flaky.
- QA policy: every task has one positive and one failure/edge scenario.
- Evidence: `.omo/evidence/live-llm-e2e/task-{N}-*.{json,log,png}`

## Execution Strategy

### Parallel Execution Waves
Wave 1: Task 1, Task 2, Task 3
Wave 2: Task 4, Task 5, Task 6
Wave 3: Task 7, Task 8, Task 9
Final: F1-F4

### Dependency Matrix
- Task 1 blocks Task 4, Task 5, Task 6, Task 8.
- Task 2 blocks Task 4 and Task 6.
- Task 3 blocks Task 5.
- Task 4 blocks Task 6 and Task 8.
- Task 5 blocks Task 8.
- Task 6 blocks Task 7 and Task 8.
- Task 7 blocks Task 9.
- Task 8 blocks Task 9.

## TODOs

- [ ] 1. Build Live E2E Fixture Isolation

  **What to do**: Add fixture helpers in `tests/test_live_llm_orchestrator_contract_v2_e2e.py` that create a temp `HOME`, temp project root, temp Atlas DB path, and copy `mctp_assembler_scratch` into that temp root. Delete copied contract signoff reports before every run. Record `run_started_at`.

  **Must NOT do**: Do not modify tracked `mctp_assembler_scratch`. Do not rely on existing pass reports without rerunning validators.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4, 5, 6, 8 | Blocked By: none

  **References**:
  - Pattern: `tests/test_db_full_stack_e2e.py:72` - temp HOME and live subprocess fixture style.
  - Pattern: `tests/test_contract_check_command.py:49` - positive contract-check fixture expectations.
  - Pattern: `tests/test_contract_check_command.py:97` - stale cached signoff must not be accepted.
  - Existing artifact: `mctp_assembler_scratch/signoff/contract_check.json` - current reference summary.

  **Acceptance Criteria**:
  - [ ] Fixture creates `tmp_path / "project" / "mctp_assembler_scratch"`.
  - [ ] Fixture deletes copied signoff reports before running.
  - [ ] Fixture writes an evidence manifest at `.omo/evidence/live-llm-e2e/task-1-fixture.json`.
  - [ ] Test helper refuses absolute IP paths and reports the temp root used.

  **QA Scenarios**:
  ```text
  Scenario: Positive isolated copy
    Tool: pytest
    Steps: run fixture-only smoke with live flag unset using a small internal test helper.
    Expected: copied IP exists in temp root; tracked source tree is unchanged; deleted reports are absent in the copy.
    Evidence: .omo/evidence/live-llm-e2e/task-1-fixture.json

  Scenario: Stale report guard
    Tool: pytest
    Steps: precreate copied signoff/contract_check.json before fixture cleanup.
    Expected: fixture removes it and records cleanup in manifest.
    Evidence: .omo/evidence/live-llm-e2e/task-1-stale-guard.json
  ```

  **Commit**: YES | Message: `test(e2e): isolate live mctp contract fixture` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 2. Add Live Lane Gate And Secret-Safe Preflight

  **What to do**: Gate the live E2E with `pytest.mark.skipif(os.getenv("ATLAS_RUN_LIVE_LLM_ORCH_E2E") != "1", ...)`. Add preflight that checks model availability by env names only, not values. Accept existing local config, but require either `LLM_MODEL_NAME`, `OPENCODE_MODEL`, `ATLAS_ORCHESTRATOR_MODEL`, or `ATLAS_HEADLESS_LLM_MODEL` to resolve to a non-empty model name. Require at least one known API key env name to be present without printing its value.

  **Must NOT do**: Do not require one provider only. Do not print API keys or `.env` contents.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 4, 6 | Blocked By: none

  **References**:
  - Pattern: `tests/test_real_glm51_headless_flow.py:31` - live real LLM skip gate style.
  - Pattern: `tests/test_db_full_stack_e2e.py:82` - subprocess env setup.
  - Existing config: `.env.example` - model and worker env names, but never use secret values in logs.

  **Acceptance Criteria**:
  - [ ] Without `ATLAS_RUN_LIVE_LLM_ORCH_E2E=1`, pytest reports skip.
  - [ ] With flag set but no model/key env, pytest skips with a clear reason.
  - [ ] Preflight output includes env key names only.
  - [ ] Evidence file records model name, provider key name presence, and redacted status.

  **QA Scenarios**:
  ```text
  Scenario: Live gate disabled
    Tool: bash
    Steps: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_live_llm_orchestrator_contract_v2_e2e.py -q
    Expected: skipped, no subprocess started.
    Evidence: .omo/evidence/live-llm-e2e/task-2-skip.log

  Scenario: Secret-safe enabled preflight
    Tool: bash
    Steps: run with ATLAS_RUN_LIVE_LLM_ORCH_E2E=1 and existing env.
    Expected: output does not contain API key values; only names/presence.
    Evidence: .omo/evidence/live-llm-e2e/task-2-preflight.json
  ```

  **Commit**: YES | Message: `test(e2e): gate live llm orchestrator lane` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 3. Lock The Deterministic Contract V2 Oracle

  **What to do**: Add helper assertions that run:

  ```bash
  python3 workflow/contract-reflection/scripts/run_contract_check.py mctp_assembler_scratch --root <temp-project-root>
  ```

  Then assert the mandatory JSON fields in `signoff/contract_check.json`, `signoff/contract_reflection_coverage.json`, and `signoff/evidence_contract_coverage.json`.

  **Must NOT do**: Do not let a live LLM final message count as pass. The helper must fail if JSON reports are missing or stale.

  **Parallelization**: Can Parallel: YES | Wave 1 | Blocks: 5 | Blocked By: none

  **References**:
  - Command owner: `workflow/contract-reflection/scripts/run_contract_check.py:172` - runs overlay, reflection, evidence, and owner classification.
  - Report shape: `workflow/contract-reflection/scripts/run_contract_check.py:129` - writes `contract_check.json`.
  - Stage owner: `workflow/STAGE_MANIFEST.json:151` - `contract-check` inputs and outputs.
  - Current expected summary: `mctp_assembler_scratch/signoff/contract_check.json`.

  **Acceptance Criteria**:
  - [ ] Positive temp copy exits `0`.
  - [ ] `contract_check.json.status == "pass"`.
  - [ ] `reflection=7/7` and `evidence=91/91`.
  - [ ] Report mtimes are greater than or equal to `run_started_at`.

  **QA Scenarios**:
  ```text
  Scenario: Positive deterministic closure
    Tool: bash + jq
    Steps: run contract_check against temp copy.
    Expected: pass, 7/7 reflection, 91/91 evidence.
    Evidence: .omo/evidence/live-llm-e2e/task-3-contract-pass.json

  Scenario: Missing input is not stale pass
    Tool: bash + pytest
    Steps: remove temp verify/evidence_contract.json and rerun helper.
    Expected: nonzero exit, contract_check.json.status != pass.
    Evidence: .omo/evidence/live-llm-e2e/task-3-contract-stale-fail.json
  ```

  **Commit**: YES | Message: `test(e2e): assert mctp contract v2 oracle` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 4. Start Real Atlas Orchestrator Server In Orchestrator Mode

  **What to do**: Add a subprocess fixture that starts the live UI/server in orchestrator mode with a temp DB and project root. Prefer:

  ```bash
  python3 src/atlas_runtime_run.py --host 127.0.0.1 --port <free-port> --root <temp-project-root> --exec orchestrator
  ```

  If `atlas_runtime_run.py` does not expose the needed behavior in tests, fall back to:

  ```bash
  ATLAS_EXEC_MODE=orchestrator python3 src/atlas_ui.py --host 127.0.0.1 --port <free-port>
  ```

  Set `ATLAS_WORKER_TRANSPORT=ipc`, `ATLAS_LAZY_WORKERS=0`, `ATLAS_WORKER_WARM_POOL=0`, `ATLAS_MULTI_USER=1`, `ATLAS_ADMIN_AUTH_MODE=local`, `PYTHONUNBUFFERED=1`, and `PYTHONPATH` from the parent process.

  **Must NOT do**: Do not use TestClient. Do not use mocked worker dispatch. Do not share the developer's normal Atlas DB.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 6, 8 | Blocked By: 1, 2

  **References**:
  - Server pattern: `tests/test_db_full_stack_e2e.py:97` - live `atlas_ui.py` subprocess.
  - Orchestrator mode: `src/atlas_runtime_run.py:1038` - `--exec orchestrator`.
  - Orchestrator worker behavior: `src/atlas_runtime_run.py:931` - orchestrator lazy/IPC mode setup.
  - Worker entrypoint: `src/main.py:3081` - `--serve`, and `src/main.py:3089` - `--all-workflows`.

  **Acceptance Criteria**:
  - [ ] `/healthz` returns HTTP 200.
  - [ ] `/api/pipeline/run_policy` reports `exec_mode == "orchestrator"` after setting policy if needed.
  - [ ] Server log is captured to evidence and redacted.
  - [ ] Teardown terminates process and frees port.

  **QA Scenarios**:
  ```text
  Scenario: Server starts in orchestrator mode
    Tool: httpx/curl
    Steps: start server, GET /healthz, GET /api/pipeline/run_policy.
    Expected: health 200, exec mode orchestrator.
    Evidence: .omo/evidence/live-llm-e2e/task-4-server.json

  Scenario: Port/process cleanup
    Tool: bash
    Steps: after fixture teardown, attempt TCP connect to server port.
    Expected: connection refused; no orphan process from fixture PID.
    Evidence: .omo/evidence/live-llm-e2e/task-4-cleanup.log
  ```

  **Commit**: YES | Message: `test(e2e): launch atlas orchestrator process` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 5. Add Negative Owner-Routing Contract Fixture

  **What to do**: In a temp copy only, remove one required RTL observed field from the MCTP evidence rows or use the established compact fixture pattern from `tests/test_contract_check_command.py`. Run `run_contract_check.py` and assert owner routing. Use the missing observable path so the expected owner is `tb-gen`.

  **Must NOT do**: Do not corrupt tracked `mctp_assembler_scratch`. Do not accept any non-pass without owner routing.

  **Parallelization**: Can Parallel: YES | Wave 2 | Blocks: 8 | Blocked By: 1, 3

  **References**:
  - Owner routing test: `tests/test_contract_check_command.py:74` - missing observable routes to `tb-gen`.
  - Owner classifier: `workflow/contract_reflection/owner_routing.py:70` - missing observable maps to `tb-gen`.
  - Rerun stages: `workflow/contract_reflection/owner_routing.py:93` - `tb-gen` rerun sequence.

  **Acceptance Criteria**:
  - [ ] Broken temp fixture exits nonzero.
  - [ ] `contract_check.json.status != "pass"`.
  - [ ] `contract_owner_routing.json.status == "blocked"`.
  - [ ] `contract_owner_routing.json.owner_workflow == "tb-gen"`.
  - [ ] Suggested commands include `/wf tb-gen` or `/ssot-tb-cocotb <ip>`.

  **QA Scenarios**:
  ```text
  Scenario: Missing observable routes to tb-gen
    Tool: pytest
    Steps: remove required observable from temp scoreboard row and run contract check.
    Expected: blocked, owner_workflow tb-gen.
    Evidence: .omo/evidence/live-llm-e2e/task-5-owner-route.json

  Scenario: Positive fixture does not fabricate owner route
    Tool: pytest
    Steps: run positive contract check and inspect owner route field.
    Expected: no non-empty owner_workflow on pass.
    Evidence: .omo/evidence/live-llm-e2e/task-5-no-route-on-pass.json
  ```

  **Commit**: YES | Message: `test(e2e): prove contract owner routing` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 6. Drive Real LLM Orchestrator Through Chat API

  **What to do**: Post a tight prompt to `/api/pipeline/orchestrator/chat` for `mctp_assembler_scratch` in the temp project root. The prompt must instruct the orchestrator to run only `contract-check`, read its artifacts, and finalize based on deterministic reports:

  ```text
  For IP mctp_assembler_scratch, verify the existing MCTP contract-v2 closure.
  Do not regenerate RTL/TB. Read pipeline state, dispatch contract-check only,
  wait for completion, read contract-check artifacts, then finalize completed
  only if contract_check.json passes with reflection 7/7 and evidence 91/91.
  ```

  Poll `/api/orchestrator/runs/{run_id}` until terminal, max 20 minutes. Assert persisted steps include tool calls, not only text. If the model times out or finalizes without tool evidence, the test fails.

  **Must NOT do**: Do not count a text answer as success. Do not allow the orchestrator to run full pipeline stages for this smoke.

  **Parallelization**: Can Parallel: NO | Wave 2 | Blocks: 7, 8 | Blocked By: 1, 2, 4

  **References**:
  - Chat API: `src/atlas_api_jobs.py:6160` - `/api/pipeline/orchestrator/chat`.
  - Run details: `src/atlas_api_jobs.py:6245` - `/api/orchestrator/runs/{run_id}`.
  - Dispatch bridge: `src/orchestrator/react_bridge.py:325` - `dispatch_workflow` tool.
  - Read pipeline state bridge: `src/orchestrator/react_bridge.py:319`.
  - Run completion logic: `src/orchestrator/react_bridge.py:1018` - orchestrator run loop.

  **Acceptance Criteria**:
  - [ ] POST returns `ok: true`, `run_id`, model, and reasoning effort.
  - [ ] Run terminal state is `completed`.
  - [ ] Steps include at least one `read_pipeline_state`.
  - [ ] Steps include `dispatch_workflow` with `stages` containing `contract-check` or workflow `contract-reflection`.
  - [ ] Steps include `read_artifact` or persisted evidence summary for `contract-check`.
  - [ ] `llm_calls` or equivalent DB trace records at least one real LLM call linked to the run.
  - [ ] Final result is rejected if reports are stale or missing.

  **QA Scenarios**:
  ```text
  Scenario: Live orchestrator closes contract-check
    Tool: httpx + jq
    Steps: POST chat prompt, poll run detail, inspect steps and reports.
    Expected: completed, real tool steps, fresh pass reports 7/7 and 91/91.
    Evidence: .omo/evidence/live-llm-e2e/task-6-live-orch-pass.json

  Scenario: LLM text-only fake green is rejected
    Tool: pytest
    Steps: use live run result that has no dispatch/read-artifact steps, if produced.
    Expected: test fails with "missing orchestrator tool evidence".
    Evidence: .omo/evidence/live-llm-e2e/task-6-text-only-rejected.json
  ```

  **Commit**: YES | Message: `test(e2e): drive live orchestrator contract check` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 7. Assert Worker/Job Evidence And No Mock Boundary

  **What to do**: After the live run, inspect `/api/pipeline/state?ip=mctp_assembler_scratch`, `/api/orchestrator/workers`, and the temp DB rows for `workflow_runs`. Assert that the contract-check job was created and reached `completed` or `blocked` according to the deterministic report. Assert `trigger_source` or persisted metadata links to the orchestrator run where available.

  **Must NOT do**: Do not infer worker execution from the LLM final message.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9 | Blocked By: 6

  **References**:
  - Pipeline state route: `src/atlas_api_jobs.py:5292`.
  - Worker snapshot route: `src/atlas_api_jobs.py:6845`.
  - Orchestrator dispatch bridge persists orchestrator run id: `src/atlas_api_jobs.py:6491`.
  - Artifact read list: `src/orchestrator/tools.py:916`.

  **Acceptance Criteria**:
  - [ ] Pipeline state includes contract-check stage status.
  - [ ] Worker/job trace includes `contract-reflection` or `contract-check`.
  - [ ] Job has terminal status matching report status.
  - [ ] No monkeypatch/mock markers appear in the live evidence manifest.

  **QA Scenarios**:
  ```text
  Scenario: Contract-check job is visible
    Tool: httpx + DB read
    Steps: query pipeline state, worker snapshot, and DB workflow_runs.
    Expected: contract-check job exists and is terminal.
    Evidence: .omo/evidence/live-llm-e2e/task-7-worker-trace.json

  Scenario: Missing job trace fails
    Tool: pytest
    Steps: simulate validation on a run detail without workflow_runs.
    Expected: assertion failure "no contract-check worker/job evidence".
    Evidence: .omo/evidence/live-llm-e2e/task-7-missing-worker-fail.json
  ```

  **Commit**: YES | Message: `test(e2e): assert live worker trace` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 8. Add UI Playwright Orchestrator Smoke

  **What to do**: Add a Playwright-backed test section that opens the live Atlas UI, ensures run policy is orchestrator mode, selects or uses `mctp_assembler_scratch`, sends the same orchestrator chat prompt, and verifies the UI displays a terminal state plus contract-check evidence links or stage status.

  **Must NOT do**: Do not make UI screenshot assertions the only source of pass/fail. UI validates visibility; JSON reports remain authority.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: 9 | Blocked By: 4, 5, 6

  **References**:
  - Browser fixture pattern: `tests/test_db_full_stack_e2e.py:45` - Playwright import/skip.
  - UI run policy call: `frontend/atlas/app.tsx:324` - `/api/pipeline/run_policy`.
  - UI orchestrator chat call: `frontend/atlas/pipeline-rail.tsx:514` - `/api/pipeline/orchestrator/chat`.
  - UI mode toggle: `frontend/atlas/pipeline-helpers.tsx:670` - orchestrator chip/policy behavior.

  **Acceptance Criteria**:
  - [ ] Browser reaches Atlas UI with HTTP 200.
  - [ ] UI policy shows or sets `exec_mode=orchestrator`.
  - [ ] UI sends orchestrator chat for `mctp_assembler_scratch`.
  - [ ] UI eventually renders terminal status or contract-check stage state.
  - [ ] Screenshot saved under evidence path.
  - [ ] JSON backend reports still satisfy Task 6 criteria.

  **QA Scenarios**:
  ```text
  Scenario: UI shows orchestrator contract-check result
    Tool: Playwright Chromium
    Steps: open UI, set orchestrator policy, send prompt, poll UI.
    Expected: visible orchestrator/contract-check terminal state and screenshot.
    Evidence: .omo/evidence/live-llm-e2e/task-8-ui-pass.png

  Scenario: UI blocked route is visible
    Tool: Playwright Chromium
    Steps: use broken temp fixture or precomputed negative run, poll pipeline UI.
    Expected: blocked/owner route text or stage status appears, no false completed UI.
    Evidence: .omo/evidence/live-llm-e2e/task-8-ui-blocked.png
  ```

  **Commit**: YES | Message: `test(e2e): verify orchestrator UI live path` | Files: `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

- [ ] 9. Add Operator Runbook And Evidence Scrubber

  **What to do**: Add a short wiki/runbook page that documents the live E2E purpose, required env flag, model/key preflight, exact commands, expected outputs, and cleanup. Add a small helper in the test file to scrub env-like secret patterns from saved logs before writing evidence.

  **Must NOT do**: Do not document secret values. Do not claim production signoff.

  **Parallelization**: Can Parallel: YES | Wave 3 | Blocks: Final | Blocked By: 7, 8

  **References**:
  - Existing live test docs: `tests/test_real_glm51_headless_flow.py:31`.
  - Existing full-stack live docstring: `tests/test_db_full_stack_e2e.py:1`.
  - Wiki index pattern: `doc/wiki/index.md`.
  - Wiki graph command: `python3 workflow/wiki/build_graph.py --check`.

  **Acceptance Criteria**:
  - [ ] Runbook includes command:
    `ATLAS_RUN_LIVE_LLM_ORCH_E2E=1 PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_live_llm_orchestrator_contract_v2_e2e.py -q`
  - [ ] Runbook states live LLM cost/time risk and skip behavior.
  - [ ] Runbook states deterministic validator authority.
  - [ ] Wiki graph passes with `broken_refs=0`.

  **QA Scenarios**:
  ```text
  Scenario: Runbook links are valid
    Tool: bash
    Steps: python3 workflow/wiki/build_graph.py --check.
    Expected: broken_refs=0.
    Evidence: .omo/evidence/live-llm-e2e/task-9-wiki-graph.log

  Scenario: Evidence logs are scrubbed
    Tool: pytest
    Steps: pass a fake line containing API_KEY=secret to scrubber.
    Expected: saved evidence contains API_KEY=[REDACTED].
    Evidence: .omo/evidence/live-llm-e2e/task-9-scrubbed.log
  ```

  **Commit**: YES | Message: `docs(e2e): document live orchestrator contract test` | Files: `doc/wiki/live-llm-orchestrator-contract-v2-e2e.md`, `doc/wiki/index.md`, `doc/wiki/log.md`, `doc/wiki/_graph.json`, `tests/test_live_llm_orchestrator_contract_v2_e2e.py`

## Final Verification Wave
> ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. Plan Compliance Audit

  Verify that all implemented files match this plan and no tracked MCTP artifact was mutated.

  ```bash
  git status --short
  git diff -- mctp_assembler_scratch
  ```

- [ ] F2. Deterministic Contract V2 Gate

  Verify the reference command still passes outside the live test:

  ```bash
  python3 workflow/contract-reflection/scripts/run_contract_check.py mctp_assembler_scratch --root .
  jq '.status, .summary' mctp_assembler_scratch/signoff/contract_check.json
  jq '.status, .summary' mctp_assembler_scratch/signoff/contract_reflection_coverage.json
  jq '.status, .summary' mctp_assembler_scratch/signoff/evidence_contract_coverage.json
  ```

- [ ] F3. Non-Live Regression Suite

  Run focused adjacent tests without live model calls:

  ```bash
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest \
    tests/test_contract_check_command.py \
    tests/test_contract_reflection_gate.py \
    tests/test_contract_reflection_stage_gate.py \
    tests/test_evidence_contract_artifact_rows.py \
    tests/test_worker_url_routing.py \
    tests/test_orchestrator_workers_route.py \
    -q
  ```

- [ ] F4. Live LLM E2E

  Run the new explicit live lane:

  ```bash
  ATLAS_RUN_LIVE_LLM_ORCH_E2E=1 \
  PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python3 -m pytest tests/test_live_llm_orchestrator_contract_v2_e2e.py -q
  ```

- [ ] F5. UI Evidence Review

  Confirm `.omo/evidence/live-llm-e2e/` includes:
  - server log
  - live run JSON
  - contract pass JSON
  - owner-route JSON
  - UI screenshot
  - redaction manifest

## Commit Strategy
- Commit after all final verification passes.
- Suggested commit message:

```text
test(e2e): add live llm orchestrator contract-v2 proof
```

## Success Criteria
- Live E2E proves a real LLM orchestrator can dispatch `contract-check` for MCTP.
- Deterministic reports prove actual closure: `7/7` reflection and `91/91` evidence.
- Controlled failure proves blocked owner routing to `tb-gen`.
- UI shows orchestrator mode and terminal contract-check status.
- No live test runs accidentally in default CI.
- No secrets are printed in evidence.
- No tracked MCTP evidence is mutated to manufacture a pass.
