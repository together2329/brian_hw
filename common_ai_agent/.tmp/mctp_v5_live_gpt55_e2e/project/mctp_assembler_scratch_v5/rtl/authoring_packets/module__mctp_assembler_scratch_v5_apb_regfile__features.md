# RTL Authoring Packet: module__mctp_assembler_scratch_v5_apb_regfile__features

- Kind: module
- Owner module: mctp_assembler_scratch_v5_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_v5_apb_regfile.sv
- Task count: 3
- Required tasks: 3

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
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 6/9 section=features task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_v5_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0386: Implement feature primary_approved_behavior

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.primary_approved_behavior
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.primary_approved_behavior.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via features.
SSOT item context: name=primary_approved_behavior; output=Observable outputs/status/events match function_model outputs and side effects.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.primary_approved_behavior
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
- SSOT refs: features.primary_approved_behavior

### RTL-0387: Implement feature backpressure_stability

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.backpressure_stability
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.backpressure_stability.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via features.
SSOT item context: name=backpressure_stability; output=No duplicated, dropped, or reordered transaction unless explicitly allowed.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.backpressure_stability
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
- SSOT refs: features.backpressure_stability

### RTL-0388: Implement feature error_policy

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.error_policy
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.error_policy.
Owner: mctp_assembler_scratch_v5_apb_regfile in rtl/mctp_assembler_scratch_v5_apb_regfile.sv via features.
SSOT item context: name=error_policy; output=Error/status/response/debug behavior follows error_handling.propagation.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.error_policy
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_apb_regfile.sv
- SSOT refs: features.error_policy
