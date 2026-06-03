# RTL Authoring Packet: module__mctp_assembler_v3_axi_wr_ingress__function_model

- Kind: module
- Owner module: mctp_assembler_v3_axi_wr_ingress
- Owner file: rtl/mctp_assembler_v3_axi_wr_ingress.sv
- Task count: 29
- Required tasks: 29

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
- LLM-actionable open tasks: 29
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, function_model, function_model.transactions.FM_INGEST_TLP, io_list, io_list.interfaces.axi_wr_slave, test_requirements
- Module slice: 2/5 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_v3_axi_wr_ingress is split into 5 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])

## Tasks

### RTL-0120: Implement transaction FM_INGEST_TLP

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_INGEST_TLP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_INGEST_TLP.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: id=FM_INGEST_TLP; name=axi_write_to_tlp_bytes.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP

### RTL-0121: Implement precondition for FM_INGEST_TLP: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=CONTROL.enable==1 or (enable==0 and drop_when_disabled==1).
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_0

### RTL-0122: Implement precondition for FM_INGEST_TLP: precondition_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=AWSIZE==5.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.preconditions.precondition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_1

### RTL-0123: Implement precondition for FM_INGEST_TLP: precondition_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_2.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=AWBURST==INCR.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.preconditions.precondition_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_2

### RTL-0124: Implement precondition for FM_INGEST_TLP: precondition_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_3.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=W beat count == AWLEN+1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.preconditions.precondition_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_3

### RTL-0125: Implement precondition for FM_INGEST_TLP: precondition_4

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_4
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_4.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=WLAST on final beat only.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.preconditions.precondition_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.preconditions.precondition_4

