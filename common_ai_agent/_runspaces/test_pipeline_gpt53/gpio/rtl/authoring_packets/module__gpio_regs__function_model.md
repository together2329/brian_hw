# RTL Authoring Packet: module__gpio_regs__function_model

- Kind: module
- Owner module: gpio_regs
- Owner file: rtl/gpio_regs.sv
- Task count: 38
- Required tasks: 38

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 38
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.S1_LATCH_CONTROL, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1_LATCH_CONTROL, function_model.transactions.FM2_SAMPLE_INPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, function_model.transactions.FM4_ASYNC_RESET, registers, registers.register_list, registers.register_list.DIR_Q, registers.register_list.DOUT_Q
- Module slice: 1/8 section=function_model task_limit=48
- Slice rule: Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])

## Tasks

### RTL-0034: Implement RTL state owner for FL state dir_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dir_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dir_state.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.state_variables.
SSOT item context: name=dir_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dir_state
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dir_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dir_state

### RTL-0035: Implement RTL state owner for FL state dout_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.dout_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.dout_state.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.state_variables.
SSOT item context: name=dout_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.dout_state
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dout_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.dout_state

### RTL-0036: Implement RTL state owner for FL state din_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.din_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.din_state.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.state_variables.
SSOT item context: name=din_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.din_state
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - din_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.din_state

### RTL-0037: Implement transaction FM1_LATCH_CONTROL

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1_LATCH_CONTROL
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: id=FM1_LATCH_CONTROL; name=latch_direction_and_output_data.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL

### RTL-0038: Implement precondition for FM1_LATCH_CONTROL: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=rst_n is deasserted.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_0

### RTL-0039: Implement precondition for FM1_LATCH_CONTROL: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=rising edge of clk.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.preconditions.precondition_1

### RTL-0040: Implement input for FM1_LATCH_CONTROL: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=dir_in.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.inputs.input_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_0

### RTL-0041: Implement input for FM1_LATCH_CONTROL: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=dout_in.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.inputs.input_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.inputs.input_1

### RTL-0042: Implement output for FM1_LATCH_CONTROL: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=dir_state equals dir_in after sampling edge.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.outputs.output_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_0

### RTL-0043: Implement output for FM1_LATCH_CONTROL: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=dout_state equals dout_in after sampling edge.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.outputs.output_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.outputs.output_1

### RTL-0044: Implement output rule for FM1_LATCH_CONTROL: dir_q_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dir_q_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dir_q_next.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: name=dir_q_next; port=dir_q; expr=dir_in; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.output_rules.dir_q_next
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dir_q_next width matches SSOT value WIDTH
  - dir_q_next RTL expression implements SSOT expression dir_in
  - DUT port dir_q is the implementation/observation point for dir_q_next
  - dir_q_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dir_q_next

### RTL-0045: Implement output rule for FM1_LATCH_CONTROL: dout_q_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dout_q_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dout_q_next.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: name=dout_q_next; port=dout_q; expr=dout_in; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.output_rules.dout_q_next
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dout_q_next width matches SSOT value WIDTH
  - dout_q_next RTL expression implements SSOT expression dout_in
  - DUT port dout_q is the implementation/observation point for dout_q_next
  - dout_q_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.output_rules.dout_q_next

### RTL-0046: Implement side effect for FM1_LATCH_CONTROL: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1_LATCH_CONTROL.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1_LATCH_CONTROL.side_effects.side_effect_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM1_LATCH_CONTROL.
SSOT item context: value=dir_q and dout_q update atomically each cycle.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1_LATCH_CONTROL.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM1_LATCH_CONTROL.side_effects.side_effect_0

### RTL-0047: Implement transaction FM2_SAMPLE_INPUTS

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: id=FM2_SAMPLE_INPUTS; name=sample_pad_inputs_for_input_bits_only.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS

### RTL-0048: Implement precondition for FM2_SAMPLE_INPUTS: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=rst_n is deasserted.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_0

### RTL-0049: Implement precondition for FM2_SAMPLE_INPUTS: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=rising edge of clk.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.preconditions.precondition_1

### RTL-0050: Implement input for FM2_SAMPLE_INPUTS: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=pad_in.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_0

### RTL-0051: Implement input for FM2_SAMPLE_INPUTS: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=dir_state.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_1

### RTL-0052: Implement input for FM2_SAMPLE_INPUTS: input_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_2.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=din_state.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_2
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.inputs.input_2

