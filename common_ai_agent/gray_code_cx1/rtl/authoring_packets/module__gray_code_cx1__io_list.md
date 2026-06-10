# RTL Authoring Packet: module__gray_code_cx1__io_list

- Kind: module
- Owner module: gray_code_cx1
- Owner file: rtl/gray_code_cx1.sv
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
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_PRIMARY, io_list, rtl_contract, test_requirements
- Module slice: 3/11 section=io_list task_limit=48
- Slice rule: Owner module gray_code_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_code_cx1.clk <= clk (integration.connections[0])
  - gray_code_cx1.rst_n <= rst_n (integration.connections[1])
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
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.main.ports.clk
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
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
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0024: Implement and connect port valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.valid.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.valid
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - valid width matches SSOT value 1
  - valid port direction remains input
- SSOT refs: io_list.interfaces.converter_io.ports.valid

### RTL-0025: Implement and connect port mode

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.mode
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.mode.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=mode; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.mode
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - mode width matches SSOT value 1
  - mode port direction remains input
- SSOT refs: io_list.interfaces.converter_io.ports.mode

### RTL-0026: Implement and connect port bin_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.bin_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.bin_in.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=bin_in; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.bin_in
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - bin_in width matches SSOT value 4
  - bin_in port direction remains input
- SSOT refs: io_list.interfaces.converter_io.ports.bin_in

### RTL-0027: Implement and connect port gray_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.gray_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.gray_in.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=gray_in; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.gray_in
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - gray_in width matches SSOT value 4
  - gray_in port direction remains input
- SSOT refs: io_list.interfaces.converter_io.ports.gray_in

### RTL-0028: Implement and connect port gray_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.gray_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.gray_out.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=gray_out; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.gray_out
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - gray_out width matches SSOT value 4
  - gray_out port direction remains output
- SSOT refs: io_list.interfaces.converter_io.ports.gray_out

### RTL-0029: Implement and connect port bin_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.converter_io.ports.bin_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.converter_io.ports.bin_out.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via io_list.
SSOT item context: name=bin_out; width=4; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.converter_io.ports.bin_out
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - bin_out width matches SSOT value 4
  - bin_out port direction remains output
- SSOT refs: io_list.interfaces.converter_io.ports.bin_out
