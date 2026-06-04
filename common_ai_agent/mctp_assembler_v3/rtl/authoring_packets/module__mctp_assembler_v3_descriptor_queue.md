# RTL Authoring Packet: module__mctp_assembler_v3_descriptor_queue

- Kind: module
- Owner module: mctp_assembler_v3_descriptor_queue
- Owner file: rtl/mctp_assembler_v3_descriptor_queue.sv
- Task count: 26
- Required tasks: 26

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: function_model, function_model.transactions.FM_PUBLISH_DESCRIPTOR, memory, memory.instances.descriptor_fifo
- SSOT target scale: min_modules=9, min_source_files=10

## Tasks

### RTL-0254: Implement transaction FM_PUBLISH_DESCRIPTOR

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: id=FM_PUBLISH_DESCRIPTOR; name=descriptor_publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR

### RTL-0255: Implement precondition for FM_PUBLISH_DESCRIPTOR: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.preconditions.precondition_0.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: value=successful EOM for a context.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.preconditions.precondition_0

### RTL-0256: Implement input for FM_PUBLISH_DESCRIPTOR: input_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_0.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: id=FM_PUBLISH_DESCRIPTOR; name=descriptor_publish; signal=["context metadata", "descriptor_queue_full"]; state=["descriptor_ready", "descriptor_payload_len", "descriptor_base_addr", "message_completed_count", "descriptor_valid",....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_0

