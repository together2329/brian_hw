# RTL Authoring Packet: module__mctp_assembler_v3_apb_regfile__interrupts

- Kind: module
- Owner module: mctp_assembler_v3_apb_regfile
- Owner file: rtl/mctp_assembler_v3_apb_regfile.sv
- Task count: 9
- Required tasks: 9

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
- LLM-actionable open tasks: 9
- Human-locked open tasks: 0
- Owner refs: decomposition, error_handling, features, function_model.state_variables, interrupts, registers, registers.register_list
- Module slice: 5/7 section=interrupts task_limit=48
- Slice rule: Owner module mctp_assembler_v3_apb_regfile is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])

## Tasks

### RTL-0389: Implement interrupt item descriptor_ready

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.descriptor_ready
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.descriptor_ready.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=descriptor_ready; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.descriptor_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_ready clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.descriptor_ready

### RTL-0390: Implement interrupt item packet_drop

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.packet_drop
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.packet_drop.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=packet_drop; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.packet_drop
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - packet_drop clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.packet_drop

### RTL-0391: Implement interrupt item assembly_drop

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.assembly_drop
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.assembly_drop.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=assembly_drop; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.assembly_drop
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - assembly_drop clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.assembly_drop

### RTL-0392: Implement interrupt item context_timeout

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.context_timeout
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.context_timeout.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=context_timeout; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.context_timeout
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - context_timeout clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.context_timeout

### RTL-0393: Implement interrupt item sram_overflow

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.sram_overflow
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.sram_overflow.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=sram_overflow; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.sram_overflow
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - sram_overflow clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.sram_overflow

### RTL-0394: Implement interrupt item descriptor_queue_full

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.descriptor_queue_full
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.descriptor_queue_full.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=descriptor_queue_full; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.descriptor_queue_full
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - descriptor_queue_full clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.descriptor_queue_full

### RTL-0395: Implement interrupt item axi_write_malformed

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.axi_write_malformed
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.axi_write_malformed.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=axi_write_malformed; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.axi_write_malformed
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - axi_write_malformed clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.axi_write_malformed

### RTL-0396: Implement interrupt item axi_read_error

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.axi_read_error
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.axi_read_error.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=axi_read_error; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.axi_read_error
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - axi_read_error clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.axi_read_error

### RTL-0397: Implement interrupt item fatal_internal_error

- Priority: high
- Required: True
- Status: planned
- Category: interrupts.sources
- Source ref: interrupts.sources.fatal_internal_error
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.fatal_internal_error.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via interrupts.
SSOT item context: name=fatal_internal_error; clear=W1C.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.fatal_internal_error
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - fatal_internal_error clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.fatal_internal_error
