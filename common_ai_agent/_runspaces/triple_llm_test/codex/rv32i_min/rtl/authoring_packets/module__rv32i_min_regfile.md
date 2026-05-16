# RTL Authoring Packet: module__rv32i_min_regfile

- Kind: module
- Owner module: rv32i_min_regfile
- Owner file: rtl/rv32i_min_regfile.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: function_model, function_model.invariants, function_model.state_variables, function_model.state_variables.regfile
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8

## Tasks

### RTL-0023: Enforce x0 immutable behavior

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Mask writes to x0 and force reads of x0 to zero
SSOT ref: workflow_todos.rtl-gen[3].
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via workflow_todos.owner.
SSOT item context: id=RTL_REGFILE_X0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Invariant regfile_x0 equals 0 always
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
  - Semantic source_refs covered: function_model.invariants
- SSOT refs: function_model.invariants, workflow_todos.rtl-gen[3]

### RTL-0052: Implement RTL state owner for FL state regfile

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.regfile
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.regfile.
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via function_model.state_variables.regfile.
SSOT item context: name=regfile; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.regfile
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
  - regfile reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.regfile

### RTL-0120: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via function_model.invariants.
SSOT item context: value=regfile_x0 == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
- SSOT refs: function_model.invariants.invariant_0

### RTL-0121: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via function_model.invariants.
SSOT item context: value=misaligned_access implies no_retire.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
- SSOT refs: function_model.invariants.invariant_1

### RTL-0122: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via function_model.invariants.
SSOT item context: value=jalr_target_lsb == 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
- SSOT refs: function_model.invariants.invariant_2

### RTL-0174: Prove module rv32i_min_regfile is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.rv32i_min_regfile.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.rv32i_min_regfile.module_equivalence.
Owner: rv32i_min_regfile in rtl/rv32i_min_regfile.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.rv32i_min_regfile.module_equivalence
  - Primary implementation evidence is in rtl/rv32i_min_regfile.sv
- SSOT refs: sub_modules.rv32i_min_regfile.module_equivalence
