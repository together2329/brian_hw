# RTL Authoring Packet: module__mctp_assembler_scratch_v4_mctp_parser

- Kind: module
- Owner module: mctp_assembler_scratch_v4_mctp_parser
- Owner file: rtl/mctp_assembler_scratch_v4_mctp_parser.sv
- Task count: 18
- Required tasks: 18

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
- Owner refs: custom, custom.mctp_transport_fields, function_model, function_model.transactions.FM_PARSE_MCTP

## Tasks

### RTL-0158: Implement transaction FM_PARSE_MCTP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_PARSE_MCTP
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: id=FM_PARSE_MCTP; name=Decode MCTP transport header and context key.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
- SSOT refs: function_model.transactions.FM_PARSE_MCTP

### RTL-0159: Implement precondition for FM_PARSE_MCTP: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_PARSE_MCTP.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.preconditions.precondition_0.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: value=vdm_supported.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.preconditions.precondition_0

### RTL-0160: Implement output for FM_PARSE_MCTP: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.output_0.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: value=debug_context_key.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.output_0

### RTL-0161: Implement output for FM_PARSE_MCTP: ctx_source_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_source_eid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_source_eid.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_source_eid; expr=source_eid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_source_eid RTL expression implements SSOT expression source_eid
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_source_eid

### RTL-0162: Implement output for FM_PARSE_MCTP: ctx_destination_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_destination_eid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_destination_eid.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_destination_eid; expr=destination_eid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_destination_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_destination_eid RTL expression implements SSOT expression destination_eid
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_destination_eid

### RTL-0163: Implement output for FM_PARSE_MCTP: ctx_tag_owner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_tag_owner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_tag_owner.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_tag_owner; expr=tag_owner.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_tag_owner RTL expression implements SSOT expression tag_owner
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_tag_owner

### RTL-0164: Implement output for FM_PARSE_MCTP: ctx_message_tag

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_tag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_tag.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_message_tag; expr=message_tag.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_tag RTL expression implements SSOT expression message_tag
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_tag

### RTL-0165: Implement output for FM_PARSE_MCTP: ctx_message_type

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_type
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_type.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_message_type; expr=message_type.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_type
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_type RTL expression implements SSOT expression message_type
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_message_type

### RTL-0166: Implement output for FM_PARSE_MCTP: ctx_last_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_last_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_last_seq.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: state=ctx_last_seq; expr=packet_seq.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.outputs.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - function_model.transactions.FM_PARSE_MCTP.outputs.ctx_last_seq RTL expression implements SSOT expression packet_seq
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.outputs.ctx_last_seq

### RTL-0167: Implement output rule for FM_PARSE_MCTP: debug_context_key

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_PARSE_MCTP.output_rules.debug_context_key
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.output_rules.debug_context_key.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=debug_context_key; port=debug_context_key; expr=context_key; width=18.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.output_rules.debug_context_key
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - debug_context_key width matches SSOT value 18
  - debug_context_key RTL expression implements SSOT expression context_key
  - DUT port debug_context_key is the implementation/observation point for debug_context_key
  - debug_context_key is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.output_rules.debug_context_key

### RTL-0168: Implement state update for FM_PARSE_MCTP: ctx_source_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_source_eid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_source_eid.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_source_eid; expr=source_eid; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_source_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_source_eid width matches SSOT value 8
  - ctx_source_eid RTL expression implements SSOT expression source_eid
  - ctx_source_eid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_source_eid

### RTL-0169: Implement state update for FM_PARSE_MCTP: ctx_destination_eid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_destination_eid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_destination_eid.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_destination_eid; expr=destination_eid; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_destination_eid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_destination_eid width matches SSOT value 8
  - ctx_destination_eid RTL expression implements SSOT expression destination_eid
  - ctx_destination_eid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_destination_eid

### RTL-0170: Implement state update for FM_PARSE_MCTP: ctx_tag_owner

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_tag_owner
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_tag_owner.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_tag_owner; expr=tag_owner; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_tag_owner
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_tag_owner width matches SSOT value 1
  - ctx_tag_owner RTL expression implements SSOT expression tag_owner
  - ctx_tag_owner updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_tag_owner

### RTL-0171: Implement state update for FM_PARSE_MCTP: ctx_message_tag

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_tag
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_tag.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_message_tag; expr=message_tag; width=3.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_tag
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_message_tag width matches SSOT value 3
  - ctx_message_tag RTL expression implements SSOT expression message_tag
  - ctx_message_tag updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_tag

### RTL-0172: Implement state update for FM_PARSE_MCTP: ctx_message_type

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_type
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_type.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_message_type; expr=message_type; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_type
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_message_type width matches SSOT value 8
  - ctx_message_type RTL expression implements SSOT expression message_type
  - ctx_message_type updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_message_type

### RTL-0173: Implement state update for FM_PARSE_MCTP: ctx_last_seq

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_last_seq
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_last_seq.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: name=ctx_last_seq; expr=packet_seq; width=2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_last_seq
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - ctx_last_seq width matches SSOT value 2
  - ctx_last_seq RTL expression implements SSOT expression packet_seq
  - ctx_last_seq updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.state_updates.ctx_last_seq

### RTL-0174: Implement side effect for FM_PARSE_MCTP: side_effect_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_PARSE_MCTP.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_PARSE_MCTP.side_effects.side_effect_0.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via function_model.transactions.FM_PARSE_MCTP.
SSOT item context: id=FM_PARSE_MCTP; name=Decode MCTP transport header and context key; port=["debug_context_key"]; signal=["context key prepared before allocation or lookup", "source_eid", "destination_eid", "tag_owner", "message_tag", "me...; state=["ctx_source_eid", "ctx_destination_eid", "ctx_tag_owner", "ctx_message_tag", "ctx_message_type", "ctx_last_seq"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_PARSE_MCTP.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
  - DUT port ["debug_context_key"] is the implementation/observation point for Decode MCTP transport header and context key
- SSOT refs: function_model.transactions.FM_PARSE_MCTP.side_effects.side_effect_0

### RTL-0423: Prove module mctp_assembler_scratch_v4_mctp_parser is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_v4_mctp_parser.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_v4_mctp_parser.module_equivalence.
Owner: mctp_assembler_scratch_v4_mctp_parser in rtl/mctp_assembler_scratch_v4_mctp_parser.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_v4_mctp_parser.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_v4_mctp_parser.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_v4_mctp_parser.module_equivalence
