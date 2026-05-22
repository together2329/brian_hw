# RTL Authoring Packet: module__model_compare_counter_core__function_model_01

- Kind: module
- Owner module: model_compare_counter_core
- Owner file: rtl/model_compare_counter_core.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE, io_list
- Module slice: 2/10 section=function_model task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0033: Implement RTL state owner for FL state count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.count_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.state_variables.
SSOT item context: name=count_q; width=8; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - count_q width matches SSOT value 8
  - count_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.count_q

### RTL-0034: Implement RTL state owner for FL state wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.wrapped_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.state_variables.
SSOT item context: name=wrapped_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - wrapped_q width matches SSOT value 1
  - wrapped_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.wrapped_q

### RTL-0035: Implement RTL state owner for FL state valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.valid_q
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.state_variables.
SSOT item context: name=valid_q; width=1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - valid_q width matches SSOT value 1
  - valid_q reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.valid_q

### RTL-0036: Implement transaction FM_CLEAR

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_CLEAR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_CLEAR.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_CLEAR

### RTL-0037: Implement precondition for FM_CLEAR: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_CLEAR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.preconditions.precondition_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: value=clear == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_CLEAR.preconditions.precondition_0

### RTL-0038: Implement input for FM_CLEAR: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CLEAR.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.inputs.input_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["clear"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.inputs.input_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.inputs.input_0

### RTL-0039: Implement input for FM_CLEAR: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CLEAR.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.inputs.input_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["enable"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.inputs.input_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.inputs.input_1

### RTL-0040: Implement input for FM_CLEAR: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CLEAR.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.inputs.input_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["step"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.inputs.input_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.inputs.input_2

### RTL-0041: Implement input for FM_CLEAR: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_CLEAR.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.inputs.input_3.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.inputs.input_3
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.inputs.input_3

### RTL-0042: Implement output for FM_CLEAR: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.output_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["count == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.output_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.output_0

### RTL-0043: Implement output for FM_CLEAR: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.output_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["wrapped == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.output_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.output_1

### RTL-0044: Implement output for FM_CLEAR: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.output_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["valid == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.output_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.output_2

### RTL-0045: Implement output for FM_CLEAR: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.out_count

### RTL-0046: Implement output for FM_CLEAR: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.out_wrapped

### RTL-0047: Implement output for FM_CLEAR: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.out_valid

### RTL-0048: Implement output for FM_CLEAR: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "co...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.count_q

### RTL-0049: Implement output for FM_CLEAR: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "wr...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.wrapped_q

### RTL-0050: Implement output for FM_CLEAR: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_CLEAR.outputs.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.outputs.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "va...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.outputs.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.outputs.valid_q

### RTL-0051: Implement output rule for FM_CLEAR: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CLEAR.output_rules.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.output_rules.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=out_count; port=count; expr=0; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.output_rules.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_count width matches SSOT value 8
  - out_count RTL expression implements SSOT expression 0
  - DUT port count is the implementation/observation point for out_count
  - out_count is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CLEAR.output_rules.out_count

### RTL-0052: Implement output rule for FM_CLEAR: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CLEAR.output_rules.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.output_rules.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=out_wrapped; port=wrapped; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.output_rules.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_wrapped width matches SSOT value 1
  - out_wrapped RTL expression implements SSOT expression 0
  - DUT port wrapped is the implementation/observation point for out_wrapped
  - out_wrapped is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CLEAR.output_rules.out_wrapped

### RTL-0053: Implement output rule for FM_CLEAR: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_CLEAR.output_rules.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.output_rules.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=out_valid; port=valid; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.output_rules.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_valid width matches SSOT value 1
  - out_valid RTL expression implements SSOT expression 0
  - DUT port valid is the implementation/observation point for out_valid
  - out_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_CLEAR.output_rules.out_valid

### RTL-0054: Implement state update for FM_CLEAR: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CLEAR.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.state_updates.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=count_q; expr=0; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.state_updates.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - count_q width matches SSOT value 8
  - count_q RTL expression implements SSOT expression 0
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CLEAR.state_updates.count_q

### RTL-0055: Implement state update for FM_CLEAR: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CLEAR.state_updates.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.state_updates.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=wrapped_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.state_updates.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - wrapped_q width matches SSOT value 1
  - wrapped_q RTL expression implements SSOT expression 0
  - wrapped_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CLEAR.state_updates.wrapped_q

### RTL-0056: Implement state update for FM_CLEAR: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_CLEAR.state_updates.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.state_updates.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: name=valid_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.state_updates.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - valid_q width matches SSOT value 1
  - valid_q RTL expression implements SSOT expression 0
  - valid_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_CLEAR.state_updates.valid_q

