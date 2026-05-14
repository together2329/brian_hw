# RTL Authoring Packet: module__uart_lite_regs__registers_01

- Kind: module
- Owner module: uart_lite_regs
- Owner file: rtl/uart_lite_regs.sv
- Task count: 48
- Required tasks: 48

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
- Module slice: 1/5 section=registers task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0131: Implement CSR/register TXDATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.TXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.TXDATA.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=TXDATA; width=32; reset=0; access=wo; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.TXDATA
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - TXDATA width matches SSOT value 32
  - TXDATA reset behavior matches SSOT value 0
  - TXDATA access policy wo is implemented without read/write shortcuts
  - TXDATA decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.TXDATA

### RTL-0132: Implement field TXDATA.tx_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.TXDATA.fields.tx_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.TXDATA.fields.tx_data.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_data; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.TXDATA.fields.tx_data
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_data reset behavior matches SSOT value 0
  - tx_data access policy wo is implemented without read/write shortcuts
  - tx_data readback returns implemented RTL state when readable
  - tx_data write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.TXDATA.fields.tx_data

### RTL-0133: Implement field TXDATA.reserved_31_8

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.TXDATA.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.TXDATA.fields.reserved_31_8.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_8; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.TXDATA.fields.reserved_31_8
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_8 reset behavior matches SSOT value 0
  - reserved_31_8 access policy reserved is implemented without read/write shortcuts
  - reserved_31_8 readback returns implemented RTL state when readable
  - reserved_31_8 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.TXDATA.fields.reserved_31_8

### RTL-0134: Implement CSR/register RXDATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.RXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.RXDATA.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=RXDATA; width=32; reset=0; access=ro; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.RXDATA
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - RXDATA width matches SSOT value 32
  - RXDATA reset behavior matches SSOT value 0
  - RXDATA access policy ro is implemented without read/write shortcuts
  - RXDATA decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.RXDATA

### RTL-0135: Implement field RXDATA.rx_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.RXDATA.fields.rx_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RXDATA.fields.rx_data.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_data; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.RXDATA.fields.rx_data
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_data reset behavior matches SSOT value 0
  - rx_data access policy ro is implemented without read/write shortcuts
  - rx_data readback returns implemented RTL state when readable
  - rx_data write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.RXDATA.fields.rx_data

### RTL-0136: Implement field RXDATA.reserved_31_8

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.RXDATA.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RXDATA.fields.reserved_31_8.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_8; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.RXDATA.fields.reserved_31_8
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_8 reset behavior matches SSOT value 0
  - reserved_31_8 access policy reserved is implemented without read/write shortcuts
  - reserved_31_8 readback returns implemented RTL state when readable
  - reserved_31_8 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.RXDATA.fields.reserved_31_8

### RTL-0137: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=STATUS; width=32; reset=4; access=ro; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 4
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0138: Implement field STATUS.tx_empty

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_empty; reset=1; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty reset behavior matches SSOT value 1
  - tx_empty access policy ro is implemented without read/write shortcuts
  - tx_empty readback returns implemented RTL state when readable
  - tx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_empty

### RTL-0139: Implement field STATUS.tx_full

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_full.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_full; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_full
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_full reset behavior matches SSOT value 0
  - tx_full access policy ro is implemented without read/write shortcuts
  - tx_full readback returns implemented RTL state when readable
  - tx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_full

### RTL-0140: Implement field STATUS.rx_empty

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_empty; reset=1; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_empty reset behavior matches SSOT value 1
  - rx_empty access policy ro is implemented without read/write shortcuts
  - rx_empty readback returns implemented RTL state when readable
  - rx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_empty

### RTL-0141: Implement field STATUS.rx_full

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_full.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_full; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_full
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_full reset behavior matches SSOT value 0
  - rx_full access policy ro is implemented without read/write shortcuts
  - rx_full readback returns implemented RTL state when readable
  - rx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_full

### RTL-0142: Implement field STATUS.frame_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.frame_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.frame_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=frame_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.frame_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err reset behavior matches SSOT value 0
  - frame_err access policy ro is implemented without read/write shortcuts
  - frame_err readback returns implemented RTL state when readable
  - frame_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.frame_err

