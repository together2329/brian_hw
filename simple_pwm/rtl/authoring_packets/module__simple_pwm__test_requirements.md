# RTL Authoring Packet: module__simple_pwm__test_requirements

- Kind: module
- Owner module: simple_pwm
- Owner file: rtl/simple_pwm.sv
- Task count: 4
- Required tasks: 4

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
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: top_module, function_model, cycle_model
- Module slice: 12/14 section=test_requirements task_limit=48
- Slice rule: Owner module simple_pwm is split into 14 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 6

## Tasks

### RTL-0084: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: id=SC1; name=Basic PWM generation; expected=3 clocks of pwm_out=1, 7 clocks of pwm_out=0, repeating 3 times.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Downstream checker compares RTL-observed behavior against expected result: 3 clocks of pwm_out=1, 7 clocks of pwm_out=0, repeating 3 times
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0085: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: id=SC2; name=Duty cycle variation; expected=First period: 3 high / 7 low; second period: 7 high / 3 low.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Downstream checker compares RTL-observed behavior against expected result: First period: 3 high / 7 low; second period: 7 high / 3 low
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0086: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: id=SC3; name=Period rollover; expected=Counter: 0,1,2,3,4,0,1,2,3,4,0,1,2,3,4; pwm_out: 1,1,0,0,0 repeating.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Downstream checker compares RTL-observed behavior against expected result: Counter: 0,1,2,3,4,0,1,2,3,4,0,1,2,3,4; pwm_out: 1,1,0,0,0 repeating
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0087: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: simple_pwm in rtl/simple_pwm.sv via single_owner.
SSOT item context: id=SC4; name=Disable behavior; expected=When enable=0: pwm_out=0, counter=0. When re-enabled: starts from counter=0.
- Current reason: Owner RTL file is missing: rtl/simple_pwm.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/simple_pwm.sv
  - Downstream checker compares RTL-observed behavior against expected result: When enable=0: pwm_out=0, counter=0. When re-enabled: starts from counter=0
- SSOT refs: test_requirements.scenarios.SC4
