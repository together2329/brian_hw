# RTL Authoring Packet: module__rv32i_min_if__workflow_todo

- Kind: module
- Owner module: rv32i_min_if
- Owner file: rtl/rv32i_min_if.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, function_model, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, function_model.transactions.FM_SYSTEM, io_list, io_list.interfaces.instr_bus
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module rv32i_min_if is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_if.i_addr <= i_addr (integration.connections[0])
  - rv32i_min_if.i_valid <= i_valid (integration.connections[1])
  - rv32i_min_if.i_rdata <= i_rdata (integration.connections[2])

## Tasks

### RTL-0020: Implement IF stage request and pc sequencing

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Drive i_addr and i_valid and IF register updates according to cycle_model IF stage and FM_FETCH
SSOT ref: workflow_todos.rtl-gen[0].
Owner: rv32i_min_if in rtl/rv32i_min_if.sv via workflow_todos.owner.
SSOT item context: id=RTL_IF_STAGE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - i_valid and i_addr comply with handshake_rules
  - next_pc logic matches FM_FETCH FM_BRANCH FM_JUMP
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/rv32i_min_if.sv
  - Semantic source_refs covered: cycle_model.handshake_rules, cycle_model.pipeline, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP
- SSOT refs: cycle_model.handshake_rules, cycle_model.pipeline, function_model.transactions.FM_BRANCH, function_model.transactions.FM_FETCH, function_model.transactions.FM_JUMP, workflow_todos.rtl-gen[0]
