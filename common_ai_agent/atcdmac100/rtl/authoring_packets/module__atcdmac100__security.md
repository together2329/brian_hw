# RTL Authoring Packet: module__atcdmac100__security

- Kind: module
- Owner module: atcdmac100
- Owner file: rtl/atcdmac100.sv
- Task count: 4
- Required tasks: 4

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: integration, io_list
- Module slice: 4/6 section=security task_limit=48
- Slice rule: Owner module atcdmac100 is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100.<port> <= <signal> (sub_modules[1].connections)
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= hresetn (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
- SSOT top IO contracts: 29

## Tasks

### RTL-0285: Implement security item asset_0

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_0
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_0.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: value=register programming state.
- Current reason: Owner RTL file is missing: rtl/atcdmac100.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_0
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: security.assets.asset_0

### RTL-0286: Implement security item asset_1

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: value=DMA source/destination addresses.
- Current reason: Owner RTL file is missing: rtl/atcdmac100.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: security.assets.asset_1

### RTL-0287: Implement security item asset_2

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_2
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_2.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: value=interrupt status.
- Current reason: Owner RTL file is missing: rtl/atcdmac100.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_2
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: security.assets.asset_2

### RTL-0288: Implement security item asset_3

- Priority: high
- Required: True
- Status: open
- Category: security.assets
- Source ref: security.assets.asset_3
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_3.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: value=AHB master access authority.
- Current reason: Owner RTL file is missing: rtl/atcdmac100.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_3
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: security.assets.asset_3
