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

Open follow-ons (next session):
- finding 4: paused-run watchdog (zombie thread) — OBL_ORCH_RUN_STUCK_WATCHDOG_001.
- finding 7: harden the gate-vs-author truth path contract so a human lock at
  the top-level root is either honored or rejected loudly (not silently unseen).
- step 12 `read_pipeline_state:tool_failed` mid-run — investigate the transient.
- continue cnt8_en_v1 past ssot-gen (fl→rtl→lint→tb→sim) and the remaining 9 IPs;
  exercise web-UI and headless entry points.

(continued as the campaign progresses)
