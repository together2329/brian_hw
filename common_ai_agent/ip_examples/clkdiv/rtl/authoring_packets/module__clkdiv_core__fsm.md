# RTL Authoring Packet: module__clkdiv_core__fsm

- Kind: module
- Owner module: clkdiv_core
- Owner file: rtl/clkdiv_core.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow, dataflow.clock_path, dataflow.control_path, fsm, fsm.divider_fsm, function_model, function_model.state_variables, function_model.transactions.FM_DIVIDE
- Module slice: 3/5 section=fsm task_limit=48
- Slice rule: Owner module clkdiv_core is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - clkdiv_core.clk_i <= clk_i (sub_modules[1].connections[0])
  - clkdiv_core.rst_ni <= rst_ni (sub_modules[1].connections[1])
  - clkdiv_core.enable_i <= enable (sub_modules[1].connections[2])
  - clkdiv_core.divisor_i <= active_divisor (sub_modules[1].connections[3])
  - clkdiv_core.clk_o <= clk_o (sub_modules[1].connections[4])
  - clkdiv_core.locked_o <= locked_o (sub_modules[1].connections[5])
  - clkdiv_core.terminal_event_o <= terminal_event (sub_modules[1].connections[6])
  - clkdiv_core.clk_i <= clk_i (integration.connections[11])
  - clkdiv_core.rst_ni <= rst_ni (integration.connections[12])
  - clkdiv_core.enable_i <= enable (integration.connections[13])
  - clkdiv_core.divisor_i <= active_divisor (integration.connections[14])
  - clkdiv_core.clk_o <= clk_o (integration.connections[15])

## Tasks

### RTL-0111: Implement FSM state divider_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.divider_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.states.state_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: value=DISABLED.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.divider_fsm.states.state_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: fsm.divider_fsm.states.state_0

### RTL-0112: Implement FSM state divider_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.divider_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.states.state_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: value=RUNNING_LOW.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.divider_fsm.states.state_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: fsm.divider_fsm.states.state_1

### RTL-0113: Implement FSM state divider_fsm.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.divider_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.states.state_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: value=RUNNING_HIGH.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.divider_fsm.states.state_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
- SSOT refs: fsm.divider_fsm.states.state_2

### RTL-0114: Implement FSM transition divider_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.divider_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.transitions.transition_0.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: from=DISABLED; to=RUNNING_LOW; condition=CTRL.enable=1.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.divider_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - fsm.divider_fsm.transitions.transition_0 condition is implemented as RTL control logic: CTRL.enable=1
  - fsm.divider_fsm.transitions.transition_0 transition path DISABLED -> RUNNING_LOW is encoded or explicitly proven equivalent
- SSOT refs: fsm.divider_fsm.transitions.transition_0

### RTL-0115: Implement FSM transition divider_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.divider_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.transitions.transition_1.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: from=RUNNING_LOW; to=RUNNING_HIGH; condition=counter reaches terminal count.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.divider_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - fsm.divider_fsm.transitions.transition_1 condition is implemented as RTL control logic: counter reaches terminal count
  - fsm.divider_fsm.transitions.transition_1 transition path RUNNING_LOW -> RUNNING_HIGH is encoded or explicitly proven equivalent
- SSOT refs: fsm.divider_fsm.transitions.transition_1

### RTL-0116: Implement FSM transition divider_fsm.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.divider_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.transitions.transition_2.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: from=RUNNING_HIGH; to=RUNNING_LOW; condition=counter reaches terminal count.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.divider_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - fsm.divider_fsm.transitions.transition_2 condition is implemented as RTL control logic: counter reaches terminal count
  - fsm.divider_fsm.transitions.transition_2 transition path RUNNING_HIGH -> RUNNING_LOW is encoded or explicitly proven equivalent
- SSOT refs: fsm.divider_fsm.transitions.transition_2

### RTL-0117: Implement FSM transition divider_fsm.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.divider_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.transitions.transition_3.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: from=RUNNING_LOW; to=DISABLED; condition=CTRL.enable=0 or reset asserted.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.divider_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - fsm.divider_fsm.transitions.transition_3 condition is implemented as RTL control logic: CTRL.enable=0 or reset asserted
  - fsm.divider_fsm.transitions.transition_3 transition path RUNNING_LOW -> DISABLED is encoded or explicitly proven equivalent
- SSOT refs: fsm.divider_fsm.transitions.transition_3

### RTL-0118: Implement FSM transition divider_fsm.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.divider_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.divider_fsm.transitions.transition_4.
Owner: clkdiv_core in rtl/clkdiv_core.sv via fsm.divider_fsm.
SSOT item context: from=RUNNING_HIGH; to=DISABLED; condition=CTRL.enable=0 or reset asserted.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.divider_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - fsm.divider_fsm.transitions.transition_4 condition is implemented as RTL control logic: CTRL.enable=0 or reset asserted
  - fsm.divider_fsm.transitions.transition_4 transition path RUNNING_HIGH -> DISABLED is encoded or explicitly proven equivalent
- SSOT refs: fsm.divider_fsm.transitions.transition_4
