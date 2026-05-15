# RTL Authoring Packet: module__arbiter_rr__test_requirements

- Kind: module
- Owner module: arbiter_rr
- Owner file: rtl/arbiter_rr.sv
- Task count: 10
- Required tasks: 10

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
- Work allowed: False
- Draft allowed: False
- Evidence closure allowed: False
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 10
- Human-locked open tasks: 0
- Owner refs: top_module, io_list, parameters, interrupts, features, error_handling, security, debug_observability, integration, timing, power, synthesis, dft, test_requirements, quality_gates, workflow_todos
- Module slice: 7/9 section=test_requirements task_limit=48
- Slice rule: Owner module arbiter_rr is split into 9 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT target scale: min_behavior_owner_logic_modules=1, min_logic_modules=1, min_modules=3, min_procedural_blocks=4, min_source_files=3, min_state_updates=3
- SSOT connection contracts:
  - arbiter_rr_regs.PCLK <= PCLK (integration.connections[0])
  - arbiter_rr_regs.PRESETn <= PRESETn (integration.connections[1])
  - arbiter_rr_regs.PADDR <= PADDR (integration.connections[2])
  - arbiter_rr_regs.PSEL <= PSEL (integration.connections[3])
  - arbiter_rr_regs.PENABLE <= PENABLE (integration.connections[4])
  - arbiter_rr_regs.PWRITE <= PWRITE (integration.connections[5])
  - arbiter_rr_regs.PWDATA <= PWDATA (integration.connections[6])
  - arbiter_rr_regs.PRDATA <= PRDATA (integration.connections[7])
  - arbiter_rr_regs.PREADY <= PREADY (integration.connections[8])
  - arbiter_rr_regs.PSLVERR <= PSLVERR (integration.connections[9])
  - arbiter_rr_regs.enable_o <= arb_enable (integration.connections[10])
  - arbiter_rr_regs.mask_o <= req_mask (integration.connections[11])
- SSOT top IO contracts: 14

## Tasks

### RTL-0160: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC1; name=Single requestor grant; expected=gnt_o[2] asserted on next cycle, gnt_valid_o=1, gnt_idx_o=2.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: gnt_o[2] asserted on next cycle, gnt_valid_o=1, gnt_idx_o=2
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0161: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC2; name=Round-robin fairness; expected=Each requestor is granted exactly once in 4 cycles in rotation order starting from (last_winner+1).
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: Each requestor is granted exactly once in 4 cycles in rotation order starting from (last_winner+1)
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0162: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC3; name=Request masking; expected=Only requestors 0 and 2 participate; grants alternate between them.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: Only requestors 0 and 2 participate; grants alternate between them
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0163: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC4; name=Enable/disable; expected=Grants stop when disabled, resume when re-enabled; last_winner is preserved across disable period.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: Grants stop when disabled, resume when re-enabled; last_winner is preserved across disable period
- SSOT refs: test_requirements.scenarios.SC4

### RTL-0164: Keep RTL observable for scenario SC5

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC5
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC5.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC5; name=No requests idle; expected=gnt_o=0, gnt_valid_o=0 on all cycles.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC5
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: gnt_o=0, gnt_valid_o=0 on all cycles
- SSOT refs: test_requirements.scenarios.SC5

### RTL-0165: Keep RTL observable for scenario SC6

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC6
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC6.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC6; name=Last winner persistence across disable; expected=Priority rotation resumes from (3+1)%4 = 0 after re-enable.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC6
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: Priority rotation resumes from (3+1)%4 = 0 after re-enable
- SSOT refs: test_requirements.scenarios.SC6

### RTL-0166: Keep RTL observable for scenario SC7

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC7
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC7.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC7; name=APB CSR read/write; expected=Written values readable; STATUS reflects internal arbiter state.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC7
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: Written values readable; STATUS reflects internal arbiter state
- SSOT refs: test_requirements.scenarios.SC7

### RTL-0167: Keep RTL observable for scenario SC8

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC8
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC8.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC8; name=APB illegal offset; expected=PSLVERR=1, PRDATA=0.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC8
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: PSLVERR=1, PRDATA=0
- SSOT refs: test_requirements.scenarios.SC8

### RTL-0168: Keep RTL observable for scenario SC9

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC9
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC9.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC9; name=One-hot grant invariant under all input combinations; expected=gnt_o is always one-hot or zero; never multi-bit or invalid.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC9
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: gnt_o is always one-hot or zero; never multi-bit or invalid
- SSOT refs: test_requirements.scenarios.SC9

### RTL-0169: Keep RTL observable for scenario SC10

- Priority: normal
- Required: True
- Status: open
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC10
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC10.
Owner: arbiter_rr in rtl/arbiter_rr.sv via test_requirements.
SSOT item context: id=SC10; name=Reset behavior; expected=All outputs zero during reset; arbitration resumes from last_winner=0 after deassertion.
- Current reason: Owner RTL file is missing: rtl/arbiter_rr.sv.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC10
  - Primary implementation evidence is in rtl/arbiter_rr.sv
  - Downstream checker compares RTL-observed behavior against expected result: All outputs zero during reset; arbitration resumes from last_winner=0 after deassertion
- SSOT refs: test_requirements.scenarios.SC10
