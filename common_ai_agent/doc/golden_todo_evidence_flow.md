# Golden Todo Evidence Flow

This document records the intended long-term control model for SSOT-driven IP
generation. The short version:

```text
LLM = worker
TodoTracker = state machine
validator/audit = judge
human review = product/spec authority
```

The goal is to keep one workflow model across GPT, Cursor CLI, Claude CLI, GLM,
Kimi, DeepSeek, and future providers. Provider-specific code should normalize
model output only; it should not define approval semantics.

For the broader end-to-end user and multi-agent operating guide, see
[`ai_driven_ip_development_guide.md`](ai_driven_ip_development_guide.md).
For cross-linked wiki navigation, start at [`wiki/index.md`](wiki/index.md),
especially [`wiki/golden-todo-evidence.md`](wiki/golden-todo-evidence.md) and
[`wiki/workflow-ownership-and-boundaries.md`](wiki/workflow-ownership-and-boundaries.md).

## Core Principle

Every stage owns a golden todo ledger derived from the approved SSOT or from the
previous stage's approved evidence.

```text
SSOT -> FL model -> CL model -> RTL -> TB -> sim/debug -> lint -> coverage
```

Each stage can ask an LLM to author artifacts, but the stage is approved only
when its required todo ledger closes with evidence.

```text
LLM says "done"        -> completed / approval_requested
validator proves done  -> approved
validator fails        -> rejected
human decision needed  -> human_review_needed
```

LLM `reason` is still valuable, but it is not the default approval authority.
It explains intent and repair history. Approval comes from evidence unless a
todo explicitly opts into a weaker policy.

During pipeline tests, do not manually patch generated IP artifacts to satisfy
todo criteria. Route the repair through the owning workflow and let the ledger
plus validator decide whether the row closes.

## Approval Policies

Default policy:

```text
approval_policy = evidence_required
```

Supported policies:

| Policy | Use | Approval authority |
| --- | --- | --- |
| `evidence_required` | RTL, SSOT, FL/CL model, TB, sim, lint, coverage, EDA reports | deterministic validator or audit |
| `human_review_required` | product intent, architecture choice, waiver, performance tradeoff, safety/security decision | user or approved review card |
| `llm_reason_allowed` | low-risk docs, comments, explanation, simple non-behavioral cleanup | LLM reason plus optional reviewer check |

If the policy is unknown, treat it as `evidence_required`. If evidence cannot be
produced and the decision is semantic, move the item to `human_review_needed`.

## Todo States

Recommended state set:

```text
pending
in_progress
completed
approval_requested
approved
rejected
human_review_needed
blocked
```

Meaning:

- `completed`: the worker produced or changed artifacts.
- `approval_requested`: the worker claims the criteria are met and points at
  evidence or reasons.
- `approved`: the configured approval authority accepted it.
- `rejected`: evidence exists and shows the criteria are not met.
- `human_review_needed`: the system cannot decide without a human product/spec
  decision. This is not a failure.
- `blocked`: required input/artifacts are missing before work can proceed.

## Artifact Envelope

Model output should be normalized into a provider-independent envelope at stage
handoff points. Free-form chat is fine inside a conversation, but artifact
handoff should be structured.

Example:

```json
{
  "schema_version": "workflow_artifact.v1",
  "workflow": "rtl-gen",
  "ip": "dma",
  "todo_id": "RTL-0021",
  "result": "completed",
  "files": [
    {
      "path": "dma/rtl/dma_core.sv",
      "kind": "rtl",
      "content": "..."
    }
  ],
  "claims": [
    "Implements function_model.transactions.FM_DESCRIPTOR_FETCH",
    "Implements cycle_model.pipeline.DESCRIPTOR_FETCH"
  ],
  "human_gate": null,
  "notes": [
    "Descriptor fetch FSM and datapath were implemented."
  ]
}
```

Providers may wrap or decorate output differently. Adapters must normalize raw
provider output into the same envelope before the workflow writes files or
updates todo state.

## Stage Ledgers

Each stage should have an explicit ledger and a summary gate.

```text
<ip>/ssot/ssot_todo_plan.json          # future
<ip>/model/fl_todo_plan.json           # future
<ip>/model/cl_todo_plan.json           # future
<ip>/rtl/rtl_todo_plan.json            # current reference pattern
<ip>/tb/tb_todo_plan.json              # future
<ip>/sim/sim_todo_plan.json            # future
<ip>/lint/lint_todo_plan.json          # future
<ip>/cov/coverage_todo_plan.json       # future
```

The current `rtl_todo_plan.json` is the reference implementation of the pattern:

- source refs are derived from SSOT sections;
- required tasks carry criteria and owner hints;
- audit writes `todo_completion.status`;
- the stage passes only when all required todo rows pass.

