# RTL Authoring Packet: module__mctp_assembler_scratch_v5_context_table

- Kind: module
- Owner module: mctp_assembler_scratch_v5_context_table
- Owner file: rtl/mctp_assembler_scratch_v5_context_table.sv
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
- Owner refs: fsm, fsm.context_fsm, function_model, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_COMPLETE_MESSAGE, memory, memory.instances.context_table, registers

## Tasks

### RTL-0178: Implement output for FM_ASSEMBLE_FRAGMENT: active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.active_context_count.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=active_context_count; expr=active_context_count + context_alloc.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.active_context_count RTL expression implements SSOT expression active_context_count + context_alloc
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.active_context_count

### RTL-0179: Implement output for FM_ASSEMBLE_FRAGMENT: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_state.
Owner: mctp_assembler_scratch_v5_pcie_vdm_parser in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=ctx_state; expr=STATE_ASSEMBLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_state RTL expression implements SSOT expression STATE_ASSEMBLING
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_state

### RTL-0181: Implement output for FM_ASSEMBLE_FRAGMENT: ctx_expected_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_expected_seq.
Owner: mctp_assembler_scratch_v5_pcie_vdm_parser in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=ctx_expected_seq; expr=next_seq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_expected_seq RTL expression implements SSOT expression next_seq
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_expected_seq

### RTL-0184: Implement output rule for FM_ASSEMBLE_FRAGMENT: debug_context_id

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.output_rules.debug_context_id
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.output_rules.debug_context_id.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=debug_context_id; port=debug_context_id; expr=context_id; width=4.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.output_rules.debug_context_id
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - debug_context_id width matches SSOT value 4
  - debug_context_id RTL expression implements SSOT expression context_id
  - DUT port debug_context_id is the implementation/observation point for debug_context_id
  - debug_context_id is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.output_rules.debug_context_id

### RTL-0185: Implement state update for FM_ASSEMBLE_FRAGMENT: active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.active_context_count.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=active_context_count; expr=active_context_count + context_alloc; width=5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - active_context_count width matches SSOT value 5
  - active_context_count RTL expression implements SSOT expression active_context_count + context_alloc
  - active_context_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.active_context_count

### RTL-0186: Implement state update for FM_ASSEMBLE_FRAGMENT: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_state.
Owner: mctp_assembler_scratch_v5_pcie_vdm_parser in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=ctx_state; expr=STATE_ASSEMBLING; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv
  - ctx_state width matches SSOT value 2
  - ctx_state RTL expression implements SSOT expression STATE_ASSEMBLING
  - ctx_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_state

### RTL-0188: Implement state update for FM_ASSEMBLE_FRAGMENT: ctx_expected_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_expected_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_expected_seq.
Owner: mctp_assembler_scratch_v5_pcie_vdm_parser in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=ctx_expected_seq; expr=next_seq; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_expected_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_pcie_vdm_parser.sv
  - ctx_expected_seq width matches SSOT value 2
  - ctx_expected_seq RTL expression implements SSOT expression next_seq
  - ctx_expected_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_expected_seq

### RTL-0218: Implement transaction FM_COMPLETE_MESSAGE

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: id=FM_COMPLETE_MESSAGE; name=Complete EOM message and publish descriptor.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE

### RTL-0219: Implement precondition for FM_COMPLETE_MESSAGE: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: value=eom and descriptor_ready.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.preconditions.precondition_0

### RTL-0220: Implement output for FM_COMPLETE_MESSAGE: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.output_0.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: value=interrupt.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.output_0

### RTL-0221: Implement output for FM_COMPLETE_MESSAGE: interrupt

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.interrupt
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.interrupt.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: name=interrupt; port=irq; expr=descriptor_publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.outputs.interrupt
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - interrupt RTL expression implements SSOT expression descriptor_publish
  - DUT port irq is the implementation/observation point for interrupt
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.interrupt

### RTL-0223: Implement output for FM_COMPLETE_MESSAGE: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.ctx_state.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: state=ctx_state; expr=STATE_DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.outputs.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - function_model.transactions.FM_COMPLETE_MESSAGE.outputs.ctx_state RTL expression implements SSOT expression STATE_DONE_WAIT_DESCRIPTOR_POP
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.ctx_state

### RTL-0224: Implement output for FM_COMPLETE_MESSAGE: active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.active_context_count.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: state=active_context_count; expr=active_context_count - descriptor_publish.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.outputs.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - function_model.transactions.FM_COMPLETE_MESSAGE.outputs.active_context_count RTL expression implements SSOT expression active_context_count - descriptor_publish
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.outputs.active_context_count

### RTL-0227: Implement state update for FM_COMPLETE_MESSAGE: ctx_state

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.ctx_state
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.ctx_state.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: name=ctx_state; expr=STATE_DONE_WAIT_DESCRIPTOR_POP; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.ctx_state
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - ctx_state width matches SSOT value 2
  - ctx_state RTL expression implements SSOT expression STATE_DONE_WAIT_DESCRIPTOR_POP
  - ctx_state updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.ctx_state

### RTL-0228: Implement state update for FM_COMPLETE_MESSAGE: active_context_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.active_context_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.active_context_count.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.transactions.FM_COMPLETE_MESSAGE.
SSOT item context: name=active_context_count; expr=active_context_count - descriptor_publish; width=5.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.active_context_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - active_context_count width matches SSOT value 5
  - active_context_count RTL expression implements SSOT expression active_context_count - descriptor_publish
  - active_context_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_COMPLETE_MESSAGE.state_updates.active_context_count

