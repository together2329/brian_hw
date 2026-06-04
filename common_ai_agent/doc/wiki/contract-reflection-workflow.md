---
title: Contract Reflection Workflow
type: concept
tags: [ip-flow, ssot, evidence, fl, cl, rtl, tb, signoff, mctp]
updated: 2026-06-04
related: [evidence-contract-obligation-traceability, truth-coverage-gate, general-ip-flow-trial-and-error-20260601, mctp-assembler-scratch-flow-20260531, workflow-ownership-and-boundaries]
---

# Contract Reflection Workflow

This page captures the next design layer after `truth_coverage` and
`evidence_contract`: every important contract item must be reflected through
FL, CL, RTL, TB, and simulation evidence with the same stable ID.

The goal is not to trust that each stage "implemented the intent." The goal is
to make each stage say, in machine-readable form:

```text
I implemented / checked / observed this exact contract_ref here.
```

The full workflow is a closed loop:

```text
lock truth
-> derive contract refs and obligations
-> reflect them into FL / CL / RTL / TB
-> run cocotb/pyuvm and collect scoreboard + wave evidence
-> close covered obligations
-> route missing or failing evidence back to the owning workflow
-> repeat until pass, explicit waiver, human decision, or retry-budget stop
```

This is the practical meaning of "evidence-required" IP development. The
workflow is not done when code exists; it is done only when locked truth is
covered by fresh executable evidence or deliberately escalated.

## Six-Layer Model

The contract workflow has six layers:

```text
Requirement
-> Obligation
-> Contract Ref
-> Stage Reflection
-> Evidence
-> Validation / Closure
```

`SC_SINGLE`, `SC_BACKPRESSURE`, `SC_INTERLEAVE_Q`, and similar names are
scenarios. A scenario is not the requirement itself. It is one execution slice
used to prove one or more obligations.

### 1. Requirement

A requirement is locked truth: the user, spec, or SSOT-authorized claim that
downstream artifacts are trying to implement.

```text
REQ_MCTP_PAYLOAD_ASSEMBLY:
  MCTP payload bytes shall be assembled into SRAM without header corruption.
```

Problem addressed:

```text
Natural-language requirements are meaningful to people but hard for machines to
judge. If an LLM silently rewrites or completes them, locked truth becomes an
LLM opinion.
```

Improvement:

```text
Give every locked claim a stable requirement_id, source, status, and owner.
If the locked claim changes, downstream evidence becomes stale.
```

Current readiness:

```text
pilot-ready:
  semantic_contracts.json can carry requirement IDs and locked semantic slices.

not complete:
  every MCTP requirement is not yet normalized into this structure.
```

### 2. Obligation

An obligation is the machine-checkable split of a requirement.

```text
OBL_PAYLOAD_COUNT:
  payload count matches accepted payload bytes

OBL_SRAM_PACK:
  SRAM write contains payload bytes with contiguous strobes

OBL_DESCRIPTOR_VISIBLE:
  descriptor becomes visible after message completion
```

Problem addressed:

```text
"SRAM packing works" is too large. A single broad pass can hide holes such as
wrong final strobe, early descriptor publish, stale APB readback, or context
mixing.
```

Improvement:

```text
Split each required claim into obligations with scenario_ids, observables, and
pass conditions.
```

Current readiness:

```text
pilot-ready:
  MCTP v3 SC_SINGLE has three semantic obligations.

not complete:
  multi-context, >32B payload, backpressure stress, APB-after-update, and
  error/drop cases still need broader semantic splits.
```

### 3. Contract Ref

A `contract_ref` is the stable identity that ties the same meaning across
SSOT, FL, CL, RTL, TB, and simulation evidence.

```text
STATE_PAYLOAD_COUNT
MEM_SRAM_PAYLOAD_PACK
DESC_PUBLISH_VISIBLE
ORDER_DESCRIPTOR_AFTER_SRAM_FLUSH
APB_Q_PAYLOAD_COUNT_VISIBILITY
```

Problem addressed:

```text
Each stage can use different names. Without a shared ID, the workflow cannot
prove that SSOT payload count, FL expected count, RTL signal, TB monitor, and
scoreboard row are about the same contract.
```

Improvement:

```text
Attach the same contract_ref to every stage reflection and evidence row.
```

Current readiness:

```text
pilot-ready:
  contract_reflection can check declared contract_refs.

not complete:
  generators do not yet emit contract_refs automatically through every stage.
  The current MCTP v3 semantic layer is an overlay, not full propagation.
```

### 4. Stage Reflection

Stage reflection states where a contract is defined, implemented, driven,
observed, and checked.

```text
SSOT:
  function_model.state_variables.payload_byte_count

FL:
  FunctionalModel expected calculation

CL:
  latency, order, hold, visibility rule

RTL:
  owner module and observable signal/register/debug path

TB:
  scenario, driver, monitor, sampled observable

SIM:
  scoreboard row, VCD/FST artifact, validator result
```

Problem addressed:

```text
"ssot/fl/cl/rtl/tb/sim ran" does not prove every stage carried the same
meaning. TB can pass without sampling the required observable unless the
reflection is explicit.
```

Improvement:

```text
Missing SSOT/FL/CL/RTL/TB/SIM reflection is blocked or failed, not silently
accepted.
```

Current readiness:

```text
pilot-ready:
  check_contract_reflection.py validates the declared reflection chain.

not complete:
  reflection is not yet mandatory for every common-engine stage.
```

### 5. Evidence

Evidence is the executable proof that a required obligation was observed and
checked.

```text
scoreboard row
rtl_observed
fl_expected
condition_results
VCD/FST event order
artifact hashes and freshness
```

Problem addressed:

```text
Legacy scoreboard evidence centered on goal_id, scenario_id, and passed=true.
That is useful but shallow: it can hide why the row passed, which obligation it
closed, whether FL expected values were used, and whether the evidence is stale.
```

Improvement:

```text
Rows and validators should carry obligation_ids, contract_refs,
condition_results, FL/CL-derived expected values, VCD/FST observations, and
freshness.
```

Current readiness:

```text
pilot-ready:
  observed_equals_fl_expected, row_passed_with_fl_expected, and vcd_event_order
  exist.

not complete:
  scoreboard generation does not yet emit semantic fields natively for every
  row, and sim rerun/freshness is not yet a full workflow gate.
```

### 6. Validation / Closure

Validation is deterministic pass/fail/blocked judgement.

```text
schema valid?
required obligation exists?
expected came from FL/CL?
observable present?
condition_results true?
VCD order holds?
artifact fresh?
```

Problem addressed:

```text
An LLM saying "this looks correct" is not executable evidence. Missing
observables, weak pass conditions, and stale artifacts must become machine
failures or blocked owner routes.
```

