---
title: Evidence Contract And Obligation Traceability
type: proposal
tags: [ip-flow, ssot, verification, evidence, signoff, cocotb, truth-coverage]
updated: 2026-06-02
related: [truth-coverage-gate, general-ip-flow-trial-and-error-20260601, mctp-assembler-scratch-flow-20260531, workflow-ownership-and-boundaries]
---

# Evidence Contract And Obligation Traceability

This page records the next workflow improvement after the MCTP assembler scratch trial.

The problem is not just generating RTL or running cocotb. The hard part is:

```text
How do we prove that a broad requirement is covered by the exact scenario,
monitor, observable, pass condition, and scoreboard row that should prove it?
```

## Current Structure

The current local signoff structure is:

```text
STAGE_MANIFEST
-> SSOT
-> FL / CL / equivalence_goals
-> ip_contract
-> cocotb TB / scoreboard_events
-> coverage
-> truth_coverage
-> ip_signoff
```

Representative artifacts:

```text
<ip>/yaml/<ip>.ssot.yaml
<ip>/model/functional_model.py
<ip>/model/cycle_model.py
<ip>/verify/equivalence_goals.json
<ip>/verify/ip_contract.json
<ip>/tb/cocotb/
<ip>/sim/scoreboard_events.jsonl
<ip>/cov/coverage.json
<ip>/signoff/truth_coverage.json
<ip>/signoff/ip_signoff.json
```

The current link is mostly built from:

```text
goal_id
scenario_id
coverage_refs
ssot_refs
rtl_observed
fl_expected
passed
```

This is useful, but it is still goal/scenario centered. It does not yet make
atomic requirement obligations a first-class artifact.

## Current Gap

For a broad requirement like:

```text
Support interleaved MCTP assembly.
```

The current workflow can often say:

```text
SC_INTERLEAVE_TWO_Q_COMPLETE ran.
The scoreboard row passed.
The coverage bin was hit.
truth_coverage found a matching token.
```

That is not the same as proving the precise engineering claim:

```text
Q0 and Q1 payload order remained independent.
Q0 and Q1 descriptors used the correct context.
The context key used the approved source/destination/tag fields.
The SRAM address ranges did not overlap.
First/last TLP headers did not cross contexts.
```

The missing layer is:

```text
Atomic obligation
-> required scenario
-> required observable
-> explicit pass condition
-> exact evidence row
```

## Proposed Artifact

Add a first-class artifact:

```text
<ip>/verify/evidence_contract.json
```

Placement in the workflow:

```text
SSOT
-> ip_contract
-> evidence_contract
-> equivalence_goals / cocotb / monitors
-> scoreboard_events
-> coverage
-> truth_coverage
-> signoff
```

`ip_contract` answers:

```text
What kind of IP is this and what verification capabilities are required?
```

`evidence_contract` answers:

```text
For each important claim, what exact executable evidence proves it?
```

## Evidence Contract Schema

Proposed top-level shape:

```json
{
  "schema_version": 1,
  "type": "evidence_contract",
  "ip": "mctp_assembler_scratch",
  "source_of_truth": "yaml/mctp_assembler_scratch.ssot.yaml",
  "obligations": []
}
```

Each obligation should be small enough that a reviewer can decide whether the
listed evidence really proves the claim.

