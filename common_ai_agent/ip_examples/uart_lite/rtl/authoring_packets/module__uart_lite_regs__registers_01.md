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
- Owner refs: error_handling, interrupts, registers, registers.register_list
- Module slice: 1/6 section=registers task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])

## Tasks

### RTL-0142: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0143: Implement field CTRL.tx_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.tx_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.tx_enable.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.tx_enable
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_enable reset behavior matches SSOT value 0
  - tx_enable access policy rw is implemented without read/write shortcuts
  - tx_enable readback returns implemented RTL state when readable
  - tx_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.tx_enable

### RTL-0144: Implement field CTRL.rx_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.rx_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.rx_enable.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.rx_enable
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_enable reset behavior matches SSOT value 0
  - rx_enable access policy rw is implemented without read/write shortcuts
  - rx_enable readback returns implemented RTL state when readable
  - rx_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.rx_enable

### RTL-0145: Implement field CTRL.loopback

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.loopback
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.loopback.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=loopback; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.loopback
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - loopback reset behavior matches SSOT value 0
  - loopback access policy rw is implemented without read/write shortcuts
  - loopback readback returns implemented RTL state when readable
  - loopback write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.loopback

### RTL-0146: Implement field CTRL.break_send

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.break_send
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.break_send.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=break_send; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.break_send
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - break_send reset behavior matches SSOT value 0
  - break_send access policy rw is implemented without read/write shortcuts
  - break_send readback returns implemented RTL state when readable
  - break_send write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.break_send

### RTL-0147: Implement field CTRL.parity_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.parity_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.parity_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parity_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.parity_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_en reset behavior matches SSOT value 0
  - parity_en access policy rw is implemented without read/write shortcuts
  - parity_en readback returns implemented RTL state when readable
  - parity_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.parity_en

### RTL-0148: Implement field CTRL.parity_odd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.parity_odd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.parity_odd.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parity_odd; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.parity_odd
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_odd reset behavior matches SSOT value 0
  - parity_odd access policy rw is implemented without read/write shortcuts
  - parity_odd readback returns implemented RTL state when readable
  - parity_odd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.parity_odd

### RTL-0149: Implement field CTRL.stop_bits

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.stop_bits
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.stop_bits.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=stop_bits; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.stop_bits
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - stop_bits reset behavior matches SSOT value 0
  - stop_bits access policy rw is implemented without read/write shortcuts
  - stop_bits readback returns implemented RTL state when readable
  - stop_bits write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.stop_bits

### RTL-0150: Implement field CTRL.reserved_31_7

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_7
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_7.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_7; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_7
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_7 reset behavior matches SSOT value 0
  - reserved_31_7 access policy reserved is implemented without read/write shortcuts
  - reserved_31_7 readback returns implemented RTL state when readable
  - reserved_31_7 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_7

### RTL-0151: Implement CSR/register STAT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STAT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STAT.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=STAT; width=32; reset=0; access=ro; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STAT
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - STAT width matches SSOT value 32
  - STAT reset behavior matches SSOT value 0
  - STAT access policy ro is implemented without read/write shortcuts
  - STAT decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.STAT

### RTL-0152: Implement field STAT.tx_full

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.tx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.tx_full.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_full; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.tx_full
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_full reset behavior matches SSOT value 0
  - tx_full access policy ro is implemented without read/write shortcuts
  - tx_full readback returns implemented RTL state when readable
  - tx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.tx_full

### RTL-0153: Implement field STAT.tx_empty

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.tx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.tx_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_empty; reset=1; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.tx_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty reset behavior matches SSOT value 1
  - tx_empty access policy ro is implemented without read/write shortcuts
  - tx_empty readback returns implemented RTL state when readable
  - tx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.tx_empty

### RTL-0154: Implement field STAT.rx_empty

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.rx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.rx_empty.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_empty; reset=1; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.rx_empty
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_empty reset behavior matches SSOT value 1
  - rx_empty access policy ro is implemented without read/write shortcuts
  - rx_empty readback returns implemented RTL state when readable
  - rx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.rx_empty

