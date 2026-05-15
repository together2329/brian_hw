# RTL Authoring Packet: module__fifo_sync__integration

- Kind: module
- Owner module: fifo_sync
- Owner file: rtl/fifo_sync.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 21
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 2/9 section=integration task_limit=48
- Slice rule: Owner module fifo_sync is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_ptrs.clk_i <= PCLK (integration.connections[0])
  - fifo_sync_ptrs.rst_ni <= PRESETn (integration.connections[1])
  - fifo_sync_mem.clk_i <= PCLK (integration.connections[2])
  - fifo_sync_mem.wr_en_i <= push_accepted (integration.connections[3])
  - fifo_sync_mem.wr_addr_i <= wr_ptr (integration.connections[4])
  - fifo_sync_mem.wr_data_i <= wr_data_i (integration.connections[5])
  - fifo_sync_mem.rd_addr_i <= rd_ptr (integration.connections[6])
  - fifo_sync_mem.rd_data_o <= mem_rd_data (integration.connections[7])
  - fifo_sync_flags.count_i <= count (integration.connections[8])
  - fifo_sync_flags.full_o <= full_o (integration.connections[9])
  - fifo_sync_flags.empty_o <= empty_o (integration.connections[10])
  - fifo_sync_flags.almost_full_o <= almost_full_o (integration.connections[11])
- SSOT top IO contracts: 20

## Tasks

### RTL-0217: Implement integration item external_modules

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0218: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0219: Implement integration item external_resets

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/fifo_sync.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0220: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0221: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0222: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0223: Implement integration item push_accepted

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.push_accepted
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.push_accepted.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=wr_en_i; signal=push_accepted.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.push_accepted
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port wr_en_i is the implementation/observation point for wr_en_i
- SSOT refs: integration.connections.push_accepted

### RTL-0224: Implement integration item wr_ptr

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.wr_ptr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.wr_ptr.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=wr_addr_i; signal=wr_ptr.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.wr_ptr
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port wr_addr_i is the implementation/observation point for wr_addr_i
- SSOT refs: integration.connections.wr_ptr

### RTL-0225: Implement integration item wr_data_i

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.wr_data_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.wr_data_i.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=wr_data_i; signal=wr_data_i.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.wr_data_i
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port wr_data_i is the implementation/observation point for wr_data_i
- SSOT refs: integration.connections.wr_data_i

### RTL-0226: Implement integration item rd_ptr

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.rd_ptr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rd_ptr.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=rd_addr_i; signal=rd_ptr.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rd_ptr
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port rd_addr_i is the implementation/observation point for rd_addr_i
- SSOT refs: integration.connections.rd_ptr

### RTL-0227: Implement integration item mem_rd_data

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.mem_rd_data
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.mem_rd_data.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=rd_data_o; signal=mem_rd_data.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.mem_rd_data
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port rd_data_o is the implementation/observation point for rd_data_o
- SSOT refs: integration.connections.mem_rd_data

### RTL-0228: Implement integration item count

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.count
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.count.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=count_i; signal=count.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.count
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port count_i is the implementation/observation point for count_i
- SSOT refs: integration.connections.count

### RTL-0229: Implement integration item full_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.full_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.full_o.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=full_o; signal=full_o.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.full_o
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port full_o is the implementation/observation point for full_o
- SSOT refs: integration.connections.full_o

### RTL-0230: Implement integration item empty_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.empty_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.empty_o.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=empty_o; signal=empty_o.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.empty_o
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port empty_o is the implementation/observation point for empty_o
- SSOT refs: integration.connections.empty_o

### RTL-0231: Implement integration item almost_full_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.almost_full_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.almost_full_o.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=almost_full_o; signal=almost_full_o.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.almost_full_o
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port almost_full_o is the implementation/observation point for almost_full_o
- SSOT refs: integration.connections.almost_full_o

### RTL-0232: Implement integration item almost_empty_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.almost_empty_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.almost_empty_o.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=almost_empty_o; signal=almost_empty_o.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.almost_empty_o
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port almost_empty_o is the implementation/observation point for almost_empty_o
- SSOT refs: integration.connections.almost_empty_o

### RTL-0233: Implement integration item mem_rd_data

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.mem_rd_data
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.mem_rd_data.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=din_i; signal=mem_rd_data.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.mem_rd_data
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port din_i is the implementation/observation point for din_i
- SSOT refs: integration.connections.mem_rd_data

### RTL-0234: Implement integration item pop_accepted

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pop_accepted
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pop_accepted.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=load_i; signal=pop_accepted.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pop_accepted
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port load_i is the implementation/observation point for load_i
- SSOT refs: integration.connections.pop_accepted

### RTL-0235: Implement integration item rd_data_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.rd_data_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.rd_data_o.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=dout_o; signal=rd_data_o.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.rd_data_o
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port dout_o is the implementation/observation point for dout_o
- SSOT refs: integration.connections.rd_data_o

### RTL-0236: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0237: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: fifo_sync in rtl/fifo_sync.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/fifo_sync.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/fifo_sync.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn
