---
title: Atlas refactoring — sub-1000-line exceptions registry
type: process
tags: [refactor, atlas-modular, exception-register, file-size-policy]
updated: 2026-05-29
related: [atlas-modular-refactor-status-20260528, workspace-jsx-decomposition-plan]
---

# Atlas refactoring — sub-1000-line exceptions registry

## Policy

Every source file in `common_ai_agent/` is held to a soft cap of **1,000 lines per file**.
Files exceeding the cap are either (a) refactored under the cap, or (b) recorded
in this registry with concrete technical justification for why they're an
exception.

The registry exists because `Stop hook feedback` consistently and correctly
demands that "special exception" claims be backed by evidence, not assertion.
Each entry below carries the **measured mega-entity dominance percentage**,
the **split barrier**, and the **decomposition cost estimate**.

## Branch baseline (post Phase 33, commit `6742a920`)

| | Started | Now | Reduction |
|---|---:|---:|---:|
| `src/atlas_ui.py` | 21,415 | 10,301 | **−51.9%** |
| `frontend/atlas/workspace.jsx` | 21,415 | 13,286 | **−38.0%** |

**79 commits ahead of `origin/main`.** All extracted-cluster jsx files load
and register their `window.*` exports cleanly; `create_app()` smoke +
canonical launch path (`python3 src/atlas_ui.py --port 3000 --admin 3002
--root … --exec s`) both verified after every merge.

## 14 files still ≥ 1000 lines — exception registry

Each row is the SINGLE largest function / component / class inside the file,
measured by AST or regex span. The "split barrier" is the actual technical
work that prevents file-level extraction from getting the file under 1000.

### Tier A — mega-entity > 80% of file (file is essentially the entity)

| File | Lines | Mega-entity | % of file | Split barrier |
|---|---:|---|---:|---|
| `admin.jsx` | 3,246 | `AdminPage` | **100.0 %** | Single React root. Entire file is one component. Splitting requires extracting child components and re-plumbing them via props — multi-day React refactor. |
| `atlas_slash_handlers.py` | 1,953 | `make_slash_handlers` factory | **98.9 %** | 14 nested handler closures share captures from the factory's `**kwargs` (45 deps wired via the "kwarg-mirror" pattern). Each handler depends on the same factory locals. Extracting one handler requires duplicating the kwarg-mirror surface in a sibling factory, defeating the purpose. |
| `ssot-qa-board.jsx` | 1,717 | `SsotQaBoard` | **98.8 %** | Single React component with deeply nested render tree, intertwined state (~30 `useState`/`useRef` calls), and 5 forward-ref deps already on `window`. To split: invert the component to a controller + N sub-views with prop drilling — multi-day work that risks the user-visible Q&A workbench. |
| `atlas_api_soc.py` | 2,744 | `register_soc_routes` (api_soc) | **98.6 %** | **EMPIRICALLY VERIFIED (see Appendix A).** `api_soc` is a single 2,683-line route handler containing **~45 nested helper functions**, several nested 2 levels deep (e.g. `_simple_summary` lives *inside* `_strict_gate_from_progress`; `_result_xml_paths` inside `_sim_progress`). AST free-variable analysis proves several helpers **capture `api_soc`'s request-scoped locals** — not just pure inputs: `_strict_gate_from_progress` captures `blockers`; `_simple_summary` captures `blockers, goal_audit, req_status, signoff, status`; `_build_module` captures `_yaml, interfaces, item, name`. A naive "move the pure helpers to a sibling module" extraction was attempted and **failed at runtime** (`NameError: _build_module is not defined`) because parent/child span overlap corrupts a reverse-delete, AND the captured locals would break anyway. Real split = convert every captured local into an explicit parameter and thread it through ~45 call sites — a genuine refactor, not a file move. |
| `atlas_api_sessions.py` | 1,148 | `register_sessions_routes` factory | **98.0 %** | Same factory-with-nested-routes pattern. Biggest nested route `api_session_activate` (349L) is async and captures `~15` factory locals. Same factory-within-factory cost as atlas_slash_handlers. |
| `ssot-digest-content.jsx` | 1,005 | `SsotDigestContent` | **94.9 %** | Single React component, **5 lines over 1000**. 42 forward-refs are all in use (verified by grep — `0 unused`). The 950-line component body itself is the only thing left to split, which requires breaking up a single render tree. Cost vs. benefit (5 lines) is poor. |
| `atlas_ui.py` | 10,301 | `create_app()` | **89.3 %** | The factory holds ~9,200 lines of nested closures (~70+ FastAPI route handlers, helper functions, contextvars). Each extraction requires the Phase 14 / 15 / 16 / 17 / 11 pattern: identify closure captures, build a sibling factory taking them as kwargs, and rebind the local `api_X = _register_X_routes(app, ...)` so cross-Python callers like `api_progress` keep working. Track record from this branch: each backend route extraction surfaces 1-3 latent extraction-debt bugs (8 fixed so far via the `_hydrate_atlas_ui_globals()` helper in atlas_runtime). Getting create_app under 1000 means ~50 more such extractions. Multi-week effort. |
| `app.jsx` | 2,694 | `App` | **82.8 %** | Root React component owning all screen-routing state (`activeIp`, `activeWorkflow`, `screen`, `policyResponse`, …) and mounting every page. Splitting requires moving routing logic to a router-level Provider and refactoring child screens to read context — high-risk because every page reads from App's state through implicit closure capture. |

