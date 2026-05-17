# RTL Authoring Packet: module__pl330realverify_channel_fsm__fsm

- Kind: module
- Owner module: pl330realverify_channel_fsm
- Owner file: rtl/pl330realverify_channel_fsm.sv
- Task count: 33
- Required tasks: 33

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
- LLM-actionable open tasks: 33
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.backpressure, cycle_model.ordering, cycle_model.pipeline, decomposition.units.channel_control, fsm, fsm.channel_fsm, function_model, function_model.transactions.FM_FAULT, function_model.transactions.FM_TRANSFER, function_model.transactions.FM_WFP
- Module slice: 3/5 section=fsm task_limit=48
- Slice rule: Owner module pl330realverify_channel_fsm is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_channel_fsm.clk_i <= dmaclk (sub_modules[1].connections[0])
  - pl330realverify_channel_fsm.rst_ni <= dmacresetn (sub_modules[1].connections[1])
  - pl330realverify_channel_fsm.start_cmd_i <= start_cmd (sub_modules[1].connections[2])
  - pl330realverify_channel_fsm.halt_cmd_i <= halt_cmd (sub_modules[1].connections[3])
  - pl330realverify_channel_fsm.selected_event_i <= selected_event (sub_modules[1].connections[4])
  - pl330realverify_channel_fsm.state_o <= channel_state (sub_modules[1].connections[5])
  - pl330realverify_channel_fsm.state_o <= channel_state (integration.connections[11])

## Tasks

### RTL-0292: Implement FSM state channel_fsm.state_0

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=STOPPED.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_0

### RTL-0293: Implement FSM state channel_fsm.state_1

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=EXECUTING.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_1

### RTL-0294: Implement FSM state channel_fsm.state_2

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=WAITING_FOR_PERIPHERAL.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_2

### RTL-0295: Implement FSM state channel_fsm.state_3

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_3.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=ISSUE_READ.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_3
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_3

### RTL-0296: Implement FSM state channel_fsm.state_4

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_4.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=WAIT_READ.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_4
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_4

### RTL-0297: Implement FSM state channel_fsm.state_5

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_5.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=ISSUE_WRITE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_5
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_5

### RTL-0298: Implement FSM state channel_fsm.state_6

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_6.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=WAIT_WRITE_RESP.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_6
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_6

### RTL-0299: Implement FSM state channel_fsm.state_7

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_7.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=COMPLETING.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_7
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_7

### RTL-0300: Implement FSM state channel_fsm.state_8

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_8
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_8.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=FAULT_COMPLETING.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_8
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_8

### RTL-0301: Implement FSM state channel_fsm.state_9

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_9
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_9.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=COMPLETED.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_9
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_9

### RTL-0302: Implement FSM state channel_fsm.state_10

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.channel_fsm.states.state_10
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.states.state_10.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: value=FAULTED.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_fsm.states.state_10
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.channel_fsm.states.state_10

### RTL-0303: Implement FSM transition channel_fsm.transition_0

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=STOPPED; to=EXECUTING; condition=start_cmd == 1 and fault_inject == 0 and addresses_aligned == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_0 condition is implemented as RTL control logic: start_cmd == 1 and fault_inject == 0 and addresses_aligned == 1
  - fsm.channel_fsm.transitions.transition_0 transition path STOPPED -> EXECUTING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_0

### RTL-0304: Implement FSM transition channel_fsm.transition_1

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=STOPPED; to=FAULT_COMPLETING; condition=start_cmd == 1 and (fault_inject == 1 or addresses_aligned == 0).
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_1 condition is implemented as RTL control logic: start_cmd == 1 and (fault_inject == 1 or addresses_aligned == 0)
  - fsm.channel_fsm.transitions.transition_1 transition path STOPPED -> FAULT_COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_1

