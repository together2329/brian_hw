# RTL Authoring Packet: module__pl330realverify__workflow_todo

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
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
- Slice rule: Owner module pl330realverify is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])
- SSOT top IO contracts: 46

## Tasks

### RTL-0027: Implement top module, parameter header, and manifest-owned hierarchy

- Priority: high
- Required: True
- Status: planned
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Create rtl/pl330realverify.sv as the top module named pl330realverify plus rtl/pl330realverify_param.vh. Instantiate or directly implement the declared manifest submodules exactly as listed in sub_modules and integration.connections. Do not introduce undeclared external modules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: pl330realverify in rtl/pl330realverify.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP_AND_PARAMS.
- Current reason: RTL audit has not run yet.
- Criteria:
  - rtl/pl330realverify.sv contains module pl330realverify with ports matching io_list
  - rtl/pl330realverify_param.vh defines DATA_WIDTH, ADDR_WIDTH, ID_WIDTH, NUM_CHANNELS, NUM_EVENTS, REG_ADDR_WIDTH, MAX_BURST_LEN, CLOCK_FREQ_MHZ, RESET_POLARITY, and SUPPORT_UNALIGNED
  - All declared manifest submodules are present or intentionally folded with provenance to their source refs
  - Integration wiring matches integration.connections or an SSOT TBD report is returned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - Semantic source_refs covered: integration.connections, io_list, parameters, sub_modules, top_module
- SSOT refs: integration.connections, io_list, parameters, sub_modules, top_module, workflow_todos.rtl-gen[0]
