# Interactive Verilog Viewer (v1)

## TL;DR

> **Quick Summary**: Replace Prism.js read-only preview with Ace Editor for Verilog/SV files, adding syntax-aware folding (Ace built-in) and static signal tracing (pyslang AST-based). Signal graph visualized via Cytoscape.js. FSM diagram and per-syntax feedback/editing deferred to v2.
>
> **Deliverables**:
> - Ace Editor integration for `.v`/`.sv`/`.vh`/`.svh` files (CDN + local fallback)
> - Backend `/api/ast` endpoint (pyslang → JSON AST with source locations)
> - Backend `/api/signals` endpoint (declaration/drivers/loads extraction)
> - Signal tracing sidebar panel (click signal → show drivers/loads)
> - Cytoscape.js signal graph visualization (fan-in/fan-out)
> - File size limits + pyslang error fallback
> - Playwright E2E tests for all features
>
> **Estimated Effort**: Medium (5 waves, ~18 tasks)
> **Parallel Execution**: YES — 5 waves, max 5 concurrent tasks
> **Critical Path**: PRECHECK-1 → Task 5/6 → Task 7 → Task 9/10 → Task 13 → F1-F4

---

## Context

### Original Request
> "verilog file view 에서 좀 더 interactive 한 요소가 많으면 좋겠어. pyslang 같은 걸로 syntax 단위로 폴당 하는 기능. 혹은 FSM이라면 그걸 Diagram으로 보여주는 기능. 각 syntax 단위로 피드백을 주면서 수정 할 수 있는 기능. 그리고 실제 신호를 tracing 하는 기능. load, drive 를 추적하는 기능. interactive 하면 좋겠어. planning 좀. 이게 html 웹 의 매력."

### Interview Summary
**Key Discussions**:
- **Editor**: Ace Editor (CDN-ready, Verilog mode, folding, markers) over Monaco (heavy/complex) and Prism (read-only)
- **v1 Scope**: Syntax Folding + Static Signal Tracing first; FSM Diagram + Per-syntax feedback/editing deferred to v2
- **FSM extraction**: Auto-detect from pyslang AST (deferred to v2)
- **Ace scope**: Verilog/SV files only (`.v`, `.sv`, `.vh`, `.svh`); other files keep existing Prism
- **Signal tracing**: Static analysis only (pyslang AST-based: declaration → drive points → load points); no simulation
- **Test strategy**: Playwright E2E after implementation

**Research Findings**:
- Current preview: `frontend/atlas/workspace.jsx` `PreviewPane` (9040-9257), read-only Prism
- `readAtlasAsyncResource` fetches `/api/file` (661-727); `useAtlasAsyncResource` cache hook (735-801)
- pyslang already installed at `vendor/pyslang-10.0.0.dist-info/`
- Existing pyslang endpoints: `/api/hierarchy`, `/api/elab/status` in `src/atlas_ui.py`
- Ace Editor: CDN-ready (`cdnjs.cloudflare.com/ajax/libs/ace/1.32.0/ace.js`), Verilog mode built-in, folding support
- Cytoscape.js: UMD (`unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js`), single script, pan/zoom/click

### Metis Review
**Identified Gaps** (addressed in plan):
- **PRECHECK-1**: pyslang AST source location fields must be validated before any frontend work
- **PRECHECK-2**: PreviewPane must support dynamic editor injection (not hardcoded Prism)
- **PRECHECK-3**: Ace + Cytoscape must work in Babel standalone + CDN environment
- **File size limit**: 5MB/10,000 lines — AST analysis skipped, Ace still loads
- **Ace read-only in v1**: Editing deferred to v2 despite Ace being an editor
- **CDN fallback**: Local copies in `vendor/` for offline/air-gapped usage
- **Error handling**: pyslang parse failure → 422 response + Ace still loads with folding/tracing disabled
- **Signal tracing scope**: Raw AST only — no elaboration (`/api/elab/status` not used in v1)
- **Cytoscape layout**: Hierarchical (dagre) only — no physics simulation in v1

---

## Work Objectives

### Core Objective
Transform the read-only Verilog file preview in Atlas UI into an interactive viewer with syntax-aware folding and static signal tracing, leveraging pyslang's AST capabilities and web-native interactivity.

### Concrete Deliverables
1. Ace Editor renders for `.v`/`.sv`/`.vh`/`.svh` files in `PreviewPane`
2. `/api/ast` returns pyslang JSON AST with source locations
3. `/api/signals` returns signal graph (declaration, drivers, loads)
4. Signal tracing sidebar shows drivers/loads when clicking a signal in Ace
5. Cytoscape.js renders signal fan-in/fan-out graph
6. Non-Verilog files continue using existing Prism preview
7. All features verified via Playwright E2E tests

### Definition of Done
- [ ] Open `.sv` file → Ace Editor loads with folding widgets in gutter
- [ ] Click signal in Ace → sidebar shows declaration line + drivers + loads
- [ ] Signal graph renders in Cytoscape panel with nodes and edges
- [ ] Open `.py` file → existing Prism preview unchanged
- [ ] Open 15MB `.sv` file → Ace loads, AST analysis skipped with toast message
- [ ] Open invalid Verilog → Ace loads, folding/tracing disabled gracefully
- [ ] All Playwright tests pass

### Must Have
- Ace Editor for Verilog/SV files with built-in folding
- `/api/ast` endpoint (pyslang → JSON)
- `/api/signals` endpoint (signal extraction)
- Signal tracing sidebar panel
- Cytoscape.js signal graph
- CDN + local fallback for Ace and Cytoscape
- File size limits (5MB / 10,000 lines)
- pyslang parse error fallback (Ace still loads)
- Playwright E2E tests

### Must NOT Have (Guardrails)
- Ace autocomplete/snippets (v1)
- Real-time syntax error underlining (v1)
- VHDL/SystemC support (v1)
- Code editing/saving (v1 — read-only)
- Ace theme customization (v1 — default dark only)
- Cytoscape physics simulation layout (v1 — hierarchical only)
- Signal value estimation/constant propagation (v1)
- Elaboration-based tracing (v1 — raw AST only)
- Multi-user sync for viewer state (v1)
- FSM diagram (v2)
- Per-syntax inline feedback/editing (v2)

---

## Verification Strategy

> **ZERO HUMAN INTERVENTION** — ALL verification is agent-executed. No exceptions.

### Test Decision
- **Infrastructure exists**: YES (Playwright config at `playwright.config.js`, baseURL `http://127.0.0.1:8765`)
- **Automated tests**: Tests-after implementation
- **Framework**: Playwright E2E + `curl` backend validation
- **Backend validation**: Each `/api/*` endpoint tested with `curl | jq`

### QA Policy
Every task MUST include agent-executed QA scenarios. Evidence saved to `.sisyphus/evidence/task-{N}-{scenario-slug}.{ext}`.

- **Frontend/UI**: Playwright — navigate, click signal, assert sidebar content, screenshot
- **API/Backend**: Bash (`curl`) — send requests, assert status + JSON schema
- **Integration**: Playwright — end-to-end file open → signal trace → graph render

---

## Execution Strategy

### Parallel Execution Waves

