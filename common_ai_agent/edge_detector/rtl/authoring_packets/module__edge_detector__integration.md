# RTL Authoring Packet: module__edge_detector__integration

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 8
- Required tasks: 8

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
- LLM-actionable open tasks: 8
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 4/16 section=integration task_limit=48
- Slice rule: Owner module edge_detector is split into 16 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4
- SSOT connection contracts:
  - edge_detector.PCLK <= PCLK (integration.connections[0])
  - edge_detector.PRESETn <= PRESETn (integration.connections[1])
  - edge_detector.signal_i <= signal_i (integration.connections[2])
  - edge_detector.edge_o <= edge_o (integration.connections[3])
  - edge_detector.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0101: Implement integration item external_modules

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=external_modules.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0102: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0103: Implement integration item external_resets

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0104: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: port=PCLK; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/edge_detector.sv
  - DUT port PCLK is the implementation/observation point for PCLK
- SSOT refs: integration.connections.PCLK

### RTL-0105: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: port=PRESETn; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/edge_detector.sv
  - DUT port PRESETn is the implementation/observation point for PRESETn
- SSOT refs: integration.connections.PRESETn

### RTL-0106: Implement integration item signal_i

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.signal_i
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.signal_i.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: port=signal_i; signal=signal_i.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.signal_i
  - Primary implementation evidence is in rtl/edge_detector.sv
  - DUT port signal_i is the implementation/observation point for signal_i
- SSOT refs: integration.connections.signal_i

### RTL-0107: Implement integration item edge_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.edge_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.edge_o.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: port=edge_o; signal=edge_o.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.edge_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - DUT port edge_o is the implementation/observation point for edge_o
- SSOT refs: integration.connections.edge_o

### RTL-0108: Implement integration item irq_o

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.irq_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.irq_o.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: port=irq_o; signal=irq_o.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.irq_o
  - Primary implementation evidence is in rtl/edge_detector.sv
  - DUT port irq_o is the implementation/observation point for irq_o
- SSOT refs: integration.connections.irq_o
