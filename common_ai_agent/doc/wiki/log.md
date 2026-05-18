# Wiki Log

## 2026-05-18

- Added [[atcdmac100-document-flow-ui-honesty-20260518]] as the corrective
  record for the Andes ATCDMAC100 PDF-based DMA run. It records the real
  artifacts and numbers produced by the backend/common-engine path
  (SSOT/models/RTL/lint/TB/sim/coverage/goal-audit/syn/STA), plus the process
  failure: the visible ATLAS tab was open, but most execution was not driven by
  right-side Orchestrator chat. The page marks the run as backend evidence, not
  UI product-flow proof, records STA setup fail at `hclk@10ns` with WNS
  `-22.560ns`, and records that PnR route was interrupted after the UI/process
  mismatch was challenged.
- Added [[atlas-browser-control-runbook]] so future agents can operate the
  visible ATLAS in-app Browser instead of substituting backend-only checks. The
  page records the exact Browser bootstrap, visible ATLAS URL open/reload,
  DOM/screenshot inspection, semantic button/chat input interaction, coordinate
  mouse move/click/type/scroll, and the PL330 signoff verification pattern where
  STA/PSTA had to be shown as failed from `wns.json` rather than passed by
  artifact existence. Extended the same runbook with the concrete synthesis
  path: dispatch `syn` via Orchestrator/Pipeline, run `/syn-auto <ip>`, verify
  `syn/out/synth.v`, `syn/out/syn.report.md`, `syn/out/area.json`, and surface
  cells/area/warnings in the browser/API. The PL330 synthesis evidence is
  `1321` cells, `16400.0 um2`, sky130 SS corner, no warnings. Follow-up:
  diagnosed why SYN looked absent in the browser: the frontend `Full IP
  pipeline` route stopped at `goal-audit` while the backend canonical pipeline
  already included `syn`, `sta`, `pnr`, and `sta-post`. The full route now
  matches the backend 15-stage order; the focused `PPA signoff` route remains
  for RTL → SYN → STA → PNR → PSTA. Recorded the concrete PL330 STA/PNR/PSTA
  evidence and generated SDC path.
- Added [[atlas-pipeline-worker-workspace-jump]] to document the real UI
  workflow drilldown behavior: clicking `ssot-gen`, `rtl-gen`, or `tb-gen` in
  the Pipeline worker row opens `.session/<session>/<ip>/<workflow>` in
  Workspace, shows worker chat history, and previews the representative SSOT,
  RTL authoring status, or cocotb TB file. Cross-linked it from
  [[atlas-pipeline-screen]] and
  [[pl330-real-orchestrator-ui-lessons-20260517]] so future UI work preserves
  the Orchestrator-first product boundary while keeping worker evidence
  inspectable.

## 2026-05-17

- New page [[pl330-real-orchestrator-ui-lessons-20260517]] captures the visible
  ATLAS UI PL330 lessons from `pl330realverify`: Browser/API/worker evidence is
  product authority, user should talk only to Orchestrator chat, RTL handoff is
  `/ssot-rtl <ip>` instead of a preloaded TODO payload, active job dedupe fixes
  duplicate loading dispatches, and the `TB failed` card in this run came from
  an accidental operator dispatch/cancel rather than real TB evidence.
- Added `doc/wiki/atcwdt200-pipeline-run-20260517.md` for the Andes watchdog
  timer flow started from `/Users/brian/Desktop/andes/atcwdt200`. The snapshot
  records clean SSOT/FL/CL/equiv/RTL/TB/lint evidence, the current sim stop
  condition (`TESTS=1 PASS=1` plus `[SIM ESCALATE] scoreboard_failed=11`), and
  recurring lessons around generated `rtl_contract.json`, comment-stripped RTL
  audit evidence, fixed-version-register FL rules, and internal-state
  observability before repair.
- Added `arm_m0_min/review/prompt_to_artifact_checklist.json`, a
  machine-readable map from the original CPU request to concrete SSOT, model,
  RTL, TB, sim, equivalence, coverage, wiki, and approval-gate evidence. The
  open req review decision now exposes this JSON as a `review_aids[]` entry so
  UI/orchestrator/future agents can distinguish machine-green evidence from the
  remaining human-owned `req` blocker without parsing prose.
