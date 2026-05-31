# Atlas Lint Report Diagnostics UI

## TL;DR
> Summary:      Enhance the Atlas lint report pane so pyslang and Verilator diagnostics are compactly grouped by rule/error type, expandable on demand, and connected to an annotated source preview at the failing line.
> Deliverables:
> - Shared lint diagnostic helpers for grouping, path matching, and width-detail extraction.
> - Foldable diagnostic groups with counts in the lint report surface.
> - Diagnostic click-through state from report row to source preview.
> - Inline source annotation under the selected line, including width details when present.
> - Layout hardening plus focused Vitest, pytest, build, and real Chrome QA evidence.
> Effort:       Medium
> Risk:         Medium - the work spans three TSX components and must preserve an already dirty workspace.

## Scope
### Must have
- Preserve existing user/work-in-progress changes, especially `frontend/atlas/workflow-report.tsx` and the untracked tests `frontend/atlas/__tests__/workflow-report-click.test.tsx` and `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx`.
- Consume the current `/api/lint/report` payload shape from `src/atlas_ui.py`; do not require a backend schema migration for the UI feature.
- Group diagnostics across pyslang and Verilator by deterministic key:
  - `diagnostic.rule` or `diagnostic.code` when present.
  - For pyslang diagnostics without a rule, display `PYSLANG ERROR` or `PYSLANG WARNING` from the owning tool result and severity.
  - For malformed entries, display `DIAGNOSTIC` and keep the UI stable.
