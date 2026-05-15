# RTL Authoring Packet: module__gpio_regs__features

- Kind: module
- Owner module: gpio_regs
- Owner file: rtl/gpio_regs.sv
- Task count: 3
- Required tasks: 3

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline.S1_LATCH_CONTROL, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1_LATCH_CONTROL, function_model.transactions.FM2_SAMPLE_INPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, function_model.transactions.FM4_ASYNC_RESET, registers, registers.register_list, registers.register_list.DIR_Q, registers.register_list.DOUT_Q
- Module slice: 5/8 section=features task_limit=48
- Slice rule: Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])

## Tasks

### RTL-0106: Implement feature Per-bit direction control

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Per_bit_direction_control
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Per_bit_direction_control.
Owner: gpio_regs in rtl/gpio_regs.sv via features.
SSOT item context: name=Per-bit direction control; output=oe_o[i]=1 when dir_q[i]=1.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Per_bit_direction_control
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: features.Per_bit_direction_control

### RTL-0107: Implement feature Registered output data

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Registered_output_data
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Registered_output_data.
Owner: gpio_regs in rtl/gpio_regs.sv via features.
SSOT item context: name=Registered output data; output=pad_o follows dout_q only for dir_q=1 bits.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Registered_output_data
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: features.Registered_output_data

### RTL-0108: Implement feature Direction-masked input sampling

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Direction_masked_input_sampling
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Direction_masked_input_sampling.
Owner: gpio_regs in rtl/gpio_regs.sv via features.
SSOT item context: name=Direction-masked input sampling; output=output-mode bits hold prior din_q.
- Current reason: Owner RTL file is missing: rtl/gpio_regs.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Direction_masked_input_sampling
  - Primary implementation evidence is in rtl/gpio_regs.sv
- SSOT refs: features.Direction_masked_input_sampling
