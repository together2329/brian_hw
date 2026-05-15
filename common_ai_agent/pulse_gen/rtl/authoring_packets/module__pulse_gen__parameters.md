# RTL Authoring Packet: module__pulse_gen__parameters

- Kind: module
- Owner module: pulse_gen
- Owner file: rtl/pulse_gen.sv
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
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 3/9 section=parameters task_limit=48
- Slice rule: Owner module pulse_gen is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen.PRDATA <= pulse_gen_regs.PRDATA (integration.connections[7])
  - pulse_gen.PREADY <= 1'b1 (zero-wait-state) (integration.connections[8])
  - pulse_gen.PSLVERR <= pulse_gen_regs.PSLVERR (integration.connections[9])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0023: Implement parameter PULSE_WIDTH_CYCLES

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.PULSE_WIDTH_CYCLES
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PULSE_WIDTH_CYCLES.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=PULSE_WIDTH_CYCLES.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PULSE_WIDTH_CYCLES
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.PULSE_WIDTH_CYCLES

### RTL-0024: Implement parameter PULSE_POLARITY

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.PULSE_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PULSE_POLARITY.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=PULSE_POLARITY.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PULSE_POLARITY
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.PULSE_POLARITY

### RTL-0025: Implement parameter PULSE_OUT_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.PULSE_OUT_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PULSE_OUT_WIDTH.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=PULSE_OUT_WIDTH.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PULSE_OUT_WIDTH
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.PULSE_OUT_WIDTH

### RTL-0026: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.APB_ADDR_WIDTH

### RTL-0027: Implement parameter CLOCK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.CLOCK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CLOCK_FREQ_MHZ.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=CLOCK_FREQ_MHZ.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CLOCK_FREQ_MHZ
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.CLOCK_FREQ_MHZ

### RTL-0028: Implement parameter RESET_POLARITY

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.RESET_POLARITY
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.RESET_POLARITY.
Owner: pulse_gen in rtl/pulse_gen.sv via parameters.
SSOT item context: name=RESET_POLARITY.
- Current reason: Owner RTL file is missing: rtl/pulse_gen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.RESET_POLARITY
  - Primary implementation evidence is in rtl/pulse_gen.sv
- SSOT refs: parameters.RESET_POLARITY
