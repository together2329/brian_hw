# RTL Authoring Packet: module__mctp_assembler_scratch_pcie_vdm_parser

- Kind: module
- Owner module: mctp_assembler_scratch_pcie_vdm_parser
- Owner file: rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
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
- Owner refs: custom, custom.pcie_vdm_fields, error_handling, error_handling.packet_drop_ids, function_model, function_model.transactions.FM_ASSEMBLE_FRAGMENT, function_model.transactions.FM_FILTER_VDM

## Tasks

### RTL-0021: Implement parser, context table, SRAM packer, descriptor queue, read egress, APB regfile, SRAM arbiter, CDC, and parameter header.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: Required modules from sub_modules and filelist must exist exactly once and satisfy function_model/state/register ownership.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - all_required_modules_in_filelist
  - no_missing_declared_module
  - per_q_state_visible
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - Semantic source_refs covered: function_model.transactions, memory.instances, registers.per_q_bank, sub_modules
- SSOT refs: function_model.transactions, memory.instances, registers.per_q_bank, sub_modules, workflow_todos.rtl-gen[1]

### RTL-0022: Implement no-hole 256-bit SRAM payload packing.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[2]
- Detail: Each Q keeps partial_word_addr, partial_word_strobe, partial_word_valid, and partial_next_lane so fragments pack contiguously.
SSOT ref: workflow_todos.rtl-gen[2].
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via custom.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - SC_UNALIGNED_SRAM_PACK_NO_HOLES_passes
  - sram_write_monitor_observes_no_holes
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[2]
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - Semantic source_refs covered: custom.sram_packing, dataflow.sram_pack, function_model.transactions.FM_SRAM_PACK_WRITE
- SSOT refs: custom.sram_packing, dataflow.sram_pack, function_model.transactions.FM_SRAM_PACK_WRITE, workflow_todos.rtl-gen[2]

### RTL-0023: Implement packet and assembly drop handling.

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Every PD_* and AD_* reason must increment the correct counter, expose last reason, and suppress illegal SRAM writes or descriptors.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via error_handling.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - all_drop_scenarios_pass
  - no_sram_write_on_drop
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - Semantic source_refs covered: error_handling.error_sources, test_requirements.scenarios
- SSOT refs: error_handling.error_sources, test_requirements.scenarios, workflow_todos.rtl-gen[3]

### RTL-0146: Implement transaction FM_FILTER_VDM

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_FILTER_VDM
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_FILTER_VDM.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: id=FM_FILTER_VDM; name=Validate PCIe VDM envelope for MCTP transport.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_FILTER_VDM

### RTL-0147: Implement precondition for FM_FILTER_VDM: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_FILTER_VDM.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.preconditions.precondition_0.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: value=tlp_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_FILTER_VDM.preconditions.precondition_0

### RTL-0148: Implement output for FM_FILTER_VDM: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FILTER_VDM.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.outputs.output_0.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: value=debug_vdm_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_FILTER_VDM.outputs.output_0

### RTL-0149: Implement output for FM_FILTER_VDM: output_1

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FILTER_VDM.outputs.output_1
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.outputs.output_1.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: value=debug_drop_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.outputs.output_1
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_FILTER_VDM.outputs.output_1

### RTL-0150: Implement output for FM_FILTER_VDM: packet_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FILTER_VDM.outputs.packet_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.outputs.packet_drop_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: state=packet_drop_count; expr=packet_drop_count + packet_drop_pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.outputs.packet_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - function_model.transactions.FM_FILTER_VDM.outputs.packet_drop_count RTL expression implements SSOT expression packet_drop_count + packet_drop_pulse
- SSOT refs: function_model.transactions.FM_FILTER_VDM.outputs.packet_drop_count

