---
title: E2E Orchestrator Loop Validation Plan
type: plan
tags: [atlas-ui, orchestrator, e2e, validation, plan]
created: 2026-05-18
related: [orchestrator-verification-report, orchestrator-workflow-bring-up-20260517, orchestrator-chat-only-product-plan]
---

# E2E Orchestrator Loop Validation Plan

Plan for validating the Phase 3 / 3.5 orchestrator loop end-to-end on a real
scratch IP. This is the "What Still Has Not Been Validated" item from
[[orchestrator-workflow-bring-up-20260517]].

## Current Environment

**Workers running (17 processes):**

| Port | Workflow | Model |
|---|---|---|
| 5621 | ssot-gen | gpt-5.5 xhigh |
| 5622 | fl-model-gen | gpt-5.5 xhigh |
| 5623 | rtl-gen | gpt-5.3-codex high |
| 5624 | lint | deepseek |
| 5625 | tb-gen | deepseek |
| 5626 | sim | gpt-5.3-codex |
| 5627 | coverage | deepseek |
| 5628 | sim_debug | kimi |
| 5629 | syn | gpt-5.3-codex |
| 5630 | sta | gpt-5.3-codex |
| 5631 | pnr | gpt-5.3-codex |
| 5632 | sta-post | gpt-5.3-codex |
| 5521–5525 | older set (ssot-gen, rtl-gen, tb-gen, sim, sim_debug) | various |

**ATLAS API:** port 62196 (atlas_ui.py, gpt-5.5 xhigh)

**IPs in DB:** Simple_Timer, arm_m0_min, atcdmac100, mini_axi_slave_wrapper,
pl330, simple_uart_tx, pl330real, pl330realverify, pl330uifresh, realpl330

## Approach: Tiered Validation

### Tier 1: Smoke Test (~5 min, ~$0.50)

**Goal:** Prove the orchestrator loop boots, reads pipeline state, and makes
at least one real dispatch decision.

**Steps:**

1. Create a fresh scratch IP `e2e_orch_smoke` via API or DB insert.
2. Send one orchestrator chat message:

   ```
   POST /api/pipeline/orchestrator/chat
   {"ip": "e2e_orch_smoke", "message": "Create a simple 4-bit counter with synchronous reset and run through ssot-gen."}
   ```

3. Poll `GET /api/orchestrator/active_run?ip=e2e_orch_smoke` every 2s for up
   to 60s.
4. Verify:
   - An `orchestrator_runs` row was created (status `running` or `completed`).
   - At least one `orchestrator_steps` row was appended (step_index ≥ 0).
   - The step has `tool_name` in `{read_pipeline_state, dispatch_workflow, ask_user}`.
   - `trigger_source=orchestrator_chat` on any dispatched job.
5. Record: run_id, steps taken, tool calls made, tokens used, wall time.
6. Stop — do not let the loop continue past ssot-gen unless explicitly asked.

**Pass criteria:** orchestrator_runs row exists + ≥1 step + tool_name is a real
orchestrator tool (not a no-op).

**Token cost estimate:** ~30K input tokens (system prompt + pipeline state read)
+ ~2K output tokens ≈ $0.30–0.60 depending on model.

### Tier 2: SSOT-Gen Through (~15 min, ~$3–5)

**Goal:** Prove the orchestrator can drive ssot-gen to completion and gate on
the result.

**Steps:**

1. Same scratch IP as Tier 1 (or fresh).
2. Chat message targets ssot-gen only.
3. Observe:
   - `dispatch_workflow(workflow="ssot-gen")` step appears.
   - Worker job completes (poll `/api/jobs`).
   - `read_artifact` or `read_pipeline_state` step reads the SSOT result.
   - Orchestrator makes a gate decision (pass/fail/needs-QA).
4. If `ask_user` fires (SSOT QA pending), record that the loop paused correctly.
5. Stop after ssot-gen gates.

