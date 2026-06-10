# RTL Authoring Packet: module__edge_det_cx1__function_model

- Kind: module
- Owner module: edge_det_cx1
- Owner file: rtl/edge_det_cx1.sv
- Task count: 37
- Required tasks: 37

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
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
- Owner refs: cycle_model, dataflow, decomposition, decomposition.units.edge_detect, decomposition.units.sync2ff, fsm, function_model, function_model.state_variables, function_model.state_variables.prev_sync, function_model.state_variables.sync1, function_model.state_variables.sync2, function_model.transactions, function_model.transactions.FM_FALL, function_model.transactions.FM_RISE, function_model.transactions.FM_STABLE, io_list
- Module slice: 4/12 section=function_model task_limit=48
- Slice rule: Owner module edge_det_cx1 is split into 12 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0028: Implement RTL state owner for FL state sync1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sync1
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sync1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.state_variables.sync1.
SSOT item context: name=sync1; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sync1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync1 reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sync1

### RTL-0029: Implement RTL state owner for FL state sync2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sync2
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sync2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.state_variables.sync2.
SSOT item context: name=sync2; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sync2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync2 reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sync2

### RTL-0030: Implement RTL state owner for FL state prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.prev_sync
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.prev_sync.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.state_variables.prev_sync.
SSOT item context: name=prev_sync; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.prev_sync
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - prev_sync reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.prev_sync

### RTL-0031: Implement transaction FM_RISE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_RISE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_RISE.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: id=FM_RISE; name=rising_edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_RISE
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_RISE

### RTL-0032: Implement precondition for FM_RISE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RISE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.preconditions.precondition_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: value=prev_sync == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_RISE.preconditions.precondition_0

### RTL-0033: Implement precondition for FM_RISE: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_RISE.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.preconditions.precondition_1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: value=sync2 == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.preconditions.precondition_1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_RISE.preconditions.precondition_1

### RTL-0034: Implement input for FM_RISE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_RISE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.inputs.input_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: id=FM_RISE; name=rising_edge; port=["rise_out", "fall_out"]; signal=["sig_in"]; state=["sync1", "sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.inputs.input_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out"] is the implementation/observation point for rising_edge
- SSOT refs: function_model.transactions.FM_RISE.inputs.input_0

### RTL-0035: Implement output for FM_RISE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_RISE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.outputs.output_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: value=rise_out=1, fall_out=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.outputs.output_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_RISE.outputs.output_0

### RTL-0036: Implement output rule for FM_RISE: rise_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RISE.output_rules.rise_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.output_rules.rise_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: name=rise_rule; port=rise_out; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.output_rules.rise_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - rise_rule width matches SSOT value 1
  - rise_rule RTL expression implements SSOT expression 1
  - DUT port rise_out is the implementation/observation point for rise_rule
  - rise_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RISE.output_rules.rise_rule

### RTL-0037: Implement output rule for FM_RISE: fall_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_RISE.output_rules.fall_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.output_rules.fall_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: name=fall_rule; port=fall_out; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.output_rules.fall_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - fall_rule width matches SSOT value 1
  - fall_rule RTL expression implements SSOT expression 0
  - DUT port fall_out is the implementation/observation point for fall_rule
  - fall_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_RISE.output_rules.fall_rule

### RTL-0038: Implement state update for FM_RISE: sync1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RISE.state_updates.sync1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.state_updates.sync1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: name=sync1; expr=sig_in; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.state_updates.sync1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync1 width matches SSOT value 1
  - sync1 RTL expression implements SSOT expression sig_in
  - sync1 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RISE.state_updates.sync1

### RTL-0039: Implement state update for FM_RISE: sync2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RISE.state_updates.sync2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.state_updates.sync2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: name=sync2; expr=sync1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.state_updates.sync2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync2 width matches SSOT value 1
  - sync2 RTL expression implements SSOT expression sync1
  - sync2 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RISE.state_updates.sync2

