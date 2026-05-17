# RTL Authoring Packet: module__dma_real_channel__error_handling

- Kind: module
- Owner module: dma_real_channel
- Owner file: rtl/dma_real_channel.sv
- Task count: 5
- Required tasks: 5

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
- Module slice: 6/9 section=error_handling task_limit=48
- Slice rule: Owner module dma_real_channel is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0358: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
SSOT item context: value=Software reads CHx_STATUS to identify error code.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0359: Implement error/fault item recovery_1

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_1
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_1.
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
SSOT item context: value=Software writes INT_CLEAR to clear error and done latches.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_1
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: error_handling.recovery.recovery_1

### RTL-0360: Implement error/fault item recovery_2

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_2
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_2.
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
SSOT item context: value=Channel returns to IDLE after status is cleared.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_2
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: error_handling.recovery.recovery_2

### RTL-0361: Implement error/fault item recovery_3

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_3
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_3.
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
SSOT item context: value=No automatic retry (software must reconfigure and restart).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_3
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: error_handling.recovery.recovery_3

### RTL-0362: Implement error/fault item recovery_4

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_4
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_4.
Owner: dma_real_channel in rtl/dma_real_channel.sv via error_handling.
SSOT item context: value=For hresp=RETRY, hardware re-requests same transfer automatically.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_4
  - Primary implementation evidence is in rtl/dma_real_channel.sv
- SSOT refs: error_handling.recovery.recovery_4
