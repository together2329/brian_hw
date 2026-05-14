# RTL Authoring Packet: module__id_stage

- Kind: module
- Owner module: id_stage
- Owner file: rtl/cortex_m0lite_id_stage.sv
- Task count: 1
- Required tasks: 1

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: coverage_tap, dataflow, dataflow.ordering, dataflow.sequence, function_model, function_model.transactions.FM_CPU_STEP, isa_spec, isa_spec.decode_rule_set, parameters
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - id_stage.clk <= clk (integration.connections[2])
  - id_stage.rst_n <= core_rst_n_sync (integration.connections[2])
  - id_stage.if_id_valid <= if_id_valid (integration.connections[2])
  - id_stage.id_ex_valid <= id_ex_valid (integration.connections[2])
  - id_stage.id_ex_ready <= id_ex_ready (integration.connections[2])

## Tasks

### RTL-0179: Prove module id_stage is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.id_stage.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.id_stage.module_equivalence.
Owner: id_stage in rtl/cortex_m0lite_id_stage.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.id_stage.module_equivalence
  - Primary implementation evidence is in rtl/cortex_m0lite_id_stage.sv
- SSOT refs: sub_modules.id_stage.module_equivalence
