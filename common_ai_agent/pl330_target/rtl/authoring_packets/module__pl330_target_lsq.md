# RTL Authoring Packet: module__pl330_target_lsq

- Kind: module
- Owner module: pl330_target_lsq
- Owner file: rtl/pl330_target_lsq.sv
- Task count: 2
- Required tasks: 2

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
- Owner refs: cycle_model.ordering.lsq_order, function_model.transactions.load, function_model.transactions.store
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_lsq.busy_o <= lsq_busy_o (observed_named_port_map)
  - pl330_target_lsq.clk <= clk (observed_named_port_map)
  - pl330_target_lsq.empty_o <= lsq_empty_o (observed_named_port_map)
  - pl330_target_lsq.flush_i <= lsq_flush_i (observed_named_port_map)
  - pl330_target_lsq.load_addr_i <= lsq_load_addr_i (observed_named_port_map)
  - pl330_target_lsq.load_ready_o <= lsq_load_ready_o (observed_named_port_map)
  - pl330_target_lsq.load_resp_data_o <= lsq_load_resp_data_o (observed_named_port_map)
  - pl330_target_lsq.load_resp_error_o <= lsq_load_resp_error_o (observed_named_port_map)

## Tasks

### RTL-0030: Implement or account for SSOT module slice `pl330_target_lsq`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: name=pl330_target_lsq
SSOT ref: workflow_todos.rtl-gen[3].
Owner: pl330_target_lsq in rtl/pl330_target_lsq.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_LSQ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/pl330_target_lsq.sv
  - Semantic source_refs covered: sub_modules[2]
- SSOT refs: sub_modules[2], workflow_todos.rtl-gen[3]

### RTL-0263: Prove module pl330_target_lsq is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_lsq.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_lsq.module_equivalence.
Owner: pl330_target_lsq in rtl/pl330_target_lsq.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_lsq.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_lsq.sv
- SSOT refs: sub_modules.pl330_target_lsq.module_equivalence
