# RTL Authoring Packet: module__dma_scratch_orch_live_20260519b__fsm

- Kind: module
- Owner module: dma_scratch_orch_live_20260519b
- Owner file: rtl/dma_scratch_orch_live_20260519b.sv
- Task count: 17
- Required tasks: 17

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 7/15 section=fsm task_limit=48
- Slice rule: Owner module dma_scratch_orch_live_20260519b is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 21

## Tasks

### RTL-0136: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0137: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=ACCEPT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0138: Implement FSM state control.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_2.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_2
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_2

### RTL-0139: Implement FSM state control.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_3.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_3
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_3

### RTL-0140: Implement FSM state control.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_4.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_4
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_4

### RTL-0141: Implement FSM state control.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_5.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_5
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_5

### RTL-0142: Implement FSM state control.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_6.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=COMPLETE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_6
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_6

### RTL-0143: Implement FSM state control.state_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_7.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: value=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_7
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
- SSOT refs: fsm.control.states.state_7

### RTL-0144: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=IDLE; to=ACCEPT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_0 transition path IDLE -> ACCEPT is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0145: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=ACCEPT; to=EXEC_FEATURE_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_1 transition path ACCEPT -> EXEC_FEATURE_1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0146: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_1; to=EXEC_FEATURE_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_2 transition path EXEC_FEATURE_1 -> EXEC_FEATURE_2 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0147: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_2; to=EXEC_FEATURE_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_3 transition path EXEC_FEATURE_2 -> EXEC_FEATURE_3 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0148: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_3; to=EXEC_FEATURE_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_4 transition path EXEC_FEATURE_3 -> EXEC_FEATURE_4 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4

### RTL-0149: Implement FSM transition control.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_5.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_4; to=COMPLETE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_5
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_5 transition path EXEC_FEATURE_4 -> COMPLETE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_5

### RTL-0150: Implement FSM transition control.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_6.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=COMPLETE; to=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_6
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_6 transition path COMPLETE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_6

### RTL-0151: Implement FSM transition control.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_7.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=*; to=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_7
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_7 transition path * -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_7

### RTL-0152: Implement FSM transition control.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_8.
Owner: dma_scratch_orch_live_20260519b in rtl/dma_scratch_orch_live_20260519b.sv via single_owner.
SSOT item context: from=ERROR; to=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_8
  - Primary implementation evidence is in rtl/dma_scratch_orch_live_20260519b.sv
  - fsm.control.transitions.transition_8 transition path ERROR -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_8
