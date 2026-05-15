# RTL Authoring Packet: module__gray_counter_core__function_model_01

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
- Task count: 48
- Required tasks: 48

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
- LLM-actionable open tasks: 48
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 1/9 section=function_model task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0030: Implement RTL state owner for FL state gray_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.gray_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.gray_state.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.state_variables.
SSOT item context: name=gray_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.gray_state
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - gray_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.gray_state

### RTL-0031: Implement RTL state owner for FL state bin_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.bin_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.bin_state.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.state_variables.
SSOT item context: name=bin_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.bin_state
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - bin_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.bin_state

### RTL-0032: Implement RTL state owner for FL state done_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_variable
- Source ref: function_model.state_variables.done_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.done_state.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.state_variables.
SSOT item context: name=done_state; reset=0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.done_state
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - done_state reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.done_state

### RTL-0033: Implement transaction GC_TXN_RESET

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.GC_TXN_RESET
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.GC_TXN_RESET.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: id=GC_TXN_RESET; name=asynchronous_reset_assert.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET

### RTL-0034: Implement precondition for GC_TXN_RESET: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_RESET.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.preconditions.precondition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=rst_n == 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.preconditions.precondition_0

### RTL-0035: Implement input for GC_TXN_RESET: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.GC_TXN_RESET.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.inputs.input_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=rst_n.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.inputs.input_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.inputs.input_0

### RTL-0036: Implement output for GC_TXN_RESET: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_RESET.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.outputs.output_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=gray_value == 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.outputs.output_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.outputs.output_0

### RTL-0037: Implement output for GC_TXN_RESET: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_RESET.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.outputs.output_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=bin_value == 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.outputs.output_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.outputs.output_1

### RTL-0038: Implement output for GC_TXN_RESET: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_RESET.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.outputs.output_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=done == 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.outputs.output_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.outputs.output_2

### RTL-0039: Implement output rule for GC_TXN_RESET: gray_value_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_RESET.output_rules.gray_value_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.output_rules.gray_value_reset.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: name=gray_value_reset; port=gray_value; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.output_rules.gray_value_reset
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - gray_value_reset width matches SSOT value WIDTH
  - gray_value_reset RTL expression implements SSOT expression 0
  - DUT port gray_value is the implementation/observation point for gray_value_reset
  - gray_value_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_RESET.output_rules.gray_value_reset

### RTL-0040: Implement output rule for GC_TXN_RESET: bin_value_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_RESET.output_rules.bin_value_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.output_rules.bin_value_reset.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: name=bin_value_reset; port=bin_value; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.output_rules.bin_value_reset
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - bin_value_reset width matches SSOT value WIDTH
  - bin_value_reset RTL expression implements SSOT expression 0
  - DUT port bin_value is the implementation/observation point for bin_value_reset
  - bin_value_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_RESET.output_rules.bin_value_reset

### RTL-0041: Implement output rule for GC_TXN_RESET: done_reset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_RESET.output_rules.done_reset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.output_rules.done_reset.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: name=done_reset; port=done; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.output_rules.done_reset
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - done_reset width matches SSOT value 1
  - done_reset RTL expression implements SSOT expression 0
  - DUT port done is the implementation/observation point for done_reset
  - done_reset is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_RESET.output_rules.done_reset

### RTL-0042: Implement side effect for GC_TXN_RESET: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=gray_state set to 0 immediately on reset assertion.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_0

### RTL-0043: Implement side effect for GC_TXN_RESET: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_RESET.
SSOT item context: value=done_state cleared.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_RESET.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_RESET.side_effects.side_effect_1

### RTL-0044: Implement transaction GC_TXN_CLEAR

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.GC_TXN_CLEAR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: id=GC_TXN_CLEAR; name=synchronous_clear.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR

### RTL-0045: Implement precondition for GC_TXN_CLEAR: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=rst_n == 1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_0

### RTL-0046: Implement precondition for GC_TXN_CLEAR: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=clear sampled high on rising clock edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.preconditions.precondition_1

