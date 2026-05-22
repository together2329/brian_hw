# RTL Authoring Packet: module__pl330realverify_channel_fsm__workflow_todo

- Kind: module
- Owner module: pl330realverify_channel_fsm
- Owner file: rtl/pl330realverify_channel_fsm.sv
- Task count: 1
- Required tasks: 1

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
- Owner refs: cycle_model, cycle_model.backpressure, cycle_model.ordering, cycle_model.pipeline, decomposition.units.channel_control, fsm, fsm.channel_fsm, function_model, function_model.transactions.FM_FAULT, function_model.transactions.FM_TRANSFER, function_model.transactions.FM_WFP
- Module slice: 5/5 section=workflow_todo task_limit=48
- Slice rule: Owner module pl330realverify_channel_fsm is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_channel_fsm.clk_i <= dmaclk (sub_modules[1].connections[0])
  - pl330realverify_channel_fsm.rst_ni <= dmacresetn (sub_modules[1].connections[1])
  - pl330realverify_channel_fsm.start_cmd_i <= start_cmd (sub_modules[1].connections[2])
  - pl330realverify_channel_fsm.halt_cmd_i <= halt_cmd (sub_modules[1].connections[3])
  - pl330realverify_channel_fsm.selected_event_i <= selected_event (sub_modules[1].connections[4])
  - pl330realverify_channel_fsm.state_o <= channel_state (sub_modules[1].connections[5])
  - pl330realverify_channel_fsm.state_o <= channel_state (integration.connections[11])

## Tasks

### RTL-0029: Implement channel FSM and command sequencing

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Implement pl330realverify_channel_fsm legal states and transitions, command accept, WFP hold/release, AXI stage sequencing, completion/fault terminal states, and halt/fault-clear behavior according to fsm.channel_fsm and cycle_model.pipeline/order/backpressure.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: pl330realverify_channel_fsm in rtl/pl330realverify_channel_fsm.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CHANNEL_FSM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Reset state is STOPPED and state transitions match fsm.channel_fsm.transitions
  - No AXI traffic is issued while WAITING_FOR_PERIPHERAL and selected_event is zero
  - Completion is posted only after final successful B response
  - First fault transitions through FAULT_COMPLETING to FAULTED and suppresses same-transfer completion
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/pl330realverify_channel_fsm.sv
  - Semantic source_refs covered: cycle_model.ordering, cycle_model.pipeline, fsm.channel_fsm, function_model.transactions.FM_FAULT, function_model.transactions.FM_WFP
- SSOT refs: cycle_model.ordering, cycle_model.pipeline, fsm.channel_fsm, function_model.transactions.FM_FAULT, function_model.transactions.FM_WFP, workflow_todos.rtl-gen[2]
