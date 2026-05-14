# RTL Authoring Packet: module__todo_counter_pipe_core__function_model_03

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
- Task count: 14
- Required tasks: 14

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
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 3/8 section=function_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0139: Implement transaction FM9

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM9
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM9.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: id=FM9; name=no_count_disabled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM9
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9

### RTL-0140: Implement precondition for FM9: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM9.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=enable == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9.preconditions.precondition_0

### RTL-0141: Implement input for FM9: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM9.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=event_i may toggle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9.inputs.input_0

### RTL-0142: Implement output for FM9: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM9.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt unchanged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9.outputs.output_0

### RTL-0143: Implement side effect for FM9: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM9.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt is preserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9.side_effects.side_effect_0

### RTL-0144: Implement side effect for FM9: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM9.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM9.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=dbg_cycle_count continues incrementing.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM9.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM9.side_effects.side_effect_1

### RTL-0152: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt never exceeds 2^WIDTH - 1 in saturate mode..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0153: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=cnt never goes below 0 in saturate mode..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0154: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=overflow is set only when cnt transitions through MAX while counting up..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0155: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=underflow is set only when cnt transitions through 0 while counting down..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_3

### RTL-0156: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=tc_pending is set when cnt reaches term (up) or 0 (down) on a count event..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_4

### RTL-0157: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=clear and load take priority over normal count/terminal/overflow/underflow logic..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_5

### RTL-0158: Preserve FL invariant invariant_6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_6
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_6.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=Register read side effects are exactly those listed in registers.register_list..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_6
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_6

### RTL-0159: Preserve FL invariant invariant_7

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_7
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_7.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.
SSOT item context: value=dbg_cycle_count increments on every core_clk edge, independent of enable or event_i..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_7
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.invariants.invariant_7
