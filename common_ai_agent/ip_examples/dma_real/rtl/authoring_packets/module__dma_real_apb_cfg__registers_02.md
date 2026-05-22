# RTL Authoring Packet: module__dma_real_apb_cfg__registers_02

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
- LLM-actionable open tasks: 16
- Human-locked open tasks: 0
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 4/8 section=registers task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0242: Implement field CH1_LEN.length

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_LEN.fields.length
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_LEN.fields.length.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=length; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_LEN.fields.length
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - length width matches SSOT value 16
  - length reset behavior matches SSOT value 0
  - length access policy rw is implemented without read/write shortcuts
  - length readback returns implemented RTL state when readable
  - length write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_LEN.fields.length

### RTL-0243: Implement field CH1_LEN.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_LEN.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_LEN.fields.reserved_31_16.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_16; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_LEN.fields.reserved_31_16
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_16 width matches SSOT value 16
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy rw is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_LEN.fields.reserved_31_16

### RTL-0244: Implement CSR/register CH1_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_STATUS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_STATUS; width=32; reset=0; access=ro; offset=336.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_STATUS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_STATUS width matches SSOT value 32
  - CH1_STATUS reset behavior matches SSOT value 0
  - CH1_STATUS access policy ro is implemented without read/write shortcuts
  - CH1_STATUS decode uses SSOT address/offset 336
- SSOT refs: registers.register_list.CH1_STATUS

### RTL-0245: Implement field CH1_STATUS.busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STATUS.fields.busy.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=busy; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STATUS.fields.busy
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STATUS.fields.busy

### RTL-0246: Implement field CH1_STATUS.done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STATUS.fields.done.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=done; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STATUS.fields.done
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - done width matches SSOT value 1
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STATUS.fields.done

### RTL-0247: Implement field CH1_STATUS.error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_STATUS.fields.error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STATUS.fields.error.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=error; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STATUS.fields.error
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - error width matches SSOT value 1
  - error reset behavior matches SSOT value 0
  - error access policy ro is implemented without read/write shortcuts
  - error readback returns implemented RTL state when readable
  - error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STATUS.fields.error

### RTL-0248: Implement field CH1_STATUS.err_code

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_STATUS.fields.err_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STATUS.fields.err_code.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=err_code; width=3; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STATUS.fields.err_code
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - err_code width matches SSOT value 3
  - err_code reset behavior matches SSOT value 0
  - err_code access policy ro is implemented without read/write shortcuts
  - err_code readback returns implemented RTL state when readable
  - err_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STATUS.fields.err_code

### RTL-0249: Implement field CH1_STATUS.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_STATUS.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STATUS.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STATUS.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy ro is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STATUS.fields.reserved_31_6

### RTL-0250: Implement CSR/register CH1_STRIDE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_STRIDE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_STRIDE.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_STRIDE; width=32; reset=4; access=rw; offset=340.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_STRIDE
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_STRIDE width matches SSOT value 32
  - CH1_STRIDE reset behavior matches SSOT value 4
  - CH1_STRIDE access policy rw is implemented without read/write shortcuts
  - CH1_STRIDE decode uses SSOT address/offset 340
- SSOT refs: registers.register_list.CH1_STRIDE

### RTL-0251: Implement field CH1_STRIDE.stride

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH1_STRIDE.fields.stride
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_STRIDE.fields.stride.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=stride; width=32; reset=4; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_STRIDE.fields.stride
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - stride width matches SSOT value 32
  - stride reset behavior matches SSOT value 4
  - stride access policy rw is implemented without read/write shortcuts
  - stride readback returns implemented RTL state when readable
  - stride write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_STRIDE.fields.stride

### RTL-0252: Implement CSR/register CH1_PERF_WORDS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_PERF_WORDS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_PERF_WORDS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_PERF_WORDS; width=32; reset=0; access=ro; offset=348.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_PERF_WORDS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_PERF_WORDS width matches SSOT value 32
  - CH1_PERF_WORDS reset behavior matches SSOT value 0
  - CH1_PERF_WORDS access policy ro is implemented without read/write shortcuts
  - CH1_PERF_WORDS decode uses SSOT address/offset 348
