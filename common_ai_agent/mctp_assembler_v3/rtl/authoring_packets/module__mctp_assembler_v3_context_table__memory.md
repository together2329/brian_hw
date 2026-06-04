# RTL Authoring Packet: module__mctp_assembler_v3_context_table__memory

- Kind: module
- Owner module: mctp_assembler_v3_context_table
- Owner file: rtl/mctp_assembler_v3_context_table.sv
- Task count: 1
- Required tasks: 1

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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: fsm, fsm.context_fsm, function_model, function_model.transactions.FM_ALLOC_CONTEXT, function_model.transactions.FM_APPEND
- Module slice: 4/6 section=memory task_limit=48
- Slice rule: Owner module mctp_assembler_v3_context_table is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])

## Tasks

### RTL-0394: Implement memory item context_table

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.context_table
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.context_table.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via memory.
SSOT item context: name=context_table; width=512; depth=15; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.context_table
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - context_table width matches SSOT value 512
  - context_table timing uses SSOT cycle/latency 0
  - context_table storage depth matches SSOT value 15
- SSOT refs: memory.instances.context_table
