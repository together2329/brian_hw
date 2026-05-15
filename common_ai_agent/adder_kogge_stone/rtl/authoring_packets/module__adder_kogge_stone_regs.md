# RTL Authoring Packet: module__adder_kogge_stone_regs

- Kind: module
- Owner module: adder_kogge_stone_regs
- Owner file: rtl/adder_kogge_stone_regs.sv
- Task count: 27
- Required tasks: 27

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: registers, registers.register_list
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=6, min_source_files=3, min_state_updates=8
- SSOT connection contracts:
  - adder_kogge_stone_regs.clk_i <= PCLK (integration.connections[2])
  - adder_kogge_stone_regs.rst_ni <= PRESETn (integration.connections[3])

## Tasks

### RTL-0028: Implement APB-lite register block in adder_kogge_stone_regs.sv

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Decode paddr to select CONTROL, STATUS, A_DATA, B_DATA, CIN, SUM_RESULT, COUT_RESULT, CONFIG. Implement RW, RO, W1C access policies. Drive pslverr for out-of-bounds. Connect shadow registers to core.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is present in rtl/adder_kogge_stone_regs.sv
  - APB protocol assertions pass
  - All register reset values match SSOT
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - Semantic source_refs covered: io_list.interfaces.apb_csr, registers.register_list
- SSOT refs: io_list.interfaces.apb_csr, registers.register_list, workflow_todos.rtl-gen[1]

### RTL-0089: Implement CSR/register CONTROL

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CONTROL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CONTROL.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=CONTROL; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CONTROL
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - CONTROL width matches SSOT value 32
  - CONTROL reset behavior matches SSOT value 0
  - CONTROL access policy rw is implemented without read/write shortcuts
  - CONTROL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CONTROL

### RTL-0090: Implement field CONTROL.start

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.start
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.start.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=start; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.start
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - start reset behavior matches SSOT value 0
  - start access policy rw is implemented without read/write shortcuts
  - start readback returns implemented RTL state when readable
  - start write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.start

### RTL-0091: Implement field CONTROL.hold_mode

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.hold_mode
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.hold_mode.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=hold_mode; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.hold_mode
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - hold_mode reset behavior matches SSOT value 0
  - hold_mode access policy rw is implemented without read/write shortcuts
  - hold_mode readback returns implemented RTL state when readable
  - hold_mode write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.hold_mode

### RTL-0092: Implement field CONTROL.clr_done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.clr_done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.clr_done.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=clr_done; reset=0; access=w1c.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.clr_done
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - clr_done reset behavior matches SSOT value 0
  - clr_done access policy w1c is implemented without read/write shortcuts
  - clr_done readback returns implemented RTL state when readable
  - clr_done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.clr_done

### RTL-0093: Implement field CONTROL.reserved_31_3

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONTROL.fields.reserved_31_3
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONTROL.fields.reserved_31_3.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_3; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONTROL.fields.reserved_31_3
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - reserved_31_3 reset behavior matches SSOT value 0
  - reserved_31_3 access policy reserved is implemented without read/write shortcuts
  - reserved_31_3 readback returns implemented RTL state when readable
  - reserved_31_3 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONTROL.fields.reserved_31_3

### RTL-0094: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.STATUS

### RTL-0095: Implement field STATUS.busy

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.busy
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.busy.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=busy; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.busy
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - busy reset behavior matches SSOT value 0
  - busy access policy ro is implemented without read/write shortcuts
  - busy readback returns implemented RTL state when readable
  - busy write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.busy

### RTL-0096: Implement field STATUS.done

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.done
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.done.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=done; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.done
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - done reset behavior matches SSOT value 0
  - done access policy ro is implemented without read/write shortcuts
  - done readback returns implemented RTL state when readable
  - done write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.done

### RTL-0097: Implement field STATUS.overflow

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.overflow
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.overflow.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=overflow; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.overflow
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - overflow reset behavior matches SSOT value 0
  - overflow access policy ro is implemented without read/write shortcuts
  - overflow readback returns implemented RTL state when readable
  - overflow write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.overflow

### RTL-0098: Implement field STATUS.reserved_31_3

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_3
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_3.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_3; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_3
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - reserved_31_3 reset behavior matches SSOT value 0
  - reserved_31_3 access policy reserved is implemented without read/write shortcuts
  - reserved_31_3 readback returns implemented RTL state when readable
  - reserved_31_3 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_3

### RTL-0099: Implement CSR/register A_DATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.A_DATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.A_DATA.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=A_DATA; width=32; reset=0; access=rw; offset=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.A_DATA
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - A_DATA width matches SSOT value 32
  - A_DATA reset behavior matches SSOT value 0
  - A_DATA access policy rw is implemented without read/write shortcuts
  - A_DATA decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.A_DATA

### RTL-0100: Implement field A_DATA.a_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.A_DATA.fields.a_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.A_DATA.fields.a_data.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=a_data; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.A_DATA.fields.a_data
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - a_data reset behavior matches SSOT value 0
  - a_data access policy rw is implemented without read/write shortcuts
  - a_data readback returns implemented RTL state when readable
  - a_data write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.A_DATA.fields.a_data

