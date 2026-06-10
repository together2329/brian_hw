# RTL Authoring Packet: module__fifo_sync_cx1__workflow_todo

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 10/11 section=workflow_todo task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0021: Implement 8x8 synchronous FIFO with full/empty flags

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Registered write and read with wr_ptr, rd_ptr, count. full = (count==8), empty = (count==0). rd_data = fifo_memory[rd_ptr] combinational.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via workflow_todos.owner.
SSOT item context: id=RTL_FIFO_CORE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL compiles with no errors
  - full/empty flags correct for boundary cases
  - rd_data tracks written data
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - Semantic source_refs covered: function_model.transactions.FM_READ, function_model.transactions.FM_WRITE
- SSOT refs: function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, workflow_todos.rtl-gen[0]
