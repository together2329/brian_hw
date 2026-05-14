# RTL Authoring Packet: module__cortex_m0lite_core__registers

- Kind: module
- Owner module: cortex_m0lite_core
- Owner file: rtl/cortex_m0lite_core.sv
- Task count: 15
- Required tasks: 15

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
- LLM-actionable open tasks: 15
- Human-locked open tasks: 0
- Owner refs: coverage_tap, cycle_model, cycle_model.pipeline, dataflow, dataflow.ordering, dataflow.sequence, dataflow.state_flow, decomposition, error_handling, fsm, fsm.control, function_model, function_model.transactions.FM_CPU_STEP, io_list, parameters, registers
- Module slice: 5/9 section=registers task_limit=48
- Slice rule: Owner module cortex_m0lite_core is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])

## Tasks

### RTL-0114: Implement CSR/register XPSR

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.XPSR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.XPSR.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=XPSR; width=XLEN; reset=0; access=ro; offset=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.XPSR
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - XPSR width matches SSOT value XLEN
  - XPSR reset behavior matches SSOT value 0
  - XPSR access policy ro is implemented without read/write shortcuts
  - XPSR decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.XPSR

### RTL-0115: Implement field XPSR.n

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.XPSR.fields.n
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.XPSR.fields.n.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=n; width=1; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.XPSR.fields.n
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - n width matches SSOT value 1
  - n reset behavior matches SSOT value 0
  - n access policy ro is implemented without read/write shortcuts
  - n readback returns implemented RTL state when readable
  - n write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.XPSR.fields.n

### RTL-0116: Implement field XPSR.z

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.XPSR.fields.z
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.XPSR.fields.z.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=z; width=1; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.XPSR.fields.z
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - z width matches SSOT value 1
  - z reset behavior matches SSOT value 0
  - z access policy ro is implemented without read/write shortcuts
  - z readback returns implemented RTL state when readable
  - z write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.XPSR.fields.z

### RTL-0117: Implement field XPSR.c

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.XPSR.fields.c
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.XPSR.fields.c.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=c; width=1; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.XPSR.fields.c
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - c width matches SSOT value 1
  - c reset behavior matches SSOT value 0
  - c access policy ro is implemented without read/write shortcuts
  - c readback returns implemented RTL state when readable
  - c write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.XPSR.fields.c

### RTL-0118: Implement field XPSR.v

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.XPSR.fields.v
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.XPSR.fields.v.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=v; width=1; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.XPSR.fields.v
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - v width matches SSOT value 1
  - v reset behavior matches SSOT value 0
  - v access policy ro is implemented without read/write shortcuts
  - v readback returns implemented RTL state when readable
  - v write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.XPSR.fields.v

### RTL-0119: Implement field XPSR.reserved_27_0

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.XPSR.fields.reserved_27_0
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.XPSR.fields.reserved_27_0.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=reserved_27_0; width=28; reset=0; access=reserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.XPSR.fields.reserved_27_0
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - reserved_27_0 width matches SSOT value 28
  - reserved_27_0 reset behavior matches SSOT value 0
  - reserved_27_0 access policy reserved is implemented without read/write shortcuts
  - reserved_27_0 readback returns implemented RTL state when readable
  - reserved_27_0 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.XPSR.fields.reserved_27_0

### RTL-0120: Implement CSR/register PC

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.PC
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PC.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=PC; width=XLEN; reset=RESET_PC; access=ro; offset=4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PC
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - PC width matches SSOT value XLEN
  - PC reset behavior matches SSOT value RESET_PC
  - PC access policy ro is implemented without read/write shortcuts
  - PC decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.PC

### RTL-0121: Implement field PC.pc

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.PC.fields.pc
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PC.fields.pc.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=pc; width=XLEN; reset=RESET_PC; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PC.fields.pc
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - pc width matches SSOT value XLEN
  - pc reset behavior matches SSOT value RESET_PC
  - pc access policy ro is implemented without read/write shortcuts
  - pc readback returns implemented RTL state when readable
  - pc write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PC.fields.pc