### RTL-0040: Implement state update for FM_RISE: prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_RISE.state_updates.prev_sync
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.state_updates.prev_sync.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: name=prev_sync; expr=sync2; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.state_updates.prev_sync
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - prev_sync width matches SSOT value 1
  - prev_sync RTL expression implements SSOT expression sync2
  - prev_sync updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_RISE.state_updates.prev_sync

### RTL-0041: Implement side effect for FM_RISE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_RISE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_RISE.side_effects.side_effect_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_RISE.
SSOT item context: id=FM_RISE; name=rising_edge; port=["rise_out", "fall_out"]; signal=["rise_out pulses for 1 cycle"]; state=["sync1", "sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_RISE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out"] is the implementation/observation point for rising_edge
- SSOT refs: function_model.transactions.FM_RISE.side_effects.side_effect_0

### RTL-0042: Implement transaction FM_FALL

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FALL
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FALL.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: id=FM_FALL; name=falling_edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FALL
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_FALL

### RTL-0043: Implement precondition for FM_FALL: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FALL.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.preconditions.precondition_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: value=prev_sync == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.preconditions.precondition_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_FALL.preconditions.precondition_0

### RTL-0044: Implement precondition for FM_FALL: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FALL.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.preconditions.precondition_1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: value=sync2 == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.preconditions.precondition_1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_FALL.preconditions.precondition_1

### RTL-0045: Implement input for FM_FALL: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_FALL.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.inputs.input_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: id=FM_FALL; name=falling_edge; port=["rise_out", "fall_out"]; signal=["sig_in"]; state=["sync1", "sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.inputs.input_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out"] is the implementation/observation point for falling_edge
- SSOT refs: function_model.transactions.FM_FALL.inputs.input_0

### RTL-0046: Implement output for FM_FALL: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FALL.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.outputs.output_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: value=rise_out=0, fall_out=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.outputs.output_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_FALL.outputs.output_0

### RTL-0047: Implement output rule for FM_FALL: rise_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FALL.output_rules.rise_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.output_rules.rise_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: name=rise_rule; port=rise_out; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.output_rules.rise_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - rise_rule width matches SSOT value 1
  - rise_rule RTL expression implements SSOT expression 0
  - DUT port rise_out is the implementation/observation point for rise_rule
  - rise_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FALL.output_rules.rise_rule

### RTL-0048: Implement output rule for FM_FALL: fall_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FALL.output_rules.fall_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.output_rules.fall_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: name=fall_rule; port=fall_out; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.output_rules.fall_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - fall_rule width matches SSOT value 1
  - fall_rule RTL expression implements SSOT expression 1
  - DUT port fall_out is the implementation/observation point for fall_rule
  - fall_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FALL.output_rules.fall_rule

### RTL-0049: Implement state update for FM_FALL: sync1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FALL.state_updates.sync1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.state_updates.sync1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: name=sync1; expr=sig_in; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.state_updates.sync1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync1 width matches SSOT value 1
  - sync1 RTL expression implements SSOT expression sig_in
  - sync1 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FALL.state_updates.sync1

### RTL-0050: Implement state update for FM_FALL: sync2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FALL.state_updates.sync2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.state_updates.sync2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: name=sync2; expr=sync1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.state_updates.sync2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync2 width matches SSOT value 1
  - sync2 RTL expression implements SSOT expression sync1
  - sync2 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FALL.state_updates.sync2

### RTL-0051: Implement state update for FM_FALL: prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FALL.state_updates.prev_sync
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.state_updates.prev_sync.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: name=prev_sync; expr=sync2; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.state_updates.prev_sync
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - prev_sync width matches SSOT value 1
  - prev_sync RTL expression implements SSOT expression sync2
  - prev_sync updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FALL.state_updates.prev_sync

