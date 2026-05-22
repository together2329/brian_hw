# RTL Authoring Packet: module__rv32i_min_core

- Kind: module
- Owner module: rv32i_min_core
- Owner file: rtl/rv32i_min_core.sv
- Task count: 28
- Required tasks: 28

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
- LLM-actionable open tasks: 0
- Human-locked open tasks: 0
- Owner refs: cycle_model, cycle_model.handshake_rules, cycle_model.ordering, cycle_model.pipeline, dataflow, decomposition, decomposition.units, function_model, function_model.invariants, function_model.state_variables, function_model.transactions, function_model.transactions.FM_ALU, function_model.transactions.FM_BRANCH, function_model.transactions.FM_JUMP, integration, integration.connections
- SSOT target scale: min_behavior_owner_logic_modules=4, min_depth_score=20, min_logic_modules=4, min_modules=6, min_procedural_blocks=8, min_source_files=6, min_state_updates=8
- SSOT connection contracts:
  - rv32i_min_core.excpt_o <= excpt_o (integration.connections[9])

## Tasks

### RTL-0133: Implement ordering rule: ordering_rule_0

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_0
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_0.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Retirement is in program order with at most one commit per cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_0
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_0 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_0

### RTL-0134: Implement ordering rule: ordering_rule_1

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_1
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_1.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Faulting misaligned or illegal instruction does not retire.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_1
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_1 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_1

### RTL-0135: Implement ordering rule: ordering_rule_2

- Priority: high
- Required: True
- Status: pass
- Category: cycle_model.ordering
- Source ref: cycle_model.ordering.ordering_rule_2
- Detail: Cycle-level behavior must be implemented in RTL, not only described in TB or FunctionalModel prose.
SSOT ref: cycle_model.ordering.ordering_rule_2.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via cycle_model.ordering.
SSOT item context: value=Store side effects occur only on aligned non-faulting stores.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL contains the control/state/handshake logic for this cycle rule
  - Rule timing is reflected in sample/hold/ready/valid or FSM behavior
  - TB scoreboard/coverage can observe the rule at the declared phase
  - Traceability keeps source_ref cycle_model.ordering.ordering_rule_2
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - cycle_model.ordering.ordering_rule_2 appears in RTL sample/hold/FSM/ready-valid timing, not only in TB
- SSOT refs: cycle_model.ordering.ordering_rule_2

### RTL-0156: Implement integration item dependencie_0

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_0
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_0.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.
SSOT item context: value=External instruction memory returns i_rdata for i_addr every cycle.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_0
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
- SSOT refs: integration.dependencies.dependencie_0

### RTL-0157: Implement integration item dependencie_1

- Priority: high
- Required: True
- Status: pass
- Category: integration.dependencies
- Source ref: integration.dependencies.dependencie_1
- Detail: This SSOT integration.dependencies item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.dependencies.dependencie_1.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.
SSOT item context: value=External data memory observes d_valid and d_we and d_be and provides d_rdata for loads.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.dependencies.dependencie_1
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
- SSOT refs: integration.dependencies.dependencie_1

### RTL-0158: Implement integration item i_addr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.i_addr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_addr.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_addr; signal=i_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_addr
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_addr is the implementation/observation point for i_addr
- SSOT refs: integration.connections.i_addr

### RTL-0159: Implement integration item i_valid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.i_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_valid.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_valid; signal=i_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_valid
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_valid is the implementation/observation point for i_valid
- SSOT refs: integration.connections.i_valid

### RTL-0160: Implement integration item i_rdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.i_rdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.i_rdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=i_rdata; signal=i_rdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.i_rdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port i_rdata is the implementation/observation point for i_rdata
- SSOT refs: integration.connections.i_rdata

### RTL-0161: Implement integration item d_addr

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_addr
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_addr.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_addr; signal=d_addr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_addr
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_addr is the implementation/observation point for d_addr
- SSOT refs: integration.connections.d_addr

### RTL-0162: Implement integration item d_wdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_wdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_wdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_wdata; signal=d_wdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_wdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_wdata is the implementation/observation point for d_wdata
- SSOT refs: integration.connections.d_wdata

### RTL-0163: Implement integration item d_rdata

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_rdata
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_rdata.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_rdata; signal=d_rdata.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_rdata
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_rdata is the implementation/observation point for d_rdata
- SSOT refs: integration.connections.d_rdata

### RTL-0164: Implement integration item d_we

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_we
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_we.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_we; signal=d_we.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_we
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_we is the implementation/observation point for d_we
- SSOT refs: integration.connections.d_we

