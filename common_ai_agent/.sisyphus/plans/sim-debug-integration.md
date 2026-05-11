# Sim Debug Integration into Main Display

## TL;DR

> **Quick Summary**: Remove the fullscreen DOM takeover of sim debug and integrate it as a first-class `mainTab='debug'` in the main Atlas UI display. The debug tab shows hierarchy (left), source+waveform (center, vertically split), and debug chat (right). Fullscreen CSS, `isSimDebug` logic, and the exit button are completely removed.
>
> **Deliverables**:
> - `mainTab='debug'` added to workspace tab strip
> - Fullscreen CSS rules removed from styles.css
> - `isSimDebug` logic removed from workspace.jsx
> - sim-debug.jsx refactored to accept `{width, height}` props
> - Debug tab renders hierarchy + source/waveform + chat in center pane
> - SourceViewer ↔ PreviewPane toggle
> - Workflow 'sim_debug' switches to debug tab (not fullscreen)
> - Playwright E2E tests for tab switching, no fullscreen, panel rendering
>
> **Estimated Effort**: Medium (4 waves, ~14 tasks)
> **Parallel Execution**: YES — 4 waves, max 3 concurrent tasks
> **Critical Path**: Task 1/2 → Task 4/5 → Task 7 → Task 9 → F1-F4

---

## Context

### Original Request
> "완전히 다른 플랜 지금 sim debug 가 별도 창으로 뜨는데 이걸 기존 workflow처럼 화면 전환 없이 main display 에 source, waveform 보여주는 방식을 원해"

### Interview Summary
**Key Discussions**:
- **Integration style**: New `mainTab='debug'` tab instead of fullscreen takeover
- **Panel scope**: Full sim debug (left hierarchy, center source+waveform, right debug chat)
- **Old mode**: Completely remove fullscreen sim debug
- **Source viewer**: Toggle between SourceViewer (per-line) and PreviewPane (AST folding)
- **Panel duplication**: Debug tab replaces left/right with debug-specific panels
- **VCD loading**: Keep existing VCD picker dropdown

**Research Findings**:
- sim debug is NOT a separate window — it's a DOM fullscreen takeover:
  - `workspace.jsx:2641` — `const isSimDebug = workflow === 'sim_debug'`
  - `workspace.jsx:2642-2643` — `effLeftW = isSimDebug ? 0 : leftW`
  - `workspace.jsx:2745-2747` — `gridTemplateColumns: isSimDebug ? '1fr' : ...`
  - `styles.css:1411-1448` — fullscreen CSS rules
  - `workspace.jsx:3043-3054` — exit button
- sim-debug.jsx (1,654 lines) already has multi-panel layout:
  - Lines 1162-1167: 5-zone grid
  - Lines 1252-1296: center vertically split
  - Lines 1074-1086: expand mode buttons
- Waveform: SVG-based (`debug-shared.jsx`)
- Main display has `useResizable` + `Splitter` + CSS Grid transitions

### Metis Review
**Identified Gaps** (addressed in plan):
- **State management**: Ephemeral (remount = reset) for v1 — no state lifting to workspace
- **Splitters**: Preserve sim-debug's internal splitters for center vertical split; workspace splitters manage left/right
- **Coverage workflow**: Explicitly excluded from this plan (uses same fullscreen pattern)
- **Debug chat**: Keep self-contained in right panel — do NOT merge with main ATLAS chat
- **Component API**: sim-debug.jsx must accept `{width, height}` props — no `100vw/100vh` or body-class manipulation
- **VCD fetch**: Lazy fetch when debug tab first activated (not eager on app load)
- **Expand modes**: Keep existing instant state flips — no animation work

---

## Work Objectives

### Core Objective
Integrate sim debug into Atlas UI's main display as a new `mainTab='debug'` tab, completely eliminating the fullscreen takeover mode while preserving all debug functionality (hierarchy, source viewer, waveform, chat).

### Concrete Deliverables
1. `mainTab='debug'` chip in workspace tab strip
2. Debug tab renders hierarchy (left), source+waveform (center), debug chat (right)
3. Fullscreen CSS rules removed from styles.css
4. `isSimDebug` logic removed from workspace.jsx
5. sim-debug.jsx refactored to accept `{width, height}` props
6. SourceViewer ↔ PreviewPane toggle button
7. Workflow 'sim_debug' switches to debug tab (not fullscreen)
8. All existing tabs (chat, ssot, qa, split, preview) unchanged
9. Playwright E2E tests for tab switching, no fullscreen, panel rendering

