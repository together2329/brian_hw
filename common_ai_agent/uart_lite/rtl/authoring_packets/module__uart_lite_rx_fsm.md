# RTL Authoring Packet: module__uart_lite_rx_fsm

- Kind: module
- Owner module: uart_lite_rx_fsm
- Owner file: rtl/uart_lite_rx_fsm.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.rx_stages, fsm, fsm.rx_fsm, io_list, io_list.interfaces.uart_rx, io_list.interfaces.uart_rx.protocol

## Tasks

### RTL-0031: Implement RX FSM with 2-FF synchronizer, shift register, and parity checker

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: State machine per fsm.rx_fsm: IDLE/START_DETECT/START_CONFIRM/DATA/PARITY/STOP/DONE. 2-FF synchronizer on rxd_i. Start-bit confirmed at oversample count 7/16. Data center-sampled at count 7 each period. Parity checked against computed value. Stop bit checked; frame error if low. Push assembled byte to RX FIFO on success.
SSOT ref: workflow_todos.rtl-gen[4].
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_RX_FSM.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All declared FSM states and transitions implemented
  - 2-FF synchronizer instantiated on rxd_i input
  - Start-bit mid-sample at oversample count 7
  - Data center-sample at oversample count 7 each baud period
  - Stop-bit check at mid-sample; frame error on low
  - False start (rxd high at confirm) returns to IDLE
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - Semantic source_refs covered: cycle_model.pipeline.rx_stages, features.rx_byte_reception, fsm.rx_fsm, io_list.interfaces.uart_rx.protocol
- SSOT refs: cycle_model.pipeline.rx_stages, features.rx_byte_reception, fsm.rx_fsm, io_list.interfaces.uart_rx.protocol, workflow_todos.rtl-gen[4]

### RTL-0261: Prove module uart_lite_rx_fsm is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.uart_lite_rx_fsm.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.uart_lite_rx_fsm.module_equivalence.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.uart_lite_rx_fsm.module_equivalence
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
- SSOT refs: sub_modules.uart_lite_rx_fsm.module_equivalence

### RTL-0041: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0042: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0043: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PADDR.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PADDR; width=12; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PADDR
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PADDR width matches SSOT value 12
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PADDR

### RTL-0044: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSEL.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSEL
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSEL

### RTL-0045: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PENABLE.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PENABLE
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PENABLE

### RTL-0046: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWRITE.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWRITE
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWRITE

### RTL-0047: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWDATA.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWDATA
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PWDATA width matches SSOT value 32
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWDATA

### RTL-0048: Implement and connect port PSTRB

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSTRB
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSTRB.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PSTRB; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSTRB
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PSTRB width matches SSOT value 4
  - PSTRB port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSTRB

### RTL-0049: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PRDATA.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PRDATA
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PRDATA width matches SSOT value 32
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PRDATA

### RTL-0050: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PREADY.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PREADY
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PREADY

### RTL-0051: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSLVERR.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSLVERR
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PSLVERR

### RTL-0052: Implement and connect port txd_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.uart_tx.ports.txd_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.uart_tx.ports.txd_o.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=txd_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.uart_tx.ports.txd_o
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - txd_o width matches SSOT value 1
  - txd_o port direction remains output
- SSOT refs: io_list.interfaces.uart_tx.ports.txd_o

### RTL-0053: Implement and connect port rxd_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.uart_rx.ports.rxd_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.uart_rx.ports.rxd_i.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=rxd_i; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.uart_rx.ports.rxd_i
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - rxd_i width matches SSOT value 1
  - rxd_i port direction remains input
- SSOT refs: io_list.interfaces.uart_rx.ports.rxd_i

### RTL-0054: Implement and connect port irq_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.irq_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.irq_o.
Owner: uart_lite_rx_fsm in rtl/uart_lite_rx_fsm.sv via io_list.
SSOT item context: name=irq_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.irq_o
  - Primary implementation evidence is in rtl/uart_lite_rx_fsm.sv
  - irq_o width matches SSOT value 1
  - irq_o port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.irq_o
