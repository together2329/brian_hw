# RTL Authoring Packet: module__pl330_target_mfifo__function_model_01

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 48
- Required tasks: 48

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
- Module slice: 2/11 section=function_model task_limit=48
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

### RTL-0111: Implement RTL state owner for FL state channel_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.channel_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.channel_state.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=channel_state; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.channel_state
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - channel_state width matches SSOT value 4
  - channel_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.channel_state

### RTL-0112: Implement RTL state owner for FL state channel_pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.channel_pc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.channel_pc.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=channel_pc; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.channel_pc
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - channel_pc width matches SSOT value 32
  - channel_pc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.channel_pc

### RTL-0113: Implement RTL state owner for FL state outstanding_reads

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.outstanding_reads
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.outstanding_reads.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=outstanding_reads; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.outstanding_reads
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - outstanding_reads width matches SSOT value 4
  - outstanding_reads reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.outstanding_reads

### RTL-0114: Implement RTL state owner for FL state outstanding_writes

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.outstanding_writes
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.outstanding_writes.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=outstanding_writes; width=4; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.outstanding_writes
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - outstanding_writes width matches SSOT value 4
  - outstanding_writes reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.outstanding_writes

### RTL-0115: Implement RTL state owner for FL state mfifo_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.mfifo_count
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.mfifo_count.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=mfifo_count; width=5; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.mfifo_count
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - mfifo_count width matches SSOT value 5
  - mfifo_count reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.mfifo_count

### RTL-0116: Implement RTL state owner for FL state irq_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.irq_status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.irq_status.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=irq_status; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.irq_status
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - irq_status width matches SSOT value 32
  - irq_status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.irq_status

### RTL-0117: Implement RTL state owner for FL state fault_status

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fault_status
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fault_status.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.state_variables.
SSOT item context: name=fault_status; width=32; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fault_status
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - fault_status width matches SSOT value 32
  - fault_status reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fault_status

### RTL-0118: Implement transaction FM_RESET

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RESET.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: id=FM_RESET; name=reset.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RESET
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET

### RTL-0119: Implement precondition for FM_RESET: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=transaction is accepted under cycle_model rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.preconditions.precondition_0

### RTL-0120: Implement output for FM_RESET: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=all state -> reset values.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.outputs.output_0

### RTL-0121: Implement side effect for FM_RESET: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=outstanding_reads=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_0

### RTL-0122: Implement side effect for FM_RESET: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=outstanding_writes=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_1

### RTL-0123: Implement side effect for FM_RESET: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_2.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=mfifo_count=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_2

### RTL-0124: Implement side effect for FM_RESET: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RESET.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RESET.side_effects.side_effect_3.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_RESET.
SSOT item context: value=irq_status=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RESET.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_RESET.side_effects.side_effect_3

### RTL-0125: Implement transaction FM_DMAGO

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMAGO
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMAGO.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: id=FM_DMAGO; name=dmago_command.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAGO

### RTL-0126: Implement precondition for FM_DMAGO: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAGO.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAGO.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: value=channel_state==0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAGO.preconditions.precondition_0

### RTL-0127: Implement precondition for FM_DMAGO: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAGO.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAGO.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: value=manager APB write to DBGINST.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAGO.preconditions.precondition_1

### RTL-0128: Implement output for FM_DMAGO: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMAGO.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAGO.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: value=channel_state=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAGO.outputs.output_0

### RTL-0129: Implement output for FM_DMAGO: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMAGO.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAGO.outputs.output_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: value=channel_pc=arg_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO.outputs.output_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAGO.outputs.output_1

### RTL-0130: Implement error case for FM_DMAGO: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMAGO.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAGO.error_cases.error_case_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAGO.
SSOT item context: condition=secure violation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAGO.error_cases.error_case_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - function_model.transactions.FM_DMAGO.error_cases.error_case_0 condition is implemented as RTL control logic: secure violation
- SSOT refs: function_model.transactions.FM_DMAGO.error_cases.error_case_0

### RTL-0131: Implement transaction FM_DMALD

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMALD
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMALD.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: id=FM_DMALD; name=dmald_load.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMALD
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD

### RTL-0132: Implement precondition for FM_DMALD: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMALD.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD.preconditions.precondition_0

### RTL-0133: Implement precondition for FM_DMALD: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMALD.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: value=mfifo has space.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD.preconditions.precondition_1

### RTL-0134: Implement output for FM_DMALD: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMALD.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: value=outstanding_reads += 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD.outputs.output_0

