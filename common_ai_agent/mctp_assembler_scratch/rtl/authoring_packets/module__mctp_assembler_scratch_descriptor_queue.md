# RTL Authoring Packet: module__mctp_assembler_scratch_descriptor_queue

- Kind: module
- Owner module: mctp_assembler_scratch_descriptor_queue
- Owner file: rtl/mctp_assembler_scratch_descriptor_queue.sv
- Task count: 20
- Required tasks: 20

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
- Owner refs: function_model, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, memory, memory.instances.descriptor_fifo, registers, registers.descriptor_window

## Tasks

### RTL-0222: Implement output for FM_COMPLETE_MESSAGE: descriptor_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.descriptor_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.descriptor_count.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: state=descriptor_count; expr=descriptor_count + descriptor_publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.outputs.descriptor_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - function_model.transactions.FM_COMPLETE_MESSAGE.outputs.descriptor_count RTL expression implements SSOT expression descriptor_count + descriptor_publish
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.descriptor_count

### RTL-0226: Implement state update for FM_COMPLETE_MESSAGE: descriptor_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.descriptor_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.descriptor_count.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: name=descriptor_count; expr=descriptor_count + descriptor_publish; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.descriptor_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - descriptor_count width matches SSOT value 4
  - descriptor_count RTL expression implements SSOT expression descriptor_count + descriptor_publish
  - descriptor_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.descriptor_count

