# RTL Authoring Packet: unowned_tasks

- Kind: unowned
- Owner module: <none>
- Owner file: <none>
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
- SSOT connection contracts:
  - gpio_regs.clk <= clk (integration.connections[0])
  - gpio_regs.rst_n <= rst_n (integration.connections[1])
  - gpio_regs.dir_in <= dir_in (integration.connections[2])
  - gpio_regs.dout_in <= dout_in (integration.connections[3])
  - gpio_regs.dir_q <= dir_q (integration.connections[4])
  - gpio_regs.dout_q <= dout_q (integration.connections[5])
  - gpio_input_sampler.clk <= clk (integration.connections[6])
  - gpio_input_sampler.rst_n <= rst_n (integration.connections[7])
  - gpio_input_sampler.pad_in <= pad_in (integration.connections[8])
  - gpio_input_sampler.dir_q <= dir_q (integration.connections[9])
  - gpio_input_sampler.din_q <= din_q (integration.connections[10])
  - gpio_pad_logic.dir_q <= dir_q (integration.connections[11])

## Tasks

### RTL-0101: Implement memory item dir_q_ff

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.dir_q_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.dir_q_ff.
SSOT item context: name=dir_q_ff; width=WIDTH; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.dir_q_ff
  - dir_q_ff width matches SSOT value WIDTH
  - dir_q_ff timing uses SSOT cycle/latency 0
  - dir_q_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.dir_q_ff

### RTL-0102: Implement memory item dout_q_ff

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.dout_q_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.dout_q_ff.
SSOT item context: name=dout_q_ff; width=WIDTH; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.dout_q_ff
  - dout_q_ff width matches SSOT value WIDTH
  - dout_q_ff timing uses SSOT cycle/latency 0
  - dout_q_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.dout_q_ff

### RTL-0103: Implement memory item din_q_ff

- Priority: high
- Required: True
- Status: open
- Category: memory.instances
- Source ref: memory.instances.din_q_ff
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.din_q_ff.
SSOT item context: name=din_q_ff; width=WIDTH; depth=1; latency=0.
- Current reason: Task has no RTL owner file.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.din_q_ff
  - din_q_ff width matches SSOT value WIDTH
  - din_q_ff timing uses SSOT cycle/latency 0
  - din_q_ff storage depth matches SSOT value 1
- SSOT refs: memory.instances.din_q_ff