### RTL-0126: Implement input for FM_INGEST_TLP: input_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.input
- Source ref: function_model.transactions.FM_INGEST_TLP.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.inputs.input_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: id=FM_INGEST_TLP; name=axi_write_to_tlp_bytes; port=["s_axi_bresp"]; signal=["axi_wr_slave AW/W/B", "wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count"]; state=["tlp_accept", "tlp_seen_count", "tlp_accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["s_axi_bresp"] is the implementation/observation point for axi_write_to_tlp_bytes
- SSOT refs: function_model.transactions.FM_INGEST_TLP.inputs.input_0

### RTL-0127: Implement output for FM_INGEST_TLP: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.output_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=ordered raw TLP byte vector with valid byte count from WSTRB.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.output_0

### RTL-0128: Implement output for FM_INGEST_TLP: output_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.output_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: value=BRESP=OKAY when transaction consumed.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.output_1

### RTL-0129: Implement output for FM_INGEST_TLP: bresp_next

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.bresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.bresp_next.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: name=bresp_next; port=s_axi_bresp; expr=BRESP_OKAY.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.bresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - bresp_next RTL expression implements SSOT expression BRESP_OKAY
  - DUT port s_axi_bresp is the implementation/observation point for bresp_next
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.bresp_next

### RTL-0130: Implement output for FM_INGEST_TLP: tlp_accept

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accept
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accept.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: state=tlp_accept; expr=wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_coun....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.tlp_accept
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - function_model.transactions.FM_INGEST_TLP.outputs.tlp_accept RTL expression implements SSOT expression wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_coun...
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accept

### RTL-0131: Implement output for FM_INGEST_TLP: tlp_seen_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_seen_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_seen_count.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: state=tlp_seen_count; expr=tlp_seen_count + 1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.tlp_seen_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - function_model.transactions.FM_INGEST_TLP.outputs.tlp_seen_count RTL expression implements SSOT expression tlp_seen_count + 1
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.tlp_seen_count

### RTL-0132: Implement output for FM_INGEST_TLP: tlp_accepted_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accepted_count.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: state=tlp_accepted_count; expr=tlp_accepted_count + (1 if tlp_accept else 0).
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.outputs.tlp_accepted_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - function_model.transactions.FM_INGEST_TLP.outputs.tlp_accepted_count RTL expression implements SSOT expression tlp_accepted_count + (1 if tlp_accept else 0)
- SSOT refs: function_model.transactions.FM_INGEST_TLP.outputs.tlp_accepted_count

### RTL-0133: Implement output rule for FM_INGEST_TLP: bresp_next

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_INGEST_TLP.output_rules.bresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.output_rules.bresp_next.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: name=bresp_next; port=s_axi_bresp; expr=BRESP_OKAY; width=2.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.output_rules.bresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - bresp_next width matches SSOT value 2
  - bresp_next RTL expression implements SSOT expression BRESP_OKAY
  - DUT port s_axi_bresp is the implementation/observation point for bresp_next
  - bresp_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_INGEST_TLP.output_rules.bresp_next

### RTL-0134: Implement state update for FM_INGEST_TLP: tlp_accept

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accept
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accept.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: name=tlp_accept; expr=wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_coun...; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accept
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - tlp_accept width matches SSOT value 1
  - tlp_accept RTL expression implements SSOT expression wlast_seen and (awsize == 5) and (awburst == INCR) and wstrb_contiguous and (tlp_byte_count >= 16) and (tlp_byte_coun...
  - tlp_accept updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accept

### RTL-0135: Implement state update for FM_INGEST_TLP: tlp_seen_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_seen_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_seen_count.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: name=tlp_seen_count; expr=tlp_seen_count + 1; width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.state_updates.tlp_seen_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - tlp_seen_count width matches SSOT value 32
  - tlp_seen_count RTL expression implements SSOT expression tlp_seen_count + 1
  - tlp_seen_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_seen_count

### RTL-0136: Implement state update for FM_INGEST_TLP: tlp_accepted_count

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accepted_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accepted_count.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: name=tlp_accepted_count; expr=tlp_accepted_count + (1 if tlp_accept else 0); width=32.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accepted_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - tlp_accepted_count width matches SSOT value 32
  - tlp_accepted_count RTL expression implements SSOT expression tlp_accepted_count + (1 if tlp_accept else 0)
  - tlp_accepted_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_INGEST_TLP.state_updates.tlp_accepted_count

### RTL-0137: Implement side effect for FM_INGEST_TLP: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: id=FM_INGEST_TLP; name=axi_write_to_tlp_bytes; port=["s_axi_bresp"]; signal=["tlp_seen_count increment", "wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count"]; state=["tlp_accept", "tlp_seen_count", "tlp_accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["s_axi_bresp"] is the implementation/observation point for axi_write_to_tlp_bytes
- SSOT refs: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_0

### RTL-0138: Implement side effect for FM_INGEST_TLP: side_effect_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: id=FM_INGEST_TLP; name=axi_write_to_tlp_bytes; port=["s_axi_bresp"]; signal=["tlp_accepted_count increment on legal TLP", "wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count"]; state=["tlp_accept", "tlp_seen_count", "tlp_accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["s_axi_bresp"] is the implementation/observation point for axi_write_to_tlp_bytes
- SSOT refs: function_model.transactions.FM_INGEST_TLP.side_effects.side_effect_1

### RTL-0139: Implement error case for FM_INGEST_TLP: error_case_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_INGEST_TLP.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_INGEST_TLP.error_cases.error_case_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.transactions.FM_INGEST_TLP.
SSOT item context: id=FM_INGEST_TLP; name=axi_write_to_tlp_bytes; port=["s_axi_bresp"]; signal=[{"condition": "empty txn / bad AWSIZE/AWBURST / interleave / beat-count mismatch / early/late WLAST / non-contiguous...; state=["tlp_accept", "tlp_seen_count", "tlp_accepted_count"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_INGEST_TLP.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["s_axi_bresp"] is the implementation/observation point for axi_write_to_tlp_bytes
- SSOT refs: function_model.transactions.FM_INGEST_TLP.error_cases.error_case_0

### RTL-0283: Preserve FL invariant invariant_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_0
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_0.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=No SRAM payload write occurs before a packet is accepted for assembly.; state=["context_table", "sram_alloc_ptr", "counters", "last_drop_class", "tlp_accepted_count", "active_context_count", "ctx....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_0

### RTL-0284: Preserve FL invariant invariant_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_1
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_1.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=The SRAM writer never writes PCIe/VDM headers, MCTP transport headers, pad bytes, or digest bytes as payload.; state=["context_table", "sram_alloc_ptr", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_payload_base_addr", "ctx_paylo....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_1

### RTL-0285: Preserve FL invariant invariant_2

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_2
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_2.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=For every published descriptor, byte address base_addr..base_addr+payload_len-1 is written exactly as the correspondi...; state=["context_table", "descriptor_queue", "sram_alloc_ptr", "ctx_payload_byte_count", "ctx_payload_base_addr", "ctx_paylo....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_2

### RTL-0286: Preserve FL invariant invariant_3

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_3
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_3.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "free_slot_available", "som"...; signal=Active context count never exceeds CONTEXT_COUNT.; state=["context_table", "tlp_seen_count", "tlp_accepted_count", "active_context_count", "ctx_payload_byte_count", "ctx_expe....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "free_slot_available", "som"... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "free_slot_available", "som"...
- SSOT refs: function_model.invariants.invariant_3

### RTL-0287: Preserve FL invariant invariant_4

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_4
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_4.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=first_tlp_header for a context is written only by the accepted SOM packet; last_tlp_header equals the most recent acc...; state=["context_table", "descriptor_queue", "counters", "last_drop_class", "tlp_seen_count", "tlp_accepted_count", "active_....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_4
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_4

### RTL-0288: Preserve FL invariant invariant_5

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_5
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_5.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=Non-final accepted packets contribute exactly the configured transmission unit byte count; EOM may contribute fewer.; state=["context_table", "tlp_seen_count", "tlp_accepted_count", "active_context_count", "ctx_payload_byte_count", "ctx_payl....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_5
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_5

### RTL-0289: Preserve FL invariant invariant_6

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_6
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_6.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=No descriptor is published before EOM; sequence mismatch aborts the active context and suppresses the success descrip...; state=["context_table", "descriptor_queue", "active_context_count", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_payl....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_6
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_6

### RTL-0290: Preserve FL invariant invariant_7

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_7
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_7.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=An earlier packet-drop reason wins over a later assembly-drop reason for the same accepted transaction (drop priority...; state=["context_table", "counters", "last_drop_class", "tlp_accepted_count", "active_context_count", "ctx_expected_seq"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_7
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_7

### RTL-0291: Preserve FL invariant invariant_8

- Priority: high
- Required: True
- Status: planned
- Category: function_model.invariant
- Source ref: function_model.invariants.invariant_8
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.invariant_8.
Owner: mctp_assembler_v3_axi_wr_ingress in rtl/mctp_assembler_v3_axi_wr_ingress.sv via function_model.
SSOT item context: port=["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...; signal=ctx_state encoding is mutually exclusive: a context cannot be IDLE and ASSEMBLING or ERROR in the same cycle.; state=["context_table", "sram_alloc_ptr", "active_context_count", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_payloa....
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.invariant_8
  - Primary implementation evidence is in rtl/mctp_assembler_v3_axi_wr_ingress.sv
  - DUT port ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",... is the implementation/observation point for ["wlast_seen", "awsize", "awburst", "wstrb_contiguous", "tlp_byte_count", "s_axi_bresp", "message_code", "vendor_id",...
- SSOT refs: function_model.invariants.invariant_8
