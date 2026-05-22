# RTL Authoring Packet: module__todo_counter_pipe

- Kind: module
- Owner module: todo_counter_pipe
- Owner file: rtl/todo_counter_pipe.sv
- Task count: 34
- Required tasks: 34

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
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- SSOT connection contracts:
  - todo_counter_pipe_cdc.bus_clk <= integration.connections.todo_counter_pipe_cdc.bus_clk (sub_modules[2].connections)
  - todo_counter_pipe_cdc.core_clk <= integration.connections.todo_counter_pipe_cdc.core_clk (sub_modules[2].connections)
  - todo_counter_pipe_cdc.bus_rst_n <= integration.connections.todo_counter_pipe_cdc.bus_rst_n (sub_modules[2].connections)
  - todo_counter_pipe_cdc.core_rst_n <= integration.connections.todo_counter_pipe_cdc.core_rst_n (sub_modules[2].connections)
  - todo_counter_pipe_cdc.control_bus_to_core <= cdc_requirements.crossings.control_bus_to_core.signals (sub_modules[2].connections)
  - todo_counter_pipe_cdc.status_core_to_bus <= cdc_requirements.crossings.status_core_to_bus.signals (sub_modules[2].connections)
  - todo_counter_pipe_regs.bus_clk <= bus_clk (integration.connections[0])
  - todo_counter_pipe_regs.bus_rst_n <= bus_rst_n (integration.connections[1])
  - todo_counter_pipe_regs.irq_o <= counter_irq (integration.connections[2])
  - todo_counter_pipe_core.core_clk <= core_clk (integration.connections[3])
  - todo_counter_pipe_core.core_rst_n <= core_rst_n (integration.connections[4])
  - todo_counter_pipe_core.event_i <= event_i (integration.connections[5])
- SSOT top IO contracts: 14

## Tasks

### RTL-0001: Read SSOT and build dynamic RTL implementation ledger

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.seed
- Source ref: top_module
- Detail: Use rtl_todo_plan.json derived from the current SSOT as the implementation checklist. Seed tasks are not the work breakdown; expand directly from the dynamic plan.
SSOT ref: top_module.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via top_module.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - rtl_todo_plan.json was regenerated from the current SSOT
  - Every required task in the plan is either implemented, evidenced, or escalated
  - No IP-specific fixed template is used as the source of truth
  - Traceability keeps source_ref top_module
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: top_module

### RTL-0002: Implement top-level ports, reset, and filelist integration

- Priority: high
- Required: True
- Status: pass
- Category: rtl_flow.top
- Source ref: io_list
- Detail: The top wrapper must expose the SSOT ports and connect every owned RTL file without hiding active behavior behind constants.
SSOT ref: io_list.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via top_module.
SSOT item context: value=todo_counter_pipe.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - Top module name matches SSOT top_module
  - Every SSOT top-level port appears with matching direction and width
  - Filelist contains all LLM-authored RTL sources and no stale sources
  - Traceability keeps source_ref io_list
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: io_list

### RTL-0023: Implement top-level integration module

- Priority: high
- Required: True
- Status: pass
- Category: workflow_todo.rtl_gen
- Source ref: workflow_todos.rtl-gen[3]
- Detail: Instantiate todo_counter_pipe_regs, todo_counter_pipe_core, and todo_counter_pipe_cdc. Wire APB ports to regs, event_i to core, CDC between regs↔core, counter_irq output from regs.
SSOT ref: workflow_todos.rtl-gen[3].
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via workflow_todos.owner.
SSOT item context: id=RTL_TODO_TOP_INTEGRATION.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - All external ports match io_list
  - Submodule instantiations use named port connections matching integration.connections
  - bus_rst_n and core_rst_n internal synchronizers for deassertion
  - No logic in top module except reset sync and wiring
  - SSOT workflow_todos.rtl-gen content/detail/criteria are preserved in rtl_todo_plan.json
  - RTL implementation evidence satisfies this SSOT-defined todo without editing SSOT, FunctionalModel, coverage goals, interface rules, or performance targets
  - Traceability keeps source_ref workflow_todos.rtl-gen[3]
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Semantic source_refs covered: integration.connections, io_list
- SSOT refs: integration.connections, io_list, workflow_todos.rtl-gen[3]

