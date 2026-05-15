# RTL Authoring Packet: module__adder_kogge_stone_core__function_model

- Kind: module
- Owner module: adder_kogge_stone_core
- Owner file: rtl/adder_kogge_stone_core.sv
- Task count: 25
- Required tasks: 25

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
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
- Owner refs: cycle_model, cycle_model.pipeline, features, features.ks_addition, fsm, fsm.adder_fsm, function_model, function_model.state_updates, function_model.transactions, function_model.transactions.FM_ADD
- Module slice: 1/6 section=function_model task_limit=48
- Slice rule: Owner module adder_kogge_stone_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0050: Implement RTL state owner for FL state a_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.a_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.a_reg.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=a_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.a_reg
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - a_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.a_reg

### RTL-0051: Implement RTL state owner for FL state b_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.b_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.b_reg.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=b_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.b_reg
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - b_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.b_reg

### RTL-0052: Implement RTL state owner for FL state cin_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.cin_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.cin_reg.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=cin_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.cin_reg
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cin_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.cin_reg

### RTL-0053: Implement RTL state owner for FL state sum_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sum_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sum_reg.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=sum_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sum_reg
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - sum_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sum_reg

### RTL-0054: Implement RTL state owner for FL state cout_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.cout_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.cout_reg.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=cout_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.cout_reg
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cout_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.cout_reg

### RTL-0055: Implement RTL state owner for FL state busy

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.busy
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.busy.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=busy; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.busy
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - busy reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.busy

### RTL-0056: Implement RTL state owner for FL state done

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.done
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.done.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=done; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.done
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - done reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.done

### RTL-0057: Implement RTL state owner for FL state overflow

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.overflow
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.overflow.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: name=overflow; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.overflow
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - overflow reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.overflow

### RTL-0058: Implement transaction FM_ADD

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ADD
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ADD.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: id=FM_ADD; name=kogge_stone_addition.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ADD
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD

### RTL-0059: Implement precondition for FM_ADD: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ADD.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.preconditions.precondition_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=CONTROL.start == 1 or (hold_mode == 0 and inputs have changed).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.preconditions.precondition_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.preconditions.precondition_0

### RTL-0060: Implement precondition for FM_ADD: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ADD.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.preconditions.precondition_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=DATA_WIDTH >= 2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.preconditions.precondition_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.preconditions.precondition_1

### RTL-0061: Implement input for FM_ADD: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ADD.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.inputs.input_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=a_i[DATA_WIDTH-1:0] or a_reg from APB shadow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.inputs.input_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.inputs.input_0

### RTL-0062: Implement input for FM_ADD: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ADD.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.inputs.input_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=b_i[DATA_WIDTH-1:0] or b_reg from APB shadow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.inputs.input_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.inputs.input_1

### RTL-0063: Implement input for FM_ADD: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ADD.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.inputs.input_2.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=cin_i or cin_reg from APB shadow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.inputs.input_2
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.inputs.input_2

### RTL-0064: Implement output for FM_ADD: sum_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ADD.outputs.sum_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.outputs.sum_o.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: name=sum_o; port=sum_o; expr=a_reg ^ b_reg ^ carry_chain; width=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.outputs.sum_o
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - sum_o width matches SSOT value DATA_WIDTH
  - sum_o RTL expression implements SSOT expression a_reg ^ b_reg ^ carry_chain
  - DUT port sum_o is the implementation/observation point for sum_o
- SSOT refs: function_model.transactions.FM_ADD.outputs.sum_o

### RTL-0065: Implement output for FM_ADD: cout_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ADD.outputs.cout_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.outputs.cout_o.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: name=cout_o; port=cout_o; expr=final_group_generate | (final_group_propagate & cin_reg); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.outputs.cout_o
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cout_o width matches SSOT value 1
  - cout_o RTL expression implements SSOT expression final_group_generate | (final_group_propagate & cin_reg)
  - DUT port cout_o is the implementation/observation point for cout_o
- SSOT refs: function_model.transactions.FM_ADD.outputs.cout_o

### RTL-0066: Implement output for FM_ADD: sum_apb

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ADD.outputs.sum_apb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.outputs.sum_apb.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: name=sum_apb; port=SUM_RESULT; expr=sum_reg; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.outputs.sum_apb
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - sum_apb width matches SSOT value 32
  - sum_apb RTL expression implements SSOT expression sum_reg
  - DUT port SUM_RESULT is the implementation/observation point for sum_apb
- SSOT refs: function_model.transactions.FM_ADD.outputs.sum_apb

### RTL-0067: Implement output for FM_ADD: cout_apb

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ADD.outputs.cout_apb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.outputs.cout_apb.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: name=cout_apb; port=COUT_RESULT; expr=cout_reg; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.outputs.cout_apb
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - cout_apb width matches SSOT value 1
  - cout_apb RTL expression implements SSOT expression cout_reg
  - DUT port COUT_RESULT is the implementation/observation point for cout_apb
- SSOT refs: function_model.transactions.FM_ADD.outputs.cout_apb

### RTL-0068: Implement side effect for FM_ADD: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ADD.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.side_effects.side_effect_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=STATUS.busy set on start, cleared after output registered.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.side_effects.side_effect_0

### RTL-0069: Implement side effect for FM_ADD: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ADD.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.side_effects.side_effect_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=STATUS.done set on completion, persists until clr_done.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.side_effects.side_effect_1

### RTL-0070: Implement side effect for FM_ADD: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ADD.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.side_effects.side_effect_2.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: value=STATUS.overflow reflects cout_reg of last operation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.transactions.FM_ADD.side_effects.side_effect_2

### RTL-0071: Implement error case for FM_ADD: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ADD.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.error_cases.error_case_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: condition=DATA_WIDTH < 2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.error_cases.error_case_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - function_model.transactions.FM_ADD.error_cases.error_case_0 condition is implemented as RTL control logic: DATA_WIDTH < 2
- SSOT refs: function_model.transactions.FM_ADD.error_cases.error_case_0

### RTL-0072: Implement error case for FM_ADD: error_case_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ADD.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ADD.error_cases.error_case_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.transactions.FM_ADD.
SSOT item context: condition=APB access to unmapped address.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ADD.error_cases.error_case_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - function_model.transactions.FM_ADD.error_cases.error_case_1 condition is implemented as RTL control logic: APB access to unmapped address
- SSOT refs: function_model.transactions.FM_ADD.error_cases.error_case_1

### RTL-0073: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: value=sum_o[DATA_WIDTH-1:0] + (cout_o << DATA_WIDTH) == a_reg + b_reg + cin_reg for all legal inputs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0074: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via function_model.
SSOT item context: value=Output registers only update on posedge PCLK when start=1 or hold_mode=0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: function_model.invariants.invariant_1
