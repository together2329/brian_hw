# RTL Authoring Packet: module__pl330realverify_regs__registers

- Kind: module
- Owner module: pl330realverify_regs
- Owner file: rtl/pl330realverify_regs.sv
- Task count: 23
- Required tasks: 23

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
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: cycle_model.handshake_rules.APB_ACCESS, decomposition.units.apb_registers, error_handling, error_handling.error_sources, function_model.transactions.FM_APB_READ, function_model.transactions.FM_APB_WRITE, function_model.transactions.FM_IRQ_CLEAR, function_model.transactions.FM_RESET, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, rtl_contract, rtl_contract.input_map
- Module slice: 4/8 section=registers task_limit=48
- Slice rule: Owner module pl330realverify_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=12, min_logic_modules=6, min_modules=7, min_procedural_blocks=14, min_source_files=7, min_state_updates=20
- SSOT connection contracts:
  - pl330realverify_regs.clk_i <= dmaclk (sub_modules[0].connections[0])
  - pl330realverify_regs.rst_ni <= dmacresetn (sub_modules[0].connections[1])
  - pl330realverify_regs.paddr_i <= paddr (sub_modules[0].connections[2])
  - pl330realverify_regs.psel_i <= psel (sub_modules[0].connections[3])
  - pl330realverify_regs.penable_i <= penable (sub_modules[0].connections[4])
  - pl330realverify_regs.pwrite_i <= pwrite (sub_modules[0].connections[5])
  - pl330realverify_regs.pwdata_i <= pwdata (sub_modules[0].connections[6])
  - pl330realverify_regs.pstrb_i <= pstrb (sub_modules[0].connections[7])
  - pl330realverify_regs.prdata_o <= prdata (sub_modules[0].connections[8])
  - pl330realverify_regs.pready_o <= pready (sub_modules[0].connections[9])
  - pl330realverify_regs.pslverr_o <= pslverr (sub_modules[0].connections[10])
  - pl330realverify_regs.irq_o <= dmac_irq (sub_modules[0].connections[11])

## Tasks

### RTL-0233: Implement CSR/register DBGSTATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGSTATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGSTATUS.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=DBGSTATUS; width=32; reset=0; access=ro; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGSTATUS
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DBGSTATUS width matches SSOT value 32
  - DBGSTATUS reset behavior matches SSOT value 0
  - DBGSTATUS access policy ro is implemented without read/write shortcuts
  - DBGSTATUS decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.DBGSTATUS

### RTL-0234: Implement field DBGSTATUS.manager_busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBGSTATUS.fields.manager_busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGSTATUS.fields.manager_busy.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=manager_busy; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGSTATUS.fields.manager_busy
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - manager_busy reset behavior matches SSOT value 0
  - manager_busy access policy ro is implemented without read/write shortcuts
  - manager_busy readback returns implemented RTL state when readable
  - manager_busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGSTATUS.fields.manager_busy

### RTL-0235: Implement field DBGSTATUS.num_channels_minus1

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBGSTATUS.fields.num_channels_minus1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGSTATUS.fields.num_channels_minus1.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=num_channels_minus1; reset=7; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGSTATUS.fields.num_channels_minus1
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - num_channels_minus1 reset behavior matches SSOT value 7
  - num_channels_minus1 access policy ro is implemented without read/write shortcuts
  - num_channels_minus1 readback returns implemented RTL state when readable
  - num_channels_minus1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGSTATUS.fields.num_channels_minus1

### RTL-0236: Implement field DBGSTATUS.reserved_31_8

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DBGSTATUS.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGSTATUS.fields.reserved_31_8.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_8; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGSTATUS.fields.reserved_31_8
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - reserved_31_8 reset behavior matches SSOT value 0
  - reserved_31_8 access policy reserved is implemented without read/write shortcuts
  - reserved_31_8 readback returns implemented RTL state when readable
  - reserved_31_8 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGSTATUS.fields.reserved_31_8

