# RTL Authoring Packet: module__pl330_target_mfifo__registers

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 19
- Required tasks: 19

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
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
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 5/11 section=registers task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_mfifo.cfg_nonsecure_allowed_i <= mfifo_cfg_nonsecure_allowed_i (observed_named_port_map)
  - pl330_target_mfifo.channel_pc_o <= mfifo_channel_pc_o (observed_named_port_map)
  - pl330_target_mfifo.channel_state_o <= mfifo_channel_state_o (observed_named_port_map)
  - pl330_target_mfifo.clk <= clk (observed_named_port_map)
  - pl330_target_mfifo.cmd_accept_o <= mfifo_cmd_accept_o (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_addr_i <= mfifo_cmd_arg_addr_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_data_i <= mfifo_cmd_arg_data_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_error_o <= mfifo_cmd_error_o (observed_named_port_map)

## Tasks

### RTL-0191: Implement CSR/register DSR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DSR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DSR.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DSR; reset=0; access=RO; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DSR
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DSR reset behavior matches SSOT value 0
  - DSR access policy RO is implemented without read/write shortcuts
  - DSR decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.DSR

### RTL-0192: Implement CSR/register DPC

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DPC
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DPC.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DPC; reset=0; access=RO; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DPC
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DPC reset behavior matches SSOT value 0
  - DPC access policy RO is implemented without read/write shortcuts
  - DPC decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.DPC

### RTL-0193: Implement CSR/register INTEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INTEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTEN.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=INTEN; reset=0; access=RW; offset=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTEN
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - INTEN reset behavior matches SSOT value 0
  - INTEN access policy RW is implemented without read/write shortcuts
  - INTEN decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.INTEN

### RTL-0194: Implement CSR/register INT_EVENT_RIS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_EVENT_RIS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_EVENT_RIS.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=INT_EVENT_RIS; reset=0; access=RO; offset=36.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_EVENT_RIS
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - INT_EVENT_RIS reset behavior matches SSOT value 0
  - INT_EVENT_RIS access policy RO is implemented without read/write shortcuts
  - INT_EVENT_RIS decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.INT_EVENT_RIS

### RTL-0195: Implement CSR/register INTMIS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INTMIS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTMIS.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=INTMIS; reset=0; access=RO; offset=40.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTMIS
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - INTMIS reset behavior matches SSOT value 0
  - INTMIS access policy RO is implemented without read/write shortcuts
  - INTMIS decode uses SSOT address/offset 40
- SSOT refs: registers.register_list.INTMIS

### RTL-0196: Implement CSR/register INTCLR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INTCLR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTCLR.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=INTCLR; reset=0; access=WO; offset=44.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTCLR
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - INTCLR reset behavior matches SSOT value 0
  - INTCLR access policy WO is implemented without read/write shortcuts
  - INTCLR decode uses SSOT address/offset 44
- SSOT refs: registers.register_list.INTCLR

### RTL-0197: Implement CSR/register FSRD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.FSRD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.FSRD.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=FSRD; reset=0; access=RO; offset=48.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.FSRD
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - FSRD reset behavior matches SSOT value 0
  - FSRD access policy RO is implemented without read/write shortcuts
  - FSRD decode uses SSOT address/offset 48
- SSOT refs: registers.register_list.FSRD

### RTL-0198: Implement CSR/register FSRC

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.FSRC
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.FSRC.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=FSRC; reset=0; access=RO; offset=52.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.FSRC
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - FSRC reset behavior matches SSOT value 0
  - FSRC access policy RO is implemented without read/write shortcuts
  - FSRC decode uses SSOT address/offset 52
- SSOT refs: registers.register_list.FSRC

### RTL-0199: Implement CSR/register FTRD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.FTRD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.FTRD.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=FTRD; reset=0; access=RO; offset=56.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.FTRD
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - FTRD reset behavior matches SSOT value 0
  - FTRD access policy RO is implemented without read/write shortcuts
  - FTRD decode uses SSOT address/offset 56
- SSOT refs: registers.register_list.FTRD

### RTL-0200: Implement CSR/register CSR_chan_n

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CSR_chan_n
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CSR_chan_n.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=CSR_chan_n; reset=0; access=RO; offset=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CSR_chan_n
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - CSR_chan_n reset behavior matches SSOT value 0
  - CSR_chan_n access policy RO is implemented without read/write shortcuts
  - CSR_chan_n decode uses SSOT address/offset 256
- SSOT refs: registers.register_list.CSR_chan_n

### RTL-0201: Implement CSR/register CPC_chan_n

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CPC_chan_n
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CPC_chan_n.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=CPC_chan_n; reset=0; access=RO; offset=260.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CPC_chan_n
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - CPC_chan_n reset behavior matches SSOT value 0
  - CPC_chan_n access policy RO is implemented without read/write shortcuts
  - CPC_chan_n decode uses SSOT address/offset 260
- SSOT refs: registers.register_list.CPC_chan_n

### RTL-0202: Implement CSR/register SAR_chan_n

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SAR_chan_n
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SAR_chan_n.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=SAR_chan_n; reset=0; access=RW; offset=1024.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SAR_chan_n
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - SAR_chan_n reset behavior matches SSOT value 0
  - SAR_chan_n access policy RW is implemented without read/write shortcuts
  - SAR_chan_n decode uses SSOT address/offset 1024
- SSOT refs: registers.register_list.SAR_chan_n

### RTL-0203: Implement CSR/register DAR_chan_n

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DAR_chan_n
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DAR_chan_n.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DAR_chan_n; reset=0; access=RW; offset=1028.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DAR_chan_n
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DAR_chan_n reset behavior matches SSOT value 0
  - DAR_chan_n access policy RW is implemented without read/write shortcuts
  - DAR_chan_n decode uses SSOT address/offset 1028
- SSOT refs: registers.register_list.DAR_chan_n

### RTL-0204: Implement CSR/register CCR_chan_n

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CCR_chan_n
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CCR_chan_n.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=CCR_chan_n; reset=0; access=RW; offset=1032.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CCR_chan_n
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - CCR_chan_n reset behavior matches SSOT value 0
  - CCR_chan_n access policy RW is implemented without read/write shortcuts
  - CCR_chan_n decode uses SSOT address/offset 1032
- SSOT refs: registers.register_list.CCR_chan_n

### RTL-0205: Implement CSR/register DBGSTATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGSTATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGSTATUS.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DBGSTATUS; reset=0; access=RO; offset=3328.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGSTATUS
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DBGSTATUS reset behavior matches SSOT value 0
  - DBGSTATUS access policy RO is implemented without read/write shortcuts
  - DBGSTATUS decode uses SSOT address/offset 3328
- SSOT refs: registers.register_list.DBGSTATUS

### RTL-0206: Implement CSR/register DBGCMD

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGCMD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGCMD.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DBGCMD; reset=0; access=WO; offset=3332.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGCMD
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DBGCMD reset behavior matches SSOT value 0
  - DBGCMD access policy WO is implemented without read/write shortcuts
  - DBGCMD decode uses SSOT address/offset 3332
- SSOT refs: registers.register_list.DBGCMD

### RTL-0207: Implement CSR/register DBGINST0

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGINST0
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGINST0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DBGINST0; reset=0; access=WO; offset=3336.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGINST0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DBGINST0 reset behavior matches SSOT value 0
  - DBGINST0 access policy WO is implemented without read/write shortcuts
  - DBGINST0 decode uses SSOT address/offset 3336
- SSOT refs: registers.register_list.DBGINST0

### RTL-0208: Implement CSR/register DBGINST1

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DBGINST1
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DBGINST1.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=DBGINST1; reset=0; access=WO; offset=3340.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DBGINST1
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - DBGINST1 reset behavior matches SSOT value 0
  - DBGINST1 access policy WO is implemented without read/write shortcuts
  - DBGINST1 decode uses SSOT address/offset 3340
- SSOT refs: registers.register_list.DBGINST1

### RTL-0209: Implement CSR/register CR0

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CR0
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CR0.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via registers.
SSOT item context: name=CR0; reset=0; access=RO; offset=3584.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CR0
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - CR0 reset behavior matches SSOT value 0
  - CR0 access policy RO is implemented without read/write shortcuts
  - CR0 decode uses SSOT address/offset 3584
- SSOT refs: registers.register_list.CR0
