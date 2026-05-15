# RTL Authoring Packet: module__fifo_sync__workflow_todo

- Kind: module
- Owner module: fifo_sync
- Owner file: rtl/fifo_sync.sv
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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 9/9 section=workflow_todo task_limit=48
- Slice rule: Owner module fifo_sync is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
- SSOT top IO contracts: 20

## Tasks

### RTL-0032: Implement top-level integration and wiring

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[5]
- Detail: Instantiate fifo_sync_mem, fifo_sync_ptrs, fifo_sync_flags, fifo_sync_output_reg, and fifo_sync_regs (conditional) with named port connections matching integration.connections. Wire top-level ports to sub-module ports.
SSOT ref: workflow_todos.rtl-gen[5].
Owner: fifo_sync in rtl/fifo_sync.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO_TOP.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - All sub_modules instantiated with correct port maps per integration.connections
  - USE_APB controls whether fifo_sync_regs is instantiated
  - USE_OUTPUT_REGISTER controls output register path
  - Top-level ports match io_list exactly
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[5]
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - Semantic source_refs covered: integration.connections, io_list.interfaces, sub_modules
- SSOT refs: integration.connections, io_list.interfaces, sub_modules, workflow_todos.rtl-gen[5]