### RTL-0229: Implement error case for FM_COMPLETE_MESSAGE: AD_DESCRIPTOR_FULL

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.error_cases.AD_DESCRIPTOR_FULL
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.error_cases.AD_DESCRIPTOR_FULL.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: id=FM_COMPLETE_MESSAGE; name=Complete EOM message and publish descriptor; port=["irq"]; signal=[{"action": "no_descriptor_publish_and_increment_assembly_drop_count", "condition": "assembly_drop_reason == 24", "id...; state=["descriptor_count", "ctx_state", "active_context_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.error_cases.AD_DESCRIPTOR_FULL
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["irq"] is the implementation/observation point for Complete EOM message and publish descriptor
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.error_cases.AD_DESCRIPTOR_FULL

### RTL-0230: Implement transaction FM_PACKET_DROP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PACKET_DROP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PACKET_DROP.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PACKET_DROP

### RTL-0231: Implement precondition for FM_PACKET_DROP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: value=packet_drop_reason != DROP_NONE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PACKET_DROP.preconditions.precondition_0

### RTL-0232: Implement output for FM_PACKET_DROP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACKET_DROP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.outputs.output_0.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: value=debug_drop_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PACKET_DROP.outputs.output_0

### RTL-0233: Implement output for FM_PACKET_DROP: packet_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACKET_DROP.outputs.packet_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.outputs.packet_drop_count.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: state=packet_drop_count; expr=packet_drop_count + (packet_drop_reason != DROP_NONE).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.outputs.packet_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - function_model.transactions.FM_PACKET_DROP.outputs.packet_drop_count RTL expression implements SSOT expression packet_drop_count + (packet_drop_reason != DROP_NONE)
- SSOT refs: function_model.transactions.FM_PACKET_DROP.outputs.packet_drop_count

### RTL-0234: Implement output for FM_PACKET_DROP: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PACKET_DROP.outputs.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.outputs.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: state=ctx_last_drop_reason; expr=packet_drop_reason.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.outputs.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - function_model.transactions.FM_PACKET_DROP.outputs.ctx_last_drop_reason RTL expression implements SSOT expression packet_drop_reason
- SSOT refs: function_model.transactions.FM_PACKET_DROP.outputs.ctx_last_drop_reason

### RTL-0235: Implement output rule for FM_PACKET_DROP: debug_drop_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: name=debug_drop_pulse; port=debug_drop_pulse; expr=packet_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - debug_drop_pulse width matches SSOT value 1
  - debug_drop_pulse RTL expression implements SSOT expression packet_drop_reason != DROP_NONE
  - DUT port debug_drop_pulse is the implementation/observation point for debug_drop_pulse
  - debug_drop_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PACKET_DROP.output_rules.debug_drop_pulse

### RTL-0236: Implement state update for FM_PACKET_DROP: packet_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PACKET_DROP.state_updates.packet_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.state_updates.packet_drop_count.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: name=packet_drop_count; expr=packet_drop_count + (packet_drop_reason != DROP_NONE); width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.state_updates.packet_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - packet_drop_count width matches SSOT value 32
  - packet_drop_count RTL expression implements SSOT expression packet_drop_count + (packet_drop_reason != DROP_NONE)
  - packet_drop_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PACKET_DROP.state_updates.packet_drop_count

### RTL-0237: Implement state update for FM_PACKET_DROP: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PACKET_DROP.state_updates.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.state_updates.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: name=ctx_last_drop_reason; expr=packet_drop_reason; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.state_updates.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - ctx_last_drop_reason width matches SSOT value 8
  - ctx_last_drop_reason RTL expression implements SSOT expression packet_drop_reason
  - ctx_last_drop_reason updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PACKET_DROP.state_updates.ctx_last_drop_reason

### RTL-0238: Implement error case for FM_PACKET_DROP: PD_DISABLED_DROP_MODE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DISABLED_DROP_MODE
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DISABLED_DROP_MODE.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write; port=["debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_count_packet_drop", "condition": "packet_drop_reason == 1", "id": "PD_DISABLED_DROP_MO...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.error_cases.PD_DISABLED_DROP_MODE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["debug_drop_pulse"] is the implementation/observation point for Packet drop without SRAM payload write
- SSOT refs: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DISABLED_DROP_MODE

### RTL-0239: Implement error case for FM_PACKET_DROP: PD_BAD_PAD_OR_ALIGNMENT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_PAD_OR_ALIGNMENT
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_PAD_OR_ALIGNMENT.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write; port=["debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_count_packet_drop", "condition": "packet_drop_reason == 5", "id": "PD_BAD_PAD_OR_ALIGN...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_PAD_OR_ALIGNMENT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["debug_drop_pulse"] is the implementation/observation point for Packet drop without SRAM payload write
- SSOT refs: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_PAD_OR_ALIGNMENT

### RTL-0240: Implement error case for FM_PACKET_DROP: PD_DEST_EID_REJECT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DEST_EID_REJECT
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DEST_EID_REJECT.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write; port=["debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_count_packet_drop", "condition": "packet_drop_reason == 6", "id": "PD_DEST_EID_REJECT"...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.error_cases.PD_DEST_EID_REJECT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["debug_drop_pulse"] is the implementation/observation point for Packet drop without SRAM payload write
- SSOT refs: function_model.transactions.FM_PACKET_DROP.error_cases.PD_DEST_EID_REJECT

### RTL-0241: Implement error case for FM_PACKET_DROP: PD_UNEXPECTED_MIDDLE_END

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_UNEXPECTED_MIDDLE_END
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_UNEXPECTED_MIDDLE_END.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write; port=["debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_count_packet_drop", "condition": "packet_drop_reason == 7", "id": "PD_UNEXPECTED_MIDDL...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.error_cases.PD_UNEXPECTED_MIDDLE_END
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["debug_drop_pulse"] is the implementation/observation point for Packet drop without SRAM payload write
- SSOT refs: function_model.transactions.FM_PACKET_DROP.error_cases.PD_UNEXPECTED_MIDDLE_END

### RTL-0242: Implement error case for FM_PACKET_DROP: PD_BAD_OR_EXPIRED_TAG

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_OR_EXPIRED_TAG
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_OR_EXPIRED_TAG.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.transactions.FM_PACKET_DROP.
SSOT item context: id=FM_PACKET_DROP; name=Packet drop without SRAM payload write; port=["debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_count_packet_drop", "condition": "packet_drop_reason == 8", "id": "PD_BAD_OR_EXPIRED_T...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_OR_EXPIRED_TAG
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["debug_drop_pulse"] is the implementation/observation point for Packet drop without SRAM payload write
- SSOT refs: function_model.transactions.FM_PACKET_DROP.error_cases.PD_BAD_OR_EXPIRED_TAG

### RTL-0293: Preserve FL invariant descriptor_bound

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.descriptor_bound
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.descriptor_bound.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via function_model.
SSOT item context: port=["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...; signal={"expr": "DESCRIPTOR_FIFO_DEPTH >= descriptor_count", "name": "descriptor_bound"}; state=["raw_debug_read_enable", "active_context_count", "descriptor_count", "payload_byte_count", "collected_tlp_count", "p....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.descriptor_bound
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - DUT port ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re... is the implementation/observation point for ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...
- SSOT refs: function_model.invariants.descriptor_bound

### RTL-0368: Implement memory item descriptor_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.descriptor_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.descriptor_fifo.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via memory.instances.descriptor_fifo.
SSOT item context: name=descriptor_fifo; depth=DESCRIPTOR_FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.descriptor_fifo
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
  - descriptor_fifo storage depth matches SSOT value DESCRIPTOR_FIFO_DEPTH
- SSOT refs: memory.instances.descriptor_fifo

### RTL-0400: Implement security item asset_1

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.asset_1
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.asset_1.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via semantic_terms:descriptor.
SSOT item context: value=firmware_visible_descriptor_metadata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.asset_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
- SSOT refs: security.assets.asset_1

### RTL-0428: Prove module mctp_assembler_scratch_descriptor_queue is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_descriptor_queue.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_descriptor_queue.module_equivalence.
Owner: mctp_assembler_scratch_descriptor_queue in rtl/mctp_assembler_scratch_descriptor_queue.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_descriptor_queue.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_descriptor_queue.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_descriptor_queue.module_equivalence
