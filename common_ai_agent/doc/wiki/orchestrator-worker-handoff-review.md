# Orchestrator Worker Handoff — Spec vs Shipped Audit (2026-05-16)

Review notes for [[orchestrator-worker-handoff]]. Captures the gap between
what the page declares as current behavior and what the codebase actually
implements, so the doc is not misread as "as-built". Each row of the gap
table doubles as a TODO for the orchestrator/gateway build-out.

Related: [[orchestrator-worker-handoff]] · [[workflow-feedback-and-scheduling]] ·
[[workflow-ownership-and-boundaries]]

## Verdict

The page is a clean control-plane design. Orchestrator-centered routing,
worker mode vs JSON fallback, multi-user lease isolation, and the
single-port gateway argument are all coherent. The risk is **tone**: most
sentences are declarative present tense ("the orchestrator must persist…",
"In Orchestrator Mode the Pipeline screen is the control plane") while the
codebase has none of the orchestrator/gateway/handoff-JSON layer yet. A
future reader will treat the page as documentation of shipped behavior.

The single most important fix is a status banner at the top distinguishing
spec from shipped.

## Response status

First pass applied:

- added the `Status: design spec, not shipped behavior` banner to
  [[orchestrator-worker-handoff]]
- relabeled `/api/pipeline/state` orchestrator fields as proposed target API
  additions
- removed the unsupported `ORCHESTRATOR_MODE=1` compatibility alias from the
  target contract
- clarified that single-port `/api/workers/<workflow>` routing is a future
  gateway shape while current shipped worker dispatch is root-route
  `WORKER_URL_*`
- marked `/take` and the `headless_workflow.py --stages take` shape as target
  behavior, not shipped CLI
- added `workspace_id` to isolation keys and handoff scope
- changed `last_heartbeat_at` examples to ISO-8601 UTC timestamps
- noted that `workflow_handoff.v1` is an intended schema name with schema file
  TBD
- reworded repeated repair failure so Review Decision Needed is the
  post-retry-budget blocker, not an immediate human gate
- narrowed the worker helper exception with a concrete `rtl-gen` local
  syntax/lint helper example

Third pass applied:

- updated [[orchestrator-worker-handoff]] from "design spec, not shipped" to
  "mixed as-built plus target design"
- added the shipped distinction for HTTP worker fanout via `WORKER_URL_*`
- captured the new integration tests that prove `/api/pipeline/dispatch`
  can complete the default 15-stage full-IP pipeline across two HTTP
  workers, and can start `rtl-gen` on one worker, poll `/status` +
  `/result`, then fan out `lint`, `tb-gen`, and `syn` to another worker
  while preserving `rtl_version_id` context
- added a real `core.agent_server.create_app()` worker-endpoint smoke with
  the LLM loop patched out, so the dispatch proof covers the production
  worker HTTP surface, not only a hand-written mock server

Second pass applied:

- renamed the durable run identifier to `pipeline_run_id` and flagged the
  collision risk with the existing in-memory `pipeline_id` in
  `src/atlas_api_jobs.py:144,427,747`; the future implementation must either
  rename the in-memory field or store the durable identifier in a new DB column
- inserted `workspace_id` into the ownership chain and into the worker lease
  scope line so the ASCII tree matches the isolation-keys list and the
  dispatch payload `scope` block
- moved the "current shipped behavior" disclaimer for worker ports to the top
  of the section so the reader meets shipped state before the target gateway
  shape
- changed "another workspace can run a `take` command" to "a workspace
  operator can run a `take` command"
- defined the `<owner>` placeholder in the Review Decision Needed filename as
  the failing workflow name (e.g. `rtl-gen`, `tb-gen`, `sim-debug`)
- added a note that offline workers omit `last_heartbeat_at`; the gateway
  treats absence as offline (kept outside the JSON code block so the example
  stays valid JSON)

Fourth pass applied (deep^6 adversarial test results, 134 tests):

