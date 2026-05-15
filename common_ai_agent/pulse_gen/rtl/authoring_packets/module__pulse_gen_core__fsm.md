# RTL Authoring Packet: module__pulse_gen_core__fsm

- Kind: module
- Owner module: pulse_gen_core
- Owner file: rtl/pulse_gen_core.sv
- Task count: 7
- Required tasks: 7

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, features, features.pulse_fire, fsm, fsm.pulse_fsm, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_FIRE
- Module slice: 3/6 section=fsm task_limit=48
- Slice rule: Owner module pulse_gen_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_core.status_busy_i <= pulse_gen_regs.status_busy (integration.connections[14])
  - pulse_gen_core.status_done_o <= pulse_gen_regs.status_done (integration.connections[15])

## Tasks

### RTL-0125: Implement FSM state pulse_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.pulse_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.states.state_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: value=IDLE.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.pulse_fsm.states.state_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: fsm.pulse_fsm.states.state_0

### RTL-0126: Implement FSM state pulse_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.pulse_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.states.state_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: value=PULSE.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.pulse_fsm.states.state_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: fsm.pulse_fsm.states.state_1

### RTL-0127: Implement FSM state pulse_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.pulse_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.states.state_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: value=DONE.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.pulse_fsm.states.state_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
- SSOT refs: fsm.pulse_fsm.states.state_2

### RTL-0128: Implement FSM transition pulse_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pulse_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.transitions.transition_0.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: from=IDLE; to=PULSE; condition=(CTRL.fire==1 || (trigger_i==1 && CTRL.hw_trig_en==1)) && CTRL.enable==1 && STATUS.busy==0.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pulse_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm.pulse_fsm.transitions.transition_0 condition is implemented as RTL control logic: (CTRL.fire==1 || (trigger_i==1 && CTRL.hw_trig_en==1)) && CTRL.enable==1 && STATUS.busy==0
  - fsm.pulse_fsm.transitions.transition_0 transition path IDLE -> PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.pulse_fsm.transitions.transition_0

### RTL-0129: Implement FSM transition pulse_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pulse_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.transitions.transition_1.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: from=PULSE; to=PULSE; condition=pulse_counter < latched_width - 1.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pulse_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm.pulse_fsm.transitions.transition_1 condition is implemented as RTL control logic: pulse_counter < latched_width - 1
  - fsm.pulse_fsm.transitions.transition_1 transition path PULSE -> PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.pulse_fsm.transitions.transition_1

### RTL-0130: Implement FSM transition pulse_fsm.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pulse_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.transitions.transition_2.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: from=PULSE; to=DONE; condition=pulse_counter == latched_width - 1.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pulse_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm.pulse_fsm.transitions.transition_2 condition is implemented as RTL control logic: pulse_counter == latched_width - 1
  - fsm.pulse_fsm.transitions.transition_2 transition path PULSE -> DONE is encoded or explicitly proven equivalent
- SSOT refs: fsm.pulse_fsm.transitions.transition_2

### RTL-0131: Implement FSM transition pulse_fsm.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pulse_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pulse_fsm.transitions.transition_3.
Owner: pulse_gen_core in rtl/pulse_gen_core.sv via fsm.pulse_fsm.
SSOT item context: from=DONE; to=IDLE; condition=STATUS.done cleared via W1C write or auto-clear after 1 cycle.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pulse_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/pulse_gen_core.sv
  - fsm.pulse_fsm.transitions.transition_3 condition is implemented as RTL control logic: STATUS.done cleared via W1C write or auto-clear after 1 cycle
  - fsm.pulse_fsm.transitions.transition_3 transition path DONE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.pulse_fsm.transitions.transition_3
