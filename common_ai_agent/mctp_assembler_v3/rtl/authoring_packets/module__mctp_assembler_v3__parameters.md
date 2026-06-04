# RTL Authoring Packet: module__mctp_assembler_v3__parameters

- Kind: module
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 18
- Required tasks: 18

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
- Module slice: 3/9 section=parameters task_limit=48
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

### RTL-0029: Implement parameter BRESP_OKAY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BRESP_OKAY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BRESP_OKAY.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=BRESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BRESP_OKAY
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.BRESP_OKAY

### RTL-0030: Implement parameter RRESP_OKAY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RRESP_OKAY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RRESP_OKAY.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=RRESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RRESP_OKAY
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.RRESP_OKAY

### RTL-0031: Implement parameter RRESP_SLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RRESP_SLVERR
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RRESP_SLVERR.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=RRESP_SLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RRESP_SLVERR
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.RRESP_SLVERR

### RTL-0032: Implement parameter INCR

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.INCR
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.INCR.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=INCR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.INCR
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.INCR

### RTL-0033: Implement parameter ASSEMBLING

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ASSEMBLING
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ASSEMBLING.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=ASSEMBLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ASSEMBLING
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.ASSEMBLING

### RTL-0035: Implement parameter AXI_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_ADDR_WIDTH.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=AXI_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_ADDR_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.AXI_ADDR_WIDTH

### RTL-0036: Implement parameter AXI_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_DATA_WIDTH.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=AXI_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_DATA_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.AXI_DATA_WIDTH

### RTL-0037: Implement parameter AXI_STRB_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_STRB_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_STRB_WIDTH.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=AXI_STRB_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_STRB_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.AXI_STRB_WIDTH

### RTL-0041: Implement parameter TLP_HEADER_SNAPSHOT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TLP_HEADER_SNAPSHOT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TLP_HEADER_SNAPSHOT_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=TLP_HEADER_SNAPSHOT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TLP_HEADER_SNAPSHOT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.TLP_HEADER_SNAPSHOT_BYTES

### RTL-0042: Implement parameter MIN_TRANSMISSION_UNIT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MIN_TRANSMISSION_UNIT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MIN_TRANSMISSION_UNIT_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=MIN_TRANSMISSION_UNIT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MIN_TRANSMISSION_UNIT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.MIN_TRANSMISSION_UNIT_BYTES

### RTL-0043: Implement parameter MAX_TRANSMISSION_UNIT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TRANSMISSION_UNIT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TRANSMISSION_UNIT_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=MAX_TRANSMISSION_UNIT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TRANSMISSION_UNIT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.MAX_TRANSMISSION_UNIT_BYTES

### RTL-0044: Implement parameter TRANSMISSION_UNIT_ALIGN_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TRANSMISSION_UNIT_ALIGN_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TRANSMISSION_UNIT_ALIGN_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=TRANSMISSION_UNIT_ALIGN_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TRANSMISSION_UNIT_ALIGN_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.TRANSMISSION_UNIT_ALIGN_BYTES

### RTL-0045: Implement parameter MAX_TLP_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TLP_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TLP_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=MAX_TLP_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TLP_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.MAX_TLP_BYTES

### RTL-0046: Implement parameter MAX_TLP_BEATS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TLP_BEATS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TLP_BEATS.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=MAX_TLP_BEATS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TLP_BEATS
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.MAX_TLP_BEATS

### RTL-0047: Implement parameter MAX_MESSAGE_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_MESSAGE_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_MESSAGE_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=MAX_MESSAGE_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_MESSAGE_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.MAX_MESSAGE_BYTES

### RTL-0048: Implement parameter BASELINE_MTU_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BASELINE_MTU_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BASELINE_MTU_BYTES.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=BASELINE_MTU_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BASELINE_MTU_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.BASELINE_MTU_BYTES

### RTL-0050: Implement parameter TIMEOUT_COUNTER_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TIMEOUT_COUNTER_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TIMEOUT_COUNTER_WIDTH.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=TIMEOUT_COUNTER_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TIMEOUT_COUNTER_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.TIMEOUT_COUNTER_WIDTH

### RTL-0051: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via top_fallback.
SSOT item context: name=RESET_POLARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
- SSOT refs: parameters.RESET_POLARITY
