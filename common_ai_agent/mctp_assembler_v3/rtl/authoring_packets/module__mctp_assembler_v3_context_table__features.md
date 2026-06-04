# RTL Authoring Packet: module__mctp_assembler_v3_context_table__features

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
- Module slice: 5/6 section=features task_limit=48
- Slice rule: Owner module mctp_assembler_v3_context_table is split into 6 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_modules=9, min_source_files=10
- SSOT connection contracts:
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])

## Tasks

### RTL-0447: Implement feature interleaved_assembly

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.interleaved_assembly
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.interleaved_assembly.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=interleaved_assembly; output=appended payload bytes + descriptor on EOM, or AD_* assembly drop.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.interleaved_assembly
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.interleaved_assembly