```
Wave 1 (Pre-checks + CDN Setup — foundation):
├── Task 1: PRECHECK-1 — Validate pyslang AST source locations [quick]
├── Task 2: PRECHECK-2 — Validate PreviewPane dynamic injection [quick]
├── Task 3: PRECHECK-3 — Validate Ace + Cytoscape in Babel standalone [quick]
└── Task 4: Add Ace Editor + Cytoscape.js CDN to index.html [quick]

Wave 2 (Backend APIs — after Wave 1):
├── Task 5: Create /api/ast endpoint (pyslang → JSON AST) [deep]
└── Task 6: Create /api/signals endpoint (signal graph extraction) [deep]

Wave 3 (Frontend Core — after Wave 1 + 2):
├── Task 7: Integrate Ace Editor into PreviewPane (Verilog/SV only) [visual-engineering]
├── Task 8: Enable Ace built-in Verilog folding [quick]
├── Task 9: Build signal tracing sidebar panel [visual-engineering]
└── Task 10: Build Cytoscape.js signal graph component [visual-engineering]

Wave 4 (Integration + Error Handling — after Wave 3):
├── Task 11: File size limits + pyslang error fallback [quick]
├── Task 12: Ace/Prism coexistence verification (non-Verilog files) [quick]
└── Task 13: Signal tracing + graph integration (click → update graph) [unspecified-high]

Wave 5 (Tests — after Wave 4):
├── Task 14: Playwright: Ace loads for .sv, Prism for .py [unspecified-high]
├── Task 15: Playwright: Folding widget visible and functional [unspecified-high]
├── Task 16: Playwright: Signal tracing panel shows drivers/loads [unspecified-high]
├── Task 17: Playwright: Cytoscape graph renders with nodes [unspecified-high]
└── Task 18: Playwright: Invalid Verilog → Ace still loads, tracing disabled [unspecified-high]

Wave FINAL (After ALL tasks — 4 parallel reviews, then user okay):
├── Task F1: Plan compliance audit (oracle)
├── Task F2: Code quality review (unspecified-high)
├── Task F3: Real manual QA (unspecified-high)
└── Task F4: Scope fidelity check (deep)
-> Present results -> Get explicit user okay

Critical Path: Task 1 → Task 5/6 → Task 7 → Task 9/10 → Task 13 → F1-F4 → user okay
Parallel Speedup: ~60% faster than sequential
Max Concurrent: 5 (Wave 3)
```

### Dependency Matrix

| Task | Blocked By | Blocks |
|------|-----------|--------|
| 1 (PRECHECK-1) | — | 5, 6 |
| 2 (PRECHECK-2) | — | 7 |
| 3 (PRECHECK-3) | — | 4, 7, 10 |
| 4 (CDN Setup) | — | 7, 10 |
| 5 (/api/ast) | 1 | 9, 11, 14, 15, 16, 18 |
| 6 (/api/signals) | 1 | 9, 10, 11, 13, 16 |
| 7 (Ace Integration) | 2, 3, 4 | 8, 9, 12, 13, 14, 15, 18 |
| 8 (Folding) | 7 | 15 |
| 9 (Tracing Panel) | 5, 6, 7 | 13, 16 |
| 10 (Cytoscape Graph) | 3, 4, 6 | 13, 17 |
| 11 (Error Handling) | 5, 6, 7 | 18 |
| 12 (Coexistence) | 7 | 14 |
| 13 (Integration) | 7, 9, 10 | — |
| 14 (Test: Ace/Prism) | 5, 7, 12 | — |
| 15 (Test: Folding) | 5, 7, 8 | — |
| 16 (Test: Tracing) | 5, 6, 9 | — |
| 17 (Test: Graph) | 6, 10 | — |
| 18 (Test: Error) | 5, 7, 11 | — |

### Agent Dispatch Summary

- **Wave 1**: **4** — T1-T3 → `quick`, T4 → `quick`
- **Wave 2**: **2** — T5 → `deep`, T6 → `deep`
- **Wave 3**: **4** — T7 → `visual-engineering`, T8 → `quick`, T9 → `visual-engineering`, T10 → `visual-engineering`
- **Wave 4**: **3** — T11 → `quick`, T12 → `quick`, T13 → `unspecified-high`
- **Wave 5**: **5** — T14-T18 → `unspecified-high`
- **FINAL**: **4** — F1 → `oracle`, F2 → `unspecified-high`, F3 → `unspecified-high`, F4 → `deep`

---

## TODOs

- [ ] 1. **PRECHECK-1: Validate pyslang AST source locations**

  **What to do**:
  - Open a Python REPL with pyslang available
  - Parse a simple Verilog module: `module m; wire a; assign a = 1'b1; endmodule`
  - Inspect the AST tree nodes for source location fields (line, column, offset, or `sourceRange`)
  - Verify that every syntax node (module, wire, assign, etc.) has retrievable start/end positions
  - Test with a slightly complex snippet: `always @(*) begin if (x) y = z; end`
  - Document the exact field names and data types in a comment

  **Must NOT do**:
  - Do NOT proceed to any other task if source locations are missing or unusable
  - Do NOT write any frontend or backend code yet

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple Python REPL verification, 5-minute task
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 2, 3, 4)
  - **Blocks**: Tasks 5, 6 (backend API development)
  - **Blocked By**: None

  **References**:
  - `vendor/pyslang-10.0.0.dist-info/` — installed pyslang package
  - `config.py:1318-1321` — pyslang is default backend
  - `src/atlas_ui.py:801-808` — existing `/api/hierarchy` using pyslang
  - External: https://sv-lang.com/pyslang/ — pyslang API reference

  **Acceptance Criteria**:
  - [ ] pyslang REPL shows source location fields for all tested nodes
  - [ ] Field names documented (e.g., `start`, `end`, `sourceRange`, `line`, `column`)

  **QA Scenarios**:

  ```
  Scenario: pyslang AST has source locations
    Tool: Bash (python -c)
    Preconditions: pyslang installed in vendor/
    Steps:
      1. Run: python -c "import pyslang; t = pyslang.SyntaxTree.fromText('module m; endmodule'); print(dir(t.root))"
      2. Assert: output contains location-related attributes (sourceRange, start, end, line, etc.)
      3. Run: python -c "import pyslang; t = pyslang.SyntaxTree.fromText('module m;\\n  wire a;\\nendmodule'); n = t.root.members[0]; print(n.sourceRange)"
      4. Assert: output shows line/column or offset range (non-None, non-empty)
    Expected Result: pyslang AST nodes expose retrievable source locations
    Failure Indicators: None/empty/missing location fields
    Evidence: .sisyphus/evidence/task-1-pyslang-locations.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-1-pyslang-locations.txt` — REPL output showing field names and sample values

  **Commit**: NO (pre-check, no code changes)

---

