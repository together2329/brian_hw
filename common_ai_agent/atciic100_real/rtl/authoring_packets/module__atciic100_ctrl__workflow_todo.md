# RTL Authoring Packet: module__atciic100_ctrl__workflow_todo

- Kind: module
- Owner module: atciic100_ctrl
- Owner file: rtl/atciic100_ctrl.v
- Task count: 1
- Required tasks: 1

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, fsm, fsm.iic_phase, function_model, function_model.transactions
- Module slice: 7/7 section=workflow_todo task_limit=48
- Slice rule: Owner module atciic100_ctrl is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])

## Tasks

### RTL-0029: Implement I2C Protocol FSM

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: State machine for Master/Slave modes, Start/Stop/Addr/Data phases.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FSM.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - FSM state coverage
  - All transitions exercised
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
  - Semantic source_refs covered: fsm, function_model
- SSOT refs: fsm, function_model, workflow_todos.rtl-gen[2]
