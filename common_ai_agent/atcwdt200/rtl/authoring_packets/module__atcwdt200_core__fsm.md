# RTL Authoring Packet: module__atcwdt200_core__fsm

- Kind: module
- Owner module: atcwdt200_core
- Owner file: rtl/atcwdt200_core.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, dataflow.sequence.sequence_2, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sinks.sinks_1, dataflow.sinks.sinks_2, decomposition.units.watchdog_core, fsm, fsm.watchdog, function_model, function_model.transactions.restart, function_model.transactions.timeout_decode, function_model.transactions.watchdog_tick
- Module slice: 3/6 section=fsm task_limit=48
- Slice rule: Owner module atcwdt200_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_core.pclk <= pclk (integration.connections[2])
  - atcwdt200_core.presetn <= presetn (integration.connections[3])

## Tasks

### RTL-0159: Implement FSM state watchdog.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.watchdog.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.states.state_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: value=ST_INTTIME.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.watchdog.states.state_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: fsm.watchdog.states.state_0

### RTL-0160: Implement FSM state watchdog.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.watchdog.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.states.state_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: value=ST_RSTTIME.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.watchdog.states.state_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
- SSOT refs: fsm.watchdog.states.state_1

### RTL-0161: Implement FSM transition watchdog.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.watchdog.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.transitions.transition_0.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: from=ST_INTTIME; to=ST_RSTTIME; condition=inttime_end and not restart_cmd.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.watchdog.transitions.transition_0
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - fsm.watchdog.transitions.transition_0 condition is implemented as RTL control logic: inttime_end and not restart_cmd
  - fsm.watchdog.transitions.transition_0 transition path ST_INTTIME -> ST_RSTTIME is encoded or explicitly proven equivalent
- SSOT refs: fsm.watchdog.transitions.transition_0

### RTL-0162: Implement FSM transition watchdog.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.watchdog.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.transitions.transition_1.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: from=ST_RSTTIME; to=ST_INTTIME; condition=restart_cmd.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.watchdog.transitions.transition_1
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - fsm.watchdog.transitions.transition_1 condition is implemented as RTL control logic: restart_cmd
  - fsm.watchdog.transitions.transition_1 transition path ST_RSTTIME -> ST_INTTIME is encoded or explicitly proven equivalent
- SSOT refs: fsm.watchdog.transitions.transition_1

### RTL-0163: Implement FSM transition watchdog.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.watchdog.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.transitions.transition_2.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: from=ST_INTTIME; to=ST_INTTIME; condition=restart_cmd or not inttime_end.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.watchdog.transitions.transition_2
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - fsm.watchdog.transitions.transition_2 condition is implemented as RTL control logic: restart_cmd or not inttime_end
  - fsm.watchdog.transitions.transition_2 transition path ST_INTTIME -> ST_INTTIME is encoded or explicitly proven equivalent
- SSOT refs: fsm.watchdog.transitions.transition_2

### RTL-0164: Implement FSM transition watchdog.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.watchdog.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.watchdog.transitions.transition_3.
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via fsm.watchdog.
SSOT item context: from=ST_RSTTIME; to=ST_RSTTIME; condition=not restart_cmd.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.watchdog.transitions.transition_3
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - fsm.watchdog.transitions.transition_3 condition is implemented as RTL control logic: not restart_cmd
  - fsm.watchdog.transitions.transition_3 transition path ST_RSTTIME -> ST_RSTTIME is encoded or explicitly proven equivalent
- SSOT refs: fsm.watchdog.transitions.transition_3
