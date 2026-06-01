# RTL Authoring Packet: module__mctp_assembler_scratch_apb_regfile__interrupts

- Kind: module
- Owner module: mctp_assembler_scratch_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_apb_regfile.sv
- Task count: 4
- Required tasks: 4

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
- Module slice: 7/9 section=interrupts task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0371: Implement interrupt item IRQ_DESCRIPTOR

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.IRQ_DESCRIPTOR
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.IRQ_DESCRIPTOR.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via interrupts.sources.
SSOT item context: id=IRQ_DESCRIPTOR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.IRQ_DESCRIPTOR
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: interrupts.sources.IRQ_DESCRIPTOR

### RTL-0372: Implement interrupt item IRQ_PACKET_DROP

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.IRQ_PACKET_DROP
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.IRQ_PACKET_DROP.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via interrupts.sources.
SSOT item context: id=IRQ_PACKET_DROP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.IRQ_PACKET_DROP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: interrupts.sources.IRQ_PACKET_DROP

### RTL-0373: Implement interrupt item IRQ_ASSEMBLY_DROP

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.IRQ_ASSEMBLY_DROP
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.IRQ_ASSEMBLY_DROP.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via interrupts.sources.
SSOT item context: id=IRQ_ASSEMBLY_DROP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.IRQ_ASSEMBLY_DROP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: interrupts.sources.IRQ_ASSEMBLY_DROP

### RTL-0374: Implement interrupt item IRQ_READ_ERROR

- Priority: high
- Required: True
- Status: pass
- Category: interrupts.sources
- Source ref: interrupts.sources.IRQ_READ_ERROR
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.IRQ_READ_ERROR.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via interrupts.sources.
SSOT item context: id=IRQ_READ_ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.IRQ_READ_ERROR
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: interrupts.sources.IRQ_READ_ERROR
