---
title: Locked Truth And Design Spec Workflow
type: proposal
tags: [ip-flow, requirements, locked-truth, ssot, design-spec, validation, todo, signoff]
updated: 2026-06-06
related: [evidence-contract-obligation-traceability, contract-reflection-workflow, workflow-feedback-and-scheduling, parallel-todo-sub-agent-workers]
---

# Locked Truth And Design Spec Workflow

This page captures the current ATLAS workflow direction from the APB timer and
MCTP assembler discussions.

The key decision is:

```text
Locked Truth is the authority.
Design Spec is a generator-ready projection of that authority.
```

Older ATLAS flows treated `yaml/<ip>.ssot.yaml` as the main source of truth.
That name is still useful for compatibility, but the meaning should change. The
canonical source of truth is the locked requirement bundle under `req/`. The
YAML file is a design/specification view that generators can consume.

## Problem

The agent can produce impressive artifacts, but it can also move too far before
the user has actually approved the engineering truth.

Examples:

```text
User: I need an MCTP assembler.
Agent: asks many questions, generates long drafts, runs tools, may start flow.
```

That is unsafe for IP design because the implementation can look complete while
the requirement authority is still ambiguous.

The desired flow is shorter and stricter:

```text
chat refinement
-> locked truth draft
-> explicit approval
-> deterministic lock writer
-> deterministic lock validator
-> design spec projection
-> implementation / verification stages
```

The agent may help draft and refine, but it must not call the result locked
until files exist and validators pass.

## Authority Model

### Locked Truth

Locked Truth is the human-approved, machine-readable authority for an IP or for
an individual requirement.

Canonical files:

```text
<ip>/req/requirements_index.json
<ip>/req/obligations.json
<ip>/req/contract_refs.json
<ip>/req/evidence_plan.json
<ip>/req/approval_manifest.json
```

Optional generated human-readable view:

```text
<ip>/req/locked_truth.md
```

These files answer:

```text
What did the user approve?
What exact requirements are locked?
What obligations came from each requirement?
What central and stage contracts bind those obligations?
What evidence will close each contract?
Who approved it, when, and with what hash?
```

### Design Spec

The Design Spec is a derived projection from Locked Truth. It is allowed to
reshape the truth into a form that generators understand:

```text
<ip>/yaml/<ip>.ssot.yaml
```

Long term, the schema should be named by meaning rather than history:

```text
schema: atlas.generator_design_spec.v1
authority: req/approval_manifest.json
```

The filename can remain `*.ssot.yaml` for compatibility, but the workflow should
not treat it as the authority.

The Design Spec answers:

```text
What ports, registers, state, parameters, and behavioral rules should generators use?
```

It must not answer:

```text
What truth was approved?
```

That answer belongs to Locked Truth.

## Trace Structure

The core trace is:

```text
REQ
-> OBL
-> CONTRACT_REF
-> STAGE_CONTRACT
-> EVIDENCE
-> VALIDATION
```

For a single requirement:

```text
REQ_TIMER_COUNT_001
  -> OBL_TIMER_DECREMENT_001
       -> CONTRACT_TIMER_COUNTDOWN
            -> SSOT/DESIGN_SPEC section
            -> FL expected rule
            -> CL timing rule
            -> RTL observable
            -> TB monitor/check
            -> SIM scoreboard row / VCD signal
            -> validator pass/fail/blocked
```

For a broader requirement:

```text
REQ
  |-> OBL_1 -> CONTRACT_1 -> EVIDENCE_1
  |-> OBL_2 -> CONTRACT_2 -> EVIDENCE_2
  `-> OBL_3 -> CONTRACT_3 -> EVIDENCE_3
```

A requirement is closed only when all required obligations are:

```text
pass
waived by explicit authority
or blocked with a recorded reason and owner
```

## Central Contract And Stage Contracts

The central contract is the stable, cross-stage identity for an obligation.

Example:

```text
CONTRACT_TIMER_BACKPRESSURE_STABLE
```

Stage contracts are stage-specific reflections of the central contract:

```text
Design Spec:
  output.valid_ready.stable_when_not_ready

FL:
  expected transfer does not advance without ready

CL:
  output beat holds across stalled cycles

RTL:
  tvalid && !tready |=> stable(tdata, tkeep, tlast)

TB:
  monitor records stall beat stability

SIM:
  VCD contains tvalid/tready/tdata/tkeep/tlast
  scoreboard event records stable-under-stall pass
```

The central contract prevents each stage from inventing a different
interpretation of the same obligation.

## Evidence Versus Artifact

An artifact is any generated output:

```text
RTL file
testbench file
VCD file
scoreboard JSONL
coverage report
lint report
formal report
```

Evidence is the part of an artifact that proves a contract.

Example:

```text
Artifact:
  sim/timer.vcd

Evidence:
  signal trace showing tdata/tkeep/tlast did not change while tvalid=1 and tready=0
