# RTL Authoring Packet: module__arm_m0_min_rf

- Kind: module
- Owner module: arm_m0_min_rf
- Owner file: rtl/arm_m0_min_rf.sv
- Task count: 5
- Required tasks: 5

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
- Owner refs: function_model, function_model.state_variables, register_file, register_file.architecture

## Tasks

### RTL-0056: Implement RTL state owner for FL state pc

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.pc
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.pc.
Owner: arm_m0_min_rf in rtl/arm_m0_min_rf.sv via function_model.state_variables.
SSOT item context: name=pc; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.pc
  - Primary implementation evidence is in rtl/arm_m0_min_rf.sv
  - pc reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.pc

### RTL-0057: Implement RTL state owner for FL state gpr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.gpr
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.gpr.
Owner: arm_m0_min_rf in rtl/arm_m0_min_rf.sv via function_model.state_variables.
SSOT item context: name=gpr; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.gpr
  - Primary implementation evidence is in rtl/arm_m0_min_rf.sv
  - gpr reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.gpr

### RTL-0058: Implement RTL state owner for FL state nzcv

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.nzcv
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.nzcv.
Owner: arm_m0_min_rf in rtl/arm_m0_min_rf.sv via function_model.state_variables.
SSOT item context: name=nzcv; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.nzcv
  - Primary implementation evidence is in rtl/arm_m0_min_rf.sv
  - nzcv reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.nzcv

### RTL-0059: Implement RTL state owner for FL state fault_halt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_variable
- Source ref: function_model.state_variables.fault_halt
- Detail: Every FunctionalModel state variable that is architecturally visible or affects outputs needs RTL storage, reset, and update behavior.
SSOT ref: function_model.state_variables.fault_halt.
Owner: arm_m0_min_rf in rtl/arm_m0_min_rf.sv via function_model.state_variables.
SSOT item context: name=fault_halt; reset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State has a flop/register/memory owner in RTL
  - Reset value matches SSOT
  - Every transaction update occurs at the SSOT-defined acceptance/cycle point
  - Traceability keeps source_ref function_model.state_variables.fault_halt
  - Primary implementation evidence is in rtl/arm_m0_min_rf.sv
  - fault_halt reset behavior matches SSOT value 0
- SSOT refs: function_model.state_variables.fault_halt

### RTL-0145: Prove module arm_m0_min_rf is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.arm_m0_min_rf.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arm_m0_min_rf.module_equivalence.
Owner: arm_m0_min_rf in rtl/arm_m0_min_rf.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arm_m0_min_rf.module_equivalence
  - Primary implementation evidence is in rtl/arm_m0_min_rf.sv
- SSOT refs: sub_modules.arm_m0_min_rf.module_equivalence
