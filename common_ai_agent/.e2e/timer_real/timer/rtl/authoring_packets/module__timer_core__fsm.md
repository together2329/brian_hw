# RTL Authoring Packet: module__timer_core__fsm

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer_core.sv
- Task count: 8
- Required tasks: 8

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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, dataflow.count_path, dataflow.irq_path, decomposition, features, fsm, function_model, function_model.state_variables, function_model.state_variables.count_q, function_model.state_variables.enable_q, function_model.state_variables.load_q, function_model.transactions.FM_DISABLED_HOLD
- Module slice: 3/8 section=fsm task_limit=48
- Slice rule: Owner module timer_core is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_core.pclk <= pclk (integration.connections[13])
  - timer_core.presetn <= presetn (integration.connections[14])
  - timer_core.load_q <= load_q (integration.connections[15])
  - timer_core.enable_q <= enable_q (integration.connections[16])
  - timer_core.count_q <= count_q (integration.connections[17])
  - timer_core.irq <= irq (integration.connections[18])

## Tasks

### RTL-0168: Implement FSM state timer_control.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.timer_control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.states.state_0.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: value=DISABLED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.timer_control.states.state_0
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: fsm.timer_control.states.state_0

### RTL-0169: Implement FSM state timer_control.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.timer_control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.states.state_1.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: value=ENABLED_COUNT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.timer_control.states.state_1
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: fsm.timer_control.states.state_1

### RTL-0170: Implement FSM state timer_control.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.timer_control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.states.state_2.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: value=RELOAD_IRQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.timer_control.states.state_2
  - Primary implementation evidence is in rtl/timer_core.sv
- SSOT refs: fsm.timer_control.states.state_2

### RTL-0171: Implement FSM transition timer_control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.timer_control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.transitions.transition_0.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: from=DISABLED; to=ENABLED_COUNT; condition=enable_q == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.timer_control.transitions.transition_0
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.timer_control.transitions.transition_0 condition is implemented as RTL control logic: enable_q == 1
  - fsm.timer_control.transitions.transition_0 transition path DISABLED -> ENABLED_COUNT is encoded or explicitly proven equivalent
- SSOT refs: fsm.timer_control.transitions.transition_0

### RTL-0172: Implement FSM transition timer_control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.timer_control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.transitions.transition_1.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: from=ENABLED_COUNT; to=RELOAD_IRQ; condition=enable_q == 1 and count_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.timer_control.transitions.transition_1
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.timer_control.transitions.transition_1 condition is implemented as RTL control logic: enable_q == 1 and count_q == 0
  - fsm.timer_control.transitions.transition_1 transition path ENABLED_COUNT -> RELOAD_IRQ is encoded or explicitly proven equivalent
- SSOT refs: fsm.timer_control.transitions.transition_1

### RTL-0173: Implement FSM transition timer_control.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.timer_control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.transitions.transition_2.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: from=RELOAD_IRQ; to=ENABLED_COUNT; condition=enable_q == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.timer_control.transitions.transition_2
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.timer_control.transitions.transition_2 condition is implemented as RTL control logic: enable_q == 1
  - fsm.timer_control.transitions.transition_2 transition path RELOAD_IRQ -> ENABLED_COUNT is encoded or explicitly proven equivalent
- SSOT refs: fsm.timer_control.transitions.transition_2

### RTL-0174: Implement FSM transition timer_control.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.timer_control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.transitions.transition_3.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: from=ENABLED_COUNT; to=DISABLED; condition=enable_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.timer_control.transitions.transition_3
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.timer_control.transitions.transition_3 condition is implemented as RTL control logic: enable_q == 0
  - fsm.timer_control.transitions.transition_3 transition path ENABLED_COUNT -> DISABLED is encoded or explicitly proven equivalent
- SSOT refs: fsm.timer_control.transitions.transition_3

### RTL-0175: Implement FSM transition timer_control.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.timer_control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.timer_control.transitions.transition_4.
Owner: timer_core in rtl/timer_core.sv via fsm.
SSOT item context: from=RELOAD_IRQ; to=DISABLED; condition=enable_q == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.timer_control.transitions.transition_4
  - Primary implementation evidence is in rtl/timer_core.sv
  - fsm.timer_control.transitions.transition_4 condition is implemented as RTL control logic: enable_q == 0
  - fsm.timer_control.transitions.transition_4 transition path RELOAD_IRQ -> DISABLED is encoded or explicitly proven equivalent
- SSOT refs: fsm.timer_control.transitions.transition_4