```json
{
  "obligation_id": "OBL_INTERLEAVE_002",
  "requirement_refs": [
    "test_requirements.scenarios.SC_INTERLEAVE_TWO_Q_COMPLETE"
  ],
  "claim": "Interleaved Q0/Q1 fragments preserve per-Q payload order.",
  "required": true,
  "owner": "tb-gen",
  "scenario_ids": [
    "SC_INTERLEAVE_TWO_Q_COMPLETE"
  ],
  "required_observables": [
    "debug_context_id",
    "debug_context_key",
    "sram_write_addr",
    "sram_write_data",
    "sram_write_strb",
    "descriptor_qid",
    "descriptor_len",
    "readback_data_out"
  ],
  "pass_conditions": [
    {
      "id": "q0_payload_matches_fl",
      "kind": "scoreboard_compare",
      "left": "rtl_observed.q0_payload_readback",
      "right": "fl_expected.q0_payload"
    },
    {
      "id": "q1_payload_matches_fl",
      "kind": "scoreboard_compare",
      "left": "rtl_observed.q1_payload_readback",
      "right": "fl_expected.q1_payload"
    },
    {
      "id": "q_ranges_do_not_overlap",
      "kind": "predicate",
      "expr": "q0_sram_range does not overlap q1_sram_range"
    }
  ],
  "evidence_rows": [
    {
      "artifact": "sim/scoreboard_events.jsonl",
      "match": {
        "goal_id": "EQ_SCENARIO_SC_INTERLEAVE_TWO_Q_COMPLETE",
        "scenario_id": "SC_INTERLEAVE_TWO_Q_COMPLETE",
        "passed": true
      }
    }
  ]
}
```

The schema should also allow optional or deferred obligations:

```json
{
  "obligation_id": "OBL_FORMAL_NO_DESC_BEFORE_EOM",
  "claim": "Descriptor publication cannot occur before EOM.",
  "required": false,
  "status": "optional",
  "owner": "formal",
  "reason": "Formal workflow is documented but not a local scratch signoff gate yet."
}
```

## Scoreboard Row Extension

The scoreboard row should explicitly name which obligations it satisfies.

Current useful fields:

```json
{
  "goal_id": "EQ_SCENARIO_SC_INTERLEAVE_TWO_Q_COMPLETE",
  "scenario_id": "SC_017_EQ_SCENARIO_SC_INTERLEAVE_TWO_Q_COMPLETE",
  "coverage_refs": ["SC_INTERLEAVE_TWO_Q_COMPLETE_executed"],
  "fl_expected": {},
  "rtl_observed": {},
  "passed": true
}
```

Proposed additional fields:

```json
{
  "obligation_ids": [
    "OBL_INTERLEAVE_001",
    "OBL_INTERLEAVE_002"
  ],
  "condition_results": {
    "q0_payload_matches_fl": true,
    "q1_payload_matches_fl": true,
    "q_ranges_do_not_overlap": true
  },
  "observed_contract": {
    "required_observables_present": true,
    "missing_observables": []
  }
}
```

Then `truth_coverage` can stop relying mainly on normalized evidence tokens and
instead check the contract directly:

```text
For each required obligation:
  scenario executed?
  required observables present?
  pass conditions evaluated?
  condition results all true?
  scoreboard row passed?
```

## MCTP Example Obligations

The MCTP assembler should not have one giant "interleaving works" obligation.
It should be split into small claims.

### Interleaving

```text
OBL_INTERLEAVE_001:
  Two contexts with different message tags can be active at the same time.

OBL_INTERLEAVE_002:
  Q0/Q1 payload order is preserved during interleaved fragments.

OBL_INTERLEAVE_003:
  First and last TLP headers are retained per context and do not cross contexts.

OBL_INTERLEAVE_004:
  A drop/error in one Q does not corrupt another active Q.
```

### Context Key

```text
OBL_CONTEXT_KEY_001:
  Context lookup uses the approved key fields.

OBL_CONTEXT_KEY_002:
  If the approved key is source EID + destination EID + tag owner + message tag,
  destination EID must be present in the observable context key or equivalent
  compare evidence.
```

This is important because a scenario can pass even when the key is incomplete
unless the scenario specifically collides on the missing key field.

### SRAM Packing

```text
OBL_SRAM_PACK_001:
  SRAM stores only MCTP payload bytes, not TLP headers.

OBL_SRAM_PACK_002:
  Payload bytes are packed contiguously across 256-bit SRAM words.

OBL_SRAM_PACK_003:
  Fragment lengths not aligned to 32B do not create holes.

OBL_SRAM_PACK_004:
  The final short fragment writes only valid byte lanes.
```

Required observables should include:

```text
sram_write_addr
sram_write_data
sram_write_strb
payload_len
fragment_index
descriptor_len
readback_data_out
```