- Added `workflow/req-gen/scripts/audit_prompt_to_artifact_checklist.py` as a
  consistency checker for that JSON map. On real `arm_m0_min` it reports
  `status=blocked`, `completion_ready=false`, no errors, and blocked items
  `human_req_approval` plus `final_audit`, which keeps the approval boundary
  machine-checkable without promoting `req/`.
- Added `doc/wiki/arm-m0-min-current-status.md` as the project-level discovery
  page for the active CPU handoff. Before this, project-level `wiki_query`
  found only `doc/wiki/log.md` for `"cpu approval req"` and returned no direct
  result for `"arm m0 handoff"` or `"readme cpu"`, even though the IP-local
  wiki was already good. The new page keeps the same approval boundary:
  `arm_m0_min/README.md` is the reviewer entry point, real final audit remains
  `15/16 blockers=req`, and `approve_locked_scope` is required before
  `workflow/req-gen/scripts/promote_requirement_review.py` may write real
  `arm_m0_min/req/` approval artifacts. The review decision's
  `evidence.review_aids[]` now includes this project wiki page so UI,
  orchestrator, and future agents land on the same current-status summary.
  Promotion preflight after the wiki/review-aid update passed in dry-run mode
  with review packet SHA256
  `e0b6e6a3d2078930bb046fd241a2422712af3155b4e823b2ec2da1bd64942a07`; no real
  `arm_m0_min/req/` artifacts were written. A live FastAPI test-client smoke
  against the real `arm_m0_min` workspace also confirmed
  `/api/pipeline/state?ip=arm_m0_min` reports one open review decision,
  recommended option `approve_locked_scope`, the then-current review aids
  including the project wiki current-status page, and `goal-audit` as
  `failed blockers=req`.
  Added
  `tests/test_atlas_api_pipeline_state.py::test_real_arm_m0_min_pipeline_state_exposes_req_review_decision`
  so this real-IP UI/API visibility cannot silently regress.
- Fresh CPU machine-evidence smoke after the API visibility test:
  `iverilog -g2012 -f list/arm_m0_min.f` compile passed, `verilator
  --lint-only -Wall -f list/arm_m0_min.f` passed with 0 errors/0 warnings,
  cocotb `test_runner.py` passed `TESTS=1 PASS=1 FAIL=0`,
  `compare_fl_rtl_results.py` passed `39/39`, and final goal audit remains
  blocked only on `req` (`15/16 blockers=req`). This confirms the new review
  docs/tests did not mask a stale CPU implementation failure. Because the
  compare file was freshly rewritten, the approval decision's pinned
  `fl_rtl_compare_sha256` needed to advance; the guard test caught the stale
  hash before approval could proceed. `compare_fl_rtl_results.py` now preserves
  `generated_at` when a rerun produces identical semantic evidence, so no-op
  reruns no longer churn approval hashes. The current stable compare SHA256 is
  `b7f758f1ecfd3a20ecab9472ec4f53834628fd9b9f1e057aa497a30a3319a062`.
- Fresh completion audit for the active "make one CPU" goal after process
  cleanup: `arm_m0_min/review/completion_readiness_checklist.md` already maps
  the user objective to concrete artifacts (SSOT, FL/CL models, RTL, filelist,
  TB, sim, scoreboard, FL-vs-RTL compare, coverage, requirement approval, final
  audit). Re-ran the real final audit:
  `python3 workflow/sim_debug/scripts/audit_fl_rtl_equivalence_goal.py arm_m0_min --root .`
  and it still reports `status=fail passed=15/16 blockers=req`. Re-ran the
  focused approval/audit/API regression set and it still passes `80 passed`.
  Therefore the CPU implementation evidence remains intact, but the thread goal
  is not complete until the human-owned locked-scope requirement approval is
  promoted into `arm_m0_min/req/`.
