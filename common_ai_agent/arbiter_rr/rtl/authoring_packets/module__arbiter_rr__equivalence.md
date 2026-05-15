# RTL Authoring Packet: module__arbiter_rr__equivalence

- Kind: module
- Owner module: arbiter_rr
- Owner file: rtl/arbiter_rr.sv
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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 8/9 section=equivalence task_limit=48
- Slice rule: Owner module arbiter_rr is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_regs.PCLK <= PCLK (integration.connections[0])
  - arbiter_rr_regs.PRESETn <= PRESETn (integration.connections[1])
  - arbiter_rr_regs.PADDR <= PADDR (integration.connections[2])
  - arbiter_rr_regs.PSEL <= PSEL (integration.connections[3])
  - arbiter_rr_regs.PENABLE <= PENABLE (integration.connections[4])
  - arbiter_rr_regs.PWRITE <= PWRITE (integration.connections[5])
  - arbiter_rr_regs.PWDATA <= PWDATA (integration.connections[6])
  - arbiter_rr_regs.PRDATA <= PRDATA (integration.connections[7])
  - arbiter_rr_regs.PREADY <= PREADY (integration.connections[8])
  - arbiter_rr_regs.PSLVERR <= PSLVERR (integration.connections[9])
  - arbiter_rr_regs.enable_o <= arb_enable (integration.connections[10])
  - arbiter_rr_regs.mask_o <= req_mask (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0159: Prove module arbiter_rr is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.arbiter_rr.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arbiter_rr.module_equivalence.
Owner: arbiter_rr in rtl/arbiter_rr.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arbiter_rr.module_equivalence
  - Primary implementation evidence is in rtl/arbiter_rr.sv
- SSOT refs: sub_modules.arbiter_rr.module_equivalence
