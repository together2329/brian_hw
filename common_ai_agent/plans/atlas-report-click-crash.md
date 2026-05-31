# Atlas Report Click Crash Fix

## TL;DR
> Summary:      Fix the Atlas Vite/TSX report-tab crash by proving the stale window-bridge bug, then replacing module-load snapshots with late runtime resolution and explicit report bridge exports.
> Deliverables:
> - RED Vitest regression for late-registered report dependencies.
> - Report-click browser probe that fails on page errors and error banners.
> - Minimal Vite/TSX bridge fix for Lint Report and Coverage Report panes.
> - Automated and real-browser evidence under `evidence/`.
> Effort:       Medium
> Risk:         Medium - import-order/global-bridge behavior is brittle and current workspace comments conflict about legacy vs Vite source of truth.

## Scope
### Must have
- Target the Vite/TSX Atlas frontend path under `frontend/atlas/`; based on exploration, `frontend/atlas/main.tsx:1` identifies this as the Vite ES-module entry.
- Fix the workflow report tab rendered by `frontend/atlas/workspace-root.tsx:367`, not the standalone coverage tab rendered by `frontend/atlas/workspace-root.tsx:357`.
- Ensure both workflow values, `lint` and `coverage`, render their report panes without React crashes after the report tab is clicked.
- Preserve `window.WorkflowReportPane` and `window.WORKFLOW_REPORT_TABS` as transitional public bridge surfaces.
- Add an import-order regression where `workflow-report.tsx` is imported before `LintReportSummary`, `CoverageReportSummary`, `PreviewPane`, and `readAtlasAsyncResource` are present on `window`.
- Add browser evidence that clicking `lint report` and `coverage report` creates no `pageerror`, no `console.error` from React invalid element types, and no `#atlas-error-banner`.
- Work with the dirty worktree. Do not revert unrelated user changes shown by `git status --short`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not change `frontend/atlas/main.tsx` import order as the primary fix; the fix must tolerate current and future import order.
- Do not directly import `OrchestratorWorkflowPane` from `workspace-git-diff.tsx` inside `workflow-report.tsx`; that risks evaluating `workspace-git-diff.tsx:244` before `window.WorkflowReportPane` exists.
- Do not suppress `console.error`, `pageerror`, or the global error banner to hide the crash.
- Do not touch unrelated Sim Debug, VCD, backend, docs/wiki, or IP example changes already present in the dirty worktree.
- Do not create or edit `docs/shared/agent-tiers.md`; it was reported absent and is unrelated to this fix.
- Do not require manual user testing. All QA must be agent-executed.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + Vitest component regression + Playwright real-browser click probe
- QA policy: every task has agent-executed scenarios
- Evidence: `evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Ground current import-order failure and evidence ledger
- Task 2: Add RED Vitest late-bridge regression
- Task 3: Capture RED browser click-path evidence

Wave 2 (after Wave 1):
- Task 4: depends [1, 2] - expose missing report bridge globals
- Task 5: depends [1, 2] - late-bind `workflow-report.tsx` dependencies
- Task 6: depends [1, 3] - add report-click mode to browser harness

Wave 3 (after Wave 2):
- Task 7: depends [4, 5] - harden `workspace-git-diff` WorkflowReportPane bridge
- Task 8: depends [4, 5, 6, 7] - run targeted automated verification and commit
- Task 9: depends [8] - run localhost:3000 real-browser QA and package evidence

Critical path: Task 1 -> Task 2 -> Task 5 -> Task 7 -> Task 8 -> Task 9

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 4, 5, 6 | 2, 3 |
| 2    | none       | 4, 5, 8 | 1, 3 |
| 3    | none       | 6, 9 | 1, 2 |
| 4    | 1, 2       | 8 | 5, 6 |
| 5    | 1, 2       | 7, 8 | 4, 6 |
| 6    | 1, 3       | 8, 9 | 4, 5 |
| 7    | 4, 5       | 8 | none |
| 8    | 4, 5, 6, 7 | 9 | none |
| 9    | 8          | final | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Ground current import-order failure and evidence ledger

  What to do: Capture the current source evidence and dirty-worktree boundary before editing. Write `evidence/task-1-report-click-grounding.md` containing the hypothesis, exact source lines, current dirty files relevant to the task, and explicit unrelated dirty files to ignore. Record that the user stack trace is not available, so the plan proceeds from code evidence: top-level window snapshots in `workflow-report.tsx` plus later bridge registration.
  Must NOT do: Do not edit `frontend/atlas/**` in this task. Do not revert any dirty files.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 6] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/main.tsx:18` - `_react-global` loads first, then legacy-compatible module side effects.
  - Pattern:  `frontend/atlas/main.tsx:26` - `workflow-report` currently imports before `preview-pane` and `workspace`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:80` - current code snapshots window dependencies at module load.
  - Pattern:  `frontend/atlas/workflow-report.tsx:244` - report summaries are rendered from the snapshotted constants.
  - Pattern:  `frontend/atlas/workspace.tsx:251` - workspace window bridge block is the intended location for Vite globals.
  - Pattern:  `frontend/atlas/workspace.tsx:260` - `WORKFLOW_REPORT_TABS` is bridged, but report summary components are not.
  - Pattern:  `frontend/atlas/workspace-git-diff.tsx:242` - `WorkflowReportPane` is also snapshotted from `window`.
  - Test:     `frontend/atlas/__tests__/workspace-render-smoke.test.tsx:117` - existing dynamic import smoke pattern.
  - External: `https://react.dev/reference/react/Component#catching-rendering-errors-with-an-error-boundary` - render errors bubble to boundaries; event handler try/catch is not the fix.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f evidence/task-1-report-click-grounding.md`
  - [ ] `rg -n "workflow-report.tsx:80|workspace.tsx:251|workspace-git-diff.tsx:242|dirty worktree" evidence/task-1-report-click-grounding.md`

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: grounding evidence is complete
    Tool:     bash
    Steps:    mkdir -p evidence && { git status --short; nl -ba frontend/atlas/workflow-report.tsx | sed -n '78,90p;240,252p'; nl -ba frontend/atlas/workspace.tsx | sed -n '251,278p'; nl -ba frontend/atlas/workspace-git-diff.tsx | sed -n '238,246p'; } > evidence/task-1-report-click-grounding.raw.txt
    Expected: evidence/task-1-report-click-grounding.raw.txt contains `workflow-report.tsx` lines with `const LintReportSummary = w.LintReportSummary` and `workspace.tsx` bridge lines without `LintReportSummary`.
    Evidence: evidence/task-1-report-click-grounding.raw.txt

  Scenario: unrelated missing doc stays out of scope
    Tool:     bash
    Steps:    { test ! -e docs/shared/agent-tiers.md; echo "docs/shared/agent-tiers.md absent and out of scope"; } | tee evidence/task-1-report-click-grounding-error.txt
    Expected: command exits 0 and the evidence says the absent file is out of scope.
    Evidence: evidence/task-1-report-click-grounding-error.txt
  ```

  Commit: NO | Message: `test(atlas): capture report click crash baseline` | Files: [`evidence/task-1-report-click-grounding.md`, `evidence/task-1-report-click-grounding.raw.txt`]

- [ ] 2. Add RED Vitest late-bridge regression

  What to do: Create `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`. The test must `vi.resetModules()`, delete `window.LintReportSummary`, `window.CoverageReportSummary`, `window.PreviewPane`, `window.readAtlasAsyncResource`, import `../workflow-report.tsx` first, then assign those globals and render `WorkflowReportPane` for `workflow="lint"` and `workflow="coverage"`. Assert that late-registered summaries and `PreviewPane` render, and that hover/click paths call `readAtlasAsyncResource` without throwing. Run the test before source fixes and capture the expected RED failure.
  Must NOT do: Do not make the test pass by importing `workspace.tsx` before `workflow-report.tsx`. Do not stub `WorkflowReportPane` itself.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 5, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/__tests__/coverage-render-smoke.test.tsx:20` - dynamic import + render smoke shape.
  - Pattern:  `frontend/atlas/__tests__/workspace-render-smoke.test.tsx:117` - import-after-window-stubs pattern to invert for RED coverage.
  - API/Type: `frontend/atlas/workflow-report.tsx:89` - `WorkflowReportPaneProps` contract.
  - API/Type: `frontend/atlas/workspace-report-status.tsx:24` - lint report tab metadata shape.
  - API/Type: `frontend/atlas/workspace-report-status.tsx:38` - coverage report tab metadata shape.
  - Test:     `frontend/atlas/package.json:5` - `npm test` and direct `npx vitest run` are supported.
  - Test:     `frontend/atlas/vitest.config.js:4` - current Vitest config uses jsdom.
  - External: `https://testing-library.com/docs/user-event/intro/` - use realistic interactions where clicking/hovering matters.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`
  - [ ] Before Tasks 4-7, `bash -lc 'cd frontend/atlas; set +e; npx vitest run __tests__/workflow-report-late-bridge.test.tsx 2>&1 | tee ../../evidence/task-2-workflow-report-red.log; status=${PIPESTATUS[0]}; test "$status" -ne 0'`
  - [ ] `rg -n "late|LintReportSummary|CoverageReportSummary|readAtlasAsyncResource" frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: RED import-order regression fails before source fix
    Tool:     bash
    Steps:    mkdir -p evidence && bash -lc 'cd frontend/atlas; set +e; npx vitest run __tests__/workflow-report-late-bridge.test.tsx 2>&1 | tee ../../evidence/task-2-workflow-report-red.log; status=${PIPESTATUS[0]}; test "$status" -ne 0'
    Expected: command exits 0 because the Vitest command itself exits nonzero; log includes a React invalid element type or undefined component failure.
    Evidence: evidence/task-2-workflow-report-red.log

  Scenario: test does not rely on workspace import order
    Tool:     bash
    Steps:    rg -n "import\\('../workflow-report\\.tsx'\\)|import\\('../workspace\\.tsx'\\)" frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx | tee evidence/task-2-workflow-report-red-error.txt
    Expected: output includes `../workflow-report.tsx` and does not include `../workspace.tsx`.
    Evidence: evidence/task-2-workflow-report-red-error.txt
  ```

  Commit: NO | Message: `test(atlas): reproduce report pane late bridge crash` | Files: [`frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`]

- [ ] 3. Capture RED browser click-path evidence

  What to do: Use Playwright against a local Atlas server to prove the user-visible click path. Before the fix, drive `/?ip=gpio_pad&workflow=lint`, click the `lint report` tab, then drive `/?ip=gpio_pad&workflow=coverage`, click the `coverage report` tab. Capture page errors, console errors, `#atlas-error-banner`, and screenshots. This task may use a temporary ad-hoc Node script written under `evidence/`; do not change product or test harness files yet.
  Must NOT do: Do not kill an existing process on port 3000. Do not treat expected pre-auth HTTP errors as the report crash.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [6, 9] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace-rootui-rail-tabs.tsx:453` - workflow report tab chip click sets `mainTab` to `workflow_report`.
  - Pattern:  `frontend/atlas/workspace-rootui-rail-tabs.tsx:466` - chip text comes from `workflowReportMeta.label`, e.g. `lint report` and `coverage report`.
  - Pattern:  `frontend/atlas/app.tsx:223` - URL `ip` query param is parsed.
  - Pattern:  `frontend/atlas/app.tsx:226` - URL `workflow` query param is parsed.
  - Test:     `scripts/atlas_vite_e2e.mjs:58` - existing harness records console/page errors.
  - Test:     `scripts/atlas_vite_e2e.mjs:74` - existing harness screenshot pattern.
  - External: `https://playwright.dev/docs/locators` - use user-facing locators such as text/role for clicks.
  - External: `https://playwright.dev/docs/api/class-page#page-event-pageerror` - capture uncaught page exceptions.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f evidence/task-3-report-click-red.mjs`
  - [ ] `test -f evidence/task-3-report-click-red.log`
  - [ ] Before Tasks 4-7, the evidence log records a failing report-click condition: `PAGEERROR`, React invalid element type, `#atlas-error-banner present`, or equivalent uncaught crash.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: browser red probe captures report-click crash
    Tool:     bash
    Steps:    mkdir -p evidence/task-3-report-click-red-shots && ATLAS_E2E_BASE=${ATLAS_E2E_BASE:-http://127.0.0.1:3000} node evidence/task-3-report-click-red.mjs 2>&1 | tee evidence/task-3-report-click-red.log; test ${PIPESTATUS[0]} -ne 0
    Expected: command exits 0 because the probe exits nonzero before the fix; log names the report workflow and the crash signal.
    Evidence: evidence/task-3-report-click-red.log

  Scenario: no server available is classified separately from the UI crash
    Tool:     bash
    Steps:    ATLAS_E2E_BASE=http://127.0.0.1:9 node evidence/task-3-report-click-red.mjs 2>&1 | tee evidence/task-3-report-click-red-error.log; test ${PIPESTATUS[0]} -ne 0
    Expected: log contains `server unavailable` or `ECONNREFUSED`, not `report tab passed`.
    Evidence: evidence/task-3-report-click-red-error.log
  ```

  Commit: NO | Message: `test(atlas): capture report click browser crash` | Files: [`evidence/task-3-report-click-red.mjs`, `evidence/task-3-report-click-red.log`]

- [ ] 4. Expose missing report bridge globals

  What to do: Update `frontend/atlas/workspace.tsx` to import, re-export, and bridge the missing report dependencies: `readAtlasAsyncResource` from `workspace-async-resource.tsx`, `OrchestratorWorkflowPane` from `workspace-git-diff.tsx`, and `LintReportSummary` / `CoverageReportSummary` from `workspace-lint-coverage.tsx`. Assign them in the existing window bridge block near `workspace.tsx:251`. Update `frontend/atlas/types/atlas-window.d.ts` with permissive `any` entries for those names, matching the current file style.
  Must NOT do: Do not move `main.tsx` imports. Do not add a new dependency. Do not bridge unrelated helpers.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace.tsx:31` - report/status imports are grouped near the top.
  - Pattern:  `frontend/atlas/workspace.tsx:59` - async resource imports are grouped here; include `readAtlasAsyncResource`.
  - Pattern:  `frontend/atlas/workspace.tsx:146` - `workspace-git-diff` imports already exist; include `OrchestratorWorkflowPane` without removing `_statusGlyph`.
  - Pattern:  `frontend/atlas/workspace.tsx:149` - lint/coverage helper imports already exist; include `LintReportSummary` and `CoverageReportSummary`.
  - Pattern:  `frontend/atlas/workspace.tsx:251` - existing bridge block is the correct registration point.
  - API/Type: `frontend/atlas/workspace-async-resource.tsx:115` - `readAtlasAsyncResource` contract.
  - API/Type: `frontend/atlas/workspace-git-diff.tsx:103` - `OrchestratorWorkflowPane` contract.
  - API/Type: `frontend/atlas/workspace-lint-coverage.tsx:195` - `LintReportSummary` contract.
  - API/Type: `frontend/atlas/workspace-lint-coverage.tsx:447` - `CoverageReportSummary` contract.
  - API/Type: `frontend/atlas/types/atlas-window.d.ts:8` - ambient window typing style.

  Acceptance criteria (agent-executable only):
  - [ ] `rg -n "readAtlasAsyncResource|OrchestratorWorkflowPane|LintReportSummary|CoverageReportSummary" frontend/atlas/workspace.tsx frontend/atlas/types/atlas-window.d.ts`
  - [ ] `bash -lc 'cd frontend/atlas && npx tsc --noEmit'`
  - [ ] `bash -lc 'cd frontend/atlas && npx vitest run __tests__/workspace-render-smoke.test.tsx'`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: bridge names are exported and typed
    Tool:     bash
    Steps:    rg -n "w\\.(readAtlasAsyncResource|OrchestratorWorkflowPane|LintReportSummary|CoverageReportSummary)|readAtlasAsyncResource: any|OrchestratorWorkflowPane: any|LintReportSummary: any|CoverageReportSummary: any" frontend/atlas/workspace.tsx frontend/atlas/types/atlas-window.d.ts | tee evidence/task-4-report-bridge.log
    Expected: all four bridge names appear in both implementation and type surface.
    Evidence: evidence/task-4-report-bridge.log

  Scenario: unrelated bridge names were not bulk-added
    Tool:     bash
    Steps:    git diff -- frontend/atlas/workspace.tsx frontend/atlas/types/atlas-window.d.ts | tee evidence/task-4-report-bridge-error.diff
    Expected: diff contains only imports/exports/window assignments/types for the four report bridge dependencies and no unrelated panel/helper exports.
    Evidence: evidence/task-4-report-bridge-error.diff
  ```

  Commit: NO | Message: `fix(atlas): expose report pane bridge globals` | Files: [`frontend/atlas/workspace.tsx`, `frontend/atlas/types/atlas-window.d.ts`]

- [ ] 5. Late-bind `workflow-report.tsx` dependencies

  What to do: Update `frontend/atlas/workflow-report.tsx` so it no longer stores `OrchestratorWorkflowPane`, `LintReportSummary`, `CoverageReportSummary`, `PreviewPane`, or `readAtlasAsyncResource` in top-level constants. Resolve them inside render/callback paths from `window` at the moment they are needed. Add small in-pane fallback UI for a missing component that names the missing bridge and does not throw. Make `readAtlasAsyncResource` calls no-op safely if the bridge is absent, while still calling it when present. Keep `WORKFLOW_REPORT_TABS` lookup inside `WorkflowReportPane`.
  Must NOT do: Do not wrap render in `try/catch`. Do not hide errors by suppressing React or browser errors. Do not import `workspace-git-diff.tsx` from this file.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [7, 8] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workflow-report.tsx:57` - local cross-dependency type view of `window`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:80` - remove or replace the top-level dependency snapshots.
  - Pattern:  `frontend/atlas/workflow-report.tsx:94` - `WorkflowReportPane` is the render boundary.
  - Pattern:  `frontend/atlas/workflow-report.tsx:158` - diagnostic click uses `readAtlasAsyncResource`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:167` - orchestrator branch must also late-resolve.
  - Pattern:  `frontend/atlas/workflow-report.tsx:200` - refresh button calls `readAtlasAsyncResource`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:213` - artifact hover preloads the selected file.
  - Pattern:  `frontend/atlas/workflow-report.tsx:244` - lint/coverage summaries must render from late-resolved components.
  - Test:     `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx` - RED regression from Task 2.
  - External: `https://react.dev/reference/eslint-plugin-react-hooks/lints/error-boundaries` - rendering errors are not fixed with render-time `try/catch`.

  Acceptance criteria (agent-executable only):
  - [ ] `! rg -n "const (OrchestratorWorkflowPane|LintReportSummary|CoverageReportSummary|PreviewPane) = w\\." frontend/atlas/workflow-report.tsx`
  - [ ] `bash -lc 'cd frontend/atlas && npx vitest run __tests__/workflow-report-late-bridge.test.tsx'`
  - [ ] `bash -lc 'cd frontend/atlas && npx tsc --noEmit'`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: late bridge regression turns GREEN
    Tool:     bash
    Steps:    bash -lc 'mkdir -p evidence; cd frontend/atlas; npx vitest run __tests__/workflow-report-late-bridge.test.tsx 2>&1 | tee ../../evidence/task-5-workflow-report-green.log'
    Expected: command exits 0 and log reports all tests in `workflow-report-late-bridge.test.tsx` passing.
    Evidence: evidence/task-5-workflow-report-green.log

  Scenario: missing bridge renders fallback instead of throwing
    Tool:     bash
    Steps:    bash -lc 'cd frontend/atlas; npx vitest run __tests__/workflow-report-late-bridge.test.tsx -t "missing bridge" 2>&1 | tee ../../evidence/task-5-workflow-report-green-error.log'
    Expected: command exits 0 and assertion confirms missing `PreviewPane` or report summary produces visible fallback text, not a thrown React error.
    Evidence: evidence/task-5-workflow-report-green-error.log
  ```

  Commit: NO | Message: `fix(atlas): late-bind report pane dependencies` | Files: [`frontend/atlas/workflow-report.tsx`, `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`]

- [ ] 6. Add report-click mode to browser harness

  What to do: Extend `scripts/atlas_vite_e2e.mjs` with an opt-in `ATLAS_E2E_REPORT_CLICK=1` mode. After workspace render, navigate to `/?ip=gpio_pad&workflow=lint`, click the `lint report` chip, assert the report pane is visible and no error banner/pageerror appears, then repeat for `/?ip=gpio_pad&workflow=coverage` and `coverage report`. Store screenshots under `ATLAS_E2E_SHOTS` with distinct names, e.g. `04_lint_report.png` and `05_coverage_report.png`. Keep default behavior unchanged when the env var is absent.
  Must NOT do: Do not fail the existing default chat-handshake e2e path when `ATLAS_E2E_REPORT_CLICK` is not set. Do not hardcode a dependency on report artifacts existing; empty report states are acceptable if they render without crash.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8, 9] | Blocked by: [1, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/atlas_vite_e2e.mjs:24` - env-driven base URL pattern.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:31` - screenshot directory setup.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:58` - page creation and error capture.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:62` - console error capture.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:63` - pageerror capture.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:83` - error banner assertion on initial load.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:107` - screenshot after workspace render.
  - Pattern:  `frontend/atlas/workspace-rootui-rail-tabs.tsx:453` - report chip click handler.
  - Pattern:  `frontend/atlas/workspace-rootui-rail-tabs.tsx:466` - report chip label text.
  - External: `https://playwright.dev/docs/actionability` - `locator.click()` waits for visibility/enabled/actionability.
  - External: `https://playwright.dev/docs/screenshots` - screenshot evidence capture.

  Acceptance criteria (agent-executable only):
  - [ ] `rg -n "ATLAS_E2E_REPORT_CLICK|lint report|coverage report|04_lint_report|05_coverage_report" scripts/atlas_vite_e2e.mjs`
  - [ ] `ATLAS_E2E_REPORT_CLICK=0 ATLAS_E2E_BASE=http://127.0.0.1:9 node scripts/atlas_vite_e2e.mjs` still fails only because the server is unavailable, not because of syntax/runtime errors in the new branch.
  - [ ] With a running Atlas test server, `ATLAS_E2E_REPORT_CLICK=1 node scripts/atlas_vite_e2e.mjs` exits 0 after Tasks 4, 5, and 7.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: report-click harness branch is syntactically valid
    Tool:     bash
    Steps:    node --check scripts/atlas_vite_e2e.mjs 2>&1 | tee evidence/task-6-report-click-harness.log
    Expected: command exits 0.
    Evidence: evidence/task-6-report-click-harness.log

  Scenario: server-unavailable failure is explicit
    Tool:     bash
    Steps:    set +e; ATLAS_E2E_REPORT_CLICK=1 ATLAS_E2E_BASE=http://127.0.0.1:9 node scripts/atlas_vite_e2e.mjs 2>&1 | tee evidence/task-6-report-click-harness-error.log; status=${PIPESTATUS[0]}; test "$status" -ne 0
    Expected: command exits 0 because the script fails as expected; log contains connection/server failure rather than a JavaScript syntax error.
    Evidence: evidence/task-6-report-click-harness-error.log
  ```

  Commit: NO | Message: `test(atlas): exercise report tabs in browser e2e` | Files: [`scripts/atlas_vite_e2e.mjs`]

- [ ] 7. Harden `workspace-git-diff` WorkflowReportPane bridge

  What to do: Replace `frontend/atlas/workspace-git-diff.tsx:244` with a small exported wrapper component/function that late-resolves `window.WorkflowReportPane` at render time. If the global is missing, render a non-crashing fallback that says the workflow report pane is not registered. Add/extend Vitest coverage so importing `workspace-git-diff.tsx` before `workflow-report.tsx` does not permanently freeze `WorkflowReportPane` as undefined.
  Must NOT do: Do not import `workflow-report.tsx` from `workspace-git-diff.tsx`; keep the dependency direction one-way through the existing window bridge.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [8] | Blocked by: [4, 5]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace-git-diff.tsx:242` - current stale bridge export to replace.
  - Pattern:  `frontend/atlas/workspace-root.tsx:36` - root imports `WorkflowReportPane` through `workspace-git-diff.tsx`.
  - Pattern:  `frontend/atlas/workspace-root.tsx:367` - root renders imported `WorkflowReportPane`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:260` - `workflow-report.tsx` publishes `window.WorkflowReportPane`.
  - Test:     `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx` - add bridge-wrapper regression here or in a sibling test.

  Acceptance criteria (agent-executable only):
  - [ ] `! rg -n "export const WorkflowReportPane: any = \\(window as any\\)\\.WorkflowReportPane" frontend/atlas/workspace-git-diff.tsx`
  - [ ] `bash -lc 'cd frontend/atlas && npx vitest run __tests__/workflow-report-late-bridge.test.tsx'`
  - [ ] `bash -lc 'cd frontend/atlas && npx tsc --noEmit'`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: bridge wrapper late-resolves window.WorkflowReportPane
    Tool:     bash
    Steps:    bash -lc 'cd frontend/atlas; npx vitest run __tests__/workflow-report-late-bridge.test.tsx -t "workspace-git-diff" 2>&1 | tee ../../evidence/task-7-workflow-report-wrapper.log'
    Expected: command exits 0 and proves the wrapper renders fallback before the global exists and the real pane after the global is assigned.
    Evidence: evidence/task-7-workflow-report-wrapper.log

  Scenario: no import cycle was introduced
    Tool:     bash
    Steps:    rg -n "from './workflow-report'|from \"./workflow-report\"|import\\(.*workflow-report" frontend/atlas/workspace-git-diff.tsx | tee evidence/task-7-workflow-report-wrapper-error.log; test ! -s evidence/task-7-workflow-report-wrapper-error.log
    Expected: command exits 0 and evidence file is empty, proving `workspace-git-diff.tsx` does not import `workflow-report.tsx`.
    Evidence: evidence/task-7-workflow-report-wrapper-error.log
  ```

  Commit: NO | Message: `fix(atlas): late-bind workflow report bridge wrapper` | Files: [`frontend/atlas/workspace-git-diff.tsx`, `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`]

- [ ] 8. Run targeted automated verification and commit

  What to do: Run the targeted regression, workspace smoke, full frontend suite, typecheck, build, and isolated Vite E2E with the report-click mode enabled. If a verification command fails only because of unrelated pre-existing dirty worktree changes, capture the failure and do not claim completion; otherwise fix the report-click regression before proceeding. After green verification, make one logical commit containing Tasks 2, 4, 5, 6, and 7 source/test changes.
  Must NOT do: Do not include evidence files in the commit unless the repo already tracks evidence artifacts. Do not commit unrelated dirty files.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [9] | Blocked by: [4, 5, 6, 7]

  References (executor has NO interview context - be exhaustive):
  - Test:     `frontend/atlas/package.json:5` - frontend `test` script.
  - Test:     `frontend/atlas/tsconfig.json:23` - TypeScript include surface for migrated TSX.
  - Test:     `scripts/run_tests.sh:138` - `frontend` mode runs Vitest in `frontend/atlas`.
  - Test:     `scripts/atlas_vite_e2e_verify.sh:40` - typecheck gate.
  - Test:     `scripts/atlas_vite_e2e_verify.sh:46` - Vitest gate.
  - Test:     `scripts/atlas_vite_e2e_verify.sh:50` - Vite build gate.
  - Test:     `scripts/atlas_vite_e2e_verify.sh:53` - isolated server start gate.
  - Test:     `scripts/atlas_vite_e2e_verify.sh:64` - browser E2E gate.
  - Test:     `scripts/atlas_vite_e2e.mjs:62` - console errors are captured.
  - Test:     `scripts/atlas_vite_e2e.mjs:63` - page errors are captured.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'cd frontend/atlas && npx vitest run __tests__/workflow-report-late-bridge.test.tsx'`
  - [ ] `./scripts/run_tests.sh frontend`
  - [ ] `bash -lc 'cd frontend/atlas && npx tsc --noEmit'`
  - [ ] `bash -lc 'cd frontend/atlas && npm run build'`
  - [ ] `ATLAS_E2E_REPORT_CLICK=1 ATLAS_E2E_SHOTS=$PWD/evidence/task-8-vite-e2e-shots ./scripts/atlas_vite_e2e_verify.sh`
  - [ ] `git diff --cached --name-only` includes only `frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`, `frontend/atlas/workflow-report.tsx`, `frontend/atlas/workspace.tsx`, `frontend/atlas/workspace-git-diff.tsx`, `frontend/atlas/types/atlas-window.d.ts`, and `scripts/atlas_vite_e2e.mjs`.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: automated verification is green
    Tool:     bash
    Steps:    mkdir -p evidence/task-8-vite-e2e-shots && { bash -lc 'cd frontend/atlas && npx vitest run __tests__/workflow-report-late-bridge.test.tsx'; ./scripts/run_tests.sh frontend; bash -lc 'cd frontend/atlas && npx tsc --noEmit'; bash -lc 'cd frontend/atlas && npm run build'; ATLAS_E2E_REPORT_CLICK=1 ATLAS_E2E_SHOTS="$PWD/evidence/task-8-vite-e2e-shots" ./scripts/atlas_vite_e2e_verify.sh; } 2>&1 | tee evidence/task-8-automated-verification.log
    Expected: command exits 0; log includes Vitest pass, tsc 0 errors, build OK, and ATLAS vite E2E verified with report-click screenshots.
    Evidence: evidence/task-8-automated-verification.log

  Scenario: commit is scoped to the report-click fix
    Tool:     bash
    Steps:    git diff --name-only HEAD | sort | tee evidence/task-8-automated-verification-error.txt
    Expected: output is limited to planned files plus uncommitted unrelated pre-existing files; before committing, stage only planned files and confirm `git diff --cached --name-only` matches the acceptance list.
    Evidence: evidence/task-8-automated-verification-error.txt
  ```

  Commit: YES | Message: `fix(atlas): keep workflow report panes late-bound` | Files: [`frontend/atlas/__tests__/workflow-report-late-bridge.test.tsx`, `frontend/atlas/workflow-report.tsx`, `frontend/atlas/workspace.tsx`, `frontend/atlas/workspace-git-diff.tsx`, `frontend/atlas/types/atlas-window.d.ts`, `scripts/atlas_vite_e2e.mjs`]

- [ ] 9. Run localhost:3000 real-browser QA and package evidence

  What to do: Validate the exact user-reported surface, `localhost:3000`, with Playwright. If an Atlas server is already listening on port 3000, reuse it without killing it. If none is listening, start `ATLAS_FRONTEND_MODE=vite python3 src/atlas_ui.py --port 3000` and stop only the process started by this task. Run the report-click browser harness with `ATLAS_E2E_REPORT_CLICK=1`, capture screenshots, console/page errors, and a final log. Confirm `lint report` and `coverage report` both render without `#atlas-error-banner`.
  Must NOT do: Do not run `scripts/atlas_vite_e2e_verify.sh` with `ATLAS_E2E_PORT=3000` because that script kills listeners on its test port. Do not kill a user-owned port 3000 process.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [final] | Blocked by: [8]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/atlas_vite_e2e_verify.sh:53` - starts an isolated Atlas server; do not use its kill behavior on port 3000.
  - Pattern:  `scripts/atlas_vite_e2e_verify.sh:54` - explicitly kills listeners on the selected port; avoid this for user localhost:3000.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:24` - accepts `ATLAS_E2E_BASE`.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:28` - accepts `ATLAS_E2E_SHOTS`.
  - Pattern:  `frontend/atlas/workspace-rootui-rail-tabs.tsx:453` - click target is the workflow report chip.
  - External: `https://playwright.dev/docs/browsers` - use real Chrome channel when available; Chromium fallback is acceptable if Chrome is absent.
  - External: `https://playwright.dev/docs/trace-viewer` - retain trace/screenshot evidence for post-run inspection.

  Acceptance criteria (agent-executable only):
  - [ ] `test -f evidence/task-9-localhost-3000-qa.log`
  - [ ] `test -f evidence/task-9-localhost-3000-shots/04_lint_report.png`
  - [ ] `test -f evidence/task-9-localhost-3000-shots/05_coverage_report.png`
  - [ ] `! rg -n "PAGEERROR|#atlas-error-banner present|invalid element type|Element type is invalid|FAIL:" evidence/task-9-localhost-3000-qa.log`

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: localhost:3000 report tabs pass in a real browser
    Tool:     playwright(real Chrome)
    Steps:    mkdir -p evidence/task-9-localhost-3000-shots && bash -lc 'set -euo pipefail; started=""; if curl -fsS --max-time 2 http://127.0.0.1:3000/healthz >/dev/null; then echo "reusing existing localhost:3000"; else ATLAS_FRONTEND_MODE=vite python3 src/atlas_ui.py --port 3000 > evidence/task-9-localhost-3000-server.log 2>&1 & started=$!; for _ in $(seq 1 45); do curl -fsS --max-time 2 http://127.0.0.1:3000/healthz >/dev/null && break; sleep 1; done; fi; trap '"'"'if [ -n "${started:-}" ]; then kill "$started" 2>/dev/null || true; fi'"'"' EXIT; ATLAS_E2E_REPORT_CLICK=1 ATLAS_E2E_BASE=http://127.0.0.1:3000 ATLAS_E2E_SHOTS="$PWD/evidence/task-9-localhost-3000-shots" node scripts/atlas_vite_e2e.mjs' 2>&1 | tee evidence/task-9-localhost-3000-qa.log
    Expected: command exits 0; log says both report click paths passed; screenshots for lint and coverage exist; no pageerror or error banner appears.
    Evidence: evidence/task-9-localhost-3000-qa.log

  Scenario: missing localhost server startup failure is explicit and non-destructive
    Tool:     bash
    Steps:    rg -n "reusing existing localhost:3000|ATLAS_FRONTEND_MODE=vite|kill \"\\$started\"" evidence/task-9-localhost-3000-qa.log evidence/task-9-localhost-3000-server.log 2>/dev/null | tee evidence/task-9-localhost-3000-qa-error.txt
    Expected: evidence shows either an existing server was reused or only the task-started server PID was killed; no command killed an arbitrary port 3000 listener.
    Evidence: evidence/task-9-localhost-3000-qa-error.txt
  ```

  Commit: NO | Message: `test(atlas): verify report tabs on localhost 3000` | Files: [`evidence/task-9-localhost-3000-qa.log`, `evidence/task-9-localhost-3000-shots/04_lint_report.png`, `evidence/task-9-localhost-3000-shots/05_coverage_report.png`]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Also satisfy the repo Lore protocol by including decision trailers in the commit body: `Constraint:`, `Rejected:`, `Confidence:`, `Scope-risk:`, `Directive:`, `Tested:`, and `Not-tested:` when applicable.
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/atlas-report-click-crash.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