- Approval promotion preflight was rechecked without writing real `req/`
  artifacts:
  `python3 workflow/req-gen/scripts/promote_requirement_review.py arm_m0_min --root . --source arm_m0_min/doc/arm_m0_min_requirement_review.md --approved-by dry-run --decision-note 'preflight after completion audit refresh' --dry-run --json`
  passed and reported the expected review source hash
  `e0b6e6a3d2078930bb046fd241a2422712af3155b4e823b2ec2da1bd64942a07`.
  Note: `sim/fl_rtl_goal_audit.json` is runtime audit output and may update
  when the audit is rerun; the pinned promotion snapshot intentionally verifies
  `doc/arm_m0_min_completion_audit.md`, SSOT, FL-vs-RTL compare, and coverage.
- Added `arm_m0_min/doc/arm_m0_min_user_handoff.md` as a non-pinned usage and
  verification guide for the generated CPU. It lists the built scope, artifact
  locations, fresh audit/regression/preflight commands, and the approval
  boundary. `arm_m0_min/doc/arm_m0_min_review_index.md` now links it in the
  review order, and `arm_m0_min/PIPELINE_SUMMARY.md` now carries a current
  status note so readers do not mistake the historical run summary for the
  current `req` signoff state. Verified with `tests/test_review_decisions.py`
  (`15 passed`) and wiki graph checks (`broken_refs=0`).
- Exposed that handoff through the Pipeline review queue as a fifth
  `review_aids[]` entry, between the review index and deeper RTL/ISA
  inventories. Added a regression that the handoff keeps the approval boundary
  explicit (`do not manually create req`, real promotion only after
  `approve_locked_scope`). API/review-decision tests pass (`41 passed`), and
  requirement-promotion dry-run still verifies the pinned review packet hash
  without writing real `req/` artifacts. The full focused
  approval/audit/API regression set now passes `81 passed`; wiki graph checks
  remain clean (`broken_refs=0`).
- Added IP-local wiki pages under `arm_m0_min/wiki/` (`index.md`, `log.md`,
  `notes.md`) so the CPU review can start from the IP directory itself. The
  index links to the handoff, approval request, readiness checklist, review
  index, and key machine artifacts, while explicitly preserving the same `req`
  approval boundary.
- Improved `core.tools.wiki_query` keyword matching for agents: queries now
  split topic terms and match them against id, title, tags, path, status,
  digest, and summary instead of requiring one exact substring in id/title/tags.
  Added `tests/test_wiki_query_tool.py` so questions like "CPU handoff approval
  req" find the IP-local handoff/review pages. Also adjusted the
  `arm_m0_min/wiki/index.md` title/summary so `wiki_query(ip="arm_m0_min",
  topic="CPU handoff")` returns a useful result.
- Added a real-IP `wiki_query` regression for `arm_m0_min` itself. The test
  rebuilds `arm_m0_min/wiki/_graph.json`, calls the same `wiki_query` tool path
  an agent would use, and verifies that topic `"CPU handoff approval req"`
  returns the IP-local wiki index, `approve_locked_scope`, and the final-signoff
  blocker wording. The focused approval/audit/API/wiki-query regression set now
  passes `84 passed`; project and IP wiki graph checks remain `broken_refs=0`.
- Added a Korean review checklist to `arm_m0_min/doc/arm_m0_min_user_handoff.md`
  so the approval decision is understandable without reading the whole English
  artifact set. The checklist says this is a minimal reference CPU, lists the
  approved ISA/pipeline/excluded features, and states the two outcomes:
  answer `approve_locked_scope` if the scope is correct, or reopen SSOT scope if
  it is insufficient.
- Added `arm_m0_min/README.md` as the root-level CPU entry point. It links to
  the handoff, approval request, completion checklist, IP wiki index, review
  index, and main artifacts, while making the current gate explicit
  (`15/16 blockers=req`) and preserving the rule that `req/` artifacts are not
  manually created before `approve_locked_scope`.
