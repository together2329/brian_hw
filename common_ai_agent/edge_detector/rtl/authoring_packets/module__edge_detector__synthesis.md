# RTL Authoring Packet: module__edge_detector__synthesis

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 7
- Required tasks: 7

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
- LLM-actionable open tasks: 7
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 13/16 section=synthesis task_limit=48
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

### RTL-0109: Implement synthesis item sdc_source

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.sdc_source
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.sdc_source.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=sdc_source; value=sdc/edge_detector.sdc.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.sdc_source
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.constraints.sdc_source

### RTL-0110: Implement synthesis item clock_groups

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.clock_groups
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.clock_groups.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=clock_groups; value=[{"name": "PCLK", "period_ns": 20.0, "source": "PCLK port", "waveform": "0 10"}].
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.clock_groups
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.constraints.clock_groups

### RTL-0111: Implement synthesis item io_constraints

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.io_constraints
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.io_constraints.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=io_constraints; value=[{"clock": "PCLK", "input_delay_ns": 0, "note": "asynchronous; sync chain handles", "ports": "signal_i"}, {"clock": "....
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.io_constraints
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.constraints.io_constraints

### RTL-0112: Implement synthesis item timing_targets

- Priority: high
- Required: True
- Status: open
- Category: synthesis.constraints
- Source ref: synthesis.constraints.timing_targets
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.timing_targets.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=timing_targets; value={"hold_wns_ns": 0.0, "setup_wns_ns": 0.0}.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.timing_targets
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.constraints.timing_targets

### RTL-0113: Implement synthesis item area_um2

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=area_um2.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.ppa_targets.area_um2

### RTL-0114: Implement synthesis item power_mw

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=power_mw.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.ppa_targets.power_mw

### RTL-0115: Implement synthesis item timing_wns_ns

- Priority: high
- Required: True
- Status: open
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.timing_wns_ns
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.timing_wns_ns.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=timing_wns_ns; value=0.0.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.timing_wns_ns
  - Primary implementation evidence is in rtl/edge_detector.sv
- SSOT refs: synthesis.ppa_targets.timing_wns_ns
