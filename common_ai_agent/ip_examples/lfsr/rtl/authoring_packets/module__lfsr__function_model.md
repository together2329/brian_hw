# RTL Authoring Packet: module__lfsr__function_model

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 32
- Required tasks: 32

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 5/13 section=function_model task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0041: Implement RTL state owner for FL state lfsr_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.lfsr_state
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.lfsr_state.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=lfsr_state; reset=DEFAULT_SEED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.lfsr_state
  - Primary implementation evidence is in rtl/lfsr.sv
  - lfsr_state reset behavior matches SSOT value DEFAULT_SEED
- SSOT refs: function_model.state_variables.lfsr_state

### RTL-0042: Implement RTL state owner for FL state poly_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.poly_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.poly_reg.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=poly_reg; reset=DEFAULT_POLY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.poly_reg
  - Primary implementation evidence is in rtl/lfsr.sv
  - poly_reg reset behavior matches SSOT value DEFAULT_POLY
- SSOT refs: function_model.state_variables.poly_reg

### RTL-0043: Implement RTL state owner for FL state ctrl_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.ctrl_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.ctrl_reg.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=ctrl_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.ctrl_reg
  - Primary implementation evidence is in rtl/lfsr.sv
  - ctrl_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.ctrl_reg

### RTL-0044: Implement RTL state owner for FL state status_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.status_reg
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.status_reg.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=status_reg; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.status_reg
  - Primary implementation evidence is in rtl/lfsr.sv
  - status_reg reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.status_reg

### RTL-0045: Implement transaction FM1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM1
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: id=FM1; name=single_step_prbs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1

### RTL-0046: Implement precondition for FM1: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=ctrl_reg.enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_0

### RTL-0047: Implement precondition for FM1: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM1.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.preconditions.precondition_1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=lfsr_state != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.preconditions.precondition_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1.preconditions.precondition_1

### RTL-0048: Implement input for FM1: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=lfsr_state (current).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_0

### RTL-0049: Implement input for FM1: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM1.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.inputs.input_1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=poly_reg (tap mask).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.inputs.input_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1.inputs.input_1

### RTL-0050: Implement output for FM1: prbs_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.prbs_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.prbs_out.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=prbs_out; port=prbs_out; expr=lfsr_state; width=LFSR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.prbs_out
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_out width matches SSOT value LFSR_WIDTH
  - prbs_out RTL expression implements SSOT expression lfsr_state
  - DUT port prbs_out is the implementation/observation point for prbs_out
- SSOT refs: function_model.transactions.FM1.outputs.prbs_out

### RTL-0051: Implement output for FM1: prbs_bit

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM1.outputs.prbs_bit
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.outputs.prbs_bit.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=prbs_bit; port=prbs_bit; expr=lfsr_state[0]; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.outputs.prbs_bit
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_bit width matches SSOT value 1
  - prbs_bit RTL expression implements SSOT expression lfsr_state[0]
  - DUT port prbs_bit is the implementation/observation point for prbs_bit
- SSOT refs: function_model.transactions.FM1.outputs.prbs_bit

### RTL-0052: Implement state update for FM1: lfsr_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM1.state_updates.lfsr_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.state_updates.lfsr_state.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=lfsr_state; expr={feedback_bit, lfsr_state[LFSR_WIDTH-1:1]} where feedback_bit = ^(lfsr_state & poly_reg); reset=DEFAULT_SEED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.state_updates.lfsr_state
  - Primary implementation evidence is in rtl/lfsr.sv
  - lfsr_state reset behavior matches SSOT value DEFAULT_SEED
  - lfsr_state RTL expression implements SSOT expression {feedback_bit, lfsr_state[LFSR_WIDTH-1:1]} where feedback_bit = ^(lfsr_state & poly_reg)
  - lfsr_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM1.state_updates.lfsr_state

### RTL-0053: Implement side effect for FM1: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM1.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM1.side_effects.side_effect_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=status_reg.running set to 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM1.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM1.side_effects.side_effect_0

### RTL-0054: Implement transaction FM2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM2
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM2.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: id=FM2; name=load_seed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM2
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM2