### RTL-0057: Implement side effect for FM_CLEAR: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_CLEAR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_CLEAR.side_effects.side_effect_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_CLEAR.
SSOT item context: id=FM_CLEAR; name=clear_priority_reset; port=["count", "wrapped", "valid"]; signal=["Clear overrides enable and forces all outputs/state low on next observed state."]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_CLEAR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for clear_priority_reset
- SSOT refs: function_model.transactions.FM_CLEAR.side_effects.side_effect_0

### RTL-0058: Implement transaction FM_UPDATE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_UPDATE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_UPDATE.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_UPDATE

### RTL-0059: Implement precondition for FM_UPDATE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_UPDATE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.preconditions.precondition_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: value=clear == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_UPDATE.preconditions.precondition_0

### RTL-0060: Implement precondition for FM_UPDATE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_UPDATE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.preconditions.precondition_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_UPDATE.preconditions.precondition_1

### RTL-0061: Implement input for FM_UPDATE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_UPDATE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.inputs.input_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["clear"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.inputs.input_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.inputs.input_0

### RTL-0062: Implement input for FM_UPDATE: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_UPDATE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.inputs.input_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["enable"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.inputs.input_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.inputs.input_1

### RTL-0063: Implement input for FM_UPDATE: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_UPDATE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.inputs.input_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["step"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.inputs.input_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.inputs.input_2

### RTL-0064: Implement input for FM_UPDATE: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_UPDATE.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.inputs.input_3.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.inputs.input_3
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.inputs.input_3

### RTL-0065: Implement output for FM_UPDATE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.output_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["count == ((count_q + step) & 0xFF)"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.output_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.output_0

### RTL-0066: Implement output for FM_UPDATE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.output_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["wrapped == 1 when (count_q + step) > 255 else 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.output_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.output_1

### RTL-0067: Implement output for FM_UPDATE: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.output_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["valid == 1"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.output_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.output_2

### RTL-0068: Implement output for FM_UPDATE: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "(count_q + step) ...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.out_count

### RTL-0069: Implement output for FM_UPDATE: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1 if ((count_q + ...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.out_wrapped

### RTL-0070: Implement output for FM_UPDATE: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "1", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.out_valid

### RTL-0071: Implement output for FM_UPDATE: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "(count_q + step)...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.count_q

### RTL-0072: Implement output for FM_UPDATE: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "1 if ((count_q +...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.wrapped_q

### RTL-0073: Implement output for FM_UPDATE: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_UPDATE.outputs.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.outputs.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "1", "state": "va...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.outputs.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.outputs.valid_q

### RTL-0074: Implement output rule for FM_UPDATE: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_UPDATE.output_rules.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.output_rules.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=out_count; port=count; expr=(count_q + step) & 0xFF; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.output_rules.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_count width matches SSOT value 8
  - out_count RTL expression implements SSOT expression (count_q + step) & 0xFF
  - DUT port count is the implementation/observation point for out_count
  - out_count is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_UPDATE.output_rules.out_count

### RTL-0075: Implement output rule for FM_UPDATE: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_UPDATE.output_rules.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.output_rules.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=out_wrapped; port=wrapped; expr=1 if ((count_q + step) > 255) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.output_rules.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_wrapped width matches SSOT value 1
  - out_wrapped RTL expression implements SSOT expression 1 if ((count_q + step) > 255) else 0
  - DUT port wrapped is the implementation/observation point for out_wrapped
  - out_wrapped is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_UPDATE.output_rules.out_wrapped

### RTL-0076: Implement output rule for FM_UPDATE: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_UPDATE.output_rules.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.output_rules.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=out_valid; port=valid; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.output_rules.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_valid width matches SSOT value 1
  - out_valid RTL expression implements SSOT expression 1
  - DUT port valid is the implementation/observation point for out_valid
  - out_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_UPDATE.output_rules.out_valid

### RTL-0077: Implement state update for FM_UPDATE: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_UPDATE.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.state_updates.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=count_q; expr=(count_q + step) & 0xFF; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.state_updates.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - count_q width matches SSOT value 8
  - count_q RTL expression implements SSOT expression (count_q + step) & 0xFF
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_UPDATE.state_updates.count_q

### RTL-0078: Implement state update for FM_UPDATE: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_UPDATE.state_updates.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.state_updates.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=wrapped_q; expr=1 if ((count_q + step) > 255) else 0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.state_updates.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - wrapped_q width matches SSOT value 1
  - wrapped_q RTL expression implements SSOT expression 1 if ((count_q + step) > 255) else 0
  - wrapped_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_UPDATE.state_updates.wrapped_q

### RTL-0079: Implement state update for FM_UPDATE: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_UPDATE.state_updates.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.state_updates.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: name=valid_q; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.state_updates.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - valid_q width matches SSOT value 1
  - valid_q RTL expression implements SSOT expression 1
  - valid_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_UPDATE.state_updates.valid_q

### RTL-0080: Implement side effect for FM_UPDATE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["Accepted enabled update advances count modulo 256 and emits valid pulse."]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.side_effects.side_effect_0
