# RTL Authoring Packet: module__fifo_sync_ptrs__workflow_todo

- Kind: module
- Owner module: fifo_sync_ptrs
- Owner file: rtl/fifo_sync_ptrs.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, decomposition.units.pointer_control, fsm.ptr_fsm, function_model, function_model.state_variables, function_model.state_variables.count, function_model.state_variables.rd_ptr, function_model.state_variables.wr_ptr
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module fifo_sync_ptrs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0027: Implement pointer management and fill counter

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model state_variables (wr_ptr, rd_ptr, count) and cycle_model pipeline stages into sequential always block with push/pop acceptance logic. Wrapping is modular at DEPTH. Count increments on push, decrements on pop, clamped to [0..DEPTH].
SSOT ref: workflow_todos.rtl-gen[0].
Owner: fifo_sync_ptrs in rtl/fifo_sync_ptrs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO_PTRS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - wr_ptr and rd_ptr are declared with correct width ($clog2(DEPTH))
  - count is declared with width $clog2(DEPTH+1)
  - Push increments wr_ptr and count when wr_en_i && !full_o && !flush_i
  - Pop increments rd_ptr and decrements count when rd_en_i && !empty_o && !flush_i
  - Simultaneous push/pop: both pointers advance, count unchanged
  - Flush: all three reset to 0, priority over push/pop
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/fifo_sync_ptrs.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm.ptr_fsm, function_model.state_variables
- SSOT refs: cycle_model.pipeline, fsm.ptr_fsm, function_model.state_variables, workflow_todos.rtl-gen[0]
