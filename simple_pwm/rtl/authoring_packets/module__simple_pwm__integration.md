# RTL Authoring Packet: module__simple_pwm__integration

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 3
- Required tasks: 3

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
- LLM-actionable open tasks: 3
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 4/14 section=integration task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0074: Implement integration item external_modules

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_modules
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_modules.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=external_modules.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_modules
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: integration.dependencies.external_modules

### RTL-0075: Implement integration item external_clocks

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_clocks
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_clocks.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=external_clocks; value=["clk"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_clocks
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: integration.dependencies.external_clocks

### RTL-0076: Implement integration item external_resets

- Priority: high
- Required: True
- Status: open
- Category: integration.dependencies
- Source ref: integration.dependencies.external_resets
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.external_resets.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=external_resets; value=["rst_n"].
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.external_resets
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: integration.dependencies.external_resets