- SSOT refs: registers.register_list.CH1_PERF_WORDS

### RTL-0253: Implement field CH1_PERF_WORDS.word_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_PERF_WORDS.fields.word_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_PERF_WORDS.fields.word_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=word_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_PERF_WORDS.fields.word_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - word_count width matches SSOT value 32
  - word_count reset behavior matches SSOT value 0
  - word_count access policy ro is implemented without read/write shortcuts
  - word_count readback returns implemented RTL state when readable
  - word_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_PERF_WORDS.fields.word_count

### RTL-0254: Implement CSR/register CH1_PERF_CYCLES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH1_PERF_CYCLES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH1_PERF_CYCLES.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH1_PERF_CYCLES; width=32; reset=0; access=ro; offset=352.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH1_PERF_CYCLES
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH1_PERF_CYCLES width matches SSOT value 32
  - CH1_PERF_CYCLES reset behavior matches SSOT value 0
  - CH1_PERF_CYCLES access policy ro is implemented without read/write shortcuts
  - CH1_PERF_CYCLES decode uses SSOT address/offset 352
- SSOT refs: registers.register_list.CH1_PERF_CYCLES

### RTL-0255: Implement field CH1_PERF_CYCLES.cycle_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH1_PERF_CYCLES.fields.cycle_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH1_PERF_CYCLES.fields.cycle_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=cycle_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH1_PERF_CYCLES.fields.cycle_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - cycle_count width matches SSOT value 32
  - cycle_count reset behavior matches SSOT value 0
  - cycle_count access policy ro is implemented without read/write shortcuts
  - cycle_count readback returns implemented RTL state when readable
  - cycle_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH1_PERF_CYCLES.fields.cycle_count

### RTL-0256: Implement CSR/register CH2_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_CTRL.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_CTRL; width=32; reset=0; access=rw; offset=384.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_CTRL
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_CTRL width matches SSOT value 32
  - CH2_CTRL reset behavior matches SSOT value 0
  - CH2_CTRL access policy rw is implemented without read/write shortcuts
  - CH2_CTRL decode uses SSOT address/offset 384
- SSOT refs: registers.register_list.CH2_CTRL

### RTL-0257: Implement field CH2_CTRL.ch_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_CTRL.fields.ch_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_CTRL.fields.ch_en.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_en; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_CTRL.fields.ch_en
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_en width matches SSOT value 1
  - ch_en reset behavior matches SSOT value 0
  - ch_en access policy rw is implemented without read/write shortcuts
  - ch_en readback returns implemented RTL state when readable
  - ch_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_CTRL.fields.ch_en

### RTL-0258: Implement field CH2_CTRL.ch_start

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_CTRL.fields.ch_start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_CTRL.fields.ch_start.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_start; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_CTRL.fields.ch_start
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_start width matches SSOT value 1
  - ch_start reset behavior matches SSOT value 0
  - ch_start access policy rw is implemented without read/write shortcuts
  - ch_start readback returns implemented RTL state when readable
  - ch_start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_CTRL.fields.ch_start

### RTL-0259: Implement field CH2_CTRL.hsize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_CTRL.fields.hsize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_CTRL.fields.hsize.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=hsize; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_CTRL.fields.hsize
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hsize width matches SSOT value 2
  - hsize reset behavior matches SSOT value 0
  - hsize access policy rw is implemented without read/write shortcuts
  - hsize readback returns implemented RTL state when readable
  - hsize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_CTRL.fields.hsize

### RTL-0260: Implement field CH2_CTRL.burst_mode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_CTRL.fields.burst_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_CTRL.fields.burst_mode.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=burst_mode; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_CTRL.fields.burst_mode
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - burst_mode width matches SSOT value 2
  - burst_mode reset behavior matches SSOT value 0
  - burst_mode access policy rw is implemented without read/write shortcuts
  - burst_mode readback returns implemented RTL state when readable
  - burst_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_CTRL.fields.burst_mode