### RTL-0135: Implement output for FM_DMALD: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMALD.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.outputs.output_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: value=mfifo entries reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.outputs.output_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD.outputs.output_1

### RTL-0136: Implement side effect for FM_DMALD: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMALD.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: value=issue AXI AR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALD.side_effects.side_effect_0

### RTL-0137: Implement error case for FM_DMALD: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMALD.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALD.error_cases.error_case_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALD.
SSOT item context: condition=AXI rresp != OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALD.error_cases.error_case_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - function_model.transactions.FM_DMALD.error_cases.error_case_0 condition is implemented as RTL control logic: AXI rresp != OKAY
- SSOT refs: function_model.transactions.FM_DMALD.error_cases.error_case_0

### RTL-0138: Implement transaction FM_DMAST

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMAST
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMAST.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: id=FM_DMAST; name=dmast_store.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMAST
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST

### RTL-0139: Implement precondition for FM_DMAST: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAST.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST.preconditions.precondition_0

### RTL-0140: Implement precondition for FM_DMAST: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMAST.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: value=mfifo has data.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST.preconditions.precondition_1

### RTL-0141: Implement output for FM_DMAST: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMAST.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: value=outstanding_writes += 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST.outputs.output_0

### RTL-0142: Implement output for FM_DMAST: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMAST.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.outputs.output_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: value=mfifo entries consumed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.outputs.output_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST.outputs.output_1

### RTL-0143: Implement side effect for FM_DMAST: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMAST.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: value=issue AXI AW + W.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMAST.side_effects.side_effect_0

### RTL-0144: Implement error case for FM_DMAST: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DMAST.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMAST.error_cases.error_case_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMAST.
SSOT item context: condition=AXI bresp != OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMAST.error_cases.error_case_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - function_model.transactions.FM_DMAST.error_cases.error_case_0 condition is implemented as RTL control logic: AXI bresp != OKAY
- SSOT refs: function_model.transactions.FM_DMAST.error_cases.error_case_0

### RTL-0145: Implement transaction FM_DMALDP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMALDP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMALDP.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: id=FM_DMALDP; name=dmaldp_periph_load.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP

### RTL-0146: Implement precondition for FM_DMALDP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMALDP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALDP.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP.preconditions.precondition_0

### RTL-0147: Implement precondition for FM_DMALDP: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMALDP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALDP.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: value=periph drvalid asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP.preconditions.precondition_1

### RTL-0148: Implement output for FM_DMALDP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMALDP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALDP.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: value=outstanding_reads += 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP.outputs.output_0

### RTL-0149: Implement side effect for FM_DMALDP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMALDP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALDP.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: value=drready asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP.side_effects.side_effect_0

### RTL-0150: Implement side effect for FM_DMALDP: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMALDP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMALDP.side_effects.side_effect_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMALDP.
SSOT item context: value=AXI AR issued.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMALDP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMALDP.side_effects.side_effect_1

### RTL-0151: Implement transaction FM_DMASTP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMASTP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMASTP.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: id=FM_DMASTP; name=dmastp_periph_store.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP

### RTL-0152: Implement precondition for FM_DMASTP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMASTP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASTP.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP.preconditions.precondition_0

### RTL-0153: Implement precondition for FM_DMASTP: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMASTP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASTP.preconditions.precondition_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: value=periph davalid acknowledged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP.preconditions.precondition_1

### RTL-0154: Implement output for FM_DMASTP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_DMASTP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASTP.outputs.output_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: value=outstanding_writes += 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP.outputs.output_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP.outputs.output_0

### RTL-0155: Implement side effect for FM_DMASTP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMASTP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASTP.side_effects.side_effect_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: value=daready asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP.side_effects.side_effect_0

### RTL-0156: Implement side effect for FM_DMASTP: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_DMASTP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASTP.side_effects.side_effect_1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASTP.
SSOT item context: value=AXI AW+W issued.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASTP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASTP.side_effects.side_effect_1

### RTL-0157: Implement transaction FM_DMASEV

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DMASEV
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DMASEV.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASEV.
SSOT item context: id=FM_DMASEV; name=dmasev_event_signal.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DMASEV
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASEV

### RTL-0158: Implement precondition for FM_DMASEV: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DMASEV.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DMASEV.preconditions.precondition_0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via function_model.transactions.FM_DMASEV.
SSOT item context: value=channel_state==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DMASEV.preconditions.precondition_0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: function_model.transactions.FM_DMASEV.preconditions.precondition_0
