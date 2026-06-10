# RTL Authoring Packet: module__edge_det_cx1__io_list

- Kind: module
- Owner module: edge_det_cx1
- Owner file: rtl/edge_det_cx1.sv
- Task count: 5
- Required tasks: 5

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
- Owner refs: cycle_model, dataflow, decomposition, decomposition.units.edge_detect, decomposition.units.sync2ff, fsm, function_model, function_model.state_variables, function_model.state_variables.prev_sync, function_model.state_variables.sync1, function_model.state_variables.sync2, function_model.transactions, function_model.transactions.FM_FALL, function_model.transactions.FM_RISE, function_model.transactions.FM_STABLE, io_list
- Module slice: 3/12 section=io_list task_limit=48
- Slice rule: Owner module edge_det_cx1 is split into 12 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0021: Implement and connect port clk

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.clock_domains.clk_domain.ports.clk
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.clock_domains.clk_domain.ports.clk.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via io_list.
SSOT item context: name=clk; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.clock_domains.clk_domain.ports.clk
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - clk width matches SSOT value 1
  - clk port direction remains input
- SSOT refs: io_list.clock_domains.clk_domain.ports.clk

### RTL-0022: Implement and connect port rst_n

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.resets.rst_n.ports.rst_n
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.resets.rst_n.ports.rst_n.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via io_list.
SSOT item context: name=rst_n; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.resets.rst_n.ports.rst_n
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - rst_n width matches SSOT value 1
  - rst_n port direction remains input
- SSOT refs: io_list.resets.rst_n.ports.rst_n

### RTL-0023: Implement and connect port sig_in

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.signal_input.ports.sig_in
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.signal_input.ports.sig_in.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via io_list.interfaces.signal_input.
SSOT item context: name=sig_in; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.signal_input.ports.sig_in
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - sig_in width matches SSOT value 1
  - sig_in port direction remains input
- SSOT refs: io_list.interfaces.signal_input.ports.sig_in

### RTL-0024: Implement and connect port rise_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.signal_input.ports.rise_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.signal_input.ports.rise_out.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via io_list.interfaces.signal_input.
SSOT item context: name=rise_out; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.signal_input.ports.rise_out
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - rise_out width matches SSOT value 1
  - rise_out port direction remains output
- SSOT refs: io_list.interfaces.signal_input.ports.rise_out

### RTL-0025: Implement and connect port fall_out

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.signal_input.ports.fall_out
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.signal_input.ports.fall_out.
Owner: edge_det_cx1 in rtl/edge_det_cx1.sv via io_list.interfaces.signal_input.
SSOT item context: name=fall_out; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.signal_input.ports.fall_out
  - Primary implementation evidence is in rtl/edge_det_cx1.sv
  - fall_out width matches SSOT value 1
  - fall_out port direction remains output
- SSOT refs: io_list.interfaces.signal_input.ports.fall_out
