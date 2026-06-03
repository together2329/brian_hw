# RTL Authoring Packet: module__mctp_assembler_scratch_v5_param

- Kind: module
- Owner module: mctp_assembler_scratch_v5_param
- Owner file: rtl/mctp_assembler_scratch_v5_param.vh
- Task count: 25
- Required tasks: 25

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
- Owner refs: parameters

## Tasks

### RTL-0024: Implement parameter AXI_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_ADDR_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=AXI_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_ADDR_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.AXI_ADDR_WIDTH

### RTL-0025: Implement parameter AXI_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_DATA_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=AXI_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_DATA_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.AXI_DATA_WIDTH

### RTL-0026: Implement parameter AXI_STRB_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AXI_STRB_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AXI_STRB_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=AXI_STRB_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AXI_STRB_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.AXI_STRB_WIDTH

### RTL-0027: Implement parameter SRAM_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.SRAM_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SRAM_ADDR_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=SRAM_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SRAM_ADDR_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.SRAM_ADDR_WIDTH

### RTL-0028: Implement parameter SRAM_DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.SRAM_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SRAM_DATA_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=SRAM_DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SRAM_DATA_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.SRAM_DATA_WIDTH

### RTL-0029: Implement parameter CONTEXT_COUNT

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CONTEXT_COUNT
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CONTEXT_COUNT.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=CONTEXT_COUNT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CONTEXT_COUNT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.CONTEXT_COUNT

### RTL-0030: Implement parameter TLP_HEADER_SNAPSHOT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TLP_HEADER_SNAPSHOT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TLP_HEADER_SNAPSHOT_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=TLP_HEADER_SNAPSHOT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TLP_HEADER_SNAPSHOT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.TLP_HEADER_SNAPSHOT_BYTES

### RTL-0031: Implement parameter MIN_TRANSMISSION_UNIT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MIN_TRANSMISSION_UNIT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MIN_TRANSMISSION_UNIT_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=MIN_TRANSMISSION_UNIT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MIN_TRANSMISSION_UNIT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.MIN_TRANSMISSION_UNIT_BYTES

### RTL-0032: Implement parameter MAX_TRANSMISSION_UNIT_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TRANSMISSION_UNIT_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TRANSMISSION_UNIT_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=MAX_TRANSMISSION_UNIT_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TRANSMISSION_UNIT_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.MAX_TRANSMISSION_UNIT_BYTES

### RTL-0033: Implement parameter TRANSMISSION_UNIT_ALIGN_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TRANSMISSION_UNIT_ALIGN_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TRANSMISSION_UNIT_ALIGN_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=TRANSMISSION_UNIT_ALIGN_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TRANSMISSION_UNIT_ALIGN_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.TRANSMISSION_UNIT_ALIGN_BYTES

### RTL-0034: Implement parameter MAX_TLP_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TLP_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TLP_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=MAX_TLP_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TLP_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.MAX_TLP_BYTES

### RTL-0035: Implement parameter MAX_TLP_BEATS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_TLP_BEATS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_TLP_BEATS.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=MAX_TLP_BEATS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_TLP_BEATS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.MAX_TLP_BEATS

### RTL-0036: Implement parameter MAX_MESSAGE_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_MESSAGE_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_MESSAGE_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=MAX_MESSAGE_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_MESSAGE_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.MAX_MESSAGE_BYTES

### RTL-0037: Implement parameter BASELINE_MTU_BYTES

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BASELINE_MTU_BYTES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BASELINE_MTU_BYTES.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=BASELINE_MTU_BYTES.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BASELINE_MTU_BYTES
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.BASELINE_MTU_BYTES

### RTL-0038: Implement parameter DESCRIPTOR_FIFO_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DESCRIPTOR_FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DESCRIPTOR_FIFO_DEPTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=DESCRIPTOR_FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DESCRIPTOR_FIFO_DEPTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.DESCRIPTOR_FIFO_DEPTH

### RTL-0039: Implement parameter TIMEOUT_COUNTER_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TIMEOUT_COUNTER_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TIMEOUT_COUNTER_WIDTH.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=TIMEOUT_COUNTER_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TIMEOUT_COUNTER_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.TIMEOUT_COUNTER_WIDTH

### RTL-0040: Implement parameter STATE_IDLE

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STATE_IDLE
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STATE_IDLE.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=STATE_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STATE_IDLE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.STATE_IDLE

### RTL-0041: Implement parameter STATE_ASSEMBLING

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STATE_ASSEMBLING
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STATE_ASSEMBLING.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=STATE_ASSEMBLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STATE_ASSEMBLING
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.STATE_ASSEMBLING

### RTL-0042: Implement parameter STATE_ERROR

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STATE_ERROR
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STATE_ERROR.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=STATE_ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STATE_ERROR
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.STATE_ERROR

### RTL-0043: Implement parameter STATE_DONE_WAIT_DESCRIPTOR_POP

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STATE_DONE_WAIT_DESCRIPTOR_POP
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STATE_DONE_WAIT_DESCRIPTOR_POP.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=STATE_DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STATE_DONE_WAIT_DESCRIPTOR_POP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.STATE_DONE_WAIT_DESCRIPTOR_POP

### RTL-0044: Implement parameter RESP_OKAY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESP_OKAY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESP_OKAY.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=RESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESP_OKAY
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.RESP_OKAY

### RTL-0045: Implement parameter RESP_SLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESP_SLVERR
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESP_SLVERR.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=RESP_SLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESP_SLVERR
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.RESP_SLVERR

### RTL-0046: Implement parameter BRESP_OKAY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BRESP_OKAY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BRESP_OKAY.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=BRESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BRESP_OKAY
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.BRESP_OKAY

### RTL-0047: Implement parameter DROP_NONE

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DROP_NONE
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DROP_NONE.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DROP_NONE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.DROP_NONE

### RTL-0048: Implement parameter ZERO_256

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ZERO_256
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ZERO_256.
Owner: mctp_assembler_scratch_v5_param in rtl/mctp_assembler_scratch_v5_param.vh via parameters.
SSOT item context: name=ZERO_256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ZERO_256
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_param.vh
- SSOT refs: parameters.ZERO_256