### RTL-0047: Implement input for GC_TXN_CLEAR: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.GC_TXN_CLEAR.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.inputs.input_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=clear.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.inputs.input_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.inputs.input_0

### RTL-0048: Implement output for GC_TXN_CLEAR: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=gray_value == 0 after edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.outputs.output_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.outputs.output_0

### RTL-0049: Implement output for GC_TXN_CLEAR: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=bin_value == 0 after edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.outputs.output_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.outputs.output_1

### RTL-0050: Implement output for GC_TXN_CLEAR: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.outputs.output_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=done == 0 after edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.outputs.output_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.outputs.output_2

### RTL-0051: Implement output rule for GC_TXN_CLEAR: gray_value_clear

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_CLEAR.output_rules.gray_value_clear
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.output_rules.gray_value_clear.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: name=gray_value_clear; port=gray_value; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.output_rules.gray_value_clear
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - gray_value_clear width matches SSOT value WIDTH
  - gray_value_clear RTL expression implements SSOT expression 0
  - DUT port gray_value is the implementation/observation point for gray_value_clear
  - gray_value_clear is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.output_rules.gray_value_clear

### RTL-0052: Implement output rule for GC_TXN_CLEAR: bin_value_clear

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_CLEAR.output_rules.bin_value_clear
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.output_rules.bin_value_clear.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: name=bin_value_clear; port=bin_value; expr=0; width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.output_rules.bin_value_clear
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - bin_value_clear width matches SSOT value WIDTH
  - bin_value_clear RTL expression implements SSOT expression 0
  - DUT port bin_value is the implementation/observation point for bin_value_clear
  - bin_value_clear is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.output_rules.bin_value_clear

### RTL-0053: Implement output rule for GC_TXN_CLEAR: done_clear

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_CLEAR.output_rules.done_clear
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.output_rules.done_clear.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: name=done_clear; port=done; expr=0; width=1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.output_rules.done_clear
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - done_clear width matches SSOT value 1
  - done_clear RTL expression implements SSOT expression 0
  - DUT port done is the implementation/observation point for done_clear
  - done_clear is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.output_rules.done_clear

### RTL-0054: Implement side effect for GC_TXN_CLEAR: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=gray_state overwritten with 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_0

### RTL-0055: Implement side effect for GC_TXN_CLEAR: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_CLEAR.
SSOT item context: value=done_state cleared.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_CLEAR.side_effects.side_effect_1

### RTL-0056: Implement transaction GC_TXN_ADVANCE

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.GC_TXN_ADVANCE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: id=GC_TXN_ADVANCE; name=advance_one_gray_step.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE

### RTL-0057: Implement precondition for GC_TXN_ADVANCE: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=rst_n == 1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_0

### RTL-0058: Implement precondition for GC_TXN_ADVANCE: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=clear == 0 on sampled edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_1

### RTL-0059: Implement precondition for GC_TXN_ADVANCE: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=enable == 1 on sampled edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.preconditions.precondition_2

### RTL-0060: Implement input for GC_TXN_ADVANCE: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.GC_TXN_ADVANCE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.inputs.input_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=enable.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.inputs.input_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.inputs.input_0

### RTL-0061: Implement input for GC_TXN_ADVANCE: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.GC_TXN_ADVANCE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.inputs.input_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=current gray_state.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.inputs.input_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.inputs.input_1

### RTL-0062: Implement output for GC_TXN_ADVANCE: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=next binary state equals (current bin_state + 1) mod 2^WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.outputs.output_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.outputs.output_0

### RTL-0063: Implement output for GC_TXN_ADVANCE: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=next gray_value equals bin_to_gray(next binary state).
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.outputs.output_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.outputs.output_1

### RTL-0064: Implement output for GC_TXN_ADVANCE: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.outputs.output_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=bin_value equals gray_to_bin(gray_value) at all observable times.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.outputs.output_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.outputs.output_2

