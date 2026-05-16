# Wiki Log

## 2026-05-16

- Review of [[orchestrator-worker-handoff]] captured at
  [[orchestrator-worker-handoff-review]]. Gap audit against
  `src/atlas_api_jobs.py`, `core/delegate_runner.py`, `core/atlas_db.py`,
  `frontend/atlas/pipeline.jsx`, and `src/headless_workflow.py`: the
  orchestrator-mode switches (`ATLAS_ORCHESTRATOR_MODE`, gateway flag,
  path-prefix `/api/workers/<wf>` route), handoff JSON queue,
  `worker_leases` table, `/take` CLI, and orchestrator fields in
  `/api/pipeline/state` are all doc-only today. Already shipped: 2 s
  poll + `/api/pipeline/dispatch`, single-endpoint `WORKER_URL_*` worker
  dispatch (`localhost:8001` default, no gateway). Highest-value fix is a
  "Status: design spec" banner at the top of
  `orchestrator-worker-handoff.md`; remaining nits (port mismatch, missing
  `workspace_id` isolation key, ambiguous `last_heartbeat_at: "UTC"`,
  schema-version pointer, line-416/433 wording tension) are incremental.
- Review response applied: [[orchestrator-worker-handoff]] now starts with a
  design-spec status banner, marks orchestrator API/gateway/`/take` behavior as
  target design rather than shipped behavior, removes the unsupported
  `ORCHESTRATOR_MODE=1` alias, adds `workspace_id` to isolation scope, switches
  heartbeat examples to ISO-8601 UTC timestamps, marks `workflow_handoff.v1` as
  schema TBD, and narrows the worker helper exception.
- Second-pass review response: renamed the durable run identifier in
  [[orchestrator-worker-handoff]] to `pipeline_run_id` with a note flagging the
  collision risk against the existing in-memory `pipeline_id` in
  `src/atlas_api_jobs.py`; added `workspace_id` to the ownership chain ASCII
  tree; moved the shipped-port-per-worker disclaimer to the top of the Worker
  Ports section; defined the `<owner>` placeholder for Review Decision Needed
  filenames; clarified that offline workers omit `last_heartbeat_at`.
