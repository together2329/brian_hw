# RTL Authoring Packet: module__simple_pwm__fsm

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 4
- Required tasks: 4

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
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 7/14 section=fsm task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0066: Implement FSM state pwm_fsm.state_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.pwm_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pwm_fsm.states.state_0.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: value=IDLE.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.pwm_fsm.states.state_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: fsm.pwm_fsm.states.state_0

### RTL-0067: Implement FSM state pwm_fsm.state_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.state
- Source ref: fsm.pwm_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pwm_fsm.states.state_1.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: value=RUNNING.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.pwm_fsm.states.state_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: fsm.pwm_fsm.states.state_1

### RTL-0068: Implement FSM transition pwm_fsm.transition_0

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pwm_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pwm_fsm.transitions.transition_0.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: from=IDLE; to=RUNNING; condition=enable == 1.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pwm_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - fsm.pwm_fsm.transitions.transition_0 condition is implemented as RTL control logic: enable == 1
  - fsm.pwm_fsm.transitions.transition_0 transition path IDLE -> RUNNING is encoded or explicitly proven equivalent
- SSOT refs: fsm.pwm_fsm.transitions.transition_0

### RTL-0069: Implement FSM transition pwm_fsm.transition_1

- Priority: high
- Required: True
- Status: open
- Category: fsm.transition
- Source ref: fsm.pwm_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.pwm_fsm.transitions.transition_1.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: from=RUNNING; to=IDLE; condition=enable == 0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.pwm_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - fsm.pwm_fsm.transitions.transition_1 condition is implemented as RTL control logic: enable == 0
  - fsm.pwm_fsm.transitions.transition_1 transition path RUNNING -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.pwm_fsm.transitions.transition_1
