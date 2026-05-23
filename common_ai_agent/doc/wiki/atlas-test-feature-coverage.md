# ATLAS Test → Feature Coverage Map

> **Last updated:** 2026-05-23
> **Scope:** All `tests/*.py` files at repo root level (161 active files) and the production features they exercise.
> **Audience:** Engineers landing changes that touch orchestrator, worker fleet, multi-user state, or pipeline DAG — use this to find which test file gates your change.

---

## 0. How to read this doc

- **Feature** = production capability (orchestrator, lazy worker spawn, SSOT export, …)
- **Code path** = the file(s) that implement it
- **Tests** = pytest files in `tests/` that exercise it
- **Status** = one of `OK · LIVE-LLM · SKIPS-ON-ENV · DEPRECATED · CLI-ONLY`

### CI

Every push and pull request to `main` or `feature/*` runs two automated jobs via `.github/workflows/tests.yml`:

| Job | Trigger | Command | Timeout |
|---|---|---|---|
| `python-smoke` | all pushes/PRs, Python 3.9 + 3.11 matrix | `./scripts/run_tests.sh smoke` | 5 min |
| `python-quick` | push to `main` or PR labeled `full-ci` | `./scripts/run_tests.sh quick` | 15 min |
| `frontend` | all pushes/PRs | `cd frontend/atlas && npx vitest run` | 5 min |

Deps installed from `requirements-test.txt` (pytest, fastapi, uvicorn, httpx, anthropic, pyyaml, aiofiles). Badge: `https://github.com/together2329/brian_hw/actions/workflows/tests.yml/badge.svg`

---

### How to verify quality (anyone landing on this repo)

One command does everything:
```
./scripts/run_tests.sh         # default: quick (no live LLM, ~3 min)
./scripts/run_tests.sh smoke   # 5 critical paths, ~10s — sanity check
./scripts/run_tests.sh full    # everything except real-LLM workers, ~5 min
./scripts/run_tests.sh live    # real LLM calls (needs .env, costs money)
./scripts/run_tests.sh load    # real subprocess load tests (cold-start + memory leak, ~3 min, needs ATLAS_LOAD_TEST=1)
```

The `quick` slice is what CI / a new contributor should run. `live` is gated by an `LLM_API_KEY` check.

#### Cost estimation

Before committing to a `live` run, preview the estimated cost with no network calls:

```bash
python3 scripts/llm_cost_dryrun.py --mode live
```

`run_tests.sh live` automatically runs this estimator and prompts `Continue with ~$X estimated cost? [y/N]` before making any LLM calls. Pass `--yes` to skip the prompt (CI / scripted runs):

```bash
./scripts/run_tests.sh live --yes
```

The estimate is conservative: 4,000 input + 2,000 output tokens per test case, no cache credit. Actual spend is typically lower.

Run a single file directly:
```
python3 -m pytest tests/<file>.py -q --tb=short
```

You no longer need `--ignore=...` flags. `tests/conftest.py:collect_ignore_glob`
skips the dead-import paths automatically (see §5).

---

## 0.5 Test execution sequence (at a glance)

### Mode → Test slice tree

```
./scripts/run_tests.sh {mode}
├─ smoke (5s)
│  ├─ tests/test_production_parity.py::test_atlas_ui_imports_cleanly_as_main_module
│  ├─ tests/test_orchestrator_react_loop.py
│  ├─ tests/test_atlas_db.py::test_atlas_db_concurrent_writers
│  └─ ... (36 total, ~10s)
│
├─ quick (3 min) — DEFAULT
│  └─ smoke + frontend + selective workflow/orchestrator suites
│
├─ full (5 min)
│  └─ quick + load-gated tests (skipped if ATLAS_LOAD_TEST ≠ 1)
│
├─ live (15 min)
│  └─ full + real-LLM calls (needs .env, asks cost before running)
│
├─ frontend (1.6 min)
│  └─ cd frontend/atlas && npx vitest run (9 JSX cases)
│
├─ load (ATLAS_LOAD_TEST=1, ~3 min)
│  ├─ test_lazy_worker_cold_start_storm.py (12-way spawn, 4 cases)
│  ├─ test_lazy_worker_real_cold_start.py (benchmark)
│  └─ test_lazy_worker_memory_leak.py (benchmark)
│
└─ mutation (overnight)
   └─ mutmut: core/atlas_db.py + src/atlas_api_jobs.py (see §7)
```

### CI jobs

| Job | Trigger | Command | Suite size | Timeout |
|---|---|---|---|---|
| `python-smoke` | push/PR, matrix py3.9+py3.11 | `./scripts/run_tests.sh smoke` | 36 cases | 5 min |
| `python-quick` | push to main / PR `full-ci` label | `./scripts/run_tests.sh quick` | 90+ cases | 15 min |
| `frontend` | push/PR | `cd frontend/atlas && npx vitest run` | 9 cases | 5 min |

### Developer workflow (edit → CI → release)

1. **Local edit** → modify source code
2. **smoke** → `./scripts/run_tests.sh smoke` (~10s sanity check)
3. **frontend** → if touched JSX: `./scripts/run_tests.sh frontend` (~1.6s)
4. **push to branch** → GitHub Actions fires all 3 CI jobs in parallel
5. **PR review** → CI completes (smoke + quick + frontend green)
6. **merge to main** → GitHub re-runs all 3 jobs as final gate
7. **weekly load sweep** → manual `ATLAS_LOAD_TEST=1 ./scripts/run_tests.sh load` (cold-start + memory)
8. **monthly mutation** → manual `./scripts/run_tests.sh mutation` (overnight; see [[mutation-baseline-2026-05-23]])
9. **pre-release** → `./scripts/run_tests.sh live --yes` (all LLM paths, costs estimated)