### RTL-0155: Implement field STAT.rx_full

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.rx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.rx_full.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_full; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.rx_full
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_full reset behavior matches SSOT value 0
  - rx_full access policy ro is implemented without read/write shortcuts
  - rx_full readback returns implemented RTL state when readable
  - rx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.rx_full

### RTL-0156: Implement field STAT.tx_busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.tx_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.tx_busy.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_busy; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.tx_busy
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_busy reset behavior matches SSOT value 0
  - tx_busy access policy ro is implemented without read/write shortcuts
  - tx_busy readback returns implemented RTL state when readable
  - tx_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.tx_busy

### RTL-0157: Implement field STAT.rx_busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.rx_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.rx_busy.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_busy; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.rx_busy
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_busy reset behavior matches SSOT value 0
  - rx_busy access policy ro is implemented without read/write shortcuts
  - rx_busy readback returns implemented RTL state when readable
  - rx_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.rx_busy

### RTL-0158: Implement field STAT.frame_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.frame_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.frame_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=frame_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.frame_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err reset behavior matches SSOT value 0
  - frame_err access policy ro is implemented without read/write shortcuts
  - frame_err readback returns implemented RTL state when readable
  - frame_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.frame_err

### RTL-0159: Implement field STAT.parity_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.parity_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.parity_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parity_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.parity_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err reset behavior matches SSOT value 0
  - parity_err access policy ro is implemented without read/write shortcuts
  - parity_err readback returns implemented RTL state when readable
  - parity_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.parity_err

### RTL-0160: Implement field STAT.overrun_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.overrun_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.overrun_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=overrun_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.overrun_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - overrun_err reset behavior matches SSOT value 0
  - overrun_err access policy ro is implemented without read/write shortcuts
  - overrun_err readback returns implemented RTL state when readable
  - overrun_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.overrun_err

### RTL-0161: Implement field STAT.underrun_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.underrun_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.underrun_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=underrun_err; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.underrun_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - underrun_err reset behavior matches SSOT value 0
  - underrun_err access policy ro is implemented without read/write shortcuts
  - underrun_err readback returns implemented RTL state when readable
  - underrun_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.underrun_err

### RTL-0162: Implement field STAT.reserved_31_10

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STAT.fields.reserved_31_10
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STAT.fields.reserved_31_10.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_10; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STAT.fields.reserved_31_10
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_10 reset behavior matches SSOT value 0
  - reserved_31_10 access policy reserved is implemented without read/write shortcuts
  - reserved_31_10 readback returns implemented RTL state when readable
  - reserved_31_10 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STAT.fields.reserved_31_10

### RTL-0163: Implement CSR/register BAUD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.BAUD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.BAUD.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=BAUD; width=32; reset=324; access=rw; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.BAUD
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - BAUD width matches SSOT value 32
  - BAUD reset behavior matches SSOT value 324
  - BAUD access policy rw is implemented without read/write shortcuts
  - BAUD decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.BAUD

### RTL-0164: Implement field BAUD.baud_div

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.BAUD.fields.baud_div
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.BAUD.fields.baud_div.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=baud_div; reset=324; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.BAUD.fields.baud_div
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - baud_div reset behavior matches SSOT value 324
  - baud_div access policy rw is implemented without read/write shortcuts
  - baud_div readback returns implemented RTL state when readable
  - baud_div write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.BAUD.fields.baud_div

### RTL-0165: Implement field BAUD.reserved_31_16

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.BAUD.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.BAUD.fields.reserved_31_16.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.BAUD.fields.reserved_31_16
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.BAUD.fields.reserved_31_16

### RTL-0166: Implement CSR/register TXDATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.TXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.TXDATA.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=TXDATA; width=32; reset=0; access=wo; offset=12.
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
  - TXDATA decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.TXDATA

### RTL-0167: Implement field TXDATA.tx_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.TXDATA.fields.tx_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.TXDATA.fields.tx_data.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
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

