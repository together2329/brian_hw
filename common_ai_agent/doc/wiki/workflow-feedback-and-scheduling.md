# Workflow Feedback And Scheduling

This page defines how common_ai_agent should run multiple IP workflows without
turning the system into either a slow serial script or an unsafe free-for-all.

## Core Concept

The pipeline has two separate concerns:

1. **Scheduling** decides which workflows can run now.
2. **Feedback** decides which owner workflow must repair a failed evidence gate.

Scheduling is about throughput. Feedback is about correctness.

## Worker-Aware Scheduling

The default schedule mode is `auto`.

```text
one worker URL      -> serial
multiple worker URLs -> DAG
```

The worker URL is the current proxy for worker capacity. If every workflow
resolves to the same `WORKER_URL_DEFAULT`, the scheduler should avoid starting
parallel jobs because one backend worker would receive competing long-running
tasks. If workflow-specific worker URLs exist, the scheduler can fan out ready
nodes.

This is an MVP heuristic, not a complete capacity model. One URL may front a
pool, and multiple URLs may still share the same physical backend. Production
scheduling should eventually use worker health/capacity metadata, but endpoint
count is a safe first guard against overloading a single local worker.

Explicit modes:

```text
schedule=auto   # choose serial or DAG from worker URLs
schedule=serial # one stage after the previous requested stage
schedule=dag    # dependency graph; ready stages run together
```

Serial mode is still dependency-aware. Requested stages are first sorted into
canonical pipeline order, then each selected stage waits for the previous
selected stage. This prevents unsafe orders such as `tb-gen` before `rtl-gen`
when a UI or script submits stages out of order.

## Dependency Graph

The intended DAG is:

```text
ssot-gen
  -> {fl-model-gen, cl-model-gen}
  -> equiv-goals
  -> rtl-gen
  -> {lint, tb-gen, syn}

tb-gen -> sim -> {coverage, sim-debug}
syn -> {sta, pnr}
pnr -> sta-post
all requested evidence -> goal-audit
```

Edges have different meanings:

```text
gate      downstream runs only when dependency passes
diagnose  downstream runs when dependency fails to classify the owner
summary   downstream can run after dependencies are terminal to report status
```

Examples:

```text
tb-gen -> sim        is a gate edge
sim -> sim-debug     is a diagnose edge when sim/scoreboard fails
all stages -> audit  is a summary edge, not only a success edge
```

The current MVP scheduler mostly implements gate edges. Diagnose and summary
edges are the next required step for automatic repair loops.

If a user requests a partial pipeline, a stage waits for the nearest selected
upstream ancestor. Example: `ssot,rtl` means `rtl` waits for `ssot` even though
`fl/cl/equiv` were omitted.

## Artifact Ownership

Each workflow owns its artifact boundary:

```text
ssot-gen       owns yaml/, req/, review decisions
fl-model-gen   owns model/, verify/, cov/*model plans
rtl-gen        owns rtl/, list/, rtl_contract.json
tb-gen         owns tb/, tc/, scoreboard harness
sim            owns sim execution evidence
sim-debug      owns mismatch classification
lint           owns lint reports and lint evidence
syn/sta/pnr    own EDA reports and handoff outputs
coverage       owns final coverage summaries
```

Workflows must not directly patch another workflow's owned artifacts. They
should write feedback.

## Feedback Packet

When a workflow fails because another workflow likely owns the root cause, it
emits a feedback packet:

```json
{
  "schema": "workflow_feedback.v1",
  "ip": "timer",
  "from_workflow": "sim-debug",
  "to_workflow": "rtl-gen",
  "severity": "blocking",
  "reason": "FL-vs-RTL mismatch",
  "evidence": [
    "sim/scoreboard_events.jsonl",
    "sim/timer.vcd",
    "verify/equivalence_goals.json"
  ],
  "expected": "count increments on TX_START",
  "observed": "count remains zero",
  "owner_confidence": "medium",
  "suggested_action": "repair RTL transaction accept path",
  "status": "pending"
}
```

Feedback is not approval. It is a repair request with evidence.

Recommended persistence:

```text
<ip>/feedback/<from_workflow>__to__<to_workflow>/<feedback_hash>.json
```

Where `feedback_hash` is derived from reason plus evidence digests. This keeps
repeated runs from creating duplicate pending feedback for the same mismatch.
The owner workflow should resolve feedback by writing a sibling resolved record
that references the artifact changes and fresh evidence.

## Repair Loop

The scheduler loop should behave like this:

```text
1. run ready workflows
2. collect stage results and feedback packets
3. if feedback has a clear owner, enqueue that owner workflow
4. mark downstream evidence stale when owner artifacts change
5. rerun only stale/blocked downstream stages
6. stop on pass, retry budget exhaustion, or human_review_needed
```

Example:

```text
sim-debug finds mismatch
  -> writes feedback to rtl-gen
rtl-gen reruns with evidence context
  -> modifies RTL
  -> lint, tb-gen, sim, coverage, syn, sta, pnr become stale
scheduler reruns ready stale stages
```

## Stale Invalidation

If an upstream owner changes artifacts, downstream evidence cannot be reused:

```text
SSOT changed -> FL, CL, equiv, RTL, TB, sim, coverage, EDA stale
FL/CL/equiv changed -> RTL, TB, sim, coverage stale
RTL changed -> lint, TB, sim, coverage, syn, sta, pnr stale
TB changed -> sim, coverage, sim-debug stale
syn changed -> sta, pnr, sta-post stale
pnr changed -> sta-post stale
```

The goal is to prevent "pass by stale evidence".

Implementation rule:

```text
stage_result records artifact_fingerprint for owned outputs
downstream stage records inputs_fingerprint for consumed upstream outputs
if upstream fingerprint changes, downstream result becomes stale
goal-audit refuses stale evidence
```

Until artifact fingerprints are wired in code, stale invalidation is a design
contract rather than a production guarantee.

## Modes

```text
interactive  ask humans for missing authority
auto-select  choose explicit safe/default SSOT answers for benchmark runs
pipeline     continue non-blocking work and collect human gates
ci           fail fast on blockers or missing evidence
```

`pipeline` mode should not hide failures. It should keep running independent
work while preserving feedback and human-review queues.

## Stop Conditions

The loop stops when one of these is true:

```text
all requested evidence is approved
a required stage fails in ci mode
retry budget is exhausted
owner cannot be classified
human authority is required
worker infrastructure is unavailable
```

Repair loops must also carry a retry budget:

```text
pipeline.attempts[stage_id] <= max_attempts
feedback.repair_depth <= max_repair_depth
```

When the budget is exhausted, the workflow should emit `human_review_needed`
rather than continuing to spend LLM calls.

## Why This Matters

This separates speed from correctness:

- DAG scheduling gives speed when workers exist.
- serial scheduling protects a single worker.
- feedback routes fixes to the right owner.
- stale invalidation prevents false pass.
- human review captures decisions automation should not guess.
