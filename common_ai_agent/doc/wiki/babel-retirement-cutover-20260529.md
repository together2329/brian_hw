# Babel / legacy-JSX Retirement — cutover progress + plan (2026-05-29)

**STATUS: PAUSED** — stopped mid-Round-1 due to a working-tree conflict with
parallel edits from another process (session-machine.ts / session-protocol.ts /
tsconfig.json / workspace.jsx / .config / mctp_assembler/ are NOT part of this
effort). Resume only after the working tree is reconciled.

Goal: retire in-browser Babel + legacy `.jsx` now that the `.jsx→.tsx` migration
is done and the Vite build exists. Related: [[frontend-modernization-2026-05-29]]
· [[tech-direction-recommendation-20260529]].

## The original 3-step idea (and why it grew)

1. Flip `ATLAS_FRONTEND_MODE` default legacy→vite.
2. Delete 36 `.jsx` + `babel.min.js` + `text/babel` tags.
3. → first-load babel cost gone + npm libraries open.

Scoping proved step 2 is **not** a blind delete. The single-entry Vite bundle
(`main.tsx`) covers **only the `/` route**. `/lobby`, `/preview`, `/admin` still
run on babel+jsx, and ~18 tests read `.jsx` source. So full retirement is a
multi-stage project, not a 2-line change.

## DONE + verified

### Step 1 — default flip (COMPLETE, verified)
- `src/atlas_ui.py` `/` route: `os.environ.get("ATLAS_FRONTEND_MODE", "legacy")`
  → default **`"vite"`** (legacy still selectable via the env var; falls through
  to legacy `index.html` if `dist` is missing — safety net retained).
- Verified in-process (FastAPI TestClient, env unset): `GET /` = 200, serves
  `/assets/index.vite-*.js` bundle, **zero `text/babel`**; `ATLAS_FRONTEND_MODE=legacy`
  still serves the babel path. No `.env`/`.config` override exists, so the code
  default is effective.
- Net: the main app `/` no longer does in-browser Babel — **the main user-facing
  load-cost win is already banked.** Remaining work is mostly hygiene.

### Pre-flight verification (5-agent workflow) — result
- build / entry-parity / backend-serving / runtime-smoke = **PASS** (vite build
  clean, 138 modules, JS 1.04MB/gzip 297KB; `tsc` 0 errors; vitest 68/68;
  `lib/*.js` window-globals are bundled in; assets mount matches dist paths).
- adversarial = **FAIL on the DELETION half only** → see blockers below.

### Scoping (4-agent workflow) — key facts
- All 36 `.jsx` have a `.tsx` twin. `workspace.jsx` is re-split across ~40
  `workspace-*.tsx` (NOT 1:1) → tests must read a **glob-union** of `*.tsx`.
- Python tests: ~40–50% of asserted substrings need **rewrites** (`React.useX(`→`useX(`,
  typed params, `window.X`→`(window as any).X`/`w.X`, `new Map()`→`new Map<`); a
  few asserts are genuinely obsolete. **Baseline is already 2-red** even against
  `.jsx` (`test_atlas_pipeline_contract` regex; `test_atlas_scm_ui_override`
  runtime `data-filename`).
- `dist/` is **git-ignored** → fresh checkout has no build → today relies on the
  legacy fallback. Hard prerequisite before deleting legacy.
- `/admin` is already babel-free (`admin.bundle.js`, esbuilt from `admin.jsx`).

## Decisions taken (2026-05-29)

| # | Decision | Chosen |
|---|---|---|
| preview.html | dead dev harness (no route, 0 refs) | **DELETE** (+ static-shim.js) |
| legacy escape hatch | `ATLAS_FRONTEND_MODE=legacy` + index.html + babel fallback | **REMOVE fully**; replace `/` fallback with a "run `npm run build`" 500 page |
| dist build delivery | currently git-ignored | **add `npm run build` to deploy/run flow** (not commit dist) |
| admin.jsx | admin already babel-free | **KEEP** admin.jsx (defer bundle rebuild); ∴ keep `vendor/react*.development.js` |

## Execution plan (resume from here)

**Round 1 — parallel, disjoint files** *(was interrupted; partial — see state below)*
- js-tests: repoint 5 test `.jsx`→`.tsx` reads/imports → vitest stays green.
- lobby-vite-frontend: `lobby-entry.tsx` + `lobby.vite.html` + `vite.config.ts`
  multi-entry `rollupOptions.input = {index, lobby}` → build emits both.
