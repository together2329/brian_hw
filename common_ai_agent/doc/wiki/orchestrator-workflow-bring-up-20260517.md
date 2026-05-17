# Orchestrator Workflow Bring-Up (2026-05-17)

The day `workflow/orchestrator/` went from a missing folder to a real workflow
with five differently-modelled workers, an LLM-driven dispatch test against a
scratch IP, an append-only trace log, a Pipeline UI debug strip, and a clear
list of architectural mismatches the bring-up surfaced.

Related: [[orchestrator-worker-handoff]] · [[parallel-todo-sub-agent-workers]] ·
[[atlas-pipeline-screen]] · [[multi-user-worker-conflicts]] ·
[[run-mode-and-provenance-policy]] · [[full-flow-pipeline]] ·
[[human-review-and-escalation]]

## Starting Point — What Was Actually Missing

Despite three reference runs ([[quad-spi-orch-run-20260517]],
[[octa-ddr-spi-orch-run-20260517]], [[atcuart100-pipeline-run]]) being labelled
"orchestrator runs", `ls workflow/` showed every other workflow but no
`orchestrator/` directory. The actual implementation was:

| Layer | Where | What |
|---|---|---|
| Python class | `core/workflow_orchestrator.py` | `WorkflowOrchestrator` dispatcher (no LLM, just todo fan-out) |
| Mode env var | `ATLAS_ORCHESTRATOR_MODE=1` | Progress event schema toggle, NOT cross-workflow routing |
| Context inject | `core/orchestrator_inject.build_orchestrator_inject_fn` | Prepends "you are in orchestrator mode" to existing worker prompts |
| **Workflow directory** | **`workflow/orchestrator/`** | **Missing** — no system_prompt, no rules, no commands |

QUAD SPI / OCTA DDR SPI wiki pages even admit it:

> "**BUG**: pipeline mode `--stages sim,sim-debug,...` does not auto-continue
> past a failed `sim`. Despite `ATLAS_ORCHESTRATOR_MODE=1`, the headless
> workflow stopped at `sim` instead of routing to `sim-debug`."

And:

```bash
ATLAS_ORCHESTRATOR_MODE=1   # progress event schema   ← not what it sounds like
```

The "orchestrator" was a label, not an agent. Routing decisions were made by a
human (me) reading stage status and issuing the next slash command.

## What This Bring-Up Built

### 1. `workflow/orchestrator/` Directory (13 files)

```
workflow/orchestrator/
├── workspace.json                  # registers workflow, routes Pipeline chat here
├── system_prompt.md                # 7,255 chars — mental model, DAG, routing,
│                                   #   budget, dispatch contract, chat behavior,
│                                   #   honesty rules, pending-QA detection
├── plan_prompt.md                  # how to draft a run-to-green plan
├── rules/
│   ├── routing_policy.md           # owner → workflow map, DAG next-stage map
│   └── retry_budget.md             # per-stage retry caps + cumulative cap=40
├── commands/
│   ├── dispatch.json               # /dispatch <workflow> <ip> [reason]
│   ├── status.json                 # /status
│   ├── retry.json                  # /retry [stage]
│   ├── route.json                  # /route — read mismatch_classification, fan-out
│   ├── escalate.json               # /escalate <reason>
│   ├── freeze.json                 # /freeze
│   └── resume.json                 # /resume
└── todo_templates/
    └── run-to-green.json           # 11-step ledger: ssot → goal-audit
```

Verified discoverable by `WorkflowOrchestrator.discover_workflows()` (23 → 24
workflows including orchestrator) and `load_workspace('orchestrator')`
(returns 7,255-char system_prompt, 7 commands, 2 rules, 1 template).

### 2. Multi-Worker Spawn With Five Different Models

```
Orchestrator    gpt-5.5        effort=xhigh    chatgpt.com OAuth
   ├─ ssot-gen     :5521  glm-5.1         api.z.ai
   ├─ rtl-gen      :5522  gpt-5.3-codex   ChatGPT OAuth
   ├─ fl-model-gen :5523  glm-5.1         api.z.ai
   ├─ tb-gen       :5524  deepseek-v4-pro api.deepseek.com
   └─ sim_debug    :5525  kimi-2.6        api.kimi.com
```