### Descriptor Ordering

```text
OBL_DESC_001:
  Descriptor is published only after EOM.

OBL_DESC_002:
  Descriptor is published only after all pending SRAM packer writes are accepted.

OBL_DESC_003:
  Descriptor length equals assembled payload byte count.
```

This catches a weakness that a simple EOM-based descriptor check can miss.

### Drop Behavior

```text
OBL_DROP_001:
  Packet drop does not write SRAM.

OBL_DROP_002:
  Packet drop increments packet drop counter and records reason.

OBL_DROP_003:
  Assembly drop clears or errors only the affected Q.

OBL_DROP_004:
  Assembly drop increments per-reason assembly drop counters.
```

### Register And Interrupt Behavior

```text
OBL_REG_001:
  Each Q exposes idle/assembling/error state.

OBL_REG_002:
  Each Q exposes SRAM base address.

OBL_REG_003:
  Debug/control/status/interrupt registers are separated.

OBL_IRQ_001:
  Message complete interrupt is sticky until the approved clear operation.

OBL_IRQ_002:
  Drop/error interrupt records the matching cause.
```

## Human And LLM Roles

The LLM can draft `evidence_contract.json` from SSOT, but it should not silently
decide that the split is sufficient.

Human-owned:

```text
Which claims are required?
Is the obligation split sufficient?
Do the pass conditions really prove the claim?
Are optional/deferred items acceptable?
```

LLM/tool-owned:

```text
Generate candidate obligations from SSOT.
Generate cocotb scenarios and monitors from the contract.
Emit scoreboard rows with obligation_ids and condition_results.
Classify missing evidence.
Patch RTL/TB when executable evidence fails.
```

## Validation Rules

A future checker should fail if:

```text
required obligation has no scenario_ids
required obligation has no required_observables
required obligation has no pass_conditions
scoreboard row claims an unknown obligation_id
required observable is absent from rtl_observed
pass condition is not evaluated in condition_results
condition_results has false for a required pass condition
obligation is covered only by coverage token, with no passing scoreboard row
```

It should warn if:

```text
an obligation is too broad
too many obligations point to the same shallow row
mutation survivors map to an obligation whose monitors are weak
an obligation relies only on debug-only signals that may be removed
```

## Judging Implementation Quality

`evidence_contract` is not only for signoff bookkeeping. It is also the practical
way to judge whether the implementation is good.

A good implementation is not proven by one green signal. It needs three layers:

```text
correctness:
  RTL behavior matches the locked FL/expected model for required obligations.

coverage:
  Important functional, error, boundary, backpressure, and readback situations
  were actually exercised.

robustness:
  If likely RTL bugs are injected, the monitors and scoreboard catch them.
```

For each obligation, quality should be judged with this checklist:

```text
requirement split:
  Is the original requirement decomposed into small enough obligations?

verification method:
  Does each obligation have scenarios, observables, and pass conditions?

execution:
  Did cocotb or another executable test actually drive the scenario?

observation:
  Did the monitor observe DUT signals/data, not copied FL expected values?

comparison:
  Did the scoreboard compare RTL-observed results against FL/expected results?

corner coverage:
  Are boundary, drop/error, interleave, backpressure, and final-partial cases hit
  when relevant to the IP?

negative pressure:
  Do mutation results, assertions, or targeted bug injections show that the test
  would fail if the RTL were wrong?

RTL structure:
  Does the module structure naturally express the requirement, or is the behavior
  only forced to pass a narrow test?
```

For the MCTP assembler, an implementation-quality review should ask:

```text
context key:
  Does the RTL use the approved key fields, including destination EID if required?

SRAM packing:
  Does the packer prove no holes across 256-bit words and final short fragments?

descriptor ordering:
  Is descriptor publication tied to SRAM write acceptance/flush, not just EOM?

Q FSM:
  Does each Q independently represent idle, assembling, complete, and error?

drop isolation:
  Does a drop/error in one Q avoid corrupting another active Q?

firmware readback:
  Does AXI readback return exactly the assembled payload byte count?
```

