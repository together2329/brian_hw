# RTL Authoring Packet: module__fifo_sync_mem

- Kind: module
- Owner module: fifo_sync_mem
- Owner file: rtl/fifo_sync_mem.sv
- Task count: 3
- Required tasks: 3

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: dataflow, dataflow.read_path, dataflow.write_path, memory, memory.instances
- SSOT connection contracts:
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])

## Tasks

### RTL-0028: Implement dual-port register array storage

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Behavioral reg array of DEPTH entries x DATA_WIDTH bits. Write port: mem[wr_ptr] <= wr_data_i on push acceptance. Read port: combinational rd_data_o = mem[rd_ptr] (or routed through output register).
SSOT ref: workflow_todos.rtl-gen[1].
Owner: fifo_sync_mem in rtl/fifo_sync_mem.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_FIFO_MEM.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_mem.sv.
- Criteria:
  - Memory array declared as reg [DATA_WIDTH-1:0] mem [0:DEPTH-1]
  - Write occurs when push_accepted
  - Read port drives mem[rd_ptr] combinationally or to output register
  - Memory resets to 0 on async reset
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/fifo_sync_mem.sv
  - Semantic source_refs covered: dataflow.read_path, dataflow.write_path, memory.instances.fifo_ram
- SSOT refs: dataflow.read_path, dataflow.write_path, memory.instances.fifo_ram, workflow_todos.rtl-gen[1]

### RTL-0191: Implement memory item fifo_ram

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.fifo_ram
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.fifo_ram.
Owner: fifo_sync_mem in rtl/fifo_sync_mem.sv via memory.instances.
SSOT item context: name=fifo_ram; width=DATA_WIDTH; depth=DEPTH; latency=0.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_mem.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.fifo_ram
  - Primary implementation evidence is in rtl/fifo_sync_mem.sv
  - fifo_ram width matches SSOT value DATA_WIDTH
  - fifo_ram timing uses SSOT cycle/latency 0
  - fifo_ram storage depth matches SSOT value DEPTH
- SSOT refs: memory.instances.fifo_ram

### RTL-0244: Prove module fifo_sync_mem is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.fifo_sync_mem.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.fifo_sync_mem.module_equivalence.
Owner: fifo_sync_mem in rtl/fifo_sync_mem.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/fifo_sync_mem.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.fifo_sync_mem.module_equivalence
  - Primary implementation evidence is in rtl/fifo_sync_mem.sv
- SSOT refs: sub_modules.fifo_sync_mem.module_equivalence
