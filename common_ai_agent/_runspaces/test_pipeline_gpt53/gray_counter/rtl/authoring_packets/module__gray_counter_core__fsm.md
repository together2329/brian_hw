# RTL Authoring Packet: module__gray_counter_core__fsm

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
- Task count: 13
- Required tasks: 13

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
- LLM-actionable open tasks: 13
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 4/9 section=fsm task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0103: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=IDLE.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0104: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=RUN.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0105: Implement FSM state control.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=WRAP_PULSE.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_2

### RTL-0106: Implement FSM state control.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_3.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=CLEARED.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_3
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_3

### RTL-0107: Implement FSM state control.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.control.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_4.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: value=RESET.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_4
  - Primary implementation evidence is in rtl/gray_counter_core.sv
- SSOT refs: fsm.control.states.state_4

### RTL-0108: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RESET; to=IDLE; condition=rst_n deasserted and first rising edge observed.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_0 condition is implemented as RTL control logic: rst_n deasserted and first rising edge observed
  - fsm.control.transitions.transition_0 transition path RESET -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0109: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=IDLE; to=CLEARED; condition=clear sampled high.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_1 condition is implemented as RTL control logic: clear sampled high
  - fsm.control.transitions.transition_1 transition path IDLE -> CLEARED is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0110: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=IDLE; to=RUN; condition=enable sampled high and clear low.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_2 condition is implemented as RTL control logic: enable sampled high and clear low
  - fsm.control.transitions.transition_2 transition path IDLE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0111: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RUN; to=WRAP_PULSE; condition=advance event causes max->0 wrap.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_3 condition is implemented as RTL control logic: advance event causes max->0 wrap
  - fsm.control.transitions.transition_3 transition path RUN -> WRAP_PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0112: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=RUN; to=IDLE; condition=enable sampled low and clear low.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_4 condition is implemented as RTL control logic: enable sampled low and clear low
  - fsm.control.transitions.transition_4 transition path RUN -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4

### RTL-0113: Implement FSM transition control.transition_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_5.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=WRAP_PULSE; to=RUN; condition=enable remains high after one pulse cycle.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_5
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_5 condition is implemented as RTL control logic: enable remains high after one pulse cycle
  - fsm.control.transitions.transition_5 transition path WRAP_PULSE -> RUN is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_5

### RTL-0114: Implement FSM transition control.transition_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_6.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=WRAP_PULSE; to=IDLE; condition=enable low after pulse.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_6
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_6 condition is implemented as RTL control logic: enable low after pulse
  - fsm.control.transitions.transition_6 transition path WRAP_PULSE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_6

### RTL-0115: Implement FSM transition control.transition_7

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_7.
Owner: gray_counter_core in rtl/gray_counter_core.sv via fsm.control.
SSOT item context: from=CLEARED; to=IDLE; condition=clear low on next edge.
- Current reason: Owner RTL file is missing: rtl/gray_counter_core.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_7
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - fsm.control.transitions.transition_7 condition is implemented as RTL control logic: clear low on next edge
  - fsm.control.transitions.transition_7 transition path CLEARED -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_7