Improvement:

```text
Validators judge closure. LLMs may author, repair, review, and explain, but
validator artifacts determine pass/fail. Human/spec authority decides locked
truth, waivers, and production claims.
```

Current readiness:

```text
pilot-ready:
  run_contract_check.py supports strict semantic closure and owner-route output.

not complete:
  orchestrator repair loops are not yet guaranteed to automatically consume
  every owner route and rerun the owning stage to closure.
```

## Required Improvements

These are the practical migration items from a working pilot into a v2 workflow.

Must-have items:

```text
contract_ref automatic propagation:
  Problem:
    overlays depend on humans or agents keeping IDs aligned
  Improvement:
    SSOT gen, FL/CL, RTL, TB, and sim emit the same IDs by construction
  Current status:
    pilot overlay exists; generator propagation remains

FL/CL-derived expected values:
  Problem:
    hardcoded expected constants can recreate fake green
  Improvement:
    expected values are produced by locked FL/CL models where possible
  Current status:
    MCTP v3 semantic slice uses FL-derived predicates for key fields

semantic scoreboard fields:
  Problem:
    passed=true does not explain which requirement predicate closed
  Improvement:
    rows carry obligation_ids, contract_refs, and condition_results directly
  Current status:
    validator can check these concepts; native row emission is still partial

stale evidence prevention:
  Problem:
    old scoreboard/VCD can be reused after RTL/TB/SSOT changes
  Improvement:
    hashes, provenance, or mandatory rerun make stale evidence fail
  Current status:
    semantic overlay artifacts now carry semantic_source_fingerprint and direct
    evidence/reflection validators reject stale semantic artifacts; simulator
    rerun freshness for RTL/TB/VCD still remains

owner routing:
  Problem:
    fail/blocked evidence can leave the user guessing where to repair
  Improvement:
    validator output routes to ssot-gen, fl-model-gen, rtl-gen, tb-gen, sim,
    sim-debug, contract-reflection, or human review
  Current status:
    route artifacts exist; automatic orchestrator repair loop remains
```

Should-have items:

```text
VCD/FST validator expansion:
  add latency, hold, backpressure, flush ordering, and APB visibility windows

risk scenario expansion:
  add SC_OVER_32B, SC_INTERLEAVE_Q, SC_BACKPRESSURE, SC_DESCRIPTOR_FLUSH,
  SC_APB_VISIBILITY, SC_DROP_ERROR, and reset/error variants

orchestrator repair loop:
  read owner route, launch the owner worker/stage, rerun validators, and stop
  only on pass, blocked human gate, waiver, or retry budget

validator negative tests:
  prove wrong scoreboard rows, missing observables, stale artifacts, and bad
  VCD order actually fail

LLM reviewer layer:
  flag weak obligation splits, missing scenarios, shallow monitors, or
  suspicious green evidence without becoming the final judge
```

## Human, LLM, And Validator Roles

Human/spec authority owns locked truth:

```text
approve requirements
approve obligation split
approve waivers
resolve spec ambiguity
authorize production-level claims
```

LLM owns authorship, analysis, and review:

```text
draft requirement splits
generate contract_ref candidates
write FL/CL/RTL/TB/checker code
triage failing evidence
suggest owner routes
review weak contracts or shallow monitors
```

LLM must not own final approval:

```text
do not approve signoff by confidence
do not replace missing evidence with prose
do not weaken expected values to match RTL
do not decide waivers or spec authority
```

Deterministic validators own closure:

```text
check schema
check source provenance
check required observable presence
check FL/CL expected versus RTL observed
check VCD/FST predicates
check freshness when available
emit pass/fail/blocked plus owner route
```

The target operating model is:

```text
Human:
  truth authority

LLM:
  author, repairer, reviewer, triage assistant

Validator:
  pass/fail judge

Workflow/orchestrator:
  executes owner routes and reruns evidence until closure or escalation
```

## Stale Evidence Prevention Slice

The first must-have item picked up from the v2 migration list is semantic source
freshness.

Problem:

```text
verify/semantic_contracts.json can change after generated
requirements_index/evidence_contract/contract_reflection artifacts were written.
If validators keep reading the old generated artifacts, the workflow can pass a
contract split that is no longer the locked semantic source.
```

Implemented slice:

```text
semantic overlay:
  writes semantic_source_fingerprint into:
    verify/requirements_index.json
    verify/evidence_contract.json
    verify/contract_reflection.json

fingerprint:
  artifact: verify/semantic_contracts.json
  sha256: hash of the current semantic source

evidence validator:
  rejects stale verify/requirements_index.json and verify/evidence_contract.json
  before accepting the evidence contract

reflection validator:
  rejects stale verify/evidence_contract.json and
  verify/contract_reflection.json before approving stage reflection

content binding:
  validators recompute the expected semantic requirements, obligations, and
  contract_refs from verify/semantic_contracts.json, so merely editing the
  fingerprint field to the current hash is not enough to pass stale content
```

The same principle now reaches one layer lower, into simulator evidence.

```text
sim evidence freshness:
  records hashes for the reflection/evidence metadata:
    verify/contract_reflection.json
    verify/evidence_contract.json
    sim/sim_stage_run.json

  embeds the owning sim-stage receipt:
    type=sim_stage_run
    source=sim_stage
    status=pass
    pass/fail counts
    runner path

  records hashes for the contract-reflection input files:
    SSOT
    FL
    CL
    RTL owner files
    TB file

  records hashes for the simulator evidence artifacts:
    sim/scoreboard_events.jsonl
    sim/<ip>.vcd

strict check:
  --require-sim-freshness runs check_sim_evidence_freshness.py
  missing or mismatched sim/evidence_freshness.json fails contract-check
  owner route is sim-debug

stamp command:
  stamp_sim_evidence_freshness.py writes sim/evidence_freshness.json after sim
  workflow/tb-gen/scripts/sim.sh runs it automatically after a successful
  Python/cocotb simulation when contract_reflection.json exists
```

This closes two concrete fake-green vectors:

```text
semantic split changed:
  old generated requirements/evidence/reflection artifacts become stale

SSOT/FL/CL/RTL/TB or scoreboard/VCD changed:
  old simulator evidence becomes stale in strict freshness mode
```

Current proof:

```text
tests/test_semantic_contract_freshness.py:
  overlay stamps the semantic source fingerprint
  evidence checker rejects stale requirements_index fingerprint
  evidence checker rejects stale semantic contract artifact
  reflection checker rejects stale semantic reflection artifact
  evidence/reflection checkers reject forged-current fingerprints on stale
  semantic content

MCTP v3 strict contract-check:
  pass, reflection=4/4 evidence=105/105
  generated artifacts carry the same semantic source sha256

tests/test_sim_evidence_freshness.py:
  strict check passes after simulator evidence freshness is stamped
  strict check rejects changed SSOT, FL, CL, RTL, TB after the stamp
  strict check rejects changed scoreboard_events.jsonl after the stamp
  strict check rejects changed VCD after the stamp
  strict check rejects invalid reflection paths
  strict check rejects reflection shrinkage after the stamp
  strict check rejects manual or forged restamp when sim evidence predates inputs
  sim.sh stamps freshness after successful Python/cocotb runner completion
```