- Fixed `wiki_query` lazy rebuild so wiki lookup does not serve stale
  `_graph.json` after markdown content changes. The tool now checks file mtimes
  under IP `wiki/` plus artifact directories, and project wiki markdown mtimes,
  instead of only checking a few IP artifact directory mtimes. Added a
  regression that edits an existing IP wiki markdown file, leaves a stale graph,
  and verifies `wiki_query` rebuilds before answering. Focused
  approval/audit/API/wiki-query regression now passes `86 passed`.
- Linked the new root `arm_m0_min/README.md` from `arm_m0_min/wiki/index.md`
  and added a real-IP `wiki_query` regression for topic `"readme cpu"`. This
  keeps the root entry point discoverable from the wiki/tool path instead of
  requiring the reviewer to know it exists. After tightening the wiki index
  title/summary, `wiki_query(ip="arm_m0_min", topic="readme cpu")` returns the
  CPU README handoff index and names `arm_m0_min/README.md` as the root README
  entry point. Focused approval/audit/API/wiki-query regression now passes
  `87 passed`.
- Improved `wiki_query` result ordering so reviewer entry points appear before
  logs/notes for the same topic. The scorer weights matches in id/title/path
  above summary-only matches and gives `wiki/index.md` a start-page boost.
  Real-IP regression now asserts `wiki_query(ip="arm_m0_min", topic="CPU handoff approval req")`
  returns the IP wiki index before the log. The focused regression remains
  `87 passed`.
- Cleaned stale Claude/worker monitor shells that were only polling with
  `until grep ... sleep` and causing repeated unified exec pressure warnings.
  The cleanup intentionally did not kill user-facing Claude sessions, `cmux`,
  or the active Textual UI process. Follow-up process scan showed zero
  remaining `until grep` monitors; one user-facing
  `textual_main.py --ui textual -s test_ip` process was left running.
- Checked the concurrent `octa_ddr_spi_ctrl` workflow run under
  `/Users/brian/Desktop/Project/OCTA_DDR_SPI_ORCH_20260517_001`: the run reached
  generated model/TB stages and ended with evidence, not a process hang.
  Current failure is `sim-debug` FL-vs-RTL mismatch: 67 goals checked, 43 pass,
  24 fail, 0 blocked. Owner classification is 18 `rtl-gen` repairs and 6
  `tb-gen` repairs. This should feed the repair loop; it should not be treated
  as a human gate or as a manual artifact edit request.
- Continuation audit for `arm_m0_min` after compaction: real final audit still
  fails only on the human-owned `req` gate (`15/16 blockers=req`). Focused
  approval/audit/API regression remains green (`75 passed`), wiki graphs remain
  clean (`doc/wiki` 33 nodes/192 edges/0 broken refs, `arm_m0_min/wiki` 11
  nodes/14 edges/0 broken refs), and promotion on a temporary copy still
  reaches `16/16 blockers=none`. Real `arm_m0_min/req/arm_m0_min_requirements.md`
  and `arm_m0_min/req/approval_manifest.json` were intentionally not written;
  the stop condition remains explicit human approval of
  `arm_m0_min/review/approval_request.md` with `approve_locked_scope`.
- Added `arm_m0_min/review/completion_readiness_checklist.md` as a review aid
  that maps the original "make a CPU" request to concrete artifacts, current
  evidence, and the single remaining blocker. It is linked from the human
  approval request and from the open review decision's `evidence.review_aids[]`.
  It is intentionally not part of the pinned approval target, so adding it does
  not mutate the reviewed requirement packet hash. Revalidation after the link:
  JSON valid, approval dry-run passes hash preflight, focused regression remains
  `75 passed`, and the real audit still fails only as expected at
  `15/16 blockers=req`.
- Strengthened the Pipeline API regression for that review queue shape:
  `tests/test_atlas_api_pipeline_state.py` now locks a four-aid list with the
  readiness checklist first, matching the real `arm_m0_min` decision record.
  Direct review queue inspection returns the same four aids, the API test file
  passes (`25 passed`), and the focused approval/audit/API set remains
  `75 passed`.
