# RTL Authoring Packet: module__priority_enc_fsm

- Kind: module
- Owner module: priority_enc_fsm
- Owner file: rtl/priority_enc_fsm.sv
- Task count: 5
- Required tasks: 5

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
- Owner refs: fsm, fsm.encoder_fsm, fsm.encoder_fsm.states, fsm.encoder_fsm.transitions
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=4
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 27 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - priority_enc_fsm.PCLK <= PCLK (observed_named_port_map)
  - priority_enc_fsm.PRESETn <= PRESETn (observed_named_port_map)
  - priority_enc_fsm.active_o <= fsm_active (observed_named_port_map)
  - priority_enc_fsm.ctrl_enable_i <= ctrl_enable (observed_named_port_map)

## Tasks

### RTL-0084: Implement FSM state encoder_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.encoder_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.encoder_fsm.states.state_0.
Owner: priority_enc_fsm in rtl/priority_enc_fsm.sv via fsm.encoder_fsm.states.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.encoder_fsm.states.state_0
  - Primary implementation evidence is in rtl/priority_enc_fsm.sv
- SSOT refs: fsm.encoder_fsm.states.state_0

### RTL-0085: Implement FSM state encoder_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.encoder_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.encoder_fsm.states.state_1.
Owner: priority_enc_fsm in rtl/priority_enc_fsm.sv via fsm.encoder_fsm.states.
SSOT item context: value=ACTIVE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.encoder_fsm.states.state_1
  - Primary implementation evidence is in rtl/priority_enc_fsm.sv
- SSOT refs: fsm.encoder_fsm.states.state_1

### RTL-0086: Implement FSM transition encoder_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.encoder_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.encoder_fsm.transitions.transition_0.
Owner: priority_enc_fsm in rtl/priority_enc_fsm.sv via fsm.encoder_fsm.transitions.
SSOT item context: from=IDLE; to=ACTIVE; condition=CTRL.enable == 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.encoder_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/priority_enc_fsm.sv
  - fsm.encoder_fsm.transitions.transition_0 condition is implemented as RTL control logic: CTRL.enable == 1
  - fsm.encoder_fsm.transitions.transition_0 transition path IDLE -> ACTIVE is encoded or explicitly proven equivalent
- SSOT refs: fsm.encoder_fsm.transitions.transition_0

### RTL-0087: Implement FSM transition encoder_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.encoder_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.encoder_fsm.transitions.transition_1.
Owner: priority_enc_fsm in rtl/priority_enc_fsm.sv via fsm.encoder_fsm.transitions.
SSOT item context: from=ACTIVE; to=IDLE; condition=CTRL.enable == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.encoder_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/priority_enc_fsm.sv
  - fsm.encoder_fsm.transitions.transition_1 condition is implemented as RTL control logic: CTRL.enable == 0
  - fsm.encoder_fsm.transitions.transition_1 transition path ACTIVE -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.encoder_fsm.transitions.transition_1

### RTL-0102: Prove module priority_enc_fsm is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.priority_enc_fsm.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.priority_enc_fsm.module_equivalence.
Owner: priority_enc_fsm in rtl/priority_enc_fsm.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.priority_enc_fsm.module_equivalence
  - Primary implementation evidence is in rtl/priority_enc_fsm.sv
- SSOT refs: sub_modules.priority_enc_fsm.module_equivalence
