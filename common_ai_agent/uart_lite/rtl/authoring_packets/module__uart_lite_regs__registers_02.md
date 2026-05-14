# RTL Authoring Packet: module__uart_lite_regs__registers_02

- Kind: module
- Owner module: uart_lite_regs
- Owner file: rtl/uart_lite_regs.sv
- Task count: 11
- Required tasks: 11

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
- Module slice: 2/5 section=registers task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0179: Implement field INT_CLEAR.clear_tx_underrun

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.clear_tx_underrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.clear_tx_underrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=clear_tx_underrun; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.clear_tx_underrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clear_tx_underrun reset behavior matches SSOT value 0
  - clear_tx_underrun access policy wo is implemented without read/write shortcuts
  - clear_tx_underrun readback returns implemented RTL state when readable
  - clear_tx_underrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.clear_tx_underrun

### RTL-0180: Implement field INT_CLEAR.clear_break_det

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.clear_break_det
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.clear_break_det.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=clear_break_det; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.clear_break_det
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clear_break_det reset behavior matches SSOT value 0
  - clear_break_det access policy wo is implemented without read/write shortcuts
  - clear_break_det readback returns implemented RTL state when readable
  - clear_break_det write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.clear_break_det

### RTL-0181: Implement field INT_CLEAR.reserved_31_7

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.reserved_31_7
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.reserved_31_7.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_7; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.reserved_31_7
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_7 reset behavior matches SSOT value 0
  - reserved_31_7 access policy reserved is implemented without read/write shortcuts
  - reserved_31_7 readback returns implemented RTL state when readable
  - reserved_31_7 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.reserved_31_7

### RTL-0182: Implement CSR/register DEBUG_TX_BYTES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DEBUG_TX_BYTES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG_TX_BYTES.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=DEBUG_TX_BYTES; width=32; reset=0; access=ro; offset=28.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG_TX_BYTES
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DEBUG_TX_BYTES width matches SSOT value 32
  - DEBUG_TX_BYTES reset behavior matches SSOT value 0
  - DEBUG_TX_BYTES access policy ro is implemented without read/write shortcuts
  - DEBUG_TX_BYTES decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.DEBUG_TX_BYTES

### RTL-0183: Implement field DEBUG_TX_BYTES.bytes_tx

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DEBUG_TX_BYTES.fields.bytes_tx
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_TX_BYTES.fields.bytes_tx.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=bytes_tx; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_TX_BYTES.fields.bytes_tx
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - bytes_tx reset behavior matches SSOT value 0
  - bytes_tx access policy ro is implemented without read/write shortcuts
  - bytes_tx readback returns implemented RTL state when readable
  - bytes_tx write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_TX_BYTES.fields.bytes_tx

### RTL-0184: Implement CSR/register DEBUG_RX_BYTES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DEBUG_RX_BYTES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG_RX_BYTES.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=DEBUG_RX_BYTES; width=32; reset=0; access=ro; offset=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG_RX_BYTES
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DEBUG_RX_BYTES width matches SSOT value 32
  - DEBUG_RX_BYTES reset behavior matches SSOT value 0
  - DEBUG_RX_BYTES access policy ro is implemented without read/write shortcuts
  - DEBUG_RX_BYTES decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.DEBUG_RX_BYTES

### RTL-0185: Implement field DEBUG_RX_BYTES.bytes_rx

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DEBUG_RX_BYTES.fields.bytes_rx
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_RX_BYTES.fields.bytes_rx.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=bytes_rx; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_RX_BYTES.fields.bytes_rx
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - bytes_rx reset behavior matches SSOT value 0
  - bytes_rx access policy ro is implemented without read/write shortcuts
  - bytes_rx readback returns implemented RTL state when readable
  - bytes_rx write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_RX_BYTES.fields.bytes_rx

### RTL-0186: Implement CSR/register DEBUG_FRAME_ERRS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DEBUG_FRAME_ERRS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG_FRAME_ERRS.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=DEBUG_FRAME_ERRS; width=32; reset=0; access=ro; offset=36.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG_FRAME_ERRS
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DEBUG_FRAME_ERRS width matches SSOT value 32
  - DEBUG_FRAME_ERRS reset behavior matches SSOT value 0
  - DEBUG_FRAME_ERRS access policy ro is implemented without read/write shortcuts
  - DEBUG_FRAME_ERRS decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.DEBUG_FRAME_ERRS

### RTL-0187: Implement field DEBUG_FRAME_ERRS.frames_errored

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DEBUG_FRAME_ERRS.fields.frames_errored
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_FRAME_ERRS.fields.frames_errored.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=frames_errored; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_FRAME_ERRS.fields.frames_errored
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frames_errored reset behavior matches SSOT value 0
  - frames_errored access policy ro is implemented without read/write shortcuts
  - frames_errored readback returns implemented RTL state when readable
  - frames_errored write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_FRAME_ERRS.fields.frames_errored

### RTL-0188: Implement CSR/register DEBUG_PARITY_ERRS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DEBUG_PARITY_ERRS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG_PARITY_ERRS.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=DEBUG_PARITY_ERRS; width=32; reset=0; access=ro; offset=40.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG_PARITY_ERRS
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DEBUG_PARITY_ERRS width matches SSOT value 32
  - DEBUG_PARITY_ERRS reset behavior matches SSOT value 0
  - DEBUG_PARITY_ERRS access policy ro is implemented without read/write shortcuts
  - DEBUG_PARITY_ERRS decode uses SSOT address/offset 40
- SSOT refs: registers.register_list.DEBUG_PARITY_ERRS

### RTL-0189: Implement field DEBUG_PARITY_ERRS.parities_errored

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DEBUG_PARITY_ERRS.fields.parities_errored
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG_PARITY_ERRS.fields.parities_errored.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parities_errored; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG_PARITY_ERRS.fields.parities_errored
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parities_errored reset behavior matches SSOT value 0
  - parities_errored access policy ro is implemented without read/write shortcuts
  - parities_errored readback returns implemented RTL state when readable
  - parities_errored write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG_PARITY_ERRS.fields.parities_errored
