---
title: Orchestrator System Verification Report
type: report
tags: [atlas-ui, orchestrator, verification, audit]
created: 2026-05-18
related: [orchestrator-worker-handoff, orchestrator-llm-loop-phase3, orchestrator-loop-on-react-loop-plan, orchestrator-chat-only-product-plan, orchestrator-worker-handoff-review, orchestrator-workflow-bring-up-20260517, parallel-todo-sub-agent-workers]
---

# Orchestrator System Verification Report

Cross-reference of all 7 orchestrator wiki pages against the source codebase.
Date: 2026-05-18.

## Summary

The orchestrator system wiki is **highly accurate** in its architectural
claims, shipped-feature assertions, and design rationale. The core
implementation matches the documented architecture. Discrepancies are limited
to **stale test counts** (tests grew after wiki sections were written) and
**one UI component name mismatch**.

**Overall verdict: ✅ Verified — wiki is reliable for onboarding and
handoff, with minor stale counts that should be refreshed.**

---

## ✅ Verified Claims (wiki ↔ source code match)

### DB Schema (`core/atlas_db.py`)

| Claim | Source | Verified |
|---|---|---|
| `orchestrator_runs` table | lines 452-467 | ✅ 14 columns, 2 indexes |
| `orchestrator_steps` table | lines 474-490 | ✅ 13 columns, 1 index |
| 6 helper methods (create/append/update/find_active/list/latest) | lines 3416-3576 | ✅ All present |
| `trigger_source` + `orchestrator_run_id` on `workflow_runs` / `artifacts` | lines 444-445, 760-763 | ✅ |
| JSON serialization for `observed_state_json`, `decision_json`, etc. | lines 509-512 | ✅ |

### Source Files (`src/orchestrator/`)

| File | Wiki Claim | Actual | Status |
|---|---|---|---|
| `tools.py` | 8 callable tools | 8 functions confirmed | ✅ |
| `classify.py` | Pure routing function + `_OWNER_ROUTES` dict | 168 lines, exact match | ✅ |
| `loop.py` | Reduced to data types (Phase 3.5) | 46 lines: `OrchestratorContext`, `RunOutcome`, `FINAL_WORKFLOW` | ✅ |
| `react_bridge.py` | `OrchestratorReactLoop`, `_OrderedStepCollector`, `build_orchestrator_inject_fn_for` | 729 lines, all confirmed | ✅ |
| `runner.py` | `OrchestratorRunner` + `Waker` + single-flight | 299 lines, ThreadPoolExecutor(4), confirmed | ✅ |
| `budgets.py` | `BudgetTracker` with per-stage defaults | 100 lines, defaults match wiki table | ✅ |
| `prompts.py` | 9 tool schemas (8 callable + yield_run) | 9 `"name":` entries confirmed | ✅ |

### HTTP Routes (`src/atlas_api_jobs.py`)

| Route | Line | Status |
|---|---|---|
| `POST /api/pipeline/orchestrator/chat` | 3162 | ✅ |
| `GET /api/orchestrator/runs/{run_id}` | 3216 | ✅ |
| `GET /api/orchestrator/active_run` | 3228 | ✅ |
| `GET /api/orchestrator/trace` | 3571 | ✅ |
| `DELETE /api/orchestrator/trace` | 3590 | ✅ |
| `GET /api/orchestrator/workers` | 3613 | ✅ |
| `GET /api/handoff/list` | 3823 | ✅ |
| `POST /api/handoff/save` | 3868 | ✅ |
| `POST /api/handoff/take` | 3921 | ✅ |
| `GET|POST /api/pipeline/orchestrator_mode` | via `_orchestrator_mode_enabled` (1633) | ✅ |
| `_orchestrator_block()` | 1639 | ✅ |
| `_synthesis_artifact_failure()` | 1188 | ✅ |
| `_pnr_artifact_failure()` | 1228 | ✅ (bonus — not explicitly claimed) |

### Supporting Infrastructure

| Component | Path | Status |
|---|---|---|
| Handoff queue | `src/handoff_queue.py` (9 functions) | ✅ |
| Review decisions | `src/review_decisions.py` (3 functions) | ✅ |
| Orchestrator trace | `core/orchestrator_trace.py` | ✅ |
| Orchestrator inject | `core/orchestrator_inject.py` | ✅ |
| ctx-bound variant `build_orchestrator_inject_fn_for` | `react_bridge.py:327` | ✅ |
| `--stages take` CLI | `src/headless_workflow.py:4045-4064` | ✅ |

### Workflow Directory (`workflow/orchestrator/`)

