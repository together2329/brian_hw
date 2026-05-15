# RTL Authoring Packet: module__edge_detector__test_requirements

- Kind: module
- Owner module: edge_detector
- Owner file: rtl/edge_detector.sv
- Task count: 12
- Required tasks: 12

## Rules

- No fixed RTL template: author real IP-specific RTL from SSOT-derived tasks.
- Do not edit locked SSOT/FL/coverage/interface/performance authority artifacts.
- Every task must satisfy content, detail, and criteria before the packet is closed.
- For split owner modules, preserve existing owner_file logic from earlier slices and add only the missing behavior for this slice.
- Static RTL evidence is matched after SystemVerilog comments are stripped: required evidence_terms must appear as live RTL identifiers, declarations, or expressions in the owner_file, and the resulting RTL must remain lint-clean.
- Do not add evidence-only alias wires or identifiers copied from natural-language criteria; evidence must come from real control, datapath, CSR, FSM, CDC, or IO behavior.
- Record generated RTL files and todo_plan_sha256 in rtl_authoring_provenance.json.

## Context

- Quality profile: production
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.latency, cycle_model.pipeline, dataflow, features, function_model, function_model.output_rules, function_model.state_variables, function_model.transactions
- Module slice: 14/16 section=test_requirements task_limit=48
- Slice rule: Owner module edge_detector is split into 16 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=2, min_logic_modules=2, min_modules=2, min_procedural_blocks=4, min_source_files=2, min_state_updates=4
- SSOT connection contracts:
  - edge_detector.PCLK <= PCLK (integration.connections[0])
  - edge_detector.PRESETn <= PRESETn (integration.connections[1])
  - edge_detector.signal_i <= signal_i (integration.connections[2])
  - edge_detector.edge_o <= edge_o (integration.connections[3])
  - edge_detector.irq_o <= irq_o (integration.connections[4])
- SSOT top IO contracts: 14

## Tasks

### RTL-0117: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC1; name=Basic rising edge detection; expected=edge_o[0]=1 for one cycle; STATUS.edge_sticky[0]=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o[0]=1 for one cycle; STATUS.edge_sticky[0]=1
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0118: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC2; name=Basic falling edge detection; expected=edge_o[0]=1 for one cycle; STATUS.edge_sticky[0]=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o[0]=1 for one cycle; STATUS.edge_sticky[0]=1
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0119: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC3; name=Both-edge detection; expected=edge_o[0]=1 on each transition.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o[0]=1 on each transition
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0120: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC4; name=Synchronizer latency; expected=First edge_o appears after SYNC_STAGES+1 cycles.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: First edge_o appears after SYNC_STAGES+1 cycles
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0121: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC5; name=Sticky and overflow behavior; expected=STATUS.overflow=1; edge_o still pulses.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: STATUS.overflow=1; edge_o still pulses
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0122: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC6; name=W1C clear; expected=STATUS.edge_sticky and STATUS.overflow cleared to 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: STATUS.edge_sticky and STATUS.overflow cleared to 0
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0123: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC7; name=Enable gating; expected=edge_o remains 0; STATUS unchanged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o remains 0; STATUS unchanged
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0124: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC8; name=Reserved mode safety; expected=edge_o remains 0 regardless of input.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o remains 0 regardless of input
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0125: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC9; name=Interrupt generation; expected=irq_o=1 same cycle as edge_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: irq_o=1 same cycle as edge_o
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0126: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC10; name=APB register read/write; expected=Read data matches expected register state.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: Read data matches expected register state
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0127: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC11; name=Illegal APB address; expected=PSLVERR=1, no state change.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: PSLVERR=1, no state change
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0128: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: edge_detector in rtl/edge_detector.sv via single_owner.
SSOT item context: id=SC12; name=Multi-bit WIDTH operation; expected=edge_o reflects all transitions; each bit independent.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/edge_detector.sv
  - Downstream checker compares RTL-observed behavior against expected result: edge_o reflects all transitions; each bit independent
- SSOT refs: test_requirements.scenarios.SC12