### RTL-0151: Implement output for FM_FILTER_VDM: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_FILTER_VDM.outputs.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.outputs.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: state=ctx_last_drop_reason; expr=packet_drop_reason.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.outputs.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - function_model.transactions.FM_FILTER_VDM.outputs.ctx_last_drop_reason RTL expression implements SSOT expression packet_drop_reason
- SSOT refs: function_model.transactions.FM_FILTER_VDM.outputs.ctx_last_drop_reason

### RTL-0152: Implement output rule for FM_FILTER_VDM: debug_vdm_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FILTER_VDM.output_rules.debug_vdm_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.output_rules.debug_vdm_valid.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: name=debug_vdm_valid; port=debug_vdm_valid; expr=vdm_supported; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.output_rules.debug_vdm_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - debug_vdm_valid width matches SSOT value 1
  - debug_vdm_valid RTL expression implements SSOT expression vdm_supported
  - DUT port debug_vdm_valid is the implementation/observation point for debug_vdm_valid
  - debug_vdm_valid is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FILTER_VDM.output_rules.debug_vdm_valid

### RTL-0153: Implement output rule for FM_FILTER_VDM: debug_drop_pulse

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output_rule
- Source ref: function_model.transactions.FM_FILTER_VDM.output_rules.debug_drop_pulse
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.output_rules.debug_drop_pulse.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: name=debug_drop_pulse; port=debug_drop_pulse; expr=packet_drop_reason != DROP_NONE; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.output_rules.debug_drop_pulse
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - debug_drop_pulse width matches SSOT value 1
  - debug_drop_pulse RTL expression implements SSOT expression packet_drop_reason != DROP_NONE
  - DUT port debug_drop_pulse is the implementation/observation point for debug_drop_pulse
  - debug_drop_pulse is not implemented only in FunctionalModel or scoreboard code
- SSOT refs: function_model.transactions.FM_FILTER_VDM.output_rules.debug_drop_pulse

### RTL-0154: Implement state update for FM_FILTER_VDM: packet_drop_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FILTER_VDM.state_updates.packet_drop_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.state_updates.packet_drop_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: name=packet_drop_count; expr=packet_drop_count + packet_drop_pulse; width=32.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.state_updates.packet_drop_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - packet_drop_count width matches SSOT value 32
  - packet_drop_count RTL expression implements SSOT expression packet_drop_count + packet_drop_pulse
  - packet_drop_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FILTER_VDM.state_updates.packet_drop_count

### RTL-0155: Implement state update for FM_FILTER_VDM: ctx_last_drop_reason

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_FILTER_VDM.state_updates.ctx_last_drop_reason
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.state_updates.ctx_last_drop_reason.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: name=ctx_last_drop_reason; expr=packet_drop_reason; width=8.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.state_updates.ctx_last_drop_reason
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - ctx_last_drop_reason width matches SSOT value 8
  - ctx_last_drop_reason RTL expression implements SSOT expression packet_drop_reason
  - ctx_last_drop_reason updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_FILTER_VDM.state_updates.ctx_last_drop_reason