### Definition of Done
- [ ] Click 'debug' tab → debug panel renders in center pane with titlebar visible
- [ ] Left panel shows hierarchy tree, center shows source+waveform, right shows debug chat
- [ ] Click 'chat' tab → back to normal chat view
- [ ] `document.body` does NOT have `atlas-sim-debug-fullscreen` class
- [ ] Run `/wf sim_debug` → switches to debug tab (not fullscreen)
- [ ] Source viewer toggle switches between SourceViewer and PreviewPane
- [ ] All Playwright tests pass

### Must Have
- `mainTab='debug'` tab
- Remove fullscreen CSS (`styles.css:1411-1448`)
- Remove `isSimDebug` from workspace.jsx
- Refactor sim-debug.jsx for embedded use
- Source/waveform vertical split preserved
- VCD picker dropdown
- SourceViewer ↔ PreviewPane toggle
- Workflow 'sim_debug' → debug tab
- Playwright E2E tests

### Must NOT Have (Guardrails)
- Coverage workflow changes
- Merge debug chat with main ATLAS chat
- New external dependencies
- Change other tabs' behavior
- Persist debug state across tab switches (v2)
- Animation work for expand modes
- Responsive/mobile layout changes
- Generic 3-pane layout abstraction

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed.

### Test Decision
- **Infrastructure exists**: YES (Playwright config at `playwright.config.js`)
- **Automated tests**: Tests-after implementation
- **Framework**: Playwright E2E

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Playwright — navigate, click tabs, assert DOM, screenshot
- **Regression**: Playwright — verify other tabs unchanged

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Remove Fullscreen — foundation):
├── Task 1: Remove fullscreen CSS from styles.css [quick]
├── Task 2: Remove isSimDebug logic from workspace.jsx [quick]
└── Task 3: Add 'debug' mainTab + tab strip chip [quick]

Wave 2 (Refactor sim-debug.jsx):
├── Task 4: Refactor sim-debug.jsx to accept {width, height} props [deep]
├── Task 5: Remove body class manipulation from sim-debug.jsx [quick]
└── Task 6: Preserve internal splitters in embedded mode [quick]

Wave 3 (Integration):
├── Task 7: Integrate DebugTab into workspace.jsx center pane [deep]
├── Task 8: Wire workflow 'sim_debug' to switch to debug tab [quick]
└── Task 9: Add SourceViewer ↔ PreviewPane toggle [quick]

Wave 4 (Tests):
├── Task 10: Playwright tab switching regression [unspecified-high]
├── Task 11: Playwright no fullscreen class [unspecified-high]
├── Task 12: Playwright debug tab renders with panels [unspecified-high]
├── Task 13: Playwright other tabs unchanged [unspecified-high]
└── Task 14: Playwright VCD load [unspecified-high]

Wave FINAL (After ALL tasks — 4 parallel reviews):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: Task 1/2 → Task 4/5 → Task 7 → Task 9 → F1-F4 → user okay
Parallel Speedup: ~50% faster than sequential
Max Concurrent: 3 (Wave 2 & 3)
```

### Dependency Matrix

| Task | Blocked By | Blocks |
|------|-----------|--------|
| 1 (Remove CSS) | — | — |
| 2 (Remove isSimDebug) | — | 7, 8 |
| 3 (Add debug tab) | — | 7, 10 |
| 4 (Refactor props) | — | 7 |
| 5 (Remove body class) | — | 7, 11 |
| 6 (Preserve splitters) | — | 7 |
| 7 (Integrate) | 2, 3, 4, 5, 6 | 9, 10, 12 |
| 8 (Wire workflow) | 2 | 10 |
| 9 (Toggle) | 7 | 12 |
| 10 (Test: tabs) | 3, 7, 8 | — |
| 11 (Test: no fullscreen) | 5 | — |
| 12 (Test: panels) | 7, 9 | — |
| 13 (Test: regression) | 7 | — |
| 14 (Test: VCD) | 7 | — |

### Agent Dispatch Summary

- **Wave 1**: **3** — T1-T3 → `quick`
- **Wave 2**: **3** — T4 → `deep`, T5-T6 → `quick`
- **Wave 3**: **3** — T7 → `deep`, T8-T9 → `quick`
- **Wave 4**: **5** — T10-T14 → `unspecified-high`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. **Remove fullscreen CSS rules from styles.css**

  **What to do**:
  - Delete `styles.css:1411-1448` (all rules under `body.atlas-sim-debug-fullscreen`)
  - These rules hide titlebar, dir-switcher, statusbar and stretch #root/app/app-main to 100vw/100vh
  - After removal, verify no other CSS references `.atlas-sim-debug-fullscreen`
  - Search with grep to ensure no lingering references

  **Must NOT do**:
  - Do NOT delete unrelated CSS
  - Do NOT modify other fullscreen rules (e.g., for coverage)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple CSS deletion
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 2, 3)
  - **Parallel Group**: Wave 1
  - **Blocks**: —
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/styles.css:1411-1448` — fullscreen rules to delete

  **Acceptance Criteria**:
  - [ ] `styles.css` no longer contains `atlas-sim-debug-fullscreen`
  - [ ] grep confirms no other references to this class

  **QA Scenarios**:

  ```
  Scenario: CSS rules removed
    Tool: Bash (grep)
    Preconditions: styles.css exists
    Steps:
      1. Run: grep -n "atlas-sim-debug-fullscreen" frontend/atlas/styles.css
      2. Assert: no output (class removed)
      3. Run: grep -rn "atlas-sim-debug-fullscreen" frontend/
      4. Assert: no output (no lingering references)
    Expected Result: Class completely removed from codebase
    Failure Indicators: grep finds remaining references
    Evidence: .sisyphus/evidence/task-1-css-removed.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-1-css-removed.txt` — grep output confirming removal

  **Commit**: YES (Wave 1)
  - Message: `refactor(ui): remove sim debug fullscreen CSS rules`
  - Files: `frontend/atlas/styles.css`

