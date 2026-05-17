# RTL Authoring Packet: module__dma_real_apb_cfg__registers_03

- Kind: module
- Owner module: dma_real_apb_cfg
- Owner file: rtl/dma_real_apb_cfg.sv
- Task count: 16
- Required tasks: 16

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
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: dataflow.ordering.ordering_0, dataflow.sequence.sequence_0, dataflow.sequence.sequence_1, function_model.state_variables, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 5/8 section=registers task_limit=48
- Slice rule: Owner module dma_real_apb_cfg is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0290: Implement field CH3_DST_ADDR.dst_addr

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_DST_ADDR.fields.dst_addr
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_DST_ADDR.fields.dst_addr.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=dst_addr; width=32; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_DST_ADDR.fields.dst_addr
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - dst_addr width matches SSOT value 32
  - dst_addr reset behavior matches SSOT value 0
  - dst_addr access policy rw is implemented without read/write shortcuts
  - dst_addr readback returns implemented RTL state when readable
  - dst_addr write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_DST_ADDR.fields.dst_addr

### RTL-0291: Implement CSR/register CH3_LEN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_LEN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_LEN.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_LEN; width=32; reset=0; access=rw; offset=460.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_LEN
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_LEN width matches SSOT value 32
  - CH3_LEN reset behavior matches SSOT value 0
  - CH3_LEN access policy rw is implemented without read/write shortcuts
  - CH3_LEN decode uses SSOT address/offset 460
- SSOT refs: registers.register_list.CH3_LEN

### RTL-0292: Implement field CH3_LEN.length

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_LEN.fields.length
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_LEN.fields.length.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=length; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_LEN.fields.length
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - length width matches SSOT value 16
  - length reset behavior matches SSOT value 0
  - length access policy rw is implemented without read/write shortcuts
  - length readback returns implemented RTL state when readable
  - length write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_LEN.fields.length

### RTL-0293: Implement field CH3_LEN.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_LEN.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_LEN.fields.reserved_31_16.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_16; width=16; reset=0; access=rw.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_LEN.fields.reserved_31_16
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_16 width matches SSOT value 16
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy rw is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_LEN.fields.reserved_31_16

### RTL-0294: Implement CSR/register CH3_STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_STATUS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_STATUS; width=32; reset=0; access=ro; offset=464.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_STATUS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_STATUS width matches SSOT value 32
  - CH3_STATUS reset behavior matches SSOT value 0
  - CH3_STATUS access policy ro is implemented without read/write shortcuts
  - CH3_STATUS decode uses SSOT address/offset 464
- SSOT refs: registers.register_list.CH3_STATUS

### RTL-0295: Implement field CH3_STATUS.busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STATUS.fields.busy.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=busy; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STATUS.fields.busy
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - busy width matches SSOT value 1
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STATUS.fields.busy

### RTL-0296: Implement field CH3_STATUS.done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STATUS.fields.done.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=done; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STATUS.fields.done
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - done width matches SSOT value 1
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STATUS.fields.done

### RTL-0297: Implement field CH3_STATUS.error

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_STATUS.fields.error
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STATUS.fields.error.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=error; width=1; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STATUS.fields.error
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - error width matches SSOT value 1
  - error reset behavior matches SSOT value 0
  - error access policy ro is implemented without read/write shortcuts
  - error readback returns implemented RTL state when readable
  - error write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STATUS.fields.error

### RTL-0298: Implement field CH3_STATUS.err_code

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_STATUS.fields.err_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STATUS.fields.err_code.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=err_code; width=3; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STATUS.fields.err_code
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - err_code width matches SSOT value 3
  - err_code reset behavior matches SSOT value 0
  - err_code access policy ro is implemented without read/write shortcuts
  - err_code readback returns implemented RTL state when readable
  - err_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STATUS.fields.err_code

