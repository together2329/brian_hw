# RTL Authoring Packet: module__atcwdt200_regs__registers

- Kind: module
- Owner module: atcwdt200_regs
- Owner file: rtl/atcwdt200_regs.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, dataflow.sinks.sinks_0, decomposition.units.apb_register_block, error_handling, function_model, function_model.transactions.apb_read, function_model.transactions.apb_write, function_model.transactions.write_unlock, registers, registers.register_list
- Module slice: 2/5 section=registers task_limit=48
- Slice rule: Owner module atcwdt200_regs is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcwdt200_regs.pclk <= pclk (integration.connections[0])
  - atcwdt200_regs.presetn <= presetn (integration.connections[1])

## Tasks

### RTL-0136: Implement CSR/register VER

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.VER
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.VER.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=VER; width=32; reset=50339842; access=ro; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.VER
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - VER width matches SSOT value 32
  - VER reset behavior matches SSOT value 50339842
  - VER access policy ro is implemented without read/write shortcuts
  - VER decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.VER

### RTL-0137: Implement field VER.id

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.VER.fields.id
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.VER.fields.id.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=id; reset=768; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.VER.fields.id
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - id reset behavior matches SSOT value 768
  - id access policy ro is implemented without read/write shortcuts
  - id readback returns implemented RTL state when readable
  - id write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.VER.fields.id

### RTL-0138: Implement field VER.rev_major

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.VER.fields.rev_major
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.VER.fields.rev_major.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=rev_major; reset=512; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.VER.fields.rev_major
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - rev_major reset behavior matches SSOT value 512
  - rev_major access policy ro is implemented without read/write shortcuts
  - rev_major readback returns implemented RTL state when readable
  - rev_major write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.VER.fields.rev_major

### RTL-0139: Implement field VER.rev_minor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.VER.fields.rev_minor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.VER.fields.rev_minor.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=rev_minor; reset=2; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.VER.fields.rev_minor
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - rev_minor reset behavior matches SSOT value 2
  - rev_minor access policy ro is implemented without read/write shortcuts
  - rev_minor readback returns implemented RTL state when readable
  - rev_minor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.VER.fields.rev_minor

### RTL-0140: Implement CSR/register CR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CR.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=CR; width=32; reset=0; access=rw; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CR
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - CR width matches SSOT value 32
  - CR reset behavior matches SSOT value 0
  - CR access policy rw is implemented without read/write shortcuts
  - CR decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.CR

### RTL-0141: Implement field CR.en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.en.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=en; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.en
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - en reset behavior matches SSOT value 0
  - en access policy rw is implemented without read/write shortcuts
  - en readback returns implemented RTL state when readable
  - en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.en

### RTL-0142: Implement field CR.clk

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.clk
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.clk.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=clk; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.clk
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - clk reset behavior matches SSOT value 0
  - clk access policy rw is implemented without read/write shortcuts
  - clk readback returns implemented RTL state when readable
  - clk write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.clk

### RTL-0143: Implement field CR.inten

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.inten
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.inten.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=inten; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.inten
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - inten reset behavior matches SSOT value 0
  - inten access policy rw is implemented without read/write shortcuts
  - inten readback returns implemented RTL state when readable
  - inten write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.inten

### RTL-0144: Implement field CR.rsten

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.rsten
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.rsten.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=rsten; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.rsten
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - rsten reset behavior matches SSOT value 0
  - rsten access policy rw is implemented without read/write shortcuts
  - rsten readback returns implemented RTL state when readable
  - rsten write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.rsten

### RTL-0145: Implement field CR.inttime

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.inttime
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.inttime.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=inttime; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.inttime
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - inttime reset behavior matches SSOT value 0
  - inttime access policy rw is implemented without read/write shortcuts
  - inttime readback returns implemented RTL state when readable
  - inttime write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.inttime

### RTL-0146: Implement field CR.rsttime

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CR.fields.rsttime
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.rsttime.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=rsttime; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.rsttime
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - rsttime reset behavior matches SSOT value 0
  - rsttime access policy rw is implemented without read/write shortcuts
  - rsttime readback returns implemented RTL state when readable
  - rsttime write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.rsttime

### RTL-0147: Implement field CR.reserved_31_11

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CR.fields.reserved_31_11
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CR.fields.reserved_31_11.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_11; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CR.fields.reserved_31_11
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - reserved_31_11 reset behavior matches SSOT value 0
  - reserved_31_11 access policy reserved is implemented without read/write shortcuts
  - reserved_31_11 readback returns implemented RTL state when readable
  - reserved_31_11 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CR.fields.reserved_31_11

### RTL-0148: Implement CSR/register RES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.RES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.RES.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=RES; width=32; reset=0; access=wo; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.RES
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - RES width matches SSOT value 32
  - RES reset behavior matches SSOT value 0
  - RES access policy wo is implemented without read/write shortcuts
  - RES decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.RES

### RTL-0149: Implement field RES.restart_magic

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.RES.fields.restart_magic
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RES.fields.restart_magic.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=restart_magic; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.RES.fields.restart_magic
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - restart_magic reset behavior matches SSOT value 0
  - restart_magic access policy wo is implemented without read/write shortcuts
  - restart_magic readback returns implemented RTL state when readable
  - restart_magic write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.RES.fields.restart_magic

### RTL-0150: Implement field RES.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.RES.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.RES.fields.reserved_31_16.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.RES.fields.reserved_31_16
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.RES.fields.reserved_31_16

### RTL-0151: Implement CSR/register WEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.WEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.WEN.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=WEN; width=32; reset=0; access=wo; offset=24.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.WEN
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - WEN width matches SSOT value 32
  - WEN reset behavior matches SSOT value 0
  - WEN access policy wo is implemented without read/write shortcuts
  - WEN decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.WEN

### RTL-0152: Implement field WEN.unlock_magic

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.WEN.fields.unlock_magic
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.WEN.fields.unlock_magic.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=unlock_magic; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.WEN.fields.unlock_magic
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - unlock_magic reset behavior matches SSOT value 0
  - unlock_magic access policy wo is implemented without read/write shortcuts
  - unlock_magic readback returns implemented RTL state when readable
  - unlock_magic write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.WEN.fields.unlock_magic

### RTL-0153: Implement field WEN.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.WEN.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.WEN.fields.reserved_31_16.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.WEN.fields.reserved_31_16
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.WEN.fields.reserved_31_16

### RTL-0154: Implement CSR/register SR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SR.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=SR; width=32; reset=0; access=rw1c; offset=28.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SR
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - SR width matches SSOT value 32
  - SR reset behavior matches SSOT value 0
  - SR access policy rw1c is implemented without read/write shortcuts
  - SR decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.SR

### RTL-0155: Implement field SR.intzero

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SR.fields.intzero
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SR.fields.intzero.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=intzero; reset=0; access=rw1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SR.fields.intzero
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - intzero reset behavior matches SSOT value 0
  - intzero access policy rw1c is implemented without read/write shortcuts
  - intzero readback returns implemented RTL state when readable
  - intzero write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SR.fields.intzero

### RTL-0156: Implement field SR.reserved_31_1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.SR.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SR.fields.reserved_31_1.
Owner: atcwdt200_regs in rtl/atcwdt200_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SR.fields.reserved_31_1
  - Primary implementation evidence is in rtl/atcwdt200_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SR.fields.reserved_31_1
