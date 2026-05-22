# RTL Authoring Packet: module__dma_real_channel__cycle_model

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
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
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.performance, cycle_model.pipeline, dataflow.ordering.ordering_1, dataflow.ordering.ordering_2, dataflow.ordering.ordering_3, dataflow.ordering.ordering_4, dataflow.sequence.sequence_10, dataflow.sequence.sequence_11, dataflow.sequence.sequence_3, dataflow.sequence.sequence_4, dataflow.sequence.sequence_5, dataflow.sequence.sequence_6, dataflow.sequence.sequence_7, dataflow.sequence.sequence_8
- Module slice: 4/9 section=cycle_model task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0176: Implement pipeline stage: IDLE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.IDLE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.IDLE.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=IDLE; action=wait for valid start/config from CDC bridge; cycle=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.IDLE
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.IDLE timing uses SSOT cycle/latency 0
  - cycle_model.pipeline.IDLE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.IDLE

### RTL-0177: Implement pipeline stage: CFG

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.CFG
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.CFG.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=CFG; action=latch src_addr, dst_addr, remaining, stride from CDC config registers; cycle=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.CFG
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.CFG timing uses SSOT cycle/latency 1
  - cycle_model.pipeline.CFG appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.CFG

### RTL-0178: Implement pipeline stage: REQUEST

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.REQUEST
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.REQUEST.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=REQUEST; action=request AHB bus via arbiter, clock gating cell enables hclk to channel; cycle=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.REQUEST
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.REQUEST timing uses SSOT cycle/latency 2
  - cycle_model.pipeline.REQUEST appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.REQUEST

### RTL-0179: Implement pipeline stage: READ

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.READ
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.READ.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=READ; action=AHB read burst from source address into pointer-based FIFO, timeout counter active; cycle=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.READ
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.READ timing uses SSOT cycle/latency 3
  - cycle_model.pipeline.READ appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.READ

### RTL-0180: Implement pipeline stage: WRITE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.WRITE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.WRITE.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=WRITE; action=AHB write burst from FIFO to destination address, FIFO read pointer advances; cycle=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.WRITE
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.WRITE timing uses SSOT cycle/latency 4
  - cycle_model.pipeline.WRITE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.WRITE

### RTL-0181: Implement pipeline stage: UPDATE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.UPDATE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.UPDATE.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=UPDATE; action=update remaining count (decrement), src_addr (+= stride), dst_addr (+= stride), perf counters increment; cycle=5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.UPDATE
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.UPDATE timing uses SSOT cycle/latency 5
  - cycle_model.pipeline.UPDATE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.UPDATE

### RTL-0182: Implement pipeline stage: DONE

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.DONE
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.DONE.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=DONE; action=assert done pulse, update status, trigger IRQ, clock gating cell may disable hclk; cycle=6.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.DONE
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.DONE timing uses SSOT cycle/latency 6
  - cycle_model.pipeline.DONE appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.DONE

### RTL-0183: Implement pipeline stage: ERROR

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.pipeline
- Source ref: cycle_model.pipeline.ERROR
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.pipeline.ERROR.
Owner: dma_real_channel in rtl/dma_real_channel.sv via cycle_model.pipeline.
SSOT item context: stage=ERROR; action=assert error pulse, latch error code, return to IDLE, clock gating cell may disable hclk; cycle=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.pipeline.ERROR
  - Primary implementation evidence is in rtl/dma_real_channel.sv
  - cycle_model.pipeline.ERROR timing uses SSOT cycle/latency 2
  - cycle_model.pipeline.ERROR appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.pipeline.ERROR
