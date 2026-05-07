# RTL Authoring Packet: module__pl330_target_axi

- Kind: module
- Owner module: pl330_target_axi
- Owner file: rtl/pl330_target_axi.sv
- Task count: 5
- Required tasks: 5

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
- Owner refs: cycle_model.handshake_rules.axi_ar, cycle_model.handshake_rules.axi_aw, cycle_model.handshake_rules.axi_b, cycle_model.handshake_rules.axi_r, cycle_model.handshake_rules.axi_w, cycle_model.ordering.axi_outstanding
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_axi.axi_busy <= axi_busy (observed_named_port_map)
  - pl330_target_axi.axi_error_sticky <= axi_error_sticky (observed_named_port_map)
  - pl330_target_axi.clk <= clk (observed_named_port_map)
  - pl330_target_axi.m_axi_araddr <= axi_m_axi_araddr (observed_named_port_map)
  - pl330_target_axi.m_axi_arburst <= axi_m_axi_arburst (observed_named_port_map)
  - pl330_target_axi.m_axi_arid <= axi_m_axi_arid (observed_named_port_map)
  - pl330_target_axi.m_axi_arlen <= axi_m_axi_arlen (observed_named_port_map)
  - pl330_target_axi.m_axi_arready <= axi_m_axi_arready (observed_named_port_map)

## Tasks

### RTL-0034: Implement or account for SSOT module slice `pl330_target_axi`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[7]
- Detail: name=pl330_target_axi
SSOT ref: workflow_todos.rtl-gen[7].
Owner: pl330_target_axi in rtl/pl330_target_axi.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_AXI.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[7]
  - Primary implementation evidence is in rtl/pl330_target_axi.sv
  - Semantic source_refs covered: sub_modules[6]
- SSOT refs: sub_modules[6], workflow_todos.rtl-gen[7]

### RTL-0267: Prove module pl330_target_axi is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_axi.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_axi.module_equivalence.
Owner: pl330_target_axi in rtl/pl330_target_axi.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_axi.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_axi.sv
- SSOT refs: sub_modules.pl330_target_axi.module_equivalence

### RTL-0093: Implement parameter AXI_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_DATA_WIDTH.
Owner: pl330_target_axi in rtl/pl330_target_axi.sv via semantic_terms:axi.
SSOT item context: name=AXI_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_DATA_WIDTH
  - Primary implementation evidence is in rtl/pl330_target_axi.sv
- SSOT refs: parameters.AXI_DATA_WIDTH

### RTL-0094: Implement parameter AXI_ID_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_ID_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_ID_WIDTH.
Owner: pl330_target_axi in rtl/pl330_target_axi.sv via semantic_terms:axi.
SSOT item context: name=AXI_ID_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_ID_WIDTH
  - Primary implementation evidence is in rtl/pl330_target_axi.sv
- SSOT refs: parameters.AXI_ID_WIDTH

### RTL-0095: Implement parameter AXI_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_ADDR_WIDTH.
Owner: pl330_target_axi in rtl/pl330_target_axi.sv via semantic_terms:axi.
SSOT item context: name=AXI_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_ADDR_WIDTH
  - Primary implementation evidence is in rtl/pl330_target_axi.sv
- SSOT refs: parameters.AXI_ADDR_WIDTH