- Added a real-artifact review decision regression in
  `tests/test_review_decisions.py`: the `arm_m0_min` requirement approval
  record must list the four expected review aids in order, and each path must
  exist on disk. This prevents Pipeline from surfacing stale or missing review
  links while the human `req` gate is open. Review-decision tests pass
  (`12 passed`), and the focused approval/audit/API set now passes
  `76 passed`; real final audit is still intentionally blocked at
  `15/16 blockers=req`.
- Added another real-artifact regression for the same approval decision: the
  pinned approval packet hash and machine evidence snapshot hashes must match
  the current files on disk (`requirement_review.md`, completion audit, SSOT,
  FL-vs-RTL compare, and coverage). This prevents approving a review decision
  whose evidence has drifted. Review-decision tests now pass `13 passed`, and
  the focused approval/audit/API set passes `77 passed`; approval dry-run still
  passes hash preflight and the real audit remains `15/16 blockers=req`.
- Added a readiness-checklist consistency regression: while the
  `arm_m0_min` requirement decision remains open, the checklist must say it is
  not complete, must mirror the real final-audit count/blocker
  (`passed=15/16`, `blockers=req`), must include `approve_locked_scope`, and
  must not coexist with real `req/arm_m0_min_requirements.md` or
  `req/approval_manifest.json`. The test skips automatically after the review
  decision is resolved, so it protects the pre-approval state without blocking
  post-approval completion. Review-decision tests now pass `14 passed`, and the
  focused approval/audit/API set passes `78 passed`; approval dry-run still
  passes and the real audit remains `15/16 blockers=req`.
- Added a temp-copy completion regression:
  `tests/test_goal_audit_requirement_review.py` copies the actual
  `arm_m0_min` artifact to a temporary directory, runs
  `promote_requirement_review.promote(...)` there with a real approver name,
  and then calls the final audit function. The temp copy reaches
  `16/16 blockers=[]`, while the real repo remains unpromoted
  (`req/arm_m0_min_requirements.md` and `req/approval_manifest.json` absent).
  Goal-audit requirement tests pass `6 passed`; the focused
  approval/audit/API set now passes `79 passed`; approval dry-run still passes
  hash preflight and the real audit remains `15/16 blockers=req`.
- Refreshed the human-facing approval docs after the regression count changed:
  `arm_m0_min/review/completion_readiness_checklist.md` now reports the focused
  set as `79 passed`, and `arm_m0_min/review/approval_request.md` explicitly
  lists both the focused regression and the temp-copy promotion regression.
  Revalidated the doc consistency path (`20 passed`) and the full focused
  approval/audit/API set (`79 passed`); real audit still remains
  `15/16 blockers=req`.
- Updated the review index to include
  `arm_m0_min/review/completion_readiness_checklist.md` in both review order
  and evidence locations, then added a regression that the human review index
  references every review aid listed in the open decision record. Review-decision
  tests now pass `15 passed`; the full focused approval/audit/API set passes
  `80 passed`, so the human-facing checklist and approval request were refreshed
  to report `80 passed`. Real audit remains `15/16 blockers=req`.
- Reduced future drift in the human-facing approval docs: the checklist and
  approval request now report the focused regression as "pass in latest
  verification" instead of hardcoding a pytest item count. The exact count is
  still available from the command output and wiki history, but approval-facing
  docs no longer need edits just because another guard test is added. Regression
  coverage was adjusted to require the pass wording and reject stale `80 passed`
  wording in the checklist. Current validation remains `21 passed` for the doc
  consistency path and `80 passed` for the focused approval/audit/API set; real
  audit remains `15/16 blockers=req`.
- Human review gate for `arm_m0_min` made user-visible without weakening
  signoff: `/api/pipeline/state` exposes `orchestrator.decision_items[]`,
  the Pipeline review chip opens `arm_m0_min/review/approval_request.md`,
  and that approval request now includes a Korean scope summary. The real
  final audit remains blocked at `15/16` until `approve_locked_scope` is
  explicitly promoted into `req/`.