### RTL-0053: Implement output for FM2_SAMPLE_INPUTS: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=din_state bits with dir_state=0 sample pad_in.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_0

### RTL-0054: Implement output for FM2_SAMPLE_INPUTS: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=din_state bits with dir_state=1 hold previous value.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.outputs.output_1

### RTL-0055: Implement output rule for FM2_SAMPLE_INPUTS: din_q_masked_next

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.output_rules.din_q_masked_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.output_rules.din_q_masked_next.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: name=din_q_masked_next; port=din_q; expr=(din_q & dir_q) | (pad_in & ~dir_q); width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.output_rules.din_q_masked_next
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - din_q_masked_next width matches SSOT value WIDTH
  - din_q_masked_next RTL expression implements SSOT expression (din_q & dir_q) | (pad_in & ~dir_q)
  - DUT port din_q is the implementation/observation point for din_q_masked_next
  - din_q_masked_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.output_rules.din_q_masked_next

### RTL-0056: Implement side effect for FM2_SAMPLE_INPUTS: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2_SAMPLE_INPUTS.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2_SAMPLE_INPUTS.side_effects.side_effect_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM2_SAMPLE_INPUTS.
SSOT item context: value=din_q updates only on input-configured bits.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2_SAMPLE_INPUTS.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM2_SAMPLE_INPUTS.side_effects.side_effect_0

### RTL-0066: Implement transaction FM4_ASYNC_RESET

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4_ASYNC_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: id=FM4_ASYNC_RESET; name=asynchronous_reset_clears_state.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET

### RTL-0067: Implement precondition for FM4_ASYNC_RESET: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4_ASYNC_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.preconditions.precondition_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=rst_n asserted low.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.preconditions.precondition_0

### RTL-0068: Implement output for FM4_ASYNC_RESET: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=dir_state zero.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.outputs.output_0

### RTL-0069: Implement output for FM4_ASYNC_RESET: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=dout_state zero.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.outputs.output_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.outputs.output_1

### RTL-0070: Implement output for FM4_ASYNC_RESET: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_2.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=din_state zero.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.outputs.output_2
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.outputs.output_2

### RTL-0071: Implement output for FM4_ASYNC_RESET: output_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_3.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=oe_o zero.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.outputs.output_3
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.outputs.output_3

### RTL-0072: Implement output for FM4_ASYNC_RESET: output_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.outputs.output_4.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=pad_o zero.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.outputs.output_4
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.outputs.output_4

### RTL-0073: Implement output rule for FM4_ASYNC_RESET: dir_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.dir_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.dir_reset.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: name=dir_reset; port=dir_q; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.output_rules.dir_reset
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dir_reset width matches SSOT value WIDTH
  - dir_reset RTL expression implements SSOT expression 0
  - DUT port dir_q is the implementation/observation point for dir_reset
  - dir_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.output_rules.dir_reset

### RTL-0074: Implement output rule for FM4_ASYNC_RESET: dout_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.dout_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.dout_reset.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: name=dout_reset; port=dout_q; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.output_rules.dout_reset
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dout_reset width matches SSOT value WIDTH
  - dout_reset RTL expression implements SSOT expression 0
  - DUT port dout_q is the implementation/observation point for dout_reset
  - dout_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.output_rules.dout_reset

### RTL-0075: Implement output rule for FM4_ASYNC_RESET: din_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.din_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.output_rules.din_reset.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: name=din_reset; port=din_q; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.output_rules.din_reset
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - din_reset width matches SSOT value WIDTH
  - din_reset RTL expression implements SSOT expression 0
  - DUT port din_q is the implementation/observation point for din_reset
  - din_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.output_rules.din_reset

### RTL-0076: Implement side effect for FM4_ASYNC_RESET: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4_ASYNC_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4_ASYNC_RESET.side_effects.side_effect_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.transactions.FM4_ASYNC_RESET.
SSOT item context: value=all architectural state cleared independent of clk.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4_ASYNC_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.transactions.FM4_ASYNC_RESET.side_effects.side_effect_0

### RTL-0077: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.
SSOT item context: value=oe_o equals dir_q at all times after combinational settle.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0078: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.
SSOT item context: value=pad_o equals (dout_q & dir_q) bitwise.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0079: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.
SSOT item context: value=din_q output-configured bits hold unless reset.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0080: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: gpio_regs in rtl/gpio_regs.sv via function_model.
SSOT item context: value=no hidden state beyond dir_q, dout_q, din_q.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: function_model.invariants.invariant_3
