# RTL Authoring Packet: module__lfsr__integration

- Kind: module
- Owner module: lfsr
- Owner file: rtl/lfsr.sv
- Task count: 6
- Required tasks: 6

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 6
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 4/13 section=integration task_limit=48
- Slice rule: Owner module lfsr is split into 13 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - lfsr.PCLK <= PCLK (integration.connections[0])
  - lfsr.PRESETn <= PRESETn (integration.connections[1])
  - lfsr_regs.apb_slave <= APB4 (integration.connections[2])
- SSOT top IO contracts: 13

## Tasks

### RTL-0112: Implement integration item external_modules

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=external_modules.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0113: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=external_clocks; value=["PCLK"].
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0114: Implement integration item external_resets

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: name=external_resets; value=["PRESETn"].
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/lfsr.sv
- SSOT refs: integration.dependencies.external_resets

### RTL-0115: Implement integration item PCLK

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PCLK
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PCLK.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: port=PCLK; signal=PCLK.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PCLK
  - Primary implementation evidence is in rtl/lfsr.sv
  - DUT port PCLK is the implementation/observation point for PCLK
- SSOT refs: integration.connections.PCLK

### RTL-0116: Implement integration item PRESETn

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.PRESETn
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.PRESETn.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: port=PRESETn; signal=PRESETn.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.PRESETn
  - Primary implementation evidence is in rtl/lfsr.sv
  - DUT port PRESETn is the implementation/observation point for PRESETn
- SSOT refs: integration.connections.PRESETn

### RTL-0117: Implement integration item APB4

- Priority: high
- Required: True
- Status: open
- Category: integration.connections
- Source ref: integration.connections.APB4
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.APB4.
Owner: lfsr in rtl/lfsr.sv via single_owner.
SSOT item context: port=apb_slave; signal=APB4.
- Current reason: Owner RTL file is missing: rtl/lfsr.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.APB4
  - Primary implementation evidence is in rtl/lfsr.sv
  - DUT port apb_slave is the implementation/observation point for apb_slave
- SSOT refs: integration.connections.APB4
