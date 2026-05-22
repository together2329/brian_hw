# RTL Authoring Packet: module__pl330realverify__integration

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
- Task count: 27
- Required tasks: 27

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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 3/9 section=integration task_limit=48
- Slice rule: Owner module pl330realverify is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])
- SSOT top IO contracts: 46

## Tasks

### RTL-0336: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0337: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: name=external_clocks; value=["dmaclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0338: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: name=external_resets; value=["dmacresetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0339: Implement integration item external_protocols

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_protocols
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_protocols.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: name=external_protocols; value=["APB4", "AXI4"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_protocols
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: integration.dependencies.external_protocols

### RTL-0340: Implement integration item dmaclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dmaclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dmaclk.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=clk_i; signal=dmaclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dmaclk
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.dmaclk

### RTL-0341: Implement integration item dmacresetn

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dmacresetn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dmacresetn.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=rst_ni; signal=dmacresetn.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dmacresetn
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.dmacresetn

### RTL-0342: Implement integration item paddr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.paddr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.paddr.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=paddr_i; signal=paddr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.paddr
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port paddr_i is the implementation/observation point for paddr_i
- SSOT refs: integration.connections.paddr

### RTL-0343: Implement integration item psel

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.psel
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.psel.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=psel_i; signal=psel.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.psel
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port psel_i is the implementation/observation point for psel_i
- SSOT refs: integration.connections.psel

### RTL-0344: Implement integration item penable

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.penable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.penable.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=penable_i; signal=penable.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.penable
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port penable_i is the implementation/observation point for penable_i
- SSOT refs: integration.connections.penable

### RTL-0345: Implement integration item pwrite

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pwrite
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwrite.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=pwrite_i; signal=pwrite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwrite
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port pwrite_i is the implementation/observation point for pwrite_i
- SSOT refs: integration.connections.pwrite

### RTL-0346: Implement integration item pwdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pwdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pwdata.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=pwdata_i; signal=pwdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pwdata
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port pwdata_i is the implementation/observation point for pwdata_i
- SSOT refs: integration.connections.pwdata

### RTL-0347: Implement integration item pstrb

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pstrb
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pstrb.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=pstrb_i; signal=pstrb.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pstrb
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port pstrb_i is the implementation/observation point for pstrb_i
- SSOT refs: integration.connections.pstrb

### RTL-0348: Implement integration item prdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.prdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.prdata.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=prdata_o; signal=prdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.prdata
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port prdata_o is the implementation/observation point for prdata_o
- SSOT refs: integration.connections.prdata

### RTL-0349: Implement integration item pready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pready.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=pready_o; signal=pready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pready
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port pready_o is the implementation/observation point for pready_o
- SSOT refs: integration.connections.pready

### RTL-0350: Implement integration item pslverr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.pslverr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pslverr.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=pslverr_o; signal=pslverr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pslverr
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port pslverr_o is the implementation/observation point for pslverr_o
- SSOT refs: integration.connections.pslverr

### RTL-0351: Implement integration item channel_state

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.channel_state
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.channel_state.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=state_o; signal=channel_state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.channel_state
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port state_o is the implementation/observation point for state_o
- SSOT refs: integration.connections.channel_state

### RTL-0352: Implement integration item arvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.arvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.arvalid.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=arvalid_o; signal=arvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.arvalid
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port arvalid_o is the implementation/observation point for arvalid_o
- SSOT refs: integration.connections.arvalid

### RTL-0353: Implement integration item arready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.arready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.arready.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=arready_i; signal=arready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.arready
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port arready_i is the implementation/observation point for arready_i
- SSOT refs: integration.connections.arready

### RTL-0354: Implement integration item rvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rvalid.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=rvalid_i; signal=rvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rvalid
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port rvalid_i is the implementation/observation point for rvalid_i
- SSOT refs: integration.connections.rvalid

### RTL-0355: Implement integration item rready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rready.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=rready_o; signal=rready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rready
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port rready_o is the implementation/observation point for rready_o
- SSOT refs: integration.connections.rready

### RTL-0356: Implement integration item awvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.awvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.awvalid.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=awvalid_o; signal=awvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.awvalid
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port awvalid_o is the implementation/observation point for awvalid_o
- SSOT refs: integration.connections.awvalid

### RTL-0357: Implement integration item wvalid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.wvalid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.wvalid.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=wvalid_o; signal=wvalid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.wvalid
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port wvalid_o is the implementation/observation point for wvalid_o
- SSOT refs: integration.connections.wvalid

### RTL-0358: Implement integration item bready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.bready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.bready.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=bready_o; signal=bready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.bready
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port bready_o is the implementation/observation point for bready_o
- SSOT refs: integration.connections.bready

### RTL-0359: Implement integration item rdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.rdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rdata.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=rd_data_i; signal=rdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rdata
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port rd_data_i is the implementation/observation point for rd_data_i
- SSOT refs: integration.connections.rdata

### RTL-0360: Implement integration item wdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.wdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.wdata.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=wr_data_o; signal=wdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.wdata
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port wr_data_o is the implementation/observation point for wr_data_o
- SSOT refs: integration.connections.wdata

### RTL-0361: Implement integration item peripheral_events

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.peripheral_events
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.peripheral_events.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=peripheral_events_i; signal=peripheral_events.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.peripheral_events
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port peripheral_events_i is the implementation/observation point for peripheral_events_i
- SSOT refs: integration.connections.peripheral_events

### RTL-0362: Implement integration item dmac_irq

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dmac_irq
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dmac_irq.
Owner: pl330realverify in rtl/pl330realverify.sv via integration.
SSOT item context: port=irq_o; signal=dmac_irq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dmac_irq
  - Primary implementation evidence is in rtl/pl330realverify.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.dmac_irq