### RTL-0165: Implement integration item d_be

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_be
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_be.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_be; signal=d_be.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_be
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_be is the implementation/observation point for d_be
- SSOT refs: integration.connections.d_be

### RTL-0166: Implement integration item d_valid

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.d_valid
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.d_valid.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=d_valid; signal=d_valid.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.d_valid
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port d_valid is the implementation/observation point for d_valid
- SSOT refs: integration.connections.d_valid

### RTL-0167: Implement integration item excpt_o

- Priority: high
- Required: True
- Status: pass
- Category: integration.connections
- Source ref: integration.connections.excpt_o
- Detail: This SSOT integration.connections item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: integration.connections.excpt_o.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via integration.connections.
SSOT item context: port=excpt_o; signal=excpt_o.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref integration.connections.excpt_o
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - DUT port excpt_o is the implementation/observation point for excpt_o
- SSOT refs: integration.connections.excpt_o

### RTL-0175: Prove module rv32i_min_core is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.rv32i_min_core.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.rv32i_min_core.module_equivalence.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.rv32i_min_core.module_equivalence
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
- SSOT refs: sub_modules.rv32i_min_core.module_equivalence

### RTL-0176: Keep RTL observable for scenario SC01

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC01
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC01.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC01; name=reset contract; expected=pc and regfile and excpt_o reset values match function_model and rtl_contract.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC01
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: pc and regfile and excpt_o reset values match function_model and rtl_contract
- SSOT refs: test_requirements.scenarios.SC01

### RTL-0177: Keep RTL observable for scenario SC02

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC02
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC02.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC02; name=opcode sweep 37; expected=pc and regfile trajectory match reference model for each opcode.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC02
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: pc and regfile trajectory match reference model for each opcode
- SSOT refs: test_requirements.scenarios.SC02

### RTL-0178: Keep RTL observable for scenario SC03

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC03
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC03.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC03; name=branch taken and untaken; expected=next pc behavior matches signed and unsigned branch rules.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC03
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: next pc behavior matches signed and unsigned branch rules
- SSOT refs: test_requirements.scenarios.SC03

### RTL-0179: Keep RTL observable for scenario SC04

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC04
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC04.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC04; name=load store extension and byte enable; expected=extension and d_be patterns match function_model contract.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC04
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: extension and d_be patterns match function_model contract
- SSOT refs: test_requirements.scenarios.SC04

### RTL-0180: Keep RTL observable for scenario SC05

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC05
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC05.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC05; name=x0 immutable; expected=regfile x0 remains zero.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC05
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: regfile x0 remains zero
- SSOT refs: test_requirements.scenarios.SC05

### RTL-0181: Keep RTL observable for scenario SC06

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC06
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC06.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC06; name=FM_FETCH transaction; expected=next_pc default rule and fetch outputs hold.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC06
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: next_pc default rule and fetch outputs hold
- SSOT refs: test_requirements.scenarios.SC06

### RTL-0182: Keep RTL observable for scenario SC07

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC07
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC07.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC07; name=FM_ALU transaction; expected=wb_data_alu equals model result.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC07
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: wb_data_alu equals model result
- SSOT refs: test_requirements.scenarios.SC07

### RTL-0183: Keep RTL observable for scenario SC08

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC08
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC08.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC08; name=FM_BRANCH transaction; expected=branch_next_pc rule matches taken and untaken outcomes.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC08
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: branch_next_pc rule matches taken and untaken outcomes
- SSOT refs: test_requirements.scenarios.SC08

### RTL-0184: Keep RTL observable for scenario SC09

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC09
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC09.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC09; name=FM_JUMP transaction; expected=link writeback and jalr lsb clear behavior match model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC09
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: link writeback and jalr lsb clear behavior match model
- SSOT refs: test_requirements.scenarios.SC09

### RTL-0185: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC10; name=FM_LOAD transaction; expected=wb_data_load rule and extension behavior match model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: wb_data_load rule and extension behavior match model
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0186: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC11; name=FM_STORE transaction; expected=d_valid and d_be and d_we behavior match model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: d_valid and d_be and d_we behavior match model
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0187: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: rv32i_min_core in rtl/rv32i_min_core.sv via test_requirements.
SSOT item context: id=SC12; name=FM_SYSTEM transaction; expected=exception pulse and fence bubble rules match model.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/rv32i_min_core.sv
  - Downstream checker compares RTL-observed behavior against expected result: exception pulse and fence bubble rules match model
- SSOT refs: test_requirements.scenarios.SC12
