---
title: Orchestrator Chat Only Product Plan
type: process
tags: [atlas-ui, orchestrator, product-flow, multi-worker, evidence, plan]
updated: 2026-05-18
related: [atcdmac100-document-flow-ui-honesty-20260518, pl330-real-orchestrator-ui-lessons-20260517, orchestrator-worker-handoff, atlas-pipeline-screen, pipeline-progress-debugging, atlas-browser-control-runbook, full-flow-pipeline, orchestrator-llm-loop-phase3]
---

# Orchestrator Chat Only Product Plan

> **Implementation status (2026-05-18)**: Phase 3 (Real Orchestrator Loop)
> shipped. See [[orchestrator-llm-loop-phase3]] for the new DB tables, tools,
> loop engine, background runner, HTTP route rewrite, and UI banner. Phases 1,
> 2, 4, 5 still open.

Plan for making ATLAS behave as a real user-facing IP creation and verification
orchestrator: the user talks only to the right-side Orchestrator chat, and the
Orchestrator owns document import, worker dispatch, evidence checks, repair
routing, and final status. This page follows the ATCDMAC100 honesty correction
in [[atcdmac100-document-flow-ui-honesty-20260518]].

Related: [[pl330-real-orchestrator-ui-lessons-20260517]],
[[orchestrator-worker-handoff]], [[atlas-pipeline-screen]],
[[pipeline-progress-debugging]], [[atlas-browser-control-runbook]],
[[full-flow-pipeline]].

## Product Rule

For product-flow claims, the only valid user command surface is:

```text
right-side Orchestrator chat -> Orchestrator loop -> worker dispatch -> evidence
```

Allowed operator surfaces:

- Browser automation to type into the Orchestrator chat and inspect visible UI.
- Read-only shell/API diagnostics when debugging why the UI did not update.
- Cleanup of already-started processes.
- Source-code fixes when the user explicitly asks for implementation.

Not product-flow authority:

- Manually running workflow scripts to advance stages.
- Direct worker chat unless the Orchestrator explicitly routes a scoped review.
- Marking stage pass from worker prose or file existence alone.
- Treating headless/common-engine success as proof that visible ATLAS UI worked.

## Current Capability

ATLAS currently has a useful dispatch control plane, but not yet a complete
LLM Orchestrator control loop.

What works today:

- `/api/pipeline/orchestrator/chat` accepts user text.
- It detects terms such as `run to green`, `pipeline`, `make`, `create`,
  `만들`, and `생성`.
- It maps those terms to pipeline stage ids.
- It creates jobs with `pipeline_run_id`, `user_id`, `ip`, `workflow`,
  `stage_id`, dependency metadata, run mode, and exec mode.
- It records chat and workflow dispatch trace events in the DB.
- If live worker URLs are registered, workers can run and produce artifacts.

What this means:

```text
Current system = Orchestrator chat dispatch gateway
Target system  = Orchestrator LLM evidence-gated control loop
```

The distinction matters. A deterministic chat route can start workers, but it
does not prove that an Orchestrator LLM read the requirement, chose the next
stage, interpreted failures, enforced retry budgets, or routed repairs.

## Capability Ladder

### L0: Parser Dispatch

The chat endpoint parses user text and creates jobs. This is the current
baseline. It is useful but should not be marketed as autonomous orchestration.

Evidence:

- chat event exists
- jobs exist
- `pipeline_run_id` is stable
- stage evidence may appear later

Missing:

- document-aware requirement import
- LLM reasoning loop
- evidence-gated next-step decisions
- owner-based repair routing

### L1: Orchestrator-Owned Document Import

The Orchestrator receives a PDF path or upload and calls an `import_document`
tool before dispatching `ssot-gen`.

Required output:

- `<ip>/req/import_manifest.json`
- extracted markdown or text under `<ip>/req/source/`
- source hash and document provenance
- `requirement_source_id` attached to the pipeline run
- `ssot-gen` payload references the imported requirement source

The user should be able to type:

```text
Create ATCDMAC100 from /path/to/AndeShape_ATCDMAC100_DS079_V1.2.pdf and run engineering full pipeline.
```