The resulting quality labels should be explicit:

```text
local evidence pass:
  Required local executable gates pass.

engineering review pass:
  RTL structure and evidence-contract coverage are judged sufficient for the
  stated local scope.

production signoff blocked:
  External standard conformance, CDC, synthesis/PPA, DFT, STA, formal, or human
  approval is not complete.

production signoff pass:
  Project-defined production gates and human approvals are complete.
```

This prevents a common mistake:

```text
18/18 local gates pass != production IP is complete
```

For MCTP today, the honest label is:

```text
local evidence pass
engineering review partial
production signoff blocked
```

## Operational Minimum

The full quality checklist is useful, but it is too heavy as the default mental
model. For day-to-day General IP work, start with four questions:

```text
1. Correctness:
   Does RTL output/readback match the FL or expected model?

2. Coverage:
   Were the important scenarios actually executed?

3. Test strength:
   If we inject a likely RTL bug, does the test fail?

4. Human RTL review:
   Does the RTL structure look natural for the requirement, with no blocker?
```

For MCTP, the same four questions become:

```text
1. Correctness:
   Does assembled payload/readback match FL expected payload?

2. Coverage:
   Did we run single, multi-fragment, interleaved, drop, boundary, final-short,
   backpressure, register, interrupt, and AXI readback scenarios?

3. Test strength:
   If context keying, SRAM write strobes, descriptor timing, or drop isolation
   are broken, does cocotb/scoreboard/mutation catch it?

4. Human RTL review:
   Are Q FSM, context table, SRAM packer, descriptor queue, and read path
   responsibilities clear enough to maintain?
```

This is the practical default:

```text
PASS judgment baseline:
  1. RTL observed behavior matches expected.
  2. Important scenarios ran.
  3. Tests can fail when realistic bugs are injected.
  4. RTL review has no blocker for the claimed scope.
```

Use the larger evidence-contract checklist only when one of these four questions
is ambiguous, the IP is broad, or production claims are being considered.

## Stage Placement

Proposed new stages:

```text
derive_evidence_contract:
  input:
    <ip>/yaml/<ip>.ssot.yaml
    <ip>/verify/ip_contract.json
    <ip>/verify/equivalence_goals.json
  output:
    <ip>/verify/evidence_contract.json

check_evidence_contract:
  input:
    <ip>/verify/evidence_contract.json
    <ip>/sim/scoreboard_events.jsonl
    <ip>/cov/coverage.json
  output:
    <ip>/signoff/evidence_contract_coverage.json
```

`truth_coverage` should eventually read `evidence_contract_coverage.json` and
treat it as stronger evidence than token matching.

## Adoption Plan

Do not replace the current workflow in one jump.

Level 0, current:

```text
equivalence_goals + scoreboard rows + truth_coverage token matching
```

Level 1:

```text
emit evidence_contract.json for scenario obligations only
scoreboard rows include obligation_ids
checker verifies row presence and pass=true
```

Level 2:

```text
checker verifies required_observables and condition_results
truth_coverage consumes evidence_contract_coverage.json
```

Level 3:

```text
contract-driven reusable cocotb monitors
mutation survivors classified by obligation
optional formal properties linked to obligations
```

This keeps small IPs lightweight while giving broad IPs, such as MCTP, the
traceability needed to avoid ambiguous green signoff.

## Why This Is Not A Static Profile

Static profiles say:

```text
This is an AXI/FIFO/SPI/UART IP, so run this fixed checklist.
```

That is too rigid for General IP.

`evidence_contract` says:

```text
Given this IP's locked SSOT, these are the exact claims and evidence needed.
```

The contract is derived from the IP's own SSOT, then reviewed. It is not a
predefined profile.

## Stop Condition

Local signoff should be allowed to say:

```text
All required evidence-contract obligations are covered by passing executable evidence.
```

It should not say:

```text
The IP is production complete.
```

Production signoff still needs whatever the project requires, such as standard
conformance review, CDC, synthesis, PPA, DFT, STA, formal, and human approval.