- py-tests: retarget 10 test files (glob-union reads + assertion rewrites; defer
  the 2 runtime-serving methods to Round 2). **Faithful rewrites — do not gut asserts.**
- delete-dead: `git rm lobby-test.html` + `pipeline.jsx.pre-enhancement-swap-20260518.bak`.

**Round 2 — sequential, `src/atlas_ui.py` only** (single owner; avoids the conflict)
- Add `_vite_lobby_html()` (mirror `_vite_index_html`), repoint `GET /lobby` to the
  built `dist/lobby.vite.html` (no legacy fallback).
- Remove the `/` legacy branch + `ATLAS_FRONTEND_MODE` read; replace fallback with
  the 500 "build missing" page. Retire `_inline_html_cached` / `_inject_scm_ui_override`
  legacy machinery (shared with /lobby until lobby is on vite). Leave the admin inliners.
- Reconcile the 2 runtime tests (`scm_ui_override` data-filename, `user_dashboard`
  served filename) to vite-mode serving.
- Add `npm run build` to `scripts/run_atlas_desktop.sh` / server start.

**Round 3 — build + deletion**
- `npm run build` (multi-entry) → confirm `dist/index.vite.html` + `dist/lobby.vite.html`.
- `git rm` 35 `.jsx` (ALL except `admin.jsx`) + `vendor/babel.min.js` + `index.html`
  + `lobby.html` + `preview.html` + `static-shim.js`.
- KEEP: `admin.jsx`, `admin.bundle.js`, `vendor/react*.development.js`,
  `vendor/{marked,mermaid,purify,prism}*`.

**Round 4 — final verification**
- `npm run build` ok; full `pytest` green; full `vitest` green.
- Server smoke: `GET /`, `/lobby`, `/admin` = 200 & no `text/babel`; `/preview` = 404;
  fallback smoke (move `dist` aside → 500 "run build" page).
- `grep` no dangling `text/babel` / `babel.min.js` / deleted-`.jsx` refs (admin excepted).

## Current working-tree state (as of pause — NOT reverted)

Mine (this effort):
- `src/atlas_ui.py` — Step 1 flip (DONE, verified).
- `.gitignore`, `rtl/rtl_compile.log` (D) — earlier cleanup task (separate).
- `doc/wiki/tech-direction-recommendation-20260529.md` (untracked), `doc/wiki/index.md`.

Round 1 partial (interrupted):
- **js-tests: DONE (5/5)** — debug-tool-card, ip-roster-source, sim-debug-vcd-scope-annotation,
  terminal-transcript-renderer, wave-edge-click.
- **lobby-vite-frontend: DONE** — `lobby-entry.tsx`, `lobby.vite.html` (untracked), `vite.config.ts` (M).
- **delete-dead: DONE** — `lobby-test.html` (D), `pipeline.jsx.pre-enhancement-swap-20260518.bak` (D).
- **py-tests: PARTIAL (3/10)** — DONE: `test_atlas_qa_history_scope.py`,
  `test_atlas_ssot_doc_tab.py`, `test_atlas_todo_tab.py`. **NOT DONE (7):**
  `test_atlas_ssot_qa_workbench.py`, `test_atlas_frontend_session_filters.py`,
  `test_atlas_file_preview_imports.py`, `test_atlas_pipeline_flow_theme.py`,
  `test_atlas_pipeline_contract.py`, `test_atlas_scm_ui_override.py`,
  `test_recent_changes.py`. ⚠️ **Test suite is mid-retarget / inconsistent** —
  do not treat as green until the remaining 7 land.

⚠️ NOT this effort (parallel work present in tree — source of the conflict):
`session-machine.ts`, `session-protocol.ts`, `__tests__/session-machine.test.ts`,
`tsconfig.json`, `workspace.jsx` (M, staged), `.config`, `mctp_assembler/` (untracked).

## Resume checklist
1. Reconcile / land the parallel work first (the `.config`/`session-*`/`workspace.jsx`/`mctp_assembler` changes).
2. Decide: keep the partial Round-1 edits or `git checkout` them and rerun Round 1 clean.
3. If keeping: finish py-tests (the 7 above) → run the targeted pytest green → Round 2 → 3 → 4.
4. Use single-owner sequencing for `src/atlas_ui.py` and `vite.config.ts` to avoid re-conflict.