Still remaining for full stale-evidence closure:

```text
make --require-sim-freshness the default in signoff mode
make every simulator entrypoint stamp freshness, not only tb-gen sim.sh
include sampled cycle/value wave predicates, not only artifact hashes
replace local artifact allowlists with simulator provenance manifests where
possible
```

## Core Idea

Use a stable `contract_ref` for every important logical requirement.

Example:

```yaml
contract_ref: STATE_PAYLOAD_COUNT
kind: state_variable
name: payload_byte_count
width: 13
reset: 0
update_on: EVENT_ACCEPTED_MCTP_PAYLOAD_BYTE
clear_on:
  - reset
  - EVENT_CONTEXT_RELEASE
observable_via:
  - debug.payload_byte_count
  - apb.Q_PAYLOAD_COUNT
  - descriptor.len
  - readback.byte_count
```

Do not force physical RTL names such as `ctx_payload_count_ff` into SSOT. That
over-constrains implementation and breaks on refactors. Instead, define the
architectural state, update/clear semantics, and required observability.

## Reflection Chain

For each required `contract_ref`, the workflow should be able to answer:

```text
SSOT:
  Where is the contract defined?

FL:
  Where is the expected meaning implemented?

CL:
  Where are cycle-visible semantics defined?

RTL:
  Which owner file/module implements it, and how is it observable?

TB:
  Which scenario/monitor drives and samples it?

Sim evidence:
  Which scoreboard row compares FL/CL expected behavior with RTL observed behavior?
```

If any required link is missing, Signoff mode should block.

## FL And CL Roles

FL and CL should stay separate because they answer different questions.

```text
FL = what is correct?
CL = what is visible when, in what order, and under what protocol pressure?
```

For MCTP, FL says:

```text
This TLP has 17 payload bytes.
SRAM should store those 17 bytes, excluding PCIe/MCTP headers.
payload_byte_count should be 17.
descriptor_len should be 17.
drop_count should remain 0.
```

CL says:

```text
After AXI W beat acceptance, parser/context/SRAM signals become visible in
defined cycle windows.
While sram_wr_valid is high and sram_wr_ready is low, data/strb must hold.
descriptor_publish must occur only after the final SRAM write or flush is
accepted.
APB Q_PAYLOAD_COUNT becomes visible only after the approved update point.
```

CL is not only "timing." It is the cycle contract: ordering, backpressure,
valid/ready hold, pipeline visibility, resource conflict behavior, queue
full/empty behavior, status visibility, and response sequencing.

## TB Role

TB is not the source of expected behavior. TB is the contract executor,
observer, and comparator.

```text
Stimulus source:
  SSOT / evidence_contract scenario_ids

Expected value source:
  FL

Expected timing and ordering source:
  CL

Observed signal source:
  evidence_contract.required_observables + ip_contract observables

Pass/fail source:
  evidence_contract.pass_conditions

Coverage source:
  SSOT coverage goals + obligation_ids
```

TB must not derive expected values from RTL observations. It must not weaken
pass conditions to make the DUT pass. It must not mark coverage hit when the
required observable was not sampled.

For cocotb/pyuvm, TB reflection should be explicit. `tb_manifest.json` should
name the scenario, driver, monitor, sampled observables, expected source, and
scoreboard row fields for each required `contract_ref`.

Example TB reflection entry:

```json
{
  "contract_ref": "STATE_PAYLOAD_COUNT",
  "framework": "cocotb+pyuvm",
  "scenario_id": "SC_MCTP_SHORT_FINAL_FRAGMENT",
  "driver": "axi_write_tlp_driver",
  "monitor": "payload_pack_monitor",
  "expected_sources": [
    "FunctionalModel.FM_SRAM_PACK_WRITE",
    "CycleModel.descriptor_after_sram_flush"
  ],
  "sampled_observables": [
    "dut.sram_wr_addr",
    "dut.sram_wr_data",
    "dut.sram_wr_strb",
    "dut.debug_payload_byte_count",
    "dut.descriptor_len"
  ],
  "scoreboard_fields": [
    "rtl_observed.sram_write_addr",
    "rtl_observed.sram_write_strb",
    "rtl_observed.debug_payload_byte_count",
    "condition_results.payload_count_matches_fl"
  ]
}
```

This prevents a generated TB from being another untracked interpretation of
the SSOT. The TB must declare which contract item it drives, which monitor
samples the DUT, and which scoreboard fields carry the evidence.

## Simulation And Wave Evidence

Simulation evidence should prove that required observables were sampled from
the DUT, not copied from FL expected values or inferred from stimulus.

For each required `contract_ref`, simulation should provide:

```text
scoreboard row:
  FL/CL expected versus RTL observed comparison, condition_results, pass/fail

wave/source evidence:
  VCD/FST path, signal paths, sample cycles, and values used by the monitor

freshness:
  RTL/TB/FL/CL input fingerprints matching the simulation run
```

The scoreboard row is the compact approval record. The waveform evidence is the
debug/audit record showing that the monitor had real DUT visibility.

Suggested sim evidence shape:

```json
{
  "contract_ref": "STATE_PAYLOAD_COUNT",
  "scenario_id": "SC_MCTP_SHORT_FINAL_FRAGMENT",
  "scoreboard_row": {
    "artifact": "sim/scoreboard_events.jsonl",
    "match": {
      "obligation_id": "OBL_MCTP_SRAM_PACK_001",
      "passed": true
    }
  },
  "wave_observations": [
    {
      "artifact": "sim/mctp_assembler_scratch.vcd",
      "signal": "top.sram_wr_strb",
      "cycle": 42,
      "value": "0x1ffff"
    },
    {
      "artifact": "sim/mctp_assembler_scratch.vcd",
      "signal": "top.debug_payload_byte_count",
      "cycle": 43,
      "value": 17
    }
  ],
  "sample_source": "payload_pack_monitor",
  "input_fingerprints": {
    "rtl": "...",
    "tb": "...",
    "functional_model": "...",
    "cycle_model": "..."
  }
}
```

Signoff should not require a human to inspect every VCD manually, but the
machine-readable evidence should make it possible to jump from an approved
scoreboard row to the exact sampled signal and cycle.

## Validator Surfaces

