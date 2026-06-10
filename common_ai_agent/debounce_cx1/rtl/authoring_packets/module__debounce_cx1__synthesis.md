# RTL Authoring Packet: module__debounce_cx1__synthesis

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 5
- Required tasks: 5

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
- LLM-actionable open tasks: 5
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 11/17 section=synthesis task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0078: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: value=No inferred latches..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0079: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: value=All architectural flops reset by rst_n..
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0080: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=area_um2_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0081: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=power_mw_max.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0082: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: planned
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: name=frequency_mhz_min; value=50.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/debounce_cx1.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min
