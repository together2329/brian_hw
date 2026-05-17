# RTL Authoring Packet: module__atcwdt200_regs__dataflow

- Kind: module
- Owner module: atcwdt200_regs
- Owner file: rtl/atcwdt200_regs.sv
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, dataflow.sinks.sinks_0, decomposition.units.apb_register_block, error_handling, function_model, function_model.transactions.apb_read, function_model.transactions.apb_write, function_model.transactions.write_unlock, registers, registers.register_list
- Module slice: 5/5 section=dataflow task_limit=48
- Slice rule: Owner module atcwdt200_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_regs.pclk <= pclk (integration.connections[0])
  - atcwdt200_regs.presetn <= presetn (integration.connections[1])

## Tasks

### RTL-0168: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=APB writes WEN magic to unlock a protected write..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0169: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=APB writes CR to configure enable, tick source, interrupt enable, reset enable, and timeout encodings..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0170: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=The watchdog counter advances on pclk cycles when CR.CLK selects pclk, or on synchronized extclk rising pulses when e....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0171: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=INTTIME timeout sets SR.INTZERO and asserts wdt_int when CR.INTEN is set..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0172: Implement dataflow sequence: sequence_4

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_4
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_4.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=RSTTIME timeout sets reset status, asserts wdt_rst when CR.RSTEN is set, and clears CR.EN..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_4
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_4

### RTL-0173: Implement dataflow sequence: sequence_5

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_5
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_5.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sequence.sequence_0.
SSOT item context: value=RES magic write restarts the watchdog counter and phase..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_5
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sequence.sequence_5

### RTL-0174: Implement dataflow sinks: sinks_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_0.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sinks.sinks_0.
SSOT item context: value=prdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_0
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sinks.sinks_0

### RTL-0175: Implement dataflow sinks: sinks_1

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sinks.sinks_0.
SSOT item context: value=wdt_int.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sinks.sinks_1

### RTL-0176: Implement dataflow sinks: sinks_2

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_2.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via dataflow.sinks.sinks_0.
SSOT item context: value=wdt_rst.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_2
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
- SSOT refs: dataflow.sinks.sinks_2