**Pass criteria:**
- SSOT YAML written to disk.
- `orchestrator_steps` contains dispatch + read + gate steps.
- `trigger_source=orchestrator_chat` on the workflow_run.
- If QA needed, run status is `paused` (not `error`).

### Tier 3: Multi-Stage DAG (~30–60 min, ~$10–20)

**Goal:** Full ssot → fl-model → equiv-goals → rtl → lint → tb → sim chain.

**Steps:**

1. Fresh scratch IP `e2e_orch_full`.
2. Chat: "Create a simple 4-bit up-counter with sync reset and async load.
   Run the full pipeline to sim pass."
3. Observe the full DAG via:
   - `GET /api/orchestrator/trace?ip=e2e_orch_full` (trace JSONL).
   - `GET /api/orchestrator/runs/{run_id}` (steps).
   - `GET /api/pipeline/state?ip=e2e_orch_full` (stage cards).
4. Record every dispatch, every gate decision, every budget check.
5. If a stage fails, verify the failure is classified and routed to the
   correct owner.

**Pass criteria:**
- Orchestrator reaches at least `rtl-gen` completion.
- `dispatch_workflow(stages=[...])` fan-out appears in steps if applicable.
- Every `workflow_run` has `trigger_source=orchestrator_chat`.
- Budget tracker is consulted (check step `retry_budget_state_json`).
- If sim fails, `classify_failure` is called before retry.

### Tier 4: Repair Routing (Bonus)

**Goal:** Prove sim_debug → owner classification → repair dispatch works.

**Steps:**

1. After Tier 3, if sim has mismatches, inject a known RTL bug.
2. Let the orchestrator run `sim_debug` → `classify_failure` → route to owner.
3. Verify the owner dispatch reaches the correct worker.
4. Verify the orchestrator gates on the repair result.

## Observation Commands

```bash
# Watch orchestrator steps in real time
cd common_ai_agent && python3 -c "
import sqlite3, json, time
db = sqlite3.connect('atlas.db')
db.row_factory = sqlite3.Row
while True:
    rows = db.execute('''
        SELECT s.step_index, s.tool_name, s.verdict, s.dispatched_workflow
        FROM orchestrator_steps s
        JOIN orchestrator_runs r ON s.run_id = r.id
        WHERE r.ip_id = (SELECT id FROM ip_blocks WHERE ip_name = \"e2e_orch_smoke\")
        ORDER BY s.step_index DESC LIMIT 5
    ''').fetchall()
    for r in rows:
        print(f'  step {r[0]}: {r[1]} → {r[2]} (dispatch: {r[3]})')
    time.sleep(2)
"
```

```bash
# Watch trace events
tail -f <ip>/orchestrator/trace.jsonl | jq -c '{step, kind, actor, corr}'
```

```bash
# Check active run
curl -s http://127.0.0.1:62196/api/orchestrator/active_run?ip=e2e_orch_smoke | jq .
```

## Risks

| Risk | Mitigation |
|---|---|
| LLM token cost spirals | Hard cap at 50 steps / 30 min built into the loop |
| Worker hangs on interactive workflow | SSOT QA escape hatch added in bring-up; watch for `paused` state |
| Model rate limits | Workers use different providers (gpt-5.5, codex, deepseek, kimi, glm) |
| Workers from older set (5521-5525) conflict | Only the 5621-5632 set should be in WORKER_URL_* |
| ATLAS API requires auth | Check if login session is needed for curl calls |

## Decision Needed

Before running any tier:

1. **Which model for the orchestrator?** The wiki bring-up used gpt-5.5 xhigh.
2. **Which scratch IP?** A new one is cleanest. `simple_counter` was used in
   the bring-up — a fresh name avoids collision.
3. **How many tiers to run?** Tier 1 is sufficient for a smoke-test proof.
   Tier 3 is needed for "product flow works" claim.
4. **Auth token?** The API returns `{"detail":"login required"}` — we need a
   session cookie or API key.
