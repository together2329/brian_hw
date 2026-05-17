# RTL Authoring Packet: module__pl330realverify_regs__equivalence

- Kind: module
- Owner module: pl330realverify_regs
- Owner file: rtl/pl330realverify_regs.sv
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
- Owner refs: cycle_model.handshake_rules.APB_ACCESS, decomposition.units.apb_registers, error_handling, error_handling.error_sources, function_model.transactions.FM_APB_READ, function_model.transactions.FM_APB_WRITE, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_RESET, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, rtl_contract, rtl_contract.input_map
- Module slice: 7/8 section=equivalence task_limit=48
- Slice rule: Owner module pl330realverify_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
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

## Tasks

### RTL-0375: Prove module pl330realverify_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.pl330realverify_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330realverify_regs.module_equivalence.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330realverify_regs.module_equivalence
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
- SSOT refs: sub_modules.pl330realverify_regs.module_equivalence
