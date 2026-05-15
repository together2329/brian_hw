# RTL Authoring Packet: unowned_tasks

- Kind: unowned
- Owner module: <none>
- Owner file: <none>
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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 14
- Human-locked open tasks: 0
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])

## Tasks

### RTL-0192: Implement FSM state ptr_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_0.
SSOT item context: value=EMPTY.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_0
- SSOT refs: fsm.ptr_fsm.states.state_0

### RTL-0193: Implement FSM state ptr_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_1.
SSOT item context: value=ALMOST_EMPTY.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_1
- SSOT refs: fsm.ptr_fsm.states.state_1

### RTL-0194: Implement FSM state ptr_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_2.
SSOT item context: value=NORMAL.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_2
- SSOT refs: fsm.ptr_fsm.states.state_2

### RTL-0195: Implement FSM state ptr_fsm.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_3.
SSOT item context: value=ALMOST_FULL.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_3
- SSOT refs: fsm.ptr_fsm.states.state_3

### RTL-0196: Implement FSM state ptr_fsm.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.ptr_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.states.state_4.
SSOT item context: value=FULL.
- Current reason: Task has no RTL owner file.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ptr_fsm.states.state_4
- SSOT refs: fsm.ptr_fsm.states.state_4

### RTL-0197: Implement FSM transition ptr_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_0.
SSOT item context: from=EMPTY; to=NORMAL; condition=push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_0
  - fsm.ptr_fsm.transitions.transition_0 condition is implemented as RTL control logic: push_accepted && count becomes > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_0 transition path EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_0

### RTL-0198: Implement FSM transition ptr_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_1.
SSOT item context: from=EMPTY; to=ALMOST_EMPTY; condition=push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_1
  - fsm.ptr_fsm.transitions.transition_1 condition is implemented as RTL control logic: push_accepted && count becomes <= ALMOST_EMPTY_THRESHOLD && count > 0
  - fsm.ptr_fsm.transitions.transition_1 transition path EMPTY -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_1

### RTL-0199: Implement FSM transition ptr_fsm.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_2.
SSOT item context: from=ALMOST_EMPTY; to=EMPTY; condition=pop_accepted && count becomes 0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_2
  - fsm.ptr_fsm.transitions.transition_2 condition is implemented as RTL control logic: pop_accepted && count becomes 0
  - fsm.ptr_fsm.transitions.transition_2 transition path ALMOST_EMPTY -> EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_2

### RTL-0200: Implement FSM transition ptr_fsm.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_3.
SSOT item context: from=ALMOST_EMPTY; to=NORMAL; condition=push_accepted && count > ALMOST_EMPTY_THRESHOLD.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_3
  - fsm.ptr_fsm.transitions.transition_3 condition is implemented as RTL control logic: push_accepted && count > ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_3 transition path ALMOST_EMPTY -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_3

### RTL-0201: Implement FSM transition ptr_fsm.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_4.
SSOT item context: from=NORMAL; to=ALMOST_FULL; condition=push_accepted && count >= ALMOST_FULL_THRESHOLD.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_4
  - fsm.ptr_fsm.transitions.transition_4 condition is implemented as RTL control logic: push_accepted && count >= ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_4 transition path NORMAL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_4

### RTL-0202: Implement FSM transition ptr_fsm.transition_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_5.
SSOT item context: from=NORMAL; to=ALMOST_EMPTY; condition=pop_accepted && count <= ALMOST_EMPTY_THRESHOLD.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_5
  - fsm.ptr_fsm.transitions.transition_5 condition is implemented as RTL control logic: pop_accepted && count <= ALMOST_EMPTY_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_5 transition path NORMAL -> ALMOST_EMPTY is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_5

### RTL-0203: Implement FSM transition ptr_fsm.transition_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_6.
SSOT item context: from=ALMOST_FULL; to=FULL; condition=push_accepted && count == DEPTH.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_6
  - fsm.ptr_fsm.transitions.transition_6 condition is implemented as RTL control logic: push_accepted && count == DEPTH
  - fsm.ptr_fsm.transitions.transition_6 transition path ALMOST_FULL -> FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_6

### RTL-0204: Implement FSM transition ptr_fsm.transition_7

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_7.
SSOT item context: from=ALMOST_FULL; to=NORMAL; condition=pop_accepted && count < ALMOST_FULL_THRESHOLD.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_7
  - fsm.ptr_fsm.transitions.transition_7 condition is implemented as RTL control logic: pop_accepted && count < ALMOST_FULL_THRESHOLD
  - fsm.ptr_fsm.transitions.transition_7 transition path ALMOST_FULL -> NORMAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_7

### RTL-0205: Implement FSM transition ptr_fsm.transition_8

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.ptr_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ptr_fsm.transitions.transition_8.
SSOT item context: from=FULL; to=ALMOST_FULL; condition=pop_accepted && count == DEPTH-1.
- Current reason: Task has no RTL owner file.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ptr_fsm.transitions.transition_8
  - fsm.ptr_fsm.transitions.transition_8 condition is implemented as RTL control logic: pop_accepted && count == DEPTH-1
  - fsm.ptr_fsm.transitions.transition_8 transition path FULL -> ALMOST_FULL is encoded or explicitly proven equivalent
- SSOT refs: fsm.ptr_fsm.transitions.transition_8
