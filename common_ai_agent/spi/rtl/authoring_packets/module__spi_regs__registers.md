# RTL Authoring Packet: module__spi_regs__registers

- Kind: module
- Owner module: spi_regs
- Owner file: rtl/spi_regs.sv
- Task count: 37
- Required tasks: 37

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
- LLM-actionable open tasks: 37
- Human-locked open tasks: 0
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 2/6 section=registers task_limit=48
- Slice rule: Owner module spi_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0136: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/spi_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0137: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/spi_regs.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0138: Implement field CTRL.start

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.start.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=start; reset=0; access=wo.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.start
  - Primary implementation evidence is in rtl/spi_regs.sv
  - start reset behavior matches SSOT value 0
  - start access policy wo is implemented without read/write shortcuts
  - start readback returns implemented RTL state when readable
  - start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.start

### RTL-0139: Implement field CTRL.cpol

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.cpol
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.cpol.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=cpol; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.cpol
  - Primary implementation evidence is in rtl/spi_regs.sv
  - cpol reset behavior matches SSOT value 0
  - cpol access policy rw is implemented without read/write shortcuts
  - cpol readback returns implemented RTL state when readable
  - cpol write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.cpol

### RTL-0140: Implement field CTRL.cpha

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.cpha
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.cpha.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=cpha; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.cpha
  - Primary implementation evidence is in rtl/spi_regs.sv
  - cpha reset behavior matches SSOT value 0
  - cpha access policy rw is implemented without read/write shortcuts
  - cpha readback returns implemented RTL state when readable
  - cpha write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.cpha

### RTL-0141: Implement field CTRL.lsb_first

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.lsb_first
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.lsb_first.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=lsb_first; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.lsb_first
  - Primary implementation evidence is in rtl/spi_regs.sv
  - lsb_first reset behavior matches SSOT value 0
  - lsb_first access policy rw is implemented without read/write shortcuts
  - lsb_first readback returns implemented RTL state when readable
  - lsb_first write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.lsb_first

### RTL-0142: Implement field CTRL.continuous_cs

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.continuous_cs
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.continuous_cs.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=continuous_cs; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.continuous_cs
  - Primary implementation evidence is in rtl/spi_regs.sv
  - continuous_cs reset behavior matches SSOT value 0
  - continuous_cs access policy rw is implemented without read/write shortcuts
  - continuous_cs readback returns implemented RTL state when readable
  - continuous_cs write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.continuous_cs

### RTL-0143: Implement field CTRL.loopback

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.loopback
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.loopback.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=loopback; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.loopback
  - Primary implementation evidence is in rtl/spi_regs.sv
  - loopback reset behavior matches SSOT value 0
  - loopback access policy rw is implemented without read/write shortcuts
  - loopback readback returns implemented RTL state when readable
  - loopback write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.loopback

### RTL-0144: Implement field CTRL.soft_reset

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.soft_reset
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.soft_reset.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=soft_reset; reset=0; access=wo.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.soft_reset
  - Primary implementation evidence is in rtl/spi_regs.sv
  - soft_reset reset behavior matches SSOT value 0
  - soft_reset access policy wo is implemented without read/write shortcuts
  - soft_reset readback returns implemented RTL state when readable
  - soft_reset write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.soft_reset

### RTL-0145: Implement field CTRL.cs_sel

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.cs_sel
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.cs_sel.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=cs_sel; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.cs_sel
  - Primary implementation evidence is in rtl/spi_regs.sv
  - cs_sel reset behavior matches SSOT value 0
  - cs_sel access policy rw is implemented without read/write shortcuts
  - cs_sel readback returns implemented RTL state when readable
  - cs_sel write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.cs_sel

### RTL-0146: Implement field CTRL.data_width_m1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.data_width_m1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.data_width_m1.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=data_width_m1; reset=7; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.data_width_m1
  - Primary implementation evidence is in rtl/spi_regs.sv
  - data_width_m1 reset behavior matches SSOT value 7
  - data_width_m1 access policy rw is implemented without read/write shortcuts
  - data_width_m1 readback returns implemented RTL state when readable
  - data_width_m1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.data_width_m1

### RTL-0147: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=18; access=ro; offset=4.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/spi_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 18
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.STATUS

### RTL-0148: Implement field STATUS.busy

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.busy.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=busy; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.busy
  - Primary implementation evidence is in rtl/spi_regs.sv
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.busy

### RTL-0149: Implement field STATUS.tx_full

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_full.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=tx_full; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_full
  - Primary implementation evidence is in rtl/spi_regs.sv
  - tx_full reset behavior matches SSOT value 0
  - tx_full access policy ro is implemented without read/write shortcuts
  - tx_full readback returns implemented RTL state when readable
  - tx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_full

