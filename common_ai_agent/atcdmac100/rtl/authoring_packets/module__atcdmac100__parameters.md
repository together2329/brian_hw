# RTL Authoring Packet: module__atcdmac100__parameters

- Kind: module
- Owner module: atcdmac100
- Owner file: rtl/atcdmac100.sv
- Task count: 6
- Required tasks: 6

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
- Module slice: 2/7 section=parameters task_limit=48
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

### RTL-0022: Implement parameter ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ADDR_WIDTH.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ADDR_WIDTH
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.ADDR_WIDTH

### RTL-0023: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0024: Implement parameter DMA_CH_NUM

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DMA_CH_NUM
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DMA_CH_NUM.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=DMA_CH_NUM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DMA_CH_NUM
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.DMA_CH_NUM

### RTL-0025: Implement parameter REQ_ACK_NUM

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.REQ_ACK_NUM
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.REQ_ACK_NUM.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=REQ_ACK_NUM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.REQ_ACK_NUM
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.REQ_ACK_NUM

### RTL-0026: Implement parameter FIFO_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.FIFO_DEPTH.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.FIFO_DEPTH
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.FIFO_DEPTH

### RTL-0027: Implement parameter CHAIN_TRANSFER_SUPPORT

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CHAIN_TRANSFER_SUPPORT
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CHAIN_TRANSFER_SUPPORT.
Owner: atcdmac100 in rtl/atcdmac100.sv via top_fallback.
SSOT item context: name=CHAIN_TRANSFER_SUPPORT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CHAIN_TRANSFER_SUPPORT
  - Primary implementation evidence is in rtl/atcdmac100.sv
- SSOT refs: parameters.CHAIN_TRANSFER_SUPPORT