and then see a document import step before SSOT begins.

### L2: Evidence-Gated Orchestrator Loop

The Orchestrator becomes a real loop:

```text
read_pipeline_state
read latest evidence
decide next workflow
dispatch_workflow
wait or poll job
check artifact gate
route failure or continue
reply to user
```

Pass rules:

- `completed` worker status is not enough.
- Artifact readers decide stage state.
- Stage evidence must include source versions and provenance.
- If evidence is stale, downstream stages are stale.
- If evidence fails, classify owner before retry.

### L3: Repair-To-Green

Failures become routed decisions instead of terminal confusion.

Examples:

- RTL compile fail -> `rtl-gen`
- Lint fail -> `rtl-gen`
- Simulation mismatch -> `sim_debug` then owner route
- Coverage gap -> `tb-gen` or coverage-plan owner
- STA setup fail -> timing target / SSOT / RTL owner classification
- Missing worker URL -> durable handoff, not shell fallback

The loop must respect per-stage retry budgets and stop at human review when
the budget or authority boundary is hit.

### L4: Team/Multiuser Control Plane

The same Orchestrator loop must hold under multiple users and IPs:

- separate `user_id`, `session_id`, `ip_id`, `workflow`, `pipeline_run_id`
- separate browser-visible state per user/IP
- admin sees all runs and blockers
- worker leases prevent cross-user job collision
- global chat can summarize each IP, but cannot mutate another IP without
  explicit admin authority

## Required Architecture Changes

### 1. Convert Chat Route Into Agent Launch

`/api/pipeline/orchestrator/chat` should stop being only a parser and job
creator. It should create or resume an Orchestrator run.

Target behavior:

```text
POST /api/pipeline/orchestrator/chat
  -> persist user message
  -> create/resume orchestrator_run
  -> start gpt-5.5 Orchestrator worker
  -> stream/record Orchestrator steps
```

The Orchestrator worker may still use deterministic helpers, but the state
machine decision belongs to the Orchestrator run, not the HTTP route.

### 2. Add Orchestrator Tools

Minimum tool set:

| Tool | Purpose |
|---|---|
| `import_document(ip, path_or_upload)` | Extract PDF/doc requirement, hash it, persist provenance |
| `read_pipeline_state(ip)` | Read DB/job/artifact state |
| `dispatch_workflow(workflow, ip, payload)` | Start a worker with scoped provenance |
| `wait_job(job_id)` | Observe worker completion without manual polling in chat code |
| `read_artifact(ip, stage)` | Read canonical evidence summaries |
| `classify_failure(ip, stage)` | Decide owner route from evidence |
| `ask_user(question, context)` | Persist human-gated decisions |
| `write_handoff(workflow, ip, payload)` | Durable fallback when no live worker exists |
| `mark_downstream_stale(ip, from_stage)` | Invalidate stale evidence after upstream changes |

### 3. Strengthen Provenance

Every worker-produced artifact should carry:

```json
{
  "trigger_source": "orchestrator_chat",
  "orchestrator_run_id": "...",
  "chat_message_id": "...",
  "pipeline_run_id": "...",
  "user_id": "...",
  "session_id": "...",
  "ip_id": "...",
  "workflow": "...",
  "stage_id": "...",
  "worker_model": "...",
  "worker_reasoning_effort": "...",
  "requirement_source_id": "..."
}
```

This is how future agents distinguish real UI Orchestrator execution from
manual backend execution.

### 4. Make UI Orchestrator-First

UI policy:

- Right rail remains the only normal command surface.
- Stage buttons should enqueue an Orchestrator chat intent, not bypass it.
- Worker workspace chat defaults to read-only or debug-only.
- Worker cards show model, active job, last command, last evidence, and
  provenance.
- A visible banner should distinguish:
  - Orchestrator-driven run
  - manual/headless evidence
  - stale evidence
  - handoff waiting
  - human decision waiting

### 5. Evidence Gates For EDA

SYN/STA/PnR/PSTA need the same strictness as RTL/sim:

- SYN pass requires mapped netlist and report checks.
- STA pass requires WNS/TNS policy, not just `sta.report.md`.
- PnR pass requires route completion, DRC/congestion status, and output DEF.
- PSTA pass requires post-route timing evidence.

