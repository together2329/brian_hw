# RTL Authoring Packet: module__dma_real_apb_cfg__registers_01

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 14
- Human-locked open tasks: 0
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 3/8 section=registers task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0194: Implement CSR/register GLOBAL_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.GLOBAL_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.GLOBAL_CTRL.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=GLOBAL_CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - GLOBAL_CTRL width matches SSOT value 32
  - GLOBAL_CTRL reset behavior matches SSOT value 0
  - GLOBAL_CTRL access policy rw is implemented without read/write shortcuts
  - GLOBAL_CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.GLOBAL_CTRL

### RTL-0195: Implement field GLOBAL_CTRL.dma_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.dma_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.dma_en.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=dma_en; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.dma_en
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dma_en width matches SSOT value 1
  - dma_en reset behavior matches SSOT value 0
  - dma_en access policy rw is implemented without read/write shortcuts
  - dma_en readback returns implemented RTL state when readable
  - dma_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.dma_en

### RTL-0196: Implement field GLOBAL_CTRL.reserved_31_1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_CTRL.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_CTRL.fields.reserved_31_1.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_1; width=31; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_CTRL.fields.reserved_31_1
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_1 width matches SSOT value 31
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy rw is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_CTRL.fields.reserved_31_1

### RTL-0197: Implement CSR/register INT_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_STATUS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=INT_STATUS; width=32; reset=0; access=ro; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_STATUS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - INT_STATUS width matches SSOT value 32
  - INT_STATUS reset behavior matches SSOT value 0
  - INT_STATUS access policy ro is implemented without read/write shortcuts
  - INT_STATUS decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.INT_STATUS

### RTL-0198: Implement field INT_STATUS.ch_status

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_STATUS.fields.ch_status
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_STATUS.fields.ch_status.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_status; width=4; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_STATUS.fields.ch_status
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_status width matches SSOT value 4
  - ch_status reset behavior matches SSOT value 0
  - ch_status access policy ro is implemented without read/write shortcuts
  - ch_status readback returns implemented RTL state when readable
  - ch_status write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_STATUS.fields.ch_status

### RTL-0199: Implement CSR/register INT_ENABLE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_ENABLE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_ENABLE.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=INT_ENABLE; width=32; reset=0; access=rw; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_ENABLE
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - INT_ENABLE width matches SSOT value 32
  - INT_ENABLE reset behavior matches SSOT value 0
  - INT_ENABLE access policy rw is implemented without read/write shortcuts
  - INT_ENABLE decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.INT_ENABLE

### RTL-0200: Implement field INT_ENABLE.ch_enable

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_ENABLE.fields.ch_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_ENABLE.fields.ch_enable.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_enable; width=4; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_ENABLE.fields.ch_enable
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_enable width matches SSOT value 4
  - ch_enable reset behavior matches SSOT value 0
  - ch_enable access policy rw is implemented without read/write shortcuts
  - ch_enable readback returns implemented RTL state when readable
  - ch_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_ENABLE.fields.ch_enable

### RTL-0201: Implement CSR/register INT_CLEAR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.INT_CLEAR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_CLEAR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=INT_CLEAR; width=32; reset=0; access=wo; offset=12.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_CLEAR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - INT_CLEAR width matches SSOT value 32
  - INT_CLEAR reset behavior matches SSOT value 0
  - INT_CLEAR access policy wo is implemented without read/write shortcuts
  - INT_CLEAR decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.INT_CLEAR

### RTL-0202: Implement field INT_CLEAR.ch_clear

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.INT_CLEAR.fields.ch_clear
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_CLEAR.fields.ch_clear.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_clear; width=4; reset=0; access=wo.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_CLEAR.fields.ch_clear
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_clear width matches SSOT value 4
  - ch_clear reset behavior matches SSOT value 0
  - ch_clear access policy wo is implemented without read/write shortcuts
  - ch_clear readback returns implemented RTL state when readable
  - ch_clear write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_CLEAR.fields.ch_clear

