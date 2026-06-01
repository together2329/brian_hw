# SSOT DOC Feedback Mode

## TL;DR
> Summary:      Add a production-grade SSOT DOC Feedback Mode where users can select rendered DOC components by click or drag, see the backing SSOT path/value through Show SSOT, and send anchored comments into the chat/composer so the SSOT can be revised.
> Deliverables:
> - Component-level `data-ssot-*` mapping in SSOT HTML export
> - Feedback selection/highlight engine for the DOC iframe
> - Show SSOT source tray with YAML path/value/history
> - Comment-to-chat prefill flow that reuses the existing workspace composer pattern
> - Backend source lookup API and expanded feedback payloads
> - Unit, route, component, and real Chrome QA evidence
> Effort:       Large
> Risk:         Medium - iframe DOM interaction plus SSOT source mapping touches frontend, export rendering, and backend route contracts.

## Scope
### Must have
- Feedback Mode in the SSOT DOC tab must allow selecting a rendered document component by click.
- Feedback Mode must allow drag-selecting or drag-dropping over the rendered document and keep a visible highlight on the selected target.
- The selected target must resolve to a stable SSOT source reference: section, YAML path, label, component kind, and current value where available.
- A Show SSOT button must display the selected source reference and YAML/value snippet without requiring the user to leave the DOC tab.
- A Comment action must place a structured message into the workspace chat/composer, focused and ready to send, with the selected DOC label, SSOT path, current value, selected text, and user comment.
- Apply Feedback must continue to persist feedback into the SSOT YAML and refresh the inline HTML export.
- The existing DOC tab iframe flow must continue using `/api/ssot/export?ip=<ip>&format=html&inline=1`.
- Tests must be TDD: each task starts by adding/adjusting a failing test or fixture proof, then makes the smallest production change to pass.
- New code must avoid growing oversized files. Prefer new focused files over expanding `frontend/atlas/ssot-doc.tsx` (currently 440 lines), `frontend/atlas/workspace-orchestrator-chat.tsx` (305 lines), and `src/atlas_ui.py` (10390 lines).

### Must NOT have (guardrails, anti-slop, scope boundaries)
- Do not rewrite the SSOT DOC tab as a landing page or marketing UI.
- Do not replace the existing `/api/ssot/doc-feedback` behavior; extend it compatibly.
- Do not auto-submit chat messages without explicit user action. The comment flow should prefill/focus the composer unless the existing workspace pattern explicitly supports a send confirmation.
- Do not add a large dependency for DOM mapping if the existing same-origin iframe DOM can be used directly.
- Do not mutate unrelated workspace tabs, SSOT QA board flows, or orchestrator worker behavior.
- Do not add broad refactors to `atlas_ui.py`; only thin route wiring is allowed there.
- Do not use brittle string-only tests as the only coverage for the new behavior.

## Verification strategy
> Zero human intervention - all verification is agent-executed.
- Test decision: TDD + pytest, Vitest/jsdom, and Playwright with real Chrome
- QA policy: every task has agent-executed scenarios
- Evidence: `evidence/task-<N>-<slug>.<ext>`

## Execution strategy
### Parallel execution waves
> Target 5-8 tasks per wave. <3 per wave (except final) = under-splitting.
> Extract shared dependencies as Wave-1 tasks to maximize parallelism.

Wave 1 (no dependencies):
- Task 1: Rebaseline DOC-tab tests and create the target frontend test harness
- Task 2: Add backend SSOT doc source mapping and lookup API
- Task 3: Add frontend feedback data models and API client helpers

Wave 2 (after Wave 1):
- Task 4: depends [2] - annotate the HTML export with `data-ssot-*` component references
- Task 5: depends [1, 3] - implement iframe hit-testing, drag targeting, and highlight overlay
- Task 6: depends [2, 3] - implement Show SSOT source tray and feedback panel component
- Task 7: depends [3] - wire SSOT DOC comment events into the existing workspace composer pattern

Wave 3 (after Wave 2):
- Task 8: depends [1, 2, 3, 4, 5, 6, 7] - integrate the DOC pane, polish UX, and add real Chrome end-to-end QA

Critical path: Task 2 -> Task 4 -> Task 5 -> Task 8

