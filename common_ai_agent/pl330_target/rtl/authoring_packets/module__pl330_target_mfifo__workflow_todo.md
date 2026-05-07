# RTL Authoring Packet: module__pl330_target_mfifo__workflow_todo

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 6
- Required tasks: 6

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
- Owner refs: cycle_model.backpressure.mfifo_full, dataflow, features, fsm, function_model.state_variables, function_model.state_variables.mfifo, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers
- Module slice: 11/11 section=workflow_todo task_limit=48
- Slice rule: Owner module pl330_target_mfifo is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_mfifo.cfg_nonsecure_allowed_i <= mfifo_cfg_nonsecure_allowed_i (observed_named_port_map)
  - pl330_target_mfifo.channel_pc_o <= mfifo_channel_pc_o (observed_named_port_map)
  - pl330_target_mfifo.channel_state_o <= mfifo_channel_state_o (observed_named_port_map)
  - pl330_target_mfifo.clk <= clk (observed_named_port_map)
  - pl330_target_mfifo.cmd_accept_o <= mfifo_cmd_accept_o (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_addr_i <= mfifo_cmd_arg_addr_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_arg_data_i <= mfifo_cmd_arg_data_i (observed_named_port_map)
  - pl330_target_mfifo.cmd_error_o <= mfifo_cmd_error_o (observed_named_port_map)

## Tasks

### RTL-0031: Implement or account for SSOT module slice `pl330_target_mfifo`

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[4]
- Detail: name=pl330_target_mfifo
SSOT ref: workflow_todos.rtl-gen[4].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_MODULE_PL330_TARGET_MFIFO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Owned SSOT refs are implemented in the owner RTL file or explicitly mapped to the top integration module
  - Module slice has traceability evidence in rtl_todo_plan.json
  - No function/cycle/register/dataflow/FSM task owned by this slice remains orphaned
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[4]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: dataflow, features, fsm, function_model.state_variables, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers, registers.register_list, test_requirements
- SSOT refs: dataflow, features, fsm, function_model.state_variables, function_model.transactions.FM_DMAEND, function_model.transactions.FM_DMAGO, function_model.transactions.FM_DMALD, function_model.transactions.FM_DMALDP, function_model.transactions.FM_DMASEV, function_model.transactions.FM_DMAST, function_model.transactions.FM_DMASTP, function_model.transactions.FM_FAULT, function_model.transactions.FM_RESET, registers, registers.register_list, test_requirements

### RTL-0038: Implement FunctionalModel transaction `FM_RESET` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[11]
- Detail: Preconditions: . Outputs: all state -> reset values. Side effects: outstanding_reads=0; outstanding_writes=0; mfifo_count=0; irq_status=0. Error cases: .
SSOT ref: workflow_todos.rtl-gen[11].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_RESET.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[11]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: function_model.transactions.FM_RESET, function_model.transactions[0]
- SSOT refs: function_model.transactions.FM_RESET, function_model.transactions[0], workflow_todos.rtl-gen[11]

### RTL-0039: Implement FunctionalModel transaction `FM_DMAGO` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[12]
- Detail: Preconditions: channel_state==0; manager APB write to DBGINST. Outputs: channel_state=1; channel_pc=arg_addr. Side effects: . Error cases: condition=secure violation.
SSOT ref: workflow_todos.rtl-gen[12].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMAGO.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[12]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMAGO, function_model.transactions[1]
- SSOT refs: function_model.transactions.FM_DMAGO, function_model.transactions[1], workflow_todos.rtl-gen[12]

### RTL-0040: Implement FunctionalModel transaction `FM_DMALD` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[13]
- Detail: Preconditions: channel_state==1; mfifo has space. Outputs: outstanding_reads += 1; mfifo entries reserved. Side effects: issue AXI AR. Error cases: condition=AXI rresp != OKAY.
SSOT ref: workflow_todos.rtl-gen[13].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMALD.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[13]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMALD, function_model.transactions[2]
- SSOT refs: function_model.transactions.FM_DMALD, function_model.transactions[2], workflow_todos.rtl-gen[13]

### RTL-0041: Implement FunctionalModel transaction `FM_DMAST` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[14]
- Detail: Preconditions: channel_state==1; mfifo has data. Outputs: outstanding_writes += 1; mfifo entries consumed. Side effects: issue AXI AW + W. Error cases: condition=AXI bresp != OKAY.
SSOT ref: workflow_todos.rtl-gen[14].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMAST.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[14]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMAST, function_model.transactions[3]
- SSOT refs: function_model.transactions.FM_DMAST, function_model.transactions[3], workflow_todos.rtl-gen[14]

### RTL-0042: Implement FunctionalModel transaction `FM_DMALDP` in RTL

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[15]
- Detail: Preconditions: channel_state==1; periph drvalid asserted. Outputs: outstanding_reads += 1. Side effects: drready asserted; AXI AR issued. Error cases: .
SSOT ref: workflow_todos.rtl-gen[15].
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via workflow_todos.owner.
SSOT item context: id=RTL_FM_TX_FM_DMALDP.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL samples the transaction only under the approved preconditions
  - All listed outputs are driven with machine-checkable behavior or SSOT-approved status/error mapping
  - All side effects and error cases have observable state, status, or handoff evidence
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[15]
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
  - Semantic source_refs covered: function_model.transactions.FM_DMALDP, function_model.transactions[4]
- SSOT refs: function_model.transactions.FM_DMALDP, function_model.transactions[4], workflow_todos.rtl-gen[15]
