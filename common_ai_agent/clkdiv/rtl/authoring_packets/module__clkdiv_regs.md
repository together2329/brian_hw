# RTL Authoring Packet: module__clkdiv_regs

- Kind: module
- Owner module: clkdiv_regs
- Owner file: rtl/clkdiv_regs.sv
- Task count: 34
- Required tasks: 34

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
- LLM-actionable open tasks: 34
- Human-locked open tasks: 0
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CTRL, registers.register_list.DIVISOR, registers.register_list.INTCLR, registers.register_list.STATUS
- SSOT connection contracts:
  - clkdiv_regs.clk_i <= clk_i (sub_modules[0].connections[0])
  - clkdiv_regs.rst_ni <= rst_ni (sub_modules[0].connections[1])
  - clkdiv_regs.enable_o <= enable (sub_modules[0].connections[2])
  - clkdiv_regs.divisor_o <= active_divisor (sub_modules[0].connections[3])
  - clkdiv_regs.irq_pending_i <= irq_pending (sub_modules[0].connections[4])
  - clkdiv_regs.clk_i <= clk_i (integration.connections[0])
  - clkdiv_regs.rst_ni <= rst_ni (integration.connections[1])
  - clkdiv_regs.paddr <= paddr (integration.connections[2])
  - clkdiv_regs.psel <= psel (integration.connections[3])
  - clkdiv_regs.penable <= penable (integration.connections[4])
  - clkdiv_regs.pwrite <= pwrite (integration.connections[5])
  - clkdiv_regs.pwdata <= pwdata (integration.connections[6])

## Tasks

### RTL-0028: Implement APB register/status block

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement CTRL, DIVISOR, STATUS, INTCLR, APB one-cycle pready/prdata/pslverr behavior, reserved-field policy, divisor zero coercion, and irq pending clear/set policy.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_CLKDIV_REGS.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Register reset, access, bit ranges, write effects, and reserved fields match registers.register_list
  - Unsupported address and RO write pslverr behavior matches error_handling
  - irq_o reflects irq_pending && irq_enable
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - Semantic source_refs covered: error_handling, interrupts, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: error_handling, interrupts, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]

### RTL-0095: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=CTRL; width=32; reset=0; access=rw; offset=0.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 0
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0096: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=enable; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - enable reset behavior matches SSOT value 0
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0097: Implement field CTRL.irq_enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.irq_enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.irq_enable.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=irq_enable; reset=0; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.irq_enable
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - irq_enable reset behavior matches SSOT value 0
  - irq_enable access policy rw is implemented without read/write shortcuts
  - irq_enable readback returns implemented RTL state when readable
  - irq_enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.irq_enable

### RTL-0098: Implement field CTRL.reserved_31_2

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_2
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_2.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.CTRL.
SSOT item context: name=reserved_31_2; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_2
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_2 reset behavior matches SSOT value 0
  - reserved_31_2 access policy reserved is implemented without read/write shortcuts
  - reserved_31_2 readback returns implemented RTL state when readable
  - reserved_31_2 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_2

### RTL-0099: Implement CSR/register DIVISOR

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DIVISOR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DIVISOR.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=DIVISOR; width=32; reset=2; access=rw; offset=4.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DIVISOR
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - DIVISOR width matches SSOT value 32
  - DIVISOR reset behavior matches SSOT value 2
  - DIVISOR access policy rw is implemented without read/write shortcuts
  - DIVISOR decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.DIVISOR

### RTL-0100: Implement field DIVISOR.divisor

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DIVISOR.fields.divisor
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIVISOR.fields.divisor.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=divisor; reset=2; access=rw.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIVISOR.fields.divisor
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - divisor reset behavior matches SSOT value 2
  - divisor access policy rw is implemented without read/write shortcuts
  - divisor readback returns implemented RTL state when readable
  - divisor write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIVISOR.fields.divisor

### RTL-0101: Implement field DIVISOR.reserved_31_16

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.DIVISOR.fields.reserved_31_16
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIVISOR.fields.reserved_31_16.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.DIVISOR.
SSOT item context: name=reserved_31_16; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIVISOR.fields.reserved_31_16
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_16 reset behavior matches SSOT value 0
  - reserved_31_16 access policy reserved is implemented without read/write shortcuts
  - reserved_31_16 readback returns implemented RTL state when readable
  - reserved_31_16 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIVISOR.fields.reserved_31_16

### RTL-0102: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0103: Implement field STATUS.running

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.running
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.running.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=running; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.running
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - running reset behavior matches SSOT value 0
  - running access policy ro is implemented without read/write shortcuts
  - running readback returns implemented RTL state when readable
  - running write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.running

### RTL-0104: Implement field STATUS.locked

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.locked
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.locked.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=locked; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.locked
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - locked reset behavior matches SSOT value 0
  - locked access policy ro is implemented without read/write shortcuts
  - locked readback returns implemented RTL state when readable
  - locked write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.locked

### RTL-0105: Implement field STATUS.irq_pending

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.irq_pending
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.irq_pending.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=irq_pending; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.irq_pending
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - irq_pending reset behavior matches SSOT value 0
  - irq_pending access policy ro is implemented without read/write shortcuts
  - irq_pending readback returns implemented RTL state when readable
  - irq_pending write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.irq_pending