Model diversity is intentional:
- `fl-model-gen` and `rtl-gen` on different models so the same LLM cannot
  replicate its own spec-interpretation mistakes on both sides of the equiv
  comparison.
- `sim_debug` on a third model so mismatch classification is not a
  confirmation-bias loop with `tb-gen`.

Spawn commands:

```bash
LLM_PROFILE=glm      python3 src/main.py --serve --port 5521 --workflow ssot-gen      --host 127.0.0.1 &
LLM_PROFILE=gpt      python3 src/main.py --serve --port 5522 --workflow rtl-gen       --host 127.0.0.1 --model gpt-5.3-codex &
LLM_PROFILE=glm      python3 src/main.py --serve --port 5523 --workflow fl-model-gen  --host 127.0.0.1 &
LLM_PROFILE=deepseek python3 src/main.py --serve --port 5524 --workflow tb-gen        --host 127.0.0.1 &
LLM_PROFILE=kimi     python3 src/main.py --serve --port 5525 --workflow sim_debug     --host 127.0.0.1 &
```

Orchestrator launch (per real prompt):

```bash
WORKER_URL_SSOT_GEN=http://127.0.0.1:5521 \
WORKER_URL_RTL_GEN=http://127.0.0.1:5522 \
WORKER_URL_FL_MODEL_GEN=http://127.0.0.1:5523 \
WORKER_URL_TB_GEN=http://127.0.0.1:5524 \
WORKER_URL_SIM_DEBUG=http://127.0.0.1:5525 \
ATLAS_ORCHESTRATOR_MODE=1 \
python3 src/main.py -w orchestrator --model gpt-5.5 --effort xhigh \
        --headless --prompt-file <prompt>
```

### 3. Trace Layer — Three Lenses, One JSONL

`<ip>/orchestrator/trace.jsonl` is append-only. Every event carries `lens`,
`actor`, `peer`, `kind`, `corr`, `step`, and kind-specific keys:

```json
{"ts":"…","step":1,"lens":"interaction","actor":"ssot-gen-worker","peer":"orchestrator","kind":"http_recv","corr":"corr_simple_counter_ssot_1","requested_workflow":"ssot-gen","task_preview":"…"}
{"ts":"…","step":2,"lens":"interaction","actor":"ssot-gen-worker","peer":"orchestrator","kind":"http_accepted","corr":"corr_simple_counter_ssot_1","status":200,"run_id":"run_8f2e47f6"}
{"ts":"…","step":3,"lens":"result","actor":"ssot-gen-worker","kind":"run_completed","corr":"corr_simple_counter_ssot_1","run_id":"run_8f2e47f6","status":"completed"}
```

Lenses:
- `interaction` — who sent what to whom (http_recv, http_accepted, http_rejected)
- `intermediate` — work-in-progress signals (llm_stream, tool_call, retry)
- `result` — final outcomes (gate_verdict, run_completed, escalate)

Writer at `core/orchestrator_trace.py`. Hooks installed in
`core/agent_server.py:/run` for request entry, F3 rejection, run accept, and
async completion.

Reader endpoint: `GET /api/orchestrator/trace?ip=<ip>&limit=&corr=&lens=` and
`DELETE` to clear. (Endpoint added; requires ATLAS API server restart to load.)

Pipeline UI strip: `OrchestratorTraceStrip` component, auto-refresh 3s, groups
events by `corr`, color-codes per lens.

CLI debugging examples:

```bash
# every dispatch the orchestrator ever made
jq -c 'select(.kind=="http_accepted") | {step,actor,corr,run_id}' \
   <ip>/orchestrator/trace.jsonl

# everything tied to one dispatch
jq 'select(.corr=="corr_simple_counter_ssot_1")' <ip>/orchestrator/trace.jsonl

# F3 guard catches
jq 'select(.kind=="http_rejected")' <ip>/orchestrator/trace.jsonl
```

### 4. End-to-End Validations Achieved

