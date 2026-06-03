# RTL Authoring Packet: module__mctp_assembler_v3_pcie_vdm_parser

- Kind: module
- Owner module: mctp_assembler_v3_pcie_vdm_parser
- Owner file: rtl/mctp_assembler_v3_pcie_vdm_parser.sv
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
- Owner refs: dataflow, features, features.vdm_decode, function_model, function_model.transactions.FM_DECODE_VDM

## Tasks

### RTL-0140: Implement transaction FM_DECODE_VDM

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_DECODE_VDM
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_DECODE_VDM.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: id=FM_DECODE_VDM; name=pcie_vdm_decode.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM

### RTL-0141: Implement precondition for FM_DECODE_VDM: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_DECODE_VDM.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.preconditions.precondition_0.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: value=legal TLP bytes available.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.preconditions.precondition_0

### RTL-0142: Implement input for FM_DECODE_VDM: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_DECODE_VDM.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.inputs.input_0.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: id=FM_DECODE_VDM; name=pcie_vdm_decode; signal=["raw TLP bytes 0..15", "message_code", "vendor_id", "vdm_code", "routing_supported", "traffic_class", "tlp", "pad_le...; state=["vdm_valid", "payload_offset", "requester_id", "pad_ok", "last_decoded_vdm"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.inputs.input_0

### RTL-0143: Implement output for FM_DECODE_VDM: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.output_0.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: value=requester_id, pcie_routing_type, message_code, vendor_id, vdm_code, payload_offset(16), pad_len.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.output_0

### RTL-0144: Implement output for FM_DECODE_VDM: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.output_1.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: value=first 16B header snapshot candidate.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.output_1

### RTL-0145: Implement output for FM_DECODE_VDM: vdm_valid

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.vdm_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.vdm_valid.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: state=vdm_valid; expr=(message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0).
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.vdm_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - function_model.transactions.FM_DECODE_VDM.outputs.vdm_valid RTL expression implements SSOT expression (message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0)
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.vdm_valid

### RTL-0146: Implement output for FM_DECODE_VDM: payload_offset

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.payload_offset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.payload_offset.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: state=payload_offset; expr=16.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.payload_offset
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - function_model.transactions.FM_DECODE_VDM.outputs.payload_offset RTL expression implements SSOT expression 16
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.payload_offset

### RTL-0147: Implement output for FM_DECODE_VDM: requester_id

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.requester_id
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.requester_id.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: state=requester_id; expr=((tlp[1] << 8) | tlp[2]).
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.requester_id
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - function_model.transactions.FM_DECODE_VDM.outputs.requester_id RTL expression implements SSOT expression ((tlp[1] << 8) | tlp[2])
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.requester_id

### RTL-0148: Implement output for FM_DECODE_VDM: pad_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.pad_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.pad_ok.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: state=pad_ok; expr=(pad_len <= 3) and ((pad_len == 0) if not eom else True).
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.pad_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - function_model.transactions.FM_DECODE_VDM.outputs.pad_ok RTL expression implements SSOT expression (pad_len <= 3) and ((pad_len == 0) if not eom else True)
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.pad_ok

### RTL-0149: Implement output for FM_DECODE_VDM: last_decoded_vdm

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_DECODE_VDM.outputs.last_decoded_vdm
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.outputs.last_decoded_vdm.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: state=last_decoded_vdm; expr=((message_code << 24) | (vendor_id << 8) | vdm_code).
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.outputs.last_decoded_vdm
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - function_model.transactions.FM_DECODE_VDM.outputs.last_decoded_vdm RTL expression implements SSOT expression ((message_code << 24) | (vendor_id << 8) | vdm_code)
- SSOT refs: function_model.transactions.FM_DECODE_VDM.outputs.last_decoded_vdm

### RTL-0150: Implement state update for FM_DECODE_VDM: vdm_valid

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_VDM.state_updates.vdm_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.state_updates.vdm_valid.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: name=vdm_valid; expr=(message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0); width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.state_updates.vdm_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - vdm_valid width matches SSOT value 1
  - vdm_valid RTL expression implements SSOT expression (message_code == 0x7F) and (vendor_id == 0x1AB4) and (vdm_code == 0x0) and routing_supported and (traffic_class == 0)
  - vdm_valid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_VDM.state_updates.vdm_valid

### RTL-0151: Implement state update for FM_DECODE_VDM: payload_offset

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_VDM.state_updates.payload_offset
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.state_updates.payload_offset.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: name=payload_offset; expr=16; width=5.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.state_updates.payload_offset
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - payload_offset width matches SSOT value 5
  - payload_offset RTL expression implements SSOT expression 16
  - payload_offset updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_VDM.state_updates.payload_offset

