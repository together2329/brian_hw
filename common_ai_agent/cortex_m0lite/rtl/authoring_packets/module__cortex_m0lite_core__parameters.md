# RTL Authoring Packet: module__cortex_m0lite_core__parameters

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 15
- Required tasks: 15

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 1/9 section=parameters task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0030: Implement parameter XLEN

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.XLEN
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.XLEN.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=XLEN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.XLEN
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.XLEN

### RTL-0031: Implement parameter RESET_PC

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_PC
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_PC.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=RESET_PC.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_PC
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.RESET_PC

### RTL-0032: Implement parameter TRAP_VECTOR

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.TRAP_VECTOR
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.TRAP_VECTOR.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=TRAP_VECTOR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.TRAP_VECTOR
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.TRAP_VECTOR

### RTL-0033: Implement parameter STACK_RESET

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.STACK_RESET
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.STACK_RESET.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=STACK_RESET.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.STACK_RESET
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.STACK_RESET

### RTL-0034: Implement parameter REG_COUNT

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.REG_COUNT
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.REG_COUNT.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=REG_COUNT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.REG_COUNT
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.REG_COUNT

### RTL-0035: Implement parameter AHB_ADDR_W

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_ADDR_W
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_ADDR_W.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_ADDR_W.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_ADDR_W
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_ADDR_W

### RTL-0036: Implement parameter AHB_DATA_W

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_DATA_W
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_DATA_W.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_DATA_W.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_DATA_W
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_DATA_W

### RTL-0037: Implement parameter CORE_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CORE_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CORE_FREQ_MHZ.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=CORE_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CORE_FREQ_MHZ
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.CORE_FREQ_MHZ

### RTL-0038: Implement parameter BUS_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.BUS_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.BUS_FREQ_MHZ.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=BUS_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.BUS_FREQ_MHZ
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.BUS_FREQ_MHZ

### RTL-0039: Implement parameter AHB_HTRANS_IDLE

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HTRANS_IDLE
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HTRANS_IDLE.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HTRANS_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HTRANS_IDLE
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HTRANS_IDLE

### RTL-0040: Implement parameter AHB_HTRANS_BUSY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HTRANS_BUSY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HTRANS_BUSY.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HTRANS_BUSY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HTRANS_BUSY
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HTRANS_BUSY

### RTL-0041: Implement parameter AHB_HTRANS_NONSEQ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HTRANS_NONSEQ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HTRANS_NONSEQ.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HTRANS_NONSEQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HTRANS_NONSEQ
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HTRANS_NONSEQ

### RTL-0042: Implement parameter AHB_HTRANS_SEQ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HTRANS_SEQ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HTRANS_SEQ.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HTRANS_SEQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HTRANS_SEQ
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HTRANS_SEQ

### RTL-0043: Implement parameter AHB_HSIZE_WORD

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HSIZE_WORD
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HSIZE_WORD.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HSIZE_WORD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HSIZE_WORD
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HSIZE_WORD

### RTL-0044: Implement parameter AHB_HBURST_SINGLE

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.AHB_HBURST_SINGLE
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.AHB_HBURST_SINGLE.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via parameters.
SSOT item context: name=AHB_HBURST_SINGLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.AHB_HBURST_SINGLE
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
- SSOT refs: parameters.AHB_HBURST_SINGLE
