# RTL Authoring Packet: module__mctp_assembler_v3_context_table__function_model

- Kind: module
- Owner module: mctp_assembler_v3_context_table
- Owner file: rtl/mctp_assembler_v3_context_table.sv
- Task count: 46
- Required tasks: 46

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
- LLM-actionable open tasks: 46
- Human-locked open tasks: 0
- Owner refs: fsm, fsm.context_fsm, function_model, function_model.transactions.FM_ALLOC_CONTEXT, function_model.transactions.FM_APPEND
- Module slice: 2/4 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_v3_context_table is split into 4 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])

## Tasks

### RTL-0182: Implement transaction FM_ALLOC_CONTEXT

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT

### RTL-0183: Implement precondition for FM_ALLOC_CONTEXT: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.preconditions.precondition_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: value=decoded MCTP packet with SOM=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.preconditions.precondition_0

### RTL-0184: Implement input for FM_ALLOC_CONTEXT: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate; signal=["assembly_key", "free_slot_available", "som", "eom", "packet_seq", "allocated_len"]; state=["alloc_ok", "single_packet", "ctx_state", "ctx_payload_base_addr", "ctx_expected_seq", "active_context_count", "sram....
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_0

### RTL-0185: Implement input for FM_ALLOC_CONTEXT: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate; signal=["first_tlp_header[0:15]", "free_slot_available", "som", "eom", "packet_seq", "allocated_len"]; state=["alloc_ok", "single_packet", "ctx_state", "ctx_payload_base_addr", "ctx_expected_seq", "active_context_count", "sram....
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.inputs.input_1

### RTL-0186: Implement output for FM_ALLOC_CONTEXT: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: value=new ASSEMBLING context (SOM,EOM=0) or single-packet path (SOM,EOM=1).
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_0

### RTL-0187: Implement output for FM_ALLOC_CONTEXT: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: value=first_tlp_header stored.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_1

### RTL-0188: Implement output for FM_ALLOC_CONTEXT: output_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: value=payload_base_addr allocated from sram_alloc_ptr.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.output_2

### RTL-0189: Implement output for FM_ALLOC_CONTEXT: alloc_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.alloc_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.alloc_ok.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=alloc_ok; expr=free_slot_available.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.alloc_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.alloc_ok RTL expression implements SSOT expression free_slot_available
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.alloc_ok

### RTL-0190: Implement output for FM_ALLOC_CONTEXT: single_packet

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.single_packet
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.single_packet.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=single_packet; expr=som and eom.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.single_packet
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.single_packet RTL expression implements SSOT expression som and eom
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.single_packet

### RTL-0191: Implement output for FM_ALLOC_CONTEXT: ctx_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_state.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=ctx_state; expr=DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_state RTL expression implements SSOT expression DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_state

### RTL-0192: Implement output for FM_ALLOC_CONTEXT: ctx_payload_base_addr

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_payload_base_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_payload_base_addr.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=ctx_payload_base_addr; expr=sram_alloc_ptr.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_payload_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_payload_base_addr RTL expression implements SSOT expression sram_alloc_ptr
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_payload_base_addr

### RTL-0193: Implement output for FM_ALLOC_CONTEXT: ctx_expected_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_expected_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=ctx_expected_seq; expr=(packet_seq + 1) % 4.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_expected_seq RTL expression implements SSOT expression (packet_seq + 1) % 4
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.ctx_expected_seq

### RTL-0194: Implement output for FM_ALLOC_CONTEXT: active_context_count

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.active_context_count.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=active_context_count; expr=active_context_count + 1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.active_context_count RTL expression implements SSOT expression active_context_count + 1
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.active_context_count

### RTL-0195: Implement output for FM_ALLOC_CONTEXT: sram_alloc_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.sram_alloc_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.outputs.sram_alloc_ptr.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: state=sram_alloc_ptr; expr=sram_alloc_ptr + allocated_len.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.outputs.sram_alloc_ptr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_ALLOC_CONTEXT.outputs.sram_alloc_ptr RTL expression implements SSOT expression sram_alloc_ptr + allocated_len
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.outputs.sram_alloc_ptr

