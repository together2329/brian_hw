# RTL Authoring Packet: module__gray_counter_core__workflow_todo

- Kind: module
- Owner module: gray_counter_core
- Owner file: rtl/gray_counter_core.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, error_handling, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions.GC_TXN_ADVANCE, function_model.transactions.GC_TXN_CLEAR, function_model.transactions.GC_TXN_HOLD, function_model.transactions.GC_TXN_RESET
- Module slice: 9/9 section=workflow_todo task_limit=48
- Slice rule: Owner module gray_counter_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_counter_core.clk <= clk (sub_modules[0].connections[0])
  - gray_counter_core.rst_n <= rst_n (sub_modules[0].connections[1])
  - gray_counter_core.enable <= enable (sub_modules[0].connections[2])
  - gray_counter_core.clear <= clear (sub_modules[0].connections[3])
  - gray_counter_core.gray_value <= gray_value (sub_modules[0].connections[4])
  - gray_counter_core.bin_value <= bin_value (sub_modules[0].connections[5])
  - gray_counter_core.done <= done (sub_modules[0].connections[6])

## Tasks

### RTL-0020: Implement core sequential and combinational behavior.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: RTL must implement priority reset>clear>enable>hold, gray/bin transforms, and one-cycle wrap done pulse.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: gray_counter_core in rtl/gray_counter_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE_SEMANTICS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All function_model transactions implemented with matching observable outputs
  - cycle_model latency/ordering rules hold in simulation
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/gray_counter_core.sv
  - Semantic source_refs covered: cycle_model, fsm.control, function_model.transactions
- SSOT refs: cycle_model, fsm.control, function_model.transactions, workflow_todos.rtl-gen[0]
