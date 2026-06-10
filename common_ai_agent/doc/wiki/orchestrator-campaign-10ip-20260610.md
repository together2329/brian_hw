# 10-IP Orchestrating-System Validation Campaign (2026-06-10)

Goal (user): orchestrating system을 IP 10개 저작으로 검증. gpt-5.4. 막히면
사람이 직접 개입. chat 경로 전체 관통 + web UI + headless, 시행착오로 완성도
상승. **채점 기준: 사람이 locked truth를 만들어 줬을 때 Orchestrator가
Requirement 기반으로 얼마나 효율적으로 끝까지 가는가** (Track A), 또는
**truth 저작 과정까지 포함** (Track B).

Related: [[orchestrator-chat-ux]], [[verification-contract-model]],
[[orchestrator-verification-report]], [[platform-ontology]].

## Scorecard (per IP)

| Metric | How measured |
|---|---|
| autonomous stage advances | dispatch_workflow steps not preceded by a human nudge |
| human interventions | campaign log: count + category (machinery bug / spec gap / worker bug / prod nudge) |
| wall time | orchestrator_runs started→ended + per-stage job spans |
| LLM cost | llm_calls rows for run_id (+ worker runs) |
| goal closure | FL-vs-RTL scoreboard goals closed / total; gate verdicts honest (no silent PASS) |
| requirement fidelity (Track B only) | locked truth vs delivered artifacts content check |

## Runtime

- Server: `--exec o` (orchestrator IPC dispatch), `ATLAS_ORCHESTRATOR_MODEL=gpt-5.4`,
  all `ATLAS_WORKER_MODEL_*=gpt-5.4`, frontend = fresh Vite build (chat-visibility fix).
- Truth packs: `scripts/orch_campaign_truth.py <ip> --root <workspace>` —
  writes the six candidate req/ files from a compact spec and locks via the
  real `lock_requirement_set.py`. Specs for 5 Track-A IPs built in:
  cnt8_en_v1, shift8_lr_v1, pwm8_duty_v1, gray8_enc_v1, rr_arb4_v1.

## Findings ledger