### RTL-0101: Implement CSR/register B_DATA

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.B_DATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.B_DATA.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=B_DATA; width=32; reset=0; access=rw; offset=12.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.B_DATA
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - B_DATA width matches SSOT value 32
  - B_DATA reset behavior matches SSOT value 0
  - B_DATA access policy rw is implemented without read/write shortcuts
  - B_DATA decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.B_DATA

### RTL-0102: Implement field B_DATA.b_data

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.B_DATA.fields.b_data
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.B_DATA.fields.b_data.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=b_data; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.B_DATA.fields.b_data
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - b_data reset behavior matches SSOT value 0
  - b_data access policy rw is implemented without read/write shortcuts
  - b_data readback returns implemented RTL state when readable
  - b_data write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.B_DATA.fields.b_data

### RTL-0103: Implement CSR/register CIN

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CIN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CIN.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=CIN; width=32; reset=0; access=rw; offset=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CIN
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - CIN width matches SSOT value 32
  - CIN reset behavior matches SSOT value 0
  - CIN access policy rw is implemented without read/write shortcuts
  - CIN decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.CIN

### RTL-0104: Implement field CIN.cin

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CIN.fields.cin
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CIN.fields.cin.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=cin; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CIN.fields.cin
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - cin reset behavior matches SSOT value 0
  - cin access policy rw is implemented without read/write shortcuts
  - cin readback returns implemented RTL state when readable
  - cin write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CIN.fields.cin

### RTL-0105: Implement field CIN.reserved_31_1

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CIN.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CIN.fields.reserved_31_1.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CIN.fields.reserved_31_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CIN.fields.reserved_31_1

### RTL-0106: Implement CSR/register SUM_RESULT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.SUM_RESULT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SUM_RESULT.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=SUM_RESULT; width=32; reset=0; access=ro; offset=20.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SUM_RESULT
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - SUM_RESULT width matches SSOT value 32
  - SUM_RESULT reset behavior matches SSOT value 0
  - SUM_RESULT access policy ro is implemented without read/write shortcuts
  - SUM_RESULT decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.SUM_RESULT

### RTL-0107: Implement field SUM_RESULT.sum_result

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.SUM_RESULT.fields.sum_result
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.SUM_RESULT.fields.sum_result.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=sum_result; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.SUM_RESULT.fields.sum_result
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - sum_result reset behavior matches SSOT value 0
  - sum_result access policy ro is implemented without read/write shortcuts
  - sum_result readback returns implemented RTL state when readable
  - sum_result write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.SUM_RESULT.fields.sum_result

### RTL-0108: Implement CSR/register COUT_RESULT

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.COUT_RESULT
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.COUT_RESULT.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=COUT_RESULT; width=32; reset=0; access=ro; offset=24.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.COUT_RESULT
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - COUT_RESULT width matches SSOT value 32
  - COUT_RESULT reset behavior matches SSOT value 0
  - COUT_RESULT access policy ro is implemented without read/write shortcuts
  - COUT_RESULT decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.COUT_RESULT

### RTL-0109: Implement field COUT_RESULT.cout_result

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.COUT_RESULT.fields.cout_result
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.COUT_RESULT.fields.cout_result.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=cout_result; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.COUT_RESULT.fields.cout_result
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - cout_result reset behavior matches SSOT value 0
  - cout_result access policy ro is implemented without read/write shortcuts
  - cout_result readback returns implemented RTL state when readable
  - cout_result write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.COUT_RESULT.fields.cout_result

### RTL-0110: Implement field COUT_RESULT.reserved_31_1

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.COUT_RESULT.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.COUT_RESULT.fields.reserved_31_1.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.COUT_RESULT.fields.reserved_31_1
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.COUT_RESULT.fields.reserved_31_1

### RTL-0111: Implement CSR/register CONFIG

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.CONFIG
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CONFIG.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=CONFIG; width=32; reset=depends on parameter DATA_WIDTH; access=ro; offset=28.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CONFIG
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - CONFIG width matches SSOT value 32
  - CONFIG reset behavior matches SSOT value depends on parameter DATA_WIDTH
  - CONFIG access policy ro is implemented without read/write shortcuts
  - CONFIG decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.CONFIG

### RTL-0112: Implement field CONFIG.data_width

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONFIG.fields.data_width
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONFIG.fields.data_width.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=data_width; reset=DATA_WIDTH; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONFIG.fields.data_width
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - data_width reset behavior matches SSOT value DATA_WIDTH
  - data_width access policy ro is implemented without read/write shortcuts
  - data_width readback returns implemented RTL state when readable
  - data_width write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONFIG.fields.data_width

### RTL-0113: Implement field CONFIG.reserved_31_8

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.CONFIG.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CONFIG.fields.reserved_31_8.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_8; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CONFIG.fields.reserved_31_8
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
  - reserved_31_8 reset behavior matches SSOT value 0
  - reserved_31_8 access policy reserved is implemented without read/write shortcuts
  - reserved_31_8 readback returns implemented RTL state when readable
  - reserved_31_8 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CONFIG.fields.reserved_31_8

### RTL-0138: Prove module adder_kogge_stone_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.adder_kogge_stone_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.adder_kogge_stone_regs.module_equivalence.
Owner: adder_kogge_stone_regs in rtl/adder_kogge_stone_regs.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.adder_kogge_stone_regs.module_equivalence
  - Primary implementation evidence is in rtl/adder_kogge_stone_regs.sv
- SSOT refs: sub_modules.adder_kogge_stone_regs.module_equivalence
