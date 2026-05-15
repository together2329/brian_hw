# RTL Authoring Packet: module__arbiter_rr_regs

- Kind: module
- Owner module: arbiter_rr_regs
- Owner file: rtl/arbiter_rr_regs.sv
- Task count: 26
- Required tasks: 26

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
- LLM-actionable open tasks: 26
- Human-locked open tasks: 0
- Owner refs: io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_regs.PCLK <= PCLK (integration.connections[0])
  - arbiter_rr_regs.PRESETn <= PRESETn (integration.connections[1])
  - arbiter_rr_regs.PADDR <= PADDR (integration.connections[2])
  - arbiter_rr_regs.PSEL <= PSEL (integration.connections[3])
  - arbiter_rr_regs.PENABLE <= PENABLE (integration.connections[4])
  - arbiter_rr_regs.PWRITE <= PWRITE (integration.connections[5])
  - arbiter_rr_regs.PWDATA <= PWDATA (integration.connections[6])
  - arbiter_rr_regs.PRDATA <= PRDATA (integration.connections[7])
  - arbiter_rr_regs.PREADY <= PREADY (integration.connections[8])
  - arbiter_rr_regs.PSLVERR <= PSLVERR (integration.connections[9])
  - arbiter_rr_regs.enable_o <= arb_enable (integration.connections[10])
  - arbiter_rr_regs.mask_o <= req_mask (integration.connections[11])

## Tasks

### RTL-0028: Implement APB-lite register decode for CTRL, REQ_MASK, STATUS

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Implement APB-lite slave interface with setup/access phase protocol. Decode PADDR for CTRL (0x00 rw), REQ_MASK (0x04 rw), STATUS (0x08 ro). Drive PSLVERR for undefined offsets. Export enable_o and mask_o to arbiter core. Import winner_oh_i and active_req_i from core for STATUS register.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_REGS_APB.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - APB-lite protocol timing matches cycle_model.latency.register_read/write
  - PSLVERR asserted for undefined offsets
  - CTRL.enable and REQ_MASK.mask readable and writable
  - STATUS register reflects live arbiter state (read-only)
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - Semantic source_refs covered: error_handling.error_sources, io_list.interfaces.apb_slave, registers.register_list
- SSOT refs: error_handling.error_sources, io_list.interfaces.apb_slave, registers.register_list, workflow_todos.rtl-gen[1]

### RTL-0100: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=CTRL; width=32; reset=1; access=rw; offset=0.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 1
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.CTRL

### RTL-0101: Implement field CTRL.enable

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.enable
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.enable.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=enable; reset=1; access=rw.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.enable
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - enable reset behavior matches SSOT value 1
  - enable access policy rw is implemented without read/write shortcuts
  - enable readback returns implemented RTL state when readable
  - enable write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.enable

### RTL-0102: Implement field CTRL.reserved_31_1

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.CTRL.fields.reserved_31_1
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.CTRL.fields.reserved_31_1.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_1; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.CTRL.fields.reserved_31_1
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - reserved_31_1 reset behavior matches SSOT value 0
  - reserved_31_1 access policy reserved is implemented without read/write shortcuts
  - reserved_31_1 readback returns implemented RTL state when readable
  - reserved_31_1 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.CTRL.fields.reserved_31_1

### RTL-0103: Implement CSR/register REQ_MASK

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.REQ_MASK
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.REQ_MASK.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=REQ_MASK; width=32; reset=15; access=rw; offset=4.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.REQ_MASK
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - REQ_MASK width matches SSOT value 32
  - REQ_MASK reset behavior matches SSOT value 15
  - REQ_MASK access policy rw is implemented without read/write shortcuts
  - REQ_MASK decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.REQ_MASK

### RTL-0104: Implement field REQ_MASK.mask

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.REQ_MASK.fields.mask
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.REQ_MASK.fields.mask.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=mask; reset=15; access=rw.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.REQ_MASK.fields.mask
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - mask reset behavior matches SSOT value 15
  - mask access policy rw is implemented without read/write shortcuts
  - mask readback returns implemented RTL state when readable
  - mask write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.REQ_MASK.fields.mask

### RTL-0105: Implement field REQ_MASK.reserved_31_4

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.REQ_MASK.fields.reserved_31_4
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.REQ_MASK.fields.reserved_31_4.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_4; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.REQ_MASK.fields.reserved_31_4
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - reserved_31_4 reset behavior matches SSOT value 0
  - reserved_31_4 access policy reserved is implemented without read/write shortcuts
  - reserved_31_4 readback returns implemented RTL state when readable
  - reserved_31_4 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.REQ_MASK.fields.reserved_31_4