### RTL-0233: Implement error/fault item recovery_0

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_0
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_0.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via error_handling.
SSOT item context: action=software W1C write to INTCLR.ovf_clr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_0
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: error_handling.recovery.recovery_0

### RTL-0234: Implement error/fault item recovery_1

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_1
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_1.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via error_handling.
SSOT item context: action=software W1C write to INTCLR.unf_clr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_1
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: error_handling.recovery.recovery_1

### RTL-0235: Implement error/fault item recovery_2

- Priority: high
- Required: True
- Status: pass
- Category: error_handling.recovery
- Source ref: error_handling.recovery.recovery_2
- Detail: This SSOT error_handling.recovery item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: error_handling.recovery.recovery_2.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via error_handling.
SSOT item context: action=software W1C write to INTCLR.tc_clr.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref error_handling.recovery.recovery_2
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: error_handling.recovery.recovery_2

### RTL-0236: Implement security item counter_value

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.counter_value
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.counter_value.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via security.
SSOT item context: name=counter_value.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.counter_value
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: security.assets.counter_value

### RTL-0237: Implement security item control_registers

- Priority: high
- Required: True
- Status: pass
- Category: security.assets
- Source ref: security.assets.control_registers
- Detail: This SSOT security.assets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: security.assets.control_registers.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via security.
SSOT item context: name=control_registers.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref security.assets.control_registers
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: security.assets.control_registers

### RTL-0251: Implement synthesis item constraint_0

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_0
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_0.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: value=No inferred latches.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_0
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.constraints.constraint_0

### RTL-0252: Implement synthesis item constraint_1

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_1
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_1.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: value=All flops reset according to clock_reset_domains.reset_scheme.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_1
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.constraints.constraint_1

### RTL-0253: Implement synthesis item constraint_2

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_2
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_2.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: value=No package/interface/modport/function/task/for/while constructs in generated RTL.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_2
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.constraints.constraint_2

### RTL-0254: Implement synthesis item constraint_3

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_3
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_3.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: value=CDC synchronizer chains must be preserved (set_dont_touch on sync FFs).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_3
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.constraints.constraint_3

### RTL-0255: Implement synthesis item constraint_4

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.constraints
- Source ref: synthesis.constraints.constraint_4
- Detail: This SSOT synthesis.constraints item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.constraints.constraint_4.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: value=Dual-clock design: bus_clk and core_clk are independent clock roots.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.constraints.constraint_4
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.constraints.constraint_4

### RTL-0256: Implement synthesis item area_um2_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.area_um2_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.area_um2_max.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: name=area_um2_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.area_um2_max
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.ppa_targets.area_um2_max

### RTL-0257: Implement synthesis item power_mw_max

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.power_mw_max
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.power_mw_max.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: name=power_mw_max.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.power_mw_max
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.ppa_targets.power_mw_max

### RTL-0258: Implement synthesis item frequency_mhz_min

- Priority: high
- Required: True
- Status: pass
- Category: synthesis.ppa_targets
- Source ref: synthesis.ppa_targets.frequency_mhz_min
- Detail: This SSOT synthesis.ppa_targets item must map to RTL behavior, integration evidence, or a precise blocker.
SSOT ref: synthesis.ppa_targets.frequency_mhz_min.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via synthesis.
SSOT item context: name=frequency_mhz_min; value=300.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL owner/evidence is named for this SSOT item
  - Behavior is not represented only by comments or TB code
  - Downstream verification can observe or justify the item
  - Traceability keeps source_ref synthesis.ppa_targets.frequency_mhz_min
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: synthesis.ppa_targets.frequency_mhz_min

### RTL-0262: Prove module todo_counter_pipe is functionally equivalent to FL

- Priority: high
- Required: True
- Status: pass
- Category: equivalence.module
- Source ref: sub_modules.todo_counter_pipe.module_equivalence
- Detail: This is a functionality-equality gate, not a style or file-existence check. The module must be driven from the same SSOT transaction intent used by FunctionalModel.apply, and its RTL-observed outputs/state must equal the FL expected result.
SSOT ref: sub_modules.todo_counter_pipe.module_equivalence.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via module_equivalence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - verify/equivalence_goals.json contains an unblocked scope.level=module goal for this RTL module
  - cocotb/pyuvm scoreboard emits a row for the module goal before top-level signoff
  - scoreboard row fl_expected.model_api is FunctionalModel.apply
  - scoreboard row rtl_observed contains real RTL module boundary observations, not copied FL expected data
  - Any mismatch keeps SSOT and FunctionalModel fixed unless the SSOT itself is proven wrong
  - Traceability keeps source_ref sub_modules.todo_counter_pipe.module_equivalence
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
- SSOT refs: sub_modules.todo_counter_pipe.module_equivalence