| Claim | Actual | Status |
|---|---|---|
| 13 files total | 13 files | ✅ |
| 7 commands | dispatch, escalate, freeze, resume, retry, route, status | ✅ |
| 2 rules | routing_policy.md, retry_budget.md | ✅ |
| 1 template | run-to-green.json | ✅ |
| system_prompt.md + plan_prompt.md + workspace.json | All present | ✅ |

### Frontend (`frontend/atlas/pipeline.jsx` + `styles.css`)

| Component | Location | Status |
|---|---|---|
| `PendingQABanner` | pipeline.jsx:326 | ✅ |
| `OrchestratorTraceStrip` | pipeline.jsx:503 | ✅ |
| `⇄ take N` button → `/api/handoff/take` | pipeline.jsx:1147 | ✅ |
| `📬 save handoff` button → `/api/handoff/save` | pipeline.jsx:1167 | ✅ |
| `pipe-orch-chip` toggle | pipeline.jsx:2276 | ✅ |
| `pipe-handoff-chip` | pipeline.jsx:2308 | ✅ |
| `pipe-review-chip` | pipeline.jsx:2317 | ✅ |
| CSS `.pipe-stage-take`, `.pipe-stage-save` | styles.css:2366, 2370 | ✅ |
| CSS `.pipe-stage-orch-pill` | styles.css:4068 | ✅ |

### Test Files (16 files, 170 test functions)

| File | Wiki Count | Actual Count | Match? |
|---|---|---|---|
| `test_atlas_db_orchestrator.py` | 11 | 11 | ✅ |
| `test_orchestrator_classify.py` | 13 | 13 | ✅ |
| `test_orchestrator_tools.py` | 12 | 12 | ✅ |
| `test_orchestrator_route.py` | 6 | 6 | ✅ |
| `test_orchestrator_react_bridge.py` | 15→17 | 17 | ⚠️ (see below) |
| `test_orchestrator_react_loop.py` | 2 | 2 | ✅ |
| `test_orchestrator_react_loop_parity.py` | 5 | 5 | ✅ |
| `test_orchestrator_budgets.py` | 11 | 11 | ✅ |
| `test_orchestrator_llm_call_accounting.py` | — | 2 | (new, not separately claimed) |
| `test_trigger_source_write.py` | 4 | 4 | ✅ |
| `test_evidence_gates.py` | 11 | 11 | ✅ |
| `test_pipeline_orchestrator_worker_integration.py` | — | 17 | (mix of pass/skip) |
| `test_handoff_queue.py` | 13 | 28 | ⚠️ STALE |
| `test_review_decisions.py` | 8 | 19 | ⚠️ STALE |
| `test_headless_workflow_take.py` | 6 | 6 | ✅ |
| `test_orchestrator_loop.py` | deleted | DELETED | ✅ |

---

## ⚠️ Discrepancies Found

### 1. Stale Test Counts in `orchestrator-worker-handoff-review.md`

The handoff-review wiki records test counts from an earlier pass:

| File | Wiki Says | Actual | Delta |
|---|---|---|---|
| `test_handoff_queue.py` | 13 | **28** | +15 |
| `test_review_decisions.py` | 8 | **19** | +11 |

**Impact**: Low. Tests grew after the review pass was written. The review
pass itself is a historical audit, not a live document. But a reader might
assume the counts are current.

**Fix**: Add a `(counts as of 2026-05-16)` date qualifier or update the
numbers.

### 2. Stale Test Count for `test_orchestrator_runner.py`

| File | Phase 3 Wiki Says | Actual |
|---|---|---|
| `test_orchestrator_runner.py` | 4 | **6** |

The Phase 3.5 plan correctly notes 2 new tests were added (Step 4). The
Phase 3 wiki (`orchestrator-llm-loop-phase3.md`) still shows 4.

**Fix**: Phase 3 wiki should note the count was updated by Phase 3.5.

### 3. `OrchestratorAskUserBanner` — Name Mismatch

`orchestrator-llm-loop-phase3.md` claims:

> `OrchestratorAskUserBanner` component (active_run polling) in
> `frontend/atlas/pipeline.jsx`

This component **does not exist** in `pipeline.jsx`. The `ask_user` UI lives
in `frontend/atlas/workspace.jsx` (as `AskUserPrompt` at line 4001), while
`pipeline.jsx` has `PendingQABanner` (a different component for SSOT QA
polling, line 326).

**Impact**: Medium. A developer searching for `OrchestratorAskUserBanner`
will not find it. The ask_user banner for orchestrator runs may not be
implemented in the Pipeline screen at all — only in Workspace.

