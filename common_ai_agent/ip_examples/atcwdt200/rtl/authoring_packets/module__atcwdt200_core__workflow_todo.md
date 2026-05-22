# RTL Authoring Packet: module__atcwdt200_core__workflow_todo

- Kind: module
- Owner module: atcwdt200_core
- Owner file: rtl/atcwdt200_core.sv
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
- Owner refs: cycle_model, cycle_model.ordering, cycle_model.pipeline, dataflow.sequence.sequence_2, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sinks.sinks_1, dataflow.sinks.sinks_2, decomposition.units.watchdog_core, fsm, fsm.watchdog, function_model, function_model.transactions.restart, function_model.transactions.timeout_decode, function_model.transactions.watchdog_tick
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module atcwdt200_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_core.pclk <= pclk (integration.connections[2])
  - atcwdt200_core.presetn <= presetn (integration.connections[3])

## Tasks

### RTL-0020: Implement clean-room watchdog timer RTL from approved SSOT.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate register block, counter, FSM, timeout decode, outputs, and synchronizer policy into manifest-owned RTL modules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: atcwdt200_core in rtl/atcwdt200_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_WDT_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL does not copy reference source.
  - Function/cycle/model traceability covers all listed owner refs.
  - Compile and lint reports are fresh after final RTL edit.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/atcwdt200_core.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm.watchdog, function_model.transactions, registers.register_list
- SSOT refs: cycle_model.pipeline, fsm.watchdog, function_model.transactions, registers.register_list, workflow_todos.rtl-gen[0]
