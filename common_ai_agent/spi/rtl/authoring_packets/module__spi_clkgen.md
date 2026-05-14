# RTL Authoring Packet: module__spi_clkgen

- Kind: module
- Owner module: spi_clkgen
- Owner file: rtl/spi_clkgen.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.pipeline, parameters, parameters.PRESCALE_WIDTH, timing
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0119: Implement handshake rule: APB

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.APB
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.APB.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=APB.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.APB
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.APB appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.APB

### RTL-0120: Implement handshake rule: CTRL.start

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.CTRL_start
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.CTRL_start.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=CTRL.start.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.CTRL_start
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.CTRL_start appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.CTRL_start

### RTL-0121: Implement handshake rule: launch_gate

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.launch_gate
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.launch_gate.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=launch_gate.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.launch_gate
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.launch_gate appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.launch_gate

### RTL-0122: Implement handshake rule: sclk_o

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sclk_o
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sclk_o.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=sclk_o.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sclk_o
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.sclk_o appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sclk_o

### RTL-0123: Implement handshake rule: sample_edge

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.sample_edge
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.sample_edge.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.handshake_rules.
SSOT item context: signal=sample_edge.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.sample_edge
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.handshake_rules.sample_edge appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.sample_edge

### RTL-0124: Implement pipeline stage: S0_APB_CFG

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S0_APB_CFG
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S0_APB_CFG.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S0_APB_CFG; action=Program mode/prescale/CS and push TX words; cycle=t.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S0_APB_CFG
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S0_APB_CFG timing uses SSOT cycle/latency t
  - cycle_model.pipeline.S0_APB_CFG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S0_APB_CFG

### RTL-0125: Implement pipeline stage: S1_LAUNCH_CHECK

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S1_LAUNCH_CHECK
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S1_LAUNCH_CHECK.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S1_LAUNCH_CHECK; action=Evaluate launch preconditions and latch frame context; cycle=t+0..t+1.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S1_LAUNCH_CHECK
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S1_LAUNCH_CHECK timing uses SSOT cycle/latency t+0..t+1
  - cycle_model.pipeline.S1_LAUNCH_CHECK appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S1_LAUNCH_CHECK

### RTL-0126: Implement pipeline stage: S2_ASSERT_CS

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S2_ASSERT_CS
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S2_ASSERT_CS.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S2_ASSERT_CS; action=Drive selected chip select active-low; cycle=next.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S2_ASSERT_CS
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S2_ASSERT_CS timing uses SSOT cycle/latency next
  - cycle_model.pipeline.S2_ASSERT_CS appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S2_ASSERT_CS

### RTL-0128: Implement pipeline stage: S4_SAMPLE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S4_SAMPLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S4_SAMPLE.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S4_SAMPLE; action=Sample MISO/loopback bit and advance bit_index; cycle=repeating.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S4_SAMPLE
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S4_SAMPLE timing uses SSOT cycle/latency repeating
  - cycle_model.pipeline.S4_SAMPLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S4_SAMPLE

### RTL-0129: Implement pipeline stage: S5_COMPLETE

- Priority: high
- Required: True
- Status: open
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.S5_COMPLETE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.S5_COMPLETE.
Owner: spi_clkgen in rtl/spi_clkgen.sv via cycle_model.pipeline.
SSOT item context: stage=S5_COMPLETE; action=Push RX word if possible, update done/errors/pending, manage CS hold/deassert; cycle=terminal.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.S5_COMPLETE
  - Primary implementation evidence is in rtl/spi_clkgen.sv
  - cycle_model.pipeline.S5_COMPLETE timing uses SSOT cycle/latency terminal
  - cycle_model.pipeline.S5_COMPLETE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.S5_COMPLETE

### RTL-0245: Prove module spi_clkgen is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.spi_clkgen.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_clkgen.module_equivalence.
Owner: spi_clkgen in rtl/spi_clkgen.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_clkgen.module_equivalence
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: sub_modules.spi_clkgen.module_equivalence

### RTL-0029: Implement parameter APB_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.APB_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_ADDR_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=APB_ADDR_WIDTH.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_ADDR_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.APB_ADDR_WIDTH

### RTL-0030: Implement parameter APB_DATA_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.APB_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.APB_DATA_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=APB_DATA_WIDTH.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.APB_DATA_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.APB_DATA_WIDTH

### RTL-0031: Implement parameter DATA_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DATA_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=DATA_WIDTH.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DATA_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.DATA_WIDTH

### RTL-0032: Implement parameter FIFO_DEPTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.FIFO_DEPTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=FIFO_DEPTH.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.FIFO_DEPTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.FIFO_DEPTH

### RTL-0033: Implement parameter NUM_CS

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.NUM_CS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.NUM_CS.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=NUM_CS.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.NUM_CS
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.NUM_CS

### RTL-0034: Implement parameter PRESCALE_WIDTH

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.PRESCALE_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PRESCALE_WIDTH.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.PRESCALE_WIDTH.
SSOT item context: name=PRESCALE_WIDTH.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PRESCALE_WIDTH
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.PRESCALE_WIDTH

### RTL-0035: Implement parameter CPOL_RESET

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.CPOL_RESET
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CPOL_RESET.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=CPOL_RESET.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CPOL_RESET
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.CPOL_RESET

### RTL-0036: Implement parameter CPHA_RESET

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.CPHA_RESET
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.CPHA_RESET.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=CPHA_RESET.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.CPHA_RESET
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.CPHA_RESET

### RTL-0037: Implement parameter LSB_FIRST_RESET

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.LSB_FIRST_RESET
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.LSB_FIRST_RESET.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=LSB_FIRST_RESET.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.LSB_FIRST_RESET
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.LSB_FIRST_RESET

### RTL-0038: Implement parameter PCLK_FREQ_MHZ

- Priority: normal
- Required: True
- Status: open
- Category: parameters.item
- Source ref: parameters.PCLK_FREQ_MHZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.PCLK_FREQ_MHZ.
Owner: spi_clkgen in rtl/spi_clkgen.sv via parameters.
SSOT item context: name=PCLK_FREQ_MHZ.
- Current reason: Owner RTL file is missing: rtl/spi_clkgen.sv.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.PCLK_FREQ_MHZ
  - Primary implementation evidence is in rtl/spi_clkgen.sv
- SSOT refs: parameters.PCLK_FREQ_MHZ
