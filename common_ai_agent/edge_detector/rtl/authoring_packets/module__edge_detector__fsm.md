# RTL Authoring Packet: module__edge_detector__fsm

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 7/16 section=fsm task_limit=48
- Slice rule: Owner module edge_detector is split into 16 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4
- SSOT connection contracts:
  - edge_detector.PCLK <= PCLK (integration.connections[0])
  - edge_detector.PRESETn <= PRESETn (integration.connections[1])
  - edge_detector.signal_i <= signal_i (integration.connections[2])
  - edge_detector.edge_o <= edge_o (integration.connections[3])
  - edge_detector.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0094: Implement FSM transition fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_0.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: from=SYNC_SAMPLE; to=EDGE_DECODE; condition=every PCLK rising edge; action=advance sync_chain, latch prev_sample.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/edge_detector.sv
  - fsm.fsm.transitions.transition_0 condition is implemented as RTL control logic: every PCLK rising edge
  - fsm.fsm.transitions.transition_0 transition path SYNC_SAMPLE -> EDGE_DECODE is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_0

### RTL-0095: Implement FSM transition fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.fsm.transitions.transition_1.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: from=EDGE_DECODE; to=OUTPUT_PULSE; condition=edge_decode matches EDGE_MODE and enable==1; action=assert edge_o, set sticky/status.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/edge_detector.sv
  - fsm.fsm.transitions.transition_1 condition is implemented as RTL control logic: edge_decode matches EDGE_MODE and enable==1
  - fsm.fsm.transitions.transition_1 transition path EDGE_DECODE -> OUTPUT_PULSE is encoded or explicitly proven equivalent
- SSOT refs: fsm.fsm.transitions.transition_1
