# RTL Authoring Packet: module__atcdmac100_core__fsm

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 19
- Required tasks: 19

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, decomposition, decomposition.owners, decomposition.source_refs, error_handling, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM_AHB_READ, function_model.transactions.FM_AHB_WRITE, function_model.transactions.FM_ARBITRATE, function_model.transactions.FM_COMPLETE, function_model.transactions.FM_ERROR_ABORT, function_model.transactions.FM_HANDSHAKE_ACK
- Module slice: 8/17 section=fsm task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0319: Implement FSM state fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_0

### RTL-0320: Implement FSM state fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=ARBITRATE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_1

### RTL-0321: Implement FSM state fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=READ_ADDR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_2

### RTL-0322: Implement FSM state fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=READ_DATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_3

### RTL-0323: Implement FSM state fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_4.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=WRITE_ADDR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_4
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_4

### RTL-0324: Implement FSM state fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_5.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=WRITE_DATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_5
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_5

### RTL-0325: Implement FSM state fsm.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_6.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=COMPLETE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_6
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_6

### RTL-0326: Implement FSM state fsm.state_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_7.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=ERROR_ABORT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_7
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_7

### RTL-0327: Implement FSM state fsm.state_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.fsm.states.state_8
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.states.state_8.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: value=CHAIN_LOAD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.fsm.states.state_8
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: fsm.fsm.states.state_8

### RTL-0328: Implement FSM transition fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=IDLE; to=ARBITRATE; condition=ch_enable != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_0 condition is implemented as RTL control logic: ch_enable != 0
  - fsm.fsm.transitions.transition_0 transition path IDLE -> ARBITRATE is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_0

### RTL-0329: Implement FSM transition fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=ARBITRATE; to=READ_ADDR; condition=selected channel ready and handshake satisfied.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_1 condition is implemented as RTL control logic: selected channel ready and handshake satisfied
  - fsm.fsm.transitions.transition_1 transition path ARBITRATE -> READ_ADDR is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_1

### RTL-0330: Implement FSM transition fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=READ_ADDR; to=READ_DATA; condition=hgrant_mst && hready_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_2 condition is implemented as RTL control logic: hgrant_mst && hready_mst
  - fsm.fsm.transitions.transition_2 transition path READ_ADDR -> READ_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_2

### RTL-0331: Implement FSM transition fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_3.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=READ_DATA; to=WRITE_ADDR; condition=read_data captured.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_3 condition is implemented as RTL control logic: read_data captured
  - fsm.fsm.transitions.transition_3 transition path READ_DATA -> WRITE_ADDR is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_3

### RTL-0332: Implement FSM transition fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_4.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=WRITE_ADDR; to=WRITE_DATA; condition=hgrant_mst && hready_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_4 condition is implemented as RTL control logic: hgrant_mst && hready_mst
  - fsm.fsm.transitions.transition_4 transition path WRITE_ADDR -> WRITE_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_4

### RTL-0333: Implement FSM transition fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_5.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=WRITE_DATA; to=COMPLETE; condition=last beat done.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_5 condition is implemented as RTL control logic: last beat done
  - fsm.fsm.transitions.transition_5 transition path WRITE_DATA -> COMPLETE is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_5

### RTL-0334: Implement FSM transition fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_6.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=WRITE_DATA; to=READ_ADDR; condition=more beats remain.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_6 condition is implemented as RTL control logic: more beats remain
  - fsm.fsm.transitions.transition_6 transition path WRITE_DATA -> READ_ADDR is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_6

### RTL-0335: Implement FSM transition fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_7.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=READ_ADDR; to=ERROR_ABORT; condition=hresp_mst error or alignment error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_7 condition is implemented as RTL control logic: hresp_mst error or alignment error
  - fsm.fsm.transitions.transition_7 transition path READ_ADDR -> ERROR_ABORT is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_7

### RTL-0336: Implement FSM transition fsm.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_8.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=COMPLETE; to=CHAIN_LOAD; condition=CHAIN_TRANSFER_SUPPORT && ChnLLPointer != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_8 condition is implemented as RTL control logic: CHAIN_TRANSFER_SUPPORT && ChnLLPointer != 0
  - fsm.fsm.transitions.transition_8 transition path COMPLETE -> CHAIN_LOAD is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_8

### RTL-0337: Implement FSM transition fsm.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_9.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via fsm.
SSOT item context: from=COMPLETE; to=IDLE; condition=no chain continuation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_9
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - fsm.fsm.transitions.transition_9 condition is implemented as RTL control logic: no chain continuation
  - fsm.fsm.transitions.transition_9 transition path COMPLETE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_9
