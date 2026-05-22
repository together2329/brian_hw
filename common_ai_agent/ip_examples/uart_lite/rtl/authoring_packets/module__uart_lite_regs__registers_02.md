# RTL Authoring Packet: module__uart_lite_regs__registers_02

- Kind: module
- Owner module: uart_lite_regs
- Owner file: rtl/uart_lite_regs.sv
- Task count: 10
- Required tasks: 10

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
- Module slice: 2/6 section=registers task_limit=48
- Slice rule: Owner module uart_lite_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])

## Tasks

### RTL-0190: Implement field CLR_STAT.clr_underrun_err

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CLR_STAT.fields.clr_underrun_err
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CLR_STAT.fields.clr_underrun_err.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=clr_underrun_err; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CLR_STAT.fields.clr_underrun_err
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - clr_underrun_err reset behavior matches SSOT value 0
  - clr_underrun_err access policy rw is implemented without read/write shortcuts
  - clr_underrun_err readback returns implemented RTL state when readable
  - clr_underrun_err write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CLR_STAT.fields.clr_underrun_err

### RTL-0191: Implement field CLR_STAT.reserved_31_4

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CLR_STAT.fields.reserved_31_4
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CLR_STAT.fields.reserved_31_4.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_4; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CLR_STAT.fields.reserved_31_4
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - reserved_31_4 reset behavior matches SSOT value 0
  - reserved_31_4 access policy reserved is implemented without read/write shortcuts
  - reserved_31_4 readback returns implemented RTL state when readable
  - reserved_31_4 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CLR_STAT.fields.reserved_31_4

### RTL-0192: Implement CSR/register DBG_BYTES_TX

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBG_BYTES_TX
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBG_BYTES_TX.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=DBG_BYTES_TX; width=32; reset=0; access=ro; offset=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBG_BYTES_TX
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DBG_BYTES_TX width matches SSOT value 32
  - DBG_BYTES_TX reset behavior matches SSOT value 0
  - DBG_BYTES_TX access policy ro is implemented without read/write shortcuts
  - DBG_BYTES_TX decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.DBG_BYTES_TX

### RTL-0193: Implement field DBG_BYTES_TX.bytes_tx

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBG_BYTES_TX.fields.bytes_tx
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBG_BYTES_TX.fields.bytes_tx.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=bytes_tx; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBG_BYTES_TX.fields.bytes_tx
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - bytes_tx reset behavior matches SSOT value 0
  - bytes_tx access policy ro is implemented without read/write shortcuts
  - bytes_tx readback returns implemented RTL state when readable
  - bytes_tx write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBG_BYTES_TX.fields.bytes_tx

### RTL-0194: Implement CSR/register DBG_BYTES_RX

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBG_BYTES_RX
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBG_BYTES_RX.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=DBG_BYTES_RX; width=32; reset=0; access=ro; offset=36.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBG_BYTES_RX
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DBG_BYTES_RX width matches SSOT value 32
  - DBG_BYTES_RX reset behavior matches SSOT value 0
  - DBG_BYTES_RX access policy ro is implemented without read/write shortcuts
  - DBG_BYTES_RX decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.DBG_BYTES_RX

### RTL-0195: Implement field DBG_BYTES_RX.bytes_rx

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBG_BYTES_RX.fields.bytes_rx
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBG_BYTES_RX.fields.bytes_rx.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=bytes_rx; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBG_BYTES_RX.fields.bytes_rx
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - bytes_rx reset behavior matches SSOT value 0
  - bytes_rx access policy ro is implemented without read/write shortcuts
  - bytes_rx readback returns implemented RTL state when readable
  - bytes_rx write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBG_BYTES_RX.fields.bytes_rx

### RTL-0196: Implement CSR/register DBG_FRAMES_ERR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBG_FRAMES_ERR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBG_FRAMES_ERR.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=DBG_FRAMES_ERR; width=32; reset=0; access=ro; offset=40.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBG_FRAMES_ERR
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DBG_FRAMES_ERR width matches SSOT value 32
  - DBG_FRAMES_ERR reset behavior matches SSOT value 0
  - DBG_FRAMES_ERR access policy ro is implemented without read/write shortcuts
  - DBG_FRAMES_ERR decode uses SSOT address/offset 40
- SSOT refs: registers.register_list.DBG_FRAMES_ERR

### RTL-0197: Implement field DBG_FRAMES_ERR.frames_errored

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBG_FRAMES_ERR.fields.frames_errored
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBG_FRAMES_ERR.fields.frames_errored.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=frames_errored; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBG_FRAMES_ERR.fields.frames_errored
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - frames_errored reset behavior matches SSOT value 0
  - frames_errored access policy ro is implemented without read/write shortcuts
  - frames_errored readback returns implemented RTL state when readable
  - frames_errored write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBG_FRAMES_ERR.fields.frames_errored

### RTL-0198: Implement CSR/register DBG_PARITIES_ERR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBG_PARITIES_ERR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBG_PARITIES_ERR.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=DBG_PARITIES_ERR; width=32; reset=0; access=ro; offset=44.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBG_PARITIES_ERR
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - DBG_PARITIES_ERR width matches SSOT value 32
  - DBG_PARITIES_ERR reset behavior matches SSOT value 0
  - DBG_PARITIES_ERR access policy ro is implemented without read/write shortcuts
  - DBG_PARITIES_ERR decode uses SSOT address/offset 44
- SSOT refs: registers.register_list.DBG_PARITIES_ERR

### RTL-0199: Implement field DBG_PARITIES_ERR.parities_errored

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBG_PARITIES_ERR.fields.parities_errored
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBG_PARITIES_ERR.fields.parities_errored.
Owner: uart_lite_regs in rtl/uart_lite_regs.sv via registers.register_list.
SSOT item context: name=parities_errored; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBG_PARITIES_ERR.fields.parities_errored
  - Primary implementation evidence is in rtl/uart_lite_regs.sv
  - parities_errored reset behavior matches SSOT value 0
  - parities_errored access policy ro is implemented without read/write shortcuts
  - parities_errored readback returns implemented RTL state when readable
  - parities_errored write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBG_PARITIES_ERR.fields.parities_errored