### RTL-0150: Implement field STATUS.tx_empty

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_empty.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=tx_empty; reset=1; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_empty
  - Primary implementation evidence is in rtl/spi_regs.sv
  - tx_empty reset behavior matches SSOT value 1
  - tx_empty access policy ro is implemented without read/write shortcuts
  - tx_empty readback returns implemented RTL state when readable
  - tx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_empty

### RTL-0151: Implement field STATUS.rx_full

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_full
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_full.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_full; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_full
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_full reset behavior matches SSOT value 0
  - rx_full access policy ro is implemented without read/write shortcuts
  - rx_full readback returns implemented RTL state when readable
  - rx_full write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_full

### RTL-0152: Implement field STATUS.rx_empty

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_empty
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_empty.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_empty; reset=1; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_empty
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_empty reset behavior matches SSOT value 1
  - rx_empty access policy ro is implemented without read/write shortcuts
  - rx_empty readback returns implemented RTL state when readable
  - rx_empty write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_empty

### RTL-0153: Implement field STATUS.done

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.done.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=done; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.done
  - Primary implementation evidence is in rtl/spi_regs.sv
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.done

### RTL-0154: Implement field STATUS.tx_overrun

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.tx_overrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.tx_overrun.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=tx_overrun; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.tx_overrun
  - Primary implementation evidence is in rtl/spi_regs.sv
  - tx_overrun reset behavior matches SSOT value 0
  - tx_overrun access policy ro is implemented without read/write shortcuts
  - tx_overrun readback returns implemented RTL state when readable
  - tx_overrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.tx_overrun

### RTL-0155: Implement field STATUS.rx_overrun

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_overrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_overrun.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_overrun; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_overrun
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_overrun reset behavior matches SSOT value 0
  - rx_overrun access policy ro is implemented without read/write shortcuts
  - rx_overrun readback returns implemented RTL state when readable
  - rx_overrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_overrun

### RTL-0156: Implement field STATUS.rx_underrun

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.rx_underrun
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.rx_underrun.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_underrun; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.rx_underrun
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_underrun reset behavior matches SSOT value 0
  - rx_underrun access policy ro is implemented without read/write shortcuts
  - rx_underrun readback returns implemented RTL state when readable
  - rx_underrun write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.rx_underrun

### RTL-0157: Implement field STATUS.mode_fault

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.mode_fault
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.mode_fault.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=mode_fault; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.mode_fault
  - Primary implementation evidence is in rtl/spi_regs.sv
  - mode_fault reset behavior matches SSOT value 0
  - mode_fault access policy ro is implemented without read/write shortcuts
  - mode_fault readback returns implemented RTL state when readable
  - mode_fault write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.mode_fault

### RTL-0158: Implement field STATUS.illegal_access

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.illegal_access
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.illegal_access.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=illegal_access; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.illegal_access
  - Primary implementation evidence is in rtl/spi_regs.sv
  - illegal_access reset behavior matches SSOT value 0
  - illegal_access access policy ro is implemented without read/write shortcuts
  - illegal_access readback returns implemented RTL state when readable
  - illegal_access write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.illegal_access

### RTL-0159: Implement field STATUS.cs_active

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.cs_active
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.cs_active.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=cs_active; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.cs_active
  - Primary implementation evidence is in rtl/spi_regs.sv
  - cs_active reset behavior matches SSOT value 0
  - cs_active access policy ro is implemented without read/write shortcuts
  - cs_active readback returns implemented RTL state when readable
  - cs_active write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.cs_active

### RTL-0160: Implement CSR/register PRESCALE

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.PRESCALE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PRESCALE.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=PRESCALE; width=32; reset=0; access=rw; offset=8.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PRESCALE
  - Primary implementation evidence is in rtl/spi_regs.sv
  - PRESCALE width matches SSOT value 32
  - PRESCALE reset behavior matches SSOT value 0
  - PRESCALE access policy rw is implemented without read/write shortcuts
  - PRESCALE decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.PRESCALE

### RTL-0161: Implement field PRESCALE.divisor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.PRESCALE.fields.divisor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PRESCALE.fields.divisor.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=divisor; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PRESCALE.fields.divisor
  - Primary implementation evidence is in rtl/spi_regs.sv
  - divisor reset behavior matches SSOT value 0
  - divisor access policy rw is implemented without read/write shortcuts
  - divisor readback returns implemented RTL state when readable
  - divisor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PRESCALE.fields.divisor

### RTL-0162: Implement CSR/register TXDATA

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.TXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.TXDATA.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=TXDATA; width=32; reset=0; access=wo; offset=12.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.TXDATA
  - Primary implementation evidence is in rtl/spi_regs.sv
  - TXDATA width matches SSOT value 32
  - TXDATA reset behavior matches SSOT value 0
  - TXDATA access policy wo is implemented without read/write shortcuts
  - TXDATA decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.TXDATA

