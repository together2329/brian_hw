# RTL Authoring Packet: module__atciic100_ctrl__equivalence

- Kind: module
- Owner module: atciic100_ctrl
- Owner file: rtl/atciic100_ctrl.v
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, fsm, fsm.iic_phase, function_model, function_model.transactions
- Module slice: 6/7 section=equivalence task_limit=48
- Slice rule: Owner module atciic100_ctrl is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])

## Tasks

### RTL-0219: Prove module atciic100_ctrl is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_ctrl.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_ctrl.module_equivalence.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_ctrl.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: sub_modules.atciic100_ctrl.module_equivalence