| Step | Result |
|---|---|
| Orchestrator workflow auto-discovered (24 total) | ✅ |
| `load_workspace('orchestrator')` returns 7,255-char system_prompt + 7 commands + 2 rules + 1 template | ✅ |
| Five workers spawn, each with distinct model | ✅ |
| F3 workflow-binding guard rejects mismatched dispatches with 403 | ✅ |
| Real-LLM orchestrator (`gpt-5.5 xhigh`) reads `simple_pwm` artifacts and correctly identifies "Pipeline complete · awaiting human sign-off" without dispatching | ✅ |
| Real-LLM orchestrator dispatches one HTTP call to `sim_debug` worker and parses response | ✅ |
| Real-LLM orchestrator fans out three parallel dispatches with distinct `trace_corr` and groups results | ✅ |
| Trace JSONL captures every dispatch with correct `corr` grouping | ✅ |
| Real-LLM orchestrator on `simple_counter` scratch IP correctly refuses to advance past ssot-gen because worker hadn't reached `completed` (gate-trust rule self-applied) | ✅ |

### 5. Architectural Mismatches Surfaced (and Fixed)

The bring-up revealed a class of workflows the original sub-agent model could
not represent: **interactive workflows** (`ssot-gen`, `req-gen`, `architect`).

**Symptom**: `ssot-gen` worker on `simple_counter` wrote a 20 KB SSOT YAML but
never reached `completed` because the worker LLM kept looping trying to
fill-in details it could not know without user input. With `ask_user` and
`record_ssot_qa` both disabled (default), the worker could neither pause nor
hallucinate safely — so it just kept calling LLM.

**Root cause**: Sub-agent fire-and-forget pattern is fine for deterministic
or fully-spec'd workflows (fl-model-gen, rtl-gen, lint, sim, coverage,
goal-audit). It is wrong for workflows that must converse with a human
(spec interview, requirement elicitation, architecture decisions).

**Workflow type matrix:**

| Workflow | Pattern | User involvement |
|---|---|---|
| `ssot-gen` | 🔴 Interactive | high — spec interview |
| `req-gen` | 🔴 Interactive | high — requirement elicitation |
| `architect` | 🔴 Interactive | high — design decisions |
| `fl-model-gen` | 🟢 Auto | none — derived from SSOT |
| `cl-model-gen` | 🟢 Auto | none — derived from SSOT |
| `equiv-goals` | 🟢 Auto | none — deterministic |
| `rtl-gen` | 🟡 Semi-auto | only on RTL_MODULE_CONTRACTS gates |
| `lint` | 🟢 Auto | none |
| `tb-gen` | 🟢 Auto | none |
| `sim` | 🟢 Auto | none |
| `sim_debug` | 🟡 Semi-auto | only on frontier classification |
| `coverage` | 🟢 Auto | none |
| `goal-audit` | 🟢 Auto | none |

**Fixes applied** (closes the interactive-workflow hang):

1. **`workflow/ssot-gen/workspace.json`** — `WORKFLOW_DISABLED_TOOLS` reduced
   from `"ask_user,record_ssot_qa"` to `"ask_user"`. Worker can now write QA
   cards to disk via `record_ssot_qa` and exit cleanly, instead of looping.

2. **`workflow/orchestrator/system_prompt.md`** — new "Pending QA Detection"
   section. Before declaring any dispatch successful, orchestrator MUST
   `GET /api/ssot/qa?ip=<ip>` and pause if `pending_count > 0`, surfacing the
   pending questions to the user instead of retrying or escalating as a
   failure.

3. **`frontend/atlas/pipeline.jsx`** — new `PendingQABanner` component above
   the flow map. Polls `/api/ssot/qa` every 5 s; when QA is pending shows a
   yellow alert with chip-list of question topics and an "Answer QA →" link.

### 6. Reference Run Data

