# RTL Authoring Packet: module__spi_regs__io_list

- Kind: module
- Owner module: spi_regs
- Owner file: rtl/spi_regs.sv
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
- Owner refs: error_handling, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list
- Module slice: 1/6 section=io_list task_limit=48
- Slice rule: Owner module spi_regs is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=3, min_depth_score=40, min_logic_modules=4, min_modules=6, min_procedural_blocks=20, min_source_files=6, min_state_updates=25

## Tasks

### RTL-0039: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.pclk.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.pclk.ports.PCLK.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.pclk.ports.PCLK
  - Primary implementation evidence is in rtl/spi_regs.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.pclk.ports.PCLK

### RTL-0040: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.presetn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.presetn.ports.PRESETn.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.presetn.ports.PRESETn
  - Primary implementation evidence is in rtl/spi_regs.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.presetn.ports.PRESETn

### RTL-0041: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PADDR.
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PADDR; width=12; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PADDR
  - Primary implementation evidence is in rtl/spi_regs.sv
  - PADDR width matches SSOT value 12
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSEL
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PENABLE
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWRITE
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWDATA
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PSTRB; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSTRB
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PRDATA
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PREADY
  - Primary implementation evidence is in rtl/spi_regs.sv
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
Owner: spi_regs in rtl/spi_regs.sv via io_list.interfaces.apb_slave.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSLVERR
  - Primary implementation evidence is in rtl/spi_regs.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PSLVERR

### RTL-0050: Implement and connect port sclk_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.spi_master.ports.sclk_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.spi_master.ports.sclk_o.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=sclk_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.spi_master.ports.sclk_o
  - Primary implementation evidence is in rtl/spi_regs.sv
  - sclk_o width matches SSOT value 1
  - sclk_o port direction remains output
- SSOT refs: io_list.interfaces.spi_master.ports.sclk_o

### RTL-0051: Implement and connect port mosi_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.spi_master.ports.mosi_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.spi_master.ports.mosi_o.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=mosi_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.spi_master.ports.mosi_o
  - Primary implementation evidence is in rtl/spi_regs.sv
  - mosi_o width matches SSOT value 1
  - mosi_o port direction remains output
- SSOT refs: io_list.interfaces.spi_master.ports.mosi_o

### RTL-0052: Implement and connect port miso_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.spi_master.ports.miso_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.spi_master.ports.miso_i.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=miso_i; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.spi_master.ports.miso_i
  - Primary implementation evidence is in rtl/spi_regs.sv
  - miso_i width matches SSOT value 1
  - miso_i port direction remains input
- SSOT refs: io_list.interfaces.spi_master.ports.miso_i

### RTL-0053: Implement and connect port csn_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.spi_master.ports.csn_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.spi_master.ports.csn_o.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=csn_o; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.spi_master.ports.csn_o
  - Primary implementation evidence is in rtl/spi_regs.sv
  - csn_o width matches SSOT value 4
  - csn_o port direction remains output
- SSOT refs: io_list.interfaces.spi_master.ports.csn_o

### RTL-0054: Implement and connect port irq_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.irq.ports.irq_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.irq.ports.irq_o.
Owner: spi_regs in rtl/spi_regs.sv via io_list.
SSOT item context: name=irq_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.irq.ports.irq_o
  - Primary implementation evidence is in rtl/spi_regs.sv
  - irq_o width matches SSOT value 1
  - irq_o port direction remains output
- SSOT refs: io_list.interfaces.irq.ports.irq_o