### RTL-0237: Implement CSR/register DBGCMD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGCMD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGCMD.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=DBGCMD; width=32; reset=0; access=wo; offset=12.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGCMD
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DBGCMD width matches SSOT value 32
  - DBGCMD reset behavior matches SSOT value 0
  - DBGCMD access policy wo is implemented without read/write shortcuts
  - DBGCMD decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.DBGCMD

### RTL-0238: Implement field DBGCMD.dbgcmd

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBGCMD.fields.dbgcmd
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGCMD.fields.dbgcmd.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=dbgcmd; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGCMD.fields.dbgcmd
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - dbgcmd reset behavior matches SSOT value 0
  - dbgcmd access policy wo is implemented without read/write shortcuts
  - dbgcmd readback returns implemented RTL state when readable
  - dbgcmd write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGCMD.fields.dbgcmd

### RTL-0239: Implement field DBGCMD.channel

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DBGCMD.fields.channel
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGCMD.fields.channel.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=channel; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGCMD.fields.channel
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - channel reset behavior matches SSOT value 0
  - channel access policy wo is implemented without read/write shortcuts
  - channel readback returns implemented RTL state when readable
  - channel write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGCMD.fields.channel

### RTL-0240: Implement field DBGCMD.reserved_31_7

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DBGCMD.fields.reserved_31_7
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DBGCMD.fields.reserved_31_7.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_7; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DBGCMD.fields.reserved_31_7
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - reserved_31_7 reset behavior matches SSOT value 0
  - reserved_31_7 access policy reserved is implemented without read/write shortcuts
  - reserved_31_7 readback returns implemented RTL state when readable
  - reserved_31_7 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DBGCMD.fields.reserved_31_7

### RTL-0251: Implement CSR/register CSR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CSR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CSR.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=CSR; width=32; reset=0; access=ro; offset=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CSR
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - CSR width matches SSOT value 32
  - CSR reset behavior matches SSOT value 0
  - CSR access policy ro is implemented without read/write shortcuts
  - CSR decode uses SSOT address/offset 256
- SSOT refs: registers.register_list.CSR

### RTL-0252: Implement field CSR.ch_status

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CSR.fields.ch_status
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CSR.fields.ch_status.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=ch_status; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CSR.fields.ch_status
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - ch_status reset behavior matches SSOT value 0
  - ch_status access policy ro is implemented without read/write shortcuts
  - ch_status readback returns implemented RTL state when readable
  - ch_status write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CSR.fields.ch_status

### RTL-0253: Implement field CSR.error_code

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CSR.fields.error_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CSR.fields.error_code.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=error_code; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CSR.fields.error_code
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - error_code reset behavior matches SSOT value 0
  - error_code access policy ro is implemented without read/write shortcuts
  - error_code readback returns implemented RTL state when readable
  - error_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CSR.fields.error_code

### RTL-0254: Implement field CSR.loop_remaining

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CSR.fields.loop_remaining
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CSR.fields.loop_remaining.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=loop_remaining; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CSR.fields.loop_remaining
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - loop_remaining reset behavior matches SSOT value 0
  - loop_remaining access policy ro is implemented without read/write shortcuts
  - loop_remaining readback returns implemented RTL state when readable
  - loop_remaining write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CSR.fields.loop_remaining

### RTL-0255: Implement field CSR.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CSR.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CSR.fields.reserved_31_16.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CSR.fields.reserved_31_16
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CSR.fields.reserved_31_16

### RTL-0256: Implement CSR/register SAR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SAR.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=SAR; width=32; reset=0; access=rw; offset=264.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SAR
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - SAR width matches SSOT value 32
  - SAR reset behavior matches SSOT value 0
  - SAR access policy rw is implemented without read/write shortcuts
  - SAR decode uses SSOT address/offset 264
- SSOT refs: registers.register_list.SAR

