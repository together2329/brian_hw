# RTL Authoring Packet: module__pulse_gen_regs

- Kind: module
- Owner module: pulse_gen_regs
- Owner file: rtl/pulse_gen_regs.sv
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
- Owner refs: integration, integration.bus_attachment, interrupts, registers, registers.register_list
- SSOT connection contracts:
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
  - pulse_gen_regs.ctrl_hw_trig_en_o <= pulse_gen_core.ctrl_hw_trig_en (integration.connections[12])
  - pulse_gen_regs.pulse_width_o <= pulse_gen_core.pulse_width_i (integration.connections[13])
  - pulse_gen_regs.fired_count_i <= pulse_gen_core.fired_count (integration.connections[16])
  - pulse_gen_regs.int_enable_o <= pulse_gen_core.int_enable_i (integration.connections[17])

## Tasks

### RTL-0021: Implement pulse_gen_regs APB-Lite register decode and interrupt logic

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement APB-Lite slave with zero-wait-state (PREADY=1), address decode for CTRL/STATUS/PULSE_WIDTH/INT_ENABLE/ID, W1C clear for STATUS.done, PSLVERR for illegal addresses, and interrupt output irq_o = STATUS.done & INT_ENABLE.done_ie.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - All 5 registers accessible at correct offsets with correct access policy
  - PREADY tied to 1 (zero-wait-state)
  - PSLVERR asserted for unsupported addresses
  - W1C clear for STATUS.done works correctly
  - irq_o = STATUS.done & INT_ENABLE.done_ie combinational
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - Semantic source_refs covered: interrupts, registers.register_list
- SSOT refs: interrupts, registers.register_list, workflow_todos.rtl-gen[1]

### RTL-0104: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0105: Implement field CTRL.fire

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.fire
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.fire.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=fire; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.fire
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - fire reset behavior matches SSOT value 0
  - fire access policy rw is implemented without read/write shortcuts
  - fire readback returns implemented RTL state when readable
  - fire write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.fire

### RTL-0106: Implement field CTRL.polarity

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.polarity
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.polarity.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=polarity; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.polarity
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - polarity reset behavior matches SSOT value 0
  - polarity access policy rw is implemented without read/write shortcuts
  - polarity readback returns implemented RTL state when readable
  - polarity write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.polarity

### RTL-0107: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=enable; reset=1; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - enable reset behavior matches SSOT value 1
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0108: Implement field CTRL.hw_trig_en

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.hw_trig_en
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.hw_trig_en.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=hw_trig_en; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.hw_trig_en
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - hw_trig_en reset behavior matches SSOT value 0
  - hw_trig_en access policy rw is implemented without read/write shortcuts
  - hw_trig_en readback returns implemented RTL state when readable
  - hw_trig_en write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.hw_trig_en

### RTL-0109: Implement field CTRL.reserved_31_4

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_4
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_4.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_4; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_4
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - reserved_31_4 reset behavior matches SSOT value 0
  - reserved_31_4 access policy reserved is implemented without read/write shortcuts
  - reserved_31_4 readback returns implemented RTL state when readable
  - reserved_31_4 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_4

### RTL-0110: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=0; access=mixed; offset=4.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy mixed is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.STATUS

### RTL-0111: Implement field STATUS.busy

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.busy.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=busy; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.busy
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.busy

### RTL-0112: Implement field STATUS.done

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.done.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=done; reset=0; access=w1c.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.done
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - done reset behavior matches SSOT value 0
  - done access policy w1c is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.done

### RTL-0113: Implement field STATUS.fired_count

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.fired_count
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.fired_count.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=fired_count; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.fired_count
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - fired_count reset behavior matches SSOT value 0
  - fired_count access policy ro is implemented without read/write shortcuts
  - fired_count readback returns implemented RTL state when readable
  - fired_count write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.fired_count

### RTL-0114: Implement field STATUS.reserved_31_18

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_18
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_18.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_18; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_18
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - reserved_31_18 reset behavior matches SSOT value 0
  - reserved_31_18 access policy reserved is implemented without read/write shortcuts
  - reserved_31_18 readback returns implemented RTL state when readable
  - reserved_31_18 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_18

### RTL-0115: Implement CSR/register PULSE_WIDTH

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.PULSE_WIDTH
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.PULSE_WIDTH.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=PULSE_WIDTH; width=32; reset=1; access=rw; offset=8.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.PULSE_WIDTH
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - PULSE_WIDTH width matches SSOT value 32
  - PULSE_WIDTH reset behavior matches SSOT value 1
  - PULSE_WIDTH access policy rw is implemented without read/write shortcuts
  - PULSE_WIDTH decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.PULSE_WIDTH