- [ ] 2. **PRECHECK-2: Validate PreviewPane dynamic editor injection**

  **What to do**:
  - Read `frontend/atlas/workspace.jsx` lines 9040-9257 (`PreviewPane` component)
  - Analyze how the current editor/renderer is determined (hardcoded Prism or conditional?)
  - Check if `PreviewPane` receives props that could be used to switch editors
  - Check if there's already a conditional path for different file types (Markdown vs code)
  - Document: can Ace Editor be injected conditionally based on file extension WITHOUT modifying Prism logic?

  **Must NOT do**:
  - Do NOT modify `workspace.jsx` yet
  - Do NOT break existing Markdown or diff preview paths

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Read-only code analysis
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 3, 4)
  - **Blocks**: Task 7 (Ace integration)
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/workspace.jsx:9040-9257` — `PreviewPane` component
  - `frontend/atlas/workspace.jsx:661-727` — `readAtlasAsyncResource`
  - `frontend/atlas/workspace.jsx:3152-3207` — center layout rendering (where PreviewPane is used)
  - `frontend/atlas/workspace.jsx:3193-3204` — conditional rendering (gitShow, ssot, preview)

  **Acceptance Criteria**:
  - [ ] Documented: whether PreviewPane uses props or hardcoded renderer
  - [ ] Documented: recommended injection strategy (conditional render, prop-based, or wrapper)

  **QA Scenarios**:

  ```
  Scenario: PreviewPane structure analysis
    Tool: Read (file)
    Preconditions: workspace.jsx exists
    Steps:
      1. Read workspace.jsx lines 9040-9257
      2. Identify: how `PreviewPane` determines which renderer to use
      3. Check: are there existing conditionals for Markdown (DeferredMarkdownPreview) vs code?
      4. Determine: can we add `isVerilog(path)` conditional without touching Prism paths?
    Expected Result: Clear documentation of injection strategy
    Failure Indicators: Hardcoded Prism with no extension point
    Evidence: .sisyphus/evidence/task-2-previewpane-analysis.md
  ```

  **Evidence to Capture**:
  - [ ] `task-2-previewpane-analysis.md` — structural analysis with line numbers and recommendations

  **Commit**: NO (pre-check, no code changes)

---

- [ ] 3. **PRECHECK-3: Validate Ace + Cytoscape in Babel standalone environment**

  **What to do**:
  - Create a temporary HTML file that loads Babel standalone (same as Atlas)
  - Load Ace Editor from CDN (`cdnjs.cloudflare.com/ajax/libs/ace/1.32.0/ace.js`)
  - Load Cytoscape.js from CDN (`unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js`)
  - Verify: `window.ace` and `window.cytoscape` are defined after load
  - Verify: Ace can create an editor with `ace.edit()` and set Verilog mode
  - Verify: Cytoscape can create a graph with `cytoscape({...})`
  - Also test: download both libraries to `vendor/` and load from local path
  - Verify local fallback works identically

  **Must NOT do**:
  - Do NOT modify Atlas `index.html` yet
  - Do NOT install npm packages

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple HTML/JS smoke test
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES
  - **Parallel Group**: Wave 1 (with Tasks 1, 2, 4)
  - **Blocks**: Tasks 4, 7, 10
  - **Blocked By**: None

  **References**:
  - `frontend/atlas/index.html` — existing CDN loading pattern for Prism
  - External: https://cdnjs.cloudflare.com/ajax/libs/ace/1.32.0/ace.js
  - External: https://unpkg.com/cytoscape@3.26.0/dist/cytoscape.min.js

  **Acceptance Criteria**:
  - [ ] CDN smoke test HTML works: Ace Verilog editor + Cytoscape graph both render
  - [ ] Local vendor/ smoke test HTML works identically

  **QA Scenarios**:

  ```
  Scenario: CDN smoke test
    Tool: Bash (create temp HTML, open with headless browser or curl check)
    Preconditions: internet access
    Steps:
      1. Create /tmp/ace-cy-test.html loading Babel + Ace + Cytoscape CDNs
      2. Add script: console.log(typeof window.ace, typeof window.cytoscape)
      3. Open with python -m http.server + curl or Playwright
      4. Assert: both are 'object' or 'function'
    Expected Result: Both libraries expose global objects in Babel standalone environment
    Failure Indicators: undefined, load errors, CORS issues
    Evidence: .sisyphus/evidence/task-3-cdn-smoke.html

  Scenario: Local vendor fallback test
    Tool: Bash
    Preconditions: vendor/ directory exists
    Steps:
      1. Download ace.js and cytoscape.min.js to vendor/ace/ and vendor/cytoscape/
      2. Create /tmp/local-test.html loading from ../vendor/ paths
      3. Verify same functionality as CDN test
    Expected Result: Local copies work identically
    Failure Indicators: Missing files, path errors, version mismatch
    Evidence: .sisyphus/evidence/task-3-local-smoke.html
  ```

  **Evidence to Capture**:
  - [ ] `task-3-cdn-smoke.html` — working CDN test page
  - [ ] `task-3-local-smoke.html` — working local fallback test page

  **Commit**: NO (pre-check, no code changes — but vendor/ downloads may be committed in Task 4)

---

- [ ] 4. **Add Ace Editor + Cytoscape.js CDN to index.html with local fallback**

  **What to do**:
  - Add Ace Editor script tag to `frontend/atlas/index.html` after Prism scripts
  - Add Cytoscape.js script tag to `frontend/atlas/index.html`
  - Download both libraries to `vendor/ace/` and `vendor/cytoscape/` for offline fallback
  - Add conditional loading: try CDN first, fall back to local if CDN fails (use `script.onerror`)
  - Ensure loading order: Ace after React, Cytoscape after Ace (or independent)
  - Verify: `index.html` still loads correctly, no console errors

  **Must NOT do**:
  - Do NOT remove existing Prism scripts
  - Do NOT change loading order of existing dependencies (React, Babel, Prism)
  - Do NOT use `type="module"` — must work with Babel standalone

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Script tag addition, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 1, 2, 3)
  - **Parallel Group**: Wave 1
  - **Blocks**: Tasks 7, 10
  - **Blocked By**: Task 3 (local fallback validated)

  **References**:
  - `frontend/atlas/index.html:43-64` — existing Prism CDN loading
  - `frontend/atlas/index.html:1-100` — full head section for dependency order

  **Acceptance Criteria**:
  - [ ] `index.html` loads Ace and Cytoscape without console errors
  - [ ] `window.ace` and `window.cytoscape` available after page load
  - [ ] Fallback mechanism works (test by blocking CDN domain)

  **QA Scenarios**:

  ```
  Scenario: Libraries load successfully
    Tool: Playwright
    Preconditions: Atlas UI server running
    Steps:
      1. Navigate to http://127.0.0.1:8765
      2. Wait for page load (timeout: 10s)
      3. Evaluate: `typeof window.ace !== 'undefined'`
      4. Evaluate: `typeof window.cytoscape !== 'undefined'`
    Expected Result: Both return true
    Failure Indicators: undefined, script load errors in console
    Evidence: .sisyphus/evidence/task-4-library-load.png

  Scenario: CDN fallback works
    Tool: Playwright
    Preconditions: Atlas UI running
    Steps:
      1. Block cdnjs.cloudflare.com and unpkg.com via route interception
      2. Refresh page
      3. Evaluate: `typeof window.ace !== 'undefined'`
      4. Evaluate: `typeof window.cytoscape !== 'undefined'`
    Expected Result: Both still return true (loaded from vendor/)
    Failure Indicators: undefined, 404 errors for vendor/ paths
    Evidence: .sisyphus/evidence/task-4-fallback.png
  ```

  **Evidence to Capture**:
  - [ ] `task-4-library-load.png` — screenshot showing console with no errors
  - [ ] `task-4-fallback.png` — screenshot with CDN blocked, libraries still loaded

  **Commit**: YES (Wave 1)
  - Message: `feat(verilog-viewer): add Ace Editor + Cytoscape.js CDN with local fallback`
  - Files: `frontend/atlas/index.html`, `vendor/ace/*`, `vendor/cytoscape/*`

---

- [ ] 5. **Create `/api/ast` endpoint (pyslang → JSON AST)**

  **What to do**:
  - Add FastAPI endpoint `POST /api/ast` in `src/atlas_ui.py`
  - Request body: `{"path": "path/to/file.sv"}`
  - Use pyslang to parse the file: `pyslang.SyntaxTree.fromFile(path)` or `fromText(content)`
  - Recursively traverse AST and extract: node type, source location (start line/col, end line/col), text snippet
  - Return JSON: `{"tree": {...}, "error": null}` or `{"tree": null, "error": "..."}`
  - Handle errors: file not found (404), parse error (422), file too large (413), pyslang not available (500)
  - Add file size check: skip AST if >5MB or >10,000 lines — return `{"tree": null, "error": "File too large for AST analysis"}`
  - Ensure response includes CORS headers if needed
  - Add a simple test: create `test_data/simple_module.sv` with a small Verilog module for testing

  **Must NOT do**:
  - Do NOT cache AST results in external DB (use in-memory LRU or no cache)
  - Do NOT use elaboration data — raw parse tree only
  - Do NOT preprocess `include files (single file scope)
  - Do NOT return full AST for files >5MB

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: pyslang AST traversal is nuanced; needs careful JSON serialization
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 6)
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 9, 11, 14, 15, 16, 18
  - **Blocked By**: Task 1 (PRECHECK-1 — source locations validated)

  **References**:
  - `src/atlas_ui.py:801-808` — existing `/api/hierarchy` using pyslang
  - `src/atlas_ui.py:832+` — existing `/api/elab/status`
  - `config.py:1318-1321` — pyslang backend config
  - `vendor/pyslang-10.0.0.dist-info/` — pyslang package
  - External: https://sv-lang.com/pyslang/ — pyslang API

  **Acceptance Criteria**:
  - [ ] `curl -X POST /api/ast -d '{"path":"test_data/simple_module.sv"}'` returns HTTP 200 with `tree` field
  - [ ] Response JSON contains source locations for all major nodes (module, port, wire, assign, always)
  - [ ] Invalid Verilog returns HTTP 422 with error message
  - [ ] Nonexistent file returns HTTP 404
  - [ ] 6MB file returns HTTP 200 with `tree: null` and error message

  **QA Scenarios**:

  ```
  Scenario: Valid Verilog AST extraction
    Tool: Bash (curl)
    Preconditions: test_data/simple_module.sv exists, server running
    Steps:
      1. Create test_data/simple_module.sv: "module simple(input clk, output reg q); always @(posedge clk) q <= ~q; endmodule"
      2. Run: curl -s -X POST http://127.0.0.1:8765/api/ast -H "Content-Type: application/json" -d '{"path":"test_data/simple_module.sv"}' | jq '.'
      3. Assert: .tree is not null
      4. Assert: .tree contains nodes with type "ModuleDeclaration" or similar
      5. Assert: nodes have location fields (startLine, endLine, etc.)
    Expected Result: Valid JSON AST with source locations
    Failure Indicators: null tree, missing locations, 500 error
    Evidence: .sisyphus/evidence/task-5-ast-valid.json

  Scenario: Invalid Verilog handling
    Tool: Bash (curl)
    Preconditions: server running
    Steps:
      1. Create test_data/broken.sv: "module broken("
      2. Run: curl -s -X POST /api/ast -d '{"path":"test_data/broken.sv"}' -w "\nHTTP:%{http_code}"
      3. Assert: HTTP code is 422
      4. Assert: response contains error field with parse error message
    Expected Result: Graceful error with 422 status
    Failure Indicators: 500 error, server crash, empty response
    Evidence: .sisyphus/evidence/task-5-ast-error.txt

  Scenario: Large file skipped
    Tool: Bash (curl + dd)
    Preconditions: server running
    Steps:
      1. Create test_data/large.sv: 6MB of repeated "wire wN; assign wN = 1'b0;\n"
      2. Run: curl -s -X POST /api/ast -d '{"path":"test_data/large.sv"}' | jq '.'
      3. Assert: .tree is null
      4. Assert: .error contains "too large" or "File too large"
    Expected Result: tree is null, error explains size limit
    Failure Indicators: Server OOM, timeout, partial AST returned
    Evidence: .sisyphus/evidence/task-5-ast-large.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-5-ast-valid.json` — sample /api/ast response
  - [ ] `task-5-ast-error.txt` — error response
  - [ ] `task-5-ast-large.txt` — large file rejection

  **Commit**: YES (Wave 2)
  - Message: `feat(api): add /api/ast endpoint for pyslang AST extraction`
  - Files: `src/atlas_ui.py`, `test_data/simple_module.sv`

---

- [ ] 6. **Create `/api/signals` endpoint (signal graph extraction)**

  **What to do**:
  - Add FastAPI endpoint `POST /api/signals` in `src/atlas_ui.py`
  - Request body: `{"path": "path/to/file.sv"}`
  - Use pyslang to parse the file (same as /api/ast)
  - Extract signals: `wire`, `reg`, `logic`, `input`, `output`, `inout` declarations
  - For each signal, find:
    - Declaration: line, column, declaration text
    - Drivers: all assignments (`assign`, `always` block LHS, procedural assignments)
    - Loads: all RHS references to the signal
  - Return JSON: `{"signals": [{"name": "clk", "type": "input", "declaration_line": 2, "drivers": [...], "loads": [...]}]}`
  - Handle same errors as /api/ast (404, 422, 413)
  - Same file size limit: >5MB → return empty signals with error
  - v1 scope: raw AST only — do NOT use elaboration data
  - v1 scope: same module only — do NOT trace across `include files

  **Must NOT do**:
  - Do NOT trace signals across module instantiations (hierarchical tracing is v2)
  - Do NOT handle `interface`, `class`, `enum`, `typedef` signals (v2)
  - Do NOT use elaboration — raw parse tree assignments only
  - Do NOT cache in external DB

  **Recommended Agent Profile**:
  - **Category**: `deep`
    - Reason: Signal extraction from AST requires understanding pyslang node types for assignments, references, ports
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Task 5)
  - **Parallel Group**: Wave 2
  - **Blocks**: Tasks 9, 10, 11, 13, 16, 17
  - **Blocked By**: Task 1 (PRECHECK-1)

  **References**:
  - `src/atlas_ui.py:801-808` — `/api/hierarchy` pattern
  - `src/atlas_ui.py:832+` — `/api/elab/status` pattern
  - `vendor/pyslang-10.0.0.dist-info/` — pyslang API
  - External: https://sv-lang.com/pyslang/ — AST node types

  **Acceptance Criteria**:
  - [ ] `curl /api/signals` returns signals array for valid Verilog
  - [ ] Each signal has name, type, declaration_line, drivers, loads
  - [ ] Driver entries contain line, column, and assignment text
  - [ ] Load entries contain line, column, and reference context
  - [ ] Invalid Verilog returns 422

  **QA Scenarios**:

  ```
  Scenario: Signal extraction from simple module
    Tool: Bash (curl)
    Preconditions: test_data/simple_module.sv exists
    Steps:
      1. Run: curl -s -X POST /api/signals -d '{"path":"test_data/simple_module.sv"}' | jq '.'
      2. Assert: .signals is an array with length >= 2 (clk, q)
      3. Assert: .signals[] | select(.name == "q") | .type == "output"
      4. Assert: .signals[] | select(.name == "q") | .drivers | length >= 1
      5. Assert: .signals[] | select(.name == "clk") | .loads | length >= 1
    Expected Result: Correct signal graph with drivers and loads
    Failure Indicators: empty signals, missing drivers/loads, wrong types
    Evidence: .sisyphus/evidence/task-6-signals-simple.json

  Scenario: Multiple drivers detection
    Tool: Bash (curl)
    Preconditions: server running
    Steps:
      1. Create test_data/multi_drive.sv with two assign statements to same wire
      2. Run: curl -s -X POST /api/signals -d '{"path":"test_data/multi_drive.sv"}' | jq '.signals[] | select(.name == "x") | .drivers | length'
      3. Assert: output is 2
    Expected Result: Both assignments detected as drivers
    Failure Indicators: Only 1 driver detected, or none
    Evidence: .sisyphus/evidence/task-6-signals-multi.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-6-signals-simple.json` — sample /api/signals response
  - [ ] `task-6-signals-multi.txt` — multiple drivers test

  **Commit**: YES (Wave 2)
  - Message: `feat(api): add /api/signals endpoint for static signal tracing`
  - Files: `src/atlas_ui.py`, `test_data/multi_drive.sv`

---

- [ ] 7. **Integrate Ace Editor into PreviewPane (Verilog/SV only)**

  **What to do**:
  - Modify `frontend/atlas/workspace.jsx` `PreviewPane` component (9040-9257)
  - Add a conditional check: if file extension is `.v`, `.sv`, `.vh`, `.svh` → render Ace Editor
  - Otherwise → keep existing Prism preview (unchanged)
  - Ace Editor initialization:
    - Create a `<div>` ref for Ace container
    - Call `ace.edit(container)` after component mount
    - Set mode to `ace/mode/verilog`
    - Set theme to `ace/theme/tomorrow` (or `ace/theme/monokai` to match dark theme)
    - Set `readOnly: true` (v1)
    - Load file content from `useAtlasAsyncResource('file', path)` into Ace session
    - Clean up Ace instance on unmount (destroy editor)
  - Ensure Ace Editor container has proper sizing (fill parent height/width)
  - Add CSS for Ace container to match existing preview pane styling

  **Must NOT do**:
  - Do NOT modify Prism logic for non-Verilog files
  - Do NOT remove existing Markdown preview (`DeferredMarkdownPreview`)
  - Do NOT enable editing in v1 (`readOnly: true`)
  - Do NOT change Ace theme dynamically

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: React component integration, DOM refs, CSS styling for editor container
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 8, 9, 10 in Wave 3)
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 8, 9, 12, 13, 14, 15, 18
  - **Blocked By**: Tasks 2 (PreviewPane analysis), 3 (Ace validated), 4 (CDN added)

  **References**:
  - `frontend/atlas/workspace.jsx:9040-9257` — `PreviewPane` (modify carefully)
  - `frontend/atlas/workspace.jsx:3152-3207` — layout where PreviewPane is rendered
  - `frontend/atlas/index.html` — Ace CDN loading (ensure loaded before PreviewPane mounts)
  - `frontend/atlas/styles.css:608-685` — Prism color overrides (Ace needs its own theme)

  **Acceptance Criteria**:
  - [ ] Opening `.sv` file shows Ace Editor instead of Prism
  - [ ] Opening `.py` file still shows Prism (unchanged)
  - [ ] Ace displays file content correctly
  - [ ] Ace editor fills preview pane without overflow

  **QA Scenarios**:

  ```
  Scenario: Ace loads for Verilog file
    Tool: Playwright
    Preconditions: Atlas UI running, test_data/simple_module.sv exists
    Steps:
      1. Navigate to Atlas UI
      2. Click file tree item "simple_module.sv"
      3. Wait 2s for preview to load
      4. Assert: DOM contains `.ace_editor` element
      5. Assert: DOM does NOT contain `.prism-code` (for this file)
      6. Screenshot: preview pane showing Ace with Verilog content
    Expected Result: Ace Editor renders with syntax highlighting
    Failure Indicators: Prism still showing, Ace not initialized, content blank
    Evidence: .sisyphus/evidence/task-7-ace-verilog.png

  Scenario: Prism still works for Python file
    Tool: Playwright
    Preconditions: Atlas UI running, a .py file exists
    Steps:
      1. Click a .py file in file tree
      2. Wait 2s
      3. Assert: DOM contains `.prism-code` or existing Prism selector
      4. Assert: DOM does NOT contain `.ace_editor`
    Expected Result: Existing Prism preview unchanged
    Failure Indicators: Ace loaded for .py, Prism broken
    Evidence: .sisyphus/evidence/task-7-prism-python.png
  ```

  **Evidence to Capture**:
  - [ ] `task-7-ace-verilog.png` — Ace rendering Verilog
  - [ ] `task-7-prism-python.png` — Prism still working for Python

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): integrate Ace Editor for Verilog/SV files in PreviewPane`
  - Files: `frontend/atlas/workspace.jsx`, `frontend/atlas/styles.css`

---

- [ ] 8. **Enable Ace built-in Verilog folding**

  **What to do**:
  - After Ace Editor is initialized in Task 7, enable folding:
    - `editor.session.setFoldStyle("markbeginend")`
    - `editor.session.setOption("foldStyle", "markbeginend")`
    - Or use `editor.session.foldAll()` to auto-fold on load
  - Verify folding widgets appear in gutter for:
    - `module` / `endmodule`
    - `always` / `end`
    - `begin` / `end`
    - `if` / `else` / `end`
    - `case` / `endcase`
    - `generate` / `endgenerate`
    - `task` / `endtask`
    - `function` / `endfunction`
  - Add a toggle button in preview meta strip (next to refresh/copy) to "Fold All" / "Unfold All"
  - Store fold state per file (optional v1 — can defer)

  **Must NOT do**:
  - Do NOT implement custom folding based on pyslang AST (v2)
  - Do NOT modify Ace's Verilog mode grammar
  - Do NOT auto-fold everything on load if it harms UX (test and decide)

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Simple Ace API calls + UI button addition
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 9, 10)
  - **Parallel Group**: Wave 3
  - **Blocks**: Task 15 (folding test)
  - **Blocked By**: Task 7 (Ace integrated)

  **References**:
  - `frontend/atlas/workspace.jsx:9160-9179` — preview meta strip (add fold toggle here)
  - Ace Editor docs: `session.setFoldStyle()`, `session.foldAll()`, `session.unfold()`

  **Acceptance Criteria**:
  - [ ] Folding widgets visible in gutter for `module`/`endmodule`
  - [ ] Clicking widget toggles fold/unfold
  - [ ] "Fold All" / "Unfold All" buttons in meta strip work

  **QA Scenarios**:

  ```
  Scenario: Folding widgets visible
    Tool: Playwright
    Preconditions: Task 7 complete, simple_module.sv open
    Steps:
      1. Open simple_module.sv in Ace
      2. Assert: gutter contains `.ace_fold-widget` elements (at least 1)
      3. Screenshot: gutter showing fold arrows
    Expected Result: Fold widgets visible next to foldable regions
    Failure Indicators: No fold widgets, gutter empty
    Evidence: .sisyphus/evidence/task-8-fold-widgets.png

  Scenario: Fold/unfold interaction
    Tool: Playwright
    Preconditions: Ace loaded with foldable code
    Steps:
      1. Count visible lines in Ace
      2. Click first `.ace_fold-widget` in gutter
      3. Assert: visible lines decreased (content folded)
      4. Click same widget again
      5. Assert: visible lines restored
    Expected Result: Toggle fold/unfold works
    Failure Indicators: Lines don't change, widget not clickable
    Evidence: .sisyphus/evidence/task-8-fold-toggle.png
  ```

  **Evidence to Capture**:
  - [ ] `task-8-fold-widgets.png` — gutter with fold arrows
  - [ ] `task-8-fold-toggle.png` — before/after fold

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): enable Ace Editor Verilog code folding`
  - Files: `frontend/atlas/workspace.jsx`, `frontend/atlas/styles.css`

---

- [ ] 9. **Build signal tracing sidebar panel**

  **What to do**:
  - Create a new React component `SignalTracePanel` in `workspace.jsx` (or separate file)
  - Panel shows when a signal is selected in Ace Editor
  - Selection mechanism: double-click or context menu on a signal name in Ace
  - Panel content (3 sections):
    1. **Declaration**: line number, type (wire/reg/logic/port), declaration text
    2. **Drivers**: list of lines where signal is assigned (LHS), each clickable to jump to line
    3. **Loads**: list of lines where signal is referenced (RHS), each clickable to jump to line
  - Fetch data from `/api/signals` when file is opened (or when signal is selected)
  - Cache `/api/signals` response in component state
  - Panel should be collapsible (show/hide toggle)
  - Panel positioning: right sidebar of preview area, or bottom split

  **Must NOT do**:
  - Do NOT trace across module boundaries (hierarchical tracing v2)
  - Do NOT show signal values (simulation v2)
  - Do NOT highlight drivers/loads in Ace yet (that needs markers — can be v1.5)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: React panel component, API integration, click-to-jump interaction
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8, 10)
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 13, 16
  - **Blocked By**: Tasks 5, 6 (APIs exist), 7 (Ace integrated)

  **References**:
  - `frontend/atlas/workspace.jsx:3152-3207` — layout structure (find space for panel)
  - `frontend/atlas/workspace.jsx:522-569` — `Splitter` component (can split preview area)
  - `frontend/atlas/workspace.jsx:9040-9257` — `PreviewPane`

  **Acceptance Criteria**:
  - [ ] Panel appears when selecting a signal in Ace
  - [ ] Panel shows declaration, drivers, loads sections
  - [ ] Clicking a driver/load line jumps Ace cursor to that line
  - [ ] Panel is collapsible

  **QA Scenarios**:

  ```
  Scenario: Signal tracing panel shows drivers and loads
    Tool: Playwright
    Preconditions: Task 5-8 complete, simple_module.sv open
    Steps:
      1. Open simple_module.sv in Ace
      2. Double-click signal name "q" in Ace editor
      3. Assert: `.signal-trace-panel` appears in DOM
      4. Assert: panel contains text "Declaration" with line number
      5. Assert: panel contains "Drivers" section with at least 1 entry
      6. Assert: panel contains "Loads" section (may be 0 for output)
      7. Screenshot: panel showing trace info
    Expected Result: Panel populated with signal trace data
    Failure Indicators: Panel empty, wrong signal, API error
    Evidence: .sisyphus/evidence/task-9-trace-panel.png

  Scenario: Click driver jumps to line
    Tool: Playwright
    Preconditions: Trace panel open with drivers listed
    Steps:
      1. Click first driver entry in panel
      2. Assert: Ace cursor line changed to driver line number
      3. Assert: Ace scrolls to show the line
    Expected Result: Cursor jumps to selected driver
    Failure Indicators: Cursor doesn't move, wrong line
    Evidence: .sisyphus/evidence/task-9-trace-jump.png
  ```

  **Evidence to Capture**:
  - [ ] `task-9-trace-panel.png` — panel showing declaration/drivers/loads
  - [ ] `task-9-trace-jump.png` — after clicking driver, cursor at correct line

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): add signal tracing sidebar panel`
  - Files: `frontend/atlas/workspace.jsx`, `frontend/atlas/styles.css`

---

- [ ] 10. **Build Cytoscape.js signal graph component**

  **What to do**:
  - Create a new React component `SignalGraph` in `workspace.jsx` (or separate file)
  - Component initializes Cytoscape.js in a `<div>` container
  - Graph data comes from `/api/signals` response:
    - Nodes: selected signal + its drivers + its loads
    - Edges: driver → signal (labeled with assignment type), signal → load (labeled with context)
  - Graph styling:
    - Selected signal: highlighted color (e.g., orange)
    - Drivers: one color (e.g., blue)
    - Loads: another color (e.g., green)
    - Edges: arrows showing direction
  - Layout: use `dagre` (hierarchical) or `grid` — NOT physics simulation
  - Interactivity (v1):
    - Pan and zoom
    - Hover nodes to see line number tooltip
  - Position: adjacent to signal trace panel (right sidebar or bottom tab)
  - Handle empty state: "Select a signal to view graph"

  **Must NOT do**:
  - Do NOT use force-directed/physics layout (v1 — hierarchical only)
  - Do NOT make nodes clickable to jump to code (v2)
  - Do NOT show module hierarchy (v2)
  - Do NOT animate transitions (performance)

  **Recommended Agent Profile**:
  - **Category**: `visual-engineering`
    - Reason: Cytoscape.js graph rendering, React integration, styling
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 7, 8, 9)
  - **Parallel Group**: Wave 3
  - **Blocks**: Tasks 13, 17
  - **Blocked By**: Tasks 3, 4 (Cytoscape validated + CDN), 6 (signals API)

  **References**:
  - `frontend/atlas/workspace.jsx` — layout for graph placement
  - Cytoscape.js docs: `cytoscape({ elements: [...], style: [...], layout: { name: 'dagre' } })`
  - `frontend/atlas/index.html` — Cytoscape CDN loading

  **Acceptance Criteria**:
  - [ ] Graph container renders when signal selected
  - [ ] Graph contains nodes for signal, drivers, loads
  - [ ] Edges show direction with arrows
  - [ ] Pan/zoom works
  - [ ] Empty state message shown when no signal selected

  **QA Scenarios**:

  ```
  Scenario: Signal graph renders with nodes and edges
    Tool: Playwright
    Preconditions: Task 6-9 complete, simple_module.sv open, signal "q" selected
    Steps:
      1. Select signal "q" in Ace (double-click)
      2. Wait 1s for graph to render
      3. Assert: `#signal-graph-container` (or similar) contains canvas
      4. Assert: Cytoscape instance has >= 1 node (the signal itself)
      5. Screenshot: graph showing nodes and edges
    Expected Result: Directed graph with signal node and connected drivers/loads
    Failure Indicators: Empty canvas, no nodes, Cytoscape init error
    Evidence: .sisyphus/evidence/task-10-graph-render.png

  Scenario: Empty state
    Tool: Playwright
    Preconditions: Ace loaded, no signal selected
    Steps:
      1. Open simple_module.sv
      2. Do NOT select any signal
      3. Assert: graph area shows "Select a signal to view graph" or similar message
    Expected Result: Helpful empty state instead of blank canvas
    Failure Indicators: Blank area, loading spinner forever
    Evidence: .sisyphus/evidence/task-10-graph-empty.png
  ```

  **Evidence to Capture**:
  - [ ] `task-10-graph-render.png` — graph with nodes and edges
  - [ ] `task-10-graph-empty.png` — empty state message

  **Commit**: YES (Wave 3)
  - Message: `feat(ui): add Cytoscape.js signal graph visualization`
  - Files: `frontend/atlas/workspace.jsx`, `frontend/atlas/styles.css`

---

- [ ] 11. **File size limits + pyslang error fallback**

  **What to do**:
  - In `PreviewPane`, before fetching `/api/ast` or `/api/signals`, check file size from `useAtlasAsyncResource` response
  - If file > 5MB or > 10,000 lines: show toast/message "File too large for AST analysis — editor only"
  - Still load Ace Editor, but skip API calls for AST and signals
  - When `/api/ast` or `/api/signals` returns 422 (parse error): show toast "Syntax error — signal tracing disabled"
  - Ace Editor still loads and displays file content even on parse error
  - Add error state UI: subtle indicator in preview meta strip (e.g., yellow dot with tooltip)
  - Handle 404 (file not found): show error message in preview area

  **Must NOT do**:
  - Do NOT block Ace Editor from loading on any error
  - Do NOT crash frontend on API errors
  - Do NOT show intrusive modal dialogs for errors

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Conditional checks + toast UI, no complex logic
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 12, 13)
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 18 (error handling test)
  - **Blocked By**: Tasks 5, 6, 7

  **References**:
  - `frontend/atlas/workspace.jsx:661-727` — `readAtlasAsyncResource` returns size info
  - `frontend/atlas/workspace.jsx:9040-9257` — `PreviewPane` (add error handling)

  **Acceptance Criteria**:
  - [ ] Large file (>5MB) opens in Ace without AST analysis
  - [ ] Invalid Verilog opens in Ace with signal tracing disabled
  - [ ] Error indicators are subtle (not blocking)

  **QA Scenarios**:

  ```
  Scenario: Large file opens without AST analysis
    Tool: Playwright
    Preconditions: 6MB test file exists
    Steps:
      1. Open large.sv in Ace
      2. Assert: Ace loads and shows content
      3. Assert: toast or meta strip shows "File too large for AST analysis"
      4. Assert: signal tracing panel shows empty/disabled state
    Expected Result: Editor works, advanced features disabled gracefully
    Failure Indicators: File doesn't open, crash, spinner forever
    Evidence: .sisyphus/evidence/task-11-large-file.png

  Scenario: Invalid Verilog still opens in Ace
    Tool: Playwright
    Preconditions: broken.sv exists (syntax error)
    Steps:
      1. Open broken.sv in Ace
      2. Assert: Ace loads with content visible
      3. Assert: toast shows "Syntax error — signal tracing disabled"
      4. Assert: signal tracing panel is disabled/hidden
    Expected Result: Graceful degradation
    Failure Indicators: Blank preview, crash, no error message
    Evidence: .sisyphus/evidence/task-11-error-fallback.png
  ```

  **Evidence to Capture**:
  - [ ] `task-11-large-file.png` — large file with disabled features
  - [ ] `task-11-error-fallback.png` — invalid file with error message

  **Commit**: YES (Wave 4)
  - Message: `feat(ui): add file size limits and pyslang error fallback`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 12. **Ace/Prism coexistence verification (non-Verilog files)**

  **What to do**:
  - Systematically test that non-Verilog files still use Prism:
    - `.py` — Python syntax highlighting
    - `.md` — Markdown preview (`DeferredMarkdownPreview`)
    - `.txt` — Plain text
    - `.json` — JSON syntax highlighting
    - `.yaml`/`.yml` — YAML syntax highlighting
    - `.c`/`.cpp`/`.h` — C/C++ syntax highlighting
    - `.js`/`.jsx` — JavaScript syntax highlighting
  - For each: verify `PreviewPane` renders Prism (not Ace)
  - Verify diff view (`GitDiffPane`) still works correctly
  - Verify SSOT preview (`SsotReviewPane`) still works correctly
  - Document any regressions

  **Must NOT do**:
  - Do NOT modify Prism logic
  - Do NOT break existing non-Verilog previews

  **Recommended Agent Profile**:
  - **Category**: `quick`
    - Reason: Systematic verification of existing functionality
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 11, 13)
  - **Parallel Group**: Wave 4
  - **Blocks**: Task 14 (coexistence test)
  - **Blocked By**: Task 7 (Ace integration)

  **References**:
  - `frontend/atlas/workspace.jsx:3193-3204` — conditional rendering (gitShow, ssot, preview)

  **Acceptance Criteria**:
  - [ ] All non-Verilog file types still use Prism
  - [ ] Markdown preview renders correctly
  - [ ] Git diff view works
  - [ ] SSOT preview works

  **QA Scenarios**:

  ```
  Scenario: Python file uses Prism
    Tool: Playwright
    Preconditions: A .py file exists
    Steps:
      1. Open .py file
      2. Assert: `.ace_editor` NOT in DOM
      3. Assert: `.prism-code` or existing Prism selectors present
    Expected Result: Prism preview for non-Verilog
    Failure Indicators: Ace loaded for .py, Prism broken
    Evidence: .sisyphus/evidence/task-12-coexist-py.png

  Scenario: Markdown file uses DeferredMarkdownPreview
    Tool: Playwright
    Preconditions: A .md file exists
    Steps:
      1. Open .md file
      2. Assert: Markdown renders with HTML (not plain text)
      3. Assert: No Ace Editor present
    Expected Result: Markdown preview unchanged
    Failure Indicators: Raw markdown shown, Ace loaded
    Evidence: .sisyphus/evidence/task-12-coexist-md.png
  ```

  **Evidence to Capture**:
  - [ ] Screenshots for each file type: `.py`, `.md`, `.json`, `.txt`

  **Commit**: NO (verification task, no code changes unless bugs found)

---

- [ ] 13. **Signal tracing + graph integration (click signal → update graph)**

  **What to do**:
  - Wire up: when user selects a signal in Ace Editor (double-click or context menu), BOTH the trace panel AND the Cytoscape graph update simultaneously
  - Ensure `/api/signals` data is shared between `SignalTracePanel` and `SignalGraph` components
  - When signal changes:
    1. Highlight signal name in Ace (optional: add temporary marker)
    2. Update trace panel with new signal's data
    3. Update Cytoscape graph with new nodes/edges
  - Add a "clear selection" button to reset graph and panel
  - Handle edge case: signal has no drivers or no loads — graph shows orphaned node

  **Must NOT do**:
  - Do NOT make graph nodes clickable to jump to code (v2)
  - Do NOT highlight all driver/load lines in Ace (v1.5)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Cross-component state management, event wiring
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 11, 12)
  - **Parallel Group**: Wave 4
  - **Blocks**: —
  - **Blocked By**: Tasks 7, 9, 10

  **References**:
  - `frontend/atlas/workspace.jsx` — component hierarchy for event passing

  **Acceptance Criteria**:
  - [ ] Selecting signal updates both panel and graph
  - [ ] Graph nodes/edges change when different signal selected
  - [ ] Clear selection button works

  **QA Scenarios**:

  ```
  Scenario: Signal selection updates both panel and graph
    Tool: Playwright
    Preconditions: Tasks 7-12 complete, simple_module.sv open
    Steps:
      1. Double-click "clk" in Ace
      2. Assert: trace panel shows "clk" data
      3. Assert: graph shows "clk" node
      4. Double-click "q" in Ace
      5. Assert: trace panel shows "q" data (different from clk)
      6. Assert: graph shows "q" node with different connections
    Expected Result: Both components synchronized with signal selection
    Failure Indicators: Panel updates but graph doesn't, or vice versa
    Evidence: .sisyphus/evidence/task-13-integration.png
  ```

  **Evidence to Capture**:
  - [ ] `task-13-integration.png` — side-by-side panel and graph for selected signal

  **Commit**: YES (Wave 4)
  - Message: `feat(ui): integrate signal tracing panel with Cytoscape graph`
  - Files: `frontend/atlas/workspace.jsx`

---

- [ ] 14. **Playwright E2E: Ace loads for .sv, Prism for .py**

  **What to do**:
  - Create `frontend/atlas/tests/verilog-viewer.spec.js`
  - Test 1: Navigate to Atlas, open `.sv` file → assert `.ace_editor` exists, `.prism-code` does not
  - Test 2: Open `.py` file → assert `.prism-code` exists, `.ace_editor` does not
  - Test 3: Open `.md` file → assert Markdown preview renders (check for HTML elements)
  - Use existing Playwright config (`playwright.config.js`, baseURL `http://127.0.0.1:8765`)
  - Use test fixture files in `test_data/` directory
  - Add setup: ensure Atlas server is running before tests

  **Must NOT do**:
  - Do NOT modify existing Playwright tests
  - Do NOT use hardcoded timeouts without `waitForSelector`

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: E2E test writing, selector strategy, test reliability
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 15-18)
  - **Parallel Group**: Wave 5
  - **Blocks**: —
  - **Blocked By**: Tasks 5, 7, 12

  **References**:
  - `playwright.config.js` — existing config
  - `tests/test_e2e_api.py` — backend test patterns

  **Acceptance Criteria**:
  - [ ] Playwright test passes for .sv → Ace
  - [ ] Playwright test passes for .py → Prism
  - [ ] Playwright test passes for .md → Markdown

  **QA Scenarios**:

  ```
  Scenario: E2E Ace/Prism switch
    Tool: Bash (npx playwright test)
    Preconditions: Atlas server running, test_data/ files exist
    Steps:
      1. Run: cd frontend/atlas && npx playwright test tests/verilog-viewer.spec.js --grep "Ace loads for Verilog"
      2. Assert: test passes
      3. Run: npx playwright test --grep "Prism still works for Python"
      4. Assert: test passes
    Expected Result: All E2E tests pass
    Failure Indicators: Test failures, timeouts
    Evidence: .sisyphus/evidence/task-14-e2e-ace-prism.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-14-e2e-ace-prism.txt` — Playwright test output

  **Commit**: YES (Wave 5)
  - Message: `test(e2e): add Ace/Prism switching tests`
  - Files: `frontend/atlas/tests/verilog-viewer.spec.js`

---

- [ ] 15. **Playwright E2E: Folding widget visible and functional**

  **What to do**:
  - Add to `verilog-viewer.spec.js`:
  - Test: Open `.sv` file with `module`/`endmodule` → assert `.ace_fold-widget` exists in gutter
  - Test: Click fold widget → assert visible lines decrease
  - Test: Click again → assert lines restore
  - Test: Click "Fold All" button → assert all foldable regions collapsed
  - Test: Click "Unfold All" button → assert all regions expanded

  **Must NOT do**:
  - Do NOT test internal Ace API — test DOM behavior only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: E2E interaction testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 14, 16-18)
  - **Parallel Group**: Wave 5
  - **Blocks**: —
  - **Blocked By**: Tasks 5, 7, 8

  **References**:
  - `frontend/atlas/workspace.jsx:9160-9179` — fold buttons location

  **Acceptance Criteria**:
  - [ ] Fold widgets visible for foldable regions
  - [ ] Click toggles fold/unfold
  - [ ] Fold All / Unfold All buttons work

  **QA Scenarios**:

  ```
  Scenario: E2E folding functionality
    Tool: Bash (npx playwright test)
    Preconditions: Task 14 complete
    Steps:
      1. Run: npx playwright test --grep "folding"
      2. Assert: all folding tests pass
    Expected Result: 4/4 folding tests pass
    Failure Indicators: Widget not found, fold doesn't change line count
    Evidence: .sisyphus/evidence/task-15-e2e-folding.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-15-e2e-folding.txt` — Playwright output

  **Commit**: YES (Wave 5)
  - Message: `test(e2e): add code folding tests`
  - Files: `frontend/atlas/tests/verilog-viewer.spec.js`

---

- [ ] 16. **Playwright E2E: Signal tracing panel shows drivers/loads**

  **What to do**:
  - Add to `verilog-viewer.spec.js`:
  - Test: Open `.sv` file, double-click signal → assert `.signal-trace-panel` appears
  - Test: Assert panel contains "Declaration", "Drivers", "Loads" sections
  - Test: Assert driver count matches expected (from test fixture)
  - Test: Click driver → assert Ace cursor jumps to correct line
  - Use test fixture with known signal structure

  **Must NOT do**:
  - Do NOT hardcode line numbers without verifying fixture content

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Complex E2E flow: file open → signal select → panel verify → line jump
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 14-15, 17-18)
  - **Parallel Group**: Wave 5
  - **Blocks**: —
  - **Blocked By**: Tasks 5, 6, 7, 9

  **References**:
  - `frontend/atlas/workspace.jsx` — trace panel selectors

  **Acceptance Criteria**:
  - [ ] Panel appears on signal selection
  - [ ] Panel shows correct sections
  - [ ] Driver click jumps to line

  **QA Scenarios**:

  ```
  Scenario: E2E signal tracing
    Tool: Bash (npx playwright test)
    Preconditions: Task 15 complete
    Steps:
      1. Run: npx playwright test --grep "signal tracing"
      2. Assert: all signal tracing tests pass
    Expected Result: 4/4 signal tracing tests pass
    Failure Indicators: Panel not found, wrong data, jump fails
    Evidence: .sisyphus/evidence/task-16-e2e-tracing.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-16-e2e-tracing.txt` — Playwright output

  **Commit**: YES (Wave 5)
  - Message: `test(e2e): add signal tracing panel tests`
  - Files: `frontend/atlas/tests/verilog-viewer.spec.js`

---

- [ ] 17. **Playwright E2E: Cytoscape graph renders with nodes**

  **What to do**:
  - Add to `verilog-viewer.spec.js`:
  - Test: Open `.sv` file, select signal → assert graph container has canvas
  - Test: Assert Cytoscape instance has nodes (check DOM for `.cy-node` or canvas content)
  - Test: Assert empty state message shown when no signal selected
  - Test: Select different signal → assert graph updates (different node count or structure)

  **Must NOT do**:
  - Do NOT test Cytoscape internal API — test DOM/visual presence only

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Canvas/graph rendering verification in E2E
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 14-16, 18)
  - **Parallel Group**: Wave 5
  - **Blocks**: —
  - **Blocked By**: Tasks 6, 7, 10

  **References**:
  - `frontend/atlas/workspace.jsx` — graph container

  **Acceptance Criteria**:
  - [ ] Graph renders when signal selected
  - [ ] Graph has nodes
  - [ ] Empty state shown when no selection

  **QA Scenarios**:

  ```
  Scenario: E2E graph rendering
    Tool: Bash (npx playwright test)
    Preconditions: Task 16 complete
    Steps:
      1. Run: npx playwright test --grep "graph"
      2. Assert: all graph tests pass
    Expected Result: 3/3 graph tests pass
    Failure Indicators: Canvas empty, no nodes, no empty state
    Evidence: .sisyphus/evidence/task-17-e2e-graph.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-17-e2e-graph.txt` — Playwright output

  **Commit**: YES (Wave 5)
  - Message: `test(e2e): add Cytoscape graph rendering tests`
  - Files: `frontend/atlas/tests/verilog-viewer.spec.js`

---

- [ ] 18. **Playwright E2E: Invalid Verilog → Ace still loads, tracing disabled**

  **What to do**:
  - Add to `verilog-viewer.spec.js`:
  - Test: Open invalid `.sv` file (syntax error) → assert Ace loads with content
  - Test: Assert toast or meta strip shows error message
  - Test: Assert signal tracing panel is disabled/hidden
  - Test: Assert no crash, no infinite spinner
  - Test: Open large file (>5MB) → assert Ace loads, toast shows size warning

  **Must NOT do**:
  - Do NOT make tests dependent on exact toast text (use partial match)

  **Recommended Agent Profile**:
  - **Category**: `unspecified-high`
    - Reason: Error state E2E testing
  - **Skills**: []

  **Parallelization**:
  - **Can Run In Parallel**: YES (with Tasks 14-17)
  - **Parallel Group**: Wave 5
  - **Blocks**: —
  - **Blocked By**: Tasks 5, 7, 11

  **References**:
  - `frontend/atlas/workspace.jsx` — error handling UI

  **Acceptance Criteria**:
  - [ ] Invalid Verilog opens in Ace
  - [ ] Error message visible
  - [ ] Tracing disabled gracefully
  - [ ] Large file handled

  **QA Scenarios**:

  ```
  Scenario: E2E error handling
    Tool: Bash (npx playwright test)
    Preconditions: Task 17 complete
    Steps:
      1. Run: npx playwright test --grep "error"
      2. Assert: all error handling tests pass
    Expected Result: 4/4 error tests pass
    Failure Indicators: Ace doesn't load, crash, missing error message
    Evidence: .sisyphus/evidence/task-18-e2e-error.txt
  ```

  **Evidence to Capture**:
  - [ ] `task-18-e2e-error.txt` — Playwright output

  **Commit**: YES (Wave 5)
  - Message: `test(e2e): add error handling and edge case tests`
  - Files: `frontend/atlas/tests/verilog-viewer.spec.js`

---

## Final Verification Wave

> 4 review agents run in PARALLEL. ALL must APPROVE. Present consolidated results to user and get explicit "okay" before completing.

- [ ] F1. **Plan Compliance Audit** — `oracle`
  Read the plan end-to-end. For each "Must Have": verify implementation exists (read file, curl endpoint, run command). For each "Must NOT Have": search codebase for forbidden patterns — reject with file:line if found. Check evidence files exist in `.sisyphus/evidence/`. Compare deliverables against plan.
  Output: `Must Have [N/N] | Must NOT Have [N/N] | Tasks [N/N] | VERDICT: APPROVE/REJECT`

- [ ] F2. **Code Quality Review** — `unspecified-high`
  Run `tsc --noEmit` + linter + `bun test`. Review all changed files for: `as any`/`@ts-ignore`, empty catches, console.log in prod, commented-out code, unused imports. Check AI slop: excessive comments, over-abstraction, generic names.
  Output: `Build [PASS/FAIL] | Lint [PASS/FAIL] | Tests [N pass/N fail] | Files [N clean/N issues] | VERDICT`

- [ ] F3. **Real Manual QA** — `unspecified-high` (+ `playwright` skill)
  Start from clean state. Execute EVERY QA scenario from EVERY task — follow exact steps, capture evidence. Test cross-task integration. Test edge cases: empty state, invalid input, large file. Save to `.sisyphus/evidence/final-qa/`.
  Output: `Scenarios [N/N pass] | Integration [N/N] | Edge Cases [N tested] | VERDICT`

- [ ] F4. **Scope Fidelity Check** — `deep`
  For each task: read "What to do", read actual diff (git log/diff). Verify 1:1 — everything in spec was built, nothing beyond spec was built. Check "Must NOT do" compliance. Detect cross-task contamination.
  Output: `Tasks [N/N compliant] | Contamination [CLEAN/N issues] | Unaccounted [CLEAN/N files] | VERDICT`

---

## Commit Strategy

- **Wave 1**: `feat(verilog-viewer): add Ace Editor + Cytoscape.js CDN with local fallback`
- **Wave 2**: `feat(api): add /api/ast and /api/signals endpoints`
- **Wave 3**: `feat(ui): integrate Ace Editor, folding, signal tracing, Cytoscape graph`
- **Wave 4**: `feat(ui): add error handling, file size limits, Ace/Prism coexistence`
- **Wave 5**: `test(e2e): add Playwright tests for Verilog viewer`
- **Wave FINAL**: `chore(verify): final verification and quality fixes`

---

## Success Criteria

### Verification Commands
```bash
# Backend API health
curl -s http://127.0.0.1:8765/api/ast -X POST -H "Content-Type: application/json" -d '{"path":"test.sv"}' | jq '.tree'
curl -s http://127.0.0.1:8765/api/signals -X POST -H "Content-Type: application/json" -d '{"path":"test.sv"}' | jq '.signals[0].name'

# Frontend E2E
cd frontend/atlas && npx playwright test tests/verilog-viewer.spec.js

# All existing tests still pass
python -m pytest tests/ -x
```

### Final Checklist
- [ ] All "Must Have" present
- [ ] All "Must NOT Have" absent
- [ ] All Playwright tests pass
- [ ] Existing tests (12/12 Python + 10/10 Playwright) still pass
- [ ] CDN fallback works (simulate offline)
- [ ] pyslang parse error handled gracefully
- [ ] File size limit enforced