ATCDMAC100 showed why this matters: synthesis produced useful evidence, but
pre-route STA failed setup at `hclk@10ns`; route was interrupted. The UI must
show that as blocked, not green.

## Implementation Plan

### Phase 1: Product Boundary Guard

Goal: make it impossible to accidentally claim manual/backend work as UI
Orchestrator work.

Work:

- Add `trigger_source` to pipeline jobs and artifact provenance.
- Set `trigger_source=orchestrator_chat` only when spawned from the right-side
  Orchestrator chat.
- Set `trigger_source=pipeline_button`, `headless`, `manual_script`, or
  `worker_direct` for other paths.
- Show the source in Pipeline UI.
- Update stage pass logic to expose mixed-source evidence.

Acceptance:

- A manually run stage cannot appear as "Orchestrator-run" in UI.
- ATCDMAC100-style backend evidence is visible but labeled non-product-flow.

### Phase 2: Document Import Tool

Goal: PDF requirements can enter the flow through Orchestrator user input.

Work:

- Implement `import_document`.
- Accept local paths and uploaded files.
- Write import manifest, extracted text, hashes, and source locator.
- Include `requirement_source_id` in `ssot-gen` dispatch payload.
- Surface imported document in Pipeline UI.

Acceptance:

- User types a PDF path in Orchestrator chat.
- `ssot-gen` receives the imported source, not only a loose prose prompt.
- The generated SSOT links back to the source manifest.

### Phase 3: Real Orchestrator Loop

Goal: gpt-5.5 Orchestrator controls stage sequencing and repair.

Work:

- Create `orchestrator_runs` and `orchestrator_steps` DB records.
- Launch/resume Orchestrator worker from chat route.
- Give the Orchestrator tools from this plan.
- Persist each decision:
  - observed state
  - selected next workflow
  - dispatch payload
  - evidence read
  - pass/fail decision
  - retry budget state
  - user-facing reply

Acceptance:

- A new IP can be started from one chat message.
- The Orchestrator pauses on QA/human gates.
- Every worker dispatch has an Orchestrator decision record.

### Phase 4: Repair Routing And Retry Budgets

Goal: failures loop to the right owner without manual intervention.

Work:

- Encode owner routing for compile, lint, sim, coverage, SYN, STA, PnR.
- Persist per-stage retry counters.
- Stop on budget exhaustion with a review card.
- Prevent duplicate active jobs for the same `user/ip/stage`.
- Mark downstream stale when upstream artifacts change.

Acceptance:

- Injected RTL failure routes to `rtl-gen`.
- Injected TB/scoreboard failure routes to `tb-gen`.
- STA fail routes to timing/RTL/SSOT classification instead of false green.

### Phase 5: Browser-Only Product Test

Goal: prove the product path exactly as a user sees it.

Test shape:

```text
open visible ATLAS URL
create fresh IP
type only in right-side Orchestrator chat
include PDF path
watch worker dispatches
inspect Pipeline UI state
click worker cards for evidence
do not run workflow scripts to advance stages
```

Required assertions:

- `chat_message` exists.
- `orchestrator_run` exists.
- every job has `trigger_source=orchestrator_chat`.
- every artifact has matching `pipeline_run_id`.
- stage state comes from artifact readers.
- worker model labels match expected bindings.
- missing workers produce handoffs, not shell fallback.

## Definition Of Done

The Orchestrator-only product is done when this statement is true:

```text
For a fresh document-based IP, a user can type one goal into the right-side
Orchestrator chat and watch ATLAS import requirements, dispatch workers, gate
evidence, route failures, ask required questions, and either reach green or
stop with a precise visible blocker, without the operator running workflow
scripts manually.
```

Until then, be precise:

- "Orchestrator dispatch path works" is acceptable when jobs are created from
  chat.
- "Real Orchestrator loop works" requires decision/evidence/retry records.
- "UI product flow works" requires a visible browser-driven test.
- "Full signoff works" requires SYN/STA/PnR/PSTA evidence, not just RTL/sim.