### RTL-0152: Implement state update for FM_DECODE_VDM: requester_id

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_VDM.state_updates.requester_id
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.state_updates.requester_id.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: name=requester_id; expr=((tlp[1] << 8) | tlp[2]); width=16.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.state_updates.requester_id
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - requester_id width matches SSOT value 16
  - requester_id RTL expression implements SSOT expression ((tlp[1] << 8) | tlp[2])
  - requester_id updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_VDM.state_updates.requester_id

### RTL-0153: Implement state update for FM_DECODE_VDM: pad_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_VDM.state_updates.pad_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.state_updates.pad_ok.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: name=pad_ok; expr=(pad_len <= 3) and ((pad_len == 0) if not eom else True); width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.state_updates.pad_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - pad_ok width matches SSOT value 1
  - pad_ok RTL expression implements SSOT expression (pad_len <= 3) and ((pad_len == 0) if not eom else True)
  - pad_ok updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_VDM.state_updates.pad_ok

### RTL-0154: Implement state update for FM_DECODE_VDM: last_decoded_vdm

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_DECODE_VDM.state_updates.last_decoded_vdm
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.state_updates.last_decoded_vdm.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: name=last_decoded_vdm; expr=((message_code << 24) | (vendor_id << 8) | vdm_code); width=32.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.state_updates.last_decoded_vdm
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
  - last_decoded_vdm width matches SSOT value 32
  - last_decoded_vdm RTL expression implements SSOT expression ((message_code << 24) | (vendor_id << 8) | vdm_code)
  - last_decoded_vdm updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_DECODE_VDM.state_updates.last_decoded_vdm

### RTL-0155: Implement error case for FM_DECODE_VDM: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_0.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: id=FM_DECODE_VDM; name=pcie_vdm_decode; signal=[{"condition": "not Non-Flit VDM-with-data / msg_code!=0x7F / vendor!=0x1AB4 / vdm_code!=0x0 / unsupported routing/TC...; state=["vdm_valid", "payload_offset", "requester_id", "pad_ok", "last_decoded_vdm"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_0

### RTL-0156: Implement error case for FM_DECODE_VDM: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_1.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via function_model.transactions.FM_DECODE_VDM.
SSOT item context: id=FM_DECODE_VDM; name=pcie_vdm_decode; signal=[{"condition": "pad_len>3 / pad_len!=0 on non-EOM / TU not in [64,4096] or not 4B-aligned / non-EOM payload != TU or ...; state=["vdm_valid", "payload_offset", "requester_id", "pad_ok", "last_decoded_vdm"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_DECODE_VDM.error_cases.error_case_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_DECODE_VDM.error_cases.error_case_1

### RTL-0437: Implement feature axi_ingress

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.axi_ingress
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.axi_ingress.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=axi_ingress; output=ordered TLP bytes + accept event, or PD_MALFORMED_TLP.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.axi_ingress
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.axi_ingress

### RTL-0438: Implement feature vdm_decode

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.vdm_decode
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.vdm_decode.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.vdm_decode.
SSOT item context: name=vdm_decode; output=validated VDM fields + payload offset, or PD_UNSUPPORTED_VDM / PD_BAD_PAD_OR_ALIGNMENT.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.vdm_decode
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.vdm_decode

### RTL-0440: Implement feature interleaved_assembly

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.interleaved_assembly
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.interleaved_assembly.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=interleaved_assembly; output=appended payload bytes + descriptor on EOM, or AD_* assembly drop.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.interleaved_assembly
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.interleaved_assembly

### RTL-0442: Implement feature descriptor_publish

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.descriptor_publish
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.descriptor_publish.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=descriptor_publish; output=descriptor_ready interrupt + APB descriptor readout, or AD_DESCRIPTOR_FULL.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.descriptor_publish
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.descriptor_publish

### RTL-0443: Implement feature firmware_read

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.firmware_read
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.firmware_read.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=firmware_read; output=rdata beats; SLVERR for out-of-window/no-descriptor reads.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.firmware_read
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.firmware_read

### RTL-0444: Implement feature drop_classification

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.drop_classification
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.drop_classification.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=drop_classification; output=last_drop_class/last_drop_reason + per-reason counters + interrupt.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.drop_classification
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.drop_classification

### RTL-0465: Prove module mctp_assembler_v3_pcie_vdm_parser is functionally equivalent to FL

- Priority: high
- Required: True
- Status: open
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_pcie_vdm_parser.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_pcie_vdm_parser.module_equivalence.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via module_equivalence.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_pcie_vdm_parser.sv.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_pcie_vdm_parser.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: sub_modules.mctp_assembler_v3_pcie_vdm_parser.module_equivalence
