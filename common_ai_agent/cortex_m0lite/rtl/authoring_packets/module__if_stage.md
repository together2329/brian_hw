# RTL Authoring Packet: module__if_stage

- Kind: module
- Owner module: if_stage
- Owner file: rtl/cortex_m0lite_if_stage.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, io_list, isa_spec, isa_spec.decode_contract, parameters
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - if_stage.clk <= clk (integration.connections[1])
  - if_stage.rst_n <= core_rst_n_sync (integration.connections[1])
  - if_stage.if_id_valid <= if_id_valid (integration.connections[1])
  - if_stage.if_id_ready <= if_id_ready (integration.connections[1])
  - if_stage.if_id_pc <= if_id_pc (integration.connections[1])
  - if_stage.if_id_instr <= if_id_instr (integration.connections[1])

## Tasks

### RTL-0178: Prove module if_stage is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.if_stage.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.if_stage.module_equivalence.
Owner: if_stage in rtl/cortex_m0lite_if_stage.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.if_stage.module_equivalence
  - Primary implementation evidence is in rtl/cortex_m0lite_if_stage.sv
- SSOT refs: sub_modules.if_stage.module_equivalence
