# RTL Authoring Packet: module__atcdmac100_core__registers

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
- Task count: 44
- Required tasks: 44

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
- LLM-actionable open tasks: 44
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, error_handling, features, fsm, function_model, interrupts, io_list, registers, test_requirements, traceability
- Module slice: 7/14 section=registers task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= hresetn (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0212: Implement CSR/register IdRev

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.IdRev
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.IdRev.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=IdRev; width=32; reset=0x01021012; access=RO; offset=0x00.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.IdRev
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - IdRev width matches SSOT value 32
  - IdRev reset behavior matches SSOT value 0x01021012
  - IdRev access policy RO is implemented without read/write shortcuts
  - IdRev decode uses SSOT address/offset 0x00
- SSOT refs: registers.register_list.IdRev

### RTL-0213: Implement field IdRev.ID

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IdRev.fields.ID
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IdRev.fields.ID.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ID; reset=0x01021; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IdRev.fields.ID
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ID reset behavior matches SSOT value 0x01021
  - ID access policy RO is implemented without read/write shortcuts
  - ID readback returns implemented RTL state when readable
  - ID write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IdRev.fields.ID

### RTL-0214: Implement field IdRev.RevMajor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IdRev.fields.RevMajor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IdRev.fields.RevMajor.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=RevMajor; reset=0x1; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IdRev.fields.RevMajor
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - RevMajor reset behavior matches SSOT value 0x1
  - RevMajor access policy RO is implemented without read/write shortcuts
  - RevMajor readback returns implemented RTL state when readable
  - RevMajor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IdRev.fields.RevMajor

### RTL-0215: Implement field IdRev.RevMinor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IdRev.fields.RevMinor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IdRev.fields.RevMinor.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=RevMinor; reset=0x2; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IdRev.fields.RevMinor
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - RevMinor reset behavior matches SSOT value 0x2
  - RevMinor access policy RO is implemented without read/write shortcuts
  - RevMinor readback returns implemented RTL state when readable
  - RevMinor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IdRev.fields.RevMinor

### RTL-0216: Implement CSR/register DMACfg

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DMACfg
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DMACfg.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DMACfg; width=32; reset=CONFIG; access=RO; offset=0x10.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DMACfg
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DMACfg width matches SSOT value 32
  - DMACfg reset behavior matches SSOT value CONFIG
  - DMACfg access policy RO is implemented without read/write shortcuts
  - DMACfg decode uses SSOT address/offset 0x10
- SSOT refs: registers.register_list.DMACfg

### RTL-0217: Implement field DMACfg.ChainXfr

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACfg.fields.ChainXfr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACfg.fields.ChainXfr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChainXfr; reset=CHAIN_TRANSFER_SUPPORT; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACfg.fields.ChainXfr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChainXfr reset behavior matches SSOT value CHAIN_TRANSFER_SUPPORT
  - ChainXfr access policy RO is implemented without read/write shortcuts
  - ChainXfr readback returns implemented RTL state when readable
  - ChainXfr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACfg.fields.ChainXfr

### RTL-0218: Implement field DMACfg.ReqSync

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACfg.fields.ReqSync
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACfg.fields.ReqSync.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ReqSync; reset=0x0; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACfg.fields.ReqSync
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ReqSync reset behavior matches SSOT value 0x0
  - ReqSync access policy RO is implemented without read/write shortcuts
  - ReqSync readback returns implemented RTL state when readable
  - ReqSync write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACfg.fields.ReqSync

### RTL-0219: Implement field DMACfg.ReqNum

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACfg.fields.ReqNum
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACfg.fields.ReqNum.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ReqNum; reset=REQ_ACK_NUM; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACfg.fields.ReqNum
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ReqNum reset behavior matches SSOT value REQ_ACK_NUM
  - ReqNum access policy RO is implemented without read/write shortcuts
  - ReqNum readback returns implemented RTL state when readable
  - ReqNum write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACfg.fields.ReqNum

### RTL-0220: Implement field DMACfg.FIFODepth

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACfg.fields.FIFODepth
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACfg.fields.FIFODepth.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=FIFODepth; reset=FIFO_DEPTH; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACfg.fields.FIFODepth
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - FIFODepth reset behavior matches SSOT value FIFO_DEPTH
  - FIFODepth access policy RO is implemented without read/write shortcuts
  - FIFODepth readback returns implemented RTL state when readable
  - FIFODepth write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACfg.fields.FIFODepth

### RTL-0221: Implement field DMACfg.ChannelNum

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACfg.fields.ChannelNum
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACfg.fields.ChannelNum.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChannelNum; reset=DMA_CH_NUM; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACfg.fields.ChannelNum
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChannelNum reset behavior matches SSOT value DMA_CH_NUM
  - ChannelNum access policy RO is implemented without read/write shortcuts
  - ChannelNum readback returns implemented RTL state when readable
  - ChannelNum write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACfg.fields.ChannelNum

### RTL-0222: Implement CSR/register DMACtrl

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DMACtrl
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DMACtrl.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DMACtrl; width=32; reset=0x0; access=WO; offset=0x20.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DMACtrl
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DMACtrl width matches SSOT value 32
  - DMACtrl reset behavior matches SSOT value 0x0
  - DMACtrl access policy WO is implemented without read/write shortcuts
  - DMACtrl decode uses SSOT address/offset 0x20
- SSOT refs: registers.register_list.DMACtrl

### RTL-0223: Implement field DMACtrl.Reset

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DMACtrl.fields.Reset
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DMACtrl.fields.Reset.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Reset; reset=0x0; access=WO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DMACtrl.fields.Reset
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Reset reset behavior matches SSOT value 0x0
  - Reset access policy WO is implemented without read/write shortcuts
  - Reset readback returns implemented RTL state when readable
  - Reset write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DMACtrl.fields.Reset

### RTL-0224: Implement CSR/register IntStatus

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.IntStatus
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.IntStatus.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=IntStatus; width=32; reset=0x0; access=R/W1C; offset=0x30.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.IntStatus
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - IntStatus width matches SSOT value 32
  - IntStatus reset behavior matches SSOT value 0x0
  - IntStatus access policy R/W1C is implemented without read/write shortcuts
  - IntStatus decode uses SSOT address/offset 0x30
- SSOT refs: registers.register_list.IntStatus

### RTL-0225: Implement field IntStatus.TC

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IntStatus.fields.TC
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IntStatus.fields.TC.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=TC; reset=0x0; access=R/W1C.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IntStatus.fields.TC
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - TC reset behavior matches SSOT value 0x0
  - TC access policy R/W1C is implemented without read/write shortcuts
  - TC readback returns implemented RTL state when readable
  - TC write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IntStatus.fields.TC

### RTL-0226: Implement field IntStatus.Abort

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IntStatus.fields.Abort
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IntStatus.fields.Abort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Abort; reset=0x0; access=R/W1C.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IntStatus.fields.Abort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Abort reset behavior matches SSOT value 0x0
  - Abort access policy R/W1C is implemented without read/write shortcuts
  - Abort readback returns implemented RTL state when readable
  - Abort write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IntStatus.fields.Abort

### RTL-0227: Implement field IntStatus.Error

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.IntStatus.fields.Error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.IntStatus.fields.Error.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Error; reset=0x0; access=R/W1C.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.IntStatus.fields.Error
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Error reset behavior matches SSOT value 0x0
  - Error access policy R/W1C is implemented without read/write shortcuts
  - Error readback returns implemented RTL state when readable
  - Error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.IntStatus.fields.Error

### RTL-0228: Implement CSR/register ChEN

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChEN.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChEN; width=32; reset=0x0; access=RO; offset=0x34.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChEN
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChEN width matches SSOT value 32
  - ChEN reset behavior matches SSOT value 0x0
  - ChEN access policy RO is implemented without read/write shortcuts
  - ChEN decode uses SSOT address/offset 0x34
- SSOT refs: registers.register_list.ChEN

### RTL-0229: Implement field ChEN.ChEN

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChEN.fields.ChEN
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChEN.fields.ChEN.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChEN; reset=0x0; access=RO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChEN.fields.ChEN
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChEN reset behavior matches SSOT value 0x0
  - ChEN access policy RO is implemented without read/write shortcuts
  - ChEN readback returns implemented RTL state when readable
  - ChEN write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChEN.fields.ChEN

### RTL-0230: Implement CSR/register ChAbort

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChAbort
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChAbort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChAbort; width=32; reset=0x0; access=WO; offset=0x40.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChAbort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChAbort width matches SSOT value 32
  - ChAbort reset behavior matches SSOT value 0x0
  - ChAbort access policy WO is implemented without read/write shortcuts
  - ChAbort decode uses SSOT address/offset 0x40
- SSOT refs: registers.register_list.ChAbort

### RTL-0231: Implement field ChAbort.ChAbort

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChAbort.fields.ChAbort
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChAbort.fields.ChAbort.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChAbort; reset=0x0; access=WO.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChAbort.fields.ChAbort
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChAbort reset behavior matches SSOT value 0x0
  - ChAbort access policy WO is implemented without read/write shortcuts
  - ChAbort readback returns implemented RTL state when readable
  - ChAbort write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChAbort.fields.ChAbort

### RTL-0232: Implement CSR/register ChnCtrl

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChnCtrl
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChnCtrl.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChnCtrl; width=32; reset=0x000A0000; access=R/W; offset=0x44+n*0x14.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChnCtrl
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChnCtrl width matches SSOT value 32
  - ChnCtrl reset behavior matches SSOT value 0x000A0000
  - ChnCtrl access policy R/W is implemented without read/write shortcuts
  - ChnCtrl decode uses SSOT address/offset 0x44+n*0x14
- SSOT refs: registers.register_list.ChnCtrl

### RTL-0233: Implement field ChnCtrl.Priority

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.Priority
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.Priority.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Priority; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.Priority
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Priority reset behavior matches SSOT value 0x0
  - Priority access policy R/W is implemented without read/write shortcuts
  - Priority readback returns implemented RTL state when readable
  - Priority write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.Priority

### RTL-0234: Implement field ChnCtrl.SrcBurstSize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.SrcBurstSize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.SrcBurstSize.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcBurstSize; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.SrcBurstSize
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcBurstSize reset behavior matches SSOT value 0x0
  - SrcBurstSize access policy R/W is implemented without read/write shortcuts
  - SrcBurstSize readback returns implemented RTL state when readable
  - SrcBurstSize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.SrcBurstSize

### RTL-0235: Implement field ChnCtrl.SrcWidth

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.SrcWidth
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.SrcWidth.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcWidth; reset=0x2; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.SrcWidth
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcWidth reset behavior matches SSOT value 0x2
  - SrcWidth access policy R/W is implemented without read/write shortcuts
  - SrcWidth readback returns implemented RTL state when readable
  - SrcWidth write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.SrcWidth

### RTL-0236: Implement field ChnCtrl.DstWidth

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.DstWidth
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.DstWidth.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DstWidth; reset=0x2; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.DstWidth
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DstWidth reset behavior matches SSOT value 0x2
  - DstWidth access policy R/W is implemented without read/write shortcuts
  - DstWidth readback returns implemented RTL state when readable
  - DstWidth write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.DstWidth

### RTL-0237: Implement field ChnCtrl.SrcMode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.SrcMode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.SrcMode.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcMode; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.SrcMode
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcMode reset behavior matches SSOT value 0x0
  - SrcMode access policy R/W is implemented without read/write shortcuts
  - SrcMode readback returns implemented RTL state when readable
  - SrcMode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.SrcMode

### RTL-0238: Implement field ChnCtrl.DstMode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.DstMode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.DstMode.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DstMode; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.DstMode
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DstMode reset behavior matches SSOT value 0x0
  - DstMode access policy R/W is implemented without read/write shortcuts
  - DstMode readback returns implemented RTL state when readable
  - DstMode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.DstMode

### RTL-0239: Implement field ChnCtrl.SrcAddrCtrl

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.SrcAddrCtrl
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.SrcAddrCtrl.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcAddrCtrl; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.SrcAddrCtrl
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcAddrCtrl reset behavior matches SSOT value 0x0
  - SrcAddrCtrl access policy R/W is implemented without read/write shortcuts
  - SrcAddrCtrl readback returns implemented RTL state when readable
  - SrcAddrCtrl write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.SrcAddrCtrl

### RTL-0240: Implement field ChnCtrl.DstAddrCtrl

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.DstAddrCtrl
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.DstAddrCtrl.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DstAddrCtrl; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.DstAddrCtrl
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DstAddrCtrl reset behavior matches SSOT value 0x0
  - DstAddrCtrl access policy R/W is implemented without read/write shortcuts
  - DstAddrCtrl readback returns implemented RTL state when readable
  - DstAddrCtrl write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.DstAddrCtrl

### RTL-0241: Implement field ChnCtrl.SrcReqSel

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.SrcReqSel
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.SrcReqSel.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcReqSel; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.SrcReqSel
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcReqSel reset behavior matches SSOT value 0x0
  - SrcReqSel access policy R/W is implemented without read/write shortcuts
  - SrcReqSel readback returns implemented RTL state when readable
  - SrcReqSel write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.SrcReqSel

### RTL-0242: Implement field ChnCtrl.DstReqSel

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.DstReqSel
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.DstReqSel.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DstReqSel; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.DstReqSel
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DstReqSel reset behavior matches SSOT value 0x0
  - DstReqSel access policy R/W is implemented without read/write shortcuts
  - DstReqSel readback returns implemented RTL state when readable
  - DstReqSel write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.DstReqSel

### RTL-0243: Implement field ChnCtrl.IntAbtMask

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.IntAbtMask
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.IntAbtMask.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=IntAbtMask; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.IntAbtMask
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - IntAbtMask reset behavior matches SSOT value 0x0
  - IntAbtMask access policy R/W is implemented without read/write shortcuts
  - IntAbtMask readback returns implemented RTL state when readable
  - IntAbtMask write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.IntAbtMask

### RTL-0244: Implement field ChnCtrl.IntErrMask

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.IntErrMask
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.IntErrMask.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=IntErrMask; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.IntErrMask
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - IntErrMask reset behavior matches SSOT value 0x0
  - IntErrMask access policy R/W is implemented without read/write shortcuts
  - IntErrMask readback returns implemented RTL state when readable
  - IntErrMask write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.IntErrMask

### RTL-0245: Implement field ChnCtrl.IntTCMask

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.IntTCMask
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.IntTCMask.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=IntTCMask; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.IntTCMask
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - IntTCMask reset behavior matches SSOT value 0x0
  - IntTCMask access policy R/W is implemented without read/write shortcuts
  - IntTCMask readback returns implemented RTL state when readable
  - IntTCMask write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.IntTCMask

### RTL-0246: Implement field ChnCtrl.Enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnCtrl.fields.Enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnCtrl.fields.Enable.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Enable; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnCtrl.fields.Enable
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Enable reset behavior matches SSOT value 0x0
  - Enable access policy R/W is implemented without read/write shortcuts
  - Enable readback returns implemented RTL state when readable
  - Enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnCtrl.fields.Enable

### RTL-0247: Implement CSR/register ChnSrcAddr

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChnSrcAddr
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChnSrcAddr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChnSrcAddr; width=32; reset=0x0; access=R/W; offset=0x48+n*0x14.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChnSrcAddr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChnSrcAddr width matches SSOT value 32
  - ChnSrcAddr reset behavior matches SSOT value 0x0
  - ChnSrcAddr access policy R/W is implemented without read/write shortcuts
  - ChnSrcAddr decode uses SSOT address/offset 0x48+n*0x14
- SSOT refs: registers.register_list.ChnSrcAddr

### RTL-0248: Implement field ChnSrcAddr.SrcAddr

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnSrcAddr.fields.SrcAddr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnSrcAddr.fields.SrcAddr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=SrcAddr; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnSrcAddr.fields.SrcAddr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - SrcAddr reset behavior matches SSOT value 0x0
  - SrcAddr access policy R/W is implemented without read/write shortcuts
  - SrcAddr readback returns implemented RTL state when readable
  - SrcAddr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnSrcAddr.fields.SrcAddr

### RTL-0249: Implement CSR/register ChnDstAddr

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChnDstAddr
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChnDstAddr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChnDstAddr; width=32; reset=0x0; access=R/W; offset=0x4C+n*0x14.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChnDstAddr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChnDstAddr width matches SSOT value 32
  - ChnDstAddr reset behavior matches SSOT value 0x0
  - ChnDstAddr access policy R/W is implemented without read/write shortcuts
  - ChnDstAddr decode uses SSOT address/offset 0x4C+n*0x14
- SSOT refs: registers.register_list.ChnDstAddr

### RTL-0250: Implement field ChnDstAddr.DstAddr

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnDstAddr.fields.DstAddr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnDstAddr.fields.DstAddr.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=DstAddr; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnDstAddr.fields.DstAddr
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - DstAddr reset behavior matches SSOT value 0x0
  - DstAddr access policy R/W is implemented without read/write shortcuts
  - DstAddr readback returns implemented RTL state when readable
  - DstAddr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnDstAddr.fields.DstAddr

### RTL-0251: Implement CSR/register ChnTranSize

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChnTranSize
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChnTranSize.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChnTranSize; width=32; reset=0x0; access=R/W; offset=0x50+n*0x14.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChnTranSize
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChnTranSize width matches SSOT value 32
  - ChnTranSize reset behavior matches SSOT value 0x0
  - ChnTranSize access policy R/W is implemented without read/write shortcuts
  - ChnTranSize decode uses SSOT address/offset 0x50+n*0x14
- SSOT refs: registers.register_list.ChnTranSize

### RTL-0252: Implement field ChnTranSize.TranSize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnTranSize.fields.TranSize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnTranSize.fields.TranSize.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=TranSize; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnTranSize.fields.TranSize
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - TranSize reset behavior matches SSOT value 0x0
  - TranSize access policy R/W is implemented without read/write shortcuts
  - TranSize readback returns implemented RTL state when readable
  - TranSize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnTranSize.fields.TranSize

### RTL-0253: Implement CSR/register ChnLLPointer

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ChnLLPointer
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ChnLLPointer.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=ChnLLPointer; width=32; reset=0x0; access=R/W; offset=0x54+n*0x14.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ChnLLPointer
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - ChnLLPointer width matches SSOT value 32
  - ChnLLPointer reset behavior matches SSOT value 0x0
  - ChnLLPointer access policy R/W is implemented without read/write shortcuts
  - ChnLLPointer decode uses SSOT address/offset 0x54+n*0x14
- SSOT refs: registers.register_list.ChnLLPointer

### RTL-0254: Implement field ChnLLPointer.LLPointer

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnLLPointer.fields.LLPointer
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnLLPointer.fields.LLPointer.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=LLPointer; reset=0x0; access=R/W.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnLLPointer.fields.LLPointer
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - LLPointer reset behavior matches SSOT value 0x0
  - LLPointer access policy R/W is implemented without read/write shortcuts
  - LLPointer readback returns implemented RTL state when readable
  - LLPointer write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnLLPointer.fields.LLPointer

### RTL-0255: Implement field ChnLLPointer.Reserved

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ChnLLPointer.fields.Reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ChnLLPointer.fields.Reserved.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via registers.
SSOT item context: name=Reserved; reset=0x0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/atcdmac100_core.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ChnLLPointer.fields.Reserved
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Reserved reset behavior matches SSOT value 0x0
  - Reserved access policy reserved is implemented without read/write shortcuts
  - Reserved readback returns implemented RTL state when readable
  - Reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ChnLLPointer.fields.Reserved
