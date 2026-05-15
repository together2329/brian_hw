# RTL Authoring Packet: module__spi_int

- Kind: module
- Owner module: spi_int
- Owner file: rtl/spi_int.sv
- Task count: 21
- Required tasks: 21

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
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0166: Implement CSR/register INT_MASK

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_MASK
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_MASK.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=INT_MASK; width=32; reset=0; access=rw; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_MASK
  - Primary implementation evidence is in rtl/spi_int.sv
  - INT_MASK width matches SSOT value 32
  - INT_MASK reset behavior matches SSOT value 0
  - INT_MASK access policy rw is implemented without read/write shortcuts
  - INT_MASK decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.INT_MASK

### RTL-0167: Implement field INT_MASK.done_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.done_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.done_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=done_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.done_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - done_en reset behavior matches SSOT value 0
  - done_en access policy rw is implemented without read/write shortcuts
  - done_en readback returns implemented RTL state when readable
  - done_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.done_en

### RTL-0168: Implement field INT_MASK.tx_overrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.tx_overrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.tx_overrun_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=tx_overrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.tx_overrun_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - tx_overrun_en reset behavior matches SSOT value 0
  - tx_overrun_en access policy rw is implemented without read/write shortcuts
  - tx_overrun_en readback returns implemented RTL state when readable
  - tx_overrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.tx_overrun_en

### RTL-0169: Implement field INT_MASK.rx_overrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.rx_overrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.rx_overrun_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_overrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.rx_overrun_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_overrun_en reset behavior matches SSOT value 0
  - rx_overrun_en access policy rw is implemented without read/write shortcuts
  - rx_overrun_en readback returns implemented RTL state when readable
  - rx_overrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.rx_overrun_en

### RTL-0170: Implement field INT_MASK.rx_underrun_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.rx_underrun_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.rx_underrun_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_underrun_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.rx_underrun_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_underrun_en reset behavior matches SSOT value 0
  - rx_underrun_en access policy rw is implemented without read/write shortcuts
  - rx_underrun_en readback returns implemented RTL state when readable
  - rx_underrun_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.rx_underrun_en

### RTL-0171: Implement field INT_MASK.mode_fault_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.mode_fault_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.mode_fault_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=mode_fault_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.mode_fault_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - mode_fault_en reset behavior matches SSOT value 0
  - mode_fault_en access policy rw is implemented without read/write shortcuts
  - mode_fault_en readback returns implemented RTL state when readable
  - mode_fault_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.mode_fault_en

### RTL-0172: Implement field INT_MASK.illegal_access_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.illegal_access_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.illegal_access_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=illegal_access_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.illegal_access_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - illegal_access_en reset behavior matches SSOT value 0
  - illegal_access_en access policy rw is implemented without read/write shortcuts
  - illegal_access_en readback returns implemented RTL state when readable
  - illegal_access_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.illegal_access_en

### RTL-0173: Implement field INT_MASK.tx_empty_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.tx_empty_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.tx_empty_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=tx_empty_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.tx_empty_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - tx_empty_en reset behavior matches SSOT value 0
  - tx_empty_en access policy rw is implemented without read/write shortcuts
  - tx_empty_en readback returns implemented RTL state when readable
  - tx_empty_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.tx_empty_en

### RTL-0174: Implement field INT_MASK.rx_full_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_MASK.fields.rx_full_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_MASK.fields.rx_full_en.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_full_en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_MASK.fields.rx_full_en
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_full_en reset behavior matches SSOT value 0
  - rx_full_en access policy rw is implemented without read/write shortcuts
  - rx_full_en readback returns implemented RTL state when readable
  - rx_full_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_MASK.fields.rx_full_en

### RTL-0175: Implement CSR/register INT_PENDING

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_PENDING
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_PENDING.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=INT_PENDING; width=32; reset=64; access=ro; offset=24.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_PENDING
  - Primary implementation evidence is in rtl/spi_int.sv
  - INT_PENDING width matches SSOT value 32
  - INT_PENDING reset behavior matches SSOT value 64
  - INT_PENDING access policy ro is implemented without read/write shortcuts
  - INT_PENDING decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.INT_PENDING

### RTL-0176: Implement field INT_PENDING.done_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.done_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.done_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=done_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.done_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - done_pend reset behavior matches SSOT value 0
  - done_pend access policy ro is implemented without read/write shortcuts
  - done_pend readback returns implemented RTL state when readable
  - done_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.done_pend