### RTL-0106: Implement field STATUS.reserved_31_3

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_3
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_3.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.STATUS.
SSOT item context: name=reserved_31_3; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_3
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_3 reset behavior matches SSOT value 0
  - reserved_31_3 access policy reserved is implemented without read/write shortcuts
  - reserved_31_3 readback returns implemented RTL state when readable
  - reserved_31_3 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_3

### RTL-0107: Implement CSR/register INTCLR

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INTCLR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INTCLR.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.
SSOT item context: name=INTCLR; width=32; reset=0; access=wo; offset=12.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INTCLR
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - INTCLR width matches SSOT value 32
  - INTCLR reset behavior matches SSOT value 0
  - INTCLR access policy wo is implemented without read/write shortcuts
  - INTCLR decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.INTCLR

### RTL-0108: Implement field INTCLR.clear_irq

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.INTCLR.fields.clear_irq
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTCLR.fields.clear_irq.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.
SSOT item context: name=clear_irq; reset=0; access=wo.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTCLR.fields.clear_irq
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - clear_irq reset behavior matches SSOT value 0
  - clear_irq access policy wo is implemented without read/write shortcuts
  - clear_irq readback returns implemented RTL state when readable
  - clear_irq write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTCLR.fields.clear_irq

### RTL-0109: Implement field INTCLR.reserved_31_1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.INTCLR.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.INTCLR.fields.reserved_31_1.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via registers.register_list.INTCLR.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.INTCLR.fields.reserved_31_1
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.INTCLR.fields.reserved_31_1

### RTL-0110: Implement interrupt item TERMINAL_EVENT

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.TERMINAL_EVENT
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.TERMINAL_EVENT.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via interrupts.
SSOT item context: name=TERMINAL_EVENT; clear=INTCLR.clear_irq W1C.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.TERMINAL_EVENT
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - TERMINAL_EVENT clear behavior matches SSOT clear policy INTCLR.clear_irq W1C
- SSOT refs: interrupts.sources.TERMINAL_EVENT

### RTL-0122: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via error_handling.
SSOT item context: action=legal APB access.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0123: Implement error/fault item recovery_1

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_1
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_1.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via error_handling.
SSOT item context: action=INTCLR.clear_irq W1C.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_1
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
- SSOT refs: error_handling.recovery.recovery_1

### RTL-0156: Prove module clkdiv_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.clkdiv_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.clkdiv_regs.module_equivalence.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.clkdiv_regs.module_equivalence
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
- SSOT refs: sub_modules.clkdiv_regs.module_equivalence

### RTL-0033: Implement and connect port clk_i

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.clk_i.ports.clk_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk_i.ports.clk_i.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.
SSOT item context: name=clk_i; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk_i.ports.clk_i
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - clk_i width matches SSOT value 1
  - clk_i port direction remains input
- SSOT refs: io_list.clock_domains.clk_i.ports.clk_i

### RTL-0034: Implement and connect port rst_ni

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.rst_ni.ports.rst_ni
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_ni.ports.rst_ni.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.
SSOT item context: name=rst_ni; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_ni.ports.rst_ni
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - rst_ni width matches SSOT value 1
  - rst_ni port direction remains input
- SSOT refs: io_list.resets.rst_ni.ports.rst_ni

### RTL-0035: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=paddr; width=8; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - paddr width matches SSOT value 8
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0036: Implement and connect port psel

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0037: Implement and connect port penable

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0038: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0039: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0040: Implement and connect port pstrb

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pstrb
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pstrb.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pstrb; width=4; direction=input.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pstrb
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - pstrb width matches SSOT value 4
  - pstrb port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pstrb

### RTL-0041: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0042: Implement and connect port pready

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pready.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pready
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pready

### RTL-0043: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pslverr.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pslverr
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pslverr

### RTL-0044: Implement and connect port clk_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.divided_clock.ports.clk_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.divided_clock.ports.clk_o.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.
SSOT item context: name=clk_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.divided_clock.ports.clk_o
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - clk_o width matches SSOT value 1
  - clk_o port direction remains output
- SSOT refs: io_list.interfaces.divided_clock.ports.clk_o

### RTL-0045: Implement and connect port locked_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.divided_clock.ports.locked_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.divided_clock.ports.locked_o.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.
SSOT item context: name=locked_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.divided_clock.ports.locked_o
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - locked_o width matches SSOT value 1
  - locked_o port direction remains output
- SSOT refs: io_list.interfaces.divided_clock.ports.locked_o

### RTL-0046: Implement and connect port irq_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.divided_clock.ports.irq_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.divided_clock.ports.irq_o.
Owner: clkdiv_regs in rtl/clkdiv_regs.sv via io_list.
SSOT item context: name=irq_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/clkdiv_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.divided_clock.ports.irq_o
  - Primary implementation evidence is in rtl/clkdiv_regs.sv
  - irq_o width matches SSOT value 1
  - irq_o port direction remains output
- SSOT refs: io_list.interfaces.divided_clock.ports.irq_o