- Render each group as an accessible disclosure using `<details>/<summary>`, collapsed by default, with the group label and count always visible.
- Reveal all diagnostics in an expanded group; do not silently drop entries via the current `diagnostics.slice(0, 5)` behavior.
- Clicking a diagnostic with a path/file opens the preview at that file and line.
- The preview renders an annotation immediately under the selected source line containing severity, rule/group, file/line/column, the raw diagnostic message, source snippet when provided, and parsed width facts when available.
- Parse width facts from both existing optional fields (`expected_width`, `actual_width`, `lhs_width`, `rhs_width`, etc.) and common message text such as `left 32 bits, right 8 bits` or `expects 3 bits ... generates 32 bits`.
- Keep the industrial/utilitarian Atlas visual language: compact mono labels, restrained borders, no decorative cards, no oversized text.
- Add agent-executed evidence under `evidence/`.

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not rewrite the lint API, lint generator, or report JSON schema unless the compatibility tests reveal a regression that cannot be fixed in the frontend.
- Do not remove or revert unrelated dirty files listed by `git status`.
- Do not use broad visual redesigns, hero/marketing patterns, decorative gradients, or nested cards.
- Do not introduce a third-party UI component library.
- Do not make users manually inspect the UI as the only verification path; all QA must be driven by commands or browser automation.
- Do not hide diagnostics without a path; render them disabled/non-clickable with an explicit missing-location cue.
- Do not run `refresh=1` in browser QA against existing IPs unless the test explicitly intends to regenerate lint reports.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + Vitest/React Testing Library for frontend, pytest for API contract, Playwright real Chrome for browser QA.
- QA policy: every task has agent-executed scenarios
- Evidence: `evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Diagnostic helper contract and focused helper tests
- Task 2: API/report compatibility guard tests
- Task 6: Report pane layout constraints and overflow tests

Wave 2 (after Wave 1):
- Task 3: depends [1, 2]
- Task 5: depends [1]

Wave 3 (after Wave 2):
- Task 4: depends [1, 3, 5]
- Task 7: depends [3, 4, 5, 6]

Wave 4 (after Wave 3):
- Task 8: depends [1, 2, 3, 4, 5, 6, 7]

Critical path: Task 1 -> Task 3 -> Task 4 -> Task 7 -> Task 8

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1    | none       | 3, 4, 5, 8 | 2, 6 |
| 2    | none       | 3, 8 | 1, 6 |
| 3    | 1, 2       | 4, 7, 8 | 5 |
| 4    | 1, 3, 5    | 7, 8 | none |
| 5    | 1          | 4, 7, 8 | 3 |
| 6    | none       | 7, 8 | 1, 2 |
| 7    | 3, 4, 5, 6 | 8 | none |
| 8    | 1, 2, 3, 4, 5, 6, 7 | none | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Diagnostic Helper Contract

  What to do: Add a small typed helper module, preferably `frontend/atlas/lint-diagnostics.ts`, for lint diagnostic normalization. Implement `LintDiagnostic`, `LintDiagnosticGroup`, `diagnosticLocationPath`, `diagnosticGroupKey`, `groupLintDiagnostics`, `sameDiagnosticPath`, and `extractWidthFacts`. Write tests first in `frontend/atlas/__tests__/lint-diagnostics.test.ts` covering Verilator `rule`, pyslang fallback grouping, malformed diagnostics, relative path matching, and width extraction from fields and messages.
  Must NOT do: Do not move existing React rendering into this helper. Do not add dependencies. Do not parse arbitrary prose beyond conservative bit-width patterns.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [3, 4, 5, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace-lint-coverage.tsx:130` - current lint card reads raw `result.diagnostics`; helpers should replace ad hoc array handling.
  - Pattern:  `frontend/atlas/workflow-report.tsx:146` - current click handler only receives `path/file/line`; helper path/line functions should feed this.
  - API/Type: `workflow/lint/scripts/dut_lint_report.py:214` - Verilator diagnostics include `severity`, `rule`, `file`, `line`, `column`, `message`.
  - API/Type: `workflow/lint/scripts/dut_lint_report.py:303` - pyslang diagnostics currently include `severity`, `file`, `line`, `message` and usually no rule.
  - Test:     `frontend/atlas/package.json:5` - frontend test command is `vitest run`.
  - External: `https://verilator.org/guide/latest/warnings.html` - Verilator warnings use named warning/rule codes.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/lint-diagnostics.test.ts) | tee evidence/task-1-lint-diagnostics.log'` exits 0.
  - [ ] The helper test asserts `WIDTHTRUNC` and `WIDTHEXPAND` diagnostics group separately, two pyslang errors group under `PYSLANG ERROR`, and malformed diagnostics group under `DIAGNOSTIC`.
  - [ ] The helper test asserts width facts for `left 32 bits, right 8 bits` and `expects 3 bits ... generates 32 bits`.
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx tsc -p tsconfig.json --noEmit) | tee evidence/task-1-tsc.log'` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Helper groups mixed pyslang and Verilator diagnostics
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/lint-diagnostics.test.ts -t "groups mixed tool diagnostics") | tee evidence/task-1-lint-diagnostics.log'
    Expected: Command exits 0 and the log contains the focused test name plus passing assertions for WIDTHTRUNC, WIDTHEXPAND, PYSLANG ERROR, and DIAGNOSTIC.
    Evidence: evidence/task-1-lint-diagnostics.log

  Scenario: Helper tolerates malformed diagnostics
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/lint-diagnostics.test.ts -t "handles malformed diagnostics") | tee evidence/task-1-lint-diagnostics-error.log'
    Expected: Command exits 0 and confirms missing path/line/message entries do not throw and group under DIAGNOSTIC.
    Evidence: evidence/task-1-lint-diagnostics-error.log
  ```

  Commit: YES | Message: `test(atlas-lint): define diagnostic helpers` | Files: [`frontend/atlas/lint-diagnostics.ts`, `frontend/atlas/__tests__/lint-diagnostics.test.ts`]

- [ ] 2. API Compatibility Guard

  What to do: Extend `tests/test_atlas_lint_report_api.py` to lock the current payload contract that the frontend will consume: normalized `path`, preserved `rule`, `severity`, `column`, `message`, and `source` for Verilator diagnostics; preserved pyslang diagnostics without requiring a rule; missing or malformed diagnostics arrays returning a stable empty list. Only change `src/atlas_ui.py` if these tests expose a real compatibility bug.
  Must NOT do: Do not introduce a new API field requirement for width details. Do not run lint regeneration in this task.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [3, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_atlas_lint_report_api.py:15` - existing API test seeds `lint/dut_lint.json` and calls `/api/lint/report`.
  - API/Type: `src/atlas_ui.py:2431` - `_normalize_lint_tool_results` copies diagnostics and sets `path`.
  - API/Type: `src/atlas_ui.py:2504` - endpoint payload includes `tool_results`, counts, paths, and run metadata.
  - API/Type: `workflow/lint/scripts/dut_lint_report.py:395` - generated report exposes diagnostics under each tool result.
  - Test:     `tests/test_atlas_lint_report_api.py:80` - existing Verilator parser test shows `source` preservation expectations.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_lint_report_api.py -q | tee evidence/task-2-lint-api.log'` exits 0.
  - [ ] The new/updated test asserts a Verilator width diagnostic keeps `rule: "WIDTHTRUNC"`, `source`, and normalized `path`.
  - [ ] The new/updated test asserts a pyslang diagnostic without `rule` is still present and normalized.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: API preserves Verilator diagnostic details
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_lint_report_api.py -q -k "lint_report_api" | tee evidence/task-2-lint-api.log'
    Expected: Command exits 0 and the seeded WIDTHTRUNC diagnostic includes path, rule, column, message, and source in the response.
    Evidence: evidence/task-2-lint-api.log

  Scenario: API handles malformed diagnostics arrays
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_lint_report_api.py -q -k "malformed" | tee evidence/task-2-lint-api-error.log'
    Expected: Command exits 0 and malformed tool_results/diagnostics do not produce a 500 or non-list diagnostics.
    Evidence: evidence/task-2-lint-api-error.log
  ```

  Commit: YES | Message: `test(atlas-lint): lock lint report api diagnostics` | Files: [`tests/test_atlas_lint_report_api.py`, `src/atlas_ui.py` if required by failing test]

- [ ] 3. Foldable Diagnostic Groups

  What to do: Replace the flat diagnostic slice in `LintToolResultCard` with grouped diagnostics from Task 1. Render each group as `<details>` with a compact `<summary>` containing severity marker, group label, count, and tool name. The group body lists every diagnostic with file:line:column, message, optional source snippet, and a disabled visual state for diagnostics without a path. Keep long messages and commands constrained with `minWidth: 0`, `overflowWrap: "anywhere"`, and existing mono sizing. Add or adapt tests in `frontend/atlas/__tests__/workflow-report-click.test.tsx` for group labels/counts, collapsed/expanded behavior, and missing-location diagnostics.
  Must NOT do: Do not keep the old top-five truncation. Do not make group summaries ordinary divs; use native disclosure semantics.

  Parallelization: Can parallel: NO | Wave 2 | Blocks: [4, 7, 8] | Blocked by: [1, 2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace-lint-coverage.tsx:166` - current flat diagnostic list starts here and truncates to five.
  - Pattern:  `frontend/atlas/workspace-lint-coverage.tsx:276` - lint summary currently renders status cards and tool cards in compact grids.
  - Test:     `frontend/atlas/__tests__/workflow-report-click.test.tsx:113` - existing untracked test already expects grouped lint diagnostics by rule with counts.
  - External: `https://developer.mozilla.org/en-US/docs/Web/HTML/Element/details` - native details/summary disclosure behavior and accessibility.
  - External: `https://testing-library.com/docs/queries/byrole/` - use role/name queries for accessible summary/buttons where practical.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "groups lint diagnostics") | tee evidence/task-3-workflow-groups.log'` exits 0.
  - [ ] The test proves `WIDTH` count `2` and `UNUSED` count `1` render from one Verilator tool result.
  - [ ] The test proves diagnostics are hidden while their group is collapsed and visible after expanding the group.
  - [ ] The test proves a diagnostic without `path/file` renders but is not clickable.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Rule groups render counts and expand to diagnostics
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "groups lint diagnostics by rule with foldable counts") | tee evidence/task-3-workflow-groups.log'
    Expected: Command exits 0; WIDTH and UNUSED groups exist; WIDTH count is 2; expanding WIDTH reveals both width diagnostics.
    Evidence: evidence/task-3-workflow-groups.log

  Scenario: Missing-location diagnostics are stable
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "renders diagnostics without source paths") | tee evidence/task-3-workflow-groups-error.log'
    Expected: Command exits 0; diagnostic text is visible after expansion and click handler is not called for the missing-location row.
    Evidence: evidence/task-3-workflow-groups-error.log
  ```

  Commit: YES | Message: `feat(atlas-lint): group diagnostics by rule` | Files: [`frontend/atlas/workspace-lint-coverage.tsx`, `frontend/atlas/__tests__/workflow-report-click.test.tsx`]

- [ ] 4. Diagnostic Selection Routing

  What to do: In `WorkflowReportPane`, add selected lint diagnostic state separate from `selected` path and `focusLine`. On diagnostic click, normalize the path, set `selected`, set `focusLine`, set `selectedLintDiagnostic`, and force-read the file. When the user manually selects an artifact/file from the left rail or opens JSON/log buttons, clear the selected lint diagnostic and reset focus only when appropriate. Pass `lintDiagnostic={selectedLintDiagnostic}` into `PreviewPane`. Prefer a dedicated test file if needed to avoid conflicts with Task 3.
  Must NOT do: Do not break coverage report click handling. Do not clear the diagnostic on hover prefetch.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [7, 8] | Blocked by: [1, 3, 5]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workflow-report.tsx:101` - current state has only `selected` and `focusLine`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:146` - current `openLintDiagnostic` sets selected path and focus line.
  - Pattern:  `frontend/atlas/workflow-report.tsx:207` - file list click currently only sets selected path.
  - Pattern:  `frontend/atlas/workflow-report.tsx:232` - lint report callback is wired here.
  - Pattern:  `frontend/atlas/workflow-report.tsx:238` - preview receives path and focus line only today.
  - Test:     `frontend/atlas/__tests__/workflow-report-click.test.tsx:153` - existing untracked test expects selected diagnostic to reach the preview mock.
  - External: `https://testing-library.com/docs/user-event/intro/` - prefer `userEvent.setup()` for realistic click behavior in new interaction tests.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "passes the selected lint diagnostic") | tee evidence/task-4-diagnostic-routing.log'` exits 0.
  - [ ] The test asserts preview mock text includes `demo_ip/rtl/demo.sv|L7|Output port connection width mismatch`.
  - [ ] The test asserts `readAtlasAsyncResource` is called with `('file', 'demo_ip/rtl/demo.sv', true)`.
  - [ ] The test asserts clicking `open json` clears the selected lint diagnostic and previews the report JSON.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Clicking diagnostic opens source and passes diagnostic
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "passes the selected lint diagnostic into the source preview") | tee evidence/task-4-diagnostic-routing.log'
    Expected: Command exits 0; preview mock shows the RTL path, line 7, and selected diagnostic message.
    Evidence: evidence/task-4-diagnostic-routing.log

  Scenario: Opening report JSON clears stale diagnostic annotation
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "clears selected lint diagnostic") | tee evidence/task-4-diagnostic-routing-error.log'
    Expected: Command exits 0; preview mock shows report JSON path and `no lint diagnostic` after `open json`.
    Evidence: evidence/task-4-diagnostic-routing-error.log
  ```

  Commit: YES | Message: `feat(atlas-lint): route selected diagnostics to preview` | Files: [`frontend/atlas/workflow-report.tsx`, `frontend/atlas/__tests__/workflow-report-click.test.tsx` or a new focused test file]

- [ ] 5. Source Line Annotation

  What to do: Extend `PreviewPaneProps` and `FoldablePaneProps` with `lintDiagnostic?: LintDiagnostic | null`. Pass the prop from `PreviewPane` to `FoldablePane` only for text/source files. In `FoldablePane`, after the matching `.line-row[data-ln]`, render a compact annotation row with `data-testid="lint-diagnostic-annotation"`, rule/severity/tool metadata, message, source snippet, and width facts from Task 1. Match by normalized path when available and by line number; if the line is missing or mismatched, do not render an annotation. Keep line focus selection behavior intact.
  Must NOT do: Do not inject annotation into markdown/binary/html render branches. Do not use `dangerouslySetInnerHTML` for diagnostic message text.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [4, 7, 8] | Blocked by: [1]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/preview-pane.tsx:216` - current `FoldablePaneProps` has `path`, `body`, `lang`, `lineCount`, `focusLine`, `feedbackMode`.
  - Pattern:  `frontend/atlas/preview-pane.tsx:311` - focus-line effect selects and scrolls the row.
  - Pattern:  `frontend/atlas/preview-pane.tsx:383` - `renderLineRow` is the correct insertion point for an annotation immediately after the matching line.
  - Pattern:  `frontend/atlas/preview-pane.tsx:495` - current `PreviewPaneProps` lacks lint diagnostic data.
  - Pattern:  `frontend/atlas/preview-pane.tsx:780` - `PreviewPane` passes props down to `FoldablePane`.
  - Test:     `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx:55` - existing untracked test expects annotation under selected source line.
  - External: `https://testing-library.com/docs/queries/about/` - prefer accessible text/testid queries only where there is no semantic role.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/preview-pane-lint-annotation.test.tsx) | tee evidence/task-5-preview-annotation.log'` exits 0.
  - [ ] The annotation test asserts `WIDTH`, raw message, source snippet, and parsed width details are visible.
  - [ ] A negative test asserts no annotation renders when diagnostic path does not match the preview path.
  - [ ] A negative test asserts no annotation renders for a diagnostic with line `0` or missing line.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Annotation renders under matching source line
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/preview-pane-lint-annotation.test.tsx -t "renders the lint diagnostic explanation") | tee evidence/task-5-preview-annotation.log'
    Expected: Command exits 0; annotation contains WIDTH, message, source snippet, and width details.
    Evidence: evidence/task-5-preview-annotation.log

  Scenario: Annotation is suppressed for mismatched path or missing line
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/preview-pane-lint-annotation.test.tsx -t "does not render lint diagnostic annotation") | tee evidence/task-5-preview-annotation-error.log'
    Expected: Command exits 0; no `lint-diagnostic-annotation` element exists for mismatched path and missing line cases.
    Evidence: evidence/task-5-preview-annotation-error.log
  ```

  Commit: YES | Message: `feat(atlas-preview): annotate lint diagnostic lines` | Files: [`frontend/atlas/preview-pane.tsx`, `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx`, `frontend/atlas/lint-diagnostics.ts` if helper refinements are needed]

- [ ] 6. Layout Hardening

  What to do: Constrain the report/preview layout so expanded lint groups cannot push the preview off-screen or overflow horizontally. Keep `WorkflowReportPane` as a two-column layout, but ensure the right column is `minHeight: 0`, the lint summary has a bounded scroll region, and command/message rows use `minWidth: 0` plus wrapping/truncation. Add class names only where they clarify testing/styling. Add DOM tests for key style invariants and keep existing long-command test green.
  Must NOT do: Do not convert the report to a landing page or decorative card grid. Do not resize fonts by viewport width.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [7, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workflow-report.tsx:178` - current shell grid is `300px minmax(0, 1fr)` with `overflow: hidden`.
  - Pattern:  `frontend/atlas/workflow-report.tsx:231` - right column is flex column and hosts report summary plus preview.
  - Pattern:  `frontend/atlas/workspace-lint-coverage.tsx:230` - lint summary currently has no bounded height/overflow.
  - Pattern:  `frontend/atlas/workspace-lint-coverage.tsx:292` - tool cards already use auto-fit grid and compact gaps.
  - Pattern:  `frontend/atlas/styles.css:2663` - preview line rows use fixed grid columns and selection style.
  - Test:     `frontend/atlas/__tests__/workflow-report-click.test.tsx:79` - existing test checks long lint commands remain constrained.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "keeps long lint commands constrained") | tee evidence/task-6-layout.log'` exits 0.
  - [ ] Add/maintain a test asserting the lint summary container has `minHeight: 0` and `overflow` bounded to `auto` or an equivalent scroll-safe style.
  - [ ] Add/maintain a test asserting expanded diagnostic message rows wrap instead of forcing horizontal overflow.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Long commands and diagnostic text stay constrained
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "keeps long lint commands constrained") | tee evidence/task-6-layout.log'
    Expected: Command exits 0; long command rows have minWidth 0 and do not rely on unconstrained inline width.
    Evidence: evidence/task-6-layout.log

  Scenario: Expanded diagnostics do not displace preview
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/workflow-report-click.test.tsx -t "keeps preview visible with expanded lint groups") | tee evidence/task-6-layout-error.log'
    Expected: Command exits 0; report summary is scroll-bounded and preview mock remains mounted after expanding a large diagnostic group.
    Evidence: evidence/task-6-layout-error.log
  ```

  Commit: YES | Message: `fix(atlas-lint): constrain report layout` | Files: [`frontend/atlas/workflow-report.tsx`, `frontend/atlas/workspace-lint-coverage.tsx`, `frontend/atlas/styles.css` if classes are added, `frontend/atlas/__tests__/workflow-report-click.test.tsx`]

- [ ] 7. Focused Real Chrome Lint QA

  What to do: Add `scripts/atlas_lint_report_e2e.mjs` as a focused Playwright real Chrome check for the lint report. It must launch Chrome with `channel: 'chrome'` when available and fall back to bundled Chromium only with a clear log. It should use an already present diagnostic-bearing fixture such as `mctp_assembler`, navigate the Atlas Vite server to lint workflow, expand a width group such as `WIDTHTRUNC` or `WIDTHEXPAND`, click a diagnostic, assert the RTL source path/line renders, assert the annotation includes the raw message and parsed width facts, and save a screenshot to `evidence/task-7-lint-report-browser.png`.
  Must NOT do: Do not rely on visual/manual inspection alone. Do not mutate existing IP lint reports or run report refresh.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [8] | Blocked by: [3, 4, 5, 6]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `scripts/atlas_vite_e2e_verify.sh:53` - starts Atlas with `ATLAS_FRONTEND_MODE=vite` on an isolated port.
  - Pattern:  `scripts/atlas_vite_e2e.mjs:31` - existing Playwright flow creates a browser context, logs in, screenshots, and asserts rendered UI.
  - Pattern:  `doc/wiki/atlas-ui-playwright-screenshot-recipe-2026-05-23.md:14` - local runbook recommends system Chrome via Playwright `channel:'chrome'`.
  - API/Type: `mctp_assembler/lint/dut_lint.json` - existing fixture includes WIDTHTRUNC/WIDTHEXPAND diagnostics and matching RTL files.
  - External: `https://playwright.dev/docs/browsers#google-chrome--microsoft-edge` - official Playwright Chrome channel docs.
  - External: `https://playwright.dev/docs/screenshots` - official Playwright screenshot docs.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; ATLAS_E2E_PORT=3037 PYTHON=python3 SKIP_VITEST=1 scripts/atlas_vite_e2e_verify.sh | tee evidence/task-7-atlas-vite-e2e.log'` exits 0.
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; ATLAS_LINT_E2E_BASE=http://127.0.0.1:3037 ATLAS_LINT_E2E_IP=mctp_assembler ATLAS_LINT_E2E_SHOT=evidence/task-7-lint-report-browser.png node scripts/atlas_lint_report_e2e.mjs | tee evidence/task-7-lint-report-browser.log'` exits 0 against the running server from the previous command or an explicitly started equivalent server.
  - [ ] Browser log proves the selected diagnostic path is an RTL `.sv` path, the selected line number matches the diagnostic, and the annotation includes width bits.
  - [ ] Screenshot file `evidence/task-7-lint-report-browser.png` exists and is non-empty.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Real Chrome opens lint report, expands width group, and clicks diagnostic
    Tool:     playwright(real Chrome)
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; ATLAS_E2E_PORT=3037 PYTHON=python3 SKIP_VITEST=1 scripts/atlas_vite_e2e_verify.sh | tee evidence/task-7-atlas-vite-e2e.log; ATLAS_LINT_E2E_BASE=http://127.0.0.1:3037 ATLAS_LINT_E2E_IP=mctp_assembler ATLAS_LINT_E2E_SHOT=evidence/task-7-lint-report-browser.png node scripts/atlas_lint_report_e2e.mjs | tee evidence/task-7-lint-report-browser.log'
    Expected: Commands exit 0; browser log includes expanded WIDTHTRUNC or WIDTHEXPAND group, clicked diagnostic, source preview path, focused line, and annotation width facts.
    Evidence: evidence/task-7-lint-report-browser.png

  Scenario: Browser QA fails clearly when lint report is absent
    Tool:     playwright(real Chrome)
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; ATLAS_LINT_E2E_BASE=http://127.0.0.1:3037 ATLAS_LINT_E2E_IP=missing_ip_for_lint_e2e node scripts/atlas_lint_report_e2e.mjs | tee evidence/task-7-lint-report-browser-error.log'
    Expected: Command exits non-zero with a clear `IP directory not found` or `No dut_lint.json found yet` assertion message, not a timeout or unhandled exception.
    Evidence: evidence/task-7-lint-report-browser-error.log
  ```

  Commit: YES | Message: `test(atlas-lint): add browser diagnostic report qa` | Files: [`scripts/atlas_lint_report_e2e.mjs`]

- [ ] 8. Full Integration Gate

  What to do: Run the focused and full frontend checks after all implementation tasks. Fix any type/build/test fallout in the smallest relevant file. Confirm no unrelated dirty files were changed by comparing `git status --short` before and after. Record all evidence logs.
  Must NOT do: Do not squash or rewrite prior task commits unless a failed gate requires correcting the relevant task commit before final handoff.

  Parallelization: Can parallel: NO | Wave 4 | Blocks: [] | Blocked by: [1, 2, 3, 4, 5, 6, 7]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/package.json:5` - `build` and `test` scripts.
  - Pattern:  `frontend/atlas/vite.config.ts:33` - Vitest includes `__tests__/**/*.test.{ts,tsx}` with jsdom.
  - Pattern:  `scripts/atlas_vite_e2e_verify.sh:40` - existing e2e script runs tsc, vitest, build, server, and browser smoke.
  - Test:     `frontend/atlas/__tests__/workflow-report-click.test.tsx` - focused workflow report behavior.
  - Test:     `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx` - focused preview annotation behavior.
  - Test:     `tests/test_atlas_lint_report_api.py` - backend/API compatibility guard.

  Acceptance criteria (agent-executable only):
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/lint-diagnostics.test.ts __tests__/workflow-report-click.test.tsx __tests__/preview-pane-lint-annotation.test.tsx) | tee evidence/task-8-focused-vitest.log'` exits 0.
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_lint_report_api.py -q | tee evidence/task-8-pytest.log'` exits 0.
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx tsc -p tsconfig.json --noEmit && npm run build && npm test) | tee evidence/task-8-frontend-full.log'` exits 0.
  - [ ] `bash -lc 'set -o pipefail; mkdir -p evidence; ATLAS_E2E_PORT=3038 PYTHON=python3 scripts/atlas_vite_e2e_verify.sh | tee evidence/task-8-atlas-vite-e2e.log'` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  ```
  Scenario: Focused lint report regression suite passes
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; (cd frontend/atlas && npx vitest run __tests__/lint-diagnostics.test.ts __tests__/workflow-report-click.test.tsx __tests__/preview-pane-lint-annotation.test.tsx) | tee evidence/task-8-focused-vitest.log'
    Expected: Command exits 0 with all focused lint report tests passing.
    Evidence: evidence/task-8-focused-vitest.log

  Scenario: Full frontend and API gates pass
    Tool:     bash
    Steps:    bash -lc 'set -o pipefail; mkdir -p evidence; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_lint_report_api.py -q | tee evidence/task-8-pytest.log; (cd frontend/atlas && npx tsc -p tsconfig.json --noEmit && npm run build && npm test) | tee evidence/task-8-frontend-full.log'
    Expected: Commands exit 0; no TypeScript, build, Vitest, or API regressions remain.
    Evidence: evidence/task-8-frontend-full.log
  ```

  Commit: YES | Message: `fix(atlas-lint): satisfy diagnostic report gates` | Files: [only files needed to fix failures from Tasks 1-7]

## Final verification wave (MANDATORY - after all implementation tasks)
> Runs in PARALLEL. ALL must APPROVE. Surface results to the caller and wait for an explicit "okay" before declaring complete.
- [ ] F1. Plan compliance audit - every task done, every acceptance criterion met
- [ ] F2. Code quality review - diagnostics clean, idioms match, no dead code
- [ ] F3. Real manual QA - every QA scenario executed with evidence captured
- [ ] F4. Scope fidelity - nothing extra shipped beyond Must-Have, nothing Must-NOT-Have introduced

## Commit strategy
- One logical change per commit. Conventional Commits (`<type>(<scope>): <subject>` body + footer).
- Atomic: every commit builds and passes tests on its own.
- No "WIP" / "fix typo squash later" commits on the final branch - clean up before merge.
- Reference the plan file path in the final commit footer: `Plan: plans/lint-report-diagnostics.md`.
- Because the workspace is already dirty, each executor must record `git status --short` before editing and must not revert unrelated changes.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
