# RTL Authoring Packet: module__dma_real_apb_cfg__dataflow

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
- Task count: 8
- Required tasks: 8

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
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 8/8 section=dataflow task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0350: Implement dataflow sequence: sequence_12

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_12
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_12.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.sequence.sequence_0.
SSOT item context: value=Channel asserts done pulse (1 hclk cycle), IRQ module latches sticky in pclk domain..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_12
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.sequence.sequence_12

### RTL-0351: Implement dataflow sequence: sequence_13

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_13
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_13.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.sequence.sequence_0.
SSOT item context: value=IRQ asserted if enabled..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_13
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.sequence.sequence_13

### RTL-0352: Implement dataflow ordering: ordering_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_0.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=Configuration (APB write in pclk) must cross CDC before hclk channel FSM reads it..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_0
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_0

### RTL-0353: Implement dataflow ordering: ordering_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_1.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=Arbiter grant must precede AHB address phase..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_1
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_1

### RTL-0354: Implement dataflow ordering: ordering_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_2.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=Read burst completion must precede write burst for same data..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_2
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_2

### RTL-0355: Implement dataflow ordering: ordering_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_3.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=Address update must precede next burst request..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_3
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_3

### RTL-0356: Implement dataflow ordering: ordering_4

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_4
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_4.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=Transfer completion (DONE) precedes done pulse observation..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_4
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_4

### RTL-0357: Implement dataflow ordering: ordering_5

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_5
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_5.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via dataflow.ordering.ordering_0.
SSOT item context: value=1KB boundary crossing starts new NONSEQ beat..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_5
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
- SSOT refs: dataflow.ordering.ordering_5