- Added non-signoff review aids for the same gate:
  `arm_m0_min/doc/arm_m0_min_review_index.md`,
  `arm_m0_min/doc/arm_m0_min_rtl_inventory.md`, and
  `arm_m0_min/doc/arm_m0_min_isa_decode_inventory.md`. The review decision
  now carries these paths in `evidence.review_aids`, Pipeline shows them in the
  review-chip tooltip, and `tests/test_atlas_api_pipeline_state.py` locks that
  the API preserves them. Promotion dry-run still reaches final audit `16/16`;
  the real artifact remains intentionally blocked on `req`.
- Rechecked the `arm_m0_min` final gate after the review-aid update:
  the pinned approval target, completion audit, SSOT, FL-vs-RTL compare, and
  coverage hashes all match the review decision snapshot; RTL/list/TB/sim/
  scoreboard/coverage/audit artifacts are present; approval promotion still
  passes `16/16` on a temporary copy; focused approval/audit/review-queue
  regression is `75 passed`. The real artifact remains `15/16` until a human
  explicitly approves `arm_m0_min/review/approval_request.md`.
- Locked another approval-gate guardrail after noticing
  `arm_m0_min/req/phase1_ledger.log`: it is only a phase marker, not
  requirement evidence. `arm_m0_min/review/approval_request.md` and
  `arm_m0_min/doc/arm_m0_min_review_index.md` now say this explicitly, and
  `tests/test_goal_audit_requirement_review.py` verifies that a non-markdown
  phase marker under `req/` still leaves the final audit blocked on `req`.
- Added `promote_requirement_review.py --dry-run` so approval promotion can be
  preflighted against pinned review/evidence hashes without writing `req/`
  artifacts or resolving the open review decision. The real `arm_m0_min`
  preflight reports it would write `arm_m0_min/req/arm_m0_min_requirements.md`
  and resolve the review item, while the real final audit correctly remains
  `15/16 blockers=req`. The script now resolves relative `--source` paths
  against `--root`, so temp-root preflight and UI/orchestrator calls do not
  accidentally validate a source file from the caller's current directory.
  Dry-run stdout includes `approved_at_utc`, `source_sha256`, and
  `target_sha256`; the target hash is tied to the printed approval timestamp.
  `--json` emits the same dry-run manifest preview as parseable JSON for UI or
  orchestrator preflight without writing files. The dry-run manifest also
  carries `target_sha256_preview` and a note so callers do not mistake a
  preview hash tied to dry-run `approved_at_utc`, `approved_by`, and
  `decision_note` for the eventual real approval artifact hash. Non-dry-run
  `--json` is also tested in a temp workspace: it writes `req/`, resolves the
  review decision, and prints the same manifest JSON that lands on disk.
  Non-dry-run promotion now rejects placeholder approvers such as `dryrun` and
  requires a real human approver name; the CLI path is covered too, so
  `--approved-by dryrun` cannot accidentally create real `req/` artifacts.
  Placeholder variants with whitespace, hyphens, and underscores are normalized
  and rejected for real promotion while remaining allowed for `--dry-run`;
  punctuation-only variants such as `n/a` and `N.A.` are normalized too. The
  inverse dry-run allowance is also tested so preflight remains ergonomic.
- Re-ran a real approval promotion on a temporary copy after the dry-run/json
  and approver-guard changes. With `--approved-by brian --json`, promotion
  wrote the approved `req/` artifact in the temp tree, resolved the review
  decision, and the temp final audit passed `16/16 blockers=none`. The real
  `arm_m0_min` artifact remains unpromoted and blocked at `15/16`.

- Captured [[run-mode-and-provenance-policy]] from the Run Mode / Exec Mode /
  SSOT provenance discussion. Decision: modes are work-maturity / evidence
  strictness (`Starter`, `Engineering`, `Signoff`), not IP-size buckets; execution
  topology is separate (`Single Worker`, `Orchestrator`). Accepted the feedback
  that inline provenance on every YAML field would worsen boilerplate, but
  refined it to `schema policy + resolved SSOT + sidecar provenance ledger`
  rather than validator-only hidden state. UI placement: global second row near
  `Workspace / Pipeline / Architect` for compact controls, Pipeline run bar for
  rich evidence (`defaults`, `review`, `signoff blocked`, workers/handoffs).