- `/api/pipeline/state` cache key now `(ip, user_id)`; `_orchestrator_block`
  accepts `scope_filter` derived from the authenticated user. user_a polling
  the shared-IP endpoint no longer sees user_b's handoffs in `pending_handoffs`,
  `claimed_handoffs`, or `handoffs_by_workflow`. Surfaced by deep^6 round T41
  + permanent regression test
  `test_pipeline_state_isolates_handoffs_by_authenticated_user`.
- `ip` query parameter capped at 64 chars and `handoff_id` capped at 200 chars
  in their respective validators. Pre-fix, oversize inputs cascaded to a raw
  `OSError [Errno 63] File name too long` at downstream `stat()`. Surfaced by
  rounds T18 and T44 + regression tests
  `test_validate_rejects_overlong_handoff_id` and
  `test_pipeline_state_rejects_oversize_ip`.
- `_write_json` in both `src/handoff_queue.py` and `src/review_decisions.py`
  now uses per-thread unique `.tmp.{pid}.{tid}.{uuid}` suffixes. Two threads
  rewriting the same JSON file pre-fix raced on `os.replace` and the loser
  got `[Errno 2] No such file or directory`. Surfaced by round T26 +
  regression test `test_concurrent_writes_same_decision_no_rename_race`.
- `claim_next` now accepts `scope_filter=` and forwards it to
  `list_pending_for_workflow`. A multi-user CLI take cannot grab a record
  outside its scope even when that record sorts older. Surfaced by round T20
  + regression test `test_claim_next_respects_scope_filter`.
- New endpoint: `GET|POST /api/pipeline/orchestrator_mode` toggles
  `ATLAS_ORCHESTRATOR_MODE` at runtime; the POST handler clears `_state_cache`
  so each user's next poll reflects the new mode immediately. Pipeline run-bar
  chip is now a clickable button (`pipe-orch-chip-on` style) that calls this
  endpoint and dispatches `atlas:pipeline-poll` to force a fresh fetch.
- Performance baseline established on a single MacBook: 1549 writes/sec,
  `summary_by_workflow` on 5000 records in 386 ms, 500 random `get()` in 39 ms,
  4-thread `claim_next` of 500 records in 15 s. Cross-process atomicity
  verified by 4 concurrent subprocesses with no double-claims.

Fifth pass applied (StageCard action endpoints + buttons):

- Three new HTTP endpoints in `src/atlas_api_jobs.py`, all scope-filtered by
  the authenticated user:
  - `GET  /api/handoff/list?ip=&workflow=` returns the four state buckets
    (pending / claimed / done / review) filtered by workflow and scope.
  - `POST /api/handoff/save {ip, from_workflow, to_workflow, reason,
    goal_ids?, evidence?, suffix?}` writes a new pending handoff with
    `scope` auto-derived from the request user. Busts the `_state_cache`
    so the next poll reflects the new pending immediately.
  - `POST /api/handoff/take {ip, workflow}` calls `claim_next` with the
    user's `scope_filter`. Returns `{status: "claimed", handoff: {...}}`
    on success, `{status: "none_available"}` otherwise. `claimed_by` is
    stamped as `ui-<username>`.
- `/api/pipeline/state` per-stage payload now carries `workflow` and
  `handoffs: {pending, claimed, done, review, latest}`. The StageCard can
  render the `⇄ take N` button (and the orchestrator chips) without
  threading the full pipeline state down. Regression test
  `test_stage_carries_workflow_and_handoffs_count`.
- Frontend StageCard now renders two new action buttons (`pipeline.jsx`,
  styles in `styles.css` as `.pipe-stage-take` warn, `.pipe-stage-save`
  accent):
  - `⇄ take N` — visible when `info.handoffs.pending > 0`; POSTs to
    `/api/handoff/take` and fires the `atlas:pipeline-poll` event so the
    UI refreshes without waiting for the 2 s poll tick.
  - `📬 save handoff` — visible when stage state is `failed` AND
    `blame.owner_workflow` is present; POSTs to `/api/handoff/save` with
    the failing stage as `from_workflow` and the blame target as
    `to_workflow`.
