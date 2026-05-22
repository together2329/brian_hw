# RTL Authoring Packet: module__pulse_gen__test_requirements

- Kind: module
- Owner module: pulse_gen
- Owner file: rtl/pulse_gen.sv
- Task count: 15
- Required tasks: 15

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
- Module slice: 7/9 section=test_requirements task_limit=48
- Slice rule: Owner module pulse_gen is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT connection contracts:
  - pulse_gen_core.clk_i <= PCLK (integration.connections[0])
  - pulse_gen_core.rst_ni <= PRESETn (integration.connections[1])
  - pulse_gen_core.trigger_i <= trigger_i (integration.connections[2])
  - pulse_gen_core.pulse_out <= pulse_out (integration.connections[3])
  - pulse_gen_core.irq_o <= irq_o (integration.connections[4])
  - pulse_gen_regs.clk_i <= PCLK (integration.connections[5])
  - pulse_gen_regs.rst_ni <= PRESETn (integration.connections[6])
  - pulse_gen.PRDATA <= pulse_gen_regs.PRDATA (integration.connections[7])
  - pulse_gen.PREADY <= 1'b1 (zero-wait-state) (integration.connections[8])
  - pulse_gen.PSLVERR <= pulse_gen_regs.PSLVERR (integration.connections[9])
  - pulse_gen_regs.ctrl_fire_o <= pulse_gen_core.ctrl_fire (integration.connections[10])
  - pulse_gen_regs.ctrl_enable_o <= pulse_gen_core.ctrl_enable (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0169: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC1; name=Software single-cycle pulse; expected=pulse_out asserts for exactly 1 PCLK cycle, STATUS.busy=1 during pulse, STATUS.done=1 after, fired_count increments.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: pulse_out asserts for exactly 1 PCLK cycle, STATUS.busy=1 during pulse, STATUS.done=1 after, fired_count increments
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0170: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC2; name=Hardware trigger pulse; expected=Identical to software trigger: pulse_out asserts for PULSE_WIDTH cycles.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: Identical to software trigger: pulse_out asserts for PULSE_WIDTH cycles
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0171: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC3; name=Multi-cycle pulse width; expected=pulse_out asserts for exactly 10 consecutive PCLK cycles.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: pulse_out asserts for exactly 10 consecutive PCLK cycles
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0172: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC4; name=Back-to-back pulses; expected=Both pulses complete with correct width; fired_count increments by 2.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: Both pulses complete with correct width; fired_count increments by 2
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0173: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC5; name=Non-reentrant rejection; expected=Second trigger ignored; only one pulse completes; fired_count increments by 1 only.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: Second trigger ignored; only one pulse completes; fired_count increments by 1 only
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0174: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC6; name=Disabled trigger rejection; expected=No pulse output; STATUS unchanged; fired_count unchanged.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: No pulse output; STATUS unchanged; fired_count unchanged
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0175: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC7; name=Polarity inversion; expected=pulse_out is low during pulse and high when idle (inverted from default).
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: pulse_out is low during pulse and high when idle (inverted from default)
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0176: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC8; name=Interrupt enable/disable; expected=First pulse: no irq_o. Second pulse: irq_o asserts at completion..
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: First pulse: no irq_o. Second pulse: irq_o asserts at completion.
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0177: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC9; name=W1C STATUS.done clear; expected=STATUS.done clears to 0; irq_o deasserts if no other pending source.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: STATUS.done clears to 0; irq_o deasserts if no other pending source
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0178: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC10; name=Runtime width change; expected=First pulse is 5 cycles; second pulse is 3 cycles; mid-pulse write ignored for current pulse.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: First pulse is 5 cycles; second pulse is 3 cycles; mid-pulse write ignored for current pulse
- SSOT refs: test_requirements.scenarios.SC10

### RTL-0179: Keep RTL observable for scenario SC11

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC11
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC11.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC11; name=Reset clears all state; expected=pulse_out returns to idle_level, FSM→IDLE, STATUS→0, counter→0, irq_o→0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC11
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: pulse_out returns to idle_level, FSM→IDLE, STATUS→0, counter→0, irq_o→0
- SSOT refs: test_requirements.scenarios.SC11

### RTL-0180: Keep RTL observable for scenario SC12

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC12
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC12.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC12; name=APB illegal address; expected=PSLVERR=1, PRDATA=0.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC12
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: PSLVERR=1, PRDATA=0
- SSOT refs: test_requirements.scenarios.SC12

### RTL-0181: Keep RTL observable for scenario SC13

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC13
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC13.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC13; name=PULSE_WIDTH=0 clamp; expected=Pulse width is treated as 1 (minimum clamp); no error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC13
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: Pulse width is treated as 1 (minimum clamp); no error
- SSOT refs: test_requirements.scenarios.SC13

### RTL-0182: Keep RTL observable for scenario SC14

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC14
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC14.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC14; name=fired_count wrap; expected=fired_count wraps cleanly; no overflow error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC14
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: fired_count wraps cleanly; no overflow error
- SSOT refs: test_requirements.scenarios.SC14

### RTL-0183: Keep RTL observable for scenario SC15

- Priority: normal
- Required: True
- Status: pass
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC15
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC15.
Owner: pulse_gen in rtl/pulse_gen.sv via test_requirements.
SSOT item context: id=SC15; name=Simultaneous SW+HW trigger; expected=Exactly one pulse fires (not double); no error.
- Current reason: Task criteria are closed by SSOT traceability plus owner RTL/audit evidence.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC15
  - Primary implementation evidence is in rtl/pulse_gen.sv
  - Downstream checker compares RTL-observed behavior against expected result: Exactly one pulse fires (not double); no error
- SSOT refs: test_requirements.scenarios.SC15