- Completed first `simple_pwm` end-to-end pipeline run. IP type:
  educational-tiny peripheral (PWM controller). Single module, 6 ports,
  3 function model transactions (FM1/FM2/FM3). Pipeline stages:
  ssot-gen → fl-model-gen → cl-model-gen → equiv-goals → rtl-gen →
  tb-gen → sim → coverage → goal-audit. All stages PASS. Key results:
  SSOT 19787B/36 sections/0 TBDs; FL model 7 decomposition units,
  29 fcov bins; equiv-goals total=26 blocked=0; iverilog compile+lint
  clean; FL-vs-RTL sim 85/85 matches (0 mismatches); coverage 3/3
  function bins + 6/6 cycle bins hit. Lessons: (1) `check_ssot_disk.sh`
  requires many non-empty sections that are empty-by-default for tiny IPs
  (pnr, security.assets, error_handling.error_sources, handshake_rules,
  trace_events, quality_gates.{dv,eda,signoff}); plan to add these from the
  start. (2) RTL-gen LLM call requires `ATLAS_RUN_REAL_LLM_TDD=1` and
  can timeout; for simple IPs, direct RTL authoring from SSOT is viable.
  (3) cocotb 1.9.2 on macOS with system Python has Makefile discovery
  issues; plain iverilog testbench is a simpler path for tiny IPs.
  (4) FL-vs-RTL timing alignment requires careful reset sequencing in the
  testbench — the FL model step must be called before the posedge, and
  comparison after.

- Added a non-destructive Fast Context / Debugging And Operations layer to
  [[index]] instead of replacing the existing reading order. The goal is faster
  agent handoff while preserving the prior wiki structure: start from the quick
  map, then follow the existing linked pages for detail.
- Captured [[pipeline-progress-debugging]] after mini CPU `ssot-gen` retries
  made progress diagnosis too file-hunting-driven. New rule: headless is a
  reproduction/regression surface, not product-flow authority. Real validation
  must use the same Atlas UI/API/worker path as users:
  `/api/pipeline/dispatch` or `/api/job/dispatch` → worker `/run` →
  `/status/<run_id>` → `/result/<run_id>` → artifacts/DB/UI state. The wiki
  now records the shared `progress_debug` payload shape and the development
  practice that code, tests, real-environment validation, and wiki updates move
  together.
- Captured [[multi-user-worker-isolation]] after the mini CPU orchestrator
  retry exposed shared-worker concerns. Code review found that handoff JSON and
  Pipeline state have user-scoped protections, but live HTTP worker dispatch is
  still URL-scoped through `WORKER_URL_<workflow>` / `WORKER_URL_DEFAULT`.
  Current runtime evidence: `:5521` and `:5522` were bound to `quad_spi`
  workers while unrelated IP jobs were active; mini CPU did not reach worker
  dispatch and no file collision occurred, but reusing those URLs for another
  IP would be a real wrong-owner dispatch risk. Required fix: worker leases
  keyed by user/workspace/IP/workflow/run, worker health metadata, fail-closed
  dispatch preflight, and no `WORKER_URL_DEFAULT` in multi-user mode.

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

- Run Mode / Exec Mode implementation landed for the first stable contract:
  ATLAS top row has `run` and `exec` selectors, pipeline dispatch/state carries
  `run_mode` and `exec_mode`, pipeline UI shows policy/provenance chips,
  `check_ssot_disk.sh --mode starter|engineering|signoff` gates SSOT strictness,
  and `repair_ssot_schema.py --mode ...` writes
  `<ip>/yaml/<ip>.ssot.provenance.json`. The provenance sidecar now records
  nested field paths too, and the pipeline summary treats signoff-critical
  prefixes such as `security.assets.*` and `quality_gates.*` as blockers when
  they are generated defaults or review-needed. Headless SSOT validation/repair
  now passes the selected Run Mode instead of always behaving as signoff. See
  [[run-mode-and-provenance-policy]].

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
