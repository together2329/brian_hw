# RTL Authoring Packet: module__todo_counter_pipe_regs__interrupts

- Kind: module
- Owner module: todo_counter_pipe_regs
- Owner file: rtl/todo_counter_pipe_regs.sv
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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model.handshake_rules.counter_irq, cycle_model.handshake_rules.prdata, cycle_model.handshake_rules.pready, cycle_model.pipeline.S0_APB_ACCESS, cycle_model.pipeline.S4_STATUS_UPDATE, decomposition.units.apb_decode, function_model.transactions.FM10, interrupts, io_list, io_list.interfaces.apb_slave, registers, registers.register_list, registers.register_list.CNT, registers.register_list.CTRL, registers.register_list.DBGCNT, registers.register_list.INTCLR
- Module slice: 5/7 section=interrupts task_limit=48
- Slice rule: Owner module todo_counter_pipe_regs is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - todo_counter_pipe_regs.bus_clk <= bus_clk (integration.connections[0])
  - todo_counter_pipe_regs.bus_rst_n <= bus_rst_n (integration.connections[1])
  - todo_counter_pipe_regs.irq_o <= counter_irq (integration.connections[2])

## Tasks

### RTL-0219: Implement interrupt item TC

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.TC
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.TC.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via interrupts.
SSOT item context: name=TC; clear=W1C via INTCLR.tc_clr (bit 0).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.TC
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - TC clear behavior matches SSOT clear policy W1C via INTCLR.tc_clr (bit 0)
- SSOT refs: interrupts.sources.TC

### RTL-0220: Implement interrupt item OVF

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.OVF
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.OVF.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via interrupts.
SSOT item context: name=OVF; clear=W1C via INTCLR.ovf_clr (bit 1); also clears STATUS.overflow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.OVF
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - OVF clear behavior matches SSOT clear policy W1C via INTCLR.ovf_clr (bit 1); also clears STATUS.overflow
- SSOT refs: interrupts.sources.OVF

### RTL-0221: Implement interrupt item UNF

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.UNF
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.UNF.
Owner: todo_counter_pipe_regs in rtl/todo_counter_pipe_regs.sv via interrupts.
SSOT item context: name=UNF; clear=W1C via INTCLR.unf_clr (bit 2); also clears STATUS.underflow.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.UNF
  - Primary implementation evidence is in rtl/todo_counter_pipe_regs.sv
  - UNF clear behavior matches SSOT clear policy W1C via INTCLR.unf_clr (bit 2); also clears STATUS.underflow
- SSOT refs: interrupts.sources.UNF
