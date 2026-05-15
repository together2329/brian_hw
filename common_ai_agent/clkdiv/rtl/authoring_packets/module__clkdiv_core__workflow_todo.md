# RTL Authoring Packet: module__clkdiv_core__workflow_todo

- Kind: module
- Owner module: clkdiv_core
- Owner file: rtl/clkdiv_core.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow, dataflow.clock_path, dataflow.control_path, fsm, fsm.divider_fsm, function_model, function_model.state_variables, function_model.transactions.FM_DIVIDE
- Module slice: 5/5 section=workflow_todo task_limit=48
- Slice rule: Owner module clkdiv_core is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - clkdiv_core.clk_i <= clk_i (sub_modules[1].connections[0])
  - clkdiv_core.rst_ni <= rst_ni (sub_modules[1].connections[1])
  - clkdiv_core.enable_i <= enable (sub_modules[1].connections[2])
  - clkdiv_core.divisor_i <= active_divisor (sub_modules[1].connections[3])
  - clkdiv_core.clk_o <= clk_o (sub_modules[1].connections[4])
  - clkdiv_core.locked_o <= locked_o (sub_modules[1].connections[5])
  - clkdiv_core.terminal_event_o <= terminal_event (sub_modules[1].connections[6])
  - clkdiv_core.clk_i <= clk_i (integration.connections[11])
  - clkdiv_core.rst_ni <= rst_ni (integration.connections[12])
  - clkdiv_core.enable_i <= enable (integration.connections[13])
  - clkdiv_core.divisor_i <= active_divisor (integration.connections[14])
  - clkdiv_core.clk_o <= clk_o (integration.connections[15])

## Tasks

### RTL-0029: Implement divider counter and output timing core

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Implement enable behavior, active/pending divisor boundary update, counter terminal detection, clk_o sequential toggle, locked_o, and terminal_event_o from function_model and cycle_model.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: clkdiv_core in rtl/clkdiv_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CLKDIV_CORE.
- Current reason: Owner RTL file is missing: rtl/clkdiv_core.sv.
- Criteria:
  - clk_o changes only on clk_i rising edge terminal count
  - DIVISOR updates are glitchless and apply only at terminal boundary
  - FSM states/transitions and coverage hooks align with fsm.divider_fsm
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/clkdiv_core.sv
  - Semantic source_refs covered: cycle_model.ordering, cycle_model.pipeline, fsm.divider_fsm, function_model.transactions.FM_DIVIDE
- SSOT refs: cycle_model.ordering, cycle_model.pipeline, fsm.divider_fsm, function_model.transactions.FM_DIVIDE, workflow_todos.rtl-gen[2]
