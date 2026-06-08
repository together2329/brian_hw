# RTL Authoring Packet: module__timer__security

- Kind: module
- Owner module: timer
- Owner file: rtl/timer.sv
- Task count: 2
- Required tasks: 2

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
- Module slice: 5/8 section=security task_limit=48
- Slice rule: Owner module timer is split into 8 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - timer_regs.pclk <= pclk (integration.connections[0])
  - timer_regs.presetn <= presetn (integration.connections[1])
  - timer_regs.paddr <= paddr (integration.connections[2])
  - timer_regs.psel <= psel (integration.connections[3])
  - timer_regs.penable <= penable (integration.connections[4])
  - timer_regs.pwrite <= pwrite (integration.connections[5])
  - timer_regs.pwdata <= pwdata (integration.connections[6])
  - timer_regs.prdata <= prdata (integration.connections[7])
  - timer_regs.pready <= pready (integration.connections[8])
  - timer_regs.pslverr <= pslverr (integration.connections[9])
  - timer_regs.load_q <= load_q (integration.connections[10])
  - timer_regs.enable_q <= enable_q (integration.connections[11])
- SSOT top IO contracts: 11

## Tasks

### RTL-0182: Implement security item timer_configuration

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.timer_configuration
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.timer_configuration.
Owner: timer in rtl/timer.sv via top_fallback.
SSOT item context: name=timer_configuration.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.timer_configuration
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: security.assets.timer_configuration

### RTL-0183: Implement security item interrupt_integrity

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.interrupt_integrity
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.interrupt_integrity.
Owner: timer in rtl/timer.sv via top_fallback.
SSOT item context: name=interrupt_integrity.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.interrupt_integrity
  - Primary implementation evidence is in rtl/timer.sv
- SSOT refs: security.assets.interrupt_integrity
