# RTL Authoring Packet: module__spi_regs__workflow_todo

- Kind: module
- Owner module: spi_regs
- Owner file: rtl/spi_regs.sv
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
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module spi_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0028: Implement APB decode and access policy

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Decode CSR map, enforce RO/WO and PSTRB policy, assert PSLVERR on illegal access, and update illegal_access sticky bits.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: spi_regs in rtl/spi_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_SPI_APB_POLICY.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Register map offsets/fields match SSOT
  - Error handling semantics match error_handling
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/spi_regs.sv
  - Semantic source_refs covered: error_handling.error_sources, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: error_handling.error_sources, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]
