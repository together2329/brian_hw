# RTL Authoring Packet: module__adder_kogge_stone_core__workflow_todo

- Kind: module
- Owner module: adder_kogge_stone_core
- Owner file: rtl/adder_kogge_stone_core.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, features, features.ks_addition, fsm, fsm.adder_fsm, function_model, function_model.state_updates, function_model.transactions, function_model.transactions.FM_ADD
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module adder_kogge_stone_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0027: Implement Kogge-Stone prefix tree in adder_kogge_stone_core.sv

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Generate propagate and generate signals, build log2(DATA_WIDTH) prefix tree levels using black/grey cell pattern, produce group carries, and form sum = a ^ b ^ carry. Register outputs on posedge PCLK.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_KS_TREE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is present in rtl/adder_kogge_stone_core.sv
  - FunctionalModel expected result and RTL observed result match for all DATA_WIDTH values
  - DUT-only compile/lint evidence is fresh after final edit
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.state_updates, function_model.transactions.FM_ADD
- SSOT refs: cycle_model.pipeline, function_model.state_updates, function_model.transactions.FM_ADD, workflow_todos.rtl-gen[0]