### RTL-0257: Implement field SAR.src_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SAR.fields.src_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SAR.fields.src_addr.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=src_addr; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SAR.fields.src_addr
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - src_addr reset behavior matches SSOT value 0
  - src_addr access policy rw is implemented without read/write shortcuts
  - src_addr readback returns implemented RTL state when readable
  - src_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SAR.fields.src_addr

### RTL-0258: Implement CSR/register DAR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DAR.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=DAR; width=32; reset=0; access=rw; offset=268.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DAR
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - DAR width matches SSOT value 32
  - DAR reset behavior matches SSOT value 0
  - DAR access policy rw is implemented without read/write shortcuts
  - DAR decode uses SSOT address/offset 268
- SSOT refs: registers.register_list.DAR

### RTL-0259: Implement field DAR.dst_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DAR.fields.dst_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DAR.fields.dst_addr.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=dst_addr; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DAR.fields.dst_addr
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - dst_addr reset behavior matches SSOT value 0
  - dst_addr access policy rw is implemented without read/write shortcuts
  - dst_addr readback returns implemented RTL state when readable
  - dst_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DAR.fields.dst_addr

### RTL-0260: Implement CSR/register LOOP_CFG

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.LOOP_CFG
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.LOOP_CFG.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=LOOP_CFG; width=32; reset=0; access=rw; offset=272.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.LOOP_CFG
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - LOOP_CFG width matches SSOT value 32
  - LOOP_CFG reset behavior matches SSOT value 0
  - LOOP_CFG access policy rw is implemented without read/write shortcuts
  - LOOP_CFG decode uses SSOT address/offset 272
- SSOT refs: registers.register_list.LOOP_CFG

### RTL-0261: Implement field LOOP_CFG.loop_count

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.LOOP_CFG.fields.loop_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.LOOP_CFG.fields.loop_count.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=loop_count; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.LOOP_CFG.fields.loop_count
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - loop_count reset behavior matches SSOT value 0
  - loop_count access policy rw is implemented without read/write shortcuts
  - loop_count readback returns implemented RTL state when readable
  - loop_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.LOOP_CFG.fields.loop_count

### RTL-0262: Implement field LOOP_CFG.burst_len

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.LOOP_CFG.fields.burst_len
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.LOOP_CFG.fields.burst_len.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=burst_len; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.LOOP_CFG.fields.burst_len
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - burst_len reset behavior matches SSOT value 0
  - burst_len access policy rw is implemented without read/write shortcuts
  - burst_len readback returns implemented RTL state when readable
  - burst_len write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.LOOP_CFG.fields.burst_len

### RTL-0263: Implement field LOOP_CFG.reserved_31_12

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.LOOP_CFG.fields.reserved_31_12
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.LOOP_CFG.fields.reserved_31_12.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_12; reset=0; access=reserved.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.LOOP_CFG.fields.reserved_31_12
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - reserved_31_12 reset behavior matches SSOT value 0
  - reserved_31_12 access policy reserved is implemented without read/write shortcuts
  - reserved_31_12 readback returns implemented RTL state when readable
  - reserved_31_12 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.LOOP_CFG.fields.reserved_31_12

### RTL-0271: Implement CSR/register PC

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.PC
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PC.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=PC; width=32; reset=0; access=rw; offset=280.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PC
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - PC width matches SSOT value 32
  - PC reset behavior matches SSOT value 0
  - PC access policy rw is implemented without read/write shortcuts
  - PC decode uses SSOT address/offset 280
- SSOT refs: registers.register_list.PC

### RTL-0272: Implement field PC.pc_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.PC.fields.pc_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PC.fields.pc_addr.
Owner: pl330realverify_regs in rtl/pl330realverify_regs.sv via registers.register_list.
SSOT item context: name=pc_addr; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PC.fields.pc_addr
  - Primary implementation evidence is in rtl/pl330realverify_regs.sv
  - pc_addr reset behavior matches SSOT value 0
  - pc_addr access policy rw is implemented without read/write shortcuts
  - pc_addr readback returns implemented RTL state when readable
  - pc_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PC.fields.pc_addr