### RTL-0257: Implement input for FM_PUBLISH_DESCRIPTOR: input_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.input
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_1.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: id=FM_PUBLISH_DESCRIPTOR; name=descriptor_publish; signal=["first/last_tlp_header", "descriptor_queue_full"]; state=["descriptor_ready", "descriptor_payload_len", "descriptor_base_addr", "message_completed_count", "descriptor_valid",....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.inputs.input_1

### RTL-0258: Implement output for FM_PUBLISH_DESCRIPTOR: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_0.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: value=descriptor{source_eid,dest_eid,tag_owner,message_tag,message_type,requester_id,pcie_routing_type,payload_base_addr,pa....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_0

### RTL-0259: Implement output for FM_PUBLISH_DESCRIPTOR: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_1.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: value=descriptor_ready interrupt; message_completed_count increment.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.output_1

### RTL-0260: Implement output for FM_PUBLISH_DESCRIPTOR: descriptor_ready

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_ready.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=descriptor_ready; expr=not descriptor_queue_full.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_ready RTL expression implements SSOT expression not descriptor_queue_full
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_ready

### RTL-0261: Implement output for FM_PUBLISH_DESCRIPTOR: descriptor_payload_len

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_payload_len
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_payload_len.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=descriptor_payload_len; expr=ctx_payload_byte_count.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_payload_len
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_payload_len RTL expression implements SSOT expression ctx_payload_byte_count
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_payload_len

### RTL-0262: Implement output for FM_PUBLISH_DESCRIPTOR: descriptor_base_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_base_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_base_addr.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=descriptor_base_addr; expr=ctx_payload_base_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_base_addr RTL expression implements SSOT expression ctx_payload_base_addr
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_base_addr

### RTL-0263: Implement output for FM_PUBLISH_DESCRIPTOR: message_completed_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.message_completed_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.message_completed_count.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=message_completed_count; expr=message_completed_count + 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.message_completed_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.message_completed_count RTL expression implements SSOT expression message_completed_count + 1
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.message_completed_count

### RTL-0264: Implement output for FM_PUBLISH_DESCRIPTOR: descriptor_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_valid.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=descriptor_valid; expr=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_valid RTL expression implements SSOT expression 1
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.descriptor_valid

### RTL-0265: Implement output for FM_PUBLISH_DESCRIPTOR: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.ctx_state.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: state=ctx_state; expr=DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.ctx_state RTL expression implements SSOT expression DONE_WAIT_DESCRIPTOR_POP
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.outputs.ctx_state

### RTL-0266: Implement state update for FM_PUBLISH_DESCRIPTOR: descriptor_ready

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_ready.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=descriptor_ready; expr=not descriptor_queue_full; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_ready
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - descriptor_ready width matches SSOT value 1
  - descriptor_ready RTL expression implements SSOT expression not descriptor_queue_full
  - descriptor_ready updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_ready

### RTL-0267: Implement state update for FM_PUBLISH_DESCRIPTOR: descriptor_payload_len

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_payload_len
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_payload_len.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=descriptor_payload_len; expr=ctx_payload_byte_count; width=13.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_payload_len
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - descriptor_payload_len width matches SSOT value 13
  - descriptor_payload_len RTL expression implements SSOT expression ctx_payload_byte_count
  - descriptor_payload_len updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_payload_len

### RTL-0268: Implement state update for FM_PUBLISH_DESCRIPTOR: descriptor_base_addr

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_base_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_base_addr.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=descriptor_base_addr; expr=ctx_payload_base_addr; width=16.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - descriptor_base_addr width matches SSOT value 16
  - descriptor_base_addr RTL expression implements SSOT expression ctx_payload_base_addr
  - descriptor_base_addr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_base_addr

### RTL-0269: Implement state update for FM_PUBLISH_DESCRIPTOR: message_completed_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.message_completed_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.message_completed_count.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=message_completed_count; expr=message_completed_count + 1; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.message_completed_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - message_completed_count width matches SSOT value 32
  - message_completed_count RTL expression implements SSOT expression message_completed_count + 1
  - message_completed_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.message_completed_count

### RTL-0270: Implement state update for FM_PUBLISH_DESCRIPTOR: descriptor_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_valid.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=descriptor_valid; expr=1; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_valid
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - descriptor_valid width matches SSOT value 1
  - descriptor_valid RTL expression implements SSOT expression 1
  - descriptor_valid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.descriptor_valid

### RTL-0271: Implement state update for FM_PUBLISH_DESCRIPTOR: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.ctx_state.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: name=ctx_state; expr=DONE_WAIT_DESCRIPTOR_POP; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - ctx_state width matches SSOT value 2
  - ctx_state RTL expression implements SSOT expression DONE_WAIT_DESCRIPTOR_POP
  - ctx_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.state_updates.ctx_state

### RTL-0272: Implement side effect for FM_PUBLISH_DESCRIPTOR: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.side_effects.side_effect_0.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: id=FM_PUBLISH_DESCRIPTOR; name=descriptor_publish; signal=["context released (or DONE_WAIT_DESCRIPTOR_POP)", "descriptor_queue_full"]; state=["descriptor_ready", "descriptor_payload_len", "descriptor_base_addr", "message_completed_count", "descriptor_valid",....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.side_effects.side_effect_0

### RTL-0273: Implement error case for FM_PUBLISH_DESCRIPTOR: error_case_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PUBLISH_DESCRIPTOR.error_cases.error_case_0.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via function_model.transactions.FM_PUBLISH_DESCRIPTOR.
SSOT item context: id=FM_PUBLISH_DESCRIPTOR; name=descriptor_publish; signal=[{"condition": "descriptor/header queue full at EOM", "result": "AD_DESCRIPTOR_FULL assembly drop; no descriptor publ...; state=["descriptor_ready", "descriptor_payload_len", "descriptor_base_addr", "message_completed_count", "descriptor_valid",....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PUBLISH_DESCRIPTOR.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: function_model.transactions.FM_PUBLISH_DESCRIPTOR.error_cases.error_case_0

### RTL-0384: Implement field DESC_VALID.tag_owner

- Priority: high
- Required: True
- Status: pass
- Category: registers.field
- Source ref: registers.register_list.DESC_VALID.fields.tag_owner
- Detail: Each register field needs access semantics, reset behavior, masks/strobes, clear behavior, and side effects as applicable.
SSOT ref: registers.register_list.DESC_VALID.fields.tag_owner.
Owner: mctp_assembler_v3_apb_regfile in rtl/mctp_assembler_v3_apb_regfile.sv via registers.register_list.
SSOT item context: name=tag_owner; reset=0; access=ro.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Field bit range, mask, and write strobe decode match SSOT
  - Field reset/access policy matches SSOT
  - Read/write/W1C/W0C/RO behavior is implemented or precisely blocked
  - Reserved fields read as the SSOT value and ignore writes
  - Field side effects are connected to owning control/status logic
  - Traceability keeps source_ref registers.register_list.DESC_VALID.fields.tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_v3_apb_regfile.sv
  - tag_owner reset behavior matches SSOT value 0
  - tag_owner access policy ro is implemented without read/write shortcuts
  - tag_owner readback returns implemented RTL state when readable
  - tag_owner write/clear side effects are connected to owning control/status logic
- SSOT refs: registers.register_list.DESC_VALID.fields.tag_owner

### RTL-0395: Implement memory item descriptor_fifo

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.descriptor_fifo
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.descriptor_fifo.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via memory.instances.descriptor_fifo.
SSOT item context: name=descriptor_fifo; width=512; depth=8; latency=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.descriptor_fifo
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
  - descriptor_fifo width matches SSOT value 512
  - descriptor_fifo timing uses SSOT cycle/latency 0
  - descriptor_fifo storage depth matches SSOT value 8
- SSOT refs: memory.instances.descriptor_fifo

### RTL-0449: Implement feature descriptor_publish

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.descriptor_publish
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.descriptor_publish.
Owner: mctp_assembler_v3_pcie_vdm_parser in rtl/mctp_assembler_v3_pcie_vdm_parser.sv via features.
SSOT item context: name=descriptor_publish; output=descriptor_ready interrupt + APB descriptor readout, or AD_DESCRIPTOR_FULL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.descriptor_publish
  - Primary implementation evidence is in rtl/mctp_assembler_v3_pcie_vdm_parser.sv
- SSOT refs: features.descriptor_publish

### RTL-0477: Prove module mctp_assembler_v3_descriptor_queue is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_v3_descriptor_queue.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_v3_descriptor_queue.module_equivalence.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_v3_descriptor_queue.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: sub_modules.mctp_assembler_v3_descriptor_queue.module_equivalence

### RTL-0034: Implement parameter DONE_WAIT_DESCRIPTOR_POP

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DONE_WAIT_DESCRIPTOR_POP
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DONE_WAIT_DESCRIPTOR_POP.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via semantic_terms:descriptor.
SSOT item context: name=DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DONE_WAIT_DESCRIPTOR_POP
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: parameters.DONE_WAIT_DESCRIPTOR_POP

### RTL-0049: Implement parameter DESCRIPTOR_FIFO_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.DESCRIPTOR_FIFO_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.DESCRIPTOR_FIFO_DEPTH.
Owner: mctp_assembler_v3_descriptor_queue in rtl/mctp_assembler_v3_descriptor_queue.sv via semantic_terms:descriptor.
SSOT item context: name=DESCRIPTOR_FIFO_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.DESCRIPTOR_FIFO_DEPTH
  - Primary implementation evidence is in rtl/mctp_assembler_v3_descriptor_queue.sv
- SSOT refs: parameters.DESCRIPTOR_FIFO_DEPTH
