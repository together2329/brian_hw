# RTL Authoring Packet: module__mctp_assembler_v3_sram_packer

- Kind: module
- Owner module: mctp_assembler_v3_sram_packer
- Owner file: rtl/mctp_assembler_v3_sram_packer.sv
- Task count: 24
- Required tasks: 24

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
- LLM-actionable open tasks: 24
- Human-locked open tasks: 0
- Owner refs: features, features.payload_pack, function_model, function_model.transactions.FM_PACK_SRAM, memory
- SSOT connection contracts:
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])

## Tasks

### RTL-0228: Implement transaction FM_PACK_SRAM

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PACK_SRAM
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PACK_SRAM.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: id=FM_PACK_SRAM; name=payload_pack_write.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: function_model.transactions.FM_PACK_SRAM

### RTL-0229: Implement precondition for FM_PACK_SRAM: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PACK_SRAM.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.preconditions.precondition_0.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: value=accepted payload bytes for a context.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: function_model.transactions.FM_PACK_SRAM.preconditions.precondition_0

### RTL-0230: Implement input for FM_PACK_SRAM: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_PACK_SRAM.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.inputs.input_0.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: id=FM_PACK_SRAM; name=payload_pack_write; port=["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"]; signal=["payload bytes", "payload_bytes"]; state=["ctx_payload_next_addr", "ctx_partial_next_lane", "payload_bytes_written_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - DUT port ["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"] is the implementation/observation point for payload_pack_write
- SSOT refs: function_model.transactions.FM_PACK_SRAM.inputs.input_0

### RTL-0231: Implement input for FM_PACK_SRAM: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_PACK_SRAM.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.inputs.input_1.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: id=FM_PACK_SRAM; name=payload_pack_write; port=["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"]; signal=["ctx partial_word state", "payload_bytes"]; state=["ctx_payload_next_addr", "ctx_partial_next_lane", "payload_bytes_written_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.inputs.input_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - DUT port ["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"] is the implementation/observation point for payload_pack_write
- SSOT refs: function_model.transactions.FM_PACK_SRAM.inputs.input_1

### RTL-0232: Implement output for FM_PACK_SRAM: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.output_0.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: value=256-bit sram_write beats; payload byte i at byte address base_addr+i; sram_wr_strb marks only payload lanes; full wor....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.output_0

### RTL-0233: Implement output for FM_PACK_SRAM: sram_wr_valid

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_valid.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_valid; port=sram_wr_valid; expr=payload_bytes > 0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_valid RTL expression implements SSOT expression payload_bytes > 0
  - DUT port sram_wr_valid is the implementation/observation point for sram_wr_valid
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_valid

### RTL-0234: Implement output for FM_PACK_SRAM: sram_wr_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_addr.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_addr; port=sram_wr_addr; expr=ctx_payload_next_addr & ~31.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_addr RTL expression implements SSOT expression ctx_payload_next_addr & ~31
  - DUT port sram_wr_addr is the implementation/observation point for sram_wr_addr
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_addr