### Test inventory snapshot

| Layer | Suite | File count | Case count | Tools |
|---|---|---|---|---|
| **DB / Storage** | A | 6 files | 50+ cases | pytest, SQLite |
| **Orchestrator** | C | 20 files | 84 cases | pytest, uvicorn, httpx |
| **Worker / Dispatch** | D | 12 files | 60+ cases | pytest, multiprocessing, threading |
| **Pipeline / DAG** | E | 7 files | 35+ cases | pytest, YAML |
| **Frontend** | K | 3 JSX files | 9 cases | vitest, @testing-library/react, jsdom |
| **Production parity** | O | 1 file | 4 cases | pytest, subprocess, SIGTERM/SIGKILL |
| **LLM cost** | I | embedded | 1 dryrun | static analysis, no network |
| **Load / Stress** | O | 2 files | 2 benchmarks | pytest, RSS sampling, real processes |
| **TOTAL ACTIVE** | — | **161 files** | **300+ cases** | pytest 7.x, vitest 1.x |

---

## 1. Category summary

| # | Category | Test files | Primary owner code |
|---|---|---|---|
| A | ATLAS DB / Storage / Schema | 6 | `core/atlas_db.py` (4494 LOC) |
| B | Multi-user / Session / Auth | 12 | `core/atlas_auth.py`, `core/session_manager.py` |
| C | Orchestrator (chat + react loop) | 20 | `src/orchestrator/runner.py`, `core/react_loop.py` |
| D | Worker fleet / Dispatch / Lazy spawn | 12 | `src/atlas_api_jobs.py` (5395 LOC) |
| E | Workflow Stages / Pipeline DAG | 7 | `src/workflow_stage_engine.py` (1977 LOC) |
| F | SSOT / RTL / TB generation | 18 | `workflow/{ssot,rtl,fl-model}-gen/scripts/` |
| G | Simulation / Coverage / Debug | 5 | `workflow/sim_debug/`, `frontend/atlas/coverage.jsx` |
| H | Chat Responder / Plan / Streaming | 12 | `src/atlas_api_chat.py`, `core/stream_parser.py` |
| I | LLM API / Cost / Pricing | 8 | `src/llm_client.py` (5238 LOC) |
| J | Tools / Edit / Replace / Cache | 9 | `core/tools.py` (7493 LOC), `core/tool_schema.py` |
| K | Frontend / Dashboard / Pipeline screen | 10 | `frontend/atlas/{pipeline,workspace,user-dashboard}.jsx` |
| L | Git / Wiki / Docs | 4 | `src/atlas_api_git.py`, wiki scripts |
| M | Custom Agents / Sub-agents | 4 | `core/tools.py` (custom agent path) |
| N | Convergence / Approvals / Promotions | 14 | `core/converge_rules.py`, `src/review_decisions.py` |
| O | Performance / Compat / OS | 14 | `core/compressor.py`, `core/stream_parser.py` |
| P | Browser / cmux / Web | 6 | `workflow/cmux/`, `tests/test_web_cmux.py` |
| | **TOTAL** | **161** | |

---

## 2. Feature ↔ Test matrix

### A. ATLAS DB / Storage / Schema

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Multi-tenant SQLite + WAL | `core/atlas_db.py` | `test_atlas_db.py`, `test_atlas_db_orchestrator.py`, `test_db_schema_complete.py`, `test_db_operations_rigorous.py` | After 2026-05-23: `AtlasDB._lock` is class-level RLock (all instances share). Test `test_db_concurrent_workflow_runs` covers concurrent writer behavior. |
| Observability ledger | `core/atlas_db.py` (trace_events) | `test_atlas_observability_db.py` | LLM call timeline, tool execution timing. |
| Storage backend abstraction | `core/atlas_db.py` (storage helpers) | `test_atlas_storage.py` | |

### B. Multi-user / Session / Auth / Permissions

| Feature | Code | Tests | Notes |
|---|---|---|---|
| User session namespace `user/ip/workflow` | `src/atlas_ui.py:activateNamespace` (FE), `core/session_manager.py` (BE) | `test_atlas_multiuser_session_scope.py`, `test_session_manager.py`, `test_session_names.py`, `test_chat_full_multiuser_system.py`, `test_multiuser_bridge.py` | 55 cases verify isolation between concurrent users. |
| Auth / token / cookie | `core/atlas_auth.py` (956 LOC) | `test_atlas_admin_auth.py`, `test_atlas_account_recovery.py`, `test_canonical_user_id.py` | |
| Per-user QA history scope | `src/atlas_api_jobs.py` + DB | `test_atlas_qa_history_scope.py` | |
| Process-per-session model | `core/session_manager.py` | `test_process_based_sessions.py` | |
| Session trace events | `core/orchestrator_trace.py` | `test_atlas_session_trace.py` | |

### C. Orchestrator (react loop + chat + runner)