### RTL-0177: Implement field INT_PENDING.tx_overrun_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.tx_overrun_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.tx_overrun_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=tx_overrun_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.tx_overrun_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - tx_overrun_pend reset behavior matches SSOT value 0
  - tx_overrun_pend access policy ro is implemented without read/write shortcuts
  - tx_overrun_pend readback returns implemented RTL state when readable
  - tx_overrun_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.tx_overrun_pend

### RTL-0178: Implement field INT_PENDING.rx_overrun_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.rx_overrun_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.rx_overrun_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_overrun_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.rx_overrun_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_overrun_pend reset behavior matches SSOT value 0
  - rx_overrun_pend access policy ro is implemented without read/write shortcuts
  - rx_overrun_pend readback returns implemented RTL state when readable
  - rx_overrun_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.rx_overrun_pend

### RTL-0179: Implement field INT_PENDING.rx_underrun_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.rx_underrun_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.rx_underrun_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_underrun_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.rx_underrun_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_underrun_pend reset behavior matches SSOT value 0
  - rx_underrun_pend access policy ro is implemented without read/write shortcuts
  - rx_underrun_pend readback returns implemented RTL state when readable
  - rx_underrun_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.rx_underrun_pend

### RTL-0180: Implement field INT_PENDING.mode_fault_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.mode_fault_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.mode_fault_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=mode_fault_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.mode_fault_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - mode_fault_pend reset behavior matches SSOT value 0
  - mode_fault_pend access policy ro is implemented without read/write shortcuts
  - mode_fault_pend readback returns implemented RTL state when readable
  - mode_fault_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.mode_fault_pend

### RTL-0181: Implement field INT_PENDING.illegal_access_pend

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.illegal_access_pend
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.illegal_access_pend.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=illegal_access_pend; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.illegal_access_pend
  - Primary implementation evidence is in rtl/spi_int.sv
  - illegal_access_pend reset behavior matches SSOT value 0
  - illegal_access_pend access policy ro is implemented without read/write shortcuts
  - illegal_access_pend readback returns implemented RTL state when readable
  - illegal_access_pend write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.illegal_access_pend

### RTL-0182: Implement field INT_PENDING.tx_empty_level

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.tx_empty_level
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.tx_empty_level.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=tx_empty_level; reset=1; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.tx_empty_level
  - Primary implementation evidence is in rtl/spi_int.sv
  - tx_empty_level reset behavior matches SSOT value 1
  - tx_empty_level access policy ro is implemented without read/write shortcuts
  - tx_empty_level readback returns implemented RTL state when readable
  - tx_empty_level write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.tx_empty_level

### RTL-0183: Implement field INT_PENDING.rx_full_level

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_PENDING.fields.rx_full_level
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_PENDING.fields.rx_full_level.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=rx_full_level; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_PENDING.fields.rx_full_level
  - Primary implementation evidence is in rtl/spi_int.sv
  - rx_full_level reset behavior matches SSOT value 0
  - rx_full_level access policy ro is implemented without read/write shortcuts
  - rx_full_level readback returns implemented RTL state when readable
  - rx_full_level write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_PENDING.fields.rx_full_level

### RTL-0184: Implement CSR/register INT_CLEAR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_CLEAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_CLEAR.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=INT_CLEAR; width=32; reset=0; access=wo; offset=28.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_CLEAR
  - Primary implementation evidence is in rtl/spi_int.sv
  - INT_CLEAR width matches SSOT value 32
  - INT_CLEAR reset behavior matches SSOT value 0
  - INT_CLEAR access policy wo is implemented without read/write shortcuts
  - INT_CLEAR decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.INT_CLEAR

### RTL-0185: Implement field INT_CLEAR.w1c

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.w1c
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.w1c.
Owner: spi_int in rtl/spi_int.sv via registers.register_list.
SSOT item context: name=w1c; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.w1c
  - Primary implementation evidence is in rtl/spi_int.sv
  - w1c reset behavior matches SSOT value 0
  - w1c access policy wo is implemented without read/write shortcuts
  - w1c readback returns implemented RTL state when readable
  - w1c write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.w1c

### RTL-0247: Prove module spi_int is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.spi_int.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.spi_int.module_equivalence.
Owner: spi_int in rtl/spi_int.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.spi_int.module_equivalence
  - Primary implementation evidence is in rtl/spi_int.sv
- SSOT refs: sub_modules.spi_int.module_equivalence
