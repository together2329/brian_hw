# RTL Authoring Packet: module__mctp_assembler_v3_mctp_decoder

- Kind: module
- Owner module: mctp_assembler_v3_mctp_decoder
- Owner file: rtl/mctp_assembler_v3_mctp_decoder.sv
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

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 27
- Human-locked open tasks: 0
- Owner refs: features, features.mctp_decode, function_model, function_model.transactions.FM_DECODE_MCTP

## Tasks

### RTL-0157: Implement transaction FM_DECODE_MCTP

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DECODE_MCTP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: id=FM_DECODE_MCTP; name=mctp_transport_decode.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP

### RTL-0158: Implement precondition for FM_DECODE_MCTP: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DECODE_MCTP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.preconditions.precondition_0.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: value=validated VDM payload present.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.preconditions.precondition_0

### RTL-0159: Implement input for FM_DECODE_MCTP: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_DECODE_MCTP.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.inputs.input_0.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: id=FM_DECODE_MCTP; name=mctp_transport_decode; signal=["MCTP transport header (last 4B of 16B header)", "header_version", "mctp_byte0", "dest_filter_enable", "dest_eid", "...; state=["header_version_ok", "som", "eom", "packet_seq", "tag_owner", "message_tag", "dest_accept", "assembly_key"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.inputs.input_0

### RTL-0160: Implement input for FM_DECODE_MCTP: input_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_DECODE_MCTP.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.inputs.input_1.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: id=FM_DECODE_MCTP; name=mctp_transport_decode; signal=["SOM body byte (IC+message_type) when SOM=1", "header_version", "mctp_byte0", "dest_filter_enable", "dest_eid", "loc...; state=["header_version_ok", "som", "eom", "packet_seq", "tag_owner", "message_tag", "dest_accept", "assembly_key"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.inputs.input_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.inputs.input_1

### RTL-0161: Implement output for FM_DECODE_MCTP: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_0.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: value=header_version, dest_eid, source_eid, SOM, EOM, packet_seq, tag_owner, message_tag.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.output_0

### RTL-0162: Implement output for FM_DECODE_MCTP: output_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_1.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: value=ic, message_type on SOM.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.output_1

### RTL-0163: Implement output for FM_DECODE_MCTP: output_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.output_2.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: value=assembly_key={source_eid,tag_owner,message_tag}.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.output_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.output_2

### RTL-0164: Implement output for FM_DECODE_MCTP: header_version_ok

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.header_version_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.header_version_ok.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=header_version_ok; expr=header_version == 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.header_version_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.header_version_ok RTL expression implements SSOT expression header_version == 1
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.header_version_ok

### RTL-0165: Implement output for FM_DECODE_MCTP: som

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.som
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.som.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=som; expr=mctp_byte0[7].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.som
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.som RTL expression implements SSOT expression mctp_byte0[7]
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.som

### RTL-0166: Implement output for FM_DECODE_MCTP: eom

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.eom
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.eom.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=eom; expr=mctp_byte0[6].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.eom
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.eom RTL expression implements SSOT expression mctp_byte0[6]
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.eom

### RTL-0167: Implement output for FM_DECODE_MCTP: packet_seq

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.packet_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.packet_seq.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=packet_seq; expr=mctp_byte0[5:4].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.packet_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.packet_seq RTL expression implements SSOT expression mctp_byte0[5:4]
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.packet_seq

### RTL-0168: Implement output for FM_DECODE_MCTP: tag_owner

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.tag_owner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.tag_owner.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=tag_owner; expr=mctp_byte0[3].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.tag_owner RTL expression implements SSOT expression mctp_byte0[3]
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.tag_owner

### RTL-0169: Implement output for FM_DECODE_MCTP: message_tag

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.message_tag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.message_tag.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=message_tag; expr=mctp_byte0[2:0].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.message_tag RTL expression implements SSOT expression mctp_byte0[2:0]
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.message_tag