### RTL-0299: Implement field CH3_STATUS.reserved_31_6

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_STATUS.fields.reserved_31_6
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STATUS.fields.reserved_31_6.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=reserved_31_6; width=26; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STATUS.fields.reserved_31_6
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - reserved_31_6 width matches SSOT value 26
  - reserved_31_6 reset behavior matches SSOT value 0
  - reserved_31_6 access policy ro is implemented without read/write shortcuts
  - reserved_31_6 readback returns implemented RTL state when readable
  - reserved_31_6 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STATUS.fields.reserved_31_6

### RTL-0300: Implement CSR/register CH3_STRIDE

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_STRIDE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_STRIDE.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_STRIDE; width=32; reset=4; access=rw; offset=468.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_STRIDE
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_STRIDE width matches SSOT value 32
  - CH3_STRIDE reset behavior matches SSOT value 4
  - CH3_STRIDE access policy rw is implemented without read/write shortcuts
  - CH3_STRIDE decode uses SSOT address/offset 468
- SSOT refs: registers.register_list.CH3_STRIDE

### RTL-0301: Implement field CH3_STRIDE.stride

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CH3_STRIDE.fields.stride
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_STRIDE.fields.stride.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=stride; width=32; reset=4; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_STRIDE.fields.stride
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - stride width matches SSOT value 32
  - stride reset behavior matches SSOT value 4
  - stride access policy rw is implemented without read/write shortcuts
  - stride readback returns implemented RTL state when readable
  - stride write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_STRIDE.fields.stride

### RTL-0302: Implement CSR/register CH3_PERF_WORDS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_PERF_WORDS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_PERF_WORDS.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_PERF_WORDS; width=32; reset=0; access=ro; offset=476.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_PERF_WORDS
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_PERF_WORDS width matches SSOT value 32
  - CH3_PERF_WORDS reset behavior matches SSOT value 0
  - CH3_PERF_WORDS access policy ro is implemented without read/write shortcuts
  - CH3_PERF_WORDS decode uses SSOT address/offset 476
- SSOT refs: registers.register_list.CH3_PERF_WORDS

### RTL-0303: Implement field CH3_PERF_WORDS.word_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_PERF_WORDS.fields.word_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_PERF_WORDS.fields.word_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=word_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_PERF_WORDS.fields.word_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - word_count width matches SSOT value 32
  - word_count reset behavior matches SSOT value 0
  - word_count access policy ro is implemented without read/write shortcuts
  - word_count readback returns implemented RTL state when readable
  - word_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_PERF_WORDS.fields.word_count

### RTL-0304: Implement CSR/register CH3_PERF_CYCLES

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CH3_PERF_CYCLES
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CH3_PERF_CYCLES.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=CH3_PERF_CYCLES; width=32; reset=0; access=ro; offset=480.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CH3_PERF_CYCLES
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - CH3_PERF_CYCLES width matches SSOT value 32
  - CH3_PERF_CYCLES reset behavior matches SSOT value 0
  - CH3_PERF_CYCLES access policy ro is implemented without read/write shortcuts
  - CH3_PERF_CYCLES decode uses SSOT address/offset 480
- SSOT refs: registers.register_list.CH3_PERF_CYCLES

### RTL-0305: Implement field CH3_PERF_CYCLES.cycle_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CH3_PERF_CYCLES.fields.cycle_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CH3_PERF_CYCLES.fields.cycle_count.
Owner: dma_real_apb_cfg in rtl/dma_real_apb_cfg.sv via registers.register_list.
SSOT item context: name=cycle_count; width=32; reset=0; access=ro.
- Current reason: Required RTL static evidence is missing.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CH3_PERF_CYCLES.fields.cycle_count
  - Primary implementation evidence is in rtl/dma_real_apb_cfg.sv
  - cycle_count width matches SSOT value 32
  - cycle_count reset behavior matches SSOT value 0
  - cycle_count access policy ro is implemented without read/write shortcuts
  - cycle_count readback returns implemented RTL state when readable
  - cycle_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CH3_PERF_CYCLES.fields.cycle_count
