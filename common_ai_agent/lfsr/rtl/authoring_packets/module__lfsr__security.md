# RTL Authoring Packet: module__lfsr__security

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: top_module, function_model, cycle_model
- Module slice: 11/13 section=security task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0110: Implement security item register_map

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.register_map
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.register_map.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=register_map.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.register_map
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: security.assets.register_map

### RTL-0111: Implement security item prbs_sequence

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.prbs_sequence
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.prbs_sequence.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=prbs_sequence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.prbs_sequence
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: security.assets.prbs_sequence
