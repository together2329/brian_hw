# RTL Authoring Packet: module__edge_detector__function_model

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 20
- Required tasks: 20

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
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, decomposition.units.csr_decode, decomposition.units.edge_detect, decomposition.units.sync, features, function_model, function_model.state_variables.control_reg, function_model.state_variables.prev_sync, function_model.state_variables.status_overflow, function_model.state_variables.status_sticky, function_model.state_variables.sync_chain, function_model.transactions.DETECT, function_model.transactions.DETECT.inputs.signal_i_at_PCLK_domain_after_sync
- Module slice: 5/16 section=function_model task_limit=48
- Slice rule: Owner module edge_detector is split into 16 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4
- SSOT connection contracts:
  - edge_detector.PCLK <= PCLK (integration.connections[0])
  - edge_detector.PRESETn <= PRESETn (integration.connections[1])
  - edge_detector.signal_i <= signal_i (integration.connections[2])
  - edge_detector.edge_o <= edge_o (integration.connections[3])
  - edge_detector.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0048: Implement RTL state owner for FL state sync_chain

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.sync_chain
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.sync_chain.
Owner: edge_detector in rtl/edge_detector.sv via function_model.state_variables.sync_chain.
SSOT item context: name=sync_chain; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.sync_chain
  - Primary implementation evidence is in rtl/edge_detector.sv
  - sync_chain reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.sync_chain

### RTL-0049: Implement RTL state owner for FL state prev_sync

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.prev_sync
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.prev_sync.
Owner: edge_detector in rtl/edge_detector.sv via function_model.state_variables.prev_sync.
SSOT item context: name=prev_sync; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.prev_sync
  - Primary implementation evidence is in rtl/edge_detector.sv
  - prev_sync reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.prev_sync

### RTL-0050: Implement RTL state owner for FL state control_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.control_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.control_reg.
Owner: edge_detector in rtl/edge_detector.sv via function_model.state_variables.control_reg.
SSOT item context: name=control_reg; reset=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.control_reg
  - Primary implementation evidence is in rtl/edge_detector.sv
  - control_reg reset behavior matches SSOT value 2
- SSOT refs: function_model.state_variables.control_reg

### RTL-0051: Implement RTL state owner for FL state status_sticky

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status_sticky
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status_sticky.
Owner: edge_detector in rtl/edge_detector.sv via function_model.state_variables.status_sticky.
SSOT item context: name=status_sticky; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status_sticky
  - Primary implementation evidence is in rtl/edge_detector.sv
  - status_sticky reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status_sticky

### RTL-0052: Implement RTL state owner for FL state status_overflow

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status_overflow
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status_overflow.
Owner: edge_detector in rtl/edge_detector.sv via function_model.state_variables.status_overflow.
SSOT item context: name=status_overflow; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status_overflow
  - Primary implementation evidence is in rtl/edge_detector.sv
  - status_overflow reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status_overflow

### RTL-0053: Implement transaction DETECT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.DETECT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.DETECT.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.preconditions.sync_chain_has_propagated_at_least_SYNC_STAGES_cycles_since_reset_deassertion.
SSOT item context: id=DETECT; name=edge_detect.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.DETECT
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT

### RTL-0054: Implement precondition for DETECT: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.DETECT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.preconditions.precondition_0.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.preconditions.precondition_0

### RTL-0055: Implement precondition for DETECT: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.DETECT.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.preconditions.precondition_1.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=sync_chain has propagated at least SYNC_STAGES cycles since reset deassertion.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.preconditions.precondition_1
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.preconditions.precondition_1

### RTL-0056: Implement input for DETECT: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.DETECT.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.inputs.input_0.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=signal_i at PCLK domain (after sync).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.inputs.input_0
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.inputs.input_0

### RTL-0057: Implement output for DETECT: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.DETECT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.outputs.output_0.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=edge_o[width-1:0] = 1 for one cycle per detected edge matching EDGE_MODE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.outputs.output_0
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.outputs.output_0

### RTL-0058: Implement output for DETECT: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.DETECT.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.outputs.output_1.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=status_sticky |= edge_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.outputs.output_1
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.outputs.output_1

### RTL-0059: Implement output for DETECT: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.DETECT.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.outputs.output_2.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=status_overflow |= edge_o & status_sticky.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.outputs.output_2
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.outputs.output_2

### RTL-0060: Implement output for DETECT: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.DETECT.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.outputs.output_3.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=irq_o = |edge_o && irq_enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.outputs.output_3
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.outputs.output_3

### RTL-0061: Implement output rule for DETECT: edge_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.DETECT.output_rules.edge_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.output_rules.edge_o.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.output_rules.edge_o.
SSOT item context: name=edge_o; port=edge_o; expr=(curr_sync ^ prev_sync) & mode_mask & {WIDTH{enable}}; width=WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.output_rules.edge_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - edge_o width matches SSOT value WIDTH
  - edge_o RTL expression implements SSOT expression (curr_sync ^ prev_sync) & mode_mask & {WIDTH{enable}}
  - DUT port edge_o is the implementation/observation point for edge_o
  - edge_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.DETECT.output_rules.edge_o

### RTL-0062: Implement output rule for DETECT: irq_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.DETECT.output_rules.irq_o
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.output_rules.irq_o.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.output_rules.irq_o.
SSOT item context: name=irq_o; port=irq_o; expr=|edge_o && irq_enable; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.output_rules.irq_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - irq_o width matches SSOT value 1
  - irq_o RTL expression implements SSOT expression |edge_o && irq_enable
  - DUT port irq_o is the implementation/observation point for irq_o
  - irq_o is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.DETECT.output_rules.irq_o

### RTL-0063: Implement side effect for DETECT: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.DETECT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.side_effects.side_effect_0.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=sync_chain shifts every PCLK cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.side_effects.side_effect_0

### RTL-0064: Implement side effect for DETECT: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.DETECT.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.DETECT.side_effects.side_effect_1.
Owner: edge_detector in rtl/edge_detector.sv via function_model.transactions.DETECT.
SSOT item context: value=prev_sync updates to last stage of sync_chain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.DETECT.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.transactions.DETECT.side_effects.side_effect_1

### RTL-0065: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: edge_detector in rtl/edge_detector.sv via function_model.
SSOT item context: value=edge_o is asserted for exactly one PCLK cycle per qualifying edge transition..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0066: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: edge_detector in rtl/edge_detector.sv via function_model.
SSOT item context: value=No edge_o pulse occurs when enable == 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0067: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: edge_detector in rtl/edge_detector.sv via function_model.
SSOT item context: value=status_sticky persists until software W1C clear..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: function_model.invariants.invariant_2
