# RTL Authoring Packet: module__atcdmac100__integration

- Kind: module
- Owner module: atcdmac100
- Owner file: rtl/atcdmac100.sv
- Task count: 32
- Required tasks: 32

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
- Owner refs: cycle_model, dataflow, fsm, function_model, integration, io_list, top_integration
- Module slice: 3/7 section=integration task_limit=48
- Slice rule: Owner module atcdmac100 is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])
- SSOT top IO contracts: 29

## Tasks

### RTL-0358: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: value=System AHB fabric grants hbusreq_mst through hgrant_mst..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0359: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: value=External low-speed devices drive dma_req and observe dma_ack..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0360: Implement integration item dependencie_2

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_2
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_2.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: value=Software programs channel register windows before setting ChnCtrl.Enable..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_2
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: integration.dependencies.dependencie_2

### RTL-0361: Implement integration item hclk

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hclk
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hclk.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hclk; signal=hclk.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hclk
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hclk is the implementation/observation point for hclk
- SSOT refs: integration.connections.hclk

### RTL-0362: Implement integration item RTL_TODO_2_quality_gates_rtl_gen

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.RTL_TODO_2_quality_gates_rtl_gen
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.RTL_TODO_2_quality_gates_rtl_gen.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hresetn; signal=RTL_TODO_2_quality_gates_rtl_gen.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.RTL_TODO_2_quality_gates_rtl_gen
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hresetn is the implementation/observation point for hresetn
- SSOT refs: integration.connections.RTL_TODO_2_quality_gates_rtl_gen

### RTL-0363: Implement integration item dma_int

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dma_int
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dma_int.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=dma_int; signal=dma_int.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dma_int
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port dma_int is the implementation/observation point for dma_int
- SSOT refs: integration.connections.dma_int

### RTL-0364: Implement integration item dma_req

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dma_req
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dma_req.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=dma_req; signal=dma_req.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dma_req
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port dma_req is the implementation/observation point for dma_req
- SSOT refs: integration.connections.dma_req

### RTL-0365: Implement integration item dma_ack

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.dma_ack
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.dma_ack.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=dma_ack; signal=dma_ack.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.dma_ack
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port dma_ack is the implementation/observation point for dma_ack
- SSOT refs: integration.connections.dma_ack

### RTL-0366: Implement integration item haddr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.haddr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.haddr.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=haddr; signal=haddr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.haddr
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port haddr is the implementation/observation point for haddr
- SSOT refs: integration.connections.haddr

### RTL-0367: Implement integration item htrans

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.htrans
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.htrans.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=htrans; signal=htrans.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.htrans
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port htrans is the implementation/observation point for htrans
- SSOT refs: integration.connections.htrans

### RTL-0368: Implement integration item hwrite

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hwrite
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hwrite.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hwrite; signal=hwrite.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hwrite
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hwrite is the implementation/observation point for hwrite
- SSOT refs: integration.connections.hwrite

### RTL-0369: Implement integration item hsize

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hsize
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hsize.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hsize; signal=hsize.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hsize
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hsize is the implementation/observation point for hsize
- SSOT refs: integration.connections.hsize

### RTL-0370: Implement integration item hburst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hburst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hburst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hburst; signal=hburst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hburst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hburst is the implementation/observation point for hburst
- SSOT refs: integration.connections.hburst

### RTL-0371: Implement integration item hwdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hwdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hwdata.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hwdata; signal=hwdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hwdata
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hwdata is the implementation/observation point for hwdata
- SSOT refs: integration.connections.hwdata

### RTL-0372: Implement integration item hsel

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hsel
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hsel.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hsel; signal=hsel.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hsel
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hsel is the implementation/observation point for hsel
- SSOT refs: integration.connections.hsel

### RTL-0373: Implement integration item hreadyin

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hreadyin
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hreadyin.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hreadyin; signal=hreadyin.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hreadyin
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hreadyin is the implementation/observation point for hreadyin
- SSOT refs: integration.connections.hreadyin