### RTL-0143: Implement field STATUS.parity_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.parity_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.parity_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parity_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.parity_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err reset behavior matches SSOT value 0
  - parity_err access policy ro is implemented without read/write shortcuts
  - parity_err readback returns implemented RTL state when readable
  - parity_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.parity_err

### RTL-0144: Implement field STATUS.rx_overrun

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_overrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_overrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_overrun; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_overrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun reset behavior matches SSOT value 0
  - rx_overrun access policy ro is implemented without read/write shortcuts
  - rx_overrun readback returns implemented RTL state when readable
  - rx_overrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_overrun

### RTL-0145: Implement field STATUS.tx_underrun

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_underrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_underrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_underrun; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_underrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_underrun reset behavior matches SSOT value 0
  - tx_underrun access policy ro is implemented without read/write shortcuts
  - tx_underrun readback returns implemented RTL state when readable
  - tx_underrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_underrun

### RTL-0146: Implement field STATUS.break_detected

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.break_detected
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.break_detected.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=break_detected; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.break_detected
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_detected reset behavior matches SSOT value 0
  - break_detected access policy ro is implemented without read/write shortcuts
  - break_detected readback returns implemented RTL state when readable
  - break_detected write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.break_detected

### RTL-0147: Implement field STATUS.reserved_31_9

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_9
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_9.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_9; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_9
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_9 reset behavior matches SSOT value 0
  - reserved_31_9 access policy reserved is implemented without read/write shortcuts
  - reserved_31_9 readback returns implemented RTL state when readable
  - reserved_31_9 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_9

### RTL-0148: Implement CSR/register CONTROL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CONTROL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CONTROL.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=CONTROL; width=32; reset=0; access=rw; offset=12.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CONTROL
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - CONTROL width matches SSOT value 32
  - CONTROL reset behavior matches SSOT value 0
  - CONTROL access policy rw is implemented without read/write shortcuts
  - CONTROL decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.CONTROL

### RTL-0149: Implement field CONTROL.baud_div

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.baud_div
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.baud_div.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=baud_div; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.baud_div
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - baud_div reset behavior matches SSOT value 0
  - baud_div access policy rw is implemented without read/write shortcuts
  - baud_div readback returns implemented RTL state when readable
  - baud_div write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.baud_div

### RTL-0150: Implement field CONTROL.parity_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.parity_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.parity_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parity_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.parity_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_en reset behavior matches SSOT value 0
  - parity_en access policy rw is implemented without read/write shortcuts
  - parity_en readback returns implemented RTL state when readable
  - parity_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.parity_en

### RTL-0151: Implement field CONTROL.parity_odd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.parity_odd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.parity_odd.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parity_odd; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.parity_odd
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_odd reset behavior matches SSOT value 0
  - parity_odd access policy rw is implemented without read/write shortcuts
  - parity_odd readback returns implemented RTL state when readable
  - parity_odd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.parity_odd

### RTL-0152: Implement field CONTROL.stop_bits

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.stop_bits
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.stop_bits.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=stop_bits; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.stop_bits
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - stop_bits reset behavior matches SSOT value 0
  - stop_bits access policy rw is implemented without read/write shortcuts
  - stop_bits readback returns implemented RTL state when readable
  - stop_bits write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.stop_bits

### RTL-0153: Implement field CONTROL.loopback

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.loopback
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.loopback.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=loopback; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.loopback
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - loopback reset behavior matches SSOT value 0
  - loopback access policy rw is implemented without read/write shortcuts
  - loopback readback returns implemented RTL state when readable
  - loopback write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.loopback

### RTL-0154: Implement field CONTROL.break_send

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.break_send
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.break_send.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=break_send; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.break_send
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_send reset behavior matches SSOT value 0
  - break_send access policy rw is implemented without read/write shortcuts
  - break_send readback returns implemented RTL state when readable
  - break_send write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.break_send

### RTL-0155: Implement field CONTROL.data_width

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.data_width
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.data_width.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=data_width; reset=3; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.data_width
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - data_width reset behavior matches SSOT value 3
  - data_width access policy rw is implemented without read/write shortcuts
  - data_width readback returns implemented RTL state when readable
  - data_width write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.data_width

### RTL-0156: Implement field CONTROL.reserved_31_24

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.reserved_31_24
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.reserved_31_24.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_24; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.reserved_31_24
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_24 reset behavior matches SSOT value 0
  - reserved_31_24 access policy reserved is implemented without read/write shortcuts
  - reserved_31_24 readback returns implemented RTL state when readable
  - reserved_31_24 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.reserved_31_24

