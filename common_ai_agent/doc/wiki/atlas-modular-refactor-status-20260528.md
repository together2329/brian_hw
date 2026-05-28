# Atlas modular refactor — status & verification rig (2026-05-28)

> Living progress note for `refactor/atlas-modular`. Source of truth for
> what's been extracted from `src/atlas_ui.py` + `frontend/atlas/workspace.jsx`
> and how to verify the next phase without booting the server.

## Where the cuts landed

`workspace.jsx` started at **21,415 lines** and is now **15,562 lines**
(**−27.3%**, **5,853 lines** lifted into focused sibling files).

| Phase | Commit | Target file | Lines moved |
|---|---|---|---|
| 1 (a/b) | 5b2477c4 / 735084e8 | `src/atlas_ssot_export.py` | 1,795 |
| 2 (a/b) | 3c9d42ac / b122e8af | `src/atlas_ssot_docx.py` | 1,609 |
| 3 (a/b) | 780975a6 / bd0ae314 | `src/atlas_compactor.py` | 143 |
| 4 (a/b) | f8796646 / ac4ddd85 | `src/atlas_runtime.py` (bootstrap+CLI) | 1,115 |
| 5 (a/b) | a737387c / d846aa64 | `src/atlas_model_options.py` | 213 |
| 6 (a/b) | 855ff47a / ae1394ab | `src/atlas_runtime.py` (`_resolve_workflow_root`) | (folded in) |
| 8/9 | 780d143a / 3e65f21e | `src/atlas_api_files.py` | ~200 |
| 10 (poc–d) | 8b3f22ae … 2450a6fd | `src/atlas_qa.py` | ~430 |
| 11 (a/b) | 569b4ddc / 1e62a6e0 | `src/atlas_api_sim_debug.py` | ~640 |
| 12 (a/b) | 6b554b8c / 90170ca5 | `src/atlas_slash_handlers.py` | 1,953 |
| **13e** | 29caf398 | `frontend/atlas/ui-utils.jsx` | 60 |
| **13a** | 928b20cb | `frontend/atlas/ssot-doc.jsx` (SsotDocPane) | 375 |
| **13b** | 0f7cb6ab | `frontend/atlas/workflow-report.jsx` | 164 |
| **13d** | 282506b7 | `frontend/atlas/preview-pane.jsx` (PreviewPane + FoldablePane + DeferredMarkdownPreview) | 712 |
| **13c** | 2096a836 | `frontend/atlas/ssot-digest.jsx` (DigestCard + BlockDiagram + SsotDigestContent + SsotReviewPane) | 2,123 |
| **13f** | f69b93be | `frontend/atlas/ssot-qa-board.jsx` (SsotQaBoard) | 1,717 |

## Pattern used by every frontend extraction (Phase 13a–f)

Each extracted jsx file is a single IIFE that:

1. **Forward-refs workspace helpers via lambdas** so the lookup defers
   to call time:
   ```js
   const _markdownHtml = (...a) => window._markdownHtml(...a);
   ```
2. **Hosts the component bodies** as ordinary local consts; co-resident
   components in the same file reference each other directly without
   going through `window`.
3. **Registers each public component on `window`** at the bottom of the
   IIFE:
   ```js
   window.PreviewPane = PreviewPane;
   ```

`workspace.jsx` then, at the end of its own load:

1. **Exposes every helper the cluster needs** as a window global
   (`window.X = X;`), placed at end-of-file so the original `const X` is
   already past its TDZ.
2. **Aliases each extracted component back** so existing render sites
   keep working without edits:
   ```js
   const PreviewPane = window.PreviewPane;
   ```

`index.html` loads each cluster jsx **before** `workspace.jsx`. The IIFE
wrapper is what prevents top-level `const` collisions across the shared
`<script>` global scope.

## Verification rig — `scripts/atlas_jsx_integration_test.js`

Pure Node — no server, no browser, no React install needed.

```bash
node scripts/atlas_jsx_integration_test.js .
```

What it does:

- Builds a `vm.Context` stocked with a React stub (`useState`,
  `useEffect`, `useCallback`, `useMemo`, `useRef`, `memo`, `forwardRef`,
  …), a DOM stub (`document`, `Element`, `IntersectionObserver`, …),
  and the usual browser globals (`fetch`, `localStorage`,
  `crypto.randomUUID`, …).
- Transforms each jsx through the bundled `frontend/atlas/vendor/babel.min.js`
  in the **exact load order** from `index.html`
  (`shared.jsx` → `ui-utils.jsx` → `preview-pane.jsx` →
  `ssot-digest.jsx` → `ssot-qa-board.jsx` → `workspace.jsx`).
- Checks every entry of `expected` (currently 55 entries: 8 extracted
  components + 47 sampled deps) lands on `window`.
- Smoke-tests forward-refs by calling helpers through `window` and
  verifying real output (e.g. `atlasFormatBytes(1536) → "1.5 KB"`,
  `_escHtml('<b>x</b>') → "&lt;b&gt;x&lt;/b&gt;"`).

Bugs the rig has caught that pure `babel.transform` syntax check
missed:

- **TDZ violations** — an expose-block reading `const X` before that
  line was reached (Phase 13d).
- **Top-level `const` collisions** between a freshly-extracted jsx and
  workspace.jsx in the shared `<script>` scope — fixed by wrapping
  every extracted file in an IIFE (Phase 13d).
- **Missing React stub APIs** (e.g. `React.memo`) that would only show
  up later in a stale rig.

## Adding a new extraction phase

1. Pick a component in `workspace.jsx` (the largest remaining ones are
   `Workspace` (5,316 lines, **don't extract** — too central / too hot),
   `AgentStatusPanel` (614), `ProgressPanel` (462), `TodoPanel` (427)).
2. Scan its external workspace-scope deps:
   ```python
   # See doc body of 282506b7 / 2096a836 commit messages for the
   # exact python scout snippet — diff workspace.jsx top-level defs
   # against identifiers referenced inside the component body.
   ```
3. Write the new jsx file with the IIFE + lambda forward-ref +
   `window.X = X` pattern.
4. Delete the component bodies from `workspace.jsx`; append the
   `window.X = X` expose-block + `const X = window.X` aliases at
   end-of-file.
5. Add the `<script src="…?v=…">` tag to `index.html` **before**
   `workspace.jsx`.
6. Update `scripts/atlas_jsx_integration_test.js`:
   - Append the new file to the `files` array.
   - Append the new component name + any newly-exposed deps you want
     spot-checked to the `expected` list.
7. Run `node scripts/atlas_jsx_integration_test.js .` — every entry
   should land as `function`, exit 0.
8. Run the targeted python sweep — many source-grep tests cluster
   around `tests/test_atlas_ssot_*.py`, `tests/test_atlas_pipeline_*.py`,
   and `tests/test_atlas_file_*.py`. Update any failing test to use
   the `_all_workspace_jsx()` helper (in `test_atlas_ssot_qa_workbench.py`)
   or define an equivalent combined source.
9. Commit only your own files (the auto-commit harness writes `todo[N]`
   commits separately — never sweep its work into yours).
