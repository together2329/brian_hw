# RTL Authoring Packet: module__todo_counter_pipe_core__fsm

- Kind: module
- Owner module: todo_counter_pipe_core
- Owner file: rtl/todo_counter_pipe_core.sv
- Task count: 5
- Required tasks: 5

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.clock, cycle_model.handshake_rules.event_i, cycle_model.pipeline.S2_COUNT_EVAL, cycle_model.reset, decomposition.units.counter_datapath, features, features.Clear_Load_Control, features.Debug_Cycle_Counter, features.Saturating_Mode, features.Terminal_Count_Interrupt, features.Up_Down_Counting, features.Wrap_Mode, fsm, fsm.core_fsm, fsm.internal_control
- Module slice: 5/9 section=fsm task_limit=48
- Slice rule: Owner module todo_counter_pipe_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])

## Tasks

### RTL-0222: Implement FSM state core_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core_fsm.states.state_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via fsm.core_fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core_fsm.states.state_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: fsm.core_fsm.states.state_0

### RTL-0223: Implement FSM state core_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.core_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core_fsm.states.state_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via fsm.core_fsm.
SSOT item context: value=COUNT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.core_fsm.states.state_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
- SSOT refs: fsm.core_fsm.states.state_1

### RTL-0224: Implement FSM transition core_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core_fsm.transitions.transition_0.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via fsm.core_fsm.
SSOT item context: from=IDLE; to=COUNT; condition=enable=1 and event_i=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - fsm.core_fsm.transitions.transition_0 condition is implemented as RTL control logic: enable=1 and event_i=1
  - fsm.core_fsm.transitions.transition_0 transition path IDLE -> COUNT is encoded or explicitly proven equivalent
- SSOT refs: fsm.core_fsm.transitions.transition_0

### RTL-0225: Implement FSM transition core_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core_fsm.transitions.transition_1.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via fsm.core_fsm.
SSOT item context: from=COUNT; to=IDLE; condition=enable=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - fsm.core_fsm.transitions.transition_1 condition is implemented as RTL control logic: enable=0
  - fsm.core_fsm.transitions.transition_1 transition path COUNT -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.core_fsm.transitions.transition_1

### RTL-0226: Implement FSM transition core_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.core_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.core_fsm.transitions.transition_2.
Owner: todo_counter_pipe_core in rtl/todo_counter_pipe_core.sv via fsm.core_fsm.
SSOT item context: from=COUNT; to=COUNT; condition=enable=1 and event_i=1 (next count).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.core_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/todo_counter_pipe_core.sv
  - fsm.core_fsm.transitions.transition_2 condition is implemented as RTL control logic: enable=1 and event_i=1 (next count)
  - fsm.core_fsm.transitions.transition_2 transition path COUNT -> COUNT is encoded or explicitly proven equivalent
- SSOT refs: fsm.core_fsm.transitions.transition_2