---

- [ ] 2. **Remove `isSimDebug` logic from workspace.jsx**

  **What to do**:
  - Find ALL occurrences of `isSimDebug` in `workspace.jsx` using grep/ast-grep
  - Remove or refactor each occurrence:
    - Line ~2641: `const isSimDebug = workflow === 'sim_debug'` — remove this line
    - Line ~2642-2643: `effLeftW = isSimDebug ? 0 : leftW` and `effRightW = isSimDebug ? 0 : rightW` — change to always use `leftW` and `rightW`
    - Line ~2735-2738: `if (isSimDebug) document.body.classList.add(...)` — remove this block
    - Line ~2745-2747: `gridTemplateColumns: isSimDebug ? '1fr' : ...` — remove conditional, always use normal grid
    - Line ~3029: `{!isSimDebug && (<Splitter ... />)}` — change to always render Splitter
    - Line ~3036-3055: `window.SimDebug` rendering + exit button — remove or repurpose
  - Ensure `workflow` state still exists (used elsewhere), but `isSimDebug` derived state is gone
  - The sim-debug component rendering should be moved to `mainTab === 'debug'` conditional

  **Must NOT do**:
  - Do NOT remove `workflow` state entirely (used by other features)
  - Do NOT break coverage workflow fullscreen

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Targeted deletions and simplifications
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 1, 3)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 8
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/workspace.jsx:2641` — `isSimDebug` declaration
  - `frontend/atlas/workspace.jsx:2642-2643` — panel width conditionals
  - `frontend/atlas/workspace.jsx:2735-2738` — body class manipulation
  - `frontend/atlas/workspace.jsx:2745-2747` — grid conditional
  - `frontend/atlas/workspace.jsx:3029` — splitter conditional
  - `frontend/atlas/workspace.jsx:3036-3055` — SimDebug rendering + exit button

  **Acceptance Criteria**:
  - [ ] `workspace.jsx` no longer contains `isSimDebug`
  - [ ] Grid always uses normal 5-column layout (never '1fr')
  - [ ] Body class manipulation removed
  - [ ] Splitters always render

  **QA Scenarios**:

  ```
  Scenario: isSimDebug removed
    Tool: Bash (grep)
    Preconditions: workspace.jsx exists
    Steps:
      1. Run: grep -n "isSimDebug" frontend/atlas/workspace.jsx
      2. Assert: no output (variable removed)
    Expected Result: isSimDebug completely removed
    Failure Indicators: grep finds remaining references
    Evidence: .sisyphus/evidence/task-2-isSimDebug-removed.txt

  Scenario: Grid always normal
    Tool: Read (file)
    Preconditions: Task 2 complete
    Steps:
      1. Read gridTemplateColumns line in workspace.jsx
      2. Assert: no conditional, always uses 5-column grid
    Expected Result: Normal grid layout regardless of workflow
    Failure Indicators: Conditional still present
    Evidence: .sisyphus/evidence/task-2-grid-normal.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-2-isSimDebug-removed.txt` — grep output
  - [ ] `task-2-grid-normal.txt` — grid line content

  **Commit**: YES (Wave 1)
  - Message: `refactor(ui): remove isSimDebug fullscreen logic from workspace`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 3. **Add 'debug' to mainTab state and tab strip**

  **What to do**:
  - Add `'debug'` to the `mainTab` state type/options in workspace.jsx (around line 1220)
  - Add a 'Debug' chip/button to the tab strip (around lines 3095-3175)
  - Style it consistently with existing tabs (chat, ssot, qa, split, preview)
  - Clicking the debug tab sets `mainTab = 'debug'`
  - Add conditional rendering in the center pane: when `mainTab === 'debug'`, render debug content
  - The debug content placeholder can be a simple `<div>Debug Tab</div>` for now (actual component integration in Task 7)

  **Must NOT do**:
  - Do NOT change existing tab styling or behavior
  - Do NOT remove existing tabs

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple state + UI addition
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 1, 2)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 10
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/workspace.jsx:1220` — mainTab state
  - `frontend/atlas/workspace.jsx:3095-3175` — tab strip rendering
  - `frontend/atlas/workspace.jsx:3231-3288` — center pane conditional rendering

  **Acceptance Criteria**:
  - [ ] 'Debug' tab chip visible in tab strip
  - [ ] Clicking it sets mainTab to 'debug'
  - [ ] Other tabs still work normally

  **QA Scenarios**:

  ```
  Scenario: Debug tab visible and clickable
    Tool: Playwright
    Preconditions: Atlas UI running
    Steps:
      1. Navigate to Atlas UI
      2. Assert: tab strip contains text "Debug" (or icon)
      3. Click "Debug" tab
      4. Assert: main content area changes (shows debug placeholder or component)
      5. Click "Chat" tab
      6. Assert: back to chat view
    Expected Result: Tab switching works for debug tab
    Failure Indicators: Debug tab not visible, click doesn't work, other tabs broken
    Evidence: .sisyphus/evidence/task-3-debug-tab.png
  ```

  **Evidence to Capture**:
  - [ ] `task-3-debug-tab.png` — screenshot showing debug tab in tab strip

  **Commit**: YES (Wave 1)
  - Message: `feat(ui): add debug tab to main tab strip`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 4. **Refactor sim-debug.jsx to accept `{width, height}` props**

  **What to do**:
  - Change `window.SimDebug = () => {…}` to `window.SimDebug = ({ width, height }) => {…}`
  - Replace any `window.innerWidth` / `window.innerHeight` usage with props
  - Update the top-level container style from `width: '100%', height: '100%'` to use the passed dimensions
  - Ensure internal flex/grid layouts adapt to the provided size
  - Update `waveWidth` calculation (currently hardcoded to 700 in sim-debug.jsx:431) to be responsive: `waveWidth = width - hierarchyWidth - chatWidth - splitterWidths`
  - Add propTypes or JSDoc comments documenting the expected props
  - Test that the component still works when rendered standalone (for backward compatibility during transition)

  **Must NOT do**:
  - Do NOT change internal component logic (hierarchy, waveform, chat)
  - Do NOT remove existing functionality

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Careful prop threading through 1,654 lines without breaking existing logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 5, 6)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 7
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/sim-debug.jsx:1-50` — component definition
  - `frontend/atlas/sim-debug.jsx:431` — `waveWidth` hardcoded
  - `frontend/atlas/sim-debug.jsx:1104` — container width/height style

  **Acceptance Criteria**:
  - [ ] `window.SimDebug` accepts `{width, height}` props
  - [ ] No `window.innerWidth` / `window.innerHeight` references remain
  - [ ] `waveWidth` is calculated from props, not hardcoded

  **QA Scenarios**:

  ```
  Scenario: Props accepted
    Tool: Read (file)
    Preconditions: sim-debug.jsx exists
    Steps:
      1. Read component definition line
      2. Assert: signature includes `width` and `height` parameters
      3. Search for "innerWidth" and "innerHeight"
      4. Assert: no matches found
    Expected Result: Component is prop-driven
    Failure Indicators: No props, innerWidth still used
    Evidence: .sisyphus/evidence/task-4-props-refactor.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-4-props-refactor.txt` — component signature and prop usage

  **Commit**: YES (Wave 2)
  - Message: `refactor(ui): refactor sim-debug.jsx to accept width/height props`
  - Files: `frontend/atlas/sim-debug.jsx`

---

- [ ] 5. **Remove body class manipulation from sim-debug.jsx**

  **What to do**:
  - Search sim-debug.jsx for any `document.body.classList` usage
  - Remove any code that adds/removes CSS classes to `<body>`
  - Remove any code that manipulates `document.title`, `document.body.style`, or other global DOM state
  - Ensure the component is a pure React component with no side effects on global DOM
  - Check for `useEffect` hooks that touch global state and remove/refactor them

  **Must NOT do**:
  - Do NOT remove local state or internal effects (e.g., VCD fetch on mount)
  - Do NOT change the component's internal behavior

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Targeted removal of global side effects
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 6)
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 7, 11
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/sim-debug.jsx` — full file search for global DOM manipulation

  **Acceptance Criteria**:
  - [ ] No `document.body` references in sim-debug.jsx
  - [ ] No global DOM side effects

  **QA Scenarios**:

  ```
  Scenario: No global side effects
    Tool: Bash (grep)
    Preconditions: sim-debug.jsx exists
    Steps:
      1. Run: grep -n "document.body" frontend/atlas/sim-debug.jsx
      2. Assert: no output
      3. Run: grep -n "document.title" frontend/atlas/sim-debug.jsx
      4. Assert: no output
    Expected Result: Component is side-effect free
    Failure Indicators: Global DOM manipulation remains
    Evidence: .sisyphus/evidence/task-5-no-global-side-effects.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-5-no-global-side-effects.txt` — grep output

  **Commit**: YES (Wave 2)
  - Message: `refactor(ui): remove global DOM side effects from sim-debug.jsx`
  - Files: `frontend/atlas/sim-debug.jsx`