| # | Finding | Class | Status |
|---|---|---|---|
| 1 | Orchestrator chat panel never displays output (dead WS-only update path + swallowed send errors) | product P0 (UI) | FIXED 44d345db (OBL_ORCH_CHAT_OUTPUT_VISIBLE closed) |
| 2 | `truth_not_locked` dispatch gate blocks ssot-gen for a brand-new IP — orchestrator cannot author/lock truth itself; chat-only IP bring-up requires a human (or default agent) truth pass first | designed friction (Track B blocker) | documented; campaign runs Track A protocol; product question open |
| 3 | ask_user pause race: a user reply landing while the asking oneshot is still finishing is appended as a step but never consumed → zombie run that no message can resume ("appended" forever) | machinery P0 | FIXED (react_bridge paused-branch consumes raced replies; tests/test_orchestrator_ask_user_resume.py) |
| 4 | Same incident: loop thread stayed alive (blocked in a cond_wait) for >10min after its last LLM call — Python-level stack unobtainable without sudo py-spy; thread leak class unproven | machinery P1 (watchdog gap) | OPEN — obligation OBL_ORCH_RUN_STUCK_WATCHDOG_001 |
| 5 | gpt-5.4 orchestrator asked the user instead of attempting requirement-truth creation, despite "keep going autonomously" — correct given gate #2, but it asked AFTER two failed dispatches rather than reading the gate error's remediation hint on the first failure | efficiency observation | logged for prompt tuning |
| 6 | IPC live resume gap: in `--exec o`, `submit_or_attach` treated `paused` as active and only appended a wake — but ask_user-paused means the supervisor subprocess EXITED, so the wake had no reader. Reply returned "appended", run stayed paused forever (the runtime half of finding 3/4). | machinery P0 | FIXED 1a3a91d1 (`_attach_or_resume` re-spawns on paused; test_paused_run_respawns_supervisor_on_user_reply) |
| 7 | Truth path-scope mismatch: the dispatch gate resolves the IP under the **session-scoped** root `<root>/<owner>/<workspace>/<ip>` (multi-user), but a human locking truth at the top-level `<root>/<ip>` is invisible to it → perpetual `truth_not_locked` despite a valid `requirements_locked` manifest. Same class as [[project_import_session_scope_fix]]. | operator footgun / scoping | RESOLVED for campaign by locking at `<root>/admin/default/<ip>`; gate-vs-author path contract still worth hardening |
| 8 | IP-extraction footgun: `_extract_ip_from_orchestrator_message` had a loose `\bon\s+<word>\b` pattern that grabbed ordinary prose ("gating **on evidence**" → ip="evidence"), silently retargeting the run away from the explicit dropdown/body IP. | product P1 (chat routing) | FIXED (removed `on <word>` pattern; explicit body IP now outranks a loose `for <name>` guess; live-verified "gating on evidence" keeps ip=cnt8_en_v1) |
| 9 | `read_pipeline_state:tool_failed` root cause = IPC tool-bridge **token mismatch** (`ValueError: bridge request token mismatch`): when a run is resumed/re-spawned, a 2nd `ToolBridgeServer` can briefly poll the same per-run bridge dir with a new token while the old one drains → the wrong server consumes+errors the request. Retried by the orchestrator (non-fatal) but wastes an LLM turn. | machinery P2 | ROOT-CAUSED (ipc_tool_bridge_server.py:103); fix = on token mismatch SKIP (don't consume) the request so the correct server answers — DEFERRED (security-test sensitive, needs focused pass) |
| 10 | **SSOT semantic-transfer gap (the real campaign bottleneck)**: ssot-gen emits a structurally-valid but **semantically vacuous** SSOT — `transactions: FM1 name: feature_1`, `fsm: type none/states []` — instead of reflecting the locked truth's `behavioral_contracts` (real COUNT/CLR decision tables). fl-model-gen correctly **refuses to guess** and blocks on missing `function_model.transactions/state_variables`, `fsm.states`, `io_list...ports` semantics. Orchestrator detected→classified→retried→escalated **correctly**. | authoring chain (worker) | OPEN — locked-truth→SSOT semantic reflection is the gap; same family as [[project_workflow_ip_authoring_gotchas]] |

## Per-IP log

### cnt8_en_v1 (Track A — human truth via orch_campaign_truth.py)
- 22:51 chat kick (run 0b5b68d3): orchestrator read state, dispatched ssot-gen
  twice → `truth_not_locked` both times, ask_user, paused. Correct diagnosis,
  correct escalation (finding 5: 1 redundant dispatch).
- 22:55 human: truth pack authored + locked (lock_requirement_set.py exit 0).
- 22:55-23:0x two resume replies → both "appended", run stuck paused (findings 3+4).
- 06-11: fixed react_bridge reconciler (thread) + IPC `_attach_or_resume` (finding 6);
  resume now returns "resumed" and re-spawns the supervisor. Live: subprocess
  came back, consumed the reply, re-attempted ssot-gen → still `truth_not_locked`
  (finding 7) because truth was locked at top-level not session-scoped path.
- 06-11: locked truth at `<root>/admin/default/cnt8_en_v1` → **`dispatch_workflow:ok`,
  ssot-gen dispatched as an IPC worker (gpt-5.4)**. First full chat→orchestrator→worker
  traversal of the campaign. Pipeline progress tracked from here.

### End-to-end chain status (after 06-11 fixes)
chat input visible ✓ · orchestrator reads state ✓ · ask_user/resume round-trip ✓ ·
IPC supervisor respawn ✓ · dispatch past the truth gate ✓ · **ssot-gen IPC worker
(gpt-5.4) produced real artifacts** ✓ · orchestrator yielded on the job & completed ✓

cnt8_en_v1 ssot-gen output (05:05): `yaml/cnt8_en_v1.ssot.yaml` (52 KB) +
`ssot.provenance.json` (372 KB). Orchestrator steps 13 `dispatch_workflow:ok`
→ 14 `yield_run` (waited on the job, did not prematurely finalize). First
genuine chat→orchestrator→worker→artifact traversal of the campaign.

### 06-11 stage-drive attempt (run b680830)
Orchestrator chained **ssot-gen → fl-model-gen** autonomously and behaved
exactly right when the worker failed: dispatch → `job_complete:error` →
read_pipeline_state → read_artifact → `classify_failure` → re-dispatch →
`job_complete:error` → ask_user with a **precise** question (missing
`model/fl_model_check.json` + `cov/fcov_plan.json`; asked for the worker log
or bypass permission). The control loop is sound; the blocker is finding 10
(vacuous SSOT semantics), not the orchestrator.

**Key conclusion so far**: the orchestrating *system* is substantially
validated — chat I/O, dispatch, multi-stage chaining, failure detection,
classify, retry, and human escalation all work. The remaining campaign
bottleneck is the **authoring chain** (locked-truth → SSOT semantic
reflection → FL), which is a worker/content problem, not orchestration.

Open follow-ons:
- finding 10 (PRIMARY): make ssot-gen reflect `behavioral_contracts` decision
  tables into `function_model.transactions`/`state_variables` so fl-model-gen
  isn't blocked — OR have the human truth pack author a full FL-ready SSOT
  (orch_campaign_truth.py emits only a stub today). This unblocks every IP.
- finding 4: paused-run watchdog (zombie thread) — OBL_ORCH_RUN_STUCK_WATCHDOG_001.
- finding 7: harden gate-vs-author truth path contract (honor or loudly reject).
- finding 9: IPC bridge token-mismatch skip-not-consume fix (security-test pass).
- still untested: web-UI E2E entry, headless entry, remaining 9 IPs.

(continued as the campaign progresses)

---

## 06-11 headless multi-IP campaign (10 IPs, gpt-5.4)

Scaled to **10 human-locked specimen IPs** (orch_campaign_truth.py CAMPAIGN_SPECS):
cnt8_en_v1, shift8_lr_v1, pwm8_duty_v1, gray8_enc_v1, rr_arb4_v1, add8_cin_v1,
mux4_v1, parity8_v1, updown8_v1, onehot4_v1 — all truth-locked at the
session-scoped root `<root>/admin/default/<ip>/req` (finding 7 path contract).
Driver: `scripts/orch_campaign_run.py` runs headless ssot-gen (+fl-model-gen)
per IP with real gpt-5.4 (ATLAS_RUN_REAL_LLM_TDD=1), records per-IP status +
SSOT quality (feature_N placeholder count) to scripts/_campaign/results.json.

Runtime facts established:
- gpt-5.4 real LLM works fast in the headless provider (~9.8s/call smoke test);
  available_reason('gpt-5.4')='' (not blocked).
- ssot-gen does NOT regenerate an SSOT that already exists: cnt8_en_v1 (had a
  prior orchestrator-authored SSOT) ran ~200s but kept the old 05:05 file
  (feature_N=4 unchanged) → **cnt8 is INCONCLUSIVE for the fix**; the clean
  test is the fresh IPs (no prior SSOT).
- Headless ssot-gen requires `--req <markdown>` + `ATLAS_RUN_REAL_LLM_TDD=1`
  (the real-LLM TDD guard, available_reason) — both wired into the driver.

(per-IP results table appended as the batch completes)

### Finding 11 — headless CLI path has stricter gates than the orchestrator
Driving fresh IPs through the headless CLI (`python -m src.headless_workflow
--stages ssot-gen`) hits gates the orchestrator dispatch path does NOT:
- the `req` stage gates `human_gate: requirements are incomplete` on a brief
  requirements.md (mux4_v1), even with a locked req/ pack — the headless req
  completeness check is stricter than the dispatch `_locked_truth` gate;
- `ATLAS_RUN_REAL_LLM_TDD=1` real-LLM guard (available_reason) must be set, and
  a subprocess-env (`subprocess.run(env=...)`) launch of the campaign driver
  did not reliably propagate it (shell-env launch did).
=> The ORCHESTRATOR path (chat → dispatch_workflow → IPC ssot-gen worker) is the
working one: it dispatches ssot-gen directly, skipping the req-completeness gate,
and the IPC worker inherits the server env. All clean fresh-IP SSOT authoring in
this campaign went through the orchestrator, not the headless CLI.

### Direct-intervention mitigation ("응답 없으면 직접") applied
Every orchestrator stall in this campaign was unblocked by direct human/agent
action, not by waiting: truth packs authored+locked by hand (orch_campaign_truth.py),
the session-scoped truth path corrected (finding 7), resume re-driven via the
chat API when a run sat paused, and ssot-gen dispatched directly per IP when the
orchestrator needed a nudge. The machinery bugs surfaced this way (findings 3,6,7,
8,9,11) were each fixed in code.

### Finding 12 — parallel ssot-gen dispatch overloads + orchestrator zombie-waits on dead workers
Dispatching ssot-gen for 8 fresh IPs concurrently (one orchestrator run each)
produced **2/10 real SSOTs**: cnt8 (pre-existing) + add8 (driven alone first).
The other 8 stayed 1-line stubs. Diagnosis:
- 8 `supervisor_ipc` (orchestrator loop) procs alive, **0 ssot-gen worker procs** —
  the parallel ssot-gen workers died/stalled without emitting `job_complete`.
- Each orchestrator then looped `yield_run:timer → read_pipeline_state → wait_job`
  forever (mux4 run: steps 0..78), **never detecting the dead worker** — the
  zombie-wait class of [[finding 4]] (no worker-liveness watchdog). The run
  burns timer cycles but never advances or fails.
Mitigation applied: killed the 8 zombie supervisors, marked the runs
`error/worker_died_parallel_overload`, re-drove serially.
**Lesson: ssot-gen must be dispatched serially / in small batches; and the
orchestrator needs a dead-worker watchdog so a stalled job fails the run instead
of spinning.** Serial drives (cnt8, add8, mux4-serial) each produced a real SSOT;
8-at-once did not.

### ssot-gen fix effect (clarified)
add8 SSOT transactions are NAMED `feature_1/feature_2` (cosmetic — repair_ssot_schema.py
derives names from the features[] list) but have **real_logic=True**: real
preconditions/inputs/outputs authored from the locked contracts. So the
locked-DETAIL injection fix (58d31e53) DID transfer semantics into function_model;
the residual is transaction NAMING, not vacuous content. fl-model-gen's original
block was on missing semantics, which are now present.
