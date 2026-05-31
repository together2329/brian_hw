# RTL Authoring Packet: module__mctp_assembler_scratch

- Kind: module
- Owner module: mctp_assembler_scratch
- Owner file: rtl/mctp_assembler_scratch.sv
- Task count: 25
- Required tasks: 25

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- SSOT connection contracts:
  - mctp_assembler_scratch_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])
  - mctp_assembler_scratch_sram_packer.sram_wr_valid <= sram_wr_valid (integration.connections[2])
  - mctp_assembler_scratch_axi_read_egress.m_axi_rvalid <= m_axi_rvalid (integration.connections[3])
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])
- SSOT top IO contracts: 55

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_module.
SSOT item context: value=mctp_assembler_scratch.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: io_list

### RTL-0020: Implement AXI write ingress and no-ID one-outstanding write behavior.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: AW/W/B channels must follow io_list and cycle_model handshake rules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_level_handshake_rule.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_compile_passes
  - lint_passes
  - axi_write_module_present
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - Semantic source_refs covered: cycle_model.handshake_rules.axi_write_channels, io_list.interfaces.axi_write_slave
- SSOT refs: cycle_model.handshake_rules.axi_write_channels, io_list.interfaces.axi_write_slave, workflow_todos.rtl-gen[0]

### RTL-0297: Implement handshake rule: axi_write_channels

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.axi_write_channels
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.axi_write_channels.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_level_handshake_rule.
SSOT item context: name=axi_write_channels; signal=m_axi_awvalid/m_axi_awready/m_axi_wvalid/m_axi_wready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.axi_write_channels
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - axi_write_channels appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.axi_write_channels

### RTL-0298: Implement handshake rule: axi_read_channels

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.axi_read_channels
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.axi_read_channels.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_level_handshake_rule.
SSOT item context: name=axi_read_channels; signal=m_axi_arvalid/m_axi_arready/m_axi_rvalid/m_axi_rready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.axi_read_channels
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - axi_read_channels appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.axi_read_channels

### RTL-0299: Implement handshake rule: apb_access

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.apb_access
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.apb_access.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_level_handshake_rule.
SSOT item context: name=apb_access; signal=psel/penable/pready.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.apb_access
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - apb_access appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.apb_access

### RTL-0300: Implement handshake rule: sram_ready_valid

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sram_ready_valid
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sram_ready_valid.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_level_handshake_rule.
SSOT item context: name=sram_ready_valid; signal=sram_wr_valid/sram_wr_ready/sram_rd_req_valid/sram_rd_req_ready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sram_ready_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - sram_ready_valid appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sram_ready_valid

### RTL-0399: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=assembled_mctp_payload_in_external_sram.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: security.assets.asset_0

### RTL-0401: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=packet_and_assembly_drop_counters.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: security.assets.asset_2

### RTL-0406: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: name=external_modules; value=["external_256b_sram"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0407: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: name=external_clocks; value=["axi_aclk", "pclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0408: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: name=external_resets; value=["axi_aresetn", "presetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0409: Implement integration item m_axi_awvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.m_axi_awvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.m_axi_awvalid.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: port=m_axi_awvalid; signal=m_axi_awvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_awvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - DUT port m_axi_awvalid is the implementation/observation point for m_axi_awvalid
- SSOT refs: integration.connections.m_axi_awvalid

### RTL-0410: Implement integration item m_axi_wvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.m_axi_wvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.m_axi_wvalid.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: port=m_axi_wvalid; signal=m_axi_wvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_wvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - DUT port m_axi_wvalid is the implementation/observation point for m_axi_wvalid
- SSOT refs: integration.connections.m_axi_wvalid

### RTL-0411: Implement integration item sram_wr_valid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.sram_wr_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.sram_wr_valid.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: port=sram_wr_valid; signal=sram_wr_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - DUT port sram_wr_valid is the implementation/observation point for sram_wr_valid
- SSOT refs: integration.connections.sram_wr_valid

### RTL-0412: Implement integration item m_axi_rvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.m_axi_rvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.m_axi_rvalid.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: port=m_axi_rvalid; signal=m_axi_rvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_rvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - DUT port m_axi_rvalid is the implementation/observation point for m_axi_rvalid
- SSOT refs: integration.connections.m_axi_rvalid

### RTL-0413: Implement integration item pready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pready.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via integration.
SSOT item context: port=pready; signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
  - DUT port pready is the implementation/observation point for pready
- SSOT refs: integration.connections.pready

### RTL-0414: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=No inferred latches..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0415: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=No unresolved black boxes except external SRAM model in integration testbench..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0416: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=All sequential state has reset or documented initialization..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0417: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: value=No AXI ID ports are generated..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0418: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: name=frequency_mhz_min; value=250.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0419: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0420: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via top_fallback.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0431: Prove module mctp_assembler_scratch is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch.module_equivalence.
Owner: mctp_assembler_scratch in rtl/mctp_assembler_scratch.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch.sv
- SSOT refs: sub_modules.mctp_assembler_scratch.module_equivalence
