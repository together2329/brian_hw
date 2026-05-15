# RTL Authoring Packet: module__lfsr__io_list

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 13
- Required tasks: 13

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 2/13 section=io_list task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0028: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/lfsr.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0029: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/lfsr.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0030: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PADDR.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PADDR; width=APB_ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PADDR
  - Primary implementation evidence is in rtl/lfsr.sv
  - PADDR width matches SSOT value APB_ADDR_WIDTH
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PADDR

### RTL-0031: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSEL.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSEL
  - Primary implementation evidence is in rtl/lfsr.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PSEL

### RTL-0032: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PENABLE.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PENABLE
  - Primary implementation evidence is in rtl/lfsr.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PENABLE

### RTL-0033: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWRITE.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWRITE
  - Primary implementation evidence is in rtl/lfsr.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWRITE

### RTL-0034: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PWDATA.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PWDATA; width=APB_DATA_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PWDATA
  - Primary implementation evidence is in rtl/lfsr.sv
  - PWDATA width matches SSOT value APB_DATA_WIDTH
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_slave.ports.PWDATA

### RTL-0035: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PRDATA.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PRDATA; width=APB_DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PRDATA
  - Primary implementation evidence is in rtl/lfsr.sv
  - PRDATA width matches SSOT value APB_DATA_WIDTH
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PRDATA

### RTL-0036: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PREADY.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PREADY
  - Primary implementation evidence is in rtl/lfsr.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PREADY

### RTL-0037: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_slave.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_slave.ports.PSLVERR.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_slave.ports.PSLVERR
  - Primary implementation evidence is in rtl/lfsr.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_slave.ports.PSLVERR

### RTL-0038: Implement and connect port prbs_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.prbs_output.ports.prbs_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.prbs_output.ports.prbs_out.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=prbs_out; width=LFSR_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.prbs_output.ports.prbs_out
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_out width matches SSOT value LFSR_WIDTH
  - prbs_out port direction remains output
- SSOT refs: io_list.interfaces.prbs_output.ports.prbs_out

### RTL-0039: Implement and connect port prbs_bit

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.prbs_output.ports.prbs_bit
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.prbs_output.ports.prbs_bit.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=prbs_bit; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.prbs_output.ports.prbs_bit
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_bit width matches SSOT value 1
  - prbs_bit port direction remains output
- SSOT refs: io_list.interfaces.prbs_output.ports.prbs_bit

### RTL-0040: Implement and connect port prbs_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status.ports.prbs_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status.ports.prbs_valid.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=prbs_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status.ports.prbs_valid
  - Primary implementation evidence is in rtl/lfsr.sv
  - prbs_valid width matches SSOT value 1
  - prbs_valid port direction remains output
- SSOT refs: io_list.interfaces.status.ports.prbs_valid
