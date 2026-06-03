# RTL Authoring Packet: module__mctp_assembler_scratch_v5_axi_read_egress

- Kind: module
- Owner module: mctp_assembler_scratch_v5_axi_read_egress
- Owner file: rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- Task count: 30
- Required tasks: 30

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
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_read_channels, function_model, function_model.transactions.FM_AXI_READBACK, io_list, io_list.interfaces.axi_read_slave, memory
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_axi_read_egress.m_axi_rvalid <= m_axi_rvalid (integration.connections[3])

## Tasks

### RTL-0274: Implement transaction FM_AXI_READBACK

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_AXI_READBACK
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_AXI_READBACK.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: id=FM_AXI_READBACK; name=AXI readback from descriptor-backed SRAM payload.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK

### RTL-0275: Implement precondition for FM_AXI_READBACK: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_AXI_READBACK.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: value=axi_ar_accept.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK.preconditions.precondition_0

### RTL-0276: Implement output for FM_AXI_READBACK: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.output_0.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: value=readback_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.output_0

### RTL-0277: Implement output for FM_AXI_READBACK: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.output_1.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: value=readback_data_out.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.output_1

### RTL-0278: Implement output for FM_AXI_READBACK: output_2

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.output_2.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: value=readback_resp.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.output_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.output_2

### RTL-0279: Implement output for FM_AXI_READBACK: output_3

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.output_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.output_3.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: value=readback_last.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.output_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.output_3

### RTL-0280: Implement output for FM_AXI_READBACK: readback_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_valid.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_valid; port=m_axi_rvalid; expr=axi_ar_accept.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.readback_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_valid RTL expression implements SSOT expression axi_ar_accept
  - DUT port m_axi_rvalid is the implementation/observation point for readback_valid
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.readback_valid

### RTL-0281: Implement output for FM_AXI_READBACK: readback_data_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_data_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_data_out.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_data_out; port=m_axi_rdata; expr=readback_data if read_has_descriptor else ZERO_256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.readback_data_out
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_data_out RTL expression implements SSOT expression readback_data if read_has_descriptor else ZERO_256
  - DUT port m_axi_rdata is the implementation/observation point for readback_data_out
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.readback_data_out

### RTL-0282: Implement output for FM_AXI_READBACK: readback_resp

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_resp
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_resp.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_resp; port=m_axi_rresp; expr=RESP_OKAY if read_has_descriptor else RESP_SLVERR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.readback_resp
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_resp RTL expression implements SSOT expression RESP_OKAY if read_has_descriptor else RESP_SLVERR
  - DUT port m_axi_rresp is the implementation/observation point for readback_resp
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.readback_resp

### RTL-0283: Implement output for FM_AXI_READBACK: readback_last

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_last
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.readback_last.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_last; port=m_axi_rlast; expr=read_last.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.readback_last
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_last RTL expression implements SSOT expression read_last
  - DUT port m_axi_rlast is the implementation/observation point for readback_last
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.readback_last

### RTL-0284: Implement output for FM_AXI_READBACK: read_error_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_AXI_READBACK.outputs.read_error_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.outputs.read_error_count.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: state=read_error_count; expr=read_error_count + (not read_has_descriptor).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.outputs.read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - function_model.transactions.FM_AXI_READBACK.outputs.read_error_count RTL expression implements SSOT expression read_error_count + (not read_has_descriptor)
- SSOT refs: function_model.transactions.FM_AXI_READBACK.outputs.read_error_count

### RTL-0285: Implement output rule for FM_AXI_READBACK: readback_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_valid.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_valid; port=m_axi_rvalid; expr=axi_ar_accept; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.output_rules.readback_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_valid width matches SSOT value 1
  - readback_valid RTL expression implements SSOT expression axi_ar_accept
  - DUT port m_axi_rvalid is the implementation/observation point for readback_valid
  - readback_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READBACK.output_rules.readback_valid

### RTL-0286: Implement output rule for FM_AXI_READBACK: readback_data_out

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_data_out
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_data_out.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_data_out; port=m_axi_rdata; expr=readback_data if read_has_descriptor else ZERO_256; width=256.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.output_rules.readback_data_out
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_data_out width matches SSOT value 256
  - readback_data_out RTL expression implements SSOT expression readback_data if read_has_descriptor else ZERO_256
  - DUT port m_axi_rdata is the implementation/observation point for readback_data_out
  - readback_data_out is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READBACK.output_rules.readback_data_out

### RTL-0287: Implement output rule for FM_AXI_READBACK: readback_resp

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_resp
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_resp.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_resp; port=m_axi_rresp; expr=RESP_OKAY if read_has_descriptor else RESP_SLVERR; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.output_rules.readback_resp
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_resp width matches SSOT value 2
  - readback_resp RTL expression implements SSOT expression RESP_OKAY if read_has_descriptor else RESP_SLVERR
  - DUT port m_axi_rresp is the implementation/observation point for readback_resp
  - readback_resp is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READBACK.output_rules.readback_resp

### RTL-0288: Implement output rule for FM_AXI_READBACK: readback_last

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_last
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.output_rules.readback_last.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=readback_last; port=m_axi_rlast; expr=read_last; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.output_rules.readback_last
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - readback_last width matches SSOT value 1
  - readback_last RTL expression implements SSOT expression read_last
  - DUT port m_axi_rlast is the implementation/observation point for readback_last
  - readback_last is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_AXI_READBACK.output_rules.readback_last