### RTL-0203: Implement CSR/register GLOBAL_TIMEOUT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.GLOBAL_TIMEOUT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.GLOBAL_TIMEOUT.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=GLOBAL_TIMEOUT; width=32; reset=1024; access=rw; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.GLOBAL_TIMEOUT
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - GLOBAL_TIMEOUT width matches SSOT value 32
  - GLOBAL_TIMEOUT reset behavior matches SSOT value 1024
  - GLOBAL_TIMEOUT access policy rw is implemented without read/write shortcuts
  - GLOBAL_TIMEOUT decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.GLOBAL_TIMEOUT

### RTL-0204: Implement field GLOBAL_TIMEOUT.timeout_val

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_TIMEOUT.fields.timeout_val
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_TIMEOUT.fields.timeout_val.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=timeout_val; width=16; reset=1024; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_TIMEOUT.fields.timeout_val
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - timeout_val width matches SSOT value 16
  - timeout_val reset behavior matches SSOT value 1024
  - timeout_val access policy rw is implemented without read/write shortcuts
  - timeout_val readback returns implemented RTL state when readable
  - timeout_val write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_TIMEOUT.fields.timeout_val

### RTL-0205: Implement field GLOBAL_TIMEOUT.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.GLOBAL_TIMEOUT.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.GLOBAL_TIMEOUT.fields.reserved_31_16.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_16; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.GLOBAL_TIMEOUT.fields.reserved_31_16
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_16 width matches SSOT value 16
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy rw is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.GLOBAL_TIMEOUT.fields.reserved_31_16

### RTL-0206: Implement CSR/register CH0_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_CTRL.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_CTRL; width=32; reset=0; access=rw; offset=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_CTRL
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_CTRL width matches SSOT value 32
  - CH0_CTRL reset behavior matches SSOT value 0
  - CH0_CTRL access policy rw is implemented without read/write shortcuts
  - CH0_CTRL decode uses SSOT address/offset 256
- SSOT refs: registers.register_list.CH0_CTRL

### RTL-0207: Implement field CH0_CTRL.ch_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_CTRL.fields.ch_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_CTRL.fields.ch_en.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_en; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_CTRL.fields.ch_en
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_en width matches SSOT value 1
  - ch_en reset behavior matches SSOT value 0
  - ch_en access policy rw is implemented without read/write shortcuts
  - ch_en readback returns implemented RTL state when readable
  - ch_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_CTRL.fields.ch_en

### RTL-0208: Implement field CH0_CTRL.ch_start

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_CTRL.fields.ch_start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_CTRL.fields.ch_start.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_start; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_CTRL.fields.ch_start
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_start width matches SSOT value 1
  - ch_start reset behavior matches SSOT value 0
  - ch_start access policy rw is implemented without read/write shortcuts
  - ch_start readback returns implemented RTL state when readable
  - ch_start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_CTRL.fields.ch_start

### RTL-0209: Implement field CH0_CTRL.hsize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_CTRL.fields.hsize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_CTRL.fields.hsize.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=hsize; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_CTRL.fields.hsize
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hsize width matches SSOT value 2
  - hsize reset behavior matches SSOT value 0
  - hsize access policy rw is implemented without read/write shortcuts
  - hsize readback returns implemented RTL state when readable
  - hsize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_CTRL.fields.hsize

### RTL-0210: Implement field CH0_CTRL.burst_mode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_CTRL.fields.burst_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_CTRL.fields.burst_mode.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=burst_mode; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_CTRL.fields.burst_mode
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - burst_mode width matches SSOT value 2
  - burst_mode reset behavior matches SSOT value 0
  - burst_mode access policy rw is implemented without read/write shortcuts
  - burst_mode readback returns implemented RTL state when readable
  - burst_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_CTRL.fields.burst_mode

### RTL-0211: Implement field CH0_CTRL.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_CTRL.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_CTRL.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_CTRL.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy rw is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_CTRL.fields.reserved_31_6

### RTL-0212: Implement CSR/register CH0_SRC_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_SRC_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_SRC_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_SRC_ADDR; width=32; reset=0; access=rw; offset=260.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_SRC_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_SRC_ADDR width matches SSOT value 32
  - CH0_SRC_ADDR reset behavior matches SSOT value 0
  - CH0_SRC_ADDR access policy rw is implemented without read/write shortcuts
  - CH0_SRC_ADDR decode uses SSOT address/offset 260
