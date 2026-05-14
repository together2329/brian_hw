# RTL Authoring Packet: module__uart_lite_tx_fsm

- Kind: module
- Owner module: uart_lite_tx_fsm
- Owner file: rtl/uart_lite_tx_fsm.sv
- Task count: 38
- Required tasks: 38

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
- LLM-actionable open tasks: 17
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.tx_stages, fsm, fsm.tx_fsm

## Tasks

### RTL-0030: Implement TX FSM with shift register and parity generator

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: State machine per fsm.tx_fsm: IDLE/START/DATA/PARITY/STOP/BREAK. Pops byte from TX FIFO at START. Shifts LSB-first on baud ticks. Computes parity inline. Supports DATA_WIDTH (5-8), parity_en, parity_odd, stop_bits (1-2). Break state holds txd_o low for 13+ bit times.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TX_FSM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All declared FSM states and transitions implemented
  - Frame format matches dataflow.tx_path.framing
  - Parity computed as XOR of data bits + parity_odd toggle
  - break_send self-clears after break duration
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - Semantic source_refs covered: cycle_model.pipeline.tx_stages, features.tx_byte_transmission, fsm.tx_fsm
- SSOT refs: cycle_model.pipeline.tx_stages, features.tx_byte_transmission, fsm.tx_fsm, workflow_todos.rtl-gen[3]

### RTL-0199: Implement FSM state tx_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_0.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_0
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_0

### RTL-0200: Implement FSM state tx_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_1.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_START.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_1
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_1

### RTL-0201: Implement FSM state tx_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_2.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_DATA.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_2
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_2

### RTL-0202: Implement FSM state tx_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_3.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_PARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_3
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_3

### RTL-0203: Implement FSM state tx_fsm.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_4.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_STOP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_4
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_4

### RTL-0204: Implement FSM state tx_fsm.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.tx_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.states.state_5.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=TX_BREAK.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.tx_fsm.states.state_5
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.tx_fsm.states.state_5

### RTL-0205: Implement FSM transition tx_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_0.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_IDLE; to=TX_START; condition=TX FIFO not empty AND baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_0 condition is implemented as RTL control logic: TX FIFO not empty AND baud tick
  - fsm.tx_fsm.transitions.transition_0 transition path TX_IDLE -> TX_START is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_0

### RTL-0206: Implement FSM transition tx_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_1.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_START; to=TX_DATA; condition=baud tick (1 bit period elapsed).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_1 condition is implemented as RTL control logic: baud tick (1 bit period elapsed)
  - fsm.tx_fsm.transitions.transition_1 transition path TX_START -> TX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_1

### RTL-0207: Implement FSM transition tx_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_2.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_DATA; to=TX_DATA; condition=baud tick AND bit_count < DATA_WIDTH-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_2 condition is implemented as RTL control logic: baud tick AND bit_count < DATA_WIDTH-1
  - fsm.tx_fsm.transitions.transition_2 transition path TX_DATA -> TX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_2

### RTL-0208: Implement FSM transition tx_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_3.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_DATA; to=TX_PARITY; condition=baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_3 condition is implemented as RTL control logic: baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=1
  - fsm.tx_fsm.transitions.transition_3 transition path TX_DATA -> TX_PARITY is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_3

### RTL-0209: Implement FSM transition tx_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_4.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_DATA; to=TX_STOP; condition=baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_4 condition is implemented as RTL control logic: baud tick AND bit_count == DATA_WIDTH-1 AND parity_en=0
  - fsm.tx_fsm.transitions.transition_4 transition path TX_DATA -> TX_STOP is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_4

### RTL-0210: Implement FSM transition tx_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_5.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_PARITY; to=TX_STOP; condition=baud tick.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_5 condition is implemented as RTL control logic: baud tick
  - fsm.tx_fsm.transitions.transition_5 transition path TX_PARITY -> TX_STOP is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_5

