# RTL Authoring Packet: module__mctp_assembler_v3_apb_regfile__error_handling

- Kind: module
- Owner module: mctp_assembler_v3_apb_regfile
- Owner file: rtl/mctp_assembler_v3_apb_regfile.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: decomposition, error_handling, features, function_model.state_variables, interrupts, registers, registers.register_list
- Module slice: 4/7 section=error_handling task_limit=48
- Slice rule: Owner module mctp_assembler_v3_apb_regfile is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])

## Tasks

### RTL-0445: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: open
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via error_handling.
SSOT item context: action=software W1C interrupt clear + counter_clear + per-context clear policy.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_apb_regfile.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
- SSOT refs: error_handling.recovery.recovery_0