Evidence does not have to come only from cocotb assertions. Any deterministic
validator can approve a contract item if it reads authoritative artifacts,
records what it checked, and emits machine-readable evidence tied to
`contract_ref`.

Useful validator surfaces:

```text
cocotb/pyuvm runtime monitor:
  samples DUT during simulation and writes scoreboard rows.

offline VCD/FST validator:
  parses waves after simulation and proves cycle/order/hold properties from
  actual signal transitions.

static RTL validator:
  checks owner module, port connectivity, observable path, reset style, no
  placeholder/tieoff, and required state/update structure.

artifact validator:
  checks JSON/XML/coverage/signoff reports, artifact freshness, hashes, and
  row/schema consistency.

formal/property validator:
  proves small safety properties when assertions and tool support exist.
```

The important rule is not the implementation language. The validator must emit
a durable artifact that says:

```text
contract_ref checked
input artifacts and hashes
observables inspected
conditions evaluated
pass/fail result
owner to route on failure
```

Example offline wave validator output:

```json
{
  "type": "contract_validator_result",
  "validator": "vcd_hold_order_checker",
  "contract_ref": "ORDER_DESCRIPTOR_AFTER_SRAM_FLUSH",
  "obligation_id": "OBL_MCTP_DESC_002",
  "status": "pass",
  "inputs": {
    "vcd": {
      "path": "sim/mctp_assembler_scratch.vcd",
      "sha256": "..."
    },
    "scoreboard": {
      "path": "sim/scoreboard_events.jsonl",
      "sha256": "..."
    }
  },
  "observations": [
    {
      "signal": "top.sram_wr_valid",
      "cycle": 42,
      "value": 1
    },
    {
      "signal": "top.sram_wr_ready",
      "cycle": 42,
      "value": 1
    },
    {
      "signal": "top.descriptor_push",
      "cycle": 43,
      "value": 1
    }
  ],
  "condition_results": {
    "descriptor_push_after_final_sram_write_accept": true
  },
  "failure_owner": "rtl-gen"
}
```

This makes validators interchangeable at the workflow level. A contract can be
closed by cocotb runtime evidence, offline wave analysis, a static audit, a
formal proof, or a combination, as long as the evidence cites the same
`contract_ref` and is strong enough for the Run Mode.

## MCTP Example

Requirement:

```text
MCTP fragment payload must be stored contiguously in SRAM, excluding
PCIe/MCTP header bytes. payload_byte_count, descriptor_len, and firmware
readback must agree with the payload actually stored.
```

Evidence obligation:

```json
{
  "obligation_id": "OBL_MCTP_SRAM_PACK_001",
  "contract_refs": [
    "STATE_PAYLOAD_COUNT",
    "MEM_SRAM_PAYLOAD_PACK"
  ],
  "claim": "SRAM stores only MCTP payload bytes contiguously, and payload_byte_count equals stored payload bytes.",
  "required": true,
  "scenario_ids": [
    "SC_MCTP_SHORT_FINAL_FRAGMENT"
  ],
  "required_observables": [
    "sram_write_addr",
    "sram_write_data",
    "sram_write_strb",
    "payload_byte_count",
    "descriptor_len",
    "readback_data_out"
  ],
  "pass_conditions": [
    "header_bytes_not_written",
    "sram_strobes_are_contiguous",
    "payload_count_matches_fl",
    "descriptor_len_matches_payload_count",
    "readback_matches_fl_payload"
  ]
}
```

Reflection manifest entry:

```json
{
  "contract_ref": "STATE_PAYLOAD_COUNT",
  "ssot_ref": "function_model.state_variables.payload_byte_count",
  "fl": {
    "artifact": "model/functional_model.py",
    "implemented_as": "state_updates.payload_byte_count",
    "transactions": [
      "FM_ASSEMBLE_FRAGMENT",
      "FM_SRAM_PACK_WRITE"
    ]
  },
  "cl": {
    "artifact": "model/cycle_model.py",
    "rule": "count updates after accepted payload beat and holds under backpressure"
  },
  "rtl": {
    "owner_files": [
      "rtl/mctp_assembler_scratch_context_table.sv",
      "rtl/mctp_assembler_scratch_sram_packer.sv"
    ],
    "observable_via": [
      "debug_payload_byte_count",
      "APB.Q_PAYLOAD_COUNT",
      "descriptor_len"
    ]
  },
  "tb": {
    "artifact": "tb/cocotb/test_mctp_assembler_scratch.py",
    "scenario": "SC_MCTP_SHORT_FINAL_FRAGMENT",
    "monitor": "payload_pack_monitor"
  }
}
```

Passing scoreboard row:

```json
{
  "goal_id": "EQ_TRANSACTION_FM_SRAM_PACK_WRITE",
  "scenario_id": "SC_MCTP_SHORT_FINAL_FRAGMENT",
  "contract_refs": [
    "STATE_PAYLOAD_COUNT",
    "MEM_SRAM_PAYLOAD_PACK"
  ],
  "obligation_ids": [
    "OBL_MCTP_SRAM_PACK_001"
  ],
  "passed": true,
  "fl_expected": {
    "payload_byte_count": 17,
    "payload_bytes": "..."
  },
  "cl_expected": {
    "descriptor_publish_after_sram_flush": true,
    "hold_under_backpressure": true
  },
  "rtl_observed": {
    "sram_write_addr": 52,
    "sram_write_strb": 131071,
    "debug_payload_byte_count": 17,
    "descriptor_len": 17,
    "readback_data_out": "..."
  },
  "condition_results": {
    "header_bytes_not_written": true,
    "sram_strobes_are_contiguous": true,
    "payload_count_matches_fl": true,
    "descriptor_len_matches_payload_count": true,
    "readback_matches_fl_payload": true
  }
}
```

## Required Checker

The future checker should behave like this:

```text
for each required requirement:
  require a stable requirement_id or direct SSOT locked claim
  require atomic obligations, unless the requirement is already atomic
  require every required obligation to name at least one contract_ref
  require every required obligation to be observable, provable, waived, or blocked

for each required contract_ref:
  require SSOT definition
  require FL reflection and self-check pass
  require CL reflection when cycle-visible semantics exist
  require RTL owner_file / owner_module / observable path
  require TB scenario and monitor
  require TB manifest to name driver, monitor, sampled observables, and expected source
  require passing scoreboard row citing the contract_ref or obligation_id
  require every required observable in rtl_observed
  require every required condition_result to be true
  require waveform/source observation metadata for debug/audit-grade claims
  require fresh input/output fingerprints
```

Suggested outputs:

```text
<ip>/verify/contract_reflection.json
<ip>/signoff/contract_reflection_coverage.json
```

Suggested stage names:

```text
derive_contract_reflection
check_contract_reflection
```

