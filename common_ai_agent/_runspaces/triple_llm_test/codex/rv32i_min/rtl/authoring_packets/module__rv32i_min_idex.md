# RTL Authoring Packet: module__rv32i_min_idex

- Kind: module
- Owner module: rv32i_min_idex
- Owner file: rtl/rv32i_min_idex.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.FM_ALU, function_model.transactions.FM_BRANCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, registers, registers.register_list
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8

## Tasks

### RTL-0021: Implement decode execute and system instruction control

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Decode RV32I subset and produce ALU compare jump target and system behavior including FENCE bubble and illegal shamt detect
SSOT ref: workflow_todos.rtl-gen[1].
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via workflow_todos.owner.
SSOT item context: id=RTL_IDEX_STAGE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All 37 opcodes decode to declared function_model transaction classes
  - Illegal shamt triggers exception path with no retirement
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - Semantic source_refs covered: fsm.control, function_model.transactions.FM_ALU, function_model.transactions.FM_BRANCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM
- SSOT refs: fsm.control, function_model.transactions.FM_ALU, function_model.transactions.FM_BRANCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, workflow_todos.rtl-gen[1]

### RTL-0051: Implement RTL state owner for FL state pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.state_variables.
SSOT item context: name=pc; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - pc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.pc

### RTL-0053: Implement RTL state owner for FL state excpt_o

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.excpt_o
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.excpt_o.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.state_variables.
SSOT item context: name=excpt_o; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.excpt_o
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - excpt_o reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.excpt_o

### RTL-0062: Implement transaction FM_ALU

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ALU
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ALU.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: id=FM_ALU; name=alu_and_immediate_ops.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ALU
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU

### RTL-0063: Implement precondition for FM_ALU: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ALU.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.preconditions.precondition_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=opcode_class == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.preconditions.precondition_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.preconditions.precondition_0

### RTL-0064: Implement input for FM_ALU: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALU.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.inputs.input_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=rs1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.inputs.input_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.inputs.input_0

### RTL-0065: Implement input for FM_ALU: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALU.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.inputs.input_1.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=rs2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.inputs.input_1
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.inputs.input_1

### RTL-0066: Implement input for FM_ALU: input_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALU.inputs.input_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.inputs.input_2.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=imm.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.inputs.input_2
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.inputs.input_2

### RTL-0067: Implement input for FM_ALU: input_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALU.inputs.input_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.inputs.input_3.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=funct3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.inputs.input_3
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.inputs.input_3

### RTL-0068: Implement input for FM_ALU: input_4

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALU.inputs.input_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.inputs.input_4.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=funct7.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.inputs.input_4
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.inputs.input_4

### RTL-0069: Implement output for FM_ALU: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALU.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.outputs.output_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=rd receives computed 32-bit result.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.outputs.output_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.outputs.output_0

### RTL-0070: Implement state update for FM_ALU: wb_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALU.state_updates.wb_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.state_updates.wb_data.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: name=wb_data; expr=alu_result & ((1 << 32) - 1); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.state_updates.wb_data
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - wb_data width matches SSOT value 32
  - wb_data RTL expression implements SSOT expression alu_result & ((1 << 32) - 1)
  - wb_data updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALU.state_updates.wb_data

### RTL-0071: Implement side effect for FM_ALU: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ALU.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.side_effects.side_effect_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: value=regfile writeback occurs when rd != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: function_model.transactions.FM_ALU.side_effects.side_effect_0

### RTL-0072: Implement error case for FM_ALU: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ALU.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALU.error_cases.error_case_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via function_model.transactions.FM_ALU.
SSOT item context: condition=illegal_shamt.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALU.error_cases.error_case_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - function_model.transactions.FM_ALU.error_cases.error_case_0 condition is implemented as RTL control logic: illegal_shamt
- SSOT refs: function_model.transactions.FM_ALU.error_cases.error_case_0

### RTL-0138: Implement CSR/register GPR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.GPR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.GPR.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via registers.register_list.
SSOT item context: name=GPR; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.GPR
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - GPR width matches SSOT value 32
  - GPR reset behavior matches SSOT value 0
  - GPR access policy rw is implemented without read/write shortcuts
  - GPR decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.GPR

### RTL-0139: Implement field GPR.value

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GPR.fields.value
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GPR.fields.value.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via registers.register_list.
SSOT item context: name=value; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GPR.fields.value
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - value reset behavior matches SSOT value 0
  - value access policy rw is implemented without read/write shortcuts
  - value readback returns implemented RTL state when readable
  - value write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GPR.fields.value

### RTL-0143: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: value=RESET.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0144: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: value=RUN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0145: Implement FSM state control.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_2.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: value=FENCE_BUBBLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_2
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: fsm.control.states.state_2

### RTL-0146: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: from=RESET; to=RUN; condition=rst_n_deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: rst_n_deasserted
  - fsm.control.transitions.transition_0 transition path RESET -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0147: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: from=RUN; to=FENCE_BUBBLE; condition=decoded_fence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: decoded_fence
  - fsm.control.transitions.transition_1 transition path RUN -> FENCE_BUBBLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0148: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via fsm.control.
SSOT item context: from=FENCE_BUBBLE; to=RUN; condition=bubble_done.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
  - fsm.control.transitions.transition_2 condition is implemented as RTL control logic: bubble_done
  - fsm.control.transitions.transition_2 transition path FENCE_BUBBLE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0149: Implement feature RV32I_37_instruction_support

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.RV32I_37_instruction_support
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.RV32I_37_instruction_support.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via features.
SSOT item context: name=RV32I_37_instruction_support; output=Architectural pc and regfile updates with load-store bus traffic.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.RV32I_37_instruction_support
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: features.RV32I_37_instruction_support

### RTL-0150: Implement feature x0_hardwired_zero

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.x0_hardwired_zero
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.x0_hardwired_zero.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via features.
SSOT item context: name=x0_hardwired_zero; output=x0 reads as zero always.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.x0_hardwired_zero
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: features.x0_hardwired_zero

### RTL-0151: Implement feature exception_pulse_profile

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.exception_pulse_profile
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.exception_pulse_profile.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via features.
SSOT item context: name=exception_pulse_profile; output=excpt_o pulse with defined pc behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.exception_pulse_profile
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: features.exception_pulse_profile

### RTL-0172: Prove module rv32i_min_idex is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.rv32i_min_idex.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.rv32i_min_idex.module_equivalence.
Owner: rv32i_min_idex in rtl/rv32i_min_idex.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.rv32i_min_idex.module_equivalence
  - Primary implementation evidence is in rtl/rv32i_min_idex.sv
- SSOT refs: sub_modules.rv32i_min_idex.module_equivalence