### RTL-0263: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC1; name=Basic up-count; expected=cnt increments 0→1→2→3→4→5; STATUS=0; no interrupts.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt increments 0→1→2→3→4→5; STATUS=0; no interrupts
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0264: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC2; name=Basic down-count; expected=cnt decrements 10→9→8→7→6.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt decrements 10→9→8→7→6
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0265: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC3; name=Terminal count up; expected=cnt=4, tc_pending=1, counter_irq asserted (if INTEN.tc_en=1).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt=4, tc_pending=1, counter_irq asserted (if INTEN.tc_en=1)
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0266: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC4; name=Terminal count down; expected=cnt=0, tc_pending=1, counter_irq asserted (if enabled).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt=0, tc_pending=1, counter_irq asserted (if enabled)
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0267: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC5; name=Overflow saturate up; expected=cnt stays at MAX, overflow=1, ovf_pending=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt stays at MAX, overflow=1, ovf_pending=1
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0268: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC6; name=Overflow wrap up; expected=cnt=0, overflow=1, ovf_pending=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt=0, overflow=1, ovf_pending=1
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0269: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC7; name=Underflow saturate down; expected=cnt stays at 0, underflow=1, unf_pending=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt stays at 0, underflow=1, unf_pending=1
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0270: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC8; name=Underflow wrap down; expected=cnt=MAX, underflow=1, unf_pending=1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt=MAX, underflow=1, unf_pending=1
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0271: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC9; name=Clear counter; expected=cnt→0 after CDC; STATUS/int flags unchanged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt→0 after CDC; STATUS/int flags unchanged
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0272: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC10; name=Load counter; expected=cnt→0xDEAD after CDC convergence.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt→0xDEAD after CDC convergence
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0273: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC11; name=Disabled no-count; expected=cnt stays 5 regardless of event_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt stays 5 regardless of event_i
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0274: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC12; name=Interrupt clear W1C; expected=tc_pending→0, counter_irq deasserts.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: tc_pending→0, counter_irq deasserts
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0275: Keep RTL observable for scenario SC13

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC13
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC13.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC13; name=Interrupt masking; expected=counter_irq deasserts; INTSTAT.tc_pending remains 1.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC13
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: counter_irq deasserts; INTSTAT.tc_pending remains 1
- SSOT refs: test_requirements.scenarios.SC13

### RTL-0276: Keep RTL observable for scenario SC14

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC14
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC14.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC14; name=Clear priority over count; expected=cnt→0 on clear pulse edge; subsequent edges count from 0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC14
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt→0 on clear pulse edge; subsequent edges count from 0
- SSOT refs: test_requirements.scenarios.SC14

### RTL-0277: Keep RTL observable for scenario SC15

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC15
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC15.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC15; name=Load priority over count; expected=cnt→0x55; subsequent counts from 0x55.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC15
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: cnt→0x55; subsequent counts from 0x55
- SSOT refs: test_requirements.scenarios.SC15

### RTL-0278: Keep RTL observable for scenario SC16

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC16
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC16.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC16; name=CDC convergence; expected=Counter starts incrementing 2-4 core_clk cycles after bus write; cnt reads back on bus 2-5 bus_clk cycles after core ....
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC16
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: Counter starts incrementing 2-4 core_clk cycles after bus write; cnt reads back on bus 2-5 bus_clk cycles after core ...
- SSOT refs: test_requirements.scenarios.SC16

### RTL-0279: Keep RTL observable for scenario SC17

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC17
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC17.
Owner: todo_counter_pipe in rtl/todo_counter_pipe.sv via test_requirements.
SSOT item context: id=SC17; name=Debug cycle counter; expected=dbg_cycle_count increments on every core_clk regardless of enable/event_i.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC17
  - Primary implementation evidence is in rtl/todo_counter_pipe.sv
  - Downstream checker compares RTL-observed behavior against expected result: dbg_cycle_count increments on every core_clk regardless of enable/event_i
- SSOT refs: test_requirements.scenarios.SC17