### RTL-0261: Implement field CH2_CTRL.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_CTRL.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_CTRL.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_CTRL.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy rw is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_CTRL.fields.reserved_31_6

### RTL-0262: Implement CSR/register CH2_SRC_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_SRC_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_SRC_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_SRC_ADDR; width=32; reset=0; access=rw; offset=388.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_SRC_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_SRC_ADDR width matches SSOT value 32
  - CH2_SRC_ADDR reset behavior matches SSOT value 0
  - CH2_SRC_ADDR access policy rw is implemented without read/write shortcuts
  - CH2_SRC_ADDR decode uses SSOT address/offset 388
- SSOT refs: registers.register_list.CH2_SRC_ADDR

### RTL-0263: Implement field CH2_SRC_ADDR.src_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_SRC_ADDR.fields.src_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_SRC_ADDR.fields.src_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=src_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_SRC_ADDR.fields.src_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - src_addr width matches SSOT value 32
  - src_addr reset behavior matches SSOT value 0
  - src_addr access policy rw is implemented without read/write shortcuts
  - src_addr readback returns implemented RTL state when readable
  - src_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_SRC_ADDR.fields.src_addr

### RTL-0264: Implement CSR/register CH2_DST_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_DST_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_DST_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_DST_ADDR; width=32; reset=0; access=rw; offset=392.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_DST_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_DST_ADDR width matches SSOT value 32
  - CH2_DST_ADDR reset behavior matches SSOT value 0
  - CH2_DST_ADDR access policy rw is implemented without read/write shortcuts
  - CH2_DST_ADDR decode uses SSOT address/offset 392
- SSOT refs: registers.register_list.CH2_DST_ADDR

### RTL-0265: Implement field CH2_DST_ADDR.dst_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_DST_ADDR.fields.dst_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_DST_ADDR.fields.dst_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=dst_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_DST_ADDR.fields.dst_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dst_addr width matches SSOT value 32
  - dst_addr reset behavior matches SSOT value 0
  - dst_addr access policy rw is implemented without read/write shortcuts
  - dst_addr readback returns implemented RTL state when readable
  - dst_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_DST_ADDR.fields.dst_addr

### RTL-0266: Implement CSR/register CH2_LEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_LEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_LEN.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_LEN; width=32; reset=0; access=rw; offset=396.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_LEN
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_LEN width matches SSOT value 32
  - CH2_LEN reset behavior matches SSOT value 0
  - CH2_LEN access policy rw is implemented without read/write shortcuts
  - CH2_LEN decode uses SSOT address/offset 396
- SSOT refs: registers.register_list.CH2_LEN

### RTL-0267: Implement field CH2_LEN.length

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_LEN.fields.length
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_LEN.fields.length.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=length; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_LEN.fields.length
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - length width matches SSOT value 16
  - length reset behavior matches SSOT value 0
  - length access policy rw is implemented without read/write shortcuts
  - length readback returns implemented RTL state when readable
  - length write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_LEN.fields.length

### RTL-0268: Implement field CH2_LEN.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_LEN.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_LEN.fields.reserved_31_16.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_16; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_LEN.fields.reserved_31_16
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_16 width matches SSOT value 16
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy rw is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_LEN.fields.reserved_31_16

### RTL-0269: Implement CSR/register CH2_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_STATUS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_STATUS; width=32; reset=0; access=ro; offset=400.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_STATUS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_STATUS width matches SSOT value 32
  - CH2_STATUS reset behavior matches SSOT value 0
  - CH2_STATUS access policy ro is implemented without read/write shortcuts
  - CH2_STATUS decode uses SSOT address/offset 400
- SSOT refs: registers.register_list.CH2_STATUS

### RTL-0270: Implement field CH2_STATUS.busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STATUS.fields.busy.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=busy; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STATUS.fields.busy
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STATUS.fields.busy

### RTL-0271: Implement field CH2_STATUS.done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STATUS.fields.done.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=done; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STATUS.fields.done
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - done width matches SSOT value 1
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STATUS.fields.done