---

- [ ] 6. **Preserve internal splitters in embedded mode**

  **What to do**:
  - Verify that sim-debug.jsx's internal `Splitter` component (around line 1088) and resize handlers work correctly when the component is embedded
  - The internal splitter manages the vertical split between source and waveform in the center panel
  - Ensure it doesn't conflict with workspace.jsx's outer splitters
  - Test that drag-to-resize still works for the source/waveform split
  - Test that expand mode buttons (hierarchy-only, wave-only, source-only, split) still work
  - If conflicts exist, namespace the internal splitter state (e.g., rename `leftW` to `debugLeftW`)

  **Must NOT do**:
  - Do NOT remove expand mode buttons
  - Do NOT replace internal splitter with workspace's Splitter

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Verification and minor adjustments
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 4, 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Task 7
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/sim-debug.jsx:1088` — internal Splitter
  - `frontend/atlas/sim-debug.jsx:1074-1086` — expand mode buttons

  **Acceptance Criteria**:
  - [ ] Internal splitter drag works in embedded mode
  - [ ] Expand mode buttons work
  - [ ] No conflicts with workspace splitters

  **QA Scenarios**:

  ```
  Scenario: Internal splitter works
    Tool: Playwright
    Preconditions: Task 4-5 complete, debug tab accessible
    Steps:
      1. Open debug tab
      2. Find and drag the horizontal splitter between source and waveform
      3. Assert: panels resize smoothly
      4. Click "wave-only" expand button
      5. Assert: waveform fills center area
      6. Click "split" button
      7. Assert: source and waveform both visible again
    Expected Result: Internal layout controls work in embedded mode
    Failure Indicators: Splitter doesn't drag, expand modes broken
    Evidence: .sisyphus/evidence/task-6-internal-splitter.png
  ```

  **Evidence to Capture**:
  - [ ] `task-6-internal-splitter.png` — before/after dragging splitter

  **Commit**: YES (Wave 2)
  - Message: `fix(ui): ensure sim-debug internal splitters work in embedded mode`
  - Files: `frontend/atlas/sim-debug.jsx`

---

- [ ] 7. **Integrate DebugTab into workspace.jsx center pane**

  **What to do**:
  - In workspace.jsx center pane conditional rendering (around lines 3231-3288), add a branch for `mainTab === 'debug'`
  - Render `<window.SimDebug width={centerWidth} height={centerHeight} />` in this branch
  - Calculate `centerWidth` and `centerHeight` from the parent grid cell dimensions
  - Ensure the debug component fills the center pane without overflowing
  - The debug tab should coexist with the existing 5-column grid — left and right panels remain visible
  - Pass the current `ipName` or relevant workspace state to SimDebug if needed
  - Handle the case where `window.SimDebug` is not yet loaded (show loading spinner)

  **Must NOT do**:
  - Do NOT collapse left/right panels when debug tab is active
  - Do NOT change the outer grid layout for other tabs

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Integration point between workspace layout and debug component, sizing calculations
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 8, 9)
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 9, 10, 12
  - **Blocked By**: Tasks 2, 3, 4, 5, 6

  **References**:
  - `frontend/atlas/workspace.jsx:3231-3288` — center pane conditional rendering
  - `frontend/atlas/workspace.jsx:2745-2747` — grid layout
  - `frontend/atlas/sim-debug.jsx` — SimDebug component

  **Acceptance Criteria**:
  - [ ] `mainTab === 'debug'` renders SimDebug in center pane
  - [ ] SimDebug fills available space without overflow
  - [ ] Left and right panels remain visible

  **QA Scenarios**:

  ```
  Scenario: Debug tab renders SimDebug
    Tool: Playwright
    Preconditions: Tasks 1-6 complete
    Steps:
      1. Navigate to Atlas UI
      2. Click "Debug" tab
      3. Assert: center pane contains debug content (hierarchy/source/waveform/chat)
      4. Assert: left sidebar (file tree) still visible
      5. Assert: right sidebar (progress/todo/git) still visible
      6. Screenshot: full layout with debug tab active
    Expected Result: Debug tab integrated without fullscreen takeover
    Failure Indicators: Content missing, overflow, panels hidden
    Evidence: .sisyphus/evidence/task-7-debug-integrated.png
  ```

  **Evidence to Capture**:
  - [ ] `task-7-debug-integrated.png` — full layout screenshot

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): integrate debug tab into workspace center pane`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 8. **Wire workflow 'sim_debug' to switch to debug tab**

  **What to do**:
  - Find where `workflow = 'sim_debug'` is set (e.g., sidebar workflow click, command palette `/wf sim_debug`)
  - Change the behavior: instead of triggering fullscreen, set `mainTab = 'debug'`
  - Keep `workflow = 'sim_debug'` for backend/agent context if needed, but remove the frontend fullscreen trigger
  - Ensure the sidebar 'sim_debug' workflow chip still works but now opens the debug tab
  - The `switchWorkflow` function or equivalent should handle this transition

  **Must NOT do**:
  - Do NOT break other workflow switches
  - Do NOT remove `workflow` state entirely

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple event handler modification
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 9)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 10
  - **Blocked By**: Task 2

  **References**:
  - `frontend/atlas/workspace.jsx:2800` — workflow switch logic
  - `frontend/atlas/data.jsx:46` — sim_debug workflow definition

  **Acceptance Criteria**:
  - [ ] Clicking 'sim_debug' workflow chip switches to debug tab
  - [ ] Running `/wf sim_debug` switches to debug tab
  - [ ] No fullscreen triggered

  **QA Scenarios**:

  ```
  Scenario: Workflow switches to debug tab
    Tool: Playwright
    Preconditions: Tasks 1-7 complete
    Steps:
      1. Click 'sim_debug' workflow chip in sidebar
      2. Assert: mainTab changes to 'debug'
      3. Assert: debug content renders in center pane
      4. Assert: no fullscreen class on body
    Expected Result: Workflow opens debug tab, not fullscreen
    Failure Indicators: Fullscreen triggered, tab not switched
    Evidence: .sisyphus/evidence/task-8-workflow-tab.png
  ```

  **Evidence to Capture**:
  - [ ] `task-8-workflow-tab.png` — after clicking sim_debug workflow

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): wire sim_debug workflow to debug tab instead of fullscreen`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 9. **Add SourceViewer ↔ PreviewPane toggle**

  **What to do**:
  - Add a toggle button in the debug tab's source panel header (next to VCD picker or in the source toolbar)
  - Toggle switches between:
    - **SourceViewer** (from sim-debug.jsx:275-356): per-line Prism highlight, cursor line, click-to-jump
    - **PreviewPane** (from workspace.jsx:9443-9615): AST-based foldable code view
  - Store toggle preference in localStorage (`atlasDebugSourceMode`)
  - Default to SourceViewer for `.v`/`.sv` files and PreviewPane for other files
  - When toggled, preserve the current file path and cursor position if possible

  **Must NOT do**:
  - Do NOT remove SourceViewer or PreviewPane components
  - Do NOT change how either component works internally

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Conditional rendering + localStorage + button
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 12
  - **Blocked By**: Task 7

  **References**:
  - `frontend/atlas/sim-debug.jsx:275-356` — SourceViewer
  - `frontend/atlas/workspace.jsx:9443-9615` — PreviewPane

  **Acceptance Criteria**:
  - [ ] Toggle button visible in source panel
  - [ ] Clicking toggles between SourceViewer and PreviewPane
  - [ ] Preference persisted in localStorage

  **QA Scenarios**:

  ```
  Scenario: Source viewer toggle works
    Tool: Playwright
    Preconditions: Task 7 complete, debug tab open with Verilog file
    Steps:
      1. Open debug tab with a .sv file
      2. Assert: SourceViewer rendered (per-line layout)
      3. Click toggle button to switch to PreviewPane
      4. Assert: PreviewPane rendered (foldable AST view)
      5. Click toggle again
      6. Assert: back to SourceViewer
    Expected Result: Toggle switches between two viewers
    Failure Indicators: Toggle doesn't work, wrong component rendered
    Evidence: .sisyphus/evidence/task-9-source-toggle.png
  ```

  **Evidence to Capture**:
  - [ ] `task-9-source-toggle.png` — before/after toggle

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): add SourceViewer/PreviewPane toggle in debug tab`
  - Files: `frontend/atlas/sim-debug.jsx`, `frontend/atlas/workspace.jsx`