### RTL-0196: Implement state update for FM_ALLOC_CONTEXT: alloc_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.alloc_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.alloc_ok.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=alloc_ok; expr=free_slot_available; width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.alloc_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - alloc_ok width matches SSOT value 1
  - alloc_ok RTL expression implements SSOT expression free_slot_available
  - alloc_ok updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.alloc_ok

### RTL-0197: Implement state update for FM_ALLOC_CONTEXT: single_packet

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.single_packet
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.single_packet.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=single_packet; expr=som and eom; width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.single_packet
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - single_packet width matches SSOT value 1
  - single_packet RTL expression implements SSOT expression som and eom
  - single_packet updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.single_packet

### RTL-0198: Implement state update for FM_ALLOC_CONTEXT: ctx_state

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_state.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=ctx_state; expr=DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING; width=2.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_state width matches SSOT value 2
  - ctx_state RTL expression implements SSOT expression DONE_WAIT_DESCRIPTOR_POP if (som and eom) else ASSEMBLING
  - ctx_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_state

### RTL-0199: Implement state update for FM_ALLOC_CONTEXT: ctx_payload_base_addr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_payload_base_addr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_payload_base_addr.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=ctx_payload_base_addr; expr=sram_alloc_ptr; width=16.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_payload_base_addr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_payload_base_addr width matches SSOT value 16
  - ctx_payload_base_addr RTL expression implements SSOT expression sram_alloc_ptr
  - ctx_payload_base_addr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_payload_base_addr

### RTL-0200: Implement state update for FM_ALLOC_CONTEXT: ctx_expected_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_expected_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=ctx_expected_seq; expr=(packet_seq + 1) % 4; width=2.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_expected_seq width matches SSOT value 2
  - ctx_expected_seq RTL expression implements SSOT expression (packet_seq + 1) % 4
  - ctx_expected_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.ctx_expected_seq

### RTL-0201: Implement state update for FM_ALLOC_CONTEXT: active_context_count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.active_context_count.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=active_context_count; expr=active_context_count + 1; width=5.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - active_context_count width matches SSOT value 5
  - active_context_count RTL expression implements SSOT expression active_context_count + 1
  - active_context_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.active_context_count

### RTL-0202: Implement state update for FM_ALLOC_CONTEXT: sram_alloc_ptr

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.sram_alloc_ptr
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.sram_alloc_ptr.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: name=sram_alloc_ptr; expr=sram_alloc_ptr + allocated_len; width=16.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.state_updates.sram_alloc_ptr
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - sram_alloc_ptr width matches SSOT value 16
  - sram_alloc_ptr RTL expression implements SSOT expression sram_alloc_ptr + allocated_len
  - sram_alloc_ptr updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.state_updates.sram_alloc_ptr

### RTL-0203: Implement side effect for FM_ALLOC_CONTEXT: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.side_effects.side_effect_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate; signal=["expected_seq initialized; ctx_state=ASSEMBLING; sram_alloc_ptr advanced", "free_slot_available", "som", "eom", "pac...; state=["alloc_ok", "single_packet", "ctx_state", "ctx_payload_base_addr", "ctx_expected_seq", "active_context_count", "sram....
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.side_effects.side_effect_0

### RTL-0204: Implement error case for FM_ALLOC_CONTEXT: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate; signal=[{"condition": "no free context for a new fragmented SOM", "result": "PD_BAD_OR_EXPIRED_TAG packet drop (context-tabl...; state=["alloc_ok", "single_packet", "ctx_state", "ctx_payload_base_addr", "ctx_expected_seq", "active_context_count", "sram....
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_0