### RTL-0272: Implement field CH2_STATUS.error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_STATUS.fields.error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STATUS.fields.error.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=error; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STATUS.fields.error
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - error width matches SSOT value 1
  - error reset behavior matches SSOT value 0
  - error access policy ro is implemented without read/write shortcuts
  - error readback returns implemented RTL state when readable
  - error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STATUS.fields.error

### RTL-0273: Implement field CH2_STATUS.err_code

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_STATUS.fields.err_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STATUS.fields.err_code.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=err_code; width=3; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STATUS.fields.err_code
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - err_code width matches SSOT value 3
  - err_code reset behavior matches SSOT value 0
  - err_code access policy ro is implemented without read/write shortcuts
  - err_code readback returns implemented RTL state when readable
  - err_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STATUS.fields.err_code

### RTL-0274: Implement field CH2_STATUS.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_STATUS.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STATUS.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STATUS.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy ro is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STATUS.fields.reserved_31_6

### RTL-0275: Implement CSR/register CH2_STRIDE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_STRIDE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_STRIDE.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_STRIDE; width=32; reset=4; access=rw; offset=404.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_STRIDE
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_STRIDE width matches SSOT value 32
  - CH2_STRIDE reset behavior matches SSOT value 4
  - CH2_STRIDE access policy rw is implemented without read/write shortcuts
  - CH2_STRIDE decode uses SSOT address/offset 404
- SSOT refs: registers.register_list.CH2_STRIDE

### RTL-0276: Implement field CH2_STRIDE.stride

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH2_STRIDE.fields.stride
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_STRIDE.fields.stride.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=stride; width=32; reset=4; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_STRIDE.fields.stride
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - stride width matches SSOT value 32
  - stride reset behavior matches SSOT value 4
  - stride access policy rw is implemented without read/write shortcuts
  - stride readback returns implemented RTL state when readable
  - stride write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_STRIDE.fields.stride

### RTL-0277: Implement CSR/register CH2_PERF_WORDS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_PERF_WORDS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_PERF_WORDS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_PERF_WORDS; width=32; reset=0; access=ro; offset=412.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_PERF_WORDS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_PERF_WORDS width matches SSOT value 32
  - CH2_PERF_WORDS reset behavior matches SSOT value 0
  - CH2_PERF_WORDS access policy ro is implemented without read/write shortcuts
  - CH2_PERF_WORDS decode uses SSOT address/offset 412
- SSOT refs: registers.register_list.CH2_PERF_WORDS

### RTL-0278: Implement field CH2_PERF_WORDS.word_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_PERF_WORDS.fields.word_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_PERF_WORDS.fields.word_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=word_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_PERF_WORDS.fields.word_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - word_count width matches SSOT value 32
  - word_count reset behavior matches SSOT value 0
  - word_count access policy ro is implemented without read/write shortcuts
  - word_count readback returns implemented RTL state when readable
  - word_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_PERF_WORDS.fields.word_count

### RTL-0279: Implement CSR/register CH2_PERF_CYCLES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH2_PERF_CYCLES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH2_PERF_CYCLES.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH2_PERF_CYCLES; width=32; reset=0; access=ro; offset=416.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH2_PERF_CYCLES
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH2_PERF_CYCLES width matches SSOT value 32
  - CH2_PERF_CYCLES reset behavior matches SSOT value 0
  - CH2_PERF_CYCLES access policy ro is implemented without read/write shortcuts
  - CH2_PERF_CYCLES decode uses SSOT address/offset 416
- SSOT refs: registers.register_list.CH2_PERF_CYCLES

### RTL-0280: Implement field CH2_PERF_CYCLES.cycle_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH2_PERF_CYCLES.fields.cycle_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH2_PERF_CYCLES.fields.cycle_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=cycle_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH2_PERF_CYCLES.fields.cycle_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - cycle_count width matches SSOT value 32
  - cycle_count reset behavior matches SSOT value 0
  - cycle_count access policy ro is implemented without read/write shortcuts
  - cycle_count readback returns implemented RTL state when readable
  - cycle_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH2_PERF_CYCLES.fields.cycle_count