- End-to-end verification on real example IPs (HTTP via `TestClient`):
  - `simple_gpio_lite`: 12-step flow (toggle ON → save sim-debug→rtl-gen
    handoff → list → take → review-decision → cross-user bob isolation →
    toggle OFF). Every step's assertions passed; `bob` saw zero of
    `alice`'s handoffs and decisions.
  - `arm_m0_min`: 7-step flow with the coverage → tb-gen scenario
    (uncovered Thumb BL branch). Cross-IP isolation verified (the
    `arm_m0_min` claim did not leak into a `simple_gpio_lite` poll).

## Implementation gap table

Verified against `src/atlas_api_jobs.py`, `core/delegate_runner.py`,
`core/atlas_db.py`, `frontend/atlas/pipeline.jsx`, and
`src/headless_workflow.py` (2026-05-16).

| Doc claim | Status | Evidence |
|---|---|---|
| `ATLAS_ORCHESTRATOR_MODE=1` switch | **shipped (read-only)** | `_orchestrator_mode_enabled()` in `src/atlas_api_jobs.py`; flips `orchestrator.enabled` in `/api/pipeline/state` response and the run-bar chip |
| `ORCHESTRATOR_MODE=1` compat alias | **removed from target after review** | no current consumer; main page no longer advertises it |
| `ATLAS_WORKER_GATEWAY_MODE=1` | **doc-only** | not referenced |
| Path-prefix gateway `localhost:8000/api/workers/<workflow>` | **not built** | code still uses `WORKER_URL_<WF>` to a full URL (`delegate_runner.py:212`, `atlas_api_jobs.py:562`); default is `localhost:8001`, single endpoint, no `/api/workers/` route |
| `<ip>/handoff/{pending,claimed,done,review,suggested}/*.json` layout | **shipped** | `src/handoff_queue.py` (`write_suggested`, `write_pending`, `promote_to_pending`, `claim`, `release_claim`, `complete`, `move_to_review`) + 28 tests in `tests/test_handoff_queue.py` (was 13 at time of 4th-pass review, grew through subsequent passes) |
| `/take <ip> --workflow rtl-gen` and `headless_workflow.py --stages take` | **shipped (CLI)** | `_run_take()` in `src/headless_workflow.py`; `--stages take --workflow <wf>` claims FIFO, runs the owner workflow, completes on pass or releases the claim on fail/error; 6 tests in `tests/test_headless_workflow_take.py` |
| `<ip>/review/decision_needed_pipeline_repeated_<owner>_mismatch.json` writer | **shipped** | `src/review_decisions.py` (`write_repeated_mismatch_decision`, `resolve_decision`, `list_open_decisions`); 19 tests in `tests/test_review_decisions.py` (was 8 at time of 4th-pass review, grew through subsequent passes) |
| `/api/pipeline/state` returns `orchestrator{…}`, `handoffs_by_workflow{…}` | **shipped** | `_orchestrator_block()` in `src/atlas_api_jobs.py`; reads handoff queue and review records from disk regardless of env flag, only `enabled`/`mode` toggles with `ATLAS_ORCHESTRATOR_MODE`; 4 new tests in `tests/test_atlas_api_pipeline_state.py` |
| `/api/pipeline/state` is multi-user scoped (cache key + scope filter) | **shipped (4th pass)** | cache key `(ip, user_id)`; `_orchestrator_block(scope_filter=…)` derived from `request.scope["user"]`; regression test `test_pipeline_state_isolates_handoffs_by_authenticated_user` |
| `GET|POST /api/pipeline/orchestrator_mode` runtime toggle | **shipped (4th pass)** | mutates `ATLAS_ORCHESTRATOR_MODE` env, clears `_state_cache`; 401 anonymous, 200 authenticated; 4 tests in `tests/test_atlas_api_pipeline_state.py` |
| Length / injection hardening on `ip` and `handoff_id` | **shipped (4th pass)** | 64-char `ip` cap; 200-char `handoff_id` cap; both reject before reaching the FS; regression tests `test_pipeline_state_rejects_oversize_ip` + `test_validate_rejects_overlong_handoff_id` |
| Atomic concurrent rewrites of the same JSON file | **shipped (4th pass)** | per-thread unique `.tmp` suffix in `_write_json` (handoff_queue) and `_atomic_write_json` (review_decisions); regression test `test_concurrent_writes_same_decision_no_rename_race` |
| `claim_next` respects `scope_filter` | **shipped (4th pass)** | new kwarg threaded through `list_pending_for_workflow`; regression test `test_claim_next_respects_scope_filter` |
| `GET /api/handoff/list?ip=&workflow=` user-scoped 4-bucket view | **shipped (5th pass)** | `api_handoff_list()` in `src/atlas_api_jobs.py`; regression test `test_handoff_list_returns_pending_for_user`; verified end-to-end on `simple_gpio_lite` and `arm_m0_min` |
| `POST /api/handoff/save` writes pending + busts cache | **shipped (5th pass)** | `api_handoff_save()`; scope auto-derived from auth; regression tests `test_handoff_save_writes_pending_and_busts_cache`, `test_handoff_save_rejects_missing_fields` |
| `POST /api/handoff/take` atomic scoped claim from UI | **shipped (5th pass)** | `api_handoff_take()` calls `claim_next` with user scope; regression test `test_handoff_take_claims_oldest_pending` |
| Per-stage `workflow` + `handoffs` in `/api/pipeline/state` payload | **shipped (5th pass)** | populated by single `_orchestrator_block()` call hoisted above the stage loop; regression test `test_stage_carries_workflow_and_handoffs_count` |
| StageCard `⇄ take N` and `📬 save handoff` action buttons | **shipped (5th pass)** | `frontend/atlas/pipeline.jsx` StageCard renders both conditionally; `.pipe-stage-take` (warn) and `.pipe-stage-save` (accent) styles in `styles.css`; click handlers POST to the new endpoints and fire `atlas:pipeline-poll` for immediate refresh |
| End-to-end UX proven on real example IPs | **shipped + e2e** | `/tmp/full_e2e_with_ip.py` (`simple_gpio_lite`, 12 steps) + `/tmp/e2e_arm_m0_min.py` (`arm_m0_min`, 7 steps with cross-IP isolation check) |
| `/api/pipeline/dispatch` can complete the default 15-stage full-IP pipeline and fan out downstream stages to a different HTTP worker | **shipped + integration-tested** | `tests/test_pipeline_orchestrator_worker_integration.py` starts two mock workers, dispatches the default full pipeline with `schedule=auto`, verifies all 15 stages complete, then separately dispatches `rtl -> {lint,tb,syn}` and verifies DAG scheduling, `/run` payloads, `/status`/`/result` polling, and downstream `rtl_version_id` context |
| `/api/pipeline/dispatch` can talk to the real agent-server worker HTTP surface | **shipped + integration-tested** | `tests/test_pipeline_orchestrator_worker_integration.py` starts two `core.agent_server.create_app()` uvicorn workers with only the LLM loop patched out, dispatches `rtl -> lint`, polls `/api/jobs`, and verifies the lint worker receives `rtl_version_id`, session, context, and project-root payload |
| Worker capacity metadata (`capacity_group`, `slots_total`, `slots_available`, `last_heartbeat_at`) | **not built** | no DB column, no API field, no in-memory registry — the `workers: {}` field in the orchestrator block is intentionally empty until a gateway lands |
| Worker lease isolation (`lease_id`, `worker_id` per user) | **not built** | no lease table in `core/atlas_db.py` |
| `pipeline.jsx` 2 s poll of `/api/pipeline/state` | **shipped** | `frontend/atlas/pipeline.jsx:647,661` |
| `pipeline.jsx` dispatch via `/api/pipeline/dispatch` | **shipped** | `frontend/atlas/pipeline.jsx:304,335,476` |
| Run-bar chips for orchestrator mode / pending handoffs / review-decisions | **shipped** | new `.pipe-orch-chip`, `.pipe-handoff-chip`, `.pipe-review-chip` rendered alongside the running chip in `pipeline.jsx`; styles in `styles.css` |
| Wiki cross-links (`full-flow-pipeline`, `workflow-feedback-and-scheduling`, `workflow-ownership-and-boundaries`, `rtl-version-run-history`, `human-review-and-escalation`) | **valid** | all 5 targets exist in `doc/wiki/` |

