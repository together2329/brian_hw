# RTL Authoring Packet: module__cortex_m0lite_core__io_list

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 1/10 section=io_list task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0045: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.core_clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.core_clk.ports.clk.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.core_clk.ports.clk
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.core_clk.ports.clk

### RTL-0047: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.core_rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.core_rst_n.ports.rst_n.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.core_rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.core_rst_n.ports.rst_n
