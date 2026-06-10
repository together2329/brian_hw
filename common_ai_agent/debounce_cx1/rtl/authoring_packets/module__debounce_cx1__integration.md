# RTL Authoring Packet: module__debounce_cx1__integration

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 3
- Required tasks: 3

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Tasks tagged repair_generated_fm_marker are advisory schema-repair markers; they are omitted from authoring packets and must not cause fm*_observed RTL ports, wires, or state.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 5/17 section=integration task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0073: Implement integration item external_modules

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=external_modules.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0074: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=external_clocks; value=["clk"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0075: Implement integration item external_resets

- Priority: high
- Required: True
- Status: planned
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=external_resets; value=["rst_n"].
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: integration.dependencies.external_resets