### RTL-0291: Preserve FL invariant context_bound

- Priority: high
- Required: True
- Status: pass
- Category: function_model.invariant
- Source ref: function_model.invariants.context_bound
- Detail: Invariants constrain legal RTL behavior and must be reflected in state, gating, error handling, assertions, or downstream checks.
SSOT ref: function_model.invariants.context_bound.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via function_model.
SSOT item context: port=["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...; signal={"expr": "CONTEXT_COUNT >= active_context_count", "name": "context_bound"}; state=["active_context_count", "descriptor_count", "payload_byte_count", "collected_tlp_count", "packet_drop_count", "assem....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL behavior cannot violate the invariant in normal operation
  - If the invariant is verification-only, the SSOT names that evidence owner
  - Coverage/equivalence references this invariant when observable
  - Traceability keeps source_ref function_model.invariants.context_bound
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - DUT port ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re... is the implementation/observation point for ["axi_aw_accept", "axi_wlast_seen", "tlp_byte_count", "m_axi_bvalid", "m_axi_bresp", "vdm_supported", "packet_drop_re...
- SSOT refs: function_model.invariants.context_bound

### RTL-0367: Implement memory item context_table

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.context_table
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.context_table.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via memory.instances.context_table.
SSOT item context: name=context_table.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.context_table
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: memory.instances.context_table

### RTL-0369: Implement memory item partial_word_buffer

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.partial_word_buffer
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.partial_word_buffer.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via memory.
SSOT item context: name=partial_word_buffer.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.partial_word_buffer
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: memory.instances.partial_word_buffer

### RTL-0375: Implement FSM state context_fsm.state_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_0
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_0.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: value=IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_0

### RTL-0376: Implement FSM state context_fsm.state_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_1
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_1.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: value=ASSEMBLING.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_1

### RTL-0377: Implement FSM state context_fsm.state_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_2
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_2.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: value=ERROR.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_2

### RTL-0378: Implement FSM state context_fsm.state_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.state
- Source ref: fsm.context_fsm.states.state_3
- Detail: Every SSOT state must be encoded or explicitly proven equivalent by a simpler implementation. Default to the conventional explicit FSM style unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.states.state_3.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: value=DONE_WAIT_DESCRIPTOR_POP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - State is encoded/reachable or explicitly replaced by equivalent logic
  - Reset/entry/exit behavior matches SSOT
  - FSM style follows SSOT/user override when present, otherwise uses the conventional state-register plus next-state/output-decode structure
  - Coverage can observe the state or equivalent condition
  - Traceability keeps source_ref fsm.context_fsm.states.state_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: fsm.context_fsm.states.state_3

### RTL-0379: Implement FSM transition context_fsm.transition_0

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_0
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_0.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=IDLE; to=ASSEMBLING; action=allocate_q_and_store_first_tlp_header.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_0 transition path IDLE -> ASSEMBLING is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_0

### RTL-0380: Implement FSM transition context_fsm.transition_1

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_1
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_1.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=ASSEMBLING; action=append_payload_and_update_last_tlp_header.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_1 transition path ASSEMBLING -> ASSEMBLING is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_1

### RTL-0381: Implement FSM transition context_fsm.transition_2

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_2
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_2.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=DONE_WAIT_DESCRIPTOR_POP; action=flush_partial_word_and_publish_descriptor.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_2
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_2 transition path ASSEMBLING -> DONE_WAIT_DESCRIPTOR_POP is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_2

### RTL-0382: Implement FSM transition context_fsm.transition_3

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_3
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_3.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=IDLE; to=ERROR; action=raise_PD_UNEXPECTED_MIDDLE_END.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_3
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_3 transition path IDLE -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_3

### RTL-0383: Implement FSM transition context_fsm.transition_4

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_4
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_4.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=ASSEMBLING; to=ERROR; action=raise_AD_drop_reason.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_4
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_4 transition path ASSEMBLING -> ERROR is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_4

### RTL-0384: Implement FSM transition context_fsm.transition_5

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_5
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_5.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=DONE_WAIT_DESCRIPTOR_POP; to=IDLE; action=release_context_without_reclaiming_sram_space.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_5
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_5 transition path DONE_WAIT_DESCRIPTOR_POP -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_5

### RTL-0385: Implement FSM transition context_fsm.transition_6

- Priority: high
- Required: True
- Status: pass
- Category: fsm.transition
- Source ref: fsm.context_fsm.transitions.transition_6
- Detail: Transition condition, action, and timing must be implemented in RTL and covered downstream. Use the conventional explicit FSM structure by default unless SSOT/user specifies another synthesizable style.
SSOT ref: fsm.context_fsm.transitions.transition_6.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via fsm.context_fsm.
SSOT item context: from=ERROR; to=IDLE; action=clear_context_visible_error_state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Transition condition is present in RTL control logic
  - Transition action/state update is implemented
  - Illegal/missing transition behavior is handled per SSOT
  - Traceability keeps source_ref fsm.context_fsm.transitions.transition_6
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
  - fsm.context_fsm.transitions.transition_6 transition path ERROR -> IDLE is encoded or explicitly proven equivalent
- SSOT refs: fsm.context_fsm.transitions.transition_6

### RTL-0424: Prove module mctp_assembler_scratch_v5_context_table is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v5_context_table.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v5_context_table.module_equivalence.
Owner: mctp_assembler_scratch_v5_context_table in rtl/mctp_assembler_scratch_v5_context_table.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v5_context_table.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v5_context_table.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v5_context_table.module_equivalence
