# RTL Authoring Packet: module__todo_counter_pipe_regs__function_model

- Kind: module
- Owner module: todo_counter_pipe_regs
- Owner file: rtl/todo_counter_pipe_regs.sv
- Task count: 7
- Required tasks: 7

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
- Owner refs: cycle_model.handshake_rules.counter_irq, cycle_model.handshake_rules.prdata, cycle_model.handshake_rules.pready, cycle_model.pipeline.S0_APB_ACCESS, cycle_model.pipeline.S4_STATUS_UPDATE, decomposition.units.apb_decode, function_model.transactions.FM10, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CNT, registers.register_list.CTRL, registers.register_list.DBGCNT, registers.register_list.INTCLR
- Module slice: 2/7 section=function_model task_limit=48
- Slice rule: Owner module todo_counter_pipe_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_regs.bus_clk <= bus_clk (integration.connections[0])
  - todo_counter_pipe_regs.bus_rst_n <= bus_rst_n (integration.connections[1])
  - todo_counter_pipe_regs.irq_o <= counter_irq (integration.connections[2])

## Tasks

### RTL-0145: Implement transaction FM10

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM10
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM10.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: id=FM10; name=interrupt_clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM10
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10

### RTL-0146: Implement precondition for FM10: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM10.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.preconditions.precondition_0.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=INTCLR.tc_clr, .ovf_clr, or .unf_clr written 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.preconditions.precondition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.preconditions.precondition_0

### RTL-0147: Implement input for FM10: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM10.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.inputs.input_0.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=W1C write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.inputs.input_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.inputs.input_0

### RTL-0148: Implement output for FM10: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM10.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.outputs.output_0.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=Corresponding INTSTAT bit cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.outputs.output_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.outputs.output_0

### RTL-0149: Implement output for FM10: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM10.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.outputs.output_1.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=For ovf_clr: STATUS.overflow cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.outputs.output_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.outputs.output_1

### RTL-0150: Implement output for FM10: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM10.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.outputs.output_2.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=For unf_clr: STATUS.underflow cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.outputs.output_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.outputs.output_2

### RTL-0151: Implement side effect for FM10: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM10.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM10.side_effects.side_effect_0.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via function_model.transactions.FM10.
SSOT item context: value=counter_irq deasserts if no other enabled pending sources remain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM10.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
- SSOT refs: function_model.transactions.FM10.side_effects.side_effect_0