### RTL-0168: Implement field TXDATA.reserved_31_8

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.TXDATA.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.TXDATA.fields.reserved_31_8.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
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

### RTL-0169: Implement CSR/register RXDATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.RXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.RXDATA.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=RXDATA; width=32; reset=0; access=ro; offset=16.
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
  - RXDATA decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.RXDATA

### RTL-0170: Implement field RXDATA.rx_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.RXDATA.fields.rx_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RXDATA.fields.rx_data.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
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

### RTL-0171: Implement field RXDATA.reserved_31_8

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.RXDATA.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RXDATA.fields.reserved_31_8.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
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

### RTL-0172: Implement CSR/register INTEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INTEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTEN.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=INTEN; width=32; reset=0; access=rw; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTEN
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - INTEN width matches SSOT value 32
  - INTEN reset behavior matches SSOT value 0
  - INTEN access policy rw is implemented without read/write shortcuts
  - INTEN decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.INTEN

### RTL-0173: Implement field INTEN.tx_empty_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.tx_empty_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.tx_empty_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_empty_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.tx_empty_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty_en reset behavior matches SSOT value 0
  - tx_empty_en access policy rw is implemented without read/write shortcuts
  - tx_empty_en readback returns implemented RTL state when readable
  - tx_empty_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.tx_empty_en

### RTL-0174: Implement field INTEN.rx_not_empty_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.rx_not_empty_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.rx_not_empty_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_not_empty_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.rx_not_empty_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_not_empty_en reset behavior matches SSOT value 0
  - rx_not_empty_en access policy rw is implemented without read/write shortcuts
  - rx_not_empty_en readback returns implemented RTL state when readable
  - rx_not_empty_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.rx_not_empty_en

### RTL-0175: Implement field INTEN.rx_overrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.rx_overrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.rx_overrun_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_overrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.rx_overrun_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun_en reset behavior matches SSOT value 0
  - rx_overrun_en access policy rw is implemented without read/write shortcuts
  - rx_overrun_en readback returns implemented RTL state when readable
  - rx_overrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.rx_overrun_en

### RTL-0176: Implement field INTEN.frame_err_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.frame_err_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.frame_err_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=frame_err_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.frame_err_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err_en reset behavior matches SSOT value 0
  - frame_err_en access policy rw is implemented without read/write shortcuts
  - frame_err_en readback returns implemented RTL state when readable
  - frame_err_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.frame_err_en

### RTL-0177: Implement field INTEN.parity_err_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.parity_err_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.parity_err_en.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parity_err_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.parity_err_en
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err_en reset behavior matches SSOT value 0
  - parity_err_en access policy rw is implemented without read/write shortcuts
  - parity_err_en readback returns implemented RTL state when readable
  - parity_err_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.parity_err_en

### RTL-0178: Implement field INTEN.reserved_31_5

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTEN.fields.reserved_31_5
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTEN.fields.reserved_31_5.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_5; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTEN.fields.reserved_31_5
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_5 reset behavior matches SSOT value 0
  - reserved_31_5 access policy reserved is implemented without read/write shortcuts
  - reserved_31_5 readback returns implemented RTL state when readable
  - reserved_31_5 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTEN.fields.reserved_31_5

### RTL-0179: Implement CSR/register INTPEND

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INTPEND
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTPEND.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=INTPEND; width=32; reset=0; access=rw; offset=24.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTPEND
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - INTPEND width matches SSOT value 32
  - INTPEND reset behavior matches SSOT value 0
  - INTPEND access policy rw is implemented without read/write shortcuts
  - INTPEND decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.INTPEND

### RTL-0180: Implement field INTPEND.tx_empty_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.tx_empty_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.tx_empty_pend.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=tx_empty_pend; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.tx_empty_pend
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - tx_empty_pend reset behavior matches SSOT value 0
  - tx_empty_pend access policy rw is implemented without read/write shortcuts
  - tx_empty_pend readback returns implemented RTL state when readable
  - tx_empty_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.tx_empty_pend

