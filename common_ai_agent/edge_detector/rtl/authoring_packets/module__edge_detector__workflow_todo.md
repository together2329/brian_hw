# RTL Authoring Packet: module__edge_detector__workflow_todo

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 16/16 section=workflow_todo task_limit=48
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

### RTL-0027: Implement edge detector core logic

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model state variables (sync_chain, prev_sync, status), cycle_model pipeline, and ownership refs into RTL state/datapath/control logic.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: edge_detector in rtl/edge_detector.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner logic is present in edge_detector.sv
  - FunctionalModel expected result and RTL observed result can be compared for DETECT transaction
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Semantic source_refs covered: cycle_model.pipeline, function_model.transactions, rtl_contract.state_updates
- SSOT refs: cycle_model.pipeline, function_model.transactions, rtl_contract.state_updates, workflow_todos.rtl-gen[0]
