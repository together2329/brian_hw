# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__io_list

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011
- Owner file: rtl/ssot_screenshot_smoke_20260524_083011.sv
- Task count: 10
- Required tasks: 10

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
- Module slice: 2/15 section=io_list task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0026: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.primary_clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.primary_clk.ports.clk.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.primary_clk.ports.clk
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.primary_clk.ports.clk

### RTL-0027: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0028: Implement and connect port valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.valid.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=valid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.valid
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - valid width matches SSOT value 1
  - valid port direction remains input
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.valid

### RTL-0029: Implement and connect port ready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.ready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.ready.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=ready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.ready
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - ready width matches SSOT value 1
  - ready port direction remains output
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.ready

### RTL-0030: Implement and connect port data_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.data_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.data_in.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=data_in; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.data_in
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - data_in width matches SSOT value 8
  - data_in port direction remains input
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.data_in

### RTL-0031: Implement and connect port result

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.result
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.result.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=result; width=8; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.result
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - result width matches SSOT value 8
  - result port direction remains output
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.result

### RTL-0032: Implement and connect port result_valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.result_valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.result_valid.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=result_valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.result_valid
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - result_valid width matches SSOT value 1
  - result_valid port direction remains output
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.result_valid

### RTL-0033: Implement and connect port accepted_count

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.valid_ready_transaction.ports.accepted_count
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.valid_ready_transaction.ports.accepted_count.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=accepted_count; width=16; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.valid_ready_transaction.ports.accepted_count
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - accepted_count width matches SSOT value 16
  - accepted_count port direction remains output
- SSOT refs: io_list.interfaces.valid_ready_transaction.ports.accepted_count

### RTL-0034: Implement and connect port busy

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.busy
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.busy.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=busy; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.busy
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - busy width matches SSOT value 1
  - busy port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.busy

### RTL-0035: Implement and connect port error

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.debug_status.ports.error
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.debug_status.ports.error.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via io_list.
SSOT item context: name=error; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.debug_status.ports.error
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - error width matches SSOT value 1
  - error port direction remains output
- SSOT refs: io_list.interfaces.debug_status.ports.error
