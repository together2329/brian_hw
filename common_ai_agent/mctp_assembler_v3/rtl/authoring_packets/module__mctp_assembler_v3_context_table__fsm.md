# RTL Authoring Packet: module__mctp_assembler_v3_context_table__fsm

- Kind: module
- Owner module: mctp_assembler_v3_context_table
- Owner file: rtl/mctp_assembler_v3_context_table.sv
- Task count: 14
- Required tasks: 14

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: fsm, fsm.context_fsm, function_model, function_model.transactions.FM_ALLOC_CONTEXT, function_model.transactions.FM_APPEND
- Module slice: 3/6 section=fsm task_limit=48
- Slice rule: Owner module mctp_assembler_v3_context_table is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])

## Tasks

### RTL-0405: Implement FSM state ingress_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.ingress_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.states.state_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.ingress_fsm.states.state_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.ingress_fsm.states.state_0

### RTL-0413: Implement FSM transition ingress_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=ACCEPT_AW; to=RESP_B; condition=illegal AWSIZE/AWBURST (PD_MALFORMED_TLP).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_2 condition is implemented as RTL control logic: illegal AWSIZE/AWBURST (PD_MALFORMED_TLP)
  - fsm.ingress_fsm.transitions.transition_2 transition path ACCEPT_AW -> RESP_B is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_2

### RTL-0416: Implement FSM transition ingress_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.ingress_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.ingress_fsm.transitions.transition_5.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.
SSOT item context: from=CHECK_LEGAL; to=RESP_B; condition=malformed (PD_MALFORMED_TLP).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.ingress_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.ingress_fsm.transitions.transition_5 condition is implemented as RTL control logic: malformed (PD_MALFORMED_TLP)
  - fsm.ingress_fsm.transitions.transition_5 transition path CHECK_LEGAL -> RESP_B is encoded or explicitly proven equivalent
- SSOT refs: fsm.ingress_fsm.transitions.transition_5

### RTL-0419: Implement FSM state context_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_0

### RTL-0420: Implement FSM state context_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: value=ASSEMBLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_1

### RTL-0421: Implement FSM state context_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: value=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_2

### RTL-0422: Implement FSM state context_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_3.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: value=DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_3

### RTL-0423: Implement FSM transition context_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=IDLE; to=ASSEMBLING; condition=accepted SOM=1,EOM=0 allocates slot.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_0 condition is implemented as RTL control logic: accepted SOM=1,EOM=0 allocates slot
  - fsm.context_fsm.transitions.transition_0 transition path IDLE -> ASSEMBLING is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_0

### RTL-0424: Implement FSM transition context_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=IDLE; to=DONE_WAIT_DESCRIPTOR_POP; condition=accepted SOM=1,EOM=1 single-packet completes.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_1 condition is implemented as RTL control logic: accepted SOM=1,EOM=1 single-packet completes
  - fsm.context_fsm.transitions.transition_1 transition path IDLE -> DONE_WAIT_DESCRIPTOR_POP is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_1

### RTL-0425: Implement FSM transition context_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=ASSEMBLING; condition=accepted SOM=0,EOM=0 append, seq ok.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_2 condition is implemented as RTL control logic: accepted SOM=0,EOM=0 append, seq ok
  - fsm.context_fsm.transitions.transition_2 transition path ASSEMBLING -> ASSEMBLING is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_2

### RTL-0426: Implement FSM transition context_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_3.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=DONE_WAIT_DESCRIPTOR_POP; condition=accepted SOM=0,EOM=1 completes; descriptor pushed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_3 condition is implemented as RTL control logic: accepted SOM=0,EOM=1 completes; descriptor pushed
  - fsm.context_fsm.transitions.transition_3 transition path ASSEMBLING -> DONE_WAIT_DESCRIPTOR_POP is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_3

### RTL-0427: Implement FSM transition context_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_4.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=ERROR; condition=AD_* assembly drop (dup SOM/seq/overflow/sram/timeout).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_4 condition is implemented as RTL control logic: AD_* assembly drop (dup SOM/seq/overflow/sram/timeout)
  - fsm.context_fsm.transitions.transition_4 transition path ASSEMBLING -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_4

### RTL-0428: Implement FSM transition context_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_5.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=DONE_WAIT_DESCRIPTOR_POP; to=IDLE; condition=descriptor copied/popped.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_5 condition is implemented as RTL control logic: descriptor copied/popped
  - fsm.context_fsm.transitions.transition_5 transition path DONE_WAIT_DESCRIPTOR_POP -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_5

### RTL-0429: Implement FSM transition context_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_6.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via fsm.context_fsm.
SSOT item context: from=ERROR; to=IDLE; condition=clear policy releases the slot.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - fsm.context_fsm.transitions.transition_6 condition is implemented as RTL control logic: clear policy releases the slot
  - fsm.context_fsm.transitions.transition_6 transition path ERROR -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_6
