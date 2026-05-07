# RTL Authoring Packet: module__pl330_target_engine

- Kind: module
- Owner module: pl330_target_engine
- Owner file: rtl/pl330_target_engine.sv
- Task count: 8
- Required tasks: 8

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model.pipeline, fsm.engine, function_model.transactions.decode, function_model.transactions.execute, function_model.transactions.fetch
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_engine.busy <= engine_busy (observed_named_port_map)
  - pl330_target_engine.channel_state <= engine_channel_state (observed_named_port_map)
  - pl330_target_engine.clk <= clk (observed_named_port_map)
  - pl330_target_engine.cmd_channel <= engine_cmd_channel (observed_named_port_map)
  - pl330_target_engine.cmd_dst_addr <= engine_cmd_dst_addr (observed_named_port_map)
  - pl330_target_engine.cmd_len <= engine_cmd_len (observed_named_port_map)
  - pl330_target_engine.cmd_opcode <= engine_cmd_opcode (observed_named_port_map)
  - pl330_target_engine.cmd_privileged <= engine_cmd_privileged (observed_named_port_map)

## Tasks

### RTL-0028: Implement or account for SSOT module slice `pl330_target_engine`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: name=pl330_target_engine
SSOT ref: workflow_todos.rtl-gen[1].
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_ENGINE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - Semantic source_refs covered: sub_modules[0]
- SSOT refs: sub_modules[0], workflow_todos.rtl-gen[1]

### RTL-0172: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=outstanding_reads >= 0 && outstanding_reads <= 2*NUM_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0173: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=outstanding_writes >= 0 && outstanding_writes <= 2*NUM_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0175: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via control_owner_fallback.
SSOT item context: value=channel_state != 1 -> outstanding_reads == 0 && outstanding_writes == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0182: Implement pipeline stage: S0_ACCEPT

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_ACCEPT
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_ACCEPT.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S0_ACCEPT; cycle=0..N.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_ACCEPT
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S0_ACCEPT timing uses SSOT cycle/latency 0..N
  - cycle_model.pipeline.S0_ACCEPT appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_ACCEPT

### RTL-0183: Implement pipeline stage: S1_EVALUATE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_EVALUATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_EVALUATE.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S1_EVALUATE; cycle=N..M.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_EVALUATE
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S1_EVALUATE timing uses SSOT cycle/latency N..M
  - cycle_model.pipeline.S1_EVALUATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_EVALUATE

### RTL-0184: Implement pipeline stage: S2_OBSERVE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_OBSERVE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_OBSERVE.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via cycle_model.pipeline.
SSOT item context: stage=S2_OBSERVE; cycle=M..K.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_OBSERVE
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
  - cycle_model.pipeline.S2_OBSERVE timing uses SSOT cycle/latency M..K
  - cycle_model.pipeline.S2_OBSERVE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_OBSERVE

### RTL-0261: Prove module pl330_target_engine is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_engine.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_engine.module_equivalence.
Owner: pl330_target_engine in rtl/pl330_target_engine.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_engine.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_engine.sv
- SSOT refs: sub_modules.pl330_target_engine.module_equivalence
