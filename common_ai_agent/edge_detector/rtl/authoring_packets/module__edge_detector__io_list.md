# RTL Authoring Packet: module__edge_detector__io_list

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
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
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 2/16 section=io_list task_limit=48
- Slice rule: Owner module edge_detector is split into 16 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4
- SSOT connection contracts:
  - edge_detector.PCLK <= PCLK (integration.connections[0])
  - edge_detector.PRESETn <= PRESETn (integration.connections[1])
  - edge_detector.signal_i <= signal_i (integration.connections[2])
  - edge_detector.edge_o <= edge_o (integration.connections[3])
  - edge_detector.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0034: Implement and connect port PCLK

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.PCLK.ports.PCLK
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.PCLK.ports.PCLK.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PCLK; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.PCLK.ports.PCLK
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PCLK width matches SSOT value 1
  - PCLK port direction remains input
- SSOT refs: io_list.clock_domains.PCLK.ports.PCLK

### RTL-0035: Implement and connect port PRESETn

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.PRESETn.ports.PRESETn
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.PRESETn.ports.PRESETn.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PRESETn; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.PRESETn.ports.PRESETn
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PRESETn width matches SSOT value 1
  - PRESETn port direction remains input
- SSOT refs: io_list.resets.PRESETn.ports.PRESETn

### RTL-0036: Implement and connect port signal_i

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.signal_in.ports.signal_i
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.signal_in.ports.signal_i.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=signal_i; width=WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.signal_in.ports.signal_i
  - Primary implementation evidence is in rtl/edge_detector.sv
  - signal_i width matches SSOT value WIDTH
  - signal_i port direction remains input
- SSOT refs: io_list.interfaces.signal_in.ports.signal_i

### RTL-0037: Implement and connect port edge_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.edge_out.ports.edge_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.edge_out.ports.edge_o.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=edge_o; width=WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.edge_out.ports.edge_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - edge_o width matches SSOT value WIDTH
  - edge_o port direction remains output
- SSOT refs: io_list.interfaces.edge_out.ports.edge_o

### RTL-0038: Implement and connect port irq_o

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.interrupt.ports.irq_o
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.interrupt.ports.irq_o.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=irq_o; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.interrupt.ports.irq_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - irq_o width matches SSOT value 1
  - irq_o port direction remains output
- SSOT refs: io_list.interfaces.interrupt.ports.irq_o

### RTL-0039: Implement and connect port PADDR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PADDR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PADDR.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PADDR; width=12; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PADDR
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PADDR width matches SSOT value 12
  - PADDR port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PADDR

### RTL-0040: Implement and connect port PSEL

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PSEL
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PSEL.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PSEL; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PSEL
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PSEL width matches SSOT value 1
  - PSEL port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PSEL

### RTL-0041: Implement and connect port PENABLE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PENABLE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PENABLE.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PENABLE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PENABLE
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PENABLE width matches SSOT value 1
  - PENABLE port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PENABLE

### RTL-0042: Implement and connect port PWRITE

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PWRITE
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PWRITE.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PWRITE; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PWRITE
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PWRITE width matches SSOT value 1
  - PWRITE port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PWRITE

### RTL-0043: Implement and connect port PWDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PWDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PWDATA.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PWDATA; width=32; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PWDATA
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PWDATA width matches SSOT value 32
  - PWDATA port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PWDATA

### RTL-0044: Implement and connect port PSTRB

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PSTRB
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PSTRB.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PSTRB; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PSTRB
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PSTRB width matches SSOT value 4
  - PSTRB port direction remains input
- SSOT refs: io_list.interfaces.apb_csr.ports.PSTRB

### RTL-0045: Implement and connect port PRDATA

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PRDATA
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PRDATA.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PRDATA; width=32; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PRDATA
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PRDATA width matches SSOT value 32
  - PRDATA port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PRDATA

### RTL-0046: Implement and connect port PREADY

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PREADY
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PREADY.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PREADY; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PREADY
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PREADY width matches SSOT value 1
  - PREADY port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PREADY

### RTL-0047: Implement and connect port PSLVERR

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.apb_csr.ports.PSLVERR
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.apb_csr.ports.PSLVERR.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=PSLVERR; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.apb_csr.ports.PSLVERR
  - Primary implementation evidence is in rtl/edge_detector.sv
  - PSLVERR width matches SSOT value 1
  - PSLVERR port direction remains output
- SSOT refs: io_list.interfaces.apb_csr.ports.PSLVERR
