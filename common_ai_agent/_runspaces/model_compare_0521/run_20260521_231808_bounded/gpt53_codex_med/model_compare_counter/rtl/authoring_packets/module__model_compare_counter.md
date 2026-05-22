# RTL Authoring Packet: module__model_compare_counter

- Kind: module
- Owner module: model_compare_counter
- Owner file: rtl/model_compare_counter.sv
- Task count: 21
- Required tasks: 21

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- SSOT connection contracts:
  - model_compare_counter.clk <= clk (integration.connections[0])
  - model_compare_counter.rst_n <= rst_n (integration.connections[1])
  - model_compare_counter.enable <= enable (integration.connections[2])
  - model_compare_counter.clear <= clear (integration.connections[3])
  - model_compare_counter.step <= step (integration.connections[4])
- SSOT top IO contracts: 8

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_module.
SSOT item context: value=model_compare_counter.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: io_list

### RTL-0136: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=Apply rst_n low then high to return outputs/state to known zero baseline..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0137: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=count output integrity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: security.assets.asset_0

### RTL-0138: Implement security item asset_1

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=clear priority correctness.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: security.assets.asset_1

### RTL-0139: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=overflow pulse correctness.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: security.assets.asset_2

### RTL-0140: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: value=Single synchronous clock domain source.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0141: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: value=Active-low reset distribution.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0142: Implement integration item clk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.clk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clk.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: port=clk; signal=clk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clk
  - Primary implementation evidence is in rtl/model_compare_counter.sv
  - DUT port clk is the implementation/observation point for clk
- SSOT refs: integration.connections.clk

### RTL-0143: Implement integration item rst_n

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rst_n
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rst_n.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: port=rst_n; signal=rst_n.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rst_n
  - Primary implementation evidence is in rtl/model_compare_counter.sv
  - DUT port rst_n is the implementation/observation point for rst_n
- SSOT refs: integration.connections.rst_n

### RTL-0144: Implement integration item enable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.enable.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: port=enable; signal=enable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.enable
  - Primary implementation evidence is in rtl/model_compare_counter.sv
  - DUT port enable is the implementation/observation point for enable
- SSOT refs: integration.connections.enable

### RTL-0145: Implement integration item clear

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.clear
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.clear.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: port=clear; signal=clear.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.clear
  - Primary implementation evidence is in rtl/model_compare_counter.sv
  - DUT port clear is the implementation/observation point for clear
- SSOT refs: integration.connections.clear

### RTL-0146: Implement integration item step

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.step
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.step.
Owner: model_compare_counter in rtl/model_compare_counter.sv via integration.
SSOT item context: port=step; signal=step.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.step
  - Primary implementation evidence is in rtl/model_compare_counter.sv
  - DUT port step is the implementation/observation point for step
- SSOT refs: integration.connections.step

### RTL-0147: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=Constrain clk to 100 MHz target.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0148: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: value=Constrain rst_n as asynchronous reset input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0149: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0150: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0151: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: name=frequency_mhz_min; value=100.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0153: Prove module model_compare_counter is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.model_compare_counter.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.model_compare_counter.module_equivalence.
Owner: model_compare_counter in rtl/model_compare_counter.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.model_compare_counter.module_equivalence
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: sub_modules.model_compare_counter.module_equivalence

### RTL-0023: Implement parameter COUNT_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.COUNT_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.COUNT_WIDTH.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: name=COUNT_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.COUNT_WIDTH
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: parameters.COUNT_WIDTH

### RTL-0024: Implement parameter STEP_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STEP_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STEP_WIDTH.
Owner: model_compare_counter in rtl/model_compare_counter.sv via top_fallback.
SSOT item context: name=STEP_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STEP_WIDTH
  - Primary implementation evidence is in rtl/model_compare_counter.sv
- SSOT refs: parameters.STEP_WIDTH
