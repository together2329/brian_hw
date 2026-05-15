# RTL Authoring Packet: module__arbiter_rr_core__fsm

- Kind: module
- Owner module: arbiter_rr_core
- Owner file: rtl/arbiter_rr_core.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, dataflow, dataflow.sequence, dataflow.sequence.sequence_0, features, fsm, fsm.arb_fsm, function_model, function_model.transactions, function_model.transactions.FM1, function_model.transactions.FM2
- Module slice: 3/7 section=fsm task_limit=48
- Slice rule: Owner module arbiter_rr_core is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_core.clk_i <= PCLK (integration.connections[12])
  - arbiter_rr_core.rst_ni <= PRESETn (integration.connections[13])
  - arbiter_rr_core.req_i <= req_i (integration.connections[14])
  - arbiter_rr_core.mask_i <= req_mask (integration.connections[15])
  - arbiter_rr_core.enable_i <= arb_enable (integration.connections[16])
  - arbiter_rr_core.gnt_o <= gnt_o (integration.connections[17])
  - arbiter_rr_core.gnt_valid_o <= gnt_valid_o (integration.connections[18])
  - arbiter_rr_core.gnt_idx_o <= gnt_idx_o (integration.connections[19])
  - arbiter_rr_core.winner_oh_o <= status_winner (integration.connections[20])
  - arbiter_rr_core.active_req_o <= status_active_req (integration.connections[21])

## Tasks

### RTL-0110: Implement FSM state arb_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.arb_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.states.state_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.arb_fsm.states.state_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: fsm.arb_fsm.states.state_0

### RTL-0111: Implement FSM state arb_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.arb_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.states.state_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: value=EVAL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.arb_fsm.states.state_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: fsm.arb_fsm.states.state_1

### RTL-0112: Implement FSM state arb_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.arb_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.states.state_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: value=GRANT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.arb_fsm.states.state_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
- SSOT refs: fsm.arb_fsm.states.state_2

### RTL-0113: Implement FSM transition arb_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.arb_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.transitions.transition_0.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: from=IDLE; to=EVAL; condition=arb_enabled==1 && (req_i & mask) != 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.arb_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - fsm.arb_fsm.transitions.transition_0 condition is implemented as RTL control logic: arb_enabled==1 && (req_i & mask) != 0
  - fsm.arb_fsm.transitions.transition_0 transition path IDLE -> EVAL is encoded or explicitly proven equivalent
- SSOT refs: fsm.arb_fsm.transitions.transition_0

### RTL-0114: Implement FSM transition arb_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.arb_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.transitions.transition_1.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: from=EVAL; to=GRANT; condition=always (1-cycle combinational eval).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.arb_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - fsm.arb_fsm.transitions.transition_1 condition is implemented as RTL control logic: always (1-cycle combinational eval)
  - fsm.arb_fsm.transitions.transition_1 transition path EVAL -> GRANT is encoded or explicitly proven equivalent
- SSOT refs: fsm.arb_fsm.transitions.transition_1

### RTL-0115: Implement FSM transition arb_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.arb_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.transitions.transition_2.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: from=GRANT; to=IDLE; condition=next cycle: re-evaluate with updated last_winner.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.arb_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - fsm.arb_fsm.transitions.transition_2 condition is implemented as RTL control logic: next cycle: re-evaluate with updated last_winner
  - fsm.arb_fsm.transitions.transition_2 transition path GRANT -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.arb_fsm.transitions.transition_2

### RTL-0116: Implement FSM transition arb_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.arb_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.arb_fsm.transitions.transition_3.
Owner: arbiter_rr_core in rtl/arbiter_rr_core.sv via fsm.arb_fsm.
SSOT item context: from=IDLE; to=IDLE; condition=arb_enabled==0 || (req_i & mask) == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.arb_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/arbiter_rr_core.sv
  - fsm.arb_fsm.transitions.transition_3 condition is implemented as RTL control logic: arb_enabled==0 || (req_i & mask) == 0
  - fsm.arb_fsm.transitions.transition_3 transition path IDLE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.arb_fsm.transitions.transition_3
