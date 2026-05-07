# RTL Authoring Packet: module__pl330_target_apb_regs

- Kind: module
- Owner module: pl330_target_apb_regs
- Owner file: rtl/pl330_target_apb_regs.sv
- Task count: 4
- Required tasks: 4

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
- Owner refs: cycle_model.handshake_rules.apb, registers.register_list
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_apb_regs.axi_error <= apb_regs_axi_error (observed_named_port_map)
  - pl330_target_apb_regs.cfg_dst_addr <= apb_regs_cfg_dst_addr (observed_named_port_map)
  - pl330_target_apb_regs.cfg_enable <= apb_regs_cfg_enable (observed_named_port_map)
  - pl330_target_apb_regs.cfg_len <= apb_regs_cfg_len (observed_named_port_map)
  - pl330_target_apb_regs.cfg_secure <= apb_regs_cfg_secure (observed_named_port_map)
  - pl330_target_apb_regs.cfg_src_addr <= apb_regs_cfg_src_addr (observed_named_port_map)
  - pl330_target_apb_regs.clear_done_pulse <= apb_regs_clear_done_pulse (observed_named_port_map)
  - pl330_target_apb_regs.clear_error_pulse <= apb_regs_clear_error_pulse (observed_named_port_map)

## Tasks

### RTL-0036: Implement or account for SSOT module slice `pl330_target_apb_regs`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[9]
- Detail: name=pl330_target_apb_regs
SSOT ref: workflow_todos.rtl-gen[9].
Owner: pl330_target_apb_regs in rtl/pl330_target_apb_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_APB_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[9]
  - Primary implementation evidence is in rtl/pl330_target_apb_regs.sv
  - Semantic source_refs covered: sub_modules[8]
- SSOT refs: sub_modules[8], workflow_todos.rtl-gen[9]

### RTL-0269: Prove module pl330_target_apb_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_apb_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_apb_regs.module_equivalence.
Owner: pl330_target_apb_regs in rtl/pl330_target_apb_regs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_apb_regs.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_apb_regs.sv
- SSOT refs: sub_modules.pl330_target_apb_regs.module_equivalence

### RTL-0096: Implement parameter APB_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_DATA_WIDTH.
Owner: pl330_target_apb_regs in rtl/pl330_target_apb_regs.sv via semantic_terms:apb.
SSOT item context: name=APB_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_DATA_WIDTH
  - Primary implementation evidence is in rtl/pl330_target_apb_regs.sv
- SSOT refs: parameters.APB_DATA_WIDTH

### RTL-0097: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: pl330_target_apb_regs in rtl/pl330_target_apb_regs.sv via semantic_terms:apb.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/pl330_target_apb_regs.sv
- SSOT refs: parameters.APB_ADDR_WIDTH