### RTL-0170: Implement output for FM_DECODE_MCTP: dest_accept

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.dest_accept
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.dest_accept.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=dest_accept; expr=(not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.dest_accept
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.dest_accept RTL expression implements SSOT expression (not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_...
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.dest_accept

### RTL-0171: Implement output for FM_DECODE_MCTP: assembly_key

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_MCTP.outputs.assembly_key
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.outputs.assembly_key.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: state=assembly_key; expr=((source_eid << 4) | (tag_owner << 3) | message_tag).
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.outputs.assembly_key
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - function_model.transactions.FM_DECODE_MCTP.outputs.assembly_key RTL expression implements SSOT expression ((source_eid << 4) | (tag_owner << 3) | message_tag)
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.outputs.assembly_key

### RTL-0172: Implement state update for FM_DECODE_MCTP: header_version_ok

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.header_version_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.header_version_ok.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=header_version_ok; expr=header_version == 1; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.header_version_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - header_version_ok width matches SSOT value 1
  - header_version_ok RTL expression implements SSOT expression header_version == 1
  - header_version_ok updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.header_version_ok

### RTL-0173: Implement state update for FM_DECODE_MCTP: som

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.som
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.som.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=som; expr=mctp_byte0[7]; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.som
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - som width matches SSOT value 1
  - som RTL expression implements SSOT expression mctp_byte0[7]
  - som updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.som

### RTL-0174: Implement state update for FM_DECODE_MCTP: eom

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.eom
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.eom.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=eom; expr=mctp_byte0[6]; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.eom
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - eom width matches SSOT value 1
  - eom RTL expression implements SSOT expression mctp_byte0[6]
  - eom updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.eom

### RTL-0175: Implement state update for FM_DECODE_MCTP: packet_seq

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.packet_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.packet_seq.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=packet_seq; expr=mctp_byte0[5:4]; width=2.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.packet_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - packet_seq width matches SSOT value 2
  - packet_seq RTL expression implements SSOT expression mctp_byte0[5:4]
  - packet_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.packet_seq

### RTL-0176: Implement state update for FM_DECODE_MCTP: tag_owner

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.tag_owner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.tag_owner.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=tag_owner; expr=mctp_byte0[3]; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - tag_owner width matches SSOT value 1
  - tag_owner RTL expression implements SSOT expression mctp_byte0[3]
  - tag_owner updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.tag_owner

### RTL-0177: Implement state update for FM_DECODE_MCTP: message_tag

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.message_tag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.message_tag.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=message_tag; expr=mctp_byte0[2:0]; width=3.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - message_tag width matches SSOT value 3
  - message_tag RTL expression implements SSOT expression mctp_byte0[2:0]
  - message_tag updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.message_tag

### RTL-0178: Implement state update for FM_DECODE_MCTP: dest_accept

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.dest_accept
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.dest_accept.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=dest_accept; expr=(not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_...; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.dest_accept
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - dest_accept width matches SSOT value 1
  - dest_accept RTL expression implements SSOT expression (not dest_filter_enable) or (dest_eid == local_eid) or (accept_broadcast_eid and (dest_eid == 0xFF)) or (accept_null_...
  - dest_accept updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.dest_accept

### RTL-0179: Implement state update for FM_DECODE_MCTP: assembly_key

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_MCTP.state_updates.assembly_key
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.state_updates.assembly_key.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: name=assembly_key; expr=((source_eid << 4) | (tag_owner << 3) | message_tag); width=12.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.state_updates.assembly_key
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
  - assembly_key width matches SSOT value 12
  - assembly_key RTL expression implements SSOT expression ((source_eid << 4) | (tag_owner << 3) | message_tag)
  - assembly_key updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.state_updates.assembly_key

### RTL-0180: Implement error case for FM_DECODE_MCTP: error_case_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_0.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: id=FM_DECODE_MCTP; name=mctp_transport_decode; signal=[{"condition": "header not present / version!=1 / SOM packet without body byte", "result": "PD_BAD_MCTP_HEADER packet...; state=["header_version_ok", "som", "eom", "packet_seq", "tag_owner", "message_tag", "dest_accept", "assembly_key"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_0

### RTL-0181: Implement error case for FM_DECODE_MCTP: error_case_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_1.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via function_model.transactions.FM_DECODE_MCTP.
SSOT item context: id=FM_DECODE_MCTP; name=mctp_transport_decode; signal=[{"condition": "dest_eid not local and not accepted broadcast/null while dest_filter_enable", "result": "PD_DEST_EID_...; state=["header_version_ok", "som", "eom", "packet_seq", "tag_owner", "message_tag", "dest_accept", "assembly_key"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: function_model.transactions.FM_DECODE_MCTP.error_cases.error_case_1

### RTL-0439: Implement feature mctp_decode

- Priority: high
- Required: True
- Status: planned
- Category: features.item
- Source ref: features.mctp_decode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.mctp_decode.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via features.mctp_decode.
SSOT item context: name=mctp_decode; output=MCTP fields + assembly key, or PD_BAD_MCTP_HEADER / PD_DEST_EID_REJECT.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.mctp_decode
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: features.mctp_decode

### RTL-0466: Prove module mctp_assembler_v3_mctp_decoder is functionally equivalent to FL

- Priority: high
- Required: True
- Status: planned
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_mctp_decoder.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_mctp_decoder.module_equivalence.
Owner: mctp_assembler_v3_mctp_decoder in rtl/mctp_assembler_v3_mctp_decoder.sv via module_equivalence.
- Current reason: RTL audit has not run yet.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_mctp_decoder.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_mctp_decoder.sv
- SSOT refs: sub_modules.mctp_assembler_v3_mctp_decoder.module_equivalence