### RTL-0374: Implement integration item hrdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hrdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hrdata.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hrdata; signal=hrdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hrdata
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hrdata is the implementation/observation point for hrdata
- SSOT refs: integration.connections.hrdata

### RTL-0375: Implement integration item hresp

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hresp
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hresp.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hresp; signal=hresp.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hresp
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hresp is the implementation/observation point for hresp
- SSOT refs: integration.connections.hresp

### RTL-0376: Implement integration item hready

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hready
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hready.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hready; signal=hready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hready
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hready is the implementation/observation point for hready
- SSOT refs: integration.connections.hready

### RTL-0377: Implement integration item haddr_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.haddr_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.haddr_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=haddr_mst; signal=haddr_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.haddr_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port haddr_mst is the implementation/observation point for haddr_mst
- SSOT refs: integration.connections.haddr_mst

### RTL-0378: Implement integration item htrans_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.htrans_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.htrans_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=htrans_mst; signal=htrans_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.htrans_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port htrans_mst is the implementation/observation point for htrans_mst
- SSOT refs: integration.connections.htrans_mst

### RTL-0379: Implement integration item hwrite_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hwrite_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hwrite_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hwrite_mst; signal=hwrite_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hwrite_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hwrite_mst is the implementation/observation point for hwrite_mst
- SSOT refs: integration.connections.hwrite_mst

### RTL-0380: Implement integration item hsize_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hsize_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hsize_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hsize_mst; signal=hsize_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hsize_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hsize_mst is the implementation/observation point for hsize_mst
- SSOT refs: integration.connections.hsize_mst

### RTL-0381: Implement integration item hprot_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hprot_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hprot_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hprot_mst; signal=hprot_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hprot_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hprot_mst is the implementation/observation point for hprot_mst
- SSOT refs: integration.connections.hprot_mst

### RTL-0382: Implement integration item hlock_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hlock_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hlock_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hlock_mst; signal=hlock_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hlock_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hlock_mst is the implementation/observation point for hlock_mst
- SSOT refs: integration.connections.hlock_mst

### RTL-0383: Implement integration item hburst_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hburst_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hburst_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hburst_mst; signal=hburst_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hburst_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hburst_mst is the implementation/observation point for hburst_mst
- SSOT refs: integration.connections.hburst_mst

### RTL-0384: Implement integration item hwdata_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hwdata_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hwdata_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hwdata_mst; signal=hwdata_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hwdata_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hwdata_mst is the implementation/observation point for hwdata_mst
- SSOT refs: integration.connections.hwdata_mst

### RTL-0385: Implement integration item hrdata_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hrdata_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hrdata_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hrdata_mst; signal=hrdata_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hrdata_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hrdata_mst is the implementation/observation point for hrdata_mst
- SSOT refs: integration.connections.hrdata_mst

### RTL-0386: Implement integration item hresp_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hresp_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hresp_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hresp_mst; signal=hresp_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hresp_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hresp_mst is the implementation/observation point for hresp_mst
- SSOT refs: integration.connections.hresp_mst

### RTL-0387: Implement integration item hready_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hready_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hready_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hready_mst; signal=hready_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hready_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hready_mst is the implementation/observation point for hready_mst
- SSOT refs: integration.connections.hready_mst

### RTL-0388: Implement integration item hbusreq_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hbusreq_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hbusreq_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hbusreq_mst; signal=hbusreq_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hbusreq_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hbusreq_mst is the implementation/observation point for hbusreq_mst
- SSOT refs: integration.connections.hbusreq_mst

### RTL-0389: Implement integration item hgrant_mst

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.hgrant_mst
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.hgrant_mst.
Owner: atcdmac100 in rtl/atcdmac100.sv via integration.
SSOT item context: port=hgrant_mst; signal=hgrant_mst.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.hgrant_mst
  - Primary implementation evidence is in rtl/atcdmac100.sv
  - DUT port hgrant_mst is the implementation/observation point for hgrant_mst
- SSOT refs: integration.connections.hgrant_mst