- SSOT refs: registers.register_list.CH0_SRC_ADDR

### RTL-0213: Implement field CH0_SRC_ADDR.src_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_SRC_ADDR.fields.src_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_SRC_ADDR.fields.src_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=src_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_SRC_ADDR.fields.src_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - src_addr width matches SSOT value 32
  - src_addr reset behavior matches SSOT value 0
  - src_addr access policy rw is implemented without read/write shortcuts
  - src_addr readback returns implemented RTL state when readable
  - src_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_SRC_ADDR.fields.src_addr

### RTL-0214: Implement CSR/register CH0_DST_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_DST_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_DST_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_DST_ADDR; width=32; reset=0; access=rw; offset=264.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_DST_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_DST_ADDR width matches SSOT value 32
  - CH0_DST_ADDR reset behavior matches SSOT value 0
  - CH0_DST_ADDR access policy rw is implemented without read/write shortcuts
  - CH0_DST_ADDR decode uses SSOT address/offset 264
- SSOT refs: registers.register_list.CH0_DST_ADDR

### RTL-0215: Implement field CH0_DST_ADDR.dst_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_DST_ADDR.fields.dst_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_DST_ADDR.fields.dst_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=dst_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_DST_ADDR.fields.dst_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dst_addr width matches SSOT value 32
  - dst_addr reset behavior matches SSOT value 0
  - dst_addr access policy rw is implemented without read/write shortcuts
  - dst_addr readback returns implemented RTL state when readable
  - dst_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_DST_ADDR.fields.dst_addr

### RTL-0216: Implement CSR/register CH0_LEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_LEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_LEN.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_LEN; width=32; reset=0; access=rw; offset=268.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_LEN
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_LEN width matches SSOT value 32
  - CH0_LEN reset behavior matches SSOT value 0
  - CH0_LEN access policy rw is implemented without read/write shortcuts
  - CH0_LEN decode uses SSOT address/offset 268
- SSOT refs: registers.register_list.CH0_LEN

### RTL-0217: Implement field CH0_LEN.length

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_LEN.fields.length
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_LEN.fields.length.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=length; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_LEN.fields.length
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - length width matches SSOT value 16
  - length reset behavior matches SSOT value 0
  - length access policy rw is implemented without read/write shortcuts
  - length readback returns implemented RTL state when readable
  - length write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_LEN.fields.length

### RTL-0218: Implement field CH0_LEN.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_LEN.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_LEN.fields.reserved_31_16.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_16; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_LEN.fields.reserved_31_16
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_16 width matches SSOT value 16
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy rw is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_LEN.fields.reserved_31_16

### RTL-0219: Implement CSR/register CH0_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_STATUS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_STATUS; width=32; reset=0; access=ro; offset=272.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_STATUS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_STATUS width matches SSOT value 32
  - CH0_STATUS reset behavior matches SSOT value 0
  - CH0_STATUS access policy ro is implemented without read/write shortcuts
  - CH0_STATUS decode uses SSOT address/offset 272
- SSOT refs: registers.register_list.CH0_STATUS

### RTL-0220: Implement field CH0_STATUS.busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STATUS.fields.busy.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=busy; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STATUS.fields.busy
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STATUS.fields.busy

### RTL-0221: Implement field CH0_STATUS.done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STATUS.fields.done.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=done; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STATUS.fields.done
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - done width matches SSOT value 1
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STATUS.fields.done

### RTL-0222: Implement field CH0_STATUS.error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_STATUS.fields.error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STATUS.fields.error.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=error; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STATUS.fields.error
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - error width matches SSOT value 1
  - error reset behavior matches SSOT value 0
  - error access policy ro is implemented without read/write shortcuts
  - error readback returns implemented RTL state when readable
  - error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STATUS.fields.error

### RTL-0223: Implement field CH0_STATUS.err_code

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_STATUS.fields.err_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STATUS.fields.err_code.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=err_code; width=3; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STATUS.fields.err_code
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - err_code width matches SSOT value 3
  - err_code reset behavior matches SSOT value 0
  - err_code access policy ro is implemented without read/write shortcuts
  - err_code readback returns implemented RTL state when readable
  - err_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STATUS.fields.err_code

