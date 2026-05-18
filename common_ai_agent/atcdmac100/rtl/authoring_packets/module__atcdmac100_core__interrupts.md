# RTL Authoring Packet: module__atcdmac100_core__interrupts

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 3
- Required tasks: 3

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 10/14 section=interrupts task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
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
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0256: Implement interrupt item source_0

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.source_0
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.source_0.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via interrupts.
SSOT item context: value=TC.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.source_0
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: interrupts.sources.source_0

### RTL-0257: Implement interrupt item source_1

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.source_1
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.source_1.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via interrupts.
SSOT item context: value=Abort.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.source_1
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: interrupts.sources.source_1

### RTL-0258: Implement interrupt item source_2

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.source_2
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.source_2.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via interrupts.
SSOT item context: value=Error.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.source_2
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
- SSOT refs: interrupts.sources.source_2