This should feed `truth_coverage` and final signoff as stronger evidence than
token matching.

## MCTP v2 Gap Closure

`mctp_assembler_scratch` is the right first migration target because it already
has most raw ingredients:

```text
req package:
  req/mctp_assembler_scratch_requirements.md
  req/source_references.md
  req/approval_manifest.json

SSOT:
  yaml/mctp_assembler_scratch.ssot.yaml
  includes function_model, cycle_model, registers, fsm, test_requirements

generated models and verification:
  model/functional_model.py
  model/cycle_model.py
  verify/ip_contract.json
  verify/equivalence_goals.json

runtime evidence:
  tb/cocotb/tb_manifest.json
  sim/scoreboard_events.jsonl
  sim/mctp_assembler_scratch.vcd
  sim/simulation_quality.json
  signoff/truth_coverage.json
  signoff/ip_signoff.json
```

The gap is not lack of evidence. The gap is that evidence is still mostly
`goal_id` / `scenario_id` / `coverage_refs` centered. The next layer must make
the evidence requirement-centered and contract-centered.

Add these artifacts first:

```text
verify/requirements_index.json:
  stable IDs for every required requirement or locked SSOT claim

verify/evidence_contract.json:
  requirement_id -> obligation_id -> contract_refs -> scenario/observable/pass condition

verify/contract_reflection.json:
  contract_ref -> FL/CL/RTL/TB/SIM reflection points

wave evidence:
  direct VCD/FST predicates in evidence_contract today; optional
  sim/wave_observations.json can later record exact signal paths, cycles, and
  sampled values

signoff/evidence_contract_coverage.json:
  required obligations closed, waived, blocked, or failed

signoff/contract_reflection_coverage.json:
  required contract_refs reflected through all required stages
```

For MCTP, a useful first migration slice is `payload_byte_count` plus SRAM
packing and descriptor visibility:

```json
{
  "requirement_id": "REQ_MCTP_PAYLOAD_ASSEMBLY_001",
  "source_refs": [
    "req/mctp_assembler_scratch_requirements.md#9.4",
    "yaml/mctp_assembler_scratch.ssot.yaml:function_model.transactions.FM_ASSEMBLE_FRAGMENT",
    "yaml/mctp_assembler_scratch.ssot.yaml:function_model.transactions.FM_SRAM_PACK_WRITE",
    "yaml/mctp_assembler_scratch.ssot.yaml:registers.Q_PAYLOAD_COUNT"
  ],
  "claim": "Accepted MCTP payload bytes are packed contiguously into SRAM and exposed as the assembled payload byte count.",
  "required": true,
  "obligation_ids": [
    "OBL_MCTP_PAYLOAD_COUNT_001",
    "OBL_MCTP_SRAM_PACK_001",
    "OBL_MCTP_DESC_VIS_001",
    "OBL_MCTP_APB_VIS_001"
  ]
}
```

Then split the requirement into machine-checkable obligations:

```json
[
  {
    "obligation_id": "OBL_MCTP_PAYLOAD_COUNT_001",
    "contract_refs": ["STATE_PAYLOAD_COUNT"],
    "claim": "payload_byte_count increments by accepted payload bytes and clears on reset or context release.",
    "required_observables": [
      "payload_len",
      "context_accept",
      "payload_byte_count",
      "ctx_payload_byte_count"
    ],
    "pass_conditions": [
      "count_updates_only_on_accept",
      "count_matches_fl_payload_len_sum",
      "count_resets_to_zero",
      "count_does_not_change_under_unaccepted_backpressure"
    ]
  },
  {
    "obligation_id": "OBL_MCTP_SRAM_PACK_001",
    "contract_refs": ["MEM_SRAM_PAYLOAD_PACK", "ORDER_SRAM_HOLD_UNTIL_READY"],
    "claim": "SRAM writes contain payload bytes only, no holes, and hold data/strb while not ready.",
    "required_observables": [
      "sram_wr_valid",
      "sram_wr_ready",
      "sram_wr_addr",
      "sram_wr_data",
      "sram_wr_strb",
      "payload_bytes"
    ],
    "pass_conditions": [
      "header_bytes_not_written",
      "sram_strobes_are_contiguous",
      "payload_bytes_match_fl",
      "valid_data_strb_hold_until_ready"
    ]
  },
  {
    "obligation_id": "OBL_MCTP_DESC_VIS_001",
    "contract_refs": ["ORDER_DESCRIPTOR_AFTER_SRAM_FLUSH", "DESC_PAYLOAD_LENGTH"],
    "claim": "Descriptor is published after final SRAM write acceptance and reports the assembled payload length.",
    "required_observables": [
      "sram_wr_valid",
      "sram_wr_ready",
      "descriptor_push",
      "descriptor_len"
    ],
    "pass_conditions": [
      "descriptor_push_after_final_sram_accept",
      "descriptor_len_matches_payload_count"
    ]
  },
  {
    "obligation_id": "OBL_MCTP_APB_VIS_001",
    "contract_refs": ["APB_Q_PAYLOAD_COUNT_VISIBILITY"],
    "claim": "APB Q_PAYLOAD_COUNT exposes the updated per-Q payload count after the approved visibility point.",
    "required_observables": [
      "paddr",
      "psel",
      "penable",
      "pready",
      "prdata",
      "payload_byte_count"
    ],
    "pass_conditions": [
      "apb_read_occurs_in_access_phase",
      "q_payload_count_visible_after_update_cycle",
      "reserved_bits_read_zero"
    ]
  }
]
```

Each stage then needs to say where it reflects the same IDs:

```json
{
  "contract_ref": "STATE_PAYLOAD_COUNT",
  "ssot": {
    "path": "yaml/mctp_assembler_scratch.ssot.yaml",
    "refs": [
      "function_model.state_variables.payload_byte_count",
      "function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.payload_byte_count",
      "registers.register_list.Q_PAYLOAD_COUNT.fields.payload_byte_count"
    ]
  },
  "fl": {
    "path": "model/functional_model.py",
    "entry_points": [
      "FunctionalModel.apply",
      "FM_ASSEMBLE_FRAGMENT"
    ]
  },
  "cl": {
    "path": "model/cycle_model.py",
    "rules": [
      "latency.FM_ASSEMBLE_FRAGMENT",
      "handshake.sram_ready_valid",
      "ordering.descriptor_after_sram_flush"
    ]
  },
  "rtl": {
    "owner_files": [
      "rtl/mctp_assembler_scratch_pcie_vdm_parser.sv",
      "rtl/mctp_assembler_scratch_context_table.sv",
      "rtl/mctp_assembler_scratch_apb_regfile.sv"
    ],
    "observable_via": [
      "payload_byte_count",
      "ctx_payload_byte_count",
      "Q_PAYLOAD_COUNT"
    ]
  },
  "tb": {
    "path": "tb/cocotb/test_mctp_assembler_scratch.py",
    "monitor": "payload_pack_monitor",
    "scoreboard_fields": [
      "rtl_observed.payload_byte_count",
      "condition_results.count_matches_fl_payload_len_sum"
    ]
  },
  "sim": {
    "scoreboard": "sim/scoreboard_events.jsonl",
    "wave": "sim/mctp_assembler_scratch.vcd"
  }
}
```

