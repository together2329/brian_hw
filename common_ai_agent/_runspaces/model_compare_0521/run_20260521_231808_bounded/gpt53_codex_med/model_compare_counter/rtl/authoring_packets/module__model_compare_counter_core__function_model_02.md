# RTL Authoring Packet: module__model_compare_counter_core__function_model_02

- Kind: module
- Owner module: model_compare_counter_core
- Owner file: rtl/model_compare_counter_core.sv
- Task count: 26
- Required tasks: 26

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
- Module slice: 3/10 section=function_model task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0081: Implement side effect for FM_UPDATE: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_UPDATE.side_effects.side_effect_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_UPDATE.
SSOT item context: id=FM_UPDATE; name=enabled_increment; port=["count", "wrapped", "valid"]; signal=["wrapped pulse is asserted only for overflowing additions."]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_UPDATE.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for enabled_increment
- SSOT refs: function_model.transactions.FM_UPDATE.side_effects.side_effect_1

### RTL-0082: Implement transaction FM_IDLE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_IDLE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_IDLE.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_IDLE
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_IDLE

### RTL-0083: Implement precondition for FM_IDLE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_IDLE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.preconditions.precondition_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: value=transaction is accepted under cycle_model rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
- SSOT refs: function_model.transactions.FM_IDLE.preconditions.precondition_0

### RTL-0084: Implement input for FM_IDLE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["clear"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_0

### RTL-0085: Implement input for FM_IDLE: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["enable"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_1

### RTL-0086: Implement input for FM_IDLE: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["step"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_2

### RTL-0087: Implement input for FM_IDLE: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_IDLE.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.inputs.input_3.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.inputs.input_3
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.inputs.input_3

### RTL-0088: Implement output for FM_IDLE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["count == count_q"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_0

### RTL-0089: Implement output for FM_IDLE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["wrapped == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_1

### RTL-0090: Implement output for FM_IDLE: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.output_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["valid == 0"]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.output_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.output_2

### RTL-0091: Implement output for FM_IDLE: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "count_q", "name":...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.out_count

### RTL-0092: Implement output for FM_IDLE: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.out_wrapped

### RTL-0093: Implement output for FM_IDLE: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable output_rules for SSOT validator completeness.", "expr": "0", "name": "out_...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.out_valid

### RTL-0094: Implement output for FM_IDLE: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "count_q", "state...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.count_q

### RTL-0095: Implement output for FM_IDLE: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "wr...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.wrapped_q

### RTL-0096: Implement output for FM_IDLE: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_IDLE.outputs.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.outputs.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=[{"description": "Mirrored from executable state_updates for SSOT validator completeness.", "expr": "0", "state": "va...; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.outputs.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.outputs.valid_q

### RTL-0097: Implement output rule for FM_IDLE: out_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_IDLE.output_rules.out_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.output_rules.out_count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=out_count; port=count; expr=count_q; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.output_rules.out_count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_count width matches SSOT value 8
  - out_count RTL expression implements SSOT expression count_q
  - DUT port count is the implementation/observation point for out_count
  - out_count is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_IDLE.output_rules.out_count

### RTL-0098: Implement output rule for FM_IDLE: out_wrapped

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_IDLE.output_rules.out_wrapped
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.output_rules.out_wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=out_wrapped; port=wrapped; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.output_rules.out_wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_wrapped width matches SSOT value 1
  - out_wrapped RTL expression implements SSOT expression 0
  - DUT port wrapped is the implementation/observation point for out_wrapped
  - out_wrapped is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_IDLE.output_rules.out_wrapped

### RTL-0099: Implement output rule for FM_IDLE: out_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_IDLE.output_rules.out_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.output_rules.out_valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=out_valid; port=valid; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.output_rules.out_valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - out_valid width matches SSOT value 1
  - out_valid RTL expression implements SSOT expression 0
  - DUT port valid is the implementation/observation point for out_valid
  - out_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_IDLE.output_rules.out_valid

### RTL-0100: Implement state update for FM_IDLE: count_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_IDLE.state_updates.count_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.state_updates.count_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=count_q; expr=count_q; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.state_updates.count_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - count_q width matches SSOT value 8
  - count_q RTL expression implements SSOT expression count_q
  - count_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_IDLE.state_updates.count_q

### RTL-0101: Implement state update for FM_IDLE: wrapped_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_IDLE.state_updates.wrapped_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.state_updates.wrapped_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=wrapped_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.state_updates.wrapped_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - wrapped_q width matches SSOT value 1
  - wrapped_q RTL expression implements SSOT expression 0
  - wrapped_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_IDLE.state_updates.wrapped_q

### RTL-0102: Implement state update for FM_IDLE: valid_q

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_IDLE.state_updates.valid_q
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.state_updates.valid_q.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: name=valid_q; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.state_updates.valid_q
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - valid_q width matches SSOT value 1
  - valid_q RTL expression implements SSOT expression 0
  - valid_q updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_IDLE.state_updates.valid_q

### RTL-0103: Implement side effect for FM_IDLE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_IDLE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_IDLE.side_effects.side_effect_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.transactions.FM_IDLE.
SSOT item context: id=FM_IDLE; name=idle_hold; port=["count", "wrapped", "valid"]; signal=["Counter holds during idle cycles while pulse outputs deassert."]; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_IDLE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid"] is the implementation/observation point for idle_hold
- SSOT refs: function_model.transactions.FM_IDLE.side_effects.side_effect_0

### RTL-0104: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.
SSOT item context: port=["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]; signal=clear==1 implies next count_q, wrapped_q, valid_q are all zero regardless of enable.; state=["count_q", "wrapped_q", "valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"] is the implementation/observation point for ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0105: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.
SSOT item context: port=["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]; signal=valid_q may only be 1 in cycles where clear==0 and enable==1.; state=["valid_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"] is the implementation/observation point for ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0106: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via function_model.
SSOT item context: port=["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]; signal=wrapped_q may only be 1 in cycles where clear==0 and enable==1 and (count_prev + step) > 255.; state=["count_q", "wrapped_q"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - DUT port ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"] is the implementation/observation point for ["count", "wrapped", "valid", "count", "wrapped", "valid", "count", "wrapped", "valid"]
- SSOT refs: function_model.invariants.invariant_2
