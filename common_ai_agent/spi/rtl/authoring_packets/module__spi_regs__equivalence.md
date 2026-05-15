# RTL Authoring Packet: module__spi_regs__equivalence

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 5/6 section=equivalence task_limit=48
- Slice rule: Owner module spi_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0243: Prove module spi_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_regs.module_equivalence.
Owner: spi_regs in rtl/spi_regs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_regs.module_equivalence
  - Primary implementation evidence is in rtl/spi_regs.sv
- SSOT refs: sub_modules.spi_regs.module_equivalence
