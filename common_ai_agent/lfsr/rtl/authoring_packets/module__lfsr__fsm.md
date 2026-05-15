# RTL Authoring Packet: module__lfsr__fsm

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 7/13 section=fsm task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0097: Implement FSM state lfsr_control.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.lfsr_control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.states.state_0.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: value=IDLE.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.lfsr_control.states.state_0
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: fsm.lfsr_control.states.state_0

### RTL-0098: Implement FSM state lfsr_control.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.lfsr_control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.states.state_1.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: value=RUNNING.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.lfsr_control.states.state_1
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: fsm.lfsr_control.states.state_1

### RTL-0099: Implement FSM state lfsr_control.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.lfsr_control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.states.state_2.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: value=LOCKUP.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.lfsr_control.states.state_2
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: fsm.lfsr_control.states.state_2

### RTL-0100: Implement FSM transition lfsr_control.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.lfsr_control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.transitions.transition_0.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: from=IDLE; to=RUNNING; condition=CTRL.enable == 1 && lfsr_state != 0.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.lfsr_control.transitions.transition_0
  - Primary implementation evidence is in rtl/lfsr.sv
  - fsm.lfsr_control.transitions.transition_0 condition is implemented as RTL control logic: CTRL.enable == 1 && lfsr_state != 0
  - fsm.lfsr_control.transitions.transition_0 transition path IDLE -> RUNNING is encoded or explicitly proven equivalent
- SSOT refs: fsm.lfsr_control.transitions.transition_0

### RTL-0101: Implement FSM transition lfsr_control.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.lfsr_control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.transitions.transition_1.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: from=RUNNING; to=IDLE; condition=CTRL.enable == 0.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.lfsr_control.transitions.transition_1
  - Primary implementation evidence is in rtl/lfsr.sv
  - fsm.lfsr_control.transitions.transition_1 condition is implemented as RTL control logic: CTRL.enable == 0
  - fsm.lfsr_control.transitions.transition_1 transition path RUNNING -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.lfsr_control.transitions.transition_1

### RTL-0102: Implement FSM transition lfsr_control.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.lfsr_control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.transitions.transition_2.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: from=RUNNING; to=LOCKUP; condition=lfsr_state == 0.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.lfsr_control.transitions.transition_2
  - Primary implementation evidence is in rtl/lfsr.sv
  - fsm.lfsr_control.transitions.transition_2 condition is implemented as RTL control logic: lfsr_state == 0
  - fsm.lfsr_control.transitions.transition_2 transition path RUNNING -> LOCKUP is encoded or explicitly proven equivalent
- SSOT refs: fsm.lfsr_control.transitions.transition_2

### RTL-0103: Implement FSM transition lfsr_control.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.lfsr_control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.transitions.transition_3.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: from=LOCKUP; to=IDLE; condition=CTRL.enable == 0.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.lfsr_control.transitions.transition_3
  - Primary implementation evidence is in rtl/lfsr.sv
  - fsm.lfsr_control.transitions.transition_3 condition is implemented as RTL control logic: CTRL.enable == 0
  - fsm.lfsr_control.transitions.transition_3 transition path LOCKUP -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.lfsr_control.transitions.transition_3

### RTL-0104: Implement FSM transition lfsr_control.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.lfsr_control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.lfsr_control.transitions.transition_4.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: from=LOCKUP; to=RUNNING; condition=CTRL.enable == 1 && CTRL.auto_reload == 1.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.lfsr_control.transitions.transition_4
  - Primary implementation evidence is in rtl/lfsr.sv
  - fsm.lfsr_control.transitions.transition_4 condition is implemented as RTL control logic: CTRL.enable == 1 && CTRL.auto_reload == 1
  - fsm.lfsr_control.transitions.transition_4 transition path LOCKUP -> RUNNING is encoded or explicitly proven equivalent
- SSOT refs: fsm.lfsr_control.transitions.transition_4