### RTL-0065: Implement output rule for GC_TXN_ADVANCE: gray_advance

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.gray_advance
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.gray_advance.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: name=gray_advance; port=gray_value; expr=((bin_state + 1) ^ ((bin_state + 1) >> 1)) & ((1<<WIDTH)-1); width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.output_rules.gray_advance
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - gray_advance width matches SSOT value WIDTH
  - gray_advance RTL expression implements SSOT expression ((bin_state + 1) ^ ((bin_state + 1) >> 1)) & ((1<<WIDTH)-1)
  - DUT port gray_value is the implementation/observation point for gray_advance
  - gray_advance is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.output_rules.gray_advance

### RTL-0066: Implement output rule for GC_TXN_ADVANCE: bin_observe

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.bin_observe
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.bin_observe.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: name=bin_observe; port=bin_value; expr=gray_to_bin(gray_value); width=WIDTH.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.output_rules.bin_observe
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - bin_observe width matches SSOT value WIDTH
  - bin_observe RTL expression implements SSOT expression gray_to_bin(gray_value)
  - DUT port bin_value is the implementation/observation point for bin_observe
  - bin_observe is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.output_rules.bin_observe

### RTL-0067: Implement output rule for GC_TXN_ADVANCE: done_wrap

- Priority: high
- Required: True
- Status: open
- Category: function_model.output_rule
- Source ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.done_wrap
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.output_rules.done_wrap.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: name=done_wrap; port=done; expr=(1 if bin_state == ((1<<WIDTH)-1) else 0); width=1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.output_rules.done_wrap
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - done_wrap width matches SSOT value 1
  - done_wrap RTL expression implements SSOT expression (1 if bin_state == ((1<<WIDTH)-1) else 0)
  - DUT port done is the implementation/observation point for done_wrap
  - done_wrap is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.output_rules.done_wrap

### RTL-0068: Implement side effect for GC_TXN_ADVANCE: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=gray_state updates to next_gray.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_0

### RTL-0069: Implement side effect for GC_TXN_ADVANCE: side_effect_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: value=done_state set to 1 iff current bin_state is max value; else 0.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.side_effects.side_effect_1

### RTL-0070: Implement error case for GC_TXN_ADVANCE: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.GC_TXN_ADVANCE.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_ADVANCE.error_cases.error_case_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_ADVANCE.
SSOT item context: condition=WIDTH < 2.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_ADVANCE.error_cases.error_case_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - function_model.transactions.GC_TXN_ADVANCE.error_cases.error_case_0 condition is implemented as RTL control logic: WIDTH < 2
- SSOT refs: function_model.transactions.GC_TXN_ADVANCE.error_cases.error_case_0

### RTL-0071: Implement transaction GC_TXN_HOLD

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.GC_TXN_HOLD
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.GC_TXN_HOLD.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: id=GC_TXN_HOLD; name=hold_state.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD

### RTL-0072: Implement precondition for GC_TXN_HOLD: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=rst_n == 1.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.preconditions.precondition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_0

### RTL-0073: Implement precondition for GC_TXN_HOLD: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=clear == 0 on sampled edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.preconditions.precondition_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_1

### RTL-0074: Implement precondition for GC_TXN_HOLD: precondition_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=enable == 0 on sampled edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.preconditions.precondition_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.preconditions.precondition_2

### RTL-0075: Implement input for GC_TXN_HOLD: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.GC_TXN_HOLD.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.inputs.input_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=enable.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.inputs.input_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.inputs.input_0

### RTL-0076: Implement output for GC_TXN_HOLD: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_HOLD.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.outputs.output_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=gray_value remains unchanged.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.outputs.output_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.outputs.output_0

### RTL-0077: Implement output for GC_TXN_HOLD: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.GC_TXN_HOLD.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.GC_TXN_HOLD.outputs.output_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via function_model.transactions.GC_TXN_HOLD.
SSOT item context: value=bin_value remains decode(gray_value).
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.GC_TXN_HOLD.outputs.output_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: function_model.transactions.GC_TXN_HOLD.outputs.output_1