### RTL-0224: Implement field CH0_STATUS.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_STATUS.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STATUS.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STATUS.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy ro is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STATUS.fields.reserved_31_6

### RTL-0225: Implement CSR/register CH0_STRIDE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_STRIDE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_STRIDE.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_STRIDE; width=32; reset=4; access=rw; offset=276.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_STRIDE
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_STRIDE width matches SSOT value 32
  - CH0_STRIDE reset behavior matches SSOT value 4
  - CH0_STRIDE access policy rw is implemented without read/write shortcuts
  - CH0_STRIDE decode uses SSOT address/offset 276
- SSOT refs: registers.register_list.CH0_STRIDE

### RTL-0226: Implement field CH0_STRIDE.stride

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH0_STRIDE.fields.stride
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_STRIDE.fields.stride.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=stride; width=32; reset=4; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_STRIDE.fields.stride
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - stride width matches SSOT value 32
  - stride reset behavior matches SSOT value 4
  - stride access policy rw is implemented without read/write shortcuts
  - stride readback returns implemented RTL state when readable
  - stride write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_STRIDE.fields.stride

### RTL-0227: Implement CSR/register CH0_PERF_WORDS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_PERF_WORDS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_PERF_WORDS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_PERF_WORDS; width=32; reset=0; access=ro; offset=284.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_PERF_WORDS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_PERF_WORDS width matches SSOT value 32
  - CH0_PERF_WORDS reset behavior matches SSOT value 0
  - CH0_PERF_WORDS access policy ro is implemented without read/write shortcuts
  - CH0_PERF_WORDS decode uses SSOT address/offset 284
- SSOT refs: registers.register_list.CH0_PERF_WORDS

### RTL-0228: Implement field CH0_PERF_WORDS.word_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_PERF_WORDS.fields.word_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_PERF_WORDS.fields.word_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=word_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_PERF_WORDS.fields.word_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - word_count width matches SSOT value 32
  - word_count reset behavior matches SSOT value 0
  - word_count access policy ro is implemented without read/write shortcuts
  - word_count readback returns implemented RTL state when readable
  - word_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_PERF_WORDS.fields.word_count

### RTL-0229: Implement CSR/register CH0_PERF_CYCLES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH0_PERF_CYCLES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH0_PERF_CYCLES.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH0_PERF_CYCLES; width=32; reset=0; access=ro; offset=288.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH0_PERF_CYCLES
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH0_PERF_CYCLES width matches SSOT value 32
  - CH0_PERF_CYCLES reset behavior matches SSOT value 0
  - CH0_PERF_CYCLES access policy ro is implemented without read/write shortcuts
  - CH0_PERF_CYCLES decode uses SSOT address/offset 288
- SSOT refs: registers.register_list.CH0_PERF_CYCLES

### RTL-0230: Implement field CH0_PERF_CYCLES.cycle_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH0_PERF_CYCLES.fields.cycle_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH0_PERF_CYCLES.fields.cycle_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=cycle_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH0_PERF_CYCLES.fields.cycle_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - cycle_count width matches SSOT value 32
  - cycle_count reset behavior matches SSOT value 0
  - cycle_count access policy ro is implemented without read/write shortcuts
  - cycle_count readback returns implemented RTL state when readable
  - cycle_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH0_PERF_CYCLES.fields.cycle_count

### RTL-0231: Implement CSR/register CH1_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_CTRL.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_CTRL; width=32; reset=0; access=rw; offset=320.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_CTRL
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_CTRL width matches SSOT value 32
  - CH1_CTRL reset behavior matches SSOT value 0
  - CH1_CTRL access policy rw is implemented without read/write shortcuts
  - CH1_CTRL decode uses SSOT address/offset 320
- SSOT refs: registers.register_list.CH1_CTRL

### RTL-0232: Implement field CH1_CTRL.ch_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_CTRL.fields.ch_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_CTRL.fields.ch_en.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_en; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_CTRL.fields.ch_en
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_en width matches SSOT value 1
  - ch_en reset behavior matches SSOT value 0
  - ch_en access policy rw is implemented without read/write shortcuts
  - ch_en readback returns implemented RTL state when readable
  - ch_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_CTRL.fields.ch_en

