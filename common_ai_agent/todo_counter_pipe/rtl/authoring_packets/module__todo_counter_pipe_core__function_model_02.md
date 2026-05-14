# RTL Authoring Packet: module__todo_counter_pipe_core__function_model_02

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 2/9 section=function_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0091: Implement precondition for FM4: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_2

### RTL-0092: Implement precondition for FM4: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM4.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.preconditions.precondition_3

### RTL-0093: Implement input for FM4: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM4.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.inputs.input_0

### RTL-0094: Implement output for FM4: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=tc_pending ← 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_0

### RTL-0095: Implement output for FM4: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==0 (saturate): cnt stays at 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_1

### RTL-0096: Implement output for FM4: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM4.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.outputs.output_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==1 (wrap): cnt ← 2^WIDTH - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.outputs.output_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.outputs.output_2

### RTL-0097: Implement side effect for FM4: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=tc_pending set to 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_0

### RTL-0098: Implement side effect for FM4: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt updated per mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_1

### RTL-0099: Implement side effect for FM4: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM4.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM4.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If wrap: further down-count from MAX proceeds normally.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM4.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM4.side_effects.side_effect_2

### RTL-0100: Implement transaction FM5

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM5
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM5.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: id=FM5; name=overflow_up.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM5
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5

### RTL-0101: Implement precondition for FM5: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_0

### RTL-0102: Implement precondition for FM5: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=up_down == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_1

### RTL-0103: Implement precondition for FM5: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt == 2^WIDTH - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_2

### RTL-0104: Implement precondition for FM5: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM5.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.preconditions.precondition_3

### RTL-0105: Implement input for FM5: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM5.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.inputs.input_0

### RTL-0106: Implement output for FM5: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=ovf_pending ← 1, overflow ← 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_0

### RTL-0107: Implement output for FM5: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==0 (saturate): cnt stays at MAX.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_1

### RTL-0108: Implement output for FM5: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM5.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.outputs.output_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==1 (wrap): cnt ← 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.outputs.output_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.outputs.output_2

### RTL-0109: Implement side effect for FM5: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=overflow sticky flag set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_0

### RTL-0110: Implement side effect for FM5: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=ovf_pending set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_1

### RTL-0111: Implement side effect for FM5: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM5.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM5.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt updated per mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM5.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM5.side_effects.side_effect_2

### RTL-0112: Implement transaction FM6

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM6
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM6.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: id=FM6; name=underflow_down.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM6
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6

### RTL-0113: Implement precondition for FM6: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_0

### RTL-0114: Implement precondition for FM6: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=up_down == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_1

### RTL-0115: Implement precondition for FM6: precondition_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_2

### RTL-0116: Implement precondition for FM6: precondition_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM6.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.preconditions.precondition_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.preconditions.precondition_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.preconditions.precondition_3

### RTL-0117: Implement input for FM6: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM6.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=event_i rising edge.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.inputs.input_0

### RTL-0118: Implement output for FM6: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=unf_pending ← 1, underflow ← 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_0

### RTL-0119: Implement output for FM6: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==0 (saturate): cnt stays at 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_1

### RTL-0120: Implement output for FM6: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM6.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.outputs.output_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If mode==1 (wrap): cnt ← 2^WIDTH - 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.outputs.output_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.outputs.output_2

### RTL-0121: Implement side effect for FM6: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=underflow sticky flag set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_0

### RTL-0122: Implement side effect for FM6: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=unf_pending set.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_1

### RTL-0123: Implement side effect for FM6: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM6.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM6.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt updated per mode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM6.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM6.side_effects.side_effect_2

### RTL-0124: Implement transaction FM7

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM7
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM7.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: id=FM7; name=clear_counter.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM7
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7

### RTL-0125: Implement precondition for FM7: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM7.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=CTRL.clear written 1 (CDC-synced pulse to core).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.preconditions.precondition_0

### RTL-0126: Implement input for FM7: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM7.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=clear pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.inputs.input_0

### RTL-0127: Implement output for FM7: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM7.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt ← 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.outputs.output_0

### RTL-0128: Implement side effect for FM7: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM7.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt is set to 0 regardless of enable/mode/direction.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.side_effects.side_effect_0

### RTL-0129: Implement side effect for FM7: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM7.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=Does not affect overflow/underflow sticky flags.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.side_effects.side_effect_1

### RTL-0130: Implement side effect for FM7: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM7.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM7.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=Does not affect tc_pending status.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM7.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM7.side_effects.side_effect_2

### RTL-0131: Implement transaction FM8

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM8
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM8.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: id=FM8; name=load_counter.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM8
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8

### RTL-0132: Implement precondition for FM8: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM8.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.preconditions.precondition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=CTRL.load written 1 (CDC-synced pulse to core).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.preconditions.precondition_0

### RTL-0133: Implement input for FM8: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM8.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.inputs.input_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=load pulse, load_value from LOAD register.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.inputs.input_0

### RTL-0134: Implement output for FM8: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM8.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.outputs.output_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt ← load_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.outputs.output_0

### RTL-0135: Implement side effect for FM8: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM8.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.side_effects.side_effect_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=cnt is set to load_value regardless of enable/mode/direction.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.side_effects.side_effect_0

### RTL-0136: Implement side effect for FM8: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM8.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.side_effects.side_effect_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=Does not affect overflow/underflow sticky flags.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.side_effects.side_effect_1

### RTL-0137: Implement side effect for FM8: side_effect_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM8.side_effects.side_effect_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.side_effects.side_effect_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=Does not affect tc_pending status.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.side_effects.side_effect_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.side_effects.side_effect_2

### RTL-0138: Implement side effect for FM8: side_effect_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM8.side_effects.side_effect_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM8.side_effects.side_effect_3.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via function_model.transactions.
SSOT item context: value=If new cnt exceeds term while up-counting, terminal count comparison uses new value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM8.side_effects.side_effect_3
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: function_model.transactions.FM8.side_effects.side_effect_3
