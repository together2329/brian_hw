# RTL Authoring Packet: module__ssot_screenshot_smoke_20260524_083011__test_requirements

- Kind: module
- Owner module: ssot_screenshot_smoke_20260524_083011
- Owner file: rtl/ssot_screenshot_smoke_20260524_083011.sv
- Task count: 8
- Required tasks: 8

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
- Owner refs: dataflow, decomposition, integration, io_list, top_module
- Module slice: 12/15 section=test_requirements task_limit=48
- Slice rule: Owner module ssot_screenshot_smoke_20260524_083011 is split into 15 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 10

## Tasks

### RTL-0126: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC01; name=reset contract; expected=Architectural state, status, outputs, and debug observability match function_model reset outputs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Architectural state, status, outputs, and debug observability match function_model reset outputs.
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0127: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC02; name=primary approved behavior; expected=Externally observable result/status/side effects match the function_model primary transaction..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Externally observable result/status/side effects match the function_model primary transaction.
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0128: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC03; name=cycle handshake and backpressure; expected=Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
- SSOT refs: test_requirements.scenarios.SC03

### RTL-0129: Keep RTL observable for scenario SC04

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC04
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC04.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC04; name=error and recovery policy; expected=Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC04
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
- SSOT refs: test_requirements.scenarios.SC04

### RTL-0130: Keep RTL observable for scenario SC05

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC05
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC05.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC05; name=debug and trace observability; expected=Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC05
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
- SSOT refs: test_requirements.scenarios.SC05

### RTL-0131: Keep RTL observable for scenario SC06

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC06
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC06.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC06; name=function_model transaction FM_RESET; expected=Outputs and side effects match `FM_RESET` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC06
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_RESET` exactly.
- SSOT refs: test_requirements.scenarios.SC06

### RTL-0132: Keep RTL observable for scenario SC07

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC07
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC07.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC07; name=function_model transaction FM_PRIMARY; expected=Outputs and side effects match `FM_PRIMARY` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC07
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_PRIMARY` exactly.
- SSOT refs: test_requirements.scenarios.SC07

### RTL-0133: Keep RTL observable for scenario SC08

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC08
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC08.
Owner: ssot_screenshot_smoke_20260524_083011 in rtl/ssot_screenshot_smoke_20260524_083011.sv via single_owner.
SSOT item context: id=SC08; name=function_model transaction FM_CSR; expected=Outputs and side effects match `FM_CSR` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC08
  - Primary implementation evidence is in rtl/ssot_screenshot_smoke_20260524_083011.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_CSR` exactly.
- SSOT refs: test_requirements.scenarios.SC08