### RTL-0305: Implement FSM transition channel_fsm.transition_2

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=EXECUTING; to=WAITING_FOR_PERIPHERAL; condition=wfp_enable == 1 and selected_event == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_2 condition is implemented as RTL control logic: wfp_enable == 1 and selected_event == 0
  - fsm.channel_fsm.transitions.transition_2 transition path EXECUTING -> WAITING_FOR_PERIPHERAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_2

### RTL-0306: Implement FSM transition channel_fsm.transition_3

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_3.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAITING_FOR_PERIPHERAL; to=ISSUE_READ; condition=selected_event == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_3 condition is implemented as RTL control logic: selected_event == 1
  - fsm.channel_fsm.transitions.transition_3 transition path WAITING_FOR_PERIPHERAL -> ISSUE_READ is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_3

### RTL-0307: Implement FSM transition channel_fsm.transition_4

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_4.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=EXECUTING; to=ISSUE_READ; condition=wfp_enable == 0 or selected_event == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_4 condition is implemented as RTL control logic: wfp_enable == 0 or selected_event == 1
  - fsm.channel_fsm.transitions.transition_4 transition path EXECUTING -> ISSUE_READ is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_4

### RTL-0308: Implement FSM transition channel_fsm.transition_5

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_5.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=ISSUE_READ; to=WAIT_READ; condition=arvalid == 1 and arready == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_5 condition is implemented as RTL control logic: arvalid == 1 and arready == 1
  - fsm.channel_fsm.transitions.transition_5 transition path ISSUE_READ -> WAIT_READ is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_5

### RTL-0309: Implement FSM transition channel_fsm.transition_6

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_6.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAIT_READ; to=ISSUE_WRITE; condition=rvalid == 1 and rready == 1 and rresp == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_6 condition is implemented as RTL control logic: rvalid == 1 and rready == 1 and rresp == 0
  - fsm.channel_fsm.transitions.transition_6 transition path WAIT_READ -> ISSUE_WRITE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_6

### RTL-0310: Implement FSM transition channel_fsm.transition_7

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_7.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAIT_READ; to=FAULT_COMPLETING; condition=rvalid == 1 and rready == 1 and rresp != 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_7 condition is implemented as RTL control logic: rvalid == 1 and rready == 1 and rresp != 0
  - fsm.channel_fsm.transitions.transition_7 transition path WAIT_READ -> FAULT_COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_7

### RTL-0311: Implement FSM transition channel_fsm.transition_8

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_8.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=ISSUE_WRITE; to=WAIT_WRITE_RESP; condition=aw_handshake == 1 and w_handshake == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_8 condition is implemented as RTL control logic: aw_handshake == 1 and w_handshake == 1
  - fsm.channel_fsm.transitions.transition_8 transition path ISSUE_WRITE -> WAIT_WRITE_RESP is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_8

### RTL-0312: Implement FSM transition channel_fsm.transition_9

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_9.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAIT_WRITE_RESP; to=COMPLETING; condition=bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_9
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_9 condition is implemented as RTL control logic: bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining == 1
  - fsm.channel_fsm.transitions.transition_9 transition path WAIT_WRITE_RESP -> COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_9

### RTL-0313: Implement FSM transition channel_fsm.transition_10

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_10.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAIT_WRITE_RESP; to=ISSUE_READ; condition=bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining > 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_10
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_10 condition is implemented as RTL control logic: bvalid == 1 and bready == 1 and bresp == 0 and loop_remaining > 1
  - fsm.channel_fsm.transitions.transition_10 transition path WAIT_WRITE_RESP -> ISSUE_READ is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_10

### RTL-0314: Implement FSM transition channel_fsm.transition_11

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_11
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_11.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=WAIT_WRITE_RESP; to=FAULT_COMPLETING; condition=bvalid == 1 and bready == 1 and bresp != 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_11
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_11 condition is implemented as RTL control logic: bvalid == 1 and bready == 1 and bresp != 0
  - fsm.channel_fsm.transitions.transition_11 transition path WAIT_WRITE_RESP -> FAULT_COMPLETING is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_11

