# RTL Authoring Packet: module__timer_core__io_list

- Kind: module
- Owner module: timer_core
- Owner file: rtl/timer.sv
- Task count: 9
- Required tasks: 9

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
- Owner refs: cycle_model, fsm, function_model, function_model.transactions.FM_TICK, io_list, parameters, rtl_contract
- Module slice: 2/17 section=io_list task_limit=48
- Slice rule: Owner module timer_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.

## Tasks

### RTL-0024: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.main.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.main.ports.clk.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.main.ports.clk
  - Primary implementation evidence is in rtl/timer.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.main.ports.clk

### RTL-0025: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/timer.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0026: Implement and connect port start

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.start
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.start.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=start; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.start
  - Primary implementation evidence is in rtl/timer.sv
  - start width matches SSOT value 1
  - start port direction remains input
- SSOT refs: io_list.interfaces.timer_ctrl.ports.start

### RTL-0027: Implement and connect port enable

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.enable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.enable.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=enable; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.enable
  - Primary implementation evidence is in rtl/timer.sv
  - enable width matches SSOT value 1
  - enable port direction remains input
- SSOT refs: io_list.interfaces.timer_ctrl.ports.enable

### RTL-0028: Implement and connect port clear

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.clear
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.clear.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=clear; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.clear
  - Primary implementation evidence is in rtl/timer.sv
  - clear width matches SSOT value 1
  - clear port direction remains input
- SSOT refs: io_list.interfaces.timer_ctrl.ports.clear

### RTL-0029: Implement and connect port load_value

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.load_value
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.load_value.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=load_value; width=COUNT_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.load_value
  - Primary implementation evidence is in rtl/timer.sv
  - load_value width matches SSOT value COUNT_WIDTH
  - load_value port direction remains input
- SSOT refs: io_list.interfaces.timer_ctrl.ports.load_value

### RTL-0030: Implement and connect port count

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.count
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.count.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=count; width=COUNT_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.count
  - Primary implementation evidence is in rtl/timer.sv
  - count width matches SSOT value COUNT_WIDTH
  - count port direction remains output
- SSOT refs: io_list.interfaces.timer_ctrl.ports.count

### RTL-0031: Implement and connect port running

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.running
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.running.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=running; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.running
  - Primary implementation evidence is in rtl/timer.sv
  - running width matches SSOT value 1
  - running port direction remains output
- SSOT refs: io_list.interfaces.timer_ctrl.ports.running

### RTL-0032: Implement and connect port done

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.timer_ctrl.ports.done
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.timer_ctrl.ports.done.
Owner: timer_core in rtl/timer.sv via io_list.
SSOT item context: name=done; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.timer_ctrl.ports.done
  - Primary implementation evidence is in rtl/timer.sv
  - done width matches SSOT value 1
  - done port direction remains output
- SSOT refs: io_list.interfaces.timer_ctrl.ports.done
