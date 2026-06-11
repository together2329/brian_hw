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

### Final 10-IP SSOT result table (2026-06-11)
| IP | SSOT | how driven | note |
|----|------|-----------|------|
| cnt8_en_v1 | REAL 1260L | orchestrator (gpt-5.4, pre-fix) | feature_N=4 (content present) |
| add8_cin_v1 | REAL 1174L | orchestrator serial (post-fix) | real_logic transactions, names cosmetic |
| gray8_enc_v1 | REAL 1152L | orchestrator (parallel survivor) | |
| mux4_v1 | REAL 306L | orchestrator serial (after kill) | |
| shift8_lr_v1 | stub | parallel — worker died | finding 12 |
| pwm8_duty_v1 | stub | parallel — worker died | finding 12 |
| rr_arb4_v1 | stub | parallel — worker died | finding 12 |
| parity8_v1 | stub | parallel — worker died | finding 12 |
| updown8_v1 | stub | parallel — worker died | finding 12 |
| onehot4_v1 | stub | parallel — worker died | finding 12 |

**4/10 real SSOTs.** Every serial/low-contention drive produced a real SSOT;
the 6 stubs are all from the 8-at-once parallel burst that killed the workers
(finding 12). Control-plane reliability: 10/10 dispatched correctly; the failure
is worker throughput under parallel load + the missing dead-worker watchdog.

## Campaign verdict
The orchestrating SYSTEM (control plane) is validated and reliable: chat in →
orchestrator reads state → dispatch_workflow → IPC worker → artifact → yield/
advance, with detect→classify→retry→escalate on failure, proven on cnt8, add8,
mux4, gray8 (ssot-gen) and **mctp_assembler_v2 driven autonomously to STA/PNR
physical-design timing failures**. 12 findings surfaced through trial-and-error;
9 fixed in code (chat-vis, ask_user resume ×2, IPC resume, IP-extraction,
ssot-gen locked-detail, React Flow pipeline, workspace chat) + UI (goal-audit).
Open reliability work: serial-dispatch policy / dead-worker watchdog (finding
12/4), ssot-gen transaction-naming + full elimination of placeholders, headless
req-gate parity (finding 11), gpt-5.4 as the pinned worker model.

---

## CORRECTION + FINAL RESULT: 10/10 real SSOTs (2026-06-11)

Finding 12 was **partially wrong**. The 8-at-once parallel ssot-gen dispatch did
NOT kill the workers — all ssot-gen work funnels through the worker server
(`WORKER_URL_SSOT_GEN=http://127.0.0.1:5621`), which **serialized the queue** and
processed them slowly (~30 min for the batch). They all eventually completed.
Corrected lesson: parallel orchestrator dispatch → a slow serialized worker-server
queue (throughput bound), not worker death. The orchestrator zombie-wait
(finding 12/4 watchdog gap) still holds for genuinely-stalled jobs, but here the
jobs were merely slow.

**FINAL: 10/10 IPs produced real SSOTs** (1142–1289 lines each), each with real
function_model.transactions authored from the locked behavioral contracts
(verified: pwm8 2tx, rr_arb4 3tx, updown8 4tx — all carry output logic, not
placeholders). The ssot-gen locked-detail fix (58d31e53) works across the whole
IP set.

| IP | SSOT lines | tx w/ logic |
|----|-----------|-------------|
| cnt8_en_v1 | 1260 | (gpt-5.4) |
| add8_cin_v1 | 1174 | ssot✓ → **fl-model PASS** (fl_model_check=True) |
| shift8_lr_v1 | 1289 | ✓ |
| pwm8_duty_v1 | 1142 | 2/2 |
| gray8_enc_v1 | 1152 | ✓ |
| rr_arb4_v1 | 1195 | 3/3 |
| mux4_v1 | 1155 | ✓ |
| parity8_v1 | 1274 | ✓ |
| updown8_v1 | 1287 | 4/4 |
| onehot4_v1 | 1146 | ✓ |

