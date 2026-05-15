# RTL Authoring Packet: module__edge_detector__interrupts

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 1
- Required tasks: 1

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
- LLM-actionable open tasks: 1
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 11/16 section=interrupts task_limit=48
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

### RTL-0093: Implement interrupt item EDGE_DETECTED

- Priority: high
- Required: True
- Status: open
- Category: interrupts.sources
- Source ref: interrupts.sources.EDGE_DETECTED
- Detail: This SSOT interrupts.sources item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: interrupts.sources.EDGE_DETECTED.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: name=EDGE_DETECTED; clear=W1C.
- Current reason: Owner RTL file is missing: rtl/edge_detector.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref interrupts.sources.EDGE_DETECTED
  - Primary implementation evidence is in rtl/edge_detector.sv
  - EDGE_DETECTED clear behavior matches SSOT clear policy W1C
- SSOT refs: interrupts.sources.EDGE_DETECTED
