# RTL Authoring Packet: module__cortex_m0lite__security

- Kind: module
- Owner module: cortex_m0lite
- Owner file: rtl/cortex_m0lite.sv
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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cdc_requirements, clock_reset_domains, integration, integration.connections, internal_interfaces, io_list, io_list.interfaces
- Module slice: 5/7 section=security task_limit=48
- Slice rule: Owner module cortex_m0lite is split into 7 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=6, min_depth_score=120, min_logic_modules=7, min_modules=8, min_procedural_blocks=12, min_source_files=8, min_state_updates=10
- SSOT connection contracts:
  - cortex_m0lite_core.clk <= clk (integration.connections[0])
  - cortex_m0lite_core.rst_n <= core_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.hclk <= hclk (integration.connections[0])
  - cortex_m0lite_core.hresetn <= bus_rst_n_sync (integration.connections[0])
  - cortex_m0lite_core.irq <= irq (integration.connections[0])
  - cortex_m0lite_core.pc_dbg <= pc_dbg (integration.connections[0])
  - cortex_m0lite_core.state_dbg <= state_dbg (integration.connections[0])
  - cortex_m0lite_core.retire <= retire (integration.connections[0])
  - cortex_m0lite_core.trap <= trap (integration.connections[0])
  - if_stage.clk <= clk (integration.connections[1])
  - if_stage.rst_n <= core_rst_n_sync (integration.connections[1])
  - if_stage.if_id_valid <= if_id_valid (integration.connections[1])
- SSOT top IO contracts: 27

## Tasks

### RTL-0156: Implement security item architectural_state

- Priority: high
- Required: True
- Status: planned
- Category: security.assets
- Source ref: security.assets.architectural_state
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.architectural_state.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: name=architectural_state.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.architectural_state
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: security.assets.architectural_state