### RTL-0233: Implement field CH1_CTRL.ch_start

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_CTRL.fields.ch_start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_CTRL.fields.ch_start.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_start; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_CTRL.fields.ch_start
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_start width matches SSOT value 1
  - ch_start reset behavior matches SSOT value 0
  - ch_start access policy rw is implemented without read/write shortcuts
  - ch_start readback returns implemented RTL state when readable
  - ch_start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_CTRL.fields.ch_start

### RTL-0234: Implement field CH1_CTRL.hsize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_CTRL.fields.hsize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_CTRL.fields.hsize.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=hsize; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_CTRL.fields.hsize
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hsize width matches SSOT value 2
  - hsize reset behavior matches SSOT value 0
  - hsize access policy rw is implemented without read/write shortcuts
  - hsize readback returns implemented RTL state when readable
  - hsize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_CTRL.fields.hsize

### RTL-0235: Implement field CH1_CTRL.burst_mode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_CTRL.fields.burst_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_CTRL.fields.burst_mode.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=burst_mode; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_CTRL.fields.burst_mode
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - burst_mode width matches SSOT value 2
  - burst_mode reset behavior matches SSOT value 0
  - burst_mode access policy rw is implemented without read/write shortcuts
  - burst_mode readback returns implemented RTL state when readable
  - burst_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_CTRL.fields.burst_mode

### RTL-0236: Implement field CH1_CTRL.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_CTRL.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_CTRL.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_CTRL.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy rw is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_CTRL.fields.reserved_31_6

### RTL-0237: Implement CSR/register CH1_SRC_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_SRC_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_SRC_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_SRC_ADDR; width=32; reset=0; access=rw; offset=324.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_SRC_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_SRC_ADDR width matches SSOT value 32
  - CH1_SRC_ADDR reset behavior matches SSOT value 0
  - CH1_SRC_ADDR access policy rw is implemented without read/write shortcuts
  - CH1_SRC_ADDR decode uses SSOT address/offset 324
- SSOT refs: registers.register_list.CH1_SRC_ADDR

### RTL-0238: Implement field CH1_SRC_ADDR.src_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_SRC_ADDR.fields.src_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_SRC_ADDR.fields.src_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=src_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_SRC_ADDR.fields.src_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - src_addr width matches SSOT value 32
  - src_addr reset behavior matches SSOT value 0
  - src_addr access policy rw is implemented without read/write shortcuts
  - src_addr readback returns implemented RTL state when readable
  - src_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_SRC_ADDR.fields.src_addr

### RTL-0239: Implement CSR/register CH1_DST_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_DST_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_DST_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_DST_ADDR; width=32; reset=0; access=rw; offset=328.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_DST_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_DST_ADDR width matches SSOT value 32
  - CH1_DST_ADDR reset behavior matches SSOT value 0
  - CH1_DST_ADDR access policy rw is implemented without read/write shortcuts
  - CH1_DST_ADDR decode uses SSOT address/offset 328
- SSOT refs: registers.register_list.CH1_DST_ADDR

### RTL-0240: Implement field CH1_DST_ADDR.dst_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_DST_ADDR.fields.dst_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_DST_ADDR.fields.dst_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=dst_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_DST_ADDR.fields.dst_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dst_addr width matches SSOT value 32
  - dst_addr reset behavior matches SSOT value 0
  - dst_addr access policy rw is implemented without read/write shortcuts
  - dst_addr readback returns implemented RTL state when readable
  - dst_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_DST_ADDR.fields.dst_addr

### RTL-0241: Implement CSR/register CH1_LEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_LEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_LEN.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_LEN; width=32; reset=0; access=rw; offset=332.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_LEN
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_LEN width matches SSOT value 32
  - CH1_LEN reset behavior matches SSOT value 0
  - CH1_LEN access policy rw is implemented without read/write shortcuts
  - CH1_LEN decode uses SSOT address/offset 332
- SSOT refs: registers.register_list.CH1_LEN