### RTL-0055: Implement precondition for FM2: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM2.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.preconditions.precondition_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=APB write to SEED register (offset 0x08).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.preconditions.precondition_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM2.preconditions.precondition_0

### RTL-0056: Implement input for FM2: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM2.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.inputs.input_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=PWDATA[APB_DATA_WIDTH-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.inputs.input_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM2.inputs.input_0

### RTL-0057: Implement state update for FM2: lfsr_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM2.state_updates.lfsr_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.state_updates.lfsr_state.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=lfsr_state; expr=PWDATA truncated to LFSR_WIDTH bits; reset=DEFAULT_SEED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.state_updates.lfsr_state
  - Primary implementation evidence is in rtl/lfsr.sv
  - lfsr_state reset behavior matches SSOT value DEFAULT_SEED
  - lfsr_state RTL expression implements SSOT expression PWDATA truncated to LFSR_WIDTH bits
  - lfsr_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM2.state_updates.lfsr_state

### RTL-0058: Implement side effect for FM2: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM2.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM2.side_effects.side_effect_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=prbs_valid deasserted for one cycle after load.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM2.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM2.side_effects.side_effect_0

### RTL-0059: Implement transaction FM3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM3
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM3.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: id=FM3; name=load_polynomial.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM3
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM3

### RTL-0060: Implement precondition for FM3: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=APB write to POLY register (offset 0x04).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_0

### RTL-0061: Implement precondition for FM3: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM3.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.preconditions.precondition_1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=ctrl_reg.enable == 0 (polynomial change only when halted).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.preconditions.precondition_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM3.preconditions.precondition_1

### RTL-0062: Implement input for FM3: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM3.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.inputs.input_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=PWDATA[APB_DATA_WIDTH-1:0].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.inputs.input_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM3.inputs.input_0

### RTL-0063: Implement state update for FM3: poly_reg

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM3.state_updates.poly_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM3.state_updates.poly_reg.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=poly_reg; expr=PWDATA truncated to LFSR_WIDTH bits; reset=DEFAULT_POLY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM3.state_updates.poly_reg
  - Primary implementation evidence is in rtl/lfsr.sv
  - poly_reg reset behavior matches SSOT value DEFAULT_POLY
  - poly_reg RTL expression implements SSOT expression PWDATA truncated to LFSR_WIDTH bits
  - poly_reg updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM3.state_updates.poly_reg

### RTL-0064: Implement transaction FM4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM4
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM4.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: id=FM4; name=lockup_recovery.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM4
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM4

### RTL-0065: Implement precondition for FM4: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=lfsr_state == 0 after a step.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_0

### RTL-0066: Implement output for FM4: prbs_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.prbs_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.prbs_valid.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=prbs_valid; port=prbs_valid; expr=0; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.prbs_valid
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_valid width matches SSOT value 1
  - prbs_valid RTL expression implements SSOT expression 0
  - DUT port prbs_valid is the implementation/observation point for prbs_valid
- SSOT refs: function_model.transactions.FM4.outputs.prbs_valid

### RTL-0067: Implement state update for FM4: lfsr_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM4.state_updates.lfsr_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.state_updates.lfsr_state.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: name=lfsr_state; expr=DEFAULT_SEED if ctrl_reg.auto_reload else 0; reset=DEFAULT_SEED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.state_updates.lfsr_state
  - Primary implementation evidence is in rtl/lfsr.sv
  - lfsr_state reset behavior matches SSOT value DEFAULT_SEED
  - lfsr_state RTL expression implements SSOT expression DEFAULT_SEED if ctrl_reg.auto_reload else 0
  - lfsr_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM4.state_updates.lfsr_state

### RTL-0068: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=status_reg.lockup set to 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0069: Implement side effect for FM4: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=status_reg.running cleared to 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_1

### RTL-0070: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=LFSR state never changes when ctrl_reg.enable == 0 except via APB write to SEED or reset..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0071: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=Polynomial register is writable only when enable == 0..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0072: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: lfsr in rtl/lfsr.sv via function_model.
SSOT item context: value=All-zero state is detected and either auto-reloaded or held..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: function_model.invariants.invariant_2
