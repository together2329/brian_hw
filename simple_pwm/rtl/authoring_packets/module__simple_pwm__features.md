# RTL Authoring Packet: module__simple_pwm__features

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 2
- Required tasks: 2

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
- LLM-actionable open tasks: 2
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 8/14 section=features task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0070: Implement feature PWM generation

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.PWM_generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.PWM_generation.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=PWM generation; output=pwm_out toggles at duty_cycle/period ratio.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.PWM_generation
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: features.PWM_generation

### RTL-0071: Implement feature Dynamic reconfiguration

- Priority: high
- Required: True
- Status: open
- Category: features.item
- Source ref: features.Dynamic_reconfiguration
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Dynamic_reconfiguration.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: name=Dynamic reconfiguration; output=PWM output adjusts within one period.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Dynamic_reconfiguration
  - Primary implementation evidence is in rtl/simple_pwm.sv
- SSOT refs: features.Dynamic_reconfiguration