### RTL-0122: Implement CSR/register EXC_CAUSE

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.EXC_CAUSE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.EXC_CAUSE.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=EXC_CAUSE; width=XLEN; reset=0; access=ro; offset=8.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.EXC_CAUSE
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - EXC_CAUSE width matches SSOT value XLEN
  - EXC_CAUSE reset behavior matches SSOT value 0
  - EXC_CAUSE access policy ro is implemented without read/write shortcuts
  - EXC_CAUSE decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.EXC_CAUSE

### RTL-0123: Implement field EXC_CAUSE.trap_valid

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.EXC_CAUSE.fields.trap_valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.EXC_CAUSE.fields.trap_valid.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=trap_valid; width=1; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.EXC_CAUSE.fields.trap_valid
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_valid width matches SSOT value 1
  - trap_valid reset behavior matches SSOT value 0
  - trap_valid access policy ro is implemented without read/write shortcuts
  - trap_valid readback returns implemented RTL state when readable
  - trap_valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.EXC_CAUSE.fields.trap_valid

### RTL-0124: Implement field EXC_CAUSE.trap_code

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.EXC_CAUSE.fields.trap_code
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.EXC_CAUSE.fields.trap_code.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=trap_code; width=7; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.EXC_CAUSE.fields.trap_code
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_code width matches SSOT value 7
  - trap_code reset behavior matches SSOT value 0
  - trap_code access policy ro is implemented without read/write shortcuts
  - trap_code readback returns implemented RTL state when readable
  - trap_code write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.EXC_CAUSE.fields.trap_code

### RTL-0125: Implement field EXC_CAUSE.trap_stage

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.EXC_CAUSE.fields.trap_stage
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.EXC_CAUSE.fields.trap_stage.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=trap_stage; width=3; reset=0; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.EXC_CAUSE.fields.trap_stage
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - trap_stage width matches SSOT value 3
  - trap_stage reset behavior matches SSOT value 0
  - trap_stage access policy ro is implemented without read/write shortcuts
  - trap_stage readback returns implemented RTL state when readable
  - trap_stage write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.EXC_CAUSE.fields.trap_stage

### RTL-0126: Implement field EXC_CAUSE.reserved_31_11

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.EXC_CAUSE.fields.reserved_31_11
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.EXC_CAUSE.fields.reserved_31_11.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=reserved_31_11; width=21; reset=0; access=reserved.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.EXC_CAUSE.fields.reserved_31_11
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - reserved_31_11 width matches SSOT value 21
  - reserved_31_11 reset behavior matches SSOT value 0
  - reserved_31_11 access policy reserved is implemented without read/write shortcuts
  - reserved_31_11 readback returns implemented RTL state when readable
  - reserved_31_11 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.EXC_CAUSE.fields.reserved_31_11

### RTL-0127: Implement CSR/register EXC_EPC

- Priority: high
- Required: True
- Status: planned
- Category: registers.register
- Source ref: registers.register_list.EXC_EPC
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.EXC_EPC.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=EXC_EPC; width=XLEN; reset=RESET_PC; access=ro; offset=12.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.EXC_EPC
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - EXC_EPC width matches SSOT value XLEN
  - EXC_EPC reset behavior matches SSOT value RESET_PC
  - EXC_EPC access policy ro is implemented without read/write shortcuts
  - EXC_EPC decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.EXC_EPC

### RTL-0128: Implement field EXC_EPC.epc

- Priority: high
- Required: True
- Status: planned
- Category: registers.field
- Source ref: registers.register_list.EXC_EPC.fields.epc
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.EXC_EPC.fields.epc.
Owner: cortex_m0lite_core in rtl/cortex_m0lite_core.sv via registers.
SSOT item context: name=epc; width=XLEN; reset=RESET_PC; access=ro.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.EXC_EPC.fields.epc
  - Primary implementation evidence is in rtl/cortex_m0lite_core.sv
  - epc width matches SSOT value XLEN
  - epc reset behavior matches SSOT value RESET_PC
  - epc access policy ro is implemented without read/write shortcuts
  - epc readback returns implemented RTL state when readable
  - epc write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.EXC_EPC.fields.epc