### RTL-0163: Implement field TXDATA.tx_payload

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.TXDATA.fields.tx_payload
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.TXDATA.fields.tx_payload.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=tx_payload; reset=0; access=wo.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.TXDATA.fields.tx_payload
  - Primary implementation evidence is in rtl/spi_regs.sv
  - tx_payload reset behavior matches SSOT value 0
  - tx_payload access policy wo is implemented without read/write shortcuts
  - tx_payload readback returns implemented RTL state when readable
  - tx_payload write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.TXDATA.fields.tx_payload

### RTL-0164: Implement CSR/register RXDATA

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.RXDATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.RXDATA.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=RXDATA; width=32; reset=0; access=ro; offset=16.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.RXDATA
  - Primary implementation evidence is in rtl/spi_regs.sv
  - RXDATA width matches SSOT value 32
  - RXDATA reset behavior matches SSOT value 0
  - RXDATA access policy ro is implemented without read/write shortcuts
  - RXDATA decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.RXDATA

### RTL-0165: Implement field RXDATA.rx_payload

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.RXDATA.fields.rx_payload
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RXDATA.fields.rx_payload.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_payload; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.RXDATA.fields.rx_payload
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_payload reset behavior matches SSOT value 0
  - rx_payload access policy ro is implemented without read/write shortcuts
  - rx_payload readback returns implemented RTL state when readable
  - rx_payload write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.RXDATA.fields.rx_payload

### RTL-0186: Implement CSR/register CS_IDLE

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CS_IDLE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CS_IDLE.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=CS_IDLE; width=32; reset=15; access=rw; offset=32.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CS_IDLE
  - Primary implementation evidence is in rtl/spi_regs.sv
  - CS_IDLE width matches SSOT value 32
  - CS_IDLE reset behavior matches SSOT value 15
  - CS_IDLE access policy rw is implemented without read/write shortcuts
  - CS_IDLE decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.CS_IDLE

### RTL-0187: Implement field CS_IDLE.cs_idle_val

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CS_IDLE.fields.cs_idle_val
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CS_IDLE.fields.cs_idle_val.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=cs_idle_val; reset=15; access=rw.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CS_IDLE.fields.cs_idle_val
  - Primary implementation evidence is in rtl/spi_regs.sv
  - cs_idle_val reset behavior matches SSOT value 15
  - cs_idle_val access policy rw is implemented without read/write shortcuts
  - cs_idle_val readback returns implemented RTL state when readable
  - cs_idle_val write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CS_IDLE.fields.cs_idle_val

### RTL-0188: Implement CSR/register DEBUG

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DEBUG
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DEBUG.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=DEBUG; width=32; reset=0; access=ro; offset=36.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DEBUG
  - Primary implementation evidence is in rtl/spi_regs.sv
  - DEBUG width matches SSOT value 32
  - DEBUG reset behavior matches SSOT value 0
  - DEBUG access policy ro is implemented without read/write shortcuts
  - DEBUG decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.DEBUG

### RTL-0189: Implement field DEBUG.tx_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DEBUG.fields.tx_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG.fields.tx_count.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=tx_count; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG.fields.tx_count
  - Primary implementation evidence is in rtl/spi_regs.sv
  - tx_count reset behavior matches SSOT value 0
  - tx_count access policy ro is implemented without read/write shortcuts
  - tx_count readback returns implemented RTL state when readable
  - tx_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG.fields.tx_count

### RTL-0190: Implement field DEBUG.rx_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DEBUG.fields.rx_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG.fields.rx_count.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=rx_count; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG.fields.rx_count
  - Primary implementation evidence is in rtl/spi_regs.sv
  - rx_count reset behavior matches SSOT value 0
  - rx_count access policy ro is implemented without read/write shortcuts
  - rx_count readback returns implemented RTL state when readable
  - rx_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG.fields.rx_count

### RTL-0191: Implement field DEBUG.bit_index

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DEBUG.fields.bit_index
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG.fields.bit_index.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=bit_index; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG.fields.bit_index
  - Primary implementation evidence is in rtl/spi_regs.sv
  - bit_index reset behavior matches SSOT value 0
  - bit_index access policy ro is implemented without read/write shortcuts
  - bit_index readback returns implemented RTL state when readable
  - bit_index write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG.fields.bit_index

### RTL-0192: Implement field DEBUG.active_cs

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DEBUG.fields.active_cs
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DEBUG.fields.active_cs.
Owner: spi_regs in rtl/spi_regs.sv via registers.register_list.
SSOT item context: name=active_cs; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/spi_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DEBUG.fields.active_cs
  - Primary implementation evidence is in rtl/spi_regs.sv
  - active_cs reset behavior matches SSOT value 0
  - active_cs access policy ro is implemented without read/write shortcuts
  - active_cs readback returns implemented RTL state when readable
  - active_cs write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DEBUG.fields.active_cs
