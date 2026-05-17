# RTL Authoring Packet: module__atcwdt200_regs__equivalence

- Kind: module
- Owner module: atcwdt200_regs
- Owner file: rtl/atcwdt200_regs.sv
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
- Owner refs: dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, dataflow.sinks.sinks_0, decomposition.units.apb_register_block, error_handling, function_model, function_model.transactions.apb_read, function_model.transactions.apb_write, function_model.transactions.write_unlock, registers, registers.register_list
- Module slice: 4/5 section=equivalence task_limit=48
- Slice rule: Owner module atcwdt200_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_regs.pclk <= pclk (integration.connections[0])
  - atcwdt200_regs.presetn <= presetn (integration.connections[1])

## Tasks

### RTL-0196: Prove module atcwdt200_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.atcwdt200_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atcwdt200_regs.module_equivalence.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atcwdt200_regs.module_equivalence
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: sub_modules.atcwdt200_regs.module_equivalence
