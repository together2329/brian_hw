# RTL Authoring Packet: module__gpio_regs__registers

- Kind: module
- Owner module: gpio_regs
- Owner file: rtl/gpio_regs.sv
- Task count: 4
- Required tasks: 4

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
- Owner refs: cycle_model, cycle_model.pipeline.S1_LATCH_CONTROL, dataflow, decomposition, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM1_LATCH_CONTROL, function_model.transactions.FM2_SAMPLE_INPUTS, function_model.transactions.FM3_DRIVE_PAD_OUTPUTS, function_model.transactions.FM4_ASYNC_RESET, registers, registers.register_list, registers.register_list.DIR_Q, registers.register_list.DOUT_Q
- Module slice: 4/8 section=registers task_limit=48
- Slice rule: Owner module gpio_regs is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])

## Tasks

### RTL-0095: Implement CSR/register DIR_Q

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DIR_Q
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DIR_Q.
Owner: gpio_regs in rtl/gpio_regs.sv via registers.register_list.DIR_Q.
SSOT item context: name=DIR_Q; width=32; reset=0; access=rw; offset=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DIR_Q
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - DIR_Q width matches SSOT value 32
  - DIR_Q reset behavior matches SSOT value 0
  - DIR_Q access policy rw is implemented without read/write shortcuts
  - DIR_Q decode uses SSOT address/offset 0
- SSOT refs: registers.register_list.DIR_Q

### RTL-0096: Implement field DIR_Q.dir

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DIR_Q.fields.dir
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DIR_Q.fields.dir.
Owner: gpio_regs in rtl/gpio_regs.sv via registers.register_list.DIR_Q.
SSOT item context: name=dir; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DIR_Q.fields.dir
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dir reset behavior matches SSOT value 0
  - dir access policy rw is implemented without read/write shortcuts
  - dir readback returns implemented RTL state when readable
  - dir write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DIR_Q.fields.dir

### RTL-0097: Implement CSR/register DOUT_Q

- Priority: high
- Required: True
- Status: pass
- Category: registers.register
- Source ref: registers.register_list.DOUT_Q
- Detail: Decode, readback, write behavior, reset value, access policy, and side effects must come from SSOT.
SSOT ref: registers.register_list.DOUT_Q.
Owner: gpio_regs in rtl/gpio_regs.sv via registers.register_list.DOUT_Q.
SSOT item context: name=DOUT_Q; width=32; reset=0; access=rw; offset=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Address/decode behavior matches SSOT
  - Readable fields return RTL state, not a constant placeholder
  - Write semantics and illegal access response match SSOT
  - Traceability keeps source_ref registers.register_list.DOUT_Q
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - DOUT_Q width matches SSOT value 32
  - DOUT_Q reset behavior matches SSOT value 0
  - DOUT_Q access policy rw is implemented without read/write shortcuts
  - DOUT_Q decode uses SSOT address/offset 4
- SSOT refs: registers.register_list.DOUT_Q

### RTL-0098: Implement field DOUT_Q.dout

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DOUT_Q.fields.dout
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DOUT_Q.fields.dout.
Owner: gpio_regs in rtl/gpio_regs.sv via registers.register_list.DOUT_Q.
SSOT item context: name=dout; reset=0; access=rw.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DOUT_Q.fields.dout
  - Primary implementation evidence is in rtl/gpio_regs.sv
  - dout reset behavior matches SSOT value 0
  - dout access policy rw is implemented without read/write shortcuts
  - dout readback returns implemented RTL state when readable
  - dout write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DOUT_Q.fields.dout