### Finding 13 — headless CLI real-LLM guard sees env as unset at stage time
With substantive requirements (≥200 chars, no placeholder words) the headless
`req` stage PASSES (finding 11's req-gate is satisfiable). But `ssot-gen` still
reports `ATLAS_RUN_REAL_LLM_TDD=1 is not set` from `RealLLMProvider.available_reason`
even when the flag is set in the launching shell AND verified preserved through
module import AND added to .env. `import src.headless_workflow` keeps `os.getenv
('ATLAS_RUN_REAL_LLM_TDD')=='1'`, no code path pops/clears it, and headless does
not route ssot-gen through WORKER_URL in-file — yet the stage-time check reads it
as unset. The SSOTs were produced via the orchestrator → worker-server (5621)
path regardless. Open: a stage-execution env-context shadowing bug in the
headless real-LLM guard (the orchestrator path is unaffected and is what
production uses).

### CAMPAIGN COMPLETE
10/10 real SSOTs authored from locked truth; one IP (add8) advanced ssot→fl-model
(PASS); orchestrating control plane validated end-to-end incl. mctp to STA/PNR;
13 findings, 9 code fixes (all on main); web UI on React Flow + chat visible.

---

## add8_cin_v1 full-pipeline drive (2026-06-11) — 6 green stages + compiling RTL + UVM TB

Drove add8 from human-locked truth through the pipeline via orchestrator chat.
Orchestrator state at the end: **passed = [ssot, fl-model, cl-model, equivalence,
lint, tb]** (6 green), **rtl = gate fail** (`open_required_todos=5,
blocking_questions=4`) despite the RTL artifact compiling (`rtl_compile=True`)
and lint passing (`dut_lint=True`). sim correctly gated because rtl is not green.

Real artifacts produced:
- rtl/: `add8_cin_v1.sv` (proper SystemVerilog, SSOT port contract) +
  comb_logic leaf + param.vh + rtl_compile.json(True) + contract/traceability.
- lint/: dut_lint.json (True).
- tb/cocotb/: full UVM-style bench — test_add8_cin_v1.py, scoreboard.py,
  sequences.py, agents.py, uvm_env.py, transactions.py, tb_coverage.py.

### Blockers resolved this drive (all direct intervention, in order)
1. **gpt-5.5 pathological latency** — one orchestrator call took 482s (vs
   gpt-5.4 4.8s). Restarted on gpt-5.4. (gpt-5.5 normal ~4.3s; the 482s was an
   endpoint overload spike.)
2. **gpt-5.3-codex-spark malformed orchestrator tool calls** — fast (1.3s) and
   good at authoring, but called dispatch_workflow with empty args ({}) →
   "workflow required" loop. Model-fit finding: spark OK for workers, too weak
   for the orchestrator's structured tool-calling → use gpt-5.4 for the
   orchestrator. (gpt-5.3-codex itself is UNAVAILABLE on a ChatGPT account: HTTP
   400.)
3. **contract-authority gate** — obligations lacked structural/behavioral
   contract_refs and the SC_/BC_ contracts had no evidence_plan closure;
   orch_campaign_truth.py now emits both + cycle_model_waiver. check_locked_truth_bundle PASS.
4. **stale-worker scheduler block** — the many model-test restarts left orphaned
   "running" worker_runs rows; the scheduler thought workers were busy and left
   rtl-gen queued. Cleared stale rows → rtl-gen picked up and produced RTL.
5. **rtl-gate spec todos (remaining)** — the rtl-gen worker left 5 required
   todos + 4 blocking questions (adder cin/cout/overflow spec ambiguities) open,
   so the rtl stage gate is red even though the RTL compiles+lints; this gates
   sim. The worker's spec-completeness handling is the open item.

### Verdict
The orchestrating system drove a fresh IP from locked truth through 6 pipeline
stages with real, compiling, lint-clean RTL + a full cocotb UVM testbench,
correctly evidence-gating each stage. Model-fit matters: **gpt-5.4 for the
orchestrator** (reliable tool calls), spark/gpt-5.4 for workers. The last gap to
signoff is the rtl-gen worker resolving its own blocking-questions to turn the
rtl gate green.

---

## 06-11 PM session — add8 signoff drive + repair-loop probe (runs a806ad40 / 0a5f0be2)

Server recipe that worked: `python3 -m src.atlas_runtime_run --root <ws> --exec o
--port 8765` + `ATLAS_ORCHESTRATOR_MODEL=gpt-5.4` + ALL `ATLAS_WORKER_MODEL_*=gpt-5.4`
+ `ATLAS_RUN_REAL_LLM_TDD=1`, kicked via `POST /api/pipeline/orchestrator/chat`
with a real **admin login cookie** (`/api/auth/login`).

### Finding 14 — auth-path scoping: local-admin can never see admin/default artifacts
`ATLAS_ADMIN_AUTH_MODE=off` makes every request `local-admin`, and in multi-user
mode the project root always follows the request username → the run scoped to a
fresh empty namespace, saw zero artifacts, tried ssot-gen restart, hit
`session owner/workspace mismatch`, asked, finalized blocked (run 63d13646,
correct behavior, wrong identity). Finding-7 family on the auth axis. Recipe:
log in as the real `admin` DB user; cookie-auth the chat kick.

### Run a806ad40 — VERIFIED full traversal (8 steps, 78s)
read_pipeline_state → parallel artifact reads → detected **stale RTL gate
evidence** → dispatched rtl-gen (IPC, gpt-5.4) → woke on job_complete →
re-verified → finalized completed. Disk evidence: rtl_compile.json +
dut_lint.json rewritten by the worker (passed=true, real iverilog/
pyslang+verilator). Sim: 3 tests 0 fail, scoreboard 28/29; the 1 open row was
NOT silently passed — gate printed `PASS_OR_ESCALATE scoreboard_failed=1` +
`[SIM ESCALATE] owner=sim_debug`.

### Run 0a5f0be2 — repair probe: gates honest, authoring non-convergent
Orchestrator correctly routed the escalation (dispatch sim_debug → error →
fl/cl → SEMANTIC GATE FAIL → equivalence → fail → classify → tb/sim probe),
and after a human root-cause nudge dispatched ssot-gen repair + used
**mark_downstream_stale(from_stage=ssot)** (previously-reported missing wiring —
now confirmed live). Worker errors surface as generic `direct slash command
failed`; the real verdicts live in the worker response result text.

### Finding 15 — ssot-gen does not honor cycle_model_waiver (root cause of the 28/29 row)
add8 locked contracts are cycle_model_waiver=true (combinational), but ssot-gen
authored a fictional control FSM (IDLE/ACCEPT/EXEC_FEATURE_*/COMPLETE/ERROR) +
state_variables, and the **repair dispatch re-authored the same FSM** (job
e2bb7c931167, 122s — non-convergent). The FL semantic gate (locked-truth
validation pattern) correctly blocks every fl/cl regen (job 5af1c569b448), so
the pipeline can never converge without an ssot-gen prompt/validator fix. The
phantom FSM also generated the phantom equivalence state goal
(EQ_STATE_CONTROL_EXEC_FEATURE_2_TO_COMPLETE_3) = the single open scoreboard
row. Ontology: OBL_SSOT_GEN_HONORS_CYCLE_WAIVER — **FIXED 48efb049** (verify_ssot blocker-fails fsm/state_variables/state_updates when all locked contracts are cycle-waived, with convergent remediation; + authoring prompt rules; live add8 phantom-FSM SSOT now FAILs the gate).

### Finding 16 — appended user_message wake never drains → busy-loop → cap death
A chat message appended to a live run is re-consumed on EVERY subsequent
yield_run (`woken: user_message`, job_ids=[]), burning 1-2 LLM calls per cycle;
run 0a5f0be2 spent ~steps 13-50 in this loop and died at the 50-step cap
(`blocked`). wake.jsonl grew to 35 rows. Ontology: OBL_ORCH_USER_WAKE_DRAINED —
**FIXED 48efb049** (runner-lifetime consumed_event_ids shared across wakers;
match-only consumption keeps unmatched job_complete deliverable = zombie-wait
protection intact). Same watchdog family as findings 4/12.

### Net assessment
Control plane re-confirmed end-to-end (read→dispatch→yield→wake→verify→finalize,
detect→classify→retry→escalate, downstream-stale marking). The two blockers to
hands-off convergence (findings 15/16) were fixed same-day in 48efb049; next
re-judge = re-drive add8 ssot repair through the orchestrator to 29/29.
