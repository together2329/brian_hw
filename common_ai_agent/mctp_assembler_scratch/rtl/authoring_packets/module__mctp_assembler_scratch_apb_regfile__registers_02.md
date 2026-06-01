# RTL Authoring Packet: module__mctp_assembler_scratch_apb_regfile__registers_02

- Kind: module
- Owner module: mctp_assembler_scratch_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_apb_regfile.sv
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
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 5/9 section=registers task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0365: Implement field Q_PAYLOAD_COUNT.partial_word_valid

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_word_valid
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_word_valid.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via registers.register_list.
SSOT item context: name=partial_word_valid; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_COUNT.fields.partial_word_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - partial_word_valid reset behavior matches SSOT value 0
  - partial_word_valid access policy ro is implemented without read/write shortcuts
  - partial_word_valid readback returns implemented RTL state when readable
  - partial_word_valid write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_PAYLOAD_COUNT.fields.partial_word_valid

### RTL-0366: Implement field Q_PAYLOAD_COUNT.reserved

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.Q_PAYLOAD_COUNT.fields.reserved
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.Q_PAYLOAD_COUNT.fields.reserved.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via registers.register_list.
SSOT item context: name=reserved; reset=0; access=reserved.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.Q_PAYLOAD_COUNT.fields.reserved
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - reserved reset behavior matches SSOT value 0
  - reserved access policy reserved is implemented without read/write shortcuts
  - reserved readback returns implemented RTL state when readable
  - reserved write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.Q_PAYLOAD_COUNT.fields.reserved
