# RTL Authoring Packet: module__arm_m0_min_id

- Kind: module
- Owner module: arm_m0_min_id
- Owner file: rtl/arm_m0_min_id.sv
- Task count: 31
- Required tasks: 31

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
- Owner refs: fsm, fsm.core, fsm.core.states.DECODE, function_model, function_model.transactions.TX_DECODE_EXEC, isa_spec, isa_spec.decode_contract

## Tasks

### RTL-0028: Implement supported Thumb-1 decode/execute subset

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement decode and execution for listed instructions with correct writeback and flag policy.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_ISA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Only supported opcodes retire
  - CMP updates flags without destination register write
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - Semantic source_refs covered: custom.assumptions, function_model.transactions.TX_DECODE_EXEC, isa_spec
- SSOT refs: custom.assumptions, function_model.transactions.TX_DECODE_EXEC, isa_spec, workflow_todos.rtl-gen[1]

### RTL-0060: Implement transaction TX_DECODE_EXEC

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.TX_DECODE_EXEC
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: id=TX_DECODE_EXEC; name=alu_compare_branch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC

### RTL-0061: Implement precondition for TX_DECODE_EXEC: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=fault_halt == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_0

### RTL-0062: Implement precondition for TX_DECODE_EXEC: precondition_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=instruction fetch completed with i_hready == 1 and i_hresp == OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.preconditions.precondition_1

### RTL-0063: Implement input for TX_DECODE_EXEC: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.TX_DECODE_EXEC.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.inputs.input_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=decoded opcode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.inputs.input_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.inputs.input_0

### RTL-0064: Implement input for TX_DECODE_EXEC: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.TX_DECODE_EXEC.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.inputs.input_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=operand values from architectural registers.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.inputs.input_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.inputs.input_1

### RTL-0065: Implement output for TX_DECODE_EXEC: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=ALU destination register update for ADD/SUB/AND/ORR/EOR/MOV/LSL/LSR/ASR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.outputs.output_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.outputs.output_0

### RTL-0066: Implement output for TX_DECODE_EXEC: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=NZCV updated only for CMP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.outputs.output_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.outputs.output_1

### RTL-0067: Implement output for TX_DECODE_EXEC: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.outputs.output_2.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=PC updated sequentially or redirected for B/BEQ/BNE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.outputs.output_2
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.outputs.output_2

### RTL-0068: Implement output rule for TX_DECODE_EXEC: pc_next_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.TX_DECODE_EXEC.output_rules.pc_next_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.output_rules.pc_next_addr.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: name=pc_next_addr; port=i_haddr; expr=(branch_target) if (branch_taken) else ((pc + 2)); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.output_rules.pc_next_addr
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - pc_next_addr width matches SSOT value 32
  - pc_next_addr RTL expression implements SSOT expression (branch_target) if (branch_taken) else ((pc + 2))
  - DUT port i_haddr is the implementation/observation point for pc_next_addr
  - pc_next_addr is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.output_rules.pc_next_addr

### RTL-0069: Implement output rule for TX_DECODE_EXEC: store_data_mux

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.TX_DECODE_EXEC.output_rules.store_data_mux
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.output_rules.store_data_mux.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: name=store_data_mux; port=d_hwdata; expr=(rs2) if (is_store) else (0); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.output_rules.store_data_mux
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - store_data_mux width matches SSOT value 32
  - store_data_mux RTL expression implements SSOT expression (rs2) if (is_store) else (0)
  - DUT port d_hwdata is the implementation/observation point for store_data_mux
  - store_data_mux is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.output_rules.store_data_mux

### RTL-0070: Implement side effect for TX_DECODE_EXEC: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=pc advances by instruction size on non-branch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_0

### RTL-0071: Implement side effect for TX_DECODE_EXEC: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: value=pc set to target when branch taken.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.side_effects.side_effect_1

### RTL-0072: Implement error case for TX_DECODE_EXEC: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.TX_DECODE_EXEC.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.TX_DECODE_EXEC.error_cases.error_case_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.transactions.TX_DECODE_EXEC.
SSOT item context: condition=instruction bus response ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.TX_DECODE_EXEC.error_cases.error_case_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - function_model.transactions.TX_DECODE_EXEC.error_cases.error_case_0 condition is implemented as RTL control logic: instruction bus response ERROR
- SSOT refs: function_model.transactions.TX_DECODE_EXEC.error_cases.error_case_0

