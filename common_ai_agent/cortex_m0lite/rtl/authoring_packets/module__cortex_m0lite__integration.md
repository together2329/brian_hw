# RTL Authoring Packet: module__cortex_m0lite__integration

- Kind: module
- Owner module: cortex_m0lite
- Owner file: rtl/cortex_m0lite.sv
- Task count: 10
- Required tasks: 10

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
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
- Owner refs: cdc_requirements, clock_reset_domains, integration, integration.connections, internal_interfaces, io_list, io_list.interfaces
- Module slice: 3/7 section=integration task_limit=48
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

### RTL-0158: Implement integration item external_modules

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.
SSOT item context: name=external_modules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0159: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.
SSOT item context: name=external_clocks; value=["clk", "hclk"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0160: Implement integration item external_resets

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.
SSOT item context: name=external_resets; value=["rst_n", "hresetn"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0161: Implement integration item connection_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_0
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_0.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_0
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_0

### RTL-0162: Implement integration item connection_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_1
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_1.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_1
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_1

### RTL-0163: Implement integration item connection_2

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_2
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_2.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_2
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_2

### RTL-0164: Implement integration item connection_3

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_3
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_3.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_3
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_3

### RTL-0165: Implement integration item connection_4

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_4
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_4.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_4
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_4

### RTL-0166: Implement integration item connection_5

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_5
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_5.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_5
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_5

### RTL-0167: Implement integration item connection_6

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.connection_6
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.connection_6.
Owner: cortex_m0lite in rtl/cortex_m0lite.sv via integration.connections.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.connection_6
  - Primary implementation evidence is in rtl/cortex_m0lite.sv
- SSOT refs: integration.connections.connection_6
