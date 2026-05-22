# RTL Authoring Packet: module__model_compare_counter_core__io_list

- Kind: module
- Owner module: model_compare_counter_core
- Owner file: rtl/model_compare_counter_core.sv
- Task count: 8
- Required tasks: 8

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, features, fsm, fsm.control, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_CLEAR, function_model.transactions.FM_IDLE, function_model.transactions.FM_UPDATE, io_list
- Module slice: 1/10 section=io_list task_limit=48
- Slice rule: Owner module model_compare_counter_core is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0025: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.clock_domains.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0026: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.resets.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0027: Implement and connect port enable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ctrl_inputs.ports.enable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ctrl_inputs.ports.enable.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=enable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ctrl_inputs.ports.enable
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - enable width matches SSOT value 1
  - enable port direction remains input
- SSOT refs: io_list.interfaces.ctrl_inputs.ports.enable

### RTL-0028: Implement and connect port clear

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ctrl_inputs.ports.clear
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ctrl_inputs.ports.clear.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=clear; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ctrl_inputs.ports.clear
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - clear width matches SSOT value 1
  - clear port direction remains input
- SSOT refs: io_list.interfaces.ctrl_inputs.ports.clear

### RTL-0029: Implement and connect port step

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.ctrl_inputs.ports.step
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.ctrl_inputs.ports.step.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=step; width=4; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.ctrl_inputs.ports.step
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - step width matches SSOT value 4
  - step port direction remains input
- SSOT refs: io_list.interfaces.ctrl_inputs.ports.step

### RTL-0030: Implement and connect port count

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status_outputs.ports.count
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status_outputs.ports.count.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=count; width=8; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status_outputs.ports.count
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - count width matches SSOT value 8
  - count port direction remains output
- SSOT refs: io_list.interfaces.status_outputs.ports.count

### RTL-0031: Implement and connect port wrapped

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status_outputs.ports.wrapped
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status_outputs.ports.wrapped.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=wrapped; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status_outputs.ports.wrapped
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - wrapped width matches SSOT value 1
  - wrapped port direction remains output
- SSOT refs: io_list.interfaces.status_outputs.ports.wrapped

### RTL-0032: Implement and connect port valid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.status_outputs.ports.valid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.status_outputs.ports.valid.
Owner: model_compare_counter_core in rtl/model_compare_counter_core.sv via io_list.interfaces.
SSOT item context: name=valid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.status_outputs.ports.valid
  - Primary implementation evidence is in rtl/model_compare_counter_core.sv
  - valid width matches SSOT value 1
  - valid port direction remains output
- SSOT refs: io_list.interfaces.status_outputs.ports.valid