### RTL-0289: Implement state update for FM_AXI_READBACK: read_error_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_AXI_READBACK.state_updates.read_error_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.state_updates.read_error_count.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: name=read_error_count; expr=read_error_count + (not read_has_descriptor); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.state_updates.read_error_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - read_error_count width matches SSOT value 32
  - read_error_count RTL expression implements SSOT expression read_error_count + (not read_has_descriptor)
  - read_error_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_AXI_READBACK.state_updates.read_error_count

### RTL-0290: Implement side effect for FM_AXI_READBACK: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_AXI_READBACK.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_AXI_READBACK.side_effects.side_effect_0.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via function_model.transactions.FM_AXI_READBACK.
SSOT item context: id=FM_AXI_READBACK; name=AXI readback from descriptor-backed SRAM payload; port=["m_axi_rvalid", "m_axi_rdata", "m_axi_rresp", "m_axi_rlast"]; signal=["no_descriptor_read_returns_zero_data_and_slverr_unless_raw_debug_enabled", "axi_ar_accept", "read_has_descriptor", ...; state=["read_error_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_AXI_READBACK.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - DUT port ["m_axi_rvalid", "m_axi_rdata", "m_axi_rresp", "m_axi_rlast"] is the implementation/observation point for AXI readback from descriptor-backed SRAM payload
- SSOT refs: function_model.transactions.FM_AXI_READBACK.side_effects.side_effect_0

### RTL-0298: Implement handshake rule: axi_read_channels

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.handshake_rules
- Source ref: cycle_model.handshake_rules.axi_read_channels
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.handshake_rules.axi_read_channels.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via cycle_model.handshake_rules.axi_read_channels.
SSOT item context: name=axi_read_channels; signal=m_axi_arvalid/m_axi_arready/m_axi_rvalid/m_axi_rready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.handshake_rules.axi_read_channels
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - axi_read_channels appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.handshake_rules.axi_read_channels

### RTL-0426: Prove module mctp_assembler_scratch_v5_axi_read_egress is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v5_axi_read_egress.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v5_axi_read_egress.module_equivalence.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v5_axi_read_egress.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v5_axi_read_egress.module_equivalence

### RTL-0067: Implement and connect port m_axi_araddr

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_araddr
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_araddr.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_araddr; width=AXI_ADDR_WIDTH; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_araddr
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_araddr width matches SSOT value AXI_ADDR_WIDTH
  - m_axi_araddr port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_araddr

### RTL-0068: Implement and connect port m_axi_arlen

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_arlen
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_arlen.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_arlen; width=8; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_arlen
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_arlen width matches SSOT value 8
  - m_axi_arlen port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_arlen

### RTL-0069: Implement and connect port m_axi_arsize

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_arsize
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_arsize.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_arsize; width=3; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_arsize
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_arsize width matches SSOT value 3
  - m_axi_arsize port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_arsize

### RTL-0070: Implement and connect port m_axi_arburst

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_arburst
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_arburst.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_arburst; width=2; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_arburst
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_arburst width matches SSOT value 2
  - m_axi_arburst port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_arburst

### RTL-0071: Implement and connect port m_axi_arvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_arvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_arvalid.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_arvalid; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_arvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_arvalid width matches SSOT value 1
  - m_axi_arvalid port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_arvalid

### RTL-0072: Implement and connect port m_axi_arready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_arready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_arready.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_arready; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_arready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_arready width matches SSOT value 1
  - m_axi_arready port direction remains output
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_arready

### RTL-0073: Implement and connect port m_axi_rdata

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_rdata
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_rdata.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_rdata; width=AXI_DATA_WIDTH; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_rdata
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_rdata width matches SSOT value AXI_DATA_WIDTH
  - m_axi_rdata port direction remains output
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_rdata

### RTL-0074: Implement and connect port m_axi_rresp

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_rresp
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_rresp.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_rresp; width=2; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_rresp
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_rresp width matches SSOT value 2
  - m_axi_rresp port direction remains output
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_rresp

### RTL-0075: Implement and connect port m_axi_rlast

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_rlast
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_rlast.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_rlast; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_rlast
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_rlast width matches SSOT value 1
  - m_axi_rlast port direction remains output
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_rlast

### RTL-0076: Implement and connect port m_axi_rvalid

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_rvalid
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_rvalid.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_rvalid; width=1; direction=output.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_rvalid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_rvalid width matches SSOT value 1
  - m_axi_rvalid port direction remains output
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_rvalid

### RTL-0077: Implement and connect port m_axi_rready

- Priority: normal
- Required: True
- Status: pass
- Category: io_list.port
- Source ref: io_list.interfaces.axi_read_slave.ports.m_axi_rready
- Detail: The port must be declared with the SSOT direction/width and participate in the described protocol or reset/clock behavior.
SSOT ref: io_list.interfaces.axi_read_slave.ports.m_axi_rready.
Owner: mctp_assembler_scratch_v5_axi_read_egress in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv via io_list.interfaces.axi_read_slave.
SSOT item context: name=m_axi_rready; width=1; direction=input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL declaration matches SSOT direction and width
  - Active input controls are consumed by behavior or explicitly justified
  - Active outputs are driven by implemented logic, not placeholder constants
  - Traceability keeps source_ref io_list.interfaces.axi_read_slave.ports.m_axi_rready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_read_egress.sv
  - m_axi_rready width matches SSOT value 1
  - m_axi_rready port direction remains input
- SSOT refs: io_list.interfaces.axi_read_slave.ports.m_axi_rready
