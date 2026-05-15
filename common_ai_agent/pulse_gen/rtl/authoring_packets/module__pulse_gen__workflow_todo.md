# RTL Authoring Packet: module__pulse_gen__workflow_todo

- Kind: module
- Owner module: pulse_gen
- Owner file: rtl/pulse_gen.sv
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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 9/9 section=workflow_todo task_limit=48
- Slice rule: Owner module pulse_gen is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen.PRDATA <= pulse_gen_regs.PRDATA (integration.connections[7])
  - pulse_gen.PREADY <= 1'b1 (zero-wait-state) (integration.connections[8])
  - pulse_gen.PSLVERR <= pulse_gen_regs.PSLVERR (integration.connections[9])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0022: Implement pulse_gen top-level wiring

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Instantiate pulse_gen_regs and pulse_gen_core in pulse_gen.sv top module. Wire APB signals to regs, wire register outputs to core inputs, wire core outputs (pulse_out, irq_o, status signals) to top-level ports.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: pulse_gen in rtl/pulse_gen.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Top module port list matches io_list.interfaces exactly
  - Internal connections match integration.connections
  - No undriven or unconnected signals
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Semantic source_refs covered: integration.connections, io_list.interfaces
- SSOT refs: integration.connections, io_list.interfaces, workflow_todos.rtl-gen[2]
