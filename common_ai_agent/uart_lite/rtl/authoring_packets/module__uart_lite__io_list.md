# RTL Authoring Packet: module__uart_lite__io_list

- Kind: module
- Owner module: uart_lite
- Owner file: rtl/uart_lite.sv
- Task count: 14
- Required tasks: 14

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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 2/8 section=io_list task_limit=48
- Slice rule: Owner module uart_lite is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_depth_score=10, min_logic_modules=4, min_modules=7, min_procedural_blocks=20, min_source_files=7, min_state_updates=8
- SSOT connection contracts:
  - uart_lite_core.PCLK <= PCLK (integration.connections[0])
  - uart_lite_core.PRESETn <= PRESETn (integration.connections[1])
  - uart_lite_regs.uart_irq_o <= uart_irq (integration.connections[2])
  - uart_lite_core.tx_o <= tx (integration.connections[3])
  - uart_lite_core.rx_i <= rx (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0039: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0040: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0041: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PADDR.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PADDR; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PADDR
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PADDR width matches SSOT value 8
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PADDR

### RTL-0042: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSEL.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSEL
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSEL

### RTL-0043: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PENABLE.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PENABLE
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PENABLE

### RTL-0044: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWRITE.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWRITE
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWRITE

### RTL-0045: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWDATA.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWDATA
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PWDATA width matches SSOT value 32
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWDATA

### RTL-0046: Implement and connect port PSTRB

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSTRB
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSTRB.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PSTRB; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSTRB
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PSTRB width matches SSOT value 4
  - PSTRB port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSTRB

### RTL-0047: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PRDATA.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PRDATA
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PRDATA width matches SSOT value 32
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PRDATA

### RTL-0048: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PREADY.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PREADY
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PREADY

### RTL-0049: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSLVERR.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSLVERR
  - Primary implementation evidence is in rtl/uart_lite.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PSLVERR

### RTL-0050: Implement and connect port tx

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.uart_serial.ports.tx
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.uart_serial.ports.tx.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=tx; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.uart_serial.ports.tx
  - Primary implementation evidence is in rtl/uart_lite.sv
  - tx width matches SSOT value 1
  - tx port direction remains output
- SSOT refs: io_list.interfaces.uart_serial.ports.tx

### RTL-0051: Implement and connect port rx

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.uart_serial.ports.rx
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.uart_serial.ports.rx.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=rx; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.uart_serial.ports.rx
  - Primary implementation evidence is in rtl/uart_lite.sv
  - rx width matches SSOT value 1
  - rx port direction remains input
- SSOT refs: io_list.interfaces.uart_serial.ports.rx

### RTL-0052: Implement and connect port uart_irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.uart_irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.uart_irq.
Owner: uart_lite in rtl/uart_lite.sv via io_list.
SSOT item context: name=uart_irq; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.uart_irq
  - Primary implementation evidence is in rtl/uart_lite.sv
  - uart_irq width matches SSOT value 1
  - uart_irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.uart_irq
