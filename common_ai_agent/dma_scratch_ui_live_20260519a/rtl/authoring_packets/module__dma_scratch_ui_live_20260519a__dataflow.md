# RTL Authoring Packet: module__dma_scratch_ui_live_20260519a__dataflow

- Kind: module
- Owner module: dma_scratch_ui_live_20260519a
- Owner file: rtl/dma_scratch_ui_live_20260519a.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 15/15 section=dataflow task_limit=48
- Slice rule: Owner module dma_scratch_ui_live_20260519a is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 36

## Tasks

### RTL-0190: Implement dataflow source: source_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.source
- Source ref: dataflow.source.source_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.source.source_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=declared io_list request/control interfaces.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.source.source_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.source.source_0

### RTL-0191: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=accept legal work under cycle_model handshake or command rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0192: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=evaluate function_model transaction and declared feature behavior.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0193: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=update only declared architectural state/status/events.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0194: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=publish response, output, interrupt, or debug observability event.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0195: Implement dataflow sinks: sinks_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=declared outputs.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sinks.sinks_0

### RTL-0196: Implement dataflow sinks: sinks_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_1.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=status/debug observability.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_1
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sinks.sinks_1

### RTL-0197: Implement dataflow sinks: sinks_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sinks
- Source ref: dataflow.sinks.sinks_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sinks.sinks_2.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=register reads if registers exist.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sinks.sinks_2
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.sinks.sinks_2

### RTL-0198: Implement dataflow ordering: ordering_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.ordering
- Source ref: dataflow.ordering.ordering_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.ordering.ordering_0.
Owner: dma_scratch_ui_live_20260519a in rtl/dma_scratch_ui_live_20260519a.sv via dataflow.
SSOT item context: value=Externally visible ordering follows cycle_model.ordering unless the SSOT explicitly approves reordering..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.ordering.ordering_0
  - Primary implementation evidence is in rtl/dma_scratch_ui_live_20260519a.sv
- SSOT refs: dataflow.ordering.ordering_0
