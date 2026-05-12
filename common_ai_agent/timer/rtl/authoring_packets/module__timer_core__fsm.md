# RTL Authoring Packet: module__timer_core__fsm

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
- Task count: 8
- Required tasks: 8

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 7/17 section=fsm task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0071: Implement FSM state control.IDLE

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.IDLE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.IDLE.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: name=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.IDLE
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: fsm.control.states.IDLE

### RTL-0072: Implement FSM state control.RUN

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.RUN
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.RUN.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: name=RUN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.RUN
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: fsm.control.states.RUN

### RTL-0073: Implement FSM state control.DONE_PULSE

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.DONE_PULSE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.DONE_PULSE.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: name=DONE_PULSE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.DONE_PULSE
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: fsm.control.states.DONE_PULSE

### RTL-0074: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: from=IDLE; to=RUN; condition=start and load_value != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/timer.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: start and load_value != 0
  - fsm.control.transitions.transition_0 transition path IDLE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0075: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: from=RUN; to=RUN; condition=enable and count > 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/timer.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: enable and count > 1
  - fsm.control.transitions.transition_1 transition path RUN -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0076: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: from=RUN; to=DONE_PULSE; condition=enable and count == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/timer.sv
  - fsm.control.transitions.transition_2 condition is implemented as RTL control logic: enable and count == 1
  - fsm.control.transitions.transition_2 transition path RUN -> DONE_PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0077: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: from=DONE_PULSE; to=IDLE; condition=next control cycle without start.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/timer.sv
  - fsm.control.transitions.transition_3 condition is implemented as RTL control logic: next control cycle without start
  - fsm.control.transitions.transition_3 transition path DONE_PULSE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0078: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: timer_core in rtl/timer.sv via fsm.
SSOT item context: from=RUN; to=IDLE; condition=clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/timer.sv
  - fsm.control.transitions.transition_4 condition is implemented as RTL control logic: clear
  - fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4
