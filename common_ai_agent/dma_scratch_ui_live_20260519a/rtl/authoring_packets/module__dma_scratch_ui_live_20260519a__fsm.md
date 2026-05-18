# RTL Authoring Packet: module__dma_scratch_ui_live_20260519a__fsm

- Kind: module
- Owner module: dma_scratch_ui_live_20260519a
- Owner file: rtl/dma_scratch_ui_live_20260519a.sv
- Task count: 19
- Required tasks: 19

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 7/15 section=fsm task_limit=48
- Slice rule: Owner module dma_scratch_ui_live_20260519a is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 36

## Tasks

### RTL-0166: Implement FSM state control.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_0

### RTL-0167: Implement FSM state control.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_1.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=ACCEPT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_1
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_1

### RTL-0168: Implement FSM state control.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_2.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_2
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_2

### RTL-0169: Implement FSM state control.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_3.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_3
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_3

### RTL-0170: Implement FSM state control.state_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_4
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_4.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_4
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_4

### RTL-0171: Implement FSM state control.state_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_5
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_5.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_5
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_5

### RTL-0172: Implement FSM state control.state_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_6
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_6.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=EXEC_FEATURE_5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_6
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_6

### RTL-0173: Implement FSM state control.state_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_7
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_7.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=COMPLETE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_7
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_7

### RTL-0174: Implement FSM state control.state_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.control.states.state_8
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.states.state_8.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: value=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.control.states.state_8
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: fsm.control.states.state_8

### RTL-0175: Implement FSM transition control.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=IDLE; to=ACCEPT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_0 transition path IDLE -> ACCEPT is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_0

### RTL-0176: Implement FSM transition control.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_1.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=ACCEPT; to=EXEC_FEATURE_1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_1
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_1 transition path ACCEPT -> EXEC_FEATURE_1 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_1

### RTL-0177: Implement FSM transition control.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_2.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_1; to=EXEC_FEATURE_2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_2
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_2 transition path EXEC_FEATURE_1 -> EXEC_FEATURE_2 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_2

### RTL-0178: Implement FSM transition control.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_3.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_2; to=EXEC_FEATURE_3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_3
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_3 transition path EXEC_FEATURE_2 -> EXEC_FEATURE_3 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_3

### RTL-0179: Implement FSM transition control.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_4.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_3; to=EXEC_FEATURE_4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_4
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_4 transition path EXEC_FEATURE_3 -> EXEC_FEATURE_4 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_4

### RTL-0180: Implement FSM transition control.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_5.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_4; to=EXEC_FEATURE_5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_5
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_5 transition path EXEC_FEATURE_4 -> EXEC_FEATURE_5 is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_5

### RTL-0181: Implement FSM transition control.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_6.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=EXEC_FEATURE_5; to=COMPLETE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_6
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_6 transition path EXEC_FEATURE_5 -> COMPLETE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_6

### RTL-0182: Implement FSM transition control.transition_7

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_7
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_7.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=COMPLETE; to=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_7
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_7 transition path COMPLETE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_7

### RTL-0183: Implement FSM transition control.transition_8

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_8
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_8.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=*; to=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_8
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_8 transition path * -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_8

### RTL-0184: Implement FSM transition control.transition_9

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.control.transitions.transition_9
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.control.transitions.transition_9.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via single_owner.
SSOT item context: from=ERROR; to=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.control.transitions.transition_9
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
  - fsm.control.transitions.transition_9 transition path ERROR -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.control.transitions.transition_9
