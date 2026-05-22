# RTL Authoring Packet: module__cortex_m0lite__synthesis

- Kind: module
- Owner module: cortex_m0lite
- Owner file: rtl/cortex_m0lite.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: cdc_requirements, clock_reset_domains, integration, integration.connections, internal_interfaces, io_list, io_list.interfaces
- Module slice: 6/7 section=synthesis task_limit=48
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

### RTL-0168: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: value=No inferred latches..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0169: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: value=No unresolved black boxes..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0170: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: value=All sequential state uses synchronized local reset release..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0171: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: value=Generated RTL uses input logic/output logic ANSI ports by default..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0172: Implement synthesis item constraint_4

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_4
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_4.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: value=Multiplication/division are not used unless explicitly approved; prefer shifts/adds for simple scaling..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_4
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.constraints.constraint_4

### RTL-0173: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: name=frequency_mhz_min; value=300.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0175: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: name=area_um2_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0176: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via top_fallback.
SSOT item context: name=power_mw_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max