```

Therefore the workflow should not stop at "VCD exists". A validator should read
the VCD, scoreboard, report, or manifest and decide whether the required
evidence exists.

## Validators

### Locked Truth Bundle Validator

The first deterministic gate is:

```text
workflow/req-gen/scripts/check_locked_truth_bundle.py
```

It checks:

```text
required files exist
approval manifest status is valid
file hashes match the manifest
requirements are locked or approved
obligations reference valid requirements
contracts reference valid obligations
evidence references valid contracts
```

This prevents the agent from saying "locked" when the canonical files were not
written or are stale.

### Design Spec Trace Validator

The Design Spec trace validator is:

```text
workflow/ssot-gen/scripts/check_design_spec_trace.py
```

It should check:

```text
Design Spec cites req/approval_manifest.json
Design Spec cites the approved locked truth bundle hash
each generated section has source_refs to REQ/OBL/CONTRACT
all must-level locked requirements are reflected
no Design Spec rule contradicts locked values
stage contract refs are present for downstream generators
```

This gate answers:

```text
Is the Design Spec actually derived from Locked Truth?
```

It does not decide whether the RTL works. It only decides whether the generator
input still reflects the approved authority.

### Evidence Validators

Later gates answer whether the implementation works:

```text
check_contract_reflection.py
check_evidence_contract.py
check_sim_evidence_freshness.py
check_ip_signoff.py
```

They should classify outcomes as:

```text
pass      observed and correct
fail      observed and wrong
blocked   missing definition, missing observable, stale artifact, or absent evidence
waived    explicitly excluded by human/spec authority
```

## Todo Harness

The todo system is the right harness for the MVP because it can combine:

```text
LLM drafting step
command gate
validator gate
repair loop
handoff step
```

Current MVP command:

```text
workflow/default/commands/locked-truth-finalize.json
workflow/default/todo_templates/locked-truth-finalize.json
workflow/req-gen/todo_templates/locked-truth-finalize.json
```

The template shape is:

```text
1. prepare locked_truth_draft.json
2. run lock_requirement_set.py
3. run check_locked_truth_bundle.py
4. handoff: locked truth is ready for Design Spec generation
```

The important control edge is:

```text
validator fail -> repair draft/writer input -> rerun writer -> rerun validator
```

This is not a pure DAG. It is a linear todo list with jump edges and repair
loops. That is acceptable for Locked Truth because the task should remain
serial and reviewable.

## Parallelism

Parallelism is useful later, but not for the lock itself.

Do not parallelize:

```text
final requirement approval
lock writer
locked truth bundle validator
```

These steps are authority-bearing and should be serial.

Parallelism can help after truth is locked:

```text
Design Spec reflection checks
FL model generation
RTL implementation exploration
TB scenario drafting
documentation projection
```

However, parallel owner workers must still route through deterministic gates.
The main orchestrator should not accept "looks good" from a worker as closure.

## Minimal Workflow

The minimum useful workflow is:

```text
1. User describes IP or requirement.
2. Default agent refines only the next missing decision.
3. If many decisions remain, agent offers grill-me or deep-interview.
4. Agent writes a draft object, not canonical locked files.
5. User explicitly approves final requirement set.
6. locked-truth-finalize command writes req/*.json and locked_truth.md.
7. check_locked_truth_bundle.py passes.
8. Agent or ssot-gen drafts Design Spec from locked truth.
9. check_design_spec_trace.py passes.
10. Implementation stages may run.
```

Normal chat should stay short:

```text
captured decisions
remaining blocker
next question
```

Full dumps should happen only when the user asks to review/export, or when
asking for final approval.

## Existing RTL Or Docs

Existing RTL, docs, or old SSOT files are candidate evidence, not authority.

When importing a legacy IP:

```text
legacy artifact
-> extract candidate requirement / obligation / contract
-> mark as draft_legacy_inferred
-> ask human to keep, update, or ignore
-> only then write locked truth
```

Do not mark a legacy-derived requirement locked just because RTL exists.

The legacy artifact can say:

```text
This is what the design appears to do.
```

Only Locked Truth can say:

```text
This is what the design is required to do.
```

## Design Spec Generation Strategy

Use a hybrid approach:

```text
LLM drafts Design Spec
scripts validate trace and consistency
LLM repairs only validator findings
```

Pure script generation is attractive, but it can become too rigid too early.
Pure LLM generation is flexible, but not trustworthy without deterministic
checks.

The MVP should therefore be:

```text
LLM writer + deterministic checker
```

Later, common sections can become deterministic skeletons:

```text
ports
register maps
reset defaults
interrupt expression
basic APB/AXI interface rules
```

The LLM can still fill architecture notes, corner-case explanations, and test
intent, but the checker remains the authority gate.

## Naming Guidance

Recommended conceptual names:

```text
Locked Truth Bundle:
  req/*.json

Design Spec:
  yaml/<ip>.ssot.yaml

Central Contract:
  req/contract_refs.json

Stage Contract:
  Design Spec / FL / CL / RTL / TB / SIM reflection of a central contract

Evidence Plan:
  req/evidence_plan.json

Evidence Artifact:
  sim/scoreboard_events.jsonl, sim/*.vcd, lint report, formal report, coverage JSON
```

The current `SSOT` label should be treated carefully:

```text
precise meaning:
  Locked Truth is the real SSOT.

compatibility meaning:
  yaml/*.ssot.yaml is the generator Design Spec.
```

## Implementation Backlog

Immediate:

```text
document locked-truth-finalize command usage
add check_design_spec_trace.py
add Design Spec source_refs schema
teach default prompt to ask short questions unless grill-me is requested
keep canonical req/*.json protected from ad hoc edits
```

Next:

```text
promote req-gen template globally if default command proves stable
add contract reflection from Design Spec to FL/CL/RTL/TB/SIM
add owner routing for blocked/fail evidence
add small APB timer fixture as reference IP
```

Later:

```text
parallel downstream owner workers
SSE/WebSocket progress feed for UI
validator-driven repair queues
formal evidence integration
VCD evidence parsers for signal-level proof
```

## Summary

The workflow should be:

```text
stage-driven execution
contract-driven signoff
owner-routed repair loop
```

But the foundation is:

```text
Locked Truth first.
Design Spec second.
Implementation third.
Evidence decides closure.
```
