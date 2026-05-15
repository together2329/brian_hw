# RTL Authoring Packet: module__fifo_sync_ptrs__fsm

- Kind: module
- Owner module: fifo_sync_ptrs
- Owner file: rtl/fifo_sync_ptrs.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, decomposition.units.pointer_control, fsm.ptr_fsm, function_model, function_model.state_variables, function_model.state_variables.count, function_model.state_variables.rd_ptr, function_model.state_variables.wr_ptr
- Module slice: 4/6 section=fsm task_limit=48
- Slice rule: Owner module fifo_sync_ptrs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0192: Implement FSM state ptr_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=EMPTY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_0

### RTL-0193: Implement FSM state ptr_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=ALMOST_EMPTY.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_1

### RTL-0194: Implement FSM state ptr_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=NORMAL.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_2

### RTL-0195: Implement FSM state ptr_fsm.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=ALMOST_FULL.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_3

### RTL-0196: Implement FSM state ptr_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: value=FULL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
- SSOT refs: fsm.ptr_fsm.states.state_4

### RTL-0197: Implement FSM transition ptr_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_0.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=EMPTY; to=NORMAL; condition=push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_0 condition is implemented as RTL control logic: push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_0 transition path EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_0

### RTL-0198: Implement FSM transition ptr_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_1.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=EMPTY; to=ALMOST_EMPTY; condition=push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_1 condition is implemented as RTL control logic: push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0
  - fsm.ptr_fsm.transitions.transition_1 transition path EMPTY -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_1

### RTL-0199: Implement FSM transition ptr_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_2.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_EMPTY; to=EMPTY; condition=pop_accepted && count becomes 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_2 condition is implemented as RTL control logic: pop_accepted && count becomes 0
  - fsm.ptr_fsm.transitions.transition_2 transition path ALMOST_EMPTY -> EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_2

### RTL-0200: Implement FSM transition ptr_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_3.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_EMPTY; to=NORMAL; condition=push_accepted && count > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_3 condition is implemented as RTL control logic: push_accepted && count > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_3 transition path ALMOST_EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_3

### RTL-0201: Implement FSM transition ptr_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_4.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=NORMAL; to=ALMOST_FULL; condition=push_accepted && count >= ALMOST_FULL_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_4 condition is implemented as RTL control logic: push_accepted && count >= ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_4 transition path NORMAL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_4

### RTL-0202: Implement FSM transition ptr_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_5.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=NORMAL; to=ALMOST_EMPTY; condition=pop_accepted && count <= ALMOST_EMPTY_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_5 condition is implemented as RTL control logic: pop_accepted && count <= ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_5 transition path NORMAL -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_5

### RTL-0203: Implement FSM transition ptr_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_6.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_FULL; to=FULL; condition=push_accepted && count == DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_6 condition is implemented as RTL control logic: push_accepted && count == DEPTH
  - fsm.ptr_fsm.transitions.transition_6 transition path ALMOST_FULL -> FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_6

### RTL-0204: Implement FSM transition ptr_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_7.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=ALMOST_FULL; to=NORMAL; condition=pop_accepted && count < ALMOST_FULL_THRESHOLD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_7 condition is implemented as RTL control logic: pop_accepted && count < ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_7 transition path ALMOST_FULL -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_7

### RTL-0205: Implement FSM transition ptr_fsm.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_8.
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via fsm.ptr_fsm.
SSOT item context: from=FULL; to=ALMOST_FULL; condition=pop_accepted && count == DEPTH-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - fsm.ptr_fsm.transitions.transition_8 condition is implemented as RTL control logic: pop_accepted && count == DEPTH-1
  - fsm.ptr_fsm.transitions.transition_8 transition path FULL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_8
