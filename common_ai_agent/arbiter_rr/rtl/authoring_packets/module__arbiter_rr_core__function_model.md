# RTL Authoring Packet: module__arbiter_rr_core__function_model

- Kind: module
- Owner module: arbiter_rr_core
- Owner file: rtl/arbiter_rr_core.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, dataflow, dataflow.sequence, dataflow.sequence.sequence_0, decomposition.units.arbitrate, features, fsm, fsm.arb_fsm, function_model, function_model.transactions, function_model.transactions.FM1, function_model.transactions.FM2
- Module slice: 1/7 section=function_model task_limit=48
- Slice rule: Owner module arbiter_rr_core is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_core.clk_i <= PCLK (integration.connections[12])
  - arbiter_rr_core.rst_ni <= PRESETn (integration.connections[13])
  - arbiter_rr_core.req_i <= req_i (integration.connections[14])
  - arbiter_rr_core.mask_i <= req_mask (integration.connections[15])
  - arbiter_rr_core.enable_i <= arb_enable (integration.connections[16])
  - arbiter_rr_core.gnt_o <= gnt_o (integration.connections[17])
  - arbiter_rr_core.gnt_valid_o <= gnt_valid_o (integration.connections[18])
  - arbiter_rr_core.gnt_idx_o <= gnt_idx_o (integration.connections[19])
  - arbiter_rr_core.winner_oh_o <= status_winner (integration.connections[20])
  - arbiter_rr_core.active_req_o <= status_active_req (integration.connections[21])

## Tasks

### RTL-0048: Implement RTL state owner for FL state last_winner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.last_winner
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.last_winner.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: name=last_winner; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.last_winner
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - last_winner reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.last_winner

### RTL-0049: Implement RTL state owner for FL state arb_enabled

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.arb_enabled
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.arb_enabled.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: name=arb_enabled; reset=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.arb_enabled
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - arb_enabled reset behavior matches SSOT value 1
- SSOT refs: function_model.state_variables.arb_enabled

### RTL-0050: Implement RTL state owner for FL state req_mask

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.req_mask
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.req_mask.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: name=req_mask; reset=all-ones.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.req_mask
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - req_mask reset behavior matches SSOT value all-ones
- SSOT refs: function_model.state_variables.req_mask

### RTL-0051: Implement transaction FM1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: id=FM1; name=arbitrate_grant.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0052: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=arb_enabled == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0053: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=(req_i & req_mask) != 0 (at least one unmasked active request).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0054: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=req_i: N-bit request vector.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0055: Implement input for FM1: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=req_mask: N-bit mask from CSR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_1

### RTL-0056: Implement input for FM1: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=last_winner: priority rotation base index.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_2

### RTL-0057: Implement output for FM1: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=gnt_o is one-hot with exactly one bit set at selected_index.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_0

### RTL-0058: Implement output for FM1: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=gnt_valid_o == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_1

### RTL-0059: Implement output for FM1: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=gnt_idx_o == selected_index (binary).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_2

### RTL-0060: Implement output for FM1: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.output_3.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=last_winner updated to selected_index.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.output_3
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.outputs.output_3