| Feature | Code | Tests | Notes |
|---|---|---|---|
| React loop core | `core/react_loop.py` (2457 LOC) | `test_orchestrator_react_loop.py`, `test_orchestrator_react_loop_parity.py`, `test_orchestrator_react_bridge.py` | |
| Runner (thread pool, single-flight) | `src/orchestrator/runner.py` | `test_orchestrator_runner.py`, `test_orchestrator_route.py` | |
| Chat endpoints `/api/pipeline/orchestrator/chat` | `src/atlas_api_jobs.py:4233` | `test_chat_orchestrator_api.py`, `test_chat_orchestrator_browser.py`, `test_chat_orchestrator_deep.py`, `test_chat_orchestrator_deepdeep.py` | 84 cases total. |
| IP extraction (rejects `default`) | `src/atlas_api_jobs.py:4163 _extract_ip_from_orchestrator_message` | `test_orchestrator_chat_ip_extraction.py` | After 2026-05-23: `default` → empty → 400. |
| Chat message normalization / accounting | `src/atlas_api_jobs.py` | `test_orchestrator_chat_messages.py`, `test_orchestrator_llm_call_accounting.py` | |
| Workflow classifier | `src/orchestrator/prompts.py` | `test_orchestrator_classify.py` | |
| Dispatch seed (initial trigger) | `src/atlas_api_jobs.py` | `test_orchestrator_dispatch_seed.py`, `test_dispatch_seed_direct.py` | |
| `dispatch_workflow` / `read_pipeline_state` tools | `src/orchestrator/tools.py` | `test_orchestrator_tools.py` | After 2026-05-23: direct fallback path now goes through `_ensure_lazy_worker_callback`. |
| Budgets (token/cost caps) | `src/orchestrator/budgets.py` | `test_orchestrator_budgets.py` | |
| Workers route `/api/orchestrator/workers` | `src/atlas_api_jobs.py:4565` | `test_orchestrator_workers_route.py` | Probes cached 1.5s server-side. |
| Document import tool | `src/orchestrator/tools.py` | `test_orchestrator_import_document.py` | |
| DB concurrent workflow runs | `core/atlas_db.py` | `test_db_concurrent_workflow_runs.py` | |
| Job model | `src/atlas_api_jobs.py:_jobs` | `test_job.py` | |

