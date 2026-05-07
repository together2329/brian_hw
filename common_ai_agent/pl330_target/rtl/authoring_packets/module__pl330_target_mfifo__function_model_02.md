# RTL Authoring Packet: module__pl330_target_mfifo__function_model_02

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 15
- Required tasks: 15

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
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 3/11 section=function_model task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_mfifo.cfg_nonsecure_allowed_i <= mfifo_cfg_nonsecure_allowed_i (observed_named_port_map)
  - pl330_target_mfifo.channel_pc_o <= mfifo_channel_pc_o (observed_named_port_map)
  - pl330_target_mfifo.channel_state_o <= mfifo_channel_state_o (observed_named_port_map)
  - pl330_target_mfifo.clk <= clk (observed_named_port_map)
  - pl330_target_mfifo.cmd_accept_o <= mfifo_cmd_accept_o (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_addr_i <= mfifo_cmd_arg_addr_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_data_i <= mfifo_cmd_arg_data_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_error_o <= mfifo_cmd_error_o (observed_named_port_map)

## Tasks

### RTL-0159: Implement precondition for FM_DMASEV: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMASEV.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASEV.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASEV.
SSOT item context: value=event index < NUM_IRQS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASEV.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASEV.preconditions.precondition_1

### RTL-0160: Implement output for FM_DMASEV: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMASEV.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASEV.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASEV.
SSOT item context: value=irq_status |= 1<<event_idx.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASEV.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASEV.outputs.output_0

### RTL-0161: Implement side effect for FM_DMASEV: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMASEV.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASEV.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASEV.
SSOT item context: value=irq[event_idx] pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASEV.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASEV.side_effects.side_effect_0

### RTL-0162: Implement transaction FM_DMAEND

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMAEND
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMAEND.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAEND.
SSOT item context: id=FM_DMAEND; name=dmaend_terminate.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMAEND
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAEND

### RTL-0163: Implement precondition for FM_DMAEND: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAEND.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAEND.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAEND.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAEND.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAEND.preconditions.precondition_0

### RTL-0164: Implement precondition for FM_DMAEND: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAEND.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAEND.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAEND.
SSOT item context: value=no outstanding.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAEND.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAEND.preconditions.precondition_1

### RTL-0165: Implement output for FM_DMAEND: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMAEND.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAEND.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAEND.
SSOT item context: value=channel_state=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAEND.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAEND.outputs.output_0

### RTL-0166: Implement error case for FM_DMAEND: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMAEND.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAEND.error_cases.error_case_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAEND.
SSOT item context: condition=outstanding > 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAEND.error_cases.error_case_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - function_model.transactions.FM_DMAEND.error_cases.error_case_0 condition is implemented as RTL control logic: outstanding > 0
- SSOT refs: function_model.transactions.FM_DMAEND.error_cases.error_case_0

### RTL-0167: Implement transaction FM_FAULT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FAULT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FAULT.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_FAULT.
SSOT item context: id=FM_FAULT; name=fault_propagate.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FAULT
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_FAULT

### RTL-0168: Implement precondition for FM_FAULT: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FAULT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=any error_case fired.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_FAULT.preconditions.precondition_0

### RTL-0169: Implement output for FM_FAULT: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FAULT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=channel_state=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_FAULT.outputs.output_0

### RTL-0170: Implement output for FM_FAULT: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FAULT.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.outputs.output_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=irq_abort pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.outputs.output_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_FAULT.outputs.output_1

### RTL-0171: Implement side effect for FM_FAULT: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FAULT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FAULT.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_FAULT.
SSOT item context: value=fault_status updated.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FAULT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_FAULT.side_effects.side_effect_0

### RTL-0174: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via semantic_terms:mfifo.
SSOT item context: value=mfifo_count <= MFIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0176: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via semantic_terms:fault.
SSOT item context: value=fault triggers irq_abort within 4 cycles.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.invariants.invariant_4
