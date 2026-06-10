# RTL Authoring Packet: module__pwm_gen_cx1__features

- Kind: module
- Owner module: pwm_gen_cx1
- Owner file: rtl/pwm_gen_cx1.sv
- Task count: 2
- Required tasks: 2

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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: function_model, function_model.transactions, function_model.transactions.FM_TICK, function_model.transactions.FM_WRITE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 9/18 section=features task_limit=48
- Slice rule: Owner module pwm_gen_cx1 is split into 18 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0064: Implement feature PWM generation

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.PWM_generation
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.PWM_generation.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: name=PWM generation; output=pwm_out duty cycle equals duty_reg/256..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.PWM_generation
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: features.PWM_generation

### RTL-0065: Implement feature Duty cycle register write

- Priority: high
- Required: True
- Status: pass
- Category: features.item
- Source ref: features.Duty_cycle_register_write
- Detail: Features are user-visible behavior and must be decomposed into RTL control/datapath/status logic.
SSOT ref: features.Duty_cycle_register_write.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: name=Duty cycle register write; output=duty_reg updated; next PWM period reflects new duty..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Feature trigger/control/data behavior has RTL owner logic
  - Feature observability and error behavior match SSOT
  - Feature is covered by function/cycle/coverage tasks or explicitly blocked
  - Traceability keeps source_ref features.Duty_cycle_register_write
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: features.Duty_cycle_register_write