### RTL-0205: Implement error case for FM_ALLOC_CONTEXT: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_ALLOC_CONTEXT.
SSOT item context: id=FM_ALLOC_CONTEXT; name=context_allocate; signal=[{"condition": "SOM for an already-active key", "result": "AD_DUPLICATE_SOM assembly drop: abort old context, suppres...; state=["alloc_ok", "single_packet", "ctx_state", "ctx_payload_base_addr", "ctx_expected_seq", "active_context_count", "sram....
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_ALLOC_CONTEXT.error_cases.error_case_1

### RTL-0206: Implement transaction FM_APPEND

- Priority: high
- Required: True
- Status: open
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APPEND
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APPEND.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APPEND
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND

### RTL-0207: Implement precondition for FM_APPEND: precondition_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APPEND.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.preconditions.precondition_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: value=SOM=0 packet matches an active key.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.preconditions.precondition_0

### RTL-0208: Implement precondition for FM_APPEND: precondition_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APPEND.preconditions.precondition_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.preconditions.precondition_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: value=packet_seq == ctx_expected_seq.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.preconditions.precondition_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.preconditions.precondition_1

### RTL-0209: Implement input for FM_APPEND: input_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_APPEND.inputs.input_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.inputs.input_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=["payload bytes", "packet_seq", "eom", "payload_bytes"]; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.inputs.input_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.inputs.input_0

### RTL-0210: Implement input for FM_APPEND: input_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.input
- Source ref: function_model.transactions.FM_APPEND.inputs.input_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.inputs.input_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=["last_tlp_header[0:15]", "packet_seq", "eom", "payload_bytes"]; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.inputs.input_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.inputs.input_1

### RTL-0211: Implement output for FM_APPEND: output_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.output_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: value=payload appended; last_tlp_header updated; expected_seq incremented modulo 4.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.outputs.output_0

### RTL-0212: Implement output for FM_APPEND: output_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.output_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: value=EOM=1 marks message complete -> FM_PUBLISH_DESCRIPTOR.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.outputs.output_1

### RTL-0213: Implement output for FM_APPEND: seq_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.seq_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.seq_ok.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: state=seq_ok; expr=packet_seq == ctx_expected_seq.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.seq_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_APPEND.outputs.seq_ok RTL expression implements SSOT expression packet_seq == ctx_expected_seq
- SSOT refs: function_model.transactions.FM_APPEND.outputs.seq_ok

### RTL-0214: Implement output for FM_APPEND: message_complete

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.message_complete
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.message_complete.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: state=message_complete; expr=eom.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.message_complete
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_APPEND.outputs.message_complete RTL expression implements SSOT expression eom
- SSOT refs: function_model.transactions.FM_APPEND.outputs.message_complete

### RTL-0215: Implement output for FM_APPEND: ctx_payload_byte_count

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.ctx_payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.ctx_payload_byte_count.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: state=ctx_payload_byte_count; expr=ctx_payload_byte_count + payload_bytes.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_APPEND.outputs.ctx_payload_byte_count RTL expression implements SSOT expression ctx_payload_byte_count + payload_bytes
- SSOT refs: function_model.transactions.FM_APPEND.outputs.ctx_payload_byte_count

### RTL-0216: Implement output for FM_APPEND: ctx_expected_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.ctx_expected_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: state=ctx_expected_seq; expr=(ctx_expected_seq + 1) % 4.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_APPEND.outputs.ctx_expected_seq RTL expression implements SSOT expression (ctx_expected_seq + 1) % 4
- SSOT refs: function_model.transactions.FM_APPEND.outputs.ctx_expected_seq

### RTL-0217: Implement output for FM_APPEND: ctx_last_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.output
- Source ref: function_model.transactions.FM_APPEND.outputs.ctx_last_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.outputs.ctx_last_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: state=ctx_last_seq; expr=packet_seq.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.outputs.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - function_model.transactions.FM_APPEND.outputs.ctx_last_seq RTL expression implements SSOT expression packet_seq
- SSOT refs: function_model.transactions.FM_APPEND.outputs.ctx_last_seq

### RTL-0218: Implement state update for FM_APPEND: seq_ok

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APPEND.state_updates.seq_ok
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.state_updates.seq_ok.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: name=seq_ok; expr=packet_seq == ctx_expected_seq; width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.state_updates.seq_ok
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - seq_ok width matches SSOT value 1
  - seq_ok RTL expression implements SSOT expression packet_seq == ctx_expected_seq
  - seq_ok updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APPEND.state_updates.seq_ok

### RTL-0219: Implement state update for FM_APPEND: message_complete

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APPEND.state_updates.message_complete
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.state_updates.message_complete.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: name=message_complete; expr=eom; width=1.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.state_updates.message_complete
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - message_complete width matches SSOT value 1
  - message_complete RTL expression implements SSOT expression eom
  - message_complete updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APPEND.state_updates.message_complete

### RTL-0220: Implement state update for FM_APPEND: ctx_payload_byte_count

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APPEND.state_updates.ctx_payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.state_updates.ctx_payload_byte_count.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: name=ctx_payload_byte_count; expr=ctx_payload_byte_count + payload_bytes; width=13.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.state_updates.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_payload_byte_count width matches SSOT value 13
  - ctx_payload_byte_count RTL expression implements SSOT expression ctx_payload_byte_count + payload_bytes
  - ctx_payload_byte_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APPEND.state_updates.ctx_payload_byte_count

### RTL-0221: Implement state update for FM_APPEND: ctx_expected_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APPEND.state_updates.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.state_updates.ctx_expected_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: name=ctx_expected_seq; expr=(ctx_expected_seq + 1) % 4; width=2.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.state_updates.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_expected_seq width matches SSOT value 2
  - ctx_expected_seq RTL expression implements SSOT expression (ctx_expected_seq + 1) % 4
  - ctx_expected_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APPEND.state_updates.ctx_expected_seq

### RTL-0222: Implement state update for FM_APPEND: ctx_last_seq

- Priority: high
- Required: True
- Status: open
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APPEND.state_updates.ctx_last_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.state_updates.ctx_last_seq.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: name=ctx_last_seq; expr=packet_seq; width=2.
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.state_updates.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
  - ctx_last_seq width matches SSOT value 2
  - ctx_last_seq RTL expression implements SSOT expression packet_seq
  - ctx_last_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APPEND.state_updates.ctx_last_seq

### RTL-0223: Implement side effect for FM_APPEND: side_effect_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APPEND.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.side_effects.side_effect_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=["ctx_payload_byte_count += payload_bytes", "packet_seq", "eom", "payload_bytes"]; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.side_effects.side_effect_0

### RTL-0224: Implement error case for FM_APPEND: error_case_0

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APPEND.error_cases.error_case_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.error_cases.error_case_0.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=[{"condition": "middle/end with no active matching context / EOM without prior SOM", "result": "PD_UNEXPECTED_MIDDLE_...; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.error_cases.error_case_0
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.error_cases.error_case_0

### RTL-0225: Implement error case for FM_APPEND: error_case_1

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APPEND.error_cases.error_case_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.error_cases.error_case_1.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=[{"condition": "packet_seq != expected modulo-4 seq", "result": "AD_SEQUENCE_MISMATCH assembly drop"}, "packet_seq", ...; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.error_cases.error_case_1
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.error_cases.error_case_1

### RTL-0226: Implement error case for FM_APPEND: error_case_2

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APPEND.error_cases.error_case_2
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.error_cases.error_case_2.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=[{"condition": "append would exceed MAX_MESSAGE_BYTES", "result": "AD_MESSAGE_OVERFLOW assembly drop"}, "packet_seq",...; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.error_cases.error_case_2
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.error_cases.error_case_2

### RTL-0227: Implement error case for FM_APPEND: error_case_3

- Priority: high
- Required: True
- Status: open
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_APPEND.error_cases.error_case_3
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APPEND.error_cases.error_case_3.
Owner: mctp_assembler_v3_context_table in rtl/mctp_assembler_v3_context_table.sv via function_model.transactions.FM_APPEND.
SSOT item context: id=FM_APPEND; name=context_append; signal=[{"condition": "context age exceeds assembly_timeout_cycles", "result": "AD_TIMEOUT assembly drop"}, "packet_seq", "e...; state=["seq_ok", "message_complete", "ctx_payload_byte_count", "ctx_expected_seq", "ctx_last_seq"].
- Current reason: Owner RTL file is missing: rtl/mctp_assembler_v3_context_table.sv.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APPEND.error_cases.error_case_3
  - Primary implementation evidence is in rtl/mctp_assembler_v3_context_table.sv
- SSOT refs: function_model.transactions.FM_APPEND.error_cases.error_case_3
