# RTL Authoring Packet: module__mctp_assembler_scratch_v4_sram_packer

- Kind: module
- Owner module: mctp_assembler_scratch_v4_sram_packer
- Owner file: rtl/mctp_assembler_scratch_v4_sram_packer.sv
- Task count: 27
- Required tasks: 27

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
- Owner refs: dataflow, dataflow.sram_pack, function_model, function_model.transactions.FM_SRAM_PACK_WRITE, io_list, memory, memory.instances.payload_sram_window
- SSOT connection contracts:
  - mctp_assembler_scratch_v4_sram_packer.sram_wr_valid <= pack_wr_valid (integration.connections[2])

## Tasks

### RTL-0193: Implement transaction FM_SRAM_PACK_WRITE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: id=FM_SRAM_PACK_WRITE; name=Pack payload bytes into 32-byte SRAM beats with no holes.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE

### RTL-0194: Implement precondition for FM_SRAM_PACK_WRITE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: value=payload_valid and context_accept.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.preconditions.precondition_0

### RTL-0195: Implement output for FM_SRAM_PACK_WRITE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_0.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: value=sram_write_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_0

### RTL-0196: Implement output for FM_SRAM_PACK_WRITE: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_1.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: value=sram_write_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_1

### RTL-0197: Implement output for FM_SRAM_PACK_WRITE: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_2.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: value=sram_write_data.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_2

### RTL-0198: Implement output for FM_SRAM_PACK_WRITE: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_3.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: value=sram_write_strb.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.output_3

### RTL-0199: Implement output for FM_SRAM_PACK_WRITE: sram_write_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_valid.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_valid; port=sram_wr_valid; expr=payload_valid and (word_full or eom).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_valid RTL expression implements SSOT expression payload_valid and (word_full or eom)
  - DUT port sram_wr_valid is the implementation/observation point for sram_write_valid
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_valid

### RTL-0200: Implement output for FM_SRAM_PACK_WRITE: sram_write_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_addr; port=sram_wr_addr; expr=current_word_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_addr RTL expression implements SSOT expression current_word_addr
  - DUT port sram_wr_addr is the implementation/observation point for sram_write_addr
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_addr

### RTL-0201: Implement output for FM_SRAM_PACK_WRITE: sram_write_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_data.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_data; port=sram_wr_data; expr=payload_data_word.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_data
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_data RTL expression implements SSOT expression payload_data_word
  - DUT port sram_wr_data is the implementation/observation point for sram_write_data
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_data

### RTL-0202: Implement output for FM_SRAM_PACK_WRITE: sram_write_strb

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_strb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_strb.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_strb; port=sram_wr_strb; expr=payload_byte_strobe.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_strb
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_strb RTL expression implements SSOT expression payload_byte_strobe
  - DUT port sram_wr_strb is the implementation/observation point for sram_write_strb
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.sram_write_strb

### RTL-0203: Implement output for FM_SRAM_PACK_WRITE: ctx_partial_word_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: state=ctx_partial_word_addr; expr=current_word_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_addr RTL expression implements SSOT expression current_word_addr
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_addr

### RTL-0204: Implement output for FM_SRAM_PACK_WRITE: ctx_partial_next_lane

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_next_lane
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_next_lane.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: state=ctx_partial_next_lane; expr=ctx_partial_next_lane + lane_advance.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_next_lane RTL expression implements SSOT expression ctx_partial_next_lane + lane_advance
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_next_lane

### RTL-0205: Implement output for FM_SRAM_PACK_WRITE: ctx_partial_word_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_valid.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: state=ctx_partial_word_valid; expr=payload_valid and not word_full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_valid RTL expression implements SSOT expression payload_valid and not word_full
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_valid

### RTL-0206: Implement output for FM_SRAM_PACK_WRITE: ctx_partial_word_strobe

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_strobe
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_strobe.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: state=ctx_partial_word_strobe; expr=payload_byte_strobe.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_strobe
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_strobe RTL expression implements SSOT expression payload_byte_strobe
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_partial_word_strobe

### RTL-0207: Implement output for FM_SRAM_PACK_WRITE: ctx_payload_next_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_payload_next_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_payload_next_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: state=ctx_payload_next_addr; expr=ctx_payload_next_addr + payload_len.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_payload_next_addr RTL expression implements SSOT expression ctx_payload_next_addr + payload_len
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.outputs.ctx_payload_next_addr

### RTL-0208: Implement output rule for FM_SRAM_PACK_WRITE: sram_write_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_valid.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_valid; port=sram_wr_valid; expr=payload_valid and (word_full or eom); width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_valid width matches SSOT value 1
  - sram_write_valid RTL expression implements SSOT expression payload_valid and (word_full or eom)
  - DUT port sram_wr_valid is the implementation/observation point for sram_write_valid
  - sram_write_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_valid

### RTL-0209: Implement output rule for FM_SRAM_PACK_WRITE: sram_write_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_addr; port=sram_wr_addr; expr=current_word_addr; width=SRAM_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_addr width matches SSOT value SRAM_ADDR_WIDTH
  - sram_write_addr RTL expression implements SSOT expression current_word_addr
  - DUT port sram_wr_addr is the implementation/observation point for sram_write_addr
  - sram_write_addr is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_addr

