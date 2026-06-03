# RTL Authoring Packet: module__mctp_assembler_v3_context_table__equivalence

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: fsm, fsm.context_fsm, function_model, function_model.transactions.FM_ALLOC_CONTEXT, function_model.transactions.FM_APPEND
- Module slice: 4/4 section=equivalence task_limit=48
- Slice rule: Owner module mctp_assembler_v3_context_table is split into 4 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])

## Tasks

### RTL-0467: Prove module mctp_assembler_v3_context_table is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_context_table.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_context_table.module_equivalence.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_context_table.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: sub_modules.mctp_assembler_v3_context_table.module_equivalence
