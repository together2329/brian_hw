# RTL Authoring Packet: module__fifo_sync_cx1__io_list

- Kind: module
- Owner module: fifo_sync_cx1
- Owner file: rtl/fifo_sync_cx1.sv
- Task count: 8
- Required tasks: 8

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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_READ, function_model.transactions.FM_WRITE, io_list, rtl_contract, test_requirements
- Module slice: 3/11 section=io_list task_limit=48
- Slice rule: Owner module fifo_sync_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - fifo_sync_cx1.clk <= clk (integration.connections[0])
  - fifo_sync_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0022: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.main.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.main.ports.clk.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.main.ports.clk
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.main.ports.clk

### RTL-0023: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0024: Implement and connect port wr_en

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.wr_en
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.wr_en.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=wr_en; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.wr_en
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - wr_en width matches SSOT value 1
  - wr_en port direction remains input
- SSOT refs: io_list.interfaces.fifo_io.ports.wr_en

### RTL-0025: Implement and connect port wr_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.wr_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.wr_data.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=wr_data; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.wr_data
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - wr_data width matches SSOT value 8
  - wr_data port direction remains input
- SSOT refs: io_list.interfaces.fifo_io.ports.wr_data

### RTL-0026: Implement and connect port rd_en

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.rd_en
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.rd_en.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=rd_en; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.rd_en
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_en width matches SSOT value 1
  - rd_en port direction remains input
- SSOT refs: io_list.interfaces.fifo_io.ports.rd_en

### RTL-0027: Implement and connect port rd_data

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.rd_data
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.rd_data.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=rd_data; width=8; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.rd_data
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - rd_data width matches SSOT value 8
  - rd_data port direction remains output
- SSOT refs: io_list.interfaces.fifo_io.ports.rd_data

### RTL-0028: Implement and connect port full

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.full
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.full.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=full; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.full
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - full width matches SSOT value 1
  - full port direction remains output
- SSOT refs: io_list.interfaces.fifo_io.ports.full

### RTL-0029: Implement and connect port empty

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.fifo_io.ports.empty
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.fifo_io.ports.empty.
Owner: fifo_sync_cx1 in rtl/fifo_sync_cx1.sv via io_list.
SSOT item context: name=empty; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.fifo_io.ports.empty
  - Primary implementation evidence is in rtl/fifo_sync_cx1.sv
  - empty width matches SSOT value 1
  - empty port direction remains output
- SSOT refs: io_list.interfaces.fifo_io.ports.empty