### RTL-0210: Implement output rule for FM_SRAM_PACK_WRITE: sram_write_data

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_data
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_data.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_data; port=sram_wr_data; expr=payload_data_word; width=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_data
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_data width matches SSOT value 256
  - sram_write_data RTL expression implements SSOT expression payload_data_word
  - DUT port sram_wr_data is the implementation/observation point for sram_write_data
  - sram_write_data is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_data

### RTL-0211: Implement output rule for FM_SRAM_PACK_WRITE: sram_write_strb

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_strb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_strb.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=sram_write_strb; port=sram_wr_strb; expr=payload_byte_strobe; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_strb
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - sram_write_strb width matches SSOT value 32
  - sram_write_strb RTL expression implements SSOT expression payload_byte_strobe
  - DUT port sram_wr_strb is the implementation/observation point for sram_write_strb
  - sram_write_strb is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.output_rules.sram_write_strb

### RTL-0212: Implement state update for FM_SRAM_PACK_WRITE: ctx_partial_word_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=ctx_partial_word_addr; expr=current_word_addr; width=SRAM_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - ctx_partial_word_addr width matches SSOT value SRAM_ADDR_WIDTH
  - ctx_partial_word_addr RTL expression implements SSOT expression current_word_addr
  - ctx_partial_word_addr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_addr

### RTL-0213: Implement state update for FM_SRAM_PACK_WRITE: ctx_partial_next_lane

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_next_lane
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_next_lane.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=ctx_partial_next_lane; expr=ctx_partial_next_lane + lane_advance; width=5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - ctx_partial_next_lane width matches SSOT value 5
  - ctx_partial_next_lane RTL expression implements SSOT expression ctx_partial_next_lane + lane_advance
  - ctx_partial_next_lane updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_next_lane

### RTL-0214: Implement state update for FM_SRAM_PACK_WRITE: ctx_partial_word_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_valid.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=ctx_partial_word_valid; expr=payload_valid and not word_full; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - ctx_partial_word_valid width matches SSOT value 1
  - ctx_partial_word_valid RTL expression implements SSOT expression payload_valid and not word_full
  - ctx_partial_word_valid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_valid

### RTL-0215: Implement state update for FM_SRAM_PACK_WRITE: ctx_partial_word_strobe

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_strobe
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_strobe.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=ctx_partial_word_strobe; expr=payload_byte_strobe; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_strobe
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - ctx_partial_word_strobe width matches SSOT value 32
  - ctx_partial_word_strobe RTL expression implements SSOT expression payload_byte_strobe
  - ctx_partial_word_strobe updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_partial_word_strobe

### RTL-0216: Implement state update for FM_SRAM_PACK_WRITE: ctx_payload_next_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_payload_next_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_payload_next_addr.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: name=ctx_payload_next_addr; expr=ctx_payload_next_addr + payload_len; width=SRAM_ADDR_WIDTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - ctx_payload_next_addr width matches SSOT value SRAM_ADDR_WIDTH
  - ctx_payload_next_addr RTL expression implements SSOT expression ctx_payload_next_addr + payload_len
  - ctx_payload_next_addr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.state_updates.ctx_payload_next_addr

### RTL-0217: Implement side effect for FM_SRAM_PACK_WRITE: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_SRAM_PACK_WRITE.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_SRAM_PACK_WRITE.side_effects.side_effect_0.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via function_model.transactions.FM_SRAM_PACK_WRITE.
SSOT item context: id=FM_SRAM_PACK_WRITE; name=Pack payload bytes into 32-byte SRAM beats with no holes; port=["sram_wr_valid", "sram_wr_addr", "sram_wr_data", "sram_wr_strb"]; signal=["sram_write_beat_emitted_only_when_32B_word_full_or_final_fragment_flushes", "payload_valid", "payload_len", "lane_a...; state=["ctx_partial_word_addr", "ctx_partial_next_lane", "ctx_partial_word_valid", "ctx_partial_word_strobe", "ctx_payload_....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_SRAM_PACK_WRITE.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
  - DUT port ["sram_wr_valid", "sram_wr_addr", "sram_wr_data", "sram_wr_strb"] is the implementation/observation point for Pack payload bytes into 32-byte SRAM beats with no holes
- SSOT refs: function_model.transactions.FM_SRAM_PACK_WRITE.side_effects.side_effect_0

### RTL-0370: Implement memory item payload_sram_window

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.payload_sram_window
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.payload_sram_window.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via memory.instances.payload_sram_window.
SSOT item context: name=payload_sram_window.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.payload_sram_window
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: memory.instances.payload_sram_window

### RTL-0425: Prove module mctp_assembler_scratch_v4_sram_packer is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v4_sram_packer.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v4_sram_packer.module_equivalence.
Owner: mctp_assembler_scratch_v4_sram_packer in rtl/mctp_assembler_scratch_v4_sram_packer.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v4_sram_packer.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_sram_packer.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v4_sram_packer.module_equivalence
