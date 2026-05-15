# RTL Authoring Packet: unowned_tasks

- Kind: unowned
- Owner module: <none>
- Owner file: <none>
- Task count: 6
- Required tasks: 6

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])
  - adder_kogge_stone_regs.clk_i <= PCLK (integration.connections[2])
  - adder_kogge_stone_regs.rst_ni <= PRESETn (integration.connections[3])

## Tasks

### RTL-0114: Implement FSM state adder_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.adder_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.states.state_0.
SSOT item context: value=IDLE.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.adder_fsm.states.state_0
- SSOT refs: fsm.adder_fsm.states.state_0

### RTL-0115: Implement FSM state adder_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.adder_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.states.state_1.
SSOT item context: value=COMPUTE.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.adder_fsm.states.state_1
- SSOT refs: fsm.adder_fsm.states.state_1

### RTL-0116: Implement FSM state adder_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.adder_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.states.state_2.
SSOT item context: value=DONE.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.adder_fsm.states.state_2
- SSOT refs: fsm.adder_fsm.states.state_2

### RTL-0117: Implement FSM transition adder_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.adder_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.transitions.transition_0.
SSOT item context: from=IDLE; to=COMPUTE; condition=CONTROL.start=1 or (hold_mode=0 and shadow_valid=1).
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.adder_fsm.transitions.transition_0
  - fsm.adder_fsm.transitions.transition_0 condition is implemented as RTL control logic: CONTROL.start=1 or (hold_mode=0 and shadow_valid=1)
  - fsm.adder_fsm.transitions.transition_0 transition path IDLE -> COMPUTE is encoded or explicitly proven equivalent
- SSOT refs: fsm.adder_fsm.transitions.transition_0

### RTL-0118: Implement FSM transition adder_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.adder_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.transitions.transition_1.
SSOT item context: from=COMPUTE; to=DONE; condition=posedge PCLK (combinational tree result captured).
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.adder_fsm.transitions.transition_1
  - fsm.adder_fsm.transitions.transition_1 condition is implemented as RTL control logic: posedge PCLK (combinational tree result captured)
  - fsm.adder_fsm.transitions.transition_1 transition path COMPUTE -> DONE is encoded or explicitly proven equivalent
- SSOT refs: fsm.adder_fsm.transitions.transition_1

### RTL-0119: Implement FSM transition adder_fsm.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.adder_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.adder_fsm.transitions.transition_2.
SSOT item context: from=DONE; to=IDLE; condition=automatic after one cycle or next start.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.adder_fsm.transitions.transition_2
  - fsm.adder_fsm.transitions.transition_2 condition is implemented as RTL control logic: automatic after one cycle or next start
  - fsm.adder_fsm.transitions.transition_2 transition path DONE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.adder_fsm.transitions.transition_2