### RTL-0211: Implement FSM transition tx_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_6.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_STOP; to=TX_IDLE; condition=baud tick AND stop_bit_count == stop_bits-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_6 condition is implemented as RTL control logic: baud tick AND stop_bit_count == stop_bits-1
  - fsm.tx_fsm.transitions.transition_6 transition path TX_STOP -> TX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_6

### RTL-0212: Implement FSM transition tx_fsm.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_7.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_STOP; to=TX_STOP; condition=baud tick AND stop_bit_count < stop_bits-1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_7 condition is implemented as RTL control logic: baud tick AND stop_bit_count < stop_bits-1
  - fsm.tx_fsm.transitions.transition_7 transition path TX_STOP -> TX_STOP is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_7

### RTL-0213: Implement FSM transition tx_fsm.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_8.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_IDLE; to=TX_BREAK; condition=CONTROL.break_send=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_8 condition is implemented as RTL control logic: CONTROL.break_send=1
  - fsm.tx_fsm.transitions.transition_8 transition path TX_IDLE -> TX_BREAK is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_8

### RTL-0214: Implement FSM transition tx_fsm.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_9.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=TX_BREAK; to=TX_IDLE; condition=break_counter expired (13+ bit times).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_9
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_9 condition is implemented as RTL control logic: break_counter expired (13+ bit times)
  - fsm.tx_fsm.transitions.transition_9 transition path TX_BREAK -> TX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_9

### RTL-0215: Implement FSM transition tx_fsm.transition_10

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.tx_fsm.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.tx_fsm.transitions.transition_10.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=*; to=TX_IDLE; condition=PRESETn asserted (async reset).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.tx_fsm.transitions.transition_10
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.tx_fsm.transitions.transition_10 condition is implemented as RTL control logic: PRESETn asserted (async reset)
  - fsm.tx_fsm.transitions.transition_10 transition path * -> TX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.tx_fsm.transitions.transition_10

### RTL-0216: Implement FSM state rx_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_0.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_IDLE.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_0
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_0

### RTL-0217: Implement FSM state rx_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_1.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_START_DETECT.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_1
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_1

### RTL-0218: Implement FSM state rx_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_2.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_START_CONFIRM.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_2
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_2

### RTL-0219: Implement FSM state rx_fsm.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_3.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_DATA.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_3
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_3

### RTL-0220: Implement FSM state rx_fsm.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_4.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_PARITY.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_4
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_4

### RTL-0221: Implement FSM state rx_fsm.state_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_5.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_STOP.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_5
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_5

### RTL-0222: Implement FSM state rx_fsm.state_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.rx_fsm.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.states.state_6.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: value=RX_DONE.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.rx_fsm.states.state_6
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: fsm.rx_fsm.states.state_6

### RTL-0223: Implement FSM transition rx_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_0.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_IDLE; to=RX_START_DETECT; condition=falling edge on synchronized rxd (rxd_sync[1]=0, rxd_sync[0]=1 on prev cycle).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_0 condition is implemented as RTL control logic: falling edge on synchronized rxd (rxd_sync[1]=0, rxd_sync[0]=1 on prev cycle)
  - fsm.rx_fsm.transitions.transition_0 transition path RX_IDLE -> RX_START_DETECT is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_0

### RTL-0224: Implement FSM transition rx_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_1.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_START_DETECT; to=RX_START_CONFIRM; condition=oversample_counter == 7 (mid-bit start confirm at 7/16).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_1 condition is implemented as RTL control logic: oversample_counter == 7 (mid-bit start confirm at 7/16)
  - fsm.rx_fsm.transitions.transition_1 transition path RX_START_DETECT -> RX_START_CONFIRM is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_1

### RTL-0225: Implement FSM transition rx_fsm.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_2.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_START_CONFIRM; to=RX_DATA; condition=rxd_sync sampled low (start confirmed) AND oversample_counter == 15 → reset to 0.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_2 condition is implemented as RTL control logic: rxd_sync sampled low (start confirmed) AND oversample_counter == 15 → reset to 0
  - fsm.rx_fsm.transitions.transition_2 transition path RX_START_CONFIRM -> RX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_2