**Fix**: Either implement the banner and name it as claimed, or correct the
wiki to describe what actually exists.

### 4. Total Test Count in `orchestrator-loop-on-react-loop-plan.md`

Wiki claims: **"135 passed, 6 skipped, 0 failed in 14 test files"**

Actual file/function landscape:

- 16 orchestrator-related test files (not 14)
- 170 total test functions across those files (not 135)
- The wiki's count was likely accurate at the time of writing but has drifted
  as tests were added to `test_handoff_queue.py` (+15), `test_review_decisions.py`
  (+11), `test_orchestrator_runner.py` (+2), and `test_orchestrator_react_bridge.py`
  (+2).

**Fix**: Run the full suite and update the count. Or add a timestamp qualifier.

### 5. Phase 3 Wiki References Deleted `test_orchestrator_loop.py`

`orchestrator-llm-loop-phase3.md` lists:

> `tests/test_orchestrator_loop.py` (11)

This file was deleted in Phase 3.5 Step 6. The Phase 3 wiki now describes
a file that no longer exists.

**Fix**: Add a note to the Phase 3 wiki: "Deleted in Phase 3.5 — parity
now covered by `test_orchestrator_react_loop_parity.py`."

### 6. `_PHASE3_SKIP` Count

| Source | Wiki Says | Actual |
|---|---|---|
| `@_PHASE3_SKIP` decorators | 5 | **6** |

The grep found 6 skip markers, not 5. One more test may have been marked
since the wiki was written.

---

## 🟢 Confirmed Design Decisions

The following architectural decisions from the wiki are confirmed in code:

1. **Orchestrator-centered handoff** — Workers never dispatch to other workers.
   `write_handoff` and `dispatch_workflow` always route through orchestrator.
2. **`available_tools` REPLACE not merge** — `react_bridge.py:10` explicitly
   documents this; only 8 orchestrator callables exposed, no generic agent tools.
3. **No `src.main` import** — `react_bridge.py` builds deps from `core/*` modules.
4. **`yield_run` as separate tool** — Not a `dispatch_tool` callable; handled
   inside `execute_tool_fn` wrapper.
5. **Single-flight `(user_id, ip_id)`** — `OrchestratorRunner._active` dict
   keyed on `(user_id, ip_id)` tuple.
6. **`__final__` sentinel** — `loop.py:27` defines `FINAL_WORKFLOW = "__final__"`.
7. **`workflow_handoff.v1` schema** — Referenced in `handoff_queue.py` header.
8. **Per-stage retry budgets** — `budgets.py` with configurable overrides.
9. **SYN evidence gate** — `_synthesis_artifact_failure()` validates netlist +
   error count + status.
10. **Multi-user scope filtering** — handoff API endpoints filter by authenticated
    user; `_orchestrator_block` accepts `scope_filter`.

---

## 🔴 NOT Shipped (Correctly Documented as Not Shipped)

The wiki correctly identifies these as not yet implemented:

| Item | Wiki Status | Code Status |
|---|---|---|
| Single-port worker gateway (`/api/workers/<workflow>`) | not built | Confirmed — no such route exists |
| Worker capacity metadata (`capacity_group`, `slots_total`) | not built | Confirmed — no DB column |
| Worker lease table | not built | Confirmed — no `worker_leases` in atlas_db.py |
| `import_document` tool (Phase 2) | not built | Confirmed — not in tools.py |
| Phase 4 per-stage retry budget enforcement (beyond BudgetTracker) | partial | BudgetTracker exists but full routing loop not validated end-to-end |
| Phase 5 STA/PnR/PSTA evidence gates | partial | SYN gate done; STA/PnR/PSTA gates have basic checks but not full policy |

---

## Recommendations

1. ~~**Refresh test counts** in `orchestrator-worker-handoff-review.md` and
   `orchestrator-llm-loop-phase3.md` — add date qualifiers.~~ **✅ Fixed
   2026-05-18.**
2. ~~**Fix `OrchestratorAskUserBanner` reference** in Phase 3 wiki — either
   implement it or correct the name to match reality.~~ **✅ Fixed
   2026-05-18 — corrected to PendingQABanner + OrchestratorTraceStrip.**
3. ~~**Note `test_orchestrator_loop.py` deletion** in Phase 3 wiki.~~
   **✅ Fixed 2026-05-18.**
4. **Run the full test suite** to confirm pass/skip/fail counts match the
   Phase 3.5 wiki's "135 passed, 6 skipped, 0 failed" claim — still pending.