### RTL-0281: Implement CSR/register CH3_CTRL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_CTRL.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_CTRL; width=32; reset=0; access=rw; offset=448.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_CTRL
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_CTRL width matches SSOT value 32
  - CH3_CTRL reset behavior matches SSOT value 0
  - CH3_CTRL access policy rw is implemented without read/write shortcuts
  - CH3_CTRL decode uses SSOT address/offset 448
- SSOT refs: registers.register_list.CH3_CTRL

### RTL-0282: Implement field CH3_CTRL.ch_en

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_CTRL.fields.ch_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_CTRL.fields.ch_en.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_en; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_CTRL.fields.ch_en
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_en width matches SSOT value 1
  - ch_en reset behavior matches SSOT value 0
  - ch_en access policy rw is implemented without read/write shortcuts
  - ch_en readback returns implemented RTL state when readable
  - ch_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_CTRL.fields.ch_en

### RTL-0283: Implement field CH3_CTRL.ch_start

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_CTRL.fields.ch_start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_CTRL.fields.ch_start.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=ch_start; width=1; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_CTRL.fields.ch_start
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - ch_start width matches SSOT value 1
  - ch_start reset behavior matches SSOT value 0
  - ch_start access policy rw is implemented without read/write shortcuts
  - ch_start readback returns implemented RTL state when readable
  - ch_start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_CTRL.fields.ch_start

### RTL-0284: Implement field CH3_CTRL.hsize

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_CTRL.fields.hsize
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_CTRL.fields.hsize.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=hsize; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_CTRL.fields.hsize
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - hsize width matches SSOT value 2
  - hsize reset behavior matches SSOT value 0
  - hsize access policy rw is implemented without read/write shortcuts
  - hsize readback returns implemented RTL state when readable
  - hsize write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_CTRL.fields.hsize

### RTL-0285: Implement field CH3_CTRL.burst_mode

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_CTRL.fields.burst_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_CTRL.fields.burst_mode.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=burst_mode; width=2; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_CTRL.fields.burst_mode
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - burst_mode width matches SSOT value 2
  - burst_mode reset behavior matches SSOT value 0
  - burst_mode access policy rw is implemented without read/write shortcuts
  - burst_mode readback returns implemented RTL state when readable
  - burst_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_CTRL.fields.burst_mode

### RTL-0286: Implement field CH3_CTRL.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_CTRL.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_CTRL.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_CTRL.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy rw is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_CTRL.fields.reserved_31_6

### RTL-0287: Implement CSR/register CH3_SRC_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_SRC_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_SRC_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_SRC_ADDR; width=32; reset=0; access=rw; offset=452.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_SRC_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_SRC_ADDR width matches SSOT value 32
  - CH3_SRC_ADDR reset behavior matches SSOT value 0
  - CH3_SRC_ADDR access policy rw is implemented without read/write shortcuts
  - CH3_SRC_ADDR decode uses SSOT address/offset 452
- SSOT refs: registers.register_list.CH3_SRC_ADDR

### RTL-0288: Implement field CH3_SRC_ADDR.src_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_SRC_ADDR.fields.src_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_SRC_ADDR.fields.src_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=src_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_SRC_ADDR.fields.src_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - src_addr width matches SSOT value 32
  - src_addr reset behavior matches SSOT value 0
  - src_addr access policy rw is implemented without read/write shortcuts
  - src_addr readback returns implemented RTL state when readable
  - src_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_SRC_ADDR.fields.src_addr

### RTL-0289: Implement CSR/register CH3_DST_ADDR

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_DST_ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_DST_ADDR.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_DST_ADDR; width=32; reset=0; access=rw; offset=456.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_DST_ADDR
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_DST_ADDR width matches SSOT value 32
  - CH3_DST_ADDR reset behavior matches SSOT value 0
  - CH3_DST_ADDR access policy rw is implemented without read/write shortcuts
  - CH3_DST_ADDR decode uses SSOT address/offset 456
- SSOT refs: registers.register_list.CH3_DST_ADDR