### RTL-0226: Implement FSM transition rx_fsm.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_3.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_START_CONFIRM; to=RX_IDLE; condition=rxd_sync sampled high (false start) → return to idle.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_3 condition is implemented as RTL control logic: rxd_sync sampled high (false start) → return to idle
  - fsm.rx_fsm.transitions.transition_3 transition path RX_START_CONFIRM -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_3

### RTL-0227: Implement FSM transition rx_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_4.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_DATA; to=RX_DATA; condition=oversample_counter == 15 AND bit_count < DATA_WIDTH-1 → reset oversample to 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_4 condition is implemented as RTL control logic: oversample_counter == 15 AND bit_count < DATA_WIDTH-1 → reset oversample to 0
  - fsm.rx_fsm.transitions.transition_4 transition path RX_DATA -> RX_DATA is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_4

### RTL-0228: Implement FSM transition rx_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_5.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_DATA; to=RX_PARITY; condition=oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_5 condition is implemented as RTL control logic: oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=1
  - fsm.rx_fsm.transitions.transition_5 transition path RX_DATA -> RX_PARITY is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_5

### RTL-0229: Implement FSM transition rx_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_6.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_DATA; to=RX_STOP; condition=oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_6 condition is implemented as RTL control logic: oversample_counter == 15 AND bit_count == DATA_WIDTH-1 AND parity_en=0
  - fsm.rx_fsm.transitions.transition_6 transition path RX_DATA -> RX_STOP is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_6

### RTL-0230: Implement FSM transition rx_fsm.transition_7

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_7.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_PARITY; to=RX_STOP; condition=oversample_counter == 15 (parity bit center-sampled at count 7/16 of current period).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_7
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_7 condition is implemented as RTL control logic: oversample_counter == 15 (parity bit center-sampled at count 7/16 of current period)
  - fsm.rx_fsm.transitions.transition_7 transition path RX_PARITY -> RX_STOP is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_7

### RTL-0231: Implement FSM transition rx_fsm.transition_8

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_8.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_STOP; to=RX_DONE; condition=oversample_counter == 15 AND rxd_sync sampled high (valid stop).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_8
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_8 condition is implemented as RTL control logic: oversample_counter == 15 AND rxd_sync sampled high (valid stop)
  - fsm.rx_fsm.transitions.transition_8 transition path RX_STOP -> RX_DONE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_8

### RTL-0232: Implement FSM transition rx_fsm.transition_9

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_9.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_STOP; to=RX_IDLE; condition=oversample_counter == 15 AND rxd_sync sampled low (frame error).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_9
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_9 condition is implemented as RTL control logic: oversample_counter == 15 AND rxd_sync sampled low (frame error)
  - fsm.rx_fsm.transitions.transition_9 transition path RX_STOP -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_9

### RTL-0233: Implement FSM transition rx_fsm.transition_10

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_10.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=RX_DONE; to=RX_IDLE; condition=byte pushed into RX FIFO or discarded if overrun.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_10
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_10 condition is implemented as RTL control logic: byte pushed into RX FIFO or discarded if overrun
  - fsm.rx_fsm.transitions.transition_10 transition path RX_DONE -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_10

### RTL-0234: Implement FSM transition rx_fsm.transition_11

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.rx_fsm.transitions.transition_11
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.rx_fsm.transitions.transition_11.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via fsm.
SSOT item context: from=*; to=RX_IDLE; condition=PRESETn asserted (async reset).
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.rx_fsm.transitions.transition_11
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
  - fsm.rx_fsm.transitions.transition_11 condition is implemented as RTL control logic: PRESETn asserted (async reset)
  - fsm.rx_fsm.transitions.transition_11 transition path * -> RX_IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.rx_fsm.transitions.transition_11

### RTL-0260: Prove module uart_lite_tx_fsm is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_tx_fsm.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_tx_fsm.module_equivalence.
Owner: uart_lite_tx_fsm in rtl/uart_lite_tx_fsm.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_tx_fsm.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_tx_fsm.sv
- SSOT refs: sub_modules.uart_lite_tx_fsm.module_equivalence
