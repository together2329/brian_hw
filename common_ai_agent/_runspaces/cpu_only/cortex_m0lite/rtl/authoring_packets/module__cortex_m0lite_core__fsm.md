# RTL Authoring Packet: module__cortex_m0lite_core__fsm

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 13
- Required tasks: 13

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 13
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 4/9 section=fsm task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0130: Implement FSM state control.RESET

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.RESET
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.RESET.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=RESET.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.RESET
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.RESET

### RTL-0131: Implement FSM state control.FETCH

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.FETCH
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.FETCH.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=FETCH.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.FETCH
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.FETCH

### RTL-0132: Implement FSM state control.DECODE

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.DECODE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.DECODE.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=DECODE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.DECODE
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.DECODE

### RTL-0133: Implement FSM state control.EXECUTE

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.EXECUTE
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.EXECUTE.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=EXECUTE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.EXECUTE
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.EXECUTE

### RTL-0134: Implement FSM state control.MEM_WAIT

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.MEM_WAIT
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.MEM_WAIT.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=MEM_WAIT.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.MEM_WAIT
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.MEM_WAIT

### RTL-0135: Implement FSM state control.TRAP

- Priority: high
- Required: True
- Status: planned
- Category: fsm.state
- Source ref: fsm.control.states.TRAP
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.TRAP.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: name=TRAP.
- Current reason: RTL audit has not run yet.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.TRAP
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.states.TRAP

### RTL-0136: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=RESET -> FETCH when rst_n=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0137: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=FETCH -> DECODE when i_hready=1 and instr_valid=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0138: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=DECODE -> EXECUTE when no stall.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0139: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=EXECUTE -> MEM_WAIT for load/store with d_hready=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0140: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=MEM_WAIT -> FETCH when d_hready=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_4

### RTL-0141: Implement FSM transition control.transition_5

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_5.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=EXECUTE -> TRAP on trap condition.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_5
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_5

### RTL-0142: Implement FSM transition control.transition_6

- Priority: high
- Required: True
- Status: planned
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_6.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via fsm.
SSOT item context: value=TRAP -> FETCH after trap PC setup.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_6
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: fsm.control.transitions.transition_6