### RTL-0156: Implement error case for FM_FILTER_VDM: PD_MALFORMED_TLP

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FILTER_VDM.error_cases.PD_MALFORMED_TLP
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.error_cases.PD_MALFORMED_TLP.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: id=FM_FILTER_VDM; name=Validate PCIe VDM envelope for MCTP transport; port=["debug_vdm_valid", "debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_increment_packet_drop_count", "condition": "packet_drop_reason == 2", "id": "PD_MALFOR...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.error_cases.PD_MALFORMED_TLP
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - DUT port ["debug_vdm_valid", "debug_drop_pulse"] is the implementation/observation point for Validate PCIe VDM envelope for MCTP transport
- SSOT refs: function_model.transactions.FM_FILTER_VDM.error_cases.PD_MALFORMED_TLP

### RTL-0157: Implement error case for FM_FILTER_VDM: PD_UNSUPPORTED_VDM

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_FILTER_VDM.error_cases.PD_UNSUPPORTED_VDM
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_FILTER_VDM.error_cases.PD_UNSUPPORTED_VDM.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_FILTER_VDM.
SSOT item context: id=FM_FILTER_VDM; name=Validate PCIe VDM envelope for MCTP transport; port=["debug_vdm_valid", "debug_drop_pulse"]; signal=[{"action": "no_sram_write_and_increment_packet_drop_count", "condition": "packet_drop_reason == 3", "id": "PD_UNSUPP...; state=["packet_drop_count", "ctx_last_drop_reason"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_FILTER_VDM.error_cases.PD_UNSUPPORTED_VDM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - DUT port ["debug_vdm_valid", "debug_drop_pulse"] is the implementation/observation point for Validate PCIe VDM envelope for MCTP transport
- SSOT refs: function_model.transactions.FM_FILTER_VDM.error_cases.PD_UNSUPPORTED_VDM

### RTL-0175: Implement transaction FM_ASSEMBLE_FRAGMENT

- Priority: high
- Required: True
- Status: pass
- Category: function_model.transaction
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT
- Detail: Transaction acceptance, outputs, side effects, error cases, and observable state updates must be implemented in RTL.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: id=FM_ASSEMBLE_FRAGMENT; name=Allocate or update a Q context for one MCTP fragment.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Acceptance/precondition logic is explicit in RTL
  - All outputs and side effects occur exactly once per accepted transaction
  - The transaction is covered by equivalence goals and scoreboard observations downstream
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT

### RTL-0176: Implement precondition for FM_ASSEMBLE_FRAGMENT: precondition_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.precondition
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.preconditions.precondition_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.preconditions.precondition_0.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: value=enable_reg and context_accept.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.preconditions.precondition_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.preconditions.precondition_0

### RTL-0177: Implement output for FM_ASSEMBLE_FRAGMENT: output_0

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.output_0
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.output_0.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: value=debug_context_id.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.output_0
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.output_0

### RTL-0180: Implement output for FM_ASSEMBLE_FRAGMENT: ctx_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_valid.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=ctx_valid; expr=context_accept.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_valid RTL expression implements SSOT expression context_accept
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_valid

### RTL-0182: Implement output for FM_ASSEMBLE_FRAGMENT: payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.payload_byte_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=payload_byte_count; expr=payload_byte_count + payload_len.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.payload_byte_count RTL expression implements SSOT expression payload_byte_count + payload_len
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.payload_byte_count

### RTL-0183: Implement output for FM_ASSEMBLE_FRAGMENT: ctx_payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.output
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_payload_byte_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: state=ctx_payload_byte_count; expr=ctx_payload_byte_count + payload_len.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_payload_byte_count RTL expression implements SSOT expression ctx_payload_byte_count + payload_len
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.outputs.ctx_payload_byte_count

### RTL-0187: Implement state update for FM_ASSEMBLE_FRAGMENT: ctx_valid

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_valid
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_valid.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=ctx_valid; expr=context_accept; width=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_valid
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - ctx_valid width matches SSOT value 1
  - ctx_valid RTL expression implements SSOT expression context_accept
  - ctx_valid updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_valid

### RTL-0189: Implement state update for FM_ASSEMBLE_FRAGMENT: payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.payload_byte_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=payload_byte_count; expr=payload_byte_count + payload_len; width=13.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - payload_byte_count width matches SSOT value 13
  - payload_byte_count RTL expression implements SSOT expression payload_byte_count + payload_len
  - payload_byte_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.payload_byte_count

### RTL-0190: Implement state update for FM_ASSEMBLE_FRAGMENT: ctx_payload_byte_count

- Priority: high
- Required: True
- Status: pass
- Category: function_model.state_update
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_payload_byte_count
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_payload_byte_count.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: name=ctx_payload_byte_count; expr=ctx_payload_byte_count + payload_len; width=13.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_payload_byte_count
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - ctx_payload_byte_count width matches SSOT value 13
  - ctx_payload_byte_count RTL expression implements SSOT expression ctx_payload_byte_count + payload_len
  - ctx_payload_byte_count updates exactly once at the SSOT-defined transaction acceptance point
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.state_updates.ctx_payload_byte_count

### RTL-0191: Implement error case for FM_ASSEMBLE_FRAGMENT: AD_DUPLICATE_SOM

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_DUPLICATE_SOM
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_DUPLICATE_SOM.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: id=FM_ASSEMBLE_FRAGMENT; name=Allocate or update a Q context for one MCTP fragment; port=["debug_context_id"]; signal=[{"action": "no_sram_write_and_increment_assembly_drop_count", "condition": "assembly_drop_reason == 20", "id": "AD_D...; state=["active_context_count", "ctx_state", "ctx_valid", "ctx_expected_seq", "payload_byte_count", "ctx_payload_byte_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_DUPLICATE_SOM
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - DUT port ["debug_context_id"] is the implementation/observation point for Allocate or update a Q context for one MCTP fragment
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_DUPLICATE_SOM

### RTL-0192: Implement error case for FM_ASSEMBLE_FRAGMENT: AD_SEQUENCE_MISMATCH

- Priority: high
- Required: True
- Status: pass
- Category: function_model.error_case
- Source ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_SEQUENCE_MISMATCH
- Detail: This is a required leaf item from the FunctionalModel contract and must not be satisfied only in TB or comments.
SSOT ref: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_SEQUENCE_MISMATCH.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via function_model.transactions.FM_ASSEMBLE_FRAGMENT.
SSOT item context: id=FM_ASSEMBLE_FRAGMENT; name=Allocate or update a Q context for one MCTP fragment; port=["debug_context_id"]; signal=[{"action": "no_sram_write_and_enter_error_state", "condition": "assembly_drop_reason == 21", "id": "AD_SEQUENCE_MISM...; state=["active_context_count", "ctx_state", "ctx_valid", "ctx_expected_seq", "payload_byte_count", "ctx_payload_byte_count"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner logic is identifiable for this SSOT leaf
  - Reset/enable/error behavior is consistent with the parent transaction
  - Downstream equivalence/coverage can observe this behavior
  - Traceability keeps source_ref function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_SEQUENCE_MISMATCH
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
  - DUT port ["debug_context_id"] is the implementation/observation point for Allocate or update a Q context for one MCTP fragment
- SSOT refs: function_model.transactions.FM_ASSEMBLE_FRAGMENT.error_cases.AD_SEQUENCE_MISMATCH

### RTL-0396: Implement error/fault item packet_drop

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.packet_drop
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.packet_drop.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via error_handling.
SSOT item context: name=packet_drop; value=next_packet_can_be_accepted_when_resources_available.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.packet_drop
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: error_handling.recovery.packet_drop

### RTL-0397: Implement error/fault item assembly_drop

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.assembly_drop
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.assembly_drop.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via error_handling.
SSOT item context: name=assembly_drop; value=software_clear_or_timeout_cleanup_returns_q_to_IDLE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.assembly_drop
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: error_handling.recovery.assembly_drop

### RTL-0398: Implement error/fault item read_error

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.read_error
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.read_error.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via error_handling.
SSOT item context: name=read_error; value=next_read_can_retry_after_response_completion.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.read_error
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: error_handling.recovery.read_error

### RTL-0422: Prove module mctp_assembler_scratch_pcie_vdm_parser is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.mctp_assembler_scratch_pcie_vdm_parser.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.mctp_assembler_scratch_pcie_vdm_parser.module_equivalence.
Owner: mctp_assembler_scratch_pcie_vdm_parser in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.mctp_assembler_scratch_pcie_vdm_parser.module_equivalence
  - Primary implementation evidence is in rtl/mctp_assembler_scratch_pcie_vdm_parser.sv
- SSOT refs: sub_modules.mctp_assembler_scratch_pcie_vdm_parser.module_equivalence