### RTL-0116: Implement field PULSE_WIDTH.width

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.PULSE_WIDTH.fields.width
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PULSE_WIDTH.fields.width.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=width; reset=1; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PULSE_WIDTH.fields.width
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - width reset behavior matches SSOT value 1
  - width access policy rw is implemented without read/write shortcuts
  - width readback returns implemented RTL state when readable
  - width write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PULSE_WIDTH.fields.width

### RTL-0117: Implement field PULSE_WIDTH.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.PULSE_WIDTH.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.PULSE_WIDTH.fields.reserved_31_16.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.PULSE_WIDTH.fields.reserved_31_16
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.PULSE_WIDTH.fields.reserved_31_16

### RTL-0118: Implement CSR/register INT_ENABLE

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INT_ENABLE
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_ENABLE.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=INT_ENABLE; width=32; reset=0; access=rw; offset=12.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_ENABLE
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - INT_ENABLE width matches SSOT value 32
  - INT_ENABLE reset behavior matches SSOT value 0
  - INT_ENABLE access policy rw is implemented without read/write shortcuts
  - INT_ENABLE decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.INT_ENABLE

### RTL-0119: Implement field INT_ENABLE.done_ie

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.INT_ENABLE.fields.done_ie
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_ENABLE.fields.done_ie.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=done_ie; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_ENABLE.fields.done_ie
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - done_ie reset behavior matches SSOT value 0
  - done_ie access policy rw is implemented without read/write shortcuts
  - done_ie readback returns implemented RTL state when readable
  - done_ie write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_ENABLE.fields.done_ie

### RTL-0120: Implement field INT_ENABLE.reserved_31_1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.INT_ENABLE.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INT_ENABLE.fields.reserved_31_1.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INT_ENABLE.fields.reserved_31_1
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INT_ENABLE.fields.reserved_31_1

### RTL-0121: Implement CSR/register ID

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ID
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ID.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=ID; width=32; reset=65568; access=ro; offset=16.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ID
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - ID width matches SSOT value 32
  - ID reset behavior matches SSOT value 65568
  - ID access policy ro is implemented without read/write shortcuts
  - ID decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.ID

### RTL-0122: Implement field ID.revision

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ID.fields.revision
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ID.fields.revision.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=revision; reset=32; access=ro.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ID.fields.revision
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - revision reset behavior matches SSOT value 32
  - revision access policy ro is implemented without read/write shortcuts
  - revision readback returns implemented RTL state when readable
  - revision write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ID.fields.revision

### RTL-0123: Implement field ID.id

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.ID.fields.id
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.ID.fields.id.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via registers.register_list.
SSOT item context: name=id; reset=256; access=ro.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.ID.fields.id
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - id reset behavior matches SSOT value 256
  - id access policy ro is implemented without read/write shortcuts
  - id readback returns implemented RTL state when readable
  - id write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.ID.fields.id

### RTL-0124: Implement interrupt item PULSE_DONE

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.PULSE_DONE
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.PULSE_DONE.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via interrupts.
SSOT item context: name=PULSE_DONE; clear=W1C via STATUS.done.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.PULSE_DONE
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - PULSE_DONE clear behavior matches SSOT clear policy W1C via STATUS.done
- SSOT refs: interrupts.sources.PULSE_DONE

### RTL-0139: Implement integration item external_modules

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0140: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0141: Implement integration item external_resets

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0142: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0143: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0144: Implement integration item trigger_i

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.trigger_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.trigger_i.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=trigger_i; signal=trigger_i.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.trigger_i
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port trigger_i is the implementation/observation point for trigger_i
- SSOT refs: integration.connections.trigger_i

### RTL-0145: Implement integration item pulse_out

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_out
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_out.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=pulse_out; signal=pulse_out.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_out
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port pulse_out is the implementation/observation point for pulse_out
- SSOT refs: integration.connections.pulse_out

### RTL-0146: Implement integration item irq_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.irq_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq_o.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=irq_o; signal=irq_o.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq_o
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.irq_o

### RTL-0147: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=clk_i; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port clk_i is the implementation/observation point for clk_i
- SSOT refs: integration.connections.PCLK

### RTL-0148: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=rst_ni; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port rst_ni is the implementation/observation point for rst_ni
- SSOT refs: integration.connections.PRESETn