## Concrete fixes for `orchestrator-worker-handoff.md`

1. **Status banner at the top** (after line 4):

   ```markdown
   > Status: design spec. The orchestrator/gateway/handoff-JSON layer
   > described below is not yet implemented in `src/` — see
   > `.omx/plans/prd-orchestrator-worker-handoff.md` for the build plan.
   > Currently shipped: `/api/pipeline/state`, `/api/pipeline/dispatch`,
   > `WORKER_URL_*` single-endpoint dispatch (no gateway, no lease, no
   > JSON handoff queue). Treat declarative sentences here as target
   > behavior.
   ```

2. **Port mismatch (lines 197–205).** The doc shows
   `localhost:8000/api/workers/<workflow>`, but `WORKER_URL_DEFAULT`
   resolves to `localhost:8001` and workers serve `/run` at root. Either
   note that the section describes a future gateway shape, or unify the
   port with `atlas_api_jobs.py:566` and `delegate_runner.py:216`.

3. **UI contract JSON (lines 466–512)** describes a payload
   `/api/pipeline/state` does not return today. Pick one: ship the empty
   shape now (`"orchestrator": null, "handoffs_by_workflow": {}`), gate it
   behind `ATLAS_ORCHESTRATOR_MODE`, or relabel the block "proposed".