### RTL-0181: Implement field INTPEND.rx_not_empty_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.rx_not_empty_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.rx_not_empty_pend.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_not_empty_pend; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.rx_not_empty_pend
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_not_empty_pend reset behavior matches SSOT value 0
  - rx_not_empty_pend access policy rw is implemented without read/write shortcuts
  - rx_not_empty_pend readback returns implemented RTL state when readable
  - rx_not_empty_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.rx_not_empty_pend

### RTL-0182: Implement field INTPEND.rx_overrun_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.rx_overrun_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.rx_overrun_pend.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=rx_overrun_pend; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.rx_overrun_pend
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - rx_overrun_pend reset behavior matches SSOT value 0
  - rx_overrun_pend access policy rw is implemented without read/write shortcuts
  - rx_overrun_pend readback returns implemented RTL state when readable
  - rx_overrun_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.rx_overrun_pend

### RTL-0183: Implement field INTPEND.frame_err_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.frame_err_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.frame_err_pend.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=frame_err_pend; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.frame_err_pend
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frame_err_pend reset behavior matches SSOT value 0
  - frame_err_pend access policy rw is implemented without read/write shortcuts
  - frame_err_pend readback returns implemented RTL state when readable
  - frame_err_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.frame_err_pend

### RTL-0184: Implement field INTPEND.parity_err_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.parity_err_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.parity_err_pend.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parity_err_pend; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.parity_err_pend
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parity_err_pend reset behavior matches SSOT value 0
  - parity_err_pend access policy rw is implemented without read/write shortcuts
  - parity_err_pend readback returns implemented RTL state when readable
  - parity_err_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.parity_err_pend

### RTL-0185: Implement field INTPEND.reserved_31_5

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INTPEND.fields.reserved_31_5
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTPEND.fields.reserved_31_5.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_5; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTPEND.fields.reserved_31_5
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_5 reset behavior matches SSOT value 0
  - reserved_31_5 access policy reserved is implemented without read/write shortcuts
  - reserved_31_5 readback returns implemented RTL state when readable
  - reserved_31_5 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTPEND.fields.reserved_31_5

### RTL-0186: Implement CSR/register CLR_STAT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CLR_STAT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CLR_STAT.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=CLR_STAT; width=32; reset=0; access=rw; offset=28.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CLR_STAT
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - CLR_STAT width matches SSOT value 32
  - CLR_STAT reset behavior matches SSOT value 0
  - CLR_STAT access policy rw is implemented without read/write shortcuts
  - CLR_STAT decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.CLR_STAT

### RTL-0187: Implement field CLR_STAT.clr_frame_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CLR_STAT.fields.clr_frame_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CLR_STAT.fields.clr_frame_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=clr_frame_err; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CLR_STAT.fields.clr_frame_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clr_frame_err reset behavior matches SSOT value 0
  - clr_frame_err access policy rw is implemented without read/write shortcuts
  - clr_frame_err readback returns implemented RTL state when readable
  - clr_frame_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CLR_STAT.fields.clr_frame_err

### RTL-0188: Implement field CLR_STAT.clr_parity_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CLR_STAT.fields.clr_parity_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CLR_STAT.fields.clr_parity_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=clr_parity_err; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CLR_STAT.fields.clr_parity_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clr_parity_err reset behavior matches SSOT value 0
  - clr_parity_err access policy rw is implemented without read/write shortcuts
  - clr_parity_err readback returns implemented RTL state when readable
  - clr_parity_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CLR_STAT.fields.clr_parity_err

### RTL-0189: Implement field CLR_STAT.clr_overrun_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CLR_STAT.fields.clr_overrun_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CLR_STAT.fields.clr_overrun_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=clr_overrun_err; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CLR_STAT.fields.clr_overrun_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clr_overrun_err reset behavior matches SSOT value 0
  - clr_overrun_err access policy rw is implemented without read/write shortcuts
  - clr_overrun_err readback returns implemented RTL state when readable
  - clr_overrun_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CLR_STAT.fields.clr_overrun_err