### D. Worker fleet / Dispatch / Lazy spawn

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Lazy worker spawn | `src/atlas_api_jobs.py:_ensure_lazy_worker` | `test_dispatch_seed_direct.py`, `test_parallel_todo_dispatcher.py` | After 2026-05-23: per-URL lock + Semaphore(4) throttle + reaper thread + direct-fallback hook. |
| Per-URL spawn lock | `src/atlas_api_jobs.py:_LAZY_WORKER_URL_LOCKS` | `test_parallel_todo_dispatcher.py` | New post-2026-05-23. |
| Worker reaper (mark dead worker's jobs as error) | `src/atlas_api_jobs.py:_lazy_worker_reaper_loop` | `test_lazy_worker_reaper.py` (6 cases) | 5s poll, runs as daemon thread. |
| Worker URL routing (single-worker vs orchestrator) | `src/atlas_api_jobs.py:_resolve_worker_url` | `test_worker_url_routing.py` | |
| Dispatch fallback (no callback path) | `core/tools.py:_dispatch_workflow_direct_fallback` | `test_agent_worker_dispatch_fallback.py`, `test_dispatch_seed_direct.py` | Now ensures lazy worker via callback. |
| Worker chain (A → B handoff) | n/a (uses `worker_call` from `core/agent_client.py`) | `test_worker_chaining.py` | **LIVE-LLM** — skips on unavailable. |
| Tool execution inside worker | `core/agent_server.py`, `core/tools.py` | `test_worker_tool_execution.py` | **LIVE-LLM**. |
| Workflow guard (binding mismatch) | `src/atlas_api_jobs.py:_worker_workflow_mismatch` | `test_worker_workflow_guard.py` | |
| All-workflows worker (shared 5601) | `core/agent_server.py` `--all-workflows` | `test_worker_all_workflows.py` | |
| Worker LLM cost roll-up | `core/agent_server.py` + DB | `test_worker_llm_cost.py` | |
| ReAct loop LLM call persistence | `core/react_loop.py` + DB | `test_react_loop_worker_llm_call_persist.py` | |
| IP block dedup (avoid double-spawn) | `src/atlas_api_jobs.py` | `test_ipblocks_dedup_worker_path.py` | |
| Workflow tool inventory | `core/tools.py:filtered_available_tools`, `core/tools_web.py:WEB_TOOLS`, `workflow/*/workspace.json:WORKFLOW_DISABLED_TOOLS` | **`test_workflow_tool_inventory.py`** (27 cases) | Catches "I don't have web_search" lie; asserts baseline+web tools present in all 12 worker workflows; checks orchestrator dispatch_workflow enum vs _DEFAULT_WORKER_PORTS drift. Smoke-mode. |

### E. Workflow Stages / Pipeline DAG

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Stage engine (YAML-driven) | `src/workflow_stage_engine.py` (1977 LOC) | `test_workflow_stage_engine.py`, `test_workflow_stage_surface.py` | |
| Pipeline contract | `src/atlas_pipeline_*.py` | `test_atlas_pipeline_contract.py`, `test_atlas_api_pipeline_state.py` | |
| Pipeline chat panel | `src/atlas_api_jobs.py` | `test_pipeline_chat_panel_api.py` | |
| Headless workflow runner (no LLM in test) | `src/headless_workflow.py` (4221 LOC) | `test_headless_workflow_runner.py`, `test_headless_workflow_take.py`, `test_headless_llm_contracts.py` | Contract-driven; deterministic. |
| Pipeline ↔ worker integration | `src/atlas_api_jobs.py` + worker | `test_pipeline_orchestrator_worker_integration.py` | |

### F. SSOT / RTL / TB / FL-model generation

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Approved-state → SSOT promotion | `workflow/ssot-gen/scripts/repair_ssot_schema.py` (and friends) | `test_approved_to_ssot.py`, `test_requirement_promotion.py` (cross-listed N) | |
| SSOT export | `workflow/ssot-gen/scripts/` | `test_ssot_export.py` | |
| SSOT QA / workbench / blocker resolution | `core/tools.py` ssot helpers | `test_atlas_ssot_qa_workbench.py`, `test_ssot_qa_tools.py`, `test_atlas_rtl_blocker_qa.py`, `test_resolve_rtl_blockers.py` | |
| SSOT → RTL contract questions | `workflow/rtl-gen/scripts/ssot_to_rtl.py` | `test_ssot_to_rtl_contract_questions.py` | |
| RTL todo derivation | `workflow/rtl-gen/scripts/derive_rtl_todos.py` | `test_derive_rtl_todos.py` | |
| RTL pipeline (lint + sim) | `workflow/rtl-gen/`, `workflow/sim/` | `test_rtl_pipeline.py` | **SKIPS-ON-ENV** when iverilog/vvp missing. |
| RTL gen source-root guidance | `workflow/rtl-gen/scripts/` | `test_rtl_gen_source_root_guidance.py` | |
| FL ↔ RTL equivalence loop | `workflow/fl-model-gen/` | `test_fl_rtl_equivalence_loop.py` | |
| Cycle model emission | `workflow/fl-model-gen/scripts/emit_fl_model.py` | `test_emit_cycle_model.py` | |
| AXI slave wrapper (minimal RTL) | n/a | `test_mini_axi_slave_wrapper.py` | |
| Worker session SSOT QA | `core/agent_server.py` + ssot tools | `test_session_worker_ssot_qa.py` | |
| Starter preview sim | `workflow/sim/` | `test_starter_preview_sim.py` | **SKIPS-ON-ENV** without simulator. |
| GLM-5.1 headless flow | end-to-end | `test_real_glm51_headless_flow.py` | **LIVE-LLM**, opt-in via `ATLAS_RUN_REAL_LLM_TDD=1`. |
| Goal-audit requirement review | `workflow/goal-audit/` | `test_goal_audit_requirement_review.py` | |

### G. Simulation / Coverage / Debug

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Coverage report API | `src/atlas_api_jobs.py` | `test_atlas_coverage_report_api.py` | |
| Coverage summary | `workflow/coverage/` | `test_coverage_summary.py` | |
| Sim debug elaboration | `workflow/sim_debug/scripts/` | `test_sim_debug_elab.py` | |
| Sim debug top-module resolution | `workflow/sim_debug/scripts/` | `test_sim_debug_top_resolution.py` | |
| Progress / debug ledger | `core/orchestrator_trace.py` | `test_progress_debug.py` | |

### H. Chat Responder / Plan / Streaming

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Chat responder core + ledger | `workflow/chat-responder/` | `test_chat_responder.py`, `test_chat_responder_deep.py`, `test_chat_responder_deepdeep.py`, `test_chat_responder_deepdeepdeep.py`, `test_chat_responder_more.py` | |
| Plan mode | `src/atlas_ui.py` (intent toggle) + `core/react_loop.py` | `test_plan_mode.py` | |
| Streaming chunk format | `core/stream_parser.py` | `test_streaming_chunk_format.py`, `test_streaming_display.py` | `chunk_format` uses `sys.exit()`; CLI-only. |
| Multiline input | `frontend/atlas/workspace.jsx` (FE) + `core/react_loop.py` (BE) | `test_multiline_input.py` | |
| Prompts | `core/react_loop.py` prompts | `test_prompts.py` | |
| Prompt → artifact checklist audit | `core/react_loop.py` | `test_prompt_to_artifact_checklist_audit.py` | |
| Responses API sync (OpenAI Responses) | `src/llm_client.py` | `test_responses_api_sync.py` | |

### I. LLM API / Cost / Models / Pricing

| Feature | Code | Tests | Notes |
|---|---|---|---|
| LLM client (Claude/GLM/Kimi/Deepseek) | `src/llm_client.py` (5238 LOC) | `test_llm_api.py` | **LIVE-LLM**. |
| LLM benchmark | `src/llm_client.py` perf paths | `test_llm_benchmark.py` | |
| CLI model backend selection | `src/llm_client.py` profiles | `test_cli_model_backends.py` | |
| Model pricing aliases | `core/model_pricing.py` (or inline in client) | `test_model_pricing_aliases.py` | |
| Prompt caching | Anthropic prompt cache | `test_cache_read.py` | **CLI-ONLY** (`sys.exit`). |
| Compression fix (context fit) | `core/compressor.py` (1822 LOC) | `test_compression_fix.py` | |
| Embedding model | `core/embeddings.py` | `test_embedding_model.py` | |
| LLM calls workflow tag | `src/atlas_api_jobs.py` + DB | `test_llm_calls_workflow_tag.py` | |

### J. Tools / Edit / Replace / Cache

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Tool descriptions / schema | `core/tools.py`, `core/tool_schema.py` (1213 LOC) | `test_tool_descriptions.py`, `test_tool_schema_api_compat.py` | |
| Tool path resolution | `core/tools.py` | `test_atlas_tool_path_resolution.py` | |
| Edit strategies / replace | `core/tools.py` (edit_in_file etc.) | `test_edit_strategies.py`, `test_replace_advanced.py`, `test_replace_deep.py`, `test_replace_in_file.py`, `test_replace_regression.py` | **All CLI-ONLY** (`sys.exit`). Need conversion to pure pytest. |
| All tools coverage | `core/tools.py` | `test_all_tools.py` | **CLI-ONLY**. |

### K. Frontend / Dashboard / Pipeline screen

| Feature | Code | Tests | Notes |
|---|---|---|---|
| User dashboard | `frontend/atlas/user-dashboard.jsx`, `core/atlas_user_dashboard.py` | `test_atlas_user_dashboard.py` | After 2026-05-23: clicking IP row navigates to workspace. |
| Session filters | `frontend/atlas/` | `test_atlas_frontend_session_filters.py` | |
| Pipeline flow theme | `frontend/atlas/pipeline.jsx` styling | `test_atlas_pipeline_flow_theme.py` | |
| Lint report API | `src/atlas_api_jobs.py` | `test_atlas_lint_report_api.py` | |
| DB ↔ frontend phase 3 integration | full stack | `test_db_frontend_phase3_integration.py` | |
| E2E (Chromium) | full stack | `test_db_full_stack_e2e.py`, `test_db_full_stack_e2e_more.py`, `test_db_full_stack_deepdeep.py` | `_deepdeep` has `skipif(True, reason="optional — needs websocket-client")`. |

### L. Git / Wiki / Docs

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Git API | `src/atlas_api_git.py` | `test_atlas_git_api.py` | |
| Wiki graph build | `core/rag_db.py` + wiki scripts | `test_wiki_build_graph.py` | |
| Wiki query tool | `core/rag_db.py` | `test_wiki_query_tool.py` | |
| Trigger-source write | `src/atlas_api_jobs.py` git integration | `test_trigger_source_write.py` | |

### M. Custom Agents / Sub-agents

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Custom agent definitions (DB-backed) | `core/atlas_db.py` (custom_agents table) | `test_custom_agents.py` | |
| Sub-agent dispatch | `core/tools.py` (`task` tool path) | `test_sub_agents.py` | |
| Agent config | `core/agent_config.py` | `test_agent_config.py` | |
| Agent runner converge | `core/agent_runner.py` | `test_agent_runner_converge.py` | |
| Skill system refactoring | `core/skills.py` | `test_skill_refactoring.py` | **CLI-ONLY**. |

### N. Convergence / Approvals / Promotions

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Converge engine | `core/converge_*.py` | `test_converge_engine.py`, `test_converge_policy.py`, `test_converge_rules.py`, `test_converge_commands.py`, `test_converge_commands_extended.py`, `test_integration_converge.py` | |
| Evidence gates | `src/workflow_stage_engine.py` | `test_evidence_gates.py` | |
| Review decisions | `src/review_decisions.py` | `test_review_decisions.py` | |
| Static command (deterministic stage step) | `src/workflow_stage_engine.py` | `test_static_command.py` | |
| Todo tracking / workflow | `core/todo_tracker.py` | `test_todo_tracking.py`, `test_todo_workflow.py`, `test_atlas_todo_payload.py` | |
| Pipeline contract checks | `src/workflow_stage_engine.py` | `test_atlas_pipeline_contract.py` | |
| Handoff queue | `core/atlas_db.py` queue helpers | `test_handoff_queue.py` | |
| Requirement promotion | `workflow/ssot-gen/` | `test_requirement_promotion.py` | |
| EDA YAML validity | various YAML schemas | `test_eda_yaml_validity.py` | |

### O. Performance / Compat / OS

| Feature | Code | Tests | Notes |
|---|---|---|---|
| Performance benchmark | mixed | `test_performance.py`, `test_llm_benchmark.py` | |
| Cross-platform compat | various | `test_deep_compat.py`, `test_deep_compat_v2.py` | `_v2` is **CLI-ONLY**. |
| Windows specific | `core/io_utils.py`, paths | `test_windows_compat.py`, `test_windows_utf8_io.py` | |
| Portable paths | `core/paths.py` | `test_portable_paths.py` | |
| PySlang fallbacks | `core/tools_verilog.py` | `test_pyslang_compat_fallbacks.py` | |
| Recent changes detection | `src/recent_changes.py` | `test_recent_changes.py` | Some sub-tests skip without Textual UI. |
| Context management | `core/compressor.py` | `test_context_management.py` | |
| Project model | `core/project.py` | `test_project.py` | |
| Workspace alignment | `frontend/atlas/workspace.jsx` ↔ backend | `test_workspace_alignment.py` | |
| Main unit | `src/main.py` | `test_main_unit.py` | |
| Connection warmup | `src/llm_client.py` | `test_connection.py` | |
| E2E API | full stack | `test_e2e_api.py` | `test_e2e.py` excluded (collection error). |
| Streaming display | `frontend/atlas/workspace.jsx` | `test_streaming_display.py` | |

### P. Browser / cmux / Web

| Feature | Code | Tests | Notes |
|---|---|---|---|
| cmux tools (browser automation) | `core/tools.py` cmux helpers | `test_web_cmux.py` | **SKIPS-ON-ENV** when cmux not running. |
| Worker cmux integration | `core/agent_server.py` + cmux | `test_worker_cmux.py` | **SKIPS-ON-ENV + LIVE-LLM**, excluded from default sweep. |
| Atlas runtime settings | `src/atlas_ui.py` runtime config | `test_atlas_runtime_settings.py` | |

---

## 3. Recent changes (2026-05-23) and the tests that gate them

### Production parity (subprocess launch) — `tests/test_production_parity.py`

Launches `src/atlas_ui.py` as a real subprocess to catch sys.path / env-var drift that pytest's
in-process imports cannot see. All four tests use a `subprocess_guard` fixture (SIGTERM → SIGKILL
after 5 s). Escape hatch: `ATLAS_SKIP_SUBPROCESS_TESTS=1`.

| Test | Verifies | Mode |
|---|---|---|
| `test_atlas_ui_imports_cleanly_as_main_module` | `exec(open('src/atlas_ui.py').read())` with `--help` raises no `ImportError`/`ModuleNotFoundError` | smoke + quick + full |
| `test_atlas_ui_launches_and_healthz_responds` | `--exec o` on port 13900 — `GET /healthz` returns 200 (skips if `requests` absent) | quick + full |
| `test_lazy_single_worker_does_not_spawn_eagerly` | `--exec s` prints `[single-worker] lazy mode:` and does NOT bind port 5601 | quick + full |
| `test_env_inheritance_smoke` | `ATLAS_SINGLE_WORKER_EAGER=1` propagates and triggers `[single-worker] spawned main-loop worker` | quick + full |

---

### Change table

| Change | Files | Gating tests | Status |
|---|---|---|---|
| Lazy single-worker mode (`[single-worker] lazy mode: ...`) | `src/atlas_ui.py:17929-18006` | `test_worker_url_routing.py`, `test_dispatch_seed_direct.py` | ✅ Pass |
| AtlasDB class-level write lock (`_WRITE_LOCK` shared by all instances) | `core/atlas_db.py:595-622` | `test_atlas_db.py`, `test_db_concurrent_workflow_runs.py`, `test_atlas_db_orchestrator.py`, **`test_atlas_db_concurrent_writers.py`** (50-thread stress, 2 cases) | ✅ Pass |
| Worker reaper thread | `src/atlas_api_jobs.py:_lazy_worker_reaper_loop` | **`test_lazy_worker_reaper.py`** (SIGKILL → job reconcile, 6 cases) | ✅ Pass |
| Per-URL lock + spawn semaphore (`ATLAS_LAZY_WORKER_SPAWN_PARALLEL=4`) | `src/atlas_api_jobs.py:_get_url_lock`, `_LAZY_WORKER_SPAWN_SEM` | `test_parallel_todo_dispatcher.py`, **`test_lazy_worker_cold_start_storm.py`** (12-way concurrent spawn, 4 cases) | ✅ Pass |
| Health probe 1.5s cache (`_probe_worker_health_cached`) | `src/atlas_api_jobs.py` | `test_orchestrator_workers_route.py` | ✅ Pass |
| Logging → stdout + RotatingFileHandler (`.session/atlas-dispatch.log`) | `src/atlas_api_jobs.py:_dispatch_logger` | covered by existing dispatch tests | ✅ Pass |
| Direct dispatch lazy-spawn hook (`_ensure_lazy_worker_callback`) | `core/tools.py:_dispatch_workflow_direct_fallback`, `src/atlas_api_jobs.py:register_jobs_routes` | `test_dispatch_seed_direct.py`, `test_agent_worker_dispatch_fallback.py` | ✅ Pass |
| `default` IP placeholder → 400 | `src/atlas_api_jobs.py:_extract_ip_from_orchestrator_message` | `test_orchestrator_chat_ip_extraction.py` | ✅ Pass |
| Multi-user job isolation (H2 + H3 leak fix) | `src/atlas_api_jobs.py:api_jobs` (H2: add `request` param + user filter), `src/atlas_api_jobs.py:api_pipeline_state` (H3: already filtered at line 4077) | **`test_multiuser_job_isolation.py`** (4 cases: per-user isolation, local-admin all-visible, pipeline state cross-contamination, unauthenticated 401) | ✅ Pass |
| Dashboard IP-row click → workspace | `frontend/atlas/user-dashboard.jsx` | `test_atlas_user_dashboard.py` (rendering) — UI click manual | ⚠ manual verification |
| WORKERS · ORCH sidebar panel | `frontend/atlas/workspace.jsx:AgentStatusPanel` | none direct (UI) | ⚠ manual verification |
| Orchestrator chat “select IP” warning banner | `frontend/atlas/workspace.jsx:renderPromptRow` | none direct (UI) | ⚠ manual verification |
| `.dir-select-wrap.run-policy` accent border removed | `frontend/atlas/styles.css` | none (cosmetic) | ⚠ manual verification |
| Orchestrator gets `web_search` + `web_fetch` (12 tools) — orchestrator can search the web and fetch URLs directly without round-tripping through a worker. Added schemas to `tool_schemas()`, wrappers in `tools.py`, and handlers in `react_bridge._make_tool_handlers`. | `src/orchestrator/prompts.py`, `src/orchestrator/tools.py`, `src/orchestrator/react_bridge.py` | **`test_workflow_tool_inventory.py::TestOrchestratorToolSet::test_orchestrator_exposes_web_search`**, `test_orchestrator_schema_count_at_least_twelve` | ✅ Pass |
| `_jobs` rehydration on boot (`_rehydrate_jobs_from_db`) — reconciles orphaned `status='running'` DB rows after orchestrator restart; healthy+busy workers rescued, others marked error. Env: none (always on). | `src/atlas_api_jobs.py:_rehydrate_jobs_from_db`, called from `register_jobs_routes` | **`test_jobs_rehydration.py`** (3 cases: rescued count, DB error status, 1-hour cutoff) | ✅ Pass |
| Lazy-worker idle TTL (`ATLAS_LAZY_WORKER_IDLE_TTL_SEC`, default 600 s) — reaper probes alive workers; if `running_count=0` for ≥ TTL seconds, calls `proc.terminate()` and removes from `_LAZY_WORKER_PROCS`. Set to `0` to disable. Tracks `_LAZY_WORKER_LAST_BUSY[url]` (monotonic). | `src/atlas_api_jobs.py:_lazy_worker_reaper_loop`, `_ensure_lazy_worker`, `_LAZY_WORKER_LAST_BUSY`, `_LAZY_WORKER_IDLE_TTL_SEC` | **`test_lazy_worker_idle_ttl.py`** (4 cases: terminate called, removed from procs, busy worker untouched, TTL=0 disables) | ✅ Pass |
| Real cold-start storm (load mode) — 12 uvicorn subprocesses spawned simultaneously on ports 5621-5632; measures time-to-last-ready and peak RSS per PID. Gate: `ATLAS_LOAD_TEST=1`. | `src/main.py --serve`, `core/agent_server.py` | **`test_lazy_worker_real_cold_start.py`** (1 benchmark case) | SKIPS-ON-ENV (`ATLAS_LOAD_TEST`) |
| Long-running memory leak detection (load mode) — 1 worker, 100 /run calls, RSS sampled every 20 calls; asserts final RSS < 1.5× baseline. Gate: `ATLAS_LOAD_TEST=1`. | `src/main.py --serve`, `core/agent_server.py` | **`test_lazy_worker_memory_leak.py`** (1 benchmark case) | SKIPS-ON-ENV (`ATLAS_LOAD_TEST`) |

---

## 4. What is *not* in the test suite

Closed (added 2026-05-23):
- ~~Lazy worker reaper~~ → `test_lazy_worker_reaper.py` (6 cases)
- ~~Orchestrator-mode cold-start storm~~ → `test_lazy_worker_cold_start_storm.py` (4 cases)
- ~~50-way concurrent DB writer~~ → `test_atlas_db_concurrent_writers.py` (2 cases)

Closed (added 2026-05-23 — vitest + @testing-library/react setup in `frontend/atlas/`):
- ~~Dashboard IP-row click navigation~~ → `__tests__/dashboard-ip-row-click.test.jsx`
- ~~AgentStatusPanel WORKERS section~~ → `__tests__/workers-sidebar-panel.test.jsx`
- ~~Orchestrator chat "select IP" warning banner~~ → `__tests__/default-ip-banner.test.jsx`

Closed (added 2026-05-23 — load mode):
- ~~**Orchestrator-mode cold-start storm**~~ → `test_lazy_worker_real_cold_start.py` (12-way real spawn; gate `ATLAS_LOAD_TEST=1`)
- ~~**Long-running memory leak**~~ → `test_lazy_worker_memory_leak.py` (100 /run calls, RSS growth cap; gate `ATLAS_LOAD_TEST=1`)

Still open (no automated coverage; manual or new tests needed):

- **`.dir-select-wrap.run-policy` border change** — cosmetic, low priority.
- **`atlas-dispatch.log` rotation correctness** — relies on stdlib RotatingFileHandler defaults; could add a synthetic 6 MB write test.
- **single-worker `WORKER_URL_DEFAULT=http://127.0.0.1:5601` env injection** — checked only indirectly via `_worker_url_is_shared_default`. A focused test on the env-set side of `atlas_ui.py:_single_worker_mode` branch would catch regressions.

Run JSX tests with: `./scripts/run_tests.sh frontend` (or `cd frontend/atlas && npx vitest run`).

---

## 5. Deprecated / broken / CLI-only test files

### 5.1 DELETED 2026-05-23 (dead imports — module `agents.sub_agents` removed in 69c75003)

| File | Failing import |
|---|---|
| `tests/test_agents/test_explore_agent_improved.py` | `agents.sub_agents.explore_agent` |
| `tests/test_agents/test_plan_agent_improved.py` | `agents.sub_agents.plan_agent` |
| `tests/test_agents/test_explore_agent.py` | conditional `agents.sub_agents.*` |
| `tests/test_integration/test_agent_iterations.py` | `agents.sub_agents.explore_agent`, `agents.sub_agents.plan_agent` |
| `tests/test_core/test_context_logging.py` | `agents.sub_agents.explore_agent` |
| `tests/test_core/test_debug_config.py` | `agents.sub_agents.base` |

All 6 removed via `git rm`. `conftest.py` entries for these files also removed.

### 5.2 Intentionally broken (manual-only)

| File | Why |
|---|---|
| `tests/test_integration/test_rag_interactive.py` | `sys.exit(1)` at module level — guards interactive harness. Either move out of `tests/` or wrap in `pytest.mark.skip(reason="interactive")`. |

### 5.3 CLI-only test scripts (`sys.exit()` at top level, not pytest-compatible)

These scripts have been moved to `scripts/cli_tests/`. Run with `python3 <file>`, not pytest.

| File |
|---|
| `scripts/cli_tests/test_all_tools.py` |
| `scripts/cli_tests/test_cache_read.py` |
| `scripts/cli_tests/test_edit_strategies.py` |
| `scripts/cli_tests/test_deep_compat_v2.py` |
| `scripts/cli_tests/test_replace_advanced.py` |
| `scripts/cli_tests/test_replace_in_file.py` |
| `scripts/cli_tests/test_replace_deep.py` |
| `scripts/cli_tests/test_replace_regression.py` |
| `scripts/cli_tests/test_skill_refactoring.py` |
| `scripts/cli_tests/test_streaming_chunk_format.py` |

### 5.4 Collection errors (other)

| File | Cause |
|---|---|
| `tests/test_e2e.py` | collection error — needs triage. |
| `tests/test_lib/test_deep_think.py` | collection error. |
| `tests/test_lib/test_readline_autocomplete.py` | `OSError: reading from terminal` — runs only when stdin attached. |
| `tests/test_worker_cmux.py` | needs cmux env; excluded from sweep but works manually. |

---

## 6. Environment-skipped (graceful, kept)

These tests `self.skipTest(...)` when their environment is unavailable. **Do not delete**; they cover real features.

| Reason | Tests |
|---|---|
| **LLM unavailable** | `test_worker_cmux.py`, `test_worker_tool_execution.py`, `test_worker_chaining.py`, `test_agent_server.py`, `test_rtl_pipeline.py` (subset) |
| **iverilog / vvp missing** | `test_rtl_pipeline.py:59,71,87,130,147,164` |
| **Textual UI not installed** | `test_recent_changes.py:1338` |
| **websocket-client missing** | `test_db_full_stack_deepdeep.py:329` (skipif true) |
| **opt-in env (`ATLAS_RUN_REAL_LLM_TDD=1`)** | `test_real_glm51_headless_flow.py:31` |
| **Missing test assets** | `test_recent_changes.py:867,930,1027,1052`, `test_integration/test_pcie_spec_code.py:60+` |
| **fastapi not installed** | `test_worker_workflow_guard.py:24`, `test_agent_server.py:94` |

---

## 7. Coverage gaps and follow-ups

Closed (2026-05-23):
1. ~~Cold-start load test~~ → `tests/test_lazy_worker_cold_start_storm.py` (4 cases)
2. ~~Reaper test~~ → `tests/test_lazy_worker_reaper.py` (6 cases)
3. ~~Concurrent DB writer stress~~ → `tests/test_atlas_db_concurrent_writers.py` (50-thread stress, 2 cases)
4. ~~Convert §5.3 CLI scripts to pytest~~ → moved to `scripts/cli_tests/` (no longer hit by default sweep)
5. ~~Long `--ignore=` flag list~~ → `tests/conftest.py:collect_ignore_glob` handles it; `pytest tests/` Just Works
6. ~~No single entry point~~ → `./scripts/run_tests.sh {quick|full|live|smoke}`
7. **Mutation baseline attempted (2026-05-23)** — mutmut 3.3.1 installed; `setup.cfg [mutmut]` and `scripts/run_tests.sh mutation` mode configured. Baseline run timed out at 9 min (cap: 5 min) during stats-collection phase before any mutation was tested. See [`doc/wiki/mutation-baseline-2026-05-23.md`](mutation-baseline-2026-05-23.md) for full details and re-run instructions.

Still open:
- **Default-IP banner snapshot test** in `frontend/atlas/` — blocked on a JSX test runner. Add `vitest` + `@testing-library/react` (separate PR).
- **Dashboard IP-row click handler** — same JSX blocker.
- **AgentStatusPanel WORKERS panel render** — same blocker.
- **`atlas-dispatch.log` rotation** — write 6 MB to the logger and assert backup files appear.
- **single-worker env injection** — add `tests/test_single_worker_env_injection.py` that imports `atlas_ui` with the lazy single-worker flag and asserts `WORKER_URL_DEFAULT` is set.
- ~~**Decide on `tests/test_agents/`**~~ — 6 dead-import files removed 2026-05-23 (see §5.1). `test_agents/test_sub_agents.py` kept (covers live `core/tools.py` task-tool path).

---

## 8. How features pair with test files (cheat sheet)

If you touch …                         → run …
- `core/atlas_db.py`                   → A + B + C subsets
- `src/atlas_api_jobs.py`              → C + D + workers route
- `src/orchestrator/*`                 → all of C
- `core/react_loop.py`                 → C subset + `test_react_loop_worker_llm_call_persist.py`
- `workflow/ssot-gen/`                 → F subset (approved/SSOT/QA)
- `workflow/rtl-gen/`                  → F subset (derive/contract/pipeline)
- `workflow/sim*/`                     → G + F (sim/starter_preview)
- `core/tools.py`                      → J + parts of D (dispatch fallback)
- `frontend/atlas/workspace.jsx`       → K manual + `test_workspace_alignment.py`
- `frontend/atlas/pipeline.jsx`        → K manual + `test_atlas_pipeline_flow_theme.py`
- `core/atlas_auth.py`                 → B subset
- `src/llm_client.py`                  → I subset (live LLM)

---

## 9. References

- Production catalog: §1 column 4 (Primary owner code)
- Memory: `~/.claude/projects/-Users-brian-Desktop-Project-brian-hw/memory/` (project_silent_pass_exposure.md, project_orchestrator_loop_decision.md)
- Wiki cross-links: `atlas-pipeline-screen.md`, `atlas-pipeline-db-state.md`, `concurrent-dispatch-queue-20260519.md`, `db-concurrent-write-race-20260519.md`, `e2e-orchestrator-validation-plan.md`