After migration, the relevant scoreboard row should stop being only:

```text
goal_id + scenario_id + coverage_refs + passed
```

and should include:

```json
{
  "contract_refs": [
    "STATE_PAYLOAD_COUNT",
    "MEM_SRAM_PAYLOAD_PACK",
    "ORDER_DESCRIPTOR_AFTER_SRAM_FLUSH"
  ],
  "obligation_ids": [
    "OBL_MCTP_PAYLOAD_COUNT_001",
    "OBL_MCTP_SRAM_PACK_001",
    "OBL_MCTP_DESC_VIS_001"
  ],
  "condition_results": {
    "count_matches_fl_payload_len_sum": true,
    "header_bytes_not_written": true,
    "sram_strobes_are_contiguous": true,
    "valid_data_strb_hold_until_ready": true,
    "descriptor_push_after_final_sram_accept": true,
    "descriptor_len_matches_payload_count": true
  },
  "observed_contract": {
    "required_observables_present": true,
    "missing_observables": []
  }
}
```

The important behavioral rule is:

```text
If a required obligation has no observable, no pass condition, no validator, or
no passing evidence row, signoff is blocked. It is not a weak pass.
```

This is the distinction between current MCTP and MCTP v2:

```text
current MCTP:
  strong local goal/scenario evidence
  truth_coverage pass through normalized tokens and existing artifacts

MCTP v2:
  every required requirement has atomic obligations
  every obligation has contract_refs
  every contract_ref is reflected through FL/CL/RTL/TB/SIM
  every required predicate has executable evidence
  every missing predicate routes to an owning stage
```

Pilot artifacts now exist for `mctp_assembler_scratch`:

```text
verify/requirements_index.json
verify/evidence_contract.json
verify/contract_reflection.json
signoff/evidence_contract_coverage.json
signoff/contract_reflection_coverage.json
workflow/contract-reflection/scripts/check_evidence_contract.py
workflow/contract-reflection/scripts/check_contract_reflection.py
workflow/contract-reflection/scripts/emit_goal_contract_overlay.py
workflow/contract_reflection/evidence_contract_json.py
workflow/contract_reflection/evidence_contract_vcd.py
mctp_assembler_scratch/tb/cocotb/test_mctp_contract_v2.py
mctp_assembler_scratch/tb/cocotb/test_contract_v2_runner.py
sim/contract_v2_events.jsonl
sim/contract_v2.vcd
```

The current pilot run is closed in two layers:

```text
rich predicate slice:
  5 MCTP payload/packing/backpressure/descriptor/APB obligations
  checked by scoreboard rows plus focused VCD predicates

legacy scoreboard closure overlay:
  86 generated equivalence goals converted into required obligations
  checked by passing scoreboard rows tied to RTL-observed fields
  reflected through LEGACY_SCOREBOARD_GOAL_CLOSURE

contract_reflection_coverage:
  pass, 7/7 contract_refs reflected through SSOT/FL/CL/RTL/TB/SIM/VCD
  wave check requires sampled VCD values for each declared RTL observable,
  not only signal declarations

evidence_contract_coverage:
  pass, 91/91 required obligations passed

rich obligations passed:
  OBL_MCTP_PAYLOAD_COUNT_001
  OBL_MCTP_SRAM_PACK_001
  OBL_MCTP_SRAM_BACKPRESSURE_001
  OBL_MCTP_DESC_VIS_001
  OBL_MCTP_APB_VIS_001

legacy obligations passed:
  OBL_GOAL_* for all 86 generated equivalence goals
```

The legacy overlay is deliberately weaker than the rich slice. It proves that
every generated goal has a passing row with RTL-observed data; it does not claim
that every semantic requirement has already been split into hand-authored
machine predicates. That is still the next migration step for requirements that
need stronger local authority.

The current MCTP pilot also keeps evidence-row artifacts on a narrow allowlist:

```text
allowed scoreboard artifacts:
  sim/scoreboard_events.jsonl
  sim/contract_v2_events.jsonl

rejected:
  verify/forged_rows.jsonl
  sim/forged_rows.jsonl
  path traversal or extra path components
```

This is adequate for the local pilot, but a common-engine stage should replace
the hardcoded allowlist with a provenance-backed simulator evidence manifest.

The rich slice uses fresh runtime evidence:

```text

  CONTRACT_V2_SRAM_BACKPRESSURE:
    cocotb drives sram_wr_ready=0, observes sram_wr_valid=1, and VCD validates
    sram_wr_addr/data/strb stability while ready is low

  CONTRACT_V2_APB_Q_PAYLOAD_COUNT_AFTER_UPDATE:
    cocotb reads Q_PAYLOAD_COUNT after payload assembly and validates
    prdata[12:0] == 17
```

This keeps the original lesson from the first failed run: the gate must expose
missing executable evidence before it allows green signoff. The closed pilot now
shows the repair path too: add a focused runtime scenario, emit fresh evidence
rows, tie those rows and VCD predicates to the obligations, then rerun the
deterministic gates.

## MCTP v3 Closure Evidence

`mctp_assembler_v3` is the current working proof for the locked-truth loop. The
semantic SC_SINGLE slice closes with FL-derived expected values and VCD
predicates, and the whole IP contract-check closes after the legacy goal overlay
also finds passing scoreboard evidence.

Fresh local evidence from 2026-06-04:

```text
truth coverage:
  pass, obligations=72 covered=72 uncovered_required=0

RTL todo audit:
  pass, tasks=501 blockers=0 orphans=0

IP signoff:
  pass, gates=18/18

simulation:
  cocotb TESTS=10 PASS=10 FAIL=0
  scoreboard goals=102 required=102 rows=104

coverage:
  functional=120/120

sim-debug:
  checked=102 passed=102 failed=0 blocked=0

goal-audit:
  pass, 16/16

contract-check:
  pass, reflection=4/4 evidence=105/105
  command:
    python3 workflow/contract-reflection/scripts/run_contract_check.py \
      mctp_assembler_v3 --root . --require-contract-closure \
      --require-sim-freshness
  runs:
    semantic_contract_overlay
    goal_contract_overlay
    sim_evidence_freshness
    contract_reflection
    evidence_contract

sim evidence freshness:
  pass, metadata=3 inputs=9 evidence_artifacts=2 issues=0
  stamp_source=sim_stage
  embedded receipt: type=sim_stage_run status=pass pass=10 fail=0
  metadata hashes cover contract_reflection.json, evidence_contract.json, and
  sim/sim_stage_run.json
  input hashes cover SSOT, FL, CL, RTL owner files, and TB
  evidence hashes cover sim/scoreboard_events.jsonl and sim/mctp_assembler_v3.vcd
```

