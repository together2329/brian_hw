# RTL Authoring Packet: module__dma_real_channel__fsm

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
- Task count: 20
- Required tasks: 20

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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 5/9 section=fsm task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0308: Implement FSM state per_channel.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_0

### RTL-0309: Implement FSM state per_channel.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=CFG.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_1

### RTL-0310: Implement FSM state per_channel.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=REQUEST.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_2

### RTL-0311: Implement FSM state per_channel.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=READ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_3

### RTL-0312: Implement FSM state per_channel.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=WRITE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_4

### RTL-0313: Implement FSM state per_channel.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=UPDATE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_5

### RTL-0314: Implement FSM state per_channel.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_6.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=DONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_6
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_6

### RTL-0315: Implement FSM state per_channel.state_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.per_channel.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.states.state_7.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: value=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.per_channel.states.state_7
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: fsm.per_channel.states.state_7

### RTL-0316: Implement FSM transition per_channel.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=IDLE; to=CFG; condition=ch_start && ch_en && dma_en && valid_cfg && cdc_config_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_0 condition is implemented as RTL control logic: ch_start && ch_en && dma_en && valid_cfg && cdc_config_valid
  - fsm.per_channel.transitions.transition_0 transition path IDLE -> CFG is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_0

### RTL-0317: Implement FSM transition per_channel.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=IDLE; to=ERROR; condition=ch_start && ch_en && !valid_cfg.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_1 condition is implemented as RTL control logic: ch_start && ch_en && !valid_cfg
  - fsm.per_channel.transitions.transition_1 transition path IDLE -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_1

### RTL-0318: Implement FSM transition per_channel.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=CFG; to=REQUEST; condition=next_cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_2 condition is implemented as RTL control logic: next_cycle
  - fsm.per_channel.transitions.transition_2 transition path CFG -> REQUEST is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_2

### RTL-0319: Implement FSM transition per_channel.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=REQUEST; to=READ; condition=arb_grant.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_3 condition is implemented as RTL control logic: arb_grant
  - fsm.per_channel.transitions.transition_3 transition path REQUEST -> READ is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_3

### RTL-0320: Implement FSM transition per_channel.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=READ; to=WRITE; condition=read_burst_complete && !fifo_full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_4 condition is implemented as RTL control logic: read_burst_complete && !fifo_full
  - fsm.per_channel.transitions.transition_4 transition path READ -> WRITE is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_4

### RTL-0321: Implement FSM transition per_channel.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=READ; to=ERROR; condition=ahb_error || timeout_expired || fifo_overflow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_5 condition is implemented as RTL control logic: ahb_error || timeout_expired || fifo_overflow
  - fsm.per_channel.transitions.transition_5 transition path READ -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_5

### RTL-0322: Implement FSM transition per_channel.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_6.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=WRITE; to=UPDATE; condition=write_burst_complete.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_6
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_6 condition is implemented as RTL control logic: write_burst_complete
  - fsm.per_channel.transitions.transition_6 transition path WRITE -> UPDATE is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_6

### RTL-0323: Implement FSM transition per_channel.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_7.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=WRITE; to=ERROR; condition=ahb_error || timeout_expired.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_7
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_7 condition is implemented as RTL control logic: ahb_error || timeout_expired
  - fsm.per_channel.transitions.transition_7 transition path WRITE -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_7

### RTL-0324: Implement FSM transition per_channel.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_8.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=UPDATE; to=REQUEST; condition=remaining_gt_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_8
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_8 condition is implemented as RTL control logic: remaining_gt_0
  - fsm.per_channel.transitions.transition_8 transition path UPDATE -> REQUEST is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_8

### RTL-0325: Implement FSM transition per_channel.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_9.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=UPDATE; to=DONE; condition=remaining_eq_0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_9
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_9 condition is implemented as RTL control logic: remaining_eq_0
  - fsm.per_channel.transitions.transition_9 transition path UPDATE -> DONE is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_9

### RTL-0326: Implement FSM transition per_channel.transition_10

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_10
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_10.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=DONE; to=IDLE; condition=status_sampled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_10
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_10 condition is implemented as RTL control logic: status_sampled
  - fsm.per_channel.transitions.transition_10 transition path DONE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_10

### RTL-0327: Implement FSM transition per_channel.transition_11

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.per_channel.transitions.transition_11
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.per_channel.transitions.transition_11.
Owner: dma_real_channel in rtl/dma_real_channel.sv via fsm.per_channel.
SSOT item context: from=ERROR; to=IDLE; condition=status_sampled.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.per_channel.transitions.transition_11
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - fsm.per_channel.transitions.transition_11 condition is implemented as RTL control logic: status_sampled
  - fsm.per_channel.transitions.transition_11 transition path ERROR -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.per_channel.transitions.transition_11
