# RTL Authoring Packet: module__pl330_target__parameters

- Kind: module
- Owner module: pl330_target
- Owner file: rtl/pl330_target.sv
- Task count: 3
- Required tasks: 3

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
- Module slice: 3/10 section=parameters task_limit=48
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

### RTL-0090: Implement parameter NUM_CHANNELS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.NUM_CHANNELS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.NUM_CHANNELS.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=NUM_CHANNELS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.NUM_CHANNELS
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: parameters.NUM_CHANNELS

### RTL-0092: Implement parameter NUM_IRQS

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.NUM_IRQS
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.NUM_IRQS.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=NUM_IRQS.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.NUM_IRQS
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: parameters.NUM_IRQS

### RTL-0101: Implement parameter SUPPORT_TZ

- Priority: normal
- Required: True
- Status: pass
- Category: parameters.item
- Source ref: parameters.SUPPORT_TZ
- Detail: Declare the parameter/localparam in the owning RTL module and ensure all derived widths/slices are legal Verilog/SystemVerilog.
SSOT ref: parameters.SUPPORT_TZ.
Owner: pl330_target in rtl/pl330_target.sv via top_fallback.
SSOT item context: name=SUPPORT_TZ.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Parameter default/value matches SSOT
  - Parameter-derived widths are implemented outside procedural part-selects
  - Compile/lint evidence covers the parameterized form
  - Traceability keeps source_ref parameters.SUPPORT_TZ
  - Primary implementation evidence is in rtl/pl330_target.sv
- SSOT refs: parameters.SUPPORT_TZ
