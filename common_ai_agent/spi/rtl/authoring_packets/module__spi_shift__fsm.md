# RTL Authoring Packet: module__spi_shift__fsm

- Kind: module
- Owner module: spi_shift
- Owner file: rtl/spi_shift.sv
- Task count: 18
- Required tasks: 18

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
- LLM-actionable open tasks: 18
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, features, fsm, fsm.channel_level, function_model, function_model.transactions
- Module slice: 4/7 section=fsm task_limit=48
- Slice rule: Owner module spi_shift is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25
- SSOT connection contracts:
  - spi_shift.start_req <= start_req (integration.connections[0])
  - spi_shift.ctrl_cfg <= ctrl_cfg (integration.connections[1])
  - spi_shift.tx_word <= tx_word (integration.connections[2])

## Tasks

### RTL-0203: Implement FSM state channel_level.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_0.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=IDLE.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_0
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_0

### RTL-0204: Implement FSM state channel_level.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_1.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=CHECK_LAUNCH.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_1
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_1

### RTL-0205: Implement FSM state channel_level.state_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_2.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=ASSERT_CS.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_2
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_2

### RTL-0206: Implement FSM state channel_level.state_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_3.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=SHIFT_EDGE.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_3
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_3

### RTL-0207: Implement FSM state channel_level.state_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_4.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=SAMPLE_EDGE.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_4
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_4

### RTL-0208: Implement FSM state channel_level.state_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_5.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=COMPLETE.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_5
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_5

### RTL-0209: Implement FSM state channel_level.state_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.channel_level.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.states.state_6.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: value=ERROR_SUPPRESS.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.channel_level.states.state_6
  - Primary implementation evidence is in rtl/spi_shift.sv
- SSOT refs: fsm.channel_level.states.state_6

### RTL-0210: Implement FSM transition channel_level.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_0.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=IDLE; to=CHECK_LAUNCH; condition=start_pulse.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_0
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_0 condition is implemented as RTL control logic: start_pulse
  - fsm.channel_level.transitions.transition_0 transition path IDLE -> CHECK_LAUNCH is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_0

### RTL-0211: Implement FSM transition channel_level.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_1.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=CHECK_LAUNCH; to=ASSERT_CS; condition=launch_gate_true.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_1
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_1 condition is implemented as RTL control logic: launch_gate_true
  - fsm.channel_level.transitions.transition_1 transition path CHECK_LAUNCH -> ASSERT_CS is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_1

### RTL-0212: Implement FSM transition channel_level.transition_2

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_2.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=CHECK_LAUNCH; to=ERROR_SUPPRESS; condition=illegal_cs_or_width.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_2
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_2 condition is implemented as RTL control logic: illegal_cs_or_width
  - fsm.channel_level.transitions.transition_2 transition path CHECK_LAUNCH -> ERROR_SUPPRESS is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_2

### RTL-0213: Implement FSM transition channel_level.transition_3

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_3.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=CHECK_LAUNCH; to=IDLE; condition=launch_gate_false_without_fault.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_3
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_3 condition is implemented as RTL control logic: launch_gate_false_without_fault
  - fsm.channel_level.transitions.transition_3 transition path CHECK_LAUNCH -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_3

### RTL-0214: Implement FSM transition channel_level.transition_4

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_4.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=ASSERT_CS; to=SHIFT_EDGE; condition=prescale_tick.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_4
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_4 condition is implemented as RTL control logic: prescale_tick
  - fsm.channel_level.transitions.transition_4 transition path ASSERT_CS -> SHIFT_EDGE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_4

### RTL-0215: Implement FSM transition channel_level.transition_5

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_5.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=SHIFT_EDGE; to=SAMPLE_EDGE; condition=mode_edge_progress.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_5
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_5 condition is implemented as RTL control logic: mode_edge_progress
  - fsm.channel_level.transitions.transition_5 transition path SHIFT_EDGE -> SAMPLE_EDGE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_5

### RTL-0216: Implement FSM transition channel_level.transition_6

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_6.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=SAMPLE_EDGE; to=SHIFT_EDGE; condition=bit_index_not_last.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_6
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_6 condition is implemented as RTL control logic: bit_index_not_last
  - fsm.channel_level.transitions.transition_6 transition path SAMPLE_EDGE -> SHIFT_EDGE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_6

### RTL-0217: Implement FSM transition channel_level.transition_7

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_7.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=SAMPLE_EDGE; to=COMPLETE; condition=bit_index_last.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_7
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_7 condition is implemented as RTL control logic: bit_index_last
  - fsm.channel_level.transitions.transition_7 transition path SAMPLE_EDGE -> COMPLETE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_7

### RTL-0218: Implement FSM transition channel_level.transition_8

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_8.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=COMPLETE; to=ASSERT_CS; condition=continuous_cs_and_next_launch_ready.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_8
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_8 condition is implemented as RTL control logic: continuous_cs_and_next_launch_ready
  - fsm.channel_level.transitions.transition_8 transition path COMPLETE -> ASSERT_CS is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_8

### RTL-0219: Implement FSM transition channel_level.transition_9

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_9.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=COMPLETE; to=IDLE; condition=otherwise.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_9
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_9 condition is implemented as RTL control logic: otherwise
  - fsm.channel_level.transitions.transition_9 transition path COMPLETE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_9

### RTL-0220: Implement FSM transition channel_level.transition_10

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.channel_level.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.channel_level.transitions.transition_10.
Owner: spi_shift in rtl/spi_shift.sv via fsm.channel_level.
SSOT item context: from=ERROR_SUPPRESS; to=IDLE; condition=one_cycle_report_done.
- Current reason: Owner RTL file is missing: rtl/spi_shift.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.channel_level.transitions.transition_10
  - Primary implementation evidence is in rtl/spi_shift.sv
  - fsm.channel_level.transitions.transition_10 condition is implemented as RTL control logic: one_cycle_report_done
  - fsm.channel_level.transitions.transition_10 transition path ERROR_SUPPRESS -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.channel_level.transitions.transition_10
