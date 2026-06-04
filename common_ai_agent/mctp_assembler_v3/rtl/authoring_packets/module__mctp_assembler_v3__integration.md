# RTL Authoring Packet: module__mctp_assembler_v3__integration

- Kind: module
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 11
- Required tasks: 11

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, function_model, function_model.transactions, integration, integration.connections, io_list, io_list.interfaces, top_module
- Module slice: 4/9 section=integration task_limit=48
- Slice rule: Owner module mctp_assembler_v3 is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])
  - mctp_assembler_v3_cdc_sync.evt_fatal_internal_error_a <= 1'b0 (integration.connections[7])
- SSOT top IO contracts: 51

## Tasks

### RTL-0455: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.
SSOT item context: name=external_modules; value=["payload_sram (256-bit, byte-strobed)"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0456: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.
SSOT item context: name=external_clocks; value=["axi_aclk", "pclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0457: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.
SSOT item context: name=external_resets; value=["axi_aresetn", "presetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0458: Implement integration item axi_aclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.axi_aclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.axi_aclk.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=axi_aclk; signal=axi_aclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.axi_aclk
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port axi_aclk is the implementation/observation point for axi_aclk
- SSOT refs: integration.connections.axi_aclk

### RTL-0459: Implement integration item axi_aresetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.axi_aresetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.axi_aresetn.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=axi_aresetn; signal=axi_aresetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.axi_aresetn
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port axi_aresetn is the implementation/observation point for axi_aresetn
- SSOT refs: integration.connections.axi_aresetn

### RTL-0460: Implement integration item pclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pclk.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=pclk; signal=pclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pclk
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port pclk is the implementation/observation point for pclk
- SSOT refs: integration.connections.pclk

### RTL-0461: Implement integration item presetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.presetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.presetn.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=presetn; signal=presetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.presetn
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port presetn is the implementation/observation point for presetn
- SSOT refs: integration.connections.presetn

### RTL-0462: Implement integration item irq

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.irq
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=irq_o; signal=irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.irq

### RTL-0463: Implement integration item sram_wr_valid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.sram_wr_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.sram_wr_valid.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=sram_wr_valid_o; signal=sram_wr_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port sram_wr_valid_o is the implementation/observation point for sram_wr_valid_o
- SSOT refs: integration.connections.sram_wr_valid

### RTL-0464: Implement integration item last_drop_class

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.last_drop_class
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.last_drop_class.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=drop_class_o; signal=last_drop_class.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.last_drop_class
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port drop_class_o is the implementation/observation point for drop_class_o
- SSOT refs: integration.connections.last_drop_class

### RTL-0465: Implement integration item 1'b0

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.item_1_b0
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.item_1_b0.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via integration.connections.
SSOT item context: port=evt_fatal_internal_error_a; signal=1'b0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.item_1_b0
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - DUT port evt_fatal_internal_error_a is the implementation/observation point for evt_fatal_internal_error_a
- SSOT refs: integration.connections.item_1_b0
