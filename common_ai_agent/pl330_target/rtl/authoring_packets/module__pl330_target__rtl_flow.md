# RTL Authoring Packet: module__pl330_target__rtl_flow

- Kind: module
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
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
- Integration signoff allowed: False
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Module slice: 1/10 section=rtl_flow task_limit=48
- Slice rule: Owner module pl330_target is split into 10 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- Reference scale profile: reports/rtl_reference_profile.json (calibration-only, files=143, modules=210, lines=130568)
- Reference target-candidate subset: basis=design_candidate, files=57, modules=52, lines=52338
- Reference target-scale candidate present; SSOT target_scale is not locked yet
- Connection contract gap: Production-profile multi-module RTL requires machine-readable integration.connections or sub_modules[].connections before top integration or signoff can close.
- Pending connection-contract suggestions: 398 rows in rtl/connection_contract_suggestions.json
- Draft top integration fragment: rtl/connection_contract_draft_top.svfrag
- Suggestion usage: draft RTL wiring may use these rows to close hierarchy/signal-flow evidence, but they are not SSOT authority and cannot close connection-contract signoff.
  - pl330_target_engine.busy <= engine_busy (observed_named_port_map)
  - pl330_target_engine.channel_state <= engine_channel_state (observed_named_port_map)
  - pl330_target_engine.clk <= clk (observed_named_port_map)
  - pl330_target_engine.cmd_channel <= engine_cmd_channel (observed_named_port_map)
  - pl330_target_engine.cmd_dst_addr <= engine_cmd_dst_addr (observed_named_port_map)
  - pl330_target_engine.cmd_len <= engine_cmd_len (observed_named_port_map)
  - pl330_target_engine.cmd_opcode <= engine_cmd_opcode (observed_named_port_map)
  - pl330_target_engine.cmd_privileged <= engine_cmd_privileged (observed_named_port_map)
- SSOT top IO contracts: 11

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: value=pl330_target.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: io_list
