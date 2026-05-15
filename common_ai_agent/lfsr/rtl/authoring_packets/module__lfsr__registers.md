# RTL Authoring Packet: module__lfsr__registers

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 14
- Required tasks: 14

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
- Owner refs: top_module, function_model, cycle_model
- Module slice: 8/13 section=registers task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0083: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/lfsr.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0084: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/lfsr.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0085: Implement field CTRL.auto_reload

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.auto_reload
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.auto_reload.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=auto_reload; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.auto_reload
  - Primary implementation evidence is in rtl/lfsr.sv
  - auto_reload reset behavior matches SSOT value 0
  - auto_reload access policy rw is implemented without read/write shortcuts
  - auto_reload readback returns implemented RTL state when readable
  - auto_reload write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.auto_reload

### RTL-0086: Implement field CTRL.reserved_31_2

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_2
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_2.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=reserved_31_2; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_2
  - Primary implementation evidence is in rtl/lfsr.sv
  - reserved_31_2 reset behavior matches SSOT value 0
  - reserved_31_2 access policy reserved is implemented without read/write shortcuts
  - reserved_31_2 readback returns implemented RTL state when readable
  - reserved_31_2 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_2

### RTL-0087: Implement CSR/register POLY

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.POLY
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.POLY.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=POLY; width=32; reset=DEFAULT_POLY; access=rw; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.POLY
  - Primary implementation evidence is in rtl/lfsr.sv
  - POLY width matches SSOT value 32
  - POLY reset behavior matches SSOT value DEFAULT_POLY
  - POLY access policy rw is implemented without read/write shortcuts
  - POLY decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.POLY

### RTL-0088: Implement field POLY.poly

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.POLY.fields.poly
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.POLY.fields.poly.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=poly; reset=DEFAULT_POLY; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.POLY.fields.poly
  - Primary implementation evidence is in rtl/lfsr.sv
  - poly reset behavior matches SSOT value DEFAULT_POLY
  - poly access policy rw is implemented without read/write shortcuts
  - poly readback returns implemented RTL state when readable
  - poly write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.POLY.fields.poly

### RTL-0089: Implement CSR/register SEED

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SEED
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SEED.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=SEED; width=32; reset=DEFAULT_SEED; access=rw; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SEED
  - Primary implementation evidence is in rtl/lfsr.sv
  - SEED width matches SSOT value 32
  - SEED reset behavior matches SSOT value DEFAULT_SEED
  - SEED access policy rw is implemented without read/write shortcuts
  - SEED decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.SEED

### RTL-0090: Implement field SEED.seed

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SEED.fields.seed
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SEED.fields.seed.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=seed; reset=DEFAULT_SEED; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SEED.fields.seed
  - Primary implementation evidence is in rtl/lfsr.sv
  - seed reset behavior matches SSOT value DEFAULT_SEED
  - seed access policy rw is implemented without read/write shortcuts
  - seed readback returns implemented RTL state when readable
  - seed write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SEED.fields.seed

### RTL-0091: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=12.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/lfsr.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.STATUS

### RTL-0092: Implement field STATUS.running

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.running
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.running.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=running; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.running
  - Primary implementation evidence is in rtl/lfsr.sv
  - running reset behavior matches SSOT value 0
  - running access policy ro is implemented without read/write shortcuts
  - running readback returns implemented RTL state when readable
  - running write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.running

### RTL-0093: Implement field STATUS.lockup

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.lockup
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.lockup.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=lockup; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.lockup
  - Primary implementation evidence is in rtl/lfsr.sv
  - lockup reset behavior matches SSOT value 0
  - lockup access policy ro is implemented without read/write shortcuts
  - lockup readback returns implemented RTL state when readable
  - lockup write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.lockup

### RTL-0094: Implement field STATUS.reserved_31_2

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_2
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_2.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=reserved_31_2; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_2
  - Primary implementation evidence is in rtl/lfsr.sv
  - reserved_31_2 reset behavior matches SSOT value 0
  - reserved_31_2 access policy reserved is implemented without read/write shortcuts
  - reserved_31_2 readback returns implemented RTL state when readable
  - reserved_31_2 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_2

### RTL-0095: Implement CSR/register PRBS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.PRBS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PRBS.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PRBS; width=32; reset=DEFAULT_SEED; access=ro; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PRBS
  - Primary implementation evidence is in rtl/lfsr.sv
  - PRBS width matches SSOT value 32
  - PRBS reset behavior matches SSOT value DEFAULT_SEED
  - PRBS access policy ro is implemented without read/write shortcuts
  - PRBS decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.PRBS

### RTL-0096: Implement field PRBS.prbs

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.PRBS.fields.prbs
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PRBS.fields.prbs.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=prbs; reset=DEFAULT_SEED; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PRBS.fields.prbs
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs reset behavior matches SSOT value DEFAULT_SEED
  - prbs access policy ro is implemented without read/write shortcuts
  - prbs readback returns implemented RTL state when readable
  - prbs write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PRBS.fields.prbs