4. **Workspace `/take` bullets (lines 569–572)** describe a command that
   doesn't exist. Either remove until implemented or mark "(not yet
   implemented)".

5. **Top-bar `decisions K needed` (line 521)** has no backing field. Same
   resolution as #3.

6. **"Compatibility alias `ORCHESTRATOR_MODE=1`" (line 27)** was a
   forward-compat slot for nothing in-tree. Applied response: dropped from the
   main target contract.

## Smaller nits

- **Line 173** mixes transport, delivery model, and endpoint shape in one
  list. Suggest:
  - in-process Python call (direct invocation)
  - subprocess CLI (`headless_workflow.py`)
  - remote worker URL (HTTP, via `WORKER_URL_*`)
  - cmux session (interactive shell, manual `/take`)
- **Line 393** `python3 src/headless_workflow.py … --stages take --workflow rtl-gen` —
  verify CLI arg shape before publishing; current `--stages` is positional.
- **Lines 277–285** isolation keys are missing `workspace_id` even though
  `core/atlas_db.py` is workspace-scoped. Add it, or explain why
  `pipeline_id` subsumes it.
- **Lines 240 / 487** `last_heartbeat_at: "UTC"` — clarify this is an
  ISO-8601 timestamp; the placeholder reads like a tz name.
- **Line 332** `schema: "workflow_handoff.v1"` — add a one-line pointer to
  the schema file once it exists, or note "schema TBD".
- **Line 416 vs 433** tension: "Repeated repair failure is not a human
  gate by default" reads as contradicting "Review Decision Needed is a
  signoff blocker". Reword the first to: "Repeated repair failure does
  not immediately escalate; the orchestrator retries within budget and
  writes Review Decision Needed when budget is exhausted."
- **Lines 76–78 "Allowed exception"** for worker→worker helper subtasks
  needs a concrete example, otherwise the loophole rationalizes any
  cross-call as a "local subtask".

## Out of scope for this review

- Whether worker-mode HTTP transport should be replaced (gRPC, NATS, …).
- DB schema changes to support `worker_leases` (covered in
  `.omx/plans/prd-orchestrator-worker-handoff.md`).
- Whether `~/.common_ai_agent/atlas.db` should become a shared service
  (the page itself defers this; consensus is per-user-machine for now).

## Bottom line

Keep the doc — the thinking is sound. The single highest-value edit is
the status banner so future readers do not conflate the spec with shipped
behavior. Everything else (port mismatch, JSON shape, missing CLI, nits)
is incremental polish on top.