### Dependency matrix
| Task | Depends on | Blocks | Can parallelize with |
|------|------------|--------|----------------------|
| 1 | none | 5, 8 | 2, 3 |
| 2 | none | 4, 6, 8 | 1, 3 |
| 3 | none | 5, 6, 7, 8 | 1, 2 |
| 4 | 2 | 8 | 5, 6, 7 |
| 5 | 1, 3 | 8 | 4, 6, 7 |
| 6 | 2, 3 | 8 | 4, 5, 7 |
| 7 | 3 | 8 | 4, 5, 6 |
| 8 | 1, 2, 3, 4, 5, 6, 7 | final verification | none |

## Todos
> Implementation + Test = ONE task. Never separate.
> Every task MUST have: References + Acceptance Criteria + QA Scenarios + Commit.

- [ ] 1. Rebaseline DOC-tab tests and create the target frontend test harness

  What to do: Update stale DOC-tab Python tests so they read the live TSX files, then add focused Vitest fixtures for the future DOC Feedback Mode behavior. The first test run must fail for missing target behavior before production changes land: expected assertions include component selection state, Show SSOT button presence, and comment-to-chat event payload shape. Keep this task to tests/test utilities only.
  Must NOT do: Do not edit production source in this task except if a test import requires a zero-behavior test-id export in a new test-only helper; prefer test fixtures over production changes.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [5, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `tests/test_atlas_ssot_doc_tab.py:1` - stale test currently points at `workspace.jsx` and `ssot-doc.jsx`.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:68` - live `SsotDocPane` implementation.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:415` - iframe uses `data-testid="ssot-doc-frame"`.
  - Pattern:  `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx:46` - small component-test setup style.
  - Pattern:  `frontend/atlas/vitest.config.js:4` - Vitest jsdom configuration.
  - Test:     `frontend/atlas/package.json:5` - frontend `npm test` command.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_ssot_doc_tab.py -q | tee evidence/task-1-doc-tab-pytest.txt` exits 0 after stale paths are fixed.
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-target.test.tsx | tee ../../evidence/task-1-doc-feedback-target-vitest.txt` exits 0 after the target test harness is made meaningful and production tasks satisfy it.
  - [ ] `grep -R "ssot-doc.jsx\\|workspace.jsx" tests/test_atlas_ssot_doc_tab.py` exits nonzero and its output is captured in `evidence/task-1-stale-path-grep.txt`.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: stale tests now target the live TSX files
    Tool:     bash
    Steps:    mkdir -p evidence && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_atlas_ssot_doc_tab.py -q | tee evidence/task-1-doc-tab-pytest.txt
    Expected: Command exits 0 and the test output names tests/test_atlas_ssot_doc_tab.py without FileNotFoundError for .jsx files.
    Evidence: evidence/task-1-doc-tab-pytest.txt

  Scenario: new target test proves missing behavior before implementation
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-target.test.tsx | tee ../../evidence/task-1-doc-feedback-target-vitest.txt
    Expected: Final implementation exits 0; red-run evidence is also saved by the executor as evidence/task-1-doc-feedback-target-red.txt before Task 5/6/7 changes.
    Evidence: evidence/task-1-doc-feedback-target-vitest.txt
  ```

  Commit: YES | Message: `test(ssot-doc): target feedback mode contracts` | Files: [`tests/test_atlas_ssot_doc_tab.py`, `frontend/atlas/__tests__/ssot-doc-feedback-target.test.tsx`]

- [ ] 2. Add backend SSOT doc source mapping and lookup API

  What to do: Add a small pure helper module that maps SSOT sections and common nested components to source references, then add a thin lookup route that returns `{ok, ip, ssot_path, section, path, label, kind, value, yaml, feedback}` for a selected DOC component. The route should accept `ip` and `path`; it should validate IP/path using the existing feedback path parser rules and reuse existing SSOT load/save helpers from the host. Start with failing pytest coverage for valid lookup, nested register field lookup, invalid path, missing IP, and feedback-history inclusion.
  Must NOT do: Do not move the existing export or feedback routes out of `atlas_ui.py` in this task. Do not expose arbitrary file reads.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [4, 6, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_ui.py:5030` - existing SSOT save emits file change events.
  - Pattern:  `src/atlas_ui.py:5043` - `_parse_ssot_feedback_path` validates dot notation.
  - Pattern:  `src/atlas_ui.py:5053` - `_set_ssot_feedback_path` traverses dot-path tokens.
  - Pattern:  `src/atlas_ui.py:8136` - existing `/api/ssot/doc-feedback` route.
  - Pattern:  `src/atlas_ui.py:8246` - existing `/api/ssot/export` route stays canonical.
  - API/Type: `src/atlas_api_ssot.py:48` - existing `/api/ssot?file=` read route shape for SSOT files.
  - Test:     `tests/test_ssot_export.py:324` - existing doc-feedback route test.
  - Test:     `tests/test_ssot_inline_export_endpoint.py:87` - existing inline HTML export endpoint test.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py tests/test_ssot_export.py::test_ssot_doc_feedback_updates_yaml_and_export -q | tee evidence/task-2-backend-source-map.txt` exits 0.
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py::test_doc_source_lookup_rejects_invalid_path -q | tee evidence/task-2-backend-source-map-error.txt` exits 0 and asserts HTTP 400 with the exact existing path validation message.
  - [ ] `python3 -m compileall src/atlas_ssot_doc_map.py src/atlas_ui.py | tee evidence/task-2-compileall.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: lookup nested register field source
    Tool:     bash
    Steps:    mkdir -p evidence && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py::test_doc_source_lookup_returns_nested_register_field -q | tee evidence/task-2-register-field-lookup.txt
    Expected: Command exits 0 and asserts JSON includes path "registers.register_list.0.fields.0.description" plus a non-empty YAML/value snippet.
    Evidence: evidence/task-2-register-field-lookup.txt

  Scenario: invalid source path is rejected
    Tool:     bash
    Steps:    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py::test_doc_source_lookup_rejects_invalid_path -q | tee evidence/task-2-backend-source-map-error.txt
    Expected: Command exits 0 and asserts HTTP 400 with "path must use dot notation".
    Evidence: evidence/task-2-backend-source-map-error.txt
  ```

  Commit: YES | Message: `feat(ssot-doc): expose source lookup for doc feedback` | Files: [`src/atlas_ssot_doc_map.py`, `src/atlas_ui.py`, `tests/test_ssot_doc_source_map.py`, `tests/test_ssot_export.py`]

- [ ] 3. Add frontend feedback data models and API client helpers

  What to do: Add focused frontend helpers for the DOC feedback contract: selected target type, source lookup response type, feedback submit payload type, chat prefill payload type, and fetch helpers for Show SSOT and Apply Feedback. Start with failing Vitest unit tests using mocked `fetch` for success, HTTP error, invalid JSON, and empty selection. Keep all logic outside `ssot-doc.tsx`.
  Must NOT do: Do not create untyped `any`-heavy helper APIs. Do not make UI changes in this task.

  Parallelization: Can parallel: YES | Wave 1 | Blocks: [5, 6, 7, 8] | Blocked by: []

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/ssot-doc.tsx:57` - current local `DocDropTarget` is too small for component-level selection.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:205` - current feedback POST body.
  - Pattern:  `frontend/atlas/workspace-orchestrator-chat.tsx:123` - frontend chat POST uses `credentials: 'include'`.
  - Pattern:  `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx:36` - mocked fetch setup style.
  - Test:     `frontend/atlas/package.json:7` - Vitest command.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/Fetch_API` - official Fetch API reference.

  Acceptance criteria (agent-executable only):
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-api.test.ts | tee ../../evidence/task-3-feedback-api-vitest.txt` exits 0.
  - [ ] `cd frontend/atlas && npx tsc --noEmit -p tsconfig.json | tee ../../evidence/task-3-feedback-api-tsc.txt` exits 0.
  - [ ] `wc -l frontend/atlas/ssot-doc-feedback-api.ts frontend/atlas/ssot-doc-feedback-types.ts | tee evidence/task-3-feedback-api-wc.txt` shows each new production helper under 250 lines.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: source lookup success and feedback POST success
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-api.test.ts -t "resolves source lookup and submits feedback" | tee ../../evidence/task-3-feedback-api-success.txt
    Expected: Command exits 0 and the mocked requests include /api/ssot/doc-source and /api/ssot/doc-feedback with credentials "include".
    Evidence: evidence/task-3-feedback-api-success.txt

  Scenario: backend error surfaces exact message
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-api.test.ts -t "surfaces backend errors" | tee ../../evidence/task-3-feedback-api-error.txt
    Expected: Command exits 0 and asserts the helper throws the server-provided error text.
    Evidence: evidence/task-3-feedback-api-error.txt
  ```

  Commit: YES | Message: `feat(ssot-doc): add feedback API helpers` | Files: [`frontend/atlas/ssot-doc-feedback-api.ts`, `frontend/atlas/ssot-doc-feedback-types.ts`, `frontend/atlas/__tests__/ssot-doc-feedback-api.test.ts`]

- [ ] 4. Annotate the HTML export with `data-ssot-*` component references

  What to do: Add `data-ssot-section`, `data-ssot-path`, `data-ssot-label`, and `data-ssot-kind` attributes to selectable HTML export targets. Cover top-level `h2` sections, rich diagram cards, register blocks, register field rows, function/cycle model cards, timing rows, module nodes, and interface links where source data exists. Start with failing pytest assertions against the generated HTML. Prefer a small helper for attribute escaping and path construction.
  Must NOT do: Do not change the visual layout of the exported document except for non-visible data attributes. Do not make Mermaid auto-rendering changes.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8] | Blocked by: [2]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `src/atlas_ssot_export.py:43` - canonical SSOT export section order.
  - Pattern:  `src/atlas_ssot_export.py:515` - markdown export emits `##` sections.
  - Pattern:  `src/atlas_ssot_export_html2.py:505` - `_ssot_to_html` converts markdown to HTML.
  - Pattern:  `src/atlas_ssot_export_html2.py:532` - `.diagram-card` CSS already exists.
  - Pattern:  `src/atlas_ssot_export_html.py:360` - register field rows are rendered manually.
  - Pattern:  `src/atlas_ssot_export_html.py:398` - register block HTML is rendered manually.
  - Pattern:  `src/atlas_ssot_export_html2.py:106` - interface links are rendered manually.
  - Pattern:  `src/atlas_ssot_export_html2.py:124` - module nodes are rendered manually.
  - Test:     `tests/test_ssot_export.py:300` - existing custom block HTML test.
  - Test:     `tests/test_ssot_inline_export_endpoint.py:87` - existing inline export endpoint test.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_export.py tests/test_ssot_inline_export_endpoint.py tests/test_ssot_doc_source_map.py -q | tee evidence/task-4-html-attrs-pytest.txt` exits 0.
  - [ ] Generated HTML for a register field contains `data-ssot-path="registers.register_list.0.fields.0"` and `data-ssot-kind="register_field"`.
  - [ ] Generated HTML for a top-level heading contains `data-ssot-section="top_module"` and `data-ssot-path="top_module"`.
  - [ ] `grep -R "window.__ssotRenderMermaid\\|mermaid.run" tests/test_ssot_inline_export_endpoint.py src/atlas_ssot_export_html*.py | tee evidence/task-4-no-mermaid-runtime-regression.txt` confirms the existing no-auto-Mermaid contract is unchanged.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: generated HTML exposes component source references
    Tool:     bash
    Steps:    mkdir -p evidence && PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py::test_html_export_marks_selectable_doc_components -q | tee evidence/task-4-html-component-markers.txt
    Expected: Command exits 0 and asserts h2, register block, field row, interface link, and module node markers.
    Evidence: evidence/task-4-html-component-markers.txt

  Scenario: inline export behavior remains compatible
    Tool:     bash
    Steps:    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_inline_export_endpoint.py::test_export_endpoint_can_render_html_inline -q | tee evidence/task-4-inline-export-regression.txt
    Expected: Command exits 0 and content-disposition remains inline with no Mermaid runtime strings.
    Evidence: evidence/task-4-inline-export-regression.txt
  ```

  Commit: YES | Message: `feat(ssot-export): mark doc components with ssot paths` | Files: [`src/atlas_ssot_doc_map.py`, `src/atlas_ssot_export.py`, `src/atlas_ssot_export_html.py`, `src/atlas_ssot_export_html2.py`, `tests/test_ssot_doc_source_map.py`, `tests/test_ssot_export.py`, `tests/test_ssot_inline_export_endpoint.py`]

- [ ] 5. Implement iframe hit-testing, drag targeting, and highlight overlay

  What to do: Add a focused hook/module for same-origin iframe interaction. It should attach listeners only in Feedback Mode, resolve nearest selectable ancestors by `data-ssot-path`, support click selection, drag-over/drop targeting, rectangular drag selection fallback, keyboard Escape clear, and a non-blocking visual highlight overlay. Use `elementFromPoint`/`elementsFromPoint` inside the iframe document and `pointer-events: none` for overlays. Start with failing jsdom tests around event wiring and target resolution; include a Playwright micro-harness for real coordinate behavior if jsdom cannot validate geometry.
  Must NOT do: Do not rely on top-level document coordinates for iframe internals. Do not block normal iframe scrolling outside feedback mode.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8] | Blocked by: [1, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/ssot-doc.tsx:163` - current Feedback Mode attaches iframe `dragover` and `drop` listeners.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:181` - current drop target only supports h2 hover/drop.
  - Pattern:  `frontend/atlas/sim-debug-panels.tsx:899` - existing source drag selection pattern with movement threshold.
  - Pattern:  `frontend/atlas/sim-debug-wave.tsx:292` - existing drag/drop reorder pattern uses `dropEffect`.
  - Test:     `frontend/atlas/__tests__/sim-debug-source-viewer.test.tsx:112` - drag selection testing precedent.
  - External: `https://developer.mozilla.org/en-US/docs/Web/HTML/Reference/Elements/iframe` - same-origin iframe DOM access constraint.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/Document/elementFromPoint` - viewport-relative hit testing and iframe behavior.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/Document/elementsFromPoint` - stacked hit testing.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API` - `DataTransfer` drag/drop rules.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/HTMLElement/drop_event` - `dragover.preventDefault()` requirement for `drop`.
  - External: `https://developer.mozilla.org/en-US/docs/Web/CSS/pointer-events` - non-blocking overlays.
  - External: `https://developer.mozilla.org/en-US/docs/Web/CSS/outline` - layout-neutral highlight outline.

  Acceptance criteria (agent-executable only):
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-frame-selection.test.tsx | tee ../../evidence/task-5-frame-selection-vitest.txt` exits 0.
  - [ ] `cd frontend/atlas && npx tsc --noEmit -p tsconfig.json | tee ../../evidence/task-5-frame-selection-tsc.txt` exits 0.
  - [ ] `wc -l frontend/atlas/ssot-doc-frame-selection.ts frontend/atlas/ssot-doc-feedback-types.ts | tee evidence/task-5-frame-selection-wc.txt` shows each new production helper under 250 lines.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: click selects nearest data-ssot component
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-frame-selection.test.tsx -t "click selects nearest selectable ssot target" | tee ../../evidence/task-5-click-selection.txt
    Expected: Command exits 0 and selected target path equals the nested element's closest data-ssot-path.
    Evidence: evidence/task-5-click-selection.txt

  Scenario: drag/drop keeps a visible non-blocking highlight
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-frame-selection.test.tsx -t "drop selection renders non-blocking highlight overlay" | tee ../../evidence/task-5-drag-highlight.txt
    Expected: Command exits 0 and the overlay style includes pointer-events: none plus a stable selected path.
    Evidence: evidence/task-5-drag-highlight.txt
  ```

  Commit: YES | Message: `feat(ssot-doc): add iframe feedback selection engine` | Files: [`frontend/atlas/ssot-doc-frame-selection.ts`, `frontend/atlas/__tests__/ssot-doc-frame-selection.test.tsx`, `frontend/atlas/ssot-doc-feedback-types.ts`]

- [ ] 6. Implement Show SSOT source tray and feedback panel component

  What to do: Extract the current inline Feedback Mode form into a small component that accepts selected target state, source lookup state, and feedback submit callbacks. Add a Show SSOT button that fetches the backend lookup, displays section/path/kind/label/current value/YAML snippet/feedback history, and clearly handles empty selection and lookup errors. Keep controls compact and utilitarian: segmented mode control, icon/text command buttons only where the command needs text, no nested cards.
  Must NOT do: Do not place explanatory help copy in the app. Do not use oversized hero-like typography or decorative gradients.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8] | Blocked by: [2, 3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/ssot-doc.tsx:316` - current Feedback Mode form to extract.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:330` - current section/path/comment controls.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:405` - current feedback status and apply button.
  - Pattern:  `frontend/atlas/workspace-ssot-panels.tsx:436` - existing SSOT panel label styling and `ssotTitleFor` usage.
  - Pattern:  `frontend/atlas/styles.css:2560` - existing selection/comment styling area for source preview.
  - Test:     `frontend/atlas/__tests__/preview-pane-lint-annotation.test.tsx:57` - focused render assertion pattern.

  Acceptance criteria (agent-executable only):
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-panel.test.tsx | tee ../../evidence/task-6-feedback-panel-vitest.txt` exits 0.
  - [ ] `cd frontend/atlas && npx tsc --noEmit -p tsconfig.json | tee ../../evidence/task-6-feedback-panel-tsc.txt` exits 0.
  - [ ] `wc -l frontend/atlas/ssot-doc-feedback-panel.tsx frontend/atlas/ssot-doc.tsx | tee evidence/task-6-feedback-panel-wc.txt` shows the new component under 250 lines and `ssot-doc.tsx` not meaningfully larger than its pre-task 440-line baseline.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: Show SSOT displays selected source value
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-panel.test.tsx -t "show ssot displays source path and yaml snippet" | tee ../../evidence/task-6-show-ssot-success.txt
    Expected: Command exits 0 and rendered output contains the selected YAML path, kind, label, and current value.
    Evidence: evidence/task-6-show-ssot-success.txt

  Scenario: Show SSOT handles no selection
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-panel.test.tsx -t "show ssot is disabled without a selected component" | tee ../../evidence/task-6-show-ssot-empty.txt
    Expected: Command exits 0 and Show SSOT is disabled with no fetch call made.
    Evidence: evidence/task-6-show-ssot-empty.txt
  ```

  Commit: YES | Message: `feat(ssot-doc): show ssot source for selected doc component` | Files: [`frontend/atlas/ssot-doc-feedback-panel.tsx`, `frontend/atlas/__tests__/ssot-doc-feedback-panel.test.tsx`, `frontend/atlas/styles.css`]

- [ ] 7. Wire SSOT DOC comment events into the existing workspace composer pattern

  What to do: Add a typed custom event for SSOT DOC comments and a listener in the workspace data hook that prefills the existing chat/composer input with an actionable SSOT-edit prompt. The message must include IP, section, YAML path, selected DOC label, current source value/YAML snippet when available, selected rendered text, and the user's comment. The DOC pane should dispatch this event and then call its existing `onBack` navigation so the user lands on chat with the prompt focused.
  Must NOT do: Do not bypass the composer by posting directly to `/api/chat/{room}/send` unless the user explicitly asks for auto-send later. Do not alter existing `atlas-fold-comment` behavior for source preview.

  Parallelization: Can parallel: YES | Wave 2 | Blocks: [8] | Blocked by: [3]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/workspace-root-data-hook.tsx:332` - existing `atlas-fold-comment` listener prefills and focuses chat input.
  - Pattern:  `frontend/atlas/workspace-root-data-hook.tsx:351` - existing prefill text format and focus behavior.
  - Pattern:  `frontend/atlas/preview-pane.tsx:329` - source preview dispatches comment event with path/lines/text.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:226` - current DOC feedback dispatches `atlas-ssot-doc-feedback`.
  - Pattern:  `frontend/atlas/workspace-root.tsx:460` - DOC pane receives `onBack={() => setMainTab('chat')}`.
  - API/Type: `frontend/atlas/workspace-orchestrator-chat.tsx:118` - separate orchestrator chat panel submit path should not be changed for composer prefill.

  Acceptance criteria (agent-executable only):
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-comment-prefill.test.tsx | tee ../../evidence/task-7-comment-prefill-vitest.txt` exits 0.
  - [ ] `cd frontend/atlas && npx tsc --noEmit -p tsconfig.json | tee ../../evidence/task-7-comment-prefill-tsc.txt` exits 0.
  - [ ] Existing source comment test still passes: `cd frontend/atlas && npm test -- __tests__/preview-pane-lint-annotation.test.tsx | tee ../../evidence/task-7-preview-regression.txt` exits 0.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: DOC comment prefills composer with SSOT context
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/ssot-doc-comment-prefill.test.tsx -t "prefills composer from atlas ssot doc comment event" | tee ../../evidence/task-7-comment-prefill-success.txt
    Expected: Command exits 0 and the composer value includes "Update the SSOT", the IP, YAML path, source value, selected DOC text, and user comment.
    Evidence: evidence/task-7-comment-prefill-success.txt

  Scenario: source preview comments still work
    Tool:     bash
    Steps:    cd frontend/atlas && npm test -- __tests__/preview-pane-lint-annotation.test.tsx | tee ../../evidence/task-7-preview-regression.txt
    Expected: Command exits 0 with no change to `atlas-fold-comment` behavior.
    Evidence: evidence/task-7-preview-regression.txt
  ```

  Commit: YES | Message: `feat(workspace): prefill chat from ssot doc comments` | Files: [`frontend/atlas/workspace-root-data-hook.tsx`, `frontend/atlas/ssot-doc-feedback-types.ts`, `frontend/atlas/__tests__/ssot-doc-comment-prefill.test.tsx`]

- [ ] 8. Integrate the DOC pane, polish UX, and add real Chrome end-to-end QA

  What to do: Replace the current inline feedback-mode logic in `SsotDocPane` with the new helper modules/components. Ensure View Mode remains unchanged, Feedback Mode selection works after iframe reloads, Apply Feedback refreshes the iframe, Show SSOT resolves the selected component, and Comment moves the user to the chat composer with context. Add a Playwright real Chrome QA script that creates or uses a small SSOT fixture IP, opens the DOC tab, selects a component by click, selects another by drag/drop, opens Show SSOT, sends a comment to chat prefill, applies feedback, and captures screenshots plus JSON assertions.
  Must NOT do: Do not leave long-running Atlas workers active after browser QA. Do not depend on real LLM calls. Do not require a manual browser step.

  Parallelization: Can parallel: NO | Wave 3 | Blocks: [final verification] | Blocked by: [1, 2, 3, 4, 5, 6, 7]

  References (executor has NO interview context - be exhaustive):
  - Pattern:  `frontend/atlas/ssot-doc.tsx:68` - integration point for `SsotDocPane`.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:73` - current reload/mode state.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:199` - current feedback submit handler.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:272` - existing refresh button.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:275` - existing View/Feedback segmented mode control.
  - Pattern:  `frontend/atlas/ssot-doc.tsx:415` - iframe render surface.
  - Pattern:  `frontend/atlas/workspace-root.tsx:460` - DOC pane mount with active SSOT IP.
  - Pattern:  `doc/wiki/atlas-ui-playwright-screenshot-recipe-2026-05-23.md:14` - repo recipe recommends Playwright with system Chrome.
  - Pattern:  `doc/wiki/atlas-ui-playwright-screenshot-recipe-2026-05-23.md:57` - Playwright script skeleton.
  - Pattern:  `src/atlas_runtime_run.py:993` - Atlas UI CLI parser.
  - Pattern:  `src/atlas_runtime_run.py:995` - `--port` argument.
  - Pattern:  `src/atlas_runtime_run.py:996` - `--host` argument.
  - External: `https://developer.mozilla.org/en-US/docs/Web/API/HTML_Drag_and_Drop_API/Drag_operations` - drag operation compatibility rules.

  Acceptance criteria (agent-executable only):
  - [ ] `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_doc_source_map.py tests/test_ssot_export.py tests/test_ssot_inline_export_endpoint.py tests/test_atlas_ssot_doc_tab.py -q | tee evidence/task-8-backend-regression.txt` exits 0.
  - [ ] `cd frontend/atlas && npm test -- __tests__/ssot-doc-feedback-target.test.tsx __tests__/ssot-doc-feedback-api.test.ts __tests__/ssot-doc-frame-selection.test.tsx __tests__/ssot-doc-feedback-panel.test.tsx __tests__/ssot-doc-comment-prefill.test.tsx | tee ../../evidence/task-8-frontend-regression.txt` exits 0.
  - [ ] `cd frontend/atlas && npx tsc --noEmit -p tsconfig.json | tee ../../evidence/task-8-tsc.txt` exits 0.
  - [ ] `cd frontend/atlas && npm run build | tee ../../evidence/task-8-vite-build.txt` exits 0.
  - [ ] `node scripts/ui_tests/ssot_doc_feedback.mjs --base http://127.0.0.1:8765 --ip ssot_doc_feedback_demo --out evidence/task-8-live-browser.png --json evidence/task-8-live-browser.json | tee evidence/task-8-live-browser.txt` exits 0 after an Atlas UI server is started for the test.
  - [ ] `cat evidence/task-8-live-browser.json` contains `"clickSelection":true`, `"dragSelection":true`, `"showSsot":true`, `"commentPrefill":true`, and `"applyFeedback":true`.

  QA scenarios (MANDATORY - task incomplete without these):
  > Name the exact tool AND its exact invocation - not "verify it works". Browser use: use Chrome to drive the page; if Chrome is not available, download and use agent-browser (https://github.com/vercel-labs/agent-browser). Computer use: OS-level GUI automation for a non-browser desktop app.
  ```
  Scenario: happy browser path - click, Show SSOT, comment prefill, apply feedback
    Tool:     playwright(real Chrome)
    Steps:    mkdir -p evidence && python3 src/atlas_ui.py --host 127.0.0.1 --port 8765 --session admin --ip ssot_doc_feedback_demo --workflow ssot-gen > evidence/task-8-server.log 2>&1 & echo $! > evidence/task-8-server.pid; node scripts/ui_tests/ssot_doc_feedback.mjs --base http://127.0.0.1:8765 --ip ssot_doc_feedback_demo --out evidence/task-8-live-browser.png --json evidence/task-8-live-browser.json | tee evidence/task-8-live-browser.txt; kill $(cat evidence/task-8-server.pid)
    Expected: Script exits 0; JSON has clickSelection, showSsot, commentPrefill, and applyFeedback all true; screenshot shows a selected DOC component and Show SSOT tray.
    Evidence: evidence/task-8-live-browser.png

  Scenario: edge browser path - no selection and invalid path are graceful
    Tool:     playwright(real Chrome)
    Steps:    node scripts/ui_tests/ssot_doc_feedback.mjs --base http://127.0.0.1:8765 --ip ssot_doc_feedback_demo --edge --json evidence/task-8-live-browser-edge.json | tee evidence/task-8-live-browser-edge.txt
    Expected: Script exits 0; JSON has noSelectionDisabled true and invalidPathError containing "path must use dot notation"; no uncaught page errors.
    Evidence: evidence/task-8-live-browser-edge.json

  Scenario: regression path - View Mode export remains usable
    Tool:     bash
    Steps:    PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python3 -m pytest tests/test_ssot_inline_export_endpoint.py::test_export_endpoint_can_render_html_inline tests/test_ssot_export.py::test_ssot_doc_feedback_updates_yaml_and_export -q | tee evidence/task-8-export-regression.txt
    Expected: Command exits 0; inline export and existing doc-feedback persistence still pass.
    Evidence: evidence/task-8-export-regression.txt
  ```

  Commit: YES | Message: `feat(ssot-doc): integrate component feedback workflow` | Files: [`frontend/atlas/ssot-doc.tsx`, `frontend/atlas/ssot-doc-feedback-api.ts`, `frontend/atlas/ssot-doc-feedback-panel.tsx`, `frontend/atlas/ssot-doc-frame-selection.ts`, `frontend/atlas/styles.css`, `scripts/ui_tests/ssot_doc_feedback.mjs`, `tests/test_atlas_ssot_doc_tab.py`]

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
- Reference the plan file path in the final commit footer: `Plan: plans/ssot-doc-feedback-mode.md`.

## Success criteria
- All Must-Have shipped; all QA scenarios pass with captured evidence; F1-F4 approved; commit history clean.