### RTL-0106: Implement CSR/register STATUS

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.STATUS
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.STATUS.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=STATUS; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.STATUS
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - STATUS width matches SSOT value 32
  - STATUS reset behavior matches SSOT value 0
  - STATUS access policy ro is implemented without read/write shortcuts
  - STATUS decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.STATUS

### RTL-0107: Implement field STATUS.winner

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.winner
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.winner.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=winner; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.winner
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - winner reset behavior matches SSOT value 0
  - winner access policy ro is implemented without read/write shortcuts
  - winner readback returns implemented RTL state when readable
  - winner write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.winner

### RTL-0108: Implement field STATUS.active_req

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.active_req
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.active_req.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=active_req; reset=0; access=ro.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.active_req
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - active_req reset behavior matches SSOT value 0
  - active_req access policy ro is implemented without read/write shortcuts
  - active_req readback returns implemented RTL state when readable
  - active_req write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.active_req

### RTL-0109: Implement field STATUS.reserved_31_8

- Priority: high
- Required: True
- Status: open
- Category: registers.field
- Source ref: registers.register_list.STATUS.fields.reserved_31_8
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.STATUS.fields.reserved_31_8.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via registers.register_list.
SSOT item context: name=reserved_31_8; reset=0; access=reserved.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.STATUS.fields.reserved_31_8
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - reserved_31_8 reset behavior matches SSOT value 0
  - reserved_31_8 access policy reserved is implemented without read/write shortcuts
  - reserved_31_8 readback returns implemented RTL state when readable
  - reserved_31_8 write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.STATUS.fields.reserved_31_8

### RTL-0157: Prove module arbiter_rr_regs is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.arbiter_rr_regs.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.arbiter_rr_regs.module_equivalence.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.arbiter_rr_regs.module_equivalence
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
- SSOT refs: sub_modules.arbiter_rr_regs.module_equivalence

### RTL-0034: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.PCLK.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.PCLK
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.PCLK

### RTL-0035: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.PRESETn.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.PRESETn
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.PRESETn

### RTL-0036: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PADDR.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PADDR; width=8; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PADDR
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PADDR width matches SSOT value 8
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PADDR

### RTL-0037: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSEL.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSEL
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSEL

### RTL-0038: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PENABLE.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PENABLE
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PENABLE

### RTL-0039: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWRITE.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWRITE
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWRITE

### RTL-0040: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWDATA.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWDATA
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PWDATA width matches SSOT value 32
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWDATA

### RTL-0041: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PRDATA.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PRDATA
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PRDATA width matches SSOT value 32
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PRDATA

### RTL-0042: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PREADY.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PREADY
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PREADY

### RTL-0043: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSLVERR.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSLVERR
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PSLVERR

### RTL-0044: Implement and connect port req_i

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.request_inputs.ports.req_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.request_inputs.ports.req_i.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=req_i; width=NUM_REQ; direction=input.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.request_inputs.ports.req_i
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - req_i width matches SSOT value NUM_REQ
  - req_i port direction remains input
- SSOT refs: io_list.interfaces.request_inputs.ports.req_i

### RTL-0045: Implement and connect port gnt_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.grant_outputs.ports.gnt_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.grant_outputs.ports.gnt_o.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=gnt_o; width=NUM_REQ; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.grant_outputs.ports.gnt_o
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - gnt_o width matches SSOT value NUM_REQ
  - gnt_o port direction remains output
- SSOT refs: io_list.interfaces.grant_outputs.ports.gnt_o

### RTL-0046: Implement and connect port gnt_valid_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.grant_outputs.ports.gnt_valid_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.grant_outputs.ports.gnt_valid_o.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=gnt_valid_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.grant_outputs.ports.gnt_valid_o
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - gnt_valid_o width matches SSOT value 1
  - gnt_valid_o port direction remains output
- SSOT refs: io_list.interfaces.grant_outputs.ports.gnt_valid_o

### RTL-0047: Implement and connect port gnt_idx_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.grant_outputs.ports.gnt_idx_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.grant_outputs.ports.gnt_idx_o.
Owner: arbiter_rr_regs in rtl/arbiter_rr_regs.sv via io_list.
SSOT item context: name=gnt_idx_o; width=IDX_WIDTH; direction=output.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr_regs.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.grant_outputs.ports.gnt_idx_o
  - Primary implementation evidence is in rtl/arbiter_rr_regs.sv
  - gnt_idx_o width matches SSOT value IDX_WIDTH
  - gnt_idx_o port direction remains output
- SSOT refs: io_list.interfaces.grant_outputs.ports.gnt_idx_o
