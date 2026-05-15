# RTL Authoring Packet: module__adder_kogge_stone_core__equivalence

- Kind: module
- Owner module: adder_kogge_stone_core
- Owner file: rtl/adder_kogge_stone_core.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, features, features.ks_addition, fsm, fsm.adder_fsm, function_model, function_model.state_updates, function_model.transactions, function_model.transactions.FM_ADD
- Module slice: 5/6 section=equivalence task_limit=48
- Slice rule: Owner module adder_kogge_stone_core is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_core.clk_i <= PCLK (integration.connections[0])
  - adder_kogge_stone_core.rst_ni <= PRESETn (integration.connections[1])

## Tasks

### RTL-0139: Prove module adder_kogge_stone_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.adder_kogge_stone_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.adder_kogge_stone_core.module_equivalence.
Owner: adder_kogge_stone_core in rtl/adder_kogge_stone_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.adder_kogge_stone_core.module_equivalence
  - Primary implementation evidence is in rtl/adder_kogge_stone_core.sv
- SSOT refs: sub_modules.adder_kogge_stone_core.module_equivalence
