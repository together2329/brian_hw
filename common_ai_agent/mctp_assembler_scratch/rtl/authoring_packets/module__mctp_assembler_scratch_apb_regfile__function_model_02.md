# RTL Authoring Packet: module__mctp_assembler_scratch_apb_regfile__function_model_02

- Kind: module
- Owner module: mctp_assembler_scratch_apb_regfile
- Owner file: rtl/mctp_assembler_scratch_apb_regfile.sv
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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 13
- Human-locked open tasks: 0
- Owner refs: debug_observability, decomposition, error_handling, features, fsm, function_model.state_variables, function_model.transactions.FM_APB_ACCESS, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_ASSEMBLY_DROP, function_model.transactions.FM_AXI_READBACK, function_model.transactions.FM_COMPLETE_MESSAGE, function_model.transactions.FM_PACKET_DROP, interrupts, interrupts.sources, io_list, io_list.interfaces.apb_slave
- Module slice: 3/9 section=function_model task_limit=48
- Slice rule: Owner module mctp_assembler_scratch_apb_regfile is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_scratch_apb_regfile.pready <= pready (integration.connections[4])

## Tasks

### RTL-0261: Implement transaction FM_APB_ACCESS

- Priority: high
- Required: True
- Status: planned
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_APB_ACCESS
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_APB_ACCESS.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: id=FM_APB_ACCESS; name=APB register access.
- Current reason: RTL audit has not run yet.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_APB_ACCESS

### RTL-0262: Implement precondition for FM_APB_ACCESS: precondition_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_APB_ACCESS.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.preconditions.precondition_0.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: value=apb_access.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_APB_ACCESS.preconditions.precondition_0

### RTL-0263: Implement output for FM_APB_ACCESS: output_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.output_0.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: value=apb_ready.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.output_0

### RTL-0264: Implement output for FM_APB_ACCESS: output_1

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.output_1.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: value=apb_error.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.output_1

### RTL-0265: Implement output for FM_APB_ACCESS: apb_ready

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.apb_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.apb_ready.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=apb_ready; port=pready; expr=apb_access.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.apb_ready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - apb_ready RTL expression implements SSOT expression apb_access
  - DUT port pready is the implementation/observation point for apb_ready
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.apb_ready

### RTL-0266: Implement output for FM_APB_ACCESS: apb_error

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.apb_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.apb_error.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=apb_error; port=pslverr; expr=illegal_apb_access.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.apb_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - apb_error RTL expression implements SSOT expression illegal_apb_access
  - DUT port pslverr is the implementation/observation point for apb_error
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.apb_error

### RTL-0267: Implement output for FM_APB_ACCESS: enable_reg

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.enable_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.enable_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: state=enable_reg; expr=apb_wdata & apb_write.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.enable_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_APB_ACCESS.outputs.enable_reg RTL expression implements SSOT expression apb_wdata & apb_write
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.enable_reg

### RTL-0268: Implement output for FM_APB_ACCESS: drop_mode_reg

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output
- Source ref: function_model.transactions.FM_APB_ACCESS.outputs.drop_mode_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.outputs.drop_mode_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: state=drop_mode_reg; expr=(apb_wdata >> 1) & apb_write.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.outputs.drop_mode_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - function_model.transactions.FM_APB_ACCESS.outputs.drop_mode_reg RTL expression implements SSOT expression (apb_wdata >> 1) & apb_write
- SSOT refs: function_model.transactions.FM_APB_ACCESS.outputs.drop_mode_reg

### RTL-0269: Implement output rule for FM_APB_ACCESS: apb_ready

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_ACCESS.output_rules.apb_ready
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.output_rules.apb_ready.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=apb_ready; port=pready; expr=apb_access; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.output_rules.apb_ready
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - apb_ready width matches SSOT value 1
  - apb_ready RTL expression implements SSOT expression apb_access
  - DUT port pready is the implementation/observation point for apb_ready
  - apb_ready is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_ACCESS.output_rules.apb_ready

### RTL-0270: Implement output rule for FM_APB_ACCESS: apb_error

- Priority: high
- Required: True
- Status: planned
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_APB_ACCESS.output_rules.apb_error
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.output_rules.apb_error.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=apb_error; port=pslverr; expr=illegal_apb_access; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.output_rules.apb_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - apb_error width matches SSOT value 1
  - apb_error RTL expression implements SSOT expression illegal_apb_access
  - DUT port pslverr is the implementation/observation point for apb_error
  - apb_error is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_APB_ACCESS.output_rules.apb_error

### RTL-0271: Implement state update for FM_APB_ACCESS: enable_reg

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_ACCESS.state_updates.enable_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.state_updates.enable_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=enable_reg; expr=apb_wdata & apb_write; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.state_updates.enable_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - enable_reg width matches SSOT value 1
  - enable_reg RTL expression implements SSOT expression apb_wdata & apb_write
  - enable_reg updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_ACCESS.state_updates.enable_reg

### RTL-0272: Implement state update for FM_APB_ACCESS: drop_mode_reg

- Priority: high
- Required: True
- Status: planned
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_APB_ACCESS.state_updates.drop_mode_reg
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.state_updates.drop_mode_reg.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: name=drop_mode_reg; expr=(apb_wdata >> 1) & apb_write; width=1.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.state_updates.drop_mode_reg
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - drop_mode_reg width matches SSOT value 1
  - drop_mode_reg RTL expression implements SSOT expression (apb_wdata >> 1) & apb_write
  - drop_mode_reg updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_APB_ACCESS.state_updates.drop_mode_reg

### RTL-0273: Implement side effect for FM_APB_ACCESS: side_effect_0

- Priority: high
- Required: True
- Status: planned
- Category: function_model.side_effect
- Source ref: function_model.transactions.FM_APB_ACCESS.side_effects.side_effect_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_APB_ACCESS.side_effects.side_effect_0.
Owner: mctp_assembler_scratch_apb_regfile in rtl/mctp_assembler_scratch_apb_regfile.sv via function_model.transactions.FM_APB_ACCESS.
SSOT item context: id=FM_APB_ACCESS; name=APB register access; port=["pready", "pslverr"]; signal=["control_status_interrupt_counter_descriptor_debug_register_visible", "apb_access", "apb_write", "apb_wdata", "illeg...; state=["enable_reg", "drop_mode_reg"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_APB_ACCESS.side_effects.side_effect_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_apb_regfile.sv
  - DUT port ["pready", "pslverr"] is the implementation/observation point for APB register access
- SSOT refs: function_model.transactions.FM_APB_ACCESS.side_effects.side_effect_0
