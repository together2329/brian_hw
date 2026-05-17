# RTL Authoring Packet: module__dma_real_channel__parameters

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 1/9 section=parameters task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0029: Implement parameter ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ADDR_WIDTH.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ADDR_WIDTH
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.ADDR_WIDTH

### RTL-0030: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0031: Implement parameter N_CHANNELS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.N_CHANNELS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.N_CHANNELS.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=N_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.N_CHANNELS
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.N_CHANNELS

### RTL-0032: Implement parameter BURST_MAX

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BURST_MAX
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BURST_MAX.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=BURST_MAX.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BURST_MAX
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.BURST_MAX

### RTL-0033: Implement parameter FIFO_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.FIFO_DEPTH.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.FIFO_DEPTH
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.FIFO_DEPTH

### RTL-0034: Implement parameter TIMEOUT_DEFAULT

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TIMEOUT_DEFAULT
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TIMEOUT_DEFAULT.
Owner: dma_real_channel in rtl/dma_real_channel.sv via parameters.
SSOT item context: name=TIMEOUT_DEFAULT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TIMEOUT_DEFAULT
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: parameters.TIMEOUT_DEFAULT