---

- [ ] 10. **Playwright E2E: Tab switching regression**

  **What to do**:
  - Create `frontend/atlas/tests/debug-tab.spec.js`
  - Test: Click `chat` tab → assert chat feed visible
  - Test: Click `debug` tab → assert debug content visible
  - Test: Click `ssot` tab → assert SSOT review visible
  - Test: Click `qa` tab → assert Q&A board visible
  - Test: Click `split` tab → assert chat + preview side-by-side
  - Test: Click `preview` tab → assert preview pane visible
  - Test: Return to `chat` tab → assert chat feed visible
  - Verify no errors in browser console during tab switches

  **Must NOT do**:
  - Do NOT modify existing Playwright tests
  - Do NOT skip any existing tabs

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: E2E test writing, tab switching flow
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 11-14)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Tasks 3, 7, 8

  **References**:
  - `playwright.config.js` — existing config
  - `frontend/atlas/workspace.jsx:3095-3175` — tab strip

  **Acceptance Criteria**:
  - [ ] All 6+ tab switching tests pass
  - [ ] No console errors during tab switches

  **QA Scenarios**:

  ```
  Scenario: All tabs switch correctly
    Tool: Bash (npx playwright test)
    Preconditions: Tasks 1-9 complete
    Steps:
      1. Run: cd frontend/atlas && npx playwright test tests/debug-tab.spec.js --grep "tab switching"
      2. Assert: all tests pass
    Expected Result: 7/7 tab switching tests pass
    Failure Indicators: Any tab fails to render
    Evidence: .sisyphus/evidence/task-10-tab-switching.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-10-tab-switching.txt` — Playwright output

  **Commit**: YES (Wave 4)
  - Message: `test(e2e): add tab switching regression tests`
  - Files: `frontend/atlas/tests/debug-tab.spec.js`

