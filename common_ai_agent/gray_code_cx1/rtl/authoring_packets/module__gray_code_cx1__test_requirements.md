# RTL Authoring Packet: module__gray_code_cx1__test_requirements

- Kind: module
- Owner module: gray_code_cx1
- Owner file: rtl/gray_code_cx1.sv
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
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.pipeline, dataflow, dataflow.sequence, decomposition, features, function_model, function_model.state_variables, function_model.transactions.FM_PRIMARY, io_list, rtl_contract, test_requirements
- Module slice: 8/11 section=test_requirements task_limit=48
- Slice rule: Owner module gray_code_cx1 is split into 11 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - gray_code_cx1.clk <= clk (integration.connections[0])
  - gray_code_cx1.rst_n <= rst_n (integration.connections[1])
- SSOT top IO contracts: 8

## Tasks

### RTL-0066: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via test_requirements.
SSOT item context: id=SC01; name=reset contract; expected=gray_out and bin_out are 0 during reset..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: gray_out and bin_out are 0 during reset.
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0067: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via test_requirements.
SSOT item context: id=SC02; name=binary to gray encoding; expected=gray_out matches bin_in ^ (bin_in >> 1) one cycle later..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: gray_out matches bin_in ^ (bin_in >> 1) one cycle later.
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0068: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: gray_code_cx1 in rtl/gray_code_cx1.sv via test_requirements.
SSOT item context: id=SC03; name=gray to binary decoding; expected=bin_out matches cascaded XOR decoding of gray_in..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/gray_code_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: bin_out matches cascaded XOR decoding of gray_in.
- SSOT refs: test_requirements.scenarios.SC03