### RTL-0157: Implement CSR/register INT_MASK

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_MASK
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_MASK.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=INT_MASK; width=32; reset=0; access=rw; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_MASK
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - INT_MASK width matches SSOT value 32
  - INT_MASK reset behavior matches SSOT value 0
  - INT_MASK access policy rw is implemented without read/write shortcuts
  - INT_MASK decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.INT_MASK

### RTL-0158: Implement field INT_MASK.tx_empty_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.tx_empty_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.tx_empty_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_empty_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.tx_empty_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty_en reset behavior matches SSOT value 0
  - tx_empty_en access policy rw is implemented without read/write shortcuts
  - tx_empty_en readback returns implemented RTL state when readable
  - tx_empty_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.tx_empty_en

### RTL-0159: Implement field INT_MASK.rx_not_empty_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.rx_not_empty_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.rx_not_empty_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_not_empty_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.rx_not_empty_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_not_empty_en reset behavior matches SSOT value 0
  - rx_not_empty_en access policy rw is implemented without read/write shortcuts
  - rx_not_empty_en readback returns implemented RTL state when readable
  - rx_not_empty_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.rx_not_empty_en

### RTL-0160: Implement field INT_MASK.rx_overrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.rx_overrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.rx_overrun_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_overrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.rx_overrun_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun_en reset behavior matches SSOT value 0
  - rx_overrun_en access policy rw is implemented without read/write shortcuts
  - rx_overrun_en readback returns implemented RTL state when readable
  - rx_overrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.rx_overrun_en

### RTL-0161: Implement field INT_MASK.frame_err_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.frame_err_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.frame_err_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=frame_err_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.frame_err_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err_en reset behavior matches SSOT value 0
  - frame_err_en access policy rw is implemented without read/write shortcuts
  - frame_err_en readback returns implemented RTL state when readable
  - frame_err_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.frame_err_en

### RTL-0162: Implement field INT_MASK.parity_err_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.parity_err_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.parity_err_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parity_err_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.parity_err_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err_en reset behavior matches SSOT value 0
  - parity_err_en access policy rw is implemented without read/write shortcuts
  - parity_err_en readback returns implemented RTL state when readable
  - parity_err_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.parity_err_en

### RTL-0163: Implement field INT_MASK.tx_underrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.tx_underrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.tx_underrun_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_underrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.tx_underrun_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_underrun_en reset behavior matches SSOT value 0
  - tx_underrun_en access policy rw is implemented without read/write shortcuts
  - tx_underrun_en readback returns implemented RTL state when readable
  - tx_underrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.tx_underrun_en

### RTL-0164: Implement field INT_MASK.break_det_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.break_det_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.break_det_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=break_det_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.break_det_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_det_en reset behavior matches SSOT value 0
  - break_det_en access policy rw is implemented without read/write shortcuts
  - break_det_en readback returns implemented RTL state when readable
  - break_det_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.break_det_en

### RTL-0165: Implement field INT_MASK.reserved_31_7

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.reserved_31_7
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.reserved_31_7.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_7; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.reserved_31_7
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_7 reset behavior matches SSOT value 0
  - reserved_31_7 access policy reserved is implemented without read/write shortcuts
  - reserved_31_7 readback returns implemented RTL state when readable
  - reserved_31_7 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.reserved_31_7

### RTL-0166: Implement CSR/register INT_PENDING

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_PENDING
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_PENDING.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=INT_PENDING; width=32; reset=0; access=ro; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_PENDING
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - INT_PENDING width matches SSOT value 32
  - INT_PENDING reset behavior matches SSOT value 0
  - INT_PENDING access policy ro is implemented without read/write shortcuts
  - INT_PENDING decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.INT_PENDING

### RTL-0167: Implement field INT_PENDING.tx_empty_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.tx_empty_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.tx_empty_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_empty_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.tx_empty_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty_pending reset behavior matches SSOT value 0
  - tx_empty_pending access policy ro is implemented without read/write shortcuts
  - tx_empty_pending readback returns implemented RTL state when readable
  - tx_empty_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.tx_empty_pending

