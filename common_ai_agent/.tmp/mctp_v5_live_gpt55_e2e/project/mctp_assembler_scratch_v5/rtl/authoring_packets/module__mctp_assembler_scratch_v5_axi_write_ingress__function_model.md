# RTL Authoring Packet: module__mctp_assembler_scratch_v5_axi_write_ingress__function_model

- Kind: module
- Owner module: mctp_assembler_scratch_v5_axi_write_ingress
- Owner file: rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- Task count: 13
- Required tasks: 13

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
- Owner refs: cycle_model, cycle_model.handshake_rules.axi_write_channels, dataflow, function_model, function_model.transactions.FM_ACCEPT_AXI_TLP, io_list, io_list.interfaces.axi_write_slave, test_requirements
- Module slice: 2/7 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_v5_axi_write_ingress is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_awvalid <= m_axi_awvalid (integration.connections[0])
  - mctp_assembler_scratch_v5_axi_write_ingress.m_axi_wvalid <= m_axi_wvalid (integration.connections[1])

## Tasks

### RTL-0134: Implement transaction FM_ACCEPT_AXI_TLP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: id=FM_ACCEPT_AXI_TLP; name=Accept one AXI4 write burst as one PCIe VDM TLP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP

### RTL-0135: Implement precondition for FM_ACCEPT_AXI_TLP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: value=axi_aw_accept and axi_wlast_seen.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.preconditions.precondition_0

### RTL-0136: Implement output for FM_ACCEPT_AXI_TLP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_0.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: value=bvalid_next.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_0

### RTL-0137: Implement output for FM_ACCEPT_AXI_TLP: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_1.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: value=bresp_next.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.output_1

### RTL-0138: Implement output for FM_ACCEPT_AXI_TLP: bvalid_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bvalid_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bvalid_next.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: name=bvalid_next; port=m_axi_bvalid; expr=axi_aw_accept and axi_wlast_seen.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bvalid_next
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - bvalid_next RTL expression implements SSOT expression axi_aw_accept and axi_wlast_seen
  - DUT port m_axi_bvalid is the implementation/observation point for bvalid_next
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bvalid_next

### RTL-0139: Implement output for FM_ACCEPT_AXI_TLP: bresp_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bresp_next.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: name=bresp_next; port=m_axi_bresp; expr=BRESP_OKAY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - bresp_next RTL expression implements SSOT expression BRESP_OKAY
  - DUT port m_axi_bresp is the implementation/observation point for bresp_next
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.bresp_next

### RTL-0140: Implement output for FM_ACCEPT_AXI_TLP: collected_tlp_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.collected_tlp_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.collected_tlp_count.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: state=collected_tlp_count; expr=collected_tlp_count + axi_wlast_seen.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.collected_tlp_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.collected_tlp_count RTL expression implements SSOT expression collected_tlp_count + axi_wlast_seen
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.outputs.collected_tlp_count

### RTL-0141: Implement output rule for FM_ACCEPT_AXI_TLP: bvalid_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bvalid_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bvalid_next.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: name=bvalid_next; port=m_axi_bvalid; expr=axi_aw_accept and axi_wlast_seen; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bvalid_next
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - bvalid_next width matches SSOT value 1
  - bvalid_next RTL expression implements SSOT expression axi_aw_accept and axi_wlast_seen
  - DUT port m_axi_bvalid is the implementation/observation point for bvalid_next
  - bvalid_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bvalid_next

### RTL-0142: Implement output rule for FM_ACCEPT_AXI_TLP: bresp_next

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bresp_next
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bresp_next.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: name=bresp_next; port=m_axi_bresp; expr=BRESP_OKAY; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bresp_next
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - bresp_next width matches SSOT value 2
  - bresp_next RTL expression implements SSOT expression BRESP_OKAY
  - DUT port m_axi_bresp is the implementation/observation point for bresp_next
  - bresp_next is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.output_rules.bresp_next

### RTL-0143: Implement state update for FM_ACCEPT_AXI_TLP: collected_tlp_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.state_updates.collected_tlp_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.state_updates.collected_tlp_count.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: name=collected_tlp_count; expr=collected_tlp_count + axi_wlast_seen; width=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.state_updates.collected_tlp_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - collected_tlp_count width matches SSOT value 16
  - collected_tlp_count RTL expression implements SSOT expression collected_tlp_count + axi_wlast_seen
  - collected_tlp_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.state_updates.collected_tlp_count

### RTL-0144: Implement side effect for FM_ACCEPT_AXI_TLP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_0.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: id=FM_ACCEPT_AXI_TLP; name=Accept one AXI4 write burst as one PCIe VDM TLP; port=["m_axi_bvalid", "m_axi_bresp"]; signal=["raw TLP bytes captured until WLAST", "axi_aw_accept", "axi_wlast_seen", "tlp_byte_count"]; state=["collected_tlp_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - DUT port ["m_axi_bvalid", "m_axi_bresp"] is the implementation/observation point for Accept one AXI4 write burst as one PCIe VDM TLP
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_0

### RTL-0145: Implement side effect for FM_ACCEPT_AXI_TLP: side_effect_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_1.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.transactions.FM_ACCEPT_AXI_TLP.
SSOT item context: id=FM_ACCEPT_AXI_TLP; name=Accept one AXI4 write burst as one PCIe VDM TLP; port=["m_axi_bvalid", "m_axi_bresp"]; signal=["write response emitted after packet classification", "axi_aw_accept", "axi_wlast_seen", "tlp_byte_count"]; state=["collected_tlp_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - DUT port ["m_axi_bvalid", "m_axi_bresp"] is the implementation/observation point for Accept one AXI4 write burst as one PCIe VDM TLP
- SSOT refs: function_model.transactions.FM_ACCEPT_AXI_TLP.side_effects.side_effect_1

### RTL-0292: Preserve FL invariant payload_bound

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.payload_bound
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.payload_bound.
Owner: mctp_assembler_scratch_v5_axi_write_ingress in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv via function_model.
SSOT item context: port=["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...; signal={"expr": "MAX_MESSAGE_BYTES >= payload_byte_count", "name": "payload_bound"}; state=["active_context_count", "descriptor_count", "payload_byte_count", "collected_tlp_count", "packet_drop_count", "assem....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.payload_bound
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_axi_write_ingress.sv
  - DUT port ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re... is the implementation/observation point for ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...
- SSOT refs: function_model.invariants.payload_bound