### RTL-0235: Implement output for FM_PACK_SRAM: sram_wr_strb

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_strb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_strb.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_strb; port=sram_wr_strb; expr=(((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31)).
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_strb
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_strb RTL expression implements SSOT expression (((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31))
  - DUT port sram_wr_strb is the implementation/observation point for sram_wr_strb
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.sram_wr_strb

### RTL-0236: Implement output for FM_PACK_SRAM: ctx_payload_next_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.ctx_payload_next_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.ctx_payload_next_addr.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: state=ctx_payload_next_addr; expr=ctx_payload_next_addr + payload_bytes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - function_model.transactions.FM_PACK_SRAM.outputs.ctx_payload_next_addr RTL expression implements SSOT expression ctx_payload_next_addr + payload_bytes
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.ctx_payload_next_addr

### RTL-0237: Implement output for FM_PACK_SRAM: ctx_partial_next_lane

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.ctx_partial_next_lane
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.ctx_partial_next_lane.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: state=ctx_partial_next_lane; expr=(ctx_partial_next_lane + payload_bytes) % 32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - function_model.transactions.FM_PACK_SRAM.outputs.ctx_partial_next_lane RTL expression implements SSOT expression (ctx_partial_next_lane + payload_bytes) % 32
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.ctx_partial_next_lane

### RTL-0238: Implement output for FM_PACK_SRAM: payload_bytes_written_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACK_SRAM.outputs.payload_bytes_written_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.outputs.payload_bytes_written_count.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: state=payload_bytes_written_count; expr=payload_bytes_written_count + payload_bytes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.outputs.payload_bytes_written_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - function_model.transactions.FM_PACK_SRAM.outputs.payload_bytes_written_count RTL expression implements SSOT expression payload_bytes_written_count + payload_bytes
- SSOT refs: function_model.transactions.FM_PACK_SRAM.outputs.payload_bytes_written_count

### RTL-0239: Implement output rule for FM_PACK_SRAM: sram_wr_valid

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_valid.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_valid; port=sram_wr_valid; expr=payload_bytes > 0; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_valid width matches SSOT value 1
  - sram_wr_valid RTL expression implements SSOT expression payload_bytes > 0
  - DUT port sram_wr_valid is the implementation/observation point for sram_wr_valid
  - sram_wr_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_valid

### RTL-0240: Implement output rule for FM_PACK_SRAM: sram_wr_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_addr.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_addr; port=sram_wr_addr; expr=ctx_payload_next_addr & ~31; width=16.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_addr width matches SSOT value 16
  - sram_wr_addr RTL expression implements SSOT expression ctx_payload_next_addr & ~31
  - DUT port sram_wr_addr is the implementation/observation point for sram_wr_addr
  - sram_wr_addr is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_addr

### RTL-0241: Implement output rule for FM_PACK_SRAM: sram_wr_strb

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_strb
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_strb.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=sram_wr_strb; port=sram_wr_strb; expr=(((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31)); width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_strb
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - sram_wr_strb width matches SSOT value 32
  - sram_wr_strb RTL expression implements SSOT expression (((1 << payload_bytes) - 1) << (ctx_payload_next_addr & 31))
  - DUT port sram_wr_strb is the implementation/observation point for sram_wr_strb
  - sram_wr_strb is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PACK_SRAM.output_rules.sram_wr_strb

### RTL-0242: Implement state update for FM_PACK_SRAM: ctx_payload_next_addr

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_payload_next_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_payload_next_addr.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=ctx_payload_next_addr; expr=ctx_payload_next_addr + payload_bytes; width=16.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.state_updates.ctx_payload_next_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - ctx_payload_next_addr width matches SSOT value 16
  - ctx_payload_next_addr RTL expression implements SSOT expression ctx_payload_next_addr + payload_bytes
  - ctx_payload_next_addr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_payload_next_addr

### RTL-0243: Implement state update for FM_PACK_SRAM: ctx_partial_next_lane

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_partial_next_lane
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_partial_next_lane.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=ctx_partial_next_lane; expr=(ctx_partial_next_lane + payload_bytes) % 32; width=5.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.state_updates.ctx_partial_next_lane
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - ctx_partial_next_lane width matches SSOT value 5
  - ctx_partial_next_lane RTL expression implements SSOT expression (ctx_partial_next_lane + payload_bytes) % 32
  - ctx_partial_next_lane updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PACK_SRAM.state_updates.ctx_partial_next_lane

### RTL-0244: Implement state update for FM_PACK_SRAM: payload_bytes_written_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PACK_SRAM.state_updates.payload_bytes_written_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.state_updates.payload_bytes_written_count.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: name=payload_bytes_written_count; expr=payload_bytes_written_count + payload_bytes; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.state_updates.payload_bytes_written_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - payload_bytes_written_count width matches SSOT value 32
  - payload_bytes_written_count RTL expression implements SSOT expression payload_bytes_written_count + payload_bytes
  - payload_bytes_written_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PACK_SRAM.state_updates.payload_bytes_written_count

### RTL-0245: Implement side effect for FM_PACK_SRAM: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PACK_SRAM.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.side_effects.side_effect_0.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: id=FM_PACK_SRAM; name=payload_pack_write; port=["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"]; signal=["ctx_payload_next_addr advanced; payload_bytes_written_count += bytes", "payload_bytes"]; state=["ctx_payload_next_addr", "ctx_partial_next_lane", "payload_bytes_written_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - DUT port ["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"] is the implementation/observation point for payload_pack_write
- SSOT refs: function_model.transactions.FM_PACK_SRAM.side_effects.side_effect_0

### RTL-0246: Implement error case for FM_PACK_SRAM: error_case_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACK_SRAM.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACK_SRAM.error_cases.error_case_0.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via function_model.transactions.FM_PACK_SRAM.
SSOT item context: id=FM_PACK_SRAM; name=payload_pack_write; port=["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"]; signal=[{"condition": "allocation/write would exceed sram_base/limit or SRAM_ADDR_WIDTH", "result": "AD_SRAM_OVERFLOW assemb...; state=["ctx_payload_next_addr", "ctx_partial_next_lane", "payload_bytes_written_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACK_SRAM.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
  - DUT port ["sram_wr_valid", "sram_wr_addr", "sram_wr_strb"] is the implementation/observation point for payload_pack_write
- SSOT refs: function_model.transactions.FM_PACK_SRAM.error_cases.error_case_0

### RTL-0387: Implement memory item context_table

- Priority: high
- Required: True
- Status: planned
- Category: memory.instances
- Source ref: memory.instances.context_table
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.context_table.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via memory.
SSOT item context: name=context_table; width=512; depth=15; latency=0.
- Current reason: RTL audit has not run yet.
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

### RTL-0441: Implement feature payload_pack

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.payload_pack
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.payload_pack.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via features.payload_pack.
SSOT item context: name=payload_pack; output=sram_write beats with strb marking valid payload lanes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.payload_pack
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: features.payload_pack

### RTL-0468: Prove module mctp_assembler_v3_sram_packer is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_sram_packer.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_sram_packer.module_equivalence.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_sram_packer.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: sub_modules.mctp_assembler_v3_sram_packer.module_equivalence

### RTL-0038: Implement parameter SRAM_ADDR_WIDTH

- Priority: normal
- Required: True
- Status: planned
- Category: parameters.item
- Source ref: parameters.SRAM_ADDR_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SRAM_ADDR_WIDTH.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via semantic_terms:sram.
SSOT item context: name=SRAM_ADDR_WIDTH.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SRAM_ADDR_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: parameters.SRAM_ADDR_WIDTH

### RTL-0039: Implement parameter SRAM_DATA_WIDTH

- Priority: normal
- Required: True
- Status: planned
- Category: parameters.item
- Source ref: parameters.SRAM_DATA_WIDTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SRAM_DATA_WIDTH.
Owner: mctp_assembler_v3_sram_packer in rtl/mctp_assembler_v3_sram_packer.sv via semantic_terms:sram.
SSOT item context: name=SRAM_DATA_WIDTH.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SRAM_DATA_WIDTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3_sram_packer.sv
- SSOT refs: parameters.SRAM_DATA_WIDTH