### RTL-0315: Implement FSM transition channel_fsm.transition_12

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_12
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_12.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=COMPLETING; to=COMPLETED; condition=complete_status_posted == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_12
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_12 condition is implemented as RTL control logic: complete_status_posted == 1
  - fsm.channel_fsm.transitions.transition_12 transition path COMPLETING -> COMPLETED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_12

### RTL-0316: Implement FSM transition channel_fsm.transition_13

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_13
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_13.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=FAULT_COMPLETING; to=FAULTED; condition=fault_status_posted == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_13
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_13 condition is implemented as RTL control logic: fault_status_posted == 1
  - fsm.channel_fsm.transitions.transition_13 transition path FAULT_COMPLETING -> FAULTED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_13

### RTL-0317: Implement FSM transition channel_fsm.transition_14

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_14
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_14.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=COMPLETED; to=STOPPED; condition=start_cmd == 0 and halt_cmd == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_14
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_14 condition is implemented as RTL control logic: start_cmd == 0 and halt_cmd == 0
  - fsm.channel_fsm.transitions.transition_14 transition path COMPLETED -> STOPPED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_14

### RTL-0318: Implement FSM transition channel_fsm.transition_15

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.channel_fsm.transitions.transition_15
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_fsm.transitions.transition_15.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.channel_fsm.
SSOT item context: from=FAULTED; to=STOPPED; condition=fault_clear == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_fsm.transitions.transition_15
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.channel_fsm.transitions.transition_15 condition is implemented as RTL control logic: fault_clear == 1
  - fsm.channel_fsm.transitions.transition_15 transition path FAULTED -> STOPPED is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_fsm.transitions.transition_15

### RTL-0319: Implement FSM state register_fsm.state_0

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.register_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.states.state_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: value=APB_IDLE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.register_fsm.states.state_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.register_fsm.states.state_0

### RTL-0320: Implement FSM state register_fsm.state_1

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.register_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.states.state_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: value=APB_SETUP.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.register_fsm.states.state_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.register_fsm.states.state_1

### RTL-0321: Implement FSM state register_fsm.state_2

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.register_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.states.state_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: value=APB_ACCESS.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.register_fsm.states.state_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
- SSOT refs: fsm.register_fsm.states.state_2

### RTL-0322: Implement FSM transition register_fsm.transition_0

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.register_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.transitions.transition_0.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: from=APB_IDLE; to=APB_SETUP; condition=psel == 1 and penable == 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.register_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.register_fsm.transitions.transition_0 condition is implemented as RTL control logic: psel == 1 and penable == 0
  - fsm.register_fsm.transitions.transition_0 transition path APB_IDLE -> APB_SETUP is encoded or explicitly proven equivalent
- SSOT refs: fsm.register_fsm.transitions.transition_0

### RTL-0323: Implement FSM transition register_fsm.transition_1

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.register_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.transitions.transition_1.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: from=APB_SETUP; to=APB_ACCESS; condition=psel == 1 and penable == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.register_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.register_fsm.transitions.transition_1 condition is implemented as RTL control logic: psel == 1 and penable == 1
  - fsm.register_fsm.transitions.transition_1 transition path APB_SETUP -> APB_ACCESS is encoded or explicitly proven equivalent
- SSOT refs: fsm.register_fsm.transitions.transition_1

### RTL-0324: Implement FSM transition register_fsm.transition_2

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.register_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.register_fsm.transitions.transition_2.
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via fsm.
SSOT item context: from=APB_ACCESS; to=APB_IDLE; condition=pready == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.register_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - fsm.register_fsm.transitions.transition_2 condition is implemented as RTL control logic: pready == 1
  - fsm.register_fsm.transitions.transition_2 transition path APB_ACCESS -> APB_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.register_fsm.transitions.transition_2
