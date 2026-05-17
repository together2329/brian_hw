# RTL Authoring Packet: module__pl330realverify__parameters

- Kind: module
- Owner module: pl330realverify
- Owner file: rtl/pl330realverify.sv
- Task count: 10
- Required tasks: 10

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
- Module slice: 2/9 section=parameters task_limit=48
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

### RTL-0032: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0033: Implement parameter ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ADDR_WIDTH.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ADDR_WIDTH
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.ADDR_WIDTH

### RTL-0034: Implement parameter ID_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.ID_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.ID_WIDTH.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=ID_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.ID_WIDTH
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.ID_WIDTH

### RTL-0035: Implement parameter NUM_CHANNELS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.NUM_CHANNELS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.NUM_CHANNELS.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=NUM_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.NUM_CHANNELS
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.NUM_CHANNELS

### RTL-0036: Implement parameter NUM_EVENTS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.NUM_EVENTS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.NUM_EVENTS.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=NUM_EVENTS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.NUM_EVENTS
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.NUM_EVENTS

### RTL-0037: Implement parameter REG_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.REG_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.REG_ADDR_WIDTH.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=REG_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.REG_ADDR_WIDTH
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.REG_ADDR_WIDTH

### RTL-0038: Implement parameter MAX_BURST_LEN

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MAX_BURST_LEN
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MAX_BURST_LEN.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=MAX_BURST_LEN.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MAX_BURST_LEN
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.MAX_BURST_LEN

### RTL-0039: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0040: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.RESET_POLARITY

### RTL-0041: Implement parameter SUPPORT_UNALIGNED

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.SUPPORT_UNALIGNED
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SUPPORT_UNALIGNED.
Owner: pl330realverify in rtl/pl330realverify.sv via parameters.
SSOT item context: name=SUPPORT_UNALIGNED.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SUPPORT_UNALIGNED
  - Primary implementation evidence is in rtl/pl330realverify.sv
- SSOT refs: parameters.SUPPORT_UNALIGNED