The existing `rtl_todo_tracker.json` is the execution view for the flat
TodoTracker. It may start rows as `pending` for interactive review. Pipeline/CI
mode should eventually sync audit pass results back into the tracker and
`.session` todo state so UI status matches the golden ledger.

## Cross-Stage Traceability

SSOT refs must propagate across the whole pipeline.

Example source ref:

```text
function_model.transactions.FM_ACCEPT
```

Expected downstream trace:

```text
SSOT FM_ACCEPT
  -> FL model transaction
  -> CL model timing/handshake row
  -> RTL implementation todo
  -> TB scoreboard/checker todo
  -> sim scenario result
  -> function coverage bin
  -> coverage closure row
```

Cycle-model refs follow the same pattern:

```text
cycle_model.pipeline.S1_EMIT
  -> CL model cycle behavior
  -> RTL sequential/state evidence
  -> TB assertion/checker
  -> sim hit
  -> cycle coverage bin
```

## Coverage Strategy

FL and CL items must be visible in RTL-based coverage.

Two evidence layers are required:

1. Static RTL evidence
   - The RTL contains real implementation structure for the SSOT ref.
   - Examples: signal use, state update, FSM transition, sequential logic,
     output drive, protocol handshake logic.
   - Static evidence proves implementation presence, not correctness.

2. Dynamic RTL-observed coverage
   - Simulation observes the behavior and checkers/scoreboards pass.
   - Function coverage maps to `function_model`.
   - Cycle coverage maps to `cycle_model`, including latency, handshake,
     ordering, backpressure, depth, outstanding, pipelining, frequency, and
     throughput targets.

Suggested outputs:

```text
cov/static_coverage.json
cov/function_coverage.json
cov/cycle_coverage.json
cov/coverage_traceability.json
```

Example row:

```json
{
  "source_ref": "cycle_model.latency.result_valid",
  "static_evidence": {
    "status": "covered",
    "rtl_files": ["rtl/timer.sv"],
    "signals": ["result_valid"],
    "logic_evidence": ["sequential update found"]
  },
  "cycle_coverage": {
    "status": "covered",
    "scenario": "TC_ACCEPT_LATENCY",
    "assertion": "accept_to_result_valid_1cycle",
    "hits": 12
  }
}
```

## Human Review Queue

Human review items should be collected separately from rejected work.

Use `human_review_needed` when:

- the SSOT requirement is ambiguous;
- a waiver is needed;
- a performance or architecture tradeoff cannot be proven by tests;
- security/safety intent changes;
- a coverage goal is unreachable and needs product approval;
- a model proposes changing FL/CL/SSOT authority to make downstream pass.

The review card should include:

```json
{
  "status": "human_review_needed",
  "decision_needed": "Choose DMA descriptor width",
  "source_refs": ["function_model.transactions.FM_DESCRIPTOR_FETCH"],
  "options": [
    {"label": "32-bit descriptor", "effect": "smaller RTL, limited address range"},
    {"label": "64-bit descriptor", "effect": "larger address range, wider datapath"}
  ],
  "recommended_default": {
    "label": "64-bit descriptor",
    "why": "More reusable for DMA-class IP"
  }
}
```

## Relationship To Existing Docs

- `workflow/COMMON_ENGINE_FLOW.md`
  - The canonical stage order and engine boundary.
  - This document defines the approval/ledger policy used inside that flow.

- `doc/ip_workflow_guide.md`
  - Operator guide for running the flow.
  - This document explains why stage todo ledgers and evidence gates exist.

- `workflow/rtl-gen/RTL_GEN_FLOW.md`
  - RTL-specific implementation of the golden todo pattern.
  - `rtl_todo_plan.json` is the current reference ledger.

- `workflow/coverage/system_prompt.md`
  - Coverage workflow prompt.
  - Should use this document's split between static evidence, function
    coverage, and cycle coverage.

- `doc/workflow_long_term_improvements.md`
  - Backlog and known gaps.
  - Stage ledger rollout should be tracked there as implementation work.

## Migration Plan

1. Keep `rtl_todo_plan.json` as the reference golden ledger.
2. Add explicit `approval_policy`, `required_evidence`, and
   `fallback_if_no_evidence` fields to ledger tasks.
3. Sync audit-approved ledger rows into TodoTracker/UI state in pipeline/CI
   mode, while preserving interactive review behavior where needed.
4. Add FL-model and CL-model ledgers derived from SSOT `function_model` and
   `cycle_model`.
5. Add TB, sim, lint, and coverage ledgers that consume upstream approved
   evidence.
6. Add cross-stage traceability summaries so one SSOT ref can be followed from
   SSOT through RTL-observed coverage.
7. Collect `human_review_needed` items into a single review queue instead of
   treating them as ordinary rejection failures.