---

- [ ] 11. **Playwright E2E: No fullscreen class on body**

  **What to do**:
  - Add to `debug-tab.spec.js`:
  - Test: Open debug tab → assert `document.body` does NOT have `atlas-sim-debug-fullscreen` class
  - Test: Open debug tab, wait 2s → assert still no class
  - Test: Switch to chat, then back to debug → assert no class
  - Test: Trigger workflow 'sim_debug' → assert no class
  - This test ensures the fullscreen takeover is completely eliminated

  **Must NOT do**:
  - Do NOT check for class presence (we want absence)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Simple but critical regression test
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 10, 12-14)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Tasks 5, 8

  **References**:
  - `frontend/atlas/styles.css` — (removed) fullscreen rules
  - `frontend/atlas/workspace.jsx` — (removed) isSimDebug logic

  **Acceptance Criteria**:
  - [ ] `atlas-sim-debug-fullscreen` class NEVER appears on body
  - [ ] Tests pass for all debug tab scenarios

  **QA Scenarios**:

  ```
  Scenario: No fullscreen class
    Tool: Bash (npx playwright test)
    Preconditions: Tasks 1-9 complete
    Steps:
      1. Run: npx playwright test --grep "no fullscreen"
      2. Assert: all tests pass
    Expected Result: 4/4 tests pass
    Failure Indicators: Class detected on body
    Evidence: .sisyphus/evidence/task-11-no-fullscreen.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-11-no-fullscreen.txt` — Playwright output

  **Commit**: YES (Wave 4)
  - Message: `test(e2e): verify no fullscreen class regression`
  - Files: `frontend/atlas/tests/debug-tab.spec.js`

