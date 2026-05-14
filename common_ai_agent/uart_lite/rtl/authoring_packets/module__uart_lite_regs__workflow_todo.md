# RTL Authoring Packet: module__uart_lite_regs__workflow_todo

- Kind: module
- Owner module: uart_lite_regs
- Owner file: rtl/uart_lite_regs.sv
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
- Owner refs: interrupts, registers, registers.register_list
- Module slice: 5/5 section=workflow_todo task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0032: Implement APB-lite register block with decode, read-mux, W1C interrupt clear

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[5]
- Detail: APB-lite slave interface. Decodes PADDR to select register. Handles RW/RO/WO/W1C access policy per registers.register_list. Generates PREADY (0 or 1 wait state) and PSLVERR for unmapped addresses. Maintains sticky status flags and debug counters. W1C logic: write 1 clears; write 0 has no effect.
SSOT ref: workflow_todos.rtl-gen[5].
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All registers in register_list implemented with correct offset, width, access, reset
  - APB-lite protocol per io_list.interfaces.apb_slave.protocol
  - W1C clear logic: write 1 clears; write 0 no effect
  - Reserved fields read as zero
  - PSLVERR asserted for unmapped addresses
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[5]
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - Semantic source_refs covered: interrupts, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: interrupts, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[5]
