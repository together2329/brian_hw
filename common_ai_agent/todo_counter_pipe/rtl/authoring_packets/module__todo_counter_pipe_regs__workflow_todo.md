# RTL Authoring Packet: module__todo_counter_pipe_regs__workflow_todo

- Kind: module
- Owner module: todo_counter_pipe_regs
- Owner file: rtl/todo_counter_pipe_regs.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model.handshake_rules.counter_irq, cycle_model.handshake_rules.prdata, cycle_model.handshake_rules.pready, cycle_model.pipeline.S0_APB_ACCESS, cycle_model.pipeline.S4_STATUS_UPDATE, decomposition.units.apb_decode, function_model.transactions.FM10, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CNT, registers.register_list.CTRL, registers.register_list.DBGCNT, registers.register_list.INTCLR
- Module slice: 7/7 section=workflow_todo task_limit=48
- Slice rule: Owner module todo_counter_pipe_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_regs.bus_clk <= bus_clk (integration.connections[0])
  - todo_counter_pipe_regs.bus_rst_n <= bus_rst_n (integration.connections[1])
  - todo_counter_pipe_regs.irq_o <= counter_irq (integration.connections[2])

## Tasks

### RTL-0021: Implement APB-lite register file and interrupt logic

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement APB-lite slave with zero-wait-state pready, register decode for CTRL/CNT/LOAD/TERM/STATUS/INTEN/INTSTAT/INTCLR/DBGCNT, W1C interrupt clear, and counter_irq combinatorial output.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_APB_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - APB zero-wait-state: pready = psel & penable (combinational)
  - All register fields match registers.register_list bit ranges, access, and reset values
  - W1C INTCLR clears corresponding INTSTAT and STATUS bits
  - counter_irq = (tc_pending & tc_en) | (ovf_pending & ovf_en) | (unf_pending & unf_en)
  - Readback of CNT/STATUS/INTSTAT/DBGCNT from CDC-synchronized bus-domain shadow registers
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - Semantic source_refs covered: interrupts, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: interrupts, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]
