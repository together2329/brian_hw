# RTL Authoring Packet: module__simple_pwm__io_list

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 6
- Required tasks: 6

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
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 2/14 section=io_list task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0023: Implement and connect port clk

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.clock_domains.clk.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk.ports.clk.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk.ports.clk
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk.ports.clk

### RTL-0024: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0025: Implement and connect port enable

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.pwm_control.ports.enable
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.pwm_control.ports.enable.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=enable; width=1; direction=input.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.pwm_control.ports.enable
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - enable width matches SSOT value 1
  - enable port direction remains input
- SSOT refs: io_list.interfaces.pwm_control.ports.enable

### RTL-0026: Implement and connect port duty_cycle

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.pwm_control.ports.duty_cycle
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.pwm_control.ports.duty_cycle.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=duty_cycle; width=COUNTER_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.pwm_control.ports.duty_cycle
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - duty_cycle width matches SSOT value COUNTER_WIDTH
  - duty_cycle port direction remains input
- SSOT refs: io_list.interfaces.pwm_control.ports.duty_cycle

### RTL-0027: Implement and connect port period

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.pwm_control.ports.period
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.pwm_control.ports.period.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=period; width=COUNTER_WIDTH; direction=input.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.pwm_control.ports.period
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - period width matches SSOT value COUNTER_WIDTH
  - period port direction remains input
- SSOT refs: io_list.interfaces.pwm_control.ports.period

### RTL-0028: Implement and connect port pwm_out

- Priority: normal
- Required: True
- Status: open
- Category: io_list.port
- Source ref: io_list.interfaces.pwm_output.ports.pwm_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.pwm_output.ports.pwm_out.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=pwm_out; width=1; direction=output.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.pwm_output.ports.pwm_out
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - pwm_out width matches SSOT value 1
  - pwm_out port direction remains output
- SSOT refs: io_list.interfaces.pwm_output.ports.pwm_out
