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
- Owner refs: error_handling, interrupts, registers, registers.register_list
- Module slice: 6/6 section=workflow_todo task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])

## Tasks

### RTL-0031: Implement APB register block and interrupt combiner

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: Full APB4 slave decode for 12 registers (CTRL through DBG_PARITIES_ERR). Implement W1C for INTPEND and CLR_STAT. OR all enabled pending interrupt sources to uart_irq.
SSOT ref: workflow_todos.rtl-gen[4].
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_IMPL_REGS_IRQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All 12 registers accessible at declared offsets
  - Reserved fields read zero, ignore writes
  - W1C semantics for INTPEND and CLR_STAT
  - PSLVERR for accesses >= 0x30
  - PREADY asserted for all valid accesses
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - Semantic source_refs covered: interrupts, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: interrupts, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[4]
