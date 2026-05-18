# RTL Authoring Packet: module__atcdmac100_core__test_requirements

- Kind: module
- Owner module: atcdmac100_core
- Owner file: rtl/atcdmac100_core.sv
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

- Quality profile: standard
- Work allowed: True
- Draft allowed: True
- Evidence closure allowed: False
- PASS allowed: True
- Integration signoff allowed: True
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, dataflow, decomposition, decomposition.owners, decomposition.source_refs, error_handling, features, fsm, function_model, function_model.state_variables, function_model.transactions.FM_AHB_READ, function_model.transactions.FM_AHB_WRITE, function_model.transactions.FM_ARBITRATE, function_model.transactions.FM_COMPLETE, function_model.transactions.FM_ERROR_ABORT, function_model.transactions.FM_HANDSHAKE_ACK
- Module slice: 13/17 section=test_requirements task_limit=48
- Slice rule: Owner module atcdmac100_core is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - atcdmac100_core.hclk <= hclk (integration.connections[0])
  - atcdmac100_core.hresetn <= RTL_TODO_2_quality_gates_rtl_gen (integration.connections[1])
  - atcdmac100_core.dma_int <= dma_int (integration.connections[2])
  - atcdmac100_core.dma_req <= dma_req (integration.connections[3])
  - atcdmac100_core.dma_ack <= dma_ack (integration.connections[4])
  - atcdmac100_core.haddr <= haddr (integration.connections[5])
  - atcdmac100_core.htrans <= htrans (integration.connections[6])
  - atcdmac100_core.hwrite <= hwrite (integration.connections[7])
  - atcdmac100_core.hsize <= hsize (integration.connections[8])
  - atcdmac100_core.hburst <= hburst (integration.connections[9])
  - atcdmac100_core.hwdata <= hwdata (integration.connections[10])
  - atcdmac100_core.hsel <= hsel (integration.connections[11])

## Tasks

### RTL-0396: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC01; name=reset contract; expected=Architectural state, status, outputs, and debug observability match function_model reset outputs..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Architectural state, status, outputs, and debug observability match function_model reset outputs.
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0397: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC02; name=primary approved behavior; expected=Externally observable result/status/side effects match the function_model primary transaction..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Externally observable result/status/side effects match the function_model primary transaction.
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0398: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC03; name=cycle handshake and backpressure; expected=Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Payloads remain stable, ordering is preserved, and completion timing respects cycle_model latency/backpressure rules.
- SSOT refs: test_requirements.scenarios.SC03

### RTL-0399: Keep RTL observable for scenario SC04

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC04
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC04.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC04; name=error and recovery policy; expected=Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC04
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Error/status/response/recovery behavior follows error_handling without corrupting unrelated architectural state.
- SSOT refs: test_requirements.scenarios.SC04

### RTL-0400: Keep RTL observable for scenario SC05

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC05
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC05.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC05; name=debug and trace observability; expected=Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC05
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Debug/status/trace events reflect committed SSOT-visible state without exposing unsupported behavior.
- SSOT refs: test_requirements.scenarios.SC05

### RTL-0401: Keep RTL observable for scenario SC06

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC06
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC06.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC06; name=function_model transaction FM_RESET; expected=Outputs and side effects match `FM_RESET` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC06
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_RESET` exactly.
- SSOT refs: test_requirements.scenarios.SC06

### RTL-0402: Keep RTL observable for scenario SC07

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC07
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC07.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC07; name=function_model transaction FM_AHB_WRITE; expected=Outputs and side effects match `FM_AHB_WRITE` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC07
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_AHB_WRITE` exactly.
- SSOT refs: test_requirements.scenarios.SC07

### RTL-0403: Keep RTL observable for scenario SC08

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC08
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC08.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC08; name=function_model transaction FM_AHB_READ; expected=Outputs and side effects match `FM_AHB_READ` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC08
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_AHB_READ` exactly.
- SSOT refs: test_requirements.scenarios.SC08

### RTL-0404: Keep RTL observable for scenario SC09

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC09
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC09.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC09; name=function_model transaction FM_ARBITRATE; expected=Outputs and side effects match `FM_ARBITRATE` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC09
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_ARBITRATE` exactly.
- SSOT refs: test_requirements.scenarios.SC09

### RTL-0405: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC10; name=function_model transaction FM_MASTER_READ; expected=Outputs and side effects match `FM_MASTER_READ` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_MASTER_READ` exactly.
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0406: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC11; name=function_model transaction FM_MASTER_WRITE; expected=Outputs and side effects match `FM_MASTER_WRITE` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_MASTER_WRITE` exactly.
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0407: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: atcdmac100_core in rtl/atcdmac100_core.sv via test_requirements.
SSOT item context: id=SC12; name=function_model transaction FM_COMPLETE; expected=Outputs and side effects match `FM_COMPLETE` exactly..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/atcdmac100_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: Outputs and side effects match `FM_COMPLETE` exactly.
- SSOT refs: test_requirements.scenarios.SC12