### RTL-0061: Implement output rule for FM1: grant_index

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.grant_index
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.grant_index.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: name=grant_index; port=gnt_idx_o; expr=1 if ((last_winner == 0) and (((req_i & req_mask) & 2) != 0)) else (2 if ((last_winner == 0) and (((req_i & req_mask)...; width=IDX_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.grant_index
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant_index width matches SSOT value IDX_WIDTH
  - grant_index RTL expression implements SSOT expression 1 if ((last_winner == 0) and (((req_i & req_mask) & 2) != 0)) else (2 if ((last_winner == 0) and (((req_i & req_mask)...
  - DUT port gnt_idx_o is the implementation/observation point for grant_index
  - grant_index is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.grant_index

### RTL-0062: Implement output rule for FM1: grant

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.grant
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.grant.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: name=grant; port=gnt_o; expr=1 << grant_index; width=NUM_REQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.grant
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant width matches SSOT value NUM_REQ
  - grant RTL expression implements SSOT expression 1 << grant_index
  - DUT port gnt_o is the implementation/observation point for grant
  - grant is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.grant

### RTL-0063: Implement output rule for FM1: grant_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM1.output_rules.grant_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.output_rules.grant_valid.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: name=grant_valid; port=gnt_valid_o; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.output_rules.grant_valid
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant_valid width matches SSOT value 1
  - grant_valid RTL expression implements SSOT expression 1
  - DUT port gnt_valid_o is the implementation/observation point for grant_valid
  - grant_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM1.output_rules.grant_valid

### RTL-0064: Implement state update for FM1: last_winner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.last_winner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.last_winner.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: name=last_winner; expr=grant_index; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.last_winner
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - last_winner reset behavior matches SSOT value 0
  - last_winner RTL expression implements SSOT expression grant_index
  - last_winner updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.last_winner

### RTL-0065: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=last_winner rotates to current winner so it gets lowest priority next cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0066: Implement side effect for FM1: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM1.
SSOT item context: value=Only one requestor is granted per cycle (one-hot invariant).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_1

### RTL-0067: Implement transaction FM2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: id=FM2; name=no_grant_idle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0068: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=arb_enabled == 0 OR (req_i & req_mask) == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0069: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=req_i: N-bit request vector.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0070: Implement input for FM2: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=req_mask: N-bit mask.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_1

### RTL-0071: Implement output for FM2: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=gnt_o == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_0

### RTL-0072: Implement output for FM2: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=gnt_valid_o == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_1

### RTL-0073: Implement output for FM2: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=gnt_idx_o == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_2

### RTL-0074: Implement output for FM2: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM2.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.outputs.output_3.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=last_winner unchanged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.outputs.output_3
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.outputs.output_3

### RTL-0075: Implement output rule for FM2: grant

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.grant
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.grant.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: name=grant; port=gnt_o; expr=0; width=NUM_REQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.grant
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant width matches SSOT value NUM_REQ
  - grant RTL expression implements SSOT expression 0
  - DUT port gnt_o is the implementation/observation point for grant
  - grant is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.grant

### RTL-0076: Implement output rule for FM2: grant_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.grant_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.grant_valid.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: name=grant_valid; port=gnt_valid_o; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.grant_valid
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant_valid width matches SSOT value 1
  - grant_valid RTL expression implements SSOT expression 0
  - DUT port gnt_valid_o is the implementation/observation point for grant_valid
  - grant_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.grant_valid

### RTL-0077: Implement output rule for FM2: grant_index

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM2.output_rules.grant_index
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.output_rules.grant_index.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: name=grant_index; port=gnt_idx_o; expr=0; width=IDX_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.output_rules.grant_index
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - grant_index width matches SSOT value IDX_WIDTH
  - grant_index RTL expression implements SSOT expression 0
  - DUT port gnt_idx_o is the implementation/observation point for grant_index
  - grant_index is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM2.output_rules.grant_index

### RTL-0078: Implement state update for FM2: last_winner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.last_winner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.last_winner.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: name=last_winner; expr=last_winner; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.last_winner
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - last_winner reset behavior matches SSOT value 0
  - last_winner RTL expression implements SSOT expression last_winner
  - last_winner updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.last_winner

### RTL-0079: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.transactions.FM2.
SSOT item context: value=last_winner is preserved unchanged when no grant is issued.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0080: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=At most one bit in gnt_o is asserted per cycle (one-hot invariant)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0081: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=gnt_valid_o == 0 implies gnt_o == 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0082: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=gnt_valid_o == 1 implies exactly one bit in gnt_o is set and gnt_idx_o equals the index of that bit..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0083: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=Masked requests never receive a grant regardless of req_i state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0084: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=When arb_enabled == 0, all outputs are zero and last_winner is frozen..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_4

### RTL-0085: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via function_model.
SSOT item context: value=Round-robin fairness: a requestor that was granted in the previous cycle has the lowest priority in the current cycle..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: function_model.invariants.invariant_5