This is contract and locked-truth closure evidence, not a claim that production
CDC, PPA, DFT, STA, or formal signoff is complete.

The important point is not that every stage ran. The proof is that the contract
gate ties locked truth to executable evidence. `contract_reflection` proves the
semantic IDs are wired through SSOT/FL/CL/RTL/TB and simulation artifacts.
`evidence_contract` then decides which obligations are closed and which ones
would route to an owner if evidence fails.

The v3 contract-check now has a real semantic overlay source:

```text
verify/semantic_contracts.json:
  human/SSOT-approved semantic split input

verify/requirements_index.json:
  REQ_MCTP_V3_SC_SINGLE_ASSEMBLY_001
  -> 3 semantic obligations
  plus legacy generated-goal closure requirement

verify/evidence_contract.json:
  105 required obligations total
  3 semantic MCTP obligations
  102 legacy scoreboard-goal obligations

verify/contract_reflection.json:
  STATE_PAYLOAD_COUNT
  MEM_SRAM_PAYLOAD_PACK
  DESC_PUBLISH_VISIBLE
  LEGACY_SCOREBOARD_GOAL_CLOSURE
```

The semantic MCTP requirement currently closes this concrete slice:

```text
REQ_MCTP_V3_SC_SINGLE_ASSEMBLY_001:
  For locked scenario SC_SINGLE, accepted MCTP payload bytes are counted,
  packed into SRAM, and made visible through descriptor publication.

OBL_MCTP_V3_SC_SINGLE_PAYLOAD_COUNT_001:
  scoreboard:
    EQ_TRANSACTION_FM_PACK_SRAM / SC_SINGLE
    ctx_payload_byte_count == FL.state_updates.payload_bytes_written_count
    ctx_payload_count_sel == FL.state_updates.payload_bytes_written_count
    row passed with FL expected model_result present
  VCD:
    ctx_payload_byte_count reaches 32

OBL_MCTP_V3_SC_SINGLE_SRAM_PACK_001:
  scoreboard:
    sram_wr_valid == FL.sram_wr_valid
    sram_wr_count == 1
    sram_wr_addr == FL.sram_wr_addr
    sram_wr_strb == FL.sram_wr_strb
    sram_wr_strb is contiguous
  VCD:
    sram_wr_valid occurs same_or_after ctx_payload_byte_count reaches 32

OBL_MCTP_V3_SC_SINGLE_DESCRIPTOR_VISIBLE_001:
  scoreboard:
    EQ_TRANSACTION_FM_PUBLISH_DESCRIPTOR / SC_SINGLE
    row passed with FL expected model_result present
    descriptor_push == 1
    descriptor_valid == FL.state_updates.descriptor_valid
    ctx_state_sel == FL.state_updates.ctx_state
  VCD:
    descriptor_push is observed
    descriptor_valid occurs same_or_after descriptor_push
```

This is not the full semantic closure of every MCTP requirement yet. It is the
first working requirement-level slice where a stable requirement is split into
semantic obligations, those obligations cite contract_refs, and the deterministic
gate closes them with FL-derived scoreboard fields plus VCD predicates. It also
keeps the legacy goal closure as a separate compatibility layer: if any required
legacy scoreboard row is false or stale, `contract-check` blocks and routes to an
owner instead of silently accepting weak evidence.

## Default Workflow Overlay

This concept does not need to start as a mandatory common-engine stage. The
practical first deployment is a default-workflow overlay:

```text
default workflow
  read req / SSOT
  read optional verify/semantic_contracts.json
  generate or update requirements_index
  generate or update evidence_contract
  generate or update contract_reflection
  run the existing FL / CL / RTL / TB / sim flow
  run check_evidence_contract
  run check_contract_reflection
  classify fail / blocked into one owner repair task
  rerun the owning stage, sim, and contract gates
```

The overlay works because it does not replace the existing workflow. It adds a
stricter contract audit above the existing artifacts. `STAGE_MANIFEST.json`
keeps the default `contract-check` command legacy-compatible and also exposes a
`contract_check_strict` entrypoint for IPs that must prove the semantic source
exists before signoff can pass.

`semantic_contracts.json` is the important user-facing seam. It is where a
human-approved requirement split can enter the default workflow without forcing
every generator to become contract-ref-aware on day one. The default flow expands
that source into the three validator artifacts, runs normal stage evidence, and
then lets deterministic gates decide pass, blocked, or fail.

Default mode treats `verify/semantic_contracts.json` as optional so existing
generated-goal contract checks keep working. Strict mode requires it; if the file
is missing, `contract-check` fails and routes repair to `contract-reflection`
even when cached generated validator artifacts would otherwise pass.

The default worker may perform the repair, but only while acting as one owner at
a time. It must not mix SSOT, RTL, TB, and evidence edits in the same repair
step.

Good default-workflow repair:

```text
blocked:
  descriptor_bytes missing from scoreboard

owner role:
  tb-gen

allowed edits:
  TB monitor / scoreboard emitter only

rerun:
  sim
  check_evidence_contract
  check_contract_reflection
```

Bad default-workflow repair:

```text
edit scoreboard JSON directly
lower the requirement in SSOT
change RTL and TB together without owner classification
declare pass from LLM reasoning
```

So the default workflow can use this concept now, but the policy must be:

```text
contract audit overlay:
  allowed

single worker editing every layer at once:
  not allowed
```

## Strict Single-Worker Repair

Strict mode makes automatic repair harder because there is only one active
worker. The correct adaptation is not multi-owner parallel repair; it is a
serialized repair queue.

```text
validator result
  -> pass:
       close obligation

  -> fail:
       choose one owning workflow
       repair behavior
       rerun evidence

  -> blocked:
       choose one owning workflow or human gate
       add missing truth / observable / monitor / validator input
       rerun evidence
```

The single worker still has to preserve owner boundaries:

```text
iteration 1:
  owner = tb-gen
  fix missing monitor
  rerun sim and contract gates

iteration 2:
  owner = rtl-gen
  fix observed RTL behavior
  rerun sim and contract gates

iteration 3:
  owner = cl-model-gen
  fix missing cycle/order rule
  rerun contract gates
```

This is slower than multi-worker orchestration, but it is often more auditable:
there is less race risk, less artifact ownership conflict, and fewer stale
evidence collisions.

Suggested repair report shape:

```json
{
  "obligation_id": "OBL_MCTP_DESC_VIS_001",
  "status": "blocked",
  "reason": "descriptor_bytes missing from scoreboard",
  "suggested_owner": "tb-gen",
  "allowed_next_stage": "tb-gen",
  "forbidden_edits": [
    "rtl",
    "ssot"
  ],
  "rerun": [
    "sim",
    "check_evidence_contract",
    "check_contract_reflection"
  ]
}
```

Owner routing rules:

```text
locked truth missing or ambiguous:
  human gate / ssot-gen

obligation split weak:
  evidence-contract reviewer / human

FL expected wrong:
  fl-model-gen

CL timing, ordering, hold, or visibility rule wrong or missing:
  cl-model-gen

RTL observed behavior wrong:
  rtl-gen

observable missing:
  rtl-gen if the signal/register path does not exist
  tb-gen if the path exists but the monitor does not sample it

scoreboard row missing:
  tb-gen / sim

VCD missing or no sampled value:
  sim / tb-gen

validator schema or tool bug:
  tool-fix
```

The current MCTP v2 pilot already exposes fail/block reasons through deterministic
reports. What is not complete yet is the automatic handoff from those reports
into a strict single-worker repair queue.

Recommended rollout:

```text
Phase 1:
  default workflow overlay on MCTP-like IPs

Phase 2:
  default workflow serialized repair queue with suggested_owner,
  allowed_edits, forbidden_edits, and rerun commands

Phase 3:
  optional common-engine contract-reflection stage

Phase 4:
  required Engineering / Signoff gate
```

## Command And Orchestrator Surfaces

The concept is now executable through a single command surface:

```text
/contract-check <ip>
```

That command runs:

```text
emit_goal_contract_overlay
check_contract_reflection
check_evidence_contract
classify_contract_owner when the result is not pass
```

Single-worker mode can use the same command serially. The worker runs one owner
repair at a time, then reruns the dependent evidence path:

```text
owner repair
-> sim / focused validator if needed
-> /contract-check <ip>
```

Orchestrator mode gets the same gate as a pipeline stage:

```text
sim-debug
-> contract-check       owner workflow: contract-reflection
-> goal-audit
```

The `contract-reflection` worker is deterministic-validator focused. It should
not rewrite SSOT/RTL/TB to force green evidence. If the gate fails or blocks, it
emits `signoff/contract_owner_routing.json`; the orchestrator should dispatch
the reported owner workflow and then rerun `contract-check`.

The implementation also has a legacy compatibility overlay. If an IP does not
yet have hand-authored `requirements_index.json` and `evidence_contract.json`,
`emit_goal_contract_overlay` can derive a weaker
`LEGACY_SCOREBOARD_GOAL_CLOSURE` requirement from existing
`verify/equivalence_goals.json` plus passing scoreboard rows. That keeps older
goal/scenario IPs working while making the weaker claim explicit.

For MCTP v2, the rich slice is stronger than the legacy overlay: it has
hand-authored requirements, atomic obligations, contract refs, scoreboard rows,
and VCD predicates for payload count, SRAM pack, backpressure, descriptor
visibility, and APB visibility.

## Locked Truth Write Guard

Once requirement truth is locked, worker stages must not rewrite it. SSOT-gen may
read locked truth and write the YAML contract, but it may not update:

```text
<ip>/req/*_requirements.md
<ip>/req/source_references.md
<ip>/req/approval_manifest.json
```

The runtime guard treats `req/approval_manifest.json` as the lock marker unless
it explicitly says the requirement is draft/unlocked. When the lock is active:

```text
write_file / replace_in_file on locked truth:
  refused before the tool writes

slash command, script, or shell mutation:
  detected after the run, restored from the pre-run byte snapshot, and reported
  as worker error
```

This is intentionally stronger than prompt policy. Prompts now tell ssot-gen not
to write approved requirements, but the deterministic guard is the authority. A
worker cannot make a green SSOT pass by silently shrinking or replacing the
locked requirement text.

If the locked requirement is wrong or incomplete, the route is:

```text
human/spec authority unlocks or re-approves truth
-> ssot-gen refreshes YAML from the updated truth
-> downstream FL/CL/RTL/TB/SIM evidence becomes stale and must rerun
```

## Current Implementation Status

Already present in the workflow:

```text
derive_ip_contract:
  emits <ip>/verify/ip_contract.json

rtl_todo_plan:
  records SSOT-derived RTL tasks with source_ref, owner_file, owner_module,
  static evidence, and todo_completion

scoreboard_events:
  records goal_id, scenario_id, fl_expected, rtl_observed, coverage_refs, passed

tb_manifest:
  records generated cocotb/pyuvm harness metadata, parameters, registers, and
  available state observables

simulation_quality:
  rejects missing required observables and shallow scenario-class evidence

truth_coverage:
  requires locked-truth obligations to be covered before signoff

ip_signoff:
  gates ip_contract, rtl_todo, simulation_quality, scoreboard, coverage,
  truth_coverage, and related artifacts

contract-check:
  runs through WorkflowStageEngine, headless serial flow, Atlas pipeline
  dispatch, and the orchestrator `contract-reflection` workflow

locked_truth_guard:
  blocks or restores writes to approved requirement files during worker runs

contract_reflection:
  validates SSOT/FL/CL/RTL/TB/SIM reflection plus sampled VCD evidence

evidence_contract:
  validates requirements, obligations, contract_refs, scoreboard rows,
  condition_results, VCD predicates, and owner-routable failure reasons
```

Not yet complete:

```text
evidence_contract.json as a required artifact for every IP
per-stage contract_ref reflection manifests for every IP
scoreboard rows emitted directly with obligation_ids and condition_results
full VCD/FST observation metadata with exact sampled cycle/value rows for every
required contract_ref, beyond the current VCD sample and predicate checks
contract-check integrated into final IP signoff as a mandatory production gate
automatic owner-route repair loops for failed obligations
```

So the workflow direction is now executable on MCTP, default serial flow, and
orchestrator dispatch. It is still not a mandatory production signoff gate for
every IP and not yet a fully automatic repair loop.

## Why This Matters

This turns the workflow from stage-driven to contract-driven:

```text
stage-driven:
  Did ssot/fl/cl/rtl/tb/sim run?

contract-driven:
  Did every required contract item survive through FL, CL, RTL, TB, and
  executable evidence without losing meaning?
```

If this works, the workflow can make a much stronger local claim:

```text
The implementation matches the locked intent covered by required local evidence.
```

It still cannot prove:

```text
The locked intent itself is complete.
The obligation split is sufficient.
External standard conformance is complete.
CDC/PPA/DFT/STA/formal/production signoff is complete.
```

Those remain human/spec authority or separate production gates.