| Run | Model + effort | Iterations | Input tokens | Output | Cache hit | Notes |
|---|---|---|---|---|---|---|
| Read-only `simple_pwm` status | glm-5.1 medium | 1/120 | 27,561 | 1,395 | 99.4% | first orchestrator real-LLM call |
| One-worker probe | glm-5.1 medium | 2/120 | 33,058 | 547+80 | 99.6% | first HTTP dispatch from orch LLM |
| Three-worker fan-out | glm-5.1 medium | multi | 37,573 | 87 | 99.8% | three distinct corr IDs, perfect grouping |
| Same run on `gpt-5.5 xhigh` | gpt-5.5 xhigh | 1/120 | 33,328 | 35 | (Responses API) | tighter output, deeper internal reasoning |
| Scratch `simple_counter` | gpt-5.5 xhigh | 3/120 | 49,053 | 606 (516 rsn) | 91% | dispatched ssot-gen, refused to advance past running worker |

## Lessons (Brief)

- **"Orchestrator" was a label, not an agent**, until this bring-up. Three
  prior reference runs all routed by a human reading stage status.
- **Sub-agent fire-and-forget breaks on interactive workflows**. The fix is
  a QA-card escape hatch + an orchestrator polling rule, not a fancier
  worker prompt.
- **Honest gate-trust matters in the orchestrator prompt**. `gpt-5.5 xhigh`
  refused to advance past ssot-gen because the worker had not returned
  `completed`, even though `yaml/simple_counter.ssot.yaml` existed on disk.
  This is the exact behavior the system_prompt asks for.
- **Trace JSONL is cheap and load-bearing**. Without it the "did the
  orchestrator actually dispatch?" question becomes archaeological. With it,
  three `jq` lines answer it.
- **Heterogeneous models reduce confirmation bias** for spec interpretation.
  Worth keeping `fl ≠ rtl` and `tb ≠ sim_debug` by model.

## What Still Has Not Been Validated

- **Full SSOT → goal-audit autonomous loop**. The scratch `simple_counter`
  run only reached "ssot-gen running" before the worker hit the
  interactive-workflow trap. The QA-card escape hatch was added after that
  observation; re-running on top of the fix is the next step.
- **Live cross-workflow routing**. The owner-classification → next-dispatch
  loop (rtl_bug → rtl-gen, tb_bug → tb-gen) has been simulated end-to-end
  through HTTP, but not yet exercised by a real `sim_debug` run on a real
  failing IP.
- **Pipeline UI integration end-to-end**. `OrchestratorTraceStrip` +
  `PendingQABanner` + trace API endpoint are all wired; the ATLAS API server
  needs a restart to pick up the new endpoint, and a real run is needed to
  populate the strip live.

## Quick Bring-Up Recipe

```bash
# spawn the five workers (different models)
LLM_PROFILE=glm      python3 src/main.py --serve --port 5521 --workflow ssot-gen      --host 127.0.0.1 &
LLM_PROFILE=gpt      python3 src/main.py --serve --port 5522 --workflow rtl-gen       --host 127.0.0.1 --model gpt-5.3-codex &
LLM_PROFILE=glm      python3 src/main.py --serve --port 5523 --workflow fl-model-gen  --host 127.0.0.1 &
LLM_PROFILE=deepseek python3 src/main.py --serve --port 5524 --workflow tb-gen        --host 127.0.0.1 &
LLM_PROFILE=kimi     python3 src/main.py --serve --port 5525 --workflow sim_debug     --host 127.0.0.1 &

# verify
for p in 5521 5522 5523 5524 5525; do curl -s http://127.0.0.1:$p/health; echo; done

# launch the orchestrator with a prompt file
WORKER_URL_SSOT_GEN=http://127.0.0.1:5521 \
WORKER_URL_RTL_GEN=http://127.0.0.1:5522 \
WORKER_URL_FL_MODEL_GEN=http://127.0.0.1:5523 \
WORKER_URL_TB_GEN=http://127.0.0.1:5524 \
WORKER_URL_SIM_DEBUG=http://127.0.0.1:5525 \
ATLAS_ORCHESTRATOR_MODE=1 \
python3 src/main.py -w orchestrator --model gpt-5.5 --effort xhigh \
        --headless --prompt-file /tmp/your_prompt.txt
```