### RTL-0085: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.
SSOT item context: value=No instruction retires while fault_halt==1..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0086: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.
SSOT item context: value=IF/ID/EX ordering remains in-order with no out-of-order commit..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0087: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via function_model.
SSOT item context: value=Register writes occur only from committed EX outcomes..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0104: Implement FSM state core.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.states.state_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: value=RESET.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core.states.state_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: fsm.core.states.state_0

### RTL-0105: Implement FSM state core.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.states.state_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: value=RUN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core.states.state_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: fsm.core.states.state_1

### RTL-0106: Implement FSM state core.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.states.state_2.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: value=STALL_IF.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core.states.state_2
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: fsm.core.states.state_2

### RTL-0107: Implement FSM state core.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.states.state_3.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: value=STALL_MEM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core.states.state_3
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: fsm.core.states.state_3

### RTL-0108: Implement FSM state core.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.states.state_4.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: value=FAULT_HALT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core.states.state_4
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: fsm.core.states.state_4

### RTL-0109: Implement FSM transition core.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_0.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=RESET; to=RUN; condition=rst deasserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_0
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_0 condition is implemented as RTL control logic: rst deasserted
  - fsm.core.transitions.transition_0 transition path RESET -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_0

### RTL-0110: Implement FSM transition core.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_1.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=RUN; to=STALL_IF; condition=i_hready==0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_1
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_1 condition is implemented as RTL control logic: i_hready==0
  - fsm.core.transitions.transition_1 transition path RUN -> STALL_IF is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_1

### RTL-0111: Implement FSM transition core.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_2.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=STALL_IF; to=RUN; condition=i_hready==1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_2
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_2 condition is implemented as RTL control logic: i_hready==1
  - fsm.core.transitions.transition_2 transition path STALL_IF -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_2

### RTL-0112: Implement FSM transition core.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_3.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=RUN; to=STALL_MEM; condition=active load/store && d_hready==0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_3
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_3 condition is implemented as RTL control logic: active load/store && d_hready==0
  - fsm.core.transitions.transition_3 transition path RUN -> STALL_MEM is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_3

### RTL-0113: Implement FSM transition core.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_4.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=STALL_MEM; to=RUN; condition=d_hready==1 && d_hresp==OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_4
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_4 condition is implemented as RTL control logic: d_hready==1 && d_hresp==OKAY
  - fsm.core.transitions.transition_4 transition path STALL_MEM -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_4

### RTL-0114: Implement FSM transition core.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_5.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=RUN; to=FAULT_HALT; condition=i_hresp==ERROR || d_hresp==ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_5
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_5 condition is implemented as RTL control logic: i_hresp==ERROR || d_hresp==ERROR
  - fsm.core.transitions.transition_5 transition path RUN -> FAULT_HALT is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_5

### RTL-0115: Implement FSM transition core.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_6.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=STALL_MEM; to=FAULT_HALT; condition=d_hresp==ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_6
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_6 condition is implemented as RTL control logic: d_hresp==ERROR
  - fsm.core.transitions.transition_6 transition path STALL_MEM -> FAULT_HALT is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_6

### RTL-0116: Implement FSM transition core.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core.transitions.transition_7.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via fsm.core.
SSOT item context: from=FAULT_HALT; to=RESET; condition=rst asserted.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core.transitions.transition_7
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
  - fsm.core.transitions.transition_7 condition is implemented as RTL control logic: rst asserted
  - fsm.core.transitions.transition_7 transition path FAULT_HALT -> RESET is encoded or explicitly proven equivalent
- SSOT refs: fsm.core.transitions.transition_7

### RTL-0143: Prove module arm_m0_min_id is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.arm_m0_min_id.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arm_m0_min_id.module_equivalence.
Owner: arm_m0_min_id in rtl/arm_m0_min_id.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arm_m0_min_id.module_equivalence
  - Primary implementation evidence is in rtl/arm_m0_min_id.sv
- SSOT refs: sub_modules.arm_m0_min_id.module_equivalence
