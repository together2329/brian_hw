# RTL Authoring Packet: module__pl330_target_merge_buffer

- Kind: module
- Owner module: pl330_target_merge_buffer
- Owner file: rtl/pl330_target_merge_buffer.sv
- Task count: 4
- Required tasks: 4

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model.handshake_rules.merge, function_model.transactions.merge
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_merge_buffer.accept_pulse_o <= merge_buffer_accept_pulse_o (observed_named_port_map)
  - pl330_target_merge_buffer.clk <= clk (observed_named_port_map)
  - pl330_target_merge_buffer.empty_o <= merge_buffer_empty_o (observed_named_port_map)
  - pl330_target_merge_buffer.flush_i <= merge_buffer_flush_i (observed_named_port_map)
  - pl330_target_merge_buffer.full_o <= merge_buffer_full_o (observed_named_port_map)
  - pl330_target_merge_buffer.in_addr_i <= merge_buffer_in_addr_i (observed_named_port_map)
  - pl330_target_merge_buffer.in_data_i <= merge_buffer_in_data_i (observed_named_port_map)
  - pl330_target_merge_buffer.in_id_i <= merge_buffer_in_id_i (observed_named_port_map)

## Tasks

### RTL-0032: Implement or account for SSOT module slice `pl330_target_merge_buffer`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[5]
- Detail: name=pl330_target_merge_buffer
SSOT ref: workflow_todos.rtl-gen[5].
Owner: pl330_target_merge_buffer in rtl/pl330_target_merge_buffer.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_MERGE_BUFFER.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[5]
  - Primary implementation evidence is in rtl/pl330_target_merge_buffer.sv
  - Semantic source_refs covered: sub_modules[4]
- SSOT refs: sub_modules[4], workflow_todos.rtl-gen[5]

### RTL-0211: Implement memory item merge_buffer

- Priority: high
- Required: True
- Status: pass
- Category: memory.instances
- Source ref: memory.instances.merge_buffer
- Detail: This SSOT memory.instances item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: memory.instances.merge_buffer.
Owner: pl330_target_merge_buffer in rtl/pl330_target_merge_buffer.sv via semantic_terms:buffer,merge.
SSOT item context: name=merge_buffer; width=AXI_DATA_WIDTH; depth=MERGE_BUFFER_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref memory.instances.merge_buffer
  - Primary implementation evidence is in rtl/pl330_target_merge_buffer.sv
  - merge_buffer width matches SSOT value AXI_DATA_WIDTH
  - merge_buffer storage depth matches SSOT value MERGE_BUFFER_DEPTH
- SSOT refs: memory.instances.merge_buffer

### RTL-0265: Prove module pl330_target_merge_buffer is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_merge_buffer.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_merge_buffer.module_equivalence.
Owner: pl330_target_merge_buffer in rtl/pl330_target_merge_buffer.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_merge_buffer.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_merge_buffer.sv
- SSOT refs: sub_modules.pl330_target_merge_buffer.module_equivalence

### RTL-0100: Implement parameter MERGE_BUFFER_DEPTH

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.MERGE_BUFFER_DEPTH
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.MERGE_BUFFER_DEPTH.
Owner: pl330_target_merge_buffer in rtl/pl330_target_merge_buffer.sv via semantic_terms:buffer,merge.
SSOT item context: name=MERGE_BUFFER_DEPTH.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.MERGE_BUFFER_DEPTH
  - Primary implementation evidence is in rtl/pl330_target_merge_buffer.sv
- SSOT refs: parameters.MERGE_BUFFER_DEPTH