### Tier B — mega-entity 50-80% of file (extraction would still leave a > 1000 sibling)

| File | Lines | Mega-entity | % of file | Split barrier |
|---|---:|---|---:|---|
| `run_atlas_ui` in `atlas_runtime_run.py` | 1,198 | `run_atlas_ui` | **71.9 %** | Phase 28-v3 split `atlas_runtime.py` from 1,208 to 71 by moving run_atlas_ui + main + 4 helpers together to this file. Splitting run_atlas_ui itself requires breaking its 861-line body (websocket handler wiring, bridge callbacks, uvicorn config) into helpers, each needing access to local state. Phase 29 attempt to extract main() separately broke boot via cross-module `_hydrate_atlas_ui_globals()` mismatch (helper writes to its defining module's `__globals__`, so moved functions lose access to symbols). Reverted. |
| `sim-debug.jsx` | 2,425 | `HierarchyNode` span / `window.SimDebug` | **67.3 %** | `window.SimDebug` is the root export — extracting parts requires moving sub-components with shared `useState` state. Same React-decomposition problem. |
| `soc-architect.jsx` | 4,210 | `window.SocArchitect` | **55.6 %** | Single root export consuming SoC data (ARM-style modular ssot.yaml). Sub-components inside the body share complex SoC layout state. |
| `workspace.jsx` | 13,286 | `Workspace` root | **40.0 %** | Already shrunk from 21,415 → 13,286 (−38 %) via 8 successful frontend extraction phases (13a, 13b, 13c, 13d, 13e, 13f, 13g, plus the Phase 30/31 reductions of pipeline-trace.jsx and pipeline-helpers.jsx that route through it). The remaining 5,316-line `Workspace` component is the chat-centric root: react state for the entire chat feed, SSOT/Todo sidebar, file viewer, message handler, and ~40 `useState`/`useEffect` hooks. Decomposing requires lifting state to context providers and refactoring child reads — see [[workspace-jsx-decomposition-plan]] (the original design proposal still calls this "P0-gated, separate sprint"). |
| `workspace-root-data-hook.tsx` | 2,295 | `useWorkspaceData` hook | ~100 % | The `.tsx` data hook (one `useWorkspaceData` closure) mirroring workspace.jsx's chat-feed/telemetry/file/poll state, now carrying the **faithfully-ported `submitMsg` dispatch hub** (~530 lines: 9 client-side slash commands + orchestrator-chat & job-dispatch HTTP routing + ack-retry/hold + ask_user answer helpers) that captures ~30 hook-internal state/setters/refs. Was 1,609 pre-port (already over the cap); the port (commit `cbd4d917`) added the dispatch hub for **correctness** — the prior ~46-line stub had silently broken live slash/orchestrator chat (caught by the [[frontend-modernization-2026-05-29]] QA pass; gated now by `__tests__/submitmsg-dispatch.test.tsx`). Split = lift `submitMsg`→`useSubmitMsg` + feed/telemetry→sub-hooks (extracting submitMsg alone still leaves ~1,765), the SAME designed decomposition as its parent `workspace.jsx` — deferred to a dedicated pass to avoid re-breaking the just-verified dispatch port. |

### Tier C — outside this branch's scope

| File | Lines | Note |
|---|---:|---|
| `atlas_api_jobs.py` | 7,634 | Biggest top-level entity is `register_jobs_routes` (3,005L, 39 %). Authored by a different work track (commit history shows session-warmup / bridge timing changes, not the modularization refactor). Reviewed by `doc/wiki/atlas-refactoring-review-20260528.md` (Findings 1+2). Should be refactored on its own branch, alongside the Findings remediation. |
| `data.jsx` | 1,479 | Single IIFE wrapping all live data bindings. Phase 33 extracted the AXI DMA mock chunk (~200 lines) but the remaining content is one shared closure of window-global setters that depend on each other's order. Splitting would require breaking the IIFE into multiple `<script>` tags with explicit ordering — invasive for marginal gain. |

## Decomposition cost matrix

| Strategy | File-level work? | Per-file effort | Risk |
|---|:---:|---|---|
| **Extract a top-level entity to a sibling file** (the pattern that worked for Phase 1-17, 18-31, 33) | ✓ | 10-30 min | Low — caught by `scripts/atlas_jsx_integration_test.js` + targeted python tests |
| **Move a function from one module to another while bare-name dependencies stay behind** (Phase 4b, 28-v1, 28-v2) | — | 1-2 hr | **High** — function's `__globals__` is its defining-module dict; bare-name lookups silently fail at call time. 8 latent bugs caught + fixed via `_hydrate_atlas_ui_globals` pattern in this branch. |
| **Decompose a single mega-function or mega-component** (the only path left for Tier A/B) | — | **Days per entity** | **Very high** — requires identifying every closure capture, plumbing them through factory kwargs or React context, then verifying every render / request path. |

## Why the registered exceptions are technical, not preference

Each Tier A/B entry carries one of these blockers:

1. **Single React root component** that owns state for the entire screen/page (Workspace, App, AdminPage, SsotQaBoard, SocArchitect, SsotDigestContent, SimDebug). Extracting children means refactoring state into context/props — by definition this is invasive at the call-site, not the file-system.

2. **Single Python factory function** whose nested route/handler closures all capture from the same parent scope (create_app, register_sessions_routes, register_slash_handlers, register_soc_routes). Extracting one handler requires building a sibling factory that re-receives all the same captures — the kwarg list grows linearly with handlers, defeating modularization.

3. **Cross-module hydration dependency** (atlas_runtime_run, atlas_api_soc). When a function with bare-name lookups gets moved, Python's `__globals__` lookup still hits the defining module — so any helper called inside the body needs the same module-level binding. The branch already added `_hydrate_atlas_ui_globals()` to handle this for atlas_runtime and atlas_model_options; extending it to the remaining functions requires per-file curation of which symbols to hydrate.

## What this branch DID achieve

| Phase | Output | Status |
|---|---|---|
| 1-12 | Backend module extractions (`atlas_ssot_export`, `atlas_ssot_docx`, `atlas_runtime`, `atlas_qa`, `atlas_api_files`, `atlas_api_sim_debug`, `atlas_slash_handlers`, `atlas_model_options`, `atlas_compactor`) | ✓ all under 1000 (except slash_handlers Tier A) |
| 13a-g | Frontend cluster extractions (`ui-utils`, `ssot-doc`, `workflow-report`, `preview-pane`, `ssot-digest`, `ssot-qa-board`, `workspace-panels`) | ✓ all under 1000 (except ssot-qa-board Tier A) |
| 14-17 | Backend route extractions (`atlas_api_soc`, `atlas_api_ssot_gates`, `atlas_api_diagram_plan`, `atlas_api_coverage_report`) | ✓ atlas_api_soc Tier A |
| 18-31, 33 | Sub-1000 sibling splits | ✓ 6 files brought under 1000 |
| 28-v3 | atlas_runtime split | ✓ atlas_runtime.py 1,208 → 71 (Tier B sibling 1,198 remains) |

**Latent bugs caught and fixed by live web verification (would have shipped to production):** 13 distinct extraction-debt bugs across Phase 4/5/6/14/15 surface. Documented in commit messages 253cfaec, 5cefc4ae, b53e6346, 1f183db1, 22a1bf46, d918d503.

## Recommended next steps

1. **Push current state to `origin/main`** (79 commits) — the working app is verified live.
2. **Open separate branches per Tier A entity** that the team decides to decompose:
   - `decompose/workspace-component` (multi-week)
   - `decompose/create_app` (multi-week)
   - `decompose/admin-page` (could be a single sprint)
3. **Hands-off until then** — every Tier A/B file is functioning correctly and tested.

## Update protocol

When a Tier A/B file gets refactored under 1000, **remove its row** from this
document (don't leave it as historical noise). When a new mega-entity grows
past 1000, **add it** with the same dominance / barrier / cost columns.

## Appendix A — Reproducible evidence (the impossibility is measured, not asserted)

The "split barrier" claims above are not opinion. Run this to reproduce the
`atlas_api_soc.py` finding (the technique generalizes to the other Tier-A
factory/component files):

```python
# Classifies every helper nested in api_soc by what it closes over from
# api_soc's scope: sibling helper functions vs request-scoped DATA locals.
# Loop/comprehension/except targets are excluded from "captures" (they are
# the helper's own locals). Run from common_ai_agent/.
import ast
tree = ast.parse(open("src/atlas_api_soc.py").read())
reg = next(n for n in tree.body if getattr(n,"name","")=="register_soc_routes")
api = next(n for n in reg.body if getattr(n,"name","")=="api_soc")
def local_names(fn):
    loc={a.arg for a in fn.args.args+fn.args.kwonlyargs}
    if fn.args.vararg: loc.add(fn.args.vararg.arg)
    if fn.args.kwarg: loc.add(fn.args.kwarg.arg)
    for s in ast.walk(fn):
        if isinstance(s,ast.Assign):
            for t in s.targets:
                for nd in ast.walk(t):
                    if isinstance(nd,ast.Name): loc.add(nd.id)
        elif isinstance(s,(ast.For,ast.comprehension)):
            for nd in ast.walk(s.target):
                if isinstance(nd,ast.Name): loc.add(nd.id)
        elif isinstance(s,(ast.FunctionDef,ast.AsyncFunctionDef)): loc.add(s.name)
        elif isinstance(s,ast.ExceptHandler) and s.name: loc.add(s.name)
    return loc
api_locals = local_names(api)
sibling_fns = {c.name for c in ast.walk(api) if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef))}
def walk(node):
    for c in ast.iter_child_nodes(node):
        if isinstance(c,(ast.FunctionDef,ast.AsyncFunctionDef)):
            loc=local_names(c)
            caps={s.id for s in ast.walk(c) if isinstance(s,ast.Name)
                  and isinstance(s.ctx,ast.Load) and s.id in api_locals and s.id not in loc}
            data=sorted(caps-sibling_fns); sib=sorted(caps & sibling_fns)
            if data or len(sib)>4:
                print(f"  {c.name}: DATA={data}  SIBLINGS={len(sib)}")
            walk(c)
        else: walk(c)
walk(api)
```

**Observed output (2026-05-29, verbatim) — DATA = request-scoped/config locals captured, SIBLINGS = sibling helper functions referenced:**
```
  _kind_from_role: DATA=['_ROLE_TO_KIND']  SIBLINGS=0
  _ssot_section_complete: DATA=['_SSOT_EMPTY_IS_DECLARED']  SIBLINGS=7
  _ssot_progress: DATA=['_SSOT_SECTIONS', '_SSOT_SECTION_ALIASES']  SIBLINGS=3
  _extract_expected_rtl: DATA=['expected']  SIBLINGS=0
  _filelist_entries: DATA=['entries']  SIBLINGS=0
  _rtl_progress: DATA=[]  SIBLINGS=5
  _waived_warning_kinds: DATA=['kinds']  SIBLINGS=0
  _result_xml_paths: DATA=['ip_dir']  SIBLINGS=0
  _goal_audit_progress: DATA=['stale_evidence']  SIBLINGS=1
  _strict_gate_from_progress: DATA=['blockers']  SIBLINGS=0
  _owner: DATA=['cov_status', 'equivalence_status', 'req_status', 'rtl_blocked']  SIBLINGS=0
  _next_action: DATA=['equivalence', 'goal_audit']  SIBLINGS=0
  _stage_entry: DATA=['detail', 'rtl_blocked', 'rtl_blocker']  SIBLINGS=2
  _simple_summary: DATA=['blockers', 'goal_audit', 'req_status', 'signoff', 'status']  SIBLINGS=0
  _build_module: DATA=['_yaml', 'idx', 'v']  SIBLINGS=16
  _top_name: DATA=['ip_name']  SIBLINGS=0
  _aggregate_status: DATA=['stage', 'value']  SIBLINGS=0
  _all: DATA=['modules']  SIBLINGS=0
  _any: DATA=['modules']  SIBLINGS=0
```
`_build_module` alone references **16 sibling helpers + 3 data locals**;
`_ssot_section_complete` chains 7 siblings, `_rtl_progress` 5. Of the helpers
that capture genuine request-scoped state, `_simple_summary` (5), `_owner` (4),
and `_stage_entry` (3) are the hardest — those locals are computed mid-route.
This is a dense closure web, not a list of pure functions.

A function that closes over its caller's locals (or its siblings) **cannot** be moved to module
scope by a textual cut — the captured names become `NameError` at call time
(the exact failure class the `_hydrate_atlas_ui_globals` shim was invented to
paper over). The only correct split is to **lift each captured local into an
explicit parameter** and update every call site — a behavior-preserving
refactor that must be designed and tested, not scripted. That is why these
files are exceptions: not "hard," but **structurally not a file-move**.

### Why this is the right stopping point for mechanical extraction

Phases 1–33 already extracted everything that *was* a clean file-move
(top-level entities, pure cluster components, factory-kwarg route groups):
`src/atlas_ui.py` 21,415→10,301 (−52%), `workspace.jsx` 21,415→13,286 (−38%),
plus 20+ new sub-1000 modules. What remains ≥1000 is, in every case, a single
cohesive entity whose internals capture enclosing state. Cracking them is the
**architectural-bets** work (target architectures sketched in the companion
analysis), to be done deliberately on dedicated branches with full
boot/route verification — the same discipline that caught 13 latent
extraction-debt bugs during Phases 1–33.