### RTL-0149: Implement integration item pulse_gen_regs.PRDATA

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_regs_PRDATA
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_regs_PRDATA.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=PRDATA; signal=pulse_gen_regs.PRDATA.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_regs_PRDATA
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port PRDATA is the implementation/observation point for PRDATA
- SSOT refs: integration.connections.pulse_gen_regs_PRDATA

### RTL-0150: Implement integration item 1'b1 (zero-wait-state)

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.item_1_b1_zero_wait_state
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.item_1_b1_zero_wait_state.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=PREADY; signal=1'b1 (zero-wait-state).
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.item_1_b1_zero_wait_state
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port PREADY is the implementation/observation point for PREADY
- SSOT refs: integration.connections.item_1_b1_zero_wait_state

### RTL-0151: Implement integration item pulse_gen_regs.PSLVERR

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_regs_PSLVERR
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_regs_PSLVERR.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=PSLVERR; signal=pulse_gen_regs.PSLVERR.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_regs_PSLVERR
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port PSLVERR is the implementation/observation point for PSLVERR
- SSOT refs: integration.connections.pulse_gen_regs_PSLVERR

### RTL-0152: Implement integration item pulse_gen_core.ctrl_fire

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_ctrl_fire
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_ctrl_fire.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=ctrl_fire_o; signal=pulse_gen_core.ctrl_fire.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_ctrl_fire
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port ctrl_fire_o is the implementation/observation point for ctrl_fire_o
- SSOT refs: integration.connections.pulse_gen_core_ctrl_fire

### RTL-0153: Implement integration item pulse_gen_core.ctrl_enable

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_ctrl_enable
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_ctrl_enable.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=ctrl_enable_o; signal=pulse_gen_core.ctrl_enable.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_ctrl_enable
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port ctrl_enable_o is the implementation/observation point for ctrl_enable_o
- SSOT refs: integration.connections.pulse_gen_core_ctrl_enable

### RTL-0154: Implement integration item pulse_gen_core.ctrl_hw_trig_en

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_ctrl_hw_trig_en
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_ctrl_hw_trig_en.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=ctrl_hw_trig_en_o; signal=pulse_gen_core.ctrl_hw_trig_en.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_ctrl_hw_trig_en
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port ctrl_hw_trig_en_o is the implementation/observation point for ctrl_hw_trig_en_o
- SSOT refs: integration.connections.pulse_gen_core_ctrl_hw_trig_en

### RTL-0155: Implement integration item pulse_gen_core.pulse_width_i

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_pulse_width_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_pulse_width_i.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=pulse_width_o; signal=pulse_gen_core.pulse_width_i.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_pulse_width_i
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port pulse_width_o is the implementation/observation point for pulse_width_o
- SSOT refs: integration.connections.pulse_gen_core_pulse_width_i

### RTL-0156: Implement integration item pulse_gen_regs.status_busy

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_regs_status_busy
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_regs_status_busy.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=status_busy_i; signal=pulse_gen_regs.status_busy.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_regs_status_busy
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port status_busy_i is the implementation/observation point for status_busy_i
- SSOT refs: integration.connections.pulse_gen_regs_status_busy

### RTL-0157: Implement integration item pulse_gen_regs.status_done

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_regs_status_done
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_regs_status_done.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=status_done_o; signal=pulse_gen_regs.status_done.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_regs_status_done
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port status_done_o is the implementation/observation point for status_done_o
- SSOT refs: integration.connections.pulse_gen_regs_status_done

### RTL-0158: Implement integration item pulse_gen_core.fired_count

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_fired_count
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_fired_count.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=fired_count_i; signal=pulse_gen_core.fired_count.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_fired_count
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port fired_count_i is the implementation/observation point for fired_count_i
- SSOT refs: integration.connections.pulse_gen_core_fired_count

### RTL-0159: Implement integration item pulse_gen_core.int_enable_i

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.pulse_gen_core_int_enable_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.pulse_gen_core_int_enable_i.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via integration.
SSOT item context: port=int_enable_o; signal=pulse_gen_core.int_enable_i.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.pulse_gen_core_int_enable_i
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
  - DUT port int_enable_o is the implementation/observation point for int_enable_o
- SSOT refs: integration.connections.pulse_gen_core_int_enable_i

### RTL-0166: Prove module pulse_gen_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.pulse_gen_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pulse_gen_regs.module_equivalence.
Owner: pulse_gen_regs in rtl/pulse_gen_regs.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/pulse_gen_regs.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pulse_gen_regs.module_equivalence
  - Primary implementation evidence is in rtl/pulse_gen_regs.sv
- SSOT refs: sub_modules.pulse_gen_regs.module_equivalence