---

- [ ] 12. **Playwright E2E: Debug tab renders with panels**

  **What to do**:
  - Add to `debug-tab.spec.js`:
  - Test: Open debug tab → assert hierarchy tree visible (check for `.hierarchy-node` or similar)
  - Test: Assert source panel visible (`.source-viewer` or `.ace_editor` or `.code-pane`)
  - Test: Assert waveform panel visible (`.wave-panel` or `svg.wave-svg`)
  - Test: Assert debug chat visible (`.debug-chat` or similar)
  - Test: Resize left panel (drag splitter) → assert hierarchy panel width changes
  - Test: Click expand mode buttons → assert panels show/hide correctly

  **Must NOT do**:
  - Do NOT test internal sim-debug logic — test DOM presence only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Multi-panel layout verification
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 10-11, 13-14)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Tasks 7, 9

  **References**:
  - `frontend/atlas/sim-debug.jsx:1162-1167` — layout structure
  - `frontend/atlas/sim-debug.jsx:362-410` — hierarchy nodes

  **Acceptance Criteria**:
  - [ ] All 4 panels visible in debug tab
  - [ ] Panel resizing works
  - [ ] Expand modes work

  **QA Scenarios**:

  ```
  Scenario: Debug panels render
    Tool: Bash (npx playwright test)
    Preconditions: Tasks 1-9 complete
    Steps:
      1. Run: npx playwright test --grep "debug panels"
      2. Assert: all tests pass
    Expected Result: 6/6 panel tests pass
    Failure Indicators: Missing panels, resize broken
    Evidence: .sisyphus/evidence/task-12-debug-panels.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-12-debug-panels.txt` — Playwright output

  **Commit**: YES (Wave 4)
  - Message: `test(e2e): add debug tab panel rendering tests`
  - Files: `frontend/atlas/tests/debug-tab.spec.js`

