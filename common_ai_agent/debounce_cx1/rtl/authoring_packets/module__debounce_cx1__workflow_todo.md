# RTL Authoring Packet: module__debounce_cx1__workflow_todo

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 1
- Required tasks: 1

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 14/17 section=workflow_todo task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0021: Implement button debouncer with stability counter

- Priority: high
- Required: True
- Status: planned
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Implement debounce_cx1.sv: stability counter, last-sample register, db_out updates after THRESH stable cycles.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: debounce_cx1 in rtl/debounce_cx1.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPLEMENT_DEBOUNCE.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL top ports match io_list.
  - fl_ctr increments when btn_in == ctr_last; resets when different.
  - db_out updates to btn_in when fl_ctr reaches THRESH-1.
  - Reset clears all state to 0.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - Semantic source_refs covered: function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list
- SSOT refs: function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, workflow_todos.rtl-gen[0]
