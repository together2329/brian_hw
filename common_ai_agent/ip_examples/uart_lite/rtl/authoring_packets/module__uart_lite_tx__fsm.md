# RTL Authoring Packet: module__uart_lite_tx__fsm

- Kind: module
- Owner module: uart_lite_tx
- Owner file: rtl/uart_lite_tx.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, cycle_model.pipeline[TX_DATA], cycle_model.pipeline[TX_IDLE], cycle_model.pipeline[TX_PARITY], cycle_model.pipeline[TX_START], cycle_model.pipeline[TX_STOP1], cycle_model.pipeline[TX_STOP2], fsm, fsm.tx_fsm, function_model, function_model.transactions.FM_TX_BYTE
- Module slice: 3/5 section=fsm task_limit=48
- Slice rule: Owner module uart_lite_tx is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8

## Tasks

### RTL-0207: Implement FSM state tx_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_0

### RTL-0208: Implement FSM state tx_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_START.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_1

### RTL-0209: Implement FSM state tx_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_DATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_2

### RTL-0210: Implement FSM state tx_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_3.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_PARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_3
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_3

### RTL-0211: Implement FSM state tx_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_4.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_STOP1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_4
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_4

### RTL-0212: Implement FSM state tx_fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_5.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: value=TX_STOP2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_5
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
- SSOT refs: fsm.tx_fsm.states.state_5

### RTL-0213: Implement FSM transition tx_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_0.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_IDLE; to=TX_START; condition=TX FIFO not empty and baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_0 condition is implemented as RTL control logic: TX FIFO not empty and baud tick
  - fsm.tx_fsm.transitions.transition_0 transition path TX_IDLE -> TX_START is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_0

### RTL-0214: Implement FSM transition tx_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_1.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_START; to=TX_DATA; condition=baud tick (1 bit period elapsed).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_1 condition is implemented as RTL control logic: baud tick (1 bit period elapsed)
  - fsm.tx_fsm.transitions.transition_1 transition path TX_START -> TX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_1

### RTL-0215: Implement FSM transition tx_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_2.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_DATA; to=TX_PARITY; condition=DATA_WIDTH bits transmitted and parity_en=1 and baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_2 condition is implemented as RTL control logic: DATA_WIDTH bits transmitted and parity_en=1 and baud tick
  - fsm.tx_fsm.transitions.transition_2 transition path TX_DATA -> TX_PARITY is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_2

### RTL-0216: Implement FSM transition tx_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_3.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_DATA; to=TX_STOP1; condition=DATA_WIDTH bits transmitted and parity_en=0 and baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_3 condition is implemented as RTL control logic: DATA_WIDTH bits transmitted and parity_en=0 and baud tick
  - fsm.tx_fsm.transitions.transition_3 transition path TX_DATA -> TX_STOP1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_3

### RTL-0217: Implement FSM transition tx_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_4.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_PARITY; to=TX_STOP1; condition=baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_4 condition is implemented as RTL control logic: baud tick
  - fsm.tx_fsm.transitions.transition_4 transition path TX_PARITY -> TX_STOP1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_4

### RTL-0218: Implement FSM transition tx_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_5.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_STOP1; to=TX_IDLE; condition=stop_bits=0 and baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_5 condition is implemented as RTL control logic: stop_bits=0 and baud tick
  - fsm.tx_fsm.transitions.transition_5 transition path TX_STOP1 -> TX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_5

### RTL-0219: Implement FSM transition tx_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_6.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_STOP1; to=TX_STOP2; condition=stop_bits=1 and baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_6 condition is implemented as RTL control logic: stop_bits=1 and baud tick
  - fsm.tx_fsm.transitions.transition_6 transition path TX_STOP1 -> TX_STOP2 is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_6

### RTL-0220: Implement FSM transition tx_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_7.
Owner: uart_lite_tx in rtl/uart_lite_tx.sv via fsm.tx_fsm.
SSOT item context: from=TX_STOP2; to=TX_IDLE; condition=baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/uart_lite_tx.sv
  - fsm.tx_fsm.transitions.transition_7 condition is implemented as RTL control logic: baud tick
  - fsm.tx_fsm.transitions.transition_7 transition path TX_STOP2 -> TX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_7
