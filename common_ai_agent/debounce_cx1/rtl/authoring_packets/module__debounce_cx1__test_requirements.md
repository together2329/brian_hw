# RTL Authoring Packet: module__debounce_cx1__test_requirements

- Kind: module
- Owner module: debounce_cx1
- Owner file: rtl/debounce_cx1.sv
- Task count: 4
- Required tasks: 4

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
- PASS allowed: False
- Integration signoff allowed: True
- LLM-actionable open tasks: 4
- Human-locked open tasks: 0
- Owner refs: decomposition.units.output_latch, decomposition.units.stability_counter, function_model, function_model.state_variables, function_model.transactions, function_model.transactions.FM_BOUNCE, function_model.transactions.FM_STABLE, io_list, io_list.interfaces, registers, registers.register_list
- Module slice: 12/17 section=test_requirements task_limit=48
- Slice rule: Owner module debounce_cx1 is split into 17 authoring slices. Update the same owner_file incrementally and preserve logic from earlier slices.
- SSOT top IO contracts: 4

## Tasks

### RTL-0084: Keep RTL observable for scenario SC1

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC1
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC1.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: id=SC1; name=Reset defaults; expected=fl_ctr=0, fl_last=0, fl_db=0, db_out=0.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC1
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: fl_ctr=0, fl_last=0, fl_db=0, db_out=0
- SSOT refs: test_requirements.scenarios.SC1

### RTL-0085: Keep RTL observable for scenario SC2

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC2
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC2.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: id=SC2; name=Stable high — debounce fires after THRESH cycles; expected=db_out=0 for cycles 0-3, db_out=1 at cycle 4.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC2
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: db_out=0 for cycles 0-3, db_out=1 at cycle 4
- SSOT refs: test_requirements.scenarios.SC2

### RTL-0086: Keep RTL observable for scenario SC3

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC3
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC3.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: id=SC3; name=Bounce rejection — counter resets on change; expected=db_out=0 until stable 4-cycle run at end.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC3
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: db_out=0 until stable 4-cycle run at end
- SSOT refs: test_requirements.scenarios.SC3

### RTL-0087: Keep RTL observable for scenario SC4

- Priority: normal
- Required: True
- Status: planned
- Category: test_requirements.scenario
- Source ref: test_requirements.scenarios.SC4
- Detail: Scenario expectations must be traceable to RTL-observed signals for cocotb/pyuvm scoreboard checks.
SSOT ref: test_requirements.scenarios.SC4.
Owner: debounce_cx1 in rtl/debounce_cx1.sv via single_owner.
SSOT item context: id=SC4; name=Stable low — db_out returns to 0; expected=db_out=1 then transitions to 0 after 4 stable-low cycles.
- Current reason: RTL audit has not run yet.
- Criteria:
  - RTL exposes enough signals/status/outputs for the scenario checker
  - FunctionalModel expected result and RTL observed result can be compared
  - Scenario has coverage refs or a precise SSOT reason for exclusion
  - Traceability keeps source_ref test_requirements.scenarios.SC4
  - Primary implementation evidence is in rtl/debounce_cx1.sv
  - Downstream checker compares RTL-observed behavior against expected result: db_out=1 then transitions to 0 after 4 stable-low cycles
- SSOT refs: test_requirements.scenarios.SC4
