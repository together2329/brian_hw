# RTL Authoring Packet: module__atciic100_apbslv

- Kind: module
- Owner module: atciic100_apbslv
- Owner file: rtl/atciic100_apbslv.v
- Task count: 27
- Required tasks: 27

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
- LLM-actionable open tasks: 27
- Human-locked open tasks: 0
- Owner refs: io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- SSOT connection contracts:
  - atciic100_apbslv.cmd_reg <= cmd (sub_modules[1].connections[0])
  - atciic100_apbslv.data_in <= pwdata (sub_modules[2].connections[0])

## Tasks

### RTL-0027: Implement APB Slave Logic

- Priority: high
- Required: True
- Status: open
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Decode paddr[5:2] to specific registers. Implement read data mux and write decode.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via workflow_todos.owner.
SSOT item context: id=RTL_TODO_APB.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - APB R/W functional
  - All register fields readable/writable per spec
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - Semantic source_refs covered: registers
- SSOT refs: registers, workflow_todos.rtl-gen[0]

### RTL-0173: Implement CSR/register ID

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ID
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ID.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=ID; width=32; reset=514; access=ro; offset=0.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ID
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - ID width matches SSOT value 32
  - ID reset behavior matches SSOT value 514
  - ID access policy ro is implemented without read/write shortcuts
  - ID decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.ID

### RTL-0174: Implement CSR/register REV

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.REV
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.REV.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=REV; width=32; reset=4098; access=ro; offset=4.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.REV
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - REV width matches SSOT value 32
  - REV reset behavior matches SSOT value 4098
  - REV access policy ro is implemented without read/write shortcuts
  - REV decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.REV

### RTL-0175: Implement CSR/register CFG

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CFG
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CFG.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CFG; width=32; reset=0; access=ro; offset=8.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CFG
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CFG width matches SSOT value 32
  - CFG reset behavior matches SSOT value 0
  - CFG access policy ro is implemented without read/write shortcuts
  - CFG decode uses SSOT address/offset 8
- SSOT refs: registers.register_list.CFG

### RTL-0176: Implement CSR/register INT_EN

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INT_EN
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_EN.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=INT_EN; width=32; reset=0; access=rw; offset=12.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_EN
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - INT_EN width matches SSOT value 32
  - INT_EN reset behavior matches SSOT value 0
  - INT_EN access policy rw is implemented without read/write shortcuts
  - INT_EN decode uses SSOT address/offset 12
- SSOT refs: registers.register_list.INT_EN

### RTL-0177: Implement CSR/register INT_ST

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.INT_ST
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.INT_ST.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=INT_ST; width=32; reset=1; access=rw1c; offset=16.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.INT_ST
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - INT_ST width matches SSOT value 32
  - INT_ST reset behavior matches SSOT value 1
  - INT_ST access policy rw1c is implemented without read/write shortcuts
  - INT_ST decode uses SSOT address/offset 16
- SSOT refs: registers.register_list.INT_ST

### RTL-0178: Implement CSR/register ADDR

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.ADDR
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.ADDR.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=ADDR; width=32; reset=0; access=rw; offset=20.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.ADDR
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - ADDR width matches SSOT value 32
  - ADDR reset behavior matches SSOT value 0
  - ADDR access policy rw is implemented without read/write shortcuts
  - ADDR decode uses SSOT address/offset 20
- SSOT refs: registers.register_list.ADDR

### RTL-0179: Implement CSR/register DATA

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.DATA
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DATA.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=DATA; width=32; reset=0; access=rw; offset=24.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DATA
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - DATA width matches SSOT value 32
  - DATA reset behavior matches SSOT value 0
  - DATA access policy rw is implemented without read/write shortcuts
  - DATA decode uses SSOT address/offset 24
- SSOT refs: registers.register_list.DATA

### RTL-0180: Implement CSR/register CMD

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CMD
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CMD.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CMD; width=32; reset=0; access=rw; offset=28.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CMD
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CMD width matches SSOT value 32
  - CMD reset behavior matches SSOT value 0
  - CMD access policy rw is implemented without read/write shortcuts
  - CMD decode uses SSOT address/offset 28