### RTL-0052: Implement side effect for FM_FALL: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_FALL.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FALL.side_effects.side_effect_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_FALL.
SSOT item context: id=FM_FALL; name=falling_edge; port=["rise_out", "fall_out"]; signal=["fall_out pulses for 1 cycle"]; state=["sync1", "sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FALL.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out"] is the implementation/observation point for falling_edge
- SSOT refs: function_model.transactions.FM_FALL.side_effects.side_effect_0

### RTL-0053: Implement transaction FM_STABLE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_STABLE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_STABLE.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: id=FM_STABLE; name=stable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_STABLE
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE

### RTL-0054: Implement precondition for FM_STABLE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_STABLE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.preconditions.precondition_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: value=prev_sync == sync2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE.preconditions.precondition_0

### RTL-0055: Implement input for FM_STABLE: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_STABLE.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.inputs.input_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: id=FM_STABLE; name=stable; port=["rise_out", "fall_out"]; signal=["sig_in"]; state=["sync1", "sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.inputs.input_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out"] is the implementation/observation point for stable
- SSOT refs: function_model.transactions.FM_STABLE.inputs.input_0

### RTL-0056: Implement output for FM_STABLE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_STABLE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.outputs.output_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: value=rise_out=0, fall_out=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.outputs.output_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
- SSOT refs: function_model.transactions.FM_STABLE.outputs.output_0

### RTL-0057: Implement output rule for FM_STABLE: rise_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_STABLE.output_rules.rise_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.output_rules.rise_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=rise_rule; port=rise_out; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.output_rules.rise_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - rise_rule width matches SSOT value 1
  - rise_rule RTL expression implements SSOT expression 0
  - DUT port rise_out is the implementation/observation point for rise_rule
  - rise_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_STABLE.output_rules.rise_rule

### RTL-0058: Implement output rule for FM_STABLE: fall_rule

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_STABLE.output_rules.fall_rule
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.output_rules.fall_rule.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=fall_rule; port=fall_out; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.output_rules.fall_rule
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - fall_rule width matches SSOT value 1
  - fall_rule RTL expression implements SSOT expression 0
  - DUT port fall_out is the implementation/observation point for fall_rule
  - fall_rule is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_STABLE.output_rules.fall_rule

### RTL-0059: Implement state update for FM_STABLE: sync1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.sync1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.sync1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=sync1; expr=sig_in; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.sync1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync1 width matches SSOT value 1
  - sync1 RTL expression implements SSOT expression sig_in
  - sync1 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.sync1

### RTL-0060: Implement state update for FM_STABLE: sync2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.sync2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.sync2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=sync2; expr=sync1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.sync2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sync2 width matches SSOT value 1
  - sync2 RTL expression implements SSOT expression sync1
  - sync2 updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.sync2

### RTL-0061: Implement state update for FM_STABLE: prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_STABLE.state_updates.prev_sync
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_STABLE.state_updates.prev_sync.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.transactions.FM_STABLE.
SSOT item context: name=prev_sync; expr=sync2; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_STABLE.state_updates.prev_sync
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - prev_sync width matches SSOT value 1
  - prev_sync RTL expression implements SSOT expression sync2
  - prev_sync updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_STABLE.state_updates.prev_sync

### RTL-0062: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.
SSOT item context: port=["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]; signal=rise_out = sync2 & ~prev_sync (combinational); state=["sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"] is the implementation/observation point for ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]
- SSOT refs: function_model.invariants.invariant_0

### RTL-0063: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.
SSOT item context: port=["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]; signal=fall_out = ~sync2 & prev_sync (combinational); state=["sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"] is the implementation/observation point for ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]
- SSOT refs: function_model.invariants.invariant_1

### RTL-0064: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via function_model.
SSOT item context: port=["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]; signal=sync2 is always 2-cycle delayed version of sig_in; state=["sync2", "prev_sync"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - DUT port ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"] is the implementation/observation point for ["rise_out", "fall_out", "rise_out", "fall_out", "rise_out", "fall_out"]
- SSOT refs: function_model.invariants.invariant_2