- Shipped the StageCard action UX (review finding #5 completion): three
  new HTTP endpoints `GET /api/handoff/list`, `POST /api/handoff/save`,
  `POST /api/handoff/take`, all scope-filtered by the authenticated user
  and clearing `_state_cache` on writes. `/api/pipeline/state` per-stage
  payload now carries `workflow` and `handoffs:{pending,claimed,done,
  review,latest}` so the StageCard renders `⇄ take N` and `📬 save handoff`
  buttons without threading the whole pipeline state down. Frontend
  buttons in `frontend/atlas/pipeline.jsx` post to the new endpoints and
  fire `atlas:pipeline-poll` for immediate refresh. End-to-end verified
  on `simple_gpio_lite` (12-step flow with cross-user `alice/bob`
  isolation) and `arm_m0_min` (7-step coverage→tb-gen flow with cross-IP
  isolation against `simple_gpio_lite`). 6 new pytest regression tests in
  `tests/test_atlas_api_pipeline_state.py` push the touched-file suite to
  79/79 passing. See [[orchestrator-worker-handoff-review]] "Fifth pass
  applied".
- Deep^6 adversarial test sweep against the orchestrator/handoff stack —
  60 stress scenarios across 6 rounds (happy path, scale, security, races,
  cross-process, multi-user) + 74 pytest cases. Caught and permanently fixed
  5 real bugs not surfaced by the original review:
  1. `claim_next` ignored `scope_filter` → multi-user CLI take could grab
     another user's older handoff. Added kwarg + regression test.
  2. Oversize `handoff_id` (>200 chars) leaked raw `OSError [Errno 63]`
     `File name too long`. Validator now rejects with a typed `ValueError`.
  3. Two threads rewriting the same JSON file raced on `os.replace`. Per-thread
     unique `.tmp.{pid}.{tid}.{uuid}` suffix in both `handoff_queue._write_json`
     and `review_decisions._atomic_write_json`.
  4. `/api/pipeline/state` cache key was `(ip,)` only and `_orchestrator_block`
     ignored auth — user_a polling the shared-IP endpoint saw user_b's
     handoffs. Cache key now `(ip, user_id)`; scope filter derived from
     `request.scope["user"]`.
  5. Oversize `ip` query param (e.g., 500 chars) also caused `OSError [Errno 63]`
     at downstream `stat()`. 64-char cap in the validator.
  Performance baseline established: 1549 writes/sec, `summary_by_workflow` on
  5000 records in 386 ms, 4-subprocess `--stages take` race with zero
  double-claims. See [[orchestrator-worker-handoff-review]] "Fourth pass applied".
- Implementation pass against the [[orchestrator-worker-handoff-review]] gap
  audit. Five slices landed (36 tests passing total):
  1. `src/handoff_queue.py` — durable `<ip>/handoff/{suggested,pending,claimed,
     done,review}/*.json` state machine with atomic moves and schema validation
     (`workflow_handoff.v1`).
  2. `src/review_decisions.py` — pipeline-level Review Decision Needed writer
     for `<ip>/review/decision_needed_pipeline_repeated_<owner>[_<signature>]_mismatch.json`
     with idempotent updates and `resolve_decision`.
  3. `ATLAS_ORCHESTRATOR_MODE` flag wired into `/api/pipeline/state`. New
     payload keys `orchestrator{enabled, mode, pending_handoffs, claimed_handoffs,
     review_decisions, decisions_needed, workers}` and `handoffs_by_workflow{}`
     are always emitted; counts read from disk regardless of flag, only
     `enabled`/`mode` toggle on env. Gateway/worker capacity is not built so
     `workers` stays empty and `mode` reports `json` when enabled.
  4. `python3 src/headless_workflow.py --stages take --workflow <wf>` claims
     the oldest pending handoff FIFO, runs the owner workflow once, completes
     on pass or releases the claim on fail/error. `--workflow` is required for
     the take path.
  5. Pipeline run-bar chips: `orchestrator: json`, `⇄ N pending`, `△ K review`
     render next to the running chip when the new payload reports them.
  Out of scope and deferred: gateway path-prefix routing (`/api/workers/<wf>`),
  `worker_leases` table + per-user lease isolation, in-memory `pipeline_id` to
  durable `pipeline_run_id` rename in `atlas_api_jobs.py`, dispatch/`take`/`view
  evidence` action buttons inside StageCards.
- New wiki page [[orchestrator-worker-handoff]] captures the control-plane
  contract: an orchestrator agent manages workflow workers, dispatches repair
  feedback in real time when worker mode is available, and otherwise writes
  durable `<ip>/handoff/pending/*.json` packets for another workspace to claim
  with `/take`. This keeps Workspace one-stage-at-a-time while pipeline mode
  can still coordinate owner-classified repair loops.
- Follow-up decision captured in [[orchestrator-worker-handoff]] and
  `.omx/plans/prd-orchestrator-worker-handoff.md`: cross-workflow routing is
  orchestrator-centered. Workers may write `suggested_handoff` records, but
  only the orchestrator dispatches to another workflow worker. UI integration
  is through the existing Pipeline screen: `/api/pipeline/state` exposes
  orchestrator mode plus handoff counts, StageCards show pending handoffs and
  owner repair actions, and Workspace resumes JSON handoffs through `/take`.
- Orchestrator UI contract refined: `ATLAS_ORCHESTRATOR_MODE=1` makes Pipeline
  the control plane and Workspace/Workflow screens detail surfaces only.
  Workflow tab changes do not stop running workers in this mode; non-
  orchestrator mode keeps the existing stop-before-switch prompt for a local
  running agent. Orchestrator may receive user input, but it records answers as
  durable Review/Pipeline Decisions and routes them to owner workflows rather
  than keeping them only in chat/Q&A history. Pipeline state should also show
  worker runtime status (`running`, `idle`, `blocked`, `stale`, `offline`,
  `done`) with current task, elapsed time, and heartbeat when available.
  Worker port rule: ATLAS should expose one Orchestrator/Gateway port; workflow
  workers are addressed by paths such as `/api/workers/rtl-gen`, and scheduling
  uses gateway capacity metadata rather than URL count. Do not make users manage
  one port per workflow.
- Multi-user feasibility clarified in [[orchestrator-worker-handoff]]:
  existing ATLAS already has DB users/sessions/IP permissions, user-filtered
  session APIs, chat permission tests, and `.session/<session>/<ip>/<workflow>/`
  scoping. Production orchestrator mode still needs per
  user-assigned orchestrators, per `session_id/pipeline_id` run contexts,
  scoped worker leases, gateway output filtering, and permission-gated admin
  aggregation.
- Captured [[gpio-serial-pipeline-run]]: `simple_gpio_lite` now reaches
  clean RTL compile/lint/todo closure, then stops at `tb-gen` human gate
  because 32 required equivalence goals carry FunctionalModel
  `ssot_question` markers. Fixed the common scoreboard self-check so this
  condition writes `tb/cocotb/tb_blocked.json` and blocks before sim, rather
  than allowing `tb-gen PASS` followed by 32 soft FL-vs-RTL mismatches.
- Tightened the upstream SSOT gate for the same GPIO finding. `check_ssot_disk.sh`
  now requires every non-reset `function_model.transactions[]` item to have
  executable `output_rules` or `state_updates`, while
  `repair_ssot_schema.py --strict-downstream` reports
  `SSOT_FM_MACHINE_RULES_MISSING_*` blockers in
  `req/ssot_downstream_blockers.json`. This is general-IP validation, not a
  GPIO template: a temp-copy `simple_gpio_lite` run now blocks at ssot-gen with
  six missing machine-rule transactions (`FM1`-`FM6`) before FL/RTL/TB token
  spend.
- New top-level ATLAS screen: [[atlas-pipeline-screen]] (`◫ Pipeline`,
  branch `feature_pipeline_ui`). Replaces the mock `◫ Architect`
  screen. Each of the 14 canonical stages becomes a click on a stage
  card with a 3-5 dot KPI scoresheet read from on-disk evidence JSON;
  the DAG MAP at the top shows token-flow animation along edges from
  running stages. Failed cards offer `[ go fix <owner> ]`, never
  `[ retry ]`, per [[workflow-ownership-and-boundaries]]. Live state
  served from a new `GET /api/pipeline/state?ip=<ip>` endpoint that
  composes `_job_artifact_recovery` + the existing `/api/jobs` poll +
  per-stage evidence JSON readers.
- New wiki page [[ui-design-references]] documents external UI
  checkouts under `~/Desktop/Project/brian_hw/external_refs/`.
  First entry: `nexu-io/open-design` (Apache-2.0). Pattern map: their
  `Theater/ScoreTicker` → our `MiniScoresheet`, `PanelistLane`
  `data-role` borders → our phase-band tints, `runtime/todos.ts`
  reverse-walk → our running-card mini-todo list, `InterruptButton`
  Esc keybind → our running-card `⏹`, `LiveArtifactBadges` → our
  state badges. Conceptual borrowing only — no code copied, no
  CSS / fonts / OKLch palettes / Next.js machinery imported.
- New IP run captured: [[arm-m0-min-pipeline-run]] — first CPU-class IP
  driven end-to-end through `ssot-gen → fl-model-gen → rtl-gen → tb-gen →
  sim → lint` with green compile/lint/sim/coverage on the headless
  surface (`gpt-5.3-codex`, `/mode pipeline`). 8 SV files (22 KB),
  scoreboard 37/37 with 0 mismatches, 35/35 fcov bins hit, lint clean.
  Detailed report at `arm_m0_min/PIPELINE_SUMMARY.md`. Open ledger
  items (8) classified as: 1 self-counter, 3 out-of-plan-scope
  (cl-model-gen / formal / production governance), 4 derive-tool
  false positives (same family as the uart_lite trial's "30 owner-file
  mismatches as tool bug"). Three workflow improvement candidates
  surfaced:
  1. `repair_ssot_schema.py` should normalize C/Verilog ternary and
     bit literals (`cond ? a : b`, `32'h0`, `1'b1`) inside `expr`
     strings — `emit_fl_model.py` crashes on these with SyntaxError.
  2. `rtl-gen` system prompt should require
     `rtl/rtl_authoring_provenance.json` emission as a closing artifact
     (schema: agent, workflow, surface, model_profile, ssot,
     rtl_files, todo_plan, todo_plan_sha256, toolchain).
  3. `react_loop` should stop on idle once the agent declares done,
     not run out the iteration cap doing nothing — ~50 min of the
     ~3 h wall-time on this run was post-completion idle.
- Updated [[rtl-version-run-history]] with the arm_m0_min row.
- New wiki page [[deterministic-emit-stages]] documents why fl-model-gen / cl-model-gen run with 0 LLM calls, what SSOT contract this places on the upstream ssot-gen LLM, and what failure modes (`SyntaxError`, helper unknown, etc.) mean for ownership. Also captures the cl-model-gen entry point: `/ssot-cycle-model <ip>` lives inside the `fl-model-gen` workspace (no separate `workflow/cl-model-gen/` directory).
- New wiki page [[karpathy-llm-wiki-pattern]] captures Andrej Karpathy's LLM Wiki concept (3-layer markdown architecture, frontmatter schema, ingest/query/lint/log operations, no RAG / no vector DB) and the gap analysis against the current `doc/wiki/`. Frontmatter rollout and lint extension are parked as follow-ups; the discussion itself is now searchable.
- New script `workflow/wiki/build_graph.py` emits `doc/wiki/_graph.json` (schema `wiki_graph.v1`) by parsing every wiki `.md`, optional YAML frontmatter, and `[[refs]]`. Initial index: nodes=15, edges=58, broken_refs=0. `--check` exits non-zero on broken refs so CI/lint can catch dangling wiki links.
- Per-IP knowledge graph + chat tool landed: `workflow/wiki/build_graph.py --ip <name>` emits `<ip>/wiki/_graph.json` (schema `ip_wiki_graph.v1`) with 10–11 synthetic artifact nodes (`ssot`, `fl_model`, `cl_model`, `rtl`, `filelist`, `lint`, `tb`, `sim`, `coverage`, `audit`, `last_run`) sourced from the canonical IP layout. `/new-ip` now scaffolds `<ip>/wiki/{index,log,notes}.md`. `core/tools.wiki_query(ip, topic, depth)` is registered in `AVAILABLE_TOOLS` so Global Chat and IP Chat agents can read the graph without grep gymnastics. `src/headless_workflow._finish()` calls `_refresh_ip_wiki_graph(ip)` so the per-IP graph stays current after every run. arm_m0_min initial graph: 10 nodes, 14 edges, 0 broken refs. 38/38 e2e checks pass.
- New page [[wiki-curation-policy]] codifies *what* belongs in the wiki and *when* to write it. Five high-signal triggers (decision-not-in-code, pattern-repeated-across-IPs, policy-not-fix, external reference, IP-handover); four no-write rules (anything already encoded in workflow source, single-shot debug traces, system-prompt rules, wishful "would be nice"); four trigger moments (surprise, commit-not-self-explaining, IP handover/completion, new-IP start with `wiki_query` lookup); four-step promotion ladder (`log line → consolidated paragraph → dedicated page → cross-IP rollup`). "Cite, don't embed" rule for large evidence (LLM trace, scoreboard JSON, DB row stays in source; wiki page only cites the locator). Policy lives next to the code so it evolves in place; revisions edit the page in the same commit.
- Addressed the three workflow improvement candidates surfaced by the arm_m0_min run:
  1. Confirmed `repair_ssot_schema.py` already normalizes C ternary (`cond ? a : b` → `(a if cond else b)`), full Verilog bit literals (`32'h0`, `1'b1`, `8'hff`), and SystemVerilog unsized fills (`'0`, `'1`, `'x`, `'z`) inside `expr` strings. Verified with a regression matrix; no further patch needed.
  2. `workflow/rtl-gen/system_prompt.md` now states the provenance JSON schema explicitly and tells the LLM rtl-gen agent NOT to write `rtl/rtl_authoring_provenance.json` directly — the engine (`src/headless_workflow.py`, `workflow/rtl-gen/scripts/ssot_to_rtl.py`) already auto-emits it at end of every rtl-gen run.
  3. `lib/iteration_control.detect_completion_signal` now recognizes narrative-end phrases ("pipeline complete", "all tasks finished", "everything is done", "nothing more to do", "✓ loop ended", "all workflows complete", "all stages passed", "run finished", …) in addition to the strict sentinel tokens. The react_loop's existing completion path at `core/react_loop.py:1266` now exits on the same plain-English declarations the LLM emitted on the arm_m0_min run, removing the ~50 min post-completion idle.

## 2026-05-15

- Created the tracked project wiki map for common_ai_agent under `doc/wiki/`.
- Added cross-linked pages for flow, ownership, todo evidence, provider call accounting, and human escalation.
- Captured the no-direct-generated-artifact-edit rule for pipeline tests.
- Pipeline smoke test (`gray_counter`, gpt-5.3-codex) under `_runspaces/test_pipeline_gpt53/`:
  - PASS: ssot-gen, fl-model-gen (after helper fix), cl-model-gen, dual-fcov, equiv-goals.
  - FAIL: rtl-gen audit. compile/lint clean, but `GC_TXN_ADVANCE.outputs.output_0` missed `bin`/`bin_state` static evidence (RTL-0062). owner = `rtl-gen` repair, no manual patch.
- Workflow source fix in `workflow/fl-model-gen/scripts/emit_fl_model.py`: registered canonical bit helpers (`gray_to_bin`, `bin_to_gray`, `popcount`, `parity`, `clog2`, `min`, `max`, `abs`) in the rule env and in `known_names`, so SSOT expressions may reference them without `run_self_check` shadowing the callable with a stub integer.
- Workflow source fix in `workflow/tb-gen/runtime/equivalence_scoreboard.py`: `_seed_rule_fields` now pulls helper names from the generated `FunctionalModel._default_rule_helpers()` and adds them to `known`, so the scoreboard does not stub callable helpers as integer stimulus fields.
- Pipeline smoke test continued — rtl-gen repair iteration passed, but sim FL-vs-RTL produced 11 SOFT_EQ_MISMATCH cases. Initial sim-debug classification attributed all 11 to `rtl-gen`.
- Workflow source fix in `workflow/sim_debug/scripts/compare_fl_rtl_results.py`: added a stimulus-vs-transaction-kind consistency check (`_stimulus_contract_violation`) that resolves to `tb-gen` when the TB drives control signals inconsistent with the named transaction kind (e.g., kind=`synchronous_clear` but `clear=0` and `enable=1`). After the patch the classification became 9 `tb-gen` / 2 `rtl-gen`, matching the true root cause: the deterministic TB stimulus generator does not encode transaction-kind preconditions.
- Confirmed limitation worth recording: `workflow/tb-gen/scripts/emit_goal_scoreboard_cocotb.py` is a deterministic generator (not an LLM), so re-running tb-gen reproduces the same stimulus pattern. The proper repair is to teach the generator (or its prompt for LLM-generated sequences) to honor transaction preconditions when driving control signals.
- Q&A history scope fix: an `mctp_assembler` grill-me session showed old GPIO entries in the UI even though `.session/2076604/mctp_assembler/ssot-gen/qa.json` did not contain GPIO. The backend QA board was scoped correctly; the browser ask_user history migration accepted legacy localStorage entries with no `session`/`ip` metadata. `workspace.jsx` now rejects scope-less legacy history when a real session/IP is active. Verified with `tests/test_atlas_qa_history_scope.py` and `tests/test_atlas_multiuser_session_scope.py` (`12 passed`).
- gpio pipeline smoke test (gpt-5.3-codex): ssot-gen / fl-model-gen / cl-model-gen / dual-fcov passed; equiv-goals blocked (sub_module `gpio_input_sampler` had no function_model_refs); rtl-gen returned `human_gate` from preflight (cyclic output dependency on `din_q_masked_next`, sample_condition not in DSL).
- Workflow source fix in `workflow/ssot-gen/scripts/repair_ssot_schema.py`: normalize SystemVerilog unsized fill literals (`'0` → `0`, `'1` → `1`, `'x`/`'z` → `0`) in rule expressions so the FL evaluator does not hit `EOL while scanning string literal`.
- Downstream readiness validator added to `repair_ssot_schema.py`: detects (a) cyclic same-cycle output_rule dependencies per transaction, (b) `sample_condition` strings that are not DSL-parseable, (c) `sub_modules[]` entries with no ownership refs. Writes `<ip>/req/ssot_downstream_blockers.json` after canonicalization; `--strict-downstream` makes the script exit non-zero so the ssot-gen stage gates instead of pushing the problem to fl/cl/equiv/rtl.
- `workflow/ssot-gen/system_prompt.md` now has a "DOWNSTREAM READINESS" section that tells the ssot-gen LLM the DSL rules, the no-output-cycle rule, the SV fill literal rule, the sub_module ownership refs rule, and the helper reserved names. Goal: catch the same gaps during authoring instead of waiting for rtl-gen preflight.
- SSOT Q&A Workbench UI contract added: `ssot-gen` now starts on Q&A Session, hides the old QA history panel, uses the full center card for ask_user, exposes Import / Deep Interview(`/grill-me`) / To SSOT(`/to-ssot`) buttons, and shows remaining SSOT requirement decisions. Verified by targeted pytest and ATLAS browser smoke.
- RTL-GEN split-workspace guidance fix: `rtl-gen` now treats `workflow/` as source-repo tooling under `ATLAS_SOURCE_ROOT`, not as an IP-workspace artifact that must exist in CWD. This prevents UI ask_user cards that ask the user to mount/copy `workflow/rtl-gen/scripts/derive_rtl_todos.py` when the source root is already injected.
- Parallel TODO worker dispatcher landed: `core/parallel_todo_dispatcher.py` + `parallel_todo_dispatch` tool in `core/tools.py`. The main agent can hand a TODO batch to `parallel_todo_dispatch(todos=[...], max_workers=3, models=None)` and the dispatcher fans the chunk out to N background sub-agent workers, each in clean ReAct mode with its own provider (auto-picks from `cursor-cli` / `claude-cli` / `gpt-5.3-codex` / `glm-5.1` / `deepseek-v4-pro` / `kimi-*` by available credentials and cheapest cost). Worker artefacts land under `.workers/ptd_<id>/`; aggregated `wait()` returns `completed` / `partial` / `partial_error` / `timeout`. Phase 1 ships clean+prompt only; `fork=True` is reserved for Phase 2. See [[parallel-todo-sub-agent-workers]].
- Companion R2 cosmetic in `frontend/atlas/workspace.jsx`: agent's `todo_update` / `todo_note` / `todo_write` calls render in the chat tool cards as `step_update` / `step_note` / `step_write` so users do not conflate agent session working-memory indexes (`#2`, `#3`) with the workflow tracker's stable `RTL-XXXX` IDs that still surface in the right-side TODO panel.
- Deep test sweep (32/32) on the dispatcher: structural correctness, profile env snapshot/restore, round-robin determinism, timeout/error handling, 1000-UUID uniqueness, 10-thread concurrent dispatch contention, 1 MiB worker return value, mixed valid/empty/None TODO inputs, JSON round-trip of the aggregated wait() output. Lives at `_runspaces/dispatcher_deep_test.py`. Real end-to-end across 6 providers (`claude-cli`, `cursor-cli`, `gpt-5.3-codex`, `glm-5.1`, `kimi-2.6`, `deepseek-v4-pro`) — all returned the requested word with their own tool use; dispatcher wall-time = the slowest worker.
- Two bugs uncovered + fixed during the real end-to-end. (1) `_thread_runtime` was a `threading.local()` — `ThreadPoolExecutor` worker threads start with empty locals, so `scoped_model_runtime("claude-cli")` never propagated `CLAUDE_CLI_ENABLE=True` into the inner LLM-call thread; replaced with a `contextvars.ContextVar`-backed proxy so the existing `_thread_runtime.stack` accessor still works. (2) `core/agent_runner.py:385` submits the LLM call to an inner `ThreadPoolExecutor` — Python does NOT auto-propagate ContextVar across that boundary, so the inner thread also has to be wrapped in `contextvars.copy_context().run(call_llm_raw, ...)`. After both fixes `claude-cli` / `cursor-cli` / `gpt-5.3-codex` honour their per-worker model runtime instead of falling back to the process-default profile.
- Granted Claude Code's built-in tools per dispatch: new `claude_tools="WebSearch,WebFetch"` and generic `extra_overrides={...}` arguments on `parallel_todo_dispatch`. Internally uses a new `config.scoped_runtime_extra(payload)` context manager that pushes an arbitrary dict (any `_THREAD_RUNTIME_KEYS` key) onto the thread-local stack for just this job's workers. The dispatcher also auto-flips `CLAUDE_CLI_PERMISSION_MODE="bypassPermissions"` when `claude_tools` is set so the headless worker doesn't stall on confirm-each-tool prompts. Verified: `claude-cli` worker with `claude_tools="WebSearch,WebFetch"` actually returned a live GitHub stars count (98.2k for tiangolo/fastapi) instead of the knowledge-cutoff refusal it produced without the grant.
- `core/tools_web.py` `web_search` / `web_fetch` got an `engine` argument with fallback chain (`auto` → firecrawl → claude-cli → cursor-cli). New `_search_via_claude_cli` / `_fetch_via_claude_cli` / `_search_via_cursor_cli` / `_fetch_via_cursor_cli` helpers call the CLIs directly (one-shot, not via the parallel dispatcher) with `permission_mode="bypassPermissions"` (claude) or `yolo=True` (cursor). Lets any agent run web search even without Firecrawl, and lets `glm` / `kimi` / `deepseek` agents reach the web indirectly through this tool dispatch (since their own backends do not have native browsing).