---

- [ ] 13. **Playwright E2E: Other tabs unchanged**

  **What to do**:
  - Add to `debug-tab.spec.js`:
  - Test: Open chat tab → assert chat feed, input box, send button all present
  - Test: Open preview tab with `.py` file → assert Prism highlighting
  - Test: Open split tab → assert both chat and preview visible
  - Test: Open ssot tab → assert SSOT sections visible
  - Test: Verify no debug-related elements leak into other tabs

  **Must NOT do**:
  - Do NOT skip any existing tab tests

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Regression verification for all existing tabs
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 10-12, 14)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Task 7

  **References**:
  - `frontend/atlas/workspace.jsx` — all tab renderings

  **Acceptance Criteria**:
  - [ ] All existing tabs render identically
  - [ ] No debug elements in other tabs

  **QA Scenarios**:

  ```
  Scenario: Other tabs unchanged
    Tool: Bash (npx playwright test)
    Preconditions: Tasks 1-9 complete
    Steps:
      1. Run: npx playwright test --grep "other tabs"
      2. Assert: all tests pass
    Expected Result: 5/5 regression tests pass
    Failure Indicators: Broken tabs, leaked debug elements
    Evidence: .sisyphus/evidence/task-13-other-tabs.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-13-other-tabs.txt` — Playwright output

  **Commit**: YES (Wave 4)
  - Message: `test(e2e): verify other tabs unchanged by debug integration`
  - Files: `frontend/atlas/tests/debug-tab.spec.js`

---

- [ ] 14. **Playwright E2E: VCD load in debug tab**

  **What to do**:
  - Add to `debug-tab.spec.js`:
  - Test: Open debug tab → assert VCD picker dropdown visible
  - Test: Click VCD picker → assert dropdown list populated
  - Test: Select a VCD file → assert waveform SVG appears in wave panel
  - Test: Assert waveform has at least 1 WaveRow (`.wave-row` in DOM)
  - Requires a workspace with at least 1 VCD file available

  **Must NOT do**:
  - Do NOT skip if no VCD available — test should handle empty state

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: VCD-specific integration test
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 10-13)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Task 7

  **References**:
  - `frontend/atlas/sim-debug.jsx:1123-1135` — VCD picker
  - `frontend/atlas/sim-debug.jsx:481` — VCD fetch
  - `frontend/atlas/debug-shared.jsx:229-257` — WaveRow

  **Acceptance Criteria**:
  - [ ] VCD picker visible and populated
  - [ ] Selecting VCD loads waveform
  - [ ] Waveform SVG renders

  **QA Scenarios**:

  ```
  Scenario: VCD load in debug tab
    Tool: Bash (npx playwright test)
    Preconditions: Tasks 1-9 complete, workspace with VCD files
    Steps:
      1. Run: npx playwright test --grep "VCD"
      2. Assert: all VCD tests pass
    Expected Result: 3/3 VCD tests pass
    Failure Indicators: Dropdown empty, waveform missing
    Evidence: .sisyphus/evidence/task-14-vcd-load.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-14-vcd-load.txt` — Playwright output

  **Commit**: YES (Wave 4)
  - Message: `test(e2e): add VCD load tests for debug tab`
  - Files: `frontend/atlas/tests/debug-tab.spec.js`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists. For each "Must NOT Have": search codebase for forbidden patterns. Check evidence files exist.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter. Review changed files for: `as any`/`@ts-ignore`, empty catches, console.log, commented-out code. Check AI slop patterns.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Execute EVERY QA scenario from EVERY task. Test cross-task integration. Test edge cases. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff. Verify 1:1 — everything in spec was built, nothing beyond spec. Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `refactor(ui): remove sim debug fullscreen takeover`
- **Wave 2**: `refactor(ui): refactor sim-debug.jsx for embedded use`
- **Wave 3**: `feat(ui): integrate debug tab into main display`
- **Wave 4**: `test(e2e): add debug tab integration tests`
- **Wave FINAL**: `chore(verify): final verification and quality fixes`

---

## Success Criteria

### Verification Commands
```bash
# Tab switching
cd frontend/atlas && npx playwright test tests/debug-tab.spec.js

# All existing tests still pass
python -m pytest tests/ -x
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All Playwright tests pass
- [ ] Existing tests still pass
- [ ] `atlas-sim-debug-fullscreen` class never appears on body
- [ ] Other tabs (chat, ssot, qa, split, preview) render identically
- [ ] Coverage workflow fullscreen untouched