### RTL-0168: Implement field INT_PENDING.rx_not_empty_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.rx_not_empty_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.rx_not_empty_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_not_empty_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.rx_not_empty_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_not_empty_pending reset behavior matches SSOT value 0
  - rx_not_empty_pending access policy ro is implemented without read/write shortcuts
  - rx_not_empty_pending readback returns implemented RTL state when readable
  - rx_not_empty_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.rx_not_empty_pending

### RTL-0169: Implement field INT_PENDING.rx_overrun_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.rx_overrun_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.rx_overrun_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=rx_overrun_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.rx_overrun_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun_pending reset behavior matches SSOT value 0
  - rx_overrun_pending access policy ro is implemented without read/write shortcuts
  - rx_overrun_pending readback returns implemented RTL state when readable
  - rx_overrun_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.rx_overrun_pending

### RTL-0170: Implement field INT_PENDING.frame_err_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.frame_err_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.frame_err_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=frame_err_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.frame_err_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err_pending reset behavior matches SSOT value 0
  - frame_err_pending access policy ro is implemented without read/write shortcuts
  - frame_err_pending readback returns implemented RTL state when readable
  - frame_err_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.frame_err_pending

### RTL-0171: Implement field INT_PENDING.parity_err_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.parity_err_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.parity_err_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=parity_err_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.parity_err_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err_pending reset behavior matches SSOT value 0
  - parity_err_pending access policy ro is implemented without read/write shortcuts
  - parity_err_pending readback returns implemented RTL state when readable
  - parity_err_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.parity_err_pending

### RTL-0172: Implement field INT_PENDING.tx_underrun_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.tx_underrun_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.tx_underrun_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=tx_underrun_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.tx_underrun_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_underrun_pending reset behavior matches SSOT value 0
  - tx_underrun_pending access policy ro is implemented without read/write shortcuts
  - tx_underrun_pending readback returns implemented RTL state when readable
  - tx_underrun_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.tx_underrun_pending

### RTL-0173: Implement field INT_PENDING.break_det_pending

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.break_det_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.break_det_pending.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=break_det_pending; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.break_det_pending
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_det_pending reset behavior matches SSOT value 0
  - break_det_pending access policy ro is implemented without read/write shortcuts
  - break_det_pending readback returns implemented RTL state when readable
  - break_det_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.break_det_pending

### RTL-0174: Implement field INT_PENDING.reserved_31_7

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.reserved_31_7
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.reserved_31_7.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=reserved_31_7; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.reserved_31_7
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_7 reset behavior matches SSOT value 0
  - reserved_31_7 access policy reserved is implemented without read/write shortcuts
  - reserved_31_7 readback returns implemented RTL state when readable
  - reserved_31_7 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.reserved_31_7

### RTL-0175: Implement CSR/register INT_CLEAR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_CLEAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_CLEAR.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=INT_CLEAR; width=32; reset=0; access=wo; offset=24.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_CLEAR
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - INT_CLEAR width matches SSOT value 32
  - INT_CLEAR reset behavior matches SSOT value 0
  - INT_CLEAR access policy wo is implemented without read/write shortcuts
  - INT_CLEAR decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.INT_CLEAR

### RTL-0176: Implement field INT_CLEAR.clear_rx_overrun

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.clear_rx_overrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.clear_rx_overrun.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=clear_rx_overrun; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.clear_rx_overrun
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clear_rx_overrun reset behavior matches SSOT value 0
  - clear_rx_overrun access policy wo is implemented without read/write shortcuts
  - clear_rx_overrun readback returns implemented RTL state when readable
  - clear_rx_overrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.clear_rx_overrun

### RTL-0177: Implement field INT_CLEAR.clear_frame_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.clear_frame_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.clear_frame_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=clear_frame_err; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.clear_frame_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clear_frame_err reset behavior matches SSOT value 0
  - clear_frame_err access policy wo is implemented without read/write shortcuts
  - clear_frame_err readback returns implemented RTL state when readable
  - clear_frame_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.clear_frame_err

### RTL-0178: Implement field INT_CLEAR.clear_parity_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.clear_parity_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.clear_parity_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.
SSOT item context: name=clear_parity_err; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.clear_parity_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clear_parity_err reset behavior matches SSOT value 0
  - clear_parity_err access policy wo is implemented without read/write shortcuts
  - clear_parity_err readback returns implemented RTL state when readable
  - clear_parity_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.clear_parity_err
