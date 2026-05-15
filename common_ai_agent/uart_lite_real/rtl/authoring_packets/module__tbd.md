# RTL Authoring Packet: module__tbd

- Kind: module
- Owner module: TBD
- Owner file: rtl/TBD.sv
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

- Quality profile: standard
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: TBD in rtl/TBD.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/TBD.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: open
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: TBD in rtl/TBD.sv via top_module.
- Current reason: Owner RTL file is missing: rtl/TBD.sv.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/TBD.sv
- SSOT refs: io_list

### RTL-0021: Implement feature feature_0

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.feature_0
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.feature_0.
Owner: TBD in rtl/TBD.sv via single_owner.
- Current reason: Owner RTL file is missing: rtl/TBD.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.feature_0
  - Primary implementation evidence is in rtl/TBD.sv
- SSOT refs: features.feature_0

### RTL-0022: Prove module TBD is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.TBD.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.TBD.module_equivalence.
Owner: TBD in rtl/TBD.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/TBD.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.TBD.module_equivalence
  - Primary implementation evidence is in rtl/TBD.sv
- SSOT refs: sub_modules.TBD.module_equivalence

### RTL-0020: Implement parameter param_0

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.param_0
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.param_0.
Owner: TBD in rtl/TBD.sv via single_owner.
- Current reason: Owner RTL file is missing: rtl/TBD.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.param_0
  - Primary implementation evidence is in rtl/TBD.sv
- SSOT refs: parameters.param_0
