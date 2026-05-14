# RTL Authoring Packet: module__uart_lite_regs__interrupts

- Kind: module
- Owner module: uart_lite_regs
- Owner file: rtl/uart_lite_regs.sv
- Task count: 7
- Required tasks: 7

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
- Owner refs: interrupts, registers, registers.register_list
- Module slice: 3/5 section=interrupts task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0192: Implement interrupt item tx_empty

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.tx_empty
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.tx_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=tx_empty; clear=N/A (level, not sticky).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.tx_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty clear behavior matches SSOT clear policy N/A (level, not sticky)
- SSOT refs: interrupts.sources.tx_empty

### RTL-0193: Implement interrupt item rx_not_empty

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.rx_not_empty
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.rx_not_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=rx_not_empty; clear=N/A (level, not sticky).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.rx_not_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_not_empty clear behavior matches SSOT clear policy N/A (level, not sticky)
- SSOT refs: interrupts.sources.rx_not_empty

### RTL-0194: Implement interrupt item rx_overrun

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.rx_overrun
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.rx_overrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=rx_overrun; clear=W1C via INT_CLEAR[2].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.rx_overrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun clear behavior matches SSOT clear policy W1C via INT_CLEAR[2]
- SSOT refs: interrupts.sources.rx_overrun

### RTL-0195: Implement interrupt item frame_error

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.frame_error
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.frame_error.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=frame_error; clear=W1C via INT_CLEAR[3].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.frame_error
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_error clear behavior matches SSOT clear policy W1C via INT_CLEAR[3]
- SSOT refs: interrupts.sources.frame_error

### RTL-0196: Implement interrupt item parity_error

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.parity_error
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.parity_error.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=parity_error; clear=W1C via INT_CLEAR[4].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.parity_error
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_error clear behavior matches SSOT clear policy W1C via INT_CLEAR[4]
- SSOT refs: interrupts.sources.parity_error

### RTL-0197: Implement interrupt item tx_underrun

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.tx_underrun
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.tx_underrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=tx_underrun; clear=W1C via INT_CLEAR[5].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.tx_underrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_underrun clear behavior matches SSOT clear policy W1C via INT_CLEAR[5]
- SSOT refs: interrupts.sources.tx_underrun

### RTL-0198: Implement interrupt item break_detected

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.break_detected
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.break_detected.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via interrupts.
SSOT item context: name=break_detected; clear=W1C via INT_CLEAR[6].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.break_detected
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_detected clear behavior matches SSOT clear policy W1C via INT_CLEAR[6]
- SSOT refs: interrupts.sources.break_detected
