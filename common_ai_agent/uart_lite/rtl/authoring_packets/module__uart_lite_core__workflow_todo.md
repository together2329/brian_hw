# RTL Authoring Packet: module__uart_lite_core__workflow_todo

- Kind: module
- Owner module: uart_lite_core
- Owner file: rtl/uart_lite_core.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, decomposition.units.execute, error_handling, features, function_model, function_model.state_variables, function_model.transactions
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module uart_lite_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])

## Tasks

### RTL-0033: Implement uart_lite_core integration module

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[6]
- Detail: Instantiate uart_lite_regs, uart_lite_tx_fifo, uart_lite_rx_fifo, uart_lite_baud_gen, uart_lite_tx_fsm, uart_lite_rx_fsm. Wire APB interface from top to regs. Wire FIFO interfaces between regs and FSMs. Implement loopback mux (txd_o to rxd synchronizer input when loopback=1). Wire interrupt aggregation (INT_PENDING & INT_MASK → irq_o). Wire debug counter increment signals from FSMs to regs.
SSOT ref: workflow_todos.rtl-gen[6].
Owner: uart_lite_core in rtl/uart_lite_core.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All sub-module instances connected per integration.connections
  - Loopback mux correctly selects txd_o vs rxd_i before synchronizer
  - irq_o = |(INT_PENDING & INT_MASK)
  - Debug counters increment on correct events
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[6]
  - Primary implementation evidence is in rtl/uart_lite_core.sv
  - Semantic source_refs covered: cycle_model, dataflow, error_handling, features, function_model, integration
- SSOT refs: cycle_model, dataflow, error_handling, features, function_model, integration, workflow_todos.rtl-gen[6]
