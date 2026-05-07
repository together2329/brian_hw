# RTL Authoring Packet: module__atciic100_ctrl__function_model_03

- Kind: module
- Owner module: atciic100_ctrl
- Owner file: rtl/atciic100_ctrl.v
- Task count: 2
- Required tasks: 2

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, fsm, fsm.iic_phase, function_model, function_model.transactions
- Module slice: 3/7 section=function_model task_limit=48
- Slice rule: Owner module atciic100_ctrl is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atciic100_ctrl.cmd <= cmd_reg (sub_modules[0].connections[0])
  - atciic100_ctrl.setup <= setup_reg (sub_modules[0].connections[1])
  - atciic100_ctrl.data_out <= rx_data (sub_modules[2].connections[1])
  - atciic100_ctrl.scl_i <= scl_filtered (sub_modules[3].connections[0])

## Tasks

### RTL-0149: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=No destination write occurs before the corresponding source read completes in any transaction..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_4

### RTL-0150: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: open
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: atciic100_ctrl in rtl/atciic100_ctrl.v via function_model.
SSOT item context: value=SCL/SDA outputs are open-drain: driven low or released high, never actively driven high..
- Current reason: Owner RTL file is missing: rtl/atciic100_ctrl.v.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/atciic100_ctrl.v
- SSOT refs: function_model.invariants.invariant_5
