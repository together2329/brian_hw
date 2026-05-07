# RTL Authoring Packet: module__pl330_target_mfifo__equivalence

- Kind: module
- Owner module: pl330_target_mfifo
- Owner file: rtl/pl330_target_mfifo.sv
- Task count: 1
- Required tasks: 1

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
- Module slice: 10/11 section=equivalence task_limit=48
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

### RTL-0264: Prove module pl330_target_mfifo is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.pl330_target_mfifo.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.pl330_target_mfifo.module_equivalence.
Owner: pl330_target_mfifo in rtl/pl330_target_mfifo.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.pl330_target_mfifo.module_equivalence
  - Primary implementation evidence is in rtl/pl330_target_mfifo.sv
- SSOT refs: sub_modules.pl330_target_mfifo.module_equivalence
