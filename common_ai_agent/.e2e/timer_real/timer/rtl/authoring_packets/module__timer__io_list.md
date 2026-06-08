# RTL Authoring Packet: module__timer__io_list

- Kind: module
- Owner module: timer
- Owner file: rtl/timer.sv
- Task count: 11
- Required tasks: 11

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 2/8 section=io_list task_limit=48
- Slice rule: Owner module timer is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])
- SSOT top IO contracts: 11

## Tasks

### RTL-0028: Implement and connect port pclk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.pclk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.pclk.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=pclk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.pclk
  - Primary implementation evidence is in rtl/timer.sv
  - pclk width matches SSOT value 1
  - pclk port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.pclk

### RTL-0029: Implement and connect port presetn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.presetn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.presetn.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=presetn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.presetn
  - Primary implementation evidence is in rtl/timer.sv
  - presetn width matches SSOT value 1
  - presetn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.presetn

### RTL-0030: Implement and connect port paddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.paddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.paddr.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=paddr; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.paddr
  - Primary implementation evidence is in rtl/timer.sv
  - paddr width matches SSOT value 4
  - paddr port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.paddr

### RTL-0031: Implement and connect port psel

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.psel
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.psel.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=psel; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.psel
  - Primary implementation evidence is in rtl/timer.sv
  - psel width matches SSOT value 1
  - psel port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.psel

### RTL-0032: Implement and connect port penable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.penable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.penable.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=penable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.penable
  - Primary implementation evidence is in rtl/timer.sv
  - penable width matches SSOT value 1
  - penable port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.penable

### RTL-0033: Implement and connect port pwrite

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwrite
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwrite.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=pwrite; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwrite
  - Primary implementation evidence is in rtl/timer.sv
  - pwrite width matches SSOT value 1
  - pwrite port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwrite

### RTL-0034: Implement and connect port pwdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pwdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pwdata.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=pwdata; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pwdata
  - Primary implementation evidence is in rtl/timer.sv
  - pwdata width matches SSOT value 32
  - pwdata port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.pwdata

### RTL-0035: Implement and connect port prdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.prdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.prdata.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=prdata; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.prdata
  - Primary implementation evidence is in rtl/timer.sv
  - prdata width matches SSOT value 32
  - prdata port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.prdata

### RTL-0036: Implement and connect port pready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pready.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=pready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pready
  - Primary implementation evidence is in rtl/timer.sv
  - pready width matches SSOT value 1
  - pready port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pready

### RTL-0037: Implement and connect port pslverr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.pslverr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.pslverr.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=pslverr; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.pslverr
  - Primary implementation evidence is in rtl/timer.sv
  - pslverr width matches SSOT value 1
  - pslverr port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.pslverr

### RTL-0038: Implement and connect port irq

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.irq
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.irq.
Owner: timer in rtl/timer.sv via io_list.
SSOT item context: name=irq; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.irq
  - Primary implementation evidence is in rtl/timer.sv
  - irq width matches SSOT value 1
  - irq port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.irq
