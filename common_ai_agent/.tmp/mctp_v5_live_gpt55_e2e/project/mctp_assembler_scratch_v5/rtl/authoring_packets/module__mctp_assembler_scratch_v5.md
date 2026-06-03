# RTL Authoring Packet: module__mctp_assembler_scratch_v5

- Kind: module
- Owner module: mctp_assembler_scratch_v5
- Owner file: rtl/mctp_assembler_scratch_v5.sv
- Task count: 24
- Required tasks: 24

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])
  - mctp_assembler_scratch_v5_sram_packer.sram_wr_valid <= pack_wr_valid (integration.connections[2])
  - mctp_assembler_scratch_v5_axi_read_egress.m_axi_rvalid <= m_axi_rvalid (integration.connections[3])
  - mctp_assembler_scratch_v5_apb_regfile.pready <= pready (integration.connections[4])
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
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_module.
SSOT item context: value=mctp_assembler_scratch_v5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: io_list

### RTL-0225: Implement output rule for FM_COMPLETE_MESSAGE: interrupt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.output_rules.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.output_rules.interrupt.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: name=interrupt; port=irq; expr=descriptor_publish; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.output_rules.interrupt
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - interrupt width matches SSOT value 1
  - interrupt RTL expression implements SSOT expression descriptor_publish
  - DUT port irq is the implementation/observation point for interrupt
  - interrupt is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.output_rules.interrupt

### RTL-0231: Implement precondition for FM_PACKET_DROP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v5_descriptor_queue in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: value=packet_drop_reason != DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0

### RTL-0232: Implement output for FM_PACKET_DROP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACKET_DROP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.outputs.output_0.
Owner: mctp_assembler_scratch_v5_descriptor_queue in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: value=debug_drop_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PACKET_DROP.outputs.output_0

### RTL-0235: Implement output rule for FM_PACKET_DROP: debug_drop_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse.
Owner: mctp_assembler_scratch_v5_descriptor_queue in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: name=debug_drop_pulse; port=debug_drop_pulse; expr=packet_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_descriptor_queue.sv
  - debug_drop_pulse width matches SSOT value 1
  - debug_drop_pulse RTL expression implements SSOT expression packet_drop_reason != DROP_NONE
  - DUT port debug_drop_pulse is the implementation/observation point for debug_drop_pulse
  - debug_drop_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse

### RTL-0399: Implement security item asset_0

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=assembled_mctp_payload_in_external_sram.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: security.assets.asset_0

### RTL-0401: Implement security item asset_2

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=packet_and_assembly_drop_counters.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: security.assets.asset_2

### RTL-0406: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: name=external_modules; value=["external_256b_sram"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0407: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: name=external_clocks; value=["axi_aclk", "pclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0408: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: name=external_resets; value=["axi_aresetn", "presetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0409: Implement integration item m_axi_awvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.m_axi_awvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.m_axi_awvalid.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: port=m_axi_awvalid; signal=m_axi_awvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_awvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
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
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: port=m_axi_wvalid; signal=m_axi_wvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_wvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
  - DUT port m_axi_wvalid is the implementation/observation point for m_axi_wvalid
- SSOT refs: integration.connections.m_axi_wvalid

### RTL-0411: Implement integration item pack_wr_valid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pack_wr_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pack_wr_valid.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: port=sram_wr_valid; signal=pack_wr_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pack_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
  - DUT port sram_wr_valid is the implementation/observation point for sram_wr_valid
- SSOT refs: integration.connections.pack_wr_valid

### RTL-0412: Implement integration item m_axi_rvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.m_axi_rvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.m_axi_rvalid.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: port=m_axi_rvalid; signal=m_axi_rvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.m_axi_rvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
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
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via integration.
SSOT item context: port=pready; signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
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
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=No inferred latches..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0415: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=No unresolved black boxes except external SRAM model in integration testbench..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0416: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=All sequential state has reset or documented initialization..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0417: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: value=No AXI ID ports are generated..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0418: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: name=frequency_mhz_min; value=250.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0419: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0420: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via top_fallback.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0431: Prove module mctp_assembler_scratch_v5 is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v5.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v5.module_equivalence.
Owner: mctp_assembler_scratch_v5 in rtl/mctp_assembler_scratch_v5.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v5.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v5.module_equivalence
