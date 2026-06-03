# RTL Authoring Packet: module__mctp_assembler_v3__workflow_todo

- Kind: module
- Owner module: mctp_assembler_v3
- Owner file: rtl/mctp_assembler_v3.sv
- Task count: 2
- Required tasks: 2

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, decomposition, function_model, function_model.transactions, integration, integration.connections, io_list, io_list.interfaces, top_module
- Module slice: 9/9 section=workflow_todo task_limit=48
- Slice rule: Owner module mctp_assembler_v3 is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - mctp_assembler_v3_axi_wr_ingress.axi_aclk <= axi_aclk (integration.connections[0])
  - mctp_assembler_v3_axi_wr_ingress.axi_aresetn <= axi_aresetn (integration.connections[1])
  - mctp_assembler_v3_apb_regfile.pclk <= pclk (integration.connections[2])
  - mctp_assembler_v3_apb_regfile.presetn <= presetn (integration.connections[3])
  - mctp_assembler_v3_apb_regfile.irq_o <= irq (integration.connections[4])
  - mctp_assembler_v3_sram_packer.sram_wr_valid_o <= sram_wr_valid (integration.connections[5])
  - mctp_assembler_v3_context_table.drop_class_o <= last_drop_class (integration.connections[6])
- SSOT top IO contracts: 51

## Tasks

### RTL-0027: Implement ingress->VDM->MCTP->context->pack->descriptor pipeline

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[0]
- Detail: Translate function_model transactions + cycle_model ordering + fsm into RTL across the manifest sub_modules.
SSOT ref: workflow_todos.rtl-gen[0].
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via workflow_todos.owner.
SSOT item context: id=RTL_ASSEMBLER_PIPELINE.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owner logic present; FunctionalModel expected vs RTL observed comparable; fresh compile/lint evidence.
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[0]
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - Semantic source_refs covered: cycle_model.pipeline, fsm, function_model.transactions
- SSOT refs: cycle_model.pipeline, fsm, function_model.transactions, workflow_todos.rtl-gen[0]

### RTL-0028: Lock or waive RTL target-scale policy before production signoff

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[1]
- Detail: The SSOT is production-profile, but quality_gates.rtl_gen.target_scale has no positive structural minima and no approved target_scale_waiver is present. Reference-derived target-scale candidates are review inputs only; a human must lock the chosen minima in SSOT or explicitly approve a waiver before rtl-gen can claim PL330-level or production top signoff.
SSOT ref: workflow_todos.rtl-gen[1].
Owner: mctp_assembler_v3 in rtl/mctp_assembler_v3.sv via workflow_todos.owner.
SSOT item context: id=RTL_TARGET_SCALE_POLICY.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - quality_gates.rtl_gen.target_scale contains at least one positive structural minimum such as source_files_min, modules_min, or depth_score_min
  - or quality_gates.rtl_gen.target_scale_waiver.approved is true with owner and reason
  - rtl_todo_plan.json target_scale_policy gate passes after rerunning rtl-gen TODO derivation
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[1]
  - Primary implementation evidence is in rtl/mctp_assembler_v3.sv
  - Semantic source_refs covered: quality_gates.rtl_gen.target_scale, quality_gates.rtl_gen.target_scale_waiver, reports/rtl_reference_profile.json
- SSOT refs: quality_gates.rtl_gen.target_scale, quality_gates.rtl_gen.target_scale_waiver, reports/rtl_reference_profile.json, workflow_todos.rtl-gen[1]
