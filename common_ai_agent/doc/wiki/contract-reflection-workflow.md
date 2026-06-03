---
title: Contract Reflection Workflow
type: concept
tags: [ip-flow, ssot, evidence, fl, cl, rtl, tb, signoff, mctp]
updated: 2026-06-03
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

## Default Workflow Overlay

This concept does not need to start as a mandatory common-engine stage. The
practical first deployment is a default-workflow overlay:

```text
default workflow
  read req / SSOT
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
stricter contract audit above the existing artifacts. That makes it useful for
scratch IPs and default-agent IP work before the contract layer is promoted into
`STAGE_MANIFEST.json`.

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