- SSOT refs: registers.register_list.CMD

### RTL-0181: Implement CSR/register CTRL

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.CTRL
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.CTRL.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=CTRL; width=32; reset=7936; access=rw; offset=32.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.CTRL
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - CTRL width matches SSOT value 32
  - CTRL reset behavior matches SSOT value 7936
  - CTRL access policy rw is implemented without read/write shortcuts
  - CTRL decode uses SSOT address/offset 32
- SSOT refs: registers.register_list.CTRL

### RTL-0182: Implement CSR/register SETUP

- Priority: high
- Required: True
- Status: open
- Category: registers.register
- Source ref: registers.register_list.SETUP
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.SETUP.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via registers.
SSOT item context: name=SETUP; width=32; reset=0; access=rw; offset=36.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.SETUP
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - SETUP width matches SSOT value 32
  - SETUP reset behavior matches SSOT value 0
  - SETUP access policy rw is implemented without read/write shortcuts
  - SETUP decode uses SSOT address/offset 36
- SSOT refs: registers.register_list.SETUP

### RTL-0218: Prove module atciic100_apbslv is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.atciic100_apbslv.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.atciic100_apbslv.module_equivalence.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.atciic100_apbslv.module_equivalence
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
- SSOT refs: sub_modules.atciic100_apbslv.module_equivalence

### RTL-0038: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0039: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.presetn
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.presetn

### RTL-0040: Implement and connect port psel

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0041: Implement and connect port penable

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0042: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0043: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=paddr; width=4; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - paddr width matches SSOT value 4
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0044: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0045: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0046: Implement and connect port scl_i

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.i2c_bus.ports.scl_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.i2c_bus.ports.scl_i.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=scl_i; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.scl_i
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - scl_i width matches SSOT value 1
  - scl_i port direction remains input
- SSOT refs: io_list.interfaces.i2c_bus.ports.scl_i

### RTL-0047: Implement and connect port sda_i

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.i2c_bus.ports.sda_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.i2c_bus.ports.sda_i.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=sda_i; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.sda_i
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - sda_i width matches SSOT value 1
  - sda_i port direction remains input
- SSOT refs: io_list.interfaces.i2c_bus.ports.sda_i

### RTL-0048: Implement and connect port scl_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.i2c_bus.ports.scl_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.i2c_bus.ports.scl_o.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=scl_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.scl_o
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - scl_o width matches SSOT value 1
  - scl_o port direction remains output
- SSOT refs: io_list.interfaces.i2c_bus.ports.scl_o

### RTL-0049: Implement and connect port sda_o

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.i2c_bus.ports.sda_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.i2c_bus.ports.sda_o.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=sda_o; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.i2c_bus.ports.sda_o
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - sda_o width matches SSOT value 1
  - sda_o port direction remains output
- SSOT refs: io_list.interfaces.i2c_bus.ports.sda_o

### RTL-0050: Implement and connect port i2c_req

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_if.ports.i2c_req
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_if.ports.i2c_req.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=i2c_req; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_if.ports.i2c_req
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - i2c_req width matches SSOT value 1
  - i2c_req port direction remains output
- SSOT refs: io_list.interfaces.dma_if.ports.i2c_req

### RTL-0051: Implement and connect port i2c_ack

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.dma_if.ports.i2c_ack
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.dma_if.ports.i2c_ack.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=i2c_ack; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.dma_if.ports.i2c_ack
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - i2c_ack width matches SSOT value 1
  - i2c_ack port direction remains input
- SSOT refs: io_list.interfaces.dma_if.ports.i2c_ack

### RTL-0052: Implement and connect port i2c_int

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.i2c_int
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.i2c_int.
Owner: atciic100_apbslv in rtl/atciic100_apbslv.v via io_list.
SSOT item context: name=i2c_int; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/atciic100_apbslv.v.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.i2c_int
  - Primary implementation evidence is in rtl/atciic100_apbslv.v
  - i2c_int width matches SSOT value 1
  - i2c_int port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.i2c_int
