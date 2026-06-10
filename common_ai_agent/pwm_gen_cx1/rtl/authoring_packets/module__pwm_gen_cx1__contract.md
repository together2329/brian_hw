# RTL Authoring Packet: module__pwm_gen_cx1__contract

- Kind: module
- Owner module: pwm_gen_cx1
- Owner file: rtl/pwm_gen_cx1.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: function_model, function_model.transactions, function_model.transactions.FM_TICK, function_model.transactions.FM_WRITE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 2/18 section=contract task_limit=48
- Slice rule: Owner module pwm_gen_cx1 is split into 18 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 5

## Tasks

### RTL-0028: Implement locked behavioral contract BC_PWM_COUNT

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_PWM_COUNT
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_PWM_COUNT.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: signal=["counter_q", "duty_reg", "pwm_gen_cx1", "pwm_out", "xFF"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_PWM_COUNT remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_PWM_COUNT
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_PWM_COUNT, rtl_contract

### RTL-0029: Implement locked behavioral contract BC_PWM_DUTY

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_PWM_DUTY
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_PWM_DUTY.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: signal=["counter_q", "duty_in", "duty_reg", "pwm_gen_cx1", "pwm_out", "xFF"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_PWM_DUTY remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_PWM_DUTY
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_PWM_DUTY, rtl_contract

### RTL-0030: Implement locked behavioral contract BC_PWM_LINT

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_PWM_LINT
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_PWM_LINT.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: signal=["counter_q", "duty_reg", "pwm_gen_cx1"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_PWM_LINT remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_PWM_LINT
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_PWM_LINT, rtl_contract

### RTL-0031: Implement locked behavioral contract BC_PWM_RESET

- Priority: critical
- Required: True
- Status: pass
- Category: contract.behavioral.rtl
- Source ref: req.behavioral_contracts.BC_PWM_RESET
- Detail: This row is derived directly from req/behavioral_contracts.json. The RTL must implement the contract's machine behavior and close the listed RTL stage_contracts.
SSOT ref: req.behavioral_contracts.BC_PWM_RESET.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: signal=["counter_q", "duty_reg", "pwm_gen_cx1", "pwm_out"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract BC_PWM_RESET remains traceable to req/behavioral_contracts.json
  - At least one SSOT behavior section projects this contract and owns RTL implementation work
  - An explicit rtl/rtl-gen stage_contract states the RTL observable/check/pass condition
  - Live owner RTL contains evidence terms from the contract inputs/outputs/state/observables
  - Traceability keeps source_ref req.behavioral_contracts.BC_PWM_RESET
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: req.behavioral_contracts.BC_PWM_RESET, rtl_contract

### RTL-0032: Implement locked structural contract SC_PWM_PORTS

- Priority: critical
- Required: True
- Status: pass
- Category: contract.structural.rtl
- Source ref: req.structural_contracts.SC_PWM_PORTS
- Detail: This row is derived directly from req/structural_contracts.json. RTL top ports must satisfy the contract's signal names, direction, width, and timing ownership.
SSOT ref: req.structural_contracts.SC_PWM_PORTS.
Owner: pwm_gen_cx1 in rtl/pwm_gen_cx1.sv via single_owner.
SSOT item context: signal=["clk", "duty_in", "pwm_out", "rst_n", "wr_en"].
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Contract SC_PWM_PORTS remains traceable to req/structural_contracts.json
  - Every structural signal is declared on the RTL top or explicitly waived by locked truth
  - Direction and width are checked against the RTL top declaration
  - Active structural inputs/outputs participate in live RTL logic or explicit SSOT waiver
  - Traceability keeps source_ref req.structural_contracts.SC_PWM_PORTS
  - Primary implementation evidence is in rtl/pwm_gen_cx1.sv
- SSOT refs: io_list, req.structural_contracts.SC_PWM_PORTS, top_module
