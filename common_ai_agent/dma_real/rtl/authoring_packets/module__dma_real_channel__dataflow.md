# RTL Authoring Packet: module__dma_real_channel__dataflow

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
- Task count: 12
- Required tasks: 12

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 9/9 section=dataflow task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0338: Implement dataflow sequence: sequence_0

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_0
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Software configures channel registers via APB in pclk domain (SRC, DST, LEN, STRIDE, CTRL)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_0

### RTL-0339: Implement dataflow sequence: sequence_1

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_1
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=APB config written to CDC async FIFO for crossing to hclk domain..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_1

### RTL-0340: Implement dataflow sequence: sequence_2

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_2
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Software sets CTRL.ch_start to initiate transfer..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_2

### RTL-0341: Implement dataflow sequence: sequence_3

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_3
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Channel FSM (hclk) transitions IDLE to CFG, latches config from CDC bridge..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_3

### RTL-0342: Implement dataflow sequence: sequence_4

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_4
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Channel requests AHB bus via arbiter (hclk)..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_4

### RTL-0343: Implement dataflow sequence: sequence_5

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_5
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_5.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Arbiter grants bus round-robin among active channels..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_5
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_5

### RTL-0344: Implement dataflow sequence: sequence_6

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_6
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_6.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=AHB master drives read burst from source address into pointer-based FIFO..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_6
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_6

### RTL-0345: Implement dataflow sequence: sequence_7

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_7
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_7.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=AHB master drives write burst from FIFO to destination address..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_7
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_7

### RTL-0346: Implement dataflow sequence: sequence_8

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_8
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_8.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Addresses increment by CHx_STRIDE per beat (default 4)..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_8
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_8

### RTL-0347: Implement dataflow sequence: sequence_9

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_9
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_9.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Timeout counter monitors hready latency; error code 4 on expiry..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_9
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_9

### RTL-0348: Implement dataflow sequence: sequence_10

- Priority: high
- Required: True
- Status: open
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_10
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_10.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_10.
SSOT item context: value=Performance counters increment (PERF_WORDS per word, PERF_CYCLES per active cycle)..
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_10
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_10

### RTL-0349: Implement dataflow sequence: sequence_11

- Priority: high
- Required: True
- Status: pass
- Category: dataflow.sequence
- Source ref: dataflow.sequence.sequence_11
- Detail: Dataflow steps must be reflected in real datapath/control/storage logic.
SSOT ref: dataflow.sequence.sequence_11.
Owner: dma_real_channel in rtl/dma_real_channel.sv via dataflow.sequence.sequence_11.
SSOT item context: value=Repeat read/write bursts until remaining count reaches zero..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL data/control path implements the described step
  - Ordering/backpressure is consistent with cycle_model
  - Downstream checks can observe the result or side effect
  - Traceability keeps source_ref dataflow.sequence.sequence_11
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: dataflow.sequence.sequence_11
